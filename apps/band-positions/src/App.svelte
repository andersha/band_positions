<script lang="ts">
  import { preventDefault } from 'svelte/legacy';

  import { onMount } from 'svelte';
  import BandTrajectoryChart from './lib/BandTrajectoryChart.svelte';
  import DataExplorer from './lib/DataExplorer.svelte';
  import PiecePerformances from './lib/PiecePerformances.svelte';
  import { slugify } from './lib/slugify';
  import type { BandDataset, BandRecord, BandEntry, PieceRecord } from './lib/types';

  type ViewType = 'bands' | 'conductors' | 'pieces' | 'data';
  type Theme = 'light' | 'dark';

  const URL_PARAM_KEYS = { bands: 'band', conductors: 'conductor', pieces: 'piece' } as const;
  const URL_MODE_KEY = 'mode';
  const URL_VIEW_KEY = 'view';
  const URL_SEPARATOR = ',';
  const DEFAULT_MODE: 'absolute' | 'relative' = 'relative';
  const DEFAULT_VIEW: ViewType = 'bands';
  const THEME_STORAGE_KEY = 'nmjanitsjar-theme';

  const viewLabels: Record<ViewType, string> = {
    bands: 'Korps',
    conductors: 'Dirigent',
    pieces: 'Stykke',
    data: 'Resultat'
  };
  const viewOrder: ViewType[] = ['bands', 'conductors', 'pieces', 'data'];

  let dataset: BandDataset | null = $state(null);
  let conductorRecords: BandRecord[] = $state([]);
  let pieceRecords: PieceRecord[] = $state([]);
  let loading = $state(true);
  let error: string | null = $state(null);
  let searchTerm = $state('');
  let selectedBands: BandRecord[] = $state([]);
  let selectedConductors: BandRecord[] = $state([]);
  let selectedPieces: PieceRecord[] = $state([]);
  let focusedIndex = $state(-1);
  let initialUrlSyncDone = false;
  let lastSyncedSignature = '';
  let yAxisMode: 'absolute' | 'relative' = $state(DEFAULT_MODE);
  let activeView: ViewType = $state(DEFAULT_VIEW);
  let theme: Theme = $state('dark');

  type ConductorPlacement = BandEntry & { band_name?: string };
  type PiecePerformance = BandEntry & { band_name: string };

  function cloneEntry(entry: BandEntry, bandName?: string): ConductorPlacement {
    const clonedPieces = Array.isArray(entry.pieces)
      ? [...entry.pieces]
      : entry.pieces != null
        ? [`${entry.pieces}`.trim()].filter(Boolean)
        : [];

    const clone: ConductorPlacement = {
      ...entry,
      pieces: clonedPieces,
      conductor: entry.conductor
    };

    if (bandName) {
      clone.band_name = bandName;
    }

    return clone;
  }

  function buildConductorRecords(bands: BandRecord[]): BandRecord[] {
    const records = new Map<string, {
      name: string;
      slug: string;
      years: Map<number, { entries: ConductorPlacement[] }>;
    }>();

    for (const band of bands) {
      for (const entry of band.entries) {
        const rawName = entry.conductor?.trim();
        if (!rawName) continue;

        const slug = slugify(rawName);
        let record = records.get(slug);
        if (!record) {
          record = { name: rawName, slug, years: new Map() };
          records.set(slug, record);
        }

        let yearBucket = record.years.get(entry.year);
        if (!yearBucket) {
          yearBucket = { entries: [] };
          record.years.set(entry.year, yearBucket);
        }

        yearBucket.entries.push(cloneEntry(entry, band.name));
      }
    }

    return Array.from(records.values())
      .map((record) => ({
        name: record.name,
        slug: record.slug,
        entries: Array.from(record.years.entries())
          .map(([year, bucket]) => {
            const sortedEntries = [...bucket.entries].sort((a, b) => {
              const aPos = a.absolute_position ?? Number.POSITIVE_INFINITY;
              const bPos = b.absolute_position ?? Number.POSITIVE_INFINITY;
              if (aPos !== bPos) return aPos - bPos;
              return (a.rank ?? Number.POSITIVE_INFINITY) - (b.rank ?? Number.POSITIVE_INFINITY);
            });

            const primary = {
              ...sortedEntries[0],
              year,
              conductor: record.name,
              aggregate_entries: sortedEntries
            } satisfies ConductorPlacement & { aggregate_entries: ConductorPlacement[] };

            return primary;
          })
          .sort((a, b) => a.year - b.year)
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
  }

  function buildPieceRecords(bands: BandRecord[]): PieceRecord[] {
    const records = new Map<string, PieceRecord>();

    for (const band of bands) {
      for (const entry of band.entries) {
        const pieces = Array.isArray(entry.pieces)
          ? entry.pieces
          : entry.pieces != null
            ? [`${entry.pieces}`]
            : [];

        for (const rawPiece of pieces) {
          const name = rawPiece.trim();
          if (!name) continue;

          const slug = slugify(name);
          let record = records.get(slug);
          if (!record) {
            record = { name, slug, performances: [] };
            records.set(slug, record);
          }

          record.performances.push({ band: band.name, entry });
        }
      }
    }

    return Array.from(records.values()).map((record) => ({
      ...record,
      performances: record.performances.map(({ band, entry }) => ({
        band,
        entry: { ...entry, pieces: [...entry.pieces] }
      }))
    })).sort((a, b) => a.name.localeCompare(b.name));
  }

  function getUrlParamKey(view: ViewType): string {
    return URL_PARAM_KEYS[view];
  }

  function getModeFromURL(): 'absolute' | 'relative' {
    if (typeof window === 'undefined') return DEFAULT_MODE;
    const params = new URLSearchParams(window.location.search);
    const raw = params.get(URL_MODE_KEY);
    const normalized = raw ? raw.toLowerCase() : null;
    return normalized === 'absolute' ? 'absolute' : 'relative';
  }

  function resolveInitialTheme(): Theme {
    if (typeof window === 'undefined') return 'dark';
    try {
      const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
      if (stored === 'light' || stored === 'dark') {
        return stored;
      }
    } catch (err) {
      console.error('Kunne ikke lese lagret tema', err);
    }
    const prefersLight = window.matchMedia?.('(prefers-color-scheme: light)').matches;
    return prefersLight ? 'light' : 'dark';
  }

  function applyThemePreference(nextTheme: Theme): void {
    if (typeof document === 'undefined') return;
    if (nextTheme === 'dark') {
      document.documentElement.removeAttribute('data-theme');
    } else {
      document.documentElement.dataset.theme = 'light';
    }
  }

  function setTheme(nextTheme: Theme): void {
    theme = nextTheme;
    applyThemePreference(nextTheme);
    if (typeof window !== 'undefined') {
      try {
        window.localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
      } catch (err) {
        console.error('Kunne ikke lagre tema', err);
      }
    }
  }

  function toggleTheme(): void {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  }

  function getViewFromURL(): ViewType {
    if (typeof window === 'undefined') return DEFAULT_VIEW;
    const params = new URLSearchParams(window.location.search);
    const raw = params.get(URL_VIEW_KEY)?.toLowerCase();
    if (!raw) return DEFAULT_VIEW;
    if (raw === 'conductors' || raw === 'dirigent' || raw === 'conductor') {
      return 'conductors';
    }
    if (raw === 'pieces' || raw === 'piece' || raw === 'stykke' || raw === 'stykker') {
      return 'pieces';
    }
    if (raw === 'data' || raw === 'resultat' || raw === 'results') {
      return 'data';
    }
    return 'bands';
  }

  function getSlugsFromURL(view: ViewType): string[] {
    if (typeof window === 'undefined') return [];
    const params = new URLSearchParams(window.location.search);
    const raw = params.get(getUrlParamKey(view));
    if (!raw) return [];
    return raw
      .split(URL_SEPARATOR)
      .map((slug) => decodeURIComponent(slug.trim()))
      .filter(Boolean);
  }

  function findMatches<T extends { slug: string }>(records: T[], slugs: string[]): T[] {
    if (!records.length || !slugs.length) return [];
    const recordMap = new Map(records.map((record) => [record.slug, record] as const));
    return slugs
      .map((slug) => recordMap.get(slug) ?? recordMap.get(slug.toLowerCase()))
      .filter((record): record is T => Boolean(record));
  }

  function areSelectionsEqual<T extends { slug: string }>(a: T[], b: T[]): boolean {
    if (a.length !== b.length) return false;
    return a.every((record, index) => record.slug === b[index].slug);
  }

  function updateUrlState(): void {
    if (typeof window === 'undefined') return;
    const params = new URLSearchParams(window.location.search);

    const bandSlugs = selectedBands.map((band) => encodeURIComponent(band.slug)).join(URL_SEPARATOR);
    if (bandSlugs.length) {
      params.set(getUrlParamKey('bands'), bandSlugs);
    } else {
      params.delete(getUrlParamKey('bands'));
    }

    const conductorSlugs = selectedConductors
      .map((conductor) => encodeURIComponent(conductor.slug))
      .join(URL_SEPARATOR);
    if (conductorSlugs.length) {
      params.set(getUrlParamKey('conductors'), conductorSlugs);
    } else {
      params.delete(getUrlParamKey('conductors'));
    }

    const pieceSlugs = selectedPieces.map((piece) => encodeURIComponent(piece.slug)).join(URL_SEPARATOR);
    if (pieceSlugs.length) {
      params.set(getUrlParamKey('pieces'), pieceSlugs);
    } else {
      params.delete(getUrlParamKey('pieces'));
    }

    params.set(URL_MODE_KEY, yAxisMode);
    params.set(URL_VIEW_KEY, activeView);

    const query = params.toString();
    const newUrl = `${window.location.pathname}${query ? `?${query}` : ''}${window.location.hash}`;
    window.history.replaceState({}, '', newUrl);
  }

  function syncSelectionFromURL({ updateHistory = false } = {}): boolean {
    const modeFromUrl = getModeFromURL();
    const viewFromUrl = getViewFromURL();
    let stateChanged = false;

    if (modeFromUrl !== yAxisMode) {
      yAxisMode = modeFromUrl;
      stateChanged = true;
    }
    if (viewFromUrl !== activeView) {
      activeView = viewFromUrl;
      stateChanged = true;
    }

    if (!dataset) {
      if (updateHistory) updateUrlState();
      return stateChanged;
    }

    const bandMatches = findMatches(dataset.bands, getSlugsFromURL('bands'));
    if (!areSelectionsEqual(selectedBands, bandMatches)) {
      selectedBands = bandMatches;
      stateChanged = true;
    }

    if (!conductorRecords.length) {
      conductorRecords = buildConductorRecords(dataset.bands);
    }
    const conductorMatches = findMatches(conductorRecords, getSlugsFromURL('conductors'));
    if (!areSelectionsEqual(selectedConductors, conductorMatches)) {
      selectedConductors = conductorMatches;
      stateChanged = true;
    }

    if (!pieceRecords.length) {
      pieceRecords = buildPieceRecords(dataset.bands);
    }
    const pieceMatches = findMatches(pieceRecords, getSlugsFromURL('pieces'));
    if (!areSelectionsEqual(selectedPieces, pieceMatches)) {
      selectedPieces = pieceMatches;
      stateChanged = true;
    }

    if (updateHistory) {
      updateUrlState();
    }

    return stateChanged;
  }

  function getSelectedSignature(): string {
    const bandSignature = selectedBands.map((band) => band.slug).join(URL_SEPARATOR);
    const conductorSignature = selectedConductors.map((conductor) => conductor.slug).join(URL_SEPARATOR);
    const pieceSignature = selectedPieces.map((piece) => piece.slug).join(URL_SEPARATOR);
    return `${activeView}|${yAxisMode}|${bandSignature}|${conductorSignature}|${pieceSignature}`;
  }

  function syncUrlIfReady(): void {
    if (!initialUrlSyncDone) return;
    const signature = getSelectedSignature();
    if (signature !== lastSyncedSignature) {
      updateUrlState();
      lastSyncedSignature = signature;
    }
  }

  function chooseRecord(record: BandRecord | PieceRecord): void {
    if (activeView === 'bands') {
      if (selectedBands.some((item) => item.slug === record.slug)) return;
      selectedBands = [...selectedBands, record];
    } else if (activeView === 'conductors') {
      if (selectedConductors.some((item) => item.slug === record.slug)) return;
      selectedConductors = [...selectedConductors, record];
    } else {
      const pieceRecord = record as PieceRecord;
      if (selectedPieces.some((item) => item.slug === pieceRecord.slug)) return;
      selectedPieces = [...selectedPieces, pieceRecord];
    }
    searchTerm = '';
    focusedIndex = -1;
    syncUrlIfReady();
  }

  function removeRecord(slug: string): void {
    if (activeView === 'bands') {
      selectedBands = selectedBands.filter((item) => item.slug !== slug);
    } else if (activeView === 'conductors') {
      selectedConductors = selectedConductors.filter((item) => item.slug !== slug);
    } else {
      selectedPieces = selectedPieces.filter((item) => item.slug !== slug);
    }
    focusedIndex = -1;
    syncUrlIfReady();
  }

  function handleSubmit(): void {
    if (trimmed.length === 0) return;
    const exact = activeRecords.find((record) => record.name.toLowerCase() === lowered);
    if (exact) {
      chooseRecord(exact);
    } else if (suggestions.length > 0) {
      chooseRecord(suggestions[0]);
    }
  }

  function onInput(event: Event): void {
    searchTerm = (event.target as HTMLInputElement).value;
    focusedIndex = -1;
  }

  function handleKeyDown(event: KeyboardEvent): void {
    if (!suggestions.length) return;
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      focusedIndex = (focusedIndex + 1) % suggestions.length;
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      focusedIndex = (focusedIndex - 1 + suggestions.length) % suggestions.length;
    } else if (event.key === 'Enter' && focusedIndex >= 0) {
      event.preventDefault();
      chooseRecord(suggestions[focusedIndex]);
    }
  }

  function setView(view: ViewType): void {
    if (view === activeView) return;
    activeView = view;
    searchTerm = '';
    focusedIndex = -1;
    syncUrlIfReady();
  }

  function setYAxisMode(mode: 'absolute' | 'relative'): void {
    if (yAxisMode === mode) return;
    yAxisMode = mode;
    syncUrlIfReady();
  }

  onMount(async () => {
    try {
      const initialTheme = resolveInitialTheme();
      theme = initialTheme;
      applyThemePreference(initialTheme);
      const response = await fetch('data/band_positions.json');
      if (!response.ok) {
        throw new Error(`Kunne ikke laste data (status ${response.status})`);
      }
      dataset = (await response.json()) as BandDataset;
      conductorRecords = buildConductorRecords(dataset.bands);
      pieceRecords = buildPieceRecords(dataset.bands);
      syncSelectionFromURL({ updateHistory: false });
      lastSyncedSignature = getSelectedSignature();
      updateUrlState();
      initialUrlSyncDone = true;
    } catch (err) {
      error = err instanceof Error ? err.message : 'Ukjent feil ved lasting av data.';
    } finally {
      loading = false;
    }
  });

  onMount(() => {
    const handlePopState = () => {
      if (!dataset) return;
      syncSelectionFromURL({ updateHistory: false });
      lastSyncedSignature = getSelectedSignature();
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  });

  let trimmed = $derived(searchTerm.trim());
  let lowered = $derived(trimmed.toLowerCase());
  let isEntityView = $derived(activeView === 'bands' || activeView === 'conductors' || activeView === 'pieces');
  let activeRecords = $derived(isEntityView
    ? activeView === 'bands'
      ? dataset?.bands ?? []
      : activeView === 'conductors'
        ? conductorRecords
        : pieceRecords
    : []);
  let activeSelection = $derived(activeView === 'bands'
    ? selectedBands
    : activeView === 'conductors'
      ? selectedConductors
      : activeView === 'pieces'
        ? selectedPieces
        : []);
  let suggestions =
    $derived(isEntityView && activeRecords && lowered.length >= 2
      ? activeRecords
          .filter(
            (record) =>
              record.name.toLowerCase().includes(lowered) &&
              !activeSelection.some((selected) => selected.slug === record.slug)
          )
          .slice(0, 10)
      : []);

  let years = $derived(dataset ? dataset.metadata.years : []);
  let maxFieldSize = $derived(dataset ? dataset.metadata.max_field_size : 0);
  let entityCount = $derived(isEntityView
    ? activeView === 'bands'
      ? dataset?.bands.length ?? 0
      : activeView === 'conductors'
        ? conductorRecords.length
        : pieceRecords.length
    : 0);
  let entityLabel = $derived(activeView === 'bands'
    ? 'korps'
    : activeView === 'conductors'
      ? 'dirigenter'
      : 'stykker');
  let coverageDescription = $derived(dataset
    ? `Dekker ${entityCount} ${entityLabel} · ${years.length} år (${dataset.metadata.min_year}–${dataset.metadata.max_year})`
    : '');

  let searchPlaceholder = $derived(activeView === 'bands'
    ? 'Begynn å skrive et korpsnavn (minst 2 bokstaver)…'
    : activeView === 'conductors'
      ? 'Begynn å skrive et dirigentnavn (minst 2 bokstaver)…'
      : activeView === 'pieces'
        ? 'Begynn å skrive en stykketittel (minst 2 bokstaver)…'
        : '');
  let searchLabel = $derived(activeView === 'bands'
    ? 'Søk etter korps'
    : activeView === 'conductors'
      ? 'Søk etter dirigent'
      : 'Søk etter musikkstykke');
  let suggestionsLabel = $derived(activeView === 'bands'
    ? 'Korpsforslag'
    : activeView === 'conductors'
      ? 'Dirigentforslag'
      : 'Stykke-forslag');
  let selectionLabel = $derived(activeView === 'bands'
    ? 'Valgte korps'
    : activeView === 'conductors'
      ? 'Valgte dirigenter'
      : 'Valgte stykker');
  let emptyStateTitle = $derived(activeView === 'bands'
    ? 'Ingen korps valgt ennå'
    : activeView === 'conductors'
      ? 'Ingen dirigenter valgt ennå'
      : 'Ingen stykker valgt ennå');
  let emptyStateBody = $derived(activeView === 'bands'
    ? 'Finn et navn i søkefeltet for å tegne kurven for samlet plassering.'
    : activeView === 'conductors'
      ? 'Finn en dirigent i søkefeltet for å tegne kurven for samlet plassering.'
      : 'Finn et musikkstykke i søkefeltet for å se alle registrerte fremføringer.');
  let leadText = $derived(activeView === 'bands'
    ? 'Søk etter et janitsjarkorps for å se hvordan den samlede plasseringen utvikler seg år for år, på tvers av alle divisjoner.'
    : activeView === 'conductors'
      ? 'Søk etter en dirigent for å se hvordan deres beste plassering utvikler seg år for år, basert på korpsene de dirigerte.'
      : activeView === 'pieces'
        ? 'Søk etter et musikkstykke for å se alle fremføringer vi har registrert.'
        : 'Velg et år og en divisjon for å vise resultatlisten i den valgte finalen.');
  let themeToggleLabel = $derived(theme === 'dark' ? 'Bytt til lyst tema' : 'Bytt til mørkt tema');
  let themeToggleText = $derived(theme === 'dark' ? 'Mørk' : 'Lys');
  let themeToggleIcon = $derived(theme === 'dark' ? '🌙' : '☀️');

  let chartHeading =
    $derived(activeSelection.length === 1
      ? activeSelection[0].name
      : activeSelection.length > 1
        ? `${activeSelection.length} ${entityLabel} valgt`
        : '');

  let comparisonSummary =
    $derived(activeSelection.length > 1 ? activeSelection.map((record) => record.name).join(' · ') : '');

  let pieceSelection = $derived(activeView === 'pieces' ? (activeSelection as PieceRecord[]) : []);
  let chartSelection =
    $derived(activeView === 'bands' || activeView === 'conductors'
      ? (activeSelection as BandRecord[])
      : []);
</script>

<main>
  <header class="page-header">
    <h1>NM Janitsjar</h1>
    <div class="header-controls">
      <div class="view-toggle" role="group" aria-label="Bytt visning">
        {#each viewOrder as view}
          <button
            type="button"
            class:selected={activeView === view}
            aria-pressed={activeView === view}
            onclick={() => setView(view)}
          >
            {viewLabels[view]}
          </button>
        {/each}
      </div>
      <button
        class="theme-toggle"
        type="button"
        onclick={toggleTheme}
        aria-label={themeToggleLabel}
      >
        <span aria-hidden="true">{themeToggleIcon}</span>
        <span class="theme-toggle__text">{themeToggleText}</span>
      </button>
    </div>
  </header>
  <p class="lead">{leadText}</p>

  {#if isEntityView}
    <form class="search" onsubmit={preventDefault(handleSubmit)}>
      <label class="sr-only" for="entity-search">{searchLabel}</label>
      <input
        id="entity-search"
        type="search"
        placeholder={searchPlaceholder}
        bind:value={searchTerm}
        oninput={onInput}
        onkeydown={handleKeyDown}
        autocomplete="off"
      />
    </form>

    {#if activeSelection.length > 0}
      <div class="selected-entities" role="list" aria-label={selectionLabel}>
        {#each activeSelection as record, index}
          <span class="selected-entity" role="listitem">
            <span class="selected-entity__index">{index + 1}</span>
            <span class="selected-entity__name">{record.name}</span>
            <button type="button" aria-label={`Fjern ${record.name}`} onclick={() => removeRecord(record.slug)}>
              ×
            </button>
          </span>
        {/each}
      </div>
    {/if}

    {#if suggestions.length > 0}
      <div class="suggestions" role="listbox" aria-label={suggestionsLabel}>
        {#each suggestions as record, index}
          <div
            class="suggestion {index === focusedIndex ? 'active' : ''}"
            role="option"
            tabindex="-1"
            aria-selected={index === focusedIndex}
            onmousedown={preventDefault(() => chooseRecord(record))}
          >
            {record.name}
          </div>
        {/each}
      </div>
    {/if}
  {/if}

  {#if loading}
    <section class="status">Laster data…</section>
  {:else if error}
    <section class="status error">{error}</section>
  {:else if !dataset}
    <section class="status">Ingen data tilgjengelig.</section>
  {:else if isEntityView}
    {#if activeSelection.length > 0}
      {#if activeView === 'pieces'}
        <PiecePerformances pieces={pieceSelection} />
      {:else}
        <section class="chart-card">
          <div class="mode-toggle">
            <span class="mode-toggle__label">Plassering:</span>
            <div class="mode-toggle__buttons" role="group" aria-label="Velg plasseringsvisning">
              <button
                type="button"
                class:selected={yAxisMode === 'absolute'}
                aria-pressed={yAxisMode === 'absolute'}
                onclick={() => setYAxisMode('absolute')}
              >
                Absolutt
              </button>
              <button
                type="button"
                class:selected={yAxisMode === 'relative'}
                aria-pressed={yAxisMode === 'relative'}
                onclick={() => setYAxisMode('relative')}
              >
                Relativ
              </button>
            </div>
          </div>
          <div class="chart-header">
            <h2>{chartHeading}</h2>
            <p>{coverageDescription}</p>
            {#if comparisonSummary}
              <p class="comparison-summary">{comparisonSummary}</p>
            {/if}
          </div>
          <BandTrajectoryChart
            {years}
            {maxFieldSize}
            bands={chartSelection}
            yMode={yAxisMode}
            showConductorMarkers={activeView === 'bands'}
          />
        </section>
      {/if}
    {:else}
      <section class="empty-state">
        <h2>{emptyStateTitle}</h2>
        <p>{emptyStateBody}</p>
      </section>
    {/if}
  {:else}
    <DataExplorer {dataset} />
  {/if}
</main>

<style>
  main {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 1rem;
  }

  h1 {
    margin: 0;
    font-size: 2rem;
    color: var(--color-text-primary);
  }

  .lead {
    margin: 0;
    color: var(--color-text-secondary);
  }

  .header-controls {
    display: inline-flex;
    align-items: center;
    gap: 0.75rem;
  }

  .view-toggle {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.25rem;
    background: var(--color-mode-toggle-bg);
    border-radius: 999px;
    border: 1px solid var(--color-mode-toggle-border);
  }

  .view-toggle button {
    appearance: none;
    border: none;
    background: transparent;
    color: var(--color-text-secondary);
    padding: 0.4rem 1.1rem;
    border-radius: 999px;
    font-size: 0.9rem;
    cursor: pointer;
    transition: background 0.18s ease, color 0.18s ease;
  }

  .view-toggle button:hover {
    color: var(--color-text-primary);
  }

  .view-toggle button.selected {
    background: var(--color-accent-strong);
    color: var(--color-text-primary);
    font-weight: 600;
  }

  .view-toggle button:focus-visible {
    outline: 2px solid var(--color-accent);
    outline-offset: 2px;
  }

  .theme-toggle {
    appearance: none;
    border: 1px solid var(--color-mode-toggle-border);
    background: var(--color-mode-toggle-bg);
    color: var(--color-text-secondary);
    border-radius: 999px;
    padding: 0.35rem 0.9rem;
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.85rem;
    cursor: pointer;
    transition: background 0.18s ease, color 0.18s ease, border 0.18s ease;
  }

  .theme-toggle:hover {
    color: var(--color-text-primary);
    border-color: var(--color-accent);
  }

  .theme-toggle:focus-visible {
    outline: 2px solid var(--color-accent);
    outline-offset: 2px;
  }

  .theme-toggle__text {
    font-weight: 600;
  }

  .search {
    position: relative;
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

  .selected-entities {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.75rem;
  }

  .selected-entity {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.3rem 0.6rem;
    border-radius: 999px;
    background: var(--color-chip-bg);
    border: 1px solid var(--color-chip-border);
    color: var(--color-text-primary);
    font-size: 0.85rem;
  }

  .selected-entity__index {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.45rem;
    height: 1.45rem;
    border-radius: 50%;
    background: var(--color-chip-index-bg);
    font-size: 0.75rem;
  }

  .selected-entity button {
    border: none;
    background: transparent;
    color: var(--color-text-secondary);
    cursor: pointer;
    font-size: 1rem;
    padding: 0;
    line-height: 1;
  }

  .selected-entity button:hover {
    color: var(--color-warning);
  }

  .selected-entity__name {
    white-space: nowrap;
  }

  .status {
    margin-top: 2rem;
    color: var(--color-text-secondary);
  }

  .status.error {
    color: var(--color-warning);
  }

  .suggestions {
    display: flex;
    flex-direction: column;
    margin-top: 0.75rem;
    border: 1px solid var(--color-border);
    border-radius: 0.6rem;
    overflow: hidden;
    background: var(--color-surface-elevated);
  }

  .suggestion {
    padding: 0.5rem 0.75rem;
    cursor: pointer;
  }

  .suggestion:hover,
  .suggestion.active {
    background: var(--color-accent-strong);
  }

  .empty-state {
    margin-top: 3rem;
    text-align: center;
    color: var(--color-text-muted);
  }

  .chart-card {
    margin-top: 2.5rem;
    padding: 1.5rem;
    background: var(--color-surface-card);
    border-radius: 1rem;
    border: 1px solid var(--color-border);
    box-shadow: 0 18px 40px rgba(15, 23, 42, 0.35);
    position: relative;
  }

  .chart-header {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    margin-bottom: 1.25rem;
    padding-right: 8rem;
  }

  .chart-header h2 {
    margin: 0;
    font-size: 1.45rem;
    color: var(--color-accent);
  }

  .chart-header p {
    margin: 0;
    color: var(--color-text-secondary);
  }

  .comparison-summary {
    color: var(--color-text-muted);
    font-size: 0.85rem;
  }

  .mode-toggle {
    position: absolute;
    top: 1rem;
    right: 1.25rem;
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-size: 0.85rem;
    color: var(--color-text-secondary);
  }

  .mode-toggle__label {
    font-weight: 600;
    color: var(--color-text-primary);
  }

  .mode-toggle__buttons {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.25rem;
    border-radius: 999px;
    background: var(--color-mode-toggle-bg);
    border: 1px solid var(--color-mode-toggle-border);
  }

  .mode-toggle button {
    appearance: none;
    background: transparent;
    border: none;
    color: var(--color-text-secondary);
    padding: 0.35rem 0.9rem;
    cursor: pointer;
    border-radius: 999px;
    font-size: inherit;
    line-height: 1.2;
    transition: background 0.18s ease, color 0.18s ease;
  }

  .mode-toggle button:hover {
    color: var(--color-text-primary);
  }

  .mode-toggle button.selected {
    background: var(--color-accent-strong);
    color: var(--color-text-primary);
    font-weight: 600;
  }

  .mode-toggle button:focus-visible {
    outline: 2px solid var(--color-accent);
    outline-offset: 2px;
    border-radius: 4px;
  }

  @media (max-width: 640px) {
    .chart-header {
      padding-right: 0;
    }

    .mode-toggle {
      position: static;
      justify-content: flex-end;
      margin-bottom: 1rem;
    }

    .header-controls {
      width: 100%;
      justify-content: flex-end;
    }
  }
</style>
