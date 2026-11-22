/**
 * Aspetti fra corpi, calcolati sulle longitudini eclittiche reali.
 *
 * Gli aspetti dipendono dalle distanze angolari fra i corpi, non da come si
 * segmenta il cerchio: sono quindi IDENTICI nelle tre viste (tropicale,
 * siderale, IAU). L'interfaccia lo dichiara esplicitamente.
 */
import { angularDelta } from './bodies';
import type {
  AspectHit,
  AspectOrbs,
  AspectType,
  BodyId,
} from './types';

/**
 * Orbi di default, in gradi. Valori prudenti e documentati: 8° per
 * congiunzione e opposizione, 6° per trigono e quadratura, 4° per sestile.
 */
export const DEFAULT_ORBS: AspectOrbs = {
  conjunction: 8,
  sextile: 4,
  square: 6,
  trine: 6,
  opposition: 8,
};

const ASPECT_ANGLES: Record<AspectType, number> = {
  conjunction: 0,
  sextile: 60,
  square: 90,
  trine: 120,
  opposition: 180,
};

export interface AspectInput {
  body: BodyId;
  longitude: number;
}

/** I nodi non formano aspetti fra loro (sono lo stesso asse due volte). */
const NODE_IDS: readonly BodyId[] = ['MeanNode', 'TrueNode'];

export function computeAspects(
  positions: AspectInput[],
  orbs: Partial<AspectOrbs> = {},
): AspectHit[] {
  const effective: AspectOrbs = { ...DEFAULT_ORBS, ...orbs };
  const hits: AspectHit[] = [];
  for (let i = 0; i < positions.length; i++) {
    for (let j = i + 1; j < positions.length; j++) {
      const a = positions[i]!;
      const b = positions[j]!;
      if (NODE_IDS.includes(a.body) && NODE_IDS.includes(b.body)) continue;
      const separation = Math.abs(angularDelta(a.longitude, b.longitude));
      for (const type of Object.keys(ASPECT_ANGLES) as AspectType[]) {
        const exact = ASPECT_ANGLES[type];
        const orb = Math.abs(separation - exact);
        if (orb <= effective[type]) {
          hits.push({
            a: a.body,
            b: b.body,
            type,
            exactAngle: exact,
            separation,
            orb,
          });
        }
      }
    }
  }
  return hits.sort((x, y) => x.orb - y.orb);
}
