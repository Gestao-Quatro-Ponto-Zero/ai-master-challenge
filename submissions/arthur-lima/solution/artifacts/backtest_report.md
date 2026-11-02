# Relatório de Validação Out-of-Time (Dois Regimes + Ablação)

## 1. Avaliação Operacional Primária — Fila Aberta Completa no Corte (Horizonte +90 Dias, Sem Censura)

> **Cortes móveis:** As janelas de 90 dias se sobrepõem e oportunidades podem reaparecer. Não são replicações independentes; não somar suas receitas como receita única.

> **Pergunta avaliada:** *Diante de todas as oportunidades abertas em `Engaging` na data de corte (sem filtrar pelo futuro e sem usar `account`), quais priorizar hoje para maximizar a receita fechada (`Won`) nos próximos 90 dias?*

**Corte `2017-07-31` — Fila Aberta Completa (`N = 2,257`, Horizonte +90d, Taxa Base = 31.5%, Receita Total 90d = US$ 1,719,442)**

| Estratégia de Priorização | AUC (P) | Brier | Lift @ Top 20% | Precisão @ Top 20% | Receita Capturada Top 20% (Global) | % Receita Total |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 🎯 **EV_90d = P_90d(idade, vendedor) × Ticket** | 0.7209 | 0.2046 | 1.31x | 41.1% | US$ 1,033,856 | **60.1%** |
| 🔬 Ablação: EV_90d (apenas idade × Ticket) | 0.7503 | 0.2043 | 1.31x | 41.1% | US$ 1,033,818 | **60.1%** |
| Baseline 1: Preço Nominal (`sales_price`) | 0.5086 | N/A | 1.05x | 33.2% | US$ 857,458 | **49.9%** |
| Baseline 2: Frescor (`-idade` no corte) | 0.5581 | N/A | 0.49x | 15.5% | US$ 183,140 | **10.7%** |
| Baseline 3: Win Rate Fechado do Vendedor | 0.4945 | 0.3170 | 1.01x | 31.9% | US$ 272,678 | **15.9%** |

*Seleção Intra-Vendedor (Top 20% dentro da carteira de cada rep em `2017-07-31`):* **EV_90d** captura **US$ 1,030,733 (59.9%)** vs Preço Nominal US$ 828,223 (48.2%) e Frescor US$ 314,570 (18.3%).

**Corte `2017-08-31` — Fila Aberta Completa (`N = 2,265`, Horizonte +90d, Taxa Base = 24.4%, Receita Total 90d = US$ 1,298,386)**

| Estratégia de Priorização | AUC (P) | Brier | Lift @ Top 20% | Precisão @ Top 20% | Receita Capturada Top 20% (Global) | % Receita Total |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 🎯 **EV_90d = P_90d(idade, vendedor) × Ticket** | 0.6556 | 0.1860 | 1.36x | 33.1% | US$ 790,036 | **60.9%** |
| 🔬 Ablação: EV_90d (apenas idade × Ticket) | 0.6593 | 0.1862 | 1.36x | 33.1% | US$ 789,714 | **60.8%** |
| Baseline 1: Preço Nominal (`sales_price`) | 0.5105 | N/A | 1.07x | 26.1% | US$ 635,562 | **49.0%** |
| Baseline 2: Frescor (`-idade` no corte) | 0.5974 | N/A | 1.41x | 34.4% | US$ 339,496 | **26.1%** |
| Baseline 3: Win Rate Fechado do Vendedor | 0.5234 | 0.3258 | 1.12x | 27.4% | US$ 299,234 | **23.1%** |

*Seleção Intra-Vendedor (Top 20% dentro da carteira de cada rep em `2017-08-31`):* **EV_90d** captura **US$ 785,445 (60.5%)** vs Preço Nominal US$ 580,894 (44.7%) e Frescor US$ 333,123 (25.7%).

**Corte `2017-09-30` — Fila Aberta Completa (`N = 2,409`, Horizonte +90d, Taxa Base = 22.5%, Receita Total 90d = US$ 1,219,993)**

| Estratégia de Priorização | AUC (P) | Brier | Lift @ Top 20% | Precisão @ Top 20% | Receita Capturada Top 20% (Global) | % Receita Total |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 🎯 **EV_90d = P_90d(idade, vendedor) × Ticket** | 0.6253 | 0.1756 | 1.37x | 30.7% | US$ 776,685 | **63.7%** |
| 🔬 Ablação: EV_90d (apenas idade × Ticket) | 0.6133 | 0.1754 | 1.36x | 30.5% | US$ 773,270 | **63.4%** |
| Baseline 1: Preço Nominal (`sales_price`) | 0.4880 | N/A | 0.98x | 22.0% | US$ 580,662 | **47.6%** |
| Baseline 2: Frescor (`-idade` no corte) | 0.8265 | N/A | 2.14x | 48.1% | US$ 564,032 | **46.2%** |
| Baseline 3: Win Rate Fechado do Vendedor | 0.4925 | 0.3509 | 0.90x | 20.1% | US$ 227,784 | **18.7%** |

*Seleção Intra-Vendedor (Top 20% dentro da carteira de cada rep em `2017-09-30`):* **EV_90d** captura **US$ 701,740 (57.5%)** vs Preço Nominal US$ 546,305 (44.8%) e Frescor US$ 551,774 (45.2%).


## 2. Diagnóstico das Estratégias Avaliadas — Subpopulação Condicional Resolvida (`Won` vs `Lost`)

> **Limitação observada:** No diagnóstico condicional dos 970 negócios resolvidos, excluindo post-hoc os 716 ainda abertos, as estratégias avaliadas ficam próximas do acaso (AUC ~0,49–0,51). Isso não estabelece um teto para outros modelos nem comprova abandono. A vantagem observada na fila completa é compatível com triagem por idade ponderada pelo ticket; impacto causal exige teste em campo.

**Diagnóstico Condicional — Subpopulação Resolvida em `2017-06-30` (`N = 970` resolvidos; `716` não-fechados removidos)**

| Estratégia (Subconjunto `Won` vs `Lost`) | AUC-ROC | Brier | Lift @ Top 20% | Precisão @ Top 20% |
| :--- | :---: | :---: | :---: | :---: |
| Motor EV_90d / P_90d(idade, vendedor) | 0.4879 | N/A | 1.03x | 64.4% |
| Baseline 1: Preço Nominal (`sales_price`) | 0.4916 | N/A | 1.02x | 63.9% |
| Baseline 2: Frescor (`-idade` no corte) | 0.5011 | N/A | 0.90x | 56.7% |
| Baseline 3: Win Rate Fechado do Vendedor | 0.5067 | 0.2352 | 1.04x | 65.5% |
