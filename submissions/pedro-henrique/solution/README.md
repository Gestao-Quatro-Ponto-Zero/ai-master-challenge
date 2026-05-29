# G4 Help — MVP

Sistema de suporte inteligente com IA para o Challenge 002 do AI Master.

**Duas jornadas principais:**
- **Cliente** — Abertura de chamado por texto ou voz com tentativa de resolução automática (RAG) antes de criar o ticket
- **Admin** — Dashboard analítico com EDA sobre dados reais + gestão de tickets + base de conhecimento + painel NLP & IA

## Stack

- Next.js 16 + TypeScript + Tailwind CSS
- Supabase (Postgres + pgvector para busca semântica)
- OpenAI: `whisper-1` (STT), `text-embedding-3-small` (embeddings), `gpt-4o-mini` (RAG + classify)
- Recharts para visualizações do dashboard

## Execução rápida

```bash
npm install
cp .env.example .env.local
# edite .env.local com suas chaves (ver seção abaixo)
npm run dev
```

Abra `http://localhost:3000/login`.

**Sem chaves configuradas o app funciona** — todas as APIs têm fallback local com dados de demonstração.

## Login de demo

Na tela `/login`:
- **"Entrar como Cliente"** → `/customer/new` (fluxo de abertura de ticket)
- **"Entrar como Administrador"** → `/admin` (dashboard analítico)

O login usa cookie `demo-role`. Supabase Auth está preparado nas variáveis mas não ativado no fluxo de UI para não bloquear validação em ambiente sem configuração.

## Variáveis de ambiente

Crie `.env.local` a partir de `.env.example`:

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `NEXT_PUBLIC_SUPABASE_URL` | Para busca vetorial | URL do projeto Supabase |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Para busca vetorial | Chave anon do Supabase |
| `SUPABASE_SERVICE_ROLE_KEY` | Para escrita na KB | Service role key |
| `OPENAI_API_KEY` | Para IA real | Sem ela, APIs usam fallback mock |
| `KAGGLE_API_TOKEN` | Para análise offline | Token novo da API Kaggle |
| `KAGGLE_USERNAME` + `KAGGLE_KEY` | Para análise offline (legado) | Download dos datasets |
| `HOURLY_AGENT_COST_BRL` | Opcional | Custo/hora por agente (default: 35) |

## Deploy na Vercel

### 1) Root Directory do projeto

Este app está dentro de um subdiretório do repositório.  
Na criação do projeto na Vercel, defina:

- **Root Directory**: `submissions/pedro-henrique-silva/solution`

### 2) Build settings

Já deixamos o projeto pronto com:

- `vercel.json` com framework Next.js
- `installCommand`: `npm ci`
- `buildCommand`: `npm run build`
- `maxDuration` para rotas de API em `60s`

### 3) Versão de Node

Next.js 16 requer Node 20.9+.

- `package.json` define `engines.node = 20.x`
- `.nvmrc` fixado em `20.9.0`

### 4) Variáveis na Vercel

Em **Project Settings → Environment Variables**, configure no mínimo:

- `OPENAI_API_KEY` (opcional, mas recomendado para IA real)
- `NEXT_PUBLIC_SUPABASE_URL` (opcional para KB vetorial real)
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` (opcional para KB vetorial real)
- `SUPABASE_SERVICE_ROLE_KEY` (opcional para escrita na KB)
- `HOURLY_AGENT_COST_BRL` (opcional, default 35)

As credenciais Kaggle **não são necessárias em runtime** na Vercel; elas são usadas só para gerar `public/insights.json` offline.

### 5) Deploy via CLI (opcional)

Da raiz do repositório:

```bash
vercel --cwd submissions/pedro-henrique-silva/solution
vercel --prod --cwd submissions/pedro-henrique-silva/solution
```

## Scripts offline

```bash
# Baixa os dois datasets do Kaggle (requer credenciais)
python scripts/download_datasets.py

# Analisa Dataset 1 e gera public/insights.json
python scripts/analyze_datasets.py

# Popula a KB vetorial com artigos reais sobre programas G4
python scripts/populate_kb.py --replace
```

`analyze_datasets.py` gera os insights reais exibidos no dashboard. Se faltar credencial, cria fallback de demonstração sem interromper o app.

## Páginas

### Cliente
| Rota | Descrição |
|------|-----------|
| `/login` | Tela de acesso (demo role por cookie) |
| `/customer/new` | Abertura de chamado por texto ou voz + sugestão RAG + deflexão |

### Admin
| Rota | Descrição |
|------|-----------|
| `/admin` | Visão Geral: KPIs, gráficos de canal/tipo/satisfação, EDA com 3 análises exploratórias |
| `/admin/tickets` | Gestão de tickets: filtro por status/prioridade, atualização inline |
| `/admin/kb` | Base de conhecimento vetorial: CRUD de artigos com embeddings automáticos |
| `/admin/nlp` | NLP & IA: pipeline, specs dos 3 modelos, custo estimado e racional estratégico |

## APIs

| Rota | Método | Descrição |
|------|--------|-----------|
| `/api/transcribe` | POST | Áudio → texto via whisper-1 |
| `/api/rag-search` | POST | Query → sugestão via RAG (embeddings + gpt-4o-mini) |
| `/api/classify` | POST | Texto → categoria + prioridade + confiança |
| `/api/tickets` | GET/POST/PATCH | CRUD de tickets |
| `/api/insights` | GET | Insights do dashboard (de `public/insights.json`) |
| `/api/kb` | GET/POST | Listar e criar artigos na KB |
| `/api/kb/[id]` | PATCH/DELETE | Editar e excluir artigos |
| `/api/kb/upload` | POST | Upload de arquivo para importação em lote |

## Estrutura de pastas

```
app/
  (auth)/login/       # tela de login
  customer/new/       # jornada do cliente
  admin/              # layout + visão geral
  admin/tickets/      # gestão de tickets
  admin/kb/           # base de conhecimento
  admin/nlp/          # painel NLP & IA
  api/                # todas as rotas serverless
components/
  AdminSidebar.tsx    # navegação lateral do admin
  TicketTable.tsx     # tabela de tickets
  TicketFilters.tsx   # filtros de status/prioridade
lib/
  openai.ts           # client singleton com fallback
  vector-search.ts    # embeddings + pgvector
  rag.ts              # pipeline RAG completo
  observability.ts    # timer para latência de APIs
scripts/
  analyze_datasets.py # EDA offline → insights.json
  populate_kb.py      # seed da base vetorial
supabase/
  schema.sql          # schema completo do banco
```
