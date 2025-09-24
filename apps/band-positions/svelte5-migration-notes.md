# Svelte 5 Migration Guide for Band Positions App

This document provides the key migration changes needed to upgrade the Norwegian Wind Band Orchestra visualization app from Svelte 4 to Svelte 5.

## Critical Breaking Changes

### 1. Reactivity System - Runes
- **`let` declarations** → `$state` rune for reactive variables
- **`$:` reactive statements** → `$derived` for computed values, `$effect` for side effects
- **`export let`** → `$props` rune for component properties

### 2. Event Handling
- **`on:click`** → `onclick` (standard DOM property)
- **Event modifiers** like `on:click|preventDefault` need to be handled explicitly
- **`createEventDispatcher`** → callback props (preferred in Svelte 5)

### 3. Component Instantiation 
- **`new Component()`** → `mount(Component, options)`
- **Component destruction** via `unmount(app)`
- **`$set` method** → direct state mutation with `$state`

### 4. Slots System Changes
- **Slots** → **Snippets** (new content projection system)
- **`<slot />`** → **`{@render children?.()}`**
- **Named slots** → snippet props

### 5. Lifecycle Changes
- **`onMount`** remains compatible but `$effect` is preferred for new code
- **`afterUpdate`** → `$effect` with proper dependencies

## Specific Changes for Our Codebase

### App.svelte Changes Needed

1. **State declarations** (lines 28-44):
```svelte
// OLD
let dataset: BandDataset | null = null;
let loading = true;
let searchTerm = '';

// NEW  
let dataset = $state<BandDataset | null>(null);
let loading = $state(true);
let searchTerm = $state('');
```

2. **Reactive statements** (lines 459-564):
```svelte  
// OLD
$: trimmed = searchTerm.trim();
$: activeRecords = isEntityView ? ... : [];

// NEW
const trimmed = $derived(searchTerm.trim());
const activeRecords = $derived(isEntityView ? ... : []);
```

3. **Event handlers** (lines 576, 585, etc.):
```svelte
// OLD
<button on:click={() => setView(view)}>

// NEW  
<button onclick={() => setView(view)}>
```

4. **Input binding and events** (lines 602-604):
```svelte
// OLD  
<input bind:value={searchTerm} on:input={onInput} on:keydown={handleKeyDown} />

// NEW
<input bind:value={searchTerm} oninput={onInput} onkeydown={handleKeyDown} />
```

### BandTrajectoryChart.svelte Changes

1. **Props declaration**:
```svelte
// OLD
export let bands: BandRecord[] = [];
export let years: number[] = [];

// NEW
let { bands = [], years = [], ...props } = $props<{
  bands?: BandRecord[];
  years?: number[];
  maxFieldSize?: number;
  yMode?: 'absolute' | 'relative';
  showConductorMarkers?: boolean;
}>();
```

2. **State variables**:
```svelte  
// OLD
let hoveredPoint: { entry: ChartEntry; bandName: string; lineColor: string } | null = null;

// NEW
let hoveredPoint = $state<{ entry: ChartEntry; bandName: string; lineColor: string } | null>(null);
```

### DataExplorer.svelte & PiecePerformances.svelte

Similar patterns:
- `export let dataset` → `let { dataset } = $props()`  
- Reactive statements `$:` → `$derived()` or `$effect()`
- Event handlers `on:change` → `onchange`

### main.ts Changes

```typescript
// OLD
const app = new App({
  target: document.getElementById('app') as HTMLElement
});

// NEW
import { mount } from 'svelte';
const app = mount(App, { 
  target: document.getElementById('app') as HTMLElement 
});
```

## Migration Strategy

1. **Automated migration** via `npx sv migrate svelte-5`
2. **Manual fixes** for complex reactive patterns
3. **TypeScript updates** for new component types
4. **Testing** of D3 integration and URL state management

## Compatibility Notes

- Can enable `compatibility.componentApi: 4` in svelte.config.js for gradual migration
- Most Svelte 4 patterns still work but generate warnings
- Performance improvements expected with new reactivity system

## Files Requiring Updates

- `src/App.svelte` (major changes to reactivity)
- `src/lib/BandTrajectoryChart.svelte` (props, state, lifecycle)
- `src/lib/DataExplorer.svelte` (props, events)  
- `src/lib/PiecePerformances.svelte` (props)
- `src/main.ts` (component instantiation)
- `package.json` (dependency updates)
- `svelte.config.js` (compiler options)