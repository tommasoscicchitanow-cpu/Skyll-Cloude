# Guida all'attivazione della protezione

Questa guida spiega come accendere la cifratura a due fattori quando il progetto su Carlo Acutis arriverà alla pubblicazione. **Fino ad allora il sistema resta spento** e funziona solo in modalità prova, con documenti e frasi inventati.

## Come funziona, in breve

Per aprire un file protetto servono due cose insieme:

1. **La tua impronta digitale.** L'impronta non viene mai copiata né salvata: il dispositivo custodisce un segreto casuale in un'area protetta (Secure Enclave, TPM, keystore) e lo libera solo quando il sensore ti riconosce.
2. **La tua frase segreta**, che conosci solo tu a memoria. Da essa si ricava una chiave con Argon2id, un algoritmo pensato apposta per rendere lentissimi i tentativi di indovinarla.

Le due chiavi vengono unite (HKDF-SHA256) e il file è cifrato con AES-256-GCM. Se manca una delle due, o se il file è stato manomesso anche di un solo byte, l'apertura fallisce. Il messaggio d'errore non dice quale dei due fattori era sbagliato, per non aiutare chi prova a indovinare.

## Cose da sapere prima di cominciare

* **La frase non si recupera.** Nessuno, nemmeno Claude, la conosce o la salva. Se la dimentichi, i file sono persi per sempre. Valuta di scriverla su carta e chiuderla in un luogo sicuro (cassaforte, busta sigillata presso persona di fiducia).
* **Anche il dispositivo è indispensabile.** Se perdi o cambi il computer o il telefono su cui hai registrato l'impronta, i file non si aprono più. Per questo il passo 4 prevede una seconda chiave di riserva.
* **Il repository Skyll-Cloude è pubblico.** Va benissimo per il codice, che non contiene segreti, ma **non devi mai caricarci** il materiale riservato, né in chiaro né cifrato, né la frase segreta.
* **Il materiale non lascia il tuo PC.** Il programma non usa la rete in nessun momento (c'è una prova automatica che lo verifica bloccando tutte le connessioni). I file cifrati e quelli in chiaro restano sul tuo disco.
* **Scegli una frase lunga**: almeno 5 o 6 parole che non abbiano un legame ovvio tra loro e con il progetto (niente nomi, date, citazioni note). Il programma rifiuta frasi sotto i 20 caratteri.

## Prova oggi (sistema spento)

Serve Python 3.10 o successivo.

```bash
cd protezione-acutis
pip install -r requirements.txt
python -m protezione_acutis stato     # deve dire: DISATTIVATO
python -m protezione_acutis prova     # dimostrazione con dati inventati
python -m pytest -q                   # tutte le prove automatiche
```

Le prove verificano: cifratura e decifratura, rifiuto con frase errata, rifiuto senza impronta o con il sensore spento, rifiuto da un altro dispositivo anche con la frase giusta, rifiuto di file alterati o troncati, e che l'interruttore resti spento.

Da spento il programma si rifiuta di toccare file che non stiano in una cartella temporanea, e rifiuta qualunque sensore biometrico reale: non puoi cifrare per sbaglio il materiale vero.

## Attivazione (al momento della pubblicazione)

### Passo 1. Prepara il materiale

Fai una copia di sicurezza completa del materiale riservato su un supporto scollegato da internet (per esempio una chiavetta USB cifrata) e tienila al sicuro finché non avrai verificato che tutto si apre correttamente.

### Passo 2. Scegli la frase segreta

Scegline una nuova, da solo, lontano da schermi e persone. Non scriverla in chat, email, note del telefono o documenti digitali.

### Passo 3. Collega il sensore biometrico del tuo dispositivo

Il tuo PC è Windows, quindi si usa **Windows Hello** (`protezione_acutis/windows_hello.py`): una chiave custodita nel chip TPM del PC, che firma solo dopo il riconoscimento dell'impronta. Su un altro PC i file non si aprono.

Serve un lettore d'impronte (integrato o USB) configurato in Impostazioni, Account, Opzioni di accesso. Poi:

```bash
pip install -r requirements-windows.txt
python -m protezione_acutis prova-hello
```

La prova usa il sensore vero ma solo un testo inventato tenuto in memoria: non legge né scrive file, e alla fine cancella la chiave di prova.

#### In alternativa: lo smartphone come lettore d'impronte

Se il PC non ha un lettore d'impronte, o preferisci usare il telefono, c'è `protezione_acutis/passkey.py`. I file **restano solo sul PC**: il telefono fa solo da sensore, collegato via Bluetooth.

1. Attiva il Bluetooth sul PC e sul telefono.
2. Lancia `python -m protezione_acutis prova-passkey`.
3. Nella finestra di Windows scegli "iPhone, iPad o dispositivo Android" e inquadra il codice QR con la fotocamera del telefono.
4. Conferma con l'impronta sul telefono. Le volte successive il telefono viene riconosciuto da solo.

Servono Windows 11 aggiornato e un telefono Android 9 o successivo (con Gestore password di Google) oppure un iPhone con iOS 18 o successivo. Se il telefono o Windows non supportano la funzione necessaria (si chiama PRF), il programma lo dice e rifiuta di proteggere i file, invece di proteggerli male.

Questo stesso metodo funziona anche con una chiave di sicurezza FIDO2 con impronta, utile come chiave di riserva (passo 4). Come per Windows Hello, se il telefono si sblocca anche con un PIN o una sequenza, chi la conosce può sostituire l'impronta: usa un codice di sblocco lungo. La frase resta comunque obbligatoria.

#### Un limite di Windows Hello

Windows Hello accetta anche il suo PIN al posto dell'impronta, e il programma non può impedirlo. Scegli quindi un PIN Hello lungo e diverso da tutti gli altri. La frase segreta resta comunque obbligatoria in ogni caso.

### Passo 4. Prepara una chiave di riserva

Registra un secondo fattore biometrico (per esempio una seconda chiave FIDO2 con impronta) da custodire in un luogo diverso. Senza riserva, un guasto al dispositivo rende i file irrecuperabili. Questa funzione verrà aggiunta insieme al passo 3.

### Passo 5. Accendi l'interruttore

Sul tuo computer, nella cartella `protezione-acutis`, crea un file chiamato `configurazione.locale.json` con questo contenuto:

```json
{ "attivo": true }
```

Solo il valore `true` senza virgolette accende il sistema. Poi verifica:

```bash
python -m protezione_acutis stato     # deve dire: ATTIVO
```

Questo file resta **solo sul tuo computer**: è escluso da git e non finisce mai nel repository pubblico. Il file `configurazione.json` del repository deve restare a `false` (c'è una prova automatica che lo controlla). Per spegnere di nuovo il sistema basta cancellare `configurazione.locale.json`.

### Passo 6. Cifra e verifica

1. Cifra **un solo** file di poco conto e riaprilo con impronta e frase.
2. Prova ad aprirlo con una frase sbagliata e senza impronta: deve rifiutare.
3. Solo allora cifra il resto del materiale.
4. Riapri a campione alcuni file, poi elimina gli originali in chiaro.

Nota: su dischi SSD la cancellazione di un file non garantisce che i dati spariscano davvero. Per questo è meglio tenere il materiale riservato fin dall'inizio su un disco già cifrato (FileVault su Mac, BitLocker su Windows) e usare questa protezione come secondo livello.

### Passo 7. Distruggi la copia di sicurezza in chiaro

Quando hai verificato che tutto si apre, la copia del passo 1 non serve più: distruggila o tienila tu in un luogo fisicamente sicuro.

## Archivio cifrato interno (consigliato, al posto di VeraCrypt)

Il programma ha un suo archivio cifrato: non serve installare VeraCrypt né altri programmi. L'archivio è una cartella, per esempio sulla partizione da 500 GB del disco E:, che dall'esterno contiene solo file con nomi casuali e contenuto illeggibile. **Anche i nomi dei file, le dimensioni e le date sono cifrati.**

Per aprirlo servono sempre la tua frase, che scrivi nella finestra del programma sul PC (non viene mostrata né salvata), e l'impronta.

**Perché algoritmi standard e non uno inventato.** Il codice dell'archivio è nostro, ma la matematica della cifratura è quella pubblica e studiata da anni (AES-256-GCM, Argon2id, HKDF). Un algoritmo inedito non è mai stato messo alla prova dagli esperti e quasi certamente avrebbe punti deboli che oggi nessuno vede: per proteggere le fonti serve il contrario.

**Differenze rispetto a VeraCrypt.** Non compare un disco con una lettera: i file si aggiungono, si elencano e si estraggono con i comandi qui sotto. Quando estrai un file per lavorarci, quella copia è in chiaro: tienila il meno possibile e poi cancellala. In cambio non serve installare nulla, e ogni file è protetto anche contro le modifiche (un solo byte alterato viene rilevato).

### Comandi

Sul tuo PC, nella cartella del programma, al posto di `python` usa `.venv\Scripts\python`. Aggiungi `--fattore hello` per usare Windows Hello del PC, oppure lascialo via per usare il telefono.

```bash
python -m protezione_acutis archivio-crea      --fattore hello CARTELLA
python -m protezione_acutis archivio-aggiungi  --fattore hello CARTELLA file1 file2 ...
python -m protezione_acutis archivio-elenca    --fattore hello CARTELLA
python -m protezione_acutis archivio-estrai    --fattore hello CARTELLA NOME DESTINAZIONE
python -m protezione_acutis archivio-rimuovi   --fattore hello CARTELLA NOME
```

Da spento l'archivio può stare solo nella cartella temporanea. Per la prova sulla partizione vera si aggiunge `--prova`, **solo con una frase di prova e file inventati**. Dopo l'aggiunta i file originali non vengono cancellati: fallo tu, dopo aver verificato che si estraggono correttamente.

### Passare al materiale vero

Fallo solo dopo aver completato la prova con file inventati. In ordine:

1. **Accendi il sistema** creando `configurazione.locale.json` con `{ "attivo": true }` (passo 5 della guida). Senza `--prova`, da qui in poi si usano la chiave Windows Hello definitiva e i parametri di sicurezza pieni.
2. **Crea l'archivio definitivo**, con la frase vera:
   `archivio-crea --fattore hello P:\archivio`
3. **Crea subito la chiave di recupero** e scrivila a mano su carta:
   `archivio-chiave-recupero --fattore hello P:\archivio`
   Insieme alla frase sostituisce l'impronta se Windows Hello o il PC si rompono. Non fotografarla e non salvarla in nessun file. Conservala lontano dal PC.
4. **Copia tutta la cartella** dalla chiavetta (gli originali non vengono toccati):
   `archivio-importa --fattore hello P:\archivio D:\CARTELLA_DEL_PROGETTO`
   Se si interrompe, rilancia lo stesso comando: riprende senza ricopiare.
5. **Verifica byte per byte** contro la chiavetta. Stampa solo numeri, mai nomi di file:
   `archivio-verifica --fattore hello P:\archivio D:\CARTELLA_DEL_PROGETTO`
   Deve dire `ESITO: OK`.
6. **Scollega la chiavetta** e controlla l'archivio da solo:
   `archivio-integrita --fattore hello P:\archivio`
   Deve dire `danneggiati: 0`.
7. **Prova il recupero** prima di formattare la chiavetta: `archivio-recupera --fattore hello P:\archivio` chiede frase e chiave di recupero e ricollega l'impronta. Se funziona, la chiave su carta è giusta.
8. Solo allora, se vuoi, formatta la chiavetta. È una scelta tua e non si può annullare.

Per lavorare su un file: `archivio-estrai` (uno) o `archivio-estrai-tutto` (tutti); le copie estratte sono in chiaro, cancellale appena finito.

## Lavoro quotidiano: l'app "Cassaforte"

Una finestra unica per tutti i progetti protetti, non solo Acutis. Ogni
progetto è un archivio cifrato con la sua frase e la tua impronta.

**Aprire l'app.** Doppio clic sull'icona "Cassaforte" (lucchetto dorato) sul
Desktop. Per averla sulla barra delle applicazioni: clic destro sull'icona
del Desktop, "Mostra altre opzioni", poi "Aggiungi alla barra delle
applicazioni" (dallo stesso menu c'è anche "Aggiungi a Start"). Windows non
permette ai programmi di farlo da soli. Se l'icona manca, si ricrea con
`python -m protezione_acutis crea-collegamenti`.

**Lavorare su un progetto.**

1. Scegli il progetto a sinistra, scrivi la frase segreta (vedi solo
   asterischi) e premi "Apri per lavorare". Poi appoggia il dito quando
   Windows Hello lo chiede.
2. Si apre la cartella di lavoro con tutti i file. Lavora normalmente: puoi
   modificare, aggiungere e cancellare file e sottocartelle.
3. Quando hai finito, chiudi Word e gli altri programmi, scrivi la frase e
   premi "Chiudi e proteggi", poi l'impronta. L'app riporta nell'archivio i
   file nuovi e modificati, controlla ogni file con SHA-256 rileggendo la
   copia cifrata, e solo se tutto torna sovrascrive con dati casuali e
   cancella la cartella di lavoro.

Lo stato è sempre in vista: verde "Protetto", arancione "Aperto per
lavorare". Finché l'app è in funzione (anche ridotta a icona) lo
stato si vede anche fuori dalla finestra:

* tutto chiuso: piccolo lucchetto verde sull'angolo dell'icona nella barra
  delle applicazioni;
* almeno un progetto aperto: lucchetto rosso sull'icona, pulsante della barra
  che lampeggia di rosso, striscia rossa "CASSAFORTE APERTA, rischio fuga di
  notizie" sempre in primo piano appena sopra la barra (un clic riporta alla
  finestra), fascia rossa nella finestra e, ogni 30 minuti, un promemoria in
  primo piano.

Costa pochissimo al PC: un controllo ogni 3 secondi sull'esistenza delle
cartelle di lavoro (senza leggere file) e un cambio di colore al secondo
solo mentre è aperta. Ad app chiusa Windows mostra l'icona fissa: per questo,
se chiudi la finestra con un progetto aperto, l'app ti avvisa. Se chiudi la finestra con un progetto aperto, l'app te lo ricorda.
Un secondo "Apri" sullo stesso progetto è bloccato finché non lo chiudi.

**File cancellati.** Se nella cartella di lavoro hai cancellato dei file,
l'app ti chiede se toglierli anche dall'archivio. Nel dubbio rispondi No:
restano al sicuro nell'archivio.

**Un file è ancora aperto in un programma.** Il lavoro è già salvato e
verificato; chiudi il programma e premi di nuovo "Chiudi e proteggi" per
finire la pulizia.

**Dove sta la cartella di lavoro.** Sul disco esterno, accanto all'archivio
(per Acutis `P:\lavoro-aperto`, per i progetti nuovi
`P:\cassaforte\<nome>\lavoro-aperto`), mai sul disco C:. Così la copia in
chiaro non finisce in OneDrive, nei backup di Windows o nei file recenti di
altri programmi; la sovrascrittura su un disco meccanico esterno è efficace
(su un SSD interno no); scollegando il disco non resta nulla sul PC.

**Due accortezze di Windows.** Word salva copie di ripristino automatico su
C: mentre lavori: in Word, File, Opzioni, Salvataggio, puoi togliere
"Salva informazioni di salvataggio automatico" per i documenti riservati. In
Sicurezza di Windows, Protezione da virus e minacce, Gestisci impostazioni,
conviene disattivare "Invio automatico di campioni", che può spedire file a
Microsoft per l'analisi.

**Nuovo progetto.** Premi "Nuovo progetto", scegli un nome che non riveli il
contenuto (l'elenco dei nomi sta in chiaro in `P:\cassaforte\progetti.json`),
una frase di almeno 20 caratteri e l'impronta. Poi "Apri per lavorare",
copia i file nella cartella che si apre e "Chiudi e proteggi". Gli originali
che avevi altrove cancellali tu solo dopo.

**Chiave di recupero.** Il pulsante "Chiave di recupero" ne crea una nuova e
la mostra sullo schermo da scrivere su carta. Attenzione: annulla quella
precedente dello stesso progetto. Per Acutis ne hai già una su carta: non
serve rifarla.

Le stesse operazioni esistono da riga di comando:
`python -m protezione_acutis lavora-apri --fattore hello P:\archivio-acutis`
e `lavora-chiudi`. Né l'app né i comandi mostrano o registrano nomi di file:
solo conteggi.

## Partizione o contenitore VeraCrypt con doppia chiave (alternativa)

Resta disponibile se in futuro preferirai un disco con lettera di unità; richiede di installare VeraCrypt.

Invece di cifrare i file uno per uno, puoi tenere tutto il materiale in un volume VeraCrypt (una partizione dedicata o un grande file contenitore). Il volume si apre solo con **due** elementi:

* **la tua frase**, che scrivi direttamente nella finestra di VeraCrypt;
* **un file chiave** che non è salvato da nessuna parte: il programma lo ricalcola ogni volta dal segreto che il telefono rilascia solo dopo la tua impronta, lo tiene su disco per pochi secondi e poi lo distrugge.

Chi ruba il PC trova solo un disco illeggibile e un piccolo file `chiave-veracrypt.json` che, senza il tuo telefono e il tuo dito, non serve a nulla.

### Prove (sistema spento)

Le prove si fanno solo su un **contenitore di prova** nella cartella temporanea, mai su una partizione o un disco veri: il programma rifiuta qualunque altro volume finché il sistema è spento.

1. Installa VeraCrypt dal sito ufficiale `veracrypt.io`.
2. `python -m protezione_acutis veracrypt-prepara` registra la passkey sul telefono.
3. Apri VeraCrypt, scegli "Crea volume", "Crea un file contenitore cifrato", e salvalo nella cartella temporanea (`%TEMP%\prova.hc`, 50 MB bastano).
4. Alla richiesta della password scrivi una **frase di prova** (non quella vera), spunta "Usa file chiave" e, in un'altra finestra, lancia `python -m protezione_acutis veracrypt-keyfile`: dopo l'impronta ti indica il file da selezionare. Finita la creazione premi Invio e il file chiave viene distrutto.
5. Prova ad aprirlo: `python -m protezione_acutis veracrypt-monta %TEMP%\prova.hc X`. Impronta sul telefono, poi VeraCrypt chiede la frase.
6. Verifica che senza impronta, o con la frase sbagliata, il volume non si apra.

### All'attivazione

Il volume definitivo sarà una **partizione dedicata sul disco esterno**: il disco viene diviso in due, una parte normale e una parte cifrata solo per il materiale riservato.

1. Fai un backup completo del disco esterno su un altro supporto.
2. In Gestione disco di Windows riduci la partizione esistente per liberare lo spazio, oppure crea una nuova partizione vuota senza lettera di unità.
3. In VeraCrypt scegli "Crea volume", poi "Crea un volume all'interno di una partizione/unità", seleziona **quella partizione** (controlla due volte numero di disco e dimensione) e ripeti i passi 4 e 6 delle prove con la frase vera.
4. Per aprirla: `python -m protezione_acutis veracrypt-monta \Device\HarddiskN\PartitionM X`, dove N e M sono i numeri che VeraCrypt mostra in "Seleziona dispositivo". Attenzione: Windows mostra una partizione VeraCrypt come "non formattata"; non accettare mai la proposta di formattarla.

## Claude e il materiale riservato

* **Claude non riceve mai la frase.** Quando un file va aperto, la frase la scrivi tu nella finestra del programma sul tuo PC, mai in chat. Allo stesso modo l'impronta la dai tu al sensore.
* **Claude può lavorare sul materiale solo dopo che tu lo hai sbloccato**, file per file.
* **Attenzione:** tutto ciò che Claude legge viene elaborato sui server di Anthropic, cioè esce dal PC. Per le parti che non devono uscire in nessun caso (nomi e dati delle fonti) hai due strade: non farle leggere a Claude, oppure toglierle prima con una copia anonimizzata. In alternativa si può usare un modello che gira interamente sul tuo PC, senza internet.

## Domande frequenti

**L'impronta viene inviata da qualche parte?** No. Resta nel sensore del dispositivo; il programma riceve solo un segreto che il dispositivo libera dopo averti riconosciuto.

**Qualcuno che ruba il computer può aprire i file?** Senza la frase no. E chi conosce la frase ma non ha il tuo dito e il tuo dispositivo nemmeno.

**Quanto è lento?** Ogni apertura impiega circa mezzo secondo per la derivazione della chiave: è voluto, rende impraticabili i tentativi a raffica.
