<script lang="ts">
  import { countTrophies } from './trophyUtils';
  import { slugify } from './slugify';
  import type { PieceRecord, ComposerRecord, BandRecord, BandType } from './types';

  interface Props {
    pieceRecords: PieceRecord[];
    composerRecords: ComposerRecord[];
    bands: BandRecord[];
    bandType: BandType;
    onViewPiece: (slug: string) => void;
    onViewComposer: (slug: string) => void;
    onViewBand: (slug: string) => void;
  }

  let { pieceRecords, composerRecords, bands, bandType, onViewPiece, onViewComposer, onViewBand }: Props = $props();

  type StatType = 'pieces' | 'trophies' | 'scores' | 'piece-scores';

  const PAGE_SIZE = 20;
  let selectedStat = $state<StatType>('pieces');
  let currentPage = $state(1);

  // Build a composer slug lookup map for fast access
  let composerSlugMap = $derived.by(() => {
    const map = new Map<string, string>(); // normalized name -> slug
    for (const c of composerRecords) {
      map.set(c.normalized, c.slug);
      map.set(slugify(c.name), c.slug);
    }
    return map;
  });

  function findComposerSlug(name: string): string | null {
    const norm = name.trim().toLowerCase();
    return composerSlugMap.get(norm) ?? composerSlugMap.get(slugify(name)) ?? null;
  }

  // Stat 1: Most popular pieces by number of performances
  let pieceStats = $derived.by(() => {
    return [...pieceRecords]
      .map(p => ({ piece: p, count: p.performances.length }))
      .filter(r => r.count > 0)
      .sort((a, b) => b.count - a.count || a.piece.name.localeCompare(b.piece.name, 'nb'));
  });

  // Stat 2: Trophy counts per band (Olympic sort)
  let trophyStats = $derived.by(() => {
    return bands
      .map(band => ({ band, trophies: countTrophies(band.entries) }))
      .filter(r => r.trophies.gold + r.trophies.silver + r.trophies.bronze > 0)
      .sort((a, b) => {
        if (b.trophies.gold !== a.trophies.gold) return b.trophies.gold - a.trophies.gold;
        if (b.trophies.silver !== a.trophies.silver) return b.trophies.silver - a.trophies.silver;
        return b.trophies.bronze - a.trophies.bronze;
      });
  });

  // Stat 3: Highest average score per band (min 3 scored performances)
  let scoreStats = $derived.by(() => {
    return bands
      .map(band => {
        const scored = band.entries.filter(e => e.points !== null);
        if (scored.length < 3) return null;
        const avg = scored.reduce((s, e) => s + e.points!, 0) / scored.length;
        return { band, count: scored.length, avg };
      })
      .filter((r): r is NonNullable<typeof r> => r !== null)
      .sort((a, b) => b.avg - a.avg || b.count - a.count);
  });

  // Stat 4: Highest average score per piece (min 3 scored performances)
  let pieceScoreStats = $derived.by(() => {
    return pieceRecords
      .map(piece => {
        const scored = piece.performances.filter(p => p.entry.points !== null);
        if (scored.length < 3) return null;
        const avg = scored.reduce((s, p) => s + p.entry.points!, 0) / scored.length;
        return { piece, count: scored.length, avg };
      })
      .filter((r): r is NonNullable<typeof r> => r !== null)
      .sort((a, b) => b.avg - a.avg || b.count - a.count);
  });

  let activeStats = $derived(
    selectedStat === 'pieces' ? pieceStats :
    selectedStat === 'trophies' ? trophyStats :
    selectedStat === 'scores' ? scoreStats :
    pieceScoreStats
  );

  let totalPages = $derived(Math.ceil(activeStats.length / PAGE_SIZE));

  let paginatedStats = $derived.by(() => {
    const start = (currentPage - 1) * PAGE_SIZE;
    return activeStats.slice(start, start + PAGE_SIZE);
  });

  function changeStat(stat: StatType) {
    selectedStat = stat;
    currentPage = 1;
  }
</script>

<div class="statistics-page">
  <div class="stats-controls">
    <select
      value={selectedStat}
      onchange={(e) => changeStat((e.currentTarget as HTMLSelectElement).value as StatType)}
      class="stat-select"
    >
      <option value="pieces">Mest fremførte verk</option>
      <option value="trophies">Flest medaljer (korps)</option>
      <option value="scores">Høyest snittpoeng (korps)</option>
      <option value="piece-scores">Høyest snittpoeng (stykke)</option>
    </select>
    <span class="results-count">{activeStats.length} resultater</span>
  </div>

  <div class="table-container">
    {#if selectedStat === 'pieces'}
      <table class="stats-table stats-pieces">
        <thead>
          <tr>
            <th class="rank-col">#</th>
            <th>Verk</th>
            <th>Komponist</th>
            <th class="num-col">Fremføringer</th>
          </tr>
        </thead>
        <tbody>
          {#each paginatedStats as row, i (row.piece.slug)}
            {@const rank = (currentPage - 1) * PAGE_SIZE + i + 1}
            <tr>
              <td class="rank-cell">{rank}</td>
              <td class="name-cell">
                <button class="link-btn" onclick={() => onViewPiece(row.piece.slug)}>
                  {row.piece.name}
                </button>
              </td>
              <td class="composer-cell">
                {#if row.piece.composerNames && row.piece.composerNames.length > 0}
                  {#each row.piece.composerNames as name, ci}
                    {#if ci > 0}<span class="composer-sep">, </span>{/if}
                    {@const cSlug = findComposerSlug(name)}
                    {#if cSlug}
                      <button class="link-btn composer-link" onclick={() => onViewComposer(cSlug)}>
                        {name}
                      </button>
                    {:else}
                      <span>{name}</span>
                    {/if}
                  {/each}
                {:else}
                  <span class="empty">—</span>
                {/if}
              </td>
              <td class="piece-count-cell">{row.count}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    {:else if selectedStat === 'trophies'}
      <table class="stats-table stats-trophies">
        <thead>
          <tr>
            <th class="rank-col">#</th>
            <th>Korps</th>
            <th class="num-col">🥇</th>
            <th class="num-col">🥈</th>
            <th class="num-col">🥉</th>
          </tr>
        </thead>
        <tbody>
          {#each paginatedStats as row, i (row.band.slug)}
            {@const rank = (currentPage - 1) * PAGE_SIZE + i + 1}
            <tr>
              <td class="rank-cell">{rank}</td>
              <td class="name-cell">
                <button class="link-btn" onclick={() => onViewBand(row.band.slug)}>
                  {row.band.name}
                </button>
              </td>
              <td class="gold-cell">{row.trophies.gold || '—'}</td>
              <td class="silver-cell">{row.trophies.silver || '—'}</td>
              <td class="bronze-cell">{row.trophies.bronze || '—'}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    {:else if selectedStat === 'piece-scores'}
      <table class="stats-table stats-piece-scores">
        <thead>
          <tr>
            <th class="rank-col">#</th>
            <th>Verk</th>
            <th>Komponist</th>
            <th class="num-col">Fremføringer</th>
            <th class="num-col">Snittpoeng</th>
          </tr>
        </thead>
        <tbody>
          {#each paginatedStats as row, i (row.piece.slug)}
            {@const rank = (currentPage - 1) * PAGE_SIZE + i + 1}
            <tr>
              <td class="rank-cell">{rank}</td>
              <td class="name-cell">
                <button class="link-btn" onclick={() => onViewPiece(row.piece.slug)}>
                  {row.piece.name}
                </button>
              </td>
              <td class="composer-cell">
                {#if row.piece.composerNames && row.piece.composerNames.length > 0}
                  {#each row.piece.composerNames as name, ci}
                    {#if ci > 0}<span class="composer-sep">, </span>{/if}
                    {@const cSlug = findComposerSlug(name)}
                    {#if cSlug}
                      <button class="link-btn composer-link" onclick={() => onViewComposer(cSlug)}>
                        {name}
                      </button>
                    {:else}
                      <span>{name}</span>
                    {/if}
                  {/each}
                {:else}
                  <span class="empty">—</span>
                {/if}
              </td>
              <td class="ps-count-cell">{row.count}</td>
              <td class="ps-avg-cell">{row.avg.toFixed(2)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    {:else}
      <table class="stats-table stats-scores">
        <thead>
          <tr>
            <th class="rank-col">#</th>
            <th>Korps</th>
            <th class="num-col">Fremføringer</th>
            <th class="num-col">Snittpoeng</th>
          </tr>
        </thead>
        <tbody>
          {#each paginatedStats as row, i (row.band.slug)}
            {@const rank = (currentPage - 1) * PAGE_SIZE + i + 1}
            <tr>
              <td class="rank-cell">{rank}</td>
              <td class="name-cell">
                <button class="link-btn" onclick={() => onViewBand(row.band.slug)}>
                  {row.band.name}
                </button>
              </td>
              <td class="score-count-cell">{row.count}</td>
              <td class="avg-cell">{row.avg.toFixed(2)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </div>

  {#if totalPages > 1}
    <div class="pagination">
      <button
        onclick={() => currentPage = Math.max(1, currentPage - 1)}
        disabled={currentPage === 1}
      >
        ‹ Forrige
      </button>
      <span class="page-info">Side {currentPage} av {totalPages}</span>
      <button
        onclick={() => currentPage = Math.min(totalPages, currentPage + 1)}
        disabled={currentPage === totalPages}
      >
        Neste ›
      </button>
    </div>
  {/if}
</div>

<style>
  .statistics-page {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .stats-controls {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .stat-select {
    padding: 0.5rem 0.75rem;
    border-radius: 0.6rem;
    border: 1px solid var(--color-border);
    background: var(--color-surface-card);
    color: var(--color-text-primary);
    font-size: 16px;
    cursor: pointer;
  }

  .results-count {
    font-size: 0.95rem;
    color: var(--color-text-secondary);
  }

  .table-container {
    overflow-x: auto;
    border-radius: 1rem;
    border: 1px solid var(--color-border);
    background: var(--color-surface-card);
    box-shadow: 0 18px 40px rgba(15, 23, 42, 0.25);
  }

  .stats-table {
    width: 100%;
    border-collapse: collapse;
  }

  .stats-table thead {
    background: var(--color-mode-toggle-bg);
  }

  .stats-table th {
    padding: 0.75rem 1rem;
    text-align: left;
    font-size: 0.85rem;
    letter-spacing: 0.02em;
    text-transform: uppercase;
    color: var(--color-text-secondary);
    user-select: none;
  }

  .stats-table th.rank-col {
    width: 3rem;
    text-align: right;
  }

  .stats-table th.num-col {
    text-align: right;
    width: 8rem;
  }

  .stats-table tbody tr:nth-child(even) {
    background: rgba(255, 255, 255, 0.02);
  }

  .stats-table tbody td {
    padding: 0.75rem 1rem;
    border-top: 1px solid var(--color-border);
    color: var(--color-text-primary);
    font-size: 0.95rem;
  }

  .rank-cell {
    text-align: right;
    color: var(--color-text-secondary);
    font-variant-numeric: tabular-nums;
    font-size: 0.85rem;
  }

  .name-cell {
    font-weight: 500;
  }

  .composer-cell {
    color: var(--color-text-secondary);
  }

  .piece-count-cell,
  .gold-cell,
  .silver-cell,
  .bronze-cell,
  .score-count-cell,
  .avg-cell,
  .ps-count-cell,
  .ps-avg-cell {
    text-align: right;
    font-variant-numeric: tabular-nums;
    color: var(--color-text-secondary);
  }

  .link-btn {
    appearance: none;
    background: none;
    border: none;
    padding: 0;
    margin: 0;
    color: var(--color-accent);
    cursor: pointer;
    font-size: inherit;
    font-weight: inherit;
    font-family: inherit;
    text-align: left;
    text-decoration: none;
    transition: opacity 0.15s ease;
  }

  .link-btn:hover {
    opacity: 0.8;
    text-decoration: underline;
  }

  .composer-link {
    font-weight: 400;
  }

  .empty {
    color: var(--color-text-secondary);
    opacity: 0.5;
  }

  .pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 1rem;
    padding: 1rem 0;
  }

  .pagination button {
    padding: 0.45rem 1rem;
    background: var(--color-accent);
    color: white;
    border: none;
    border-radius: 0.6rem;
    cursor: pointer;
    font-size: 0.95rem;
    font-weight: 500;
    transition: opacity 0.18s ease, transform 0.18s ease;
  }

  .pagination button:hover:not(:disabled) {
    opacity: 0.9;
    transform: translateY(-1px);
  }

  .pagination button:active:not(:disabled) {
    transform: translateY(0);
  }

  .pagination button:disabled {
    background: var(--color-border);
    cursor: not-allowed;
    opacity: 0.4;
  }

  .page-info {
    font-size: 0.95rem;
    color: var(--color-text-secondary);
    font-weight: 500;
  }

  /* ── Mobile layout ── */
  @media (max-width: 768px) {
    .stats-table thead {
      display: none;
    }

    .stats-table tbody td {
      border-top: none;
      padding: 0.1rem 0;
      text-align: left;
    }

    /* Shared row grid */
    .stats-table tbody tr {
      display: grid;
      grid-template-columns: 2rem 1fr auto;
      column-gap: 0.75rem;
      padding: 0.75rem 1rem;
      border-top: 1px solid var(--color-border);
    }

    /* ── Mest fremførte verk ──
       col 1: rank (spans 2 rows)
       col 2: title / composer
       col 3: Fremføringer: count (row 1 only)
    */
    .stats-pieces .rank-cell      { grid-column: 1; grid-row: 1 / 3; align-self: start; text-align: right; }
    .stats-pieces .name-cell      { grid-column: 2; grid-row: 1; }
    .stats-pieces .composer-cell  { grid-column: 2; grid-row: 2; font-size: 0.85rem; }
    .stats-pieces .piece-count-cell {
      grid-column: 3; grid-row: 1;
      align-self: center;
      text-align: right;
      white-space: nowrap;
    }
    .stats-pieces .piece-count-cell::before {
      content: 'Fremføringer: ';
      color: var(--color-text-secondary);
      font-size: 0.8rem;
    }

    /* ── Flest medaljer ──
       col 1: rank (spans 3 rows)
       col 2: band name (row 1)
       col 3: 🥇 / 🥈 / 🥉 counts (rows 1–3)
    */
    .stats-trophies .rank-cell   { grid-column: 1; grid-row: 1 / 4; align-self: start; text-align: right; }
    .stats-trophies .name-cell   { grid-column: 2; grid-row: 1; }
    .stats-trophies .gold-cell   { grid-column: 3; grid-row: 1; text-align: right; white-space: nowrap; }
    .stats-trophies .silver-cell { grid-column: 3; grid-row: 2; text-align: right; white-space: nowrap; }
    .stats-trophies .bronze-cell { grid-column: 3; grid-row: 3; text-align: right; white-space: nowrap; }
    .stats-trophies .gold-cell::before   { content: '🥇: '; }
    .stats-trophies .silver-cell::before { content: '🥈: '; }
    .stats-trophies .bronze-cell::before { content: '🥉: '; }

    /* ── Høyest snittpoeng ──
       col 1: rank (spans 2 rows)
       col 2: band name (row 1)
       col 3: Snittpoeng / Fremføringer (rows 1–2)
    */
    .stats-scores .rank-cell       { grid-column: 1; grid-row: 1 / 3; align-self: start; text-align: right; }
    .stats-scores .name-cell       { grid-column: 2; grid-row: 1; }
    .stats-scores .avg-cell        { grid-column: 3; grid-row: 1; text-align: right; white-space: nowrap; }
    .stats-scores .score-count-cell { grid-column: 3; grid-row: 2; text-align: right; white-space: nowrap; }
    .stats-scores .avg-cell::before         { content: 'Snittpoeng: '; color: var(--color-text-secondary); font-size: 0.8rem; }
    .stats-scores .score-count-cell::before { content: 'Fremføringer: '; color: var(--color-text-secondary); font-size: 0.8rem; }

    /* ── Høyest snittpoeng (stykke) ──
       col 1: rank (spans 2 rows)
       col 2: title / composer
       col 3: Snittpoeng: avg (row 1) / Fremføringer: count (row 2)
    */
    .stats-piece-scores .rank-cell     { grid-column: 1; grid-row: 1 / 3; align-self: start; text-align: right; }
    .stats-piece-scores .name-cell     { grid-column: 2; grid-row: 1; }
    .stats-piece-scores .composer-cell { grid-column: 2; grid-row: 2; font-size: 0.85rem; }
    .stats-piece-scores .ps-avg-cell   { grid-column: 3; grid-row: 1; text-align: right; white-space: nowrap; }
    .stats-piece-scores .ps-count-cell { grid-column: 3; grid-row: 2; text-align: right; white-space: nowrap; }
    .stats-piece-scores .ps-avg-cell::before   { content: 'Snittpoeng: '; color: var(--color-text-secondary); font-size: 0.8rem; }
    .stats-piece-scores .ps-count-cell::before { content: 'Fremføringer: '; color: var(--color-text-secondary); font-size: 0.8rem; }
  }
</style>
