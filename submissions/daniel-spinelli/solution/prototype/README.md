# RavenStack Churn Risk Analyzer

Protótipo operacional de priorização de churn para o **Challenge 001 — Diagnóstico de Churn da RavenStack**.

---

## O que o protótipo faz

Carrega os dados reais da RavenStack, cruza as cinco fontes (contas, assinaturas, uso, suporte e eventos de churn), calcula um **risk score explicável de 0–100** para cada conta ativa e apresenta uma interface para o time de CS/Revenue:

- Visualizar contas priorizadas por risco
- Filtrar por industry, referral source, country, plan tier e risk level
- Ver o detalhe de cada conta: score, drivers, recomendação de ação e histórico de uso/suporte
- Exportar um CSV com as contas priorizadas

---

## Como rodar

**Pré-requisitos:** Python 3.9+

```bash
# 1. Instale as dependências
pip install -r requirements.txt

# 2. Garanta que os CSVs estejam em uma pasta data/ no mesmo diretório
ls data/
# ravenstack_accounts.csv
# ravenstack_subscriptions.csv
# ravenstack_feature_usage.csv
# ravenstack_support_tickets.csv
# ravenstack_churn_events.csv

# 3. Rode a aplicação
streamlit run churn_risk_app.py
```

A aplicação abrirá automaticamente em `http://localhost:8501`.

---

## Quais dados usa

| Arquivo | Uso |
|---|---|
| `ravenstack_accounts.csv` | Base de contas (identity, industry, country, referral, plan) |
| `ravenstack_subscriptions.csv` | MRR por conta e flag is_trial |
| `ravenstack_feature_usage.csv` | Contagem de eventos e features únicas usadas |
| `ravenstack_support_tickets.csv` | Volume de tickets, escalações e satisfação média |
| `ravenstack_churn_events.csv` | Exclusão de contas já churned da análise |

Campos ausentes ou nulos são tratados com fallback (zero ou "unknown"), sem quebrar a aplicação.

---

## Como o score é calculado

O score é **heurístico e explicável** — não depende de modelo de ML. Cada regra traduz um achado da análise de churn:

| Condição | Pontos | Justificativa |
|---|---|---|
| Base | +20 | Ponto de partida |
| Industry = DevTools | +20 | Maior taxa de churn: 30,9% |
| Industry = FinTech | +12 | Maior impacto financeiro: $265k MRR |
| Referral = event | +20 | Maior churn por canal: 30,2% |
| Referral = ads | +10 | Canal de médio risco |
| Referral = partner | -10 | Menor churn: 14,6% |
| Country = US | +10 | Variável mais importante no modelo preditivo |
| Country = DE | +8 | Segunda variável regional relevante |
| is_trial = True | +8 | Trials com maior risco de não converter |
| unique_features_used > mediana | +5 | Variável relevante no modelo (ROC-AUC 0.611) |
| escalations > 0 | +8 | Sinal de insatisfação escalada |
| MRR > percentil 75 | +10 | Alta prioridade financeira (não causa churn, mas amplifica impacto) |

**Score final:** clamped entre 0 e 100.

**Risk levels:**
- 🟢 Low: 0–39
- 🟡 Medium: 40–59
- 🟠 High: 60–79
- 🔴 Critical: 80–100

---

## Limitações

1. **Sem aprendizado de máquina:** o score é baseado em regras fixas. O modelo preditivo teve ROC-AUC 0.611, próximo de aleatório — indicando que os dados atuais não sustentam um modelo confiável. A heurística explicável é mais segura para uso operacional imediato.
2. **Sem dados temporais:** o score não captura tendências de decaimento de uso ao longo do tempo.
3. **Feedbacks não processados automaticamente:** o histórico de feedbacks ("too expensive", "missing features") foi incorporado como peso por segmento, não por conta individualmente.
4. **Dados imperfeitos:** a aplicação trata nulos e campos ausentes, mas não valida a integridade referencial dos CSVs.
5. **Score estático:** recalculado a cada carregamento, sem histórico de evolução do risco.

---

## Como colocar em produção

**Curto prazo (operacional imediato):**
- Rodar localmente com dados atualizados mensalmente
- Compartilhar CSV exportado com o time de CS via Slack ou e-mail

**Médio prazo (automatizado):**
- Hospedar no Streamlit Community Cloud (gratuito) ou em instância interna
- Conectar diretamente ao data warehouse (BigQuery, Snowflake, Redshift) substituindo os `pd.read_csv` por queries SQL
- Agendar recálculo diário/semanal via cron ou Airflow

**Longo prazo (evolução do modelo):**
- Coletar mais dados comportamentais (NPS, login recency, feature adoption rate)
- Treinar modelo supervisionado com janela histórica maior
- Substituir a heurística pelo score do modelo, mantendo a UI atual
- Implementar alertas automáticos para contas que entram em "Critical"
