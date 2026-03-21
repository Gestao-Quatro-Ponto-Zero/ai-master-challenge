# Social Dashboard — Challenge 004

Dashboard de estratégia de social media com análise de 52K posts. Processa o dataset de Social Media Sponsorship & Engagement (Kaggle, MIT) e expõe métricas de performance, patrocínios, audiência e recomendações estratégicas.

---

## O que faz

Analisa eficiência de creators, padrões de engajamento, impacto de patrocínios e distribuição por plataforma — com ressalva explícita de que o dataset é sintético (engagement rate ~19,9% uniforme em todas as dimensões).

---

## Rotas do app

| Rota | Descrição |
|------|-----------|
| `/overview` | KPIs gerais: total posts, avg engagement rate, top plataforma, top creator |
| `/performance` | Performance por plataforma, categoria e dia da semana |
| `/sponsorship` | Comparativo patrocinado vs orgânico; disclosure explícita vs implícita |
| `/audience` | Distribuição por localização e language |
| `/strategy` | Recomendações estratégicas com análise de eficiência por tamanho de audiência (nano/micro/macro) |

---

## Como rodar

**Pré-requisito — scripts Python (pré-processamento):**

```bash
cd apps/social-dashboard
pip install -r scripts/requirements.txt

# Gerar as 8 análises pré-computadas
python scripts/analyze.py    # → data/*.json
```

**App Next.js:**

```bash
# Da raiz do monorepo
pnpm dev:social-dashboard    # http://localhost:3004

# Ou isolado
pnpm dev
```

**Docker:**

```bash
docker compose up social-dashboard --build
```

**Variáveis de ambiente (opcionais):**

```bash
OPENROUTER_API_KEY=sk-or-v1-...   # Ativa insights estratégicos via LLM
```

---

## Findings principais

- Dataset sintético: engagement rate ~19,9% uniforme — sem variância real entre plataformas ou categorias
- Exceção relevante: `engPer1KFollowers` mostra nano-creators (< 10K seguidores) 10× mais eficientes que micro-creators
- Conteúdo com disclosure explícita de patrocínio performa melhor que patrocínio implícito

---

## Arquitetura

Scripts Python geram 8 JSONs de análise em build time (temporal, hashtags, content length, language, day-of-week, creator efficiency, location, platform×day heatmap). O app Next.js consome os JSONs — sem reprocessamento em runtime. Dois notebooks Jupyter em `notebooks/` documentam o processo analítico (EDA e estratégia).
