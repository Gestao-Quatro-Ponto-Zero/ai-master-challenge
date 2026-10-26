# Score e validação

Data de referência ("hoje"): 31/12/2017. As tabelas entre marcadores `AUTO` são geradas por `python -m scorer.docs` a partir de `solution/data/processed/backtest_metrics.json` (que `python -m scorer.validate` calcula dos dados). Os números do texto são conferidos contra o mesmo arquivo por `tests/test_docs_numbers.py`. A seção 9 (critério pré-registrado) foi escrita às 16:28 de 25/10/2026, antes de existir o código do backtest; o relato da ordem real está em `process-log/03_bloco-3.md`. **A curva do score foi trocada depois do backtest, a pedido do Rafael: a seção 0 conta o que mudou e a seção 9 declara que é uma mudança pós-backtest.**

## 0. Correção após revisão do Rafael

O Rafael abriu a página publicada como vendedor e viu a chance de ganho constante, de 0 a 95 dias, para todo deal do Foque. Isso contradiz o que o briefing já mostrava (no corte de 30/09/2017, 50% de ganhos até 30 dias, 34% de 31 a 60, 7% de 61 a 90 e 0% acima de 90), e tinha três efeitos na tela dele: o deal do topo da Rosalina Dieter era um GTK 500 com 95 dias e score 100; dentro do Foque a ordem virou uma ordenação por preço; e a caixa "Atenção" do Foque admitia o erro em vez de corrigi-lo. A curva v1 ("platô + queda", seção 2) foi mantida só para comparação.

**Diagnóstico.** Dois motivos achatavam a curva. O primeiro é que o treino empilhava fotos de fases diferentes do trimestre, que têm padrões opostos e se cancelam:

<!-- AUTO:scoring-diagnostico -->
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
<!-- /AUTO:scoring-diagnostico -->

Nas fotos de fim de trimestre (março, junho e setembro) a taxa cai com a idade e chega a zero depois dos 90 dias; nas de meio de trimestre ela sobe até os 90 dias e só cai depois. Juntas, dão uma taxa quase plana. O segundo motivo é o desenho da v1: com `logit = b0 + b1 * max(0, idade - joelho) / 30`, a chance é constante antes do joelho por construção, mesmo que os dados peçam o contrário. A data de referência (31/12) e os cortes de 30/06 e 30/09 são fins de trimestre.

**O que mudou.** A curva v2 (seção 2) é monotonicamente não crescente desde o dia 0, por faixas de idade isotônicas, e cada corte treina só com as fotos da mesma fase do trimestre que ele. Os limites das listas saem da curva. Em números:

<!-- AUTO:scoring-correcao -->
- **Chance de hoje.** v1: 40% de 0 a 95 dias, igual para todos (o platô). v2: 50% para um deal novo e 49% com 30 dias, 27% com 60 dias, 7% com 90 dias.
- **Listas de hoje.** Foque: 126 → 60 deals. Reative: 172 → 66. Limpe: 1.291 → 1.463 (US$ 3.198.664 → US$ 3.591.439 de tabela).
- **Backtest principal (receita no top 20%, média dos cortes).** v1: 61,1%; v2: 62,5%. AUC: 0,64 → 0,66.
- **Ordem dentro do Foque (deals de até 90 dias).** Receita no top 20%: v1 49,7%, v2 52,5%, valor 49,1%; AUC: v1 0,51, v2 0,52, valor 0,50.
<!-- /AUTO:scoring-correcao -->

**O que a correção não resolveu** (os detalhes estão nas seções 6, 7 e 10): a v2 não é melhor que a v1 na receita média dos cortes de 30/06, 31/07 e 31/08 (empata ou perde por menos de um ponto percentual); a vantagem está no corte de 30/09, que é de fim de trimestre como hoje. Dentro do Foque a AUC continua perto de um sorteio. Três dos quatro cortes têm uma só foto de treino, porque agora só vale a fase do trimestre do corte.

## 1. Resumo

O score responde a uma pergunta: dos negócios abertos hoje, quais valem a próxima hora do vendedor? Para cada negócio, a ferramenta estima a chance de ele ser ganho nos próximos 90 dias olhando só para a idade dele, isto é, há quanto tempo está aberto. A estimativa vem de como negócios da mesma idade se comportaram no passado, nas fotos do mesmo ponto do trimestre (hoje é o último mês do trimestre). A chance cai com a idade desde o primeiro dia, e o limite do Foque é a idade em que ela chega à metade da de um negócio novo; o Limpe começa quando a chance fica abaixo de 2% ou o negócio passa do maior ciclo já ganho (nenhum negócio do histórico foi ganho depois de 138 dias aberto). A chance multiplicada pelo preço de tabela dá o valor esperado, e o score de 0 a 100 é esse valor numa escala que não deixa o produto mais caro engolir os demais. Para saber se funciona, voltamos no tempo quatro vezes (30/06, 31/07, 31/08 e 30/09/2017), usando em cada uma só o que o CRM sabia naquele dia, e conferimos o que aconteceu depois. Em média, os 20% de negócios no topo do score v2 concentraram 62,5% da receita que foi de fato ganha em seguida (61,1% com a curva v1), contra 48,1% se o time ordenasse só pelo preço e 29,7% se ordenasse pelos mais recentes; um sorteio daria 20,0%. O score ficou à frente dos três nos quatro cortes, pelo critério que fixamos antes de olhar o resultado, mas a curva v2 é uma mudança feita depois do backtest, a pedido do Rafael. Há quatro ressalvas. Primeira: se a pergunta for só "quem vai ganhar", e não "onde está o dinheiro", ordenar pelos mais recentes acerta mais em três dos quatro cortes. Segunda: entre os negócios que já foram encerrados (ganhos ou perdidos), o score não é melhor que ordenar pelo preço; a vantagem vem de tirar do topo os negócios parados há muito tempo. Terceira: só entre os negócios de até 90 dias (a ordem dentro do Foque) o score v2 ordena melhor que o preço apenas no corte de fim de trimestre, e a AUC fica perto de um sorteio. Quarta: três dos quatro cortes treinam com uma foto só. Os dados são sintéticos, e parte do padrão que o score usa (o teto de 138 dias e a queda no fim do trimestre) provavelmente é do gerador, não do comércio real.

## 2. Fórmula

```
chance(idade)   = taxa de ganho em 90 dias por faixa de 15 dias de idade, não crescente (PAVA),
                  interpolada linearmente entre os pontos médios das faixas
valor esperado  = chance(idade) * preço de tabela
score           = 100 * ln(1 + VE / VE_min) / ln(1 + VE_max / VE_min)      (arredondado, de 0 a 100)
VE_min / VE_max = chance de um deal novo * menor / maior preço do catálogo
```

- **Chance (curva v2).** Para cada corte T: (1) pegam-se as fotos mensais do pipeline (fim de cada mês, de 31/03/2017 até 90 dias antes de T) **que caem no mesmo mês do trimestre que T**, isto é, no mês 1 (jan, abr, jul, out), 2 (fev, mai, ago, nov) ou 3 (mar, jun, set, dez); (2) cada linha é um deal aberto na foto, com o desfecho nos 90 dias seguintes; (3) a taxa de ganho é calculada em faixas de 15 dias de idade, sem pseudo-contagem; (4) a regressão isotônica (PAVA, pesos = número de casos) funde as faixas vizinhas que subiriam, e a chance fica não crescente desde o dia 0; (5) entre os pontos médios das faixas, interpolação linear, e depois da última faixa a chance fica constante. Se a fase do corte não tivesse nenhuma foto elegível, o ajuste cairia para todas as fotos elegíveis e o caso ficaria registrado no modelo (não ocorreu em nenhum corte, nem hoje). Dentro de cada fase só entram fotos com data mais 90 dias até T, então a curva só usa dados anteriores a T.
- **Por que sem pseudo-contagem.** A suavização do ajuste único (20 deals rumo à taxa média em cada faixa) empurrava a cauda sem nenhum ganho para uma chance alta: aos 730 dias a curva dizia 26,9% no corte de 30/06 e 13,1% no de 30/09, onde nenhum deal com mais de 138 dias foi ganho. Com isso o Foque do corte de 30/06 nunca terminava. A tabela de sensibilidade da seção 7 mostra a v2 com essa suavização.
- **Valor.** O valor do deal aberto é o preço de tabela (`sales_price`); o `close_value` só serve como desfecho no backtest (DATA_QUALITY, seção 4).
- **Listas, a partir da curva.** Foque: idade até a última idade em que a chance ainda é pelo menos metade da de um deal novo. Limpe: chance abaixo de 2% (`config.LIMPE_MIN_CHANCE`) **ou** idade acima do maior ciclo já ganho até a data do modelo; vale o que chegar primeiro. Reative: o que fica entre os dois. Qualifique: Prospecting, que não tem data de engajamento e por isso não tem chance nem score.
- **Vendedor.** Não entra em nenhuma conta (CLAUDE.md, decisão 4); um teste permuta os vendedores e confere que nenhum score muda.
- **Curva v1 (só comparação).** `logit = b0 + b1 * max(0, idade - joelho) / 30`, com `b1 <= 0` e o joelho escolhido numa grade de 0 a 180 dias; todas as fotos, sem separar a fase do trimestre. A tabela dos modelos v1 está no fim desta seção.

Parâmetros de hoje e a regra das listas (curva v2):

<!-- AUTO:scoring-hoje -->
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
<!-- /AUTO:scoring-hoje -->

Antes e depois da correção, as mesmas listas de hoje:

<!-- AUTO:scoring-hoje-antes-depois -->
| Lista | Regra v1 | Deals (v1) | Valor de tabela (v1) | Regra v2 | Deals (v2) | Valor de tabela (v2) |
| :--- | :--- | ---: | ---: | :--- | ---: | ---: |
| Foque | idade até 95 dias | 126 | US$ 300.790 | idade até 61 dias | 60 | US$ 123.253 |
| Reative | 96 a 138 dias | 172 | US$ 392.775 | 62 a 95 dias | 66 | US$ 177.537 |
| Limpe | mais de 138 dias | 1.291 | US$ 3.198.664 | mais de 95 dias | 1.463 | US$ 3.591.439 |
| Qualifique | Prospecting (sem data) | 500 | US$ 1.073.986 | Prospecting (sem data) | 500 | US$ 1.073.986 |
<!-- /AUTO:scoring-hoje-antes-depois -->

Parâmetros do modelo v2 ajustado em cada corte (cada um vê só os dados até a sua data):

<!-- AUTO:scoring-modelos -->
| Modelo ajustado até | Mês do trimestre | Chance de deal novo | Fim do Foque (dias) | Fim do Reative (dias) | O Limpe começa por | Fotos | Linhas de treino | Taxa base de treino |
| :--- | ---: | ---: | ---: | ---: | :--- | ---: | ---: | ---: |
| 30/06/2017 | 3 | 49,3% | 79 | 95 | chance abaixo de 2% | 1 | 1.330 | 45,8% |
| 31/07/2017 | 1 | 46,8% | 109 | 125 | chance abaixo de 2% | 1 | 1.618 | 44,4% |
| 31/08/2017 | 2 | 43,4% | 133 | 138 | maior ciclo já ganho | 1 | 1.535 | 40,1% |
| 30/09/2017 | 3 | 50,2% | 75 | 95 | chance abaixo de 2% | 2 | 3.016 | 40,0% |
| 31/12/2017 (hoje) | 3 | 49,5% | 61 | 95 | chance abaixo de 2% | 3 | 5.425 | 32,2% |

Fim do Foque = última idade em que a chance ainda é pelo menos 50% da de um deal novo. Fim do Reative = o que chegar primeiro: chance abaixo de 2% ou idade acima do maior ciclo já ganho até a data do modelo (138, 138, 138, 138 dias nos quatro cortes e 138 hoje). Casos em que a fase do trimestre não tinha foto elegível e o ajuste usou todas as fotos: 0.
<!-- /AUTO:scoring-modelos -->

A chance que cada modelo dá por idade:

<!-- AUTO:scoring-curva -->
| Modelo ajustado até | 0 dias | 15 dias | 30 dias | 45 dias | 60 dias | 75 dias | 90 dias | 105 dias | 120 dias | 150 dias |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 30/06/2017 | 49,3% | 49,3% | 48,9% | 48,5% | 48,5% | 33,1% | 8,8% | 0,0% | 0,0% | 0,0% |
| 31/07/2017 | 46,8% | 46,8% | 46,8% | 46,8% | 46,8% | 46,8% | 46,8% | 32,2% | 8,8% | 0,0% |
| 31/08/2017 | 43,4% | 43,4% | 43,4% | 43,4% | 43,4% | 43,4% | 43,4% | 39,3% | 35,1% | 1,3% |
| 30/09/2017 | 50,2% | 50,2% | 49,6% | 46,5% | 41,3% | 26,0% | 6,6% | 0,0% | 0,0% | 0,0% |
| 31/12/2017 (hoje) | 49,5% | 49,5% | 49,0% | 42,3% | 27,0% | 15,5% | 6,6% | 0,0% | 0,0% | 0,0% |
<!-- /AUTO:scoring-curva -->

Nos cortes de 31/07 e 31/08 a curva é plana por mais tempo porque, naquela fase do trimestre (1º e 2º mês), os deals de 30 a 100 dias de fato ganharam tanto quanto ou mais que os novos nas fotos de treino. A curva v2 é monotônica desde o dia 0, mas só cai quando os dados mostram a queda; o corte de 30/09 e hoje, ambos de fim de trimestre, caem cedo.

Modelos v1 (os da curva antiga), para comparação:

<!-- AUTO:scoring-modelos-v1 -->
| Modelo ajustado até | Joelho (dias) | Chance de deal novo | Inclinação por 30 dias | Meia-vida depois do joelho (dias) | Limite de Limpe (dias) | Fotos | Linhas de treino | Taxa base de treino |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 30/06/2017 | 70 | 49,0% | -4,71 | 6,9 | 138 | 1 | 1.330 | 45,8% |
| 31/07/2017 | 100 | 46,9% | -5,60 | 5,7 | 138 | 2 | 2.948 | 45,0% |
| 31/08/2017 | 95 | 46,0% | -1,72 | 18,3 | 138 | 3 | 4.483 | 43,3% |
| 30/09/2017 | 90 | 45,6% | -1,96 | 16,0 | 138 | 4 | 6.169 | 41,2% |
| 31/12/2017 (hoje) | 95 | 39,9% | -2,59 | 11,3 | 138 | 7 | 13.100 | 33,2% |
<!-- /AUTO:scoring-modelos-v1 -->

## 3. Por que assim

- **Horizonte de 90 dias (um trimestre).** Os deals do dataset fecham no trimestre do engajamento ou no seguinte, e o win rate depende do mês dentro do trimestre (DATA_QUALITY, seção 2). Uma janela de 90 dias contém sempre exatamente um mês de fim de trimestre. Na v1 isso neutralizava a sazonalidade só na média; na v2 a sazonalidade passa a ser tratada de frente, treinando cada corte com as fotos da mesma fase. O 90 foi escolhido conhecendo o dataset; é uma escolha de desenho divulgada (seção 4, risco 8), não um parâmetro otimizado.
- **Monotonicidade desde o dia 0.** Um protótipo exploratório do planejador (logística segmentada sem restrição) produziu uma curva que sobe com a idade. Isso não faz sentido para uma lista de prioridades. A v1 impôs `b1 <= 0`, mas ficava plana antes do joelho; a v2 impõe a monotonicidade por regressão isotônica, sem forma paramétrica.
- **Mesma fase do trimestre.** A seção 0 mostra que as fotos de fim e de meio de trimestre têm padrões opostos. Misturá-las dá uma média sem significado para nenhuma data. O custo é treinar com menos fotos (seção 11).
- **Primeira foto em 31/03/2017.** O primeiro fechamento do dataset é de 01/03/2017, e os fechamentos do primeiro trimestre são só de março (artefato de recorte, DATA_QUALITY, seção 2). Começar em 28/02 exigiria supor que o recorte removeu exatamente os fechados antes de 01/03. Esta regra foi escolhida depois de o planejador ver que 28/02 piora o corte de 30/06 na v1; 28/02 é reportado como sensibilidade (seção 7).
- **Ordenação do Foque por valor esperado.** Agora a chance cai dentro do Foque, então o valor esperado não ordena mais só pelo preço: um deal de 60 dias e um de 20 dias do mesmo produto recebem scores diferentes. Os empates saem por "faltam menos dias até o fim do Foque".
- **Limpe por dois critérios.** Só o maior ciclo já ganho (138 dias) é um teto do gerador. A chance abaixo de 2% é um critério que viria dos dados também num CRM real; vale o que chegar primeiro. Hoje a chance chega a 2% antes do teto, e por isso o Limpe de hoje inclui deals que a v1 chamava de Reative.
- **Faixas fixas do briefing contra limiares aprendidos.** O briefing separou hoje em até 90 dias (110 deals), de 91 a 138 dias (188) e acima de 138 (1.291). A curva aprende limiares mais estreitos para o Foque e o Reative, e um Limpe maior. A tabela da seção 2 mostra os dois conjuntos de contagens lado a lado.

## 4. Checagem de vazamento

Para um corte T, o modelo e os scores só podem depender do que um CRM já teria registrado até o fim do dia T. Cada risco abaixo tem uma guarda no código e um teste; a prova central é o **teste de mutação do futuro**: tudo o que acontece depois de T (desfecho, datas, valores, contas, produtos, vendedores dos deals engajados depois) é trocado por valores aleatórios, e o modelo e os scores dos abertos em T têm de ficar idênticos, bit a bit. Um controle negativo (um modelo de corte posterior tem de mudar com a mutação) garante que a mutação mexe em algo que importa. O teste vale para a curva v2 (o modelo padrão) e para a v1.

| # | Risco | Guarda | Teste |
|---|---|---|---|
| 1 | Estágio final (Won/Lost) usado como estado em T | `as_of(T)` reconstrói o estado a partir das datas | `test_as_of_hides_every_event_after_T`, `test_future_mutation_leaves_model_and_scores_unchanged` |
| 2 | Rótulo de treino com evento depois de T | só fotos com S + 90 dias <= T, com `assert` | `test_training_set_respects_the_horizon_for_every_cut` |
| 3 | Conta ausente equivale a "nunca fechou" (os 1.425 sem conta estão todos abertos) | `has_account` fora do modelo; atributos de conta só no subconjunto com conta | `test_account_columns_do_not_change_the_model_or_scores`; auditoria da seção 7 |
| 4 | `close_value` usado como valor do deal aberto | o valor é `sales_price` | `test_close_value_is_never_read` |
| 5 | Parâmetros (faixas da curva, fim do Foque, fim do Reative, escala) ajustados com dados de depois de T | tudo ajustado por corte, a partir de `as_of(T)` | mutação do futuro; `test_limpe_limit_comes_from_wins_closed_up_to_T` |
| 6 | Explicações vindas de um modelo que viu o futuro | `explain` só recebe o modelo do corte | `test_explanation_uses_the_cut_model_not_a_global_one` |
| 7 | Prospecting no passado não é reconstruível | `as_of` descarta Prospecting; Qualifique só na data de referência | `test_prospecting_is_only_scored_when_asked_and_never_gets_a_score` (limite de cobertura, não vazamento) |
| 8 | Hiperparâmetros (horizonte, primeira foto, largura da faixa, fase do trimestre) escolhidos conhecendo os dados | divulgado; sensibilidade em 28/02 e com pseudo-contagem | sem teste unitário possível |
| 9 | Preço de catálogo estático | um preço por produto, premissa documentada | `test_each_product_has_a_single_list_price` |
| 10 | Colunas derivadas do arquivo (`age_days`, `cycle_days`, `is_open`) calculadas com a data de referência | `as_of` as recalcula em T | `test_as_of_recomputes_age_and_cycle_from_dates` |
| 11 | Vendedor ou manager entrando no score | o treino não tem essas colunas | `test_permuting_sales_agent_changes_no_score`, `test_training_set_has_no_seller_columns` |
| 12 | Foto de outra fase do trimestre, ou posterior a T, entrando no treino da curva v2 | `same_phase` filtra depois de `training_set`, que já exige S + 90 dias <= T | `test_v2_trains_only_with_photos_of_the_same_phase_and_before_T`, `test_v2_ignores_the_outcomes_of_photos_from_other_phases` |

Para ver se os testes pegam o vazamento de verdade, a 3a estragou uma guarda por vez em cópias do pacote (6 sabotagens, sobre o código da v1): todas foram detectadas, por 2 a 9 testes cada. A sabotagem "treino sem a regra S + 90 <= T" não é pega pela mutação (o rótulo vira "não ganho", que enviesa mas não vaza), só pelos testes de horizonte; por isso as duas guardas do rótulo existem. As sabotagens não foram repetidas para a v2, que reaproveita as mesmas guardas e acrescenta a do risco 12. **O que a checagem não cobre:** escolher o desenho (horizonte, primeira foto, fase do trimestre) olhando os mesmos cortes que depois avaliam o modelo é um risco de ajuste ao teste que nenhum teste unitário elimina (risco 8). A troca de curva desta correção foi feita depois de ver o backtest da v1, então esse risco é maior para a v2 do que era para a v1 (seção 9).

## 5. Desenho do backtest e censura

- **Cortes.** 30/06, 31/07, 31/08 e 30/09/2017 (rolling-origin). Em cada um, o modelo é ajustado só com `as_of(T)`; na v2, só com as fotos da mesma fase do trimestre de T, então os cortes de 30/06, 31/07 e 31/08 têm uma só foto de treino e o de 30/09 tem duas.
- **População.** Os Engaging abertos em T, incluindo os zumbis. Prospecting fica de fora (sem data de engajamento).
- **Desfecho.** Vem dos dados completos: ganho até 31/12/2017 (`y`), receita ganha (`close_value` dos Won) e ganho dentro dos 90 dias seguintes ao corte (`y_90`, usado só em Brier, log-loss e calibração). Os quatro cortes têm a janela de 90 dias completa antes de 31/12/2017.
- **Métodos comparados.** Score v2 (valor esperado); score v1; ordenar por **valor** (preço de tabela); **recência** (os mais novos primeiro); **aleatório** (200 sorteios, sementes 0 a 199, com p5 e p95). Como diagnóstico, a chance v2 sozinha, sem o preço.
- **Métricas.** AUC; ganhos capturados no top 20% (por contagem de deals); receita capturada no top 20% (a métrica primária). Empates de score são tratados pelo valor esperado sob desempate aleatório, e não pela ordem do arquivo.
- **Ordem dentro do Foque (métrica nova).** População: os Engaging abertos em T com idade de até 90 dias, a mesma para todos os métodos (score v1, score v2, valor, recência). Métricas: AUC de ganho até 31/12/2017 e receita no top 20% dessa população. O aleatório entra só como referência. Calculada nos 4 cortes e na média.
- **Censura.** Os deals ainda abertos em 31/12/2017 contam como "não ganho até 31/12". Isso é uma suposição: um deal aberto pode ainda fechar. A tabela de sensibilidade da seção 7 separa os que de fato podem fechar (abertos em 31/12 com idade ainda dentro do maior ciclo ganho: zero nos cortes de junho e julho, 81 no de agosto e 183 no de setembro) dos zumbis que o dataset nunca fecha. E mostra o resultado só com os resolvidos.

## 6. Resultados

Receita capturada no top 20%, corte a corte, contra o critério pré-registrado (curva v2; a v1 passou também):

<!-- AUTO:scoring-criterio -->
| Corte | Score v2 | Valor | Recência | Aleatório (média) | Aleatório (p95) | Margem sobre o melhor baseline | Vence os 4? |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 30/06/2017 | 61,0% | 48,6% | 27,7% | 20,0% | 23,4% | +12,4 pp | sim |
| 31/07/2017 | 57,4% | 48,7% | 12,8% | 20,1% | 23,4% | +8,7 pp | sim |
| 31/08/2017 | 59,9% | 48,2% | 31,6% | 19,8% | 23,0% | +11,8 pp | sim |
| 30/09/2017 | 71,7% | 47,1% | 46,8% | 20,3% | 24,4% | +24,7 pp | sim |

Receita capturada no top 20%, curva v2. Empate é diferença de até 0,01 e não vence. Resultado: **PASSOU**.
- curva v1 (platô + queda, todas as fotos): passou; receita média do score nos cortes: 61,1%.
- curva v2 (faixas isotônicas, fotos da mesma fase do trimestre): passou; receita média do score nos cortes: 62,5%.
<!-- /AUTO:scoring-criterio -->

Tabela principal (corte × método, com a v1 ao lado):

<!-- AUTO:scoring-backtest -->
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
<!-- /AUTO:scoring-backtest -->

Média dos cortes:

<!-- AUTO:scoring-media -->
| Método | AUC | Ganhos capturados no top 20% | Receita capturada no top 20% |
| :--- | ---: | ---: | ---: |
| Score v2 (valor esperado, curva por faixas) | 0,66 | 27,4% | 62,5% |
| Score v1 (platô, antes da correção) | 0,64 | 26,3% | 61,1% |
| Ordenar por valor | 0,49 | 20,0% | 48,1% |
| Mais recentes primeiro | 0,70 | 29,8% | 29,7% |
| Aleatório (média de sorteios) | 0,50 | 20,0% | 20,0% |
| Só a chance v2 (diagnóstico) | 0,72 | 30,6% | 31,1% |

Média simples dos 4 cortes. Brier da chance v2: 0,180 (v1: 0,185) contra 0,221 da taxa média de treino (log-loss 0,512, v1: 0,524, contra 0,636), sobre ganhos em 90 dias.
<!-- /AUTO:scoring-media -->

**Onde o score v2 ganha.** Na receita capturada, em todos os cortes, com folga sobre o melhor baseline. O score troca um pouco de taxa de acerto por mais receita: a chance sozinha, sem o preço, captura bem menos receita que o score. Quem põe a receita é o preço.

**v2 contra v1, sem rodeio.** Na receita capturada a v2 fica abaixo da v1 por menos de um ponto percentual nos cortes de 30/06, 31/07 e 31/08, e acima por cerca de sete pontos percentuais no de 30/09. A média sobe por causa de um corte. Os três primeiros têm uma foto só de treino, então a v2 e a v1 aprendem quase a mesma coisa neles. A melhora é real onde importa para hoje (um fim de trimestre), mas está apoiada num só corte e esse corte tem poucas fotos.

**Onde a recência ganha, sem rodeio.** Em AUC e em captura de ganhos, nos cortes de 30/06, 31/08 e 30/09 (a AUC da recência chega a 0,83 em 30/09, contra 0,72 do score v2 e 0,65 do v1). Em receita, a recência perde para o score nos quatro cortes, mas em 30/09 chega a 46,8%, quase igual ao valor (47,1%). A chance v2 sozinha, sem o preço, empata com a recência em AUC nesse corte (0,83): a curva v2 aprendeu o que a recência já sabia. É coerente com o padrão do gerador que o DATA_QUALITY documenta (os deals fecham no trimestre do engajamento ou no seguinte, e os fechamentos rápidos se concentram no primeiro mês do trimestre): num fim de trimestre, quem foi engajado há 61 a 90 dias e continua aberto já passou da janela em que o gerador costuma fechar.

**Onde a recência desaba.** Em 31/07 ela captura 12,8% da receita, abaixo do sorteio (20,1%), e só 12,2% dos ganhos. Nesse corte, os deals de até 30 dias (engajados em julho) ganharam 24,3% nos 90 dias seguintes, contra 53,8% dos de 31 a 60 dias (tabela da seção 10). Ordenar pelos mais novos põe no topo os que menos ganham.

**Ordem dentro do Foque.** A pergunta do Rafael foi "dentro do Foque, o score ordena ou só ordena por preço?". A resposta, para deals de até 90 dias:

<!-- AUTO:scoring-foque-ordem -->
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
<!-- /AUTO:scoring-foque-ordem -->

Só no corte de 30/09 o score v2 ordena melhor que o preço e que o v1, com um intervalo que não inclui zero; nos de 31/07 e 31/08 os três métodos dão exatamente a mesma ordem, porque a curva v2 desses cortes é plana até além de 90 dias (acima). No de 30/06 a diferença sobre o valor é de 2,3 pontos percentuais, com intervalo que inclui zero. A AUC média do v2 é perto de um sorteio: o ganho de ordem dentro do Foque existe, mas é pequeno e concentrado no fim de trimestre. A recência tem a maior AUC média nessa população e a pior receita, de novo pelo mesmo motivo: ordena os mais novos primeiro, que não são os de maior valor.

**Brier e log-loss.** A chance v2 supera a constante (a taxa média de treino) nos quatro cortes, tanto em Brier quanto em log-loss. Contra a v1, a v2 melhora no corte de 31/08 e muito no de 30/09 (fim de trimestre), e fica uma fração de milésimo pior nos de 30/06 e 31/07. Isso não decide o critério.

**Categorias.** Quase toda a receita ganha depois do corte vem do Foque; o Limpe, por construção do dataset, nunca ganha (zero ganhos nos quatro cortes):

<!-- AUTO:scoring-categorias -->
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
<!-- /AUTO:scoring-categorias -->

**Calibração.** A chance do modelo agora é a das fotos da mesma fase do trimestre. Nos cortes de fim de trimestre a faixa de 61 a 90 dias deixa de ser a média achatada da v1, mas ainda fica acima do observado no corte de 30/09:

<!-- AUTO:scoring-calibracao -->
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
<!-- /AUTO:scoring-calibracao -->

No corte de 30/09 a chance média de 61 a 90 dias cai de 45,6% (v1) para 33,7% (v2) e o observado foi 6,7%: melhorou, mas a v2 ainda é otimista nessa faixa. Não testei a causa; o modelo desse corte tem só duas fotos de fim de trimestre (março e junho). No corte de 31/08 a v2 fica pior que a v1 nas faixas de 121 a 150 dias (18,6% contra 8,7%, com 2,3% observado), por causa de uma foto só.

**Bootstrap.** A diferença do score v2 para valor e recência, com intervalo de confiança por reamostragem dos deals:

<!-- AUTO:scoring-bootstrap -->
| Corte | Score v2 menos valor | Score v2 menos recência |
| :--- | ---: | ---: |
| 30/06/2017 | +12,4 pp (IC +9,3 pp a +15,7 pp) | +33,3 pp (IC +26,7 pp a +40,5 pp) |
| 31/07/2017 | +8,7 pp (IC +6,4 pp a +11,3 pp) | +44,6 pp (IC +39,2 pp a +50,1 pp) |
| 31/08/2017 | +11,8 pp (IC +9,1 pp a +14,6 pp) | +28,3 pp (IC +22,1 pp a +34,6 pp) |
| 30/09/2017 | +24,7 pp (IC +20,3 pp a +30,0 pp) | +24,9 pp (IC +17,8 pp a +32,0 pp) |

Diferença na receita capturada no top 20%, em pontos percentuais; IC de 2,5% a 97,5% por 1.000 reamostragens dos deals do corte (semente 0).
<!-- /AUTO:scoring-bootstrap -->

Os intervalos não incluem zero em nenhum corte, mas os quatro cortes usam os mesmos deals em datas diferentes e não são amostras independentes. O bootstrap reamostra deals, não épocas.

## 7. Sensibilidades e auditoria

<!-- AUTO:scoring-sensibilidade -->
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
<!-- /AUTO:scoring-sensibilidade -->

- **Primeira foto em 28/02.** O critério passaria do mesmo jeito. Na v2 quase nada muda, porque a foto de 28/02 é da fase 2 e só entra no corte de 31/08.
- **Pseudo-contagem do ajuste único.** Com 20 deals de pseudo-contagem por faixa, o critério também passaria, mas o Foque dos cortes de 30/06 e 31/07 nunca terminaria (a cauda sem ganhos fica em chance alta), a AUC cai para uma faixa de 0,54 a 0,59 e a chance de um deal com 730 dias vira 26,9%. É a razão de a v2 usar a regressão isotônica pura.
- **Só resolvidos.** Quando se tiram os deals ainda abertos em 31/12, o score deixa de ser melhor que ordenar por valor: a diferença fica em torno de 1 ponto percentual para um lado ou para o outro, e a AUC dos três métodos fica em torno de 0,5. Na população de deals que fecharam, a chance por idade não separa ganhos de perdas. A vantagem do score sobre o valor nos cortes completos vem de identificar os zumbis: deals abertos há mais que o maior ciclo já ganho, que o dataset nunca fecha. Esse padrão (nenhum ciclo acima de 138 dias) é provável artefato do gerador (DATA_QUALITY, seção 1). O score sobre a população completa é a leitura honesta do que a ferramenta faz na prática (limpar a fila), mas não prova que ela preveja ganhos entre deals que de fato se resolvem. A correção não mudou isso.

<!-- AUTO:scoring-auditoria -->
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
<!-- /AUTO:scoring-auditoria -->

- **"E se houvesse vazamento?"** Um modelo v2 ajustado com os dados até 31/12/2017 (da mesma fase do trimestre do corte) e avaliado nos cortes passados, rotulado VAZADO e nunca reportado como resultado, é igual ou melhor que o honesto em todos os cortes, e no de 30/09 a receita vazada é 7,2 pontos percentuais maior (nos outros, entre 0,4 e 1,0). Isso muda o que o texto da v1 dizia ("o vazamento de parâmetros custa pouco"): a curva v2 é flexível e, com o futuro, ganha de verdade no corte de 30/09, porque o modelo de hoje já viu o desfecho de setembro. É exatamente o que a mutação do futuro e as guardas da seção 4 impedem no modelo honesto; não prova que o modelo esteja livre de vazamento, mostra o tamanho do que as guardas protegem.
- **`has_account` sozinho.** Na população dos cortes, nenhum deal sem conta foi ganho depois (zero em todos), e a AUC de `has_account` sozinho (0,72 a 0,79) é maior que a do score v2 em todos os cortes. Por isso é proibido: parece o melhor preditor, mas só identifica deals que nunca fecham no dataset, e um modelo que o usasse venceria o backtest sem entender nada do negócio.

## 8. Atributos testados e descartados

Um atributo por vez, sobre a curva de idade com o joelho fixo, com one-hot (categoria de referência a mais frequente) e penalidade L2 de 1,0 só nos coeficientes do atributo. Produto e região usam todos os deals; setor e porte (tercil de funcionários, calculado nas contas) só os deals com conta, no treino e na avaliação, contra a curva só de idade ajustada no mesmo subconjunto. Regra pré-registrada: entra só se melhorar o log-loss em todos os cortes e não piorar a receita no top 20% em nenhum. O vendedor não é testado. **O teste foi feito sobre a curva v1 e não foi repetido sobre a v2** (o desenho com um joelho fixo não se aplica à curva por faixas); é uma limitação (seção 11).

<!-- AUTO:scoring-atributos -->
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
<!-- /AUTO:scoring-atributos -->

**Nenhum atributo entra.** Produto, setor e porte pioram o log-loss em pelo menos um corte (porte melhora em três de quatro por margens de milésimos), e todos pioram a receita no top 20% em algum corte. A região é o caso instrutivo: dentro da amostra de treino ela parece ajudar (o Δ log-loss no treino é o mais negativo da tabela de diagnóstico), mas fora da amostra piora em três dos quatro cortes. No treino do corte de 30/09, a região Central ganhava bem mais que as outras entre os deals jovens; depois do corte, a diferença desapareceu e até se inverteu. É a razão de a validação ser sempre temporal (CLAUDE.md, decisão 6).

## 9. Critério pré-registrado e se houve ajuste

**Escrito antes do backtest** (25/10/2026, 16:28; o primeiro número de desempenho só apareceu às 19:05, depois de uma interrupção por limite de uso da API, registrada em `process-log/03_bloco-3.md`).

**Métrica primária.** Receita capturada no top 20%: fração da receita ganha (o `close_value` dos Won) que cai nos 20% de maior score, por contagem de deals, com empates tratados pelo valor esperado sob desempate aleatório.

**O score vence se**, em cada um dos 4 cortes (30/06, 31/07, 31/08 e 30/09/2017), a receita capturada no top 20% for maior que a de ordenar por valor, maior que a de ordenar pelos mais recentes, e maior que a média e o percentil 95 de 200 sorteios aleatórios (sementes 0 a 199).

**Empate.** Diferença de até 0,01 (1 ponto percentual) é empate, e empate não vence.

**Não decidem.** AUC, captura de ganhos e Brier são reportados, mas não entram na decisão.

**Ajuste único, só se o critério falhar.** Trocar a curva "platô + queda" por faixas de 15 dias de idade, com a taxa de cada faixa suavizada por uma pseudo-contagem de 20 deals rumo à taxa média de treino, forçada a não crescer (algoritmo PAVA, pesos = n + 20) e interpolada linearmente entre os pontos médios das faixas. Mesma janela, mesmo horizonte de 90 dias, nada mais muda. Roda-se uma vez.

**Se ainda falhar.** Fica o modelo de melhor média na métrica primária e a falha é documentada com números. Sem novas tentativas e sem trocar de métrica.

**Regra para atributos.** Um atributo só entra no score se melhorar o log-loss da chance de ganho em 90 dias em todos os cortes e não piorar a receita capturada no top 20% em nenhum. O vendedor não é testado.

**Resultado original: PASSOU com a curva v1, e o ajuste não foi aplicado.** O critério passou na primeira rodada; o ajuste único (faixas de 15 dias e PAVA) estava implementado e testado, mas não foi rodado, porque a regra só o autoriza se o critério falhar.

**Mudança pós-backtest: a curva v2.** Depois de publicada, o Rafael usou a ferramenta como vendedor, viu a chance constante no Foque e pediu a correção. **Esta é uma mudança feita depois de ver o resultado do backtest, pedida por ele depois de revisar a ferramenta, e não faz parte do pré-registro.** A mudança tem duas partes que o pré-registro não previa: (a) as faixas isotônicas treinadas só com fotos da mesma fase do trimestre, e (b) a retirada da pseudo-contagem do ajuste único, escolhida por um motivo medido (a cauda sem ganhos subia a 13% a 27%), não pelo backtest. O critério pré-registrado, a métrica primária, o empate de 1 ponto percentual e os quatro cortes foram mantidos, e o resultado é reportado para a v2 e para a v1 (seção 6): **PASSOU nas duas**. Como a v2 foi desenhada sabendo o que o backtest da v1 mostrou (a queda no fim do trimestre), o PASSOU da v2 não tem o valor de um teste às cegas; vale como verificação de que a correção não estragou o que já funcionava, e o corte de 30/09 (onde a v2 mais melhora) é justamente o que inspirou o desenho.

**O que o pré-registro garante, e o que não.** A regra, o desempate e o ajuste único não mudaram depois de ver o resultado. Mas o critério não foi fixado às cegas: o planejador tinha rodado um protótipo e o plano trazia valores esperados próximos dos obtidos, então já se sabia que o score tendia a passar. A métrica primária foi escolhida porque a dor é onde pôr a hora do vendedor, e não por ser a que o score ganha (a recência ganha em AUC).

## 10. O que não funcionou e por quê

- **A curva não monotônica do protótipo.** A logística sem restrição subia com a idade no corte de 30/06. Corrigido com `b1 <= 0`; foi uma correção de desenho antes do backtest, não um ajuste pós-resultado.
- **O platô da v1 (o erro desta correção).** A justificativa do bloco 6 era que, dentro do Foque, a diferença entre os deals velhos e os novos trocava de sinal entre os cortes, então "não havia inclinação estável a aprender". O sinal troca, mas por um motivo que a v1 não enxergava: a posição do corte no trimestre. Separando as fotos por fase (seção 0), a inclinação é estável dentro de cada fase. Medido na tabela abaixo, no corte de 30/09 a v1 dava 45,6% a todo o Foque e o observado foi de 48,0% (até 30 dias) a 6,7% (61 dias ou mais). O erro foi aceitar um platô que contradizia o briefing e só chamar de "medido, não corrigido".
- **A chance estável "em cada data".** A justificativa do plano era que a chance de ganho fica estável enquanto o deal é jovem. No agregado das fotos é verdade, mas por data não é: depende da posição da foto no trimestre.
- **Reative fraco nos fins de trimestre.** No corte de 30/09, os deals de Reative da v2 ganharam 5,2% e no de 30/06, 4,3%. A lista Reative promete pouco e entrega pouco; com a v2 ela ficou menor.
- **Corte de 30/06 com uma foto só.** O modelo desse corte vê 1.330 linhas de uma só foto. Na v2 isso vale para três dos quatro cortes. Eles sustentam o critério, mas são os menos estáveis.
- **P < recência em AUC e captura de ganhos** na maioria dos cortes (seção 6), e a antecipação do plano de que isso valeria sempre falhou em 31/07.
- **Região** parecia ajudar no treino e não ajudou fora da amostra (seção 8).
- **Só resolvidos.** O score não bate o valor entre os deals que fecharam (seção 7). Isto é o que mais pesa contra a tese de "frescor": a idade ajuda a achar o que está morto, não a escolher entre o que está vivo.

**Foque do corte por idade, com a chance da v2** (a comparação entre a chance que o modelo deu e o que de fato aconteceu dentro do Foque de cada corte):

<!-- AUTO:scoring-foque-idade -->
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
<!-- /AUTO:scoring-foque-idade -->

Com a v2 o Foque é mais curto nos fins de trimestre e a chance dentro dele cai com a idade (45,9% de 31 a 60 dias e 36,6% a partir de 61 dias, no corte de 30/09), mas continua otimista para os deals de 61 dias ou mais (6,7% observado). O resíduo vem de o modelo de 30/09 ter só duas fotos de treino de fim de trimestre.

## 11. Limitações

- **Dados sintéticos.** O dataset é gerado; em CRM real, o decaimento seria mais suave. O teto de 138 dias é provável artefato do gerador e o Limpe herda esse artefato quando é ele que decide (nos cortes de agosto e em casos de idade acima do teto); a queda no fim do trimestre também parece do gerador. Em dados reais, um deal com mais de 138 dias pode ser ganho.
- **A vantagem vem dos zumbis.** Entre os deals resolvidos, o score não é melhor que o preço (seção 7). A ferramenta ajuda a limpar a fila e a priorizar por valor; ordena pouco o que está vivo (AUC média de 0,52 dentro do Foque).
- **Poucas fotos por fase.** Treinar só com a fase do corte deixa os cortes de 30/06, 31/07 e 31/08 com uma foto. A forma da curva muda de um corte para outro (seção 2) em parte por isso. Hoje o modelo tem três fotos, todas de fim de trimestre.
- **A v2 foi desenhada depois do backtest.** O PASSOU da v2 não é um teste às cegas (seção 9). Escolhas da v2 (largura da faixa de 15 dias, fase do trimestre, 50% e 2% como limiares) são divulgadas e não tiveram sensibilidade medida, exceto a pseudo-contagem.
- **Atributos não retestados.** O teste da seção 8 foi feito sobre a v1.
- **Censura.** Deals abertos em 31/12/2017 contam como "não ganho". Para os cortes de agosto e setembro, uma parte deles ainda pode fechar (seção 7), e isso subestima o ganho desses cortes.
- **Cortes sobrepostos.** Os quatro cortes usam os mesmos deals em datas vizinhas; o critério "vence em todos" tem menos força do que quatro testes independentes.
- **Preço de tabela.** O valor esperado usa o preço de tabela; nos ganhos, o valor fechado fica perto dele em média, mas varia por deal (DATA_QUALITY, seção 4).
- **Prospecting.** Sem data de engajamento, não tem chance, score nem backtest. Qualifique é uma lista sem prova.
- **Vendedor.** Fora do score por decisão. Não se testou se haveria ganho em usá-lo.
