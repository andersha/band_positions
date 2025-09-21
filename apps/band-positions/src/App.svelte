<script lang="ts">
  import { onMount } from 'svelte';
  import BandTrajectoryChart from './lib/BandTrajectoryChart.svelte';
  import type { BandDataset, BandRecord } from './lib/types';

  let dataset: BandDataset | null = null;
  let loading = true;
  let error: string | null = null;
  let searchTerm = '';
  let selectedBand: BandRecord | null = null;
  let focusedIndex = -1;

  onMount(async () => {
    try {
      const response = await fetch('data/band_positions.json');
      if (!response.ok) {
        throw new Error(`Kunne ikke laste data (status ${response.status})`);
      }
      dataset = (await response.json()) as BandDataset;
    } catch (err) {
      error = err instanceof Error ? err.message : 'Ukjent feil ved lasting av data.';
    } finally {
      loading = false;
    }
  });

  $: trimmed = searchTerm.trim();
  $: lowered = trimmed.toLowerCase();
  $: suggestions =
    dataset && lowered.length >= 2
      ? dataset.bands.filter((band) => band.name.toLowerCase().includes(lowered)).slice(0, 10)
      : [];

  $: if (selectedBand && lowered && selectedBand.name.toLowerCase() !== lowered) {
    selectedBand = null;
  }

  function handleSubmit() {
    if (!dataset) return;
    if (trimmed.length === 0) {
      selectedBand = null;
      return;
    }
    const exact = dataset.bands.find((band) => band.name.toLowerCase() === lowered);
    if (exact) {
      chooseBand(exact);
    } else if (suggestions.length > 0) {
      chooseBand(suggestions[0]);
    }
  }

  function onInput(event: Event) {
    const value = (event.target as HTMLInputElement).value;
    searchTerm = value;
    focusedIndex = -1;
  }

  function chooseBand(band: BandRecord) {
    selectedBand = band;
    searchTerm = band.name;
    focusedIndex = -1;
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

  $: selectedEntries = selectedBand ? selectedBand.entries : [];
  $: years = dataset ? dataset.metadata.years : [];
  $: maxFieldSize = dataset ? dataset.metadata.max_field_size : 0;
  let coverageDescription = '';
  $: coverageDescription = dataset
    ? `Dekker ${dataset.bands.length} korps · ${years.length} år (${dataset.metadata.min_year}–${dataset.metadata.max_year})`
    : '';
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
  {:else if selectedBand}
    <section class="chart-card">
      <div class="chart-header">
        <h2>{selectedBand.name}</h2>
        <p>{coverageDescription}</p>
      </div>
      <BandTrajectoryChart entries={selectedEntries} {years} {maxFieldSize} />
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

  .status {
    margin-top: 2rem;
    color: rgba(226, 232, 240, 0.8);
  }

  .status.error {
    color: #fca5a5;
  }

  .suggestion.active {
    background-color: rgba(59, 130, 246, 0.25);
  }
</style>
