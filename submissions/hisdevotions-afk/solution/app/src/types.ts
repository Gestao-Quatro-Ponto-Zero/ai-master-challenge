// Formato do data.json gerado por engine/scoring.py.

export type Bucket = "fechar" | "decidir" | "avancar" | "prospectar";
export type Stage = "Prospecting" | "Engaging" | "Won" | "Lost";

export interface Reason {
  kind: "+" | "-" | "i" | "!";
  text: string;
}

/** Outro vendedor fechou o mesmo produto nesta conta depois do deal abrir. */
export interface Conflict {
  agent: string;
  days_ago: number;
  value: number;
}

export interface Deal {
  id: string;
  agent: string;
  manager: string;
  region: string;
  product: string;
  series: string;
  price: number;
  account: string | null;
  stage: Stage;
  engage: string | null;
  close: string | null;
  close_value: number | null;
}

/** Deal aberto (Prospecting/Engaging), já pontuado pelo motor. */
export interface OpenDeal extends Deal {
  age: number | null;
  bucket: Bucket;
  win_prob: number | null;
  close_soon: number | null;
  ev: number;
  ev_soon: number;
  /** Chance de ganhar em até horizon_days, 0–100. null = fora do modelo (zumbi ou prospecção). */
  score: number | null;
  /** Faixa do score contra o melhor score possível na base (meta.peak_score). */
  tier: "alta" | "media" | "baixa" | null;
  reasons: Reason[];
  action: string;
  /** Só preenchido na fila "decidir": sugestão de qual dos dois botões apertar
      (não é previsão de resultado — zumbi ainda não tem outcome conhecido). */
  suggested_action: "encerrar" | "confirmar" | null;
  /** Vazio quando não há outro vendedor no mesmo produto/conta. */
  conflicts?: Conflict[];
}

export interface Meta {
  reference_date: string;
  horizon_days: number;
  base_rate: number;
  max_cycle: number;
  window_start: number;
  /** Idade com a maior chance de ganhar em 30 dias, e essa chance (0–100). */
  peak_age: number;
  peak_score: number;
  late_start: number;
  closed_deals: number;
  data_fixes: string[];
}

export interface CurvePoint {
  age: number;
  n: number;
  win: number;
  close_soon: number;
  win_soon: number;
}

export interface SignificanceTest {
  feature: string;
  groups: number;
  p_value: number;
  used: boolean;
  note: string;
}

export interface Agent {
  name: string;
  manager: string;
  region: string;
  closed: number;
  won: number;
  win_rate: number | null;
  ci_low: number;
  ci_high: number;
  verdict: string;
  revenue_won: number;
  avg_ticket: number | null;
  has_deals: boolean;
}

export interface Account {
  account: string;
  sector: string;
  year_established: string;
  revenue: string;
  employees: string;
  office_location: string;
  subsidiary_of: string;
}

export interface Quality {
  open_total: number;
  missing_account: number;
  missing_account_value: number;
  stalled: number;
  stalled_value: number;
  conflicts: number;
  conflicts_value: number;
  duplicate_pairs: number;
  duplicate_deals: number;
  product_fixed: number;
  won_without_value: number;
  close_before_engage: number;
  unknown_account: number;
}

export interface BacktestMetrics {
  deals: number;
  wins: number;
  revenue: number;
  capture: number;
  zombies: number;
}

export interface BacktestStrategy {
  name: string;
  auc: number;
  top: BacktestMetrics;
  seller: { deals: number; wins: number; revenue: number };
}

export interface BacktestForecast {
  predicted: number;
  naive: number;
  actual: number;
  predicted_error: number | null;
  naive_error: number | null;
}

export interface BacktestRun {
  cutoff: string;
  candidates: number;
  known: number;
  won: number;
  base_rate: number;
  total_revenue: number;
  strategies: BacktestStrategy[];
  forecast: BacktestForecast;
}

export interface BacktestSummary {
  name: string;
  auc: number;
  top_revenue: number;
  top_wins: number;
  top_deals: number;
  capture: number;
  min_capture: number;
  max_capture: number;
  seller_revenue: number;
  seller_wins: number;
  zombies: number;
}

export interface Backtest {
  horizon_days: number;
  top_fraction: number;
  top_per_seller: number;
  cutoffs: string[];
  note: string;
  forecast: BacktestForecast;
  summary: BacktestSummary[];
  runs: BacktestRun[];
}

export interface RawData {
  meta: Meta;
  curve: CurvePoint[];
  significance: SignificanceTest[];
  agents: Agent[];
  quality: Quality;
  backtest: Backtest;
  accounts: Account[];
  deals: (Deal | OpenDeal)[];
}
