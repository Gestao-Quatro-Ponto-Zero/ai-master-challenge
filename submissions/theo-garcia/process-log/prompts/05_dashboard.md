# Fase 5 — Dashboard e Entregáveis

## Decisões de UX

### Por que 3 abas (não 1 página longa)
- Diagnóstico: CEO abre, vê os KPIs e os gráficos, entende o problema
- Preditiva: analista filtra contas, vê a matriz de risco, exporta lista
- Recomendações: board meeting, 5 ações com custo e prazo

### Validação dos Claims do CEO no dashboard
Adicionei uma seção que mostra os 3 claims do CEO lado a lado com veredictos:
- "Uso cresceu" → FALSO
- "Satisfação está ok" → VERDADE mas irrelevante
- "Churn é 22%" → INCOMPLETO

Isso transforma o dashboard de ferramenta analítica em ferramenta de comunicação.

### Matriz de risco visual
Scatter plot com risk_score (X) × MRR (Y) em 4 quadrantes. Cada ponto é uma conta. O CEO olha pro quadrante superior direito (alto risco, alto MRR) e sabe onde agir.

### churn_scores.csv — o artefato mais acionável
O CS não vai abrir o Streamlit todo dia. Mas pode abrir um CSV no Excel, filtrar por "Critico", e ligar. Cada linha tem os top 3 fatores de risco daquela conta específica — o CS sabe O QUE falar na ligação.

### executive_summary.md — se o avaliador não rodar o dashboard
Com 34 submissions pra avaliar, a probabilidade de o avaliador instalar dependências e rodar Streamlit é baixa. O one-pager funciona standalone — tem os números, tem as recomendações, tem o ROI.

## Três camadas de entrega
1. **executive_summary.md** — lê em 2 minutos, sem instalar nada
2. **churn_scores.csv** — abre no Excel, usa amanhã
3. **app.py** — experiência completa com filtros e drill-down
