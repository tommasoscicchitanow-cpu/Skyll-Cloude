/**
 * Stampa testuale della carta per una data di prova (fase 1, §11).
 *
 * Uso:
 *   npm run chart -- --date 1990-05-10 --time 16:30 --lat 41.9 --lon 12.5
 *   npm run chart                        (usa la data di prova di default)
 *   npm run chart -- --no-time           (ora ignota)
 *   npm run chart -- --spans 2026        (tabella ampiezze costellazioni)
 */
import {
  computeChart,
  resolveBirthTime,
  solarConstellationSpans,
  formatOffset,
  SIGN_NAMES_IT,
  AYANAMSA_ANCHORS,
  type AyanamsaId,
  type BodyPosition,
  type PointPosition,
} from '../src/engine';

const BODY_LABELS: Record<string, string> = {
  Sun: 'Sole', Moon: 'Luna', Mercury: 'Mercurio', Venus: 'Venere',
  Mars: 'Marte', Jupiter: 'Giove', Saturn: 'Saturno', Uranus: 'Urano',
  Neptune: 'Nettuno', Pluto: 'Plutone', MeanNode: 'Nodo Nord (medio)',
  TrueNode: 'Nodo Nord (vero)', Ascendant: 'Ascendente',
  Midheaven: 'Medio Cielo',
};

function arg(name: string): string | undefined {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 ? process.argv[i + 1] : undefined;
}

function has(name: string): boolean {
  return process.argv.includes(`--${name}`);
}

function fmtDeg(deg: number): string {
  const d = Math.floor(deg);
  const m = Math.round((deg - d) * 60);
  return `${String(d).padStart(2, '0')}°${String(m).padStart(2, '0')}′`;
}

function fmtLon(deg: number): string {
  const sign = SIGN_NAMES_IT[Math.floor(deg / 30) % 12];
  return `${fmtDeg(deg % 30)} ${sign}`;
}

function row(p: BodyPosition | PointPosition, retro = ''): string {
  const label = (BODY_LABELS[('body' in p ? p.body : p.point)] ?? '').padEnd(18);
  const trop = fmtLon(p.ecliptic.longitude).padEnd(19);
  const sid = fmtLon(p.siderealLongitude).padEnd(19);
  const iau = `${p.constellation.italianName} (${p.constellation.symbol})`;
  return `  ${label}${trop}${sid}${iau}${retro}`;
}

const spansYear = arg('spans');
if (spansYear) {
  const year = Number(spansYear);
  console.log(`\nFinestre di transito del Sole nelle costellazioni IAU, ${year}\n`);
  for (const s of solarConstellationSpans(year)) {
    const bar = '█'.repeat(Math.max(1, Math.round(s.days / 2)));
    console.log(
      `  ${s.label.padEnd(22)}${s.enterUtc.slice(0, 10)} → ${s.exitUtc.slice(0, 10)}  ` +
      `${s.days.toFixed(1).padStart(5)} gg  ${bar}`,
    );
  }
  process.exit(0);
}

const date = arg('date') ?? '1990-05-10';
const time = arg('time') ?? '16:30';
const lat = Number(arg('lat') ?? 41.9);
const lon = Number(arg('lon') ?? 12.5);
const timeKnown = !has('no-time');
const ayanamsa = (arg('ayanamsa') ?? 'lahiri') as AyanamsaId;

const [y, mo, d] = date.split('-').map(Number);
const [h, mi] = time.split(':').map(Number);

const resolved = resolveBirthTime({
  year: y!, month: mo!, day: d!, hour: h, minute: mi,
  timeKnown, latitude: lat, longitude: lon,
});

if (resolved.error) {
  console.error(`Data non valida: ${resolved.error}`);
  process.exit(1);
}

console.log(`\nDati di nascita`);
console.log(`  Locale:  ${resolved.localIso}  (${resolved.zone}, ${formatOffset(resolved.offsetMinutes)})`);
console.log(`  UTC:     ${resolved.utc.toISOString()}`);
console.log(`  Luogo:   lat ${lat}, lon ${lon}`);

const chart = computeChart({
  utc: resolved.utc, latitude: lat, longitude: lon, timeKnown, ayanamsa,
});

for (const w of chart.warnings) console.log(`  ⚠ ${w.message}`);
if (chart.bodies.length === 0) process.exit(1);

console.log(`\nAyanamsa ${AYANAMSA_ANCHORS[ayanamsa].labelIt}: ${fmtDeg(chart.ayanamsaDegrees)}`);
console.log(`\n  ${'Corpo'.padEnd(18)}${'Tropicale'.padEnd(19)}${'Siderale'.padEnd(19)}Costellazione IAU`);
console.log('  ' + '-'.repeat(76));
for (const b of chart.bodies) {
  console.log(row(b, b.retrograde ? '  ℞' : ''));
}
if (chart.angles) {
  console.log(row(chart.angles.ascendant));
  console.log(row(chart.angles.midheaven));
}

if (chart.houses) {
  console.log(`\nCase (cuspidi tropicali)`);
  for (const hs of chart.houses) {
    console.log(
      `  ${hs.system.padEnd(12)}` +
      hs.cusps.map((c) => fmtDeg(c).padStart(7)).join(' '),
    );
  }
}

if (chart.moonDailyRange) {
  console.log(
    `\nEscursione della Luna nella giornata: ` +
    `${fmtLon(chart.moonDailyRange.minLongitude)} → ${fmtLon(chart.moonDailyRange.maxLongitude)}`,
  );
}

console.log(`\nAspetti (identici in tutte e tre le viste)`);
for (const a of chart.aspects) {
  const type = {
    conjunction: 'congiunzione', sextile: 'sestile', square: 'quadratura',
    trine: 'trigono', opposition: 'opposizione',
  }[a.type];
  console.log(
    `  ${(BODY_LABELS[a.a] ?? a.a)} ${type} ${(BODY_LABELS[a.b] ?? a.b)}` +
    `  (orbe ${a.orb.toFixed(2)}°)`,
  );
}
console.log();
