# Fase 4 — Backtest do motor de P(fechar) (deals fechados, Won+Lost)

## Metodologia (anti-vazamento)
- Universo: 6711 deals fechados (Won+Lost) de `pipeline_clean.csv`.
- K-fold=5, estratificado por outcome (Won/Lost), seed=42 (reprodutivel).
- Em cada fold, win rate de PRODUTO e de SETOR (com shrinkage, k=30) sao recalculados usando SOMENTE os outros 4 folds (treino). O fold de teste nunca contribui para a taxa usada em si mesmo.
- `deal_stage` NAO entra no score aqui — deal fechado nao tem estagio aberto, e o multiplicador e heuristico (nao testavel contra outcome real).
- Valor potencial = `products.sales_price` (mesma escolha da Fase 3), nao `close_value` — closed_value so e conhecido apos o fechamento e nao pode ser usado como input do score.
- **Limitacao importante**: no universo fechado, 6711/6711 deals tem `account`/`sector` conhecido (0 sem sector). Ou seja, este backtest valida quase exclusivamente o ramo 'com conta' da logica — o ramo 'sem conta, so produto' (que cobre ~68% dos deals ABERTOS, ver Fase 2) tem pouquissimo ou nenhum dado fechado equivalente para validar. A qualidade de P(fechar) para deals sem conta permanece uma suposicao nao testada por este backtest.
- Taxa global por fold (treino): ['63.2%', '63.2%', '63.2%', '63.1%', '63.1%'] — estavel entre folds.

## 1. Discriminacao (AUC)
- **AUC (produto + setor)**: 0.485
- **AUC (so produto, diagnostico)**: 0.493
- Referencia: 0.5 = sem poder discriminativo (equivalente a chute aleatorio); 1.0 = separacao perfeita.
- **Achado esperado, nao e bug**: AUC de 0.485 indica discriminacao BAIXA. Win rate por produto/setor varia pouco (55%-65%) — quase todo deal historico tem probabilidade parecida de fechar, entao o modelo separa mal quem vai Won de quem vai Lost usando so essas features. Isso bate com o que a Fase 3 ja mostrava: o efeito de setor e minusculo (<2pp) e o de produto e modesto.

## 2. Calibracao (decis de P previsto vs win rate real)
| Decil (p_pred) | n | p previsto (media) | win rate real |
|---|---|---|---|
| (0.553, 0.602] | 693 | 59.4% | 63.6% |
| (0.602, 0.612] | 661 | 60.8% | 65.1% |
| (0.612, 0.621] | 679 | 61.7% | 62.2% |
| (0.621, 0.628] | 663 | 62.5% | 62.6% |
| (0.628, 0.633] | 660 | 63.1% | 65.0% |
| (0.633, 0.637] | 682 | 63.5% | 65.7% |
| (0.637, 0.643] | 684 | 64.0% | 64.9% |
| (0.643, 0.648] | 650 | 64.5% | 63.1% |
| (0.648, 0.66] | 671 | 65.4% | 62.3% |
| (0.66, 0.677] | 668 | 66.8% | 57.0% |

- Gap medio absoluto entre previsto e real por decil: 2.8%.
- **Razoavelmente calibrado NA MEDIA**: a probabilidade prevista fica perto da taxa real observada na maioria das faixas — o modelo nao discrimina bem QUAL deal individual vai fechar, mas as MEDIAS por segmento sao uteis o suficiente pra EV agregado fazer sentido.
- **Mas ha um furo na ponta**: o decil de MAIOR P previsto (66.8%) tem a MENOR win rate real observada (57.0%) — o oposto do esperado. Isso e consistente com o AUC ficar levemente abaixo de 0.5: nao ha garantia de que 'score mais alto' realmente signifique 'mais chance de fechar' nos extremos. Nao suavizo isso so porque a media geral fecha bem — a calibracao e boa NO AGREGADO, nao necessariamente na cauda.

## 3. Captura de valor no top-20% (o que a ferramenta REALMENTE promete)
- Top 20% = 1342 de 6711 deals fechados.
- Valor Won total no universo: 10,005,534

| Metodo de ranking | % do valor Won capturado no top-20% |
|---|---|
| **EV previsto (produto+setor, sem estagio)** | 46.8% |
| (b) Ordenar por valor puro (`sales_price`) | 47.9% |
| (a) Ordem aleatoria (media de 500 simulacoes, ±1 desvio) | 20.0% ± 0.7% |

### Sobre a baseline (c) 'ordenar por estagio' — nao computada, e por que
- Neste universo de backtest, `deal_stage` so assume `Won` ou `Lost` — ou seja, **e o proprio rotulo que estamos tentando prever**. Ordenar por estagio aqui seria ordenar pela resposta certa: daria ~100% de captura trivialmente, mas isso nao mede nada sobre o valor do scoring, so mede que sabemos separar Won de Lost quando ja sabemos quem e Won. Incluir esse numero seria enganoso (um vazamento disfarcado de baseline). A comparacao contra estagio (Prospecting vs Engaging) so faz sentido no pipeline ABERTO, em producao, olhando pra frente — nao da pra backtestar com dados historicos fechados.

- **Lift vs aleatorio**: 2.35x
- **Lift vs valor puro**: 0.98x
- **Correlacao de Spearman entre ranking por EV e ranking por valor puro**: 0.985
- Correlacao muito alta: como o win rate varia pouco entre produtos, o ranking por EV e quase o mesmo que simplesmente ordenar pelos deals mais caros.
- **Honestidade sem meio-termo: o EV NAO supera a baseline 'valor puro' neste backtest** (46.8% vs 47.9%, lift=0.98x). A diferenca e pequena e pode ser so ruido (rankings 98.5% correlacionados), mas o dado bruto nao mostra ganho — mostra empate ou leve perda. Nao vou reportar isso como 'lift modesto positivo' quando o numero real e <= 1.0x.

## Conclusao honesta
- O modelo **nao discrimina bem** quem individualmente vai fechar (AUC=0.485, perto de 0.5, com inversao no decil mais alto).
- As taxas por segmento **sao razoavelmente calibradas na media agregada** — uteis pra EV agregado, nao pra apostar num deal so.
- A captura de valor no top-20% (46.8%) bate a ordem aleatoria (20.0% ± 0.7%), lift de 2.35x.
- **Mas contra a baseline 'valor puro' o EV nao ganha** (46.8% vs 47.9%, lift=0.98x) — porque o win rate quase nao varia entre segmentos neste dataset (rankings 98.5% correlacionados). Priorizar por EV aqui e, na pratica, quase o mesmo que so olhar pro tamanho do deal.
- O valor real da ferramenta, neste dataset, nao esta em 'prever quem vai fechar' com precisao — esta em dar VISIBILIDADE e EXPLICABILIDADE sobre um pipeline de 8800 linhas priorizado 'no feeling', mais o multiplicador de estagio (heuristico, nao testavel aqui) que empurra deals ja engajados pra frente. O componente empirico (produto+setor) contribui pouco alem do que o valor do deal ja diria sozinho — isso deve ser dito com todas as letras na documentacao do app, nao escondido.