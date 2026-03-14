import type {
  LoginResponse, Ticket, TriagemResponse, Metricas,
  TopMotivos, Alerta, Agente, SugestaoResponse, DiagnosticoData,
  Usuario, OnboardingResponse, HealthStatus,
} from "@/types";

const BASE = "/api";

function token(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

async function request<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const t = token();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(t ? { Authorization: `Bearer ${t}` } : {}),
    ...(opts.headers as Record<string, string> || {}),
  };

  const res = await fetch(`${BASE}${path}`, { ...opts, headers });

  if (res.status === 401) {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "/";
    throw new Error("Sessão expirada");
  }

  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Erro ${res.status}`);
  }

  return res.json();
}

export const api = {
  login: async (email: string, senha: string): Promise<LoginResponse> => {
    const res = await fetch(`${BASE}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, senha }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: "Erro desconhecido" }));
      throw new Error(body.detail || `Erro ${res.status}`);
    }
    return res.json();
  },

  triagem: (texto: string, nome_cliente = "Cliente", canal = "chat") =>
    request<TriagemResponse>("/triagem", {
      method: "POST",
      body: JSON.stringify({ texto, nome_cliente, canal }),
    }),

  sugerirResposta: (texto: string, quantidade = 3) =>
    request<SugestaoResponse>("/sugerir-resposta", {
      method: "POST",
      body: JSON.stringify({ texto, quantidade }),
    }),

  listarTickets: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<Ticket[]>(`/tickets${qs}`);
  },

  obterTicket: (id: string) =>
    request<Ticket>(`/tickets/${id}`),

  atualizarStatus: (id: string, status: string, nome_agente?: string) =>
    request<Ticket>(`/tickets/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status, ...(nome_agente ? { nome_agente } : {}) }),
    }),

  metricas: (periodo = "dia") =>
    request<Metricas>(`/metricas?periodo=${periodo}`),

  topMotivos: (periodo = "dia", severidade = "todos") =>
    request<TopMotivos>(`/metricas/top-motivos?periodo=${periodo}&severidade=${severidade}`),

  alertas: (apenas_ativos = false) =>
    request<Alerta[]>(`/alertas?apenas_ativos=${apenas_ativos}`),

  agentesOnline: () =>
    request<Agente[]>("/agentes/online"),

  definirStatusAgente: (nome: string, status: string) =>
    request<Agente>("/agentes/status", {
      method: "POST",
      body: JSON.stringify({ nome, status }),
    }),

  diagnostico: () =>
    request<DiagnosticoData>("/diagnostico"),

  listarUsuarios: () =>
    request<Usuario[]>("/usuarios"),

  criarUsuario: (nome: string, email: string, senha: string, perfil: string) =>
    request<Usuario>("/usuarios", {
      method: "POST",
      body: JSON.stringify({ nome, email, senha, perfil }),
    }),

  atualizarUsuario: (email: string, dados: { nome?: string; perfil?: string; ativo?: boolean }) =>
    request<Usuario>(`/usuarios/${encodeURIComponent(email)}`, {
      method: "PUT",
      body: JSON.stringify(dados),
    }),

  desativarUsuario: (email: string) =>
    request<{ mensagem: string }>(`/usuarios/${encodeURIComponent(email)}`, {
      method: "DELETE",
    }),

  uploadDados: async (file: File) => {
    const t = token();
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${BASE}/onboarding/upload`, {
      method: "POST",
      headers: { ...(t ? { Authorization: `Bearer ${t}` } : {}) },
      body: formData,
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json() as Promise<OnboardingResponse>;
  },

  health: () =>
    fetch(`${BASE}/health`).then(r => r.json()) as Promise<HealthStatus>,
};
