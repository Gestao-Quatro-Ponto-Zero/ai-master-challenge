/**
 * Os limites do motor de pontos. Nenhum peso mora aqui: os pontos de cada fator saem do
 * histórico, na carga. Aqui ficam só as regras do método (de onde vêm os cortes do replay, o n
 * mínimo, a suavização, o ganho mínimo de AUC para um fator entrar e as faixas dos derivados).
 */
import type { ConfigMotor } from './motor';

export const configMotorPadrao: ConfigMotor = {
  // treino: abertos em R − 184 d, desfecho "ganhou até R − 92 d"
  treinoDias: 184,
  // validação: abertos em R − 92 d, desfecho "ganhou até R"; os pesos finais saem deste recorte
  horizonteDias: 92,
  // categoria com menos negócios que isso no recorte vale 0 ponto
  nMinimo: 30,
  // 20 negócios fictícios na taxa geral (o peso de 10 ganhos + 10 perdas) somados a cada categoria
  suavizacao: 20,
  // um fator só entra se o AUC do score na validação subir pelo menos isso
  ganhoMinimoAuc: 0.005,
  // pontos = escala × ln(taxa da categoria ÷ taxa geral) (método HubSpot, escala log)
  escala: 10,
  // idade ÷ mediana do ciclo dos ganhos: tetos das faixas (a última faixa fica sem teto)
  faixasCiclo: [0.5, 1, 1.5, 2, 3],
  // contadores e razões viram quartis medidos no próprio corte
  quantis: 4,
  // Prospecting não tem data de início: o replay não tem nenhum deles, então fica sem score
  pontuarSemData: false,
  // razão: taxa base × e^(pontos ÷ escala), com teto 1. Calibrada no recorte 30/09→31/12 (+0,2% na receita; log-odds dava −14%)
  conversao: 'razao', // calibrada: no recorte 30/09→31/12 erra +0,2% na receita (log_odds: −14%); ver evidencias/motor-de-pontos
};
