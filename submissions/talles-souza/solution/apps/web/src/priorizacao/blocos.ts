/**
 * Os grupos da tela, na ordem do domínio (Foque agora, Siga no ritmo, Aborde primeiro,
 * Nutrição): cada grupo é um bloco. Título, subtítulo, ação e frase de vazio vêm dos textos da
 * política; aqui fica só o identificador estável de cada grupo nos `data-testid`.
 */
import { GRUPOS, type Fila, type Grupo, type ItemFila } from '@lead-scorer/dominio/priorizacao';

/** Os grupos na ordem da tela. */
export const ORDEM: readonly Grupo[] = GRUPOS;

/** Identificador de cada grupo nos `data-testid` (`bloco-<slug>`, `contador-<slug>`). */
export const SLUG: Readonly<Record<Grupo, string>> = {
  foque_agora: 'foque-agora',
  siga_no_ritmo: 'siga-no-ritmo',
  nutricao: 'nutricao',
  sem_inicio: 'ainda-nao-comecou',
};

/** O `data-testid` do contêiner de cada grupo. */
export function testidDoGrupo(g: Grupo): string {
  return g === 'sem_inicio' ? 'grupo-ainda-nao-comecou' : 'bloco-' + SLUG[g];
}

/** Os negócios da fila por grupo da tela, na ordem de cada bloco (o que vale mais primeiro). */
export function agruparPorGrupo(fila: Fila): Record<Grupo, ItemFila[]> {
  return fila.blocos;
}

/** Quantos negócios em cada grupo (contado dos itens, igual ao que a tela mostra). */
export function contarGrupos(fila: Fila): Record<Grupo, number> {
  const g = agruparPorGrupo(fila);
  return Object.fromEntries(ORDEM.map((k) => [k, g[k].length])) as Record<Grupo, number>;
}
