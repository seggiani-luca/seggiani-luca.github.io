# 2026 07 24 Lauree Tesi e pensieri

A quanto pare domani mi laureo, per cui è arrivata l'ora di condividere la mia [tesi](https://github.com/seggiani-luca/block-fat16-thesis).
Il lavoro che ho fatto è stato più o meno anticipato da [questo post](/blog/2026-07-04-come-essere-pigro-mi-ha-insegnato-l-allocazione-di-memoria.html) sugli allocatori di memoria.
Oggi, a lavoro svolto, finito, terminato, volevo prendermi un secondo per discutere ciò che ho fatto senza rompermi le scatole col linguaggio formale e le buone maniere.

## Cosa

Ormai tutto il discorsetto me lo sono imparato a memoria. L'obiettivo della tesi era:
1. Prendere un emulatore preesistente (che sarebbe il mio emulatore [micro-sim](https://seggiani-luca.github.io/progetti/micro-sim.html) per un sistema RISC-V);
2. Estenderlo con l'emulazione di un dispositivo ATA (o per essere scorbutici, *Parallel* ATA o simpaticamente PATA, per distinguerlo dal "moderno" SATA seriale);
3. Implementarci sopra il filesystem FAT16 come lo si trovava nei DOS Compaq o Microsoft (ci sono in verità alcune differenze, nella tesi ne parlo ma non è particolarmente interessante);
4. Dimostrare il tutto attraverso una semplice shell (shell DOS, bash, quello che vi pare, la mia implementazione è talmente rudimentale che non si distingue uno standard in particolare).

Insomma, avevo già il mio emulatore e volevo implementarci sopra la componente che al momento mi sembrava fosse più necessario avere: il disco.
Per seguire l'ispirazione all'IBM PC AT che ho adottato finora l'ho fatto ATA, che è semplice e con cui avevo un po' di abitudine.

L'unico problema (che fortunatamente nessuno ha sollevato) è che l'emulatore non supporta ancora le interruzioni e quindi si fa tutto in busy wait.
Se fra disco e interruzioni il primo è effettivamente più importante, poi, è una domanda che lascio agli ingegneri degli anni '60.
Io probabilmente devo sbrigarmi ad implementare tutt'e due (e con questa tesi, finalmente, il primo l'ho gia fatto).

## Come

La tesi è divisa in 3 capitoli.

### Capitolo 1

Il primo è palloso in quanto semplicemente descrive la struttura dell'emulatore.
Non l'ho scritto io, l'ha scritto il mio ego perché mi girava che tutto l'emulatore l'avevo implementato e non potevo parlarne nemmeno un po'.
Comunque una descrizione migliore è più sintetica si trova nell'[articolo](https://seggiani-luca.github.io/progetti/micro-sim.html), nella [repo](https://github.com/seggiani-luca/micro-sim), nell'allegata documentazione (a proposito, mi sono ricordato di caricare la documentazione!) o forse direttamente nel codice.

### Capitolo 2

Questo capitolo è dove prendo lo standard dell'interfaccia ATA e lo metto effettivamente in pratica per la gestione del disco del sistema.

Internamente il "disco" è quasi ironicamente semplice: è un array `byte[]` di 16 MiB.
Che sembra quasi deludente finché non ti rendi conto che un'array è quello che praticamente ogni dispositivo di archiviazione diventa quando astrai via tutte le complicazioni hardware.
Almeno, finché non ti confondi con roba ad accesso sequenziale (che schifo i supporti ottici), o peggio, ad accesso indicizzato (che ad oggi non ho capito se è una cosa reale o un'allucinazione di chi scrive i libri di sistemi). 

L'unica parte noiosa è la persistenza.
Senza di questa ogni riavvio ripulisce tutto il filesystem, che diventa fastidioso molto velocemente.
L'emulatore carica quindi un file `.img` prima di avviare ogni simulazione, e ci ricopia l'array quando una simulazione chiude.
Congratulazioni, hai appena reinventato le immagini di disco.
Si scopre che sono solo blob di byte! Chi l'avrebbe mai detto...

La decisione progettuale principale (che è un alias di "il punto dove mi sono arreso e ho fatto il vigliacco") è che non mi preoccupo di simulare le temporizzazioni.
Non c'è latenza di seek, delay rotazionale e tutte quelle cose.
Tu dai il comando al disco e il disco sa subito cosa vuoi e dove si trova.
Al prossimo ciclo di clock la porta di stato è alta e tu inizi a leggere o scrivere, a seconda di cosa hai chiesto.

```java
/**
 * Gets block device ports.
 *
 * @param index index of port
 * @return value port should return
 */
@Override
public int getPort(int index) {
  // wait for error to be removed
  if (error && index != 1) {
    return 0;
  }

  switch (index) {
    case 0 -> {
      // data port
      if (currentOp != null && currentOp.type == DiskOpType.READ) {
        int byteIndex = getIndex();
        int data = (storage[byteIndex + 1] & 0xff) << 8;
        data |= (storage[byteIndex] & 0xff);

        return data;
      }
    }
    case 1 -> {
      // error port
      int lastError = error ? 1 : 0;
      error = false;
      return lastError;
    }
    case 4 -> {
      // status port
      return ((currentOp != null) ? DRQ_BIT : 0)
              | (error ? ERR_BIT : 0);
    }
  }

  return 0;
}

/**
 * Sets block device ports.
 *
 * @param index index of port
 * @param data value to give port
 */
@Override
public void setPort(int index, int data) {
  // wait for error to be removed
  if (error) {
    return;
  }

  switch (index) {
    case 0 -> {
      // data port
      if (currentOp != null && currentOp.type == DiskOpType.WRITE) {
        int byteIndex = getIndex();
        storage[byteIndex] = (byte) data;
        storage[byteIndex + 1] = (byte) (data >>> 8);
      }
    }
    case 2 -> {
      // address port
      nextOp.blockAddress = data;
    }
    case 3 -> {
      // block counter port
      nextOp.blockNumber = data & 0xff;
      if (data == 0) {
        nextOp.blockNumber = 256;
      }
    }
    case 4 -> {
      // command port, parse given command
      switch (data) {
        case READ_COMMAND -> {
          nextOp.type = DiskOpType.READ;
        }
        case WRITE_COMMAND -> {
          nextOp.type = DiskOpType.WRITE;
        }
        default -> {
          // ignore unknown commands
          return;
        }
      }

      // start operation if free
      beginOperation();
    }
  }
}
```

Codice di accesso al disco

Per fare ciò mi è bastato estendere la classe `IoDevice` (consultare la documentazione se questo suona strano).
Avrei già la classe `ThreadedIoDevice`, che col metodo `smartSpin()` permette di attendere tempo di simulazione in millisecondi.
Lascio a qualcun'altro il piacere di implementare la latenza rotazionale, l'algoritmo SCAN, la logica di interfaccia completa (col bit BUSY e via dicendo) e tutto il resto.
Io nella tesi ho cercato di far sembrare questa decisione una semplificazione deliberata, e non un'omissione (oh, mi toglieva tempo per fare il filesystem).

Montare il disco è altrettanto semplice, visto che le classi per i dispositivi me le ero fatte tempo fa.
Si sceglie un indirizzo base MMIO (`0x00070000`, subito dopo il "dispositivo di rete", che un giorno devo riprendere e approfondire), si mette tutto sul bus, ci si ricorda di aggiornare con `step()` e via.

La cosa che a me sembra particolarmente ganza è che dal punto di vista della CPU c'è solo un altro dispositivo nello spazio di memoria, che risponde a certi indirizzi.

In sostanza l'implementazione è piacevolmente noiosa in tutti i modi possibili.
Niente nel codice sta facendo roba da filesystem.
Si fa solo finta di essere un dispositivo a blocchi: esponendo i registri (porte ! anche se sono in memoria) giusti, validando i comandi, spostando byte in giro, ricordando lo stato e lamentandosi quando qualcuno fa qualcosa di stupido.

Una volta che tutto questo è in posizione, tutto ciò che sta sopra (FAT16, la shell, ecc...) può far finta di parlare con un disco reale anziché con un array Java da 16 MiB. 
Tutto questo anche se alla fine dei salmi sotto c'è comunque un array Java da 16 MiB.
I just think that's neat...

### Capitolo 3

Nel capitolo 3 si mette in piedi il filesystem vero e proprio.
Qui si capisce un po' tutta la filosofia:
- Prima si crea qualcosa che finge di essere un dispositivo a blocchi;
- Il processore simulato, che è scemo, non si rende conto che questo qualcosa sta facendo finta: e quindi in un ambiente completamente simulato noi programmatori abbiamo la fortuna di implementare un filesystem, proprio come lo faremmo su una macchina vera.

A questo punto non mi ricordo se da qualche parte ho già citato questa [ottima risorsa](https://8dcc.github.io/programming/understanding-fat.html) sul FAT in generale, per cui la riporto.
Il cuore di tutta la implementazione (cioè gli struct, perche scrivere le funzioni richiede 10 minuti di stesura codice e 3 settimane di debugging) l'ho scritto in una notte con questo articolo aperto da una parte.
Giuro che è fatto davvero così bene.

### Le basi

In ogni caso provero a riassumere (in maniera molto meno accurata) quello che ho effettivamente fatto.

Tutti sanno che il dispositivo a blocchi concede l'accesso a (duh) blocchi.
Poi di blocchi ce ne sono tanti tipi, e allora rubiamo un po' di nomenclatura dall'ATA e li chiamiamo *settori* (da 512 byte).

FAT16 è speciale, e quindi prende più di questi settori insieme (1, 2 o 4) e ci forma un *cluster* (in verità ha ottimi motivi per farlo, e lo vedremo più avanti).

Quindi, si possono concatenare più di questi cluster in liste per contenere buffer di vario tipo (e di varie dimensioni): file e directory.
In un isolato lampo di genio, la Microsoft ha deciso per una volta di fare le cose centralizzate e non distribuite (non temete, però, le directory sono comunque distribuite, per cui niente hard link!).
C'è quindi una tabella centrale che contiene i puntatori di queste liste.
Come si chiamerà mai questa tabella?
Come suona File Allocation Table? Ecco, hai reinventato la tabella FAT e hai capito come mai il filesystem si chiama così.

### La questione delle (fastidiose) directory

Il primo problema sono le directory, e FAT16 decide subito di essere una discreta rottura di scatole (discreta rottura di scatole non ce lo puoi scrivere nella tesi, però ho scritto "fastidioso" che nella mia testa in scala linguaggio formale è un espressione molto forte).

Una directory, infatti, non è semplicemente un blocco.
Può estendersi su più cluster concatenati attraverso la FAT (che ci torna), tranne la directory di root (che ci torna meno!).
Questo perché DOS, nella sua infinita saggezza, ha deciso che la root dovesse essere un bimbo speciale: dimensione fissa e comportamento diverso da tutte le altre directory, dimensione in settori anziché cluster, e non ridimensionaile!
Quindi la prima cosa che il codice deve fare è chiedersi "sono nella root?", e non si riesce mai a fare le cose pulite. Vabbé.

### L'iteratore

All'inizio l'API voleva un bell'iteratore con `next()` e `prev()`, e magari perché no, `up()` e `down()` per l'attraversamento di directory.
Poi è arrivata la realtà, cioè che mi mancavano 2 settimane e avevo a muovermi.

Il discorso dell'`up()` e `down()` l'ho abbandonato subito perché era anche poco elegante.
Ho quindi costretto l'utente a portarsi dietro un `uint16_t` con l'indice del primo cluster della directory corrente.
Vuoi cambiare directory? Cambia l'indice.
Questo è semplice perchè ogni volta che si crea una directory si creano anche le due entrate magiche che ogni utente Unix usa ogni giorno senza pensarci:

```
.
..
```

dove.
- `.` punta alla directory stessa;
- `..` punta alla directory padre.

Fine.
È davvero così che funziona "torna indietro di una directory". Non esiste una struttura ad albero segreta da qualche altra parte.
Ogni directory porta semplicemente con sé un bigliettino con scritto "questa sono io" e "mio padre sta laggiù".
Se vuoi spostarti, metti nel puntatore a directory corrente il nome del padre o del figlio (o dello spirito santo), fine.

Quindi ho semplificato anche la `prev()`.
In FAT16 il cluster precedente semplicemente non esiste.
La catena è unidirezionale.
Vuoi tornare indietro?
Certo: scorri tutta la FAT finché non trovi chi punta a te.
Oppure mantieni un indice inverso per conto tuo.
Entrambe idee orribili.
Così `prev()` viene silenziosamente accompagnata all'uscita e l'API viene ripensata in modo da non averne mai bisogno.
È probabilmente il primo momento in cui è l'implementazione ad adattarsi al filesystem, invece di cercare di costringere FAT16 dentro un'astrazione più elegante.
Così si scrive meno codice (buono), ci si costringe a scrivere codice che aderisce alla realtà (buono), e si fanno meno voli pindarici (buono?).

L'iteratore, nel frattempo, si trasforma lentamente in un oggetto sorprendentemente pesante
Deve ricordarsi se sta attraversando la strana directory di root, dove si trova, mantenere in memoria una copia dell'intero cluster corrente perché rileggerlo dal "disco" a ogni iterazione sarebbe stupido, sapere quale entrata di directory sta visitando e, alla fine, avere pure un booleano che dice semplicemente "ok, qui abbiamo finito".
È una di quelle strutture che nascono con tre campi e qualche ora dopo contengono quattro kilobyte di cache perché... prestazioni.

La cache, tra l'altro, è una piccola ottimizzazione piuttosto carina.
Certo, il disco dell'emulatore è solo RAM, ma fingere di rileggere il cluster a ogni `next()` sarebbe comunque sciocco.
Così l'iteratore si porta dietro una copia del blocco corrente e la riscrive sul disco solo quando qualcuno modifica davvero qualcosa (e quindi chiama la `sync()`).
In pratica è una minuscola cache write-back nascosta dentro un iteratore di directory: contemporaneamente eccessiva e assolutamente sensata.

```c
/**
 * Iterator for directory traversal.
 */
struct dir_iter {
private:
    /**
     * Is this iterator on the rootdir?
     */
    bool root;

    /**
     * Block address of iterator, can be sector (for rootdir) or 
     * cluster (for normal dirs).
     */
    union {
        uint32_t sector;
        uint16_t cluster;
    } block;
    
    /**
     * Current (cached) block. 
     */
    fat::dir_ent cache[MAX_CLUSTER_SIZE / sizeof(fat::dir_ent)];

    /**
     * Entries in current block.
     */
    int entries;

    /**
     * Entry in the current block.
     */
    int entry;

    /**
     * Did the iterator reach end?
     */
    bool valid;
public:
    /**
     * Returns an iterator for preorder traversal of directory.
     *
     * @param dir directory to iterate over 
     */
    dir_iter(uint16_t dir);

    /**
     * Returns the current entry.
     */
    fat::dir_ent& get_entry();

    /**
     * Syncs cached block to disk.
     */
    void sync();

    /**
     * Moves iterator to next directory entry.
     *
     * @param alloc should a new cluster be allocated if at the end of
     *        the directory?
     * @return did iterator reach end?
     */
    bool next(bool alloc = false);
};

bool dir_iter::next(bool alloc) {
    if(!valid) return false;

    // advance entry
    entry++;
    if(entry != entries) return true;
    // have to move to next block

    // rootdir
    if(root) {
        // get next sector
        block.sector++;

        // check if end reached
        uint32_t end = fat::get_rootdir(tab::cur_vbr) +
                       fat::get_rootdir_len(tab::cur_vbr);
        if(block.sector >= end) {
            entry--;
            valid = false;
            return false;
        }
        
        // cache this sector
        sec::read(block.sector, cache);

    // normal directory
    } else {
        // get next cluster 
        uint16_t next = tab::lookup(block.cluster);
        int cluster_len = fat::get_cluster_len(tab::cur_vbr);

        // check if end reached
        if(fat::is_end_of_chain(next)) {
            if(alloc) {
                // need to allocate more space for directory
                uint16_t new_cluster = tab::chain(cluster_len);
                clu::zero(new_cluster);

                // append to fat table
                tab::set(block.cluster, new_cluster);
                block.cluster = new_cluster;
            } else {
                entry--;
                valid = false;
                return false;
            }
        } else {
            // move to next cluster
            block.cluster = next;
        }
        
        // cache this cluster
        int cluster_bts = fat::get_cluster_bts(tab::cur_vbr);
        clu::read(block.cluster, cache, cluster_bts);
    }

    // reset entry
    entry = 0;
    return true;
}
```

Codice di implementazione dell'iteratore

Per spiegare al meglio l'iteratore, ho riportato il codice di avanzamento del suddetto:
Per la maggior parte del tempo basta:
- Caricare un blocco (settore per la directory di root, cluster per le altre) dal disco, che è fatto da altre funzioni di libreria;
- Incrementare l'indice di entrata nel blocco, che è facile.

Il problema è che prima o poi si arriva alla fine del blocco corrente.
A quel punto bisogna chiedersi:
- Sono nella directory di root? Se sì, passa al settore successivo.
- Altrimenti segui la catena nella FAT. Ma qui aspetta... la catena è finita? Se sì... mi è permesso allocare un altro cluster? Se sì, allocane uno, concatenalo, azzeralo, ricarica la cache e continua. Altrimenti fermati con dignità.

### Altre cose

Tutto il resto è abbastanza standard, nel senso:
- La gestione della FAT è solo bookkeeping e gestione delle liste, che non interessa a nessuno;
- Quando hai implementato l'iteratore, tutte le operazioni sul filesystem diventano banali (creare directory, file, fare listati, ecc... basta sempre fare un iteratore e scorrerlo).

La parte migliore arriva alla fine.
Monti l'immagine generata sotto Linux usando `vfat`.

Si monta.

Nessun parser personalizzato. Nessun trucco. Linux guarda quel file e dice semplicemente: "Sì, questo è FAT16.".
Probabilmente è la validazione più forte di tutto il progetto.
L'emulatore non sta più fingendo di implementare FAT16: ha prodotto qualcosa che un sistema operativo vero accetta senza fare una piega.

Cosa ancorà più ganza: puoi modificare quell'immagine dal tuo sistema operativo, salvarla, rimetterla nel sistema simulato, e (sperabilmente) non si rompe nulla.
Potresti avere dei problemi se usi dei nomi che sono troppo lunghi o contengono caratteri minuscoli, ma questo perché il driver del tuo sistema operativo sicuramente è più intelligente del mio e usa l'estensione di FAT16 per i nomi di file lunghi (che nel mio sistema compaiono come file corrotti).

Non nego che non ho fiducia che tutte le funzionalità che la versione di FAT16 che avrei dovuto coprire sono implementate.
Però il fatto che tutto il ciclo di montaggio -> modifica -> salvataggio non rompa tutto mi rende già molto speranzoso.
Ulteriore debugging si fa solo usando il sistema (e io mi sono messo a scriverci e salvare la documentazione proprio per questo).

![dimostrazione](/pics/blog/block_thesis_demo.png)

Egli vive!

## Perché

Il motivo della tesi, di `micro-sim`, e di tutto questo discorso in primo luogo non era quello di vantarmi o far vedere un'implementazione ganza o altre cose del genere.

Io ho scritto `micro-sim` perché volevo vedere come funziona un computer da *dentro*, farne una mia stupida approssimazione e vederla fallire, funzionare, quindi fallire di nuovo in un ciclo che prima o poi mi ha insegnato qualcosa.
Con questo progetto, mi sono convinto che con questo strumento si possono imparare anche tante altre cose (come funziona il filesystem, altri dispositivi, magari un giorno l'interfaccia di rete? ecc...).

Per questo motivo scrivo questi articolini e per questo motivo pubblico tutto il codice, documentato, gratuitamente e senza licenza in Internet.
Spero che se qualcuno si imbatterà in questo progetto, e avrà voglia di approfondire qualche concetto nel mondo dell'ingegneria informatica, magari potrà farlo implementando qualche altra nuova funzionalità per il sistema.

Non prometto codice facile da capire o anche solo scritto bene.
Prometto però la possibilità di imparare qualcosa tutti insieme, e di vedere un progetto crescere, che forse è gia qualcosa.
