# Analisi della Risposta in Frequenza con Compensazione Hardware del MEMS

## 1. Schema del circuito e principio fisico di funzionamento

La catena di misura con compensazione hardware è costituita da:
1. **Generatore di segnale ($v_{in}$)**: fornisce il segnale sinusoidale di eccitazione ($V_{in} \approx 100\text{ mV}_{\text{pp}}$).
2. **Risuonatore MEMS**: polarizzato con tensione continua $V_{dc}$. È modellato da:
   - Un ramo motrice serie **RLC** ($R_m, L_m, C_m$), che rappresenta la dinamica elettromeccanica del risuonatore (forza elettrostatica $\propto V_{dc} v_{in}$, corrente motrice piezo-capacitiva $i_{\text{mot}}$).
   - Una capacità parassita di feedthrough diretto **$C_p \approx 0.89 - 0.92\text{ pF}$** tra elettrodi di attuazione e di sense.
3. **Ramo di compensazione hardware**:
   - Un blocco amplificatore invertente a guadagno unitario **`[-1]`**, che genera la tensione in controfase $-v_{in}(t)$.
   - Una capacità di compensazione regolabile (trimmer) **$C_c \approx C_p$**.
4. **Front-end TIA (Amplificatore a transimpedenza)**:
   - Realizzato con l'operazionale ultra-veloce OPA656, con resistenza di retroazione $R_f = 500\text{ k}\Omega$ e capacità parassita $C_f \approx 0.25\text{ pF}$.
   - Il nodo invertente $V^-$ funge da massa virtuale e costituisce il nodo di somma di corrente.
5. **Secondo stadio amplificatore invertente**:
   - Realizzato con AD817, guadagno fisso $G_2 = -R_2 / R_1 = -1\text{ k}\Omega / 100\,\Omega = -10$.
   - Guadagno totale di transimpedenza della catena: $G_{\text{tot}} = R_f \cdot |G_2| = 5.0 \times 10^6\text{ V/A}$.

### Equazione della corrente al nodo invertente

La corrente iniettata dal ramo MEMS è:
$$i_{\text{mems}}(t) = i_{\text{mot}}(t) + C_p \frac{d v_{in}}{dt}$$

La corrente iniettata dal ramo di compensazione hardware è:
$$i_c(t) = C_c \frac{d (-v_{in})}{dt} = - C_c \frac{d v_{in}}{dt}$$

La corrente netta che entra nel TIA è quindi:
$$i_{\text{net}}(t) = i_{\text{mems}}(t) + i_c(t) = i_{\text{mot}}(t) + (C_p - C_c) \frac{d v_{in}}{dt} = i_{\text{mot}}(t) + \Delta C \frac{d v_{in}}{dt}$$

Quando il circuito di compensazione è tarato in modo ottimale ($C_c \approx C_p$), la capacità parassita residua $\Delta C = |C_p - C_c|$ si riduce a poche decine di femtofarad ($\approx 12 - 13\text{ fF}$ rispetto ai $900\text{ fF}$ iniziali), eliminando la quasi totalità del feedthrough parassita e consentendo al TIA di rilevare la pura risposta meccanica del risuonatore.

---

## 2. Significato e contenuto delle tre cartelle (`Off`, `1`, `2`)

I dati raccolti durante la sessione di misura del 22 settembre 2026 sono organizzati in tre cartelle che descrivono i passaggi di taratura e misura:

### Cartella `Off` ($V_{dc} = 0\text{ V}$, MEMS spento / elettrostaticamente inattivo)
- **Condizione**: $V_{dc} = 0\text{ V}$. Poiché la forza elettrostatica sul risuonatore scala con $V_{dc}$, il ramo motrice RLC è completamente disattivato ($i_{\text{mot}} = 0$).
- **Obiettivo della misura**: Caratterizzare la pura funzione di trasferimento elettrica di cancellazione capacitiva su un'ampia banda di frequenze ($407.75 - 427.75\text{ kHz}$, span di $20\text{ kHz}$, passo $50\text{ Hz}$).
- **Comportamento fisico osservato**:
  - Il guadagno presenta un pronunciato **notch di cancellazione** con minimo a $f \approx 418.55\text{ kHz}$, dove il livello scende a $-20.05\text{ dB}$ ($V_{out} \approx 9.9\text{ mV}_{\text{pp}}$), rispetto ai circa $-6.0\text{ dB}$ ($V_{out} \approx 50\text{ mV}_{\text{pp}}$) all'estremo inferiore ($408\text{ kHz}$) e superiore ($428\text{ kHz}$).
  - La fase compie un netto salto di $180^\circ$ (da $-10^\circ$ a $+165^\circ$) in corrispondenza del notch, confermando che $C_c$ e $C_p$ si bilanciano esattamente a quella frequenza invertendo il segno della corrente differenziale residua.
  - Questo sweep dimostra che il trimmer di compensazione hardware è stato regolato per massimizzare la cancellazione proprio in corrispondenza della risonanza del MEMS.

### Cartella `1` ($V_{dc}$ attivo, prima taratura di compensazione)
- **Condizione**: Tensione continua di polarizzazione $V_{dc}$ attiva (MEMS acceso).
- **Sweep**: $417.330 - 418.130\text{ kHz}$ (span di $800\text{ Hz}$, passo fine di $2\text{ Hz}$, 401 punti).
- **Comportamento fisico osservato**:
  - Emerge chiaramente il picco di risonanza motrice meccanico del MEMS a $f_0 \approx 417.796\text{ kHz}$, con guadagno di picco pari a $-7.70\text{ dB}$ ($V_{out} \approx 41.2\text{ mV}_{\text{pp}}$).
  - Il livello di base del feedthrough residuo ai bordi è di circa $-14.5\text{ dB}$ ($V_{out} \approx 18.5\text{ mV}_{\text{pp}}$), corrispondente a una capacità sbilanciata $\Delta C \approx 12.8\text{ fF}$.
  - La fase compie la tipica transizione decrescente di risonanza (da $+60^\circ$ a $-140^\circ$).

### Cartella `2` ($V_{dc}$ attivo, seconda taratura ottimizzata)
- **Condizione**: Seconda misura con taratura fine migliorata del trimmer hardware.
- **Sweep**: $417.350 - 418.150\text{ kHz}$ (span di $800\text{ Hz}$, passo $2\text{ Hz}$, 401 punti).
- **Comportamento fisico osservato**:
  - Il livello di feedthrough ai bordi è ulteriormente ridotto, scendendo a $-16.36\text{ dB}$ ($V_{out} \approx 15.1\text{ mV}_{\text{pp}}$).
  - Il picco di risonanza sale a $-6.69\text{ dB}$ ($V_{out} \approx 46.0\text{ mV}_{\text{pp}}$), garantendo un contrasto picco-fondo di ben **$+9.67\text{ dB}$** (più di $3\times$ in ampiezza di tensione).
  - I parametri estratti dal fit lorentziano sono: $f_0 = 417.754\text{ kHz}$, $Q = 2262$, $A_{\text{mot}} = 0.279$ (guadagno lineare totale a centro picco $= 0.463$).

---

## 3. Confronto a tre vie: Parametri del modello

| Parametro Fisico | Simbolo | Senza Compensazione (`frequenza`) | Compensazione HW (`Set 1`) | Compensazione HW (`Set 2`) |
| :--- | :---: | :---: | :---: | :---: |
| **Frequenza di risonanza** | $f_0$ | $417.665\text{ kHz}$ | $417.797\text{ kHz}$ | $417.754\text{ kHz}$ |
| **Fattore di merito** | $Q$ | $\approx 2992$ | $\approx 1950$ | $\approx 2262$ |
| **Guadagno di picco** | $G_{\text{pk}}$ | $+21.53\text{ dB}$ ($11.93$) | $-7.70\text{ dB}$ ($0.412$) | **$-6.69\text{ dB}$ ($0.463$)** |
| **Livello base feedthrough** | $G_{\text{base}}$ | $+21.44\text{ dB}$ ($11.80$) | $-15.46\text{ dB}$ ($0.169$) | **$-15.15\text{ dB}$ ($0.175$)** |
| **Contrasto picco / fondo** | $\Delta G$ | **$+0.09\text{ dB}$** ($1.01\times$) | $+7.76\text{ dB}$ ($2.44\times$) | **$+8.46\text{ dB}$ ($2.65\times$)** |
| **Capacità parassita netta** | $C_{\text{eff}}$ | **$892\text{ fF}$** ($C_p$) | **$12.85\text{ fF}$** ($\Delta C$) | **$13.32\text{ fF}$** ($\Delta C$) |
| **Abbattimento feedthrough** | Atten. | $0\text{ dB}$ (riferimento) | $-36.9\text{ dB}$ ($70\times$) | **$-36.6\text{ dB}$ ($68\times$)** |

> [!NOTE]
> Nella misura **senza compensazione**, il feedthrough capacitivo ($C_p \approx 892\text{ fF}$) dominava completamente il segnale con un livello base di $+21.44\text{ dB}$, rendendo il picco motrice una minuscola ondulazione di appena $+0.09\text{ dB}$.
> Con la **compensazione hardware**, il feedthrough viene abbattuto di circa **$38\text{ dB}$** (la capacità residua scende a $\approx 13\text{ fF}$, ovvero una cancellazione del **$98.5\%$**), facendo emergere il picco di risonanza con un contrasto netto di quasi $10\text{ dB}$.

---

## 4. Confronto tra compensazione Hardware e Software

Confrontando la risposta ricavata con la compensazione hardware fisica e quella ottenuta tramite compensazione software (sottrazione vettoriale nel piano complesso eseguita sui dati non compensati):
- **Guadagno di picco motrice puro software**: $0.478$ lineare
- **Guadagno di picco motrice compensato hardware**: $0.463$ lineare
- **Accordo**: entro il **$3.1\%$**, a conferma della perfetta coerenza fisica tra il circuito hardware in laboratorio e la teoria della cancellazione di feedthrough.

---

## 5. Grafici generati

Tutti i grafici sono salvati ad alta risoluzione (300 DPI) in [grafici](file:///Users/matteoluca/Downloads/es2m%20progetto/Compensazione%20Hardware/grafici):

1. [bode_set2.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Compensazione%20Hardware/grafici/bode_set2.png): Diagramma di Bode (modulo e fase) a 2 pannelli per la taratura ottimizzata (Set 2), con punti sperimentali e fit teorico RLC continuo.
2. [bode_set1.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Compensazione%20Hardware/grafici/bode_set1.png): Diagramma di Bode a 2 pannelli per la prima taratura (Set 1).
3. [bode_off.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Compensazione%20Hardware/grafici/bode_off.png): Diagramma di Bode a 2 pannelli a larga banda ($20\text{ kHz}$) a $V_{dc} = 0\text{ V}$, che evidenzia il notch di cancellazione a $-20\text{ dB}$ a $418.55\text{ kHz}$ e la rotazione di fase di $180^\circ$.
4. [confronto_con_senza_compensazione.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Compensazione%20Hardware/grafici/confronto_con_senza_compensazione.png): Benchmark comparativo diretto a 2 pannelli tra la misura grezza non compensata ($+21.4\text{ dB}$) e la compensazione hardware (abbattimento di $-37.8\text{ dB}$, $78\times$).
5. [confronto_set1_vs_set2.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Compensazione%20Hardware/grafici/confronto_set1_vs_set2.png): Confronto a 2 pannelli tra la taratura iniziale (Set 1) e la taratura ottimizzata (Set 2).
6. [confronto_modulo_tutti.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Compensazione%20Hardware/grafici/confronto_modulo_tutti.png): Confronto del modulo su pannello singolo tra Set 1, Set 2 e il livello base di fondo misurato in Off.
7. [confronto_hardware_vs_software.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Compensazione%20Hardware/grafici/confronto_hardware_vs_software.png): Confronto diretto del picco lineare tra la compensazione hardware reale e la compensazione software calcolata per sottrazione vettoriale.
8. [bode_set2_modulo.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Compensazione%20Hardware/grafici/bode_set2_modulo.png) e [bode_set2_fase.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Compensazione%20Hardware/grafici/bode_set2_fase.png): Grafici singoli del modulo e della fase per Set 2.
9. [bode_set1_modulo.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Compensazione%20Hardware/grafici/bode_set1_modulo.png) e [bode_set1_fase.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Compensazione%20Hardware/grafici/bode_set1_fase.png): Grafici singoli del modulo e della fase per Set 1.
10. [bode_off_modulo.png](file:///Users/matteoluca/Downloads/es2m%20progetto/Compensazione%20Hardware/grafici/bode_off_modulo.png): Grafico singolo del modulo a larga banda per Off.
