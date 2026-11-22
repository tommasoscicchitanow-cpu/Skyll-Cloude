# Prompt di continuazione — da incollare all'assistente/sviluppatore che riprende il progetto

> Consegna questo documento INSIEME alla cartella del progetto (o al clone del
> repository GitHub `tommasoscicchitanow-cpu/Skyll-Cloude`, branch
> `claude/zodiac-astronomy-app-5gz48v`, PR #3).

---

Sei incaricato di proseguire lo sviluppo di **«Cielo reale»** (nome
provvisorio): una web app statica che calcola le posizioni **reali** dei
corpi del sistema solare alla nascita e le confronta con le due convenzioni
astrologiche (tropicale e siderale) e con le costellazioni IAU. Leggi prima
`README.md` e `docs/METODO.md`, che documentano lo stato e ogni scelta di
calcolo.

## Tesi del prodotto (vincola copy e interfaccia)

Lo zodiaco a dodici settori uguali non è un errore da correggere: è una
convenzione consapevole che si è staccata dal cielo osservabile. L'app non
«smaschera» niente: mostra la distanza fra tre modi di segmentare la stessa
volta celeste e spiega da dove viene. Quindi: **niente oroscopi, niente
previsioni, niente profili di personalità, niente derisione dell'astrologia,
niente significati inventati per Ofiuco**. Se l'utente chiede «cosa
significa», la risposta onesta è che non esiste tradizione interpretativa.

## Stato attuale: fase 1 COMPLETATA e verificata

- `src/engine/` — motore astronomico puro (zero dipendenze da React):
  posizioni geocentriche apparenti (Sole→Plutone, nodi lunari medio e vero),
  Ascendente/MC vettoriali, case Whole Sign ed Equal, ayanamsa Lahiri e
  Fagan-Bradley, aspetti, ampiezze delle costellazioni calcolate a runtime.
- `tests/engine/` — **69 test, tutti verdi**, contro riferimenti esterni
  (120 campioni JPL Horizons con scarto max 0,36′; equinozi USNO entro
  0,005°; finestre di Ofiuco/Vergine/Scorpione 2026; Plutone fuori fascia
  zodiacale; fusi storici italiani).
- `scripts/chart-cli.ts` — carta testuale di prova (`npm run chart`).

**Prima di qualunque modifica esegui**: `npm install && npm test &&
npm run typecheck`. Devono restare verdi. Non marcare mai completato un
modulo con test rossi.

## Invarianti del motore da NON violare

1. Longitudini zodiacali sull'**eclittica vera della data**:
   `Ecliptic(GeoVector(body, t, true))`.
2. Costellazione IAU da RA/Dec **J2000** (`EquatorFromVector` →
   `Constellation`), MAI da coordinate «of date»: doppio conteggio della
   precessione (~0,4° nel 2026). C'è un test di regressione dedicato.
3. Costellazione determinata da RA **e** declinazione (mai dalla sola
   longitudine proiettata): Plutone ha latitudine ±17°.
4. Ampiezze delle costellazioni **calcolate**, mai costanti scritte a mano.
5. Aspetti identici nelle tre viste (dipendono dalle distanze angolari).
6. **Mai Swiss Ephemeris** (AGPL). Solo `astronomy-engine` (MIT).
7. Intervallo supportato dichiarato: 1700–2200; fuori intervallo si avvisa,
   non si degradano i numeri in silenzio.

## Decisioni già prese dal committente

- Licenza: **GPL-3.0** (LICENSE già nel repo).
- Lingua: **solo italiano**, ma architettura i18n pronta (file di stringhe
  separati chiave→testo, cartella `src/i18n/it/`, `en/` predisposta).
- **Nessuna monetizzazione, nessun account, nessun backend**: tutto
  client-side, nessun dato di nascita lascia il dispositivo.
- WordPress di destinazione: **tommasoautore.it** (self-hosted).
  Utente WP: `tommaso`. È stata generata una **Application Password**
  (il committente la fornisce a parte: NON è inclusa in questa cartella e
  non va mai committata). Installazione plugin: .zip caricabile dal
  pannello admin (Bacheca → Plugin → Aggiungi nuovo → Carica plugin).

## Fasi rimanenti (procedi per tappe, fermati a fine tappa per mostrare il risultato)

### Fase 2 — Interfaccia minima
React 18 + TypeScript + Vite (build statica, `base` relativo), Tailwind CSS,
Vitest. Form conversazionale (data, ora con opzione «ora ignota», luogo con
autocompletamento su GeoNames `cities5000` ridotto e compresso nel bundle,
CC BY 4.0 con attribuzione nei crediti; fallback lat/lon manuali). Ruota SVG
disegnata a mano (niente librerie di charting) con anello esterno che cambia
per vista; tooltip/pannello per corpo con longitudine in gradi/primi,
latitudine, costellazione IAU, segno tropicale, segno siderale, retrogrado.
Tabella di confronto 12 corpi × 3 viste con righe divergenti evidenziate.
Interruttore fra le viste con transizione animata; riga di sintesi tipo
«il tuo Sole: Bilancia (tropicale) · Vergine (siderale) · Vergine (IAU)».
Mostra sempre fuso applicato, ora UTC risultante e valore dell'ayanamsa.
Se l'ora è ignota: niente ASC/MC/case, mostra l'escursione della Luna
(il motore la fornisce già in `moonDailyRange`).

### Fase 3 — Pagine esplicative
«Perché divergono»: visualizzazione interattiva della precessione
(cursore sul ciclo di ~25.800 anni; evidente che ~II secolo a.C. le griglie
coincidevano e oggi divergono di ~24°). «Le costellazioni vere»: tabella
delle ampiezze da `solarConstellationSpans()` con barre proporzionali,
Ofiuco senza enfasi speciale. «Metodo e limiti»: riusa i contenuti di
`docs/METODO.md`. Registro divulgativo alto, ogni affermazione con fonte;
spiega che il tropicale resta ancorato agli equinozi per scelta deliberata,
non per ignoranza della precessione; segnala che la siderale indiana fa da
secoli ciò che molti credono una novità. Testi in file di stringhe separati.

### Fase 4 — Rifinitura
Responsive da 360px (ruota leggibile su telefono), WCAG AA, navigazione da
tastiera completa, tabella come alternativa testuale alla ruota,
`prefers-reduced-motion`, **zero chiamate di rete dopo il caricamento
(verificalo)**, condivisione via URL con parametri codificati (data, ora,
coordinate), palette scura di default + chiara. Estetica: atlante celeste /
Stellarium, niente cliché mistici, niente viola saturi, niente stelline.

### Fase 5 — Integrazione WordPress
Plugin PHP in `wp-plugin/`: shortcode `[cielo-reale]` che stampa il nodo
radice; accoda JS/CSS **solo** dove lo shortcode è presente; verifica
`post_password_required()` prima di stampare qualunque cosa; meta
`noindex, nofollow` ed esclusione dalla sitemap. Pagina WordPress con
visibilità nativa «Protetta da password», nessun plugin di membership.
Incapsulamento stili: prefisso Tailwind dedicato + preflight disattivato
(o Shadow DOM); React nel bundle, scope globale pulito; percorsi asset
relativi alla cartella del plugin. Script `npm run build:wp` che produce la
cartella/zip del plugin con versione che invalida la cache a ogni build.
Nel README: istruzioni passo passo (installazione, pagina, password,
verifica del gate in finestra anonima). Dichiara apertamente il limite:
la protezione nativa difende il contenuto della pagina, non i file della
build; l'endpoint PHP che gate-a gli asset è una variante da proporre al
committente indicandone il costo in complessità, e la scelta spetta a lui.

## Rigore

Se una scelta richiesta risulta astronomicamente scorretta, dillo e proponi
l'alternativa con la motivazione. La precisione non è una raffinatezza:
è l'intero prodotto.
