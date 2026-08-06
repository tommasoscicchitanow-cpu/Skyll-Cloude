/**
 * Test sui nodi lunari (§3.1).
 */
import { describe, expect, it } from 'vitest';
import { MakeTime } from 'astronomy-engine';
import {
  meanNodeLongitude,
  trueNodeLongitude,
  computeBody,
  angularDelta,
} from '../../src/engine/bodies';

describe('nodo lunare medio', () => {
  it('a J2000.0 vale ~125,04° (Meeus) più la nutazione', () => {
    // J2000.0 = 2000-01-01 12:00 TT ≈ 11:58:56 UTC.
    const t = MakeTime(new Date('2000-01-01T11:58:56Z'));
    const v = meanNodeLongitude(t);
    // Valore di Meeus per l'equinozio medio: 125,0445°; la nutazione in
    // longitudine a quell'epoca è ~ -13,9″ ≈ -0,004°.
    expect(v).toBeGreaterThan(124.9);
    expect(v).toBeLessThan(125.2);
  });

  it('è sempre retrogrado (~ -0,053°/giorno)', () => {
    const t1 = MakeTime(new Date('2010-03-01T00:00:00Z'));
    const t2 = MakeTime(new Date('2010-03-31T00:00:00Z'));
    const drift = angularDelta(meanNodeLongitude(t1), meanNodeLongitude(t2)) / 30;
    expect(drift).toBeLessThan(-0.05);
    expect(drift).toBeGreaterThan(-0.056);
  });
});

describe('nodo lunare vero', () => {
  it('oscilla attorno al medio entro ~2,5°', () => {
    for (const iso of [
      '1950-06-01T00:00:00Z',
      '1988-11-11T00:00:00Z',
      '2000-01-01T00:00:00Z',
      '2026-08-05T00:00:00Z',
    ]) {
      const t = MakeTime(new Date(iso));
      const d = Math.abs(angularDelta(meanNodeLongitude(t), trueNodeLongitude(t)));
      expect(d, iso).toBeLessThan(2.5);
    }
  });

  it('ha latitudine eclittica nulla per costruzione', () => {
    const p = computeBody('TrueNode', new Date('2003-07-07T00:00:00Z'), {
      ayanamsa: 'lahiri',
    });
    expect(Math.abs(p.ecliptic.latitude)).toBeLessThan(1e-9);
    // Il nodo giace sull'eclittica: la costellazione è nella fascia zodiacale.
    expect(p.constellation.zodiacal).toBe(true);
  });
});
