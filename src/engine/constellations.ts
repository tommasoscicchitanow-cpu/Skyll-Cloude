/**
 * Determinazione della costellazione IAU in cui cade un punto del cielo.
 *
 * PUNTO CRITICO (vedi docs/METODO.md): `Astronomy.Constellation()` richiede
 * coordinate equatoriali J2000 e applica internamente la precessione a B1875,
 * l'epoca dei confini fissati dalla IAU nel 1930 (delimitazione di Delporte).
 * Le coordinate vanno quindi ricavate dal vettore EQJ con
 * `EquatorFromVector()`, MAI da `Equator(..., ofdate=true)`: passare
 * coordinate "of date" introduce un doppio conteggio della precessione
 * (~0,4° nel 2026, crescente), sufficiente a sbagliare costellazione vicino
 * ai confini. Il test tests/engine/constellations.test.ts copre il caso.
 */
import { Constellation, EquatorFromVector, Vector } from 'astronomy-engine';
import type { ConstellationHit } from './types';

/** Le 13 costellazioni attraversate dall'eclittica (fascia zodiacale IAU). */
export const ZODIACAL_BAND: readonly string[] = [
  'Ari', 'Tau', 'Gem', 'Cnc', 'Leo', 'Vir', 'Lib', 'Sco', 'Oph', 'Sgr',
  'Cap', 'Aqr', 'Psc',
];

/** Nomi italiani delle 88 costellazioni IAU, indicizzati per sigla. */
export const CONSTELLATION_NAMES_IT: Record<string, string> = {
  And: 'Andromeda', Ant: 'Macchina Pneumatica', Aps: 'Uccello del Paradiso',
  Aqr: 'Acquario', Aql: 'Aquila', Ara: 'Altare', Ari: 'Ariete',
  Aur: 'Auriga', Boo: 'Boote', Cae: 'Bulino', Cam: 'Giraffa',
  Cnc: 'Cancro', CVn: 'Cani da Caccia', CMa: 'Cane Maggiore',
  CMi: 'Cane Minore', Cap: 'Capricorno', Car: 'Carena', Cas: 'Cassiopea',
  Cen: 'Centauro', Cep: 'Cefeo', Cet: 'Balena', Cha: 'Camaleonte',
  Cir: 'Compasso', Col: 'Colomba', Com: 'Chioma di Berenice',
  CrA: 'Corona Australe', CrB: 'Corona Boreale', Crv: 'Corvo',
  Crt: 'Coppa', Cru: 'Croce del Sud', Cyg: 'Cigno', Del: 'Delfino',
  Dor: 'Dorado', Dra: 'Drago', Equ: 'Cavallino', Eri: 'Eridano',
  For: 'Fornace', Gem: 'Gemelli', Gru: 'Gru', Her: 'Ercole',
  Hor: 'Orologio', Hya: 'Idra', Hyi: 'Idra Australe', Ind: 'Indiano',
  Lac: 'Lucertola', Leo: 'Leone', LMi: 'Leone Minore', Lep: 'Lepre',
  Lib: 'Bilancia', Lup: 'Lupo', Lyn: 'Lince', Lyr: 'Lira',
  Men: 'Mensa', Mic: 'Microscopio', Mon: 'Unicorno', Mus: 'Mosca',
  Nor: 'Regolo', Oct: 'Ottante', Oph: 'Ofiuco', Ori: 'Orione',
  Pav: 'Pavone', Peg: 'Pegaso', Per: 'Perseo', Phe: 'Fenice',
  Pic: 'Pittore', Psc: 'Pesci', PsA: 'Pesce Australe', Pup: 'Poppa',
  Pyx: 'Bussola', Ret: 'Reticolo', Sge: 'Freccia', Sgr: 'Sagittario',
  Sco: 'Scorpione', Scl: 'Scultore', Sct: 'Scudo', Ser: 'Serpente',
  Sex: 'Sestante', Tau: 'Toro', Tel: 'Telescopio', Tri: 'Triangolo',
  TrA: 'Triangolo Australe', Tuc: 'Tucano', UMa: 'Orsa Maggiore',
  UMi: 'Orsa Minore', Vel: 'Vele', Vir: 'Vergine', Vol: 'Pesce Volante',
  Vul: 'Volpetta',
};

/**
 * Costellazione IAU del punto individuato da un vettore geocentrico EQJ
 * (equatore medio J2000), come restituito da `GeoVector`.
 */
export function constellationFromVector(vec: Vector): ConstellationHit {
  const eq = EquatorFromVector(vec);
  return constellationFromJ2000(eq.ra, eq.dec);
}

/**
 * Costellazione IAU da ascensione retta (ore) e declinazione (gradi) J2000.
 */
export function constellationFromJ2000(
  raHours: number,
  decDegrees: number,
): ConstellationHit {
  const info = Constellation(raHours, decDegrees);
  return {
    symbol: info.symbol,
    latinName: info.name,
    italianName: CONSTELLATION_NAMES_IT[info.symbol] ?? info.name,
    zodiacal: ZODIACAL_BAND.includes(info.symbol),
  };
}
