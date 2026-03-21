# Plan 001 — Churn Dashboard

> Status: pronto para implementar
> Terceiro desafio — o mais analítico, depende de cruzar 5 tabelas

---

## Contexto e decisão de arquitetura

O CEO quer respostas para três perguntas: o que está causando o churn, quais segmentos estão em risco, e o que fazer. A app estrutura exatamente isso em rotas separadas. O diferencial é cruzar as 5 tabelas — a maioria das análises rasas olha só uma.

O ponto-chave levantado pelo CEO: *"o time de produto diz que o uso cresceu"* — isso precisa ser verificado com dados segmentados. Crescimento médio pode esconder queda nos segmentos que mais churnaram.

DuckDB server-side faz todos os joins. As queries são pesadas (join de 5 tabelas com ~32K registros total) mas executam em milissegundos no DuckDB. Resultados cacheados em memória por rota.

---

## Estrutura de rotas

```
/                     → redirect → /overview
/overview             → sumário executivo: KPIs, top 3 achados, recomendações rápidas
/segments             → churn por segmento: indústria, país, plano, canal de aquisição
/behavior             → uso de features: churned vs. retained (aqui mora a resposta real)
/accounts             → tabela de contas ativas em risco com score e fatores
/recommendations      → plano de ação priorizado com impacto estimado
```

---

## Datasets e joins

```
ravenstack_accounts (~500)          ← ponto de entrada principal
         ↓ account_id
ravenstack_subscriptions (~5K)      ← MRR, ARR, plano, upgrades/downgrades
         ↓ subscription_id
ravenstack_feature_usage (~25K)     ← uso diário por feature
         ↓ account_id
ravenstack_support_tickets (~2K)    ← CSAT, tempo de resolução, escalações
         ↓ account_id
ravenstack_churn_events (~600)      ← reason code, feedback em texto (só churned)
```

---

## API routes

### Overview

```
GET /api/overview
→ {
    totalAccounts,
    churnRate,               // churned / total
    mrrAtRisk,               // MRR das contas ativas com risk score acima do threshold
    mrrLostToChurn,          // MRR das contas que já churnearam
    avgMrrChurned,           // vs avgMrrRetained — diferença a ser descoberta nos dados
    topChurnReasons: [       // do ravenstack_churn_events.reason_code, ordenado por count
      { reason, count, mrrLost }
    ],
    usageBySegment: [        // para responder o CEO: uso cresceu pra quem?
      { segment, avgUsageRecent, avgUsagePrevious, delta_pct }
    ]
  }
```

> Os números e o que revelam só vamos saber ao conectar os dados reais.

### Churn por segmento

```
GET /api/segments?dimension=industry|country|plan|channel
→ array de {
    segment,
    totalAccounts,
    churnedAccounts,
    churnRate,
    mrrLost,
    avgMrrChurned,
    avgMrrRetained
  }
  ordenado por mrrLost DESC (churn ponderado por valor, não por volume)
```

**Query exemplo (por indústria):**

```sql
SELECT
  a.industry,
  COUNT(DISTINCT a.account_id)                                         AS total_accounts,
  COUNT(DISTINCT ce.account_id)                                        AS churned_accounts,
  ROUND(COUNT(DISTINCT ce.account_id) * 100.0 / COUNT(DISTINCT a.account_id), 1) AS churn_rate_pct,
  COALESCE(SUM(ce.refund_value), 0)                                    AS mrr_lost,
  AVG(CASE WHEN ce.account_id IS NOT NULL THEN s.mrr END)              AS avg_mrr_churned,
  AVG(CASE WHEN ce.account_id IS NULL     THEN s.mrr END)              AS avg_mrr_retained
FROM read_csv_auto('/data/ravenstack_accounts.csv') a
LEFT JOIN read_csv_auto('/data/ravenstack_subscriptions.csv')  s  ON a.account_id = s.account_id
LEFT JOIN read_csv_auto('/data/ravenstack_churn_events.csv')   ce ON a.account_id = ce.account_id
GROUP BY a.industry
ORDER BY mrr_lost DESC
```

### Comportamento: churned vs. retained

```
GET /api/behavior
→ {
    features: [
      {
        feature_name,
        avgUsageChurned,     // média diária nos 90 dias antes do churn
        avgUsageRetained,    // média diária do mesmo período
        ratio,               // retained/churned — quanto mais alto, mais preditivo
        isBetaFeature
      }
    ],
    usageTrend: {
      churned:  [{ week: -12, avgUsage: 18 }, ..., { week: -1, avgUsage: 4 }],
      retained: [{ week: -12, avgUsage: 16 }, ..., { week: -1, avgUsage: 22 }]
    },
    supportCorrelation: {
      avgTicketsChurned: 4.2,
      avgTicketsRetained: 1.8,
      avgCsatChurned: 2.1,
      avgCsatRetained: 4.1,
      escalationRateChurned: 0.38
    }
  }
```

Este é o cruzamento mais revelador: a curva de uso das contas que churnearam cai nas semanas antes do churn — isso é o "sinal precoce" que o CS pode monitorar.

### Contas em risco

```
GET /api/accounts/at-risk
→ array de {
    account_id,
    industry,
    country,
    mrr,
    billingFrequency,
    riskScore,        // 0-100
    riskLabel,        // "critical" | "high" | "medium"
    riskFactors: [    // os fatores que mais pesam no score
      "Uso caiu 65% nos últimos 30 dias",
      "3 escalações de suporte abertas",
      "Plano mensal sem renovação próxima"
    ]
  }
  filtrado: só contas ativas (não churneadas)
  ordenado por (riskScore × mrr) DESC — prioriza risco ponderado por valor
```

```
GET /api/accounts/[id]
→ {
    account,          // dados da conta
    subscription,     // MRR, plano, histórico de upgrades/downgrades
    usageLast90Days,  // array de { date, featureName, usageCount }
    supportHistory,   // tickets ordenados por data, com CSAT e status
    riskBreakdown     // score por componente (igual ao lead scorer: explicável)
  }
```

---

## Lógica de risk score

```sql
-- Executado sobre contas ativas (sem churn_event)
SELECT
  a.account_id,
  s.mrr,
  s.billing_frequency,

  -- Tendência de uso: compara últimos 30 dias vs. 30 dias anteriores
  COALESCE(recent.avg_usage, 0)   AS usage_last30,
  COALESCE(previous.avg_usage, 0) AS usage_prev30,

  ROUND(
    -- Queda de uso (0-35 pts)
    CASE
      WHEN COALESCE(recent.avg_usage, 0) = 0                            THEN 35
      WHEN COALESCE(previous.avg_usage, 1) > 0
        AND (recent.avg_usage / previous.avg_usage) < 0.5               THEN 30
      WHEN (recent.avg_usage / NULLIF(previous.avg_usage, 0)) < 0.75    THEN 15
      ELSE 0
    END

    -- CSAT de suporte ruim (0-25 pts)
    + CASE
        WHEN COALESCE(AVG(t.satisfaction_score), 5) < 2 THEN 25
        WHEN COALESCE(AVG(t.satisfaction_score), 5) < 3 THEN 12
        ELSE 0
      END

    -- Escalações (0-20 pts)
    + LEAST(20, COUNT(t.escalation_flag) FILTER (WHERE t.escalation_flag = true) * 7)

    -- Plano mensal sem renovação próxima (0-15 pts)
    + CASE WHEN s.billing_frequency = 'Monthly' THEN 15 ELSE 0 END

    -- Downgrade recente (0-10 pts)
    + CASE WHEN s.downgrade_count > 0 THEN 10 ELSE 0 END

  , 1) AS risk_score

FROM read_csv_auto('/data/ravenstack_accounts.csv') a
LEFT JOIN read_csv_auto('/data/ravenstack_subscriptions.csv')   s       ON a.account_id = s.account_id
LEFT JOIN read_csv_auto('/data/ravenstack_support_tickets.csv') t       ON a.account_id = t.account_id
LEFT JOIN (
  -- uso médio nos últimos 30 dias
  SELECT subscription_id, AVG(usage_count) AS avg_usage
  FROM read_csv_auto('/data/ravenstack_feature_usage.csv')
  WHERE usage_date >= CURRENT_DATE - INTERVAL 30 DAY
  GROUP BY subscription_id
) recent   ON s.subscription_id = recent.subscription_id
LEFT JOIN (
  -- uso médio nos 30 dias anteriores (30-60 dias atrás)
  SELECT subscription_id, AVG(usage_count) AS avg_usage
  FROM read_csv_auto('/data/ravenstack_feature_usage.csv')
  WHERE usage_date BETWEEN CURRENT_DATE - INTERVAL 60 DAY
                       AND CURRENT_DATE - INTERVAL 30 DAY
  GROUP BY subscription_id
) previous ON s.subscription_id = previous.subscription_id
WHERE a.is_churned = false
GROUP BY a.account_id, a.industry, a.country, s.mrr, s.billing_frequency,
         s.downgrade_count, recent.avg_usage, previous.avg_usage
ORDER BY risk_score DESC
```

| Componente | Peso máx | Raciocínio |
|------------|----------|------------|
| Queda de uso | 35 pts | Maior preditor de churn nos dados |
| CSAT de suporte | 25 pts | Insatisfação com suporte precede saída |
| Escalações | 20 pts | Sinal de problema grave não resolvido |
| Plano mensal | 15 pts | Sem lock-in, fricção de saída mínima |
| Downgrade recente | 10 pts | Sinal de redução de comprometimento |

---

## Componentes de UI

### `/overview` — Sumário executivo

**4 KPIs:**
- Churn rate (%)
- MRR perdido no período
- MRR em risco (contas ativas com score acima do threshold)
- CSAT médio pré-churn vs. contas retidas

**Top 3 achados** (cards com dados):
- Estrutura pronta, conteúdo preenchido após exploração dos dados reais
- Um dos cards responde diretamente ao CEO: "uso cresceu" é verdade pra quais segmentos?

**Alerta sobre a afirmação do CEO** (card destacado):
- Query `usageBySegment` no overview decompõe o crescimento de uso por segmento
- A conclusão — cresceu pra todos, só para alguns, ou caiu para os churned — vem dos dados

### `/segments` — Churn por segmento

- Selector de dimensão: Indústria / País / Plano / Canal de Aquisição
- Bar chart: churn rate por segmento (ordenado por MRR perdido, não volume)
- Tabela abaixo com todos os números
- Destaque visual nos segmentos de maior risco ponderado

### `/behavior` — Uso de features

**Gráfico de linha principal:**
- Eixo X: semanas relativas ao churn (semana -12 até -1)
- Duas linhas: contas que churnearam vs. que ficaram
- Mostra a divergência crescente — o "sinal precoce"

**Tabela de features:**
- Quais features os retidos usam mais que os churned
- Ordenada por `ratio` — features com maior poder preditivo no topo
- Beta features destacadas (potencial problema de produto)

**Cards de correlação com suporte:**
- Tickets médios: churned vs. retained
- CSAT médio: churned vs. retained
- Taxa de escalação

### `/accounts` — Contas em risco

- Tabela TanStack: account, indústria, MRR, score de risco (badge colorido), fatores principais
- Filtros: indústria, país, faixa de MRR, faixa de score
- Ordenação padrão: `risk_score × mrr` DESC (prioridade real para o CS)
- Click → `/accounts/[id]` com detalhe completo

### `/recommendations` — Plano de ação

> **Conteúdo definido após análise dos dados reais.**

A estrutura da página é:
- Cards priorizados por impacto (urgência × MRR em risco)
- Cada card tem: achado dos dados → ação concreta → impacto estimado
- Categorias prováveis: intervenção imediata em contas de alto risco, mudança de processo, investigação com produto

Os cards serão montados a partir do que os dados revelarem em `/segments`, `/behavior` e `/accounts`.

---

## Estrutura de arquivos da app

```
apps/churn-dashboard/
├── data/                              # CSVs aqui (gitignored, Railway Volume)
│   ├── ravenstack_accounts.csv
│   ├── ravenstack_subscriptions.csv
│   ├── ravenstack_feature_usage.csv
│   ├── ravenstack_support_tickets.csv
│   └── ravenstack_churn_events.csv
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                   # redirect → /overview
│   │   ├── overview/page.tsx
│   │   ├── segments/page.tsx
│   │   ├── behavior/page.tsx
│   │   ├── accounts/
│   │   │   ├── page.tsx
│   │   │   └── [id]/page.tsx
│   │   └── recommendations/page.tsx
│   ├── api/
│   │   ├── overview/route.ts
│   │   ├── segments/route.ts          # ?dimension=industry|country|plan|channel
│   │   ├── behavior/route.ts
│   │   └── accounts/
│   │       ├── at-risk/route.ts
│   │       └── [id]/route.ts
│   ├── components/
│   │   ├── KPICard.tsx
│   │   ├── UsageTrendChart.tsx        # linha dupla: churned vs retained
│   │   ├── SegmentBarChart.tsx
│   │   ├── FeatureTable.tsx
│   │   ├── RiskTable.tsx
│   │   ├── RiskScoreBreakdown.tsx     # igual ao ScoreCard do lead scorer
│   │   └── RecommendationCard.tsx
│   └── lib/
│       └── duckdb.ts
├── package.json
└── next.config.ts
```

---

## O que vai no process log

- Screenshot da exploração inicial: `SELECT * FROM ... LIMIT 10` nas 5 tabelas — entender o schema real antes de qualquer análise
- Queries de exploração e o que cada uma revelou (documentar ao vivo, não reconstituir)
- Iteração no risk score: pesos iniciais vs. ajustes após ver a distribuição real dos dados
- Screenshot da curva de uso churned vs. retained — seja qual for o resultado
- O achado mais surpreendente — documentado no momento em que aparecer
- A resposta à pergunta do CEO sobre uso, com query e resultado

---

## Dependências

```json
{
  "@duckdb/node-api": "latest",
  "recharts": "^2",
  "@tanstack/react-table": "^8",
  "next": "15",
  "tailwindcss": "^4"
}
```
