# Java RPG
Un JRPG distribuito e collaborativo scritto in Java.
Il nome è un gioco di parole fra "Java RPG" e "Japanese RPG".

![overhead](/pics/java-rpg/battle.png)

Una battaglia in corso

Sono disponibili le repository del [client](https://gitlab.com/seggianiluca2004/jrpg.client) e del [server](https://gitlab.com/seggianiluca2004/jrpg.server).

## Regole di gioco
Il funzionamento del gioco è dettagliato nelle seguenti [slide](https://gitlab.com/seggianiluca2004/jrpg.server/-/raw/main/doc/JRPG.pdf?ref_type=heads&inline=true).
In breve, abbiamo che un giocatore si registra al sistema creando un suo avatar contenente:
- Nome giocatore;
- Immagine;
- Classe (stregone, paladino, ecc...).
Ogni avatar contribuisce un certo numero di punti alle campagne a cui partecipa. 
Per ogni avatar si mantiene un campo livello che incrementa per ogni campagna a cui questo partecipa, e scala il numero di punti contribuiiti. 
Il giocatore che ha creato l'avatar non può usare il suo avatar, ma deve usarne di altri.

Il server rende disponibili un certo numero di campagne. 
Ogni campagna ha bisogno di un certo numero di punti per essere completata. 
Solo quando una campagna viene completata, il server la resetta e si ricomincia da capo.

Il server mantiene, per ogni campagna, una lista di partecipanti.
Il server registra quindi gli avatar dei partecipanti ad una campagna in tale lista. 
I successivi utenti che partecipano alla campagna possono scaricare tali avatar, e usarli ciascuno una sola volta per partecipare ad altre campagne (la stessa o un altra) a loro scelta.

Per accedere alla prima campagna, il server fornisce all'inizio un certo numero di token ad ogni giocatore. 
Questi token possono essere usati per acquistare avatar virtuali. 
La partecipazione ad una campagna con un avatar virtuale porta all'ottenimento di nuovi avatar, e così il giocatore può iniziare a giocare.

![overhead](/pics/java-rpg/avatars.png)

Avatar di un giocatore

In particolare, nel server si mantiene informazione riguardo a:
- I giocatori che partecipano al gioco, i loro avatar personali e gli avatar che possono usare in 
battaglia;
- Le campagne a cui i giocatori possono partecipare, e i nemici da cui sono composte.
Mentre il client:
- Scarica le informazioni dal server;
- Esegue le battaglie in locale e le sincronizza sul server. 

## Implementazione
Il server viene offerto di default a `http://localhost:8080/`, ed è stato implementato con il pacchetto `org.sun.httpserver`. 
Si è deciso di adottare questa soluzione anziché alternative come [Spring Boot](https://docs.spring.io/spring-boot/index.html) in quanto la funzionalità del server è estremamente semplice.
Nel dettaglio, le richieste dei client sono tutte di tipo POST, con parametri passati nel corpo della richiesta. 
Il server quindi si limita a rispondere con oggetti JSON serializzati, o stringhe di auth (Login successful, ecc...).

L'implementazione dell'interfaccia grafica del client viene invece fatta attraverso [JavaFX](https://openjfx.io/).

