# Regole di Progetto e Vincoli di Comportamento dell'Agente

## 1. Isolamento della Memoria e delle Sessioni
- **NON cercare MAI, NON leggere e NON fare MAI riferimento** a script, file, log, cronologie o conversazioni precedenti memorizzate nella memoria dell'IDE, nei log di sistema o in cartelle esterne alla repository.
- **È severamente vietato** cercare o riutilizzare codice o frammenti provenienti da altre sessioni passate.

## 2. Esclusività della Repository Corrente
- L'assistente deve considerare e utilizzare **ESCLUSIVAMENTE** i file e gli script che sono fisicamente ed esplicitamente presenti all'interno della cartella di lavoro (repository) corrente.
- Se uno script non è presente nella cartella corrente, l'assistente deve considerarlo inesistente.

## 3. Sviluppo Diretto e Trasparenza
- Qualsiasi nuovo algoritmo, script o analisi deve essere sviluppato **da zero** basandosi unicamente:
  1. Sui dati grezzi e sui documenti presenti in questa repository.
  2. Sulle istruzioni fornite direttamente dall'utente nella chat attiva.
- Ogni passaggio logico, fisico e computazionale deve essere spiegato in modo semplice, trasparente e verificabile, senza dare nulla per scontato.
