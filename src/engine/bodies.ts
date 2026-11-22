/**
 * Posizioni geocentriche apparenti dei corpi del sistema solare.
 *
 * Sequenza per ogni corpo (vedi docs/METODO.md):
 *  1. `GeoVector(body, t, true)` → vettore geocentrico apparente EQJ
 *     (equatore medio J2000), con correzione per tempo-luce e aberrazione.
 *  2. `Ecliptic(vec)` → longitudine/latitudine sull'eclittica VERA della data
 *     (sistema ECT): è il riferimento per le viste tropicale e siderale.
 *  3. `EquatorFromVector(vec)` → RA/Dec J2000, da cui `Constellation()`
 *     ricava la costellazione IAU precessando internamente a B1875.
 *  4. Retrogradazione: segno della derivata numerica della longitudine
 *     eclittica su un intervallo di ±6 ore.
 */
import {
  AstroTime,
  Body,
  Ecliptic,
  EquatorFromVector,
  GeoMoonState,
  GeoVector,
  MakeTime,
  RotateVector,
  Rotation_ECT_EQJ,
  Rotation_EQJ_ECT,
  StateVector,
  Vector,
  e_tilt,
} from 'astronomy-engine';
import { constellationFromVector } from './constellations';
import {
  AyanamsaId,
  BodyId,
  BodyPosition,
  degreeInSign,
  normalizeDegrees,
  signOf,
} from './types';
import { ayanamsaDegrees } from './ayanamsa';

export const BODY_ORDER: readonly BodyId[] = [
  'Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn',
  'Uranus', 'Neptune', 'Pluto', 'MeanNode', 'TrueNode',
];

const PLANET_MAP: Partial<Record<BodyId, Body>> = {
  Sun: Body.Sun,
  Moon: Body.Moon,
  Mercury: Body.Mercury,
  Venus: Body.Venus,
  Mars: Body.Mars,
  Jupiter: Body.Jupiter,
  Saturn: Body.Saturn,
  Uranus: Body.Uranus,
  Neptune: Body.Neptune,
  Pluto: Body.Pluto,
};

const DEG = Math.PI / 180;

/** Intervallo della derivata numerica: ±6 ore. */
const SPEED_HALF_STEP_DAYS = 0.25;

export interface RawEclipticState {
  /** Longitudine eclittica vera della data [0, 360). */
  longitude: number;
  latitude: number;
  distanceAu: number;
  /** Vettore geocentrico EQJ da cui derivare RA/Dec J2000. */
  eqjVector: Vector;
}

/** Stato eclittico di un corpo (pianeti e luminari). */
function planetEclipticState(body: Body, time: AstroTime): RawEclipticState {
  const vec = GeoVector(body, time, true);
  const ecl = Ecliptic(vec);
  return {
    longitude: normalizeDegrees(ecl.elon),
    latitude: ecl.elat,
    distanceAu: vec.Length(),
    eqjVector: vec,
  };
}

/**
 * Longitudine del Nodo Lunare Nord MEDIO sull'eclittica vera della data.
 *
 * Polinomio di Meeus (Astronomical Algorithms, 2ª ed., cap. 47) per il nodo
 * medio riferito all'equinozio MEDIO della data, più la nutazione in
 * longitudine (dpsi) per riportarlo all'equinozio vero, coerente con le
 * longitudini degli altri corpi.
 */
export function meanNodeLongitude(time: AstroTime): number {
  const T = time.tt / 36525;
  const omegaMean =
    125.0445479 -
    1934.1362891 * T +
    0.0020754 * T * T +
    (T * T * T) / 467441 -
    (T * T * T * T) / 60616000;
  const dpsiDeg = e_tilt(time).dpsi / 3600;
  return normalizeDegrees(omegaMean + dpsiDeg);
}

/**
 * Longitudine del Nodo Lunare Nord VERO (osculante).
 *
 * Dal vettore di stato geocentrico della Luna (posizione + velocità EQJ),
 * ruotato nel sistema dell'eclittica vera della data: il momento angolare
 * h = r × v definisce il piano orbitale istantaneo; il nodo ascendente è la
 * direzione ẑ × h.
 */
export function trueNodeLongitude(time: AstroTime): number {
  const state = GeoMoonState(time);
  const rot = Rotation_EQJ_ECT(time);
  const r = RotateVector(rot, new Vector(state.x, state.y, state.z, time));
  const v = RotateVector(rot, new Vector(state.vx, state.vy, state.vz, time));
  // h = r × v (piano orbitale istantaneo della Luna)
  const hx = r.y * v.z - r.z * v.y;
  const hy = r.z * v.x - r.x * v.z;
  const hz = r.x * v.y - r.y * v.x;
  // nodo ascendente: n = ẑ × h = (-hy, hx, 0)
  return normalizeDegrees(Math.atan2(hx, -hy) / DEG);
}

/** Stato eclittico di un nodo lunare (punto sull'eclittica: latitudine 0). */
function nodeEclipticState(body: BodyId, time: AstroTime): RawEclipticState {
  const lon =
    body === 'MeanNode' ? meanNodeLongitude(time) : trueNodeLongitude(time);
  // Vettore unitario nel sistema ECT, riportato a EQJ per la costellazione.
  const ect = new Vector(
    Math.cos(lon * DEG),
    Math.sin(lon * DEG),
    0,
    time,
  );
  const eqj = RotateVector(Rotation_ECT_EQJ(time), ect);
  return { longitude: lon, latitude: 0, distanceAu: 0, eqjVector: eqj };
}

export function eclipticState(body: BodyId, time: AstroTime): RawEclipticState {
  const planet = PLANET_MAP[body];
  if (planet !== undefined) return planetEclipticState(planet, time);
  return nodeEclipticState(body, time);
}

/** Solo la longitudine (per derivate e ricerche, senza costi extra). */
export function eclipticLongitude(body: BodyId, time: AstroTime): number {
  return eclipticState(body, time).longitude;
}

/** Differenza angolare con segno, in (-180, 180]. */
export function angularDelta(from: number, to: number): number {
  let d = normalizeDegrees(to) - normalizeDegrees(from);
  if (d > 180) d -= 360;
  if (d <= -180) d += 360;
  return d;
}

/** Velocità in longitudine (gradi/giorno), derivata centrata su ±6 h. */
export function longitudeSpeed(body: BodyId, time: AstroTime): number {
  const before = eclipticLongitude(body, time.AddDays(-SPEED_HALF_STEP_DAYS));
  const after = eclipticLongitude(body, time.AddDays(SPEED_HALF_STEP_DAYS));
  return angularDelta(before, after) / (2 * SPEED_HALF_STEP_DAYS);
}

export interface ComputeBodyOptions {
  ayanamsa: AyanamsaId;
}

export function computeBody(
  body: BodyId,
  date: Date | AstroTime,
  options: ComputeBodyOptions,
): BodyPosition {
  const time = MakeTime(date);
  const state = eclipticState(body, time);
  const eq = EquatorFromVector(state.eqjVector);
  const speed = longitudeSpeed(body, time);
  const ayan = ayanamsaDegrees(options.ayanamsa, time);
  const siderealLongitude = normalizeDegrees(state.longitude - ayan);
  return {
    body,
    ecliptic: {
      longitude: state.longitude,
      latitude: state.latitude,
      distanceAu: state.distanceAu,
    },
    equatorialJ2000: { ra: eq.ra, dec: eq.dec },
    constellation: constellationFromVector(state.eqjVector),
    longitudeSpeed: speed,
    retrograde: speed < 0,
    tropicalSign: signOf(state.longitude),
    tropicalDegree: degreeInSign(state.longitude),
    siderealSign: signOf(siderealLongitude),
    siderealDegree: degreeInSign(siderealLongitude),
    siderealLongitude,
  };
}

export function computeBodies(
  date: Date | AstroTime,
  options: ComputeBodyOptions,
): BodyPosition[] {
  const time = MakeTime(date);
  return BODY_ORDER.map((b) => computeBody(b, time, options));
}

export type { StateVector };
