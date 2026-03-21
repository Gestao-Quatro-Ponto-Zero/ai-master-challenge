# Scoring v2 (CRP-REAL-04)

## Objetivo
Enriquecer o score com sinais do **dataset real** (joins de `accounts`, `products`, `sales_teams`, datas de `sales_pipeline`) mantendo **explicabilidade** linha a linha (`positives` / `negatives` / `risks`).

## Limitações honestas do v0 (antes)
- Apenas `deal_stage`, `close_value` e presença de `account` (via título) influenciavam o score.
- Campos já disponíveis no pipeline (idade desde `engage_date`, série de produto, receita/headcount da conta, região do time) **não** entravam no cálculo.
- Risco de parecer “ranking superficial” frente ao potencial analítico do challenge.

## O que mudou (v2)
| Sinal | Origem | Efeito (configurável) |
|--------|--------|------------------------|
| `days_since_engage` / `pipeline_age_bucket` | `engage_date` vs data de referência | `fresh` / `active` / `stale` (**apenas oportunidades abertas**; `Won`/`Lost` não recebem este sinal para evitar penalizar fechos antigos) |
| `stage_rank` | estágio (`Prospecting`…`Lost`) | ajuste fino além do peso de `deal_stage` |
| `account_revenue_band` | `accounts.revenue` | `enterprise` / `mid` / `small` / `unknown` |
| `employee_band` | `accounts.employees` | `large` / `medium` / `small` / `unknown` |
| `product_series` | `products.series` | pesos por série (ex.: GTX, MG, GTK) |
| `product_price` | `products.sales_price` | faixas de preço de lista |
| `regional_office` | `sales_teams.regional_office` | bónus de “escritório conhecido” (sem hierarquia arbitrária entre Central/East/West) |
| `manager_name` | `sales_teams.manager` | bónus leve de completude |
| Qualidade de registro | `close_date` em deals `Won`/`Lost` | penalidade/bónus explícitos |

## Onde está no código
- Regras versionadas: `config/scoring-rules.json` (`"version": 2`).
- Construção de features a partir do payload HTTP/row: `feature_set_from_payload` em `src/features/engineering.py`.
- Motor: `src/scoring/engine.py` (`score_opportunity` → `score_from_features`).
- Dados expostos na row de serving: `ServingOpportunity.to_api_row()` (`engage_date`, `close_date`, `account_revenue`, `account_employees`, `team_regional_office`, `product_sales_price`, …).
- API: `src/api/app.py` (`_to_scoring_payload` passa o conjunto enriquecido).

## Compatibilidade
- arquivos de regras **sem** `version >= 2` continuam a usar só o bloco clássico (`deal_stage`, `close_value`, `missing_account_penalty`), para testes e rollbacks.

## Exemplo real (ilustrativo)
Oportunidade `1C1I7A6R` (dataset local):
- **Payload mínimo** (só estágio/valor/conta): score **70** (ilustração com regras atuais).
- **Payload enriquecido** (row completa do pipeline): score **85**, com explicações como estágio terminal, porte da conta, série GTX, região, manager e `close_date` em deal fechado.

*(Valores exatos dependem do snapshot CSV e de `config/scoring-rules.json`.)*

## Testes
- `tests/test_scoring_v2_features.py` — payload enriquecido, pipeline stale, compat v1.
- `tests/test_scoring_engine.py` — regressões do contrato básico.

## Racional (submissão)
- Pesos são **heurísticos** e não calibrados por histórico de conversão; servem para demonstrar **uso estratégico do dataset** e **auditabilidade** (cada incremento pode ser rastreado a um campo e a uma chave JSON).
- Próximo passo natural seria calibrar pesos com dados de outcome ou modelo supervisionado — fora do escopo deste CRP.

## Recalibração CRP-FIN-03 (ranking operacional)
- `deal_stage_weights` foram revistos para **não privilegiar excessivamente `Won`** no topo: `Won` desce (ex.: +25 → +10) e estágios abertos (`Prospecting`, `Engaging`) sobem, mantendo `Lost` fortemente penalizado.
- Objetivo: o ranking principal refletir melhor **ação comercial sobre pipeline aberto**, sem eliminar o sinal de negócio já fechado.

## CRP-FIN-04 — Sinais extra para abertos
- Pesos de `pipeline_age` mais expressivos; penalidade por **engage ausente** em abertos; bloco `open_operational` para **prospecção de baixo valor** já com tempo no pipeline (`active`/`stale`).

## CRP-FIN-06 — Narrativa na UI
- O motor continua a emitir frases estáveis para auditoria; a camada `explanation_narrative` traduz para **linguagem de negócio** antes do payload de detalhe (`scoreExplanation`).
