/**
 * Orchestrazione: dall'istante UTC risolto alla carta completa.
 */
import { MakeTime } from 'astronomy-engine';
import { computeBodies, eclipticLongitude } from './bodies';
import { computeAngles, computeAnglesRaw, houseCusps, AVAILABLE_HOUSE_SYSTEMS, POLAR_WARNING_LATITUDE } from './houses';
import { computeAspects } from './aspects';
import { ayanamsaDegrees } from './ayanamsa';
import {
  Chart,
  ChartInput,
  ChartWarning,
  SUPPORTED_RANGE,
  normalizeDegrees,
} from './types';

export function computeChart(input: ChartInput): Chart {
  const time = MakeTime(input.utc);
  const warnings: ChartWarning[] = [];

  const year = input.utc.getUTCFullYear();
  if (year < SUPPORTED_RANGE.minYear || year > SUPPORTED_RANGE.maxYear) {
    warnings.push({
      code: 'outside-supported-range',
      message:
        `La data è fuori dall'intervallo affidabile del motore ` +
        `(${SUPPORTED_RANGE.minYear}–${SUPPORTED_RANGE.maxYear}): ` +
        `le posizioni non vengono calcolate.`,
    });
    return {
      input,
      bodies: [],
      angles: null,
      houses: null,
      aspects: [],
      ayanamsaDegrees: Number.NaN,
      warnings,
    };
  }

  const bodies = computeBodies(time, { ayanamsa: input.ayanamsa });
  const ayan = ayanamsaDegrees(input.ayanamsa, time);

  let angles = null;
  let houses = null;
  let moonDailyRange: Chart['moonDailyRange'];

  if (input.timeKnown) {
    angles = computeAngles(time, input.latitude, input.longitude, input.ayanamsa);
    if (angles.degenerate || Math.abs(input.latitude) > POLAR_WARNING_LATITUDE) {
      warnings.push({
        code: 'polar-degenerate-angles',
        message:
          'Alle latitudini polari l\'eclittica può non intersecare ' +
          'l\'orizzonte in modo convenzionale: Ascendente e case vanno ' +
          'letti con cautela.',
      });
    }
    if (!angles.degenerate) {
      const raw = computeAnglesRaw(time, input.latitude, input.longitude);
      houses = AVAILABLE_HOUSE_SYSTEMS.map((system) =>
        houseCusps(system, {
          ascendant: raw.ascendant,
          midheaven: raw.midheaven,
          ramc: raw.ramc,
          obliquity: raw.obliquity,
          latitude: input.latitude,
        }),
      );
    }
  } else {
    warnings.push({
      code: 'time-unknown',
      message:
        'Ora di nascita ignota: calcolo sulle 12:00 locali. Ascendente, ' +
        'Medio Cielo e case sono disattivati; la posizione della Luna può ' +
        'variare sensibilmente nell\'arco della giornata.',
    });
    // Escursione della Luna nelle 24 ore della giornata (UTC ±12 h).
    const lonStart = eclipticLongitude('Moon', time.AddDays(-0.5));
    const lonEnd = eclipticLongitude('Moon', time.AddDays(0.5));
    moonDailyRange = {
      minLongitude: normalizeDegrees(lonStart),
      maxLongitude: normalizeDegrees(lonEnd),
    };
  }

  const aspects = computeAspects(
    bodies
      .filter((b) => b.body !== 'MeanNode') // un solo nodo negli aspetti
      .map((b) => ({ body: b.body, longitude: b.ecliptic.longitude })),
    input.orbs,
  );

  return {
    input,
    bodies,
    angles,
    houses,
    aspects,
    ayanamsaDegrees: ayan,
    warnings,
    moonDailyRange,
  };
}
