# Relatório de Auditoria — Ingestão dos 5 Datasets RavenStack (Iteração 01)

Gerado por `solution/src/01_ingest_audit.py` (execução offline e determinística; sem timestamp para garantir output byte-a-byte estável entre execuções).

## 1. Metodologia

- **Origem dos dados:** `solution/data/raw/` (5 CSVs commitados; checksums no `README.md` da pasta — cópia byte-for-byte da origem local, MD5 idêntico).
- **Fonte oficial:** Kaggle, *SaaS Subscription & Churn Analytics* (licença MIT), conforme `challenges/data-001-churn/README.md`.
- **Referência do brief:** contagens anunciadas (~500 / ~5.000 / ~25.000 / ~2.000 / ~600) e chaves (`account_id`, `subscription_id`).
- **Semântica:** `PASS` = estrutura/qualidade confirmada; `WARN` = anomalia de qualidade esperada em base sintética (documentada, não bloqueia); `FAIL` = arquivo/schema/chave estrutural ausente ou violação estrutural. Exit code 0 se não houver FAIL.
- **Escopo:** auditoria de estrutura/qualidade/integridade. Nenhuma conclusão de negócio ou definição de churn é adotada aqui (Iteração 02).

## 2. Resumo executivo

| Resultado | Quantidade |
|---|---|
| PASS | 72 |
| WARN | 18 |
| FAIL | 0 |

### 2.1 Registros vs brief

| Arquivo | Registros reais | Brief (~) | Veredito |
|---|---|---|---|
| `ravenstack_accounts.csv` | 500 | 500 | PASS |
| `ravenstack_subscriptions.csv` | 5000 | 5000 | PASS |
| `ravenstack_feature_usage.csv` | 25000 | 25000 | PASS |
| `ravenstack_support_tickets.csv` | 2000 | 2000 | PASS |
| `ravenstack_churn_events.csv` | 600 | 600 | PASS |

## 3. Detalhamento por arquivo (schema, tipos, nulos, chaves)

### ravenstack_accounts.csv

| Coluna | Tipo (pandas) | Nulos |
|---|---|---|
| `account_id` | str | 0 |
| `account_name` | str | 0 |
| `industry` | str | 0 |
| `country` | str | 0 |
| `signup_date` | str | 0 |
| `referral_source` | str | 0 |
| `plan_tier` | str | 0 |
| `seats` | int64 | 0 |
| `is_trial` | bool | 0 |
| `churn_flag` | bool | 0 |

- Registros: 500; colunas: 10.

### ravenstack_subscriptions.csv

| Coluna | Tipo (pandas) | Nulos |
|---|---|---|
| `subscription_id` | str | 0 |
| `account_id` | str | 0 |
| `start_date` | str | 0 |
| `end_date` | str | 4514 |
| `plan_tier` | str | 0 |
| `seats` | int64 | 0 |
| `mrr_amount` | int64 | 0 |
| `arr_amount` | int64 | 0 |
| `is_trial` | bool | 0 |
| `upgrade_flag` | bool | 0 |
| `downgrade_flag` | bool | 0 |
| `churn_flag` | bool | 0 |
| `billing_frequency` | str | 0 |
| `auto_renew_flag` | bool | 0 |

- Registros: 5000; colunas: 14.

### ravenstack_feature_usage.csv

| Coluna | Tipo (pandas) | Nulos |
|---|---|---|
| `usage_id` | str | 0 |
| `subscription_id` | str | 0 |
| `usage_date` | str | 0 |
| `feature_name` | str | 0 |
| `usage_count` | int64 | 0 |
| `usage_duration_secs` | int64 | 0 |
| `error_count` | int64 | 0 |
| `is_beta_feature` | bool | 0 |

- Registros: 25000; colunas: 8.

### ravenstack_support_tickets.csv

| Coluna | Tipo (pandas) | Nulos |
|---|---|---|
| `ticket_id` | str | 0 |
| `account_id` | str | 0 |
| `submitted_at` | str | 0 |
| `closed_at` | str | 0 |
| `resolution_time_hours` | float64 | 0 |
| `priority` | str | 0 |
| `first_response_time_minutes` | int64 | 0 |
| `satisfaction_score` | float64 | 825 |
| `escalation_flag` | bool | 0 |

- Registros: 2000; colunas: 9.

### ravenstack_churn_events.csv

| Coluna | Tipo (pandas) | Nulos |
|---|---|---|
| `churn_event_id` | str | 0 |
| `account_id` | str | 0 |
| `churn_date` | str | 0 |
| `reason_code` | str | 0 |
| `refund_amount_usd` | float64 | 0 |
| `preceding_upgrade_flag` | bool | 0 |
| `preceding_downgrade_flag` | bool | 0 |
| `is_reactivation` | bool | 0 |
| `feedback_text` | str | 148 |

- Registros: 600; colunas: 9.

## 4. Checks executados

| ID | Escopo | Check | Veredito | Detalhe |
|---|---|---|---|---|
| F01-ravenstack_accounts.csv | ravenstack_accounts.csv | arquivo presente e carregável | **PASS** | 36148 bytes, CSV parseado |
| F02-ravenstack_accounts.csv | ravenstack_accounts.csv | contagem de registros = valor do brief | **PASS** | 500 registros (brief: ~500) |
| F01-ravenstack_subscriptions.csv | ravenstack_subscriptions.csv | arquivo presente e carregável | **PASS** | 432565 bytes, CSV parseado |
| F02-ravenstack_subscriptions.csv | ravenstack_subscriptions.csv | contagem de registros = valor do brief | **PASS** | 5000 registros (brief: ~5000) |
| F01-ravenstack_feature_usage.csv | ravenstack_feature_usage.csv | arquivo presente e carregável | **PASS** | 1375897 bytes, CSV parseado |
| F02-ravenstack_feature_usage.csv | ravenstack_feature_usage.csv | contagem de registros = valor do brief | **PASS** | 25000 registros (brief: ~25000) |
| F01-ravenstack_support_tickets.csv | ravenstack_support_tickets.csv | arquivo presente e carregável | **PASS** | 143597 bytes, CSV parseado |
| F02-ravenstack_support_tickets.csv | ravenstack_support_tickets.csv | contagem de registros = valor do brief | **PASS** | 2000 registros (brief: ~2000) |
| F01-ravenstack_churn_events.csv | ravenstack_churn_events.csv | arquivo presente e carregável | **PASS** | 44029 bytes, CSV parseado |
| F02-ravenstack_churn_events.csv | ravenstack_churn_events.csv | contagem de registros = valor do brief | **PASS** | 600 registros (brief: ~600) |
| S01-ravenstack_accounts.csv | ravenstack_accounts.csv | schema mínimo (colunas do brief) | **PASS** | 10 colunas, ordem idêntica ao brief |
| S02-ravenstack_accounts.csv | ravenstack_accounts.csv | chave candidata account_id sem nulos | **PASS** | 0 nulos |
| S03-ravenstack_accounts.csv | ravenstack_accounts.csv | chave candidata account_id sem duplicatas | **PASS** | 0 duplicatas |
| S04-ravenstack_accounts.csv | ravenstack_accounts.csv | linhas exatamente duplicadas | **PASS** | 0 linhas duplicadas |
| S05-ravenstack_accounts.csv | ravenstack_accounts.csv | nulos por coluna (não-chave) | **PASS** | 0 nulos em todas as colunas |
| T01-ravenstack_accounts.csv | ravenstack_accounts.csv | seats > 0 | **PASS** | 0 violações |
| T02-ravenstack_accounts.csv | ravenstack_accounts.csv | domínio de industry | **PASS** | 5 valores válidos |
| T02-ravenstack_accounts.csv | ravenstack_accounts.csv | domínio de country | **PASS** | 7 valores válidos |
| T02-ravenstack_accounts.csv | ravenstack_accounts.csv | domínio de referral_source | **PASS** | 5 valores válidos |
| T02-ravenstack_accounts.csv | ravenstack_accounts.csv | domínio de plan_tier | **PASS** | 3 valores válidos |
| I01-ravenstack_accounts.csv | ravenstack_accounts.csv | IDs no padrão <PREFIXO>-<6 hex> | **PASS** | 0 violações em 1 coluna(s) de ID |
| D01-ravenstack_accounts.csv | ravenstack_accounts.csv | signup_date parseável (YYYY-MM-DD) | **PASS** | 0 valores não parseáveis |
| D02-ravenstack_accounts.csv | ravenstack_accounts.csv | janela global de datas dentro de 2023-01-01..2024-12-31 | **PASS** | 0 valores fora da janela; signup_date: 2023-01-02..2024-12-31 |
| S01-ravenstack_subscriptions.csv | ravenstack_subscriptions.csv | schema mínimo (colunas do brief) | **PASS** | 14 colunas, ordem idêntica ao brief |
| S02-ravenstack_subscriptions.csv | ravenstack_subscriptions.csv | chave candidata subscription_id sem nulos | **PASS** | 0 nulos |
| S03-ravenstack_subscriptions.csv | ravenstack_subscriptions.csv | chave candidata subscription_id sem duplicatas | **PASS** | 0 duplicatas |
| S04-ravenstack_subscriptions.csv | ravenstack_subscriptions.csv | linhas exatamente duplicadas | **PASS** | 0 linhas duplicadas |
| S05-ravenstack_subscriptions.csv | ravenstack_subscriptions.csv | nulos por coluna (não-chave) | **PASS** | end_date=4514 (90.3%) [esperado (semântica: assinatura ativa)] |
| T01-ravenstack_subscriptions.csv | ravenstack_subscriptions.csv | seats > 0, mrr >= 0, arr >= 0 | **PASS** | violações: seats<=0=0, mrr<0=0, arr<0=0 |
| T03-ravenstack_subscriptions.csv | ravenstack_subscriptions.csv | ARR = 12 x MRR (invariante de unidade) | **PASS** | 0 violações em 4222 linhas com MRR>0 |
| T02-ravenstack_subscriptions.csv | ravenstack_subscriptions.csv | domínios plan_tier e billing_frequency | **PASS** | plan_tier fora: []; billing_frequency fora: [] |
| I01-ravenstack_subscriptions.csv | ravenstack_subscriptions.csv | IDs no padrão <PREFIXO>-<6 hex> | **PASS** | 0 violações em 2 coluna(s) de ID |
| D01-ravenstack_subscriptions.csv | ravenstack_subscriptions.csv | start_date/end_date parseáveis | **PASS** | 0 valores não parseáveis (end_date nulo é semântica de assinatura ativa: 4514) |
| D03-ravenstack_subscriptions.csv | ravenstack_subscriptions.csv | end_date >= start_date (quando presente) | **PASS** | 0 violações |
| D04-ravenstack_subscriptions.csv | ravenstack_subscriptions.csv | flags vs datas: churn_flag consistente com end_date | **PASS** | 0 linhas inconsistentes (churn sem end_date ou end_date sem churn); ativas=4514 |
| D02-ravenstack_subscriptions.csv | ravenstack_subscriptions.csv | janela global de datas dentro de 2023-01-01..2024-12-31 | **PASS** | 0 valores fora da janela; start_date: 2023-01-09..2024-12-31; end_date: 2023-04-05..2024-12-31 |
| S01-ravenstack_feature_usage.csv | ravenstack_feature_usage.csv | schema mínimo (colunas do brief) | **PASS** | 8 colunas, ordem idêntica ao brief |
| S02-ravenstack_feature_usage.csv | ravenstack_feature_usage.csv | chave candidata usage_id sem nulos | **PASS** | 0 nulos |
| S03-ravenstack_feature_usage.csv | ravenstack_feature_usage.csv | chave candidata usage_id sem duplicatas | **WARN** | 21 ids duplicados (anomalia de qualidade; join não afetado) |
| S04-ravenstack_feature_usage.csv | ravenstack_feature_usage.csv | linhas exatamente duplicadas | **PASS** | 0 linhas duplicadas |
| S05-ravenstack_feature_usage.csv | ravenstack_feature_usage.csv | nulos por coluna (não-chave) | **PASS** | 0 nulos em todas as colunas |
| T01-ravenstack_feature_usage.csv | ravenstack_feature_usage.csv | usage_count/duration/error >= 0 | **PASS** | violações: count<0=0, duration<0=0, error<0=0 |
| T04-ravenstack_feature_usage.csv | ravenstack_feature_usage.csv | error_count <= usage_count (consistência lógica) | **WARN** | 17 linhas com erro_count > usage_count |
| T05-ravenstack_feature_usage.csv | ravenstack_feature_usage.csv | usage_count > 0 (linha de uso com contagem) | **WARN** | 2 linhas com usage_count = 0 |
| I01-ravenstack_feature_usage.csv | ravenstack_feature_usage.csv | IDs no padrão <PREFIXO>-<6 hex> | **PASS** | 0 violações em 2 coluna(s) de ID |
| D01-ravenstack_feature_usage.csv | ravenstack_feature_usage.csv | usage_date parseável | **PASS** | 0 valores não parseáveis |
| D02-ravenstack_feature_usage.csv | ravenstack_feature_usage.csv | janela global de datas dentro de 2023-01-01..2024-12-31 | **PASS** | 0 valores fora da janela; usage_date: 2023-01-01..2024-12-31 |
| S01-ravenstack_support_tickets.csv | ravenstack_support_tickets.csv | schema mínimo (colunas do brief) | **PASS** | 9 colunas, ordem idêntica ao brief |
| S02-ravenstack_support_tickets.csv | ravenstack_support_tickets.csv | chave candidata ticket_id sem nulos | **PASS** | 0 nulos |
| S03-ravenstack_support_tickets.csv | ravenstack_support_tickets.csv | chave candidata ticket_id sem duplicatas | **PASS** | 0 duplicatas |
| S04-ravenstack_support_tickets.csv | ravenstack_support_tickets.csv | linhas exatamente duplicadas | **PASS** | 0 linhas duplicadas |
| S05-ravenstack_support_tickets.csv | ravenstack_support_tickets.csv | nulos por coluna (não-chave) | **WARN** | satisfaction_score=825 (41.2%) [WARN] |
| T01-ravenstack_support_tickets.csv | ravenstack_support_tickets.csv | resolution_time_hours/first_response >= 0 | **PASS** | violações: res<0=0, frt<0=0 |
| T06-ravenstack_support_tickets.csv | ravenstack_support_tickets.csv | CSAT nulo ou fora do domínio 1-5 | **WARN** | nulos=825 (41.2%); valores fora de [1,5]=0; valores observados=[3.0, 4.0, 5.0] |
| T02-ravenstack_support_tickets.csv | ravenstack_support_tickets.csv | domínio de priority | **PASS** | 4 valores válidos |
| I01-ravenstack_support_tickets.csv | ravenstack_support_tickets.csv | IDs no padrão <PREFIXO>-<6 hex> | **PASS** | 0 violações em 2 coluna(s) de ID |
| D01-ravenstack_support_tickets.csv | ravenstack_support_tickets.csv | submitted_at/closed_at parseáveis | **PASS** | 0 valores não parseáveis |
| D03-ravenstack_support_tickets.csv | ravenstack_support_tickets.csv | closed_at >= submitted_at | **PASS** | 0 violações |
| D05-ravenstack_support_tickets.csv | ravenstack_support_tickets.csv | resolution_time_hours <= tempo decorrido real | **PASS** | 0 violações |
| D02-ravenstack_support_tickets.csv | ravenstack_support_tickets.csv | janela global de datas dentro de 2023-01-01..2024-12-31 | **PASS** | 0 valores fora da janela; submitted_at: 2023-01-02..2024-12-31; closed_at: 2023-01-03..2024-12-31 |
| S01-ravenstack_churn_events.csv | ravenstack_churn_events.csv | schema mínimo (colunas do brief) | **PASS** | 9 colunas, ordem idêntica ao brief |
| S02-ravenstack_churn_events.csv | ravenstack_churn_events.csv | chave candidata churn_event_id sem nulos | **PASS** | 0 nulos |
| S03-ravenstack_churn_events.csv | ravenstack_churn_events.csv | chave candidata churn_event_id sem duplicatas | **PASS** | 0 duplicatas |
| S04-ravenstack_churn_events.csv | ravenstack_churn_events.csv | linhas exatamente duplicadas | **PASS** | 0 linhas duplicadas |
| S05-ravenstack_churn_events.csv | ravenstack_churn_events.csv | nulos por coluna (não-chave) | **WARN** | feedback_text=148 (24.7%) [WARN] |
| T01-ravenstack_churn_events.csv | ravenstack_churn_events.csv | refund_amount_usd >= 0 | **PASS** | 0 violações |
| T02-ravenstack_churn_events.csv | ravenstack_churn_events.csv | domínio de reason_code | **PASS** | 6 valores válidos |
| I01-ravenstack_churn_events.csv | ravenstack_churn_events.csv | IDs no padrão <PREFIXO>-<6 hex> | **PASS** | 0 violações em 2 coluna(s) de ID |
| D01-ravenstack_churn_events.csv | ravenstack_churn_events.csv | churn_date parseável | **PASS** | 0 valores não parseáveis |
| D02-ravenstack_churn_events.csv | ravenstack_churn_events.csv | janela global de datas dentro de 2023-01-01..2024-12-31 | **PASS** | 0 valores fora da janela; churn_date: 2023-01-25..2024-12-31 |
| K01-subscriptions | subscriptions -> accounts | FK account_id sem órfãos | **PASS** | 0 órfãos |
| K02-tickets | tickets -> accounts | FK account_id sem órfãos | **PASS** | 0 órfãos |
| K03-churn | churn_events -> accounts | FK account_id sem órfãos | **PASS** | 0 órfãos |
| K04-usage | feature_usage -> subscriptions | FK subscription_id sem órfãos | **PASS** | 0 órfãos |
| K05-usage | subscriptions -> feature_usage | assinaturas com registro de uso (sem 'assinatura sem uso') | **WARN** | 33 assinaturas sem nenhuma linha de uso |
| D06-churn | churn_events vs accounts | churn_date >= signup_date da conta | **PASS** | 0 eventos de churn anteriores ao signup |
| D07-tickets | tickets vs accounts | submitted_at >= signup_date da conta | **WARN** | 1077 tickets abertos antes do signup |
| D08-usage | feature_usage vs accounts | usage_date >= signup_date da conta | **WARN** | 13198 linhas de uso anteriores ao signup da conta |
| D09-usage | feature_usage vs subscriptions | usage_date dentro da janela da assinatura | **WARN** | antes do início=19142 (76.6%), depois do fim=290, dentro da janela=5568 (22.3%) |
| D10-churn | churn_events vs subscriptions | churn_date >= primeira start_date da conta | **WARN** | 53 eventos de churn anteriores à primeira assinatura |
| D11-churn | churn_events vs subscriptions | churn_date <= última end_date (contas com assinatura encerrada) | **WARN** | 90 eventos de churn posteriores à última end_date |
| C01-churn | accounts.churn_flag vs churn_events | flag de churn da conta consistente com eventos de churn | **WARN** | contas com flag sem evento=35; contas com evento sem flag=277 (flag=True=110, contas com evento=352, eventos=600) |
| C02-churn | subscriptions.churn_flag vs churn_events | contas com evento de churn têm assinatura churn_flag | **WARN** | 125 contas com evento sem assinatura churn_flag (assinaturas churn_flag=312) |
| C03-churn | churn_events | múltiplos eventos por conta (ciclos de reativação) | **PASS** | 175 contas com >1 evento (máx 5); eventos is_reactivation=61 (55 contas) — insumo da Iteração 02 |
| C04-churn | churn_events | sem eventos duplicados por conta+data | **WARN** | 1 pares conta+data duplicados |
| C05-churn | churn_events | reason_code 'unknown' sem feedback preenchido | **WARN** | 22 eventos 'unknown' sem feedback (feedback nulo total=148) |
| C06-churn | churn_events | refund_amount_usd > 0 apenas onde há reembolso | **PASS** | 142 eventos com refund > 0; 458 com 0 |
| C07-subs | subscriptions | trial => MRR 0; não-trial => MRR > 0 | **PASS** | trial com MRR>0=0; não-trial com MRR=0=0 (trial=778) |
| C08-subs | subscriptions | upgrade_flag e downgrade_flag mutuamente exclusivos | **WARN** | 23 linhas com ambas as flags (upgrade=529, downgrade=218) |
| C09-subs | accounts vs subscriptions | atributos de conta (seats/plano) coerentes com histórico de assinaturas | **WARN** | seats da conta != máx. seats de assinatura: 439; plano da conta != moda de plano de assinatura: 363 (accounts é snapshot atual; assinaturas são histórico — registrar, não concluir) |

## 5. Parecer de sinteticidade (evidência objetiva)

Os padrões abaixo são observações de estrutura/distribuição dos arquivos — **não** extrapolam causa de negócio e **não** escolhem definição de churn (Iteração 02). Em conjunto, são consistentes com base **gerada sinteticamente**:

| Aspecto | Observação |
|---|---|
| accounts.industry — distribuição (contagem) | Cybersecurity=100; DevTools=113; EdTech=79; FinTech=112; HealthTech=96 |
| accounts.country — distribuição (contagem) | AU=32; CA=23; DE=25; FR=22; IN=49; UK=58; US=291 |
| accounts.referral_source — distribuição (contagem) | ads=98; event=96; organic=114; other=103; partner=89 |
| accounts.plan_tier — distribuição (contagem) | Basic=168; Enterprise=154; Pro=178 |
| subscriptions.plan_tier — distribuição (contagem) | Basic=1602; Enterprise=1723; Pro=1675 |
| subscriptions.billing_frequency — distribuição (contagem) | annual=2461; monthly=2539 |
| subscriptions.mrr — estrutura | mrr=0 => trial (778); ARR=12xMRR em 100% das linhas com MRR>0 |
| feature_usage.usage_date — distribuição por ano | 2023=12430; 2024=12570 |
| feature_usage.usage_date — uniformidade mensal (24 meses) | min por mês=944, máx=1137, média=1041.67 |
| feature_usage.usage_id — ids duplicados | 21 ids reutilizados em linhas distintas (mesmo id; assinaturas diferentes em 21/21; features diferentes em 19/21) |
| tickets.satisfaction_score — distribuição | nulos=825 (41.2%); valores=[3.0, 4.0, 5.0] |
| tickets.priority — distribuição (contagem) | high=510; low=485; medium=491; urgent=514 |
| churn_events.reason_code — distribuição (contagem) | budget=104; competitor=92; features=114; pricing=91; support=104; unknown=95 |
| churn_events.churn_date — distribuição mensal | meses=23, min por mês=1, máx=117 |
| churn_events por conta — multiplicidade | contas=352, eventos=600, contas com >1 evento=175, máx=5 |
| feature_usage vs subscriptions — uso fora da janela da assinatura | 19142 de 25000 linhas (76.6%) com usage_date anterior ao start_date (assinaturas com início em 2024: 4334 de 5000) |

## 6. Limitações da auditoria

- **Sem semântica externa:** não há fonte externa para validar valores reais de MRR, CSAT, tempos de resolução etc.; a auditoria valida consistência interna e domínios declarados, não verdade de negócio.
- **`accounts` como snapshot:** divergências entre atributos da conta (seats/plano) e o histórico de assinaturas são registradas (C09) sem julgar qual fonte é canônica — decisão da Iteração 02.
- **Flags de churn divergentes entre fontes:** a divergência entre `churn_flag` (accounts/subscriptions) e `churn_events` é quantificada (C01/C02) e **não** resolvida aqui; a reconciliação é o objeto da Iteração 02.
- **Anomalias temporais:** uso/eventos fora da janela esperada são registrados (D06–D11) como anomalias de qualidade; nenhuma interpretação causal é feita nesta etapa.
- **Ferramenta:** auditoria usa pandas sobre os CSVs commitados; sem rede, sem dependências além de `pandas` (ver `requirements.txt`).

## 7. Proveniência

- Script: `solution/src/01_ingest_audit.py` (executado de `submissions/jose-nascimento/`).
- Dados: `solution/data/raw/ravenstack_*.csv` (MD5 no `data/raw/README.md`).
- Este relatório: `solution/evidence/01_audit_report.md` (regenerado a cada execução).
- Python/pandas: versões registradas na execução (ver report de processo).
