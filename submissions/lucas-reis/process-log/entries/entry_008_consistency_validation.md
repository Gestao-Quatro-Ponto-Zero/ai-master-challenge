# Entry 008 — Validação de Consistência: Notebook vs Dashboard

**Data:** 2026-03-20
**Status:** ✅ CONSISTENTE — 20/20 métricas OK, 0 divergências

---

## Motivação

Após a regeneração do `data.json` com sanitização (entry_007), foi executada validação
cruzada completa para garantir que todos os números exibidos no dashboard correspondem
exatamente aos valores calculados pelas queries DuckDB (fonte verdade).

---

## Tabela de Comparação Completa

| Métrica | Dashboard | Notebook/DuckDB | Status |
|---------|-----------|-----------------|--------|
| churn_rate | 22.0% | 22.0% | ✅ OK |
| total_churned | 110 | 110 | ✅ OK |
| industry_DevTools | 31.0% | 31.0% | ✅ OK |
| industry_FinTech | 22.3% | 22.3% | ✅ OK |
| industry_HealthTech | 21.9% | 21.9% | ✅ OK |
| industry_EdTech | 16.5% | 16.5% | ✅ OK |
| industry_Cybersecurity | 16.0% | 16.0% | ✅ OK |
| channel_event | 30.2% | 30.2% | ✅ OK |
| channel_other | 24.3% | 24.3% | ✅ OK |
| channel_ads | 23.5% | 23.5% | ✅ OK |
| channel_organic | 17.5% | 17.5% | ✅ OK |
| channel_partner | 14.6% | 14.6% | ✅ OK |
| reason_no_record | 32.7% (36) | 32.7% (36) | ✅ OK |
| reason_support | 16.4% (18) | 16.4% (18) | ✅ OK |
| reason_budget | 14.5% (16) | 14.5% (16) | ✅ OK |
| reason_features | 11.8% (13) | 11.8% (13) | ✅ OK |
| reason_pricing | 11.8% (13) | 11.8% (13) | ✅ OK |
| reason_competitor | 6.4% (7) | 6.4% (7) | ✅ OK |
| reason_unknown | 6.4% (7) | 6.4% (7) | ✅ OK |
| high_risk_mrr | $12,230 | $12,230 | ✅ OK |

**Total: 20 OK / 0 DIVERGE**

---

## Observação sobre churn_score (não é divergência)

O campo `churn_score` das contas HIGH risk aparece com precisão diferente:
- Dashboard: `73` (INTEGER — `CAST(cs.churn_score AS INTEGER)` na query do data.json)
- Fonte verdade: `72.6` (FLOAT — sem cast na query de validação)

Isso é intencional: o dashboard exibe scores arredondados para inteiros por legibilidade.
O MRR (métrica financeira que importa) é idêntico: `$12,230` em ambos.
Não configura divergência de dados.

---

## Divergências encontradas

**Nenhuma.** 0 de 20 métricas divergem.

---

## Contexto dos números validados

Os números críticos do diagnóstico foram confirmados como consistentes:

- **22% churn rate** — 110 de 500 contas (base no `accounts.churn_flag`)
- **DevTools 31% vs Cybersecurity 16%** — OR=2.36× (calculado direto de `churn_flag × industry`)
- **Event 30.2% vs Partner 14.6%** — OR=2.53× (calculado direto de `churn_flag × referral_source`)
- **reason_code sem dominância** — no_record(32.7%), support(16.4%), budget(14.5%), features(11.8%)
- **$12,230 MRR** em 10 contas HIGH risk ainda ativas
- **Paradoxo do uso** — churners: 28.3 features / retidos: 27.4 features (+3.4%)

Todos estes valores são consistentes entre o `data.json` (servido pelo dashboard),
as queries DuckDB diretas (fonte verdade), e os relatórios executivos em markdown.

---

## Status final

**CONSISTENTE.** Dashboard e notebook exibem os mesmos dados.
Qualquer apresentação do projeto (README, relatório, dashboard, notebook) mostra
números derivados da mesma fonte (DuckDB sobre os CSVs originais) com as mesmas
queries, produzindo resultados idênticos.
