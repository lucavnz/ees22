"""
Analisi del Ring-Down del MEMS al variare della Fase del Burst (Gate):
Studio dell'ampiezza iniziale A0 in funzione della fase di spegnimento phi (-360 deg .. +360 deg).

Pipeline di analisi:
1. Caricamento delle 145 tracce sperimentali dell'oscilloscopio (passo 5 deg da -360 deg a +360 deg).
2. Rilevamento automatico del fronte di discesa del Gate (CH2) che definisce l'istante t = 0.
3. Analisi del segnale di ingresso v_in(t) (CH3) prima e dopo t = 0:
   - Verifica della fase di interruzione della sinusoide a t = 0^-
   - Misura della tensione continua V_post(phi) = V_AC * sin(phi) mantenuta dal DAC per t >= 0.
4. Rimozione dell'offset DC da CH1 (uscita condizionamento TIA) e taglio dei primi t_cut = 20 us
   per escludere il transitorio elettrico parassita dovuto a Cp.
5. Filtraggio passa-banda (390 kHz - 445 kHz), individuazione dei picchi di oscillazione meccanica
   e fit esponenziale dell'inviluppo A(t) = A0 * exp(-t / tau) per estrarre l'ampiezza iniziale A0.
6. Estrazione della frequenza di oscillazione libera f1 tramite trasformata di Hilbert per
   quantificare e compensare la deriva termica (+35 Hz) accumulata durante la scansione sequenziale.
7. Generazione dei grafici in stile editoriale (sfondo bianco, 300 DPI) coerenti con la relazione.
"""

import os
import glob
import re
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, butter, filtfilt, hilbert, savgol_filter
from scipy.optimize import curve_fit

# ---------------------------------------------------------
# 1. Configurazione Percorsi e Stile Grafico
# ---------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'grafici')
os.makedirs(OUTPUT_DIR, exist_ok=True)

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.labelsize': 11.5,
    'axes.titlesize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'lines.linewidth': 1.6,
    'grid.alpha': 0.35,
    'grid.linestyle': '--',
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'savefig.facecolor': 'white'
})


def load_phase_trace(filepath):
    """Carica un file CSV traccia_fase_*.csv dell'oscilloscopio (3 righe di header)."""
    data = np.loadtxt(filepath, delimiter=',', skiprows=3)
    t = data[:, 0]    # Tempo relativo al trigger del Gate (t = 0 s allo spegnimento)
    ch1 = data[:, 1]  # Uscita circuito di condizionamento v_out(t)
    ch3 = data[:, 2]  # Segnale di eccitazione v_in(t)
    return t, ch1, ch3


def process_single_phase_file(filepath, phase_deg, t_cut_us=20.0, fit_duration_ms=2.5):
    """
    Elabora una singola traccia di ringdown per una data fase del burst:
    - Individua l'istante di spegnimento del Gate (t = 0)
    - Misura il livello DC post-gate V_post su CH3 (v_in)
    - Rimuove l'offset DC su CH1 (v_out)
    - Scarta i primi t_cut_us dopo t = 0 per escludere l'oscillazione parassita di Cp
    - Estrae i picchi del ringdown e calcola A0 tramite fit esponenziale
    - Stima la frequenza naturale f1 durante il ringdown tramite fase istantanea di Hilbert
    """
    t, ch1, ch3 = load_phase_trace(filepath)
    dt = (t[-1] - t[0]) / (len(t) - 1)
    fs = 1.0 / dt

    # 1. Istante di spegnimento del Gate (trigger dell'oscilloscopio a t = 0.0 s)
    g_idx = int(np.argmin(np.abs(t - 0.0)))
    t_gate = t[g_idx]

    # 2. Analisi di v_in (CH3): offset medio pre-gate e tensione congelata post-gate
    v_in_pre = ch3[:g_idx - 4]
    v_in_dc_pre = np.mean(v_in_pre)
    v_post_raw = np.mean(ch3[g_idx + int(50e-6 / dt):])
    v_post_net = v_post_raw - v_in_dc_pre

    # Stima ampiezza di v_in prima dello spegnimento
    v_in_ac = v_in_pre - v_in_dc_pre
    v_in_amp = np.sqrt(2.0) * np.std(v_in_ac)

    # 3. Rimozione offset DC da CH1 (calcolato nella regione di ringdown dopo 50 us)
    dc_start = g_idx + int(50e-6 / dt)
    y_dc = np.mean(ch1[dc_start:])
    ch1_no_dc = ch1 - y_dc

    # 4. Taglio post-gate t_cut_us per escludere il transitorio elettrico parassita
    cut_samples = int(t_cut_us * 1e-6 / dt)
    i_start = g_idx + cut_samples
    t_ring = t[i_start:] - t_gate
    sig_ring = ch1_no_dc[i_start:]

    # 5. Filtro passa-banda (390 kHz - 445 kHz) identico a analizza_ringdown.py
    b_bp, a_bp = butter(2, [390000.0 / (fs / 2.0), 445000.0 / (fs / 2.0)], btype='bandpass')
    sig_filtered = filtfilt(b_bp, a_bp, sig_ring)

    # 6. Individuazione dei picchi e fit esponenziale ln(A(t)) = ln(A0) - t / tau
    peaks, _ = find_peaks(sig_filtered, distance=6, height=0.0)
    t_peaks = t_ring[peaks]
    v_peaks = sig_filtered[peaks]

    mask = (t_peaks >= 50e-6) & (t_peaks <= fit_duration_ms * 1e-3)
    t_fit = t_peaks[mask]
    v_fit = v_peaks[mask]

    p_log = np.polyfit(t_fit, np.log(v_fit), 1)
    tau = -1.0 / p_log[0]
    A0 = np.exp(p_log[1])

    # 7. Frequenza di oscillazione libera f1 (tramite fase istantanea di Hilbert su [50 us, 2.5 ms])
    i_fstart = g_idx + int(50e-6 / dt)
    i_fend = g_idx + int(fit_duration_ms * 1e-3 / dt)
    t_fwin = t[i_fstart:i_fend] - t_gate
    sig_fwin_filt = filtfilt(b_bp, a_bp, ch1_no_dc[i_fstart:i_fend])

    analytic_sig = hilbert(sig_fwin_filt)
    phase_inst = np.unwrap(np.angle(analytic_sig))
    p_phase = np.polyfit(t_fwin, phase_inst, 1)
    f1_hilbert = p_phase[0] / (2.0 * np.pi)

    return {
        'phase_deg': phase_deg,
        'filepath': filepath,
        't': t,
        'ch1': ch1,
        'ch1_no_dc': ch1_no_dc,
        'ch3': ch3,
        'ch3_no_dc': ch3 - v_in_dc_pre,
        'g_idx': g_idx,
        't_gate': t_gate,
        'dt': dt,
        'fs': fs,
        'v_post_mv': v_post_net * 1e3,
        'v_in_amp_mv': v_in_amp * 1e3,
        't_ring': t_ring,
        'sig_ring': sig_ring,
        'sig_filtered': sig_filtered,
        't_peaks': t_peaks,
        'v_peaks': v_peaks,
        'A0': A0,
        'A0_mv': A0 * 1e3,
        'tau': tau,
        'tau_ms': tau * 1e3,
        'f1_hz': f1_hilbert
    }


def main():
    print("Avvio analisi variazione della fase del burst (-360 deg .. +360 deg)...")
    pattern = os.path.join(BASE_DIR, 'traccia_fase_*deg.csv')
    files = glob.glob(pattern)

    phase_files = []
    for fpath in files:
        m = re.search(r'traccia_fase_([+-]?\d+\.?\d*)deg\.csv', os.path.basename(fpath))
        if m:
            phase_files.append((float(m.group(1)), fpath))

    phase_files.sort(key=lambda x: x[0])
    print(f"Trovate {len(phase_files)} tracce sperimentali.")

    results = []
    by_phase = {}
    for ph, fpath in phase_files:
        res = process_single_phase_file(fpath, ph, t_cut_us=20.0, fit_duration_ms=2.5)
        results.append(res)
        by_phase[round(ph, 1)] = res

    phases = np.array([r['phase_deg'] for r in results])
    a0_mv = np.array([r['A0_mv'] for r in results])
    v_post_mv = np.array([r['v_post_mv'] for r in results])
    f1_hz = np.array([r['f1_hz'] for r in results])
    steps = np.arange(1, len(results) + 1)

    # ---------------------------------------------------------
    # Modellazione della deriva termica su f1 e impatto lorenziano su A0
    # ---------------------------------------------------------
    # Frequenza del generatore durante il burst (misurata da CH3: 417896.0 Hz)
    f_in_hz = 417896.0

    # Fit della curva lorenziana A0(f1) = A_max / sqrt(1 + (2*(f_in - f1)/bw)^2)
    def lorentz_from_f1(f1_val, a_max, bw):
        return a_max / np.sqrt(1.0 + (2.0 * (f_in_hz - f1_val) / bw) ** 2)

    popt_lor, _ = curve_fit(lorentz_from_f1, f1_hz, a0_mv, p0=[37.3, 137.0])
    a_max_fit, bw_fit = popt_lor

    # Trend liscio della deriva termica di f1 lungo la scansione sequenziale
    f1_smooth = savgol_filter(f1_hz, window_length=15, polyorder=2)
    a0_thermal_pred = lorentz_from_f1(f1_smooth, a_max_fit, bw_fit)

    # Compensazione della deriva termica riportando tutti i punti alla frequenza di riferimento a phi = 0 deg
    idx_zero = np.argmin(np.abs(phases - 0.0))
    a0_ref_zero = a0_thermal_pred[idx_zero]
    a0_comp_mv = a0_mv * (a0_ref_zero / a0_thermal_pred)

    a0_comp_mean = np.mean(a0_comp_mv)
    a0_comp_std = np.std(a0_comp_mv)

    print("=" * 70)
    print(f"F_in generatore (burst): {f_in_hz:.1f} Hz")
    print(f"Parametri lorenziana: A_max = {a_max_fit:.2f} mV, Delta_f = {bw_fit:.1f} Hz")
    print(f"Deriva termica di f1 da Step 1 (-360 deg) a Step 145 (+360 deg):")
    print(f"  f1(-360 deg) = {f1_hz[0]:.2f} Hz")
    print(f"  f1(   0 deg) = {f1_hz[idx_zero]:.2f} Hz")
    print(f"  f1(+360 deg) = {f1_hz[-1]:.2f} Hz")
    print(f"  Delta f1 totale = +{f1_hz[-1] - f1_hz[0]:.2f} Hz")
    print("-" * 70)
    print(f"Ampiezza A0 misurata alle tre fasi fisicamente identiche (-360, 0, +360 deg):")
    print(f"  A0(-360 deg) = {a0_mv[0]:.2f} mV (predetta da deriva termica: {a0_thermal_pred[0]:.2f} mV)")
    print(f"  A0(   0 deg) = {a0_mv[idx_zero]:.2f} mV (predetta da deriva termica: {a0_thermal_pred[idx_zero]:.2f} mV)")
    print(f"  A0(+360 deg) = {a0_mv[-1]:.2f} mV (predetta da deriva termica: {a0_thermal_pred[-1]:.2f} mV)")
    print("-" * 70)
    print(f"Ampiezza A0 compensata per la deriva termica:")
    print(f"  Media = {a0_comp_mean:.2f} mV, Dev.Std = {a0_comp_std:.2f} mV ({a0_comp_std / a0_comp_mean * 100:.2f}%)")
    print("=" * 70)

    # Salvataggio CSV pulito dei risultati
    csv_out = os.path.join(BASE_DIR, 'risultati_A0_vs_fase.csv')
    with open(csv_out, 'w') as f:
        f.write("Step,Fase_deg,V_post_mV,f1_ringdown_Hz,A0_misurata_mV,A0_modello_termico_mV,A0_compensata_mV\n")
        for i, r in enumerate(results):
            f.write(
                f"{i+1},{r['phase_deg']:.1f},{r['v_post_mv']:.3f},{r['f1_hz']:.2f},"
                f"{r['A0_mv']:.4f},{a0_thermal_pred[i]:.4f},{a0_comp_mv[i]:.4f}\n"
            )
    print(f"Tabella salvata in: {csv_out}")

    # =========================================================
    # GRAFICO 1: Significato fisico della fase del burst su v_in(t)
    # =========================================================
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.2, 5.2), dpi=300)

    demo_phases = [
        (0.0, '#1971c2', '-', r'$\phi = 0^\circ$ (stacco sullo zero, pendenza max)'),
        (90.0, '#2b8a3e', '-', r'$\phi = +90^\circ$ (stacco sul picco $+V_{\mathrm{AC}}$, pendenza $0$)'),
        (180.0, '#e67700', '--', r'$\phi = +180^\circ$ (stacco sullo zero, pendenza min)'),
        (-90.0, '#d62728', '-', r'$\phi = -90^\circ$ (stacco sul picco $-V_{\mathrm{AC}}$, pendenza $0$)')
    ]

    t_fine_us = np.linspace(-4.8, 4.8, 1200)
    # Piccola latenza di propagazione (~0.13 us) tra lo stop del DAC interno e la soglia di trigger
    t_dac_offset_us = -0.132
    for ph_val, col, ls, lbl in demo_phases:
        d = by_phase[ph_val]
        t_us_raw = (d['t'] - d['t_gate']) * 1e6

        # Fit della sinusoide su CH3 per t < 0 per interpolare esattamente i campioni dell'oscilloscopio
        mask_pre = (t_us_raw >= -45.0) & (t_us_raw <= -0.5)
        t_pre_s = d['t'][mask_pre] - d['t_gate']
        y_pre_mv = d['ch3_no_dc'][mask_pre] * 1e3

        def sin_pre(t_s, amp, f_hz, ph_rad):
            return amp * np.sin(2.0 * np.pi * f_hz * t_s + ph_rad)

        p0_sin = [99.5, 417800.0, np.deg2rad(ph_val)]
        popt_sin, _ = curve_fit(sin_pre, t_pre_s, y_pre_mv, p0=p0_sin)

        v_post = d['v_post_mv']
        t_us_aligned = t_us_raw - t_dac_offset_us
        mask_z = (t_us_aligned >= -4.8) & (t_us_aligned <= 4.8)

        v_fine = np.where(
            t_fine_us <= 0.0,
            sin_pre((t_fine_us + t_dac_offset_us) * 1e-6, *popt_sin),
            v_post
        )
        ax1.plot(t_fine_us, v_fine, linestyle=ls, color=col, linewidth=1.7, label=lbl)
        ax1.plot(t_us_aligned[mask_z], d['ch3_no_dc'][mask_z] * 1e3, 'o', color=col, markersize=4.0, alpha=0.85)

    ax1.axvline(0.0, color='#343a40', linestyle=':', linewidth=1.6, label=r'Spegnimento Gate ($t = 0$)')
    ax1.set_xlim(-4.8, 4.8)
    ax1.set_ylim(-135, 165)
    ax1.set_xlabel(r'Tempo relativo al fronte di discesa del Gate [$\mu$s]')
    ax1.set_ylabel(r'Tensione di ingresso $v_{\mathrm{in}}(t)$ [mV]')
    ax1.set_title(r'Segnale di eccitazione $v_{\mathrm{in}}(t)$ allo stacco del Gate ($t = 0$)', pad=9)
    ax1.grid(True)
    ax1.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.93, edgecolor='#ced4da', fontsize=8.4)

    # Pannello destro: V_post(phi) misurata vs V_AC * sin(phi)
    ax2.plot(phases, v_post_mv, 'o', color='#1971c2', markersize=4.2, alpha=0.85,
             label=r'Livello $V_{\mathrm{post}}$ misurato per $t > 0$ (CH3)')
    phi_dense = np.linspace(-360.0, 360.0, 500)
    v_ac_fit = 99.5
    ax2.plot(phi_dense, v_ac_fit * np.sin(np.deg2rad(phi_dense)), '--', color='#d62728', linewidth=2.0,
             label=r'Legge teorica $V_{\mathrm{AC}} \sin(\phi)$')

    ax2.set_xlim(-375, 375)
    ax2.set_xticks(np.arange(-360, 361, 90))
    ax2.set_xlabel(r'Fase impostata sul generatore $\phi$ [gradi]')
    ax2.set_ylabel(r'Tensione mantenuta dopo lo stacco $V_{\mathrm{post}}$ [mV]')
    ax2.set_title(r'Tensione $v_{\mathrm{in}}(t \geq 0) = V_{\mathrm{AC}}\sin(\phi)$ al variare della fase $\phi$', pad=9)
    ax2.grid(True)
    ax2.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.93, edgecolor='#ced4da', fontsize=9.5)

    plt.tight_layout()
    g1_path = os.path.join(OUTPUT_DIR, 'stacco_gate_fase_vin.png')
    plt.savefig(g1_path)
    plt.close()
    print(f"Salvato Grafico 1: {g1_path}")

    # Versione a singolo pannello (solo V_post vs fase phi) per la relazione
    fig_vp, ax_vp = plt.subplots(figsize=(8.8, 5.2), dpi=300)
    ax_vp.plot(phases, v_post_mv, 'o', color='#1971c2', markersize=4.8, alpha=0.85,
               label=r'Livello $V_{\mathrm{post}}$ misurato per $t \geq 0$ (CH3)')
    ax_vp.plot(phi_dense, v_ac_fit * np.sin(np.deg2rad(phi_dense)), '--', color='#d62728', linewidth=2.0,
               label=r'Legge teorica $V_{\mathrm{AC}} \sin(\phi)$')
    ax_vp.axhline(0.0, color='black', linestyle=':', linewidth=0.8, alpha=0.5)
    ax_vp.set_xlim(-375, 375)
    ax_vp.set_xticks(np.arange(-360, 361, 90))
    ax_vp.set_ylim(-120, 148)
    ax_vp.set_xlabel(r'Fase impostata sul generatore $\phi$ [gradi]')
    ax_vp.set_ylabel(r'Tensione mantenuta dopo lo stacco $V_{\mathrm{post}}$ [mV]')
    ax_vp.set_title(r'Tensione continua $v_{\mathrm{in}}(t \geq 0) = V_{\mathrm{AC}}\sin(\phi)$ al variare della fase $\phi$', pad=9)
    ax_vp.grid(True)
    ax_vp.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.93, edgecolor='#ced4da', fontsize=10)
    plt.tight_layout()
    g1_single_path = os.path.join(OUTPUT_DIR, 'vpost_vs_fase.png')
    plt.savefig(g1_single_path, bbox_inches='tight')
    plt.close()
    print(f"Salvato Grafico 1 (singolo pannello): {g1_single_path}")

    # =========================================================
    # GRAFICO 2: Dettaglio Ring-Down e Fit Esponenziale per 4 Fasi
    # (Stile identico a ringdown_fit_4casi.png della Sezione 7, solo A0)
    # =========================================================
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=300)
    axes = axes.flatten()

    sample_phases = [-90.0, 0.0, 90.0, 180.0]
    titles = [
        r"Fase di stacco $\phi = -90^\circ$ (picco negativo, $V_{\mathrm{post}} \approx -100$ mV)",
        r"Fase di stacco $\phi = 0^\circ$ (passaggio per lo zero, $V_{\mathrm{post}} \approx 0$ mV)",
        r"Fase di stacco $\phi = +90^\circ$ (picco positivo, $V_{\mathrm{post}} \approx +96$ mV)",
        r"Fase di stacco $\phi = +180^\circ$ (passaggio per lo zero, $V_{\mathrm{post}} \approx 0$ mV)"
    ]

    t_shift_ms = 0.028

    for i, ph_val in enumerate(sample_phases):
        ax = axes[i]
        d = by_phase[ph_val]

        t_raw_from_gate = (d['t'][d['g_idx']:] - d['t_gate']) * 1e3 - t_shift_ms
        sig_raw_from_gate = d['ch1_no_dc'][d['g_idx']:] * 1e3
        ax.plot(t_raw_from_gate, sig_raw_from_gate, color='#aec7e8', alpha=0.5, linewidth=0.8,
                label='Segnale ring-down (senza DC)')

        pt_ms = d['t_peaks'] * 1e3 - t_shift_ms
        pv_mv = d['v_peaks'] * 1e3
        ax.plot(pt_ms, pv_mv, '.', color='#1971c2', markersize=3.5, alpha=0.7,
                label='Picchi oscillazione')

        t_dense_ms = np.linspace(0.0, 2.8, 500)
        A0_plot = d['A0'] * np.exp(-t_shift_ms * 1e-3 / d['tau'])
        fit_curve = (A0_plot * np.exp(-t_dense_ms * 1e-3 / d['tau'])) * 1e3
        ax.plot(t_dense_ms, fit_curve, '-', color='#d62728', linewidth=2.0,
                label=f'Fit inviluppo: $A_0 = {d["A0_mv"]:.2f}$ mV')

        ax.set_title(titles[i], fontsize=11, pad=8)
        ax.set_xlabel('Tempo dopo lo spegnimento del gate [ms]')
        ax.set_ylabel('Ampiezza [mV]')
        ax.set_xlim(0.0, 2.8)
        ax.set_ylim(-30.0, 30.0)
        ax.grid(True, linestyle='--', alpha=0.35)
        ax.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da', fontsize=9.0)

    plt.tight_layout()
    g2_path = os.path.join(OUTPUT_DIR, 'ringdown_fit_4fasi.png')
    plt.savefig(g2_path)
    plt.close()
    print(f"Salvato Grafico 2: {g2_path}")

    # =========================================================
    # GRAFICO 3: Deriva termica di f1 durante lo sweep e impatto su A0
    # =========================================================
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.2, 8.2), dpi=300, sharex=True)

    # Pannello superiore: frequenza di oscillazione f1 misurata durante il ringdown
    ax1.plot(phases, f1_hz / 1e3, 'o', color='#2b8a3e', markersize=4.5, alpha=0.8,
             label=r'Frequenza di oscillazione del ringdown $f_1$')

    ax1.ticklabel_format(useOffset=False, style='plain')
    ax1.set_ylabel(r'Frequenza di oscillazione $f_1$ [kHz]')
    ax1.set_title(r'Frequenza di oscillazione $f_1$ e $A_0$ vs $\phi$', pad=9)
    ax1.grid(True)
    ax1.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.93, edgecolor='#ced4da')

    # Pannello inferiore: A0 misurata vs predizione dalla curva di risonanza lorentziana
    ax2.plot(phases, a0_mv, 'o', color='#1971c2', markersize=4.8, alpha=0.85,
             label=r'Ampiezza iniziale $A_0$ misurata')
    ax2.plot(phases, a0_thermal_pred, '--', color='#d62728', linewidth=2.2,
             label=r'Ampiezza predetta dalla lorentziana per deriva di $f_1$')

    ax2.set_xlim(-375, 375)
    ax2.set_xticks(np.arange(-360, 361, 90))
    ax2.set_ylim(18.0, 28.0)
    ax2.set_xlabel(r'Fase impostata sul generatore $\phi$ [gradi]')
    ax2.set_ylabel(r'Ampiezza iniziale del ringdown $A_0$ [mV]')
    ax2.grid(True)
    ax2.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.93, edgecolor='#ced4da')

    plt.tight_layout()
    g3_path = os.path.join(OUTPUT_DIR, 'deriva_termica_f1_e_A0.png')
    plt.savefig(g3_path)
    plt.close()
    print(f"Salvato Grafico 3: {g3_path}")

    # =========================================================
    # GRAFICO 4: Ampiezza A0 vs Fase (compensata dalla deriva)
    # (Stile identico a ampiezza_vs_frequenza.png e tau_vs_frequenza.png)
    # =========================================================
    fig, ax = plt.subplots(figsize=(8.8, 5.5), dpi=300)
    ax.plot(phases, a0_comp_mv, 'o', color='#1971c2', markersize=5.5, alpha=0.85,
            label=r'Ampiezza iniziale $A_0$ (compensata dalla deriva)')
    ax.axhline(a0_comp_mean, color='#d62728', linestyle='--', linewidth=2.0,
               label=rf'Valore medio: $A_0 = {a0_comp_mean:.2f}$ mV ($\sigma = {a0_comp_std:.2f}$ mV)')

    ax.set_xlim(-375, 375)
    ax.set_xticks(np.arange(-360, 361, 90))
    ax.set_ylim(a0_comp_mean - 3.5, a0_comp_mean + 3.5)
    ax.set_xlabel(r'Fase di spegnimento del burst $\phi$ [gradi]')
    ax.set_ylabel(r'Ampiezza iniziale del ringdown $A_0$ [mV]')
    ax.set_title(r"Ampiezza iniziale del ringdown $A_0$ al variare della fase di spegnimento $\phi$", pad=9)
    ax.grid(True)
    ax.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.93, edgecolor='#ced4da')

    plt.tight_layout()
    g4_path = os.path.join(OUTPUT_DIR, 'ampiezza_A0_vs_fase.png')
    plt.savefig(g4_path)
    plt.close()
    print(f"Salvato Grafico 4: {g4_path}")


if __name__ == '__main__':
    main()
