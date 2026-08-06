/**
 * Test su Ascendente, Medio Cielo e case (§3.4, §3.5, §10.5).
 *
 * Verifica geometrica indipendente: l'Ascendente deve giacere
 * sull'orizzonte (altezza 0 senza rifrazione) sul lato est; il Medio Cielo
 * deve avere angolo orario nullo (RA della data = RAMC).
 */
import { describe, expect, it } from 'vitest';
import { Horizon, MakeTime, Observer, e_tilt } from 'astronomy-engine';
import {
  computeAngles,
  computeAnglesRaw,
  houseCusps,
} from '../../src/engine/houses';
import { normalizeDegrees } from '../../src/engine/types';

const DEG = Math.PI / 180;

/** RA (ore) e Dec (gradi) "of date" di un punto dell'eclittica vera. */
function ofDateFromEcliptic(lambda: number, epsDeg: number) {
  const l = lambda * DEG;
  const e = epsDeg * DEG;
  const x = Math.cos(l);
  const y = Math.sin(l) * Math.cos(e);
  const z = Math.sin(l) * Math.sin(e);
  const ra = normalizeDegrees(Math.atan2(y, x) / DEG) / 15;
  const dec = Math.asin(z) / DEG;
  return { ra, dec };
}

const CASES = [
  { name: 'Roma', lat: 41.9, lon: 12.5, iso: '1990-05-10T14:30:00Z' },
  { name: 'Sydney', lat: -33.87, lon: 151.21, iso: '2005-11-02T03:15:00Z' },
  { name: 'Quito', lat: -0.18, lon: -78.47, iso: '1977-01-21T09:00:00Z' },
  { name: 'Reykjavik', lat: 64.15, lon: -21.94, iso: '2000-06-21T00:00:00Z' },
  { name: 'Longitudine 180', lat: -16.5, lon: 180, iso: '1988-08-08T08:08:00Z' },
];

describe('Ascendente e Medio Cielo: verifica geometrica', () => {
  for (const c of CASES) {
    it(`${c.name}: ASC sull'orizzonte a est, MC sul meridiano`, () => {
      const time = MakeTime(new Date(c.iso));
      const raw = computeAnglesRaw(time, c.lat, c.lon);
      expect(raw.degenerate).toBe(false);
      const eps = e_tilt(time).tobl;
      const observer = new Observer(c.lat, c.lon, 0);

      // ASC: altezza ~0 (senza rifrazione), azimut orientale (0..180).
      const asc = ofDateFromEcliptic(raw.ascendant, eps);
      const horAsc = Horizon(time, observer, asc.ra, asc.dec);
      expect(Math.abs(horAsc.altitude)).toBeLessThan(0.02);
      expect(horAsc.azimuth).toBeGreaterThan(0);
      expect(horAsc.azimuth).toBeLessThan(180);

      // MC: angolo orario nullo → RA della data uguale al RAMC.
      const mc = ofDateFromEcliptic(raw.midheaven, eps);
      let dRa = Math.abs(mc.ra * 15 - raw.ramc);
      if (dRa > 180) dRa = 360 - dRa;
      expect(dRa).toBeLessThan(0.01);
    });
  }

  it('latitudini polari estreme: il caso degenere è segnalato, non un crash', () => {
    // Con lo zenit vicino al polo dell'eclittica il piano dell'orizzonte e
    // quello dell'eclittica quasi coincidono. Cerchiamo un istante critico
    // a 89.9° di latitudine: qualunque risultato deve essere finito o
    // dichiarato degenere, mai NaN silenzioso.
    for (let h = 0; h < 24; h += 1) {
      const t = MakeTime(new Date(Date.UTC(2020, 2, 20, h)));
      const raw = computeAnglesRaw(t, 89.9, 0);
      if (!raw.degenerate) {
        expect(Number.isFinite(raw.ascendant)).toBe(true);
      }
      expect(Number.isFinite(raw.midheaven)).toBe(true);
    }
  });
});

describe('sistemi di case', () => {
  const ctx = {
    ascendant: 123.45,
    midheaven: 33.3,
    ramc: 30,
    obliquity: 23.44,
    latitude: 45,
  };

  it('whole sign: dodici cuspidi sui confini dei segni', () => {
    const { cusps } = houseCusps('whole-sign', ctx);
    expect(cusps).toHaveLength(12);
    expect(cusps[0]).toBe(120); // ASC in Leone → casa 1 = 120°
    for (const c of cusps) expect(c % 30).toBe(0);
  });

  it('equal: dodici cuspidi a 30° esatti dall\'Ascendente', () => {
    const { cusps } = houseCusps('equal', ctx);
    expect(cusps[0]).toBeCloseTo(123.45, 10);
    expect(cusps[6]).toBeCloseTo(normalizeDegrees(123.45 + 180), 10);
  });
});

describe('computeAngles: costellazione IAU anche per ASC e MC (§3.4)', () => {
  it('restituisce una costellazione per entrambi i punti', () => {
    const res = computeAngles(
      new Date('1990-05-10T14:30:00Z'),
      41.9,
      12.5,
      'lahiri',
    );
    expect(res.ascendant.constellation.symbol).toMatch(/^[A-Z]/);
    expect(res.midheaven.constellation.symbol).toMatch(/^[A-Z]/);
    expect(res.degenerate).toBe(false);
  });
});
