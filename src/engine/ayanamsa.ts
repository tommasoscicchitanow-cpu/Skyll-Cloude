/**
 * Ayanamsa: scarto fra zodiaco tropicale e zodiaco siderale.
 *
 * Definizione: longitudine_siderale = longitudine_tropicale − ayanamsa.
 *
 * Implementazione ad ancoraggio: per ogni sistema è fissato un istante t0 e
 * il valore dell'ayanamsa in t0 (parametri standard, gli stessi usati da
 * Swiss Ephemeris e documentati in letteratura):
 *
 *  - Lahiri / Chitrapaksha: 23°15′00.658″ al 21 marzo 1956, 00:00
 *    (JD 2435553.5) — valore definito dall'Indian Calendar Reform Committee
 *    e adottato dall'Indian Astronomical Ephemeris.
 *  - Fagan-Bradley: 24°02′31.36″ al 1 gennaio 1950, 00:00 (JD 2433282.5).
 *
 * L'accumulo di precessione fra t0 e la data richiesta è misurato con le
 * matrici di rotazione di astronomy-engine: si prende la direzione fissa
 * dell'equinozio J2000 (asse x del sistema EQJ) e se ne calcola la
 * longitudine sull'eclittica vera della data; la differenza fra le due
 * epoche è la precessione generale in longitudine maturata nel frattempo
 * (~50,29″/anno). Poiché si usa l'eclittica VERA (nutazione inclusa),
 * lo scarto rispetto ai valori pubblicati su equinozio medio è al massimo
 * di ±18″, sotto la precisione dichiarata dell'app (1′).
 */
import {
  AstroTime,
  MakeTime,
  RotateVector,
  Rotation_EQJ_ECT,
  Vector,
} from 'astronomy-engine';
import { AyanamsaId, normalizeDegrees } from './types';

interface AyanamsaAnchor {
  /** Istante di ancoraggio (UTC; la differenza UT/TT è irrilevante qui). */
  anchorUtc: Date;
  /** Valore dell'ayanamsa all'ancoraggio, in gradi. */
  anchorDegrees: number;
  labelIt: string;
  source: string;
}

export const AYANAMSA_ANCHORS: Record<AyanamsaId, AyanamsaAnchor> = {
  lahiri: {
    anchorUtc: new Date(Date.UTC(1956, 2, 21, 0, 0, 0)),
    anchorDegrees: 23 + 15 / 60 + 0.658 / 3600,
    labelIt: 'Lahiri (Chitrapaksha)',
    source:
      'Indian Astronomical Ephemeris (Calendar Reform Committee, 1955): ' +
      'ayanamsa 23°15′00.658″ al 21/03/1956.',
  },
  'fagan-bradley': {
    anchorUtc: new Date(Date.UTC(1950, 0, 1, 0, 0, 0)),
    anchorDegrees: 24 + 2 / 60 + 31.36 / 3600,
    labelIt: 'Fagan-Bradley',
    source:
      'Fagan & Bradley, ayanamsa 24°02′31.36″ al 01/01/1950 ' +
      '(parametri standard, cfr. Swiss Ephemeris, sistema siderale n. 0).',
  },
};

/**
 * Longitudine, sull'eclittica vera della data, della direzione fissa
 * dell'equinozio J2000. Cresce nel tempo al ritmo della precessione
 * generale in longitudine.
 */
function fixedDirectionLongitude(time: AstroTime): number {
  const xJ2000 = new Vector(1, 0, 0, time);
  const ect = RotateVector(Rotation_EQJ_ECT(time), xJ2000);
  return Math.atan2(ect.y, ect.x) * (180 / Math.PI);
}

/**
 * Differenza di longitudine accumulata fra due istanti, senza ambiguità di
 * giro completo nell'intervallo supportato (1700–2200: al massimo ~7°).
 */
function accumulatedPrecession(from: AstroTime, to: AstroTime): number {
  let d = fixedDirectionLongitude(to) - fixedDirectionLongitude(from);
  while (d > 180) d -= 360;
  while (d < -180) d += 360;
  return d;
}

/** Valore dell'ayanamsa in gradi per il sistema scelto alla data richiesta. */
export function ayanamsaDegrees(
  system: AyanamsaId,
  date: Date | AstroTime,
): number {
  const anchor = AYANAMSA_ANCHORS[system];
  const t = MakeTime(date);
  const t0 = MakeTime(anchor.anchorUtc);
  return normalizeDegrees(
    anchor.anchorDegrees + accumulatedPrecession(t0, t),
  ) % 360;
}
