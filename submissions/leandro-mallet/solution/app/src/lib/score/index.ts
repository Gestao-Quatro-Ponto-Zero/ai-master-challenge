/**
 * Motor do lead score (lógica pura). A rotina diária/semanal faz o I/O:
 * - semanal (domingo da data de negócio): calcular() → celulas, padroes e fit_vendedores; planejarRedistribuicao() → chamadas;
 * - diário: calcular() → deals (nota, componentes, motivos, marcadores, ação); planejarRepasses() → chamadas;
 * - lead novo: rotearLeadNovo().
 * Referência e paridade: solution/scoring/regra.py (tests/score-paridade.test.ts).
 */
export * from "./regra";
export * from "./movimentos";
