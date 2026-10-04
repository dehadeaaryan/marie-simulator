import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
export default defineConfig({
  plugins: [sveltekit()],
  server: { proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: false } }, port: 5175, strictPort: true },
  preview: { proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: false } }, port: 4173, strictPort: true }
});
