# F2 — Diagnóstico enxuto + instrumentação (spec para o Claude Code)

- **Teto:** 30 min. Ao chegar a 36 min (120%), pare e proponha o corte no report.
- **Leia antes:** `CLAUDE.md`, `planning/F0-escopo.md` (seções 3 Q1, 4 H5 e 6) e `planning/F1-report.md`.
- **Objetivo:** responder às 3 perguntas do brief sobre o DS1 em até 5 linhas, com o efeito mínimo detectável (MDE); calcular o custo de triagem nos cenários A e B; especificar os 5 eventos de instrumentação e em quantas semanas eles tornam o diagnóstico real.
- **Proibido nesta fase:** teste de permutação por segmento, Holm, ε², bootstrap por segmento; qualquer modelo no DS2; tocar em `planning/F1-revisao/` (o Gustavo está adjudicando); commit.

## Passo 0 — Correções pendentes da F1 (≤ 5 min)

1. **Caminho absoluto:** `solution/outputs/f1_dados.json` contém `C:\Users\...`. Faça `f1_verificar_dados.py` gravar só o nome do arquivo (ou caminho relativo a `DATA_DIR`). Rode de novo só esse script e confirme que os demais campos não mudaram.
2. **Leitura robusta do Excel:** em `solution/comum.py`, `ler_csv_excel` deve aceitar separador `;` ou `,` (detectar pela linha de cabeçalho) e codificação UTF-8 com BOM, UTF-8 sem BOM ou cp1252, nessa ordem. A escrita (`salvar_csv_excel`) não muda. Acrescente testes com 3 arquivos sintéticos em `tmp_path` (`;` + utf-8-sig; `,` + utf-8; `,` + cp1252 com `ã`). Motivo: o Excel online exportou a revisão com `,` e em cp1252, e o `preparar` quebrou.
3. Não rode `f1_planilha_revisao.py` nem `f1_adjudicacao.py`.

## Passo 1 — `solution/f2_diagnostico.py` (≤ 15 min)

Leia o DS1. "Duração" = `Time to Resolution` − `First Response Time`, em horas, só para `Closed` com duração > 0 (mesma base da T6, n = 1.402). Rotule toda saída que usa duração como **"variável sintética e inválida (T3); usada só como premissa de variância"**.

**1.1 MDE.** Função `mde(sd, n1, n2, alfa=0.05, poder=0.8)` = (z₁₋α/₂ + z_poder) × sd × √(1/n₁ + 1/n₂). Com `sd` = desvio padrão da duração (premissa):
- MDE atual para a comparação entre os dois menores grupos de prioridade, os dois menores de canal e as duas menores combinações canal × prioridade × tipo com n ≥ 20;
- n por grupo necessário para MDE = 2 h (n₁ = n₂);
- semanas até atingir esse n no **menor** grupo, para 3 granularidades — prioridade (4 grupos), canal × prioridade (16), canal × prioridade × tipo (80) — com volume de **30.000 tickets/ano** (premissa do brief, 52 semanas) e as participações observadas no DS1.
- Grave `solution/outputs/f2_mde.csv` (granularidade, menor_grupo, participacao, n_atual, mde_atual_h, n_para_2h, semanas_para_2h) e os parâmetros (sd, alfa, poder, volume) em `solution/outputs/f2_premissas.json`, todos rotulados como premissa.

**1.2 "Piores combinações" (uma linha, sem teste).** Entre as combinações canal × prioridade × tipo com n ≥ 20: a maior diferença observada de duração média entre duas combinações e o MDE para os n dessas duas. Grave em `f2_mde.csv` como linha extra ou em `f2_diagnostico.json`.

**1.3 Custo de triagem.**
- Cenário A (existe etapa separada de triagem): custo anual de triagem manual = volume × minutos/60 × R$/h, na grade {2, 3, 4} min × {25, 35, 50} R$/h. Grave `solution/outputs/f2_custo_triagem.csv`. **Não calcule economia**: a economia depende da cobertura medida na F3. Deixe a fórmula escrita (economia = cobertura_automatica × custo_anual) no JSON.
- Cenário B (não existe etapa separada): economia de triagem = 0; o ganho viria do reroteamento evitado, **não calculável** (nenhum dataset registra transferência). Registre essa frase no JSON.

**1.4 Teste:** `solution/tests/test_f2.py` com `mde(10, 100, 100)` ≈ 3,96 (tolerância 0,01) e um caso de semanas calculado à mão.

## Passo 2 — `docs/instrumentacao.md` (≤ 7 min)

Tabela com os 5 eventos: `ticket_criado`, `resposta_agente`, `status_mudou`, `reatribuido`, `csat_respondido`. Colunas: evento | quando dispara | campos mínimos | o que permite calcular | pergunta do brief que responde.

- Campos comuns a todos: `event_id` (único, chave de idempotência para descartar evento duplicado), `ticket_id`, `timestamp_utc`, `ator` (cliente / agente / sistema).
- `status_mudou`: `status_de`, `status_para` (incluindo "aguardando cliente", "resolvido", "reaberto").
- `reatribuido`: `fila_de`, `fila_para`, `motivo`.
- `csat_respondido`: `nota`, ligada ao `ticket_id`.
- Métricas derivadas mínimas: tempo até a 1ª resposta; tempo de resolução **líquido** (descontando o tempo em "aguardando cliente"); taxa de reabertura; reatribuições por ticket; CSAT por ticket cruzado com as anteriores.
- Uma linha final com o prazo: "com ~30 mil tickets/ano, o diagnóstico por <granularidade> fica possível em <semanas> semanas", usando `f2_mde.csv`.
- Sem texto sobre a experiência do Gustavo.

## Passo 3 — `docs/diagnostico.md` (≤ 3 min)

No máximo **5 linhas**, cada uma com número e arquivo de origem, respondendo nesta ordem:
1. Onde o fluxo trava: não é afirmável (T3 e T6), com o MDE atual e a maior diferença observada (1.2).
2. O que impacta a satisfação: nada distinguível (T5).
3. Quanto se desperdiça: não mensurável em horas no DS1; o custo de triagem do cenário A (valor base R$ 35/h e 3 min, com a faixa da grade).
4. Cenário B: economia de triagem zero; o ganho real depende de reatribuições, que hoje não são registradas.
5. O que fazer: os 5 eventos e o prazo em semanas.

## Passo 4 — Report

`planning/F2-report.md` no formato da seção 8 do `CLAUDE.md`. Acrescente a linha da F2 em `process-log/process-log.md` com "Decisão minha" vazia.

## Critérios de aceite

- `python solution/f2_diagnostico.py` e `pytest solution/tests -q` passam (todos os testes, incluindo os da F1).
- Todo número de `docs/diagnostico.md` e `docs/instrumentacao.md` aparece em um arquivo de `solution/outputs/`.
- Toda premissa aparece rotulada como premissa.
- `f1_splits.csv` com o mesmo SHA-256 (37703450…865ba0).
- Nenhum arquivo de `planning/F1-revisao/` modificado. Nenhum commit.
