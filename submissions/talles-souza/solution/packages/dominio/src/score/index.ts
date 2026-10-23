/**
 * Contexto `score`: motor puro que lê os fatos de um deal e os explica em frases (sem LLM):
 * a idade contra a janela dos ganhos, a chance histórica de quem tinha a mesma idade, o preço de
 * tabela, a receita esperada (chance × preço) e o contexto que não decide nada (conta, porte,
 * setor). Falta de dado
 * vira "sem dado", nunca penalidade. Também mede, no histórico, a tabela de pontos por atributo
 * (Perfil × Interesse): é ela que mostra por que a nota usa só o tempo.
 */
import {
  situacaoNaJanela,
  type Conta,
  type Deal,
  type Janela,
  type Produto,
  type SituacaoJanela,
} from '../pipeline';
import { chanceDosPontos, chancesDaIdade, type Pontuador, type ScoreDoDeal } from './motor';
import type { PosicaoNaLista } from './posicao';
import { qualidadeDoDado, type QualidadeDoDado } from './qualidade';

export * from './http';
export * from './motor';
export * from './posicao';
export * from './qualidade';
export { configMotorPadrao } from './motor.config';
export { configQualidadePadrao } from './qualidade.config';

/** Um fato do deal, com a frase que o explica. */
export interface Fato {
  id: 'idade' | 'em_jogo';
  rotulo: string;
  /** null = sem dado. */
  valor: number | null;
  /** "aberto há 40 d; 95% dos ganhos fecharam em até 116 d". */
  detalhe: string;
}

/** A chance histórica que vale para um deal (a da faixa de idade dele no replay). */
export interface ChanceDoDeal {
  /** Rótulo da faixa do replay ("41 a 50 dias"). */
  faixa: string;
  /** Ganhos ÷ população da faixa (0 a 1); null se a faixa não teve negócio no replay. */
  taxa: number | null;
  /** Quantos negócios a faixa teve no replay. */
  n: number;
}

/** Os fatos de um deal, explicados. */
export interface Avaliacao {
  dealId: string;
  situacao: SituacaoJanela;
  /** null = sem data de engajamento (prospecção). */
  idadeDias: number | null;
  /** Preço de tabela do produto (US$). */
  emJogo: number;
  /**
   * Receita esperada nos próximos ~3 meses (US$): a chance do score, sem arredondar, × o preço de
   * tabela (sem motor no contexto, a taxa da faixa de idade no replay). null sem idade (sem data
   * de início) ou sem replay no contexto. Ordena dentro do bloco.
   */
  esperado: number | null;
  /**
   * A chance absoluta do motor de pontos (0–100 = chance × 100), com a conta por fator; null sem
   * motor ou sem data de início. Não é o score exibido: o score é a qualidade (`qualidade` mais as
   * respostas do vendedor, na priorização).
   */
  score: ScoreDoDeal | null;
  /**
   * A parte do dado no score de qualidade: a chance da faixa de idade ÷ a maior chance entre as
   * faixas. null sem data de início, negócio fechado ou sem chance no contexto.
   */
  qualidade: QualidadeDoDado | null;
  /**
   * A posição na lista aberta do vendedor, na ordem da tela (o grupo, depois o valor esperado; sem
   * data de início, o preço): por onde começar, não o score. null fora de uma lista (negócio
   * fechado, ou `avaliar` sozinho).
   */
  posicao: PosicaoNaLista | null;
  /** Chance histórica para a idade do deal; null sem idade (ou sem replay no contexto). */
  chance: ChanceDoDeal | null;
  fatos: Fato[];
  /** Contexto que não decide nada ("conta de 4.540 funcionários", "sem dado de conta"). */
  contexto: string[];
  /** Os fatos em uma frase. */
  explicacao: string;
  /** "Hoje" do dataset, contra o qual a idade foi medida (ISO `AAAA-MM-DD`). */
  referencia: string;
  /** O ganho mais longo do histórico (dias): o teto que o dataset mostra. */
  maxJanelaDias: number;
}

/** Como medir a chance histórica: o recuo do corte e as faixas de idade (tetos inclusivos). */
export interface ConfigChance {
  /** O corte do replay fica `corteDias` antes da referência. */
  corteDias: number;
  /** Em ordem crescente de `ateDias`; a última tem `ateDias: null` (sem teto). */
  faixas: { ateDias: number | null }[];
}

/** Uma faixa de idade do replay, com o que aconteceu com ela até a referência. */
export interface FaixaDeChance {
  /** Idade mínima da faixa (dias, inclusiva). */
  de: number;
  /** Idade máxima (inclusiva); null = sem teto. */
  ateDias: number | null;
  /** "41 a 50 dias", "acima de 90 dias". */
  rotulo: string;
  /** Negócios abertos no corte com essa idade. */
  n: number;
  /** Quantos deles ganharam até a referência. */
  ganhos: number;
  /** `ganhos ÷ n`; null se `n` = 0. */
  taxa: number | null;
}

/**
 * A chance histórica medida por replay: no corte (referência − `corteDias`), pega os negócios
 * já engajados e ainda abertos, mede a idade de cada um no corte e conta quantos ganharam até a
 * referência, por faixa de idade.
 */
export interface ChanceHistorica {
  referencia: string;
  corte: string;
  corteDias: number;
  /** Negócios abertos no corte (a população do replay). */
  populacao: number;
  ganhos: number;
  /** `ganhos ÷ populacao`; null se a população for vazia. */
  taxaGeral: number | null;
  faixas: FaixaDeChance[];
}

/** Um valor de atributo com a taxa de fechamento e os pontos (taxa ÷ taxa de base). */
export interface ValorPontuado {
  valor: string;
  n: number;
  ganhos: number;
  taxa: number;
  pontos: number;
}

/** Um atributo da tabela de pontos (método HubSpot: pontos = taxa do valor ÷ taxa geral). */
export interface AtributoPontuado {
  id: 'setor' | 'produto' | 'porte' | 'escritorio' | 'vendedor' | 'idade';
  /** Perfil = quem é o cliente e o que compra; Interesse = o tempo do negócio. */
  eixo: 'perfil' | 'interesse';
  rotulo: string;
  /** A taxa que serve de base aos pontos (a geral dos fechados ou a do replay). */
  taxaBase: number;
  valores: ValorPontuado[];
  minPontos: number;
  maxPontos: number;
}

/** A tabela de pontos por atributo, medida no histórico. */
export interface TabelaDePontos {
  /** Ganhos ÷ fechados (Won + Lost). */
  taxaGeral: number;
  fechados: number;
  atributos: AtributoPontuado[];
}

/** O que o motor precisa saber do pipeline para avaliar qualquer deal. */
export interface ContextoScore {
  janela: Janela;
  catalogo: readonly Produto[];
  contas: readonly Conta[];
  /** A chance histórica por idade; sem ela, `Avaliacao.chance` sai null. */
  chance?: ChanceHistorica | undefined;
  /** O motor de pontos medido; sem ele, `Avaliacao.score` sai null e o esperado vem da faixa. */
  pontuador?: Pontuador | undefined;
}

const DIA_MS = 86_400_000;
const inteiro = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });

function diaUtc(iso: string): number {
  return Date.parse(iso + 'T00:00:00Z');
}

/** "US$ 4.821". */
function dolares(valor: number): string {
  return 'US$ ' + inteiro.format(valor);
}

function rotuloDaFaixa(de: number, ate: number | null): string {
  return ate === null
    ? 'acima de ' + inteiro.format(de - 1) + ' dias'
    : inteiro.format(de) + ' a ' + inteiro.format(ate) + ' dias';
}

function faixaDe<T extends { ateDias: number | null }>(
  faixas: readonly T[],
  idade: number,
): T | undefined {
  return faixas.find((f) => f.ateDias === null || idade <= f.ateDias);
}

/**
 * Mede a chance histórica por idade com o replay: corte = referência − `corteDias`; população =
 * deals com engajamento até o corte e ainda abertos nele (sem fechamento ou fechados depois);
 * idade no corte; ganho = Won com fechamento até a referência.
 */
export function medirChance(
  deals: readonly Deal[],
  referencia: string,
  config: ConfigChance,
): ChanceHistorica {
  const fim = diaUtc(referencia);
  const corte = fim - config.corteDias * DIA_MS;
  let de = 0;
  const faixas: FaixaDeChance[] = config.faixas.map((f) => {
    const faixa: FaixaDeChance = {
      de,
      ateDias: f.ateDias,
      rotulo: rotuloDaFaixa(de, f.ateDias),
      n: 0,
      ganhos: 0,
      taxa: null,
    };
    de = (f.ateDias ?? de) + 1;
    return faixa;
  });
  let populacao = 0;
  let ganhos = 0;
  for (const d of deals) {
    if (d.dataEngajamento === null) continue;
    const engajou = diaUtc(d.dataEngajamento);
    const fechou = d.dataFechamento === null ? null : diaUtc(d.dataFechamento);
    if (engajou > corte || (fechou !== null && fechou <= corte)) continue;
    const faixa = faixaDe(faixas, Math.round((corte - engajou) / DIA_MS));
    if (!faixa) continue;
    const ganhou = d.estagio === 'Won' && fechou !== null && fechou <= fim;
    faixa.n += 1;
    populacao += 1;
    if (ganhou) {
      faixa.ganhos += 1;
      ganhos += 1;
    }
  }
  for (const f of faixas) f.taxa = f.n === 0 ? null : f.ganhos / f.n;
  return {
    referencia,
    corte: new Date(corte).toISOString().slice(0, 10),
    corteDias: config.corteDias,
    populacao,
    ganhos,
    taxaGeral: populacao === 0 ? null : ganhos / populacao,
    faixas,
  };
}

/** A faixa do replay que vale para uma idade (null sem idade). */
export function chanceDaIdade(
  chance: ChanceHistorica,
  idadeDias: number | null,
): ChanceDoDeal | null {
  if (idadeDias === null) return null;
  const faixa = faixaDe(chance.faixas, idadeDias);
  if (!faixa) return null;
  return {
    faixa: faixa.rotulo,
    taxa: faixa.taxa,
    n: faixa.n,
  };
}

/** Percentil por interpolação linear entre os vizinhos (o padrão do numpy e do pandas). */
function percentil(ordenados: readonly number[], p: number): number {
  const h = (ordenados.length - 1) * p;
  const baixo = Math.floor(h);
  const a = ordenados[baixo] ?? 0;
  const b = ordenados[Math.min(baixo + 1, ordenados.length - 1)] ?? a;
  return a + (h - baixo) * (b - a);
}

function pontuar(
  id: AtributoPontuado['id'],
  eixo: AtributoPontuado['eixo'],
  rotulo: string,
  taxaBase: number,
  grupos: readonly { valor: string; n: number; ganhos: number }[],
): AtributoPontuado {
  const valores = grupos
    .filter((g) => g.n > 0)
    .map((g) => {
      const taxa = g.ganhos / g.n;
      return {
        valor: g.valor,
        n: g.n,
        ganhos: g.ganhos,
        taxa,
        pontos: taxaBase === 0 ? 0 : taxa / taxaBase,
      };
    });
  const pontos = valores.map((v) => v.pontos);
  return {
    id,
    eixo,
    rotulo,
    taxaBase,
    valores,
    minPontos: pontos.length ? Math.min(...pontos) : 0,
    maxPontos: pontos.length ? Math.max(...pontos) : 0,
  };
}

function agrupar(
  fechados: readonly Deal[],
  chave: (d: Deal) => string | null,
  ordem?: readonly string[],
) {
  const grupos = new Map<string, { valor: string; n: number; ganhos: number }>();
  for (const v of ordem ?? []) grupos.set(v, { valor: v, n: 0, ganhos: 0 });
  for (const d of fechados) {
    const valor = chave(d);
    if (valor === null) continue;
    const g = grupos.get(valor) ?? { valor, n: 0, ganhos: 0 };
    g.n += 1;
    if (d.estagio === 'Won') g.ganhos += 1;
    grupos.set(valor, g);
  }
  const lista = [...grupos.values()];
  return ordem ? lista : lista.sort((a, b) => a.valor.localeCompare(b.valor, 'pt-BR'));
}

const QUARTIS = ['Q1 menor', 'Q2', 'Q3', 'Q4 maior'] as const;

/**
 * Mede a tabela de pontos (método HubSpot: pontos = taxa de fechamento do valor ÷ taxa geral).
 * Perfil, nos fechados (Won + Lost): setor, produto, porte da conta (quartis de receita),
 * escritório e vendedor. Interesse: a faixa de idade do replay, com a taxa do replay por base.
 */
export function medirPontos(deals: readonly Deal[], chance: ChanceHistorica): TabelaDePontos {
  const fechados = deals.filter((d) => d.estagio === 'Won' || d.estagio === 'Lost');
  const ganhos = fechados.filter((d) => d.estagio === 'Won').length;
  const taxaGeral = fechados.length === 0 ? 0 : ganhos / fechados.length;

  const receitas = fechados
    .map((d) => d.receitaConta)
    .filter((r): r is number => r !== null)
    .sort((a, b) => a - b);
  const cortes = receitas.length ? [0.25, 0.5, 0.75].map((p) => percentil(receitas, p)) : [];
  const quartil = (d: Deal): string | null => {
    if (d.receitaConta === null || cortes.length === 0) return null;
    const i = cortes.findIndex((c) => (d.receitaConta as number) <= c);
    return QUARTIS[i === -1 ? 3 : i] ?? null;
  };

  const interesse = chance.faixas.map((f) => ({ valor: f.rotulo, n: f.n, ganhos: f.ganhos }));
  return {
    taxaGeral,
    fechados: fechados.length,
    atributos: [
      pontuar(
        'setor',
        'perfil',
        'Setor',
        taxaGeral,
        agrupar(fechados, (d) => d.setor),
      ),
      pontuar(
        'produto',
        'perfil',
        'Produto',
        taxaGeral,
        agrupar(fechados, (d) => d.produto),
      ),
      pontuar(
        'porte',
        'perfil',
        'Tamanho da empresa (receita)',
        taxaGeral,
        agrupar(fechados, quartil, QUARTIS),
      ),
      pontuar(
        'escritorio',
        'perfil',
        'Escritório',
        taxaGeral,
        agrupar(fechados, (d) => d.regiao),
      ),
      pontuar(
        'vendedor',
        'perfil',
        'Vendedor',
        taxaGeral,
        agrupar(fechados, (d) => d.vendedor),
      ),
      pontuar('idade', 'interesse', 'Idade do negócio', chance.taxaGeral ?? 0, interesse),
    ],
  };
}

function detalheDaIdade(deal: Deal, situacao: SituacaoJanela, janela: Janela): string {
  if (!deal.aberto) {
    const como = deal.estagio === 'Won' ? 'ganho' : 'perdido';
    return deal.duracaoDias === null
      ? 'negócio fechado (' + como + ')'
      : 'negócio fechado (' + como + ') em ' + inteiro.format(deal.duracaoDias) + ' d';
  }
  if (deal.idadeDias === null) return 'em prospecção, ainda sem data de engajamento';
  const aberto = 'aberto há ' + inteiro.format(deal.idadeDias) + ' d';
  const p95 = '95% dos ganhos fecharam em até ' + inteiro.format(janela.p95Dias) + ' d';
  if (situacao === 'na_janela') return aberto + '; ' + p95;
  if (situacao === 'perto_do_limite')
    return aberto + '; ' + p95 + ' e o mais longo levou ' + inteiro.format(janela.maxDias) + ' d';
  return (
    aberto + '; nenhum ganho deste histórico levou mais de ' + inteiro.format(janela.maxDias) + ' d'
  );
}

function contextoDaConta(deal: Deal, contas: readonly Conta[]): string[] {
  if (deal.conta === null) return ['sem dado de conta'];
  const conta = contas.find((c) => c.nome === deal.conta);
  const funcionarios = deal.funcionarios ?? conta?.funcionarios ?? null;
  const setor = deal.setor ?? conta?.setor ?? null;
  return [
    'conta ' + deal.conta,
    funcionarios === null
      ? 'sem dado de porte'
      : 'conta de ' + inteiro.format(funcionarios) + ' funcionários',
    setor === null ? 'sem dado de setor' : 'setor ' + setor,
  ];
}

/**
 * A parte do dado no score de qualidade: com o motor, a chance só da idade (os pontos da parcela
 * de idade, pela conversão do motor) contra a maior chance entre as faixas de idade do motor; sem
 * motor, a taxa da faixa no replay contra a maior taxa do replay. null sem idade.
 */
function qualidadeDaIdade(
  deal: Deal,
  contexto: ContextoScore,
  score: ScoreDoDeal | null,
  taxaDaFaixa: number | null,
): QualidadeDoDado | null {
  if (!deal.aberto || deal.idadeDias === null) return null;
  const { pontuador } = contexto;
  const fecharam =
    taxaDaFaixa === null || !contexto.chance
      ? null
      : { taxa: taxaDaFaixa, faixas: contexto.chance.faixas.map((f) => f.taxa ?? 0) };
  if (pontuador) {
    if (score === null) return null;
    const idade = score.parcelas.find((p) => p.fator === 'idade');
    const chance = chanceDosPontos(pontuador.motor, idade?.pontos ?? 0);
    return qualidadeDoDado(
      chance,
      chancesDaIdade(pontuador.motor).map((f) => f.chance),
      fecharam,
    );
  }
  if (fecharam === null) return null;
  return qualidadeDoDado(fecharam.taxa, fecharam.faixas, fecharam);
}

function maiuscula(frase: string): string {
  return frase.charAt(0).toUpperCase() + frase.slice(1);
}

/**
 * Lê e explica os fatos de um deal: a idade contra a janela dos ganhos, a chance histórica da
 * mesma idade (se o contexto traz o replay), o preço de tabela do catálogo e a receita esperada
 * (taxa da faixa × preço).
 * Conta, porte e setor entram só como contexto; sem conta, o contexto diz "sem dado de conta" e
 * nada é descontado.
 */
export function avaliar(deal: Deal, contexto: ContextoScore): Avaliacao {
  const { janela } = contexto;
  const situacao = situacaoNaJanela(deal, janela);
  const emJogo =
    contexto.catalogo.find((p) => p.nome === deal.produto)?.precoTabela ?? deal.precoTabela;
  const idade: Fato = {
    id: 'idade',
    rotulo: 'Idade',
    valor: deal.idadeDias,
    detalhe: detalheDaIdade(deal, situacao, janela),
  };
  const emJogoFato: Fato = {
    id: 'em_jogo',
    rotulo: 'Preço de tabela',
    valor: emJogo,
    detalhe: deal.produto + ': preço de tabela ' + dolares(emJogo),
  };
  const chance = contexto.chance
    ? chanceDaIdade(contexto.chance, deal.aberto ? deal.idadeDias : null)
    : null;
  const score = deal.aberto && contexto.pontuador ? contexto.pontuador.pontuar(deal) : null;
  const taxaDaFaixa = chance?.taxa ?? null;
  let esperado: number | null = taxaDaFaixa === null ? null : taxaDaFaixa * emJogo;
  if (contexto.pontuador) esperado = score === null ? null : score.chance * emJogo;
  return {
    dealId: deal.id,
    situacao,
    idadeDias: deal.idadeDias,
    emJogo,
    esperado,
    score,
    qualidade: qualidadeDaIdade(deal, contexto, score, taxaDaFaixa),
    posicao: null,
    chance,
    fatos: [idade, emJogoFato],
    contexto: contextoDaConta(deal, contexto.contas),
    explicacao: maiuscula(idade.detalhe) + '. ' + emJogoFato.detalhe + '.',
    referencia: janela.referencia,
    maxJanelaDias: janela.maxDias,
  };
}
