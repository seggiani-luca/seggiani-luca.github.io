# Chi sono?

Studente di Ingegneria Informatica.

Questo è il mio sito Web personale. 
Lo uso per raccogliere cose che ho fatto, fra cui:
- Appunti ed esercizi dei corsi universitari che ho seguito;
- Progetti di sviluppo software che ho realizzato;
- Altre cose che mi passano per la testa.

## Progetti

Ho raccolto alcuni dei miei [progetti](/progetti.html) più significativi, con allegate le relative documentazioni.

{{ create_list progetti recurse=True blurb=True }}

## Blog

Qualche volta scrivo di programmazione, tecnologia o altre cose che trovo interessanti.
Gli ultimi 10 post dal [blog](blog.html) sono:

{{ create_list blog number=10 blurb=True }}

## Appunti

Probabilmente sei qui per i miei [appunti](/appunti.html) (corsi di Ingegnera Informatica e affini).
Ricordo che potrebbero esserci refusi, e questo materiale non intende in nessun modo sostituirsi ai libri di testo o alle lezioni frontali.

<p class=label>Università di Pisa (2023/2026)</p>

{{ create_list appunti/triennale recurse=True blurb=True }}

<p class=label>Politecnico di Torino (2026/20XX)</p>

{{ create_list appunti/magistrale recurse=True blurb=True }}
