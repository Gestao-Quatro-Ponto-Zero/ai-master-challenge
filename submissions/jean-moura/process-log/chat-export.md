# Chat Export — Lead Scorer (Challenge 003)

> Conversa completa entre Jean Moura e Claude Code (Oh My Pi)
> Data: 2026-07-16
> Ferramenta: Claude Code via Oh My Pi (modelo deepseek/deepseek-v4-flash)

---

## Fase 1: Escolha do Desafio

**Usuário:** Leu todos os desafios e perguntou qual o mais rápido de resolver tecnicamente.

**Claude:** Análise comparativa dos 4 desafios. Recomendou o **Lead Scorer (003)**:
- Dataset mais leve (~8.9K registros vs 33K–78K dos outros)
- Zero análise exploratória complexa (sem NLP, sem causalidade oculta)
- Build é o core, não opcional
- Menor risco de retrabalho

**Usuário:** Pediu para ler o README completo do Lead Scorer e preparar a estrutura base.

**Claude:**
- Leu o README do desafio
- Extraiu `archive.zip` em `challenges/build-003-lead-scorer/data/`
- Criou `src/`, `notebooks/`, `requirements.txt`, `process-log.md`

---

## Fase 2: Planejamento (openspec-propose)

**Usuário:** Invocou openspec-propose, pedindo para seguir as instruções e preencher o process-log.

**Claude:** Criou o change `build-lead-scorer` com schema spec-driven:

| Artifact | Descrição |
|----------|-----------|
| **proposal.md** | Problema, changes, 4 capabilities, impacto |
| **design.md** | Stack (Streamlit + Pandas + Plotly), scoring heurístico, 3 abas, riscos |
| **specs/** | 4 capabilities: lead-scoring-engine, pipeline-dashboard, deal-explainability, sales-analytics |
| **tasks.md** | 8 grupos, 36 tarefas |

**Usuário:** Pediu para incluir submission-guide.md e CONTRIBUTING.md no plano.

**Claude:** Adicionou seção "Submission Structure" no design.md e grupo 8 (Submission Package) nas tasks.

---

## Fase 3: Implementação (openspec-apply)

### Setup & Dependências
- Adicionou streamlit, pandas, plotly ao requirements.txt
- Instalou e verificou imports

### EDA (Data Loading)
Carregou 4 CSVs e merge completo. Descobertas críticas:
- 8.800 oportunidades, 85 contas, 35 vendedores, 7 produtos
- **1.425 órfãos** (deals sem account) — necessidade de fallbacks
- Prospecting **não tem engage_date** — score base fixo 30
- Lost fecha rápido (mediana 14d) vs Won demora (mediana 57d)
- Seller win rate: 54.9%–70.4% — melhor preditor individual
- Account revenue tem correlação levemente negativa com win rate

### Scoring Engine (src/scorer.py)
Scorer heurístico com 6 features:

| Feature | Peso | Lógica |
|---------|------|--------|
| deal_stage | 30% | Won=100, Engaging=70, Prospecting=30, Lost=0 |
| time_in_stage | 15% | Engaging ganha momentum até 365d, depois decai |
| seller_win_rate | 15% | Com fallback para média do manager se <5 deals |
| sector_win_rate | 15% | Taxa de conversão do setor |
| product_price | 10% | Normalizado pelo range do catálogo |
| account_revenue | 15% | Normalizado pelo range de contas |

### Streamlit App (src/app.py)
App com 3 abas: Pipeline, Deal Detail, Analytics. Sidebar com filtros.

### Debugging
- **Import path**: Streamlit não adiciona diretório ao sys.path → corrigido
- **Pipeline value = $0**: close_value é 0 para abertos → corrigido para sales_price
- **nan no display**: numpy.nan é truthy → corrigido com pd.notna()
- **Pesos dinâmicos**: features sem dados têm peso redistribuído

---

## Fase 4: Refinamentos

**Usuário:** Pediu para remover "nan" e "$nan" do display.

**Claude:** 
- Deal órfão mostra "Deal sem conta" em vez de "nan"
- Pipeline sem close_value não mostra "$nan"
- Pesos dinâmicos: features sem dados (sector, revenue) têm peso 0, redistribuído

**Usuário:** Analytics como aba principal, com visão por manager.

**Claude:** 
- Reordenou abas: Analytics → Pipeline → Deal Detail
- Manager KPIs (deals, valor, score, win rate)
- Gráficos comparativos entre managers
- Top 3 deals por vendedor, agrupado por manager (expanders)

**Usuário:** Probabilidade de win baseada em tempo em aberto.

**Claude:** 
- Buckets históricos: 0-7d (53.5%), 8-14d (57.5%), 15-30d (72.8%), 31-60d (66.3%), 61-90d (66.5%), 91-120d (70.4%), 120d+ (75.6%)
- Adicionado ao Pipeline e Deal Detail

**Usuário:** Manager expanders com primeiro aberto, fecha outros.

**Claude:** Groupby manager com `expanded=idx==0`.

**Usuário:** Estágios sem default, Top Deals com Win %.

**Claude:** Filtro de estágios vazio por padrão. Win probability em cada linha.

---

## Fase 5: Preparação da Submissão

**Usuário:** Pediu para preparar o envio via fork (https://github.com/jeanjeferson/ai-master-challenge.git)

**Claude:**
- Adicionou fork como remote
- Criou branch `submission/jean-moura`
- Descobriu que `submissions/` está no `.gitignore`
- Copiou datasets e openspec artifacts para dentro da submissão
- Estrutura final:

```
submissions/jean-moura/
├── README.md
├── solution/
│   ├── data/           (5 CSVs)
│   ├── requirements.txt
│   └── src/
│       ├── app.py
│       └── scorer.py
├── process-log/
│   ├── process-log.md
│   └── chat-export.md  ← este arquivo
└── docs/
    ├── architecture.md
    ├── challenge/README.md
    └── specs/ (proposal, design, tasks, 4 specs)
```

---

## Resumo de Arquivos Modificados/Criados

### Código Fonte
- `src/app.py` — 539 linhas, interface Streamlit completa
- `src/scorer.py` — 300 linhas, scoring heurístico + win probability

### Planejamento (openspec)
- `openspec/changes/build-lead-scorer/proposal.md`
- `openspec/changes/build-lead-scorer/design.md`
- `openspec/changes/build-lead-scorer/tasks.md` — 36 tarefas
- `openspec/changes/build-lead-scorer/specs/*/spec.md` — 4 specs

### Documentação
- `process-log.md` — workflow, erros, contribuição humana
- `README.md` — template de submissão preenchido
- `docs/architecture.md` — stack, scoring, estrutura

---

## Decisões Técnicas

| Decisão | Alternativas | Escolha |
|---------|-------------|---------|
| Stack | React, Dash, CLI, Excel | **Streamlit** — prototipação mais rápida, zero frontend |
| Scoring | XGBoost, RegLog, Random Forest | **Heurístico** — explainabilidade > acurácia de caixa-preta |
| Arquitetura | Páginas separadas | **3 abas** — navegação fluida |
| Pesos | Fixos | **Dinâmicos** — redistribui quando faltam dados |
| Prob. Win | Regressão Logística | **Buckets históricos** — simples e data-driven |
