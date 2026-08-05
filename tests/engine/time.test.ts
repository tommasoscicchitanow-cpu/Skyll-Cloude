/**
 * Test sui fusi orari e sulla risoluzione dell'istante di nascita (§10.3).
 */
import { describe, expect, it } from 'vitest';
import { resolveBirthTime, resolveZone } from '../../src/engine/time';

describe('risoluzione del fuso da coordinate', () => {
  it('Roma → Europe/Rome', () => {
    expect(resolveZone(41.9, 12.5)).toBe('Europe/Rome');
  });
  it('longitudine 180 → una zona valida', () => {
    expect(typeof resolveZone(-16.5, 180)).toBe('string');
  });
});

describe('nascite italiane', () => {
  it('1980, ora legale attiva: offset +2', () => {
    const r = resolveBirthTime({
      year: 1980, month: 7, day: 15, hour: 10, minute: 0,
      timeKnown: true, latitude: 41.9, longitude: 12.5,
    });
    expect(r.offsetMinutes).toBe(120);
    expect(r.utc.toISOString()).toBe('1980-07-15T08:00:00.000Z');
  });

  it('1980, inverno: offset +1', () => {
    const r = resolveBirthTime({
      year: 1980, month: 1, day: 15, hour: 10, minute: 0,
      timeKnown: true, latitude: 41.9, longitude: 12.5,
    });
    expect(r.offsetMinutes).toBe(60);
  });

  it('prima del 1893: tempo locale medio di Roma (+00:49:56)', () => {
    const r = resolveBirthTime({
      year: 1880, month: 3, day: 2, hour: 12, minute: 0,
      timeKnown: true, latitude: 41.9, longitude: 12.5,
    });
    // Il database IANA attribuisce a Europe/Rome l'LMT +00:49:56 fino al
    // 1893-10-31: mezzogiorno locale corrisponde alle 11:10:04 UTC.
    expect(r.offsetMinutes).toBeCloseTo(49.93, 1);
    expect(r.utc.toISOString()).toBe('1880-03-02T11:10:04.000Z');
  });

  it('giorno del passaggio all\'ora legale: l\'ora inesistente è segnalata', () => {
    // In Italia il 30 marzo 2003 le 02:30 non esistono (salto 02:00→03:00).
    const r = resolveBirthTime({
      year: 2003, month: 3, day: 30, hour: 2, minute: 30,
      timeKnown: true, latitude: 41.9, longitude: 12.5,
    });
    expect(r.adjustedForGap).toBe(true);
  });

  it('ritorno all\'ora solare: l\'ora ambigua è segnalata', () => {
    // Il 26 ottobre 2003 le 02:30 esistono due volte.
    const r = resolveBirthTime({
      year: 2003, month: 10, day: 26, hour: 2, minute: 30,
      timeKnown: true, latitude: 41.9, longitude: 12.5,
    });
    expect(r.ambiguous).toBe(true);
  });

  it('nascita a cavallo della mezzanotte', () => {
    const r = resolveBirthTime({
      year: 1999, month: 12, day: 31, hour: 23, minute: 59,
      timeKnown: true, latitude: 41.9, longitude: 12.5,
    });
    expect(r.utc.toISOString()).toBe('1999-12-31T22:59:00.000Z');
  });
});

describe('casi limite di calendario (§10.5)', () => {
  it('29 febbraio in anno bisestile: valido', () => {
    const r = resolveBirthTime({
      year: 2000, month: 2, day: 29, hour: 12, minute: 0,
      timeKnown: true, latitude: 41.9, longitude: 12.5,
    });
    expect(r.error).toBeUndefined();
  });

  it('29 febbraio in anno secolare non bisestile (1900): errore esplicito', () => {
    const r = resolveBirthTime({
      year: 1900, month: 2, day: 29, hour: 12, minute: 0,
      timeKnown: true, latitude: 41.9, longitude: 12.5,
    });
    expect(r.error).toBeDefined();
  });

  it('fuori intervallo supportato: segnalato, non silenzioso', () => {
    const r = resolveBirthTime({
      year: 1650, month: 6, day: 1, hour: 12, minute: 0,
      timeKnown: true, latitude: 41.9, longitude: 12.5,
    });
    expect(r.outsideSupportedRange).toBe(true);
  });

  it('ora ignota: si usano le 12:00 locali', () => {
    const r = resolveBirthTime({
      year: 1975, month: 4, day: 20,
      timeKnown: false, latitude: 41.9, longitude: 12.5,
    });
    expect(r.localIso.includes('T12:00')).toBe(true);
  });
});
