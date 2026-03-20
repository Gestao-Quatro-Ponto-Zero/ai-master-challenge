# Prompt 003 — Agent Cross-Table

**Data:** 2026-03-20
**Agent:** 02_cross_table_agent.py
**Ferramenta:** Claude Code
**Executado por:** Lucas Reis

---

## Prompt enviado ao Claude Code

> Contexto: projeto G4 AI Master Challenge — Challenge 001 Diagnóstico de Churn.
> Leia o CLAUDE.md e docs/data_dictionary.md antes de começar.
>
> **CORREÇÃO OBRIGATÓRIA:** Target variable = accounts.churn_flag (22%),
> NÃO churn_events deduplicado (70.4%).
>
> Rode python submissions/lucas-reis/solution/agents/02_cross_table_agent.py
>
> O script deve construir uma master table e responder 6 perguntas de negócio:
> P1: Buyer's remorse (upgrade → churn)?
> P2: Suporte quebrado afeta churn?
> P3: Baixo uso de features prediz churn?
> P4: Qual segmento está mais em risco?
> P5: auto_renew=False é sinal antecipado?
> P6: Quanto MRR está em risco hoje?
>
> Para cada pergunta: query DuckDB, resultado em tabela, interpretação.
> Após: ranking de causas do churn.
>
> Salvar: entry_002_cross_table_output.md, entry_002_cross_table_analysis.md,
> entry_002_target_correction.md, este arquivo.

---

## Preparação necessária

Antes de executar, o Agent 02 foi completamente reescrito para:
1. Corrigir o target: `CAST(a.churn_flag AS INTEGER)` em vez de `COALESCE(c.churned, 0)`
2. Adicionar as 6 funções de análise de negócio
3. Renomear CTE `latest_churn` para `latest_churn_info` (explicita que é só vars explicativas)

**Bugs encontrados e corrigidos em runtime:**
- `a.initial_plan_tier` em raw SQL → `a.plan_tier` (alias só existe na master view)
- Lógica genérica de filtro em Q2 → masks booleanas explícitas

---

## Números mais importantes do output

### Master view
| Métrica | Valor |
|---------|-------|
| Shape | 500 linhas × 42 colunas |
| Churn rate (correto) | **22.0%** — 110/500 contas |

### P1 — Buyer's remorse
| Grupo | Churners | % | MRR médio |
|-------|---------|---|---------|
| Com upgrade antes de churnar | 11 | 14.7% | $2,140 |
| Sem upgrade | 64 | 85.3% | $2,204 |
→ **Buyer's remorse é fraco como causa raiz** (10% dos churners)

### P2 — Suporte
| Grupo | Churn rate |
|-------|-----------|
| COM ticket urgent | **19.9%** (menor!) |
| SEM ticket urgent | **25.7%** |
| COM escalation | 25.3% |
| Q1 resposta rápida | **29.0%** (maior!) |
→ **Hipótese invertida:** tickets urgentes NÃO aumentam churn

### P3 — Feature usage
| Métrica | Churners | Retidos |
|---------|---------|---------|
| Features distintas | **28.34** (+3.4%) | 27.41 |
| Total eventos | **52.05** (+5.3%) | 49.42 |
→ **Churners usam MAIS features — hipótese refutada**

### P4 — Segmentos
| Segmento | Churn rate |
|----------|-----------|
| **DevTools** | **31.0%** 🚨 |
| Event-sourced | **30.2%** 🚨 |
| Partner-sourced | **14.6%** ✅ |
| Cybersecurity | **16.0%** ✅ |
→ **DevTools e event são os segmentos problemáticos**

### P5 — auto_renew
| Grupo | Churn rate |
|-------|-----------|
| COM auto_renew=False | 21.4% |
| SEM auto_renew=False | 25.4% |
→ **auto_renew=False é anti-sinal — hipótese refutada**

### P6 — MRR em risco
| Sinais | Contas | MRR em risco |
|--------|--------|-------------|
| 4+ sinais | 20 | $46,174 |
| 3+ sinais | 118 | $277,319 |
| **2+ sinais** | **306** | **$710,421** |
→ **Conta mais crítica: A-e43bf7 (Cybersecurity, $6,667, 4/4 sinais)**

### Ranking de causas
| Rank | Causa | % churners | MRR perdido |
|------|-------|-----------|------------|
| 1 | Product gap (features) | **60.9%** | $145,526 |
| 2 | Suporte ruim | 32.7% | $80,633 |
| 3 | auto_renew+baixo_uso | 26.4% | $52,680 |
| 4 | Budget | 15.5% | $37,281 |
| 5 | Buyer's remorse | 10.0% | $23,540 |

---

## Decisão estratégica tomada

**Os dados refutaram as hipóteses de uso que esperávamos validar.**
Churners usam mais features, não menos. auto_renew não é sinal de churn.
Tickets urgentes reduzem churn (churners silenciosos são o real risco).

Isso muda o foco do Agent 03 (hipóteses): ao invés de validar comportamental (uso),
deve investigar **segmental** (DevTools, event) e **declarativo** (reason_code=features).

A pergunta que o Agent 04 (modelo) precisa responder não é "quem usa pouco"
mas "qual perfil de conta tem product-market fit ruim com a RavenStack".
