import type { BandRecord, PieceRecord } from './types';

export interface StatsFilter {
  division: string;
  from: number | null;
  to: number | null;
}

export const EMPTY_FILTER: StatsFilter = { division: '', from: null, to: null };

/** 'Elite' → 0, '3. divisjon' → 3, ukjent → 99 */
export function getDivisionOrder(division: string): number {
  const norm = division.trim().toLowerCase();
  if (norm === 'elite') return 0;
  const m = norm.match(/(\d+)/);
  return m ? parseInt(m[1], 10) : 99;
}

export function isActive(f: StatsFilter): boolean {
  return Boolean(f.division) || f.from !== null || f.to !== null;
}

export function matchesFilter(e: { year: number; division: string }, f: StatsFilter): boolean {
  if (f.division && e.division !== f.division) return false;
  if (f.from !== null && e.year < f.from) return false;
  if (f.to !== null && e.year > f.to) return false;
  return true;
}

export function filterBands(bands: BandRecord[], f: StatsFilter): BandRecord[] {
  if (!isActive(f)) return bands;
  return bands
    .map((band) => ({ ...band, entries: band.entries.filter((e) => matchesFilter(e, f)) }))
    .filter((band) => band.entries.length > 0);
}

export function filterPieces(pieces: PieceRecord[], f: StatsFilter): PieceRecord[] {
  if (!isActive(f)) return pieces;
  return pieces
    .map((piece) => ({
      ...piece,
      performances: piece.performances.filter((p) => matchesFilter(p.entry, f)),
    }))
    .filter((piece) => piece.performances.length > 0);
}
