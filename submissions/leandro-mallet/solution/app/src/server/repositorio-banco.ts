import "server-only";
// Repositório no banco (Supabase). Leitura: view core_deals_visao e tabelas, filtradas pelo perfil.
// Escrita: só pelas functions do banco, com o usuário do perfil e o correlation_id do servidor.
import { CONFIG } from "@/lib/config";
import type {
  Comentario, ContaDetalhe, ContaVisao, Contato, CorTag, DealDetalhe, DealVisao, Escopo, Estagio, EventoLinhaDoTempo,
  MotivoPerda, Papel, Porte, Prioridade, Tag, Usuario,
} from "@/lib/tipos";
import { banco, ErroCRM, escrever, ler, lerTudo } from "./banco";

// ------------------------------------------------------------------------------------------- cadastros

interface Cadastros {
  usuarios: Usuario[];
  equipe: { vendedor: string; manager: string; regiao: string }[];
  produtos: { nome: string; serie: string; preco: number }[];
  contas: ContaLinha[];
}
interface ContaLinha {
  nome: string; setor: string | null; porte: Porte | null; funcionarios: number | null; receita_milhoes: number | null;
  ano_fundacao: number | null; pais: string | null; empresa_mae_nome: string | null;
}

const g = globalThis as unknown as { __g4Cad?: { ate: number; dados: Promise<Cadastros> } };
const VALIDADE_CADASTROS_MS = 60_000;

/** Time, produtos, contas e usuários mudam pouco: ficam guardados por 1 minuto em cada instância. */
export async function cadastros(): Promise<Cadastros> {
  if (g.__g4Cad && g.__g4Cad.ate > Date.now()) return g.__g4Cad.dados;
  const dados = (async (): Promise<Cadastros> => {
    const db = banco();
    const [us, vs, ms, ps, cs] = await Promise.all([
      ler<{ id: number; papel: Papel | "sistema"; nome_exibicao: string; vendedor_nome: string | null; manager_nome: string | null }[]>(
        db.from("config_usuarios").select("id,papel,nome_exibicao,vendedor_nome,manager_nome").eq("ativo", true).neq("papel", "sistema").order("id")),
      ler<{ nome: string; manager_nome: string }[]>(db.from("core_vendedores").select("nome,manager_nome").order("nome")),
      ler<{ nome: string; escritorio_nome: string }[]>(db.from("core_managers").select("nome,escritorio_nome")),
      ler<{ nome: string; serie: string; preco: number }[]>(db.from("core_produtos").select("nome,serie,preco").order("nome")),
      ler<ContaLinha[]>(db.from("core_contas").select("nome,setor,porte,funcionarios,receita_milhoes,ano_fundacao,pais,empresa_mae_nome").order("nome")),
    ]);
    const regiao = new Map(ms.map((m) => [m.nome, m.escritorio_nome]));
    const manager = new Map(vs.map((v) => [v.nome, v.manager_nome]));
    return {
      equipe: vs.map((v) => ({ vendedor: v.nome, manager: v.manager_nome, regiao: regiao.get(v.manager_nome) ?? "—" })),
      produtos: ps,
      contas: cs,
      usuarios: us.map((u) => {
        const papel = u.papel as Papel;
        if (papel === "vendedor" && u.vendedor_nome) {
          const m = manager.get(u.vendedor_nome);
          return { id: u.id, papel, nome: u.nome_exibicao, vendedor: u.vendedor_nome, manager: m, regiao: m ? regiao.get(m) : undefined };
        }
        if (papel === "manager" && u.manager_nome) return { id: u.id, papel, nome: u.nome_exibicao, manager: u.manager_nome, regiao: regiao.get(u.manager_nome) };
        return { id: u.id, papel, nome: u.nome_exibicao };
      }),
    };
  })();
  g.__g4Cad = { ate: Date.now() + VALIDADE_CADASTROS_MS, dados };
  dados.catch(() => {
    g.__g4Cad = undefined;
  });
  return dados;
}

export async function listarTags(): Promise<Tag[]> {
  const linhas = await ler<{ id: number; nome: string; cor_token: CorTag; ativa: boolean }[]>(
    banco().from("config_tags").select("id,nome,cor_token,ativa").eq("ativa", true).order("nome"));
  return linhas.map((t) => ({ id: t.id, nome: t.nome, cor: t.cor_token, ativa: t.ativa }));
}

// ---------------------------------------------------------------------------------------------- deals

interface LinhaVisao {
  opportunity_id: string; nome: string; estagio: Estagio; vendedor_nome: string; manager_nome: string; escritorio_nome: string;
  produto_nome: string; serie: string; preco: number; conta_nome: string | null; setor: string | null; porte: Porte | null;
  contato_id: number | null; contato_nome: string | null; contato_cargo: string | null; data_abertura: string | null;
  dias_desde_abertura: number | null; ultimo_contato: string | null; close_date: string | null; close_value: number | null;
  motivo_perda: MotivoPerda | null; execucao_id: number | null; fit: number | null; heat: number | null; bonus: number | null;
  score: number | null; faixa_nota: DealVisao["faixaNota"]; acao_sugerida: DealVisao["acaoSugerida"]; marcadores: string[] | null;
  valor_esperado: number | null; valor_pelo_preco_de_tabela: boolean; icone: DealVisao["icone"]; tags: string[] | null;
  qtd_comentarios: number; atualizado_depois_da_nota: boolean; criado_em: string | null; atualizado_em: string;
}

function paraVisao(l: LinhaVisao, tags: Map<string, Tag>): DealVisao {
  return {
    id: l.opportunity_id, nome: l.nome, estagio: l.estagio, vendedor: l.vendedor_nome, manager: l.manager_nome, regiao: l.escritorio_nome,
    produto: l.produto_nome, serie: l.serie, preco: l.preco, conta: l.conta_nome, setor: l.setor, porte: l.porte,
    contato: l.contato_id && l.contato_nome ? { id: l.contato_id, nome: l.contato_nome, cargo: l.contato_cargo } : null,
    dataAbertura: l.data_abertura, diasDesdeAbertura: l.dias_desde_abertura, ultimoContato: l.ultimo_contato,
    closeDate: l.close_date, closeValue: l.close_value, motivoPerda: l.motivo_perda,
    fit: l.fit, heat: l.heat, bonus: l.bonus, score: l.score, faixaNota: l.faixa_nota, acaoSugerida: l.acao_sugerida,
    marcadores: l.marcadores ?? [], valorEsperado: l.valor_esperado, valorPeloPrecoDeTabela: l.valor_pelo_preco_de_tabela, icone: l.icone,
    tags: (l.tags ?? []).map((n) => tags.get(n) ?? { id: 0, nome: n, cor: "tag-6" as CorTag, ativa: false }),
    qtdComentarios: Number(l.qtd_comentarios) || 0, atualizadoDepoisDaNota: l.atualizado_depois_da_nota,
    criadoEm: l.criado_em, atualizadoEm: l.atualizado_em,
  };
}

const mapaTags = async () => new Map((await listarTags()).map((t) => [t.nome, t]));

// Colunas básicas da view (sem as calculadas: ícone, nota, tags e comentários). Usadas nos deals fechados,
// que são a maioria (6.711 de 8.800) e não têm ícone nem nota; ler tudo deles pesava vários segundos.
const COLUNAS_BASICAS =
  "opportunity_id,nome,estagio,vendedor_nome,manager_nome,escritorio_nome,produto_nome,serie,preco,conta_nome,setor,porte," +
  "contato_id,contato_nome,contato_cargo,data_abertura,ultimo_contato,close_date,close_value,motivo_perda,criado_em,atualizado_em";

// Forma mínima da consulta do supabase-js que este arquivo usa (os tipos completos da biblioteca são
// pesados demais para o compilador quando a consulta é montada em etapas).
interface Consulta {
  eq(coluna: string, valor: string): Consulta;
  in(coluna: string, valores: string[]): Consulta;
  order(coluna: string): Consulta;
  range(de: number, ate: number): PromiseLike<{ data: LinhaVisao[] | null; error: { code?: string; message?: string } | null; count?: number | null }>;
}
const visaoDeDeals = (colunas: string) => banco().from("core_deals_visao").select(colunas, { count: "exact" }) as unknown as Consulta;

function filtrarEscopo(q: Consulta, e: Escopo): Consulta {
  if (e.papel === "vendedor") q = q.eq("vendedor_nome", e.vendedor ?? "");
  else if (e.papel === "manager") q = q.eq("manager_nome", e.manager ?? "");
  if (e.papel !== "vendedor" && e.vendedor) q = q.eq("vendedor_nome", e.vendedor);
  if (e.papel === "admin" && e.manager) q = q.eq("manager_nome", e.manager);
  if (e.papel === "admin" && e.regiao) q = q.eq("escritorio_nome", e.regiao);
  return q;
}

/** Tags ativas e quantidade de comentários por deal (tabelas pequenas), para completar os deals fechados. */
async function extrasPorDeal(tags: Map<string, Tag>): Promise<{ tags: Map<string, Tag[]>; comentarios: Map<string, number> }> {
  const db = banco();
  const porId = new Map([...tags.values()].map((t) => [t.id, t]));
  const [dt, cm] = await Promise.all([
    lerTudo<{ opportunity_id: string; tag_id: number }>((de, ate) =>
      db.from("acao_deal_tags").select("opportunity_id,tag_id", { count: "exact" }).is("removida_em", null).order("id").range(de, ate)),
    lerTudo<{ opportunity_id: string }>((de, ate) =>
      db.from("acao_comentarios").select("opportunity_id", { count: "exact" }).is("removido_em", null).order("id").range(de, ate)),
  ]);
  const tagsPorDeal = new Map<string, Tag[]>();
  for (const x of dt) {
    const t = porId.get(x.tag_id);
    if (t) tagsPorDeal.set(x.opportunity_id, [...(tagsPorDeal.get(x.opportunity_id) ?? []), t]);
  }
  const comentarios = new Map<string, number>();
  for (const x of cm) comentarios.set(x.opportunity_id, (comentarios.get(x.opportunity_id) ?? 0) + 1);
  return { tags: tagsPorDeal, comentarios };
}

/** Os deals que o perfil enxerga, lidos da view com o filtro do escopo aplicado no banco. */
export async function dealsDoEscopo(e: Escopo, soAbertos = false): Promise<DealVisao[]> {
  const tags = await mapaTags();
  const abertos = lerTudo<LinhaVisao>((de, ate) => filtrarEscopo(visaoDeDeals("*"), e).in("estagio", ["Prospecting", "Engaging"]).order("opportunity_id").range(de, ate));
  if (soAbertos) return (await abertos).map((l) => paraVisao(l, tags));
  const [a, fechados, extras] = await Promise.all([
    abertos,
    lerTudo<LinhaVisao>((de, ate) => filtrarEscopo(visaoDeDeals(COLUNAS_BASICAS), e).in("estagio", ["Won", "Lost"]).order("opportunity_id").range(de, ate)),
    extrasPorDeal(tags),
  ]);
  return [
    ...a.map((l) => paraVisao(l, tags)),
    ...fechados.map((l) => ({
      ...paraVisao({ ...l, dias_desde_abertura: null, execucao_id: null, fit: null, heat: null, bonus: null, score: null, faixa_nota: null, acao_sugerida: null,
        marcadores: [], valor_esperado: null, valor_pelo_preco_de_tabela: false, icone: null, tags: [], qtd_comentarios: 0, atualizado_depois_da_nota: false }, tags),
      tags: extras.tags.get(l.opportunity_id) ?? [],
      qtdComentarios: extras.comentarios.get(l.opportunity_id) ?? 0,
    })),
  ];
}

async function dealsPorIds(ids: string[]): Promise<DealVisao[]> {
  if (!ids.length) return [];
  const [linhas, tags] = await Promise.all([ler<LinhaVisao[]>(banco().from("core_deals_visao").select("*").in("opportunity_id", ids)), mapaTags()]);
  return linhas.map((l) => paraVisao(l, tags));
}

function transicoes(estagio: Estagio, papel: Papel): Estagio[] {
  if (estagio === "Prospecting") return ["Engaging", "Lost"];
  if (estagio === "Engaging") return ["Won", "Lost"];
  return (CONFIG.papeisReabrir as readonly string[]).includes(papel) ? ["Engaging"] : [];
}

export async function detalheDeal(id: string, u: Usuario): Promise<DealDetalhe> {
  const db = banco();
  const [deal] = await dealsPorIds([id]);
  if (!deal) throw new ErroCRM("GS404", "Este deal não foi encontrado.");
  const linha = await ler<LinhaVisao | null>(db.from("core_deals_visao").select("execucao_id,contato_id").eq("opportunity_id", id).maybeSingle() as never);
  const execucao = linha?.execucao_id ?? null;
  const [tempo, coment, comp, motivos, contato, cad] = await Promise.all([
    ler<{ data_negocio: string | null; momento: string | null; tipo: string; descricao: string; autor: string | null; desfeito: boolean }[]>(
      db.rpc("core_linha_do_tempo", { p_opportunity_id: id })),
    ler<{ id: number; usuario_id: number; texto: string; data_negocio: string; criado_em: string; editado_em: string | null }[]>(
      db.from("acao_comentarios").select("id,usuario_id,texto,data_negocio,criado_em,editado_em").eq("opportunity_id", id).is("removido_em", null).order("criado_em", { ascending: false })),
    execucao
      ? ler<{ grupo: "fit" | "heat" | "bonus"; componente: string; pontos: number; maximo: number | null }[]>(
          db.from("score_componentes").select("grupo,componente,pontos,maximo").eq("execucao_id", execucao).eq("opportunity_id", id))
      : Promise.resolve([]),
    execucao
      ? ler<{ texto: string }[]>(db.from("score_motivos").select("texto,ordem").eq("execucao_id", execucao).eq("opportunity_id", id).order("ordem"))
      : Promise.resolve([]),
    linha?.contato_id
      ? ler<{ id: number; conta_nome: string | null; nome: string; cargo: string | null; email: string | null; telefone: string | null } | null>(
          db.from("core_contatos").select("id,conta_nome,nome,cargo,email,telefone").eq("id", linha.contato_id).maybeSingle() as never)
      : Promise.resolve(null),
    cadastros(),
  ]);
  const nomes = new Map(cad.usuarios.map((x) => [x.id, x.nome]));
  const tipos = new Set<EventoLinhaDoTempo["tipo"]>(["aberto", "fechado", "criado", "estagio", "dados", "acao", "comentario", "tag", "repasse"]);
  return {
    deal,
    componentes: comp.map((c) => ({ grupo: c.grupo, nome: c.componente, pontos: Number(c.pontos), maximo: c.maximo === null ? null : Number(c.maximo) })),
    motivos: motivos.map((m) => m.texto),
    linhaDoTempo: tempo.map((t) => ({
      data: t.data_negocio, momento: t.momento, descricao: t.descricao, autor: t.autor, desfeito: t.desfeito,
      tipo: tipos.has(t.tipo as EventoLinhaDoTempo["tipo"]) ? (t.tipo as EventoLinhaDoTempo["tipo"]) : "criado",
    })),
    comentarios: coment.map<Comentario>((c) => ({
      id: c.id, autorId: c.usuario_id, autor: nomes.get(c.usuario_id) ?? "—", texto: c.texto, data: c.data_negocio, criadoEm: c.criado_em, editado: !!c.editado_em,
    })),
    contatoCompleto: contato ? ({ id: contato.id, conta: contato.conta_nome, nome: contato.nome, cargo: contato.cargo, email: contato.email, telefone: contato.telefone } satisfies Contato) : null,
    transicoes: transicoes(deal.estagio, u.papel),
  };
}

export async function notasDisponiveis(): Promise<boolean> {
  const p = await ler<{ valor: unknown }[]>(banco().from("config_parametros").select("valor").eq("chave", "execucao_ativa"));
  return p[0]?.valor !== null && p[0]?.valor !== undefined;
}

/** Deals abertos por vendedor, para a tela de escolha de perfil. */
export async function contagemPorVendedor(): Promise<Map<string, number>> {
  const db = banco();
  const linhas = await lerTudo<{ vendedor_nome: string }>((de, ate) =>
    db.from("core_deals").select("vendedor_nome", { count: "exact" }).in("estagio", ["Prospecting", "Engaging"]).order("opportunity_id").range(de, ate));
  const m = new Map<string, number>();
  for (const l of linhas) m.set(l.vendedor_nome, (m.get(l.vendedor_nome) ?? 0) + 1);
  return m;
}

/** Contadores do quadro "Por vendedor" que não saem dos deals: ✓ de hoje e leads perdidos por repasse. */
export async function contadoresDoTime(): Promise<{ feitas: Map<number, number>; perdidos: Map<string, number> }> {
  const db = banco();
  const inicioDoDia = new Date(`${new Date().toLocaleDateString("sv-SE", { timeZone: CONFIG.fusoHorario })}T00:00:00-03:00`).toISOString();
  const [acoes, repasses] = await Promise.all([
    ler<{ usuario_id: number }[]>(db.from("acao_registros").select("usuario_id").eq("acao", "prioridade_feita").is("desfeita_em", null).gte("criado_em", inicioDoDia)),
    ler<{ de_vendedor: string }[]>(db.from("acao_reatribuicoes").select("de_vendedor").neq("origem", "manager")),
  ]);
  const feitas = new Map<number, number>();
  for (const a of acoes) feitas.set(a.usuario_id, (feitas.get(a.usuario_id) ?? 0) + 1);
  const perdidos = new Map<string, number>();
  for (const r of repasses) perdidos.set(r.de_vendedor, (perdidos.get(r.de_vendedor) ?? 0) + 1);
  return { feitas, perdidos };
}

// ---------------------------------------------------------------------------------- prioridades do dia

interface LinhaPrioridade { posicao: number; opportunity_id: string; marcada: "feita" | "pulada" | "contato" | null; pulado_dias_seguidos: number | null }

async function montarLista(linhas: LinhaPrioridade[]): Promise<Prioridade[]> {
  const deals = new Map((await dealsPorIds(linhas.map((l) => l.opportunity_id))).map((d) => [d.id, d]));
  return linhas.flatMap((l) => {
    const deal = deals.get(l.opportunity_id);
    return deal ? [{ posicao: l.posicao, deal, marcada: l.marcada, puladoDiasSeguidos: l.pulado_dias_seguidos ?? 0 }] : [];
  });
}

/** A lista do dia fica no banco (acao_prioridades): a mesma para qualquer instância do servidor. */
export async function prioridadesDoDia(u: Usuario): Promise<Prioridade[]> {
  let linhas = await ler<LinhaPrioridade[]>(banco().rpc("acao_listar_prioridades", { p_usuario_id: u.id }));
  if (linhas.length === 0) linhas = (await escrever<LinhaPrioridade[]>("acao_prioridades_do_dia", u.id)).dados;
  return montarLista(linhas);
}

export async function puxarMaisPrioridades(u: Usuario, qtd = 5): Promise<void> {
  await escrever("acao_puxar_mais_prioridades", u.id, { p_quantidade: qtd });
}

export async function marcarPrioridade(u: Usuario, dealId: string, resultado: "feita" | "pulada", registro: { tipoAtividade?: string | null; comentario?: string | null }) {
  const { dados } = await escrever<{ id: number }>("acao_marcar_prioridade", u.id, {
    p_opportunity_id: dealId, p_resultado: resultado,
    p_tipo_atividade: resultado === "feita" ? (registro.tipoAtividade ?? null) : null,
    p_comentario: resultado === "feita" ? (registro.comentario ?? null) : null,
  });
  return { desfazer: `acao:${dados.id}` };
}

// --------------------------------------------------------------------------------------------- escrita

export async function mudarEstagio(u: Usuario, id: string, versao: string | null, para: Estagio, extra: { valor?: number | null; motivo?: MotivoPerda | null }) {
  const { correlationId } = await escrever("core_mudar_estagio", u.id, {
    p_opportunity_id: id, p_versao: versao, p_para: para, p_valor: extra.valor ?? null, p_motivo: extra.motivo ?? null,
  });
  const [deal] = await dealsPorIds([id]);
  return { deal, desfazer: `deal:${correlationId}` };
}

export async function salvarContato(u: Usuario, dados: { id?: number; conta: string | null; nome: string; cargo?: string | null; email?: string | null; telefone?: string | null }, dealId?: string, versao?: string | null) {
  const r = await escrever<{ id: number }>("core_salvar_contato", u.id, {
    p_contato_id: dados.id ?? null, p_conta: dados.conta, p_nome: dados.nome, p_cargo: dados.cargo ?? null, p_email: dados.email ?? null,
    p_telefone: dados.telefone ?? null, p_opportunity_id: dealId ?? null, p_versao: versao ?? null,
  });
  return { id: r.dados.id };
}

export async function registrarAcao(u: Usuario, dealId: string, acao: "liguei" | "requalifiquei" | "desisti", nota?: string | null) {
  const { dados } = await escrever<{ id: number }>("acao_registrar", u.id, { p_opportunity_id: dealId, p_acao: acao, p_nota: nota ?? null });
  return { desfazer: `acao:${dados.id}` };
}

export async function comentar(u: Usuario, dealId: string, texto: string) {
  const { dados } = await escrever<{ id: number }>("acao_comentar", u.id, { p_opportunity_id: dealId, p_texto: texto });
  return { id: dados.id };
}

/** "Apagar" comentário = remoção lógica no banco (removido_em), com a restauração como desfazer. */
export async function removerComentario(u: Usuario, id: number) {
  await escrever("acao_remover_comentario", u.id, { p_comentario_id: id });
  return { desfazer: `comentario:${id}` };
}

export async function criarTag(u: Usuario, nome: string, cor: CorTag): Promise<Tag> {
  const { dados } = await escrever<{ id: number; nome: string; cor_token: CorTag; ativa: boolean }>("config_criar_tag", u.id, { p_nome: nome.trim().replace(/^#/, ""), p_cor_token: cor });
  return { id: dados.id, nome: dados.nome, cor: dados.cor_token, ativa: dados.ativa };
}

export async function aplicarTag(u: Usuario, dealId: string, tagId: number) {
  await escrever("acao_aplicar_tag", u.id, { p_opportunity_id: dealId, p_tag_id: tagId });
  return { desfazer: `tagmais:${dealId}:${tagId}` };
}

export async function removerTag(u: Usuario, dealId: string, tagId: number) {
  await escrever("acao_remover_tag", u.id, { p_opportunity_id: dealId, p_tag_id: tagId });
  return { desfazer: `tagmenos:${dealId}:${tagId}` };
}

export async function executarLote(u: Usuario, tipo: string, ids: string[], p: { tagId?: number; texto?: string; motivo?: MotivoPerda | null }) {
  const { dados } = await escrever<{ lote_id: number; aplicados: number; pulados: number }>("system_executar_lote", u.id, {
    p_tipo: tipo, p_ids: ids, p_etiquetas: {},
    p_parametros: { ...(p.tagId !== undefined ? { tag_id: p.tagId } : {}), ...(p.texto ? { texto: p.texto } : {}), ...(p.motivo ? { motivo: p.motivo } : {}) },
  });
  return { loteId: dados.lote_id, aplicados: dados.aplicados, pulados: dados.pulados };
}

export async function criarDeal(u: Usuario, d: { produto: string; conta?: string | null; vendedor?: string | null; estagio: "Prospecting" | "Engaging"; nome?: string | null }) {
  const { dados } = await escrever<{ opportunity_id: string }>("core_criar_deal", u.id, {
    p_produto: d.produto, p_conta: d.conta ?? null, p_vendedor: d.vendedor ?? null, p_estagio: d.estagio, p_nome: d.nome ?? null,
  });
  return { id: dados.opportunity_id };
}

/** Desfaz pelo token devolvido na escrita: cada tipo chama a function do banco que reverte sem apagar. */
export async function desfazer(u: Usuario, token: string): Promise<void> {
  const [tipo, a, b] = token.split(":");
  if (tipo === "deal" && a) await escrever("core_desfazer_alteracao", u.id, { p_correlation_original: a });
  else if (tipo === "acao" && a) await escrever("acao_desfazer", u.id, { p_acao_id: Number(a) });
  else if (tipo === "comentario" && a) await escrever("acao_restaurar_comentario", u.id, { p_comentario_id: Number(a) });
  else if (tipo === "tagmais" && a && b) await escrever("acao_remover_tag", u.id, { p_opportunity_id: a, p_tag_id: Number(b) });
  else if (tipo === "tagmenos" && a && b) await escrever("acao_aplicar_tag", u.id, { p_opportunity_id: a, p_tag_id: Number(b) });
  else if (tipo === "lote" && a) await escrever("system_desfazer_lote", u.id, { p_lote_id: Number(a) });
  else throw new ErroCRM("GS422", "O prazo para desfazer passou.");
}

// ---------------------------------------------------------------------------------------------- contas

interface Padrao { conta_nome: string; intervalo_tipico_dias: number | null; mes_habitual: number | null; proxima_compra_esperada: string | null; na_janela: boolean; bonus: number; explicacao: string | null }

async function padroes(conta?: string): Promise<Map<string, Padrao>> {
  const db = banco();
  const p = await ler<{ valor: unknown }[]>(db.from("config_parametros").select("valor").eq("chave", "execucao_ativa"));
  const execucao = Number(p[0]?.valor);
  if (!execucao) return new Map();
  let q = db.from("score_padroes_conta").select("conta_nome,intervalo_tipico_dias,mes_habitual,proxima_compra_esperada,na_janela,bonus,explicacao").eq("execucao_id", execucao);
  if (conta) q = q.eq("conta_nome", conta);
  return new Map((await ler<Padrao[]>(q)).map((x) => [x.conta_nome, x]));
}

function contaVisao(c: ContaLinha, a: { abertos: number; ganhos: number; perdidos: number; receita: number } | undefined, p: Padrao | undefined): ContaVisao {
  return {
    nome: c.nome, setor: c.setor, porte: c.porte, funcionarios: c.funcionarios, receitaMilhoes: c.receita_milhoes === null ? null : Number(c.receita_milhoes),
    anoFundacao: c.ano_fundacao, sede: c.pais, empresaMae: c.empresa_mae_nome,
    dealsAbertos: a?.abertos ?? 0, compras: a?.ganhos ?? 0, perdas: a?.perdidos ?? 0, receitaGanha: a?.receita ?? 0,
    padrao: !p ? null : p.na_janela ? "na_janela" : p.intervalo_tipico_dias ? "fora_da_janela" : "sem_padrao",
    bonus: p ? p.bonus : null,
  };
}

export async function listarContas(): Promise<ContaVisao[]> {
  const db = banco();
  const [cad, deals, pad] = await Promise.all([
    cadastros(),
    lerTudo<{ conta_nome: string; estagio: Estagio; close_value: number | null }>((de, ate) =>
      db.from("core_deals").select("conta_nome,estagio,close_value", { count: "exact" }).not("conta_nome", "is", null).order("opportunity_id").range(de, ate)),
    padroes(),
  ]);
  const agg = new Map<string, { abertos: number; ganhos: number; perdidos: number; receita: number }>();
  for (const d of deals) {
    const a = agg.get(d.conta_nome) ?? { abertos: 0, ganhos: 0, perdidos: 0, receita: 0 };
    if (d.estagio === "Won") { a.ganhos++; a.receita += d.close_value ?? 0; } else if (d.estagio === "Lost") a.perdidos++; else a.abertos++;
    agg.set(d.conta_nome, a);
  }
  return cad.contas.map((c) => contaVisao(c, agg.get(c.nome), pad.get(c.nome)));
}

const MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];

export async function detalheConta(nome: string, noEscopo: (d: DealVisao) => boolean): Promise<ContaDetalhe> {
  const cad = await cadastros();
  const c = cad.contas.find((x) => x.nome === nome);
  if (!c) throw new ErroCRM("GS404", "Esta empresa não foi encontrada.");
  const [linhas, tags, pad] = await Promise.all([
    ler<LinhaVisao[]>(banco().from("core_deals_visao").select("*").eq("conta_nome", nome)),
    mapaTags(),
    padroes(nome),
  ]);
  const deals = linhas.map((l) => paraVisao(l, tags));
  const ganhos = deals.filter((d) => d.estagio === "Won").sort((a, b) => (a.closeDate ?? "").localeCompare(b.closeDate ?? ""));
  const perdidos = deals.filter((d) => d.estagio === "Lost");
  const abertos = deals.filter((d) => d.estagio === "Prospecting" || d.estagio === "Engaging");
  const meses = new Map<string, { ganhos: number; perdidos: number }>();
  for (const d of [...ganhos, ...perdidos]) {
    if (!d.closeDate) continue;
    const m = d.closeDate.slice(0, 7);
    const r = meses.get(m) ?? { ganhos: 0, perdidos: 0 };
    if (d.estagio === "Won") r.ganhos++; else r.perdidos++;
    meses.set(m, r);
  }
  const porProduto = new Map<string, { compras: number; receita: number }>();
  for (const d of ganhos) {
    const r = porProduto.get(d.produto) ?? { compras: 0, receita: 0 };
    r.compras++;
    r.receita += d.closeValue ?? 0;
    porProduto.set(d.produto, r);
  }
  const receita = ganhos.reduce((a, d) => a + (d.closeValue ?? 0), 0);
  const p = pad.get(nome);
  return {
    conta: contaVisao(c, { abertos: abertos.length, ganhos: ganhos.length, perdidos: perdidos.length, receita }, p),
    porMes: [...meses.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([mes, v]) => ({ mes, ...v })),
    produtos: [...porProduto.entries()].map(([produto, v]) => ({ produto, ...v })).sort((a, b) => b.receita - a.receita),
    ticketMedio: ganhos.length ? Math.round(receita / ganhos.length) : null,
    primeiraCompra: ganhos[0]?.closeDate ?? null,
    ultimaCompra: ganhos.at(-1)?.closeDate ?? null,
    padrao: p
      ? { intervaloTipicoDias: p.intervalo_tipico_dias, mesHabitual: p.mes_habitual ? (MESES[p.mes_habitual - 1] ?? null) : null, proximaCompra: p.proxima_compra_esperada, explicacao: p.explicacao }
      : null,
    // Os totais históricos são da empresa inteira; os deals abertos seguem o escopo do perfil.
    abertos: abertos.filter(noEscopo).sort((a, b) => (b.score ?? -1) - (a.score ?? -1) || (b.valorEsperado ?? 0) - (a.valorEsperado ?? 0)),
  };
}
