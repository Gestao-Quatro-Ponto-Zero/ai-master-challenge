import { defineConfig } from 'vitest/config';
import { loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  return {
    plugins: [react()],
    server: {
      port: 5173,
      open: true,
      // Só é usado com VITE_API_MODE=http: encaminha /api/* para o backend FastAPI.
      proxy: {
        '/api': {
          target: env.G4_API_URL || env.VITE_API_PROXY_TARGET || 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
    test: {
      environment: 'jsdom',
      setupFiles: ['./src/test/setup.ts'],
      css: false,
      restoreMocks: true,
      // Repassa G4_API_URL (do .env ou do shell) aos testes de integração.
      env: {
        ...(env.G4_API_URL ? { G4_API_URL: env.G4_API_URL } : {}),
        ...(env.G4_API_USER ? { G4_API_USER: env.G4_API_USER } : {}),
      },
    },
  };
});
