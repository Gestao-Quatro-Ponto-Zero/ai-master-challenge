# CRP-D02 — Validar regras estruturais do dataset

## Objetivo
Transformar as características dos CSVs em regras automatizadas.

## Regras que já devem entrar
- `opportunity_id` é único
- `deal_stage` ∈ `{Prospecting, Engaging, Won, Lost}`
- `Lost` deve ter `close_value = 0`
- `Won` deve ter `close_value > 0` e `close_date` preenchida
- `Engaging` deve ter `engage_date` preenchida e não deve ter `close_date`
- `Prospecting` pode não ter `engage_date`, `close_date`, `close_value`

## Saídas
- `docs/DATA_QUALITY_RULES.md`
- suíte de validação de dados
- atualização de `LOG.md`

## Definition of Done
- existe um comando tipo `validate-data`
- a validação falha quando uma regra crítica quebra
- as regras estão documentadas e testadas

## Prompt para o Cursor
```text
Implemente o CRP-D02: validação estrutural do dataset.

Tarefa:
1. Criar regras automatizadas de qualidade para os CSVs.
2. Priorizar regras críticas:
   - unicidade de opportunity_id
   - enum válido de deal_stage
   - coerência entre stage, datas e close_value
3. Gerar docs/DATA_QUALITY_RULES.md com:
   - regra
   - severidade
   - motivação
   - ação esperada quando falhar
4. Criar testes/validações reproduzíveis no código.
5. Expor um comando único para validação dos dados.
6. Atualizar LOG.md.

Critérios:
- Regras pequenas e explícitas
- Falha rápida para regras críticas
- Não usar ferramenta pesada sem necessidade
```
