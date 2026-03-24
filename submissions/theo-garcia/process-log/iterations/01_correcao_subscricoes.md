# Iteracao: Correcao na Agregacao de Subscricoes

**Fase:** 2 — Integracao Cross-Table
**Ferramenta:** Claude Code (Opus 4.6)

---

**Eu:** "Cruze as 5 tabelas por account_id numa master table. Para subscricoes, agregue por conta."

**IA:** Criou o merge corretamente, mas usou apenas a ultima subscricao de cada conta (filtro por max(start_date)). Justificativa: "a subscricao mais recente reflete o estado atual do cliente".

**Meu julgamento:** Rejeitei. Se um cliente fez upgrade de Basic pra Pro, depois downgrade pra Basic, depois cancelou — essa trajetoria é o sinal mais importante. Usar so a ultima é ver a foto final e perder o filme inteiro.

**O que fiz:** Pedi para agregar TODAS as subscricoes por account_id:
- Media de MRR (avg_mrr) em vez de ultimo MRR
- Contagem de upgrades e downgrades
- net_plan_movement = upgrades - downgrades (sinal de deterioracao)
- Percentual de billing anual vs mensal
- Taxa de churn de subscricoes (sub_churn_rate)

**Resultado:** A master table ficou com 30+ features derivadas que capturam COMPORTAMENTO ao longo do tempo, nao apenas estado atual. O net_plan_movement acabou sendo uma das features mais informativas na analise.

**Evidencia:** `notebooks/02_data_integration.py` linhas 85-120
