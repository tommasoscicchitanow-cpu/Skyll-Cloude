# Cielo reale (nome provvisorio)

Web app che calcola la posizione **reale** dei corpi del sistema solare
alla nascita e la confronta con le due convenzioni astrologiche in uso:
lo stesso identico cielo, tre griglie di lettura affiancate (tropicale,
siderale, costellazioni IAU — Ofiuco compreso, senza sensazionalismi).

Non produce oroscopi né interpretazioni. Mostra la distanza fra tre modi
di segmentare la stessa volta celeste e spiega da dove viene.

## Stato

**Fase 1 completata**: motore astronomico puro (`src/engine/`), 69 test
verdi contro riferimenti esterni (JPL Horizons, equinozi USNO), script di
prova da riga di comando. Le fasi successive (interfaccia React, pagine
esplicative, integrazione WordPress) sono descritte nel briefing.

## Comandi

```bash
npm install
npm test                 # suite completa (Vitest)
npm run typecheck        # controllo dei tipi
npm run chart            # carta di prova (Roma, 10/05/1990 16:30)
npm run chart -- --date 1971-03-15 --time 08:00 --lat 45.46 --lon 9.19
npm run chart -- --no-time --date 1971-03-15 --lat 45.46 --lon 9.19
npm run chart -- --spans 2026   # ampiezze reali delle costellazioni
```

## Struttura

```
src/engine/       motore astronomico puro, zero dipendenze da React
tests/engine/     test con valori di riferimento esterni
  fixtures/       campioni JPL Horizons (dati pubblici NASA/JPL)
scripts/          chart-cli.ts: stampa testuale della carta
docs/METODO.md    documentazione tecnica delle scelte di calcolo
```

## Scelte vincolate

- `astronomy-engine` 2.1.19 (MIT) — mai Swiss Ephemeris (AGPL).
- Tutto client-side: nessun dato di nascita lascia il dispositivo.
- Intervallo supportato dichiarato: 1700–2200.
- Licenza del progetto: GPL-3.0.

I dettagli di ogni scelta di calcolo, con le verifiche eseguite, sono in
[docs/METODO.md](docs/METODO.md).
