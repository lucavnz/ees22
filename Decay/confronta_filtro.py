"""
Confronto tra segnale reale dell'oscilloscopio e segnale filtrato:
1. Panoramica temporale completa: evidenza che il profilo a 'cono' e presente gia nel segnale grezzo.
2. Zoom temporale a livello dei microsecondi: visualizzazione dei singoli cicli sinusoidali a 417.8 kHz.
3. Zoom sul punto di minimo: visualizzazione dell'annullamento dell'oscillazione meccanica e inversione di fase.
4. Spettro in frequenza (FFT): preservazione totale del picco di risonanza ed eliminazione del rumore fuori banda.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'grafici')
os.makedirs(OUTPUT_DIR, exist_ok=True)

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 10,
    'axes.labelsize': 10.5,
    'axes.titlesize': 11,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'lines.linewidth': 1.4,
    'grid.alpha': 0.35,
    'grid.linestyle': '--',
    'figure.titlesize': 11.5
})


def load_scope_file(filepath):
    """Carica il file CSV dell'oscilloscopio ignorando righe vuote e header."""
    rows = []
    with open(filepath, 'r') as f:
        f.readline()
        f.readline()
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 2 and parts[0] != '' and parts[1] != '':
                try:
                    rows.append([float(parts[0]), float(parts[1])])
                except ValueError:
                    continue
    return np.array(rows)


def main():
    filepath = os.path.join(BASE_DIR, 'Decay_controfase.csv')
    data = load_scope_file(filepath)
    t = data[:, 0]
    raw = data[:, 1]
    dt = t[1] - t[0]
    fs = 1.0 / dt

    # 1. Segnale grezzo con rimozione offset DC medio
    v_dc = np.mean(raw)
    raw_no_dc = raw - v_dc

    # 2. Filtro passa-banda Butterworth del 2 ordine (390 - 445 kHz)
    # filtfilt applica il filtro in avanti e indietro: fase rigorosamente zero (nessun ritardo)
    f_low = 390000.0
    f_high = 445000.0
    b, a = butter(2, [f_low / (fs / 2.0), f_high / (fs / 2.0)], btype='bandpass')
    filt = filtfilt(b, a, raw_no_dc)

    # 3. FFT del segnale grezzo e filtrato per confronto spettrale
    n_pts = len(raw_no_dc)
    fft_raw = np.abs(np.fft.rfft(raw_no_dc)) * (2.0 / n_pts) * 1e3
    fft_filt = np.abs(np.fft.rfft(filt)) * (2.0 / n_pts) * 1e3
    freqs_khz = np.fft.rfftfreq(n_pts, dt) / 1e3

    fig, axes = plt.subplots(2, 2, figsize=(13, 8.2), dpi=300)

    # -------------------------------------------------------------------------
    # Subplot 1: Panoramica completa (dimostra che il 'cono' c'e gia nel grezzo)
    # -------------------------------------------------------------------------
    ax1 = axes[0, 0]
    t_ms = t * 1e3
    ax1.plot(t_ms, raw_no_dc * 1e3, color='#ced4da', alpha=0.9, linewidth=0.8,
             label='Segnale grezzo oscilloscopio (senza filtri)')
    ax1.plot(t_ms, filt * 1e3, color='#1971c2', alpha=0.85, linewidth=0.9,
             label='Segnale filtrato passa-banda (390-445 kHz)')
    ax1.axvline(0.6898, color='#d62728', linestyle='--', linewidth=1.4,
                label='Punto di azzeramento ($t^* = 0.69$ ms)')
    ax1.set_xlabel('Tempo dal trigger [ms]')
    ax1.set_ylabel('Tensione [mV]')
    ax1.set_title('Panoramica completa: il profilo a cono e reale e visibile nel grezzo')
    ax1.grid(True)
    ax1.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')

    # -------------------------------------------------------------------------
    # Subplot 2: Zoom microscopico su 10 cicli di oscillazione (da 0.200 a 0.225 ms)
    # -------------------------------------------------------------------------
    ax2 = axes[0, 1]
    mask_zoom = (t >= 0.200e-3) & (t <= 0.225e-3)
    t_zoom_us = (t[mask_zoom] - 0.200e-3) * 1e6
    raw_zoom = raw_no_dc[mask_zoom] * 1e3
    filt_zoom = filt[mask_zoom] * 1e3

    ax2.plot(t_zoom_us, raw_zoom, 'o-', color='#868e96', markersize=3.2, linewidth=1.0, alpha=0.75,
             label='Campioni grezzi oscilloscopio (con rumore analogico)')
    ax2.plot(t_zoom_us, filt_zoom, '-', color='#1971c2', linewidth=1.8,
             label='Sinusoide filtrata a fase zero (passa al centro dei punti)')
    ax2.set_xlabel('Tempo relativo nella finestra di zoom [$\\mu$s]')
    ax2.set_ylabel('Tensione [mV]')
    ax2.set_title('Zoom sui singoli cicli a 417.8 kHz (frequenza reale, non fittizia)')
    ax2.grid(True)
    ax2.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')

    # -------------------------------------------------------------------------
    # Subplot 3: Zoom sul punto di minimo di annullamento (da 0.675 a 0.705 ms)
    # -------------------------------------------------------------------------
    ax3 = axes[1, 0]
    mask_min = (t >= 0.675e-3) & (t <= 0.705e-3)
    t_min_us = (t[mask_min] - 0.675e-3) * 1e6
    raw_min = raw_no_dc[mask_min] * 1e3
    filt_min = filt[mask_min] * 1e3

    ax3.plot(t_min_us, raw_min, 'o-', color='#868e96', markersize=3.2, linewidth=1.0, alpha=0.75,
             label='Grezzo: collasso dell\'ampiezza nel noise floor')
    ax3.plot(t_min_us, filt_min, '-', color='#d62728', linewidth=1.8,
             label='Filtrato: annullamento a zero e ripartenza')
    ax3.axvline((0.6898e-3 - 0.675e-3) * 1e6, color='#495057', linestyle=':', linewidth=1.3,
                label='Istante esatto di estinzione')
    ax3.set_xlabel('Tempo relativo attorno al minimo [$\\mu$s]')
    ax3.set_ylabel('Tensione [mV]')
    ax3.set_title('Dettaglio dell\'annullamento: il moto scompare realmente a zero')
    ax3.grid(True)
    ax3.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')

    # -------------------------------------------------------------------------
    # Subplot 4: Spettro in frequenza FFT (segnale grezzo vs filtrato)
    # -------------------------------------------------------------------------
    ax4 = axes[1, 1]
    mask_f = (freqs_khz >= 300) & (freqs_khz <= 550)
    ax4.plot(freqs_khz[mask_f], fft_raw[mask_f], color='#adb5bd', linewidth=1.0, alpha=0.8,
             label='Spettro segnale grezzo (con rumore a larga banda)')
    ax4.plot(freqs_khz[mask_f], fft_filt[mask_f], color='#1971c2', linewidth=1.6,
             label='Spettro segnale filtrato (picco intatto, rumore rimosso)')
    ax4.axvspan(f_low / 1e3, f_high / 1e3, color='#e7f5ff', alpha=0.6, label='Banda passante filtro (390-445 kHz)')
    ax4.axvline(417.8, color='#d62728', linestyle=':', linewidth=1.3, label='Frequenza di risonanza MEMS (417.8 kHz)')
    ax4.set_xlabel('Frequenza [kHz]')
    ax4.set_ylabel('Ampiezza spettrale [mV]')
    ax4.set_title('Spettro FFT: la risonanza del MEMS non viene modificata dal filtro')
    ax4.grid(True)
    ax4.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, 'confronto_reale_vs_filtrato.png')
    plt.savefig(out_path)
    plt.close()
    print(f"Grafico salvato con successo in: {out_path}")


if __name__ == '__main__':
    main()
