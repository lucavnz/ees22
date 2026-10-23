Listed directory es2m%20progetto
Viewed relazione.tex:600-660
Listed directory Ampiezza_Frequenza
Searched for "lorentz"
Viewed analizza_ringdown.py:285-340
Viewed risultati_ringdown.csv:1-27
Ran command: `python3 -c "
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

df = pd.read_csv('Ampiezza_Frequenza/risultati_ringdown.csv')
freqs = df['Frequenza_in_Hz'].values
a0 = df['A0_mV'].values

def lorentz_profile(f, a_max, f0, bw):
    return a_max / np.sqrt(1.0 + (2.0 * (f - f0) / bw)**2)

popt, pcov = curve_fit(lorentz_profile, freqs, a0, p0=[37.0, 417835.0, 150.0])
perr = np.sqrt(np.diag(pcov))
print(f'A_max: {popt[0]:.4f} +/- {perr[0]:.4f} mV')
print(f'f0:    {popt[1]:.4f} +/- {perr[1]:.4f} Hz')
print(f'bw:    {popt[2]:.4f} +/- {perr[2]:.4f} Hz')
"`
Ran command: `python3 -c "
import csv
import numpy as np
from scipy.optimize import curve_fit

freqs, a0 = [], []
with open('Ampiezza_Frequenza/risultati_ringdown.csv') as f:
    r = csv.DictReader(f)
    for row in r:
        freqs.append(float(row['Frequenza_in_Hz']))
        a0.append(float(row['A0_mV']))

freqs = np.array(freqs)
a0 = np.array(a0)

def lorentz_profile(f, a_max, f0, bw):
    return a_max / np.sqrt(1.0 + (2.0 * (f - f0) / bw)**2)

popt, pcov = curve_fit(lorentz_profile, freqs, a0, p0=[37.0, 417835.0, 150.0])
perr = np.sqrt(np.diag(pcov))
print(f'A_max: {popt[0]:.4f} +/- {perr[0]:.4f} mV')
print(f'f0:    {popt[1]:.4f} +/- {perr[1]:.4f} Hz')
print(f'bw:    {popt[2]:.4f} +/- {perr[2]:.4f} Hz (Delta f)')
print(f'Q_factor: {popt[1]/popt[2]:.1f}')
"`
Used tool: manage_task
Viewed relazione.tex:540-600
Listed directory Paper
Viewed relazione.tex:660-730

Ecco una spiegazione completa, fisica e computazionale di quella formula, di cosa fa esattamente lo script e di come definire in modo rigoroso tutti i parametri nella tua relazione.

---

### 1. Cos'è quella formula e perché ha questa forma? (Origine Fisica)

Nel tuo circuito, il MEMS è polarizzato in continua con $V_{\text{DC}} = 5\,\text{V}$ ed eccitato con una tensione alternata $v_{\text{in}}(t) = V_{\text{AC}}\sin(2\pi f_{\text{in}} t)$ con $V_{\text{AC}} = 100\,\text{mV}$. Il comportamento dinamico del risonatore attorno al primo modo di flessione è modellato con il circuito equivalente **RLC serie** ($R_m, L_m, C_m$) in parallelo alla capacità parassita $C_p$:

1. **L'ammettenza del ramo motrice RLC** è data da:
   $$Y_m(\omega) = \frac{1}{R_m + j\left(\omega L_m - \frac{1}{\omega C_m}\right)}$$
2. In prossimità della risonanza propria $\omega_0 = 2\pi f_0 = \frac{1}{\sqrt{L_m C_m}}$, con scostamento $\Delta\omega = \omega - \omega_0 \ll \omega_0$, la reattanza si linearizza:
   $$\omega L_m - \frac{1}{\omega C_m} = L_m \frac{\omega^2 - \omega_0^2}{\omega} \approx 2 L_m (\omega - \omega_0) = 4\pi L_m (f_{\text{in}} - f_0)$$
3. Il modulo dell'ammettenza vale quindi:
   $$|Y_m(f_{\text{in}})| \approx \frac{1}{\sqrt{R_m^2 + \left[4\pi L_m (f_{\text{in}} - f_0)\right]^2}} = \frac{1/R_m}{\sqrt{1 + \left( \frac{4\pi L_m}{R_m} (f_{\text{in}} - f_0) \right)^2}}$$
4. Definiamo la **larghezza di banda a metà potenza ($-3\,\text{dB}$)** del risonatore:
   $$\Delta f = \frac{R_m}{2\pi L_m} = \frac{f_0}{Q}$$
   da cui:
   $$\frac{4\pi L_m}{R_m} = \frac{2}{\Delta f}$$
5. La corrente motrice $i_m(t)$ entra nel TIA ($v_{\text{out,TIA}} = -R_f i_m$) e viene amplificata dall'inverting amplifier ($G_{\text{IA}} = -10$), per una transresistenza totale $R_{\text{trans}} = 10 R_f = 5.0\,\text{M}\Omega$.
   L'ampiezza iniziale del segnale al momento dello spegnimento ($t=0$) è l'ampiezza a regime stazionario:
   $$A_0(f_{\text{in}}) = R_{\text{trans}} \cdot |Y_m(f_{\text{in}})| \cdot V_{\text{AC}}$$
   Ponendo l'ampiezza massima di picco $A_{\max} = R_{\text{trans}} \frac{V_{\text{AC}}}{R_m}$, otteniamo esattamente l'**espressione lorentziana**:
   $$A_0(f_{\text{in}}) = \frac{A_{\max}}{\sqrt{1 + \left( \frac{2(f_{\text{in}} - f_0)}{\Delta f} \right)^2}}$$

---

### 2. Cosa sono $A_{\max}$, $f_0$ e $\Delta f$?

Nella relazione mancano queste definizioni, che vanno inserite subito sotto l'equazione:

* **$f_{\text{in}}$**: la frequenza della forzante sinusoidale applicata prima dello spegnimento del gate.
* **$A_0(f_{\text{in}})$**: l'ampiezza iniziale dell'oscillazione libera (a $t=0$) estratta dalla traccia di ring-down.
* **$A_{\max}$**: l'**ampiezza massima teorica** al centro esatto della risonanza ($f_{\text{in}} = f_0$).
* **$f_0$**: la **frequenza centrale di risonanza** meccanica del primo modo.
* **$\Delta f$** (chiamato `bw` nello script per *bandwidth*): la **larghezza di banda a $-3\,\text{dB}$** (Full Width at Half Maximum per la potenza, o fattore $1/\sqrt{2} \approx 0.707$ per l'ampiezza). È l'intervallo di frequenza attorno al picco entro cui l'ampiezza soddisfa $A_0 \ge \frac{A_{\max}}{\sqrt{2}}$.
* Dal rapporto tra frequenza centrale e banda si ricava direttamente il fattore di merito nel dominio della frequenza:
  $$Q = \frac{f_0}{\Delta f}$$

---

### 3. Cosa fa esattamente lo script? Li trova tutti lo script?

**Sì, lo script trova tutti e tre i parametri in automatico!**

Nel file [analizza_ringdown.py:L298-L306](file:///Users/matteoluca/Downloads/es2m%20progetto/Ampiezza_Frequenza/analizza_ringdown.py#L298-L306):
1. **Passaggio nel tempo (su ciascuno dei 25 file di misura):**
   Per ogni frequenza $f_{\text{in}}$, lo script isola la risposta libera post-spegnimento (scartando i primi $20\,\mu\text{s}$ dovuti alla corrente impulsiva attraverso $C_p$), individua i picchi e fitta l'esponenziale:
   $$A(t) = A_0 e^{-t/\tau}$$
   In questo modo estrae una coppia sperimentale $(f_{\text{in}}, A_0)$ per ciascuna frequenza (salvate in [risultati_ringdown.csv](file:///Users/matteoluca/Downloads/es2m%20progetto/Ampiezza_Frequenza/risultati_ringdown.csv)).
2. **Passaggio in frequenza (Grafico 1):**
   Lo script prende l'array delle 25 frequenze e delle 25 ampiezze $A_0$ e applica la funzione di fitting non-lineare ai minimi quadrati (`scipy.optimize.curve_fit`):
   ```python
   def lorentz_profile(f, a_max, f0, bw):
       return a_max / np.sqrt(1.0 + (2.0 * (f - f0) / bw)**2)

   popt_l, _ = curve_fit(lorentz_profile, freqs, a0_vals, p0=[37.0, 417835.0, 150.0])
   ```
   I parametri restituiti dal fit numerico su [risultati_ringdown.csv](file:///Users/matteoluca/Downloads/es2m%20progetto/Ampiezza_Frequenza/risultati_ringdown.csv) sono:
   * **$A_{\max} = 37.26 \pm 0.46\,\text{mV}$** (il picco teorico della curva continua)
   * **$f_0 = 417836.2 \pm 2.3\,\text{Hz} \approx 417.84\,\text{kHz}$**
   * **$\Delta f = 175.1 \pm 7.0\,\text{Hz}$**
   * Fattore di merito da fit frequenziale: $Q = \frac{f_0}{\Delta f} \approx \frac{417836}{175.1} \approx \mathbf{2386}$

> **Attenzione a una svista presente in [relazione.tex](file:///Users/matteoluca/Downloads/es2m%20progetto/Relazione/relazione.tex#L632):**
> Nel testo attuale della relazione hai scritto:
> *"Il picco si ha in corrispondenza di $f_{in} = 417.83\,\text{kHz}$, con ampiezza $A_0 = 36.13\,\text{mV}$"*.
> Questo valore ($36.13\,\text{mV}$) è il punto discreto misurato più alto (il file `Scope 5`), **non** il parametro $A_{\max}$ del fit lorentziano ($37.26\,\text{mV}$ a $417.84\,\text{kHz}$). È buona norma scientifica distinguere il massimo campionato discreto dai parametri ottimali del fit continuo.

---

### 4. Come integrare e correggere [relazione.tex](file:///Users/matteoluca/Downloads/es2m%20progetto/Relazione/relazione.tex#L618-L644)

Per rendere la sottosezione 7.2 chiara e completa, ti propongo di aggiornare quel paragrafo in questo modo:

```latex
\subsection{Risposta in ampiezza del risonatore (\texorpdfstring{$A_0$}{A0} vs \texorpdfstring{$f_{\text{in}}$}{fin})}
\label{subsec:risposta_ampiezza}

In Fig.~\ref{fig:ampiezza_vs_frequenza} è riportata l'ampiezza iniziale $A_0$ del ring-down, estrapolata all'istante di spegnimento della forzante ($t=0$), in funzione della frequenza di eccitazione $f_{\text{in}}$.

\noindent La linea tratteggiata rossa rappresenta il fit lorentziano non lineare ai minimi quadrati, caratterizzato dalla curva di risonanza universale del secondo ordine:
\begin{equation}
    A_0(f_{\text{in}}) = \frac{A_{\max}}{\sqrt{1 + \left( \frac{2(f_{\text{in}} - f_0)}{\Delta f} \right)^2}}
\end{equation}
dove:
\begin{itemize}
    \item $A_{\max}$ è l'ampiezza di picco in tensione alla frequenza di risonanza centrale;
    \item $f_0$ è la frequenza di risonanza del primo modo flessionale;
    \item $\Delta f$ è la larghezza di banda a metà potenza (a $\SI{-3}{\decibel}$ in ampiezza, cioè per $A_0 = A_{\max}/\sqrt{2}$).
\end{itemize}

\vspace{0.2cm}
\noindent I parametri ottimali ottenuti dalla regressione sono:
\begin{equation}
    f_0 = \SI{417.84}{\kilo\hertz}, \quad A_{\max} = \SI{37.26}{\milli\volt}, \quad \Delta f = \SI{175.1}{\hertz}
\end{equation}
Il singolo punto sperimentale campionato più prossimo al vertice corrisponde a $f_{\text{in}} = \SI{417.83}{\kilo\hertz}$ con ampiezza misurata $A_0 = \SI{36.13}{\milli\volt}$. 

Dalla larghezza di banda $\Delta f$ possiamo ricavare una prima stima del fattore di merito nel dominio della frequenza:
\begin{equation}
    Q = \frac{f_0}{\Delta f} = \frac{\SI{417836}{\hertz}}{\SI{175.1}{\hertz}} \approx 2386
\end{equation}
Dato che la transresistenza complessiva del circuito di condizionamento è $R_{\text{trans}} = \SI{5.0}{\mega\ohm}$, possiamo ricavare l'ampiezza della corrente motrice di picco $i_{m, \max}$ che fluisce dal terminale di sense del MEMS alla risonanza:
\begin{equation}
    i_{m, \max} = \frac{A_{\max}}{R_{\text{trans}}} = \frac{\SI{37.26}{\milli\volt}}{\SI{5.0}{\mega\ohm}} \approx \SI{7.45}{\nano\ampere}
\end{equation}
Allontanandosi di appena $\pm \SI{500}{\hertz}$ dalla risonanza, l'ampiezza di oscillazione crolla a valori inferiori a $\SI{5}{\milli\volt}$, confermando l'elevata selettività del dispositivo.
```

Se desideri, posso procedere ad applicare direttamente questa modifica in [relazione.tex](file:///Users/matteoluca/Downloads/es2m%20progetto/Relazione/relazione.tex).