// Regras de negócio SIMULADAS para o mock. Na API real tudo isto vem do backend
// (GET /meta, /deals, /summary). Este arquivo só pode ser importado de dentro de src/api/mock.
import type {
  BandKey,
  Deal,
  DataQuality,
  DealExplanation,
  DealFilters,
  DealsPage,
  Funnel,
  ListDealsQuery,
  ListTab,
  Meta,
  PriorityLabel,
  PriorityLevelDef,
  Summary,
  TabKey,
  Thresholds,
  ViewDef,
} from '../types';

export const MOCK_THRESHOLDS: Thresholds = {
  typicalP50: 41,
  staleDays: 104,
  reviewDays: 138,
  focusScore: 80,
  followUpScore: 40,
};

export const MOCK_LOW_CONFIDENCE_BELOW = 30;

export const MOCK_PRIORITY_LEVELS: PriorityLevelDef[] = [
  { key: 'high', label: 'Alta', minScore: 80, maxScore: 100 },
  { key: 'medium', label: 'Média', minScore: 40, maxScore: 79 },
  { key: 'low', label: 'Baixa', minScore: 0, maxScore: 39 },
];

const ALL_BANDS: BandKey[] = ['focus', 'follow_up', 'low', 'stale_risk', 'review', 'prospecting'];

export const MOCK_VIEWS: ViewDef[] = [
  { key: 'focus', bands: ['focus', 'follow_up'], defaultSort: 'score' },
  { key: 'decide', bands: ['stale_risk'], defaultSort: 'score' },
  { key: 'follow', bands: ['low'], defaultSort: 'score' },
  { key: 'prospecting', bands: ['prospecting'], defaultSort: 'score' },
  { key: 'review', bands: ['review'], defaultSort: 'score' },
  { key: 'all', bands: ALL_BANDS, defaultSort: 'score' },
  { key: 'ev', bands: ALL_BANDS.filter((b) => b !== 'review'), defaultSort: 'expected_value' },
];

export const MOCK_SUGGESTED_ACTIONS: Record<BandKey, string> = {
  focus: 'Agende uma conversa com quem decide ainda esta semana.',
  follow_up: 'Mantenha o ritmo e revise na próxima semana.',
  low: 'Pouco valor esperado. Só vale o tempo se for rápido.',
  stale_risk: 'Decidir agora: este deal passou do prazo em que 90% dos deals fecham.',
  review: 'Mais antigo que qualquer deal já fechado. Encerrar ou reativar.',
  prospecting: 'Sem contato registrado. Inicie o engajamento.',
};

export function mockPriorityLabel(score: number | null): PriorityLabel | null {
  if (score === null) return null;
  const level = MOCK_PRIORITY_LEVELS.find((l) => score >= l.minScore && score <= l.maxScore);
  return level?.label ?? null;
}

export function mockMeta(showProbability: boolean, referenceDate: string): Meta {
  return {
    referenceDate,
    modelVersion: 'exemplo-0',
    showProbability,
    sampleData: true,
    thresholds: MOCK_THRESHOLDS,
    priorityLevels: MOCK_PRIORITY_LEVELS,
    views: MOCK_VIEWS,
    lowConfidenceBelowClosedDeals: MOCK_LOW_CONFIDENCE_BELOW,
    horizonDays: 30,
    calibrationUseful: false,
  };
}

/** Texto da confiança, como a API (confidence_reason). */
export function mockConfidenceReason(confidence: 'low' | 'medium' | 'high', prospecting: boolean): string {
  if (prospecting) return 'o deal ainda não tem histórico';
  if (confidence === 'low') return `o vendedor tem menos de ${MOCK_LOW_CONFIDENCE_BELOW} deals fechados`;
  return `o vendedor tem ${MOCK_LOW_CONFIDENCE_BELOW} ou mais deals fechados`;
}

/** Completude dos dados, como a API (data_quality). A conta não entra no cálculo da prioridade. */
export function mockDataQuality(account: string | null): DataQuality {
  if (account !== null) return { status: 'complete', summary: 'Todos os campos do deal estão preenchidos.', missing: [] };
  return {
    status: 'incomplete',
    summary: 'Falta informar a conta. Ela não entra no cálculo da prioridade.',
    missing: [{ field: 'account', label: 'Conta', affectsPrediction: false }],
  };
}

/** Explicação do índice, como GET /deals/{id} (explanation). */
export function explainDeal(deal: Deal): DealExplanation {
  const total = deal.reasons.reduce((t, r) => t + r.weight, 0) || 1;
  const { typicalP50, staleDays } = MOCK_THRESHOLDS;
  return {
    disclaimer: 'Associações no histórico; não são causas.',
    factors: deal.reasons.map((r) => {
      const [factor, observed] = r.long.includes(': ') ? r.long.split(': ') : [r.long, r.short];
      return {
        code: r.short,
        factor,
        observed,
        reference: factor === 'Tempo no funil' ? `Prazo típico: ${typicalP50} dias. A maioria fecha em até ${staleDays} dias.` : null,
        direction: r.direction === 'pos' ? ('positive' as const) : ('negative' as const),
        impact: r.weight / total,
      };
    }),
  };
}

const viewOf = (key: ListTab): ViewDef => MOCK_VIEWS.find((v) => v.key === key) as ViewDef;

/** Filtra e ordena como a API (GET /deals): aba, produto, prioridade, busca e ordenação. */
export function filterDeals(all: Deal[], hidden: Set<string>, f: DealFilters): Deal[] {
  const view = viewOf(f.tab);
  let list = all.filter((d) => !hidden.has(d.id) && view.bands.includes(d.band));
  if (f.product !== 'all') list = list.filter((d) => d.product === f.product);

  if (f.level !== 'all') {
    const level = MOCK_PRIORITY_LEVELS.find((l) => l.key === f.level) as PriorityLevelDef;
    list = list.filter((d) => d.score !== null && d.score >= level.minScore && d.score <= level.maxScore);
  }

  const q = f.q.trim().toLowerCase();
  if (q) list = list.filter((d) => `${d.id} ${d.product} ${d.account ?? ''}`.toLowerCase().includes(q));

  const sort = f.sort ?? view.defaultSort;
  const byEv = (a: Deal, b: Deal) => b.expectedValue - a.expectedValue;
  const sorters = {
    score: (a: Deal, b: Deal) => (b.score ?? -1) - (a.score ?? -1) || byEv(a, b),
    expected_value: byEv,
    age_days: (a: Deal, b: Deal) => (b.ageDays ?? -1) - (a.ageDays ?? -1) || byEv(a, b),
  };
  return list.slice().sort(sorters[sort]);
}

export function paginate(list: Deal[], query: Pick<ListDealsQuery, 'page' | 'pageSize'>): DealsPage {
  const pageCount = Math.max(1, Math.ceil(list.length / query.pageSize));
  const page = Math.min(pageCount, Math.max(1, query.page));
  const start = (page - 1) * query.pageSize;
  return { items: list.slice(start, start + query.pageSize), total: list.length, page, pageSize: query.pageSize, pageCount };
}

/** Totais por aba, como GET /summary (views). Deals "A revisar" não somam valor esperado. */
export function summarize(visible: Deal[]): Summary {
  const views = {} as Summary['views'];
  for (const view of MOCK_VIEWS) {
    const part = visible.filter((d) => view.bands.includes(d.band));
    const live = part.filter((d) => d.band !== 'review');
    views[view.key] = { count: part.length, expectedValue: live.reduce((t, d) => t + d.expectedValue, 0) };
  }
  return { views, funnel: funnelOf(visible) };
}

/** Heatmap do funil como GET /summary (funnel): produto x tempo no funil. */
export function funnelOf(visible: Deal[]): Funnel {
  const { typicalP50: p50, staleDays: stale, reviewDays: review } = MOCK_THRESHOLDS;
  const edges: [number, number | null][] = [[0, p50], [p50 + 1, stale], [stale + 1, review], [review + 1, null]];
  const labels = [`até ${p50} d`, `${p50 + 1}–${stale} d`, `${stale + 1}–${review} d`, `mais de ${review} d`];
  const columns = edges.map(([minDays, maxDays], i) => ({ key: `d${i}`, label: labels[i], minDays, maxDays }));
  const aged = visible.filter((d) => d.ageDays !== null && d.band !== 'prospecting');
  const rows = [...new Set(aged.map((d) => d.product))].map((product) => {
    const mine = aged.filter((d) => d.product === product);
    const cells = edges.map(([lo, hi]) => {
      const cell = mine.filter((d) => (d.ageDays as number) >= lo && (hi === null || (d.ageDays as number) <= hi));
      const live = cell.filter((d) => d.band !== 'review');
      return { count: cell.length, expectedValue: live.reduce((t, d) => t + d.expectedValue, 0) };
    });
    return {
      product,
      count: cells.reduce((t, c) => t + c.count, 0),
      expectedValue: cells.reduce((t, c) => t + c.expectedValue, 0),
      cells,
    };
  });
  rows.sort((a, b) => b.expectedValue - a.expectedValue || a.product.localeCompare(b.product));
  return { columns, rows };
}

/** "Seu dia": os maiores índices do foco da semana (prioridade Alta e Média), limitados ao tamanho do dia. */
export function todayDeals(visible: Deal[], cap: number): Deal[] {
  const week = MOCK_VIEWS.find((v) => v.key === 'focus')?.bands ?? [];
  return visible
    .filter((d) => week.includes(d.band) && d.score !== null)
    .sort((a, b) => (b.score ?? 0) - (a.score ?? 0) || b.expectedValue - a.expectedValue)
    .slice(0, cap);
}

export const MOCK_TABS: TabKey[] = ['focus', 'decide', 'follow', 'prospecting', 'review'];
