# Plano Estratégico: Elevar o Diagnóstico de Churn ao Padrão Consultoria Global

## Contexto

A análise atual do Challenge 001 atingiu um bom nível para um exercício individual (~4-6h):
22% de churn identificado, 5 tabelas cruzadas, insights segmentados por indústria, 21 contas em
risco mapeadas. Mas para competir com o padrão de consultorias como McKinsey, BCG, Deloitte,
Accenture, KPMG e Bain, precisamos de uma evolução estrutural.

A pesquisa de mercado com 4 agentes revelou o que separa uma análise "boa" de uma análise
"de classe mundial". Este documento sintetiza os achados e propõe um plano de evolução.

---

## 1. Onde Estamos vs. Onde Precisamos Chegar

| Dimensão | Nível Atual (Challenge) | Padrão Consultoria Global | Gap |
|---|---|---|---|
| **Dados** | 5 tabelas internas (uso, suporte, assinatura, conta, churn) | Customer 360: mesmo base + CRM activity, competitive signals, stakeholder mapping, communication sentiment, acquisition channel | Ampliar fontes |
| **Segmentação** | Por indústria, plano, país, canal | Multidimensional: ACV band, buyer seniority, usage pattern clusters, lifecycle stage, churn type (voluntary vs involuntary) | +involuntary churn, +buyer seniority |
| **Modelagem** | Heurísticas + análise descritiva | Multi-model stack: voluntary classifier + involuntary classifier + survival analysis (when) + uplift modeling (who can be saved) + CLV projection | +survival analysis, +uplift |
| **Explainability** | Score de risco (0-100) | Per-customer "Retention Fingerprint" (KPMG) + SHAP decomposition + intervention ROI estimate | +explicabilidade por conta |
| **Actionability** | Relatório + 7 recomendações | 3-tier risk-to-intervention mapping with CRM triggers, A/B test design, ARR-weighted forecast | +experimentos, +triggers |
| **Economics** | MRR perdido total | NRR-to-valuation linkage, CLTV uplift per intervention, $8:$1 ROI metrics, segment-specific resource allocation | +ROI por intervenção |
| **Organizacional** | Recomendações para CS | Cross-functional playbook: pricing, product, sales incentives, CS workflows, CRO-level forecasting | +cross-functional |
| **Timing** | Quem churnou (passado) | Quem vai churnar (predição 90d antes) + quando (survival) + o que fazer (prescrição) | +preditivo +prescritivo |

---

## 2. Diagnóstico do Gap: Por que não somos consulting-grade?

### 2.1 Ausência de Voluntary vs Involuntary Churn

20-40% do churn em SaaS B2B é *involuntary* — cartão expirado, falha de cobrança,
limite de crédito. No Brasil, isso é ainda maior (boletos, inadimplência estrutural).

**Nossa análise atual**: Trata todo churn como igual.
**O que falta**: Separar voluntary de involuntary. As intervenções são COMPLETAMENTE diferentes:
- Involuntary → dunning, retentativas, mudar forma de pagamento (ROI imediato)
- Voluntary → produto, suporte, pricing (ROI de médio prazo)

### 2.2 Sem Survival Analysis

Classificadores binários (XGBoost, Random Forest) predizem *quem* vai churnar,
mas não *quando*. Para uma empresa com contratos anuais, saber *quando* um
cliente vai churnar é tão importante quanto saber *quem*. Impacto direto em:
- Planejamento de capacidade do CS team
- Forecast de renovação para o CRO
- Priorização: quem está prestes a churnar vs. quem vai churnar em 6 meses

### 2.3 Sem Voluntary Churn Type Taxonomy

Os motivos de churn na RavenStack são: features, support, budget, competitor,
pricing, unknown. Mas isso é superficial. Consultorias decompõem:
- **Features**: falta de funcionalidade específica? Performance? UX? Integração?
- **Support**: tempo de resposta? Qualidade técnica? Idioma? Canal?
- **Budget**: preço alto? Falta de ROI percebido? Concorrência mais barata?

### 2.4 Sem Intervention Economics

Saber que uma conta tem score 85 é útil. Saber que para salvar essa conta
precisamos investir $500 em treinamento e o LTV dela é $50K — isso é
**acionável**. Nossa análise atual para no score, não chega no ROI da intervenção.

### 2.5 Sem Experiment Design

Consultorias não só diagnosticam — elas desenham experimentos para validar
intervenções. Grupos de tratamento vs controle, métricas de sucesso definidas,
período de observação de 90 dias. Nossa abordagem é "one-shot".

---

## 3. Plano de Evolução em 3 Fases

### Fase 1: 🎯 Diagnóstico Avançado (Sprint 1-2 semanas)

**Objetivo**: Elevar a análise descritiva ao padrão consultoria.

**Entregáveis**:

1. **Separação Voluntary vs Involuntary Churn**
   - Cruzar churn_events com dados de pagamento (se disponíveis)
   - Identificar contas que churnearam por falha de cobrança vs. decisão ativa
   - Calcular impacto separado de cada tipo

2. **Análise de Sobrevivência (Survival Analysis)**
   - Implementar Kaplan-Meier por segmento (indústria, plano, país)
   - Implementar Cox Proportional Hazards para identificar hazard ratios
   - Curvas de sobrevivência: "qual a probabilidade de um cliente da indústria X
     ainda estar conosco após 12 meses?"

3. **Decomposição de Motivos por Tipo**
   - Analisar feedback_text dos churn events com NLP (tema, sentimento)
   - Categorizar churn voluntary em subtipos acionáveis
   - Mapa de calor: motivo de churn × indústria × plano

4. **Health Score com Validação**
   - Score atual (0-100) é heurístico. Validar contra churn real.
   - Calcular precisão por threshold: "score > 70 → quantos churnaram?"
   - Ajustar pesos com base em dados, não suposição

**Tecnologias**: Python (lifelines para survival analysis), pandas, plotly
**Resultado esperado**: Relatório com curvas de sobrevivência, taxas de hazard
por segmento, voluntary vs involuntary split

---

### Fase 2: 🤖 Modelagem Preditiva (Sprint 2-3 semanas)

**Objetivo**: Construir pipeline preditivo que identifica risco 90 dias antes.

**Entregáveis**:

1. **Feature Engineering**
   - Features temporais (últimos 30, 60, 90 dias de uso)
   - Features de tendência (declínio de uso, aceleração de erros)
   - Features de suporte (escalações ponderadas por recência)
   - Features de relacionamento (champion detection)

2. **Model Stack**
   - Classificador voluntary (XGBoost ou LightGBM) → *quem* vai churnar
   - Modelo de sobrevivência (CoxPH) → *quando* vai churnar
   - Uplift model (causal forest) → *quem pode ser salvo* e *como*

3. **Explainability Layer**
   - SHAP values por previsão
   - "Retention Fingerprint" por conta (top 3 drivers de risco)
   - Explicações em linguagem natural via LLM

4. **Validação**
   - Backtest: o modelo teria previsto os churns dos últimos 6 meses?
   - Precisão, recall, F1 por segmento
   - Curva de ganhos cumulativos

**Tecnologias**: Python (scikit-learn, xgboost, lifelines, causalml, shap),
MLflow para tracking
**Resultado esperado**: Pipeline que gera lista semanal de contas em risco
com explicação e janela de tempo estimada

---

### Fase 3: 🚀 Plataforma Prescritiva (Sprint 4-6 semanas)

**Objetivo**: Ir de "quem vai churnar" para "o que fazer" com ROI estimado.

**Entregáveis**:

1. **Intervention Playbook Engine**
   - Catálogo de intervenções com custo estimado
   - Match automático: perfil de risco → intervenção recomendada
   - ROI estimado por intervenção (LTV salvo - custo da intervenção)

2. **Automation Layer**
   - Alertas no Slack/email quando conta cruza threshold
   - Draft automático de plano de ação para CSM
   - Sugestão de próximas ações baseada em similaridade com casos anteriores

3. **A/B Test Framework**
   - Design de experimentos para validar intervenções
   - Randomização por conta ou por segmento
   - Métricas de sucesso: churn rate, NRR, satisfação

4. **Dashboard Executivo**
   - Visão CRO: NRR forecast, ARR em risco, eficácia das intervenções
   - Visão CS: lista priorizada de contas, próximas ações, histórico
   - Visão Produto: features mais associadas a churn, gaps competitivos

**Tecnologias**: Streamlit ou React para dashboard, LLM (Claude/GPT) para
geração de playbooks, PostgreSQL para estado
**Resultado esperado**: Plataforma funcional que um time de CS pode usar
semanalmente

---

## 4. Benchmarks para Validar o Resultado

| Métrica | Onde Estamos | Onde Queremos Chegar | Referência |
|---|---|---|---|
| Precisão preditiva (quem churna) | N/A (descritivo) | >85% AUC (30d), >80% AUC (90d) | KPMG claims 85%+ |
| Janela de predição | Passado (já churnou) | 90 dias antes | Padrão consultoria |
| Voluntary/Involuntary split | Não separa | Separa com confiança >90% | KPMG, Accenture |
| Explicabilidade | Score numérico | Top 3 drivers por conta + ROI | "Retention Fingerprint" |
| Intervention economics | Não calcula | Custo vs benefício por intervenção | McKinsey NRR framework |
| Segmentação | 4 dimensões | 8+ dimensões com hierarquia | BCG, Bain |
| Time-to-value | N/A | <7 dias onboarding | Top performers globais |

---

## 5. O que NÃO Fazer

Tão importante quanto o plano: o que não priorizar agora.

- **❌ Modelo deep learning complexo (LSTM, Transformer)**: Dados são tabulares,
  não sequenciais o suficiente. XGBoost + survival analysis dá 90% do resultado
  com 10% da complexidade.
- **❌ Dashboard em tempo real**: Streaming não é necessário para análise de
  churn semanal. Batch processing é suficiente e muito mais simples.
- **❌ Mobile app**: Time de CS trabalha em desktop. Aplicativo móvel é
  desperdício de energia.
- **❌ Integração com 20 ferramentas**: Começar apenas com os dados que já
  temos (5 tabelas) + 1 fonte externa (ex: dados de pagamento). Depois expandir.

---

## 6. Diferencial Competitivo: Onde Podemos SUPERAR as Consultorias

### 6.1 Human-in-the-loop + AI

Consultorias são lentas (8-16 semanas para um diagnóstico). Nossa abordagem
com AI pode entregar em dias. O diferencial não é ser melhor que a IA sozinha
— é ser melhor que a consultoria no *timing* e no *custo*.

### 6.2 Explicabilidade em Linguagem Natural

Enquanto consultorias entregam PowerPoint com SHAP plots, podemos entregar
explicações em linguagem natural geradas por LLM: *"Esta conta está em risco
porque reduziu o uso da feature X em 40% nas últimas 2 semanas, abriu 3
tickets de alta prioridade e o champion da conta parou de logar."*

### 6.3 Experimentação Contínua

Consultorias diagnosticam e saem. Nossa plataforma pode monitorar, iterar e
aprender continuamente — cada intervenção vira dado para a próxima iteração.
É um produto, não um projeto.

### 6.4 Custo 10x Menor

Um diagnóstico da McKinsey custa $200K-$500K+. Uma plataforma como a que
estamos propondo pode ser construída por uma fração disso e entregar ROI
recorrente.

---

## 7. Próximos Passos Imediatos

1. **Implementar survival analysis** no dataset atual (lifelines + CoxPH)
   - Curvas Kaplan-Meier por indústria, plano, país
   - Hazard ratios: quais fatores aceleram o churn?
   - Esta análise cabe em 1-2 dias e já eleva o patamar significativamente

2. **Criar taxonomy voluntary/involuntary** nos churn events
   - Classificar cada reason_code como V ou I
   - Se faltam dados de pagamento, estimar por padrão (ex: "budget" codes)

3. **Adicionar SHAP ao modelo de risco**
   - Explicar o score de cada uma das 21 contas em risco
   - "Por que esta conta tem score 85 e não 50?"

4. **Documentar como plataforma replicável**
   - O código atual (analysis.py) é um script único
   -> Refatorar como pipeline modular: load → transform → analyze → report
   -> Configurável por dataset (não só RavenStack)

---

## 8. Referências da Pesquisa

A pesquisa de mercado que embasa este plano foi conduzida por 4 agentes
especializados, cobrindo:

- **Consultorias globais**: McKinsey (NRR Advantage Framework, SaaSRadar),
  BCG (Deep Customer Engagement AI, SHoP Framework), Deloitte (InSightIQ, DDRP),
  Accenture (Patented Churn Prediction System, Customer Analytical Records),
  Bain (NPS 3.0, Earned Growth, NPS Prism), KPMG (Retention Fingerprint,
  Retention Play Catalog)
- **Consultorias brasileiras**: Falconi (Excelência Comercial, Mid Falconi),
  Foco Direto (Diagnóstico de Churn), Sales Hackers, Peers Consulting,
  Bruno Scott (O Código da Retenção)
- **Ferramentas**: Gainsight, ChurnZero, Totango, Catalyst, Planhat, Vitally,
  além de ferramentas nacionais (Metricaas.ai, SoftCS, ChurnAI, Fairview)
- **Benchmarks**: ChurnTools 2026, Vitally/Recurly 2025, SaaS Capital 2025,
  Focus Digital 2025, Kumo.ai 2026
- **Metodologias**: Survival analysis, uplift modeling, causal inference,
  health scoring, NRR frameworks
