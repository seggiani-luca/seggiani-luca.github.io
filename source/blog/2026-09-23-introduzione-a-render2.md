<!-- Unity, in piccolo. -->
<!-- Una quantità poco ragionevole di infrastruttura costruita a mano. -->
<!-- (Quasi) tutto da zero. -->
<!-- Per imparare Unity, devi scrivere Unity. -->
<!-- Presente quell'idea sugli ECS? -->

# Introduzione a render2
{{ page_blurb }}
{{ estimate_time }}

Un po' di tempo fa ho scritto [questo](/blog/2026-06-28-sull-allocazione-degli-oggetti.html) articolo su un sistema per la gestione di oggetti polimorfi, simile ad un ECS, improntato allo sviluppo di motori grafici e/o per videogiochi.
Ho approfondito l'idea, sviluppato un po' di sistemi, e il risultato è disponibile a [questa](https://github.com/seggiani-luca/render2) repository.
Ho scritto anche una [pagina](/progetti/render2.html) che dettaglia il progetto (ho copia-incollato il `README.md`, non aspettatevi molto).

Il nome del progetto è **render2**.
Se avete letto gli scorsi articoli, avrete notato che questa è la terza volta che ricomincio questo progetto da capo.
Quindi, i programmatori iniziano a contare da 0, per cui render *2*.

## Che cos'è?

L'idea dello scorso articolo era di avere **entità**, cioè oggetti rappresentati come una semplice lista di campi di qualsiasi tipo.
Mesh, materiale, trasformazione o qualsiasi altro parametro: tutto diventa un campo.
Questo mi semplifica di molto la vita dal punto di vista implementativo, in quanto bastava scrivere le sole funzioni che agivano sui campi, ed incollarle insieme per gestire oggetti arbitrariamente complessi.
Avevo quindi la semplice implementazione dell'entità:

```c
// entity data
struct entity {
	// name of entity
	char name[ENT_NAME_SIZ];

	// root of field list
	field* root;

	// number of fields
	int fieldCount;

	// parent of this entity (NULL for root)
	struct entity* parent;

	// direct children of this entity
	struct entity* child;

	// next peer of this entity
	struct entity* peer;

	// number of children
	int childCount;
};
typedef struct entity entity;
```

e un'altrettanto semplice GUI per la gestione degli oggetti, che mi aveva dimostrato che l'approccio poteva funzionare.
Questi oggetti, poi, potevano essere organizzati in scene (lo si vede dal codice sopra, lo `struct` ha un po' di stato riguardo alla gerarchia):

```c
// a scene is just an entity hierarchy
struct scene {
	// scene name
	char name[ENT_NAME_SIZ];

	// root of scene hierarchy
	entity root;

    // here be dragons!

	// rendering state
	renderScene render;

	// dirty flag
	int dirty;
};
typedef struct scene scene;
```

Il prossimo passo era chiaramente quello di attaccare un sistema più complesso a questi oggetti, che altrimenti risultavano inutili.
Il codice sopra dovrebbe dare qualche indizio su quale sistema ho scelto di implementare per primo: per un motore di rendering un buon inizio è, sorpresa, *renderizzare* gli oggetti.
Chi se lo sarebbe aspettato.

## Come?

Nell'articolo su [OpenGL](/blog/2026-06-30-fare-3d-con-opengl.html), e anche nel [precedente](2026-06-28-esperimenti-3d.html), ho parlato del rendering 3D in generale.
Eravamo arrivati alla conclusione che ci servivano:
- Delle `mesh`, cioè buffer di vertici, normali, e altre informazioni geometriche sugli oggetti da disegnare;
- `texture`, cioè mappe che venivano applicate alle mesh per determinare il loro colore;
- `shader`, ovvero piccoli programmi che venivano eseguiti sulle mesh per renderizzarle effettivamente nello spazio schermo;
- `material` che raggruppavano texture e shader, assieme ai loro parametri, in unità compatte da assegnare alle `mesh`.

Questa idea si sposa perfettamente con le entità: ognuno di questi oggetti può essere un *campo*, associato alle rispettive informazioni.
Anzi, abbiamo bisogno solo di una `mesh` e di un `material` per renderizzare un oggetto, in quanto abbiamo detto `texture` e `shader` sono racchiuse nel `material` stesso.

In verità, però, vediamo che  ci sono alcune complicazioni che dobbiamo ancora gestire.

### Dove sono gli oggetti?

Nulla di un oggetto ci dice, di per sé, dove questo oggetto si trova: è una conseguenza naturale dell'assegnare tutto ai campi che lo compongono.
Questo, però, risulta abbastanza importante da sapere quanto si vuole renderizzare l'oggetto sullo schermo.
Basta quindi dotarsi di un ulteriore campo, il campo `transform`, che ne determina la trasformazione.

Si potrebbe parlare a lungo delle trasformazioni.
Cercando di essere sintetici, abbiamo che ci serve:
- La posizione dell'oggetto (semplice);
- La sua rotazione (molto meno semplice);
- La sua scala, cioè quanto l'oggetto viene "dilatato" in ogni asse.

Le rotazioni sono particolarmente complesse in quanto, al contrario delle altre 2 informazioni, non basta un vettore tridimensionale a rappresentarle.
Non ricordo se ne ho già parlato in profondità, ma su [Wikipedia](https://en.wikipedia.org/wiki/Gimbal_lock) ci sono spiegazioni.
L'idea è che soli 3 gradi di libertà non riescono a rappresentare univocamente lo spazio di trasformazioni tridimensionali (isomorfo allo spazio delle matrici di rotazione).
Finché le cose stanno ferme ce la si può cavare con gli [angoli di eulero](https://it.wikipedia.org/wiki/Angoli_di_Eulero), ma nel caso di applicazioni interattive come i *videogiochi*, le cose si rompono molto velocemente.

La soluzione è quindi da oggetti matematici molto paurosi detti [quaternioni](https://it.wikipedia.org/wiki/Quaternione).
Non mi dilungherò sulla teoria dei quaternioni (anche perché non la capisco), ma mi limiterò a dire che possiamo vederli come vettori quadridimensionali.
Di questi 4 numeri, 3 rappresenteranno l'*asse* di rotazione, e il rimanente l'*angolo* (o circa) attorno a quell'asse.
Comunque, nell'header `math.h` della repo ci sono tutte le funzioni.
Probabilmente si fa prima a studiare quelle.

Il risultato è il seguente `struct`:
```c
// definition of transform
typedef struct {
	// position
	float3 position;

	// rotation
	quat rotation; // praticamente, typedef vec4 quat ...

	// scale
	float3 scale;
} transform;
```

### Da dove si parte

Una volta che abbiamo le nostre entità in ordine, con `transform`, `mesh` e `material`, vogliamo effettivamente disegnarle su un framebuffer.

![entità renderizzabile](/pics/blog/renderable_entity.png)

Un entità pronta ad essere renderizzata

Iniziamo col fare un po' d'ordine.
Queste entità stanno in una scena: possono essere figlie di altre entità, ecc...
Le scene sono grafi aclici diretti, per cui l'algoritmo è semplice:
1. Percorriamo l'intero grafo della scena;
2. Per ogni entità renderizzabile trovata, la renderizziamo.

Il processo di rendering è banale consultati gli scorsi articoli sul rendering (ho fatto alcuni aggiornamenti ai materiali e alle shader, ma nulla che non sia coerente con quanto altri motori già fanno).

L'idea interessante è che non tutte le entità sono di per sé renderizzabili.
Anzi, mi è venuto in mente che avere entità senza trasformazioni, o con trasformazioni ma senza campi `mesh` e `material`, potevano tornare utili a diversi scopi:
- Entità senza `transform`: non occupa una posizione nello spazio e può quindi fungere da nodo puramente logico. Può essere utilizzata, per esempio, come controller invisibile, contenitore semantico o punto di organizzazione per un insieme di entità figlie. La sua presenza nella gerarchia non introduce alcun effetto geometrico.
- Entità con `transform` ma senza `mesh`/`material`: rappresenta invece un vero e proprio riferimento spaziale. Non viene renderizzata, ma possiede una posizione, orientazione e scala proprie. Questo la rende utile per punti di aggancio, pivot, socket, bones semplificati o, più in generale, per costruire strutture meccaniche attraverso la gerarchia.

### Composizioni spaziali

A proposito di quest'ultimo punto, noto che ho finalmente implementato la corretta *composizione* delle trasformazioni.
Questo è particolarmente interessante perché permette di sfruttare la gerarchia delle entità come un sistema di *composizione spaziale*.
Un'entità può definire un sistema di coordinate locale e le sue figlie possono definire ulteriori trasformazioni relative a quel sistema.

Per esempio, si può avere:
```
robot
└── torso
    ├── arm
    │   └── forearm
    │       └── hand
    └── head
```

dove `robot`, `torso`, `arm` e `forearm`` potrebbero essere semplicemente entità dotate di `transform`, mentre solo alcune foglie possiedono effettivamente `mesh` e `material`.
La cosa importante è che la trasformazione della figlia non viene interpretata nello spazio globale, ma nello spazio locale del padre.
In termini matriciali, si moltiplica la trasformazione della figlia per quella del padre.
Quindi, se il padre ruota, anche il sistema di riferimento della figlia ruota con esso.
Una figlia che ha, ad esempio, una traslazione locale lungo l'asse X, continuerà a essere a +X rispetto al padre, non rispetto al mondo.
Così si rappresentano velocemente strutture meccaniche come quella riportata sopra (un semplice braccio meccanico).

### Liste di rendering

Un ottimizzazione che si può fare, nel contesto di entità così variegate, è quella di realizzare a partire dal grafo delle scene, una rappresentazione semplificata che chiamo *lista di rendering*.
La lista di rendering è una versione "appiattita" della scena contenente i soli oggetti renderizzabili, e le loro trasformazioni già composte.

La realizziamo come una lista collegata, associata ad ogni scena: 

```c
// an entity, which can be rendered to screen
struct renderEntity {
	// entity transformation
	mat4 transform;

	// mesh of entity
	mesh* mesh;
	
	// material of entity
	material* material;

	// next render entity in list
	struct renderEntity* next;
};
typedef struct renderEntity renderEntity;

// a rendering view of a scene
typedef struct {
	// scene camera
	struct {
		// camera field
		camera* info;

		// camera transform
		mat4 transform;
	} camera;

	// scene atmosphere
	struct {
		// atmosphere field
		atmosphere* info;
		
		// atmosphere transform
		mat4 transform;
	} atmosphere;

	// root of scene hierarchy
	renderEntity* root;
} renderScene;
```

Il rendering risulta quindi banale (basta scorrere la lista).
Più interessante è come si costruisce la lista di rendering (`renderScene`)·
- Ha senso compilare la lista di rendering solo quando qualcosa nella scena cambia davvero. Questo si rileva attraverso un apposito flag `dirty`: se qualcuno modifica la scena, si alza `dirty`, e da lì in poi il sottosistema di rendering ha il compito di ricompilare la lista;
- Le trasformazioni vengono composte con l'ausilio di uno stack che mantiene, per ogni entità, le trasformazioni delle entità genitore. Queste possono quindi essere composte con una semplice moltiplicazione matriciale. Quando si finisce di consultare le entità figlie di una data entità, quindi, basta risalire nello stack fino al padre dell'entità stessa, e via dicendo. In codice:
```c
// codice di percorrenza del grafo [...]

// calcola la variazione di profondità 
int depthDelta = it->base.depth - it->lastDepth;

// aggiorna lo stack 
it->stack.cur += depthDelta;
if (it->stack.cur < 0 || it->stack.cur >= SCN_MAX_DEPTH) return NULL;

// ottieni trasformazione locale 
field* f = getField(new, REN_TRANSFORM_NAME);
transform tf;
if(f) tf = ((transformField*)f)->val;
else tf = transformIdent();

// converti la trasformazione in matrice 
mat4 local = transformToMat4(tf);

// componi la trasformazione con la precedente
it->stack.vec[it->stack.cur] =
    matMul4(it->stack.vec[it->stack.cur - 1], local);

// aggiorna lo stato, in modo da conoscere la variazione di profondità alla
// prossima iterazione
it->lastDepth = it->base.depth;

// [...]
```

## Risultati

I risultati di questo approccio sono principalmente 2:
- Si ha un modo versatile non solo per rappresentare grafi di scene, ma anche costruzioni geometriche arbitrariamente complesse;
- Si possono disegnare tali costruzioni a schermo ottenendo, anche qui, effetti grafici tanto complessi quanto si è disposti a sviluppare mesh, materiali e shader forniti alle primitive di OpenGL. Assicuro che null'altro è stato aggiunto a quanto detto in [questo](/blog/2026-06-30-fare-3d-con-opengl.html) articolo, se non alcune funzionalità di *quality-of-life* per la gestione di shader e materiali. 

Vediamo quindi un semplice render che sono riuscito a fare in fase di testing:

![reiko nagase su una bisonte](/pics/blog/reiko_render.png)

Mai giocato a Ridge Racer?

### Spiegazioni

Ho aggiornato anche la GUI, che dovrebbe risultare più leggibile.
- A sinistra si nota la *gerarchia*, cioè una rappresentazione grafica della scena. Vediamo che non è altro che un albero n-ario. In particolare, l'automobile è rappresentata dall'entità *Bisonte*, di cui vediamo sono figlie le entità *Body* (carrozzeria), e le varie *Wheel FR*, etc... (le ruote). Anche la signorina sul cofano è figlia dell'entità *Bisonte*: così se l'automibile ruota, anche lei ruota in maniera solidale;
- Al centro c'è la finestra principale, che mostra il rendering vero e proprio. Si notano alcuni effetti grafici "avanzati", come la simulazione del cielo, illuminazione ambientale più sofisticata, e materiali che simulano caratteristiche ottiche più complesse come i riflessi sulla vernice dell'automobile, o la colorazione della pelle della signorina;
- A destra c'è il fedele *ispettore*, che permette di analizzare le entità. Nello screenshot è selezionata l'entità *Reiko* (la signorina). Si nota come questa è renderizzabile: è dotata di un campo `transform`, con la sua posizione nello spazio locale all'automobile, un campo `mesh` con la sua mesh e un campo `material` col rispettivo materiale.

## Bonus: approfondimenti sull'esempio

La parte spiegata sopra è abbastanza concettosa, per cui voglio alleggerire un po' parlando della scena di prova mostrata sopra.
L'ispirazione sono i poster promozionali del videogioco [Ridge Racer Type 4](https://en.wikipedia.org/wiki/R4%3A_Ridge_Racer_Type_4), della Namco, per la Playstation 1 (o più precisamente PSX, visto che comprende anche la *PS One*).
Ho scelto questo tema in quanto i rendering che venivano realizzati all'epoca erano molto rudimentali, e mi sono reso conto che forse potevo avvicinarmi allo stesso stile con il mio motore altrettanto (se non di più) rudimentale.

Ciònonostante, c'è stato comunque modo di sperimentare con shader e materiali abbastanza interessanti, per cui vale la pena spendere 2 parole.

### I modelli

Questo è stato il primo progetto di modellazione "seria" che ho fatto con Blender.
L'idea di modellare un'automobile non mi sembrava poi tanto fuori dal normale.
Quella di modellare un personaggio umano, invece, mi terrorizzava.

L'automobile che ho modellato è la *Bisonte*, che nel gioco è prodotta dal (fittizio) marchio italiano *Assoluto*.
Questo è molto particolare, in quanto la linea ricorda più quella di una Ford GT40.
I giapponesi sono fantasiosi.

![bisonte](/pics/blog/bisonte.png)

Bisonte + Reference

L'approccio che ho usato, non essendo capace a modellare a occhio, e visto che non si trovavano blueprint in rete (cosa che ha senso, in quanto l'automobile non è mai stata costruita nella realtà), è quello di scaricare un modello a bassa risoluzione da sito [Modelers Resource](https://models.spriters-resource.com/).
Questo sito è ottimo per trovare modelli di vecchi (o nuovi) videogiochi da studiare.
Mi sembra che io ho preso un modello da un gioco per Nintendo 64.

Ho quindi usato gli strumenti di Blender per realizzare una versione a risoluzione più alta, tracciandola sul modello originale.
Quindi ho potuto *smussare* questo modello attraverso il modificatore [Subdivision Surface](https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/subdivision_surface.html), per averlo ancora più liscio.
Mi è tornato particolarmente lo strumento [Edge Data](https://docs.blender.org/manual/en/latest/modeling/meshes/editing/edge/edge_data.html): selezionando determinati spigoli del modello e digitando `Ctrl + E` in *edit mode*, è possibile renderli più "spigolosi", cioè diminuire l'effetto del modificatore *Subdivision Surface*.
Un giorno sarebbe simpatico approfondire come questo modificatore funziona a basso livello.
Se non sbaglio, ha qualcosa a che fare con l'algoritmo di [Catmull-Clark](https://en.wikipedia.org/wiki/Catmull%E2%80%93Clark_subdivision_surface).

![bisonte](/pics/blog/bisonte_wires.png)

Wireframe della Bisonte

Veniamo alla signorina.
Il nome è *Reiko Nagase*, e nel gioco originale fa un po' da *cover girl* e ombrellina durante le gare.
Pare che il personaggio abbia avuto un grande successo fra i fan del gioco.
Non sembra difficile immaginare il perché.

Essendo questa la prima volta che modellavo un personaggio da zero, ho dovuto fare molte iterazioni.
La parte più complicata è sicuramente la faccia: basta poco per passare da qualcosa di decente a un alieno dalle proporzioni amorfe.
La soluzione per me è stata di prendere un modello di riferimento (sempre da[Modelers Resource](https://models.spriters-resource.com/), e studiarmelo a fondo).

![facce di reiko](/pics/blog/reiko_faces.png)

Iterazioni su iterazioni

Il resto del modello è stato molto più semplice.
Mi sono basato su alcune immagini di riferimento (basta cercare cose come "anime reference" sul Web), e sui tutorial di [questo](https://www.youtube.com/@2amgoodnight) artista su YouTube.

![reiko](/pics/blog/reiko.png)

Il modello di Reiko finito

Una parte interessante è come ho messo il personaggio in *posa* sul cofano dell'automobile.
Senza dilungarsi sui dettagli, il modo in cui vengono posati (e quindi animati) i modelli tridimensionali è associandogli una *armatura*.
Un armatura non è altro che un insieme di *ossa* virtuali (per cui a volte la chiamiamo *scheletro*), che sono organizzate esattamente come la nostra scena di prima, a supportare la composizione delle trasformazioni.
Risulta quindi facile assegnare una determinata posa all'armatura, modificando le trasformazioni delle singole ossa.

Per riflettere queste trasformazioni sul modello vero e proprio, si estende la rappresentazione dei singoli vertici introducendo una serie di pesi.
Ognuno di questi pesi rappresenta quanto ogni osso virtuale contribuisce alla trasformazione del vertice.
In pseudocodice:
```c
// vertex data type (mirrors OpenGL)
typedef struct {
	float x, y, z;           // position
	float u, v;              // UV
	float nx, ny, nz;        // normal
    float wights[NUM_BONES]; // weights
} vertex;
```

Quindi, basta interpolare linearmente per portare ogni vertice nella posizione data dalle ossa, e i relativi pesi.

Generare questi pesi è complicato, per cui ho in primo luogo sperimentato con tool automatizzati come [Mixamo](https://www.mixamo.com/), di Adobe.
Ho avuto scarsi risultati, però, per cui ho preferito usare gli strumenti interni di [rigging](https://www.blender.org/features/animation/) di Blender, uniti ad alcune modifiche manuali.

![armatura reko](/pics/blog/reiko_rig.png)

L'armatura

Credo che il risultato sia, per un primo tentativo, soddisfacente.

### I materiali e le shader

Arriviamo infine alla parte più interessante dal punto di vista grafico: i materiali.

Come avevamo detto, un `material` raccoglie tutte le informazioni necessarie a descrivere come una `mesh` deve essere renderizzata.
Nel caso più semplice, abbiamo quindi:
- Un colore diffuso, cioè il colore "base" dell'oggetto;
- Un colore speculare, che determina il colore dei riflessi;
- Un parametro di *shininess*, che determina quanto questi riflessi siano concentrati;
- Eventualmente delle texture per modificare localmente ciascuno di questi parametri.

Il materiale viene poi passato alla shader, che si occupa di combinare queste informazioni con la geometria e con l'illuminazione della scena.

La shader principale che ho utilizzato è basata su un modello abbastanza semplice di illuminazione.
Per ogni frammento vengono calcolati la normale alla superficie, la direzione verso la luce e quella verso la telecamera.

La componente diffusa segue sostanzialmente il modello di [Lambert](https://en.wikipedia.org/wiki/Lambertian_reflectance) (che ormai conosciamo bene):

```glsl
float lambertDot = dot(L, N);
vec3 lambert = max(lambertDot, 0.0) * uSunCol;

vec3 diffuse = albedo * lambert;
```

In pratica, una superficie rivolta verso la luce riceve più illuminazione, mentre una superficie perpendicolare o rivolta nella direzione opposta ne riceve poca o nulla.

A questa si aggiunge una componente speculare, calcolata riflettendo la direzione della telecamera rispetto alla normale:

```glsl
vec3 specular =
    specularCol *
    uSunCol *
    step(0.0, lambertDot) *
    pow(max(dot(R, L), 0.0), specExponent);
```

Il parametro di *shininess* viene trasformato in un esponente compreso fra `1` e `256`.
Valori elevati producono riflessi più piccoli e concentrati, mentre valori bassi producono riflessi più larghi.

Non mi sono però fermato alla sola luce diretta.
Per evitare che le superfici non direttamente illuminate risultassero completamente nere, ho aggiunto una componente ambientale.

L'ambiente è rappresentato da una texture equirettangolare, cioè una normale immagine panoramica che rappresenta ciò che circonda l'oggetto.
Data una direzione nello spazio, posso quindi convertirla nelle coordinate della texture:

```glsl
vec2 enviroUV = dirToEquirectUV(N);
enviro *= textureLod(uAmbientMap, enviroUV, DIFFUSE_MIP).rgb;
```

La stessa tecnica viene utilizzata anche per simulare i riflessi dell'ambiente sulla superficie.
In questo caso si utilizza la direzione riflessa `R`, e il livello di mipmap viene modificato in funzione della *shininess*: superfici più lucide producono riflessi più definiti, mentre quelle più opache li sfocano.

Il risultato finale è quindi una combinazione di illuminazione ambientale, diffusione e riflessione speculare.

Per la pelle di Reiko ho fatto un ulteriore passo, introducendo una shader specifica.

La pelle, a differenza di una superficie completamente opaca, lascia penetrare una piccola quantità di luce e la diffonde al suo interno.
Non ho implementato un vero modello di *subsurface scattering*, che sarebbe decisamente eccessivo per questo progetto, ma una semplice approssimazione:

```glsl
float scatter =
    max(0.0, (lambertDot + SUBSURFACE_WRAP) /
               (1.0 + SUBSURFACE_WRAP));

scatter = pow(1.0 - scatter, SUBSURFACE_EXPONENT);

vec3 subsurf = scatter * uSubsurfCol * uSunCol;
```

L'idea è quella di permettere alla luce di contribuire anche quando la superficie è orientata lontano dalla sorgente luminosa, simulando in maniera molto approssimativa la luce che attraversa e viene diffusa dalla pelle.

Ho inoltre utilizzato due componenti speculari con diversa concentrazione.
Una rappresenta il normale riflesso della superficie, mentre l'altra è più largo e debole, per approssimare il comportamento della pelle.

Infine, la texture diffusa viene utilizzata anche come maschera alpha per alcuni elementi, come i capelli:

```glsl
if(mapCol.a < CLIP_THRESHOLD)
    discard;
```

Non è quindi trasparenza vera e propria: il frammento viene semplicemente eliminato sotto una certa soglia.
Per il tipo di geometria utilizzata è più che sufficiente.

Anche il cielo utilizza una tecnica abbastanza semplice.
Viene renderizzato come una sfera che circonda la scena, ma la sua profondità viene forzata al valore massimo:

```glsl
gl_Position =
    (uProjection * uView * vec4(aPos, 1.0)).xyww;
```

In questo modo il cielo rimane sempre dietro a tutti gli altri oggetti.

La sua posizione nello spazio non è quindi particolarmente importante: quello che ci interessa è soltanto la direzione del vertice rispetto alla telecamera. Questa viene trasformata in coordinate equirettangolari e utilizzata per campionare la texture panoramica.

Il risultato è una pipeline grafica tutt'altro che fisicamente corretta, ma sufficientemente flessibile da permettermi di ottenere materiali molto diversi partendo dagli stessi componenti di base.
Lo si vede dalla figura di esempio di prima.

## Conclusioni

Voglio chiudere notando che questo non è assolutamente la fine di questo progetto, e spero nemmeno degli articoli che lo dettagliano.
Ho fatto diverse altre cose, fra cui un overhaul completo del toolkit grafico, l'implementazione del sistema di serializzazione (noioso) e l'inizio dell'implementazione del sistema di scripting (molto meno noioso).

Attualmente mi sto concentrando sul ripulire ulteriormente il toolkit grafico, con l'intenzione di renderlo abbastanza maturo da costituire una libreria a sé.
Questo mi renderebbe molto più facile lo sviluppo del motore, in quanto non dovrei più stare continuamente a risolvere problemi di GUI quando sto lavorando altre cose.

Purtroppo (o per fortuna) è ricominciata anche l'università.
Io ho passato molto del tempo libero che ho avuto a lavorare a questo progetto, ma chiaramente da qui in poi il tempo scarseggierà sempre di più (a malapena ho trovato la volontà, anzi la *pretesa* di scrivere questo articolo).
Spero quindi di riuscire almeno a portare il sistema di scripting ad un livello funzionale, e a documentarlo (e magari anche la serializzazione).
Fino a quel punto, navighiamo in mare aperto.
Cheers!
