import os
import numpy as np
import matplotlib.pyplot as plt

# Percorsi
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, 'misure_max_min_vs_fase_20260923_131303.csv')
OUT_PNG  = os.path.join(BASE_DIR, 'plot_misure_cp_vs_fase.png')

# Caricamento dati da CSV
data = np.genfromtxt(CSV_FILE, delimiter=',', comments='#', skip_header=3)
phase = data[:, 1]
vmax  = data[:, 2]
vmin  = data[:, 3]
apeak = data[:, 4]
vpp   = data[:, 5]

# Stile pulito, minimale e leggibile
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.labelsize': 11.5,
    'axes.titlesize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 9.5,
    'lines.linewidth': 1.2,
    'grid.alpha': 0.35,
    'grid.linestyle': '--'
})

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11.5, 9), sharex=True, dpi=300)
fig.subplots_adjust(hspace=0.16)

# -------------------------------------------------------------------------
# SUBPLOT 1: Vmax e Vmin (Picchi Positivo e Negativo)
# -------------------------------------------------------------------------
color_max = '#1971c2'  # Blu
color_min = '#d6336c'  # Magenta / Rosso elegante

# Solo punti sperimentali
ax1.scatter(phase, vmax, color=color_max, s=26, edgecolors='white', linewidths=0.4, zorder=3, label=r'$V_{max}$')
ax1.scatter(phase, vmin, color=color_min, s=26, edgecolors='white', linewidths=0.4, zorder=3, label=r'$V_{min}$')

ax1.axhline(0, color='gray', linestyle=':', linewidth=0.8, alpha=0.7)

ax1.set_title(r"$V_{max}$ e $V_{min}$ al variare della fase di burst", pad=8)
ax1.set_ylabel(r"Tensione [mV]")
ax1.set_ylim(-1300, 1300)
ax1.grid(True)
ax1.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='#ced4da', ncol=2)

# -------------------------------------------------------------------------
# SUBPLOT 2: Escursione Picco-Picco Totale Vpp = Vmax - Vmin
# -------------------------------------------------------------------------
color_pp = '#212529'  # Antracite scuro

# Solo punti sperimentali
ax2.scatter(phase, vpp, color=color_pp, s=26, edgecolors='white', linewidths=0.4, zorder=3, label=r'$V_{pp} = V_{max} - V_{min}$')

ax2.set_title(r"$V_{pp} = V_{max} - V_{min}$ al variare della fase di burst", pad=8)
ax2.set_xlabel(r"Fase impostata sul generatore $\phi$ [°]")
ax2.set_ylabel(r"$V_{pp}$ [mV]")
ax2.set_xlim(-185, 185)
ax2.set_xticks(np.arange(-180, 181, 30))
ax2.set_ylim(800, 1680)
ax2.grid(True)
ax2.legend(loc='lower center', frameon=True, facecolor='white', edgecolor='#ced4da')

# Salvataggio
plt.savefig(OUT_PNG, bbox_inches='tight')
plt.close()
print(f"Grafico salvato con successo in: {OUT_PNG}")
