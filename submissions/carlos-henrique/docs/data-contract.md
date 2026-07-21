# Contrato de dados — Fases 1 e 2

> **Status geral:** `VALIDATED_WITH_WARNINGS`. As cinco fontes foram auditadas e a camada temporal foi implementada com identidade determinística, provenance, quarentena e reconciliação zero. Eventos ativos continuam sujeitos aos warnings e cutoffs descritos neste contrato.

## Inventário validado

| Tabela | Arquivo real | Registros | Granularidade observada | Chave | Chaves estrangeiras | Campos temporais | Status |
|---|---|---:|---|---|---|---|---|
| Contas | `ravenstack_accounts.csv` | 500 | uma linha por `account_id` no snapshot | `account_id` — `CANDIDATE` | nenhuma | `signup_date` | `VALIDATED_WITH_WARNINGS` |
| Assinaturas | `ravenstack_subscriptions.csv` | 5.000 | uma linha por `subscription_id` no snapshot | `subscription_id` — `CANDIDATE` | `account_id` → contas | `start_date`, `end_date` | `VALIDATED_WITH_WARNINGS` |
| Uso de funcionalidades | `ravenstack_feature_usage.csv` | 25.000 | evento de uso; identidade definitiva não provada | `usage_id` — `INVALID`; composto testado — `INVALID` | `subscription_id` → assinaturas | `usage_date` | `INCONCLUSIVE` |
| Tickets de suporte | `ravenstack_support_tickets.csv` | 2.000 | uma linha por `ticket_id` no snapshot | `ticket_id` — `CANDIDATE` | `account_id` → contas | `submitted_at`, `closed_at` | `VALIDATED_WITH_WARNINGS` |
| Eventos de churn | `ravenstack_churn_events.csv` | 600 | uma linha por `churn_event_id` no snapshot | `churn_event_id` — `CANDIDATE` | `account_id` → contas | `churn_date` | `VALIDATED_WITH_WARNINGS` |

`CANDIDATE` significa completo e único neste snapshot. Estabilidade entre snapshots depende de evidência de governança da fonte.

## Contrato por tabela

### Contas

- **Arquivo:** `ravenstack_accounts.csv`.
- **Registros/colunas:** 500/10; nenhuma linha completamente duplicada.
- **Campos:** `account_id` (str), `account_name` (str), `industry` (str), `country` (str), `signup_date` (str), `referral_source` (str), `plan_tier` (str), `seats` (int64), `is_trial` (bool), `churn_flag` (bool).
- **Granularidade/chave:** uma conta por `account_id`; 500 valores não nulos e únicos.
- **Temporal:** `signup_date`, formato `YYYY-MM-DD`, intervalo 2023-01-02 a 2024-12-31, sem inválidos e sem timezone declarado.
- **Financeiro:** nenhum campo monetário; `seats` é medida operacional.
- **Texto:** `account_name`; somente estatísticas agregadas podem sair da zona bruta.
- **Leakage:** `churn_flag` é explícito e proibido como feature anterior ao churn.
- **Qualidade:** 277 contas têm evento de churn com flag falsa; 35 têm flag verdadeira sem evento.
- **Status:** `VALIDATED_WITH_WARNINGS`.

### Assinaturas

- **Arquivo:** `ravenstack_subscriptions.csv`.
- **Registros/colunas:** 5.000/14; nenhuma linha completamente duplicada.
- **Campos:** `subscription_id`, `account_id`, `start_date`, `end_date`, `plan_tier`, `seats`, `mrr_amount`, `arr_amount`, `is_trial`, `upgrade_flag`, `downgrade_flag`, `churn_flag`, `billing_frequency`, `auto_renew_flag`.
- **Granularidade/chave:** uma assinatura por `subscription_id`; completa e única no snapshot.
- **Relacionamento:** `account_id` cobre 100% das linhas; zero órfãos; 2–19 assinaturas por conta, mediana 10.
- **Temporal:** `start_date` e `end_date`; 4.514 `end_date` ausentes; datas válidas, sem end anterior ao start.
- **Financeiro:** `mrr_amount` e `arr_amount`; zero valores negativos e zero divergências de `ARR = MRR × 12` no snapshot.
- **Texto:** nenhum texto livre.
- **Leakage:** `churn_flag` é explícito; `end_date` é proxy; demais campos exigem corte as-of quando mutáveis.
- **Qualidade:** relação um-para-muitos infla o grão de contas em 10× se unida sem agregação.
- **Status:** `VALIDATED_WITH_WARNINGS`.

### Uso de funcionalidades

- **Arquivo:** `ravenstack_feature_usage.csv`.
- **Registros/colunas:** 25.000/8; nenhuma linha completamente duplicada.
- **Campos:** `usage_id`, `subscription_id`, `usage_date`, `feature_name`, `usage_count`, `usage_duration_secs`, `error_count`, `is_beta_feature`.
- **Granularidade/chave:** `usage_id` tem 21 duplicatas excedentes/42 linhas afetadas; o composto `subscription_id + usage_date + feature_name` tem 3 excedentes/6 linhas afetadas. Identidade final `INCONCLUSIVE`.
- **Relacionamento:** `subscription_id` cobre 100% das linhas; zero órfãos; 33 assinaturas sem uso; 0–16 eventos por assinatura, mediana 5.
- **Temporal:** `usage_date`, formato `YYYY-MM-DD`, 2023-01-01 a 2024-12-31, sem inválidos; 19.142 registros (76,568%) antecedem o início da assinatura e 290 (1,16%) sucedem o fim.
- **Financeiro/texto:** sem campo monetário ou texto livre; `feature_name` é categórico.
- **Leakage:** `usage_date` e medidas somente podem ser usados com corte as-of e vínculo temporal válido.
- **Qualidade:** identidade duplicada e cronologia incompatível exigem quarentena ou regra explícita na Fase 2.
- **Status:** `INCONCLUSIVE` para a chave; `VALIDATED_WITH_WARNINGS` para schema e relacionamento.

### Tickets de suporte

- **Arquivo:** `ravenstack_support_tickets.csv`.
- **Registros/colunas:** 2.000/9; nenhuma linha completamente duplicada.
- **Campos:** `ticket_id`, `account_id`, `submitted_at`, `closed_at`, `resolution_time_hours`, `priority`, `first_response_time_minutes`, `satisfaction_score`, `escalation_flag`.
- **Granularidade/chave:** uma linha por `ticket_id`; completa e única no snapshot.
- **Relacionamento:** `account_id` cobre 100% das linhas; zero órfãos; 8 contas sem ticket; 0–11 tickets por conta, mediana 4.
- **Temporal:** `submitted_at` é data e `closed_at` é datetime sem timezone declarado; zero datas inválidas e zero encerramentos anteriores à abertura.
- **Financeiro/texto:** sem campos monetários e sem texto livre no schema real.
- **Leakage:** fechamento, duração, primeira resposta, satisfação e escalonamento dependem do tempo de disponibilidade e exigem corte as-of.
- **Qualidade:** 825 valores de satisfação ausentes; 1.077 tickets (53,85%) antecedem o signup; 386 de 1.395 tickets em contas com churn ocorrem após o primeiro churn e são ocorrências a investigar.
- **Status:** `VALIDATED_WITH_WARNINGS`.

### Eventos de churn

- **Arquivo:** `ravenstack_churn_events.csv`.
- **Registros/colunas:** 600/9; nenhuma linha completamente duplicada.
- **Campos:** `churn_event_id`, `account_id`, `churn_date`, `reason_code`, `refund_amount_usd`, `preceding_upgrade_flag`, `preceding_downgrade_flag`, `is_reactivation`, `feedback_text`.
- **Granularidade/chave:** um evento por `churn_event_id`; completa e única no snapshot.
- **Relacionamento:** `account_id` cobre 100% das linhas; zero órfãos; 0–5 eventos por conta, mediana 1.
- **Temporal:** `churn_date`, formato `YYYY-MM-DD`, 2023-01-25 a 2024-12-31, sem inválidos; 53 eventos (8,8333%) antecedem a primeira assinatura; 55 não encontram assinatura ativa.
- **Financeiro:** `refund_amount_usd`, sem valores negativos.
- **Texto:** `feedback_text`, 148 ausentes; nenhum texto bruto é reproduzido nos artefatos.
- **Leakage:** todos os campos da tabela, exceto a identidade relacional usada para auditoria, são proibidos como features anteriores ao desfecho.
- **Qualidade:** 148 contas sem churn, 177 com um evento e 175 com múltiplos; máximo 5; 61 eventos têm reativação explícita.
- **Status:** `VALIDATED_WITH_WARNINGS`.

## Relacionamentos e política de join

As quatro relações mínimas têm taxa de match de 100%, zero chaves estrangeiras nulas e zero órfãos. Todas são um-para-muitos e `UNSAFE_WITHOUT_AGGREGATION`. Simulações key-only mediram multiplicadores de 10×, 5,0066×, 4,016× e 1,496×. O encadeamento ingênuo alcançou 147.896 linhas a partir de 500 contas (295,792×).

É proibido materializar uma mega-tabela. A Fase 2 deve normalizar eventos por fonte e unir somente dimensões ou agregados as-of no grão explicitamente escolhido.

## Testes obrigatórios recorrentes

1. unicidade e não nulidade das chaves candidatas;
2. duplicidade de `usage_id` e do composto de uso;
3. integridade referencial e taxa de match;
4. missingness, strings vazias e sentinelas;
5. domínios, valores negativos e reconciliação financeira;
6. parsing, intervalos e ordem temporal;
7. inflação de joins e preservação de entidades;
8. conflitos entre flags de churn e eventos;
9. leakage por disponibilidade temporal;
10. regex agregada de privacidade sem reprodução de texto;
11. churn recorrente e reativação.

## Gate para a Fase 2

**`PASS_WITH_WARNINGS`**. Chaves relacionais, cobertura e campos temporais permitem construir um event log, desde que a Fase 2: defina identidade substituta para uso; não use `accounts.churn_flag` como fonte soberana sem regra de precedência; mantenha fontes em grãos separados; aplique corte as-of; marque ou coloque em quarentena eventos temporalmente impossíveis; e preserve churn recorrente e reativação sem colapsá-los.

---

## Camada temporal canônica — Fase 2

### Event log ativo

- **Arquivo:** `solution/data/processed/event_log.parquet`.
- **Registros/colunas:** 13.927/28.
- **Período:** 2023-01-01 00:00:00 a 2024-12-31 19:00:00.
- **Grão:** uma ocorrência de evento de origem temporalmente utilizável.
- **Chave:** `event_id`, hash SHA-256 determinístico truncado, único neste build.
- **Timezone:** `NAIVE_SOURCE_TIME`; datas sem hora usam meia-noite como representação técnica.

| Campo | Tipo lógico | Nulabilidade | Regra |
|---|---|---|---|
| `event_id` | string | não nulo | identidade determinística por fonte, registro, linha, tipo e tempo |
| `account_id` | string | não nulo no ativo | entidade obrigatória e provenance relacional |
| `subscription_id` | string | opcional | preenchido somente para eventos de assinatura/uso |
| `event_time` | datetime64[ns] | não nulo no ativo | timestamp canônico da fonte |
| `event_type` | enum | não nulo | um dos oito tipos implementados |
| `event_subtype` | string controlada | opcional | subtipo categórico, nunca texto livre |
| `event_value_numeric` | float | opcional | MRR no início, uso ou satisfação no momento permitido |
| `event_value_category` | string controlada | opcional | plano, funcionalidade, prioridade ou escalonamento |
| `source_table` | enum | não nulo | tabela oficial de origem |
| `source_record_id` | string | não nulo no ativo | ID preservado do registro original |
| `source_row_number` | int | não nulo | linha física do CSV, com cabeçalho na linha 1 |
| `derivation_type` | enum | não nulo | `SOURCE`; nenhum evento comportamental derivado nesta fase |
| `derivation_rule` | string controlada | não nulo | regra versionada de geração |
| `quality_status` | enum | não nulo | `VALID` ou `VALID_WITH_WARNING` no log ativo |
| `quality_flags` | string delimitada | opcional | flags ordenadas por `|` |
| `is_quarantined` | bool | não nulo | sempre falso no log ativo |
| `is_post_churn` | bool | não nulo | evento estritamente posterior ao primeiro churn utilizável |
| `is_pre_subscription` | bool | não nulo | uso anterior ao episódio; somente verdadeiro na quarentena |
| `is_post_subscription` | bool | não nulo | uso posterior ao episódio; somente verdadeiro na quarentena |
| `episode_id` | string | opcional | vínculo determinístico para assinatura/uso |
| `event_order_on_same_day` | int | não nulo | desempate técnico não causal |
| `candidate_subscription_id` | string | opcional | somente `EXACT_ACTIVE_MATCH` para churn/reativação |
| `churn_assignment_status` | enum | opcional | resultado conservador da atribuição |
| `churn_sequence_number` | int | opcional | ordem de churn por conta |
| `reactivation_sequence_number` | int | opcional | ordem de reativação explícita por conta |
| `previous_churn_time` | datetime64[ns] | opcional | churn anterior utilizável |
| `next_churn_time` | datetime64[ns] | opcional | próximo churn observado |
| `days_since_previous_churn` | int | opcional | diferença calendária sem inferência causal |

### Tipos implementados

`ACCOUNT_CREATED`, `SUBSCRIPTION_STARTED`, `SUBSCRIPTION_ENDED`, `FEATURE_USED`, `SUPPORT_TICKET_OPENED`, `SUPPORT_TICKET_CLOSED`, `CHURN_RECORDED` e `REACTIVATION_RECORDED`.

Não foram implementados upgrade, downgrade, satisfação separada, inatividade ou variação de uso porque não há timestamp inequívoco ou necessidade estrutural nesta fase.

### Quarentena

- **Arquivo:** `solution/data/processed/quarantined_events.parquet`.
- **Registros/colunas:** 21.659/28.
- **Schema:** idêntico ao event log; `quality_status=QUARANTINED` e `is_quarantined=true`.
- **Regra:** preservar eventos com erro fatal sem permitir seu uso analítico como cronologia válida.

Erros fatais incluem ID obrigatório ausente, timestamp inválido, evento pré-conta, uso pré/pós-assinatura, fim anterior ao início, fechamento anterior à abertura, churn anterior à primeira assinatura e reativação sem churn anterior utilizável.

### Episódios de assinatura

- **Arquivo:** `solution/data/processed/subscription_episodes.parquet`.
- **Registros/colunas:** 5.000/16.
- **Grão:** uma linha por `subscription_id`; assinaturas nunca são fundidas automaticamente.

| Campo | Regra |
|---|---|
| `episode_id` | hash determinístico de conta e assinatura |
| `account_id`, `subscription_id` | identidades de origem |
| `episode_start`, `episode_end` | datas preservadas da assinatura |
| `episode_status` | `OPEN` ou `CLOSED` conforme `end_date` |
| `plan`, `mrr` | atributos do episódio, sem texto livre |
| `previous_subscription_id`, `next_subscription_id` | ordem temporal na mesma conta, sem fusão |
| `is_post_churn_start` | início estritamente após churn anterior |
| `has_churn_during_episode` | churn de conta dentro do intervalo |
| `has_reactivation_during_episode` | reativação explícita dentro do intervalo |
| `has_overlap` | outra assinatura da conta cruza o intervalo |
| `quality_status`, `quality_flags` | qualidade do episódio |

Há 4.514 episódios abertos, 486 encerrados e 4.992 episódios afetados por sobreposição. Sobreposição é warning; churn não encerra assinatura automaticamente.

## Provenance e identidade

1. `source_table`, `source_record_id` e `source_row_number` rastreiam cada evento ao CSV.
2. `event_id` inclui a linha física para preservar registros distintos com o mesmo ID de origem.
3. `derivation_rule` documenta a transformação; todos os tipos implementados são `SOURCE`.
4. `episode_id` não substitui `subscription_id`; é uma identidade técnica estável.
5. Nenhum nome, feedback, motivo, refund ou texto completo é copiado.

## Quality statuses e flags

- `VALID`: sem anomalia sustentada;
- `VALID_WITH_WARNING`: utilizável somente com filtro e interpretação documentados;
- `QUARANTINED`: preservado para auditoria, proibido em cronologia analítica válida.

Flags observadas: `PRE_ACCOUNT_EVENT`, `PRE_SUBSCRIPTION_USAGE`, `POST_SUBSCRIPTION_USAGE`, `CHURN_BEFORE_FIRST_SUBSCRIPTION`, `CHURN_WITHOUT_ACTIVE_SUBSCRIPTION`, `DUPLICATE_SOURCE_ID`, `DUPLICATE_CANDIDATE_KEY`, `MULTIPLE_ACTIVE_SUBSCRIPTIONS`, `AMBIGUOUS_CHURN_SUBSCRIPTION`, `POST_CHURN_EVENT`, `REACTIVATION_WITHOUT_PRIOR_CHURN` e `SAME_DAY_ORDER_ASSIGNED`.

## Reconciliação da camada temporal

| Métrica | Resultado |
|---|---:|
| registros de origem | 33.100 |
| oportunidades de evento | 35.586 |
| eventos gerados | 35.586 |
| eventos válidos | 10.703 |
| eventos com warning | 3.224 |
| eventos em quarentena | 21.659 |
| duplicatas exatas removidas | 0 |
| diferença não explicada | 0 |

O denominador é oportunidade de evento porque assinatura e ticket podem produzir dois tipos temporais. Todos os detalhes por fonte estão em `reconciliation_report.json`.

## Uso permitido

- reconstruir jornadas usando o log ativo e qualidade explícita;
- analisar churn recorrente e reativação como eventos separados;
- aplicar cutoffs as-of e filtros por `quality_status`/`quality_flags`;
- usar atribuição a assinatura apenas quando `EXACT_ACTIVE_MATCH`.

## Uso proibido

- usar quarentena como sequência válida ou remover suas ocorrências silenciosamente;
- tratar desempate no mesmo dia como causal ou intradiário;
- usar churn flags snapshot, motivo, refund, feedback ou end date antes de disponíveis;
- atribuir churn a múltiplas assinaturas ou criar assinatura ausente;
- colapsar churn recorrente, reativação ou duplicatas distintas;
- materializar mega-join ou produzir diagnóstico nesta fase.

## Gate para a Fase 3

**`PASS_WITH_WARNINGS`**. Event log e episódios estão reconciliados, auditáveis e reproduzíveis. Diagnósticos futuros devem excluir quarentena, respeitar warnings, declarar cutoffs e preservar a semântica de conta versus assinatura.

---

## Contrato analítico — Fase 3

### Populações

- **principal:** eventos `VALID` ou `VALID_WITH_WARNING`, sempre com `is_quarantined=false`;
- **estrita:** somente eventos `VALID`, com quarentena excluída;
- **sensibilidade:** recálculo independente nas populações principal e estrita;
- **quarentena:** autorizada exclusivamente para cobertura, exclusão e qualidade.

### Janela, cutoff e censura

- `observation_end`: maior `event_time` utilizável da população principal;
- granularidade: diária, preservando datetime de origem onde existente;
- timezone: `NAIVE_SOURCE_TIME`;
- conta com churn: `feature_cutoff_time = first_churn_time`;
- conta sem churn: `feature_cutoff_time = observation_end`;
- janelas as-of: 7, 30, 60 e 90 dias, além de lifetime até o cutoff;
- episódio aberto: não recebe fim artificial; `is_censored_episode=true` e duração observada até `observation_end`.

`NO_CHURN_OBSERVED` significa ausência de churn utilizável no horizonte observado, nunca retenção definitiva.

### Desfecho principal mutuamente exclusivo

Prioridade: `REACTIVATED_THEN_CHURNED_AGAIN`, `REACTIVATED`, `RECURRING_CHURN`, `SINGLE_CHURN`, `NO_CHURN_OBSERVED`. Estados auxiliares podem se sobrepor, mas tabelas executivas usam exatamente um estado principal por conta.

### Schema de account diagnostic

- **Arquivo/grão:** `solution/data/processed/account_diagnostic_features.parquet`; uma linha por `account_id`;
- **identidade e desfecho:** `account_id`, `primary_outcome`, `churn_count`, `reactivation_count`, `first_churn_time`, `last_churn_time`, `first_reactivation_time`, `last_reactivation_time` e flags auxiliares;
- **observação:** `observation_start`, `observation_end`, `feature_cutoff_time`, `observed_days`;
- **assinatura/MRR:** `subscription_count`, `active_subscription_count_at_observation_end`, `closed_subscription_count`, `overlapping_subscription_count`, `total_mrr_current`, `max_mrr`, `mean_mrr`, `first_plan`, `latest_plan`;
- **uso:** contagens de eventos, usos, features distintas e dias ativos em lifetime/7d/30d/60d/90d, intensidade, concentração, recência e variação 30d versus 60 dias anteriores;
- **suporte:** tickets em lifetime/7d/30d/60d/90d, fechamentos, resolução média/mediana, satisfação média/mais recente e recência;
- **qualidade:** `has_usage_warning`, `has_support_warning`, `has_subscription_overlap`, `quality_coverage_ratio`.

Por compatibilidade com o campo mínimo solicitado, `active_subscription_count_at_observation_end` e `total_mrr_current` são calculados no cutoff específico da conta. O nome não autoriza consulta posterior ao primeiro churn; `feature_cutoff_time` torna a disponibilidade auditável.

### Schema de subscription diagnostic

- **Arquivo/grão:** `solution/data/processed/subscription_diagnostic_features.parquet`; uma linha por `episode_id`;
- **identidade:** `episode_id`, `account_id`, `subscription_id`;
- **tempo/censura:** `episode_start`, `episode_end`, `episode_duration_days`, `observed_duration_days`, `episode_status`, `is_censored_episode`;
- **negócio:** `plan`, `mrr`, churn e reativação utilizáveis durante o intervalo;
- **uso:** `usage_event_count`, `usage_active_days`, `distinct_features_used`, sempre vinculado pela assinatura;
- **suporte contextual:** `support_ticket_count`, `mean_resolution_hours` no intervalo da conta;
- **qualidade:** `overlap_count`, `quality_status`, `quality_flags`.

Suporte não possui `subscription_id` na fonte. Por isso suas métricas de episódio são contexto de conta/intervalo e podem repetir em episódios sobrepostos; não constituem atribuição a uma assinatura.

### Resolução de tickets

`resolution_time_hours` é o único complemento lido do CSV bruto. A consulta é read-only, por `ticket_id` único, e o valor só entra quando existe evento `SUPPORT_TICKET_CLOSED` utilizável disponível até o cutoff. Nenhum texto, prioridade futura ou atributo posterior é copiado.

### Receita associada

- conta: soma do MRR dos episódios ativos no cutoff da conta;
- episódio: MRR preservado no grão original;
- faixas: quartis por rank estável do MRR no cutoff;
- terminologia: somente “MRR associado”, sem inferir perda, recuperação ou reconhecimento contábil.

### Grupos pequenos e findings

Coortes com menos de 20 contas recebem `SMALL_SAMPLE` e não são findings principais. Findings exigem evidência quantitativa, denominador, n, comparação, efeito, limitação e sensibilidade. `UNSTABLE` é automaticamente rejeitado.

### Campos proibidos e controles de leakage

São proibidos em features: `churn_flag`, `account_name`, `feedback_text`, `reason_code`, refund, flags snapshot, `end_date` como antecipação do desfecho e qualquer evento posterior ao cutoff. Fechamento, satisfação e resolução só entram se disponíveis até o cutoff. Quarentena nunca entra em uso, suporte, MRR, outcomes ou jornadas.

### Artefato de atenção

`retention_attention_segments.parquet` contém no máximo cinco linhas agregadas com definição, contagem, MRR associado, evidência, limitação, ação de investigação e prioridade. Não contém `account_id` e não é score preditivo.

---

## Contrato anal?tico ? Fase 4

### Unidade, origem e endpoint

- **unidade:** conta, no m?ximo uma linha por `account_id`;
- **origem principal:** primeira `SUBSCRIPTION_STARTED` utiliz?vel;
- **origem alternativa:** `ACCOUNT_CREATED` utiliz?vel, somente em sensibilidade;
- **endpoint:** primeiro `CHURN_RECORDED` utiliz?vel em ou ap?s a origem;
- **censura:** administrativa ? direita em `2024-12-31T19:00:00`;
- **popula??o principal:** `VALID + VALID_WITH_WARNING`, sem quarentena;
- **popula??o estrita:** somente `VALID`, sem quarentena.

Churn anterior ? exposi??o ? ignorado e contabilizado. Churn recorrente n?o substitui o primeiro endpoint. Dura??o zero ? preservada como `same_day_event`; dura??o negativa ou origem ausente recebe `exclusion_reason` e n?o entra na curva.

### `account_survival_dataset.parquet`

- **gr?o:** uma linha por conta da tabela anal?tica da Fase 3; 500 linhas m?ximas;
- **tempo:** `exposure_start`, `exposure_end`, `duration_days`, `first_churn_time`, `observation_end`, `time_origin`;
- **evento/censura:** `event_observed`, `censoring_status`, `same_day_event`, `exclusion_reason`, `is_eligible`;
- **baseline:** `first_plan`, `latest_plan`, `baseline_mrr`, `mrr_band`, `subscription_count_band`, `has_subscription_overlap`;
- **qualidade:** `quality_population`, `quality_coverage_ratio`;
- **comportamento controlado:** `initial_usage_band`, `support_band`, `behavior_window_days=30`, `behavior_group_use=LANDMARK_ONLY`;
- **auditoria:** `pre_exposure_churn_count`, `primary_outcome` reduzido a primeiro churn/censura/exclus?o.

`account_id` permanece apenas nos Parquets operacionais locais. JSONs, relat?rios e figuras cont?m somente agregados. S?o proibidos `account_name`, `churn_flag`, feedback, motivo, refund e qualquer evento posterior ao endpoint.

### Landmarks

Arquivos:

- `account_survival_landmark_30d.parquet`;
- `account_survival_landmark_60d.parquet`;
- `account_survival_landmark_90d.parquet`.

Campos: `account_id`, `landmark_days`, `landmark_time`, `duration_after_landmark`, `event_observed_after_landmark`, contagem de uso, dias ativos, features distintas, suporte, resolu??o, satisfa??o, MRR, quantidade de assinaturas, popula??o de qualidade e bandas comportamentais no marco.

Somente contas observ?veis at? o marco e sem churn antes ou no marco entram. Features usam eventos entre exposi??o e landmark, inclusive; eventos posteriores s?o proibidos. Exclus?es reconciliam com a popula??o de origem.

### Estimadores e suporte

- Kaplan?Meier: produto `1-d/n`, intervalo de 95% por Greenwood;
- Nelson?Aalen: soma `d/n`, com intervalo normal descritivo;
- at-risk m?nimo: 20; abaixo disso, `LOW_AT_RISK`;
- grupos: n m?nimo 20 e ao menos 5 eventos para log-rank;
- multiplicidade: Benjamini?Hochberg;
- RMST: 90, 180 e 365 dias, sem interpreta??o causal;
- mediana: `NOT_REACHED` quando a curva n?o atinge 0,5;
- al?m do maior suporte observado: `BEYOND_SUPPORT`, sem extrapola??o.

### Sensibilidade

S?o comparados: principal, estrita, signup, primeira assinatura, exclus?o de overlap no baseline e cobertura de qualidade `>=0,50`. Varia??o relativa at? 10% ? `ROBUST`, at? 30% ? `SENSITIVE`; acima disso, falta de suporte ou mudan?a de ordena??o ? `UNSTABLE`. Resultados inst?veis n?o s?o findings principais.

### Uso permitido e proibido

Permitido: evid?ncia agregada descritiva de tempo at? primeiro churn, censura, suporte, landmarks e sensibilidade. Proibido: probabilidade individual, score, ranking, causalidade, previs?o, taxa empresarial, a??o automatizada, curva independente por assinatura ou uso de quarentena.

---

## Contratos da Fase 5 ? jornadas e padr?es

### `account_journeys.parquet`

Gr?o: uma linha por `account_id + journey_scope + quality_population`. Escopos autorizados: `FULL_OBSERVED_JOURNEY`, `PRE_FIRST_CHURN`, `BETWEEN_CHURN_AND_REACTIVATION`, `POST_REACTIVATION`, `BETWEEN_RECURRING_CHURNS` e landmarks de 30/60/90 dias.

Campos principais:

- limites: `journey_start`, `journey_end`;
- representa??es est?veis: `raw_sequence`, `collapsed_sequence`, `time_bucketed_sequence`;
- m?tricas: `raw_length`, `collapsed_length`, `distinct_event_types`, `observed_days`, `repeated_event_ratio`;
- governan?a: `same_day_order_dependency`, `quality_coverage_ratio`, `source_contract`;
- marcadores descritivos: `contains_churn`, `contains_reactivation` e sequ?ncias num?ricas.

`RAW_SEQUENCE` preserva tipos can?nicos completos. `COLLAPSED_SEQUENCE` usa vocabul?rio reduzido e colapsa repeti??es consecutivas. `TIME_BUCKETED_SEQUENCE` ? JSON estruturado por dia, evento e contagem.

### Transi??es

Gr?o agregado: `source_event + target_event + journey_scope + outcome + quality_population`. Cont?m suporte por conta, ocorr?ncias, denominador, probabilidade condicional de origem, lift versus refer?ncia, estabilidade, depend?ncia de ordem e gate de amostra.

### Padr?es

Gr?o agregado: padr?o serializado + representa??o + escopo + desfecho + popula??o. N-grams t?m comprimento 2?5; subsequ?ncias frequentes usam suporte m?nimo 15 contas, comprimento m?ximo 5, gap m?ximo 5 eventos/90 dias e pruning fechado.

### `account_journey_taxonomy.parquet`

Gr?o: uma linha por `account_id + journey_scope + quality_population`. Campos:

- `primary_journey_class`: uma classe determin?stica;
- `secondary_journey_classes`: JSON est?vel com zero ou mais classes;
- `classification_rule` e `supporting_metrics`: regra e evid?ncia audit?veis;
- `confidence_level`, `stability_status`, `limitations`.

O Parquet cont?m IDs t?cnicos para rastreabilidade; JSONs, relat?rios e figuras cont?m somente agregados.

### Estabilidade

- `ROBUST`: presen?a/dire??o preservadas e suporte materialmente est?vel, sem depend?ncia HIGH;
- `SENSITIVE`: presen?a/dire??o preservadas com varia??o relevante;
- `UNSTABLE`: desaparecimento, invers?o, amostra pequena ou depend?ncia HIGH.

### Controle de exposi??o

S?o obrigat?rios suporte por conta, janelas fixas, pseudo-cutoff no fim da observa??o para n?o churn, landmarks e bandas `SHORT_JOURNEY`, `MEDIUM_JOURNEY`, `LONG_JOURNEY` baseadas nos quantis 33%/67% da jornada completa principal.

### Restri??es

Quarentena, texto livre, PII, causalidade, score, previs?o, interven??o, grafo, centralidade, comunidades e app n?o integram os contratos desta fase.

---

## Contratos da Fase 6 ? JourneyGraph

### Schemas de n?s

Dez labels controlados: `Account`, `Journey`, `EventInstance`, `EventType`, `Pattern`, `Outcome`, `Taxonomy`, `QualityProfile`, `Finding` e `Investigation`. Cada n? cont?m apenas tipos GraphML simples. Listas e estruturas s?o JSON est?vel. Account exp?e somente `account_key` an?nimo, bandas/agregados, outcome, qualidade e contagens; n?o exp?e PII, texto livre ou ID operacional.

### Schemas de rela??es

Tipos controlados: `HAS_JOURNEY`, `HAS_EVENT`, `OF_TYPE`, `NEXT_EVENT`, `CLASSIFIED_AS`, `ASSOCIATED_WITH_OUTCOME`, `HAS_QUALITY_PROFILE`, `MATCHES_PATTERN`, `CONTAINS_EVENT_TYPE`, `OBSERVED_BEFORE`, `ASSOCIATED_WITH`, `SUPPORTED_BY`, `RECOMMENDS_INVESTIGATION` e `TRANSITIONS_TO`.

`TRANSITIONS_TO` tem gr?o `source EventType + target EventType + journey_scope + outcome + quality population` e preserva suporte por conta, contagem, denominador, suporte relativo, probabilidade condicional, lift, suportes principal/estrito, estabilidade, ordem, amostra, promo??o e MRR associado.

### Pol?tica de identificadores

- SHA-256 truncado em 16 caracteres;
- namespace/salt local est?tico e documentado: `ai-master-challenge::carlos-henrique::journeygraph::v1`;
- prefixos por entidade (`acct_`, `journey_`, `event_`, `pattern_`, `quality_`);
- nenhuma revers?o direta ou tabela de mapeamento versionada;
- `event_instance_key` incorpora `journey_key`, evitando reuso entre escopos.

### QualityProfile

Gr?o: combina??o de popula??o, estabilidade, depend?ncia intradi?ria, amostra, banda de warning, cobertura e confian?a. Campos: `quality_profile_key`, `population`, `stability_status`, `same_day_dependency`, `small_sample`, `warning_dependency_ratio_band`, `coverage_band`, `confidence_level` e `limitations_count`.

### Provenance

N?s e rela??es conservam escopo, popula??o, source artifact/source table, filtros, denominadores, estabilidade e limita??es. O event log ativo ? a fonte temporal; artefatos da Fase 5 fornecem padr?es, transi??es, taxonomia, findings e sensibilidade. Quarentena n?o entra no grafo.

### Contrato de promo??o

Somente evid?ncia `ROBUST` ou `SENSITIVE`, com suporte m?nimo, denominador positivo, `small_sample=false` e `same_day_dependency != HIGH`, entra no grafo promov?vel. `UNSTABLE`, HIGH e grupos pequenos permanecem contabilizados, mas exclu?dos.

### Contrato de reconcilia??o

Devem reconciliar contas, jornadas, classes taxon?micas, padr?es promovidos, transi??es promovidas, findings e MRR agregado. O campo `difference_unexplained` deve ser zero. Toda diferen?a esperada exige `reason`, `source`, `count` e `expected_behavior`.

### Contrato GraphML

`journey_instance_graph.graphml` cont?m o grafo completo de rastreabilidade; `journey_analytical_graph.graphml` cont?m somente a camada promovida. Propriedades aceitas: string, integer, float e boolean. IDs brutos, PII, texto livre sens?vel e sem?ntica causal s?o proibidos.

### Contrato Neo4j

A exporta??o cont?m dez CSVs de n?s, doze CSVs de rela??es, constraints, ?ndices, import e dez consultas equivalentes. EventInstance ? uma amostra determin?stica das primeiras 250 `journey_key` ordenadas; o GraphML permanece completo. A exporta??o ? derivada, sem servidor, credenciais ou rede, e n?o cont?m `account_id` bruto ou source event id.

### Uso permitido e proibido

---

## Contratos da Fase 7 ? Intervention Watchlist

### `intervention_watchlist.parquet`

Gr?o: `account_key ? reference_date ? watchlist_rule_id`. Chave an?nima, regra, fila, quatro componentes LOW/MEDIUM/HIGH, prioridade P1?P4, m?tricas retrospectivas, qualidade, MRR associado, evid?ncia de grafo promov?vel, propriet?rio humano e limites operacionais.

### `account_watchlist_summary.parquet`

Gr?o: uma linha por `account_key` no cutoff. Cont?m prioridade mais alta, filas e regras serializadas, extremos discretos dos componentes, MRR deduplicado, outcome, taxonomia, qualidade e revis?o humana obrigat?ria.

### `watchlist_evidence.parquet`

Gr?o: um pacote por `watchlist_item_key`. Cont?m `rule_id`, fontes, m?tricas observadas, padr?es/caminhos/findings promov?veis, popula??o, denominadores, cutoff, janelas, flags, estabilidade, limita??es, provenance e explica??o estruturada.

### Configura??o e prioridade

`config/watchlist_rules.json` versiona condi??es, exclus?es, cobertura, estabilidade, suporte, propriet?rio, investiga??o autorizada e a??es proibidas. A prioridade combina evidence strength, temporal urgency, materiality e data confidence por matriz expl?cita; n?o existe m?dia ponderada, score ou probabilidade.

### Provenance e explica??o

Fontes controladas: `PHASE_3_DIAGNOSTIC`, `PHASE_4_SURVIVAL`, `PHASE_5_JOURNEY`, `PHASE_6_GRAPH` e `DATA_QUALITY`. Caminhos s?o relativos. Templates registram observa??o, motivo, evid?ncia, contexto temporal/de grafo/de qualidade, limita??es, pr?ximo passo autorizado e interpreta??o proibida.

### Privacidade

Parquets individuais usam apenas `account_key` an?nimo. JSONs agregados, relat?rios e figuras n?o cont?m account keys, IDs brutos, PII ou texto livre sens?vel.

Permitido: investiga??o agregada, estrutura, caminhos observados, qualidade, suporte, estabilidade, taxonomia e MRR associado. Proibido: score individual, causalidade, previs?o, perda/economia atribu?da, ranking de conta, recomenda??o autom?tica, contato, interven??o, GNN, link prediction e app.

---

## Contratos da Fase 8 ? Experiment Lab

### Registro e especifica??es

`experiment_registry.parquet` tem uma linha por experimento e registra desenho, unidades, cutoff, regras, popula??o eleg?vel, amostra requerida, MDE, alpha, power, dura??o, riscos, aprova??es, limita??es e `causal_status=UNTESTED`. `experiment_specifications.parquet` normaliza se??es e par?metros das oito especifica??es individuais em JSON.

### Cat?logo, hip?teses e an?lise

`config/intervention_catalog.json` versiona dez interven??es somente como op??es futuras. Os artefatos agregados de hip?teses, elegibilidade, baseline, power, SAP, guardrails, stopping rules, governan?a e findings n?o cont?m chaves de conta. Baselines s?o hist?ricos e descritivos; n?o equivalem a bra?o de controle.

### Simula??o de assignment

`experiment_assignment_simulation.parquet` usa apenas `account_key` an?nima, experimento, bra?o simulado, bloco, seed, elegibilidade, motivo e `simulation_only=true`. A simula??o testa reprodutibilidade e balan?o; n?o constitui execu??o, exposi??o, tratamento ou resultado.

### Estados e linguagem

Estados permitidos: `DRAFT`, `READY_FOR_REVIEW`, `PILOT_ONLY`, `UNDERPOWERED`, `NOT_FEASIBLE` e `BLOCKED`. O contrato pro?be `RUNNING`, `SUCCESS`, `FAILED`, `EFFECTIVE`, uplift observado, efeito estimado ou resultado causal. Um futuro sistema operacional dever? impor uma interven??o comportamental por conta, aprova??es, consentimento e monitoramento externo.
