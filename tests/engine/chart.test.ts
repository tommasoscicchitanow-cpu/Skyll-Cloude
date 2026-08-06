/**
 * Test d'integrazione del calcolo della carta completa.
 */
import { describe, expect, it } from 'vitest';
import { computeChart } from '../../src/engine/chart';
import { resolveBirthTime } from '../../src/engine/time';

function chartFor(overrides: Partial<Parameters<typeof computeChart>[0]> = {}) {
  const resolved = resolveBirthTime({
    year: 1990, month: 5, day: 10, hour: 16, minute: 30,
    timeKnown: true, latitude: 41.9, longitude: 12.5,
  });
  return computeChart({
    utc: resolved.utc,
    latitude: 41.9,
    longitude: 12.5,
    timeKnown: true,
    ayanamsa: 'lahiri',
    ...overrides,
  });
}

describe('computeChart', () => {
  it('calcola dodici corpi, angoli, case e aspetti', () => {
    const chart = chartFor();
    expect(chart.bodies).toHaveLength(12);
    expect(chart.angles).not.toBeNull();
    expect(chart.houses?.map((h) => h.system)).toEqual([
      'whole-sign', 'equal',
    ]);
    expect(chart.aspects.length).toBeGreaterThan(0);
    expect(Number.isFinite(chart.ayanamsaDegrees)).toBe(true);
    // Tropicale meno ayanamsa = siderale, per ogni corpo.
    for (const b of chart.bodies) {
      const expected =
        (((b.ecliptic.longitude - chart.ayanamsaDegrees) % 360) + 360) % 360;
      expect(b.siderealLongitude).toBeCloseTo(expected, 9);
    }
  });

  it('ora ignota: niente angoli né case, escursione della Luna presente', () => {
    const chart = chartFor({ timeKnown: false });
    expect(chart.angles).toBeNull();
    expect(chart.houses).toBeNull();
    expect(chart.moonDailyRange).toBeDefined();
    expect(chart.warnings.some((w) => w.code === 'time-unknown')).toBe(true);
  });

  it('fuori intervallo: avvertenza esplicita e nessun numero degradato', () => {
    const chart = chartFor({ utc: new Date('1500-01-01T12:00:00Z') });
    expect(chart.bodies).toHaveLength(0);
    expect(
      chart.warnings.some((w) => w.code === 'outside-supported-range'),
    ).toBe(true);
  });

  it('latitudine polare: avvertenza dedicata', () => {
    const chart = chartFor({ latitude: 78 });
    expect(
      chart.warnings.some((w) => w.code === 'polar-degenerate-angles'),
    ).toBe(true);
  });

  it('un solo nodo partecipa agli aspetti', () => {
    const chart = chartFor();
    expect(chart.aspects.some((a) => a.a === 'MeanNode' || a.b === 'MeanNode'))
      .toBe(false);
  });
});
