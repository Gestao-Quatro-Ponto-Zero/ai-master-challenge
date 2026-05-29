# SPEC-MVP — G4 Suporte Inteligente

> Spec de produto para ser executada num code assistant (Cursor, Lovable, Bolt, Claude Code).
> Mantenha esse arquivo como contexto inicial do projeto.

---

## 0. Regras obrigatórias de submissão (CONTRIBUTING.md)

**Antes de qualquer linha de código**, leia e respeite:

- **Branch:** `submission/pedro-henrique-silva`
- **Pasta única permitida:** `submissions/pedro-henrique-silva/` — **qualquer arquivo fora dela faz o PR ser rejeitado**
- **Estrutura obrigatória dentro da pasta:**
  ```
  submissions/pedro-henrique-silva/
  ├── README.md            ← seguir templates/submission-template.md (na raiz do repo)
  ├── solution/            ← TODO o código do MVP (projeto Next.js inteiro) vai aqui
  ├── process-log/         ← screenshots, chat exports, evidências de uso de IA
  └── docs/                ← este SPEC, plano de execução, anotações
  ```
- **Título do PR:** `[Submission] Pedro Henrique — Challenge 002`
- **Não tocar em arquivo nenhum fora dessa pasta** (nem README, nem CONTRIBUTING, nem outros challenges)
- Um PR por pessoa — atualizações vão na mesma branch via push

**Implicação prática para o code assistant:**
> Quando rodar `npx create-next-app` ou equivalente, fazer dentro de `submissions/pedro-henrique-silva/solution/`. Todos os caminhos da seção 9 são **relativos a `solution/`**, não à raiz do repo.

---

## 1. Visão do produto

Webapp de suporte ao cliente que demonstra como IA reduz fricção dos dois lados:

- **Diretor de Operações (admin)** vê um dashboard que responde sozinho às perguntas-chave do diagnóstico (gargalos, drivers de satisfação, desperdício em horas/R$).
- **Cliente final** abre tickets por texto **ou áudio**. Antes de virar caso, o sistema busca soluções similares na base histórica via RAG e tenta resolver o problema no ato. Se não resolver, vira ticket priorizado.

**Tese:** o maior ganho não é responder ticket mais rápido — é evitar que ele exista.

---

## 2. Personas e jobs-to-be-done

| Persona | Job principal | Sucesso = |
|---|---|---|
| Cliente final | "Tenho um problema, quero resolver agora" | Resolve sem abrir ticket ou abre com expectativa clara de prazo |
| Admin (Diretor de Ops) | "Onde estamos sangrando e o que fazer?" | Decisão acionável em < 5 min olhando o dashboard |

---

## 3. Stack

| Camada | Escolha | Por quê |
|---|---|---|
| Frontend | **Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui** | Padrão que Lovable/Bolt/Cursor entendem nativamente |
| Backend | **Next.js Route Handlers (API serverless)** | Sem servidor separado pra manter |
| Banco + Auth + Storage | **Supabase** (Postgres + pgvector + Auth + Storage) | BaaS completo, vector store nativo |
| LLM (chat/classificação) | **OpenAI GPT-4o-mini** | Custo baixo, latência ok, JSON mode |
| Transcrição de áudio | **OpenAI Whisper API** (`whisper-1`) | Já mencionado no requisito |
| Embeddings | **OpenAI `text-embedding-3-small`** (1536 dim) | Padrão, barato, bom o suficiente |
| Análise dos datasets | **Python (pandas, scikit-learn) — script offline** | Gera `insights.json` consumido pelo dashboard |
| Charts | **Recharts** ou **Tremor** | Plug-and-play |
| Deploy | **Vercel** + **Supabase Cloud** | Free tier resolve o MVP |

---

## 4. Arquitetura (alto nível)

```
┌──────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                     │
│  ┌──────────────────┐         ┌─────────────────────────┐   │
│  │ /customer        │         │ /admin                  │   │
│  │  - Novo ticket   │         │  - Dashboard analítico  │   │
│  │  - Voz → texto   │         │  - Lista de tickets     │   │
│  │  - Resposta IA   │         │  - Detalhe / ações      │   │
│  │  - Meus tickets  │         │                         │   │
│  └────────┬─────────┘         └────────────┬────────────┘   │
└───────────┼──────────────────────────────────┼──────────────┘
            │                                  │
            ▼                                  ▼
┌──────────────────────────────────────────────────────────────┐
│                   API ROUTES (Next.js)                        │
│  /api/transcribe   /api/embed   /api/rag-search              │
│  /api/classify     /api/tickets  /api/insights               │
└──────┬──────────────────┬─────────────────────┬──────────────┘
       │                  │                     │
       ▼                  ▼                     ▼
┌─────────────┐   ┌───────────────┐   ┌──────────────────────┐
│   OpenAI    │   │   Supabase    │   │  insights.json       │
│   (Whisper, │   │ (Postgres +   │   │  (gerado offline pelo│
│    GPT-4o,  │   │  pgvector +   │   │   script Python que  │
│    embed)   │   │  Auth +       │   │   analisa o Dataset 1)│
│             │   │  Storage)     │   │                      │
└─────────────┘   └───────────────┘   └──────────────────────┘
```

---

## 5. Módulos do MVP

### 5.1 Análise offline dos datasets (script Python)

Gera `public/insights.json` que o dashboard admin consome. **Não roda em produção** — roda 1x antes do deploy.

**Aquisição dos datasets — usar `kagglehub` (não baixar manual):**

```python
# scripts/download_datasets.py
import kagglehub

# Dataset 1 — Customer Support Ticket Dataset (~30k registros, métricas + texto)
path_1 = kagglehub.dataset_download("suraj520/customer-support-ticket-dataset")
print("Dataset 1:", path_1)

# Dataset 2 — IT Service Ticket Classification Dataset (~48k textos em 8 categorias)
path_2 = kagglehub.dataset_download("adisongoh/it-service-ticket-classification-dataset")
print("Dataset 2:", path_2)
```

**Setup necessário:**
```bash
pip install kagglehub pandas scikit-learn openai supabase
# Autenticação: kagglehub usa ~/.kaggle/kaggle.json (criar token em kaggle.com/settings)
```

**Notas:**
- `kagglehub` baixa pra cache local (`~/.cache/kagglehub/`) — os scripts seguintes leem de lá via os paths retornados.
- **Não comitar os CSVs** no repo (alguns têm > 50MB, GitHub avisa em 50MB e rejeita em 100MB). Adicionar `solution/data/` ao `.gitignore`. Se quiser deixar evidência, comitar uma **amostra de 100 linhas** em `solution/data/sample_dataset1.csv` e `sample_dataset2.csv`.
- Em vez de baixar manual e colocar em `data/`, o pipeline é: `download_datasets.py` → `analyze_datasets.py` → `populate_kb.py`. Tudo rodável de `solution/scripts/`.

**Responsabilidades:**
1. Carregar Dataset 1 (suporte) e Dataset 2 (classificação IT).
2. Calcular:
   - Heatmap canal × tipo × prioridade → tempo médio até resolução
   - Correlação de cada feature com `Customer Satisfaction Rating` (correlação de Pearson + feature importance via Random Forest pequeno)
   - Desperdício: `(tickets acima da mediana segmentada × tempo excedente em horas) × R$ hora-agente` (assumir R$ 35/h, ajustável)
   - Top-10 padrões repetitivos em `Ticket Description` (TF-IDF + KMeans, k=10)
   - Volume por categoria do Dataset 2 (vai virar tag de roteamento)
3. **Popular Supabase Vector Store** com embeddings de `Ticket Description` + `Resolution` do Dataset 1 (insumo do RAG).

**Saídas:**
- `solution/analysis/insights.json` (consumido pelo dashboard)
- `solution/analysis/notebook.ipynb` (evidência de análise no PR)
- Tabela `support_tickets_kb` no Supabase populada com vetores

### 5.2 Autenticação e roles

- Supabase Auth (email + senha).
- Campo `role` em `profiles`: `'admin' | 'customer'`.
- Middleware Next.js bloqueia rotas:
  - `/admin/*` exige `role = 'admin'`
  - `/customer/*` exige usuário logado
- Seed inicial: 1 admin (você) + 2 customers de teste.

### 5.3 Cliente — abrir ticket (texto OU áudio)

**Fluxo "Novo ticket":**

1. Cliente escolhe **Texto** ou **Áudio**.
2. Se Áudio:
   - Grava no navegador (MediaRecorder API → blob WebM/MP4).
   - Upload pra Supabase Storage (bucket `ticket-audio`).
   - POST `/api/transcribe` → Whisper retorna texto.
3. Texto (do form ou transcrito) é exibido pro cliente revisar.
4. POST `/api/rag-search` com o texto:
   - Gera embedding do texto.
   - `match_documents` em `support_tickets_kb` (top-5 por similaridade coseno).
   - LLM monta resposta sugerida usando os top-5 como contexto.
5. Cliente vê:
   - **Resposta sugerida** + tickets similares com confiança.
   - Botões: **"Resolveu meu problema"** (encerra sem virar ticket) ou **"Ainda preciso de ajuda"** (continua pro form).
6. Se continuar, o ticket é criado:
   - Categoria (classificada via LLM com as 8 do Dataset 2 + opção "Other")
   - Prioridade (classificada via LLM)
   - Status `open`
   - Vetor já salvo

**Critério de aceite:**
- Áudio de 30s transcreve em < 8s
- RAG retorna sugestão em < 4s
- Botão "Resolveu" registra evento e fecha — não cria ticket (essa métrica é o ROI vivo)

### 5.4 Cliente — meus tickets

Lista simples com filtros (status, data). Detalhe mostra histórico de mensagens.

### 5.5 Admin — dashboard analítico

**Página `/admin`** com 4 blocos respondendo às perguntas do challenge:

| Bloco | Pergunta respondida | Visual |
|---|---|---|
| 1. Onde o fluxo trava | "Combinações canal × tipo × prioridade com piores tempos" | Heatmap + tabela top-10 |
| 2. O que impacta satisfação | "Variáveis correlacionadas com CSAT" | Bar chart de feature importance + scatter resposta-vs-CSAT |
| 3. Quanto desperdiçamos | "Horas e R$ recuperáveis" | KPI cards + waterfall por segmento |
| 4. O que automatizar primeiro | "Top padrões repetitivos = ROI imediato" | Tabela com volume × economia estimada |

Dados vêm de `public/insights.json`. **Não recalcula em tempo real.**

### 5.6 Admin — gestão de tickets

Tabela paginada de todos os tickets (live, vinda do Supabase). Filtros por categoria/prioridade/status. Drilldown mostra histórico + sugestões da IA + ações (reatribuir, mudar prioridade, fechar).

### 5.7 Admin — métricas de deflexão (diferencial)

Card no dashboard com:
- **Taxa de deflexão**: % de sessões `/customer/new` que terminaram em "Resolveu meu problema" antes de virar ticket
- **Confiança média do RAG**
- **Top-5 perguntas resolvidas sem virar ticket**

Isso prova que o sistema **previne** tickets, não só os processa mais rápido.

---

## 6. Schema Supabase (SQL para rodar direto)

```sql
-- 1. Extensão pgvector
create extension if not exists vector;

-- 2. Perfis (estende auth.users)
create table profiles (
  id uuid primary key references auth.users on delete cascade,
  email text not null,
  full_name text,
  role text not null default 'customer' check (role in ('admin','customer')),
  created_at timestamptz default now()
);

-- 3. Base de conhecimento (vinda do Dataset 1) — RAG source
create table support_tickets_kb (
  id bigserial primary key,
  source_ticket_id text,
  description text not null,
  resolution text,
  category text,
  priority text,
  channel text,
  embedding vector(1536),
  created_at timestamptz default now()
);
create index on support_tickets_kb using ivfflat (embedding vector_cosine_ops) with (lists = 100);

-- 4. Tickets reais criados no app
create table tickets (
  id bigserial primary key,
  customer_id uuid not null references profiles(id),
  source text not null check (source in ('text','audio')),
  audio_path text,                    -- path no Storage se source='audio'
  raw_text text not null,             -- texto final (transcrito ou digitado)
  category text,
  priority text check (priority in ('low','medium','high','critical')),
  status text not null default 'open' check (status in ('open','pending','resolved','deflected')),
  rag_suggestion text,                -- resposta sugerida pela IA
  rag_confidence numeric,             -- 0..1
  resolved_by_ai boolean default false,
  created_at timestamptz default now(),
  resolved_at timestamptz
);
create index on tickets (customer_id, created_at desc);
create index on tickets (status);

-- 5. Eventos de deflexão (cliente clicou "Resolveu meu problema")
create table deflection_events (
  id bigserial primary key,
  customer_id uuid references profiles(id),
  raw_text text,
  top_matches jsonb,
  created_at timestamptz default now()
);

-- 6. Função de busca por similaridade
create or replace function match_kb (
  query_embedding vector(1536),
  match_threshold float default 0.75,
  match_count int default 5
)
returns table (
  id bigint,
  description text,
  resolution text,
  category text,
  similarity float
)
language sql stable
as $$
  select id, description, resolution, category,
         1 - (embedding <=> query_embedding) as similarity
  from support_tickets_kb
  where 1 - (embedding <=> query_embedding) > match_threshold
  order by embedding <=> query_embedding
  limit match_count;
$$;

-- 7. RLS básico
alter table tickets enable row level security;
create policy "customers see own" on tickets for select
  using (auth.uid() = customer_id);
create policy "customers insert own" on tickets for insert
  with check (auth.uid() = customer_id);
create policy "admins see all" on tickets for all
  using (exists (select 1 from profiles where id = auth.uid() and role = 'admin'));
```

---

## 7. API Routes (Next.js)

| Método | Path | Função |
|---|---|---|
| POST | `/api/transcribe` | Recebe `audio_path`, baixa do Storage, manda pro Whisper, retorna `{ text }` |
| POST | `/api/rag-search` | Recebe `text`, gera embedding, chama `match_kb`, monta resposta via GPT-4o-mini, retorna `{ suggestion, sources[], confidence }` |
| POST | `/api/classify` | Recebe `text`, retorna `{ category, priority }` via GPT-4o-mini JSON mode |
| POST | `/api/tickets` | Cria ticket (após cliente clicar "Ainda preciso de ajuda") |
| POST | `/api/deflection` | Registra evento quando cliente clica "Resolveu" |
| GET | `/api/insights` | Retorna `insights.json` (admin only) |
| GET | `/api/tickets` | Lista tickets (RLS aplica) |

**Prompt do classificador (`/api/classify`):**
```
System: Você classifica tickets de suporte. Retorne SEMPRE JSON válido:
{
  "category": "Hardware|Software|Access|Storage|HR|Purchase|Network|Other",
  "priority": "low|medium|high|critical",
  "reasoning": "breve",
  "confidence": 0.0-1.0
}
Se confidence < 0.7, marque category="Other" e priority="medium".

User: {{texto do ticket}}
```

**Prompt do RAG (`/api/rag-search`):**
```
System: Você é um assistente de suporte. Use APENAS os trechos de resoluções
similares abaixo para sugerir uma resposta. Se nenhum trecho cobrir o problema,
diga claramente "Não tenho confiança para responder" — não invente.

Trechos:
{{top-5 resolutions vindos do match_kb}}

User: {{texto do ticket}}

Retorne JSON:
{ "suggestion": "...", "confidence": 0.0-1.0, "used_sources": [ids] }
```

---

## 8. Variáveis de ambiente (`.env.local`)

```bash
# Next.js
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=             # server-side only

# OpenAI
OPENAI_API_KEY=

# Configs
HOURLY_AGENT_COST_BRL=35                # usado no cálculo de desperdício
```

---

## 9. Estrutura de pastas

> ⚠️ **Tudo abaixo é relativo a `submissions/pedro-henrique-silva/solution/`** — não à raiz do repo. Nada pode vazar para fora dessa pasta (regra do CONTRIBUTING.md).

```
submissions/pedro-henrique-silva/
├── README.md                     ← gerado a partir de templates/submission-template.md
├── solution/                     ← PROJETO NEXT.JS COMPLETO COMEÇA AQUI
│   ├── app/
│   │   ├── (auth)/login/page.tsx
│   │   ├── customer/
│   │   │   ├── new/page.tsx          ← form + voice + RAG
│   │   │   └── tickets/page.tsx
│   │   ├── admin/
│   │   │   ├── page.tsx              ← dashboard (consome insights.json)
│   │   │   └── tickets/page.tsx
│   │   └── api/
│   │       ├── transcribe/route.ts
│   │       ├── rag-search/route.ts
│   │       ├── classify/route.ts
│   │       ├── tickets/route.ts
│   │       ├── deflection/route.ts
│   │       └── insights/route.ts
│   ├── components/
│   │   ├── ui/                       ← shadcn
│   │   ├── VoiceRecorder.tsx
│   │   ├── RagSuggestion.tsx
│   │   ├── InsightCards.tsx
│   │   └── HeatmapChart.tsx
│   ├── lib/
│   │   ├── supabase/server.ts
│   │   ├── supabase/client.ts
│   │   └── openai.ts
│   ├── public/
│   │   └── insights.json             ← gerado pelo script Python (commitado)
│   ├── scripts/
│   │   ├── download_datasets.py      ← kagglehub: baixa Dataset 1 e Dataset 2
│   │   ├── analyze_datasets.py       ← gera insights.json
│   │   ├── populate_kb.py            ← embeddings → support_tickets_kb
│   │   └── seed_users.ts
│   ├── data/                         ← CSVs do Kaggle (gitignored se grandes; senão amostra)
│   ├── supabase/
│   │   └── schema.sql                ← SQL da seção 6 deste spec
│   ├── .env.example
│   ├── package.json
│   └── README.md                     ← setup local + deploy
├── process-log/
│   ├── screenshots/              ← prints das conversas com IA
│   ├── chat-exports/             ← exports do Claude/ChatGPT/Cursor
│   └── NOTES.md                  ← narrativa do "como cheguei aqui"
└── docs/
    ├── SPEC-MVP.md               ← este arquivo (inclui compliance checklist na §13)
    ├── 00-PLANO-DE-EXECUCAO.md   ← plano estratégico
    └── 03-process-and-roi.md     ← matriz humano-vs-IA + cálculo de ROI (gerado na Fase 3)
```

---

## 10. Sprints de execução (ordem recomendada pro code assistant)

### Sprint 1 — Foundations (30-40 min de prompts)
1. Setup Next.js + Tailwind + shadcn + Supabase client
2. Auth (login/signup) + middleware de roles
3. Schema SQL aplicado no Supabase
4. Seed de 1 admin + 2 customers

### Sprint 2 — Análise + KB (script Python, ~30 min)
5. Rodar `analyze_datasets.py` → gera `insights.json`
6. Rodar `populate_kb.py` → preenche `support_tickets_kb` com 3-5k embeddings (amostra do Dataset 1, não os 30k pra economizar API)

### Sprint 3 — Cliente (1h)
7. Página `/customer/new` com toggle texto/áudio
8. Componente `VoiceRecorder` + endpoint `/api/transcribe`
9. Endpoint `/api/rag-search` + UI de resposta sugerida
10. Botões "Resolveu" / "Ainda preciso" → `/api/deflection` ou `/api/tickets`
11. Página `/customer/tickets`

### Sprint 4 — Admin (45 min)
12. Página `/admin` consumindo `insights.json` (4 blocos com Recharts/Tremor)
13. Página `/admin/tickets` (tabela + filtros)
14. Card de métricas de deflexão

### Sprint 5 — Polimento + deploy (30 min)
15. Loading states, error toasts, empty states
16. README com instruções de setup local + deploy
17. Deploy Vercel + Supabase + variáveis de ambiente

---

## 11. Critérios de aceite do MVP (checklist final)

- [ ] Login funciona pros dois roles
- [ ] Cliente consegue gravar áudio e ver transcrição em < 8s
- [ ] RAG retorna 3+ resultados relevantes pra um ticket comum (testar com texto real do Dataset 1)
- [ ] Botão "Resolveu" registra evento e não cria ticket
- [ ] Ticket criado aparece no admin
- [ ] Dashboard admin tem os 4 blocos com dados reais
- [ ] Taxa de deflexão aparece com pelo menos 1 evento
- [ ] App roda do `git clone` em < 10 min com README

---

## 12. O que NÃO está no MVP (deixar explícito pro avaliador)

- Notificações push/email
- Chat em tempo real cliente ↔ agente
- Fine-tuning de modelo
- Multi-idioma (PT-BR fixo)
- Mobile nativo (responsive web resolve)
- Integração com canais externos (WhatsApp, Email)

Esses itens entram no "Próximos passos" da submissão — sinaliza maturidade, não preguiça.

---

## 13. Compliance checklist (rodar antes de cada push e DEFINITIVAMENTE antes do PR)

### 13.1 Regras críticas (PR é rejeitado se quebrar)

- [ ] **Branch correta:** `submission/pedro-henrique-silva`
- [ ] **Zero arquivos modificados fora de `submissions/pedro-henrique-silva/`**
  ```bash
  git diff --name-only main...HEAD | grep -v '^submissions/pedro-henrique-silva/' || echo "OK: nada fora da pasta"
  ```
- [ ] **Estrutura de pastas presente:**
  - [ ] `submissions/pedro-henrique-silva/README.md`
  - [ ] `submissions/pedro-henrique-silva/solution/`
  - [ ] `submissions/pedro-henrique-silva/process-log/`
  - [ ] `submissions/pedro-henrique-silva/docs/`
- [ ] **README segue `templates/submission-template.md`**
- [ ] **Process Log existe e tem evidência** (sem ele = desclassificado)
- [ ] **Título do PR exato:** `[Submission] Pedro Henrique — Challenge 002`

### 13.2 Regras de conteúdo (não invalida, mas penaliza)

- [ ] Se construí código, incluí instruções de setup no `solution/README.md`
- [ ] `.env.example` no `solution/` (sem secrets reais)
- [ ] `data/` no `.gitignore` (CSVs grandes — GitHub rejeita > 100MB)
- [ ] `node_modules/`, `.next/`, `.env*` no `.gitignore`
- [ ] Datasets do Kaggle são **CC0** (ok pra usar e citar)

### 13.3 Armadilhas comuns do code assistant

⚠️ **Cursor/Lovable/Bolt tendem a:**

1. Rodar `npx create-next-app` na raiz do repo em vez de dentro de `solution/`
   → **Mitigação:** sempre incluir no prompt "estamos dentro de `submissions/pedro-henrique-silva/solution/`"

2. Modificar `.gitignore` global ou `README.md` da raiz do repo
   → **Mitigação:** revisar `git status` antes de cada commit

3. Criar `node_modules/` commitado por engano
   → **Mitigação:** `.gitignore` dentro de `solution/` com `node_modules/`, `.next/`, `.env*`

4. Adicionar `package.json` na raiz do repo
   → **Mitigação:** não deve existir — só em `solution/`

### 13.4 Verificação final (4 comandos)

```bash
cd <raiz-do-repo>

# 1. Branch certa?
git branch --show-current
# Esperado: submission/pedro-henrique-silva

# 2. Nada fora da pasta?
git diff --name-only main...HEAD | grep -v '^submissions/pedro-henrique-silva/'
# Esperado: (output vazio)

# 3. Estrutura completa?
ls submissions/pedro-henrique-silva/
# Esperado: README.md  docs  process-log  solution

# 4. README segue template?
head -5 submissions/pedro-henrique-silva/README.md
# Esperado: começa com "# Submissão — Pedro Henrique — Challenge 002"
```

Se todos os 4 comandos passam, está pronto pra abrir PR.

---

## 14. Próximo passo pra você (Pedro)

**Setup do git (uma vez):**
```bash
# fork o repo via UI do GitHub, então:
git clone https://github.com/SEU-USUARIO/ai-master-challenge.git
cd ai-master-challenge
git checkout -b submission/pedro-henrique-silva
cd submissions/pedro-henrique-silva/solution
```

**Setup do projeto:**
1. Criar projeto no Supabase (free tier) + projeto OpenAI → guardar as keys em `.env.local`
2. `npx create-next-app@latest .` dentro de `solution/` (já estamos lá)
3. Colar este SPEC no Cursor/Lovable/Bolt como contexto inicial
4. Primeiro prompt sugerido: *"Implemente o Sprint 1 do SPEC-MVP.md, respeitando que estamos dentro de submissions/pedro-henrique-silva/solution/ e nada pode vazar pra fora dessa pasta."*
5. Avançar sprint por sprint, validando antes de seguir
6. Eu (Claude) gero os scripts Python (`download_datasets.py` via kagglehub, `analyze_datasets.py` e `populate_kb.py`) — basta criar o token do Kaggle em `~/.kaggle/kaggle.json` que o resto é automático

**Antes de abrir o PR:**
```bash
# garantir que nenhum arquivo vazou pra fora da pasta
git status
# deve mostrar apenas mudanças em submissions/pedro-henrique-silva/

git add submissions/pedro-henrique-silva/
git commit -m "feat: Challenge 002 submission"
git push origin submission/pedro-henrique-silva
```

Abrir PR na UI do GitHub com título exato: `[Submission] Pedro Henrique — Challenge 002`

---

*Versão 1.2 — 2026-05-28 (acesso aos datasets via kagglehub + checklist de compliance incorporado)*
