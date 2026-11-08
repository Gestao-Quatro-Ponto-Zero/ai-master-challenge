import type { DealsApi } from './DealsApi';
import { HttpDealsApi } from './HttpDealsApi';
import { MockDealsApi } from './mock/MockDealsApi';

type Env = Record<string, string | undefined>;

/** Escolhe a implementação pela variável VITE_API_MODE. Padrão: API real em `npm run dev`, mock nos demais modos. */
export function createApi(env: Env = import.meta.env as Env): DealsApi {
  const mode = env.VITE_API_MODE ?? (env.MODE === 'development' ? 'http' : 'mock');
  if (mode === 'http') {
    return new HttpDealsApi({
      baseUrl: env.VITE_API_BASE_URL || '/api/v1',
      userKey: env.VITE_API_USER || 'vicki-laflamme',
    });
  }
  return new MockDealsApi({
    latencyMs: Number(env.VITE_MOCK_LATENCY_MS ?? 200) || 0,
    showProbability: env.VITE_SHOW_PROBABILITY === 'true',
  });
}
