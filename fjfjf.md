Analyzed analizza_piano_complesso.py:L200-444
Analyzed cerchio_nyquist_confronto_globale.png
Analyzed cerchio_nyquist_dettaglio_fano.png
Analyzed nyquist_set2_frequenza.png
Edited analizza_piano_complesso.py
Edited analizza_piano_complesso.py
Edited analizza_piano_complesso.py
Edited analizza_compensazione_hardware.py
Edited analizza_compensazione_hardware.py
Ran regenerate Nyquist and hardware compensation plots
Analyzed cerchio_nyquist_confronto_globale.png
Analyzed cerchio_nyquist_dettaglio_fano.png
Analyzed nyquist_set2_frequenza.png
Edited analizza_piano_complesso.py
Ran re-run analizza_piano_complesso.py to fix math rendering
Analyzed cerchio_nyquist_confronto_globale.png
Analyzed relazione.tex:L1185-1285
Edited relazione.tex

Ho aggiornato i grafici di Nyquist rimuovendo completamente il `Set 1` (e ogni dicitura `Set 2`) in [analizza_piano_complesso.py](file:///Users/matteoluca/Downloads/es2m%20progetto/Compensazione%20Hardware/analizza_piano_complesso.py#L225-L280) e ho aggiornato la sezione sul piano complesso in [relazione.tex](file:///Users/matteoluca/Downloads/es2m%20progetto/Relazione/relazione.tex#L1212-L1301).

Ecco la spiegazione fisica completa di cosa fanno $C_p$ e $R_p$ nel piano complesso $(\mathrm{Re}\{T\}, \mathrm{Im}\{T\})$ e di cosa succede tra compensazione software e compensazione hardware:

---

### 1. Cosa traslano $C_p$ e $R_p$ nel piano Reale / Immaginario?
Il ramo parassita in parallelo al MEMS è formato da $C_p \parallel R_p$, la cui ammettenza moltiplicata per $R_{\text{trans}} = \SI{5.0}{\mega\ohm}$ vale:
$$\vec{T}_{\text{feed}} = R_{\text{trans}} \left( \underbrace{\frac{1}{R_p}}_{\text{Reale (in fase)}} + j \underbrace{\omega_0 C_p}_{\text{Immaginario (in quadratura)}} \right)$$
* **$R_p = \SI{11.2}{\mega\ohm}$ (corrente in fase con $v_{\text{in}}$):** trasla il cerchio **orizzontalmente lungo l'asse Reale** ($\mathrm{Re}\{T\}$) di una quantità:
  $$\Delta\mathrm{Re}_{Rp} = \frac{R_{\text{trans}}}{R_p} = \frac{\SI{5.0}{\mega\ohm}}{\SI{11.2}{\mega\ohm}} \approx \mathbf{0.445}$$
* **$C_p = \SI{0.892}{\pico\farad}$ (corrente sfasata di $+90^\circ$):** trasla il cerchio **verticalmente lungo l'asse Immaginario** ($\mathrm{Im}\{T\}$) di una quantità:
  $$\Delta\mathrm{Im}_{Cp} = \omega_0 C_p R_{\text{trans}} \approx \mathbf{11.70}$$
* **Perché nel grafico globale il vettore rosso $\vec{T}_{\text{feed}}$ non è dritto a $+90^\circ$ sull'asse immaginario ma è inclinato a $+68.6^\circ$, nel punto $(4.24, 10.90)$?**
  Perché a $\SI{418}{\kilo\hertz}$ gli operazionali della catena di lettura (TIA + stadio invertente AD817) introducono un ritardo di fase elettronico $\phi_m \approx -21.4^\circ$, che ruota in senso orario sia il cerchio sia il vettore parassita:
  $$(0.445 + j\,11.70) \cdot e^{-j\,21.4^\circ} \approx \mathbf{4.24 + j\,10.90} \quad (\text{modulo } 11.708,\ \text{angolo } +68.6^\circ)$$

---

### 2. Nella compensazione software abbiamo compensato anche $R_p$?
**Sì, automaticamente!**
Quando nella compensazione software fai la sottrazione vettoriale:
$$T_m(f) = T(f) - \vec{T}_{\text{feed}} = T(f) - (C_{\text{re}} + j\,C_{\text{im}})$$
stai sottraendo l'intero vettore complesso di fondo misurato fuori risonanza $\vec{T}_{\text{feed}} = 4.24 + j\,10.90$ (cioè sottrai **sia la parte immaginaria $C_{\text{im}}$ sia la parte reale $C_{\text{re}}$**, proprio come nella procedura numerica delle slide UniBS in [2026_02_20_UniBSMeasurements_Report.pptx.pdf](file:///Users/matteoluca/Downloads/es2m%20progetto/Paper/2026_02_20_UniBSMeasurements_Report.pptx.pdf) a pag. 17: *"2. Subtraction of the offset of the imaginary part $y_c$; 3. Subtraction of the offset of the real part $\Delta x$"*).
Quindi la sottrazione vettoriale software cancella in automatico **sia $C_p$ che $R_p$**, riportando il cerchio tratteggiato verde esattamente sull'origine $(0,0)$.

---

### 3. Perché allora in hardware $R_p$ (e quindi $R_c$) diventa fondamentale proprio guardando i cerchi di Nyquist?
Guarda i numeri nel piano complesso, perché qui si capisce tutto il senso del tuo circuito hardware:
* **Prima della compensazione** (quando c'è $C_p$ che vale $11.70$), il contributo ortogonale di $R_p$ ($0.445$) cambia la lunghezza del vettore totale di pochissimo:
  $$\sqrt{11.70^2 + 0.445^2} = 11.708 \quad (\text{variazione dello } 0.07\%, \text{ invisibile!})$$
* **Ma appena cancelli $C_p$ con il condensatore $C_c$**, il termine da $11.70$ sparisce e rimane **solo** lo spostamento dovuto a $R_p$:
  $$\frac{R_{\text{trans}}}{R_p} \approx \mathbf{0.445}$$
  Quanto è grande $0.445$ rispetto al cerchio di risonanza del MEMS? **Il diametro dell'intero cerchio del MEMS è $A_{\text{mot}} \approx 0.44$!**
  Cioè:
  * **Se in hardware avessi messo solo $C_c$ senza il resistore $R_c = \SI{1}{\mega\ohm}$**, nel piano Reale/Immaginario il cerchio del MEMS **non sarebbe tornato sull'origine $(0,0)$**, ma sarebbe rimasto **traslato di $0.445$ (un intero diametro!)** lungo la direzione reale, e nel diagramma di Bode il pavimento fuori risonanza si sarebbe fermato a $0.445$ ($-\SI{7}{\decibel}$), alto quanto il picco stesso del MEMS!
  * **Inserendo anche $R_c = \SI{1}{\mega\ohm}$ in parallelo a $C_c$**, hai cancellato in hardware **sia** la traslazione immaginaria di $C_p$ ($11.70$) **sia** la traslazione reale di $R_p$ ($0.445$), riportando il cerchio blu sull'origine $(0,0)$ esattamente come fa la compensazione software!

Ho inserito tutta questa spiegazione in modo chiaro e diretto in [relazione.tex](file:///Users/matteoluca/Downloads/es2m%20progetto/Relazione/relazione.tex#L1212-L1296).


