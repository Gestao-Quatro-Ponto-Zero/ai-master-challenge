export type Severidade = "baixo" | "medio" | "critico";
export type StatusTicket = "novo" | "em_andamento" | "resolvido" | "escalado";
export type StatusAgente = "online" | "offline" | "ocupado";
export type Perfil = "agente" | "gestor" | "diretor";

export interface LoginResponse {
  token: string;
  nome: string;
  email: string;
  perfil: Perfil;
}

export interface Ticket {
  id: string;
  texto: string;
  nome_cliente: string;
  canal: string;
  categoria: string;
  confianca: number;
  severidade: Severidade;
  status: StatusTicket;
  resposta_ia: string | null;
  resumo_ia: string | null;
  solucoes_sugeridas: string[] | null;
  agente_responsavel: string | null;
  criado_em: string;
  resolvido_em: string | null;
}

export interface TriagemResponse {
  ticket_id: string;
  categoria: string;
  confianca: number;
  severidade: Severidade;
  acao: string;
  resposta_ia: string | null;
  resumo_ia: string | null;
  solucoes_sugeridas: string[] | null;
  notificar_agente: boolean;
  encaminhar_humano: boolean;
}

export interface Metricas {
  periodo: string;
  total_tickets: number;
  por_severidade: Record<string, number>;
  por_status: Record<string, number>;
  tempo_medio_resolucao_horas: number | null;
  auto_resolvidos: number;
  pct_auto_resolvidos: number;
}

export interface TopMotivos {
  periodo: string;
  filtro_severidade: string;
  motivos: { categoria: string; quantidade: number; percentual: number }[];
}

export interface Alerta {
  id: string;
  tipo: string;
  mensagem: string;
  severidade: Severidade;
  contagem: number;
  limite: number;
  disparado_em: string;
  reconhecido: boolean;
}

export interface Agente {
  nome: string;
  status: StatusAgente;
  tickets_atribuidos: number;
  ultimo_acesso: string;
}

export interface TicketSimilar {
  texto: string;
  resolucao: string;
  pontuacao_similaridade: number;
}

export interface SugestaoResponse {
  consulta: string;
  tickets_similares: TicketSimilar[];
}

export interface DiagnosticoData {
  total_tickets: number;
  tickets_fechados: number;
  satisfacao_media: number;
  tempo_medio_resolucao_horas: number;
  tempo_por_canal: Record<string, number>;
  tempo_por_tipo: Record<string, number>;
  tempo_por_prioridade: Record<string, number>;
  satisfacao_por_canal: Record<string, number>;
  satisfacao_por_prioridade: Record<string, number>;
  distribuicao_tipo: Record<string, number>;
  distribuicao_prioridade: Record<string, number>;
  desperdicio: {
    tickets_automatizaveis_ano: number;
    horas_economizadas_ano: number;
    economia_estimada_ano: number;
  };
}

export interface Usuario {
  email: string;
  nome: string;
  perfil: Perfil;
  ativo: boolean;
}

export interface OnboardingResponse {
  registros_importados: number;
  categorias_encontradas: string[];
  rag_atualizado: boolean;
  mensagem: string;
}

export interface HealthStatus {
  status: string;
  projeto: string;
  versao: string;
  motor_ia: string;
  rag_ativo: boolean;
  rag_documentos: number;
  tickets: number;
  agentes_online: number;
  alertas_ativos: number;
}
