/**
 * Test sull'ayanamsa (§10.4).
 */
import { describe, expect, it } from 'vitest';
import { ayanamsaDegrees, AYANAMSA_ANCHORS } from '../../src/engine/ayanamsa';

function dms(d: number, m: number, s: number): number {
  return d + m / 60 + s / 3600;
}

describe('Lahiri / Chitrapaksha', () => {
  it('riproduce il valore di definizione all\'ancoraggio (21/03/1956)', () => {
    const v = ayanamsaDegrees('lahiri', new Date(Date.UTC(1956, 2, 21)));
    expect(v).toBeCloseTo(dms(23, 15, 0.658), 6);
  });

  it('cresce al ritmo della precessione (~50,3″/anno)', () => {
    // Finestra lunga (200 anni) per mediare l'oscillazione di nutazione
    // (±17″ con periodo 18,6 anni), inclusa nell'eclittica vera.
    const v1850 = ayanamsaDegrees('lahiri', new Date(Date.UTC(1850, 0, 1)));
    const v2050 = ayanamsaDegrees('lahiri', new Date(Date.UTC(2050, 0, 1)));
    const ratePerYear = ((v2050 - v1850) / 200) * 3600;
    expect(ratePerYear).toBeGreaterThan(49.8);
    expect(ratePerYear).toBeLessThan(50.8);
  });

  it('valori pubblicati: ~23°51′ nel 2000, ~24°09′ nel 2020 (±1′)', () => {
    // Estrapolazione lineare dall'ancoraggio del 1956 (23°15′00.658″) con
    // precessione ~50,29″/anno, coerente con i valori dell'Indian
    // Astronomical Ephemeris.
    const v2000 = ayanamsaDegrees('lahiri', new Date(Date.UTC(2000, 0, 1)));
    expect(v2000 * 60).toBeGreaterThan(dms(23, 51, 0) * 60 - 1);
    expect(v2000 * 60).toBeLessThan(dms(23, 52, 0) * 60 + 1);
    const v2020 = ayanamsaDegrees('lahiri', new Date(Date.UTC(2020, 0, 1)));
    expect(v2020 * 60).toBeGreaterThan(dms(24, 8, 0) * 60 - 1);
    expect(v2020 * 60).toBeLessThan(dms(24, 10, 0) * 60 + 1);
  });
});

describe('Fagan-Bradley', () => {
  it('riproduce il valore di definizione all\'ancoraggio (01/01/1950)', () => {
    const v = ayanamsaDegrees('fagan-bradley', new Date(Date.UTC(1950, 0, 1)));
    expect(v).toBeCloseTo(dms(24, 2, 31.36), 6);
  });

  it('resta maggiore del Lahiri di ~0,88° a ogni epoca', () => {
    for (const year of [1850, 1950, 2000, 2050]) {
      const d = new Date(Date.UTC(year, 0, 1));
      const diff =
        ayanamsaDegrees('fagan-bradley', d) - ayanamsaDegrees('lahiri', d);
      expect(diff).toBeGreaterThan(0.8);
      expect(diff).toBeLessThan(1.0);
    }
  });
});

describe('coerenza interna', () => {
  it('gli ancoraggi dichiarati sono quelli documentati', () => {
    expect(AYANAMSA_ANCHORS.lahiri.anchorDegrees).toBeCloseTo(23.2501828, 6);
    expect(AYANAMSA_ANCHORS['fagan-bradley'].anchorDegrees).toBeCloseTo(
      24.0420444, 6,
    );
  });
});
