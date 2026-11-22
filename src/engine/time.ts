/**
 * Risoluzione dei dati di nascita in un istante UTC.
 *
 * - Il fuso orario è risolto dalle coordinate con tz-lookup (offline).
 * - La conversione in UTC usa Luxon con il database IANA, che applica le
 *   regole storiche: ora legale nelle date passate e tempo locale medio
 *   (LMT) per le nascite anteriori all'adozione dei fusi (in Italia il
 *   fuso dell'Europa centrale è in vigore dal 1893; prima Luxon applica
 *   l'offset LMT della zona, es. Roma +00:49:56).
 * - Le date sono interpretate nel calendario GREGORIANO. Il passaggio
 *   giuliano/gregoriano (1582) è fuori dall'intervallo supportato dal
 *   motore (1700–2200), dichiarato in docs/METODO.md.
 */
import { DateTime } from 'luxon';
import tzLookup from 'tz-lookup';
import { SUPPORTED_RANGE } from './types';

export interface BirthDataInput {
  year: number;
  month: number; // 1-12
  day: number; // 1-31
  /** Ora locale 0-23; ignorata se timeKnown è false (si usano le 12:00). */
  hour?: number;
  minute?: number;
  timeKnown: boolean;
  latitude: number;
  longitude: number;
  /** Zona IANA esplicita; se assente è risolta dalle coordinate. */
  zoneOverride?: string;
}

export interface ResolvedBirthTime {
  utc: Date;
  /** Identificatore IANA applicato (es. "Europe/Rome"). */
  zone: string;
  /** Offset applicato, in minuti rispetto a UTC. */
  offsetMinutes: number;
  /** Nome breve dell'offset (es. "GMT+1", "LMT"). */
  offsetLabel: string;
  /** Ora locale effettivamente interpretata (ISO, senza zona). */
  localIso: string;
  /** Calendario di interpretazione della data. */
  calendarUsed: 'gregorian';
  /**
   * true se l'ora locale indicata non esiste (buco dell'ora legale):
   * Luxon la sposta in avanti; l'utente va avvisato.
   */
  adjustedForGap: boolean;
  /** true se l'ora locale è ambigua (ripetuta al ritorno all'ora solare). */
  ambiguous: boolean;
  /** true se la data è fuori dall'intervallo affidabile del motore. */
  outsideSupportedRange: boolean;
  /** Errore bloccante (data inesistente), altrimenti undefined. */
  error?: string;
}

export function resolveZone(latitude: number, longitude: number): string {
  return tzLookup(latitude, longitude);
}

export function resolveBirthTime(input: BirthDataInput): ResolvedBirthTime {
  const zone = input.zoneOverride ?? resolveZone(input.latitude, input.longitude);
  const hour = input.timeKnown ? (input.hour ?? 12) : 12;
  const minute = input.timeKnown ? (input.minute ?? 0) : 0;

  const dt = DateTime.fromObject(
    {
      year: input.year,
      month: input.month,
      day: input.day,
      hour,
      minute,
    },
    { zone },
  );

  if (!dt.isValid) {
    return {
      utc: new Date(NaN),
      zone,
      offsetMinutes: 0,
      offsetLabel: '',
      localIso: '',
      calendarUsed: 'gregorian',
      adjustedForGap: false,
      ambiguous: false,
      outsideSupportedRange: true,
      error: `${dt.invalidReason}: ${dt.invalidExplanation ?? ''}`.trim(),
    };
  }

  // Buco dell'ora legale: l'ora richiesta non esiste e Luxon la sposta.
  const adjustedForGap = dt.hour !== hour || dt.minute !== minute;

  // Ambiguità: al ritorno all'ora solare la stessa ora locale esiste due
  // volte (Luxon sceglie la prima occorrenza). La rileviamo verificando se
  // spostandosi di un'ora fisica in avanti o indietro si ritrova lo stesso
  // orario locale.
  const ambiguous =
    !adjustedForGap &&
    [60, -60].some((minutes) => {
      const c = dt.plus({ minutes });
      return (
        c.day === dt.day && c.hour === dt.hour && c.minute === dt.minute
      );
    });

  const outsideSupportedRange =
    input.year < SUPPORTED_RANGE.minYear || input.year > SUPPORTED_RANGE.maxYear;

  return {
    utc: dt.toUTC().toJSDate(),
    zone,
    offsetMinutes: dt.offset,
    offsetLabel: formatOffset(dt.offset),
    localIso: dt.toISO({ includeOffset: false }) ?? '',
    calendarUsed: 'gregorian',
    adjustedForGap,
    ambiguous,
    outsideSupportedRange,
  };
}

export function formatOffset(minutes: number): string {
  const sign = minutes < 0 ? '-' : '+';
  const abs = Math.abs(minutes);
  const h = Math.floor(abs / 60);
  const m = Math.round(abs % 60);
  return `UTC${sign}${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}
