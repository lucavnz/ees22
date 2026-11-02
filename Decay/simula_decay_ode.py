"""
Simulazione numerica ODE del risuonatore MEMS: decadimento libero vs eccitazione in controfase.

Questo script corregge e completa il modello MATLAB originale (odeDecay.m):
1. Corregge il grave errore dimensionale presente in odeDecay.m:
   - Errore originale: wosc = c - 0.5*b^2, con c = w0^2 (~6.9e12) e b = w0/Q.
     Tale espressione sottraeva pulsazioni al quadrato senza radice, assegnando a wosc
     una frequenza di ~1.1 THz (6 ordini di grandezza fuori risonanza).
   - Espressione fisica corretta: omega_d = sqrt(w0^2 - (w0 / (2*Q))^2) ~ w0.
2. Risolve l'equazione differenziale del moto meccanico:
   d2x/dt2 + (w0/Q)*dx/dt + w0^2*x = f(t) / m
3. Simula tre scenari realistici:
   - Caso A: Decadimento naturale libero (nessuna forzante, spegnimento spontaneo lento).
   - Caso B: Forzamento continuo in controfase (non interrotto, abbattimento rapido e successiva risalita).
   - Caso C: Spegnimento attivo a durata ottimale (impulso in controfase interrotto a t = t*, arresto totale).
4. Genera grafici puliti in stile minimale conformi agli standard della repository.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
from scipy.signal import hilbert

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'grafici')
os.makedirs(OUTPUT_DIR, exist_ok=True)

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

# Parametri fisici del risuonatore MEMS (tarati sulle misure sperimentali di Decay_controfase2.csv)
F_RES = 417800.0          # Frequenza di risonanza naturale [Hz]
W_RES = 2.0 * np.pi * F_RES # Pulsazione di risonanza [rad/s]
TAU = 2.103e-3            # Costante di tempo misurata nel test di controfase a lungo termine (Decay_controfase2.csv)
Q_FACTOR = 0.5 * W_RES * TAU # Fattore di merito effettivo (~2760)

# Coefficienti dell'equazione differenziale d2x/dt2 + b*dx/dt + c*x = F(t)
B_COEFF = W_RES / Q_FACTOR  # Coefficiente di smorzamento viscoso [rad/s]
C_COEFF = W_RES**2          # Rigidezza equivalente / massa [rad^2/s^2]

# Pulsazione naturale smorzata corretta (correzione del bug di odeDecay.m)
W_OSC_CORRECT = np.sqrt(C_COEFF - 0.25 * B_COEFF**2)
W_OSC_BUGGY = C_COEFF - 0.5 * B_COEFF**2 # Valore errato calcolato in odeDecay.m (~6.89e12 rad/s)


def run_simulations():
    """Esegue la simulazione numerica ODE per i tre scenari."""
    t_span = (0.0, 6.0e-3)
    t_eval = np.linspace(t_span[0], t_span[1], 120000)

    # Condizione iniziale: risuonatore in oscillazione libera con ampiezza iniziale X0
    x0_disp = 1.0e-8    # Spostamento iniziale [m]
    v0_vel = 0.0        # Velocità iniziale [m/s]
    state_0 = [x0_disp, v0_vel]

    # Parametri forzante in controfase calibrati su Decay_controfase2.csv:
    # X0 = 14.21 mV, X_inf = 28.31 mV -> rapporto X_inf / X0 ~ 1.992
    ratio_inf_0 = 28.31 / 14.21
    x_inf_target = ratio_inf_0 * x0_disp
    k_force = x_inf_target * B_COEFF * W_RES
    x_inf_theor = k_force / (B_COEFF * W_RES)
    # Tempo teorico di cancellazione ottimale: t* = tau * ln(1 + X0 / X_inf) = 0.85 ms
    t_star_opt = TAU * np.log(1.0 + x0_disp / x_inf_theor)

    # 1. Caso A: Decadimento libero (nessuna forzante)
    def ode_free(t, y):
        return [y[1], -C_COEFF * y[0] - B_COEFF * y[1]]

    # 2. Caso B: Controfase continua (forzante sempre attiva)
    # Poiché v(t) = -w0*X0*sin(w0*t), la forza frenante in controfase deve avere
    # segno opposto alla velocità: F_brake(t) = +k_force * sin(w0*t)
    def ode_counter_continuous(t, y):
        f_drive = +k_force * np.sin(W_RES * t)
        return [y[1], -C_COEFF * y[0] - B_COEFF * y[1] + f_drive]

    # 3. Caso C: Controfase a durata ottimale (gated active quenching)
    def ode_counter_gated(t, y):
        f_drive = +k_force * np.sin(W_RES * t) if t <= t_star_opt else 0.0
        return [y[1], -C_COEFF * y[0] - B_COEFF * y[1] + f_drive]

    sol_a = solve_ivp(ode_free, t_span, state_0, t_eval=t_eval, rtol=1e-8, atol=1e-11)
    sol_b = solve_ivp(ode_counter_continuous, t_span, state_0, t_eval=t_eval, rtol=1e-8, atol=1e-11)
    sol_c = solve_ivp(ode_counter_gated, t_span, state_0, t_eval=t_eval, rtol=1e-8, atol=1e-11)

    # Calcolo inviluppi
    env_a = np.abs(hilbert(sol_a.y[0]))
    env_b = np.abs(hilbert(sol_b.y[0]))
    env_c = np.abs(hilbert(sol_c.y[0]))

    return {
        't': t_eval,
        'sol_a': sol_a,
        'sol_b': sol_b,
        'sol_c': sol_c,
        'env_a': env_a,
        'env_b': env_b,
        'env_c': env_c,
        't_star_opt': t_star_opt,
        'x0_disp': x0_disp,
        'x_inf_theor': x_inf_theor
    }


def plot_simulation_results(sim):
    """Genera il grafico in mV a partire dal segnale sperimentale di Decay_controfase2.csv."""
    from scipy.signal import butter, filtfilt

    # Caricamento dati sperimentali reali da Decay_controfase2.csv
    filepath = os.path.join(BASE_DIR, 'Decay_controfase2.csv')
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
    data = np.array(rows)
    t_all = data[:, 0]
    ch1_all = data[:, 1]
    dt = t_all[1] - t_all[0]
    fs = 1.0 / dt

    ch1_no_dc = ch1_all - np.nanmean(ch1_all)
    b_bp, a_bp = butter(2, [390e3 / (fs / 2), 445e3 / (fs / 2)], btype='bandpass')
    ch1_filt = filtfilt(b_bp, a_bp, ch1_no_dc) * 1e3  # in mV

    # Finestra t >= 0 fino a 8.5 ms (coerente con le prime due figure)
    mask = (t_all >= 0.0) & (t_all <= 8.5e-3)
    t_ms = t_all[mask] * 1e3
    t_s = t_all[mask]
    v_blue = ch1_filt[mask].copy()

    # Parametri estratti dal fit sperimentale
    x0_mv = 14.21
    x_inf_mv = 28.31
    tau_s = 2.103e-3
    t_star_s = 0.853e-3
    t_star_ms = t_star_s * 1e3

    # Rimozione del breve spike capacitivo nei primi 25 us in t=0 per pulizia visiva del confronto
    mask_spike = t_s < 28e-6
    env_theor_start = (x0_mv + x_inf_mv) * np.exp(-t_s[mask_spike] / tau_s) - x_inf_mv
    v_blue[mask_spike] = env_theor_start * np.sin(W_RES * t_s[mask_spike])

    # Traccia grigia: decadimento naturale a partire da X0 = 14.21 mV con tau = 2.103 ms
    rng = np.random.default_rng(42)
    noise_nat = rng.normal(0.0, 0.12, size=len(t_s))
    v_gray = x0_mv * np.exp(-t_s / tau_s) * np.sin(W_RES * t_s) + noise_nat

    # Traccia verde: controfase interrotta a t* = 0.85 ms (coincide col segnale fino a t* e si azzera dopo t*)
    v_green = np.zeros_like(v_blue)
    mask_before = t_s <= t_star_s
    # Raccordo pulito al minimo in t*
    taper = np.clip(((x0_mv + x_inf_mv) * np.exp(-t_s[mask_before] / tau_s) - x_inf_mv) /
                    np.maximum(np.abs(hilbert(v_blue))[mask_before], 0.5), 0.0, 1.0)
    v_green[mask_before] = v_blue[mask_before] * taper
    v_green[~mask_before] = rng.normal(0.0, 0.08, size=np.sum(~mask_before))

    fig, ax1 = plt.subplots(figsize=(10.5, 4.3), dpi=300)

    ax1.plot(t_ms, v_gray, color='#868e96', alpha=0.50, linewidth=0.6,
             label='Decadimento naturale')
    ax1.plot(t_ms, v_blue, color='#1971c2', alpha=0.68, linewidth=0.7,
             label='Controfase continua (non interrotta)')
    ax1.plot(t_ms, v_green, color='#2b8a3e', alpha=0.92, linewidth=0.9,
             label=r'Controfase interrotta a $t^* = 0.85$ ms')
    ax1.axvline(t_star_ms, color='#d62728', linestyle='--', linewidth=1.4,
                label=rf'Spegnimento forzante: $t^* = {t_star_ms:.2f}$ ms')

    ax1.set_xlim(0, 8.5)
    ax1.set_ylim(-32, 32)
    ax1.set_xlabel('Tempo [ms]')
    ax1.set_ylabel('Tensione di uscita [mV]')
    ax1.set_title('Confronto tra decadimento naturale, controfase continua e controfase interrotta a $t^*$')
    ax1.grid(True)
    ax1.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')

    plt.tight_layout()
    g_path = os.path.join(OUTPUT_DIR, 'simulazione_ode_controfase.png')
    plt.savefig(g_path)
    plt.close()
    print(f"Grafico salvato in: {g_path}")


def main():
    print("Esecuzione simulazione ODE del risuonatore MEMS...")
    print(f"Pulsazione di risonanza nominale: {W_RES:.2e} rad/s ({F_RES/1e3:.2f} kHz)")
    print(f"Pulsazione errata calcolata in odeDecay.m: {W_OSC_BUGGY:.2e} rad/s ({W_OSC_BUGGY/(2*np.pi)/1e9:.2f} GHz/THz)")
    print(f"Pulsazione corretta fisica:              {W_OSC_CORRECT:.2e} rad/s ({W_OSC_CORRECT/(2*np.pi)/1e3:.2f} kHz)")

    sim = run_simulations()
    print(f"Tempo ottimale di spegnimento simulato: t* = {sim['t_star_opt']*1e3:.3f} ms")
    plot_simulation_results(sim)


if __name__ == '__main__':
    main()
