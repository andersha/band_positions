<script lang="ts">
  import { onMount } from 'svelte';
  import BandTrajectoryChart from './lib/BandTrajectoryChart.svelte';
  import type { BandDataset, BandRecord, BandEntry } from './lib/types';

  type ViewType = 'bands' | 'conductors';

  const URL_PARAM_KEYS = { bands: 'band', conductors: 'conductor' } as const;
  const URL_MODE_KEY = 'mode';
  const URL_VIEW_KEY = 'view';
  const URL_SEPARATOR = ',';
  const DEFAULT_MODE: 'absolute' | 'relative' = 'relative';
  const DEFAULT_VIEW: ViewType = 'bands';

  const viewLabels: Record<ViewType, string> = {
    bands: 'Korps',
    conductors: 'Dirigent'
  };
  const viewOrder: ViewType[] = ['bands', 'conductors'];

  let dataset: BandDataset | null = null;
  let conductorRecords: BandRecord[] = [];
  let loading = true;
  let error: string | null = null;
  let searchTerm = '';
  let selectedBands: BandRecord[] = [];
  let selectedConductors: BandRecord[] = [];
  let focusedIndex = -1;
  let initialUrlSyncDone = false;
  let lastSyncedSignature = '';
  let yAxisMode: 'absolute' | 'relative' = DEFAULT_MODE;
  let activeView: ViewType = DEFAULT_VIEW;
  let activeRecords: BandRecord[] = [];
  let activeSelection: BandRecord[] = [];

  function slugify(value: string): string {
    return (
      value
        .normalize('NFKD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase()
        .trim()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '') || 'uidentifisert'
    );
  }

  type ConductorPlacement = BandEntry & { band_name?: string };

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

  function getViewFromURL(): ViewType {
    if (typeof window === 'undefined') return DEFAULT_VIEW;
    const params = new URLSearchParams(window.location.search);
    const raw = params.get(URL_VIEW_KEY)?.toLowerCase();
    if (!raw) return DEFAULT_VIEW;
    if (raw === 'conductors' || raw === 'dirigent' || raw === 'conductor') {
      return 'conductors';
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

  function findMatches(records: BandRecord[], slugs: string[]): BandRecord[] {
    if (!records.length || !slugs.length) return [];
    const recordMap = new Map(records.map((record) => [record.slug, record] as const));
    return slugs
      .map((slug) => recordMap.get(slug) ?? recordMap.get(slug.toLowerCase()))
      .filter((record): record is BandRecord => Boolean(record));
  }

  function areSelectionsEqual(a: BandRecord[], b: BandRecord[]): boolean {
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

    params.set(URL_MODE_KEY, yAxisMode);
    params.set(URL_VIEW_KEY, activeView === 'conductors' ? 'conductors' : 'bands');

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

    if (updateHistory) {
      updateUrlState();
    }

    return stateChanged;
  }

  function getSelectedSignature(): string {
    const bandSignature = selectedBands.map((band) => band.slug).join(URL_SEPARATOR);
    const conductorSignature = selectedConductors.map((conductor) => conductor.slug).join(URL_SEPARATOR);
    return `${activeView}|${yAxisMode}|${bandSignature}|${conductorSignature}`;
  }

  function chooseRecord(record: BandRecord): void {
    if (activeView === 'bands') {
      if (selectedBands.some((item) => item.slug === record.slug)) return;
      selectedBands = [...selectedBands, record];
    } else {
      if (selectedConductors.some((item) => item.slug === record.slug)) return;
      selectedConductors = [...selectedConductors, record];
    }
    searchTerm = '';
    focusedIndex = -1;
  }

  function removeRecord(slug: string): void {
    if (activeView === 'bands') {
      selectedBands = selectedBands.filter((item) => item.slug !== slug);
    } else {
      selectedConductors = selectedConductors.filter((item) => item.slug !== slug);
    }
    focusedIndex = -1;
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
  }

  onMount(async () => {
    try {
      const response = await fetch('data/band_positions.json');
      if (!response.ok) {
        throw new Error(`Kunne ikke laste data (status ${response.status})`);
      }
      dataset = (await response.json()) as BandDataset;
      conductorRecords = buildConductorRecords(dataset.bands);
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

  $: trimmed = searchTerm.trim();
  $: lowered = trimmed.toLowerCase();
  $: activeRecords = activeView === 'bands' ? dataset?.bands ?? [] : conductorRecords;
  $: activeSelection = activeView === 'bands' ? selectedBands : selectedConductors;
  $: suggestions =
    activeRecords && lowered.length >= 2
      ? activeRecords
          .filter(
            (record) =>
              record.name.toLowerCase().includes(lowered) &&
              !activeSelection.some((selected) => selected.slug === record.slug)
          )
          .slice(0, 10)
      : [];

  $: years = dataset ? dataset.metadata.years : [];
  $: maxFieldSize = dataset ? dataset.metadata.max_field_size : 0;
  $: entityCount = activeView === 'bands' ? dataset?.bands.length ?? 0 : conductorRecords.length;
  $: entityLabel = activeView === 'bands' ? 'korps' : 'dirigenter';
  let coverageDescription = '';
  $: coverageDescription = dataset
    ? `Dekker ${entityCount} ${entityLabel} · ${years.length} år (${dataset.metadata.min_year}–${dataset.metadata.max_year})`
    : '';

  $: searchPlaceholder =
    activeView === 'bands'
      ? 'Begynn å skrive et korpsnavn (minst 2 bokstaver)…'
      : 'Begynn å skrive et dirigentnavn (minst 2 bokstaver)…';
  $: searchLabel = activeView === 'bands' ? 'Søk etter korps' : 'Søk etter dirigent';
  $: suggestionsLabel = activeView === 'bands' ? 'Korpsforslag' : 'Dirigentforslag';
  $: selectionLabel = activeView === 'bands' ? 'Valgte korps' : 'Valgte dirigenter';
  $: emptyStateTitle = activeView === 'bands' ? 'Ingen korps valgt ennå' : 'Ingen dirigenter valgt ennå';
  $: emptyStateBody =
    activeView === 'bands'
      ? 'Finn et navn i søkefeltet for å tegne kurven for samlet plassering.'
      : 'Finn en dirigent i søkefeltet for å tegne kurven for samlet plassering.';
  $: leadText =
    activeView === 'bands'
      ? 'Søk etter et janitsjarkorps for å se hvordan den samlede plasseringen utvikler seg år for år, på tvers av alle divisjoner.'
      : 'Søk etter en dirigent for å se hvordan deres beste plassering utvikler seg år for år, basert på korpsene de dirigerte.';

  $: if (initialUrlSyncDone) {
    const signature = getSelectedSignature();
    if (signature !== lastSyncedSignature) {
      updateUrlState();
      lastSyncedSignature = signature;
    }
  }

  $: chartHeading =
    activeSelection.length === 1
      ? activeSelection[0].name
      : activeSelection.length > 1
        ? `${activeSelection.length} ${entityLabel} valgt`
        : '';

  $: comparisonSummary =
    activeSelection.length > 1 ? activeSelection.map((record) => record.name).join(' · ') : '';
</script>

<main>
  <header class="page-header">
    <h1>NM Janitsjar: Plassering over tid</h1>
    <div class="view-toggle" role="group" aria-label="Bytt mellom korps- og dirigentvisning">
      {#each viewOrder as view}
        <button
          type="button"
          class:selected={activeView === view}
          aria-pressed={activeView === view}
          on:click={() => setView(view)}
        >
          {viewLabels[view]}
        </button>
      {/each}
    </div>
  </header>
  <p class="lead">{leadText}</p>

  <form class="search" on:submit|preventDefault={handleSubmit}>
    <label class="sr-only" for="entity-search">{searchLabel}</label>
    <input
      id="entity-search"
      type="search"
      placeholder={searchPlaceholder}
      bind:value={searchTerm}
      on:input={onInput}
      on:keydown={handleKeyDown}
      autocomplete="off"
    />
  </form>

  {#if activeSelection.length > 0}
    <div class="selected-entities" role="list" aria-label={selectionLabel}>
      {#each activeSelection as record, index}
        <span class="selected-entity" role="listitem">
          <span class="selected-entity__index">{index + 1}</span>
          <span class="selected-entity__name">{record.name}</span>
          <button type="button" aria-label={`Fjern ${record.name}`} on:click={() => removeRecord(record.slug)}>
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
          on:mousedown|preventDefault={() => chooseRecord(record)}
        >
          {record.name}
        </div>
      {/each}
    </div>
  {/if}

  {#if loading}
    <section class="status">Laster data…</section>
  {:else if error}
    <section class="status error">{error}</section>
  {:else if activeSelection.length > 0}
    <section class="chart-card">
      <div class="mode-toggle">
        <span class="mode-toggle__label">Plassering:</span>
        <div class="mode-toggle__buttons" role="group" aria-label="Velg plasseringsvisning">
          <button
            type="button"
            class:selected={yAxisMode === 'absolute'}
            aria-pressed={yAxisMode === 'absolute'}
            on:click={() => (yAxisMode = 'absolute')}
          >
            Absolutt
          </button>
          <button
            type="button"
            class:selected={yAxisMode === 'relative'}
            aria-pressed={yAxisMode === 'relative'}
            on:click={() => (yAxisMode = 'relative')}
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
        bands={activeSelection}
        yMode={yAxisMode}
        showConductorMarkers={activeView === 'bands'}
      />
    </section>
  {:else}
    <section class="empty-state">
      <h2>{emptyStateTitle}</h2>
      <p>{emptyStateBody}</p>
    </section>
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
    color: #e0f2fe;
  }

  .lead {
    margin: 0;
    color: rgba(226, 232, 240, 0.8);
  }

  .view-toggle {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.25rem;
    background: rgba(15, 23, 42, 0.65);
    border-radius: 999px;
    border: 1px solid rgba(59, 130, 246, 0.35);
  }

  .view-toggle button {
    appearance: none;
    border: none;
    background: transparent;
    color: rgba(226, 232, 240, 0.75);
    padding: 0.4rem 1.1rem;
    border-radius: 999px;
    font-size: 0.9rem;
    cursor: pointer;
    transition: background 0.18s ease, color 0.18s ease;
  }

  .view-toggle button:hover {
    color: rgba(226, 232, 240, 0.95);
  }

  .view-toggle button.selected {
    background: rgba(59, 130, 246, 0.35);
    color: #e0f2fe;
    font-weight: 600;
  }

  .view-toggle button:focus-visible {
    outline: 2px solid rgba(59, 130, 246, 0.65);
    outline-offset: 2px;
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

  .search input {
    width: 100%;
    padding: 0.9rem 1.1rem;
    border-radius: 0.9rem;
    border: 1px solid rgba(148, 163, 184, 0.25);
    background: rgba(15, 23, 42, 0.85);
    color: #e2e8f0;
    font-size: 1rem;
    transition: border 0.15s ease, box-shadow 0.15s ease;
  }

  .search input:focus {
    outline: none;
    border-color: rgba(59, 130, 246, 0.75);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
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
    background: rgba(59, 130, 246, 0.16);
    border: 1px solid rgba(59, 130, 246, 0.35);
    color: #e0f2fe;
    font-size: 0.85rem;
  }

  .selected-entity__index {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.45rem;
    height: 1.45rem;
    border-radius: 50%;
    background: rgba(59, 130, 246, 0.45);
    font-size: 0.75rem;
  }

  .selected-entity button {
    border: none;
    background: transparent;
    color: rgba(226, 232, 240, 0.85);
    cursor: pointer;
    font-size: 1rem;
    padding: 0;
    line-height: 1;
  }

  .selected-entity button:hover {
    color: #fca5a5;
  }

  .selected-entity__name {
    white-space: nowrap;
  }

  .status {
    margin-top: 2rem;
    color: rgba(226, 232, 240, 0.8);
  }

  .status.error {
    color: #fca5a5;
  }

  .suggestions {
    display: flex;
    flex-direction: column;
    margin-top: 0.75rem;
    border: 1px solid rgba(148, 163, 184, 0.25);
    border-radius: 0.6rem;
    overflow: hidden;
    background: rgba(15, 23, 42, 0.85);
  }

  .suggestion {
    padding: 0.5rem 0.75rem;
    cursor: pointer;
  }

  .suggestion:hover {
    background: rgba(59, 130, 246, 0.2);
  }

  .suggestion.active {
    background-color: rgba(59, 130, 246, 0.25);
  }

  .empty-state {
    margin-top: 3rem;
    text-align: center;
    color: rgba(226, 232, 240, 0.75);
  }

  .chart-card {
    margin-top: 2.5rem;
    padding: 1.5rem;
    background: rgba(15, 23, 42, 0.85);
    border-radius: 1rem;
    border: 1px solid rgba(148, 163, 184, 0.2);
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
    color: #38bdf8;
  }

  .chart-header p {
    margin: 0;
    color: rgba(226, 232, 240, 0.7);
  }

  .comparison-summary {
    color: rgba(148, 163, 184, 0.85);
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
    color: rgba(226, 232, 240, 0.8);
  }

  .mode-toggle__label {
    font-weight: 600;
    color: rgba(226, 232, 240, 0.85);
  }

  .mode-toggle__buttons {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.25rem;
    border-radius: 999px;
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(59, 130, 246, 0.35);
  }

  .mode-toggle button {
    appearance: none;
    background: transparent;
    border: none;
    color: rgba(226, 232, 240, 0.7);
    padding: 0.35rem 0.9rem;
    cursor: pointer;
    border-radius: 999px;
    font-size: inherit;
    line-height: 1.2;
    transition: background 0.18s ease, color 0.18s ease;
  }

  .mode-toggle button:hover {
    color: rgba(226, 232, 240, 0.92);
  }

  .mode-toggle button.selected {
    background: rgba(59, 130, 246, 0.35);
    color: #e0f2fe;
    font-weight: 600;
  }

  .mode-toggle button:focus-visible {
    outline: 2px solid rgba(59, 130, 246, 0.65);
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
  }
</style>
