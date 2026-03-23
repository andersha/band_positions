import type { BandType, PromotionRules, PromotionStatus } from './types';

export function determinePromotionStatus(
  rules: PromotionRules | null,
  bandType: BandType,
  year: number,
  division: string,
  rank: number | null
): PromotionStatus {
  if (!rules || rank == null) return null;

  const byType = rules[bandType];
  if (!byType) return null;

  // Exact year match first
  let byYear = byType[String(year)];

  // Brass fallback: if no exact year but year is 2016 or later, use 2016 rules
  if (!byYear && bandType === 'brass' && year >= 2016) {
    byYear = byType['2016'];
  }

  if (!byYear) return null;

  const rule = byYear[division];
  if (!rule) return null;

  if (rule.promote && rule.promote.includes(rank)) return 'promote';
  if (rule.demote && rule.demote.includes(rank)) return 'demote';
  return 'safe';
}
