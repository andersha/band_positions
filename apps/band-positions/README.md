# Band Position Visualizer

Svelte + Vite web app that powers the GitHub Pages visualisation for NM Janitsjar band placements.

## Prerequisites
- Node 18+
- npm or pnpm/yarn

## Install & Run
```bash
cd apps/band-positions
npm install
npm run dev -- --open
```

## Data Refresh
Regenerate the static dataset before each deploy:
```bash
python ../../scripts/generate_band_positions.py
```

This writes `public/data/band_positions.json`, which Vite copies into the build output.

## Build for GitHub Pages
```bash
npm run build
```

The build is emitted to `docs/band-positions/`. Commit that folder to publish via GitHub Pages.
