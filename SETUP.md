# Installazione di Celestia sul Xiaomi Watch 2

Guida passo-passo per compilare e installare il quadrante dal **tuo computer**
(unico dispositivo sulla stessa rete dell'orologio).

## Prerequisiti (una tantum)

1. **Android Studio** installato (Hedgehog 2023.1+) — porta con sé JDK 17 e Gradle.
2. **Android SDK Platform-Tools** (contiene `adb`). Si installa da Android Studio:
   *Settings → Languages & Frameworks → Android SDK → SDK Tools → Android SDK Platform-Tools*.
3. **Wear OS SDK API 33 e 34** (stessa schermata, tab *SDK Platforms*).
4. PC e orologio sulla **stessa rete Wi-Fi**.

## Attivare il Debug wireless sull'orologio

1. *Impostazioni → Informazioni → Versione software* → tocca 7 volte "Numero build"
   per sbloccare le **Opzioni sviluppatore**.
2. *Impostazioni → Opzioni sviluppatore → Debug wireless* → **ON**.
3. Tieni questa schermata aperta: mostra **IP:porta** di connessione
   (es. `192.168.178.32:45491`).

## Installazione automatica (consigliata)

Apri **PowerShell** nella cartella del progetto.

**La prima volta** (con accoppiamento):
```powershell
.\install.ps1 -Pair
```
Lo script:
- compila l'APK,
- ti chiede la **porta di abbinamento** e il **codice a 6 cifre**
  (sull'orologio: *Debug wireless → Abbina dispositivo con codice* — è una
  porta DIVERSA da quella di connessione),
- connette e installa.

**Le volte successive** (già accoppiato):
```powershell
.\install.ps1
```

Se l'IP/porta del tuo orologio sono diversi:
```powershell
.\install.ps1 -Pair -WatchIp 192.168.178.40 -ConnectPort 40000
```

## Installazione manuale (se preferisci i comandi singoli)

```powershell
# 1. Build
.\gradlew.bat :app:assembleDebug
#    -> app\build\outputs\apk\debug\app-debug.apk

# 2. Accoppiamento (solo la prima volta)
adb pair 192.168.178.32:<PORTA_ABBINAMENTO>   # poi inserisci il codice a 6 cifre

# 3. Connessione + installazione
adb connect 192.168.178.32:45491
adb install -r app\build\outputs\apk\debug\app-debug.apk
```

## Dopo l'installazione

1. Sull'orologio tieni premuto sul quadrante → **galleria quadranti** → **Celestia**.
2. Concedi i permessi quando richiesti:
   - **Sensori corporei (BODY_SENSORS)** → pulsazione cardiaca della nebulosa.
   - **Posizione** → orientamento della mappa siderale.

## Problemi comuni

| Sintomo | Causa / soluzione |
|---|---|
| `adb: command not found` | Platform-Tools non installati o non nel PATH. Installa da Android Studio. |
| `failed to connect` | Orologio e PC su reti diverse, oppure serve riaccoppiare: usa `-Pair`. |
| `more than one device` | Stacca altri dispositivi o usa `adb -s 192.168.178.32:45491 install ...`. |
| Build fallisce al primo sync | Apri prima il progetto in Android Studio e lascia completare il Gradle Sync. |
| Permessi negati a runtime | Concedili da *Impostazioni → App → Celestia → Autorizzazioni*. |
