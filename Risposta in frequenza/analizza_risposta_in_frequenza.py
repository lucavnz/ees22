"""
Analisi della Risposta in Frequenza e Compensazione Software di Cp del MEMS

Questo script:
1. Carica i dati di sweep in frequenza (modulo e fase) a Vdc = 5.0 V, limitando l'asse a 418.0 kHz.
2. Esegue il fit del modello elettromeccanico RLC con capacita parassita di feedthrough Cp in parallelo.
3. Analizza le misure nel dominio del tempo a Vdc = 0 V (scope_69 e scope_70) a 50 kHz e 417.8 kHz,
   ricavando la capacita parassita Cp direttamente dalla relazione I = j*w*Cp*Vin.
4. Esegue la COMPENSAZIONE SOFTWARE di Cp sottraendo il feedthrough dalla risposta misurata per isolare
   il puro picco di risonanza motrice meccanico.
5. Genera tutti i grafici ad alta risoluzione in stile minimale con punti sperimentali semitrasparenti
   e curva di fit continuo al 100% di opacita, rigorosamente in sentence case e senza grassetto.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# -----------------------------------------------------------------------------
# 1. Configurazione percorsi e parametri del circuito
# -----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'frequenza')
OUT_DIR  = os.path.join(BASE_DIR, 'grafici')
os.makedirs(OUT_DIR, exist_ok=True)

FILE_MODULO = os.path.join(DATA_DIR, 'modulo_VDC_05p0V_417820Hz_501pt_20260916_171901.csv')
FILE_FASE   = os.path.join(DATA_DIR, 'fase_VDC_05p0V_417820Hz_501pt_20260916_171901.csv')
FILE_S69    = os.path.join(DATA_DIR, 'scope_69.csv')
FILE_S70    = os.path.join(DATA_DIR, 'scope_70.csv')

# Parametri front-end di misura
Rf = 500e3         # Resistenza di retroazione TIA [Ohm]
G2 = 10.0          # Guadagno stadio invertente (R2/R1 = 1k / 100)
G_tot = Rf * G2    # Guadagno totale di transimpedenza = 5.0e6 V/A

# -----------------------------------------------------------------------------
# 2. Caricamento sweep in frequenza e taglio a 418.0 kHz
# -----------------------------------------------------------------------------
raw_mod  = np.loadtxt(FILE_MODULO, delimiter=',', skiprows=2)
raw_fase = np.loadtxt(FILE_FASE, delimiter=',', skiprows=2)

f_all_hz   = raw_mod[:, 0]
f_all_khz  = f_all_hz / 1e3
gain_lin_all = raw_mod[:, 3]
gain_db_all  = raw_mod[:, 4]
phase_deg_all = raw_fase[:, 1]

# Filtro: taglia a destra fino a 418.0 kHz come richiesto
mask = f_all_khz <= 418.0
f_hz      = f_all_hz[mask]
f_khz     = f_all_khz[mask]
gain_lin  = gain_lin_all[mask]
gain_db   = gain_db_all[mask]
phase_deg = phase_deg_all[mask]
phase_rad = np.deg2rad(phase_deg)

# -----------------------------------------------------------------------------
# 3. Fit del modello teorico RLC + Cp sullo sweep a Vdc = 5.0 V
# -----------------------------------------------------------------------------
# T(f) = (C_re + j*C_im) + (A_mot * e^(j*phi_m)) / (1 + 2j * Q * (f - f0) / f0)
def model_real_imag(f_arr, C_re, C_im, A_mot, f0, Q, phi_m):
    x = 2.0 * Q * (f_arr - f0) / f0
    mot = (A_mot * np.exp(1j * phi_m)) / (1.0 + 1j * x)
    T = (C_re + 1j * C_im) + mot
    return np.concatenate([np.real(T), np.imag(T)])

T_meas = gain_lin * np.exp(1j * phase_rad)
y_meas = np.concatenate([np.real(T_meas), np.imag(T_meas)])

p0 = [4.27, 10.90, 0.46, 417640.0, 3000.0, -0.4]
popt, _ = curve_fit(
    lambda f_arr, *p: model_real_imag(f_arr, *p),
    f_hz, y_meas, p0=p0, maxfev=10000
)
C_re, C_im, A_mot, f0_fit, Q_fit, phi_m = popt

# Capacita parassita stimata dal fit dello sweep
C_feed_mag = np.hypot(C_re, C_im)
Cp_fit_pF  = (C_feed_mag / (2.0 * np.pi * f0_fit * G_tot)) * 1e12

# Griglia densa per la curva di fit continuo
f_dense = np.linspace(f_hz[0], 418.0e3, 1000)
f_dense_khz = f_dense / 1e3
x_dense = 2.0 * Q_fit * (f_dense - f0_fit) / f0_fit
T_fit_dense = (C_re + 1j * C_im) + (A_mot * np.exp(1j * phi_m)) / (1.0 + 1j * x_dense)
gain_fit_db_dense = 20.0 * np.log10(np.abs(T_fit_dense))
phase_fit_deg_dense = np.rad2deg(np.angle(T_fit_dense))

# -----------------------------------------------------------------------------
# 4. Analisi oscilloscopio a Vdc = 0 V (Scope 69 e Scope 70)
# -----------------------------------------------------------------------------
def fit_sine_wave(t, y, f_guess):
    def sine_fn(t, A, f, phi, off):
        return A * np.sin(2.0 * np.pi * f * t + phi) + off
    p, _ = curve_fit(sine_fn, t, y, p0=[np.ptp(y) / 2.0, f_guess, 0.0, np.mean(y)])
    return abs(p[0]), abs(p[1]), p[2], p[3]

# Scope 70: bassa frequenza (50 kHz)
d70 = np.genfromtxt(FILE_S70, delimiter=',', skip_header=2)
t70 = d70[:, 0]
v_out_70 = d70[:, 1]
v_in_70  = d70[:, 3]

A_in_70, f70, phi_in_70, off_in_70   = fit_sine_wave(t70, v_in_70, 50.0e3)
A_out_70, _, phi_out_70, off_out_70  = fit_sine_wave(t70, v_out_70, 50.0e3)
gain_70 = A_out_70 / A_in_70
Cp_70_pF = (gain_70 / (2.0 * np.pi * f70 * G_tot)) * 1e12

# Scope 69: vicino alla risonanza (417.8 kHz)
d69 = np.genfromtxt(FILE_S69, delimiter=',', skip_header=2)
t69 = d69[:, 0]
v_out_69 = d69[:, 1]
v_in_69  = d69[:, 3]

A_in_69, f69, phi_in_69, off_in_69   = fit_sine_wave(t69, v_in_69, 417.8e3)
A_out_69, _, phi_out_69, off_out_69  = fit_sine_wave(t69, v_out_69, 417.8e3)
gain_69 = A_out_69 / A_in_69
Cp_69_pF = (gain_69 / (2.0 * np.pi * f69 * G_tot)) * 1e12

print("=" * 65)
print("STIMA DELLA CAPACITA PARASSITA Cp DA TRE METODI INDIPENDENTI:")
print(f"1. Scope 70 (f = {f70/1e3:.2f} kHz, Vdc = 0 V):")
print(f"   Vin = {A_in_70*1e3:.2f} mV, Vout = {A_out_70*1e3:.2f} mV -> Cp = {Cp_70_pF:.3f} pF")
print(f"2. Scope 69 (f = {f69/1e3:.2f} kHz, Vdc = 0 V):")
print(f"   Vin = {A_in_69*1e3:.2f} mV, Vout = {A_out_69:.3f} V  -> Cp = {Cp_69_pF:.3f} pF")
print(f"3. Fit dello sweep in frequenza (Vdc = 5.0 V):")
print(f"   Base feedthrough |C_feed| = {C_feed_mag:.3f} -> Cp = {Cp_fit_pF:.3f} pF")
print(f"   Frequenza di risonanza motrice f0: {f0_fit:.2f} Hz, Q: {Q_fit:.1f}")
print("=" * 65)

# -----------------------------------------------------------------------------
# 5. COMPENSAZIONE SOFTWARE DI Cp
# -----------------------------------------------------------------------------
# Sottraiamo il contributo complesso di feedthrough C_feed dalla misura sperimentale:
T_cp = C_re + 1j * C_im
T_comp_meas = T_meas - T_cp

# Curva teorica del solo ramo motrice
T_comp_fit_dense = (A_mot * np.exp(1j * phi_m)) / (1.0 + 1j * x_dense)

# Allineamento di fase: rotazione per porre la risonanza motrice a 0 gradi
T_comp_meas_aligned = T_comp_meas * np.exp(-1j * phi_m)
T_comp_fit_aligned  = T_comp_fit_dense * np.exp(-1j * phi_m)

gain_comp_meas_lin = np.abs(T_comp_meas)
gain_comp_fit_lin  = np.abs(T_comp_fit_dense)
phase_comp_meas_deg = np.rad2deg(np.angle(T_comp_meas_aligned))
phase_comp_fit_deg  = np.rad2deg(np.angle(T_comp_fit_aligned))

# -----------------------------------------------------------------------------
# 6. Stile tipografico (nessun grassetto, solo sentence case)
# -----------------------------------------------------------------------------
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.labelsize': 11.5,
    'axes.titlesize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'grid.alpha': 0.35,
    'grid.linestyle': '--'
})

COLOR_MOD  = '#1971c2'  # Blu
COLOR_FASE = '#e8590c'  # Arancione/Corallo

# -----------------------------------------------------------------------------
# GRAFICO 1: Bode completo (modulo + fase) fino a 418.0 kHz
# -----------------------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.8, 7.0), sharex=True, dpi=300)

ax1.plot(f_khz, gain_db, 'o', color=COLOR_MOD, alpha=0.45, markersize=3.2, label='Punti sperimentali')
ax1.plot(f_dense_khz, gain_fit_db_dense, color=COLOR_MOD, linewidth=2.0, alpha=1.0, label=r'Fit modello (RLC + $C_p$)')
ax1.set_ylabel('Guadagno [dB]')
ax1.set_title(r'Risposta in frequenza del MEMS ($V_{dc} = 5.0$ V)', pad=9)
ax1.grid(True)
ax1.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
ax1.ticklabel_format(useOffset=False, style='plain')
ax1.set_xlim(f_khz[0], 418.0)

ax2.plot(f_khz, phase_deg, 'o', color=COLOR_FASE, alpha=0.45, markersize=3.2, label='Punti sperimentali')
ax2.plot(f_dense_khz, phase_fit_deg_dense, color=COLOR_FASE, linewidth=2.0, alpha=1.0, label=r'Fit modello (RLC + $C_p$)')
ax2.set_xlabel(r'Frequenza $f_{in}$ [kHz]')
ax2.set_ylabel('Fase [°]')
ax2.grid(True)
ax2.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
ax2.ticklabel_format(useOffset=False, style='plain')
ax2.set_xlim(f_khz[0], 418.0)

plt.tight_layout()
p1 = os.path.join(OUT_DIR, 'bode_completo.png')
plt.savefig(p1)
plt.close()
print(f"[OK] Grafico 1 salvato: {p1}")

# -----------------------------------------------------------------------------
# GRAFICO 2: Modulo singolo fino a 418.0 kHz
# -----------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8.8, 5.5), dpi=300)
ax.plot(f_khz, gain_db, 'o', color=COLOR_MOD, alpha=0.45, markersize=3.2, label='Punti sperimentali')
ax.plot(f_dense_khz, gain_fit_db_dense, color=COLOR_MOD, linewidth=2.0, alpha=1.0, label=r'Fit modello (RLC + $C_p$)')
ax.set_xlabel(r'Frequenza $f_{in}$ [kHz]')
ax.set_ylabel('Guadagno [dB]')
ax.set_title(r'Modulo della risposta in frequenza ($V_{dc} = 5.0$ V)', pad=9)
ax.grid(True)
ax.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
ax.ticklabel_format(useOffset=False, style='plain')
ax.set_xlim(f_khz[0], 418.0)
plt.tight_layout()
p2 = os.path.join(OUT_DIR, 'bode_modulo.png')
plt.savefig(p2)
plt.close()
print(f"[OK] Grafico 2 salvato: {p2}")

# -----------------------------------------------------------------------------
# GRAFICO 3: Fase singola fino a 418.0 kHz
# -----------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8.8, 5.5), dpi=300)
ax.plot(f_khz, phase_deg, 'o', color=COLOR_FASE, alpha=0.45, markersize=3.2, label='Punti sperimentali')
ax.plot(f_dense_khz, phase_fit_deg_dense, color=COLOR_FASE, linewidth=2.0, alpha=1.0, label=r'Fit modello (RLC + $C_p$)')
ax.set_xlabel(r'Frequenza $f_{in}$ [kHz]')
ax.set_ylabel('Fase [°]')
ax.set_title(r'Fase della risposta in frequenza ($V_{dc} = 5.0$ V)', pad=9)
ax.grid(True)
ax.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
ax.ticklabel_format(useOffset=False, style='plain')
ax.set_xlim(f_khz[0], 418.0)
plt.tight_layout()
p3 = os.path.join(OUT_DIR, 'bode_fase.png')
plt.savefig(p3)
plt.close()
print(f"[OK] Grafico 3 salvato: {p3}")

# -----------------------------------------------------------------------------
# GRAFICO 4: Bode del solo ramo compensato (puro picco motrice meccanico)
# -----------------------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.8, 7.0), sharex=True, dpi=300)

ax1.plot(f_khz, gain_comp_meas_lin, 'o', color='#2b8a3e', alpha=0.45, markersize=3.2, label='Punti sperimentali compensati')
ax1.plot(f_dense_khz, gain_comp_fit_lin, color='#2b8a3e', linewidth=2.0, alpha=1.0, label='Fit')
ax1.set_ylabel(r'Guadagno $|V_{out} / V_{in}|$')
ax1.set_title(r'Risposta in frequenza compensata software ($V_{dc} = 5.0$ V)', pad=9)
ax1.grid(True)
ax1.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
ax1.ticklabel_format(useOffset=False, style='plain')
ax1.set_xlim(f_khz[0], 418.0)

ax2.plot(f_khz, phase_comp_meas_deg, 'o', color='#7048e8', alpha=0.45, markersize=3.2, label='Punti sperimentali compensati')
ax2.plot(f_dense_khz, phase_comp_fit_deg, color='#7048e8', linewidth=2.0, alpha=1.0, label='Fit')
ax2.set_xlabel(r'Frequenza $f_{in}$ [kHz]')
ax2.set_ylabel('Fase [°]')
ax2.grid(True)
ax2.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
ax2.ticklabel_format(useOffset=False, style='plain')
ax2.set_xlim(f_khz[0], 418.0)

plt.tight_layout()
p4 = os.path.join(OUT_DIR, 'bode_compensato.png')
plt.savefig(p4)
plt.close()
print(f"[OK] Grafico 4 salvato: {p4}")

# -----------------------------------------------------------------------------
# GRAFICO 5: Confronto prima e dopo la compensazione software
# -----------------------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.8, 7.0), sharex=True, dpi=300)

# Modulo
ax1.plot(f_khz, gain_lin, 'o', color=COLOR_MOD, alpha=0.35, markersize=2.8, label='Non compensato (misura reale)')
ax1.plot(f_dense_khz, np.abs(T_fit_dense), color=COLOR_MOD, linewidth=1.8, label=r'Modello totale (con $C_p$)')
ax1.plot(f_khz, gain_comp_meas_lin, 'o', color='#2b8a3e', alpha=0.45, markersize=2.8, label=r'Compensato software ($C_p$ rimossa)')
ax1.plot(f_dense_khz, gain_comp_fit_lin, color='#2b8a3e', linewidth=2.0, label='Puro picco motrice')
ax1.set_ylabel('Guadagno $|V_{out} / V_{in}|$')
ax1.set_title(r'Confronto risposta in frequenza: prima e dopo compensazione software di $C_p$', pad=9)
ax1.grid(True)
ax1.legend(loc='center right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
ax1.ticklabel_format(useOffset=False, style='plain')
ax1.set_xlim(f_khz[0], 418.0)

# Fase
ax2.plot(f_khz, phase_deg, 'o', color=COLOR_FASE, alpha=0.35, markersize=2.8, label='Non compensato (misura reale)')
ax2.plot(f_dense_khz, phase_fit_deg_dense, color=COLOR_FASE, linewidth=1.8, label=r'Modello totale (con $C_p$)')
ax2.plot(f_khz, phase_comp_meas_deg, 'o', color='#7048e8', alpha=0.45, markersize=2.8, label=r'Compensato software ($C_p$ rimossa)')
ax2.plot(f_dense_khz, phase_comp_fit_deg, color='#7048e8', linewidth=2.0, label='Transizione di fase motrice')
ax2.set_xlabel(r'Frequenza $f_{in}$ [kHz]')
ax2.set_ylabel('Fase [°]')
ax2.grid(True)
ax2.legend(loc='center right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')
ax2.ticklabel_format(useOffset=False, style='plain')
ax2.set_xlim(f_khz[0], 418.0)

plt.tight_layout()
p5 = os.path.join(OUT_DIR, 'bode_confronto_compensazione.png')
plt.savefig(p5)
plt.close()
print(f"[OK] Grafico 5 salvato: {p5}")

# -----------------------------------------------------------------------------
# GRAFICO 6: Segnali temporali oscilloscopio a Vdc = 0 V (Scope 69 e Scope 70)
# -----------------------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.8), dpi=300)

# Scope 70 (50 kHz): 2 periodi ~ 40 us
t70_us = (t70 - t70[0]) * 1e6
idx70 = t70_us <= 40.0
ax1.plot(t70_us[idx70], v_in_70[idx70] * 1e3, color='#495057', alpha=0.8, linewidth=1.5,
         label=rf'$V_{{in}}$ ($V_{{pk}} = {A_in_70*1e3:.1f}$ mV)')
ax1.plot(t70_us[idx70], v_out_70[idx70] * 1e3, color='#1971c2', linewidth=1.8,
         label=rf'$V_{{out}}$ ($V_{{pk}} = {A_out_70*1e3:.1f}$ mV)')
ax1.set_xlabel(r'Tempo [$\mu$s]')
ax1.set_ylabel('Tensione [mV]')
ax1.set_title(r'Scope 70: $f = 50.0$ kHz ($V_{dc} = 0$ V, $C_p = 0.899$ pF)', pad=9)
ax1.grid(True)
ax1.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')

# Scope 69 (417.8 kHz): 2 periodi ~ 4.8 us
t69_us = (t69 - t69[0]) * 1e6
idx69 = t69_us <= 4.8
ax2.plot(t69_us[idx69], v_in_69[idx69] * 1e3, color='#495057', alpha=0.8, linewidth=1.5,
         label=rf'$V_{{in}}$ ($V_{{pk}} = {A_in_69*1e3:.1f}$ mV)')
ax2.plot(t69_us[idx69], v_out_69[idx69], color='#1971c2', linewidth=1.8,
         label=rf'$V_{{out}}$ ($V_{{pk}} = {A_out_69:.3f}$ V)')
ax2.set_xlabel(r'Tempo [$\mu$s]')
ax2.set_ylabel(r'Tensione: $V_{in}$ [mV] / $V_{out}$ [V]')
ax2.set_title(r'Scope 69: $f = 417.8$ kHz ($V_{dc} = 0$ V, $C_p = 0.921$ pF)', pad=9)
ax2.grid(True)
ax2.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')

plt.tight_layout()
p6 = os.path.join(OUT_DIR, 'scope_stima_cp.png')
plt.savefig(p6)
plt.close()
print(f"[OK] Grafico 6 salvato: {p6}")

print("\nPipeline completata con successo!")
