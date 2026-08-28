# Relatório de Consistência — Reconciliação de Churn e Base Account-Month (Iteração 02)

Gerado por `solution/src/02_reconcile_churn.py` (execução offline e determinística; sem timestamp para garantir output byte-a-byte estável entre execuções).

## 1. Metodologia

- **Origem dos dados:** `solution/data/raw/` (5 CSVs commitados; auditoria na Iteração 01).
- **Escopo:** reconciliar as três fontes de "churn" (`accounts.churn_flag`, `subscriptions.churn_flag/end_date`, `churn_events`), quantificar divergências, construir a base-mestre account-month e fixar o contrato analítico (`solution/docs/analytical-contract.md`). Nenhuma conclusão causal é feita aqui (Iteração 03).
- **Semântica:** `PASS` = estrutura/qualidade confirmada; `WARN` = divergência/anomalia esperada em base sintética (documentada com números); `FAIL` = arquivo/schema estrutural ausente ou invariante violado. Exit code 0 se não houver FAIL.
- **Regras fixadas (resumo):** janela observacional 2023-01..2024-12; painel account×mês do mês do signup ao corte 2024-12-31; estado no FIM do mês; intervalo de assinatura [start_date, end_date] inclusive; winner = não-trial, maior MRR, start mais recente, subscription_id lexicográfico (determinístico).

## 2. Resumo executivo

| Resultado | Quantidade |
|---|---|
| PASS | 28 |
| WARN | 1 |
| FAIL | 0 |

- **Lente A (accounts.churn_flag):** 110 de 500 contas (22.0%).
- **Lente B (subscriptions):** 486 assinaturas encerradas (9.7% de 5000); 312 contas únicas (62.4% de 500); 4514 ativas.
- **Lente C (churn_events):** 600 eventos; 352 contas únicas (70.4%); 175 contas com >1 evento (máx 5); 61 eventos `is_reactivation` (55 contas).
- **Divergências (recalculadas):** flag sem evento = 35; evento sem flag = 277; evento sem assinatura churn_flag = 125.
- **Base account-month:** 5807 linhas (uma por account×mês; 500 contas × janela do signup ao corte); 5254 linhas com assinatura ativa, das quais 4686 (89.2%) com >1 assinatura ativa (sobreposição).
- **Impacto da regra do winner:** soma ingênua = 62216507 vs winner = 28766224 (razão 2.16×; diferença 33450283 = 53.8% da soma ingênua).

## 3. Lentes de churn e interseções

| Lente | Fonte | Contagem | Grão |
|---|---|---|---|
| A — flag de conta | `accounts.churn_flag` (snapshot no corte) | 110 contas | account |
| B — assinatura encerrada | `subscriptions.end_date`/`churn_flag` | 486 assinaturas; 312 contas | subscription / account |
| C — evento de churn | `churn_events` | 600 eventos; 352 contas | event / account |

### 3.1 Interseções e diferenças (contas; recalculadas nesta execução)

| Conjunto | Contagem |
|---|---|
| flag A ∩ eventos C | 75 |
| flag A ∩ assinatura churn B | 72 |
| assinatura churn B ∩ eventos C | 227 |
| A ∩ B ∩ C | 50 |
| somente A (flag) | 13 |
| somente B (assinatura churn) | 63 |
| somente C (evento) | 100 |
| A ∩ B, sem C | 22 |
| A ∩ C, sem B | 25 |
| B ∩ C, sem A | 177 |
| em nenhuma lente | 50 |
| em pelo menos uma lente | 450 |

Conferência com a Iteração 01 (recalculada, não copiada): flag sem evento = 35; evento sem flag = 277; evento sem assinatura churn_flag = 125; assinatura churn sem evento = 85.

### 3.2 Estado no corte (2024-12-31) por lente

- contas com `accounts.churn_flag=True` no corte: **110**
- contas inativas por lente de assinatura (sem assinatura ativa no fim de 2024-12): **0**
- contexto da inatividade por assinatura em toda a janela: **553** linhas account-mês inativas em **279** contas; **2** contas com ciclo ativo→inativo→(re)ativo (A-0baac2, A-180abf) — na maioria, a inatividade ocorre entre o signup e a primeira assinatura; nenhuma conta fica inativa no corte.
- contas com evento que seguem ativas no corte: **352** de 352 (episódio de evento ≠ conta perdida).

## 4. Alinhamento temporal `churn_date` vs `end_date`

Para cada evento, a `end_date` mais próxima entre as assinaturas ENCERRADAS da mesma conta (menor |churn_date − end_date|). Alinhamento é documentado como imperfeito — as lentes são decopladas na base (ver contrato §9).

- Eventos com assinatura encerrada na conta: **386** de 600 (64.3%); sem nenhuma assinatura encerrada na conta: **214**.

| Janela (|lag| em dias) | Eventos com match | Acumulado |
|---|---|---|
| ≤ 0 | 6 (1.0%) | 1.0% |
| ≤ 3 | 31 (5.2%) | 5.2% |
| ≤ 7 | 47 (7.8%) | 7.8% |
| ≤ 15 | 81 (13.5%) | 13.5% |
| ≤ 30 | 126 (21.0%) | 21.0% |
| ≤ 60 | 193 (32.2%) | 32.2% |
| ≤ 90 | 222 (37.0%) | 37.0% |
| ≤ 180 | 305 (50.8%) | 50.8% |
| ≤ 365 | 369 (61.5%) | 61.5% |

- Lag sinalizado (churn_date − end_date, dias), eventos com match: exatos=**6**; antes do fim=**268**; depois do fim=**112**; quantis [10,25,50,75,90]% = [-267, -133, -34, 6, 57].

Sensibilidade: a tabela acima mostra o efeito da janela de tolerância (0 a 365 dias). Nenhuma janela razoável alinha a maioria dos eventos — reforça que `churn_events` e `end_date` medem fenômenos distintos nesta base.

## 5. Múltiplos eventos e reativação (episódio ≠ conta perdida)

- 175 contas com >1 evento (máx 5); 61 eventos marcados `is_reactivation` (55 contas).
- A base account-month registra `n_events_in_month` (contagem) e `churn_event_in_month` (binário) por mês, sem dupla contagem: um episódio com N eventos no mesmo mês contribui com 1 para o binário e N para a contagem; a conta só é `status=inactive` pela lente de assinatura (nenhuma assinatura ativa no fim do mês).
- No corte, 352 de 352 contas com evento seguem ativas pela lente de assinatura — múltiplos eventos não implicam conta perdida.

## 6. Base account-month e impacto da sobreposição de assinaturas

| Métrica | Valor |
|---|---|
| Linhas account×mês | 5807 |
| Contas | 500 |
| Linhas com ≥1 assinatura ativa no fim do mês | 5254 |
| Linhas com >1 assinatura ativa (sobreposição) | 4686 (89.2%) |
| MRR total — soma ingênua (todas as ativas) | 62216507 |
| MRR total — regra do winner | 28766224 |
| MRR total — winner por start mais recente (sensibilidade) | 13516561 |
| Razão soma ingênua / winner | 2.16× |
| Diferença (double-counting da soma ingênua) | 33450283 (53.8% da soma ingênua) |

Regra do winner (determinística, contrato §6): entre as assinaturas ativas no fim do mês — (1) prefere não-trial; (2) maior `mrr_amount`; (3) `start_date` mais recente; (4) `subscription_id` lexicográfico. A soma ingênua dobra/estoura MRR onde há sobreposição (89.2% das linhas com assinatura) e é **rejeitada** para métricas de receita; seu valor é preservado na coluna `mrr_sum_naive` apenas para auditoria. A variante por start mais recente (13516561 na janela) tende a escolher assinaturas mais novas, inclusive trials (MRR 0), subestimando a receita dominante — por isso a variante por maior MRR (não-trial) é a regra primária.

## 7. Registros temporalmente inválidos (quantificação; política no contrato §9)

| Fenômeno | Quantidade | Política |
|---|---|---|
| Uso antes do `start_date` da assinatura | 19.142 de 25.000 (76.6%) | excluído de janela alinhada; contado à parte |
| Uso depois do `end_date` | 290 | excluído de janela alinhada; contado à parte |
| Uso dentro da janela da assinatura | 5.568 (22.3%) | base dos sinais de atividade alinhados |
| Uso anterior ao signup da conta | 13.198 | fora da janela observacional da conta |
| Tickets abertos antes do signup | 1.077 | fora da janela observacional da conta |
| Eventos antes da primeira assinatura | 53 | mantidos na lente de eventos (não dependem de assinatura) |
| Eventos após a última `end_date` | 90 | mantidos na lente de eventos; alinhamento documentado (§4) |

Nada é descartado silenciosamente: os números acima são reproduzíveis e o contrato §9 define o uso de cada conjunto.

## 8. Checks e invariantes

| ID | Escopo | Check | Veredito | Detalhe |
|---|---|---|---|---|
| F01-ravenstack_accounts.csv | ravenstack_accounts.csv | arquivo presente e carregável | **PASS** | 36148 bytes, CSV parseado (500 registros) |
| S01-ravenstack_accounts.csv | ravenstack_accounts.csv | colunas mínimas desta iteração presentes | **PASS** | 3 colunas exigidas presentes |
| F01-ravenstack_subscriptions.csv | ravenstack_subscriptions.csv | arquivo presente e carregável | **PASS** | 432565 bytes, CSV parseado (5000 registros) |
| S01-ravenstack_subscriptions.csv | ravenstack_subscriptions.csv | colunas mínimas desta iteração presentes | **PASS** | 10 colunas exigidas presentes |
| F01-ravenstack_churn_events.csv | ravenstack_churn_events.csv | arquivo presente e carregável | **PASS** | 44029 bytes, CSV parseado (600 registros) |
| S01-ravenstack_churn_events.csv | ravenstack_churn_events.csv | colunas mínimas desta iteração presentes | **PASS** | 4 colunas exigidas presentes |
| F01-ravenstack_feature_usage.csv | ravenstack_feature_usage.csv | arquivo presente e carregável | **PASS** | 1375897 bytes, CSV parseado (25000 registros) |
| S01-ravenstack_feature_usage.csv | ravenstack_feature_usage.csv | colunas mínimas desta iteração presentes | **PASS** | 2 colunas exigidas presentes |
| F01-ravenstack_support_tickets.csv | ravenstack_support_tickets.csv | arquivo presente e carregável | **PASS** | 143597 bytes, CSV parseado (2000 registros) |
| S01-ravenstack_support_tickets.csv | ravenstack_support_tickets.csv | colunas mínimas desta iteração presentes | **PASS** | 3 colunas exigidas presentes |
| D01-ravenstack_accounts.csv | ravenstack_accounts.csv | signup_date parseável | **PASS** | 0 valores não parseáveis |
| D01-ravenstack_subscriptions.csv | ravenstack_subscriptions.csv | start_date parseável | **PASS** | 0 valores não parseáveis |
| D01-ravenstack_subscriptions.csv | ravenstack_subscriptions.csv | end_date parseável | **PASS** | 0 valores não parseáveis |
| D01-ravenstack_churn_events.csv | ravenstack_churn_events.csv | churn_date parseável | **PASS** | 0 valores não parseáveis |
| D01-ravenstack_feature_usage.csv | ravenstack_feature_usage.csv | usage_date parseável | **PASS** | 0 valores não parseáveis |
| D01-ravenstack_support_tickets.csv | ravenstack_support_tickets.csv | submitted_at parseável | **PASS** | 0 valores não parseáveis |
| G1-panel | account_month | unicidade account_id × mês | **PASS** | 0 linhas duplicadas |
| G2-panel | account_month | MRR não negativo; seats > 0 quando ativa | **PASS** | winner_mrr<0=0, mrr_sum_naive<0=0, winner_seats<=0=0 |
| G3-panel | account_month | meses na janela 2023-01..2024-12 e >= mês do signup | **PASS** | meses fora da janela=0, linhas com mês < signup=0 |
| G4-panel | account_month | contas ativas por mês <= 500 | **PASS** | máx. ativas por mês=500 (total de contas=500) |
| G5-panel | account_month | abertura + movimentos = fechamento (contagem, tolerância 0) | **PASS** | 0 meses com identidade quebrada |
| G6-panel | account_month | abertura + movimentos = fechamento (MRR, tolerância 0, inteiros) | **PASS** | 0 meses com identidade quebrada |
| G7-panel | lentes vs fonte | totais de cada lente reconciliam à fonte (eventos 600/352; subs 486/312; flag 110) | **PASS** | eventos no painel=600 (fonte 600); contas c/ evento no painel=352 (fonte 352); subs churn_flag=486 (fonte 486); contas c/ sub churn_flag=312 (fonte 312); contas flag=110 (fonte 110) |
| G8-panel | account_month | tamanho do painel = soma independente de meses por conta | **PASS** | painel=5807; esperado=5807 (min meses=1, máx=24) |
| G9-panel | account_month | meses ativos de cada assinatura dentro do painel da conta (cobertura) | **PASS** | 0 de 5000 assinaturas com meses ativos fora do painel da conta |
| G10-panel | account_month | nenhum campo pós-data-índice em colunas de risco (anti-leakage) | **PASS** | month_end > corte=0; winner fora da janela do mês=0; colunas de risco ausentes=nenhuma |
| G11-align | churn_date vs end_date | alinhamento temporal documentado (matching por conta + sensibilidade a janelas) | **PASS** | eventos com assinatura encerrada na conta=386 de 600; janelas (|lag|<=d): 0d=6; 3d=31; 7d=47; 15d=81; 30d=126; 60d=193; 90d=222; 180d=305; 365d=369 |
| G12-panel | registros temporalmente inválidos | uso fora da janela da assinatura quantificado (política no contrato §9) | **WARN** | antes do início=19142 (76.6%), depois do fim=290, dentro da janela=5568 (22.3%) |
| G13-panel | eventos vs estado no corte | múltiplos eventos não contam episódio como conta perdida (medição) | **PASS** | contas com evento ainda ativas no corte=352 de 352; contas com evento inativas no corte=0; linhas inativas na janela=553 (279 contas; 2 com ciclo ativo→inativo→(re)ativo) |

## 9. Proveniência

- Script: `solution/src/02_reconcile_churn.py` (executado de `submissions/jose-nascimento/`).
- Dados de entrada: `solution/data/raw/ravenstack_*.csv` (MD5 no `data/raw/README.md`).
- Outputs: `solution/data/processed/account_month.csv` (checksum no `data/processed/README.md`); este relatório; `solution/docs/analytical-contract.md`.
- Python/pandas: versões registradas na execução (ver report de processo).
