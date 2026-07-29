import { describe, it, expect } from 'vitest';
import {
  EMPTY_FILTER,
  getDivisionOrder,
  isActive,
  matchesFilter,
  filterBands,
  filterPieces,
} from '../../src/lib/statsFilter';
import type { BandEntry, BandRecord, PieceRecord } from '../../src/lib/types';

function entry(year: number, division: string): BandEntry {
  return {
    year,
    division,
    rank: 1,
    division_size: 10,
    absolute_position: 1,
    field_size: 50,
    points: 90,
    max_points: 100,
    conductor: 'Kari Nordmann',
    pieces: ['Marinarella'],
  };
}

describe('getDivisionOrder', () => {
  it('puts Elite first', () => {
    expect(getDivisionOrder('Elite')).toBe(0);
    expect(getDivisionOrder('elite')).toBe(0);
  });

  it('parses numbered divisions, including 7. divisjon', () => {
    expect(getDivisionOrder('1. divisjon')).toBe(1);
    expect(getDivisionOrder('7. divisjon')).toBe(7);
  });

  it('sends unknown divisions last', () => {
    expect(getDivisionOrder('Ukjent')).toBe(99);
  });

  it('sorts a full division list ladder-style', () => {
    const sorted = ['3. divisjon', 'Elite', '7. divisjon', '1. divisjon']
      .sort((a, b) => getDivisionOrder(a) - getDivisionOrder(b));
    expect(sorted).toEqual(['Elite', '1. divisjon', '3. divisjon', '7. divisjon']);
  });
});

describe('isActive', () => {
  it('is false for the empty filter', () => {
    expect(isActive(EMPTY_FILTER)).toBe(false);
  });

  it('is true when any field is set', () => {
    expect(isActive({ division: 'Elite', from: null, to: null })).toBe(true);
    expect(isActive({ division: '', from: 2010, to: null })).toBe(true);
    expect(isActive({ division: '', from: null, to: 2010 })).toBe(true);
  });
});

describe('matchesFilter', () => {
  const e = entry(2015, 'Elite');

  it('lets everything through when empty', () => {
    expect(matchesFilter(e, EMPTY_FILTER)).toBe(true);
  });

  it('matches division exactly', () => {
    expect(matchesFilter(e, { division: 'Elite', from: null, to: null })).toBe(true);
    expect(matchesFilter(e, { division: '1. divisjon', from: null, to: null })).toBe(false);
  });

  it('treats the year range as inclusive', () => {
    expect(matchesFilter(e, { division: '', from: 2015, to: 2015 })).toBe(true);
    expect(matchesFilter(e, { division: '', from: 2016, to: null })).toBe(false);
    expect(matchesFilter(e, { division: '', from: null, to: 2014 })).toBe(false);
  });

  it('supports an open-ended range', () => {
    expect(matchesFilter(e, { division: '', from: 2010, to: null })).toBe(true);
    expect(matchesFilter(e, { division: '', from: null, to: 2020 })).toBe(true);
  });

  it('requires all set fields to match', () => {
    expect(matchesFilter(e, { division: 'Elite', from: 2016, to: null })).toBe(false);
  });
});

describe('filterBands', () => {
  const bands: BandRecord[] = [
    { name: 'A', slug: 'a', entries: [entry(2000, 'Elite'), entry(2020, '1. divisjon')] },
    { name: 'B', slug: 'b', entries: [entry(1990, '2. divisjon')] },
  ];

  it('returns the input untouched when the filter is empty', () => {
    expect(filterBands(bands, EMPTY_FILTER)).toBe(bands);
  });

  it('drops bands with no remaining entries', () => {
    const result = filterBands(bands, { division: 'Elite', from: null, to: null });
    expect(result).toHaveLength(1);
    expect(result[0].name).toBe('A');
    expect(result[0].entries).toHaveLength(1);
  });

  it('does not mutate the source', () => {
    filterBands(bands, { division: 'Elite', from: null, to: null });
    expect(bands[0].entries).toHaveLength(2);
  });
});

describe('filterPieces', () => {
  const pieces: PieceRecord[] = [
    {
      name: 'Marinarella',
      slug: 'marinarella',
      performances: [
        { band: 'A', entry: entry(2000, 'Elite') },
        { band: 'B', entry: entry(2020, '4. divisjon') },
      ],
    },
    {
      name: 'Festive Piece',
      slug: 'festive-piece',
      performances: [{ band: 'C', entry: entry(1990, '2. divisjon') }],
    },
  ];

  it('keeps only performances in the selected division', () => {
    const result = filterPieces(pieces, { division: '4. divisjon', from: null, to: null });
    expect(result).toHaveLength(1);
    expect(result[0].slug).toBe('marinarella');
    expect(result[0].performances).toHaveLength(1);
    expect(result[0].performances[0].band).toBe('B');
  });

  it('drops pieces with no performances left in the year range', () => {
    expect(filterPieces(pieces, { division: '', from: 2021, to: null })).toEqual([]);
  });
});
