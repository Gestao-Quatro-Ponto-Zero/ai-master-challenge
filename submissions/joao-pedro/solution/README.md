# **README** Challenge 003 — Lead Scorer

> **AI Master Challenge · G4 Educação**
> Área: Vendas / RevOps · Tipo: Build 
---
> **Nota sobre este README**
> Este documento cobre a entrega, a arquitetura e o funcionamento geral da solução.
> Os fundamentos que embasaram as decisões de design — análise exploratória, raciocínio do modelo e limitações — não são detalhados aqui.
>
> Para o entendimento completo do que foi construído e por quê, é fortemente recomendada a leitura dos quatro tópicos disponíveis em **Fundamentos** no Streamlit:
>
> | Tópico | O que cobre |
> |---|---|
> | **Macro** | Problema, diagnóstico, decisões de design e KPIs esperados |
> | **Heurística** | Análise exploratória — como os dados revelaram a tese central |
> | **Score-model** | Lógica técnica detalhada do scoring e das transferências |
> | **Limitações** | O que o modelo não faz, trade-offs e caminhos de evolução |

## Documentação

| Arquivo | Conteúdo |
|---|---|
| [`docs/macro.md`](docs/macro.md) | Big picture — problema, diagnóstico, decisões de design e KPIs esperados |
| [`docs/heuristica.md`](docs/heuristica.md) | Análise exploratória completa — como os dados revelaram a tese central |
| [`docs/logica.md`](docs/logica.md) | Detalhamento técnico do scoring, viabilidade e lógica de transferência |
| [`docs/limitacoes.md`](docs/limitacoes.md) | O que o modelo não faz, trade-offs e caminhos de evolução |
| [`docs/stack.md`](docs/stack.md) | Arquitetura, estrutura de pastas e decisões de design |
| [`docs/inicializacao.md`](docs/inicializacao.md) | Pré-requisitos e instruções completas de inicialização dos três serviços |
| [`docs/README.api.md`](docs/README.api.md) | Documentação de todos os endpoints REST |

---
## O Desafio

### Contexto
> "Nossos vendedores gastam tempo demais em deals que não vão fechar e deixam oportunidades boas esfriar. 
>Preciso de algo funcional — não um modelo no Jupyter Notebook que ninguém vai usar. Quero uma ferramenta que o vendedor abra, veja o pipeline, e saiba onde focar. Pode ser simples, mas precisa funcionar."

| | |
|---|---|
| 👥 **Time** | 30 vendedores, 3 regiões, múltiplos managers |
| 📦 **Pipeline** | ~8.800 oportunidades |
| ⚠️ **Problema** | Priorização feita "no feeling" |




### O ponto-chave:

  > **"O que o vendedor deve trabalhar segunda-feira de manhã?"**




### Dados Disponíveis

Quatro tabelas de um CRM, todas interconectadas.

> Dataset: CRM Sales Predictive Analytics (licença CC0)

| Arquivo | O que contém | Registros | Campo-chave |
|---|---|---|---|
| `accounts.csv` | Contas clientes — setor, receita, número de funcionários, localização, empresa-mãe | ~85 | `account` |
| `products.csv` | Catálogo de produtos com série e preço | 7 | `product` |
| `sales_teams.csv` | Vendedores com seu manager e escritório regional | 35 | `sales_agent` |
| `sales_pipeline.csv` | Pipeline completo — cada oportunidade com stage, datas, vendedor, produto, conta e valor de fechamento | ~8.800 | `opportunity_id` → liga tudo |

**Estrutura dos dados:**
```
accounts ←— sales_pipeline —→ products
                ↓
           sales_teams
```

O `sales_pipeline.csv` é a tabela central. Cada registro é uma oportunidade com:

- `deal_stage`: Prospecting, Engaging, Won, Lost
- `engage_date` / `close_date`: timeline do deal
- `close_value`: valor real de fechamento (0 se Lost)

---
## O que foi entregue

Uma aplicação funcional de priorização de pipeline com duas interfaces complementares:

- **Streamlit** — exploração analítica dos dados, validação do modelo, documentação interativa
- **React + FastAPI** — produto final voltado para o vendedor e o manager, com views específicas por papel

A solução roda com dados reais do CRM, gera ação recomendada para cada deal, e explica o porquê de cada decisão — sem black box.

---

  #### Streamlit View 

  * Interface analítica com 26 páginas organizadas em seis grupos, acessíveis por um hub de navegação central.

    * Documentação e contexto — enunciado do challenge, guia de navegação, instruções de inicialização e o próprio README renderizado na interface.

    * Raciocínio e modelo — cinco páginas que reconstroem o processo de decisão: visão macro do problema, análise heurística exploratória, preview interativo da lógica de scoring, detalhamento técnico do modelo e limitações conhecidas.

    * Dados brutos — visualização direta dos quatro CSVs do CRM (pipeline, contas, produtos, equipes) com contagem de linhas e prévia da estrutura.

    * Listas e cadastros — tabelas filtráveis de deals, contas, produtos, vendedores e managers, com métricas calculadas pelo motor de scoring aplicadas sobre cada entidade.

    * Análises — seis painéis com gráficos interativos: saúde e tempo do pipeline, distribuição de ações recomendadas, performance por produto, análise regional, drilldown por vendedor e análise de transferências recomendadas.

    * Sistema — Descrição completa sobre inicialização, arquitetura & stack e API da aplicação. 

<!-- imagens / vídeo: streamlit view -->

---


#### Seller View

* A experiência do vendedor começa com um dashboard pessoal: gráficos de saúde do pipeline, distribuição de ações recomendadas, série temporal de valor convertido e análise de win rate por produto — tudo filtrado para o próprio portfólio. 

  * O elemento central, porém, é o **feed de deals priorizados**:

  * Cada deal é apresentado como um conjunto de três cartões conectados por linhas:
    * O primeiro traz o contexto completo do deal (conta, região, produto, dias no pipeline, score com breakdown em urgência, probabilidade, valor e viabilidade); 
    
    * O segundo apresenta a ação recomendada em destaque com a justificativa em linguagem natural e os próximos passos numerados; 
    
    * O terceiro, exibido apenas em deals com sugestão de transferência, mostra o vendedor de destino recomendado, sua viabilidade esperada e as razões específicas do match — por que aquele vendedor, naquele momento, tem mais condições de fechar esse deal. 
    
  * O vendedor navega horizontalmente pelo feed, deal a deal, e sai sabendo exatamente o que fazer — sem precisar interpretar um único número.

<!-- imagens / vídeo: seller view -->

---

#### Manager View

* A view do manager é organizada em cartões verticais que ocupam a altura total da tela, navegáveis com scroll. 

    * O primeiro cartão é um **dashboard analítico em carrossel** com três seções: 
      * *Macro Analysis* (KPIs agregados, valor convertido no tempo, saúde do prospecting e medianas de tempo no pipeline); 
      * *Products & Regional Analysis* (performance por produto e por escritório regional); 
      * *Transfer Analysis* (4 métricas de resumo — total de transfers, críticos, consider e score médio — seguidas de dois gráficos, razões mais frequentes para transferência e distribuição do ganho de viabilidade esperado, e três mini-cards de impacto: Δ viabilidade média, viabilidade atual → target e contagem de transfers de alto impacto). 
    
      * Outros cartões incluem **Transfers** (feed de deals com ações TRANSFER e CONSIDER_TRANSFER), **Seller Analysis** (drilldown por vendedor), **Alertas** e **Squad** (cards dos vendedores com acesso à seller view).

<!-- imagens / vídeo: manager view -->


---

## O insight que mudou a direção
>**57%** dos vendedores protegem deals ruins para se defenderem contra a falta de novos leads.

* A abordagem óbvia seria ordenar deals por `probabilidade × valor`. 
* Rejeitamos antes de escrever uma linha de código.

**Por quê:** essa solução responde "qual deal vale mais" — não responde "o que o vendedor deve fazer segunda de manhã". São perguntas diferentes.

A análise exploratória revelou o problema real:

```
Won  (fechados)      →  57 dias (mediana)
Lost (perdidos)      →  14 dias (mediana)   ← percebem rápido que não vai
Engaging (travados)  → 165 dias (mediana)   ← 2.9× Won. Ninguém age.
```

→ **Deals não ficam parados porque são difíceis.**
→ **Ficam parados porque ninguém age sobre eles.**

E a causa raiz: 57% dos vendedores têm prospecting = 0. 

Estão sobrecarregados (carga média 108 deals), protegendo o pipeline antigo para "manter aparência de pipeline". 


→ **Círculo vicioso clássico**.

Isso mudou o design inteiro: o sistema precisa considerar **capacidade do vendedor**, não só importância do deal.


→ A documentação descritiva completa da análise está em [`docs/heuristica.md`](docs/heuristica.md)

---

## Como o scoring funciona

Dois componentes independentes:

```
SCORE (0–100)        importância objetiva do deal
  50%  Urgência      → tempo travado vs. mediana histórica do produto
  30%  Probabilidade → win rate do vendedor ponderado por estágio e setor
  20%  Valor         → ticket vs. média histórica do portfólio

VIABILIDADE (0–100)  capacidade contextual do vendedor agora
  →  prospecting ativo?
  →  carga de deals suportável?
  →  especialização no produto/setor?
```

A cruzamento Score × Viabilidade gera a ação:

| Score \ Viabilidade | Alta ≥ 60 | Média 40–60 | Baixa < 40 |
|---|---|---|---|
| **≥ 80** | 🔥 PUSH HARD | 🔄 RE-QUALIFY | 🔀 TRANSFER |
| **70–79** | 🔥 PUSH HARD | 🔄 RE-QUALIFY | 🔀 TRANSFER · ❌ DISCARD |
| **60–69** | ⚡ ACCELERATE | 🔍 INVESTIGATE | 🔀 CONSIDER TRANSFER |
| **< 60** | ⏸ MONITOR | ⏸ MONITOR | ⏸ MONITOR |

**Por que viabilidade baixa pode significar transferência — não descarte:**

* Um deal com viabilidade 22 pode ser excelente. 

* O problema é o contexto: O vendedor com 148 deals e win rate de 31% naquele produto simplesmente não vai conseguir trabalhar esse deal. 

Transferido para um vendedor com carga de 41 deals e win rate de 57% no produto, a viabilidade sobe para 68. 

→ **O deal não mudou — o contexto mudou**.

→ Lógica técnica completa em [`docs/logica.md`](docs/logica.md)

→ Raciocínio sobre transferências em [`docs/heuristica.md#transferências`](docs/heuristica.md)

---

## Como rodar: Resumo Rápido

> → Três terminais, três comandos. 

> → Cada serviço roda de forma independente.

* **Streamlit:** páginas como `Deals_Analysis.py` usam **Plotly** (`plotly.express`). 

* Com o `venv` ativo, instale dependências Python antes do primeiro run — por exemplo `pip install -r requirements.txt` (inclui `plotly` se listado no arquivo). 

* Detalhes em **Plotly (páginas Streamlit)** nos Pré-requisitos.

```bash
# Terminal 1 — Streamlit (Frontend A)
cd deal-prioritization
source venv/bin/activate
streamlit run streamlit_app/app.py

# Terminal 2 — API REST (FastAPI)
cd deal-prioritization
source venv/bin/activate
uvicorn api.main:app --reload --port 8001

# Terminal 3 — React (Frontend B)
cd deal-prioritization/frontend
npm run dev
```

| Serviço | URL | Depende de |
|---|---|---|
| Streamlit | `http://localhost:8501` | `core/` (direto, sem API) |
| FastAPI | `http://localhost:8001` | `core/` (direto) |
| Swagger UI | `http://localhost:8001/docs` | FastAPI rodando |
| React | `http://localhost:5173` | FastAPI rodando |

> → Acesse a documentação completa de Inicialização em /Sistema/Inicialização no streamlit.

 
---
## Arquitetura & Stack

### Visão Geral da Arquitetura

O sistema é composto por três camadas independentes que compartilham um núcleo (`core/`) de dados e lógica de negócio.
```
┌─────────────────────────────────────────────────────────┐
│                      DATA SOURCES                        │
│   accounts.csv · products.csv · sales_pipeline.csv      │
│   sales_teams.csv                                        │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                        core/                             │
│   data_loader.py      — CSVs, joins, load_benchmarks()  │
│   scoring_engine.py   — score, viabilidade, ação, etc.  │
│   features.py · pipeline_win_rate_buckets.py — auxiliares│
└──────────┬──────────────────────────┬───────────────────┘
           │                          │
           ▼                          ▼
┌──────────────────┐       ┌─────────────────────────────┐
│  streamlit_app/  │       │           api/               │
│  (Frontend A)    │       │      (FastAPI REST)          │
│                  │       │                              │
│  Análise e       │       │  Expõe os dados via HTTP     │
│  exploração de   │       │  para consumo do frontend    │
│  dados           │       │  React                       │
└──────────────────┘       └──────────┬──────────────────┘
                                      │
                                      ▼
                           ┌─────────────────────────────┐
                           │        frontend/             │
                           │    (React — Frontend B)      │
                           │                              │
                           │  Seller + Manager views      │
                           │  (consome a API)             │
                           └─────────────────────────────┘
```
### Fluxo de Dados
```
data/metrics/          4 CSVs do CRM (accounts, products, sales_teams, pipeline)
      │
      ▼
core/                  Motor de scoring — Python puro, sem framework
  data_loader.py       → lê, normaliza e faz join das 4 tabelas
  scoring_engine.py    → calcula score, viabilidade e ação por deal
  benchmarks.py        → medianas históricas, win rates, top 20 contas
      │
      ├──▶  streamlit_app/    Frontend A — análise e validação (Streamlit)
      │
      └──▶  api/              FastAPI REST — expõe o motor via HTTP
                │
                ▼
            frontend/          Frontend B — produto final (React + TypeScript)
```

O `core/` é completamente desacoplado. Tanto o Streamlit quanto a API importam a mesma lógica — sem duplicação.

→ Detalhe completo da stack em [`docs/stack.md`](docs/stack.md)
→ Documentação dos endpoints em [`docs/README.api.md`](docs/README.api.md)


### Estrutura de pastas
```
deal-prioritization/
│
├── 📂 core/                          # Motor de dados e scoring (Python puro)
│   ├── data_loader.py                #   CSVs, joins, load_benchmarks(), preprocess
│   ├── scoring_engine.py             #   Urgência · Probabilidade · Valor · Score · Ação
│   ├── features.py                   #   Feature engineering auxiliar
│   ├── pipeline_win_rate_buckets.py  #   Faixas de tempo no pipeline (win rate)
│   └── __init__.py
│
├── 📂 data/
│   └── metrics/                      # CSVs originais do CRM
│       ├── accounts.csv
│       ├── products.csv
│       ├── sales_teams.csv
│       └── sales_pipeline.csv
│
├── 📂 docs/                          # Documentação em Markdown
│   ├── macro.md
│   ├── heuristica.md
│   ├── logica.md
│   ├── limitacoes.md
│   ├── stack.md
│   ├── inicializacao.md
│   └── README.api.md                 #   Documentação dos endpoints REST
│
├── 📂 api/                           # FastAPI REST — porta 8001
│   ├── main.py                       #   App, CORS, routers, GET /benchmarks, warmup
│   ├── dependencies.py               #   Cache de benchmarks e DataFrame do pipeline
│   └── routers/
│       ├── deals.py                  #   /deals
│       ├── sellers.py                #   /sellers
│       ├── managers.py               #   /managers
│       ├── products.py               #   /products
│       ├── accounts.py               #   /accounts
│       └── analysis.py               #   /analysis/*
│
├── 📂 streamlit_app/                 # Frontend A — análise e exploração
│   ├── app.py                        #   Hub de navegação (st.navigation)
│   └── pages/
│       ├── Navegacao.py              #   Mapa do sistema
│       ├── Inicializacao.py          #   Como rodar os serviços
│       ├── Challenge.py
│       ├── Macro.py
│       ├── Como_funciona.py
│       ├── Heuristica.py
│       ├── Score_Model.py
│       ├── Limitacoes.py
│       ├── Stack.py
│       ├── API.py
│       ├── Deal_List.py · Deal_Details.py
│       ├── Accounts_List.py · Products_List.py · Sellers_List.py · Managers_List.py
│       ├── Raw_Pipeline.py · Raw_Accounts.py · Raw_Products.py · Raw_Teams.py
│       └── Deals_Analysis.py · Action_Analysis.py · Products_Analysis.py
│           Regional_Analysis.py · Seller_Analysis.py · Transfer_Analysis.py
│
├── 📂 frontend/                      # Frontend B — React + Vite
│   ├── index.html
│   ├── vite.config.ts
│   ├── package.json
│   └── src/
│       ├── App.tsx · main.tsx
│       ├── types/index.ts
│       ├── api/                      #   client.ts + fetchers por entidade
│       ├── hooks/                    #   TanStack Query
│       ├── pages/
│       │   ├── Home.tsx              #   Manager view
│       │   └── SellerPage.tsx        #   Seller view
│       ├── components/               #   Dashboards, feed, charts (Recharts)
│       └── lib/                      #   utils.ts, helpers
│
├── README.md
└── requirements.txt
```

---

## Limitações & Escalabilidade

**Dados**

- Sem timestamps por estágio — urgência usa proxy de tempo total, não tempo real travado em cada fase
- Sem dados de atividade — não diferenciamos "deal sendo trabalhado" de "deal abandonado"
- Sem contexto competitivo — probabilidade não considera pressão de concorrentes

**Escopo do MVP**

- Modelo baseado em regras (não ML) — thresholds fixos, não detecta padrões não-óbvios; escolha consciente por explicabilidade
- Viabilidade calculada por vendedor, não por deal — não captura nuances como relacionamento pessoal com o cliente
- Ações são sugestões, não execuções — depende de adoção humana, sem tracking de taxa de execução
- Lê CSVs estáticos — sem integração com CRM real, sem sincronização bidirecional

**Escala e produção**

- Sem banco de dados real, sem cache distribuído, sem testes automatizados e sem autenticação/RBAC

→ Análise completa com caminhos de evolução em [`docs/limitacoes.md`](docs/limitacoes.md)

---

## Documentação

| Arquivo | Conteúdo |
|---|---|
| [`docs/macro.md`](docs/macro.md) | Big picture — problema, diagnóstico, solução, KPIs esperados |
| [`docs/heuristica.md`](docs/heuristica.md) | Análise exploratória completa — como chegamos na tese |
| [`docs/logica.md`](docs/logica.md) | Detalhamento técnico do scoring e lógica de transferência |
| [`docs/README.api.md`](docs/README.api.md) | Documentação de todos os endpoints REST |
| [`docs/stack.md`](docs/stack.md) | Arquitetura, estrutura de pastas, decisões de design |
| [`docs/limitacoes.md`](docs/limitacoes.md) | O que o modelo não faz e o que precisaria pra escalar |
