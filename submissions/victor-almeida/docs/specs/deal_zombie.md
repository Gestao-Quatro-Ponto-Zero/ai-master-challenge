# Spec Tecnica: Sistema de Deteccao de Deal Zumbi

**Modulo:** `scoring/deal_zombie.py`
**Autor:** Victor Almeida
**Data:** 21 de marco de 2026
**Status:** Especificacao

---

## 1. Contexto e Motivacao

O pipeline do CRM esta massivamente inflado. Dos 1.589 deals ativos em Engaging:

- Mediana de **165 dias** no stage (referencia Won: 57 dias)
- **96.7%** ja passaram da mediana de velocidade dos deals Won
- **88.3%** estao acima do **dobro** da mediana

Isso significa que a maioria dos deals ativos ja deveria ter sido fechada (won ou lost) ha muito tempo. Sem uma classificacao explicita, esses deals inflam o forecast e consomem atencao do vendedor sem retorno.

O sistema de Deal Zumbi existe para **tornar visivel o que o pipeline esconde**: deals que ainda aparecem como "ativos" mas cujo comportamento temporal indica probabilidade minima de fechamento.

---

## 2. Definicoes

| Termo | Definicao |
|-------|-----------|
| **Deal Zumbi** | Deal ativo cujo tempo no stage atual excede 2x a referencia do stage. Aparenta estar vivo no pipeline, mas comportamento temporal indica que esta morto. |
| **Deal Zumbi Critico** | Deal Zumbi cujo valor estimado esta acima do percentil 75. Infla significativamente o forecast. |
| **Conta Recorrente Lost** | Conta com 2 ou mais deals fechados como Lost. Indica padrao problematico na relacao comercial. |
| **Referencia do stage** | Benchmark temporal calibrado com dados reais de deals Won. Ponto a partir do qual o tempo no stage comeca a ser atipico. |
| **Pipeline inflado** | Soma dos valores estimados de todos os deals classificados como Zumbi. Representa valor que aparece no forecast mas tem probabilidade minima de se concretizar. |

---

## 3. Criterios de Classificacao

### 3.1 Deal Zumbi

Um deal e classificado como **Zumbi** quando TODAS as condicoes abaixo sao verdadeiras:

```
deal_stage == 'Engaging'                       # deal ativo COM data disponivel
E tempo_no_stage > 2 * referencia_stage        # tempo excede o dobro da referencia (176 dias)
```

> **NOTA:** Deals em Prospecting NAO podem ser classificados como Zumbi porque nao possuem nenhuma data no dataset (`engage_date` e null, e nao existe campo `created_date`). Apenas Engaging tem dados temporais.

### 3.2 Deal Zumbi Critico

Um deal e classificado como **Zumbi Critico** quando:

```
is_zombie == True
E valor_estimado > percentil_75_valor           # valor alto inflando forecast
```

### 3.3 Conta Recorrente Lost

Uma conta recebe a flag **Conta Recorrente Lost** quando:

```
total_deals_lost >= 2
```

Essa flag e independente do status de Zumbi, mas agrava a avaliacao. Um deal Zumbi em uma Conta Recorrente Lost e o cenario de maior risco.

---

## 4. Thresholds Numericos

### 4.1 Referencias Temporais por Stage

Calculadas a partir dos deals Won do dataset:

| Stage | Referencia (dias) | Fonte | Justificativa |
|-------|-------------------|-------|---------------|
| **Engaging** | **88** | P75 dos deals Won (Engaging -> Close) | Mediana e 57 dias, mas deals de 90-150 dias tem WR mais alta (70-75%). Usar P75 evita penalizar deals que ainda tem boa chance. |
| **Prospecting** | **N/A** | O dataset NAO possui `created_date` nem qualquer data para deals em Prospecting. | Deals em Prospecting nao podem ser classificados como Zumbi — tratar como "sem dados temporais". |

### 4.2 Threshold de Zumbi por Stage

| Stage | Referencia | Threshold Zumbi (2x) | Deals ativos acima do threshold |
|-------|------------|----------------------|-------------------------------|
| Engaging | 88 dias | **176 dias** | **46.9%** dos 1.589 deals ativos (745 deals). Nota: 88.3% esta acima de 2x a *mediana* (114d), nao 2x o P75. |
| Prospecting | **N/A** | **N/A** | Prospecting NAO tem datas no dataset (sem `engage_date`, sem `created_date`). Impossivel classificar como Zumbi. |

### 4.3 Threshold de Valor para Zumbi Critico

O percentil 75 de valor e calculado sobre **todos os deals ativos** usando o valor estimado:

- Para deals em **Engaging** sem `close_value`: usar preco de lista do produto como proxy
- Para deals em **Prospecting** sem `close_value`: usar preco de lista do produto como proxy
- Para deals Won: `close_value` real

O P75 e recalculado no carregamento dos dados. Com base nos precos dos produtos:

| Produto | Preco |
|---------|-------|
| GTK 500 | $26.768 |
| GTX Plus Pro | $5.482 |
| GTXPro | $4.821 |
| MG Advanced | $3.393 |
| GTX Plus Basic | $1.096 |
| GTX Basic | $550 |
| MG Special | $55 |

O P75 vai depender da distribuicao de produtos nos deals ativos, mas espera-se algo na faixa de **$4.000-$5.500**.

### 4.4 Threshold de Conta Recorrente Lost

| Condicao | Threshold | Justificativa |
|----------|-----------|---------------|
| Conta Recorrente Lost | >= 2 losses | Padrao minimo para indicar problema recorrente |
| Conta de Alto Risco | >= 5 losses | Top contas: Hottechi (82), Kan-code (72), Konex (63) |

---

## 5. Problema de Calibracao

### O pipeline esta tao inflado que "quase tudo e zumbi"

Este e o maior desafio tecnico do modulo. Com 88.3% dos deals em Engaging acima do dobro da mediana dos Won, o threshold padrao de 2x classifica a grande maioria como Zumbi. Isso reduz a utilidade da classificacao -- se tudo e zumbi, nada e zumbi.

### Estrategia de calibracao adotada

**Usar P75 (88 dias) como referencia em vez da mediana (57 dias).** Isso muda o threshold de Zumbi para 176 dias em vez de 114 dias. Com P75, **46.9% dos deals Engaging** sao classificados como Zumbi (745 de 1.589) — um numero acionavel. Com a mediana, seriam 88.3% — perde utilidade.

**NOTA:** Apenas deals em **Engaging** podem ser classificados como Zumbi, pois Prospecting nao tem datas no dataset. Os 500 deals em Prospecting ficam sem classificacao temporal.

A utilidade da classificacao nao esta em separar "poucos zumbis dos muitos saudaveis", mas em:

1. **Quantificar o problema:** mostrar ao manager o tamanho do pipeline inflado
2. **Destacar os Zumbis Criticos:** dos muitos zumbis, quais sao de alto valor e mais distorcem o forecast
3. **Cruzar com Conta Recorrente Lost:** zumbis em contas problematicas sao os primeiros candidatos a limpeza
4. **Ranquear por gravidade:** um deal a 3x da referencia e pior que um a 2.1x

### Faixas de gravidade

| Faixa | Ratio (tempo/referencia) | Label | Cor |
|-------|--------------------------|-------|-----|
| Saudavel | <= 1.0 | -- | Verde |
| Atencao | 1.0 - 1.5 | -- | Amarelo |
| Alerta | 1.5 - 2.0 | -- | Laranja |
| **Zumbi** | 2.0 - 3.0 | "Zumbi" | Vermelho |
| **Zumbi Cronico** | > 3.0 | "Zumbi Cronico" | Vermelho escuro |

Zumbi Critico e ortogonal a essas faixas -- depende do valor, nao do tempo.

---

## 6. Calculo do Valor de Pipeline Inflado

### Definicao

```
pipeline_inflado = SUM(valor_estimado) para todos os deals onde is_zombie == True
```

### Calculo do valor estimado por deal

| Situacao | Valor estimado |
|----------|----------------|
| Deal com `close_value` preenchido | `close_value` |
| Deal em Engaging sem `close_value` | Preco de lista do produto associado |
| Deal em Prospecting sem `close_value` | Preco de lista do produto associado |

### Metricas derivadas

```python
# Pipeline total ativo
pipeline_total = sum(valor_estimado para deals ativos)

# Pipeline inflado (zumbis)
pipeline_inflado = sum(valor_estimado para deals zumbis)

# Percentual inflado
pct_inflado = pipeline_inflado / pipeline_total * 100

# Pipeline inflado critico (zumbis criticos)
pipeline_inflado_critico = sum(valor_estimado para deals zumbis criticos)
```

---

## 7. Identificacao de Contas com Padrao Recorrente de Losses

### Calculo

```python
# Para cada conta no dataset:
conta_losses = count(deals WHERE deal_stage == 'Lost' AND account == conta)
conta_total_fechados = count(deals WHERE deal_stage IN ('Won', 'Lost') AND account == conta)
conta_loss_rate = conta_losses / conta_total_fechados  # se total > 0

# Flags
is_recurrent_loss = conta_losses >= 2
is_high_risk_account = conta_losses >= 5
```

### Dados de referencia

As 85 contas do dataset tem 3+ losses cada. As piores:

| Conta | Losses | Win Rate Conta |
|-------|--------|----------------|
| Hottechi | 82 | A calcular |
| Kan-code | 72 | A calcular |
| Konex | 63 | A calcular |

### Cruzamento com Deal Zumbi

Quando um deal Zumbi esta em uma Conta Recorrente Lost, a explicacao textual deve incluir ambas as informacoes:

> "Deal Zumbi: parado ha 210 dias (referencia: 88 dias). Conta com 15 deals perdidos historicamente. Risco muito alto."

---

## 8. Interface do Modulo

### 8.1 Arquivo: `scoring/deal_zombie.py`

### 8.2 Constantes

```python
# Referencia temporal por stage (em dias)
ENGAGING_REFERENCE_DAYS = 88        # P75 dos deals Won
# PROSPECTING_REFERENCE_DAYS calculado dinamicamente

# Multiplicador para threshold de Zumbi
ZOMBIE_THRESHOLD_MULTIPLIER = 2.0

# Threshold minimo de losses para Conta Recorrente Lost
RECURRENT_LOSS_THRESHOLD = 2

# Threshold de alto risco para contas
HIGH_RISK_LOSS_THRESHOLD = 5

# Data de referencia ("hoje")
REFERENCE_DATE = pd.Timestamp('2017-12-31')
```

### 8.3 Funcoes Publicas

#### `classify_zombies(deals_df, products_df, reference_date) -> pd.DataFrame`

Funcao principal. Recebe o DataFrame de deals ativos e retorna o mesmo DataFrame com colunas adicionais de classificacao.

**Inputs:**
| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| `deals_df` | `pd.DataFrame` | DataFrame com deals ativos (Engaging — Prospecting sera ignorado por falta de datas). Deve conter: `opportunity_id`, `deal_stage`, `engage_date`, `product`, `close_value`, `account` |
| `products_df` | `pd.DataFrame` | DataFrame de produtos. Deve conter: `product`, `sales_price` |
| `reference_date` | `pd.Timestamp` | Data de referencia para calculo de tempo. Default: `2017-12-31` |

**Output:** `pd.DataFrame` -- o `deals_df` original acrescido das colunas:

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| `days_in_stage` | `int` | Dias no stage atual ate `reference_date` |
| `stage_reference_days` | `int` | Referencia temporal do stage (88 para Engaging) |
| `time_ratio` | `float` | `days_in_stage / stage_reference_days` |
| `is_zombie` | `bool` | `True` se `time_ratio > 2.0` |
| `zombie_severity` | `str` | `None`, `'zombie'`, ou `'zombie_chronic'` (> 3.0) |
| `estimated_value` | `float` | Valor estimado do deal (close_value ou preco produto) |
| `is_zombie_critical` | `bool` | `True` se Zumbi + valor > P75 |
| `zombie_label` | `str` | Label para UI: `None`, `'Zumbi'`, `'Zumbi Critico'` |

#### `classify_accounts(pipeline_df) -> pd.DataFrame`

Calcula metricas de saude por conta baseado em historico de wins/losses.

**Inputs:**
| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| `pipeline_df` | `pd.DataFrame` | DataFrame completo do pipeline (incluindo Won e Lost). Deve conter: `account`, `deal_stage` |

**Output:** `pd.DataFrame` com uma linha por conta:

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| `account` | `str` | Nome da conta |
| `total_deals` | `int` | Total de deals historicos |
| `total_won` | `int` | Total de deals Won |
| `total_lost` | `int` | Total de deals Lost |
| `win_rate` | `float` | Win rate da conta (Won / fechados) |
| `is_recurrent_loss` | `bool` | `True` se `total_lost >= 2` |
| `is_high_risk` | `bool` | `True` se `total_lost >= 5` |

#### ~~`calculate_prospecting_reference(pipeline_df) -> int`~~ **REMOVIDA**

**Motivo:** O dataset NAO possui campo `created_date`. Deals em Prospecting nao tem nenhuma data disponivel, tornando impossivel calcular uma referencia temporal. Deals em Prospecting nao sao classificados como Zumbi.

#### `get_zombie_summary(classified_df) -> dict`

Gera metricas de resumo sobre deals zumbis para uso na UI.

**Inputs:**
| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| `classified_df` | `pd.DataFrame` | DataFrame retornado por `classify_zombies()` |

**Output:** `dict` com as seguintes chaves:

```python
{
    "total_active_deals": int,          # Total de deals ativos
    "total_zombies": int,               # Total de deals Zumbi
    "total_zombies_critical": int,      # Total de deals Zumbi Critico
    "total_zombies_chronic": int,       # Total de Zumbis Cronicos (> 3x)
    "pct_zombies": float,              # Percentual de zumbis no pipeline
    "pipeline_total": float,            # Valor total do pipeline ativo
    "pipeline_inflated": float,         # Valor somado dos zumbis
    "pipeline_inflated_critical": float,# Valor somado dos zumbis criticos
    "pct_pipeline_inflated": float,     # % do pipeline que e inflado
    "zombies_by_stage": dict,           # {"Engaging": n, "Prospecting": n}
    "top_zombie_accounts": list,        # Top 10 contas com mais deals zumbis
}
```

#### `get_zombie_summary_by_seller(classified_df, sales_teams_df) -> pd.DataFrame`

Gera metricas de resumo agrupadas por vendedor para visao de manager.

**Inputs:**
| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| `classified_df` | `pd.DataFrame` | DataFrame retornado por `classify_zombies()` |
| `sales_teams_df` | `pd.DataFrame` | DataFrame de vendedores com manager e regional_office |

**Output:** `pd.DataFrame` com uma linha por vendedor:

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| `sales_agent` | `str` | Nome do vendedor |
| `manager` | `str` | Manager do vendedor |
| `regional_office` | `str` | Escritorio regional |
| `total_active` | `int` | Total de deals ativos |
| `total_zombies` | `int` | Total de zumbis |
| `total_zombies_critical` | `int` | Total de zumbis criticos |
| `pct_zombies` | `float` | % de zumbis nos deals do vendedor |
| `pipeline_value` | `float` | Valor total do pipeline do vendedor |
| `inflated_value` | `float` | Valor inflado (zumbis) |

---

## 9. Representacao na UI

### 9.1 Tags Visuais

Cada deal no Pipeline View recebe uma tag baseada na classificacao:

| Classificacao | Tag | Cor de fundo | Cor do texto |
|---------------|-----|-------------|-------------|
| Saudavel | -- | -- | -- |
| Zumbi | `Zumbi` | `#FF4444` (vermelho) | Branco |
| Zumbi Critico | `Zumbi Critico` | `#CC0000` (vermelho escuro) | Branco |
| Zumbi Cronico | `Zumbi Cronico` | `#880000` (vermelho muito escuro) | Branco |
| Conta Recorrente Lost | `Conta Problematica` | `#FF8800` (laranja) | Branco |

Quando um deal e Zumbi E esta em Conta Recorrente Lost, ambas as tags aparecem.

### 9.2 Filtro "Mostrar Deal Zumbis"

No painel de filtros (`components/filters.py`), incluir:

- **Toggle "Mostrar apenas Deal Zumbis"** -- filtra a tabela para so exibir zumbis
- **Dropdown "Classificacao"** com opcoes: Todos, Saudaveis, Zumbis, Zumbis Criticos
- O filtro e combinavel com os outros filtros (vendedor, manager, regiao, produto)

### 9.3 Card de Resumo

Na area de metricas (`components/metrics.py`), exibir um card de resumo:

```
+----------------------------------------------------------+
|  DEALS ZUMBI                                             |
|                                                          |
|  X deals zumbis representando $Y em pipeline inflado     |
|  (Z% do pipeline total)                                  |
|                                                          |
|  Zumbis Criticos: N deals ($W)                           |
|  Contas problematicas: M contas                          |
+----------------------------------------------------------+
```

**Linguagem para o vendedor (simples, sem jargao):**

- "X deals parados ha muito tempo e com chance minima de fechar"
- "Esses deals somam $Y no seu pipeline, mas provavelmente nao vao converter"
- "Recomendacao: revise esses deals com seu manager e limpe o pipeline"

### 9.4 Explicacao no Detalhe do Deal

No componente de detalhe (`components/deal_detail.py`), quando o deal e Zumbi, exibir:

```
ALERTA: Deal Zumbi
Esse deal esta parado em Engaging ha 210 dias.
A referencia para deals que fecham e 88 dias.
Tempo excedido: 2.4x a referencia.

[Se Conta Recorrente Lost]
Agravante: a conta Hottechi ja teve 82 deals perdidos.

Acao sugerida: Revise com seu manager. Considere marcar como Lost
para limpar o pipeline e focar em oportunidades com mais chance.
```

### 9.5 Visao de Manager

Para managers, exibir tabela de resumo por vendedor:

```
| Vendedor | Deals Ativos | Zumbis | % Zumbi | Pipeline Inflado |
|----------|-------------|--------|---------|-----------------|
| Agent A  | 77          | 62     | 80.5%   | $234,567        |
| Agent B  | 45          | 31     | 68.9%   | $156,789        |
| ...      |             |        |         |                 |
```

Ordenado por `Pipeline Inflado` descendente -- mostra onde esta o maior problema.

---

## 10. Integracao com o Score Composto

O Deal Zumbi **nao e um componente do score** -- e uma flag independente. Porem, o status de Zumbi afeta o score indiretamente via componente de **Velocidade** (peso 25%):

```
# No modulo velocity.py:
ratio = dias_no_stage / referencia_stage

if ratio > 2.0:   decay = 0.10    # Zumbi: score de velocidade quase zero
if ratio > 1.5:   decay = 0.30    # Pre-zumbi
```

Ou seja, deals Zumbi automaticamente tem score de velocidade muito baixo (decay de 0.10), o que puxa o score composto para baixo. A flag de Zumbi e uma **camada adicional de comunicacao** -- torna explicito o que o score numerico ja indica.

### Relacao score vs flag

| Score Composto | Flag Zumbi | Interpretacao |
|---------------|-----------|---------------|
| Alto (70+) | Nao | Deal saudavel e prioritario |
| Medio (40-70) | Nao | Deal que precisa de atencao |
| Baixo (< 40) | Nao | Deal com problemas (valor baixo, setor ruim, etc) |
| Baixo (< 40) | Sim | Deal morto -- revisar ou descartar |
| Medio (40-70) | Sim | **Caso raro** -- possivel se valor muito alto compensa o decay. Zumbi Critico provavel. Merece atencao do manager. |

---

## 11. Logica de Calculo Detalhada

### 11.1 Dias no stage

```python
def calculate_days_in_stage(deal, reference_date):
    if deal['deal_stage'] == 'Engaging':
        # Engaging: tempo desde engage_date
        stage_start = pd.to_datetime(deal['engage_date'])
        return (reference_date - stage_start).days
    elif deal['deal_stage'] == 'Prospecting':
        # NOTA: Prospecting NAO tem nenhuma data no dataset.
        # Impossivel calcular dias no stage.
        return None
    else:
        return None  # Won/Lost nao se aplica
```

### 11.2 Referencia por stage

```python
def get_stage_reference(stage, pipeline_df):
    if stage == 'Engaging':
        return ENGAGING_REFERENCE_DAYS  # 88 dias (P75 Won)

    elif stage == 'Prospecting':
        # NOTA: O dataset NAO possui campo `created_date`.
        # Deals em Prospecting nao tem nenhuma data disponivel.
        # Impossivel calcular referencia temporal.
        return None  # Prospecting nao pode ser classificado como Zumbi
```

### 11.3 Valor estimado

```python
def estimate_deal_value(deal, products_df):
    if pd.notna(deal['close_value']) and deal['close_value'] > 0:
        return deal['close_value']

    # Sem close_value: usar preco de lista do produto
    product_price = products_df.loc[
        products_df['product'] == deal['product'], 'sales_price'
    ]
    if not product_price.empty:
        return product_price.iloc[0]

    return 0.0  # fallback
```

### 11.4 Classificacao completa

```python
def classify_single_deal(deal, stage_reference, value_p75):
    time_ratio = deal['days_in_stage'] / stage_reference

    is_zombie = time_ratio > ZOMBIE_THRESHOLD_MULTIPLIER
    is_chronic = time_ratio > 3.0
    is_critical = is_zombie and deal['estimated_value'] > value_p75

    if is_critical:
        label = 'Zumbi Critico'
    elif is_chronic:
        label = 'Zumbi Cronico'
    elif is_zombie:
        label = 'Zumbi'
    else:
        label = None

    severity = None
    if is_chronic:
        severity = 'zombie_chronic'
    elif is_zombie:
        severity = 'zombie'

    return {
        'time_ratio': round(time_ratio, 2),
        'is_zombie': is_zombie,
        'is_zombie_critical': is_critical,
        'zombie_severity': severity,
        'zombie_label': label,
    }
```

**Nota sobre precedencia de labels:** Um deal pode ser Zumbi Cronico (tempo > 3x) e Zumbi Critico (valor > P75) simultaneamente. Nesse caso, o label prioritario e **Zumbi Critico**, porque o impacto no forecast e a informacao mais acionavel para o manager. A severidade temporal fica registrada em `zombie_severity`.

---

## 12. Metricas de Resumo para Managers

### 12.1 Dashboard de Saude do Pipeline

| Metrica | Descricao | Objetivo |
|---------|-----------|----------|
| **Total Zumbis** | Contagem de deals classificados como Zumbi | Dimensionar o problema |
| **% Pipeline Inflado** | Valor dos zumbis / valor total pipeline | Mostrar distorcao do forecast |
| **Pipeline Inflado ($)** | Soma dos valores dos deals zumbis | Quantificar o risco financeiro |
| **Zumbis Criticos** | Contagem e valor de zumbis de alto valor | Priorizar revisao |
| **Top Contas Problematicas** | Contas com mais zumbis + historico de losses | Decidir se vale manter a conta |
| **Zumbis por Vendedor** | Distribuicao de zumbis por vendedor | Identificar quem precisa de coaching |
| **Zumbis por Manager** | Agregacao por manager | Visao de lideranca |
| **Zumbis por Regiao** | Agregacao por regional_office | Identificar padroes regionais |

### 12.2 Perguntas que o manager deve conseguir responder

1. **"Quanto do meu forecast e real?"** -- % pipeline inflado mostra isso diretamente
2. **"Quais deals devo pedir pro vendedor descartar?"** -- filtro Zumbi Critico, ordenado por valor
3. **"Quais vendedores estao com pipeline mais sujo?"** -- tabela zumbis por vendedor
4. **"Quais contas estao nos custando tempo?"** -- contas com mais zumbis + historico loss
5. **"Se eu limpar os zumbis, como fica o pipeline real?"** -- pipeline total - pipeline inflado

### 12.3 Alertas sugeridos

```
# Para o manager na visao de equipe:
"Seu time tem X deals zumbis que somam $Y em pipeline inflado.
Os 3 vendedores com mais deals parados sao: [A], [B], [C].
Recomendacao: agendar revisao de pipeline com cada um."

# Para o vendedor na visao individual:
"Voce tem X deals parados ha mais de [threshold] dias.
Esses deals somam $Y, mas a chance de fechar e muito baixa.
Revise com seu manager quais manter e quais marcar como Lost."
```

---

## 13. Testes e Validacao

### Cenarios de teste

| Cenario | Input | Resultado esperado |
|---------|-------|--------------------|
| Deal Engaging com 100 dias | stage=Engaging, days=100 | ratio=1.14, **nao** e Zumbi |
| Deal Engaging com 180 dias | stage=Engaging, days=180 | ratio=2.05, **e** Zumbi |
| Deal Engaging com 270 dias | stage=Engaging, days=270 | ratio=3.07, Zumbi **Cronico** |
| Deal Zumbi com GTK 500 | Zumbi + valor=$26.768 | Provavel Zumbi **Critico** (depende do P75) |
| Deal Zumbi com MG Special | Zumbi + valor=$55 | Zumbi simples (valor abaixo do P75) |
| Conta com 0 losses | losses=0 | **Nao** e recorrente |
| Conta com 2 losses | losses=2 | **E** recorrente |
| Conta com 10 losses | losses=10 | Recorrente + **Alto Risco** |

### Validacao de sanidade

Com referencia P75 (88 dias) e threshold 2x (176 dias):

- Deals Engaging ativos: 1.589
- Mediana de dias no stage: 165 dias
- Deals acima de 176 dias: **745 (46.9%)**
- Portanto, **aproximadamente 47%** dos deals Engaging sao classificados como Zumbi

Se o modulo retornar menos de 40% ou mais de 55% dos deals Engaging como Zumbi, revisar a calibracao.

**NOTA:** Os 500 deals em Prospecting ficam fora desta classificacao (sem dados temporais).

---

## 14. Decisoes de Design e Tradeoffs

| Decisao | Alternativa considerada | Justificativa |
|---------|------------------------|---------------|
| Usar P75 (88 dias) como referencia em vez de mediana (57 dias) | Mediana classificaria ~88% como zumbi | Com P75, a classificacao fica mais seletiva e util. Ainda captura a maioria dos deals problematicos, mas deixa uma faixa de "atencao" entre mediana e P75. |
| Threshold fixo de 2x | Threshold adaptativo por vendedor ou produto | Simplicidade. Com 35 vendedores e 7 produtos, thresholds adaptativos adicionam complexidade sem ganho proporcional. O dataset nao e grande o suficiente para calibracao estatistica por combinacao. |
| Flag independente do score | Integrar zumbi como componente do score | O Zumbi e uma comunicacao binaria ("este deal esta morto"). O score ja reflete o problema via decay de velocidade. A flag adiciona clareza sem redundancia. |
| Conta Recorrente Lost com threshold de 2 | Usar win rate da conta (< 50%) | O threshold absoluto e mais intuitivo para o manager. "Esta conta ja perdeu 15 deals" e mais acionavel que "win rate de 42%". |
| Labels em portugues na UI | Labels em ingles | O usuario final e vendedor brasileiro. Linguagem natural em PT-BR e requisito do projeto. |

---

## 15. Testes TDD (test_deal_zombie.py)

Antes de implementar `deal_zombie.py`, escrever os seguintes testes em `tests/test_deal_zombie.py`. Todos devem falhar inicialmente (Red) e passar apos a implementacao (Green).

### 15.1 Testes de classificacao de zumbi

```python
def test_engaging_100_days_not_zombie():
    """Deal Engaging com 100 dias (ratio 1.14) NAO e zumbi."""

def test_engaging_180_days_is_zombie():
    """Deal Engaging com 180 dias (ratio 2.05) E zumbi."""

def test_engaging_270_days_is_chronic_zombie():
    """Deal Engaging com 270 dias (ratio 3.07) e Zumbi Cronico."""

def test_prospecting_never_classified_as_zombie():
    """Deals em Prospecting NAO podem ser classificados como Zumbi (sem dados temporais)."""

def test_zombie_threshold_is_176_days():
    """Threshold para Engaging = 2 * 88 (P75) = 176 dias."""
```

### 15.2 Testes de zumbi critico

```python
def test_zombie_with_gtk500_is_critical():
    """Zumbi com GTK 500 ($26.768) provavelmente e Zumbi Critico (valor > P75)."""

def test_zombie_with_mg_special_not_critical():
    """Zumbi com MG Special ($55) NAO e Zumbi Critico (valor < P75)."""

def test_non_zombie_never_critical():
    """Deal nao-zumbi nunca e classificado como Zumbi Critico."""
```

### 15.3 Testes de conta recorrente lost

```python
def test_account_0_losses_not_recurrent():
    """Conta com 0 losses nao e recorrente."""

def test_account_1_loss_not_recurrent():
    """Conta com 1 loss nao e recorrente."""

def test_account_2_losses_is_recurrent():
    """Conta com 2 losses E recorrente."""

def test_account_10_losses_is_high_risk():
    """Conta com 10 losses e recorrente E alto risco."""
```

### 15.4 Testes de valor estimado

```python
def test_estimated_value_uses_close_value_when_available():
    """Se close_value > 0, usar close_value."""

def test_estimated_value_uses_product_price_when_no_close_value():
    """Se close_value null, usar preco de lista do produto."""
```

### 15.5 Testes de resumo (get_zombie_summary)

```python
def test_zombie_summary_has_expected_keys():
    """Resumo contem: total_active_deals, total_zombies, pct_zombies, pipeline_total, pipeline_inflated."""

def test_zombie_summary_pct_consistent():
    """pct_zombies = total_zombies / total_active_deals * 100."""

def test_zombie_summary_pipeline_inflated_sum_of_zombie_values():
    """pipeline_inflated = soma dos valores estimados dos deals zumbis."""
```

### 15.6 Testes de sanidade com dados reais

```python
def test_approximately_47_percent_engaging_are_zombies():
    """Com referencia P75 (88d) e threshold 2x, ~40-55% dos deals Engaging sao zumbis."""

def test_classify_zombies_adds_expected_columns():
    """classify_zombies retorna DataFrame com colunas: is_zombie, zombie_severity, zombie_label, time_ratio, estimated_value, is_zombie_critical."""
```
