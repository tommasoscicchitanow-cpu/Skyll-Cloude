/**
 * Test sugli aspetti (§3.7).
 */
import { describe, expect, it } from 'vitest';
import { computeAspects, DEFAULT_ORBS } from '../../src/engine/aspects';

describe('computeAspects', () => {
  it('riconosce i cinque aspetti maggiori entro l\'orbe', () => {
    const hits = computeAspects([
      { body: 'Sun', longitude: 10 },
      { body: 'Moon', longitude: 12 }, // congiunzione, orbe 2
      { body: 'Mars', longitude: 100.5 }, // quadratura col Sole, orbe 0.5
      { body: 'Jupiter', longitude: 190.1 }, // opposizione col Sole, orbe 0.1
      { body: 'Venus', longitude: 71 }, // sestile col Sole, orbe 1
    ]);
    const get = (a: string, b: string) =>
      hits.find(
        (h) => (h.a === a && h.b === b) || (h.a === b && h.b === a),
      );
    expect(get('Sun', 'Moon')?.type).toBe('conjunction');
    expect(get('Sun', 'Mars')?.type).toBe('square');
    expect(get('Sun', 'Jupiter')?.type).toBe('opposition');
    expect(get('Sun', 'Venus')?.type).toBe('sextile');
  });

  it('fuori orbe: nessun aspetto', () => {
    const hits = computeAspects([
      { body: 'Sun', longitude: 0 },
      { body: 'Moon', longitude: 45 },
    ]);
    expect(hits).toHaveLength(0);
  });

  it('gestisce il passaggio per 0°', () => {
    const hits = computeAspects([
      { body: 'Sun', longitude: 359 },
      { body: 'Moon', longitude: 3 },
    ]);
    expect(hits[0]?.type).toBe('conjunction');
    expect(hits[0]?.orb).toBeCloseTo(4, 10);
  });

  it('orbi configurabili', () => {
    const none = computeAspects(
      [
        { body: 'Sun', longitude: 0 },
        { body: 'Moon', longitude: 7 },
      ],
      { conjunction: 5 },
    );
    expect(none).toHaveLength(0);
    expect(DEFAULT_ORBS.conjunction).toBe(8);
  });

  it('i due nodi non formano aspetti fra loro', () => {
    const hits = computeAspects([
      { body: 'MeanNode', longitude: 100 },
      { body: 'TrueNode', longitude: 101 },
    ]);
    expect(hits).toHaveLength(0);
  });
});
