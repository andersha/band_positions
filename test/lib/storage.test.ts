import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { readLS, writeLS, STORAGE_KEYS } from '../../src/lib/storage';

describe('storage', () => {
  // Create a proper storage mock
  let store: Record<string, string> = {};
  const originalLocalStorage = globalThis.localStorage;
  
  const mockLocalStorage = {
    getItem: vi.fn((key: string) => store[key] ?? null),
    setItem: vi.fn((key: string, value: string) => { store[key] = value; }),
    removeItem: vi.fn((key: string) => { delete store[key]; }),
    clear: vi.fn(() => { store = {}; }),
    length: 0,
    key: vi.fn(() => null),
  };

  beforeEach(() => {
    store = {};
    vi.clearAllMocks();
    // Replace window.localStorage
    Object.defineProperty(window, 'localStorage', {
      value: mockLocalStorage,
      writable: true,
      configurable: true,
    });
  });

  afterEach(() => {
    // Restore original localStorage
    Object.defineProperty(window, 'localStorage', {
      value: originalLocalStorage,
      writable: true,
      configurable: true,
    });
  });

  describe('readLS', () => {
    it('returns fallback when key does not exist', () => {
      expect(readLS('nonexistent', 'default')).toBe('default');
    });

    it('returns stored value when key exists', () => {
      store['testKey'] = 'storedValue';
      expect(readLS('testKey', 'default')).toBe('storedValue');
    });

    it('returns fallback on localStorage error', () => {
      mockLocalStorage.getItem.mockImplementationOnce(() => {
        throw new Error('Storage error');
      });
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      expect(readLS('key', 'fallback')).toBe('fallback');
      
      consoleSpy.mockRestore();
    });
  });

  describe('writeLS', () => {
    it('stores value in localStorage', () => {
      writeLS('testKey', 'testValue');
      expect(store['testKey']).toBe('testValue');
    });

    it('handles localStorage error gracefully', () => {
      mockLocalStorage.setItem.mockImplementationOnce(() => {
        throw new Error('Storage full');
      });
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      // Should not throw
      expect(() => writeLS('key', 'value')).not.toThrow();
      
      consoleSpy.mockRestore();
    });
  });

  describe('STORAGE_KEYS', () => {
    it('has expected keys defined', () => {
      expect(STORAGE_KEYS.THEME).toBe('nmkorps-theme');
      expect(STORAGE_KEYS.BAND_TYPE).toBe('nmkorps-band-type');
      expect(STORAGE_KEYS.YAXIS_MODE).toBe('nmkorps-yaxis-mode');
      expect(STORAGE_KEYS.YAXIS_SCALE).toBe('nmkorps-yaxis-scale');
      expect(STORAGE_KEYS.SELECTION_MODE).toBe('nmkorps-selection-mode');
    });
  });
});
