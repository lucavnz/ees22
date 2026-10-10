Ran command: `python3 -c "
import pypdf
reader = pypdf.PdfReader('Paper/Frangi_2023.pdf')
# Let's search for Fig 1 caption and text around electrode layout
print('=== FRANGI 2023 PAGE 4 ===')
print(reader.pages[3].extract_text()[:3000])
"`
Ran command: `python3 -c "
import pypdf
reader = pypdf.PdfReader('Paper/A15_2026_IEEE_Sensors_Letters.pdf')
print('=== IEEE SENSORS LETTERS PAGE 2 ===')
print(reader.pages[1].extract_text()[:2500])
"`
Ran command: `python3 -c "
import pypdf
reader = pypdf.PdfReader('Paper/Frangi_2023.pdf')
page4 = reader.pages[3]
for count, image_file_object in enumerate(page4.images):
    with open(f'Paper/frangi_p4_img_{count}.png', 'wb') as fp:
        fp.write(image_file_object.data)
    print(f'Extracted Paper/frangi_p4_img_{count}.png')
"`
Viewed frangi_p4_img_0.png:1-800
Viewed relazione.tex:130-165
Viewed relazione.tex:280-330
Edited relazione.tex
Viewed relazione.tex:140-160
Edited relazione.tex
Ran command: `pdflatex -interaction=nonstopmode relazione.tex && pdflatex -interaction=nonstopmode relazione.tex`
Edited relazione.tex
Ran command: `pdflatex -interaction=nonstopmode relazione.tex`

Hai toccato due punti **fondamentali e acutissimi**, che dimostrano che stai davvero visualizzando la fisica del dispositivo!

Vediamoli nel dettaglio, uno per uno, spiegando la realtà del silicio e perché la matematica torna perfettamente.

---

### 1. Il Dubbio sugli Elettrodi: "Come sono fatti? Si annullano a vicenda?"

#### A. Come è fatto DAVVERO il risonatore (la foto SEM del paper)
Nel modello schematizzato spesso si disegna una trave con un elettrodo sopra e uno sotto, ma se guardiamo la foto reale al microscopio elettronico SEM del paper ([`Paper/frangi_p4_img_0.png`](file:///Users/matteoluca/Downloads/es2m%20progetto/Paper/frangi_p4_img_0.png), Fig. 1 di Frangi):
- La struttura mobile (in blu) **non è una sola trave dritta**, ma un **telaio a doppio arco chiuso**: sono **due archi ricurvi paralleli** uniti insieme agli estremi (agli incastri) e collegati al centro da un traversino rigido di rinforzo.
- Questo telaio forma una "fessura" interna tra i due archi!
- Gli elettrodi fissi sono disposti così:
  - **Elettrodi di DRIVE (verdi):** sono posizionati **all'esterno dell'arco superiore** (sia a sinistra che a destra).
  - **Elettrodi di SENSE (rossi):** sono posizionati **all'interno della fessura tra i due archi** e **all'esterno dell'arco inferiore**!
  - **Elettrodi di TUNING (azzurri, $V_T = 0\text{ V}$):** nella parte centrale superiore.
  - **Elettrodi DUMMY (arancioni, a $V_{\text{DC}}$):** nella parte centrale inferiore.

#### B. Perché non si annullano a vicenda?
Sembrano simmetrici, ma hanno **due compiti fisici completamente diversi**:

1. **Il DRIVE è un ATTUATORE (Tensione $\to$ Forza):**
   - Il segnale alternato d'ingresso $v_{\text{in}}(t)$ è applicato **SOLO ed ESCLUSIVAMENTE all'elettrodo di DRIVE**.
   - L'elettrodo di Sense NON riceve alcun generatore di tensione forzante AC: il Sense è collegato al morsetto invertente del TIA, che si trova a massa virtuale fissa ($0\text{ V}$).
   - Quindi, chi sposta la trave? **Solo il Drive!** Quando $v_{\text{in}}(t)$ oscilla, la forza forzante che fa partire il moto è generata unicamente dal lato Drive.

2. **Il SENSE è un SENSORE (Velocità $\to$ Corrente):**
   - Quando la trave si muove di $x(t)$ (ad esempio si sposta verso l'alto, verso il Drive):
     - La distanza tra trave e Drive si riduce $\implies$ aumenta la capacità di Drive.
     - Contemporaneamente, la distanza tra trave e Sense aumenta $\implies$ diminuisce la capacità di Sense ($dC_s / dt < 0$).
   - Mezzo periodo dopo, la trave torna indietro e va verso il basso:
     - La distanza verso il Sense si riduce $\implies$ la capacità di Sense aumenta ($dC_s / dt > 0$).
   - La corrente che entra nel TIA è:
     $$i_s(t) = V_{\text{DC}} \frac{dC_s}{dt}$$
   - Non c'è nessuna cancellazione: il Sense converte fedelmente l'avvicinamento e l'allontanamento continuo della trave in una corrente alternata sinusoidale $i_s(t)$ a $417\text{ kHz}$.

3. **Perché nel modello RLC li raggruppiamo in un solo blocco?**
   Tutti i pezzetti di silicio dell'elettrodo di Drive sono collegati in parallelo metallicamente allo stesso pad di ingresso ($v_{\text{in}}$). Tutti i pezzetti dell'elettrodo di Sense sono collegati insieme al pad di uscita verso il TIA.  
   L'integrale della riduzione modale (ROM) somma le aree di tutte le facce affacciate e ti restituisce un unico coefficiente complessivo:
   $$\eta = V_{\text{DC}} \left.\frac{\partial C}{\partial x}\right|_0$$

---

### 2. Il Dubbio sullo *Spring Softening*: "C'è softening anche per colpa di $V_{\text{AC}}$? Lo trascuriamo?"

**La risposta è: SÌ, fisicamente esiste uno softening dovuto ad AC, ma è TOTALMENTE TRASCURABILE (inferiore allo $0.04\%$), ecco la dimostrazione matematica:**

Prendiamo la tensione istantanea al quadrato ai capi del gap:
$$V(t) = V_{\text{DC}} - v_{\text{in}}(t) = V_{\text{DC}} - V_{\text{AC}} \sin(\omega t)$$
Facendo il quadrato:
$$V^2(t) = \underbrace{V_{\text{DC}}^2}_{\text{Termine 1 (DC)}} - \underbrace{2 V_{\text{DC}} V_{\text{AC}} \sin(\omega t)}_{\text{Termine 2 (AC lineare)}} + \underbrace{V_{\text{AC}}^2 \sin^2(\omega t)}_{\text{Termine 3 (AC quadratico)}}$$

La forza totale sullo spostamento è $F_e \propto \frac{1}{2} \left.\frac{\partial^2 C}{\partial x^2}\right|_0 V^2(t) \cdot x(t)$.  
Vediamo cosa fanno i tre termini sulla rigidezza:

#### Termine 1: $V_{\text{DC}}^2$ (Softening Statico - Il vero protagonista)
È una costante nel tempo. Riduce permanentemente la costante elastica:
$$k_{e, \text{DC}} = \frac{1}{2} \left.\frac{\partial^2 C}{\partial x^2}\right|_0 V_{\text{DC}}^2$$
Questo è il motivo per cui aumentando $V_{\text{DC}}$ da $5\text{ V}$ a $10\text{ V}$ vedi il picco di risonanza spostarsi da $417.8\text{ kHz}$ a valori inferiori (*spring softening statico*).

#### Termine 3: $V_{\text{AC}}^2 \sin^2(\omega t) = \frac{V_{\text{AC}}^2}{2}[1 - \cos(2\omega t)]$
Questo termine ha una parte continua $\frac{1}{2} V_{\text{AC}}^2$ che potrebbe dare un ulteriore softening statico.  
Ma confrontiamo i numeri delle nostre misure reali di laboratorio:
- $V_{\text{DC}} \ge 5\text{ V}$
- $V_{\text{AC}} \approx 100\text{ mV} = 0.1\text{ V}$
Facciamo il rapporto tra i due effetti:
$$\frac{V_{\text{AC}}^2}{V_{\text{DC}}^2} = \left(\frac{0.1}{5}\right)^2 = \frac{0.01}{25} = \frac{1}{2500} = 0.04\%$$
Lo softening introdotto da $V_{\text{AC}}^2$ è **meno di 4 parti su 10.000** rispetto a quello di $V_{\text{DC}}$! È totalmente invisibile all'oscilloscopio, abbondantemente al di sotto dell'incertezza strumentale.

#### Termine 2: $-2 V_{\text{DC}} v_{\text{in}}(t) \cdot x(t)$ (Softening dinamico intra-periodo / Modulazione parametrica)
Questo termine moltiplica $v_{\text{in}}(t)$ per $x(t)$:
$$v_{\text{in}}(t) \cdot x(t) = V_{\text{AC}} \sin(\omega t) \cdot X \cos(\omega t + \phi) \propto V_{\text{AC}} X \sin(2\omega t + \dots)$$
- Questo termine fa oscillare la rigidezza della trave nel tempo a frequenza **doppia ($2\omega$)**: in fisica si chiama **eccitazione parametrica** (governata dall'equazione di Mathieu).
- In regime di **piccolo segnale** (spostamenti di pochi nanometri), questo termine genera solo microscopiche armoniche superiori a frequenza $2\omega$, con ampiezza insignificante rispetto alla risposta fondamentale a $\omega$.
- Nel modello lineare del ramo RLC serie a frequenza $\omega$, questo termine viene legittimamente trascurato perché è un effetto non lineare di ordine superiore. Diventa importante solo se piloti il MEMS a grandissimo segnale (regime non lineare di Duffing, di cui hai i grafici nella presentazione!) oppure se ecciti intenzionalmente a $2\omega_0$ per ottenere amplificazione parametrica.

---

### Dove trovare tutto questo nella Relazione

Ho già inserito e formalizzato entrambe queste spiegazioni direttamente nel documento:
- In **Sezione 1.4**: *"Perché gli Elettrodi di Drive e Sense non si annullano a vicenda?"*
- In **Sezione 4.3**: *"Esiste uno Spring Softening Dinamico dovuto a $v_{\text{in}}(t)$ (AC)?"*

Il documento aggiornato è stato ricompilato ed è pronto in:
- Sorgente LaTeX: **[`Relazione/relazione.tex`](file:///Users/matteoluca/Downloads/es2m%20progetto/Relazione/relazione.tex)**
- PDF compilato: **[`Relazione/relazione.pdf`](file:///Users/matteoluca/Downloads/es2m%20progetto/Relazione/relazione.pdf)**