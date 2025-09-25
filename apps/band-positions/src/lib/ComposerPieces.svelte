<script lang="ts">
  import type { ComposerRecord } from './types';
  interface Props {
    composers?: ComposerRecord[];
  }

  let { composers = [] }: Props = $props();

  let sortedComposers = $derived([...composers].sort((a, b) => a.name.localeCompare(b.name)));
</script>

<section class="composers-view">
  {#each sortedComposers as composer}
    <article class="composer-card">
      <header class="composer-header">
        <div>
          <h2>{composer.name}</h2>
          <p>{composer.pieces.length} {composer.pieces.length === 1 ? 'stykke' : 'stykker'}</p>
        </div>
      </header>
      <ul>
        {#each composer.pieces as piece}
          <li>
            <a href={`?view=pieces&piece=${encodeURIComponent(piece.slug)}`}>
              {piece.name}
            </a>
          </li>
        {/each}
      </ul>
    </article>
  {/each}
</section>

<style>
  .composers-view {
    display: flex;
    flex-direction: column;
    gap: 1.75rem;
    margin-top: 1rem;
  }

  .composer-card {
    padding: 1.5rem;
    background: var(--color-surface-card);
    border-radius: 1rem;
    border: 1px solid var(--color-border);
    box-shadow: 0 18px 40px rgba(15, 23, 42, 0.25);
  }

  .composer-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .composer-header h2 {
    margin: 0;
    color: var(--color-accent);
  }

  .composer-header p {
    margin: 0.25rem 0 0;
    color: var(--color-text-secondary);
    font-size: 0.9rem;
  }

  ul {
    margin: 0;
    padding-left: 1.1rem;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }

  li {
    color: var(--color-text-primary);
    font-size: 0.95rem;
  }

  a {
    color: var(--color-accent);
    text-decoration: none;
  }

  a:hover,
  a:focus-visible {
    text-decoration: underline;
  }
</style>
