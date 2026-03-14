# DealSignal — Lógica de Scoring

Esta seção explica como o **DealSignal** avalia e prioriza oportunidades no pipeline de vendas.

O objetivo é tornar a priorização de deals **transparente, explicável e acionável** para o time comercial.

---

# 1. Qualidade do Deal (Motores de Sinal)

O DealSignal avalia a força de cada oportunidade usando quatro motores de sinal.

## 1.1 Seller Power (Força do Vendedor)

Mede o desempenho histórico do vendedor responsável pelo deal.

Principais fatores:

- `agent_win_rate`
- `agent_avg_deal_value`
- `agent_close_velocity`

Vendedores com maior taxa de fechamento tendem a aumentar a probabilidade de conversão do deal.

---

## 1.2 Deal Momentum (Momento do Deal)

Avalia a velocidade com que a oportunidade avança no pipeline.

Principais fatores:

- `days_since_engage`
- `pipeline_velocity`
- `stage_progression_speed`

Deals que avançam rapidamente no pipeline geralmente têm maior chance de fechamento.

---

## 1.3 Product Performance (Performance do Produto)

Mede o desempenho histórico de conversão do produto.

Principais fatores:

- `product_win_rate`
- `product_avg_close_value`
- `product_sales_cycle`

Produtos com maior taxa histórica de conversão aumentam a confiança no deal.

---

## 1.4 Account Strength (Força da Conta)

Avalia a qualidade econômica e maturidade da empresa cliente.

Principais fatores:

- `revenue`
- `employees`
- `revenue_per_employee`
- `company_age`
- `digital_presence_score`

Empresas maiores ou mais maduras tendem a apresentar maior capacidade de compra.

---

# 2. Probabilidade de Fechamento (Win Probability)

O DealSignal utiliza **regressão logística** para estimar a probabilidade de um deal ser fechado.

Forma geral do modelo:

z = β0 + β1x1 + β2x2 + ... + βnxn


Onde:

- `xi` representam as features do deal
- `βi` representam os coeficientes aprendidos pelo modelo

O resultado é transformado em probabilidade usando a função sigmoide:

P(win) = 1 / (1 + e^(-z))


Exemplo:
z = 0.70
Win Probability = 0.668 (66.8%)


---

# 3. Receita Esperada (Expected Revenue)

O DealSignal prioriza oportunidades com base no **impacto financeiro esperado**.

Fórmula:

Expected Revenue = Win Probability × Deal Value


Exemplo:

Win Probability = 66.8%
Deal Value = $4,823

Expected Revenue = 0.668 × 4,823 = $3,222


Isso permite que o time de vendas priorize oportunidades com maior impacto potencial.

---

# 4. Rating do Deal

Para facilitar a tomada de decisão, a probabilidade de fechamento é convertida em um **sistema de rating**.

| Rating | Probabilidade de Fechamento |
|------|-----------------------------|
| AAA | > 90% |
| AA | 80 – 90% |
| A | 70 – 80% |
| BBB | 60 – 70% |
| BB | 50 – 60% |
| B | 40 – 50% |
| CCC | < 40% |

Exemplo:

Win Probability = 66.8%
Rating = BBB


---

# 5. Regra de Priorização do Pipeline

O DealSignal prioriza oportunidades usando a **receita esperada**.

Priority Score = Win Probability × Deal Value


Isso garante que o pipeline priorize oportunidades com maior potencial de retorno financeiro.

---

# 6. Lógica Simplificada do Scoring

Para facilitar a compreensão na interface do produto, a lógica do DealSignal pode ser resumida assim:

**Signals (Sinais)**  
Seller Power + Deal Momentum + Product Performance + Account Strength

↓

**Prediction (Previsão)**  
Signals → Win Probability

↓

**Business Impact (Impacto de Negócio)**  
Win Probability × Deal Value = Expected Revenue

↓

**Decision Layer (Camada de Decisão)**  
Probability → Rating (AAA → CCC)

---

# 7. Por que essa abordagem

O DealSignal combina:

- **previsão baseada em machine learning**
- **cálculo de impacto financeiro**
- **motores de explicação do score**

O resultado é um sistema de priorização de pipeline **orientado por dados e fácil de interpretar para o time de vendas**.

