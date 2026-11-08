import type { DealsApi } from '../DealsApi';
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
} from '../types';
import { ApiError } from '../errors';
import { browserStore, readJson, writeJson, type KeyValueStore } from '../../lib/storage';
import { REFERENCE_DATE, buildSeedDeals } from './seed';
import { explainDeal, filterDeals, mockMeta, paginate, summarize, todayDeals } from './rules';

export { filterDeals };

export interface MockOptions {
  /** Atraso simulado de cada chamada (ms). Padrão 0. */
  latencyMs?: number;
  showProbability?: boolean;
  /** Onde guardar adiados e feedback entre recarregamentos. null = só em memória. */
  storage?: KeyValueStore | null;
  now?: () => Date;
}

export const MOCK_STORAGE_KEY = 'g4.mock.v1';

interface Persisted {
  hidden: string[];
  feedback: Record<string, FeedbackEntry[]>;
}

const USER: CurrentUser = { userKey: 'vicki.laflamme', name: 'Vicki Laflamme', role: 'seller', region: 'West' };

const clone = <T>(value: T): T => (value === undefined ? value : (JSON.parse(JSON.stringify(value)) as T));

export class MockDealsApi implements DealsApi {
  private readonly deals: Deal[];
  private readonly latencyMs: number;
  private readonly showProbability: boolean;
  private readonly storage: KeyValueStore | null;
  private readonly now: () => Date;
  private hidden: Set<string>;
  private feedback: Record<string, FeedbackEntry[]>;

  constructor(options: MockOptions = {}) {
    this.latencyMs = options.latencyMs ?? 0;
    this.showProbability = options.showProbability ?? false;
    // Como a API: sem show_probability, a probabilidade não sai.
    this.deals = buildSeedDeals().map((d) => ({ ...d, probability: this.showProbability ? d.probability : null }));
    this.storage = options.storage === undefined ? browserStore() : options.storage;
    this.now = options.now ?? (() => new Date());
    const saved = readJson<Persisted>(this.storage, MOCK_STORAGE_KEY, { hidden: [], feedback: {} });
    this.hidden = new Set(saved.hidden);
    this.feedback = saved.feedback ?? {};
  }

  private persist(): void {
    writeJson(this.storage, MOCK_STORAGE_KEY, { hidden: [...this.hidden], feedback: this.feedback });
  }

  private respond<T>(produce: () => T): Promise<T> {
    return new Promise<T>((resolve, reject) => {
      const run = () => {
        try {
          resolve(clone(produce()));
        } catch (error) {
          reject(error);
        }
      };
      if (this.latencyMs > 0) setTimeout(run, this.latencyMs);
      else run();
    });
  }

  getCurrentUser(): Promise<CurrentUser> {
    return this.respond(() => USER);
  }

  getMeta(): Promise<Meta> {
    return this.respond(() => mockMeta(this.showProbability, REFERENCE_DATE));
  }

  getFilters(): Promise<ListFilters> {
    return this.respond(() => ({ products: [...new Set(this.deals.map((d) => d.product))].sort() }));
  }

  getSummary(): Promise<Summary> {
    return this.respond(() => summarize(this.deals.filter((d) => !this.hidden.has(d.id))));
  }

  listDeals(query: ListDealsQuery): Promise<DealsPage> {
    return this.respond(() => {
      if (query.pageSize < 1) throw new ApiError(422, 'INVALID_PAGE_SIZE', 'O tamanho da página deve ser 1 ou mais.');
      return paginate(filterDeals(this.deals, this.hidden, query), query);
    });
  }

  getDealExplanation(dealId: string): Promise<DealExplanation> {
    return this.respond(() => {
      const deal = this.deals.find((d) => d.id === dealId);
      if (!deal) throw new ApiError(404, 'DEAL_NOT_FOUND', 'Deal não encontrado.');
      return explainDeal(deal);
    });
  }

  listTodayDeals(query: TodayQuery): Promise<Deal[]> {
    return this.respond(() => todayDeals(this.deals.filter((d) => !this.hidden.has(d.id)), query.cap));
  }

  applyAction(request: DealActionRequest): Promise<ActionResult> {
    return this.respond(() => {
      const known = new Set(this.deals.map((d) => d.id));
      const affectedIds = request.dealIds.filter((id) => known.has(id));
      affectedIds.forEach((id) => this.hidden.add(id));
      this.persist();
      return { affectedIds };
    });
  }

  undoAction(dealIds: string[]): Promise<ActionResult> {
    return this.respond(() => {
      const affectedIds = dealIds.filter((id) => this.hidden.delete(id));
      this.persist();
      return { affectedIds };
    });
  }

  sendFeedback(dealId: string, kind: FeedbackKind, reason: DisagreeReason | null = null): Promise<void> {
    return this.respond(() => {
      if (!this.deals.some((d) => d.id === dealId)) {
        throw new ApiError(404, 'DEAL_NOT_FOUND', 'Deal não encontrado.');
      }
      const entry: FeedbackEntry = { kind, reason, createdAt: this.now().toISOString() };
      this.feedback[dealId] = [entry, ...(this.feedback[dealId] ?? [])];
      this.persist();
    });
  }

  listFeedback(dealId: string): Promise<FeedbackEntry[]> {
    return this.respond(() => this.feedback[dealId] ?? []);
  }

  reset(): Promise<void> {
    return this.respond(() => {
      this.hidden = new Set();
      this.feedback = {};
      this.persist();
    });
  }
}
