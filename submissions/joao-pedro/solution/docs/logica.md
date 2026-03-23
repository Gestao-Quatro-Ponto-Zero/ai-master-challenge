# 🧠 Score-model

Documento técnico descrevendo como o sistema calcula scores e sugere ações para priorização de deals, equilibrando score geral

e viabilidade do vendedor. 

---

## 1. Visão Geral do Sistema

### Fluxo de Processamento

```
┌─────────────┐
│  Deal Input │
│  (8,800)    │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────┐
│   Feature Extraction             │
│   • days_in_pipeline             │
│   • sales_agent                  │
│   • product                      │
│   • close_value                  │
│   • account                      │
│   • deal_stage                   │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│   Calculate Components           │
│   ├─ Urgência (50%)              │
│   ├─ Probabilidade (30%)         │
│   └─ Valor (20%)                 │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│   Aggregate Score                │
│   Score = 0.5×URG + 0.3×PROB     │
│          + 0.2×VAL               │
│   Output: 0-100                  │
└──────┬───────────────────────────┘
       │
       ├─────────────────────┐
       │                     │
       ▼                     ▼
┌──────────────┐    ┌─────────────────┐
│ Score (0-100)│    │ Viability (0-100)│
│ Importância  │    │ Capacidade       │
│ objetiva     │    │ do vendedor      │
└──────┬───────┘    └────────┬────────┘
       │                     │
       └──────────┬──────────┘
                  │
                  ▼
         ┌────────────────┐
         │ Matrix Decision│
         │ Score × Viab   │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │ Action         │
         │ • PUSH HARD    │
         │ • TRANSFER     │
         │ • DISCARD      │
         │ • RE-QUALIFY   │
         │ • MONITOR      │
         └───────┬────────┘
                 │
         ┌───────▼────────────────────────────┐
         │ TRANSFER / CONSIDER_TRANSFER?      │
         │ viability < 40                     │
         └───────┬──────────────┬─────────────┘
                 │ sim          │ não
                 ▼              ▼
   ┌─────────────────────┐   (outros
   │ find_best_seller     │    fluxos)
   │ ─────────────────── │
   │ 1. Mesmo time        │
   │ 2. Mesma região      │
   │ 3. Outra região      │
   └──────────┬──────────┘
              │
              ▼
   ┌──────────────────────┐
   │ score_candidate()    │
   │ ─────────────────── │
   │ + prospecting        │
   │ + carga leve         │
   │ + WR produto         │
   │ + WR setor da conta  │
   │ + WR geral           │
   └──────────┬───────────┘
              │
              ▼
   ┌──────────────────────┐
   │ target_seller        │
   │ + why_this_helps     │
   │ + transfer_level     │
   │ + target_context     │
   └──────────────────────┘
```

### Princípios do Modelo

1. **Score mede importância objetiva** (igual para todos os vendedores)
2. **Viabilidade mede capacidade contextual** (varia por vendedor)
3. **Ação combina os dois** no momento de executar

---

## 2. Componentes do Score (50/30/20)

### 2.1 Urgência (50%) — "Há quanto tempo sem decisão?"

**Conceito:** Quanto tempo o deal está sem ser resolvido (fechado ou perdido).

#### Fórmula Base

```python
def calculate_urgency_base(days_in_pipeline: int) -> int:
    """
    Retorna urgência base (0-100) baseada em tempo sem decisão.
    
    Thresholds derivados das medianas reais:
    - Lost mediana: 14 dias
    - Won mediana: 57 dias
    - Engaging aberto mediana: 165 dias
    """
    if days_in_pipeline >= 200:
        return 100  # Crítico: além da média Engaging (199d)
    elif days_in_pipeline >= 165:
        return 80   # Congelado: mediana Engaging
    elif days_in_pipeline >= 85:
        return 60   # Atrasado: 1.5x Won mediana (57d)
    elif days_in_pipeline >= 57:
        return 40   # Limite: Won mediana (prazo venceu)
    elif days_in_pipeline >= 28:
        return 20   # Normal: 0.5x Won
    else:
        return 10   # Recente: ainda aquecendo
```

#### Tabela de Thresholds


| Dias        | Urgência Base | Categoria    | Origem do Threshold                              |
| ----------- | ------------- | ------------ | ------------------------------------------------ |
| **≥200**    | 100           | 🔴 CRÍTICO   | 3.5× Won mediana, além da média Engaging         |
| **165-199** | 80            | 🟠 CONGELADO | Mediana de Engaging aberto (deal típico travado) |
| **85-164**  | 60            | 🟡 ATRASADO  | 1.5× Won mediana (fora da curva normal)          |
| **57-84**   | 40            | 🟢 LIMITE    | Won mediana (prazo natural de fecho)             |
| **28-56**   | 20            | ⚪ NORMAL     | 0.5× Won (meio do caminho típico)                |
| **<28**     | 10            | ⚫ RECENTE    | Deal novo, deixar aquecer                        |


#### Multiplicadores

**1. Seller Factor (Sobrecarga):**

```python
def get_seller_load_factor(seller_active_deals: int) -> float:
    """
    Deals de vendedores sobrecarregados têm urgência amplificada.
    Média do time: 75 deals ativos.
    """
    if seller_active_deals > 150:
        return 1.3  # +30% urgência (muito sobrecarregado)
    elif seller_active_deals > 100:
        return 1.15 # +15% urgência (carga alta)
    else:
        return 1.0  # Neutro
```

**Justificativa:** Vendedor com 194 deals (caso real: Darcel) não consegue dar atenção adequada. Deals dele têm maior risco de neglect.

---

**2. Account Factor (Conta Difícil):**

```python
def get_account_difficulty_factor(account_historical_wr: float, 
                                   global_wr: float = 63.15) -> float:
    """
    Conta com histórico ruim + deal travado = urgência maior
    (precisa decidir logo se continua ou descarta).
    """
    if account_historical_wr < 40:
        return 1.2  # +20% urgência (conta muito difícil)
    else:
        return 1.0  # Neutro
```

**Justificativa:** Conta com 35% WR histórico + deal há 120 dias = combinação tóxica. Melhor forçar decisão rápida.

---

**3. Deal Oversize Factor:**

```python
def get_oversize_factor(close_value: float,
                        seller_avg_ticket: float) -> float:
    """
    Deal muito maior que experiência do vendedor.
    Pode estar intimidado/paralizado.
    """
    if close_value > 3 * seller_avg_ticket:
        return 1.15  # +15% urgência (precisa suporte/transfer)
    else:
        return 1.0  # Neutro
```

**Justificativa:** Vendedor com ticket médio $500 pegando deal de $25.000 = fora da zona de conforto. Precisa ação (coaching ou transferir).

---

#### Cálculo Final de Urgência

```python
def calculate_urgency(deal: dict, benchmarks: dict) -> float:
    """
    Urgência final com multiplicadores aplicados.
    """
    urgency_base = calculate_urgency_base(deal['days_in_pipeline'])
    
    # Multiplicadores
    seller_factor = get_seller_load_factor(
        benchmarks['seller_active_deals'][deal['sales_agent']]
    )
    
    account_factor = 1.0
    if deal['account'] in benchmarks['account_wr']:
        account_factor = get_account_difficulty_factor(
            benchmarks['account_wr'][deal['account']]
        )
    
    oversize_factor = get_oversize_factor(
        deal['close_value'],
        benchmarks['seller_avg_ticket'][deal['sales_agent']]
    )
    
    # Aplicar multiplicadores
    urgency = urgency_base * seller_factor * account_factor * oversize_factor
    
    # Clamp entre 0-100
    return min(100, max(0, urgency))
```

---

### 2.2 Probabilidade (30%) — "Vale tentar salvar?"

**Conceito:** Qual a chance real de fechar este deal, considerando todos os fatores contextuais.

#### Fórmula Base (Prior Bayesiano)

```python
GLOBAL_WIN_RATE = 63.15  # 4,238 Won / (4,238 Won + 2,473 Lost)

probability_base = GLOBAL_WIN_RATE
```

**Justificativa:** Antes de saber qualquer coisa sobre o deal, a chance baseline é o win rate geral.

---

#### Fatores Multiplicativos

**1. Seller Factor (Performance Individual):**

```python
def get_seller_factor(seller: str, benchmarks: dict) -> float:
    """
    Vendedor com WR 70% tem 1.11× probabilidade vs vendedor com 55% que tem 0.87×.
    Spread real: 70.39% (Hayden) a 54.98% (Lajuana) = 15.4 pontos.
    """
    seller_wr = benchmarks['seller_wr'].get(seller, GLOBAL_WIN_RATE)
    return seller_wr / GLOBAL_WIN_RATE
```

**Exemplo:**

- Hayden (70.39% WR) → 70.39 / 63.15 = **1.115** (+11.5%)
- Lajuana (54.98% WR) → 54.98 / 63.15 = **0.871** (-12.9%)

---

**2. Product Factor (Dificuldade do Produto):**

```python
def get_product_factor(product: str, benchmarks: dict) -> float:
    """
    GTK 500 (premium, $26k) tem WR 60% vs MG Special (entry, $55) com 64.8%.
    """
    product_wr = benchmarks['product_wr'].get(product, GLOBAL_WIN_RATE)
    return product_wr / GLOBAL_WIN_RATE
```

**Exemplo:**

- MG Special (64.8% WR) → 64.8 / 63.15 = **1.026** (+2.6%)
- GTK 500 (60.0% WR) → 60.0 / 63.15 = **0.950** (-5.0%)

---

**3. Account Factor (Histórico da Conta):**

```python
def get_account_factor(account: str, benchmarks: dict) -> float:
    """
    Conta com histórico de 35% WR tem probabilidade muito menor que 
    conta com 75% WR, independente do tamanho.
    """
    if account not in benchmarks['account_wr']:
        return 1.0  # Neutro (conta nova, sem histórico)
    
    account_wr = benchmarks['account_wr'][account]
    return account_wr / GLOBAL_WIN_RATE
```

**Exemplo:**

- Hottechi (58% WR histórico) → 58 / 63.15 = **0.918** (-8.2%)
- Conta sem histórico → **1.0** (neutro)

---

**4. Region Factor (Diferenças Geográficas):**

```python
def get_region_factor(region: str, benchmarks: dict) -> float:
    """
    West 63.9% vs Central 62.6% = 1.3 pontos de diferença.
    Impacto pequeno mas captura diferenças estruturais de mercado.
    """
    region_wr = benchmarks['region_wr'].get(region, GLOBAL_WIN_RATE)
    return region_wr / GLOBAL_WIN_RATE
```

**Exemplo:**

- West (63.94%) → 63.94 / 63.15 = **1.013** (+1.3%)
- Central (62.56%) → 62.56 / 63.15 = **0.991** (-0.9%)

---

**5. Especialização Produto × Vendedor (DIFERENCIAL):**

```python
def get_specialist_factor(seller: str, product: str, benchmarks: dict) -> float:
    """
    Detecta se vendedor é especialista (ou tem mismatch) neste produto.
    
    Dados reais:
    - Rosalina em GTK 500: 83.3% (vs 65.5% geral dela) = +17.8 pts
    - Elease em GTK 500: 58.3% (vs 63.5% geral dela) = -5.2 pts
    """
    combo_key = f"{product}|{seller}"
    
    if combo_key not in benchmarks['product_seller_wr']:
        return 1.0  # Sem dados suficientes (< 3 fechos)
    
    combo_wr = benchmarks['product_seller_wr'][combo_key]
    seller_avg_wr = benchmarks['seller_wr'][seller]
    
    delta = combo_wr - seller_avg_wr
    
    if delta > 5:
        return 1.15  # Especialista (+15%)
    elif delta < -10:
        return 0.85  # Mismatch (-15%)
    else:
        return 1.0   # Neutro
```

**Exemplo real:**

- Deal GTK 500 com Rosalina → **1.15** (especialista, +15%)
- Deal GTK 500 com Elease → **0.85** (mismatch, -15%)

---

#### Penalidades (Fatores de Risco)

**1. Tempo Excessivo:**

```python
def get_time_penalty(days_in_pipeline: int) -> float:
    """
    Deal que ultrapassou MUITO o tempo típico de Lost (14d mediana)
    tem probabilidade reduzida.
    """
    LOST_MEDIAN = 14
    
    if days_in_pipeline > 2.5 * LOST_MEDIAN:  # > 35 dias
        return 0.75  # -25% probabilidade
    elif days_in_pipeline > 1.5 * WON_MEDIAN:  # > 85.5 dias
        return 0.90  # -10% probabilidade
    else:
        return 1.0   # Neutro
```

**Justificativa:** Se passou 35+ dias sem fechar nem perder, algo estrutural está errado (budget, decisor, fit). Probabilidade real é menor.

---

**2. Deal Oversized:**

```python
def get_oversize_penalty(close_value: float,
                         seller_avg_ticket: float) -> float:
    """
    Deal 3x+ maior que experiência do vendedor = risco de execução.
    """
    if close_value > 3 * seller_avg_ticket:
        return 0.90  # -10% probabilidade
    else:
        return 1.0   # Neutro
```

**Justificativa:** Vendedor habituado a deals de $500 pegando $25.000 = ciclo diferente, stakeholders diferentes, risco maior.

---

**3. Seller Overload:**

```python
def get_overload_penalty(seller_active_deals: int) -> float:
    """
    Vendedor sobrecarregado dá menos atenção por deal.
    """
    if seller_active_deals > 150:
        return 0.85  # -15% probabilidade
    elif seller_active_deals > 100:
        return 0.92  # -8% probabilidade
    else:
        return 1.0   # Neutro
```

**Justificativa:** Darcel com 194 deals = atenção diluída. Cada deal tem menor chance de fechar.

---

#### Cálculo Final de Probabilidade

```python
def calculate_probability(deal: dict, benchmarks: dict) -> float:
    """
    Probabilidade final com todos os fatores.
    """
    prob = GLOBAL_WIN_RATE
    
    # Fatores multiplicativos
    prob *= get_seller_factor(deal['sales_agent'], benchmarks)
    prob *= get_product_factor(deal['product'], benchmarks)
    
    if deal['account'] in benchmarks['account_wr']:
        prob *= get_account_factor(deal['account'], benchmarks)
    
    prob *= get_region_factor(deal['region'], benchmarks)
    prob *= get_specialist_factor(deal['sales_agent'], deal['product'], benchmarks)
    
    # Penalidades
    prob *= get_time_penalty(deal['days_in_pipeline'])
    prob *= get_oversize_penalty(deal['close_value'], 
                                  benchmarks['seller_avg_ticket'][deal['sales_agent']])
    prob *= get_overload_penalty(benchmarks['seller_active_deals'][deal['sales_agent']])
    
    # Clamp entre 0-100
    return min(100, max(0, prob))
```

---

### 2.3 Valor (20%) — "Prioridade entre travados?"

**Conceito:** Não é o `close_value` absoluto, mas o **valor ajustado pela viabilidade e contexto estratégico**.

#### Por que Percentil (não valor bruto)?

**Distribuição real dos dados:**

- Mediana: $472
- Média: $1,491
- Assimetria: 3.2× (cauda pesada)

**Problema com valor absoluto:**

```python
# Ruim:
value_score = close_value / 1000  # Deal $10k = score 10, $1k = score 1

# Problema: Linear não reflete realidade
# - 80% dos deals < $2k
# - 15% dos deals $2k-$10k  
# - 5% dos deals > $10k
```

**Solução: Percentil**

```python
def calculate_value_percentile(close_value: float, 
                                value_distribution: list) -> float:
    """
    Retorna posição percentil (0-100) do valor no dataset.
    
    Exemplo:
    - $472 (mediana) → percentil 50
    - $10,000 → percentil ~95
    - $26,768 (GTK 500) → percentil ~98
    """
    sorted_values = sorted(value_distribution)
    position = sum(1 for v in sorted_values if v <= close_value)
    percentile = (position / len(sorted_values)) * 100
    return percentile
```

---

#### Ajustes ao Percentil Base

**1. Produto Premium:**

```python
def apply_premium_product_bonus(percentile: float, product: str) -> float:
    """
    GTK 500 ($26k) é único produto premium/enterprise.
    Fechar abre conta para upsell futuro = valor estratégico.
    """
    if product == 'GTK 500':
        return percentile * 1.20  # +20%
    else:
        return percentile
```

---

**2. Conta Estratégica:**

```python
def apply_strategic_account_bonus(percentile: float, 
                                   account: str,
                                   top_accounts: list) -> float:
    """
    Top 20 contas por volume (ex: Hottechi com 200 deals).
    Lifetime value > valor do deal individual.
    """
    if account in top_accounts:
        return percentile * 1.15  # +15%
    else:
        return percentile
```

**Justificativa:** Perder deal pequeno ($500) com Hottechi pode fechar porta para deals futuros. Relacionamento tem valor.

---

**3. Desconto por Baixa Probabilidade:**

```python
def apply_probability_discount(percentile: float, probability: float) -> float:
    """
    Valor esperado = Valor × Probabilidade.
    Deal grande com chance baixa vale menos que deal médio com chance alta.
    """
    if probability < 40:
        return percentile * 0.70  # -30%
    elif probability < 55:
        return percentile * 0.85  # -15%
    else:
        return percentile  # Sem desconto
```

**Exemplo:**

- Deal $50k, prob 20% → Valor esperado = $10k
- Deal $15k, prob 70% → Valor esperado = $10.5k
- **Deal menor vence** (mesma expectativa, mais viável)

---

#### Cálculo Final de Valor

```python
def calculate_value(deal: dict, benchmarks: dict) -> float:
    """
    Valor ponderado final.
    """
    # Percentil base
    value = calculate_value_percentile(
        deal['close_value'],
        benchmarks['value_distribution']
    )
    
    # Ajustes
    value = apply_premium_product_bonus(value, deal['product'])
    value = apply_strategic_account_bonus(value, deal['account'], 
                                          benchmarks['top_20_accounts'])
    
    # Desconto por baixa prob (calculada anteriormente)
    probability = deal['_probability']  # Já calculado
    value = apply_probability_discount(value, probability)
    
    # Clamp
    return min(100, max(0, value))
```

---

### 2.4 Agregação Final do Score

```python
def calculate_score(deal: dict, benchmarks: dict) -> dict:
    """
    Score final (0-100) com breakdown de componentes.
    """
    urgency = calculate_urgency(deal, benchmarks)
    probability = calculate_probability(deal, benchmarks)
    
    # Armazena prob para uso no cálculo de valor
    deal['_probability'] = probability
    
    value = calculate_value(deal, benchmarks)
    
    # Agregação ponderada
    score = (
        0.50 * urgency +
        0.30 * probability +
        0.20 * value
    )
    
    return {
        'score': round(score, 1),
        'urgency': round(urgency, 1),
        'probability': round(probability, 1),
        'value': round(value, 1)
    }
```

---

## 3. Viabilidade (0-100, Separada do Score)

### 3.1 Por que Separada?

**Score** = Importância objetiva do deal

- "Este deal PRECISA de atenção?" (urgente, viável, valioso)
- Mesma para todos os vendedores

**Viabilidade** = Capacidade do vendedor resolver

- "Este vendedor CONSEGUE dar atenção adequada?"
- Varia por vendedor

**Ação** = f(Score, Viabilidade)

- Score 72 + Viab 65% → "Push hard"
- Score 72 + Viab 20% → "Transfer"

---

### 3.2 Cálculo de Viabilidade

```python
def calculate_viability(seller: str, 
                        product: str,
                        benchmarks: dict) -> float:
    """
    Viabilidade (0-100) baseada em capacidade do vendedor.
    """
    viability_base = 50  # Ponto neutro
    
    # Fator 1: Prospecting (pipeline novo)
    prospecting_count = benchmarks['seller_prospecting'].get(seller, 0)
    
    if prospecting_count == 0:
        prospecting_factor = 0.5  # -50% (SEM pipeline novo)
    elif prospecting_count < 10:
        prospecting_factor = 0.8  # -20%
    elif prospecting_count <= 30:
        prospecting_factor = 1.0  # Neutro
    else:  # > 30
        prospecting_factor = 1.3  # +30% (pipeline saudável)
    
    # Fator 2: Carga (deals ativos)
    active_deals = benchmarks['seller_active_deals'].get(seller, 75)
    
    if active_deals > 150:
        load_factor = 0.6   # -40% (sobrecarregado)
    elif active_deals > 100:
        load_factor = 0.8   # -20%
    elif active_deals >= 40:
        load_factor = 1.0   # Neutro
    elif active_deals > 0:
        load_factor = 1.3   # +30% (tem tempo)
    else:  # 0 deals
        load_factor = 1.5   # +50% (totalmente disponível)
    
    # Fator 3: Especialização (já calculado antes)
    specialist_factor = get_specialist_factor(seller, product, benchmarks)
    
    # Se specialist_factor for para probabilidade, mapear para viabilidade:
    if specialist_factor == 1.15:
        specialist_viab = 1.2  # Especialista
    elif specialist_factor == 0.85:
        specialist_viab = 0.8  # Mismatch
    else:
        specialist_viab = 1.0  # Neutro
    
    # Calcular viabilidade final
    viability = viability_base * prospecting_factor * load_factor * specialist_viab
    
    # Clamp
    return min(100, max(0, viability))
```

---

### 3.3 Exemplos de Viabilidade

**Exemplo 1: Darcel (Sobrecarregado COM prospecting)**

```python
prospecting_count = 35      → factor = 1.3 (saudável)
active_deals = 194          → factor = 0.6 (muito sobrecarregado)
specialist = 1.0            → factor = 1.0 (neutro)

viability = 50 × 1.3 × 0.6 × 1.0 = 39
```

**Interpretação:** Pipeline novo é bom, mas carga alta prejudica capacidade.

---

**Exemplo 2: Anna (Sobrecarregada SEM prospecting)**

```python
prospecting_count = 0       → factor = 0.5 (crítico)
active_deals = 112          → factor = 0.8 (carga alta)
specialist = 1.0            → factor = 1.0 (neutro)

viability = 50 × 0.5 × 0.8 × 1.0 = 20
```

**Interpretação:** Sem pipeline novo + carga alta = viabilidade péssima.

---

**Exemplo 3: Wilburn (Leve COM prospecting)**

```python
prospecting_count = 25      → factor = 1.0 (neutro)
active_deals = 31           → factor = 1.3 (tem tempo)
specialist = 1.0            → factor = 1.0 (neutro)

viability = 50 × 1.0 × 1.3 × 1.0 = 65
```

**Interpretação:** Carga leve + pipeline ok = boa capacidade.

---

## 4. Matriz de Ação (Score × Viabilidade)

### 4.1 Lógica de Decisão

```python
def suggest_action(score: float, 
                   urgency: float,
                   probability: float,
                   viability: float) -> dict:
    """
    Deriva ação baseada em score × viabilidade.
    """
    
    # CASO 1: Score alto (crítico/high)
    if score >= 70:
        if viability >= 60:
            return {
                'action': 'PUSH_HARD',
                'icon': '🔥',
                'message': 'Critical deal — close or discard this week',
                'reason': 'High urgency + you have capacity'
            }
        
        elif viability >= 40:
            return {
                'action': 'RE_QUALIFY',
                'icon': '🔄',
                'message': 'Re-validate budget/timeline/authority before pushing',
                'reason': 'High urgency but limited capacity — qualify to avoid waste'
            }
        
        else:  # viability < 40
            if probability >= 60:
                return {
                    'action': 'TRANSFER',
                    'icon': '🔀',
                    'message': f'Transfer to {find_best_seller(deal)}',
                    'reason': 'Important deal but you cannot action (no prospecting/overloaded)',
                    'expected_impact': '+15% close probability with focused seller'
                }
            else:
                return {
                    'action': 'DISCARD',
                    'icon': '❌',
                    'message': 'Move to Lost — low probability + low capacity',
                    'reason': 'Not worth transfer (low probability)'
                }
    
    # CASO 2: Score médio (60-69)
    elif score >= 60:
        if viability >= 60:
            return {
                'action': 'ACCELERATE',
                'icon': '⚡',
                'message': 'Push to close this week',
                'reason': 'Good opportunity + you have capacity'
            }
        
        elif viability < 40:
            return {
                'action': 'CONSIDER_TRANSFER',
                'icon': '🔀',
                'message': f'Consider transferring to {find_best_seller(deal)}',
                'reason': 'Medium priority + low capacity = may benefit from transfer'
            }
        
        else:
            return {
                'action': 'INVESTIGATE',
                'icon': '🔍',
                'message': 'Understand what is blocking',
                'reason': 'Medium urgency + medium capacity'
            }
    
    # CASO 3: Score baixo (<60)
    else:
        return {
            'action': 'MONITOR',
            'icon': '⏸',
            'message': 'Continue standard engagement',
            'reason': 'Not urgent yet'
        }
```

---

### 4.2 Matriz Visual


| Score / Viab      | Alta (>60)   | Média (40-60)  | Baixa (<40)              |
| ----------------- | ------------ | -------------- | ------------------------ |
| **Alta (≥70)**    | 🔥 PUSH HARD | 🔄 RE-QUALIFY  | 🔀 TRANSFER ou ❌ DISCARD |
| **Média (60-69)** | ⚡ ACCELERATE | 🔍 INVESTIGATE | 🔀 CONSIDER TRANSFER     |
| **Baixa (<60)**   | ✓ MONITOR    | ✓ MONITOR      | ⏸ LOW PRIORITY           |


---

## 5. Exemplos Trabalhados

### 5.1 Deal Crítico (Score 94)

#### Input

```python
deal = {
    'deal_id': '4521',
    'account': 'Hottechi',
    'product': 'GTX Pro',
    'sales_agent': 'Anna Snelling',
    'days_in_pipeline': 215,
    'close_value': 4850,
    'deal_stage': 'Engaging',
    'region': 'West'
}
```

#### Cálculo Passo-a-Passo

**URGÊNCIA:**

```python
# Base
days = 215 → urgency_base = 100 (≥200)

# Multiplicadores
seller_active = 112 → seller_factor = 1.15 (>100)
account_wr = 58% → account_factor = 1.0 (≥40%)
oversize = 4850 / 800 = 6× → oversize_factor = 1.15

urgency = 100 × 1.15 × 1.0 × 1.15 = 132 → clamp to 100
```

**PROBABILIDADE:**

```python
# Base
prob = 63.15

# Fatores
seller: 61.9 / 63.15 = 0.98
product: 63.6 / 63.15 = 1.01
account: 58 / 63.15 = 0.92
region: 63.9 / 63.15 = 1.01
specialist: 1.0 (sem dados específicos)

# Penalidades
time: 215 > 35 → 0.75
oversize: 4850 > 2400 → 0.90
overload: 112 > 100 → 0.92

prob = 63.15 × 0.98 × 1.01 × 0.92 × 1.01 × 1.0 × 0.75 × 0.90 × 0.92
     = 37.2%
```

**VALOR:**

```python
percentile(4850) = 82

# Ajustes
strategic_account (Hottechi top 5): 82 × 1.15 = 94.3
low_prob (37% < 40%): 94.3 × 0.70 = 66

value = 66
```

**SCORE FINAL:**

```python
score = 0.50 × 100 + 0.30 × 37.2 + 0.20 × 66
      = 50 + 11.16 + 13.2
      = 74.36 → 74.4
```

**VIABILIDADE:**

```python
Anna: 0 prospecting, 112 deals

viability = 50 × 0.5 × 0.8 × 1.0 = 20
```

**AÇÃO:**

```python
score 74 (HIGH) + viab 20 (BAIXA) + prob 37 (BAIXA)
→ DISCARD ou TRANSFER

Como prob < 60: DISCARD
```

#### Output

```json
{
  "score": 74.4,
  "urgency": 100,
  "probability": 37.2,
  "value": 66,
  "viability": 20,
  "action": {
    "type": "DISCARD",
    "icon": "❌",
    "message": "Move to Lost — frozen 7+ months with low probability",
    "reason": "Strategic account but stuck too long + seller overloaded + no prospecting"
  }
}
```

---

### 5.2 Deal Hot (Score 71)

#### Input

```python
deal = {
    'deal_id': '2341',
    'account': 'Kan-code',
    'product': 'GTK 500',
    'sales_agent': 'Rosalina Dieter',
    'days_in_pipeline': 42,
    'close_value': 26500,
    'deal_stage': 'Engaging',
    'region': 'West'
}
```

#### Cálculo Resumido

**URGÊNCIA:** 20 (days 42 < 57, normal)

**PROBABILIDADE:**

```python
# Base: 63.15
# Seller: 65.5 / 63.15 = 1.04
# Product: 60 / 63.15 = 0.95
# Account: 68 / 63.15 = 1.08
# Specialist: Rosalina em GTK = 1.15 (83% vs 65%)
# Penalidades: nenhuma (tempo ok, não oversize, não overload)

prob = 63.15 × 1.04 × 0.95 × 1.08 × 1.15 = 79.5%
```

**VALOR:**

```python
percentile(26500) = 98
× 1.20 (GTK 500 premium)
× 1.15 (Kan-code top 2)
= 100 (clamp)
```

**SCORE:** 0.50×20 + 0.30×79.5 + 0.20×100 = **53.9**

**VIABILIDADE:** Rosalina: 15 prosp, 50 deals → **60**

**AÇÃO:** score 54 (BAIXO) + viab 60 (BOA) → **MONITOR** (ainda não urgente)

#### Output

```json
{
  "score": 53.9,
  "action": {
    "type": "MONITOR",
    "icon": "✓",
    "message": "On track — continue standard engagement",
    "reason": "Recent deal (42d), high probability (79%), specialist match"
  }
}
```

**Nota:** Apesar de ser deal grande e especialista, urgência baixa (42d < 57d) mantém score moderado. Sistema não força ação prematura.

---

### 5.3 Deal para Transfer (Score 72)

#### Input

```python
deal = {
    'deal_id': '3241',
    'account': 'Acme Corp',
    'product': 'GTX Basic',
    'sales_agent': 'Anna Snelling',  # 0 prospecting, 112 deals
    'days_in_pipeline': 180,
    'close_value': 550,
    'deal_stage': 'Engaging',
    'region': 'East'
}
```

#### Comparação: Anna vs Wilburn (mesmo deal)

**Deal com Anna:**

```
URG: 80 (180 dias)
PROB: 58% (Anna 61.9%, produto ok, sem especialização)
VAL: 25 (baixo valor, $550)
VIAB: 20 (0 prospecting, 112 deals)

Score = 0.50×80 + 0.30×58 + 0.20×25 = 62.4
Ação = TRANSFER (score médio-alto, viab baixa)
```

**Mesmo deal com Wilburn:**

```
URG: 80 (mesmo deal, 180 dias)
PROB: 60% (Wilburn similar, sem especialização)
VAL: 25 (mesmo valor)
VIAB: 65 (25 prospecting, 31 deals)

Score = 0.50×80 + 0.30×60 + 0.20×25 = 63
Ação = PUSH HARD (score médio-alto, viab boa)
```

#### Output (para Anna)

```json
{
  "score": 62.4,
  "action": {
    "type": "TRANSFER",
    "icon": "🔀",
    "message": "Transfer to Wilburn Farren",
    "reason": "Stuck 6 months but you cannot give adequate attention (0 prospecting, high load)",
    "expected_impact": "Close probability 58% → 65% with transfer"
  }
}
```

**Insight:** Score é praticamente idêntico (62.4 vs 63), mas **ação completamente diferente** baseada em viabilidade.

---

## 6. Edge Cases e Tratamentos

### 6.1 Dados Faltantes

**Caso: Account sem histórico de WR**

```python
if account not in benchmarks['account_wr']:
    account_factor = 1.0  # Neutro (não penaliza nem bonifica)
```

**Caso: Vendedor sem fechos (novo)**

```python
if seller not in benchmarks['seller_wr']:
    seller_wr = GLOBAL_WIN_RATE  # Prior bayesiano (63.15%)
```

**Caso: Combinação produto×vendedor sem dados**

```python
if combo_key not in benchmarks['product_seller_wr']:
    specialist_factor = 1.0  # Neutro (precisa ≥3 fechos)
```

---

### 6.2 Outliers

**Caso: close_value extremo**

```python
# Evitar que um deal de $1M distorça todo o percentil
if close_value > percentile_99:
    close_value = percentile_99  # Clamp no 99º percentil
```

**Caso: days_in_pipeline > 365**

```python
# Evitar que deal de 2 anos distorça thresholds
if days_in_pipeline > 365:
    days_in_pipeline = 365  # Trata como 1 ano (máximo)
```

---

### 6.3 Divisão por Zero

**Caso: seller_avg_ticket = 0** (vendedor só com Lost ou sem closes)

```python
if seller_avg_ticket == 0:
    oversize_factor = 1.0  # Não aplica penalidade
```

**Caso: seller_active_deals = 0** (vendedor sem pipeline)

```python
if seller_active_deals == 0:
    load_factor = 1.5  # Totalmente disponível
```

---

### 6.4 Score Bounds

**Garantia de range:**

```python
# Score SEMPRE entre 0-100
score = min(100, max(0, score))

# Idem para componentes
urgency = min(100, max(0, urgency))
probability = min(100, max(0, probability))
value = min(100, max(0, value))
viability = min(100, max(0, viability))
```

---

### 6.5 Ação Sempre Definida

```python
# NUNCA retornar ação = None
if action is None:
    action = {
        'type': 'MONITOR',
        'message': 'Default action (insufficient data)',
        'reason': 'Could not determine specific action'
    }
```

---

## 7. Calibração e Validação

### 7.1 Como Thresholds Foram Escolhidos

**Baseados nas medianas reais dos cohorts:**

```python
# Dados brutos das métricas
LOST_MEDIAN = 14 dias     # 50% dos Lost fecham em ≤14 dias
WON_MEDIAN = 57 dias      # 50% dos Won fecham em ≤57 dias
ENGAGING_MEDIAN = 165 dias # 50% dos Engaging estão há ≥165 dias

# Thresholds derivados
CRITICAL = 200  # 3.5× Won, além da média Engaging (199d)
FROZEN = 165    # Mediana Engaging
DELAYED = 85    # 1.5× Won
LIMIT = 57      # Won mediana
NORMAL = 28     # 0.5× Won
```

**Por que não usar números redondos (30d, 60d, 90d)?**

- ❌ Arbitrário (não reflete dados reais)
- ✅ Medianas são **objetivas**, derivadas empiricamente

---

### 7.2 Como Pesos Foram Definidos (50/30/20)

**Processo:**

1. **Análise do problema:** Gargalo é tempo (165d vs 57d vs 14d)
2. **Hipótese:** Urgência deve dominar (foco em destravar)
3. **Teste conceitual:** 40/30/30 vs 50/30/20
4. **Decisão:** 50% urgência (problema é TEMPO sem decisão)

**Validação futura (A/B test):**

```python
# Grupo A: 50/30/20
# Grupo B: 60/25/15
# Métrica: Tempo médio de resolução (Won + Lost) / dias
```

---

### 7.3 Testes de Sanidade

**1. Monotonia:**

```python
# Mais dias = mais urgência (sempre)
assert urgency(200) > urgency(165) > urgency(85)

# Maior WR vendedor = maior prob
assert prob(seller='Hayden') > prob(seller='Lajuana')
```

**2. Bounds:**

```python
# Scores sempre no range
for deal in all_deals:
    assert 0 <= deal['score'] <= 100
    assert 0 <= deal['viability'] <= 100
```

**3. Consistência:**

```python
# Mesmo deal, mesmo score (determinístico)
score1 = calculate_score(deal, benchmarks)
score2 = calculate_score(deal, benchmarks)
assert score1 == score2
```

---

## 8. Referência Rápida

### Fórmulas Principais

```python
# Score Final
score = 0.50 × urgency + 0.30 × probability + 0.20 × value

# Urgência
urgency = urgency_base(days) × seller_factor × account_factor × oversize_factor

# Probabilidade
prob = 63.15 × seller × product × account × region × specialist 
       × time_penalty × oversize_penalty × overload_penalty

# Valor
value = percentile(close_value) × premium × strategic × prob_discount

# Viabilidade
viab = 50 × prospecting_factor × load_factor × specialist_factor
```

### Thresholds


| Métrica           | Threshold   | Valor        |
| ----------------- | ----------- | ------------ |
| **Urgência**      | CRÍTICO     | ≥200 dias    |
|                   | CONGELADO   | 165-199 dias |
|                   | ATRASADO    | 85-164 dias  |
|                   | LIMITE      | 57-84 dias   |
| **Probabilidade** | Muito Baixa | <30%         |
|                   | Baixa       | 30-50%       |
|                   | Média       | 50-70%       |
|                   | Alta        | ≥70%         |
| **Viabilidade**   | Baixa       | <40          |
|                   | Média       | 40-60        |
|                   | Alta        | ≥60          |


### Ações


| Score | Viabilidade | Ação                     |
| ----- | ----------- | ------------------------ |
| ≥70   | ≥60         | 🔥 PUSH HARD             |
| ≥70   | 40-60       | 🔄 RE-QUALIFY            |
| ≥70   | <40         | 🔀 TRANSFER ou ❌ DISCARD |
| 60-69 | ≥60         | ⚡ ACCELERATE             |
| 60-69 | <40         | 🔀 CONSIDER TRANSFER     |
| <60   | *           | ⏸ MONITOR                |


---

## 9. Lógica de Transferência

### 9.1 Por que Transferir?

O sistema sugere transferência quando um deal tem **potencial real, mas o vendedor atual não tem capacidade de executá-lo adequadamente**. A lógica parte de uma premissa simples: a viabilidade baixa não é culpa do deal — é uma limitação contextual do vendedor. Se existir outro vendedor com capacidade disponível, a oportunidade não deve ser descartada.

**Gatilho:** viabilidade do vendedor atual `< 40`

A viabilidade < 40 significa que o vendedor combina dois ou mais fatores de risco:

- Sem prospecting ativo (fator 0.5): sem pipeline novo, o vendedor está em modo de sobrevivência
- Carga excessiva (fator 0.6–0.8): >100 deals ativos comprometem atenção por deal
- Sem especialização no produto (fator 0.8): menor probabilidade histórica nesse produto

**Diferença entre TRANSFER e CONSIDER_TRANSFER:**

| Situação                         | Ação              | Urgência         |
| -------------------------------- | ----------------- | ---------------- |
| Score ≥ 70 + viab < 40 + prob ≥ 60% | 🔀 TRANSFER       | Imediata         |
| Score 60–69 + viab < 40          | 🔀 CONSIDER_TRANSFER | Avaliação ativa |
| Score ≥ 70 + viab < 40 + prob < 60% | ❌ DISCARD        | Sem retorno      |

O TRANSFER é acionado quando o deal é crítico (score alto) e tem probabilidade suficiente para justificar o esforço de handoff. O CONSIDER_TRANSFER é acionado quando o deal tem potencial médio — ainda há tempo, mas a janela está se fechando.

---

### 9.2 Hierarquia de Busca do Vendedor Alvo

A seleção do vendedor receptor segue uma **hierarquia organizacional** que minimiza o atrito da transferência:

```
1. Mesmo time (mesmo manager)
   → Menor fricção: mesmo processo, mesmo contexto, sem aprovação extra

2. Mesma região, outro time
   → Proximidade geográfica com cliente; manager diferente, mas mesma regional

3. Outra região
   → Último recurso; maior atrito mas mantém a oportunidade viva
```

```python
def find_best_seller_for_transfer(deal, benchmarks):
    """
    Percorre a hierarquia e retorna o melhor candidato disponível.
    Retorna: (nome_com_tag, contexto_de_hierarquia)
    """
    # Filtros eliminatórios (aplicados antes de pontuar)
    # • prospecting == 0  → vendedor não está crescendo pipeline
    # • active_deals > 150 → sobrecarregado demais para receber mais um deal

    for seller in candidatos:
        if prospecting == 0: continue
        if active_deals > 150: continue
        candidate_score = score_candidate(seller, deal['product'])
        classificar_em(priority_1, priority_2, ou_priority_3)

    # Retorna o melhor dentro da prioridade mais alta disponível
    return melhor_de(priority_1 or priority_2 or priority_3)
```

**Por que filtrar `prospecting == 0`?**

Vendedor sem prospecting está em círculo vicioso — cada deal ganho vira carga, sem novos entrando. Transferir para ele apenas replica o problema.

---

### 9.3 Score do Candidato (`score_candidate`)

Dentro de cada nível hierárquico, os candidatos são **rankeados por pontuação**. A função `score_candidate` avalia 4 dimensões:

```python
def score_candidate(seller: str, product: str) -> int:
    score = 0

    # 1. Prospecting (pipeline novo)
    if prospecting > 20:   score += 30
    elif prospecting > 10: score += 20
    else:                  score += 10

    # 2. Carga atual (deals ativos)
    if active_deals < 50:   score += 30
    elif active_deals < 100: score += 20
    else:                    score += 10

    # 3. Especialização no produto (win rate produto > win rate geral + 5pp)
    if combo_wr > seller_wr + 5:
        score += 40

    # 4. Especialização no setor da conta (win rate setor > global + 10pp)
    if sector_wr > global_wr + 10:
        score += 25

    # 5. Win rate geral (proporcional ao global)
    score += (seller_wr / global_wr) * 20

    return score
```

**Tabela de pontos máximos por dimensão:**

| Dimensão                | Pontos máx. | Critério                               |
| ----------------------- | ----------- | -------------------------------------- |
| Prospecting             | 30          | >20 prospects ativos                   |
| Carga leve              | 30          | <50 deals ativos                       |
| Especialização produto  | 40          | WR produto > WR geral do seller +5pp   |
| Especialização setor    | 25          | WR setor > WR global +10pp             |
| Win rate geral          | ~20         | Proporcional ao benchmark global       |
| **Total máx. teórico**  | **~145**    | —                                      |

A especialização no produto recebe maior peso (40 pts) porque é o sinal mais direto de fit: um vendedor com 80% de WR em GTK 500 vs média de 63% tem histórico comprovado naquele produto específico.

---

### 9.4 Métricas Qualitativas de Suporte

Além dos indicadores quantitativos (carga, prospecting, WR geral), o sistema incorpora **três métricas qualitativas** derivadas do histórico de fechamentos:

#### `seller_sector_wr` — Win rate por setor

```python
# Calculado em data_loader.calculate_seller_qualitative_metrics()
# Chave: "{seller}|{sector}"  →  win_rate (%)
# Mínimo: 3 deals no setor para incluir (evita overfitting)

seller_sector_wr = {
    "Wilburn Farren|Technology": 72.5,
    "Hayden Kruise|Healthcare": 68.0,
    ...
}
```

**Uso no scoring:** se o setor da conta do deal tiver WR > global_wr + 10pp para o candidato, ele recebe +25 pts em `score_candidate`.

**Uso em `why_this_helps`:** se WR > global_wr (sem o gap de 10pp), exibe como benefício qualitativo no card de transferência.

---

#### `seller_product_cycle` — Tempo médio de fechamento por produto

```python
# Chave: "{product}|{seller}"  →  avg_days (apenas fechamentos Won)
# Mínimo: 3 deals Won no produto

seller_product_cycle = {
    "GTK 500|Rosalina Dieter": 38.0,
    "GTX Pro|Wilburn Farren": 41.0,
    ...
}
```

**Uso em `why_this_helps`:** se o ciclo do candidato for < 85% da mediana global de Won (57d), exibe como vantagem de velocidade.

```python
# Threshold de exibição
if target_cycle < benchmarks['won_median'] * 0.85:
    transfer_benefits.append(
        f"Ciclo médio de {target_cycle:.0f} dias nesse produto — mais rápido que a média"
    )
```

---

#### `account_sector` — Mapeamento conta → setor

```python
# Derivado do accounts.csv (campo industry/sector)
account_sector = {
    "Hottechi": "Technology",
    "MedVance": "Healthcare",
    ...
}
```

Este mapeamento é o elo entre o deal (que referencia conta) e as métricas de setor (que referenciam setor). Sem ele, não é possível aplicar `seller_sector_wr`.

---

### 9.5 Geração do `why_this_helps`

O campo `why_this_helps` é uma lista dinâmica de justificativas que explica **por que aquele vendedor específico deve receber o deal** — não apenas que ele existe, mas o que o torna a escolha certa.

A lista é construída em ordem de relevância:

```python
transfer_benefits = []

# 1. Carga comparativa (diferença significativa de capacidade)
if target_active < active_deals * 0.6:
    ratio = active_deals / max(target_active, 1)
    transfer_benefits.append(
        f"Carga {ratio:.1f}× menor que a sua ({target_active} vs {active_deals} deals ativos)"
    )
elif target_active < active_deals:
    transfer_benefits.append(f"Carga menor que a sua ({target_active} deals ativos)")

# 2. Pipeline ativo (se vendedor atual está em círculo vicioso)
if prospecting == 0 and target_prospecting > 0:
    transfer_benefits.append(
        f"Pipeline ativo em crescimento ({target_prospecting} prospects)"
    )

# 3. Capacidade geral superior
if target_viability > viability + 20:   # TRANSFER: +20pp
    transfer_benefits.append(
        "O vendedor sugerido pode dedicar atenção focada a esse deal crítico"
    )

# 4. Especialização no produto (WR produto > WR geral +5pp)
if target_product_wr > global_wr + 5:
    transfer_benefits.append(f"{target_product_wr:.0f}% de win rate em {product}")

# 5. Especialização no setor (WR setor > WR global)
if target_sector_wr > global_wr:
    transfer_benefits.append(
        f"Histórico forte no setor {sector} — {target_sector_wr:.0f}% de win rate"
    )

# 6. Ciclo de fechamento mais rápido (< 85% da mediana Won)
if target_cycle < won_median * 0.85:
    transfer_benefits.append(
        f"Ciclo médio de {target_cycle:.0f} dias nesse produto — mais rápido que a média"
    )

# 7. Benefício de liberação (apenas TRANSFER, quando vendedor está sobrecarregado)
if active_deals > 100:
    transfer_benefits.append(
        f"Libera você para focar nos seus outros {active_deals - 1} deals"
    )
```

**Princípio de design:** os benefícios são sempre contextuais e comparativos — não dizem "esse vendedor é bom", dizem "esse vendedor é melhor para *este deal específico*, dado *o seu contexto atual*".

---

### 9.6 Exemplo Completo — TRANSFER

**Cenário:** Deal de $12.000 em GTK 500, conta do setor Technology, vendedor atual com 130 deals ativos e 0 prospects.

```python
# Gatilho
score = 74      → score HIGH (≥70)
viability = 18  → viability BAIXA (<40)
probability = 67% → prob ≥ 60 → TRANSFER (não DISCARD)

# Busca do candidato
# Candidato selecionado: Wilburn Farren (mesmo time)
# Wilburn: 25 prospects, 31 deals, GTK 500 WR = 78%, Technology WR = 72.5%

# score_candidate(Wilburn, "GTK 500") =
#   prospecting 25 > 20  → +30
#   active 31 < 50       → +30
#   GTK 500 WR 78 > 65+5 → +40
#   Technology WR 72.5 > 63+10 → +25
#   WR geral: (65/63) × 20 → +20.6
#   Total: ~145.6

# why_this_helps gerado:
[
    "Carga 4.2× menor que a sua (31 vs 130 deals ativos)",
    "Pipeline ativo em crescimento (25 prospects)",
    "78% de win rate em GTK 500",
    "Histórico forte no setor Technology — 72.5% de win rate",
    "Libera você para focar nos seus outros 129 deals"
]
```

---




