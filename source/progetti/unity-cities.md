# Unity Cities
Un sistema per la generazione di ambienti urbani procedurali usando [Unity](https://www.unity.com) come motore grafico. Questo progetto è stato perlopiù una scusa per approfondire ed implementare una versione dell'algoritmo [WFC (Wave Function Collapse)](https://github.com/mxgmn/WaveFunctionCollapse) per la popolazione di griglie di caselle modulari, basata su regole di adiacenza. La scelta della piattaforma da usare è caduta proprio su Unity in quanto fornisce diverse funzionalità avanzate (sopratutto per quanto riguarda la gestione delle gerarchie di oggetti, il sistema di prefab modulari e delle shader), restando abbastanza semplice e facile da estendere attraverso il sistema di scripting in [C#](https://dotnet.microsoft.com/en-us/languages/csharp). Si rende disponibile una [repository](https://github.com/seggiani-luca/city-unity) con asset e sorgente C#.


![sunset](/pics/unity-cities/sunset_19_30.png)

Autostrada alle 7:30 PM

I risultati non mirano al realismo, ma offrono una prospettiva interessante sulle proprietà emergenti del sistema generativo, nonché un'implementazione particolare dell'algoritmo WFC su griglie multilivello.

## Algoritmo WFC

L'algoritmo WFC (descritto per la prima volta [qui](https://github.com/mxgmn/WaveFunctionCollapse)) popola una griglia NxN in maniera procedurale usando un processo ispirato dal [collasso della funzione d'onda](https://it.wikipedia.org/wiki/Collasso_della_funzione_d%27onda) in meccanica quantistica. Si assume la griglia come composta da _caselle_, e si determina una serie di _regole di adiacenza_ che specificano quali caselle possono essere disposte di fianco ad altre.

Vediamo innanzitutto come queste regole di adiacenza vengono definite nel codice. Per ogni casella si avrà:

```C#
class Tile {
	// number of layers this tile defines adjacency rules for
	[Min(1)]
	public int layers = 1;

	// flag enum for adjacency directions
	[Flags]
	public enum Adjacency
	{
		None = 0,
		North = 1 << 0,
		East = 1 << 1,
		South = 1 << 2,
		West = 1 << 3
	}
		
	// array of adjaciencies for each layer
	public Adjacency[] adjacencies;

	// ...
}
```

cioè un numero di livelli su cui si definiscono adiacenze, e un array di tipi `flag enum` che indicano verso quali direzioni cardinali le adiacenze sono concesse, ad ogni livello.

Lo svolgimento dell'algoritmo, quindi, è sintetizzato grossomodo nei seguenti passaggi:

1.  Si inizializza una griglia NxN di caselle. Ad ogni casella si associa un insieme di stati possibili, e una funzione del numero di stati che rappresenta l'_entropia_ di tale casella. L'entropia dovrà essere monotona crescente col numero di stati possibili. Nel codice la implementiamo come segue:
    
    ```C#    
    // entropy of the tile set
    public float getEntropy()
    {
    	// entropy depedends on number of valid instances
    	int num = instances.Count;
    
    	if (num <= 1)
    	{
    		// if only one instance, tile set is collapsed
    	 	// and entropy is infinite
    		return float.PositiveInfinity;
    	}
    	else
    	{
    		return num;
    	}
    }
    ```
    
    dove notiamo il valore infinito fa da "sentinella" per le caselle già collassate (con un solo numero o meno di stati validi possibili);
2.  Si sceglie una casella a caso e si _collassa_, cioè si sceglie uno a caso fra gli stati possibili e si seleziona come l'unico valido per tale casella. Quindi, questo collassamento viene propagato alle caselle vicine, eliminando in queste gli stati che non sono più validi a seguito del collassamento. Il codice di collassamento di una casella si presenta come segue:
    
    ```C#
    // collapse one tile at a certain coordinate
    private void collapseTile(int r, int c)
    {
    	// get tile set at coordinate
    	TileSet set = grid[r, c];
    
    	// collapse tile set
    	set.collapse(rng);
    
    	// get adjacency
    	Tile.Adjacency[] adjacencies = set.getAdjacencies();
    
    	// use adjacency to mask neighboring tiles
    	if (r < rows - 1)
    	{
    		grid[r + 1, c].restrict(adjacencies, 
    	 		Tile.Adjacency.North);
    	}
    	if (c < cols - 1)
    	{
    		grid[r, c + 1].restrict(adjacencies, 
    	 		Tile.Adjacency.East);
    	}
    	if (r > 0)
    	{
    		grid[r - 1, c].restrict(adjacencies, 
    			Tile.Adjacency.South);
    	}
    	if (c > 0)
    	{
    		grid[r, c - 1].restrict(adjacencies, 
    			Tile.Adjacency.West);
    	}
    }
    ````
    
    dove notiamo la propagazione si fa ad un solo livello (vicini immediati) della casella collassata;
3.  Da qui in poi per ogni casella rimanente si sceglie una per volta quella ad entropia minore, e la si collassa;
4.  Dopo NxN passaggi (incluso quello casuale iniziale) si ha una griglia totalmente popolata e coerente alle regole imposte, che può essere a questo punto disegnata a schermo.

In codice, questo si traduce in una routine di generazione del tipo:

```C#
void generate() {
	// initialize grid
	initGrid();

	// get random tile
	int firstR = rng.Next(rows);
	int firstC = rng.Next(cols);

	// collapse first tile
	collapseTile(firstR, firstC);

	// update tiles
	for (int i = 1; i < rows \* cols; i++)
	{
		// get lowest entropy tile
		int r, c;
		getLowestEntropy(out r, out c);

		// collapse tile
		collapseTile(r, c);
	}

	// realize
	realizeInstances(true);
}
````

In figura si vede come questo processo viene a svolgersi nel tempo, su una griglia 8x8:

![generation](/pics/unity-cities/generation_13_30.gif)

Generazione di una griglia 8x8

Dalla figura si vede come l'algoritmo WFC va a comporre la base della città (cioè la griglia stradale), al di sopra della quale vengono disposti dettagli aggiuntivi come edifici, lampioni, ecc...

## Caselle

Di base una casella è un modulo che rappresenta una certa caratteristica della griglia stradale (una strada dritta, una curva, ecc...) lasciando spazio per dettagli aggiuntivi come palazzi, ecc...

Le dimensioni adottate sono mostrate in figura:

![tile dimensions](/pics/unity-cities/tile_dimensions.png)

Dimensioni di una casella

dove in particolare abbiamo una dimensione di casella di 64x64 metri, una larghezza della carreggiata di 6 metri, ed uno spazio di 29x29 metri fra le strade (che può ospitare edifici o altri dettagli).

Dopo alcuni esperimenti con implementazioni semplici della WFC sono rimasto deluso dalla poca varietà delle griglie stradali che si ottenevano. Quest'implementazione è stata quindi pensata per supportare griglie che si sviluppavano non solo planarmente, ma anche verticalmente su un numero arbitrario di livelli. Questo permette ad esempio di generare griglie più complesse che comprendono:

1.  Un livello base, con autostrade interrate o sistemi di canali;
2.  Un livello stradale intermedio con incroci a raso e passaggi pedonali;
3.  Un livello superiore di autostrade, ferrovie, ecc...

Chiaramente il carico di caselle che vanno modellate si moltiplica, e bisogna tenere a mente che caselle diverse possono avere adiacenze su più livelli.

Per diminuire il numero di modelli da realizzare si è deciso di spostare la complessità nel codice, e permettere a più caselle di sovrapporsi su diversi livelli. Questo permette, ad esempio, di modellare un sovrappasso autostradale e sovrapporlo ad un canale come ad una strada a livello pedonale.

I modelli che sono stati realizzati per le caselle sono quindi i seguenti:

![tiles](/pics/unity-cities/tiles.png)

Insieme di caselle modellate

che dal basso verso l'alto corrispondono con i livelli esemplificati prima: un primo livello di canali, un piano stradale intermedio formato da strade con incroci a raso, ed un livello superiore di autostrade. Sono state modellate anche alcune caselle particolari che uniscono più livelli, come un ponte su un canale o una rampa di accesso al livello autostradale.

Gran parte della complessità del progetto sta negli _script_ C# che sono stati realizzati. In particolare, si è voluto realizzare un sistema che fosse facile ed efficiente per la definizione delle caselle, e che allo stesso tempo restituisse una rappresentazione delle stesse abbastanza efficiente per l'esecuzione dell'algoritmo WFC.

Si ha quindi una distinzione fra due definizioni delle caselle (e quindi due gerarchie di classi), in base al dominio considerato:

-   All'utente interessa poter definire velocemente singole caselle, le relative regole di adiacenza su ogni livello, e sopratutto il modo in cui queste caselle possono essere sovrapposte sui livelli verticali. Per questo si definisce:
    -   La classe `Tile`, che rappresenta lo stato di una casella ad un singolo livello, con il suo modello e le sue adiacenze. Il sistema degli `ScriptableObject` di Unity permette di rendere questa classe facilmente modificabile da interfaccia grafica. Vediamo ad esempio il tile che rappresenta una rampa autostradale:
        
        ![on ramp inspector](/pics/unity-cities/on_ramp_inspect.png)
        
        Inspector di un tile
        
    -   La classe `TileStack`, che rappresenta una serie di liste (`TileList`) contenente gli stati validi per ogni livello di un certo tipo di casella. Anche questa classe ha una comoda interfaccia grafica, vediamo ad esempio lo stack che rappresenta le caselle stradali semplici:
        
        ![road stack inspector](/pics/unity-cities/road_stack_inspect.png)
        
        Inspector di uno stack
        
-   All'algoritmo WFC interessa avere una rappresentazione efficiente di tutti gli stati possibili per ogni casella. Per questo si è ritenuto necessario perdere l'astrazione delle `TileList` e collassare gli stati possibili ad una lista unificata, rappresentata come un insieme hash. Questo è utile in quanto semplifica di molto la logica che verifica se le regole di adiacenza sono rispettate (non si devono considerare ogni volta tutti i casi in quanto sono precalcolati).
    -   Una singola istanza realizzata di casella viene rappresentata da una classe `TileInstance`. Questa unifica un singolo stato completo di una casella (collassato lo stato ad ogni livello);
    -   L'insieme completo di istanze su cui l'algoritmo WFC esegue viene detto `TileSet`, che contiene l'insieme hash vero e proprio.

Questa configurazione permette quindi sia un semplice _authoring_ delle caselle che una semplice implementazione dell'algoritmo WFC. Come abbiamo visto, l'authoring si fa via interfaccia grafica.

Quindi, la trasformazione dei `TileStack` in `TileSet` si fa in maniera ricorsiva con backtracking considerando tutte le possibili combinazioni di stati ad ogni livello. Per questo è predisposta una funzione:

```C#
// performs a recursive step to get the combinations from a tile stack
private static void populateTileSet(
	TileStack.TileList[] lists,           // tile lists
	int depth,                            // depth of the current step
	List<TileInstance.Component> current, // current component list 
	TileSet result)                       // result set 
{
	// did you reach the end?
	if (depth == lists.Length)
	{
		// end reached, append this instance 
		TileInstance instance 
			= new TileInstance(result.layers, current);
		result.instances.Add(instance);
		return;
	}

	// get the next tile list
	Tile[] tiles = lists[depth].tiles;

	// go through each tile in the list
	foreach (Tile tile in tiles)
	{
		// generate the tile component from this tile
		TileInstance.Component component 
			= new TileInstance.Component(tile, orientation);

		// add it to the current set
		current.Add(component);

		// go to the next step
		populateTileSet(lists, depth + 1, current, result);

		// remove tile component from the current set
		current.RemoveAt(current.Count - 1); // backtrack
	}
}
```

A questo punto la logica dell'algoritmo WFC è semplice. Ad esempio, per restringere una `TileSet` ai soli stati concessi da un adiacenza in una data direzione, basta controllare tutti i casi precalcolati:

```C#
// collapse tile set to tiles that satisfy given adjacency in direction
public bool restrict(
	Tile.Adjacency[] baseAdjacencies, // requested adjacency 
	Tile.Adjacency direction)         // in which direction
{
	// get opposite direction 
	Tile.Adjacency opposite = Tile.oppositeAdjacency(direction);

	// check all candidate tile instances
	int removed = instances.RemoveWhere(tileInstance =>
	{
		// get the adjacencies of the candidate
		Tile.Adjacency[] candidate = tileInstance.getAdjacencies();

		// check on each layer
		for (int i = 0; i < layers; i++)
		{
			// base tile has adjacency in this direction?
			bool baseHasEdge
	 			= (baseAdjacencies[i] & direction) != 0;

			// candidate has adjacency in this direction?
			bool candidateHasEdge 
	 			= (candidate[i] & opposite) != 0;

			// if adjacencies don't match remove candidate
			if (baseHasEdge != candidateHasEdge) return true;
		}

		return false;
	});

	// return if something was removed
	return removed > 0;
}
```

## Edifici

Per riempire gli spazi liberi delle caselle sono stati modellati alcuni edifici. Questi sono stati divisi, per ispirazione da videogiochi come [SimCity](https://www.ea.com/it-it/games/simcity), in categorie, fra cui:

-   Edifici residenziali;
-   Edifici commerciali;
-   Edifici industriali.

L'idea dietro questa suddivisione è quella di poter, in fase di generazione, individuare diverse regioni della città a concentrazioni diverse di edifici di un certo tipo, come zone industriali, residenziali, commerciali, ecc...

I modelli che sono stati realizzati per gli edifici sono quindi i seguenti:

![buildings](/pics/unity-cities/buildings.png)

Insieme di edifici modellati

Oltre a questi modelli, sono stati poi realizzati altri dettagli minori (da sovrapporre sulle caselle popolate da edifici), come ad esempio lampioni, vegetazione, ecc... Questi vengono sempre distribuiti in maniera proceduale in zone appropiate (lampioni a bordo strada, vegetazione nei parchi, ecc...).

Anche per gli edifici si sono fatte delle considerazioni riguardo alla modalità della generazione. Ad esempio, per realizzare la divisione fra diverse regioni si è usato un approccio basato sul [rumore di Perlin](https://en.wikipedia.org/wiki/Perlin_noise). Sostanzialmente, per ogni casella viene calcolato un rumore casuale campionato dal rumore di Perlin (che è spazialmente corente e porta a regioni distinte). Questo va ad indicizzare una delle regioni possibili (e quindi di tipologie di edificio possibili). In codice:

```C#
// sample perlin noise
float noise = Mathf.PerlinNoise(
	origin.position.x \* zoneFrequency + i \* zoneFrequency + noiseOffset,
	origin.position.z \* zoneFrequency + i \* zoneFrequency + noiseOffset
);
noise = Mathf.SmoothStep(0f, 1f, noise);

// make selection
int selection = (int)(noise \* factors.list[i].options.Length);
```

Un esempio dell'esecuzione di questo algoritmo si ha visualizzando come vengono disposte le zone. Indichiamo in verde le zone residenziali, in blu le zone commerciali, ed in giallo le zone industriali:

![zoning](/pics/unity-cities/zoning.png)

Suddivisione in zone

## Conclusioni

Il sistema così realizzato permette di definire velocemente insiemi di stati di caselle a partire da asset generati a mano, modificare le regole di adiacenza e ricavare un gran numero di varietà di ambienti urbani.

![overhead](/pics/unity-cities/overhead_13_30.png)

Vista dall'alto, 8x8

Ci sono molti elementi del progetto che non sono stati visti in questo writeup. Ad esempio:

-   Sono state scritte shader apposite che permettono di visualizzare sui modelli effetti di ombra precalcolati da software esterni;
-   Diverse caratteristiche della città generate sono ulteriormente randomizzate dopo la generazione, come l'altezza dei palazzi, la distribuzione della vegetazione e altri dettagli;
-   Sono stati realizzati diversi effetti grafici, ad esempio atmosferici (nuvole, ciclo del giorno e della notte) o a livello stradale (accensione dei lampioni a ore prefissate del giorno, ecc...);
-   La gestione degli edifici non è limitata al singolo fattore tipologia, ma può essere estesa a più fattori attraverso un meccanismo di selezione multidimensionale (si pensava di implementare un ulteriore fattore densità che caratterizzasse le zone ulteriormente). Si rende disponibile anche un' integrazione nell'interfaccia grafica per tale meccanismo.

Il sistema presenta anche limitazioni. Ad esempio, la propagazione ad un solo livello delle caselle porta a volte al raggiungimento di stati inconsistenti, sopratutto su griglie di grandi dimensioni. Questo si traduce in un "buchi" nella griglia che non hanno una casella valida. Si potrebbe pensare di risolvere il problema aggiungendo un sistema di propagazione ricorsiva delle variazioni nella griglia (che però diventa molto velocemente pesante e inefficiente), oppure introducendo una serie di caselle "wildcard" che possono riempire i buchi con un adiacenza ad ogni livello. In ogni caso, modificando l'insieme di caselle fornite al sistema, si può migliorare la qualità delle griglie ottenute (ad esempio fornendo una maggiore varietà di caselle con diverse adiacenze).

Per chi volesse approfondire, c'è una [repo](https://github.com/seggiani-luca/city-unity) con tutto il sorgente e gli asset usati, più una scena di esempio (quella usata finora come esempio).

![night](/pics/unity-cities/night_06_00.png)

Cielo di notte alle 6:00 AM
