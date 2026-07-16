# Submissão — Jean Moura — Challenge 003

## Sobre mim

- **Nome:** Jean Moura
- **LinkedIn:** https://www.linkedin.com/in/jean-moura/
- **Challenge escolhido:** 003 — Lead Scorer (Build)

---

## Executive Summary

Ferramenta web de priorização de pipeline comercial que calcula score (0–100) e probabilidade de win para cada oportunidade com base em 6 fatores. O vendedor abre a aplicação, vê os deals ordenados por score com código de cores, entende por que cada deal tem aquele score através de breakdowns explicativos, e acompanha métricas do time por manager. Scoring heurístico — explicável por design.

---

## Solução

### Abordagem

Planejamento com OpenSpec (proposal → design → specs → tasks), implementação em 3 camadas: (1) EDA para extrair padrões dos dados históricos, (2) scoring engine modular com probabilidade temporal de win, (3) interface Streamlit com 3 abas (Analytics como principal, Pipeline, Deal Detail).

### Funcionalidades

- **Score 0–100** com 6 fatores: deal_stage, time_in_stage, seller_win_rate, sector_win_rate, product_price, account_revenue
- **Probabilidade de Win** baseada em buckets históricos de tempo em aberto
- **Pesos dinâmicos**: features sem dados têm peso redistribuído para as que têm
- **Visão gerencial**: KPIs por manager, gráficos comparativos, top deals por vendedor agrupados
- **Pipeline**: lista ordenada por score com breakdown explicativo e probabilidade
- **Deal Detail**: breakdown visual (Plotly), tabela de fatores com interpretação
- **Filtros**: vendedor, manager, região, estágio, score mínimo

### Setup

```bash
# 1. Instale as dependências
pip install -r solution/requirements.txt

# 2. Rode (a partir da raiz do submission)
cd submissions/jean-moura
streamlit run solution/src/app.py
```

> Os dados já estão inclusos em `solution/data/` (5 CSVs do dataset Kaggle CRM Sales Predictive Analytics).

### Resultados

- **2089 deals abertos** analisados e priorizados
- **Score médio**: 42.9/100
- **Probabilidade de Win**: de 54% (0–7 dias) a 76% (120+ dias)
- **Melhor preditor**: win rate do vendedor (54.9%–70.4% de variação)
- **Score range**: 27–67 para deals abertos

### Recomendações

1. Usar a ferramenta semanalmente para priorizar top 10 deals por vendedor
2. Calibrar pesos trimestralmente via ScoreConfig
3. Adicionar estimated_value com sales_price do produto
4. Expandir scoring para ML quando houver mais dados históricos

### Limitações

- Dados estáticos (depende de exportação do CRM)
- 1425 deals órfãos (~16%) sem dados de conta
- Sem autenticação multi-usuário
- GTX Pro com 0 won deals (possível erro no dataset)

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Claude Code (Oh My Pi) | Planejamento, implementação, debugging |
| OpenSpec CLI | Geração de artifacts (proposal, design, specs, tasks) |

### Workflow

1. **Planejamento**: Claude gerou proposal → design → specs → tasks via OpenSpec, validando cada etapa
2. **EDA**: Scripts de análise exploratória; decisões de pesos e features baseadas nos dados
3. **Scoring Engine**: Implementação do scorer; validação de range e breakdowns
4. **UI**: App Streamlit com ajustes de UX (pesos dinâmicos, sem nan, probabilidade de win)
5. **Process Log**: Documentação final

### Onde a IA errou e como corrigi

- **Import path**: Streamlit não adiciona diretório ao sys.path — corrigido com insert explícito
- **Pipeline value = $0**: close_value de deals abertos é sempre 0 — corrigido para usar sales_price
- **Órfãos ignorados**: primeira EDA não notou 1425 deals sem account — corrigido na segunda rodada
- **nan no display**: numpy.nan é truthy em Python — corrigido com pd.notna()

### O que eu adicionei que a IA sozinha não faria

- Fallback de win rate por manager para vendedores com poucos deals fechados
- Tratamento de Prospecting sem engage_date (dias=0)
- Score de momentum para Engaging (tempo investido = sinal positivo, não negativo)
- Pesos dinâmicos para features sem dados disponíveis

---

## Evidências

- [x] Process log detalhado
- [x] Código fonte completo em `solution/`
- [x] Documentação de design em `docs/specs/` (proposal, design, specs, tasks)
- [x] Arquitetura em `docs/architecture.md`
- [x] Chat exports (conversa completa em `process-log/chat-export.md`)
---

## Documentação de Design

Os artefatos completos de planejamento estão em `docs/specs/`:

| Documento | Descrição |
|-----------|-----------|
| `proposal.md` | Problema, changes, capabilities |
| `design.md` | Stack, arquitetura, scoring, riscos |
| `specs/lead-scoring-engine/spec.md` | Especificação do scoring |
| `specs/pipeline-dashboard/spec.md` | Especificação da UI |
| `specs/deal-explainability/spec.md` | Breakdown de fatores |
| `specs/sales-analytics/spec.md` | Métricas e analytics |
| `tasks.md` | 36 tarefas de implementação |

---

_Submissão preparada, aguardando revisão final._
