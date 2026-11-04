# F3 — Report (Experimento clássico × LLM, faixas da Q2, H2)

Caminhos relativos à submissão (`ai-master-challenge/submissions/gustavo-covaleski/`). Os scripts rodam com `.venv/Scripts/python`. A ordem de execução foi: `f3_classico.py` → `f3_faixas.py` → `f3_h2.py` → `f3_llm.py` → `f3_faixas.py` (de novo, para o ponto de equilíbrio, que depende do custo do LLM).

## 1. O que foi feito

1. **Passo 0:**
   - chave presente em `challenge-g4-ai-master/.env` (só verificada, nunca impressa);
   - preço e modelo consultados nas páginas oficiais em 03/11/2026 22:52 −03 → `solution/outputs/f3_premissas.json`;
   - dependência nova: `anthropic==2.4.0`.
2. **Passo 1** (`f3_classico.py`): TF-IDF + LR fixos, treinados e avaliados nos dois splits congelados; IC por bootstrap; vazamento; probabilidades do holdout por grupo; **passo 4** (latência, 1.000 tickets um a um).
3. **Passo 2** (`f3_faixas.py`): curva com 50 limiares; *e* adjudicado ponderado com bootstrap estratificado; *e* por quase-duplicados com Wilson; *e*_Q2; 3 faixas; economia no cenário A; ponto de equilíbrio.
4. **Passo 3** (`f3_h2.py`): concordância nos 60 tickets revisados, desfechos, teste de consistência, tabela por categoria e 20 suspeitos em `planning/F3/`.
5. **Passo 5** (`f3_llm.py`): 400 tickets fora da faixa "IA decide", prompt versionado em `solution/prompts/classificar_v1.txt`, log em `planning/F3/f3_llm_log.jsonl`.
6. **Passo 6:** `solution/tests/test_f3.py`. `pytest solution/tests -q` → **26 passed**.

## 2. Resultados

Siglas: **[cl]** `f3_classico.json`, **[fx]** `f3_faixas.json`, **[cv]** `f3_curva.csv`, **[h2]** `f3_h2.json`, **[llm]** `f3_llm.json`, **[pr]** `f3_premissas.json`. Todos em `solution/outputs/`, gerados pelo script de mesmo nome.

### Clássico e vazamento [cl]

| Holdout | n | Acurácia (IC 95%) | Macro-F1 (IC 95%) |
|---|---|---|---|
| Por grupo | 9.567 | 85,07% (84,34–85,79) | 84,52% (83,59–85,36) |
| Aleatório | 9.568 | 85,38% (84,70–86,05) | 84,58% (83,67–85,42) |
| **Vazamento (aleatório − grupo)** | | **+0,31 p.p.** | **+0,06 p.p.** |
| Holdout aleatório, 564 tickets com quase-duplicado no treino | 564 | 91,84% | — |
| Holdout aleatório, demais tickets | 9.004 | 84,97% | — |

- **F1 por classe (holdout por grupo):** Access 0,872; Administrative rights **0,715**; HR Support 0,867; Hardware 0,837; Internal Project 0,841; Miscellaneous 0,830; Purchase 0,917; Storage 0,882.
- **Latência do clássico (1.000 tickets, um a um):** p50 0,430 ms; p95 0,648 ms; 0,461 s por 1.000. Custo marginal ≈ 0 (CPU local).

### *e* e faixas da Q2 [fx], [cv]

| Item | Valor |
|---|---|
| *e* adjudicado bruto | 21/60 = 35,00% |
| *e* adjudicado ponderado pela prevalência | **31,79%** (IC 95% bootstrap estratificado: 19,62–43,92%) |
| *e* por quase-duplicados | 118/3.092 = **3,82%** (Wilson: 3,20–4,55%) |
| *e*_Q2 (menor valor pontual) | 3,82%, fonte: quase-duplicados |
| Meta "IA decide" / "IA sugere" (LI ≥) | 0,9680 / 0,9545 |
| **IA decide** (p_max ≥ 0,74) | cobertura **57,17%** (5.469); precisão 97,37% (96,91–97,76) |
| **IA sugere, humano confirma** (0,66 ≤ p_max < 0,74) | cobertura 8,65% (828); precisão 88,53% (86,18–90,52) |
| **Humano decide** (p_max < 0,66) | cobertura 34,18% (3.270); precisão do modelo 63,64% (61,98–65,27) |

- **Economia, cenário A** (cobertura 57,17% × custo anual de triagem; premissas): R$ 30.014/ano na base (3 min, R$ 35/h). Faixa da grade: de R$ 14.293 (2 min, R$ 25/h) a R$ 57.170 (4 min, R$ 50/h). A recomendação de automatizar a faixa se mantém em toda a grade, porque o custo marginal do clássico é ≈ 0.
- **Cenário B:** economia de triagem = 0.
- **Ponto de equilíbrio do LLM:** US$ 0,000151 por ticket. Com câmbio de 5 ou 6 R$/US$ (premissa **não consultada**) e R$ 25–50/h, ele fica entre 0,05 e 0,13 **segundo** de triagem por ticket.

### H2 [h2]

| Item | Valor |
|---|---|
| Concordância nos 60 tickets: modelo × original / modelo × Gustavo / Gustavo × original | 88,33% / 50,00% / 46,67% |
| 21 "original errado": modelo prevê o original / o rótulo do Gustavo / outro | **18** / 1 / 2 |
| 11 "ambíguo": modelo prevê o original / o rótulo do Gustavo / outro | 8 / 2 / 1 |
| Teste de consistência: 1 − *e* ponderado; 1 − *e*_superior; acurácia medida | 68,21%; 56,08%; **85,07%** |
| Conclusão pré-registrada (as duas condições disparam) | "a discordância do revisor reflete uma convenção da taxonomia que o modelo aprende, não erro aleatório do rótulo" |
| Erros do modelo com p_max ≥ 0,90 no holdout por grupo | 25 (0,26%); 20 exemplos em `planning/F3/f3_suspeitos.csv` |

| Categoria | Original errado | Ambíguo | F1 do modelo | 3 confusões mais frequentes no holdout (verdadeiro → previsto) |
|---|---|---|---|---|
| **Administrative rights** | **6/6 (100%)** | 0% | **0,715** | Hardware 124, Miscellaneous 8, Access 6 |
| Storage | 4/6 (66,7%) | 16,7% | 0,882 | Hardware 51, HR Support 22, Miscellaneous 13 |
| Hardware | 4/11 (36,4%) | 9,1% | 0,837 | HR Support 124, Miscellaneous 64, Access 33 |
| HR Support | 3/9 (33,3%) | 33,3% | 0,867 | Hardware 162, Miscellaneous 67, Access 18 |
| Miscellaneous | 2/8 (25,0%) | 25,0% | 0,830 | Hardware 155, HR Support 75, Access 17 |
| Internal Project | 1/6 (16,7%) | 33,3% | 0,841 | HR Support 39, Hardware 28, Miscellaneous 26 |
| Access | 1/8 (12,5%) | 25,0% | 0,872 | Hardware 144, HR Support 55, Miscellaneous 39 |
| Purchase | 0/6 (0%) | 0% | 0,917 | Hardware 46, HR Support 10, Access 4 |

**Par Hardware × Storage** (holdout): Storage → Hardware em 51 de 555 tickets; Hardware → Storage em 8 de 2.723. É assimétrico: Storage é absorvido por Hardware.

### LLM na faixa de abstenção [llm], [pr]

| Item | Valor |
|---|---|
| Modelo | `claude-haiku-5-5` (o Haiku mais recente na página oficial de modelos) |
| Preço | US$ 0,10 por MTok de entrada; US$ 0,50 por MTok de saída (prompts ≤ 100 mil tokens). Fonte: platform.claude.com/docs/en/about-claude/pricing, 03/11/2026 22:52 −03 |
| Amostra | 400 tickets (seed 42) de 4.098 do holdout por grupo com p_max < 0,74 |
| **LLM: acurácia / macro-F1** | **26,50%** (22,25–31,00) / 26,67% (20,15–32,44) |
| **Clássico nos mesmos 400** | **69,50%** (64,99–74,00) / 70,95% (62,65–76,26) |
| Falhas finais / saídas inválidas na 1ª tentativa / erros de API | 0 / 1 (recuperada na repetição) / 0 |
| Latência p50 / p95 (8 chamadas concorrentes) | 1.152 ms / 1.495 ms |
| Tokens médios: entrada / saída / system com exemplos fixos | 1.383,9 / 24,1 / 1.305 |
| Custo por 1.000 tickets | **US$ 0,1508**, dos quais US$ 0,1308 são instruções + exemplos fixos |
| Híbrido: ganho na faixa de abstenção | **−43,0 p.p.** (o LLM piora; custo por acerto adicional indefinido) |
| Híbrido: acurácia estimada no holdout inteiro (clássico na faixa IA decide + LLM no resto) | 67,02% (contra 85,07% do clássico sozinho) |

O erro dominante do LLM foi prever **Access** em excesso. Na matriz de 400 tickets, saíram como Access 41 tickets HR Support, 33 Miscellaneous, 32 Hardware e 18 Storage.

## Escolha da abordagem

A escolha fica com o Gustavo. A tabela só apresenta os números.

| Abordagem | Acurácia | Macro-F1 | Cobertura automática | Custo por 1.000 | Latência p50 / p95 | Origem |
|---|---|---|---|---|---|---|
| Clássico, tudo automático | 85,07% | 84,52% | 100% | ≈ 0 (CPU local) | 0,43 / 0,65 ms | [cl] |
| Clássico com faixas da Q2 | 97,37% na faixa automática | — | 57,17% (+ 8,65% sugerindo) | ≈ 0 | 0,43 / 0,65 ms | [fx], [cl] |
| LLM (Haiku 5.5) na faixa de abstenção | 26,50% (amostra de abstenção) | 26,67% | — | US$ 0,1508 por 1.000 chamadas | 1.152 / 1.495 ms | [llm] |
| Clássico nos mesmos 400 de abstenção | 69,50% | 70,95% | — | ≈ 0 | 0,43 / 0,65 ms | [llm], [cl] |
| Híbrido (clássico na faixa IA decide + LLM no resto) | 67,02% (estimada no holdout inteiro) | — | 57,17% clássico + 42,83% LLM | US$ 0,1508 por 1.000 enviados ao LLM | clássico + 1.152 / 1.495 ms | [llm], [fx] |

## O que os dados permitem e não permitem afirmar (F3)

**Permitem:**
- No holdout por grupo, o clássico acerta 85,07% (IC 84,34–85,79) [cl].
- Com *e*_Q2 = 3,82%, 57,17% dos tickets passam na meta mais exigente, com precisão de 97,37% [fx].
- No DS2, o LLM com few-shot erra mais que o clássico na faixa de abstenção, por 43 p.p. [llm].
- O revisor discorda do rótulo de forma sistemática, e não aleatória: o modelo reproduz o original em 18 de 21 casos [h2].

**Não permitem:**
- Que o rótulo original esteja "errado" em 31,79% dos tickets em sentido absoluto. A H2 indica convenção de taxonomia, e o *e* adjudicado mede a distância entre a leitura do revisor e a convenção da base.
- Que o LLM seja ruim para triagem em geral. O resultado vale para texto pré-processado (F1, 3.2), um prompt fixo, 8 exemplos e uma taxonomia com convenções não escritas.
- O vazamento como "número de capa" grande: no agregado ele é de 0,31 p.p.

## 3. O que contraria a hipótese ou a expectativa

- **O vazamento agregado é pequeno (+0,31 p.p.),** e o F0 o tratava como número de capa. A exposição é real (+6,87 p.p. de acurácia nos 564 expostos: 91,84% contra 84,97%), mas atinge só 5,89% do holdout, então dilui no agregado. O número útil é o efeito nos expostos, não a diferença agregada.
- **O LLM ficou muito abaixo do clássico** (26,5% contra 69,5% nos mesmos tickets) e abaixo até do acaso ponderado das classes mais frequentes. Hipóteses, não testadas:
  1. texto pré-processado (F1, 3.2);
  2. a taxonomia segue convenções que o modelo não vê. Exemplo: pedidos de acesso rotulados como Hardware, HR Support ou Miscellaneous. É coerente com a H2: o revisor humano também concordou só 46,67% com o original;
  3. o prompt v1 não foi ajustado, porque a spec proíbe ajustar olhando o holdout.
- ***e* adjudicado de 31,79%**, muito acima dos 3,82% dos quase-duplicados. Pela regra pré-registrada, *e*_Q2 usa o menor (3,82%). Com o *e* adjudicado, as metas seriam LI ≥ 0,56–0,80, e quase todo o holdout entraria em "IA decide".
- **Administrative rights:** 6 de 6 "original errado" e o pior F1 (0,715). 124 dos tickets da classe no holdout são previstos como Hardware. É a categoria com maior evidência de convenção conflitante.
- **A saída inválida foi rara** (1 em 400 na 1ª tentativa, 0 falhas finais). O risco de JSON inválido existe, mas é pequeno nesta configuração.

## 4. Desvios da spec

- **`temperature = 0` não foi enviado.** O Claude Haiku 5.5 recusa `temperature` com valor diferente do padrão (400, segundo a referência da API). Usei `thinking: disabled` + `output_config.effort: low`, `max_tokens = 64`. O determinismo não é garantido. Está registrado em [pr].
- **Câmbio R$/US$** (5 e 6) para o ponto de equilíbrio: é premissa **não consultada** em fonte oficial e está rotulada assim em [pr] e [fx]. A conclusão (equilíbrio < 0,2 s/ticket) não muda nessa faixa.
- **`f3_premissas.json`** foi escrito à mão, a partir da consulta (não há script que raspe a página). URLs e data estão no arquivo.
- **Latência do LLM** medida com 8 chamadas concorrentes, por chamada, no cliente. Pode ser maior do que em chamadas seriais.
- **1 chamada de teste extra** (texto sintético, fora da amostra), para validar os parâmetros da API. Não entra nas métricas nem no log.
- **Híbrido "acurácia estimada no holdout inteiro":** combina a precisão medida na faixa IA decide com a acurácia do LLM na amostra (não é medida ticket a ticket). Está rotulado no JSON.

## 5. Erros e correções durante a execução

- 1ª chamada à API: `400 — Your credit balance is too low` (request_id `req_011Cgh4LrsVxV7NPgYKuN2UW`). Parei e perguntei; o Gustavo adicionou crédito, e a 2ª tentativa funcionou.
- O resultado de 26,5% do LLM pareceu bug. Conferi refazendo o cálculo por junção de `id` entre o log e as probabilidades: deu o mesmo valor, e a matriz de confusão mostra o excesso de Access.
- `planning/F1-revisao/adjudicacao.csv` aparece com hash diferente do snapshot da F2: foi modificado às 22:43, antes do início da F3 (22:50), pela adjudicação do Gustavo. Nenhum script da F3 escreve em `planning/F1-revisao/`.

## 6. Pendências e decisões que dependem do Gustavo

1. **Escolha da abordagem** (tabela acima).
2. *e*_Q2 = 3,82% (quase-duplicados), conforme a regra pré-registrada. O *e* adjudicado (31,79%) entra só como achado da H2. Confirmar se é essa a leitura.
3. Câmbio: confirmar a premissa ou fornecer a fonte.
4. Se quiser um prompt v2 do LLM, ele precisa ser ajustado **fora do holdout** (por exemplo, numa fatia do treino), para não violar a spec.

## 7. Tempo gasto × orçado

- Orçado: 50 min (teto 60).
- Relógio: das 22:50 às ~23:08 (~18 min), incluindo a espera pela recarga de crédito. Os modelos rodaram em ~2,5 min (clássico) e ~1,2 min (LLM).

## 8. Commit (Parte 2)

- `.env` em `challenge-g4-ai-master/.env`, **fora** de `ai-master-challenge/`; nenhum `.env` dentro do clone.
- `pytest solution/tests -q` antes do commit: 26 passed.
- **Commit:** `d79a7b7156288a4ced3920cd864df0ed9bd153be`, com a mensagem "F3: experimento clássico × LLM, faixas da Q2, H2 e revisão adjudicada". Sem push.
- `git diff --cached --name-only`:

```
submissions/gustavo-covaleski/process-log/process-log.md
submissions/gustavo-covaleski/process-log/revisao_rotulos_adjudicada.csv
submissions/gustavo-covaleski/requirements.txt
submissions/gustavo-covaleski/solution/comum.py
submissions/gustavo-covaleski/solution/f3_classico.py
submissions/gustavo-covaleski/solution/f3_faixas.py
submissions/gustavo-covaleski/solution/f3_h2.py
submissions/gustavo-covaleski/solution/f3_llm.py
submissions/gustavo-covaleski/solution/outputs/f3_classico.json
submissions/gustavo-covaleski/solution/outputs/f3_curva.csv
submissions/gustavo-covaleski/solution/outputs/f3_faixas.json
submissions/gustavo-covaleski/solution/outputs/f3_h2.json
submissions/gustavo-covaleski/solution/outputs/f3_llm.json
submissions/gustavo-covaleski/solution/outputs/f3_premissas.json
submissions/gustavo-covaleski/solution/outputs/f3_probs_holdout_grupo.csv
submissions/gustavo-covaleski/solution/prompts/classificar_v1.txt
submissions/gustavo-covaleski/solution/tests/test_f3.py
```

- Nenhum caminho fora da submissão, nenhum `.venv`, `.env`, `__pycache__`, `.pytest_cache` ou arquivo de `planning/`.
- **Checagem de segredo:**
  - `git diff --cached | findstr /C:"sk-ant"` voltou vazio (código de saída 1);
  - o valor de `ANTHROPIC_API_KEY` lido do `.env` foi comparado, sem impressão, com o conteúdo de cada arquivo staged: **nenhum** o contém.
- **Checagem de texto de ticket:** 3.000 textos do DS2 (sorteados com seed 1) procurados pelos seus 40 primeiros caracteres em cada arquivo staged, exceto a planilha adjudicada: **nenhum** encontrado. O prompt versionado tem só o marcador `{exemplos}`; os exemplos reais são inseridos em tempo de execução.
- `test_f3.py` teve os comentários de `test_e_ponderado` corrigidos antes do commit (as asserções não mudaram).
- `requirements.txt` recebeu `anthropic==2.4.0`.
