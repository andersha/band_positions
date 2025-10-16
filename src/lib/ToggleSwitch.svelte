<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  interface Props {
    value: string;
    options: [string, string];
    labels: [string, string];
    ariaLabel: string;
  }

  let { value = $bindable(), options, labels, ariaLabel }: Props = $props();

  const dispatch = createEventDispatcher<{ change: { value: string } }>();

  function toggle(): void {
    const newValue = value === options[0] ? options[1] : options[0];
    value = newValue;
    dispatch('change', { value: newValue });
  }

  function handleKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      toggle();
    }
  }

  let isFirstOption = $derived(value === options[0]);
</script>

<div class="toggle-switch" role="group" aria-label={ariaLabel}>
  <button
    type="button"
    class="toggle-switch__option"
    class:active={isFirstOption}
    onclick={() => {
      if (!isFirstOption) toggle();
    }}
    aria-pressed={isFirstOption}
  >
    {labels[0]}
  </button>
  <button
    type="button"
    class="toggle-switch__option"
    class:active={!isFirstOption}
    onclick={() => {
      if (isFirstOption) toggle();
    }}
    aria-pressed={!isFirstOption}
  >
    {labels[1]}
  </button>
  <div
    class="toggle-switch__slider"
    class:toggle-switch__slider--right={!isFirstOption}
  ></div>
</div>

<style>
  .toggle-switch {
    position: relative;
    display: inline-flex;
    align-items: center;
    background: var(--color-mode-toggle-bg);
    border: 1px solid var(--color-mode-toggle-border);
    border-radius: 999px;
    padding: 0.25rem;
    gap: 0.25rem;
    isolation: isolate;
  }

  .toggle-switch__option {
    position: relative;
    z-index: 2;
    appearance: none;
    border: none;
    background: transparent;
    color: var(--color-text-secondary);
    padding: 0.5rem 1.25rem;
    border-radius: 999px;
    font-size: 0.9rem;
    cursor: pointer;
    transition: color 0.2s ease;
    min-height: 44px; /* iOS tap target */
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 1;
    min-width: 0;
  }

  .toggle-switch__option:hover {
    color: var(--color-text-primary);
  }

  .toggle-switch__option.active {
    color: var(--color-text-primary);
    font-weight: 600;
  }

  .toggle-switch__option:focus-visible {
    outline: 2px solid var(--color-accent);
    outline-offset: 2px;
  }

  .toggle-switch__slider {
    position: absolute;
    z-index: 1;
    top: 0.25rem;
    left: 0.25rem;
    width: calc(50% - 0.375rem);
    height: calc(100% - 0.5rem);
    background: var(--color-accent-strong);
    border-radius: 999px;
    transition: transform 0.2s ease;
    pointer-events: none;
  }

  .toggle-switch__slider--right {
    transform: translateX(calc(100% + 0.25rem));
  }

  @media (max-width: 450px) {
    .toggle-switch__option {
      padding: 0.5rem 1rem;
      font-size: 0.85rem;
    }
  }
</style>
