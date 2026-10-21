// Tipos e chamadas da API do backend (FastAPI) — espelham os dicts de
// backend/app/scoring.py, alertas.py, emergencia.py, metricas.py e crosssell.py.

export type Acao = "Atacar agora" | "Nutrir" | "Primeiro contato" | "Requalificar" | "Encerrar" | "Baixa prioridade"
export type Severidade = "critico" | "atencao" | "lembrete"
export type Pilar = "chance" | "valor" | "dados"

export interface Motivo {
  pilar: Pilar
  pontos: number
  maximo: number
  texto: string
  tom: "positivo" | "neutro" | "negativo"
}

export interface Redistribuicao {
  opportunity_id: string
  conta: string | null
  produto: string
  score: number
  valor_esperado: number
  de: string
  para: string
  afinidade_destino: number
}

export interface Alerta {
  tipo: string
  severidade: Severidade
  titulo: string
  mensagem: string
  acao_sugerida: string
  na_fila: boolean
  rebaixado?: boolean
  opportunity_id?: string
  agente?: string
  manager?: string
  stage?: string
  produto?: string
  conta?: string | null
  score?: number
  valor_esperado?: number
  redistribuicao?: Redistribuicao[]
}

export interface DealResumo {
  opportunity_id: string
  agente: string
  conta: string | null
  produto: string
  stage: "Prospecting" | "Engaging"
  idade_dias: number | null
  score: number
  acao: Acao
  probabilidade: number | null
  prob_min: number | null
  prob_max: number | null
  valor: number
  valor_liquido: number
  valor_esperado: number
  prob_trimestre: number
  valor_esperado_trimestre: number
}

export interface Deal extends DealResumo {
  manager: string
  regiao: string
  serie: string
  setor: string | null
  engage_date: string | null
  fora_do_ciclo: boolean
  motivos: Motivo[]
  alertas: Alerta[]
}

export interface PipelineResponse {
  data_referencia: string
  horizonte: { fim: string; dias: number }
  resumo: {
    total: number
    valor_total: number
    valor_esperado_total: number
    por_acao: Partial<Record<Acao, { n: number; valor: number; valor_esperado: number }>>
  }
  deals: Deal[]
}

export interface DatasResponse {
  padrao: string
  datas: { data: string; dias_para_fim_trimestre: number; final: boolean }[]
}

export interface FiltrosResponse {
  data_referencia: string
  agentes: { nome: string; manager: string; regiao: string; deals_abertos: number }[]
  managers: string[]
  regioes: string[]
  acoes: Acao[]
}

export interface AlertasResponse {
  contagem: Record<Severidade, number>
  time: Alerta[]
  alertas: Alerta[]
}

export interface Trimestre {
  inicio: string
  fim: string
  dias_total: number
  dias_decorridos: number
  dias_restantes: number
  pct_decorrido: number
}

export interface EmergenciaResponse {
  ativa: boolean
  na_janela: boolean
  em_risco: boolean
  trimestre: Trimestre
  meta: number | null
  fechado: number
  valor_esperado: number
  projecao: number
  falta: number
  gap: number
  pct_meta: number | null
  janela_dias: number
  meta_fator: number
  resgate: { n: number; valor: number; cobre_a_meta: boolean; deals: DealResumo[] }
}

export interface MetricaVendedor {
  agente: string
  manager: string
  regiao: string
  media_trimestral: number | null
  meta: number | null
  fechado_trimestre: number
  pct_meta: number | null
  pct_trimestre: number
  valor_ponderado: number
  cobertura: number | null
  projecao: number
  ciclo_mediano: number | null
  ciclo_vs_time: number | null
  throughput_mes: number
  capacidade: number
  carga: number
  carga_total: number
  carga_rel: number | null
  deals_abertos: number
  pct_sem_conta: number | null
  n_atacar: number
}

export interface MetricaTime {
  manager: string
  regiao: string
  meta: number | null
  fechado_trimestre: number
  pct_meta: number | null
  cobertura: number | null
  carga_rel: number | null
  deals_abertos: number
  n_atacar: number
}

export interface TimeResponse {
  trimestre: Trimestre
  fator_sobrecarga: number
  vendedores: MetricaVendedor[]
  times: MetricaTime[]
}

export interface CrossSell {
  conta: string
  setor: string
  series_compradas: string[]
  serie_sugerida: string
  produto_sugerido: string
  valor_historico: number
  n_compras: number
  ultima_compra: string
  agente: string
}

export interface CrossSellResponse {
  total: number
  sugestoes: CrossSell[]
}

export interface PontoCalibracao {
  de: number
  ate: number
  previsto: number
  real: number
  calibrado: number
  n: number
}

export interface BenchmarksResponse {
  win_rate_geral: number
  zona_risco_dias: number
  pct_perdidos_na_zona: number
  ciclo_max_dias: number
  ciclo_p75_produto: Record<string, number>
  win_fim_trimestre: number
  win_fora_trimestre: number
  desconto_produto: Record<string, number>
  pesos: Record<Pilar, number>
  limites_acao: { atacar: number; nutrir: number; percentil_atacar: number; percentil_nutrir: number }
  calibracao: {
    calibrada: boolean
    data_corte: string
    curva: PontoCalibracao[]
    auc: number
    auc_com_teto: number
    n_observacoes: number
    data_inicio: string | null
    data_fim: string | null
    n_datas: number
    zumbis_observados: number
    zumbis_que_ganharam: number
  }
}

export interface Recorte {
  regiao?: string
  manager?: string
  agente?: string
  stage?: string
  acao?: string
}

// ── IA ──
export interface TextoIA {
  texto: string
  fonte: "ia" | "template"
  modelo?: string
  motivo?: string
  cache?: boolean
  deals_citados?: string[]
  ferramentas?: string[]
}

export interface RascunhoIA {
  assunto: string
  corpo: string
  fonte: "ia" | "template"
}

export type TipoRascunho = "followup" | "requalificacao" | "encerramento"

export interface MensagemChat {
  role: "user" | "assistant"
  content: string
}

export interface IaStatus {
  ativa: boolean
  provedor: string
  modelo: string | null
}

// ── E-mails ──
export interface DestinatarioEmail {
  publico: "equipe" | "gestao"
  papel: "vendedor" | "manager" | "revops"
  nome: string
  para: string[]
}

export interface EmailsResponse {
  modo: string
  redirecionar: boolean
  destinatarios_reais: boolean
  ia: IaStatus
  emails: DestinatarioEmail[]
}

function query(params: Record<string, string | number | undefined>): string {
  const q = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== "") q.set(k, String(v))
  const s = q.toString()
  return s ? `?${s}` : ""
}

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`/api${path}`)
  if (!r.ok) {
    const corpo = await r.json().catch(() => null)
    throw new Error(corpo?.detail ?? "Não consegui falar com o servidor do Lead Scorer. Ele está rodando?")
  }
  return r.json() as Promise<T>
}

async function post<T>(path: string, corpo: unknown): Promise<T> {
  const r = await fetch(`/api${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(corpo),
  })
  if (!r.ok) {
    const c = await r.json().catch(() => null)
    throw new Error(typeof c?.detail === "string" ? c.detail : "A IA não respondeu. Tente de novo.")
  }
  return r.json() as Promise<T>
}

// Filtros de pessoa (sem stage/ação) — usados por time, emergência e cross-sell
const pessoas = (r: Recorte) => ({ regiao: r.regiao, manager: r.manager, agente: r.agente })

// Escopo da IA: vendedor tem prioridade sobre manager; sem os dois = visão RevOps
const escopo = (r: Recorte) => (r.agente ? { agente: r.agente } : r.manager ? { manager: r.manager } : {})

export const urlPreviewEmail = (data: string, d: DestinatarioEmail) =>
  `/api/emails/preview${query({ data, papel: d.papel, nome: d.nome })}`

export const ia = {
  status: () => get<IaStatus>("/ia/status"),
  briefing: (data: string, r: Recorte) => post<TextoIA>("/ia/briefing", { data, ...escopo(r) }),
  deal: (data: string, id: string) => post<TextoIA>(`/ia/deal/${id}`, { data }),
  perguntar: (data: string, pergunta: string, historico: MensagemChat[]) =>
    post<TextoIA>("/ia/perguntar", { data, pergunta, historico }),
  planoResgate: (data: string, r: Recorte) => post<TextoIA>("/ia/plano-resgate", { data, ...escopo(r) }),
  rascunho: (data: string, id: string, tipo: TipoRascunho) => post<RascunhoIA>(`/ia/rascunho/${id}`, { data, tipo }),
  winloss: (data: string, r: Recorte) => post<TextoIA>("/ia/winloss", { data, ...escopo(r) }),
  emails: (data: string) => get<EmailsResponse>(`/emails${query({ data })}`),
}

export const api = {
  datas: () => get<DatasResponse>("/datas"),
  filtros: (data: string) => get<FiltrosResponse>(`/filtros${query({ data })}`),
  pipeline: (data: string, r: Recorte) => get<PipelineResponse>(`/pipeline${query({ data, ...r, limite: 5000 })}`),
  alertas: (data: string, r: Recorte) => get<AlertasResponse>(`/alertas${query({ data, ...r, acao: undefined })}`),
  emergencia: (data: string, r: Recorte) => get<EmergenciaResponse>(`/emergencia${query({ data, ...pessoas(r) })}`),
  time: (data: string, r: Recorte) => get<TimeResponse>(`/time${query({ data, ...pessoas(r) })}`),
  crossSell: (data: string, r: Recorte) => get<CrossSellResponse>(`/cross-sell${query({ data, ...pessoas(r) })}`),
  benchmarks: (data: string) => get<BenchmarksResponse>(`/benchmarks${query({ data })}`),
}
