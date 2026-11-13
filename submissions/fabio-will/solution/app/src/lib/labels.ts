import type { Reason, Tier } from './router'

/** Queue names as the support team would say them. Keys are the dataset labels. */
export const QUEUE_PT: Record<string, string> = {
  Access: 'Acesso',
  'Administrative rights': 'Direitos de administrador',
  'HR Support': 'RH',
  Hardware: 'Hardware',
  'Internal Project': 'Projeto interno',
  Miscellaneous: 'Diversos',
  Purchase: 'Compras',
  Storage: 'Armazenamento',
}

export const queuePt = (q: string): string => QUEUE_PT[q] ?? q

export const TIER_PT: Record<Tier, string> = {
  auto: 'Automático',
  assist: 'Assistido',
  human: 'Humano',
}

export const TIER_HINT: Record<Tier, string> = {
  auto: 'Vai direto para a fila. Entra na auditoria por amostra.',
  assist: 'O agente confirma entre as duas filas mais prováveis com um clique.',
  human: 'Triagem feita por uma pessoa, do zero.',
}

export const REASON_PT: Record<Reason, string> = {
  confianca_alta: 'Confiança acima do limiar de 95% de precisão',
  confianca_media: 'Confiança média: a fila certa está entre as duas sugeridas em 9 de cada 10 casos',
  confianca_baixa: 'Confiança baixa demais para sugerir',
  fila_privilegiada: 'Pedido de direito de administrador: uma pessoa sempre confirma',
  possivel_conteudo_sensivel: 'Pode ter conteúdo de RH ou de acesso privilegiado: uma pessoa confirma',
  sem_historico_parecido: 'Nada parecido no histórico: triagem humana',
  vocabulario_desconhecido: 'Texto fora do vocabulário conhecido (outro idioma ou ruído): triagem humana',
  trecho_sensivel: 'Um trecho do ticket tem cara de RH ou de acesso privilegiado: uma pessoa confirma',
  sequencia_incomum: 'Sequência de palavras que não existe no histórico (texto embaralhado ou colado): triagem humana',
}

/** Dataset 1 categories, as the operation would say them. */
export const D1_PT: Record<string, string> = {
  Email: 'E-mail',
  Phone: 'Telefone',
  Chat: 'Chat',
  'Social media': 'Redes sociais',
  Low: 'Baixa',
  Medium: 'Média',
  High: 'Alta',
  Critical: 'Crítica',
  'Technical issue': 'Problema técnico',
  'Billing inquiry': 'Cobrança',
  'Product inquiry': 'Dúvida de produto',
  'Refund request': 'Reembolso',
  'Cancellation request': 'Cancelamento',
}

export const d1Pt = (v: string): string => D1_PT[v] ?? v

export const SEVERITY_PT = {
  extreme: 'Extremamente crítico',
  critical: 'Crítico',
  medium: 'Médio',
  light: 'Leve',
} as const

export type Severity = keyof typeof SEVERITY_PT

export const pct = (v: number, digits = 1): string =>
  `${(v * 100).toLocaleString('pt-BR', { minimumFractionDigits: digits, maximumFractionDigits: digits })}%`

export const num = (v: number, digits = 0): string =>
  v.toLocaleString('pt-BR', { minimumFractionDigits: digits, maximumFractionDigits: digits })
