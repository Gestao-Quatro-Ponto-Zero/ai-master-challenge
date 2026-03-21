# Como Continuar o Challenge (para Janus/OpenClaw)

## Status Atual: Partes 1-5 concluídas

O projeto está em `C:\Users\theog\ai-master-challenge\submissions\theo-garcia\`.
Repo GitHub (privado): https://github.com/theoggarcia7-source/ravenstack-churn-diagnosis

### O que já foi feito

| Parte | Status | Arquivo |
|-------|--------|---------|
| 1. Setup & Ingestão | ✅ Concluída | `notebooks/01_data_exploration.py` |
| 2. Integração Cross-Table | ✅ Concluída | `notebooks/02_data_integration.py` + `data/master_churn_analysis.csv` |
| 3. Causa Raiz | ✅ Concluída | `notebooks/03_root_cause_analysis.py` |
| 4. Segmentação de Risco | ✅ Concluída | `notebooks/04_risk_segmentation.py` |
| 5. Dashboard + Preditiva | ✅ Concluída | `app.py` (risk matrix, CEO claims, aceleração) |
| 6. Documentação & PR | ⏳ Pendente | `README.md` atualizado, falta process-log e PR |

### Dados disponíveis

- `data/ravenstack_accounts.csv` — 500 contas
- `data/ravenstack_subscriptions.csv` — 5000 subscrições
- `data/ravenstack_feature_usage.csv` — 25000 registros de uso
- `data/ravenstack_support_tickets.csv` — 2000 tickets
- `data/ravenstack_churn_events.csv` — 600 eventos de churn
- `data/master_churn_analysis.csv` — **MASTER TABLE** com 500 rows x 55 cols (todas as 5 cruzadas)

---

## PARTE 4 — Segmentação de Risco ✅ CONCLUÍDA

**O que foi feito:**
- K-Means clustering (k=4) com 9 features normalizadas
- Risk scoring rule-based (0-100) com 5 fatores ponderados
- Validação: Critico=50% churn vs Baixo=11% (4.5x separação)
- Top 20 contas ativas em risco: $35K MRR
- Master table atualizada: 500 rows x 63 cols (com risk_score, risk_level, cluster)
- Arquivo: `notebooks/04_risk_segmentation.py`

---

## PARTE 5 — Dashboard Atualizado ✅ CONCLUÍDA

**O que foi adicionado ao `app.py`:**
- Gráfico de aceleração trimestral (6→251, 42x)
- Seção "Validação dos Claims do CEO" (3 claims)
- Matriz de risco scatter plot (risk_score × MRR, 4 quadrantes)
- Top 20 contas em risco com score
- Risk scoring integrado nas recomendações
- RF mantido como complementar (F1=0.098)

### Para rodar o dashboard
```bash
cd C:\Users\theog\ai-master-challenge\submissions\theo-garcia
pip install -r requirements.txt
streamlit run app.py
```

---

## PARTE 6 — Documentação & Submissão

### Process Log (OBRIGATÓRIO — sem ele = desclassificado)

Criar `process-log/workflow.md` com:
1. Ferramentas usadas: Claude Code (Opus 4.6) para análise e construção
2. Workflow passo a passo (já documentado nos notebooks)
3. Onde a IA errou (3 correções já documentadas no README)
4. O que EU adicionei: julgamento sobre médias mascarem problema, validação do claim do CEO, decisão de não imputar satisfaction scores

### Submissão via PR

1. Fork o repo original: `gh repo fork Gestao-Quatro-Ponto-Zero/ai-master-challenge`
2. Copiar a pasta `submissions/theo-garcia/` pro fork
3. PR com título: `[Submission] Theo Garcia — Challenge 001`
4. Body do PR: copiar o Executive Summary do README

### Git workflow para cada mudança
```bash
cd C:\Users\theog\ai-master-challenge\submissions\theo-garcia
git add -A
git commit -m "feat: descricao do que mudou"
git push
```

---

## Findings Chave (para referência rápida)

| # | Finding | Dados |
|---|---------|-------|
| 1 | Churn acelerando 42x em 2 anos | Q1/23: 6 → Q4/24: 251 eventos |
| 2 | DevTools sangra mais | 31% churn vs ~16% Cybersecurity/EdTech |
| 3 | Eventos = pior canal | 30% churn vs 15% partners |
| 4 | Mid-market squeeze | $1K-2.5K MRR = 26% churn, 55% da base |
| 5 | Médias mascaram tudo | Churned ≈ retidos em todas as métricas |
| 6 | CEO errado sobre uso | Usage per-account caiu, não cresceu |
| 7 | CS tem razão E está errada | Satisfação ok, mas problema é pricing/features |
| 8 | 70% já churnearam | 352/500 contas, 175 múltiplas vezes |
| 9 | Feedback: 3 categorias | too expensive 36%, missing features 34%, competitor 30% |

---

## LEIS (critérios de qualidade — nunca violar)

1. Cruzar as 5 tabelas (check — master table com 55 cols)
2. Insights verificáveis com números (check)
3. Recomendações acionáveis (check — 5 ações com $ e prazo)
4. Distinguir correlação de causalidade (check)
5. CEO não-técnico lê e age (check — linguagem limpa)
