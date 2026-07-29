import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./vitest-setup.ts'],
    include: ['test/**/*.{test,spec}.{js,ts}'],
    alias: {
      '$lib': '/Users/anders.abrahamsen/apps/band_app/app/src/lib',
    },
  },
});
