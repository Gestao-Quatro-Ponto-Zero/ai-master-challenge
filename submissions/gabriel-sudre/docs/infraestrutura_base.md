# Lead Scorer — Arquitetura e Infraestrutura
> Versão final pré-desenvolvimento. Revisada para consistência e viabilidade em 3h.

## Stack
- **Frontend/App:** Python + Streamlit
- **Backend/Dados:** Supabase self-hosted (PostgreSQL + REST API) na Hostinger
- **Deploy:** EasyPanel (Hostinger) — container Docker
- **Auth:** Supabase Auth OTP (email) → redirect para URL pública
- **IA:** OpenAI GPT-4o-mini (explicações, recomendações, chat)

## Infraestrutura de Deploy
```
Hostinger
├── EasyPanel
│   └── lead-scorer (container Docker)
│       ├── Streamlit app (porta 8501 interna)
│       └── Env vars: SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_KEY, OPENAI_API_KEY
│
└── Supabase self-hosted
    ├── PostgreSQL (5 tabelas + RLS)
    ├── Auth (OTP email)
    └── REST API (PostgREST)
```

- **Acesso:** `https://leadscorer.seudominio.com` (HTTPS via EasyPanel)
- **Usuário final:** abre o link no navegador, zero instalação
- **Avaliador:** acessa a URL, testa direto

## Fluxo de Dados
```
CSVs (Kaggle) → Import manual no Supabase Dashboard → 5 tabelas
                                                          │
                                            Supabase REST API
                                                          │
                              ┌────────────────────────────┤
                              │                            │
                    Streamlit (EasyPanel)         OpenAI GPT-4o-mini
                              │                            │
                    ┌─────────┴──────────┐      ┌──────────┴──────────┐
                    │ Camada 1           │      │ Camada 2            │
                    │ Score Engine       │─────→│ AI Layer            │
                    │ (determinístico)   │      │ (sob demanda)       │
                    │ Score 0-100        │      │ Explicações         │
                    │ Features calculadas│      │ Recomendações       │
                    │ (service_role key) │      │ Chat restrito       │
                    └────────────────────┘      │ Resumo executivo    │
                                                └─────────────────────┘
                                                Cache: st.session_state
```

**Nota sobre chaves Supabase:**
- `SUPABASE_KEY` (anon) — usado para auth e queries do usuário (respeita RLS)
- `SUPABASE_SERVICE_KEY` — usado **apenas** pelo scoring engine server-side para calcular agregados do time (win rates, médias) sem restrição de RLS

## Autenticação

### Fluxo
```
1. Usuário acessa https://leadscorer.seudominio.com
2. Tela de login → insere email
3. Supabase envia código OTP por email
4. Usuário insere código OTP
5. Supabase autentica → session token
6. App consulta tabela users (via auth.uid()) → identifica role + vínculo
7. Dashboard carrega filtrado pelo perfil
```

### Mapeamento Auth → Perfil
- `auth.uid()` → tabela `users` → role (admin/vendedor/manager) + sales_team_id/manager_name
- RLS usa `auth.uid()` para filtrar dados conforme o perfil
- Admin cadastra usuários via Supabase Dashboard (email + role + vínculo)
- Usuário sem registro na tabela `users` → tela de "acesso não autorizado"

## Estrutura do Projeto
```
lead-scorer/
├── app.py                  # Entry point Streamlit
├── auth.py                 # Login OTP + session management
├── scoring/
│   ├── engine.py           # Camada 1: score composto determinístico
│   └── features.py         # Cálculo de features (win rates, aging, fit)
├── ai/
│   ├── client.py           # Client OpenAI (GPT-4o-mini)
│   ├── explainer.py        # Camada 2: explicações e recomendações
│   ├── chat.py             # Chat restrito à plataforma
│   └── prompts.py          # System prompts e templates
├── data_source.py          # Queries Supabase (anon key = RLS, service key = agregados)
├── components/             # Componentes visuais do dashboard
├── supabase/
│   └── schema.sql          # DDL das 5 tabelas + RLS policies (entregável)
├── Dockerfile              # Imagem Docker para deploy no EasyPanel
├── .streamlit/
│   └── config.toml         # Config Streamlit (tema, porta)
├── requirements.txt
├── .env.example            # Template de variáveis de ambiente
├── PROCESS_LOG.md
└── README.md
```

## Banco de Dados (Supabase)

### Schema (FKs com IDs surrogate)

```sql
-- ============================================================
-- TABELA: users
-- Mapeia auth do Supabase ao perfil na aplicação
-- ============================================================
CREATE TABLE users (
  id              uuid PRIMARY KEY REFERENCES auth.users(id),
  email           text UNIQUE NOT NULL,
  role            text NOT NULL CHECK (role IN ('admin', 'vendedor', 'manager')),
  sales_team_id   integer REFERENCES sales_teams(id),   -- preenchido para vendedores
  manager_name    text,                                  -- preenchido para managers
  created_at      timestamptz DEFAULT now()
);
-- vendedor: sales_team_id preenchido, manager_name NULL
-- manager: sales_team_id NULL, manager_name preenchido (deve bater com sales_teams.manager)
-- admin: ambos NULL

-- ============================================================
-- TABELA: accounts
-- Contas/clientes do CRM
-- ============================================================
CREATE TABLE accounts (
  id                serial PRIMARY KEY,
  name              text UNIQUE NOT NULL,
  sector            text,
  year_established  integer,
  revenue           numeric,            -- em milhões USD
  employees         integer,
  office_location   text,
  subsidiary_of     text                -- nome da empresa pai (informativo, sem FK)
);

-- ============================================================
-- TABELA: products
-- Catálogo de produtos (gerenciado pelo admin)
-- ============================================================
CREATE TABLE products (
  id              serial PRIMARY KEY,
  name            text UNIQUE NOT NULL,
  series          text,
  sales_price     numeric NOT NULL
);

-- ============================================================
-- TABELA: sales_teams
-- Vendedores, seus managers e escritórios regionais
-- ============================================================
CREATE TABLE sales_teams (
  id              serial PRIMARY KEY,
  sales_agent     text UNIQUE NOT NULL,
  manager         text NOT NULL,
  regional_office text NOT NULL
);

-- ============================================================
-- TABELA: sales_pipeline
-- Oportunidades de venda (tabela central)
-- ============================================================
CREATE TABLE sales_pipeline (
  id              serial PRIMARY KEY,
  opportunity_id  text UNIQUE NOT NULL,
  sales_agent_id  integer NOT NULL REFERENCES sales_teams(id),
  product_id      integer NOT NULL REFERENCES products(id),
  account_id      integer NOT NULL REFERENCES accounts(id),
  deal_stage      text NOT NULL,
  engage_date     date,
  close_date      date,
  close_value     numeric DEFAULT 0,

  -- Integridade por stage
  CONSTRAINT valid_stage CHECK (deal_stage IN ('Prospecting', 'Engaging', 'Won', 'Lost')),
  CONSTRAINT won_rules CHECK (deal_stage != 'Won' OR (engage_date IS NOT NULL AND close_date IS NOT NULL AND close_value > 0)),
  CONSTRAINT lost_rules CHECK (deal_stage != 'Lost' OR (engage_date IS NOT NULL AND close_date IS NOT NULL AND close_value = 0)),
  CONSTRAINT engaging_rules CHECK (deal_stage != 'Engaging' OR (engage_date IS NOT NULL AND close_date IS NULL)),
  CONSTRAINT prospecting_rules CHECK (deal_stage != 'Prospecting' OR (engage_date IS NULL AND close_date IS NULL))
);
```

### Volumetria
| Tabela | Registros | Origem |
|--------|-----------|--------|
| `users` | dinâmico | cadastro manual pelo admin via Supabase Dashboard |
| `accounts` | 85 | accounts.csv |
| `products` | 7 | products.csv |
| `sales_teams` | 35 | sales_teams.csv |
| `sales_pipeline` | 8.800 | sales_pipeline.csv |

### Distribuição de Deal Stages
| Stage | Qtd | % | engage_date | close_date | close_value | Uso no app |
|-------|-----|---|-------------|------------|-------------|------------|
| Won | 4.238 | 48% | preenchido | preenchido | > 0 (média $2.360) | Histórico/benchmark |
| Lost | 2.473 | 28% | preenchido | preenchido | sempre 0 | Histórico/benchmark |
| Engaging | 1.589 | 18% | preenchido | NULL | NULL | **Scoring ativo** |
| Prospecting | 500 | 6% | NULL | NULL | NULL | **Scoring ativo** |

- **Won/Lost:** dados históricos para calcular win rates, médias e benchmarks
- **Engaging + Prospecting:** deals acionáveis — foco do dashboard e scoring

### Correções nos Dados (pré-import)
| Correção | Arquivo | De → Para |
|----------|---------|-----------|
| Nome do produto | sales_pipeline.csv | "GTXPro" → "GTX Pro" |
| Setor | accounts.csv | "technolgy" → "technology" |

### Tratamento de close_value em Lost
- **No banco:** mantém 0 (fato: não gerou receita)
- **No scoring:** cruza com `products.sales_price` para estimar "valor potencial perdido"
- Dado original não é poluído; cálculo de potencial é feito na engine de scoring

### Referência Temporal
- Dataset: Out/2016 a Dez/2017
- **`REFERENCE_DATE = 2017-12-31`** (data máxima do dataset)
- Deals Engaging/Prospecting são avaliados contra essa data, não contra `today()`
- Em produção com dados reais: substituir por `today()`

### Fluxo de Import no Supabase
```
1. Executar schema.sql (cria tabelas, constraints, RLS policies)
2. Import CSV → accounts, products, sales_teams (IDs gerados automaticamente)
3. Import CSV → sales_pipeline (com colunas texto temporárias: sales_agent, product, account)
4. SQL de mapeamento: resolve nomes → IDs nas FKs
5. Drop colunas texto temporárias
6. Admin cadastra users manualmente (email + role + vínculo com sales_teams)
```

### Input de Dados (pós-setup)
- Admin gerencia catálogo de produtos e usuários diretamente no Supabase Dashboard
- Novos deals: inseridos via Supabase Dashboard (futuramente via integração CRM)

### Row Level Security (RLS)

| Role | Tabela | Permissão | Regra |
|------|--------|-----------|-------|
| **admin** | todas | CRUD total | `users.role = 'admin'` |
| **vendedor** | products | SELECT (tudo) | sem filtro |
| **vendedor** | accounts | SELECT (tudo) | sem filtro |
| **vendedor** | sales_teams | SELECT (tudo) | sem filtro (para benchmarks agregados) |
| **vendedor** | sales_pipeline | SELECT (seus deals) | `sales_agent_id = users.sales_team_id` |
| **manager** | products, accounts, sales_teams | SELECT (tudo) | sem filtro |
| **manager** | sales_pipeline | SELECT (deals do time) | `sales_agent_id IN (SELECT id FROM sales_teams WHERE manager = users.manager_name)` |

**Importante:** o scoring engine usa `SUPABASE_SERVICE_KEY` (server-side) para calcular agregados globais (win rates, médias do time). O RLS se aplica apenas às queries do usuário na interface.

## Scoring — Camada 1 (Determinístico)

Score composto 0-100 com pesos explícitos.
Aplicado a **deals ativos** (Engaging + Prospecting).
Calculado server-side com `service_role key` (acesso a dados globais para benchmarks).

```
Score = Σ (peso × feature normalizada 0-1) × 100

Features:
├── pipeline_aging         (peso 0.20) → dias em Engaging vs média do produto
│   └── Prospecting: valor neutro (0.5) — sem engage_date
│
├── win_rate_sector        (peso 0.15) → % Won do setor da conta (histórico global)
├── win_rate_product       (peso 0.15) → % Won do produto (histórico global)
│
├── account_fit            (peso 0.10) → revenue + employees normalizados
├── win_rate_account       (peso 0.10) → % Won dessa conta específica (histórico)
├── potential_value        (peso 0.10) → products.sales_price normalizado pelo range de preços
│
├── agent_performance      (peso 0.10) → win rate do vendedor vs média do time
│
├── repeat_customer        (peso 0.05) → nº de compras anteriores da conta (Won)
└── product_price_tier     (peso 0.05) → tier de preço (alto = mais potencial + mais risco)
```

### Detalhamento das Features

| Feature | Cálculo | Range | Fonte |
|---------|---------|-------|-------|
| `pipeline_aging` | 1 - (dias_em_engaging / max_dias_engaging_do_produto). Quanto mais tempo parado, menor o score. | 0-1 | sales_pipeline (histórico) |
| `win_rate_sector` | Won / (Won + Lost) do setor | 0-1 | sales_pipeline + accounts |
| `win_rate_product` | Won / (Won + Lost) do produto | 0-1 | sales_pipeline |
| `account_fit` | (revenue_normalizada + employees_normalizado) / 2 | 0-1 | accounts |
| `win_rate_account` | Won / (Won + Lost) da conta. Se conta nova (sem histórico) = média global | 0-1 | sales_pipeline |
| `potential_value` | sales_price / max(sales_price) | 0-1 | products |
| `agent_performance` | win_rate_vendedor / win_rate_media_time | 0-1 (capped) | sales_pipeline + sales_teams |
| `repeat_customer` | min(compras_anteriores / 5, 1) — cap em 5+ compras | 0-1 | sales_pipeline |
| `product_price_tier` | sales_price / max(sales_price) | 0-1 | products |

### Notas
- **Pesos ajustáveis** via configuração (não hardcoded)
- **`potential_value` vs `product_price_tier`:** `potential_value` mede valor absoluto do potencial; `product_price_tier` mede o nível de risco/complexidade (ticket alto = ciclo mais longo, mais stakeholders). Correlacionados mas com semânticas distintas
- **Contas sem histórico:** win_rate_account usa média global como fallback
- **Vendedores sem histórico:** agent_performance usa 0.5 (neutro)

## IA — Camada 2 (OpenAI GPT-4o-mini)

### Modelo e Custo
- **Modelo:** GPT-4o-mini
- **Processamento:** sob demanda (só deals visíveis na tela, não os 8.800)
- **Cache:** `st.session_state` (em memória, dura enquanto a sessão estiver ativa)
- **Custo estimado:** ~$0.001/deal → ~$0.02/sessão típica (20 deals)

### Funcionalidades IA

**1. Explicação do Score (por deal)**
A IA recebe: score, features calculadas, dados do deal/conta/produto.
Retorna: 3-5 bullets em linguagem natural explicando fatores positivos e negativos.
Exemplo:
> "Score 82 — A Cancity já comprou 3 vezes (100% conversão), GTX Basic tem win rate de 62% no setor retail, e o deal está em Engaging há 12 dias (dentro da janela ideal). Atenção: ticket abaixo da média pode indicar upsell."

**2. Recomendação de Ação (por deal)**
Próximos passos contextualizados: quando fazer follow-up, o que propor, risco de perda.

**3. Resumo Executivo (para manager)**
Síntese do pipeline do time: valor total em jogo, deals críticos, vendedores que precisam de suporte.

**4. Chat Restrito à Plataforma**
Perguntas livres sobre deals, pipeline e estratégia. Restrito ao contexto de vendas.

### System Prompt do Chat
```
Você é o assistente de vendas do Lead Scorer.
Você tem acesso aos dados do pipeline, contas, produtos e performance do usuário.

Responda APENAS sobre:
- Deals, oportunidades e pipeline do usuário
- Contas, produtos e performance de vendas
- Estratégias de fechamento baseadas nos dados da plataforma
- Comparações com médias do time (sem citar nomes de outros vendedores)

NÃO responda sobre:
- Temas fora do contexto de vendas/pipeline
- Informações que não estejam nos dados da plataforma
- Pedidos de geração de conteúdo genérico
- Dados individuais de outros vendedores (apenas médias agregadas)

Se a pergunta não for relacionada, responda:
"Só posso ajudar com análises do seu pipeline e estratégias de vendas."
```

### Visibilidade de Dados no Chat por Perfil
| Perfil | Dados próprios | Dados do time | Dados individuais de outros |
|--------|---------------|---------------|----------------------------|
| **Vendedor** | Tudo | Médias agregadas (sem nomes) | Nunca |
| **Manager** | Tudo | Tudo (com nomes) | Sim, do seu time |

## UX por Perfil

### Vendedor
- Dashboard "Meu Pipeline" com score ranking (**Engaging + Prospecting**)
- Aba "Histórico" com deals Won/Lost (contexto, não ação)
- Explicação IA por deal (botão "Por que esse score?")
- Recomendação de ação por deal (botão "O que fazer?")
- Alerta visual para deals em risco (aging acima da média)
- Filtros: produto, stage, conta
- Card de métricas: pipeline total, win rate pessoal, ticket médio, comparação com média do time
- Chat IA (sidebar ou modal)

### Manager
- Visão consolidada do time (todos os vendedores)
- Ranking de vendedores por performance
- Pipeline total do time, win rate, ticket médio
- Deals críticos do time (aging alto, alto valor)
- Resumo executivo (IA — botão "Gerar resumo do time")
- Filtros: vendedor, região, produto, stage
- Chat IA sobre qualquer dado do time

### Admin
- Sem dashboard próprio
- Gerencia catálogo de produtos via Supabase Dashboard
- Gerencia usuários (email + role + vínculo) via Supabase Dashboard
- Link direto para o Supabase Dashboard no app

## Deploy

### Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Variáveis de Ambiente (EasyPanel)
| Variável | Descrição |
|----------|-----------|
| `SUPABASE_URL` | URL da instância Supabase |
| `SUPABASE_KEY` | Anon key (queries com RLS) |
| `SUPABASE_SERVICE_KEY` | Service role key (scoring engine — bypassa RLS) |
| `OPENAI_API_KEY` | Chave da API OpenAI |

### Setup Local (desenvolvimento)
- Clonar repo → copiar `.env.example` para `.env` → preencher variáveis
- `pip install -r requirements.txt && streamlit run app.py`
- Acesso em `http://localhost:8501`

## Ordem de Execução (3h)
```
Fase 1 — Fundação (1h)
├── 1.1 Supabase: schema.sql + import CSVs + mapeamento IDs   (40min)
└── 1.2 Auth: login OTP + session + identificação de perfil    (20min)

Fase 2 — Core (1h15)
├── 2.1 Scoring engine: features + score composto              (45min)
└── 2.2 Dashboard Streamlit: UI principal + filtros + perfis   (30min)

Fase 3 — IA + Entrega (45min)
├── 3.1 AI: explainer + recomendações                          (25min)
├── 3.2 Deploy: Dockerfile + EasyPanel + domínio               (10min)
└── 3.3 Docs: README + Process Log                             (10min)

── Entrega completa (3h) ──

Bônus (se sobrar tempo)
└── 4.1 Chat IA restrito à plataforma                          (25min)
```

## Evolução Futura
- Integração direta com CRM (substituir import manual por sync automático)
- Painel admin dedicado dentro do app (hoje via Supabase Dashboard)
- `REFERENCE_DATE` dinâmica baseada em `today()` com dados em tempo real
- Upgrade para GPT-4o para análises mais profundas
- Notificações automáticas para deals em risco (email/Slack)
- Cache persistente em Supabase (tabela ai_cache) com invalidação por alteração de dados
- Histórico de scores (tracking de evolução do deal ao longo do tempo)

---

> Documento revisado e validado. Pronto para desenvolvimento.
