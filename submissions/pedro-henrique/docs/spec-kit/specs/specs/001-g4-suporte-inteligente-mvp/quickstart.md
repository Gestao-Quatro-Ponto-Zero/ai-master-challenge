# Quickstart - G4 Suporte Inteligente (MVP)

## 1. Pré-requisitos

- Node.js 20+
- npm 10+
- Python 3.11+
- Conta Supabase (URL, anon key, service role key)
- Conta OpenAI (API key)
- Token Kaggle em `~/.kaggle/kaggle.json`

## 2. Preparar projeto web

```bash
cd submissions/pedro-henrique-silva/solution
npm install
cp .env.example .env.local
```

Preencher `.env.local`:

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `OPENAI_API_KEY`
- `HOURLY_AGENT_COST_BRL`

## 3. Configurar banco

- Executar SQL de schema em `solution/supabase/schema.sql` no Supabase SQL editor.
- Criar bucket `ticket-audio` no Supabase Storage.
- Garantir políticas de acesso para roles e RLS em tickets.

## 4. Gerar insights e base vetorial (offline)

```bash
cd submissions/pedro-henrique-silva/solution
python -m venv .venv
source .venv/bin/activate
pip install kagglehub pandas scikit-learn openai supabase
python scripts/download_datasets.py
python scripts/analyze_datasets.py
python scripts/populate_kb.py
```

Resultados esperados:
- `solution/public/insights.json` gerado
- tabela `support_tickets_kb` populada com embeddings

## 5. Rodar aplicação

```bash
cd submissions/pedro-henrique-silva/solution
npm run dev
```

Abrir:
- `http://localhost:3000/customer/new`
- `http://localhost:3000/customer/tickets`
- `http://localhost:3000/admin`
- `http://localhost:3000/admin/tickets`

## 6. Testes manuais mínimos de aceite

- Login de customer e admin funcionando
- Áudio de 30s transcrevendo em <= 8s
- Busca semântica retornando sugestão em <= 4s
- Clique em "Resolveu" registrando evento sem abrir ticket
- Clique em "Ainda preciso" criando ticket visível no admin
- Dashboard com 4 blocos e card de deflexão preenchidos
