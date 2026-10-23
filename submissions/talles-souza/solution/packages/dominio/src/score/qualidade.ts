/**
 * O score: a qualidade do negócio, de 0 a 100. Duas partes.
 * 1. O dado: a chance da faixa de idade do negócio ÷ a maior chance entre as faixas (as chances
 *    do motor), × 100. A idade é o único fator que sobreviveu no histórico.
 * 2. O vendedor: as respostas às perguntas (quem decide, o problema do cliente, a próxima conversa
 *    com data). Cada "Sim" soma e cada "Não" tira o peso do config; sem resposta, nada muda. Os
 *    pesos são heurística declarada: o histórico não tem essas respostas.
 * Sem data de início não há idade: sem nenhuma resposta, o score fica em branco; com pelo menos
 * uma, parte do ponto do config. O preço não entra: o score diz se o negócio é bom, o preço diz
 * quanto está em jogo e a ordem da tela diz por onde começar.
 */

/** Os pesos das respostas (heurística declarada, em `qualidade.config.ts`). */
export interface ConfigQualidade {
  /** Quanto cada "Sim" soma ao score. */
  porSim: number;
  /** Quanto cada "Não" muda o score (negativo). */
  porNao: number;
  /** Sem data de início, com pelo menos uma resposta: o score parte daqui. */
  semDataBase: number;
}

/** A parte do dado de um negócio: a chance da faixa dele contra a melhor faixa. */
export interface QualidadeDoDado {
  /** A chance da faixa de idade do negócio (0 a 1). */
  chance: number;
  /** A maior chance entre as faixas de idade (0 a 1). */
  maxima: number;
  /** `round(100 × chance ÷ maxima)`, de 0 a 100. */
  parte: number;
  /**
   * O que de fato fechou no replay: a taxa da faixa do negócio e a maior taxa entre as faixas
   * (0 a 1). É o que a frase "x% fecharam" mostra; a chance do motor é essa taxa suavizada.
   * null sem replay no contexto.
   */
  fecharam: { taxa: number; maxima: number } | null;
}

/** Uma resposta do vendedor, como o score a vê. */
export interface RespostaNoScore {
  perguntaId: string;
  valor: 'sim' | 'nao';
}

/** O que uma resposta fez com o score. */
export interface AjusteDoScore extends RespostaNoScore {
  /** +10 para "Sim", −15 para "Não" (pelo config). */
  pontos: number;
}

/** O score de qualidade de um negócio, com a conta. */
export interface ScoreDeQualidade {
  /** 0 a 100; null = sem data de início e sem nenhuma resposta. */
  score: number | null;
  /** De onde a conta parte: a parte do dado, ou o ponto do config sem data; null sem nada. */
  base: number | null;
  /** true quando a base é a parte do dado (o negócio tem idade). */
  temIdade: boolean;
  /** Uma linha por resposta, na ordem dada. */
  ajustes: AjusteDoScore[];
}

const limitar = (v: number) => Math.min(100, Math.max(0, v));

/** `round(100 × chance ÷ maxima)`, de 0 a 100; maxima 0 (nenhuma faixa fechou) = 0. */
export function parteDoDado(chance: number, maxima: number): number {
  if (!(maxima > 0)) return 0;
  return limitar(Math.round((100 * chance) / maxima));
}

const maior = (valores: readonly number[]) => valores.reduce((m, c) => Math.max(m, c), 0);

/**
 * A parte do dado de uma chance, contra a maior chance de uma lista de faixas. `fecharam`: a taxa
 * observada da faixa e as taxas de todas as faixas (o que a frase mostra), se houver replay.
 */
export function qualidadeDoDado(
  chance: number,
  faixas: readonly number[],
  fecharam: { taxa: number; faixas: readonly number[] } | null = null,
): QualidadeDoDado {
  const maxima = maior(faixas);
  return {
    chance,
    maxima,
    parte: parteDoDado(chance, maxima),
    fecharam: fecharam ? { taxa: fecharam.taxa, maxima: maior(fecharam.faixas) } : null,
  };
}

/**
 * O score de qualidade: a parte do dado (null sem data de início) mais o ajuste de cada resposta,
 * limitado a 0–100. Sem data e sem resposta = null; sem data com resposta, parte do
 * `semDataBase`. O preço do negócio não entra aqui de propósito.
 */
export function pontuarQualidade(
  dado: number | null,
  respostas: readonly RespostaNoScore[],
  config: ConfigQualidade,
): ScoreDeQualidade {
  const ajustes = respostas.map((r) => ({
    perguntaId: r.perguntaId,
    valor: r.valor,
    pontos: r.valor === 'sim' ? config.porSim : config.porNao,
  }));
  const temIdade = dado !== null;
  if (!temIdade && ajustes.length === 0) return { score: null, base: null, temIdade, ajustes };
  const base = dado ?? config.semDataBase;
  const score = limitar(ajustes.reduce((s, a) => s + a.pontos, base));
  return { score, base, temIdade, ajustes };
}
