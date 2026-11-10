/**
 * Regra do lead score em TypeScript (decisões 28 a 40). Referência: solution/scoring/regra.py.
 * NOTA = 0,70 × FIT + 0,30 × HEAT + BONUS, de 0 a 120.
 *
 * Funções puras: entram linhas do banco, saem linhas para inserir. Nada aqui lê ou grava no banco.
 * A paridade com o Python é testada deal a deal (tests/score-paridade.test.ts).
 */

export const VERSAO = "lead-score-1.0";
export const PESOS = { fit: 0.7, heat: 0.3, bonus_max: 20 } as const;

export const ENCOLHIMENTO = 20;
export const MINIMO_CASOS = 10;
export const CORTE_DESTAQUE = 0.03;
export const JANELA_MESES = 3;
export const DIMENSOES = ["produto", "serie", "setor", "receita", "funcionarios", "empresa", "sede"] as const;
export type Dimensao = (typeof DIMENSOES)[number];

export const FAIXAS_HEAT: readonly [number | null, number, string][] = [
  [1, 100, "até 1 dia"], [7, 85, "2 a 7 dias"], [15, 70, "8 a 15 dias"], [30, 55, "16 a 30 dias"],
  [60, 40, "31 a 60 dias"], [90, 25, "61 a 90 dias"], [180, 10, "91 a 180 dias"], [null, 0, "181 dias ou mais"],
];
export const HEAT_SEM_DATA = 50;
export const FATOR_CONTATO: readonly [number | null, number][] = [[7, 1.0], [14, 0.8], [30, 0.5], [null, 0.2]];
export const RISCO_ESFRIAR: readonly [number, number] = [107, 138];
export const DESISTIR_ACIMA = 276;
export const FIT_FURAR_FILA = 75;
export const BONUS_HISTORICO = [0, 5, 10] as const;
export const BONUS_JANELA = 10;

export const SETORES: Record<string, string> = {
  employment: "recrutamento", entertainment: "entretenimento", finance: "finanças", marketing: "marketing",
  medical: "saúde", retail: "varejo", services: "serviços", software: "software",
  technology: "tecnologia", telecommunications: "telecomunicações",
};
const PORTE: Record<string, string> = { pequena: "pequena", media: "média", grande: "grande" };

/* ------------------------------------------------------------------ linhas do banco */

export interface LinhaDeal {
  opportunity_id: string;
  vendedor_nome: string;
  produto_nome: string;
  conta_nome: string | null;
  estagio: "Prospecting" | "Engaging" | "Won" | "Lost" | string;
  data_abertura: string | null;
  close_date: string | null;
  close_value: number | null;
  ultimo_contato_em: string | null;
  criado_em: string | null;
}
export interface LinhaConta { nome: string; setor: string | null; receita_milhoes: number | string | null; funcionarios: number | null; pais: string | null }
export interface LinhaProduto { nome: string; serie: string; preco: number }

/* ------------------------------------------------------------------ utilitários com a mesma aritmética do Python */

const DIA = 86_400_000;
/** Dia (UTC) de uma data "AAAA-MM-DD" ou de um instante ISO. */
export function dia(s: string): number {
  if (/^\d{4}-\d{2}-\d{2}$/.test(s.slice(0, 10)) && (s.length === 10 || s[10] === "T" || s[10] === " ") && !/[zZ+]|-\d\d:\d\d$/.test(s.slice(10))) {
    return Date.UTC(+s.slice(0, 4), +s.slice(5, 7) - 1, +s.slice(8, 10)) / DIA;
  }
  return Math.floor(Date.parse(s) / DIA);
}
export function diaIso(d: number): string {
  return new Date(d * DIA).toISOString().slice(0, 10);
}
/** referencia − N meses (dia preso ao fim do mês, como pandas.DateOffset) + 1 dia. */
export function janela(referencia: string): [number, number] {
  const r = new Date(dia(referencia) * DIA);
  const y = r.getUTCFullYear(), m = r.getUTCMonth() - JANELA_MESES, d = r.getUTCDate();
  const ultimo = new Date(Date.UTC(y, m + 1, 0)).getUTCDate();
  const ini = Date.UTC(y, m, Math.min(d, ultimo)) / DIA + 1;
  return [ini, dia(referencia)];
}

/** round() do Python: meio para o par, sobre o valor binário exato. */
export function arredondar(x: number, casas = 0): number {
  // expansão decimal exata do double (60 casas bastam para |x| < 2^20 com 52 bits de mantissa)
  const neg = x < 0;
  const [int = "0", dec = ""] = Math.abs(x).toFixed(60).split(".");
  const manter = dec.slice(0, casas), resto = dec.slice(casas);
  const digitos = (int + manter).split("").map(Number);
  const ultimo = digitos[digitos.length - 1] ?? 0;
  const sobe = resto[0]! > "5" || (resto[0] === "5" && (/[1-9]/.test(resto.slice(1)) || ultimo % 2 === 1));
  if (sobe) {
    let i = digitos.length - 1;
    while (i >= 0) { const di = digitos[i] ?? 0; if (di < 9) { digitos[i] = di + 1; break; } digitos[i] = 0; i -= 1; }
    if (i < 0) digitos.unshift(1);
  }
  const s = digitos.join("");
  const v = Number(casas ? `${s.slice(0, s.length - casas)}.${s.slice(s.length - casas)}` : s);
  return neg ? -v : v;
}

/** Quantil linear do numpy/pandas (com a correção de lerp do numpy). */
function quantil(valores: number[], q: number): number {
  const a = [...valores].sort((x, y) => x - y);
  const pos = (a.length - 1) * q;
  const lo = Math.floor(pos), hi = Math.min(lo + 1, a.length - 1);
  const t = pos - lo;
  const va = a[lo]!, vb = a[hi]!;
  const diff = vb - va;
  return t >= 0.5 ? vb - diff * (1 - t) : va + diff * t;
}

function faixa(valores: number[]): (v: number) => string {
  const c0 = quantil(valores, 1 / 3), c1 = quantil(valores, 2 / 3);
  return (v) => (v <= c0 ? "pequena" : v <= c1 ? "media" : "grande");
}

/* ------------------------------------------------------------------ preparo */

export interface Lead extends LinhaDeal {
  serie: string;
  preco: number;
  setor: string | null;
  faixa_receita: string | null;
  faixa_funcionarios: string | null;
  sede: string | null;
}

export function preparar(deals: LinhaDeal[], contas: LinhaConta[], produtos: LinhaProduto[]): Lead[] {
  const fr = faixa(contas.map((c) => Number(c.receita_milhoes)));
  const ff = faixa(contas.map((c) => Number(c.funcionarios)));
  const conta = new Map(contas.map((c) => [c.nome, {
    setor: c.setor, faixa_receita: fr(Number(c.receita_milhoes)), faixa_funcionarios: ff(Number(c.funcionarios)),
    sede: c.pais === "United States" ? "EUA" : "fora dos EUA",
  }]));
  const prod = new Map(produtos.map((p) => [p.nome, p]));
  return deals.map((d) => {
    const p = prod.get(d.produto_nome);
    const c = d.conta_nome ? conta.get(d.conta_nome) : undefined;
    return {
      ...d, serie: p?.serie ?? "", preco: Number(p?.preco ?? 0),
      setor: c?.setor ?? null, faixa_receita: c?.faixa_receita ?? null, faixa_funcionarios: c?.faixa_funcionarios ?? null, sede: c?.sede ?? null,
    };
  });
}

function valorDe(l: Pick<Lead, "produto_nome" | "serie" | "setor" | "faixa_receita" | "faixa_funcionarios" | "conta_nome" | "sede">, dim: Dimensao): string | null {
  switch (dim) {
    case "produto": return l.produto_nome;
    case "serie": return l.serie;
    case "setor": return l.setor;
    case "receita": return l.faixa_receita;
    case "funcionarios": return l.faixa_funcionarios;
    case "empresa": return l.conta_nome;
    case "sede": return l.sede;
  }
}

/* ------------------------------------------------------------------ FIT (semanal) */

export interface Celula { vendedor: string; dim: Dimensao; valor: string; n: number; ganhos: number; taxa_encolhida: number; desvio: number; ok: boolean }
export interface Celulas {
  taxaVendedor: Map<string, number>;
  fechadosVendedor: Map<string, number>;
  tabela: Map<string, Celula>;
  destaque: Map<string, Celula>;
  janela: [number, number];
}
const chave = (v: string, d: string, x: string) => `${v}\u0000${d}\u0000${x}`;

export function celulas(leads: Lead[], referencia: string): Celulas {
  const [ini, fim] = janela(referencia);
  const f = leads.filter((d) => (d.estagio === "Won" || d.estagio === "Lost") && d.close_date !== null
    && dia(d.close_date) >= ini && dia(d.close_date) <= fim);
  const ag = new Map<string, { s: number; n: number }>();
  for (const d of f) {
    const a = ag.get(d.vendedor_nome) ?? { s: 0, n: 0 };
    a.s += d.estagio === "Won" ? 1 : 0; a.n += 1; ag.set(d.vendedor_nome, a);
  }
  const taxa = new Map([...ag].map(([v, a]) => [v, a.s / a.n]));
  const cont = new Map<string, { vendedor: string; dim: Dimensao; valor: string; ganhos: number; n: number }>();
  for (const dim of DIMENSOES) {
    for (const d of f) {
      const v = valorDe(d, dim);
      if (v === null || v === undefined) continue;
      const k = chave(d.vendedor_nome, dim, String(v));
      const c = cont.get(k) ?? { vendedor: d.vendedor_nome, dim, valor: String(v), ganhos: 0, n: 0 };
      c.ganhos += d.estagio === "Won" ? 1 : 0; c.n += 1; cont.set(k, c);
    }
  }
  const tabela = new Map<string, Celula>();
  for (const [k, c] of cont) {
    const tv = taxa.get(c.vendedor)!;
    const te = (c.ganhos + ENCOLHIMENTO * tv) / (c.n + ENCOLHIMENTO);
    const ok = c.n >= MINIMO_CASOS;
    tabela.set(k, { ...c, taxa_encolhida: te, ok, desvio: ok ? te - tv : 0 });
  }
  const destaque = new Map<string, Celula>();
  for (const c of tabela.values()) {
    if (!c.ok) continue;
    const atual = destaque.get(c.vendedor);
    if (!atual || c.taxa_encolhida > atual.taxa_encolhida
      || (c.taxa_encolhida === atual.taxa_encolhida && (c.dim < atual.dim || (c.dim === atual.dim && c.valor < atual.valor)))) {
      destaque.set(c.vendedor, c);
    }
  }
  return { taxaVendedor: taxa, fechadosVendedor: new Map([...ag].map(([v, a]) => [v, a.n])), tabela, destaque, janela: [ini, fim] };
}

export function temDestaque(cel: Celulas, vendedor: string): boolean {
  const d = cel.destaque.get(vendedor);
  return !!d && d.desvio >= CORTE_DESTAQUE;
}

export interface ItemFit { dim: Dimensao; valor: string; n: number; ganhos: number; taxa_encolhida: number | null; desvio: number }
export interface DetalheFit { fit: number; sem_destaque: boolean; sem_historico: boolean; usadas: ItemFit[]; fora: ItemFit[]; media: number; destaque: Celula | null }

type CaracteristicasLead = Pick<Lead, "produto_nome" | "serie" | "setor" | "faixa_receita" | "faixa_funcionarios" | "conta_nome" | "sede">;

export function fitDoLead(cel: Celulas, vendedor: string, lead: CaracteristicasLead): DetalheFit {
  const usadas: ItemFit[] = [], fora: ItemFit[] = [];
  for (const dim of DIMENSOES) {
    const v = valorDe(lead, dim);
    if (v === null || v === undefined || v === "") continue;
    const c = cel.tabela.get(chave(vendedor, dim, String(v)));
    const item: ItemFit = { dim, valor: String(v), n: c?.n ?? 0, ganhos: c?.ganhos ?? 0, taxa_encolhida: c ? c.taxa_encolhida : null, desvio: c ? c.desvio : 0 };
    (c && c.ok ? usadas : fora).push(item);
  }
  // sem destaque ou sem histórico na janela (decisão 49: os sem histórico entram com FIT 50 em todo lead)
  if (!temDestaque(cel, vendedor)) return { fit: 50, sem_destaque: true, sem_historico: !cel.taxaVendedor.has(vendedor), usadas, fora, media: 0, destaque: null };
  const dest = cel.destaque.get(vendedor)!;
  let soma = 0;
  for (const u of usadas) soma += u.desvio;
  const media = usadas.length ? soma / usadas.length : 0;
  const fit = Math.min(100, Math.max(0, 50 + (50 * media) / dest.desvio));
  return { fit, sem_destaque: false, sem_historico: false, usadas, fora, media, destaque: dest };
}

/* ------------------------------------------------------------------ HEAT (diário) */

export function faixaHeat(dias: number | null): [number, string] {
  if (dias === null) return [HEAT_SEM_DATA, "sem data de abertura"];
  for (const [limite, pts, rot] of FAIXAS_HEAT) if (limite === null || dias <= limite) return [pts, rot];
  throw new Error("faixa");
}
export function fatorContato(diasSemContato: number | null): number {
  if (diasSemContato === null) return 1.0;
  for (const [limite, f] of FATOR_CONTATO) if (limite === null || diasSemContato <= limite) return f;
  throw new Error("fator");
}

/* ------------------------------------------------------------------ BONUS (semanal) */

export interface PadraoConta {
  conta_nome: string; compras_ganhas: number; receita_ganha: number; ultima_compra: string;
  terco: 0 | 1 | 2; bonus_historico: number; bonus_janela: number; bonus: number; na_janela: boolean;
}

export function padroesConta(leads: Lead[], referencia: string): { padroes: Map<string, PadraoConta>; cortes: [number, number] } {
  const ref = dia(referencia);
  const g = new Map<string, { n: number; r: number; u: number }>();
  for (const d of leads) {
    if (d.estagio !== "Won" || !d.conta_nome || d.close_date === null || dia(d.close_date) > ref) continue;
    const x = g.get(d.conta_nome) ?? { n: 0, r: 0, u: -Infinity };
    x.n += 1; x.r += Number(d.close_value ?? 0); x.u = Math.max(x.u, dia(d.close_date)); g.set(d.conta_nome, x);
  }
  const receitas = [...g.values()].map((x) => x.r);
  const c0 = quantil(receitas, 1 / 3), c1 = quantil(receitas, 2 / 3);
  const padroes = new Map<string, PadraoConta>();
  for (const [nome, x] of g) {
    const terco = (x.r > c1 ? 2 : x.r > c0 ? 1 : 0) as 0 | 1 | 2;
    const bh = BONUS_HISTORICO[terco];
    // janela de compra por calendário: nenhuma empresa passa no teste nestes dados (validacao.md); fica pronta e vale 0
    padroes.set(nome, { conta_nome: nome, compras_ganhas: x.n, receita_ganha: x.r, ultima_compra: diaIso(x.u), terco, bonus_historico: bh,
      bonus_janela: 0, bonus: bh, na_janela: false });
  }
  return { padroes, cortes: [c0, c1] };
}

export function explicacaoConta(p: PadraoConta): string {
  const terco = { 2: "entre as que mais compram (terço de cima da receita ganha): +10", 1: "no terço do meio da receita ganha: +5",
    0: "no terço de baixo da receita ganha: +0" }[p.terco];
  const receita = Math.trunc(p.receita_ganha).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `${p.compras_ganhas} compras ganhas. US$ ${receita} em receita; empresa ${terco}. `
    + "Sem época de compra própria: compra no mesmo calendário das outras empresas.";
}

/* ------------------------------------------------------------------ nota do dia */

export interface DealNota {
  opportunity_id: string; vendedor_nome: string; produto_nome: string; conta_nome: string | null; estagio: string;
  cohort: string; fit: number; heat: number; heat_faixa: string; heat_pontos: number; fator_contato: number;
  bonus: number; bonus_historico: number; bonus_janela: number; terco: number | null; nota: number;
  acao_sugerida: "focar" | "requalificar" | "desistir"; dias: number | null; valor_esperado: number;
  marcadores: string[]; detalhe_fit: DetalheFit; ativo: boolean; motivos: [string, string][];
}

export function notaDoDeal(l: Lead, dono: string, cel: Celulas, padroes: Map<string, PadraoConta>, referencia: string): DealNota {
  const ref = dia(referencia);
  const f = fitDoLead(cel, dono, l);
  const dias = l.data_abertura ? ref - dia(l.data_abertura) : null;
  const [pts, rot] = faixaHeat(dias);
  const diasContato = l.ultimo_contato_em ? ref - dia(l.ultimo_contato_em) : null;
  const fator = fatorContato(diasContato);
  const heat = pts * fator;
  const p = l.conta_nome ? padroes.get(l.conta_nome) : undefined;
  const bh = p ? p.bonus_historico : 0, bj = p ? p.bonus_janela : 0;
  const bonus = bh + bj;
  const nota = PESOS.fit * f.fit + PESOS.heat * heat + bonus;
  const marcadores: string[] = [];
  if (dias !== null && dias >= RISCO_ESFRIAR[0] && dias <= RISCO_ESFRIAR[1]) marcadores.push("risco_esfriar");
  if (dias !== null && dias > RISCO_ESFRIAR[1]) marcadores.push("esfriou");
  if (l.criado_em && diasContato === null && f.fit >= FIT_FURAR_FILA && ref - dia(l.criado_em) > 1) marcadores.push("atendimento_atrasado");
  const acao = dias !== null && dias > DESISTIR_ACIMA ? "desistir" : dias !== null && dias > RISCO_ESFRIAR[1] ? "requalificar" : "focar";
  const d: DealNota = {
    opportunity_id: l.opportunity_id, vendedor_nome: dono, produto_nome: l.produto_nome, conta_nome: l.conta_nome, estagio: l.estagio,
    cohort: `produto=${l.produto_nome}`, fit: f.fit, heat, heat_faixa: rot, heat_pontos: pts, fator_contato: fator, bonus,
    bonus_historico: bh, bonus_janela: bj, terco: p ? p.terco : null, nota, acao_sugerida: acao, dias, valor_esperado: Math.trunc(l.preco),
    marcadores, detalhe_fit: f, ativo: l.estagio === "Prospecting" || (dias !== null && dias <= RISCO_ESFRIAR[1]), motivos: [],
  };
  d.motivos = motivos(d);
  return d;
}

export function rotulo(item: { dim: Dimensao; valor: string }): string {
  const { dim, valor: v } = item;
  switch (dim) {
    case "produto": return `produto ${v}`;
    case "serie": return `série ${v}`;
    case "setor": return `setor ${SETORES[v] ?? v}`;
    case "receita": return `empresa de receita ${PORTE[v] ?? v}`;
    case "funcionarios": return `empresa ${PORTE[v] ?? v} em funcionários`;
    case "empresa": return `empresa ${v}`;
    case "sede": return v === "EUA" ? "sede nos EUA" : "sede fora dos EUA";
  }
}

/** 2 ou 3 frases, em terceira pessoa (servem para o vendedor e para o manager). Mesmo texto da execução 7. */
export function motivos(l: DealNota): [string, string][] {
  const f = l.detalhe_fit;
  const saida: [string, string][] = [];
  if (f.sem_historico) saida.push(["fit", "Vendedor sem histórico: encaixe neutro (50)."]);
  else if (f.sem_destaque) saida.push(["fit", "O vendedor não tem um destaque com casos suficientes nos últimos 3 meses: o encaixe fica neutro (50)."]);
  else if (!f.usadas.length) saida.push(["fit", "Ainda não há casos suficientes para medir o encaixe deste lead com o vendedor: nota neutra (50)."]);
  else {
    const dest = f.destaque!;
    const bate = f.usadas.find((u) => u.dim === dest.dim && u.valor === dest.valor);
    if (bate) saida.push(["fit", `Encaixa no destaque do vendedor: ${rotulo(bate)} (${bate.ganhos} de ${bate.n} ganhos nos últimos 3 meses).`]);
    else if (f.media >= 0) {
      const u = f.usadas.reduce((a, b) => (b.desvio > a.desvio ? b : a));
      saida.push(["fit", `Encaixe acima da média do vendedor: ${rotulo(u)} (${u.ganhos} de ${u.n} ganhos nos últimos 3 meses).`]);
    } else {
      const u = f.usadas.reduce((a, b) => (b.desvio < a.desvio ? b : a));
      saida.push(["fit", `Fora do forte do vendedor: ${rotulo(u)} (${u.ganhos} de ${u.n} ganhos nos últimos 3 meses, abaixo da média dele).`]);
    }
  }
  if (l.conta_nome === null) saida.push(["fit", "Sem empresa cadastrada: o encaixe usa só o produto. Identifique a empresa."]);
  const dias = l.dias;
  if (dias === null) saida.push(["heat", "Ainda não começou: sem data de início. O relógio começa no primeiro contato."]);
  else if (dias > RISCO_ESFRIAR[1]) saida.push(["heat", `Parado há ${dias} dias: nenhum deal fechou depois de 138 dias. Requalifique ou encerre.`]);
  else if (dias >= RISCO_ESFRIAR[0]) saida.push(["heat", `Aberto há ${dias} dias: em risco de esfriar.`]);
  else if (dias <= 15) saida.push(["heat", `Aberto há ${dias} dias: atenda agora, a nota de tempo cai a cada faixa.`]);
  else saida.push(["heat", `Aberto há ${dias} dias: a nota de tempo já caiu para ${l.heat_pontos}.`]);
  if (l.conta_nome !== null && saida.length < 3) {
    if (l.bonus_historico === 10) saida.push(["bonus", "Empresa entre as que mais compram: +10."]);
    else if (l.bonus_historico === 5) saida.push(["bonus", "Empresa no terço do meio em compras: +5."]);
  }
  return saida.slice(0, 3);
}

export interface Componente { grupo: "fit" | "heat" | "bonus"; componente: string; pontos: number; maximo: number | null }

export function componentes(l: DealNota): Componente[] {
  const f = l.detalhe_fit, dest = f.destaque;
  const out: Componente[] = [
    { grupo: "fit", componente: "Encaixe com o vendedor (70%)", pontos: arredondar(PESOS.fit * l.fit, 2), maximo: 70 },
    { grupo: "heat", componente: "Tempo de atendimento (30%)", pontos: arredondar(PESOS.heat * l.heat, 2), maximo: 30 },
    { grupo: "heat", componente: `Faixa: ${l.heat_faixa}`, pontos: l.heat_pontos, maximo: 100 },
    { grupo: "heat", componente: "Fator de contato", pontos: l.fator_contato, maximo: 1 },
    { grupo: "bonus", componente: "Histórico da empresa", pontos: l.bonus_historico, maximo: 10 },
    { grupo: "bonus", componente: "Janela de compra", pontos: l.bonus_janela, maximo: 10 },
  ];
  for (const u of f.usadas) {
    out.push({ grupo: "fit", componente: `Desvio: ${rotulo(u)}`.slice(0, 60), pontos: arredondar(u.desvio * 100, 2),
      maximo: dest ? arredondar(dest.desvio * 100, 2) : null });
  }
  return out;
}

/* ------------------------------------------------------------------ FIT por vendedor e cohort (base do roteamento) */

export interface FitVendedor { vendedor_nome: string; cohort: string; produto_nome: string; taxa_media_movel: number; casos: number; fit: number; janela_inicio: string; janela_fim: string }

export function fitVendedores(cel: Celulas, produtos: LinhaProduto[]): FitVendedor[] {
  const out: FitVendedor[] = [];
  for (const v of [...cel.taxaVendedor.keys()].sort()) {
    for (const p of produtos) {
      const lead = { produto_nome: p.nome, serie: p.serie, setor: null, faixa_receita: null, faixa_funcionarios: null, conta_nome: null, sede: null };
      const f = fitDoLead(cel, v, lead);
      const cp = cel.tabela.get(chave(v, "produto", p.nome)), cs = cel.tabela.get(chave(v, "serie", p.serie));
      out.push({
        vendedor_nome: v, cohort: `produto=${p.nome}`, produto_nome: p.nome,
        taxa_media_movel: arredondar(cp && cp.ok ? cp.taxa_encolhida : cel.taxaVendedor.get(v)!, 4),
        casos: Math.max(cp?.n ?? 0, cs?.n ?? 0), fit: arredondar(f.fit),
        janela_inicio: diaIso(cel.janela[0]), janela_fim: diaIso(cel.janela[1]),
      });
    }
  }
  return out;
}

/* ------------------------------------------------------------------ execução completa (mesma saída da carga do Python) */

export interface LinhaScoreDeal {
  opportunity_id: string; vendedor_nome: string; cohort: string; fit: number; heat: number; bonus: number; score: number;
  nota_exata: number; acao_sugerida: string; dias_no_pipeline: number | null; valor_esperado: number; marcadores: string[];
  componentes: Componente[]; motivos: { ordem: number; grupo: string; texto: string }[];
}
export interface LinhaPadraoConta {
  conta_nome: string; compras_ganhas: number; receita_ganha: number; intervalo_tipico_dias: null; mes_habitual: null;
  ultima_compra: string; proxima_compra_esperada: null; na_janela: boolean; bonus: number; explicacao: string;
}

export function calcular(deals: LinhaDeal[], contas: LinhaConta[], produtos: LinhaProduto[], referencia: string) {
  const leads = preparar(deals, contas, produtos);
  const cel = celulas(leads, referencia);
  const { padroes, cortes } = padroesConta(leads, referencia);
  const notas = leads.filter((l) => l.estagio === "Prospecting" || l.estagio === "Engaging")
    .map((l) => notaDoDeal(l, l.vendedor_nome, cel, padroes, referencia));
  const linhas: LinhaScoreDeal[] = [...notas].sort((a, b) => (a.opportunity_id < b.opportunity_id ? -1 : 1)).map((n) => ({
    opportunity_id: n.opportunity_id, vendedor_nome: n.vendedor_nome, cohort: n.cohort, fit: arredondar(n.fit), heat: arredondar(n.heat),
    bonus: n.bonus, score: arredondar(n.nota), nota_exata: arredondar(n.nota, 4), acao_sugerida: n.acao_sugerida, dias_no_pipeline: n.dias,
    valor_esperado: n.valor_esperado, marcadores: n.marcadores, componentes: componentes(n),
    motivos: n.motivos.map(([g, t], i) => ({ ordem: i + 1, grupo: g, texto: t })),
  }));
  const contasOut: LinhaPadraoConta[] = [...padroes.values()].sort((a, b) => (a.conta_nome < b.conta_nome ? -1 : 1)).map((p) => ({
    conta_nome: p.conta_nome, compras_ganhas: p.compras_ganhas, receita_ganha: Math.trunc(p.receita_ganha), intervalo_tipico_dias: null,
    mes_habitual: null, ultima_compra: p.ultima_compra, proxima_compra_esperada: null, na_janela: p.na_janela, bonus: p.bonus,
    explicacao: explicacaoConta(p),
  }));
  return { notas, deals: linhas, fit_vendedores: fitVendedores(cel, produtos), padroes_conta: contasOut, celulas: cel, padroes, cortes, leads };
}

export function top5(notas: DealNota[]): DealNota[] {
  const por = new Map<string, DealNota[]>();
  for (const n of [...notas].sort((a, b) => b.nota - a.nota || b.heat - a.heat)) {
    const l = por.get(n.vendedor_nome) ?? [];
    if (l.length < 5) l.push(n);
    por.set(n.vendedor_nome, l);
  }
  return [...por.values()].flat();
}
