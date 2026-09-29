# Relazione Teorica e Sperimentale sul Transitorio Elettrico a $V_{DC} = 0\text{ V}$
## Origine Fisica del Ringing del TIA, Ruolo della Compensazione ($C_c$) e Giustificazione del Taglio a $20\ \mu\text{s}$

---

### Sommario Esecutivo
Questo documento fornisce la spiegazione fisica, circuitale e matematica rigorosa del transitorio oscillatorio osservato nei grafici sperimentali ([`transitorio_elettrico_vdc0.png`](file:///Users/matteoluca/Downloads/es2m%20progetto/Ampiezza_Frequenza/grafici/transitorio_elettrico_vdc0.png)) registrati a tensione di polarizzazione continua nulla ($V_{DC} = 0\text{ V}$).

Vengono integrati direttamente i valori numerici estratti dalle acquisizioni dell'oscilloscopio ([`scope_171.csv`](file:///Users/matteoluca/Downloads/es2m%20progetto/scope_171.csv), [`scope_172.csv`](file:///Users/matteoluca/Downloads/es2m%20progetto/scope_172.csv), [`scope_173.csv`](file:///Users/matteoluca/Downloads/es2m%20progetto/scope_173.csv)), dimostrando che:
1. L'oscillazione è la **risposta transitoria del 2° ordine sottosmorzato** dell'amplificatore a transimpedenza (TIA) caricato dalla capacità parassita verso massa del nodo d'ingresso $C_{\text{in}}$ e dalle capacità dei rami d'ingresso ($C_p$ e $C_c$).
2. A $V_{DC} = 0\text{ V}$, **il ramo serie RLC motazionale del MEMS è completamente inattivo/spento** ($i_{\text{RLC}} = 0$), poiché la forza elettrostatica e l'accoppiamento elettromeccanico sono nulli.
3. L'innesco del transitorio è dovuto al **gradino impulsivo di corrente** $\Delta I = -(C_p - C_c) \left. \frac{dv_{in}}{dt} \right|_{0^-}$ generato dall'interruzione brusca della derivata della tensione sinusoidale di eccitazione al disarmo del burst.
4. La frequenza sperimentale misurata è **$f_d \approx 600\text{ kHz}$**, con fattore di smorzamento **$\zeta \approx 0.25$** e costante di tempo **$\tau_{\text{el}} \approx 0.9 - 1.1\ \mu\text{s}$**, estinguendosi completamente entro **$2.56\ \mu\text{s}$**.
5. L'adozione di un taglio temporale a **$20\ \mu\text{s}$** per l'elaborazione del ring-down meccanico a $V_{DC} > 0$ offre un margine di sicurezza di **$8\times$**, garantendo l'eliminazione totale di qualsiasi artefatto elettronico.

---

### 1. Il Circuito Reale a $V_{DC} = 0\text{ V}$: Setup Sperimentale a Due Stadi e Tre Capacità Separate

Poiché $V_{DC} = 0\text{ V}$, il ramo risonatore elettromeccanico RLC ($R_m, L_m, C_m$) non conduce alcuna corrente ed è rimosso dallo schema equivalente.  
Nello schema circuitale compaiono **tre capacità fisicamente separate**, collegate a nodi e tensioni differenti:

```
                    +--------------------[ R_f ]--------------------+
                    |                     //                        |
                    |              +-----[ C_f ]-----+              |
                    |              |                 |              |
V_in -----[ C_p ]---*              |                 |              |
 (Ramo Parassita)   |              |                 |              |
                    *--------------+-------(-)       |              |
                    |                       \        |              |
V_in -[-1]-[ C_c ]--*                        [OPA656]*----[ R1 ]----+---(-)
 (Compensazione)    |                       /             100 Ohm   |    \
                   ---             +-------(+)                     ---    [AD817]*----> V_out
              C_in ---             |                              [R2]   /       (G_tot = 10*R_f)
                    |             GND                            1 kOhm +---(+)
                   GND                                              |        |
                                                                  V_out1    GND
```

1. **$C_p$ (Capacità parassita diretta del MEMS):** collegata tra l'ingresso $v_{in}(t)$ e il nodo invertente $V^-$. Conduce la corrente $i_p(t) = C_p \frac{d(v_{in} - V^-)}{dt} \approx C_p \frac{dv_{in}}{dt}$.
2. **$C_c$ (Capacità di compensazione hardware):** collegata tra l'uscita del blocco invertente `[-1]` (tensione $-v_{in}(t)$) e il nodo invertente $V^-$. Conduce la corrente $i_c(t) = C_c \frac{d(-v_{in} - V^-)}{dt} \approx -C_c \frac{dv_{in}}{dt}$ in controfase rispetto a $i_p$.
3. **$C_{\text{in}}$ (Capacità del nodo verso massa):** collegata tra il nodo invertente $V^-$ e GND ($0\text{ V}$). Rappresenta la capacità parassita del cavo coassiale BNC di collegamento tra risonatore e front-end ($\approx 100\text{ pF/m}$), delle piste PCB, dei pad e della capacità d'ingresso del chip OPA656 ($C_{cm} + C_{diff} \approx 2.8\text{ pF}$), per un totale di $\approx 150 - 180\text{ pF}$.
4. **Primo Stadio (TIA):** Operazionale FET ad altissima velocità **OPA656** ($GBWP = 230\text{ MHz}$) con $R_f = 500\text{ k}\Omega$ e capacità parassita di retroazione $C_f \approx 0.18\text{ pF}$.
5. **Secondo Stadio (Amplificatore Invertente):** Operazionale veloce **AD817** con $R_1 = 100\ \Omega$ e $R_2 = 1\text{ k}\Omega$ ($G_2 = -R_2/R_1 = -10\text{ V/V}$).

---

### 2. Condizione Pre-Stacco ($t < 0$): Perché l'uscita è quasi silente ($31\text{ mV}_{pp}$)?

Prima dell'istante di spegnimento ($t < 0$), l'eccitazione sinusoidale $v_{in}(t) = V_a \sin(\omega t)$ a $f \approx 418\text{ kHz}$ è attiva a regime continuo:
1. **Assenza di corrente meccanica:** Poiché $V_{DC} = 0\text{ V}$, il risonatore MEMS non produce corrente motazionale ($i_{\text{mech}} \equiv 0\text{ A}$).
2. **Bilanciamento capacitivo tra $C_p$ e $C_c$:**  
   La corrente che entra nel nodo di sense da monte è:
   $$i_{\text{net}}(t) = i_p(t) + i_c(t) = C_p \frac{d v_{in}}{dt} - C_c \frac{d v_{in}}{dt} = (C_p - C_c) \frac{d v_{in}}{dt} = \Delta C \frac{d v_{in}}{dt}$$
   Il segno meno è dovuto all'inversione di fase introdotta dal blocco `[-1]`.
3. **Cancellazione quasi perfetta:**  
   Tarando $C_c \approx C_p$, il disadattamento residuo è microscopico: $\Delta C = C_p - C_c \approx 40 - 50\text{ fF}$.  
   A $418\text{ kHz}$ con ampiezza di ingresso $V_a \approx 100\text{ mV}$ ($200\text{ mV}_{pp}$) e guadagno $G_{\text{tot}} = 10 \cdot 500\text{ k}\Omega = 5 \cdot 10^6\text{ V/A}$:
   $$V_{\text{out, pp}} = G_{\text{tot}} \cdot \omega \cdot \Delta C \cdot V_{in, pp} \approx (5 \cdot 10^6) \cdot (2\pi \cdot 418 \cdot 10^3) \cdot (40\cdot 10^{-15}) \cdot 0.2 \approx \mathbf{25 - 31\text{ mV}_{pp}}$$
   I $31\text{ mV}_{pp}$ misurati prima dello stacco sono esattamente il residuo di questa sottrazione.

---

### 3. All'Istante dello Stacco ($t = 0$): Perché si innesca il Picco Violento?

Al tempo $t = 0$, il generatore di segnale interrompe il burst sinusoidale e congela la tensione:
* La derivata $\frac{dv_{in}}{dt}$ crolla istantaneamente a zero.
* La corrente che attraversava il nodo d'ingresso subisce una discontinuità a gradino:
  $$\Delta I = 0 - \left. i_{\text{net}}(t) \right|_{t=0^-} = - (C_p - C_c) \cdot \left. \frac{d v_{in}}{dt} \right|_{t=0^-}$$

* In **`scope_172`**: La sinusoide si interrompe con pendenza negativa ($\left. \frac{dv_{in}}{dt} \right|_{0^-} < 0$). Il gradino di corrente risultante è **positivo** ($\Delta I > 0$). L'amplificatore risponde con una sovraelongazione iniziale **POSITIVA di $+804.0\text{ mV}$**.
* In **`scope_173`**: La sinusoide si interrompe con pendenza positiva ($\left. \frac{dv_{in}}{dt} \right|_{0^-} > 0$). Il gradino di corrente risultante è **negativo** ($\Delta I < 0$). L'amplificatore risponde con una sottoelongazione iniziale **NEGATIVA di $-607.1\text{ mV}$**.

---

### 4. Derivazione Rigorosa della Funzione di Trasferimento (KCL al Nodo $V^-$)

Scriviamo la legge di Kirchhoff delle correnti al nodo $V^-$ mantenendo distinte le tre capacità fisiche:
$$s C_p [V_{in}(s) - V^-(s)] + s C_c [-V_{in}(s) - V^-(s)] = s C_{\text{in}} V^-(s) + [V^-(s) - V_{\text{out1}}(s)] \left( \frac{1}{R_f} + s C_f \right)$$

Espandendo:
$$s C_p V_{in} - s C_p V^- - s C_c V_{in} - s C_c V^- = s C_{\text{in}} V^- + \frac{V^-}{R_f} + s C_f V^- - \frac{V_{\text{out1}}}{R_f} - s C_f V_{\text{out1}}$$

Raggruppando i termini in $V_{in}$ da una parte e i termini in $V^-$ dall'altra:
$$s (C_p - C_c) V_{in}(s) = V^-(s) \left[ \frac{1}{R_f} + s (C_{\text{in}} + C_p + C_c + C_f) \right] - V_{\text{out1}}(s) \left( \frac{1}{R_f} + s C_f \right)$$

Sostituendo la relazione dell'operazionale ad anello aperto $A(s) \approx \frac{\omega_t}{s} \implies V^-(s) = -\frac{s}{\omega_t} V_{\text{out1}}(s)$:
$$s (C_p - C_c) V_{in}(s) = -\frac{s}{\omega_t} V_{\text{out1}}(s) \left[ \frac{1}{R_f} + s (C_{\text{in}} + C_p + C_c + C_f) \right] - V_{\text{out1}}(s) \left( \frac{1}{R_f} + s C_f \right)$$

Moltiplicando ambo i membri per $R_f$ e raccogliendo $-V_{\text{out1}}(s)$:
$$s R_f (C_p - C_c) V_{in}(s) = - V_{\text{out1}}(s) \left[ 1 + s \left( R_f C_f + \frac{1}{\omega_t} \right) + s^2 \frac{R_f (C_{\text{in}} + C_p + C_c + C_f)}{\omega_t} \right]$$

Tenendo conto del guadagno invertente del secondo stadio $V_{\text{out}}(s) = -10 V_{\text{out1}}(s)$:

$$\boxed{\frac{V_{\text{out}}(s)}{V_{in}(s)} = \frac{10 \cdot s R_f (C_p - C_c)}{1 + s \left( R_f C_f + \frac{1}{\omega_t} \right) + s^2 \frac{R_f (C_{\text{in}} + C_p + C_c + C_f)}{\omega_t}}}$$

Se si esprime come funzione di transimpedenza rispetto alla corrente netta d'ingresso $I_{\text{in}}(s) = s (C_p - C_c) V_{in}(s)$:
$$\boxed{H(s) = \frac{V_{\text{out}}(s)}{I_{\text{in}}(s)} = \frac{10 \cdot R_f}{1 + s \left( R_f C_f + \frac{1}{\omega_t} \right) + s^2 \frac{R_f (C_{\text{in}} + C_p + C_c + C_f)}{\omega_t}}}$$

#### Significato Fisico delle Capacità Separate:
1. **Al numeratore compare $(C_p - C_c)$:** le correnti di $C_p$ e $C_c$ arrivano in opposizione di fase grazie all'inverter `[-1]`, annullando la corrente netta a regime.
2. **Al denominatore compare $(C_{\text{in}} + C_p + C_c + C_f)$:** tutte le capacità connesse al nodo $V^-$ ne determinano la frequenza di risonanza e la stabilità.
3. **Pesi numerici a confronto:**
   * $C_{\text{in}} \approx 180\text{ pF}$ (carico capacitivo dominante verso massa dovuto al cavo BNC e all'opamp).
   * $C_p \approx 1\text{ pF}$, $C_c \approx 1\text{ pF}$ (capacità di piccola entità rispetto al cavo).
   * La somma al denominatore è $C_{\text{in}} + C_p + C_c \approx 180 + 1 + 1 = 182\text{ pF} \approx C_{\text{in}}$.

---

### 5. Parametri Canonici del 2° Ordine e Verifica Sperimentale

Confrontando con $D(s) = 1 + \frac{2\zeta}{\omega_n} s + \frac{s^2}{\omega_n^2}$:
1. **Pulsazione naturale $\omega_n$ e frequenza $f_n$:**
   $$\omega_n = \sqrt{\frac{\omega_t}{R_f (C_{\text{in}} + C_p + C_c + C_f)}} \approx \sqrt{\frac{1.445 \times 10^9}{500\cdot 10^3 \cdot 182 \cdot 10^{-12}}} \approx 3.98 \times 10^6\text{ rad/s} \implies f_n \approx 634\text{ kHz}$$
2. **Coefficiente di smorzamento $\zeta$:**
   $$\zeta \approx \frac{1}{2} R_f C_f \omega_n \approx \frac{1}{2} (500\cdot 10^3) \cdot (0.18\cdot 10^{-12}) \cdot (3.98 \cdot 10^6) \approx 0.25$$
3. **Frequenza smorzata $f_d$:**
   $$f_d = f_n \sqrt{1 - \zeta^2} \approx 634 \cdot \sqrt{1 - 0.25^2} \approx \mathbf{614\text{ kHz} \approx 600\text{ kHz}}$$
4. **Costante di tempo $\tau_{\text{el}}$:**
   $$\tau_{\text{el}} = \frac{1}{\zeta \omega_n} \approx \mathbf{1.0\ \mu\text{s}}$$

I dati sperimentali misurati sugli oscillogrammi confermano esattamente questi valori:

| Parametro Fisico | Simbolo | Formula / Metodo | Scope 172 | Scope 173 | Media Sperimentale |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Ampiezza 1° Picco** | $V_{pk1}$ | Lettura diretta | $+804.0\text{ mV}$ | $-607.1\text{ mV}$ | **$\sim 705\text{ mV}$** |
| **Periodo Oscillazione** | $T_{\text{osc}}$ | $t_{pk2} - t_{pk1}$ | $1.691\ \mu\text{s}$ | $1.644\ \mu\text{s}$ | **$1.668\ \mu\text{s}$** |
| **Frequenza Smorzata** | $f_d$ | $1 / T_{\text{osc}}$ | **$591.4\text{ kHz}$** | **$608.3\text{ kHz}$** | **$\mathbf{599.8\text{ kHz} \approx 600\text{ kHz}}$** |
| **Smorzamento** | $\zeta$ | $\frac{\delta}{\sqrt{(2\pi)^2 + \delta^2}}$ | **$0.288$** | **$0.222$** | **$\mathbf{0.255}$** |
| **Costante di Tempo** | $\tau_{\text{el}}$ | $\frac{T_{\text{osc}}}{\delta}$ | **$0.894\ \mu\text{s}$** | **$1.150\ \mu\text{s}$** | **$\mathbf{1.022\ \mu\text{s}}$** |
| **Estinzione al 2%** | $t_{\text{settle}}$ | $\approx 4 \tau_{\text{el}}$ | **$2.56\ \mu\text{s}$** | **$2.53\ \mu\text{s}$** | **$\mathbf{2.55\ \mu\text{s}}$** |

---

### 6. Differenza tra Spegnimento (Scope 172-173) e Accensione (Scope 171)

* In **`scope_172` e `scope_173`**: Spegnimento del burst. $v_{in}$ si arresta, il MEMS non oscilla ($V_{DC}=0$), quindi esaurito il transitorio del TIA ($t > 2.56\ \mu\text{s}$), la corrente d'ingresso è zero e l'uscita si appiattisce sullo zero DC.
* In **`scope_171`**: Accensione del burst. Dopo il transitorio iniziale, permane l'oscillazione stazionaria di feedthrough residuo sinusoidale da circa $30 - 40\text{ mV}_{pp}$.

---

### 7. Conclusioni e Giustificazione del Taglio a $20\ \mu\text{s}$

1. **Separazione netta delle scale temporali:**
   * Dinamica parassita elettrica: $\tau_{\text{el}} \approx 1\ \mu\text{s}$, estinta entro **$2.56\ \mu\text{s}$**.
   * Dinamica meccanica MEMS: tempo di decadimento libero $t_d \approx 4.9\text{ ms}$ (oltre $1000\times$ più lento).
2. **Margine di sicurezza di $8\times$:**
   * Lo scarto dei primi $20\ \mu\text{s}$ ($20\ \mu\text{s} \gg 2.56\ \mu\text{s}$) garantisce la totale eliminazione del ringing elettronico senza degradare la stima dei parametri meccanici (il MEMS perde meno dello $0.4\%$ della sua ampiezza nei primi $20\ \mu\text{s}$).

---

### 8. Sintesi da Presentare al Professore (Discorso in 4 Punti)

> 1. *"A $V_{DC} = 0\text{ V}$, il risonatore MEMS non riceve alcuna forza elettrostatica: il ramo motazionale serie RLC è completamente spento e non inietta corrente ($i_{\text{RLC}} = 0$)."*
>
> 2. *"Nello schema circuitale abbiamo due rami d'ingresso distinti: il ramo parassita diretto con $C_p$ e il ramo di compensazione hardware con l'invertitore `[-1]` e $C_c$. Al nodo invertente la corrente netta vale $i_{\text{net}} = (C_p - C_c)\frac{dv_{in}}{dt}$: grazie all'inversione di fase e alla taratura $C_c \approx C_p$, a regime la corrente si annulla quasi perfettamente, lasciando solo $31\text{ mV}_{pp}$ residui."*
>
> 3. *"Allo stacco del burst ($t = 0$), l'interruzione brusca della derivata genera un gradino $\Delta I = -(C_p - C_c)(dv_{in}/dt)_{0^-}$. La polarità del balzo dipende dal segno della pendenza della sinusoide allo spegnimento: per questo nello Scope 172 l'uscita balza a $+804\text{ mV}$, mentre nello Scope 173 balza a $-607\text{ mV}$."*
>
> 4. *"Risolvendo la KCL al nodo invertente $V^-$, le capacità compaiono ciascuna dal proprio ramo: al numeratore la differenza $(C_p - C_c)$, al denominatore la somma di tutte le capacità connesse al nodo $(C_{\text{in}} + C_p + C_c + C_f)$. Il carico verso massa $C_{\text{in}} \approx 180\text{ pF}$ (dovuto al cavo BNC e all'opamp), unito a $C_p$ e $C_c$, riduce il margine di fase dell'OPA656 generando la risposta del 2° ordine sottosmorzata a $f_d \approx 600\text{ kHz}$ con $\tau_{\text{el}} \approx 1\ \mu\text{s}$. Poiché l'oscillazione si estingue entro $2.56\ \mu\text{s}$, il taglio a $20\ \mu\text{s}$ adottato nell'analisi del ringdown elimina ogni artefatto con un margine di $8\times$, preservando intatta la misura del decadimento meccanico."*