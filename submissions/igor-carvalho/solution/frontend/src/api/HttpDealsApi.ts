import type { DealsApi } from './DealsApi';
import type {
  ActionResult,
  BandKey,
  Confidence,
  CurrentUser,
  Deal,
  DealActionRequest,
  DealsPage,
  DisagreeReason,
  FeedbackEntry,
  FeedbackKind,
  ListDealsQuery,
  ListFilters,
  ListTab,
  Meta,
  PriorityLabel,
  Reason,
  ReasonDirection,
  SortKey,
  DealExplanation,
  Funnel,
  Summary,
  TabKey,
  TodayQuery,
  UserRole,
} from './types';
import { ApiError } from './errors';
import { browserStore, readJson, writeJson, type KeyValueStore } from '../lib/storage';

// O frontend NÃO decide nada de negócio: abas, faixas de score, prazos, confiança, textos de ação,
// filtros, ordenação e totais vêm da API (GET /meta, /deals, /summary). Aqui só se traduz formato.

// ---- Formato "no fio" da API (backend/src/lead_api/schemas.py) ----

interface WireReason {
  code: string;
  label: string;
  value: string | null;
  direction: 'positive' | 'negative';
  impact: number;
}

export interface DealDto {
  opportunity_id: string;
  stage: 'Engaging' | 'Prospecting';
  product: string;
  account: string | null;
  list_price: number;
  age_days: number | null;
  score: number | null;
  priority_level: PriorityLabel | null;
  band: BandKey;
  view: TabKey;
  expected_value: number;
  p_win: number | null;
  confidence: Confidence;
  confidence_reason: string | null;
  data_quality?: {
    status: 'complete' | 'incomplete';
    summary: string;
    missing: { field: string; label: string; affects_prediction: boolean }[];
  };
  suggested_action: string;
  reasons: WireReason[];
}

interface FunnelDto {
  columns: { key: string; label: string; min_days: number; max_days: number | null }[];
  rows: { product: string; count: number; expected_value: number; cells: { count: number; expected_value: number }[] }[];
}

function mapFunnel(dto: FunnelDto | undefined): Funnel {
  if (!dto) return { columns: [], rows: [] };
  return {
    columns: dto.columns.map((c) => ({ key: c.key, label: c.label, minDays: c.min_days, maxDays: c.max_days })),
    rows: dto.rows.map((r) => ({
      product: r.product,
      count: r.count,
      expectedValue: r.expected_value,
      cells: r.cells.map((c) => ({ count: c.count, expectedValue: c.expected_value })),
    })),
  };
}

interface ViewSummaryDto {
  count: number;
  expected_value: number;
}

interface ErrorBody {
  error?: { code?: string; message?: string; request_id?: string };
}

function mapReason(r: WireReason): Reason {
  // Só apresentação: "Tempo no funil" negativo aparece como alerta, não como fator ruim comum.
  const direction: ReasonDirection = r.direction === 'positive' ? 'pos' : r.code === 'age_band' ? 'warn' : 'neg';
  return { short: r.label, long: r.label, direction, weight: r.impact };
}

export function mapDeal(dto: DealDto): Deal {
  return {
    id: dto.opportunity_id,
    tab: dto.view,
    band: dto.band,
    product: dto.product,
    stage: dto.stage,
    ageDays: dto.age_days,
    score: dto.score,
    priorityLevel: dto.priority_level,
    probability: dto.p_win,
    price: dto.list_price,
    expectedValue: dto.expected_value,
    account: dto.account,
    suggestedAction: dto.suggested_action,
    confidence: dto.confidence,
    confidenceReason: dto.confidence_reason,
    dataQuality: dto.data_quality
      ? {
          status: dto.data_quality.status,
          summary: dto.data_quality.summary,
          missing: dto.data_quality.missing.map((m) => ({ field: m.field, label: m.label, affectsPrediction: m.affects_prediction })),
        }
      : null,
    reasons: dto.reasons.map(mapReason),
  };
}

// Nomes dos parâmetros de ordenação já são os da API (SortKey = score | expected_value | age_days).
export const SORT_PARAM: Record<SortKey, string> = { score: 'score', expected_value: 'expected_value', age_days: 'age_days' };

/** Parâmetros de GET /deals para uma aba/filtro. O servidor filtra, ordena e pagina. */
export function buildListQuery(q: ListDealsQuery): Record<string, string | number | undefined> {
  return {
    view: q.tab,
    priority: q.level === 'all' ? undefined : q.level,
    product: q.product === 'all' ? undefined : q.product,
    q: q.q.trim() || undefined,
    sort: q.sort === null ? undefined : SORT_PARAM[q.sort], // sem sort: a API usa o padrão da aba
    order: 'desc',
    page: q.page,
    page_size: q.pageSize,
  };
}

// ---- Feedback: ações do frontend <-> ações da API (worked | disagree | ignore + comentário) ----

export function encodeFeedback(kind: FeedbackKind, reason: DisagreeReason | null): { action: string; comment: string | null } {
  if (kind === 'act') return { action: 'worked', comment: null };
  if (kind === 'disagree') return { action: 'disagree', comment: reason ? `reason:${reason}` : null };
  return { action: 'ignore', comment: null };
}

export function decodeFeedback(action: string, comment: string | null): { kind: FeedbackKind; reason: DisagreeReason | null } {
  if (action === 'worked') return { kind: 'act', reason: null };
  if (action === 'ignore') return { kind: 'ignore', reason: null };
  const reason = comment?.startsWith('reason:') ? (comment.slice(7) as DisagreeReason) : null;
  return { kind: 'disagree', reason };
}

// ---- Cliente ----

export interface HttpOptions {
  baseUrl?: string;
  fetchImpl?: typeof fetch;
  /** Token já pronto (ex.: SSO). Se ausente e houver userKey, o cliente faz login sozinho. */
  getToken?: () => string | null;
  /** user_key para POST /auth/login (MVP da API). */
  userKey?: string;
  storage?: KeyValueStore | null;
  now?: () => number;
}

interface RequestOptions {
  query?: Record<string, string | number | undefined>;
  body?: unknown;
  auth?: boolean;
}

export const HTTP_STORAGE_KEY = 'g4.http.hidden.v2';
const MS_PER_DAY = 86_400_000;

// TODO(api): "Adiar" e "Encerrar como perdido" ainda não têm endpoint (o esquema do banco está
// congelado). Enquanto isso o estado fica só neste navegador. Não é regra do produto.
interface LocalHide {
  /** até quando fica fora da lista (ms); null = sem prazo */
  until: number | null;
  view: TabKey;
  expectedValue: number;
}

export class HttpDealsApi implements DealsApi {
  private readonly baseUrl: string;
  private readonly fetchImpl: typeof fetch;
  private readonly getToken: (() => string | null) | null;
  private readonly userKey: string | null;
  private readonly storage: KeyValueStore | null;
  private readonly now: () => number;
  private token: string | null = null;
  private loggingIn: Promise<string> | null = null;
  private hidden: Record<string, LocalHide>;
  /** Último view/valor conhecido de cada deal visto, para o ajuste local de totais. */
  private seen = new Map<string, { view: TabKey; expectedValue: number }>();

  constructor(options: HttpOptions = {}) {
    this.baseUrl = (options.baseUrl ?? '/api/v1').replace(/\/$/, '');
    this.fetchImpl = options.fetchImpl ?? ((...args) => fetch(...args));
    this.getToken = options.getToken ?? null;
    this.userKey = options.userKey ?? null;
    this.storage = options.storage === undefined ? browserStore() : options.storage;
    this.now = options.now ?? (() => Date.now());
    this.hidden = readJson<Record<string, LocalHide>>(this.storage, HTTP_STORAGE_KEY, {});
  }

  // ---- HTTP ----

  private async login(): Promise<string> {
    const dto = await this.request<{ access_token: string }>('POST', '/auth/login', {
      body: { user_key: this.userKey },
      auth: false,
    });
    this.token = dto.access_token;
    return this.token;
  }

  private async bearer(): Promise<string | null> {
    if (this.getToken) return this.getToken();
    if (!this.userKey) return null;
    if (this.token) return this.token;
    // Chamadas em paralelo esperam o mesmo login, em vez de fazer um cada.
    this.loggingIn ??= this.login().finally(() => {
      this.loggingIn = null;
    });
    return this.loggingIn;
  }

  private async request<T>(method: string, path: string, options: RequestOptions = {}, retried = false): Promise<T> {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(options.query ?? {})) {
      if (value !== undefined && value !== '') params.set(key, String(value));
    }
    const qs = params.toString();
    const headers: Record<string, string> = { Accept: 'application/json' };
    if (options.body !== undefined) headers['Content-Type'] = 'application/json';
    if (options.auth !== false) {
      const token = await this.bearer();
      if (token) headers.Authorization = `Bearer ${token}`;
    }

    const response = await this.fetchImpl(`${this.baseUrl}${path}${qs ? `?${qs}` : ''}`, {
      method,
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    });

    if (response.status === 401 && options.auth !== false && this.userKey && !this.getToken && !retried) {
      this.token = null; // token expirado: entra de novo uma vez
      return this.request<T>(method, path, options, true);
    }
    if (!response.ok) {
      let body: ErrorBody = {};
      try {
        body = (await response.json()) as ErrorBody;
      } catch {
        /* corpo vazio ou não-JSON */
      }
      throw new ApiError(
        response.status,
        body.error?.code ?? 'HTTP_ERROR',
        body.error?.message ?? `Erro ${response.status} ao falar com o servidor.`,
        body.error?.request_id ?? null,
      );
    }
    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
  }

  // ---- Adiar / perdido (local, ver TODO acima) ----

  private hiddenIds(): Set<string> {
    const now = this.now();
    return new Set(Object.keys(this.hidden).filter((id) => this.hidden[id].until === null || (this.hidden[id].until as number) > now));
  }

  private persist(): void {
    writeJson(this.storage, HTTP_STORAGE_KEY, this.hidden);
  }

  private remember(deals: Deal[]): void {
    deals.forEach((d) => this.seen.set(d.id, { view: d.tab, expectedValue: d.expectedValue }));
  }

  private async fetchDeals(query: Record<string, string | number | undefined>): Promise<{ items: Deal[]; total: number; page: number; pageSize: number }> {
    const dto = await this.request<{ items: DealDto[]; total: number; page: number; page_size: number }>('GET', '/deals', { query });
    const items = dto.items.map(mapDeal);
    this.remember(items);
    return { items, total: dto.total, page: dto.page, pageSize: dto.page_size };
  }

  // ---- DealsApi ----

  async getCurrentUser(): Promise<CurrentUser> {
    const dto = await this.request<{ user_key: string; full_name: string; role: UserRole; regional_office: string | null }>('GET', '/me');
    return { userKey: dto.user_key, name: dto.full_name, role: dto.role, region: dto.regional_office ?? '' };
  }

  async getMeta(): Promise<Meta> {
    const dto = await this.request<{
      reference_date: string;
      model_version: string;
      show_probability: boolean;
      thresholds: { typical_p50: number; stale_days: number; review_days: number; focus_score: number; follow_up_score: number };
      priority_levels: { key: 'high' | 'medium' | 'low'; label: PriorityLabel; min_score: number; max_score: number }[];
      views: { key: ListTab; bands: BandKey[]; default_sort: SortKey }[];
      low_confidence_below_closed_deals: number;
      horizon_days?: number | null;
      calibration_useful?: boolean | null;
    }>('GET', '/meta');
    const t = dto.thresholds;
    return {
      referenceDate: dto.reference_date,
      modelVersion: dto.model_version,
      showProbability: dto.show_probability,
      sampleData: false,
      thresholds: {
        typicalP50: t.typical_p50,
        staleDays: t.stale_days,
        reviewDays: t.review_days,
        focusScore: t.focus_score,
        followUpScore: t.follow_up_score,
      },
      priorityLevels: dto.priority_levels.map((l) => ({ key: l.key, label: l.label, minScore: l.min_score, maxScore: l.max_score })),
      views: dto.views.map((v) => ({ key: v.key, bands: v.bands, defaultSort: v.default_sort })),
      lowConfidenceBelowClosedDeals: dto.low_confidence_below_closed_deals,
      horizonDays: dto.horizon_days ?? null,
      calibrationUseful: dto.calibration_useful ?? null,
    };
  }

  async getFilters(): Promise<ListFilters> {
    const dto = await this.request<{ products: string[] }>('GET', '/filters');
    return { products: dto.products };
  }

  async getSummary(): Promise<Summary> {
    const dto = await this.request<{ views: Record<ListTab, ViewSummaryDto>; funnel?: FunnelDto }>('GET', '/summary');
    const views = {} as Summary['views'];
    for (const [key, v] of Object.entries(dto.views) as [ListTab, ViewSummaryDto][]) {
      views[key] = { count: v.count, expectedValue: v.expected_value };
    }
    // TODO(api): tira do total o que foi adiado/encerrado só neste navegador.
    const now = this.now();
    for (const [id, hide] of Object.entries(this.hidden)) {
      if (hide.until !== null && hide.until <= now) continue;
      for (const key of Object.keys(views) as ListTab[]) {
        // O deal só entra nas abas que o contêm: a aba própria, "all" e (se não for "A revisar") "ev".
        const inView = key === hide.view || key === 'all' || (key === 'ev' && hide.view !== 'review');
        if (!inView || !views[key]) continue;
        views[key].count = Math.max(0, views[key].count - 1);
        if (hide.view !== 'review') views[key].expectedValue = Math.max(0, views[key].expectedValue - hide.expectedValue);
      }
      void id;
    }
    // TODO(api): o heatmap não desconta o que foi adiado/encerrado só neste navegador (a API não conhece esses deals).
    return { views, funnel: mapFunnel(dto.funnel) };
  }

  async listDeals(query: ListDealsQuery): Promise<DealsPage> {
    const page = await this.fetchDeals(buildListQuery(query));
    // TODO(api): esconde o que foi adiado/encerrado só neste navegador.
    const hidden = this.hiddenIds();
    const items = page.items.filter((d) => !hidden.has(d.id));
    const total = Math.max(0, page.total - (page.items.length - items.length));
    return { items, total, page: page.page, pageSize: page.pageSize, pageCount: Math.max(1, Math.ceil(total / page.pageSize)) };
  }

  /**
   * "Seu dia".
   * TODO(api): esta regra (maiores índices do foco da semana, limitada) deveria ser uma rota da API.
   * Hoje usa GET /deals com view=focus (a semana) ordenado por score: o dia é o topo da semana.
   */
  async listTodayDeals(query: TodayQuery): Promise<Deal[]> {
    const hidden = this.hiddenIds();
    const page = await this.fetchDeals({
      view: 'focus',
      sort: 'score',
      order: 'desc',
      page: 1,
      page_size: Math.min(200, query.cap + hidden.size),
    });
    return page.items.filter((d) => !hidden.has(d.id)).slice(0, query.cap);
  }

  async applyAction(request: DealActionRequest): Promise<ActionResult> {
    const affectedIds = request.dealIds.filter((id) => this.seen.has(id));
    const until = request.action === 'snooze' && request.snoozeDays ? this.now() + request.snoozeDays * MS_PER_DAY : null;
    affectedIds.forEach((id) => {
      const known = this.seen.get(id) as { view: TabKey; expectedValue: number };
      this.hidden[id] = { until, view: known.view, expectedValue: known.expectedValue };
    });
    this.persist();
    return { affectedIds };
  }

  async undoAction(dealIds: string[]): Promise<ActionResult> {
    const affectedIds = dealIds.filter((id) => id in this.hidden);
    affectedIds.forEach((id) => delete this.hidden[id]);
    this.persist();
    return { affectedIds };
  }

  async getDealExplanation(dealId: string): Promise<DealExplanation> {
    const dto = await this.request<{
      explanation: {
        disclaimer: string;
        contributions: {
          code: string;
          factor?: string;
          label: string;
          observed?: string | null;
          reference?: string | null;
          direction: 'positive' | 'negative';
          impact: number;
        }[];
      };
    }>('GET', `/deals/${encodeURIComponent(dealId)}`);
    return {
      disclaimer: dto.explanation.disclaimer,
      factors: dto.explanation.contributions.map((c) => ({
        code: c.code,
        factor: c.factor ?? c.label,
        observed: c.observed ?? null,
        reference: c.reference ?? null,
        direction: c.direction,
        impact: c.impact,
      })),
    };
  }

  async sendFeedback(dealId: string, kind: FeedbackKind, reason: DisagreeReason | null = null): Promise<void> {
    await this.request('POST', `/deals/${encodeURIComponent(dealId)}/feedback`, { body: encodeFeedback(kind, reason) });
  }

  async listFeedback(dealId: string): Promise<FeedbackEntry[]> {
    const dto = await this.request<{ items: { action: string; comment: string | null; created_at: string }[] }>(
      'GET',
      `/deals/${encodeURIComponent(dealId)}/feedback`,
    );
    return dto.items.map((item) => ({ ...decodeFeedback(item.action, item.comment), createdAt: item.created_at }));
  }

  async reset(): Promise<void> {
    this.hidden = {};
    this.persist();
  }
}
