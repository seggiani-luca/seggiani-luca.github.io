# 2026 06 25 via al nuovo sito
Test. Prova.
Ho riscritto tutto il mio sito perché aggiornare la scorsa versione mi faceva venire il mal di testa.
La [repository](https://github.com/seggiani-luca/seggiani-luca.github.io) con tutto il codice (incluso quello di questa pagina) è al solito posto.

L'idea era di usare qualcosa come [Jekyll](https://jekyllrb.com/) in quanto:
- Risulta già integrato in [GitHub Pages](https://docs.github.com/en/pages), servizio di "hosting" che già usavo (e uso ancora), ben integrato con gli strumenti di CI di GitHub;
- Mi permette di scrivere comodamente in Markdown, e si occupa della traduzione in HTML autonomamente.

Il problema è che questo non è particolarmente divertente, e mi richiede di (re)imparare un nuovo strumento.
Ad oggi non ho trovato problemi che non si risolvano lanciandogli contro Python.
Quindi, in mezza giornata e con l'aiuto di Google, ho creato uno script:

```python
[...]

# pulizia 
clear_dir(stt)

# percorri file sorgente 
for fr in src.rglob("*"):
    to = stt / fr.relative_to(src)

    # ricostruisci directory
    if fr.is_dir():
        to.mkdir(parents=True, exist_ok=True)
    
    else:
        to.parent.mkdir(parents=True, exist_ok=True)
 
        # converti file a HTML
        proc = process(fr)
        to = to.with_suffix(".html")
        to.write_text(proc, encoding="utf-8")
```

L'idea è di avere 2 directory separate:
- Una directory `source`, che contiene il mio sorgente in Markdown (da cui generare la pagina);
- Una directory `static`, che contiene le pagine HTML generate.

Quindi, il sito si costruisce:
1. Percorrendo la directory `source`;
2. Prendendo i file `.md` e convertendoli in `.html`;
3. Inserendo tali file in una gerarchia di directory, a partire da `static`, che rispecchi quella di `source`.

## Preprocessore

La funzione `process()` si occupa della conversione da `.md` a `.html`.
La maggior parte del lavoro sporco viene fatta dalla libreria [markdown-it-py](https://pypi.org/project/markdown-it-py/).
Ciò che ho introdotto è uno stadio di preprocessing che mi permette di usare macro speciali nel mio Markdown.
Ad esempio, per realizzare un indice di pagine, posso dire:

```Markdown
# Indice
Il mio splendido indice

\{\{ create_list pagine \}\}
```

dove mi è toccato fare l'escape delle parentesi graffe perché il mio codice è anche troppo zelante nel riconoscere le macro.

Il seguente codice viene preso dallo script Python, espanso attraverso la regex (abbastanza complicata, per visualizzarla è comodo [regex101](https://regex101.com/)):

```
\{\{\s*(\w+)\s+(.*?)\s*\}\}
```

Questa mi dà due gruppi:
- La parola chiave che identifica la macro (qui `create_list`);
- Una lista di argomenti.

Quindi posso passare tali argomenti alla macro giusta (individuata sempre nello script), e realizzare qualsiasi funzionalità dinamica che voglio in Python.
In questo caso mi basta scansionare la directory indicata e realizzare un'elenco di link alle entrate trovate.
Così ho realizzato tutti gli indici del sito.

Altre macro si possono realizzare a discrezione (magari per elementi di pagina che vanno ripetuti fra più pagine, ecc...).
Per ora non ho trovato altre cose da farci.
Però si può chiamare qualsiasi funzione del Python (uso la mappa `global()` per risolvere la parola chiave), quindi sicuramente c'è la possibilità di fare danni.
Ad esempio, se volessi implementare qualcosa di ridicolo come un generatore casuale di classifiche delle canzoni dei Sonic Youth che posso piazzare dove mi pare in una pagina, potrei farlo senza chiedere il permesso a nessuno.
Forse vale la pena di aver riscritto la mia versione peggiore di Jekyll.

## Temi

Non c'è gusto a sviluppare siti Web senza toccare mai il CSS.
Quindi ho creato un'ulteriore directory, `theme`, dove ho inserito:
- Gli stili CSS e vari effetti grafici;
- Template per alcune sezioni di pagina che voglio controllare a parte (header e footer).

Quello che faccio nello script Python è:
- Copiare tutti i file non `.html` della directory `theme` nella directory `static`;
- Includere le sezioni di pagina giuste (header e footer) in ogni pagina statica generata.

In questo modo posso stilizzare il sito in maniera simile (se non più rudimentale) a quanto offerto da Jekyll.

Resta da creare un tema vero e proprio.
Sono rimasto affascinato da siti "vecchio stile" come quello di [wriks](https://www.wriks.motorcycles/), se non da siti vecchi davvero come [Pouet](https://www.pouet.net/) (che ho spudoratamente copiato).
Quindi ho cercato di replicare quello stesso stile, testo piccolo, un sacco di effetti base CSS e loghi in stile demoscene.
Ho persino aggiunto i badge 88x31 delle tecnologie usate a fondo pagina, per il massimo effetto "Netscape Navigator".

Trovo che il risultato è (a me) abbastanza gradevole.
Se non altro, uno stile così minimalista rispetta l'architettura (altrettanto minimalista) di tutto il sito.
Semplice è bello.

## Logo

Pouet (link sopra) ha di interessante che il logo cambia ogni volta che si aggiorna la pagina.
Quindi ci sono tutti questi loghi carini che si alternano.

Fare la stessa cosa, dove ogni logo è il mio nome, mi sembrava un po' troppo, per cui ho deciso di fare almeno un logo in stile demoscene (alcuni ottimi esempi si trovano qui [qui](https://demoscenelogogallery.org/), comunque lo stile è quello delle distribuzioni software pirata che si trovavano su PirateBay, pensa Razor1911).
Lo stile che ho cercato di imitare è quello dei loghi in 3D, di un bell'arancione che complementa bene i toni di blu del resto della pagina.
Su Blender ho realizzato la seguente scena:

![logo blender](/pics/blog/logo_blender.png)

Scena su Blender

dove semplicemente ho estruso il testo generato da [questo](https://www.dafont.com/it/father-galaxy.font?text=seggianiLu.ca) font, con la stringa `seggianiLu.ca` (il punto è perché il nome di dominio `seggianilu.ca` è libero e prima o poi lo comprerò dall'autorità canadese).
Ho usato una versione estrusa e con le normali invertite del logo per realizzare un "contorno" in tinta unita del testo (come si vede [qui](https://bnpr.gitbook.io/bnpr/outline/inverse-hull-method))
Per il materiale ho realizzato la seguente shader NPR con l'editor di Blender:

![logo shader](/pics/blog/logo_shader.png)

Shader su Blender

dove l'obiettivo è di avere dei colori arancioni fissi, e separazione fra i caratteri data dall'effetto Fresnel.
Quindi, ho preso l'immagine renderizzata e l ho portata su Gimp per alcuni ritocchi (un po' di effetti di luce e di ombra).

Il risultato è il seguente, che credo sia abbastanza carino:

![log](/art/logo.png)

Logo finito
