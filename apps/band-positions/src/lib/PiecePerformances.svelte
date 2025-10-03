<script lang="ts">
  import type { PieceRecord, PiecePerformance, BandType, StreamingLink } from './types';
  import { extractComposerNames } from './composerUtils';
  import { slugify } from './slugify';

  interface Props {
    pieces?: PieceRecord[];
    bandType?: BandType;
  }

  let { pieces = [], bandType = 'wind' }: Props = $props();

  const pointsFormatter = new Intl.NumberFormat('nb-NO', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1
  });

  function sortPerformances(performances: PiecePerformance[]): PiecePerformance[] {
    return [...performances].sort((a, b) => {
      const yearDiff = a.entry.year - b.entry.year;
      if (yearDiff !== 0) return yearDiff;
      const rankA = a.entry.rank ?? Number.POSITIVE_INFINITY;
      const rankB = b.entry.rank ?? Number.POSITIVE_INFINITY;
      if (rankA !== rankB) return rankA - rankB;
      return a.band.localeCompare(b.band);
    });
  }

  function resolveComposerNames(piece: PieceRecord): string[] {
    if (piece.composerNames && piece.composerNames.length > 0) {
      return piece.composerNames;
    }
    if (piece.composer) {
      return extractComposerNames(piece.composer);
    }
    return [];
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

  let sortedPieces = $derived(pieces.map((piece) => ({
    ...piece,
    performances: sortPerformances(piece.performances)
  })));
</script>

<section class="pieces-view">
  {#each sortedPieces as piece}
    {@const composerNames = resolveComposerNames(piece)}
    <article class="piece-card">
      <header class="piece-header">
        <div>
          <h2>{piece.name}</h2>
          {#if composerNames.length > 0}
            <p class="piece-composer">
              {#each composerNames as composerName, index}
                <a
                  href={`?type=${bandType}&view=composers&composer=${encodeURIComponent(slugify(composerName))}`}
                  class="composer-link"
                >
                  {composerName}
                </a>{index < composerNames.length - 1 ? ', ' : ''}
              {/each}
            </p>
          {:else if piece.composer}
            <p class="piece-composer">{piece.composer}</p>
          {/if}
          <p class="piece-count">{piece.performances.length} fremføringer</p>
        </div>
      </header>

      <div class="table-wrapper" role="region" aria-label={`Fremføringer av ${piece.name}`}>
        <table>
          <thead>
            <tr>
              <th scope="col">År</th>
              <th scope="col">Divisjon</th>
              <th scope="col">Korps</th>
              <th scope="col">Plass</th>
              <th scope="col">Poeng</th>
              <th scope="col">Dirigent</th>
              <th scope="col" class="streaming-column">Opptak</th>
            </tr>
          </thead>
          <tbody>
            {#each piece.performances as performance}
              {@const conductorName = performance.entry.conductor?.trim() ?? ''}
              {@const hasConductor = conductorName.length > 0}
              {@const conductorSlug = hasConductor ? slugify(conductorName) : ''}
              {@const bandSlug = slugify(performance.band)}
              {@const streaming = performance.streaming ?? null}
              <tr>
                <td data-label="År">{performance.entry.year}</td>
                <td data-label="Divisjon">{performance.entry.division}</td>
                <td data-label="Korps">
                  <a
                    href={`?type=${bandType}&view=bands&band=${encodeURIComponent(bandSlug)}`}
                    class="entity-link"
                  >
                    {performance.band}
                  </a>
                </td>
                <td data-label="Plass">{formatRank(performance.entry.rank)}</td>
                <td data-label="Poeng">{formatPoints(performance.entry.points)}</td>
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
                <td data-label="Opptak" class="streaming-cell">
                  {#if hasStreamingLinks(streaming)}
                    <div class="streaming-links">
                      {#if streaming?.spotify}
                        <a
                          href={streaming.spotify}
                          target="_blank"
                          rel="noopener noreferrer"
                          class="streaming-link spotify"
                          title={buildStreamingTitle(piece.name, streaming, 'spotify')}
                        >
                          <span class="sr-only">Hør på Spotify</span>
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
                            title={buildStreamingTitle(piece.name, streaming, 'apple')}
                          >
                            <span class="sr-only">Hør på Apple Music</span>
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
  .pieces-view {
    display: flex;
    flex-direction: column;
    gap: 1.75rem;
    margin-top: 1rem;
  }

  .piece-card {
    padding: 1.5rem;
    background: var(--color-surface-card);
    border-radius: 1rem;
    border: 1px solid var(--color-border);
    box-shadow: 0 18px 40px rgba(15, 23, 42, 0.25);
  }

  .piece-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .piece-header h2 {
    margin: 0;
    color: var(--color-accent);
  }

  .piece-header p {
    margin: 0.25rem 0 0;
    color: var(--color-text-secondary);
    font-size: 0.9rem;
  }

  .piece-header .piece-composer {
    font-size: 0.95rem;
    font-style: italic;
  }

  .piece-header .piece-composer .composer-link {
    color: var(--color-accent);
    text-decoration: none;
  }

  .piece-header .piece-composer .composer-link:hover,
  .piece-header .piece-composer .composer-link:focus-visible {
    text-decoration: underline;
  }

  .entity-link {
    color: var(--color-accent);
    text-decoration: none;
  }

  .entity-link:hover,
  .entity-link:focus-visible {
    text-decoration: underline;
  }

  .piece-header .piece-count {
    font-size: 0.85rem;
  }

  .piece-header .piece-composer + .piece-count {
    margin-top: 0.15rem;
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

  tbody tr:nth-child(even) {
    background: rgba(255, 255, 255, 0.02);
  }

  tbody td {
    border-top: 1px solid var(--color-border);
    color: var(--color-text-primary);
    font-size: 0.95rem;
  }

  .streaming-column,
  .streaming-cell {
    text-align: center;
  }

  .streaming-cell {
    white-space: nowrap;
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
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 0.35rem 0.75rem;
      padding: 0.85rem 1rem;
    }

    tbody td {
      border: none;
      padding: 0;
      display: flex;
      align-items: baseline;
      gap: 0.35rem;
    }

    td[data-label]::before {
      display: inline-flex;
      color: var(--color-text-secondary);
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.02em;
    }

    .streaming-cell {
      justify-content: flex-end;
    }

    .streaming-links {
      justify-content: flex-end;
    }
  }
</style>
