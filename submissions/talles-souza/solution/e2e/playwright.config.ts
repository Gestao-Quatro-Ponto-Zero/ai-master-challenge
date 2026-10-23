/**
 * E2E do Lead Scorer: sobe o app como o avaliador sobe (`npm start`, API + web numa porta só)
 * e grava vídeo de cada fluxo em `e2e/videos/`. Sobe sem `DATABASE_URL`: deals.json + memória.
 */
import { defineConfig, devices } from '@playwright/test';

const PORTA = Number(process.env.E2E_PORTA ?? 8787);
const BASE = 'http://127.0.0.1:' + PORTA;

export default defineConfig({
  testDir: './testes',
  outputDir: './videos',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 60_000,
  reporter: [['list']],
  use: {
    baseURL: BASE,
    video: 'on',
    trace: 'retain-on-failure',
    locale: 'pt-BR',
  },
  projects: [
    {
      name: 'desktop',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1280, height: 800 } },
    },
    {
      name: 'celular',
      use: { ...devices['Desktop Chrome'], viewport: { width: 390, height: 844 } },
      grep: /@celular/,
    },
  ],
  webServer: {
    command: 'npm start',
    cwd: '..',
    url: BASE + '/health',
    reuseExistingServer: false,
    timeout: 240_000,
    // sem banco: o E2E grava respostas e decisões, e elas não podem ir para o banco compartilhado.
    // Balde maior no rate limit: todos os fluxos saem do mesmo IP (127.0.0.1) e a suíte passa dos
    // 60 pedidos de uma vez; o limite em si é testado em apps/api/test/protecoes.test.ts.
    env: { PORT: String(PORTA), DATABASE_URL: '', RATE_LIMIT_CAPACIDADE: '1000' },
  },
});
