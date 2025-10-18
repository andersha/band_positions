<script lang="ts">
  import type { BandRecord, BandEntry, BandType, StreamingLink, EliteTestPiecesData } from './types';
  import { slugify } from './slugify';
  import { getTrophy, countTrophies, formatTrophySummary } from './trophyUtils';

  interface Props {
    bands?: BandRecord[];
    bandType?: BandType;
    streamingResolver?: (entry: BandEntry, bandName: string, pieceName: string) => StreamingLink | null;
    eliteTestPieces?: EliteTestPiecesData | null;
  }

  let { bands = [], bandType = 'wind', streamingResolver, eliteTestPieces = null }: Props = $props();

  const pointsFormatter = new Intl.NumberFormat('nb-NO', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1
  });

  // Sorting state and utilities
  type Direction = 'asc' | 'desc';
  type BandSortColumn = 'year' | 'division' | 'rank' | 'points' | 'conductor';

  let sortColumn = $state<BandSortColumn>('year');
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

  function ariaSort(current: BandSortColumn, target: BandSortColumn, dir: Direction): 'ascending' | 'descending' | 'none' {
    if (current !== target) return 'none';
    return dir === 'asc' ? 'ascending' : 'descending';
  }

  function indicator(current: BandSortColumn, target: BandSortColumn, dir: Direction): string {
    if (current !== target) return '';
    return dir === 'asc' ? ' ▲' : ' ▼';
  }

  function handleSort(column: BandSortColumn) {
    if (sortColumn === column) {
      sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      sortColumn = column;
      // Points should default to descending (highest first)
      sortDirection = column === 'points' ? 'desc' : 'asc';
    }
  }

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

  function getValue(entry: BandEntry, column: BandSortColumn) {
    switch (column) {
      case 'year': return entry.year;
      case 'division': return getDivisionRank(entry.division ?? null);
      case 'rank': return entry.rank ?? entry.absolute_position ?? null;
      case 'points': return entry.points ?? null;
      case 'conductor': return entry.conductor ?? null;
    }
  }

  function sortEntries(entries: BandEntry[]): BandEntry[] {
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

  function hasStreamingLinks(streaming?: StreamingLink | null): boolean {
    return Boolean(streaming?.spotify || streaming?.apple_music);
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

  function testPieceForYear(year: string | number): { composer: string; piece: string } | null {
    const y = String(year);
    const tp = eliteTestPieces?.test_pieces?.[y];
    return tp ? { composer: tp.composer, piece: tp.piece } : null;
  }

  function isEliteDivision(division: string | undefined): boolean {
    return (division || '').toLowerCase() === 'elite';
  }

  let normalizedBands = $derived(
    bands.map((band) => ({
      ...band,
      entries: sortEntries(band.entries)
    }))
  );
</script>

<section class="band-performances">
  {#each normalizedBands as band}
    {@const trophyCount = countTrophies(band.entries)}
    {@const trophySummary = formatTrophySummary(trophyCount)}
    <article class="band-card">
      <header class="band-header">
        <div>
          <h2>{band.name}</h2>
          {#if trophySummary}
            <p class="trophy-summary">{trophySummary}</p>
          {/if}
          <p class="band-count">{band.entries.length} fremføringer</p>
        </div>
      </header>

      <div class="table-wrapper" role="region" aria-label={`Fremføringer av ${band.name}`}>
        <table>
          <thead>
            <tr>
              <th scope="col" class="sortable" onclick={() => handleSort('year')} aria-sort={ariaSort(sortColumn, 'year', sortDirection)}>År<span class="sort-indicator">{indicator(sortColumn, 'year', sortDirection)}</span></th>
              <th scope="col" class="division-column sortable" onclick={() => handleSort('division')} aria-sort={ariaSort(sortColumn, 'division', sortDirection)}>Divisjon<span class="sort-indicator">{indicator(sortColumn, 'division', sortDirection)}</span></th>
              <th scope="col" class="sortable" onclick={() => handleSort('rank')} aria-sort={ariaSort(sortColumn, 'rank', sortDirection)}>Plass<span class="sort-indicator">{indicator(sortColumn, 'rank', sortDirection)}</span></th>
              <th scope="col" class="sortable" onclick={() => handleSort('points')} aria-sort={ariaSort(sortColumn, 'points', sortDirection)}>Poeng<span class="sort-indicator">{indicator(sortColumn, 'points', sortDirection)}</span></th>
              <th scope="col" class="sortable" onclick={() => handleSort('conductor')} aria-sort={ariaSort(sortColumn, 'conductor', sortDirection)}>Dirigent<span class="sort-indicator">{indicator(sortColumn, 'conductor', sortDirection)}</span></th>
              <th scope="col">Program</th>
              <th scope="col" class="streaming-column">Opptak</th>
            </tr>
          </thead>
          <tbody>
            {#each band.entries as entry}
              {@const rawPieces = Array.isArray(entry.pieces) ? entry.pieces : []}
              {@const pieces = rawPieces.filter((piece) => piece && piece.trim().length > 0)}
              {@const testPiece = bandType === 'brass' && isEliteDivision(entry.division) ? testPieceForYear(entry.year) : null}
              {@const conductorName = entry.conductor?.trim() ?? ''}
              {@const hasConductor = conductorName.length > 0}
              {@const conductorSlug = hasConductor ? slugify(conductorName) : ''}
              {@const ownChoicePieceEntries = pieces.map((piece) => {
                const pieceName = piece.trim();
                const pieceSlug = pieceName ? slugify(pieceName) : '';
                const streaming = pieceName ? resolveStreaming(entry, band.name, pieceName) : null;
                return { pieceName, pieceSlug, streaming, isTestPiece: false };
              })}
              {@const testPieceEntry = testPiece ? [{
                pieceName: testPiece.piece,
                pieceSlug: slugify(testPiece.piece),
                streaming: resolveStreaming(entry, band.name, testPiece.piece),
                isTestPiece: true
              }] : []}
              {@const pieceEntries = [...testPieceEntry, ...ownChoicePieceEntries]}
              {@const streamingEntries = pieceEntries.filter((item) => hasStreamingLinks(item.streaming))}
              <tr>
                <td data-label="År">{entry.year}</td>
                <td data-label="Divisjon" class="division-cell">{entry.division}</td>
                <td data-label="Plass" class="rank-col">{getTrophy(entry.rank)}{formatRank(entry.rank)}</td>
                <td data-label="Poeng">{formatPoints(entry.points)}</td>
                <td data-label="Dirigent">
                  {#if hasConductor}
                    <a
                      href={`?type=${bandType}&view=conductors&conductor=${encodeURIComponent(conductorSlug)}`}
                      class="entity-link"
                    >
                      {conductorName}
                    </a>
                  {:else}
                    <span>Ukjent</span>
                  {/if}
                </td>
                <td data-label="Program" class="piece-cell">
                  {#if pieceEntries.length > 0}
                    <ul class="piece-list">
                      {#each pieceEntries as pieceEntry}
                        <li>
                          {#if pieceEntry.isTestPiece}
                            <span class="test-piece-label" title="Pliktstykke (fredag)">P:</span>
                          {:else if bandType === 'brass' && isEliteDivision(entry.division)}
                            <span class="own-choice-label" title="Selvvalgt (lørdag)">S:</span>
                          {/if}
                          {#if pieceEntry.pieceSlug}
                            <a
                              href={`?type=${bandType}&view=pieces&piece=${encodeURIComponent(pieceEntry.pieceSlug)}`}
                              class="entity-link"
                              class:test-piece-link={pieceEntry.isTestPiece}
                            >
                              {pieceEntry.pieceName}
                            </a>
                          {:else if pieceEntry.pieceName}
                            <span>{pieceEntry.pieceName}</span>
                          {:else}
                            <span>Ukjent</span>
                          {/if}
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
                        {#if hasStreamingLinks(streaming)}
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
                            </span>
                          </div>
                        {/if}
                      {/each}
                    </div>
                  {:else}
                    <span class="streaming-missing" aria-hidden="true">–</span>
                  {/if}
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
  .band-performances {
    display: flex;
    flex-direction: column;
    gap: 1.75rem;
    margin-top: 1.5rem;
  }

  .band-card {
    padding: 1.5rem;
    background: var(--color-surface-card);
    border-radius: 1rem;
    border: 1px solid var(--color-border);
    box-shadow: 0 18px 40px rgba(15, 23, 42, 0.25);
  }

  .band-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .band-header h2 {
    margin: 0;
    color: var(--color-accent);
  }

  .band-header p {
    margin: 0.25rem 0 0;
    color: var(--color-text-secondary);
    font-size: 0.9rem;
  }

  .band-count {
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
    min-width: 560px;
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
    min-width: 200px;
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
    justify-content: center;
    min-height: 1.75rem;
  }

  .streaming-links {
    display: inline-flex;
    align-items: center;
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

  .test-piece-label,
  .own-choice-label {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.7rem;
    font-weight: 700;
    border-radius: 0.25rem;
    padding: 0.1rem 0.3rem;
    margin-right: 0.35rem;
    text-transform: uppercase;
    letter-spacing: 0.02em;
  }

  .test-piece-label {
    color: var(--color-accent);
    background: rgba(var(--color-accent-rgb, 147, 51, 234), 0.1);
    border: 1px solid var(--color-accent);
  }

  .own-choice-label {
    color: #10b981;
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid #10b981;
  }

  .test-piece-link {
    font-weight: 600;
  }

  td[data-label]::before {
    content: attr(data-label);
    display: none;
    font-weight: 600;
    margin-right: 0.5rem;
  }

  @media (max-width: 640px) {
    table {
      min-width: auto;
    }

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

    /* Reorder cells: År/Divisjon, Plass/Poeng, Dirigent (full width), Program/Opptak */
    td[data-label="År"] { order: 1; }
    td[data-label="Divisjon"] { order: 2; }
    td[data-label="Plass"] { order: 3; }
    td[data-label="Poeng"] { order: 4; }
    td[data-label="Dirigent"] { order: 5; grid-column: 1 / -1; }
    td[data-label="Program"] { order: 6; }
    td[data-label="Opptak"] { order: 7; }

    /* Adjust piece list for mobile */
    .piece-list li {
      flex-wrap: wrap;
      gap: 0.25rem;
    }

    /* Ensure piece names can wrap */
    .entity-link {
      word-break: break-word;
      overflow-wrap: break-word;
      hyphens: auto;
    }

    /* Keep streaming icons aligned to the right on mobile, but label left-aligned */
    .streaming-cell {
      align-items: flex-start;
    }

    .streaming-list {
      align-items: flex-end;
    }

    .streaming-piece-row {
      justify-content: flex-end;
    }
  }
</style>
