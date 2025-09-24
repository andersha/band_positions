<script lang="ts">

  import type { BandDataset, BandEntry } from './types';
  import { slugify } from './slugify';

  interface Props {
    dataset?: BandDataset | null;
  }

  let { dataset = null }: Props = $props();

  type TableRow = {
    band: string;
    entry: BandEntry;
  };

  const pointsFormatter = new Intl.NumberFormat('nb-NO', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1
  });

  let availableYears: number[] = $state([]);
  let selectedYear: number | null = $state(null);
  let divisionsForYear: string[] = $state([]);
  let selectedDivision: string | null = $state(null);
  let tableRows: TableRow[] = $state([]);
  let divisionSize: number | null = $state(null);
  let fieldSize: number | null = $state(null);
  let generatedAt: string | null = $state(null);

  let yearDivisionMap: Map<number, Map<string, TableRow[]>> = $state(new Map());

  function buildYearDivisionMap(source: BandDataset): Map<number, Map<string, TableRow[]>> {
    const map = new Map<number, Map<string, TableRow[]>>();

    for (const band of source.bands) {
      for (const entry of band.entries) {
        let yearBucket = map.get(entry.year);
        if (!yearBucket) {
          yearBucket = new Map();
          map.set(entry.year, yearBucket);
        }

        const divisionKey = entry.division;
        let divisionRows = yearBucket.get(divisionKey);
        if (!divisionRows) {
          divisionRows = [];
          yearBucket.set(divisionKey, divisionRows);
        }

        divisionRows.push({ band: band.name, entry });
      }
    }

    return map;
  }

  function ensureYearSelection(years: number[]): number | null {
    if (!years.length) return null;
    if (selectedYear && years.includes(selectedYear)) return selectedYear;
    return years[years.length - 1] ?? null;
  }

  function ensureDivisionSelection(divisions: string[]): string | null {
    if (!divisions.length) return null;
    if (selectedDivision && divisions.includes(selectedDivision)) return selectedDivision;
    return divisions[0] ?? null;
  }

  function sortRows(rows: TableRow[]): TableRow[] {
    return [...rows].sort((a, b) => {
      const rankA = a.entry.rank ?? Number.POSITIVE_INFINITY;
      const rankB = b.entry.rank ?? Number.POSITIVE_INFINITY;
      if (rankA !== rankB) return rankA - rankB;
      const absA = a.entry.absolute_position ?? Number.POSITIVE_INFINITY;
      const absB = b.entry.absolute_position ?? Number.POSITIVE_INFINITY;
      if (absA !== absB) return absA - absB;
      return a.band.localeCompare(b.band);
    });
  }

  function formatRank(rank: number | null): string {
    return rank != null ? `${rank}` : '–';
  }

  function formatPoints(points: number | null, max: number | null): string {
    if (points == null && max == null) return '–';
    const base = points == null ? '–' : pointsFormatter.format(points);
    if (max == null) return base;
    return base;
  }

  function formatPieces(pieces: string[]): string[] {
    return pieces.map((piece) => piece.trim()).filter(Boolean);
  }

  function formatGeneratedTimestamp(value: string | null): string | null {
    if (!value) return null;
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    return new Intl.DateTimeFormat('nb-NO', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  }

  function handleYearChange(event: Event): void {
    const value = Number((event.target as HTMLSelectElement).value);
    selectedYear = Number.isNaN(value) ? null : value;
  }

  function handleDivisionChange(event: Event): void {
    selectedDivision = (event.target as HTMLSelectElement).value || null;
  }

  $effect(() => {
    if (dataset) {
      yearDivisionMap = buildYearDivisionMap(dataset);
      availableYears = dataset.metadata.years;
      generatedAt = dataset.metadata.generated_at ?? null;
      selectedYear = ensureYearSelection(availableYears);
    } else {
      yearDivisionMap = new Map();
      availableYears = [];
      generatedAt = null;
      selectedYear = null;
    }
  });

  $effect(() => {
    if (dataset && selectedYear != null) {
      const divisionsMap = yearDivisionMap.get(selectedYear) ?? new Map<string, TableRow[]>();
      const ordered = dataset.metadata.divisions.filter((division) => divisionsMap.has(division));
      const remaining = Array.from(divisionsMap.keys()).filter((division) => !ordered.includes(division)).sort();
      divisionsForYear = [...ordered, ...remaining];
      selectedDivision = ensureDivisionSelection(divisionsForYear);
    } else {
      divisionsForYear = [];
      selectedDivision = null;
    }
  });

  $effect(() => {
    if (selectedYear != null && selectedDivision && yearDivisionMap.has(selectedYear)) {
      const rows = yearDivisionMap.get(selectedYear)?.get(selectedDivision) ?? [];
      tableRows = sortRows(rows);
      const first = tableRows[0]?.entry;
      const computedDivisionSize = first?.division_size ?? tableRows.length;
      divisionSize = computedDivisionSize && computedDivisionSize > 0 ? computedDivisionSize : null;
      const computedFieldSize = first?.field_size ?? null;
      fieldSize = computedFieldSize && computedFieldSize > 0 ? computedFieldSize : null;
    } else {
      tableRows = [];
      divisionSize = null;
      fieldSize = null;
    }
  });

  let formattedGeneratedAt = $derived(formatGeneratedTimestamp(generatedAt));
</script>

<section class="data-view">
  <div class="data-lead">
    <h2>Resultatlister per divisjon</h2>
    {#if formattedGeneratedAt}
      <p>Data oppdatert {formattedGeneratedAt}</p>
    {/if}
  </div>

  {#if !dataset}
    <p class="data-status">Kunne ikke finne datasettet.</p>
  {:else if !availableYears.length}
    <p class="data-status">Ingen årsdata tilgjengelig.</p>
  {:else}
    <div class="data-controls">
      <label class="control">
        <span>År</span>
        <select onchange={handleYearChange}>
          {#each availableYears as year}
            <option value={year} selected={selectedYear === year}>{year}</option>
          {/each}
        </select>
      </label>
      <label class="control">
        <span>Divisjon</span>
        <select onchange={handleDivisionChange}>
          {#if divisionsForYear.length === 0}
            <option value="" selected>Ingen divisjoner</option>
          {:else}
            {#each divisionsForYear as division}
              <option value={division} selected={selectedDivision === division}>{division}</option>
            {/each}
          {/if}
        </select>
      </label>
      {#if divisionSize}
        <div class="control control--summary" aria-live="polite">
          <span>{divisionSize} korps</span>
          {#if fieldSize}
            <span>Totalt felt: {fieldSize}</span>
          {/if}
        </div>
      {/if}
    </div>

    {#if tableRows.length === 0}
      <p class="data-status">Ingen resultater for valgt kombinasjon.</p>
    {:else}
      <div class="table-wrapper" role="region" aria-live="polite">
        <table>
          <thead>
            <tr>
              <th scope="col">Plass</th>
              <th scope="col">Korps</th>
              <th scope="col">Dirigent</th>
              <th scope="col">Poeng</th>
              <th scope="col">Program</th>
            </tr>
          </thead>
          <tbody>
            {#each tableRows as { band, entry }}
              <tr>
                <td data-label="Plass">{formatRank(entry.rank)}</td>
                <td data-label="Korps">{band}</td>
                <td data-label="Dirigent">{entry.conductor ?? 'Ukjent'}</td>
                <td data-label="Poeng">{formatPoints(entry.points, entry.max_points)}</td>
                <td data-label="Program" class="program-cell">
                  {#if true}
                    {@const pieces = formatPieces(entry.pieces)}
                    {#if pieces.length === 0}
                      <span>–</span>
                    {:else}
                      {#each pieces as piece, index}
                        <a
                          href={`?view=pieces&piece=${encodeURIComponent(slugify(piece))}`}
                          class="program-link"
                        >
                          {piece}
                        </a>{index < pieces.length - 1 ? ', ' : ''}
                      {/each}
                    {/if}
                  {/if}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  {/if}
</section>

<style>
  .data-view {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    margin-top: 1.5rem;
  }

  .data-lead h2 {
    margin: 0;
    color: var(--color-accent);
  }

  .data-lead p {
    margin: 0.25rem 0 0;
    color: var(--color-text-secondary);
    font-size: 0.9rem;
  }

  .data-status {
    margin: 0.5rem 0;
    color: var(--color-text-secondary);
  }

  .data-controls {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    align-items: flex-end;
  }

  .control {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    font-size: 0.95rem;
    color: var(--color-text-secondary);
  }

  .control span {
    font-weight: 600;
    color: var(--color-text-primary);
  }

  .control select {
    min-width: 10rem;
    padding: 0.45rem 0.75rem;
    border-radius: 0.6rem;
    border: 1px solid var(--color-border);
    background: var(--color-surface-card);
    color: var(--color-text-primary);
  }

  .control--summary {
    gap: 0.2rem;
  }

  .control--summary span {
    font-weight: 500;
    color: var(--color-text-secondary);
  }

  .table-wrapper {
    overflow-x: auto;
    border-radius: 1rem;
    border: 1px solid var(--color-border);
    background: var(--color-surface-card);
    box-shadow: 0 18px 40px rgba(15, 23, 42, 0.25);
  }

  table {
    width: 100%;
    border-collapse: collapse;
    min-width: 600px;
  }

  th,
  td {
    padding: 0.75rem 1rem;
    text-align: left;
  }

  thead {
    background: var(--color-mode-toggle-bg);
  }

  th {
    font-size: 0.85rem;
    letter-spacing: 0.02em;
    text-transform: uppercase;
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

  .program-cell {
    white-space: normal;
  }

  .program-link {
    color: var(--color-accent);
    text-decoration: none;
  }

  .program-link:hover,
  .program-link:focus-visible {
    text-decoration: underline;
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
      padding: 0.75rem 1rem;
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
