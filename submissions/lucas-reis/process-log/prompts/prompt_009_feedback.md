# Prompt 009 — Análise de feedback_text + Correção do 60.9%

**Data:** 2026-03-20
**Agente:** Claude Code
**Executado por:** Lucas Reis

---

## Prompt enviado ao Claude Code

> A auditoria revelou que o campo feedback_text em ravenstack_churn_events.csv
> nunca foi analisado. Este dado pode mudar a narrativa de causa raiz.
>
> Execute 4 queries DuckDB:
> 1. Frequência dos textos mais comuns
> 2. Cruzar feedback_text com reason_code
> 3. Cruzar feedback com industry
> 4. MRR perdido por categoria de feedback
>
> Salvar resultados em entry_006_feedback_text.md.
> Se o feedback_text mudar a narrativa: atualizar executive_report.md e executive_summary_1page.md.

---

## O que as queries revelaram

### feedback_text

| feedback | n | % |
|----------|---|---|
| too expensive | 140 | 34.6% |
| missing features | 140 | 34.6% |
| switched to competitor | 125 | 30.9% |

**3 categorias apenas, distribuição quase uniforme = artefato sintético.**
O campo feedback_text é ruído — não adiciona informação porque é independente do reason_code.

### Bug crítico descoberto durante a investigação

Ao investigar a distribuição de reason_code, foi identificado um bug de denominador
na função `ranking_causas()` do Agent 02:

```python
# BUGADO (linha 433 do 02_cross_table_agent.py):
feat_reason = (master['reason_code'] == 'features').sum()  # conta 500 accounts
feat_reason / n_ch  # divide por 110 churners → 67/110 = 60.9%

# CORRETO:
feat_reason = (churners['reason_code'] == 'features').sum()  # conta só churners
# → 15/110 = 13.6%
```

O `master` DataFrame contém contas RETIDAS que também têm reason_code preenchido
(cancelaram subscrições individuais no passado mas não churnarão). Isso inflou
o count de 'features' de 15 para 67.

### Distribuição correta de reason_code (só churned, evento mais recente)

| reason_code | n | % |
|-------------|---|---|
| sem evento registrado | 35 | 31.8% |
| budget | 17 | 15.5% |
| pricing | 16 | 14.5% |
| features | 15 | 13.6% |
| support | 14 | 12.7% |
| competitor | 7 | 6.4% |
| unknown | 6 | 5.5% |

---

## Impacto na narrativa

**Muda:** O headline "60.9% saiu por features" → corrigido para "sem causa dominante"
**Permanece:** DevTools OR=2.36×, event OR=2.53×, AUC=0.34, CS action list, $710K MRR

---

## Arquivos atualizados

- `solution/executive_report.md` — TL;DR, seção causa raiz, seção reason_code, nota metodológica
- `solution/executive_summary_1page.md` — remove 60.9%, adiciona nota de correção
- `process-log/entries/entry_006_feedback_text.md` — análise completa + documentação do bug
