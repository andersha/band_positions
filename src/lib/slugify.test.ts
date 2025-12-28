import { describe, it, expect } from 'vitest';
import { slugify } from './slugify';

describe('slugify', () => {
  it('converts basic text to lowercase slug', () => {
    expect(slugify('Hello World')).toBe('hello-world');
  });

  it('handles Norwegian characters (æ, ø, å)', () => {
    // Note: ø becomes empty after NFKD normalization and non-ASCII removal
    expect(slugify('Bjørn Ærlig Åsen')).toBe('bjrn-rlig-asen');
  });

  it('removes accents from characters', () => {
    expect(slugify('Café Naïve')).toBe('cafe-naive');
  });

  it('replaces multiple spaces with single hyphen', () => {
    expect(slugify('Hello    World')).toBe('hello-world');
  });

  it('removes special characters', () => {
    expect(slugify('Hello! @World# $Test%')).toBe('hello-world-test');
  });

  it('trims leading and trailing hyphens', () => {
    expect(slugify('  Hello World  ')).toBe('hello-world');
    expect(slugify('---Hello---')).toBe('hello');
  });

  it('returns "uidentifisert" for empty strings', () => {
    expect(slugify('')).toBe('uidentifisert');
    expect(slugify('   ')).toBe('uidentifisert');
  });

  it('handles numbers', () => {
    expect(slugify('Test 123')).toBe('test-123');
  });

  it('handles band names with special Norwegian characters', () => {
    expect(slugify('Manger Musikklag')).toBe('manger-musikklag');
    expect(slugify('Stavanger Brass Band')).toBe('stavanger-brass-band');
    expect(slugify('Ørskog Musikklag')).toBe('rskog-musikklag');
  });

  it('handles piece titles with parentheses and punctuation', () => {
    expect(slugify('Symphony No. 5 (Finale)')).toBe('symphony-no-5-finale');
    expect(slugify('Dances: Part 1')).toBe('dances-part-1');
  });
});
