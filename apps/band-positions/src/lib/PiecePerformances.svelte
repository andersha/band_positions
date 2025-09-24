<script lang="ts">
  import type { PieceRecord, PiecePerformance } from './types';

  interface Props {
    pieces?: PieceRecord[];
  }

  let { pieces = [] }: Props = $props();

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

  function formatPoints(points: number | null): string {
    if (points == null) return '–';
    return pointsFormatter.format(points);
  }

  function formatRank(rank: number | null): string {
    return rank != null ? `${rank}` : '–';
  }

  let sortedPieces = $derived(pieces.map((piece) => ({
    ...piece,
    performances: sortPerformances(piece.performances)
  })));
</script>

<section class="pieces-view">
  {#each sortedPieces as piece}
    <article class="piece-card">
      <header class="piece-header">
        <div>
          <h2>{piece.name}</h2>
          <p>{piece.performances.length} fremføringer</p>
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
            </tr>
          </thead>
          <tbody>
            {#each piece.performances as performance}
              <tr>
                <td data-label="År">{performance.entry.year}</td>
                <td data-label="Divisjon">{performance.entry.division}</td>
                <td data-label="Korps">{performance.band}</td>
                <td data-label="Plass">{formatRank(performance.entry.rank)}</td>
                <td data-label="Poeng">{formatPoints(performance.entry.points)}</td>
                <td data-label="Dirigent">{performance.entry.conductor ?? 'Ukjent'}</td>
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
  }
</style>
