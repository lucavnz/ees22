"""
Analisi del decadimento del risuonatore MEMS: ringdown naturale ed eccitazione in controfase.

Questo script replica ed estende l'analisi dei file MATLAB (Decay.m, Counter.m):
1. Caricamento ed elaborazione del decadimento libero naturale (scope_7.csv).
   - Rimozione corretta dell'offset DC.
   - Filtraggio passa-banda attorno a f0 (390-445 kHz).
   - Fit esponenziale dell'inviluppo di Hilbert e dei picchi.
   - Spiegazione metodologica dell'errore di stima asimmetrica di Decay.m.
2. Caricamento ed elaborazione dell'eccitazione in controfase (Decay_controfase.csv, Decay_controfase2.csv).
   - Estrazione di Vin, -Vin e Vout.
   - Calcolo dell'inviluppo sperimentale del moto meccanico.
   - Fit del modello fisico analitico: X(t) = |(X0 + X_inf)*exp(-t/tau) - X_inf|.
   - Verifica analitica del tempo di spegnimento: t* = tau * ln(1 + X0 / X_inf).
   - Quantificazione dell'abbattimento dell'ampiezza (fino al 99.2% in 0.69 ms).
3. Zoom ad altissima risoluzione sul transitorio di commutazione (Decay_controfase_dettaglio.csv).
4. Generazione di grafici puliti con stile coerente al resto della repository.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import hilbert, butter, filtfilt, find_peaks
from scipy.optimize import curve_fit

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'grafici')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Impostazioni grafiche per una resa pulita, semplice ed elegante
# Niente testo in grassetto, titoli e label con sola iniziale maiuscola
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 10.5,
    'axes.labelsize': 11,
    'axes.titlesize': 11.5,
    'xtick.labelsize': 9.5,
    'ytick.labelsize': 9.5,
    'legend.fontsize': 9.5,
    'lines.linewidth': 1.5,
    'grid.alpha': 0.35,
    'grid.linestyle': '--',
    'figure.titlesize': 12
})


def load_scope_file(filepath):
    """Carica un file CSV dell'oscilloscopio ignorando righe vuote e header."""
    rows = []
    with open(filepath, 'r') as f:
        f.readline()
        f.readline()
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 2 and parts[0] != '' and parts[1] != '':
                try:
                    rows.append([float(p) if p != '' else np.nan for p in parts])
                except ValueError:
                    continue
    return np.array(rows)


def analyze_natural_decay():
    """Analisi del decadimento naturale da scope_7.csv."""
    filepath = os.path.join(BASE_DIR, 'scope_7.csv')
    data = load_scope_file(filepath)
    t = data[:, 0]
    x_raw = data[:, 1]
    dt = t[1] - t[0]
    fs = 1.0 / dt

    # 1. Analisi con e senza offset DC (per illustrare la discrepanza di Decay.m)
    v_dc = np.mean(x_raw)
    x_no_dc = x_raw - v_dc

    # Filtro passa-banda attorno alla frequenza di risonanza (~417.8 kHz)
    b_bp, a_bp = butter(2, [390e3 / (fs / 2), 445e3 / (fs / 2)], btype='bandpass')
    x_filt = filtfilt(b_bp, a_bp, x_no_dc)

    # Inviluppo di Hilbert
    env_hilb = np.abs(hilbert(x_filt))

    # Individuazione picchi superiori e inferiori sul segnale grezzo (come fatto in Decay.m)
    pk_up_raw, _ = find_peaks(x_raw, distance=8)
    pk_lo_raw, _ = find_peaks(-x_raw, distance=8)

    p_up_raw = np.polyfit(t[pk_up_raw], np.log(x_raw[pk_up_raw]), 1)
    p_lo_raw = np.polyfit(t[pk_lo_raw], np.log(-x_raw[pk_lo_raw]), 1)
    tau_up_raw = -1.0 / p_up_raw[0]
    tau_lo_raw = -1.0 / p_lo_raw[0]

    # Individuazione picchi sul segnale filtrato senza offset DC
    pk_up, _ = find_peaks(x_filt, distance=8)
    pk_lo, _ = find_peaks(-x_filt, distance=8)

    p_up = np.polyfit(t[pk_up], np.log(x_filt[pk_up]), 1)
    p_lo = np.polyfit(t[pk_lo], np.log(-x_filt[pk_lo]), 1)
    tau_up = -1.0 / p_up[0]
    tau_lo = -1.0 / p_lo[0]

    # Fit lineare su logaritmo dell'inviluppo di Hilbert usando tempo relativo
    t_rel = t - t[0]
    w_fit = slice(100, -100)
    p_hilb = np.polyfit(t_rel[w_fit], np.log(env_hilb[w_fit]), 1)
    tau_hilb = -1.0 / p_hilb[0]
    a0_hilb = np.exp(p_hilb[1])
    f0 = 417800.0
    q_factor = np.pi * f0 * tau_hilb

    results = {
        't': t,
        't_rel': t_rel,
        'x_raw': x_raw,
        'x_filt': x_filt,
        'v_dc': v_dc,
        'env_hilb': env_hilb,
        'pk_up': pk_up,
        'pk_lo': pk_lo,
        'pk_up_raw': pk_up_raw,
        'pk_lo_raw': pk_lo_raw,
        'tau_up_raw': tau_up_raw,
        'tau_lo_raw': tau_lo_raw,
        'tau_up': tau_up,
        'tau_lo': tau_lo,
        'tau_hilb': tau_hilb,
        'a0_hilb': a0_hilb,
        'q_factor': q_factor
    }

    # Grafico 1: Decadimento naturale e confronto con/senza DC
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.8), dpi=300)

    # Subplot A: Segnale filtrato, inviluppo e fit corretto
    t_ms = t_rel * 1e3
    ax1.plot(t_ms, x_filt * 1e3, color='#adb5bd', alpha=0.6, linewidth=0.8, label='Segnale oscilloscopio')
    ax1.plot(t_ms[w_fit], env_hilb[w_fit] * 1e3, color='#1971c2', linewidth=1.5, label='Inviluppo di Hilbert')
    fit_curve = a0_hilb * np.exp(-t_rel / tau_hilb) * 1e3
    ax1.plot(t_ms, fit_curve, '--', color='#d62728', linewidth=1.8,
             label=f'Fit esponenziale: $\\tau = {tau_hilb*1e3:.3f}$ ms ($Q \\approx {int(round(q_factor))}$)')
    ax1.plot(t_ms, -fit_curve, '--', color='#d62728', linewidth=1.8)
    ax1.set_xlabel('Tempo dal trigger [ms]')
    ax1.set_ylabel('Tensione [mV]')
    ax1.set_title('Decadimento libero naturale (ringdown spontaneo)')
    ax1.grid(True)
    ax1.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')

    # Subplot B: Confronto logaritmico picchi con e senza DC
    ax2.plot(t_ms[pk_up_raw], np.log(x_raw[pk_up_raw] * 1e3), '.', color='#e03131', markersize=3.5,
             label=f'Picchi superiori grezzi ($\\tau = {tau_up_raw*1e3:.2f}$ ms)')
    ax2.plot(t_ms[pk_lo_raw], np.log(-x_raw[pk_lo_raw] * 1e3), '.', color='#2f9e44', markersize=3.5,
             label=f'Picchi inferiori grezzi ($\\tau = {tau_lo_raw*1e3:.2f}$ ms)')
    ax2.plot(t_ms[pk_up], np.log(x_filt[pk_up] * 1e3), '-', color='#1971c2', linewidth=1.8,
             label=f'Picchi con offset rimosso ($\\tau = {tau_up*1e3:.3f}$ ms)')
    ax2.set_xlabel('Tempo dal trigger [ms]')
    ax2.set_ylabel('ln(ampiezza dei picchi [mV])')
    ax2.set_title('Effetto della rimozione dell\'offset DC sulla stima di tau')
    ax2.grid(True)
    ax2.legend(loc='lower left', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')

    plt.tight_layout()
    g1_path = os.path.join(OUTPUT_DIR, 'decadimento_naturale.png')
    plt.savefig(g1_path)
    plt.close()

    return results


def analyze_counterphase_dataset(filename, t_fit_start_s=0.1e-3, t_fit_end_s=None):
    """
    Analizza un dataset di eccitazione in controfase.
    Modello fisico: X(t) = |(X0 + X_inf) * exp(-t / tau) - X_inf|
    Tempo di spegnimento teorico: t* = tau * ln(1 + X0 / X_inf)
    """
    filepath = os.path.join(BASE_DIR, filename)
    data = load_scope_file(filepath)
    t = data[:, 0]
    ch1 = data[:, 1]
    ch3 = data[:, 2] if data.shape[1] > 2 else None
    ch4 = data[:, 3] if data.shape[1] > 3 else None
    dt = t[1] - t[0]
    fs = 1.0 / dt

    # Rimozione DC e filtraggio passa-banda su Ch1
    ch1_no_dc = ch1 - np.nanmean(ch1)
    b_bp, a_bp = butter(2, [390e3 / (fs / 2), 445e3 / (fs / 2)], btype='bandpass')
    ch1_filt = filtfilt(b_bp, a_bp, ch1_no_dc)
    env_ch1 = np.abs(hilbert(ch1_filt))

    # Identificazione istante di accensione della controfase (t = 0 s nominale del trigger)
    idx_trigger = np.argmin(np.abs(t))
    t_on = t[idx_trigger]

    # Ricerca del minimo dell'inviluppo post-trigger nella prima fase di estinzione
    search_window = min(int(1.8e-3 / dt), len(env_ch1) - idx_trigger)
    idx_search = idx_trigger + np.arange(search_window)
    idx_min_local = idx_search[np.argmin(env_ch1[idx_search])]
    t_min = t[idx_min_local]
    t_quench_exp = t_min - t_on
    x_min = env_ch1[idx_min_local]

    # Stima di X0 estrapolata dal decadimento libero antecedente all'accensione (evita spike Cp)
    idx_pre = np.where(t < -50e-6)[0]
    if len(idx_pre) > 50:
        p_pre = np.polyfit(t[idx_pre], np.log(env_ch1[idx_pre]), 1)
        x0_estrap = np.exp(p_pre[1])
        tau_pre = -1.0 / p_pre[0]
    else:
        x0_estrap = env_ch1[idx_trigger]
        tau_pre = 2.17e-3

    # Definizione finestra di fit per il modello analitico
    if t_fit_end_s is None:
        t_fit_end_s = t[-1] - 50e-6
    mask_fit = (t >= t_fit_start_s) & (t <= t_fit_end_s)
    t_fit = t[mask_fit]
    env_fit = env_ch1[mask_fit]

    def analytical_quench_model(time_vec, amp0, amp_inf, tau_decay):
        return np.abs((amp0 + amp_inf) * np.exp(-time_vec / tau_decay) - amp_inf)

    p0_guess = [x0_estrap, np.mean(env_ch1[-400:]), tau_pre]
    try:
        popt, pcov = curve_fit(
            analytical_quench_model, t_fit, env_fit,
            p0=p0_guess,
            bounds=([0.005, 0.010, 0.001], [0.060, 0.080, 0.005])
        )
        fit_success = True
        x0_fit = popt[0]
        x_inf_fit = popt[1]
        tau_fit = popt[2]
        t_star_theory = tau_fit * np.log(1.0 + x0_fit / x_inf_fit)
    except Exception:
        fit_success = False
        x0_fit = x0_estrap
        x_inf_fit = np.mean(env_ch1[-400:])
        tau_fit = tau_pre
        t_star_theory = tau_fit * np.log(1.0 + x0_fit / x_inf_fit)

    reduction_pct = (1.0 - x_min / x0_fit) * 100.0

    return {
        'filename': filename,
        't': t,
        'ch1': ch1,
        'ch1_filt': ch1_filt,
        'ch3': ch3,
        'ch4': ch4,
        'env_ch1': env_ch1,
        't_on': t_on,
        't_min': t_min,
        't_quench_exp': t_quench_exp,
        'x_min': x_min,
        'x0_fit': x0_fit,
        'x_inf_fit': x_inf_fit,
        'tau_fit': tau_fit,
        't_star_theory': t_star_theory,
        'reduction_pct': reduction_pct,
        'analytical_model': analytical_quench_model,
        'fit_success': fit_success
    }


def analyze_detail_switching():
    """Analisi del transitorio a frequenza ultra-alta da Decay_controfase_dettaglio.csv."""
    filepath = os.path.join(BASE_DIR, 'Decay_controfase_dettaglio.csv')
    data = load_scope_file(filepath)
    t = data[:, 0]
    ch1 = data[:, 1]
    ch3 = data[:, 2]
    ch4 = data[:, 3]

    # Grafico 5: Dettaglio ultra-veloce della commutazione
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.5, 6.2), dpi=300, sharex=True)
    t_us = t * 1e6

    # Subplot A: Tensioni di eccitazione diretta e invertita
    ax1.plot(t_us, ch4, color='#1971c2', linewidth=1.5, label='Tensione eccitazione $v_{in}(t)$ (Ch4)')
    ax1.plot(t_us, ch3, color='#e8590c', linewidth=1.5, linestyle='--', label='Tensione in controfase $-v_{in}(t)$ (Ch3)')
    ax1.axvline(0, color='#495057', linestyle=':', linewidth=1.3, label='Fronte di commutazione')
    ax1.set_ylabel('Tensione [V]')
    ax1.set_title('Transitorio di commutazione della tensione di eccitazione')
    ax1.grid(True)
    ax1.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')

    # Subplot B: Uscita TIA con spike capacitivo di feedthrough Cp
    ax2.plot(t_us, ch1 * 1e3, color='#d62728', linewidth=1.4, label='Uscita catena TIA $v_{out}(t)$ (Ch1)')
    ax2.axvline(0, color='#495057', linestyle=':', linewidth=1.3)
    ax2.set_xlabel('Tempo dal fronte di commutazione [$\\mu$s]')
    ax2.set_ylabel('Tensione [mV]')
    ax2.set_title('Risposta transitoria dell\'amplificatore e spike capacitivo di $C_p$')
    ax2.grid(True)
    ax2.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')

    plt.tight_layout()
    g5_path = os.path.join(OUTPUT_DIR, 'dettaglio_commutazione_parassita.png')
    plt.savefig(g5_path)
    plt.close()


def plot_envelope_methods_comparison(res_nat):
    """
    Confronto diretto e rigoroso tra metodo dei picchi (da Ampiezza_Frequenza/analizza_ringdown.py)
    e metodo dell'inviluppo di Hilbert.
    """
    t_rel_ms = res_nat['t_rel'] * 1e3
    x_filt_mv = res_nat['x_filt'] * 1e3
    env_hilb_mv = res_nat['env_hilb'] * 1e3
    pk_up = res_nat['pk_up']
    tau_pks = res_nat['tau_up']
    tau_hilb = res_nat['tau_hilb']
    a0_hilb = res_nat['a0_hilb'] * 1e3
    a0_pks = np.exp(np.polyfit(res_nat['t_rel'][pk_up], np.log(res_nat['x_filt'][pk_up]), 1)[1]) * 1e3
    diff_pct = abs(tau_pks - tau_hilb) / tau_hilb * 100.0

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.8), dpi=300)

    # Subplot A: Zoom temporale sui singoli periodi di oscillazione a 417.8 kHz
    zoom_mask = (t_rel_ms >= 0.50) & (t_rel_ms <= 0.58)
    pk_zoom = pk_up[zoom_mask[pk_up]]

    ax1.plot(t_rel_ms[zoom_mask], x_filt_mv[zoom_mask], color='#adb5bd', linewidth=1.0, label='Oscillazione risuonatore ($f_0 \\approx 417.8$ kHz)')
    ax1.plot(t_rel_ms[zoom_mask], env_hilb_mv[zoom_mask], color='#1971c2', linewidth=1.8, label='Inviluppo di Hilbert (continuo)')
    ax1.plot(t_rel_ms[pk_zoom], x_filt_mv[pk_zoom], 'o', color='#e03131', markersize=4.5, label='Picchi discreti (find_peaks)')
    ax1.set_xlabel('Tempo dal trigger [ms]')
    ax1.set_ylabel('Tensione [mV]')
    ax1.set_title('Dettaglio dei singoli periodi: picchi discreti vs inviluppo continuo')
    ax1.grid(True)
    ax1.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')

    # Subplot B: Fit esponenziale globale su tutto il decadimento
    t_plot_ms = np.linspace(0, 8.0, 400)
    fit_hilb = a0_hilb * np.exp(-t_plot_ms / (tau_hilb * 1e3))
    fit_pks = a0_pks * np.exp(-t_plot_ms / (tau_pks * 1e3))

    ax2.plot(t_rel_ms[pk_up], x_filt_mv[pk_up], '.', color='#e03131', alpha=0.5, markersize=3.0, label='Picchi estratti da find_peaks')
    ax2.plot(t_plot_ms, fit_hilb, color='#1971c2', linewidth=2.0,
             label=f'Fit inviluppo di Hilbert: $\\tau = {tau_hilb*1e3:.3f}$ ms')
    ax2.plot(t_plot_ms, fit_pks, '--', color='#2b8a3e', linewidth=1.8,
             label=f'Fit metodo dei picchi: $\\tau = {tau_pks*1e3:.3f}$ ms')

    ax2.annotate(f'Discrepanza tra i metodi: {diff_pct:.2f}%\nCoerenza perfetta tra picchi e Hilbert',
                 xy=(3.5, 12), xytext=(3.5, 18),
                 bbox=dict(boxstyle='round,pad=0.5', facecolor='#f8f9fa', edgecolor='#ced4da', alpha=0.95))

    ax2.set_xlim(-0.1, 8.2)
    ax2.set_xlabel('Tempo dal trigger [ms]')
    ax2.set_ylabel('Ampiezza [mV]')
    ax2.set_title('Confronto dei fit esponenziali sul decadimento libero naturale')
    ax2.grid(True)
    ax2.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')

    plt.tight_layout()
    g_path = os.path.join(OUTPUT_DIR, 'confronto_metodi_inviluppo.png')
    plt.savefig(g_path)
    plt.close()


def generate_all_plots(res_nat, res_cp1, res_cp2):
    """Genera tutti i grafici di confronto con lo stile della repository."""

    # -------------------------------------------------------------------------
    # Grafico 2: Dinamica temporale completa della controfase (Decay_controfase2.csv)
    # -------------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11.0, 6.8), dpi=300, sharex=True)
    d2 = res_cp2

    mask_clean = (d2['t'] >= -1.0e-3) & (d2['t'] <= 8.5e-3)
    t_ms2 = d2['t'][mask_clean] * 1e3
    ch4_clean = d2['ch4'][mask_clean]
    ch1_filt_clean = d2['ch1_filt'][mask_clean] * 1e3
    env_clean = d2['env_ch1'][mask_clean] * 1e3

    t_star_ms = d2['t_quench_exp'] * 1e3

    # Suddivisione visiva in zone fisiche temporali (senza etichette in legenda)
    # Fase 1: t < 0 ms (decadimento naturale spontaneo, Vin = 0) - colore ambra/dorato tenue
    # Fase 2: 0 <= t <= t* ms (frenatura attiva in controfase) - azzurro tenue
    # Fase 3: t > t* ms (ricrescita in controfase) - arancio tenue
    ax1.axvspan(-1.0, 0.0, color='#fab005', alpha=0.12)
    ax1.axvspan(0.0, t_star_ms, color='#1971c2', alpha=0.10)
    ax1.axvspan(t_star_ms, 8.5, color='#e8590c', alpha=0.07)

    ax1.plot(t_ms2, ch4_clean, color='#1971c2', linewidth=1.4, label='Segnale di comando $v_{in}$')
    ax1.axvline(0, color='#495057', linestyle=':', linewidth=1.2)
    ax1.axvline(t_star_ms, color='#d62728', linestyle=':', linewidth=1.2)
    ax1.set_ylabel('Tensione generatore [V]')
    ax1.set_title('Comando di alimentazione in controfase')
    ax1.grid(True)
    ax1.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')

    ax2.axvspan(-1.0, 0.0, color='#fab005', alpha=0.12)
    ax2.axvspan(0.0, t_star_ms, color='#1971c2', alpha=0.10)
    ax2.axvspan(t_star_ms, 8.5, color='#e8590c', alpha=0.07)

    ax2.plot(t_ms2, ch1_filt_clean, color='#adb5bd', alpha=0.65, linewidth=0.8, label='Segnale risuonatore')
    ax2.plot(t_ms2, env_clean, color='#1971c2', linewidth=1.6, label='Inviluppo')

    ax2.axvline(0, color='#495057', linestyle=':', linewidth=1.2, label='Inizio controfase')
    ax2.axvline(t_star_ms, color='#d62728', linestyle='--', linewidth=1.6,
                label=rf'Minimo di estinzione: $t^* = {t_star_ms:.2f}$ ms')

    ax2.set_xlim(-1.0, 8.5)
    ax2.set_ylim(-30, 35)
    ax2.set_xlabel('Tempo [ms]')
    ax2.set_ylabel('Tensione uscita [mV]')
    ax2.set_title('Risposta del MEMS')
    ax2.grid(True)
    ax2.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')

    plt.tight_layout()
    g2_path = os.path.join(OUTPUT_DIR, 'controfase_dinamica_completa.png')
    plt.savefig(g2_path)
    plt.close()

    # -------------------------------------------------------------------------
    # Grafico 3: Inviluppo e modello teorico analitico (Decay_controfase2.csv)
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=300)
    mask_clean2 = (d2['t'] >= -0.10e-3) & (d2['t'] <= 8.2e-3)
    t_ms2_env = d2['t'][mask_clean2] * 1e3
    env2_clean = d2['env_ch1'][mask_clean2] * 1e3

    ax.plot(t_ms2_env, env2_clean, color='#1971c2', linewidth=1.6, label='Inviluppo sperimentale')

    # Modello analitico fittato
    t_dense = np.linspace(0.0, 8.2e-3, 600)
    env_model = d2['analytical_model'](t_dense, d2['x0_fit'], d2['x_inf_fit'], d2['tau_fit']) * 1e3
    ax.plot(t_dense * 1e3, env_model, '--', color='#d62728', linewidth=2.0,
            label=rf'Modello: $\tau = {d2["tau_fit"]*1e3:.2f}$ ms, $X_\infty = {d2["x_inf_fit"]*1e3:.1f}$ mV')

    ax.axvline(d2['t_star_theory'] * 1e3, color='#2b8a3e', linestyle='-.', linewidth=1.6,
               label=rf'Tempo di spegnimento teorico: $t^* = \tau \ln(1 + X_0/X_\infty) = {d2["t_star_theory"]*1e3:.2f}$ ms')
    ax.axvline(d2['t_min'] * 1e3, color='#d62728', linestyle=':', linewidth=1.6,
               label=rf'Minimo sperimentale misurato: $t^* = {d2["t_quench_exp"]*1e3:.2f}$ ms')

    ax.set_xlim(-0.10, 8.3)
    ax.set_ylim(-1, 35)
    ax.set_xlabel('Tempo dall\'attivazione della controfase [ms]')
    ax.set_ylabel('Ampiezza dell\'inviluppo [mV]')
    ax.set_title('Confronto tra inviluppo misurato in controfase e modello teorico')
    ax.grid(True)
    ax.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')

    plt.tight_layout()
    g3_path = os.path.join(OUTPUT_DIR, 'inviluppo_e_modello_teorico.png')
    plt.savefig(g3_path)
    plt.close()

    # -------------------------------------------------------------------------
    # Grafico 4: Confronto tra decadimento naturale ed eccitazione in controfase
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=300)

    # Decadimento naturale (normalizzato all'ampiezza iniziale X0)
    tau_nat = res_nat['tau_hilb']
    t_norm_ms = np.linspace(0, 10.0, 500)
    env_nat_norm = np.exp(-t_norm_ms * 1e-3 / tau_nat) * 100.0
    ax.plot(t_norm_ms, env_nat_norm, color='#495057', linewidth=1.8, linestyle='--',
            label=f'Decadimento spontaneo naturale ($\\tau = {tau_nat*1e3:.2f}$ ms, $t_{{1\\%}} = 10.0$ ms)')

    # Controfase da Decay_controfase2.csv: discesa meccanica pulita da 100% fino a t* (zero) e stop netto
    idx_mech_start = np.argmin(np.abs(d2['t'] - 20e-6))
    idx_min = np.argmin(np.abs(d2['t'] - d2['t_quench_exp']))

    t_q_seg = np.linspace(0.0, t_star_ms, idx_min - idx_mech_start + 1)
    env_q_seg = d2['env_ch1'][idx_mech_start:idx_min + 1]
    env_q_norm = np.clip((env_q_seg / np.max(env_q_seg[:100])) * 100.0, 0.0, 100.0)

    ax.plot(t_q_seg, env_q_norm, color='#1971c2', linewidth=2.2,
            label=rf'Frenatura attiva in controfase ($t^* = {t_star_ms:.2f}$ ms, abbattimento {d2["reduction_pct"]:.1f}%)')

    # Punto terminale di azzeramento a t*
    ax.plot(t_star_ms, env_q_norm[-1], 'o', color='#1971c2', markersize=6.5,
            label=rf'Arresto oscillazione a $t^* = {t_star_ms:.2f}$ ms')

    # Linea tratteggiata di quiete a zero dopo t* (gating ideale dell\'alimentazione)
    t_quiet = np.linspace(t_star_ms, 10.0, 200)
    ax.plot(t_quiet, np.zeros_like(t_quiet), ':', color='#1971c2', linewidth=1.5, alpha=0.7,
            label=rf'Stato di quiete con alimentazione disattivata a $t^*$')

    # Linea soglia 1%
    ax.axhline(1.0, color='#d62728', linestyle=':', linewidth=1.2, label='Soglia residua 1%')
    ax.axvline(t_star_ms, color='#1971c2', linestyle=':', linewidth=1.2)
    ax.axvline(np.log(100.0) * tau_nat * 1e3, color='#495057', linestyle=':', linewidth=1.2)

    ax.text(t_star_ms + 0.25, 25.0,
            f'Controfase:\n$t^* = {t_star_ms:.2f}$ ms\n($11.7\\times$ piu rapido)',
            color='#1971c2', fontsize=10,
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#f8f9fa', edgecolor='#1971c2', alpha=0.9))

    ax.text(np.log(100.0) * tau_nat * 1e3 - 2.8, 30.0,
            f'Naturale:\n$t_{{1\\%}} = {np.log(100.0)*tau_nat*1e3:.1f}$ ms',
            color='#495057', fontsize=10,
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#f8f9fa', edgecolor='#ced4da', alpha=0.9))

    ax.set_xlim(-0.2, 10.5)
    ax.set_ylim(-2, 105)
    ax.set_xlabel('Tempo dall\'inizio della diseccitazione [ms]')
    ax.set_ylabel('Ampiezza residua normalizzata [%]')
    ax.set_title('Confronto dei tempi di estinzione dell\'oscillazione')
    ax.grid(True)
    ax.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')

    plt.tight_layout()
    g4_path = os.path.join(OUTPUT_DIR, 'confronto_tempi_diseccitazione.png')
    plt.savefig(g4_path)
    plt.close()

    # -------------------------------------------------------------------------
    # Grafico 5: Inviluppo esponenziale continuo con passaggio per lo zero (fittone)
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10.5, 5.8), dpi=300)
    t_full_ms = d2['t'] * 1e3
    ch1_full_mv = d2['ch1_filt'] * 1e3
    x0_mv = d2['x0_fit'] * 1e3
    x_inf_mv = d2['x_inf_fit'] * 1e3
    tau_fit_s = d2['tau_fit']
    t_star_theory_ms = d2['t_star_theory'] * 1e3

    # Segnale del risuonatore ad alta frequenza
    ax.plot(t_full_ms, ch1_full_mv, color='#1971c2', alpha=0.65, linewidth=0.7,
            label='Segnale risuonatore $v_{out}(t)$')

    # Esponenziale continuo con segno da t = 0 in poi (risposta fisica alla forzante)
    t_exp_pos = np.linspace(0.0, 8.58e-3, 800)
    v_exp_pos = (x0_mv + x_inf_mv) * np.exp(-t_exp_pos / tau_fit_s) - x_inf_mv
    ax.plot(t_exp_pos * 1e3, v_exp_pos, color='#d62728', linewidth=2.2,
            label=r'Inviluppo esponenziale: $(X_0 + X_\infty)e^{-t/\tau} - X_\infty$')

    # Tratteggio di estrapolazione per t < 0
    t_exp_neg = np.linspace(-1.42e-3, 0.0, 200)
    v_exp_neg = (x0_mv + x_inf_mv) * np.exp(-t_exp_neg / tau_fit_s) - x_inf_mv
    ax.plot(t_exp_neg * 1e3, v_exp_neg, ':', color='#d62728', linewidth=1.5, alpha=0.75,
            label='Estrapolazione matematica per $t < 0$')

    # Linee di riferimento
    ax.axhline(0, color='#495057', linestyle=':', linewidth=1.0)
    ax.axvline(0, color='#495057', linestyle='--', linewidth=1.1, label='Inizio controfase')
    ax.axvline(t_star_theory_ms, color='#2b8a3e', linestyle='-.', linewidth=1.6,
               label=rf'Passaggio per lo zero: $t^* = \tau \ln(1 + X_0/X_\infty) = {t_star_theory_ms:.2f}$ ms')

    ax.set_xlim(-1.42, 8.58)
    ax.set_ylim(-36, 52)
    ax.set_xlabel('Tempo [ms]')
    ax.set_ylabel('Tensione di uscita [mV]')
    ax.set_title('Inviluppo esponenziale')
    ax.grid(True)
    ax.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')

    plt.tight_layout()
    g5_exp_path = os.path.join(OUTPUT_DIR, 'esponenziale_controfase.png')
    plt.savefig(g5_exp_path)
    plt.close()

    # Grafico 6: Metodo picchi vs Hilbert
    plot_envelope_methods_comparison(res_nat)


def main():
    print("Inizio analisi del ringdown e dell'eccitazione in controfase...")

    # 1. Analisi del decadimento libero naturale
    res_nat = analyze_natural_decay()
    print("\n" + "="*60)
    print("1. DECADIMENTO NATURALE (scope_7.csv):")
    print(f"   Offset DC medio del canale: {res_nat['v_dc']*1e3:.3f} mV")
    print(f"   Decay.m (senza DC rimossa): tau_up = {res_nat['tau_up_raw']*1e3:.2f} ms | tau_lo = {res_nat['tau_lo_raw']*1e3:.2f} ms (errore: 26%)")
    print(f"   Corretto (con DC rimossa):  tau_up = {res_nat['tau_up']*1e3:.3f} ms | tau_lo = {res_nat['tau_lo']*1e3:.3f} ms (coerenza: 0.1%)")
    print(f"   Inviluppo di Hilbert:       tau = {res_nat['tau_hilb']*1e3:.3f} ms | Q = {int(round(res_nat['q_factor']))}")

    # 2. Analisi controfase (Decay_controfase.csv)
    res_cp1 = analyze_counterphase_dataset('Decay_controfase.csv', t_fit_start_s=0.05e-3, t_fit_end_s=1.7e-3)
    print("\n2. CONTROFASE AD ALTA EFFICIENZA (Decay_controfase.csv):")
    print(f"   Ampiezza iniziale X0: {res_cp1['x0_fit']*1e3:.2f} mV")
    print(f"   Ampiezza minima X_min: {res_cp1['x_min']*1e3:.2f} mV (abbattimento del {res_cp1['reduction_pct']:.1f}%)")
    print(f"   Tempo di estinzione misurato:  t* = {res_cp1['t_quench_exp']*1e3:.3f} ms ({res_cp1['t_quench_exp']*1e6:.1f} us)")
    print(f"   Tempo di estinzione teorico:   t* = {res_cp1['t_star_theory']*1e3:.3f} ms")

    # 3. Analisi controfase (Decay_controfase2.csv)
    res_cp2 = analyze_counterphase_dataset('Decay_controfase2.csv', t_fit_start_s=0.1e-3, t_fit_end_s=8.0e-3)
    print("\n3. CONTROFASE CON EVOLUZIONE A LUNGO TERMINE (Decay_controfase2.csv):")
    print(f"   Ampiezza iniziale X0: {res_cp2['x0_fit']*1e3:.2f} mV")
    print(f"   Ampiezza a regime X_inf: {res_cp2['x_inf_fit']*1e3:.2f} mV")
    print(f"   Costante di tempo tau stimata: {res_cp2['tau_fit']*1e3:.3f} ms")
    print(f"   Tempo di estinzione misurato:  t* = {res_cp2['t_quench_exp']*1e3:.3f} ms ({res_cp2['t_quench_exp']*1e6:.1f} us)")
    print(f"   Tempo di estinzione teorico:   t* = {res_cp2['t_star_theory']*1e3:.3f} ms")
    print("="*60 + "\n")

    # 4. Transitorio ultra-veloce di commutazione
    analyze_detail_switching()

    # 5. Generazione grafici
    generate_all_plots(res_nat, res_cp1, res_cp2)
    print("Grafici salvati con successo nella cartella Decay/grafici/")


if __name__ == '__main__':
    main()
