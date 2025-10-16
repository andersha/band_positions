# Band Position Visualizer

Svelte + Vite web app that powers the GitHub Pages visualization for NM Janitsjar band placements.

**🎵 Live App:** [https://andersha.github.io/band_positions/](https://andersha.github.io/band_positions/)

## Mobile Apps

This repository contains the web application that is shared across all platforms. For mobile apps:

- **iOS App:** [band_positions_ios](https://github.com/andersha/band_positions_ios)
- **Android App:** [band_positions_android](https://github.com/andersha/band_positions_android)

Both mobile repositories include this web app as a git submodule.

## Prerequisites
- Node 18+
- npm or pnpm/yarn

## Install & Run

### Web Development
```bash
npm install
npm run dev
```

Visit http://localhost:5173 to see the app.

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

The build is emitted to `docs/`. Commit that folder to publish via GitHub Pages.

## NPM Scripts

- `npm run dev` - Start Vite dev server
- `npm run build` - Build web app to docs/
- `npm run preview` - Preview production build locally

## Project Structure

- `src/` - Svelte source code
- `public/` - Static assets (copied to build)
- `docs/` - Built output for GitHub Pages
- `index.html` - Entry HTML file
- `vite.config.ts` - Vite configuration
