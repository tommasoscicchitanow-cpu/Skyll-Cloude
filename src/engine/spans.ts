/**
 * Ampiezze reali delle costellazioni: finestre di transito del Sole.
 *
 * Le date di ingresso e uscita del Sole da ogni costellazione IAU sono
 * CALCOLATE a runtime per l'anno richiesto — mai scritte come costanti —
 * campionando la posizione del Sole e raffinando ogni attraversamento di
 * confine con una bisezione precisa al minuto. I valori che circolano
 * online sono spesso approssimativi, e cambiano lentamente per precessione.
 */
import { AstroTime, Body, GeoVector, MakeTime } from 'astronomy-engine';
import { constellationFromVector } from './constellations';
import { CONSTELLATION_NAMES_IT } from './constellations';
import type { TransitSpan } from './types';

function sunConstellation(time: AstroTime): string {
  const vec = GeoVector(Body.Sun, time, true);
  return constellationFromVector(vec).symbol;
}

/** Bisezione dell'istante di cambio costellazione fra t0 e t1 (< 1 minuto). */
function bisectBoundary(t0: AstroTime, t1: AstroTime): AstroTime {
  const from = sunConstellation(t0);
  let lo = t0;
  let hi = t1;
  const minuteDays = 1 / 1440;
  while (hi.ut - lo.ut > minuteDays / 2) {
    const mid = MakeTime(lo.ut + (hi.ut - lo.ut) / 2);
    if (sunConstellation(mid) === from) lo = mid;
    else hi = mid;
  }
  return hi;
}

export interface SolarSpanOptions {
  /** Passo di campionamento in giorni (default 1). */
  sampleStepDays?: number;
}

/**
 * Finestre di permanenza del Sole nelle costellazioni IAU per l'anno civile
 * indicato (UTC). La prima e l'ultima finestra sono troncate ai bordi
 * dell'anno solo se `clipToYear` è true; di default si estendono agli
 * istanti reali di ingresso/uscita anche se cadono nell'anno adiacente.
 */
export function solarConstellationSpans(
  year: number,
  options: SolarSpanOptions = {},
): TransitSpan[] {
  const step = options.sampleStepDays ?? 1;
  const start = MakeTime(new Date(Date.UTC(year, 0, 1)));
  const end = MakeTime(new Date(Date.UTC(year + 1, 0, 1)));

  // Campionamento: elenco di (istante, costellazione).
  const boundaries: { crossing: AstroTime; to: string }[] = [];
  let prevTime = start;
  let prevConst = sunConstellation(start);
  const firstConst = prevConst;
  for (let ut = start.ut + step; ; ut = Math.min(ut + step, end.ut)) {
    const t = MakeTime(Math.min(ut, end.ut));
    const c = sunConstellation(t);
    if (c !== prevConst) {
      const crossing = bisectBoundary(prevTime, t);
      boundaries.push({ crossing, to: c });
      prevConst = c;
    }
    prevTime = t;
    if (t.ut >= end.ut) break;
  }

  // Estendi all'indietro fino all'ingresso reale nella prima costellazione.
  let firstEnter = start;
  {
    let t = start;
    const back = 40; // giorni massimi di ricerca all'indietro
    let found = false;
    for (let i = 1; i <= back; i++) {
      const prev = MakeTime(start.ut - i * step);
      if (sunConstellation(prev) !== firstConst) {
        firstEnter = bisectBoundary(prev, t);
        found = true;
        break;
      }
      t = prev;
    }
    if (!found) firstEnter = start; // non dovrebbe accadere: Sole < 45gg/cost.
  }

  // Estendi in avanti fino all'uscita reale dall'ultima costellazione.
  const lastConst = prevConst;
  let lastExit = end;
  {
    let t = end;
    const fwd = 40;
    let found = false;
    for (let i = 1; i <= fwd; i++) {
      const next = MakeTime(end.ut + i * step);
      if (sunConstellation(next) !== lastConst) {
        lastExit = bisectBoundary(t, next);
        found = true;
        break;
      }
      t = next;
    }
    if (!found) lastExit = end;
  }

  // Componi le finestre.
  const spans: TransitSpan[] = [];
  let enter = firstEnter;
  let current = firstConst;
  for (const b of boundaries) {
    spans.push(makeSpan(current, enter, b.crossing));
    current = b.to;
    enter = b.crossing;
  }
  spans.push(makeSpan(current, enter, lastExit));
  return spans;
}

function makeSpan(
  symbol: string,
  enter: AstroTime,
  exit: AstroTime,
): TransitSpan {
  return {
    key: symbol,
    label: CONSTELLATION_NAMES_IT[symbol] ?? symbol,
    enterUtc: enter.date.toISOString(),
    exitUtc: exit.date.toISOString(),
    days: exit.ut - enter.ut,
  };
}
