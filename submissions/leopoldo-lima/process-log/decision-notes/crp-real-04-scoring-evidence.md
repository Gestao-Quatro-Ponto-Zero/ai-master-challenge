# CRP-REAL-04 — Evidências de scoring enriquecido

## Diff de configuração (`config/scoring-rules.json`)

- **Antes (v0 implícita):** apenas `base_score`, `deal_stage_weights`, `close_value`, `missing_account_penalty`, `actions`.
- **Depois (v2):** campo `"version": 2` + blocos `pipeline_age`, `stage_rank_adjustment`, `account_revenue_band`, `employee_band`, `product_series`, `regional_office` (+ `known_office_bonus`), `manager_signal`, `product_price`, `data_quality`.

## Antes / depois — prioridade (exemplo verificável)

Oportunidade real **`1C1I7A6R`** (modo `real_dataset`, snapshot local):

| Abordagem | Score (aprox.) | Notas |
|-----------|------------------|--------|
| Payload mínimo (`deal_stage`, `close_value`, `account`/`title`) | **70** | ignora joins de conta/produto/equipe e metadados de datas |
| Payload enriquecido (row completa `to_api_row()` + joins) | **85** | explica GTX, headcount, região Central, manager, estágio terminal, qualidade de `close_date` |

Exemplo de fatores positivos (enriquecido):
- `deal_stage Won contribuiu +25.`
- `porte por headcount large (+4).`
- `serie de produto GTX (+2).`
- `escritorio regional identificado (Central); sinal de completude +1.`
- `manager atribuido (completude de equipe).`

## Hipóteses e decisões humanas

- **Incluído:** sinais derivados diretamente de CSVs oficiais já carregados no serving (sem novas fontes).
- **Evitado:** hierarquia arbitrária “Central melhor que East” — `by_office` a 0 e apenas `known_office_bonus` para presença de região.
- **Risco de modelagem (IA):** tendência a duplicar penalidade “sem engage” + bucket `unknown`; mitigado com `missing_engage_date_penalty: 0` e penalidade única via `pipeline_age.weights.unknown`.

## Como reproduzir

```powershell
python -m pytest -q tests/test_scoring_v2_features.py tests/test_scoring_engine.py
```

Script ad-hoc (amostra `1C1I7A6R`): ver histórico do CRP-REAL-04 no chat ou executar `build_serving_opportunities` + `to_api_row` + `score_opportunity`.
