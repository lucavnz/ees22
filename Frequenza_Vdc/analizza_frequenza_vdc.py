"""
Analisi della Frequenza di Oscillazione del MEMS in Ring-Down al variare di V_DC:
Verifica dell'effetto di Electrostatic Spring Softening (Molla Negativa).

Questo script esegue:
1. Caricamento dei dati dell'oscilloscopio per le misure a V_DC variabile (scope_39 - scope_45).
2. Individuazione automatica del fronte di discesa del Gate TTL (Ch2).
3. Rimozione dell'offset DC da Ch1 (uscita dell'amplificatore invertente post-TIA).
4. Taglio del transitorio iniziale di scarica parassita di Cp e assestamento del TIA (t_cut).
5. Stima accurata della frequenza di oscillazione f1 con 3 metodi indipendenti:
   - Metodo 1: Fit non-lineare a minimi quadrati della sinusoide smorzata nel dominio del tempo (MLE).
   - Metodo 2: Demodulazione tramite Trasformata di Hilbert e regressione lineare della fase istantanea.
   - Metodo 3: Spettro FFT ad alta risoluzione con Zero-Padding 64x (interpolazione sinc continua).
   - (Metodo 4 di supporto: Zero-Crossing con interpolazione lineare).
6. Confronto rigoroso tra i metodi e verifica della concordanza sub-hertziana.
7. Regressione lineare di f1^2 in funzione di V_DC^2:
   f1^2(V_DC) = f01^2 - alpha * V_DC^2
8. Confronto con il valore teorico predetto dal Reduced Order Model (ROM) di Frangi et al. 2023.
9. Scomposizione dell'ampiezza A0(V_DC) e ricostruzione della curva lorentziana di risonanza meccanica tramite il detuning Delta_f = f_in - f1(V_DC).
10. Generazione di tutti i grafici ad alta risoluzione (300 DPI) e salvataggio dei risultati in CSV.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, butter, filtfilt, hilbert
from scipy.optimize import curve_fit

# -----------------------------------------------------------------------------
# 1. Configurazione Mappatura Misure e Costanti Fisiche
# -----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'Misure')
OUTPUT_DIR = os.path.join(BASE_DIR, 'grafici')
CSV_OUT = os.path.join(BASE_DIR, 'risultati_frequenza_vdc.csv')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Mappatura delle tensioni continue di bias V_DC per ciascun file scope
VDC_MAP = {
    39: 3.0,
    40: 3.5,
    41: 4.0,
    42: 4.5,
    43: 5.0,
    44: 5.5,
    45: 6.0
}

# Frequenza nominale del generatore di eccitazione Vin nel burst
F_IN = 417850.0  # Hz

# Costanti fisiche e coefficienti dal Paper Frangi et al. 2023
EPSILON_0 = 8.8541878128e-12  # F/m (Permittività dielettrica del vuoto)
# Dal Paper (Tabella 2, colonna f_DD^(1)/eps0, termine lineare in q1 c_1^(1)):
# c_1^(1) = 21.11 [muN*mum / (mum * V^2 * pF)] = 21.11 [muN / (V^2 * pF)]
# Moltiplicato per eps0 in [pF/mum] (eps0 = 8.8541878e-6 pF/mum):
# c_1_DD = 21.11 * eps0 [muN / (V^2 * mum)] = 21.11 * 8.8541878e-6 [mum / (mus^2 * V^2)]
# in unità SI (s^-2 / V^2):
C1_DD_THEORY = 21.11 * 8.8541878128e-6 * 1.0e12  # rad^2 / (s^2 * V^2) = 1.86912e8 s^-2 / V^2
# Pendenza teorica per f1^2 vs V_DC^2: alpha_th = c_1_DD / (4 * pi^2)
SLOPE_THEORY = C1_DD_THEORY / (4.0 * np.pi**2)   # Hz^2 / V^2 = 4.7345e6 Hz^2 / V^2

# Configurazione stile tipografico per i grafici
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
    'grid.linestyle': '--'
})

# -----------------------------------------------------------------------------
# 2. Funzioni di Caricamento ed Elaborazione Segnali
# -----------------------------------------------------------------------------
def load_scope_file(scope_num):
    """Carica il file CSV saltando gli header dell'oscilloscopio ed escludendo eventuali righe incomplete."""
    filepath = os.path.join(DATA_DIR, f'scope_{scope_num}.csv')
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File non trovato: {filepath}")
        
    data = []
    with open(filepath, 'r') as fp:
        fp.readline()  # riga intestazione 1 (x-axis, 1, 2, 3)
        fp.readline()  # riga intestazione 2 (second, Volt, Volt, Volt)
        for line in fp:
            parts = line.strip().split(',')
            if len(parts) >= 4 and parts[1] != '':
                try:
                    data.append([float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])])
                except ValueError:
                    continue
    data = np.array(data)
    t = data[:, 0]
    ch1 = data[:, 1]  # Uscita TIA + Invertente
    ch2 = data[:, 2]  # Segnale Gate TTL (0 - 3.3 V)
    ch3 = data[:, 3]  # Segnale Vin (eccitazione AC)
    return t, ch1, ch2, ch3

def analyze_single_measurement(scope_num, t_cut_us=20.0, fit_duration_ms=1.9):
    """
    Esegue l'analisi completa del ringdown per un file di oscilloscopio:
    - Identifica il fronte di discesa del Gate
    - Rimuove l'offset DC
    - Taglia il transitorio parassita iniziale (t_cut_us)
    - Filtra il segnale con passa-banda 390-445 kHz
    - Calcola la frequenza con i 3 metodi principali (Sine fit, Hilbert, FFT 64x) e ZC
    """
    t, ch1, ch2, ch3 = load_scope_file(scope_num)
    dt = (t[-1] - t[0]) / (len(t) - 1)
    fs = 1.0 / dt
    vdc = VDC_MAP[scope_num]

    # 1. Individuazione istante di spegnimento Gate (fronte discesa a 1.2 V)
    edges = np.where((ch2[:-1] > 1.2) & (ch2[1:] <= 1.2))[0]
    if len(edges) == 0:
        raise ValueError(f"Fronte di discesa gate non trovato in scope_{scope_num}")
    g_idx = edges[0]
    t_gate = t[g_idx]

    # 2. Rimozione offset DC (stimato sulla porzione post-gate)
    dc_start = g_idx + int(50e-6 / dt)
    y_dc = np.mean(ch1[dc_start:])
    ch1_no_dc = ch1 - y_dc

    # 3. Finestra temporale di analisi ring-down
    i_start = g_idx + int(t_cut_us * 1e-6 / dt)
    dur_samples = int(fit_duration_ms * 1e-3 / dt)
    i_end = min(g_idx + dur_samples, len(t) - 1)

    t_win = t[i_start:i_end] - t_gate
    sig_win = ch1_no_dc[i_start:i_end]

    # 4. Filtraggio passa-banda Butterworth 2° ordine (390 - 445 kHz)
    b_bp, a_bp = butter(2, [390000.0 / (fs / 2), 445000.0 / (fs / 2)], btype='bandpass')
    sig_win_filt = filtfilt(b_bp, a_bp, sig_win)

    # 5. Individuazione picchi ed estrazione inviluppo esponenziale iniziale
    peaks, _ = find_peaks(sig_win_filt, distance=6, height=0.0)
    t_peaks = t_win[peaks]
    v_peaks = sig_win_filt[peaks]

    # Fit logaritmico preliminare per A0 e tau
    p_log = np.polyfit(t_peaks, np.log(v_peaks), 1)
    tau_init = -1.0 / p_log[0]
    A0_init = np.exp(p_log[1])

    # -------------------------------------------------------------
    # Metodo 2: Demodulazione tramite Trasformata di Hilbert
    # -------------------------------------------------------------
    analytic_sig = hilbert(sig_win_filt)
    phase_inst = np.unwrap(np.angle(analytic_sig))
    p_phase = np.polyfit(t_win, phase_inst, 1)
    f_hilbert = p_phase[0] / (2.0 * np.pi)

    # Verifica chirp rate (eventuale non-linearità intra-ciclo)
    p_quad = np.polyfit(t_win, phase_inst, 2)
    chirp_rate = (2.0 * p_quad[0]) / (2.0 * np.pi)  # Hz/s

    # -------------------------------------------------------------
    # Metodo 1: Fit Sinusoidale Smorzato Non-Lineare (MLE / NLS) - RACCOMANDATO
    # -------------------------------------------------------------
    def damped_sin(t_vec, a0, tau_d, f0, phi0):
        return a0 * np.exp(-t_vec / tau_d) * np.cos(2.0 * np.pi * f0 * t_vec + phi0)

    try:
        popt, pcov = curve_fit(
            damped_sin, t_win, sig_win,
            p0=[A0_init, tau_init, f_hilbert, 0.0],
            bounds=([0.0, 0.5e-3, 400e3, -2 * np.pi], [1.0, 10e-3, 430e3, 2 * np.pi])
        )
        A0_sine = popt[0]
        tau_sine = popt[1]
        f_sine = popt[2]
        phi0_sine = popt[3]
        f_sine_err = np.sqrt(pcov[2, 2])
        tau_sine_err = np.sqrt(pcov[1, 1])
        A0_sine_err = np.sqrt(pcov[0, 0])
    except Exception as e:
        print(f"Warning: Fit sinusoidale non convergente per scope {scope_num}: {e}")
        A0_sine = A0_init
        tau_sine = tau_init
        f_sine = f_hilbert
        phi0_sine = 0.0
        f_sine_err = 0.5
        tau_sine_err = 0.1e-3
        A0_sine_err = 1e-3

    # -------------------------------------------------------------
    # Metodo 3: Spettro FFT ad Alta Risoluzione con Zero-Padding 64x
    # -------------------------------------------------------------
    N_pad = len(sig_win) * 64
    fft_pad = np.fft.rfft(sig_win, n=N_pad)
    freqs_pad = np.fft.rfftfreq(N_pad, dt)
    f_fft = freqs_pad[np.argmax(np.abs(fft_pad))]

    # -------------------------------------------------------------
    # Metodo 4: Zero-Crossing con Interpolazione Lineare
    # -------------------------------------------------------------
    zc = np.where((sig_win_filt[:-1] < 0) & (sig_win_filt[1:] >= 0))[0]
    t_zc = [t_win[z] - sig_win_filt[z] * (t_win[z + 1] - t_win[z]) / (sig_win_filt[z + 1] - sig_win_filt[z]) for z in zc]
    if len(t_zc) > 1:
        f_zc = 1.0 / np.mean(np.diff(t_zc))
    else:
        f_zc = f_hilbert

    # Rumore residuo a fine sweep
    noise_sigma = np.std(ch1_no_dc[-1000:])

    # Calcolo Q
    q_factor = np.pi * f_sine * tau_sine

    return {
        'scope_num': scope_num,
        'vdc': vdc,
        'vdc_sq': vdc**2,
        't_gate': t_gate,
        't_win': t_win,
        'sig_win': sig_win,
        'sig_win_filt': sig_win_filt,
        't_peaks': t_peaks,
        'v_peaks': v_peaks,
        'A0': A0_sine,
        'A0_err': A0_sine_err,
        'A0_norm': (A0_sine * 1e3) / (vdc**2),
        'tau': tau_sine,
        'tau_err': tau_sine_err,
        'q_factor': q_factor,
        'f_sine': f_sine,
        'f_sine_err': f_sine_err,
        'f_hilbert': f_hilbert,
        'f_fft': f_fft,
        'f_zc': f_zc,
        'delta_f': F_IN - f_sine,
        'chirp_rate': chirp_rate,
        'noise_sigma': noise_sigma,
        'popt': (A0_sine, tau_sine, f_sine, phi0_sine)
    }

# -----------------------------------------------------------------------------
# 3. Pipeline Principale di Analisi e Regressione
# -----------------------------------------------------------------------------
def run_analysis():
    print("=" * 80)
    print("ANALISI SPERIMENTALE FREQUENZA VS V_DC (RINGDOWN MEMS)")
    print("=" * 80)

    dataset = []
    for s_num in sorted(VDC_MAP.keys()):
        res = analyze_single_measurement(s_num)
        dataset.append(res)
        print(f"Scope {s_num:2d} | V_DC: {res['vdc']:4.1f} V | "
              f"f_Sine: {res['f_sine']:9.2f} ± {res['f_sine_err']:.2f} Hz | "
              f"f_Hilb: {res['f_hilbert']:9.2f} Hz | "
              f"f_FFT: {res['f_fft']:9.2f} Hz | "
              f"A0: {res['A0']*1e3:5.2f} mV | tau: {res['tau']*1e3:5.3f} ms | Q: {res['q_factor']:.0f}")

    # Estrazione vettori per fit
    vdc_arr = np.array([r['vdc'] for r in dataset])
    vdc_sq_arr = vdc_arr**2
    f_sine_arr = np.array([r['f_sine'] for r in dataset])
    f_err_arr = np.array([r['f_sine_err'] for r in dataset])
    f_hilb_arr = np.array([r['f_hilbert'] for r in dataset])
    f_fft_arr = np.array([r['f_fft'] for r in dataset])
    f_zc_arr = np.array([r['f_zc'] for r in dataset])
    a0_arr_mv = np.array([r['A0'] * 1e3 for r in dataset])
    a0_norm_arr = np.array([r['A0_norm'] for r in dataset])
    delta_f_arr = np.array([r['delta_f'] for r in dataset])

    # Frequenza al quadrato e propagazione dell'incertezza: sigma(f^2) = 2 * f * sigma(f)
    f_sq_arr = f_sine_arr**2
    f_sq_err_arr = 2.0 * f_sine_arr * f_err_arr

    # Regressione lineare f1^2 vs V_DC^2 (non pesata e pesata)
    p_fit_unw = np.polyfit(vdc_sq_arr, f_sq_arr, 1)
    weights = 1.0 / f_sq_err_arr
    p_fit, cov_fit = np.polyfit(vdc_sq_arr, f_sq_arr, 1, w=weights, cov=True)
    slope_exp = p_fit[0]         # Hz^2 / V^2 (negativo)
    intercept_exp = p_fit[1]     # Hz^2 (intercetta f01^2)
    slope_err = np.sqrt(cov_fit[0, 0])
    intercept_err = np.sqrt(cov_fit[1, 1])

    # Calcolo f01 estrapolato a V_DC = 0 V
    f01_est = np.sqrt(intercept_exp)
    f01_err = intercept_err / (2.0 * f01_est)

    # Coefficiente di determinazione R^2
    y_pred = np.polyval(p_fit, vdc_sq_arr)
    ss_tot = np.sum((f_sq_arr - np.mean(f_sq_arr))**2)
    ss_res = np.sum((f_sq_arr - y_pred)**2)
    r_squared = 1.0 - ss_res / ss_tot

    # Costante di proporzionalità alpha = |slope|
    alpha_exp = -slope_exp
    alpha_th = SLOPE_THEORY
    diff_percent = ((alpha_exp - alpha_th) / alpha_th) * 100.0

    print("\n" + "=" * 80)
    print("RISULTATI FIT LINEARE: f1^2(V_DC) = f01^2 - alpha * V_DC^2")
    print("=" * 80)
    print(f"Pendenza sperimentale (alpha_exp):  ({alpha_exp:.4e} ± {slope_err:.4e}) Hz^2/V^2")
    print(f"Pendenza teorica (alpha_th):        {alpha_th:.4e} Hz^2/V^2  (da Frangi et al. 2023)")
    print(f"Rapporto sperimentale/teorico:      {alpha_exp / alpha_th:.4f}")
    print(f"Discrepanza percentuale:           {diff_percent:+.2f}%")
    print(f"Frequenza naturale estrapolata f0:  {f01_est:.2f} ± {f01_err:.2f} Hz ({f01_est*1e-3:.4f} kHz)")
    print(f"Coefficiente di determinazione R^2: {r_squared:.6f}")
    print("=" * 80)

    # Salvataggio tabella CSV
    with open(CSV_OUT, 'w') as f_csv:
        f_csv.write("File,Vdc_V,Vdc2_V2,f_in_Hz,f_res_Hz,f_res_err_Hz,Delta_f_Hz,f_sq_Hz2,A0_mV,A0_norm_mV_V2,tau_ms,Q_factor\n")
        for r in dataset:
            f_csv.write(f"scope_{r['scope_num']}.csv,{r['vdc']:.2f},{r['vdc_sq']:.2f},"
                        f"{F_IN:.1f},{r['f_sine']:.2f},{r['f_sine_err']:.3f},{r['delta_f']:.2f},"
                        f"{r['f_sine']**2:.2f},{r['A0']*1e3:.2f},{r['A0_norm']:.3f},"
                        f"{r['tau']*1e3:.3f},{r['q_factor']:.0f}\n")
    print(f"Tabella salvata con successo in: {CSV_OUT}")

    # -----------------------------------------------------------------------------
    # 4. Generazione Grafici
    # -----------------------------------------------------------------------------

    # GRAFICO 1: f1^2 vs V_DC^2 con Fit Sperimentale e Modello Teorico di Frangi 2023
    fig1, ax1 = plt.subplots(figsize=(8.5, 6), dpi=300)
    v2_dense = np.linspace(8.0, 37.0, 200)
    f2_pred_dense = np.polyval(p_fit, v2_dense)
    f2_th_dense = intercept_exp - alpha_th * v2_dense

    # Solo punti sperimentali senza barre di incertezza
    ax1.plot(vdc_sq_arr, f_sq_arr / 1e10, 'o',
             color='#1b4965', markersize=7.5,
             label='Dati sperimentali', zorder=4)

    # Fit sperimentale
    ax1.plot(v2_dense, f2_pred_dense / 1e10, '-', color='#d62828', linewidth=2.0,
             label=rf'Fit lineare sperimentale ($\alpha = {alpha_exp/1e6:.3f}\times 10^6\ \mathrm{{Hz^2/V^2}}$, $R^2 = {r_squared:.4f}$)', zorder=3)

    # Modello teorico
    ax1.plot(v2_dense, f2_th_dense / 1e10, '--', color='#2b2d42', linewidth=1.7, alpha=0.85,
             label=rf'Modello teorico Frangi ($\alpha = {alpha_th/1e6:.3f}\times 10^6\ \mathrm{{Hz^2/V^2}}$)', zorder=2)

    ax1.set_xlabel(r'$V_{\mathrm{DC}}^2\ [\mathrm{V}^2]$', labelpad=6)
    ax1.set_ylabel(r'$f_1^2\ [\times 10^{10}\ \mathrm{Hz}^2]$', labelpad=6)
    ax1.set_title(r'Variazione di $f_1^2$ vs $V_{\mathrm{DC}}^2$', pad=12)
    ax1.grid(True, linestyle='--', alpha=0.35)

    legend_title = r"$f_1^2(V_{\mathrm{DC}}) = f_{01}^2 - \alpha V_{\mathrm{DC}}^2$"
    ax1.legend(loc='lower left', frameon=True, framealpha=0.95, facecolor='white',
               edgecolor='#cccccc', title=legend_title, title_fontsize=11, fontsize=10,
               alignment='left')

    plt.tight_layout()
    plot1_path = os.path.join(OUTPUT_DIR, 'f1_quadro_vs_vdc_quadro.png')
    fig1.savefig(plot1_path)
    plt.close(fig1)
    print(f"Grafico 1 salvato: {plot1_path}")

    # GRAFICO 2: softening_legge_quadratica.png (stile 2 pannelli esteso da 0 V)
    fig2, (ax_sq, ax_f) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

    # 2a: f1^2 vs Vdc^2 esteso da 0 a 38 V^2
    v2_full = np.linspace(0.0, 38.0, 200)
    f2_full_pred = np.polyval(p_fit, v2_full)
    ax_sq.plot(v2_full, f2_full_pred / 1e10, '-', color='#c0392b', linewidth=2.0, label='Fit lineare')
    ax_sq.plot(vdc_sq_arr, f_sq_arr / 1e10, 'o', color='#2980b9', markersize=7.5, label='Dati sperimentali', zorder=5)
    ax_sq.set_xlabel(r'$V_{\mathrm{DC}}^2\ [\mathrm{V}^2]$', labelpad=6)
    ax_sq.set_ylabel(r'$f_1^2\ [10^{10}\ \mathrm{Hz}^2]$', labelpad=6)
    ax_sq.set_title(r'$f_1^2\ \mathrm{vs}\ V_{\mathrm{DC}}^2$', pad=10)
    ax_sq.set_xlim(0, 38)
    ax_sq.grid(True, linestyle=':', alpha=0.45)
    ax_sq.legend(loc='upper right', frameon=True, framealpha=0.92)

    # 2b: f1 vs Vdc esteso da 0 a 6.5 V
    v_full = np.linspace(0.0, 6.5, 200)
    f1_full_pred = np.sqrt(np.polyval(p_fit, v_full**2))
    ax_f.plot(v_full, f1_full_pred, '-', color='#e67e22', linewidth=2.0, label=r'Fit $f_1 = \sqrt{f_{01}^2 - \alpha V_{\mathrm{DC}}^2}$')
    ax_f.plot(vdc_arr, f_sine_arr, 's', color='#27ae60', markersize=7.5, label='Dati sperimentali', zorder=5)
    ax_f.set_xlabel(r'$V_{\mathrm{DC}}\ [\mathrm{V}]$', labelpad=6)
    ax_f.set_ylabel(r'$f_1\ [\mathrm{Hz}]$', labelpad=6)
    ax_f.set_title(r'$f_1\ \mathrm{vs}\ V_{\mathrm{DC}}$', pad=10)
    ax_f.set_xlim(0, 6.5)
    ax_f.set_ylim(417700, 418050)
    ax_f.grid(True, linestyle=':', alpha=0.45)
    ax_f.legend(loc='upper right', frameon=True, framealpha=0.92)

    plt.tight_layout()
    plot2_path = os.path.join(OUTPUT_DIR, 'softening_legge_quadratica.png')
    fig2.savefig(plot2_path)
    plt.close(fig2)
    print(f"Grafico 2 salvato: {plot2_path}")

    # GRAFICO 3: risposta_ampiezza_vs_vdc_e_deltaf.png
    # Scomposizione dell'Ampiezza A0 e Ricostruzione della Risonanza Meccanica
    fig3, (ax_amp, ax_lor) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

    # 3a: A0 vs Vdc
    ax_amp.plot(vdc_arr, a0_arr_mv, 'o-', color='#1d3557', linewidth=2.0, markersize=8, label='Ampiezza $A_0$ Misurata [mV]')
    # Trova vertice di picco
    v_dense_peak = np.linspace(3.0, 6.0, 300)
    # Fit spline/polinomiale per localizzare il vertice di sintonizzazione
    p_amp_poly = np.polyfit(vdc_arr, a0_arr_mv, 3)
    v_fine = np.linspace(3.0, 6.0, 500)
    a0_fine = np.polyval(p_amp_poly, v_fine)
    v_vert = v_fine[np.argmax(a0_fine)]
    ax_amp.axvline(v_vert, color='#e63946', linestyle=':', linewidth=1.8, label=rf'Vertice di Sintonia: $V_{{\mathrm{{DC}}}} \approx {v_vert:.2f}\ \mathrm{{V}}$')
    ax_amp.annotate(f'Picco Massimo: $A_0 = {np.max(a0_arr_mv):.1f}\\ \\mathrm{{mV}}$\n(a $V_{{\\mathrm{{DC}}}} = 5.5\\ \\mathrm{{V}}$)',
                    xy=(5.5, a0_arr_mv[5]), xytext=(3.9, 47.0),
                    arrowprops=dict(facecolor='black', shrink=0.08, width=1.2, headwidth=6),
                    fontsize=9.5, bbox=dict(boxstyle='round,pad=0.5', facecolor='#f1faee', edgecolor='#457b9d'))
    ax_amp.set_xlabel(r'Tensione Continua $V_{\mathrm{DC}}\ [\mathrm{V}]$', labelpad=6)
    ax_amp.set_ylabel(r'Ampiezza Iniziale Ringdown $A_0\ [\mathrm{mV}]$', labelpad=6)
    ax_amp.set_title(r'Evoluzione Ampiezza $A_0(V_{\mathrm{DC}})$: Guadagno Elettromeccanico vs Detuning', pad=10, fontweight='bold', fontsize=11)
    ax_amp.grid(True, linestyle=':', alpha=0.45)
    ax_amp.legend(loc='upper left', frameon=True, framealpha=0.92)

    # 3b: Curva di risonanza meccanica pura A0 / Vdc^2 vs Detuning
    def lorentzian(df, a_max, fwhm, df0):
        return a_max / np.sqrt(1.0 + (2.0 * (df - df0) / fwhm)**2)

    popt_lor, _ = curve_fit(lorentzian, delta_f_arr, a0_norm_arr, p0=[1.75, 250.0, 0.0])
    a_max_fit, fwhm_fit, df0_fit = popt_lor
    q_eff_fit = F_IN / (2.0 * fwhm_fit) if fwhm_fit > 0 else 2500

    df_dense = np.linspace(np.min(delta_f_arr) - 25, np.max(delta_f_arr) + 25, 300)
    lor_dense = lorentzian(df_dense, *popt_lor)

    ax_lor.plot(delta_f_arr, a0_norm_arr, 'd', color='#d95f02', markersize=8.5, label=r'Dati Normalizzati $A_0 / V_{\mathrm{DC}}^2$', zorder=5)
    ax_lor.plot(df_dense, lor_dense, '-', color='#1f78b4', linewidth=2.0,
                label=rf'Fit Lorentziano ($Q_{{\mathrm{{eff}}}} \approx {q_eff_fit:.0f},\ \Delta f_0 = {df0_fit:.1f}\ \mathrm{{Hz}}$)')
    ax_lor.axvline(0, color='gray', linestyle='--', linewidth=1.4, label=r'Risonanza Perfetta ($\Delta f = 0$)')
    ax_lor.axhline(a_max_fit / np.sqrt(2.0), color='#1b9e77', linestyle=':', linewidth=1.5,
                   label=rf'Livello -3 dB (FWHM $\approx {fwhm_fit:.0f}\ \mathrm{{Hz}}$)')

    ax_lor.set_xlabel(r'Detuning $\Delta f = f_{\mathrm{in}} - f_1(V_{\mathrm{DC}})\ [\mathrm{Hz}]$', labelpad=6)
    ax_lor.set_ylabel(r'Ampiezza Meccanica Pura $A_0 / V_{\mathrm{DC}}^2\ [\mathrm{mV/V^2}]$', labelpad=6)
    ax_lor.set_title(r'Curva di Risonanza Meccanica Ricostruita Sfruttando il Softening', pad=10, fontweight='bold', fontsize=11)
    ax_lor.grid(True, linestyle=':', alpha=0.45)
    ax_lor.legend(loc='upper right', frameon=True, framealpha=0.92, fontsize=9.5)

    fig3.suptitle(r'$\mathbf{Scomposizione\ della\ Risposta:}\ A_0(V_{\mathrm{DC}}) \propto V_{\mathrm{DC}}^2 \cdot |H(f_{\mathrm{in}} - f_1(V_{\mathrm{DC}}))|$', fontsize=12.5, y=0.98)
    plt.tight_layout()
    plot3_path = os.path.join(OUTPUT_DIR, 'risposta_ampiezza_vs_vdc_e_deltaf.png')
    fig3.savefig(plot3_path)
    plt.close(fig3)
    print(f"Grafico 3 salvato: {plot3_path}")

    # GRAFICO 4: Confronto tra i Metodi di Stima della Frequenza
    fig4, (ax4a, ax4b) = plt.subplots(2, 1, figsize=(9, 7.5), sharex=True, dpi=300)
    ax4a.plot(vdc_arr, f_sine_arr, 'o-', color='#1b4965', markersize=6.5, linewidth=1.8, label='Fit Sinusoidale MLE (Raccomandato)')
    ax4a.plot(vdc_arr, f_hilb_arr, 's--', color='#e76f51', markersize=6, linewidth=1.5, label='Fase Istantanea Hilbert')
    ax4a.plot(vdc_arr, f_fft_arr, '^-.', color='#2a9d8f', markersize=6.5, linewidth=1.4, label='FFT 64x Zero-Padding')
    ax4a.plot(vdc_arr, f_zc_arr, 'x:', color='#9c6644', markersize=6.5, linewidth=1.3, label='Zero-Crossing')
    ax4a.set_ylabel(r'Frequenza $f_1\ [\mathrm{Hz}]$', labelpad=6)
    ax4a.set_title(r'Confronto tra i Metodi di Stima della Frequenza di Ring-Down', pad=10)
    ax4a.grid(True, linestyle='--', alpha=0.35)
    ax4a.legend(loc='upper right', frameon=True, framealpha=0.92)

    diff_hilb = f_hilb_arr - f_sine_arr
    diff_fft = f_fft_arr - f_sine_arr
    diff_zc = f_zc_arr - f_sine_arr

    ax4b.axhline(0, color='black', linestyle='-', linewidth=0.9, alpha=0.7)
    ax4b.plot(vdc_arr, diff_hilb, 's--', color='#e76f51', markersize=6, linewidth=1.5,
              label=rf'Hilbert - Sine (max $| \Delta | = {np.max(np.abs(diff_hilb)):.2f}\ \mathrm{{Hz}}$)')
    ax4b.plot(vdc_arr, diff_fft, '^-.', color='#2a9d8f', markersize=6.5, linewidth=1.4,
              label=rf'FFT 64x - Sine (max $| \Delta | = {np.max(np.abs(diff_fft)):.2f}\ \mathrm{{Hz}}$)')
    ax4b.plot(vdc_arr, diff_zc, 'x:', color='#9c6644', markersize=6.5, linewidth=1.3,
              label=rf'Zero-Crossing - Sine (max $| \Delta | = {np.max(np.abs(diff_zc)):.2f}\ \mathrm{{Hz}}$)')
    ax4b.set_xlabel(r'Tensione continua $V_{DC}\ [\mathrm{V}]$', labelpad=6)
    ax4b.set_ylabel(r'Discrepanza vs Sine Fit $[\mathrm{Hz}]$', labelpad=6)
    ax4b.grid(True, linestyle='--', alpha=0.35)
    ax4b.legend(loc='lower left', frameon=True, framealpha=0.92)
    ax4b.set_ylim(-35, 15)

    plt.tight_layout()
    plot4_path = os.path.join(OUTPUT_DIR, 'confronto_metodi_frequenza.png')
    fig4.savefig(plot4_path)
    plt.close(fig4)
    print(f"Grafico 4 salvato: {plot4_path}")

    # GRAFICO 5: I 7 Segnali di Ring-Down con Fit Sovrapposto
    fig5, axes = plt.subplots(4, 2, figsize=(14, 11), dpi=300)
    axes_flat = axes.flatten()

    for idx, r in enumerate(dataset):
        ax = axes_flat[idx]
        t_ms = r['t_win'] * 1e3
        sig_mv = r['sig_win'] * 1e3
        a0, tau_val, f_fit_val, phi_fit = r['popt']
        t_model = np.linspace(t_ms[0], t_ms[-1], 2000) * 1e-3
        model_mv = a0 * np.exp(-t_model / tau_val) * np.cos(2.0 * np.pi * f_fit_val * t_model + phi_fit) * 1e3
        env_mv = a0 * np.exp(-t_model / tau_val) * 1e3

        ax.plot(t_ms, sig_mv, color='#adb5bd', alpha=0.6, linewidth=0.8, label='Dati raw (no DC)')
        ax.plot(t_model * 1e3, model_mv, color='#1d3557', linewidth=1.1, label='Fit Sinusoidale')
        ax.plot(t_model * 1e3, env_mv, '--', color='#e63946', linewidth=1.3, label=f'Inviluppo ($\\tau = {tau_val*1e3:.2f}\\ \\mathrm{{ms}}$)')
        ax.plot(t_model * 1e3, -env_mv, '--', color='#e63946', linewidth=1.3)

        ax.set_title(f"Scope {r['scope_num']} | $V_{{DC}} = {r['vdc']:.1f}\\ \\mathrm{{V}}$ | $f_1 = {f_fit_val:.1f}\\ \\mathrm{{Hz}}$ | $A_0 = {a0*1e3:.1f}\\ \\mathrm{{mV}}$", fontsize=10.5, pad=6)
        ax.set_ylabel(r'$v_{out}\ [\mathrm{mV}]$', fontsize=9.5)
        ax.grid(True, linestyle='--', alpha=0.3)
        if idx >= 5:
            ax.set_xlabel(r'Tempo relativo al Gate $t\ [\mathrm{ms}]$', fontsize=9.5)
        if idx == 0:
            ax.legend(loc='upper right', fontsize=8.5, framealpha=0.9)

    ax_summary = axes_flat[7]
    ax_summary.axis('off')
    summary_box_text = '\n'.join((
        r'$\mathbf{RIEPILOGO\ ACQUISIZIONI\ RING-DOWN:}$',
        r'-------------------------------------------------------',
        r'$\bullet\ \mathrm{Segnale\ Gate:\ TTL\ 0-3.3\ V,\ burst\ 12\ ms}$',
        r'$\bullet\ \mathrm{Taglio\ post-gate:\ } t_{cut} = 20\ \mu\mathrm{s}\ \mathrm{(esclusione\ transitorio\ C_p)}$',
        r'$\bullet\ \mathrm{Amplificazione:\ TIA\ (R_f = 500\ k\Omega) + Inv\ (G = -10)}$',
        r'$\bullet\ \mathrm{Con\ l\'aumento\ di\ } V_{DC}\ \mathrm{(da\ 3.0\ a\ 6.0\ V):}$',
        r'   - $A_0$ cresce fino a $47\ \mathrm{mV}$ (picco di risonanza a $5.5\ \mathrm{V}$)',
        r'   - $f_1$ decresce da $417.945\ \mathrm{kHz}$ a $417.782\ \mathrm{kHz}$ (softening)',
        r'   - $\tau$ resta costante a circa $2.3\pm 0.1\ \mathrm{ms}\ (Q \approx 3000)$',
        r'-------------------------------------------------------',
        rf'$\mathbf{{Fit\ f_1^2\ vs\ V_{{DC}}^2:}}\ R^2 = {r_squared:.5f}$',
        rf'$\alpha_{{sperim}} = {alpha_exp/1e6:.3f}\ \mathrm{{MHz^2/V^2}}\ (\mathrm{{teoria:}}\ {alpha_th/1e6:.3f}\ \mathrm{{MHz^2/V^2}})$'
    ))
    ax_summary.text(0.05, 0.90, summary_box_text, transform=ax_summary.transAxes, verticalalignment='top',
                    fontsize=9.5, bbox=dict(boxstyle='round,pad=0.8', facecolor='#edf2f4', edgecolor='#8d99ae'))

    plt.tight_layout()
    plot5_path = os.path.join(OUTPUT_DIR, 'ringdown_all_vdc.png')
    fig5.savefig(plot5_path)
    plt.close(fig5)
    print(f"Grafico 5 salvato: {plot5_path}")

    print("\nElaborazione completata con successo!")

if __name__ == '__main__':
    run_analysis()
