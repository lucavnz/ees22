import os
import numpy as np
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OSC_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
DATA_DIR = os.path.join(OSC_DIR, 'Misure')
OUT_DIR = os.path.join(OSC_DIR, 'Grafici')
os.makedirs(OUT_DIR, exist_ok=True)

OUT_PNG = os.path.join(OUT_DIR, 'sweep_fase_con_scope.png')
SWEEP_CSV = os.path.join(BASE_DIR, 'misure_max_min_vs_fase_20260923_131303.csv')
SCOPE_CSV = os.path.join(DATA_DIR, 'scope_172.csv')

# Caricamento dati Scope 172
scope_data = np.genfromtxt(SCOPE_CSV, delimiter=',', skip_header=2)
t_scope = scope_data[:, 0] * 1e6   # us
vout_scope = scope_data[:, 1] * 1e3 # mV
vin_scope = scope_data[:, 2] * 1e3  # mV

# Caricamento dati Sweep fase
sweep_data = np.genfromtxt(SWEEP_CSV, delimiter=',', comments='#', skip_header=3)
phase = sweep_data[:, 1]
vmax  = sweep_data[:, 2]
vmin  = sweep_data[:, 3]
vpp   = sweep_data[:, 5]

# Stile minimale e pulito
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.labelsize': 11,
    'axes.titlesize': 11.5,
    'xtick.labelsize': 9.5,
    'ytick.labelsize': 9.5,
    'legend.fontsize': 9.5,
    'lines.linewidth': 1.4,
    'grid.alpha': 0.35,
    'grid.linestyle': '--'
})

fig = plt.figure(figsize=(13.5, 6.2), dpi=300)
gs = fig.add_gridspec(2, 2, width_ratios=[1.05, 1.25], height_ratios=[1.3, 0.9],
                       wspace=0.22, hspace=0.20)

ax_vout = fig.add_subplot(gs[0, 0])
ax_vin  = fig.add_subplot(gs[1, 0], sharex=ax_vout)
ax_vpp  = fig.add_subplot(gs[:, 1])

# -------------------------------------------------------------------------
# PANNELLO SINISTRO (A): Traccia Oscilloscopio e Definizione Vmax, Vmin, Vpp
# -------------------------------------------------------------------------
# Finestra temporale di zoom
t_mask = (t_scope >= -1.0) & (t_scope <= 3.2)
t_win = t_scope[t_mask]
vout_win = vout_scope[t_mask]
vin_win = vin_scope[t_mask]

# Traccia Vout
color_vout = '#1971c2'
ax_vout.plot(t_win, vout_win, color=color_vout, linewidth=1.5, label=r'$v_{out}(t)$')
ax_vout.axhline(0, color='gray', linestyle=':', linewidth=0.8, alpha=0.6)
ax_vout.axvline(0, color='#495057', linestyle='--', linewidth=1.2, alpha=0.8)

# Valori estremi nel transitorio (t >= 0)
trans_mask = t_win >= 0
idx_max_trans = np.argmax(vout_win[trans_mask])
idx_min_trans = np.argmin(vout_win[trans_mask])
t_vmax = t_win[trans_mask][idx_max_trans]
val_vmax = vout_win[trans_mask][idx_max_trans]
t_vmin = t_win[trans_mask][idx_min_trans]
val_vmin = vout_win[trans_mask][idx_min_trans]
val_vpp = val_vmax - val_vmin

# Linee di livello orizzontali
ax_vout.axhline(val_vmax, color='#2b8a3e', linestyle='--', linewidth=1.0, alpha=0.85)
ax_vout.axhline(val_vmin, color='#d6336c', linestyle='--', linewidth=1.0, alpha=0.85)

# Punti sui picchi
ax_vout.scatter([t_vmax], [val_vmax], color='#2b8a3e', s=45, zorder=5)
ax_vout.scatter([t_vmin], [val_vmin], color='#d6336c', s=45, zorder=5)

# Etichette di Vmax e Vmin
box_kw = dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.9, edgecolor='#adb5bd', linewidth=0.7)
ax_vout.text(t_vmax + 0.15, val_vmax - 30, f'$V_{{max}} = +{val_vmax:.0f}$ mV', fontsize=9,
             color='#2b8a3e', bbox=box_kw)
ax_vout.text(t_vmin + 0.15, val_vmin + 30, f'$V_{{min}} = {val_vmin:.0f}$ mV', fontsize=9,
             color='#d6336c', bbox=box_kw)

# Freccia a doppia punta per Vpp
arrow_x = 2.15
ax_vout.annotate('', xy=(arrow_x, val_vmax), xytext=(arrow_x, val_vmin),
                 arrowprops=dict(arrowstyle='<->', color='#212529', lw=1.3))
ax_vout.text(arrow_x + 0.08, (val_vmax + val_vmin)/2, f'$V_{{pp}} = {val_vpp:.0f}$ mV',
             va='center', fontsize=8.8, color='#212529', bbox=box_kw)

ax_vout.set_title(r"Definizione di $V_{max}, V_{min}$ e $V_{pp}$ sulla traccia reale", pad=7)
ax_vout.set_ylabel(r"$v_{out}$ [mV]")
ax_vout.set_xlim(-0.8, 3.1)
ax_vout.set_ylim(-780, 980)
ax_vout.grid(True)
plt.setp(ax_vout.get_xticklabels(), visible=False)

# Traccia Vin (interruzione allo stacco)
color_vin = '#0ca678'
ax_vin.plot(t_win, vin_win, color=color_vin, linewidth=1.5, label=r'$v_{in}(t)$')
ax_vin.axvline(0, color='#495057', linestyle='--', linewidth=1.2, alpha=0.8)
ax_vin.axhline(0, color='gray', linestyle=':', linewidth=0.8, alpha=0.6)

# Indicazione Gate OFF
ax_vin.text(0.08, 65, 'Gate OFF\n($t = 0$)', fontsize=8.5, color='#495057')

ax_vin.set_xlabel(r"Tempo [$\mu$s]")
ax_vin.set_ylabel(r"$v_{in}$ [mV]")
ax_vin.set_xlim(-0.8, 3.1)
ax_vin.set_ylim(-115, 115)
ax_vin.grid(True)

# -------------------------------------------------------------------------
# PANNELLO DESTRO (B): Sweep di Vpp vs Fase di Burst (solo punti sperimentali)
# -------------------------------------------------------------------------
color_pp = '#212529'
ax_vpp.scatter(phase, vpp, color=color_pp, s=28, edgecolors='white', linewidths=0.5, zorder=3,
               label=r'Punti sperimentali $V_{pp}$')

ax_vpp.set_title(r"$V_{pp} = V_{max} - V_{min}$ al variare della fase di burst $\phi$", pad=7)
ax_vpp.set_xlabel(r"Fase impostata sul generatore $\phi$ [°]")
ax_vpp.set_ylabel(r"$V_{pp}$ [mV]")
ax_vpp.set_xlim(-185, 185)
ax_vpp.set_xticks(np.arange(-180, 181, 30))
ax_vpp.set_ylim(800, 1680)
ax_vpp.grid(True)
ax_vpp.legend(loc='lower center', frameon=True, facecolor='white', edgecolor='#ced4da')

# Salvataggio
plt.savefig(OUT_PNG, bbox_inches='tight')
plt.close()
print(f"Grafico salvato con successo in: {OUT_PNG}")
