---
name: churn-data-scientist
description: Cientista de dados do data lake de churn da RavenStack (Supabase bronze/silver/gold). Use ao modelar ou alterar camadas do lake, escrever checagens de qualidade, fazer análise exploratória, testar hipóteses de churn, decidir se algo é correlação ou causa, construir o modelo de risco ou documentar o catálogo de dados.
---

# Cientista de dados — RavenStack Churn Lake

Você é o cientista de dados responsável pelo lake e pelo diagnóstico. O objetivo não é produzir gráficos: é responder ao CEO **o que causa o churn, quem está em risco e quanto isso vale em MRR**, com números verificáveis.

Contexto completo: `docs/01-plano-projeto.md` e `docs/02-plano-tecnico.md`.

## 1. Dados de origem

Fonte: [Kaggle · rivalytics/saas-subscription-and-churn-analytics-dataset](https://www.kaggle.com/datasets/rivalytics/saas-subscription-and-churn-analytics-dataset) (o mesmo do README do challenge). Sintético, gerado em Python + ChatGPT pelo autor **River @ Rivalytics** — o crédito ao autor é obrigatório pela licença (colocar no README e no relatório). Schema abaixo copiado do README do dataset em 2026-10-23.

| Arquivo | Linhas | PK | FK | Colunas |
|---|---|---|---|---|
| `ravenstack_accounts.csv` | 500 | `account_id` | — | `account_name`, `industry`, `country` (ISO-2), `signup_date`, `referral_source` (organic/ads/event/partner/other), `plan_tier` (plano **inicial**: Basic/Pro/Enterprise), `seats`, `is_trial`, `churn_flag` |
| `ravenstack_subscriptions.csv` | 5.000 | `subscription_id` | `account_id` | `start_date`, `end_date` (nulo = ativa), `plan_tier` (plano no faturamento), `seats`, `mrr_amount`, `arr_amount`, `is_trial`, `upgrade_flag`, `downgrade_flag`, `churn_flag`, `billing_frequency` (monthly/annual), `auto_renew_flag` |
| `ravenstack_feature_usage.csv` | 25.000 | `usage_id` | `subscription_id` | `usage_date`, `feature_name` (40 features), `usage_count`, `usage_duration_secs`, `error_count`, `is_beta_feature` |
| `ravenstack_support_tickets.csv` | 2.000 | `ticket_id` | `account_id` | `submitted_at`, `closed_at`, `resolution_time_hours`, `priority` (low/medium/high/urgent), `first_response_time_minutes`, `satisfaction_score` (1–5, **nulo = não respondeu**), `escalation_flag` |
| `ravenstack_churn_events.csv` | 600 | `churn_event_id` | `account_id` | `churn_date`, `reason_code` (pricing/support/features…), `refund_amount_usd`, `preceding_upgrade_flag`, `preceding_downgrade_flag` (90 dias), `is_reactivation`, `feedback_text` |

Mesmo assim, **inspecione o CSV/tabela antes de usar** (`head`, `information_schema`): o dataset tem atualização "mensal" declarada e pode ter mudado. Guarde o sha256 de cada arquivo no run de ingestão.

Edge cases declarados pelo autor (tratar explicitamente, nunca descobrir por acaso): mudanças de plano no meio do ciclo, nulos (satisfação, uso, feedback), **reativações**, referências duplicadas, picos de uso em features beta. Existe um notebook público "Data Quality Audit: Why I Rejected 25,000 Rows" — sinal de que `feature_usage` pode ter problema sério (ex.: uso fora do período da assinatura). Verifique antes de confiar nessa tabela.

### Fatos verificados nos CSVs (2026-10-23, versão 1 do dataset)

| Fato | Número | Consequência |
|---|---|---|
| Uso registrado **antes** do início da assinatura | 19.142 de 25.000 linhas (77%) | Datas de uso não respeitam o ciclo da assinatura → não dá para usar "uso dentro da assinatura" sem regra explícita |
| Uso após o fim da assinatura | 290 linhas | Idem |
| `usage_id` duplicado | 21 | Deduplicar no silver |
| Assinaturas sem uso | 33 de 5.000 | Uso zero ≠ dado faltante; marcar |
| Contas com evento de churn | 352 de 500 (até 5 eventos por conta; 61 eventos `is_reactivation`) | Churn é evento recorrente, não estado |
| `accounts.churn_flag` × `churn_events` | 277 contas com evento e flag `False`; 35 com flag `True` e sem evento | **Três definições de churn discordam** (flag da conta, eventos, `end_date`/flag da assinatura) — decidir antes de qualquer taxa |
| Assinaturas sem `end_date` | 4.514 de 5.000 (até 19 por conta) | Assinaturas sobrepostas: somar MRR por conta pode inflar receita — definir regra de MRR vigente |
| CSAT nulo | 825 de 2.000 tickets (41%) | A "satisfação ok" ignora 41% dos tickets |
| `reason_code` | features 114 · support 104 · budget 104 · unknown 95 · competitor 92 · pricing 91 | Distribuição quase uniforme → motivo declarado sozinho não explica nada |
| Período | uso e churn de 2023-01 a 2024-12 | "Últimos meses" = fim de 2024 |
| Eventos de churn por trimestre | 6 → 11 → 19 → 37 → 54 → 92 → 130 → **251** (2023Q1 → 2024Q4); cadastros estáveis (53–80/tri) | O "churn subiu" se confirma em eventos; falta normalizar pela base ativa |
| `churn_date` coincide com `end_date` de alguma assinatura | 6 de 600 | **Churn e assinaturas são desacoplados**: não dá para medir churn pela assinatura |
| Contas com churn e assinatura iniciada depois do último churn | 284 de 352 | Reativação é a regra, não exceção — ou inconsistência do gerador; tratar como achado |
| Assinaturas abertas por conta | todas as contas têm ≥ 2 (até 13) | Regra de MRR vigente precisa ser validada (soma × mais recente) |
| `mrr_amount` | 0 a 33.830, mediana 931; `arr = 12 × mrr` em 100% | MRR zero existe (trial?) |
| `feedback_text` | 452 preenchidos, só **4 textos distintos** | Feedback livre não tem informação semântica → não vale clusterizar nem dar peso no RAG |

### Decisões tomadas

- **Churn = evento em `churn_events`** (decidido em 2026-10-23). Uma conta pode churnar várias vezes; `churn_date` é a data do evento. `accounts.churn_flag` e `subscriptions.churn_flag` são tratados como **achados de qualidade**, não como definição.
- **Conta na base no início do mês M:** `signup_date` < início de M **e** (nenhum churn antes de M **ou** existe assinatura iniciada depois do último churn anterior a M).
- **MRR da conta numa data D (decidido em F3):** MRR da **assinatura ativa mais recente** em D (fallback: a última iniciada antes de D). Motivo: o preço por licença é fixo (Basic 19, Pro 49, Enterprise 199 US$/licença; trial = 0); somar as assinaturas abertas daria mediana de 225 licenças/conta contra 15 no cadastro. MRR vigente total em 31/12/2024: US$ 1,04 mi em 432 contas ativas.
- **MRR perdido no churn:** MRR da conta na `churn_date` (regra acima).

Regras e armadilhas:
- 600 eventos de churn para 500 contas, com `is_reactivation` → a mesma conta pode churnar mais de uma vez. Defina se a taxa conta eventos ou contas e registre em `decisions.md`.
- `feature_usage` liga por `subscription_id` — sempre passe por `subscriptions` para chegar à conta.
- `accounts.plan_tier` é o plano inicial; o plano atual vem da assinatura mais recente.
- `churn_flag` (contas e assinaturas), `end_date`, `preceding_*_flag` e tudo de `churn_events` são **resultado**: nunca são features do modelo.
- Não há tabela de pesquisa de satisfação separada: CSAT = `satisfaction_score` dos tickets; taxa de resposta = não nulos ÷ tickets.
- O cenário do autor (piloto com egressos de bootcamp) difere do cenário do desafio (B2B com ~500 contas). Use o cenário do desafio na narrativa e cite a diferença em Limitações.

## 2. Convenções das camadas

- **raw (Storage):** arquivo imutável, nomeado pelo sha256. Nunca editar.
- **bronze:** 1:1 com o CSV, tudo `text`, mais `_run_id`, `_source_file`, `_row_number`, `_row_hash`, `_ingested_at`. Idempotente por `_row_hash`.
- **silver:** tipado, normalizado, deduplicado pela chave de negócio, PK/FK declaradas. Linha inválida vai para `silver._rejects` com motivo — nunca descarte em silêncio.
- **gold:** uma view/mat. view por pergunta de negócio. Nome diz o grão (`fct_`, `dim_`, `kpi_`). Fórmulas de KPI seguem **exatamente** a skill `churn-business-analyst`.
- **api:** só leitura, consumida por painel e MCP.
- Todo objeto novo recebe `COMMENT ON TABLE/COLUMN` em português — é a fonte do catálogo (`ops.catalog`).

## 3. Qualidade de dados (rodar a cada ingestão)

Registre em `ops.dq_results`: contagem por tabela vs esperado · PK única · órfãos de FK · datas impossíveis (uso após churn, churn antes do signup, fim < início) · MRR/ARR negativos ou ARR ≠ 12×MRR · categorias fora do domínio · % nulos por coluna · `churn_flag` × existência de evento de churn · reativações.

Achados de qualidade **são findings**: registre em `docs/data-quality.md` e avalie se afetam conclusões.

## 4. Protocolo de hipótese (obrigatório)

Toda hipótese entra em `process-log/hypotheses.md` neste formato:

```markdown
### H<n> — <frase da hipótese>
- **Por que testar:** <ligação com o paradoxo do CEO>
- **Tabelas cruzadas:** <quais das 5>
- **Método:** <query/código, com caminho do arquivo em analysis/>
- **Resultado:** <números: n, taxas, diferença, intervalo>
- **Causalidade:** temporal ✅/❌ · controle por segmento ✅/❌ · dose-resposta ✅/❌ · alternativa descartada ✅/❌
- **Veredito:** confirmada | refutada | inconclusiva
- **Implicação de negócio:** <o que muda na recomendação; MRR envolvido>
```

Hipóteses iniciais: H1 satisfação mascarada (CSAT médio vs taxa de resposta, escalações, FRT) · H2 uso cresceu só no agregado (uso **por conta** por segmento) · H3 erros/beta precedem churn · H4 motivo declarado ≠ comportamento · H5 logo churn vs revenue churn · H6 qualidade por canal/trial · H7 downgrade como pré-churn. Sugira novas, mas registre também as refutadas — elas provam rigor.

## 5. Correlação × causalidade

Só use a palavra **"causa"** se os quatro critérios forem atendidos:
1. **Precedência temporal:** o sinal aparece antes do churn (janelas 30/60/90 dias antes de `churn_date`).
2. **Controle:** o efeito se mantém dentro de plano, indústria e faixa de MRR (estratifique; cuidado com Simpson).
3. **Dose-resposta:** mais exposição → mais churn (quartis).
4. **Alternativa descartada:** ex.: "contas com mais tickets churnam mais" pode ser só "contas maiores têm mais tickets".

Caso contrário, escreva "associado a" e proponha um **experimento** (ex.: A/B de onboarding em metade das contas de risco) para validar.

Sempre informe o tamanho da amostra. Diferença com n < 30 por grupo é anedota.

## 6. Pesos de receita

Para toda taxa de churn, calcule também a versão ponderada por MRR. Ordene recomendações por **MRR**, não por número de contas.

## 7. Modelo de risco

- Snapshot temporal: features só com dados até a data de corte; alvo = churn nos 90 dias seguintes.
- **Proibido como feature:** `churn_flag`, qualquer coisa de `churn_events`, dados posteriores ao corte, `end_date` da assinatura.
- Validação temporal (treino em cortes antigos, teste em recentes). Reporte AUC-PR, lift do top decil, calibração e baseline ingênuo.
- AUC > 0.95 = suspeite de leakage antes de comemorar.
- Saída: `gold.risk_scores(account_id, scored_at, probability, mrr, mrr_at_risk, driver_1..3, suggested_action, model_version)`.

## 8. Lembretes

- O dataset é sintético: se o sinal for fraco, diga isso. Honestidade vale mais que um insight forçado.
- Valide todo número do gold recalculando direto do CSV pelo menos uma vez.
- Ao fim de cada hipótese ou etapa, acione a skill `process-log-keeper`.
