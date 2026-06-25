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
