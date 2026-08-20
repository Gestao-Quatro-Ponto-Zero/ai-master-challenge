import type {
  DealDetail,
  DealsEnvelope,
  Filtros,
  FilterOptions,
  Kpis,
  Rollup,
  ScoreAvulsaResult,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (opts.headers) Object.assign(headers, opts.headers as Record<string, string>);

  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      // corpo não era JSON — mantém o statusText.
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

function qs(params: object): string {
  const usp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "") continue;
    if (Array.isArray(v)) {
      for (const item of v) usp.append(k, String(item));
    } else {
      usp.set(k, String(v));
    }
  }
  const s = usp.toString();
  return s ? `?${s}` : "";
}

export interface DealsQuery extends Filtros {
  estado?: string[];
  as_of?: string;
  page?: number;
  page_size?: number;
  sort?: string;
  order?: string;
}

export const api = {
  getDeals: (query: DealsQuery, signal?: AbortSignal) =>
    request<DealsEnvelope>(`/deals${qs(query)}`, { signal }),

  getDealDetail: (opportunityId: string, as_of?: string) =>
    request<DealDetail>(`/deals/${encodeURIComponent(opportunityId)}${qs({ as_of })}`),

  getFilterOptions: () => request<FilterOptions>("/filter-options"),

  getKpis: (query: DealsQuery, signal?: AbortSignal) =>
    request<Kpis>(`/kpis${qs(query)}`, { signal }),

  getRollup: (
    query: Pick<Filtros, "sales_agent" | "manager" | "regional_office" | "product"> & {
      as_of?: string;
    }
  ) => request<Rollup>(`/rollup${qs(query)}`),

  scoreAvulsa: (body: { product: string; age_days?: number; porte?: string }) =>
    request<ScoreAvulsaResult>("/score", { method: "POST", body: JSON.stringify(body) }),

  async downloadProcessedCsv(): Promise<Blob> {
    const res = await fetch(`${API_BASE}/export/csv`);
    if (!res.ok) throw new ApiError(res.status, "falha ao baixar o dataset processado");
    return res.blob();
  },

  async exportDealIds(query: DealsQuery): Promise<Blob> {
    const res = await fetch(`${API_BASE}/export/deal-ids${qs(query)}`);
    if (!res.ok) throw new ApiError(res.status, "falha ao exportar identificadores filtrados");
    return res.blob();
  },
};

export function triggerBlobDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
