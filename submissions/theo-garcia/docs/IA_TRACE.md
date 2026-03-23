# Rastreio de Uso de IA — Challenge 001

## Stack de IA utilizada

| Ferramenta | Papel no projeto | Fases de uso |
|---|---|---|
| Claude Code (Opus 4.6) | Motor principal — analise exploratoria, feature engineering, construcao do dashboard, iteracao em tempo real via terminal | Todas (1-6) |
| OpenClaw (plataforma multi-agente) | Orquestracao paralela — agentes especializados em decomposicao de problemas, validacao de hipoteses e revisao de entregaveis rodaram em paralelo ao desenvolvimento principal | Planejamento (1), Validacao (3-4), Revisao final (6) |
| Python 3.11 + Pandas + Plotly + Streamlit + Scikit-learn | Stack de execucao e visualizacao | Fases 2-5 |

## Como as ferramentas se complementaram

O Claude Code foi o motor de execucao: recebia instrucoes, processava dados, gerava codigo e graficos. O trabalho pesado de analise rodou aqui.

O OpenClaw operou como camada de validacao paralela. Enquanto o Claude Code executava, agentes especializados na plataforma multi-agente revisavam hipoteses, questionavam premissas e sugeriam angulos de analise alternativos. Exemplos concretos:

- Um agente de decomposicao quebrou o problema em 6 fases antes de qualquer codigo ser escrito — definindo criterios de qualidade e sequencia de execucao
- Um agente de validacao cruzou os achados da Fase 3 contra benchmarks de churn SaaS B2B para confirmar que os numeros faziam sentido (DevTools a 31% é alto mas plausivel para verticais com alta competicao)
- Um agente de revisao leu o executive summary e os notebooks finais para identificar inconsistencias entre numeros reportados em diferentes arquivos

Essa separacao (execucao vs validacao) evitou o problema de "a mesma IA que gerou o resultado avaliar o resultado". O OpenClaw nunca tocou no codigo — apenas questionou e validou.

---

## Trace por fase

### Fase 1 — Setup e Exploracao Inicial

| Item | Detalhe |
|---|---|
| Ferramenta | Claude Code (Opus 4.6) + OpenClaw (decomposicao) |
| O que pedi | Carregar 5 CSVs, validar integridade referencial entre tabelas |
| O que a IA fez | Carregou dados, mostrou shapes/dtypes/nulls, confirmou zero orphans |
| Erro/limitacao | Nenhum erro tecnico, mas a IA nao flagou espontaneamente o gap entre churn_flag (22%) e churn_events (70%) |
| Julgamento humano | EU identifiquei que 352 contas tinham eventos de churn mas so 110 estavam flagged — 277 reativaram. Isso virou o insight central |
| Evidencia | `notebooks/01_data_exploration.py` linhas 45-80 |
| Iteracoes | 3 |

### Fase 2 — Integracao Cross-Table

| Item | Detalhe |
|---|---|
| Ferramenta | Claude Code (Opus 4.6) |
| O que pedi | Merge das 5 tabelas por account_id, feature engineering |
| O que a IA fez | Criou master table com 55 colunas, sugeriu usar ultima subscricao e imputar satisfaction com media |
| Erro 1 | Sugeriu agregar apenas a ultima subscricao — perderia historico de up/downgrade |
| Correcao 1 | Rejeitei. Agreguei TODAS as subscricoes com medias, totais, net_plan_movement |
| Erro 2 | Sugeriu imputar satisfaction_score com a media (41% nulls) |
| Correcao 2 | Rejeitei por non-response bias — insatisfeitos nao respondem pesquisas. Manter NaN |
| Evidencia | `notebooks/02_data_integration.py` linhas 85-120 (correcao 1), linhas 140-155 (correcao 2) |
| Iteracoes | 5 |

### Fase 3 — Analise de Causa Raiz

| Item | Detalhe |
|---|---|
| Ferramenta | Claude Code (Opus 4.6) + OpenClaw (validacao de hipoteses) |
| O que pedi | Testar 5 hipoteses de segmentacao: industria, canal, MRR, temporal, suporte |
| O que a IA fez | Calculou todas as metricas pedidas corretamente |
| O que EU defini | A IA calcula o que peco. EU decidi O QUE perguntar. A decisao de testar "uso cresceu" segmentando por account e por semestre foi minha |
| Descoberta humana 1 | Uso per-account CAIU -2.5% no H2/2024 — CEO errado |
| Descoberta humana 2 | Satisfacao churned (4.01) > retidos (3.97) — interpretei como churn exogeno, nao insatisfacao |
| Descoberta humana 3 | Escala de satisfacao quebrada: zero notas 1 e 2 em 2.000 tickets. Instrumento nao detecta insatisfacao |
| Validacao OpenClaw | Agente de validacao confirmou que 31% churn em DevTools é consistente com benchmarks de verticais com alta competicao (ferramentas dev tem switching cost baixo) |
| Evidencia | `notebooks/03_root_cause_analysis.py` (7 findings documentados) |
| Iteracoes | 7 |

### Fase 4 — Segmentacao de Risco

| Item | Detalhe |
|---|---|
| Ferramenta | Claude Code (Opus 4.6) |
| O que pedi | K-Means clustering + modelo preditivo |
| O que a IA fez | Random Forest com F1 = 0.098. K-Means com k=4 |
| Erro/limitacao | F1 = 0.098 — modelo praticamente nao discrimina churned de retidos |
| Julgamento humano | Em vez de forcar overfitting ou testar XGBoost/SMOTE, reconheci que F1 baixo e um INSIGHT: features comportamentais nao separam churned de retidos. Criei risk scoring rule-based baseado nos segmentos da Fase 3 |
| Resultado | Risk scoring validado: Critico = 50% churn real vs Baixo = 11% (4.5x separacao) |
| Evidencia | `notebooks/04_risk_segmentation.py` |
| Iteracoes | 4 |

### Fase 5 — Dashboard

| Item | Detalhe |
|---|---|
| Ferramenta | Claude Code (Opus 4.6) + OpenClaw (revisao de entregaveis) |
| O que pedi | Dashboard Streamlit com 3 abas, integracao do risk scoring |
| O que a IA fez | Construiu dashboard funcional com Plotly |
| Decisao humana | 3 camadas de entrega: executive_summary.md (2 min), churn_scores.csv (Excel), app.py (completo). Avaliador pode nao instalar dependencias — precisa funcionar sem dashboard |
| Validacao OpenClaw | Agente de revisao leu executive_summary.md e verificou consistencia dos numeros contra os notebooks. Identificou que o ROI das recomendacoes precisava de custo estimado, nao so retorno |
| Evidencia | `app.py`, `executive_summary.md`, `data/churn_scores.csv` |
| Iteracoes | 6 |

### Fase 6 — Documentacao e Submissao

| Item | Detalhe |
|---|---|
| Ferramenta | Claude Code + OpenClaw (revisao final) |
| O que fiz | Process log, prompt files por fase, IA trace, PR |
| Validacao final | Agente de revisao verificou que todos os numeros citados no README, executive summary e PR body sao consistentes entre si e rastreiaveis ate os notebooks |

---

## Resumo de correcoes humanas

| # | O que a IA propôs | O que corrigi | Motivo | Fase |
|---|---|---|---|---|
| 1 | Usar ultima subscricao | Agregar todas | Historico de up/downgrade é sinal critico | 2 |
| 2 | Imputar satisfaction com media | Manter NaN | Non-response bias | 2 |
| 3 | F1=0.098 como falha | Reframing como insight | Churn exogeno, nao comportamental | 4 |
| 4 | Nao questionar claim do CEO | Testar "uso cresceu" per-account | Uso agregado ≠ uso por conta | 3 |
| 5 | Nao investigar escala de satisfacao | Descobrir que so tem notas 3-5 | Instrumento quebrado | 3 |

---

## Total de iteracoes por fase

| Fase | Iteracoes | Correcoes |
|---|---|---|
| 1. Setup/EDA | 3 | 0 |
| 2. Integracao | 5 | 2 |
| 3. Causa Raiz | 7 | 0 (mas 3 descobertas humanas) |
| 4. Risk Scoring | 4 | 1 |
| 5. Dashboard | 6 | 0 |
| 6. Documentacao | 2 | 0 |
| **Total** | **27** | **3 correcoes + 3 descobertas** |
