/**
 * Movimentos de dono: redistribuição de domingo, repasse por mudança de faixa e roteamento de lead novo.
 * Funções puras: devolvem o plano e as chamadas de função do banco; quem executa é a rotina (I/O fora daqui).
 * Referência da redistribuição: solution/scoring/redistribuir.py.
 */
import {
  arredondar, dia, faixaHeat, fitDoLead, FIT_FURAR_FILA, PESOS, temDestaque,
  type Celulas, type DealNota, type Lead,
} from "./regra";

/** Chamada de core_repassar_deal (o banco troca o dono, registra a reatribuição e a auditoria). */
export interface ChamadaRepasse {
  funcao: "core_repassar_deal";
  p_opportunity_id: string;
  p_para_vendedor: string;
  p_origem: "redistribuicao" | "repasse_janela";
  p_execucao_id: number;
  p_fit_dono: number | null;
  p_fit_novo: number;
  p_posicao_top: number | null;
  p_faixa_heat: string | null;
}

/* ------------------------------------------------------------------ redistribuição de domingo (cenário B, só equilíbrio) */

export interface TrocaPlano { opportunity_id: string; de: string; para: string; fit_dono: number; fit_novo: number; muda: boolean }

/**
 * Só leads em Prospecting sem contato registrado e sem trava do manager. Elegíveis: os vendedores ativos do time
 * (decisão 49); sem destaque ou sem histórico entram com FIT 50. Sem a lista, os que têm fechamentos na janela.
 * Limite da semana = ativos ÷ elegíveis, arredondado para cima, contando os ativos que cada um já tem.
 */
export function planejarRedistribuicao(leads: Lead[], notas: DealNota[], cel: Celulas, travados: Set<string> = new Set(), vendedores?: string[]) {
  const elegiveis = vendedores?.length ? [...vendedores].sort() : [...cel.taxaVendedor.keys()].sort();
  const eleg = new Set(elegiveis);
  const alvo = leads.filter((l) => l.estagio === "Prospecting" && !l.ultimo_contato_em && !travados.has(l.opportunity_id));
  const alvoIds = new Set(alvo.map((l) => l.opportunity_id));
  const ativos = notas.filter((n) => n.ativo);
  const carga = new Map(elegiveis.map((v) => [v, 0]));
  for (const n of ativos) if (!alvoIds.has(n.opportunity_id) && eleg.has(n.vendedor_nome)) carga.set(n.vendedor_nome, carga.get(n.vendedor_nome)! + 1);
  const base = ativos.filter((n) => eleg.has(n.vendedor_nome) || alvoIds.has(n.opportunity_id)).length;
  const limite = Math.ceil(base / elegiveis.length);
  const fit = new Map<string, number>();
  const pares: [number, string, string][] = [];
  for (const l of alvo) for (const v of elegiveis) {
    const f = fitDoLead(cel, v, l).fit;
    fit.set(`${l.opportunity_id}|${v}`, f);
    pares.push([f, l.opportunity_id, v]);
  }
  pares.sort((a, b) => b[0] - a[0] || (a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0) || (a[2] < b[2] ? -1 : a[2] > b[2] ? 1 : 0));
  const vagas = new Map(elegiveis.map((v) => [v, Math.max(0, limite - carga.get(v)!)]));
  const dono = new Map<string, string>();
  for (const [, o, v] of pares) {
    if (dono.has(o) || vagas.get(v)! <= 0) continue;
    dono.set(o, v);
    vagas.set(v, vagas.get(v)! - 1);
  }
  const notaPor = new Map(notas.map((n) => [n.opportunity_id, n]));
  const trocas: TrocaPlano[] = alvo.map((l) => {
    const de = l.vendedor_nome, para = dono.get(l.opportunity_id) ?? de;
    const fd = fit.get(`${l.opportunity_id}|${de}`) ?? notaPor.get(l.opportunity_id)?.fit ?? 50;
    return { opportunity_id: l.opportunity_id, de, para, fit_dono: arredondar(fd, 2), fit_novo: arredondar(fit.get(`${l.opportunity_id}|${para}`)!, 2), muda: para !== de };
  });
  return { limite, elegiveis, trocas };
}

export function chamadasRedistribuicao(trocas: TrocaPlano[], execucaoId: number): ChamadaRepasse[] {
  return trocas.filter((t) => t.muda).map((t) => ({
    funcao: "core_repassar_deal", p_opportunity_id: t.opportunity_id, p_para_vendedor: t.para, p_origem: "redistribuicao",
    p_execucao_id: execucaoId, p_fit_dono: arredondar(t.fit_dono), p_fit_novo: arredondar(t.fit_novo), p_posicao_top: null,
    p_faixa_heat: "sem data de abertura",
  }));
}

/* ------------------------------------------------------------------ repasse diário por mudança de faixa sem contato */

export interface ParametrosRepasse {
  fitMinimo: number;          // config repasse.fit_minimo (75)
  maxAbaixoDoDono: number;    // config repasse.max_abaixo_do_dono (3)
  topN: number;               // config repasse.top_n (5)
  maxRepassesPorLead: number | null; // config repasse.max_repasses_por_lead (proposta: 2)
}
export const PARAMETROS_REPASSE: ParametrosRepasse = { fitMinimo: 75, maxAbaixoDoDono: 3, topN: 5, maxRepassesPorLead: 2 };

export interface ResultadoRepasse { chamadas: ChamadaRepasse[]; filaManager: string[] }

/**
 * Lead aberto, sem contato registrado e sem trava, que mudou de faixa do HEAT entre ontem e hoje.
 * Passa ao vendedor de maior FIT entre os que: têm destaque e 1+ característica do lead com 10+ fechados,
 * FIT ≥ fitMinimo, FIT ≥ FIT do dono − maxAbaixoDoDono e em cujo top N o lead entra pela nota com ele.
 * Empate: menos ativos e depois menos penalidade. Lead que atingiu o máximo de repasses vai à fila do manager.
 * A penalidade de quem perde o lead é gravada pelo próprio core_repassar_deal (config penalidade_roteamento).
 */
export function planejarRepasses(
  leads: Lead[], notas: DealNota[], cel: Celulas, referencia: string, execucaoId: number,
  opcoes: { repassesPorLead?: Map<string, number>; travados?: Set<string>; penalidades?: Map<string, number>; parametros?: ParametrosRepasse } = {},
): ResultadoRepasse {
  const par = opcoes.parametros ?? PARAMETROS_REPASSE;
  const ref = dia(referencia);
  const notaPor = new Map(notas.map((n) => [n.opportunity_id, n]));
  const listas = new Map<string, number[]>();
  const ativos = new Map<string, number>();
  for (const n of notas) {
    (listas.get(n.vendedor_nome) ?? listas.set(n.vendedor_nome, []).get(n.vendedor_nome)!).push(n.nota);
    if (n.ativo) ativos.set(n.vendedor_nome, (ativos.get(n.vendedor_nome) ?? 0) + 1);
  }
  const vendedores = [...cel.taxaVendedor.keys()].sort();
  const candidatos = leads.filter((l) => (l.estagio === "Prospecting" || l.estagio === "Engaging") && !l.ultimo_contato_em
    && l.data_abertura && !opcoes.travados?.has(l.opportunity_id)
    && faixaHeat(ref - dia(l.data_abertura))[0] !== faixaHeat(ref - 1 - dia(l.data_abertura))[0]);
  const chamadas: ChamadaRepasse[] = [], fila: string[] = [];
  for (const l of candidatos.sort((a, b) => (notaPor.get(b.opportunity_id)?.nota ?? 0) - (notaPor.get(a.opportunity_id)?.nota ?? 0))) {
    const n = notaPor.get(l.opportunity_id);
    if (!n) continue;
    if (par.maxRepassesPorLead !== null && (opcoes.repassesPorLead?.get(l.opportunity_id) ?? 0) >= par.maxRepassesPorLead) {
      fila.push(l.opportunity_id);
      continue;
    }
    let melhor: { v: string; fit: number; pos: number } | null = null;
    for (const v of vendedores) {
      if (v === l.vendedor_nome || !temDestaque(cel, v)) continue;
      const f = fitDoLead(cel, v, l);
      if (!f.usadas.length || f.fit < par.fitMinimo || f.fit < n.fit - par.maxAbaixoDoDono) continue;
      const notaCom = PESOS.fit * f.fit + PESOS.heat * n.heat + n.bonus;
      const pos = 1 + (listas.get(v) ?? []).filter((x) => x > notaCom).length;
      if (pos > par.topN) continue;
      const melhorQue = (a: { v: string; fit: number }) =>
        f.fit > a.fit || (f.fit === a.fit && ((ativos.get(v) ?? 0) < (ativos.get(a.v) ?? 0)
          || ((ativos.get(v) ?? 0) === (ativos.get(a.v) ?? 0) && (opcoes.penalidades?.get(v) ?? 0) < (opcoes.penalidades?.get(a.v) ?? 0))));
      if (!melhor || melhorQue(melhor)) melhor = { v, fit: f.fit, pos };
    }
    if (!melhor) continue;
    chamadas.push({
      funcao: "core_repassar_deal", p_opportunity_id: l.opportunity_id, p_para_vendedor: melhor.v, p_origem: "repasse_janela",
      p_execucao_id: execucaoId, p_fit_dono: arredondar(n.fit), p_fit_novo: arredondar(melhor.fit), p_posicao_top: melhor.pos, p_faixa_heat: n.heat_faixa,
    });
    (listas.get(melhor.v) ?? listas.set(melhor.v, []).get(melhor.v)!).push(PESOS.fit * melhor.fit + PESOS.heat * n.heat + n.bonus);
    ativos.set(melhor.v, (ativos.get(melhor.v) ?? 0) + 1);
    ativos.set(l.vendedor_nome, (ativos.get(l.vendedor_nome) ?? 1) - 1);
  }
  return { chamadas, filaManager: fila };
}

/* ------------------------------------------------------------------ lead novo durante a semana */

export interface Rota { vendedor: string | null; conversao: number | null; fit: number | null; motivo: string }

/**
 * Lead novo vai ao vendedor de maior conversão no perfil (taxa dele + média dos desvios do lead), já descontada a
 * penalidade (em pontos percentuais). Fora: quem está no limite da semana, quem não tem 1+ característica do lead
 * com 10+ fechados e quem teria FIT abaixo de 50. Empate: menos ativos. Ninguém passa: fila do manager.
 */
export function rotearLeadNovo(
  lead: Pick<Lead, "produto_nome" | "serie" | "setor" | "faixa_receita" | "faixa_funcionarios" | "conta_nome" | "sede">,
  cel: Celulas, ativos: Map<string, number>, limiteSemana: number, penalidades: Map<string, number> = new Map(),
): Rota {
  let melhor: { v: string; conv: number; fit: number } | null = null;
  for (const v of [...cel.taxaVendedor.keys()].sort()) {
    if ((ativos.get(v) ?? 0) >= limiteSemana) continue;
    const f = fitDoLead(cel, v, lead);
    if (!f.usadas.length || f.fit < 50) continue;
    let soma = 0;
    for (const u of f.usadas) soma += u.desvio;
    const conv = cel.taxaVendedor.get(v)! + soma / f.usadas.length - (penalidades.get(v) ?? 0) / 100;
    if (!melhor || conv > melhor.conv || (conv === melhor.conv && (ativos.get(v) ?? 0) < (ativos.get(melhor.v) ?? 0))) melhor = { v, conv, fit: f.fit };
  }
  if (!melhor) return { vendedor: null, conversao: null, fit: null, motivo: "Nenhum vendedor passou nas travas: fila do manager." };
  return {
    vendedor: melhor.v, conversao: arredondar(melhor.conv * 100, 1), fit: arredondar(melhor.fit),
    motivo: melhor.fit >= FIT_FURAR_FILA ? "Lead novo de alto encaixe: entra no topo das prioridades." : "Lead novo roteado pela maior conversão no perfil.",
  };
}
