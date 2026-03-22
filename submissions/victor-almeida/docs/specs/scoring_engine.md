# Especificacao Tecnica — Scoring Engine

**Modulo:** `scoring/`
**Autor:** Victor Almeida
**Data:** 21 de marco de 2026
**Status:** Draft
**Referencia:** PRD.md, secao 5 (Algoritmo de Scoring)

---

## 1. Visao Geral

O Scoring Engine calcula um score de 0 a 100 para cada deal ativo (Prospecting ou Engaging) do pipeline. O score representa a **prioridade relativa** do deal — quanto maior, mais o vendedor deveria focar nele.

O engine combina 5 componentes independentes com pesos fixos:

```
SCORE_FINAL = stage_score      * 0.30
            + value_score      * 0.25
            + velocity_score   * 0.25
            + seller_fit_score * 0.10
            + account_health   * 0.10
```

Cada componente retorna um valor normalizado entre 0 e 100. O score final e a media ponderada, garantindo resultado no intervalo [0, 100].

---

## 2. Constantes Globais

```python
# Data de referencia — "hoje" para todos os calculos temporais
REFERENCE_DATE = pd.Timestamp("2017-12-31")

# Stages que recebem score (deals ativos)
ACTIVE_STAGES = ["Prospecting", "Engaging"]

# Stages finalizados — excluidos do scoring
CLOSED_STAGES = ["Won", "Lost"]

# Pesos dos componentes
WEIGHTS = {
    "stage":          0.30,
    "expected_value": 0.25,
    "velocity":       0.25,
    "seller_fit":     0.10,
    "account_health": 0.10,
}
```

**Justificativa dos pesos:**
- **Stage (30%):** O fator mais determinante. Um deal em Engaging ja passou por qualificacao e tem probabilidade significativamente maior de fechar que Prospecting.
- **Valor Esperado (25%):** Deals de alto valor merecem mais atencao, mas nao devem dominar (por isso log-scale).
- **Velocidade (25%):** Deals parados por muito tempo tem probabilidade decrescente de fechar — peso alto para penalizar deals zumbis.
- **Seller Fit e Saude da Conta (10% cada):** Fatores contextuais importantes mas com dados menos robustos (dependem de volume historico).

---

## 3. Componente 1 — Deal Stage (`stage_score`)

### 3.1 Descricao

Score fixo baseado no estagio atual do deal. Reflete a probabilidade empirica de conversao: deals em Engaging ja foram qualificados e tem ~63% de win rate historico.

### 3.2 Calculo

```python
STAGE_SCORES = {
    "Prospecting": 30,
    "Engaging":    70,
}

def calculate_stage_score(deal_stage: str) -> float:
    return STAGE_SCORES.get(deal_stage, 0)
```

### 3.3 Inputs

| Parametro    | Tipo  | Origem                         | Nullable |
|-------------|-------|--------------------------------|----------|
| `deal_stage` | str   | `sales_pipeline.deal_stage`    | Nao      |

### 3.4 Output

| Retorno | Tipo  | Range  |
|---------|-------|--------|
| score   | float | {0, 30, 70} |

### 3.5 Edge Cases

| Cenario                     | Tratamento                |
|-----------------------------|---------------------------|
| Stage = "Won" ou "Lost"    | Retorna 0 (nao deveria chegar aqui — filtrar antes) |
| Stage desconhecido/null     | Retorna 0                 |

---

## 4. Componente 2 — Valor Esperado (`value_score`)

### 4.1 Descricao

Avalia o valor monetario do deal usando escala logaritmica. A escala log evita que mega-deals (GTK 500, ~$26.768) dominem completamente deals menores (MG Special, ~$55) — uma diferenca de 486x no valor bruto se torna uma diferenca de ~3.5x na escala log.

### 4.2 Calculo

```python
import math

# Valor maximo de referencia para normalizacao (calculado dos dados)
# max_value = maior close_value dos deals Won no dataset
# No dataset atual: ~$26.768 (GTK 500)

def calculate_value_score(
    deal_stage: str,
    close_value: float | None,
    product_price: float,
    max_value: float,
) -> float:
    """
    Retorna score de 0 a 100 baseado no valor esperado do deal.

    Para deals ativos (Prospecting e Engaging): close_value e SEMPRE null.
    Usa product_price (sales_price) como proxy para todos os deals ativos.
    """
    # Determinar valor efetivo
    if deal_stage == "Prospecting" or close_value is None or close_value <= 0:
        effective_value = product_price
    else:
        effective_value = close_value

    # Protecao contra max_value invalido
    if max_value <= 0:
        return 0.0

    # Escala logaritmica normalizada
    score = math.log(1 + effective_value) / math.log(1 + max_value)

    # Normalizar para 0-100
    return min(score * 100, 100.0)
```

### 4.3 Inputs

| Parametro       | Tipo          | Origem                                     | Nullable |
|----------------|---------------|---------------------------------------------|----------|
| `deal_stage`   | str           | `sales_pipeline.deal_stage`                 | Nao      |
| `close_value`  | float or None | `sales_pipeline.close_value`                | Sim      |
| `product_price`| float         | `products.sales_price` (via join por produto) | Nao      |
| `max_value`    | float         | Calculado: `max(products.sales_price)`      | Nao      |

### 4.4 Output

| Retorno | Tipo  | Range     |
|---------|-------|-----------|
| score   | float | [0, 100]  |

### 4.5 Calculo de `max_value`

O `max_value` e calculado uma unica vez no startup e passado para a funcao:

```python
# Usar o maior preco de produto como referencia (nao close_value dos Won,
# porque queremos normalizar em relacao ao catalogo, nao a outliers historicos)
max_value = products_df["sales_price"].max()  # 26768 (GTK 500)
```

**Justificativa:** Usar `products.sales_price.max()` em vez de `sales_pipeline.close_value.max()` dos Won porque:
1. Deals ativos nao tem `close_value` — precisamos de referencia consistente
2. O preco de lista e o teto teorico — normaliza o score de forma justa
3. Deals Won com close_value ligeiramente diferente do preco de lista nao criam distorcao

### 4.6 Exemplos de Calculo

| Produto        | Preco    | log(1+preco) | log(1+26768) | Score |
|---------------|----------|-------------|-------------|-------|
| GTK 500       | $26.768  | 10.195      | 10.195      | 100.0 |
| GTX Plus Pro  | $5.482   | 8.610       | 10.195      | 84.4  |
| GTXPro        | $4.821   | 8.481       | 10.195      | 83.2  |
| MG Advanced   | $3.393   | 8.130       | 10.195      | 79.7  |
| GTX Plus Basic| $1.096   | 7.001       | 10.195      | 68.7  |
| GTX Basic     | $550     | 6.312       | 10.195      | 61.9  |
| MG Special    | $55      | 4.025       | 10.195      | 39.5  |

### 4.7 Edge Cases

| Cenario                                         | Tratamento                          |
|------------------------------------------------|-------------------------------------|
| `close_value` e null (Prospecting)             | Usa `product_price` como proxy      |
| `close_value` = 0 (Lost que passou pelo filtro)| Usa `product_price` como proxy      |
| `product_price` nao encontrado (join falhou)   | Usar 0, score = 0                   |
| `max_value` = 0                                | Retorna 0 (evita divisao por zero)  |

### 4.8 Join de Produtos — Atencao ao Nome

O campo `product` no `sales_pipeline.csv` usa "GTXPro" (sem espaco), enquanto `products.csv` usa "GTX Pro" (com espaco). O data_loader deve normalizar isso no carregamento:

```python
# Mapeamento de nomes inconsistentes
PRODUCT_NAME_MAP = {
    "GTXPro": "GTX Pro",
}
```

---

## 5. Componente 3 — Velocidade / Decay por Tempo (`velocity_score`)

### 5.1 Descricao

Penaliza deals que estao parados ha muito tempo no stage atual. Baseado em dados reais dos deals Won, o decay comeca apos o P75 de tempo de fechamento.

### 5.2 Dados de Calibracao

Extraidos dos deals Won no dataset:

| Metrica                           | Valor     | Uso                        |
|----------------------------------|-----------|----------------------------|
| Mediana Won (Engaging -> Close)  | 57 dias   | Referencia informativa      |
| P75 Won (Engaging -> Close)      | 88 dias   | **Referencia para Engaging** |
| P90 Won (Engaging -> Close)      | 106 dias  | Threshold de zumbi          |
| Mediana deals ativos Engaging    | 165 dias  | Diagnostico de inflacao     |

**Achado contra-intuitivo:** Deals que fecham entre 90-150 dias tem win rate de 70-75%, superior aos de 0-15 dias (56%). O decay nao deve penalizar deals prematuramente — por isso a referencia e o P75 (88 dias), nao a mediana (57 dias).

### 5.3 Constantes

```python
# Referencia de tempo saudavel por stage (em dias)
# NOTA: Prospecting NAO tem engage_date nem created_date no dataset.
# Impossivel calcular days_in_stage para Prospecting.
# Tratamento: score de velocidade = 50 (neutro) para todos os Prospecting.
STAGE_REFERENCE_DAYS = {
    "Prospecting": None,  # Sem dados temporais — usar score neutro (50)
    "Engaging":    88,    # P75 dos deals Won (Engaging -> Close)
}

# Tabela de decay por faixa de ratio
DECAY_TABLE = [
    # (ratio_max, decay_factor, label)
    (1.0,  1.00, "saudavel"),
    (1.2,  0.85, "atencao"),
    (1.5,  0.60, "alerta"),
    (2.0,  0.30, "candidato_zumbi"),
    (float("inf"), 0.10, "quase_morto"),
]

# Thresholds para flags de deal zumbi
ZOMBIE_THRESHOLD = 2.0       # ratio >= 2.0 = flag de zumbi
ZOMBIE_CRITICAL_PCTILE = 75  # Zumbi + valor > P75 = zumbi critico
```

### 5.4 Calculo

```python
def calculate_velocity_score(
    deal_stage: str,
    days_in_stage: int,
    stage_reference_days: dict[str, int] = STAGE_REFERENCE_DAYS,
) -> tuple[float, str, dict]:
    """
    Retorna:
    - score (0-100): score de velocidade
    - label (str): classificacao textual ("saudavel", "atencao", etc.)
    - metadata (dict): dados adicionais para explicabilidade
    """
    reference = stage_reference_days.get(deal_stage)

    if reference is None or reference <= 0:
        return 50.0, "sem_referencia", {"ratio": None}

    ratio = days_in_stage / reference

    # Encontrar faixa de decay
    decay = 0.10  # default: quase morto
    label = "quase_morto"
    for ratio_max, decay_factor, decay_label in DECAY_TABLE:
        if ratio <= ratio_max:
            decay = decay_factor
            label = decay_label
            break

    score = decay * 100

    metadata = {
        "days_in_stage": days_in_stage,
        "reference_days": reference,
        "ratio": round(ratio, 2),
        "decay_factor": decay,
        "is_zombie": ratio >= ZOMBIE_THRESHOLD,
    }

    return score, label, metadata
```

### 5.5 Calculo de `days_in_stage`

```python
def calculate_days_in_stage(
    deal_stage: str,
    engage_date: pd.Timestamp | None,
    close_date: pd.Timestamp | None,
    reference_date: pd.Timestamp = REFERENCE_DATE,
) -> int:
    """
    Calcula dias no stage atual com base nas datas disponiveis.

    Prospecting: reference_date - engage_date (se tiver) ou estimativa
    Engaging:    reference_date - engage_date
    """
    if deal_stage == "Prospecting":
        # Prospecting nao tem engage_date — nao sabemos quando entrou
        # Sera tratado como edge case (ver secao 5.7)
        return 0  # Placeholder — ver tratamento em 5.7

    elif deal_stage == "Engaging":
        if engage_date is not None and pd.notna(engage_date):
            return (reference_date - engage_date).days
        return 0  # Fallback se data ausente

    return 0
```

### 5.6 Inputs

| Parametro         | Tipo                  | Origem                                  | Nullable |
|------------------|----------------------|-----------------------------------------|----------|
| `deal_stage`     | str                  | `sales_pipeline.deal_stage`             | Nao      |
| `engage_date`    | Timestamp or None    | `sales_pipeline.engage_date`            | Sim      |
| `close_date`     | Timestamp or None    | `sales_pipeline.close_date`             | Sim      |

### 5.7 Edge Cases

| Cenario                                              | Tratamento                                   |
|-----------------------------------------------------|----------------------------------------------|
| Prospecting sem nenhuma data (todos os 500)          | Nao ha `engage_date` nem `created_date` no dataset. `days_in_stage` = None -> score = 50 (neutro). Nao penalizar nem bonificar. |
| Engaging sem `engage_date` (anomalia nos dados)     | score = 50 (neutro), label = "sem_data"      |
| `days_in_stage` negativo (data futura no dataset)   | Tratar como 0                                |
| `stage_reference_days` = 0 (evitar divisao por zero)| score = 50 (neutro)                          |

### 5.8 Exemplos de Calculo — Engaging

| Engage Date  | Dias no Stage | Ratio (ref=88) | Decay | Score | Label            |
|-------------|--------------|-----------------|-------|-------|------------------|
| 2017-11-15  | 46           | 0.52            | 1.00  | 100   | saudavel         |
| 2017-09-01  | 121          | 1.37            | 0.60  | 60    | alerta           |
| 2017-06-15  | 199          | 2.26            | 0.10  | 10    | quase_morto      |
| 2017-10-03  | 89           | 1.01            | 0.85  | 85    | atencao          |
| 2017-04-01  | 274          | 3.11            | 0.10  | 10    | quase_morto      |

---

## 6. Componente 4 — Seller-Deal Fit (`seller_fit_score`)

### 6.1 Descricao

Avalia a afinidade do vendedor com o setor da conta. Um vendedor com alto win rate em determinado setor tem mais chance de fechar deals nesse setor. O score compara o desempenho do vendedor naquele setor com a media geral do time.

### 6.2 Constantes

```python
# Minimo de deals no setor para considerar dados significativos
SELLER_FIT_MIN_DEALS = 5

# Limites do multiplicador (evita outliers)
FIT_MULTIPLIER_MIN = 0.3   # Piso: vendedor muito abaixo da media
FIT_MULTIPLIER_MAX = 2.0   # Teto: vendedor muito acima da media

# Score neutro para dados insuficientes
FIT_NEUTRAL_SCORE = 50.0
```

### 6.3 Pre-calculo de Estatisticas

Antes de calcular o score individual, o modulo precisa gerar tabelas de referencia a partir dos dados historicos (deals Won + Lost):

```python
def build_seller_fit_stats(
    pipeline_df: pd.DataFrame,
    accounts_df: pd.DataFrame,
) -> dict:
    """
    Pre-calcula estatisticas de win rate por vendedor x setor e time x setor.

    Retorna dict com:
    - seller_sector_stats: {(sales_agent, sector): {"wins": int, "total": int, "winrate": float}}
    - team_sector_stats:   {sector: {"wins": int, "total": int, "winrate": float}}
    """
    # Filtrar apenas deals fechados (Won ou Lost)
    closed = pipeline_df[pipeline_df["deal_stage"].isin(["Won", "Lost"])].copy()

    # Fazer join com accounts para obter setor
    closed = closed.merge(
        accounts_df[["account", "sector"]],
        on="account",
        how="left",
    )

    # Marcar wins
    closed["is_win"] = (closed["deal_stage"] == "Won").astype(int)

    # Stats por vendedor x setor
    seller_sector = closed.groupby(["sales_agent", "sector"]).agg(
        wins=("is_win", "sum"),
        total=("is_win", "count"),
    ).reset_index()
    seller_sector["winrate"] = seller_sector["wins"] / seller_sector["total"]

    # Stats por setor (media do time)
    team_sector = closed.groupby("sector").agg(
        wins=("is_win", "sum"),
        total=("is_win", "count"),
    ).reset_index()
    team_sector["winrate"] = team_sector["wins"] / team_sector["total"]

    return {
        "seller_sector": seller_sector,
        "team_sector": team_sector,
    }
```

### 6.4 Calculo do Score Individual

```python
def calculate_seller_fit_score(
    sales_agent: str,
    account_sector: str,
    fit_stats: dict,
) -> tuple[float, dict]:
    """
    Retorna:
    - score (0-100)
    - metadata (dict): dados para explicabilidade
    """
    seller_sector = fit_stats["seller_sector"]
    team_sector = fit_stats["team_sector"]

    # Buscar stats do vendedor neste setor
    seller_row = seller_sector[
        (seller_sector["sales_agent"] == sales_agent) &
        (seller_sector["sector"] == account_sector)
    ]

    # Buscar stats do time neste setor
    team_row = team_sector[team_sector["sector"] == account_sector]

    metadata = {
        "sales_agent": sales_agent,
        "sector": account_sector,
    }

    # Verificar se ha dados suficientes do vendedor
    if seller_row.empty or seller_row.iloc[0]["total"] < SELLER_FIT_MIN_DEALS:
        metadata["reason"] = "dados_insuficientes"
        metadata["seller_deals_in_sector"] = 0 if seller_row.empty else int(seller_row.iloc[0]["total"])
        return FIT_NEUTRAL_SCORE, metadata

    seller_wr = seller_row.iloc[0]["winrate"]
    seller_total = int(seller_row.iloc[0]["total"])

    # Verificar se ha dados do time no setor
    if team_row.empty or team_row.iloc[0]["winrate"] == 0:
        metadata["reason"] = "sem_referencia_time"
        return FIT_NEUTRAL_SCORE, metadata

    team_wr = team_row.iloc[0]["winrate"]

    # Calcular multiplicador
    raw_multiplier = seller_wr / team_wr
    clamped_multiplier = max(FIT_MULTIPLIER_MIN, min(raw_multiplier, FIT_MULTIPLIER_MAX))

    # Normalizar para 0-100
    # multiplier 0.3 -> score 0
    # multiplier 1.0 -> score 50 (na media)
    # multiplier 2.0 -> score 100
    score = ((clamped_multiplier - FIT_MULTIPLIER_MIN) / (FIT_MULTIPLIER_MAX - FIT_MULTIPLIER_MIN)) * 100

    metadata.update({
        "seller_winrate": round(seller_wr, 3),
        "team_winrate": round(team_wr, 3),
        "raw_multiplier": round(raw_multiplier, 3),
        "clamped_multiplier": round(clamped_multiplier, 3),
        "seller_deals_in_sector": seller_total,
        "reason": "calculado",
    })

    return round(score, 1), metadata
```

### 6.5 Inputs

| Parametro        | Tipo  | Origem                                        | Nullable |
|-----------------|-------|-----------------------------------------------|----------|
| `sales_agent`   | str   | `sales_pipeline.sales_agent`                  | Nao      |
| `account_sector`| str   | `accounts.sector` (via join por `account`)    | Sim      |
| `fit_stats`     | dict  | Pre-calculado por `build_seller_fit_stats()`  | Nao      |

### 6.6 Output

| Retorno  | Tipo           | Descricao                    |
|----------|----------------|------------------------------|
| score    | float          | 0-100                        |
| metadata | dict           | Dados para explicabilidade   |

### 6.7 Normalizacao do Multiplicador

O multiplicador cru (`seller_wr / team_wr`) precisa ser mapeado para 0-100:

```
multiplicador   ->  score
0.3 (piso)      ->  0
0.65            ->  ~20.6
1.0 (media)     ->  41.2
1.2             ->  52.9
1.5             ->  70.6
2.0 (teto)      ->  100
```

A funcao de normalizacao e linear entre o piso (0.3) e o teto (2.0).

### 6.8 Exemplos com Dados Reais

| Vendedor        | Setor          | Seller WR | Team WR | Multiplier | Score |
|----------------|----------------|-----------|---------|------------|-------|
| Markita Hansen | entertainment  | 90.5%     | ~63%    | 1.44       | 67.1  |
| Markita Hansen | technology     | 35.7%     | ~63%    | 0.57       | 15.9  |
| (Qualquer)     | (< 5 deals)   | —         | —       | 1.0        | 50.0  |

### 6.9 Edge Cases

| Cenario                                    | Tratamento                              |
|-------------------------------------------|-----------------------------------------|
| Vendedor com < 5 deals no setor           | Score = 50 (neutro)                     |
| Setor da conta nao encontrado no join     | Score = 50 (neutro)                     |
| Team WR = 0 no setor (todos perdidos)     | Score = 50 (neutro, evita divisao por 0)|
| Vendedor nao existe nos dados historicos  | Score = 50 (neutro)                     |
| Multiplicador > 2.0 (super performer)     | Clamped em 2.0 -> score = 100           |
| Multiplicador < 0.3 (muito abaixo)        | Clamped em 0.3 -> score = 0             |
| Setor "technolgy" (typo no dataset)       | Corrigido para "technology" no data_loader. JOIN usa `account`, nao `sector`. |

---

## 7. Componente 5 — Saude da Conta (`account_health_score`)

### 7.1 Descricao

Avalia o historico de sucesso (wins vs losses) da conta. Contas com alto win rate historico indicam relacionamento saudavel; contas com muitos losses sugerem problemas recorrentes.

### 7.2 Constantes

```python
# Minimo de deals fechados para considerar dados significativos
ACCOUNT_HEALTH_MIN_DEALS = 3

# Score neutro para dados insuficientes
ACCOUNT_HEALTH_NEUTRAL = 50.0

# Penalizacao extra para contas com losses recentes
RECENT_LOSS_PENALTY = 10.0  # Pontos subtraidos por loss recente
RECENT_LOSS_WINDOW_DAYS = 180  # Janela para considerar "recente" (6 meses antes de REFERENCE_DATE)
MAX_LOSS_PENALTY = 30.0  # Teto da penalizacao cumulativa
```

### 7.3 Pre-calculo de Estatisticas

```python
def build_account_health_stats(
    pipeline_df: pd.DataFrame,
    reference_date: pd.Timestamp = REFERENCE_DATE,
) -> pd.DataFrame:
    """
    Pre-calcula estatisticas de saude por conta.

    Retorna DataFrame com:
    - account, wins, losses, total, winrate, recent_losses
    """
    closed = pipeline_df[pipeline_df["deal_stage"].isin(["Won", "Lost"])].copy()

    # Stats gerais por conta
    stats = closed.groupby("account").agg(
        wins=("deal_stage", lambda x: (x == "Won").sum()),
        losses=("deal_stage", lambda x: (x == "Lost").sum()),
        total=("deal_stage", "count"),
    ).reset_index()
    stats["winrate"] = stats["wins"] / stats["total"]

    # Losses recentes (ultimos 180 dias antes da data de referencia)
    cutoff_date = reference_date - pd.Timedelta(days=RECENT_LOSS_WINDOW_DAYS)
    recent_lost = closed[
        (closed["deal_stage"] == "Lost") &
        (closed["close_date"] >= cutoff_date)
    ]
    recent_counts = recent_lost.groupby("account").size().reset_index(name="recent_losses")

    stats = stats.merge(recent_counts, on="account", how="left")
    stats["recent_losses"] = stats["recent_losses"].fillna(0).astype(int)

    return stats
```

### 7.4 Calculo do Score Individual

```python
def calculate_account_health_score(
    account: str,
    account_stats: pd.DataFrame,
) -> tuple[float, dict]:
    """
    Retorna:
    - score (0-100)
    - metadata (dict): dados para explicabilidade
    """
    row = account_stats[account_stats["account"] == account]

    metadata = {"account": account}

    if row.empty or row.iloc[0]["total"] < ACCOUNT_HEALTH_MIN_DEALS:
        metadata["reason"] = "dados_insuficientes"
        metadata["total_deals"] = 0 if row.empty else int(row.iloc[0]["total"])
        return ACCOUNT_HEALTH_NEUTRAL, metadata

    r = row.iloc[0]
    winrate = r["winrate"]
    recent_losses = int(r["recent_losses"])

    # Score base = winrate normalizado para 0-100
    base_score = winrate * 100

    # Penalizacao por losses recentes
    loss_penalty = min(recent_losses * RECENT_LOSS_PENALTY, MAX_LOSS_PENALTY)

    score = max(0, base_score - loss_penalty)

    metadata.update({
        "wins": int(r["wins"]),
        "losses": int(r["losses"]),
        "total_deals": int(r["total"]),
        "winrate": round(winrate, 3),
        "recent_losses": recent_losses,
        "loss_penalty": loss_penalty,
        "reason": "calculado",
    })

    return round(score, 1), metadata
```

### 7.5 Inputs

| Parametro       | Tipo         | Origem                                      | Nullable |
|----------------|-------------|----------------------------------------------|----------|
| `account`      | str          | `sales_pipeline.account`                     | Nao      |
| `account_stats`| DataFrame    | Pre-calculado por `build_account_health_stats()` | Nao |

### 7.6 Output

| Retorno  | Tipo   | Descricao                   |
|----------|--------|-----------------------------|
| score    | float  | 0-100                       |
| metadata | dict   | Dados para explicabilidade  |

### 7.7 Exemplos com Dados Reais

| Conta     | Wins | Losses | Total | WR    | Losses Recentes | Penalizacao | Score |
|-----------|------|--------|-------|-------|-----------------|-------------|-------|
| Hottechi  | ~55  | 82     | ~137  | 40.1% | 8               | 30 (teto)   | 10.1  |
| Kan-code  | ~48  | 72     | ~120  | 40.0% | 6               | 30 (teto)   | 10.0  |
| (Conta X) | 8    | 2      | 10    | 80.0% | 0               | 0           | 80.0  |
| (Conta Y) | 1    | 1      | 2     | 50.0% | —               | —           | 50.0* |

*Score neutro — menos de 3 deals fechados.

### 7.8 Edge Cases

| Cenario                                     | Tratamento                        |
|--------------------------------------------|-----------------------------------|
| Conta com < 3 deals fechados               | Score = 50 (neutro)               |
| Conta nao encontrada nos dados historicos   | Score = 50 (neutro)               |
| Conta com 100% win rate                     | Score = 100                       |
| Conta com 0% win rate + losses recentes     | Score = 0 (0 - penalty, clamped)  |
| `close_date` null em deal Lost (anomalia)   | Nao conta como "recente", conta no total |

---

## 8. Engine — Orquestrador (`engine.py`)

### 8.1 Responsabilidades

O `engine.py` e o ponto de entrada unico para calculo de scores. Ele:

1. Recebe os DataFrames carregados
2. Pre-calcula estatisticas (seller fit stats, account health stats, max_value)
3. Filtra deals ativos (Prospecting + Engaging)
4. Calcula cada componente para cada deal
5. Combina os componentes com os pesos
6. Retorna DataFrame enriquecido com score e metadados

### 8.2 Interface Publica

```python
class ScoringEngine:
    """
    Orquestrador do calculo de score.
    Inicializado uma vez com os DataFrames; calcula scores sob demanda.
    """

    def __init__(
        self,
        pipeline_df: pd.DataFrame,
        accounts_df: pd.DataFrame,
        products_df: pd.DataFrame,
        sales_teams_df: pd.DataFrame,
        reference_date: pd.Timestamp = REFERENCE_DATE,
    ):
        """
        Inicializa o engine e pre-calcula estatisticas.

        Este construtor faz o trabalho pesado:
        - Normaliza nomes de produtos
        - Merge de tabelas auxiliares
        - Pre-calcula seller_fit_stats e account_health_stats
        - Calcula max_value
        """
        ...

    def score_pipeline(self) -> pd.DataFrame:
        """
        Calcula score para todos os deals ativos.

        Retorna DataFrame com colunas originais + colunas adicionais:
        - score_final (float, 0-100)
        - score_stage (float)
        - score_value (float)
        - score_velocity (float)
        - score_seller_fit (float)
        - score_account_health (float)
        - velocity_label (str): "saudavel", "atencao", "alerta", etc.
        - velocity_ratio (float): ratio dias/referencia
        - is_zombie (bool): True se ratio >= 2.0
        - is_critical_zombie (bool): True se zumbi + valor > P75
        - days_in_stage (int)
        - score_breakdown (dict): detalhamento completo para explicabilidade
        """
        ...

    def score_single_deal(self, opportunity_id: str) -> dict:
        """
        Calcula score detalhado para um unico deal.
        Util para a tela de detalhe do deal.

        Retorna dict com score, componentes e metadados completos.
        """
        ...
```

### 8.3 Fluxo de Inicializacao

```
__init__()
    |
    +-> Normalizar nomes de produtos (PRODUCT_NAME_MAP)
    +-> Merge: pipeline + accounts (obter sector)
    +-> Merge: pipeline + products (obter sales_price)
    +-> Merge: pipeline + sales_teams (obter manager, regional_office)
    +-> Filtrar deals ativos: deal_stage in ACTIVE_STAGES
    +-> Calcular days_in_stage para cada deal
    +-> Pre-calcular seller_fit_stats (build_seller_fit_stats)
    +-> Pre-calcular account_health_stats (build_account_health_stats)
    +-> Calcular max_value = products_df["sales_price"].max()
```

### 8.4 Fluxo de Calculo (`score_pipeline`)

```
score_pipeline()
    |
    Para cada deal ativo:
    |   +-> calculate_stage_score(deal_stage)
    |   +-> calculate_value_score(deal_stage, close_value, product_price, max_value)
    |   +-> calculate_velocity_score(deal_stage, days_in_stage)
    |   +-> calculate_seller_fit_score(sales_agent, sector, fit_stats)
    |   +-> calculate_account_health_score(account, account_stats)
    |
    +-> score_final = sum(componente * peso for componente, peso in WEIGHTS)
    +-> Determinar is_zombie e is_critical_zombie
    +-> Gerar score_breakdown para cada deal
    +-> Ordenar por score_final descendente
    +-> Retornar DataFrame enriquecido
```

### 8.5 Calculo do Score Final

```python
def _compute_final_score(self, row: pd.Series) -> float:
    """
    Combina os 5 componentes com os pesos definidos.
    Resultado garantido no intervalo [0, 100].
    """
    score = (
        row["score_stage"]          * WEIGHTS["stage"]
        + row["score_value"]        * WEIGHTS["expected_value"]
        + row["score_velocity"]     * WEIGHTS["velocity"]
        + row["score_seller_fit"]   * WEIGHTS["seller_fit"]
        + row["score_account_health"] * WEIGHTS["account_health"]
    )
    return round(min(max(score, 0), 100), 1)
```

### 8.6 Determinacao de Flags

```python
def _apply_flags(self, df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica flags de deal zumbi e zumbi critico.
    """
    df["is_zombie"] = df["velocity_ratio"] >= ZOMBIE_THRESHOLD

    # Zumbi critico: zumbi + valor do deal acima do P75
    if not df.empty:
        value_p75 = df["effective_value"].quantile(0.75)
        df["is_critical_zombie"] = df["is_zombie"] & (df["effective_value"] > value_p75)
    else:
        df["is_critical_zombie"] = False

    return df
```

---

## 9. Score Breakdown — Explicabilidade

### 9.1 Estrutura do Breakdown

Cada deal recebe um `score_breakdown` dict que alimenta a UI de explicacao:

```python
score_breakdown = {
    "score_final": 72.3,
    "components": {
        "stage": {
            "score": 70,
            "weight": 0.30,
            "weighted": 21.0,
            "detail": "Deal em Engaging — ja qualificado",
        },
        "expected_value": {
            "score": 84.4,
            "weight": 0.25,
            "weighted": 21.1,
            "detail": "Valor alto (GTX Plus Pro, $5.482)",
        },
        "velocity": {
            "score": 85,
            "weight": 0.25,
            "weighted": 21.25,
            "detail": "46 dias em Engaging (saudavel, ref: 88 dias)",
            "ratio": 0.52,
            "label": "saudavel",
        },
        "seller_fit": {
            "score": 67.1,
            "weight": 0.10,
            "weighted": 6.71,
            "detail": "Seu WR neste setor (90.5%) esta acima da media do time (63%)",
        },
        "account_health": {
            "score": 80.0,
            "weight": 0.10,
            "weighted": 8.0,
            "detail": "Conta com bom historico (80% WR em 10 deals)",
        },
    },
    "flags": {
        "is_zombie": False,
        "is_critical_zombie": False,
        "zombie_detail": None,
    },
}
```

### 9.2 Geracao de Textos Explicativos

Os textos de `detail` sao gerados por modulo. Exemplos de templates:

| Componente      | Condicao              | Template                                                        |
|----------------|----------------------|-----------------------------------------------------------------|
| Stage          | Prospecting           | "Deal em Prospecting — ainda em qualificacao"                   |
| Stage          | Engaging              | "Deal em Engaging — ja qualificado"                             |
| Value          | Alto (score > 75)     | "Valor alto ({produto}, ${valor})"                              |
| Value          | Medio (25-75)         | "Valor medio ({produto}, ${valor})"                             |
| Value          | Baixo (< 25)          | "Valor baixo ({produto}, ${valor})"                             |
| Velocity       | Saudavel              | "{dias} dias em {stage} (saudavel, ref: {ref} dias)"           |
| Velocity       | Atencao               | "{dias} dias em {stage} — ficando lento (ref: {ref} dias)"     |
| Velocity       | Alerta                | "Parado ha {dias} dias — risco de esfriar"                      |
| Velocity       | Zumbi                 | "ALERTA: {dias} dias parado — {ratio}x acima do esperado"       |
| Seller Fit     | Acima da media        | "Seu WR neste setor ({wr}%) esta acima da media ({team_wr}%)"  |
| Seller Fit     | Abaixo da media       | "Seu WR neste setor ({wr}%) esta abaixo da media ({team_wr}%)" |
| Seller Fit     | Dados insuficientes   | "Poucos deals neste setor para avaliar fit"                     |
| Account Health | Saudavel (> 65%)      | "Conta com bom historico ({wr}% WR em {n} deals)"              |
| Account Health | Risco (< 40%)         | "Conta com historico desfavoravel ({wr}% WR, {losses} perdidos)"|
| Account Health | Dados insuficientes   | "Pouco historico desta conta"                                    |

---

## 10. Exemplo Completo de Calculo

### Deal hipotetico

```
opportunity_id: ABC123
sales_agent:    Markita Hansen
product:        GTX Plus Pro
account:        Hottechi
deal_stage:     Engaging
engage_date:    2017-10-03
close_value:    null (deal ativo)
```

### Passo 1 — Stage Score

```
deal_stage = "Engaging" -> score_stage = 70
```

### Passo 2 — Value Score

```
close_value = null -> usar product_price
product_price (GTX Plus Pro) = $5.482
max_value = $26.768

score_value = log(1 + 5482) / log(1 + 26768) * 100
            = 8.610 / 10.195 * 100
            = 84.4
```

### Passo 3 — Velocity Score

```
days_in_stage = (2017-12-31) - (2017-10-03) = 89 dias
reference = 88 dias (Engaging)
ratio = 89 / 88 = 1.01

ratio 1.01 cai na faixa (1.0, 1.2] -> decay = 0.85
score_velocity = 0.85 * 100 = 85
label = "atencao"
```

### Passo 4 — Seller Fit Score

```
Markita Hansen em sector de Hottechi (assumindo "technology"):
seller_wr = 35.7% (Markita em technology)
team_wr = ~63% (media do time em technology)

raw_multiplier = 0.357 / 0.63 = 0.567
clamped = 0.567 (dentro de [0.3, 2.0])

score_seller_fit = (0.567 - 0.3) / (2.0 - 0.3) * 100
                 = 0.267 / 1.7 * 100
                 = 15.7
```

### Passo 5 — Account Health Score

```
Hottechi: wins=~55, losses=82, total=~137, winrate=40.1%
recent_losses = 8 (muitos)
loss_penalty = min(8 * 10, 30) = 30

score_account_health = 40.1 - 30 = 10.1
```

### Passo 6 — Score Final

```
score_final = 70   * 0.30   (stage)
            + 84.4 * 0.25   (value)
            + 85   * 0.25   (velocity)
            + 15.7 * 0.10   (seller_fit)
            + 10.1 * 0.10   (account_health)

            = 21.0 + 21.1 + 21.25 + 1.57 + 1.01

            = 65.9
```

### Interpretacao

Score de **65.9** — deal com valor alto e velocidade razoavel, mas prejudicado pelo fit fraco do vendedor neste setor e historico ruim da conta. Acao sugerida: "Seu historico neste setor esta abaixo da media. Consultar vendedor com melhor fit para estrategia."

---

## 11. Tratamento Global de Edge Cases

### 11.1 Dados Nulos

| Campo           | Ocorrencia esperada              | Tratamento                       |
|----------------|----------------------------------|----------------------------------|
| `engage_date`  | Null em Prospecting              | days_in_stage = 0, velocity = 100|
| `close_date`   | Null em Prospecting e Engaging   | Nao afeta (nao usado para ativos)|
| `close_value`  | Null em Prospecting e Engaging   | Usa product_price como proxy     |
| `account`      | Potencialmente null              | Seller fit = 50, Account health = 50 |
| `sector`       | Conta sem match no accounts.csv  | Seller fit = 50                  |

### 11.2 Divisao por Zero

| Situacao                 | Onde ocorre            | Protecao                     |
|-------------------------|------------------------|------------------------------|
| `max_value = 0`         | Value score            | Retorna 0                    |
| `reference_days = 0`    | Velocity score         | Retorna 50 (neutro)          |
| `team_wr = 0`           | Seller fit             | Retorna 50 (neutro)          |
| `total_deals = 0`       | Account health         | Retorna 50 (neutro)          |

### 11.3 Valores Fora do Range

Todos os componentes sao clamped entre 0 e 100 antes da combinacao final. O score final tambem e clamped:

```python
score_final = min(max(score_final, 0), 100)
```

---

## 12. Performance

### 12.1 Requisitos

- Dataset: ~8.800 registros, ~2.089 deals ativos (500 Prospecting + 1.589 Engaging)
- Tempo de calculo: < 1 segundo para score completo do pipeline
- Carregamento: < 3 segundos incluindo leitura dos CSVs

### 12.2 Estrategia

- Pre-calcular todas as estatisticas (seller fit, account health) uma unica vez no `__init__`
- Usar operacoes vetorizadas do Pandas em vez de loops Python
- Cache via `@st.cache_data` no Streamlit para evitar recalculo em rerender
- Evitar `.apply()` com funcoes Python puras quando possivel — preferir `.map()` e operacoes de coluna

### 12.3 Vetorizacao do Score

Em vez de calcular deal a deal, o engine deve calcular cada componente como coluna do DataFrame:

```python
# Exemplo: stage score vetorizado
df["score_stage"] = df["deal_stage"].map(STAGE_SCORES).fillna(0)

# Exemplo: value score vetorizado
df["score_value"] = (
    np.log(1 + df["effective_value"]) / np.log(1 + max_value) * 100
).clip(0, 100)
```

---

## 13. Testes e Validacao

### 13.1 Cenarios de Teste por Componente

**Stage Score:**
- Prospecting -> 30
- Engaging -> 70
- Won -> 0
- Valor desconhecido -> 0

**Value Score:**
- GTK 500 ($26.768) -> ~100
- MG Special ($55) -> ~39.5
- close_value null -> usa product_price
- max_value = 0 -> retorna 0

**Velocity Score:**
- 44 dias Engaging (ratio 0.5) -> 100, "saudavel"
- 88 dias Engaging (ratio 1.0) -> 100, "saudavel"
- 95 dias Engaging (ratio 1.08) -> 85, "atencao"
- 120 dias Engaging (ratio 1.36) -> 60, "alerta"
- 150 dias Engaging (ratio 1.70) -> 30, "candidato_zumbi"
- 200 dias Engaging (ratio 2.27) -> 10, "quase_morto"

**Seller Fit:**
- Markita Hansen + entertainment -> score alto (~67)
- Markita Hansen + technology -> score baixo (~16)
- Vendedor com < 5 deals -> 50 (neutro)

**Account Health:**
- Conta com 80% WR, 0 losses recentes -> 80
- Hottechi (40% WR, 8 losses recentes) -> ~10
- Conta com < 3 deals -> 50 (neutro)

### 13.2 Testes de Integracao

- Score final de todos os deals ativos esta entre 0 e 100
- Nenhum NaN no score final
- Deals Won/Lost nao recebem score
- Soma dos weighted scores = score final (com tolerancia de arredondamento)
- Deals em Engaging com mais tempo tem score de velocity menor
- Ordenacao por score_final e estavel

### 13.3 Validacao de Sanidade

- Score medio do pipeline esta entre 30 e 70 (nao enviesado para extremos)
- Deals em Engaging tem score medio > deals em Prospecting
- GTK 500 tem value_score > MG Special
- Deals com 200+ dias tem velocity_score baixo

---

## 14. Estrutura de Arquivos

```
scoring/
├── __init__.py           # Exporta ScoringEngine
├── constants.py          # Todas as constantes e thresholds
├── engine.py             # Classe ScoringEngine (orquestrador)
├── velocity.py           # calculate_velocity_score, calculate_days_in_stage
├── seller_fit.py         # build_seller_fit_stats, calculate_seller_fit_score
├── account_health.py     # build_account_health_stats, calculate_account_health_score
└── explainability.py     # Geracao de textos explicativos (score_breakdown)
```

**Nota:** `constants.py` e `explainability.py` sao adicoes em relacao ao PRD original. A separacao de constantes facilita calibracao futura, e o modulo de explicabilidade isola a logica de geracao de texto da logica de calculo.

---

## 15. Testes TDD (test_scoring_engine.py)

Antes de implementar o scoring engine, escrever os seguintes testes em `tests/test_scoring_engine.py`. Todos devem falhar inicialmente (Red) e passar apos a implementacao (Green).

### 15.1 Testes do Stage Score

```python
def test_stage_score_prospecting_returns_30():
    """Prospecting deve retornar score 30."""

def test_stage_score_engaging_returns_70():
    """Engaging deve retornar score 70."""

def test_stage_score_won_returns_0():
    """Won nao e deal ativo, retorna 0."""

def test_stage_score_unknown_returns_0():
    """Stage desconhecido retorna 0."""
```

### 15.2 Testes do Value Score

```python
def test_value_score_gtk500_near_100():
    """GTK 500 ($26.768) deve ter value_score proximo de 100."""

def test_value_score_mg_special_around_39():
    """MG Special ($55) deve ter value_score em torno de 39."""

def test_value_score_uses_product_price_when_close_value_null():
    """Quando close_value e null, usa sales_price do produto."""

def test_value_score_zero_when_max_value_zero():
    """Se max_value = 0, retorna 0 (sem divisao por zero)."""

def test_value_score_always_between_0_and_100():
    """value_score deve estar sempre entre 0 e 100."""
```

### 15.3 Testes do Velocity Score

```python
def test_velocity_score_healthy_deal():
    """Deal com 44 dias em Engaging (ratio 0.5) -> score 100, label 'saudavel'."""

def test_velocity_score_at_reference():
    """Deal com 88 dias em Engaging (ratio 1.0) -> score 100, label 'saudavel'."""

def test_velocity_score_attention():
    """Deal com 95 dias (ratio ~1.08) -> score ~85, label 'atencao'."""

def test_velocity_score_alert():
    """Deal com 120 dias (ratio ~1.36) -> score ~60, label 'alerta'."""

def test_velocity_score_zombie():
    """Deal com 200 dias (ratio ~2.27) -> score ~10, label 'quase_morto'."""

def test_velocity_score_prospecting_returns_neutral():
    """Deal em Prospecting (sem engage_date) retorna score neutro."""

def test_velocity_decay_is_monotonically_decreasing():
    """Score de velocidade deve diminuir conforme ratio aumenta."""
```

### 15.4 Testes do Seller Fit Score

```python
def test_seller_fit_neutral_when_few_deals():
    """Vendedor com < 5 deals no setor retorna 50 (neutro)."""

def test_seller_fit_neutral_when_no_sector():
    """Deal sem setor (account null) retorna 50 (neutro)."""

def test_seller_fit_high_when_above_team_average():
    """Vendedor com WR acima da media do time retorna score > 50."""

def test_seller_fit_low_when_below_team_average():
    """Vendedor com WR abaixo da media retorna score < 50."""

def test_seller_fit_clamped_at_100():
    """Multiplicador > 2.0 deve ser clamped, score maximo = 100."""

def test_seller_fit_clamped_at_0():
    """Multiplicador < 0.3 deve ser clamped, score minimo = 0."""

def test_build_seller_fit_stats_uses_only_closed_deals():
    """Stats devem ser calculadas apenas com deals Won e Lost."""
```

### 15.5 Testes do Account Health Score

```python
def test_account_health_neutral_when_few_deals():
    """Conta com < 3 deals fechados retorna 50 (neutro)."""

def test_account_health_high_winrate():
    """Conta com 80% WR e 0 losses recentes -> score 80."""

def test_account_health_low_with_recent_losses():
    """Conta com WR baixo + losses recentes -> score penalizado."""

def test_account_health_penalty_capped_at_30():
    """Penalizacao por losses recentes nao ultrapassa 30 pontos."""

def test_account_health_score_never_negative():
    """Score nunca fica abaixo de 0."""
```

### 15.6 Testes do Engine (integracao)

```python
def test_score_pipeline_returns_all_active_deals():
    """score_pipeline() retorna um score para cada deal ativo."""

def test_score_final_between_0_and_100():
    """Todos os scores finais estao entre 0 e 100."""

def test_score_final_no_nan():
    """Nenhum NaN no score final."""

def test_won_and_lost_excluded_from_scoring():
    """Deals Won e Lost nao aparecem no resultado."""

def test_weighted_components_sum_to_final():
    """Soma dos componentes ponderados = score final (tolerancia 0.1)."""

def test_engaging_mean_score_higher_than_prospecting():
    """Score medio de Engaging > score medio de Prospecting."""

def test_zombie_flag_set_when_ratio_above_2():
    """is_zombie = True quando velocity_ratio >= 2.0."""

def test_critical_zombie_requires_zombie_and_high_value():
    """is_critical_zombie requer is_zombie AND valor > P75."""

def test_score_breakdown_has_all_components():
    """score_breakdown contem stage, expected_value, velocity, seller_fit, account_health."""
```
