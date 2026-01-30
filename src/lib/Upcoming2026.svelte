<script lang="ts">
  import type { BandType } from './types';
  import { onMount } from 'svelte';
  import { slugify } from './slugify';

  interface Props {
    bandType: BandType;
  }

  let { bandType }: Props = $props();

  interface Piece {
    title: string;
    composer: string;
    duration_minutes: number | null;
    difficulty: number | null;
  }

  interface UpcomingEntry {
    orchestra: string;
    division: string;
    play_order: number | null;
    play_datetime: string | null;
    venue: string | null;
    conductor: string | null;
    pieces: Piece[];
    korpsnr: number | null;
    image_url: string | null;
  }

  interface UpcomingDivision {
    name: string;
    entries: UpcomingEntry[];
    play_date: string | null;
    venue: string | null;
  }

  interface UpcomingData {
    year: number;
    competition_type: 'wind' | 'brass';
    stage: number;
    divisions: UpcomingDivision[];
    location: string | null;
    date_range: string | null;
    last_updated: string;
    notes: string;
  }

  let windData = $state<UpcomingData | null>(null);
  let brassData = $state<UpcomingData | null>(null);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let selectedDivision = $state<string | null>(null);

  let data = $derived(bandType === 'wind' ? windData : brassData);
  let availableDivisions = $derived(data?.divisions.map(d => d.name) ?? []);
  let visibleDivisions = $derived(
    !data ? [] :
    (!selectedDivision || selectedDivision === 'all') ? data.divisions :
    data.divisions.filter(d => d.name === selectedDivision)
  );

  const stageDescriptions: Record<number, string> = {
    1: 'Divisjonsinndeling kunngjort',
    2: 'Spilleplan kunngjort',
    3: 'Stykkevalg kunngjort',
    4: 'Dirigenter kunngjort'
  };

  function translateNotes(notes: string): string {
    // Translate common English phrases to Norwegian
    return notes
      .replace(/Division assignments announced/g, 'Divisjonsinndeling kunngjort')
      .replace(/Playing schedule announced/g, 'Spilleplan kunngjort')
      .replace(/Pieces and conductors TBA/g, 'Stykkevalg og dirigenter kommer senere')
      .replace(/~1 month before competition/g, 'ca. 1 måned før konkurransen')
      .replace(/Playing schedule, pieces, and conductors TBA/g, 'Spilleplan, stykkevalg og dirigenter kommer senere');
  }

  function formatDateTime(dateTimeStr: string | null): string {
    if (!dateTimeStr) return '';
    try {
      const date = new Date(dateTimeStr);
      const options: Intl.DateTimeFormatOptions = {
        weekday: 'short',
        day: 'numeric',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit'
      };
      return date.toLocaleDateString('nb-NO', options);
    } catch {
      return dateTimeStr;
    }
  }

  function formatDate(dateStr: string | null): string {
    if (!dateStr) return '';
    try {
      const date = new Date(dateStr);
      const options: Intl.DateTimeFormatOptions = {
        weekday: 'long',
        day: 'numeric',
        month: 'long'
      };
      return date.toLocaleDateString('nb-NO', options);
    } catch {
      return dateStr;
    }
  }

  function formatTime(dateTimeStr: string | null): string {
    if (!dateTimeStr) return '';
    try {
      const date = new Date(dateTimeStr);
      return date.toLocaleTimeString('nb-NO', { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  }

  async function loadUpcomingData() {
    try {
      const [windResponse, brassResponse] = await Promise.all([
        fetch('data/upcoming_wind_2026.json'),
        fetch('data/upcoming_brass_2026.json')
      ]);

      if (windResponse.ok) {
        windData = await windResponse.json();
      } else {
        console.warn('Could not load wind upcoming data');
      }

      if (brassResponse.ok) {
        brassData = await brassResponse.json();
      } else {
        console.warn('Could not load brass upcoming data');
      }

      if (!windData && !brassData) {
        throw new Error('Kunne ikke laste kommende konkurransedata');
      }
    } catch (err) {
      error = err instanceof Error ? err.message : 'Ukjent feil ved lasting av data';
    } finally {
      loading = false;
    }
  }

  // Reset division selection when band type changes
  $effect(() => {
    if (bandType) {
      selectedDivision = 'all';
    }
  });

  onMount(() => {
    loadUpcomingData();
  });
</script>

{#if loading}
  <section class="status">Laster data for NM 2026...</section>
{:else if error}
  <section class="status error">{error}</section>
{:else if !data}
  <section class="status">Ingen data tilgjengelig for NM 2026.</section>
{:else}
  <section class="upcoming-container">
    <div class="upcoming-header">
      <h2>NM {data.competition_type === 'wind' ? 'Janitsjar' : 'Brass'} 2026</h2>
      {#if data.location}
        <p class="location">📍 {data.location}</p>
      {/if}
      {#if data.date_range}
        <p class="date-range">🗓️ {data.date_range}</p>
      {/if}
      <div class="stage-badge stage-{data.stage}">
        {stageDescriptions[data.stage] || `Stadium ${data.stage}`}
      </div>
      {#if data.notes}
        <p class="notes">{translateNotes(data.notes)}</p>
      {/if}
    </div>

    {#if availableDivisions.length > 1}
      <div class="division-selector">
        <label for="division-select">Velg divisjon:</label>
        <select id="division-select" bind:value={selectedDivision}>
          <option value="all">Alle divisjoner ({data.divisions.length})</option>
          {#each availableDivisions as division}
            <option value={division}>{division}</option>
          {/each}
        </select>
      </div>
    {/if}

    {#each visibleDivisions as division}
      <div class="division-card">
        <div class="division-header">
          <h3>{division.name}</h3>
          <span class="entry-count">{division.entries.length} korps</span>
        </div>
        
        {#if division.play_date}
          <p class="division-date">📅 {formatDate(division.play_date)}</p>
        {/if}
        {#if division.venue}
          <p class="division-venue">🎵 {division.venue}</p>
        {/if}
        
        {#if data.competition_type === 'brass' && division.name === 'Elite'}
          <div class="test-piece-notice">
            <strong>Pliktnummer:</strong> <a href="?type=brass&view=pieces&piece=concerto-for-band-no-1" class="entity-link">Concerto No. 1</a> av <a href="?type=brass&view=composers&composer=derek-bourgeois" class="entity-link">Derek Bourgeois</a> (1999) spilles fredag 6. februar, spillerekkefølge trekkes samme dag.
          </div>
        {/if}

        <div class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th scope="col" class="time-column">Tid</th>
                <th scope="col">Korps</th>
                <th scope="col">Dirigent</th>
                <th scope="col">Stykke</th>
              </tr>
            </thead>
            <tbody>
              {#each division.entries as entry, idx}
                {@const bandSlug = slugify(entry.orchestra)}
                {@const conductorName = entry.conductor?.trim() ?? ''}
                {@const hasConductor = conductorName.length > 0}
                {@const conductorSlug = hasConductor ? slugify(conductorName) : ''}
                {@const pieces = entry.pieces ?? []}
                <tr>
                  <td data-label="Tid" class="time-cell">{formatTime(entry.play_datetime)}</td>
                  <td data-label="Korps">
                    <a
                      href={`?type=${bandType}&view=bands&band=${encodeURIComponent(bandSlug)}`}
                      class="entity-link"
                    >
                      {entry.orchestra}
                    </a>
                  </td>
                  <td data-label="Dirigent">
                    {#if hasConductor}
                      <a
                        href={`?type=${bandType}&view=conductors&conductor=${encodeURIComponent(conductorSlug)}`}
                        class="entity-link"
                      >
                        {conductorName}
                      </a>
                    {:else}
                      <span class="missing-data">–</span>
                    {/if}
                  </td>
                  <td data-label="Stykke" class="piece-cell">
                    {#if pieces.length > 0}
                      <ul class="piece-list">
                        {#each pieces as piece}
                          {@const pieceTitle = piece.title?.trim() ?? ''}
                          {@const pieceSlug = pieceTitle ? slugify(pieceTitle) : ''}
                          {@const composer = piece.composer?.trim() ?? ''}
                          <li>
                            {#if pieceSlug}
                              <a
                                href={`?type=${bandType}&view=pieces&piece=${encodeURIComponent(pieceSlug)}`}
                                class="entity-link"
                              >
                                {pieceTitle}
                              </a>
                            {:else if pieceTitle}
                              <span>{pieceTitle}</span>
                            {/if}
                            {#if composer}
                              <span class="composer"> ({composer})</span>
                            {/if}
                          </li>
                        {/each}
                      </ul>
                    {:else}
                      <span class="missing-data">–</span>
                    {/if}
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>
    {/each}
  </section>
{/if}

<style>
  .status {
    margin: 2rem 0;
    padding: 1.5rem;
    text-align: center;
    color: var(--color-text-secondary);
    background: var(--color-surface-card);
    border-radius: 1rem;
    border: 1px solid var(--color-border);
  }

  .status.error {
    color: var(--color-warning);
  }

  .upcoming-container {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .upcoming-header {
    padding: 1.5rem;
    background: var(--color-surface-card);
    border-radius: 1rem;
    border: 1px solid var(--color-border);
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.25);
  }

  .upcoming-header h2 {
    margin: 0 0 0.75rem 0;
    font-size: 1.75rem;
    color: var(--color-accent);
  }

  .location,
  .date-range {
    margin: 0.5rem 0;
    color: var(--color-text-secondary);
    font-size: 1rem;
  }

  .stage-badge {
    display: inline-block;
    margin: 0.75rem 0;
    padding: 0.4rem 0.9rem;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 600;
  }

  .stage-1 {
    background: rgba(59, 130, 246, 0.15);
    color: rgb(59, 130, 246);
    border: 1px solid rgba(59, 130, 246, 0.3);
  }

  .stage-2 {
    background: rgba(34, 197, 94, 0.15);
    color: rgb(34, 197, 94);
    border: 1px solid rgba(34, 197, 94, 0.3);
  }

  .stage-3 {
    background: rgba(251, 191, 36, 0.15);
    color: rgb(251, 191, 36);
    border: 1px solid rgba(251, 191, 36, 0.3);
  }

  .stage-4 {
    background: rgba(168, 85, 247, 0.15);
    color: rgb(168, 85, 247);
    border: 1px solid rgba(168, 85, 247, 0.3);
  }

  .notes {
    margin: 0.75rem 0 0 0;
    color: var(--color-text-muted);
    font-size: 0.9rem;
    font-style: italic;
  }

  .division-selector {
    padding: 1rem 1.5rem;
    background: var(--color-surface-card);
    border-radius: 1rem;
    border: 1px solid var(--color-border);
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .division-selector label {
    font-weight: 600;
    color: var(--color-text-primary);
    white-space: nowrap;
  }

  .division-selector select {
    flex: 1;
    padding: 0.5rem 0.75rem;
    border-radius: 0.5rem;
    border: 1px solid var(--color-border);
    background: var(--color-surface-elevated);
    color: var(--color-text-primary);
    font-size: 0.95rem;
    cursor: pointer;
    transition: border-color 0.2s ease;
  }

  .division-selector select:hover {
    border-color: var(--color-accent);
  }

  .division-selector select:focus {
    outline: none;
    border-color: var(--color-accent);
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
  }

  .division-card {
    padding: 1.5rem;
    background: var(--color-surface-card);
    border-radius: 1rem;
    border: 1px solid var(--color-border);
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.2);
  }

  .division-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .division-header h3 {
    margin: 0;
    font-size: 1.35rem;
    color: var(--color-text-primary);
  }

  .entry-count {
    padding: 0.25rem 0.7rem;
    background: var(--color-chip-bg);
    border: 1px solid var(--color-chip-border);
    border-radius: 999px;
    font-size: 0.8rem;
    color: var(--color-text-secondary);
  }

  .division-date,
  .division-venue {
    margin: 0.5rem 0;
    color: var(--color-text-secondary);
    font-size: 0.95rem;
  }

  .test-piece-notice {
    margin: 1rem 0;
    padding: 0.75rem 0;
    color: var(--color-text-secondary);
    font-size: 0.9rem;
    line-height: 1.5;
  }

  .test-piece-notice strong {
    color: var(--color-text-primary);
  }

  .test-piece-notice .entity-link {
    color: var(--color-accent);
    text-decoration: none;
  }

  .test-piece-notice .entity-link:hover,
  .test-piece-notice .entity-link:focus-visible {
    text-decoration: underline;
  }

  .table-wrapper {
    margin-top: 1rem;
    overflow-x: auto;
    border-radius: 0.85rem;
    border: 1px solid var(--color-border);
  }

  table {
    width: 100%;
    border-collapse: collapse;
  }

  th,
  td {
    padding: 0.7rem 1rem;
    text-align: left;
  }

  thead {
    background: var(--color-mode-toggle-bg);
  }

  th {
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.02em;
    color: var(--color-text-secondary);
  }

  tbody tr:nth-child(even) {
    background: rgba(255, 255, 255, 0.02);
  }

  tbody td {
    border-top: 1px solid var(--color-border);
    color: var(--color-text-primary);
    font-size: 0.95rem;
  }

  .time-column,
  .time-cell {
    width: 5rem;
    white-space: nowrap;
  }

  .piece-cell {
    max-width: 20rem;
  }

  .piece-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .piece-list li {
    margin: 0.25rem 0;
  }

  .piece-list li:first-child {
    margin-top: 0;
  }

  .piece-list li:last-child {
    margin-bottom: 0;
  }

  .composer {
    color: var(--color-text-secondary);
    font-size: 0.85em;
  }

  .missing-data {
    color: var(--color-text-muted);
  }

  .entity-link {
    color: var(--color-accent);
    text-decoration: none;
  }

  .entity-link:hover,
  .entity-link:focus-visible {
    text-decoration: underline;
  }

  td[data-label]::before {
    content: attr(data-label);
    display: none;
    font-weight: 600;
    margin-right: 0.5rem;
  }

  @media (max-width: 780px) {
    .upcoming-header,
    .division-card,
    .division-selector {
      padding: 1rem;
    }

    .division-selector {
      flex-direction: column;
      align-items: stretch;
      gap: 0.5rem;
    }

    .upcoming-header h2 {
      font-size: 1.5rem;
    }

    .division-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.5rem;
    }
  }

  @media (max-width: 640px) {
    thead {
      display: none;
    }

    tbody tr {
      display: grid;
      grid-template-columns: 70% 30%;
      gap: 0.35rem 0.75rem;
      padding: 0.75rem 1rem;
      border-bottom: 1px solid var(--color-border);
    }

    tbody tr:last-child {
      border-bottom: none;
    }

    tbody td {
      border-top: none;
      padding: 0;
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }

    td[data-label]::before {
      display: block;
      color: var(--color-text-secondary);
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.02em;
    }

    /* Mobile layout order: Korps, Tid, Dirigent, Stykke */
    td[data-label="Korps"] {
      order: 1;
    }

    td[data-label="Tid"] {
      order: 2;
    }

    td[data-label="Dirigent"] {
      order: 3;
    }

    td[data-label="Stykke"] {
      order: 4;
    }

    .time-cell {
      color: var(--color-text-secondary);
    }

    .piece-list li {
      word-break: break-word;
      overflow-wrap: break-word;
    }

    .entity-link {
      word-break: break-word;
      overflow-wrap: break-word;
      hyphens: auto;
    }
  }
</style>
