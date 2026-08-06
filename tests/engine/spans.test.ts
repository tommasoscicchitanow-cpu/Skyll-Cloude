/**
 * Test sulle ampiezze calcolate delle costellazioni (§3.6, §10.2).
 */
import { describe, expect, it } from 'vitest';
import { solarConstellationSpans } from '../../src/engine/spans';

describe('finestre di transito solare 2026', () => {
  const spans = solarConstellationSpans(2026);

  function span(symbol: string, after?: string) {
    const startIdx = after ? spans.findIndex((s) => s.key === after) + 1 : 0;
    const found = spans.slice(startIdx).find((s) => s.key === symbol);
    if (!found) throw new Error(`nessuna finestra per ${symbol}`);
    return found;
  }

  it('coprono l\'anno senza buchi né sovrapposizioni', () => {
    for (let i = 1; i < spans.length; i++) {
      expect(spans[i]!.enterUtc).toBe(spans[i - 1]!.exitUtc);
    }
    expect(Date.parse(spans[0]!.enterUtc)).toBeLessThanOrEqual(
      Date.parse('2026-01-01T00:00:00Z'),
    );
    expect(Date.parse(spans.at(-1)!.exitUtc)).toBeGreaterThanOrEqual(
      Date.parse('2027-01-01T00:00:00Z'),
    );
  });

  it('attraversano solo le 13 costellazioni zodiacali', () => {
    const symbols = new Set(spans.map((s) => s.key));
    const expected = new Set([
      'Sgr', 'Cap', 'Aqr', 'Psc', 'Ari', 'Tau', 'Gem', 'Cnc', 'Leo', 'Vir',
      'Lib', 'Sco', 'Oph',
    ]);
    for (const s of symbols) expect(expected.has(s), s).toBe(true);
  });

  it('Ofiuco: ingresso 30 novembre, uscita 18 dicembre (±1 giorno)', () => {
    const oph = span('Oph');
    expect(Math.abs(Date.parse(oph.enterUtc) - Date.parse('2026-11-30T12:00:00Z')))
      .toBeLessThan(36 * 3600 * 1000);
    expect(Math.abs(Date.parse(oph.exitUtc) - Date.parse('2026-12-18T12:00:00Z')))
      .toBeLessThan(36 * 3600 * 1000);
    expect(oph.days).toBeGreaterThan(16);
    expect(oph.days).toBeLessThan(20);
  });

  it('Vergine larghissima (~45 giorni), Scorpione strettissimo (~6 giorni)', () => {
    const vir = span('Vir');
    const sco = span('Sco');
    expect(vir.days).toBeGreaterThan(42);
    expect(vir.days).toBeLessThan(48);
    expect(sco.days).toBeGreaterThan(5);
    expect(sco.days).toBeLessThan(8);
    // L'arbitrarietà dei dodici settori uguali, in un numero:
    expect(vir.days / sco.days).toBeGreaterThan(5);
  });

  it('le finestre sono precise al minuto (bisezione)', () => {
    const oph = span('Oph');
    const enter = new Date(oph.enterUtc);
    // La bisezione si ferma sotto il mezzo minuto: il valore non è
    // arrotondato al giorno.
    expect(enter.getUTCHours() + enter.getUTCMinutes()).not.toBe(0);
  });
});
