# Data quality rules

## Escopo
Regras estruturais automatizadas para `data/sales_pipeline.csv`.

Entrypoint reproduzível:

```powershell
python .\scripts\validate_data_quality.py
```

## Regras implementadas

| Regra | Severidade | Motivação | Ação esperada quando falhar |
|---|---|---|---|
| `opportunity_id` único | crítica | Evita duplicidade na oportunidade e inconsistência de score/ranking | Bloquear pipeline e corrigir IDs duplicados |
| `deal_stage` em `{Prospecting, Engaging, Won, Lost}` | crítica | Taxonomia consistente para regras de negócio | Bloquear pipeline e normalizar estágio |
| `Lost` deve ter `close_value = 0` | crítica | Coerência financeira de oportunidade perdida | Bloquear pipeline e revisar valor |
| `Won` deve ter `close_value > 0` | crítica | Oportunidade ganha precisa valor fechado | Bloquear pipeline e corrigir valor |
| `Won` deve ter `close_date` preenchida | crítica | Fechamento ganho exige data de fechamento | Bloquear pipeline e preencher data |
| `Engaging` deve ter `engage_date` preenchida | crítica | Estado de engajamento exige data de início | Bloquear pipeline e preencher data |
| `Engaging` não deve ter `close_date` | crítica | Ainda não deveria estar fechada | Bloquear pipeline e remover inconsistência |
| `Prospecting` pode não ter `engage_date`, `close_date`, `close_value` | informativa | Estado inicial permite ausência desses campos | Não bloquear por ausência |

## Cobertura de testes
- `tests/test_data_quality.py`
  - cenário válido (passa)
  - cenário inválido (falha com mensagens explícitas)

## Impacto
Essas regras elevam a confiança da entrada usada por scoring e API, reduzindo risco de output enganoso na submissão.
