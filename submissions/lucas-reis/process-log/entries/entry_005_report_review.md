# Entry 005 — Review crítico do relatório executivo

**Data:** 2026-03-20
**Arquivos gerados:** executive_report.md, executive_summary_1page.md
**Autor:** Lucas Reis

---

## O que o relatório captura bem

### 1. A inversão de narrativa sobre o ML

O relatório transforma o AUC=0.34 (resultado tecnicamente ruim) em evidência de negócio:
*"se o modelo não consegue separar churners de retidos por comportamento, é porque o problema
não está no comportamento."* Esta é a conclusão mais sofisticada da análise inteira, e o
relatório a apresenta em linguagem acessível para um CEO não-técnico.

Essa inversão é difícil de fazer automaticamente — é preciso saber que AUC < 0.5 em contextos
com causa segmental é esperado e diagnóstico, não um fracasso do modelo.

### 2. O paradoxo do uso como "aha moment"

A seção "O paradoxo do uso" captura o achado mais contraintuitivo: churners usam mais o produto
que os que ficam. O relatório usa a analogia do cozinheiro para traduzir isso em intuição
executiva — funciona porque é concreto e descarta instantaneamente a solução errada (onboarding).

### 3. A seção "O que NÃO fazer"

Frequentemente omitida de relatórios de dados, esta seção é derivada diretamente das hipóteses
refutadas. Cada bullet tem uma hipótese específica como base:
- "não investir em onboarding" ← H3 refutada (uso igual entre churners e retidos)
- "não focar em SLA de suporte" ← H2/H4 refutadas (tickets urgentes → churn menor)
- "não segmentar por plano" ← H5 nulo perfeito (22.1% / 22.0% / 21.9%)

Isso transforma dados negativos (hipóteses refutadas) em valor positivo para o CEO.

### 4. Quantificação das ações

As 3 ações têm números concretos:
- Ação 1: $12,231 MRR em risco, meta de 50% = $73K ARR
- Ação 2: $25,248/mês potencial se DevTools churn cair para 16%
- Ação 3: estimativa de +$8–12K/mês com migração de 30% de event para partner

CEOs tomam decisões com números. Estimativas mesmo que aproximadas são mais úteis
que "potencial significativo".

---

## O que eu ajustaria com mais tempo

### 1. NLP do feedback_text

75% dos churn_events têm feedback_text preenchido. Uma análise de texto simples
(frequência de termos, clustering semântico) revelaria quais features específicas
os churners de DevTools mencionam. O relatório atual sabe que é "features" mas não
sabe se é "API de integração", "relatórios de produtividade", ou "automação de fluxo".

Com NLP: "Os 35 churners DevTools mencionam 'integração GitHub' e 'CI/CD pipeline'
em 71% dos feedbacks" seria muito mais acionável que o atual "product gap em DevTools".

### 2. Análise de cohort por data de signup

O dataset tem `signup_date`. Uma análise de cohorts mostraria se o churn está
acelerando nos cohorts mais recentes (produto piorando) ou se é estável (produto
sempre teve este problema). Isso mudaria a urgência da recomendação:
- Churn estável → problema crônico, roadmap
- Churn acelerando → problema agudo, resposta imediata

### 3. Análise de tenure até churn por segmento

Sabemos que buyer's remorse (preceding_upgrade_flag) sai em 165 dias vs 263 dias.
Seria útil saber: o churner DevTools sai em quantos dias? E o de event? Se DevTools
sai em 90 dias (curto), o problema é na proposta inicial. Se sai em 360 dias (longo),
o produto entregou valor por um tempo mas depois falhou.

### 4. Dashboard interativo

O prompt original mencionava Plotly para visualizações interativas. O relatório
está em markdown — um dashboard com os segmentos de churn, MRR em risco por tier,
e a lista CS filtrada por indústria seria mais consumível em uma reunião executiva.

---

## A frase mais importante do relatório e por quê

> *"O modelo de machine learning tentou prever quem vai sair com base em
> comportamento de uso. Não conseguiu — e isso é a descoberta mais importante."*

**Por quê esta é a frase mais importante:**

Ela inverte a expectativa. A maioria das pessoas leria "modelo falhou" como
*problema técnico*. A frase enquadra isso como *descoberta de negócio*.

Em termos de análise de dados, há dois tipos de falha de modelo:
1. Falha técnica (bug, dado errado, target errado) → precisa corrigir
2. Falha de sinal (o dado genuinamente não prediz o outcome) → é informação

Este modelo falhou por tipo 2. E tipo 2 significa: *a causa do churn não está onde
você está procurando.* Está no produto, não nos logs de uso.

Esta frase, com a explicação que a segue, evita que o CEO invista $300K
num sistema de detecção precoce baseado em comportamento de uso — que seria o
investimento errado dado o diagnóstico real. O valor desta frase é negativo
no sentido de "evitar gasto errado", o que frequentemente vale mais que
recomendar o gasto certo.

---

## Avaliação de completude do projeto

| Entregável | Status |
|-----------|--------|
| 01_eda_agent.py | ✅ Executado |
| 02_cross_table_agent.py | ✅ Executado |
| 03_hypothesis_agent.py | ✅ Executado |
| 04_predictive_agent.py | ✅ Executado |
| churn_scores.csv | ✅ Gerado (500 linhas) |
| executive_report.md | ✅ Gerado |
| executive_summary_1page.md | ✅ Gerado |
| process-log completo | ✅ 6 prompts + 10 entries |
| Dashboard Plotly | ⏳ Não implementado |
| NLP de feedback_text | ⏳ Não implementado |
| submissions/lucas-reis/README.md | ⏳ Atualizar com summary |

O projeto cobre os entregáveis principais. Dashboard e NLP são melhorias que
requerem tempo adicional mas não invalidam as conclusões do diagnóstico.
