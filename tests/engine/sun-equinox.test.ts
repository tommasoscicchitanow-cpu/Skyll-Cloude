/**
 * Riferimento esterno indipendente: agli istanti pubblicati di equinozi e
 * solstizi la longitudine eclittica apparente del Sole vale per definizione
 * 0°, 90°, 180°, 270°. Istanti dall'Astronomical Almanac / USNO per il 2000.
 */
import { describe, expect, it } from 'vitest';
import { Body, GeoVector, Ecliptic } from 'astronomy-engine';
import { angularDelta } from '../../src/engine/bodies';

function sunLongitude(iso: string): number {
  return Ecliptic(GeoVector(Body.Sun, new Date(iso), true)).elon;
}

describe('longitudine apparente del Sole agli equinozi e ai solstizi 2000', () => {
  const cases: [string, number][] = [
    ['2000-03-20T07:35:00Z', 0],
    ['2000-06-21T01:48:00Z', 90],
    ['2000-09-22T17:28:00Z', 180],
    ['2000-12-21T13:37:00Z', 270],
  ];
  for (const [iso, expected] of cases) {
    it(`${iso} → ${expected}°`, () => {
      const lon = sunLongitude(iso);
      // Tolleranza 0,005° ≈ ±7 minuti di tempo sull'istante pubblicato.
      expect(Math.abs(angularDelta(expected, lon))).toBeLessThan(0.005);
    });
  }
});
