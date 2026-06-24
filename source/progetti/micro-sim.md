# Micro Sim
Un emulatore per un sistema basato su [RISC-V](https://github.com/seggiani-luca/micro-sim/blob/main/riscv.org).

![hello-world](/pics/micro-sim/filesystem_term.png)

Visualizzazione di un file system 

## Introduzione

L'emulatore simula un sistema con processore ad architettura RISC-V a 32 bit, in particolare basato sull'ISA *RV32I*. Il codice sorgente è scritto in *Java*.
Sono disponibili il sorgente dell'emulatore e una piccola libreria per lo sviluppo del firmware di sistema nella [repository](https://github.com/seggiani-luca/micro-sim). 

Le componenti simulate sono:
-   Processore che implementa l'ISA RV32I;
-   Spazio di memoria a 32 bit, composto da EPROM in sola lettura, RAM e VRAM;
-   Supporto per interfacce simulate, e.g. video, tastiera, ecc...

Il firmware (caricato nelle EPROM simulate) dei sistemi emulati deve essere compilato o assemblato per architettura RISC-V, ISA RV32I. Per compilare il proprio firmware viene resa disponibile una libreria scritta in C++, e file di configurazione per la toolchain [riscv-gnu-toolchain](https://github.com/riscv-collab/riscv-gnu-toolchain) (basata sulla comune toolchain GNU).

Si possono eseguire più istanze concorrenti del sistema, dove ognuna viene simulata nel dettaglio dei suoi componenti (processore, memoria, ecc\...). La configurazione del sistema (cioè la disposizione delle regioni di memoria e dei dispositivi) è fissa.

Le componenti gestite dall'emulatore per ogni istanza del sistema simulato sono:

-   Un processore che implementa l'ISA RV32I. Questa prevede le istruzioni minime definite da RISC-V, ovvero operazioni aritmetiche, accesso alla memoria, esecuzione condizionale e chiamate di sistema tramite le primitive `EBREAK` ed `ECALL`. Il processore viene modellizzato con un approccio a coda di micro-operazioni, dove la macchina a stati viene ridotta ad un esecutore sequenziale;
-   Spazio di memoria a 32 bit, composto da EPROM in sola lettura, RAM e VRAM in sola scrittura. Il firmware fornito all'emulatore in formato ELF viene caricato nella memoria EPROM dei sistemi simulati, prima dell'avvio della simulazione;
-   Supporto per dispositivi di I/O mappati in memoria, e.g. video, tastiera, ecc\... Questi possono essere completamente *sincroni* al bus locale del processore (come ad esempio la *tastiera*), o operare in maniera *asincrona* su thread separati rispetto a quello del processore, in modo da simulare interazioni concorrenti (come ad esempio il *timer*).

    I dispositivi disponibili sul sistema sono:
    -   Dispositivo *tastiera* *PS/2*, con supporto parziale allo scan set 1 dell'IBM PC AT. A questo vengono indirizzati i caratteri digitati sulla finestra grafica dell'emulatore;
    -   Dispositivo *video* in modalità testo, 80 per 30 caratteri, con supporto alla *Code Page 437*. Il framebuffer renderizzato da questo viene disegnato sulla finestra grafica;
    -   Dispositivo *timer* a 3 canali programmabile dal processore, ispirato dal *PIT* dell'IBM PC AT;
    -   Dispositivo di *rete* per la trasmissione seriale ispirata da *RS-232*. Permette di simulare la comunicazione fra più istanze disposte secondo una topologia *a stella* basata su un hub centrale.

L'emulatore è pensato per essere *interattivo*: lo stato delle simulazioni viene visualizzato attraverso delle *interfacce utente*, ovvero una finestra grafica per simulazione, ed una shell di debug condivisa. Si può interagire con la finestra grafica (e quindi con il sistema simulato) come con una qualsiasi riga di comando, e osservare il comportamento ad un maggiore livello di dettaglio dalla shell di debug.

## Uso dell'emulatore

Si interagisce con l'emulatore attraverso la riga di comando, fornendo come argomenti i parametri da usare per configurare l'emulatore stesso ed inizializzare e le simulazioni.

![hello-world](/pics/micro-sim/hello_world_win.png)

Schermata di Hello, World!

Gli argomenti supportati sono:

-   `-e`: indica il percorso della directory delle EPROM. All'avvio, l'emulatore scansiona questa directory per file ELF, e per ciascuno istanzia una simulazione, caricandone i contenuti nell'EPROM del sistema simulato. Questo permette di lanciare più simulazioni concorrenti, ognuna con la propria immagine dell'EPROM all'avvio. Di default, questo percorso è configurato come `emulator/data/eprom`;
-   `-d`: indica se abilitare la shell di debug all'avvio dell'emulatore. Questa fornisce alcune funzionalità di debugging durante l'esecuzione, fra cui la possibilità di fare `step` a livello di micro-operazioni, analizzare e modificare il contenuto della memoria a tempo di esecuzione, ed arrestare/ripristinare i thread di esecuzione.
    Se non si fornisce l'argomento `-d`, il firmware del sistema simulato può comunque lanciare la shell di debug in qualsiasi momento eseguendo l'istruzione `EBREAK` (che viene interpretata come \"chiamata ad ambiente\");
-   `-s`: configura la scala di un pixel della finestra grafica mostrata a schermo, che deve essere un numero intero maggiore di 0.

Prima dell'avvio delle simulazioni, l'emulatore crea una finestra grafica per simulazione. Questa viene collegata al dispositivo tastiera (cioè vi vengono reindirizzati i caratteri digitati con la finestra selezionata) e al dispositivo video (cioè sulla finestra viene mostrato il framebuffer). Una finestra grafica tipica dell'emulatore viene mostrata in figura. Nell'esempio, viene caricato un firmware contenente un'implementazione del *TinyBASIC*, quindi viene inserito nella memoria del sistema simulato un semplice programma di \"Ciao, mondo!\" in BASIC, e ne viene richiesta l'esecuzione.
