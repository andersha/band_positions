import { rm } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const OUT_DIR_RELATIVE = '../../docs/band-positions';
const assetsDir = path.resolve(__dirname, OUT_DIR_RELATIVE, 'assets');

// Clean out the pre-generated assets folder while leaving other published files intact.
const cleanAssetsPlugin = () => ({
  name: 'clean-docs-assets',
  apply: 'build',
  async buildStart() {
    await rm(assetsDir, { recursive: true, force: true });
  }
});

export default defineConfig({
  plugins: [svelte(), cleanAssetsPlugin()],
  base: './',
  build: {
    outDir: OUT_DIR_RELATIVE,
    emptyOutDir: false
  }
});
