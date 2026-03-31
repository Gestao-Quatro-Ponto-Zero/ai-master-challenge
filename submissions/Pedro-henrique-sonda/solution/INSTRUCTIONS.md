# INSTRUCTIONS.md — Especificação Técnica do Lead Scorer

## Visão Geral

Aplicação Streamlit que calcula e exibe um score de priorização (0-100) para cada deal aberto no pipeline de vendas. O score ajuda o vendedor a decidir onde focar seu tempo.

---

## 1. Dados

### Tabelas e relacionamentos

```
accounts ←── sales_pipeline ──→ products
                   ↓
              sales_teams
```

### sales_pipeline.csv (~8800 registros) — TABELA CENTRAL
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| opportunity_id | string | ID único do deal |
| sales_agent | string | Nome do vendedor (FK → sales_teams) |
| product | string | Nome do produto (FK → products) |
| account | string | Nome da conta (FK → accounts) |
| deal_stage | string | Prospecting, Engaging, Won, Lost |
| engage_date | date | Data de início do Engaging (vazio em Prospecting) |
| close_date | date | Data de fechamento (vazio em abertos) |
| close_value | float | Valor real de fechamento (0 se Lost, vazio se aberto) |

### accounts.csv (~85 registros)
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| account | string | Nome da conta (PK) |
| sector | string | Setor (10 setores: technology, medical, retail, etc.) |
| revenue | float | Receita da empresa |
| employees | int | Número de funcionários |
| subsidiary_of | string | Empresa-mãe (vazio se independente) |

### products.csv (7 registros)
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| product | string | Nome do produto (PK) |
| series | string | Série (GTX, MG, GTK) |
| sales_price | int | Preço de tabela |

### sales_teams.csv (35 registros)
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| sales_agent | string | Nome do vendedor (PK) |
| manager | string | Nome do manager |
| regional_office | string | Escritório (Central, East, West) |

---

## 2. Lógica de Scoring

### Escopo
- Score é calculado APENAS para deals abertos (deal_stage = "Prospecting" ou "Engaging")
- Deals Won e Lost são usados como dados HISTÓRICOS para calcular taxas de conversão
- O vendedor NÃO é fator no scoring

### Fórmula principal

```python
score_final = (score_probabilidade * 0.70) + (score_valor * 0.30)
```

### Score de Probabilidade (0-100)

```python
score_probabilidade = (sazonalidade * 0.35) + (setor_produto * 0.30) + (stage * 0.20) + (tempo * 0.15)
```

#### Fator 1 — Sazonalidade (peso 0.35)
Baseado no mês ATUAL (datetime.now().month):

```python
mes = datetime.now().month
if mes in [3, 6, 9, 12]:    # Último mês do trimestre
    sazonalidade = 95
elif mes in [2, 5, 8, 11]:  # Segundo mês
    sazonalidade = 55
else:                         # Primeiro mês (1, 4, 7, 10)
    sazonalidade = 35
```

#### Fator 2 — Combinação Setor + Produto (peso 0.30)
Calcula taxa de conversão histórica para cada combinação:

```python
# Para cada combinação sector+product nos deals Won e Lost:
taxa_combo = won / (won + lost)

# Normalização:
setor_produto = ((taxa_combo - 0.52) / (0.73 - 0.52)) * 100
setor_produto = max(0, min(100, setor_produto))  # Clamp 0-100

# Se combo tem menos de 30 deals fechados (Won+Lost):
# Usa taxa média geral (0.632) como fallback
```

#### Fator 3 — Stage (peso 0.20)

```python
if deal_stage == "Engaging":
    stage = 75
elif deal_stage == "Prospecting":
    stage = 40
```

#### Fator 4 — Tempo no pipeline (peso 0.15)
Calcula dias desde engage_date até hoje:

```python
if deal_stage == "Prospecting":  # Sem engage_date
    tempo = 50
else:
    dias = (hoje - engage_date).days
    if dias <= 30:
        tempo = 45
    elif dias <= 60:
        tempo = 55
    elif dias <= 90:
        tempo = 55
    else:  # 90+
        tempo = 50
```

### Score de Valor (0-100)
Escala logarítmica baseada no sales_price do produto:

```python
import math
score_valor = (math.log(sales_price) / math.log(26768)) * 100
```

---

## 3. Explicação do Score

Para cada deal, gerar um texto curto em português explicando os fatores principais. Modelo:

```
"Probabilidade [alta/média/baixa]: combinação [setor] + [produto] converte [X%] historicamente.
[Mês de fechamento trimestral / Mês intermediário / Início de trimestre].
Deal em [stage] há [N] dias. Valor potencial: $[valor]."
```

Classificação:
- score_probabilidade > 70: "alta"
- score_probabilidade 40-70: "média"
- score_probabilidade < 40: "baixa"

---

## 4. Interface Streamlit

### Layout geral

```
┌─────────────────────────────────────────────────┐
│  🎯 Lead Scorer — Pipeline Intelligence         │
│  Subtítulo: Priorize seus deals com dados        │
├──────────┬──────────────────────────────────────┤
│ SIDEBAR  │  KPIs (4 colunas)                     │
│          │  [Deals] [Score Médio] [Alta] [Valor] │
│ Filtros: │──────────────────────────────────────│
│ Vendedor │  Tabela principal                     │
│ Manager  │  (ordenada por Score Final desc)      │
│ Office   │                                       │
│ Stage    │  Colunas:                             │
│ Score    │  Score | Conta | Produto | Valor |    │
│          │  Stage | Vendedor | Dias | Explicação │
│          │──────────────────────────────────────│
│          │  Gráfico: distribuição dos scores     │
└──────────┴──────────────────────────────────────┘
```

### Sidebar — Filtros
- Vendedor: selectbox com "Todos" + lista de vendedores
- Manager: selectbox com "Todos" + lista de managers
- Escritório: selectbox com "Todos" + Central/East/West
- Stage: selectbox com "Todos" / "Prospecting" / "Engaging"
- Faixa de Score: slider de 0 a 100 (range)

Os filtros devem ser encadeados: ao selecionar um manager, a lista de vendedores mostra só os vendedores daquele manager.

### KPIs (métricas no topo)
4 colunas usando st.metric():
1. Total de deals (filtrados)
2. Score médio (filtrado)
3. Deals prioridade alta (score > 70)
4. Valor potencial total ($)

### Tabela principal
- Ordenada por Score Final decrescente
- Score com cor visual:
  - 🟢 Verde: score > 70
  - 🟡 Amarelo: score 40-70
  - 🔴 Vermelho: score < 40
- Usar st.dataframe() com formatação de cores via pandas Styler

### Gráfico
- Histograma de distribuição dos scores usando st.bar_chart() ou altair
- Mostrar abaixo da tabela

---

## 5. Construção em etapas

O código será construído em 4 etapas incrementais:

### Etapa 1 — Estrutura + dados
- Carregar CSVs, fazer merges, filtrar deals abertos
- Mostrar tabela básica

### Etapa 2 — Scoring
- Implementar os 4 fatores + score de valor + score final
- Adicionar colunas de score na tabela

### Etapa 3 — Interface
- Sidebar com filtros encadeados
- KPIs no topo
- Tabela com cores
- Explicação do score por deal

### Etapa 4 — Polimento
- Gráfico de distribuição
- Ajustes visuais
- Testes com dados reais
