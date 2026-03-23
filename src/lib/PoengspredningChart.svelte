<script lang="ts">
  import { scaleLinear, scalePoint, ticks } from 'd3';
  import type { BandRecord, BandType, PromotionRules } from './types';
  import { determinePromotionStatus } from './promotionUtils';

  interface Props {
    bands: BandRecord[];
    bandType: BandType;
  }

  let { bands, bandType }: Props = $props();

  const margin = { top: 16, right: 16, bottom: 40, left: 48 };
  const width = 880;
  const height = 360;
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  let promotionRules = $state<PromotionRules | null>(null);

  $effect(() => {
    fetch('data/promotion_rules.json')
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) promotionRules = data; })
      .catch(() => {});
  });

  function getDivisionOrder(division: string): number {
    const norm = division.trim().toLowerCase();
    if (norm === 'elite') return 0;
    const m = norm.match(/(\d+)/);
    return m ? parseInt(m[1], 10) : 99;
  }

  // Divisions that have at least one scored entry
  let availableDivisions = $derived.by(() => {
    const seen = new Set<string>();
    for (const band of bands) {
      for (const entry of band.entries) {
        if (entry.points !== null && entry.division) seen.add(entry.division);
      }
    }
    return [...seen].sort((a, b) => getDivisionOrder(a) - getDivisionOrder(b));
  });

  let selectedDivision = $state('');

  // Auto-select first available division
  $effect(() => {
    if (availableDivisions.length > 0 && !availableDivisions.includes(selectedDivision)) {
      selectedDivision = availableDivisions[0];
    }
  });

  interface YearBands {
    year: number;
    topMax: number;
    greenBlueEdge: number; // boundary: bottom of green / top of blue = max safe score
    blueRedEdge: number;   // boundary: bottom of blue / top of red = min safe score
    bottomMin: number;
  }

  let chartData = $derived.by(() => {
    if (!selectedDivision) return [];

    // Collect all (year, points, rank) for this division
    const byYear = new Map<number, Array<{ points: number; rank: number | null }>>();
    for (const band of bands) {
      for (const entry of band.entries) {
        if (entry.division !== selectedDivision || entry.points === null) continue;
        if (!byYear.has(entry.year)) byYear.set(entry.year, []);
        byYear.get(entry.year)!.push({ points: entry.points, rank: entry.rank });
      }
    }

    const result: YearBands[] = [];
    for (const [year, entries] of byYear) {
      if (entries.length === 0) continue;

      const promoted: number[] = [];
      const safe: number[] = [];
      const demoted: number[] = [];

      for (const e of entries) {
        const status = determinePromotionStatus(promotionRules, bandType, year, selectedDivision, e.rank);
        if (status === 'promote') promoted.push(e.points);
        else if (status === 'demote') demoted.push(e.points);
        else safe.push(e.points);
      }

      const allPoints = entries.map(e => e.points);
      const topMax = Math.max(...allPoints);
      const bottomMin = Math.min(...allPoints);

      // Zone boundaries defined by safe band scores so promoted/demoted areas
      // extend fully rather than collapsing to a thin line when only 1 band qualifies.
      // Fallback to promoted/demoted min/max when no safe bands exist.
      const greenBlueEdge = safe.length > 0
        ? Math.max(...safe)
        : (promoted.length > 0 ? Math.min(...promoted) : topMax);
      const blueRedEdge = safe.length > 0
        ? Math.min(...safe)
        : (demoted.length > 0 ? Math.max(...demoted) : bottomMin);

      result.push({ year, topMax, greenBlueEdge, blueRedEdge, bottomMin });
    }

    return result.sort((a, b) => a.year - b.year);
  });

  let activeYears = $derived(chartData.map(d => d.year));

  let globalMin = $derived(chartData.length > 0 ? Math.min(...chartData.map(d => d.bottomMin)) : 0);
  let globalMax = $derived(chartData.length > 0 ? Math.max(...chartData.map(d => d.topMax)) : 100);

  let xScale = $derived(
    scalePoint<number>()
      .domain(activeYears)
      .range([0, innerWidth])
      .padding(0.3)
  );

  let yScale = $derived(
    scaleLinear()
      .domain([Math.max(0, globalMin - 3), Math.min(100, globalMax + 3)])
      .range([innerHeight, 0])
      .nice()
  );

  let yTicks = $derived(ticks(Math.max(0, globalMin - 3), Math.min(100, globalMax + 3), 8));

  // Build area path: goes right along topLine, then left along bottomLine
  function areaPath(points: Array<{ x: number; y1: number; y2: number }>): string {
    if (points.length === 0) return '';
    const top = points.map(p => `${p.x},${p.y1}`).join(' L ');
    const bot = [...points].reverse().map(p => `${p.x},${p.y2}`).join(' L ');
    return `M ${top} L ${bot} Z`;
  }

  let greenPath = $derived.by(() => {
    const pts = chartData.map(d => ({
      x: xScale(d.year)!,
      y1: yScale(d.topMax),
      y2: yScale(d.greenBlueEdge),
    }));
    return areaPath(pts);
  });

  let bluePath = $derived.by(() => {
    const pts = chartData.map(d => ({
      x: xScale(d.year)!,
      y1: yScale(d.greenBlueEdge),
      y2: yScale(d.blueRedEdge),
    }));
    return areaPath(pts);
  });

  let redPath = $derived.by(() => {
    const pts = chartData.map(d => ({
      x: xScale(d.year)!,
      y1: yScale(d.blueRedEdge),
      y2: yScale(d.bottomMin),
    }));
    return areaPath(pts);
  });

  // Only label every other year when there are many data points
  let xLabels = $derived(
    activeYears.length > 15
      ? activeYears.filter((_, i) => i % 2 === 0)
      : activeYears
  );
</script>

<div class="poengspredning-chart">
  <div class="chart-controls">
    <select
      value={selectedDivision}
      onchange={(e) => { selectedDivision = (e.currentTarget as HTMLSelectElement).value; }}
      class="division-select"
    >
      {#each availableDivisions as div}
        <option value={div}>{div}</option>
      {/each}
    </select>
    <span class="chart-legend">
      <span class="legend-dot promote"></span>Rykker opp
      <span class="legend-dot safe"></span>Trygg
      <span class="legend-dot demote"></span>Rykker ned
    </span>
  </div>

  {#if chartData.length === 0}
    <div class="empty-state">Ingen poengdata for {selectedDivision || 'valgt divisjon'}.</div>
  {:else}
    <div class="svg-wrapper">
      <svg
        viewBox="0 0 {width} {height}"
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label="Poengspredning for {selectedDivision}"
      >
        <g transform="translate({margin.left},{margin.top})">
          <!-- Y-axis grid lines and labels -->
          {#each yTicks as tick}
            <line
              x1={0} x2={innerWidth}
              y1={yScale(tick)} y2={yScale(tick)}
              stroke="var(--color-border)"
              stroke-opacity="0.5"
              stroke-width="1"
            />
            <text
              x={-8}
              y={yScale(tick)}
              text-anchor="end"
              dominant-baseline="middle"
              class="axis-label"
            >{tick}</text>
          {/each}

          <!-- Colored area paths -->
          {#if redPath}
            <path d={redPath} fill="rgba(239,68,68,0.55)" />
          {/if}
          {#if bluePath}
            <path d={bluePath} fill="rgba(59,130,246,0.45)" />
          {/if}
          {#if greenPath}
            <path d={greenPath} fill="rgba(16,185,129,0.55)" />
          {/if}

          <!-- Top and bottom boundary lines -->
          <polyline
            points={chartData.map(d => `${xScale(d.year)},${yScale(d.topMax)}`).join(' ')}
            fill="none"
            stroke="rgba(16,185,129,0.9)"
            stroke-width="1.5"
          />
          <polyline
            points={chartData.map(d => `${xScale(d.year)},${yScale(d.bottomMin)}`).join(' ')}
            fill="none"
            stroke="rgba(239,68,68,0.9)"
            stroke-width="1.5"
          />

          <!-- X-axis year labels (thinned when > 15 years) -->
          {#each xLabels as year}
            <text
              x={xScale(year)}
              y={innerHeight + 24}
              text-anchor="middle"
              class="axis-label"
            >{year}</text>
          {/each}

          <!-- X-axis baseline -->
          <line
            x1={0} x2={innerWidth}
            y1={innerHeight} y2={innerHeight}
            stroke="var(--color-border)"
            stroke-width="1"
          />
        </g>
      </svg>
    </div>
  {/if}
</div>

<style>
  .poengspredning-chart {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .chart-controls {
    display: flex;
    align-items: center;
    gap: 1.25rem;
    flex-wrap: wrap;
  }

  .division-select {
    padding: 0.5rem 0.75rem;
    border-radius: 0.6rem;
    border: 1px solid var(--color-border);
    background: var(--color-surface-card);
    color: var(--color-text-primary);
    font-size: 16px;
    cursor: pointer;
  }

  .chart-legend {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.85rem;
    color: var(--color-text-secondary);
  }

  .legend-dot {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 2px;
    margin-left: 0.5rem;
  }

  .legend-dot.promote { background: rgba(16,185,129,0.8); }
  .legend-dot.safe    { background: rgba(59,130,246,0.7); }
  .legend-dot.demote  { background: rgba(239,68,68,0.8); }

  .svg-wrapper {
    border-radius: 1rem;
    border: 1px solid var(--color-border);
    background: var(--color-surface-card);
    box-shadow: 0 18px 40px rgba(15, 23, 42, 0.25);
    overflow: hidden;
  }

  svg {
    width: 100%;
    height: auto;
    display: block;
  }

  .axis-label {
    font-size: 11px;
    fill: var(--color-text-secondary);
    font-family: inherit;
  }

  .empty-state {
    padding: 3rem;
    text-align: center;
    color: var(--color-text-secondary);
    border-radius: 1rem;
    border: 1px solid var(--color-border);
    background: var(--color-surface-card);
  }
</style>
