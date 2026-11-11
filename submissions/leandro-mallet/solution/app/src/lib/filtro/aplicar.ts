// Aplica as etiquetas a um deal ou a uma conta. Mesma regra de core_atende_etiquetas no banco.
import { diasEntre, semAcento } from "../calculos";
import { etapaDe } from "../etapas";
import type { ContaVisao, DealVisao } from "../tipos";
import type { Etiquetas } from "./etiquetas";

/** "Contém": todas as palavras precisam aparecer, em qualquer ordem, sem diferenciar acento nem maiúscula. */
export function contemTodas(alvo: string, busca: string): boolean {
  const texto = semAcento(alvo).toLowerCase();
  return semAcento(busca).toLowerCase().split(/\s+/).filter(Boolean).every((p) => texto.includes(p));
}

const em = <T,>(lista: T[] | undefined, v: T | null): boolean => !lista || (v !== null && lista.includes(v));

export function atendeDeal(d: DealVisao, e: Etiquetas, hoje: string): boolean {
  const semContatoHa = d.ultimoContato ? diasEntre(d.ultimoContato, hoje) : null;
  if (!em(e.estagios, d.estagio)) return false;
  if (!em(e.etapas, etapaDe(d))) return false;
  if (e.nota_min !== undefined && (d.score === null || d.score < e.nota_min)) return false;
  if (e.nota_max !== undefined && (d.score === null || d.score > e.nota_max)) return false;
  if (e.sem_nota && d.score !== null) return false;
  if (!em(e.icones, d.icone)) return false;
  if (e.abertura_de && (!d.dataAbertura || d.dataAbertura < e.abertura_de)) return false;
  if (e.abertura_ate && (!d.dataAbertura || d.dataAbertura > e.abertura_ate)) return false;
  if (e.sem_abertura && d.dataAbertura) return false;
  if (e.dias_aberto_min !== undefined && (d.diasDesdeAbertura === null || d.diasDesdeAbertura <= e.dias_aberto_min)) return false;
  if (e.contato_ha_dias_min !== undefined && semContatoHa !== null && semContatoHa < e.contato_ha_dias_min) return false;
  if (e.contato_ha_dias_max !== undefined && (semContatoHa === null || semContatoHa > e.contato_ha_dias_max)) return false;
  if (e.sem_contato && d.ultimoContato) return false;
  if (e.sem_contato_principal && d.contato) return false;
  if (!em(e.setores, d.setor)) return false;
  if (!em(e.portes, d.porte)) return false;
  if (e.sem_empresa && d.conta) return false;
  if (!em(e.empresas, d.conta)) return false;
  if (!em(e.produtos, d.produto)) return false;
  if (!em(e.series, d.serie)) return false;
  if (!em(e.vendedores, d.vendedor)) return false;
  if (!em(e.managers, d.manager)) return false;
  if (!em(e.regioes, d.regiao)) return false;
  if (!em(e.acoes_sugeridas, d.acaoSugerida)) return false;
  if (e.valor_min !== undefined && (d.valorEsperado ?? d.closeValue ?? 0) < e.valor_min) return false;
  if (e.fechamento_de && (!d.closeDate || d.closeDate < e.fechamento_de)) return false;
  if (e.fechamento_ate && (!d.closeDate || d.closeDate > e.fechamento_ate)) return false;
  if (e.tags && !d.tags.some((t) => e.tags?.some((x) => semAcento(x) === semAcento(t.nome)))) return false;
  if (e.sem_tag && d.tags.length > 0) return false;
  if (e.com_comentario && d.qtdComentarios === 0) return false;
  if (e.contem) {
    const alvo = [d.id, d.nome, d.produto, d.conta, d.vendedor, d.contato?.nome, ...d.tags.map((t) => t.nome)].filter(Boolean).join(" ");
    if (!contemTodas(alvo, e.contem)) return false;
  }
  return true;
}

export function atendeConta(c: ContaVisao, e: Etiquetas): boolean {
  if (!em(e.setores, c.setor)) return false;
  if (!em(e.portes, c.porte)) return false;
  if (e.padroes && !e.padroes.includes(c.padrao ?? "sem_padrao")) return false;
  if (e.compras_min !== undefined && c.compras < e.compras_min) return false;
  if (e.com_aberto && c.dealsAbertos === 0) return false;
  if (e.sem_aberto && c.dealsAbertos > 0) return false;
  if (e.receita_min !== undefined && c.receitaGanha < e.receita_min) return false;
  if (e.subsidiaria && !c.empresaMae) return false;
  if (e.independente && c.empresaMae) return false;
  if (e.bonus_min !== undefined && (c.bonus === null || c.bonus < e.bonus_min)) return false;
  if (!em(e.sedes, c.sede)) return false;
  if (!em(e.empresas, c.nome)) return false;
  if (e.contem && !contemTodas([c.nome, c.setor, c.sede, c.empresaMae].filter(Boolean).join(" "), e.contem)) return false;
  return true;
}
