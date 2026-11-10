// Etapas do funil na tela (O-31, decisão do Leandro): Novo lead, Atendimento, Em negociação, Fechado, Perdido.
// O banco continua com 4 estágios (Prospecting, Engaging, Won, Lost). "Novo lead" e "Atendimento" são o
// Prospecting sem e com contato registrado no CRM: o primeiro contato leva o lead para Atendimento sozinho.
import type { DealVisao, Estagio, EventoLinhaDoTempo, Papel } from "./tipos";

export type Etapa = "novo" | "atendimento" | "negociacao" | "fechado" | "perdido";

export const ETAPAS: Etapa[] = ["novo", "atendimento", "negociacao", "fechado", "perdido"];

export const ROTULO_ETAPA: Record<Etapa, string> = {
  novo: "Novo lead",
  atendimento: "Atendimento",
  negociacao: "Em negociação",
  fechado: "Fechado",
  perdido: "Perdido",
};

/** Estágio do banco de cada etapa. */
export const ESTAGIO_DA_ETAPA: Record<Etapa, Estagio> = {
  novo: "Prospecting",
  atendimento: "Prospecting",
  negociacao: "Engaging",
  fechado: "Won",
  perdido: "Lost",
};

/**
 * Etapa de um deal. ultimoContato do Prospecting é o contato registrado no CRM (a view só usa a data de
 * abertura como primeiro contato para Em negociação), então "com contato" = Atendimento.
 */
export function etapaDe(d: Pick<DealVisao, "estagio" | "ultimoContato">): Etapa {
  if (d.estagio === "Prospecting") return d.ultimoContato ? "atendimento" : "novo";
  if (d.estagio === "Engaging") return "negociacao";
  return d.estagio === "Won" ? "fechado" : "perdido";
}

export const rotuloDoDeal = (d: Pick<DealVisao, "estagio" | "ultimoContato">) => ROTULO_ETAPA[etapaDe(d)];

/**
 * Para onde o deal pode ir. Atendimento só para quem ainda é Novo lead (entra registrando o contato);
 * não existe voltar para Novo lead (o contato não se desfaz). Reabrir encerrado: manager e admin.
 */
export function destinosDe(etapa: Etapa, papel: Papel): Etapa[] {
  if (etapa === "novo") return ["atendimento", "negociacao", "perdido"];
  if (etapa === "atendimento") return ["negociacao", "perdido"];
  if (etapa === "negociacao") return ["fechado", "perdido"];
  return papel === "vendedor" ? [] : ["negociacao"];
}

/** Texto do destino no controle do cartão. */
export function rotuloDestino(de: Etapa, para: Etapa): string {
  if (de === "fechado" || de === "perdido") return "Reabrir (Em negociação)";
  if (para === "atendimento") return "Registrar atendimento";
  if (para === "perdido" && (de === "novo" || de === "atendimento")) return "Descartar (Perdido)";
  return `Mover para ${ROTULO_ETAPA[para]}`;
}

// Ações que contam como contato na linha do tempo (as mesmas do banco: acoes_contato, ✓ e atendimento).
const CONTATO = /^(Liguei|Requalifiquei|Feito na prioridade do dia|Atendimento:|Ligação|E-mail|Mensagem|Reunião|Proposta enviada|Requalificado|Sem resposta)/;

/**
 * Linha do tempo: o banco escreve o estágio "Prospecção" e "Ganho". Na tela vira a etapa da época:
 * "Novo lead" antes do primeiro contato registrado e "Atendimento" depois; "Ganho" vira "Fechado".
 */
export function rotularLinhaDoTempo<T extends Pick<EventoLinhaDoTempo, "tipo" | "descricao" | "desfeito">>(eventos: T[]): T[] {
  let comContato = false;
  return eventos.map((e) => {
    if (e.tipo === "acao" && !e.desfeito && CONTATO.test(e.descricao)) comContato = true;
    const descricao = e.descricao
      .replace(/\bProspecção\b/g, comContato ? "Atendimento" : "Novo lead")
      .replace(/^Ganho:/, "Fechado:")
      .replace(/→ Ganho\b/, "→ Fechado")
      .replace(/Estágio: Ganho\b/, "Estágio: Fechado");
    return descricao === e.descricao ? e : { ...e, descricao };
  });
}
