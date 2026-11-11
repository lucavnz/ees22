"""
Simulazione circuitale completa in LTspice dell'oscillazione elettrica parassita
allo spegnimento del gate (V_DC = 0 V, compensazione hardware attiva).

Modelli SPICE impiegati nella cartella LTspice/:
- OPA656.LIB : Modello SPICE ufficiale Texas Instruments (SBOM136, alimentazione duale +-5 V) per il TIA (U3).
- TL082.LIB  : Modello SPICE ufficiale Texas Instruments (SLOJ070, ingresso JFET, +-12 V) per U1 e U2.
- UniversalOpAmp2.lib / opamps_mems.lib : Macromodello nativo LTspice/Analog Devices level2 parametrizzato
  da datasheet per il secondo stadio invertente AD817 (U4, G = -10) e funzione sorgente burst.

Questo script:
1. Genera lo schematico completo LTspice (.asc) in LTspice/oscillazione_parassita.asc
   e renderizza l'immagine pulita Grafici/circuito_ltspice_schema.png (senza commenti ne direttive).
2. Esegue direttamente il motore LTspice in modalita batch (-b) per i due transitori sperimentali:
   - dv_in/dt > 0 (confronto con Misure/scope_173.csv)
   - dv_in/dt < 0 (confronto con Misure/scope_172.csv)
3. Verifica anche lo sweep di fase V_pp(phi) predetto da LTspice tra -180 deg e +180 deg.
4. Genera il grafico ad alta risoluzione (300 DPI) Grafici/simulazione_ltspice_confronto.png.
"""

import os
import subprocess
import zipfile
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Misure")
LTSPICE_DIR = os.path.join(BASE_DIR, "LTspice")
OUT_DIR = os.path.join(BASE_DIR, "Grafici")
os.makedirs(LTSPICE_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

LTSPICE_BIN = "/Applications/LTspice.app/Contents/MacOS/LTspice"

# -----------------------------------------------------------------------------
# 1. PARAMETRI FISICI DEL CIRCUITO COMPLETO (coerenti con Sezioni 6, 8 e 9)
# -----------------------------------------------------------------------------
PARAMS = {
    "f0_hz": 417830.0,       # Frequenza forzante del burst [Hz]
    "toff_us": 35.0,         # Istante di spegnimento del gate nella simulazione [us]
    "vac_v": 0.09889,        # Ampiezza di picco misurata su CH3 (~100 mV) [V]
    "vdc_in_v": -0.00385,    # Piccolo offset DC del generatore su CH3 [V]
    "t_freeze_us": -0.025,   # Offset temporale tra stop del DAC su CH3 e trigger CH2 [us]
    # Ramo parassita MEMS a V_DC = 0 V (Sezioni 8 e 9)
    "Cp_pF": 0.892,
    "Rp_Meg": 11.2,
    # Circuito di compensazione hardware attiva tarato a 417.83 kHz con TL082.LIB ufficiale TI
    "Cphi_pF": 100.0,
    "Rin_phi_ohm": 2899.05,  # R_phi1 + R_Pphi1 tarato per l'opposizione di fase di U1-U2 a f1
    "Rf_phi_ohm": 24450.0,   # R_phi2 + R_Pphi2
    "alpha": 0.01156,        # Posizione cursore potenziometro R_A = 10 kOhm
    "Cc_pF": 10.0,
    "Rc_Meg": 1.0,
    # Stadio TIA (OPA656.LIB ufficiale TI, +-5 V) + capacita parassite di cablaggio/retroazione
    "Rf_tia_kohm": 500.0,
    "Cf_pF": 0.138,
    "Cin_ext_pF": 7.60,      # Capacita parassita esterna PCB/cablaggio sul nodo invertente V-
    # Secondo stadio invertente G = -10 (AD817)
    "R1_ohm": 100.0,
    "R2_ohm": 1000.0,
    "Vos_AD817_mV": -2.05,   # Tensione di offset d'ingresso statica dell'AD817 (< 2.5 mV da datasheet)
}


def ensure_aux_libs():
    """Assicura la presenza di UniversalOpAmp2.lib da LTspice e scrive opamps_mems.lib."""
    univ_dst = os.path.join(LTSPICE_DIR, "UniversalOpAmp2.lib")
    if not os.path.exists(univ_dst):
        zf = zipfile.ZipFile("/Applications/LTspice.app/Contents/Resources/lib.zip")
        with open(univ_dst, "wb") as f:
            f.write(zf.read("lib/sub/UniversalOpAmp2.lib"))

    lib_path = os.path.join(LTSPICE_DIR, "opamps_mems.lib")
    lib_txt = f"""* Funzione sorgente burst (Agilent 33220A) e wrapper AD817 su UniversalOpAmp2 nativo LTspice
.lib UniversalOpAmp2.lib

.func v_burst(t) {{if(t < 1u, 0, Vdc_in + if(t < toff, Vac*sin(2*pi*f0*(t - toff) + phi), Vac*sin(phi)))}}

* AD817: High-Speed Bipolar Op-Amp (GBW = 50 MHz, Slew = 350 V/us, Avol = 3.5 V/mV)
.subckt AD817 inp inn vcc vee out
XU_AD inp inn vcc vee out level2 Avol=3.5k GBW=50Meg Slew=350Meg Ilimit=50m rail=1.5 Vos={PARAMS['Vos_AD817_mV']}m Phimargin=60
.ends AD817
"""
    with open(lib_path, "w") as f:
        f.write(lib_txt)


def build_spice_netlist(phi_deg):
    """Genera la netlist SPICE completa usando i modelli ufficiali OPA656.LIB e TL082.LIB."""
    ra_tot = 10000.0
    ra2 = ra_tot * PARAMS["alpha"]
    ra1 = ra_tot - ra2
    phi_rad = np.deg2rad(phi_deg)

    opa_lib = os.path.join(LTSPICE_DIR, "OPA656.LIB")
    tl_lib = os.path.join(LTSPICE_DIR, "TL082.LIB")
    aux_lib = os.path.join(LTSPICE_DIR, "opamps_mems.lib")

    return f"""* Simulazione LTspice - Transitorio elettrico parassita allo spegnimento del gate (V_DC = 0 V)
.lib "{opa_lib}"
.lib "{tl_lib}"
.lib "{aux_lib}"
.options plotwinsize=0 reltol=1e-5 srcstepmethod=1 noopiter gminsteps=0

VCC vcc 0 12
VEE vee 0 -12
VCC5 vcc5 0 5
VEE5 vee5 0 -5

.param f0 = {PARAMS['f0_hz']}
.param toff = {PARAMS['toff_us']}u
.param Vac = {PARAMS['vac_v']:.6f}
.param phi = {phi_rad:.8f}
.param Vdc_in = {PARAMS['vdc_in_v']:.6f}

Bvin vin 0 V = v_burst(time)

* Ramo parassita del MEMS spento (V_DC = 0 V)
Cp vin v_minus {PARAMS['Cp_pF']}p
Rp vin v_minus {PARAMS['Rp_Meg']}Meg

* Circuito di compensazione hardware attiva (U1 e U2: modello ufficiale TI TL082.LIB)
Cphi vin n_cphi {PARAMS['Cphi_pF']}p
Rin_phi n_cphi u1_inv {PARAMS['Rin_phi_ohm']:.2f}
Rf_phi u1_inv v_u1 {PARAMS['Rf_phi_ohm']:.2f}
XU1 0 u1_inv vcc vee v_u1 TL082

RA1 v_u1 v_a {ra1:.3f}
RA2 v_a 0 {ra2:.3f}
XU2 v_a v_u2 vcc vee v_u2 TL082

Cc v_u2 v_minus {PARAMS['Cc_pF']}p
Rc v_u2 v_minus {PARAMS['Rc_Meg']}Meg

* Stadio TIA (U3: modello ufficiale TI OPA656.LIB, alimentato a +-5 V)
Cin_ext v_minus 0 {PARAMS['Cin_ext_pF']}p
Rf v_minus v_tia {PARAMS['Rf_tia_kohm']}k
Cf v_minus v_tia {PARAMS['Cf_pF']}p
XU3 0 v_minus vcc5 vee5 v_tia OPA656

* Secondo stadio invertente G = -10 (U4: AD817)
R1 v_tia ad_inv {PARAMS['R1_ohm']}
R2 ad_inv v_out {PARAMS['R2_ohm']}
XU4 0 ad_inv vcc vee v_out AD817

.tran 0 42u 20u 2n
.end
"""


def write_ltspice_plt(plt_path):
    """Salva il file .plt di configurazione tracce per mostrare subito V(v_out) e V(vin) al Run in LTspice."""
    plt_txt = """[Transient Analysis]
{
   Npanes: 2
   ActivePane: 1
   {
      traces: 1 {524290,0,"V(vin)"}
      X: ('u',0,3.3e-05,1e-06,4.2e-05)
      Y[0]: ('m',1,-0.12,0.04,0.12)
      Units: "V"
   }
   {
      traces: 1 {524291,0,"V(v_out)"}
      X: ('u',0,3.3e-05,1e-06,4.2e-05)
      Y[0]: ('m',1,-0.8,0.2,0.9)
      Units: "V"
   }
}
"""
    with open(plt_path, "w") as f:
        f.write(plt_txt)


def build_ltspice_asc(asc_path):
    """
    Costruisce lo schematico nativo LTspice (.asc) pulito (senza testi di commento),
    con i simboli standard integrati (bv, voltage, res, cap, OpAmps\\opamp2) collegati
    ai modelli ufficiali OPA656.LIB, TL082.LIB e opamps_mems.lib.
    """
    ensure_aux_libs()
    write_ltspice_plt(asc_path.replace(".asc", ".plt"))

    lines = ["Version 4", "SHEET 1 2160 860"]
    wires = []
    flags = []
    syms = []
    texts = []

    def wire(x1, y1, x2, y2):
        wires.append(f"WIRE {x2} {y2} {x1} {y1}")

    def flag(x, y, name):
        flags.append(f"FLAG {x} {y} {name}")

    def res_h(x_left, y, name, val):
        x0, y0 = x_left + 96, y - 16
        syms.append(
            f"SYMBOL res {x0} {y0} R90\n"
            f"WINDOW 0 0 56 VBottom 2\n"
            f"WINDOW 3 32 56 VTop 2\n"
            f"SYMATTR InstName {name}\n"
            f"SYMATTR Value {val}"
        )
        return x_left + 80

    def res_v(x, y_top, name, val):
        x0, y0 = x - 16, y_top - 16
        syms.append(
            f"SYMBOL res {x0} {y0} R0\n"
            f"SYMATTR InstName {name}\n"
            f"SYMATTR Value {val}"
        )
        return y_top + 80

    def cap_h(x_left, y, name, val):
        x0, y0 = x_left + 64, y - 16
        syms.append(
            f"SYMBOL cap {x0} {y0} R90\n"
            f"SYMATTR InstName {name}\n"
            f"SYMATTR Value {val}"
        )
        return x_left + 64

    def cap_v(x, y_top, name, val):
        x0, y0 = x - 16, y_top
        syms.append(
            f"SYMBOL cap {x0} {y0} R0\n"
            f"SYMATTR InstName {name}\n"
            f"SYMATTR Value {val}"
        )
        return y_top + 64

    def opamp2(xc, y0, name, model, vpos="vcc", vneg="vee"):
        syms.append(
            f"SYMBOL OpAmps\\opamp2 {xc} {y0} R0\n"
            f"SYMATTR InstName {name}\n"
            f"SYMATTR Value {model}"
        )
        flag(xc, y0 + 32, vpos)
        flag(xc, y0 + 96, vneg)
        return {
            "inm": (xc - 32, y0 + 48),
            "inp": (xc - 32, y0 + 80),
            "out": (xc + 32, y0 + 64),
        }

    # --- Alimentazioni duali (+-12 V per TL082/AD817 e +-5 V per OPA656) in alto a sinistra ---
    for x_s, inst_s, val_s, fl_s in [
        (-304, "VCC", "12", "vcc"),
        (-184, "VEE", "-12", "vee"),
        (-64, "VCC5", "5", "vcc5"),
        (56, "VEE5", "-5", "vee5"),
    ]:
        syms.append(f"SYMBOL voltage {x_s} 64 R0\nSYMATTR InstName {inst_s}\nSYMATTR Value {val_s}")
        flag(x_s, 80, fl_s)
        flag(x_s, 160, "0")

    # --- Sorgente Burst Bvin (Agilent 33220A) ---
    syms.append(
        "SYMBOL bv -48 336 R0\n"
        "SYMATTR InstName Bvin\n"
        "SYMATTR Value V=v_burst(time)"
    )
    wire(-48, 352, -48, 320)
    wire(-48, 320, 176, 320)
    flag(80, 320, "vin")
    flag(-48, 432, "0")

    # --- Ramo Parassita MEMS (Cp || Rp) ---
    wire(176, 320, 176, 160)
    wire(176, 160, 560, 160)
    xr = cap_h(560, 160, "Cp", f"{PARAMS['Cp_pF']}p")
    wire(xr, 160, 1184, 160)

    wire(176, 240, 544, 240)
    xr_rp = res_h(544, 240, "Rp", f"{PARAMS['Rp_Meg']}Meg")
    wire(xr_rp, 240, 1184, 240)
    wire(1184, 160, 1184, 336)

    wire(176, 320, 176, 464)

    # --- Circuito di Compensazione Hardware Attiva (U1 -> RA1/RA2 -> U2 -> Cc || Rc) ---
    wire(176, 464, 224, 464)
    xc_end = cap_h(224, 464, "Cphi", f"{PARAMS['Cphi_pF']:.0f}p")
    wire(xc_end, 464, 320, 464)
    xr_in = res_h(320, 464, "Rin_phi", f"{PARAMS['Rin_phi_ohm']:.0f}")
    wire(xr_in, 464, 448, 464)

    opamp2(480, 416, "U1", "TL082", "vcc", "vee")
    wire(448, 496, 448, 528)
    flag(448, 528, "0")

    wire(432, 464, 432, 352)
    wire(432, 352, 448, 352)
    x_rf1 = res_h(448, 352, "Rf_phi", f"{PARAMS['Rf_phi_ohm']/1e3:.2f}k")
    wire(x_rf1, 352, 560, 352)
    wire(512, 480, 560, 480)
    wire(560, 352, 560, 480)
    flag(600, 480, "v_u1")

    ra2_val = 10000.0 * PARAMS["alpha"]
    ra1_val = 10000.0 - ra2_val
    wire(560, 480, 640, 480)
    yb1 = res_v(640, 480, "RA1", f"{ra1_val:.1f}")
    wire(640, yb1, 640, 608)
    flag(696, 576, "v_a")
    yb2 = res_v(640, 608, "RA2", f"{ra2_val:.1f}")
    flag(640, yb2, "0")

    opamp2(800, 496, "U2", "TL082", "vcc", "vee")
    wire(640, 576, 768, 576)
    wire(832, 560, 864, 560)
    flag(888, 560, "v_u2")
    wire(864, 560, 864, 464)
    wire(864, 464, 736, 464)
    wire(736, 464, 736, 544)
    wire(736, 544, 768, 544)

    wire(864, 560, 912, 560)
    wire(912, 560, 912, 496)
    wire(912, 560, 912, 624)
    wire(912, 496, 960, 496)
    xcc_end = cap_h(960, 496, "Cc", f"{PARAMS['Cc_pF']:.0f}p")
    wire(xcc_end, 496, 1104, 496)
    wire(912, 624, 944, 624)
    xrc_end = res_h(944, 624, "Rc", f"{PARAMS['Rc_Meg']:.0f}Meg")
    wire(xrc_end, 624, 1104, 624)
    wire(1104, 496, 1104, 624)
    wire(1104, 560, 1184, 560)
    wire(1184, 560, 1184, 336)

    # --- Stadio TIA (OPA656 ufficiale TI, +-5 V) ---
    wire(1184, 336, 1360, 336)
    flag(1216, 336, "v_minus")
    wire(1264, 336, 1264, 416)
    yc_in = cap_v(1264, 416, "Cin_ext", f"{PARAMS['Cin_ext_pF']:.2f}p")
    flag(1264, yc_in, "0")

    opamp2(1392, 288, "U3", "OPA656", "vcc5", "vee5")
    wire(1360, 368, 1360, 400)
    flag(1360, 400, "0")

    wire(1328, 336, 1328, 144)
    wire(1328, 240, 1360, 240)
    x_rf = res_h(1360, 240, "Rf", f"{PARAMS['Rf_tia_kohm']:.0f}k")
    wire(x_rf, 240, 1472, 240)
    wire(1328, 144, 1376, 144)
    x_cf = cap_h(1376, 144, "Cf", f"{PARAMS['Cf_pF']}p")
    wire(x_cf, 144, 1472, 144)
    wire(1472, 144, 1472, 352)
    wire(1424, 352, 1472, 352)
    flag(1504, 352, "v_tia")

    # --- Secondo Stadio Invertente G = -10 (AD817) ---
    wire(1472, 352, 1536, 352)
    xr1 = res_h(1536, 352, "R1", f"{PARAMS['R1_ohm']:.0f}")
    wire(xr1, 352, 1696, 352)
    opamp2(1728, 304, "U4", "AD817", "vcc", "vee")
    wire(1696, 384, 1696, 416)
    flag(1696, 416, "0")

    wire(1664, 352, 1664, 240)
    wire(1664, 240, 1696, 240)
    xr2 = res_h(1696, 240, "R2", f"{PARAMS['R2_ohm']/1e3:.0f}k")
    wire(xr2, 240, 1808, 240)
    wire(1760, 368, 1888, 368)
    wire(1808, 240, 1808, 368)
    flag(1888, 368, "v_out")

    # Direttiva SPICE posizionata fuori dall'area visiva del circuito (cosi il file .asc resta
    # immediatamente eseguibile cliccando Run in LTspice, senza sporcare lo schema!)
    phi_default_rad = np.deg2rad(-159.58)
    spice_directives = (
        f"!.lib OPA656.LIB\\n"
        f".lib TL082.LIB\\n"
        f".lib opamps_mems.lib\\n"
        f".options plotwinsize=0 reltol=1e-5 srcstepmethod=1 noopiter gminsteps=0\\n"
        f".param f0={PARAMS['f0_hz']:.0f} toff={PARAMS['toff_us']:.0f}u Vac={PARAMS['vac_v']} "
        f"phi={phi_default_rad:.6f} Vdc_in={PARAMS['vdc_in_v']}\\n"
        f".tran 0 42u 33u 2n"
    )
    texts.append(f"TEXT -256 1056 Left 0 {spice_directives}")

    content = "\n".join(lines + wires + flags + syms + texts) + "\n"
    with open(asc_path, "w") as f:
        f.write(content)


def parse_ltspice_raw(raw_path):
    """Legge il file binario .raw prodotto da LTspice su macOS (header UTF-16LE + dati binari)."""
    with open(raw_path, "rb") as f:
        blob = f.read()
    marker = "Binary:\n".encode("utf-16le")
    idx = blob.find(marker)
    if idx < 0:
        raise RuntimeError(f"Marker Binary non trovato in {raw_path}")
    header = blob[:idx].decode("utf-16le", errors="ignore")
    bin_data = blob[idx + len(marker):]

    n_vars = 0
    n_pts = 0
    var_names = []
    in_vars = False
    for line in header.splitlines():
        ls = line.strip()
        if ls.startswith("No. Variables:"):
            n_vars = int(ls.split(":")[1].strip())
        elif ls.startswith("No. Points:"):
            n_pts = int(ls.split(":")[1].strip())
        elif ls.startswith("Variables:"):
            in_vars = True
        elif in_vars:
            parts = ls.split()
            if len(parts) >= 2 and parts[0].isdigit():
                var_names.append(parts[1].lower())

    stride = 8 + 4 * (n_vars - 1)
    arr_u8 = np.frombuffer(bin_data[:n_pts * stride], dtype=np.uint8).reshape(n_pts, stride)
    out = {var_names[0]: np.abs(arr_u8[:, :8].copy().view(np.float64).ravel())}
    vals = arr_u8[:, 8:].copy().view(np.float32).reshape(n_pts, n_vars - 1)
    for i, name in enumerate(var_names[1:]):
        out[name] = vals[:, i]
    return out


def run_ltspice_case(cir_path, phi_deg):
    """Scrive la netlist .cir, lancia LTspice -b e restituisce i vettori simulati."""
    raw_path = cir_path.replace(".cir", ".raw")
    if os.path.exists(LTSPICE_BIN):
        netlist = build_spice_netlist(phi_deg=phi_deg)
        with open(cir_path, "w") as f:
            f.write(netlist)
        subprocess.run(
            [LTSPICE_BIN, "-b", cir_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    raw = parse_ltspice_raw(raw_path)
    # .tran 0 42u 20u 2n salva il tempo a partire da Tstart = 20 us -> toff (35 us) cade a 15 us nel .raw
    t_us = (raw["time"] - (PARAMS["toff_us"] - 20.0) * 1e-6) * 1e6 + PARAMS["t_freeze_us"]
    return {
        "t_us": t_us,
        "vin_mv": raw["v(vin)"] * 1e3,
        "vu2_mv": raw["v(v_u2)"] * 1e3,
        "vout_mv": raw["v(v_out)"] * 1e3,
    }


def _rot_pt(px, py, rot):
    if rot == "R0": return (px, py)
    if rot == "R90": return (-py, px)
    if rot == "R180": return (-px, -py)
    if rot == "R270": return (py, -px)
    if rot == "M0": return (-px, py)
    if rot == "M90": return (py, px)
    if rot == "M180": return (px, -py)
    if rot == "M270": return (-py, -px)
    raise ValueError(rot)


def render_asc_to_png(asc_path, out_png):
    """
    Renderizza direttamente il file schematico .asc utilizzando le primitive vettoriali
    originali dei simboli LTspice (.asy da lib.zip) e la palette colori dell'editor LTspice,
    mostrando ESCLUSIVAMENTE il circuito elettrico pulito (senza commenti ne direttive SPICE).
    """
    lib_zip = "/Applications/LTspice.app/Contents/Resources/lib.zip"
    zf = zipfile.ZipFile(lib_zip)

    def load_asy_geom(sym_name):
        rel = "lib/sym/" + sym_name.replace("\\", "/") + ".asy"
        for n in zf.namelist():
            if n.lower() == rel.lower():
                txt = zf.read(n).decode("latin1")
                break
        else:
            raise FileNotFoundError(rel)
        lines_g, circles_g = [], []
        for l in txt.splitlines():
            ls = l.strip()
            if ls.startswith("LINE "):
                p = ls.split()
                lines_g.append((int(p[2]), int(p[3]), int(p[4]), int(p[5])))
            elif ls.startswith("CIRCLE "):
                p = ls.split()
                circles_g.append((int(p[2]), int(p[3]), int(p[4]), int(p[5])))
        return lines_g, circles_g

    wires, flags, comps = [], [], []
    cur = None
    with open(asc_path) as f:
        for raw_l in f:
            ls = raw_l.rstrip("\r\n")
            if ls.startswith("WIRE "):
                _, x1, y1, x2, y2 = ls.split()
                wires.append(((int(x1), int(y1)), (int(x2), int(y2))))
            elif ls.startswith("FLAG "):
                _, x, y, nm = ls.split(None, 3)
                flags.append(((int(x), int(y)), nm))
            elif ls.startswith("SYMBOL "):
                _, sym, x, y, rot = ls.split()
                cur = {"sym": sym, "x": int(x), "y": int(y), "rot": rot, "inst": "", "val": ""}
                comps.append(cur)
            elif ls.startswith("SYMATTR InstName ") and cur is not None:
                cur["inst"] = ls.split(None, 2)[2]
            elif ls.startswith("SYMATTR Value ") and cur is not None:
                cur["val"] = ls.split(None, 2)[2]

    bg_color = "#e6e6e6"
    wire_color = "#000080"
    sym_color = "#000080"
    body_fill = "#ffffcc"
    inst_color = "#000000"

    fig, ax = plt.subplots(figsize=(17.2, 6.8), dpi=300)
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)

    gx, gy = np.meshgrid(np.arange(-352, 1984, 32), np.arange(32, 736, 32))
    ax.plot(gx.ravel(), gy.ravel(), ",", color="#bdbdbd", alpha=0.55, zorder=0)

    for (x1, y1), (x2, y2) in wires:
        ax.plot([x1, x2], [y1, y2], color=wire_color, linewidth=1.25, solid_capstyle="round", zorder=2)

    all_pts = []
    for p1, p2 in wires:
        all_pts.extend([p1, p2])
    junctions = set()
    for px, py in set(all_pts):
        deg = 0
        for (x1, y1), (x2, y2) in wires:
            if (px, py) == (x1, y1) or (px, py) == (x2, y2):
                deg += 1
            elif x1 == x2 == px and min(y1, y2) < py < max(y1, y2):
                deg += 2
            elif y1 == y2 == py and min(x1, x2) < px < max(x1, x2):
                deg += 2
        if deg >= 3:
            junctions.add((px, py))

    for jx, jy in junctions:
        ax.add_patch(patches.Rectangle((jx - 3.2, jy - 3.2), 6.4, 6.4, facecolor=wire_color, edgecolor="none", zorder=5))

    supply_bot_pins = set()
    for c in comps:
        lines_g, circles_g = load_asy_geom(c["sym"])
        cx, cy, rot = c["x"], c["y"], c["rot"]

        if "opamp" in c["sym"].lower():
            supply_bot_pins.add((cx, cy + 96))
            tri = [_rot_pt(-32, 32, rot), _rot_pt(-32, 96, rot), _rot_pt(32, 64, rot)]
            ax.add_patch(patches.Polygon([(cx + px, cy + py) for px, py in tri], closed=True,
                                         facecolor=body_fill, edgecolor="none", zorder=2.5))

        for x1, y1, x2, y2 in lines_g:
            rx1, ry1 = _rot_pt(x1, y1, rot)
            rx2, ry2 = _rot_pt(x2, y2, rot)
            ax.plot([cx + rx1, cx + rx2], [cy + ry1, cy + ry2], color=sym_color, linewidth=1.35, zorder=3)

        for x1, y1, x2, y2 in circles_g:
            rx1, ry1 = _rot_pt(x1, y1, rot)
            rx2, ry2 = _rot_pt(x2, y2, rot)
            ax.add_patch(patches.Ellipse((cx + 0.5 * (rx1 + rx2), cy + 0.5 * (ry1 + ry2)),
                                         abs(rx2 - rx1), abs(ry2 - ry1),
                                         facecolor=body_fill, edgecolor=sym_color, linewidth=1.35, zorder=2.8))

        pts_rot = [_rot_pt(x1, y1, rot) for x1, y1, _, _ in lines_g] + [_rot_pt(x2, y2, rot) for _, _, x2, y2 in lines_g]
        for x1, y1, x2, y2 in circles_g:
            pts_rot.extend([_rot_pt(x1, y1, rot), _rot_pt(x2, y2, rot)])
        xs_c = [cx + p[0] for p in pts_rot]
        ys_c = [cy + p[1] for p in pts_rot]
        xmin_c, xmax_c = min(xs_c), max(xs_c)
        ymin_c, ymax_c = min(ys_c), max(ys_c)
        xmid_c, ymid_c = 0.5 * (xmin_c + xmax_c), 0.5 * (ymin_c + ymax_c)

        if "opamp" in c["sym"].lower():
            ax.text(cx + 12, ymin_c + 10, c["inst"], fontsize=7.5, fontweight="bold", color=inst_color, ha="left", va="bottom", family="monospace")
            ax.text(cx + 12, ymax_c - 8, c["val"], fontsize=7.2, color=inst_color, ha="left", va="top", family="monospace")
        elif rot == "R90":
            ax.text(xmid_c, ymin_c - 5, c["inst"], fontsize=7.5, fontweight="bold", color=inst_color, ha="center", va="bottom", family="monospace")
            ax.text(xmid_c, ymax_c + 6, c["val"], fontsize=7.2, color=inst_color, ha="center", va="top", family="monospace")
        else:
            ax.text(xmax_c + 5, ymid_c - 9, c["inst"], fontsize=7.2, fontweight="bold", color=inst_color, ha="left", va="center", family="monospace")
            ax.text(xmax_c + 5, ymid_c + 11, c["val"], fontsize=6.8, color=inst_color, ha="left", va="center", family="monospace")

    for (fx, fy), nm in flags:
        if nm == "0":
            tri_g = [(fx - 12, fy), (fx + 12, fy), (fx, fy + 14), (fx - 12, fy)]
            ax.plot([p[0] for p in tri_g], [p[1] for p in tri_g], color=sym_color, linewidth=1.35, zorder=4)
        elif nm in ("vcc", "vee", "vcc5", "vee5"):
            is_bot = (fx, fy) in supply_bot_pins
            dy = +4 if is_bot else -4
            va = "top" if is_bot else "bottom"
            ax.plot([fx - 7, fx + 7], [fy, fy], color=wire_color, linewidth=1.2, zorder=4)
            ax.text(fx, fy + dy, nm, fontsize=6.6, color=wire_color, ha="center", va=va, family="monospace", fontweight="bold")
        else:
            ax.text(fx, fy - 6, nm, fontsize=7.5, color=wire_color, ha="center", va="bottom",
                    family="monospace", fontweight="bold",
                    bbox=dict(boxstyle="square,pad=0.08", facecolor=bg_color, edgecolor="none", alpha=0.88))

    ax.set_xlim(-352, 1950)
    ax.set_ylim(725, 42)
    ax.set_aspect("equal")
    ax.axis("off")

    plt.tight_layout(pad=0.2)
    plt.savefig(out_png, dpi=300, facecolor=bg_color, bbox_inches="tight")
    plt.close()


def main():
    # 1. Generazione schematico .asc + rendering pulito dello schematico LTspice
    asc_path = os.path.join(LTSPICE_DIR, "oscillazione_parassita.asc")
    build_ltspice_asc(asc_path)
    schema_png = os.path.join(OUT_DIR, "circuito_ltspice_schema.png")
    if os.path.exists("/Applications/LTspice.app/Contents/Resources/lib.zip"):
        render_asc_to_png(asc_path, schema_png)
    print(f"[OK] Schematico LTspice salvato in: {asc_path}")
    print(f"[OK] Immagine schematico LTspice generata in: {schema_png}")

    # 2. Esecuzione LTspice per i due casi sperimentali (scope_173: dv_in/dt > 0, scope_172: dv_in/dt < 0)
    cir_pos = os.path.join(LTSPICE_DIR, "oscillazione_parassita_dv_pos.cir")
    cir_neg = os.path.join(LTSPICE_DIR, "oscillazione_parassita_dv_neg.cir")

    sim_pos = run_ltspice_case(cir_pos, phi_deg=+40.80)
    sim_neg = run_ltspice_case(cir_neg, phi_deg=-159.58)

    # 3. Caricamento misure reali all'oscilloscopio
    d173 = np.genfromtxt(os.path.join(DATA_DIR, "scope_173.csv"), delimiter=",", skip_header=2)
    d172 = np.genfromtxt(os.path.join(DATA_DIR, "scope_172.csv"), delimiter=",", skip_header=2)

    for label, d, sim in [
        ("dv_in/dt > 0 (scope_173)", d173, sim_pos),
        ("dv_in/dt < 0 (scope_172)", d172, sim_neg),
    ]:
        t_sc = d[:, 0] * 1e6
        v_sc = d[:, 1] * 1e3
        m_w = (t_sc >= -1.5) & (t_sc <= 4.0)
        v_lt_i = np.interp(t_sc[m_w], sim["t_us"], sim["vout_mv"])
        rms = np.sqrt(np.mean((v_lt_i - v_sc[m_w]) ** 2))
        m_p_lt = sim["t_us"] > 0
        m_p_sc = t_sc > 0
        print(f"=== {label} ===")
        print(f"  Misura reale : Vmax = {v_sc[m_p_sc].max():+6.1f} mV ({t_sc[m_p_sc][v_sc[m_p_sc].argmax()]:.2f} us), "
              f"Vmin = {v_sc[m_p_sc].min():+6.1f} mV ({t_sc[m_p_sc][v_sc[m_p_sc].argmin()]:.2f} us)")
        print(f"  LTspice      : Vmax = {sim['vout_mv'][m_p_lt].max():+6.1f} mV ({sim['t_us'][m_p_lt][sim['vout_mv'][m_p_lt].argmax()]:.2f} us), "
              f"Vmin = {sim['vout_mv'][m_p_lt].min():+6.1f} mV ({sim['t_us'][m_p_lt][sim['vout_mv'][m_p_lt].argmin()]:.2f} us)")
        print(f"  Errore RMS su [-1.5, +4.0] us: {rms:.2f} mV")

    # 4. Verifica in LTspice dei valori estremi di V_pp(phi) a phi = 0 deg e phi = +-90 deg
    if os.path.exists(LTSPICE_BIN):
        tmp_cir = os.path.join(LTSPICE_DIR, "_tmp_sweep.cir")
        for ph_test in [-90.0, 0.0, 90.0, 180.0]:
            s_ph = run_ltspice_case(tmp_cir, phi_deg=ph_test)
            mp = (s_ph["t_us"] >= 0.0) & (s_ph["t_us"] <= 4.0)
            vpp = s_ph["vout_mv"][mp].max() - s_ph["vout_mv"][mp].min()
            print(f"  LTspice V_pp(phi = {ph_test:+6.1f} deg) = {vpp:.1f} mV")
        for ext in [".cir", ".raw", ".op.raw", ".log"]:
            p_rm = tmp_cir.replace(".cir", ext)
            if os.path.exists(p_rm):
                os.remove(p_rm)

    # 5. Generazione grafico editoriale (300 DPI) coerente con lo stile della relazione
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 11,
        "axes.labelsize": 11.5,
        "axes.titlesize": 12,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "lines.linewidth": 1.8,
        "grid.alpha": 0.35,
        "grid.linestyle": "--",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
    })

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.2, 5.4), dpi=300, sharey=True)

    # Pannello sinistro: dv_in/dt > 0 (scope_173)
    ax1.plot(d173[:, 0] * 1e6, d173[:, 1] * 1e3, color="#495057", alpha=0.58, linewidth=2.3,
             label="Misura sperimentale")
    ax1.plot(sim_pos["t_us"], sim_pos["vout_mv"], color="#c92a2a", linewidth=2.0,
             label="Simulazione LTspice")
    ax1.axvline(0.0, color="black", linestyle="--", linewidth=1.2, alpha=0.75, label="Gate OFF")
    ax1.axhline(0.0, color="black", linestyle=":", linewidth=0.8, alpha=0.5)
    ax1.set_xlim(-1.0, 4.0)
    ax1.set_ylim(-750, 920)
    ax1.set_xlabel(r"Tempo [$\mu$s]")
    ax1.set_ylabel(r"Tensione di uscita $v_{\mathrm{out}}(t)$ [mV]")
    ax1.set_title(r"Spegnimento del gate quando $\frac{dv_{\mathrm{in}}}{dt} > 0$", pad=9)
    ax1.grid(True)
    ax1.legend(loc="upper right", frameon=True, facecolor="white", framealpha=0.92, edgecolor="#ced4da")

    # Pannello destro: dv_in/dt < 0 (scope_172)
    ax2.plot(d172[:, 0] * 1e6, d172[:, 1] * 1e3, color="#495057", alpha=0.58, linewidth=2.3,
             label="Misura sperimentale")
    ax2.plot(sim_neg["t_us"], sim_neg["vout_mv"], color="#1971c2", linewidth=2.0,
             label="Simulazione LTspice")
    ax2.axvline(0.0, color="black", linestyle="--", linewidth=1.2, alpha=0.75, label="Gate OFF")
    ax2.axhline(0.0, color="black", linestyle=":", linewidth=0.8, alpha=0.5)
    ax2.set_xlim(-1.0, 4.0)
    ax2.set_xlabel(r"Tempo [$\mu$s]")
    ax2.set_title(r"Spegnimento del gate quando $\frac{dv_{\mathrm{in}}}{dt} < 0$", pad=9)
    ax2.grid(True)
    ax2.legend(loc="upper right", frameon=True, facecolor="white", framealpha=0.92, edgecolor="#ced4da")

    plt.tight_layout()
    out_png = os.path.join(OUT_DIR, "simulazione_ltspice_confronto.png")
    plt.savefig(out_png, bbox_inches="tight")
    plt.close()
    print(f"[OK] Grafico LTspice generato: {out_png}")


if __name__ == "__main__":
    main()
