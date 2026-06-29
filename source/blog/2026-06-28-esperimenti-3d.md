# 2026 06 28 esperimenti 3d
Da un po' di tempo sono interessato allo sviluppo di motori grafici.
Questo perché ho avuto un po' di esperienza con [Unity](https://unity.com/) (ad esempio [qui](/progetti/unity-cities.html)), e prima o poi era chiaro che mi sarebbe venuto voglia di provare a reimplementare qualcosa del genere.

Ora, visto che è abbastanza improbabile che io reimplementi un motore che è in circolazione da anni e viene mantenuto da un team di diverse persone, per iniziare mi sono accontentato di renderizzare qualche wireframe a schermo.
Avevo sentito parlare della [SDL](https://www.libsdl.org/) (e l'avevo anche usata per qualche progetto stupido), per cui ho deciso di iniziare da lì per disegnare qualcosa a schermo.

Nota!
Ho buttato il codice descritto in questo articolo in questa [repository](https://github.com/seggiani-luca/rendering-experiments/tree/main/render_0).
Sulla mia macchina (Arch Linux, aggiornato a Giugno 2026) funziona, ma non ho fatto nessuno sforzo per assicurarmi che fosse portatile o quantomeno stabile.
Più che altro lo allego a scopo sperimentale e didattico.

## Buffer

L'idea è di avere un semplicissimo header `buffer.h` che fa da "lavagna", cioè permette di:
1. Creare una finestra contenente un buffer di pixel;
2. Cambiare il colore di un qualsiasi pixel.

Questa funzionalità di base si può quindi estendere per disegnare linee e triangoli.
Il risultato è una cosa del genere:

```c
// buffer.h

// gets called once at the start of runtime 
void init();

// gets called once at the end of runtime 
void destroy();

// gets called for each frame
void update(float delta);

// typedef for colors
typedef uint32_t color;

// gets a single SDL color out of RGB components
color rgb(uint8_t r, uint8_t g, uint8_t b);

// plots a pixel on the screen
void pixel(int x, int y, color col);

// plots a line on the screen
void line(int x0, int y0, int x1, int y1, color col);
```

L'implementazione di questi è banale (per la SDL ci sono ottimi tutorial come [questi](https://lazyfoo.net/tutorials/SDL/)).
Il tipo `color` è necessario in quanto per SDL un colore è rappresentato da 3 interi su 8 bit (`r`, `g` e `b` per i canali Rosso, Grerde e Blu), impacchettati in un intero da 32 bit secondo un formato specifico (attraverso `SDL_MapRGB(surface->format, r, g, b)`).

Più interessante è il tracciamento delle linee, che usa l’[algoritmo di Bresenham](https://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm).
Non starò a dilungarmi sulla teoria (c'è un ottima spiegazione [qui](https://www.youtube.com/watch?v=CceepU1vIKo)).
L’idea è discretizzare una retta scegliendo l’asse dominante (x o y), cioè la direzione in cui avanzare a ogni step.
Durante l’avanzamento si accumula un errore rispetto alla retta ideale; quando questo supera 0.5, si incrementa anche la coordinata sull’asse secondario.


A questo punto dobbiamo:
1. Importare delle *mesh*, cioè degli insiemi di triangoli che rappresentano gli oggetti che vogliamo renderizzare a schermo;
2. Definire delle *scene*, cioè collezioni di mesh disposte nello spazio;
3. Fare un po' di algebra lineare per ricavare la posizione dei punti delle mesh sullo schermo, in relazione ad una certa *telecamera* virtuale.

## Mesh

Per il punto 1. ho deciso di importare il formato [Wavefront `.obj`](https://en.wikipedia.org/wiki/Wavefront_.obj_file) in quanto è semplice e in formato testo.
Blender, con un po' di configurazione, permette di generare file `.obj` molto semplici:

![preset blender](/pics/blog/render0_blender_preset.png)

Configurazione exporter Blender

La cui struttura testuale è:
```obj
# vertici
v -6.000000 0.000000 8.000000
v -4.000000 0.000000 8.000000
v -4.000000 0.000000 6.000000
[...]

# facce
f 2 5 1
f 5 6 4
f 9 11 8
[...]
```

Tutte le informazioni in un file `.obj` sono rappresentate da buffer.
Il primo buffer (sempre presente) è quello dei vertici, rappresentati dal carattere `v` e 3 numeri in virgola mobile (le coordinate del vertice).
In file più complessi ci sono poi i buffer delle normali e delle coordinate UV (di cui forse parlerò in seguito).
In fondo c'è sempre un buffer di facce, che altro non sono che triple di puntatori ai buffer definiti prima.
Ad esempio, in questo caso banale dove c'è solo il buffer di vertici, una faccia è data da 3 indici, che indicizzano appunto i vertici nel buffer.

Per rappresentare una mesh in memoria ci dotiamo quindi dei seguenti struct:
```c
typedef struct {
	int a;
	int b;
	int c;
} triangle;

typedef struct  {
    // array di vertici
	vector3* verts;
	int n_verts;

    // array di triangoli
	triangle* tris;
	int n_tris;

    // numero di riferimenti
	int refs;
} mesh;
```
che rispecchiano direttamente la struttura del formato `.obj`.
Basterà leggere tutte le righe di un file in tale struct per caricare una mesh in memoria: quindi questa potrà essere renderizzata.

Una particolarità è data dal campo `refs`.
Assunto che in una scena una stessa mesh può essere usata più volte, è opportuno dotarsi di una tabella di risorse: quando si carica una mesh per la prima volta, la si inserisce in un'entrata della tabella di risorse e si restituisce un puntatore a tale entrata.
Da lì in poi, per accedere alla stessa mesh basta ottenere lo stesso puntatore, senza doverla ricaricare dal disco.

Questo meccanismo (sostanzialmente di caching) viene implementato creando una tabella:
```c
typedef struct {
	char path[MESH_NAME_LEN];
	mesh* mesh;
} mesh_cache_entry;

// tabella di mesh 
static mesh_cache_entry mesh_cache[MESH_CACHE_LEN];
```
e definendo una funzione che importi le mesh, solo dopo aver controllato di non averle già in cache.
In pseudocodice:
```c
mesh* import_mesh(const char* path) {
	// cerca nella cache 
	for(int i = 0; i < MESH_CACHE_LEN; i++) {
		mesh_cache_entry* entry = &mesh_cache[i];

		if(entry->mesh != NULL && strcmp(entry->path, path) == 0) { // match su percorso
			entry->mesh->refs++; // conta
			return entry->mesh;  // restituisci
		}
	}

    // carica mesh da file
    [...]
	
    // alloca mesh
	mesh* m = malloc(sizeof(mesh));
	*m = (mesh){verts, n_verts, tris, n_tris, 1};

    // registra mesh nella cache
	for(int i = 0; i < MESH_CACHE_LEN; i++) {
		mesh_cache_entry* entry = &mesh_cache[i];

		if(entry->mesh == NULL) {
			strncpy(entry->path, path, MESH_NAME_LEN - 1); // copia percorso
			entry->path[MESH_NAME_LEN - 1] = '\0';
			entry->mesh = m;                               // assegna mesh
			break;
		}
	}

	return m;
}
```

In questo caso il contatore di riferimenti `refs` è utile per capire se una mesh nella tabella può essere liberata, o è ancora riferita da oggetti nella scena.

## Scene

Una scena è un albero di oggetti, che dovranno avere degli attributi come:
1. Posizione, rotazione e scala nella scena (solitamente detti *transform* o *trasformazione* dell'oggetto);
2. Mesh che usano;
3. Altri attributi grafici come colore, materiale, ecc...

Quindi, se si accetta di adottare il modello più semplice possibile, una scena è una lista concatenata di oggetti da renderizzare in sequenza.
In codice questo equivale a:

```c
typedef struct object {
	// nome
	char name[OBJ_NAME_LEN + 1];

	// mesh e colore
	mesh* mesh;
	color col;

	// transform 
	vector3 point;
	vector3 euler;
	vector3 scale;

	struct object* next;
} object;

// lista di oggetti da renderizzare, sostanzialmente la scena
extern object* obj_list;
```

Questo modello rende sia il rendering che la serializzazione/deserializzazione di scene molto semplice, in quanto in entrambi i casi si scorrono liste (e le liste sono molto facili da serializzare, a differenza degli alberi che vanno scritti in qualche tipo di ordine).

Notiamo che si usano i tipi `vector3`: per questi ho definito il mio piccolissimo header di algebra lineare (`vector.h`), che include definizioni di vettori, matrici, e alcune funzioni di base.
Lo vedremo più nel dettaglio fra poco.

Vediamo anche che la rotazione viene codificata nel campo `euler`: gli [angoli di Eulero](https://it.wikipedia.org/wiki/Angoli_di_Eulero) sono un modo semplice (e in verità abbastanza limitato) per rappresentare la rotazione degli oggetti nello spazio.
Consistono nei 3 angoli (attorno agli assi X, Y e Z) con cui dobbiamo ruotare il corpo per ottenere una certa rotazione.
Notiamo che l'ordine con cui si applicano le rotazioni è importante!
Qui si è usato l'ordine Z, Y, X.

## Rendering

Possiamo finalmente provare a renderizzare qualcosa a schermo.
Il piano è semplice: una volta che le mesh sono state configurate e assemblate in una simpatica lista di oggetti (che chiamiamo scena), basterà scorrere tutti gli oggetti, disegnandone ciascuno a schermo.

Per disegnare un oggetto, che ha la sua posizione, rotazione e scala (trasformazione) nella secna, dobbiamo capire da dove lo guardiamo, cioè definire una telecamera virtuale.
La mettiamo nel seguente struct:

```c
typedef struct {
	vector3 point; // dove si trova?
	vector3 euler; // dove sta guardando?
	float focal;   // lunghezza focale
} camera;

// telecamera della secna 
static camera cam;
```

`point` è chiaramente la posizione della telecamera.
`euler` è la rotazione, nello stesso formato visto prima per gli oggetti.
Infine, `focal` è la lunghezza focale.

Non bisogna essere fotografi per capire il ruolo della lunghezza focale.
L'idea è di considerare una [camera oscura](https://it.wikipedia.org/wiki/Camera_oscura), cioè una scatola con un foro che lascia passare la luce.
Dal punto di vista matematico, il foro è infinitamente piccolo e della scatola ci interessa solo la parete opposta al foro.
Questa parete sarà la superficie su cui comparirà la proiezione bidimensionale del mondo tridimensionale che sta dall'altra parte del foro.

Questa situazione è modellizzata in 2D nel seguente Desmos (metà del motivo di questa spiegazione era provare ad includere i grafici Desmos nella pagina).
Si possono spostare i punti P1, P2 e P3, e vedere come viene aggiornata la proiezione sulla parete della camera oscura!

<iframe src="https://www.desmos.com/calculator/6igulxk1ql" class="calc"></iframe>

Camera oscura in 2D

La stessa cosa si ripete in 3D, per cui possiamo fare cose più sofisticate come nel seguente Desmos:

<iframe src="https://www.desmos.com/3d/vkuycclpal" class="calc"></iframe>

Camera oscura in 3D

In questo caso ho scelto di renderizzare un cubo in 3D, con la possibilità di ruotarlo.
Per le matrici di rotazione (che ci torneranno utili a breve) rimando a quanto scritto [qui](https://seggiani-luca.github.io/quartz/Meccanica-Razionale/Matrici-di-rotazione), che è un po formale, ma dovrebbe spiegare la forma che usiamo:

```c
matrix3 rot_matrix(axis ax, float angle) {
	float c = cos(angle);
	float s = sin(angle);

	switch(ax) {
		case X:
			return (matrix3) {{
				{ 1,  0,   0},
				{ 0,  c,  -s},
				{ 0,  s,   c}
			}};
		case Y:
			return (matrix3) {{
				{ c,  0,  s},
				{ 0,  1,  0},
				{-s,  0,  c}
			}};
		case Z:
			return (matrix3) {{
				{ c, -s,  0},
				{ s,  c,  0},
				{ 0,  0,  1}
			}};
		default:
			return (matrix3){0};
	}
}
```

Quindi, è bastato definire una semplice mesh direttamente in Desmos, trasformarla con la matrice di rotazione su Z, e proiettare.

La stessa cosa è quella che facciamo in codice C nell'applicazione:
```c
void render_obj(const object* obj) {
	if(obj->mesh == NULL) return;

    // array di vertici proiettati
	vector3* proj_verts = malloc(sizeof(vector3) * obj->mesh->n_verts);

    // itera su tutti i vertici
	for(int v = 0; v < obj->mesh->n_verts; v++) {
        // trasforma vertice
		vector3 vert = obj->mesh->verts[v];
		vert = transform(vert, obj->point, obj->euler, obj->scale);
	
        // proietta vertice e memoriza
		vector3 proj = project(vert);
		proj_verts[v] = proj;
	}

    // disegna triangoli
	for(int t = 0; t < obj->mesh->n_tris; t++) {
		// get triangle
		triangle tri = obj->mesh->tris[t];
        line(
			proj_verts[tri.a].x, proj_verts[tri.a].y,
			proj_verts[tri.b].x, proj_verts[tri.b].y,
			obj->col
		);
	    line(
			proj_verts[tri.b].x, proj_verts[tri.b].y,
			proj_verts[tri.c].x, proj_verts[tri.c].y,
			obj->col
		);
		line(
			proj_verts[tri.a].x, proj_verts[tri.a].y,
			proj_verts[tri.c].x, proj_verts[tri.c].y,
			obj->col
		);
	}

    // libera array di vertici proiettati 
	free(proj_verts);
}
```

Per disegnare i triangoli, facciamo semplicemente uso della funzione `line()` chiamata su tutte le coppie di vertici che formano i triangoli, come definito dalla mesh.

La `project()` equivale a come l'abbiamo vista in Desmos:
```c
vector3 project(vector3 vert) {
    // trasla nello spazio della telecamera
    vector3 d = vec_pl_vec(vert, vec_by_sca(cam.point, -1));
	d = rotate(d, vec_by_sca(cam.euler, -1));

    if (d.z <= 0.01f) // salta

    // formule di proiezione
	float proj_x = (cam.focal * d.x) / d.z;
	float proj_y = (cam.focal * d.y) / d.z;

    // scala sullo schermo
	float screen_x = WIDTH  * 0.5f + proj_x;
    float screen_y = HEIGHT * 0.5f - proj_y;

	return (vector3){screen_x, screen_y, 0};
}
```
cioè prima dobbiamo riportarci allo spazio della telecamera (essenzialmente applicare la posizione della telecamera e la sua rotazione).
Quindi si possono applicare le formule di proiezione, con una leggera complicazione data dal fatto che dobbiamo riportare tutto nello spazio di coordinate dello schermo.

La `transform()` è invece l'applicazione di alcune funzioncine di algebra lineare:

```c
vector3 transform(vector3 vert, vector3 point, vector3 euler, vector3 scale) {
	vert = vec_by_vec(vert, scale); // scala  (moltiplicazione membro a membro)
	vert = rotate(vert, euler);     // ruota  (moltiplicazione per le 3 matrici di rotazione Z, Y e X)
	vert = vec_pl_vec(vert, point); // trasla (addizione vettoriale)
	return vert;
}
```

La `rotate()`, come notato dai commenti, consiste in 3 moltiplicazioni matriciali, una per ciascuna matrice di rotazione Z, Y e X:
```c
vector3 rotate(vector3 v, vector3 euler) {
	v = mat_by_vec(rot_matrix(Z, euler.z), v);
	v = mat_by_vec(rot_matrix(Y, euler.y), v);
	v = mat_by_vec(rot_matrix(X, euler.x), v);

	return v;
}
```

Il risultato di tutto questo codice è che, con le mesh giuste e una scena appositamente configurata, si possono renderizzare dei semplici wireframe:


![scacchiera](/pics/blog/render0_rendering.png)

Una scacchiera!

Ci sono tante cose che non sono state discusse qui (di base il clipping, poi funzioni avanzate come le texture, i materiali, ecc...).
Chiaramente, oggi come oggi non ha particolare significato reimplementare tutto da 0 in software, sopratutto quando esistono API come OpenGL che permettono di fare tutto, in hardware, e meglio.
Infatti, in altri articoli spero di poter parlare di OpenGL e presentare una piccola demo.
In ogni caso, spero che quanto visto qui possa essere stato utile o almeno interessante.
Cheers!
