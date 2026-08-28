# Decisões — Iteração 02 · Contrato Analítico (problema → opções → evidência → decisão → trade-off)

- **Iteração:** 02 (reconciliação das definições/grãos de churn e contrato analítico)
- **Data:** 2026-08-28
- **Executor:** exatamente um subagente `deepseek-max` (via OpenCode Go), sob orquestração do opencode — julgamento do executor registrado de forma explícita vs output/contexto da IA, conforme regra de governança (execution-plan regra 8; report da Iteração 01 §3).
- **Evidência dos números:** todas as decisões abaixo usam números re-derivados dos 5 CSVs commitados (`solution/data/raw/`) pelo `solution/src/02_reconcile_churn.py`; nada é copiado de fonte externa. O resumo executivo destas decisões é versão gerada no `solution/docs/analytical-contract.md` §12.

---

## D1 — Lente primária por pergunta de negócio (nenhuma fonte resolve tudo)

- **Problema:** `accounts.churn_flag` (110 contas), `subscriptions.churn_flag/end_date` (486 assinaturas; 312 contas) e `churn_events` (600 eventos; 352 contas) divergem entre si. Usar uma única fonte para todas as perguntas produziria números enganosos (ex.: "taxa de churn" mudaria conforme a tabela escolhida).
- **Opções:**
  1. Escolher uma fonte canônica (ex.: eventos) para tudo;
  2. Definir lente primária POR pergunta, com regra explícita de não-mistura;
  3. Misturar lentes livremente conforme conveniência.
- **Evidência:** interseções/diferenças recalculadas (report §3.1): flag∩eventos=75, assinatura∩eventos=227, as três=50; divergências 35/277/125; alinhamento temporal fraco (apenas 21,0% dos eventos com |lag|≤30 dias de uma `end_date`; 214 eventos sem nenhuma assinatura encerrada na conta) — as lentes são decopladas na base sintética.
- **Decisão:** opção 2 — contrato §4 define a lente primária por pergunta: eventos para diagnóstico/causa; assinaturas para receita/MRR; `accounts.churn_flag` apenas como status snapshot no corte; painel account-month para risco. O contrato §4 lista explicitamente quando as lentes NÃO podem ser comparadas.
- **Trade-off:** exige disciplina das iterações seguintes (declarar a lente em cada análise) em troca de nenhum número enganoso.

## D2 — Grão-mestre account-month (painel do signup ao corte)

- **Problema:** contagens em grão de conta (110/312/352) não suportam séries temporais, coortes nem mensuração de MRR ao longo do tempo.
- **Opções:**
  1. Grão account (uma linha por conta);
  2. Grão subscription (uma linha por assinatura);
  3. Grão account × mês.
- **Evidência:** necessidade de coortes/tempo-ao-churn (Iteração 03) e jornadas (Iteração 04) exige linha por conta×mês; 5.807 linhas geradas (500 contas × meses do signup ao corte 2024-12), tamanho pequeno e auditável.
- **Decisão:** opção 3 — `solution/data/processed/account_month.csv`, uma linha por `account_id`×mês, do mês do signup ao corte inclusive, com estado no FIM do mês.
- **Trade-off:** painel maior que o mínimo necessário; em troca, análises posteriores não precisam reconstruir o painel e os invariantes G1–G13 garantem consistência.

## D3 — Regra do winner vs soma ingênua de MRR sobreposto

- **Problema:** contas têm 2–19 assinaturas (mediana 10) com sobreposição massiva: 4.686 de 5.254 linhas account-mês com >1 assinatura ativa (89,2%). Somar MRR das ativas dobra a receita.
- **Opções:**
  1. Soma ingênua (todas as ativas);
  2. Winner por maior MRR (não-trial primeiro);
  3. Winner por `start_date` mais recente;
  4. Sem regra (ignorar a sobreposição).
- **Evidência:** na janela, soma ingênua = 62.216.507 vs winner max-MRR = 28.766.224 (razão 2,16×; diferença 33.450.283 = 53,8% da soma ingênua); winner por start recente = 13.516.561 (tende a escolher assinaturas novas, inclusive trials MRR 0 — subestima a receita dominante).
- **Decisão:** opção 2 — winner determinístico: (1) não-trial; (2) maior `mrr_amount`; (3) `start_date` mais recente; (4) `subscription_id` lexicográfico. `mrr_sum_naive` preservado apenas para auditoria; variante por start recente registrada como sensibilidade.
- **Trade-off:** o MRR da conta reflete a assinatura dominante (não a soma de todas); em troca, zero double-counting e regra reproduzível byte-a-byte.

## D4 — Semântica temporal (fim do mês; intervalos inclusive)

- **Problema:** bordas de mês e intervalos ambíguas geram contagens diferentes (ex.: assinatura que termina em 12/04 é ativa em abril?).
- **Opções:**
  1. Estado no INÍCIO do mês;
  2. Estado no FIM do mês;
  3. Intervalo [start, end) exclusive;
  4. Intervalo [start, end] inclusive.
- **Evidência:** a auditoria It01 (D03/D04) não define semântica; durante o desenvolvimento, uma exploração com comparação ao início do mês contou 3 linhas account-mês a mais (5.257 vs 5.254) e MRR total maior (63,3M vs 62,2M) — erro real do executor, corrigido ao fixar "ativo no fim do mês" com `end_date ≥ último dia do mês`.
- **Decisão:** opções 2+4 — estado no FIM do mês (sem look-ahead intra-mês) e [start_date, end_date] inclusive. Ativa em `m` ⟺ start ≤ último dia de `m` e (end nulo ou end ≥ último dia de `m`).
- **Trade-off:** regra simples e determinística; assinatura que termina em `d` deixa de contar no mês cujo último dia > d (ex.: fim em 12-15 → inativa em dezembro — estado medido no fim do mês; conservadora).

## D5 — Registros temporalmente inválidos (uso pré-start 76,6%; uso/tickets pré-signup)

- **Problema:** 19.142 de 25.000 linhas de uso (76,6%) anteriores ao `start_date` da assinatura; 13.198 usos e 1.077 tickets anteriores ao signup; 53 eventos antes da 1ª assinatura; 90 após a última `end_date`. Descartar silenciosamente viesaria qualquer análise temporal.
- **Opções:**
  1. Descartar os inválidos sem registro;
  2. Reter tudo sem política;
  3. Política dupla: quantificar tudo, manter contagens brutas e alinhadas separadas, definir uso permitido por conjunto.
- **Evidência:** partição exata (19.142 antes / 290 depois / 5.568 dentro = 25.000); sensibilidade documentada no report §7 e contrato §9 (análises declaram variante bruta vs alinhada).
- **Decisão:** opção 3 — `usage_rows_month` (bruto) e `usage_rows_in_window_month` (dentro de [start, end]) no painel; conjuntos inválidos quantificados e com uso permitido declarado (contrato §9); nada descartado silenciosamente.
- **Trade-off:** análises precisam declarar a variante; em troca, nenhum viés oculto e sensibilidade mensurável.

## D6 — Rótulo snapshot no painel (anti-leakage)

- **Problema:** `accounts.churn_flag` é snapshot do corte; usá-lo como série temporal vazaria informação futura para meses anteriores.
- **Opções:**
  1. Não incluir no painel;
  2. Incluir com nome explícito e proibição documentada + invariante estrutural (G10).
- **Evidência:** G10 verifica que colunas variantes no tempo usam apenas linhas-fonte com data ≤ fim do mês; a única coluna que referencia o corte é `churn_flag_snapshot_2024_12_31`.
- **Decisão:** opção 2 — coluna incluída como rótulo do corte, PROIBIDA em features de risco (contrato §8), com a regra "alvo vs feature no mesmo mês" explicitada (features de mês ≤ m−1 quando o desfecho é churn em `m`).
- **Trade-off:** conveniência (rótulo final disponível) vs risco de mau uso — mitigado por contrato + invariante + nome da coluna autoexplicativo.

## D7 — CSAT/reason/feedback como evidência sugestiva

- **Problema:** `satisfaction_score` restrito a {3,4,5} com 825 nulos (41,2%); `reason_code` com 95 'unknown' (22 sem feedback); `feedback_text` 148 nulos — qualidade/completude limitadas e domínio suspeito de geração sintética.
- **Opções:**
  1. Tratar como prova (causal);
  2. Tratar como evidência sugestiva rotulada.
- **Evidência:** auditoria It01 (T06, C05, §5) documenta as limitações; nenhuma relação causal pode ser derivada destas colunas com essa completude.
- **Decisão:** opção 2 — contrato §10: evidência sugestiva de qualidade da experiência; relações observadas são correlações e serão rotuladas como tal (It03–05).
- **Trade-off:** conclusões causais proibidas; em troca, nenhuma afirmação não suportada.

## D9 — Duas lentes de receita (correção M1 do review gate 3x)

- **Problema:** a fórmula única de "revenue churn" do contrato §5 baseada no winner (Σ winner_mrr(m−1) de contas que ficam inativas) é quase degenerada nesta base: soma **18.507** na janela (2 transições), enquanto a exposição contratual bruta (Σ MRR das assinaturas encerradas, lente B) é **1.179.139** (486 assinaturas) e as saídas de assinaturas **não-dominantes** com a conta permanecendo ativa somam **422.691** em 274 assinaturas (episódios conta-mês: 254; 226 com winner_mrr inalterado, 0 com redução) — razão ≈22,8× vs o capturado. Exemplo: A-5a215a em 2024-12 — duas assinaturas de 17.313 (34.626) encerram com winner inalterado em 17.313 (perda invisível).
- **Opções:**
  1. Manter a fórmula única do winner como "revenue churn";
  2. Definir duas lentes nomeadas (exposição bruta vs perda líquida de estado) e proibir o uso isolado do winner;
  3. Trocar a métrica primária para a lente B sem distinção de troca/replacement.
- **Evidência:** recálculo independente (ver report de correção do gate): 1.179.139 / 18.507 / 422.691 / 150.817 (contraction ativa em 36 transições) / 2.287.279 (expansão ativa em 590 transições — a maior parte das saídas é compensada dentro da conta).
- **Decisão:** opção 2 — **R1 gross subscription ending MRR** (exposição contratual bruta; NÃO chamada de "receita perdida" automaticamente — pode ser troca/replacement/sobreposição) e **R2 net account-state MRR loss** (churn-to-inactive + active contraction entre snapshots), com cobertura/trade-off explícitos; winner preservado como **estado/risco** e **PROIBIDO** como total de churn contratual isolado (contrato §5/§6; report §7).
- **Trade-off:** análises de receita (It03+) precisam declarar a lente e reportar o gap entre R1 e R2; em troca, nenhum número enganoso de "receita perdida".

## D10 — Política de `closed_at` (correção do review gate 3x)

- **Problema:** a It01 adiou a semântica de `closed_at` (assimetria de nulos vs `end_date`) para o contrato analítico; sem política explícita, métricas de resolução/CSAT posteriores poderiam vazar (imputar fechamento futuro ou incluir tickets abertos na data índice).
- **Opções:**
  1. Imputar fechamento futuro quando ausente;
  2. Documentar a política sem alterar a base atual;
  3. Ignorar o campo.
- **Evidência:** na base atual 0 nulos em `closed_at` (2.000/2.000 tickets fechados); satisfação tem 825 nulos (41,2%) → denominador explícito de 1.175 tickets com nota (gate G15).
- **Decisão:** opção 2 — tickets existem por `submitted_at`; métricas de resolução/CSAT usam APENAS tickets fechados com informação observável até a data índice; `closed_at` nulo exclui o ticket com denominador explícito; **nunca imputar fechamento futuro** (contrato §7/§10; `closed_at` promovida a coluna mínima do REQUIRED e parseada — D01).
- **Trade-off:** métricas de resolução ficam dependentes da completude de `closed_at` (hoje 0 nulos); em troca, zero risco de leakage por imputação.

---

## Decisão de processo — bloqueio estrutural (lição da Iteração 01 aplicada)

- **Problema:** em It01, schema quebrado causava `KeyError` + relatório stale. Esta iteração reutiliza a lição: pipeline profundo (lentes → alinhamento → painel → gates) dependente das colunas mínimas.
- **Decisão:** colunas mínimas por arquivo (REQUIRED no script); se ausentes → FAILs estruturados (S01 + R01–R04 "não executado (schema)"), relatório SEMPRE regravado, outputs de dados NÃO regenerados (mensagem explícita de stale), exit 1, sem traceback. Uma base parcial violaria o schema do contrato — bloquear com diagnóstico preciso é preferível a gerar artefato incompleto.
- **Evidência:** 3 cenários sandbox (coluna `churn_date` renomeada; arquivo ausente; coluna `signup_date` renomeada) — exit 1, 5 FAILs, sem traceback, idempotente.
- **Trade-off:** perde-se preservação parcial de checks possíveis (que It01 fazia); em troca, o contrato da base-mestre nunca é violado por schema quebrado.