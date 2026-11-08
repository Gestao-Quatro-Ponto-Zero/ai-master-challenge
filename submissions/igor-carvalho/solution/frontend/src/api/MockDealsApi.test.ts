import { describe, expect, it } from 'vitest';
import { MockDealsApi } from './mock/MockDealsApi';
import { ApiError } from './errors';
import type { ListDealsQuery } from './types';

const memory = () => {
  const m = new Map<string, string>();
  return { getItem: (k: string) => m.get(k) ?? null, setItem: (k: string, v: string) => void m.set(k, v), removeItem: (k: string) => void m.delete(k) };
};
const make = () => new MockDealsApi({ latencyMs: 0, storage: memory() });
const q = (o: Partial<ListDealsQuery> = {}): ListDealsQuery => ({
  tab: 'all', product: 'all', q: '', sort: null, level: 'all', page: 1, pageSize: 50, ...o,
});

describe('MockDealsApi', () => {
  it('summary counts match the rows', async () => {
    const api = make();
    const s = await api.getSummary();
    const all = await api.listDeals(q());
    expect(s.views.all.count).toBe(all.total);
    const v = s.views;
    expect(v.focus.count + v.decide.count + v.follow.count + v.prospecting.count + v.review.count).toBe(all.total);
    expect(v.ev.count).toBe(all.total - v.review.count);
  });
  it('filters by tab and keeps prospecting without score', async () => {
    const api = make();
    const p = await api.listDeals(q({ tab: 'prospecting' }));
    expect(p.items.length).toBeGreaterThan(0);
    expect(p.items.every((d) => d.score === null)).toBe(true);
  });
  it('ev tab excludes review', async () => {
    const api = make();
    const ev = await api.listDeals(q({ tab: 'ev' }));
    expect(ev.items.some((d) => d.tab === 'review')).toBe(false);
  });
  it('devolve os mesmos campos da API: view, priority_level, suggested_action, confidence_reason', async () => {
    const api = make();
    const meta = await api.getMeta();
    expect(meta.priorityLevels.map((l) => l.key)).toEqual(['high', 'medium', 'low']);
    expect(meta.views.map((x) => x.key)).toContain('ev');
    const labels = new Set(meta.priorityLevels.map((l) => l.label));
    for (const d of (await api.listDeals(q())).items) {
      expect(d.suggestedAction.length).toBeGreaterThan(0);
      expect(d.score === null ? d.priorityLevel === null : labels.has(d.priorityLevel!)).toBe(true);
      if (d.confidence === 'low') expect(d.confidenceReason).toBeTruthy();
    }
  });
  it('filtra por nível de prioridade e ordena como a API', async () => {
    const api = make();
    const high = await api.listDeals(q({ level: 'high' }));
    expect(high.items.length).toBeGreaterThan(0);
    expect(high.items.every((d) => d.priorityLevel === 'Alta')).toBe(true);
    const ev = (await api.listDeals(q({ tab: 'ev' }))).items.map((d) => d.expectedValue);
    expect(ev).toEqual([...ev].sort((a, b) => b - a)); // padrão da aba ev = valor esperado
  });
  it('searches by id', async () => {
    const api = make();
    const first = (await api.listDeals(q())).items[0];
    const r = await api.listDeals(q({ q: first.id.toLowerCase() }));
    expect(r.items.map((d) => d.id)).toContain(first.id);
  });
  it('paginates and clamps the page', async () => {
    const api = make();
    const r = await api.listDeals(q({ pageSize: 5, page: 99 }));
    expect(r.page).toBe(r.pageCount);
    expect(r.items.length).toBeGreaterThan(0);
  });
  it('hides a snoozed deal and restores it on undo', async () => {
    const api = make();
    const id = (await api.listDeals(q({ tab: 'review' }))).items[0].id;
    await api.applyAction({ action: 'snooze', dealIds: [id], snoozeDays: 7 });
    expect((await api.listDeals(q())).items.some((d) => d.id === id)).toBe(false);
    await api.undoAction([id]);
    expect((await api.listDeals(q())).items.some((d) => d.id === id)).toBe(true);
  });
  it('today respects the cap and excludes review/prospecting', async () => {
    const api = make();
    const t = await api.listTodayDeals({ cap: 3 });
    expect(t.length).toBeLessThanOrEqual(3);
    expect(t.every((d) => d.tab !== 'review' && d.tab !== 'prospecting')).toBe(true);
  });
  it('stores feedback and rejects unknown deals', async () => {
    const api = make();
    const id = (await api.listDeals(q())).items[0].id;
    await api.sendFeedback(id, 'disagree', 'value');
    const h = await api.listFeedback(id);
    expect(h[0]).toMatchObject({ kind: 'disagree', reason: 'value' });
    await expect(api.sendFeedback('NOPE', 'act')).rejects.toBeInstanceOf(ApiError);
  });
});
