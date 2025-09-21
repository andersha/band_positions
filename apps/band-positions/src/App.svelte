<script lang="ts">
  import { onMount } from 'svelte';
  import BandTrajectoryChart from './lib/BandTrajectoryChart.svelte';
  import type { BandDataset, BandRecord } from './lib/types';

  const URL_PARAM_KEY = 'band';
  const URL_SEPARATOR = ',';

  let dataset: BandDataset | null = null;
  let loading = true;
  let error: string | null = null;
  let searchTerm = '';
  let selectedBands: BandRecord[] = [];
  let focusedIndex = -1;
  let initialUrlSyncDone = false;
  let lastSyncedSignature = '';

  onMount(async () => {
    try {
      const response = await fetch('data/band_positions.json');
      if (!response.ok) {
        throw new Error(`Kunne ikke laste data (status ${response.status})`);
      }
      dataset = (await response.json()) as BandDataset;
      syncSelectionFromURL({ updateHistory: false });
      initialUrlSyncDone = true;
      lastSyncedSignature = getSelectedSignature();
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

  function getSelectedSignature(bands: BandRecord[] = selectedBands): string {
    return bands.map((band) => band.slug).join(URL_SEPARATOR);
  }

  function getSlugsFromURL(): string[] {
    if (typeof window === 'undefined') return [];
    const params = new URLSearchParams(window.location.search);
    const raw = params.get(URL_PARAM_KEY);
    if (!raw) return [];
    return raw
      .split(URL_SEPARATOR)
      .map((slug) => decodeURIComponent(slug.trim()))
      .filter(Boolean);
  }

  function updateUrlForBands(bands: BandRecord[]): void {
    if (typeof window === 'undefined') return;
    const params = new URLSearchParams(window.location.search);
    if (bands.length) {
      params.set(
        URL_PARAM_KEY,
        bands.map((band) => encodeURIComponent(band.slug)).join(URL_SEPARATOR)
      );
    } else {
      params.delete(URL_PARAM_KEY);
    }
    const query = params.toString();
    const newUrl = `${window.location.pathname}${query ? `?${query}` : ''}${window.location.hash}`;
    window.history.replaceState({}, '', newUrl);
  }

  function syncSelectionFromURL({ updateHistory = false } = {}): boolean {
    if (!dataset) return false;
    const slugs = getSlugsFromURL();

    if (slugs.length === 0) {
      if (selectedBands.length > 0) {
        selectedBands = [];
      }
      searchTerm = '';
      focusedIndex = -1;
      if (updateHistory) {
        updateUrlForBands([]);
      }
      return true;
    }

    const matches: BandRecord[] = [];
    const seen = new Set<string>();
    for (const slug of slugs) {
      const normalized = slug.toLowerCase();
      const match = dataset.bands.find(
        (band) => band.slug === slug || band.slug === normalized
      );
      if (match && !seen.has(match.slug)) {
        seen.add(match.slug);
        matches.push(match);
      }
    }

    if (matches.length > 0) {
      selectedBands = matches;
      searchTerm = '';
      focusedIndex = -1;
      if (updateHistory) {
        updateUrlForBands(matches);
      }
      return true;
    }

    return false;
  }

  $: trimmed = searchTerm.trim();
  $: lowered = trimmed.toLowerCase();
  $: suggestions =
    dataset && lowered.length >= 2
      ? dataset.bands
          .filter(
            (band) =>
              band.name.toLowerCase().includes(lowered) &&
              !selectedBands.some((selected) => selected.slug === band.slug)
          )
          .slice(0, 10)
      : [];

  function handleSubmit() {
    if (!dataset || trimmed.length === 0) return;
    const exact = dataset.bands.find((band) => band.name.toLowerCase() === lowered);
    if (exact) {
      chooseBand(exact);
    } else if (suggestions.length > 0) {
      chooseBand(suggestions[0]);
    }
  }

  function onInput(event: Event) {
    searchTerm = (event.target as HTMLInputElement).value;
    focusedIndex = -1;
  }

  function chooseBand(band: BandRecord) {
    if (!selectedBands.some((selected) => selected.slug === band.slug)) {
      selectedBands = [...selectedBands, band];
    }
    searchTerm = '';
    focusedIndex = -1;
  }

  function removeBand(slug: string) {
    selectedBands = selectedBands.filter((band) => band.slug !== slug);
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (!suggestions.length) return;
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      focusedIndex = (focusedIndex + 1) % suggestions.length;
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      focusedIndex = (focusedIndex - 1 + suggestions.length) % suggestions.length;
    } else if (event.key === 'Enter' && focusedIndex >= 0) {
      event.preventDefault();
      chooseBand(suggestions[focusedIndex]);
    }
  }

  $: years = dataset ? dataset.metadata.years : [];
  $: maxFieldSize = dataset ? dataset.metadata.max_field_size : 0;
  let coverageDescription = '';
  $: coverageDescription = dataset
    ? `Dekker ${dataset.bands.length} korps · ${years.length} år (${dataset.metadata.min_year}–${dataset.metadata.max_year})`
    : '';

  $: if (initialUrlSyncDone) {
    const signature = getSelectedSignature();
    if (signature !== lastSyncedSignature) {
      updateUrlForBands(selectedBands);
      lastSyncedSignature = signature;
    }
  }

  $: chartHeading =
    selectedBands.length === 1
      ? selectedBands[0].name
      : selectedBands.length > 1
        ? `${selectedBands.length} korps valgt`
        : '';

  $: comparisonSummary =
    selectedBands.length > 1 ? selectedBands.map((band) => band.name).join(' · ') : '';
</script>

<main>
  <h1>NM Janitsjar: Plassering over tid</h1>
  <p class="lead">
    Søk etter et janitsjarkorps for å se hvordan den samlede plasseringen utvikler seg år for år, på tvers av alle divisjoner.
  </p>

  <form class="search" on:submit|preventDefault={handleSubmit}>
    <label class="sr-only" for="band-search">Søk etter korps</label>
    <input
      id="band-search"
      type="search"
      placeholder="Begynn å skrive et korpsnavn (minst 2 bokstaver)…"
      bind:value={searchTerm}
      on:input={onInput}
      on:keydown={handleKeyDown}
      autocomplete="off"
    />
  </form>

  {#if selectedBands.length > 0}
    <div class="selected-bands" role="list" aria-label="Valgte korps">
      {#each selectedBands as band, index}
        <span class="selected-band" role="listitem">
          <span class="selected-band__index">{index + 1}</span>
          <span class="selected-band__name">{band.name}</span>
          <button type="button" aria-label={`Fjern ${band.name}`} on:click={() => removeBand(band.slug)}>
            ×
          </button>
        </span>
      {/each}
    </div>
  {/if}

  {#if suggestions.length > 0}
    <div class="suggestions" role="listbox" aria-label="Forslag">
      {#each suggestions as band, index}
        <div
          class="suggestion {index === focusedIndex ? 'active' : ''}"
          role="option"
          tabindex="-1"
          aria-selected={index === focusedIndex}
          on:mousedown|preventDefault={() => chooseBand(band)}
        >
          {band.name}
        </div>
      {/each}
    </div>
  {/if}

  {#if loading}
    <section class="status">Laster data…</section>
  {:else if error}
    <section class="status error">{error}</section>
  {:else if selectedBands.length > 0}
    <section class="chart-card">
      <div class="chart-header">
        <h2>{chartHeading}</h2>
        <p>{coverageDescription}</p>
        {#if comparisonSummary}
          <p class="comparison-summary">{comparisonSummary}</p>
        {/if}
      </div>
      <BandTrajectoryChart {years} {maxFieldSize} bands={selectedBands} />
    </section>
  {:else}
    <section class="empty-state">
      <h2>Ingen korps valgt ennå</h2>
      <p>Finn et navn i søkefeltet for å tegne kurven for samlet plassering.</p>
    </section>
  {/if}
</main>

<style>
  main {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
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

  .selected-bands {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.75rem;
  }

  .selected-band {
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

  .selected-band__index {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.45rem;
    height: 1.45rem;
    border-radius: 50%;
    background: rgba(59, 130, 246, 0.45);
    font-size: 0.75rem;
  }

  .selected-band button {
    border: none;
    background: transparent;
    color: rgba(226, 232, 240, 0.85);
    cursor: pointer;
    font-size: 1rem;
    padding: 0;
    line-height: 1;
  }

  .selected-band button:hover {
    color: #fca5a5;
  }

  .selected-band__name {
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
  }

  .chart-header {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    margin-bottom: 1.25rem;
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
</style>
