/** Contrato HTTP do contexto `score`: os fatos explicados de um deal ou de um lead novo. */
import { z } from 'zod';
import { idDealSchema, novoLeadSchema, type Deal } from '../pipeline';
import type { Avaliacao, ChanceHistorica, MotorDePontos, TabelaDePontos } from './index';

export const ROTA_AVALIAR = '/api/score/avaliar';
/** `GET`: a chance histórica por faixa de idade, medida pelo replay. */
export const ROTA_CHANCE = '/api/score/chance';
/** `GET`: a tabela de pontos por atributo (Perfil × Interesse), medida no histórico. */
export const ROTA_PONTOS = '/api/score/pontos';

/** `GET`: o motor de pontos (fatores, AUC na validação, escolhidos, pontos por categoria). */
export const ROTA_MOTOR = '/api/score/motor';

export type RespostaMotor = MotorDePontos;
export type RespostaChance = ChanceHistorica;
export type RespostaPontos = TabelaDePontos;

/** Um deal existente OU um lead novo. */
export const pedidoAvaliacaoSchema = z.union([
  z.strictObject({ dealId: idDealSchema }),
  z.strictObject({ lead: novoLeadSchema }),
]);
export type PedidoAvaliacao = z.infer<typeof pedidoAvaliacaoSchema>;

export interface RespostaAvaliacao {
  deal: Deal;
  avaliacao: Avaliacao;
}
