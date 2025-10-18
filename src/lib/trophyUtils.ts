export function getTrophy(rank: number | null): string {
  if (rank === 1) return '🥇 ';
  if (rank === 2) return '🥈 ';
  if (rank === 3) return '🥉 ';
  return '';
}

export interface TrophyCount {
  gold: number;
  silver: number;
  bronze: number;
}

export function countTrophies(entries: Array<{ rank: number | null }>): TrophyCount {
  return entries.reduce(
    (acc, entry) => {
      if (entry.rank === 1) acc.gold++;
      else if (entry.rank === 2) acc.silver++;
      else if (entry.rank === 3) acc.bronze++;
      return acc;
    },
    { gold: 0, silver: 0, bronze: 0 }
  );
}

export function formatTrophySummary(count: TrophyCount): string {
  const parts: string[] = [];
  if (count.gold > 0) parts.push(`${count.gold} 🥇`);
  if (count.silver > 0) parts.push(`${count.silver} 🥈`);
  if (count.bronze > 0) parts.push(`${count.bronze} 🥉`);
  return parts.join(' ');
}
