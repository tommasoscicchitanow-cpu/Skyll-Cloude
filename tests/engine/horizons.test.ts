/**
 * Test di riferimento sulle effemeridi (§10.1).
 *
 * Valori attesi: JPL Horizons (dati pubblici NASA/JPL), campionati dai file
 * di verifica del repository upstream cosinekitty/astronomy
 * (generate/horizons/*.txt): colonna astrometrica ICRF/J2000, osservatore
 * topocentrico a 29°N 81°W. Il confronto usa Equator(..., ofdate=false,
 * aberration=false), che è la stessa semantica ("astrometric" = corretta
 * per tempo-luce, senza aberrazione), e il modello DeltaT di JPL Horizons
 * per coerenza con la sorgente.
 *
 * Tolleranza dichiarata: 1 primo d'arco per pianeti e Sole; 1 primo anche
 * per la Luna (topocentrica, quindi con parallasse inclusa).
 */
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import {
  Body,
  DeltaT_EspenakMeeus,
  DeltaT_JplHorizons,
  Equator,
  Observer,
  SetDeltaTFunction,
} from 'astronomy-engine';
import fixture from './fixtures/horizons.json';

const DEG2RAD = Math.PI / 180;

const BODY_MAP: Record<string, Body> = {
  Sun: Body.Sun,
  Moon: Body.Moon,
  Mercury: Body.Mercury,
  Venus: Body.Venus,
  Mars: Body.Mars,
  Jupiter: Body.Jupiter,
  Saturn: Body.Saturn,
  Uranus: Body.Uranus,
  Neptune: Body.Neptune,
  Pluto: Body.Pluto,
};

const ARCMIN_TOLERANCE = 1.0;

describe('confronto con JPL Horizons', () => {
  beforeAll(() => SetDeltaTFunction(DeltaT_JplHorizons));
  afterAll(() => SetDeltaTFunction(DeltaT_EspenakMeeus));

  const observer = new Observer(
    fixture.site.latitude,
    fixture.site.longitude,
    fixture.site.elevationMeters,
  );

  for (const sample of fixture.samples) {
    it(`${sample.body}: ${sample.rows.length} istanti entro ${ARCMIN_TOLERANCE}′`, () => {
      let worst = 0;
      for (const row of sample.rows) {
        const date = new Date(row.utc);
        const eq = Equator(BODY_MAP[sample.body]!, date, observer, false, false);
        let raErr = Math.abs(eq.ra * 15 - row.raDeg);
        if (raErr > 180) raErr = 360 - raErr;
        const raArcmin = raErr * 60 * Math.cos(row.dec * DEG2RAD);
        const decArcmin = Math.abs(eq.dec - row.dec) * 60;
        const arcmin = Math.hypot(raArcmin, decArcmin);
        worst = Math.max(worst, arcmin);
        expect(arcmin, `${sample.body} @ ${row.utc}`).toBeLessThan(
          ARCMIN_TOLERANCE,
        );
      }
      // Log del massimo scarto per la documentazione della precisione.
      // eslint-disable-next-line no-console
      console.log(`${sample.body}: max ${worst.toFixed(3)}′`);
    });
  }
});
