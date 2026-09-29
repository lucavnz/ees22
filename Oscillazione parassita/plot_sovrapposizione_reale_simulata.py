import os
import numpy as np
import matplotlib.pyplot as plt

# Percorsi
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'Misure')
OUT_DIR  = os.path.join(BASE_DIR, 'Grafici')
os.makedirs(OUT_DIR, exist_ok=True)
OUT_PNG  = os.path.join(OUT_DIR, 'sovrapposizione_simulazione_reale.png')

# -----------------------------------------------------------------------------
# 1. PARAMETRI DEI COMPONENTI SCELTI NEL MODELLO
# -----------------------------------------------------------------------------
Rf      = 500e3            # Resistore TIA [Ohm]
wt      = 2 * np.pi * 230e6 # Guadagno prodotto-banda OPA656 (GBWP = 230 MHz) [rad/s]
Cp      = 1.0e-12          # [F]
Cc      = 1.0e-12          # [F]
Cin     = 188e-12          # [F]
Cf      = 0.25e-12         # [F]
G2      = 10.0             # |G2| = R2/R1 = 1k/100

Cnodo   = Cin + Cp + Cc + Cf
a2      = Rf * Cnodo / wt
a1      = Rf * Cf + 1.0 / wt
a0      = 1.0

wn      = np.sqrt(a0 / a2)
zeta    = a1 / (2 * np.sqrt(a0 * a2))
wd      = wn * np.sqrt(1.0 - zeta**2)
fd      = wd / (2 * np.pi)
tau_el  = 1.0 / (zeta * wn)

# -----------------------------------------------------------------------------
# 2. CARICAMENTO DATI SPERIMENTALI REALI (SCOPE 172)
# -----------------------------------------------------------------------------
scope_path = os.path.join(DATA_DIR, 'scope_172.csv')
data_scope = np.genfromtxt(scope_path, delimiter=',', skip_header=2)
t_scope    = data_scope[:, 0] * 1e6    # us
vout_scope = data_scope[:, 1] * 1e3    # mV

# -----------------------------------------------------------------------------
# 3. COSTRUZIONE DELLA FORMA D'ONDA SIMULATA
# -----------------------------------------------------------------------------
t_sim_us = np.linspace(-0.8, 3.8, 5000) # us
t_sim_s  = t_sim_us * 1e-6              # s
vout_sim = np.zeros_like(t_sim_us)

# Pre-stacco (t < 0): oscillazione residua sinusoidale a f0 = 417.83 kHz
f0_stim = 417.83e3
w0_stim = 2 * np.pi * f0_stim
idx_pre = t_sim_s < 0
V_offset = -24.0 # mV
vout_sim[idx_pre] = V_offset + 15.5 * np.sin(w0_stim * t_sim_s[idx_pre] - 1.1)

# Post-stacco (t >= 0): risposta continua del 2° ordine
idx_post = t_sim_s >= 0
dt = t_sim_s[idx_post]

t_pk_rel = np.arctan(wd * tau_el) / wd
A0 = (804.0 - V_offset) / (np.exp(-t_pk_rel / tau_el) * np.sin(wd * t_pk_rel))
vout_sim[idx_post] = V_offset + A0 * np.exp(-dt / tau_el) * np.sin(wd * dt)

# -----------------------------------------------------------------------------
# 4. PLOTTING MINIMALE E PULITO
# -----------------------------------------------------------------------------
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

fig, ax = plt.subplots(figsize=(8.8, 5.8), dpi=300)

# 1. Traccia sperimentale reale
ax.plot(t_scope, vout_scope, color='#495057', alpha=0.55, linewidth=2.2,
        label='Misura reale')

# 2. Curva teorica simulata
ax.plot(t_sim_us, vout_sim, color='#1971c2', linewidth=2.0,
        label='Modello teorico')

# 3. Linea di riferimento Gate OFF (solo "Gate OFF", senza t=0)
ax.axvline(0, color='black', linestyle='--', linewidth=1.2, alpha=0.75, label='Gate OFF')
ax.axhline(0, color='black', linestyle=':', linewidth=0.8, alpha=0.5)

ax.set_xlim(-0.5, 3.5)
ax.set_ylim(-750, 950)
ax.set_xlabel(r'Tempo [$\mu$s]')
ax.set_ylabel(r'Tensione $V_{out}$ [mV]')
ax.set_title('Misura reale vs modello teorico simulato', pad=9)
ax.grid(True)
ax.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')

plt.savefig(OUT_PNG, bbox_inches='tight')
plt.close()
print(f"[OK] Grafico minimale generato: {OUT_PNG}")
