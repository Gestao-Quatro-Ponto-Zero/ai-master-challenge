import { describe, expect, it, vi } from 'vitest';
import sample from './__fixtures__/deals.sample.json';
import { HttpDealsApi, buildListQuery, decodeFeedback, encodeFeedback, mapDeal, type DealDto } from './HttpDealsApi';
import type { ListDealsQuery } from './types';
import { ApiError } from './errors';

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } });

const dtos = sample.items as unknown as DealDto[];
const memory = () => {
  const m = new Map<string, string>();
  return { getItem: (k: string) => m.get(k) ?? null, setItem: (k: string, v: string) => void m.set(k, v), removeItem: (k: string) => void m.delete(k) };
};

const META_BODY = {
  reference_date: '2017-12-31', model_version: 'v1', show_probability: false,
  thresholds: { typical_p50: 45, stale_days: 104, review_days: 138, focus_score: 80, follow_up_score: 40 },
  priority_levels: [
    { key: 'high', label: 'Alta', min_score: 80, max_score: 100 },
    { key: 'medium', label: 'Média', min_score: 40, max_score: 79 },
    { key: 'low', label: 'Baixa', min_score: 0, max_score: 39 },
  ],
  views: [{ key: 'focus', bands: ['focus'], default_sort: 'score' }, { key: 'ev', bands: ['focus'], default_sort: 'expected_value' }],
  low_confidence_below_closed_deals: 30,
};

/** Servidor falso com o formato real: login, /me, /meta, /summary e /deals (devolve o que o teste pedir). */
function fakeServer(extra: Record<string, () => Response> = {}) {
  const calls: { method: string; url: string; auth: string | null }[] = [];
  const fetchImpl = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const headers = (init?.headers ?? {}) as Record<string, string>;
    calls.push({ method: init?.method ?? 'GET', url, auth: headers.Authorization ?? null });
    for (const [key, make] of Object.entries(extra)) if (url.includes(key)) return make();
    if (url.endsWith('/auth/login')) return json({ access_token: 'tok-1', token_type: 'bearer', expires_in: 60 });
    if (url.includes('/deals?')) return json({ items: dtos, total: dtos.length, page: 1, page_size: 10 });
    return json({}, 404);
  });
  const dealCalls = () => calls.filter((c) => c.url.includes('/deals?')).map((c) => new URL(c.url, 'http://x').searchParams);
  return { fetchImpl: fetchImpl as unknown as typeof fetch, calls, dealCalls };
}

const base: ListDealsQuery = { tab: 'focus', product: 'all', q: '', sort: null, level: 'all', page: 1, pageSize: 10 };

describe('mapDeal (resposta real da API)', () => {
  it('usa os campos da API sem recalcular', () => {
    for (const dto of dtos) {
      const deal = mapDeal(dto);
      expect(deal.id).toBe(dto.opportunity_id);
      expect(deal.tab).toBe(dto.view);
      expect(deal.band).toBe(dto.band);
      expect(deal.priorityLevel).toBe(dto.priority_level);
      expect(deal.suggestedAction).toBe(dto.suggested_action);
      expect(deal.confidenceReason).toBe(dto.confidence_reason);
      expect(deal.confidence).toBe(dto.confidence);
      expect(deal.score).toBe(dto.score);
      expect(deal.price).toBe(dto.list_price);
      expect(deal.expectedValue).toBe(dto.expected_value);
      expect(deal.probability).toBeNull(); // p_win vem nulo quando show_probability=false
      expect(deal.reasons.length).toBeGreaterThan(0);
    }
  });
  it('completude dos dados vem da API (data_quality) e é nula em API antiga', () => {
    const dq = { status: 'incomplete', summary: 'Falta informar a conta.', missing: [{ field: 'account', label: 'Conta', affects_prediction: false }] };
    expect(mapDeal({ ...dtos[0], data_quality: dq } as DealDto).dataQuality).toEqual({
      status: 'incomplete',
      summary: 'Falta informar a conta.',
      missing: [{ field: 'account', label: 'Conta', affectsPrediction: false }],
    });
    expect(mapDeal({ ...dtos[0], data_quality: undefined } as DealDto).dataQuality).toBeNull();
  });
  it('a aba vem de view, mesmo que a faixa sugira outra', () => {
    const dto = { ...dtos[0], band: 'low', view: 'decide' } as DealDto;
    expect(mapDeal(dto).tab).toBe('decide');
  });
  it('direção dos motivos: positive->pos, negative->neg, tempo no funil negativo->warn', () => {
    const dto = { ...dtos[0], reasons: [
      { code: 'price', label: 'a', value: '1', direction: 'positive', impact: 0.5 },
      { code: 'agent_load', label: 'b', value: '1', direction: 'negative', impact: 0.3 },
      { code: 'age_band', label: 'c', value: '1', direction: 'negative', impact: 0.2 },
    ] } as DealDto;
    expect(mapDeal(dto).reasons.map((r) => r.direction)).toEqual(['pos', 'neg', 'warn']);
  });
});

describe('buildListQuery', () => {
  it('manda tudo ao servidor e omite o que não é filtro', () => {
    expect(buildListQuery(base)).toEqual({ view: 'focus', priority: undefined, product: undefined, q: undefined, sort: undefined, order: 'desc', page: 1, page_size: 10 });
    expect(buildListQuery({ ...base, tab: 'ev', level: 'high', product: 'GTX Pro', q: ' acme ', sort: 'age_days', page: 3, pageSize: 25 })).toEqual({
      view: 'ev', priority: 'high', product: 'GTX Pro', q: 'acme', sort: 'age_days', order: 'desc', page: 3, page_size: 25,
    });
  });
});

describe('feedback', () => {
  it('ida e volta', () => {
    expect(encodeFeedback('act', null)).toEqual({ action: 'worked', comment: null });
    expect(encodeFeedback('ignore', null)).toEqual({ action: 'ignore', comment: null });
    const d = encodeFeedback('disagree', 'value');
    expect(d).toEqual({ action: 'disagree', comment: 'reason:value' });
    expect(decodeFeedback(d.action, d.comment)).toEqual({ kind: 'disagree', reason: 'value' });
    expect(decodeFeedback('worked', null)).toEqual({ kind: 'act', reason: null });
  });
});

describe('HttpDealsApi', () => {
  it('faz login com o user_key e usa o token nas chamadas', async () => {
    const { fetchImpl, calls } = fakeServer();
    const api = new HttpDealsApi({ fetchImpl, userKey: 'vicki-laflamme', storage: memory() });
    await api.listDeals(base);
    expect(calls[0]).toMatchObject({ method: 'POST', url: '/api/v1/auth/login', auth: null });
    expect(calls.slice(1).every((c) => c.auth === 'Bearer tok-1')).toBe(true);
  });

  it('trocar aba, filtro, busca, ordem e página dispara GET /deals com os parâmetros certos', async () => {
    const { fetchImpl, dealCalls } = fakeServer();
    const api = new HttpDealsApi({ fetchImpl, userKey: 'u', storage: memory() });
    await api.listDeals({ ...base, tab: 'decide' });
    await api.listDeals({ ...base, tab: 'decide', level: 'medium' });
    await api.listDeals({ ...base, tab: 'decide', product: 'MG Special' });
    await api.listDeals({ ...base, tab: 'decide', q: 'abc' });
    await api.listDeals({ ...base, tab: 'decide', sort: 'expected_value' });
    await api.listDeals({ ...base, tab: 'decide', page: 2, pageSize: 25 });
    const p = dealCalls().map((s) => Object.fromEntries(s.entries()));
    expect(p).toEqual([
      { view: 'decide', order: 'desc', page: '1', page_size: '10' },
      { view: 'decide', priority: 'medium', order: 'desc', page: '1', page_size: '10' },
      { view: 'decide', product: 'MG Special', order: 'desc', page: '1', page_size: '10' },
      { view: 'decide', q: 'abc', order: 'desc', page: '1', page_size: '10' },
      { view: 'decide', sort: 'expected_value', order: 'desc', page: '1', page_size: '10' },
      { view: 'decide', order: 'desc', page: '2', page_size: '25' },
    ]);
  });

  it('cada chamada vai ao servidor (sem cache nem filtro no cliente)', async () => {
    const { fetchImpl, dealCalls } = fakeServer();
    const api = new HttpDealsApi({ fetchImpl, userKey: 'u', storage: memory() });
    const page = await api.listDeals(base);
    await api.listDeals(base);
    expect(dealCalls().length).toBe(2);
    expect(page.items.map((d) => d.id)).toEqual(dtos.map((d) => d.opportunity_id)); // mesma ordem do servidor
    expect(page.total).toBe(dtos.length);
  });

  it('entra de novo quando o token expira (401)', async () => {
    let first = true;
    const { fetchImpl, calls } = fakeServer({
      '/me': () => {
        if (first) {
          first = false;
          return json({ error: { code: 'UNAUTHENTICATED', message: 'expirou' } }, 401);
        }
        return json({ user_key: 'u', full_name: 'Vicki Laflamme', role: 'seller', regional_office: 'West' });
      },
    });
    const api = new HttpDealsApi({ fetchImpl, userKey: 'u', storage: memory() });
    const me = await api.getCurrentUser();
    expect(me).toEqual({ userKey: 'u', name: 'Vicki Laflamme', role: 'seller', region: 'West' });
    expect(calls.filter((c) => c.url.endsWith('/auth/login')).length).toBe(2);
  });

  it('lê limiares, níveis de prioridade e abas de /meta', async () => {
    const { fetchImpl } = fakeServer({ '/meta': () => json(META_BODY) });
    const meta = await new HttpDealsApi({ fetchImpl, userKey: 'u', storage: memory() }).getMeta();
    expect(meta).toMatchObject({
      modelVersion: 'v1', sampleData: false, lowConfidenceBelowClosedDeals: 30,
      thresholds: { typicalP50: 45, staleDays: 104, reviewDays: 138, focusScore: 80, followUpScore: 40 },
    });
    expect(meta.priorityLevels[0]).toEqual({ key: 'high', label: 'Alta', minScore: 80, maxScore: 100 });
    expect(meta.views[1]).toEqual({ key: 'ev', bands: ['focus'], defaultSort: 'expected_value' });
  });

  it('totais vêm de /summary (views)', async () => {
    const { fetchImpl } = fakeServer({ '/summary': () => json({ views: { focus: { count: 5, expected_value: 100 }, ev: { count: 24, expected_value: 900 } } }) });
    const s = await new HttpDealsApi({ fetchImpl, userKey: 'u', storage: memory() }).getSummary();
    expect(s.views.focus).toEqual({ count: 5, expectedValue: 100 });
    expect(s.views.ev).toEqual({ count: 24, expectedValue: 900 });
  });

  it('heatmap do funil vem de /summary (funnel)', async () => {
    const funnel = {
      columns: [{ key: 'd0', label: 'até 45 d', min_days: 0, max_days: 45 }, { key: 'd1', label: 'mais de 45 d', min_days: 46, max_days: null }],
      rows: [{ product: 'GTX Pro', count: 3, expected_value: 90, cells: [{ count: 1, expected_value: 90 }, { count: 2, expected_value: 0 }] }],
    };
    const { fetchImpl } = fakeServer({ '/summary': () => json({ views: {}, funnel }) });
    const s = await new HttpDealsApi({ fetchImpl, userKey: 'u', storage: memory() }).getSummary();
    expect(s.funnel.columns[1]).toEqual({ key: 'd1', label: 'mais de 45 d', minDays: 46, maxDays: null });
    expect(s.funnel.rows[0]).toEqual({ product: 'GTX Pro', count: 3, expectedValue: 90, cells: [{ count: 1, expectedValue: 90 }, { count: 2, expectedValue: 0 }] });
  });

  it('explicação do índice vem de GET /deals/{id} (fator, observado, referência, peso)', async () => {
    const explanation = {
      disclaimer: 'Associações no histórico; não são causas.',
      contributions: [
        { code: 'age_band', label: 'Tempo no funil: 92 dias', value: '92', direction: 'positive', impact: 0.4, factor: 'Tempo no funil', observed: '92 dias', reference: 'Prazo típico: 45 dias.' },
        { code: 'product', label: 'Produto: GTX Pro', value: 'GTX Pro', direction: 'negative', impact: 0.6 },
      ],
    };
    const { fetchImpl, calls } = fakeServer({ '/deals/ABC': () => json({ explanation }) });
    const e = await new HttpDealsApi({ fetchImpl, userKey: 'u', storage: memory() }).getDealExplanation('ABC');
    expect(calls.some((c) => c.url.endsWith('/deals/ABC'))).toBe(true);
    expect(e.disclaimer).toBe('Associações no histórico; não são causas.');
    expect(e.factors[0]).toEqual({ code: 'age_band', factor: 'Tempo no funil', observed: '92 dias', reference: 'Prazo típico: 45 dias.', direction: 'positive', impact: 0.4 });
    expect(e.factors[1]).toMatchObject({ factor: 'Produto: GTX Pro', observed: null, reference: null });
  });

  it('erros da API viram ApiError', async () => {
    const { fetchImpl } = fakeServer({
      '/meta': () => json({ error: { code: 'MODEL_NOT_READY', message: 'Sem modelo', request_id: 'r1' } }, 503),
    });
    const api = new HttpDealsApi({ fetchImpl, userKey: 'u', storage: memory() });
    await expect(api.getMeta()).rejects.toMatchObject({ status: 503, code: 'MODEL_NOT_READY', requestId: 'r1' });
    await expect(api.getMeta()).rejects.toBeInstanceOf(ApiError);
  });

  // TODO(api): adiar/encerrar não têm endpoint; o estado é local.
  it('adiar esconde o deal e desfazer devolve; adiado expira', async () => {
    const { fetchImpl } = fakeServer();
    let now = 1_000_000;
    const api = new HttpDealsApi({ fetchImpl, userKey: 'u', storage: memory(), now: () => now });
    const id = (await api.listDeals(base)).items[0].id;
    await api.applyAction({ action: 'snooze', dealIds: [id], snoozeDays: 7 });
    expect((await api.listDeals(base)).items.some((d) => d.id === id)).toBe(false);
    now += 8 * 86_400_000;
    expect((await api.listDeals(base)).items.some((d) => d.id === id)).toBe(true);
    await api.applyAction({ action: 'lost', dealIds: [id] });
    expect((await api.listDeals(base)).items.some((d) => d.id === id)).toBe(false);
    await api.undoAction([id]);
    expect((await api.listDeals(base)).items.some((d) => d.id === id)).toBe(true);
  });

  it('envia feedback no formato da API', async () => {
    const { fetchImpl, calls } = fakeServer({ '/feedback': () => json({ id: 1, created_at: '2017-12-31T00:00:00Z' }, 201) });
    const api = new HttpDealsApi({ fetchImpl, userKey: 'u', storage: memory() });
    await api.sendFeedback('ABC', 'disagree', 'stalled');
    const call = (fetchImpl as unknown as ReturnType<typeof vi.fn>).mock.calls.find((c) => String(c[0]).endsWith('/deals/ABC/feedback'))!;
    expect(JSON.parse((call[1] as RequestInit).body as string)).toEqual({ action: 'disagree', comment: 'reason:stalled' });
    expect(calls.some((c) => c.method === 'POST' && c.url.endsWith('/deals/ABC/feedback'))).toBe(true);
  });
});
