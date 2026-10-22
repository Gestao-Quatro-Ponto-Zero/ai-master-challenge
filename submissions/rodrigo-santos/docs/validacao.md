# Validação da pontuação (backtest)

Gerado por `python -m app.servicos.validacao`. Em cada data de corte, as estatísticas usam só
negócios fechados antes do corte; os negócios em andamento naquele dia são pontuados com a mesma
função da tela e comparados com o que aconteceu depois.

## Negócios parados

Somando os cortes, **1246 negócios** já estavam abertos há mais tempo que qualquer negócio
do histórico. Desses, **0 foram fechados depois** (ganhos ou perdidos).

| Corte | Fechados antes (treino) | Limite (dias) | Em andamento | Resolvidos depois | Parados | Parados que fecharam |
|---|---|---|---|---|---|---|
| 2017-05-01 | 1233 | 138 | 1618 | 1147 | 25 | 0 |
| 2017-07-01 | 2679 | 138 | 1686 | 970 | 153 | 0 |
| 2017-09-01 | 4091 | 138 | 2265 | 893 | 411 | 0 |
| 2017-11-01 | 5292 | 138 | 2604 | 1072 | 657 | 0 |

## Resultado por prioridade (negócios resolvidos depois do corte)

| Prioridade | Negócios | Taxa de vitória | Receita média por negócio |
|---|---|---|---|
| Alta | 2956 | 65.3% | US$ 2.068 |
| Média | 1126 | 67.0% | US$ 159 |
| Baixa | 0 | 0.0% | US$ 0 |

A taxa de vitória é parecida entre as faixas (nenhum atributo prevê vitória, ver abaixo); a diferença
está na receita por negócio trabalhado. A faixa Baixa fica vazia porque, no dia do corte, todo negócio
que depois foi fechado ainda estava ativo: os de prioridade baixa são os parados (que nunca fecharam)
e a prospecção de baixo valor (sem data de início, fora do backtest).

## Algum atributo prevê quem ganha?

AUC fora da amostra (0,5 = sorteio; 1,0 = acerta sempre), média dos cortes:

| Atributo | AUC médio | 2017-05-01 | 2017-07-01 | 2017-09-01 | 2017-11-01 |
|---|---|---|---|---|---|
| Vendedor × produto | 0.506 | 0.479 | 0.483 | 0.551 | 0.513 |
| Nº de funcionários da conta | 0.503 | 0.491 | 0.508 | 0.489 | 0.524 |
| Produto | 0.502 | 0.481 | 0.533 | 0.500 | 0.496 |
| Série do produto | 0.502 | 0.497 | 0.495 | 0.510 | 0.506 |
| País da conta | 0.502 | 0.509 | 0.486 | 0.510 | 0.504 |
| Porte da conta (receita) | 0.500 | 0.509 | 0.485 | 0.504 | 0.503 |
| Vendedor | 0.495 | 0.456 | 0.507 | 0.529 | 0.490 |
| Escritório regional | 0.493 | 0.480 | 0.502 | 0.499 | 0.492 |
| Gerente | 0.488 | 0.461 | 0.515 | 0.499 | 0.477 |
| Setor da conta | 0.486 | 0.477 | 0.504 | 0.516 | 0.446 |
| Conta | 0.473 | 0.486 | 0.475 | 0.462 | 0.471 |

