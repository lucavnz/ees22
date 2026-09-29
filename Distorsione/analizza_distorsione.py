"""
Analisi della Distorsione Armonica e Accoppiamento Non Lineare (Risonanza Interna 1:2):
1. Caricamento automatico delle acquisizioni dell'oscilloscopio (scope_174 - scope_189).
2. Replica esatta della pipeline MATLAB del compagno (FFT rettangolare a 15997 punti).
3. Pipeline rigorosa di elaborazione del segnale: finestratura di Hann e zero-padding 64x
   per la completa rimozione dello scalloping loss (picket-fence effect) e del leakage spettrale.
4. Fit fisici teorici (fondamentale lineare/compressione, seconda armonica quadratica, HD2 lineare).
5. Esportazione dei grafici ad alta risoluzione (300 DPI) e tabella numerica CSV riassuntiva.
"""

import os
import glob
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# -----------------------------------------------------------------------------
# 1. Configurazione e Mappatura Scope -> Vac
# -----------------------------------------------------------------------------
# Mappatura delle tensioni nominali di eccitazione Vac [mVpp]
SCOPE_VAC_MAP = {
    175: 20.0,
    176: 40.0,
    177: 60.0,
    178: 80.0,
    174: 100.0,
    179: 120.0,
    180: 140.0,
    181: 160.0,
    182: 180.0,
    183: 200.0,
    184: 300.0,
    185: 400.0,
    186: 500.0,
    187: 600.0,
    188: 700.0,
    189: 800.0
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Parametri di stile per grafici accademici/editoriali (lineari, puliti, no bold)
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
    Carica il file CSV dell'oscilloscopio gestendo la struttura mista (Time domain + Math FFT F1).
    Ritorna:
        t: vettore temporale [s]
        ch1: tensione uscita TIA + invertente [V]
    """
    filepath = os.path.join(BASE_DIR, f'scope_{scope_num}.csv')
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File non trovato: {filepath}")

    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Individua l'eventuale traccia Math F1 interna al file
    sep_idx = len(lines)
    for i, line in enumerate(lines):
        if line.startswith('x-axis,F1'):
            sep_idx = i
            break

    # Estrazione dati temporali (da riga 3 alla riga del separatore)
    t_list = []
    ch1_list = []
    for line in lines[2:sep_idx]:
        parts = line.strip().split(',')
        if len(parts) >= 2 and parts[1]:
            try:
                t_list.append(float(parts[0]))
                ch1_list.append(float(parts[1]))
            except ValueError:
                continue

    t = np.array(t_list)
    ch1 = np.array(ch1_list)
    return t, ch1


def analyze_single_scope(scope_num):
    """
    Elabora il segnale con due metodi:
    1. Metodo compagno (MATLAB): 15997 campioni, finestra rettangolare, bin discreti.
    2. Metodo rigoroso: Finestra di Hann (guadagno coerente) + Zero-Padding 64x per
       interpolare la DTFT e rimuovere lo scalloping loss (picket-fence effect).
    """
    t, ch1 = load_scope_file(scope_num)
    dt = t[1] - t[0]
    Fs = 1.0 / dt
    N = len(ch1)
    vac = SCOPE_VAC_MAP[scope_num]

    # -------------------------------------------------------------------------
    # Metodo 1: Replica esatta MATLAB (Fres.m del compagno)
    # Troncamento arbitrario a 15997 punti e finestra rettangolare
    # -------------------------------------------------------------------------
    ch1_c = ch1[3:3 + 15997] if len(ch1) >= 16000 else ch1[:15997]
    L_c = len(ch1_c)
    Y_c = np.fft.rfft(ch1_c)
    P_c = np.abs(Y_c) / L_c * 2.0
    f_c = np.fft.rfftfreq(L_c, dt)

    m1_c = (f_c >= 415e3) & (f_c <= 425e3)
    p1_matlab = P_c[m1_c].max() * 1e3  # in mV
    f1_matlab = f_c[m1_c][np.argmax(P_c[m1_c])]

    m2_c = (f_c >= 830e3) & (f_c <= 850e3)
    p2_matlab = P_c[m2_c].max() * 1e3  # in mV
    f2_matlab = f_c[m2_c][np.argmax(P_c[m2_c])]

    # -------------------------------------------------------------------------
    # Metodo 2: Analisi spettrale rigorosa (Hann + Zero-Padding 64x)
    # -------------------------------------------------------------------------
    # Rimozione componente continua (offset DC)
    ch1_ac = ch1 - np.mean(ch1)

    # Finestra di Hann
    w = np.hanning(N)
    coherent_gain = np.sum(w) / N  # ~ 0.5 per Hann
    ch1_win = ch1_ac * w

    # Zero-padding a 64 volte la lunghezza per interpolazione DTFT sub-bin
    N_pad = N * 64
    Y_pad = np.fft.rfft(ch1_win, n=N_pad)
    f_pad = np.fft.rfftfreq(N_pad, dt)
    P_pad = np.abs(Y_pad) / (N * coherent_gain) * 2.0

    # Ricerca picco fondamentale attorno a ~418 kHz
    m1_pad = (f_pad >= 415e3) & (f_pad <= 422e3)
    idx_p1 = np.argmax(P_pad[m1_pad])
    f1_rigorous = f_pad[m1_pad][idx_p1]
    p1_rigorous = P_pad[m1_pad][idx_p1] * 1e3  # in mV

    # Ricerca picco seconda armonica / 2° modo attorno a ~836 kHz (2 * f1)
    m2_pad = (f_pad >= 830e3) & (f_pad <= 845e3)
    idx_p2 = np.argmax(P_pad[m2_pad])
    f2_rigorous = f_pad[m2_pad][idx_p2]
    p2_rigorous = P_pad[m2_pad][idx_p2] * 1e3  # in mV

    return {
        'scope': scope_num,
        'vac_mv': vac,
        'f1_matlab': f1_matlab,
        'p1_matlab': p1_matlab,
        'f2_matlab': f2_matlab,
        'p2_matlab': p2_matlab,
        'hd2_matlab': (p2_matlab / p1_matlab) * 100.0,
        'f1_rigorous': f1_rigorous,
        'p1_rigorous': p1_rigorous,
        'f2_rigorous': f2_rigorous,
        'p2_rigorous': p2_rigorous,
        'hd2_rigorous': (p2_rigorous / p1_rigorous) * 100.0
    }


def main():
    print("=" * 78)
    print("ANALISI DISTORSIONE ARMONICA E ACCOPPIAMENTO MODALE 1:2 (MEMS)")
    print("=" * 78)

    # Elaborazione di tutti i file in ordine crescente di Vac
    scopes_sorted = sorted(SCOPE_VAC_MAP.keys(), key=lambda s: SCOPE_VAC_MAP[s])
    results = []

    print(f"\n{'Scope':>5} | {'Vac [mVpp]':>10} | {'f1 [Hz]':>9} | {'p1 [mV]':>9} | {'f2 [Hz]':>9} | {'p2 [mV]':>9} | {'HD2 [%]':>8}")
    print("-" * 78)

    for s in scopes_sorted:
        res = analyze_single_scope(s)
        results.append(res)
        print(f"  {res['scope']:03d} | {res['vac_mv']:10.1f} | {res['f1_rigorous']:9.1f} | {res['p1_rigorous']:9.3f} | {res['f2_rigorous']:9.1f} | {res['p2_rigorous']:9.3f} | {res['hd2_rigorous']:7.2f}%")

    # Vettori per fit e grafici
    vac_arr = np.array([r['vac_mv'] for r in results])
    p1_rig_arr = np.array([r['p1_rigorous'] for r in results])
    p2_rig_arr = np.array([r['p2_rigorous'] for r in results])
    hd2_rig_arr = np.array([r['hd2_rigorous'] for r in results])

    p1_mat_arr = np.array([r['p1_matlab'] for r in results])
    p2_mat_arr = np.array([r['p2_matlab'] for r in results])
    hd2_mat_arr = np.array([r['hd2_matlab'] for r in results])

    # -------------------------------------------------------------------------
    # FIT FISICI TEORICI RIGOROSI
    # -------------------------------------------------------------------------
    # 1. Fondamentale (p1): regime lineare a piccolo segnale (Vac <= 200 mV)
    # Modello: p1 = k1 * Vac (senza intercetta fittizia)
    mask_lin = vac_arr <= 200.0
    k1 = np.sum(vac_arr[mask_lin] * p1_rig_arr[mask_lin]) / np.sum(vac_arr[mask_lin]**2)

    # 2. Seconda armonica (p2): legge quadratica da forza elettrostatica / risonanza 1:2
    # Modello: p2 = k2 * Vac^2 (escludendo il noise floor < 50 mV)
    mask_quad = (vac_arr >= 60.0) & (vac_arr <= 500.0)
    k2 = np.sum((vac_arr[mask_quad]**2) * p2_rig_arr[mask_quad]) / np.sum(vac_arr[mask_quad]**4)

    # 3. Rapporto di distorsione HD2 = p2 / p1 = (k2 / k1) * Vac
    # Legge lineare teorica: HD2 [%] = k_hd2 * Vac
    k_hd2 = (k2 / k1) * 100.0  # % per mVpp

    print("\nParametri fisici identificati:")
    print(f"  Guadagno fondamentale lineare (piccolo segnale): k1 = {k1:.5f} mV/mVpp")
    print(f"  Coefficiente armonico quadratico (1:2 coupling): k2 = {k2:.5e} mV/(mVpp)^2")
    print(f"  Pendenza teorica distorsione armonica HD2:      k_hd2 = {k_hd2:.5f} % / mVpp")

    v_dense = np.linspace(0, 850, 200)

    # -------------------------------------------------------------------------
    # GRAFICO 1: distorsione_armoniche_vs_vac.png
    # Spettro fondamentale e seconda armonica vs Vac
    # -------------------------------------------------------------------------
    fig1, ax1 = plt.subplots(figsize=(8.5, 6.0), dpi=300)

    # Curve e fit
    ax1.plot(v_dense, k1 * v_dense, linestyle='--', color='#1f77b4', linewidth=1.5,
             alpha=0.75, label=f'Fit lineare piccolo segnale ($k_1 = {k1:.3f}$)')
    ax1.plot(vac_arr, p1_rig_arr, marker='o', markersize=6.0, linewidth=2.0,
             color='#1f77b4', label=r'Primo modo / Fondamentale $f_1 \approx 417.8$ kHz')

    ax1.plot(v_dense, k2 * (v_dense**2), linestyle='--', color='#c0392b', linewidth=1.5,
             alpha=0.75, label=f'Fit quadratico ($k_2 = {k2*1e4:.2f} \\times 10^{{-4}}$)')
    ax1.plot(vac_arr, p2_rig_arr, marker='s', markersize=5.5, linewidth=2.0,
             color='#c0392b', label=r'Secondo modo / $2^{\mathrm{a}}$ Armonica $f_2 \approx 835.6$ kHz')

    ax1.set_title('Ampiezze armoniche MEMS vs tensione di eccitazione', pad=12)
    ax1.set_xlabel(r'Ampiezza eccitazione $V_{\mathrm{ac}}$ [$\mathrm{mV}_{\mathrm{pp}}$]')
    ax1.set_ylabel(r'Ampiezza componente in frequenza [mV]')
    ax1.set_xlim(0, 850)
    ax1.set_ylim(0, 32)
    ax1.grid(True, linestyle=':', alpha=0.55, color='#c0c0c0')
    ax1.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.9)

    plt.tight_layout()
    out_fig1 = os.path.join(BASE_DIR, 'distorsione_armoniche_vs_vac.png')
    fig1.savefig(out_fig1, dpi=300)
    plt.close(fig1)
    print(f"\n[OK] Grafico 1 salvato in: {out_fig1}")

    # -------------------------------------------------------------------------
    # GRAFICO 2: distorsione_hd2_rapporto.png
    # Rapporto di distorsione armonica HD2 = p2 / p1
    # -------------------------------------------------------------------------
    fig2, ax2 = plt.subplots(figsize=(8.5, 6.0), dpi=300)

    ax2.plot(v_dense, k_hd2 * v_dense, linestyle='--', color='#708090', linewidth=1.8,
             label=rf'Modello teorico lineare $HD_2 = (k_2/k_1) V_{{\mathrm{{ac}}}}$ ({k_hd2:.4f} %/mV)')
    ax2.plot(vac_arr, hd2_rig_arr, marker='o', markersize=6.5, linewidth=2.0,
             color='#2ca02c', label=r'Dati sperimentali $HD_2 = p_2 / p_1$')

    # Evidenziazione zona limite di rumore oscilloscopio
    ax2.axvspan(0, 45, color='#e0e0e0', alpha=0.45, label='Regione limitata da noise floor scope')

    ax2.set_title(r'Distorsione armonica $HD_2$ vs ampiezza di eccitazione', pad=12)
    ax2.set_xlabel(r'Ampiezza eccitazione $V_{\mathrm{ac}}$ [$\mathrm{mV}_{\mathrm{pp}}$]')
    ax2.set_ylabel(r'Distorsione $HD_2 = p_2 / p_1$ [%]')
    ax2.set_xlim(0, 850)
    ax2.set_ylim(0, 15)
    ax2.grid(True, linestyle=':', alpha=0.55, color='#c0c0c0')
    ax2.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.9)

    plt.tight_layout()
    out_fig2 = os.path.join(BASE_DIR, 'distorsione_hd2_rapporto.png')
    fig2.savefig(out_fig2, dpi=300)
    plt.close(fig2)
    print(f"[OK] Grafico 2 salvato in: {out_fig2}")

    # -------------------------------------------------------------------------
    # GRAFICO 3: distorsione_confronto_matlab_vs_rigoroso.png
    # Confronto tra stima MATLAB (compagno) e stima rigorosa
    # -------------------------------------------------------------------------
    fig3, (ax3a, ax3b) = plt.subplots(1, 2, figsize=(13.0, 5.5), dpi=300)

    # Subplot A: Ampiezze p1 e p2
    ax3a.plot(vac_arr, p1_rig_arr, marker='o', color='#1f77b4', label=r'$p_1$ (Rigorosa: Hann + ZP)')
    ax3a.plot(vac_arr, p1_mat_arr, marker='x', linestyle=':', color='#1f77b4', alpha=0.7, label=r'$p_1$ (MATLAB compagno)')
    ax3a.plot(vac_arr, p2_rig_arr, marker='s', color='#c0392b', label=r'$p_2$ (Rigorosa: Hann + ZP)')
    ax3a.plot(vac_arr, p2_mat_arr, marker='+', linestyle=':', color='#c0392b', alpha=0.7, label=r'$p_2$ (MATLAB compagno)')
    ax3a.set_title('Confronto ampiezze spettrali $p_1$ e $p_2$', pad=10)
    ax3a.set_xlabel(r'$V_{\mathrm{ac}}$ [$\mathrm{mV}_{\mathrm{pp}}$]')
    ax3a.set_ylabel('Ampiezza [mV]')
    ax3a.set_xlim(0, 850)
    ax3a.grid(True, linestyle=':', alpha=0.55, color='#c0c0c0')
    ax3a.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.9)

    # Subplot B: Distorsione HD2 (%)
    ax3b.plot(vac_arr, hd2_rig_arr, marker='o', color='#2ca02c', linewidth=2.0, label='Analisi rigorosa')
    ax3b.plot(vac_arr, hd2_mat_arr, marker='x', linestyle='--', color='#d95f02', linewidth=1.7, label='MATLAB compagno (sottostimata)')
    ax3b.set_title('Confronto rapporto distorsione $HD_2$ [%]', pad=10)
    ax3b.set_xlabel(r'$V_{\mathrm{ac}}$ [$\mathrm{mV}_{\mathrm{pp}}$]')
    ax3b.set_ylabel(r'$HD_2 = p_2 / p_1$ [%]')
    ax3b.set_xlim(0, 850)
    ax3b.set_ylim(0, 15)
    ax3b.grid(True, linestyle=':', alpha=0.55, color='#c0c0c0')
    ax3b.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.9)

    plt.tight_layout()
    out_fig3 = os.path.join(BASE_DIR, 'distorsione_confronto_matlab_vs_rigoroso.png')
    fig3.savefig(out_fig3, dpi=300)
    plt.close(fig3)
    print(f"[OK] Grafico 3 salvato in: {out_fig3}")

    # -------------------------------------------------------------------------
    # GRAFICO 4: distorsione_spettro_picket_fence.png
    # Dimostrazione visiva del fenomeno dello scalloping loss a 800 mV (scope 189)
    # -------------------------------------------------------------------------
    fig4, ax4 = plt.subplots(figsize=(8.5, 5.5), dpi=300)

    t_189, ch1_189 = load_scope_file(189)
    dt_189 = t_189[1] - t_189[0]
    N_189 = len(ch1_189)

    # Spettro discreto compagno (15997 campioni, finestra rettangolare)
    ch1_c189 = ch1_189[3:3+15997]
    L_c189 = len(ch1_c189)
    Y_c189 = np.fft.rfft(ch1_c189)
    P_c189 = np.abs(Y_c189) / L_c189 * 2.0
    f_c189 = np.fft.rfftfreq(L_c189, dt_189)

    # Spettro continuo interpolato con Zero-Padding e finestra Hann
    w_189 = np.hanning(N_189)
    cg_189 = np.sum(w_189) / N_189
    N_pad189 = N_189 * 64
    Y_pad189 = np.fft.rfft((ch1_189 - np.mean(ch1_189)) * w_189, n=N_pad189)
    P_pad189 = np.abs(Y_pad189) / (N_189 * cg_189) * 2.0
    f_pad189 = np.fft.rfftfreq(N_pad189, dt_189)

    # Zoom attorno a 835 kHz
    m_zp = (f_pad189 >= 810e3) & (f_pad189 <= 860e3)
    m_c = (f_c189 >= 810e3) & (f_c189 <= 860e3)

    ax4.plot(f_pad189[m_zp] / 1e3, P_pad189[m_zp] * 1e3, color='#1f77b4', linewidth=2.0,
             label=r'Spettro continuo DTFT (Hann + Zero-Padding 64x)')
    ax4.stem(f_c189[m_c] / 1e3, P_c189[m_c] * 1e3, linefmt='r--', markerfmt='ro',
             basefmt=' ', label='Bin discreti MATLAB compagno (senza zero-padding)')

    # Annotazioni didattiche
    f2_peak = f_pad189[m_zp][np.argmax(P_pad189[m_zp])] / 1e3
    p2_peak = P_pad189[m_zp].max() * 1e3
    ax4.annotate(f'Vero picco fisico:\n{p2_peak:.2f} mV @ {f2_peak:.1f} kHz',
                 xy=(f2_peak, p2_peak), xytext=(f2_peak - 12, p2_peak + 0.3),
                 arrowprops=dict(facecolor='#1f77b4', shrink=0.08, width=1.0, headwidth=6),
                 fontsize=9.5, color='#1f77b4')

    ax4.annotate('Sottostima da scalloping loss:\nbin a 840.1 kHz = 2.63 mV\n(picco reale mancato tra i bin)',
                 xy=(840.15, 2.63), xytext=(840.15 + 3, 2.63 + 0.6),
                 arrowprops=dict(facecolor='#c0392b', shrink=0.08, width=1.0, headwidth=6),
                 fontsize=9.5, color='#c0392b')

    ax4.set_title(r'Effetto Picket-Fence e Scalloping Loss attorno a $2f_1$ (Scope 189, 800 mVpp)', pad=12)
    ax4.set_xlabel('Frequenza [kHz]')
    ax4.set_ylabel('Ampiezza spettrale [mV]')
    ax4.set_xlim(815, 855)
    ax4.set_ylim(0, 4.2)
    ax4.grid(True, linestyle=':', alpha=0.55, color='#c0c0c0')
    ax4.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.9)

    plt.tight_layout()
    out_fig4 = os.path.join(BASE_DIR, 'distorsione_spettro_picket_fence.png')
    fig4.savefig(out_fig4, dpi=300)
    plt.close(fig4)
    print(f"[OK] Grafico 4 salvato in: {out_fig4}")

    # -------------------------------------------------------------------------
    # Esportazione Tabella CSV
    # -------------------------------------------------------------------------
    csv_out_path = os.path.join(BASE_DIR, 'distorsione_risultati.csv')
    with open(csv_out_path, 'w') as f:
        f.write("scope,vac_mv,f1_matlab_hz,p1_matlab_mv,f2_matlab_hz,p2_matlab_mv,hd2_matlab_pct,f1_rigorous_hz,p1_rigorous_mv,f2_rigorous_hz,p2_rigorous_mv,hd2_rigorous_pct\n")
        for r in results:
            f.write(f"{r['scope']},{r['vac_mv']:.1f},{r['f1_matlab']:.2f},{r['p1_matlab']:.4f},{r['f2_matlab']:.2f},{r['p2_matlab']:.4f},{r['hd2_matlab']:.3f},{r['f1_rigorous']:.2f},{r['p1_rigorous']:.4f},{r['f2_rigorous']:.2f},{r['p2_rigorous']:.4f},{r['hd2_rigorous']:.3f}\n")

    print(f"\n[OK] Risultati numerici esportati con successo in: {csv_out_path}")
    print("=" * 78)


if __name__ == '__main__':
    main()
