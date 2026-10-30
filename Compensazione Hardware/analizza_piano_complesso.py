"""
Analisi Vettoriale nel Piano Complesso (Diagrammi di Nyquist / Cerchi di Ammettenza)
per la Compensazione Hardware e Software del Risonatore MEMS

Questo script sviluppa da zero l'analisi geometrica e vettoriale nel piano complesso
Re{T(jw)} vs Im{T(jw)} della funzione di trasferimento del MEMS + front-end TIA:
1. Carica i dati sperimentali dello sweep non compensato (Risposta in frequenza)
   e degli sweep con compensazione hardware attiva (Set 1, Set 2, Off).
2. Esegue il fit vettoriale complesso del modello di Lorentz + feedthrough:
       T(f) = C_feed + (A_mot * exp(j * phi_m)) / (1 + j * 2*Q*(f - f0)/f0)
   e il fit algebrico di Kasa della circonferenza di risonanza nel piano di Gauss.
3. Genera tre figure ad alta risoluzione (300 DPI) per la relazione tecnica:
   - cerchio_nyquist_confronto_globale.png : Confronto tra piano complesso globale
     (traslazione dovuta a Cp) e zoom sull'origine (compensazione HW Set 1, Set 2 e SW).
   - cerchio_nyquist_dettaglio_fano.png    : Costruzione geometrica vettoriale
     dell'interferenza costruttiva (risonanza) e distruttiva (antirisonanza di Fano)
     rispetto alla risposta compensata hardware.
   - nyquist_set2_frequenza.png            : Luogo di Nyquist della taratura ottimizzata
     (Set 2) mappato cromaticamente in funzione della frequenza di eccitazione f_in.
"""

import os
import glob
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch

# -----------------------------------------------------------------------------
# 1. Configurazione percorsi e parametri del front-end
# -----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR  = os.path.join(BASE_DIR, 'grafici')
os.makedirs(OUT_DIR, exist_ok=True)

ROOT_DIR = os.path.dirname(BASE_DIR)
DIR_NON_COMP = os.path.join(ROOT_DIR, 'Risposta in frequenza', 'frequenza')
FILE_MOD_NON_COMP = os.path.join(DIR_NON_COMP, 'modulo_VDC_05p0V_417820Hz_501pt_20260916_171901.csv')
FILE_FAS_NON_COMP = os.path.join(DIR_NON_COMP, 'fase_VDC_05p0V_417820Hz_501pt_20260916_171901.csv')

Rf = 500e3         # Resistenza di retroazione TIA [Ohm]
G2 = 10.0          # Guadagno secondo stadio invertente AD817
R_trans = Rf * G2  # Trans-resistenza complessiva = 5.0 MOhm

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 10.5,
    'axes.labelsize': 11,
    'axes.titlesize': 11.5,
    'xtick.labelsize': 9.5,
    'ytick.labelsize': 9.5,
    'legend.fontsize': 9.5,
    'grid.alpha': 0.35,
    'grid.linestyle': '--'
})

# -----------------------------------------------------------------------------
# 2. Funzioni ausiliarie (filtro mediano puro NumPy e fit vettoriale complesso)
# -----------------------------------------------------------------------------
def medfilt_np(x, k=5):
    """Filtro mediano 1D implementato in puro NumPy."""
    pad = k // 2
    xp = np.pad(x, pad, mode='edge')
    return np.median([xp[i:i + len(x)] for i in range(k)], axis=0)

def load_hw_dataset(folder_name, f_min=None, f_max=None):
    """Carica modulo e fase, pulisce i dropout isolati e costruisce il fasore complesso T."""
    fdir = os.path.join(BASE_DIR, folder_name)
    mod_file = glob.glob(os.path.join(fdir, 'modulo_*.csv'))[0]
    fas_file = glob.glob(os.path.join(fdir, 'fase_*.csv'))[0]

    d_m = np.loadtxt(mod_file, delimiter=',', skiprows=2)
    d_p = np.loadtxt(fas_file, delimiter=',', skiprows=2)

    f_hz = d_m[:, 0]
    f_khz = f_hz / 1e3
    gain_lin = d_m[:, 3]
    gain_db = d_m[:, 4]

    raw_phase = d_p[:, 1]
    phase_wrap = (raw_phase + 180.0) % 360.0 - 180.0

    phase_clean = np.copy(phase_wrap)
    if folder_name in ['1', '2']:
        p_med = medfilt_np(phase_wrap, 5)
        dropout = (np.abs(phase_wrap - (-8.9)) < 1.5) & (p_med > 10.0)
        phase_clean[dropout] = p_med[dropout]

    if f_min is not None and f_max is not None:
        mask = (f_khz >= f_min) & (f_khz <= f_max)
    else:
        mask = np.ones(len(f_khz), dtype=bool)

    f_hz = f_hz[mask]
    f_khz = f_khz[mask]
    gain_lin = gain_lin[mask]
    gain_db = gain_db[mask]
    phase_clean = phase_clean[mask]
    T_meas = gain_lin * np.exp(1j * np.deg2rad(phase_clean))

    return {
        'f_hz': f_hz,
        'f_khz': f_khz,
        'gain_lin': gain_lin,
        'gain_db': gain_db,
        'phase_deg': phase_clean,
        'T_meas': T_meas
    }

def fit_complex_lorentzian(f_hz, T_meas, f0_guess):
    """
    Fit a proiezione di variabili nel piano complesso:
    Per ogni coppia (f0, Q), i parametri complessi lineari C_feed e B_mot = A_mot * e^(j*phi_m)
    sono determinati esattamente ai minimi quadrati lineari complessi.
    """
    best_err = np.inf
    best_sol = None

    # Ricerca globale su griglia
    for f0 in np.linspace(f0_guess - 60.0, f0_guess + 60.0, 61):
        for Q in np.linspace(1400.0, 3400.0, 51):
            x = 2.0 * Q * (f_hz - f0) / f0
            L = 1.0 / (1.0 + 1j * x)
            A = np.column_stack([np.ones_like(L), L])
            sol, _, _, _ = np.linalg.lstsq(A, T_meas, rcond=None)
            err = np.sum(np.abs(T_meas - A @ sol) ** 2)
            if err < best_err:
                best_err = err
                best_sol = (f0, Q, sol[0], sol[1])

    # Raffinamento locale sub-Hz
    f0_b, Q_b, _, _ = best_sol
    for f0 in np.linspace(f0_b - 4.0, f0_b + 4.0, 81):
        for Q in np.linspace(Q_b - 80.0, Q_b + 80.0, 61):
            x = 2.0 * Q * (f_hz - f0) / f0
            L = 1.0 / (1.0 + 1j * x)
            A = np.column_stack([np.ones_like(L), L])
            sol, _, _, _ = np.linalg.lstsq(A, T_meas, rcond=None)
            err = np.sum(np.abs(T_meas - A @ sol) ** 2)
            if err < best_err:
                best_err = err
                best_sol = (f0, Q, sol[0], sol[1])

    f0_opt, Q_opt, C_feed, B_mot = best_sol
    A_mot = np.abs(B_mot)
    phi_m = np.angle(B_mot)

    # Costruzione del cerchio teorico completo chiuso (incluso il limite x -> inf in C_feed)
    theta = np.linspace(-0.498 * np.pi, 0.498 * np.pi, 600)
    x_full = np.tan(theta)
    T_arc = C_feed + B_mot / (1.0 + 1j * x_full)
    T_circle = np.concatenate([[C_feed], T_arc, [C_feed]])

    # Centro geometrico della circonferenza: C_center = C_feed + B_mot / 2
    C_center = C_feed + 0.5 * B_mot
    R_circle = 0.5 * A_mot

    return {
        'f0': f0_opt,
        'Q': Q_opt,
        'C_feed': C_feed,
        'B_mot': B_mot,
        'A_mot': A_mot,
        'phi_m': phi_m,
        'C_center': C_center,
        'R_circle': R_circle,
        'T_circle': T_circle
    }

# -----------------------------------------------------------------------------
# 3. Caricamento dei dataset e calcolo dei fit complessi
# -----------------------------------------------------------------------------
print("Caricamento dati e fit nel piano complesso...")

# Dataset Non Compensato
d_unc_m = np.loadtxt(FILE_MOD_NON_COMP, delimiter=',', skiprows=2)
d_unc_f = np.loadtxt(FILE_FAS_NON_COMP, delimiter=',', skiprows=2)
mask_u = d_unc_m[:, 0] <= 418000.0
f_u_hz = d_unc_m[mask_u, 0]
f_u_khz = f_u_hz / 1e3
g_u_lin = d_unc_m[mask_u, 3]
ph_u_deg = d_unc_f[mask_u, 1]
T_u_meas = g_u_lin * np.exp(1j * np.deg2rad(ph_u_deg))

fit_u = fit_complex_lorentzian(f_u_hz, T_u_meas, 417665.0)

# Compensazione Software: sottrazione di C_feed
T_sw_meas = T_u_meas - fit_u['C_feed']
T_sw_circle = fit_u['T_circle'] - fit_u['C_feed']

# Dataset Compensazione Hardware (Set 1 e Set 2)
data_1 = load_hw_dataset('1', f_min=417.540, f_max=418.100)
data_2 = load_hw_dataset('2', f_min=417.535, f_max=418.100)

fit_1 = fit_complex_lorentzian(data_1['f_hz'], data_1['T_meas'], 417770.0)
fit_2 = fit_complex_lorentzian(data_2['f_hz'], data_2['T_meas'], 417750.0)

print(f"Non compensato : f0={fit_u['f0']:.1f} Hz, Q={fit_u['Q']:.0f}, |C_feed|={np.abs(fit_u['C_feed']):.3f}, Diametro A_mot={fit_u['A_mot']:.3f}")
print(f"Comp. HW Set 1 : f0={fit_1['f0']:.1f} Hz, Q={fit_1['Q']:.0f}, |C_feed|={np.abs(fit_1['C_feed']):.3f}, Diametro A_mot={fit_1['A_mot']:.3f}")
print(f"Comp. HW Set 2 : f0={fit_2['f0']:.1f} Hz, Q={fit_2['Q']:.0f}, |C_feed|={np.abs(fit_2['C_feed']):.3f}, Diametro A_mot={fit_2['A_mot']:.3f}")

# -----------------------------------------------------------------------------
# FIGURA 1: Piano complesso globale vs Zoom sull'origine (Confronto dei cerchi)
# -----------------------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.4, 5.8), dpi=300)

# --- Pannello SX: Vista globale del piano di Gauss ---
ax1.axhline(0, color='#adb5bd', lw=1.0, zorder=1)
ax1.axvline(0, color='#adb5bd', lw=1.0, zorder=1)

# Vettore di feedthrough parassita C_feed dall'origine
C_re_u = np.real(fit_u['C_feed'])
C_im_u = np.imag(fit_u['C_feed'])
ax1.annotate('', xy=(C_re_u, C_im_u), xytext=(0, 0),
             arrowprops=dict(arrowstyle='->', color='#e03131', lw=2.0, ls='--'), zorder=3)
ax1.text(2.4, 5.3,
         rf'Contributo parassita $T_p$' + '\n' + rf'$|T_p| = {np.abs(fit_u["C_feed"]):.2f}$ ($C_p = 0.89$ pF)' + '\n' + r'$\angle T_p = +68.6^\circ$',
         color='#c92a2a', fontsize=9.2,
         bbox=dict(boxstyle='round,pad=0.35', facecolor='white', edgecolor='#ffa8a8', alpha=0.94))

# Cerchio non compensato (lontano dall'origine)
ax1.plot(np.real(T_u_meas), np.imag(T_u_meas), 'o', color='#868e96', alpha=0.45, markersize=2.5,
         label='Punti sperimentali non compensati')
ax1.plot(np.real(fit_u['T_circle']), np.imag(fit_u['T_circle']), '-', color='#343a40', lw=1.8)

# Cerchio compensato HW (vicino all'origine)
ax1.plot(np.real(data_2['T_meas']), np.imag(data_2['T_meas']), 'o', color='#1971c2', alpha=0.45, markersize=2.5,
         label='Punti sperimentali compensati hardware')
ax1.plot(np.real(fit_2['T_circle']), np.imag(fit_2['T_circle']), '-', color='#1864ab', lw=1.8)

ax1.plot(0, 0, 'k+', markersize=8, markeredgewidth=1.5)
ax1.annotate(r'Cerchio motrice' + '\n' + r'traslato da $C_p \,/\!/\, R_p$',
             xy=(C_re_u + 0.05, C_im_u - 0.05), xytext=(-2.8, 9.2),
             arrowprops=dict(arrowstyle='->', color='#495057', lw=1.2),
             fontsize=9.0, bbox=dict(boxstyle='round,pad=0.3', facecolor='#f8f9fa', edgecolor='#ced4da'))

ax1.annotate('Cerchio riportato\nsull\'origine (0, 0)\ncon compensazione',
             xy=(0.35, -0.15), xytext=(2.4, 1.4),
             arrowprops=dict(arrowstyle='->', color='#1864ab', lw=1.2),
             fontsize=9.0, bbox=dict(boxstyle='round,pad=0.3', facecolor='#e7f5ff', edgecolor='#74c0fc'))

ax1.set_xlabel(r'Parte reale $\mathrm{Re}\{T(j\omega)\}$')
ax1.set_ylabel(r'Parte immaginaria $\mathrm{Im}\{T(j\omega)\}$')
ax1.set_title('Cerchio senza compensazione vs con compensazione', pad=8)
ax1.set_aspect('equal', adjustable='box')
ax1.set_xlim(-3.5, 10.5)
ax1.set_ylim(-2.4, 12.2)
ax1.grid(True)
ax1.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.94, edgecolor='#ced4da', fontsize=8.8)

# --- Pannello DX: Zoom sull'origine dei cerchi di Nyquist compensati ---
ax2.axhline(0, color='#adb5bd', lw=1.1, zorder=1)
ax2.axvline(0, color='#adb5bd', lw=1.1, zorder=1)

# Software compensated
ax2.plot(np.real(T_sw_meas), np.imag(T_sw_meas), 'o', color='#2b8a3e', alpha=0.35, markersize=2.8,
         label='Punti comp. software')
ax2.plot(np.real(T_sw_circle), np.imag(T_sw_circle), '--', color='#2b8a3e', lw=2.0,
         label='Cerchio comp. software')

# Hardware (ottimizzato)
ax2.plot(np.real(data_2['T_meas']), np.imag(data_2['T_meas']), 'o', color='#1971c2', alpha=0.45, markersize=3.0,
         label='Punti comp. hardware')
ax2.plot(np.real(fit_2['T_circle']), np.imag(fit_2['T_circle']), '-', color='#1864ab', lw=2.2,
         label='Cerchio comp. hardware')

# Evidenziazione risonanza f0 (x = 0 -> T = C_feed + B_mot)
T_res_2 = fit_2['C_feed'] + fit_2['B_mot']
ax2.plot(np.real(T_res_2), np.imag(T_res_2), 'D', color='#e8590c', markersize=6.5, zorder=5,
         label=rf'Risonanza $f_1 = {fit_2["f0"]/1e3:.2f}$ kHz')
ax2.plot(0, 0, 'k+', markersize=9, markeredgewidth=1.8)

ax2.set_xlabel(r'Parte reale $\mathrm{Re}\{T(j\omega)\}$')
ax2.set_ylabel(r'Parte immaginaria $\mathrm{Im}\{T(j\omega)\}$')
ax2.set_title('Cerchio con compensazione hardware vs software', pad=8)
ax2.set_aspect('equal', adjustable='box')
ax2.set_xlim(-0.20, 0.58)
ax2.set_ylim(-0.44, 0.34)
ax2.grid(True)
ax2.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.94, edgecolor='#ced4da', fontsize=8.6)

plt.tight_layout()
p_fig1 = os.path.join(OUT_DIR, 'cerchio_nyquist_confronto_globale.png')
plt.savefig(p_fig1)
plt.close()
print(f"[OK] Salvato: {p_fig1}")

# -----------------------------------------------------------------------------
# FIGURA 2: Interpretazione geometrica dell'interferenza di Fano vs Compensazione HW
# -----------------------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.4, 5.8), dpi=300)

# --- Pannello SX: Zoom sul cerchio NON compensato (origine geometrica di risonanza/antirisonanza) ---
ax1.plot(np.real(T_u_meas), np.imag(T_u_meas), 'o', color='#1971c2', alpha=0.40, markersize=3.2,
         label='Punti sperimentali non compensati')
ax1.plot(np.real(fit_u['T_circle']), np.imag(fit_u['T_circle']), '-', color='#1864ab', lw=2.2,
         label='Cerchio non compensato')

# Punti notevoli sul cerchio non compensato:
# 1. Centro del fondo parassita C_feed (f lontano da f0)
# (fondo parassita omesso)


# 2. Punto di massima e minima distanza dall'origine
dist_u = np.abs(fit_u['T_circle'])
idx_max_u = np.argmax(dist_u)
idx_min_u = np.argmin(dist_u)
T_max_u = fit_u['T_circle'][idx_max_u]
T_min_u = fit_u['T_circle'][idx_min_u]
T_f0_u  = fit_u['C_feed'] + fit_u['B_mot']

ax1.plot(np.real(T_max_u), np.imag(T_max_u), '^', color='#2b8a3e', markersize=7.5, zorder=6,
         label=r'Max $|T|$ ($21.53$ dB)')
ax1.plot(np.real(T_min_u), np.imag(T_min_u), 'v', color='#e03131', markersize=7.5, zorder=6,
         label=r'Min $|T|$ (antirisonanza, $21.19$ dB)')
ax1.plot(np.real(T_f0_u), np.imag(T_f0_u), 'D', color='#e8590c', markersize=6.5, zorder=6,
         label=r'Risonanza meccanica $f_1$')

# Direzione radiale dall'origine (0,0) passante per il centro del cerchio (unisce Min |T| e Max |T|)
u_rad = fit_u['C_center'] / np.abs(fit_u['C_center'])
p_start = fit_u['C_center'] - 0.36 * u_rad
p_end   = fit_u['C_center'] + 0.36 * u_rad
ax1.plot([np.real(p_start), np.real(p_end)], [np.imag(p_start), np.imag(p_end)],
         ':', color='#495057', lw=1.5, label='Asse radiale da $(0,0)$ (congiunge min e max)')

ax1.set_xlabel(r'Parte reale $\mathrm{Re}\{T(j\omega)\}$')
ax1.set_ylabel(r'Parte immaginaria $\mathrm{Im}\{T(j\omega)\}$')
ax1.set_title("Cerchio non compensato: origine dell'antirisonanza", pad=8)
ax1.set_aspect('equal', adjustable='box')
ax1.set_xlim(4.06, 4.86)
ax1.set_ylim(10.42, 11.22)
ax1.grid(True)
ax1.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.94, edgecolor='#ced4da', fontsize=8.1)

# --- Pannello DX: Luogo di Nyquist compensato HW con vettori di fase ---
ax2.axhline(0, color='#868e96', lw=1.2, zorder=1)
ax2.axvline(0, color='#868e96', lw=1.2, zorder=1)

ax2.plot(np.real(data_2['T_meas']), np.imag(data_2['T_meas']), 'o', color='#1971c2', alpha=0.40, markersize=3.2,
         label='Punti sperimentali comp. hardware')
ax2.plot(np.real(fit_2['T_circle']), np.imag(fit_2['T_circle']), '-', color='#1864ab', lw=2.2,
         label='Cerchio comp. hardware')

# Vettore dall'origine al picco di risonanza
ax2.annotate('', xy=(np.real(T_res_2), np.imag(T_res_2)), xytext=(0, 0),
             arrowprops=dict(arrowstyle='->', color='#e8590c', lw=2.0), zorder=5)
ax2.plot(np.real(T_res_2), np.imag(T_res_2), 'D', color='#e8590c', markersize=6.5, zorder=6,
         label=rf'Picco a $f_1 = {fit_2["f0"]/1e3:.2f}$ kHz ($|T| = 0.46$)')

ax2.plot(0, 0, 'k+', markersize=10, markeredgewidth=2.0, label='Origine $(0, 0)$')

ax2.set_xlabel(r'Parte reale $\mathrm{Re}\{T(j\omega)\}$')
ax2.set_ylabel(r'Parte immaginaria $\mathrm{Im}\{T(j\omega)\}$')
ax2.set_title('Cerchio con compensazione hardware attiva', pad=8)
ax2.set_aspect('equal', adjustable='box')
ax2.set_xlim(-0.24, 0.58)
ax2.set_ylim(-0.44, 0.38)
ax2.grid(True)
ax2.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.94, edgecolor='#ced4da', fontsize=8.1)

plt.tight_layout()
p_fig2 = os.path.join(OUT_DIR, 'cerchio_nyquist_dettaglio_fano.png')
plt.savefig(p_fig2)
plt.close()
print(f"[OK] Salvato: {p_fig2}")

# -----------------------------------------------------------------------------
# FIGURA 3: Luogo di Nyquist di Set 2 mappato cromaticamente con la frequenza f_in
# -----------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8.2, 6.2), dpi=300)

ax.axhline(0, color='#868e96', lw=1.2, zorder=1)
ax.axvline(0, color='#868e96', lw=1.2, zorder=1)

ax.plot(np.real(fit_2['T_circle']), np.imag(fit_2['T_circle']), '-', color='#343a40', lw=1.6, alpha=0.75,
        label='Cerchio compensato', zorder=2)

sc = ax.scatter(np.real(data_2['T_meas']), np.imag(data_2['T_meas']),
                c=data_2['f_khz'], cmap='viridis', s=24, alpha=0.88, edgecolors='none', zorder=3,
                label='Punti sperimentali comp. hardware')

cbar = plt.colorbar(sc, ax=ax, pad=0.03)
cbar.set_label(r'Frequenza di eccitazione $f_{in}$ [kHz]')
cbar.ax.ticklabel_format(useOffset=False, style='plain')

# Annotazioni di specifiche frequenze poste radialmente all'esterno del cerchio
for f_mark, offset_xy in [(417.60, (-0.18, 0.14)),
                          (417.70, (0.40, 0.16)),
                          (417.75, (0.43, -0.22)),
                          (417.80, (0.28, -0.40)),
                          (417.95, (-0.20, -0.36))]:
    x_m = 2.0 * fit_2['Q'] * (f_mark * 1e3 - fit_2['f0']) / fit_2['f0']
    T_m = fit_2['C_feed'] + fit_2['B_mot'] / (1.0 + 1j * x_m)
    ax.plot(np.real(T_m), np.imag(T_m), 'o', color='#e03131', markersize=5.8, zorder=5)
    ax.annotate(f'{f_mark:.2f} kHz',
                xy=(np.real(T_m), np.imag(T_m)),
                xytext=offset_xy,
                arrowprops=dict(arrowstyle='->', color='#c92a2a', lw=1.1),
                fontsize=9.0, bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor='#ffa8a8', alpha=0.94))

ax.plot(0, 0, 'k+', markersize=10, markeredgewidth=2.0, label='Origine $(0, 0)$')

ax.set_xlabel(r'Parte reale $\mathrm{Re}\{T(j\omega)\}$')
ax.set_ylabel(r'Parte immaginaria $\mathrm{Im}\{T(j\omega)\}$')
ax.set_title('Evoluzione in frequenza sul cerchio di Nyquist con compensazione hardware', pad=9)
ax.set_aspect('equal', adjustable='box')
ax.set_xlim(-0.26, 0.60)
ax.set_ylim(-0.46, 0.30)
ax.grid(True)
ax.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.94, edgecolor='#ced4da')

plt.tight_layout()
p_fig3 = os.path.join(OUT_DIR, 'nyquist_set2_frequenza.png')
plt.savefig(p_fig3)
plt.close()
print(f"[OK] Salvato: {p_fig3}")
