/**
 * Test sulle costellazioni IAU (§10.2 e §3.3).
 */
import { describe, expect, it } from 'vitest';
import {
  Body,
  DefineStar,
  Equator,
  GeoVector,
  MakeTime,
  Observer,
} from 'astronomy-engine';
import {
  constellationFromJ2000,
  constellationFromVector,
} from '../../src/engine/constellations';
import { computeBody } from '../../src/engine/bodies';

function sunConstellationOn(iso: string): string {
  const vec = GeoVector(Body.Sun, new Date(iso), true);
  return constellationFromVector(vec).symbol;
}

describe('Sole nelle costellazioni reali, 2026 (riferimento del briefing)', () => {
  it('è in Ofiuco fra il 30 novembre e il 18 dicembre', () => {
    expect(sunConstellationOn('2026-12-01T00:00:00Z')).toBe('Oph');
    expect(sunConstellationOn('2026-12-10T00:00:00Z')).toBe('Oph');
    expect(sunConstellationOn('2026-12-17T00:00:00Z')).toBe('Oph');
    // Subito prima e subito dopo la finestra dichiarata:
    expect(sunConstellationOn('2026-11-29T00:00:00Z')).toBe('Sco');
    expect(sunConstellationOn('2026-12-19T12:00:00Z')).toBe('Sgr');
  });

  it('è in Vergine dal 17 settembre al 1 novembre', () => {
    expect(sunConstellationOn('2026-09-18T00:00:00Z')).toBe('Vir');
    expect(sunConstellationOn('2026-10-15T00:00:00Z')).toBe('Vir');
    expect(sunConstellationOn('2026-10-31T00:00:00Z')).toBe('Vir');
    expect(sunConstellationOn('2026-09-16T00:00:00Z')).toBe('Leo');
    expect(sunConstellationOn('2026-11-02T00:00:00Z')).toBe('Lib');
  });

  it('è in Scorpione solo dal 24 al 30 novembre (circa 6 giorni)', () => {
    expect(sunConstellationOn('2026-11-25T00:00:00Z')).toBe('Sco');
    expect(sunConstellationOn('2026-11-23T00:00:00Z')).toBe('Lib');
  });
});

describe('Plutone: latitudine eclittica alta, fuori dalla fascia zodiacale (§3.3)', () => {
  it('nel 1971 è nella Chioma di Berenice (Com)', () => {
    const p = computeBody('Pluto', new Date('1971-06-01T00:00:00Z'), {
      ayanamsa: 'lahiri',
    });
    expect(p.constellation.symbol).toBe('Com');
    expect(p.constellation.zodiacal).toBe(false);
  });

  it('nel 1980 è in Boote (Boo)', () => {
    // I moti retrogradi fanno oscillare Plutone più volte fra Vergine e
    // Boote nel 1979-1981; la finestra continua verificata col motore è
    // febbraio-ottobre 1980.
    const p = computeBody('Pluto', new Date('1980-05-01T00:00:00Z'), {
      ayanamsa: 'lahiri',
    });
    expect(p.constellation.symbol).toBe('Boo');
    expect(p.constellation.zodiacal).toBe(false);
  });

  it('nel 1991 è nel Serpente (Ser)', () => {
    // Il periodo 1990-2006 citato nel briefing è la lettura a grana
    // grossa: il motore mostra più finestre in Serpente alternate a
    // Bilancia, Ofiuco e Scorpione. Finestra continua verificata:
    // ottobre 1990 - novembre 1991.
    const p = computeBody('Pluto', new Date('1991-01-01T00:00:00Z'), {
      ayanamsa: 'lahiri',
    });
    expect(p.constellation.symbol).toBe('Ser');
    expect(p.constellation.zodiacal).toBe(false);
  });

  it('la proiezione sull\'eclittica avrebbe dato un risultato diverso (1971)', () => {
    // Se si usasse la sola longitudine eclittica (latitudine azzerata),
    // Plutone nel 1971 risulterebbe in una costellazione zodiacale:
    // la determinazione va fatta da RA *e* declinazione reali.
    const p = computeBody('Pluto', new Date('1971-06-01T00:00:00Z'), {
      ayanamsa: 'lahiri',
    });
    expect(Math.abs(p.ecliptic.latitude)).toBeGreaterThan(10);
  });
});

describe('trappola del doppio conteggio della precessione (§3.2)', () => {
  it('una stella fissa resta nella stessa costellazione dal 1700 al 2200', () => {
    // Regolo (alfa Leonis), coordinate J2000: dentro il Leone.
    DefineStar(Body.Star1, 10.13953, 11.96721, 79);
    for (const year of [1700, 1900, 2000, 2100, 2200]) {
      const vec = GeoVector(Body.Star1, new Date(Date.UTC(year, 5, 1)), true);
      const hit = constellationFromVector(vec);
      expect(hit.symbol, `Regolo nel ${year}`).toBe('Leo');
    }
    // Spica (alfa Virginis), J2000: dentro la Vergine.
    DefineStar(Body.Star2, 13.41989, -11.16132, 250);
    for (const year of [1700, 2000, 2200]) {
      const vec = GeoVector(Body.Star2, new Date(Date.UTC(year, 5, 1)), true);
      expect(constellationFromVector(vec).symbol, `Spica nel ${year}`).toBe(
        'Vir',
      );
    }
  });

  it('passare coordinate "of date" sposta il risultato vicino ai confini', () => {
    // La mattina del 30 novembre 2026 il Sole è ancora in Scorpione
    // (l'ingresso in Ofiuco avviene fra le 03 e le 06 UTC). Con le
    // coordinate equatoriali della data (ofdate=true) la precessione
    // viene contata due volte (~0,4° nel 2026) e il Sole risulterebbe già
    // in Ofiuco con circa 9 ore di anticipo: è l'errore che il motore
    // deve evitare.
    const date = new Date('2026-11-30T00:00:00Z');
    const observer = new Observer(0, 0, 0);
    const wrong = Equator(Body.Sun, date, observer, true, true);
    const wrongHit = constellationFromJ2000(wrong.ra, wrong.dec);
    expect(sunConstellationOn(date.toISOString())).toBe('Sco');
    expect(wrongHit.symbol).toBe('Oph');
  });
});
