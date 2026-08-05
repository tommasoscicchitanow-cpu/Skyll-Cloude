declare module 'tz-lookup' {
  /**
   * Risolve latitudine/longitudine in un identificatore di zona IANA
   * (es. "Europe/Rome"). Lancia un errore per coordinate fuori intervallo.
   */
  export default function tzLookup(latitude: number, longitude: number): string;
}
