# Metodo di calcolo — documentazione tecnica

Stato: fase 1 (motore astronomico). Questo documento cresce con il progetto.

## Effemeridi

Il motore usa [`astronomy-engine`](https://github.com/cosinekitty/astronomy)
2.1.19 di Don Cross (licenza MIT): VSOP87 troncato per i pianeti, modello
TOP2013 adattato per Plutone, teoria lunare derivata da ELP. L'autore
dichiara una precisione entro ±1 primo d'arco rispetto alle effemeridi JPL
nell'intervallo 1700–2200, che adottiamo come **intervallo supportato
dichiarato**: fuori da esso l'app avvisa e non mostra numeri degradati.

### Verifica indipendente eseguita

- **JPL Horizons** (§10.1): 120 istanti campionati (12 per corpo,
  1908–2091 per i pianeti interni/esterni, 1962–2017 per Nettuno e
  Plutone) dai file di verifica del repository upstream, colonna
  astrometrica ICRF/J2000, osservatore topocentrico 29°N 81°W. Confronto
  con `Equator(body, t, observer, ofdate=false, aberration=false)` e
  modello ΔT di JPL Horizons. **Scarto massimo misurato: Sole 0,03′,
  Luna 0,36′, Mercurio 0,12′, Venere 0,15′, Marte 0,08′, Giove 0,17′,
  Saturno 0,33′, Urano 0,17′, Nettuno 0,31′, Plutone 0,05′** — tutti
  entro la tolleranza dichiarata di 1′.
- **Equinozi e solstizi 2000** (Astronomical Almanac/USNO): la
  longitudine apparente del Sole risulta 0°/90°/180°/270° entro 0,005°
  agli istanti pubblicati.

## Sequenza di calcolo per ogni corpo

1. `GeoVector(body, t, true)` → vettore geocentrico apparente nel sistema
   **EQJ** (equatore medio J2000), con correzione per tempo-luce e
   aberrazione.
2. `Ecliptic(vec)` → longitudine e latitudine sull'**eclittica vera della
   data** (ECT). È il riferimento per le viste tropicale e siderale.
3. `EquatorFromVector(vec)` → RA/Dec **J2000**, passate a
   `Constellation()`, che precede internamente all'epoca **B1875** dei
   confini IAU (delimitazione di Delporte, 1930).
4. Retrogradazione: segno della derivata numerica della longitudine su
   ±6 ore.

### La trappola del doppio conteggio della precessione

`Constellation()` vuole coordinate J2000 e precede da sola a B1875.
Passare coordinate «of date» (`Equator(..., ofdate=true)`) conta la
precessione due volte: misurato al 2026 lo scarto vale ~0,4° e anticipa
di ~9 ore l'ingresso del Sole in Ofiuco. Test di regressione:
`tests/engine/constellations.test.ts` (include anche la stabilità secolare
di stelle fisse: Regolo resta in Leone e Spica in Vergine dal 1700 al 2200).

### Costellazione dalla posizione reale, non dalla proiezione

La costellazione è determinata da RA **e** declinazione. Plutone
(inclinazione ~17°) attraversa nel Novecento costellazioni fuori dalla
fascia zodiacale: il motore verifica Chioma di Berenice (1971), Boote
(1980), Serpente (1991). Nota: per effetto dei moti retrogradi apparenti i
passaggi di confine si ripetono più volte; le finestre "1969–1974",
"1980–81", "1990–2006" citate in letteratura sono letture a grana grossa
di una sequenza fatta di andirivieni (il motore la riproduce per intero).

## Nodi lunari

- **Nodo medio**: polinomio di Meeus (Astronomical Algorithms, 2ª ed.,
  cap. 47) riferito all'equinozio medio, più la nutazione in longitudine
  per coerenza con l'equinozio vero usato per gli altri corpi.
- **Nodo vero (osculante)**: dal vettore di stato geocentrico della Luna
  (`GeoMoonState`), ruotato in ECT: il momento angolare r×v definisce il
  piano orbitale istantaneo, il nodo ascendente è ẑ×h.
- Verifiche: valore J2000 (~125,04°), moto medio retrogrado ~−0,053°/g,
  |vero − medio| < 2,5°.

## Ascendente e Medio Cielo

Tempo siderale apparente di Greenwich (`SiderealTime`) + longitudine
geografica → RAMC; obliquità vera (`e_tilt().tobl`). Il MC è il punto
dell'eclittica con angolo orario nullo; l'Ascendente è l'intersezione
orientale fra piano dell'orizzonte e piano dell'eclittica, calcolata
vettorialmente (niente ambiguità di quadrante). Verifica geometrica nei
test: l'ASC ha altezza 0 (senza rifrazione) e azimut orientale, il MC ha
RA = RAMC, in 5 località comprese Sydney, Quito e Reykjavik.

Caso degenere polare: quando lo zenit è quasi allineato al polo
dell'eclittica i due piani quasi coincidono; il motore segnala
`degenerate` e l'app mostra l'avvertenza (soglia di avviso: |φ| > 66°).

## Case

Fase 1: Whole Sign ed Equal House. L'interfaccia del modulo
(`HouseContext`) trasporta già RAMC, obliquità e latitudine, così i
sistemi quadranti della fase 2 (Placidus, Koch, Campanus) si aggiungono
senza riscritture.

## Ayanamsa

`λ_siderale = λ_tropicale − ayanamsa`. Implementazione ad ancoraggio:

| Sistema | Epoca t₀ | Valore a t₀ | Fonte |
|---|---|---|---|
| Lahiri (Chitrapaksha) — default | 21/03/1956 00:00 (JD 2435553.5) | 23°15′00,658″ | Indian Calendar Reform Committee / Indian Astronomical Ephemeris |
| Fagan-Bradley | 01/01/1950 00:00 (JD 2433282.5) | 24°02′31,36″ | Fagan & Bradley (parametri standard, cfr. Swiss Ephemeris) |

L'accumulo di precessione fra t₀ e la data è misurato con le matrici di
rotazione della libreria: longitudine, sull'eclittica vera della data,
della direzione fissa dell'equinozio J2000. Poiché si usa l'eclittica
vera, il valore include la nutazione (±17″ con periodo 18,6 anni):
scarto massimo rispetto ai valori pubblicati su equinozio medio ~18″,
sotto la precisione di 1′ dichiarata dall'app. Tasso verificato nei test:
~50,3″/anno su una finestra di 200 anni.

## Ampiezze delle costellazioni

Calcolate a runtime (`spans.ts`): campionamento giornaliero della
costellazione del Sole e bisezione di ogni attraversamento di confine
fino a precisione < 1 minuto. Nessuna costante scritta a mano.
Riferimento 2026 verificato nei test: Ofiuco 30/11 → 18/12 (~18,3 giorni),
Vergine 17/09 → 31/10 (~44,5 giorni), Scorpione 23/11 → 30/11
(~6,5 giorni).

## Aspetti

Congiunzione, sestile, quadratura, trigono, opposizione sulle longitudini
eclittiche reali. Orbi di default: 8° (congiunzione/opposizione),
6° (trigono/quadratura), 4° (sestile), configurabili. Gli aspetti sono
identici nelle tre viste: dipendono dalle distanze angolari, non dalla
segmentazione del cerchio.

## Data, ora e fuso

- Fuso da coordinate: `tz-lookup` (offline). Conversione in UTC: Luxon con
  database IANA, che applica le regole storiche (ora legale passata e
  tempo locale medio pre-standardizzazione: per Roma LMT +00:49:56 fino
  al 31/10/1893 — verificato nei test).
- Ora inesistente (buco dell'ora legale) e ora ambigua (ritorno all'ora
  solare) sono rilevate e segnalate.
- Ora ignota: calcolo alle 12:00 locali, Ascendente/MC/case disattivati,
  escursione della Luna nella giornata mostrata.
- Calendario: le date sono interpretate nel calendario **gregoriano**.
  Il passaggio giuliano/gregoriano (1582) è fuori dall'intervallo
  supportato (1700–2200), quindi non si pone; resta dichiarato qui.

## ΔT

In produzione si usa il modello di default di astronomy-engine
(Espenak-Meeus). Solo il test di confronto con Horizons imposta
temporaneamente il modello ΔT di JPL per coerenza con la sorgente dei
valori attesi (differenze dell'ordine dei secondi, rilevanti solo per la
Luna al di sotto del primo d'arco).

## Dati di terze parti

- Campioni JPL Horizons: dati pubblici NASA/JPL, via repository
  cosinekitty/astronomy (MIT).
- (Fase 2) GeoNames `cities5000`, licenza CC BY 4.0, attribuzione nei
  crediti dell'app.
