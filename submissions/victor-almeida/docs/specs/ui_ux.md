# Especificacao Tecnica de UI/UX — Lead Scorer

**Documento:** Especificacao de Interface e Experiencia do Usuario
**Aplicacao:** Lead Scorer — Priorizacao de Pipeline para Vendedores
**Stack:** Streamlit (Python) + Plotly + CSS customizado
**Autor:** Victor Almeida
**Data:** 21 de marco de 2026

---

## 1. Layout Geral da Aplicacao

### 1.1 Configuracao do Streamlit

```python
st.set_page_config(
    page_title="Lead Scorer — Pipeline Inteligente",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

- Layout `wide` obrigatorio — tabela de pipeline precisa de espaco horizontal
- Sidebar sempre expandida no primeiro acesso (filtros visiveis)
- Titulo da aba do navegador: "Lead Scorer — Pipeline Inteligente"

### 1.2 Wireframe Textual (ASCII)

```
+------------------------------------------------------------------+
| BARRA SUPERIOR (st.title + st.caption)                           |
| Lead Scorer                                                       |
| Priorizacao inteligente de pipeline — [data referencia]           |
+------------------------------------------------------------------+
|          |                                                        |
| SIDEBAR  |  AREA PRINCIPAL                                       |
| (280px)  |                                                        |
|          |  +--------------------------------------------------+ |
| Filtros  |  | METRICAS RESUMO (4 colunas st.metric)            | |
|          |  | Deals   | Valor    | Score   | Deals             | |
|          |  | Ativos  | Pipeline | Medio   | Zumbis            | |
|          |  +--------------------------------------------------+ |
| Vendedor |                                                        |
| Manager  |  +--------------------------------------------------+ |
| Regiao   |  | GRAFICO DISTRIBUICAO DE SCORES (Plotly)          | |
| Produto  |  | [histograma ou gauge chart]                      | |
| Faixa    |  +--------------------------------------------------+ |
| Score    |                                                        |
| Zumbis   |  +--------------------------------------------------+ |
|          |  | TABELA PIPELINE (st.dataframe ou AgGrid)         | |
| -------- |  |                                                  | |
| Legenda  |  | Score | Deal | Conta | Produto | Valor | Stage  | |
| de Cores |  |  87   | #123 | Acme  | GTK 500 | $26k  | Engag. | |
|          |  |  72   | #456 | Beta  | GTXPro  | $4.8k | Engag. | |
|          |  |  34   | #789 | Gama  | MG Spc  | $55   | Prosp. | |
|          |  |                                                  | |
|          |  +--------------------------------------------------+ |
|          |                                                        |
|          |  +--------------------------------------------------+ |
|          |  | DETALHE DO DEAL (expander ou secao condicional)  | |
|          |  |                                                  | |
|          |  | Score: 72/100                                    | |
|          |  | [===========================-------] 72           | |
|          |  |                                                  | |
|          |  | Composicao do Score:                             | |
|          |  |   Stage (Engaging)         21/30                 | |
|          |  |   Valor Esperado           18/25                 | |
|          |  |   Velocidade               15/25                 | |
|          |  |   Seller-Fit                8/10                 | |
|          |  |   Saude da Conta            6/10                 | |
|          |  |                                                  | |
|          |  | Proxima Acao:                                    | |
|          |  | "Deal saudavel e de alto valor.                  | |
|          |  |  Prioridade maxima para fechar."                 | |
|          |  +--------------------------------------------------+ |
|          |                                                        |
+------------------------------------------------------------------+
```

### 1.3 Hierarquia de Leitura (Ordem Visual)

A ordem em que o usuario percorre a tela corresponde a prioridade de informacao:

1. **Metricas resumo** — visao instantanea da saude do pipeline
2. **Distribuicao de scores** — contexto visual antes de mergulhar nos dados
3. **Tabela pipeline** — os deals rankeados, onde o vendedor toma decisao
4. **Detalhe do deal** — drill-down sob demanda (nao polui a visao geral)

---

## 2. Paleta de Cores e Sistema de Cores por Score

### 2.1 Cores Primarias da Aplicacao

| Elemento              | Cor          | Hex       | Uso                             |
|-----------------------|--------------|-----------|----------------------------------|
| Fundo principal       | Branco       | `#FFFFFF` | Background da area principal     |
| Fundo sidebar         | Cinza claro  | `#F0F2F6` | Background sidebar (padrao Streamlit) |
| Texto principal       | Cinza escuro | `#262730` | Corpo de texto                   |
| Texto secundario      | Cinza medio  | `#6B7280` | Labels, captions                 |
| Acento primario       | Azul         | `#1F77B4` | Links, botoes, elementos interativos |

### 2.2 Sistema de Cores por Faixa de Score

O score de 0 a 100 e mapeado em 4 faixas com cores semanticas. As cores devem comunicar urgencia e prioridade sem necessitar explicacao textual.

| Faixa de Score | Label          | Cor de Fundo   | Cor do Texto | Hex Fundo   | Hex Texto   |
|----------------|----------------|----------------|--------------|-------------|-------------|
| 80-100         | Alta Prioridade | Verde claro    | Verde escuro | `#DEF7EC`   | `#03543F`   |
| 60-79          | Atencao         | Amarelo claro  | Amarelo esc. | `#FDF6B2`   | `#723B13`   |
| 40-59          | Risco           | Laranja claro  | Laranja esc. | `#FEECDC`   | `#9A3412`   |
| 0-39           | Critico         | Vermelho claro | Vermelho esc.| `#FDE8E8`   | `#9B1C1C`   |

> **Nota:** Faixas padronizadas com `scoring/constants.py` e identicas em todos os componentes (pipeline_view, metrics, ui). Calibradas com a distribuicao real: score medio ~45-55.

### 2.3 Cores de Flags e Status

| Flag / Status     | Cor           | Hex       | Icone sugerido |
|-------------------|---------------|-----------|----------------|
| Deal Zumbi        | Vermelho      | `#DC2626` | caveira / alerta |
| Zumbi Critico     | Vermelho dark | `#991B1B` | caveira dupla  |
| Conta Recorrente Lost | Laranja   | `#EA580C` | alerta         |
| Deal Saudavel     | Verde         | `#059669` | check          |
| Dados Insuficientes | Cinza       | `#9CA3AF` | info           |

### 2.4 Implementacao das Cores na Tabela

Usar `st.dataframe` com `Styler` do Pandas para colorir linhas por faixa de score:

```python
def colorir_por_score(row):
    score = row['Score']
    if score >= 75:
        return ['background-color: #DEF7EC; color: #03543F'] * len(row)
    elif score >= 50:
        return ['background-color: #FDF6B2; color: #723B13'] * len(row)
    elif score >= 25:
        return ['background-color: #FEECDC; color: #9A3412'] * len(row)
    else:
        return ['background-color: #FDE8E8; color: #9B1C1C'] * len(row)
```

Alternativa: usar `st.data_editor` (Streamlit 1.23+) com `column_config` para formatacao nativa, ou renderizar HTML customizado via `st.markdown` com `unsafe_allow_html=True`.

---

## 3. Tipografia e Hierarquia Visual

### 3.1 Hierarquia de Textos

Streamlit usa Source Sans Pro por padrao. Manter essa fonte para consistencia. A hierarquia e controlada pelos componentes nativos:

| Nivel       | Componente Streamlit    | Uso                                   | Tamanho aprox. |
|-------------|-------------------------|----------------------------------------|----------------|
| H1          | `st.title()`            | Titulo da aplicacao (1 por pagina)    | 32px bold      |
| H2          | `st.header()`           | Secoes principais (Metricas, Pipeline) | 24px bold      |
| H3          | `st.subheader()`        | Subsecoes (Detalhe do Deal)           | 20px bold      |
| Caption     | `st.caption()`          | Texto auxiliar, datas, disclaimers     | 14px regular   |
| Body        | `st.write()` / `st.markdown()` | Explicacoes, textos de NBA       | 16px regular   |
| Metric      | `st.metric()`           | KPIs resumo (valor + delta)           | 28px value     |

### 3.2 Regras de Formatacao de Dados

| Tipo de dado     | Formato                  | Exemplo          |
|------------------|--------------------------|------------------|
| Score            | Inteiro sem decimal      | `72`             |
| Valor monetario  | USD com separador milhar | `$26.768`        |
| Percentual       | 1 casa decimal + %       | `63.2%`          |
| Dias             | Inteiro + " dias"        | `45 dias`        |
| Data             | DD/MM/YYYY               | `31/12/2017`     |
| Win Rate         | 1 casa decimal + %       | `70.4%`          |
| Contagem         | Inteiro com separador    | `1.589`          |

### 3.3 Espacamento

- Usar `st.divider()` entre secoes principais (metricas, grafico, tabela)
- `st.write("")` ou `st.markdown("<br>", unsafe_allow_html=True)` para espacamento fino entre blocos (quando necessario)
- Colunas com `gap="medium"` (padrao) para metricas resumo
- Nao usar `st.empty()` para espacamento — polui o DOM

---

## 4. Fluxo do Usuario

### 4.1 Fluxo Primario — Vendedor (Segunda-feira de Manha)

```
ABRIR APP
    |
    v
[Tela carrega com TODOS os deals ativos — sem filtro]
    |
    v
VENDEDOR SELECIONA SEU NOME na sidebar
    |
    v
[Metricas atualizam: seus deals, seu pipeline, seu score medio]
[Tabela filtra: apenas deals DELE, ordenados por score desc]
    |
    v
VENDEDOR VE TOP 5-10 DEALS (prioridade alta em verde)
    |
    v
CLICA/EXPANDE UM DEAL para ver detalhe
    |
    v
[Ve composicao do score + explicacao + proxima acao]
    |
    v
ENTENDE O QUE FAZER (NBA diz a acao)
    |
    v
REPETE para proximo deal ou FILTRA deals zumbis
```

### 4.2 Fluxo Secundario — Manager (Reuniao de Pipeline)

```
ABRIR APP
    |
    v
MANAGER SELECIONA SEU NOME como manager na sidebar
    |
    v
[Ve todos os deals do time]
    |
    v
ATIVA FILTRO "Mostrar apenas Deals Zumbis"
    |
    v
[Ve deals zumbis do time — candidatos a limpeza de forecast]
    |
    v
ANALISA METRICAS do time (score medio, deals zumbis, valor inflado)
```

### 4.3 Fluxo Terciario — Head RevOps (Visao Macro)

```
ABRIR APP
    |
    v
[Mantem visao geral — sem filtro de vendedor]
    |
    v
FILTRA POR REGIAO ou PRODUTO
    |
    v
[Compara saude do pipeline por escritorio/produto]
    |
    v
ANALISA DISTRIBUICAO DE SCORES
    |
    v
[Identifica regioes/produtos com mais deals de baixo score]
```

### 4.4 Estado Inicial da Aplicacao (Primeiro Carregamento)

Ao abrir sem nenhum filtro selecionado:

- **Tabela:** mostra TODOS os deals ativos (Prospecting + Engaging), ordenados por score descendente
- **Metricas:** mostram totais gerais do pipeline
- **Filtros:** todos em estado "Todos" (nenhum selecionado)
- **Mensagem de boas-vindas:** `st.info()` sutil sugerindo selecionar um vendedor
  - Texto: "Selecione um vendedor na barra lateral para ver o pipeline personalizado."

---

## 5. Linguagem e Tom de Comunicacao

### 5.1 Principios

1. **Linguagem de vendedor, nao de analista.** O usuario nao sabe o que e P75, decay exponencial ou log-scaling. Ele sabe o que e "deal parado", "conta dificil" e "prioridade alta".
2. **Direto ao ponto.** Frases curtas. Verbos de acao. Sem rodeios.
3. **Portugues (PT-BR)** em toda a interface — labels, tooltips, mensagens, explicacoes.
4. **Tom profissional mas acessivel.** Nao e um paper academico nem um chat casual.

### 5.2 Exemplos de Textos: Bom vs Ruim

**Labels da interface:**

| Contexto           | Ruim                                          | Bom                                    |
|--------------------|-----------------------------------------------|----------------------------------------|
| Coluna de score    | "Score Composto Ponderado"                    | "Score"                                |
| Coluna de tempo    | "Dias de Permanencia no Stage Atual"          | "Dias no Stage"                        |
| Filtro de zumbi    | "Filtrar por Flag de Inatividade Temporal"     | "Mostrar Deals Zumbis"                 |
| Metrica de valor   | "Soma Agregada de Close Value Estimado"        | "Valor Total do Pipeline"              |
| Filtro de score    | "Range de Score Composto"                      | "Faixa de Score"                       |

**Explicacoes de score:**

| Contexto                         | Ruim                                                                  | Bom                                                                 |
|----------------------------------|-----------------------------------------------------------------------|---------------------------------------------------------------------|
| Deal saudavel                    | "Ratio temporal 0.8x (abaixo do P75), EV log-normalized em Q3"       | "Deal em Engaging ha 45 dias (saudavel). Valor alto. Prioridade."  |
| Deal parado                      | "Decay factor 0.30 aplicado — ratio 1.7x acima da referencia P75"    | "Deal parado ha 150 dias — muito acima do normal (88 dias)."       |
| Seller fit alto                  | "Multiplicador seller-sector 1.78 (WR 80% vs baseline 45%)"          | "Voce tem historico forte neste setor (80% de fechamento)."        |
| Conta com problemas              | "Account health score 0.23 — 5/22 deals Won, penalizacao aplicada"   | "Esta conta tem historico dificil — so 23% dos deals fecharam."    |

**Next Best Action (NBA):**

| Contexto                          | Ruim                                                          | Bom                                                                    |
|-----------------------------------|---------------------------------------------------------------|------------------------------------------------------------------------|
| Deal parado                       | "Executar acao de re-engajamento conforme SLA do stage"       | "Deal parado ha 120 dias. Agende um follow-up ou reavalie."           |
| Deal em risco com valor alto      | "Acionar escalation path para deal de alto EV"                | "Deal de alto valor perdendo ritmo. Envolver seu manager."            |
| Vendedor fraco no setor           | "Consultar peer com superior seller-sector fit"               | "Seu historico nesse setor e abaixo da media. Fale com [nome]."      |
| Conta com multiplos losses        | "Reavaliar account strategy baseado no historico"             | "Esta conta ja teve 4 deals perdidos. Revise a abordagem."           |
| Tudo certo                        | "Manter cadencia atual de follow-up"                          | "Deal saudavel e de alto valor. Foque em fechar essa semana."        |

### 5.3 Glossario da Interface (Termos Permitidos)

| Termo tecnico interno     | Traduzido para o usuario         |
|---------------------------|----------------------------------|
| Score                     | Score (manter — vendedores entendem) |
| Stage                     | Estagio (ou Stage — ja e jargao de CRM) |
| Prospecting               | Prospeccao (ou manter Prospecting) |
| Engaging                  | Em Negociacao (ou manter Engaging) |
| Win Rate                  | Taxa de Fechamento               |
| Decay                     | Nunca usar — dizer "deal perdendo forca" |
| Seller-Deal Fit           | Nunca usar — dizer "seu historico neste setor" |
| Account Health            | Nunca usar — dizer "historico da conta" |
| Expected Value            | Nunca usar — dizer "valor do deal" |
| Deal Zumbi                | Deal Zumbi (manter — e descritivo) |
| Pipeline                  | Pipeline (manter — vendedores usam) |
| Forecast                  | Forecast (manter)                |
| NBA                       | "Proxima Acao" ou "Acao Sugerida" |

---

## 6. Componentes Streamlit Recomendados por Secao

### 6.1 Sidebar — Filtros (`components/filters.py`)

```python
# Estrutura recomendada da sidebar
with st.sidebar:
    st.header("Filtros")

    # Filtro de vendedor — o mais importante, vem primeiro
    vendedor = st.selectbox(
        "Vendedor",
        options=["Todos"] + lista_vendedores,
        index=0,
        help="Selecione para ver apenas seus deals"
    )

    # Filtro de manager
    manager = st.selectbox(
        "Manager",
        options=["Todos"] + lista_managers,
        index=0
    )

    # Filtro de regiao
    regiao = st.selectbox(
        "Escritorio Regional",
        options=["Todos"] + lista_regioes,
        index=0
    )

    # Filtro de produto
    produto = st.multiselect(
        "Produtos",
        options=lista_produtos,
        default=lista_produtos  # todos selecionados
    )

    st.divider()

    # Faixa de score — slider
    faixa_score = st.slider(
        "Faixa de Score",
        min_value=0,
        max_value=100,
        value=(0, 100),
        step=5
    )

    # Toggle de deals zumbis
    mostrar_zumbis = st.toggle(
        "Mostrar apenas Deals Zumbis",
        value=False,
        help="Filtra deals parados ha mais que o dobro do tempo normal"
    )

    st.divider()

    # Legenda de cores
    st.caption("Legenda de Cores")
    st.markdown("""
    - 🟢 **80-100:** Alta Prioridade
    - 🟡 **60-79:** Atencao
    - 🟠 **40-59:** Risco
    - 🔴 **0-39:** Critico
    """)
```

**Notas sobre os filtros:**

- `st.selectbox` para vendedor/manager/regiao (selecao unica — o vendedor so e um)
- `st.multiselect` para produto (pode querer filtrar por grupo de produtos)
- `st.slider` com range para faixa de score (intuitivo, visual)
- `st.toggle` para deals zumbis (on/off binario)
- Ordem dos filtros: do mais usado (vendedor) para o menos usado (zumbis)
- Filtros devem ser **interdependentes**: ao selecionar manager, a lista de vendedores filtra apenas os daquele manager. Ao selecionar regiao, manager e vendedor filtram pela regiao.

### 6.2 Metricas Resumo (`components/metrics.py`)

```python
# 4 colunas com metricas principais
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Deals Ativos",
        value="127",
        help="Total de deals em Prospecting e Engaging"
    )

with col2:
    st.metric(
        label="Valor do Pipeline",
        value="$1.2M",
        help="Soma do valor estimado dos deals ativos"
    )

with col3:
    st.metric(
        label="Score Medio",
        value="54",
        help="Media dos scores de todos os deals filtrados"
    )

with col4:
    st.metric(
        label="Deals Zumbis",
        value="23",
        delta="-18%",
        delta_color="normal",
        help="Deals parados ha mais que o dobro do tempo de referencia"
    )
```

**Notas:**

- Usar `delta` do `st.metric` quando houver comparacao relevante (ex: vs media do time)
- `help` parameter adiciona tooltip com o "?" — usar para explicacoes sem poluir a tela
- As metricas devem reagir aos filtros — se o vendedor seleciona seu nome, mostra apenas os dados dele
- Considerar uma segunda linha com metricas secundarias (taxa de fechamento, dias medio no stage) usando `st.columns(4)` novamente, mas com `st.caption` ao inves de `st.metric` para menor destaque

### 6.3 Grafico de Distribuicao (`components/metrics.py`)

```python
import plotly.express as px

# Histograma de distribuicao de scores
fig = px.histogram(
    df_ativos,
    x="score",
    nbins=20,
    color_discrete_sequence=["#1F77B4"],
    labels={"score": "Score", "count": "Quantidade de Deals"},
    title="Distribuicao de Scores do Pipeline"
)
fig.update_layout(
    height=250,         # compacto, nao domina a tela
    margin=dict(l=20, r=20, t=40, b=20),
    showlegend=False,
    xaxis_title="Score",
    yaxis_title="Quantidade"
)

st.plotly_chart(fig, use_container_width=True)
```

**Alternativa recomendada:** usar `px.histogram` com `color` mapeado para a faixa de score (verde/amarelo/laranja/vermelho) para manter consistencia visual com a tabela.

**Grafico opcional para manager/RevOps:** distribuicao por vendedor (box plot) ou por regiao (barra empilhada). Usar `st.tabs()` para nao poluir:

```python
tab_geral, tab_vendedor, tab_regiao = st.tabs([
    "Visao Geral", "Por Vendedor", "Por Regiao"
])
```

### 6.4 Tabela do Pipeline (`components/pipeline_view.py`)

Essa e a tabela central da aplicacao. Deve ser a parte mais polida.

**Opcao A — `st.dataframe` com Styler (recomendada para MVP):**

```python
# Colunas visiveis na tabela
colunas_exibicao = [
    "Score", "Deal", "Conta", "Setor", "Produto",
    "Valor", "Stage", "Dias no Stage", "Vendedor", "Flags"
]

styled_df = (
    df_display[colunas_exibicao]
    .style
    .apply(colorir_por_score, axis=1)
    .format({
        "Valor": "${:,.0f}",
        "Score": "{:.0f}",
        "Dias no Stage": "{:.0f} dias"
    })
)

st.dataframe(
    styled_df,
    use_container_width=True,
    height=500,
    column_config={
        "Score": st.column_config.ProgressColumn(
            "Score",
            min_value=0,
            max_value=100,
            format="%d",
        ),
    }
)
```

**Opcao B — `st.data_editor` com `column_config` (Streamlit 1.23+):**

Permite usar `ProgressColumn` para o score (barra visual inline), `NumberColumn` com formatacao, e melhor performance para datasets grandes.

**Opcao C — HTML customizado via `st.markdown`:**

Maximo controle visual, mas perde interatividade nativa (sort, resize columns). Usar apenas se as opcoes A/B nao atenderem.

**Comportamento da tabela:**

- Ordenada por score descendente (padrao)
- Clicavel — ao selecionar uma linha, popula a secao de detalhe abaixo
- Altura fixa com scroll (500px) para nao empurrar o conteudo
- Colunas com largura ajustavel pelo usuario
- Flag de "Zumbi" como emoji ou badge inline na coluna Flags

### 6.5 Detalhe do Deal (`components/deal_detail.py`)

Acionado quando o usuario seleciona um deal na tabela. Duas opcoes de implementacao:

**Opcao A — `st.expander` abaixo da tabela (recomendada):**

```python
if deal_selecionado:
    with st.expander(f"Detalhe — {deal_selecionado['deal']}", expanded=True):

        col_score, col_info = st.columns([1, 2])

        with col_score:
            # Score visual (gauge ou progress)
            st.subheader(f"Score: {deal['score']}/100")
            st.progress(deal['score'] / 100)

            # Composicao do score
            st.caption("Composicao do Score:")
            componentes = [
                ("Stage", deal['stage_score'], 30),
                ("Valor Esperado", deal['value_score'], 25),
                ("Velocidade", deal['velocity_score'], 25),
                ("Seller-Fit", deal['fit_score'], 10),
                ("Saude da Conta", deal['health_score'], 10),
            ]
            for nome, valor, maximo in componentes:
                st.markdown(f"**{nome}:** {valor:.0f}/{maximo}")
                st.progress(valor / maximo)

        with col_info:
            # Informacoes do deal
            st.markdown(f"""
            **Conta:** {deal['account']} ({deal['sector']})
            **Produto:** {deal['product']} — {deal['value']}
            **Stage:** {deal['stage']} ha {deal['days']} dias
            **Vendedor:** {deal['agent']}
            """)

            st.divider()

            # Explicacao textual
            st.markdown(f"**Por que este score?**")
            st.info(deal['explicacao'])

            # Next Best Action
            st.markdown(f"**Proxima Acao:**")
            st.success(deal['nba'])

            # Flags
            if deal['is_zombie']:
                st.error("Deal Zumbi — parado ha mais que o dobro do tempo normal")
            if deal['conta_recorrente_lost']:
                st.warning(f"Conta com {deal['losses']} deals perdidos anteriormente")
```

**Opcao B — `st.dialog` (Streamlit 1.30+):**

Modal popup — mais limpo visualmente, mas pode ser menos acessivel. Usar se disponivel na versao.

**Componentes do detalhe (obrigatorios):**

1. Score numerico com barra de progresso visual
2. Decomposicao dos 5 componentes com barras individuais
3. Explicacao textual em linguagem simples
4. Next Best Action destacada visualmente (usar `st.success` para acoes positivas, `st.warning` para alertas)
5. Flags (zumbi, conta problematica) com `st.error` / `st.warning`

---

## 7. Responsividade (Desktop-First)

### 7.1 Premissas

- Vendedores usam **desktop** (monitores 1366x768 a 1920x1080)
- Mobile nao e requisito
- Layout `wide` do Streamlit aproveita toda a largura

### 7.2 Breakpoints e Larguras

| Componente       | Largura minima | Comportamento abaixo         |
|------------------|---------------|-------------------------------|
| Area principal   | 800px         | Scroll horizontal na tabela   |
| Sidebar          | 280px         | Padrao do Streamlit           |
| Tabela pipeline  | 750px         | Colunas secundarias ocultam   |
| Metricas (4 col) | 600px         | Stack em 2x2                  |
| Detalhe deal     | 600px         | Colunas empilham              |

### 7.3 Colunas da Tabela por Largura

**Largura >= 1200px (todas as colunas):**
Score, Deal, Conta, Setor, Produto, Valor, Stage, Dias no Stage, Vendedor, Flags

**Largura 800-1200px (remove secundarias):**
Score, Deal, Conta, Produto, Valor, Dias no Stage, Flags

**Largura < 800px (essencial):**
Score, Deal, Valor, Dias no Stage

Na pratica, como Streamlit nao tem media queries nativas, usar `column_order` do `st.dataframe` para definir a ordem de prioridade das colunas. O scroll horizontal cuida do resto.

---

## 8. Performance — Targets e Estrategias

### 8.1 Targets

| Metrica                          | Target     | Justificativa                    |
|----------------------------------|------------|-----------------------------------|
| Tempo de carregamento inicial    | < 3s       | Requisito do PRD                  |
| Tempo de atualizacao de filtro   | < 500ms    | Sensacao de resposta imediata     |
| Renderizacao da tabela           | < 1s       | Critico — e o componente central  |
| Tamanho do dataset em memoria    | < 50MB     | ~8.800 linhas e pequeno           |

### 8.2 Estrategias de Performance

**Carregamento de dados:**

```python
@st.cache_data(ttl=3600)  # cache por 1 hora
def carregar_dados():
    pipeline = pd.read_csv("data/sales_pipeline.csv")
    accounts = pd.read_csv("data/accounts.csv")
    products = pd.read_csv("data/products.csv")
    teams = pd.read_csv("data/sales_teams.csv")
    return pipeline, accounts, products, teams

@st.cache_data
def calcular_scores(pipeline, accounts, products, teams):
    # Todo o scoring calculado uma vez e cacheado
    return df_com_scores
```

- Usar `@st.cache_data` para carregar CSVs e calcular scores (executar uma vez, cachear)
- Nao recalcular scores a cada interacao — scores sao estaticos (dados estaticos)
- Filtros operam sobre o DataFrame ja calculado (operacao rapida em Pandas)

**Renderizacao:**

- `st.dataframe` com `height` fixo (500px) — renderiza apenas linhas visiveis (virtual scrolling nativo)
- Plotly charts com `height` fixo e `margin` reduzida
- Evitar `st.table` (renderiza tudo no DOM) — usar `st.dataframe` (virtualizado)
- Limitar `st.progress` a 5 barras por deal (nao 50)

**Session state:**

```python
# Usar session_state para manter selecao entre reruns
if 'deal_selecionado' not in st.session_state:
    st.session_state.deal_selecionado = None
```

- Filtros em `st.session_state` para persistir entre interacoes
- Nao recarregar dados a cada widget change

---

## 9. Acessibilidade Basica

### 9.1 Requisitos Minimos

O publico e interno (vendedores do time), nao publico geral. Ainda assim, boas praticas basicas:

| Requisito                     | Implementacao                                                |
|-------------------------------|--------------------------------------------------------------|
| Contraste de cores            | Todas as combinacoes fundo/texto com ratio >= 4.5:1 (WCAG AA) |
| Cores nao como unico indicador | Score numerico SEMPRE acompanha a cor (nunca cor sozinha)    |
| Textos de ajuda               | `help` parameter em todos os filtros e metricas              |
| Ordem de tabulacao            | Sidebar primeiro, depois area principal (padrao Streamlit)    |
| Texto alternativo para graficos | `st.caption` abaixo de cada grafico com resumo textual      |

### 9.2 Contraste das Cores de Score

Verificar contraste WCAG AA (ratio >= 4.5:1) para cada combinacao:

| Faixa     | Fundo     | Texto     | Ratio estimado |
|-----------|-----------|-----------|----------------|
| 80-100    | `#DEF7EC` | `#03543F` | ~7.5:1 (OK)   |
| 60-79     | `#FDF6B2` | `#723B13` | ~5.8:1 (OK)   |
| 40-59     | `#FEECDC` | `#9A3412` | ~5.2:1 (OK)   |
| 0-39      | `#FDE8E8` | `#9B1C1C` | ~6.1:1 (OK)   |

### 9.3 Tooltips e Explicacoes

Cada metrica e filtro deve ter um tooltip (`help` parameter) explicando em linguagem simples:

```python
st.metric(
    label="Score Medio",
    value="54",
    help="Media dos scores de prioridade dos deals filtrados. "
         "Quanto maior, mais saudavel o pipeline."
)
```

---

## 10. CSS Customizado

### 10.1 Quando Usar CSS Customizado

O Streamlit tem estilizacao limitada. CSS customizado e necessario para:

1. Ajustar padding/margens do header
2. Estilizar badges de flags (Zumbi, Alerta)
3. Melhorar visual das barras de score na tabela
4. Ocultar elementos padrao do Streamlit que poluem (footer, menu hamburguer)

### 10.2 CSS Base Recomendado

```python
st.markdown("""
<style>
    /* Ocultar menu hamburguer e footer do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Reduzir padding superior (o Streamlit tem muito espaco vazio no topo) */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 1rem;
    }

    /* Estilo para badges de flag */
    .badge-zumbi {
        background-color: #FDE8E8;
        color: #9B1C1C;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }

    .badge-alerta {
        background-color: #FEECDC;
        color: #9A3412;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }

    .badge-saudavel {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }

    /* Card de NBA (Next Best Action) destacado */
    .nba-card {
        background-color: #EFF6FF;
        border-left: 4px solid #1F77B4;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin: 8px 0;
    }

    /* Score grande no detalhe do deal */
    .score-grande {
        font-size: 48px;
        font-weight: 700;
        line-height: 1;
    }

    .score-verde  { color: #059669; }
    .score-amarelo { color: #D97706; }
    .score-laranja { color: #EA580C; }
    .score-vermelho { color: #DC2626; }

    /* Ajuste de tamanho da sidebar */
    [data-testid="stSidebar"] {
        min-width: 280px;
        max-width: 320px;
    }

    /* Metrica customizada — valor mais destacado */
    [data-testid="stMetricValue"] {
        font-size: 28px;
    }

    /* Tabela — linhas com hover */
    .stDataFrame tbody tr:hover {
        background-color: #F3F4F6 !important;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)
```

### 10.3 Helper para Renderizar Badges

```python
def badge_html(texto: str, tipo: str) -> str:
    """Gera HTML de badge para usar em st.markdown."""
    return f'<span class="badge-{tipo}">{texto}</span>'

# Uso:
st.markdown(
    f"Flags: {badge_html('Zumbi', 'zumbi')} {badge_html('Conta Dificil', 'alerta')}",
    unsafe_allow_html=True
)
```

### 10.4 Helper para Score Grande no Detalhe

```python
def score_html(score: int) -> str:
    """Renderiza score grande com cor por faixa."""
    if score >= 75:
        classe = "score-verde"
    elif score >= 50:
        classe = "score-amarelo"
    elif score >= 25:
        classe = "score-laranja"
    else:
        classe = "score-vermelho"
    return f'<span class="score-grande {classe}">{score}</span>'
```

---

## 11. Mapa de Componentes por Arquivo

Resumo de qual arquivo implementa o que:

### `app.py` — Entrada Principal

- `st.set_page_config()`
- CSS customizado (inject via `st.markdown`)
- Carregamento de dados (com cache)
- Calculo de scores (com cache)
- Orquestracao: chama `render_filters()`, `render_metrics()`, `render_pipeline()`, `render_deal_detail()`

### `components/filters.py`

- `render_filters() -> dict` — renderiza sidebar e retorna dicionario de filtros ativos
- Filtros interdependentes (manager filtra vendedores, regiao filtra managers)
- Legenda de cores no final da sidebar

### `components/metrics.py`

- `render_metrics(df_filtrado)` — 4 metricas em colunas
- `render_distribuicao(df_filtrado)` — histograma Plotly de scores
- Metricas reagem ao DataFrame ja filtrado

### `components/pipeline_view.py`

- `render_pipeline(df_filtrado) -> str | None` — tabela estilizada, retorna ID do deal selecionado
- Coloracao por faixa de score
- Ordenacao por score descendente
- Flags inline (badges de zumbi, alerta)

### `components/deal_detail.py`

- `render_deal_detail(deal_data)` — expander com detalhes completos
- Composicao do score com barras visuais
- Explicacao textual em linguagem simples
- Next Best Action destacada
- Flags com `st.error` / `st.warning`

### `utils/formatters.py`

- `formatar_valor(v) -> str` — "$26.768"
- `formatar_percentual(v) -> str` — "63.2%"
- `formatar_dias(d) -> str` — "45 dias"
- `badge_html(texto, tipo) -> str`
- `score_html(score) -> str`
- `cor_por_score(score) -> str` — retorna hex da cor

---

## 12. Checklist de Implementacao

Referencia rapida para validar que todos os aspectos de UI/UX foram cobertos:

### Layout e Estrutura
- [ ] `st.set_page_config` com layout wide, titulo e icone
- [ ] CSS customizado injetado (ocultar menu, ajustar padding, badges)
- [ ] Sidebar com filtros na ordem correta (vendedor > manager > regiao > produto > score > zumbis)
- [ ] Legenda de cores na sidebar
- [ ] Metricas resumo em 4 colunas no topo
- [ ] Grafico de distribuicao de scores
- [ ] Tabela de pipeline como componente central
- [ ] Secao de detalhe do deal (expander)

### Cores e Visual
- [ ] 4 faixas de score com cores consistentes (verde/amarelo/laranja/vermelho)
- [ ] Contraste WCAG AA em todas as combinacoes
- [ ] Badges estilizados para flags (Zumbi, Alerta, Saudavel)
- [ ] Score numerico sempre acompanha a cor (nunca cor sozinha)

### Linguagem
- [ ] Todo o texto em portugues (PT-BR)
- [ ] Linguagem de vendedor, sem jargao tecnico
- [ ] Explicacoes de score em linguagem simples
- [ ] Next Best Action com verbos de acao diretos
- [ ] Tooltips (`help`) em metricas e filtros

### Fluxo do Usuario
- [ ] Estado inicial mostra todos os deals (sem filtro)
- [ ] Mensagem sugerindo selecionar vendedor no primeiro acesso
- [ ] Filtros interdependentes (manager filtra vendedores)
- [ ] Selecao de deal na tabela popula o detalhe
- [ ] Tabela ordenada por score descendente por padrao

### Performance
- [ ] `@st.cache_data` para carregamento de CSVs
- [ ] `@st.cache_data` para calculo de scores
- [ ] `st.dataframe` com altura fixa (virtual scrolling)
- [ ] Carregamento inicial < 3 segundos
- [ ] Atualizacao de filtro < 500ms

### Acessibilidade
- [ ] Tooltips em filtros e metricas
- [ ] Caption descritivo abaixo de graficos
- [ ] Contraste adequado em todas as cores

---

## 13. Testes TDD (test_formatters.py)

Antes de implementar `utils/formatters.py`, escrever os seguintes testes em `tests/test_formatters.py`. Todos devem falhar inicialmente (Red) e passar apos a implementacao (Green).

### 13.1 Testes de formatacao de moeda

```python
def test_formatar_valor_milhoes():
    """1_200_000 -> '$1.2M'."""

def test_formatar_valor_milhares():
    """26_768 -> '$26.8K' ou '$27K'."""

def test_formatar_valor_centenas():
    """550 -> '$550'."""

def test_formatar_valor_dezenas():
    """55 -> '$55'."""

def test_formatar_valor_zero():
    """0 -> '$0'."""
```

### 13.2 Testes de formatacao de percentual

```python
def test_formatar_percentual_normal():
    """0.632 -> '63.2%'."""

def test_formatar_percentual_zero():
    """0.0 -> '0.0%'."""

def test_formatar_percentual_cem():
    """1.0 -> '100.0%'."""
```

### 13.3 Testes de formatacao de dias

```python
def test_formatar_dias_positivo():
    """45 -> '45 dias'."""

def test_formatar_dias_singular():
    """1 -> '1 dia'."""
```

### 13.4 Testes de cor por score

```python
def test_cor_por_score_verde():
    """Score 85 -> '#2ecc71' (verde)."""

def test_cor_por_score_amarelo():
    """Score 65 -> '#f1c40f' (amarelo)."""

def test_cor_por_score_laranja():
    """Score 45 -> '#e67e22' (laranja)."""

def test_cor_por_score_vermelho():
    """Score 20 -> '#e74c3c' (vermelho)."""
```

### 13.5 Testes de badge HTML

```python
def test_badge_html_zumbi():
    """badge_html('Zumbi', 'zumbi') retorna HTML com classe badge-zumbi."""

def test_badge_html_saudavel():
    """badge_html('OK', 'saudavel') retorna HTML com classe badge-saudavel."""

def test_score_html_aplica_cor_correta():
    """score_html(85) retorna HTML com classe score-verde."""
```
