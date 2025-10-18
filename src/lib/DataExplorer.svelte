<script lang="ts">

  import type { BandDataset, BandEntry, BandType, StreamingLink, EliteTestPiecesData, PromotionRules, PromotionStatus } from './types';
  import { slugify } from './slugify';
  import { onMount } from 'svelte';

  interface Props {
    dataset?: BandDataset | null;
    bandType?: BandType;
    streamingResolver?: (entry: BandEntry, band: string, piece: string) => StreamingLink | null;
    eliteTestPieces?: EliteTestPiecesData | null;
  }

  let { dataset = null, bandType = 'wind', streamingResolver = undefined, eliteTestPieces = null }: Props = $props();

  interface PrizeEntry {
    prize_type: 'soloist' | 'group';
    instrument: string;
    orchestra: string;
    korpsnr: number | null;
  }

  interface PrizeYearDivision {
    year: number;
    division: string;
    entries: PrizeEntry[];
  }

  interface PrizeDataset {
    prizes: PrizeYearDivision[];
    metadata: {
      years: number[];
      min_year: number;
      max_year: number;
      total_prizes: number;
      divisions: string[];
      generated_at: string;
    };
  }

  let prizeData = $state<PrizeDataset | null>(null);
  let prizeDataLoading = $state(false);
  let promotionRules = $state<PromotionRules | null>(null);

  type TableRow = {
    band: string;
    entry: BandEntry;
  };

  const pointsFormatter = new Intl.NumberFormat('nb-NO', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1
  });

  // Local storage keys for persisting selections per band type
  const STORAGE_KEY_YEAR = (type: BandType) => `band-positions-${type}-year`;
  const STORAGE_KEY_DIVISION = (type: BandType) => `band-positions-${type}-division`;

  // Initialize from local storage if available
  function getStoredYear(type: BandType): number | null {
    if (typeof localStorage === 'undefined') return null;
    try {
      const stored = localStorage.getItem(STORAGE_KEY_YEAR(type));
      if (stored) {
        const parsed = Number(stored);
        return Number.isNaN(parsed) ? null : parsed;
      }
    } catch (e) {
      console.warn('Failed to read year from localStorage', e);
    }
    return null;
  }

  function getStoredDivision(type: BandType): string | null {
    if (typeof localStorage === 'undefined') return null;
    try {
      return localStorage.getItem(STORAGE_KEY_DIVISION(type));
    } catch (e) {
      console.warn('Failed to read division from localStorage', e);
    }
    return null;
  }

  function setStoredYear(type: BandType, year: number | null): void {
    if (typeof localStorage === 'undefined') return;
    try {
      if (year === null) {
        localStorage.removeItem(STORAGE_KEY_YEAR(type));
      } else {
        localStorage.setItem(STORAGE_KEY_YEAR(type), String(year));
      }
    } catch (e) {
      console.warn('Failed to write year to localStorage', e);
    }
  }

  function setStoredDivision(type: BandType, division: string | null): void {
    if (typeof localStorage === 'undefined') return;
    try {
      if (division === null) {
        localStorage.removeItem(STORAGE_KEY_DIVISION(type));
      } else {
        localStorage.setItem(STORAGE_KEY_DIVISION(type), division);
      }
    } catch (e) {
      console.warn('Failed to write division to localStorage', e);
    }
  }

  let selectedYear: number | null = $state(getStoredYear(bandType));
  let selectedDivision: string | null = $state(getStoredDivision(bandType));

  // Derived values that recalculate when dataset changes
  let yearDivisionMap = $derived(dataset
    ? buildYearDivisionMap(dataset)
    : new Map<number, Map<string, TableRow[]>>());
  let availableYears = $derived(dataset?.metadata?.years ?? []);
  let generatedAt = $derived(dataset?.metadata?.generated_at ?? null);
  
  // Derived divisions for the selected year
  let divisionsForYear = $derived((() => {
    if (!dataset || !dataset.metadata || !Array.isArray(dataset.metadata.divisions) || selectedYear == null || !yearDivisionMap.has(selectedYear)) {
      return [];
    }
    const divisionsMap = yearDivisionMap.get(selectedYear) ?? new Map<string, TableRow[]>();
    const ordered = dataset.metadata.divisions.filter((division) => divisionsMap.has(division));
    const remaining = Array.from<string>(divisionsMap.keys())
      .filter((division) => !ordered.includes(division))
      .sort();
    return [...ordered, ...remaining];
  })());
  
  // Direct derived table rows for selected year/division
  let tableRows = $derived((() => {
    if (selectedYear != null && selectedDivision && yearDivisionMap.has(selectedYear)) {
      const yearMap = yearDivisionMap.get(selectedYear!);
      const rows = (selectedDivision && yearMap?.get(selectedDivision)) ?? [];
      return sortRows(rows);
    }
    return [];
  })());
  
  let divisionSize = $derived((() => {
    if (tableRows.length > 0) {
      const first = tableRows[0]?.entry;
      const computedDivisionSize = first?.division_size ?? tableRows.length;
      return computedDivisionSize && computedDivisionSize > 0 ? computedDivisionSize : null;
    }
    return null;
  })());
  
  let fieldSize = $derived((() => {
    if (tableRows.length > 0) {
      const first = tableRows[0]?.entry;
      const computedFieldSize = first?.field_size ?? null;
      return computedFieldSize && computedFieldSize > 0 ? computedFieldSize : null;
    }
    return null;
  })());

  function buildYearDivisionMap(source: BandDataset): Map<number, Map<string, TableRow[]>> {
    const map = new Map<number, Map<string, TableRow[]>>();
    
    if (!source?.bands || !Array.isArray(source.bands)) {
      return map;
    }
    
    for (const band of source.bands) {
      if (!band || !band.entries || !Array.isArray(band.entries)) {
        continue;
      }
      
      for (const entry of band.entries) {
        if (!entry || typeof entry.year !== 'number' || !entry.division) {
          continue;
        }
        
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

  function resolveStreamingLink(entry: BandEntry, band: string, piece: string): StreamingLink | null {
    if (typeof streamingResolver !== 'function') return null;
    try {
      return streamingResolver(entry, band, piece) ?? null;
    } catch (err) {
      console.error('Kunne ikke hente streaming-lenke', err);
      return null;
    }
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

  function testPieceForYear(year: string | number): { composer: string; piece: string } | null {
    const y = String(year);
    const tp = eliteTestPieces?.test_pieces?.[y];
    return tp ? { composer: tp.composer, piece: tp.piece } : null;
  }

  function isEliteDivision(division: string | undefined | null): boolean {
    return (division || '').toLowerCase() === 'elite';
  }

  function determinePromotionStatus(
    rules: PromotionRules | null,
    bandType: BandType,
    year: number,
    division: string,
    rank: number | null
  ): PromotionStatus {
    if (!rules || rank == null) return null;

    const byType = rules[bandType];
    if (!byType) return null;

    // Exact year match first
    let byYear = byType[String(year)];

    // Brass fallback: if no exact year but year is 2016 or later, use 2016 rules
    if (!byYear && bandType === 'brass' && year >= 2016) {
      byYear = byType['2016'];
    }

    if (!byYear) return null;

    const rule = byYear[division];
    if (!rule) return null;

    if (rule.promote && rule.promote.includes(rank)) return 'promote';
    if (rule.demote && rule.demote.includes(rank)) return 'demote';
    return 'safe';
  }

  function getTrophy(rank: number | null): string {
    if (rank === 1) return '🥇 ';
    if (rank === 2) return '🥈 ';
    if (rank === 3) return '🥉 ';
    return '';
  }

  function handleYearChange(event: Event): void {
    const value = Number((event.target as HTMLSelectElement).value);
    selectedYear = Number.isNaN(value) ? null : value;
  }

  function handleDivisionChange(event: Event): void {
    selectedDivision = (event.target as HTMLSelectElement).value || null;
  }

  // Effect to sync selectedYear to localStorage whenever it changes
  $effect(() => {
    setStoredYear(bandType, selectedYear);
  });

  // Effect to sync selectedDivision to localStorage whenever it changes
  $effect(() => {
    setStoredDivision(bandType, selectedDivision);
  });

  // Effect to clear selections when bandType changes
  $effect(() => {
    // This effect runs when bandType changes
    // Reset selections and clear storage for the new band type
    const storedYear = getStoredYear(bandType);
    const storedDivision = getStoredDivision(bandType);
    
    selectedYear = storedYear;
    selectedDivision = storedDivision;
  });

  // Single effect to handle initial selections when dataset changes
  $effect(() => {
    if (dataset && availableYears && Array.isArray(availableYears) && availableYears.length > 0) {
      // Set initial year if not set or invalid
      const newSelectedYear = ensureYearSelection(availableYears);
      if (selectedYear !== newSelectedYear) {
        selectedYear = newSelectedYear;
      }
    } else {
      // Clear selections when no dataset
      selectedYear = null;
      selectedDivision = null;
    }
  });
  
  // Effect to handle division selection when year changes or divisions change
  $effect(() => {
    if (selectedYear != null && divisionsForYear && Array.isArray(divisionsForYear) && divisionsForYear.length > 0) {
      const newSelectedDivision = ensureDivisionSelection(divisionsForYear);
      if (selectedDivision !== newSelectedDivision) {
        selectedDivision = newSelectedDivision;
      }
    } else if (selectedYear != null) {
      // Clear division if year is set but no divisions available
      selectedDivision = null;
    }
  });

  let formattedGeneratedAt = $derived(formatGeneratedTimestamp(generatedAt));

  // Fetch prize data when bandType changes
  async function loadPrizeData(type: BandType): Promise<void> {
    prizeDataLoading = true;
    try {
      const filename = type === 'wind' ? 'wind_prizes.json' : 'brass_prizes.json';
      const response = await fetch(`data/${filename}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch prize data: ${response.statusText}`);
      }
      prizeData = await response.json();
    } catch (err) {
      console.error('Error loading prize data:', err);
      prizeData = null;
    } finally {
      prizeDataLoading = false;
    }
  }

  // Load prize data and promotion rules on mount
  onMount(() => {
    loadPrizeData(bandType);
    
    // Load promotion rules
    fetch('data/promotion_rules.json')
      .then((res) => {
        if (res.ok) {
          return res.json();
        }
        console.warn('promotion_rules.json not found or failed to load');
        return null;
      })
      .then((data) => {
        if (data) {
          promotionRules = data;
        }
      })
      .catch((err) => {
        console.warn('Failed to load promotion rules', err);
      });
  });

  $effect(() => {
    loadPrizeData(bandType);
  });

  // Find prizes for the selected year and division
  let prizesForSelection = $derived((() => {
    if (!prizeData || selectedYear == null || !selectedDivision) {
      return null;
    }
    const yearDivisionEntry = prizeData.prizes.find(
      (p) => p.year === selectedYear && p.division === selectedDivision
    );
    if (!yearDivisionEntry || !yearDivisionEntry.entries) {
      return null;
    }

    const soloistPrize = yearDivisionEntry.entries.find((e) => e.prize_type === 'soloist');
    const groupPrize = yearDivisionEntry.entries.find((e) => e.prize_type === 'group');

    return {
      soloist: soloistPrize || null,
      group: groupPrize || null
    };
  })());
</script>

<section class="data-view">
  <div class="data-lead">
    <h2>Resultatlister per divisjon</h2>
  </div>


  {#if !dataset}
    <p class="data-status">Kunne ikke finne datasettet.</p>
  {:else if !availableYears || !availableYears.length}
    <p class="data-status">Ingen årsdata tilgjengelig.</p>
  {:else}
    <div class="data-controls">
      <label class="control">
        <span>År</span>
        <select onchange={handleYearChange}>
          {#each availableYears || [] as year}
            <option value={year} selected={selectedYear === year}>{year}</option>
          {/each}
        </select>
      </label>
      <label class="control">
        <span>Divisjon</span>
        <select onchange={handleDivisionChange}>
          {#if !divisionsForYear || divisionsForYear.length === 0}
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

    {#if prizesForSelection && (prizesForSelection.soloist || prizesForSelection.group)}
      <div class="prize-section" role="complementary" aria-label="Priser">
        <h3>🏆 Priser</h3>
        <div class="prize-cards">
          {#if prizesForSelection.soloist}
            <div class="prize-card prize-card--soloist">
              <div class="prize-card__header">
                <span class="prize-card__type">Solistpris</span>
                <span class="prize-card__instrument">{prizesForSelection.soloist.instrument}</span>
              </div>
              <div class="prize-card__winner">
                <a
                  href={`?type=${bandType}&view=bands&band=${encodeURIComponent(slugify(prizesForSelection.soloist.orchestra))}`}
                  class="prize-winner-link"
                >
                  {prizesForSelection.soloist.orchestra}
                </a>
              </div>
            </div>
          {/if}
          {#if prizesForSelection.group}
            <div class="prize-card prize-card--group">
              <div class="prize-card__header">
                <span class="prize-card__type">Gruppepris</span>
                <span class="prize-card__instrument">{prizesForSelection.group.instrument}</span>
              </div>
              <div class="prize-card__winner">
                <a
                  href={`?type=${bandType}&view=bands&band=${encodeURIComponent(slugify(prizesForSelection.group.orchestra))}`}
                  class="prize-winner-link"
                >
                  {prizesForSelection.group.orchestra}
                </a>
              </div>
            </div>
          {/if}
        </div>
      </div>
    {/if}

    {#if !tableRows || tableRows.length === 0}
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
              <th scope="col" class="streaming-column">Opptak</th>
            </tr>
          </thead>
          <tbody>
            {#each tableRows as { band, entry }}
              {@const promotionStatus = determinePromotionStatus(promotionRules, bandType, selectedYear ?? 0, entry.division ?? '', entry.rank)}
              <tr
                class:row-promote={promotionStatus === 'promote'}
                class:row-demote={promotionStatus === 'demote'}
              >
                <td data-label="Plass" class="rank-col">{getTrophy(entry.rank)}{formatRank(entry.rank)}</td>
                <td data-label="Korps">
                  <a
                    href={`?type=${bandType}&view=bands&band=${encodeURIComponent(slugify(band))}`}
                    class="entity-link"
                  >
                    {band}
                  </a>
                </td>
                <td data-label="Dirigent">
                  {#if entry.conductor && entry.conductor.trim().length > 0}
                    <a
                      href={`?type=${bandType}&view=conductors&conductor=${encodeURIComponent(slugify(entry.conductor))}`}
                      class="entity-link"
                    >
                      {entry.conductor.trim()}
                    </a>
                  {:else}
                    <span>Ukjent</span>
                  {/if}
                </td>
                <td data-label="Poeng">{formatPoints(entry.points, entry.max_points)}</td>
                <td data-label="Program" class="program-cell">
                  {#if true}
                    {@const testPiece = bandType === 'brass' && isEliteDivision(entry.division) ? testPieceForYear(entry.year) : null}
                    {@const ownChoicePieces = formatPieces(entry.pieces)}
                    {@const allPieces = testPiece ? [{name: testPiece.piece, isTestPiece: true}, ...ownChoicePieces.map(p => ({name: p, isTestPiece: false}))] : ownChoicePieces.map(p => ({name: p, isTestPiece: false}))}
                    {#if allPieces.length === 0}
                      <span>–</span>
                    {:else}
                      <div class="program-list">
                        {#each allPieces as pieceItem}
                          {@const piece = pieceItem.name}
                          <div class="program-piece">
                            {#if pieceItem.isTestPiece}
                              <span class="test-piece-label" title="Pliktstykke (fredag)">P:</span>
                            {:else if bandType === 'brass' && isEliteDivision(entry.division)}
                              <span class="own-choice-label" title="Selvvalgt (lørdag)">S:</span>
                            {/if}
                            <a
                              href={`?type=${bandType}&view=pieces&piece=${encodeURIComponent(slugify(piece))}`}
                              class="program-link"
                              class:test-piece-link={pieceItem.isTestPiece}
                            >
                              {piece}
                            </a>
                          </div>
                        {/each}
                      </div>
                    {/if}
                  {/if}
                </td>
                <td data-label="Opptak" class="streaming-cell">
                  {#if true}
                    {@const testPiece = bandType === 'brass' && isEliteDivision(entry.division) ? testPieceForYear(entry.year) : null}
                    {@const ownChoicePieces = formatPieces(entry.pieces)}
                    {@const allPieces = testPiece ? [{name: testPiece.piece, isTestPiece: true}, ...ownChoicePieces.map(p => ({name: p, isTestPiece: false}))] : ownChoicePieces.map(p => ({name: p, isTestPiece: false}))}
                    {#if allPieces.length === 0}
                      <span class="streaming-missing" aria-hidden="true">–</span>
                    {:else}
                      <div class="streaming-list">
                        {#each allPieces as pieceItem}
                          {@const piece = pieceItem.name}
                          {@const streaming = resolveStreamingLink(entry, band, piece)}
                          <div class="streaming-piece-row">
                            {#if hasStreamingLinks(streaming)}
                              <span class="streaming-links">
                                {#if streaming?.spotify}
                                  <a
                                    href={streaming.spotify}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    class="streaming-link spotify"
                                    title={buildStreamingTitle(piece, streaming, 'spotify')}
                                  >
                                    <span class="sr-only">Hør {piece} på Spotify</span>
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
                                      title={buildStreamingTitle(piece, streaming, 'apple')}
                                    >
                                      <span class="sr-only">Hør {piece} på Apple Music</span>
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
                            {:else}
                              <span class="streaming-missing" aria-hidden="true">–</span>
                            {/if}
                          </div>
                        {/each}
                      </div>
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
  }

  .data-lead h2 {
    margin: 0;
    color: var(--color-accent);
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

  .prize-section {
    padding: 1.5rem;
    background: var(--color-surface-card);
    border-radius: 1rem;
    border: 1px solid var(--color-border);
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.15);
  }

  .prize-section h3 {
    margin: 0 0 1rem;
    font-size: 1.1rem;
    color: var(--color-accent);
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .prize-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
  }

  .prize-card {
    padding: 1rem 1.25rem;
    background: var(--color-mode-toggle-bg);
    border-radius: 0.75rem;
    border: 2px solid transparent;
    transition: border-color 0.2s ease;
  }

  .prize-card--soloist {
    border-color: rgba(147, 51, 234, 0.3);
  }

  .prize-card--group {
    border-color: rgba(16, 185, 129, 0.3);
  }

  .prize-card__header {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    margin-bottom: 0.75rem;
  }

  .prize-card__type {
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: var(--color-text-secondary);
  }

  .prize-card__instrument {
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--color-text-primary);
  }

  .prize-card__winner {
    font-size: 1.05rem;
  }

  .prize-winner-link {
    color: var(--color-accent);
    text-decoration: none;
    font-weight: 600;
    transition: text-decoration 0.15s ease;
  }

  .prize-winner-link:hover,
  .prize-winner-link:focus-visible {
    text-decoration: underline;
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

  /* Promotion/demotion row backgrounds */
  tr.row-promote {
    background-color: rgba(16, 185, 129, 0.08);
  }

  tr.row-demote {
    background-color: rgba(239, 68, 68, 0.08);
  }

  tbody td {
    border-top: 1px solid var(--color-border);
    color: var(--color-text-primary);
    font-size: 0.95rem;
  }

  .rank-col {
    white-space: nowrap;
  }

  .program-cell {
    white-space: normal;
  }

  .program-list {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }

  .program-piece {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
  }

  .streaming-list {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }

  .streaming-piece-row {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    min-height: 1.5rem;
  }

  .streaming-links {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
  }

  .streaming-link {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.5rem;
    height: 1.5rem;
    border-radius: 999px;
    color: var(--color-text-secondary);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
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
    width: 1.15rem;
    height: 1.15rem;
    fill: currentColor;
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
    font-size: 0.75rem;
    font-weight: 700;
    border-radius: 0.25rem;
    padding: 0.1rem 0.35rem;
    margin-right: 0.4rem;
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

  .program-link,
  .entity-link {
    color: var(--color-accent);
    text-decoration: none;
  }

  .program-link:hover,
  .program-link:focus-visible,
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

    /* Reorder cells: Korps before Plass for better mobile layout */
    td[data-label="Korps"] {
      order: 1;
    }

    td[data-label="Plass"] {
      order: 2;
    }

    td[data-label="Dirigent"] {
      order: 3;
    }

    td[data-label="Poeng"] {
      order: 4;
    }

    td[data-label="Program"] {
      order: 5;
    }

    td[data-label="Opptak"] {
      order: 6;
    }

    /* Adjust program piece layout for mobile */
    .program-piece {
      flex-wrap: wrap;
      gap: 0.25rem;
    }

    /* Ensure piece names can wrap */
    .program-link {
      word-break: break-word;
      overflow-wrap: break-word;
      hyphens: auto;
    }
  }
</style>
