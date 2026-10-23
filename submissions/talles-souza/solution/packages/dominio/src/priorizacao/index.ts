/**
 * Contexto `priorizacao`: a segunda-feira do vendedor ("onde focar hoje") em quatro blocos (Foque
 * agora, Siga no ritmo, Nutrição e Aborde primeiro, o dos negócios sem data de início). A
 * POLÍTICA (config) põe cada deal num bloco pela idade, com os limites medidos no histórico.
 * Três coisas separadas: o score diz se o negócio é bom (a idade medida + as respostas do
 * vendedor); o lugar na tela diz por onde começar (o grupo, depois o valor esperado); o preço diz
 * quanto está em jogo. Acima do limite, a ação é encaminhar para nutrição. As respostas do
 * vendedor mudam o score e a ação, nunca o bloco nem a ordem.
 */
import { z } from 'zod';
import { falha, ok, type Resultado } from '../compartilhado';
import type { Deal, Janela, MembroDoTime } from '../pipeline';
import {
  BLOCOS,
  perguntasPendentes,
  type Bloco,
  type DecisaoDoVendedor,
  type MetodoQualificacao,
  type PerguntaFato,
  type Resposta,
  type RespostasDoDeal,
  type TipoAcao,
} from '../qualificacao';
import type {
  Avaliacao,
  ConfigChance,
  ConfigQualidade,
  EntradaDaLista,
  MotivoDaParcela,
  MotivoDoFator,
  MotorDePontos,
  PosicaoNaLista,
  ScoreDeQualidade,
} from '../score';
import { compararNaLista, configQualidadePadrao, posicionar, pontuarQualidade } from '../score';
import { politicaProvisoria } from './politica.provisoria.config';

export * from './http';
export { politicaProvisoria };

/** Cada grupo da tela é um bloco (cada negócio aparece em um só). */
export type Grupo = Bloco;

/**
 * Os grupos na ordem da tela, do que mais precisa do vendedor para o que menos precisa: Foque
 * agora, Siga no ritmo, Aborde primeiro e, por último, Nutrição.
 */
export const GRUPOS: readonly Grupo[] = ['foque_agora', 'siga_no_ritmo', 'sem_inicio', 'nutricao'];

/** Os blocos que a idade decide (todos menos `sem_inicio`, que é a falta de idade). */
export type BlocoPorIdade = Exclude<Bloco, 'sem_inicio'>;

/** Uma faixa de idade da política. */
export interface FaixaDeIdade {
  bloco: BlocoPorIdade;
  /** Idade máxima da faixa, inclusiva (dias); null = sem teto. */
  ateDias: number | null;
  /** "41 a 60 dias". */
  rotulo: string;
  /** A medição que sustenta a faixa. */
  porque: string;
}

/** Os textos de um grupo da tela. `{de}`, `{ate}` e `{limite}` vêm das faixas da política. */
export interface TextoDoGrupo {
  titulo: string;
  subtitulo: string;
  /** A ação do grupo (em Nutrição, o rótulo do botão). */
  acao: string;
  /** O que a tela diz quando o grupo está vazio. */
  vazio: string;
}

/** Todos os textos da tela, editáveis no config. `{…}` são valores que o domínio preenche. */
export interface TextosDaTela {
  /**
   * `{n}` = negócios abertos do filtro. `quem` e `escolha`: a entrada ("Quem é você?");
   * `semNegocios`: o vendedor sem nenhum negócio aberto.
   */
  pagina: {
    titulo: string;
    subtitulo: string;
    quem: string;
    escolha: string;
    semNegocios: string;
  };
  /** `semNumero` entra no lugar do número quando não há score ("Score —"); `aviso`, embaixo do score. */
  indicador: {
    semNumero: string;
    aviso: string;
  };
  /**
   * A receita esperada. Por negócio: `porNegocio` (`{esperado}`), `zero` (nenhum da faixa fechou),
   * `semData`; no detalhe, `preco` (`{valor}`). No topo da lista: `total` (`{total}`), ou
   * `totalQuaseNada` quando o total arredondado fica abaixo de US$ 1, `aviso`, `semDataNaConta`
   * (`{n}`) e `semDataNaContaUm`. Comissão (opcional, do vendedor): `campo` e `comissao`
   * (`{valor}`), ou `comissaoQuaseNada` pela mesma regra.
   */
  receita: TextosDaReceita;
  /**
   * O grupo Nutrição, recolhido por padrão: `mostrar` e `recolher` (`{n}`), o lote (`botao` e
   * `pergunta` com `{n}`, `confirmar`, `cancelar`) e o encaminhado (`encaminhado` com `{data}`,
   * `contestar`).
   */
  nutricao: TextosDaNutricao;
  /** O painel "Acompanhar a equipe": título de cada métrica e a frase do que ela mede. */
  painel: TextosDoPainel;
  /**
   * O score (a qualidade do negócio) e o porquê. No cartão: `numero` (`{score}`, ou o `semNumero`
   * do indicador) e `emJogo` (`{produto}`, `{preco}`). No "ver por quê": `idade` (`{dias}`,
   * `{taxa}` e `{max}` em %), ou `semData` (`{base}`) / `semScore` sem data de início; uma linha por
   * resposta (`resposta`: `{rotulo}`, `{pontos}` com sinal) e a posição (`posicao`: `{k}`, `{n}`).
   * A chance por trás: `chance` (`{chance}` em %) ou `chanceSemData`, e a conta da chance
   * (`conta`): `parcela` (`{pontos}` com sinal, `{fator}`, `{valor}`), `parcelaZero` (`{fator}`,
   * `{motivo}`) e o motivo de cada zero.
   */
  score: TextosDoScore;
  /** Por que está no grupo, por faixa de idade (tetos inclusivos; o último sem teto): `{dias}`, `{taxa}` (%). */
  motivos: { ateDias: number | null; texto: string }[];
  /** Por que está no Aborde primeiro (sem data de início): `{preco}`. */
  motivoSemData: string;
  grupos: Record<Grupo, TextoDoGrupo>;
  perguntas: { titulo: string; sim: string; nao: string };
  /** `nutricao`: `{maxDias}`; `referencia`: `{referencia}`. */
  avisos: { nutricao: string; modoLocal: string; referencia: string };
  /**
   * Onde ficam as respostas, no rodapé: `banco` com o banco compartilhado ativo; `local` sem
   * banco ou com a API fora (modo local).
   */
  respostas: { banco: string; local: string };
  /**
   * `score`: o que o score é (a qualidade; `{sim}`, `{nao}` e `{base}` são os pesos das respostas)
   * e o que a ordem da tela é. `respostasBanco` e `respostasLocal`: o mesmo
   * aviso das respostas, pelo modo. Do motor: `calculo` (`{n}` fatores), `testado`
   * (`{escolhidos}`, `{corte}`, `{referencia}`), `acerto` (`{score}` e `{idade}`, o AUC × 100) e o
   * porquê de cada fator (`motivos`).
   */
  comoFunciona: {
    score: string;
    calculo: string;
    testado: string;
    acerto: string;
    motivos: Record<MotivoDoFator, string>;
    fonte: string;
    respostasBanco: string;
    respostasLocal: string;
  };
}

/** Os textos do score (ver `TextosDaTela.score`). */
export interface TextosDoScore {
  numero: string;
  rotulo: string;
  emJogo: string;
  idade: string;
  semData: string;
  semScore: string;
  resposta: string;
  posicao: string;
  chance: string;
  chanceSemData: string;
  /** O título da conta da chance, no detalhe. */
  conta: string;
  /** O link do cartão para o detalhe (a chance, os fatores e a posição). */
  verPorque: string;
  parcela: string;
  parcelaZero: string;
  zero: Record<MotivoDaParcela, string>;
}

/** Título, rótulo curto (embaixo do número) e frase do que mede, de uma métrica do painel. */
export interface TextoDaMetrica {
  titulo: string;
  rotulo: string;
  mede: string;
}

/**
 * Os textos do painel: as 4 métricas (`parado` com `{limite}`), a tabela por vendedor (título,
 * frase e o nome de cada coluna) e, com `{x}` e `{n}`, de onde vêm as respostas: `local` quando são
 * só as deste navegador; `banco` quando vêm do banco compartilhado.
 */
export interface TextosDoPainel {
  titulo: string;
  subtitulo: string;
  receita: TextoDaMetrica;
  foqueSemConversa: TextoDaMetrica;
  parado: TextoDaMetrica;
  semInicio: TextoDaMetrica;
  tabela: {
    titulo: string;
    mede: string;
    vendedor: string;
    receita: string;
    foqueSemConversa: string;
    parado: string;
    semInicio: string;
    respostas: string;
  };
  local: string;
  banco: string;
}

/** Os textos do grupo Nutrição (ver `TextosDaTela.nutricao`). */
export interface TextosDaNutricao {
  mostrar: string;
  recolher: string;
  botao: string;
  pergunta: string;
  confirmar: string;
  cancelar: string;
  encaminhado: string;
  contestar: string;
}

/** Os textos da receita esperada (ver `TextosDaTela.receita`). */
export interface TextosDaReceita {
  porNegocio: string;
  zero: string;
  semData: string;
  preco: string;
  total: string;
  totalQuaseNada: string;
  aviso: string;
  semDataNaConta: string;
  semDataNaContaUm: string;
  campo: string;
  comissao: string;
  comissaoQuaseNada: string;
}

/** A política que põe cada deal num bloco pela idade. Trocar a política = trocar o config. */
export interface PoliticaPriorizacao {
  id: string;
  nome: string;
  versao: string;
  /** true enquanto a política final não for escolhida. */
  provisoria: boolean;
  aviso: string | null;
  /** Em ordem crescente de `ateDias`; a última tem `ateDias: null`. */
  faixas: FaixaDeIdade[];
  /** Deal sem data de engajamento: bloco próprio (`sem_inicio`), sem idade inventada. */
  semData: { rotulo: string; porque: string };
  /** Como o domínio mede a chance histórica (replay): recuo do corte e faixas de idade. */
  chance: ConfigChance;
  /** O que a nota mede, dito na tela ("diz se negócios com essa idade costumam fechar"). */
  leitura: string;
  /** Rótulo e porquê da ordenação dentro do bloco. */
  ordenacao: { rotulo: string; porque: string };
  textos: TextosDaTela;
}

/** A política em uso. Trocar a política = apontar para outro config. */
export const politicaAtiva: PoliticaPriorizacao = politicaProvisoria;

/** Uma linha da conta da chance ("+7 · Idade: 45 dias (41 a 50 dias)"). */
export interface LinhaDoScore {
  fator: string;
  pontos: number;
  /** true se o fator está no motor (mesmo valendo 0 para este negócio). */
  noScore: boolean;
  texto: string;
}

/**
 * O indicador do negócio: o score (a qualidade), o que está em jogo, o porquê do score e a chance
 * por trás. A posição na lista fica só no detalhe.
 */
export interface Indicador {
  /**
   * O score exibido, 0–100: a qualidade do negócio (a idade medida + as respostas do vendedor).
   * null sem data de início e sem resposta (ou sem chance medida no contexto).
   */
  score: number | null;
  /** A conta do score: de onde parte e o que cada resposta somou ou tirou. */
  qualidade: ScoreDeQualidade;
  /** "GTX Pro · US$ 4.821 em jogo": o valor, fora do score. */
  emJogo: string;
  /**
   * O "ver por quê" do score, uma frase por linha: a idade (ou sem data), uma linha por resposta
   * ("Decisor confirmado: +10") e a posição na lista, quando há.
   */
  porqueScore: string[];
  /** `k`º de `n` na lista do vendedor; null fora de uma lista. */
  posicao: { k: number; n: number } | null;
  /** "Na sua lista: 3º de 41 (…)" (vazio fora de uma lista). */
  posicaoTexto: string;
  /** A chance absoluta do motor, de 0 a 1; null sem data de início. */
  chance: number | null;
  /** "Chance de fechar em 3 meses: 38%" ou a frase de sem dado. */
  chanceTexto: string;
  /** A conta da chance, fator a fator, com os zeros e o motivo (vazia sem data de início). */
  parcelas: LinhaDoScore[];
  /** A taxa medida no replay para a faixa de idade (0 a 1); null sem data de início. */
  taxa: number | null;
  /** Quantos negócios a faixa teve no replay. */
  n: number | null;
  /** A faixa do replay ("41 a 50 dias"). */
  faixa: string | null;
  /** "Score 87" ou "Score —". */
  numero: string;
  /** O que o score mede, em poucas palavras. */
  rotulo: string;
  /** A primeira linha do porquê do score: a idade e quanto fechou nela, ou a falta de data. */
  motivo: string;
  /** Por que está no grupo: a idade e quanto fechou nessa idade. */
  porque: string;
  /** "Deve render cerca de US$ 1.558 em 3 meses (estimativa pela nota)." */
  receita: string;
  /** "Preço de tabela: US$ 4.821" (só no detalhe do negócio). */
  preco: string;
}

/** A ação sugerida para o deal. */
export interface ProximaAcao {
  tipo: TipoAcao;
  /** A frase da ação (do grupo, ou a da pergunta respondida com "não"). */
  texto: string;
  /** A pergunta cuja resposta "não" definiu o texto; null quando é a ação do grupo. */
  perguntaId: string | null;
}

/** Um deal na segunda-feira do vendedor: o bloco, o indicador e a ação sugerida. */
export interface ItemFila {
  deal: Deal;
  avaliacao: Avaliacao;
  /**
   * Bloco pela idade (política); `sem_inicio` sem data de início. Nenhuma resposta do vendedor
   * muda o bloco.
   */
  bloco: Bloco;
  /** Rótulo da faixa de idade ("41 a 60 dias") ou do grupo sem data. */
  faixa: string;
  indicador: Indicador;
  /** Perguntas opcionais que ainda valem para o deal. */
  pendentes: PerguntaFato[];
  /** As respostas do vendedor que valem para este negócio (do mesmo deal e do mesmo método). */
  respostas: Resposta[];
  proximaAcao: ProximaAcao;
  decisao: DecisaoDoVendedor | null;
  /** Por que está no grupo, em uma frase (a idade e quanto fechou nessa idade). */
  porque: string;
}

/** Quantos deals há em cada bloco (cada negócio em um só). */
export interface Contadores {
  total: number;
  porBloco: Record<Bloco, number>;
  /** Parte da Nutrição acima do máximo da janela (nenhum ganho chegou lá). */
  alemDaJanela: number;
}

/** A receita esperada da lista: a soma do esperado de cada negócio (sem arredondar). */
export interface ReceitaDaFila {
  /** US$ nos próximos ~3 meses, pela chance da idade × preço de tabela. */
  total: number;
  /** Negócios sem estimativa (sem data de início): não entram na conta. */
  semEstimativa: number;
}

/** A segunda-feira do vendedor. */
export interface Fila {
  /**
   * O que a tela mostra em cada grupo, na ordem da tela: valor esperado (sem data de início, só
   * o preço) desc, depois preço de tabela (desc), idade (asc, nulos por último) e id (asc). Se o
   * Foque agora de um vendedor está vazio, os negócios do Siga no ritmo dele sobem para o Foque
   * (`promovidos`); o `bloco` de cada item continua o da idade.
   */
  blocos: Record<Bloco, ItemFila[]>;
  /** Quantos negócios do Siga no ritmo foram mostrados no Foque agora (0 = nenhuma promoção). */
  promovidos: number;
  contadores: Contadores;
  receita: ReceitaDaFila;
}

const textoObrigatorio = z.string().trim().min(1);
const tetoSchema = z.number().int().min(0).nullable();
const textoDoGrupoSchema = z.strictObject({
  titulo: textoObrigatorio,
  subtitulo: textoObrigatorio,
  acao: textoObrigatorio,
  vazio: textoObrigatorio,
});

const metricaSchema = z.strictObject({
  titulo: textoObrigatorio,
  rotulo: textoObrigatorio,
  mede: textoObrigatorio,
});

/** Schema de uma política de priorização (o config validado na carga). */
export const politicaSchema = z.strictObject({
  id: textoObrigatorio.max(80),
  nome: textoObrigatorio,
  versao: textoObrigatorio,
  provisoria: z.boolean(),
  aviso: z.string().nullable(),
  faixas: z
    .array(
      z.strictObject({
        bloco: z.enum(['foque_agora', 'siga_no_ritmo', 'nutricao']),
        ateDias: tetoSchema,
        rotulo: textoObrigatorio,
        porque: textoObrigatorio,
      }),
    )
    .min(1),
  semData: z.strictObject({
    rotulo: textoObrigatorio,
    porque: textoObrigatorio,
  }),
  chance: z.strictObject({
    corteDias: z.number().int().min(1).max(365),
    faixas: z.array(z.strictObject({ ateDias: tetoSchema })).min(1),
  }),
  leitura: textoObrigatorio,
  ordenacao: z.strictObject({ rotulo: textoObrigatorio, porque: textoObrigatorio }),
  textos: z.strictObject({
    pagina: z.strictObject({
      titulo: textoObrigatorio,
      subtitulo: textoObrigatorio,
      quem: textoObrigatorio,
      escolha: textoObrigatorio,
      semNegocios: textoObrigatorio,
    }),
    indicador: z.strictObject({
      semNumero: textoObrigatorio,
      aviso: textoObrigatorio,
    }),
    receita: z.strictObject({
      porNegocio: textoObrigatorio,
      zero: textoObrigatorio,
      semData: textoObrigatorio,
      preco: textoObrigatorio,
      total: textoObrigatorio,
      totalQuaseNada: textoObrigatorio,
      aviso: textoObrigatorio,
      semDataNaConta: textoObrigatorio,
      semDataNaContaUm: textoObrigatorio,
      campo: textoObrigatorio,
      comissao: textoObrigatorio,
      comissaoQuaseNada: textoObrigatorio,
    }),
    nutricao: z.strictObject({
      mostrar: textoObrigatorio,
      recolher: textoObrigatorio,
      botao: textoObrigatorio,
      pergunta: textoObrigatorio,
      confirmar: textoObrigatorio,
      cancelar: textoObrigatorio,
      encaminhado: textoObrigatorio,
      contestar: textoObrigatorio,
    }),
    painel: z.strictObject({
      titulo: textoObrigatorio,
      subtitulo: textoObrigatorio,
      receita: metricaSchema,
      foqueSemConversa: metricaSchema,
      parado: metricaSchema,
      semInicio: metricaSchema,
      tabela: z.strictObject({
        titulo: textoObrigatorio,
        mede: textoObrigatorio,
        vendedor: textoObrigatorio,
        receita: textoObrigatorio,
        foqueSemConversa: textoObrigatorio,
        parado: textoObrigatorio,
        semInicio: textoObrigatorio,
        respostas: textoObrigatorio,
      }),
      local: textoObrigatorio,
      banco: textoObrigatorio,
    }),
    score: z.strictObject({
      numero: textoObrigatorio,
      rotulo: textoObrigatorio,
      emJogo: textoObrigatorio,
      idade: textoObrigatorio,
      semData: textoObrigatorio,
      semScore: textoObrigatorio,
      resposta: textoObrigatorio,
      posicao: textoObrigatorio,
      chance: textoObrigatorio,
      chanceSemData: textoObrigatorio,
      conta: textoObrigatorio,
      verPorque: textoObrigatorio,
      parcela: textoObrigatorio,
      parcelaZero: textoObrigatorio,
      zero: z.strictObject({
        pontua: textoObrigatorio,
        sem_dado: textoObrigatorio,
        n_pequeno: textoObrigatorio,
        fora_do_score: textoObrigatorio,
      }),
    }),
    motivos: z.array(z.strictObject({ ateDias: tetoSchema, texto: textoObrigatorio })).min(1),
    motivoSemData: textoObrigatorio,
    grupos: z.strictObject({
      foque_agora: textoDoGrupoSchema,
      siga_no_ritmo: textoDoGrupoSchema,
      nutricao: textoDoGrupoSchema,
      sem_inicio: textoDoGrupoSchema,
    }),
    perguntas: z.strictObject({
      titulo: textoObrigatorio,
      sim: textoObrigatorio,
      nao: textoObrigatorio,
    }),
    avisos: z.strictObject({
      nutricao: textoObrigatorio,
      modoLocal: textoObrigatorio,
      referencia: textoObrigatorio,
    }),
    respostas: z.strictObject({ banco: textoObrigatorio, local: textoObrigatorio }),
    comoFunciona: z.strictObject({
      score: textoObrigatorio,
      calculo: textoObrigatorio,
      testado: textoObrigatorio,
      acerto: textoObrigatorio,
      motivos: z.strictObject({
        entrou: textoObrigatorio,
        nao_melhorou: textoObrigatorio,
        n_pequeno: textoObrigatorio,
      }),
      fonte: textoObrigatorio,
      respostasBanco: textoObrigatorio,
      respostasLocal: textoObrigatorio,
    }),
  }),
});

/** Confere tetos em ordem crescente, o último sem teto. Devolve a mensagem do erro ou null. */
function erroDosTetos(tetos: readonly (number | null)[], onde: string): string | null {
  if (tetos[tetos.length - 1] !== null)
    return 'A última faixa de ' + onde + ' precisa ficar sem teto (ateDias: null).';
  let anterior = -1;
  for (const t of tetos.slice(0, -1)) {
    if (t === null) return 'Em ' + onde + ', só a última faixa pode ficar sem teto.';
    if (t <= anterior)
      return 'As faixas de ' + onde + ' precisam estar em ordem crescente de ateDias.';
    anterior = t;
  }
  return null;
}

/** Valida uma política (faixas em ordem crescente, a última sem teto, blocos e textos válidos). */
export function validarPolitica(bruto: unknown): Resultado<PoliticaPriorizacao> {
  const lido = politicaSchema.safeParse(bruto);
  if (!lido.success) {
    const detalhes = lido.error.issues.map((i) => ({
      caminho: i.path.join('.'),
      mensagem: i.message,
    }));
    return falha('politica_invalida', 'A política de priorização não segue o formato.', detalhes);
  }
  const p = lido.data;
  const erro =
    erroDosTetos(
      p.faixas.map((f) => f.ateDias),
      'idade',
    ) ??
    erroDosTetos(
      p.chance.faixas.map((f) => f.ateDias),
      'chance',
    ) ??
    erroDosTetos(
      p.textos.motivos.map((m) => m.ateDias),
      'motivos',
    );
  if (erro) return falha('politica_invalida', erro);
  return ok(p);
}

/** Troca `{chave}` pelos valores dados; chaves sem valor ficam como estão. */
export function preencher(
  modelo: string,
  valores: Readonly<Record<string, string | number>>,
): string {
  return modelo.replace(/\{(\w+)\}/g, (inteiro, chave: string) => {
    const valor = valores[chave];
    return valor === undefined ? inteiro : String(valor);
  });
}

const numero = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });

/** "2017-12-31" → "31/12/2017" (sem fuso: a data é do dataset, não do relógio). */
function dataBr(iso: string): string {
  const [a, m, d] = iso.slice(0, 10).split('-');
  return a && m && d ? d + '/' + m + '/' + a : iso;
}

/** De que idade a que idade vai cada bloco ({de, ate}; ate null = sem teto), pelas faixas da política. */
function limitesDoBloco(
  politica: PoliticaPriorizacao,
  bloco: Bloco,
): { de: number; ate: number | null } | null {
  let de = 0;
  for (const f of politica.faixas) {
    if (f.bloco === bloco) return { de, ate: f.ateDias };
    de = (f.ateDias ?? de) + 1;
  }
  return null;
}

/** Os textos dos grupos e os avisos da tela, já preenchidos com os limites da política e a janela. */
export interface TextosPreenchidos {
  grupos: Record<Grupo, TextoDoGrupo>;
  avisos: { nutricao: string; modoLocal: string; referencia: string };
}

/**
 * Preenche os textos dos grupos (`{de}`, `{ate}`, `{limite}`) com os limites da política e os
 * avisos com a janela (`{maxDias}`, `{referencia}` em dd/mm/aaaa). Ex.: "Nenhum negócio seu está
 * entre 41 e 60 dias hoje."
 */
export function textosDaTela(politica: PoliticaPriorizacao, janela: Janela): TextosPreenchidos {
  const { textos } = politica;
  const limiteNutricao = limitesDoBloco(politica, 'nutricao');
  const limite = limiteNutricao ? Math.max(limiteNutricao.de - 1, 0) : 0;
  const grupos = {} as Record<Grupo, TextoDoGrupo>;
  for (const g of GRUPOS) {
    const faixa = g === 'sem_inicio' ? null : limitesDoBloco(politica, g);
    const valores: Record<string, string | number> = { limite };
    if (faixa) {
      valores.de = faixa.de;
      if (faixa.ate !== null) valores.ate = faixa.ate;
    }
    const t = textos.grupos[g];
    grupos[g] = {
      titulo: preencher(t.titulo, valores),
      subtitulo: preencher(t.subtitulo, valores),
      acao: preencher(t.acao, valores),
      vazio: preencher(t.vazio, valores),
    };
  }
  return {
    grupos,
    avisos: {
      nutricao: preencher(textos.avisos.nutricao, { maxDias: janela.maxDias }),
      modoLocal: textos.avisos.modoLocal,
      referencia: preencher(textos.avisos.referencia, { referencia: dataBr(janela.referencia) }),
    },
  };
}

function faixaDaIdade(politica: PoliticaPriorizacao, idade: number): FaixaDeIdade {
  const faixa = politica.faixas.find((f) => f.ateDias === null || idade <= f.ateDias);
  // validarPolitica garante a última faixa sem teto; a última serve de rede para config não validado
  return faixa ?? (politica.faixas[politica.faixas.length - 1] as FaixaDeIdade);
}

/** A frase da receita esperada do negócio: sem data, zero (nenhum da faixa fechou) ou o valor. */
function textoDaReceita(avaliacao: Avaliacao, textos: TextosDaReceita): string {
  if (avaliacao.idadeDias === null) return textos.semData;
  if (avaliacao.esperado === null || Math.round(avaliacao.esperado) === 0) return textos.zero;
  return preencher(textos.porNegocio, { esperado: numero.format(avaliacao.esperado) });
}

/** Uma taxa (0 a 1) em % inteiro; acima de zero e abaixo de 0,5%, "menos de 1". */
export function emPorcento(taxa: number): string {
  if (taxa > 0 && taxa < 0.005) return 'menos de 1';
  return numero.format(Math.round(taxa * 100));
}

/** As respostas que entram no score: as das perguntas que valem para o bloco, na ordem do método. */
function respostasNoScore(
  metodo: MetodoQualificacao,
  bloco: Bloco,
  respostas: RespostasDoDeal | null,
): Resposta[] {
  if (!respostas) return [];
  return metodo.perguntas.flatMap((p) => {
    if (!p.aplicaEm.includes(bloco)) return [];
    const r = respostas.respostas.find((x) => x.perguntaId === p.id);
    return r ? [r] : [];
  });
}

/**
 * O score e as frases do negócio. O score é a qualidade: a parte do dado (vem na avaliação) mais
 * o ajuste de cada resposta do vendedor que vale para o bloco. O valor fica fora do score, numa
 * linha própria ("US$ … em jogo"); a posição na lista entra só no porquê. A chance absoluta e a
 * conta por fator ficam para o detalhe. Sem replay no contexto (só fora de `criarServicos`), o
 * porquê do grupo vem da faixa da política.
 */
function montarIndicador(
  deal: Deal,
  avaliacao: Avaliacao,
  politica: PoliticaPriorizacao,
  faixa: FaixaDeIdade | null,
  metodo: MetodoQualificacao,
  respostas: readonly Resposta[],
  config: ConfigQualidade,
): Indicador {
  const { indicador, motivos, motivoSemData, receita: textosReceita } = politica.textos;
  const ts = politica.textos.score;
  const { chance, score, posicao } = avaliacao;
  const idade = avaliacao.idadeDias;
  const taxa = idade === null ? null : (chance?.taxa ?? null);
  const emJogo = preencher(ts.emJogo, {
    produto: deal.produto,
    preco: numero.format(avaliacao.emJogo),
  });
  let porque = preencher(motivoSemData, { preco: numero.format(avaliacao.emJogo) });
  if (idade !== null) {
    const dias = numero.format(idade);
    const modelo = motivos.find((m) => m.ateDias === null || idade <= m.ateDias)?.texto;
    porque =
      taxa === null || modelo === undefined
        ? (faixa?.porque ?? porque)
        : preencher(modelo, { dias, taxa: emPorcento(taxa) });
  }

  // o score: com idade, só se a chance foi medida (sem ela, nada a pontuar, nem com respostas)
  const dado = avaliacao.qualidade?.parte ?? null;
  const qualidade: ScoreDeQualidade =
    idade !== null && dado === null
      ? { score: null, base: null, temIdade: true, ajustes: [] }
      : pontuarQualidade(dado, respostas, config);
  let motivo =
    qualidade.score === null ? ts.semScore : preencher(ts.semData, { base: qualidade.base ?? 0 });
  if (idade !== null) {
    // a frase diz o que fechou de fato (a taxa do replay); a conta usa a chance do motor
    const q = avaliacao.qualidade;
    const fechou = q?.fecharam ?? (q ? { taxa: q.chance, maxima: q.maxima } : null);
    motivo = fechou
      ? preencher(ts.idade, {
          dias: numero.format(idade),
          taxa: emPorcento(fechou.taxa),
          max: emPorcento(fechou.maxima),
        })
      : porque;
  }
  const rotuloDaResposta = (perguntaId: string, valor: 'sim' | 'nao') => {
    const p = metodo.perguntas.find((x) => x.id === perguntaId);
    return (
      p?.noScore?.[valor] ?? (p?.rotulo ?? perguntaId) + ': ' + (valor === 'sim' ? 'Sim' : 'Não')
    );
  };
  const posicaoTexto = posicao ? preencher(ts.posicao, { k: posicao.k, n: posicao.n }) : '';
  const porqueScore = [
    motivo,
    ...qualidade.ajustes.map((a) =>
      preencher(ts.resposta, {
        rotulo: rotuloDaResposta(a.perguntaId, a.valor),
        pontos: (a.pontos > 0 ? '+' : '−') + Math.abs(a.pontos),
      }),
    ),
    ...(posicaoTexto ? [posicaoTexto] : []),
  ];

  // a chance do motor; sem motor no contexto, a taxa da faixa de idade no replay
  const chanceAbsoluta = score?.chance ?? taxa;
  return {
    score: qualidade.score,
    qualidade,
    emJogo,
    porqueScore,
    posicao: posicao ? { k: posicao.k, n: posicao.n } : null,
    posicaoTexto,
    chance: chanceAbsoluta,
    chanceTexto:
      chanceAbsoluta === null
        ? ts.chanceSemData
        : preencher(ts.chance, { chance: emPorcento(chanceAbsoluta) }),
    parcelas: (score?.parcelas ?? []).map((p) => ({
      fator: p.fator,
      pontos: p.pontos,
      noScore: p.noScore,
      texto:
        p.pontos === 0
          ? preencher(ts.parcelaZero, { fator: p.rotulo, motivo: ts.zero[p.motivo] })
          : preencher(ts.parcela, {
              pontos: (p.pontos > 0 ? '+' : '−') + Math.abs(p.pontos),
              fator: p.rotulo,
              valor: (p.valor ?? '') + (p.faixa && p.faixa !== p.valor ? ' (' + p.faixa + ')' : ''),
            }),
    })),
    taxa,
    n: idade === null ? null : (chance?.n ?? null),
    faixa: idade === null ? null : (chance?.faixa ?? null),
    numero: preencher(ts.numero, { score: qualidade.score ?? indicador.semNumero }),
    rotulo: ts.rotulo,
    motivo,
    porque,
    receita: textoDaReceita(avaliacao, textosReceita),
    preco: preencher(textosReceita.preco, { valor: numero.format(avaliacao.emJogo) }),
  };
}

/** Os textos de "Como a nota funciona" que vêm do motor, já preenchidos. */
export interface TextosDoMotor {
  score: string;
  calculo: string;
  testado: string;
  acerto: string;
  motivos: Record<MotivoDoFator, string>;
}

/** O que o score é, em "Como a nota funciona", com os pesos das respostas do config. */
export function textoDoScore(
  politica: PoliticaPriorizacao,
  qualidade: ConfigQualidade = configQualidadePadrao,
): string {
  return preencher(politica.textos.comoFunciona.score, {
    sim: Math.abs(qualidade.porSim),
    nao: Math.abs(qualidade.porNao),
    base: qualidade.semDataBase,
  });
}

/**
 * Preenche os textos do motor: o que o score é (com os pesos das respostas, `{sim}`, `{nao}` e
 * `{base}`), quantos fatores, quais entraram, os recortes e o acerto (AUC × 100).
 */
export function textosDoMotor(
  politica: PoliticaPriorizacao,
  motor: MotorDePontos,
  qualidade: ConfigQualidade = configQualidadePadrao,
): TextosDoMotor {
  const t = politica.textos.comoFunciona;
  const rotulos = motor.escolhidos.map(
    (id) => motor.fatores.find((f) => f.id === id)?.rotulo ?? id,
  );
  const cem = (auc: number | null) => (auc === null ? '–' : numero.format(auc * 100));
  return {
    score: textoDoScore(politica, qualidade),
    calculo: preencher(t.calculo, { n: motor.fatores.length }),
    testado: preencher(t.testado, {
      escolhidos: rotulos.join(', ').toLowerCase(),
      corte: dataBr(motor.validacao.corte),
      referencia: dataBr(motor.validacao.ate),
    }),
    acerto: preencher(t.acerto, { score: cem(motor.aucScore), idade: cem(motor.aucIdade) }),
    motivos: t.motivos,
  };
}

function tipoDaAcao(bloco: Bloco): TipoAcao {
  if (bloco === 'foque_agora') return 'avancar_hoje';
  if (bloco === 'nutricao') return 'encaminhar_para_nutricao';
  if (bloco === 'sem_inicio') return 'qualificar';
  return 'manter_ritmo';
}

function acaoSugerida(
  bloco: Bloco,
  politica: PoliticaPriorizacao,
  metodo: MetodoQualificacao,
  respostas: RespostasDoDeal | null,
): ProximaAcao {
  const tipo = tipoDaAcao(bloco);
  const doGrupo = politica.textos.grupos[bloco].acao;
  if (bloco === 'nutricao' || !respostas) return { tipo, texto: doGrupo, perguntaId: null };
  for (const pergunta of metodo.perguntas) {
    if (!pergunta.acaoSeNao || !pergunta.aplicaEm.includes(bloco)) continue;
    const resposta = respostas.respostas.find((r) => r.perguntaId === pergunta.id);
    if (resposta?.valor === 'nao')
      return { tipo, texto: pergunta.acaoSeNao, perguntaId: pergunta.id };
  }
  return { tipo, texto: doGrupo, perguntaId: null };
}

/**
 * Classifica um deal: a política põe no bloco pela idade (sem data → `sem_inicio`, "Aborde
 * primeiro"). Nenhuma resposta muda o bloco: cada resposta soma ou tira do score (pelos pesos de
 * `qualidade`), e a resposta "não" troca a ação pela frase da pergunta (a primeira, na ordem do
 * método). Só valem as perguntas que se aplicam ao bloco; respostas de outro deal ou de outro
 * método são ignoradas. Em Nutrição, a ação é encaminhar para nutrição.
 */
export function classificar(
  deal: Deal,
  avaliacao: Avaliacao,
  politica: PoliticaPriorizacao,
  metodo: MetodoQualificacao,
  respostas: RespostasDoDeal | null,
  qualidade: ConfigQualidade = configQualidadePadrao,
): ItemFila {
  const semIdade = avaliacao.idadeDias === null;
  const faixaDoDeal = semIdade ? null : faixaDaIdade(politica, avaliacao.idadeDias as number);
  const bloco: Bloco = faixaDoDeal?.bloco ?? 'sem_inicio';
  const faixa = faixaDoDeal?.rotulo ?? politica.semData.rotulo;

  const validas =
    respostas && respostas.dealId === deal.id && respostas.metodoId === metodo.id
      ? respostas
      : null;
  const indicador = montarIndicador(
    deal,
    avaliacao,
    politica,
    faixaDoDeal,
    metodo,
    respostasNoScore(metodo, bloco, validas),
    qualidade,
  );

  return {
    deal,
    avaliacao,
    bloco,
    faixa,
    indicador,
    pendentes: perguntasPendentes(metodo, bloco, validas),
    respostas: validas?.respostas ?? [],
    proximaAcao: acaoSugerida(bloco, politica, metodo, validas),
    decisao: validas?.decisao ?? null,
    porque: indicador.porque,
  };
}

/** O negócio como a posição o vê: o grupo da tela (pela ordem de `GRUPOS`) e o que há a ganhar. */
function naLista(item: ItemFila, grupo: Grupo): EntradaDaLista {
  return {
    id: item.deal.id,
    grupo: GRUPOS.indexOf(grupo),
    esperado: item.avaliacao.esperado,
    emJogo: item.avaliacao.emJogo,
    idadeDias: item.avaliacao.idadeDias,
  };
}

/**
 * A ordem dentro do grupo: a da posição (valor esperado, ou só o preço sem data de início;
 * empate, o preço maior, o mais novo e o id). Num filtro com mais de um vendedor, compara pelo
 * mesmo valor.
 */
function ordemNoBloco(a: ItemFila, b: ItemFila): number {
  return compararNaLista(naLista(a, a.bloco), naLista(b, a.bloco));
}

/**
 * Em que grupo a tela mostra cada negócio: o bloco da idade, menos para o vendedor com o Foque
 * agora vazio, cujo Siga no ritmo aparece no Foque (o `bloco` do item continua o da idade).
 */
export function grupoNaTela(itens: readonly ItemFila[]): Map<string, Grupo> {
  const comFoque = new Set(
    itens.filter((i) => i.bloco === 'foque_agora').map((i) => i.deal.vendedor),
  );
  return new Map(
    itens.map((i) => [
      i.deal.id,
      i.bloco === 'siga_no_ritmo' && !comFoque.has(i.deal.vendedor) ? 'foque_agora' : i.bloco,
    ]),
  );
}

/**
 * A posição de cada negócio na lista aberta de um vendedor, na ordem em que a tela os
 * mostra. Primeiro o grupo (Foque agora, Siga no ritmo, Aborde primeiro, Nutrição, com a promoção
 * do Siga), depois o que há a ganhar. A posição diz por onde começar; não é o score.
 */
export function posicionarNaTela(itens: readonly ItemFila[]): Map<string, PosicaoNaLista> {
  const grupos = grupoNaTela(itens);
  return posicionar(itens.map((i) => naLista(i, grupos.get(i.deal.id) ?? i.bloco)));
}

/**
 * Monta a segunda-feira a partir dos itens classificados. Vendedor com o Foque agora vazio tem
 * os negócios do Siga no ritmo mostrados no Foque (todos, na ordem da tela), e o Siga dele fica
 * vazio: o Foque nunca fica zerado enquanto houver negócio vivo. Com o Foque não vazio, nada muda.
 */
export function montarFila(itens: readonly ItemFila[]): Fila {
  const blocos = Object.fromEntries(BLOCOS.map((b) => [b, [] as ItemFila[]])) as Record<
    Bloco,
    ItemFila[]
  >;
  const grupos = grupoNaTela(itens);
  let promovidos = 0;
  for (const item of itens) {
    const grupo = grupos.get(item.deal.id) ?? item.bloco;
    if (grupo !== item.bloco) promovidos += 1;
    blocos[grupo].push(item);
  }
  for (const b of BLOCOS) blocos[b].sort(ordemNoBloco);
  return {
    blocos,
    promovidos,
    contadores: {
      total: itens.length,
      porBloco: Object.fromEntries(BLOCOS.map((b) => [b, blocos[b].length])) as Record<
        Bloco,
        number
      >,
      alemDaJanela: blocos.nutricao.filter((i) => i.avaliacao.situacao === 'alem_da_janela').length,
    },
    receita: {
      total: itens.reduce((soma, i) => soma + (i.avaliacao.esperado ?? 0), 0),
      semEstimativa: itens.filter((i) => i.avaliacao.esperado === null).length,
    },
  };
}

/** Um número do painel com a porcentagem sobre a base dele (0 a 1; 0 quando a base é vazia). */
export interface Parte {
  n: number;
  base: number;
  pct: number;
}

function parte(n: number, base: number): Parte {
  return { n, base, pct: base === 0 ? 0 : n / base };
}

/** Quantos negócios e quanto está em jogo neles (a soma do preço de tabela, US$). */
export interface EmJogo {
  n: number;
  valor: number;
}

/** As 4 métricas medidas numa lista de negócios (a do time ou a de um vendedor). */
export interface MetricasDoPainel {
  /** Abertos na lista. */
  total: number;
  /**
   * 1. Receita esperada: a soma de chance × preço dos abertos com data de início (US$, nos
   * próximos ~3 meses, sem contar negócios novos).
   */
  receita: number;
  /**
   * 2. Negócios que a tela mostra em Foque agora (com a promoção do Siga no ritmo) sem "Sim" para
   * a pergunta da próxima conversa: `n` e `valor` = "Não" + sem resposta. `foque` = todos os do
   * Foque agora da tela.
   */
  foqueSemConversa: EmJogo & { foque: number; sim: number; nao: number; semResposta: number };
  /** 3. Pipeline parado: abertos no bloco Nutrição (acima do limite da política). */
  parado: EmJogo;
  /** 4. Leads sem primeira conversa: abertos sem data de início. */
  semInicio: EmJogo;
  /** Respostas registradas: negócios com ao menos uma resposta ÷ negócios em que alguma pergunta vale. */
  respostas: Parte;
}

/** Uma linha da tabela por vendedor: as mesmas métricas, na lista dele. */
export interface LinhaDoPainel extends MetricasDoPainel {
  vendedor: string;
  manager: string;
  regiao: string;
}

/**
 * O painel "Acompanhar a equipe": onde o time está perdendo dinheiro, num filtro, só leitura. No
 * topo, as 4 métricas do filtro; embaixo, uma linha por vendedor do filtro (todos, com zero quando
 * for o caso), do que mais tem Foque agora sem próxima conversa para o que menos tem. Sem ranking
 * por taxa de ganho (a taxa por vendedor não prevê ganho fora da amostra).
 */
export interface Painel extends MetricasDoPainel {
  /** O limite do bloco Nutrição (dias), para a frase do que mede. */
  limiteParadoDias: number;
  vendedores: LinhaDoPainel[];
}

/** Soma o que está em jogo numa lista de negócios. */
function emJogo(itens: readonly ItemFila[]): EmJogo {
  return { n: itens.length, valor: itens.reduce((soma, i) => soma + i.avaliacao.emJogo, 0) };
}

/**
 * Monta o painel a partir da fila do filtro (já com as respostas e com a promoção do Siga feita
 * por vendedor), do time do filtro (cada vendedor ganha uma linha, mesmo sem negócio), do método
 * (qual pergunta é a da próxima conversa e quais valem em cada bloco) e da política (o limite do
 * bloco Nutrição).
 */
export function montarPainel(
  fila: Fila,
  time: readonly MembroDoTime[],
  metodo: MetodoQualificacao,
  politica: PoliticaPriorizacao,
): Painel {
  // o Foque agora é o da tela do vendedor: com o Foque dele vazio, o Siga sobe para lá
  const naTela = new Map<string, Grupo>();
  for (const b of BLOCOS) for (const i of fila.blocos[b]) naTela.set(i.deal.id, b);
  // a pergunta da próxima conversa é a ligada ao critério de compromisso no método
  const idProximoPasso =
    metodo.criterios.find((c) => c.id === 'compromisso')?.perguntaId ?? 'proximo_passo';
  const proximoPasso = (i: ItemFila) =>
    i.respostas.find((r) => r.perguntaId === idProximoPasso)?.valor;
  const valemPerguntas = (i: ItemFila) =>
    metodo.perguntas.some((p) => p.aplicaEm.includes(i.bloco));

  function medir(itens: readonly ItemFila[]): MetricasDoPainel {
    const foque = itens.filter((i) => naTela.get(i.deal.id) === 'foque_agora');
    const semSim = foque.filter((i) => proximoPasso(i) !== 'sim');
    const nao = foque.filter((i) => proximoPasso(i) === 'nao').length;
    const comPerguntas = itens.filter(valemPerguntas);
    return {
      total: itens.length,
      receita: itens.reduce((soma, i) => soma + (i.avaliacao.esperado ?? 0), 0),
      foqueSemConversa: {
        ...emJogo(semSim),
        foque: foque.length,
        sim: foque.length - semSim.length,
        nao,
        semResposta: semSim.length - nao,
      },
      parado: emJogo(itens.filter((i) => i.bloco === 'nutricao')),
      semInicio: emJogo(itens.filter((i) => i.bloco === 'sem_inicio')),
      respostas: parte(
        comPerguntas.filter((i) => i.respostas.length > 0).length,
        comPerguntas.length,
      ),
    };
  }

  const itens = BLOCOS.flatMap((b) => fila.blocos[b]);
  const porVendedor = new Map<string, ItemFila[]>();
  for (const i of itens)
    porVendedor.set(i.deal.vendedor, [...(porVendedor.get(i.deal.vendedor) ?? []), i]);
  const vendedores = time
    .map((v) => ({
      vendedor: v.nome,
      manager: v.manager,
      regiao: v.regiao,
      ...medir(porVendedor.get(v.nome) ?? []),
    }))
    .sort(
      (a, b) =>
        b.foqueSemConversa.n - a.foqueSemConversa.n ||
        b.foqueSemConversa.valor - a.foqueSemConversa.valor ||
        a.vendedor.localeCompare(b.vendedor, 'pt-BR'),
    );
  const limite = limitesDoBloco(politica, 'nutricao');
  return {
    ...medir(itens),
    limiteParadoDias: limite ? Math.max(limite.de - 1, 0) : 0,
    vendedores,
  };
}
