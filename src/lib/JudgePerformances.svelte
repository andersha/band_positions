<script lang="ts">
  import type { BandType } from './types';
  import { slugify } from './slugify';

  interface JudgeEntry {
    year: number;
    division: string;
    panel: string | null;
    judges: string[];
  }

  interface Props {
    judgeSlug: string;
    judgesData: { wind: JudgeEntry[]; brass: JudgeEntry[] } | null;
    bandType: BandType;
  }

  let { judgeSlug, judgesData, bandType }: Props = $props();

  let judgeName = $derived.by(() => {
    if (!judgesData) return judgeSlug;
    for (const entry of judgesData[bandType]) {
      const match = entry.judges.find(n => slugify(n) === judgeSlug);
      if (match) return match;
    }
    return judgeSlug;
  });

  let judgeEntries = $derived.by(() => {
    if (!judgesData) return [];
    return judgesData[bandType]
      .filter(entry => entry.judges.some(n => slugify(n) === judgeSlug))
      .sort((a, b) => b.year - a.year || a.division.localeCompare(b.division, 'nb'));
  });

  let hasPanel = $derived(judgeEntries.some(e => e.panel !== null));

  function formatPanel(panel: string | null): string {
    if (panel === 'plikt') return 'Pliktstykke';
    if (panel === 'selvvalgt') return 'Selvvalgt';
    return panel ?? '—';
  }
</script>

<div class="judge-performances">
  <header class="judge-header">
    <h2>{judgeName}</h2>
  </header>

  {#if judgesData === null}
    <p class="loading">Laster...</p>
  {:else if judgeEntries.length === 0}
    <p class="empty">Ingen dommertjeneste funnet.</p>
  {:else}
    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th scope="col">År</th>
            <th scope="col">Divisjon</th>
            {#if hasPanel}
              <th scope="col">Panel</th>
            {/if}
          </tr>
        </thead>
        <tbody>
          {#each judgeEntries as entry}
            <tr>
              <td data-label="År">{entry.year}</td>
              <td data-label="Divisjon" class="division-cell">
                <a
                  href={`?type=${bandType}&view=data&year=${entry.year}&division=${encodeURIComponent(entry.division)}`}
                  class="entity-link"
                >
                  {entry.division}
                </a>
              </td>
              {#if hasPanel}
                <td data-label="Panel">{formatPanel(entry.panel)}</td>
              {/if}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    <p class="summary">{judgeEntries.length} {judgeEntries.length === 1 ? 'oppdrag' : 'oppdrag'}</p>
  {/if}
</div>

<style>
  .judge-performances {
    padding: 1rem;
    max-width: 600px;
    margin: 0 auto;
  }

  .judge-header {
    margin-bottom: 1.5rem;
  }

  .judge-header h2 {
    margin: 0;
    color: var(--color-accent);
    font-size: 1.4rem;
  }

  .table-wrapper {
    overflow-x: auto;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
  }

  thead th {
    text-align: left;
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid var(--color-border, #444);
    color: var(--color-text-secondary, #999);
    font-weight: 600;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  tbody tr:hover {
    background: var(--color-surface-hover, rgba(255,255,255,0.05));
  }

  td {
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid var(--color-border-subtle, rgba(255,255,255,0.07));
    vertical-align: middle;
  }

  .division-cell a {
    color: var(--color-link, var(--color-accent));
    text-decoration: none;
  }

  .division-cell a:hover {
    text-decoration: underline;
  }

  .summary {
    margin-top: 1rem;
    font-size: 0.85rem;
    color: var(--color-text-secondary, #999);
  }

  .loading,
  .empty {
    color: var(--color-text-secondary, #999);
    font-style: italic;
  }
</style>
