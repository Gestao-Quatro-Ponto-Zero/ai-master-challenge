# Especificacao Tecnica — Modelo de Dados do Lead Scorer

**Documento:** `specs/data_model.md`
**Projeto:** Lead Scorer (Challenge 003)
**Autor:** Victor Almeida
**Ultima atualizacao:** 2026-03-21

---

## 1. Visao Geral

O Lead Scorer opera sobre quatro tabelas CSV originadas do dataset **CRM Sales Predictive Analytics** (Kaggle, licenca CC0). A tabela central e `sales_pipeline`, que referencia as demais por chaves textuais (nao ha IDs numericos).

### Diagrama de Relacoes

```
accounts ←─── sales_pipeline ───→ products
  (account)    (opportunity_id)     (product)
                     │
                     ↓
               sales_teams
               (sales_agent)
```

### Volumetria

| Tabela | Arquivo | Registros | Tamanho aproximado |
|--------|---------|----------:|--------------------|
| accounts | `accounts.csv` | 85 | ~5 KB |
| products | `products.csv` | 7 | <1 KB |
| sales_teams | `sales_teams.csv` | 35 | ~2 KB |
| sales_pipeline | `sales_pipeline.csv` | 8.800 | ~450 KB |

---

## 2. Schema Detalhado das Tabelas

### 2.1 `accounts.csv`

Cadastro de contas (empresas clientes).

| Campo | Tipo Pandas | Tipo Logico | Nullable | Descricao |
|-------|------------|-------------|----------|-----------|
| `account` | `object` (str) | **PK textual** | Nao | Nome da conta. Chave de ligacao com `sales_pipeline.account`. |
| `sector` | `object` (str) | Enum (10 valores) | Nao | Setor da empresa. |
| `year_established` | `int64` | Ano (inteiro) | Nao | Ano de fundacao. Range: 1979-2017. |
| `revenue` | `float64` | Numerico (milhoes USD) | Nao | Receita anual em milhoes de USD. Range: $4.54M a $11.698,03M (~$11.7B). |
| `employees` | `int64` | Inteiro positivo | Nao | Numero de funcionarios. Range: 9 a 34.288. |
| `office_location` | `object` (str) | Pais (15 valores) | Nao | Localizacao do escritorio principal. |
| `subsidiary_of` | `object` (str) | FK para `account` | **Sim** | Empresa-mae, se for subsidiaria. 70 de 85 sao nulos (82%). |

**Valores possiveis de `sector`:**

```
employment, entertainment, finance, marketing, medical,
retail, services, software, technolgy*, telecommunications

(* normalizado para `technology` no data_loader — ver secao 4.3)
```

> **ATENCAO:** O valor `technolgy` e um typo no dataset original (deveria ser `technology`). Sao 12 contas com esse valor. **Corrigir no data_loader** — o JOIN entre pipeline e accounts usa `account` (nome da empresa), NAO `sector`, entao a correcao nao afeta integridade referencial. Corrigir melhora a legibilidade na UI.

**Valores possiveis de `office_location`:**

```
Belgium, Brazil, China, Germany, Italy, Japan, Jordan, Kenya,
Korea, Norway, Panama, Philipines, Poland, Romania, United States
```

> **ATENCAO:** `Philipines` tambem e um typo (deveria ser `Philippines`). Manter como esta.

### 2.2 `products.csv`

Catalogo de produtos.

| Campo | Tipo Pandas | Tipo Logico | Nullable | Descricao |
|-------|------------|-------------|----------|-----------|
| `product` | `object` (str) | **PK textual** | Nao | Nome do produto. Chave de ligacao com `sales_pipeline.product`. |
| `series` | `object` (str) | Enum (3 valores) | Nao | Linha do produto: `GTX`, `GTK` ou `MG`. |
| `sales_price` | `int64` | Inteiro positivo (USD) | Nao | Preco de lista em dolares. |

**Catalogo completo (7 produtos):**

| Produto | Serie | Preco (USD) |
|---------|-------|------------:|
| GTK 500 | GTK | 26.768 |
| GTX Plus Pro | GTX | 5.482 |
| GTX Pro | GTX | 4.821 |
| MG Advanced | MG | 3.393 |
| GTX Plus Basic | GTX | 1.096 |
| GTX Basic | GTX | 550 |
| MG Special | MG | 55 |

> **INCONSISTENCIA CRITICA:** Na tabela `products.csv` o nome e `"GTX Pro"` (com espaco), mas em `sales_pipeline.csv` o valor e `"GTXPro"` (sem espaco). O `data_loader` **deve normalizar** esse valor durante o carregamento para permitir o JOIN. Detalhes na secao 4.

### 2.3 `sales_teams.csv`

Cadastro de vendedores e sua hierarquia.

| Campo | Tipo Pandas | Tipo Logico | Nullable | Descricao |
|-------|------------|-------------|----------|-----------|
| `sales_agent` | `object` (str) | **PK textual** | Nao | Nome completo do vendedor. Chave de ligacao com `sales_pipeline.sales_agent`. |
| `manager` | `object` (str) | Enum (6 valores) | Nao | Nome do manager direto. |
| `regional_office` | `object` (str) | Enum (3 valores) | Nao | Escritorio regional: `Central`, `East` ou `West`. |

**Managers (6):** Cara Losch, Celia Rouche, Dustin Brinkmann, Melvin Marxen, Rocco Neubert, Summer Sewald.

**Escritorios regionais (3):** Central, East, West.

### 2.4 `sales_pipeline.csv`

Pipeline de oportunidades. **Tabela central da aplicacao.**

| Campo | Tipo Pandas | Tipo Logico | Nullable | Descricao |
|-------|------------|-------------|----------|-----------|
| `opportunity_id` | `object` (str) | **PK textual** | Nao | Identificador unico da oportunidade. 8 caracteres alfanumericos. Todos unicos (8.800 valores distintos). |
| `sales_agent` | `object` (str) | **FK → sales_teams** | Nao | Vendedor responsavel. Todos existem em `sales_teams.csv`. |
| `product` | `object` (str) | **FK → products** | Nao | Produto da oportunidade. Ver nota sobre `GTXPro` vs `GTX Pro`. |
| `account` | `object` (str) | **FK → accounts** | **Sim** | Conta associada. **1.425 nulos** (16,2% do total). Todas as contas nao-nulas existem em `accounts.csv`. |
| `deal_stage` | `object` (str) | Enum (4 valores) | Nao | Estagio do deal: `Prospecting`, `Engaging`, `Won`, `Lost`. |
| `engage_date` | `object` (str) | Data ISO (YYYY-MM-DD) | **Sim** | Data em que o deal entrou em Engaging. Nulo para Prospecting (500). |
| `close_date` | `object` (str) | Data ISO (YYYY-MM-DD) | **Sim** | Data de fechamento. Nulo para Prospecting (500) e Engaging (1.589). |
| `close_value` | `float64` | Numerico (USD) | **Sim** | Valor de fechamento. Nulo para Prospecting e Engaging. Para Won: valor real. Para Lost: 0. |

---

## 3. Matriz de Nulidade por `deal_stage`

Esta e a regra mais importante do modelo de dados. O padrao de nulidade e **deterministico** baseado no `deal_stage`.

| Campo | Prospecting (500) | Engaging (1.589) | Won (4.238) | Lost (2.473) |
|-------|:-----------------:|:----------------:|:-----------:|:------------:|
| `opportunity_id` | Preenchido | Preenchido | Preenchido | Preenchido |
| `sales_agent` | Preenchido | Preenchido | Preenchido | Preenchido |
| `product` | Preenchido | Preenchido | Preenchido | Preenchido |
| `account` | **67,4% nulo** | **68,5% nulo** | Preenchido | Preenchido |
| `deal_stage` | Preenchido | Preenchido | Preenchido | Preenchido |
| `engage_date` | **100% nulo** | Preenchido | Preenchido | Preenchido |
| `close_date` | **100% nulo** | **100% nulo** | Preenchido | Preenchido |
| `close_value` | **100% nulo** | **100% nulo** | Preenchido (>0) | Preenchido (=0) |

### Regras derivadas

1. **`engage_date` nulo** ↔ `deal_stage == "Prospecting"` (relacao bicondicional)
2. **`close_date` nulo** ↔ `deal_stage in ("Prospecting", "Engaging")` (deals ativos)
3. **`close_value` nulo** ↔ `deal_stage in ("Prospecting", "Engaging")` (deals ativos)
4. **`close_value == 0`** ↔ `deal_stage == "Lost"`
5. **`close_value > 0`** ↔ `deal_stage == "Won"`
6. **`account` nulo** pode ocorrer em qualquer deal ativo (Prospecting/Engaging), **nunca** em deals fechados (Won/Lost)

### Implicacao para o scoring

Deals **ativos** (que recebem score) sao apenas `Prospecting` e `Engaging`. Nesses deals:
- **`close_value` e SEMPRE null** (100% dos 2.089 deals ativos) → usar `sales_price` do produto como proxy para o componente de valor
- **`close_date` e SEMPRE null** → calcular tempo no stage a partir da data de referencia
- **`engage_date` e null para Prospecting** (500 deals) → componente de velocidade fica neutro (50); impossivel classificar como Deal Zumbi
- **`account` e null em ~68% dos deals ativos** (1.425 de 2.089) → impacto direto:
  - Seller-Deal Fit: sem setor → `fit_multiplier = 1.0` (neutro) para ~68% dos deals
  - Account Health: sem historico → `health_score = 0.5` (neutro) para ~68% dos deals
  - Apenas **31.8% dos deals ativos** (664) conseguem join com setor da conta

---

## 4. Integridade Referencial e Normalizacao

### 4.1 Chaves de ligacao

| FK em `sales_pipeline` | Tabela referenciada | Campo PK | Integridade | Observacao |
|------------------------|--------------------|---------:|:-----------:|-----------|
| `sales_agent` | `sales_teams` | `sales_agent` | 100% | Todos os 35 agentes existem. |
| `product` | `products` | `product` | **99,9%** | `"GTXPro"` no pipeline nao bate com `"GTX Pro"` em products. |
| `account` | `accounts` | `account` | 100% (dos nao-nulos) | 1.425 registros sem account (nulo), mas todos os nao-nulos existem em accounts. |

### 4.2 Normalizacao obrigatoria: `GTXPro` → `GTX Pro`

O pipeline usa `"GTXPro"` (sem espaco) enquanto `products.csv` registra `"GTX Pro"` (com espaco).

**Regra de carregamento:** Ao carregar `sales_pipeline.csv`, normalizar o campo `product`:

```python
pipeline_df['product'] = pipeline_df['product'].replace('GTXPro', 'GTX Pro')
```

Esta normalizacao **deve ocorrer antes de qualquer JOIN** com a tabela de produtos.

### 4.3 Normalizacao de setor: `technolgy` → `technology`

**Regra de carregamento:** Ao carregar `accounts.csv`, normalizar o campo `sector`:

```python
accounts_df['sector'] = accounts_df['sector'].replace('technolgy', 'technology')
```

Justificativa: o JOIN entre pipeline e accounts usa `account` (nome da empresa), NAO `sector`. Corrigir o typo nao afeta nenhum JOIN, e melhora a legibilidade nos filtros e explicacoes da UI.

### 4.4 Typos mantidos (NAO normalizar)

| Tabela | Campo | Valor no CSV | Valor correto | Acao |
|--------|-------|-------------|---------------|------|
| accounts | `office_location` | `Philipines` | `Philippines` | **Manter** — nao aparece de forma prominente na UI. |

---

## 5. Data de Referencia e Calculos Temporais

### 5.1 Data de referencia

```python
REFERENCE_DATE = pd.Timestamp('2017-12-31')
```

A data de referencia e **fixa** em `2017-12-31`, que corresponde a data maxima de `close_date` no dataset. Para todos os calculos de "dias no stage" e "dias desde", usar esta data como "hoje".

**Ranges de datas no dataset:**
- `engage_date`: 2016-10-20 a 2017-12-27
- `close_date`: 2017-03-01 a 2017-12-31

### 5.2 Calculo de dias no stage

Para deals **ativos** (Prospecting e Engaging):

```python
# Prospecting: nao tem engage_date, usar a data mais antiga do dataset como proxy
# ou calcular com base em padroes observados.
# Na pratica, Prospecting nao tem data de entrada registrada.
# Usar REFERENCE_DATE - max(engage_date do dataset) como estimativa conservadora,
# ou tratar como "tempo desconhecido" e aplicar score neutro para o componente de velocidade.

# Engaging: tem engage_date
dias_no_stage = (REFERENCE_DATE - pd.to_datetime(row['engage_date'])).days
```

**Problema dos deals em Prospecting:** Nao ha registro de quando o deal entrou em Prospecting. Opcoes de tratamento:

| Estrategia | Descricao | Recomendacao |
|-----------|-----------|:------------:|
| Score neutro (0.5) | Nao penalizar nem bonificar velocidade | **Recomendada** |
| Usar data media | Assumir que entraram na data media do dataset | Nao recomendada (impreciso) |
| Ignorar componente | Redistribuir peso para outros componentes | Aceitavel |

### 5.3 Benchmarks de velocidade (calibrados com dados reais)

Estes valores sao derivados dos deals `Won` e usados como referencia para o decay de velocidade:

| Metrica | Valor | Descricao |
|---------|------:|-----------|
| Mediana Won (Engaging → Close) | **57 dias** | Tempo tipico de fechamento |
| P75 Won | **88 dias** | Limite saudavel — inicio do decay |
| P90 Won | **106 dias** | Alerta |
| Mediana deals Engaging ativos | **165 dias** | Situacao atual do pipeline (inflado) |
| % Engaging ativos > mediana Won | **96,7%** | Quase todos os deals ativos estao acima do tempo tipico |

---

## 6. Constantes Derivadas dos Dados

### 6.1 Precos dos produtos (para proxy de valor em deals ativos)

```python
PRODUCT_PRICES = {
    'GTK 500': 26768,
    'GTX Plus Pro': 5482,
    'GTX Pro': 4821,      # Nome normalizado (no pipeline aparece como "GTXPro")
    'MG Advanced': 3393,
    'GTX Plus Basic': 1096,
    'GTX Basic': 550,
    'MG Special': 55,
}

MAX_PRODUCT_PRICE = 26768   # GTK 500
MIN_PRODUCT_PRICE = 55      # MG Special
PRICE_RATIO = 486.7         # Razao max/min
```

### 6.2 Win rates por produto (para referencia)

```python
PRODUCT_WIN_RATES = {
    'MG Special': 0.648,
    'GTX Plus Pro': 0.643,
    'GTX Basic': 0.637,
    'GTX Pro': 0.636,
    'GTX Plus Basic': 0.621,
    'MG Advanced': 0.603,
    'GTK 500': 0.600,
}

OVERALL_WIN_RATE = 0.632    # Win rate geral (Won / (Won + Lost))
```

### 6.3 Limites para o scoring

```python
# Velocity decay — referencia por stage
VELOCITY_REFERENCE_ENGAGING = 88    # P75 dos Won (dias)
VELOCITY_REFERENCE_PROSPECTING = None  # Dataset NAO tem datas para Prospecting — usar score neutro (50)

# Deal Zumbi
ZOMBIE_THRESHOLD_MULTIPLIER = 2.0   # tempo > 2x referencia
ZOMBIE_CRITICAL_PERCENTILE = 75     # valor acima do P75 do pipeline

# Seller-Deal Fit
SELLER_FIT_MIN_DEALS = 5            # Minimo de deals para calcular fit

# Account Health
ACCOUNT_HEALTH_MIN_DEALS = 3        # Minimo de deals fechados para calcular saude
ACCOUNT_HEALTH_NEUTRAL = 0.5        # Score padrao quando dados insuficientes

# Conta com losses recorrentes
RECURRENT_LOSS_THRESHOLD = 2        # 2+ losses para flag "Conta Recorrente Lost"
```

### 6.4 Valor de referencia para normalizacao

```python
# close_value dos deals Won
CLOSE_VALUE_MAX = 30288.0           # Maximo observado
CLOSE_VALUE_MEDIAN = 1117.0         # Mediana dos Won
CLOSE_VALUE_P75 = 4430.0            # Percentil 75 dos Won
CLOSE_VALUE_P25 = 518.0             # Percentil 25 dos Won
CLOSE_VALUE_MEAN = 2360.9           # Media dos Won

# Para deals ativos: usar sales_price do produto como proxy
# NOTA: close_value e NULL para TODOS os deals ativos (Prospecting e Engaging)
```

---

## 7. Interface do `data_loader.py`

### 7.1 Localizacao

```
submissions/victor-almeida/solution/utils/data_loader.py
```

### 7.2 Funcoes esperadas

#### `load_data() → dict[str, pd.DataFrame]`

Funcao principal. Carrega os 4 CSVs, aplica validacoes e normalizacoes, retorna um dicionario com os DataFrames prontos para uso.

```python
def load_data(data_dir: str = "data") -> dict[str, pd.DataFrame]:
    """
    Carrega e prepara todos os DataFrames do Lead Scorer.

    Etapas:
    1. Carrega os 4 CSVs de `data_dir/`
    2. Normaliza 'GTXPro' → 'GTX Pro' no pipeline
    3. Converte colunas de data para datetime
    4. Calcula colunas derivadas (dias_no_stage, is_active, etc.)
    5. Faz merge enriquecendo pipeline com dados de accounts, products e sales_teams
    6. Valida integridade referencial

    Args:
        data_dir: Caminho relativo ou absoluto para o diretorio com os CSVs.

    Returns:
        Dicionario com chaves:
        - 'pipeline': DataFrame enriquecido (tabela central com JOINs)
        - 'accounts': DataFrame de contas
        - 'products': DataFrame de produtos
        - 'sales_teams': DataFrame de vendedores
    """
```

**Retorno esperado — `pipeline` (DataFrame enriquecido):**

Alem das colunas originais do `sales_pipeline.csv`, o DataFrame `pipeline` deve conter:

| Coluna derivada | Tipo | Descricao |
|----------------|------|-----------|
| `engage_date` | `datetime64` | Convertida de string para datetime |
| `close_date` | `datetime64` | Convertida de string para datetime |
| `is_active` | `bool` | `True` se `deal_stage in ('Prospecting', 'Engaging')` |
| `days_in_stage` | `float64` ou `Int64` | Dias desde `engage_date` ate `REFERENCE_DATE`. `NaN` para Prospecting. |
| `sales_price` | `int64` | Preco do produto (via JOIN com products) |
| `series` | `object` (str) | Serie do produto (via JOIN com products) |
| `sector` | `object` (str) | Setor da conta (via JOIN com accounts). `NaN` se account nulo. |
| `revenue` | `float64` | Receita da conta (via JOIN com accounts). `NaN` se account nulo. |
| `employees` | `float64` | Funcionarios da conta (via JOIN com accounts). `NaN` se account nulo. |
| `office_location` | `object` (str) | Localizacao da conta (via JOIN). `NaN` se account nulo. |
| `manager` | `object` (str) | Manager do vendedor (via JOIN com sales_teams) |
| `regional_office` | `object` (str) | Escritorio regional (via JOIN com sales_teams) |

#### `load_accounts(data_dir: str) → pd.DataFrame`

```python
def load_accounts(data_dir: str = "data") -> pd.DataFrame:
    """Carrega accounts.csv sem transformacoes."""
```

#### `load_products(data_dir: str) → pd.DataFrame`

```python
def load_products(data_dir: str = "data") -> pd.DataFrame:
    """Carrega products.csv sem transformacoes."""
```

#### `load_sales_teams(data_dir: str) → pd.DataFrame`

```python
def load_sales_teams(data_dir: str = "data") -> pd.DataFrame:
    """Carrega sales_teams.csv sem transformacoes."""
```

#### `load_pipeline(data_dir: str) → pd.DataFrame`

```python
def load_pipeline(data_dir: str = "data") -> pd.DataFrame:
    """
    Carrega sales_pipeline.csv com normalizacoes:
    - Normaliza 'GTXPro' → 'GTX Pro'
    - Converte engage_date e close_date para datetime
    - Adiciona coluna is_active
    - Adiciona coluna days_in_stage
    """
```

#### `get_active_deals(pipeline: pd.DataFrame) → pd.DataFrame`

```python
def get_active_deals(pipeline: pd.DataFrame) -> pd.DataFrame:
    """Retorna apenas deals ativos (Prospecting + Engaging)."""
    return pipeline[pipeline['is_active']].copy()
```

#### `get_reference_date() → pd.Timestamp`

```python
def get_reference_date() -> pd.Timestamp:
    """Retorna a data de referencia fixa: 2017-12-31."""
    return pd.Timestamp('2017-12-31')
```

### 7.3 Pipeline de carregamento (ordem de execucao)

```
1. Ler CSVs brutos (pd.read_csv)
       │
2. Normalizar produto: 'GTXPro' → 'GTX Pro' no pipeline
       │
3. Converter datas: engage_date, close_date → datetime64
       │
4. Calcular colunas derivadas:
   ├── is_active = deal_stage in ('Prospecting', 'Engaging')
   └── days_in_stage = (REFERENCE_DATE - engage_date).days  [NaN p/ Prospecting]
       │
5. LEFT JOIN pipeline ← products ON product
       │
6. LEFT JOIN pipeline ← accounts ON account (preserva NaN p/ account nulo)
       │
7. LEFT JOIN pipeline ← sales_teams ON sales_agent
       │
8. Validar integridade (asserts opcionais em modo debug)
       │
9. Retornar dict de DataFrames
```

### 7.4 Exemplo de uso

```python
from utils.data_loader import load_data, get_active_deals

# Carregamento completo
data = load_data(data_dir="data")
pipeline = data['pipeline']
accounts = data['accounts']
products = data['products']
sales_teams = data['sales_teams']

# Filtrar deals ativos para scoring
active_deals = get_active_deals(pipeline)
# active_deals tem 2.089 registros (500 Prospecting + 1.589 Engaging)

# Acessar informacoes enriquecidas
deal = active_deals.iloc[0]
print(deal['product'])         # 'MG Advanced'
print(deal['sales_price'])     # 3393
print(deal['manager'])         # 'Melvin Marxen'
print(deal['sector'])          # NaN (se account for nulo)
print(deal['days_in_stage'])   # 423 (dias desde engage_date)
```

---

## 8. Regras de Validacao

### 8.1 Validacoes no carregamento

```python
# 1. Volumetria minima
assert len(accounts) >= 80, "Accounts com menos registros que o esperado"
assert len(products) == 7, "Products deve ter exatamente 7 registros"
assert len(sales_teams) >= 30, "Sales teams com menos registros que o esperado"
assert len(pipeline) >= 8000, "Pipeline com menos registros que o esperado"

# 2. Chave primaria unica
assert pipeline['opportunity_id'].is_unique, "opportunity_id nao e unico"
assert accounts['account'].is_unique, "account nao e unico"
assert products['product'].is_unique, "product nao e unico"
assert sales_teams['sales_agent'].is_unique, "sales_agent nao e unico"

# 3. Deal stages validos
valid_stages = {'Prospecting', 'Engaging', 'Won', 'Lost'}
assert set(pipeline['deal_stage'].unique()) == valid_stages, "Stages inesperados"

# 4. Integridade referencial (apos normalizacao do produto)
pipeline_products = set(pipeline['product'].unique())
csv_products = set(products['product'].unique())
assert pipeline_products.issubset(csv_products), f"Produtos orfaos: {pipeline_products - csv_products}"

pipeline_agents = set(pipeline['sales_agent'].unique())
csv_agents = set(sales_teams['sales_agent'].unique())
assert pipeline_agents.issubset(csv_agents), f"Agentes orfaos: {pipeline_agents - csv_agents}"

pipeline_accounts = set(pipeline['account'].dropna().unique())
csv_accounts = set(accounts['account'].unique())
assert pipeline_accounts.issubset(csv_accounts), f"Contas orfas: {pipeline_accounts - csv_accounts}"

# 5. Regras de nulidade por stage
prosp = pipeline[pipeline['deal_stage'] == 'Prospecting']
assert prosp['engage_date'].isna().all(), "Prospecting nao deve ter engage_date"
assert prosp['close_date'].isna().all(), "Prospecting nao deve ter close_date"
assert prosp['close_value'].isna().all(), "Prospecting nao deve ter close_value"

engaging = pipeline[pipeline['deal_stage'] == 'Engaging']
assert engaging['engage_date'].notna().all(), "Engaging deve ter engage_date"
assert engaging['close_date'].isna().all(), "Engaging nao deve ter close_date"
assert engaging['close_value'].isna().all(), "Engaging nao deve ter close_value"

won = pipeline[pipeline['deal_stage'] == 'Won']
assert (won['close_value'] > 0).all(), "Won deve ter close_value > 0"
assert won['account'].notna().all(), "Won deve ter account"

lost = pipeline[pipeline['deal_stage'] == 'Lost']
assert (lost['close_value'] == 0).all(), "Lost deve ter close_value == 0"
assert lost['account'].notna().all(), "Lost deve ter account"
```

### 8.2 Validacoes de tipo apos conversao

```python
# Datas devem ser datetime64 (nao string)
assert pd.api.types.is_datetime64_any_dtype(pipeline['engage_date'])
assert pd.api.types.is_datetime64_any_dtype(pipeline['close_date'])

# Numericos
assert pd.api.types.is_numeric_dtype(pipeline['close_value'])
assert pd.api.types.is_numeric_dtype(pipeline['sales_price'])
```

---

## 9. Tratamento de Casos Especiais

### 9.1 Deals ativos sem `account` (1.425 registros)

| Situacao | Impacto no scoring | Tratamento |
|----------|-------------------|------------|
| `account` nulo | Sem dados de setor para Seller-Fit | Usar `fit_multiplier = 1.0` (neutro) |
| `account` nulo | Sem historico para Account Health | Usar `health_score = 0.5` (neutro) |
| `account` nulo | Sem `revenue`/`employees` | Campos ficam `NaN` apos JOIN — nao usar para scoring |

### 9.2 Deals em Prospecting (500 registros)

| Situacao | Impacto | Tratamento |
|----------|---------|------------|
| Sem `engage_date` | Impossivel calcular `days_in_stage` | `days_in_stage = NaN` |
| Sem `close_value` | Sem valor para componente de valor | Usar `sales_price` do produto como proxy |
| Sem velocidade | Componente de velocidade nao calculavel | Aplicar score neutro (0.5) para velocidade |

### 9.3 Proxy de valor para deals ativos

Como deals em Prospecting e Engaging nao tem `close_value`, o valor estimado vem do preco do produto:

```python
def get_expected_value(row: pd.Series) -> float:
    """Retorna o valor estimado do deal para calculo do score."""
    if pd.notna(row['close_value']) and row['close_value'] > 0:
        return row['close_value']       # Won: valor real
    return row['sales_price']           # Ativo: preco de lista
```

### 9.4 Normalizacao logaritmica do valor

A diferenca de 486x entre o produto mais caro e o mais barato exige normalizacao logaritmica para evitar que GTK 500 domine completamente o componente de valor:

```python
import numpy as np

def normalize_value(value: float, max_value: float = 30288.0) -> float:
    """Normaliza valor para 0-1 usando escala logaritmica."""
    return np.log1p(value) / np.log1p(max_value)

# Exemplos:
# GTK 500 ($26.768) → 0.99
# GTX Plus Pro ($5.482) → 0.81
# MG Special ($55) → 0.39
```

---

## 10. Glossario

| Termo | Definicao |
|-------|-----------|
| **Deal ativo** | Oportunidade com `deal_stage` em `Prospecting` ou `Engaging`. Sao os deals que recebem score. |
| **Deal fechado** | Oportunidade com `deal_stage` em `Won` ou `Lost`. Usados apenas para calculos historicos (win rates, benchmarks). |
| **Deal zumbi** | Deal ativo cujo `days_in_stage > 2 * VELOCITY_REFERENCE` do stage. Indica oportunidade provavelmente morta que infla o pipeline. |
| **Data de referencia** | `2017-12-31`. Usada como "hoje" para todos os calculos temporais. Corresponde a data maxima do dataset. |
| **Proxy de valor** | `sales_price` do produto, usado como estimativa de `close_value` para deals ativos (que nao tem valor de fechamento). |
| **Fit** | Compatibilidade vendedor-setor, medida pelo win rate do vendedor no setor vs media do time. |
| **Saude da conta** | Win rate historico da conta em deals fechados. Indica se a conta tende a converter ou nao. |

---

## 11. Testes TDD (test_data_loader.py)

Antes de implementar `data_loader.py`, escrever os seguintes testes em `tests/test_data_loader.py`. Todos devem falhar inicialmente (Red) e passar apos a implementacao (Green).

### 11.1 Testes de carregamento basico

```python
def test_load_data_returns_dict_with_expected_keys():
    """load_data() retorna dict com chaves 'pipeline', 'accounts', 'products', 'sales_teams'."""

def test_load_accounts_returns_dataframe_with_expected_columns():
    """accounts tem colunas: account, sector, year_established, revenue, employees, office_location, subsidiary_of."""

def test_load_products_returns_exactly_7_products():
    """products tem exatamente 7 registros."""

def test_load_sales_teams_returns_at_least_30_agents():
    """sales_teams tem pelo menos 30 registros."""

def test_load_pipeline_returns_at_least_8000_records():
    """pipeline tem pelo menos 8.000 registros."""
```

### 11.2 Testes de normalizacao

```python
def test_product_gtxpro_normalized_to_gtx_pro():
    """No pipeline, 'GTXPro' deve ser normalizado para 'GTX Pro'."""

def test_sector_technolgy_normalized_to_technology():
    """Em accounts, 'technolgy' deve ser normalizado para 'technology'."""

def test_all_pipeline_products_exist_in_products_table():
    """Apos normalizacao, todos os produtos do pipeline existem na tabela products."""
```

### 11.3 Testes de tipos e conversoes

```python
def test_engage_date_is_datetime_type():
    """Coluna engage_date no pipeline deve ser datetime64."""

def test_close_date_is_datetime_type():
    """Coluna close_date no pipeline deve ser datetime64."""

def test_close_value_is_numeric_type():
    """Coluna close_value no pipeline deve ser numerica."""
```

### 11.4 Testes de colunas derivadas

```python
def test_is_active_true_for_prospecting_and_engaging():
    """is_active == True para deals Prospecting e Engaging, False para Won e Lost."""

def test_days_in_stage_nan_for_prospecting():
    """days_in_stage deve ser NaN para todos os deals Prospecting."""

def test_days_in_stage_positive_for_engaging():
    """days_in_stage deve ser positivo para deals Engaging."""

def test_reference_date_is_2017_12_31():
    """get_reference_date() retorna pd.Timestamp('2017-12-31')."""
```

### 11.5 Testes de integridade referencial

```python
def test_all_pipeline_agents_exist_in_sales_teams():
    """Todos os sales_agent do pipeline existem em sales_teams."""

def test_all_non_null_accounts_exist_in_accounts_table():
    """Todos os account nao-nulos do pipeline existem em accounts."""

def test_opportunity_id_is_unique():
    """opportunity_id no pipeline e unico."""
```

### 11.6 Testes de nulidade por stage

```python
def test_prospecting_has_no_engage_date():
    """Deals Prospecting tem engage_date 100% nulo."""

def test_prospecting_has_no_close_date():
    """Deals Prospecting tem close_date 100% nulo."""

def test_engaging_has_engage_date():
    """Deals Engaging tem engage_date 100% preenchido."""

def test_won_has_positive_close_value():
    """Deals Won tem close_value > 0."""

def test_lost_has_zero_close_value():
    """Deals Lost tem close_value == 0."""
```

### 11.7 Testes de enriquecimento (JOINs)

```python
def test_pipeline_has_sales_price_after_merge():
    """Pipeline enriquecido tem coluna sales_price (do JOIN com products)."""

def test_pipeline_has_manager_after_merge():
    """Pipeline enriquecido tem coluna manager (do JOIN com sales_teams)."""

def test_pipeline_has_sector_after_merge():
    """Pipeline enriquecido tem coluna sector (do JOIN com accounts). NaN quando account e nulo."""

def test_get_active_deals_returns_only_active():
    """get_active_deals() retorna apenas Prospecting e Engaging."""
```
