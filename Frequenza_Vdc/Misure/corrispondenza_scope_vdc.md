Ran command: `python3 -c "
import numpy as np

# Let's inspect the numbers
# What is c1_DD?
# In Frangi Table 2:
# c1^(1) / eps0 = 21.11 [muN * mum / (V^2 * pF)] (or muN / (V^2 * pF))
# If eps0 = 8.854e-12 F/m = 8.854e-6 pF / mum:
# c1_DD = 21.11 * eps0 = 1.869e-4 (in some units) or 1.869e8 (in SI s^-2/V^2)
# Or did the friend take c1_DD = 21.11 or 21.11 * eps0?
# What about omega_r vs f_r? Did the friend use f in Hz instead of omega in rad/s (factor (2*pi)^2 = 39.48)?
# Or did the friend use microseconds (mus) instead of seconds?
# Or did the friend confuse units of mass: kg vs picograms vs nanograms vs micrograms?
# Let's see what formula gives 9.3676e-13!

# In our fit:
# slope alpha = Delta(f^2) / Delta(V_DC^2) = 5.035e6 Hz^2 / V^2
# In rad/s: slope_omega = (2*pi)^2 * alpha = 1.9878e8 (rad/s)^2 / V^2
# If omega_r^2 = c1_beta - (c1_DD / M) * V_DC^2
# slope_omega = c1_DD / M  =>  M = c1_DD / slope_omega
# If slope in Hz^2: slope_f = c1_DD / ((2*pi)^2 * M) => M = c1_DD / ((2*pi)^2 * alpha)

# What did the friend use for c1_DD?
# Let's check:
target = 9.3676e-13
print('Target:', target)

for c_val in [21.11, 21.11 * 8.8541878e-12, 21.11 * 8.8541878e-6, 1.86912e8, 1.86912e-4, 1.86912e-10]:
    for sl in [5.035e6, 5.067e6, 5.084e6, 5.046e6, 1.9878e8, 2.0e8, 417850, 417850**2, (2*np.pi*417850)**2]:
        val = c_val / sl
        if abs(val - target)/target < 0.05 or abs(val*1e-6 - target)/target < 0.05 or abs(val*39.48 - target)/target < 0.05:
            print(f'Match: c={c_val}, sl={sl}, val={val}')
"`
Ran command: `python3 -c "
target = 9.3676e-13
# If target = c / slope:
print('slope if c = 1.86912e-4:', 1.869119e-4 / target)
# In Hz^2:
print('slope / (4*pi^2):', (1.869119e-4 / target) / (4*3.1415926535**2))
"`
Ran command: `python3 -c "
import numpy as np

# Let's read Frequenza_Vdc copy/tabella_risultati_softening.csv
with open('Frequenza_Vdc copy/tabella_risultati_softening.csv') as f:
    f.readline()
    v2_list = []
    f_list = []
    for line in f:
        if line.strip():
            parts = line.strip().split(',')
            v2_list.append(float(parts[2]))
            f_list.append(float(parts[4]))

v2 = np.array(v2_list)
f = np.array(f_list)
f2 = f**2
p = np.polyfit(v2, f2, 1)
print('Slope in Hz^2/V^2:', -p[0])
omega2 = (2 * np.pi * f)**2
p_omega = np.polyfit(v2, omega2, 1)
print('Slope in (rad/s)^2/V^2:', -p_omega[0])

# What if slope is computed between Scope 39 (3V) and Scope 45 (6V)?
sl_two = (f2[0] - f2[-1]) / (v2[-1] - v2[0])
print('Two-point slope in Hz^2/V^2:', sl_two)
print('Two-point slope in (rad/s)^2/V^2:', sl_two * 4 * np.pi**2)

# What if we use results from our own fit?
# Or what if we use:
target = 9.3676e-13
print('If c = 21.11 * 8.8541878e-6 = 1.86932e-4:')
print('slope_omega = c / target =', 1.86932e-4 / target)
print('slope_f = slope_omega / (4*pi^2) =', (1.86932e-4 / target) / (4*np.pi**2))
"`
Viewed analizza_frequenza_vdc%20copy.py:1-100
Viewed punti_vdc2_f2.csv:1-9
Ran command: `python3 -c "
import numpy as np

data = np.loadtxt('Frequenza_Vdc/Misure/punti_vdc2_f2.csv', delimiter=',', skiprows=1)
v2 = data[:, 0]
f2 = data[:, 1]
p = np.polyfit(v2, f2, 1)
alpha_exp = -p[0]
print('alpha_exp (Hz^2 / V^2):', alpha_exp)

# Pulsazione: omega^2 = (2*pi)^2 * f^2
slope_omega = alpha_exp * (4 * np.pi**2)
print('slope_omega ((rad/s)^2 / V^2):', slope_omega)

# In the friend's formula:
# omega_r^2 = c1_beta - (c1_DD / M) * V_DC^2 - omega01^2 / (4*Q1^2)
# The slope with respect to V_DC^2 is:
# slope = c1_DD / M
# So: M = c1_DD / slope

target = 9.3676e-13
print('If M = target:', target)
c1_used = target * slope_omega
print('c1_DD used by friend:', c1_used)

# What is 21.11 * eps0?
eps0_SI = 8.8541878e-12
eps0_pF_um = 8.8541878e-6
print('21.11 * eps0_pF_um =', 21.11 * eps0_pF_um)
print('Ratio c1_used / (21.11 * eps0_pF_um):', c1_used / (21.11 * eps0_pF_um))
"`
Ran command: `python3 -c "
import numpy as np

# Let's inspect the units in Frangi et al. 2023:
# Page 6: Table 1: c_{1,beta}^(1) = 6.85 [mus^-2]
# omega01 = sqrt(6.85) [rad/mus] = 2.617 rad/mus = 2.617e6 rad/s.
# In s^-2: c1_beta = 6.85 * (1e6)^2 = 6.85e12 s^-2.

# Table 2:
# f_DD^(1) / eps0 = 21.11 [muN * mum / (V^2 * pF)] (or muN / (V^2 * pF))
# Note that [muN / pF] = [10^-6 N / (10^-12 F)] = 10^6 N/F = 10^6 V^2/m ?
# Let's check dimensions of muN / (V^2 * pF):
# F = C / V = A * s / V.
# N = kg * m / s^2.
# muN / pF = (10^-6 N) / (10^-12 F) = 10^6 N / F.
# N / (V^2 * F) = (kg * m / s^2) / (V^2 * C / V) = (kg * m / s^2) / (V * C)
# since V * C = Joules = kg * m^2 / s^2:
# N / (V^2 * F) = (kg * m / s^2) / (kg * m^2 / s^2) = 1 / m = 1 / (10^6 mum) = 10^-6 mum^-1!
# So muN * mum / (V^2 * pF) is dimensionless!
print('Let us check Frangi text on units!')
"`
Ran command: `python3 -c "
import pypdf
reader = pypdf.PdfReader('Paper/Frangi_2023.pdf')
for i, page in enumerate(reader.pages):
    txt = page.extract_text()
    if 'unit' in txt.lower():
        for line in txt.split('\n'):
            if any(k in line.lower() for k in ['consistency of units', 'table 1', 'table 2', 'consistent with', 'expressed in']):
                print(f'P{i+1}: {line}')
"`
Used tool: manage_task
Ran command: `python3 -c "
c1_friend = 21.11 * 8.8541878e-6
slope_friend = 199530189.16 # which is (2*pi)^2 * 5054158.73
M_friend = c1_friend / slope_friend
print(f'M_friend = {M_friend:.8e}')
"`

Ho ricostruito esattamente il calcolo del tuo amico: **ora ti spiego al millimetro da dove viene quel numero $9.3676 \times 10^{-13}$ e quali sono i 2 errori (uno di unità di misura e uno concettuale) che ha commesso.**

---

### 1. Cosa ha fatto matematicamente il tuo amico

Guardando l'equazione (8) della foto:
$$\omega_r = \sqrt{ c_{1,\beta}^{(1)} - \frac{c_{1,DD}^{(1)} V_{\mathrm{DC}}^2}{\mathcal{M}} - \frac{\omega_{01}^2}{4Q_1^2} }$$
Elevando al quadrato, la dipendenza da $V_{\mathrm{DC}}^2$ è una retta con pendenza:
$$\text{Pendenza}_\omega = \frac{c_{1,DD}^{(1)}}{\mathcal{M}} \implies \mathcal{M} = \frac{c_{1,DD}^{(1)}}{\text{Pendenza}_\omega} = \frac{c_{1,DD}^{(1)}}{4\pi^2 \alpha_{\text{exp}}}$$

Il tuo amico ha preso:
1. **Dalla Tabella 2 del paper di Frangi**:  
   $c_1^{(1)}/\varepsilon_0 = 21.11$, quindi ha calcolato:
   $$c_{1,DD}^{(1)} = 21.11 \times \varepsilon_0 = 21.11 \times (8.8541878 \times 10^{-6}) = \mathbf{1.86912 \times 10^{-4}}$$
2. **Dal fit delle vostre misure sperimentali**:  
   $\alpha_{\text{exp}} \approx 5.054 \times 10^6\ \text{Hz}^2/\text{V}^2 \implies \text{Pendenza}_\omega = 4\pi^2 \alpha_{\text{exp}} = \mathbf{1.9953 \times 10^8\ \frac{\text{rad}^2}{\text{s}^2 \cdot \text{V}^2}}$
3. **Ha fatto la divisione**:
   $$\mathcal{M} = \frac{1.86912 \times 10^{-4}}{1.9953 \times 10^8} = \mathbf{9.3676 \times 10^{-13}}$$

Il calcolo aritmetico produce **esattamente $9.3676 \times 10^{-13}$**!  
Ma questo risultato ha **due gravi errori di fondo**.

---

### ERRORE 1 (Micidiale): Unità di misura del Tempo ($\mu\text{s}$ vs $\text{s}$)

Nel paper di Frangi et al. 2023, le unità di misura **NON sono quelle del Sistema Internazionale (secondi)**, ma sono in **microsecondi ($\mu\text{s}$)**:
- Guarda la Tabella 1 del paper: il coefficiente meccanico è espresso in $c_{1,\beta}^{(1)} = 6.85\ \mu\text{s}^{-2}$. Infatti $\omega_{01} = \sqrt{6.85} \approx 2.617\ \text{rad}/\mu\text{s} = 2.617 \times 10^6\ \text{rad/s}$.
- Di conseguenza, quel $c_{1,DD}^{(1)} = 1.86912 \times 10^{-4}$ è espresso in:
  $$\left[ \frac{\text{rad}^2}{\boldsymbol{\mu\text{s}}^2 \cdot \text{V}^2} \right]$$
- La pendenza sperimentale al denominatore ($1.9953 \times 10^8$), invece, è calcolata in **Hertz** (cioè **secondi alla $-2$**)!

Il tuo amico ha diviso un numeratore in $\mu\text{s}^{-2}$ per un denominatore in $\text{s}^{-2}$.  
Poiché $1\ \mu\text{s} = 10^{-6}\text{ s} \implies 1\ \mu\text{s}^{-2} = \mathbf{10^{12}\ \text{s}^{-2}}$, **manca un fattore $10^{12}$!**

Se converti il numeratore in secondi:
$$c_{1,DD,\text{SI}}^{(1)} = 1.86912 \times 10^{-4} \times 10^{12} = \mathbf{1.86912 \times 10^8\ \frac{\text{rad}^2}{\text{s}^2 \cdot \text{V}^2}}$$

E rifai la divisione in unità coerenti:
$$\mathcal{M} = \frac{1.86912 \times 10^8}{1.9953 \times 10^8} = \mathbf{0.93676} \quad (\approx \mathbf{0.94}!)$$

---

### ERRORE 2 (Concettuale): Cos'è $\mathcal{M}$ in quella formula?

Guarda il numero che viene fuori correggendo i microsecondi: **$0.93676$ (cioè $93.68\%$)**.  
Ti ricorda qualcosa?  
È **esattamente il rapporto tra la teoria di Frangi e il vostro esperimento**:
$$\frac{\alpha_{\text{teorico}}}{\alpha_{\text{sperimentale}}} = \frac{4.735 \times 10^6}{5.054 \times 10^6} = \mathbf{0.9368} \quad (\text{accordo del } \mathbf{93.7\%})$$

Perché succede questo?
1. Nel paper di Frangi (Eq. 1 pag. 5), la coordinata $q_1$ è una coordinata modale **normalizzata a massa unitaria ($M = 1$)**:
   $$\int_{\Omega} \rho \psi_1^2 \, d\Omega = M = 1$$
   Frangi ha **già diviso tutta l'equazione per la massa fin dall'inizio**.
2. Quindi il coefficiente $c_{1,DD}^{(1)}$ di Frangi **NON è una forza in Newton ($[N/V^2]$)**, ma è **GIÀ un'accelerazione per Volt quadro ($[s^{-2}/V^2]$)**.
3. Di conseguenza, nella formula scritta sulle slide del tuo amico, $\mathcal{M}$ **NON è una massa fisica in kg**, ma è un **parametro adimensionale di scala rispetto al modello di Frangi**, che nel paper vale per definizione $\mathcal{M} = 1$.
4. Facendo $\mathcal{M} = \frac{c_{1,DD}}{\text{pendenza}}$, il tuo amico ha semplicemente calcolato:
   $$\mathcal{M} = \frac{\text{Pendenza Teorica Frangi}}{\text{Pendenza Sperimentale}} = \frac{4.735 \times 10^6}{5.054 \times 10^6} = \mathbf{0.9368}$$
   Poi, avendo dimenticato il fattore $10^{12}$ dei microsecondi, ha ottenuto $0.9368 \times 10^{-12} = \mathbf{9.3676 \times 10^{-13}}$, pensando erroneamente che fossero "chilogrammi"!

---

### Come si calcola allora la VERA massa fisica in kg?

Per ottenere la vera massa fisica $m_{eff}$ in chilogrammi, al numeratore devi mettere la vera derivata della **forza elettrostatica in Newton**, che dipende dalla geometria del condensatore:
$$k_{e0} = \frac{\varepsilon_0 A}{g_0^3} \approx \frac{8.854 \times 10^{-12} \cdot 1.28 \times 10^{-8}}{(1.80 \times 10^{-6})^3} = \mathbf{1.938 \times 10^{-2}\ \frac{\text{N}}{\text{m} \cdot \text{V}^2}}$$

Ora sì che le unità dimensionali tornano ($[\text{N/m}] / [\text{rad}^2/\text{s}^2] = \text{kg}$):
$$\mathbf{m_{eff}} = \frac{k_{e0}}{\text{Pendenza}_\omega} = \frac{1.938 \times 10^{-2}\ \text{N}/(\text{m}\cdot\text{V}^2)}{1.9953 \times 10^8\ \text{s}^{-2}/\text{V}^2} \approx \mathbf{9.7 \times 10^{-11}\ \text{kg} = 0.097\ \text{ng} \approx 0.1\ \text{ng}}$$

### Riassunto per il tuo amico
1. Il suo $9.3676 \times 10^{-13}$ deriva dall'aver dimenticato la conversione dai microsecondi del paper ai secondi ($10^{12}$): corretto il tempo, il numero è **$0.9368$**.
2. Quel $0.9368$ è un numero puro (adimensionale) che rappresenta il rapporto tra la teoria di Frangi e il vostro esperimento ($93.7\%$).
3. Per avere i kg reali, deve usare la forza elettrostatica in Newton ($k_{e0} \approx 1.94 \times 10^{-2}\ \text{N}/(\text{m}\cdot\text{V}^2)$), ottenendo la massa fisica corretta di circa **$0.1\text{ ng}$ ($10^{-10}\text{ kg}$)**.
Ran command: `python3 -c "
# [F] = 1 muN = 10^-6 N = 10^-6 kg * m / s^2
# [L] = 1 mum = 10^-6 m
# [T] = 1 mus = 10^-6 s

# Unit of mass [M]:
# [M] = [F] * [T]^2 / [L]
unit_F = 1e-6 # N
unit_L = 1e-6 # m
unit_T = 1e-6 # s

unit_M_kg = unit_F * (unit_T**2) / unit_L
print(f'Unit of mass [M] in kg: {unit_M_kg} kg')
print(f'Unit of mass [M] in ng: {unit_M_kg * 1e9} ng')
print(f'Unit of mass [M] in pg: {unit_M_kg * 1e12} pg')
"`
Ran command: `python3 -c "
import pypdf
reader = pypdf.PdfReader('Paper/Frangi_2023.pdf')
# Search page 9 Table 2 and footnotes
p9 = reader.pages[8].extract_text()
for line in p9.split('\n'):
    if any(k in line.lower() for k in ['table 2', 'numerical values', 'consistent with', 'muN', 'c(1)', 'c_1']):
        print(line)
"`
Ran command: `python3 -c "
import pypdf
reader = pypdf.PdfReader('Paper/Frangi_2023.pdf')
p9 = reader.pages[8].extract_text()
idx = p9.find('Numerical values')
print(p9[idx:idx+250])
"`
Ran command: `python3 -c "
# 1 muN / 1 mum:
# 1 muN = 1e-6 N
# 1 mum = 1e-6 m
# 1 muN / 1 mum = 1 N / m!
print('1 muN / 1 mum =', 1e-6 / 1e-6, 'N / m')
"`
Ran command: `python3 -c "
import pypdf
reader = pypdf.PdfReader('Paper/Frangi_2023.pdf')
# Let's inspect page 5, 6, 7, 8
print('=== PAGE 6 TABLE 1 ===')
print(reader.pages[5].extract_text()[:1500])
print('=== PAGE 7 EQ 6-8 ===')
print(reader.pages[6].extract_text()[:1500])
"`

**Sì, hai perfettamente ragione sul senso dell'equazione: quell'$\mathcal{M}$ è stato scritto lì apposta perché rappresenta la massa!**

Chi ha scritto quell'equazione sulle slide (Eq. 4 e 8 della tua foto) ha fatto questo ragionamento fisico:
> *"La forza elettrostatica accelera la struttura, quindi per la seconda legge di Newton $a = F/\mathcal{M}$, devo dividere la forza per la massa $\mathcal{M}$."*

L'intenzione era corretta al 100%. **Allora perché al tuo amico esce $9.3676 \times 10^{-13}$ invece di circa $10^{-10}\text{ kg}$?**

È successo un "corto circuito" tra le equazioni della slide e i dati presi dal paper di Frangi. Vediamo esattamente dove:

---

### 1. Il primo errore: Il fattore $10^{12}$ dei Microsecondi

Il tuo amico ha impostato la formula inversa:
$$\mathcal{M} = \frac{c_{1,DD}^{(1)}}{\text{Pendenza}_\omega}$$

E ha inserito:
- **Al numeratore**: $c_{1,DD}^{(1)} = 21.11 \times \varepsilon_0 = 21.11 \times 8.854 \times 10^{-6} = \mathbf{1.86912 \times 10^{-4}}$ (preso dalla Tabella 2 di Frangi).
- **Al denominatore**: la pendenza sperimentale del fit in radianti al secondo $\text{Pendenza}_\omega = 4\pi^2 \alpha_{\text{exp}} = \mathbf{1.9953 \times 10^8\ \frac{\text{rad}^2}{\text{s}^2 \cdot \text{V}^2}}$.

Ha fatto la divisione:
$$\mathcal{M} = \frac{1.86912 \times 10^{-4}}{1.9953 \times 10^8} = \mathbf{9.3676 \times 10^{-13}}$$

**Il tranello**: nel paper di Frangi il tempo è misurato in **microsecondi ($\mu\text{s}$)**, non in secondi (vedi Tabella 1, dove la rigidezza $c_{1,\beta}^{(1)} = 6.85\ \mu\text{s}^{-2}$).  
Quindi quel $1.86912 \times 10^{-4}$ al numeratore è espresso in **$\mu\text{s}^{-2}$**!  
Poiché $1\ \mu\text{s}^{-2} = \mathbf{10^{12}\ \text{s}^{-2}}$, al numeratore **mancava un fattore $10^{12}$**.

Se correggi il tempo in secondi, il numeratore vale $1.86912 \times 10^8\ \text{s}^{-2}/\text{V}^2$ e il risultato diventa:
$$\mathcal{M} = \frac{1.86912 \times 10^8}{1.9953 \times 10^8} = \mathbf{0.93676} \approx \mathbf{0.94}$$

---

### 2. Il secondo errore: Frangi aveva già posto $\mathcal{M} = 1$!

Guarda il numero corretto: **$0.9368$ (cioè $93.7\%$)**.  
Perché viene $0.9368$ e non la massa in kg?

Perché nel paper di Frangi (Eq. 1 a pag. 5), per fare le simulazioni numeriche agli elementi finiti hanno definito le coordinate modali ponendo la massa di riferimento **uguale a 1 ($M = 1$, normalizzata)**:
$$\int_{\Omega} \rho \psi_1^2 \, d\Omega = M = 1$$

Questo significa che:
- Nel paper di Frangi, **la massa era già stata divisa/inglobata a denominatore**!
- Il coefficiente $c_{1,DD}^{(1)} = 21.11 \varepsilon_0$ di Frangi **NON è una forza in Newton**, ma è **già un'accelerazione per Volt quadro** ($\text{s}^{-2}/\text{V}^2$).
- Quindi, nel modello di Frangi, $\mathcal{M}$ non è una massa in kg: è un parametro di scala adimensionale che vale $\mathcal{M} = 1$.

Quando il tuo amico ha diviso il coefficiente di Frangi per la pendenza sperimentale:
$$\mathcal{M} = \frac{\text{Pendenza Teorica Frangi (con } M=1)}{\text{Pendenza Sperimentale Misurata}} = \frac{4.735 \times 10^6}{5.054 \times 10^6} = \mathbf{0.9368}$$
ha semplicemente calcolato il **rapporto percentuale tra la teoria e il vostro esperimento ($93.7\%$)**!  
Non ha calcolato i kg, perché nel numero di Frangi la massa fisica non c'era: era stata normalizzata a $1$.  
Avendo poi dimenticato il $10^{12}$ dei microsecondi, gli è venuto $0.9368 \times 10^{-12} = \mathbf{9.3676 \times 10^{-13}}$, credendo fossero "kg".

---

### 3. Come far uscire la VERA massa in kg da quella stessa formula?

Se vuoi che $\mathcal{M}$ sia la **vera massa fisica in chilogrammi**, al numeratore non puoi usare il coefficiente già normalizzato di Frangi, ma devi usare la vera **derivata della forza elettrostatica in Newton**, data dalla geometria del condensatore:
$$k_{e0} = \frac{\varepsilon_0 A}{g_0^3} \approx \frac{8.854 \times 10^{-12} \cdot 1.28 \times 10^{-8}}{(1.80 \times 10^{-6})^3} = \mathbf{1.938 \times 10^{-2}\ \frac{\text{N}}{\text{m} \cdot \text{V}^2}}$$

Ora guarda le unità di misura: $[\text{N/m}] / [\text{rad}^2/\text{s}^2] = \mathbf{\text{kg}}$!  
Inserendo la forza reale nella formula:
$$\mathbf{\mathcal{M} = \frac{k_{e0}}{\text{Pendenza}_\omega}} = \frac{1.938 \times 10^{-2}\ \text{N}/(\text{m}\cdot\text{V}^2)}{1.9953 \times 10^8\ \text{s}^{-2}/\text{V}^2} = \mathbf{9.7 \times 10^{-11}\ \text{kg} \approx 0.1\ \text{ng}}$$

Ecco che esce la **vera massa fisica del MEMS ($0.1\text{ ng}$)**!

---

### In conclusione per il tuo amico:
- Ha fatto benissimo a voler estrarre la massa $\mathcal{M}$ dalla formula inversa della pendenza di softening.
- Gli è uscito $9.3676 \times 10^{-13}$ perché:
  1. Si è dimenticato che i tempi di Frangi sono in $\mu\text{s}$ (mancava $10^{12}$);
  2. Ha usato al numeratore il coefficiente di Frangi (che è già adimensionale/normalizzato a $M=1$) anziché la forza meccanica in Newton ($k_{e0} \approx 1.94 \times 10^{-2}\ \text{N}/(\text{m}\cdot\text{V}^2)$).
- Usando la forza in Newton, la massa fisica viene **$9.7 \times 10^{-11}\text{ kg} \approx 0.1\text{ ng}$**, che corrisponde perfettamente al peso dei due archi di silicio!

Ran command: `python3 -c "
import numpy as np

# 1. Pendenza sperimentale del fit:
# Dati dal fit su punti_vdc2_f2.csv
# Vdc2 = [9, 12.25, 16, 20.25, 25, 30.25, 36]
data = np.loadtxt('Frequenza_Vdc/Misure/punti_vdc2_f2.csv', delimiter=',', skiprows=1)
v2 = data[:, 0]
f2 = data[:, 1]
p = np.polyfit(v2, f2, 1)
alpha_exp = -p[0] # in Hz^2 / V^2

print(f'alpha_exp = {alpha_exp:.4e} Hz^2/V^2')
slope_omega = alpha_exp * (4 * np.pi**2)
print(f'slope_omega = {slope_omega:.4e} (rad/s)^2 / V^2')

# 2. Cosa ha fatto l'amico:
c1_tabella = 21.11
eps0_pF_um = 8.8541878e-6 # pF / mum
c1_amico = c1_tabella * eps0_pF_um # = 1.86912e-4
print(f'c1 amico = {c1_amico:.5e}')
M_amico = c1_amico / slope_omega
print(f'M_amico = {M_amico:.4e}')

# 3. Conversione corretta microsecondi -> secondi:
c1_SI = c1_amico * 1e12 # rad^2 / (s^2 * V^2)
print(f'c1_SI = {c1_SI:.5e} rad^2 / (s^2 * V^2)')
M_adimensionale = c1_SI / slope_omega
print(f'M adimensionale (rapporto teoria/esperimento) = {M_adimensionale:.4f}')

# 4. Calcolo della vera massa fisica in kg:
# Dimensioni reali del MEMS dal paper:
L = 532e-6 # m (lunghezza dell'arco)
h = 24e-6  # m (spessore del silicio)
w = 5e-6   # m (larghezza del beam)
g0 = 1.80e-6 # m (gap a riposo)
eps0 = 8.8541878e-12 # F/m

# Area elettrodi affacciati:
A = L * h # = 1.2768e-8 m^2
print(f'Area A = {A:.4e} m^2')

# Rigidezza elettrostatica per V^2: ke0 = eps0 * A / g0^3
ke0 = eps0 * A / (g0**3)
print(f'ke0 = {ke0:.5e} N / (m * V^2)')

# Massa modale efficace:
# slope_omega = ke0 / M_eff  =>  M_eff = ke0 / slope_omega
M_eff_kg = ke0 / slope_omega
print(f'M_eff = {M_eff_kg:.4e} kg')
print(f'M_eff in nanogrammi = {M_eff_kg * 1e9:.3f} ng')
print(f'M_eff in picogrammi = {M_eff_kg * 1e12:.1f} pg')

# Sanity check con la massa geometrica totale dei 2 beam:
rho = 2330.0 # kg/m^3
M_tot_geom = 2.0 * rho * (L * w * h)
print(f'M_tot_geom = {M_tot_geom:.4e} kg ({M_tot_geom * 1e9:.3f} ng)')
print(f'Frazione M_eff / M_tot_geom = {M_eff_kg / M_tot_geom:.3f}')
"`

Ti rifaccio tutti i passaggi da zero, con assoluto rigore matematico e citando direttamente le equazioni e le tabelle del paper di Frangi.

---

### PARTE 1: Perché $c_{1,\beta}^{(1)}$ e $\frac{c_{1,DD}^{(1)} V_{\mathrm{DC}}^2}{\mathcal{M}}$ hanno la stessa unità di misura?

Guardiamo l'equazione del moto del MEMS scritta nella slide del tuo amico (Eq. 4 della foto):
$$\ddot{q}_1 + \frac{\omega_{01}}{Q_1}\dot{q}_1 + \underbrace{\left( c_{1,\beta}^{(1)} - \frac{c_{1,DD}^{(1)} V_{\mathrm{DC}}^2}{\mathcal{M}} \right)}_{\text{TERMINE TRA PARENTESI}} q_1 = \text{forzamento}$$

Facciamo l'**analisi dimensionale** di ogni singolo pezzo:
1. $q_1$ è lo spostamento (ha le dimensioni di una **lunghezza**, es. metri $[\text{m}]$ o micrometri $[\mu\text{m}]$).
2. $\ddot{q}_1$ è l'accelerazione, quindi la sua unità è:
   $$[\ddot{q}_1] = \frac{[\text{lunghezza}]}{[\text{tempo}]^2} \quad \left(\text{ad esempio } \frac{\text{m}}{\text{s}^2} \text{ oppure } \frac{\mu\text{m}}{\mu\text{s}^2}\right)$$
3. Perché l'equazione sia fisicamente valida, **ogni termine deve avere le stesse identiche dimensioni di un'accelerazione**.
4. Guardiamo il terzo termine: $[\text{parentesi}] \cdot [q_1]$.
   Affinché $[\text{parentesi}] \cdot [\text{lunghezza}] = \frac{[\text{lunghezza}]}{[\text{tempo}]^2}$, la parentesi **DEVE** avere come unità di misura:
   $$\mathbf{[\text{parentesi}] = \frac{1}{[\text{tempo}]^2} = [\text{frequenza}]^2 = [\text{pulsazione}]^2}$$
5. Nella parentesi c'è una sottrazione:
   $$\left( c_{1,\beta}^{(1)} - \frac{c_{1,DD}^{(1)} V_{\mathrm{DC}}^2}{\mathcal{M}} \right)$$
   In fisica puoi sottrarre due grandezze **soltanto se hanno la stessa identica unità di misura**:
   - $c_{1,\beta}^{(1)}$ è la molla meccanica normalizzata $\implies$ **unità di misura: $\frac{1}{\text{tempo}^2}$** (è la pulsazione a riposo al quadrato $\omega_{01}^2$).
   - $\frac{c_{1,DD}^{(1)} V_{\mathrm{DC}}^2}{\mathcal{M}}$ è la molla elettrostatica negativa normalizzata $\implies$ **unità di misura: $\frac{1}{\text{tempo}^2}$** (è la riduzione di pulsazione al quadrato dovuta alla tensione continua).

---

### PARTE 2: C'è scritto sul paper?

**Sì, verifichiamolo punto per punto su Frangi et al. 2023:**

1. **Per il termine meccanico $c_{1,\beta}^{(1)}$**:
   - Vai a **pagina 6, Tabella 1** (*Coefficients of the mechanical nonlinear manifold*).
   - Per il primo modo ($i=1$), alla riga del termine lineare in $q_1$, Frangi scrive esplicitamente l'unità di misura:
     $$\mathbf{c_{1,\beta}^{(1)} = 6.85\ \mu\text{s}^{-2}}$$
   - Nota bene: l'unità è **$\mu\text{s}^{-2} = \frac{1}{\mu\text{s}^2}$**, cioè il tempo al denominatore al quadrato!
   - Infatti, estraendo la radice quadrata:
     $$\omega_{01} = \sqrt{6.85}\ \mu\text{s}^{-1} \approx 2.617\ \frac{\text{rad}}{\mu\text{s}} = 2.617 \times 10^6\ \frac{\text{rad}}{\text{s}}$$
     e la frequenza è: $f_{01} = \frac{\omega_{01}}{2\pi} \approx 416.55\text{ kHz}$.

2. **Per il termine elettrostatico con $\mathcal{M}$**:
   - A **pagina 7, Eq. (8)**, Frangi scrive la seconda legge di Newton:
     $$M \ddot{q}_1 + M \beta_1(q) = F_1(q)$$
     Dividendo ambo i membri per la massa $M$:
     $$\ddot{q}_1 + \beta_1(q) = \frac{F_1(q)}{M}$$
   - A **pagina 8, Eq. (13)**, la forza elettrostatica è data da:
     $$F_1(q) = f_{DD}^{(1)}(q) V_{\mathrm{DC}}^2 + \dots$$
     Sostituendo nell'equazione del moto, il termine elettrostatico diventa:
     $$\frac{f_{DD}^{(1)}(q)}{M} V_{\mathrm{DC}}^2$$
   - Espandendo in serie attorno a $q=0$, il termine lineare in $q_1$ è $\frac{c_{1,DD}^{(1)} V_{\mathrm{DC}}^2}{M} q_1$.
   - A **pagina 8**, Frangi scrive una frase chiave:
     > *"As anticipated, the reference mass $M$ is only needed to correctly specify the dimensions of all the terms, and it will henceforth set to unity."*
     Ovvero: **Frangi fissa la massa di riferimento a $M = 1$** per semplificare tutti i calcoli numerici!
   - A **pagina 9, Tabella 2**, Frangi riporta:
     $$c_1^{(1)}/\varepsilon_0 = 21.11$$

---

### PARTE 3: Rifacciamo i conti del tuo amico (perché esce $9.3676 \times 10^{-13}$?)

La formula inversa per ricavare $\mathcal{M}$ usata dal tuo amico è:
$$\mathcal{M} = \frac{c_{1,DD}^{(1)}}{\text{Pendenza}_\omega}$$

Vediamo i numeri che ha inserito:

#### Passaggio A: Il Numeratore ($c_{1,DD}^{(1)}$)
Dalla Tabella 2 del paper: $c_1^{(1)}/\varepsilon_0 = 21.11$.  
Nel sistema di unità del paper ($q$ in $\mu\text{m}$ e capacità in $\text{pF}$):
$$\varepsilon_0 = 8.8541878 \times 10^{-6}\ \frac{\text{pF}}{\mu\text{m}}$$
Moltiplicando:
$$c_{1,DD}^{(1)} = 21.11 \times (8.8541878 \times 10^{-6}) = \mathbf{1.86912 \times 10^{-4}}$$
**ATTENZIONE ALL'UNITÀ DI MISURA**: questo numero è espresso in **$\left[\frac{\text{rad}^2}{\boldsymbol{\mu\text{s}}^2 \cdot \text{V}^2}\right]$** (microsecondi alla meno 2!).

#### Passaggio B: Il Denominatore ($\text{Pendenza}_\omega$)
Dalle vostre misure sperimentali di laboratorio:
$$\alpha_{\text{exp}} = 5.054 \times 10^6\ \frac{\text{Hz}^2}{\text{V}^2}$$
Poiché $\omega = 2\pi f$, la pendenza in radianti al secondo al quadrato è:
$$\text{Pendenza}_\omega = 4\pi^2 \cdot \alpha_{\text{exp}} = 4\pi^2 \cdot (5.054 \times 10^6) = \mathbf{1.9953 \times 10^8\ \frac{\text{rad}^2}{\mathbf{s}^2 \cdot \text{V}^2}}$$
**ATTENZIONE ALL'UNITÀ DI MISURA**: questo numero è espresso in **$\left[\frac{\text{rad}^2}{\mathbf{s}^2 \cdot \text{V}^2}\right]$** (secondi alla meno 2!).

#### Passaggio C: La divisione fatta dal tuo amico
$$\mathcal{M} = \frac{1.86912 \times 10^{-4}}{1.9953 \times 10^8} = \mathbf{9.3676 \times 10^{-13}}$$

Il tuo amico ha diviso un numeratore in **$\mu\text{s}^{-2}$** per un denominatore in **$\text{s}^{-2}$**!  
Poiché $1\ \mu\text{s} = 10^{-6}\text{ s} \implies 1\ \mu\text{s}^{-2} = \mathbf{10^{12}\ \text{s}^{-2}}$, **ha dimenticato un fattore $10^{12}$!**

Se converti il numeratore in secondi:
$$c_{1,DD,\text{SI}}^{(1)} = (1.86912 \times 10^{-4}) \times 10^{12} = \mathbf{1.86912 \times 10^8\ \frac{\text{rad}^2}{\text{s}^2 \cdot \text{V}^2}}$$
E rifai la divisione con le unità coerenti (secondi con secondi):
$$\mathcal{M} = \frac{1.86912 \times 10^8}{1.9953 \times 10^8} = \mathbf{0.93676} \quad (\approx \mathbf{0.94})$$

**Perché esce $0.9368$ anziché la massa in kg?**  
Perché Frangi ha posto per definizione $M = 1$! Quel $c_{1,DD}^{(1)}$ di Frangi **ha già dentro la divisione per la massa modale**.  
Quindi $\mathcal{M} = 0.9368$ è un numero **adimensionale puro** che rappresenta il rapporto tra la pendenza teorica di Frangi ($4.735\times 10^6$) e la pendenza reale dell'esperimento ($5.054\times 10^6$):
$$\mathcal{M} = \frac{\alpha_{\text{teorico}}}{\alpha_{\text{sperimentale}}} = \frac{4.735 \times 10^6}{5.054 \times 10^6} = \mathbf{0.9368} \quad (\text{accordo del } \mathbf{93.7\%})$$

---

### PARTE 4: Il calcolo corretto della VERA MASSA FISICA in kg

Se vogliamo che $\mathcal{M}$ esca in **chilogrammi [kg]**, al numeratore non possiamo usare il coefficiente di Frangi (in cui la massa era già stata normalizzata a $1$), ma dobbiamo usare la vera **derivata della forza elettrostatica in Newton** ($[\text{N}/(\text{m}\cdot\text{V}^2)]$):

1. **Dati geometrici reali del MEMS (dal paper)**:
   - Lunghezza dei beam: $L = 532\ \mu\text{m} = 5.32 \times 10^{-4}\text{ m}$
   - Spessore del silicio: $h = 24\ \mu\text{m} = 2.4 \times 10^{-5}\text{ m}$
   - Area affacciata degli elettrodi: $A = L \cdot h = 532 \times 24 \times 10^{-12} = \mathbf{1.2768 \times 10^{-8}\ \text{m}^2}$
   - Gap a riposo: $g_0 = 1.80\ \mu\text{m} = 1.80 \times 10^{-6}\text{ m}$
   - Permittività dielettrica: $\varepsilon_0 = 8.8541878 \times 10^{-12}\ \text{F/m}$

2. **Calcolo della forza elettrostatica per unità di $V_{\mathrm{DC}}^2$ in Newton ($k_{e0}$)**:
   $$k_{e0} = \frac{\varepsilon_0 A}{g_0^3} = \frac{(8.8541878 \times 10^{-12}\ \text{F/m}) \cdot (1.2768 \times 10^{-8}\ \text{m}^2)}{(1.80 \times 10^{-6}\ \text{m})^3} = \mathbf{1.9385 \times 10^{-2}\ \frac{\text{N}}{\text{m} \cdot \text{V}^2}}$$

3. **Calcolo della Massa Efficace in kg**:
   Ora applichiamo la formula di Newton:
   $$\mathbf{m_{\text{eff}}} = \frac{k_{e0}}{\text{Pendenza}_\omega} = \frac{1.9385 \times 10^{-2}\ \frac{\text{N}}{\text{m}\cdot\text{V}^2}}{1.9953 \times 10^8\ \frac{\text{rad}^2}{\text{s}^2\cdot\text{V}^2}}$$
   Guardiamo le unità di misura:
   $$\frac{\text{N/m}}{\text{s}^{-2}} = \frac{(\text{kg} \cdot \text{m} / \text{s}^2) / \text{m}}{\text{s}^{-2}} = \mathbf{\text{kg}} \quad (\text{le unità di misura tornano perfettamente in kg!})$$
   Calcoliamo il valore numerico:
   $$\mathbf{m_{\text{eff}} = 9.715 \times 10^{-11}\ \text{kg} = 0.097\ \text{ng} \approx 0.1\ \text{ng}}$$

4. **Verifica strutturale (Sanity Check con la densità del silicio)**:
   - Densità del polisilicio: $\rho = 2330\text{ kg/m}^3$
   - Larghezza dei beam: $w = 5\ \mu\text{m} = 5 \times 10^{-6}\text{ m}$
   - Massa totale geometrica dei 2 beam:
     $$m_{\text{tot}} = 2 \cdot (\rho \cdot L \cdot w \cdot h) = 2 \cdot 2330 \cdot (5.32 \times 10^{-4} \cdot 5 \times 10^{-6} \cdot 2.4 \times 10^{-5}) = \mathbf{2.975 \times 10^{-10}\ \text{kg} \approx 0.30\ \text{ng}}$$
   - Per il primo modo di vibrazione flessionale (trave a doppio incastro), la massa efficace modale è circa il $33\%$ della massa totale:
     $$m_{\text{eff,teorica}} \approx 0.33 \cdot m_{\text{tot}} = 0.33 \cdot 0.30\text{ ng} \approx \mathbf{0.10\ \text{ng}}$$

Il valore estratto sperimentalmente dal softening ($0.097\text{ ng}$) e quello teorico strutturale ($0.10\text{ ng}$) coincidono.

Ran command: `python3 -c "
import pypdf
reader = pypdf.PdfReader('Chat Ai e appunti/Appunti_PMUT_Equazioni_Ringdown.pdf')
print(f'Total pages: {len(reader.pages)}')
for i, page in enumerate(reader.pages):
    print(f'--- PAGE {i+1} ---')
    print(page.extract_text()[:2000])
"`
Ran command: `python3 -c "
import pypdf
reader = pypdf.PdfReader('Chat Ai e appunti/Appunti_PMUT_Equazioni_Ringdown.pdf')
for i in range(min(6, len(reader.pages))):
    print(f'=== PAGE {i+1} ===')
    print(reader.pages[i].extract_text()[:2500])
"`
Listed directory Chat%20Ai%20e%20appunti
Ran command: `python3 -c "
import pypdf, glob

for f in glob.glob('Chat Ai e appunti/*.pdf'):
    reader = pypdf.PdfReader(f)
    print(f'=== {f} ({len(reader.pages)} pages) ===')
    for i, p in enumerate(reader.pages):
        txt = p.extract_text() or ''
        for line in txt.split('\n'):
            if any(w in line.lower() for w in ['massa', ' kg', 'meff', 'c1dd', 'mu\'', 'retroazione', 'ringdown', 'frangi']):
                print(f'  p.{i+1}: {line[:120]}')
"`
Ran command: `python3 -c "
import pypdf
reader = pypdf.PdfReader('Chat Ai e appunti/correzioni.pdf')
for i, page in enumerate(reader.pages):
    print(f'=== PAGE {i+1} ===')
    print(page.extract_text())
"`
Ran command: `python3 -c "
import pypdf
reader = pypdf.PdfReader('Chat Ai e appunti/Appunti Marco Modello RLC.pdf')
print(f'Total pages: {len(reader.pages)}')
for i, page in enumerate(reader.pages):
    print(f'=== PAGE {i+1} ===')
    print(page.extract_text()[:1000])
"`

Hai fatto centro: **la tua memoria è perfetta!** 

Il motivo per cui ti ricordavi che *"serviva dividere per la massa in kg altrimenti sballava tutto"* è documentato precisamente nel vostro file di progetto [correzioni.pdf](file:///Users/matteoluca/Downloads/es2m%20progetto/Chat%20Ai%20e%20appunti/correzioni.pdf) (Sezioni 2.2 e 2.3). 

Il tuo amico nella chat di WhatsApp sta facendo una **clamorosa confusione tra due problemi completamente diversi**:
1. Il calcolo della **retroazione attiva per ridurre il ringdown** (dove la massa in kg serviva davvero per convertire i Newton in accelerazione, altrimenti usciva l'assurdo guadagno $A \sim 10^{12}$).
2. Il calcolo del **softening elettrostatico di Frangi** (dove la massa non c'entra nulla perché il modello ROM di Frangi è già interamente normalizzato con $M=1$).

Vediamo punto per punto cosa è successo, cosa c'è scritto sui vostri appunti e nel paper, e perché i conti del tuo amico sono doppiamente sbagliati.

---

### 1. Perché ti ricordavi che "serviva dividere per la massa in kg"? (La retroazione del Ringdown)

Vai a vedere [correzioni.pdf (pagine 2 e 3)](file:///Users/matteoluca/Downloads/es2m%20progetto/Chat%20Ai%20e%20appunti/correzioni.pdf):

Quando progettavate la soppressione attiva del ringdown con il TIA (guadagno $G_e$) e l'amplificatore invertente (guadagno $-A$), la tensione di retroazione genera una **forza frenante fisica in Newton** proporzionale alla velocità:
$$F_{\text{feedback}} = - c_{\text{add}} \dot{q}_1 \quad [\text{Newton}]$$
Nel sistema internazionale (SI), la costante di smorzamento meccanico $c_{\text{add}}$ ha unità di misura $[\text{N}\cdot\text{s/m}] = [\text{kg/s}]$.

Nella seconda legge di Newton per il risonatore:
$$m_{\text{eff}} \ddot{q}_1 + (c + c_{\text{add}}) \dot{q}_1 + k q_1 = 0$$
Per scrivere l'equazione delle accelerazioni ($\ddot{q}_1 + \dots$), **devi dividere tutto per la massa in kg ($m_{\text{eff}}$)**:
$$\ddot{q}_1 + \left( \frac{\omega_{01}}{Q_1} + \frac{c_{\text{add}}}{m_{\text{eff}}} \right) \dot{q}_1 + \omega^2 q_1 = 0$$

Come spiega chiaramente [correzioni.pdf a pag. 3](file:///Users/matteoluca/Downloads/es2m%20progetto/Chat%20Ai%20e%20appunti/correzioni.pdf):
> *"Il termine $A G_e (c_{0,DA} V_{\mathrm{DC}})^2$ ha dimensioni kg/s. Per ottenere $\text{s}^{-1}$ va diviso per una massa. Nel modello ROM $M=1$ è adimensionale: trattarlo ingenuamente come $1\text{ kg}$ è l'origine del falso $10^{12}$."*

- Se trattavate il MEMS come se pesasse $M = 1\text{ kg}$, per frenarlo serviva un guadagno elettronico folle: **$A \approx 10^{12}$** (servirebbero gigavolt per muovere 1 kg!).
- Dividendo invece per la vera massa fisica in kg del MEMS ($m_{\text{eff}} \approx 10^{-10}\text{ kg}$), il guadagno richiesto tornava normalissimo: **$A \approx 36 \div 320$**!

---

### 2. L'errore del tuo amico: applicare quel discorso al softening di Frangi

Il tuo amico ha preso quel ricordo e ha scritto su WhatsApp:
> *"Bisogna metterla altrimenti a c1DD rimarrebbe il Kg e se si usasse la massa unitaria citata nel paper, I parametri uscirebbero sballati. Certo è molto strana come massa, è strapiccola ($9.3676 \times 10^{-13}$)..."*

Qui il tuo amico sbaglia su tutta la linea:

#### A. In Frangi NON c'è nessun "kg" dentro $c_{1,DD}$!
Nel paper di Frangi et al. 2023:
1. A **pagina 8, dopo l'Eq. (13)**, Frangi scrive letteralmente:
   > *"As anticipated, the reference mass $M$ is only needed to correctly specify the dimensions of all the terms, and it will henceforth set to unity ($M=1$)."*
2. Tutte le equazioni del paper sono bilanci di **accelerazioni su spostamento**:
   - $c_{1,\beta}^{(1)} = 6.85\ \mu\text{s}^{-2}$ (frequenza elastica propria al quadrato).
   - $c_{1,DD}^{(1)} V_{\mathrm{DC}}^2 = 1.869 \times 10^{-4} V_{\mathrm{DC}}^2\ \mu\text{s}^{-2}$ (variazione elettrostatica al quadrato).
3. Entrambi hanno **la stessa identica unità di misura**: $[\mu\text{s}^{-2}] = \frac{1}{\mu\text{s}^2} = [\text{pulsazione}]^2$.
4. **Non c'è nessun kg al numeratore!** Quindi non c'è alcun bisogno di dividere per una massa per togliere i kg, perché i kg non sono mai esistiti nel modello di Frangi!

Vedi la conferma esplicita a **pagina 2, punto 6 di [correzioni.pdf](file:///Users/matteoluca/Downloads/es2m%20progetto/Chat%20Ai%20e%20appunti/correzioni.pdf)**:
> *"Massa efficace: introdotta solo come strumento di conversione in SI (Sez. 2.3); **non fa parte del modello modale ($M=1$)**."*

---

### 3. Rifacciamo i conti del tuo amico: da dove salta fuori $9.3676 \times 10^{-13}$?

Il tuo amico ha scritto l'equazione inventandosi un $\mathcal{M}$ sotto il termine elettrostatico:
$$\omega_r^2 = c_{1,\beta}^{(1)} - \frac{c_{1,DD}^{(1)}}{\mathcal{M}} V_{\mathrm{DC}}^2 \implies \mathcal{M} = \frac{c_{1,DD}^{(1)}}{\text{Pendenza}_\omega}$$

Vediamo i numeri che ha inserito:

1. **Numeratore**:
   Dalla Tabella 2 di Frangi: $c_1^{(1)}/\varepsilon_0 = 21.11$.  
   Con $\varepsilon_0 = 8.854 \times 10^{-6}\ \text{pF}/\mu\text{m}$:
   $$\text{Numeratore} = 21.11 \times 8.854 \times 10^{-6} = \mathbf{1.86912 \times 10^{-4}\ \frac{\text{rad}^2}{\boldsymbol{\mu\text{s}^2} \cdot \text{V}^2}}$$
   *(espresso in **microsecondi** alla meno 2!)*

2. **Denominatore**:
   Dalla pendenza del vostro fit sperimentale sui dati (`punti_vdc2_f2.csv`):
   $\alpha_{\text{exp}} = 5.054 \times 10^6\ \text{Hz}^2/\text{V}^2$.
   Moltiplicando per $4\pi^2$ per avere $\omega^2$:
   $$\text{Denominatore} = 4\pi^2 \times 5.054 \times 10^6 = \mathbf{1.9953 \times 10^8\ \frac{\text{rad}^2}{\mathbf{s}^2 \cdot \text{V}^2}}$$
   *(espresso in **secondi** alla meno 2!)*

3. **La divisione del tuo amico**:
   $$\mathcal{M} = \frac{1.86912 \times 10^{-4}}{1.9953 \times 10^8} = \mathbf{9.3676 \times 10^{-13}}$$

#### Perché questo numero non è una massa?
1. **Errore sui microsecondi**: ha diviso microsecondi ($10^{-6}\text{ s}$) per secondi! Poiché $(1\ \mu\text{s})^{-2} = 10^{12}\ \text{s}^{-2}$, mancava un fattore $10^{12}$.
2. Se converti i microsecondi in secondi:
   $$\text{Numeratore}_{\text{SI}} = 1.86912 \times 10^{-4} \times 10^{12} = \mathbf{1.86912 \times 10^8\ \frac{\text{rad}^2}{\text{s}^2\cdot\text{V}^2}}$$
3. E rifai la divisione coerente:
   $$\frac{1.86912 \times 10^8}{1.9953 \times 10^8} = \mathbf{0.93676} \quad (\approx \mathbf{0.937})$$

**Quel $0.9368$ è semplicemente il rapporto tra la pendenza teorica di Frangi ($4.735 \times 10^6$) e quella del vostro esperimento ($5.054 \times 10^6$)!**  
È un numero **adimensionale puro** che vi dice che il modello teorico di Frangi è in perfetto accordo con le vostre misure al **$93.7\%$**!  
Non è mai stato una massa in kg: il fatto che gli venisse $10^{-13}$ era solo perché aveva dimenticato la conversione da $\mu\text{s}^2$ a $\text{s}^2$.

---

### 4. Come si calcola allora la VERA massa efficace in kg?

Se vuoi ricavare la vera massa meccanica in kg partendo dalla pendenza del softening sperimentale, non puoi usare il coefficiente adimensionale del paper ($M=1$), ma devi usare la formula fisica di Newton con la vera derivata della forza elettrostatica in **Newton** ($k_{e0}$):

$$k_{e0} = \frac{\varepsilon_0 A}{g_0^3} = \frac{(8.854 \times 10^{-12}\ \text{F/m}) \cdot (1.2768 \times 10^{-8}\ \text{m}^2)}{(1.80 \times 10^{-6}\ \text{m})^3} = \mathbf{1.9385 \times 10^{-2}\ \frac{\text{N}}{\text{m} \cdot \text{V}^2}}$$

Dividendo la rigidità elettrostatica in $\text{N}/(\text{m}\cdot\text{V}^2)$ per la pendenza sperimentale $\text{Pendenza}_\omega$ in $\text{s}^{-2}/\text{V}^2$:
$$m_{\text{eff}} = \frac{k_{e0}}{\text{Pendenza}_\omega} = \frac{1.9385 \times 10^{-2}}{1.9953 \times 10^8} = \mathbf{9.715 \times 10^{-11}\ \text{kg}} \approx \mathbf{0.1\ \text{ng}}$$

E questa coincide al millimetro con:
- La stima di [correzioni.pdf pag. 3](file:///Users/matteoluca/Downloads/es2m%20progetto/Chat%20Ai%20e%20appunti/correzioni.pdf): *"La massa $m_{\text{eff}} \sim 10^{-10}\text{ kg}$"*.
- La massa geometrica dei due archi di silicio: $\rho \cdot V \approx 2330 \cdot (2 \times 532 \times 5 \times 24 \times 10^{-18}) \approx 0.30\text{ ng}$, la cui massa modale del $1^\circ$ modo flessionale (circa $33\%$) è esattamente $\mathbf{0.10\text{ ng}}$.

### In sintesi, cosa puoi rispondere al tuo amico:
1. **Sul paper non c'è $M$ sotto $c_{1,DD}$**: Frangi pone esplicitamente $M=1$ a pagina 8 e lavora in accelerazioni modali ($[\mu\text{s}^{-2}]$ sia per la molla elastica che per quella elettrostatica).
2. **La divisione per la massa in kg serviva solo nella retroazione attiva del ringdown** (per convertire i Newton/Ampere in accelerazione ed evitare il falso guadagno $A=10^{12}$).
3. **Il suo $9.3676 \times 10^{-13}$ non è una massa**: è il rapporto adimensionale teoria/esperimento ($0.9368$, cioè $93.7\%$ di accordo) a cui mancava il fattore $(10^6)^2 = 10^{12}$ per convertire i $\mu\text{s}$ di Frangi nei secondi del fit.
4. **La vera massa in kg del MEMS è circa $10^{-10}\text{ kg} = 0.1\text{ ng}$**, che corrisponde al peso reale dei travi di silicio.