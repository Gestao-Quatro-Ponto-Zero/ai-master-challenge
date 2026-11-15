// Marcações locais que mais de uma tela lê e grava (via ctx.store, só neste navegador).
//   Decisão sobre deal sem desfecho: por deal, a mesma no Foco da semana e no Pipeline.
//   Deals tratados: por vendedor e data, só no Foco da semana.
//   Fase movida à mão: por deal, só no Pipeline. Não muda o score nem os números das outras telas.

export const STALE_DECISIONS = {
  segue: { label: 'Segue de pé', short: 'Segue' },
  encerrar: { label: 'Encerrar', short: 'Encerrar' },
};

const decisionKey = (dealId) => `sem-desfecho:${dealId}`;
const treatedKey = (seller, date) => `foco:tratados:${seller}:${date}`;

// 'segue' | 'encerrar' | null
export function getDecision(store, dealId) {
  const value = store.get(decisionKey(dealId));
  return Object.hasOwn(STALE_DECISIONS, value) ? value : null;
}

// value null (ou desconhecido) desfaz a marcação.
export function setDecision(store, dealId, value) {
  if (Object.hasOwn(STALE_DECISIONS, value)) store.set(decisionKey(dealId), value);
  else store.remove(decisionKey(dealId));
}

export function getTreated(store, seller, date) {
  const saved = store.get(treatedKey(seller, date), []);
  return new Set(Array.isArray(saved) ? saved : []);
}

export function setTreated(store, seller, date, ids) {
  if (ids.size) store.set(treatedKey(seller, date), [...ids]);
  else store.remove(treatedKey(seller, date));
}

const MOVES_KEY = 'pipeline:movidos';

// { dealId: chave da coluna para onde o cartão foi arrastado }
export function getMoves(store) {
  const saved = store.get(MOVES_KEY, {});
  return saved && typeof saved === 'object' && !Array.isArray(saved) ? saved : {};
}

// column null desfaz o movimento.
export function setMove(store, dealId, column) {
  const moves = { ...getMoves(store) };
  if (column) moves[dealId] = column;
  else delete moves[dealId];
  if (Object.keys(moves).length) store.set(MOVES_KEY, moves);
  else store.remove(MOVES_KEY);
}
