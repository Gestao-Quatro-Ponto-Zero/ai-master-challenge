import type {
  ActionResult,
  CurrentUser,
  Deal,
  DealActionRequest,
  DealExplanation,
  DealsPage,
  DisagreeReason,
  FeedbackEntry,
  FeedbackKind,
  ListDealsQuery,
  ListFilters,
  Meta,
  Summary,
  TodayQuery,
} from './types';

/**
 * Contrato que a interface usa para falar com o backend.
 * Há duas implementações: MockDealsApi (navegador) e HttpDealsApi (FastAPI).
 */
export interface DealsApi {
  getCurrentUser(): Promise<CurrentUser>;
  getMeta(): Promise<Meta>;
  getSummary(): Promise<Summary>;
  getFilters(): Promise<ListFilters>;
  listDeals(query: ListDealsQuery): Promise<DealsPage>;
  /** Explicação do índice, fator por fator (valor observado, referência e peso). */
  getDealExplanation(dealId: string): Promise<DealExplanation>;
  listTodayDeals(query: TodayQuery): Promise<Deal[]>;
  applyAction(request: DealActionRequest): Promise<ActionResult>;
  undoAction(dealIds: string[]): Promise<ActionResult>;
  sendFeedback(dealId: string, kind: FeedbackKind, reason?: DisagreeReason | null): Promise<void>;
  listFeedback(dealId: string): Promise<FeedbackEntry[]>;
  /** Só o mock implementa: volta os dados de exemplo ao estado inicial. */
  reset?(): Promise<void>;
}
