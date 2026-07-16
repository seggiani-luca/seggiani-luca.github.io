# 2026 07 04 Come essere pigro mi ha insegnato l'allocazione di memoria

Ho scritto la mia tesi di laurea triennale sull'estensione dispositivo [ATA](https://en.wikipedia.org/wiki/Parallel_ATA) per l'emulatore [micro-sim](/progetti/micro-sim.html).
Prima o poi metterò il link alla tesi qui da qualche parte, ma per la cosa di cui voglio parlare oggi non serve.

## L'idea 

Ho passato una settimana ad implementare il dispositivo ATA stesso, simulandolo solo a livello logico (niente algoritmo SCAN, niente fasi BUSY del disco, solo scritture alla porta comandi che si traducono immediatamente nel disco pronto a ricevere/inviare settori).
Quindi, ho passato un'altra settimana (se non di più) ad implementare il filesystem FAT16, per dimostrare il funzionamento del dispositivo.
Sul FAT16 non collego Wikipedia perché ci sono diecimila versioni e si fa un po' di confusione, ma c'è una buona risorsa [qui](https://8dcc.github.io/programming/understanding-fat.html).

L'idea era che alla fine implementavo sull'API di accesso al filesystem FAT16 un semplice caricatore non rilocante, in modo da dimostrare che dal filesystem si possono caricare programmi.
Sotto avviso del relatore (e visto che il tempo stringeva), però, sono stato dissuaso da questa idea.

Il problema era che volevo comunque delle applicazioni: di base un editor per testare il filesystem, e quindi volevo portare sul sistema un vecchio progetto per un'interprete [TinyBASIC](https://en.wikipedia.org/wiki/Tiny_BASIC) che avevo scritto in passato.
"Nessun problema!" ho pensato - basta mantenere tutte le applicazioni che mi servono in RAM, e saltarci direttamente quando le voglio chiamare.

## Il problema

Il piano si traduceva così: per preparare il firmware di micro-sim (leggere l'[articolo](/progetti/micro-sim.html)) si compila codice C++.
Quindi mi bastava scrivere un header per "applicazione", avere un header centrale con una tabella che associa gli entry point delle applicazioni ai loro nomi, e scansionare tale tabella ogni volta che veniva richiesto un programma.

Il problema si nota se si va a vedere cosa succede quando si compila il programma.
Ciò che fa la suite compilatore, assemblatore e linker (trovati in [questa](github.com/riscv-collab/riscv-gnu-toolchain) repository) è, per quanto io posso capire:
1. Prendere il codice sorgente (C++);
2. Determinare la memoria necessaria per le sezioni statiche (`.data`, `.rodata` e `.bss`);
3. Tradurre il codice in istruzioni macchina;
4. Generare un file ELF contenente le sezioni `.text` (codice), `.data`, `.rodata` e `.bss`, organizzate per il caricamento in memoria.
Ci si aspetta che il lettore sia familiare con il formato [ELF](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format).
Giusto per chiarezza, un ELF è un file binario che contiene *sezioni* di codice o dati, raggruppate in *segmenti* da caricare in memoria ad indirizzi precisi. 
Nel nostro caso, `.data` contiene le variabili statiche che andremo a modificare, `.rodata` quelle in sola lettura (che dichiariamo con `const`), e `.bss` le variabili statiche non inizializzate, che andrebbero comunque inizializzate a zero in RAM.

Questo si sposa perfettamente con l'emulatore, in quanto nello spazio di memoria abbiamo:
1. La EPROM, in sola scrittura, perfetta per contenere le sezioni `.text` e `.rodata` (che comunque non avremmo mai toccato);
2. La RAM, dove dobbiamo copiare la sezione `.data` prima dell'entry point del C++ (il `main`), e dove manteniamo la pila (che comincia dal fondo in maniera tale da lasciare la parte iniziale alla sezione `.data` stessa);
3. La VRAM, che parte inizializzata a zero, e non inizializziamo.

Mi ero lasciato dei commenti nel codice dell'emulatore che dettagliano questa cosa:
```Java
	// expected program headers are:
	// 0) riscv attributes (ignored)
	// 1) text + rodata
	// 2) data (to be loaded in RAM by _start routine)
	// 3) bss (ignored)
	// 4) video (ignored)
	// 5) gnu stack (ignored)
```

Vediamo che abbiamo diversi *segmenti* (non sezioni), organizzati per essere caricati direttamente nelle regioni di memoria che ci interessavano.
1. Ignoriamo il segmento 0, che è specifico al compilatore RISC-V e contiene alcuni attributi;
2. Carichiamo i segmenti 1 e 2 (dati in sola lettura, codice incluso, e dati in lettura/scrittura) nell'EPROM;
3. Ignoriamo il `.bss`, visto che la memoria parte tutta inizializata a zero. Allo stesso modo ignoriamo la memoria video e lo stack GNU (altre cose specifiche al compilatore);
4. Quindi, una routine inclusa nel segmento `.text` copia i dati in lettura/scrittura dall'EPROM alla RAM, e possiamo iniziare l'escuzione.

La routine del punto 4., in codice assembly RISC-V, ha il seguente aspetto:

```asm
.section .start

.extern main 
.extern check_disk 
.global _start

	# routine di avvio
_start:

	# qui si inizializza lo stack
	la sp, __stack_top

	# qui iniziamo a copiare .data in RAM 
	la a0, __data_ram_start
	la a1, __data_ram_end
	la a2, __data_eprom_start

	# questo e' il loop di copia, byte per byte 
_data_cpy_loop:
	beq a0, a1, _data_cpy_end
	
	lb t0, 0(a2)
	sb t0, 0(a0)

	addi a0, a0, 1
	addi a2, a2, 1
	j _data_cpy_loop

_data_cpy_end:

	# qui saltiamo all'entry point! 
	call main 
```

Tutto questo discorso era per dire che, se negli header relativi ad ogni applicazione dichiariamo le nostre variabili statiche, il compilatore felicemente metterà da parte la memoria necessaria nel segmento `.data`, che dovrà essere disponibile in RAM!
Se si ha un caricatore, questo non è un problema, in quanto:
1. I segmenti vengono caricati in memoria (dal caricatore) all'avvio dell'applicazione;
2. Restano in memoria finché l'applicazione esegue;
3. Quindi vengono deallocati quando l'applicazione termina (o insomma si ritorna al chiamante e quello che è in RAM lo possiamo riutilizzare).

Mettiamo però di voler usare il nostro approccio, dove tutti i programmi vengono compilati insieme e noi ci limitiamo a chiamarli.
Il compilatore riseverà felicemente lo spazio nella sezione `.data` di tutti (non sapendo che non eseguiremo mai tutti i programmi contemporaneamente): l'emulatore ha però solo 64 KiB di memoria, che prima o poi finiscono.
Il risultato è che esauriamo lo stack, o peggio, tutta la RAM!

## La "soluzione" 

La soluzione che ho trovato a questo problema è stupida(mente semplice), però mi ha portato a studiare un mucchio di cose interessanti su come gestiamo la memoria nei nostri programmi.
Se non altro, ho trovato un'ottima risorsa [qui](https://www.dgtlgrove.com/p/untangling-lifetimes-the-arena-allocator), che consiglio a tutti.

Mi sono divertito a reimplementare (male) un mucchio di cose della standard library del C, ma una cosa che (per pigrizia) non ho mai voluto implementare in micro-sim è l'heap.
Già ne avrei avuto bisogno quando ho implementato un rudimentale stack di rete (dove l'heap sembra essere la soluzione effettivamente più appropiata): mi sono accontentato di passare tutto per valore.
In questo caso però, sono rimasto soddisfatto dal fatto che effettivamente l'heap non serviva.

Prendiamo l'applicazione X.
Con un heap, il suo ciclo di vita potrebbe essere:
```c
int app_main() {
	void* mem = malloc(QUANTO_BASTA);

	// ...

	free(mem);

	return 0;
}
```

Quindi, all'avvio (quando l'applicazione viene chiamata) si alloca un tot. di memoria, e quando l'applicazione termina, la si libera.
Riflettiamo però su cosa succede dietro le quinte: avere una `malloc()` e una `free()` significa:
1. Avere una regione (grande) di memoria riservata nella RAM, posta ben lontana dallo stack;
2. Mantenere una qualche struttura dati che tenga conto delle regioni di memoria usate e della loro dimensione.

Tutto questo per fare una cosa di base molto semplice: dare tutta la memoria ad un singolo utente per volta.

Possiamo fare la stessa cosa col solo stack: l'idea di fondo dello stack è infatti che creiamo "frame", cioè blocchi dove allochiamo le nostre variabili, uno sopra l'altro.
Questo è esattamente il caso in cui ci troviamo: quando chiamiamo un'applicazione allochiamo la sua memoria, e quando questa termina, vogliamo riprendercela.
Il nostro codice diventa quindi:
```c
int app_main() {
	uint8_t mem[QUANTO_BASTA];

	// ...

	return 0;

	// usciti dal frame la memoria viene deallocata!
}
```

Vediamo come lo stack, anzi come la sintassi stessa del C, esprime perfettamente quello che volevamo (almeno in fase di liberazione della memoria).
Ci siamo resi conto che stavamo cercando di implementare un allocator quando il linguaggio ne aveva già uno incorporato: lo stack.

Una cosa di cui non mi volevo privare erano le variabili globali, per cui, a costo di "sprecare" un po' di memoria per qualche puntatore (in RV32I occupano 32 bit ciascuno), ho deciso di fare una cosa del tipo:
```c

// da qui riferisco
uint8_t* mem;

int app_main() {
	// qui la alloco
	uint8_t _mem[QUANTO_BASTA];
	mem = _mem;

	// ...

	return 0;

	// usciti dal frame la memoria viene deallocata!
}
```

Questa sintassi è un po' brutta (sono sicuro si potrebbe risparmiare un po' di codice attraverso qualche macro), ma esprime bene il concetto: mi mantengo un puntatore globale alla regione di memoria che mi interessa, ma la alloco sullo stack, esattamente quando mi serve.
Questo, unito al fatto che lo stack me lo gestisco da solo (come abbiamo visto prima, tutta la memoria va gestita manualmente), significa che l'intero problema che avevamo all'inizio viene risolto in maniera estremamente semplice.
L'unico rischio è quello di allocare troppa memoria e portare lo stack troppo vicino alla sezione `.data`.
Yuck!

## Da qui in poi 

I più ferrati si saranno resi conto che quello che si va ad implementare è una sorta di allocatore ad arena.
Visto che è interessante anche vedere *come* usiamo questi blocchi di memoria sullo stack una volta allocati, andiamo ad approfondire il discorso degli allocatori.
Useremo, come esempi, la suite di applicazioni che ho inizialmente sviluppato per micro-sim (un clone di PACMAN, un interprete BASIC, e un editor di testo).

### PACMAN

PACMAN (io lo chiamo Risc-man) è il caso più semplice. 
Quando lo avvio, voglio spazio per:
- L'area di gioco stessa;
- I dati su Risc-man;
- I dati sui fantasmini.

Alloco un frame sullo stack e metto tutto lì.
Quando il giocatore ha finito, posso deallocare tutto insieme semplicemente liberando il frame (ovvero ritornando dalla funzione).

### Interprete BASIC

Dell'interprete BASIC ci interessa come allochiamo i dati in memoria, e in particolare:
- I token, cioè i frammenti che compongono le nostre istruzioni (parole chiave come IF, THEN, nomi  di variabile, ecc..);
- Le stringhe, che purtroppo occupano più memoria di qualsiasi token.

Per i token, ho scelto una soluzione semplice: presumo di avere al massimo tot. linee, e per ogni linea tot. token.
Questo è concesso dal fatto che i token sono fatti per essere piccoli.
Proprio per il fatto che sono piccoli, vediamo come trattiamo i token:
```c
struct token {
	tok_type type;

	union {
		// variabili
		char var;

		// operatori
		op_type op;

		// letterali numero
		int num;

		// parole chiave
		key_type key;
		
		// stringhe
		char* str;
	} payload;
}
```

Vediamo che trattiamo i token stringa proprio come se gestissere stringhe allocate sull'heap: ci conserviamo il puntatore, e ci aspettiamo che l'allocazione effettiva venga fatta da qualche altra parte.

La soluzione che usiamo per l'allocazione delle stringhe, però, non è l'heap, ma l'*allocatore ad arena*.
L'idea è sostanzialmente di creare un *altro* piccolo stack, all'interno di un buffer di memoria riservato (che nel nostro caso, per coincidenza, è esso stesso allocato su uno stack).
Forse il codice si spiega meglio da solo:
```c
// array di stringhe
#define MAX_STRLEN 32
#define MAX_STRINGS 128
char (*strings)[MAX_STRLEN];

// indice della prossima stringa da allocare
int cur_string = 0;

// allocatore delle stringhe
char* alloc_string() {
	// controlla di non essere in fondo
	if(cur_string == MAX_STRINGS) return NULL;

	// semplicemente, alloca la prossima
	return strings[cur_string++];
}
```

In questo caso, deallocare tutte le stringhe diventa banalmente semplice: basta deallocare l'intero blocco di memoria che usavamo per l'arena.
Questo è reso *ancora* più semplice dal fatto che, nel nostro specifico caso di applicazione, una volta terminato il programma BASIC possiamo liberare tutta la memoria usata: e lo facciamo (come detto prima) semplicemente uscendo dal frame dello stack.

Nel caso invece avessimo voluto esplicitamente liberare la memoria (magari per eseguire più programmi BASIC in un singolo ciclo di vita dell'interpete, ad esempio in modalità REPL), sarebbe bastato impostare il cursore `cur_string` a zero.

### Editor di testo

L'editor di testo presenta forse il modello più interessante di allocazione della memoria.
Il problema è dato dal fatto che possiamo avere:
1. Un numero non specificato di stringhe;
2. Tutte di una lunghezza non specificata.

L'approccio usato per l'interprete BASIC, delle linee di lunghezza fissa, fallisce in quanto un file di testo arbitrario è molto meno standard di un programma BASIC.
In un programma BASIC non ci sono righe senza token (le saltiamo), e tutte le righe contengono un numero prevedibile di token.
In un file di testo arbitrario possiamo avere 15 righe con un solo carattere, e una riga con 1000 caratteri, senza particolari sorprese, e dobbiamo rappresentarle in memoria così come sono!

La soluzione, dal punto di vista logico, è stata di usare una struttura dati detta *corda*.
Senza andare nel dettaglio, una corda non è altro che una *lista* di buffer di dimensione prefissata, che chiamiamo *pezzi*.
Quando si inizia a digitare una linea, si alloca un primo pezzo.
Quando il buffer del pezzo è pieno, ne si alloca un altro e lo si concatena al primo, e cosi via.
Mantenendo un'array di linee, che punteranno ciascuna ad una corda di pezzi, si riesce ad immagazzinare file di natura qualsiasi, in maniera abbastanza efficiente.
L'idea in codice è:
```c
// un pezzo di corda
#define PIECE_SIZE 32
struct piece {
	char buf[PIECE_SIZE];
	piece* next;
};

// array di linee
#define MAX_LINES 1024
piece** lines;
```

La cosa interessante, però, non è la struttura dati, ma come viene gestita la memoria.
Guardiamo ai nostri pezzi.
Il contratto di utilizzo che abbiamo descritto sopra (si prende un pezzo ogni volta che c'è n'è bisogno per estendere una corda) sembra aderire perfettamente a quello dell'heap!
Infatti, in questo caso, un semplice stack non funzionarebbe.
Si potrebbe ad esempio avere il caso dove si alloca un pezzo A, quindi un pezzo B, e quindi perché è stata modificata una linea bisogna deallocare il pezzo A.
Gli stack questa cosa non la fanno.

Potremmo pensare di doverci rassegnare all'heap.
La soluzione, però, può essere data anche da un allocatore più semplice, che l'*allocatore a pool* (mi rifiuto di tradurre pool in piscina, pozza o quant'altro).

In un allocatore aa pool manteniamo un array base di oggetti, tutti della stessa dimensione (che come sempre allochiamo sullo stack).
Quindi, concediamo ad ogni oggetto di puntare ad un successivo, in maniera da organizzarli in liste: nel nostro caso siamo a cavallo, in quanto i pezzi di corda erano già stati realizzati per questo scopo!
L'idea è quindi di mantenere una lista di *oggetti liberi*: allocare un oggetto significa estrarlo da tale lista, e liberarlo significa metterlo in testa a tale lista.
In codice:

```c
// array di pezzi
#define MAX_PIECES 1024
piece* pieces;

// lista pezzi liberi
piece* pieces_free;

piece* alloc_piece() {
	// estrai dalla testa
	piece* piece = pieces_free;
	if(piece == NULL) utl::panic("Memoria esaurita");
	
	// sposta avanti la lista
	pieces_free = pieces_free->next;

	return piece;
}

void free_piece(piece* piece) {
	// inserisci in testa 
	piece->next = pieces_free;
	pieces_free = piece;	
}
```

Ecco le classiche `malloc()` (che ha perso una `m`) e `free()`, ma senza nessuna traccia di un'heap (nel senso stretto del termine).
Tutto questo per voler essere pigri, e non volerlo implementare.

## Conclusioni

Voglio concludere dicendo che l'heap non è di per se sbagliato: molto spesso però è un arma troppo potente per un problema che può essere anche più semplice (ammazzare un moscerino con un cannone o roba del genere).

Inoltre, le tecniche viste in questo articolo (spiegate in maniera basilare ed implementate in maniera ancora più basilare) compaiono spesso nella programmazione embedded, o comunque in tutti i casi in cui bisogna fare attenzione a come si usa quella risorsa preziosa che è la memoria.
Per questo motivo, spero che questa breve introduzione possa essere stata utile, o almeno abbia incuriosito il lettore su quali modi, oltre alla `malloc()` e la `free()`, esistono per gestire la memoria. 
