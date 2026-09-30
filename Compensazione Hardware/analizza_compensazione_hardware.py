"""
Analisi della Risposta in Frequenza con Compensazione Hardware del MEMS

Questo script:
1. Carica i dati delle misure con circuito di compensazione hardware:
   - '1'  : prima taratura di compensazione hardware a Vdc attivo.
   - '2'  : seconda taratura ottimizzata di compensazione hardware a Vdc attivo.
   - 'Off': misura a Vdc = 0 V (MEMS spento / elettrostaticamente inattivo) a larga banda (20 kHz),
            che rivela la pura funzione di trasferimento di cancellazione capacitiva (notch di -20 dB).
2. Pulisce la fase sperimentale:
   - Rimuove i campioni iniziali a sinistra con fase bloccata a -8.9° (timeout trigger dell'oscilloscopio a basso segnale).
   - Taglia simmetricamente i campioni a destra della risonanza per centrare la finestra di sweep attorno al picco motrice.
   - Corregge l'artifizio di wrap a +-180° nella misura 'Off', evidenziando la zona di basso SNR e il salto di fase di 180°.
3. Carica i dati non compensati da 'Risposta in frequenza' per il confronto diretto prima/dopo compensazione hardware.
4. Esegue il fit del modello elettromeccanico RLC sui dati centrati e ripuliti.
5. Genera tutti i grafici ad alta risoluzione (300 DPI) con stile minimale, colori curati,
   punti sperimentali semitrasparenti e curve teoriche continue al 100% di opacità,
   rigorosamente in sentence case e senza grassetto.
"""

import os
import glob
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.signal import medfilt

# -----------------------------------------------------------------------------
# 1. Configurazione percorsi e parametri del circuito
# -----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR  = os.path.join(BASE_DIR, 'grafici')
os.makedirs(OUT_DIR, exist_ok=True)

# Percorso dati non compensati di confronto
ROOT_DIR = os.path.dirname(BASE_DIR)
DIR_NON_COMP = os.path.join(ROOT_DIR, 'Risposta in frequenza', 'frequenza')
FILE_MOD_NON_COMP = os.path.join(DIR_NON_COMP, 'modulo_VDC_05p0V_417820Hz_501pt_20260916_171901.csv')
FILE_FAS_NON_COMP = os.path.join(DIR_NON_COMP, 'fase_VDC_05p0V_417820Hz_501pt_20260916_171901.csv')

# Parametri front-end di misura
Rf = 500e3         # Resistenza di retroazione TIA [Ohm]
G2 = 10.0          # Guadagno stadio invertente (R2/R1 = 1k / 100)
G_tot = Rf * G2    # Guadagno totale di transimpedenza = 5.0e6 V/A

# Stile tipografico standard del progetto (senza grassetto, solo sentence case)
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.labelsize': 11.5,
    'axes.titlesize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'grid.alpha': 0.35,
    'grid.linestyle': '--'
})

COLOR_MOD    = '#1971c2'  # Blu brillante
COLOR_FASE   = '#e8590c'  # Arancione / Corallo
COLOR_SET1   = '#d6336c'  # Magenta intenso
COLOR_SET2   = '#1971c2'  # Blu primario
COLOR_OFF    = '#495057'  # Grigio antracite
COLOR_UNCOMP = '#868e96'  # Grigio medio
COLOR_FIT    = '#1864ab'  # Blu scuro continuo

# -----------------------------------------------------------------------------
# 2. Caricamento e pulizia dati con filtraggio asimmetrie e blocco fase
# -----------------------------------------------------------------------------
def load_and_clean_dataset(folder_name, f_min=None, f_max=None):
    """Carica i dati, converte la fase in [-180, 180], elimina dropout e applica il ritaglio centrato."""
    fdir = os.path.join(BASE_DIR, folder_name)
    mod_files = glob.glob(os.path.join(fdir, 'modulo_*.csv'))
    fas_files = glob.glob(os.path.join(fdir, 'fase_*.csv'))
    if not mod_files or not fas_files:
        raise FileNotFoundError(f"File CSV non trovati in {fdir}")
    
    d_m = np.loadtxt(mod_files[0], delimiter=',', skiprows=2)
    d_p = np.loadtxt(fas_files[0], delimiter=',', skiprows=2)
    
    f_hz = d_m[:, 0]
    f_khz = f_hz / 1e3
    vin = d_m[:, 1]
    vout = d_m[:, 2]
    gain_lin = d_m[:, 3]
    gain_db = d_m[:, 4]
    
    raw_phase = d_p[:, 1]
    phase_wrap = (raw_phase + 180.0) % 360.0 - 180.0
    
    # Pulizia dropout isolati dell'oscilloscopio sulla fase
    phase_clean = np.copy(phase_wrap)
    if folder_name in ['1', '2']:
        p_med = medfilt(phase_wrap, 5)
        # I punti a -8.9° isolati mentre i vicini sono a fase alta (> 10°) sono dropout
        dropout = (np.abs(phase_wrap - (-8.9)) < 1.5) & (p_med > 10.0)
        phase_clean[dropout] = p_med[dropout]
    
    # Taglio centrato attorno alla risonanza se specificato
    if f_min is not None and f_max is not None:
        mask = (f_khz >= f_min) & (f_khz <= f_max)
    else:
        mask = np.ones(len(f_khz), dtype=bool)
        
    return {
        'folder': folder_name,
        'f_hz': f_hz[mask],
        'f_khz': f_khz[mask],
        'vin': vin[mask],
        'vout': vout[mask],
        'gain_lin': gain_lin[mask],
        'gain_db': gain_db[mask],
        'phase_clean': phase_clean[mask],
        'f_all_khz': f_khz,
        'gain_all_db': gain_db,
        'gain_all_lin': gain_lin,
        'phase_all_clean': phase_clean
    }

print("Caricamento e pulizia dataset...")

# Set 2: picco a 417.754 kHz. Rimosso blocco fase a sx (< 417.535 kHz), taglio leggero a dx a 418.100 kHz (tagliati solo 25 campioni rumorosi)
data_2 = load_and_clean_dataset('2', f_min=417.535, f_max=418.100)

# Set 1: picco a 417.770 kHz. Rimosso blocco fase a sx (< 417.540 kHz), taglio leggero a dx a 418.100 kHz (tagliati solo 15 campioni prima dei glitch)
data_1 = load_and_clean_dataset('1', f_min=417.540, f_max=418.100)

# Off: intera banda da 407.75 a 427.75 kHz
data_off = load_and_clean_dataset('Off')

# Correzione wrap di fase a +-180° per la misura Off:
# Per f > 418.55 kHz la fase passa a circa +165°, quindi i punti a -175° vanno traslati di +360° per evitare salti grafici
p_off_corr = np.copy(data_off['phase_clean'])
for i in range(len(data_off['f_khz'])):
    if data_off['f_khz'][i] > 418.55 and p_off_corr[i] < -100.0:
        p_off_corr[i] += 360.0
data_off['phase_corr'] = p_off_corr

# Caricamento dataset non compensato di confronto
has_uncomp = os.path.exists(FILE_MOD_NON_COMP) and os.path.exists(FILE_FAS_NON_COMP)
if has_uncomp:
    d_unc_m = np.loadtxt(FILE_MOD_NON_COMP, delimiter=',', skiprows=2)
    d_unc_f = np.loadtxt(FILE_FAS_NON_COMP, delimiter=',', skiprows=2)
    data_uncomp = {
        'f_hz': d_unc_m[:, 0],
        'f_khz': d_unc_m[:, 0] / 1e3,
        'gain_lin': d_unc_m[:, 3],
        'gain_db': d_unc_m[:, 4],
        'phase_wrap': (d_unc_f[:, 1] + 180.0) % 360.0 - 180.0
    }
    print("[OK] Dati non compensati di confronto caricati correttamente.")

# -----------------------------------------------------------------------------
# 3. Fit del modello fisico RLC + feedthrough residuo sui dati centrati
# -----------------------------------------------------------------------------
def model_mag(f_arr, C_re, C_im, A_mot, f0, Q, phi_m):
    x = 2.0 * Q * (f_arr - f0) / f0
    mot = (A_mot * np.exp(1j * phi_m)) / (1.0 + 1j * x)
    T = (C_re + 1j * C_im) + mot
    return np.abs(T)

def model_phase(f_arr, f0, Q, phi_mid, span_deg):
    x = 2.0 * Q * (f_arr - f0) / f0
    return phi_mid - (span_deg / np.pi) * np.arctan(x)

def fit_resonator(dataset):
    f_hz = dataset['f_hz']
    g_lin = dataset['gain_lin']
    p_clean = dataset['phase_clean']
    f0_guess = f_hz[np.argmax(g_lin)]
    A_guess = np.ptp(g_lin)
    base_lin = np.min(g_lin)
    p0 = [base_lin, 0.0, A_guess, f0_guess, 2200.0, 0.0]
    
    popt, _ = curve_fit(model_mag, f_hz, g_lin, p0=p0, maxfev=50000)
    C_re, C_im, A_mot, f0_fit, Q_fit, phi_m = popt
    C_feed = np.hypot(C_re, C_im)
    
    delta_C_fF = (C_feed / (2.0 * np.pi * f0_fit * G_tot)) * 1e15
    
    # Fit teorico della fase con transizione arctan
    p0_phase = [f0_fit, Q_fit, -30.0, 180.0]
    try:
        popt_phase, _ = curve_fit(model_phase, f_hz, p_clean, p0=p0_phase, maxfev=10000)
    except Exception:
        popt_phase = p0_phase
    
    # Griglia densa per linea continua
    f_dense = np.linspace(f_hz[0], f_hz[-1], 1000)
    x_dense = 2.0 * Q_fit * (f_dense - f0_fit) / f0_fit
    T_dense = (C_re + 1j * C_im) + (A_mot * np.exp(1j * phi_m)) / (1.0 + 1j * x_dense)
    g_dense_db = 20.0 * np.log10(np.abs(T_dense))
    p_dense_deg = model_phase(f_dense, *popt_phase)
    
    return {
        'popt': popt,
        'popt_phase': popt_phase,
        'f0_fit': f0_fit,
        'Q_fit': Q_fit,
        'A_mot': A_mot,
        'C_feed': C_feed,
        'C_feed_db': 20.0 * np.log10(C_feed),
        'delta_C_fF': delta_C_fF,
        'f_dense': f_dense,
        'f_dense_khz': f_dense / 1e3,
        'g_dense_db': g_dense_db,
        'p_dense_deg': p_dense_deg,
        'T_dense': T_dense
    }

fit_res_1 = fit_resonator(data_1)
fit_res_2 = fit_resonator(data_2)

print("=" * 70)
print("RISULTATI FIT RISPOSTA IN FREQUENZA (DATI CENTRATI E RIPULITI)")
print(f"Set 1: f0 = {fit_res_1['f0_fit']:.2f} Hz | Q = {fit_res_1['Q_fit']:.1f} | A_mot = {fit_res_1['A_mot']:.4f}")
print(f"       Feedthrough residuo: {fit_res_1['C_feed']:.4f} ({fit_res_1['C_feed_db']:.2f} dB) -> Delta C = {fit_res_1['delta_C_fF']:.2f} fF")
print(f"Set 2: f0 = {fit_res_2['f0_fit']:.2f} Hz | Q = {fit_res_2['Q_fit']:.1f} | A_mot = {fit_res_2['A_mot']:.4f}")
print(f"       Feedthrough residuo: {fit_res_2['C_feed']:.4f} ({fit_res_2['C_feed_db']:.2f} dB) -> Delta C = {fit_res_2['delta_C_fF']:.2f} fF")
print("=" * 70)

# -----------------------------------------------------------------------------
# GRAFICO 1: Bode completo a 2 pannelli - Set 1 (centrato)
# -----------------------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.8, 7.0), sharex=True, dpi=300)

ax1.plot(data_1['f_khz'], data_1['gain_db'], 'o', color=COLOR_MOD, alpha=0.45, markersize=3.2, label='Punti sperimentali')
ax1.plot(fit_res_1['f_dense_khz'], fit_res_1['g_dense_db'], color=COLOR_FIT, linewidth=2.0, label='Fit')
ax1.set_ylabel('Guadagno [dB]')
ax1.set_title('Risposta in frequenza con compensazione hardware - Set 1', pad=9)
ax1.grid(True)
ax1.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
ax1.ticklabel_format(useOffset=False, style='plain')
ax1.set_xlim(data_1['f_khz'][0], data_1['f_khz'][-1])

ax2.plot(data_1['f_khz'], data_1['phase_clean'], 'o', color=COLOR_FASE, alpha=0.45, markersize=3.2, label='Punti sperimentali')
ax2.plot(fit_res_1['f_dense_khz'], fit_res_1['p_dense_deg'], color='#d9480f', linewidth=2.0, label='Fit')
ax2.set_xlabel(r'Frequenza $f_{in}$ [kHz]')
ax2.set_ylabel('Fase [°]')
ax2.grid(True)
ax2.legend(loc='lower left', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
ax2.ticklabel_format(useOffset=False, style='plain')
ax2.set_xlim(data_1['f_khz'][0], data_1['f_khz'][-1])

plt.tight_layout()
p_set1 = os.path.join(OUT_DIR, 'bode_set1.png')
plt.savefig(p_set1)
plt.close()
print(f"[OK] Grafico salvato: {p_set1}")

# -----------------------------------------------------------------------------
# GRAFICO 2: Bode completo a 2 pannelli - Set 2 (centrato e ottimizzato)
# -----------------------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.8, 7.0), sharex=True, dpi=300)

ax1.plot(data_2['f_khz'], data_2['gain_db'], 'o', color=COLOR_MOD, alpha=0.45, markersize=3.2, label='Punti sperimentali')
ax1.plot(fit_res_2['f_dense_khz'], fit_res_2['g_dense_db'], color=COLOR_FIT, linewidth=2.0, label='Fit')
ax1.set_ylabel('Guadagno [dB]')
ax1.set_title('Risposta in frequenza con compensazione hardware', pad=9)
ax1.grid(True)
ax1.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
ax1.ticklabel_format(useOffset=False, style='plain')
ax1.set_xlim(data_2['f_khz'][0], data_2['f_khz'][-1])

ax2.plot(data_2['f_khz'], data_2['phase_clean'], 'o', color=COLOR_FASE, alpha=0.45, markersize=3.2, label='Punti sperimentali')
ax2.plot(fit_res_2['f_dense_khz'], fit_res_2['p_dense_deg'], color='#d9480f', linewidth=2.0, label='Fit')
ax2.set_xlabel(r'Frequenza $f_{in}$ [kHz]')
ax2.set_ylabel('Fase [°]')
ax2.grid(True)
ax2.legend(loc='lower left', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
ax2.ticklabel_format(useOffset=False, style='plain')
ax2.set_xlim(data_2['f_khz'][0], data_2['f_khz'][-1])

plt.tight_layout()
p_set2 = os.path.join(OUT_DIR, 'bode_set2.png')
plt.savefig(p_set2)
plt.close()
print(f"[OK] Grafico salvato: {p_set2}")

# -----------------------------------------------------------------------------
# GRAFICO 3: Bode completo a 2 pannelli - Off (Vdc = 0 V, pura cancellazione capacitiva)
# -----------------------------------------------------------------------------
from scipy.interpolate import UnivariateSpline

spl_off = UnivariateSpline(data_off['f_khz'], data_off['gain_db'], s=25.0)
f_off_dense = np.linspace(data_off['f_khz'][0], data_off['f_khz'][-1], 600)
g_off_fit = spl_off(f_off_dense)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.8, 7.0), sharex=True, dpi=300)

# Modulo: punti sperimentali e fit, senza linee di collegamento né testi superflui
ax1.plot(data_off['f_khz'], data_off['gain_db'], 'o', color='#1971c2', alpha=0.45, markersize=3.0, label='Punti sperimentali')
ax1.plot(f_off_dense, g_off_fit, '-', color='#1864ab', linewidth=2.0, label='Fit')
ax1.set_ylabel('Guadagno [dB]')
ax1.set_title(r'Funzione di trasferimento del circuito di compensazione hardware ($V_{dc} = 0$ V)', pad=9)
ax1.grid(True)
ax1.legend(loc='lower left', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
ax1.ticklabel_format(useOffset=False, style='plain')
ax1.set_xlim(data_off['f_khz'][0], data_off['f_khz'][-1])

# Fase: tutti i punti dello stesso colore, senza asintoti, senza bande, solo "Punti sperimentali"
ax2.plot(data_off['f_khz'], data_off['phase_corr'], 'o', color=COLOR_FASE, alpha=0.45, markersize=3.0, label='Punti sperimentali')
ax2.set_xlabel(r'Frequenza $f_{in}$ [kHz]')
ax2.set_ylabel('Fase [°]')
ax2.grid(True)
ax2.legend(loc='center right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
ax2.ticklabel_format(useOffset=False, style='plain')
ax2.set_xlim(data_off['f_khz'][0], data_off['f_khz'][-1])

plt.tight_layout()
p_off = os.path.join(OUT_DIR, 'bode_off.png')
plt.savefig(p_off)
plt.close()
print(f"[OK] Grafico salvato: {p_off}")

# -----------------------------------------------------------------------------
# GRAFICI SINGOLI (Modulo e Fase separati per Set 1, Set 2 e Off)
# -----------------------------------------------------------------------------
# Set 1 - Solo modulo
fig, ax = plt.subplots(figsize=(8.8, 5.5), dpi=300)
ax.plot(data_1['f_khz'], data_1['gain_db'], 'o', color=COLOR_MOD, alpha=0.45, markersize=3.2, label='Punti sperimentali')
ax.plot(fit_res_1['f_dense_khz'], fit_res_1['g_dense_db'], color=COLOR_FIT, linewidth=2.0, label='Fit')
ax.set_xlabel(r'Frequenza $f_{in}$ [kHz]')
ax.set_ylabel('Guadagno [dB]')
ax.set_title('Modulo della risposta in frequenza - Set 1', pad=9)
ax.grid(True)
ax.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
ax.ticklabel_format(useOffset=False, style='plain')
ax.set_xlim(data_1['f_khz'][0], data_1['f_khz'][-1])
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, 'bode_set1_modulo.png'))
plt.close()

# Set 1 - Solo fase
fig, ax = plt.subplots(figsize=(8.8, 5.5), dpi=300)
ax.plot(data_1['f_khz'], data_1['phase_clean'], 'o', color=COLOR_FASE, alpha=0.45, markersize=3.2, label='Punti sperimentali')
ax.plot(fit_res_1['f_dense_khz'], fit_res_1['p_dense_deg'], color='#d9480f', linewidth=2.0, label='Fit')
ax.set_xlabel(r'Frequenza $f_{in}$ [kHz]')
ax.set_ylabel('Fase [°]')
ax.set_title('Fase della risposta in frequenza - Set 1', pad=9)
ax.grid(True)
ax.legend(loc='lower left', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
ax.ticklabel_format(useOffset=False, style='plain')
ax.set_xlim(data_1['f_khz'][0], data_1['f_khz'][-1])
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, 'bode_set1_fase.png'))
plt.close()

# Set 2 - Solo modulo
fig, ax = plt.subplots(figsize=(8.8, 5.5), dpi=300)
ax.plot(data_2['f_khz'], data_2['gain_db'], 'o', color=COLOR_MOD, alpha=0.45, markersize=3.2, label='Punti sperimentali')
ax.plot(fit_res_2['f_dense_khz'], fit_res_2['g_dense_db'], color=COLOR_FIT, linewidth=2.0, label='Fit')
ax.set_xlabel(r'Frequenza $f_{in}$ [kHz]')
ax.set_ylabel('Guadagno [dB]')
ax.set_title('Modulo della risposta in frequenza con compensazione hardware', pad=9)
ax.grid(True)
ax.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
ax.ticklabel_format(useOffset=False, style='plain')
ax.set_xlim(data_2['f_khz'][0], data_2['f_khz'][-1])
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, 'bode_set2_modulo.png'))
plt.close()

# Set 2 - Solo fase
fig, ax = plt.subplots(figsize=(8.8, 5.5), dpi=300)
ax.plot(data_2['f_khz'], data_2['phase_clean'], 'o', color=COLOR_FASE, alpha=0.45, markersize=3.2, label='Punti sperimentali')
ax.plot(fit_res_2['f_dense_khz'], fit_res_2['p_dense_deg'], color='#d9480f', linewidth=2.0, label='Fit')
ax.set_xlabel(r'Frequenza $f_{in}$ [kHz]')
ax.set_ylabel('Fase [°]')
ax.set_title('Fase della risposta in frequenza con compensazione hardware', pad=9)
ax.grid(True)
ax.legend(loc='lower left', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
ax.ticklabel_format(useOffset=False, style='plain')
ax.set_xlim(data_2['f_khz'][0], data_2['f_khz'][-1])
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, 'bode_set2_fase.png'))
plt.close()

# Off - Solo modulo
fig, ax = plt.subplots(figsize=(8.8, 5.5), dpi=300)
ax.plot(data_off['f_khz'], data_off['gain_db'], 'o', color='#1971c2', alpha=0.45, markersize=3.0, label='Punti sperimentali')
ax.plot(f_off_dense, g_off_fit, '-', color='#1864ab', linewidth=2.0, label='Fit')
ax.set_xlabel(r'Frequenza $f_{in}$ [kHz]')
ax.set_ylabel('Guadagno [dB]')
ax.set_title(r'Modulo della cancellazione di feedthrough ($V_{dc} = 0$ V)', pad=9)
ax.grid(True)
ax.legend(loc='lower left', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
ax.ticklabel_format(useOffset=False, style='plain')
ax.set_xlim(data_off['f_khz'][0], data_off['f_khz'][-1])
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, 'bode_off_modulo.png'))
plt.close()

# -----------------------------------------------------------------------------
# GRAFICO 4: Confronto diretto Set 1 vs Set 2 (dati centrati)
# -----------------------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.8, 7.0), sharex=True, dpi=300)

common_min = max(data_1['f_khz'][0], data_2['f_khz'][0])
common_max = min(data_1['f_khz'][-1], data_2['f_khz'][-1])

m1_c = (data_1['f_khz'] >= common_min) & (data_1['f_khz'] <= common_max)
m2_c = (data_2['f_khz'] >= common_min) & (data_2['f_khz'] <= common_max)

ax1.plot(data_1['f_khz'][m1_c], data_1['gain_db'][m1_c], 'o', color=COLOR_SET1, alpha=0.40, markersize=2.8, label='Set 1 (taratura iniziale)')
ax1.plot(fit_res_1['f_dense_khz'], fit_res_1['g_dense_db'], color=COLOR_SET1, linewidth=1.8, label='Fit Set 1')
ax1.plot(data_2['f_khz'][m2_c], data_2['gain_db'][m2_c], 'o', color=COLOR_SET2, alpha=0.45, markersize=2.8, label='Set 2 (taratura ottimizzata)')
ax1.plot(fit_res_2['f_dense_khz'], fit_res_2['g_dense_db'], color=COLOR_SET2, linewidth=2.0, label='Fit Set 2')
ax1.set_ylabel('Guadagno [dB]')
ax1.set_title('Confronto risposta in frequenza: taratura Set 1 vs Set 2', pad=9)
ax1.grid(True)
ax1.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
ax1.ticklabel_format(useOffset=False, style='plain')
ax1.set_xlim(common_min, common_max)

ax2.plot(data_1['f_khz'][m1_c], data_1['phase_clean'][m1_c], 'o', color=COLOR_SET1, alpha=0.35, markersize=2.8, label='Fase Set 1')
ax2.plot(data_2['f_khz'][m2_c], data_2['phase_clean'][m2_c], 'o', color=COLOR_SET2, alpha=0.45, markersize=2.8, label='Fase Set 2')
ax2.set_xlabel(r'Frequenza $f_{in}$ [kHz]')
ax2.set_ylabel('Fase [°]')
ax2.grid(True)
ax2.legend(loc='lower left', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
ax2.ticklabel_format(useOffset=False, style='plain')
ax2.set_xlim(common_min, common_max)

plt.tight_layout()
p_comp_12 = os.path.join(OUT_DIR, 'confronto_set1_vs_set2.png')
plt.savefig(p_comp_12)
plt.close()
print(f"[OK] Grafico salvato: {p_comp_12}")

# -----------------------------------------------------------------------------
# GRAFICO 5: Confronto modulo di tutte e tre le configurazioni (Set 1, Set 2, Off)
# -----------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8.8, 5.5), dpi=300)

m_off_band = (data_off['f_khz'] >= common_min) & (data_off['f_khz'] <= common_max)

ax.plot(data_off['f_khz'][m_off_band], data_off['gain_db'][m_off_band], 's-', color='#868e96',
        alpha=0.75, markersize=3.5, linewidth=1.2, label=r'Off ($V_{dc} = 0$ V, solo feedthrough compensato)')
ax.plot(data_1['f_khz'][m1_c], data_1['gain_db'][m1_c], 'o', color=COLOR_SET1, alpha=0.40, markersize=2.8, label='Set 1 (Vdc ON, prima taratura)')
ax.plot(fit_res_1['f_dense_khz'], fit_res_1['g_dense_db'], color=COLOR_SET1, linewidth=1.6)
ax.plot(data_2['f_khz'][m2_c], data_2['gain_db'][m2_c], 'o', color=COLOR_SET2, alpha=0.45, markersize=2.8, label='Set 2 (Vdc ON, taratura fine)')
ax.plot(fit_res_2['f_dense_khz'], fit_res_2['g_dense_db'], color=COLOR_SET2, linewidth=2.0)

ax.set_xlabel(r'Frequenza $f_{in}$ [kHz]')
ax.set_ylabel('Guadagno [dB]')
ax.set_title('Confronto modulo: Set 1, Set 2 e livello base Off attorno alla risonanza', pad=9)
ax.grid(True)
ax.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
ax.ticklabel_format(useOffset=False, style='plain')
ax.set_xlim(common_min, common_max)
plt.tight_layout()
p_mod_all = os.path.join(OUT_DIR, 'confronto_modulo_tutti.png')
plt.savefig(p_mod_all)
plt.close()
print(f"[OK] Grafico salvato: {p_mod_all}")

# -----------------------------------------------------------------------------
# GRAFICO 6: Benchmark fondamentale - Con vs Senza compensazione hardware
# -----------------------------------------------------------------------------
if has_uncomp:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.8, 7.2), sharex=True, dpi=300)
    
    m_unc = (data_uncomp['f_khz'] >= data_2['f_khz'][0]) & (data_uncomp['f_khz'] <= data_2['f_khz'][-1])
    
    # Modulo
    ax1.plot(data_uncomp['f_khz'][m_unc], data_uncomp['gain_db'][m_unc], 'o', color='#868e96',
             alpha=0.45, markersize=2.6, label='Non compensato (misura reale, dominata da Cp)')
    ax1.plot(data_2['f_khz'], data_2['gain_db'], 'o', color='#2b8a3e',
             alpha=0.45, markersize=2.8, label=r'Compensazione hardware (Set 2, $\Delta C \approx 12.9$ fF)')
    ax1.plot(fit_res_2['f_dense_khz'], fit_res_2['g_dense_db'], color='#2b8a3e', linewidth=2.0, label='Fit risonanza motrice')
    
    # Freccia verticale di abbattimento feedthrough
    delta_feed_db = data_uncomp['gain_db'][0] - fit_res_2['C_feed_db']
    ax1.annotate('', xy=(417.55, 21.0), xytext=(417.55, -15.0),
                 arrowprops=dict(arrowstyle='<->', color='#2b8a3e', lw=2.0))
    ax1.text(417.57, 3.0,
             f'Abbattimento feedthrough:\n-{delta_feed_db:.1f} dB ({data_uncomp["gain_lin"][0]/fit_res_2["C_feed"]:.0f}×)',
             fontsize=10, bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='#2b8a3e', alpha=0.95))
    
    ax1.set_ylabel('Guadagno [dB]')
    ax1.set_title('Efficacia della compensazione hardware: risposta grezza vs compensata', pad=9)
    ax1.grid(True)
    ax1.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
    ax1.ticklabel_format(useOffset=False, style='plain')
    ax1.set_xlim(data_2['f_khz'][0], data_2['f_khz'][-1])
    
    # Fase
    ax2.plot(data_uncomp['f_khz'][m_unc], data_uncomp['phase_wrap'][m_unc], 'o', color='#868e96',
             alpha=0.45, markersize=2.6, label='Non compensato (fase bloccata a +68° da Cp)')
    ax2.plot(data_2['f_khz'], data_2['phase_clean'], 'o', color='#7048e8',
             alpha=0.45, markersize=2.8, label='Compensato hardware (transizione motrice di 180°)')
    ax2.set_xlabel(r'Frequenza $f_{in}$ [kHz]')
    ax2.set_ylabel('Fase [°]')
    ax2.grid(True)
    ax2.legend(loc='lower left', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
    ax2.ticklabel_format(useOffset=False, style='plain')
    ax2.set_xlim(data_2['f_khz'][0], data_2['f_khz'][-1])
    
    plt.tight_layout()
    p_bench = os.path.join(OUT_DIR, 'confronto_con_senza_compensazione.png')
    plt.savefig(p_bench)
    plt.close()
    print(f"[OK] Grafico salvato: {p_bench}")

# -----------------------------------------------------------------------------
# GRAFICO 7: Confronto tra compensazione Hardware e Software
# -----------------------------------------------------------------------------
if has_uncomp:
    fig, ax = plt.subplots(figsize=(8.8, 5.5), dpi=300)
    
    T_raw = data_uncomp['gain_lin'] * np.exp(1j * np.deg2rad(data_uncomp['phase_wrap']))
    C_feed_raw = 4.27 + 1j * 10.90
    T_comp_soft = T_raw - C_feed_raw
    gain_comp_soft_lin = np.abs(T_comp_soft)
    
    m_unc = (data_uncomp['f_khz'] >= data_2['f_khz'][0]) & (data_uncomp['f_khz'] <= data_2['f_khz'][-1])
    
    ax.plot(data_uncomp['f_khz'][m_unc], gain_comp_soft_lin[m_unc], 'o', color='#7048e8',
            alpha=0.45, markersize=2.8, label=r'Compensazione software (sottrazione vettoriale di $C_p$)')
    ax.plot(data_2['f_khz'], data_2['gain_lin'], 'o', color='#2b8a3e',
            alpha=0.55, markersize=2.8, label=r'Compensazione hardware reale (Set 2)')
    ax.plot(fit_res_2['f_dense_khz'], np.abs(fit_res_2['T_dense']), color='#2b8a3e',
            linewidth=2.0, label='Fit risonanza hardware')
    
    ax.set_xlabel(r'Frequenza $f_{in}$ [kHz]')
    ax.set_ylabel(r'Guadagno lineare $|V_{out} / V_{in}|$')
    ax.set_title('Confronto tra compensazione hardware fisica e compensazione software', pad=9)
    ax.grid(True)
    ax.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
    ax.ticklabel_format(useOffset=False, style='plain')
    ax.set_xlim(data_2['f_khz'][0], data_2['f_khz'][-1])
    
    plt.tight_layout()
    p_hw_sw = os.path.join(OUT_DIR, 'confronto_hardware_vs_software.png')
    plt.savefig(p_hw_sw)
    plt.close()
    print(f"[OK] Grafico salvato: {p_hw_sw}")

print("\nTutti i grafici aggiornati sono stati generati con successo!")
