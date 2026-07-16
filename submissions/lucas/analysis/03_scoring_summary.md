# Fase 3 — Motor de scoring (logica + validacao)

## Metodologia
- **Win rate global** (base do shrinkage): 63.2% (n=6711)
- **Shrinkage**: `shrunk = (n*raw + k*global) / (n+k)`, k=30. Segmentos com n<30 regridem fortemente a media global; em n=30 o peso e 50/50.
- **P(fechar)** = win rate do PRODUTO (shrunk) + efeito aditivo do SETOR (shrunk - global, em pp), só quando o deal tem `account`; depois multiplicado pelo fator HEURISTICO de `deal_stage`. Resultado limitado a [1%, 99%].
- **deal_stage NAO tem win rate empirico** — cada opportunity_id so registra o estagio final, sem historico de transicao, entao nao da pra medir 'taxa de fechamento condicional ao estagio' nos dados. O multiplicador e uma HEURISTICA explicita: {'Prospecting': 0.85, 'Engaging': 1.15} (Engaging > Prospecting).
- **Valor potencial** de deal aberto = `products.sales_price` do produto — `close_value` so existe apos o fechamento, entao nao pode ser usado como input do scoring de um deal aberto.
- **EV = P(fechar) x valor potencial**.
- **Esfriando** = dias desde `engage_date` > p75 do `days_to_close` dos deals **WON do mesmo produto**. Deals `Prospecting` nunca recebem a flag (nao tem `engage_date`).

## Tabela de referencia — win rate por PRODUTO (empirico, com shrinkage)
| Produto | n | raw | shrunk | shrunk < raw? (regrediu p/ media) |
|---|---|---|---|---|
| GTK 500 | 25 | 60.0% | 61.7% | sim |
| GTX Plus Pro | 745 | 64.3% | 64.3% | nao |
| GTX Plus Basic | 1051 | 62.1% | 62.2% | nao |
| MG Advanced | 1084 | 60.3% | 60.4% | nao |
| GTX Pro | 1147 | 63.6% | 63.5% | nao |
| MG Special | 1223 | 64.8% | 64.8% | nao |
| GTX Basic | 1436 | 63.7% | 63.7% | nao |

## Tabela de referencia — win rate por SETOR da conta (empirico, com shrinkage)
| Setor | n | raw | shrunk | efeito vs. global (pp) |
|---|---|---|---|---|
| employment | 286 | 62.6% | 62.6% | -0.5 |
| services | 352 | 63.4% | 63.3% | +0.2 |
| entertainment | 402 | 64.7% | 64.6% | +1.4 |
| telecommunications | 456 | 62.5% | 62.5% | -0.6 |
| finance | 613 | 61.2% | 61.3% | -1.9 |
| marketing | 623 | 64.8% | 64.8% | +1.6 |
| software | 704 | 63.9% | 63.9% | +0.7 |
| medical | 950 | 62.3% | 62.3% | -0.8 |
| technolgy | 1058 | 63.4% | 63.4% | +0.3 |
| retail | 1267 | 63.1% | 63.1% | -0.1 |

## Multiplicador de estagio (HEURISTICO — nao derivado do historico)
| Estagio | Multiplicador |
|---|---|
| Prospecting | x0.85 |
| Engaging | x1.15 |

## Limiar de 'esfriando' por produto (p75 do ciclo dos deals WON)
| Produto | n_won | p75 dias |
|---|---|---|
| GTK 500 | 15 | 100 |
| GTX Plus Pro | 479 | 85 |
| GTX Plus Basic | 653 | 90 |
| MG Advanced | 654 | 87 |
| GTX Pro | 729 | 84 |
| MG Special | 793 | 88 |
| GTX Basic | 915 | 91 |

## Valor potencial por produto (products.sales_price)
| Produto | sales_price |
|---|---|
| GTX Basic | 550 |
| GTX Pro | 4821 |
| MG Special | 55 |
| MG Advanced | 3393 |
| GTX Plus Pro | 5482 |
| GTX Plus Basic | 1096 |
| GTK 500 | 26768 |

## Validacao agregada — deals abertos scorados (Prospecting + Engaging)
- Total scorado: 2089
- P(fechar): media=68.1%, mediana=72.4%, min=49.8%, max=76.4%
- EV: media=1619, mediana=783, min=29, max=19436
- Flag 'esfriando': 1481 deals (93.2% dos Engaging — Prospecting nunca flegado)

### Limitacao conhecida da flag 'esfriando'
- 93.2% dos deals Engaging estao flegados como esfriando — proporcao alta demais pra discriminar prioridade de verdade. Motivo provavel: o dataset e uma FOTO estatica (nao um CRM ao vivo). A data de referencia usada e a data mais recente encontrada no proprio dataset (2017-12-31), entao TODO deal que segue aberto ali e, por construcao, um deal que nao fechou rapido — os que fechariam rapido ja teriam saido do balde 'aberto' antes dessa data. Isso enviesa a amostra de deals abertos para os mais antigos (nao e erro de calculo, e vies de amostragem por corte no tempo). Num CRM ao vivo, com deals novos entrando toda semana, a proporcao tende a ser bem menor. Vale reconsiderar o percentil (ex.: p90 em vez de p75) ou comunicar esse caveat explicitamente no app.

## Amostra para inspecao manual (drivers completos)
### Engaging, com conta, esfriando
- **01XZ9CRY** (GTX Plus Pro, Engaging) — P(fechar)=73%, valor_potencial=5482, EV=4012, esfriando=True
  - Drivers: Produto 'GTX Plus Pro' fecha historicamente 64% (n=745) | Setor 'telecommunications' -0.6pp vs. media global (n=456) | Estagio 'Engaging': multiplicador heuristico x1.15 (nao empirico) | 104 dias aberto — acima do típico de vitória do produto (85 dias, p75)
- **021Z2J9L** (GTK 500, Engaging) — P(fechar)=71%, valor_potencial=26768, EV=19079, esfriando=True
  - Drivers: Produto 'GTK 500' fecha historicamente 62% (n=25) | Setor 'technolgy' +0.3pp vs. media global (n=1058) | Estagio 'Engaging': multiplicador heuristico x1.15 (nao empirico) | 161 dias aberto — acima do típico de vitória do produto (100 dias, p75)
- **041Q1IZL** (GTX Pro, Engaging) — P(fechar)=73%, valor_potencial=4821, EV=3534, esfriando=True
  - Drivers: Produto 'GTX Pro' fecha historicamente 64% (n=1147) | Setor 'services' +0.2pp vs. media global (n=352) | Estagio 'Engaging': multiplicador heuristico x1.15 (nao empirico) | 138 dias aberto — acima do típico de vitória do produto (84 dias, p75)

### Engaging, com conta, nao esfriando
- **0N11U6L3** (GTX Plus Basic, Engaging) — P(fechar)=72%, valor_potencial=1096, EV=787, esfriando=False
  - Drivers: Produto 'GTX Plus Basic' fecha historicamente 62% (n=1051) | Setor 'technolgy' +0.3pp vs. media global (n=1058) | Estagio 'Engaging': multiplicador heuristico x1.15 (nao empirico)
- **1LY8CAXD** (GTK 500, Engaging) — P(fechar)=70%, valor_potencial=26768, EV=18750, esfriando=False
  - Drivers: Produto 'GTK 500' fecha historicamente 62% (n=25) | Setor 'medical' -0.8pp vs. media global (n=950) | Estagio 'Engaging': multiplicador heuristico x1.15 (nao empirico)
- **2DY9U1V7** (GTX Pro, Engaging) — P(fechar)=73%, valor_potencial=4821, EV=3538, esfriando=False
  - Drivers: Produto 'GTX Pro' fecha historicamente 64% (n=1147) | Setor 'technolgy' +0.3pp vs. media global (n=1058) | Estagio 'Engaging': multiplicador heuristico x1.15 (nao empirico)

### Engaging, sem conta
- **01EH41WA** (GTX Pro, Engaging) — P(fechar)=73%, valor_potencial=4821, EV=3523, esfriando=True
  - Drivers: Produto 'GTX Pro' fecha historicamente 64% (n=1147) | Conta nao identificada no CRM — sem ajuste de setor | Estagio 'Engaging': multiplicador heuristico x1.15 (nao empirico) | 302 dias aberto — acima do típico de vitória do produto (84 dias, p75)
- **02K37JAK** (GTX Plus Basic, Engaging) — P(fechar)=71%, valor_potencial=1096, EV=783, esfriando=True
  - Drivers: Produto 'GTX Plus Basic' fecha historicamente 62% (n=1051) | Conta nao identificada no CRM — sem ajuste de setor | Estagio 'Engaging': multiplicador heuristico x1.15 (nao empirico) | 163 dias aberto — acima do típico de vitória do produto (90 dias, p75)
- **03VCDZEE** (GTX Pro, Engaging) — P(fechar)=73%, valor_potencial=4821, EV=3523, esfriando=True
  - Drivers: Produto 'GTX Pro' fecha historicamente 64% (n=1147) | Conta nao identificada no CRM — sem ajuste de setor | Estagio 'Engaging': multiplicador heuristico x1.15 (nao empirico) | 311 dias aberto — acima do típico de vitória do produto (84 dias, p75)

### Prospecting, com conta
- **0BQTT5UF** (GTX Pro, Prospecting) — P(fechar)=55%, valor_potencial=4821, EV=2671, esfriando=False
  - Drivers: Produto 'GTX Pro' fecha historicamente 64% (n=1147) | Setor 'marketing' +1.6pp vs. media global (n=623) | Estagio 'Prospecting': multiplicador heuristico x0.85 (nao empirico)
- **0HR4TEU4** (GTX Plus Basic, Prospecting) — P(fechar)=53%, valor_potencial=1096, EV=578, esfriando=False
  - Drivers: Produto 'GTX Plus Basic' fecha historicamente 62% (n=1051) | Setor 'retail' -0.1pp vs. media global (n=1267) | Estagio 'Prospecting': multiplicador heuristico x0.85 (nao empirico)
- **0KSK9O00** (GTX Basic, Prospecting) — P(fechar)=54%, valor_potencial=550, EV=299, esfriando=False
  - Drivers: Produto 'GTX Basic' fecha historicamente 64% (n=1436) | Setor 'technolgy' +0.3pp vs. media global (n=1058) | Estagio 'Prospecting': multiplicador heuristico x0.85 (nao empirico)

### Prospecting, sem conta
- **00400B1S** (GTX Basic, Prospecting) — P(fechar)=54%, valor_potencial=550, EV=298, esfriando=False
  - Drivers: Produto 'GTX Basic' fecha historicamente 64% (n=1436) | Conta nao identificada no CRM — sem ajuste de setor | Estagio 'Prospecting': multiplicador heuristico x0.85 (nao empirico)
- **03P9VXWG** (GTX Basic, Prospecting) — P(fechar)=54%, valor_potencial=550, EV=298, esfriando=False
  - Drivers: Produto 'GTX Basic' fecha historicamente 64% (n=1436) | Conta nao identificada no CRM — sem ajuste de setor | Estagio 'Prospecting': multiplicador heuristico x0.85 (nao empirico)
- **0C34Z5UZ** (GTX Pro, Prospecting) — P(fechar)=54%, valor_potencial=4821, EV=2604, esfriando=False
  - Drivers: Produto 'GTX Pro' fecha historicamente 64% (n=1147) | Conta nao identificada no CRM — sem ajuste de setor | Estagio 'Prospecting': multiplicador heuristico x0.85 (nao empirico)

## Sanity check — top 5 e bottom 5 por EV
Top 5:
- DJMPI9TO (GTK 500, Engaging): EV=19436 — Produto 'GTK 500' fecha historicamente 62% (n=25) | Setor 'entertainment' +1.4pp vs. media global (n=402) | Estagio 'Engaging': multiplicador heuristico x1.15 (nao empirico) | 257 dias aberto — acima do típico de vitória do produto (100 dias, p75)
- 021Z2J9L (GTK 500, Engaging): EV=19079 — Produto 'GTK 500' fecha historicamente 62% (n=25) | Setor 'technolgy' +0.3pp vs. media global (n=1058) | Estagio 'Engaging': multiplicador heuristico x1.15 (nao empirico) | 161 dias aberto — acima do típico de vitória do produto (100 dias, p75)
- 125VIRMX (GTK 500, Engaging): EV=19058 — Produto 'GTK 500' fecha historicamente 62% (n=25) | Setor 'services' +0.2pp vs. media global (n=352) | Estagio 'Engaging': multiplicador heuristico x1.15 (nao empirico) | 377 dias aberto — acima do típico de vitória do produto (100 dias, p75)
- GL1YE4PQ (GTK 500, Engaging): EV=18999 — Produto 'GTK 500' fecha historicamente 62% (n=25) | Conta nao identificada no CRM — sem ajuste de setor | Estagio 'Engaging': multiplicador heuristico x1.15 (nao empirico) | 236 dias aberto — acima do típico de vitória do produto (100 dias, p75)
- AKMV6WN5 (GTK 500, Engaging): EV=18999 — Produto 'GTK 500' fecha historicamente 62% (n=25) | Conta nao identificada no CRM — sem ajuste de setor | Estagio 'Engaging': multiplicador heuristico x1.15 (nao empirico) | 269 dias aberto — acima do típico de vitória do produto (100 dias, p75)
Bottom 5:
- W2149WNZ (MG Special, Prospecting): EV=29 — Produto 'MG Special' fecha historicamente 65% (n=1223) | Setor 'finance' -1.9pp vs. media global (n=613) | Estagio 'Prospecting': multiplicador heuristico x0.85 (nao empirico)
- KLUS7RVS (MG Special, Prospecting): EV=29 — Produto 'MG Special' fecha historicamente 65% (n=1223) | Setor 'finance' -1.9pp vs. media global (n=613) | Estagio 'Prospecting': multiplicador heuristico x0.85 (nao empirico)
- F4W7Z1UU (MG Special, Prospecting): EV=29 — Produto 'MG Special' fecha historicamente 65% (n=1223) | Setor 'finance' -1.9pp vs. media global (n=613) | Estagio 'Prospecting': multiplicador heuristico x0.85 (nao empirico)
- I93XL6Q9 (MG Special, Prospecting): EV=29 — Produto 'MG Special' fecha historicamente 65% (n=1223) | Setor 'finance' -1.9pp vs. media global (n=613) | Estagio 'Prospecting': multiplicador heuristico x0.85 (nao empirico)
- F22C6LKO (MG Special, Prospecting): EV=30 — Produto 'MG Special' fecha historicamente 65% (n=1223) | Setor 'medical' -0.8pp vs. media global (n=950) | Estagio 'Prospecting': multiplicador heuristico x0.85 (nao empirico)
