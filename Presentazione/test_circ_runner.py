import subprocess

circ_tex = r'''\documentclass[aspectratio=169, 10pt]{beamer}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{amsmath, amssymb}
\usepackage{circuitikz}
\usetikzlibrary{calc}
\usetheme{default}
\usecolortheme{dove}
\setbeamertemplate{navigation symbols}{}

\begin{document}
\begin{frame}{Funzione di trasferimento complessiva}
\centering
\resizebox{0.92\textwidth}{!}{%
\begin{circuitikz}[scale=0.85, transform shape, line width=0.7pt]
  % Ingresso Vin
  \draw (-0.8, 0.3) node[left] {$v_{in}(t)$} to[short, o-] (0.2, 0.3);
  \draw (0.2, 0.3) -- (0.2, 1.2);
  \draw (0.2, 0.3) -- (0.2, -0.6);
  
  % Ramo RLC MEMS (in alto)
  \draw (0.2, 1.2) to[R, l=$R_m$] (1.5, 1.2)
                   to[L, l=$L_m$] (2.7, 1.2)
                   to[C, l=$C_m$] (3.9, 1.2) -- (4.4, 1.2);
  \node[above, font=\scriptsize] at (2.2, 1.6) {Ramo serie MEMS};

  % Ramo Cp (in basso)
  \draw (0.2, -0.6) to[C, l_=$C_p$] (3.9, -0.6) -- (4.4, -0.6);
  \node[below, font=\scriptsize] at (2.2, -1.0) {Capacit\`a parassita diretta};

  % Connessione al nodo di sense
  \draw (4.4, 1.2) -- (4.4, -0.6);
  \draw (4.4, 0.3) to[short, -*] (5.2, 0.3) node[above] {$V^-$};
  
  % Cin verso massa
  \draw (5.2, 0.3) to[C, l_=$C_{\text{in}}$, *-] (5.2, -1.8) node[ground]{};

  % TIA OPA656
  \node[op amp, anchor=-] (opamp1) at (6.8, 0.3) {};
  \node[font=\scriptsize, above=1pt] at (opamp1.north) {OPA656};
  \draw (opamp1.+) -- ++(-0.2,0) node[ground]{};

  % Retroazione TIA (Rf // Cf)
  \draw (5.2, 0.3) -- (5.2, 1.8) -- (5.8, 1.8);
  \draw (5.8, 2.2) to[R, l=$R_f$] (7.4, 2.2);
  \draw (5.8, 1.4) to[C, l_=$C_f$] (7.4, 1.4);
  \draw (5.8, 2.2) -- (5.8, 1.4);
  \draw (7.4, 2.2) -- (7.4, 1.4);
  \draw (7.4, 1.8) -| (opamp1.out) to[short, *-] ++(0.3, 0) coordinate (v1);
  \node[above, font=\scriptsize] at (opamp1.out) {$V_{\text{out1}}$};

  % Secondo stadio AD817 (invertente G = -10)
  \draw (v1) to[R, l=$R_1$, a=100\,\Omega] ++(1.8, 0) coordinate (in2);
  \node[op amp, anchor=-] (opamp2) at ($(in2) + (1.2, 0)$) {};
  \node[font=\scriptsize, above=1pt] at (opamp2.north) {AD817};
  \draw (opamp2.+) -- ++(-0.2,0) node[ground]{};

  % Retroazione AD817 (R2)
  \draw (in2) to[short, *-] ++(0, 1.2) to[R, l=$R_2$, a=1\,\text{k}\Omega] ++(1.8, 0) -| (opamp2.out);
  
  % Uscita finale
  \draw (opamp2.out) to[short, *-o] ++(0.6, 0) node[right] {$V_{\text{out}}$};
  \node[below, font=\scriptsize] at ($(opamp2.out)+(0.3, -0.2)$) {$G = -10$};
\end{circuitikz}
}

\vspace{0.4em}
{\small\textbf{Funzione di trasferimento complessiva ($2^\circ$ ordine sottosmorzato):}}
{\footnotesize
\[
  H(s) = \frac{V_{\text{out}}(s)}{I_{\text{in}}(s)} = \frac{10 \cdot R_f}{1 + s \left( R_f C_f + \frac{1}{\omega_t} \right) + s^2 \frac{R_f (C_{\text{in}} + C_f)}{\omega_t}}
\]
}

\vspace{-0.2em}
\footnotesize
\begin{itemize}
  \setlength{\itemsep}{0.2em}
  \item $C_{\text{in}}$ (somma di parassite verso massa) e $C_f$ (capacit\`a parassita di $R_f$) riducono il margine di fase dell'OPA656.
  \item Dinamica risultante: sistema del $2^\circ$ ordine sottosmorzato ($\zeta \approx 0.25$), responsabile del ringing a $f_d \approx 600\text{ kHz}$.
\end{itemize}
\end{frame}
\end{document}
'''

with open('test_circ.tex', 'w') as f:
    f.write(circ_tex)

res = subprocess.run(['pdflatex', '-interaction=nonstopmode', 'test_circ.tex'], capture_output=True, text=True)
print('Compilazione circ 2:', res.returncode)
if res.returncode == 0:
    subprocess.run(['sips', '-s', 'format', 'png', 'test_circ.pdf', '--out', 'test_circ.png'], capture_output=True)
    print('Immagine generata con successo!')
else:
    print(res.stdout[-1500:])
