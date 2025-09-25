<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import { scaleLinear, scalePoint, line, curveMonotoneX, ticks } from 'd3';
  import type { BandEntry, BandRecord } from './types';

  let { 
    bands = [], 
    years = [], 
    maxFieldSize = 0, 
    yMode = 'relative', 
    showConductorMarkers = true 
  } = $props<{
    bands?: BandRecord[];
    years?: number[];
    maxFieldSize?: number;
    yMode?: 'absolute' | 'relative';
    showConductorMarkers?: boolean;
  }>();

  const margin = { top: 24, right: 48, bottom: 48, left: 72 };
  const width = 880;
  const height = 360;

  const divisionColors: Record<string, string> = {
    Elite: '#38bdf8',
    '1. divisjon': '#f97316',
    '2. divisjon': '#a855f7',
    '3. divisjon': '#facc15',
    '4. divisjon': '#22c55e',
    '5. divisjon': '#ec4899',
    '6. divisjon': '#14b8a6',
    '7. divisjon': '#eab308'
  };

  const LINE_COLORS = ['#38bdf8', '#f97316', '#22c55e', '#a855f7', '#f43f5e', '#facc15', '#14b8a6'];
  const SHAPE_SEQUENCE: MarkerShape[] = ['circle', 'square', 'triangle'];
  const SHAPE_SIZE = 6;
  const CONDUCTOR_LANES = 3;
  const LANE_HEIGHT = 18;
  const LABEL_OFFSET_ABOVE = 18;
  const LABEL_OFFSET_BELOW = 22;
  const MIN_LABEL_TOP = margin.top + 6;
  const MAX_LABEL_BOTTOM = height - margin.bottom - 12;
  const YEAR_AXIS_PADDING = 10;
  const ESTIMATED_CHARACTER_WIDTH = 6;

  type MarkerShape = 'circle' | 'square' | 'triangle';

  type RawAggregatedEntry = BandEntry & {
    band_name?: string;
    aggregate_entries?: BandEntry[];
  };

  type ChartEntry = BandEntry & {
    pieces: string[];
    band_name?: string;
    aggregate_entries?: ChartEntry[];
  };
  interface ConductorChange {
    year: number;
    conductor: string;
    lane: number;
  }
  interface BandSeries {
    band: BandRecord;
    entries: ChartEntry[];
    color: string;
    shape: MarkerShape;
    timeline: (ChartEntry | null)[];
    pathData?: string;
    conductorChanges: ConductorChange[];
  }

  let svgElement = $state<SVGSVGElement | null>(null);
  let labelGeometry = $state({ offsetX: 0, scaleX: 1, offsetY: 0, scaleY: 1 });
  let resizeObserver: ResizeObserver | null = null;
  let observedElement: SVGSVGElement | null = null;


  let hoveredPoint = $state<{ entry: ChartEntry; bandName: string; lineColor: string } | null>(null);
  let tooltipX = $state(0);
  let tooltipY = $state(0);

  const showConductorLabels = () => showConductorMarkers && bands.length === 1;

  function getRelativePercent(entry: ChartEntry): number {
    if (entry.absolute_position == null) {
      return 0;
    }
    const denominator = entry.field_size ?? chartMaxField ?? maxFieldSize ?? 1;
    if (!denominator) {
      return 0;
    }
    return (entry.absolute_position / denominator) * 100;
  }

  function getEntryYValue(entry: ChartEntry): number {
    if (yMode === 'relative') {
      return getRelativePercent(entry);
    }
    return entry.absolute_position ?? 0;
  }

  function normalizeEntry(entry: BandEntry): ChartEntry {
    const rawPieces = (entry as BandEntry & { pieces?: unknown }).pieces ?? entry.pieces;
    const pieces = Array.isArray(rawPieces)
      ? rawPieces.map((piece) => `${piece}`.trim()).filter(Boolean)
      : rawPieces != null && `${rawPieces}`.trim().length
        ? [`${rawPieces}`.trim()]
        : [];

    const normalized: ChartEntry = {
      ...entry,
      pieces
    };

    const rawAggregated = entry as RawAggregatedEntry;
    if (rawAggregated.band_name != null) {
      normalized.band_name = rawAggregated.band_name;
    }

    if (Array.isArray(rawAggregated.aggregate_entries) && rawAggregated.aggregate_entries.length > 0) {
      normalized.aggregate_entries = rawAggregated.aggregate_entries.map((aggregateEntry) =>
        normalizeEntry(aggregateEntry)
      );
    }

    return normalized;
  }

  function normalizeEntries(entries: BandEntry[]): ChartEntry[] {
    return entries.map((entry) => normalizeEntry(entry));
  }

  function computeConductorChanges(entries: ChartEntry[]): ConductorChange[] {
    const markers: ConductorChange[] = [];
    let laneIndex = 0;
    if (entries.length > 0) {
      const first = entries[0];
      if (first.conductor) {
        const lane = laneIndex % CONDUCTOR_LANES;
        markers.push({ year: first.year, conductor: first.conductor, lane });
        laneIndex += 1;
      }
    }

    for (let index = 1; index < entries.length; index += 1) {
      const prev = entries[index - 1];
      const current = entries[index];
      if (prev.conductor && current.conductor && prev.conductor !== current.conductor) {
        const lane = laneIndex % CONDUCTOR_LANES;
        markers.push({ year: current.year, conductor: current.conductor, lane });
        laneIndex += 1;
      }
    }

    return markers;
  }

  function updateLabelGeometry() {
    if (!svgElement) return;
    const svgRect = svgElement.getBoundingClientRect();
    const container = svgElement.parentElement;
    if (!container) return;
    const containerRect = container.getBoundingClientRect();
    if (svgRect.width === 0 || svgRect.height === 0) return;

    const newGeometry = {
      offsetX: svgRect.left - containerRect.left,
      scaleX: svgRect.width / width,
      offsetY: svgRect.top - containerRect.top,
      scaleY: svgRect.height / height
    };
    
    // Only update if values actually changed to prevent infinite loops
    if (
      Math.abs(newGeometry.offsetX - labelGeometry.offsetX) > 0.1 ||
      Math.abs(newGeometry.scaleX - labelGeometry.scaleX) > 0.001 ||
      Math.abs(newGeometry.offsetY - labelGeometry.offsetY) > 0.1 ||
      Math.abs(newGeometry.scaleY - labelGeometry.scaleY) > 0.001
    ) {
      labelGeometry = newGeometry;
    }
  }

  function ensureObserved() {
    if (!resizeObserver || !svgElement) return;
    if (observedElement === svgElement) return;
    if (observedElement) {
      resizeObserver.unobserve(observedElement);
    }
    resizeObserver.observe(svgElement);
    observedElement = svgElement;
  }

  onMount(() => {
    if (typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(() => updateLabelGeometry());
    }
    ensureObserved();
    updateLabelGeometry();
    window.addEventListener('resize', updateLabelGeometry);
  });

  $effect(() => {
    // This runs after each update, similar to afterUpdate
    ensureObserved();
    updateLabelGeometry();
  });

  onDestroy(() => {
    resizeObserver?.disconnect();
    window.removeEventListener('resize', updateLabelGeometry);
  });

  function getConductorLabelProps(change: ConductorChange) {
    const scale = xScale;
    if (!scale) {
      return { anchor: 'middle', dx: 0 } as const;
    }

    const xPosition = scale(change.year) ?? margin.left;
    const estimatedWidth = (change.conductor?.length ?? 0) * ESTIMATED_CHARACTER_WIDTH;
    const halfWidth = estimatedWidth / 2;
    const chartRight = width - margin.right;

    if (xPosition + halfWidth > chartRight) {
      return { anchor: 'end', dx: -8 } as const;
    }
    if (xPosition - halfWidth < margin.left) {
      return { anchor: 'start', dx: 8 } as const;
    }
    return { anchor: 'middle', dx: 0 } as const;
  }

  function splitConductorLabel(name: string | null | undefined): string[] {
    const trimmed = name?.trim();
    if (!trimmed) return [''];
    const parts = trimmed.split(/\s+/);
    if (parts.length <= 1) {
      return [trimmed];
    }
    const lastPart = parts.pop() as string;
    const firstPart = parts.join(' ');
    if (!firstPart) {
      return [lastPart];
    }
    return [firstPart, lastPart];
  }

  function getConductorLabelY(entries: ChartEntry[], change: ConductorChange) {
    const entry = entries.find((item) => item.year === change.year);
    if (!entry) {
      return margin.top - 8 + change.lane * LANE_HEIGHT;
    }

    const dotY = yScale(getEntryYValue(entry));

    const neighbours = entries
      .filter((item) => item.year >= change.year - 1 && item.year <= change.year + 1)
      .map((item) => ({ year: item.year, y: yScale(getEntryYValue(item)) }))
      .sort((a, b) => a.year - b.year);

    const localIndex = neighbours.findIndex((row) => row.year === change.year);

    let placeAbove = true;
    if (localIndex > 0 && localIndex < neighbours.length - 1) {
      const prev = neighbours[localIndex - 1];
      const next = neighbours[localIndex + 1];
      const aboveSpacePrev = Math.abs(dotY - prev.y);
      const aboveSpaceNext = Math.abs(dotY - next.y);
      if (aboveSpacePrev < LABEL_OFFSET_ABOVE + 4 || aboveSpaceNext < LABEL_OFFSET_ABOVE + 4) {
        placeAbove = false;
      }
    }

    const aboveOffset = LABEL_OFFSET_ABOVE + change.lane * (LANE_HEIGHT / 2);
    const candidateAbove = dotY - aboveOffset;
    if (placeAbove && candidateAbove > MIN_LABEL_TOP) {
      return candidateAbove;
    }

    const laneDepth = change.lane / CONDUCTOR_LANES;
    const belowOffset = LABEL_OFFSET_BELOW + change.lane * (LANE_HEIGHT / 2) + laneDepth * 24;
    return Math.min(dotY + belowOffset, MAX_LABEL_BOTTOM);
  }

  function getTrianglePath(cx: number, cy: number, size: number): string {
    return `M ${cx} ${cy - size} L ${cx + size} ${cy + size} L ${cx - size} ${cy + size} Z`;
  }

  function getDivisionOrder(division: string): number {
    if (!division) return Number.POSITIVE_INFINITY;
    const normalized = division.trim().toLowerCase();
    if (normalized === 'elite') {
      return 0;
    }
    const match = normalized.match(/(\d+)/);
    if (match) {
      return parseInt(match[1], 10);
    }
    return Number.POSITIVE_INFINITY;
  }

  function compareDivisions(a: string, b: string): number {
    const orderA = getDivisionOrder(a);
    const orderB = getDivisionOrder(b);
    if (orderA !== orderB) {
      return orderA - orderB;
    }
    return a.localeCompare(b);
  }

  interface NormalizedBand {
    band: BandRecord;
    entries: ChartEntry[];
  }

  let normalizedBands = $derived<NormalizedBand[]>(bands.map((band: BandRecord) => ({
    band,
    entries: normalizeEntries(band.entries)
  })));

  let allEntries = $derived<ChartEntry[]>(
    normalizedBands.reduce<ChartEntry[]>((accumulator, item) => {
      accumulator.push(...item.entries);
      return accumulator;
    }, [])
  );

  let yearsDomain = $derived((() => {
    if (years.length) return years;
    if (!allEntries.length) return [0];
    const yearSet = new Set<number>(allEntries.map((entry) => entry.year));
    return Array.from<number>(yearSet).sort((a, b) => a - b);
  })());

  let xScale = $derived(scalePoint<number>().domain(yearsDomain).range([margin.left, width - margin.right]));

  let chartMaxField = $derived(maxFieldSize || (allEntries.length ? Math.max(...allEntries.map((entry: ChartEntry) => entry.field_size ?? 0)) : 1));

  let yDomain = $derived<[number, number]>(yMode === 'relative' ? [100, 0] : [chartMaxField + 1, 0]);

  let yScale = $derived(scaleLinear().domain(yDomain).range([height - margin.bottom, margin.top]));

  let series = $derived(normalizedBands.map((item, index) => {
    const sortedEntries = [...item.entries].sort((a, b) => a.year - b.year);
    const timeline: (ChartEntry | null)[] = yearsDomain.map((year: number) =>
      sortedEntries.find((entry) => entry.year === year) ?? null
    );
    const pathGenerator = line<ChartEntry | null>()
      .defined((value): value is ChartEntry => value !== null)
      .x((entry) => (entry ? xScale(entry.year) ?? margin.left : margin.left))
      .y((entry) => (entry ? yScale(getEntryYValue(entry)) : yScale(yDomain[1])))
      .curve(curveMonotoneX);

    const pathData = pathGenerator(timeline) ?? undefined;
    const conductorChanges: ConductorChange[] = showConductorLabels()
      ? computeConductorChanges(sortedEntries)
      : [];

    return {
      band: item.band,
      entries: sortedEntries,
      timeline,
      pathData,
      conductorChanges,
      color: LINE_COLORS[index % LINE_COLORS.length],
      shape: SHAPE_SEQUENCE[index % SHAPE_SEQUENCE.length]
    } satisfies BandSeries;
  }));

  let conductorLabels = $derived(
    showConductorLabels() && series.length
      ? series[0].conductorChanges.map((change) => ({
          ...change,
          ...getConductorLabelProps(change),
          y: getConductorLabelY(series[0].entries, change),
          labelLines: splitConductorLabel(change.conductor)
        }))
      : []
  );

  let yTicks = $derived((() => {
    if (yMode === 'relative') {
      return Array.from({ length: 11 }, (_, index) => index * 10);
    } else {
      const tickValues = Array.from(new Set<number>(ticks(1, chartMaxField, 6).map((tick) => Math.round(tick))))
        .filter((tick) => tick >= 1)
        .sort((a, b) => a - b);
      if (!tickValues.includes(1)) {
        return [1, ...tickValues];
      }
      return tickValues;
    }
  })());

  let participatingYears = $derived(new Set(allEntries.map((entry) => entry.year)));

  let labelStep = $derived(yearsDomain.length > 30 ? 5 : yearsDomain.length > 18 ? 3 : 1);

  let yearLabels = $derived(yearsDomain.filter((year: number, index: number) => {
    if (index === 0 || index === yearsDomain.length - 1) return true;
    if (year === 2019) return true;
    return year % labelStep === 0;
  }));

  let yearLabelPositions = $derived(yearLabels.map((year: number) => {
    const baseX = xScale(year) ?? margin.left;
    const x = labelGeometry.offsetX + baseX * labelGeometry.scaleX;
    return {
      year,
      x,
      inactive: !participatingYears.has(year)
    };
  }));

  let yearAxisY = $derived(labelGeometry.offsetY + (height - margin.bottom) * labelGeometry.scaleY + YEAR_AXIS_PADDING);

  let legendDivisions = $derived(Array.from(new Set(allEntries.map((entry: ChartEntry) => entry.division)))
    .filter((division): division is string => typeof division === 'string' && division.length > 0)
    .sort(compareDivisions));

  const showDivisionLegend = () => legendDivisions.length > 0;

  function showTooltip(event: MouseEvent | FocusEvent, entry: ChartEntry, bandName: string, lineColor: string) {
    const target = event.currentTarget as SVGElement;
    const svg = target.ownerSVGElement;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    if (event instanceof MouseEvent) {
      tooltipX = event.clientX - rect.left;
      tooltipY = event.clientY - rect.top;
    } else {
      const elementRect = target.getBoundingClientRect();
      tooltipX = elementRect.left + elementRect.width / 2 - rect.left;
      tooltipY = elementRect.top + elementRect.height / 2 - rect.top;
    }
    hoveredPoint = { entry, bandName, lineColor };
  }

  function hideTooltip() {
    hoveredPoint = null;
  }

  function getAggregatedPlacements(entry: ChartEntry): ChartEntry[] | undefined {
    return entry.aggregate_entries;
  }
</script>

<div class="chart-canvas">
  <svg
    bind:this={svgElement}
    viewBox={`0 0 ${width} ${height}`}
    role="img"
    aria-label="Band placement over tid"
  >
    <defs>
      <linearGradient id="trajectory" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.9" />
        <stop offset="100%" stop-color="#2563eb" stop-opacity="0.35" />
      </linearGradient>
    </defs>

    <g class="grid">
      {#each yTicks as tick}
        <line
          x1={margin.left}
          x2={width - margin.right}
          y1={yScale(tick)}
          y2={yScale(tick)}
          stroke="rgba(148, 163, 184, 0.25)"
          stroke-width="1"
        />
        <text
          x={margin.left - 12}
          y={yScale(tick) + 4}
          text-anchor="end"
          font-size="12"
          fill="var(--color-text-secondary)"
        >
          {yMode === 'relative' ? `${tick}%` : `#${tick}`}
        </text>
      {/each}
    </g>

    {#each series as seriesData}
      {#if seriesData.pathData}
        <path d={seriesData.pathData} fill="none" stroke={seriesData.color} stroke-width="3" stroke-opacity="0.85" />
      {/if}
    {/each}

    {#if showConductorLabels()}
      {#each conductorLabels as change}
        {#if xScale(change.year) !== undefined}
          {#key `${change.year}-${change.conductor}`}
            <g class="conductor-change" aria-hidden="true">
              <line
                x1={xScale(change.year)}
                x2={xScale(change.year)}
                y1={margin.top}
                y2={height - margin.bottom}
                stroke="var(--color-conductor-line)"
                stroke-dasharray="4 8"
                stroke-width="1.5"
              />
              <text
                x={xScale(change.year)}
                y={change.y}
                text-anchor={change.anchor}
                dx={change.dx}
                font-size="11"
                fill="var(--color-text-secondary)"
              >
                {#each change.labelLines as line, index}
                  <tspan x={xScale(change.year)} dy={index === 0 ? 0 : '1.1em'}>
                    {line}
                  </tspan>
                {/each}
              </text>
            </g>
          {/key}
        {/if}
      {/each}
    {/if}

    {#each series as seriesData}
      {#each seriesData.entries as entry (entry.year)}
        {#if xScale(entry.year) !== undefined}
          {@const cx = xScale(entry.year) ?? margin.left}
          {@const cy = yScale(getEntryYValue(entry))}
          {@const hasFieldSize = (entry.field_size ?? 0) > 0}
          {@const relativeLabel = hasFieldSize ? `${getRelativePercent(entry).toFixed(1)}%` : null}
          <g>
            {#if seriesData.shape === 'circle'}
              <circle
                cx={cx}
                cy={cy}
                r={SHAPE_SIZE}
                fill={divisionColors[entry.division] ?? '#f8fafc'}
                stroke={seriesData.color}
                stroke-width="1.5"
                role="button"
                tabindex="0"
                aria-label={`${seriesData.band.name}: ${entry.year} – ${entry.division} plass ${entry.rank} (absolutt #${entry.absolute_position}${relativeLabel ? ` · relativ ${relativeLabel}` : ''})${entry.conductor ? ` – Dirigent: ${entry.conductor}` : ''}`}
                onmouseenter={(event) => showTooltip(event, entry, seriesData.band.name, seriesData.color)}
                onmouseleave={hideTooltip}
                onfocus={(event) => showTooltip(event, entry, seriesData.band.name, seriesData.color)}
                onblur={hideTooltip}
              />
            {:else if seriesData.shape === 'square'}
              <rect
                x={cx - SHAPE_SIZE}
                y={cy - SHAPE_SIZE}
                width={SHAPE_SIZE * 2}
                height={SHAPE_SIZE * 2}
                rx="2"
                fill={divisionColors[entry.division] ?? '#f8fafc'}
                stroke={seriesData.color}
                stroke-width="1.5"
                role="button"
                tabindex="0"
                aria-label={`${seriesData.band.name}: ${entry.year} – ${entry.division} plass ${entry.rank} (absolutt #${entry.absolute_position}${relativeLabel ? ` · relativ ${relativeLabel}` : ''})${entry.conductor ? ` – Dirigent: ${entry.conductor}` : ''}`}
                onmouseenter={(event) => showTooltip(event, entry, seriesData.band.name, seriesData.color)}
                onmouseleave={hideTooltip}
                onfocus={(event) => showTooltip(event, entry, seriesData.band.name, seriesData.color)}
                onblur={hideTooltip}
              />
            {:else}
              <path
                d={getTrianglePath(cx, cy, SHAPE_SIZE)}
                fill={divisionColors[entry.division] ?? '#f8fafc'}
                stroke={seriesData.color}
                stroke-width="1.5"
                role="button"
                tabindex="0"
                aria-label={`${seriesData.band.name}: ${entry.year} – ${entry.division} plass ${entry.rank} (absolutt #${entry.absolute_position}${relativeLabel ? ` · relativ ${relativeLabel}` : ''})${entry.conductor ? ` – Dirigent: ${entry.conductor}` : ''}`}
                onmouseenter={(event) => showTooltip(event, entry, seriesData.band.name, seriesData.color)}
                onmouseleave={hideTooltip}
                onfocus={(event) => showTooltip(event, entry, seriesData.band.name, seriesData.color)}
                onblur={hideTooltip}
              />
            {/if}
          </g>
        {/if}
      {/each}
    {/each}
  </svg>

  {#if hoveredPoint}
    {@const aggregated = getAggregatedPlacements(hoveredPoint.entry)}
    <div class="tooltip" style={`left: ${tooltipX}px; top: ${tooltipY}px`}>
      <strong>{hoveredPoint.entry.year} · {hoveredPoint.bandName}</strong>
      {#if aggregated && aggregated.length}
        {#each aggregated as placement, index}
          <div class="tooltip-band">
            <div class="tooltip-band__title">{placement.band_name ?? 'Ukjent korps'}</div>
            <div>{placement.division} · #{placement.rank}</div>
            <div>Absolutt plassering: #{placement.absolute_position}</div>
            {#if (placement.field_size ?? 0) > 0}
              {@const relativePercent = getRelativePercent(placement).toFixed(1)}
              <div>Relativ plassering: {relativePercent}%</div>
            {/if}
            <div>Deltakere: {placement.division_size} (div) / {placement.field_size} (totalt)</div>
            {#if placement.points !== null}
              <div>Poeng: {placement.points} / {placement.max_points}</div>
            {/if}
            {#if placement.pieces.length > 0}
              <div>Stykker: {placement.pieces.join('; ')}</div>
            {/if}
          </div>
          {#if index < aggregated.length - 1}
            <div class="tooltip-divider"></div>
          {/if}
        {/each}
      {:else}
        <div>{hoveredPoint.entry.division} · #{hoveredPoint.entry.rank}</div>
        {#if hoveredPoint.entry.conductor}
          <div>Dirigent: {hoveredPoint.entry.conductor}</div>
        {/if}
        <div>Absolutt plassering: #{hoveredPoint.entry.absolute_position}</div>
        {#if (hoveredPoint.entry.field_size ?? 0) > 0}
          {@const relativePercent = getRelativePercent(hoveredPoint.entry).toFixed(1)}
          <div>Relativ plassering: {relativePercent}%</div>
        {/if}
        <div>Deltakere: {hoveredPoint.entry.division_size} (div) / {hoveredPoint.entry.field_size} (totalt)</div>
        {#if hoveredPoint.entry.points !== null}
          <div>Poeng: {hoveredPoint.entry.points} / {hoveredPoint.entry.max_points}</div>
        {/if}
        {#if hoveredPoint.entry.pieces.length > 0}
          <div>Stykker: {hoveredPoint.entry.pieces.join('; ')}</div>
        {/if}
      {/if}
    </div>
  {/if}

  <div class="year-labels" style={`top: ${yearAxisY}px`}>
    {#each yearLabelPositions as label}
      <span
        class:inactive={label.inactive}
        style={`left: ${label.x}px`}
      >
        {label.year}
      </span>
    {/each}
  </div>
</div>

{#if series.length > 0}
  <div class="band-legend">
    {#each series as item}
      <span>
        <svg width="42" height="14" aria-hidden="true">
          <line x1="2" y1="7" x2="40" y2="7" stroke={item.color} stroke-width="2.5" stroke-linecap="round" />
          {#if item.shape === 'circle'}
            <circle cx="21" cy="7" r="5" fill="var(--color-input-bg, #0f172a)" stroke={item.color} stroke-width="2" />
          {:else if item.shape === 'square'}
            <rect x="16" y="2" width="10" height="10" rx="2" fill="var(--color-input-bg, #0f172a)" stroke={item.color} stroke-width="2" />
          {:else}
            <path d={getTrianglePath(21, 7, 6)} fill="var(--color-input-bg, #0f172a)" stroke={item.color} stroke-width="2" />
          {/if}
        </svg>
        {item.band.name}
      </span>
    {/each}
  </div>
{/if}

{#if showDivisionLegend()}
  <div class="legend">
    {#each legendDivisions as division}
      <span>
        <i style={`background-color: ${divisionColors[division] ?? '#94a3b8'}`}></i>
        {division}
      </span>
    {/each}
  </div>
{/if}

<style>
  .tooltip {
    position: absolute;
    pointer-events: none;
    white-space: nowrap;
    padding: 0.5rem 0.75rem;
    background: var(--color-tooltip-bg);
    border: 1px solid var(--color-tooltip-border);
    border-radius: 0.5rem;
    color: var(--color-tooltip-text);
    font-size: 0.85rem;
    transform: translate(-50%, calc(-100% - 12px));
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.4);
  }

  .tooltip-band {
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
    margin-top: 0.35rem;
  }

  .tooltip-band:first-of-type {
    margin-top: 0.5rem;
  }

  .tooltip-band__title {
    font-weight: 600;
    color: var(--color-tooltip-text);
  }

  .tooltip-divider {
    height: 1px;
    margin: 0.35rem 0;
    background: var(--color-divider);
  }

  .chart-canvas {
    position: relative;
    padding-bottom: 12px;
  }

  .year-labels {
    position: absolute;
    left: 0;
    right: 0;
    top: 0;
    font-size: 0.75rem;
    color: var(--color-text-secondary);
    pointer-events: none;
  }

  .year-labels span {
    position: absolute;
    transform: translateX(-50%);
    white-space: nowrap;
  }

  .inactive {
    opacity: 1;
    color: var(--color-year-inactive);
  }

  .conductor-change text {
    transform: translateY(-4px);
  }

  .band-legend {
    margin-top: 1rem;
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    font-size: 0.85rem;
    color: var(--color-text-secondary);
  }

  .band-legend span {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
  }

  .band-legend svg {
    display: block;
  }

  .legend {
    margin-top: 1rem;
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    font-size: 0.8rem;
    color: var(--color-text-muted);
  }

  .legend span {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
  }

  .legend i {
    display: inline-block;
    width: 1rem;
    height: 0.35rem;
    border-radius: 999px;
  }
</style>
