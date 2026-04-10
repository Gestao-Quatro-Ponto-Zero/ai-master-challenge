# DealSignal — Lógica de Scoring

Esta seção explica como o **DealSignal** avalia e prioriza oportunidades no pipeline de vendas.

O objetivo é tornar a priorização de deals **transparente, explicável e acionável** para o time comercial.

---

# 1. Qualidade do Deal (Motores de Sinal)

O DealSignal avalia a força de cada oportunidade usando cinco motores de sinal.
Cada motor produz um score de 0 a 100 que alimenta o diagnóstico de fricção e a explicação do deal.

## 1.1 Seller Power (Força do Vendedor)

Mede o desempenho histórico do vendedor responsável pelo deal.

Principais features:

- `seller_win_rate` — taxa histórica de vitória do vendedor
- `seller_rank_percentile` — posição percentual no ranking do time
- `seller_close_speed` — velocidade média de fechamento (dias)
- `seller_product_experience` — quantidade de deals no combo vendedor × produto
- `seller_pipeline_load` — número de deals em aberto do vendedor
- `seller_product_win_rate` — win rate específico no produto atual

Vendedores com maior taxa de fechamento e experiência no produto tendem a aumentar a probabilidade de conversão.

---

## 1.2 Deal Momentum (Momento do Deal)

Avalia a velocidade e o avanço recente da oportunidade no pipeline.

Principais features:

- `log_days_since_engage` — log do tempo desde o último engajamento
- `deal_age_percentile` — posição percentual de idade frente ao pipeline
- `deal_value_percentile_within_seller` — valor do deal vs. histórico do vendedor
- `deal_value_percentile_within_product` — valor do deal vs. histórico do produto

Deals que avançam rapidamente e têm valor compatível com o histórico do vendedor/produto têm maior chance de fechamento.

---

## 1.3 Product Performance (Performance do Produto)

Mede o desempenho histórico de conversão do produto envolvido.

Principais features:

- `product_win_rate` — taxa histórica de vitória por produto
- `product_rank_percentile` — posição percentual do produto no portfólio
- `product_avg_sales_cycle` — ciclo médio de fechamento (dias)
- `product_relative_performance` — win rate do produto ÷ win rate global

Produtos com maior taxa histórica de conversão aumentam a confiança no deal.

---

## 1.4 Account Strength (Força da Conta)

Avalia a qualidade econômica e maturidade digital da empresa cliente.

Principais features:

- `account_size_percentile` — percentil de receita da conta no base de clientes
- `digital_maturity_index` — maturidade digital normalizada (0–1)
- `revenue_per_employee` — receita por funcionário
- `company_age_score` — idade da empresa normalizada (0–1)

Empresas maiores, mais maduras e com maior presença digital tendem a apresentar maior capacidade de compra e decisão mais estruturada.

---

## 1.5 Stagnation Risk (Risco de Estagnação)

Identifica deals parados ou em situação de risco operacional.

Principais features (flags binárias):

- `is_stale_flag` — deal acima do 75º percentil de idade
- `is_very_old_deal` — deal acima do 90º percentil de idade
- `deal_estagnado` — deal sem avanço (≥ p90 dias)
- `deal_muito_antigo` — deal crítico (≥ p95 dias)
- `seller_overloaded_flag` — vendedor sobrecarregado (pipeline acima do p75)
- `low_product_performance_flag` — produto abaixo do 33º percentil de rank
- `produto_fraco` — win rate do produto abaixo da média global
- `conta_fraca` — conta abaixo do 33º percentil de tamanho

Deals com múltiplos flags de risco recebem penalização na probabilidade de fechamento.

---

# 2. Probabilidade de Fechamento (Win Probability)

O DealSignal utiliza **regressão logística** treinada sobre 6.711 deals históricos (Won/Lost).

Pipeline de transformação:

```
Dados brutos → Feature Engineering (79 features)
             → Target Encoding (31 categóricas, smoothing m=10)
             → StandardScaler (48 numéricas)
             → L1 Feature Selection (LogisticRegression C=0.03)
             → Modelo final (LogisticRegression C=0.5)
             → Win Probability
```

Forma geral do modelo:

```
z = β0 + β1x1 + β2x2 + ... + βnxn
P(win) = 1 / (1 + e^(-z))
```

Onde `xi` são as features selecionadas e `βi` os coeficientes aprendidos.

Exemplo:
```
z = 0.70  →  Win Probability = 66.8%
```

**Performance:** AUC-ROC = 0.674 (validação cruzada 5-fold, out-of-fold)

---

# 3. Receita Esperada (Expected Revenue)

O DealSignal prioriza oportunidades com base no **impacto financeiro esperado**.

```
Expected Revenue = Win Probability × Deal Value
```

Exemplo:
```
Win Probability = 66.8%
Deal Value      = R$ 4.823
Expected Revenue = 0.668 × 4.823 = R$ 3.222
```

Isso permite que o time de vendas priorize oportunidades com maior impacto potencial.

---

# 4. Rating do Deal

Para facilitar a tomada de decisão, a probabilidade de fechamento é convertida em um **sistema de rating** inspirado no rating bancário.

| Rating | Win Probability |
|--------|-----------------|
| AAA    | > 90%           |
| AA     | 80 – 90%        |
| A      | 70 – 80%        |
| BBB    | 60 – 70%        |
| BB     | 50 – 60%        |
| B      | 40 – 50%        |
| CCC    | < 40%           |

Exemplo:
```
Win Probability = 66.8%  →  Rating = BBB
```

---

# 5. Diagnóstico de Fricção

Além do score, o DealSignal identifica o **principal obstáculo comercial** de cada deal — a fricção dominante — usando um motor baseado em regras determinísticas.

## Tipos de Fricção

| Fricção | Label | Interpretação |
|---|---|---|
| `execucao` | Execução / Fechamento | Deal próximo de fechar — remover barreiras operacionais |
| `decisao` | Decisão Pendente | Deal bem qualificado mas travado na decisão |
| `urgencia` | Risco de Engajamento | Engajamento se deteriorando — reativar urgentemente |
| `valor` | Proposta de Valor | Cliente ainda não convencido do impacto |

## Confiança do Diagnóstico

A confiança é calculada pela margem entre o score da fricção dominante e o segundo colocado:

| Margem | Confiança |
|---|---|
| > 0.30 | Alto |
| 0.15 – 0.30 | Médio |
| < 0.15 | Baixo |

---

# 6. Próxima Ação (Next Best Action)

Com base na fricção identificada, o DealSignal recomenda a **ação mais adequada** a partir de um catálogo fixo de 11 ações:

| Chave | Ação |
|---|---|
| `confirmar_decisor` | Confirmar decisor |
| `validar_orcamento` | Validar orçamento |
| `confirmar_prazo` | Confirmar prazo |
| `agendar_reuniao` | Agendar reunião |
| `enviar_proposta` | Enviar proposta |
| `alinhar_criterios` | Alinhar critérios de decisão |
| `reengajar_insight` | Reengajar com insight |
| `explorar_impacto` | Explorar impacto |
| `validar_prioridade` | Validar prioridade |
| `confirmar_aprovacao` | Confirmar aprovação |
| `negociar_condicoes` | Negociar condições |
| `avancar_assinatura` | Avançar para assinatura |

---

# 7. Priorização do Pipeline (Envio de Email)

Para o envio manual de prioridades por email, o DealSignal aplica critérios distintos de seleção e ordenação.

## Critérios de Prioridade

Um deal é considerado prioritário se **qualquer** condição for verdadeira:

- `rating == "C"`
- `friction == "high"`
- `days_in_stage > 20`
- `win_probability < 0.55`

## Cálculo do Priority Score

Os deals prioritários são ordenados por:

```
priority_score = (100 - final_score) + (days_in_stage × 1.5) + friction_weight

friction_weight: high = 20 | medium = 10 | low = 0
```

Os **5 deals com maior priority_score** são incluídos no email.

---

# 8. Fluxo Completo do Scoring

```
Dados do Deal (CRM / API)
        ↓
Feature Engineering (79 features)
        ↓
Target Encoding + StandardScaler
        ↓
Modelo Logístico → Win Probability
        ↓
Rating (AAA–CCC) + Expected Revenue
        ↓
Motores de Sinal (5 engines → scores 0–100)
        ↓
Friction Engine → Fricção dominante + Confiança
        ↓
Next Best Action → Ação recomendada
        ↓
Explicação narrativa do deal
```

---

# 9. Por que essa abordagem

O DealSignal combina:

- **Machine learning** — regressão logística treinada em histórico real de Won/Lost
- **Impacto financeiro** — Expected Revenue orienta priorização por retorno potencial
- **Explicabilidade** — friction engine e engine scores tornam o diagnóstico interpretável
- **Acionabilidade** — Next Best Action traduz o diagnóstico em ação concreta
- **Integração** — API REST permite scoring em tempo real a partir do CRM

O resultado é um sistema de priorização de pipeline **orientado por dados, transparente e fácil de interpretar para o time de vendas**.
