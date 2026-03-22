# Spec Técnica — Pipeline View + Deal Detail

**Componente:** `components/pipeline_view.py` e `components/deal_detail.py`
**Autor:** Victor Almeida
**Data:** 21 de março de 2026
**Status:** Draft
**Referência:** PRD seções 6.1, 6.2, 8

---

## 1. Visão Geral

O Pipeline View é a tela principal da aplicação. Quando o vendedor abre o Lead Scorer na segunda-feira de manhã, esta é a primeira coisa que ele vê: seus deals ativos ordenados por score, com código de cores, explicação do score e recomendação de ação.

Dois componentes trabalham juntos:
- **`pipeline_view.py`** — Tabela principal de deals rankeados + métricas de resumo no topo
- **`deal_detail.py`** — Painel expandido com detalhes, breakdown do score e Next Best Action

---

## 2. Layout da Tela (Wireframe Textual)

```
┌──────────────────────────────────────────────────────────────────────┐
│  HEADER: "Lead Scorer — Pipeline de [Vendedor]"                     │
│  (ou "Pipeline Geral" se nenhum vendedor selecionado)               │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │ Deals Ativos│  │ Valor Total │  │ Score Médio │  │ Deals      │ │
│  │     142     │  │  R$ 1.2M    │  │     58      │  │ Zumbis: 23 │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │
│                                                                      │
│  [SIDEBAR: Filtros — ver filters.py]                                │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  TABELA DE DEALS (ordenada por Score desc)                          │
│  ┌────┬────────────┬──────────┬──────────┬────────┬───────┬──────┐ │
│  │ ## │ Deal       │ Conta    │ Produto  │ Valor  │ Stage │ Dias │ │
│  ├────┼────────────┼──────────┼──────────┼────────┼───────┼──────┤ │
│  │ 85 │ OPP-12345  │ Acme Co  │ GTK 500  │$26.7K  │ Eng.  │  34  │ │
│  │ 72 │ OPP-23456  │ Globex   │ GTXPro   │ $4.8K  │ Eng.  │  52  │ │
│  │ 41 │ OPP-34567  │ Initech  │ MG Adv.  │ $3.3K  │ Prosp.│  18  │ │
│  │ 🧟 │            │          │          │        │       │      │ │
│  │ 15 │ OPP-45678  │ Hottechi │ GTX Bas. │  $550  │ Eng.  │ 210  │ │
│  └────┴────────────┴──────────┴──────────┴────────┴───────┴──────┘ │
│                                                                      │
│  ▼ Expandir deal OPP-12345                                          │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ DEAL DETAIL (deal_detail.py)                                 │   │
│  │                                                              │   │
│  │ Score: 85/100                                                │   │
│  │ ████████████████████░░░░                                     │   │
│  │                                                              │   │
│  │ Breakdown:                                                   │   │
│  │  • Stage (Engaging)          ████████░░  70 → 21.0 pts      │   │
│  │  • Valor Esperado ($26.7K)   █████████░  90 → 22.5 pts      │   │
│  │  • Velocidade (34 dias)      ██████████  100 → 25.0 pts     │   │
│  │  • Seller-Fit (setor Tech)   ████████░░  80 → 8.0 pts       │   │
│  │  • Saúde Conta (Acme Co)     ████████░░  85 → 8.5 pts       │   │
│  │                                                              │   │
│  │ Explicação:                                                  │   │
│  │ "Deal em Engaging há 34 dias — saudável, dentro do          │   │
│  │  esperado. Valor alto (GTK 500, $26.7K). Seu histórico      │   │
│  │  no setor Technology está acima da média do time."           │   │
│  │                                                              │   │
│  │ Próxima Ação:                                                │   │
│  │ "Deal saudável e de alto valor. Prioridade máxima para      │   │
│  │  fechar. Agendar reunião de proposta."                       │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  [Paginação: < 1 2 3 ... 10 >]                                     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. Tabela de Deals

### 3.1 Colunas

| # | Coluna | Campo fonte | Formatação | Largura |
|---|--------|-------------|------------|---------|
| 1 | **Score** | `score` (calculado) | Inteiro 0-100 com badge colorido | Fixa, estreita |
| 2 | **Deal** | `opportunity_id` | String | Média |
| 3 | **Conta** | `account` (join accounts.csv) | Nome da conta. Se `account` null: exibir "Sem conta" em cinza italico | Média |
| 4 | **Produto** | `product` (join products.csv) | Nome do produto | Média |
| 5 | **Valor** | `close_value` ou preço do produto (Prospecting) | Moeda USD abreviada ($26.7K, $4.8K, $550) | Fixa, estreita |
| 6 | **Stage** | `deal_stage` | "Prospecting" ou "Engaging" | Fixa, estreita |
| 7 | **Dias no Stage** | Calculado: `DATA_REF - engage_date` (Engaging). Para Prospecting: exibir "—" (sem dados temporais no dataset) | Inteiro + cor se excessivo, ou "—" | Fixa, estreita |
| 8 | **Vendedor** | `sales_agent` (join sales_teams.csv) | Nome do vendedor | Média |

**Nota sobre DATA_REF:** Sempre `2017-12-31`, a última data do dataset. Todos os cálculos de "dias" usam essa data como "hoje".

### 3.2 Fonte de Dados

Apenas deals com `deal_stage` em `["Prospecting", "Engaging"]`. Deals Won e Lost nao aparecem na tabela principal.

### 3.3 Ordenacao Padrao

Por `score` descendente (maior score no topo = maior prioridade).

### 3.4 Ordenacao Secundaria

Permitir que o usuario clique no cabecalho para reordenar por qualquer coluna. Comportamento nativo do `st.dataframe` com `column_config`.

### 3.5 Paginacao

- **Tamanho da pagina:** 25 deals por pagina
- **Controle:** `st.number_input` ou `st.selectbox` para selecionar pagina
- **Motivo:** Com ~8.800 registros (filtrados para ativos serao menos, mas potencialmente centenas por vendedor), renderizar tudo de uma vez impacta performance. Paginacao mantem a UI responsiva.
- **Alternativa aceitavel:** Usar `st.dataframe` com `height` fixo e scroll nativo do Streamlit, sem paginacao manual. Testar qual abordagem funciona melhor com o volume de dados.

---

## 4. Codigo de Cores

### 4.1 Faixas de Score

| Faixa | Cor | Hex | Significado | Label |
|-------|-----|-----|-------------|-------|
| 80-100 | Verde | `#2ecc71` | Prioridade alta, deal saudavel | "Alta Prioridade" |
| 60-79 | Amarelo | `#f1c40f` | Atencao, deal requer acompanhamento | "Atencao" |
| 40-59 | Laranja | `#e67e22` | Alerta, deal em risco | "Risco" |
| 0-39 | Vermelho | `#e74c3c` | Risco critico, candidato a zumbi | "Critico" |

> **Nota:** Faixas calibradas com a distribuicao real do scoring. Score medio do pipeline ~45-55 (Prospecting ~46, zombies ~35-43, saudaveis ~65-79, melhores ~80-85). Definicao unica em `scoring/constants.py`.

### 4.2 Aplicacao das Cores

**Na coluna Score da tabela:**
- Usar `st.dataframe` com `column_config` e `st.column_config.ProgressColumn` para exibir o score como barra de progresso colorida.
- Alternativa: estilizar via `pandas.Styler` com `background_gradient` ou funcao customizada que aplica cor de fundo na celula do score.

**Na coluna Dias no Stage:**
- Aplicar cor de fundo conforme o ratio de velocidade (decay):
  - ratio <= 1.0: sem cor (saudavel)
  - ratio 1.0-1.5: amarelo claro `#fff3cd`
  - ratio > 1.5: vermelho claro `#f8d7da`
  - ratio > 2.0 (zumbi): vermelho forte `#e74c3c` + texto branco

### 4.3 Flag de Deal Zumbi

Deals com `tempo_no_stage > 2x referencia_stage` recebem:
- Emoji de indicador visual na linha (caveira ou marcador vermelho)
- A linha inteira com fundo vermelho sutil `#fdecea`
- Tag textual "ZUMBI" ao lado do score

Para zumbis criticos (zumbi + valor > P75), usar `#e74c3c` mais intenso e tag "ZUMBI CRITICO".

---

## 5. Score Explanation (Explicacao do Score)

### 5.1 Onde Aparece

A explicacao aparece dentro do **deal detail** (secao 6) quando o usuario expande um deal. NAO aparece na tabela principal para nao poluir a visao geral.

Na tabela principal, o score numerico + cor ja comunicam a prioridade. A explicacao eh o proximo nivel de detalhe.

### 5.2 Formato

A explicacao eh composta por tres blocos:

**Bloco 1: Frase-resumo (sempre presente)**
Uma unica frase em linguagem natural que sintetiza a situacao do deal.

Template:
```
"Score {score} — Deal em {stage} ha {dias} dias ({status_velocidade}).
{comentario_valor}. {comentario_seller_fit}."
```

Exemplos reais:
- "Score 85 — Deal em Engaging ha 34 dias (saudavel). Valor alto (GTK 500, $26.7K). Seu historico no setor Technology esta acima da media do time."
- "Score 38 — Deal em Engaging ha 180 dias (parado). Valor medio (GTXPro, $4.8K). Conta com historico abaixo da media (3 perdas em 5 deals)."
- "Score 12 — Deal em Engaging ha 240 dias (zumbi). Valor baixo (MG Special, $55). Conta Hottechi com 82 deals perdidos — revisar urgentemente."

**Bloco 2: Breakdown numerico (sempre presente)**
Tabela com os 5 componentes do score:

```
Componente           Peso    Score Componente    Contribuicao
Stage (Engaging)     30%     70/100              21.0 pts
Valor Esperado       25%     90/100              22.5 pts
Velocidade           25%     100/100             25.0 pts
Seller-Fit           10%     80/100              8.0 pts
Saude da Conta       10%     85/100              8.5 pts
                                         TOTAL: 85.0 pts
```

**Bloco 3: Next Best Action (sempre presente)**
Uma recomendacao concreta de proxima acao. Ver secao 6.4.

### 5.3 Vocabulario de Status de Velocidade

| Ratio (dias / referencia) | Status | Cor |
|---------------------------|--------|-----|
| <= 1.0 | "saudavel" | Verde |
| 1.0 - 1.2 | "no limite" | Amarelo |
| 1.2 - 1.5 | "parado" | Laranja |
| 1.5 - 2.0 | "em risco" | Vermelho |
| > 2.0 | "zumbi" | Vermelho escuro |

### 5.4 Vocabulario de Valor

| Preco do produto | Label |
|------------------|-------|
| >= $5.000 | "Valor alto" |
| $1.000 - $4.999 | "Valor medio" |
| < $1.000 | "Valor baixo" |

---

## 6. Deal Detail View

### 6.1 Acionamento

O deal detail abre quando o usuario interage com uma linha da tabela. Implementacao via `st.expander` para cada deal, posicionado logo abaixo da tabela, ou usando `st.dataframe` com `on_select` callback (Streamlit >= 1.35).

**Abordagem recomendada:** Usar `st.expander` em loop apos a tabela, um por deal (visivel na pagina atual). O usuario clica para expandir. Motivo: `st.expander` eh nativo, estavel, e funciona bem para este caso. Evitar `st.dialog` (modal) pois bloqueia a visao da tabela.

**Abordagem alternativa:** Usar `st.selectbox` ou `st.radio` acima da tabela para selecionar o deal, e renderizar o detalhe em uma area fixa abaixo. Mais simples, mas menos intuitivo.

### 6.2 Conteudo do Deal Detail

O painel expandido contem (nesta ordem):

#### A) Cabecalho
```
Deal: OPP-12345 | Conta: Acme Co | Produto: GTK 500
Stage: Engaging | Desde: 2017-11-27 (34 dias)
Vendedor: Anna Thompson | Manager: Melvin Marxen | Escritorio: Central
```

#### B) Score com Barra Visual
```
Score: 85 / 100
[████████████████████░░░░]  Alta Prioridade
```

Usar `st.progress` para a barra (convertendo score/100 para float 0-1) com cor condicional via CSS customizado, ou `st.metric` com `delta` para mostrar se o score esta acima/abaixo da media.

#### C) Breakdown do Score (secao 5.2)
Usar `st.dataframe` ou `st.table` com o breakdown de 5 componentes. Cada linha mostra peso, score do componente, e contribuicao em pontos.

Incluir mini-barras visuais por componente (via `st.column_config.ProgressColumn` ou HTML customizado).

#### D) Explicacao Textual (secao 5.2 bloco 1)
Usar `st.info()`, `st.warning()`, ou `st.error()` conforme a faixa do score:
- Score >= 80: `st.success(frase_resumo)`
- Score 60-79: `st.info(frase_resumo)`
- Score 40-59: `st.warning(frase_resumo)`
- Score < 40: `st.error(frase_resumo)`

#### E) Next Best Action
Usar `st.markdown` com destaque visual (bold, emoji de seta ou check) para a recomendacao:
```python
st.markdown(f"**Proxima Acao:** {acao_recomendada}")
```

#### F) Contexto Adicional (se disponivel)
- **Historico da conta:** Win rate, total de deals, deals recentes
- **Performance do vendedor no setor:** Win rate do vendedor vs media do time naquele setor
- **Flags:** Tags visuais para zumbi, conta recorrente lost, etc.

### 6.3 Componentes Streamlit Usados no Deal Detail

| Secao | Componente | Motivo |
|-------|-----------|--------|
| Cabecalho | `st.columns` + `st.markdown` | Layout em colunas para dados basicos |
| Score barra | `st.progress` ou `st.metric` | Visual rapido do score |
| Breakdown | `st.dataframe` com `column_config` | Tabela formatada com barras |
| Explicacao | `st.success/info/warning/error` | Cor automatica por severidade |
| Next Action | `st.markdown` | Flexibilidade de formatacao |
| Historico | `st.expander` aninhado | Detalhe sob demanda, nao polui |

### 6.4 Logica de Next Best Action

Regras avaliadas em ordem de prioridade (a primeira que casar eh usada):

| Prioridade | Condicao | Mensagem |
|------------|----------|----------|
| 1 | Deal zumbi (ratio > 2.0) | "Deal parado ha {dias} dias — {2x}x mais que o esperado. Avaliar se vale manter no pipeline ou marcar como perdido." |
| 2 | Conta com multiplos losses (>= 2 recentes) | "Conta com {n} deals perdidos recentemente. Revisar abordagem antes de investir mais tempo." |
| 3 | Deal em risco (ratio 1.5-2.0) | "Deal em risco — {dias} dias sem avanco. Agendar follow-up urgente ou requalificar." |
| 4 | Deal parado (ratio 1.2-1.5) | "Deal parado ha {dias} dias. Enviar case de sucesso do setor {setor} para reengajar." |
| 5 | Valor alto + Prospecting ha muito tempo | "Conta de alto valor em Prospecting. Envolver manager para acelerar a qualificacao." |
| 6 | Seller WR baixo no setor (< media time) | "Seu historico no setor {setor} esta abaixo da media. Consultar {top_seller} para estrategia." |
| 7 | Engaging + valor alto + tempo OK | "Deal saudavel e de alto valor. Prioridade maxima para fechar. Agendar reuniao de proposta." |
| 8 | Engaging + tempo OK (fallback) | "Deal em andamento saudavel. Manter cadencia de follow-up." |
| 9 | Prospecting (fallback) | "Deal em fase inicial. Qualificar necessidade e agendar primeiro contato." |

---

## 7. Comportamento Padrao ao Abrir (Visao de Segunda-Feira)

### 7.1 Estado Inicial (Nenhum Filtro Aplicado)

Quando o vendedor abre a aplicacao sem selecionar nenhum filtro:

1. **Tabela mostra todos os deals ativos** (Prospecting + Engaging) ordenados por score descendente
2. **Metricas de resumo no topo** mostram totais gerais (todos os vendedores)
3. **Nenhum deal expandido** — tabela limpa para visao geral

### 7.2 Estado Apos Selecionar Vendedor

Quando o vendedor seleciona seu nome no filtro:

1. **Tabela filtra para seus deals apenas**
2. **Metricas atualizam** para refletir somente os deals do vendedor
3. **Titulo atualiza** para "Pipeline de [Nome do Vendedor]"
4. Ordenacao mantem por score descendente

### 7.3 Destaque Inicial

No topo da pagina, antes da tabela, exibir um bloco de "Destaques" que chama atencao imediata:

```python
col1, col2 = st.columns(2)
with col1:
    st.error(f"⚠ {n_zombies} deals zumbis — ${valor_zombies:,.0f} em pipeline inflado")
with col2:
    st.success(f"★ {n_hot} deals de alta prioridade prontos para fechar")
```

Isso responde a pergunta "o que eu faco agora?" antes mesmo de olhar a tabela.

---

## 8. Componentes Streamlit — Mapa de Uso

### 8.1 `pipeline_view.py`

```python
# Estrutura do arquivo

def render_pipeline_view(df_scored: pd.DataFrame, filters: dict) -> None:
    """Renderiza a visao principal do pipeline."""

    # 1. Aplicar filtros ao DataFrame
    df_filtered = apply_filters(df_scored, filters)

    # 2. Metricas de resumo (st.columns + st.metric)
    render_summary_metrics(df_filtered)

    # 3. Destaques (st.error / st.success)
    render_highlights(df_filtered)

    # 4. Tabela principal (st.dataframe)
    render_deals_table(df_filtered)

    # 5. Deal details (st.expander em loop)
    render_deal_expanders(df_filtered)
```

**Componentes usados:**
- `st.columns(4)` — Layout das 4 metricas de resumo
- `st.metric` — Cada metrica individual (deals ativos, valor, score medio, zumbis)
- `st.dataframe` — Tabela principal de deals com `column_config`
- `st.expander` — Um por deal na pagina atual, para abrir o detalhe
- `st.error` / `st.success` — Blocos de destaque no topo

### 8.2 `deal_detail.py`

```python
# Estrutura do arquivo

def render_deal_detail(deal: pd.Series, score_breakdown: dict) -> None:
    """Renderiza o detalhe de um deal dentro de um st.expander."""

    # 1. Cabecalho (st.columns + st.markdown)
    render_deal_header(deal)

    # 2. Score com barra (st.progress ou st.metric)
    render_score_bar(deal.score)

    # 3. Breakdown (st.dataframe com column_config)
    render_score_breakdown(score_breakdown)

    # 4. Explicacao (st.success/info/warning/error)
    render_explanation(deal, score_breakdown)

    # 5. Next Best Action (st.markdown)
    render_next_action(deal, score_breakdown)

    # 6. Contexto adicional (st.expander aninhado)
    render_context(deal)
```

**Componentes usados:**
- `st.columns(3)` — Layout do cabecalho
- `st.markdown` — Textos formatados
- `st.progress` — Barra visual do score
- `st.dataframe` com `ProgressColumn` — Breakdown com mini-barras
- `st.success` / `st.info` / `st.warning` / `st.error` — Explicacao colorida
- `st.expander` (aninhado) — Contexto adicional sob demanda

### 8.3 Column Config da Tabela Principal

```python
column_config = {
    "score": st.column_config.ProgressColumn(
        "Score",
        min_value=0,
        max_value=100,
        format="%d",
    ),
    "opportunity_id": st.column_config.TextColumn("Deal"),
    "account": st.column_config.TextColumn("Conta"),
    "product": st.column_config.TextColumn("Produto"),
    "valor_display": st.column_config.TextColumn("Valor"),
    "deal_stage": st.column_config.TextColumn("Stage"),
    "dias_no_stage": st.column_config.NumberColumn("Dias no Stage", format="%d"),
    "sales_agent": st.column_config.TextColumn("Vendedor"),
}
```

---

## 9. Performance

### 9.1 Metas

- **Tempo de carga inicial:** < 3 segundos (incluindo leitura dos CSVs e calculo de scores)
- **Tempo de interacao (filtro, ordenar, expandir):** < 500ms percebido pelo usuario
- **Memoria:** < 200MB (dados em memoria com Pandas)

### 9.2 Estrategias

| Estrategia | Implementacao | Impacto |
|------------|---------------|---------|
| **Cache de dados** | `@st.cache_data` no `data_loader.py` para leitura dos CSVs | Evita reler CSVs a cada interacao |
| **Cache de scoring** | `@st.cache_data` no `engine.py` para o calculo dos scores | Evita recalcular scores quando so o filtro muda |
| **Filtrar antes de renderizar** | Aplicar filtros no DataFrame antes de passar para `st.dataframe` | Reduz volume de dados renderizados |
| **Paginacao ou scroll fixo** | Limitar a 25 linhas visiveis ou usar `height` fixo no `st.dataframe` | Evita renderizar centenas de linhas de uma vez |
| **Expanders sob demanda** | Criar `st.expander` apenas para deals da pagina atual (25), nao para todos | Evita criar centenas de componentes Streamlit |
| **Pre-computar colunas derivadas** | Calcular `dias_no_stage`, `valor_display`, `status_velocidade` uma vez no DataFrame | Evita recalculos em cada render |
| **Evitar Styler em tabelas grandes** | `pandas.Styler` eh lento para muitas linhas. Preferir `column_config` nativo do Streamlit | Rendering mais rapido |

### 9.3 Volume Esperado

- Total de registros no sales_pipeline.csv: ~8.800
- Deals ativos (Prospecting + Engaging): estimado ~1.500-2.500
- Deals por vendedor: ~40-70 ativos em media
- Apos filtro por vendedor: tabela de 40-70 linhas (leve)
- Sem filtro (visao geral): tabela de ~2.000 linhas (precisa paginacao ou scroll)

---

## 10. Decisoes de Design e Tradeoffs

### 10.1 `st.dataframe` vs `st.table` vs HTML customizado

**Decisao:** Usar `st.dataframe` com `column_config`.

**Motivo:** `st.dataframe` eh interativo (sort, scroll, resize colunas), suporta `ProgressColumn` para barras de score, e tem boa performance com ate milhares de linhas. `st.table` eh estatico e sem interacao. HTML customizado daria mais controle visual mas adicionaria complexidade desnecessaria.

**Tradeoff:** `st.dataframe` nao suporta cores de fundo customizadas por celula de forma nativa via `column_config` (apenas `ProgressColumn` com gradiente). Para cores totalmente customizadas na coluna de score, seria necessario usar `pandas.Styler`, que eh mais lento. A `ProgressColumn` com gradiente eh um compromisso aceitavel.

### 10.2 `st.expander` vs modal vs pagina separada

**Decisao:** Usar `st.expander` inline para deal detail.

**Motivo:** Mantem o contexto da tabela visivel. O vendedor pode abrir um deal, ler, fechar, e abrir outro sem navegar. Modais bloqueiam a visao. Paginas separadas perdem contexto.

**Tradeoff:** Com muitos expanders (um por deal na pagina), pode haver lentidao se a pagina mostrar muitos deals. Mitigacao: paginacao de 25 deals limita a 25 expanders.

### 10.3 Paginacao manual vs scroll nativo

**Decisao:** Comecar com scroll nativo do `st.dataframe` (height fixo). Se a performance for ruim, implementar paginacao manual.

**Motivo:** `st.dataframe` com `height=600` renderiza de forma virtualizada (somente linhas visiveis no viewport). Isso pode ser suficiente para ate ~2.000 linhas sem paginacao manual.

**Tradeoff:** Paginacao manual daria mais controle sobre quais `st.expander` criar, mas adiciona complexidade de UI (controles de pagina, estado).

---

## 11. Contrato de Dados

### 11.1 Input para `pipeline_view.py`

O componente recebe um `pd.DataFrame` ja com scores calculados (output do `scoring/engine.py`) e um dict de filtros (output do `components/filters.py`).

**Colunas esperadas no DataFrame:**

| Coluna | Tipo | Origem |
|--------|------|--------|
| `opportunity_id` | str | sales_pipeline.csv |
| `sales_agent` | str | sales_pipeline.csv |
| `account` | str | sales_pipeline.csv |
| `product` | str | sales_pipeline.csv |
| `deal_stage` | str | sales_pipeline.csv (filtrado: Prospecting/Engaging) |
| `close_value` | float | sales_pipeline.csv (ou preco produto se Prospecting) |
| `engage_date` | datetime | sales_pipeline.csv |
| ~~`created_date`~~ | ~~datetime~~ | **REMOVIDO — campo nao existe no dataset** |
| `score` | float | scoring/engine.py |
| `score_stage` | float | scoring/engine.py |
| `score_value` | float | scoring/engine.py |
| `score_velocity` | float | scoring/engine.py |
| `score_seller_fit` | float | scoring/engine.py |
| `score_account_health` | float | scoring/engine.py |
| `dias_no_stage` | int | calculado |
| `is_zombie` | bool | scoring/engine.py |
| `is_critical_zombie` | bool | scoring/engine.py |
| `velocity_status` | str | scoring/velocity.py |
| `sector` | str | join com accounts.csv |
| `revenue` | float | join com accounts.csv |
| `manager` | str | join com sales_teams.csv |
| `regional_office` | str | join com sales_teams.csv |
| `sales_price` | float | join com products.csv (coluna `sales_price` do products.csv) |
| `next_action` | str | scoring/engine.py |
| `explanation` | str | scoring/engine.py |

### 11.2 Input para `deal_detail.py`

Uma `pd.Series` (uma linha do DataFrame acima) + um dict de breakdown:

```python
score_breakdown = {
    "stage": {"weight": 0.30, "raw_score": 70, "weighted": 21.0, "label": "Engaging"},
    "value": {"weight": 0.25, "raw_score": 90, "weighted": 22.5, "label": "$26.7K"},
    "velocity": {"weight": 0.25, "raw_score": 100, "weighted": 25.0, "label": "34 dias (saudavel)"},
    "seller_fit": {"weight": 0.10, "raw_score": 80, "weighted": 8.0, "label": "WR 72% no setor Tech"},
    "account_health": {"weight": 0.10, "raw_score": 85, "weighted": 8.5, "label": "Acme Co (WR 78%)"},
}
```

---

## 12. Testes Manuais (Checklist)

Antes de considerar o componente pronto, verificar:

- [ ] Tabela carrega com todos os deals ativos (Prospecting + Engaging)
- [ ] Deals Won/Lost NAO aparecem na tabela
- [ ] Ordenacao padrao eh por score descendente
- [ ] Clicar no cabecalho de coluna reordena a tabela
- [ ] Scores aparecem com cor correta (verde/amarelo/laranja/vermelho)
- [ ] Deals zumbi tem flag visual (cor de fundo / tag)
- [ ] Expandir deal mostra cabecalho completo
- [ ] Breakdown de score soma corretamente para o score total
- [ ] Explicacao textual usa linguagem simples (sem jargao)
- [ ] Next Best Action eh contextual (muda conforme o deal)
- [ ] Filtro por vendedor filtra corretamente e atualiza metricas
- [ ] Metricas de resumo refletem os deals filtrados
- [ ] Performance: pagina carrega em < 3 segundos
- [ ] Nenhum erro no console ao navegar entre deals
- [ ] Valores monetarios formatados corretamente ($26.7K, nao 26768.0)
- [ ] Dias no stage calculados a partir de 2017-12-31 (DATA_REF)

---

## 13. Testes TDD (test_pipeline_view.py)

Antes de implementar `pipeline_view.py` e `deal_detail.py`, escrever os seguintes testes em `tests/test_pipeline_view.py`. Todos devem falhar inicialmente (Red) e passar apos a implementacao (Green).

### 13.1 Testes de dados da tabela

```python
def test_pipeline_view_only_active_deals():
    """Tabela contem apenas deals Prospecting e Engaging (nao Won/Lost)."""

def test_pipeline_view_sorted_by_score_desc():
    """Deals ordenados por score descendente por padrao."""

def test_pipeline_view_has_expected_columns():
    """Tabela tem colunas: Score, Deal, Conta, Produto, Valor, Stage, Dias no Stage, Vendedor."""

def test_pipeline_view_displays_sem_conta_when_null():
    """Quando account e null, exibir 'Sem conta'."""

def test_pipeline_view_value_uses_proxy_for_active():
    """Valor exibido usa sales_price como proxy para deals ativos (sem close_value)."""

def test_pipeline_view_days_dash_for_prospecting():
    """Dias no Stage mostra '—' para deals Prospecting (sem engage_date)."""
```

### 13.2 Testes de codigo de cores

```python
def test_score_color_green_for_80_plus():
    """Score >= 80 retorna cor verde (#2ecc71)."""

def test_score_color_yellow_for_60_to_79():
    """Score 60-79 retorna cor amarela (#f1c40f)."""

def test_score_color_orange_for_40_to_59():
    """Score 40-59 retorna cor laranja (#e67e22)."""

def test_score_color_red_for_below_40():
    """Score < 40 retorna cor vermelha (#e74c3c)."""
```

### 13.3 Testes do deal detail

```python
def test_deal_detail_score_breakdown_sums_to_total():
    """Soma dos componentes ponderados = score total (tolerancia 0.1)."""

def test_deal_detail_has_explanation_text():
    """Deal detail inclui texto de explicacao nao-vazio."""

def test_deal_detail_has_next_action():
    """Deal detail inclui next best action nao-vazia."""

def test_deal_detail_zombie_flag_shown_when_zombie():
    """Deal zumbi mostra flag visual de alerta."""
```

### 13.4 Testes de formatacao

```python
def test_format_value_abbreviation():
    """26768 -> '$26.7K', 550 -> '$550', 55 -> '$55'."""

def test_velocity_status_vocabulary():
    """Ratio <= 1.0 -> 'saudavel', 1.0-1.2 -> 'no limite', > 2.0 -> 'zumbi'."""
```
