# WARP.md - Band Positions App

This file provides guidance to WARP (warp.dev) when working with the Band Positions visualization app.

## Project Overview

Band Positions is a Svelte 5 + TypeScript application that visualizes Norwegian wind band and brass band competition data. This repository contains **only the frontend application**. The data scraping and processing pipeline lives in a separate private repository: [band_data](https://github.com/andersha/band_data).

## Repository Split

This project was split from a monorepo in October 2025:
- **band_positions** (this repo, public): Frontend app for web, iOS, and Android
- **band_data** (private): Data scraping, processing, and export pipeline

## Quick Reference

### Essential Commands

```bash
# Web Development
cd apps/band-positions
npm install
npm run dev -- --open        # Development server
npm run build                # Build to docs/
npm run preview              # Preview production build

# iOS Development
npm run ios:run              # Build, sync, and open in Xcode
npm run ios:open             # Just open Xcode
npm run ios:sync             # Full sync with plugin updates
npm run ios:copy             # Quick copy without plugin sync

# Android Development
npm run android:run          # Build, sync, and open in Android Studio
npm run android:open         # Just open Android Studio
npm run android:sync         # Full sync with plugin updates
npm run android:copy         # Quick copy without plugin sync
npm run android:build:release  # Build signed AAB/APK for Play Store
```

### Data Updates

**IMPORTANT**: This repo does not scrape or process data. All data comes from the private `band_data` repository.

To update app data:
1. Go to `band_data` repo and run export scripts
2. Data is written to `public/data/` in this repo
3. Build and commit the updated app

See [README.md](README.md#data-updates) for detailed workflow.

## Project Structure

```
band_positions/


│       ├── src/
│       │   ├── App.svelte       # Main app component
│       │   └── lib/             # Reusable components & utilities
│       ├── public/
│       │   └── data/            # JSON data files (from band_data)
│       ├── ios/                 # Capacitor iOS project
│       ├── android/             # Capacitor Android project
│       ├── docs/                # Development documentation
│       └── package.json
├── docs/
│   ├── band-positions/          # Built app (GitHub Pages)
│   └── privacy/                 # Privacy policy
└── README.md
```

## Technology Stack

- **Frontend**: Svelte 5 with runes for reactivity
- **Language**: TypeScript
- **Visualization**: D3.js for interactive charts
- **Build**: Vite
- **Mobile**: Capacitor for iOS and Android
- **Hosting**: GitHub Pages (static)

## Key Development Patterns

### Svelte 5 Runes

This app uses Svelte 5's new runes syntax:
- `$state()` - Reactive state
- `$derived()` - Computed values
- `$effect()` - Side effects
- `$props()` - Component props

### Data Loading

Data files are loaded from `public/data/`:
- `band_positions.json` - Wind band competition data
- `brass_positions.json` - Brass band competition data
- `repertoire.json` - Piece metadata from WindRep.org
- `streaming/wind/*.json` - Per-year Spotify/Apple Music links
- `streaming/brass/*.json` - Brass band streaming links

Files are fetched dynamically at runtime and cached in component state.

### URL State Management

The app uses URL parameters to maintain state:
- Selected band, year, division encoded in URL
- Allows deep linking and sharing
- Updates without page reload

### D3.js Integration

Charts are rendered using D3.js with Svelte lifecycle:
- D3 creates/updates SVG elements
- Svelte manages component lifecycle and reactivity
- Smooth transitions on data changes

## iOS Development

### Capacitor Setup

The iOS app is in `ios/App/`. Key files:
- `App.xcworkspace` - Open this in Xcode (NOT .xcodeproj)
- `App/App/Info.plist` - App configuration
- `App/App/Assets.xcassets` - App icons and images

### Build Process

1. `npm run build` - Builds web app to `docs/`
2. `npx cap sync ios` - Copies web assets to iOS project
3. Open in Xcode - Build and run on simulator/device

### Common iOS Tasks

```bash
# After adding Capacitor plugins
npm install @capacitor/plugin-name
npm run ios:sync  # Sync plugins to iOS

# Quick iteration (no plugin changes)
npm run ios:copy

# Open in Xcode
npm run ios:open
```

## Android Development

### Capacitor Setup

The Android app is in `android/`. Key files:
- `android/app/build.gradle` - Version numbers, signing, dependencies
- `android/app/src/main/AndroidManifest.xml` - App permissions
- `android/app/src/main/res/` - Resources (icons, strings, styles)
- `android/keystore.properties` - Signing credentials (NOT in git)
- `android/release-key.jks` - Signing keystore (NOT in git)

### Build Process

1. `npm run build` - Builds web app to `docs/`
2. `npx cap sync android` - Copies web assets to Android project
3. Open in Android Studio - Build and run on emulator/device

### Common Android Tasks

```bash
# After adding Capacitor plugins
npm install @capacitor/plugin-name
npm run android:sync  # Sync plugins to Android

# Quick iteration (no plugin changes)
npm run android:copy

# Open in Android Studio
npm run android:open

# Build release for Play Store
npm run android:build:release
# Output: android/app/build/outputs/bundle/release/app-release.aab

# Test on emulator
adb install -r android/app/build/outputs/apk/release/app-release.apk

# View logs
adb logcat | grep -i band
```

### Version Management

Edit `android/app/build.gradle` before each release:

```gradle
versionCode 1        // Increment by 1 for each release
versionName "1.0.0"  // Semantic versioning
```

### ⚠️ **CRITICAL: Keystore Backup**

The signing keystore (`android/release-key.jks`) is **irreplaceable**. If lost, you cannot update the app on Play Store.

**Backup locations:**
- Password manager
- Encrypted external drive
- Secure cloud storage

Also backup `android/keystore.properties` with passwords.

## Data Schema

### Band Positions (`band_positions.json`)

```typescript
{
  bands: Array<{
    name: string;
    slug: string;
    entries: Array<{
      year: number;
      division: string;
      rank: number;
      absolute_position: number;
      field_size: number;
      points?: number;
      conductor?: string;
      pieces: string[];
    }>;
  }>;
  metadata: {
    years: number[];
    divisions: string[];
    max_field_size: number;
    generated_at: string;
  };
}
```

### Streaming Links (`streaming/wind/2025.json`)

```typescript
{
  year: number;
  band_type: "wind" | "brass";
  entries: Array<{
    year: number;
    division: string;
    band: string;
    result_piece: string;
    spotify?: {
      track_name: string;
      artist: string;
      album: string;
      url: string;
      preview_url?: string;
    };
    apple_music?: {
      track_name: string;
      artist: string;
      album: string;
      url: string;
      preview_url?: string;
    };
  }>;
}
```

## Common Development Tasks

### Adding a New Feature

1. Create component in `src/lib/`
2. Import and use in `App.svelte`
3. Test in browser (`npm run dev`)
4. Test on iOS if relevant
5. Build and commit

### Updating Styles

CSS is component-scoped in Svelte. Global styles in:
- `src/app.css` - Global styles
- `<style>` blocks in .svelte files - Component styles

### Debugging

- **Browser**: Use browser DevTools with Svelte extension
- **iOS**: Use Safari Web Inspector (Develop menu)
- **Android**: Use `adb logcat` or Android Studio Logcat
- **Console logs**: `console.log()` works in all environments

### Building for Production

```bash
cd apps/band-positions
npm run build

# Output goes to docs/
# Commit and push to deploy via GitHub Pages
```

## Documentation

- **Main README**: [README.md](README.md)
- **iOS Setup**: [docs/START_HERE.md](docs/START_HERE.md)
- **iOS App Store Guide**: [docs/APP_STORE_GUIDE.md](docs/APP_STORE_GUIDE.md)
- **Android Play Store Guide**: [PLAY_STORE_GUIDE.md](PLAY_STORE_GUIDE.md)
- **Android Quick Ref**: [ANDROID_QUICK_REF.md](ANDROID_QUICK_REF.md)
- **Architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Related Repository

For data pipeline tasks (scraping, processing, exporting):
- **Repository**: [github.com/andersha/band_data](https://github.com/andersha/band_data) (private)
- **Documentation**: See `band_data/README.md` and `band_data/EXPORT.md`

## Deployment

### Web (GitHub Pages)

1. Build: `npm run build`
2. Commit: `git add docs/ && git commit -m "Update app"`
3. Push: `git push`
4. GitHub automatically deploys to [andersha.github.io/band_positions/](https://andersha.github.io/band_positions/)

### iOS (App Store)

See [docs/APP_STORE_CHECKLIST.md](docs/APP_STORE_CHECKLIST.md) for complete deployment guide.

### Android (Google Play Store)

See [PLAY_STORE_CHECKLIST.md](PLAY_STORE_CHECKLIST.md) for complete deployment guide.

Key steps:
1. Update version: `android/app/build.gradle` (versionCode + versionName)
2. Build: `npm run android:build:release`
3. Test: `adb install -r android/app/build/outputs/apk/release/app-release.apk`
4. Upload AAB: `android/app/build/outputs/bundle/release/app-release.aab`
5. Submit via [Play Console](https://play.google.com/console)

## Troubleshooting

### iOS Build Fails

- Check that you opened `.xcworkspace` not `.xcodeproj`
- Run `pod install` in `ios/App/` directory
- Clean build folder in Xcode (Shift+Cmd+K)

### Android Build Fails

- Clean build: `cd android && ./gradlew clean && cd ..`
- Verify keystore: `ls -l android/release-key.jks`
- Check keystore.properties exists and has correct passwords
- Clear Gradle cache: `rm -rf ~/.gradle/caches/`
- Sync project in Android Studio: File → Sync Project with Gradle Files

### Data Not Loading

- Check browser console for fetch errors
- Verify data files exist in `public/data/`
- Check file paths are correct (case-sensitive on iOS/Android)
- For Android: Check `adb logcat` for network/fetch errors
- Ensure INTERNET permission in AndroidManifest.xml

### Vite Build Errors

- Delete `node_modules/` and reinstall: `rm -rf node_modules && npm install`
- Clear Vite cache: `rm -rf .vite`
- Check for TypeScript errors: `npm run check`

## Key Files

- `src/App.svelte` - Main application
- `vite.config.ts` - Build configuration
- `capacitor.config.ts` - iOS and Android configuration
- `package.json` - Dependencies and scripts
- `android/app/build.gradle` - Android version and build config
- `android/release-key.jks` - Android signing keystore (⚠️ BACKUP!)
- `.gitignore` - Git ignore patterns
- `WARP.md` - This file

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and test
npm run dev

# Build and commit
npm run build
git add .
git commit -m "Add new feature"

# Push and create PR
git push origin feature/new-feature
```

## Notes for AI Assistants

- This repo contains ONLY the frontend app code
- Data processing is in a separate private `band_data` repository
- Do not suggest changes to data pipeline here
- Focus on UI, visualization, iOS app, and Android app improvements
- Data files in `public/data/` are generated externally
- Android keystore (`android/release-key.jks`) must be backed up - irreplaceable!
