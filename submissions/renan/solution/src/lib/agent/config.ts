/** Configuração do agente escolhida pelo usuário na tela Configurações (fica no navegador). */
export const MODELS = [
  { id: "claude-opus-5-5", label: "Claude Opus 5.5", hint: "Mais capaz (padrão)" },
  { id: "claude-sonnet-5-5", label: "Claude Sonnet 5.5", hint: "Equilíbrio entre qualidade e custo" },
  { id: "claude-haiku-5-5", label: "Claude Haiku 5.5", hint: "Mais rápido e barato" },
] as const;

export type ModelId = (typeof MODELS)[number]["id"];

export const EFFORTS = [
  { id: "low", label: "Baixo", hint: "Respostas rápidas" },
  { id: "medium", label: "Médio", hint: "Padrão" },
  { id: "high", label: "Alto", hint: "Análises mais cuidadosas" },
] as const;

export type Effort = (typeof EFFORTS)[number]["id"];

export interface AgentSettings {
  apiKey: string;
  model: ModelId;
  effort: Effort;
}

export const DEFAULT_SETTINGS: AgentSettings = { apiKey: "", model: "claude-opus-5-5", effort: "medium" };

export const SETTINGS_STORAGE_KEY = "regua.agente.config";

/** Cabeçalho em que a chave do próprio usuário viaja até a rota do agente. */
export const KEY_HEADER = "x-anthropic-key";

export const isModelId = (v: unknown): v is ModelId => MODELS.some((m) => m.id === v);
export const isEffort = (v: unknown): v is Effort => EFFORTS.some((e) => e.id === v);

/** Lê a configuração salva no navegador; nunca quebra se o storage estiver indisponível. */
export function loadSettings(): AgentSettings {
  try {
    const raw = localStorage.getItem(SETTINGS_STORAGE_KEY);
    if (!raw) return DEFAULT_SETTINGS;
    const saved = JSON.parse(raw) as Partial<AgentSettings>;
    return {
      apiKey: typeof saved.apiKey === "string" ? saved.apiKey : "",
      model: isModelId(saved.model) ? saved.model : DEFAULT_SETTINGS.model,
      effort: isEffort(saved.effort) ? saved.effort : DEFAULT_SETTINGS.effort,
    };
  } catch {
    return DEFAULT_SETTINGS;
  }
}

export function saveSettings(settings: AgentSettings): boolean {
  try {
    localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings));
    return true;
  } catch {
    return false;
  }
}

export function clearSettings() {
  try {
    localStorage.removeItem(SETTINGS_STORAGE_KEY);
  } catch {}
}
