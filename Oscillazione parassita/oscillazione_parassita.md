# Analisi del Transitorio Elettrico a $V_{DC} = 0\text{ V}$ e Ruolo della Compensazione ($C_c$)

## 1. Assenza della Corrente Meccanica (Ramo RLC Spento a $V_{DC} = 0\text{ V}$)
A tensione di polarizzazione continua nulla ($V_{DC} = 0\text{ V}$), la forza elettrostatica motrice e il coefficiente di trasduzione elettromeccanico sono nulli:
$$I_{\text{mech}}(t) \approx 2 c_{0,DA}^{(1)} V_{DC} \, \dot{q}_1(t) = 0\text{ A}$$

Di conseguenza, **il ramo serie RLC equivalente del MEMS ($R_m, L_m, C_m$) non conduce alcuna corrente ed è rimosso dallo schema equivalente**. L'intero comportamento del circuito è puramente elettrico ed è determinato dal front-end TIA e dai rami capacitivi.

---

## 2. Lo Schema Circuitale: Tre Capacità Distinte ($C_p$, $C_c$, $C_{\text{in}}$)
Nello schema circuitale reale compaiono tre capacità fisicamente distinte e collegate a nodi diversi:
1. **$C_p$ (Capacità parassita diretta del MEMS):** collegata tra l'ingresso $v_{in}(t)$ e il nodo invertente $V^-$.
2. **$C_c$ (Capacità di compensazione hardware):** collegata tra l'uscita del blocco invertente `[-1]` (che fornisce $-v_{in}(t)$) e il nodo invertente $V^-$.
3. **$C_{\text{in}}$ (Capacità d'ingresso verso massa del nodo $V^-$):** collegata tra il nodo invertente $V^-$ e GND ($0\text{ V}$). Rappresenta la capacità parassita del layout, del cavo coassiale BNC di collegamento al chip carrier ($\approx 100\text{ pF/m}$), dei pad e dell'ingresso FET dell'OPA656 ($C_{cm} + C_{diff} \approx 2.8\text{ pF}$), per un totale di $\approx 150 - 180\text{ pF}$.

Non sono in parallelo tra loro: ciascuna appartiene al proprio ramo fisico con tensioni a monte diverse ($v_{in}$, $-v_{in}$ e $0\text{ V}$).

---

## 3. Corrente Netta Iniettata e Gradino allo Spegnimento ($t = 0$)
La corrente che fluisce attraverso $C_p$ verso il nodo $V^-$ è:
$$i_p(t) = C_p \frac{d(v_{in} - V^-)}{dt} \approx C_p \frac{dv_{in}}{dt}$$

La corrente che fluisce attraverso $C_c$ verso il nodo $V^-$ è:
$$i_c(t) = C_c \frac{d(-v_{in} - V^-)}{dt} \approx - C_c \frac{dv_{in}}{dt}$$

La corrente netta che entra nel nodo da monte è la loro somma:
$$i_{\text{net}}(t) = i_p(t) + i_c(t) = (C_p - C_c) \frac{d v_{in}(t)}{dt} = \Delta C \frac{d v_{in}(t)}{dt}$$
dove il segno meno deriva direttamente dal blocco invertente `[-1]` del ramo di compensazione.  
A regime sinusoidale, grazie alla taratura $C_c \approx C_p$, le due correnti si cancellano quasi perfettamente ($\Delta C \approx 40 - 50\text{ fF}$), lasciando solo $31\text{ mV}_{pp}$ in uscita prima dello stacco.

All'istante di spegnimento del burst ($t = 0$), la brusca interruzione della derivata della tensione genera un gradino impulsivo di corrente:
$$\Delta I = 0 - i_{\text{net}}(0^-) = - (C_p - C_c) \left. \frac{d v_{in}}{dt} \right|_{0^-}$$
* Se $\left. \frac{dv_{in}}{dt} \right|_{0^-} < 0 \implies \Delta I > 0$: picco iniziale positivo di $+804.0\text{ mV}$ (Scope 172).
* Se $\left. \frac{dv_{in}}{dt} \right|_{0^-} > 0 \implies \Delta I < 0$: picco iniziale negativo di $-607.1\text{ mV}$ (Scope 173).

---

## 4. Derivazione Rigorosa della Funzione di Trasferimento (KCL al Nodo $V^-$)

Scriviamo la legge di Kirchhoff delle correnti (KCL) al nodo invertente $V^-$ tenendo tutte le capacità separate:
* Corrente dal ramo $C_p$: $I_p(s) = s C_p [V_{in}(s) - V^-(s)]$
* Corrente dal ramo $C_c$: $I_c(s) = s C_c [-V_{in}(s) - V^-(s)]$
* Corrente verso massa attraverso $C_{\text{in}}$: $I_{Cin}(s) = s C_{\text{in}} V^-(s)$
* Corrente nel ramo di retroazione $R_f \parallel C_f$: $I_f(s) = [V^-(s) - V_{\text{out1}}(s)] \left( \frac{1}{R_f} + s C_f \right)$

Bilancio al nodo $V^-$ (correnti entranti = correnti uscenti):
$$s C_p [V_{in}(s) - V^-(s)] + s C_c [-V_{in}(s) - V^-(s)] = s C_{\text{in}} V^-(s) + [V^-(s) - V_{\text{out1}}(s)] \left( \frac{1}{R_f} + s C_f \right)$$

Espandendo e separando i termini in $V_{in}(s)$ da quelli in $V^-(s)$ e $V_{\text{out1}}(s)$:
$$s (C_p - C_c) V_{in}(s) = V^-(s) \left[ \frac{1}{R_f} + s C_f + s C_{\text{in}} + s C_p + s C_c \right] - V_{\text{out1}}(s) \left( \frac{1}{R_f} + s C_f \right)$$

Raccogliendo tutte le capacità che insistono sul nodo $V^-$:
$$s (C_p - C_c) V_{in}(s) = V^-(s) \left[ \frac{1}{R_f} + s (C_{\text{in}} + C_p + C_c + C_f) \right] - V_{\text{out1}}(s) \left( \frac{1}{R_f} + s C_f \right)$$

Modellando l'operazionale OPA656 ad anello aperto con guadagno $A(s) \approx \frac{\omega_t}{s}$:
$$V_{\text{out1}}(s) = -A(s) V^-(s) \implies V^-(s) = -\frac{s}{\omega_t} V_{\text{out1}}(s)$$

Sostituendo $V^-(s)$ nell'equazione:
$$s (C_p - C_c) V_{in}(s) = -\frac{s}{\omega_t} V_{\text{out1}}(s) \left[ \frac{1}{R_f} + s (C_{\text{in}} + C_p + C_c + C_f) \right] - V_{\text{out1}}(s) \left( \frac{1}{R_f} + s C_f \right)$$

Raccogliendo $-V_{\text{out1}}(s)$ e moltiplicando per $R_f$:
$$s R_f (C_p - C_c) V_{in}(s) = -V_{\text{out1}}(s) \left[ 1 + s \left( R_f C_f + \frac{1}{\omega_t} \right) + s^2 \frac{R_f (C_{\text{in}} + C_p + C_c + C_f)}{\omega_t} \right]$$

Il secondo stadio (AD817 in configurazione invertente) ha guadagno $G_2 = -\frac{R_2}{R_1} = -\frac{1\text{ k}\Omega}{100\ \Omega} = -10$, quindi $V_{\text{out}}(s) = -10 V_{\text{out1}}(s)$:

### Funzione di Trasferimento Tensione-Tensione:
$$\boxed{\frac{V_{\text{out}}(s)}{V_{in}(s)} = \frac{10 \cdot s R_f (C_p - C_c)}{1 + s \left( R_f C_f + \frac{1}{\omega_t} \right) + s^2 \frac{R_f (C_{\text{in}} + C_p + C_c + C_f)}{\omega_t}}}$$

### Funzione di Trasferimento Transimpedenza (Corrente-Tensione):
Definendo la corrente netta che entra nel nodo da monte come $I_{\text{in}}(s) = s(C_p - C_c) V_{in}(s)$:
$$\boxed{H(s) = \frac{V_{\text{out}}(s)}{I_{\text{in}}(s)} = \frac{10 \cdot R_f}{1 + s \left( R_f C_f + \frac{1}{\omega_t} \right) + s^2 \frac{R_f (C_{\text{in}} + C_p + C_c + C_f)}{\omega_t}}}$$

---

## 5. Analisi dei Termini e Peso Numerico delle Capacità
Questa formulazione mostra in modo trasparente dove va ciascuna capacità:
1. **Al numeratore:** compaiono unicamente $C_p$ e $C_c$ come $(C_p - C_c)$, perché sono le uniche due capacità attraversate dal segnale $v_{in}$ e dal suo opposto invertito $[-1]$.
2. **Al denominatore:** compaiono tutte le capacità collegate al nodo $V^-$:
   $$C_{\text{nodo}} = C_{\text{in}} + C_p + C_c$$
   * $C_{\text{in}} \approx 180\text{ pF}$ (la capacità dominante verso massa dovuta al cavo BNC di misura e all'opamp).
   * $C_p \approx 1\text{ pF}$ (parassita del chip MEMS).
   * $C_c \approx 1\text{ pF}$ (compensazione hardware).
   * $C_f \approx 0.18\text{ pF}$ (retroazione TIA).

Poiché $C_p + C_c \approx 2\text{ pF} \ll C_{\text{in}} \approx 180\text{ pF}$, la somma $C_{\text{in}} + C_p + C_c \approx 182\text{ pF}$ è numericamente dominata da $C_{\text{in}}$, ma nella formula analitica rigorosa compaiono tutte e tre separate!

---

## 6. Parametri Canonici del $2^\circ$ Ordine e Confronto Sperimentale
Confrontando con $D(s) = 1 + \frac{2\zeta}{\omega_n} s + \frac{s^2}{\omega_n^2}$:

1. **Pulsazione naturale $\omega_n$:**
   $$\omega_n = \sqrt{\frac{\omega_t}{R_f (C_{\text{in}} + C_p + C_c + C_f)}} \approx \sqrt{\frac{1.445 \times 10^9}{500\cdot 10^3 \cdot 182 \cdot 10^{-12}}} \approx 3.98 \times 10^6\text{ rad/s}$$
   $$f_n = \frac{\omega_n}{2\pi} \approx 634\text{ kHz}$$
2. **Fattore di smorzamento $\zeta$:**
   $$\zeta \approx \frac{1}{2} R_f C_f \omega_n \approx \frac{1}{2} (500\cdot 10^3) \cdot (0.18\cdot 10^{-12}) \cdot (3.98 \cdot 10^6) \approx 0.25$$
3. **Frequenza di oscillazione smorzata $f_d$:**
   $$f_d = f_n \sqrt{1 - \zeta^2} \approx 634 \cdot \sqrt{1 - 0.25^2} \approx \mathbf{614\text{ kHz} \approx 600\text{ kHz}}$$
4. **Costante di tempo $\tau_{\text{el}}$:**
   $$\tau_{\text{el}} = \frac{1}{\zeta \omega_n} \approx \mathbf{1.0\ \mu\text{s}}$$

Il transitorio si esaurisce completamente entro $4\tau_{\text{el}} \approx 2.56\ \mu\text{s}$, rendendo il taglio a $20\ \mu\text{s}$ sicuro e privo di distorsioni sul ringdown meccanico del MEMS.
