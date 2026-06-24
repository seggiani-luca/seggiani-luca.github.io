# Logic Sim
Un editor di circuiti e simulatore logico scritto in JavaScript.

Sono disponibili una [versione statica](https://seggiani-luca.github.io/logic-sim/) da provare nel browser, e la [repository](https://github.com/seggiani-luca/logic-sim).

![un adder a 4 cifre](/pics/logic-sim/screenshot.png)

Un adder a 4 bit che mostra 6 + 4 = 10

## Uso dell'editor
Dal menu dei componenti si può trascinare (cliccando, non trascinando), per inserire nello spazio di lavoro di destra. Sono disponibili i seguenti tipi di componenti:

-   Ingresso/uscita
    -   Porte di ingresso
    -   Porte di uscita
-   Porte logiche
    -   Porte NOT
    -   Porte AND
    -   Porte NAND
    -   Porte OR
    -   Porte NOR
    -   Porte XOR
    -   Porte XNOR
-   Miscellanee
    -   Nodi di testo

Cliccando di nuovo su un componente creato viene visualizzato un pulsante per la rimozione dello stesso.

Cliccando sul pin di uscita di un componente si può creare una connessione col pin di ingressso di un altro componente, mentre cliccando di nuovo sul pin di ingresso si può eliminare una connessione già esistente. Eliminare un componente significa eliminare tutte le sue connessioni.

Cliccando sul LED di una porta di ingresso si può aggiornare il suo valore logico. Le variazioni delle variabili logiche si propagano automaticamente attraverso il circuito fino alle porte di uscita, e vengono visualizzate lungo le connessioni fra componenti, sulla base dei colori:

- Rosso: segnale _basso_;
- Verde: segnale _alto_;
- Grigio: segnale in _alta impedenza_.

I circuiti si possono salvare e caricare da locare, in formato `.json`, usando i pulsanti **Save** e **Load**. Sono disponibili una serie di circuiti di esempio in logica combinatoria e sequenziale.
