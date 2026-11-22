/**
 * Tipi condivisi del motore astronomico.
 *
 * Il motore è un modulo puro: nessuna dipendenza da React o dal DOM.
 * Tutte le longitudini eclittiche sono riferite all'eclittica VERA della data
 * (true ecliptic of date), in gradi [0, 360).
 */

/** Corpi calcolati dal motore. */
export type BodyId =
  | 'Sun'
  | 'Moon'
  | 'Mercury'
  | 'Venus'
  | 'Mars'
  | 'Jupiter'
  | 'Saturn'
  | 'Uranus'
  | 'Neptune'
  | 'Pluto'
  | 'MeanNode'
  | 'TrueNode';

/** Punti derivati dal luogo e dall'ora (richiedono ora di nascita nota). */
export type PointId = 'Ascendant' | 'Midheaven';

/** I dodici segni, indice 0 = Ariete. */
export type SignIndex = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11;

export interface EclipticPosition {
  /** Longitudine eclittica vera della data, gradi [0, 360). */
  longitude: number;
  /** Latitudine eclittica, gradi. */
  latitude: number;
  /** Distanza geocentrica in UA (0 per i punti geometrici). */
  distanceAu: number;
}

export interface EquatorialJ2000 {
  /** Ascensione retta J2000 in ore [0, 24). */
  ra: number;
  /** Declinazione J2000 in gradi. */
  dec: number;
}

export interface ConstellationHit {
  /** Sigla IAU a tre lettere (es. "Oph"). */
  symbol: string;
  /** Nome latino ufficiale IAU. */
  latinName: string;
  /** Nome italiano. */
  italianName: string;
  /** true se appartiene alla fascia delle 13 costellazioni zodiacali. */
  zodiacal: boolean;
}

export interface BodyPosition {
  body: BodyId;
  ecliptic: EclipticPosition;
  equatorialJ2000: EquatorialJ2000;
  constellation: ConstellationHit;
  /** Velocità in longitudine, gradi/giorno (derivata numerica ±6 h). */
  longitudeSpeed: number;
  retrograde: boolean;
  /** Segno tropicale (0 = Ariete). */
  tropicalSign: SignIndex;
  /** Gradi entro il segno tropicale [0, 30). */
  tropicalDegree: number;
  /** Segno siderale secondo l'ayanamsa scelto. */
  siderealSign: SignIndex;
  /** Gradi entro il segno siderale [0, 30). */
  siderealDegree: number;
  /** Longitudine siderale [0, 360). */
  siderealLongitude: number;
}

export type AyanamsaId = 'lahiri' | 'fagan-bradley';

export interface AnglesResult {
  ascendant: PointPosition;
  midheaven: PointPosition;
  /**
   * true quando il calcolo è degenerato (latitudini polari in cui l'eclittica
   * non interseca l'orizzonte in modo convenzionale). In quel caso i valori
   * vanno mostrati con l'avvertenza, non nascosti.
   */
  degenerate: boolean;
}

export interface PointPosition {
  point: PointId;
  ecliptic: EclipticPosition;
  equatorialJ2000: EquatorialJ2000;
  constellation: ConstellationHit;
  tropicalSign: SignIndex;
  tropicalDegree: number;
  siderealSign: SignIndex;
  siderealDegree: number;
  siderealLongitude: number;
}

export type HouseSystemId = 'whole-sign' | 'equal';

export interface HousesResult {
  system: HouseSystemId;
  /** Cuspidi 1..12 in longitudine eclittica tropicale, gradi [0, 360). */
  cusps: number[];
}

export type AspectType =
  | 'conjunction'
  | 'sextile'
  | 'square'
  | 'trine'
  | 'opposition';

export interface AspectHit {
  a: BodyId;
  b: BodyId;
  type: AspectType;
  /** Angolo esatto dell'aspetto in gradi (0, 60, 90, 120, 180). */
  exactAngle: number;
  /** Separazione angolare effettiva in gradi. */
  separation: number;
  /** Scarto dall'aspetto esatto in gradi (sempre >= 0). */
  orb: number;
}

export interface AspectOrbs {
  conjunction: number;
  sextile: number;
  square: number;
  trine: number;
  opposition: number;
}

/** Finestra di permanenza del Sole in una costellazione o in un segno. */
export interface TransitSpan {
  /** Sigla IAU o indice del segno, secondo la modalità. */
  key: string;
  label: string;
  /** Istanti UTC ISO di ingresso e uscita, precisi al minuto. */
  enterUtc: string;
  exitUtc: string;
  /** Durata in giorni. */
  days: number;
}

export interface ChartInput {
  /** Istante UTC dell'evento, già risolto dal modulo time. */
  utc: Date;
  /** Latitudine geografica in gradi (+N). */
  latitude: number;
  /** Longitudine geografica in gradi (+E). */
  longitude: number;
  /** Ora di nascita nota? Se false, niente Ascendente/MC/case. */
  timeKnown: boolean;
  ayanamsa: AyanamsaId;
  orbs?: Partial<AspectOrbs>;
}

export interface ChartWarning {
  code:
    | 'outside-supported-range'
    | 'polar-degenerate-angles'
    | 'time-unknown';
  message: string;
}

export interface Chart {
  input: ChartInput;
  bodies: BodyPosition[];
  angles: AnglesResult | null;
  houses: HousesResult[] | null;
  aspects: AspectHit[];
  /** Valore dell'ayanamsa applicato, in gradi. */
  ayanamsaDegrees: number;
  warnings: ChartWarning[];
  /** Escursione della Luna nella giornata, se l'ora è ignota. */
  moonDailyRange?: { minLongitude: number; maxLongitude: number };
}

/** Intervallo di date dichiarato affidabile (vedi docs/METODO.md). */
export const SUPPORTED_RANGE = { minYear: 1700, maxYear: 2200 } as const;

export const SIGN_NAMES_IT = [
  'Ariete',
  'Toro',
  'Gemelli',
  'Cancro',
  'Leone',
  'Vergine',
  'Bilancia',
  'Scorpione',
  'Sagittario',
  'Capricorno',
  'Acquario',
  'Pesci',
] as const;

export function normalizeDegrees(d: number): number {
  const r = d % 360;
  return r < 0 ? r + 360 : r;
}

export function signOf(longitude: number): SignIndex {
  return (Math.floor(normalizeDegrees(longitude) / 30) % 12) as SignIndex;
}

export function degreeInSign(longitude: number): number {
  return normalizeDegrees(longitude) % 30;
}
