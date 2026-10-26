# Bloco 3 — features, score, explicação e validação

> Este log é escrito em duas partes. A **parte 3a** (esta execução, E4 do plano) cobre a checagem de vazamento, `features.py`, `score.py` e `explain.py`. A **parte 3b** (E5) acrescenta o backtest, o `SCORING.md` e o ajuste pré-registrado, e completa este mesmo arquivo.

## Objetivo

Construir o motor de score e de explicação (`features`, `score`, `explain`) de modo que o modelo de um corte T só enxergue o que existia em T, e **provar isso com testes** antes de qualquer número de desempenho. Pedido explícito do Rafael (PROMPTS.md, bloco 3): "pelo menos uma checagem de vazamento de dados (usar informação do futuro no treino)".

## Executor

Claude Sonnet (subagente executor). Execução da especificação E4 de `process-log/plano_execucao_opus.md`, planejada pelo Claude Opus em modo somente leitura. Nenhuma pergunta foi feita e ninguém respondeu: as decisões marcadas "(decisão autônoma do Claude)" são do executor.

## Planejamento (Opus) — protótipo exploratório

Durante o planejamento, o Claude Opus (somente leitura) rodou protótipos descartáveis via `python -c`, sem criar arquivos. Quatro achados dele moldaram o plano:

1. Uma logística segmentada sem restrição, treinada a partir de 28/02, gerou para o corte de 30/06 uma curva que **sobe** com a idade até 90 dias (não monotônica). Isso motivou a restrição monotônica e a regra de fotos a partir de 31/03. **Essa regra foi adotada depois de ver o resultado**; por isso 28/02 é reportado como sensibilidade, e não como alternativa equivalente (a justificativa a priori está em `docs/DATA_QUALITY.md`, seção 2).
2. Ordenar por recência é um baseline forte em AUC nos cortes de fim de trimestre.
3. Os deals fecham no trimestre do engajamento ou no seguinte (artefato do gerador).
4. Entre 0 e 90 dias, a taxa de ganho em 90 dias fica estável, perto de 40%, e cai depois disso.

Os números do protótipo (modelo em 31/12/2017: 7 fotos, 13.100 linhas, joelho 95, P de deal novo perto de 0,40, limite de Limpe 138; hoje: Foque 126, Reative 172, Limpe 1.291, Qualifique 500; joelhos por corte 70, 100, 95 e 90 com 1.330, 2.948, 4.483 e 6.169 linhas) entram **só como sanidade para achar bug**, não como meta. Se o meu resultado divergir, investigo o código primeiro; se o meu número estiver certo, mantenho o meu e registro a divergência.

A afirmação 4 já tinha sido questionada no bloco 1 (Q3): as duas fotos do briefing mostram a chance caindo desde cedo (50%, 34%, 7% por faixa de 30 dias, em 30/09), e não estável. A resposta com a curva ajustada fica na seção "Parte 3a — implementação".

## Checagem de vazamento — escrita antes do código

**Ordem real do trabalho.** Esta seção foi escrita antes de qualquer arquivo de código do bloco: no momento em que a escrevo, `solution/scorer/` tem só os arquivos do bloco 2 (`__init__`, `config`, `fmt`, `clean`, `facts`, `docs`), e `features.py`, `score.py` e `explain.py` não existem. Antes disto, só li a especificação, os documentos e o código do bloco 2; não rodei nenhuma conta sobre os dados. Ao final, confiro as datas de criação dos arquivos (seção "Parte 3a") para registrar a ordem de fato.

**Princípio.** Para um corte T, o modelo e os scores só podem depender de fatos que um CRM já teria registrado até o fim do dia T. O teste que prova isso é de **mutação do futuro**: troco tudo o que acontece depois de T por valores aleatórios e exijo que o modelo e os scores dos deals abertos em T fiquem idênticos, bit a bit.

| # | Risco de vazamento | Guarda no código | Teste (arquivo) |
|---|---|---|---|
| 1 | Estágio final (Won/Lost) usado como estado em T: um deal ganho em novembro apareceria como "ganho" numa foto de junho | `features.as_of(deals, T)` reconstrói o estado a partir das datas: quem não fechou até T vira `Engaging`, com `close_date` vazia e `close_value` vazio | `test_as_of_hides_every_event_after_T`, `test_future_mutation_leaves_model_and_scores_unchanged` (`test_features.py`) |
| 2 | Rótulo de treino com evento posterior a T: a foto S olha S+H dias à frente, e S+H pode passar de T | `training_set` só usa fotos S com S+H ≤ T e tem `assert max(S)+H <= T`; `open_at` recusa S depois da data do `as_of` | `test_training_set_respects_the_horizon_for_every_cut`, `test_open_at_refuses_snapshots_after_the_as_of_date` (`test_features.py`) |
| 3 | Conta ausente equivale a "nunca fechou" (os 1.425 sem conta estão todos abertos): `has_account` e a categoria "desconhecido" de setor ou porte funcionariam como detector de zumbi | `has_account` só vai ao `training_set` como coluna de diagnóstico; nenhuma função de `score.py` lê conta, setor ou porte. Atributos de conta, no bloco 3b, só no subconjunto com conta | `test_account_columns_do_not_change_the_model_or_scores` (`test_score.py`); a mutação do futuro apaga a conta de deals fechados depois de T |
| 4 | `close_value` usado como valor do deal aberto (ele é 0 nos perdidos e positivo nos ganhos: entrega o desfecho) | O valor do deal é `sales_price`; `close_value` só existe como desfecho no backtest (3b) | `test_close_value_is_never_read` (`test_score.py`): embaralhar `close_value` não muda nada |
| 5 | Parâmetros (joelho, P de deal novo, limite de Limpe, escala do score) ajustados com dados de depois de T | Tudo é ajustado por corte, dentro de `fit_model(deals, T)`, a partir de `as_of(T)`; o limite de Limpe é o maior ciclo dos ganhos com `close_date` ≤ T (e não o 138 global) | `test_future_mutation_leaves_model_and_scores_unchanged` (parâmetros idênticos); `test_limpe_limit_comes_from_wins_closed_up_to_T` (`test_score.py`) |
| 6 | Explicações e números do modo teste vindos de um modelo que viu o futuro | `explain_deal(row, model)` e `how_it_works(model, ...)` só recebem o modelo do corte; nenhum número é lido de arquivo global | `test_explanation_uses_the_cut_model_not_a_global_one` (`test_explain.py`) |
| 7 | Prospecting no passado não é reconstruível (o CRM não registra quando o deal entrou em Prospecting) | `as_of` exige `engage_date` e descarta Prospecting; `score_deals` só devolve Qualifique com `include_prospecting=True` (data de referência = fim dos dados) | `test_prospecting_is_only_scored_when_asked_and_never_gets_a_score` (`test_score.py`). Limite de cobertura, não vazamento: Qualifique fica fora do backtest |
| 8 | Hiperparâmetros (H = 90, primeira foto, grade de joelhos) escolhidos conhecendo os dados | Divulgados: H é um trimestre; a primeira foto vem da investigação 2a (justificada a priori, mas escolhida depois de ver o protótipo); a grade vai de 0 a 180 em passos de 5 | Sem teste unitário possível. Sensibilidade (28/02 e demais) fica para o 3b |
| 9 | Preço de catálogo é estático, então o preço usado em T pode ter vindo de depois | Aceitável: `sales_price` é o preço de tabela do produto (um preço por produto) e `price_min`/`price_max` são o mínimo e o máximo do catálogo. Documentado como premissa | `test_price_range_matches_the_catalog` e `test_each_product_has_a_single_list_price` (`test_score.py`) |
| 10 | Colunas derivadas do `deals.csv` (`age_days`, `cycle_days`, `is_open`) foram calculadas com a data de referência 31/12/2017 e carregam o futuro (por exemplo, `cycle_days` existe para deals fechados depois de T) | `as_of` descarta essas colunas e as recalcula a partir das datas e de T; `open_at` recalcula a idade em S | `test_as_of_recomputes_age_and_cycle_from_dates` (`test_features.py`); a mutação do futuro corrompe de propósito `cycle_days` dos fechados depois de T |
| 11 | O vendedor (ou o manager) entrar no score, direta ou indiretamente (CLAUDE.md, decisão 4) | O `training_set` não tem colunas de vendedor nem de manager; `fit_model` e `score_deals` só leem `age_days` e `sales_price` | `test_training_set_has_no_seller_columns` (`test_features.py`), `test_permuting_sales_agent_changes_no_score` (`test_score.py`) |

**O que o teste de mutação muda** (para valer como prova, e não como formalidade):

- Todo deal com `close_date` > T: desfecho (Won/Lost) sorteado, `close_date` sorteada em (T, 31/12/2017], `close_value` sorteado, `cycle_days` (coluna derivada) corrompida, e `account` apagada em metade deles.
- Todo deal engajado depois de T: produto e preço (juntos, porque o preço vem do produto), vendedor, manager, região e data de engajamento embaralhados; estágio sorteado.
- Os Prospecting (que no passado não existem): produto, preço e vendedor embaralhados.
- **Controle negativo:** um modelo ajustado num corte **posterior** (30/09) com os dados mutados tem de **mudar**. Sem isso, "o modelo de 30/06 não mudou" poderia ser verdade só porque a mutação não mexeu em nada que importe.
- Critério: `fit_model` devolve o mesmo objeto (igualdade exata dos números) e `score_deals` devolve as mesmas colunas de score, categorias e prazos para todos os deals abertos em T.

**O que esta checagem não cobre** (limites que o 3b e o SCORING repetem):

- Escolher o desenho (H, primeira foto, grade) olhando os mesmos cortes que depois avaliam o modelo é um risco de "ajuste ao teste" que nenhum teste unitário elimina; ele é divulgado (risco 8).
- Os deals ainda abertos em 31/12/2017 contam como "não ganhos" no backtest (censura à direita); isso afeta as métricas do 3b e será tratado lá.
- O gerador sintético ensina regras (Q/Q+1, fechamento rápido no 1º mês do trimestre, teto de 138 dias) que o score não explora, mas que fazem a idade parecer mais previsível do que seria num CRM real.

## Parte 3a — implementação

### O que foi feito (comandos)

1. **Leitura** (nada foi calculado ainda): `plano_execucao_opus.md` inteiro (755 linhas, em chamadas com `offset`, sem truncamento), `CLAUDE.md`, `docs/briefing.md`, `docs/SCOPE.md`, `docs/DATA_QUALITY.md`, `process-log/01_bloco-1.md` e `02_bloco-2.md`, `PROMPTS.md` (bloco 3), `solution/app/data-contract.md` (para os nomes de colunas que o `build.py` vai consumir) e `scorer/{config,fmt,clean,facts}.py`, `tests/test_clean.py`.
2. **Este log, seções "Planejamento" e "Checagem de vazamento"**, antes de qualquer código. Ordem de criação medida no sistema de arquivos (`CreationTime`): `03_bloco-3.md` às 16:08:05; `features.py` às 16:08:22. Os horários de `score.py`, `explain.py` e dos testes são posteriores e foram regravados por edições; só o de `features.py` é evidência limpa de ordem, e `score.py`/`explain.py` foram escritos depois dele.
3. **Código** (`solution/scorer/`): `features.py` (102 linhas), `score.py` (297), `explain.py` (152). Acrescentei `CATEGORIES` ao `config.py` (nenhuma constante existente foi alterada).
4. **Testes** (`solution/tests/`): `test_features.py` (18), `test_score.py` (28), `test_explain.py` (10).
5. **Fumaça** (scripts no scratchpad, fora da submissão): contagem de linhas de treino por corte, ajuste por corte, explicações de exemplo, forma da curva observada. Os números abaixo que não vêm de `python -m scorer.score` vêm do comando da seção "Q3".
6. **Sabotagens** (cópias do pacote no scratchpad; nenhuma alteração na submissão): estraguei uma guarda por vez e rodei `test_features.py` e `test_score.py` para ver se os testes acusam. Resultado em "Os testes pegam o vazamento?".

Comandos de verificação (cwd `$SOL`):

```
& $PY -B -m pytest -p no:cacheprovider tests/test_features.py tests/test_score.py tests/test_explain.py tests/test_clean.py
& $PY -B -m pytest -p no:cacheprovider
& $PY -B -c "from scorer.score import *"
& $PY -B -m scorer.score
```

### Resultados

#### Testes

| Comando | Saída |
|---|---|
| 4 arquivos pedidos (`test_features`, `test_score`, `test_explain`, `test_clean`) | `68 passed in 26.27s`, exit 0 (18 + 28 + 10 + 12) |
| `pytest` completo | `128 passed in 26.80s`, exit 0 (inclui o `test_validate.py` que o outro executor estava escrevendo; passou no momento em que rodei) |
| `from scorer.score import *` | exit 0; exporta `AgeCurve, FitConfig, LogisticFit, ScoreModel, age_design, fit_age_curve, fit_logistic, fit_model, limpe_limit, order_for_list, score_deals, score_from_ev` |
| `gitw.py status` | "FORA da pasta da submissão: nada"; 1 arquivo não preparado: `config.py` (a constante `CATEGORIES`) |

#### Parâmetros da curva por corte e hoje (`& $PY -B -m scorer.score`) contra o protótipo do planejador

| Corte | Joelho k (protótipo) | Chance de deal novo | Inclinação por 30 dias | Meia-vida (dias depois do joelho) | Limite de Limpe | Fotos | Linhas (protótipo) | Taxa base |
|---|---|---|---|---|---|---|---|---|
| 30/06/2017 | 70 (70) | 49,0% | −4,71 | 6,9 | 138 | 1 | 1.330 (1.330) | 45,8% |
| 31/07/2017 | 100 (100) | 46,9% | −5,60 | 5,7 | 138 | 2 | 2.948 (2.948) | 45,0% |
| 31/08/2017 | 95 (95) | 46,0% | −1,72 | 18,3 | 138 | 3 | 4.483 (4.483) | 43,3% |
| 30/09/2017 | 90 (90) | 45,6% | −1,96 | 16,0 | 138 | 4 | 6.169 (6.169) | 41,2% |
| **31/12/2017 (hoje)** | **95 (95)** | **39,9%** (b0 = −0,4102; protótipo ≈ −0,41) | **−2,59** (−2,5923; protótipo ≈ −2,59) | **11,3** | **138 (138)** | **7 (7)** | **13.100 (13.100)** | 33,2% |

Todos os valores batem com o protótipo: nenhuma divergência acima da tolerância (joelho ±5, contagens ±2%); as linhas de treino são idênticas, o que confirma a regra "só fotos com S + 90 ≤ T". Nos cinco ajustes o gradiente final é praticamente zero (no máximo 5e-05 em módulo), então o otimizador convergiu. A verossimilhança perto do melhor joelho é achatada: os joelhos vizinhos (±5 dias) custam de 0,6 a 6,9 unidades de NLL (por exemplo, em 31/08, o joelho 100 perde só 0,56 para o 95). O joelho é identificado com margem de uns 5 a 10 dias, não ao dia.

#### Listas hoje, 31/12/2017 (`& $PY -B -m scorer.score`; protótipo: Foque 126, Reative 172, Limpe 1.291, Qualifique 500)

| Lista | Deals | Valor de tabela | Valor esperado |
|---|---|---|---|
| Foque (idade ≤ 95) | 126 | US$ 300.790 | US$ 119.977 |
| Reative (96 a 138 dias) | 172 | US$ 392.775 | US$ 45.854 |
| Limpe (> 138 dias) | 1.291 | US$ 3.198.664 | US$ 5.717 |
| Qualifique (Prospecting) | 500 | US$ 1.073.986 | — (sem score) |

Contagens e valor de tabela do Limpe idênticos ao protótipo e ao `facts.json` (1.291; US$ 3.198.664). Score: Foque de 11 a 100 (mediana 49), Reative de 1 a 72 (mediana 26), Limpe de 0 a 33 (mediana 0). No topo do Foque, o deal de GTK 500 (US$ 26.768, 95 dias, score 100) e depois uma sequência de GTX Plus Pro (EV de US$ 2.187, score 75), desempatados por "faltam menos dias até o joelho", como manda o `order_for_list`. O Foque tem 89 deals sem conta e o Reative 120; o aviso de higiene aparece neles e o score não muda.

#### Q3 do bloco 1: a chance é mesmo "estável enquanto o deal é jovem"?

A pergunta ficou aberta no bloco 1 (a justificativa do plano não bate com as fotos do briefing). O que a curva e os dados mostram, com `H = 90` e as 7 fotos de hoje:

```
@'
import pandas as pd
from scorer import clean, features
d = clean.load_deals(); T = "2017-12-31"
tr = features.training_set(features.as_of(d, T), T)
tr["faixa15"] = pd.cut(tr.age_days, list(range(0, 181, 15)) + [10000], right=False)
print(tr.groupby("faixa15", observed=True).y.agg(["size", "mean"]).round(3).to_string())
tr["faixa30"] = pd.cut(tr.age_days, [-1, 30, 60, 90, 120, 10000])
tr["foto"] = tr.snapshot_date.dt.strftime("%Y-%m-%d")
print(tr.pivot_table(index="foto", columns="faixa30", values="y", aggfunc="mean", observed=True).round(2).to_string())
'@ | & $PY -B -
```

Taxa de ganho em 90 dias, **fotos agrupadas**, por faixa de idade de 15 dias:

| Idade | 0–14 | 15–29 | 30–44 | 45–59 | 60–74 | 75–89 | 90–104 | 105–119 | 120–134 | 135–149 | 150 ou mais |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Casos | 2.514 | 1.762 | 1.888 | 1.541 | 1.501 | 906 | 652 | 452 | 311 | 304 | 1.269 |
| Ganhos | 37,5% | 43,9% | 39,3% | 44,8% | 35,5% | 39,7% | 33,1% | 15,0% | 5,8% | 0,3% | 0,0% |

Por foto, em faixas de 30 dias (idade 0–30 / 31–60 / 61–90 / 91–120):

| Foto | 0–30 | 31–60 | 61–90 | 91–120 |
|---|---|---|---|---|
| 31/03 | 49% | 48% | 38% | 0% |
| 30/04 | 38% | 51% | 49% | 38% |
| 31/05 | 39% | 44% | 48% | 42% |
| **30/06** | **51%** | **44%** | **22%** | 0% |
| 31/07 | 24% | 54% | 46% | 23% |
| 31/08 | 29% | 21% | 52% | 32% |
| **30/09** | **48%** | **34%** | **7%** | 0% |

**Resposta.**

- **No agregado, o plano estava certo.** De 0 a 89 dias a taxa fica entre 35,5% e 44,8%, sem tendência, e só cai depois de uns 95 dias (33,1% em 90–104, 15,0% em 105–119, 5,8% em 120–134, 0,3% em 135–149). A curva ajustada reproduz esse desenho: joelho 95, chance de deal novo 39,9% (a taxa observada de 0 a 89 dias é de 40,0% nos mesmos dados) e meia-vida de 11,3 dias (a taxa observada cai de 33,1% para 15,0% em 15 dias). Em verossimilhança, o joelho em 95 supera por 302 unidades de NLL uma queda linear desde o dia zero (joelho 0: 7.787 contra 7.484) e por 839 unidades o modelo sem idade (taxa constante: 8.323).
- **Por foto, o briefing também estava certo.** Em 30/06 e 30/09 (fins de trimestre) a taxa cai cedo, de 51% para 22% e de 48% para 7% entre as faixas de 0–30 e 61–90, o mesmo desenho do briefing. Nas fotos de 31/07 e 31/08 os deals novos (até 30 dias) ganham menos (24% e 29%) do que os de 31 a 90 dias. A estabilidade é uma média de padrões opostos que dependem da posição da foto no trimestre (o artefato do gerador descrito no DATA_QUALITY, seção 2), e **não** uma propriedade de cada data.
- **Efeito no desenho.** Dentro do platô a chance é a mesma para todo deal, então no Foque o valor esperado ordena pelo preço (os desempates saem pelos dias até o joelho). A decisão de ordenar por valor esperado (Q3) continua, mas a justificativa passa a ser "a curva é plana até o joelho", e não "a chance é estável em cada data". O SCORING deve dizer isso.
- **Limitação a levar ao 3b.** Hoje (31/12/2017) é um fim de trimestre, e a curva diz 40% para todo Foque. Dos 126 deals do Foque, 69 têm mais de 60 dias (53 de 61 a 90 e 16 de 91 a 95), a faixa em que as fotos de fim de trimestre (30/06 e 30/09) mostram 22% e 7%. O backtest dos cortes de 30/06 e 30/09 vai medir quanto isso custa.

#### Os testes pegam o vazamento? (sabotagens, em cópias do pacote no scratchpad)

Estraguei uma guarda por vez e rodei `test_features.py` e `test_score.py`. Todas as sabotagens foram detectadas:

| Sabotagem | Testes que falharam | Observação |
|---|---|---|
| S1. `as_of` não esconde o desfecho depois de T | 9 | inclui as três execuções da mutação do futuro e o controle |
| S2. treino sem a regra S + H ≤ T (e sem os `assert`) | 6 | a mutação do futuro **não** acusa: com `as_of` o rótulo vira "não ganho" (censura), que enviesa o modelo mas não vaza. Quem acusa são os testes de horizonte e de tamanho do treino |
| S3. limite de Limpe tirado do maior ciclo de todos os ganhos | 6 | a mutação acusa (o limite sobe de 138 para outro valor) |
| S4. conta ausente reduz a chance pela metade | 4 | mutação do futuro (3) e `test_account_columns_do_not_change_the_model_or_scores` |
| S5. o vendedor muda a chance | 4 | permutação de `sales_agent` (2) e testes de escala |
| S6. preço mínimo tirado só de deals fechados depois de T | 2 | testes do catálogo |

A sabotagem S2 mostra que as duas guardas do rótulo (`as_of` e S + H ≤ T) são independentes: o horizonte sozinho impede que o rótulo veja depois de T, e o `as_of` impede que o limite de Limpe, os deals abertos e as colunas derivadas vejam o futuro.

### Autoverificação do checkpoint

- [x] `pytest` dos 4 arquivos pedidos: exit 0, 68 testes.
- [x] `03_bloco-3.md` tem "Planejamento (Opus)" e "Checagem de vazamento", escritas antes de `features.py` (16:08:05 contra 16:08:22).
- [x] `from scorer.score import *` funciona.
- [x] `gitw.py status`: nada fora da pasta da submissão.
- [x] Números contra o protótipo: nenhuma divergência acima da tolerância.
- [x] Cada risco da tabela de vazamento tem teste com o nome que a tabela cita (conferido por `Grep` nos arquivos de teste).
- [x] O vendedor não entra em nenhuma função de score: `test_permuting_sales_agent_changes_no_score` (T = 30/06 e 31/12) e `test_training_set_has_no_seller_columns`.
- [x] Frases de explicação: de 2 a 4, até 160 caracteres, sem as palavras `nan`, `logit`, `probabilidade`, `coeficiente`, para os 2.089 deals de hoje; o nome do vendedor nunca aparece.

### O que deu errado / iterações

Erros e testes que falharam de verdade, com antes e depois:

1. **`score` saía com dtype `object` (código).** Na primeira fumaça (`python -m scorer.score` ainda não existia; foi o script do scratchpad), o `dtypes` mostrou `score`, `days_to_knot` e `days_to_limpe` como `object` depois de juntar os Qualifique, porque `pd.NA` escalar atribuído a uma coluna cria `object`. Antes: `object`; depois: `Int64` por conversão explícita (`NULLABLE_INT_COLUMNS`) no fim de `score_deals`. Coberto por `test_score_is_integer_in_range_...` (`dtype == "Int64"`).
2. **KeyError no teste do treino (fixture).** O primeiro `pytest` de `test_features.py` falhou em `test_training_set_labels_on_a_toy_example`: `KeyError: ['regional_office', 'sector', 'employees'] not in index`. A base de brinquedo não tinha as colunas de diagnóstico que `training_set` devolve. Era erro da fixture, não do código. Corrigi o brinquedo (`attributes`). Depois: 18 passaram.
3. **Teste do limite de Limpe comparava o modelo inteiro (teste).** `test_limpe_limit_comes_from_wins_closed_up_to_T` falhou com `train_rows=1331 != 1330`: o ganho sintético que acrescentei (engajado em janeiro, fechado em agosto) é um deal aberto em 30/06 e vira uma linha de treino a mais. O limite de Limpe não mudou; quem mudou foi a curva, por ter uma linha a mais. Comparar só `limpe_after_days`, que é o que o teste quer provar.
4. **Ordem esperada errada no teste de Limpe (teste).** `ids[5:8]` esperava `["D007","D006","D005"]`; o código devolveu `["D007","D005","D006"]`. O código estava certo: dentro do mesmo preço (US$ 3.393), vem primeiro o deal mais velho (300 dias, `D005`). Corrigi a expectativa.
5. **"0%" dentro de "40%" (teste).** `test_a_chance_that_rounds_to_zero_...` afirmava `"0%" not in frase`, e a frase tem "40%". Troquei por `"para 0%" not in frase`.
6. **Primeira versão do teste de "modelo sem `as_of` vaza" não provava nada.** Eu havia escrito `test_a_model_fitted_without_as_of_would_leak` comparando contagens de ganhos que já eram diferentes por construção. Ao raciocinar sobre o que o teste exercitava, vi que ele passaria mesmo com a guarda quebrada. Troquei por `test_naive_choices_would_leak_and_the_mutation_exposes_them`, que mostra que o limite de Limpe do arquivo inteiro e o rótulo de uma foto com horizonte além de T **mudam** com o futuro mutado, e que o modelo do código não muda. As sabotagens S1 a S6 vieram dessa dúvida: quis ver os testes falharem de verdade.
7. **Teste de piso do limite de Limpe confuso.** A primeira versão misturava um `ScoreModel` à mão com um `max()` solto no próprio teste. Extraí `limpe_limit(won_cycles, knot)` (função pura de 1 linha) e passei a testá-la direto.
8. **Script do scratchpad com nome de módulo da biblioteca padrão.** Salvei um script como `numbers.py`; o interpretador o carregou no lugar do módulo `numbers` e o `import numpy` quebrou (`partially initialized module 'numpy'`). Sem efeito na submissão. Renomeei para `collect_numbers.py` e apaguei o `__pycache__` do scratchpad.
9. **Pequenas limpezas feitas antes dos testes finais:** import não usado de `pandas` e parâmetro `model` sem uso em `_value_sentence` (explain); import `round_half_up` sem uso (score).
10. **Nenhum erro de pandas 3 ou de scipy:** sem avisos de depreciação nas execuções. A atribuição por `.loc` com dtype `str` e datas `datetime64[us]` funcionou na mutação do futuro.

### Decisões (todas "decisão autônoma do Claude")

Linhas para o orquestrador consolidar em `docs/DECISIONS.md` (formato `| data | decisão | alternativa descartada | motivo |`):

```
| 2026-10-25 | Bloco 3 — Checagem de vazamento escrita antes do código (11 riscos, cada um com guarda e teste) e teste de mutação do futuro como prova central (decisão autônoma do Claude) | Revisar o código e conferir só o horizonte S+H ≤ T | A mutação embaralha tudo o que acontece depois de T e exige modelo e scores idênticos. Das 6 sabotagens, todas foram pegas (2 a 9 testes cada); a sabotagem sem a regra S+H ≤ T não foi pega pela mutação, só pelos testes de horizonte, por isso as duas guardas existem |
| 2026-10-25 | Bloco 3 — Curva de chance "platô + queda" com inclinação ≤ 0 e joelho numa grade de 5 em 5 dias (menor NLL; empate: menor joelho) (decisão autônoma do Claude) | Logística segmentada sem restrição (protótipo: sobe com a idade); queda linear desde o dia zero | Hoje: joelho 95, chance de deal novo 39,9%, meia-vida 11,3 dias. NLL 7.484 contra 7.787 (linear) e 8.323 (sem idade). Joelho identificado com margem de 5 a 10 dias (os vizinhos a ±5 dias custam de 0,6 a 6,9 de NLL) |
| 2026-10-25 | Bloco 3 — Limite de Limpe = maior ciclo entre os ganhos fechados até T, nunca menor que o joelho (decisão autônoma do Claude) | Fixar 138 dias no código | 138 em todos os cortes e hoje; derivado por corte, nunca do arquivo inteiro (sabotagem S3 falha 6 testes) |
| 2026-10-25 | Bloco 3 — Score 0 a 100 em escala logarítmica do valor esperado, entre o deal novo mais barato e o mais caro (decisão autônoma do Claude) | Escala linear do valor esperado | Preços vão de US$ 55 a US$ 26.768 (razão 487). Hoje, no Foque e Reative (298 deals), 220 teriam score ≤ 5 na escala linear (mediana 2) contra 30 na logarítmica (mediana 39) |
| 2026-10-25 | Bloco 3 — Preço mínimo e máximo do catálogo tirados de `sales_price` dos deals, não lidos de `products.csv` dentro de `fit_model` (decisão autônoma do Claude) | Ler o catálogo dentro da função de ajuste | Cada produto tem um único preço (teste) e os extremos são US$ 55 e US$ 26.768, iguais aos do catálogo (teste contra `products.csv`); a função fica pura e sem acesso a disco |
| 2026-10-25 | Bloco 3 — Q3 (bloco 1) respondida: a chance é plana até o joelho no agregado das fotos, mas cai cedo nas fotos de fim de trimestre; ordenação do Foque por valor esperado mantida com a justificativa trocada (decisão autônoma do Claude) | Afirmar que a chance é estável em cada data | Agregado: 35,5% a 44,8% de 0 a 89 dias, 15,0% em 105–119. Em 30/06 e 30/09: 51% para 22% e 48% para 7% entre 0–30 e 61–90 dias. Hoje, 69 dos 126 deals do Foque têm mais de 60 dias |
| 2026-10-25 | Bloco 3 — Explicação do Qualifique sem conta diz "isso não muda a ordem da lista" (nas outras listas, "isso não muda o score") (decisão autônoma do Claude) | Usar a mesma frase nas quatro listas | Qualifique não tem score; a frase "não muda o score" soaria estranha ao lado de "Sem score" |
| 2026-10-25 | Bloco 3 — `score_deals` recusa modelo ajustado depois de T e recusa Prospecting antes do fim dos dados; `open_at` recusa foto depois do `as_of` da visão (decisão autônoma do Claude) | Confiar na disciplina de quem chama | Transformam vazamento acidental em erro: Prospecting no passado não é reconstruível (500 deals sem `engage_date`) |
```

Escolhas de código sem linha própria:

- `fit_logistic` devolve `LogisticFit(coef, nll)` (o plano não dizia o retorno); a E5 usa `coef` e `nll` no teste de atributos.
- `AgeCurve.train_snapshots` é uma tupla de datas ISO (não um inteiro): serve ao "7 fotos, de 31/03/2017 a 30/09/2017" do `how_it_works`; `len()` dá a contagem.
- `ScoreModel` ganhou o campo `horizon_days` (o texto das explicações cita "90 dias").
- `FitConfig(horizon_days, first_snapshot, knot_grid)` é o `cfg` de `fit_model`; a sensibilidade de 28/02 é `FitConfig(first_snapshot="2017-02-28")`.
- `score_deals` devolve `score`, `days_to_knot`, `days_to_limpe` e `age_days` como `Int64` (nulo no Qualifique) e as demais colunas de entrada intactas, mais `p_win`, `expected_value`, `category`. As colunas já têm os nomes que o `data-contract.md` espera depois de um renome simples (`p_win`→`p`, `expected_value`→`ev`, `category`→`cat`, `age_days`→`age`).
- `as_of` descarta e recalcula `age_days`, `cycle_days` e `is_open` (o plano só dizia ajustar estágio e datas), porque essas colunas do `deals.csv` usam 31/12/2017 e carregam o futuro (risco 10).
- `how_it_works(model, headline_metrics)` já implementa a linha 5 completa: `headline_metrics` é um dict com `n_cortes`, `receita_score`, `receita_valor` e `receita_recencia` (frações da média dos cortes). Sem ele, a linha diz "O teste no passado ainda não foi rodado". Isso adianta um pedaço da E5; só falta passar o dict.
- `python -m scorer.score` imprime a tabela de parâmetros por corte e a contagem das listas (reproduz os números deste log).
- `config.CATEGORIES = ("Foque", "Reative", "Limpe", "Qualifique")` foi a única constante acrescentada.

### Pendências para a 3b (E5) e para o orquestrador

- **Consolidar** as oito linhas acima em `docs/DECISIONS.md` (não toquei no arquivo).
- **Consumo pela E5.** `features.as_of(deals, T)`, `features.open_at(view, S)`, `features.training_set(view, T, H, first_snapshot)`, `score.fit_model(deals, T, cfg=None)`, `score.score_deals(deals, T, model, include_prospecting=False)` e `AgeCurve.p_win(age)` (aceita escalar ou array). O modelo para a auditoria "VAZADO" (modelo ajustado em 31/12/2017 e avaliado num corte) é `fit_model(deals, "2017-12-31")` aplicado com `curve.p_win` às idades do corte; `score_deals` recusa essa combinação de propósito (modelo posterior a T). Para o teste de atributos use `fit_logistic(X, y, l2=1.0, bounds=...)`, com o joelho fixo em `model.knot_days` e a coluna de idade `np.maximum(0, age - k) / 30` (`score.age_design(age, knot)` monta a matriz com o intercepto).
- **Hoje é fim de trimestre.** A curva diz 40% para todo o Foque, mas 69 dos 126 têm mais de 60 dias, e em 30/06 e 30/09 essa faixa teve 22% e 7%. O SCORING precisa dizer isso, e o backtest dos cortes 30/06 e 30/09 vai mostrar o custo. Não exploro a posição no trimestre (decisão 6 do bloco 2: artefatos do gerador não são explorados).
- **Joelho pouco identificado.** Os vizinhos a ±5 dias custam de 0,6 a 6,9 unidades de NLL (em 31/08, o 100 perde só 0,56 para o 95). A sensibilidade a esse passo (grade de 5 dias) pode entrar no SCORING.
- **Linha 5 do `how_it_works`:** já pronta; a E5 só precisa montar o dict a partir da média dos cortes.
- **`limpe_after_days` é 138 em todos os cortes e hoje.** Se o teto de 138 dias é artefato do gerador (documentado), o Limpe herda esse artefato; o SCORING deve repetir a ressalva.
- **Testes de números (`test_docs_numbers`)** não foram tocados: nenhum doc novo cobre números da 3a. O `SCORING.md` entra na E5.
- **Commit:** nenhum (o bloco 3 é commitado depois da E5). Os arquivos novos de `scorer/` e `tests/` ficam ignorados pelo `.gitignore` do repositório e precisam de `git add -f`, que o `gitw.py` já faz.

## Parte 3a.2 — primitivas de métrica (executor paralelo)

As primitivas de métrica de `scorer/validate.py` (`auc`, `top_share`, `random_baseline`, `bootstrap_diff`, `brier`, `log_loss`, `beats`) e o `tests/test_validate.py` foram escritos por outro executor, Claude Sonnet, em paralelo à 3a. Resumo do que ele registrou:

- **32 testes** de brinquedo, com resultados conferidos à mão.
- **Erro real evitado em `beats`.** Em ponto flutuante, `0,61 − 0,60` vale `0,010000000000000009`, que é maior que `0,01`: um empate de exatamente 1 ponto percentual contaria como vitória. Correção: `score − v − tie_tol > 1e-12`.
- **Um teste mal escrito, e não o código.** `test_bootstrap_diff_detects_clearly_better_method` falhou com `ci_low` de 0,35 contra o esperado acima de 0,5, porque o oráculo do teste ordenava só por `y` (acerto) e a métrica é de receita. O teste foi trocado por um oráculo que ordena pela receita; o código não mudou.

## Parte 3b — backtest, critério pré-registrado e SCORING.md (E5)

### Executor

Claude Sonnet (subagente executor). Execução da especificação E5 de `process-log/plano_execucao_opus.md`. Ninguém respondeu perguntas; as decisões marcadas "(decisão autônoma do Claude)" são do executor.

### Pré-registro: critério "bater os baselines" (escrito antes de rodar o backtest completo)

**Ordem real do trabalho.** Esta seção foi escrita em 25/10/2026 às 16:28 (relógio do sistema, `Get-Date`), depois de ler a especificação, o log da 3a e o código existente, e **antes** de existir `evaluate_cut`/`run_backtest`: no momento em que escrevo, `scorer/validate.py` só tem as primitivas de métrica, e `data/processed/backtest_metrics.json` não existe. O `pytest` completo (128 testes) passou antes de escrever esta seção. Não rodei nenhuma conta de desempenho (AUC ou receita no top 20%) dos métodos nos cortes.

**Limites do pré-registro (para não vender como cego).** O critério e a métrica primária já estavam no `docs/SCOPE.md` (bloco 1, escrito antes do código de avaliação) e no plano. Mesmo assim, o planejador (Opus) rodou um protótipo e o plano traz os valores esperados (receita no top 20%: score 0,58 a 0,65, valor 0,47 a 0,49, recência 0,13 a 0,47; AUC da recência 0,58 a 0,83). Logo o critério não foi fixado às cegas: sabíamos que o score tendia a passar. O que o pré-registro garante é que a regra, o desempate e o ajuste único não mudam depois de ver o resultado.

**Regra (copiada do plano, E5 item 5):**

1. **Métrica primária:** receita capturada no top 20% (fração do `close_value` dos Won capturada pelos 20% de maior score, por contagem, com empates tratados pelo valor esperado sob desempate aleatório).
2. **O score vence se**, em **cada um dos 4 cortes** (30/06, 31/07, 31/08 e 30/09/2017), a sua receita no top 20% for maior que a de **valor** (ordenar pelo preço de tabela), maior que a de **recência** (os mais novos primeiro), e maior que a **média** e o **percentil 95** dos 200 sorteios aleatórios (sementes 0 a 199).
3. **Empate:** diferença menor ou igual a 0,01 (1 ponto percentual) conta como empate, e empate não bate. A comparação usa `validate.beats`.
4. **Não decidem** (são reportados): AUC, captura de ganhos no top 20% e Brier.
5. **Ajuste único, pré-definido, só se o critério falhar:** trocar a curva "platô + queda" por faixas de 15 dias de idade, com taxa por faixa suavizada por pseudo-contagem α = 20 rumo à taxa média de treino, forçada a não crescer com PAVA (pesos = n + α) e interpolada linearmente entre os pontos médios das faixas. Mesma janela, mesmo H = 90, mesma métrica, nada mais muda. Roda-se de novo uma vez.
6. **Se ainda falhar:** mantém-se o modelo de melhor média na métrica primária e documenta-se a falha com números. Sem novas tentativas, sem trocar de métrica.
7. **Corrigir bug** (código que não faz o que o SCORING descreve) não conta como ajuste, mas é logado com antes e depois.

**Regra pré-registrada para os atributos** (um por vez, sobre o modelo de idade, com o joelho fixo no valor da curva só de idade; one-hot com categoria de referência, L2 = 1,0 nos coeficientes do atributo): o atributo entra **só se** melhorar o log-loss em `y_H` em **todos** os cortes **e** não piorar a receita no top 20% (P_attr × preço) em nenhum. Produto e região usam todos os deals; setor e porte (tercil de `employees` na tabela de contas) só o subconjunto com conta, no treino e na avaliação, comparado com a curva só de idade ajustada no mesmo subconjunto. O vendedor **não** é testado (decisão 4). Esperado: nenhum entra.

**Interrupção (fato registrado).** A execução da 3b foi interrompida por limite de uso da API depois de gravar esta seção de pré-registro e o rascunho de `docs/SCORING.md` (1,8 KB, só a seção 9). O último arquivo gravado foi às 16:28; a retomada foi às 19:01 (relógio do sistema), por mensagem do coordenador. Ao retomar, conferi o estado real: `validate.py` ainda só tinha as primitivas (7.229 bytes, sem `evaluate_cut`), `backtest_metrics.json` e `backtest_tables.md` não existiam, `docs.py`, `config.py`, `explain.py` e os testes estavam como antes. Portanto **nenhum resultado de backtest foi visto antes da retomada**, e o pré-registro continua anterior ao primeiro número de desempenho.

**Detalhes de implementação fixados antes de rodar (ainda sem resultado):** (a) "piorar a receita" no teste de atributos significa Δ < −1e-12 (qualquer queda real); (b) o L2 = 1,0 vale só para os coeficientes do atributo, e não para a inclinação da idade, por isso o ajuste com máscara de penalização fica em `validate.py` (o `fit_logistic` penaliza todos os coeficientes menos o intercepto) e é testado contra o `fit_logistic` no caso em que as penalizações coincidem; (c) tercis de porte calculados sobre as 85 contas (uma linha por conta); (d) categoria de referência = a mais frequente no treino.

**Desenho do desfecho no backtest (também fixado agora):** população = Engaging abertos em T (`open_at(as_of(T), T)`), incluindo zumbis; `y` = Won até 31/12/2017; `gain` = `close_value` dos Won; `y_H` = Won com `close_date` ≤ T + 90 dias (usado só no Brier e no log-loss). Deals ainda abertos em 31/12/2017 contam como "não ganho" (censura à direita); a sensibilidade "só resolvidos" mostra o efeito.

### O que foi feito (comandos), em ordem

1. **Retomada às 19:01** (após a interrupção descrita acima): conferi o estado real dos arquivos (`Get-Item` com tamanho e horário) antes de continuar.
2. **`config.py`** (só acréscimos): `CRITERION_TIE_TOL`, `ADJUST_BIN_DAYS`, `ADJUST_PSEUDO_COUNT`, `ATTRIBUTE_L2`, `FOQUE_AGE_BANDS`, `BACKTEST_TABLES_MD`, `SCORING.md` em `COVERED_DOCS` e `RANDOM_SEEDS - 1` (199) em `ALLOWED_CONSTANTS`.
3. **`validate.py`** (extensão): `evaluate_cut`, `check_criterion`, `pava_nonincreasing`, `fit_binned_curve` (o ajuste único, não rodado), `fit_logistic_masked`, teste de atributos, auditorias, `run_backtest`, `write_tables`, `main`. Escrito **antes** da primeira execução do backtest.
4. **`docs.py`**: 12 blocos `scoring-*` (`criterio`, `backtest`, `media`, `categorias`, `calibracao`, `bootstrap`, `foque-idade`, `sensibilidade`, `auditoria`, `atributos`, `modelos`, `hoje`) e o reconhecimento de "pp" / "pontos percentuais" no verificador de números.
5. **Testes**: `test_validate.py` (de 32 para 51) e `test_docs_numbers.py` (um teste novo, sobre "pp").
6. **Primeira execução do backtest completo: `& $PY -B -m scorer.validate`, 19:05:33 a 19:05:42 (9 s).** Resultado: PASSOU na primeira rodada, sem ajuste.
7. **Segunda execução** (mesma tarde): só para acrescentar o diagnóstico `delta_log_loss_treino` aos atributos, depois de ver que a região piorava fora da amostra. O JSON da primeira execução, menos esse campo novo, é idêntico ao da segunda (comparado por programa). O diagnóstico não entra na regra.
8. **`docs/SCORING.md`** reescrito por inteiro (a seção 9 do rascunho de 16:28 foi mantida e ganhou o resultado); `python -m scorer.docs` preenche os blocos AUTO; `docs/DECISIONS.md` recebeu as linhas do Bloco 3.
9. Verificação final (cwd `$SOL`): `scorer.validate` (exit 0), `scorer.docs` (0), `pytest` (168 passaram e 1 foi pulado, em 35 s; exit 0), `scorer.docs --check` (0). O JSON e o `backtest_tables.md` saem com os mesmos bytes numa segunda execução.

### Resultados

Fonte de todos os números abaixo: `solution/data/processed/backtest_metrics.json` e `backtest_tables.md`.

**Tabela principal, copiada de `backtest_tables.md`** (negrito: o melhor entre score, valor, recência e aleatório; aleatório com o intervalo de p5 a p95 de 200 sorteios):

| Corte | Método | AUC | Ganhos capturados no top 20% | Receita capturada no top 20% |
| :--- | :--- | ---: | ---: | ---: |
| 30/06/2017 | Score (valor esperado) | 0,66 | 25,8% | **61,3%** |
| 30/06/2017 | Ordenar por valor | 0,48 | 19,6% | 48,6% |
| 30/06/2017 | Mais recentes primeiro | **0,73** | **29,3%** | 27,7% |
| 30/06/2017 | Aleatório (média de sorteios) | 0,50 (0,47 a 0,52) | 19,9% (18,1% a 21,8%) | 20,0% (16,8% a 23,4%) |
| 30/06/2017 | Só a chance (diagnóstico) | 0,70 | 26,9% | 26,8% |
| 31/07/2017 | Score (valor esperado) | **0,64** | **25,1%** | **57,9%** |
| 31/07/2017 | Ordenar por valor | 0,51 | 20,5% | 48,7% |
| 31/07/2017 | Mais recentes primeiro | 0,58 | 12,2% | 12,8% |
| 31/07/2017 | Aleatório (média de sorteios) | 0,50 (0,48 a 0,52) | 20,0% (18,1% a 22,0%) | 20,1% (17,2% a 23,4%) |
| 31/07/2017 | Só a chance (diagnóstico) | 0,64 | 24,7% | 24,6% |
| 31/08/2017 | Score (valor esperado) | 0,63 | 26,4% | **60,7%** |
| 31/08/2017 | Ordenar por valor | 0,50 | 20,4% | 48,2% |
| 31/08/2017 | Mais recentes primeiro | **0,66** | **34,0%** | 31,6% |
| 31/08/2017 | Aleatório (média de sorteios) | 0,50 (0,48 a 0,52) | 19,9% (18,1% a 22,0%) | 19,8% (16,4% a 23,0%) |
| 31/08/2017 | Só a chance (diagnóstico) | 0,66 | 25,7% | 25,8% |
| 30/09/2017 | Score (valor esperado) | 0,65 | 27,9% | **64,8%** |
| 30/09/2017 | Ordenar por valor | 0,48 | 19,4% | 47,1% |
| 30/09/2017 | Mais recentes primeiro | **0,83** | **43,6%** | 46,8% |
| 30/09/2017 | Aleatório (média de sorteios) | 0,50 (0,48 a 0,53) | 20,2% (17,5% a 22,5%) | 20,3% (16,1% a 24,4%) |
| 30/09/2017 | Só a chance (diagnóstico) | 0,70 | 28,6% | 28,6% |

**Média dos 4 cortes:**

| Método | AUC | Ganhos capturados no top 20% | Receita capturada no top 20% |
| :--- | ---: | ---: | ---: |
| Score (valor esperado) | 0,64 | 26,3% | 61,1% |
| Ordenar por valor | 0,49 | 20,0% | 48,1% |
| Mais recentes primeiro | 0,70 | 29,8% | 29,7% |
| Aleatório (média de sorteios) | 0,50 | 20,0% | 20,0% |
| Só a chance (diagnóstico) | 0,67 | 26,5% | 26,5% |

**Valores contra o protótipo do planejador** (receita no top 20%: score / valor / recência; AUC do score e da recência): 30/06 ≈ 0,61 / 0,49 / 0,28 (obtido 0,613 / 0,486 / 0,277; AUC 0,66 e 0,73); 31/07 ≈ 0,58 / 0,49 / 0,13 (0,579 / 0,487 / 0,128; AUC 0,64 e 0,58); 31/08 ≈ 0,61 / 0,48 / 0,32 (0,607 / 0,482 / 0,316; AUC 0,63 e 0,66); 30/09 ≈ 0,65 / 0,47 / 0,47 (0,648 / 0,471 / 0,468; AUC 0,65 e 0,83). Nenhuma divergência. Aleatório ≈ 0,20 em todos. Limpe com 0% de ganhos nos quatro cortes; Foque entre 33,2% e 48,5% (`cuts[].categorias`).

**Critério pré-registrado: PASSOU, sem ajuste.** O score vence valor, recência e a média e o p95 do aleatório nos 4 cortes; a menor margem sobre o melhor baseline é de 9,2 pontos percentuais (31/07), a maior 17,7 (30/09). Bootstrap: diferença score menos valor de +9,2 a +17,7 pontos percentuais e score menos recência de +17,9 a +45,1, com IC de 2,5% a 97,5% fora de zero nos 8 casos. Brier da chance 0,185 contra 0,226 da constante na média (log-loss 0,524 contra 0,644). O ajuste único (faixas de 15 dias e PAVA) foi implementado e testado em toy data, **mas não foi rodado nos dados reais**: a regra só o autoriza se o critério falhar.

**Onde a recência ganha (sem rodeio).** AUC e captura de ganhos em 30/06, 31/08 e 30/09 (AUC 0,83 contra 0,65 em 30/09). O score só ganha em AUC e captura no corte de 31/07. A recência desaba em 31/07 (12,8% da receita, abaixo do sorteio): os deals de até 30 dias, engajados em julho, ganharam 24,3% nos 90 dias seguintes, contra 53,8% dos de 31 a 60 dias.

**Antecipação do plano que falhou.** O plano dizia que a chance sozinha nunca ordenaria melhor que a recência. Em 31/07 a AUC da chance sozinha é 0,64 contra 0,58 da recência (o empate no platô vale 0,5, melhor que uma ordem anti-informativa).

**Atributos testados e descartados (regra pré-registrada).** Nenhum entra:

| Atributo | Subconjunto | Δ log-loss (30/06, 31/07, 31/08, 30/09) | Δ receita top 20% (mesmos cortes) | Entra? |
|---|---|---|---|---|
| produto | todos | +0,0060, +0,0017, −0,0003, +0,0007 | −0,5, +0,2, −0,3, −0,1 pp | não |
| região | todos | −0,0158, +0,0321, +0,0596, +0,0645 | +2,5, −4,7, −4,2, −6,1 pp | não |
| setor | só com conta | +0,0061, +0,0039, +0,0029, +0,0028 | −0,8, −0,8, +0,2, −0,3 pp | não |
| porte (tercil) | só com conta | −0,0007, −0,0004, −0,0001, +0,0004 | +1,3, +0,8, +0,0, −0,1 pp | não |

Diagnóstico no treino (não decide): o Δ log-loss dentro da amostra é negativo (melhora) para os quatro atributos nos quatro cortes; o da região vai de −0,0191 a −0,0305. Região: no treino do corte de 30/09, entre os deals com idade até o joelho, o Central ganhava 62,8% contra 42,7% (East) e 35,5% (West); fora da amostra, 26,7% contra 36,6% e 37,0%. Contagem feita num script de depuração no scratchpad (fora da submissão), para descartar bug no código do atributo.

**Auditoria (perguntas respondidas com números).**

- *Modelo VAZADO* (ajustado até 31/12/2017, avaliado em cada corte; rotulado, nunca reportado como resultado): receita vazada menos honesta de −3,6 (30/06), −0,3, −0,2 e −0,4 pontos percentuais; AUC vazada 0,59, 0,63, 0,64 e 0,66 (honesta 0,66, 0,64, 0,63 e 0,65). O vazamento de parâmetros não infla o score, porque ele só usa a idade (joelho vazado de 95 dias em todos os cortes). Isso não prova ausência de vazamento; a proteção está nos testes da 3a.
- *`has_account` sozinho:* AUC de 0,72, 0,75, 0,79 e 0,77, acima da do score nos quatro cortes (0,63 a 0,66). Zero ganhos entre os sem conta (484, 760, 934 e 1.008 deals) e 39,9% a 50,7% de ganhos entre os com conta. Mostra por que é proibido.
- *Primeira foto em 28/02:* o critério passaria; receita média do score 59,0%; só o corte de 30/06 muda (joelho de 70 para 125 dias, −7,4 pontos percentuais, 2.515 linhas contra 1.330).
- *Só resolvidos:* receita no top 20% de score / valor / recência: 49,7 / 49,9 / 17,7 (30/06), 48,5 / 48,8 / 19,9 (31/07), 48,6 / 49,1 / 17,0 (31/08), 48,2 / 48,2 / 19,4 (30/09); AUC dos três em torno de 0,5. O score deixa de ganhar do valor: a vantagem do backtest completo vem de identificar zumbis. Abertos em 31/12 (716, 1.118, 1.372 e 1.474 deals), dos quais podem fechar de fato (idade em 31/12 dentro do limite de Limpe): 0, 0, 81 e 183.

**Achado do Foque (risco levantado na 3a), por corte.** Ganho em 90 dias, deals do Foque com 61 dias ou mais menos os de 0 a 30 dias (IC de 2,5% a 97,5%): 30/06 −17,4 pp (−27,8 a −6,9; 83 deals na faixa); 31/07 +19,2 pp (+14,1 a +24,4); 31/08 +21,3 pp (+15,1 a +27,4); 30/09 −41,3 pp (−45,8 a −36,8; 460 deals). Nos fins de trimestre testados a faixa de 61+ dias do Foque ganha muito menos; hoje (fim de trimestre) são 69 dos 126 do Foque (18 com até 30 dias, 39 de 31 a 60). A curva do modelo, plana, não captura isso. Calibração na faixa de 61 a 90 dias: modelo 32,9% contra 21,6% observado (30/06) e 45,6% contra 6,7% (30/09). Isso entra em "O que não funcionou" e em Limitações no SCORING; o modelo não foi mexido.

**Faixas fixas do briefing (110 / 188 / 1.291) contra aprendidas (126 / 172 / 1.291).** O limite de Limpe aprendido é 138, igual ao do briefing, então o Limpe é o mesmo; o joelho aprendido é 95 e não 90, e 16 deals passam de Reative para Foque (`hoje.faixas_fixas_do_briefing` contra `hoje.categorias`).

### Autoverificação do checkpoint

(O PROMPTS.md mandava mostrar a tabela do backtest ao Rafael e esperar; no modo autônomo o Claude verificou sozinho, com a tabela acima, e registrou aqui.)

- [x] Critério copiado para o SCORING (seção 9) e para este log **antes** do primeiro número de desempenho: log às 16:28, rascunho do SCORING às 16:28:19, primeiro backtest às 19:05:33.
- [x] Resultado declarado sem maquiar: PASSOU na métrica primária; a recência ganha em AUC e captura de ganhos em 3 de 4 cortes; o score não bate o valor entre os resolvidos; o Foque de 61+ dias perde nos fins de trimestre.
- [x] Nenhuma divergência em relação ao protótipo do planejador (tabela acima).
- [x] `beats` usado no critério (`check_criterion`), com empate de até 0,01 não vencendo; teste `test_check_criterion_tie_of_one_point_does_not_win`.
- [x] `backtest_metrics.json` com 4 cortes e `criterion.passed`; `check_criterion` aplicada ao JSON reproduz `passed` (`test_criterion_function_reproduces_the_stored_verdict`).
- [x] Todos os números do SCORING.md vêm do JSON: blocos AUTO (`scorer.docs --check` exit 0) e prosa (`test_prose_numbers_come_from_the_facts[SCORING.md]` passa).
- [x] Determinismo: duas execuções de `scorer.validate` geram o mesmo JSON e o mesmo `backtest_tables.md` (hash igual).
- [x] `gitw.py status`: "FORA da pasta da submissão: nada".

### O que deu errado / iterações (3b)

1. **Interrupção por limite de uso da API** entre 16:28 e 19:01 (registrada acima). Nada se perdeu: o pré-registro e o rascunho do SCORING estavam gravados. Mas um efeito colateral: `docs/SCORING.md` foi reescrito por inteiro, então o `CreationTime` do arquivo final (19:09) não serve de prova da ordem; a prova é o horário do rascunho (16:28:19) medido antes da retomada e o horário deste log.
2. **Quatro testes meus falharam na primeira execução de `test_validate.py` (erros dos testes, não do código):** (a) `NameError: pd` (faltava `import pandas`) em dois testes; (b) `TypeError: _build_cut() got an unexpected keyword argument 'curve_kind'` (o parâmetro se chama `kind`); (c) `test_binned_curve_skips_empty_bins` esperava o ponto médio 105 e o código deu 97,5 (idade 100 cai na faixa de 90 a 104, de ponto médio 97,5; a conta do teste estava errada). Depois: 50 passaram (51 com o teste da linha 5).
3. **Verificador de números acusou o SCORING recém-escrito:** `298` (soma de Foque e Reative, que não é um fato), `199` (última semente), `9,2`, `140`. Correções: tirei o 298 e troquei o 140 por "mais de 138 dias" (um número a menos, e mais correto); `199` entrou em `ALLOWED_CONSTANTS` (é parâmetro de desenho, 0 a 199); `9,2` virou "9,2 pontos percentuais", e o verificador passou a entender "pp" e "pontos percentuais" (fração × 100). O teste novo errou num primeiro rascunho (um "9,25 arredondado" que não é um token válido); retirado.
4. **Afirmações do primeiro rascunho do SCORING que não batiam com a tabela, corrigidas antes de fechar:** "três fotos com 28/02" (são duas), "a recência fica a 0,2 pp do valor em 30/09" (é 0,3: 46,8% contra 47,1%), "a chance sozinha no nível da recência" (26,5% contra 29,7%) e "poucos" abertos que ainda podem fechar (são 81 e 183).
5. **Antecipação do plano falsa** (chance sozinha nunca vence a recência): vence em 31/07 (0,64 contra 0,58). Reportada no SCORING como erro de previsão do plano.
6. **`pytest` completo travou numa execução** (mais de 10 minutos, 609 s de CPU no processo) enquanto o executor da interface editava `tests/test_build.py`. Encerrei o processo, rodei a suíte sem esse arquivo (150 passaram em 30 s) e, depois, o arquivo sozinho (passou) e a suíte inteira (168 passaram e 1 foi pulado, em 35 s). Não diagnostiquei a causa da primeira execução; o provável é um estado intermediário do arquivo do outro executor. Fica como observação, não como resolvido.
7. **Diagnóstico acrescentado depois de ver o resultado:** `delta_log_loss_treino` nos atributos, para mostrar que a região parecia ajudar no treino. É informativo e não entra na regra; o resto do JSON ficou idêntico.

### Desvios do especificado

- O plano pedia `run_backtest()` gravando `criterion` com "regra, passed, adjustment_applied"; acrescentei `per_cut`, `runs`, `final_curve`, `metric` e `tie_tol` (sem remover nada).
- O bloco `hoje.categorias` é um dicionário por lista (e não uma lista), e `cuts[].categorias` também; as demais coleções por corte são listas.
- Blocos AUTO além dos dez pedidos: `scoring-criterio` e `scoring-foque-idade`.
- A linha 5 de `explain.how_it_works` já estava pronta na 3a; não alterei `explain.py`. `validate.headline_metrics(backtest)` devolve o dict que ela espera e o teste `test_how_it_works_line_5_uses_the_headline_from_the_json` confere.
- Não alterei `features.py` nem `score.py`. O ajuste com L2 só nos coeficientes do atributo ficou em `validate.py` (`fit_logistic_masked`), testado contra `fit_logistic`.

### Decisões

As linhas estão em `docs/DECISIONS.md` (as 8 da 3a, consolidadas sem edição, e 9 novas da 3b: H = 90, primeira foto, métrica primária, ajuste único não aplicado, atributos descartados, censura, Foque 61+, verificador de "pp").

### Pendências

- O Foque de hoje (fim de trimestre) provavelmente está otimista para os 69 deals de 61+ dias. A interface e o MODEL_CARD devem repetir a ressalva.
- A sensibilidade ao horizonte (H) e ao passo da grade do joelho não foi medida.
- O `test_build.py` do executor da interface precisa ser conferido por ele (uma execução da suíte travou enquanto ele o editava; a seguinte passou).
- Commit: nenhum (quem commita é o orquestrador). `gitw.py status`: tudo dentro da pasta da submissão.