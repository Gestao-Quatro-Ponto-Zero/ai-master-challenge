import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

const apiPort = process.env.API_PORT ?? '3001';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    strictPort: true,
    proxy: {
      '/api': `http://127.0.0.1:${apiPort}`,
    },
    watch: process.env.CODEX_SANDBOX === 'seatbelt' ? { usePolling: true } : undefined,
  },
});
