import "server-only";
// Repositório em arquivo: a RESERVA do app quando o banco não está configurado ou não responde.
// Lê data/base.json. Por padrão é somente leitura; com G4_ESCRITA_EM_MEMORIA=1 aceita escritas em memória
// (somem ao reiniciar), para rodar o app sem banco. As regras seguem as functions do banco.
import { CONFIG } from "@/lib/config";
import { diasEntre, faixaNota, icone as calcIcone, nomePadrao, ROTULO_ESTAGIO, ROTULO_MOTIVO } from "@/lib/calculos";
import { atendeConta, atendeDeal } from "@/lib/filtro/aplicar";
import type { Etiquetas } from "@/lib/filtro/etiquetas";
import type { Contexto, Modo } from "@/lib/filtro/interpretar";
import { funil, numerosPainel } from "@/lib/painel";
import type {
  Comentario, ContaDetalhe, ContaVisao, Contato, CorTag, DealDetalhe, DealVisao, Escopo, Estagio,
  EventoLinhaDoTempo, MotivoPerda, Pagina, Papel, Porte, Prioridade, Tag, TipoAcao, Usuario,
} from "@/lib/tipos";
import { ErroCRM } from "./banco";
import { carregarBase, type Base, type ContaBase, type DealBase } from "./fonte";


interface DealEstado extends DealBase {
  contatoId: number | null;
  motivoPerda: MotivoPerda | null;
  ultimoContatoCrm: string | null;
  criadoEm: string | null;
  atualizadoEm: string;
  atualizadoPor: string | null;
}
interface AcaoReg { id: number; dealId: string; usuarioId: number; autor: string; acao: TipoAcao; tipoAtividade: string | null; nota: string | null; data: string; criadoEm: string; diaReal: string; desfeitaEm: string | null }
interface ComentarioReg { id: number; dealId: string; usuarioId: number; autor: string; texto: string; data: string; criadoEm: string; editado: boolean; removidoEm: string | null; removidoPor: number | null }
interface DealTagReg { id: number; dealId: string; tagId: number; criadoEm: string; removidaEm: string | null }
interface EventoReg { dealId: string; data: string; momento: string; tipo: EventoLinhaDoTempo["tipo"]; descricao: string; autor: string }
interface Desfazer { usuarioId: number; expira: number; aplicar: () => void }
interface LoteReg { id: number; usuarioId: number; papel: Papel; criadoEm: number; desfeito: boolean; reverter: (() => boolean)[] }

interface Estado {
  base: Base;
  equipe: Map<string, { manager: string; regiao: string }>;
  produtos: Map<string, { serie: string; preco: number }>;
  contas: Map<string, ContaBase>;
  deals: Map<string, DealEstado>;
  usuarios: Usuario[];
  acoes: AcaoReg[];
  comentarios: ComentarioReg[];
  tags: Tag[];
  dealTags: DealTagReg[];
  contatos: Contato[];
  eventos: EventoReg[];
  prioridades: Map<string, string[]>;
  repasses: { dealId: string; de: string; para: string; data: string }[];
  desfazer: Map<string, Desfazer>;
  lotes: Map<number, LoteReg>;
  seq: number;
}

const ABERTOS: Estagio[] = ["Prospecting", "Engaging"];
const g = globalThis as unknown as { __g4Estado?: Promise<Estado> };

function criarUsuarios(base: Base): Usuario[] {
  const managers = [...new Set(base.equipe.map((e) => e.manager))].sort();
  const vendedores = [...base.equipe].sort((a, b) => a.vendedor.localeCompare(b.vendedor));
  const regiaoManager = new Map(base.equipe.map((e) => [e.manager, e.regiao]));
  // Mesmos ids do banco: 1 = sistema, 2 = admin, vendedores em ordem alfabética e depois os managers.
  let id = 3;
  return [
    { id: 2, papel: "admin", nome: "Admin" },
    ...vendedores.map((v) => ({ id: id++, papel: "vendedor" as const, nome: v.vendedor, vendedor: v.vendedor, manager: v.manager, regiao: v.regiao })),
    ...managers.map((m) => ({ id: id++, papel: "manager" as const, nome: m, manager: m, regiao: regiaoManager.get(m) })),
  ];
}

async function iniciar(): Promise<Estado> {
  const base = await carregarBase();
  // Versão inicial fixa: a mesma em qualquer instância do servidor. (Com a hora de partida de cada
  // instância, a versão lida numa não batia com a de outra, e toda mudança dava "alterado por outra pessoa".)
  const agora = `${base.dataReferencia}T00:00:00.000Z`;
  return {
    base,
    equipe: new Map(base.equipe.map((e) => [e.vendedor, { manager: e.manager, regiao: e.regiao }])),
    produtos: new Map(base.produtos.map((p) => [p.nome, { serie: p.serie, preco: p.preco }])),
    contas: new Map(base.contas.map((c) => [c.nome, { ...c }])),
    deals: new Map(base.deals.map((d) => [d.id, { ...d, contatoId: null, motivoPerda: null, ultimoContatoCrm: null, criadoEm: null, atualizadoEm: agora, atualizadoPor: null }])),
    usuarios: criarUsuarios(base),
    acoes: [], comentarios: [], tags: [], dealTags: [], contatos: [], eventos: [], repasses: [],
    prioridades: new Map(), desfazer: new Map(), lotes: new Map(), seq: 1,
  };
}

async function estado(): Promise<Estado> {
  g.__g4Estado ??= iniciar().catch((e) => {
    g.__g4Estado = undefined;
    throw e;
  });
  return g.__g4Estado;
}

/** Na reserva em arquivo, escrever só com a opção explícita de memória. */
export const escritaEmMemoria = (): boolean => process.env.G4_ESCRITA_EM_MEMORIA === "1";
export const dataNegocio = (): string => CONFIG.dataReferencia;
const diaReal = (): string => new Date().toLocaleDateString("sv-SE", { timeZone: CONFIG.fusoHorario });
const agoraIso = (): string => new Date().toISOString();

// ---------------------------------------------------------------------------------------------- leitura

interface Indices { tags: Map<string, Tag[]>; comentarios: Map<string, number> }

function indices(est: Estado): Indices {
  const tagPorId = new Map(est.tags.map((t) => [t.id, t]));
  const tags = new Map<string, Tag[]>();
  for (const dt of est.dealTags) {
    if (dt.removidaEm) continue;
    const t = tagPorId.get(dt.tagId);
    if (t) tags.set(dt.dealId, [...(tags.get(dt.dealId) ?? []), t]);
  }
  const comentarios = new Map<string, number>();
  for (const c of est.comentarios) if (!c.removidoEm) comentarios.set(c.dealId, (comentarios.get(c.dealId) ?? 0) + 1);
  return { tags, comentarios };
}

function visao(est: Estado, d: DealEstado, idx: Indices): DealVisao {
  const eq = est.equipe.get(d.vendedor);
  const prod = est.produtos.get(d.produto);
  const conta = d.conta ? est.contas.get(d.conta) : undefined;
  const nota = est.base.notas.get(d.id);
  const contato = d.contatoId ? est.contatos.find((c) => c.id === d.contatoId) : undefined;
  const hoje = dataNegocio();
  const aberto = ABERTOS.includes(d.estagio);
  const dias = aberto && d.dataAbertura ? diasEntre(d.dataAbertura, hoje) : null;
  const preco = prod?.preco ?? 0;
  const score = nota?.score ?? null;
  return {
    id: d.id,
    nome: d.nome,
    estagio: d.estagio,
    vendedor: d.vendedor,
    manager: eq?.manager ?? "—",
    regiao: eq?.regiao ?? "—",
    produto: d.produto,
    serie: prod?.serie ?? "",
    preco,
    conta: d.conta,
    setor: conta?.setor ?? null,
    porte: conta?.porte ?? null,
    contato: contato ? { id: contato.id, nome: contato.nome, cargo: contato.cargo } : null,
    dataAbertura: d.dataAbertura,
    diasDesdeAbertura: dias,
    ultimoContato: d.ultimoContatoCrm,
    closeDate: d.closeDate,
    closeValue: d.closeValue,
    motivoPerda: d.motivoPerda,
    fit: nota?.fit ?? null,
    heat: nota?.heat ?? null,
    bonus: nota?.bonus ?? null,
    score,
    faixaNota: faixaNota(score),
    acaoSugerida: nota?.acaoSugerida ?? null,
    marcadores: nota?.marcadores ?? [],
    valorEsperado: aberto ? (nota?.valorEsperado ?? preco) : null,
    valorPeloPrecoDeTabela: aberto && nota?.valorEsperado == null,
    icone: calcIcone(d.estagio, dias, preco, d.ultimoContatoCrm ? diasEntre(d.ultimoContatoCrm, hoje) : null),
    tags: idx.tags.get(d.id) ?? [],
    qtdComentarios: idx.comentarios.get(d.id) ?? 0,
    atualizadoDepoisDaNota: false,
    criadoEm: d.criadoEm,
    atualizadoEm: d.atualizadoEm,
  };
}

export function noEscopo(e: Escopo, d: { vendedor: string; manager: string; regiao: string }): boolean {
  if (e.papel === "vendedor") return d.vendedor === e.vendedor;
  if (e.papel === "manager") return d.manager === e.manager && (!e.vendedor || d.vendedor === e.vendedor);
  return (!e.regiao || d.regiao === e.regiao) && (!e.manager || d.manager === e.manager) && (!e.vendedor || d.vendedor === e.vendedor);
}

export function escopoDe(u: Usuario, filtros: { regiao?: string; manager?: string; vendedor?: string } = {}): Escopo {
  if (u.papel === "vendedor") return { papel: "vendedor", vendedor: u.vendedor };
  if (u.papel === "manager") return { papel: "manager", manager: u.manager, vendedor: filtros.vendedor };
  return { papel: "admin", ...filtros };
}

export async function dealsDoEscopo(e: Escopo): Promise<DealVisao[]> {
  const est = await estado();
  const idx = indices(est);
  const out: DealVisao[] = [];
  for (const d of est.deals.values()) {
    const v = visao(est, d, idx);
    if (noEscopo(e, v)) out.push(v);
  }
  return out;
}

const rankIcone = (d: DealVisao) => (d.icone === "super_hot" ? 0 : d.icone === "em_risco" ? 1 : d.icone === "esfriou" ? 3 : 2);

export type Ordem = "nota" | "valor" | "dias_sem_contato" | "dias_aberto" | "abertura" | "fechamento" | "vendedor" | "lead" | "padrao_leads";

export function ordenar(lista: DealVisao[], ordem: Ordem): DealVisao[] {
  const nn = (v: number | null, nulo = -Infinity) => v ?? nulo;
  const porNota = (a: DealVisao, b: DealVisao) =>
    nn(b.score) - nn(a.score) || rankIcone(a) - rankIcone(b) || nn(b.valorEsperado ?? b.closeValue) - nn(a.valorEsperado ?? a.closeValue) || a.id.localeCompare(b.id);
  const cmp: Record<Ordem, (a: DealVisao, b: DealVisao) => number> = {
    nota: porNota,
    valor: (a, b) => nn(b.valorEsperado ?? b.closeValue) - nn(a.valorEsperado ?? a.closeValue) || a.id.localeCompare(b.id),
    dias_sem_contato: (a, b) => (a.ultimoContato ?? "").localeCompare(b.ultimoContato ?? "") || porNota(a, b),
    dias_aberto: (a, b) => (a.dataAbertura ?? "9").localeCompare(b.dataAbertura ?? "9") || porNota(a, b),
    abertura: (a, b) => (b.dataAbertura ?? "").localeCompare(a.dataAbertura ?? "") || porNota(a, b),
    fechamento: (a, b) => (b.closeDate ?? "").localeCompare(a.closeDate ?? "") || porNota(a, b),
    vendedor: (a, b) => a.vendedor.localeCompare(b.vendedor) || porNota(a, b),
    lead: (a, b) => a.nome.localeCompare(b.nome),
    padrao_leads: (a, b) => {
      const fa = ABERTOS.includes(a.estagio) ? 0 : 1;
      const fb = ABERTOS.includes(b.estagio) ? 0 : 1;
      return fa - fb || (fa === 0 ? porNota(a, b) : (b.closeDate ?? "").localeCompare(a.closeDate ?? ""));
    },
  };
  return [...lista].sort(cmp[ordem]);
}

export async function buscarDeals(e: Escopo, et: Etiquetas, ordem: Ordem, offset = 0, limite: number = CONFIG.porPagina): Promise<Pagina<DealVisao>> {
  const hoje = dataNegocio();
  const lista = ordenar((await dealsDoEscopo(e)).filter((d) => atendeDeal(d, et, hoje)), ordem);
  return { total: lista.length, linhas: lista.slice(offset, offset + limite) };
}

export async function colunasPipeline(e: Escopo, et: Etiquetas, ordem: Ordem, limite: number) {
  const hoje = dataNegocio();
  const abertos = (await dealsDoEscopo(e)).filter((d) => ABERTOS.includes(d.estagio) && atendeDeal(d, et, hoje));
  return (["Prospecting", "Engaging"] as const).map((estagio) => {
    const l = ordenar(abertos.filter((d) => d.estagio === estagio), ordem);
    return { estagio, total: l.length, valor: l.reduce((a, d) => a + (d.valorEsperado ?? 0), 0), cartoes: l.slice(0, limite) };
  });
}

export async function contextoFiltro(modo: Modo, u: Usuario): Promise<Contexto> {
  const est = await estado();
  const vend = u.papel === "manager" ? est.base.equipe.filter((x) => x.manager === u.manager).map((x) => x.vendedor) : est.base.equipe.map((x) => x.vendedor);
  return {
    modo,
    papel: u.papel,
    hoje: dataNegocio(),
    vendedores: vend,
    managers: [...new Set(est.base.equipe.map((x) => x.manager))],
    empresas: [...est.contas.keys()],
    produtos: [...est.produtos.keys()],
    tags: est.tags.map((t) => t.nome),
    sedes: [...new Set([...est.contas.values()].map((c) => c.sede).filter((s): s is string => !!s))],
  };
}

export function transicoes(estagio: Estagio, papel: Papel): Estagio[] {
  if (estagio === "Prospecting") return ["Engaging", "Lost"];
  if (estagio === "Engaging") return ["Won", "Lost"];
  return (CONFIG.papeisReabrir as readonly string[]).includes(papel) ? ["Engaging"] : [];
}

export async function detalheDeal(id: string, u: Usuario): Promise<DealDetalhe> {
  const est = await estado();
  const d = est.deals.get(id);
  if (!d) throw new ErroCRM("GS404", "Este deal não foi encontrado.");
  const deal = visao(est, d, indices(est));
  const nota = est.base.notas.get(id);
  const eventos = est.eventos.filter((e) => e.dealId === id);
  const linha: EventoLinhaDoTempo[] = [];
  const mudouPara = (alvo: string) => eventos.some((e) => e.tipo === "estagio" && e.descricao.endsWith(alvo));
  if (d.dataAbertura && !mudouPara(ROTULO_ESTAGIO.Engaging)) linha.push({ data: d.dataAbertura, momento: null, tipo: "aberto", descricao: "Aberto (entrou em negociação)", autor: null, desfeito: false });
  if ((d.estagio === "Won" || d.estagio === "Lost") && d.closeDate && !eventos.some((e) => e.tipo === "estagio" && e.descricao.includes(`→ ${ROTULO_ESTAGIO[d.estagio]}`)))
    linha.push({ data: d.closeDate, momento: null, tipo: "fechado", descricao: d.estagio === "Won" ? `Ganho: US$ ${(d.closeValue ?? 0).toLocaleString("pt-BR")}` : "Perdido", autor: null, desfeito: false });
  for (const e of eventos) linha.push({ data: e.data, momento: e.momento, tipo: e.tipo, descricao: e.descricao, autor: e.autor, desfeito: false });
  const rotuloAcao: Record<TipoAcao, string> = { liguei: "Liguei", requalifiquei: "Requalifiquei", desisti: "Desisti", prioridade_feita: "Feito na prioridade do dia", prioridade_pulada: "Pulado na prioridade do dia" };
  for (const a of est.acoes.filter((x) => x.dealId === id))
    linha.push({
      data: a.data, momento: a.criadoEm, tipo: "acao", autor: a.autor, desfeito: !!a.desfeitaEm,
      descricao: (a.tipoAtividade ? `${CONFIG.tiposAtividade.find((t) => t.codigo === a.tipoAtividade)?.rotulo ?? a.tipoAtividade} (prioridade do dia)` : rotuloAcao[a.acao]) + (a.nota ? ` — "${a.nota}"` : ""),
    });
  const comentarios = est.comentarios.filter((c) => c.dealId === id && !c.removidoEm);
  for (const c of comentarios) linha.push({ data: c.data, momento: c.criadoEm, tipo: "comentario", descricao: c.texto + (c.editado ? " (editado)" : ""), autor: c.autor, desfeito: false });
  linha.sort((a, b) => (a.data ?? "").localeCompare(b.data ?? "") || (a.momento ?? "").localeCompare(b.momento ?? ""));
  return {
    deal,
    componentes: nota?.componentes ?? [],
    motivos: nota?.motivos ?? [],
    linhaDoTempo: linha,
    comentarios: comentarios
      .map<Comentario>((c) => ({ id: c.id, autorId: c.usuarioId, autor: c.autor, texto: c.texto, data: c.data, criadoEm: c.criadoEm, editado: c.editado }))
      .sort((a, b) => b.criadoEm.localeCompare(a.criadoEm)),
    contatoCompleto: d.contatoId ? (est.contatos.find((c) => c.id === d.contatoId) ?? null) : null,
    transicoes: transicoes(d.estagio, u.papel),
  };
}

export async function painel(e: Escopo) {
  const deals = await dealsDoEscopo(e);
  const est = await estado();
  return { numeros: numerosPainel(deals, dataNegocio()), funil: funil(deals), notasDisponiveis: est.base.notasDisponiveis };
}

export async function porVendedor(e: Escopo) {
  const est = await estado();
  const deals = await dealsDoEscopo(e);
  const hoje = diaReal();
  const nomes = [...new Set(est.base.equipe.filter((x) => noEscopo(e, { vendedor: x.vendedor, manager: x.manager, regiao: x.regiao })).map((x) => x.vendedor))].sort();
  return nomes.map((v) => {
    const meus = deals.filter((d) => d.vendedor === v);
    const u = est.usuarios.find((x) => x.vendedor === v);
    return {
      vendedor: v,
      abertos: meus.filter((d) => ABERTOS.includes(d.estagio)).length,
      emRisco: meus.filter((d) => d.icone === "em_risco").length,
      esfriaram: meus.filter((d) => d.icone === "esfriou").length,
      prioridadesFeitas: est.acoes.filter((a) => a.usuarioId === u?.id && a.acao === "prioridade_feita" && a.diaReal === hoje && !a.desfeitaEm).length,
      perdidosPorFaltaDeAtendimento: est.repasses.filter((r) => r.de === v).length,
    };
  });
}

// -------------------------------------------------------------------------------------- prioridades do dia

function candidatosPrioridade(est: Estado, u: Usuario, jaNaLista: Set<string>): DealVisao[] {
  const idx = indices(est);
  const hoje = diaReal();
  const tocadosHoje = new Set(est.acoes.filter((a) => a.usuarioId === u.id && a.diaReal === hoje && !a.desfeitaEm).map((a) => a.dealId));
  const lista: DealVisao[] = [];
  for (const d of est.deals.values()) {
    if (!ABERTOS.includes(d.estagio) || jaNaLista.has(d.id) || tocadosHoje.has(d.id)) continue;
    const v = visao(est, d, idx);
    const ok =
      u.papel === "vendedor" ? v.vendedor === u.vendedor
      : u.papel === "manager" ? v.manager === u.manager && (v.icone === "super_hot" || v.icone === "em_risco")
      : v.icone === "super_hot" || v.icone === "em_risco";
    if (ok) lista.push(v);
  }
  const furaFila = (d: DealVisao) => (d.criadoEm?.startsWith(hoje) && (d.fit ?? 0) >= CONFIG.fitMinimoFurarFila ? 0 : 1);
  return lista.sort((a, b) =>
    furaFila(a) - furaFila(b) ||
    (u.papel === "vendedor"
      ? (b.score ?? -1) - (a.score ?? -1) || rankIcone(a) - rankIcone(b) || (b.valorEsperado ?? 0) - (a.valorEsperado ?? 0)
      : (b.valorEsperado ?? 0) - (a.valorEsperado ?? 0) || (b.score ?? -1) - (a.score ?? -1)) ||
    a.id.localeCompare(b.id));
}

async function montarPrioridades(u: Usuario, qtd: number) {
  const est = await estado();
  const chave = `${u.id}|${diaReal()}`;
  const atual = est.prioridades.get(chave) ?? [];
  const novos = candidatosPrioridade(est, u, new Set(atual)).slice(0, qtd).map((d) => d.id);
  est.prioridades.set(chave, [...atual, ...novos]);
}

export async function prioridadesDoDia(u: Usuario): Promise<Prioridade[]> {
  const est = await estado();
  const hoje = diaReal();
  const chave = `${u.id}|${hoje}`;
  if (!est.prioridades.has(chave)) await montarPrioridades(u, CONFIG.metaPrioridadesDia);
  const idx = indices(est);
  const ids = est.prioridades.get(chave) ?? [];
  return ids.flatMap((id, i) => {
    const d = est.deals.get(id);
    if (!d) return [];
    const minhas = est.acoes.filter((a) => a.dealId === id && a.usuarioId === u.id && !a.desfeitaEm);
    const ultima = minhas.filter((a) => a.diaReal === hoje).at(-1);
    const marcada = !ultima ? null : ultima.acao === "prioridade_feita" ? "feita" : ultima.acao === "prioridade_pulada" ? "pulada" : "contato";
    const diasPulado = new Set(minhas.filter((a) => a.acao === "prioridade_pulada" && diasEntre(a.diaReal, hoje) < CONFIG.diasPuladoAlerta).map((a) => a.diaReal)).size;
    return [{ posicao: i + 1, deal: visao(est, d, idx), marcada, puladoDiasSeguidos: diasPulado } as Prioridade];
  });
}

export async function puxarMaisPrioridades(u: Usuario, qtd = 5): Promise<void> {
  await montarPrioridades(u, Math.min(Math.max(qtd, 1), 20));
}

// ----------------------------------------------------------------------------------------------- contas

function contaVisao(c: ContaBase, deals: DealEstado[]): ContaVisao {
  const meus = deals.filter((d) => d.conta === c.nome);
  const ganhos = meus.filter((d) => d.estagio === "Won");
  return {
    nome: c.nome,
    setor: c.setor,
    porte: c.porte,
    funcionarios: c.funcionarios,
    receitaMilhoes: c.receitaMilhoes,
    anoFundacao: c.anoFundacao,
    sede: c.sede,
    empresaMae: c.empresaMae,
    dealsAbertos: meus.filter((d) => ABERTOS.includes(d.estagio)).length,
    compras: ganhos.length,
    perdas: meus.filter((d) => d.estagio === "Lost").length,
    receitaGanha: ganhos.reduce((a, d) => a + (d.closeValue ?? 0), 0),
    padrao: null,
    bonus: null,
  };
}

export type OrdemContas = "receita" | "compras" | "abertos" | "bonus" | "nome";

export async function buscarContas(et: Etiquetas, ordem: OrdemContas = "receita"): Promise<ContaVisao[]> {
  const est = await estado();
  const deals = [...est.deals.values()];
  const lista = [...est.contas.values()].map((c) => contaVisao(c, deals)).filter((c) => atendeConta(c, et));
  const cmp: Record<OrdemContas, (a: ContaVisao, b: ContaVisao) => number> = {
    receita: (a, b) => b.receitaGanha - a.receitaGanha,
    compras: (a, b) => b.compras - a.compras,
    abertos: (a, b) => b.dealsAbertos - a.dealsAbertos,
    bonus: (a, b) => (b.bonus ?? -1) - (a.bonus ?? -1),
    nome: (a, b) => a.nome.localeCompare(b.nome),
  };
  return lista.sort((a, b) => cmp[ordem](a, b) || a.nome.localeCompare(b.nome));
}

export async function detalheConta(nome: string, escopo: Escopo): Promise<ContaDetalhe> {
  const est = await estado();
  const c = est.contas.get(nome);
  if (!c) throw new ErroCRM("GS404", "Esta empresa não foi encontrada.");
  const deals = [...est.deals.values()].filter((d) => d.conta === nome);
  const meses = new Map<string, { ganhos: number; perdidos: number }>();
  for (const d of deals) {
    if (!d.closeDate || (d.estagio !== "Won" && d.estagio !== "Lost")) continue;
    const m = d.closeDate.slice(0, 7);
    const r = meses.get(m) ?? { ganhos: 0, perdidos: 0 };
    if (d.estagio === "Won") r.ganhos++; else r.perdidos++;
    meses.set(m, r);
  }
  const ganhos = deals.filter((d) => d.estagio === "Won").sort((a, b) => (a.closeDate ?? "").localeCompare(b.closeDate ?? ""));
  const porProduto = new Map<string, { compras: number; receita: number }>();
  for (const d of ganhos) {
    const r = porProduto.get(d.produto) ?? { compras: 0, receita: 0 };
    r.compras++;
    r.receita += d.closeValue ?? 0;
    porProduto.set(d.produto, r);
  }
  const idx = indices(est);
  return {
    conta: contaVisao(c, [...est.deals.values()]),
    porMes: [...meses.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([mes, v]) => ({ mes, ...v })),
    produtos: [...porProduto.entries()].map(([produto, v]) => ({ produto, ...v })).sort((a, b) => b.receita - a.receita),
    ticketMedio: ganhos.length ? Math.round(ganhos.reduce((a, d) => a + (d.closeValue ?? 0), 0) / ganhos.length) : null,
    primeiraCompra: ganhos[0]?.closeDate ?? null,
    ultimaCompra: ganhos.at(-1)?.closeDate ?? null,
    padrao: null,
    // Os totais históricos são da empresa inteira; os deals abertos seguem o escopo do perfil.
    abertos: ordenar(deals.filter((d) => ABERTOS.includes(d.estagio)).map((d) => visao(est, d, idx)).filter((d) => noEscopo(escopo, d)), "nota"),
  };
}

// ----------------------------------------------------------------------------------------------- escrita

function exigirEscrita() {
  if (!escritaEmMemoria()) throw new ErroCRM("GS503", "Modo somente leitura: mudanças estão desligadas agora.");
}

function exigirPapel(u: Usuario, papeis: readonly string[], frase: string) {
  if (!papeis.includes(u.papel)) throw new ErroCRM("GS403", frase);
}

function travar(est: Estado, id: string, versao?: string | null): DealEstado {
  const d = est.deals.get(id);
  if (!d) throw new ErroCRM("GS404", "Este deal não foi encontrado.");
  if (versao && d.atualizadoEm !== versao)
    throw new ErroCRM("GS409", `Este deal foi alterado por ${d.atualizadoPor ?? "outra pessoa"}. Recarregue para ver a versão atual.`, { alteradoPor: d.atualizadoPor, alteradoEm: d.atualizadoEm });
  return d;
}

function tocar(d: DealEstado, u: Usuario) {
  d.atualizadoEm = agoraIso();
  d.atualizadoPor = u.nome;
}

function registrarDesfazer(est: Estado, u: Usuario, aplicar: () => void): string {
  const token = `d${est.seq++}`;
  est.desfazer.set(token, { usuarioId: u.id, expira: Date.now() + 60_000, aplicar });
  return token;
}

function evento(est: Estado, u: Usuario, dealId: string, tipo: EventoReg["tipo"], descricao: string) {
  est.eventos.push({ dealId, data: dataNegocio(), momento: agoraIso(), tipo, descricao, autor: u.nome });
}

export async function desfazer(u: Usuario, token: string): Promise<void> {
  exigirEscrita();
  const est = await estado();
  const r = est.desfazer.get(token);
  if (!r || r.usuarioId !== u.id || r.expira < Date.now()) throw new ErroCRM("GS422", "O prazo para desfazer passou.");
  est.desfazer.delete(token);
  r.aplicar();
}

export async function mudarEstagio(
  u: Usuario, id: string, versao: string | null, para: Estagio,
  extra: { valor?: number | null; motivo?: MotivoPerda | null; motivoDetalhe?: string | null } = {},
): Promise<{ deal: DealVisao; desfazer: string }> {
  exigirEscrita();
  const est = await estado();
  const d = travar(est, id, versao);
  const antes = { ...d };
  const hoje = dataNegocio();
  if (d.estagio === para) throw new ErroCRM("GS422", "O deal já está neste estágio.");
  if (d.estagio === "Prospecting" && para === "Engaging") {
    d.estagio = "Engaging";
    d.dataAbertura ??= hoje;
  } else if (d.estagio === "Engaging" && para === "Won") {
    if (!extra.valor || extra.valor <= 0 || !Number.isInteger(extra.valor)) throw new ErroCRM("GS400", "Informe o valor de fechamento: um número inteiro maior que zero.");
    Object.assign(d, { estagio: "Won", closeDate: hoje, closeValue: extra.valor, motivoPerda: null });
  } else if (ABERTOS.includes(d.estagio) && para === "Lost") {
    Object.assign(d, { estagio: "Lost", closeDate: hoje, closeValue: 0, motivoPerda: extra.motivo ?? null });
  } else if ((d.estagio === "Won" || d.estagio === "Lost") && para === "Engaging") {
    exigirPapel(u, CONFIG.papeisReabrir, "Reabrir um deal encerrado é feito pelo manager ou pelo admin.");
    Object.assign(d, { estagio: "Engaging", closeDate: null, closeValue: null, motivoPerda: null, dataAbertura: d.dataAbertura ?? hoje });
  } else {
    throw new ErroCRM("GS422", `Mudar de ${ROTULO_ESTAGIO[d.estagio]} para ${ROTULO_ESTAGIO[para]} não é permitido.`);
  }
  tocar(d, u);
  const sufixo = d.estagio === "Won" ? ` (US$ ${(d.closeValue ?? 0).toLocaleString("pt-BR")})` : d.estagio === "Lost" && d.motivoPerda ? ` (${ROTULO_MOTIVO[d.motivoPerda]})` : "";
  evento(est, u, id, "estagio", `Estágio: ${ROTULO_ESTAGIO[antes.estagio]} → ${ROTULO_ESTAGIO[d.estagio]}${sufixo}`);
  const versaoNova = d.atualizadoEm;
  const token = registrarDesfazer(est, u, () => {
    if (d.atualizadoEm !== versaoNova) throw new ErroCRM("GS409", "O deal mudou depois; não dá mais para desfazer.");
    Object.assign(d, antes, { atualizadoEm: agoraIso(), atualizadoPor: u.nome });
    est.eventos.pop();
  });
  return { deal: visao(est, d, indices(est)), desfazer: token };
}

export async function atualizarDeal(u: Usuario, id: string, versao: string | null, campos: { nome?: string; conta?: string; contatoId?: number | null }) {
  exigirEscrita();
  const est = await estado();
  const d = travar(est, id, versao);
  const antes = { ...d };
  const partes: string[] = [];
  if (campos.nome !== undefined) {
    const n = campos.nome.trim();
    if (n.length < 1 || n.length > 120) throw new ErroCRM("GS400", "O nome do deal precisa ter de 1 a 120 caracteres.");
    d.nome = n;
    partes.push("Nome alterado");
  }
  if (campos.conta !== undefined) {
    if (!est.contas.has(campos.conta)) throw new ErroCRM("GS400", "Empresa não cadastrada.");
    d.conta = campos.conta;
    partes.push(`Empresa: ${campos.conta}`);
  }
  if (campos.contatoId !== undefined) {
    const c = campos.contatoId === null ? null : est.contatos.find((x) => x.id === campos.contatoId);
    if (campos.contatoId !== null && !c) throw new ErroCRM("GS404", "Contato não encontrado.");
    if (c?.conta && c.conta !== d.conta) throw new ErroCRM("GS422", "O contato é de outra empresa.");
    d.contatoId = campos.contatoId;
    partes.push("Contato principal alterado");
  }
  tocar(d, u);
  if (partes.length) evento(est, u, id, "dados", partes.join("; "));
  const versaoNova = d.atualizadoEm;
  const token = registrarDesfazer(est, u, () => {
    if (d.atualizadoEm !== versaoNova) throw new ErroCRM("GS409", "O deal mudou depois; não dá mais para desfazer.");
    Object.assign(d, antes, { atualizadoEm: agoraIso(), atualizadoPor: u.nome });
  });
  return { deal: visao(est, d, indices(est)), desfazer: token };
}

export async function salvarContato(u: Usuario, dados: { id?: number; conta: string | null; nome: string; cargo?: string | null; email?: string | null; telefone?: string | null }, dealId?: string, versao?: string | null) {
  exigirEscrita();
  const est = await estado();
  if (!dados.nome.trim()) throw new ErroCRM("GS400", "Informe o nome do contato.");
  if (dados.email && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(dados.email)) throw new ErroCRM("GS400", "E-mail em formato inválido.");
  let c = dados.id ? est.contatos.find((x) => x.id === dados.id) : undefined;
  if (dados.id && !c) throw new ErroCRM("GS404", "Contato não encontrado.");
  if (!c) {
    c = { id: est.seq++, conta: dados.conta, nome: dados.nome.trim(), cargo: dados.cargo ?? null, email: dados.email ?? null, telefone: dados.telefone ?? null };
    est.contatos.push(c);
  } else Object.assign(c, { nome: dados.nome.trim(), cargo: dados.cargo ?? null, email: dados.email ?? null, telefone: dados.telefone ?? null });
  if (dealId) await atualizarDeal(u, dealId, versao ?? null, { contatoId: c.id });
  return c;
}

export async function registrarAcao(u: Usuario, dealId: string, acao: "liguei" | "requalifiquei" | "desisti", nota?: string | null) {
  exigirEscrita();
  const est = await estado();
  const d = travar(est, dealId);
  if (!ABERTOS.includes(d.estagio)) throw new ErroCRM("GS422", "Só é possível registrar ação em deal aberto.");
  if (nota && nota.length > 280) throw new ErroCRM("GS400", "A nota pode ter até 280 caracteres.");
  const r: AcaoReg = { id: est.seq++, dealId, usuarioId: u.id, autor: u.nome, acao, tipoAtividade: null, nota: nota?.trim() || null, data: dataNegocio(), criadoEm: agoraIso(), diaReal: diaReal(), desfeitaEm: null };
  est.acoes.push(r);
  recalcularContato(est, d);
  const token = registrarDesfazer(est, u, () => {
    r.desfeitaEm = agoraIso();
    recalcularContato(est, d);
  });
  return { desfazer: token };
}

function recalcularContato(est: Estado, d: DealEstado) {
  const contaComoContato = (a: AcaoReg) =>
    (CONFIG.acoesContato as readonly string[]).includes(a.acao) ||
    (a.acao === "prioridade_feita" && !!CONFIG.tiposAtividade.find((t) => t.codigo === a.tipoAtividade)?.contaComoContato);
  const contatos = est.acoes.filter((a) => a.dealId === d.id && !a.desfeitaEm && contaComoContato(a));
  d.ultimoContatoCrm = contatos.map((a) => a.data).sort().at(-1) ?? null;
}

export async function comentar(u: Usuario, dealId: string, texto: string) {
  exigirEscrita();
  const est = await estado();
  travar(est, dealId);
  const t = texto.trim();
  if (t.length < 1 || t.length > 1000) throw new ErroCRM("GS400", "O comentário precisa ter de 1 a 1.000 caracteres.");
  if (/<[a-zA-Z/!]/.test(t)) throw new ErroCRM("GS400", "O comentário não pode ter HTML.");
  const c: ComentarioReg = { id: est.seq++, dealId, usuarioId: u.id, autor: u.nome, texto: t, data: dataNegocio(), criadoEm: agoraIso(), editado: false, removidoEm: null, removidoPor: null };
  est.comentarios.push(c);
  return { id: c.id };
}

/** "Apagar" na tela = remoção lógica: some da tela e da linha do tempo, fica guardado. */
export async function removerComentario(u: Usuario, id: number) {
  exigirEscrita();
  const est = await estado();
  const c = est.comentarios.find((x) => x.id === id && !x.removidoEm);
  if (!c) throw new ErroCRM("GS404", "Comentário não encontrado.");
  if (c.usuarioId !== u.id && u.papel === "vendedor") throw new ErroCRM("GS403", "Só o autor, o manager ou o admin apagam o comentário.");
  c.removidoEm = agoraIso();
  c.removidoPor = u.id;
  const token = registrarDesfazer(est, u, () => {
    c.removidoEm = null;
    c.removidoPor = null;
  });
  return { desfazer: token };
}

export async function criarTag(u: Usuario, nome: string, cor: CorTag) {
  exigirEscrita();
  exigirPapel(u, CONFIG.papeisCriarTag, "Tags novas são criadas pelo manager ou pelo admin.");
  const est = await estado();
  const n = nome.trim().replace(/^#/, "");
  if (n.length < 1 || n.length > 30) throw new ErroCRM("GS400", "O nome da tag precisa ter de 1 a 30 caracteres.");
  if (est.tags.some((t) => t.nome.toLowerCase() === n.toLowerCase())) throw new ErroCRM("GS422", "Já existe uma tag com esse nome.");
  const t: Tag = { id: est.seq++, nome: n, cor, ativa: true };
  est.tags.push(t);
  return t;
}

export async function listarTags(): Promise<Tag[]> {
  return (await estado()).tags.filter((t) => t.ativa);
}

function aplicarTagInterno(est: Estado, u: Usuario, dealId: string, tagId: number): DealTagReg | null {
  if (est.dealTags.some((x) => x.dealId === dealId && x.tagId === tagId && !x.removidaEm)) return null;
  if (est.dealTags.filter((x) => x.dealId === dealId && !x.removidaEm).length >= CONFIG.maxTagsPorDeal) return null;
  const r: DealTagReg = { id: est.seq++, dealId, tagId, criadoEm: agoraIso(), removidaEm: null };
  est.dealTags.push(r);
  const t = est.tags.find((x) => x.id === tagId);
  evento(est, u, dealId, "tag", `Tag #${t?.nome}`);
  return r;
}

export async function aplicarTag(u: Usuario, dealId: string, tagId: number) {
  exigirEscrita();
  const est = await estado();
  travar(est, dealId);
  if (!est.tags.some((t) => t.id === tagId && t.ativa)) throw new ErroCRM("GS404", "Tag não encontrada.");
  const r = aplicarTagInterno(est, u, dealId, tagId);
  if (!r && est.dealTags.filter((x) => x.dealId === dealId && !x.removidaEm).length >= CONFIG.maxTagsPorDeal)
    throw new ErroCRM("GS422", `Este deal já tem o máximo de ${CONFIG.maxTagsPorDeal} tags.`);
  return { desfazer: r ? registrarDesfazer(est, u, () => { r.removidaEm = agoraIso(); }) : null };
}

export async function removerTag(u: Usuario, dealId: string, tagId: number) {
  exigirEscrita();
  const est = await estado();
  const r = est.dealTags.find((x) => x.dealId === dealId && x.tagId === tagId && !x.removidaEm);
  if (!r) throw new ErroCRM("GS404", "Este deal não tem essa tag.");
  r.removidaEm = agoraIso();
  const t = est.tags.find((x) => x.id === tagId);
  evento(est, u, dealId, "tag", `Tag removida: #${t?.nome}`);
  return { desfazer: registrarDesfazer(est, u, () => { r.removidaEm = null; }) };
}

export type TipoLote = "aplicar_tag" | "remover_tag" | "comentar" | "avancar_estagio" | "encerrar_perdido";

export async function executarLote(u: Usuario, tipo: TipoLote, ids: string[], p: { tagId?: number; texto?: string; motivo?: MotivoPerda | null }) {
  exigirEscrita();
  const est = await estado();
  const unicos = [...new Set(ids)];
  if (!unicos.length) throw new ErroCRM("GS400", "Selecione pelo menos um lead.");
  if (unicos.length > CONFIG.limiteLote) throw new ErroCRM("GS400", `Selecione até ${CONFIG.limiteLote} por vez; refine o filtro.`);
  if ((tipo === "aplicar_tag" || tipo === "remover_tag") && !est.tags.some((t) => t.id === p.tagId)) throw new ErroCRM("GS404", "Tag não encontrada.");
  if (tipo === "comentar" && (!p.texto?.trim() || p.texto.length > 1000 || /<[a-zA-Z/!]/.test(p.texto)))
    throw new ErroCRM("GS400", "Escreva um comentário de 1 a 1.000 caracteres, sem HTML.");
  const lote: LoteReg = { id: est.seq++, usuarioId: u.id, papel: u.papel, criadoEm: Date.now(), desfeito: false, reverter: [] };
  let aplicados = 0;
  let pulados = 0;
  for (const id of unicos) {
    const d = est.deals.get(id);
    if (!d) { pulados++; continue; }
    if (tipo === "aplicar_tag" && p.tagId) {
      const r = aplicarTagInterno(est, u, id, p.tagId);
      if (r) { aplicados++; lote.reverter.push(() => (r.removidaEm ? false : ((r.removidaEm = agoraIso()), true))); } else pulados++;
    } else if (tipo === "remover_tag") {
      const r = est.dealTags.find((x) => x.dealId === id && x.tagId === p.tagId && !x.removidaEm);
      if (r) { r.removidaEm = agoraIso(); aplicados++; lote.reverter.push(() => (r.removidaEm = null, true)); } else pulados++;
    } else if (tipo === "comentar" && p.texto) {
      const c: ComentarioReg = { id: est.seq++, dealId: id, usuarioId: u.id, autor: u.nome, texto: p.texto.trim(), data: dataNegocio(), criadoEm: agoraIso(), editado: false, removidoEm: null, removidoPor: null };
      est.comentarios.push(c);
      aplicados++;
      lote.reverter.push(() => (c.removidoEm ? false : ((c.removidoEm = agoraIso()), (c.removidoPor = u.id), true)));
    } else if ((tipo === "avancar_estagio" && d.estagio === "Prospecting") || (tipo === "encerrar_perdido" && ABERTOS.includes(d.estagio))) {
      const antes = { ...d };
      if (tipo === "avancar_estagio") Object.assign(d, { estagio: "Engaging", dataAbertura: d.dataAbertura ?? dataNegocio() });
      else Object.assign(d, { estagio: "Lost", closeDate: dataNegocio(), closeValue: 0, motivoPerda: p.motivo ?? null });
      tocar(d, u);
      evento(est, u, id, "estagio", `Estágio: ${ROTULO_ESTAGIO[antes.estagio]} → ${ROTULO_ESTAGIO[d.estagio]} (em lote)`);
      const versao = d.atualizadoEm;
      aplicados++;
      lote.reverter.push(() => {
        if (d.atualizadoEm !== versao) return false;
        Object.assign(d, antes, { atualizadoEm: agoraIso(), atualizadoPor: u.nome });
        return true;
      });
    } else pulados++;
  }
  est.lotes.set(lote.id, lote);
  return { loteId: lote.id, aplicados, pulados };
}

export async function desfazerLote(u: Usuario, loteId: number) {
  exigirEscrita();
  const est = await estado();
  const l = est.lotes.get(loteId);
  if (!l) throw new ErroCRM("GS404", "Lote não encontrado.");
  if (l.desfeito) throw new ErroCRM("GS422", "Este lote já foi desfeito.");
  if (l.usuarioId !== u.id && u.papel === "vendedor") throw new ErroCRM("GS403", "Só quem aplicou o lote, o manager ou o admin podem desfazer.");
  if (Date.now() - l.criadoEm > 24 * 3_600_000) throw new ErroCRM("GS422", "O prazo para desfazer este lote (24 h) passou.");
  let restaurados = 0;
  let pulados = 0;
  for (const r of [...l.reverter].reverse()) if (r()) restaurados++; else pulados++;
  l.desfeito = true;
  return { restaurados, pulados };
}

export async function marcarPrioridade(
  u: Usuario, dealId: string, resultado: "feita" | "pulada",
  registro: { tipoAtividade?: string | null; comentario?: string | null } = {},
) {
  exigirEscrita();
  const est = await estado();
  const hoje = diaReal();
  // A lista do dia pode não existir nesta instância do servidor (ela é montada na primeira leitura).
  // Sem isto, o ✓ respondia "não está na sua lista de hoje" mesmo com o deal na tela.
  if (!est.prioridades.has(`${u.id}|${hoje}`)) await montarPrioridades(u, CONFIG.metaPrioridadesDia);
  if (!(est.prioridades.get(`${u.id}|${hoje}`) ?? []).includes(dealId)) {
    const d0 = est.deals.get(dealId);
    if (!d0 || !ABERTOS.includes(d0.estagio)) throw new ErroCRM("GS404", "Este deal não está na sua lista de hoje.");
    est.prioridades.set(`${u.id}|${hoje}`, [...(est.prioridades.get(`${u.id}|${hoje}`) ?? []), dealId]);
  }
  if (est.acoes.some((a) => a.dealId === dealId && a.usuarioId === u.id && a.diaReal === hoje && !a.desfeitaEm && a.acao.startsWith("prioridade")))
    throw new ErroCRM("GS422", "Este item já foi marcado hoje.");
  const d = travar(est, dealId);
  if (!ABERTOS.includes(d.estagio)) throw new ErroCRM("GS422", "Este deal já foi encerrado.");
  const comentario = registro.comentario?.trim() || null;
  const tipo = registro.tipoAtividade || null;
  if (resultado === "feita") {
    // Decisão 37: o ✓ registra o que foi feito (tipo de atividade e comentário obrigatórios; o horário é salvo).
    if (!tipo || !CONFIG.tiposAtividade.some((t) => t.codigo === tipo)) throw new ErroCRM("GS400", "Escolha o tipo de atividade.");
    if (!comentario) throw new ErroCRM("GS400", "Escreva o que foi feito.");
  }
  if (comentario && comentario.length > 280) throw new ErroCRM("GS400", "O comentário pode ter até 280 caracteres.");
  const r: AcaoReg = {
    id: est.seq++, dealId, usuarioId: u.id, autor: u.nome, acao: resultado === "feita" ? "prioridade_feita" : "prioridade_pulada",
    tipoAtividade: resultado === "feita" ? tipo : null, nota: comentario, data: dataNegocio(), criadoEm: agoraIso(), diaReal: hoje, desfeitaEm: null,
  };
  est.acoes.push(r);
  recalcularContato(est, d);
  return { desfazer: registrarDesfazer(est, u, () => { r.desfeitaEm = agoraIso(); recalcularContato(est, d); }) };
}

export async function criarDeal(u: Usuario, dados: { produto: string; conta?: string | null; vendedor?: string | null; estagio: "Prospecting" | "Engaging"; nome?: string | null }) {
  exigirEscrita();
  const est = await estado();
  if (!est.produtos.has(dados.produto)) throw new ErroCRM("GS400", "Produto não encontrado no catálogo.");
  if (dados.conta && !est.contas.has(dados.conta)) throw new ErroCRM("GS400", "Empresa não cadastrada.");
  let vendedor = dados.vendedor || (u.papel === "vendedor" ? u.vendedor : undefined);
  let regra = "escolhido";
  if (!vendedor) {
    // Sem FIT ainda (o score não chegou): o vendedor com menos deals abertos no escopo.
    const abertos = new Map<string, number>();
    for (const d of est.deals.values()) if (ABERTOS.includes(d.estagio)) abertos.set(d.vendedor, (abertos.get(d.vendedor) ?? 0) + 1);
    const cand = est.base.equipe.filter((e) => u.papel !== "manager" || e.manager === u.manager).map((e) => e.vendedor);
    vendedor = cand.sort((a, b) => (abertos.get(a) ?? 0) - (abertos.get(b) ?? 0) || a.localeCompare(b))[0];
    regra = "menos deals abertos";
  }
  if (!vendedor || !est.equipe.has(vendedor)) throw new ErroCRM("GS400", "Vendedor não encontrado no time.");
  const letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
  let id = "";
  do id = Array.from({ length: 8 }, () => letras[Math.floor(Math.random() * 36)]).join(""); while (est.deals.has(id));
  const d: DealEstado = {
    id, nome: dados.nome?.trim() || nomePadrao(dados.conta ?? null, dados.produto), vendedor, produto: dados.produto, conta: dados.conta ?? null,
    estagio: dados.estagio, dataAbertura: dados.estagio === "Engaging" ? dataNegocio() : null, closeDate: null, closeValue: null,
    contatoId: null, motivoPerda: null, ultimoContatoCrm: null, criadoEm: agoraIso(), atualizadoEm: agoraIso(), atualizadoPor: u.nome,
  };
  est.deals.set(id, d);
  evento(est, u, id, "criado", `Cadastrado no CRM; vendedor: ${vendedor} (${regra})`);
  return { id };
}

export async function salvarConta(u: Usuario, dados: { nome: string; novo: boolean; setor?: string | null; funcionarios?: number | null; receitaMilhoes?: number | null; anoFundacao?: number | null; sede?: string | null; empresaMae?: string | null }) {
  exigirEscrita();
  const est = await estado();
  const nome = dados.nome.trim();
  if (nome.length < 1 || nome.length > 120) throw new ErroCRM("GS400", "O nome da empresa precisa ter de 1 a 120 caracteres.");
  if (dados.empresaMae && !est.contas.has(dados.empresaMae)) throw new ErroCRM("GS400", "A empresa-mãe não está cadastrada.");
  if (dados.empresaMae === nome) throw new ErroCRM("GS400", "A empresa não pode ser mãe dela mesma.");
  const porte = (f: number | null | undefined): Porte | null => (f == null ? null : f <= 1428 ? "pequena" : f <= 4540 ? "media" : "grande");
  if (dados.novo) {
    if (est.contas.has(nome)) throw new ErroCRM("GS422", "Já existe uma empresa com esse nome.");
    est.contas.set(nome, { nome, setor: dados.setor ?? null, funcionarios: dados.funcionarios ?? null, receitaMilhoes: dados.receitaMilhoes ?? null, anoFundacao: dados.anoFundacao ?? null, sede: dados.sede ?? null, empresaMae: dados.empresaMae ?? null, porte: porte(dados.funcionarios) });
  } else {
    const c = est.contas.get(nome);
    if (!c) throw new ErroCRM("GS404", "Esta empresa não foi encontrada.");
    Object.assign(c, { setor: dados.setor ?? null, funcionarios: dados.funcionarios ?? null, receitaMilhoes: dados.receitaMilhoes ?? null, anoFundacao: dados.anoFundacao ?? null, sede: dados.sede ?? null, empresaMae: dados.empresaMae ?? null, porte: porte(dados.funcionarios) });
  }
  return { nome };
}

// ------------------------------------------------------------------------------------------------ apoio

export async function listarUsuarios(): Promise<Usuario[]> {
  return (await estado()).usuarios;
}

export async function usuarioPorId(id: number): Promise<Usuario | undefined> {
  return (await estado()).usuarios.find((u) => u.id === id);
}

export async function listarProdutos() {
  return (await estado()).base.produtos;
}

export async function listarEquipe() {
  return (await estado()).base.equipe;
}

export async function contagemPorVendedor(): Promise<Map<string, number>> {
  const est = await estado();
  const m = new Map<string, number>();
  for (const d of est.deals.values()) if (ABERTOS.includes(d.estagio)) m.set(d.vendedor, (m.get(d.vendedor) ?? 0) + 1);
  return m;
}

export async function notasDisponiveis(): Promise<boolean> {
  return (await estado()).base.notasDisponiveis;
}
