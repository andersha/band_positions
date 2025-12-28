import { describe, it, expect } from 'vitest';
import { normalizeComposerName, extractComposerNames, getPrimaryComposer } from './composerUtils';

describe('normalizeComposerName', () => {
  it('trims whitespace', () => {
    expect(normalizeComposerName('  John Williams  ')).toBe('John Williams');
  });

  it('collapses multiple spaces', () => {
    expect(normalizeComposerName('John    Williams')).toBe('John Williams');
  });

  it('handles empty string', () => {
    expect(normalizeComposerName('')).toBe('');
  });
});

describe('extractComposerNames', () => {
  it('returns empty array for null/undefined', () => {
    expect(extractComposerNames(null)).toEqual([]);
    expect(extractComposerNames(undefined)).toEqual([]);
    expect(extractComposerNames('')).toEqual([]);
  });

  it('extracts single composer name', () => {
    expect(extractComposerNames('John Williams')).toEqual(['John Williams']);
  });

  it('splits composers by comma', () => {
    expect(extractComposerNames('Bach, Handel')).toEqual(['Bach', 'Handel']);
  });

  it('splits composers by semicolon', () => {
    expect(extractComposerNames('Bach; Handel')).toEqual(['Bach', 'Handel']);
  });

  it('splits composers by "og" (Norwegian "and")', () => {
    expect(extractComposerNames('Bach og Handel')).toEqual(['Bach', 'Handel']);
  });

  it('splits composers by "and"', () => {
    expect(extractComposerNames('Bach and Handel')).toEqual(['Bach', 'Handel']);
  });

  it('splits composers by ampersand', () => {
    expect(extractComposerNames('Bach & Handel')).toEqual(['Bach', 'Handel']);
  });

  it('splits composers by slash', () => {
    expect(extractComposerNames('Bach / Handel')).toEqual(['Bach', 'Handel']);
  });

  it('removes arrangement info with "arr."', () => {
    expect(extractComposerNames('Mozart, arr. Smith')).toEqual(['Mozart']);
  });

  it('removes arrangement info with "arrangement"', () => {
    expect(extractComposerNames('Mozart, arrangement by Smith')).toEqual(['Mozart']);
  });

  it('removes arrangement info with "bearb."', () => {
    expect(extractComposerNames('Mozart, bearb. Smith')).toEqual(['Mozart']);
  });

  it('removes arrangement info with "trans."', () => {
    expect(extractComposerNames('Mozart, trans. Smith')).toEqual(['Mozart']);
  });

  it('handles multiple delimiters', () => {
    expect(extractComposerNames('Bach, Handel og Mozart')).toEqual(['Bach', 'Handel', 'Mozart']);
  });

  it('deduplicates names (case-insensitive)', () => {
    expect(extractComposerNames('Bach, BACH')).toEqual(['Bach']);
  });

  it('preserves original casing of first occurrence', () => {
    const result = extractComposerNames('John Williams, JOHN WILLIAMS');
    expect(result).toEqual(['John Williams']);
  });

  it('handles complex real-world examples', () => {
    expect(extractComposerNames('Philip Sparke, arr. John Doe')).toEqual(['Philip Sparke']);
    expect(extractComposerNames('Torstein Aagaard-Nilsen og Ståle Kleiberg')).toEqual([
      'Torstein Aagaard-Nilsen',
      'Ståle Kleiberg'
    ]);
  });
});

describe('getPrimaryComposer', () => {
  it('returns null for empty input', () => {
    expect(getPrimaryComposer(null)).toBeNull();
    expect(getPrimaryComposer('')).toBeNull();
  });

  it('returns the first composer', () => {
    expect(getPrimaryComposer('Bach, Handel, Mozart')).toBe('Bach');
  });

  it('returns single composer when only one', () => {
    expect(getPrimaryComposer('John Williams')).toBe('John Williams');
  });
});
