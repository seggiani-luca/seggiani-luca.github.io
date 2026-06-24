# Kanban
Server e client per un protocollo scritto in C, che realizza il metodo di gestione del lavoro basato su **kanban**

Sono disponibili i sorgenti del client e del server nella [repository](https://github.com/seggiani-luca/kanban).

I principi che si sono voluti seguire in fase di sviluppo sono:

-   Protocollo di trasmissione livello *application* basato su stringhe ASCII separate da ritorni carrello (`\n`), leggibili da uomo, ispirato a SMTP. 
    Queste stringhe vanno a rappresentare i *comandi* dell'applicazione in maniera espressiva e su cui è facile fare debugging;
-   Comandi fra server e client inviati su TCP, comandi fra client inviati su UDP (con minima affidabilità basata su ritrasmissioni).
    L'uso di socket TCP e UDP sulla stessa porta permette di discriminare gli utenti per porte anche nelle connessioni peer-to-peer;
-   Design *modulare*, dove si divide la funzionalità in appositi moduli `core`, `net`, ecc\... lato client e server, per maggiore leggibilità;
-   Approccio il più semplice possibile: no allocazioni sull'heap, client e server ciascuno su un unico thread di esecuzione Questo è stato fatto per aumentare la robustezza del codice e ridurre la possibilità di errori, con il contro di minore scalabilità.
