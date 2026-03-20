# Prompt 010 — Dashboard + Notebook técnico

**Data:** 2026-03-20
**Agente:** Claude Code
**Executado por:** Lucas Reis

---

## Prompt enviado ao Claude Code

> Vamos construir dois entregáveis finais em paralelo:
>
> **ENTREGÁVEL 1: dashboard/index.html**
> - HTML standalone (sem servidor) com Chart.js 4.4.1 via CDN
> - Dark theme (#0f1117 background, fontes mono)
> - 4 tabs: Causa raiz | Segmentos em risco | Ações CS | Modelo preditivo
>
> **ENTREGÁVEL 2: notebooks/churn_analysis.ipynb**
> - Jupyter notebook técnico com 15 seções
> - Cobre todo o pipeline de análise
> - Inclui correção do bug 60.9%
>
> **CONTEXTO CRÍTICO — narrativa correta após auditoria:**
> - Headline: "22% churn — causa segmental, não comportamental"
> - DevTools OR=2.36×, Event OR=2.53× — evidência primária
> - reason_code: sem_registro(31.8%), budget(15.5%), pricing(14.5%), features(13.6%)
> - AUC=0.3444 — discovery, não falha
> - "60.9% por features" era ERRADO — corrigido para 13.6%

---

## O que foi gerado

### STEP 1 — data.json

Arquivo: `solution/dashboard/data.json` (7.298 linhas)

8 chaves geradas via DuckDB queries:
- `summary`: total_accounts=500, churned=110, churn_rate=22.0, mrr_perdido_anual=2749457
- `by_industry`: 5 indústrias com churn_rate, mrr_perdido, n_churned
- `by_channel`: 5 canais com churn_rate, mrr_perdido
- `reasons`: distribuição correta de reason_code (pós-correção do bug)
- `usage_paradox`: churners vs retidos — features distintas e sessions
- `scores`: 500 registros de churn_scores.csv
- `high_risk`: 10 contas HIGH risk ainda ativas com MRR total $12,231
- `shap_features`: top 10 features por importância SHAP com direção

### STEP 2 — index.html

Arquivo: `solution/dashboard/index.html` (544 linhas, ~190KB)

**4 tabs:**
1. **Causa raiz** — Donut (reason codes corrigidos) + Bar (paradoxo do uso) + 2 insight boxes
2. **Segmentos** — Horizontal bars de churn por indústria e canal
3. **Ações CS** — Tabela interativa com filtros + modal de script contextual + "mark as contacted"
4. **Modelo** — Scatter score×MRR + SHAP bar + Risk tier doughnut

**Features do dashboard:**
- data.json embutido inline como `const DATA = {...}` (sem servidor necessário)
- Modal "Ver script" com argumentos específicos por top_risk_factor_1
- Filtros por indústria/canal na tab de CS
- ROI estimado visível (metas 50%/70%)
- OR=2.36× e OR=2.53× destacados com contexto explicativo

### STEP 3 — churn_analysis.ipynb

Arquivo: `solution/notebooks/churn_analysis.ipynb`

15 seções cobrindo o pipeline completo:
1. Setup e carregamento de dados
2. Target correto vs bug de 70.4%
3. Perfil comparativo churners/retidos
4. Segmentação por indústria e canal (com gráficos)
5. Odds Ratio DevTools e event channel
6. Bug crítico do 60.9% — reprodução e correção documentadas
7. feedback_text — artefato sintético (independente de reason_code)
8. Paradoxo do uso — churners usam +3.4% mais features
9. Testes de hipóteses (chi-square + Welch's t-test)
10. LightGBM — carregar churn_scores.csv, visualizar distribuição
11. Por que AUC < 0.5 é descoberta (tabela comparativa)
12. SHAP — importância e direção das features
13. CS Action List — 10 contas com cálculo de ROI
14. Multi-signal risk analysis ($710K)
15. Conclusões — tabela resumo de evidências + 3 ações

### STEP 4 — Abertura do dashboard

Dashboard aberto em `/solution/dashboard/index.html` via `open` command.

---

## Verificação final do projeto

| Entregável | Status |
|-----------|--------|
| 01_eda_agent.py | ✅ Executado |
| 02_cross_table_agent.py | ✅ Executado (bug correto documentado) |
| 03_hypothesis_agent.py | ✅ Executado |
| 04_predictive_agent.py | ✅ Executado (AUC=0.3444) |
| churn_scores.csv | ✅ 500 linhas |
| executive_report.md | ✅ Atualizado (bug 60.9% corrigido) |
| executive_summary_1page.md | ✅ Atualizado |
| dashboard/data.json | ✅ Gerado |
| dashboard/index.html | ✅ Gerado (544 linhas) |
| notebooks/churn_analysis.ipynb | ✅ Gerado (15 seções) |
| process-log/ | ✅ 10 prompts + 11 entries |
| submissions/lucas-reis/README.md | ⏳ Ainda template |

---

## Reflexão sobre esta etapa

O dashboard e o notebook são os entregáveis mais visíveis do projeto.

**O dashboard** resolve o problema de comunicação: executivos não lêem tabelas em markdown. O Chart.js com dark theme e 4 tabs permite navegar pelo diagnóstico de forma não-linear — o CEO vai para "Ações CS" diretamente; o CPO vai para "Segmentos em risco"; o time técnico vai para "Modelo preditivo".

**O notebook** resolve o problema de auditabilidade: cada célula reproduz uma análise específica com dados reais, permitindo que outro analista verifique os números. A célula 6 (bug do 60.9%) é especialmente importante — documenta não só o que está certo mas o que estava errado e por quê.

**O que a IA fez bem:** gerou estruturas completas e funcionais sem erros de sintaxe. O HTML funciona offline (data.json embutido). O notebook tem queries DuckDB corretas.

**O que exigiu julgamento humano:** a decisão de documentar o bug (não esconder) e de reposicionar a narrativa como segmental em vez de "product features". Isso não é um ajuste de código — é uma decisão editorial sobre o que o relatório afirma.
