# Analisi della Risposta in Frequenza del MEMS ($V_{dc} = 5.0$ V)

## 1. Schema del circuito e modello fisico

La catena di misura è costituita da:
1. **Generatore di segnale ($V_{in}$)**: segnale sinusoidale di sweep in frequenza ($V_{in} \approx 101.3\text{ mV}_{\text{pp}}$).
2. **Risuonatore MEMS**: polarizzato con tensione continua $V_{dc} = 5.0\text{ V}$. Il risuonatore è modellato tramite:
   - Un ramo motrice serie **RLC** ($R_m, L_m, C_m$), che descrive l'accoppiamento elettromeccanico e la risonanza meccanica.
   - Una capacità parassita di feedthrough **$C_p$** in parallelo tra elettrodo di ingresso e uscita ($C_p \approx 0.89\text{ pF}$).
3. **Amplificatore a transimpedenza (TIA)**: la corrente in uscita dal MEMS entra nel nodo invertente (massa virtuale) di un OPA656 con resistenza di retroazione $R_f = 500\text{ k}\Omega$ e capacità parassita $C_f \approx 0.25\text{ pF}$.
4. **Stadio invertente a guadagno fisso**: guadagno $G_2 = -R_2 / R_1 = -1\text{ k}\Omega / 100\,\Omega = -10$.

### Funzione di trasferimento teorica

L'ammettenza complessiva del risuonatore MEMS è:
$$Y_{\text{mems}}(s) = s C_p + \frac{1}{R_m + s L_m + \frac{1}{s C_m}}$$

La corrente iniettata nel nodo del TIA è $I_{\text{in}}(s) = V_{in}(s) \cdot Y_{\text{mems}}(s)$.
La tensione di uscita finale dopo il TIA e lo stadio invertente è:
$$V_{out}(s) = G_2 \cdot Z_f(s) \cdot I_{\text{in}}(s) \approx G_2 R_f \cdot Y_{\text{mems}}(s) \cdot V_{in}(s)$$

Nella banda di sweep stretta ($\approx 800\text{ Hz}$ attorno a $417.8\text{ kHz}$):
- Il contributo di **feedthrough parassita** $s C_p$ produce un livello base costante di ampiezza ($|V_{out}/V_{in}| \approx 11.7$, pari a circa $21.36\text{ dB}$) e una fase base di circa $+68.6^\circ$ (determinata dalla fase capacitiva $+90^\circ$ e dal ritardo di fase del TIA e dello stadio invertente).
- Il **ramo motrice RLC** si sovrappone a questo livello base, generando la tipica coppia risonanza-antirisonanza (risonanza parallela / profilo Fano):
  - **Picco di modulo**: $f \approx 417.59\text{ kHz}$ ($G \approx 21.53\text{ dB}$).
  - **Minimo di modulo (antirisonanza)**: $f \approx 417.73\text{ kHz}$ ($G \approx 21.19\text{ dB}$).
  - **Minimo di fase**: la fase scende a un minimo di $66.4^\circ$ in corrispondenza del passaggio di risonanza motrice a $f \approx 417.64 - 417.67\text{ kHz}$.

---

## 2. Risultati del fit del modello RLC + $C_p$

Dal fit non lineare nel piano complesso della funzione di trasferimento $V_{out}/V_{in}(f)$:
- **Frequenza di risonanza naturale motrice ($f_0$)**: $417.665\text{ kHz}$ ($417665.1\text{ Hz}$)
- **Fattore di merito ($Q$)**: $2991.8 \approx 3000$
- **Ampiezza ramo motrice ($A_{\text{mot}}$)**: $0.4364$
- **Guadagno base feedthrough ($|C_{\text{feed}}|$)**: $11.701$ lineare ($\approx 21.36\text{ dB}$)
- **Stima capacità parassita $C_p$**:
  $$C_p = \frac{|C_{\text{feed}}|}{2\pi f_0 \cdot R_f \cdot G_2} = \frac{11.701}{2\pi \cdot 417665 \cdot 500\cdot 10^3 \cdot 10} \approx 0.89\text{ pF}$$

> [!NOTE]
> Il fattore di merito $Q \approx 2992$ ottenuto dal fit della risposta in frequenza coincide perfettamente con il valore ricavato dall'analisi nel dominio del tempo (ringdown decay time $\tau \approx 2.3\text{ ms}$, per cui $Q = \pi f_0 \tau \approx 3018$).

---

## 3. Stima diretta di $C_p$ da oscilloscopio a $V_{dc} = 0$ V

A tensione di polarizzazione continua $V_{dc} = 0\text{ V}$, il coefficiente di trasduzione elettromeccanica $\eta \propto V_{dc}$ si annulla completamente, disattivando il ramo motrice RLC (il silicio non oscilla). In queste condizioni, l'unica corrente che scorre verso la massa virtuale del TIA è quella puramente capacitiva dovuta a $C_p$:
$$I(t) = C_p \frac{d V_{in}}{dt} \iff I(j\omega) = j\omega C_p V_{in}$$

Attraversando il TIA ($R_f = 500\text{ k}\Omega$) e lo stadio invertente ($G_2 = 10$), il guadagno totale è $G_{\text{tot}} = R_f \cdot G_2 = 5.0 \times 10^6\text{ V/A}$, da cui:
$$|V_{out}| = 2\pi f C_p |V_{in}| \cdot G_{\text{tot}} \implies C_p = \frac{V_{out,\text{pk}}}{V_{in,\text{pk}} \cdot 2\pi f \cdot R_f \cdot G_2}$$

### Risultati da oscilloscopio:
1. **Scope 70 (bassa frequenza, $f \approx 50.0\text{ kHz}$)**:
   - $V_{in,\text{pk}} = 99.84\text{ mV}$, $V_{out,\text{pk}} = 140.96\text{ mV}$ (Guadagno = $1.412$)
   - Sfasamento: $\Delta\phi \approx +87.8^\circ$ (puro anticipo capacitivo)
   - **$C_p = 0.899\text{ pF}$**
2. **Scope 69 (frequenza prossima alla risonanza, $f \approx 417.8\text{ kHz}$)**:
   - $V_{in,\text{pk}} = 100.20\text{ mV}$, $V_{out,\text{pk}} = 1.212\text{ V}$ (Guadagno = $12.094$)
   - **$C_p = 0.921\text{ pF}$**

### Confronto a 3 vie sulla capacità parassita $C_p$:
| Metodo | Condizione | Frequenza | Guadagno $|V_{out}/V_{in}|$ | $C_p$ ricavata |
| :--- | :--- | :--- | :--- | :--- |
| **Scope 70** | $V_{dc} = 0\text{ V}$ (solo dielettrico) | $50.00\text{ kHz}$ | $1.412$ | **$0.899\text{ pF}$** |
| **Scope 69** | $V_{dc} = 0\text{ V}$ (solo dielettrico) | $417.79\text{ kHz}$ | $12.094$ | **$0.921\text{ pF}$** |
| **Fit dello sweep** | $V_{dc} = 5.0\text{ V}$ (RLC + $C_p$) | $417.66\text{ kHz}$ | $11.698$ | **$0.892\text{ pF}$** |

L'accordo tra i tre metodi è eccezionale (entro $\pm 2.5\%$), confermando che il livello base nello sweep di Bode è interamente spiegato dal feedthrough capacitivo $C_p$.

---

## 4. Compensazione software di $C_p$

La compensazione software consiste nel sottrarre vettorialmente nel dominio complesso il contributo di feedthrough $T_{\text{feed}} = C_{re} + j C_{im}$ dalla funzione di trasferimento misurata:
$$T_{\text{comp}}(f) = T_{\text{meas}}(f) - (C_{re} + j C_{im})$$

### Effetto fisico della compensazione:
1. **Modulo**: scompare l'antirisonanza (il minimo di cancellazione distruttiva) e viene ripristinato un picco lorentziano perfettamente simmetrico centrato su $f_0 = 417.664\text{ kHz}$, con ampiezza motrice pura $A_{\text{mot}} \approx 0.43$.
2. **Fase**: la fase non compensata era dominata dal $+68.6^\circ$ del condensatore parassita con solo una piccola ondulazione. Dopo la compensazione software, la fase compie la classica e completa rotazione di $180^\circ$ propria del risonatore meccanico del secondo ordine, passando per $0^\circ$ esattamente a $f = f_0$.

---

## 5. Grafici generati

I grafici sono salvati in [grafici](file:///Users/matteoluca/Downloads/es2m%20progetto/Risposta%20in%20frequenza/grafici) ad alta risoluzione (300 DPI), con asse delle frequenze limitato a $418.0\text{ kHz}$ e curve di fit continuo al 100% di opacità sopra i singoli punti sperimentali:

1. [bode_completo.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Risposta%20in%20frequenza/grafici/bode_completo.png): diagramma di Bode a 2 pannelli (modulo in alto, fase in basso) con punti sperimentali e fit teorico sovrapposto (fino a $418.0\text{ kHz}$).
2. [bode_modulo.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Risposta%20in%20frequenza/grafici/bode_modulo.png): grafico singolo del modulo (punti sperimentali + fit).
3. [bode_fase.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Risposta%20in%20frequenza/grafici/bode_fase.png): grafico singolo della fase (punti sperimentali + fit).
4. [bode_confronto_compensazione.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Risposta%20in%20frequenza/grafici/bode_confronto_compensazione.png): confronto diretto a 2 pannelli prima e dopo la compensazione software di $C_p$.
5. [bode_compensato.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Risposta%20in%20frequenza/grafici/bode_compensato.png): risposta del solo ramo motrice purificata dal parassita $C_p$.
6. [scope_stima_cp.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Risposta%20in%20frequenza/grafici/scope_stima_cp.png): forme d'onda temporali a $V_{dc} = 0\text{ V}$ a $50.0\text{ kHz}$ e $417.8\text{ kHz}$ con stima diretta di $C_p$.

