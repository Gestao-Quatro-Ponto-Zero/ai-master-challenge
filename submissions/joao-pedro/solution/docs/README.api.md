# API REST — Deal Prioritization

API REST construída com FastAPI que expõe o motor de scoring e priorização de deals.

**Base URL (local):** `http://localhost:8000`
**Documentação interativa:** `http://localhost:8000/docs`
**Como rodar:** `uvicorn api.main:app --reload` (a partir de `deal-prioritization/`)

---

## Endpoints

### Meta

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/health` | Health check — retorna `{"status": "ok"}` |
| GET | `/benchmarks` | Win rates globais, medianas de tempo (Won/Lost/Engaging), top 20 contas |

---

### Deals — `/deals`

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/deals` | Lista deals com score e ação recomendada (padrão: apenas Engaging) |
| GET | `/deals/{opportunity_id}` | Detalhe completo de um deal com breakdown do score |

**Filtros disponíveis em `GET /deals`:**

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `sales_agent` | string | Filtrar por vendedor |
| `product` | string | Filtrar por produto |
| `account` | string | Filtrar por conta |
| `action` | string | `PUSH_HARD` · `ACCELERATE` · `MONITOR` · `INVESTIGATE` · `TRANSFER` · `CONSIDER_TRANSFER` · `DISCARD` · `RE_QUALIFY` |
| `min_score` | float | Score mínimo (0–100) |
| `min_days` | int | Mínimo de dias no pipeline |
| `all_stages` | bool | `true` retorna todos os estágios (Prospecting, Engaging, Won, Lost); Won/Lost retornam score 0 e sem ação — usado pelo kanban |

**Response `GET /deals` (item):**
```json
{
  "opportunity_id": "string",
  "sales_agent": "string",
  "product": "string",
  "account": "string",
  "deal_stage": "Engaging",
  "close_value": 12500.0,
  "days_in_pipeline": 87,
  "regional_office": "string",
  "score": 74.3,
  "urgency": 68.0,
  "probability": 82.0,
  "value": 61.0,
  "viability": 0.78,
  "action": "PUSH_HARD",
  "message": "string"
}
```

---

### Sellers — `/sellers`

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/sellers` | Lista vendedores com KPIs agregados |
| GET | `/sellers/{sales_agent}` | Detalhe de um vendedor |

**Filtros disponíveis em `GET /sellers`:**

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `region` | string | Filtrar por escritório regional |
| `viability` | string | `Alta` · `Média` · `Baixa` |
| `sort_by` | string | `win_rate` · `active_deals` · `prospecting` · `viability` |

---

### Managers — `/managers`

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/managers` | Lista managers com métricas agregadas do time |

**Filtros disponíveis:**

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `region` | string | Filtrar por escritório regional |
| `viability` | string | `Alta` · `Média` · `Baixa` |
| `sort_by` | string | `avg_win_rate` · `total_active_deals` · `avg_viability` |

---

### Products — `/products`

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/products` | Lista produtos com métricas de performance |

**Filtros disponíveis:**

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `sort_by` | string | `win_rate` · `avg_ticket` · `avg_cycle` · `total_deals` |

---

### Accounts — `/accounts`

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/accounts` | Lista contas com win rate e volume de deals |

**Filtros disponíveis:**

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `sector` | string | Filtrar por setor |
| `office_location` | string | Filtrar por localidade |
| `top20_only` | bool | Apenas as top 20 contas por revenue |
| `min_deals` | int | Mínimo de deals |
| `sort_by` | string | `win_rate` · `total_deals` · `avg_value` |

---

### Analysis — `/analysis`

#### Ações

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/analysis/actions` | Distribuição de ações recomendadas com breakdown por seller, produto e região |

**Response `GET /analysis/actions`:**
```json
{
  "total_deals": 120,
  "distribution": {
    "PUSH_HARD": { "count": 30, "pct": 25.0 }
  },
  "by_seller": { "Ana Silva": { "PUSH_HARD": 5, "MONITOR": 2 } },
  "by_product": { "Produto X": { "TRANSFER": 3 } },
  "by_region": { "São Paulo": { "ACCELERATE": 10 } }
}
```

---

#### Alertas (Manager view)

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/analysis/alerts` | Alertas consolidados: bloco **geral** (empresa) e, opcionalmente, bloco **squad** |

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `manager` | string (query, opcional) | Quando informado, a resposta inclui `squad` com os mesmos indicadores filtrados a esse manager (mesmo critério de `scope=squad` nos endpoints de pipeline). |

**Response `GET /analysis/alerts`:**

- `geral`: `{ scope, total_alerts, triggered_count, alerts[] }` — sempre presente; pipeline e deals pontuados em toda a base.
- `squad`: mesmo formato, mais `manager`, ou `null` se o parâmetro `manager` não foi enviado.

Cada item de `alerts` inclui `key`, `severity`, `triggered`, `title`, `message` e `data`.

---

#### Pipeline

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/analysis/pipeline` | Distribuição de deals por estágio do funil |
| GET | `/analysis/pipeline/time-medians` | Medianas de dias no pipeline por estágio (Won/Lost/Engaging) e ratio Engaging/Won |
| GET | `/analysis/pipeline/win-rate-by-time-bucket` | Win rate (%) por faixa de dias no pipeline para deals fechados |

Todos os endpoints de pipeline aceitam:

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `scope` | string | `geral` (padrão) · `squad` |
| `manager` | string | Obrigatório quando `scope=squad` |

**Response `GET /analysis/pipeline`:**
```json
{
  "total_deals": 400,
  "stages": {
    "Prospecting": { "count": 120, "pct": 30.0 },
    "Engaging":    { "count": 100, "pct": 25.0 },
    "Won":         { "count": 110, "pct": 27.5 },
    "Lost":        { "count": 70,  "pct": 17.5 }
  }
}
```

**Response `GET /analysis/pipeline/time-medians`:**
```json
{
  "scope": "squad",
  "manager": "João",
  "won_median_days": 45.0,
  "lost_median_days": 60.0,
  "engaging_median_days": 72.0,
  "engaging_to_won_ratio": 1.6,
  "cohort_counts": { "total": 400, "won": 110, "lost": 70, "engaging": 100 }
}
```

**Response `GET /analysis/pipeline/win-rate-by-time-bucket`:**
```json
{
  "scope": "geral",
  "manager": null,
  "benchmark_global_wr": 42.5,
  "scoped_closed_win_rate": 44.1,
  "buckets": [
    { "label": "0–30d", "win_rate": 60.0, "total": 20 }
  ]
}
```

---

#### Transferências

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/analysis/transfers` | Deals candidatos a redistribuição (TRANSFER + CONSIDER_TRANSFER), ordenados por score |

**Response `GET /analysis/transfers`:**
```json
{
  "total_transfers": 18,
  "deals": [
    {
      "opportunity_id": "string",
      "sales_agent": "string",
      "product": "string",
      "account": "string",
      "score": 81.2,
      "viability": 32.0,
      "action": "TRANSFER",
      "message": "string",
      "details": {
        "target_seller": "string",
        "transfer_level": "same_team | same_region | other_region",
        "why_this_helps": ["string"],
        "your_context":   { "viability": 28.0 },
        "target_context": { "viability": 61.0 }
      }
    }
  ]
}
```

---

#### Regional

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/analysis/regional` | Overview de todas as regiões: métricas, insights e transferências inter-regionais |
| GET | `/analysis/regional/{region}` | Drill-down de uma região específica com métricas por vendedor |

`GET /analysis/regional` aceita `scope` e `manager` (mesmo padrão dos endpoints de pipeline).

**Response `GET /analysis/regional` (resumido):**
```json
{
  "global_wr": 42.5,
  "regions": [
    {
      "region": "São Paulo",
      "deals_engaging": 40,
      "sellers_count": 5,
      "avg_score": 68.1,
      "avg_viability": 55.3,
      "win_rate": 48.0,
      "avg_load_per_seller": 8.0,
      "avg_prospecting_per_seller": 3.2,
      "discard_pct": 12.5,
      "transfer_pct": 17.5,
      "actions": { "PUSH_HARD": 10, "TRANSFER": 7 }
    }
  ],
  "insights": {
    "best_region":  { "region": "string", "win_rate": 55.0 },
    "worst_region": { "region": "string", "win_rate": 28.0 },
    "load_imbalance": {
      "detected": true,
      "ratio": 2.1,
      "most_loaded":  { "region": "string", "avg_load_per_seller": 12.0 },
      "least_loaded": { "region": "string", "avg_load_per_seller": 5.7 }
    }
  },
  "inter_regional_transfers": {
    "total_transfers": 18,
    "inter_regional_count": 6,
    "inter_regional_pct": 33.3
  }
}
```

---

#### Produtos (Analysis)

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/analysis/products` | Overview de todos os produtos: métricas, ciclo de tempo, especialistas |
| GET | `/analysis/products/{product}` | Drill-down de um produto com lista de deals em Engaging |

`GET /analysis/products` aceita `scope` e `manager` (mesmo padrão dos endpoints de pipeline).

**Response `GET /analysis/products` (resumido):**
```json
{
  "global_wr": 42.5,
  "products": [
    {
      "product": "Produto X",
      "deals_engaging": 22,
      "avg_score": 71.0,
      "win_rate": 50.0,
      "avg_ticket": 15000.0,
      "avg_days_engaging": 90.0,
      "avg_cycle_days_won": 55.0,
      "cycle_ratio": 1.64,
      "discard_pct": 9.1,
      "transfer_pct": 18.2,
      "actions": { "PUSH_HARD": 8, "TRANSFER": 4 }
    }
  ],
  "insights": {
    "best_product":  { "product": "string", "win_rate": 60.0 },
    "worst_product": { "product": "string", "win_rate": 25.0 },
    "most_stuck": { "product": "string", "avg_days_engaging": 110.0, "ratio": 2.0 },
    "high_discard_warning": { "product": "string", "discard_pct": 38.0 }
  },
  "specialists": [
    { "product": "string", "sales_agent": "string", "combo_wr": 72.0, "seller_avg_wr": 45.0, "delta": 27.0 }
  ]
}
```

---

#### Série Temporal

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/analysis/sellers/won-value-over-time` | Série temporal de valor convertido (Won) por dia de um vendedor |

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `sales_agent` | string | **Obrigatório.** Nome do vendedor |

**Response:**
```json
{
  "sales_agent": "string",
  "date_range": { "min": "2024-01-05", "max": "2024-12-20" },
  "points": [
    { "date": "2024-03-10", "value": 25000.0, "count": 2 }
  ]
}
```
