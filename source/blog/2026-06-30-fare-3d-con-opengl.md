# 2026 06 30 fare 3d con opengl
Nello [scorso articolo](/blog/2026-06-28-esperimenti-3d.html) ho parlato della grafica 3D e mostrato l'implementazione di un (semplicissimo) software renderer.
Alla fine ci eravamo detti che per fare le cose per bene era opportuno usare un'API per l'accelerazione grafica come OpenGL.
Questo dà diversi vantaggi:
- In un software renderer dobbiamo implementare tutto da soli (e quindi probabilmente troveremo implementazioni meno efficienti rispetto a quelle sviluppate dagli esperti negli anni);
- Le CPU di oggi, seppur ricche di estensioni, sono comunque relativamente lente per le operazioni estremamente vettorializzabili (come la grafica 3D).

Per questo motivo ho deciso di prendere l'esempio dello scorso articolo e portarlo su OpenGL.

![glxgears](/pics/blog/render1_glxgears.png)

`glxgears` in esecuzione su ambiente Wayland

Ho buttato il codice descritto in questo articolo nella stessa [repository](https://github.com/seggiani-luca/rendering-experiments/tree/main/render_1).
Ricordiamo ancora che non si fanno grandi garanzie sulla portabilità (la combinazione di GLAD e GLFW che uso funziona tranquillamente su Arch Linux, e dovrebbe essere portatile).

## Che cos'è? 

La prima domanda ragionevole è "cosa razza di diavolo è OpenGL?".
[OpenGL](https://www.khronos.org/opengl/) è un'API (solo la specifica dell'API, senza nessuna implementazione predefinita o di riferimento) pensata per fare da ponte fra:
- L'hardware di accelerazione grafica, cioè le "schede grafiche" (o GPU) che offrono memoria dedicata alla grafica e coprocessori per operazioni fortemente vettorializzate;
- I programmatori, che vogliono un'interfaccia predefinita per parlare con tale hardware.

OpenGL nasce dentro [SGI](https://en.wikipedia.org/wiki/Silicon_Graphics) negli anni '90 come versione open source della proprietaria IRIS GL.
Oggi è mantenuta da [Khronos Group](https://www.khronos.org/) (infatti alcuni header li dobbiamo a loro).
Viene aggiornata negli anni diventando abbastanza centrale, sopratutto nello sviluppo di applicazioni in grafica 3D e non solo (giochi, tool di modellazione e CAD) open source.
Alcune caratteristiche fondamentali sono:

- OpenGL è fortemente *stateful*: quando si opera su un oggetto bisogna assegnarlo, dopodiché l'API se lo "ricorda" e lo si può modificare implicitamente (cosa molto poco intuitiva);
- Ha 2 modalità: immediata (comandi vengono renderizzati subito a schermo) o moderna, a buffer (si da una lista di comandi più complessa che viene gestita in differita nelle cosiddette *draw call*);
- Il rendering si basa su buffer passati alla GPU, e su cui vengono eseguiti dei microprogammi detti **shader**. OpenGL ha 2 tipi di shader (vertex e fragment) e diversi tipi di buffer che gestiscono qualsiasi cosa, dai vertici delle mesh alle texture;
- OpenGL non fornisce alcun sistema di windowing, cioè non interagisce col sistema operativo per creare finestre. La gestione dei *contesti* OpenGL (cioè le superfici su cui si renderizza) va quindi fatta altrove. Noi useremo la libreria [GLFW](https://www.glfw.org/);
- OpenGL non fornisce nulla nemmeno sul fronte input/output, cioè non rileva comandi da tastiera, mouse, non può gestire le periferiche o emettere suono. Anche qui ci aiuta la libreria GLFW (di base gestisce l'input).

Oggi questa API è stata sorpassata da [Vulkan](https://www.vulkan.org/), che ne risolve molti dei problemi originali.
Per noi, però, OpenGL è più che abbastanza per iniziare a discutere con la GPU.

Nella figura precedente si vede il modo più veloce per vedere se OpenGL gira sul nostro sistema.
Da terminale:
- Con `glxinfo` si ottengono alcune informazioni sull'ambiente di esecuzione che effettivamente si prende a carico le nostre chiamate all'API (l'hardware e i driver della GPU);
- Con `glxgears` si mostra una scena di esempio. Se questo funziona, tutto il resto dovrebbe funzionare. Notare che quando si lancia `glxgears`, prima si deve ottenere un qualche tipo di contesto grafico (la finestra) dal sistema operativo, e solo dopo si può interrogare la GPU e iniziare a renderizzare.

## Come si usa?

La seconda domanda ragionevole è "come si usa?".
Qui voglio discutere come io ho realizzato un semplice esempio (quello nella repo).
> Nota! Questo esempio è molto specifico (si usa la modalità a buffer di OpenGL, caricato con GLAD, e si creano i contesti con GLFW). Esistono 1000 altri modi di fare la stessa cosa, e di questi almeno 900 sono più efficienti. Io mostro la mia implementazione solo a scopo didattico: è quella a cui io stesso sono arrivato sperimentando ed imparando.

Lavoriamo in C (l'API è cross-language, ma C è il binding più vicino).
Per aprire un contesto OpenGL e disegnare qualcosa abbiamo bisogno *almeno* degli header per accedere a:
- L'API OpenGL stessa. Gli header forniti dai sistemi operativi sia Linux che Microsft (non ho esperienza con i prodotti Apple) sono molto attempati, e la specifica è stata largamente estesa negli anni, per cui oggi va di moda usare "caricatori" come [GLAD](https://glad.dav1d.de/). Questi sono header con le funzioni OpenGL, le cui definizioni vengono risolte a tempo di esecuzione;
- Una qualche API per la generazione di finestre. Abbiamo già detto che noi useremo la libreria [GLFW](https://www.glfw.org/), che su Arch Linux è disponibile direttamente nelle repository di pacchetti. Altre librerie come [SDL](https://www.libsdl.org/), [Allegro](https://liballeg.org/), ecc... fanno la stessa cosa, ma qui uso GLFW.

Facciamo quindi zoom sulla fase di inizializzazione:
```c
#define GLFW_INCLUDE_NONE
#include <GLFW/glfw3.h>		  // GLFW: gestisce le finestre 
#include "../../lib/glad/glad.h" // GLAD: carica le funzioni OpenGL

GLFWwindow* window = NULL; // la finestra

int coreCreate() {
	// 1. inizializza GLFW

	if (!glfwInit()) {
		printf("Failed to initialize GLFW\n");
		return 0;
	}

	// 2. indica

	// indica finestra fluttuante e a dimensione fissa 
	glfwWindowHint(GLFW_FLOATING, GLFW_TRUE);
	glfwWindowHint(GLFW_RESIZABLE, GLFW_FALSE);

	// indica versione OpenGL
	glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, OPENGL_VERSION_MAJOR);
	glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, OPENGL_VERSION_MINOR);
	glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);

	// indica piattaforma
	glfwInitHint(GLFW_PLATFORM, GLFW_PLATFORM_WAYLAND);
	
	// indica double buffering 
	glfwWindowHint(GLFW_DOUBLEBUFFER, GLFW_TRUE);

	// 3. crea finestra

	window = glfwCreateWindow(
		WIN_WIDTH,
		WIN_HEIGHT, 
		WIN_TITLE, 
		NULL, NULL
	);
	if (!window) {
		glfwTerminate();
		printf("Failed to create context\n");
		return 0;
	}

	glfwMakeContextCurrent(window);

	// 4. carica OpenGL

	if (!gladLoadGLLoader((GLADloadproc)glfwGetProcAddress)) {
		printf("Failed to initialize GLAD\n");
		return 0;
	}

	// 5. configura OpenGL

	int fWidth, fHeight;
	glfwGetFramebufferSize(window, &fWidth, &fHeight);
	glViewport(0, 0, fWidth, fHeight);
	glEnable(GL_DEPTH_TEST);		

	return 1;
}

```

Qui abbiamo indicato a commenti 5 fasi distinte:
1. GLFW va inizializzato: questo si fa con la funzione `glfwInit()`. Quindi si controllano gli errori e si prosegue;
2. GLFW ci permette di dare alcune indicazioni (gli [hint](https://www.glfw.org/docs/latest/window_guide.html#window_hints)). Queste sono in sostanza indicazioni riguardo a come presentare la finestra, come gestire OpenGL, ecc... Vanno date prima della creazione della finestra, e di lì in poi conservano il loro valore;
3. A questo punto si può creare la finestra vera e propria. Questo si fa con la `glfwCreateWindow()`, a cui si danno in argomento le dimensioni e il titolo della finestra. Anche qui si controllano gli errori e si prosegue. Notiamo che anche GLFW è stateful: una volta creata una finestra bisogna renderla corrente con `glfwMakeContextCurrent()`. Da lì in poi i comandi rivolti alle finestre influenzeranno la finestra corrente;
4. Una volta che c'è una finestra attiva si può caricare OpenGL, attraverso GLAD (`gladLoadGLLoader`). Nessuna delle funzioni OpenGL sarà valide prima di questa chiamata. Controllare errori e proseguire;
5. Infine, si possono configurare alcune impostazioni di OpenGL, come la dimensione del framebuffer sulla finestra corrente (ottenuta da GLFW), e il *depth testing* (che permette di gestire la trasparenza).

## Arrivare alla draw call

A questo punto abbiamo una finestrella a schermo con un contesto OpenGL vuoto.
Vorremo disegnarci qualcosa.

Il problema è che per disegnare qualcosa dobbiamo fornire un mucchio di informazioni alla GPU (i cosiddetti buffer di cui parlavamo prima), informazioni che dovremo caricare dal disco e offrire all'API OpenGL in maniera strutturata.
Ricordando lo scorso articolo, queste di base saranno:
1. Le **mesh** stesse, cioè i buffer di vertici, normali, coordinate UV, ecc... che rappresenteranno i nostri modelli tridimensionali. Approfondiremo che cosa sono tutti questi buffer aggiuntivi fra poco;
2. I **materiali**: indichiamo come *materiale* la collezione di informazioni che servono a "colorare", o in termini tecnici fare lo *shading* delle mesh. Infatti, queste contengono solo informazioni geometriche: per tutto il resto abbiamo bisogno di particolari programmi (detti *shader*) che portano tali informazioni sullo schermo (*vert* shading) e decidono i colori dei pixel (*frag* shading). Quindi, queste shader come tutti i programmi hanno bisogno di ingressi, che saranno texture, colori, e altri parametri (a seconda della shader stessa). Anche questo lo approfondiremo fra poco.

### Tabelle di risorse

Come ultima cosa prima di addentrarci nella pipeline OpenGL, notiamo che il sistema delle tabelle di risorse dello scorso articolo torna utile anche adesso.
Infatti, quando si carica una risorsa dal disco (sia questo un materiale), la si inserisce in un'entrata della tabella di risorse e si restituisce un puntatore a tale entrata.
Da lì in poi, per accedere alla stessa mesh basta ottenere lo stesso puntatore, senza doverla ricaricare dal disco.

Questo può essere realizzato in maniera indipendente dal tipo di risorsa trattato dotandoci di un riferimento a risorsa generico:
```c
typedef struct {
	char path[DATA_PATH_SIZE];
	void* data;
	int ref_count;
} dataRef;
```

Il puntatore `data` sarà di tipo `void` per puntare a qualsiasi `struct` rappresentante dati.
Attraverso una serie di macro, quindi, si potranno generare le funzioni di accesso alla tabella di qualsiasi tipo di risorsa:
```c
#define DATA_TABLE_DECL(Name, name)										   \
	void print##Name##Table();												\
	name* import##Name(const char* path);									 \
	void free##Name(name* obj);											   \
	void destroy##Name##Table();
```

Nell'implementazione, ciò che chiederemo di sviluppare (specifico alla risorsa) saranno solo le funzioni di caricamento e di liberazione della memoria dedicata alle risorse (le `d_import()` e `d_free()`).
Potremo usare queste funzioni in un altra macro come:
```c
#define DATA_TABLE_IMPL(Name, name)										   \
	dataRef name##_table[DATA_TABLE_SIZE] = {0};							  \
																			  \
	void print##Name##Table() {											   \
		printDataTable(name##_table, (void(*)(void*))print##Name);			\
	}																		 \
																			  \
	name* import##Name(const char* path) {									\
		return importData(path, name##_table, (void*(*)(FILE*))name##_import);\
	}																		 \
																			  \
	void free##Name(name* data) {											 \
		freeData(data, name##_table, (void(*)(void*))name##_free);			\
	}																		 \
																			  \
	void destroy##Name##Table() {											 \
		destroyTable(name##_table, (void(*)(void*))name##_free);			  \
	}																		 
```

Il codice è un po' strano perché usa i nomi generici `Name` e `name` per la risorsa arbitraria.
Per capire meglio, si può provare a sostituire questi nomi con una risorsa vera (magari `mesh`) e vedere il codice che viene generato.
Le funzioni:
```c
// stampa tabella di risorse
void printDataTable(dataTable table, void (*printData)(void*));

// importa una risorsa nella tabella di risorse
void* importData(const char* path, dataTable table, void* (*d_import)(FILE*));

// libera una risorsa dalla tabella di risorse
void freeData(void* data, dataTable table, void (*d_free)(void*));

// libera tutte le risorse e distruggi la tabella di risorse
void destroyTable(dataTable table, void (*d_free)(void*));
```
avranno semplicemente il compito di chiamare le `d_import()` e `d_free()` all'occorrenza per effettuare le operazioni richieste.

### Pipeline

Vediamo velocemente la pipeline di rendering di OpenGL per capire cosa dobbiamo dargli e dove.

![GL pipeline](/pics/blog/opengl_pipeline.svg)

Pipeline di OpenGL

Questo grafico in verità è un po' attempato (l'ho preso [qui](https://en.wikipedia.org/wiki/OpenGL)), ma mostra i componenti che dobbiamo toccare.

Prima di tutto, OpenGL ha bisogno di indicazioni su cosa fare.
Oggi non si usano le display list, ma come abbiamo detto si forniscono buffer e si fanno le draw call.
La filosofia è però la stessa.

I buffer che rappresentano informazioni geometriche sono usati in una prima fase, dove eseguiamo le cosiddette `vert` shader.
Queste hanno semplicemente il compito di:
- Prendere i buffer di vertici, normali, e altre informazioni geometriche;
- Riportarli ad informazioni che stiano prima sullo spazio dello schermo.
In sostanza, le `vert` shader portano i modelli sullo schermo.

A questo punto, però, i modelli non sono ancora stati "disegnati", cioè esistono solo come coordinate sullo schermo.
Dobbiamo quindi *rasterizzarli*, cioè eseguire le `frag` shader.
Queste, in maniera simmetrica alle `vert`, hanno il compito di:
- Prendere le informazioni restituite dalle `vert` shader;
- Restituire il colore di un pixel nello schermo.
Per questo motivo, a volte chiamiamo le `frag` shader anche `pixel` shader.

I pixel renderizzati vanno sul framebuffer, un'array di pixel che poi viene mostrata a schermo.
Fai questa cosa 60 volte al secondo ed hai un hardware renderer.

### Mesh

Le mesh stanno quindi esattamente nello stadio `vert` della pipeline, e anzi sono i buffer che diamo in ingresso alle `vert` shader.
Avevamo visto un semplice caricatore di file `.obj` in passato, ma oggi conviene fare una discussione un attimino più approfondita di tutto ciò che serve per poi poter eseguire le `frag` shader correttamente.

Un file `.obj` più serio ha il seguente aspetto:

```obj
# Blender 4.5.5 LTS
# www.blender.org
o base
v -8.000000 1.956600 -6.000000
v -7.935841 1.996513 -6.064161
v -6.000000 1.956596 -8.000000
[...]

vn -0.0000 0.8491 0.5282
vn -0.5282 0.8491 -0.0000
vn -0.0000 0.8491 -0.5283
[...]

vt 0.513896 0.763869
vt 0.743777 0.756250
vt 0.506277 0.756250
[...]

s 1
f 7/1/1 1/2/1 6/3/1
f 5/4/2 1/2/2 2/5/2
f 8/6/3 4/7/3 5/4/3
[...]
```

Intanto vediamo l'attribuzione all'esportatore (questo file lo ha generato Blender).
Poi ci sono un po' di chiavi, molte associate a buffer:
- `o`: è l'oggetto contenuto dal file. Un file `.obj` può contenere più oggetti, e li distingue così;
- `v`: sono sempre le coordinate 3D dei vertici:
- `vn`: questo è nuovo. Rappresenta il buffer dei vettori *normali*, cioè se vogliamo "perpendicolari" alla superficie dell'oggetto in ogni vertice.
- `vt`: anche questo è nuovo. Rappresenta le coordinate UV (o a volte coordinate `texture`) associate ad ogni vertice. Queste verrano usate per campionare le texture che applicheremo sugli oggetti. La trattazione delle coordinate UV è problema perlopiù degli artisti e di chi costruisce i loro strumenti. A noi basta sapere che ogni vertice mappa 2 spazi vettoriali: quello 3D, dell'oggetto vero e proprio, e quello 2D, delle texture;
- `s`: è lo *smoothing group*, funzione che non ci interessa;
- `f`: questo è il buffer delle facce. Semplicemente, per ogni faccia (triangolare) specifichiamo 3 triple di indici: sono gli indici rispettivamente nel buffer `v`, `vn` e `vt`. Quando si trova `f 7/1/1 1/2/1 6/3/1`, per esempio, bisogna prendere, per il primo vertice, il settimo vertice, la prima normale e la prima coordinata UV, e così via.

![vertici](/pics/blog/render1_vertices.png)

Vertici su Blender

In figura ho cercato di creare uno spazio di lavoro in Blender che dasse l'idea di cosa sono tutte queste informazioni nella mesh vera e propria.
- Nel riquadro a destra, in arancione, ho identificato un singolo vertice. Questo è alla posizione data dal campo `v`, nello spazio 3D;
- In blu vediamo i vettori normali associate ad ogni vertice: questi stanno nei campi `vn`, sempre nello spazio 3D;
- Infine, nel riquadro a sinistra, vediamo lo spazio 2D, cioè lo spazio UV. Anche qui la posizione del vertice è identificata in arancione: questa sarà data dal campo `vt`, nello spazio 2D.

La struttura dei file `.obj` ne rende molto facile l'importazione, in quanto basta:
1. Leggere i buffer in memoria;
2. Costruire le facce indicizzando i buffer appena letti.

Per portare effettivamente tali buffer dentro OpenGL (cioè caricarli sulla memoria della GPU) bisogna parlare un po' di VAO e VBO (c'è un buon articolo [qui](https://dev.to/deyan2306/the-definitive-guide-to-opengl-vbos-vaos-and-ebos-1j0)).
A noi basta dire che:
- Un **VBO** (Vertex Buffer Object) è il buffer di dati da passare effettivamente alla GPU (vertici, normali, quello che ti pare);
- Un **VAO** (Vertex Array Object) è una sorta di "guida" per interpretare i VBO. Torna utile quando si fanno cose complicate (tipo usare lo stesso VBO più volte per risparmiare memoria). I nostri VAO saranno banali.

Quindi, un'altro tipo di informazione di cui OpenGL ha bisogno sono gli *attributi* di vertice: se i VBO sono le informazioni grezze passate alla GPU, gli attributi sono un modo per definire quali informazioni stiamo passando, in che formato, e a quali input delle shader dovranno andare.

Chiudiamo vedendo un po' di codice, che dovrebbe solidificare il tutto:
```c
void generateGLMeshes(mesh* mesh) {
	// genera VBO
	glGenBuffers(1, &mesh->vbo);
	glBindBuffer(GL_ARRAY_BUFFER, mesh->vbo);	
	glBufferData(
		GL_ARRAY_BUFFER, 
		mesh->n_verts * sizeof(vertex), 
		mesh->verts,
		GL_STATIC_DRAW
	);

	// genera VAO
	glGenVertexArrays(1, &mesh->vao);
	glBindVertexArray(mesh->vao);
	glBindBuffer(GL_ARRAY_BUFFER, mesh->vbo);

	// attributi delle posizioni di vertice
	glVertexAttribPointer(
		0,
		3,
		GL_FLOAT,
		GL_FALSE,
		sizeof(vertex),
		(void*)0
	);
	glEnableVertexAttribArray(0);
	
	// attributi delle coordinate UV
	glVertexAttribPointer(
		1,
		2,
		GL_FLOAT,
		GL_FALSE,
		sizeof(vertex),
		(void*)(3 * sizeof(float))
	);
	glEnableVertexAttribArray(1);
	
	// attributi dei vettori normali
	glVertexAttribPointer(
		2,
		3,
		GL_FLOAT,
		GL_FALSE,
		sizeof(vertex),
		(void*)(5 * sizeof(float))
	);
	glEnableVertexAttribArray(2);
}
```

### Materiali

Ora che la mesh sono pronte possiamo passare a tutte le informazioni necessarie alle `frag` shader.

Intanto vediamo cos'è una shader.
Nella prima versione di OpenGL pubblicata da SGI la pipeline era fissa, e se si volevano implementare funzioni particolari si doveva ricorrere all'ARB assembly (vedere [qui](https://mid.net.ua/posts/glarbasm.html)), una sorta di assembly per di alto livello per l'hardware grafico.
In OpenGL 2.0 viene introdotto il [GLSL](https://wikis.khronos.org/opengl/Core_Language_(GLSL)) (GL Shading Language), un simpatico linguaggio simil-C che permette di fare la stessa cosa in maniera più comoda.

Le shader GLSL sono effettivamente programmi, che vengono eseguiti nelle fasi `vert` e `frag` della pipeline di rendering (rispettivamente per ogni vertice e per ogni pixel).
A differenza di altri programmi, però, vengono compilati a tempo di esecuzione da un'applicazione madre (quella che scriviamo noi), e quindi forniti alla GPU.

Tutto il resto diventa chiaro una volta vista una shader, per cui vediamo prima una `vert` shader:
```glsl
#version 330 core

uniform mat4 _model;				  // uniform modello 

uniform mat4 _view;				   // uniform globali
uniform mat4 _projection;
uniform vec3 _cameraPosition;

layout(location = 0) in vec3 aPos;	// input vertice
layout(location = 1) in vec2 aUv;
layout(location = 2) in vec3 aNormal;

out vec2 fragUv;					  // output 
out vec3 fragNormal;
out vec3 fragView;

void main() {
	// trasforma vertice e proietta
	gl_Position = _projection * _view * _model * vec4(aPos, 1.0);

	// passa altri parametri
	fragUv = aUv;
	fragNormal = mat3(_model) * aNormal;
	fragView = _cameraPosition - aPos;
}
```

Qui siamo nella terra delle mesh, per cui vediamo gli ingressi:
- L'`uniform` `_model`. Gli `uniform` sono variabili globali a tutte le istanze di esecuzione della shader: qui li usiamo per rappresentare la matrice di trasformazione di un singolo oggetto;
- Similmente, `_view`, `_projection` e `_cameraPosition` sono `uniform` che rappresentano la matrice di trasformazione della telecamera, la matrice di proiezione, e la posizione della telecamera;
- Quindi abbiamo gli input dalla mesh: la posizione del vertice corrente, la sua coordinata UV e il vettore normale. Notiamo che la parola chiave `location` ci permette di specificare la posizione del buffer che ci interessa, come definito dagli attributi di vertice (vedere scorsa sezione).

La shader dovrà restituire qualcosa, per cui abbiamo:
- `gl_Position`, che è un parametro di ritorno esplicito rappresentante la posizione del vertice nello schermo;
- `fragUv` e `fragNormal`, la coordinata UV e il vettore normale (da passare al `frag`);
- `fragView` è un vettore misterioso che ci servirà dopo (il vettore distanza fra la telecamera e il vertice corrente).

Come vediamo, il codice è banale: si moltiplica per le matrici giuste e si restituiscono i risultati.

Vediamo allora la `frag` shader, che ha bisogno dei materiali veri e propri (texture e altri parametri):
```glsl
#version 330 core

uniform sampler2D _tex0; // texture !

in vec2 fragUv;		  // input dalla vert
in vec3 fragNormal;

out vec4 fragColor;	  // output pixel

void main() {
	// restituisci colore 
	vec3 albedo = texture(_tex0, fragUv).rgb;
	fragColor = vec4(albedo, 1.0); 
}
```

Qui prendiamo in ingresso:
- La texture vera e propria, che sarà un `uniform` (ogni pixel campiona dalla stessa texture, in punti diversi);
- I parametri in ingresso dalla `vert` shader, cioè `fragUv` e `fragNormal`.

In uscita diamo solo il pixel, campionato dalla texture alla posizione `fragUv`.

Abbiamo quindi che per realizzare un materiale basta:
1. Compilare le shader;
2. Fornire alla GPU tutti gli altri buffer, texture, `uniform` e in generale risorse di cui la shader ha bisogno.

Questo è facile in codice.
Per compilare una shader la si importa come stringa da un file e si usano alcune chiamate OpenGL:
```c
GLuint compileShaders(const char* vert_shader, const char* frag_shader) {
	// compila vert
	GLuint vert = glCreateShader(GL_VERTEX_SHADER);
	glShaderSource(vert, 1, &vert_shader, NULL);
	glCompileShader(vert);
	
	// compila frag
	GLuint frag = glCreateShader(GL_FRAGMENT_SHADER);
	glShaderSource(frag, 1, &frag_shader, NULL);
	glCompileShader(frag);

	// crea programma (vert + frag) 
	GLuint program = glCreateProgram();
	glAttachShader(program, vert);
	glAttachShader(program, frag);

	// collega programma 
	glLinkProgram(program);

	// pulisci 
	glDeleteShader(vert);
	glDeleteShader(frag);

	return program;
}
```

Altri oggetti come texture, ecc... si caricano quindi come qualsiasi altro buffer.
Ad esempio, per le `texture` è:
```c
void generateGLTextures(texture* texture) {
	// genera texture 
	glGenTextures(1, &texture->tex);
	glBindTexture(GL_TEXTURE_2D, texture->tex);

	// imposta alcune opzioni 
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);	
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);

	// assegna dati alla texture 
	glTexImage2D(GL_TEXTURE_2D, 
		0, 
		GL_RGBA, 
		texture->width, 
		texture->height, 
		0, 
		GL_RGBA, 
		GL_UNSIGNED_BYTE, 
		texture->data
	);

	// genera mip map (non significativo per ora) 
	glGenerateMipmap(GL_TEXTURE_2D);
}
```

Stare qui a fare altri listati di codice non sarebbe utile.
In ogni caso c'è la [documentazione](https://registry.khronos.org/OpenGL-Refpages/gl4/html/start.html).

Quello che ci basta sapere è che quando la GPU ha:
- Il programma da eseguire (`vert` e `frag` shader);
- I dati su cui eseguire tale programma (buffer, texture, ecc...)
Basta dargli il via e vedere le immagini sullo schermo (se nulla va storto).

### Oggetti

Conviene rappresentare queste informazioni in gerarchie di **oggetti**: un oggetto unirà la sua mesh, il suo materiale, e tutte le altre informazioni necessarie al rendering in un unico luogo.
Con gli oggetti è poi utile realizzare i cosiddetti *scene graph*, cioè organizzarli in gerarchie (banalmente in strutture ad albero).
Questi alberi sono rappresentati, come si può studiare in qualsiasi dispensa di strutture dati, con 2 puntatori (più il puntatore a padre, incluso per comodità).
Vediamo l'oggetto `object`:
```c
typedef struct object {
	char name[OBJECT_NAME_SIZE];
	transform transform;
	mesh* mesh;
	material* material;
	
	// gerarchia 
	struct object* next;
	struct object* parent; // OBJECT_INVALID signal 
	struct object* child;
} object;
```

Gli scene graph dovevano inizialmente essere parte dello standard OpenGL, ma SGI non è riuscita a standardizzarli.

Il nostro approccio dovrebbe essere più che abbastanza.
Basterà prevedere un oggetto `scene` che raggruppa più oggetti in un albero, puntato da un nodo `root`:
```c
typedef struct {
	char name[DATA_NAME_SIZE];

	// oggetti speciali 
	camera camera;
	lighting lighting;

	// oggetti 
	object objects[SCENE_MAX_OBJECTS];
	int n_objects;
	object* root;
} scene;
```

Vediamo che abbiamo bisogno di alcuni oggetti speciali: un'API più simpatica prevederebbe il polimorfismo degli oggetti (o un pattern più complicato come l'[ECS](https://en.wikipedia.org/wiki/Entity_component_system)).
Per ora ci accontentiamo di fare eccezioni per `camera` (la telecamera) e `lightning` (un oggetto che descrive l'atmosfera e l'illuminazione della scena).

Una complicazione interessante è data in fase di serializzazione delle scene.
Visto che queste sono alberi, per serializzarli bisogna adottare un qualche tipo di notazione degli alberi (prendiamo la notazione prefissa).
Inoltre, visto che il numero di figli è arbitrario, abbiamo bisogno di un carattere "sentinella" per la fine di una lista di nodi fratelli (prendiamo `;`).

## La draw call

Ora che è tutto pronto, manca l'ultimo passo per vedere effettivamente qualcosa a schermo.
Riassumiamo brevemente cosa abbiamo fatto. Abbiamo:
- Caricato tutte le risorse che ci servivano dal disco (mesh, shader e texture);
- Caricato la mesh nella memoria delle GPU, gestendo VAO, VBO e attributi di vertice come dio comanda;
- Compilato le shader in programmi, che abbiamo quindi fornito alla GPU;
- Organizzato tutto questo in materiali, che abbiamo assegnato ad oggetti in una certa gerarchia detta scena.

A questo punto tutto quello che resta da fare è, per un dato oggetto, popolare gli `uniform` e fare la draw call, cioè richiedere l'escuzione dei programmi shader e la renderizzazione dell'oggetto.
Facciamo questa cosa percorrendo l'albero della scena, e abbiamo renderizzato suddetta scena.

In codice:
```c
// invia alla GPU tutte le informazioni necessarie allo shader
void populateUniforms(
	material* material,
	transform transform,
	mat4x4 view,
	mat4x4 proj,
	scene* scene
) {
	// costruzione della matrice di modello:
	// scala -> rotazione -> traslazione
	mat4x4 model;
	mat4x4_identity(model);

	mat4x4_scale_aniso(
		model, model,
		transform.scale[0],
		transform.scale[1],
		transform.scale[2]
	);

	mat4x4 rotation;
	mat4x4_rotate_euler(rotation, transform.rotation);
	mat4x4_mul(model, rotation, model);

	mat4x4 translation;
	mat4x4_translate(
		translation,
		transform.position[0],
		transform.position[1],
		transform.position[2]
	);
	mat4x4_mul(model, translation, model);

	shader* shader = material->shader;

	// invia le matrici di trasformazione
	glUniformMatrix4fv(shader->uniformLocations[MODEL],	  1, GL_FALSE, &model[0][0]);
	glUniformMatrix4fv(shader->uniformLocations[VIEW],	   1, GL_FALSE, &view[0][0]);
	glUniformMatrix4fv(shader->uniformLocations[PROJECTION], 1, GL_FALSE, &proj[0][0]);

	// invia i parametri della camera
	glUniform3fv(
		shader->uniformLocations[CAMERA_POSITION],
		1,
		scene->camera.transform.position
	);

	// invia i parametri dell'illuminazione
	glUniform3fv(shader->uniformLocations[SUN_DIRECTION], 1, scene->lighting.sunDirection.position);
	glUniform3fv(shader->uniformLocations[SUN_COLOR],	 1, scene->lighting.sunColor);
	glUniform3fv(shader->uniformLocations[AMBIENT_COLOR], 1, scene->lighting.ambientColor);

	// associa le texture alle texture unit
	for (int i = 0; i < material->n_textures; i++) {
		glActiveTexture(GL_TEXTURE0 + i);
		glBindTexture(GL_TEXTURE_2D, material->textures[i]->tex);
		glUniform1i(shader->uniformLocations[TEX0 + i], i);
	}
}

// disegna un singolo oggetto della scena
void renderObject(
	object* object,
	transform transform,
	mat4x4 view,
	mat4x4 proj,
	scene* scene
) {
	// attiva lo shader
	glUseProgram(object->material->shader->program);

	// aggiorna tutte le uniform
	populateUniforms(
		object->material,
		transform,
		view,
		proj,
		scene
	);

	// seleziona la geometria
	glBindVertexArray(object->mesh->vao);

	// emette la draw call
	glDrawArrays(GL_TRIANGLES, 0, object->mesh->n_verts);
}
```

Abbiamo finito.
Il codice nella repository allegata fa in sostanza tutto questo (più un po di pulizia e di cose noiose in più), e renderizza scene 3D tutte su OpenGL:

![scacchiera](/pics/blog/render1_rendering.png)

Una scacchiera texturizzata!

Vediamo che ci sono tante cose che ho trascurato.

Ad esempio, si potrebbero discutere shader più complicate (il [Gorraud shading](https://en.wikipedia.org/wiki/Gouraud_shading), i termini di riflessione di [Lambert](https://en.wikipedia.org/wiki/Lambertian_reflectance) e di [Phong](https://en.wikipedia.org/wiki/Phong_reflection_model)).

Quindi, si possono fare tante discussioni su come si gestiscono gli oggetti, mesh e materiali, sopratutto nella ricerca di metodi di allocazione che siano efficienti sia per il rendering 3D che per la gestione attraverso strumenti esterni, cosa che si vuole fare ad esempio nello sviluppo di videogiochi.
