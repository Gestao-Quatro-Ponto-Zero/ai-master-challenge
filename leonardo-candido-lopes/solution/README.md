# Solução — Challenge 002

## Estrutura

- `data/`: datasets originais públicos usados no desafio.
- `analysis/`: EDA, resultados e relatório de qualidade dos dados.
- `fase3/`: diagnóstico executivo, redesign, matriz, fluxo, KPIs, riscos e ROI.
- `fase4/ml/`: pipeline, modelo, avaliação, splits, regras, testes e documentação.
- `fase4/api/`: API FastAPI.
- `fase4/app/nextjs_space/`: interface Next.js.
- `fase4/evidencias/`: capturas e logs da interface.

## Execução local do protótipo

### 1. API Python

Na raiz desta pasta `solution/`:

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r fase4/api/requirements.txt
python fase4/api/main.py
```

A API sobe em `http://localhost:8000`. Verifique `GET /health`.

### 2. Frontend Next.js

Em outro terminal:

```bash
cd fase4/app/nextjs_space
npm install
npm run dev
```

A interface fica em `http://localhost:3000`. Por padrão, as rotas Next.js encaminham as chamadas para `http://localhost:8000`. Se necessário, configure `CLASSIFIER_API_URL` no ambiente do frontend.

### 3. Dependências ML

O backend carrega os arquivos `.pkl` em `fase4/ml/model/` e importa os módulos em `fase4/ml/`. Não mova os arquivos do modelo isoladamente.

**Importante:** o protótipo é demonstrativo e local. A versão submetida não executa ações externas nem roteia tickets automaticamente. Toda recomendação requer confirmação humana.
