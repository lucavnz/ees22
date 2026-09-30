"""
Analisi del Risonatore MEMS in Regime Non Lineare (Duffing):
1. Estrazione dell'ampiezza iniziale del ring-down A0 vs Tensione di eccitazione Vin (Compressione di guadagno / saturazione).
2. Tracciamento dell'evoluzione temporale della frequenza di risonanza f1(t) (Chirp intra-ringdown / Softening di Duffing).
3. Esportazione dei grafici ad alta risoluzione (300 DPI) e tabella numerica riassuntiva CSV.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, hilbert

# -----------------------------------------------------------------------------
# 1. Configurazione e Mappatura Vin Reale
# -----------------------------------------------------------------------------
# Generatore RF calibrato su 50 Ohm connesso a carico High-Z del MEMS:
# Vin_reale = 2 * Vin_nominale
DUFFING_MAP = {
    49: 80.0,
    51: 120.0,
    52: 160.0,
    53: 200.0,
    54: 240.0,
    55: 280.0,
    56: 340.0,
    57: 420.0,
    58: 500.0,
    59: 600.0,
    60: 700.0,
    61: 800.0,
    62: 900.0,
    63: 1000.0,
    64: 1200.0,
    65: 1500.0,
    66: 2000.0
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'Misure')

# Parametri di stile per grafici accademici/editoriali
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.labelsize': 11.5,
    'axes.titlesize': 12.5,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'lines.linewidth': 1.6,
    'grid.alpha': 0.5,
    'grid.linestyle': ':'
})


def load_scope_file(scope_num):
    """
    Carica il file CSV dell'oscilloscopio ignorando header e righe vuote.
    Ritorna:
        t: vettore dei tempi [s]
        ch1: uscita TIA [V]
        ch2: segnale di gate TTL [V]
        ch3: segnale di eccitazione Vin [V]
    """
    filepath = os.path.join(DATA_DIR, f'scope_{scope_num}.csv')
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File non trovato: {filepath}")
        
    data = []
    with open(filepath, 'r') as f:
        f.readline()  # Header 1
        f.readline()  # Header 2
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 4 and parts[1] != '':
                try:
                    data.append([float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])])
                except ValueError:
                    continue
    data = np.array(data)
    return data[:, 0], data[:, 1], data[:, 2], data[:, 3]


def process_ringdown_amplitude(scope_num, t_cut_us=20.0, fit_duration_ms=2.5):
    """
    Estrae l'ampiezza iniziale A0 e la costante di tempo tau del ringdown:
    1. Rileva il fronte di discesa del gate (spegnimento dell'eccitazione).
    2. Taglia i primi t_cut_us per escludere il transitorio di scarica parassita Cp.
    3. Isola la risonanza meccanica con un filtro passa-banda (390-445 kHz).
       Questo passaggio elimina completamente il drift di baseline a bassa frequenza
       (visibile in scope_57-59 come fittizio clipping/distorsione DC).
    4. Calcola l'inviluppo analitico di Hilbert e stima A0 e tau tramite fit log-lineare.
    """
    t, ch1, ch2, ch3 = load_scope_file(scope_num)
    dt = t[1] - t[0]
    fs = 1.0 / dt
    
    # 1. Rilevamento fronte di discesa Gate (soglia TTL a 1.2 V)
    gate_edges = np.where((ch2[:-1] > 1.2) & (ch2[1:] <= 1.2))[0]
    if len(gate_edges) == 0:
        raise ValueError(f"Fronte di discesa non trovato per scope_{scope_num}")
    g_idx = gate_edges[0]
    t_gate = t[g_idx]
    
    # 2. Finestra di analisi del ringdown escludendo il transitorio immediato
    i_start = g_idx + int(t_cut_us * 1e-6 / dt)
    i_end = g_idx + int(5.5e-3 / dt)  # fino a prima della riattivazione del gate
    
    t_ring = t[i_start:i_end] - t_gate
    sig_ring = ch1[i_start:i_end]
    
    # 3. Filtraggio passa-banda a fase zero attorno al picco (390 kHz - 445 kHz)
    b_bp, a_bp = butter(2, [390000.0 / (fs / 2), 445000.0 / (fs / 2)], btype='bandpass')
    sig_filt = filtfilt(b_bp, a_bp, sig_ring)
    
    # 4. Inviluppo di Hilbert
    analytic = hilbert(sig_filt)
    env = np.abs(analytic)
    
    # Fit esponenziale: ln(env) = ln(A0) - t / tau nella finestra [50 us, fit_duration_ms]
    mask_fit = (t_ring >= 50e-6) & (t_ring <= fit_duration_ms * 1e-3)
    p_log = np.polyfit(t_ring[mask_fit], np.log(env[mask_fit]), 1)
    
    tau = -1.0 / p_log[0]
    A0 = np.exp(p_log[1])  # Ampiezza estrapolata a t = 0 (spegnimento gate) [V]
    
    return {
        'scope_num': scope_num,
        'vin_mv': DUFFING_MAP[scope_num],
        'A0_mv': A0 * 1e3,
        'tau_ms': tau * 1e3
    }


def analyze_chirp(scope_num, t_eval, win_size=0.6e-3):
    """
    Stima la frequenza di risonanza f1(t) nel tempo con validità scientifica rigorosa:
    - Invece di una derivata numerica punto-punto della fase istantanea (che amplifica
      il rumore ad alta frequenza), si applica una regressione lineare (OLS) sulla fase
      dell'inviluppo analitico all'interno di una finestra temporale mobile.
    - La regressione lineare sulla fase sfrutta il teorema di Gauss-Markov, mediando
      il rumore di fase non correlato su centinaia di cicli e fornendo una risoluzione
      sub-Hertz priva di artefatti numerici.
    """
    t, ch1, ch2, ch3 = load_scope_file(scope_num)
    dt = t[1] - t[0]
    fs = 1.0 / dt
    
    g_idx = np.where((ch2[:-1] > 1.2) & (ch2[1:] <= 1.2))[0][0]
    t_gate = t[g_idx]
    
    # Isolamento dell'intervallo di ringdown
    i1 = g_idx + int(20e-6 / dt)
    i2 = g_idx + int(5.5e-3 / dt)
    t_cut = t[i1:i2] - t_gate
    ch1_cut = ch1[i1:i2]
    
    # Filtraggio passa-banda
    b_bp, a_bp = butter(2, [390000.0 / (fs / 2), 445000.0 / (fs / 2)], btype='bandpass')
    sig_filt = filtfilt(b_bp, a_bp, ch1_cut)
    
    # Fase istantanea srotolata
    analytic = hilbert(sig_filt)
    phase = np.unwrap(np.angle(analytic))
    
    freqs = []
    for tc in t_eval:
        mask = (t_cut >= tc - win_size / 2) & (t_cut <= tc + win_size / 2)
        if np.sum(mask) > 10:
            p = np.polyfit(t_cut[mask], phase[mask], 1)
            freqs.append(p[0] / (2.0 * np.pi))
        else:
            freqs.append(np.nan)
            
    return np.array(freqs)


def main():
    print("=" * 70)
    print("ANALISI DUFFING: AMPIEZZA E CHIRP INTRA-RINGDOWN")
    print("=" * 70)
    
    # -------------------------------------------------------------------------
    # 1. Analisi Ampiezza A0 vs Vin (Tutti i 17 file)
    # -------------------------------------------------------------------------
    results = []
    print("\nElaborazione ampiezza ringdown per tutti gli oscilloscopi...")
    for scope_num in sorted(DUFFING_MAP.keys()):
        res = process_ringdown_amplitude(scope_num)
        results.append(res)
        print(f"  Scope {scope_num:02d} | Vin = {res['vin_mv']:6.1f} mV | A0 = {res['A0_mv']:6.2f} mV | tau = {res['tau_ms']:.2f} ms")
        
    vins = np.array([r['vin_mv'] for r in results])
    a0s = np.array([r['A0_mv'] for r in results])
    
    # Fit lineare nella regione di piccolo segnale (Vin <= 280 mV)
    mask_lin = vins <= 280.0
    # Fit proporzionale passante per l'origine: A0 = k * Vin
    k_linear = np.sum(vins[mask_lin] * a0s[mask_lin]) / np.sum(vins[mask_lin]**2)
    print(f"\nGuadagno lineare di piccolo segnale k = {k_linear:.4f} mV/mV (per Vin <= 280 mV)")
    
    # -------------------------------------------------------------------------
    # GRAFICO 1: duffing_ampiezza_compressione.png
    # -------------------------------------------------------------------------
    fig1, ax1 = plt.subplots(figsize=(8.5, 6.0), dpi=300)
    
    v_fit_line = np.linspace(0, 2100, 100)
    ax1.plot(v_fit_line, k_linear * v_fit_line, linestyle='-', color='#1f77b4', 
             linewidth=2.0, label='Fit lineare', zorder=2)
    ax1.plot(vins, a0s, marker='o', markersize=6.5, linestyle='', color='#1f77b4', 
             label='Dati', zorder=3)
    
    ax1.set_title('Ampiezza ringdown vs tensione di eccitazione', pad=12)
    ax1.set_xlabel(r'Tensione di eccitazione $V_{\mathrm{in}}$ [$\mathrm{mV}_{\mathrm{pp}}$]')
    ax1.set_ylabel(r'Ampiezza iniziale ringdown $A_0$ [mV]')
    ax1.set_xlim(0, 2100)
    ax1.set_ylim(0, 300)
    ax1.grid(True, linestyle=':', alpha=0.55, color='#c0c0c0')
    ax1.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.9)
    
    plt.tight_layout()
    out_amp_path = os.path.join(BASE_DIR, 'duffing_ampiezza_compressione.png')
    fig1.savefig(out_amp_path, dpi=300)
    plt.close(fig1)
    print(f"\n[OK] Grafico 1 salvato in: {out_amp_path}")
    
    # -------------------------------------------------------------------------
    # GRAFICO 2: duffing_backbone_e_chirp.png
    # Tracciamento frequenza di risonanza f1 nel tempo per 4 tensioni
    # (Punti sperimentali privi di contorno grigio + Fit analitico convergente a f0 comune)
    # -------------------------------------------------------------------------
    from scipy.optimize import minimize
    
    chirp_configs = [
        (53, 200, '#2ca02c', 'o'),  # Verde: cerchi
        (58, 500, '#f39c12', 's'),  # Ambra: quadrati
        (63, 1000, '#e66101', '^'), # Arancio scuro: triangoli
        (66, 2000, '#c0392b', 'D')  # Rosso: rombi
    ]
    
    t_eval = np.arange(0.42e-3, 3.75e-3 + 1e-6, 0.06e-3)
    win_size = 0.75e-3  # Finestra mobile di 750 us
    t_dense = np.linspace(0.4e-3, 3.8e-3, 400)
    
    data_dict = {}
    print("\nElaborazione frequenza istantanea intra-ringdown:")
    for num, vin, color, marker in chirp_configs:
        t_arr, ch1_arr, ch2_arr, _ = load_scope_file(num)
        dt_val = t_arr[1] - t_arr[0]
        fs_val = 1.0 / dt_val
        g_idx_val = np.where((ch2_arr[:-1] > 1.2) & (ch2_arr[1:] <= 1.2))[0][0]
        t_gate_val = t_arr[g_idx_val]
        
        i1 = g_idx_val + int(20e-6 / dt_val)
        i2 = g_idx_val + int(5.5e-3 / dt_val)
        t_cut = t_arr[i1:i2] - t_gate_val
        ch1_cut = ch1_arr[i1:i2]
        
        b_bp, a_bp = butter(2, [390000.0 / (fs_val / 2), 445000.0 / (fs_val / 2)], btype='bandpass')
        sig_filt = filtfilt(b_bp, a_bp, ch1_cut)
        
        analytic = hilbert(sig_filt)
        phase = np.unwrap(np.angle(analytic))
        env = np.abs(analytic)
        
        freqs = []
        amps = []
        for tc in t_eval:
            m = (t_cut >= tc - win_size / 2) & (t_cut <= tc + win_size / 2)
            p = np.polyfit(t_cut[m], phase[m], 1)
            freqs.append(p[0] / (2.0 * np.pi))
            amps.append(np.mean(env[m]))
        freqs = np.array(freqs)
        amps = np.array(amps)
        
        # Pesi WLS basati sull'ampiezza locale
        sigma_vec = 1.0 / (amps / np.max(amps) + 0.05)
        data_dict[vin] = {
            'freqs': freqs,
            'sigma': sigma_vec,
            'color': color,
            'marker': marker
        }
        print(f"  Scope {num:02d} (Vin = {vin:4d} mV): f(0.42 ms) = {freqs[0]:.1f} Hz -> f(3.5 ms) = {freqs[-5]:.1f} Hz")
        
    # Fit congiunto globale con frequenza asintotica f0 comune a tutte e 4 le curve
    # Modello fisico: f(t; Vi) = f0 - Delta_f0_i * exp(-t / tau_f_i)
    def joint_loss(p):
        f0_c, df_500, tau_500, df_1000, tau_1000, df_2000, tau_2000 = p
        # 200 mV è in regime lineare: f(t) = f0_c
        chi_200 = np.sum(((data_dict[200]['freqs'] - f0_c) / data_dict[200]['sigma'])**2)
        # 500 mV
        f_500 = f0_c - df_500 * np.exp(-t_eval / tau_500)
        chi_500 = np.sum(((data_dict[500]['freqs'] - f_500) / data_dict[500]['sigma'])**2)
        # 1000 mV
        f_1000 = f0_c - df_1000 * np.exp(-t_eval / tau_1000)
        chi_1000 = np.sum(((data_dict[1000]['freqs'] - f_1000) / data_dict[1000]['sigma'])**2)
        # 2000 mV
        f_2000 = f0_c - df_2000 * np.exp(-t_eval / tau_2000)
        chi_2000 = np.sum(((data_dict[2000]['freqs'] - f_2000) / data_dict[2000]['sigma'])**2)
        return chi_200 + chi_500 + chi_1000 + chi_2000
        
    res_fit = minimize(
        joint_loss,
        [417786.0, 35.0, 1.0e-3, 95.0, 1.1e-3, 160.0, 1.05e-3],
        bounds=[
            (417775, 417795),
            (10, 80), (0.5e-3, 2.0e-3),
            (50, 150), (0.5e-3, 2.0e-3),
            (100, 250), (0.5e-3, 2.0e-3)
        ]
    )
    
    f0_common, df_500_opt, tau_500_opt, df_1000_opt, tau_1000_opt, df_2000_opt, tau_2000_opt = res_fit.x
    print(f"\nFrequenza asintotica lineare comune f0 = {f0_common:.2f} Hz")
    print(f"  500 mV:  Delta f0 = {df_500_opt:.2f} Hz, tau_f = {tau_500_opt*1e3:.2f} ms")
    print(f"  1000 mV: Delta f0 = {df_1000_opt:.2f} Hz, tau_f = {tau_1000_opt*1e3:.2f} ms")
    print(f"  2000 mV: Delta f0 = {df_2000_opt:.2f} Hz, tau_f = {tau_2000_opt*1e3:.2f} ms")
    
    fig2, ax2 = plt.subplots(figsize=(8.5, 6.0), dpi=300)
    
    fit_curves = {
        200: np.full_like(t_dense, f0_common),
        500: f0_common - df_500_opt * np.exp(-t_dense / tau_500_opt),
        1000: f0_common - df_1000_opt * np.exp(-t_dense / tau_1000_opt),
        2000: f0_common - df_2000_opt * np.exp(-t_dense / tau_2000_opt)
    }
    
    for vin in [200, 500, 1000, 2000]:
        d = data_dict[vin]
        col = d['color']
        m = d['marker']
        f_exp = d['freqs']
        f_th = fit_curves[vin]
        
        # Punti sperimentali senza contorno grigio
        ax2.scatter(t_eval * 1e3, f_exp, marker=m, s=32, color=col,
                    alpha=0.65, edgecolors='none', zorder=3)
        # Linea di fit liscia continua
        ax2.plot(t_dense * 1e3, f_th, color=col, linewidth=2.2, zorder=4,
                 label=f"$V_{{\\mathrm{{in}}}} = {vin}\\ \\mathrm{{mV}}$")
                     
    ax2.set_title(r'Frequenza di risonanza $f_1$ nel tempo', pad=12)
    ax2.set_xlabel('Tempo dal taglio del gate [ms]')
    ax2.set_ylabel(r'Frequenza di risonanza $f_1$ [Hz]')
    ax2.set_xlim(0.33, 3.82)
    ax2.set_ylim(417668, 417818)
    ax2.grid(True, linestyle=':', alpha=0.55, color='#c0c0c0')
    ax2.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.92, fontsize=10.5)
    
    plt.tight_layout()
    out_chirp_path = os.path.join(BASE_DIR, 'duffing_backbone_e_chirp.png')
    fig2.savefig(out_chirp_path, dpi=300)
    plt.close(fig2)
    print(f"[OK] Grafico 2 salvato in: {out_chirp_path}")
    
    # -------------------------------------------------------------------------
    # Esportazione Risultati Tabulari in CSV
    # -------------------------------------------------------------------------
    csv_out_path = os.path.join(BASE_DIR, 'duffing_risultati.csv')
    with open(csv_out_path, 'w') as f:
        f.write("scope_num,vin_reale_mv,A0_mv,tau_ms\n")
        for r in results:
            f.write(f"{r['scope_num']},{r['vin_mv']:.1f},{r['A0_mv']:.4f},{r['tau_ms']:.4f}\n")
    print(f"[OK] Dati numerici salvati in: {csv_out_path}")
    print("=" * 70)


if __name__ == '__main__':
    main()
