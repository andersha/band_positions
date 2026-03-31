<script lang="ts">
  import type { BandRecord, BandEntry, BandType, StreamingLink } from './types';
  import { slugify } from './slugify';
  import { getTrophy, countTrophies, formatTrophySummary } from './trophyUtils';

  interface Props {
    conductors?: BandRecord[];
    bandType?: BandType;
    sortOrder?: 'asc' | 'desc';
    streamingResolver?: (entry: BandEntry, bandName: string, pieceName: string) => StreamingLink | null;
    pieceLengthResolver?: (pieceName: string) => number | null;
    onRemove?: (slug: string) => void;
  }

  type ConductorEntry = BandEntry & {
    band_name?: string | null;
    aggregate_entries?: ConductorEntry[];
  };

  interface ConductorSummary extends BandRecord {
    performances: ConductorEntry[];
  }

  let { conductors = [], bandType = 'wind', sortOrder = 'asc', streamingResolver, pieceLengthResolver, onRemove }: Props = $props();

  const pointsFormatter = new Intl.NumberFormat('nb-NO', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1
  });

  // Sorting state and utilities
  type Direction = 'asc' | 'desc';
  type ConductorSortColumn = 'year' | 'division' | 'rank' | 'points' | 'band';

  let sortColumn = $state<ConductorSortColumn>('year');
  let sortDirection = $state<Direction>('asc');

  function cmp(a: unknown, b: unknown, dir: Direction): number {
    const aNull = a == null || a === '';
    const bNull = b == null || b === '';
    if (aNull && bNull) return 0;
    if (aNull) return 1;   // nulls/empties last for ascending
    if (bNull) return -1;

    let result: number;
    if (typeof a === 'number' && typeof b === 'number') {
      result = a - b;
    } else {
      result = String(a).localeCompare(String(b), 'nb', { numeric: true, sensitivity: 'base' });
    }
    return dir === 'asc' ? result : -result;
  }

  function ariaSort(current: ConductorSortColumn, target: ConductorSortColumn, dir: Direction): 'ascending' | 'descending' | 'none' {
    if (current !== target) return 'none';
    return dir === 'asc' ? 'ascending' : 'descending';
  }

  function indicator(current: ConductorSortColumn, target: ConductorSortColumn, dir: Direction): string {
    if (current !== target) return '';
    return dir === 'asc' ? ' ▲' : ' ▼';
  }

  function handleSort(column: ConductorSortColumn) {
    if (sortColumn === column) {
      sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      sortColumn = column;
      // Points should default to descending (highest first)
      sortDirection = column === 'points' ? 'desc' : sortOrder;
    }
  }

  $effect(() => {
    sortColumn = 'year';
    sortDirection = sortOrder;
  });

  function getDivisionRank(division: string | null): number {
    if (!division) return 999;
    const div = division.toLowerCase();
    if (div === 'elite') return 0;
    if (div.includes('1.') || div === '1') return 1;
    if (div.includes('2.') || div === '2') return 2;
    if (div.includes('3.') || div === '3') return 3;
    if (div.includes('4.') || div === '4') return 4;
    if (div.includes('5.') || div === '5') return 5;
    if (div.includes('6.') || div === '6') return 6;
    return 10; // Other divisions
  }

  function getValue(entry: ConductorEntry, column: ConductorSortColumn) {
    switch (column) {
      case 'year': return entry.year;
      case 'division': return getDivisionRank(entry.division ?? null);
      case 'rank': return entry.rank ?? entry.absolute_position ?? null;
      case 'points': return entry.points ?? null;
      case 'band': return entry.band_name ?? null;
    }
  }

  function sortPerformances(entries: ConductorEntry[]): ConductorEntry[] {
    const sorted = [...entries];
    sorted.sort((a, b) => {
      const primary = cmp(getValue(a, sortColumn), getValue(b, sortColumn), sortDirection);
      if (primary !== 0) return primary;
      // Stable secondary key: year ascending
      return cmp(a.year, b.year, 'asc');
    });
    return sorted;
  }

  function formatPoints(points: number | null): string {
    if (points == null) return '–';
    return pointsFormatter.format(points);
  }

  function formatRank(rank: number | null): string {
    return rank != null ? `${rank}` : '–';
  }

  function formatLengde(durationSeconds?: number | null, fallbackMinutes?: number | null): string {
    if (durationSeconds != null) return `${Math.round(durationSeconds / 60)}'`;
    if (fallbackMinutes != null) return `${Math.round(fallbackMinutes)}'`;
    return '';
  }

  function hasStreamingLinks(streaming?: StreamingLink | null): boolean {
    return Boolean(streaming?.spotify || streaming?.apple_music || streaming?.youtube);
  }

  function toAppleMusicHref(url: string | null | undefined): string | null {
    if (!url) return null;
    const trimmed = url.trim();
    if (!trimmed) return null;
    if (!/^https?:\/\//i.test(trimmed)) {
      return trimmed;
    }
    try {
      const parsed = new URL(trimmed);
      const path = `${parsed.host}${parsed.pathname}${parsed.search}${parsed.hash}`;
      return `music://${path}`;
    } catch (err) {
      console.warn('Kunne ikke konvertere Apple Music-lenke', err);
      return trimmed;
    }
  }

  function buildStreamingTitle(
    pieceName: string,
    streaming: StreamingLink | null | undefined,
    platform: 'spotify' | 'apple'
  ): string {
    if (!streaming) return pieceName;
    const trackName = streaming.recording_title?.trim();
    const albumName = streaming.album?.trim();
    const platformLabel = platform === 'spotify' ? 'Spotify' : 'Apple Music';
    const base = trackName && trackName.length > 0 ? trackName : pieceName;
    if (albumName && albumName.length > 0) {
      return `${base} • ${albumName} (${platformLabel})`;
    }
    return `${base} (${platformLabel})`;
  }

  function resolveStreaming(entry: BandEntry, bandName: string, pieceName: string): StreamingLink | null {
    if (!streamingResolver) return null;
    return streamingResolver(entry, bandName, pieceName) ?? null;
  }

  function flattenPerformances(conductor: BandRecord): ConductorEntry[] {
    const entries = (conductor.entries ?? []) as ConductorEntry[];
    const expanded = entries.flatMap((entry) => {
      const aggregate = entry.aggregate_entries && Array.isArray(entry.aggregate_entries)
        ? entry.aggregate_entries
        : [entry];
      return aggregate.map((item) => ({
        ...item,
        band_name: item.band_name ?? entry.band_name ?? null
      }));
    });

    return sortPerformances(expanded);
  }

  let normalizedConductors = $derived<ConductorSummary[]>(
    conductors.map((conductor) => ({
      ...conductor,
      performances: flattenPerformances(conductor)
    }))
  );
</script>

<section class="conductor-performances">
  {#each normalizedConductors as conductor}
    {@const trophyCount = countTrophies(conductor.performances)}
    {@const trophySummary = formatTrophySummary(trophyCount)}
    <article class="conductor-card">
      <header class="conductor-header">
        <div>
          <h2>{conductor.name}</h2>
          {#if trophySummary}
            <p class="trophy-summary">{trophySummary}</p>
          {/if}
          <p class="conductor-count">{conductor.performances.length} fremføringer</p>
        </div>
        {#if onRemove}
          <button
            type="button"
            class="card-remove-btn"
            aria-label={`Fjern ${conductor.name}`}
            onclick={() => onRemove!(conductor.slug)}
          >×</button>
        {/if}
      </header>

      <div class="table-wrapper" role="region" aria-label={`Fremføringer av ${conductor.name}`}>
        <table>
          <thead>
            <tr>
              <th scope="col" class="sortable" onclick={() => handleSort('year')} aria-sort={ariaSort(sortColumn, 'year', sortDirection)}>År<span class="sort-indicator">{indicator(sortColumn, 'year', sortDirection)}</span></th>
              <th scope="col" class="division-column sortable" onclick={() => handleSort('division')} aria-sort={ariaSort(sortColumn, 'division', sortDirection)}>Divisjon<span class="sort-indicator">{indicator(sortColumn, 'division', sortDirection)}</span></th>
              <th scope="col" class="sortable" onclick={() => handleSort('rank')} aria-sort={ariaSort(sortColumn, 'rank', sortDirection)}>Plass<span class="sort-indicator">{indicator(sortColumn, 'rank', sortDirection)}</span></th>
              <th scope="col" class="sortable" onclick={() => handleSort('points')} aria-sort={ariaSort(sortColumn, 'points', sortDirection)}>Poeng<span class="sort-indicator">{indicator(sortColumn, 'points', sortDirection)}</span></th>
              <th scope="col" class="sortable" onclick={() => handleSort('band')} aria-sort={ariaSort(sortColumn, 'band', sortDirection)}>Korps<span class="sort-indicator">{indicator(sortColumn, 'band', sortDirection)}</span></th>
              <th scope="col">Program</th>
              <th scope="col" class="streaming-column">Opptak</th>
              <th scope="col" class="lengde-column">Lengde</th>
            </tr>
          </thead>
          <tbody>
            {#each conductor.performances as performance}
              {@const bandName = performance.band_name?.trim() ?? ''}
              {@const hasBand = bandName.length > 0}
              {@const bandSlug = hasBand ? slugify(bandName) : ''}
              {@const pieces = Array.isArray(performance.pieces) ? performance.pieces : []}
              {@const filteredPieces = pieces.filter((piece) => piece && piece.trim().length > 0)}
              {@const pieceEntries = filteredPieces.map((piece) => {
                const pieceName = piece.trim();
                const pieceSlug = pieceName ? slugify(pieceName) : '';
                const streaming = hasBand && pieceName ? resolveStreaming(performance, bandName, pieceName) : null;
                return { pieceName, pieceSlug, streaming };
              })}
              {@const streamingEntries = pieceEntries.filter((item) => hasStreamingLinks(item.streaming))}
              <tr>
                <td data-label="År">{performance.year}</td>
                <td data-label="Divisjon" class="division-cell"><a href={`?type=${bandType}&view=data&year=${performance.year}&division=${encodeURIComponent(performance.division ?? '')}`} class="entity-link">{performance.division}</a></td>
                <td data-label="Plass" class="rank-col">{getTrophy(performance.rank)}{formatRank(performance.rank)}</td>
                <td data-label="Poeng">{formatPoints(performance.points)}</td>
                <td data-label="Korps">
                  {#if hasBand && bandSlug}
                    <a
                      href={`?type=${bandType}&view=bands&band=${encodeURIComponent(bandSlug)}`}
                      class="entity-link"
                    >
                      {bandName}
                    </a>
                  {:else if hasBand}
                    <span>{bandName}</span>
                  {:else}
                    <span>Ukjent</span>
                  {/if}
                </td>
                <td data-label="Program" class="piece-cell">
                  {#if pieceEntries.length > 0}
                    <ul class="piece-list">
                      {#each pieceEntries as pieceEntry}
                        {@const lengdeInline = formatLengde(pieceEntry.streaming?.duration_seconds, pieceLengthResolver?.(pieceEntry.pieceName))}
                        <li>
                          {#if pieceEntry.pieceSlug}
                            <a
                              href={`?type=${bandType}&view=pieces&piece=${encodeURIComponent(pieceEntry.pieceSlug)}`}
                              class="entity-link"
                            >
                              {pieceEntry.pieceName}
                            </a>
                          {:else if pieceEntry.pieceName}
                            <span>{pieceEntry.pieceName}</span>
                          {:else}
                            <span>Ukjent</span>
                          {/if}
                          <span class="piece-opptak-mobile">
                            {#if hasStreamingLinks(pieceEntry.streaming)}
                              <span class="streaming-links">
                                {#if pieceEntry.streaming?.spotify}
                                  <a href={pieceEntry.streaming.spotify} target="_blank" rel="noopener noreferrer" class="streaming-link spotify" title={buildStreamingTitle(pieceEntry.pieceName, pieceEntry.streaming, 'spotify')}>
                                    <span class="sr-only">Hør {pieceEntry.pieceName} på Spotify</span>
                                    <svg class="streaming-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="10.5" opacity="0.15" fill="currentColor" /><path d="M16.88 16.13a.75.75 0 0 0-1.03-.26c-2.36 1.43-5.48 1.8-9.09 1.04a.75.75 0 1 0-.3 1.47c3.96.81 7.47.39 10.05-1.12a.75.75 0 0 0 .37-.37.75.75 0 0 0 0-.76z" fill="currentColor" /><path d="M16.1 13.69c-2.01 1.2-4.92 1.55-8.16.9a.75.75 0 0 0-.29 1.47c3.56.71 6.91.31 9.27-1.08a.75.75 0 0 0-.77-1.29h-.05z" fill="currentColor" opacity="0.8" /><path d="M15.24 11.12c-1.76 1.04-4.31 1.34-7.15.79a.75.75 0 0 0-.29 1.47c3.15.6 6.02.27 8.07-.96a.75.75 0 0 0-.77-1.3h-.04z" fill="currentColor" opacity="0.6" /></svg>
                                  </a>
                                {/if}
                                {#if pieceEntry.streaming?.apple_music}
                                  {@const appleHref = toAppleMusicHref(pieceEntry.streaming.apple_music)}
                                  {#if appleHref}
                                    <a href={appleHref} target="_blank" rel="noopener noreferrer" class="streaming-link apple" title={buildStreamingTitle(pieceEntry.pieceName, pieceEntry.streaming, 'apple')}>
                                      <span class="sr-only">Hør {pieceEntry.pieceName} på Apple Music</span>
                                      <svg class="streaming-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="10.5" opacity="0.15" fill="currentColor" /><path d="M14.75 6.75a.75.75 0 0 1 .75.75v6.33a2.92 2.92 0 1 1-1.5-2.54V9.25h-1.5A.75.75 0 0 1 12 8.5v-1a.75.75 0 0 1 .75-.75z" fill="currentColor" /><path d="M9.75 13.75a.75.75 0 0 1 .75.75c0 .69.56 1.25 1.25 1.25s1.25-.56 1.25-1.25a.75.75 0 0 1 1.5 0 2.75 2.75 0 1 1-5.5 0 .75.75 0 0 1 .75-.75z" fill="currentColor" opacity="0.8" /></svg>
                                    </a>
                                  {/if}
                                {/if}
                                {#if pieceEntry.streaming?.youtube}
                                  <a href={pieceEntry.streaming.youtube} target="_blank" rel="noopener noreferrer" class="streaming-link youtube" title={`${pieceEntry.pieceName} (YouTube)`}>
                                    <span class="sr-only">Hør {pieceEntry.pieceName} på YouTube</span>
                                    <svg class="streaming-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="10.5" opacity="0.15" fill="currentColor" /><path d="M19.6 8.2a2.4 2.4 0 0 0-1.69-1.7C16.54 6.2 12 6.2 12 6.2s-4.54 0-5.91.3A2.4 2.4 0 0 0 4.4 8.2C4.1 9.58 4.1 12 4.1 12s0 2.42.3 3.8a2.4 2.4 0 0 0 1.69 1.7c1.37.3 5.91.3 5.91.3s4.54 0 5.91-.3a2.4 2.4 0 0 0 1.69-1.7c.3-1.38.3-3.8.3-3.8s0-2.42-.3-3.8z" fill="currentColor" /><path d="M10.2 14.8V9.2l5.2 2.8-5.2 2.8z" fill="var(--color-surface-card, #1a1f2e)" /></svg>
                                  </a>
                                {/if}
                              </span>
                            {/if}
                            {#if lengdeInline}<span class="lengde-mobile">{lengdeInline}</span>{/if}
                          </span>
                        </li>
                      {/each}
                    </ul>
                  {:else}
                    <span>Ukjent</span>
                  {/if}
                </td>
                <td data-label="Opptak" class="streaming-cell">
                  {#if streamingEntries.length > 0}
                    <div class="streaming-list">
                      {#each streamingEntries as streamingEntry}
                        {@const streaming = streamingEntry.streaming}
                        {@const lengdeMobile = formatLengde(streaming?.duration_seconds, pieceLengthResolver?.(streamingEntry.pieceName))}
                        <div class="streaming-piece-row">
                          <span class="streaming-links">
                            {#if streaming?.spotify}
                          <a
                            href={streaming.spotify}
                            target="_blank"
                            rel="noopener noreferrer"
                            class="streaming-link spotify"
                            title={buildStreamingTitle(streamingEntry.pieceName, streaming, 'spotify')}
                          >
                            <span class="sr-only">Hør {streamingEntry.pieceName} på Spotify</span>
                            <svg class="streaming-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                              <circle cx="12" cy="12" r="10.5" opacity="0.15" fill="currentColor" />
                              <path
                                d="M16.88 16.13a.75.75 0 0 0-1.03-.26c-2.36 1.43-5.48 1.8-9.09 1.04a.75.75 0 1 0-.3 1.47c3.96.81 7.47.39 10.05-1.12a.75.75 0 0 0 .37-.37.75.75 0 0 0 0-.76z"
                                fill="currentColor"
                              />
                              <path
                                d="M16.1 13.69c-2.01 1.2-4.92 1.55-8.16.9a.75.75 0 0 0-.29 1.47c3.56.71 6.91.31 9.27-1.08a.75.75 0 0 0-.77-1.29h-.05z"
                                fill="currentColor"
                                opacity="0.8"
                              />
                              <path
                                d="M15.24 11.12c-1.76 1.04-4.31 1.34-7.15.79a.75.75 0 0 0-.29 1.47c3.15.6 6.02.27 8.07-.96a.75.75 0 0 0-.77-1.3h-.04z"
                                fill="currentColor"
                                opacity="0.6"
                              />
                            </svg>
                          </a>
                        {/if}
                        {#if streaming?.apple_music}
                          {@const appleHref = toAppleMusicHref(streaming.apple_music)}
                          {#if appleHref}
                            <a
                              href={appleHref}
                              target="_blank"
                              rel="noopener noreferrer"
                              class="streaming-link apple"
                              title={buildStreamingTitle(streamingEntry.pieceName, streaming, 'apple')}
                            >
                              <span class="sr-only">Hør {streamingEntry.pieceName} på Apple Music</span>
                              <svg class="streaming-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                                <circle cx="12" cy="12" r="10.5" opacity="0.15" fill="currentColor" />
                                <path
                                  d="M14.75 6.75a.75.75 0 0 1 .75.75v6.33a2.92 2.92 0 1 1-1.5-2.54V9.25h-1.5A.75.75 0 0 1 12 8.5v-1a.75.75 0 0 1 .75-.75z"
                                  fill="currentColor"
                                />
                                <path
                                  d="M9.75 13.75a.75.75 0 0 1 .75.75c0 .69.56 1.25 1.25 1.25s1.25-.56 1.25-1.25a.75.75 0 0 1 1.5 0 2.75 2.75 0 1 1-5.5 0 .75.75 0 0 1 .75-.75z"
                                  fill="currentColor"
                                  opacity="0.8"
                                />
                              </svg>
                            </a>
                          {/if}
                        {/if}
                        {#if streaming?.youtube}
                          <a
                            href={streaming.youtube}
                            target="_blank"
                            rel="noopener noreferrer"
                            class="streaming-link youtube"
                            title={`${streamingEntry.pieceName} (YouTube)`}
                          >
                            <span class="sr-only">Hør {streamingEntry.pieceName} på YouTube</span>
                            <svg class="streaming-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                              <circle cx="12" cy="12" r="10.5" opacity="0.15" fill="currentColor" />
                              <path
                                d="M19.6 8.2a2.4 2.4 0 0 0-1.69-1.7C16.54 6.2 12 6.2 12 6.2s-4.54 0-5.91.3A2.4 2.4 0 0 0 4.4 8.2C4.1 9.58 4.1 12 4.1 12s0 2.42.3 3.8a2.4 2.4 0 0 0 1.69 1.7c1.37.3 5.91.3 5.91.3s4.54 0 5.91-.3a2.4 2.4 0 0 0 1.69-1.7c.3-1.38.3-3.8.3-3.8s0-2.42-.3-3.8z"
                                fill="currentColor"
                              />
                              <path d="M10.2 14.8V9.2l5.2 2.8-5.2 2.8z" fill="var(--color-surface-card, #1a1f2e)" />
                            </svg>
                          </a>
                        {/if}
                          </span>
                          {#if lengdeMobile}<span class="lengde-mobile">{lengdeMobile}</span>{/if}
                        </div>
                      {/each}
                    </div>
                  {:else}
                    {#each pieceEntries as pieceEntry}
                      {@const lm = formatLengde(null, pieceLengthResolver?.(pieceEntry.pieceName))}
                      {#if lm}<span class="lengde-mobile">{lm}</span>{/if}
                    {/each}
                    <span class="streaming-missing" aria-hidden="true">–</span>
                  {/if}
                </td>
                <td data-label="Lengde" class="lengde-cell">
                  <div class="lengde-list">
                    {#each pieceEntries as pieceEntry}
                      {@const l = formatLengde(pieceEntry.streaming?.duration_seconds, pieceLengthResolver?.(pieceEntry.pieceName))}
                      {#if l}<div class="lengde-row">{l}</div>{/if}
                    {/each}
                  </div>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </article>
  {/each}
</section>

<style>
  .conductor-performances {
    display: flex;
    flex-direction: column;
    gap: 1.75rem;
    margin-top: 1.5rem;
  }

  .conductor-card {
    padding: 1.5rem;
    background: var(--color-surface-card);
    border-radius: 1rem;
    border: 1px solid var(--color-border);
    box-shadow: 0 18px 40px rgba(15, 23, 42, 0.25);
  }

  .conductor-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .card-remove-btn {
    flex-shrink: 0;
    border: none;
    background: transparent;
    color: var(--color-text-secondary);
    cursor: pointer;
    font-size: 1.1rem;
    line-height: 1;
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
    align-self: flex-start;
  }
  .card-remove-btn:hover {
    color: var(--color-warning);
    background: var(--color-chip-bg);
  }

  .conductor-header h2 {
    margin: 0;
    color: var(--color-accent);
  }

  .conductor-header p {
    margin: 0.25rem 0 0;
    color: var(--color-text-secondary);
    font-size: 0.9rem;
  }

  .conductor-count {
    font-size: 0.85rem;
  }

  .trophy-summary {
    font-size: 1rem;
    font-weight: 600;
    color: var(--color-text-primary);
  }

  .rank-col {
    white-space: nowrap;
  }

  .table-wrapper {
    overflow-x: auto;
    border-radius: 0.85rem;
    border: 1px solid var(--color-border);
  }

  table {
    width: 100%;
    border-collapse: collapse;
    min-width: 640px;
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

  th.sortable {
    cursor: pointer;
    user-select: none;
    white-space: nowrap;
  }

  th.sortable:hover {
    background: rgba(255, 255, 255, 0.05);
  }

  .sort-indicator {
    font-size: 0.85em;
    margin-left: 0.25rem;
    opacity: 0.8;
  }

  tbody tr:nth-child(even) {
    background: rgba(255, 255, 255, 0.02);
  }

  tbody td {
    border-top: 1px solid var(--color-border);
    color: var(--color-text-primary);
    font-size: 0.95rem;
  }

  .division-column,
  .division-cell {
    white-space: nowrap;
  }

  .piece-cell {
    min-width: 220px;
  }

  .piece-list {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    padding: 0;
    margin: 0;
    list-style: none;
  }

  .piece-list li {
    display: flex;
    align-items: center;
    gap: 0.35rem;
  }

  .entity-link {
    color: var(--color-accent);
    text-decoration: none;
  }

  .entity-link:hover,
  .entity-link:focus-visible {
    text-decoration: underline;
  }

  .streaming-column,
  .streaming-cell {
    text-align: center;
  }

  .streaming-cell {
    white-space: nowrap;
  }

  .streaming-list {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    align-items: flex-end;
  }

  .streaming-piece-row {
    display: flex;
    align-items: center;
    justify-content: flex-end;
  }

  .streaming-links {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.35rem;
  }

  .streaming-link {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.75rem;
    height: 1.75rem;
    border-radius: 999px;
    color: var(--color-text-secondary);
    transition: transform 0.15s ease, color 0.15s ease, box-shadow 0.15s ease;
  }

  .streaming-link.spotify {
    color: #1db954;
  }

  .streaming-link.apple {
    color: #fa2d48;
  }

  .streaming-link.youtube {
    color: #ff0000;
  }

  .streaming-link:hover,
  .streaming-link:focus-visible {
    transform: translateY(-1px) scale(1.05);
    box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.2);
  }

  .streaming-link:focus-visible {
    outline: 2px solid var(--color-accent);
    outline-offset: 2px;
  }

  .streaming-icon {
    width: 1.25rem;
    height: 1.25rem;
    fill: currentColor;
  }

  .streaming-missing {
    color: var(--color-text-secondary);
  }

  .lengde-mobile {
    display: none;
  }

  .piece-opptak-mobile {
    display: none;
  }

  .lengde-column,
  .lengde-cell {
    text-align: right;
    white-space: nowrap;
    color: var(--color-text-secondary);
    font-size: 0.9rem;
  }

  .lengde-list {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    align-items: flex-end;
  }

  .lengde-row {
    min-height: 1.75rem;
    display: flex;
    align-items: center;
    justify-content: flex-end;
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

  td[data-label]::before {
    content: attr(data-label);
    display: none;
    font-weight: 600;
    margin-right: 0.5rem;
  }

  @media (max-width: 640px) {
    .conductor-card {
      padding: 0.75rem 0.5rem; /* Reduced from 1.5rem for narrower viewports */
    }

    .conductor-header h2 {
      font-size: 1.25rem; /* Reduced header size for mobile */
    }

    table {
      min-width: auto;
    }

    thead {
      display: none;
    }

    tbody tr {
      display: grid;
      grid-template-columns: 68% 32%;
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

    /* Reorder cells: År/Divisjon, Plass/Poeng, Korps (full width), Program (full width) */
    td[data-label="År"] { order: 1; }
    td[data-label="Divisjon"] { order: 2; }
    td[data-label="Plass"] { order: 3; }
    td[data-label="Poeng"] { order: 4; }
    td[data-label="Korps"] { order: 5; grid-column: 1 / -1; }
    td[data-label="Program"] { order: 6; grid-column: 1 / -1; }
    td[data-label="Opptak"] { display: none; }
    td[data-label="Lengde"] { display: none; }

    /* Each piece row: name left, streaming+duration right */
    .piece-list li {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;
      flex-wrap: nowrap;
    }

    .entity-link {
      flex: 1;
      min-width: 0;
      word-break: break-word;
      overflow-wrap: break-word;
      hyphens: auto;
    }

    /* Mobile streaming inline with piece */
    .piece-opptak-mobile {
      display: flex;
      align-items: center;
      gap: 0.3rem;
      flex-shrink: 0;
    }

    .lengde-mobile {
      display: inline-block;
      width: 2.2ch;
      text-align: right;
      color: var(--color-text-secondary);
      font-size: 0.85rem;
      white-space: nowrap;
    }
  }
</style>
