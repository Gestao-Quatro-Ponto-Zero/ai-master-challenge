// Teste contra a API de verdade. Só roda com G4_API_URL definido, por exemplo:
//   G4_API_URL=http://localhost:8000 npm run test:integration
import { describe, expect, it } from 'vitest';
import { HttpDealsApi } from './HttpDealsApi';
import type { ListDealsQuery } from './types';

const url = process.env.G4_API_URL;
const userKey = process.env.G4_API_USER ?? 'vicki-laflamme';

describe.skipIf(!url)('API real', () => {
  const api = () => new HttpDealsApi({ baseUrl: `${url}/api/v1`, userKey, storage: null });
  const q = (o: Partial<ListDealsQuery> = {}): ListDealsQuery => ({
    tab: 'all', product: 'all', q: '', sort: null, level: 'all', page: 1, pageSize: 100, ...o,
  });

  it('usuário e meta (limiares, níveis e abas)', async () => {
    const a = api();
    const me = await a.getCurrentUser();
    expect(me.userKey).toBe(userKey);
    expect(me.role).toBe('seller');
    const meta = await a.getMeta();
    expect(meta.referenceDate).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(meta.thresholds.reviewDays).toBeGreaterThan(meta.thresholds.staleDays);
    expect(meta.priorityLevels.length).toBe(3);
    expect(meta.views.map((v) => v.key)).toEqual(expect.arrayContaining(['focus', 'decide', 'follow', 'prospecting', 'review', 'all', 'ev']));
  });

  it('totais de /summary batem com a lista de cada aba', async () => {
    const a = api();
    const s = await a.getSummary();
    for (const tab of ['focus', 'decide', 'follow', 'review', 'all', 'ev'] as const) {
      const page = await a.listDeals(q({ tab, pageSize: 1 }));
      expect(page.total, tab).toBe(s.views[tab].count);
    }
  });

  it('priority_level e view de cada deal batem com /meta e com a aba pedida', async () => {
    const a = api();
    const meta = await a.getMeta();
    const bandsOf = new Map(meta.views.map((v) => [v.key, v.bands]));
    for (const tab of ['focus', 'decide', 'follow', 'review'] as const) {
      const page = await a.listDeals(q({ tab }));
      for (const d of page.items) {
        expect(d.tab, d.id).toBe(tab);
        expect(bandsOf.get(tab), d.id).toContain(d.band);
        const level = meta.priorityLevels.find((l) => d.score !== null && d.score >= l.minScore && d.score <= l.maxScore);
        expect(d.priorityLevel, d.id).toBe(level?.label ?? null);
      }
    }
  });

  it('filtro de prioridade e ordenação são feitos pela API', async () => {
    const a = api();
    const high = await a.listDeals(q({ level: 'high' }));
    const wrong = high.items.filter((d) => d.priorityLevel !== 'Alta').map((d) => `${d.id}: score=${d.score} priority_level=${d.priorityLevel} view=${d.tab}`);
    expect(wrong).toEqual([]);
    expect(high.items.length).toBeGreaterThan(0);
    const ev = (await a.listDeals(q({ tab: 'ev' }))).items.map((d) => d.expectedValue);
    expect(ev, 'view=ev deve vir por valor esperado decrescente').toEqual([...ev].sort((x, y) => y - x));
  });

  it('seu dia respeita o limite e não traz "A revisar"', async () => {
    const today = await api().listTodayDeals({ cap: 5 });
    expect(today.length).toBeLessThanOrEqual(5);
    expect(today.every((d) => d.tab !== 'review' && d.score !== null)).toBe(true);
    // O dia sai da semana: todo deal do dia está no foco da semana, e a semana é maior que o dia.
    const week = await api().listDeals(q({ tab: 'focus', pageSize: 100 }));
    const weekIds = new Set(week.items.map((d) => d.id));
    expect(today.every((d) => weekIds.has(d.id))).toBe(true);
    expect(week.total).toBeGreaterThanOrEqual(today.length);
  });

  it('feedback é gravado e lido de volta', async () => {
    const a = api();
    const id = (await a.listDeals(q())).items[0].id;
    await a.sendFeedback(id, 'disagree', 'value');
    const history = await a.listFeedback(id);
    expect(history[0]).toMatchObject({ kind: 'disagree', reason: 'value' });
  });

  it('detalhe explica cada fator e a probabilidade segue o /meta', async () => {
    const a = api();
    const meta = await a.getMeta();
    const page = await a.listDeals(q({ tab: 'ev', sort: 'score', pageSize: 5 }));
    expect(page.items.length).toBeGreaterThan(0);
    let referenced = false;
    for (const deal of page.items) {
      expect(deal.dataQuality, deal.id).not.toBeNull();
      expect(deal.confidenceReason, deal.id).toBeTruthy();
      expect(deal.probability !== null, deal.id).toBe(meta.showProbability);
      const e = await a.getDealExplanation(deal.id);
      expect(e.disclaimer).toBeTruthy();
      for (const f of e.factors) {
        expect(f.factor).toBeTruthy();
        expect(f.impact).toBeGreaterThanOrEqual(0);
        referenced = referenced || f.reference !== null;
      }
    }
    expect(referenced).toBe(true);
  });

  it('heatmap do funil: faixas dos limiares e soma igual aos deals com data', async () => {
    const a = api();
    const [meta, summary] = await Promise.all([a.getMeta(), a.getSummary()]);
    const { funnel } = summary;
    expect(funnel.columns).toHaveLength(4);
    expect(funnel.columns[0].maxDays).toBe(meta.thresholds.typicalP50);
    expect(funnel.columns[2].maxDays).toBe(meta.thresholds.reviewDays);
    expect(funnel.columns[3].maxDays).toBeNull();
    const total = funnel.rows.reduce((t, r) => t + r.count, 0);
    let withDate = 0;
    for (let page = 1; ; page++) {
      const res = await a.listDeals(q({ tab: 'all', page, pageSize: 100 }));
      withDate += res.items.filter((d) => d.ageDays !== null && d.band !== 'prospecting').length;
      if (page >= res.pageCount) break;
    }
    expect(total).toBe(withDate);
  });
});
