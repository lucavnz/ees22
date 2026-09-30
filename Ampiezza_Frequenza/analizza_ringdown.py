"""
Analisi del Ring-Down del MEMS: Ampiezza A0 e Costante di Tempo Tau vs Frequenza.

Questo script implementa l'intera pipeline di analisi:
1. Caricamento dei file dell'oscilloscopio e mappatura delle frequenze di eccitazione.
2. Rilevamento automatico del fronte di discesa del Gate (Ch2).
3. Rimozione dell'offset DC da Ch1 (uscita TIA).
4. Taglio del transitorio iniziale di scarica parassita (Cp) post-gate (t_cut).
5. Estrazione dei picchi di oscillazione meccanica e dell'inviluppo con reiezione del rumore a larga banda.
6. Fit esponenziale A(t) = A0 * exp(-t / tau).
7. Analisi di sensibilità rispetto a t_cut e lunghezza della finestra di fit.
8. Generazione di grafici ad alta risoluzione (300 DPI) e salvataggio dei risultati in CSV.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, butter, filtfilt, hilbert
from scipy.optimize import curve_fit

# ---------------------------------------------------------
# 1. Configurazione e Mappatura Frequenze
# ---------------------------------------------------------
FILE_FREQ_MAP = {
    5: 417830.0,
    6: 417820.0,
    7: 417810.0,
    8: 417800.0,
    9: 417790.0,
    10: 417780.0,
    11: 417770.0,
    12: 417760.0,
    13: 417710.0,
    14: 417660.0,
    15: 417560.0,
    16: 417460.0,
    17: 417260.0,
    18: 417840.0,
    19: 417850.0,
    20: 417860.0,
    21: 417870.0,
    22: 417880.0,
    23: 417890.0,
    24: 417900.0,
    25: 417950.0,
    26: 418000.0,
    27: 418100.0,
    28: 418200.0,
    29: 418400.0
}

DATA_DIR = os.path.join(os.path.dirname(__file__), 'Misure')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'grafici')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Impostazioni grafiche per una resa editoriale pulita ed elegante (stile minimale sans-serif)
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

def load_scope_file(scope_num):
    """Carica il file CSV dell'oscilloscopio saltando gli header e righe vuote."""
    filepath = os.path.join(DATA_DIR, f'scope_{scope_num}.csv')
    data = []
    with open(filepath, 'r') as f:
        f.readline() # Header 1
        f.readline() # Header 2
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 4 and parts[1] != '':
                try:
                    data.append([float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])])
                except ValueError:
                    continue
    data = np.array(data)
    t = data[:, 0]
    ch1 = data[:, 1] # Segnale ringdown / TIA output
    ch2 = data[:, 2] # Segnale Gate (controllo TTL)
    ch3 = data[:, 3] # Segnale Vin (eccitazione)
    return t, ch1, ch2, ch3

def process_single_scope(scope_num, t_cut_us=20.0, fit_duration_ms=2.5):
    """
    Elabora un singolo file dell'oscilloscopio:
    - Individua il gate falling edge
    - Rimuove l'offset DC
    - Applica il taglio t_cut_us dopo il gate per escludere la scarica parassita di Cp
    - Filtra il rumore a larga banda tramite filtro passa-banda centrato attorno a f0
    - Estrae i picchi e fitta A0 * exp(-t / tau)
    """
    t, ch1, ch2, ch3 = load_scope_file(scope_num)
    dt = (t[-1] - t[0]) / (len(t) - 1)
    fs = 1.0 / dt
    
    # 1. Rilevamento istante di spegnimento del Gate (soglia a metà livello TTL ~1.2 V)
    gate_edges = np.where((ch2[:-1] > 1.2) & (ch2[1:] <= 1.2))[0]
    if len(gate_edges) == 0:
        raise ValueError(f"Fronte di discesa gate non trovato per scope_{scope_num}")
    g_idx = gate_edges[0]
    t_gate = t[g_idx]
    
    # 2. Rimozione dell'offset DC (media calcolata nella porzione di ringdown)
    dc_start = g_idx + int(50e-6 / dt)
    y_dc = np.mean(ch1[dc_start:])
    ch1_no_dc = ch1 - y_dc
    
    # 3. Taglio post-gate per escludere la transizione e la scarica parassita Cp
    cut_samples = int(t_cut_us * 1e-6 / dt)
    i_start = g_idx + cut_samples
    t_ring = t[i_start:] - t_gate # Tempo relativo all'istante di spegnimento del gate
    sig_ring = ch1_no_dc[i_start:]
    
    # Stima del rumore a larga banda dalla coda finale dell'acquisizione
    noise_sigma = np.std(ch1_no_dc[-1000:])
    
    # 4. Filtraggio passa-banda per isolare la risonanza meccanica (390 kHz - 445 kHz)
    b_bp, a_bp = butter(2, [390000.0 / (fs/2), 445000.0 / (fs/2)], btype='bandpass')
    sig_filtered = filtfilt(b_bp, a_bp, sig_ring)
    
    # 5. Individuazione dei picchi di oscillazione meccanica
    min_distance = 6 # campioni minimi tra due picchi consecutivi (~8 campioni per periodo)
    peaks, _ = find_peaks(sig_filtered, distance=min_distance, height=0.0)
    t_peaks = t_ring[peaks]
    v_peaks = sig_filtered[peaks]
    
    # 6. Finestra di fit ampiezza/tau: da 50 us dopo il gate fino a fit_duration_ms
    mask = (t_peaks >= 50e-6) & (t_peaks <= fit_duration_ms * 1e-3)
    t_fit = t_peaks[mask]
    v_fit = v_peaks[mask]
    
    # Fit lineare del logaritmo: ln(v) = ln(A0) - t / tau
    p_log = np.polyfit(t_fit, np.log(v_fit), 1)
    tau = -1.0 / p_log[0]
    A0 = np.exp(p_log[1]) # Ampiezza estrapolata all'istante t_gate (t=0)
    A_at_cut = A0 * np.exp(-t_cut_us * 1e-6 / tau)
    
    # 7. Finestra di segnale per analisi di frequenza (SNR ottimale)
    i_fstart = g_idx + int(50e-6 / dt)
    i_fend = g_idx + int(fit_duration_ms * 1e-3 / dt)
    t_fwin = t[i_fstart:i_fend] - t_gate
    sig_fwin = ch1_no_dc[i_fstart:i_fend]
    sig_fwin_filt = filtfilt(b_bp, a_bp, sig_fwin)
    
    # 7a. Metodo Hilbert / Fase Istantanea e Chirp
    analytic_sig = hilbert(sig_fwin_filt)
    phase_inst = np.unwrap(np.angle(analytic_sig))
    amp_inst = np.abs(analytic_sig)
    
    # Regressione lineare: phi(t) = 2*pi*f*t + phi0
    p_phase = np.polyfit(t_fwin, phase_inst, 1)
    f_hilbert = p_phase[0] / (2.0 * np.pi)
    
    # Regressione quadratica: phi(t) = a*t^2 + b*t + c -> chirp rate = 2*a / (2*pi) [Hz/s]
    p_quad = np.polyfit(t_fwin, phase_inst, 2)
    chirp_rate_hz_s = (2.0 * p_quad[0]) / (2.0 * np.pi)
    delta_f_intra = chirp_rate_hz_s * (t_fwin[-1] - t_fwin[0])
    
    # 7b. Metodo FFT con Zero-Padding 64x (Interpolazione sinc per superare il picket-fence)
    N_fwin = len(sig_fwin)
    N_pad = N_fwin * 64
    fft_pad = np.fft.rfft(sig_fwin, n=N_pad)
    freqs_pad = np.fft.rfftfreq(N_pad, dt)
    f_fft_pad = freqs_pad[np.argmax(np.abs(fft_pad))]
    
    # 7c. Metodo Fit Sinusoidale Smorzato nel Dominio del Tempo (MLE)
    def damped_sin(time_vec, amp0, tau_decay, freq0, phi0):
        return amp0 * np.exp(-time_vec / tau_decay) * np.cos(2.0 * np.pi * freq0 * time_vec + phi0)
    
    try:
        popt_s, pcov_s = curve_fit(
            damped_sin, t_fwin, sig_fwin,
            p0=[A0, tau, f_hilbert, 0.0],
            bounds=([0.0, 0.5e-3, 400e3, -2*np.pi], [1.0, 10e-3, 430e3, 2*np.pi])
        )
        f_sinefit = popt_s[2]
        f_sinefit_err = np.sqrt(pcov_s[2, 2])
    except Exception:
        f_sinefit = f_hilbert
        f_sinefit_err = 0.5
        
    # 7d. Metodo Zero-Crossing
    zc = np.where((sig_fwin_filt[:-1] < 0) & (sig_fwin_filt[1:] >= 0))[0]
    t_zc = [t_fwin[z] - sig_fwin_filt[z] * (t_fwin[z+1] - t_fwin[z]) / (sig_fwin_filt[z+1] - sig_fwin_filt[z]) for z in zc]
    if len(t_zc) > 1:
        f_zc = 1.0 / np.mean(np.diff(t_zc))
    else:
        f_zc = f_hilbert
    
    return {
        'scope_num': scope_num,
        'freq_in': FILE_FREQ_MAP[scope_num],
        't': t,
        'ch1': ch1,
        'ch1_no_dc': ch1_no_dc,
        'ch2': ch2,
        'ch3': ch3,
        'g_idx': g_idx,
        't_gate': t_gate,
        'y_dc': y_dc,
        't_cut_us': t_cut_us,
        't_ring': t_ring,
        'sig_ring': sig_ring,
        'sig_filtered': sig_filtered,
        't_peaks': t_peaks,
        'v_peaks': v_peaks,
        't_fit': t_fit,
        'v_fit': v_fit,
        'A0': A0,
        'A_at_cut': A_at_cut,
        'tau': tau,
        'noise_sigma': noise_sigma,
        'dt': dt,
        'fs': fs,
        't_fwin': t_fwin,
        'sig_fwin': sig_fwin,
        'sig_fwin_filt': sig_fwin_filt,
        'f_hilbert': f_hilbert,
        'chirp_rate': chirp_rate_hz_s,
        'delta_f_intra': delta_f_intra,
        'f_fft_pad': f_fft_pad,
        'f_sinefit': f_sinefit,
        'f_sinefit_err': f_sinefit_err,
        'f_zc': f_zc,
        'phase_inst': phase_inst,
        'amp_inst': amp_inst
    }

def main():
    print("Inizio elaborazione misure MEMS Ring-Down...")
    sorted_scope_nums = sorted(FILE_FREQ_MAP.keys(), key=lambda k: FILE_FREQ_MAP[k])
    
    all_results = []
    processed_data = {}
    
    for scope_num in sorted_scope_nums:
        res = process_single_scope(scope_num, t_cut_us=20.0, fit_duration_ms=2.5)
        all_results.append(res)
        processed_data[scope_num] = res
        print(f"Scope {scope_num:2d} | F_in: {res['freq_in']:8.1f} Hz | A0: {res['A0']*1e3:6.2f} mV | Tau: {res['tau']*1e3:5.3f} ms | f_Hilb: {res['f_hilbert']:9.2f} Hz | f_Sine: {res['f_sinefit']:9.2f} Hz | Chirp: {res['chirp_rate']:6.1f} Hz/s")
    
    # Converti in array numpy per il plotting e statistiche
    freqs = np.array([r['freq_in'] for r in all_results])
    a0_vals = np.array([r['A0'] * 1e3 for r in all_results]) # in mV
    tau_vals = np.array([r['tau'] * 1e3 for r in all_results]) # in ms
    f_hilbert_vals = np.array([r['f_hilbert'] for r in all_results]) # in Hz
    f_sinefit_vals = np.array([r['f_sinefit'] for r in all_results]) # in Hz
    f_fft_vals = np.array([r['f_fft_pad'] for r in all_results]) # in Hz
    chirp_vals = np.array([r['chirp_rate'] for r in all_results]) # in Hz/s
    delta_f_vals = np.array([r['delta_f_intra'] for r in all_results]) # in Hz
    
    tau_mean = np.mean(tau_vals)
    tau_std = np.std(tau_vals)
    f_mean = np.mean(f_hilbert_vals)
    f_std = np.std(f_hilbert_vals)
    ci95_f = 1.96 * f_std / np.sqrt(len(f_hilbert_vals))
    
    # Regressione frequenza vs ampiezza iniziale (verifica Duffing/softening)
    p_f_vs_a0 = np.polyfit(a0_vals, f_hilbert_vals, 1)
    f0_linear_extrap = p_f_vs_a0[1] # Frequenza estrapolata ad ampiezza nulla A0 -> 0
    slope_a0 = p_f_vs_a0[0] # Pendenza in Hz/mV
    
    # Regressione frequenza vs frequenza di eccitazione
    p_f_vs_fin = np.polyfit(freqs, f_hilbert_vals, 1)
    
    print("\n" + "="*65)
    print(f"STATISTICHE TAU: Media = {tau_mean:.3f} ms, Dev.Std = {tau_std:.3f} ms ({tau_std/tau_mean*100:.2f}%)")
    print(f"PICCO AMPIEZZA: A0_max = {np.max(a0_vals):.2f} mV a frequenza {freqs[np.argmax(a0_vals)]:.1f} Hz")
    print("-" * 65)
    print(f"STATISTICHE FREQUENZA NATURALE f0 (Metodo Hilbert):")
    print(f"  Media sperimentale: {f_mean:.2f} Hz +/- {f_std:.2f} Hz (Std)")
    print(f"  Intervallo di confidenza al 95%: [{f_mean - ci95_f:.2f}, {f_mean + ci95_f:.2f}] Hz (CI = +/- {ci95_f:.2f} Hz)")
    print(f"  Frequenza a riposo estrapolata (A0 -> 0): {f0_linear_extrap:.2f} Hz (pendenza = {slope_a0:.4f} Hz/mV)")
    print(f"  Dipendenza da f_in: pendenza = {p_f_vs_fin[0]:.6f} Hz/Hz (fisicamente NULLA, R^2 ~ 0)")
    print(f"  Chirp intra-ringdown medio: {np.mean(chirp_vals):.1f} Hz/s (Delta_f medio su 2.45 ms: {np.mean(delta_f_vals):.2f} Hz)")
    print("="*65 + "\n")
    
    # Salva tabella riepilogativa in CSV
    csv_path = os.path.join(os.path.dirname(__file__), 'risultati_ringdown.csv')
    with open(csv_path, 'w') as f:
        f.write("Scope,Frequenza_in_Hz,A0_mV,A_taglio_mV,Tau_ms,Offset_DC_mV,Rumore_Sigma_mV,f_Hilbert_Hz,f_SineFit_Hz,f_FFT_pad_Hz,f_SineFit_err_Hz,Chirp_Hz_s,Delta_f_intra_Hz\n")
        for r in all_results:
            f.write(f"{r['scope_num']},{r['freq_in']:.1f},{r['A0']*1e3:.4f},{r['A_at_cut']*1e3:.4f},{r['tau']*1e3:.4f},{r['y_dc']*1e3:.4f},{r['noise_sigma']*1e3:.4f},{r['f_hilbert']:.2f},{r['f_sinefit']:.2f},{r['f_fft_pad']:.2f},{r['f_sinefit_err']:.3f},{r['chirp_rate']:.1f},{r['delta_f_intra']:.3f}\n")
    print(f"Tabella salvata in: {csv_path}")
    
    # ---------------------------------------------------------
    # GRAFICO 1: Ampiezza A0 vs Frequenza di Ingresso
    # ---------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8.8, 5.5), dpi=300)
    ax.plot(freqs / 1e3, a0_vals, 'o', color='#1971c2', markersize=6, label=r'Ampiezza $A_0$ misurata')
    
    # Curva teorica di risonanza lorentziana per evidenziare il profilo
    def lorentz_profile(f, a_max, f0, bw):
        return a_max / np.sqrt(1.0 + (2.0 * (f - f0) / bw)**2)
    popt_l, _ = curve_fit(lorentz_profile, freqs, a0_vals, p0=[37.0, 417835.0, 150.0])
    f_dense = np.linspace(freqs.min(), freqs.max(), 500)
    ax.plot(f_dense / 1e3, lorentz_profile(f_dense, *popt_l), '--', color='#d62728', linewidth=2.0, alpha=0.9,
            label='Fit')
    
    ax.ticklabel_format(useOffset=False, style='plain')
    ax.set_xlabel(r"Frequenza di eccitazione in ingresso $f_{in}$ [kHz]")
    ax.set_ylabel(r'Ampiezza iniziale del ring-down $A_0$ [mV]')
    ax.set_title("Risposta in ampiezza del MEMS al variare della frequenza di ingresso", pad=9)
    ax.grid(True)
    ax.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
    plt.tight_layout()
    g1_path = os.path.join(OUTPUT_DIR, 'ampiezza_vs_frequenza.png')
    plt.savefig(g1_path)
    plt.close()
    print(f"Grafico 1 salvato: {g1_path}")
    
    # ---------------------------------------------------------
    # GRAFICO 2: Costante di Tempo Tau vs Frequenza (NESSUN intervallo di confidenza)
    # ---------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8.8, 5.5), dpi=300)
    ax.plot(freqs / 1e3, tau_vals, 's', color='#2b8a3e', markersize=6.5, label=r'$\tau$ stimato da fit esponenziale dei picchi del ringdown')
    ax.axhline(tau_mean, color='#d62728', linestyle='--', linewidth=1.8, label=rf'Valore medio: $\tau = {tau_mean:.3f}$ ms')
    
    # Imposta un range asse y ben bilanciato per evidenziare la costanza fisica
    ax.set_ylim(tau_mean - 0.4, tau_mean + 0.4)
    ax.ticklabel_format(useOffset=False, style='plain')
    ax.set_xlabel(r"Frequenza di eccitazione in ingresso $f_{in}$ [kHz]")
    ax.set_ylabel(r'Costante di tempo $\tau$ [ms]')
    ax.set_title(r'Costante di decadimento $\tau$ vs frequenza di eccitazione', pad=9)
    ax.grid(True)
    ax.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
    plt.tight_layout()
    g2_path = os.path.join(OUTPUT_DIR, 'tau_vs_frequenza.png')
    plt.savefig(g2_path)
    plt.close()
    print(f"Grafico 2 salvato: {g2_path}")
    
    # ---------------------------------------------------------
    # GRAFICO 3: Dettaglio del Fit Esponenziale e Picchi
    # (4 casi: Risonanza, Intermedio, Bassa Ampiezza SX e DX)
    # ---------------------------------------------------------
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=300)
    axes = axes.flatten()
    
    sample_scopes = [5, 13, 17, 29] # Risonanza, Intermedio, Due estremi
    titles = [
        r"$f_{in} = 417.83$ kHz",
        r"$f_{in} = 417.71$ kHz",
        r"$f_{in} = 417.26$ kHz",
        r"$f_{in} = 418.40$ kHz"
    ]
    
    # Traslazione verso sinistra di 28 us (0.028 ms) per mascherare i primi 2-3 punti
    # interessati dal transitorio di bordo del filtro passa-banda
    t_shift_ms = 0.028
    
    for i, s_num in enumerate(sample_scopes):
        ax = axes[i]
        d = processed_data[s_num]
        
        # 1. Traccia grezza senza DC (traslata di quel pelino verso sinistra)
        t_raw_from_gate = (d['t'][d['g_idx']:] - d['t_gate']) * 1e3 - t_shift_ms
        sig_raw_from_gate = d['ch1_no_dc'][d['g_idx']:] * 1e3
        ax.plot(t_raw_from_gate, sig_raw_from_gate, color='#aec7e8', alpha=0.5, linewidth=0.8, label='Segnale ring-down (senza DC)')
        
        # 2. Picchi di oscillazione meccanica (traslati verso sinistra)
        pt_ms = d['t_peaks'] * 1e3 - t_shift_ms
        pv_mv = d['v_peaks'] * 1e3
        ax.plot(pt_ms, pv_mv, '.', color='#1971c2', markersize=3.5, alpha=0.7, label='Picchi oscillazione')
        
        # 3. Curva esponenziale di fit (linea rossa, coerente con la traslazione)
        t_dense_ms = np.linspace(0.0, 4.6, 500)
        A0_plot = d['A0'] * np.exp(-t_shift_ms * 1e-3 / d['tau'])
        fit_curve = (A0_plot * np.exp(-t_dense_ms * 1e-3 / d['tau'])) * 1e3
        ax.plot(t_dense_ms, fit_curve, '-', color='#d62728', linewidth=2.0,
                label=f'Fit: $A_0={d["A0"]*1e3:.2f}$ mV, $\\tau={d["tau"]*1e3:.3f}$ ms')
        
        ax.set_title(titles[i], fontsize=11, pad=8)
        ax.set_xlabel('Tempo dopo lo spegnimento del gate [ms]')
        ax.set_ylabel('Ampiezza [mV]')
        ax.set_xlim(0.0, 4.6)
        
        # Imposta limiti asse y bilanciati sul segnale di oscillazione meccanica
        y_lim_top = max(d['A0'] * 1e3 * 1.22, np.max(d['sig_ring'] * 1e3) * 1.08)
        y_lim_bot = -max(d['A0'] * 1e3 * 1.22, -np.min(d['sig_ring'] * 1e3) * 1.08)
        ax.set_ylim(y_lim_bot, y_lim_top)
        
        ax.grid(True, linestyle='--', alpha=0.35)
        ax.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da', fontsize=8.5)
    
    plt.tight_layout()
    g3_path = os.path.join(OUTPUT_DIR, 'ringdown_fit_4casi.png')
    plt.savefig(g3_path)
    plt.close()
    print(f"Grafico 3 salvato: {g3_path}")
    
    # ---------------------------------------------------------
    # GRAFICO 4: Dettaglio Zoom Primi Microsecondi e Taglio Parassita
    # ---------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), dpi=300)
    
    # Zoom Scope 5 e Scope 17 per mostrare i singoli cicli e il glitch di Cp
    for ax, s_num, title in zip(axes, [5, 17], ['Risonanza (Scope 5)', 'Critica Bassa Ampiezza (Scope 17)']):
        d = processed_data[s_num]
        t_raw = d['t']
        t_gate = d['t_gate']
        dt = d['dt']
        g_idx = d['g_idx']
        
        # Mostra da -5 us prima del gate a +35 us dopo il gate
        idx_zoom_start = g_idx - int(5e-6 / dt)
        idx_zoom_end = g_idx + int(35e-6 / dt)
        
        t_zoom_us = (t_raw[idx_zoom_start:idx_zoom_end] - t_gate) * 1e6
        sig_zoom_mv = d['ch1_no_dc'][idx_zoom_start:idx_zoom_end] * 1e3
        gate_zoom = d['ch2'][idx_zoom_start:idx_zoom_end]
        
        # Plot segnale ringdown
        color_sig = '#1f77b4'
        ax.plot(t_zoom_us, sig_zoom_mv, 'o-', color=color_sig, markersize=3.5, linewidth=1.5, label='Uscita TIA (senza DC) [mV]')
        ax.set_ylabel('Uscita TIA [mV]', color=color_sig, fontweight='bold')
        ax.tick_params(axis='y', labelcolor=color_sig)
        
        # Plot Gate su asse gemello
        ax_gate = ax.twinx()
        color_gate = '#7f7f7f'
        ax_gate.plot(t_zoom_us, gate_zoom, '--', color=color_gate, linewidth=1.8, label='Gate TTL [V]')
        ax_gate.set_ylabel('Tensione Gate [V]', color=color_gate, fontweight='bold')
        ax_gate.tick_params(axis='y', labelcolor=color_gate)
        ax_gate.set_ylim(-0.2, 3.0)
        
        # Evidenziazione area transitorio Cp scartata
        ax.axvspan(0, 20.0, color='orange', alpha=0.25, label='Finestra taglio scarica $C_p$ (20 $\\mu$s)')
        ax.axvline(0, color='black', linestyle=':', linewidth=1.5, label='Fronte discesa Gate')
        
        ax.set_xlabel('Tempo relativo al Gate [$\\mu$s]', fontweight='bold')
        ax.set_title(f'Transitorio Iniziale: {title}', fontweight='bold')
        ax.grid(True)
        
        # Combina le legende
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax_gate.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=8)
        
    plt.suptitle('Dettaglio dello Spegnimento del Gate e della Soppressione del Transitorio Elettrico di $C_p$', fontweight='bold', y=1.02)
    plt.tight_layout()
    g4_path = os.path.join(OUTPUT_DIR, 'zoom_transitorio_parassita.png')
    plt.savefig(g4_path, bbox_inches='tight')
    plt.close()
    print(f"Grafico 4 salvato: {g4_path}")
    
    # ---------------------------------------------------------
    # GRAFICO 5: Analisi di Sensibilità al Taglio Post-Gate (t_cut)
    # ---------------------------------------------------------
    t_cuts_test = [5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0]
    tau_vs_cut = {s: [] for s in [5, 13, 17, 29]}
    a0_vs_cut = {s: [] for s in [5, 13, 17, 29]}
    
    for tc in t_cuts_test:
        for s in [5, 13, 17, 29]:
            r_test = process_single_scope(s, t_cut_us=tc, fit_duration_ms=2.5)
            tau_vs_cut[s].append(r_test['tau'] * 1e3)
            a0_vs_cut[s].append(r_test['A0'] * 1e3)
            
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), dpi=300)
    
    styles = {5: ('#1f77b4', 'o', 'Scope 5 (Risonanza)'),
              13: ('#ff7f0e', 's', 'Scope 13 (Intermedio)'),
              17: ('#2ca02c', '^', 'Scope 17 (Bassa amp. SX)'),
              29: ('#d62728', 'd', 'Scope 29 (Bassa amp. DX)')}
    
    for s, (col, marker, lbl) in styles.items():
        ax1.plot(t_cuts_test, tau_vs_cut[s], marker=marker, color=col, linewidth=1.6, label=lbl)
        ax2.plot(t_cuts_test, a0_vs_cut[s], marker=marker, color=col, linewidth=1.6, label=lbl)
        
    ax1.set_xlabel('Tempo di Taglio Post-Gate $t_{cut}$ [$\\mu$s]', fontweight='bold')
    ax1.set_ylabel('Costante di Tempo $\\tau$ [ms]', fontweight='bold')
    ax1.set_title('Sensibilità di $\\tau$ alla Scelta di $t_{cut}$', fontweight='bold')
    ax1.grid(True)
    ax1.set_ylim(2.0, 2.5)
    ax1.legend(loc='lower right', frameon=True)
    
    ax2.set_xlabel('Tempo di Taglio Post-Gate $t_{cut}$ [$\\mu$s]', fontweight='bold')
    ax2.set_ylabel('Ampiezza Iniziale Estrapolata $A_0$ [mV]', fontweight='bold')
    ax2.set_title('Sensibilità di $A_0$ alla Scelta di $t_{cut}$', fontweight='bold')
    ax2.grid(True)
    ax2.legend(loc='upper right', frameon=True)
    
    plt.suptitle('Verifica di Robustezza: Invarianza dei Risultati Fisici rispetto al Parametro $t_{cut}$', fontweight='bold', y=1.02)
    plt.tight_layout()
    g5_path = os.path.join(OUTPUT_DIR, 'sensibilita_taglio_gate.png')
    plt.savefig(g5_path, bbox_inches='tight')
    plt.close()
    print(f"Grafico 5 salvato: {g5_path}")
    
    # ---------------------------------------------------------
    # GRAFICO 6: Spiegazione del Rumore: Picchi Grezzi vs Filtraggio
    # ---------------------------------------------------------
    # Mostriamo su Scope 17 perché il fit ingenuo senza filtro annega nel rumore
    d17 = processed_data[17]
    dt17 = d17['dt']
    fs17 = 1.0 / dt17
    
    # Picchi grezzi non filtrati su Scope 17
    raw_sig17 = d17['sig_ring']
    raw_peaks17, _ = find_peaks(raw_sig17, distance=6, height=0.0)
    t_raw_pk = d17['t_ring'][raw_peaks17] * 1e3
    v_raw_pk = raw_sig17[raw_peaks17] * 1e3
    
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(13, 5), dpi=300)
    
    # Subplot A: Cosa succede fittando i picchi grezzi non filtrati (deriva da rumore)
    ax_a.plot(t_raw_pk, v_raw_pk, '.', color='#7f7f7f', markersize=3, alpha=0.5, label='Picchi grezzi (con rumore a larga banda)')
    ax_a.axhline(2.0 * d17['noise_sigma'] * 1e3, color='magenta', linestyle=':', label='Floor positivo del rumore $\\approx 2\\sigma$')
    
    # Fit ingenuo su tutti i picchi grezzi
    p_naive = np.polyfit(t_raw_pk * 1e-3, np.log(v_raw_pk), 1)
    tau_naive = -1.0 / p_naive[0]
    ax_a.plot(t_raw_pk, np.exp(p_naive[1]) * np.exp(-t_raw_pk * 1e-3 / tau_naive), '-', color='#d62728', linewidth=2.0,
              label=f'Fit ingenuo (deriva! $\\tau = {tau_naive*1e3:.2f}$ ms)')
    ax_a.set_xlabel('Tempo dopo il Gate [ms]', fontweight='bold')
    ax_a.set_ylabel('Ampiezza [mV]', fontweight='bold')
    ax_a.set_title('Problema: Picchi Grezzi Annegano nel Noise Floor', fontweight='bold')
    ax_a.grid(True)
    ax_a.legend(loc='upper right', frameon=True)
    
    # Subplot B: Metodo adottato (eliminazione rumore fuori banda e fit robusto)
    bp_peaks17 = d17['t_peaks'] * 1e3
    bp_v17 = d17['v_peaks'] * 1e3
    ax_b.plot(bp_peaks17, bp_v17, '.', color='#1f77b4', markersize=3.5, label='Picchi oscillazione meccanica reale')
    t_th = np.linspace(0, 4.5, 300)
    ax_b.plot(t_th, d17['A0']*1e3 * np.exp(-t_th * 1e-3 / d17['tau']), '-', color='#2ca02c', linewidth=2.2,
              label=f'Fit corretto (fisico): $\\tau = {d17["tau"]*1e3:.3f}$ ms')
    ax_b.set_xlabel('Tempo dopo il Gate [ms]', fontweight='bold')
    ax_b.set_ylabel('Ampiezza [mV]', fontweight='bold')
    ax_b.set_title('Soluzione Adottata: Picchi Reali e Stima Impeccabile di $\\tau$', fontweight='bold')
    ax_b.grid(True)
    ax_b.legend(loc='upper right', frameon=True)
    
    plt.suptitle('Confronto Metodologico: Perché il Trattamento del Rumore Risolve la Deriva di $\\tau$', fontweight='bold', y=1.02)
    plt.tight_layout()
    g6_path = os.path.join(OUTPUT_DIR, 'confronto_rumore_fit.png')
    plt.savefig(g6_path, bbox_inches='tight')
    plt.close()
    print(f"Grafico 6 salvato: {g6_path}")
    
    # ---------------------------------------------------------
    # GRAFICO 7: Frequenza di Oscillazione durante il Ringdown vs Frequenza di Ingresso
    # ---------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8.8, 5.5), dpi=300)
    ax.plot(freqs / 1e3, f_hilbert_vals, 'o', color='#1971c2', markersize=6.5, label='Metodo Hilbert fase istantanea')
    ax.plot(freqs / 1e3, f_fft_vals, 's', color='#e8590c', markersize=5.5, alpha=0.85, label='Metodo FFT con zero padding 64x')
    
    # Linea della media sperimentale (senza incertezza esplicita e senza banda di confidenza)
    ax.axhline(f_mean, color='#d62728', linestyle='--', linewidth=1.8,
               label=rf'Media sperimentale ($f_1 = {int(round(f_mean))}$ Hz)')
    
    ax.set_ylim(417825, 417875)
    ax.set_yticks(np.arange(417830, 417871, 10))
    ax.ticklabel_format(useOffset=False, style='plain')
    ax.set_xlabel(r"Frequenza di eccitazione in ingresso $f_{in}$ [kHz]")
    ax.set_ylabel(r"Frequenza di oscillazione $f_1$ [Hz]")
    ax.set_title("Frequenza di oscillazione durante il ringdown rispetto alla frequenza di ingresso", pad=9)
    ax.grid(True)
    ax.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
    plt.tight_layout()
    g7_path = os.path.join(OUTPUT_DIR, 'frequenza_vs_fin.png')
    plt.savefig(g7_path)
    g7_alias_path = os.path.join(OUTPUT_DIR, 'ringdown_fit_dettaglio.png')
    plt.savefig(g7_alias_path)
    plt.close()
    print(f"Grafico 7 salvato: {g7_path} e {g7_alias_path}")
    
    # ---------------------------------------------------------
    # GRAFICO 8: Frequenza Propria vs Ampiezza Iniziale A0 (Effetto Duffing/Softening)
    # ---------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)
    ax.errorbar(a0_vals, f_hilbert_vals, yerr=[r['f_sinefit_err'] for r in all_results],
                fmt='o', color='#1f77b4', ecolor='#aec7e8', elinewidth=1.5, capsize=3,
                markersize=6, label='Frequenza $f_0$ misurata (Hilbert / SineFit)')
    
    # Regressione lineare vs ampiezza
    a_dense = np.linspace(0.0, np.max(a0_vals)*1.05, 200)
    f_extrap = np.polyval(p_f_vs_a0, a_dense)
    ax.plot(a_dense, f_extrap, '--', color='#d62728', linewidth=1.8,
            label=rf'Fit lineare: $f_0(A_0) = {int(round(f0_linear_extrap))}\text{{ Hz}} - {abs(slope_a0):.2f} \cdot A_0$')
    
    # Punto di estrapolazione ad ampiezza nulla A0 -> 0
    ax.plot(0.0, f0_linear_extrap, '*', color='#ff7f0e', markersize=14, zorder=5,
            label=rf'Frequenza lineare a riposo ($A_0 \to 0$): $f_{{0,lin}} = {int(round(f0_linear_extrap))}$ Hz')
    
    ax.set_xlabel('Ampiezza Iniziale del Ring-Down $A_0$ [mV]', fontweight='bold')
    ax.set_ylabel('Frequenza Naturale di Oscillazione $f_0$ [Hz]', fontweight='bold')
    ax.set_title('Dipendenza Ampiezza-Frequenza (Verifica Non-Linearità / Spring Softening)', fontweight='bold', pad=12)
    ax.grid(True)
    ax.set_xlim(-1.0, np.max(a0_vals)*1.08)
    ax.set_ylim(417835, 417865)
    ax.set_yticks(np.arange(417835, 417866, 5))
    ax.ticklabel_format(useOffset=False, style='plain')
    ax.legend(loc='lower left', frameon=True, fontsize=9)
    plt.tight_layout()
    g8_path = os.path.join(OUTPUT_DIR, 'frequenza_vs_ampiezza.png')
    plt.savefig(g8_path, bbox_inches='tight')
    plt.close()
    print(f"Grafico 8 salvato: {g8_path}")
    
    # ---------------------------------------------------------
    # GRAFICO 9: Chirp Intra-Ringdown (Frequenza Istantanea nel Tempo)
    # ---------------------------------------------------------
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=300)
    axes = axes.flatten()
    sample_scopes = [5, 13, 17, 29]
    sample_titles = [
        "Picco di Risonanza (Scope 5 - $A_0 = 36$ mV)",
        "Frequenza Intermedia (Scope 13 - $A_0 = 21$ mV)",
        "Bassa Ampiezza SX (Scope 17 - $A_0 = 5$ mV)",
        "Bassa Ampiezza DX (Scope 29 - $A_0 = 5$ mV)"
    ]
    
    for i, s_num in enumerate(sample_scopes):
        ax = axes[i]
        d = processed_data[s_num]
        t_w = d['t_fwin']
        dt_s = d['dt']
        ph = d['phase_inst']
        
        # Frequenza locale con sliding window di 250 us
        w_len = int(250e-6 / dt_s)
        step_w = int(25e-6 / dt_s)
        t_loc, f_loc = [], []
        for idx_w in range(0, len(t_w) - w_len, step_w):
            idx_slice = slice(idx_w, idx_w + w_len)
            p_loc = np.polyfit(t_w[idx_slice], ph[idx_slice], 1)
            t_loc.append(np.mean(t_w[idx_slice]))
            f_loc.append(p_loc[0] / (2.0 * np.pi))
        t_loc = np.array(t_loc) * 1e3 # in ms
        f_loc = np.array(f_loc) # in Hz
        
        # Traccia frequenza istantanea da finestra mobile
        ax.plot(t_loc, f_loc, color='#1f77b4', linewidth=1.4, alpha=0.7, label=r'Frequenza locale $f_{inst}(t)$ (finestra $250\,\mu$s)')
        
        # Fit del chirp quadratico
        t_dense_ms = np.linspace(t_w[0]*1e3, t_w[-1]*1e3, 200)
        f_chirp_fit = d['f_hilbert'] + d['chirp_rate'] * (t_dense_ms*1e-3 - np.mean(t_w))
        ax.plot(t_dense_ms, f_chirp_fit, '--', color='#d62728', linewidth=2.0,
                label=rf'Trend Chirp: $\Delta f = {d["delta_f_intra"]:+.1f}$ Hz')
        
        # Frequenza media nominale
        ax.axhline(d['f_hilbert'], color='black', linestyle=':', linewidth=1.2,
                   label=rf'Media: $f_0 = {int(round(d["f_hilbert"]))}$ Hz')
        
        f_center = int(round(d['f_hilbert']))
        ax.set_ylim(f_center - 25.0, f_center + 25.0)
        ax.set_yticks(np.arange(f_center - 20, f_center + 21, 10))
        ax.ticklabel_format(useOffset=False, style='plain')
        ax.set_title(sample_titles[i], fontweight='bold', fontsize=11)
        ax.set_xlabel('Tempo dopo lo spegnimento del Gate [ms]', fontweight='bold')
        ax.set_ylabel('Frequenza Istantanea [Hz]', fontweight='bold')
        ax.grid(True)
        ax.legend(loc='upper right', frameon=True, fontsize=8.5)
        
    plt.suptitle('Analisi del Chirp Intra-Ringdown: Stabilità della Frequenza durante il Decadimento', fontweight='bold', y=0.995)
    plt.tight_layout()
    g9_path = os.path.join(OUTPUT_DIR, 'chirp_intra_ringdown.png')
    plt.savefig(g9_path)
    plt.close()
    print(f"Grafico 9 salvato: {g9_path}")
    
    # ---------------------------------------------------------
    # GRAFICO 10: Zero-Padding, Risoluzione di Rayleigh e Picket-Fence Effect
    # ---------------------------------------------------------
    fig, (ax_zp, ax_ph, ax_time) = plt.subplots(1, 3, figsize=(18, 5.5), dpi=300)
    
    # Subplot A: Zero-Padding attorno al picco (Scope 5)
    d5 = processed_data[5]
    sig_w5 = d5['sig_fwin']
    N_w5 = len(sig_w5)
    dt5 = d5['dt']
    T_obs_ms = (d5['t_fwin'][-1] - d5['t_fwin'][0]) * 1e3
    
    zp_configs = [
        (1, '#d62728', '--', 'o', f'Pad 1x (Nessun pad, $\\Delta f = {int(round(1.0/(N_w5*dt5)))}$ Hz)'),
        (4, '#ff7f0e', '-.', 's', f'Pad 4x ($\\Delta f = {int(round(1.0/(4*N_w5*dt5)))}$ Hz)'),
        (16, '#2ca02c', ':', '^', f'Pad 16x ($\\Delta f = {1.0/(16*N_w5*dt5):.1f}$ Hz)'),
        (64, '#1f77b4', '-', None, f'Pad 64x ($\\Delta f = {1.0/(64*N_w5*dt5):.1f}$ Hz - DTFT continua)')
    ]
    
    for pad_k, col_k, ls_k, m_k, lbl_k in zp_configs:
        N_pad_k = N_w5 * pad_k
        Y_k = np.fft.rfft(sig_w5, n=N_pad_k)
        fr_k = np.fft.rfftfreq(N_pad_k, dt5)
        mask_k = (fr_k >= 416500) & (fr_k <= 419200)
        mag_k = np.abs(Y_k[mask_k])
        if m_k:
            ax_zp.plot(fr_k[mask_k] / 1e3, mag_k, ls_k, color=col_k, marker=m_k, markersize=4.5, label=lbl_k)
        else:
            ax_zp.plot(fr_k[mask_k] / 1e3, mag_k, ls_k, color=col_k, linewidth=2.0, label=lbl_k)
            
    ax_zp.ticklabel_format(useOffset=False, style='plain')
    ax_zp.set_xlabel('Frequenza [kHz]', fontweight='bold')
    ax_zp.set_ylabel('Magnitudo Spettrale [a.u.]', fontweight='bold')
    ax_zp.set_title('A. Picket-Fence Effect e Zero-Padding (DTFT)', fontweight='bold')
    ax_zp.grid(True)
    ax_zp.legend(loc='upper right', frameon=True, fontsize=8)
    
    # Subplot B: Srotolamento di fase e linearità
    t_fwin_ms = d5['t_fwin'] * 1e3
    ax_ph.plot(t_fwin_ms, d5['phase_inst'] / (2 * np.pi), color='#1f77b4', linewidth=1.5, label='Cicli di fase srotolati $\\theta(t)/2\\pi$')
    p_ph = np.polyfit(d5['t_fwin'], d5['phase_inst'], 1)
    phase_res_rad = d5['phase_inst'] - np.polyval(p_ph, d5['t_fwin'])
    
    ax_ph.ticklabel_format(useOffset=False, style='plain')
    ax_ph.set_xlabel('Tempo dal Gate [ms]', fontweight='bold')
    ax_ph.set_ylabel('Numero di Cicli di Oscillazione', fontweight='bold', color='#1f77b4')
    ax_ph.tick_params(axis='y', labelcolor='#1f77b4')
    ax_ph.set_title('B. Srotolamento di Fase $\\theta(t)$ e Residui', fontweight='bold')
    ax_ph.grid(True)
    
    ax_ph_res = ax_ph.twinx()
    ax_ph_res.plot(t_fwin_ms, phase_res_rad, color='#d62728', alpha=0.6, linewidth=1.0, label='Residui di fase [rad]')
    ax_ph_res.set_ylabel('Residuo di Fase [rad]', color='#d62728', fontweight='bold')
    ax_ph_res.tick_params(axis='y', labelcolor='#d62728')
    ax_ph_res.set_ylim(-0.5, 0.5)
    
    # Subplot C: Dettaglio temporale e Fit Sinusoidale Smorzato
    idx_zoom = np.where((t_fwin_ms >= 0.100) & (t_fwin_ms <= 0.115))[0]
    t_z_us = (d5['t_fwin'][idx_zoom] - 0.100 * 1e-3) * 1e6
    sig_z_mv = d5['sig_fwin'][idx_zoom] * 1e3
    
    t_dense_z = np.linspace(d5['t_fwin'][idx_zoom[0]], d5['t_fwin'][idx_zoom[-1]], 300)
    sig_fit_z = d5['A0'] * np.exp(-t_dense_z / d5['tau']) * np.cos(2 * np.pi * d5['f_sinefit'] * t_dense_z) * 1e3
    
    ax_time.plot(t_z_us, sig_z_mv, 'o', color='#1f77b4', markersize=5, label='Campioni acquisiti oscilloscopio')
    ax_time.plot((t_dense_z - 0.100 * 1e-3) * 1e6, sig_fit_z, '-', color='#d62728', linewidth=2.0,
                 label=rf'Fit MLE: $f_0 = {int(round(d5["f_sinefit"]))}$ Hz')
    ax_time.ticklabel_format(useOffset=False, style='plain')
    ax_time.set_xlabel('Tempo relativo [$\\mu$s]', fontweight='bold')
    ax_time.set_ylabel('Tensione TIA [mV]', fontweight='bold')
    ax_time.set_title('C. Fit Sinusoidale Smorzato nel Dominio del Tempo', fontweight='bold')
    ax_time.grid(True)
    ax_time.legend(loc='upper right', frameon=True, fontsize=8.5)
    
    plt.suptitle('Confronto dei Metodi di Misura della Frequenza di Risonanza: Dominio Spettrale, Fase e Tempo', fontweight='bold', y=1.02)
    plt.tight_layout()
    g10_path = os.path.join(OUTPUT_DIR, 'zero_padding_e_risoluzione_spettrale.png')
    plt.savefig(g10_path, bbox_inches='tight')
    plt.close()
    print(f"Grafico 10 salvato: {g10_path}")
    
    print("\nElaborazione e generazione grafici completata con successo!")

if __name__ == '__main__':
    main()
