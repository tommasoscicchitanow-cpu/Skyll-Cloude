/**
 * Ascendente, Medio Cielo e sistemi di case.
 *
 * Tutto è calcolato nei sistemi "veri della data": tempo siderale apparente
 * di Greenwich (`SiderealTime`), obliquità vera (`e_tilt().tobl`), equatore
 * vero (EQD) ed eclittica vera (ECT). L'Ascendente è ottenuto come
 * intersezione fra piano dell'orizzonte e piano dell'eclittica (ramo
 * orientale), il Medio Cielo come punto dell'eclittica sul meridiano
 * superiore (angolo orario nullo). La geometria vettoriale evita ambiguità
 * di quadrante delle formule in tangente e rende riconoscibile il caso
 * degenere polare (orizzonte quasi parallelo all'eclittica).
 */
import {
  AstroTime,
  MakeTime,
  RotateVector,
  Rotation_EQD_EQJ,
  SiderealTime,
  Vector,
  e_tilt,
} from 'astronomy-engine';
import { constellationFromVector } from './constellations';
import { ayanamsaDegrees } from './ayanamsa';
import {
  AnglesResult,
  AyanamsaId,
  HouseSystemId,
  HousesResult,
  PointId,
  PointPosition,
  degreeInSign,
  normalizeDegrees,
  signOf,
} from './types';
import { EquatorFromVector } from 'astronomy-engine';

const DEG = Math.PI / 180;

/** Oltre questa latitudine il risultato va mostrato con l'avvertenza polare. */
export const POLAR_WARNING_LATITUDE = 66;

/** Sotto questo seno dell'angolo fra i piani il calcolo è degenere. */
const DEGENERATE_SIN_THRESHOLD = 1e-6;

export interface AnglesRaw {
  /** Longitudine eclittica (ECT) dell'Ascendente, gradi [0, 360). */
  ascendant: number;
  /** Longitudine eclittica (ECT) del Medio Cielo, gradi [0, 360). */
  midheaven: number;
  /** Tempo siderale locale apparente in gradi [0, 360) (RAMC). */
  ramc: number;
  /** Obliquità vera della data in gradi. */
  obliquity: number;
  degenerate: boolean;
}

/**
 * Ascendente e Medio Cielo in longitudine eclittica vera della data.
 *
 * @param latitude  Latitudine geografica in gradi (+N).
 * @param longitude Longitudine geografica in gradi (+E).
 */
export function computeAnglesRaw(
  date: Date | AstroTime,
  latitude: number,
  longitude: number,
): AnglesRaw {
  const time = MakeTime(date);
  const gastHours = SiderealTime(time);
  const ramc = normalizeDegrees(gastHours * 15 + longitude);
  const eps = e_tilt(time).tobl;

  const theta = ramc * DEG;
  const phi = latitude * DEG;
  const epsR = eps * DEG;

  // Medio Cielo: punto dell'eclittica con angolo orario nullo (RA = RAMC).
  const mc = normalizeDegrees(
    Math.atan2(Math.sin(theta), Math.cos(theta) * Math.cos(epsR)) / DEG,
  );

  // Sistema EQD (equatore vero della data, x = equinozio vero).
  // Zenit dell'osservatore:
  const zenith = [
    Math.cos(phi) * Math.cos(theta),
    Math.cos(phi) * Math.sin(theta),
    Math.sin(phi),
  ] as const;
  // Normale all'eclittica (polo nord eclittico) in EQD:
  const eclPole = [0, -Math.sin(epsR), Math.cos(epsR)] as const;

  // Intersezione dei due piani: d = zenit × poloEclittico.
  const d = [
    zenith[1] * eclPole[2] - zenith[2] * eclPole[1],
    zenith[2] * eclPole[0] - zenith[0] * eclPole[2],
    zenith[0] * eclPole[1] - zenith[1] * eclPole[0],
  ];
  const dLen = Math.hypot(d[0]!, d[1]!, d[2]!);
  const degenerate = dLen < DEGENERATE_SIN_THRESHOLD;

  let asc = Number.NaN;
  if (!degenerate) {
    // Direzione est dell'osservatore: ê = ẑ(polo celeste) × zenit.
    const east = [
      -zenith[1],
      zenith[0],
      0,
    ];
    let dx = d[0]! / dLen;
    let dy = d[1]! / dLen;
    let dz = d[2]! / dLen;
    const dotEast = dx * east[0]! + dy * east[1]! + dz * east[2]!;
    if (dotEast < 0) {
      dx = -dx;
      dy = -dy;
      dz = -dz;
    }
    // Da EQD a ECT: rotazione di ε attorno all'asse x.
    const ectY = dy * Math.cos(epsR) + dz * Math.sin(epsR);
    asc = normalizeDegrees(Math.atan2(ectY, dx) / DEG);
  }

  return { ascendant: asc, midheaven: mc, ramc, obliquity: eps, degenerate };
}

function pointPosition(
  point: PointId,
  longitudeEcl: number,
  time: AstroTime,
  ayanamsa: AyanamsaId,
): PointPosition {
  // Vettore ECT del punto, riportato in EQJ per la costellazione IAU.
  const ect = new Vector(
    Math.cos(longitudeEcl * DEG),
    Math.sin(longitudeEcl * DEG),
    0,
    time,
  );
  // ECT → EQD → EQJ (l'asse x di ECT è l'equinozio vero, come EQD).
  const epsR = e_tilt(time).tobl * DEG;
  const eqd = new Vector(
    ect.x,
    ect.y * Math.cos(epsR) - ect.z * Math.sin(epsR),
    ect.y * Math.sin(epsR) + ect.z * Math.cos(epsR),
    time,
  );
  const eqj = RotateVector(Rotation_EQD_EQJ(time), eqd);
  const eq = EquatorFromVector(eqj);
  const ayan = ayanamsaDegrees(ayanamsa, time);
  const sid = normalizeDegrees(longitudeEcl - ayan);
  return {
    point,
    ecliptic: { longitude: longitudeEcl, latitude: 0, distanceAu: 0 },
    equatorialJ2000: { ra: eq.ra, dec: eq.dec },
    constellation: constellationFromVector(eqj),
    tropicalSign: signOf(longitudeEcl),
    tropicalDegree: degreeInSign(longitudeEcl),
    siderealSign: signOf(sid),
    siderealDegree: degreeInSign(sid),
    siderealLongitude: sid,
  };
}

export function computeAngles(
  date: Date | AstroTime,
  latitude: number,
  longitude: number,
  ayanamsa: AyanamsaId,
): AnglesResult {
  const time = MakeTime(date);
  const raw = computeAnglesRaw(time, latitude, longitude);
  return {
    ascendant: pointPosition('Ascendant', raw.ascendant, time, ayanamsa),
    midheaven: pointPosition('Midheaven', raw.midheaven, time, ayanamsa),
    degenerate: raw.degenerate,
  };
}

/**
 * Contesto passato ai sistemi di case. Contiene già tutto ciò che serve
 * anche ai sistemi quadranti della fase 2 (Placidus, Koch, Campanus),
 * così da poterli aggiungere senza cambiare la firma.
 */
export interface HouseContext {
  /** Longitudine dell'Ascendente NEL sistema di riferimento richiesto
   *  (tropicale o siderale: per il siderale sottrarre prima l'ayanamsa). */
  ascendant: number;
  /** Longitudine del Medio Cielo nello stesso sistema. */
  midheaven: number;
  ramc: number;
  obliquity: number;
  latitude: number;
}

type HouseFn = (ctx: HouseContext) => number[];

const HOUSE_SYSTEMS: Record<HouseSystemId, HouseFn> = {
  'whole-sign': (ctx) => {
    const start = 30 * Math.floor(normalizeDegrees(ctx.ascendant) / 30);
    return Array.from({ length: 12 }, (_, i) =>
      normalizeDegrees(start + 30 * i),
    );
  },
  equal: (ctx) =>
    Array.from({ length: 12 }, (_, i) =>
      normalizeDegrees(ctx.ascendant + 30 * i),
    ),
};

export function houseCusps(
  system: HouseSystemId,
  ctx: HouseContext,
): HousesResult {
  const fn = HOUSE_SYSTEMS[system];
  return { system, cusps: fn(ctx) };
}

export const AVAILABLE_HOUSE_SYSTEMS: readonly HouseSystemId[] = [
  'whole-sign',
  'equal',
];
