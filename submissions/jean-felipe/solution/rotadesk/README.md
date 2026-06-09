# RotaDesk — Protótipo Challenge 002

Suporte inteligente com **ack automático**, **triagem sklearn**, **LLM (gpt-4o-mini)** para baixa confiança, rascunhos e RAG.

Baseado em `../automacao/PROPOSTA.md` e `../automacao/fluxo.md`.

## Stack

- Next.js 16 + React 19 + Tailwind CSS v4
- Supabase (PostgreSQL)
- scikit-learn (TF-IDF + Logistic Regression, DS2)
- OpenAI gpt-4o-mini

## Setup

### 1. Dependências

```bash
npm install
pip install -r ml/requirements.txt
python ml/train_export.py
```

### 2. Supabase

1. Crie um projeto em [supabase.com](https://supabase.com)
2. Rode a migration `supabase/migrations/001_initial.sql` no SQL Editor
3. Copie `.env.local.example` → `.env.local` e preencha as chaves

### 3. Executar

```bash
npm run dev
```

Abra [http://localhost:3000](http://localhost:3000)

## Deploy na Vercel

O app fica em um subdiretório do monorepo. **Sem as duas configurações abaixo, a Vercel retorna 404.**

1. **Production Branch** (Settings → Git → Production Branch):  
   `submission/jean-felipe` **ou** `main` (após merge da submissão no fork)  
   > A branch `main` do fork **não** contém o app até o merge — deploy em `main` sem código = 404.
2. **Root Directory** (Settings → General):  
   `submissions/jean-felipe/solution/rotadesk`
3. **Environment Variables** (Settings → Environment Variables):
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `OPENAI_API_KEY`
4. **Build Command:** `npm run build` (padrão)
5. Redeploy após salvar branch, root directory e variáveis.

### Build OK mas 404 na URL?

O erro `404 NOT_FOUND` com ID `gru1::...` é da **plataforma Vercel** (não do Next.js). Se o build passou:

1. **Settings → Build and Deployment → Framework Settings → Framework Preset = `Next.js`** (não `Other` — causa #1 de 404 com build OK).
2. **Output Directory** deve estar **vazio** (deixe em Automatic / padrão do Next.js).
3. **Deployments** → deploy ✓ Ready → **Visit** (teste essa URL antes do domínio principal).
4. Se o preview abre: **⋯ → Promote to Production**.
5. **Root Directory** = `submissions/jean-felipe/solution/rotadesk` (sem `/` no final).
6. Desative **Include files outside the root directory**.
7. Se nada resolver: delete o projeto na Vercel e reimporte o repo (config corrompida).

## Classificador sklearn em produção (Render)

A Vercel **não executa Python**. O classificador roda numa **API FastAPI no Render**:

1. Deploy do serviço em `ml/` — ver [`ml/README.md`](./ml/README.md)
2. Na Vercel, configure `CLASSIFIER_API_URL=https://seu-servico.onrender.com`

Com isso, criar ticket em produção usa **sklearn na Render** → LLM se confiança &lt; 85% → roteamento. Localmente (`npm run dev`), sem `CLASSIFIER_API_URL`, continua usando `python ml/classify.py`.

## Páginas

| Rota | Função |
|------|--------|
| `/` | Dashboard — métricas, gráficos, últimos tickets |
| `/simulador` | Criar tickets como cliente (fluxo completo) |
| `/chat` | Atendimento simulado + rascunho RAG + resolver com IA |
| `/kanban` | Acompanhar chamados por status |

## Fluxo de ticket

1. **Ack** imediato + `first_response_at`
2. **Classificação** sklearn (`ml/pipeline.joblib`)
3. Se confiança **&lt; 85%** → **gpt-4o-mini** reclassifica
4. **Regras DS1**: Refund, Cancellation, Critical → humano obrigatório
5. **Administrative rights** → revisão humana
6. Roteamento para fila Supabase

## Threshold

Confiança mínima para auto-roteamento: **85%** (`src/lib/constants.ts`).
