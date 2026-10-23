/**
 * A posição do negócio na lista ABERTA do vendedor dele, na ordem em que a tela mostra os
 * negócios. Primeiro o grupo (Foque agora, Siga no ritmo, Aborde primeiro, Nutrição, já com a
 * promoção do Siga quando o Foque está vazio); dentro do grupo, o que há a ganhar (valor esperado
 * = chance do motor × preço de tabela; sem data de início, só o preço). A posição diz por onde
 * começar; não é o score (o score mede a qualidade do negócio: ver `qualidade.ts`). Cada negócio
 * tem posição própria: o empate se desfaz pelo preço, depois pela idade e pelo id.
 */

/** O que a posição precisa saber de cada negócio da lista. */
export interface EntradaDaLista {
  id: string;
  /** A ordem do grupo em que a tela mostra o negócio (0 = o primeiro grupo da tela). */
  grupo: number;
  /** Chance × preço (US$); null = sem data de início (a chance não dá pra medir). */
  esperado: number | null;
  /** Preço de tabela (US$). */
  emJogo: number;
  /** Dias desde o início; null = sem data de início. */
  idadeDias: number | null;
}

/** A posição de um negócio na lista do vendedor. */
export interface PosicaoNaLista {
  /** 1 = o primeiro; cada negócio tem a sua (nenhum empate divide posição). */
  k: number;
  /** Quantos negócios abertos a lista tem. */
  n: number;
  /** O que pôs o negócio na posição dentro do grupo: o valor esperado ou, sem data, só o preço. */
  pelo: 'esperado' | 'preco';
}

/** O valor que ordena: o esperado; sem data de início, a chance não existe e entra só o preço. */
export function valorNaLista(e: EntradaDaLista): number {
  return e.esperado ?? e.emJogo;
}

/**
 * Ordem da lista: o grupo da tela primeiro; dentro dele, maior valor primeiro; empate, o de preço
 * maior; depois o mais novo (sem data por último, entre os de mesmo valor) e o id. Só dá 0 para o
 * mesmo negócio.
 */
export function compararNaLista(a: EntradaDaLista, b: EntradaDaLista): number {
  const porValor = a.grupo - b.grupo || valorNaLista(b) - valorNaLista(a) || b.emJogo - a.emJogo;
  if (porValor !== 0) return porValor;
  if (a.idadeDias !== b.idadeDias) {
    if (a.idadeDias === null) return 1;
    if (b.idadeDias === null) return -1;
    return a.idadeDias - b.idadeDias;
  }
  return a.id < b.id ? -1 : a.id > b.id ? 1 : 0;
}

/**
 * Posiciona cada negócio da lista na ordem da tela. Lista vazia = mapa vazio.
 * Determinístico: a mesma lista, em qualquer ordem de entrada, dá as mesmas posições.
 */
export function posicionar(lista: readonly EntradaDaLista[]): Map<string, PosicaoNaLista> {
  const n = lista.length;
  const posicoes = new Map<string, PosicaoNaLista>();
  [...lista].sort(compararNaLista).forEach((e, i) => {
    const k = i + 1;
    posicoes.set(e.id, {
      k,
      n,
      pelo: e.esperado === null ? 'preco' : 'esperado',
    });
  });
  return posicoes;
}
