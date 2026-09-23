<!-- Unity, in piccolo. -->
<!-- Una quantità poco ragionevole di infrastruttura costruita a mano. -->
<!-- (Quasi) tutto da zero. -->
<!-- Per imparare Unity, devi scrivere Unity. -->

# render2
{{ page_blurb }}
{{ estimate_time }}

Un motore di rendering sperimentale scritto da zero in C, GLAD e GLFW3.
L'idea originale è di avere compatibilità piena con C99, ma per ora sono rimasto a C11. 
La repository si trova [qui](https://github.com/seggiani-luca/render2).

## Funzionalità
Pipeline di rendering 3D accelerata via OpenGL:
- Programmabile via shader GLSL;
- Con supporto alle mesh in formato `.obj`, materiali in formato `.mtl`, e texture in formato `.tga` senza compressione RLE;
- Tipi dedicati al rendering (telecamere con controlli FOV, near e far plane; oggetti "atmosfera" per i vettori di illuminazione e gli uniform shader).

Architettura ad entità:
- Sistema flessibile ed estendibile basato su campi polimorfi (`field`) con vtable dedicate (`int`, `float`, `float2/3/4`, `color`, `string`, `texture`, `mesh`, `material`, `camera`);
- Gerarchia ad albero delle entità con composizione delle trasformazioni.

Interfaccia utente grafica:
- Editor visuale renderizzato direttamente via OpenGL: vista scena, gerarchia ed ispettore;
- Motore di rendering della GUI dedicato.

Serializzazione delle scene:
- Parser e serializer JSON dedicato per il salvataggio e caricamento dello stato delle scene.

L'intero progetto è stato sviluppato con l'obiettivo di essere il più educativo possibile:
- Tutto è sviluppato da zero, in modo da mostrare come funziona ogni passo dello sviluppo di un motore grafico;
- Le soluzioni adottate sono standard e (idealmente) semplici da capire per chi ha un po' di familiarità con altri motori (come Unity);
- Il motore è stato sviluppato per essere versatile e gestire progetti di vario tipo.

## Requisiti di Sistema

Su distribuzioni Linux (Debian/Ubuntu e derivate), puoi installare le dipendenze (GLFW3, OpenGL e libm) con:
```
sudo apt update
sudo apt install build-essential libglfw3-dev libgl1-mesa-dev
```

Quindi hai bisogno di un compilatore C compatibile almeno con C99 (GCC o Clang).

## Compilare

Per ottenere la repository puoi fare la `clone`:
```bash
git clone https://github.com/seggiani-luca/render2.git
```

Quindi c'è un `Makefile` per compilare tutto:
```bash
make run    # compila il progetto e lo esegue
make        # compila soltanto
make debug  # avvia GDB per il debugging, con qualche soppressione abilitata
make clean  # ripulisce gli oggetti
```

## Struttura

L'idea è che puoi fare la `clone` dell'intera repository render2, ed usare la directory madre come base per il tuo progetto.

L'organizzazione che è stata adottata in fase di sviluppo è la seguente:
```
├── dat                # asset (texture, mesh, ecc...)
│   ├── icon           # icone delle finestre
│   ├── material       # materiali (.mtl)
│   ├── model          # modelli (.obj)
│   ├── scene          # scene serializzate (.json)
│   ├── shader         # shader frag e vert (.glsl)
│   └── texture        # texture (.tga senza RLE)
├── lib/glad           # libreria GLAD
├── src                # codice sorgente
│   ├── data           # caricamento di dati dal disco, tabelle dei riferimenti
│   │   ├── material   # caricamento e decodifica materiali
│   │   ├── mesh       # caricamento e decodifica mesh, upload alla GPU
│   │   ├── shader     # caricamento e decodifica shader, compilazione
│   │   └── texture    # caricamento e decodifica texture
│   ├── gui            # toolkit GUI dedicato
│   │   ├── hierarchy  # GUI della gerarchia
│   │   ├── inspector  # GUI dell'ispettore
│   │   ├── render     # backend della GUI, rendering su superfici OpenGL e input
│   │   └── widget     # toolkit di widget di default
│   ├── math           # libreria di algebra lineare dedicata
│   ├── render         # rendering delle entità
│   ├── scene          # gestione delle scene (grafi di entità)
│   │   └── entity     # definizione di entità con campi polimorfi
│   ├── serial         # serializzazione e deserializzazione di scene
│   │   └── json       # motore di serializzazione e deserializzazione JSON dedicato
│   └── window         # adattatore su GLFW per le finestre
└── tst                # soppressioni GDB, test vari
```
