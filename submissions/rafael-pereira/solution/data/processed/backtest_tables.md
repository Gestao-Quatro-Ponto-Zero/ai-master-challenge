# Tabelas do backtest

Gerado por `python -m scorer.validate`; não editar à mão.

## Diagnóstico: taxa de ganho por idade e fase do trimestre

Taxa de ganho em 90 dias por idade do deal na foto, com o número de casos entre parênteses. Fotos de treino de hoje (31/12/2017): fim de trimestre = 31/03/2017, 30/06/2017 e 30/09/2017; meio de trimestre = 30/04/2017, 31/05/2017, 31/07/2017 e 31/08/2017.

| Idade do deal na foto | Fotos de fim de trimestre | Fotos de meio de trimestre | Todas juntas |
| :--- | ---: | ---: | ---: |
| 0 a 30 dias | 49,5% (2.055) | 31,7% (2.375) | 40,0% (4.430) |
| 31 a 60 dias | 41,7% (1.449) | 41,9% (1.953) | 41,8% (3.402) |
| 61 a 90 dias | 15,9% (793) | 48,3% (1.541) | 37,3% (2.334) |
| 91 a 105 dias | 0,0% (153) | 39,9% (499) | 30,5% (652) |
| 106 a 120 dias | 0,0% (138) | 22,8% (281) | 15,3% (419) |

Mesmas fotos, uma coluna por mês do trimestre:

| Idade do deal na foto | 1º mês do trimestre (jan, abr, jul, out) | 2º mês (fev, mai, ago, nov) | 3º mês (mar, jun, set, dez) |
| :--- | ---: | ---: | ---: |
| 0 a 30 dias | 29,5% (1.146) | 33,8% (1.229) | 49,5% (2.055) |
| 31 a 60 dias | 52,6% (1.068) | 29,0% (885) | 41,7% (1.449) |
| 61 a 90 dias | 47,2% (911) | 49,8% (630) | 15,9% (793) |
| 91 a 105 dias | 37,4% (227) | 41,9% (272) | 0,0% (153) |
| 106 a 120 dias | 12,3% (114) | 29,9% (167) | 0,0% (138) |

## Critério pré-registrado, corte a corte

| Corte | Score v2 | Valor | Recência | Aleatório (média) | Aleatório (p95) | Margem sobre o melhor baseline | Vence os 4? |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 30/06/2017 | 61,0% | 48,6% | 27,7% | 20,0% | 23,4% | +12,4 pp | sim |
| 31/07/2017 | 57,4% | 48,7% | 12,8% | 20,1% | 23,4% | +8,7 pp | sim |
| 31/08/2017 | 59,9% | 48,2% | 31,6% | 19,8% | 23,0% | +11,8 pp | sim |
| 30/09/2017 | 71,7% | 47,1% | 46,8% | 20,3% | 24,4% | +24,7 pp | sim |

Receita capturada no top 20%, curva v2. Empate é diferença de até 0,01 e não vence. Resultado: **PASSOU**.
- curva v1 (platô + queda, todas as fotos): passou; receita média do score nos cortes: 61,1%.
- curva v2 (faixas isotônicas, fotos da mesma fase do trimestre): passou; receita média do score nos cortes: 62,5%.

## Backtest: corte × método

| Corte | Método | AUC | Ganhos capturados no top 20% | Receita capturada no top 20% |
| :--- | :--- | ---: | ---: | ---: |
| 30/06/2017 | Score v2 (valor esperado, curva por faixas) | 0,66 | 25,7% | 61,0% |
| 30/06/2017 | Score v1 (platô, antes da correção) | 0,66 | 25,8% | **61,3%** |
| 30/06/2017 | Ordenar por valor | 0,48 | 19,6% | 48,6% |
| 30/06/2017 | Mais recentes primeiro | **0,73** | **29,3%** | 27,7% |
| 30/06/2017 | Aleatório (média de sorteios) | 0,50 (0,47 a 0,52) | 19,9% (18,1% a 21,8%) | 20,0% (16,8% a 23,4%) |
| 30/06/2017 | Só a chance v2 (diagnóstico) | 0,73 | 28,8% | 28,3% |
| 31/07/2017 | Score v2 (valor esperado, curva por faixas) | 0,63 | 24,8% | 57,4% |
| 31/07/2017 | Score v1 (platô, antes da correção) | **0,64** | **25,1%** | **57,9%** |
| 31/07/2017 | Ordenar por valor | 0,51 | 20,5% | 48,7% |
| 31/07/2017 | Mais recentes primeiro | 0,58 | 12,2% | 12,8% |
| 31/07/2017 | Aleatório (média de sorteios) | 0,50 (0,48 a 0,52) | 20,0% (18,1% a 22,0%) | 20,1% (17,2% a 23,4%) |
| 31/07/2017 | Só a chance v2 (diagnóstico) | 0,64 | 24,8% | 24,7% |
| 31/08/2017 | Score v2 (valor esperado, curva por faixas) | 0,63 | 26,1% | 59,9% |
| 31/08/2017 | Score v1 (platô, antes da correção) | 0,63 | 26,4% | **60,7%** |
| 31/08/2017 | Ordenar por valor | 0,50 | 20,4% | 48,2% |
| 31/08/2017 | Mais recentes primeiro | **0,66** | **34,0%** | 31,6% |
| 31/08/2017 | Aleatório (média de sorteios) | 0,50 (0,48 a 0,52) | 19,9% (18,1% a 22,0%) | 19,8% (16,4% a 23,0%) |
| 31/08/2017 | Só a chance v2 (diagnóstico) | 0,66 | 25,9% | 26,0% |
| 30/09/2017 | Score v2 (valor esperado, curva por faixas) | 0,72 | 32,8% | **71,7%** |
| 30/09/2017 | Score v1 (platô, antes da correção) | 0,65 | 27,9% | 64,8% |
| 30/09/2017 | Ordenar por valor | 0,48 | 19,4% | 47,1% |
| 30/09/2017 | Mais recentes primeiro | **0,83** | **43,6%** | 46,8% |
| 30/09/2017 | Aleatório (média de sorteios) | 0,50 (0,48 a 0,53) | 20,2% (17,5% a 22,5%) | 20,3% (16,1% a 24,4%) |
| 30/09/2017 | Só a chance v2 (diagnóstico) | 0,83 | 43,0% | 45,5% |

Em negrito, o melhor entre score v2, score v1, valor, recência e aleatório. No aleatório, entre parênteses, o intervalo de p5 a p95 de 200 sorteios.

## Média dos cortes

| Método | AUC | Ganhos capturados no top 20% | Receita capturada no top 20% |
| :--- | ---: | ---: | ---: |
| Score v2 (valor esperado, curva por faixas) | 0,66 | 27,4% | 62,5% |
| Score v1 (platô, antes da correção) | 0,64 | 26,3% | 61,1% |
| Ordenar por valor | 0,49 | 20,0% | 48,1% |
| Mais recentes primeiro | 0,70 | 29,8% | 29,7% |
| Aleatório (média de sorteios) | 0,50 | 20,0% | 20,0% |
| Só a chance v2 (diagnóstico) | 0,72 | 30,6% | 31,1% |

Média simples dos 4 cortes. Brier da chance v2: 0,180 (v1: 0,185) contra 0,221 da taxa média de treino (log-loss 0,512, v1: 0,524, contra 0,636), sobre ganhos em 90 dias.

## Ordem dentro do Foque

População: engaging abertos em T com idade de até 90 dias; mesma população para todos os métodos. Desfecho: ganho até 31/12/2017.

**AUC**

| Corte | Deals | Score v2 (curva por faixas) | Score v1 (platô) | Ordenar por valor | Mais recentes primeiro | Aleatório (referência) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| 30/06/2017 | 1.336 | 0,50 | 0,50 | 0,48 | **0,61** | 0,50 |
| 31/07/2017 | 1.703 | **0,51** | **0,51** | **0,51** | 0,39 | 0,50 |
| 31/08/2017 | 1.566 | **0,51** | **0,51** | **0,51** | 0,51 | 0,50 |
| 30/09/2017 | 1.684 | 0,55 | 0,50 | 0,50 | **0,73** | 0,50 |
| **Média dos 4 cortes** | — | 0,52 | 0,51 | 0,50 | **0,56** | 0,50 |

**Receita ganha capturada pelo top 20%**

| Corte | Deals | Score v2 (curva por faixas) | Score v1 (platô) | Ordenar por valor | Mais recentes primeiro | Aleatório (referência) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| 30/06/2017 | 1.336 | 50,5% | **50,7%** | 48,3% | 22,2% | 20,1% |
| 31/07/2017 | 1.703 | **49,2%** | **49,2%** | **49,2%** | 10,2% | 20,1% |
| 31/08/2017 | 1.566 | **50,4%** | **50,4%** | **50,4%** | 28,0% | 20,0% |
| 30/09/2017 | 1.684 | **59,9%** | 48,5% | 48,5% | 33,7% | 20,1% |
| **Média dos 4 cortes** | — | **52,5%** | 49,7% | 49,1% | 23,5% | 20,1% |

**Diferença na receita capturada, com IC por bootstrap (pp)**

| Corte | Score v2 menos score v1 | Score v2 menos valor |
| :--- | ---: | ---: |
| 30/06/2017 | -0,1 pp (IC -2,5 pp a +2,2 pp) | +2,3 pp (IC -0,5 pp a +4,8 pp) |
| 31/07/2017 | 0,0 pp (IC 0,0 pp a 0,0 pp) | 0,0 pp (IC 0,0 pp a 0,0 pp) |
| 31/08/2017 | 0,0 pp (IC 0,0 pp a 0,0 pp) | 0,0 pp (IC 0,0 pp a 0,0 pp) |
| 30/09/2017 | +11,4 pp (IC +7,5 pp a +14,8 pp) | +11,4 pp (IC +7,5 pp a +14,8 pp) |

Em negrito, o melhor entre score v2, score v1, valor e recência (o aleatório é só referência).

## Categorias por corte

| Corte | Lista | Deals | Ganhos até 31/12/2017 | Receita ganha | % da receita | Valor de tabela | Valor esperado |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| 30/06/2017 | Foque | 1.283 | 47,2% | US$ 1.439.736 | 99,9% | US$ 3.202.532 | US$ 1.543.971 |
| 30/06/2017 | Reative | 70 | 4,3% | US$ 1.714 | 0,1% | US$ 175.739 | US$ 22.511 |
| 30/06/2017 | Limpe | 333 | 0,0% | US$ 0 | 0,0% | US$ 838.536 | US$ 344 |
| 31/07/2017 | Foque | 1.848 | 40,0% | US$ 1.791.976 | 99,9% | US$ 4.470.015 | US$ 2.071.386 |
| 31/07/2017 | Reative | 75 | 4,0% | US$ 1.714 | 0,1% | US$ 189.545 | US$ 23.646 |
| 31/07/2017 | Limpe | 334 | 0,0% | US$ 0 | 0,0% | US$ 839.632 | US$ 100 |
| 31/08/2017 | Foque | 1.831 | 34,8% | US$ 1.450.144 | 100,0% | US$ 4.266.512 | US$ 1.817.151 |
| 31/08/2017 | Reative | 26 | 0,0% | US$ 0 | 0,0% | US$ 83.815 | US$ 15.094 |
| 31/08/2017 | Limpe | 408 | 0,0% | US$ 0 | 0,0% | US$ 1.038.920 | US$ 4.775 |
| 30/09/2017 | Foque | 1.626 | 34,1% | US$ 1.243.729 | 99,3% | US$ 3.693.202 | US$ 1.679.751 |
| 30/09/2017 | Reative | 77 | 5,2% | US$ 8.199 | 0,7% | US$ 192.165 | US$ 19.864 |
| 30/09/2017 | Limpe | 706 | 0,0% | US$ 0 | 0,0% | US$ 1.878.123 | US$ 195 |

## Calibração

| Corte | Deals | Brier da v2 | Brier da v1 | Brier da constante | Log-loss da v2 | Log-loss da v1 | Log-loss da constante |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 30/06/2017 | 1.686 | 0,189 | 0,189 | 0,239 | 0,530 | 0,529 | 0,672 |
| 31/07/2017 | 2.257 | 0,200 | 0,199 | 0,232 | 0,561 | 0,560 | 0,658 |
| 31/08/2017 | 2.265 | 0,182 | 0,184 | 0,209 | 0,522 | 0,526 | 0,611 |
| 30/09/2017 | 2.409 | 0,151 | 0,169 | 0,205 | 0,435 | 0,483 | 0,602 |

| Corte | Idade | Deals | Chance média da v2 | Chance média da v1 | Ganhos em 90 dias (observado) |
| :--- | :--- | ---: | ---: | ---: | ---: |
| 30/06/2017 | 0 a 30 dias | 692 | 49,3% | 49,0% | 51,2% |
| 30/06/2017 | 31 a 60 dias | 454 | 48,6% | 49,0% | 44,5% |
| 30/06/2017 | 61 a 90 dias | 190 | 34,4% | 32,9% | 21,6% |
| 30/06/2017 | 91 a 120 dias | 133 | 0,9% | 0,8% | 0,0% |
| 30/06/2017 | 121 a 150 dias | 103 | 0,0% | 0,0% | 0,0% |
| 30/06/2017 | 151 dias ou mais | 114 | 0,0% | 0,0% | 0,0% |
| 31/07/2017 | 0 a 30 dias | 720 | 46,8% | 46,9% | 24,3% |
| 31/07/2017 | 31 a 60 dias | 522 | 46,8% | 46,9% | 53,8% |
| 31/07/2017 | 61 a 90 dias | 461 | 46,8% | 46,9% | 45,6% |
| 31/07/2017 | 91 a 120 dias | 198 | 34,0% | 30,6% | 22,7% |
| 31/07/2017 | 121 a 150 dias | 133 | 1,0% | 0,3% | 0,0% |
| 31/07/2017 | 151 dias ou mais | 223 | 0,0% | 0,0% | 0,0% |
| 31/08/2017 | 0 a 30 dias | 662 | 43,4% | 46,0% | 29,2% |
| 31/08/2017 | 31 a 60 dias | 587 | 43,4% | 46,0% | 21,3% |
| 31/08/2017 | 61 a 90 dias | 317 | 43,4% | 46,0% | 51,7% |
| 31/08/2017 | 91 a 120 dias | 211 | 39,8% | 34,1% | 32,2% |
| 31/08/2017 | 121 a 150 dias | 128 | 18,6% | 8,7% | 2,3% |
| 31/08/2017 | 151 dias ou mais | 360 | 0,1% | 0,7% | 0,0% |
| 30/09/2017 | 0 a 30 dias | 679 | 50,1% | 45,6% | 48,0% |
| 30/09/2017 | 31 a 60 dias | 545 | 45,9% | 45,6% | 33,8% |
| 30/09/2017 | 61 a 90 dias | 460 | 33,7% | 45,6% | 6,7% |
| 30/09/2017 | 91 a 120 dias | 118 | 0,8% | 25,4% | 0,0% |
| 30/09/2017 | 121 a 150 dias | 123 | 0,0% | 4,6% | 0,0% |
| 30/09/2017 | 151 dias ou mais | 484 | 0,0% | 0,2% | 0,0% |

## Bootstrap

| Corte | Score v2 menos valor | Score v2 menos recência |
| :--- | ---: | ---: |
| 30/06/2017 | +12,4 pp (IC +9,3 pp a +15,7 pp) | +33,3 pp (IC +26,7 pp a +40,5 pp) |
| 31/07/2017 | +8,7 pp (IC +6,4 pp a +11,3 pp) | +44,6 pp (IC +39,2 pp a +50,1 pp) |
| 31/08/2017 | +11,8 pp (IC +9,1 pp a +14,6 pp) | +28,3 pp (IC +22,1 pp a +34,6 pp) |
| 30/09/2017 | +24,7 pp (IC +20,3 pp a +30,0 pp) | +24,9 pp (IC +17,8 pp a +32,0 pp) |

Diferença na receita capturada no top 20%, em pontos percentuais; IC de 2,5% a 97,5% por 1.000 reamostragens dos deals do corte (semente 0).

## Foque por idade

| Corte | Idade (dentro do Foque do corte) | Deals | Chance do modelo (v2) | Ganhos em 90 dias (observado) |
| :--- | :--- | ---: | ---: | ---: |
| 30/06/2017 | 0 a 30 dias | 692 | 49,3% | 51,2% |
| 30/06/2017 | 31 a 60 dias | 454 | 48,6% | 44,5% |
| 30/06/2017 | 61 dias ou mais | 137 | 42,3% | 27,7% |
| 31/07/2017 | 0 a 30 dias | 720 | 46,8% | 24,3% |
| 31/07/2017 | 31 a 60 dias | 522 | 46,8% | 53,8% |
| 31/07/2017 | 61 dias ou mais | 606 | 45,5% | 41,6% |
| 31/08/2017 | 0 a 30 dias | 662 | 43,4% | 29,2% |
| 31/08/2017 | 31 a 60 dias | 587 | 43,4% | 21,3% |
| 31/08/2017 | 61 dias ou mais | 582 | 41,1% | 40,4% |
| 30/09/2017 | 0 a 30 dias | 679 | 50,1% | 48,0% |
| 30/09/2017 | 31 a 60 dias | 545 | 45,9% | 33,8% |
| 30/09/2017 | 61 dias ou mais | 402 | 36,6% | 6,7% |

Foque de hoje (60 deals) por idade: 0 a 30 dias: 18, 31 a 60 dias: 39, 61 dias ou mais: 3.

## Sensibilidades

**Primeira foto de treino em 28/02/2017**

| Corte | Fim do Foque (foto de 28/02) | Fim do Foque (principal) | Linhas de treino | AUC | Ganhos no top 20% | Receita no top 20% | Receita vs. principal |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 30/06/2017 | 79 | 79 | 1.330 | 0,66 | 25,7% | 61,0% | 0,0 pp |
| 31/07/2017 | 109 | 109 | 1.618 | 0,63 | 24,8% | 57,4% | 0,0 pp |
| 31/08/2017 | 135 | 133 | 2.720 | 0,63 | 25,6% | 59,0% | -1,0 pp |
| 30/09/2017 | 75 | 75 | 3.016 | 0,72 | 32,8% | 71,7% | 0,0 pp |

Com a primeira foto em 28/02/2017 o critério passaria; receita média do score v2: 62,3%.

**Pseudo-contagem do ajuste único na curva v2**

| Corte | Fim do Foque (com pseudo-contagem) | Fim do Foque (principal) | Chance aos 730 dias (com pseudo-contagem) | Chance aos 730 dias (principal) | AUC (com pseudo-contagem) | AUC (principal) | Receita no top 20% (com pseudo-contagem) | Receita vs. principal |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 30/06/2017 | 730 | 79 | 26,9% | 0,0% | 0,54 | 0,66 | 60,6% | -0,4 pp |
| 31/07/2017 | 730 | 109 | 26,2% | 0,0% | 0,55 | 0,63 | 57,0% | -0,4 pp |
| 31/08/2017 | 142 | 133 | 21,3% | 0,0% | 0,55 | 0,63 | 59,6% | -0,3 pp |
| 30/09/2017 | 77 | 75 | 13,1% | 0,0% | 0,59 | 0,72 | 70,1% | -1,7 pp |

Com 20 deals de pseudo-contagem por faixa o critério passaria; receita média do score v2: 61,8%.

**Só deals resolvidos (fechados até 31/12/2017)**

| Corte | Abertos no corte | Resolvidos até 31/12 | Ainda abertos em 31/12 | Desses, com idade em 31/12 dentro do maior ciclo ganho até o corte | Receita no top 20%: score v2 / valor / recência / aleatório | AUC: score v2 / valor / recência |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| 30/06/2017 | 1.686 | 970 | 716 | 0 | 49,1% / 49,9% / 17,7% / 19,9% | 0,49 / 0,49 / 0,50 |
| 31/07/2017 | 2.257 | 1.139 | 1.118 | 0 | 48,4% / 48,8% / 19,9% / 19,9% | 0,51 / 0,51 / 0,53 |
| 31/08/2017 | 2.265 | 893 | 1.372 | 81 | 48,9% / 49,1% / 17,0% / 19,9% | 0,50 / 0,50 / 0,44 |
| 30/09/2017 | 2.409 | 935 | 1.474 | 183 | 49,2% / 48,2% / 19,4% / 19,8% | 0,48 / 0,48 / 0,50 |

## Auditoria

**Modelo ajustado com o futuro (VAZADO; nunca é resultado)**

| Corte | Rótulo | Fim do Foque do modelo vazado | AUC vazado | Receita vazada | AUC honesto | Receita honesta | Receita: vazado menos honesto |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| 30/06/2017 | VAZADO | 61 | 0,67 | 62,0% | 0,66 | 61,0% | +1,0 pp |
| 31/07/2017 | VAZADO | 107 | 0,63 | 58,1% | 0,63 | 57,4% | +0,6 pp |
| 31/08/2017 | VAZADO | 123 | 0,64 | 60,3% | 0,63 | 59,9% | +0,4 pp |
| 30/09/2017 | VAZADO | 61 | 0,73 | 79,0% | 0,72 | 71,7% | +7,2 pp |

**`has_account` sozinho (proibido como variável)**

| Corte | Com conta | Sem conta | AUC de `has_account` sozinho | Ganhos depois (com conta) | Ganhos depois (sem conta) | Ganhos entre os sem conta |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| 30/06/2017 | 1.202 | 484 | 0,72 | 50,7% | 0,0% | 0 |
| 31/07/2017 | 1.497 | 760 | 0,75 | 49,6% | 0,0% | 0 |
| 31/08/2017 | 1.331 | 934 | 0,79 | 47,9% | 0,0% | 0 |
| 30/09/2017 | 1.401 | 1.008 | 0,77 | 39,9% | 0,0% | 0 |

## Atributos

Δ log-loss negativo é melhora (log-loss de 90 dias, contra a curva só de idade no mesmo subconjunto). Teste feito sobre a curva v1 (joelho fixo), antes da correção.

| Atributo | Subconjunto | Níveis | Δ log-loss 30/06/2017 | Δ log-loss 31/07/2017 | Δ log-loss 31/08/2017 | Δ log-loss 30/09/2017 | Melhora em todos? |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| produto | todos os deals | 7 | 0,0060 | 0,0017 | -0,0003 | 0,0007 | não |
| região | todos os deals | 3 | -0,0158 | 0,0321 | 0,0596 | 0,0645 | não |
| setor | só deals com conta | 10 | 0,0061 | 0,0039 | 0,0029 | 0,0028 | não |
| porte | só deals com conta | 3 | -0,0007 | -0,0004 | -0,0001 | 0,0004 | não |

| Atributo | Subconjunto | Níveis | Δ receita top 20% 30/06/2017 | Δ receita top 20% 31/07/2017 | Δ receita top 20% 31/08/2017 | Δ receita top 20% 30/09/2017 | Não piora em nenhum? | Entra? |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| produto | todos os deals | 7 | -0,5 pp | +0,2 pp | -0,3 pp | -0,1 pp | não | não |
| região | todos os deals | 3 | +2,5 pp | -4,7 pp | -4,2 pp | -6,1 pp | não | não |
| setor | só deals com conta | 10 | -0,8 pp | -0,8 pp | +0,2 pp | -0,3 pp | não | não |
| porte | só deals com conta | 3 | +1,3 pp | +0,8 pp | +0,0 pp | -0,1 pp | não | não |

Diagnóstico, que não decide: o mesmo Δ log-loss medido dentro da amostra de treino.

| Atributo | Subconjunto | Δ log-loss no treino 30/06/2017 | Δ log-loss no treino 31/07/2017 | Δ log-loss no treino 31/08/2017 | Δ log-loss no treino 30/09/2017 |
| :--- | :--- | ---: | ---: | ---: | ---: |
| produto | todos os deals | -0,0057 | -0,0030 | -0,0006 | -0,0004 |
| região | todos os deals | -0,0191 | -0,0237 | -0,0305 | -0,0288 |
| setor | só deals com conta | -0,0048 | -0,0038 | -0,0030 | -0,0018 |
| porte | só deals com conta | -0,0003 | -0,0002 | -0,0004 | -0,0005 |

## Modelos por corte (v2)

| Modelo ajustado até | Mês do trimestre | Chance de deal novo | Fim do Foque (dias) | Fim do Reative (dias) | O Limpe começa por | Fotos | Linhas de treino | Taxa base de treino |
| :--- | ---: | ---: | ---: | ---: | :--- | ---: | ---: | ---: |
| 30/06/2017 | 3 | 49,3% | 79 | 95 | chance abaixo de 2% | 1 | 1.330 | 45,8% |
| 31/07/2017 | 1 | 46,8% | 109 | 125 | chance abaixo de 2% | 1 | 1.618 | 44,4% |
| 31/08/2017 | 2 | 43,4% | 133 | 138 | maior ciclo já ganho | 1 | 1.535 | 40,1% |
| 30/09/2017 | 3 | 50,2% | 75 | 95 | chance abaixo de 2% | 2 | 3.016 | 40,0% |
| 31/12/2017 (hoje) | 3 | 49,5% | 61 | 95 | chance abaixo de 2% | 3 | 5.425 | 32,2% |

Fim do Foque = última idade em que a chance ainda é pelo menos 50% da de um deal novo. Fim do Reative = o que chegar primeiro: chance abaixo de 2% ou idade acima do maior ciclo já ganho até a data do modelo (138, 138, 138, 138 dias nos quatro cortes e 138 hoje). Casos em que a fase do trimestre não tinha foto elegível e o ajuste usou todas as fotos: 0.

## Curva por idade (v2)

| Modelo ajustado até | 0 dias | 15 dias | 30 dias | 45 dias | 60 dias | 75 dias | 90 dias | 105 dias | 120 dias | 150 dias |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 30/06/2017 | 49,3% | 49,3% | 48,9% | 48,5% | 48,5% | 33,1% | 8,8% | 0,0% | 0,0% | 0,0% |
| 31/07/2017 | 46,8% | 46,8% | 46,8% | 46,8% | 46,8% | 46,8% | 46,8% | 32,2% | 8,8% | 0,0% |
| 31/08/2017 | 43,4% | 43,4% | 43,4% | 43,4% | 43,4% | 43,4% | 43,4% | 39,3% | 35,1% | 1,3% |
| 30/09/2017 | 50,2% | 50,2% | 49,6% | 46,5% | 41,3% | 26,0% | 6,6% | 0,0% | 0,0% | 0,0% |
| 31/12/2017 (hoje) | 49,5% | 49,5% | 49,0% | 42,3% | 27,0% | 15,5% | 6,6% | 0,0% | 0,0% | 0,0% |

## Modelos por corte (v1)

| Modelo ajustado até | Joelho (dias) | Chance de deal novo | Inclinação por 30 dias | Meia-vida depois do joelho (dias) | Limite de Limpe (dias) | Fotos | Linhas de treino | Taxa base de treino |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 30/06/2017 | 70 | 49,0% | -4,71 | 6,9 | 138 | 1 | 1.330 | 45,8% |
| 31/07/2017 | 100 | 46,9% | -5,60 | 5,7 | 138 | 2 | 2.948 | 45,0% |
| 31/08/2017 | 95 | 46,0% | -1,72 | 18,3 | 138 | 3 | 4.483 | 43,3% |
| 30/09/2017 | 90 | 45,6% | -1,96 | 16,0 | 138 | 4 | 6.169 | 41,2% |
| 31/12/2017 (hoje) | 95 | 39,9% | -2,59 | 11,3 | 138 | 7 | 13.100 | 33,2% |

## Hoje

| Lista | Regra | Deals | Valor de tabela | Valor esperado |
| :--- | :--- | ---: | ---: | ---: |
| Foque | idade até 61 dias | 60 | US$ 123.253 | US$ 47.500 |
| Reative | 62 a 95 dias | 66 | US$ 177.537 | US$ 17.818 |
| Limpe | mais de 95 dias | 1.463 | US$ 3.591.439 | US$ 99 |
| Qualifique | Prospecting (sem data) | 500 | US$ 1.073.986 | — |

| Limpe de hoje | Deals | Valor de tabela |
| :--- | ---: | ---: |
| Acima do maior ciclo já ganho (138 dias) | 1.291 | US$ 3.198.664 |
| Só pela chance (idade até o maior ciclo, chance abaixo do mínimo) | 172 | US$ 392.775 |

| Lista | Faixas fixas do briefing (90 e 138 dias) | Limiares aprendidos pela curva v2 |
| :--- | ---: | ---: |
| Foque | 110 | 60 |
| Reative | 188 | 66 |
| Limpe | 1.291 | 1.463 |

## Hoje: antes e depois da correção

| Lista | Regra v1 | Deals (v1) | Valor de tabela (v1) | Regra v2 | Deals (v2) | Valor de tabela (v2) |
| :--- | :--- | ---: | ---: | :--- | ---: | ---: |
| Foque | idade até 95 dias | 126 | US$ 300.790 | idade até 61 dias | 60 | US$ 123.253 |
| Reative | 96 a 138 dias | 172 | US$ 392.775 | 62 a 95 dias | 66 | US$ 177.537 |
| Limpe | mais de 138 dias | 1.291 | US$ 3.198.664 | mais de 95 dias | 1.463 | US$ 3.591.439 |
| Qualifique | Prospecting (sem data) | 500 | US$ 1.073.986 | Prospecting (sem data) | 500 | US$ 1.073.986 |
