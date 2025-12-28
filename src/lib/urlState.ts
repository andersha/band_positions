import type { BandType } from './types';

export type ViewType = 'bands' | 'conductors' | 'pieces' | 'composers' | 'data' | 'repertoire' | '2026' | 'om' | 'innstillinger';

export const URL_PARAM_KEYS = { 
  bands: 'band', 
  conductors: 'conductor', 
  pieces: 'piece', 
  composers: 'composer' 
} as const;

export const URL_VIEW_KEY = 'view';
export const URL_BAND_TYPE_KEY = 'type';
export const URL_YEAR_KEY = 'year';
export const URL_DIVISION_KEY = 'division';
export const URL_SEPARATOR = ',';

export const DEFAULT_VIEW: ViewType = 'data';
export const DEFAULT_BAND_TYPE: BandType = 'wind';

export function getUrlParamKey(view: ViewType): string {
  if (view === 'data') return 'data';
  return URL_PARAM_KEYS[view as keyof typeof URL_PARAM_KEYS] ?? view;
}

/**
 * Parse view type from URL search params
 */
export function getViewFromURL(searchParams: URLSearchParams): ViewType {
  const raw = searchParams.get(URL_VIEW_KEY)?.toLowerCase();
  if (!raw) return DEFAULT_VIEW;
  
  if (raw === 'conductors' || raw === 'dirigent' || raw === 'conductor') {
    return 'conductors';
  }
  if (raw === 'pieces' || raw === 'piece' || raw === 'stykke' || raw === 'stykker') {
    return 'pieces';
  }
  if (raw === 'composers' || raw === 'komponist' || raw === 'composer') {
    return 'composers';
  }
  if (raw === 'data' || raw === 'resultat' || raw === 'results') {
    return 'data';
  }
  if (raw === 'om' || raw === 'about') {
    return 'om';
  }
  if (raw === '2026' || raw === 'upcoming') {
    return '2026';
  }
  if (raw === 'repertoire' || raw === 'repertoar') {
    return 'repertoire';
  }
  if (raw === 'innstillinger' || raw === 'settings') {
    return 'innstillinger';
  }
  if (raw === 'bands' || raw === 'korps' || raw === 'band') {
    return 'bands';
  }
  
  return 'bands';
}

/**
 * Parse band type from URL search params
 */
export function getBandTypeFromURL(searchParams: URLSearchParams): BandType {
  const raw = searchParams.get(URL_BAND_TYPE_KEY)?.toLowerCase();
  if (raw === 'brass' || raw === 'brassband') return 'brass';
  if (raw === 'wind' || raw === 'janitsjar') return 'wind';
  return DEFAULT_BAND_TYPE;
}

/**
 * Parse entity slugs from URL for a given view
 */
export function getSlugsFromURL(searchParams: URLSearchParams, view: ViewType): string[] {
  const raw = searchParams.get(getUrlParamKey(view));
  if (!raw) return [];
  return raw
    .split(URL_SEPARATOR)
    .map((slug) => decodeURIComponent(slug.trim()))
    .filter(Boolean);
}

/**
 * Check if URL has any navigation parameters (used to determine if showing startup screen)
 */
export function hasNavigationParams(searchParams: URLSearchParams): boolean {
  return searchParams.has(URL_VIEW_KEY) || 
         searchParams.has('band') || 
         searchParams.has('conductor') || 
         searchParams.has('piece') || 
         searchParams.has('composer') ||
         searchParams.has(URL_YEAR_KEY) ||
         searchParams.has(URL_DIVISION_KEY);
}

/**
 * Build URL search params from state
 */
export function buildUrlParams(options: {
  bandType: BandType;
  view: ViewType;
  selectedBandSlugs: string[];
  selectedConductorSlugs: string[];
  selectedPieceSlugs: string[];
  selectedComposerSlugs: string[];
}): URLSearchParams {
  const params = new URLSearchParams();
  
  params.set(URL_BAND_TYPE_KEY, options.bandType);
  params.set(URL_VIEW_KEY, options.view);
  
  if (options.selectedBandSlugs.length) {
    params.set(getUrlParamKey('bands'), options.selectedBandSlugs.map(encodeURIComponent).join(URL_SEPARATOR));
  }
  if (options.selectedConductorSlugs.length) {
    params.set(getUrlParamKey('conductors'), options.selectedConductorSlugs.map(encodeURIComponent).join(URL_SEPARATOR));
  }
  if (options.selectedPieceSlugs.length) {
    params.set(getUrlParamKey('pieces'), options.selectedPieceSlugs.map(encodeURIComponent).join(URL_SEPARATOR));
  }
  if (options.selectedComposerSlugs.length) {
    params.set(getUrlParamKey('composers'), options.selectedComposerSlugs.map(encodeURIComponent).join(URL_SEPARATOR));
  }
  
  return params;
}
