# Protezione progetto Acutis (prototipo)

Prototipo di cifratura dei file riservati con **due fattori obbligatori**: impronta digitale e frase segreta.

**Stato: DISATTIVATO.** Funziona solo in modalità prova, su dati inventati. Per l'attivazione alla pubblicazione segui [GUIDA_ATTIVAZIONE.md](GUIDA_ATTIVAZIONE.md).

## Struttura

| File | Contenuto |
|---|---|
| `protezione_acutis/cripto.py` | Argon2id (frase), HKDF-SHA256 (unione dei fattori), AES-256-GCM (cifratura con intestazione autenticata) |
| `protezione_acutis/biometria.py` | Interfaccia `FattoreBiometrico` indipendente dalla piattaforma e `BiometriaSimulata` per le prove |
| `protezione_acutis/windows_hello.py` | Impronta tramite Windows Hello (chiave nel TPM del PC) |
| `protezione_acutis/passkey.py` | Impronta tramite smartphone o chiave FIDO2 (passkey con estensione PRF); i file restano sul PC |
| `protezione_acutis/archivio.py` | Archivio cifrato interno (consigliato): cartella con nomi casuali, indice cifrato, blocchi AES-256-GCM autenticati, chiave principale avvolta da frase + impronta |
| `protezione_acutis/lavoro.py` | "Apri per lavorare" e "Chiudi e proteggi": cartella di lavoro unica, reimportazione con verifica SHA-256, sovrascrittura e cancellazione |
| `protezione_acutis/app.py`, `progetti.py` | App grafica "Cassaforte" per tutti i progetti protetti |
| `protezione_acutis/icona.py`, `collegamenti.py` | Icona disegnata in Python e collegamenti su Desktop e menu Start |
| `protezione_acutis/veracrypt.py` | Volume VeraCrypt con frase + file chiave ricalcolato dall'impronta, mai salvato |
| `protezione_acutis/attivazione.py` | Interruttore: da spento lavora solo in cartelle temporanee e solo con biometria simulata |
| `protezione_acutis/__main__.py` | Riga di comando (`app`, `lavora-apri`, `lavora-chiudi`, `archivio-*`, `prova`, ...) |
| `configurazione.json` | Deve restare `"attivo": false`. L'accensione avviene con un file locale escluso da git (vedi guida, passo 5) |
| `tests/` | Prove automatiche |

## Prove

```bash
pip install -r requirements.txt
python -m pytest -q
python -m protezione_acutis prova
```

Le prove girano anche su GitHub (Linux, macOS, Windows) a ogni modifica di questa cartella.

## Formato del file cifrato

```
"PACUTIS1" | lunghezza intestazione (4 byte) | intestazione JSON | testo cifrato + tag GCM
```

L'intestazione contiene versione, parametri Argon2, sale, nonce e l'identificativo pubblico del segreto biometrico. Non contiene nulla di segreto ed è autenticata: modificarla fa fallire la decifratura.
