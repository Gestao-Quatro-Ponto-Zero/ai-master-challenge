import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

// A API roda em 8787 (npm run dev -w @lead-scorer/api); no dev e no preview a web repassa /api e /health.
const API_URL = process.env.API_URL ?? 'http://localhost:8787';
const proxy = {
  '/api': { target: API_URL, changeOrigin: true },
  '/health': { target: API_URL, changeOrigin: true },
};

export default defineConfig({
  plugins: [react()],
  server: { port: 5173, strictPort: true, proxy },
  preview: { port: 4173, strictPort: true, proxy },
  build: { outDir: 'dist', emptyOutDir: true },
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.{ts,tsx}'],
  },
});
