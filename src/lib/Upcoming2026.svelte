<script lang="ts">
  import type { BandType } from './types';
  import { onMount } from 'svelte';
  import { slugify } from './slugify';
  import { readLS, writeLS, STORAGE_KEYS } from './storage';

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
  let starredEntries = $state<Set<string>>(new Set());

  let data = $derived(bandType === 'wind' ? windData : brassData);
  let availableDivisions = $derived(data?.divisions.map(d => d.name) ?? []);
  
  // Group starred entries chronologically by day
  let starredByDay = $derived.by(() => {
    if (!data || selectedDivision !== 'starred') return [];
    
    const allStarredEntries: Array<{entry: UpcomingEntry, division: string}> = [];
    
    // Collect all starred entries across divisions
    for (const division of data.divisions) {
      for (const entry of division.entries) {
        if (isStarred(entry, division.name)) {
          allStarredEntries.push({ entry, division: division.name });
        }
      }
    }
    
    // Sort by datetime
    allStarredEntries.sort((a, b) => {
      const timeA = a.entry.play_datetime ? new Date(a.entry.play_datetime).getTime() : 0;
      const timeB = b.entry.play_datetime ? new Date(b.entry.play_datetime).getTime() : 0;
      return timeA - timeB;
    });
    
    // Group by day
    const byDay = new Map<string, Array<{entry: UpcomingEntry, division: string}>>();
    for (const item of allStarredEntries) {
      if (!item.entry.play_datetime) continue;
      const date = new Date(item.entry.play_datetime);
      const dayKey = date.toISOString().split('T')[0];
      if (!byDay.has(dayKey)) {
        byDay.set(dayKey, []);
      }
      byDay.get(dayKey)!.push(item);
    }
    
    // Convert to array with formatted day names
    return Array.from(byDay.entries()).map(([dateKey, entries]) => {
      const date = new Date(dateKey);
      const dayName = date.toLocaleDateString('nb-NO', { weekday: 'long' });
      const dayNameCapitalized = dayName.charAt(0).toUpperCase() + dayName.slice(1);
      return { dateKey, dayName: dayNameCapitalized, entries };
    });
  });
  
  // Check if we should show pieces - only if at least one division has complete piece data
  let showPieces = $derived.by(() => {
    if (!data) return false;
    
    // Check each division to see if all bands have at least one piece
    for (const division of data.divisions) {
      const allHavePieces = division.entries.every(entry => 
        entry.pieces && entry.pieces.length > 0
      );
      if (allHavePieces) {
        return true; // At least one complete division found
      }
    }
    
    return false; // No complete division found
  });
  
  // Check if we should show conductors - only if at least one division has complete conductor data
  let showConductors = $derived.by(() => {
    if (!data) return false;
    
    // Check each division to see if all bands have a conductor
    for (const division of data.divisions) {
      const allHaveConductors = division.entries.every(entry => 
        entry.conductor && entry.conductor.trim().length > 0
      );
      if (allHaveConductors) {
        return true; // At least one complete division found
      }
    }
    
    return false; // No complete division found
  });
  
  let visibleDivisions = $derived(
    !data ? [] :
    selectedDivision === 'starred' ? [] : // Empty when showing chronological view
    (!selectedDivision || selectedDivision === 'all') ? data.divisions :
    data.divisions.filter(d => d.name === selectedDivision)
  );
  let starredCount = $derived(starredEntries.size);
  let showChronologicalView = $derived(selectedDivision === 'starred');

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

  function getEntryId(entry: UpcomingEntry, division: string): string {
    const orchestraSlug = slugify(entry.orchestra);
    const divisionSlug = slugify(division);
    return `${orchestraSlug}-${divisionSlug}`;
  }

  function isStarred(entry: UpcomingEntry, division: string): boolean {
    return starredEntries.has(getEntryId(entry, division));
  }

  function toggleStar(entry: UpcomingEntry, division: string): void {
    const entryId = getEntryId(entry, division);
    const newStarred = new Set(starredEntries);
    
    if (newStarred.has(entryId)) {
      newStarred.delete(entryId);
    } else {
      newStarred.add(entryId);
    }
    
    starredEntries = newStarred;
    saveStarredEntries();
  }

  function loadStarredEntries(): Set<string> {
    const storageKey = bandType === 'wind' 
      ? STORAGE_KEYS.STARRED_2026_WIND 
      : STORAGE_KEYS.STARRED_2026_BRASS;
    
    const stored = readLS(storageKey, '[]');
    try {
      const parsed = JSON.parse(stored);
      return new Set(Array.isArray(parsed) ? parsed : []);
    } catch {
      return new Set();
    }
  }

  function saveStarredEntries(): void {
    const storageKey = bandType === 'wind' 
      ? STORAGE_KEYS.STARRED_2026_WIND 
      : STORAGE_KEYS.STARRED_2026_BRASS;
    
    const array = Array.from(starredEntries);
    writeLS(storageKey, JSON.stringify(array));
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
      starredEntries = loadStarredEntries();
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

    {#if availableDivisions.length > 1}
      <div class="division-selector">
        <label for="division-select">Velg divisjon:</label>
        <select id="division-select" bind:value={selectedDivision}>
          <option value="all">Alle divisjoner ({data.divisions.length})</option>
          {#if starredCount > 0}
            <option value="starred">⭐ Kun favoritter ({starredCount})</option>
          {/if}
          {#each availableDivisions as division}
            <option value={division}>{division}</option>
          {/each}
        </select>
      </div>
    {/if}

    {#if showChronologicalView}
      {#each starredByDay as day}
        <div class="division-card">
          <div class="division-header">
            <h3>{day.dayName}</h3>
            <span class="entry-count">{day.entries.length} korps</span>
          </div>
          
          <div class="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th scope="col" class="time-column">Tid</th>
                  <th scope="col">Korps</th>
                  <th scope="col">Divisjon</th>
                  <th scope="col">Lokale</th>
                  {#if showConductors}
                    <th scope="col">Dirigent</th>
                  {/if}
                  {#if showPieces}
                    <th scope="col">Stykke</th>
                  {/if}
                </tr>
              </thead>
              <tbody>
                {#each day.entries as {entry, division}}
                  {@const bandSlug = slugify(entry.orchestra)}
                  {@const conductorName = entry.conductor?.trim() ?? ''}
                  {@const hasConductor = conductorName.length > 0}
                  {@const conductorSlug = hasConductor ? slugify(conductorName) : ''}
                  {@const pieces = entry.pieces ?? []}
                  {@const starred = isStarred(entry, division)}
                  <tr class="entry-row">
                    <td data-label="Tid" class="time-cell">
                      {formatTime(entry.play_datetime)}
                      <button
                        type="button"
                        class="star-button"
                        class:star-button--starred={starred}
                        aria-label={starred ? 'Fjern fra favoritter' : 'Legg til i favoritter'}
                        onclick={() => toggleStar(entry, division)}
                      >
                        {starred ? '★' : '☆'}
                      </button>
                    </td>
                    <td data-label="Korps">
                      <a
                        href={`?type=${bandType}&view=bands&band=${encodeURIComponent(bandSlug)}`}
                        class="entity-link"
                      >
                        {entry.orchestra}
                      </a>
                    </td>
                    <td data-label="Divisjon" class="division-cell">{division}</td>
                    <td data-label="Lokale" class="venue-cell">
                      {#if entry.venue}
                        {entry.venue}
                      {:else}
                        <span class="missing-data">–</span>
                      {/if}
                    </td>
                    {#if showConductors}
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
                    {/if}
                    {#if showPieces}
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
                    {/if}
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        </div>
      {/each}
    {:else}
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
                {#if showConductors}
                  <th scope="col">Dirigent</th>
                {/if}
                {#if showPieces}
                  <th scope="col">Stykke</th>
                {/if}
              </tr>
            </thead>
            <tbody>
              {#each division.entries as entry, idx}
                {@const bandSlug = slugify(entry.orchestra)}
                {@const conductorName = entry.conductor?.trim() ?? ''}
                {@const hasConductor = conductorName.length > 0}
                {@const conductorSlug = hasConductor ? slugify(conductorName) : ''}
                {@const pieces = entry.pieces ?? []}
                {@const starred = isStarred(entry, division.name)}
                <tr class="entry-row">
                  <td data-label="Tid" class="time-cell">
                    {formatTime(entry.play_datetime)}
                    <button
                      type="button"
                      class="star-button"
                      class:star-button--starred={starred}
                      aria-label={starred ? 'Fjern fra favoritter' : 'Legg til i favoritter'}
                      onclick={() => toggleStar(entry, division.name)}
                    >
                      {starred ? '★' : '☆'}
                    </button>
                  </td>
                  <td data-label="Korps">
                    <a
                      href={`?type=${bandType}&view=bands&band=${encodeURIComponent(bandSlug)}`}
                      class="entity-link"
                    >
                      {entry.orchestra}
                    </a>
                  </td>
                  {#if showConductors}
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
                  {/if}
                  {#if showPieces}
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
                  {/if}
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>
      {/each}
    {/if}
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

  .entry-row {
    position: relative;
  }

  .time-cell {
    position: relative;
  }

  .star-button {
    appearance: none;
    border: none;
    background: transparent;
    color: var(--color-text-muted);
    font-size: 1rem;
    line-height: 1;
    cursor: pointer;
    padding: 0.35rem;
    position: absolute;
    top: 50%;
    left: 0;
    transform: translateY(-50%);
    min-width: 32px;
    min-height: 32px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: color 0.2s ease, transform 0.15s ease;
    opacity: 0.6;
  }

  .star-button:hover,
  .entry-row:hover .star-button {
    opacity: 1;
    color: var(--color-accent);
    transform: translateY(-50%) scale(1.2);
  }

  .star-button--starred {
    color: rgb(251, 191, 36);
    opacity: 1;
  }

  .star-button--starred:hover {
    color: rgb(245, 158, 11);
  }

  .star-button:focus-visible {
    outline: 2px solid var(--color-accent);
    outline-offset: 2px;
    border-radius: 4px;
    opacity: 1;
  }

  .time-column {
    width: 7rem;
  }

  .time-cell {
    width: 7rem;
    white-space: nowrap;
    padding-left: 2.5rem;
    padding-right: 0;
  }

  .division-cell {
    white-space: nowrap;
  }

  .venue-cell {
    font-size: 0.9em;
    color: var(--color-text-secondary);
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
    .division-card,
    .division-selector {
      padding: 1rem;
    }

    .division-selector {
      flex-direction: column;
      align-items: stretch;
      gap: 0.5rem;
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
      grid-template-columns: 60% 40%;
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

    /* Mobile layout order: Korps, Tid, Divisjon, Lokale, Dirigent, Stykke */
    td[data-label="Korps"] {
      order: 1;
    }

    td[data-label="Tid"] {
      order: 2;
    }

    td[data-label="Divisjon"] {
      order: 3;
    }

    td[data-label="Lokale"] {
      order: 4;
    }

    td[data-label="Dirigent"] {
      order: 5;
    }

    td[data-label="Stykke"] {
      order: 6;
    }

    .time-cell {
      color: var(--color-text-secondary);
    }

    .piece-list li {
      word-break: break-word;
      overflow-wrap: break-word;
    }

    .piece-cell {
      padding-right: 0;
      padding-bottom: 0;
    }

    .time-cell {
      position: relative;
      padding-left: 0;
      padding-right: 2.5rem;
    }

    .star-button {
      position: absolute;
      top: 50%;
      left: auto;
      right: 0;
      transform: translateY(-50%);
      font-size: 0.9rem;
      min-width: 28px;
      min-height: 28px;
      padding: 0.25rem;
    }

    .star-button:hover,
    .entry-row:hover .star-button {
      transform: translateY(-50%) scale(1.15);
    }

    .entity-link {
      word-break: break-word;
      overflow-wrap: break-word;
      hyphens: auto;
    }
  }
</style>
