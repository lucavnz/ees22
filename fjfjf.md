Searched for "C_{\text{feed}}"
Searched for "C_{\text{re}}"

Ecco il motivo della confusione, ed è un equivoco normalissimo generato dalla lettera usata:

> **$C_{\text{feed}}$ NON è una capacità! Non si misura in Farad!**  
> $C_{\text{feed}}$ è un **GUADAGNO DI TENSIONE** adimensionale ($V_{\text{out}}/V_{\text{in}}$).  
> Nello script python è stato chiamato $C$ solo dall'inglese *"Constant"* (il fondo costante) o *"Coupling"*, ma **non è un condensatore**.

Vediamo passo dopo passo cosa significa fisicamente e perché si fa il modulo:

---

### 1. Che cos'è quel numero $11.7$?
Nel circuito ideale, il segnale che attraversa il condensatore parassita $C_p$ e arriva all'uscita produce una funzione di trasferimento:
$$
T_{Cp}(j\omega) = \frac{V_{\text{out}}}{V_{\text{in}}} = j \omega C_p R_{\text{trans}}
$$
Guardiamo le unità di misura:
* $\omega \approx 2\pi \cdot 418\,000\text{ rad/s}$ ($1/\text{s}$)
* $C_p \approx 0.89\cdot 10^{-12}\text{ F}$ ($\text{A}\cdot\text{s}/\text{V}$)
* $R_{\text{trans}} = 5.0\cdot 10^6\ \Omega$ ($\text{V}/\text{A}$)

Se li moltiplichi tra loro:  
$(1/\text{s}) \times (\text{A}\cdot\text{s}/\text{V}) \times (\text{V}/\text{A}) =$ **un numero puro, senza unità di misura**!  
È il guadagno di tensione $|V_{\text{out}}/V_{\text{in}}|$. E quanto vale numericamente?
$$
2\pi \cdot (417\,665) \cdot (0.892\cdot 10^{-12}) \cdot (5.0\cdot 10^6) \approx \mathbf{11.70}
$$
In decibel:
$$
20 \log_{10}(11.70) \approx \mathbf{+21.36\text{ dB}}
$$
Se guardi il grafico di Bode (Fig. 8.1), **la linea di base piatta** (fuori dalla risonanza) sta esattamente a $+21.36\text{ dB}$! Quello è il guadagno con cui l'ingresso passa dritto all'uscita attraverso $C_p$.

---

### 2. Perché questo guadagno ha una parte reale e una parte immaginaria?
La capacità $C_p$ in sé è un normale condensatore reale (non ha una "componente reale").  
Se gli amplificatori operazionali fossero perfetti e istantanei:
* La corrente del condensatore avrebbe sfasamento di $+90^\circ$ ($j$ puro).
* Il guadagno all'uscita sarebbe puramente immaginario: $0 + j\, 11.70$.

**MA nella realtà del laboratorio:**
Il segnale parassita deve attraversare il TIA (OPA656) e l'amplificatore invertente (AD817). A $\SI{418}{\kilo\hertz}$, gli operazionali non sono infinitamente veloci: hanno una banda finita e introducono un **ritardo di propagazione** (uno sfasamento di circa $-21.4^\circ$).  
In più, il substrato di silicio ha una piccola perdita dielettrica conduttiva.

Quindi il segnale parassita che esce su $V_{\text{out}}$ non arriva a $+90^\circ$, ma arriva sfasato a:
$$
+90^\circ - 21.4^\circ = \mathbf{+68.6^\circ}
$$
Nel piano complesso, un vettore che ha ampiezza $11.70$ e angolo $+68.6^\circ$ si scompone con seno e coseno:
* **Parte reale**: $11.70 \cdot \cos(68.6^\circ) = \mathbf{4.27}$
* **Parte immaginaria**: $11.70 \cdot \sin(68.6^\circ) = \mathbf{10.90}$

Ecco perché il fit trova due numeri: $C_{\text{re}} = 4.27$ e $C_{\text{im}} = 10.90$!  
Non è la capacità ad avere una parte reale: **è la tensione di uscita del fondo parassita che è ruotata a $68.6^\circ$ a causa del ritardo degli operazionali!**

---

### 3. Perché facciamo il modulo con Pitagora per trovare $C_p$?
Il ritardo degli operazionali ha solo girato l'angolo del vettore, ma **non ne ha cambiato la lunghezza totale**!  
La lunghezza totale del vettore (il modulo del guadagno) è determinata unicamente da $C_p$:
$$
\text{Modulo del guadagno} = \sqrt{(\text{Re})^2 + (\text{Im})^2} = \sqrt{4.27^2 + 10.90^2} = \mathbf{11.701}
$$
Poiché sappiamo che questo modulo vale teoricamente $\omega_0 C_p R_{\text{trans}}$, invertiamo la formula e ricaviamo la vera capacità fisica $C_p$:
$$
C_p = \frac{\text{Modulo del guadagno}}{2\pi f_0 R_{\text{trans}}} = \frac{11.701}{2\pi \cdot (417\,665\text{ Hz}) \cdot (5.0\cdot 10^6\ \Omega)} = \mathbf{0.892\text{ pF}}
$$

---

### Consiglio per la relazione
Chiamarlo $C_{\text{feed}} = C_{\text{re}} + j C_{\text{im}}$ trae in inganno perché fa pensare a una capacità in Farad.  
Se vuoi, nella relazione possiamo cambiare la notazione chiamandolo:
$$
T_{\text{feed}} = T_{\text{feed, re}} + j T_{\text{feed, im}} \quad \text{oppure} \quad G_{\text{feed}} = G_{\text{re}} + j G_{\text{im}}
$$
dove $T$ sta per *"Transfer function di feedthrough"* (o $G$ per *"Guadagno di fondo"*). Così chiunque legga capisce al primo sguardo che è un guadagno di tensione in uscita, non una bizzarra "capacità complessa"!