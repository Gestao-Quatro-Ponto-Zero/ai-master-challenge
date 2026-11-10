import "server-only";
// Repositório: a única porta das telas para ler e gravar.
//   - Banco configurado e respondendo: lê a view do banco e grava pelas functions do banco.
//   - Banco fora ou não configurado: lê a reserva em arquivo (data/base.json), em modo somente leitura.
// As contas das telas (filtro, ordenação, números do painel) são as mesmas funções puras nos dois modos.
import { cache } from "react";
import { CONFIG } from "@/lib/config";
import { atendeConta, atendeDeal } from "@/lib/filtro/aplicar";
import type { Etiquetas } from "@/lib/filtro/etiquetas";
import type { Contexto, Modo } from "@/lib/filtro/interpretar";
import { lotesRecentesPara } from "@/lib/lotes";
import { funil, numerosPainel } from "@/lib/painel";
import type { ContaDetalhe, ContaVisao, CorTag, DealDetalhe, DealVisao, Escopo, Estagio, LoteRecente, MotivoPerda, Pagina, Prioridade, Tag, Usuario } from "@/lib/tipos";
import { bancoAtivo, BancoFora, ErroCRM } from "./banco";
import * as A from "./repositorio-arquivo";
import * as B from "./repositorio-banco";

export { ErroCRM, estadoBanco, type CodigoErro } from "./banco";
export { escopoDe, noEscopo, ordenar, type Ordem, type OrdemContas, type TipoLote } from "./repositorio-arquivo";

/** Leitura: tenta o banco; se ele não responder, usa a reserva em arquivo (e marca o banco como fora). */
async function lendo<T>(noBanco: () => Promise<T>, naReserva: () => Promise<T>): Promise<T> {
  if (!bancoAtivo()) return naReserva();
  try {
    return await noBanco();
  } catch (e) {
    if (e instanceof BancoFora) return naReserva();
    throw e;
  }
}

/** Escrita: só no banco. Sem banco, só com a opção explícita de memória (rodar o app sem credenciais). */
async function gravando<T>(noBanco: () => Promise<T>, naMemoria: () => Promise<T>): Promise<T> {
  if (process.env.G4_SOMENTE_LEITURA === "1") throw new ErroCRM("GS503", "Modo somente leitura: mudanças estão desligadas agora.");
  if (bancoAtivo()) {
    try {
      return await noBanco();
    } catch (e) {
      if (e instanceof BancoFora) throw new ErroCRM("GS503", "Não foi possível salvar agora: o banco não respondeu. Tente de novo em alguns segundos.");
      throw e;
    }
  }
  if (A.escritaEmMemoria()) return naMemoria();
  throw new ErroCRM("GS503", "Modo somente leitura: o banco está indisponível e as mudanças estão desligadas.");
}

/** A tela mostra a faixa de somente leitura e esconde os botões de mudança. */
export function somenteLeitura(): boolean {
  return process.env.G4_SOMENTE_LEITURA === "1" || !(bancoAtivo() || A.escritaEmMemoria());
}

/** Sem banco, com a opção de memória ligada: as mudanças não sobrevivem ao reinício. */
export function escritaSoEmMemoria(): boolean {
  return !bancoAtivo() && A.escritaEmMemoria() && process.env.G4_SOMENTE_LEITURA !== "1";
}

/** De onde os dados estão vindo agora (aparece no rodapé e no /api/health). */
export function fonteDosDados(): "banco" | "arquivo" {
  return bancoAtivo() ? "banco" : "arquivo";
}

export const dataNegocio = A.dataNegocio;

// ---------------------------------------------------------------------------------------------- leitura

/** Deals do perfil. Dentro de um mesmo carregamento de página, a mesma consulta é feita uma vez só. */
const dealsDoEscopo = cache(async (chave: string): Promise<DealVisao[]> => {
  const { e, soAbertos } = JSON.parse(chave) as { e: Escopo; soAbertos: boolean };
  return lendo(
    () => B.dealsDoEscopo(e, soAbertos),
    async () => (await A.dealsDoEscopo(e)).filter((d) => !soAbertos || d.estagio === "Prospecting" || d.estagio === "Engaging"),
  );
});
const deals = (e: Escopo, soAbertos = false) => dealsDoEscopo(JSON.stringify({ e, soAbertos }));

export async function buscarDeals(e: Escopo, et: Etiquetas, ordem: A.Ordem, offset = 0, limite: number = CONFIG.porPagina): Promise<Pagina<DealVisao>> {
  const hoje = dataNegocio();
  const lista = A.ordenar((await deals(e)).filter((d) => atendeDeal(d, et, hoje)), ordem);
  return { total: lista.length, linhas: lista.slice(offset, offset + limite) };
}

export async function colunasPipeline(e: Escopo, et: Etiquetas, ordem: A.Ordem, limite: number) {
  const hoje = dataNegocio();
  const abertos = (await deals(e, true)).filter((d) => atendeDeal(d, et, hoje));
  return (["Prospecting", "Engaging"] as const).map((estagio) => {
    const l = A.ordenar(abertos.filter((d) => d.estagio === estagio), ordem);
    return { estagio, total: l.length, valor: l.reduce((a, d) => a + (d.valorEsperado ?? 0), 0), cartoes: l.slice(0, limite) };
  });
}

export async function painel(e: Escopo) {
  const lista = await deals(e);
  return { numeros: numerosPainel(lista, dataNegocio()), funil: funil(lista) };
}

export async function porVendedor(e: Escopo) {
  const [lista, equipe, usuarios, cont] = await Promise.all([
    deals(e),
    listarEquipe(),
    listarUsuarios(),
    lendo(() => B.contadoresDoTime(), async () => ({ feitas: new Map<number, number>(), perdidos: new Map<string, number>() })),
  ]);
  const nomes = [...new Set(equipe.filter((x) => A.noEscopo(e, x)).map((x) => x.vendedor))].sort();
  return nomes.map((v) => {
    const meus = lista.filter((d) => d.vendedor === v);
    const u = usuarios.find((x) => x.vendedor === v);
    return {
      vendedor: v,
      abertos: meus.filter((d) => d.estagio === "Prospecting" || d.estagio === "Engaging").length,
      emRisco: meus.filter((d) => d.icone === "em_risco").length,
      esfriaram: meus.filter((d) => d.icone === "esfriou").length,
      prioridadesFeitas: u ? (cont.feitas.get(u.id) ?? 0) : 0,
      perdidosPorFaltaDeAtendimento: cont.perdidos.get(v) ?? 0,
    };
  });
}

export const detalheDeal = (id: string, u: Usuario): Promise<DealDetalhe> => lendo(() => B.detalheDeal(id, u), () => A.detalheDeal(id, u));
export const listarUsuarios = (): Promise<Usuario[]> => lendo(async () => (await B.cadastros()).usuarios, () => A.listarUsuarios());
export const usuarioPorId = async (id: number): Promise<Usuario | undefined> => (await listarUsuarios()).find((u) => u.id === id);
export const listarEquipe = () => lendo(async () => (await B.cadastros()).equipe, () => A.listarEquipe());
export const listarProdutos = () => lendo(async () => (await B.cadastros()).produtos, () => A.listarProdutos());
export const listarTags = (): Promise<Tag[]> => lendo(() => B.listarTags(), () => A.listarTags());
export const contagemPorVendedor = () => lendo(() => B.contagemPorVendedor(), () => A.contagemPorVendedor());
export const notasDisponiveis = () => lendo(() => B.notasDisponiveis(), () => A.notasDisponiveis());

export async function contextoFiltro(modo: Modo, u: Usuario): Promise<Contexto> {
  const [equipe, produtos, tags, contas] = await Promise.all([listarEquipe(), listarProdutos(), listarTags(), listaDeContas()]);
  return {
    modo,
    papel: u.papel,
    hoje: dataNegocio(),
    vendedores: (u.papel === "manager" ? equipe.filter((x) => x.manager === u.manager) : equipe).map((x) => x.vendedor),
    managers: [...new Set(equipe.map((x) => x.manager))],
    empresas: contas.map((c) => c.nome),
    produtos: produtos.map((p) => p.nome),
    tags: tags.map((t) => t.nome),
    sedes: [...new Set(contas.map((c) => c.sede).filter((s): s is string => !!s))],
  };
}

const listaDeContas = cache((): Promise<ContaVisao[]> => lendo(() => B.listarContas(), () => A.buscarContas({}, "nome")));

export async function buscarContas(et: Etiquetas, ordem: A.OrdemContas = "receita"): Promise<ContaVisao[]> {
  const cmp: Record<A.OrdemContas, (a: ContaVisao, b: ContaVisao) => number> = {
    receita: (a, b) => b.receitaGanha - a.receitaGanha,
    compras: (a, b) => b.compras - a.compras,
    abertos: (a, b) => b.dealsAbertos - a.dealsAbertos,
    bonus: (a, b) => (b.bonus ?? -1) - (a.bonus ?? -1),
    nome: (a, b) => a.nome.localeCompare(b.nome),
  };
  return (await listaDeContas()).filter((c) => atendeConta(c, et)).sort((a, b) => cmp[ordem](a, b) || a.nome.localeCompare(b.nome));
}

/** Ficha da empresa. Os totais históricos são gerais; os deals abertos seguem o escopo do perfil. */
export function detalheConta(nome: string, u: Usuario): Promise<ContaDetalhe> {
  const escopo = A.escopoDe(u);
  return lendo(() => B.detalheConta(nome, (d) => A.noEscopo(escopo, d)), () => A.detalheConta(nome, escopo));
}

/** Criar e editar empresa ainda não tem function no banco: só funciona na opção de memória. */
export function podeEditarContas(): boolean {
  return !somenteLeitura() && !bancoAtivo();
}

// ---------------------------------------------------------------------------------- prioridades do dia

export const prioridadesDoDia = (u: Usuario): Promise<Prioridade[]> => lendo(() => B.prioridadesDoDia(u), () => A.prioridadesDoDia(u));
export const puxarMaisPrioridades = (u: Usuario, qtd = 5) => gravando(() => B.puxarMaisPrioridades(u, qtd), () => A.puxarMaisPrioridades(u, qtd));
export const marcarPrioridade = (u: Usuario, dealId: string, resultado: "feita" | "pulada", registro: { tipoAtividade?: string | null; comentario?: string | null } = {}) =>
  gravando<{ desfazer: string | null }>(() => B.marcarPrioridade(u, dealId, resultado, registro), () => A.marcarPrioridade(u, dealId, resultado, registro));

// ---------------------------------------------------------------------------------------------- escrita

export const mudarEstagio = (u: Usuario, id: string, versao: string | null, para: Estagio, extra: { valor?: number | null; motivo?: MotivoPerda | null } = {}) =>
  gravando<{ deal: DealVisao | undefined; desfazer: string | null }>(() => B.mudarEstagio(u, id, versao, para, extra), () => A.mudarEstagio(u, id, versao, para, extra));

export const salvarContato = (u: Usuario, dados: { id?: number; conta: string | null; nome: string; cargo?: string | null; email?: string | null; telefone?: string | null }, dealId?: string, versao?: string | null) =>
  gravando<{ id: number }>(() => B.salvarContato(u, dados, dealId, versao), () => A.salvarContato(u, dados, dealId, versao));

export const registrarAcao = (u: Usuario, dealId: string, acao: "liguei" | "requalifiquei" | "desisti", nota?: string | null) =>
  gravando<{ desfazer: string | null }>(() => B.registrarAcao(u, dealId, acao, nota), () => A.registrarAcao(u, dealId, acao, nota));

export const comentar = (u: Usuario, dealId: string, texto: string) => gravando(() => B.comentar(u, dealId, texto), () => A.comentar(u, dealId, texto));
export const removerComentario = (u: Usuario, id: number) => gravando<{ desfazer: string | null }>(() => B.removerComentario(u, id), () => A.removerComentario(u, id));
export const criarTag = (u: Usuario, nome: string, cor: CorTag) => gravando(() => B.criarTag(u, nome, cor), () => A.criarTag(u, nome, cor));
export const aplicarTag = (u: Usuario, dealId: string, tagId: number) => gravando<{ desfazer: string | null }>(() => B.aplicarTag(u, dealId, tagId), () => A.aplicarTag(u, dealId, tagId));
export const removerTag = (u: Usuario, dealId: string, tagId: number) => gravando<{ desfazer: string | null }>(() => B.removerTag(u, dealId, tagId), () => A.removerTag(u, dealId, tagId));

export const executarLote = (u: Usuario, tipo: A.TipoLote, ids: string[], p: { tagId?: number; texto?: string; motivo?: MotivoPerda | null }) =>
  gravando(() => B.executarLote(u, tipo, ids, p), () => A.executarLote(u, tipo, ids, p));

export const criarDeal = (u: Usuario, d: { produto: string; conta?: string | null; vendedor?: string | null; estagio: "Prospecting" | "Engaging"; nome?: string | null }) =>
  gravando(() => B.criarDeal(u, d), () => A.criarDeal(u, d));

export const salvarConta = (u: Usuario, d: Parameters<typeof A.salvarConta>[1]) =>
  gravando<{ nome: string }>(
    async () => {
      throw new ErroCRM("GS422", "O cadastro de empresa ainda não está ligado ao banco. Peça ao admin para cadastrar a empresa.");
    },
    () => A.salvarConta(u, d),
  );

/** Desfazer pelo token devolvido na escrita (mudança, ação, comentário, tag ou lote). */
export const desfazer = (u: Usuario, token: string): Promise<{ restaurados: number; pulados: number } | void> =>
  gravando<{ restaurados: number; pulados: number } | void>(
    () => B.desfazer(u, token),
    async () => {
      const lote = /^lote:(\d+)$/.exec(token);
      if (lote) return A.desfazerLote(u, Number(lote[1]));
      await A.desfazer(u, token);
    },
  );

/** Lotes das últimas 24 horas que o perfil pode desfazer: os próprios, os do time (manager) ou todos (admin). */
export const lotesRecentes = async (u: Usuario): Promise<LoteRecente[]> =>
  lotesRecentesPara(await lendo(() => B.lotesBrutos(), () => A.lotesBrutos()), u, await listarUsuarios(), Date.now());
