import os
import numpy as np
import matplotlib.pyplot as plt

# Percorsi delle directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'Misure')
OUTPUT_DIR = os.path.join(BASE_DIR, 'Grafici')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Caricamento dei dati
def load_scope(filename):
    filepath = os.path.join(DATA_DIR, filename)
    data = np.genfromtxt(filepath, delimiter=',', skip_header=2)
    t = data[:, 0]
    ch1 = data[:, 1] # Vout
    ch3 = data[:, 2] # Vin
    return t, ch1, ch3

t173, vout173, vin173 = load_scope('scope_173.csv')
t172, vout172, vin172 = load_scope('scope_172.csv')

# Conversione unità: microsecondi e millivolt
t173_us = t173 * 1e6
t172_us = t172 * 1e6

vout173_mv = vout173 * 1e3
vin173_mv = vin173 * 1e3

vout172_mv = vout172 * 1e3
vin172_mv = vin172 * 1e3

# Stile grafico minimalista e pulito: nessun grassetto
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.labelsize': 11.5,
    'axes.titlesize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 9.5,
    'lines.linewidth': 1.6,
    'grid.alpha': 0.3,
    'grid.linestyle': '--'
})

fig, axes = plt.subplots(2, 2, figsize=(14, 8.5), sharex=True, dpi=300,
                         gridspec_kw={'height_ratios': [1.3, 1.0], 'hspace': 0.12, 'wspace': 0.16})

ax_vout_173 = axes[0, 0]
ax_vout_172 = axes[0, 1]
ax_vin_173  = axes[1, 0]
ax_vin_172  = axes[1, 1]

t_min, t_max = -2.5, 5.0

# -------------------------------------------------------------
# COLONNA 1: SCOPE 173 (dvin/dt > 0)
# -------------------------------------------------------------

# 1.1 Vout Scope 173
color_out_173 = '#c92a2a'
ax_vout_173.plot(t173_us, vout173_mv, color=color_out_173, label=r'Uscita $V_{out}$')
ax_vout_173.axhline(0, color='black', linestyle=':', linewidth=0.8, alpha=0.6)
ax_vout_173.axvline(0, color='#495057', linestyle='--', linewidth=1.3, alpha=0.75, label='Gate OFF')

# Annotazioni minimaliste senza aggettivi e senza grassetto
box_kw = dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.85, edgecolor='#ced4da', linewidth=0.8)

ax_vout_173.annotate(r'$-607$ mV' '\n' r'($t = 0.20\ \mu$s)',
                     xy=(0.197, -607.1), xytext=(0.55, -550),
                     arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.0),
                     fontsize=9, bbox=box_kw)

ax_vout_173.annotate(r'$+720$ mV' '\n' r'($t = 0.74\ \mu$s)',
                     xy=(0.738, 720.3), xytext=(1.25, 680),
                     arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.0),
                     fontsize=9, bbox=box_kw)

ax_vout_173.annotate(r'$-161$ mV' '\n' r'($t = 1.84\ \mu$s)',
                     xy=(1.841, -160.7), xytext=(2.35, -280),
                     arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.0),
                     fontsize=9, bbox=box_kw)

ax_vout_173.set_title(r"Spegnimento del gate quando $\frac{dv_{in}}{dt} > 0$", pad=9)
ax_vout_173.set_ylabel(r"Uscita $V_{out}$ [mV]")
ax_vout_173.set_ylim(-750, 950)
ax_vout_173.grid(True)
ax_vout_173.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='#ced4da')

# 1.2 Vin Scope 173
color_in_173 = '#e67700'
ax_vin_173.plot(t173_us, vin173_mv, color=color_in_173, linewidth=1.7, label=r'Ingresso $V_{in}$')
ax_vin_173.axvline(0, color='#495057', linestyle='--', linewidth=1.3, alpha=0.75)
ax_vin_173.axhline(0, color='black', linestyle=':', linewidth=0.8, alpha=0.5)

ax_vin_173.set_xlabel(r"Tempo [$\mu$s]")
ax_vin_173.set_ylabel(r"Ingresso $V_{in}$ [mV]")
ax_vin_173.set_ylim(-115, 115)
ax_vin_173.grid(True)
ax_vin_173.legend(loc='lower right', frameon=True, facecolor='white', edgecolor='#ced4da')


# -------------------------------------------------------------
# COLONNA 2: SCOPE 172 (dvin/dt < 0)
# -------------------------------------------------------------

# 2.1 Vout Scope 172
color_out_172 = '#1971c2'
ax_vout_172.plot(t172_us, vout172_mv, color=color_out_172, label=r'Uscita $V_{out}$')
ax_vout_172.axhline(0, color='black', linestyle=':', linewidth=0.8, alpha=0.6)
ax_vout_172.axvline(0, color='#495057', linestyle='--', linewidth=1.3, alpha=0.75)

ax_vout_172.annotate(r'$+804$ mV' '\n' r'($t = 0.21\ \mu$s)',
                     xy=(0.213, 804.0), xytext=(0.6, 780),
                     arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.0),
                     fontsize=9, bbox=box_kw)

ax_vout_172.annotate(r'$-671$ mV' '\n' r'($t = 0.82\ \mu$s)',
                     xy=(0.816, -671.4), xytext=(1.3, -580),
                     arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.0),
                     fontsize=9, bbox=box_kw)

ax_vout_172.annotate(r'$+99$ mV' '\n' r'($t = 1.90\ \mu$s)',
                     xy=(1.904, 98.5), xytext=(2.35, 230),
                     arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.0),
                     fontsize=9, bbox=box_kw)

ax_vout_172.set_title(r"Spegnimento del gate quando $\frac{dv_{in}}{dt} < 0$", pad=9)
ax_vout_172.set_ylabel(r"Uscita $V_{out}$ [mV]")
ax_vout_172.set_ylim(-750, 950)
ax_vout_172.grid(True)
ax_vout_172.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='#ced4da')

# 2.2 Vin Scope 172
color_in_172 = '#0ca678'
ax_vin_172.plot(t172_us, vin172_mv, color=color_in_172, linewidth=1.7, label=r'Ingresso $V_{in}$')
ax_vin_172.axvline(0, color='#495057', linestyle='--', linewidth=1.3, alpha=0.75)
ax_vin_172.axhline(0, color='black', linestyle=':', linewidth=0.8, alpha=0.5)

ax_vin_172.set_xlabel(r"Tempo [$\mu$s]")
ax_vin_172.set_ylabel(r"Ingresso $V_{in}$ [mV]")
ax_vin_172.set_ylim(-115, 115)
ax_vin_172.grid(True)
ax_vin_172.legend(loc='lower right', frameon=True, facecolor='white', edgecolor='#ced4da')

# Limiti X comuni per tutti i subplot
for ax in axes.flat:
    ax.set_xlim(t_min, t_max)

# Nessun titolo gigante (plt.suptitle rimosso)

out_file = os.path.join(OUTPUT_DIR, 'transitorio_elettrico_vdc0.png')
plt.savefig(out_file, bbox_inches='tight')
plt.close()
print(f'Grafico generato con successo: {out_file}')

# Sincronizzazione con Ampiezza_Frequenza/grafici/
out_amp = os.path.join(BASE_DIR, '..', 'Ampiezza_Frequenza', 'grafici', 'transitorio_elettrico_vdc0.png')
if os.path.exists(os.path.dirname(out_amp)):
    import shutil
    shutil.copy(out_file, out_amp)
    print(f'Copia sincronizzata in: {out_amp}')
