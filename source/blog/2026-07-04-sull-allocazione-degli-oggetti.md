# 2026 07 04 Sull'allocazione degli oggetti

Qualche giorno fa ho scritto qualcosa sul rendering [3D](/blog/2026-06-28-esperimenti-3d.html) e su [OpenGL](2026-06-30-fare-3d-con-opengl.html).
Con l'idea di trasformare questo progetto in un motore per videogiochi vero e proprio, oggi voglio passare un po' di tempo a divagare sull'allocazione degli oggetti.
Il risultato pratico è che ho reimplementato tutto per la terza volta.
E stavolta mi sono reimplementato pure tutto il toolkit grafico! Fidarsi è bene non fidarsi è meglio.

## Come ho fatto in passato

Nello [scorso](2026-06-30-fare-3d-con-opengl.html) articolo ho descritto tutto il discorso di OpenGL, ma non mi sono soffermato particolarmente sulla gestione dello scene graph e degli oggetti.
Riassumiamo adesso ciò che ho fatto.

Un oggetto era rappresentato dal seguente struct:

```c
typedef struct object {
	char name[OBJECT_NAME_SIZE];
	transform transform;
	mesh* mesh;
	material* material;

	// gerarchia 
	struct object* next;
	struct object* parent; // qui segnalavo gli oggetti invalidi con 0
	struct object* child;
} object;
```

1. Come mai segnalavo gli oggetti invalidi? Se avete letto il mio scorso [articolo](2026-07-04-come-essere-pigro-mi-ha-insegnato-l-allocazione-di-memoria.html) avrete capito che fissato con il NON usare l'heap. Anche qui ho fatto la stessa cosa, e infatti c'era un allocatore ad arena di oggetti;
2. Tutto il resto è abbastanza standard, manteniamo il nome dell'oggetto, la sua trasformazione, la mesh e il materiale, e quindi le strutture dati standard per gestire lo scene graph (puntatori al prossimo, al padre, e al figlio).

Abbiamo detto che usavo un allocatore ad arena, infatti le scene erano rappresentate dallo struct:

```c
typedef struct {
	char name[DATA_NAME_SIZE];

	// oggetti "speciali"
	camera camera;
	lighting lighting;

	// oggetti
	object objects[SCENE_MAX_OBJECTS];
	int n_objects;
	object* root;
} scene;
```

Questo inizia ad essere brutto.
1. L'allocatore ad arena è standard: teniamo il contatore di oggetti (di cui facciamo "bump" quando ne allochiamo uno nuovo), e l'array di oggetti vera e propria. Notiamo che questo funziona finché non si deallocano oggetti: al massimo possiamo deallocare l'ultimo allocato (semantica dello stack), ma cose più strane tipo deallocare un oggetto allocato prima di un altro non si possono fare;
2. Chiaramente, dopo l'allocatore ad arena, serve comunque un puntatore all'oggetto *radice*, visto che tutti gli oggetti devono essere organizzati in uno scene graph;
3. La mia poca esperienza col C si vede dal fatto che ho oggetti "speciali", cioè semplicemente volevo specializzare l'oggetto base ma non sapevo come fare. Questi sono la telecamera e un oggetto `lighting`, che mantiene informazioni riguardo all'atmosfera della scena.

Ora, siamo chiari, questo approccio funziona per scene molto semplici, e per un primo prototipo andava più che bene.
Il problema arriva quando provo ad estenderlo.
Innanzitutto, bisogna rendersi conto che un oggetto non vive solo in memoria:
- Bisogna poterlo serializzare sul disco, perché un motore che si rispetti permette all'utente di salvare il lavoro che ha fatto;
- Quindi, a meno di non fare tutto da riga di comando, bisogna anche mostrarlo a video attraverso un qualche toolkit grafico.

Queste cose, nella mia prima implementazione, venivano fatte in maniera disordinata e molto poco generale.
Infatti, avevo un header apposito per la serializzazione di scene, dove associavo uno ad uno ad ogni parametro degli oggetti una chiave alfanumerica.
I file così generati avevano un aspetto del tipo:
```
[...]

o White Knight
me dat/mesh/knight.obj
ma dat/material/white_piece.mat
p 5 2 -7
r 0 0 0
s 1 1 1

[...]
```
con chiara ispirazione dal formato `.obj` (che avevo usato già per le mesh).

Il problema: cambia la struttura dell'oggetto, devi cambiare anche il codice di serializzazione.
Per il toolkit grafico (avevo usato [Nuklear](https://github.com/Immediate-Mode-UI/Nuklear/tree/master)) valgono le stesse considerazioni: quando hai una funzione per renderizzare un singolo oggetto, se cambi l'oggetto devi cambiare anche il codice di rendering.

Usando questo approccio (molto macchinoso) ero riuscito a realizzare la seguente interfaccia, di cui vado comunque abbastanza fiero:

![vecchia GUI](/pics/blog/ents_old.png)

La vecchia GUI

Un problema minore è dato dal fatto che Nuklear come libreria mi sta simpatica filosoficamente ma antipatica dal punto di vista pratico.
Probabilmente sono io che non sono capace ad usarla, ma è minimalista al punto da non funzionare poi tanto bene.
[ImGui](github.com/ocornut/imgui?tab=readme-ov-file) è scritta in C++ e io non mi voglio abbassare a tanto.

## Come voglio fare ora

Non avevo finito di scrivere il codice mostrato sopra che mi è venuto in mente un approccio diverso.

In JavaScript un oggetto non è altro che un insieme di campi arbitrari (internamente una mappa hash).
Ho pensato di spingere quest'idea ancora oltre: rappresentare un oggetto come una semplice lista di campi di qualsiasi tipo. Mesh, materiale, trasformazione o qualsiasi altro parametro: tutto diventa un campo.

Questo risolve 2 problemi:
1. Specializzare gli oggetti è semplice, o anzi non si pone più come problema: basta dotare l'oggetto dei campi che ci servono. In sostanza facciamo una sorta di programmazione ad oggetti, via prototipi (sempre come il JavaScript);
2. Serializzare / renderizzare / fare qualsiasi altra cosa agli oggetti diventa semplice. Infatti, per ogni tipo di campo basterà definire tutte le routine che servono (di serializzazione / rendering / ecc..). Quindi basta chiamare tali routine per ogni campo di un oggetto, e si è finito. Le routine sono piccole e fisse, e gli oggetti possono essere gestiti anche se cambiano struttura (cioè se cambiamo i campi che li compongono).

L'approccio sembrava molto promettente! Ho deciso di chiamare gli oggetti di questo tipo **entità**.

## Come l'ho fatto

Il divertimento sta nei dettagli.

Intanto inserisco un link alla [repo](https://github.com/seggiani-luca/render2), che invito i più curiosi a visitare in quanto il codice è tutto commentato.

Quindi, per implementare questa cosa in C, mi sono ispirato a come il C++ implementa il dispatch delle funzioni virtuali, cioè alle *vtable*.
Una vtable non è altro che uno struct di puntatori a funzione.
Definendolo, definiamo un insieme di *metodi* con la stessa firma, che costituiscono l'interfaccia attraverso cui accedere a determinati oggetti .
Dico *metodi* perché qui ci addentriamo nel funzionamento interno dell'OOP e fa sembre figo usare la nomenclatura giusta.

L'idea è che ogni campo è dato da:
1. Il suo nome;
2. La sua vtable, che sostanzialmente si identifica col suo tipo: a diversi *tipi* di oggetti si associano diversi *metodi* di accesso.

Quindi, per includere informazioni arbitrarie in ogni campo, si usa una tecnica che è l'*incapsulamento* dello struct campo in uno struct più grande.
Se uno si ricorda il tipo di ogni campo, basta convertire i puntatori per ritrovare i dati.

Il codice si spiega meglio delle parole:
```c
// vtabe dei metodi di accesso ai campi 
typedef struct {
	// metodo di lettura 
	void (*read)(const field* f, void* dst);

	// metodo di scrittura 
	void (*write)(field* f, const void* src);

	// metodo di stampa 
	void (*print)(const field* f);
	
	// metodo di serializzazione 
	void (*serialize)(const field* f, char* buf);
	
	// metodo di deserializzazione 
	field* (*deserialize)(const char* buf);

	// metodo di rendering sull'interfaccia 
	int (*gui)(const field* f, guiContext* ctx);
} fieldVtable;

// un campo base
struct field {
	char name[ENT_NAME_SIZ];

	// vtable dei metodi di accesso
	fieldVtable* vtable;

	// è una lista, quindi prossimo
	field* next;
};

// entità
struct entity {
	char name[ENT_NAME_SIZ];

	// radice della lista di campi
	field* root;


	// gerarchia
	struct entity* parent;
	struct entity* child;
	struct entity* peer;
};
typedef struct entity entity;
```

Qui tutto è disposto come vogliamo.
1. Abbiamo le nostre entità, che puntano a liste di campi;
2. Ogni campo è formato dal suo nome e la sua vtable, nonché il puntatore al campo successivo (semplicissima lista);
3. La vtable contiene i metodi di accesso per tutto ciò che potremmo voler fare con un campo: leggerlo, scriverlo, stamparlo, serializzarlo/deserializzarlo, o renderizzarlo sull'interfaccia grafica.

Dichiarare un campo significa:
1. Dichiararne uno struct che incapsuli il campo base;
2. Realizzare un "costruttore", cioè una funzione che alloca memoria (ebbene si, ho ceduto all'heap) per il campo incapsulato;
3. Realizzare i metodi di accesso e usarli.

Sempre in codice, vediamo il campo `int`, cioè il semplice tipo intero:
```c
// int.h

typedef struct {
	field base;

	// dati, cioè l'int stessa
	int val;
} intField;

// crea un nuovo campo int
field* intNew(const char* name);

// int.c

// legge l'int
void intRead(const field* f, void* dst) {
	*(int*)dst = ((intField*)f)->val;
}

// scrive l'int
void intWrite(field* f, const void* src) {
	((intField*)f)->val = *(int*)src;
}

// stampa l'int
void intFieldPrint(const field* f) {
	printf("%s (Integer): %d", f->name, ((intField*)f)->val);
}

fieldVtable intFieldVtable = { 
	.read  = intRead,		  
	.write = intWrite,		 
	.print = intFieldPrint,	
	.gui   = intFieldGui,	  
};

field* intNew(const char* name) {
	ALLOC_FIELD(int) // questo semplicemente alloca l'intField
	f->val = 0;

	return (field*)f;
}
```

Lo so, ci sono alcune macro, ma l'idea di fondo è semplice: implementiamo la struttura `intField` stessa, quindi dichiariamo il costruttore (`intNew`).
A questo punto basta definire i metodi di accesso, usarli per popolare una `vtable`, ed assegnare tale `vtable` ai campi `intField` che andiamo a generare.
Basta questo per avere campi dinamici, cioè effettivamente implementare il dispatch dei metodi virtuali.

Questo si estende facilmente a diversi tipo di campo, e quindi in un attimo si hanno `floatField`, `vectorField`, ecc...

Una comodità che mi sono permesso è avere alcuni helper che vanno ad applicare effettivamente i metodi della vtable secondo una firma standard.
Questo in C è relativamente brutto in quanto ci costringe ad usare tipi `void*` ovunque, però è molto comodo:

```c
void readField(const field* f, void* dst) { f->vtable->read(f, dst); }
void writeField(field* f, const void* src) { f->vtable->write(f, src); }
void printField(const field* f) { f->vtable->print(f); }
int guiField(const field* f, guiContext* ctx) { return f->vtable->gui(f, ctx);}
```

Il risultato è un sistema che offre buona parte della flessibilità di un [ECS](https://en.wikipedia.org/wiki/Entity_component_system) o dell'ereditarietà di un linguaggio OOP, pur rimanendo scritto interamente in C.
Certo, è un po' un abuso del linguaggio. Ma se è andata bene a Bjarne, penso che me la possa cavare anch'io.

## Altre cose

Vi sarete accorti che l'implementazione del metodo `guiInt` non si è vista da nessuna parte nel codice sopra.
Questa è la parte simpatica di questo approccio!
Infatti, i metodi specifici ad un certo dominio (in questo caso l'interfaccia grafica, cioè la GUI) posso definirli nell'header relativo a tale dominio.
Questo mi semplifica di molto la struttura del progetto.

Avrò quindi un header da qualche parte con tutte le funzioni della GUI:
```c
// primitive della GUI

int intFieldGui(const field* f, guiContext* ctx);
int floatFieldGui(const field* f, guiContext* ctx);
int stringFieldGui(const field* f, guiContext* ctx);
// [...]
```
e nell'implementazione dei campi stessi, di tutte queste cose non me ne dovro nemmeno preoccupare.
 
Stessa cosa vale per la serializzazione / deserializzazione: da qualche parte possiamo avere un motore di serializzazione semplicemente implementando metodi che manipolano i campi.
Tutto questo in maniera estremamente semplice, senza decoratori, riflessione, o altre cose sofisticate (anche se probabilmente ci tocca scrivere un po' più di codice del dovuto).

### GUI

A questo punto potrebbe valere la pena di parlare del toolkit grafico che ho realizzato per renderizzare queste entità su una GUI.
Senza divagare troppo, uso OpenGL sia per il rendering della scena di gioco vera e propria, che per l'interfaccia dell'editor.

Questo, che sembrava inizialmente molto complicato, si riassume nel:
1. Dotarsi di una mesh basilare, cioè un rettangolo, e di una shader che renderizza una texture così com'è a schermo su tale triangolo;
2. Quindi bisogna formare una coda di possibili *trasformazioni* di quel triangolo per poter renderizzare ogni elemento dell'interfaccia (rivedere il discorso dei VAO/VBO dello scorso articolo);
3. Infine, si scorre tale lista, popolando appunto un VBO, e quindi si fa la draw call.

Con un po' di fantasia, questi rettangoli possono rappresentare pulsanti, testo, ecc... e quindi si può formare un'intera GUI.

In codice possiamo riassumere come segue:

```c
// singolo rettangolo
struct quad {
	float4 pos;
	float4 uv;
};
typedef struct quad quad;

// coda di rettangoli da renderizzare 
typedef struct {
	quad vec[QUEUE_SIZ];
	int last;
} guiQueue;

void updateGUI() {
	guiQueue q = {0};

	// qui chiamiamo il codice utente
	codice_utente(&q);

	// ora la guiQueue è popolata di rettangoli da disegnare!
	// inviamo questi rettangoli alla GPU e disegnamoli
	flushLayer(&q); // chiama codice specifico OpenGL
}
```

Risparmio altri dettagli in quanto probabilmente è meglio riprendere l'argomento in mano quando il toolkit è più maturo, e fare un discorso più serio.

Il risultato di questo approccio, però, è molto promettente:

![nuova GUI](/pics/blog/ents_new.png)

La nuova GUI

In figura, vediamo un'oggetto, dove abbiamo diversi campi: la trasformazione; un campo stringa; un campo float; un campo intero.

Certo, non ho parlato di diverse cose anche molto importanti, come la gestione delle finestre (che pressappoco combacia con quanto già visto su GLFW), e la gestione dell'input (effettivamente complicata, ma basata sempre su GLFW).
La [documentazione](https://www.glfw.org/docs/latest/) aiuta di molto in questi casi!
