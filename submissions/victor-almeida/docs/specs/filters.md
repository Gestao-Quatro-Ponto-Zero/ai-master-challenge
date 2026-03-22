# Spec Tecnica — Sistema de Filtros (`components/filters.py`)

**Modulo:** `components/filters.py`
**Autor:** Victor Almeida
**Status:** Draft
**Referencia PRD:** Secao 6.5 (Filtros)

---

## 1. Objetivo

O modulo de filtros e o ponto de entrada da experiencia do usuario. Quando o vendedor abre a ferramenta na segunda-feira de manha, os filtros determinam **o que ele ve**. O sistema precisa:

1. Permitir que cada persona (vendedor, manager, head RevOps) chegue a sua visao em no maximo 2 cliques.
2. Aplicar logica AND entre todos os filtros — cada filtro adicional restringe o resultado.
3. Retornar um DataFrame filtrado que alimenta todos os outros componentes (pipeline_view, deal_detail, metrics).

---

## 2. Lista Completa de Filtros

| # | Filtro | Componente Streamlit | Tipo | Coluna(s) de referencia | Obrigatorio PRD |
|---|--------|---------------------|------|------------------------|----------------|
| 1 | Escritorio/Regiao | `st.selectbox` | single-select | `sales_teams.regional_office` | Sim |
| 2 | Manager | `st.selectbox` | single-select | `sales_teams.manager` | Sim |
| 3 | Vendedor | `st.selectbox` | single-select | `sales_teams.sales_agent` | Sim |
| 4 | Produto | `st.multiselect` | multi-select | `products.product` | Sim |
| 5 | Faixa de Score | `st.slider` | range slider | `score` (coluna calculada) | Sim |
| 6 | Deals Zumbis | `st.radio` | 3 opcoes | `is_zombie` (flag calculada) | Sim |
| 7 | Setor da Conta | `st.multiselect` | multi-select | `accounts.sector` | Nao (adicional) |

---

## 3. Hierarquia Cascata: Regiao → Manager → Vendedor

Os tres primeiros filtros formam uma cascata hierarquica. A selecao de um nivel superior restringe as opcoes dos niveis inferiores.

### 3.1 Mapeamento dos dados

```
Central (11 vendedores)
├── Dustin Brinkmann (5)
└── Melvin Marxen (6)

East (12 vendedores)
├── Cara Losch (6)
└── Rocco Neubert (6)

West (12 vendedores)
├── Celia Rouche (6)
└── Summer Sewald (6)
```

### 3.2 Regras de cascata

```
1. Regiao selecionada → filtra lista de managers (so mostra managers daquela regiao)
2. Manager selecionado → filtra lista de vendedores (so mostra vendedores daquele manager)
3. Vendedor selecionado → filtra para deals individuais

Cada nivel tem opcao "Todos" como default.
Se Regiao = "Todos" → managers e vendedores de todas as regioes ficam disponiveis.
Se Manager = "Todos" (com regiao selecionada) → todos os vendedores daquela regiao.
```

### 3.3 Implementacao da cascata

```python
def _get_manager_options(df_teams: pd.DataFrame, selected_office: str) -> list[str]:
    """Retorna managers disponiveis dado o escritorio selecionado."""
    if selected_office == OPTION_ALL:
        managers = sorted(df_teams["manager"].unique().tolist())
    else:
        managers = sorted(
            df_teams[df_teams["regional_office"] == selected_office]["manager"]
            .unique()
            .tolist()
        )
    return [OPTION_ALL] + managers


def _get_agent_options(
    df_teams: pd.DataFrame, selected_office: str, selected_manager: str
) -> list[str]:
    """Retorna vendedores disponiveis dado escritorio e manager."""
    mask = pd.Series(True, index=df_teams.index)
    if selected_office != OPTION_ALL:
        mask &= df_teams["regional_office"] == selected_office
    if selected_manager != OPTION_ALL:
        mask &= df_teams["manager"] == selected_manager
    agents = sorted(df_teams[mask]["sales_agent"].unique().tolist())
    return [OPTION_ALL] + agents
```

### 3.4 Comportamento ao mudar nivel superior

Quando o usuario muda a **regiao**, o filtro de manager volta para "Todos" e o de vendedor tambem. Idem ao mudar manager: vendedor volta para "Todos". Isso evita estados inconsistentes (ex: manager do East selecionado com regiao Central).

Implementar via `st.session_state`:

```python
# Detectar mudanca de regiao
if st.session_state.get("_prev_office") != selected_office:
    st.session_state["filter_manager"] = OPTION_ALL
    st.session_state["filter_agent"] = OPTION_ALL
    st.session_state["_prev_office"] = selected_office

# Detectar mudanca de manager
if st.session_state.get("_prev_manager") != selected_manager:
    st.session_state["filter_agent"] = OPTION_ALL
    st.session_state["_prev_manager"] = selected_manager
```

---

## 4. Detalhamento de Cada Filtro

### 4.1 Escritorio/Regiao

- **Componente:** `st.selectbox`
- **Opcoes:** `["Todos", "Central", "East", "West"]`
- **Default:** `"Todos"`
- **Coluna filtrada:** `regional_office` (vem do merge com `sales_teams`)
- **Label:** `"Escritorio"`

### 4.2 Manager

- **Componente:** `st.selectbox`
- **Opcoes:** dinamicas (cascata da regiao). Total: 6 managers.
  - `Dustin Brinkmann`, `Melvin Marxen` (Central)
  - `Cara Losch`, `Rocco Neubert` (East)
  - `Celia Rouche`, `Summer Sewald` (West)
- **Default:** `"Todos"`
- **Coluna filtrada:** `manager`
- **Label:** `"Manager"`

### 4.3 Vendedor

- **Componente:** `st.selectbox`
- **Opcoes:** dinamicas (cascata de regiao + manager). Total: 35 vendedores.
- **Default:** `"Todos"`
- **Coluna filtrada:** `sales_agent`
- **Label:** `"Vendedor"`

### 4.4 Produto

- **Componente:** `st.multiselect`
- **Opcoes:** 7 produtos, ordem por preco decrescente:
  ```
  ["GTK 500", "GTX Plus Pro", "GTX Pro", "MG Advanced",
   "GTX Plus Basic", "GTX Basic", "MG Special"]
  ```
- **Default:** todos selecionados (lista completa)
- **Coluna filtrada:** `product`
- **Label:** `"Produto"`
- **Comportamento quando vazio:** se o usuario remover todos, tratar como "todos selecionados" (nao mostrar pipeline vazio).

### 4.5 Faixa de Score

- **Componente:** `st.slider`
- **Range:** `(0, 100)`
- **Default:** `(0, 100)`
- **Step:** `5`
- **Coluna filtrada:** `score` (coluna calculada pelo scoring engine)
- **Label:** `"Faixa de Score"`
- **Formato de exibicao:** `"Score: 25 - 80"`

### 4.6 Deals Zumbis (toggle)

- **Componente:** `st.radio`
- **Opcoes:**
  - `"Todos os deals"` — sem filtro, mostra tudo (default)
  - `"Apenas zumbis"` — so deals com `is_zombie == True`
  - `"Ocultar zumbis"` — so deals com `is_zombie == False`
- **Default:** `"Todos os deals"`
- **Coluna filtrada:** `is_zombie` (flag booleana calculada pelo scoring engine)
- **Label:** `"Deals Zumbis"`
- **Layout:** `horizontal=True` para ocupar menos espaco vertical.

### 4.7 Setor da Conta (adicional)

- **Componente:** `st.multiselect`
- **Opcoes:** 10 setores (alphabetico):
  ```
  ["employment", "entertainment", "finance", "marketing", "medical",
   "retail", "services", "software", "technology", "telecommunications"]
  ```
  **Nota:** o dataset tem um typo — `technolgy` em vez de `technology`. Corrigir na carga de dados (`data_loader.py`), nao no filtro.
- **Default:** todos selecionados
- **Coluna filtrada:** `sector` (vem do merge com `accounts`)
- **Label:** `"Setor"`
- **Comportamento quando vazio:** tratar como "todos selecionados".

---

## 5. Defaults por Persona

| Filtro | Vendedor | Manager | Head RevOps |
|--------|----------|---------|-------------|
| Escritorio | Todos | Todos | *seleciona regiao* |
| Manager | Todos | *seleciona seu nome* | Todos |
| Vendedor | *seleciona seu nome* | Todos | Todos |
| Produto | Todos | Todos | Todos |
| Score | 0-100 | 0-100 | 0-100 |
| Zumbis | Todos os deals | Apenas zumbis | Todos os deals |
| Setor | Todos | Todos | Todos |

**Nota sobre implementacao:** como nao ha autenticacao, nao ha como detectar automaticamente a persona. Os defaults sao `"Todos"` para todos os filtros. O usuario ajusta manualmente. A hierarquia cascata garante que 1-2 cliques sao suficientes para qualquer persona.

---

## 6. Logica de Aplicacao de Filtros (AND)

Todos os filtros sao combinados com logica AND. Cada filtro adicional restringe mais o resultado.

### 6.1 Funcao de aplicacao

```python
def apply_filters(df: pd.DataFrame, filters: FilterState) -> pd.DataFrame:
    """
    Aplica todos os filtros ao DataFrame de deals scorados.

    Parametros:
        df: DataFrame com deals scorados (ja com colunas de merge:
            regional_office, manager, score, is_zombie, sector)
        filters: objeto/dict com o estado de todos os filtros

    Retorno:
        DataFrame filtrado (subset de linhas de df)
    """
    mask = pd.Series(True, index=df.index)

    # Hierarquia organizacional
    if filters.office != OPTION_ALL:
        mask &= df["regional_office"] == filters.office
    if filters.manager != OPTION_ALL:
        mask &= df["manager"] == filters.manager
    if filters.agent != OPTION_ALL:
        mask &= df["sales_agent"] == filters.agent

    # Produto (multiselect — filtrar so se nao esta vazio e nao e o total)
    if filters.products and len(filters.products) < total_products:
        mask &= df["product"].isin(filters.products)

    # Score range
    mask &= df["score"].between(filters.score_min, filters.score_max)

    # Deals zumbis
    if filters.zombie_mode == "Apenas zumbis":
        mask &= df["is_zombie"] == True
    elif filters.zombie_mode == "Ocultar zumbis":
        mask &= df["is_zombie"] == False

    # Setor (multiselect)
    if filters.sectors and len(filters.sectors) < total_sectors:
        mask &= df["sector"].isin(filters.sectors)

    return df[mask]
```

### 6.2 Ordem de avaliacao

A ordem logica nao importa (todas sao condicoes AND sobre booleanos), mas a **ordem de exibicao** na sidebar importa para a experiencia do usuario. Ver secao 7.

---

## 7. Layout na Sidebar

Os filtros residem na sidebar do Streamlit (`st.sidebar`). Ordem de cima para baixo:

```
┌─────────────────────────┐
│  LEAD SCORER             │
│  ─────────────────────── │
│                          │
│  📋 VISAO                │
│  ┌─────────────────────┐ │
│  │ Escritorio    [▼]   │ │
│  └─────────────────────┘ │
│  ┌─────────────────────┐ │
│  │ Manager       [▼]   │ │
│  └─────────────────────┘ │
│  ┌─────────────────────┐ │
│  │ Vendedor      [▼]   │ │
│  └─────────────────────┘ │
│                          │
│  ─────────────────────── │
│  🔍 FILTROS              │
│  ┌─────────────────────┐ │
│  │ Produto     [multi] │ │
│  └─────────────────────┘ │
│  ┌─────────────────────┐ │
│  │ Setor       [multi] │ │
│  └─────────────────────┘ │
│  ┌─────────────────────┐ │
│  │ Score   [===●===●=] │ │
│  └─────────────────────┘ │
│                          │
│  ○ Todos ● Zumbis ○ OK  │
│                          │
│  ─────────────────────── │
│  35 deals encontrados    │
│  Pipeline: $1.2M         │
│                          │
└─────────────────────────┘
```

### Grupos visuais

1. **Grupo "Visao"** — Escritorio, Manager, Vendedor (cascata hierarquica, separador `st.divider()` ou `st.markdown("---")`)
2. **Grupo "Filtros"** — Produto, Setor, Score, Zumbis
3. **Resumo** — contador de deals e valor total apos filtros (feedback imediato)

O resumo no rodape da sidebar e essencial: ao ajustar filtros, o usuario ve instantaneamente quantos deals restaram. Isso evita configuracoes que resultam em zero deals sem que o usuario perceba.

---

## 8. Interface do Modulo

### 8.1 Constantes

```python
OPTION_ALL: str = "Todos"

SCORE_MIN: int = 0
SCORE_MAX: int = 100
SCORE_STEP: int = 5

ZOMBIE_OPTIONS: list[str] = ["Todos os deals", "Apenas zumbis", "Ocultar zumbis"]
```

### 8.2 FilterState (dataclass)

```python
from dataclasses import dataclass

@dataclass
class FilterState:
    """Estado imutavel dos filtros selecionados pelo usuario."""
    office: str            # "Todos" ou nome do escritorio
    manager: str           # "Todos" ou nome do manager
    agent: str             # "Todos" ou nome do vendedor
    products: list[str]    # lista de produtos selecionados
    sectors: list[str]     # lista de setores selecionados
    score_min: int         # limite inferior do slider de score
    score_max: int         # limite superior do slider de score
    zombie_mode: str       # "Todos os deals" | "Apenas zumbis" | "Ocultar zumbis"
```

### 8.3 Funcoes publicas

```python
def render_filters(
    df_teams: pd.DataFrame,
    df_products: pd.DataFrame,
    df_accounts: pd.DataFrame,
) -> FilterState:
    """
    Renderiza os filtros na sidebar do Streamlit e retorna o estado selecionado.

    Parametros:
        df_teams: DataFrame de sales_teams.csv (colunas: sales_agent, manager, regional_office)
        df_products: DataFrame de products.csv (colunas: product, series, sales_price)
        df_accounts: DataFrame de accounts.csv (colunas: account, sector, ...)

    Retorno:
        FilterState com todos os valores selecionados pelo usuario

    Efeitos colaterais:
        - Renderiza widgets na st.sidebar
        - Usa st.session_state para persistir estado da cascata
    """
    ...


def apply_filters(df: pd.DataFrame, filters: FilterState) -> pd.DataFrame:
    """
    Aplica o FilterState ao DataFrame de deals scorados.

    Parametros:
        df: DataFrame com deals scorados. Colunas esperadas:
            - sales_agent, manager, regional_office (do merge com sales_teams)
            - product (do pipeline)
            - sector (do merge com accounts)
            - score (float, 0-100, calculado pelo scoring engine)
            - is_zombie (bool, calculado pelo scoring engine)

    Retorno:
        DataFrame filtrado (mesmo schema, menos linhas)

    Nota:
        O DataFrame de entrada deve conter APENAS deals ativos (Prospecting + Engaging).
        Deals Won/Lost nao recebem score e nao devem ser passados para filtragem.
    """
    ...


def render_filter_summary(df_filtered: pd.DataFrame) -> None:
    """
    Renderiza o resumo pos-filtro na sidebar (contagem e valor total).

    Parametros:
        df_filtered: DataFrame ja filtrado

    Efeitos colaterais:
        - Renderiza metricas na st.sidebar
    """
    ...
```

### 8.4 Fluxo de uso no app.py

```python
# app.py — fluxo principal
from components.filters import render_filters, apply_filters, render_filter_summary

# 1. Carregar dados
df_pipeline, df_teams, df_products, df_accounts = load_data()

# 2. Calcular scores (apenas deals ativos)
df_scored = scoring_engine.score(df_pipeline, df_teams, df_products, df_accounts)

# 3. Renderizar filtros e obter estado
filters = render_filters(df_teams, df_products, df_accounts)

# 4. Aplicar filtros ao DataFrame scorado
df_filtered = apply_filters(df_scored, filters)

# 5. Mostrar resumo na sidebar
render_filter_summary(df_filtered)

# 6. Renderizar componentes com df_filtered
pipeline_view.render(df_filtered)
metrics.render(df_filtered)
```

---

## 9. Performance

### 9.1 Contexto

- ~8.800 registros totais no pipeline
- Deals ativos (Prospecting + Engaging): subset menor (a maioria e Won/Lost)
- Requisito PRD: carregamento em < 3 segundos

### 9.2 Estrategias

**A. Pre-computar o DataFrame merged uma unica vez**

O merge entre `sales_pipeline`, `sales_teams`, `accounts` e `products` deve acontecer uma vez na carga de dados, nao a cada mudanca de filtro. O DataFrame passado para `apply_filters` ja deve conter todas as colunas necessarias.

```python
# Em data_loader.py — executar uma vez
@st.cache_data
def load_and_merge() -> pd.DataFrame:
    pipeline = pd.read_csv("data/sales_pipeline.csv")
    teams = pd.read_csv("data/sales_teams.csv")
    accounts = pd.read_csv("data/accounts.csv")
    products = pd.read_csv("data/products.csv")

    df = pipeline.merge(teams, on="sales_agent", how="left")
    df = df.merge(accounts, on="account", how="left")
    df = df.merge(products, on="product", how="left")
    return df
```

**B. Filtragem via mascara booleana (nao copias)**

A funcao `apply_filters` usa `pd.Series` booleana com operadores `&=`. Isso opera sobre a mesma Serie sem criar copias intermediarias. A copia so acontece no `df[mask]` final, que e necessaria.

Para ~8.800 registros, cada operacao de mascara leva < 1ms. Todos os 7 filtros combinados: < 10ms. Nao ha preocupacao de performance nesta escala.

**C. Evitar re-renderizacao desnecessaria**

Usar `st.session_state` para armazenar o estado anterior dos filtros. Se nada mudou, nao recalcular. Porem, com ~8.800 registros, o custo de recalcular e negligivel — otimizacao prematura. Implementar apenas se necessario.

**D. Cache dos dados de referencia dos filtros**

As listas de opcoes (managers, vendedores, produtos, setores) sao derivadas dos CSVs e nao mudam. Computar uma vez e guardar.

### 9.3 O que NAO fazer

- Nao usar `@st.cache_data` em `render_filters` (funcoes que renderizam widgets nao devem ser cacheadas).
- Nao converter para categorias Pandas (overhead desnecessario para esta escala).
- Nao implementar filtragem server-side/database — os dados cabem confortavelmente em memoria.

---

## 10. Tratamento de Casos Especiais

### 10.1 Filtros que resultam em zero deals

Quando a combinacao de filtros resulta em DataFrame vazio:
- `render_filter_summary` mostra "0 deals encontrados"
- `pipeline_view` mostra mensagem: "Nenhum deal encontrado com os filtros selecionados. Tente ajustar os filtros."
- Nao quebrar, nao mostrar erro

### 10.2 Multiselect vazio

Quando o usuario remove todos os itens de um `st.multiselect` (Produto ou Setor):
- Tratar como "todos selecionados" — nao filtrar por essa dimensao
- Nao mostrar pipeline vazio

### 10.3 Typo no dataset

O campo `sector` em `accounts.csv` contem `"technolgy"` em vez de `"technology"`. A correcao deve ser feita no `data_loader.py` durante a carga, nao no modulo de filtros. O filtro recebe dados ja limpos.

### 10.4 Deals sem conta associada

Se algum deal nao tiver match no merge com `accounts` (sector = NaN):
- Incluir no filtro de setor como "Sem setor" ou tratar como match para qualquer filtro de setor
- Decisao: tratar NaN como match (nao excluir deals sem setor quando setor esta filtrado). Se o usuario filtra por "software", deals sem setor nao aparecem — isso e aceitavel.

---

## 11. Testes Manuais (Checklist)

Antes de considerar o modulo pronto, validar:

- [ ] Selecionar regiao "Central" → managers mostra apenas Dustin Brinkmann e Melvin Marxen
- [ ] Selecionar manager "Cara Losch" → vendedores mostra apenas os 6 vendedores dela
- [ ] Mudar regiao de "East" para "West" → manager e vendedor voltam para "Todos"
- [ ] Slider de score 50-80 → so mostra deals com score entre 50 e 80
- [ ] "Apenas zumbis" → so mostra deals com flag is_zombie == True
- [ ] "Ocultar zumbis" → nenhum deal zumbi no resultado
- [ ] Remover todos os produtos do multiselect → mostra todos os deals (nao pipeline vazio)
- [ ] Combinacao de filtros (manager + produto + score) → resultado e intersecao (AND)
- [ ] Resumo na sidebar atualiza ao mudar qualquer filtro
- [ ] Nenhuma combinacao de filtros causa erro/excecao

---

## 12. Dependencias

### Modulos que filters.py consome
- `streamlit` — widgets de sidebar
- `pandas` — manipulacao de DataFrame

### Modulos que consomem filters.py
- `app.py` — chama `render_filters()`, `apply_filters()`, `render_filter_summary()`
- `components/pipeline_view.py` — recebe o `df_filtered` resultante
- `components/deal_detail.py` — recebe o `df_filtered` resultante
- `components/metrics.py` — recebe o `df_filtered` resultante

### Dados de entrada necessarios (pre-merge)
O DataFrame passado para `apply_filters` deve conter estas colunas (resultado do merge em `data_loader.py`):

| Coluna | Origem | Tipo |
|--------|--------|------|
| `sales_agent` | sales_pipeline.csv | str |
| `manager` | sales_teams.csv (merge) | str |
| `regional_office` | sales_teams.csv (merge) | str |
| `product` | sales_pipeline.csv | str |
| `sector` | accounts.csv (merge) | str |
| `score` | scoring engine (calculado) | float |
| `is_zombie` | scoring engine (calculado) | bool |

---

## 13. Testes TDD (test_filters.py)

Antes de implementar `filters.py`, escrever os seguintes testes em `tests/test_filters.py`. Todos devem falhar inicialmente (Red) e passar apos a implementacao (Green).

### 13.1 Testes da cascata hierarquica

```python
def test_manager_options_filtered_by_office_central():
    """Selecionar 'Central' retorna apenas Dustin Brinkmann e Melvin Marxen."""

def test_manager_options_filtered_by_office_east():
    """Selecionar 'East' retorna apenas Cara Losch e Rocco Neubert."""

def test_manager_options_all_when_office_todos():
    """Selecionar 'Todos' retorna os 6 managers."""

def test_agent_options_filtered_by_manager():
    """Selecionar manager 'Cara Losch' retorna apenas os 6 vendedores dela."""

def test_agent_options_all_when_manager_todos():
    """Selecionar manager 'Todos' com regiao 'East' retorna todos os vendedores do East."""
```

### 13.2 Testes do apply_filters

```python
def test_apply_filters_office_filters_by_regional_office():
    """Filtrar por office='Central' retorna apenas deals de vendedores do Central."""

def test_apply_filters_manager_filters_by_manager():
    """Filtrar por manager='Cara Losch' retorna apenas deals dos vendedores dela."""

def test_apply_filters_agent_filters_by_sales_agent():
    """Filtrar por agent retorna apenas deals daquele vendedor."""

def test_apply_filters_products_multiselect():
    """Filtrar por lista de produtos retorna apenas deals com esses produtos."""

def test_apply_filters_score_range():
    """Filtrar por score_min=50, score_max=80 retorna deals com score nessa faixa."""

def test_apply_filters_zombie_mode_apenas_zumbis():
    """Filtrar 'Apenas zumbis' retorna so deals com is_zombie == True."""

def test_apply_filters_zombie_mode_ocultar_zumbis():
    """Filtrar 'Ocultar zumbis' retorna so deals com is_zombie == False."""

def test_apply_filters_combined_and_logic():
    """Multiplos filtros combinam com logica AND (intersecao)."""

def test_apply_filters_empty_products_returns_all():
    """Lista vazia de produtos trata como 'todos selecionados'."""

def test_apply_filters_empty_sectors_returns_all():
    """Lista vazia de setores trata como 'todos selecionados'."""

def test_apply_filters_no_filters_returns_all():
    """Sem filtros ativos retorna todos os deals."""
```

### 13.3 Testes de edge cases

```python
def test_apply_filters_returns_empty_when_no_match():
    """Combinacao impossivel retorna DataFrame vazio (sem erro)."""

def test_filter_state_dataclass_has_expected_fields():
    """FilterState tem todos os campos: office, manager, agent, products, sectors, score_min, score_max, zombie_mode."""
```
