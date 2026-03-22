# Spec Tecnica — Metricas de Resumo (Dashboard)

**Componente:** `components/metrics.py`
**Prioridade:** Desejavel (PRD 6.6)
**Ultima atualizacao:** 21 de marco de 2026

---

## 1. Visao Geral

O painel de metricas fica no topo da pagina principal, acima da tabela de pipeline. Funciona como o "resumo executivo" que o vendedor (ou manager) ve ao abrir a ferramenta na segunda-feira de manha. Todas as metricas sao **reativas aos filtros** aplicados na sidebar (vendedor, manager, regiao, produto, faixa de score, toggle de zumbis).

---

## 2. Layout Geral

```
+------------------------------------------------------------------+
|  [KPI Card 1]  [KPI Card 2]  [KPI Card 3]  [KPI Card 4]        |  <- Linha 1: 4 colunas (st.columns)
+------------------------------------------------------------------+
|  [Distribuicao por Faixa de Score]  |  [Pipeline Health]         |  <- Linha 2: 2 colunas (60/40)
|  (grafico de barras horizontal)     |  (donut chart)             |
+------------------------------------------------------------------+
|  [Win Rate Vendedor/Time]                                        |  <- Linha 3: condicional (so aparece
|  (barra horizontal comparativa)                                  |     quando ha filtro de vendedor/time)
+------------------------------------------------------------------+
|                                                                  |
|  [Tabela de Pipeline — pipeline_view.py]                         |  <- Resto da pagina
|                                                                  |
+------------------------------------------------------------------+
```

Posicionamento: as metricas devem ser renderizadas **antes** da tabela de pipeline em `app.py`. O `app.py` chama `render_metrics(df_filtered, df_full)` passando tanto o DataFrame filtrado quanto o completo (para calculos de comparacao/delta).

---

## 3. KPI Cards (Linha 1)

Usar `st.metric()` em 4 colunas via `st.columns(4)`. Cada card mostra valor principal + delta comparativo.

### 3.1 Deals Ativos

| Atributo | Valor |
|----------|-------|
| **Label** | "Deals Ativos" |
| **Valor** | Contagem de deals onde `deal_stage` in (`Prospecting`, `Engaging`) no DataFrame filtrado |
| **Formula** | `len(df[df['deal_stage'].isin(['Prospecting', 'Engaging'])])` |
| **Formato** | Inteiro com separador de milhar (ex: "2.089") |
| **Delta** | Quando ha filtro de vendedor: mostrar comparacao com media dos vendedores. Label do delta: "vs media/vendedor". Quando nao ha filtro: sem delta |

### 3.2 Valor Total do Pipeline

| Atributo | Valor |
|----------|-------|
| **Label** | "Pipeline Total" |
| **Valor** | Soma do valor estimado dos deals ativos filtrados |
| **Formula para Engaging** | `close_value` se disponivel; senao, usar preco do produto (`products.sales_price`) como proxy |
| **Formula para Prospecting** | Sempre usar preco do produto como proxy (nao ha `close_value`) |
| **Formato** | Moeda USD abreviada: "$1.2M", "$345K", "$12.5K" |
| **Delta** | Mostrar percentual que o pipeline filtrado representa do pipeline total. Ex: "32% do total" |

**Funcao auxiliar para formatacao de moeda:**

```python
def format_currency(value: float) -> str:
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    elif value >= 1_000:
        return f"${value / 1_000:.0f}K"
    else:
        return f"${value:.0f}"
```

### 3.3 Deals Zumbis

| Atributo | Valor |
|----------|-------|
| **Label** | "Deals Zumbis" |
| **Valor** | Contagem de deals com flag `is_zombie == True` no DataFrame filtrado |
| **Formula** | `len(df[df['is_zombie'] == True])` (flag calculada pelo scoring engine) |
| **Formato** | Inteiro + percentual do total. Ex: "847 (40%)" |
| **Delta** | Valor em pipeline inflado pelos zumbis: "~$X em risco". Usar `delta_color="inverse"` para que o delta apareca em vermelho |

### 3.4 Win Rate

| Atributo | Valor |
|----------|-------|
| **Label** | "Win Rate" |
| **Valor** | Win rate calculada sobre deals fechados (Won + Lost) no escopo do filtro |
| **Formula** | `won / (won + lost) * 100` onde Won = `deal_stage == 'Won'` e Lost = `deal_stage == 'Lost'` |
| **Formato** | Percentual com 1 decimal: "63.2%" |
| **Delta** | Comparacao com win rate geral (63.2%). Ex: "+5.2pp vs geral" ou "-3.1pp vs geral". Obs: usar `delta_color="normal"` (verde = positivo, vermelho = negativo) |

**Nota sobre Win Rate:** calcular usando **todos** os deals historicos do escopo (incluindo Won/Lost), nao apenas os ativos. Quando filtrado por vendedor, usar os deals historicos daquele vendedor.

---

## 4. Distribuicao por Faixa de Score (Linha 2, Coluna Esquerda)

### Definicao das Faixas

| Faixa | Range | Cor (hex) | Cor (nome) | Significado |
|-------|-------|-----------|------------|-------------|
| Prioridade Alta | 80-100 | `#2ecc71` | Verde | Deals saudaveis e de alto potencial |
| Atencao | 60-79 | `#f1c40f` | Amarelo | Deals que merecem acompanhamento |
| Risco | 40-59 | `#e67e22` | Laranja | Deals em deterioracao |
| Critico | 0-39 | `#e74c3c` | Vermelho | Deals com pouca chance de fechar |

### Grafico

| Atributo | Valor |
|----------|-------|
| **Tipo** | Barras horizontais (`plotly.express.bar`, orientation='h') |
| **Eixo Y** | Faixa de score (categorico, ordenado de cima para baixo: Alta -> Critico) |
| **Eixo X** | Quantidade de deals |
| **Cores** | Mapeadas pela tabela acima |
| **Anotacoes** | Dentro de cada barra: contagem + percentual. Ex: "234 (47%)" |
| **Titulo** | "Distribuicao por Score" |
| **Altura** | 250px |

### Implementacao Plotly

```python
import plotly.express as px

def create_score_distribution_chart(df: pd.DataFrame) -> go.Figure:
    bins = [0, 40, 60, 80, 101]
    labels = ['Critico (0-39)', 'Risco (40-59)', 'Atencao (60-79)', 'Alta (80-100)']
    colors = ['#e74c3c', '#e67e22', '#f1c40f', '#2ecc71']

    df['score_range'] = pd.cut(
        df['score'], bins=bins, labels=labels, right=False
    )
    counts = df['score_range'].value_counts().reindex(labels)

    fig = px.bar(
        x=counts.values,
        y=counts.index,
        orientation='h',
        color=counts.index,
        color_discrete_map=dict(zip(labels, colors)),
        text=[f"{v} ({v/len(df)*100:.0f}%)" for v in counts.values],
    )
    fig.update_layout(
        title="Distribuicao por Score",
        showlegend=False,
        height=250,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis_title="Deals",
        yaxis_title="",
    )
    fig.update_traces(textposition='inside')
    return fig
```

Renderizar com `st.plotly_chart(fig, use_container_width=True)`.

---

## 5. Pipeline Health (Linha 2, Coluna Direita)

### Grafico

| Atributo | Valor |
|----------|-------|
| **Tipo** | Donut chart (`plotly.graph_objects.Pie`, hole=0.5) |
| **Segmentos** | 2: Saudaveis vs Zumbis |
| **Cores** | Saudaveis: `#2ecc71` (verde), Zumbis: `#e74c3c` (vermelho) |
| **Centro** | Texto central: total de deals ativos. Ex: "2.089 deals" |
| **Titulo** | "Saude do Pipeline" |
| **Altura** | 250px |

### Definicao de "Zumbi" (referencia)

Um deal e classificado como zumbi quando:

```
tempo_no_stage > 2x referencia_do_stage
AND deal_stage IN ('Prospecting', 'Engaging')
```

Onde `referencia_do_stage`:
- Prospecting: mediana de dias em Prospecting dos deals que avancaram para Engaging
- Engaging: P75 dos deals Won (88 dias)

**A flag `is_zombie` ja vem calculada pelo `scoring/engine.py`.** O componente de metricas apenas consome essa flag.

### Anotacao abaixo do grafico

Texto descritivo com `st.caption()`:

```
"X deals zumbis representando ~$Y em pipeline inflado"
```

Onde `$Y` e a soma do valor estimado dos deals zumbis, formatado com `format_currency()`.

### Implementacao Plotly

```python
import plotly.graph_objects as go

def create_pipeline_health_chart(df: pd.DataFrame) -> go.Figure:
    zombies = df['is_zombie'].sum()
    healthy = len(df) - zombies

    fig = go.Figure(data=[go.Pie(
        labels=['Saudaveis', 'Zumbis'],
        values=[healthy, zombies],
        hole=0.5,
        marker_colors=['#2ecc71', '#e74c3c'],
        textinfo='label+percent',
        textposition='outside',
    )])
    fig.update_layout(
        title="Saude do Pipeline",
        height=250,
        margin=dict(l=0, r=0, t=40, b=0),
        showlegend=False,
        annotations=[dict(
            text=f"{len(df)}<br>deals",
            x=0.5, y=0.5,
            font_size=16, showarrow=False,
        )],
    )
    return fig
```

---

## 6. Win Rate Vendedor/Time (Linha 3 — Condicional)

Esta secao **so aparece** quando ha um filtro de vendedor ou manager ativo. Sem filtro, nao renderizar (evitar poluicao visual).

### Cenario: Filtro por Vendedor

Mostrar barra horizontal comparativa com 3 valores:

| Metrica | Calculo | Cor |
|---------|---------|-----|
| WR do Vendedor | `wins_vendedor / (wins_vendedor + losses_vendedor)` | Azul `#3498db` |
| WR do Time (manager) | `wins_time / (wins_time + losses_time)` | Cinza `#95a5a6` |
| WR Geral | 63.2% (constante ou recalculada) | Cinza claro `#bdc3c7` |

### Cenario: Filtro por Manager (time)

Mostrar barras horizontais para cada vendedor do time, ordenadas por WR decrescente:

| Atributo | Valor |
|----------|-------|
| **Tipo** | Barras horizontais (`px.bar`, orientation='h') |
| **Eixo Y** | Nome do vendedor |
| **Eixo X** | Win Rate (%) |
| **Cor** | Gradiente: verde (>65%), amarelo (55-65%), vermelho (<55%) |
| **Linha de referencia** | Linha vertical tracejada no WR geral (63.2%) |
| **Titulo** | "Win Rate — Time de [Manager]" |
| **Altura** | 40px por vendedor, minimo 200px |

### Implementacao Plotly

```python
def create_seller_winrate_chart(
    seller_name: str,
    seller_wr: float,
    team_wr: float,
    general_wr: float,
) -> go.Figure:
    categories = ['Geral', 'Time', seller_name]
    values = [general_wr * 100, team_wr * 100, seller_wr * 100]
    colors = ['#bdc3c7', '#95a5a6', '#3498db']

    fig = go.Figure(data=[go.Bar(
        y=categories,
        x=values,
        orientation='h',
        marker_color=colors,
        text=[f"{v:.1f}%" for v in values],
        textposition='outside',
    )])
    fig.update_layout(
        title=f"Win Rate — {seller_name}",
        height=200,
        margin=dict(l=0, r=60, t=40, b=0),
        xaxis=dict(range=[0, 100], title="Win Rate (%)"),
        yaxis_title="",
    )
    return fig
```

---

## 7. Reatividade aos Filtros

Todas as metricas **reagem** aos filtros da sidebar. A logica de filtragem e aplicada **antes** de chamar `render_metrics()`.

### Matriz de Impacto dos Filtros

| Filtro | KPI Cards | Distrib. Score | Pipeline Health | WR Vendedor |
|--------|-----------|----------------|-----------------|-------------|
| Vendedor | Recalcula para deals do vendedor | Recalcula | Recalcula | **Aparece** com comparacao |
| Manager | Recalcula para deals do time | Recalcula | Recalcula | **Aparece** com barras por vendedor |
| Regiao | Recalcula para deals da regiao | Recalcula | Recalcula | Nao aparece |
| Produto | Recalcula para deals do produto | Recalcula | Recalcula | Nao aparece |
| Faixa de Score | Recalcula contagens | **Destaca** faixa selecionada | Recalcula | Nao afeta |
| Toggle Zumbis | Se "so zumbis": filtra | Recalcula | Mostra so zumbis | Nao afeta |

### Comportamento dos Deltas

Os deltas nos KPI cards comparam o escopo filtrado com o escopo total. Isso significa que:

- `render_metrics()` recebe **dois** DataFrames: `df_filtered` (com filtros aplicados) e `df_all` (sem filtros, mas com scores calculados)
- Deltas sao calculados como: `metrica(df_filtered) - metrica(df_all)` ou como percentual relativo
- Quando nao ha filtro ativo (df_filtered == df_all), os deltas sao omitidos (`delta=None` no `st.metric`)

---

## 8. Assinatura da Funcao Principal

```python
def render_metrics(
    df_filtered: pd.DataFrame,
    df_all: pd.DataFrame,
    active_filters: dict,
) -> None:
```

### Parametros

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| `df_filtered` | `pd.DataFrame` | DataFrame de **todos** os deals (incluindo Won/Lost) filtrado pela sidebar. Deve conter a coluna `score` calculada pelo engine e a flag `is_zombie` |
| `df_all` | `pd.DataFrame` | DataFrame completo sem filtros, para calculo de deltas comparativos |
| `active_filters` | `dict` | Dicionario indicando quais filtros estao ativos. Chaves: `seller` (str ou None), `manager` (str ou None), `region` (str ou None), `product` (str ou None), `score_range` (tuple ou None), `zombies_only` (bool) |

### Colunas Esperadas no DataFrame

O DataFrame passado para `render_metrics` deve conter pelo menos:

| Coluna | Tipo | Origem |
|--------|------|--------|
| `opportunity_id` | str | sales_pipeline.csv |
| `deal_stage` | str | sales_pipeline.csv |
| `sales_agent` | str | sales_pipeline.csv |
| `product` | str | sales_pipeline.csv |
| `account` | str | sales_pipeline.csv |
| `close_value` | float | sales_pipeline.csv (null para Prospecting/Engaging) |
| `engage_date` | datetime | sales_pipeline.csv |
| `close_date` | datetime | sales_pipeline.csv |
| `sales_price` | float | products.csv (join) |
| `sector` | str | accounts.csv (join) |
| `manager` | str | sales_teams.csv (join) |
| `regional_office` | str | sales_teams.csv (join) |
| `score` | float | scoring/engine.py |
| `is_zombie` | bool | scoring/engine.py |
| `days_in_stage` | int | calculado pelo engine |
| `estimated_value` | float | close_value ou sales_price como proxy |

---

## 9. Tratamento de Edge Cases

| Situacao | Comportamento |
|----------|---------------|
| Nenhum deal ativo no filtro | Mostrar "0" nos KPIs, graficos com estado vazio (mensagem "Nenhum deal encontrado") |
| Vendedor sem deals historicos (Won/Lost) | Win Rate mostra "N/D" em vez de percentual. Delta omitido |
| Todos os deals sao zumbis | Donut mostra 100% vermelho. Caption: "Atencao: todos os deals no filtro sao zumbis" |
| Filtro retorna 1 deal | Graficos simplificados; distribuicao de score mostra 1 barra |
| Pipeline value = $0 (so Prospecting sem proxy) | Mostrar "$0" e caption explicativa: "Deals em Prospecting sem valor estimado" |

---

## 10. Performance

| Requisito | Target |
|-----------|--------|
| Renderizacao das metricas | < 200ms para 8.800 registros |
| Recalculo apos filtro | < 100ms (operacoes Pandas vetorizadas) |
| Tamanho dos graficos Plotly | Limitar dados a agregacoes (nunca passar 8.800 pontos para Plotly) |

**Estrategias:**
- Usar `@st.cache_data` para calculos que dependem so do dataset completo (WR geral, medias de referencia)
- Graficos recebem dados ja agregados (contagens, somas), nao o DataFrame bruto
- Evitar loops Python; usar operacoes vetorizadas do Pandas

---

## 11. Dados de Referencia (Constantes)

Valores pre-calculados a partir da analise exploratoria, usados como benchmarks:

```python
# Constantes de referencia (calibradas com dados reais)
REFERENCE_DATE = pd.Timestamp('2017-12-31')
GENERAL_WIN_RATE = 0.632              # 63.2%
TOTAL_OPPORTUNITIES = 8800
TOTAL_ACTIVE_DEALS = 2089             # 1589 Engaging + 500 Prospecting
ENGAGING_VELOCITY_P75 = 88            # dias (referencia para decay)
ENGAGING_VELOCITY_MEDIAN = 57         # dias (mediana dos Won)
ZOMBIE_THRESHOLD_MULTIPLIER = 2.0     # tempo > 2x referencia = zumbi
SELLER_WR_MIN = 0.55                  # Lajuana Vencill
SELLER_WR_MAX = 0.704                 # Hayden Neloms
AVG_DEALS_PER_SELLER = 77             # media de deals ativos por vendedor
```

---

## 12. Exemplo de Uso no app.py

```python
# app.py (trecho relevante)
from components.metrics import render_metrics
from components.filters import render_filters
from components.pipeline_view import render_pipeline

# Carregar e processar dados
df_all = load_and_score_data()

# Sidebar: filtros
active_filters = render_filters(df_all)

# Aplicar filtros
df_filtered = apply_filters(df_all, active_filters)

# Metricas no topo
render_metrics(df_filtered, df_all, active_filters)

# Tabela de pipeline abaixo
render_pipeline(df_filtered)
```

---

## 13. Checklist de Implementacao

- [ ] KPI Card: Deals Ativos com delta vs media/vendedor
- [ ] KPI Card: Pipeline Total com formatacao de moeda abreviada
- [ ] KPI Card: Deals Zumbis com valor em risco
- [ ] KPI Card: Win Rate com delta vs geral em pontos percentuais
- [ ] Grafico: Distribuicao por faixa de score (barras horizontais, 4 cores)
- [ ] Grafico: Pipeline Health donut (saudaveis vs zumbis)
- [ ] Grafico: Win Rate vendedor/time (condicional, so com filtro)
- [ ] Reatividade: todas as metricas recalculam ao mudar filtros
- [ ] Deltas: omitidos quando nao ha filtro ativo
- [ ] Edge cases: estados vazios, vendedor sem historico, pipeline zerado
- [ ] Performance: metricas renderizam em < 200ms
- [ ] Cache: `@st.cache_data` nos calculos de referencia

---

## 14. Testes TDD (test_metrics.py)

Antes de implementar `metrics.py`, escrever os seguintes testes em `tests/test_metrics.py`. Todos devem falhar inicialmente (Red) e passar apos a implementacao (Green).

### 14.1 Testes de calculo de KPIs

```python
def test_count_active_deals_only_prospecting_and_engaging():
    """Contagem de deals ativos inclui apenas Prospecting e Engaging."""

def test_pipeline_total_uses_estimated_value():
    """Valor total usa close_value (Won) ou sales_price (ativos) como proxy."""

def test_zombie_count_matches_is_zombie_flag():
    """Contagem de zumbis = len(df[df['is_zombie'] == True])."""

def test_win_rate_calculated_from_won_and_lost():
    """Win rate = Won / (Won + Lost), usando deals historicos."""

def test_win_rate_returns_none_when_no_closed_deals():
    """Win rate e None quando nao ha deals fechados no filtro."""
```

### 14.2 Testes de formatacao de moeda

```python
def test_format_currency_millions():
    """1.200.000 -> '$1.2M'."""

def test_format_currency_thousands():
    """45.000 -> '$45K'."""

def test_format_currency_small():
    """55 -> '$55'."""
```

### 14.3 Testes de distribuicao de score

```python
def test_score_distribution_has_4_faixas():
    """Distribuicao retorna exatamente 4 faixas: Critico, Risco, Atencao, Alta."""

def test_score_distribution_counts_sum_to_total():
    """Soma das contagens das faixas = total de deals."""

def test_score_80_falls_in_alta_prioridade():
    """Score 80 cai na faixa 'Alta (80-100)'."""

def test_score_39_falls_in_critico():
    """Score 39 cai na faixa 'Critico (0-39)'."""
```

### 14.4 Testes de pipeline health

```python
def test_pipeline_health_sums_to_total_deals():
    """Saudaveis + Zumbis = total de deals."""

def test_pipeline_health_zero_zombies():
    """Quando nao ha zumbis, donut mostra 100% saudavel."""
```

### 14.5 Testes de edge cases

```python
def test_metrics_handle_empty_dataframe():
    """DataFrame vazio nao causa erro, mostra zeros."""

def test_metrics_handle_single_deal():
    """DataFrame com 1 deal funciona corretamente."""
```
