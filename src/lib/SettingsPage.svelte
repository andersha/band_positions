<script lang="ts">
  import { untrack } from 'svelte';
  import ToggleSwitch from './ToggleSwitch.svelte';

  interface Props {
    yAxisMode: 'absolute' | 'relative';
    yAxisScale: 'fitted' | 'full';
    theme: 'light' | 'dark';
    onYAxisModeChange?: (value: 'absolute' | 'relative') => void;
    onYAxisScaleChange?: (value: 'fitted' | 'full') => void;
    onThemeChange?: (value: 'light' | 'dark') => void;
  }

  let { 
    yAxisMode = $bindable(), 
    yAxisScale = $bindable(), 
    theme = $bindable(),
    onYAxisModeChange,
    onYAxisScaleChange,
    onThemeChange
  }: Props = $props();

  let initialized = false;

  // Watch for changes and call parent handlers (skip first run)
  $effect(() => {
    if (!initialized) {
      // Skip the initial run
      untrack(() => {
        yAxisMode;
        initialized = true;
      });
      return;
    }
    onYAxisModeChange?.(yAxisMode);
  });

  $effect(() => {
    if (!initialized) return;
    onYAxisScaleChange?.(yAxisScale);
  });

  $effect(() => {
    if (!initialized) return;
    onThemeChange?.(theme);
  });
</script>

<section class="settings-page">
  <header class="settings-header">
    <h2>Innstillinger</h2>
    <p class="settings-lead">
      Tilpass visningen av diagrammer og tema. Endringer lagres automatisk og gjelder for alle visninger.
    </p>
  </header>

  <div class="settings-grid">
    <div class="setting-card">
      <div class="setting-info">
        <h3>Plassering</h3>
        <p>
          Velg hvordan plasseringer vises i diagrammet. <strong>Relativ</strong> viser plassering som prosent av 
          antall deltakere (f.eks. 10% = topp 10%). <strong>Absolutt</strong> viser faktisk plasseringsnummer 
          (f.eks. 3. plass).
        </p>
      </div>
      <div class="setting-control">
        <ToggleSwitch
          bind:value={yAxisMode}
          options={['absolute', 'relative']}
          labels={['Absolutt', 'Relativ']}
          ariaLabel="Velg plasseringsvisning"
        />
      </div>
    </div>

    <div class="setting-card">
      <div class="setting-info">
        <h3>Y-akse</h3>
        <p>
          Velg hvordan Y-aksen skaleres. <strong>Tilpasset</strong> zoomer inn på de faktiske plasseringene 
          for bedre detaljer. <strong>Full</strong> viser hele skalaen fra beste til dårligste mulige plassering.
        </p>
      </div>
      <div class="setting-control">
        <ToggleSwitch
          bind:value={yAxisScale}
          options={['fitted', 'full']}
          labels={['Tilpasset', 'Full']}
          ariaLabel="Velg Y-akse skalering"
        />
      </div>
    </div>

    <div class="setting-card">
      <div class="setting-info">
        <h3>Tema</h3>
        <p>
          Velg fargetema for appen. <strong>Mørkt</strong> tema er bedre for svakt lys og sparer batteri på OLED-skjermer. 
          <strong>Lyst</strong> tema er bedre i sterkt lys.
        </p>
      </div>
      <div class="setting-control">
        <ToggleSwitch
          bind:value={theme}
          options={['dark', 'light']}
          labels={['Mørkt', 'Lyst']}
          ariaLabel="Velg fargetema"
        />
      </div>
    </div>
  </div>
</section>

<style>
  .settings-page {
    max-width: 900px;
    margin: 0 auto;
  }

  .settings-header {
    margin-bottom: 2rem;
  }

  .settings-header h2 {
    margin: 0 0 0.5rem 0;
    font-size: 1.75rem;
    color: var(--color-accent);
  }

  .settings-lead {
    margin: 0;
    color: var(--color-text-secondary);
    font-size: 1rem;
    line-height: 1.6;
  }

  .settings-grid {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  .setting-card {
    background: var(--color-surface-card);
    border: 1px solid var(--color-border);
    border-radius: 1rem;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
  }

  .setting-info h3 {
    margin: 0 0 0.5rem 0;
    font-size: 1.15rem;
    color: var(--color-text-primary);
  }

  .setting-info p {
    margin: 0;
    color: var(--color-text-secondary);
    font-size: 0.9rem;
    line-height: 1.6;
  }

  .setting-control {
    display: flex;
    justify-content: flex-start;
  }

  @media (min-width: 640px) {
    .setting-card {
      flex-direction: row;
      align-items: center;
      justify-content: space-between;
    }

    .setting-info {
      flex: 1;
      padding-right: 2rem;
    }

    .setting-control {
      flex-shrink: 0;
    }
  }

  @media (max-width: 450px) {
    .settings-header h2 {
      font-size: 1.4rem;
    }

    .settings-lead {
      font-size: 0.9rem;
    }

    .setting-card {
      padding: 1rem;
      gap: 1rem;
    }

    .setting-info h3 {
      font-size: 1.05rem;
    }

    .setting-info p {
      font-size: 0.85rem;
    }
  }
</style>
