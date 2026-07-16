## Context

Time comercial de 35 vendedores, 8 managers, 4 escritórios. Pipeline de ~8.800 oportunidades em 4 estágios (Prospecting → Engaging → Won → Lost). Dados em 4 CSVs relacionais. Hoje a priorização é subjetiva ("feeling" do vendedor). A Head de RevOps quer uma ferramenta funcional que qualquer vendedor possa usar sem treinamento.

Restrição crítica: solução precisa **rodar** e ser **útil na segunda-feira de manhã**. Não pode exigir infraestrutura, deploy complexo ou conhecimento técnico do usuário.

## Goals / Non-Goals

**Goals:**
- Aplicação web que roda localmente com `streamlit run app.py`
- Scoring de oportunidades baseado em regras + heurísticas extraídas dos dados históricos
- Score explicável: vendedor vê o breakdown dos fatores
- Filtros por vendedor, manager, região, estágio
- Pipeline ordenado por score com destaques visuais para top deals
- Relatório executivo com win rates, tempo médio por estágio, valor total do pipeline

**Non-Goals:**
- Modelo preditivo ML (regras + heurísticas são suficientes e mais explaináveis)
- Deploy em produção (Streamlit Cloud seria próximo passo, fora do escopo)
- Autenticação/multi-tenant (solução single-user para o desafio)
- Integração com CRM real (dados estáticos dos CSVs)
- Pipeline de dados automatizado (recarregar CSVs manualmente é aceitável)

## Decisions

### Stack: Streamlit + Pandas + Plotly
- **Alternativas consideradas**: React/Next (sobre-engenharia para o escopo), Dash (mais pesado), CLI tool (menos acessível para não-técnicos), Excel (limitado para scoring dinâmico)
- **Por que Streamlit**: Único framework que entrega UI funcional em ~200 linhas com filtros, gráficos e interatividade. Vendedor não-técnico abre URL e usa. Zero configuração de frontend.

### Scoring: Heurístico, não ML
- **Alternativas**: XGBoost/LightGBM (mais acurado mas caixa-preta), Regressão Logística (explicável mas requer mais engenharia), Random Forest (importância de features ajuda explainability)
- **Por que heurístico**: O README do desafio diz explicitamente que "scoring baseado em regras + heurísticas bem apresentado vale mais que XGBoost sem interface". Explainabilidade é requisito. Features: deal_stage, days_in_stage, account_revenue, account_employees, product_price, seller_historical_win_rate, sector_win_rate.

### Arquitetura: Single-page com abas
- Uma página Streamlit com 3 abas: **Pipeline** (deals ordenados por score com filtros), **Deal Detail** (breakdown do score), **Analytics** (métricas agregadas)
- Dados carregados uma vez em cache (`@st.cache_data`)
- Scoring engine em módulo separado (`src/scorer.py`)

### Filtros: Sidebar persistente
- Vendedor (dropdown), Manager (dropdown), Região (dropdown), Estágio (multi-select), Score mínimo (slider)
- Filtros ficam visíveis em todas as abas

## Data Model (in-memory)

```
accounts (85) ──┐
                 ├── sales_pipeline (8.800) ── products (7)
sales_teams (35) ┘
```

Merge feito em pandas no carregamento:
- pipeline + accounts via `account`
- pipeline + products via `product`
- pipeline + sales_teams via `sales_agent`

## Scoring Engine (src/scorer.py)

Features e pesos (calibrados contra dados históricos):

| Feature | Peso | Fonte | Lógica |
|---------|------|-------|--------|
| deal_stage | 30% | pipeline | Won=100, Engaging=70, Prospecting=30, Lost=0 |
| days_in_stage | 15% | pipeline | Deals parados há muito tempo perdem pontos |
| account_revenue | 15% | accounts | Empresas maiores = mais potencial |
| product_price | 10% | products | Produtos mais caros = deal maior |
| seller_win_rate | 15% | histórico | Vendedor com bom histórico = maior chance |
| sector_win_rate | 15% | histórico | Setor com boa conversão = maior chance |

Score final = 0–100, com breakdown por fator (explainability).

## UI Structure

```
app.py
├── sidebar (filtros)
├── tab "Pipeline"
│   ├── métricas do topo (total deals, total value, avg score)
│   └── tabela com deals ordenados por score
│       └── cada linha: score (barra colorida), conta, produto, valor, vendedor, estágio
│       └── expandir → breakdown do score
├── tab "Deal Detail"
│   ├── selector de deal
│   └── breakdown visual (Plotly bar chart horizontal)
│   └── fatores com contribuição positiva/negativa
└── tab "Analytics"
    ├── Win rate por vendedor (bar chart)
    ├── Distribuição de estágios (pie chart)
    ├── Tempo médio por estágio
    └── Pipeline value por região
```

## Risks / Trade-offs

- **[Scoring heurístico]** Pode não capturar padrões não-lineares que um ML capturaria → Mitigação: arquitetura permite substituir scorer por modelo ML sem mudar UI. Pesos são configuráveis.
- **[Dados estáticos]** Solução não reflete mudanças em tempo real → Mitigação: botão "Recarregar Dados" para reimportar CSVs. Aceitável para o desafio.
- **[Streamlit + muitos dados]** 8.800 linhas pode ficar lento em filtros complexos → Mitigação: pandas filter opera em memória, deve ser suficiente. Se necessário, paginação.
- **[Single-user]** Dois vendedores não usam ao mesmo tempo → Não-Goal explícito. Se precisar, Streamlit Community Cloud permite compartilhar.

## Submission Structure

Conforme [CONTRIBUTING.md](../../../../CONTRIBUTING.md) e [submission-guide.md](../../../../submission-guide.md), a solução final será empacotada em:

```
submissions/<nome>/
├── README.md                 ← template em templates/submission-template.md
├── solution/                 ← código, datasets, tudo que roda
│   ├── src/app.py
│   ├── src/scorer.py
│   ├── data/ (CSVs)
│   └── requirements.txt
├── process-log/              ← evidências de uso de IA
│   ├── process-log.md
│   └── chat-exports/ (opcional)
└── docs/                     ← documentação adicional
```

Regras de submissão:
- Nenhum arquivo fora de `submissions/<nome>/` pode ser alterado no PR
- README deve seguir o template (`templates/submission-template.md`)
- Título do PR: `[Submission] <Nome> — Challenge 003`
- Branch: `submission/<nome>`
