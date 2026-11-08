// Tipos de domínio usados pelo frontend (camelCase).
// O formato "no fio" (snake_case) fica isolado em HttpDealsApi.

export type TabKey = 'focus' | 'decide' | 'follow' | 'prospecting' | 'review';
/** 'all' = todos os abertos; 'ev' = todos menos "A revisar", do maior valor esperado para o menor. */
export type ListTab = TabKey | 'all' | 'ev';
/** Faixa do deal, com os mesmos nomes da API (usada só para escolher cor e rótulo). */
export type BandKey = 'focus' | 'follow_up' | 'low' | 'stale_risk' | 'review' | 'prospecting';
export type ReasonDirection = 'pos' | 'neg' | 'neu' | 'warn';
/** Mesmos nomes do parâmetro `sort` da API. */
export type SortKey = 'score' | 'expected_value' | 'age_days';
export type FeedbackKind = 'act' | 'disagree' | 'ignore';
export type DisagreeReason = 'value' | 'stalled' | 'closed' | 'other';
export type DealActionKind = 'snooze' | 'lost';
export type Confidence = 'low' | 'medium' | 'high';
/** Texto de prioridade como a API devolve (priority_level). */
export type PriorityLabel = 'Alta' | 'Média' | 'Baixa';
export type UserRole = 'seller' | 'manager' | 'revops';
/** Chaves do parâmetro `priority` da API; 'all' = sem filtro. */
export type PriorityLevel = 'all' | 'high' | 'medium' | 'low';

export interface Reason {
  short: string;
  long: string;
  direction: ReasonDirection;
  weight: number;
}

/** Completude dos dados do deal (separada da confiança da previsão). Texto pronto da API. */
export interface DataQuality {
  status: 'complete' | 'incomplete';
  summary: string;
  missing: { field: string; label: string; affectsPrediction: boolean }[];
}

/** Um fator da explicação do índice (GET /deals/{id}, explanation). Associação no histórico, não causa. */
export interface Factor {
  code: string;
  factor: string;
  observed: string | null;
  /** Com o que comparar o valor observado (prazo típico, média geral...). null quando não há referência. */
  reference: string | null;
  direction: 'positive' | 'negative';
  /** Peso relativo (0–1; a soma de todos os fatores é 1). */
  impact: number;
}

export interface DealExplanation {
  factors: Factor[];
  disclaimer: string;
}

export interface Deal {
  id: string;
  /** Aba (campo `view` da API). */
  tab: TabKey;
  band: BandKey;
  product: string;
  stage: string;
  /** Dias no funil; null quando o deal ainda não tem data (Prospecting). */
  ageDays: number | null;
  /** Índice de prioridade 0–100; null = sem prioridade (ex.: "A revisar", Prospecting). */
  score: number | null;
  /** Texto de prioridade vindo da API; null quando não há índice. */
  priorityLevel: PriorityLabel | null;
  /** null quando a API não expõe a probabilidade (show_probability=false). */
  probability: number | null;
  price: number;
  expectedValue: number;
  account: string | null;
  /** Ação sugerida, texto pronto da API. */
  suggestedAction: string;
  confidence: Confidence;
  /** Por que a confiança é baixa, texto da API (null quando não há motivo). */
  confidenceReason: string | null;
  /** null quando a API não informa (versão antiga). */
  dataQuality: DataQuality | null;
  /** Já ordenadas da mais para a menos relevante. */
  reasons: Reason[];
}

export interface CurrentUser {
  userKey: string;
  name: string;
  role: UserRole;
  region: string;
}

/** Limiares do modelo, como vêm de GET /meta (thresholds). */
export interface Thresholds {
  typicalP50: number;
  staleDays: number;
  reviewDays: number;
  focusScore: number;
  followUpScore: number;
}

export interface PriorityLevelDef {
  key: Exclude<PriorityLevel, 'all'>;
  label: PriorityLabel;
  minScore: number;
  maxScore: number;
}

export interface ViewDef {
  key: ListTab;
  bands: BandKey[];
  defaultSort: SortKey;
}

export interface Meta {
  /** YYYY-MM-DD */
  referenceDate: string;
  modelVersion: string;
  showProbability: boolean;
  /** true quando os dados são de exemplo (mock). */
  sampleData: boolean;
  thresholds: Thresholds;
  priorityLevels: PriorityLevelDef[];
  views: ViewDef[];
  /** Vendedor com menos deals fechados que isso tem confiança baixa. */
  lowConfidenceBelowClosedDeals: number;
  /** Horizonte do modelo em dias (receita esperada nos próximos N dias); null em versões antigas da API. */
  horizonDays: number | null;
  /** A chance em % só é confiável quando a calibração do modelo provou valor; null em versões antigas. */
  calibrationUseful: boolean | null;
}

export interface ListFilters {
  products: string[];
}

export interface ViewTotals {
  count: number;
  expectedValue: number;
}

/** Faixa de dias do heatmap do funil. Os limites vêm da API (a partir dos limiares do modelo). */
export interface FunnelColumn {
  key: string;
  label: string;
  minDays: number;
  /** null = sem limite superior. */
  maxDays: number | null;
}

export interface FunnelCell {
  count: number;
  expectedValue: number;
}

export interface FunnelRow {
  product: string;
  count: number;
  expectedValue: number;
  /** Uma célula por coluna, na mesma ordem. */
  cells: FunnelCell[];
}

/** Heatmap do funil (GET /summary, funnel): produto x tempo no funil. Prospecção não entra (sem data). */
export interface Funnel {
  columns: FunnelColumn[];
  rows: FunnelRow[];
}

/** Totais por aba e heatmap do funil, como vêm de GET /summary. */
export interface Summary {
  views: Record<ListTab, ViewTotals>;
  funnel: Funnel;
}

export interface DealFilters {
  tab: ListTab;
  /** 'all' = sem filtro */
  product: string;
  q: string;
  /** null = padrão da aba (a API decide). */
  sort: SortKey | null;
  level: PriorityLevel;
}

export interface ListDealsQuery extends DealFilters {
  page: number;
  pageSize: number;
}

export interface DealsPage {
  items: Deal[];
  total: number;
  page: number;
  pageSize: number;
  pageCount: number;
}

export interface TodayQuery {
  cap: number;
}

export interface DealActionRequest {
  action: DealActionKind;
  dealIds: string[];
  snoozeDays?: number;
}

export interface ActionResult {
  affectedIds: string[];
}

export interface FeedbackEntry {
  kind: FeedbackKind;
  reason: DisagreeReason | null;
  /** ISO 8601 */
  createdAt: string;
}
