# Validação do modelo

> Gerado por `solution/scorer.py`. Não editar à mão.

## 1. Backtest por snapshot: alguém consegue ordenar quem vai ganhar?

Simula o uso real. Em cada data de corte, o modelo vê só o passado e ordena os deals que estavam em Engaging naquele dia, com a idade que tinham. Depois compara com o resultado real.

AUC 0,50 = cara ou coroa. Gate para um atributo entrar no score: AUC >= 0.55 em todos os cortes.

| Fator | 2017-05-01 | 2017-07-01 | 2017-09-01 |
|---|---|---|---|
| idade do deal (curva de sobrevivência) | 0.512 [0.48-0.55] | 0.517 [0.48-0.55] | 0.553 [0.51-0.59] |
| vendedor x produto | 0.460 [0.43-0.49] | 0.492 [0.46-0.52] | 0.552 [0.52-0.60] |
| conta | 0.486 [0.46-0.52] | 0.475 [0.44-0.51] | 0.460 [0.42-0.50] |
| vendedor | 0.458 [0.43-0.49] | 0.507 [0.47-0.54] | 0.530 [0.49-0.57] |
| produto | 0.481 [0.45-0.51] | 0.533 [0.50-0.57] | 0.500 [0.46-0.54] |
| deals no teste (taxa de ganho) | 1147 (66%) | 970 (63%) | 893 (71%) |

Atributos aprovados no gate: nenhum.

**Leitura honesta:** nenhum componente ordena ganhos de forma confiável. A idade fica entre 0,51 e 0,55 conforme o corte, e em dois dos três cortes o intervalo de 95% inclui 0,50. Por isso o score NÃO usa probabilidade: é uma política explícita de valor x momento (docs/logica.md). Setor, região, porte, preço, carga do vendedor e 'conta já comprou' também foram testados (`process-log/eda3_sinais.py`): AUC entre 0,49 e 0,51.

## 2. Onde as perdas acontecem (corte 2017-07-01)

P(ganho | deal ainda aberto após t dias). Treino e teste mostram o mesmo formato.

| t (dias) | Treino | Teste |
|---|---|---|
| 0 | 66.6% (n=2679) | 60.8% (n=4032) |
| 7 | 68.8% (n=2274) | 62.7% (n=3325) |
| 14 | 71.8% (n=1703) | 66.3% (n=2293) |
| 30 | 71.7% (n=1512) | 65.7% (n=2044) |
| 60 | 72.2% (n=1288) | 66.1% (n=1728) |
| 90 | 73.8% (n=646) | 69.1% (n=770) |
| 120 | 79.5% (n=117) | 70.0% (n=100) |

51% das perdas acontecem até o dia 14. Maior ciclo já observado: 138 dias (era o mesmo no corte de maio/2017).

## 3. Pipeline aberto na data de referência

Valores em reais pela PTAX de venda de 2026-11-05: US$ 1 = R$ 5,4621.

- Deals abertos: 2089 (1589 Engaging, 500 Prospecting)
- Engaging além de 138 dias ('zumbis', verificar no CRM): 1291 = 81% do Engaging, R$ 17.471.423 em tabela
- Engaging dentro do ciclo: 298 deals, valor esperado R$ 2.655.833
- Prospecting: 500 deals, R$ 5.866.219 em tabela, chance desconhecida (o histórico nunca registra Prospecting -> Won)
- Valor de tabela nominal de tudo: R$ 27.125.963
- Deals sem conta preenchida: 1425
