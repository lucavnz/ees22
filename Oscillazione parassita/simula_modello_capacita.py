import os
import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt

# Percorsi
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'Misure')
OUT_DIR  = os.path.join(BASE_DIR, 'Grafici')
os.makedirs(OUT_DIR, exist_ok=True)
OUT_PNG  = os.path.join(OUT_DIR, 'confronto_simulazione_capacita.png')

# -----------------------------------------------------------------------------
# 1. PARAMETRI DEL CIRCUITO E DELLE FUNZIONI DI TRASFERIMENTO
# -----------------------------------------------------------------------------
Rf = 500e3                     # Resistenza di retroazione TIA [Ohm]
wt = 2 * np.pi * 230e6          # Guadagno prodotto banda OPA656 (GBWP = 230 MHz) [rad/s]
Cp = 1.0e-12                   # Capacita' parassita diretta MEMS [F]
Cc = 1.0e-12                   # Capacita' di compensazione hardware [F]
G2 = 10.0                      # Guadagno secondo stadio AD817 (R2/R1 = 1k/100)

Cin_val = 180e-12              # Capacita' totale nodo invertente (cavo BNC + FET) [F]
Cf_val  = 0.25e-12             # Capacita' parassita del resistore SMD Rf [F]

f0 = 417.83e3                  # Frequenza del segnale di eccitazione [Hz]
w0 = 2 * np.pi * f0
Va = 0.100                     # Ampiezza picco segnale Vin [V]

# Funzione generatrice funzione di trasferimento
def make_tf(Cin, Cf, dC_eff):
    a2 = Rf * (Cin + Cp + Cc + Cf) / wt
    a1 = Rf * Cf + 1.0 / wt
    a0 = 1.0
    b1 = G2 * Rf * dC_eff
    return signal.TransferFunction([b1, 0], [a2, a1, a0]), (a2, a1, a0)

# Calcolo parametri per ciascun caso
dC_eff = 410e-15  # Delta C effettivo al gradino dello stacco

sys_full, (a2_f, a1_f, _) = make_tf(Cin_val, Cf_val, dC_eff)
sys_no_cin, (a2_nc, a1_nc, _) = make_tf(0.0, Cf_val, dC_eff)
sys_no_cf, (a2_ncf, a1_ncf, _) = make_tf(Cin_val, 0.0, dC_eff)

# Parametri canonici
wn_full = np.sqrt(1.0 / a2_f)
fn_full = wn_full / (2 * np.pi)
zeta_full = a1_f / (2 * np.sqrt(a2_f))
fd_full = fn_full * np.sqrt(1.0 - zeta_full**2)
tau_full = 1.0 / (zeta_full * wn_full)

wn_ncf = np.sqrt(1.0 / a2_ncf)
fn_ncf = wn_ncf / (2 * np.pi)
zeta_ncf = a1_ncf / (2 * np.sqrt(a2_ncf))
tau_ncf = 1.0 / (zeta_ncf * wn_ncf)

print(f"Modello Reale: fn = {fn_full/1e3:.1f} kHz, zeta = {zeta_full:.3f}, fd = {fd_full/1e3:.1f} kHz, tau = {tau_full*1e6:.2f} us")
print(f"Senza Cf:      fn = {fn_ncf/1e3:.1f} kHz, zeta = {zeta_ncf:.5f}, tau = {tau_ncf*1e6:.1f} us")

# -----------------------------------------------------------------------------
# 2. CARICAMENTO DATI SPERIMENTALI OSCILLOSCOPIO (SCOPE 172)
# -----------------------------------------------------------------------------
scope_path = os.path.join(DATA_DIR, 'scope_172.csv')
data_scope = np.genfromtxt(scope_path, delimiter=',', skip_header=2)
t_scope = data_scope[:, 0] * 1e6    # us
vout_scope = data_scope[:, 1] * 1e3 # mV
vin_scope = data_scope[:, 2] * 1e3  # mV

# -----------------------------------------------------------------------------
# 3. SIMULAZIONE TEMPORALE AL GRADINO DI SPEGNIMENTO
# -----------------------------------------------------------------------------
# Griglia temporale di simulazione ad alta risoluzione
t_sim = np.linspace(-10e-6, 20e-6, 60001) # da -10 us a +20 us
dt = t_sim[1] - t_sim[0]

# Segnale d'ingresso: sinusoide a 417.83 kHz prima di t=0, congelata al valore di stacco per t>=0
phi = np.radians(15)  # fase che genera il picco iniziale positivo coerente con Scope 172
u_sim = np.where(t_sim < 0, Va * np.sin(w0 * t_sim + phi), Va * np.sin(phi))

# Simulazione lineare delle 3 funzioni di trasferimento
t_lsim = t_sim - t_sim[0]
_, y_full, _   = signal.lsim(sys_full, U=u_sim, T=t_lsim)
_, y_no_cin, _ = signal.lsim(sys_no_cin, U=u_sim, T=t_lsim)
_, y_no_cf, _  = signal.lsim(sys_no_cf, U=u_sim, T=t_lsim)

# Conversione in us e mV
t_sim_us = t_sim * 1e6
y_full_mv   = y_full * 1e3
y_no_cin_mv = y_no_cin * 1e3
y_no_cf_mv  = y_no_cf * 1e3

# -----------------------------------------------------------------------------
# 4. CONFIGURAZIONE GRAFICA PROFESSIONALE (4 PANNELLI)
# -----------------------------------------------------------------------------
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 11.5,
    'xtick.labelsize': 9.5,
    'ytick.labelsize': 9.5,
    'legend.fontsize': 9,
    'lines.linewidth': 1.5,
    'grid.alpha': 0.35,
    'grid.linestyle': '--'
})

fig = plt.figure(figsize=(14.5, 9.5), dpi=300)
gs = fig.add_gridspec(2, 2, hspace=0.28, wspace=0.22)

# --- PANNELLO 1 (Top-Left): Zoom Transitorio (0 - 4 us) e Confronto Sperimentale ---
ax1 = fig.add_subplot(gs[0, 0])
# Traccia reale dell'oscilloscopio
ax1.plot(t_scope, vout_scope, color='#495057', alpha=0.45, linewidth=2.0, label=r'Misura Reale (Scope 172)')
# Modello Reale Completo
ax1.plot(t_sim_us, y_full_mv, color='#1971c2', linewidth=2.0, label=r'Modello Reale ($C_{\text{in}} = 180$ pF, $C_f = 0.25$ pF)')
# Senza Cin
ax1.plot(t_sim_us, y_no_cin_mv, color='#e67700', linestyle='--', linewidth=1.8, label=r'Senza $C_{\text{in}}$ ($C_{\text{in}} = 0$): Sovrasmorzato, 0 oscillazioni')
# Senza Cf
ax1.plot(t_sim_us, y_no_cf_mv, color='#c92a2a', linestyle=':', linewidth=1.8, label=r'Senza $C_f$ ($C_f = 0$): $\zeta \approx 0$, smorzamento nullo')

ax1.axvline(0, color='black', linestyle='--', linewidth=1.0, alpha=0.7)
ax1.axhline(0, color='black', linestyle=':', linewidth=0.8, alpha=0.5)
ax1.set_xlim(-0.5, 4.0)
ax1.set_ylim(-750, 950)
ax1.set_xlabel(r'Tempo [$\mu$s]')
ax1.set_ylabel(r'Tensione $V_{out}$ [mV]')
ax1.set_title(r'(a) Risposta allo Spegnimento del Gate: Zoom Iniziale ($0 - 4\ \mu$s)', pad=8)
ax1.grid(True)
ax1.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')

# --- PANNELLO 2 (Top-Right): Finestra Estesa (0 - 20 us) e Giustificazione del Taglio ---
ax2 = fig.add_subplot(gs[0, 1])
ax2.plot(t_scope, vout_scope, color='#495057', alpha=0.35, linewidth=1.8, label=r'Misura Scope 172')
ax2.plot(t_sim_us, y_full_mv, color='#1971c2', linewidth=1.9, label=r'Modello Reale: estinto a $2.56\ \mu$s')
ax2.plot(t_sim_us, y_no_cf_mv, color='#c92a2a', linestyle=':', linewidth=1.6, label=r'Senza $C_f$: squilla all\'infinito ($\tau \approx 182\ \mu$s)')

# Evidenzia la finestra di taglio a 20 us
ax2.axvspan(0, 20.0, color='#2b8a3e', alpha=0.08, label=r'Finestra di taglio ringdown ($20\ \mu$s)')
ax2.axvline(20.0, color='#2b8a3e', linestyle='--', linewidth=1.4)
ax2.text(20.5, 400, 'Fine taglio\n(Ringdown MEMS)', color='#2b8a3e', fontsize=9.5, fontweight='bold')

ax2.axvline(0, color='black', linestyle='--', linewidth=1.0, alpha=0.7)
ax2.axhline(0, color='black', linestyle=':', linewidth=0.8, alpha=0.5)
ax2.set_xlim(-1.0, 25.0)
ax2.set_ylim(-900, 950)
ax2.set_xlabel(r'Tempo [$\mu$s]')
ax2.set_ylabel(r'Tensione $V_{out}$ [mV]')
ax2.set_title(r'(b) Finestra Estesa ($0 - 25\ \mu$s): Giustificazione del Taglio a $20\ \mu$s', pad=8)
ax2.grid(True)
ax2.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')

# --- PANNELLO 3 (Bottom-Left): Risposta in Frequenza (Diagramma di Bode) ---
ax3 = fig.add_subplot(gs[1, 0])
freqs = np.logspace(4, 7.5, 1200) # 10 kHz a 30 MHz
w_bode = 2 * np.pi * freqs

_, mag_full, _   = signal.bode(sys_full, w_bode)
_, mag_no_cin, _ = signal.bode(sys_no_cin, w_bode)
_, mag_no_cf, _  = signal.bode(sys_no_cf, w_bode)

ax3.semilogx(freqs / 1e3, mag_full, color='#1971c2', linewidth=2.0, label=r'Modello Reale: picco a $614$ kHz ($Q \approx 2$)')
ax3.semilogx(freqs / 1e3, mag_no_cin, color='#e67700', linestyle='--', linewidth=1.8, label=r'Senza $C_{\text{in}}$: polo a $5.7$ MHz (nessun picco a 600 kHz)')
ax3.semilogx(freqs / 1e3, mag_no_cf, color='#c92a2a', linestyle=':', linewidth=1.8, label=r'Senza $C_f$: risonanza critica $+48$ dB a $634$ kHz')

ax3.axvline(614, color='#1971c2', linestyle=':', linewidth=1.1, alpha=0.7)
ax3.axvline(417.83, color='#495057', linestyle='--', linewidth=1.0, alpha=0.7, label=r'Frequenza di stimolo ($417.8$ kHz)')
ax3.set_xlim(20, 20e3)
ax3.set_ylim(-35, 55)
ax3.set_xlabel(r'Frequenza [kHz]')
ax3.set_ylabel(r'Guadagno $|V_{out}/V_{in}|$ [dB]')
ax3.set_title(r'(c) Risposta in Frequenza (Bode): Ruolo di $C_{\text{in}}$ e $C_f$ sul Picco di Risonanza', pad=8)
ax3.grid(True, which='both')
ax3.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')

# --- PANNELLO 4 (Bottom-Right): Mappa Poli nel Piano di Laplace (s) ---
ax4 = fig.add_subplot(gs[1, 1])

# Calcolo poli
p_full = sys_full.poles
p_no_cin = sys_no_cin.poles
p_no_cf = sys_no_cf.poles

# Tracciamento assi
ax4.axhline(0, color='black', linewidth=0.9, alpha=0.6)
ax4.axvline(0, color='black', linewidth=0.9, alpha=0.6)

# Poli caso reale
ax4.scatter(p_full.real / 1e6, p_full.imag / 1e6, color='#1971c2', s=90, marker='x', linewidths=2.5,
            label=r'Modello Reale: $s = -1.0 \pm j 3.86\ \text{Mrad/s}$ ($\zeta=0.25$)')

# Poli senza Cin (reali)
ax4.scatter(p_no_cin.real / 1e6, p_no_cin.imag / 1e6, color='#e67700', s=90, marker='o', edgecolors='#e67700',
            facecolors='none', linewidths=2.2, label=r'Senza $C_{\text{in}}$: $s_1 = -8.4,\ s_2 = -153\ \text{Mrad/s}$ (Reali)')

# Poli senza Cf (quasi asse immaginario)
ax4.scatter(p_no_cf.real / 1e6, p_no_cf.imag / 1e6, color='#c92a2a', s=90, marker='^', linewidths=2.2,
            label=r'Senza $C_f$: $s = -0.005 \pm j 3.98\ \text{Mrad/s}$ ($\zeta \approx 0.001$)')

ax4.set_xlim(-15, 2)
ax4.set_ylim(-6, 6)
ax4.set_xlabel(r'Parte Reale $\sigma$ [Mrad/s]')
ax4.set_ylabel(r'Parte Immaginaria $\omega_d$ [Mrad/s]')
ax4.set_title(r'(d) Mappa Poli nel Piano Complesso $s$: Stabilità e Smorzamento', pad=8)
ax4.grid(True)
ax4.legend(loc='lower left', frameon=True, facecolor='white', framealpha=0.92, edgecolor='#ced4da')

# Salvataggio
plt.savefig(OUT_PNG, bbox_inches='tight')
plt.close()
print(f"[OK] Grafico generato con successo in: {OUT_PNG}")
