# Documentacao Tecnica — Scoring Engine v5

## Visao geral

O scoring engine e um script Python que consome dados de CRM e gera um JSON com deals priorizados. Ele nao usa machine learning — usa heuristicas calibradas com cascata hierarquica de confianca.

**Input:** 4 tabelas CSV (pipeline, accounts, products, sales_teams) via API Kaggle ou fallback local.
**Output:** `scored_deals.json` com 2.089 deals ativos scorados + 6.711 deals fechados (backtest) + estatisticas de referencia.

---

## Fonte de dados

```python
import kagglehub
from kagglehub import KaggleDatasetAdapter

dataset = "agungpambudi/crm-sales-predictive-analytics"
pipeline = kagglehub.load_dataset(KaggleDatasetAdapter.PANDAS, dataset, "sales_pipeline.csv")
accounts  = kagglehub.load_dataset(KaggleDatasetAdapter.PANDAS, dataset, "accounts.csv")
products  = kagglehub.load_dataset(KaggleDatasetAdapter.PANDAS, dataset, "products.csv")
teams     = kagglehub.load_dataset(KaggleDatasetAdapter.PANDAS, dataset, "sales_teams.csv")
```

Se a API falha, carrega CSVs de `data/`.

---

## Arquitetura do score

Cada deal recebe 3 componentes independentes que sao combinados em uma prioridade final:

```
priority = 0.55 * quality + 0.25 * urgency + 0.20 * impact
```

### 1. Quality (chance de fechar)

5 sinais com cascata hierarquica de confianca:

| Sinal | Peso | Threshold | Fallback |
|-------|------|-----------|----------|
| Taxa do vendedor | 30% | 20 deals | Media global (63.2%) |
| Vendedor x Produto | 25% | 10 deals | 50% taxa_vendedor + 50% taxa_produto |
| Relacionamento (conta) | 25% | 5 deals | Cascata: Vendedor-Conta > Gestor-Conta > Vendedor-Setor > Global |
| Taxa do produto | 10% | — | Estavel (todos >500 deals) |
| Sazonalidade (mes) | 10% | 100 deals | Media global |

**Mecanica de confianca:**

```python
confidence = min(1.0, n_deals / threshold)
blended = confidence * taxa_raw + (1 - confidence) * taxa_fallback
```

Usa taxas RAW (nao bayesianas) no blend. A cascata de confianca ja regulariza — aplicar suavizacao bayesiana antes causava dupla-suavizacao (comprimia tudo para a media).

**Cascata de relacionamento (para o sinal de 25%):**

```
1. Vendedor ja vendeu para esta conta? → taxa_raw do par
2. Gestor do vendedor ja vendeu para esta conta? → taxa_raw do gestor-conta
3. Vendedor vende no setor desta conta? → taxa_raw vendedor-setor
4. Nenhum historico (ou deal sem conta) → media global
```

Cada nivel so e usado se o anterior nao tem dados suficientes (threshold = 5 deals).

### 2. Urgency (urgencia temporal)

Baseada na distribuicao real dos deals Won:

| Faixa | Dias | Score | Base nos dados |
|-------|------|-------|----------------|
| Normal | 0-30 | 0.3 | 43% dos Won fecham aqui |
| Mediana | 31-60 | 0.5 | Proximo da mediana (57d) |
| Atencao | 61-90 | 0.7 | 77% dos Won ja fecharam |
| Urgente | 91-120 | 0.9 | So 20% fecham tao tarde |
| Resgate | >120 | 1.0 | <4% dos Won |

Para deals em Prospecting sem engage_date: score fixo 0.4.

### 3. Impact (valor)

Normalizado 0-1 entre min ($55, MG Special) e max ($26,768, GTK 500):

```python
impact = (price - min_price) / (max_price - min_price)
```

Componente menos discriminante, mas disponivel para 100% dos deals.

---

## Baldes de acao

Apos calcular quality, urgency e priority, cada deal e classificado em um balde:

| Balde | Regra | Significado |
|-------|-------|-------------|
| Atacar Agora | quality >= 0.60 E urgency >= 0.5 | Alta chance + timing ideal |
| Resgatar Hoje | quality >= 0.45 E dias > 90 | Potencial real, mas esfriando |
| Avancar Qualificacao | quality >= 0.55 E urgency < 0.5 | Boa chance, ainda cedo |
| Trabalhar Esta Semana | quality >= 0.45 | Chance moderada, manter ritmo |
| Limpar Pipeline | quality < 0.45 E dias > 90 | Baixa chance + tempo excessivo |
| Nutrir | demais | Fase inicial ou chance baixa |

A avaliacao e sequencial (primeiro match ganha).

---

## Output (scored_deals.json)

```json
{
  "generated_at": "2026-04-13T15:48:00",
  "engine_version": "v5",
  "total_active": 2089,
  "total_closed": 6711,
  "global_win_rate": 0.632,
  "accuracy": 0.636,
  "active_deals": [
    {
      "id": "DWUXMAGZ",
      "agent": "Corliss Cosme",
      "manager": "Melvin Marxen",
      "office": "Central",
      "account": "...",
      "account_missing": false,
      "sector": "technology",
      "tier": "enterprise",
      "product": "GTX Plus Pro",
      "price": 5482,
      "stage": "Engaging",
      "age_days": 135,
      "quality": 0.58,
      "urgency": 0.9,
      "impact": 0.20,
      "priority": 0.585,
      "action": "Resgatar Hoje",
      "human_quality": "Chance razoavel...",
      "signals": {
        "agent_rate": 0.52,
        "agent_product_rate": 0.55,
        "relationship_rate": 0.63,
        "product_rate": 0.61,
        "seasonality_rate": 0.64
      }
    }
  ],
  "closed_deals": [...],
  "agent_stats": {...},
  "refs": {...},
  "deciles": [...]
}
```

### Campos por deal

| Campo | Tipo | Descricao |
|-------|------|-----------|
| id | string | Opportunity ID do CRM |
| agent | string | Nome do vendedor |
| manager | string | Gestor do vendedor |
| office | string | Escritorio regional |
| account | string | Nome da conta (ou texto indicando ausencia) |
| account_missing | bool | true se deal nao tem conta no CRM |
| sector | string | Setor da conta (ou "—") |
| tier | string | Porte da conta (ou "—") |
| product | string | Produto do deal |
| price | number | Valor do produto |
| stage | string | "Prospecting" ou "Engaging" |
| age_days | number | Dias desde engage_date (0 se Prospecting) |
| quality | float | Chance de fechar (0-1) |
| urgency | float | Urgencia temporal (0-1) |
| impact | float | Valor normalizado (0-1) |
| priority | float | Score final composto (0-1) |
| action | string | Balde de acao |
| human_quality | string | Explicacao em linguagem simples |
| signals | object | Taxas individuais dos 5 sinais |

---

## Backtest

O motor e validado nos 6.711 deals fechados (Won + Lost). Metrica principal: precisao do ranking — deals com score mais alto devem ter win rate mais alto.

**Resultado v5:**

| Decil | Win Rate | N deals | Score medio |
|-------|----------|---------|-------------|
| D1 (top) | 82.0% | 671 | 0.569 |
| D2 | 75.3% | 671 | 0.522 |
| D3 | 70.8% | 671 | 0.504 |
| D4 | 66.6% | 671 | 0.490 |
| D5 | 66.6% | 671 | 0.478 |
| D6 | 60.2% | 671 | 0.467 |
| D7 | 57.7% | 671 | 0.455 |
| D8 | 58.3% | 671 | 0.443 |
| D9 | 55.1% | 671 | 0.426 |
| D10 (bottom) | 39.0% | 672 | 0.398 |

Separacao monotonica (D7/D8 com inversao minima de 0.6pp). Spread total: 43 pontos percentuais.

---

## Dependencias

```
pandas
numpy
kagglehub
```

Python 3.9+. Sem frameworks de ML.

---

## Como re-rodar

```bash
cd submissions/pedro-lima/solution
python3 scoring_engine.py
```

Output: `data/scored_deals.json` (~7.5 MB)

Tempo de execucao: ~5 segundos.
