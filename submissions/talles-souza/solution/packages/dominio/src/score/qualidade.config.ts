/**
 * Os pesos das respostas do vendedor no score de qualidade. Heurística declarada: o histórico não
 * tem essas respostas, então nenhum destes números foi medido; são uma escolha, e trocar a escolha
 * = trocar este config. A parte do dado (a idade) não mora aqui: ela sai do motor, na carga.
 */
import type { ConfigQualidade } from './qualidade';

export const configQualidadePadrao: ConfigQualidade = {
  // heurística declarada: o histórico não tem essas respostas. Cada "Sim" soma isso ao score
  porSim: 10,
  // heurística declarada: o histórico não tem essas respostas. Cada "Não" tira isso do score
  porNao: -15,
  // negócio sem data de início (sem idade): com pelo menos uma resposta, o score parte daqui
  semDataBase: 50,
};
