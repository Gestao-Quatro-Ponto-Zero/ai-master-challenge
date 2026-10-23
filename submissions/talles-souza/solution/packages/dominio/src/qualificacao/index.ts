/**
 * Contexto `qualificacao`: o MÉTODO de qualificação como configuração. O método traz as
 * perguntas de fato (sim/não, opcionais) que o vendedor responde dentro do deal. Cada resposta
 * soma ou tira do score (os pesos ficam no contexto `score`), e a resposta "não" troca a ação
 * sugerida pela frase da pergunta; nenhuma resposta muda o bloco nem a ordem da tela (o schema
 * nem aceita um efeito sobre o bloco). Trocar o método = trocar o config.
 */
import { z } from 'zod';
import { falha, ok, type Resultado } from '../compartilhado';
import { respostasDoDealSchema } from './http';
import { metodoProvisorio } from './metodo.provisorio.config';

export * from './http';
export { metodoProvisorio };

export type MetodoReferencia = 'BANT' | 'MEDDIC' | 'SPICED';

/**
 * Os blocos da segunda-feira do vendedor: o que avançar hoje, o que segue no ritmo, o que o
 * vendedor encaminha para nutrição (sai da fila ativa) e o que ainda não começou (sem data de
 * início, sem idade: o próximo passo é qualificar).
 */
export type Bloco = 'foque_agora' | 'siga_no_ritmo' | 'nutricao' | 'sem_inicio';

/** Os blocos na ordem em que a segunda-feira os mostra. */
export const BLOCOS: readonly Bloco[] = ['foque_agora', 'siga_no_ritmo', 'nutricao', 'sem_inicio'];

/** Pergunta de fato, opcional, respondida com sim ou não dentro do deal. */
export interface PerguntaFato {
  id: string;
  rotulo: string;
  pergunta: string;
  ajuda?: string;
  /** Em quais blocos (pela idade) a pergunta aparece. */
  aplicaEm: Bloco[];
  /** A ação que o vendedor vê quando a resposta é "não" (uma frase). */
  acaoSeNao?: string;
  /** Como a resposta aparece no porquê do score ("Decisor confirmado" / "Sem decisor"). */
  noScore?: { sim: string; nao: string };
  /** O critério do método que a pergunta confirma (ex.: `A` do BANT). */
  criterio?: string;
  /** De quais métodos a pergunta vem (pode ser vazio). */
  referencias: MetodoReferencia[];
  porque: string;
}

/**
 * Um critério do método. `dado` = vem do CRM (idade, valor); `vendedor` = só o vendedor
 * confirma, pela pergunta ligada.
 */
export interface CriterioMetodo {
  id: string;
  nome: string;
  origem: 'dado' | 'vendedor';
  descricao: string;
  /** A pergunta que confirma o critério (só nos de origem `vendedor`). */
  perguntaId: string | null;
}

/** Um método de qualificação: os critérios, as perguntas de fato e o aviso enquanto for provisório. */
export interface MetodoQualificacao {
  id: string;
  nome: string;
  versao: string;
  /** true enquanto o método final não for escolhido. */
  provisorio: boolean;
  aviso: string | null;
  criterios: CriterioMetodo[];
  perguntas: PerguntaFato[];
  /** De onde vêm o método e as frases de ação (crédito pelo nome da obra). */
  fontes: string[];
}

/** Versão do formato das respostas guardadas; a leitura recusa outra. */
export const FORMATO_RESPOSTAS = 1 as const;

/** Resposta a uma pergunta de fato. */
export type ValorResposta = 'sim' | 'nao';

/** Uma resposta do vendedor, com o momento em que foi dada. */
export interface Resposta {
  perguntaId: string;
  valor: ValorResposta;
  /** ISO 8601 do momento da resposta. */
  respondidoEm: string;
}

/**
 * A ação que a ferramenta sugere (ver `priorizacao.ProximaAcao`): avançar hoje, manter o ritmo,
 * qualificar o que ainda não começou ou encaminhar para nutrição (sai da fila ativa).
 */
export type TipoAcao = 'avancar_hoje' | 'manter_ritmo' | 'qualificar' | 'encaminhar_para_nutricao';

/** O vendedor aceita ou contesta a ação sugerida; contestar exige motivo. */
export interface DecisaoDoVendedor {
  acao: TipoAcao;
  aceita: boolean;
  motivo: string | null;
  /** ISO 8601. */
  em: string;
}

/** O que o vendedor registrou num deal: respostas às perguntas e a decisão sobre a ação. */
export interface RespostasDoDeal {
  formato: typeof FORMATO_RESPOSTAS;
  dealId: string;
  metodoId: string;
  respostas: Resposta[];
  decisao: DecisaoDoVendedor | null;
}

/** Porta da persistência das respostas (a web implementa com localStorage). */
export interface RepositorioRespostas {
  ler(dealId: string): RespostasDoDeal | null;
  salvar(respostas: RespostasDoDeal): void;
  listar(): RespostasDoDeal[];
  limpar(dealId: string): void;
}

/** O método em uso. Trocar o método = apontar para outro config. */
export const metodoAtivo: MetodoQualificacao = metodoProvisorio;

/** Schema de um bloco (para validar configs de método e de política). */
export const blocoSchema = z.enum(['foque_agora', 'siga_no_ritmo', 'nutricao', 'sem_inicio']);
const perguntaSchema = z.strictObject({
  id: z.string().trim().min(1).max(80),
  rotulo: z.string().trim().min(1),
  pergunta: z.string().trim().min(1),
  ajuda: z.string().optional(),
  aplicaEm: z.array(blocoSchema).min(1),
  acaoSeNao: z.string().trim().min(1).optional(),
  noScore: z
    .strictObject({ sim: z.string().trim().min(1), nao: z.string().trim().min(1) })
    .optional(),
  criterio: z.string().trim().min(1).optional(),
  referencias: z.array(z.enum(['BANT', 'MEDDIC', 'SPICED'])),
  porque: z.string().trim().min(1),
});
const criterioSchema = z.strictObject({
  id: z.string().trim().min(1).max(40),
  nome: z.string().trim().min(1),
  origem: z.enum(['dado', 'vendedor']),
  descricao: z.string().trim().min(1),
  perguntaId: z.string().trim().min(1).nullable(),
});

/** Schema de um método de qualificação (o config validado na carga). */
export const metodoSchema = z.strictObject({
  id: z.string().trim().min(1).max(80),
  nome: z.string().trim().min(1),
  versao: z.string().trim().min(1),
  provisorio: z.boolean(),
  aviso: z.string().nullable(),
  criterios: z.array(criterioSchema),
  perguntas: z.array(perguntaSchema),
  fontes: z.array(z.string().trim().min(1)),
});

function detalhesZod(erro: z.ZodError): { caminho: string; mensagem: string }[] {
  return erro.issues.map((i) => ({ caminho: i.path.join('.'), mensagem: i.message }));
}

/**
 * Valida um método (ids únicos, cada pergunta com `aplicaEm` não vazio). Campo desconhecido é
 * recusado: um efeito da resposta sobre o bloco (`seSim`/`seNao`) não passa.
 */
export function validarMetodo(bruto: unknown): Resultado<MetodoQualificacao> {
  const lido = metodoSchema.safeParse(bruto);
  if (!lido.success) {
    return falha(
      'metodo_invalido',
      'O método de qualificação não segue o formato.',
      detalhesZod(lido.error),
    );
  }
  const ids = new Set<string>();
  for (const p of lido.data.perguntas) {
    if (ids.has(p.id))
      return falha('metodo_invalido', 'Pergunta repetida no método: ' + p.id + '.');
    ids.add(p.id);
  }
  const criterios = new Set<string>();
  for (const c of lido.data.criterios) {
    if (criterios.has(c.id))
      return falha('metodo_invalido', 'Critério repetido no método: ' + c.id + '.');
    criterios.add(c.id);
    if (c.perguntaId !== null && !ids.has(c.perguntaId)) {
      return falha(
        'metodo_invalido',
        'O critério ' + c.id + ' aponta para a pergunta ' + c.perguntaId + ', que não existe.',
      );
    }
  }
  return ok(lido.data as MetodoQualificacao);
}

/** Valida respostas lidas de fora (localStorage, corpo HTTP) contra o schema versionado. */
export function validarRespostas(bruto: unknown): Resultado<RespostasDoDeal> {
  const lido = respostasDoDealSchema.safeParse(bruto);
  if (!lido.success) {
    return falha(
      'respostas_invalidas',
      'As respostas guardadas não seguem o formato.',
      detalhesZod(lido.error),
    );
  }
  return ok(lido.data);
}

/** As respostas atuais do deal, ou um registro vazio se não houver (ou se forem de outro deal/método). */
function base(
  atual: RespostasDoDeal | null,
  dealId: string,
  metodo: MetodoQualificacao,
): RespostasDoDeal {
  if (atual && atual.dealId === dealId && atual.metodoId === metodo.id) return atual;
  return { formato: FORMATO_RESPOSTAS, dealId, metodoId: metodo.id, respostas: [], decisao: null };
}

/** Registra (ou troca) a resposta de uma pergunta; recusa pergunta que não existe no método. */
export function responder(
  atual: RespostasDoDeal | null,
  dealId: string,
  metodo: MetodoQualificacao,
  perguntaId: string,
  valor: ValorResposta,
  agoraIso: string,
): Resultado<RespostasDoDeal> {
  if (!metodo.perguntas.some((p) => p.id === perguntaId)) {
    return falha(
      'pergunta_inexistente',
      'A pergunta ' + perguntaId + ' não existe no método ' + metodo.id + '.',
    );
  }
  const anterior = base(atual, dealId, metodo);
  const respostas = anterior.respostas.filter((r) => r.perguntaId !== perguntaId);
  respostas.push({ perguntaId, valor, respondidoEm: agoraIso });
  return ok({ ...anterior, respostas });
}

/**
 * Registra que o vendedor aceitou ou contestou a ação, com a data. Contestar sem motivo é erro
 * `motivo_obrigatorio`; ao aceitar (por exemplo, encaminhar para nutrição) o motivo é opcional.
 */
export function decidir(
  atual: RespostasDoDeal | null,
  dealId: string,
  metodo: MetodoQualificacao,
  decisao: { acao: TipoAcao; aceita: boolean; motivo?: string | null },
  agoraIso: string,
): Resultado<RespostasDoDeal> {
  const motivo = decisao.motivo?.trim() ?? '';
  if (!decisao.aceita && motivo.length < 3) {
    return falha('motivo_obrigatorio', 'Para contestar a ação sugerida, diga o motivo.');
  }
  const anterior = base(atual, dealId, metodo);
  return ok({
    ...anterior,
    decisao: {
      acao: decisao.acao,
      aceita: decisao.aceita,
      motivo: motivo.length >= 3 ? motivo : null,
      em: agoraIso,
    },
  });
}

/** Perguntas do método que valem para o bloco e ainda não têm resposta, na ordem do config. */
export function perguntasPendentes(
  metodo: MetodoQualificacao,
  bloco: Bloco,
  respostas: RespostasDoDeal | null,
): PerguntaFato[] {
  const respondidas = new Set(respostas?.respostas.map((r) => r.perguntaId) ?? []);
  return metodo.perguntas.filter((p) => p.aplicaEm.includes(bloco) && !respondidas.has(p.id));
}

/** Repositório em memória (testes e fallback quando o localStorage não existe). */
export function criarRepositorioEmMemoria(): RepositorioRespostas {
  const guardadas = new Map<string, RespostasDoDeal>();
  return {
    ler: (dealId) => guardadas.get(dealId) ?? null,
    salvar: (respostas) => {
      guardadas.set(respostas.dealId, respostas);
    },
    listar: () => [...guardadas.values()],
    limpar: (dealId) => {
      guardadas.delete(dealId);
    },
  };
}

/**
 * Decisão em lote ("Encaminhar os N"): a mesma decisão, com a mesma data e o mesmo motivo,
 * aplicada a cada negócio da lista. Devolve um registro por negócio. Erros: `lote_vazio`,
 * `lote_repetido` (o mesmo negócio duas vezes) e os de `decidir` (contestar exige motivo).
 */
export function decidirEmLote(
  atual: (dealId: string) => RespostasDoDeal | null,
  dealIds: readonly string[],
  metodo: MetodoQualificacao,
  decisao: { acao: TipoAcao; aceita: boolean; motivo?: string | null },
  agoraIso: string,
): Resultado<RespostasDoDeal[]> {
  if (dealIds.length === 0) return falha('lote_vazio', 'O lote não tem nenhum negócio.');
  if (new Set(dealIds).size !== dealIds.length)
    return falha('lote_repetido', 'O lote repete o mesmo negócio.');
  const saida: RespostasDoDeal[] = [];
  for (const id of dealIds) {
    const r = decidir(atual(id), id, metodo, decisao, agoraIso);
    if (!r.ok) return r;
    saida.push(r.valor);
  }
  return ok(saida);
}

/** Uma resposta como linha gravada (o banco guarda só linhas novas; nunca altera nem apaga). */
export interface LinhaResposta {
  dealId: string;
  vendedor: string;
  perguntaId: string;
  valor: ValorResposta;
  /** ISO 8601. */
  em: string;
}

/** Uma decisão do vendedor como linha gravada. */
export interface LinhaDecisao {
  dealId: string;
  vendedor: string;
  acao: TipoAcao;
  aceita: boolean;
  motivo: string | null;
  /** ISO 8601. */
  em: string;
}

/**
 * Monta o estado atual de cada negócio a partir das linhas gravadas: por pergunta, vale a
 * resposta mais recente; a decisão também é a mais recente. Empate de data: vale a linha que vem
 * depois na lista (a gravada por último). Saída em ordem de `dealId`.
 */
export function montarRegistros(
  respostas: readonly LinhaResposta[],
  decisoes: readonly LinhaDecisao[],
  metodoId: string,
): RespostasDoDeal[] {
  const porDeal = new Map<string, RespostasDoDeal>();
  const doDeal = (dealId: string): RespostasDoDeal => {
    let r = porDeal.get(dealId);
    if (!r) {
      r = { formato: FORMATO_RESPOSTAS, dealId, metodoId, respostas: [], decisao: null };
      porDeal.set(dealId, r);
    }
    return r;
  };
  for (const l of respostas) {
    const r = doDeal(l.dealId);
    const anterior = r.respostas.find((x) => x.perguntaId === l.perguntaId);
    if (anterior && anterior.respondidoEm > l.em) continue;
    r.respostas = r.respostas.filter((x) => x.perguntaId !== l.perguntaId);
    r.respostas.push({ perguntaId: l.perguntaId, valor: l.valor, respondidoEm: l.em });
  }
  for (const l of decisoes) {
    const r = doDeal(l.dealId);
    if (r.decisao && r.decisao.em > l.em) continue;
    r.decisao = { acao: l.acao, aceita: l.aceita, motivo: l.motivo, em: l.em };
  }
  return [...porDeal.values()].sort((a, b) => (a.dealId < b.dealId ? -1 : 1));
}

/**
 * Junta dois registros do mesmo negócio (por exemplo, o deste navegador e o do servidor): por
 * pergunta, a resposta mais recente; a decisão mais recente. Empate: vale `b`.
 */
export function mesclarRegistros(a: RespostasDoDeal, b: RespostasDoDeal): RespostasDoDeal {
  const linhas = (r: RespostasDoDeal): LinhaResposta[] =>
    r.respostas.map((x) => ({
      dealId: r.dealId,
      vendedor: '',
      perguntaId: x.perguntaId,
      valor: x.valor,
      em: x.respondidoEm,
    }));
  const decisoes = (r: RespostasDoDeal): LinhaDecisao[] =>
    r.decisao ? [{ dealId: r.dealId, vendedor: '', ...r.decisao }] : [];
  const [junto] = montarRegistros(
    [...linhas(a), ...linhas(b)],
    [...decisoes(a), ...decisoes(b)],
    b.metodoId,
  );
  return junto ?? b;
}
