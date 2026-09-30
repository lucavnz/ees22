Viewed analizza_ringdown.py:1-757
Viewed analizza_duffing.py:1-371

Sì, esattamente: in entrambi gli script lo scopo cruciale è **misurare la frequenza di oscillazione naturale del MEMS con precisione estrema** (al singolo Hertz o frazione di Hertz), analizzando cosa succede quando l'eccitazione viene spenta e il dispositivo continua a oscillare liberamente (fenomeno del *ring-down*).

* In [analizza_ringdown.py](file:///Users/matteoluca/Downloads/es2m%20progetto/Ampiezza_Frequenza/analizza_ringdown.py) si verifica se la frequenza propria $f_0$ cambia o rimane costante al variare della frequenza con cui il MEMS era stato eccitato prima del gate.
* In [analizza_duffing.py](file:///Users/matteoluca/Downloads/es2m%20progetto/Duffing/analizza_duffing.py) si misura come la frequenza istantanea $f_1(t)$ varia nel tempo durante il decadimento: quando oscilla con ampiezza grandissima la molla "cede" un po' (non-linearità di Duffing / *spring softening*) e la frequenza è più bassa, per poi risalire man mano che l'ampiezza diminuisce.

Vediamo ora in modo chiaro, intuitivo e passo dopo passo cosa significano lo **Zero-Padding 64x** e il **metodo della fase istantanea** (con parte reale e immaginaria).

---

### 1. Cosa significa "Zero-Padding 64x"?

#### Il problema: l'effetto "staccionata" della FFT (*Picket-Fence Effect*)
Quando registri un segnale con l'oscilloscopio per una durata finita (ad esempio $T = 2.45\text{ ms}$), la trasformata di Fourier classica (FFT) scompone il segnale in "scatole" o frequenze discrete (*bin*), separate tra loro di un passo:
$$\Delta f = \frac{1}{T} \approx \frac{1}{2.45 \times 10^{-3}\text{ s}} \approx 408\text{ Hz}$$

Immagina di guardare un panorama dietro una **staccionata**: vedi solo attraverso le fessure verticali ogni 408 Hz (ad esempio a $417\,200\text{ Hz}$, $417\,608\text{ Hz}$, $418\,016\text{ Hz}$, ...).
Se il picco reale della frequenza del MEMS si trova a **$417\,840\text{ Hz}$**, esso cade **in mezzo a due fessure**! La FFT standard assegnerà il picco al punto più vicino, commettendo un errore di decine o centinaia di Hertz.

```
       Spettro continuo reale:              /\
                                           /  \
       Punti FFT standard (1x):      *    |    |    *
                                     417.6     418.0 kHz
                          (Il vero vertice cade nel vuoto!)
```

#### La soluzione: lo Zero-Padding (es. 64x)
In [analizza_ringdown.py (righe 168-172)](file:///Users/matteoluca/Downloads/es2m%20progetto/Ampiezza_Frequenza/analizza_ringdown.py#L168-L172):
```python
N_fwin = len(sig_fwin)
N_pad = N_fwin * 64
fft_pad = np.fft.rfft(sig_fwin, n=N_pad)
```
* **Cosa si fa fisicamente?** Si prende il segnale registrato di $N$ campioni e si "incollano" in coda degli zeri fino a raggiungere $64 \times N$ campioni.
* **Cosa produce?** Aggiungere zeri non crea informazione fasulla (il segnale è sempre quello), ma nella trasformata di Fourier equivale a **campionare lo spettro su una griglia 64 volte più densa**:
  $$\Delta f_{\text{pad}} = \frac{408\text{ Hz}}{64} \approx 6.4\text{ Hz}$$
* **Risultato:** La campana dello spettro non è più una linea spezzata con 2 o 3 punti grossolani, ma una curva liscia e continua. Cercare il punto di massimo (`np.argmax`) permette di individuare il vertice del picco con un'accuratezza di pochissimi Hertz.

---

### 2. Il Metodo della Fase Istantanea: Perché "Reale" e "Immaginario"?

Questa è la tecnica più potente ed elegante usata negli script ([analizza_ringdown.py:153-165](file:///Users/matteoluca/Downloads/es2m%20progetto/Ampiezza_Frequenza/analizza_ringdown.py#L153-L165) e [analizza_duffing.py:163-172](file:///Users/matteoluca/Downloads/es2m%20progetto/Duffing/analizza_duffing.py#L163-L172)).

#### L'analogia: la Ruota Panoramica e la sua Ombra
Immagina una ruota panoramica illuminata dal sole laterale, che proietta la sua **ombra su un muro**:
* L'ombra sul muro va avanti e indietro su una linea orizzontale: questo è il **segnale reale** $s(t) = A \cos(\theta(t))$ che l'oscilloscopio misura (la tensione elettrica).
* **Il problema dell'ombra (1D):** quando l'ombra si trova al centro (tensione = $0\text{ V}$), dove si trova la cabina? Sta andando a destra o a sinistra? E quanto velocemente sta girando la ruota in quell'istante? Solo guardando l'ombra in un punto è difficile dirlo con precisione, specie se c'è rumore.
* **La soluzione (2D):** guardare la ruota panoramica **di fronte**, nel piano a due dimensioni!

```
                Asse Immaginario (Y = Hilbert)
                             ^
                             |       Cabina (Vettore Reale + Immaginario)
                             |      * 
                             |     /|
                             | A  / | 
                             |   /  |  
                             |  / θ | 
                             +--------------> Asse Reale (X = Segnale Misurato)
                                    |
                                    Ombra proiettata (il voltaggio reale)
```

#### Cos'è la Trasformata di Hilbert?
La funzione `hilbert(segnale)` costruisce il cosiddetto **segnale analitico complesso**:
$$z(t) = X(t) + j \cdot Y(t)$$
* **Parte Reale $X(t)$:** è il segnale autentico misurato (la posizione orizzontale dell'ombra).
* **Parte Immaginaria $Y(t)$:** è esattamente lo stesso segnale **sfasato di 90° (un quarto di giro)**. In fisica corrisponde alla "velocità" con cui si muove l'oscillatore.
* Mettendo insieme $X$ e $Y$, a ogni istante di tempo abbiamo una **freccia (vettore)** che ruota nel piano:
  1. La **lunghezza della freccia** è l'ampiezza dell'oscillazione: $A(t) = \sqrt{X^2 + Y^2}$ (`np.abs(analytic)`).
  2. L'**angolo della freccia** è la **fase istantanea**: $\theta(t) = \arctan(Y / X)$ (`np.angle(analytic)`).

---

### 3. Lo Srotolamento (`np.unwrap`) e la Funzione di Fit: Cosa Fanno?

Quando la freccia gira, l'angolo calcolato matematicamente con l'arcotangente va da $-180^\circ$ a $+180^\circ$ (da $-\pi$ a $+\pi$). Appena fa un giro completo, "scatta" indietro a $-180^\circ$.

1. **Lo srotolamento (`np.unwrap`):**
   Rimuove i salti di $360^\circ$ e tiene il conto continuo di tutti i giri percorsi:
   $$1^\circ\text{ giro } (360^\circ) \to 2^\circ\text{ giro } (720^\circ) \to \dots \to 1000^\circ\text{ giro } (360\,000^\circ)$$
   Otteniamo così una curva della **fase cumulativa $\theta(t)$** che cresce continuamente nel tempo.

2. **Cos'è la funzione di fit della fase?**
   Fisicamente, la fase di una sinusoide che gira a frequenza $f$ è:
   $$\theta(t) = 2\pi f \cdot t + \phi_0$$
   Questa è l'equazione di una **linea retta**: $y = m \cdot x + q$.
   * $x$ è il tempo $t$
   * $y$ è la fase srotolata $\theta(t)$
   * La **pendenza $m$** della retta è la velocità angolare $\omega = 2\pi f$ (quanti radianti al secondo compie la rotazione).

3. **Il fit lineare (`np.polyfit(t, phase, 1)`):**
   ```python
   p_phase = np.polyfit(t_fwin, phase_inst, 1)
   f_hilbert = p_phase[0] / (2.0 * np.pi)
   ```
   Trova la retta che meglio interpola i dati. Dividendo la sua pendenza per $2\pi$, otteniamo direttamente la **frequenza media di oscillazione**.

#### Perché questo metodo è molto superiore a contare i picchi o gli zeri?
* Se conti solo i passaggi per lo zero (*zero-crossing*), usi solo 2 campioni per ogni ciclo (e se c'è rumore puoi avere falsi passaggi per lo zero).
* Il fit della fase istantanea di Hilbert usa **ogni singolo campione registrato dall'oscilloscopio** (spesso $20\,000$ o più punti). Tutti i micro-errori e il rumore bianco vengono mediati e cancellati dalla regressione lineare, garantendo una precisione di frazioni di Hertz.

---

### 4. E nel caso di Duffing (Frequenza che varia nel tempo)?

In regime non-lineare (Duffing), la frequenza non è perfettamente costante: all'inizio la molla è "ammorbidita" dall'ampia oscillazione, quindi la ruota gira leggermente più lenta, poi man mano che l'ampiezza decade, la velocità di rotazione aumenta.

Per vederlo:
* In [analizza_duffing.py (righe 166-173)](file:///Users/matteoluca/Downloads/es2m%20progetto/Duffing/analizza_duffing.py#L166-L173), invece di fittare l'intero segnale con una sola retta, si prende una **finestrella mobile di $750\,\mu\text{s}$** e si calcola la pendenza della fase locale in quel piccolo intervallo:
  $$f_1(t) = \frac{1}{2\pi} \frac{\Delta \theta}{\Delta t}$$
* In questo modo si ottiene il grafico continuo di $f_1(t)$ che mostra la risalita della frequenza (da $\approx 417.65\text{ kHz}$ a $\approx 417.79\text{ kHz}$) durante il ring-down.
Listed directory Risposta%20in%20frequenza
Listed directory Compensazione%20Hardware
Searched for "curve_fit"
Searched for "curve_fit"
Viewed analizza_risposta_in_frequenza.py:50-115
Viewed analizza_compensazione_hardware.py:150-200
Searched for "fit"

L'algoritmo utilizzato per i fit in [Risposta in frequenza](file:///Users/matteoluca/Downloads/es2m%20progetto/Risposta%20in%20frequenza/analizza_risposta_in_frequenza.py) e in [Compensazione Hardware](file:///Users/matteoluca/Downloads/es2m%20progetto/Compensazione%20Hardware/analizza_compensazione_hardware.py) appartiene alla famiglia dei **Minimi Quadrati Non Lineari** (*Non-linear Least Squares*) ed è noto come **Algoritmo di Levenberg-Marquardt** (spesso abbreviato in **LM**).

In Python è richiamato tramite la funzione `curve_fit` della libreria scientifica `scipy.optimize`.

---

### 1. Che cos'è un "fit" (in parole semplici)?
Immagina di avere:
1. **Punti sperimentali misurati**: i dati reali acquisiti dallo strumento (frequenze, ampiezze, fasi, tensioni dell'oscilloscopio), che contengono rumore e piccole imprecisioni.
2. **Un modello teorico (una formula fisica)**: per esempio, la risposta in frequenza di un circuito RLC o una sinusoide $A \sin(2\pi f t + \phi)$. Questa formula ha delle "manopole" che non conosciamo a priori con precisione assoluta (frequenza di risonanza $f_0$, fattore di merito $Q$, capacità parassita $C_p$, ampiezza $A$, ecc.).

**Fare il fit** significa far girare quelle manopole al computer finché la curva matematica non si sovrappone ai punti misurati nel miglior modo possibile.

---

### 2. Come decide il computer qual è la curva "migliore"? (I Minimi Quadrati)
Per ogni punto sperimentale $(x_i, y_i)$, il computer calcola la distanza verticale tra il valore reale misurato e quello che la formula teorica prevederebbe:
$$\text{errore}_i = y_{\text{misurato}, i} - y_{\text{modello}, i}$$

L'algoritmo:
1. Eleva ogni errore al **quadrato** ($\text{errore}_i^2$): questo fa sì che gli errori positivi e negativi non si annullino a vicenda e "punisce" molto di più i punti che si allontanano tanto dalla curva.
2. Fa la **somma di tutti i quadrati degli errori** (detta funzione di costo o $\chi^2$).
3. Cerca la combinazione di parametri che rende questa somma **la più piccola possibile** (*Minimi Quadrati*).

---

### 3. Come funziona l'algoritmo di Levenberg-Marquardt? (La metafora della nebbia)
Immagina di trovarti su una montagna immersa in una fitta nebbia. L'altitudine a cui ti trovi rappresenta l'errore: il tuo obiettivo è scendere nella valle più profonda (errore minimo), ma non vedi la mappa completa.

L'algoritmo di **Levenberg-Marquardt** è brillante perché combina insieme due strategie diverse:

1. **La Discesa del Gradiente (*Gradient Descent*) – La strategia prudente**:
   - Guardi sotto i tuoi piedi, vedi da che parte il terreno scende e fai un piccolo passo in quella direzione.
   - *Pregio*: È molto affidabile e non ti fa cadere nei dirupi, anche se sei lontanissimo dalla soluzione.
   - *Difetto*: Quando sei vicino al fondo valle diventa lentissima a trovare il punto esatto.

2. **Il Metodo di Gauss-Newton – La strategia veloce**:
   - Approssima il terreno attorno a te come una conca parabolica e cerca di "saltare" direttamente al presunto fondo con un calcolo matematico.
   - *Pregio*: Quando sei già vicino alla valle, trova il punto di minimo in pochissimi passaggi con precisione chirurgica.
   - *Difetto*: Se lo usi quando sei ancora in quota o lontano, l'approssimazione fallisce e rischi di fare un salto nel vuoto (il fit "esplode" o non converge).

**La genialità di Levenberg-Marquardt**:
L'algoritmo ha un "regolatore" interno (chiamato fattore di smorzamento $\lambda$). 
- Se un passo riduce l'errore, l'algoritmo prende fiducia e passa al metodo veloce (Gauss-Newton).
- Se un passo rischia di peggiorare le cose o aumentare l'errore, torna immediatamente cauto (Discesa del Gradiente), fa passi più piccoli e ritrova la traiettoria giusta.

---

### 4. A cosa serve il parametro iniziale `p0` (Initial Guess)?
Poiché i nostri modelli fisici sono **non lineari** (ci sono frazioni con numeri complessi al denominatore, risonanze molto strette, seni e arcotangenti), il paesaggio montuoso presenta molte "buche secondarie" (minimi locali). 

Se lasciassimo partire l'algoritmo da valori a caso (es. $f_0 = 0\text{ Hz}$), l'algoritmo potrebbe incastrarsi nella prima buca che trova e fallire. 

Per questo negli script viene sempre fornita una stima iniziale ragionevole (`p0`):
- Ad esempio, per stimare la risonanza diciamo all'algoritmo: *guarda il punto più alto nei dati sperimentali* (`f0_guess = f_hz[np.argmax(g_lin)]`).
- In questo modo l'esploratore viene paracadutato già sul crinale della montagna giusta, a pochi passi dalla valle corretta.

---

### 5. Dove e come viene usato nei due moduli del progetto

#### A. In [Risposta in frequenza](file:///Users/matteoluca/Downloads/es2m%20progetto/Risposta%20in%20frequenza/analizza_risposta_in_frequenza.py)
1. **Fit completo dello sweep a $V_{dc} = 5.0\text{ V}$** (funzione `model_real_imag` a riga 63):
   - Fitta contemporaneamente **la parte reale e la parte immaginaria** della funzione di trasferimento $T(f)$ del risonatore RLC sommata al feedthrough capacitivo $C_p$.
   - Trova in un colpo solo 6 parametri fisici: la risonanza $f_0$ ($\approx 417.66\text{ kHz}$), il fattore di merito $Q$ ($\approx 2992$), l'ampiezza meccanica $A_{mot}$, la fase residua $\phi_m$ e le componenti della capacità parassita $C_p$ ($\approx 0.89\text{ pF}$).
2. **Fit delle forme d'onda dell'oscilloscopio a $V_{dc} = 0\text{ V}$** (funzione `fit_sine_wave` a riga 94):
   - Fitta una pura sinusoide $y(t) = A \sin(2\pi f t + \phi) + \text{offset}$ sulle tracce temporali dei file `Scope 69` e `Scope 70`.
   - Serve a estrarre con accuratezza sub-campionamento l'ampiezza esatta $A_{in}, A_{out}$ e la frequenza $f$, calcolando il guadagno capacitivo puro senza risonanza meccanica attiva.

#### B. In [Compensazione Hardware](file:///Users/matteoluca/Downloads/es2m%20progetto/Compensazione%20Hardware/analizza_compensazione_hardware.py)
1. **Fit del modulo di ampiezza** (funzione `model_mag` a riga 156):
   - Fitta il modulo lineare della funzione di trasferimento per quantificare la capacità parassita residua sbilanciata ($\Delta C$ in femtofarad) dopo la compensazione hardware con i trimmer nelle configurazioni `Off`, `1` e `2`.
2. **Fit della fase** (funzione `model_phase` a riga 162):
   - Fitta la curva di fase tramite una transizione ad arcotangente $\phi(f) = \phi_{mid} - \frac{\text{span}}{\pi}\arctan\left(2Q \frac{f-f_0}{f_0}\right)$, verificando la tipica rotazione di circa 180° attraverso il polo di risonanza.