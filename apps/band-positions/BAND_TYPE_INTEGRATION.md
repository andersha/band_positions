# Band Type Integration - Wind & Brass Bands

This document describes the dual dataset support added to the NM Korps visualization app.

## Overview

The app now supports switching between two types of band competitions:
- **Janitsjarkorps (Wind Bands)** 🎷 - Norwegian wind band competitions (1981-2025, 41 years)
- **Brassband (Brass Bands)** 🎺 - Norwegian brass band competitions (2001-2025, 23 years)

## User Interface Changes

### Global Band Type Toggle

A new toggle button has been added next to the theme toggle in the header:
- **Icon**: 🎷 for wind bands, 🎺 for brass bands
- **Label**: "Janitsjar" or "Brass"
- **Location**: Header controls, left of the theme toggle

### Page Header

- **Title**: Changed from "NM Janitsjar" to "NM Korps"
- **Subtitle**: Dynamic subtitle showing current band type:
  - "Janitsjarkorps" when viewing wind bands
  - "Brassband" when viewing brass bands

### Color Schemes

#### Wind Bands (Default - Blue)
- **Dark mode**: Blue gradient (#0f172a → #1e293b → #334155)
- **Accent color**: Light blue (#38bdf8)
- **Chip colors**: Blue-tinted backgrounds and borders

#### Brass Bands (Purple)
- **Dark mode**: Purple gradient (#1e1b3a → #2d2355 → #3d2f6d)
- **Light mode**: Light purple gradient (#faf5ff → #f3e8ff)
- **Accent color**: Purple (#c084fc dark, #9333ea light)
- **Chip colors**: Purple-tinted backgrounds and borders

## Technical Implementation

### Data Files

Two separate dataset files are maintained:

```
apps/band-positions/public/data/
├── band_positions.json      # Wind band data (1.0MB, 41 years)
├── brass_positions.json     # Brass band data (586KB, 23 years)
└── piece_metadata.json      # Shared piece/composer metadata
```

### State Management

**URL Parameters**:
- `type`: Band type in URL query string (`?type=wind` or `?type=brass`)
  - Enables shareable links
  - First priority for band type resolution
  - Supports aliases: `wind`, `janitsjar`, `brass`, `brassband`

**Storage Keys**:
- `nmkorps-band-type`: Persists user's band type selection (localStorage, fallback)
- `nmkorps-theme`: Persists theme preference (localStorage)

**State Variables** (App.svelte):
```typescript
let bandType = $state<BandType>('wind');  // 'wind' | 'brass'
let theme = $state<Theme>('dark');        // 'dark' | 'light'
```

### Data Loading

The app dynamically loads the appropriate dataset based on selected band type:

```typescript
async function loadDataForBandType(type: BandType) {
  const dataFile = type === 'wind' 
    ? 'data/band_positions.json' 
    : 'data/brass_positions.json';
  
  // Fetch and load data...
}
```

### Switching Behavior

When switching between wind and brass bands:

1. **Clear all selections**: selectedBands, selectedConductors, selectedPieces, selectedComposers
2. **Update URL parameter**: Set `?type=wind` or `?type=brass` in URL
3. **Clear other URL parameters**: Remove band, conductor, piece, composer query strings
4. **Reset UI state**: searchTerm, focusedIndex
5. **Update DOM attributes**: `data-band-type` on document root
6. **Persist selection**: Save to localStorage (as fallback)
7. **Reload data**: Fetch appropriate dataset
8. **Reapply theme**: Theme persists across band type changes

### Band Type Resolution Priority

Band type is determined in this order:

1. **URL parameter** (`?type=wind` or `?type=brass`) - Highest priority
2. **localStorage** (`nmkorps-band-type`) - Fallback
3. **Default** (`wind`) - If neither is available

### CSS Architecture

Band type styling uses CSS custom properties with cascading specificity:

```css
/* Base (wind bands, dark) */
:root {
  --color-accent: #38bdf8;
  /* ... */
}

/* Wind bands, light mode */
:root[data-theme='light'] {
  --color-accent: #2563eb;
  /* ... */
}

/* Brass bands, dark mode */
:root[data-band-type='brass'] {
  --color-accent: #c084fc;
  /* ... */
}

/* Brass bands, light mode */
:root[data-theme='light'][data-band-type='brass'] {
  --color-accent: #9333ea;
  /* ... */
}
```

## Component Structure

### New Functions in App.svelte

- `getBandTypeFromURL()`: Extract band type from URL query parameter (`?type=`)
- `resolveInitialBandType()`: Read band type from URL, localStorage, or default to 'wind'
- `applyBandTypePreference(type)`: Update DOM `data-band-type` attribute
- `setBandType(type, updateUrl)`: Switch band type with full state reset and URL update
- `toggleBandType()`: Toggle between wind and brass
- `loadDataForBandType(type)`: Fetch and load dataset for given type
- `closeBandTypeMenu()`: Close band type dropdown (future enhancement)
- `toggleBandTypeMenu()`: Toggle band type dropdown (future enhancement)

### Updated Reactive Variables

Added band type awareness to:
- `leadText`: Context-specific search instructions
- `bandTypeToggleLabel`: Accessibility label
- `bandTypeToggleText`: Button text
- `bandTypeToggleIcon`: Emoji icon

## Data Schema Compatibility

Both datasets use identical JSON schema, ensuring seamless switching:

```typescript
interface BandDataset {
  bands: BandRecord[];
  metadata: {
    years: number[];
    divisions: string[];
    max_field_size: number;
    min_year: number;
    max_year: number;
    generated_at: string;
  };
}
```

## Generating Brass Band Data

The brass band dataset is generated from CSV export using:

```bash
python3 scripts/generate_band_positions.py \
  --input data/brass/processed/all_placements.csv \
  --output apps/band-positions/public/data/brass_positions.json
```

## Browser Compatibility

### localStorage Support
- Gracefully degrades if localStorage is unavailable
- Falls back to default values (wind bands, dark theme)

### CSS Custom Properties
- Fully supported in modern browsers
- Progressive enhancement approach

### Data Attributes
- Standard HTML5 `data-*` attributes
- Universal browser support

## Shareable Links

Links now include the band type in the URL, making them shareable:

**Examples:**
- Wind bands: `https://example.com/?type=wind`
- Brass bands: `https://example.com/?type=brass`
- With selections: `https://example.com/?type=brass&band=eikanger-bjorsvik-musikklag&view=bands`

**Supported URL values:**
- Wind: `type=wind` or `type=janitsjar`
- Brass: `type=brass` or `type=brassband`

## Future Enhancements

### Potential Improvements

1. ✅ **URL persistence**: Band type is now stored in URL (`?type=brass` or `?type=wind`)
2. **Comparison mode**: Allow side-by-side comparison of wind vs brass
3. **Unified search**: Search across both datasets simultaneously
4. **Animation**: Smooth color transition when switching band types
5. **Keyboard shortcut**: Ctrl+B or Cmd+B to toggle band type
6. **Separate metadata**: Brass-specific piece metadata file
7. **Analytics**: Track which band type is more popular

### Known Limitations

1. **No cross-dataset comparison**: Cannot compare wind and brass bands directly
2. **Selections clear on switch**: Band/conductor/piece selections reset when changing band type
3. **No mixed selections**: Cannot select both wind and brass bands simultaneously

## Testing Checklist

✅ Band type toggle appears in header  
✅ Toggle switches between wind (🎷) and brass (🎺)  
✅ Color scheme changes when switching band types  
✅ Data loads correctly for both types  
✅ Band type persists in URL (`?type=wind` or `?type=brass`)  
✅ Shareable links work correctly  
✅ URL parameter takes priority over localStorage  
✅ Selection URL params clear on band type switch  
✅ Selections reset when switching  
✅ Theme persists across band type changes  
✅ localStorage saves band type preference (fallback)  
✅ Page subtitle updates based on band type  
✅ Lead text updates for brass bands  
✅ All views work (bands, conductors, pieces, composers, data)  
✅ Browser back/forward buttons respect band type changes

## Development

### Run Dev Server
```bash
cd apps/band-positions
npm run dev
```

### Build for Production
```bash
cd apps/band-positions
npm run build
```

### Update Data
```bash
# Wind bands (from root)
python3 scripts/generate_band_positions.py

# Brass bands (from root)
python3 scripts/generate_band_positions.py \
  --input data/brass/processed/all_placements.csv \
  --output apps/band-positions/public/data/brass_positions.json
```

## Accessibility

- ✅ Proper ARIA labels on toggle buttons
- ✅ Keyboard navigation supported
- ✅ Focus indicators on interactive elements
- ✅ Semantic HTML structure maintained
- ✅ Screen reader friendly state changes

---

**Last Updated**: September 29, 2025  
**App Version**: With dual dataset support and URL-based band type persistence
