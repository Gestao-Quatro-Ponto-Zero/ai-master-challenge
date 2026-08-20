import type {
  Filtros,
  Identities,
  Kpis,
  Oportunidade,
  Rollup,
  ScoreAvulsaResult,
  Session,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, opts: RequestInit = {}, token?: string): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (opts.headers) Object.assign(headers, opts.headers as Record<string, string>);
  if (token) headers.Authorization = `Bearer ${token}`;

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
    if (v !== undefined && v !== "") usp.set(k, String(v));
  }
  const s = usp.toString();
  return s ? `?${s}` : "";
}

export const api = {
  getIdentities: () => request<Identities>("/identities"),

  identify: (name: string) =>
    request<Session>("/identify", { method: "POST", body: JSON.stringify({ name }) }),

  getDeals: (token: string, filtros: Filtros & { estado?: string; as_of?: string }) =>
    request<Oportunidade[]>(`/deals${qs(filtros)}`, {}, token),

  getKpis: (token: string, as_of?: string) =>
    request<Kpis>(`/kpis${qs({ as_of })}`, {}, token),

  getRollup: (token: string, as_of?: string) =>
    request<Rollup>(`/rollup${qs({ as_of })}`, {}, token),

  scoreAvulsa: (
    token: string,
    body: { product: string; age_days?: number; porte?: string }
  ) => request<ScoreAvulsaResult>("/score", { method: "POST", body: JSON.stringify(body) }, token),

  async downloadProcessedCsv(token: string): Promise<Blob> {
    const res = await fetch(`${API_BASE}/export/csv`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new ApiError(res.status, "falha ao baixar o dataset processado");
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
