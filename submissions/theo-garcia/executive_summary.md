# RavenStack — Diagnóstico de Churn
### Executive Summary · Theo Garcia

---

## O problema real (não o que o CEO está vendo)

O CEO acredita que o churn está em **22%**. O número correto é **70%** — a proporção de contas que já cancelaram pelo menos uma vez. A diferença existe porque 277 contas reativaram, mascarando o volume real de perdas. **175 contas cancelaram mais de uma vez.**

Além disso, o claim de que "uso cresceu" é **falso**. Uso per-account caiu -2.5% no H2/2024. O time de Produto provavelmente reporta uso agregado (mais contas × mesmo uso = total maior), não uso por conta.

---

## Os 3 drivers (com dados)

| Driver | Churn | Benchmark | MRR em risco |
|---|---|---|---|
| Indústria DevTools | **31%** | EdTech 16%, Cyber 16% | ~$50K/mês |
| Canal: eventos | **30%** | Partners 15% | CAC desperdiçado |
| Mid-market $1K–$2.5K MRR | **26%** | 55% da base | ~$120K/mês |

O churn não está estável: **6 eventos em Q1/2023 → 251 em Q4/2024. 42x em 2 anos.**

---

## O que a análise de satisfação não mostra

A pesquisa de satisfação tem escala quebrada: **zero respostas 1 ou 2** em 2.000 tickets (escala efetiva: 3–5). Somado aos 41% de nulls, a métrica não captura insatisfação — captura ausência de resposta. O CS está certo que "satisfação está ok", mas está medindo um instrumento que não detecta insatisfação.

---

## 5 ações prioritárias

| # | Ação | Custo estimado | Retorno potencial | Prazo |
|---|---|---|---|---|
| 1 | Squad CS dedicado DevTools | ~$8K/mês (1 CSM) | ~$50K MRR recuperado | 90 dias |
| 2 | Realocar budget eventos → partners | $0 (redistribuição) | 2x LTV por lead | 30 dias |
| 3 | Tier "Growth" mid-market | ~$15K implementação | ~$120K MRR protegido | 120 dias |
| 4 | Outreach top 20 contas em risco | $0 (CS existente) | $35K MRR imediato | 48h |
| 5 | Corrigir métrica de churn (3 visões) | $0 | Visibilidade executiva | 30 dias |

**Potencial de recuperação conservador: ~$80–120K MRR nos próximos 6 meses.**

---

## Como usar o `churn_scores.csv`

O arquivo `data/churn_scores.csv` contém todas as 500 contas rankeadas por risco (0–100) com os 3 principais fatores de risco por conta. O CS pode abrir no Excel, filtrar por `risk_level = Critico` e iniciar contato imediato — sem precisar abrir o dashboard.

---

*Dashboard interativo: `streamlit run app.py` · Análise completa: `README.md`*
