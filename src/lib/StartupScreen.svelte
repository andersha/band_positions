<script lang="ts">
  import type { BandType } from './types';

  interface Props {
    onSelect: (type: BandType) => void;
  }

  let { onSelect }: Props = $props();
</script>

<div class="startup-screen">
  <div class="startup-content">
    <h1>NM Korps</h1>
    <p class="subtitle">Resultatoversikt</p>
    
    <div class="choice-container">
      <button 
        class="choice-button choice-button--janitsjar"
        onclick={() => onSelect('wind')}
      >
        <span class="choice-icon" aria-hidden="true">🎷</span>
        <span class="choice-title">NM Janitsjar</span>
        <span class="choice-description">Norges janitsjarkorps</span>
      </button>

      <button 
        class="choice-button choice-button--brass"
        onclick={() => onSelect('brass')}
      >
        <span class="choice-icon" aria-hidden="true">🎺</span>
        <span class="choice-title">NM Brass</span>
        <span class="choice-description">Norges brassband</span>
      </button>
    </div>
  </div>
</div>

<style>
  .startup-screen {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--gradient-page);
    z-index: 1000;
    padding: 2rem;
  }

  .startup-content {
    text-align: center;
    max-width: 600px;
    width: 100%;
  }

  h1 {
    margin: 0 0 0.5rem 0;
    font-size: 3rem;
    color: var(--color-text-primary);
    font-weight: 700;
  }

  .subtitle {
    margin: 0 0 3rem 0;
    font-size: 1.25rem;
    color: var(--color-text-secondary);
  }

  .choice-container {
    display: flex;
    gap: 1.5rem;
    flex-wrap: wrap;
    justify-content: center;
  }

  .choice-button {
    flex: 1;
    min-width: 220px;
    max-width: 280px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    padding: 2.5rem 2rem;
    background: var(--color-surface-card);
    border: 2px solid var(--color-border);
    border-radius: 1.5rem;
    cursor: pointer;
    transition: all 0.25s ease;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.2);
  }

  .choice-button:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 32px rgba(15, 23, 42, 0.35);
  }

  .choice-button:focus-visible {
    outline: 3px solid var(--color-accent);
    outline-offset: 3px;
  }

  .choice-button--janitsjar:hover {
    border-color: #38bdf8;
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, var(--color-surface-card) 100%);
  }

  .choice-button--brass:hover {
    border-color: #c084fc;
    background: linear-gradient(135deg, rgba(192, 132, 252, 0.1) 0%, var(--color-surface-card) 100%);
  }

  .choice-icon {
    font-size: 4rem;
    line-height: 1;
  }

  .choice-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--color-text-primary);
  }

  .choice-description {
    font-size: 0.95rem;
    color: var(--color-text-secondary);
  }

  @media (max-width: 640px) {
    h1 {
      font-size: 2.25rem;
    }

    .subtitle {
      font-size: 1.1rem;
      margin-bottom: 2rem;
    }

    .choice-container {
      gap: 1rem;
    }

    .choice-button {
      min-width: 100%;
      padding: 2rem 1.5rem;
    }

    .choice-icon {
      font-size: 3rem;
    }

    .choice-title {
      font-size: 1.3rem;
    }
  }
</style>
