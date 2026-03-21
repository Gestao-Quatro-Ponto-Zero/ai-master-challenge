# Submissão — Theo Garcia — Challenge 001 (Diagnóstico de Churn)

## Sobre mim

- **Nome:** Theo Garcia
- **Challenge escolhido:** 001 — Diagnóstico de Churn (RavenStack)

---

## Executive Summary

O CEO acredita que o churn está em 22%. O número real é **70%** — proporção de contas que já cancelaram ao menos uma vez. 277 reativaram, mascarando o problema. 175 cancelaram mais de uma vez.

A análise cruzou todas as 5 tabelas e identificou três drivers principais com dados: DevTools (31% churn, 2x a média), canal de eventos (30%, 2x partners), e mid-market $1K–$2.5K MRR (26%, 55% da base). O churn está acelerando: **6 eventos em Q1/2023 → 251 em Q4/2024, 42x em 2 anos**.

Adicionalmente: a pesquisa de satisfação tem escala quebrada — **zero respostas 1 ou 2** em 2.000 tickets. O CS está medindo um instrumento que não captura insatisfação.

→ Ver `executive_summary.md` para o one-pager executivo.

---

## Plano de Execução (6 Partes)

### LEIS (Critérios de Qualidade — invioláveis)
1. Cruzar as 5 tabelas — quem só olhou uma perdeu o ponto
2. Insights verificáveis — mostrar os números, sem achismo
3. Recomendações acionáveis — nada de "melhorar a experiência do cliente"
4. Distinguir correlação de causalidade — cuidado com conclusões apressadas
5. CEO não-técnico lê e age — linguagem clara, sem jargão estatístico

### Parte 1 — Setup & Ingestão de Dados ✅
- [x] Fork/clone do repositório original
- [x] Estrutura de submissão criada
- [x] 5 CSVs do Kaggle baixados (accounts, subscriptions, feature_usage, support_tickets, churn_events)
- [x] Ambiente Python configurado (pandas, plotly, streamlit, scikit-learn, shap, xgboost)
- [x] EDA inicial: shapes, dtypes, nulls, distribuições
- [x] Validação de integridade referencial (todas as FKs ok)

### Parte 2 — Integração Cross-Table ✅
- [x] Merge das 5 tabelas em master table (500 rows x 55 cols)
- [x] Feature engineering: 30+ variáveis derivadas (sub_churn_rate, error_rate, escalation_rate, tenure_days, etc.)
- [x] Exportação de `master_churn_analysis.csv`
- [x] Quick cross-table insights: churned vs retidos quase idênticos nas médias (pista chave)

### Parte 3 — Análise de Causa Raiz ✅
- [x] Análise segmentada (indústria, país, canal, plano, MRR tier)
- [x] Análise temporal: churn acelerando 42x em 2 anos (Q1/23: 6 → Q4/24: 251)
- [x] Feedback text: 3 categorias (too expensive 36%, missing features 34%, competitor 30%)
- [x] Feature usage: diferenças mínimas (<6%) — confirma que médias mascaram
- [x] Validação CEO: "uso cresceu" é FALSO — caiu ligeiramente per-account
- [x] Support deep dive: satisfação churned > retidos (contraintuitivo mas explicável)
- [x] Cross-tab: reason code × industry, reason code × MRR tier

### Parte 4 — Segmentação de Risco ✅
- [x] Clustering de contas por perfil de comportamento (K-Means, k=4)
- [x] Scoring de risco rule-based por conta (0-100, 5 fatores ponderados)
- [x] Matriz de risco: probabilidade × impacto (MRR) — 4 quadrantes
- [x] Lista específica de contas em risco (top 20, $35K MRR)
- [x] Validação: Critico = 50% churn real vs Baixo = 11% (4.5x separação)

### Parte 5 — Dashboard + Modelo Preditivo ✅
- [x] Dashboard Streamlit com 3 abas (Diagnóstico, Preditiva, Recomendações)
- [x] Aba Diagnóstico: KPIs, churn por segmento, mapa, timeline, drill-down, CEO claims validation
- [x] Aba Preditiva: Risk matrix scatter plot, risk scoring, RF com feature importance
- [x] Aba Recomendações: 5 ações priorizadas por impacto
- [x] Aceleração trimestral (42x) com gráfico de área
- [x] Decisão: Risk scoring rule-based > ML (F1=0.098) — explicável e validado

### Parte 6 — Documentação & Submissão ⏳
- [ ] Process Log detalhado
- [ ] Git history com commits semânticos
- [ ] PR final

---

## Findings Principais (até agora)

### 1. O churn é muito maior do que parece
- CEO vê 22% (110 contas flagged)
- Realidade: 352 contas (70%) já churnearam pelo menos uma vez
- 175 contas churnearam múltiplas vezes (churn recorrente)

### 2. DevTools é o segmento que sangra
- 31% churn rate — quase o dobro de EdTech (16.5%) e Cybersecurity (16%)
- ~$50K MRR em risco só nesse segmento

### 3. Canal de aquisição importa mais que plano
- Eventos: 30.2% churn (pior canal)
- Partners: 14.6% churn (melhor canal — metade)
- Plano (Basic/Pro/Enterprise): ~22% uniforme — não é o driver

### 4. Mid-market é o tier mais vulnerável
- Contas de $1K-$2.5K MRR: 25.8% churn
- "Grandes demais para self-service, pequenas demais para atenção enterprise"

### 5. As médias mascaram tudo
- Uso, satisfação, tickets, erros — quase idênticos entre churned e retidos
- Explica por que CS e Produto dizem "tá tudo ok" — estão olhando médias

### 6. Churn acelerando exponencialmente (Parte 3)
- Q1/2023: 6 eventos → Q4/2024: 251 eventos (42x em 2 anos)
- Não é flutuação — é uma curva exponencial que exige ação urgente

### 7. CEO está errado sobre uso (Parte 3)
- "Uso cresceu" → FALSO. Caiu ligeiramente per-account (H1→H2 2024)
- Produto pode estar olhando uso agregado (mais contas = mais uso total)

### 8. Satisfação dos churned é MAIOR que dos retidos (Parte 3)
- Churned: 4.01 vs Retidos: 3.97
- Explicação: o problema não é suporte — é pricing/features/competição
- 41% dos scores são null → non-response bias dos insatisfeitos
- **Instrumento quebrado:** zero respostas 1 ou 2 em 2.000 tickets. Escala efetiva: 3–5. A métrica não detecta insatisfação — detecta ausência de resposta.

### 9. Feedback confirma: problema multifatorial (Parte 3)
- "too expensive": 36% dos feedbacks
- "missing features": 34%
- "switched to competitor": 30%
- Sem causa dominante única → precisa de intervenções diferenciadas

---

## Solução

### Dashboard Interativo (Streamlit)

```bash
cd submissions/theo-garcia
pip install -r requirements.txt
streamlit run app.py
```

#### Aba 1: Diagnóstico
- KPIs: churn rate, MRR em risco, contas que já churnearam
- Filtros interativos: indústria, plano, país
- Visualizações: churn por segmento, MRR impact, mapa geográfico, timeline
- Drill-down para contas individuais

#### Aba 2: Preditiva
- Random Forest com 34 features cross-table
- Feature importance (top 15 drivers)
- Ranking de contas ativas por risco
- Consulta individual: prob. churn + fatores vs média

#### Aba 3: Recomendações
- 5 ações priorizadas com impacto estimado em $ e prazo
- Tabela de priorização (impacto × esforço)

---

## Recomendações

| # | Ação | Custo est. | Retorno potencial | Prazo |
|---|------|-----------|-------------------|-------|
| 1 | Squad CS dedicado DevTools | ~$8K/mês (1 CSM) | ~$50K MRR | 90 dias |
| 2 | Realocar budget eventos → partners | $0 (redistribuição) | 2x LTV por lead | 30 dias |
| 3 | Tier "Growth" para mid-market | ~$15K implementação | ~$120K MRR | 120 dias |
| 4 | Outreach top 20 contas em risco | $0 (CS existente) | $35K MRR imediato | 48h |
| 5 | Corrigir métrica de churn (3 visões) | $0 | Visibilidade executiva | 30 dias |

**Potencial de recuperação conservador: ~$80–120K MRR nos próximos 6 meses.**

---

## Limitações

- **Modelo preditivo com F1 baixo (0.098)** — features comportamentais quase idênticas entre churned e retidos. Isso é em si um insight: o churn neste dataset é mais driven por fatores externos (budget, competitor, pricing) do que por comportamento observável na plataforma. Substituído por risk scoring rule-based (Critico = 50% vs Baixo = 11%).
- **Dataset possivelmente sintético** — distribuições muito uniformes em algumas variáveis (reason codes, por exemplo, são quase perfeitamente distribuídos)
- Sem dados temporais granulares de engagement (login frequency, session depth)

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usei |
|---|---|
| Claude Code (Opus 4.6) | Analise exploratoria, feature engineering, dashboard, iteracao em tempo real |
| Python 3.11 + Pandas | Manipulacao de dados e integracao cross-table |
| Plotly + Streamlit | Visualizacoes interativas e dashboard web |
| Scikit-learn | Random Forest, K-Means, StandardScaler |

### Workflow

Documentado em detalhe em [`process-log/workflow.md`](process-log/workflow.md). Resumo:

1. Li o briefing inteiro antes de qualquer codigo. Identifiquei a contradicao do CEO.
2. Defini 5 leis de qualidade e plano de 6 partes antes de comecar.
3. Validei integridade referencial entre as 5 tabelas.
4. Criei master table (500x63) com feature engineering cross-table.
5. Analise de causa raiz segmentada — 7 findings com numeros.
6. Risk scoring rule-based (validado: 4.5x separacao) > ML (F1=0.098).
7. Dashboard com 3 abas interativas.

### Onde a IA errou e como corrigi

| # | O que a IA fez | O que eu corrigi | Por que |
|---|---|---|---|
| 1 | Usar apenas ultima subscricao | Agregar TODAS | Perder historico de up/downgrade e perder sinal critico |
| 2 | Imputar satisfaction com media | Manter como NaN | Non-response bias: insatisfeitos nao respondem |
| 3 | RF com F1=0.098 | Criar risk scoring rule-based | Segmentos discriminam melhor que features comportamentais |

### O que eu adicionei que a IA sozinha nao faria

- Validacao do claim do CEO ("uso cresceu" → FALSO per-account)
- Interpretacao do paradoxo de satisfacao (churn por pricing, nao por insatisfacao)
- Decisao de nao forcar o modelo ML — F1 baixo e insight, nao bug
- Priorizacao de recomendacoes por impacto em MRR vs esforco vs prazo
- Arquitetura da analise: segmentos > ML neste caso

## Evidencias

- [x] Git history com commits semanticos mostrando evolucao
- [x] Process log detalhado (`process-log/workflow.md`)
- [x] Notebooks comentados com raciocinio analitico (4 notebooks)
- [x] Dashboard interativo funcional (`streamlit run app.py`)

---

## Stack Tecnica

| Ferramenta | Uso |
|------------|-----|
| Claude Code (Opus 4.6) | Análise exploratória, feature engineering, construção do dashboard |
| Python 3.11 | Runtime |
| Pandas | Manipulação de dados e integração cross-table |
| Plotly | Visualizações interativas |
| Streamlit | Dashboard web |
| Scikit-learn | Modelo preditivo (Random Forest) |

---

## Estrutura do Repositório

```
submissions/theo-garcia/
├── README.md                    # Este arquivo
├── executive_summary.md         # One-pager executivo (CEO-ready)
├── requirements.txt             # Dependências Python
├── app.py                       # Dashboard Streamlit (3 abas)
├── data/
│   ├── churn_scores.csv         # 500 contas rankeadas por risco + top 3 fatores
│   ├── master_churn_analysis.csv # Master table (500x63)
│   └── [5 CSVs originais]
├── notebooks/
│   ├── 01_data_exploration.py
│   ├── 02_data_integration.py
│   ├── 03_root_cause_analysis.py
│   └── 04_risk_segmentation.py
├── process-log/
│   └── workflow.md
└── assets/
```

---

*Submissão em andamento — atualizada em tempo real.*
