/**
 * Reads a value from localStorage with a fallback default value
 * @param key - The localStorage key to read
 * @param fallback - The default value to return if key doesn't exist or there's an error
 * @returns The stored value or the fallback
 */
export function readLS<T extends string>(key: string, fallback: T): T {
  if (typeof window === 'undefined') return fallback;
  
  try {
    const stored = window.localStorage.getItem(key);
    return (stored ?? fallback) as T;
  } catch (err) {
    console.error(`Could not read from localStorage (key: ${key})`, err);
    return fallback;
  }
}

/**
 * Writes a value to localStorage
 * @param key - The localStorage key to write to
 * @param value - The value to store
 */
export function writeLS(key: string, value: string): void {
  if (typeof window === 'undefined') return;
  
  try {
    window.localStorage.setItem(key, value);
  } catch (err) {
    console.error(`Could not write to localStorage (key: ${key})`, err);
  }
}

// Storage keys
export const STORAGE_KEYS = {
  THEME: 'nmkorps-theme',
  BAND_TYPE: 'nmkorps-band-type',
  YAXIS_MODE: 'nmkorps-yaxis-mode',
  YAXIS_SCALE: 'nmkorps-yaxis-scale',
} as const;
