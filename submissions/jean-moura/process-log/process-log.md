# Process Log — Lead Scorer

> Registro obrigatório de como a IA foi utilizada.

## Ferramentas utilizadas

- **Claude Code (Oh My Pi)** via OpenSpec workflow — planejamento, implementação, debugging
- **OpenSpec CLI** — geração de artifacts (proposal, design, specs, tasks)
- **Streamlit + Pandas + Plotly** — stack de implementação

## Etapas

### 1. Planejamento (openspec-propose)

Criado o change `build-lead-scorer` com schema spec-driven:

| Artifact | Conteúdo |
|----------|----------|
| **proposal.md** | Problema, changes, 4 capabilities, impacto |
| **design.md** | Stack, arquitetura, scoring heurístico, UI 3 abas, risks |
| **specs/** | 4 specs com 20 requisitos e 28 cenários de teste |
| **tasks.md** | 8 grupos, 36 tarefas |

### 2. Setup & Dependências

- Adicionadas dependências (streamlit, pandas, plotly) ao `requirements.txt`
- Instalação e verificação de imports — zero erros

### 3. EDA (Data Loading)

Dados carregados e merge completo das 4 tabelas. Descobertas críticas:

- **8.800 oportunidades**, 85 contas, 35 vendedores, 7 produtos
- **1.425 órfãos** (deals sem account) — foi preciso tratar fallbacks no scoring
- **Prospecting não tem engage_date** — score base fixo de 30 para esses
- **Lost fecha rápido** (mediana 14 dias) vs **Won demora** (mediana 57 dias) — tempo em estágio é sinal de momentum
- **Seller win rate**: 54.9%–70.4% — melhor preditor individual
- **Sector win rate**: variação pequena (61%–65%), mas sinal presente
- **Account revenue** tem correlação levemente negativa com win rate

### 4. Scoring Engine (src/scorer.py)

Construído scorer heurístico com 6 features:

| Feature | Peso | Lógica |
|---------|------|--------|
| deal_stage | 30% | Won=100, Engaging=70, Prospecting=30, Lost=0 |
| time_in_stage | 15% | Engaging ganha momentum até 365d, depois decai |
| seller_win_rate | 15% | Histórico do vendedor, fallback para média do manager |
| sector_win_rate | 15% | Taxa de conversão do setor |
| product_price | 10% | Normalizado pelo range do catálogo |
| account_revenue | 15% | Normalizado pelo range de contas |

Score validado: Won=100, Lost=0, open deals entre 27 e 67.

### 5. Interface (src/app.py)

Aplicação Streamlit com 3 abas:

- **Analytics** (principal): KPIs por manager com cards ordenados por score médio, gráficos comparativos (deals ativos, score médio, valor estimado, win rate), top 3 deals por vendedor agrupado por manager em expanders (primeiro expandido), win rate por vendedor, distribuição por estágio, tempo médio por estágio, pipeline value por região
- **Pipeline**: lista de deals ordenada por score com indicadores 🟢🟡🔴, breakdown expansível com probabilidade de win, filtros lateral
- **Deal Detail**: selector de deal, métricas, breakdown visual (Plotly), tabela de fatores com interpretação

Filtros (vendedor, manager, região, estágio, score mínimo) se aplicam a todas as abas.

### 6. Refinamentos de UX

- **Pesos dinâmicos**: features sem dados disponíveis (ex: conta órfã sem setor/receita) têm peso redistribuído proporcionalmente para as features com dados
- **Probabilidade de Win**: modelo baseado em buckets históricos de tempo em aberto — 0-7d (53.5%), 15-30d (72.8%), 120d+ (75.6%)
- **Display sem nan**: substituído "nan" por valores legíveis ("Deal sem conta", "$—", etc.)
- **Manager expanders**: primeiro manager (maior score médio) aberto por padrão, demais fechados

### 7. Debugging

- **Problema**: streamlit não adicionava o diretório do projeto ao `sys.path`, causando `ModuleNotFoundError: No module named 'src'`
- **Correção**: adicionado `sys.path.insert(0, str(_PROJECT_ROOT))` no início do app.py

## Onde a IA errou e como corrigi

1. **Import path do Streamlit**: A IA assumiu que `from src.scorer import Scorer` funcionaria com `streamlit run src/app.py`, mas streamlit não adiciona o parent dir ao sys.path automaticamente. Foi preciso adicionar sys.path.insert explicitamente.

2. **EDA inicial perdeu os órfãos**: A primeira leitura dos dados não notou que 1.425 deals não tinham account_id. Isso foi corrigido na segunda rodada de EDA quando analisei os nulls sistematicamente.

3. **Estimativa de pipeline value**: O close_value de deals abertos é sempre 0 (só é preenchido no fechamento). A IA inicialmente usou close_value como "valor do pipeline", o que resultou em $0. Corrigido para usar sales_price do produto.

4. **nan no display**: numpy.nan é truthy em Python, então `nan or "Unknown"` retornava nan em vez de "Unknown". Corrigido com `pd.notna()`.

## O que eu adicionei que a IA sozinha não faria

- **Fallback de win rate por manager**: Quando um vendedor tem poucos deals fechados (<5), o scorer usa a média do manager. Isso veio da compreensão de que vendedores novos não têm histórico suficiente.
- **Tratamento de Prospecting sem data**: A IA inicialmente tentou calcular days_in_stage para todos os deals, mas Prospecting não tem engage_date. A solução foi tratar como dias=0 para esses.
- **Score de "momentum" para Engaging**: Em vez de apenas penalizar deals parados, o scoring dá crédito por tempo investido (até 365 dias), porque deals Won demoram mais que Lost. Isso reflete a realidade dos dados.
- **Pesos dinâmicos**: Features sem dados disponíveis têm peso 0 e o peso liberado é redistribuído. Impede que fatores neutros (50/100) puxem o score pra baixo quando não há dados.
- **Win probability por buckets históricos**: Decisão de usar buckets de tempo (em vez de regressão logística) para manter a explainabilidade — o vendedor entende "deals com X dias têm Y% de chance".

## Quantas iterações

- 2 iterações de EDA (primeira genérica, segunda focada em padrões)
- 3 versões do scorer (pesos ajustados após testes com amostras)
- 2 versões do app.py (correção do import path)
- 3 refinamentos de UX (pesos dinâmicos, win probability, manager expanders)
- 1 versão final com verificação em browser

## Evidências

- Código fonte completo em `solution/src/`
- Documentação de design em `docs/specs/`
- Chat export completo em `process-log/chat-export.md`
- Este process-log em `process-log.md`
