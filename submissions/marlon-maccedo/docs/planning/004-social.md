# Plan 004 — Social Dashboard

> Status: pronto para implementar
> Quarto desafio — o mais visual, 52K posts cross-platform

---

## Contexto e decisão de arquitetura

O Head de Marketing quer três respostas: o que gera engajamento, se patrocínio vale a pena, e qual a estratégia de conteúdo. A armadilha óbvia é dizer "vídeos performam melhor" — isso qualquer IA diz. O diferencial é controlar por plataforma, creator size e categoria antes de qualquer conclusão.

52K posts é grande demais para o client. DuckDB server-side agrega tudo — o client recebe apenas os sumários necessários para cada view. Nenhuma rota retorna mais que ~200 registros.

---

## Estrutura de rotas

```
/                   → redirect → /overview
/overview           → sumário executivo: top insights + headline numbers
/performance        → análise de engajamento: plataforma × conteúdo × creator size
/sponsorship        → orgânico vs. patrocinado (comparação controlada por contexto)
/audience           → perfil de audiência por plataforma e conteúdo
/strategy           → recomendações priorizadas com evidências dos dados
```

---

## API routes

### Overview

```
GET /api/overview
→ {
    totalPosts: 52000,
    platforms: ['YouTube', 'TikTok', 'Instagram', 'Bilibili', 'RedNote'],
    avgEngagementRate: 0.048,
    sponsoredShare: 0.31,         // 31% dos posts são patrocinados
    topPlatformByEngagement,
    topContentTypeByEngagement,
    bestCreatorTier,              // nano/micro/macro/mega
    headlineInsights: []          // 3 achados calculados dos dados reais — definidos após exploração
  }
```

### Performance

```
GET /api/performance/matrix
→ array de {
    platform,
    content_type,
    creator_tier,        // nano | micro | macro | mega
    post_count,
    avg_engagement_rate,
    avg_views,
    avg_interactions,    // likes + shares + comments
    median_engagement    // mediana, não média (resistente a outliers)
  }
  filtrado: HAVING post_count > 30 (mínimo estatístico)

GET /api/performance/by-category?platform=X
→ array de {
    category,
    post_count,
    avg_engagement_rate,
    avg_shares,          // shares = intenção real, não vanity metric
    top_content_type     // qual content_type domina nessa categoria
  }

GET /api/performance/time-patterns
→ {
    byDayOfWeek: [{ day, avg_engagement }],
    byHour:      [{ hour, avg_engagement }],
    byLanguage:  [{ language, platform, avg_engagement, post_count }]
  }
```

**Query principal — matrix de performance:**

```sql
SELECT
  platform,
  content_type,
  CASE
    WHEN follower_count < 10000   THEN 'nano (<10K)'
    WHEN follower_count < 100000  THEN 'micro (10K-100K)'
    WHEN follower_count < 1000000 THEN 'macro (100K-1M)'
    ELSE                               'mega (>1M)'
  END AS creator_tier,
  COUNT(*)                                  AS post_count,
  ROUND(AVG(engagement_rate), 4)            AS avg_engagement_rate,
  ROUND(MEDIAN(engagement_rate), 4)         AS median_engagement_rate,
  ROUND(AVG(views), 0)                      AS avg_views,
  ROUND(AVG(likes + shares + comments), 0)  AS avg_interactions,
  ROUND(AVG(shares), 0)                     AS avg_shares
FROM read_csv_auto('/data/social_media_posts.csv')
GROUP BY platform, content_type, creator_tier
HAVING COUNT(*) > 30
ORDER BY avg_engagement_rate DESC
```

### Sponsorship

A comparação justa é o coração desta análise. Comparar orgânico vs. patrocinado sem controlar por contexto é falso — um micro-creator patrocinado no TikTok não pode ser comparado com um mega-creator orgânico no YouTube.

```
GET /api/sponsorship/comparison
→ array de {
    platform,
    content_type,
    creator_tier,
    organic_posts,
    sponsored_posts,
    organic_avg_engagement,
    sponsored_avg_engagement,
    delta_pct,              // (sponsored - organic) / organic × 100
    organic_avg_views,
    sponsored_avg_views,
    disclosure_type         // quando disponível
  }
  filtrado: HAVING organic_posts > 20 AND sponsored_posts > 20

GET /api/sponsorship/by-category
→ array de {
    sponsor_category,
    post_count,
    avg_engagement_rate,
    avg_views,
    best_platform,
    best_creator_tier
  }
  → quais categorias de patrocinador geram melhor resultado
```

**Query de comparação controlada:**

```sql
WITH base AS (
  SELECT
    platform,
    content_type,
    CASE
      WHEN follower_count < 10000   THEN 'nano'
      WHEN follower_count < 100000  THEN 'micro'
      WHEN follower_count < 1000000 THEN 'macro'
      ELSE                               'mega'
    END AS creator_tier,
    is_sponsored,
    engagement_rate,
    views
  FROM read_csv_auto('/data/social_media_posts.csv')
)
SELECT
  platform,
  content_type,
  creator_tier,
  COUNT(*) FILTER (WHERE NOT is_sponsored)   AS organic_posts,
  COUNT(*) FILTER (WHERE is_sponsored)       AS sponsored_posts,
  AVG(engagement_rate) FILTER (WHERE NOT is_sponsored) AS organic_eng,
  AVG(engagement_rate) FILTER (WHERE is_sponsored)     AS sponsored_eng,
  ROUND(
    (AVG(engagement_rate) FILTER (WHERE is_sponsored) -
     AVG(engagement_rate) FILTER (WHERE NOT is_sponsored))
    / NULLIF(AVG(engagement_rate) FILTER (WHERE NOT is_sponsored), 0) * 100
  , 1) AS delta_pct
FROM base
GROUP BY platform, content_type, creator_tier
HAVING
  COUNT(*) FILTER (WHERE NOT is_sponsored) > 20
  AND COUNT(*) FILTER (WHERE is_sponsored) > 20
ORDER BY ABS(delta_pct) DESC
```

### Audience

```
GET /api/audience/demographics
→ {
    byPlatform: [
      {
        platform,
        age_18_24_pct,
        age_25_34_pct,
        age_35_44_pct,
        age_45_plus_pct,
        gender_female_pct,
        gender_male_pct,
        top_locations: []
      }
    ],
    byContentType: [
      { content_type, dominant_age_group, avg_engagement_by_age }
    ]
  }
```

---

## Componentes de UI

### `/overview` — Sumário executivo

**5 KPIs rápidos:**
- Total de posts analisados
- Plataforma com maior engajamento médio
- Melhor tier de creator (nano/micro/macro/mega)
- % de posts patrocinados
- Impacto médio do patrocínio no engajamento (delta %)

**3 cards de insight** — estrutura pronta, conteúdo preenchido após exploração dos dados reais.

### `/performance` — Análise de engajamento

**Heatmap principal:**
- Linhas: plataformas
- Colunas: tipos de conteúdo (Video, Image, Text, Mixed)
- Célula: avg engagement rate (cor por intensidade)
- Tooltip: post_count, avg_views, avg_shares

**Selector de creator tier** — filtra o heatmap por tier: mostra que a mesma combinação plataforma × conteúdo tem resultado diferente por tamanho de creator

**Gráfico de shares por categoria:**
- Shares escolhidos sobre likes/comments: intenção de amplificação, não vanity
- Bar chart ordenado por avg_shares
- Permite ver quais categorias realmente se propagam

**Padrões temporais:**
- Heatmap dia × hora com engajamento médio
- Por plataforma (comportamento diferente em cada uma)

### `/sponsorship` — Orgânico vs. patrocinado

**Mensagem principal:** a comparação é controlada — comparamos criadores do mesmo tier, na mesma plataforma, com o mesmo tipo de conteúdo.

**Gráfico de barras agrupadas:**
- Grupos: plataforma × creator_tier
- Barras: orgânico vs. patrocinado
- Cor do delta: verde se patrocinado > orgânico, vermelho se <

**Tabela de sponsor categories:**
- Quais categorias de patrocinador geram melhor resultado por plataforma
- Ex: "Tech sponsors em TikTok com micro-creators → +12% vs. orgânico"

**Card de política recomendada** — estrutura pronta, conclusões definidas após ver os deltas reais.

### `/audience` — Perfil de audiência

**Stacked bar por plataforma:**
- Distribuição de idade em cada plataforma
- Mostra qual plataforma tem qual persona

**Scatter — audiência vs. engajamento:**
- Eixo X: % audiência feminina
- Eixo Y: avg engagement rate
- Por plataforma + content type
- Revela se há correlação entre perfil demográfico e performance

### `/strategy` — Recomendações

A página mais importante. Estrutura deliberada:

> **Conteúdo definido após análise dos dados reais.**

A estrutura da página é:

**1. Onde concentrar esforço** — top 3 combinações plataforma × content_type × creator_tier por engajamento, com volume mínimo para ser estatisticamente válido

**2. Política de patrocínio** — baseada no delta real orgânico vs. patrocinado da rota `/api/sponsorship/comparison`

**3. O que parar de fazer** — combinações com alto volume e baixo retorno, identificadas na matriz de performance

**4. Quick wins** — ações concretas derivadas dos dados, definidas após exploração

---

## Estrutura de arquivos da app

```
apps/social-dashboard/
├── data/                              # CSV aqui (gitignored, Railway Volume)
│   └── social_media_posts.csv        # ~52K posts
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                  # redirect → /overview
│   │   ├── overview/page.tsx
│   │   ├── performance/page.tsx
│   │   ├── sponsorship/page.tsx
│   │   ├── audience/page.tsx
│   │   └── strategy/page.tsx
│   ├── api/
│   │   ├── overview/route.ts
│   │   ├── performance/
│   │   │   ├── matrix/route.ts
│   │   │   ├── by-category/route.ts
│   │   │   └── time-patterns/route.ts
│   │   ├── sponsorship/
│   │   │   ├── comparison/route.ts
│   │   │   └── by-category/route.ts
│   │   └── audience/
│   │       └── demographics/route.ts
│   ├── components/
│   │   ├── EngagementHeatmap.tsx
│   │   ├── SponsorshipBarChart.tsx
│   │   ├── CreatorTierSelector.tsx
│   │   ├── AudienceStackedBar.tsx
│   │   ├── InsightCard.tsx
│   │   ├── StrategyCard.tsx          # card de recomendação com evidência inline
│   │   └── PlatformFilter.tsx
│   └── lib/
│       └── duckdb.ts
├── package.json
└── next.config.ts
```

---

## Cuidados analíticos documentados no process log

**Viés de survivorship:** posts com zero engajamento podem estar subrepresentados. Documentar se o dataset inclui posts com 0 views ou começa de um mínimo.

**Engagement rate vs. volume:** um post com 0.15 engagement rate e 100 views é diferente de 0.15 com 1M views. As análises precisam contextualizar ambos.

**Média vs. mediana:** distribuições de engajamento são assimétricas (poucos posts virais distorcem a média). Usar mediana onde isso importa — e documentar a escolha.

**Janela temporal:** se o dataset cobre múltiplos anos, algoritmos das plataformas mudaram. Idealmente segmentar por período. Documentar se não for possível.

---

## O que vai no process log

- Screenshot da exploração inicial: distribuição de engajamento por plataforma (assimétrica — documentar a surpresa)
- Momento em que decidi usar mediana em vez de média e por quê
- A comparação controlada de patrocínio: antes (sem controle) vs. depois (com controle por tier/plataforma) — os números mudam
- Screenshot do heatmap de performance com dados reais
- O achado mais contraintuitivo do dataset (micro vs. mega creators ou algo similar)
- Rascunho das recomendações vs. versão final — mostrar a iteração

---

## Dependências

```json
{
  "@duckdb/node-api": "latest",
  "recharts": "^2",
  "next": "15",
  "tailwindcss": "^4"
}
```
