import { describe, it, expect } from 'vitest';
import {
  getViewFromURL,
  getBandTypeFromURL,
  getSlugsFromURL,
  hasNavigationParams,
  buildUrlParams,
  getUrlParamKey,
  DEFAULT_VIEW,
  DEFAULT_BAND_TYPE,
} from './urlState';

describe('getViewFromURL', () => {
  it('returns default view when no view parameter', () => {
    const params = new URLSearchParams();
    expect(getViewFromURL(params)).toBe(DEFAULT_VIEW);
  });

  it('parses "bands" view', () => {
    expect(getViewFromURL(new URLSearchParams('view=bands'))).toBe('bands');
    expect(getViewFromURL(new URLSearchParams('view=korps'))).toBe('bands');
    expect(getViewFromURL(new URLSearchParams('view=band'))).toBe('bands');
  });

  it('parses "conductors" view', () => {
    expect(getViewFromURL(new URLSearchParams('view=conductors'))).toBe('conductors');
    expect(getViewFromURL(new URLSearchParams('view=conductor'))).toBe('conductors');
    expect(getViewFromURL(new URLSearchParams('view=dirigent'))).toBe('conductors');
  });

  it('parses "pieces" view', () => {
    expect(getViewFromURL(new URLSearchParams('view=pieces'))).toBe('pieces');
    expect(getViewFromURL(new URLSearchParams('view=piece'))).toBe('pieces');
    expect(getViewFromURL(new URLSearchParams('view=stykke'))).toBe('pieces');
    expect(getViewFromURL(new URLSearchParams('view=stykker'))).toBe('pieces');
  });

  it('parses "composers" view', () => {
    expect(getViewFromURL(new URLSearchParams('view=composers'))).toBe('composers');
    expect(getViewFromURL(new URLSearchParams('view=composer'))).toBe('composers');
    expect(getViewFromURL(new URLSearchParams('view=komponist'))).toBe('composers');
  });

  it('parses "data" view', () => {
    expect(getViewFromURL(new URLSearchParams('view=data'))).toBe('data');
    expect(getViewFromURL(new URLSearchParams('view=resultat'))).toBe('data');
    expect(getViewFromURL(new URLSearchParams('view=results'))).toBe('data');
  });

  it('parses "om" (about) view', () => {
    expect(getViewFromURL(new URLSearchParams('view=om'))).toBe('om');
    expect(getViewFromURL(new URLSearchParams('view=about'))).toBe('om');
  });

  it('parses "2026" view', () => {
    expect(getViewFromURL(new URLSearchParams('view=2026'))).toBe('2026');
    expect(getViewFromURL(new URLSearchParams('view=upcoming'))).toBe('2026');
  });

  it('parses "repertoire" view', () => {
    expect(getViewFromURL(new URLSearchParams('view=repertoire'))).toBe('repertoire');
    expect(getViewFromURL(new URLSearchParams('view=repertoar'))).toBe('repertoire');
  });

  it('parses "innstillinger" (settings) view', () => {
    expect(getViewFromURL(new URLSearchParams('view=innstillinger'))).toBe('innstillinger');
    expect(getViewFromURL(new URLSearchParams('view=settings'))).toBe('innstillinger');
  });

  it('is case-insensitive', () => {
    expect(getViewFromURL(new URLSearchParams('view=BANDS'))).toBe('bands');
    expect(getViewFromURL(new URLSearchParams('view=Conductors'))).toBe('conductors');
  });

  it('returns bands for unknown view values', () => {
    expect(getViewFromURL(new URLSearchParams('view=unknown'))).toBe('bands');
  });
});

describe('getBandTypeFromURL', () => {
  it('returns default band type when no type parameter', () => {
    const params = new URLSearchParams();
    expect(getBandTypeFromURL(params)).toBe(DEFAULT_BAND_TYPE);
  });

  it('parses "wind" type', () => {
    expect(getBandTypeFromURL(new URLSearchParams('type=wind'))).toBe('wind');
    expect(getBandTypeFromURL(new URLSearchParams('type=janitsjar'))).toBe('wind');
  });

  it('parses "brass" type', () => {
    expect(getBandTypeFromURL(new URLSearchParams('type=brass'))).toBe('brass');
    expect(getBandTypeFromURL(new URLSearchParams('type=brassband'))).toBe('brass');
  });

  it('is case-insensitive', () => {
    expect(getBandTypeFromURL(new URLSearchParams('type=BRASS'))).toBe('brass');
    expect(getBandTypeFromURL(new URLSearchParams('type=Wind'))).toBe('wind');
  });

  it('returns default for unknown type values', () => {
    expect(getBandTypeFromURL(new URLSearchParams('type=unknown'))).toBe(DEFAULT_BAND_TYPE);
  });
});

describe('getSlugsFromURL', () => {
  it('returns empty array when no slugs', () => {
    const params = new URLSearchParams();
    expect(getSlugsFromURL(params, 'bands')).toEqual([]);
  });

  it('parses single slug for bands', () => {
    const params = new URLSearchParams('band=stavanger-brass-band');
    expect(getSlugsFromURL(params, 'bands')).toEqual(['stavanger-brass-band']);
  });

  it('parses multiple slugs separated by comma', () => {
    const params = new URLSearchParams('band=band-a,band-b,band-c');
    expect(getSlugsFromURL(params, 'bands')).toEqual(['band-a', 'band-b', 'band-c']);
  });

  it('handles URL-encoded slugs', () => {
    const params = new URLSearchParams('band=band%20with%20spaces');
    expect(getSlugsFromURL(params, 'bands')).toEqual(['band with spaces']);
  });

  it('parses slugs for conductors', () => {
    const params = new URLSearchParams('conductor=john-doe');
    expect(getSlugsFromURL(params, 'conductors')).toEqual(['john-doe']);
  });

  it('parses slugs for pieces', () => {
    const params = new URLSearchParams('piece=symphony-no-5');
    expect(getSlugsFromURL(params, 'pieces')).toEqual(['symphony-no-5']);
  });

  it('parses slugs for composers', () => {
    const params = new URLSearchParams('composer=beethoven');
    expect(getSlugsFromURL(params, 'composers')).toEqual(['beethoven']);
  });

  it('filters out empty slugs', () => {
    const params = new URLSearchParams('band=band-a,,band-b');
    expect(getSlugsFromURL(params, 'bands')).toEqual(['band-a', 'band-b']);
  });

  it('trims whitespace from slugs', () => {
    const params = new URLSearchParams('band= band-a , band-b ');
    expect(getSlugsFromURL(params, 'bands')).toEqual(['band-a', 'band-b']);
  });
});

describe('hasNavigationParams', () => {
  it('returns false for empty params', () => {
    expect(hasNavigationParams(new URLSearchParams())).toBe(false);
  });

  it('returns true when view is present', () => {
    expect(hasNavigationParams(new URLSearchParams('view=bands'))).toBe(true);
  });

  it('returns true when band is present', () => {
    expect(hasNavigationParams(new URLSearchParams('band=test'))).toBe(true);
  });

  it('returns true when conductor is present', () => {
    expect(hasNavigationParams(new URLSearchParams('conductor=test'))).toBe(true);
  });

  it('returns true when piece is present', () => {
    expect(hasNavigationParams(new URLSearchParams('piece=test'))).toBe(true);
  });

  it('returns true when composer is present', () => {
    expect(hasNavigationParams(new URLSearchParams('composer=test'))).toBe(true);
  });

  it('returns true when year is present', () => {
    expect(hasNavigationParams(new URLSearchParams('year=2024'))).toBe(true);
  });

  it('returns true when division is present', () => {
    expect(hasNavigationParams(new URLSearchParams('division=elite'))).toBe(true);
  });

  it('returns false when only type is present', () => {
    expect(hasNavigationParams(new URLSearchParams('type=wind'))).toBe(false);
  });
});

describe('buildUrlParams', () => {
  it('builds params with band type and view', () => {
    const params = buildUrlParams({
      bandType: 'wind',
      view: 'bands',
      selectedBandSlugs: [],
      selectedConductorSlugs: [],
      selectedPieceSlugs: [],
      selectedComposerSlugs: [],
    });

    expect(params.get('type')).toBe('wind');
    expect(params.get('view')).toBe('bands');
  });

  it('includes selected band slugs', () => {
    const params = buildUrlParams({
      bandType: 'wind',
      view: 'bands',
      selectedBandSlugs: ['band-a', 'band-b'],
      selectedConductorSlugs: [],
      selectedPieceSlugs: [],
      selectedComposerSlugs: [],
    });

    expect(params.get('band')).toBe('band-a,band-b');
  });

  it('includes selected conductor slugs', () => {
    const params = buildUrlParams({
      bandType: 'wind',
      view: 'conductors',
      selectedBandSlugs: [],
      selectedConductorSlugs: ['conductor-a'],
      selectedPieceSlugs: [],
      selectedComposerSlugs: [],
    });

    expect(params.get('conductor')).toBe('conductor-a');
  });

  it('includes selected piece slugs', () => {
    const params = buildUrlParams({
      bandType: 'wind',
      view: 'pieces',
      selectedBandSlugs: [],
      selectedConductorSlugs: [],
      selectedPieceSlugs: ['piece-a', 'piece-b'],
      selectedComposerSlugs: [],
    });

    expect(params.get('piece')).toBe('piece-a,piece-b');
  });

  it('includes selected composer slugs', () => {
    const params = buildUrlParams({
      bandType: 'wind',
      view: 'composers',
      selectedBandSlugs: [],
      selectedConductorSlugs: [],
      selectedPieceSlugs: [],
      selectedComposerSlugs: ['composer-a'],
    });

    expect(params.get('composer')).toBe('composer-a');
  });

  it('URL-encodes slugs with special characters', () => {
    const params = buildUrlParams({
      bandType: 'wind',
      view: 'bands',
      selectedBandSlugs: ['band with spaces'],
      selectedConductorSlugs: [],
      selectedPieceSlugs: [],
      selectedComposerSlugs: [],
    });

    expect(params.get('band')).toBe('band%20with%20spaces');
  });

  it('omits empty selection arrays', () => {
    const params = buildUrlParams({
      bandType: 'brass',
      view: 'data',
      selectedBandSlugs: [],
      selectedConductorSlugs: [],
      selectedPieceSlugs: [],
      selectedComposerSlugs: [],
    });

    expect(params.has('band')).toBe(false);
    expect(params.has('conductor')).toBe(false);
    expect(params.has('piece')).toBe(false);
    expect(params.has('composer')).toBe(false);
  });
});

describe('getUrlParamKey', () => {
  it('returns correct key for bands', () => {
    expect(getUrlParamKey('bands')).toBe('band');
  });

  it('returns correct key for conductors', () => {
    expect(getUrlParamKey('conductors')).toBe('conductor');
  });

  it('returns correct key for pieces', () => {
    expect(getUrlParamKey('pieces')).toBe('piece');
  });

  it('returns correct key for composers', () => {
    expect(getUrlParamKey('composers')).toBe('composer');
  });

  it('returns "data" for data view', () => {
    expect(getUrlParamKey('data')).toBe('data');
  });

  it('returns view name for views without mapping', () => {
    expect(getUrlParamKey('om')).toBe('om');
    expect(getUrlParamKey('2026')).toBe('2026');
    expect(getUrlParamKey('repertoire')).toBe('repertoire');
  });
});
