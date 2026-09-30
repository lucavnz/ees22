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
    """Genera il grafico di confronto tra simulazione libera e controfase."""
    t_ms = sim['t'] * 1e3
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10.5, 6.8), dpi=300, sharex=True)

    # Subplot 1: Forme d'onda temporali (zoom)
    # Mostriamo i segnali normalizzati rispetto allo spostamento iniziale x0
    scale = 1.0 / sim['x0_disp']
    ax1.plot(t_ms, sim['sol_a'].y[0] * scale, color='#868e96', alpha=0.5, linewidth=0.6, label='Decadimento naturale')
    ax1.plot(t_ms, sim['sol_b'].y[0] * scale, color='#1971c2', alpha=0.7, linewidth=0.7, label='Controfase continua (non interrotta)')
    ax1.plot(t_ms, sim['sol_c'].y[0] * scale, color='#2b8a3e', linewidth=1.1, label='Controfase ottimale con gating (active quenching)')
    ax1.axvline(sim['t_star_opt'] * 1e3, color='#d62728', linestyle=':', linewidth=1.3,
                label=rf'Spegnimento forzante: $t^* = {sim["t_star_opt"]*1e3:.2f}$ ms')
    ax1.set_ylabel('Spostamento normalizzato $x(t) / X_0$')
    ax1.set_title('Risposta dinamica simulata del risuonatore MEMS (risoluzione ODE)')
    ax1.grid(True)
    ax1.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')

    # Subplot 2: Inviluppi a confronto
    ax2.plot(t_ms, sim['env_a'] * scale, color='#495057', linestyle='--', linewidth=1.8,
             label=rf'Inviluppo naturale: $\tau = {TAU*1e3:.2f}$ ms')
    ax2.plot(t_ms, sim['env_b'] * scale, color='#1971c2', linewidth=1.8,
             label=r'Inviluppo controfase continua (minimo a $t^*$ e ricrescita)')
    ax2.plot(t_ms, sim['env_c'] * scale, color='#2b8a3e', linewidth=2.0,
             label=r'Inviluppo controfase con gating (arresto immediato a zero)')
    ax2.axvline(sim['t_star_opt'] * 1e3, color='#d62728', linestyle=':', linewidth=1.3)
    ax2.axhline(0.01, color='#e03131', linestyle=':', linewidth=1.0, label='Soglia residua 1%')

    ax2.set_xlim(0, 6.0)
    ax2.set_ylim(-0.05, 1.8)
    ax2.set_xlabel('Tempo [ms]')
    ax2.set_ylabel('Ampiezza inviluppo normalizzata')
    ax2.set_title('Confronto degli inviluppi: dimostrazione fisica dell\'arresto rapido')
    ax2.grid(True)
    ax2.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')

    plt.tight_layout()
    g_path = os.path.join(OUTPUT_DIR, 'simulazione_ode_controfase.png')
    plt.savefig(g_path)
    plt.close()
    print(f"Grafico simulazione ODE salvato in: {g_path}")


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
