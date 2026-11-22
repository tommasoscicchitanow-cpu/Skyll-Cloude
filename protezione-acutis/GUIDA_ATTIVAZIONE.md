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

Il prototipo definisce un'interfaccia comune (`FattoreBiometrico` in `protezione_acutis/biometria.py`); manca solo il collegamento al sensore reale, che dipende dal dispositivo che userai. Le opzioni previste sono:

| Dispositivo | Soluzione consigliata |
|---|---|
| Mac con Touch ID | Segreto nel portachiavi protetto dalla Secure Enclave, con regola "solo impronta attuale" (se aggiungi una nuova impronta, il segreto si invalida). |
| PC Windows con lettore d'impronte | Windows Hello con chiave nel TPM. |
| Telefono Android | Android Keystore con autenticazione biometrica forte richiesta a ogni uso. |
| Qualsiasi computer | Chiave di sicurezza FIDO2 con lettore d'impronte (per esempio YubiKey Bio), usando l'estensione hmac-secret. È la soluzione più portabile. |

Quando sapremo quale dispositivo usi, Claude scriverà questo pezzo e le relative prove sul tuo dispositivo reale. Il collegamento deve avere `simulato = False`.

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

## Domande frequenti

**L'impronta viene inviata da qualche parte?** No. Resta nel sensore del dispositivo; il programma riceve solo un segreto che il dispositivo libera dopo averti riconosciuto.

**Qualcuno che ruba il computer può aprire i file?** Senza la frase no. E chi conosce la frase ma non ha il tuo dito e il tuo dispositivo nemmeno.

**Quanto è lento?** Ogni apertura impiega circa mezzo secondo per la derivazione della chiave: è voluto, rende impraticabili i tentativi a raffica.
