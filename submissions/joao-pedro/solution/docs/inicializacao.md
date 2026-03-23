# 🚀 Inicialização do Projeto

## ⚡ Resumo Rápido

> Três terminais, três comandos. Cada serviço roda de forma independente.
>
> **Streamlit:** páginas como `Deals_Analysis.py` usam **Plotly** (`plotly.express`). Com o `venv` ativo, instale dependências Python antes do primeiro run — por exemplo `pip install -r requirements.txt` (inclui `plotly` se listado no arquivo). Detalhes em **Plotly (páginas Streamlit)** nos Pré-requisitos.

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


> A primeira inicialização - sobretudo no streamlit - demora alguns segundos.
> No primeiro carregamento, o sistema executa três etapas em sequência:
>
> - **Leitura e join dos dados** — os quatro CSVs do CRM são carregados e cruzados em memória
> - **Cálculo de benchmarks** — medianas históricas, win rates por vendedor, produto e região são computados sobre as ~8.800 oportunidades
> - **Warm-up do cache** — a API pré-aquece o cache no startup para que todas as requisições subsequentes sejam imediatas
>
> Após a primeira inicialização, o sistema roda em cache, respondendo instantaneamente.



| Serviço | URL | Depende de |
|---|---|---|
| Streamlit | `http://localhost:8501` | `core/` (direto, sem API) |
| FastAPI | `http://localhost:8001` | `core/` (direto) |
| Swagger UI | `http://localhost:8001/docs` | FastAPI rodando |
| React | `http://localhost:5173` | FastAPI rodando |

---

## 📋 Pré-requisitos

Antes de rodar qualquer serviço, verifique:

### Python + virtualenv

```bash
# A partir de deal-prioritization/
source venv/bin/activate        # macOS / Linux
# ou: venv\Scripts\activate     # Windows

# Confirmar que o ambiente está ativo:
which python                    # deve apontar para .../venv/bin/python
```

> O `venv` já está criado no repositório. Se precisar recriar:
> ```bash
> python3 -m venv venv
> venv/bin/pip install -r requirements.txt
> ```

### Plotly (páginas Streamlit)

Algumas páginas em `streamlit_app/pages/` importam **Plotly** (ex.: `import plotly.express as px` em `Deals_Analysis.py`). Sem o pacote `plotly` no ambiente ativo, o Streamlit falha ao abrir essas páginas.

**Com o `venv` ativo** (recomendado):

```bash
pip install "plotly>=5.18.0"
```

Se `plotly` já estiver listado em `requirements.txt`, o `pip install -r requirements.txt` instala junto com as demais dependências. Confira com:

```bash
python -c "import plotly; print(plotly.__version__)"
```

**Sem `venv` (Python do sistema — macOS):**

Se o Streamlit estiver rodando com o Python do sistema em vez de um virtualenv, use o pip correspondente:

```bash
/Library/Frameworks/Python.framework/Versions/3.13/bin/pip3 install "plotly>=5.18.0"
```

Confira com:

```bash
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 -c "import plotly; print(plotly.__version__)"
```

### Node.js + npm

```bash
node --version    # v18+ recomendado
npm --version     # v9+
```

> Se for a primeira vez rodando o frontend:
> ```bash
> cd deal-prioritization/frontend
> npm install
> ```

---

## 🖥️ Serviço 1 — Streamlit (Frontend A)

**O que é:** Interface de análise e exploração de dados. Acessa o `core/` diretamente, **sem depender da API**.

**Porta:** `8501` (padrão do Streamlit)

**Como rodar:**

```bash
cd deal-prioritization
source venv/bin/activate
streamlit run streamlit_app/app.py
```

**O que acontece na inicialização:**
- Streamlit carrega o `app.py` que define o hub de navegação
- Ao acessar qualquer página de dados, o `@st.cache_data(ttl=3600)` carrega os CSVs e calcula benchmarks na primeira requisição
- O cache persiste por 1 hora — recargas subsequentes são instantâneas

**Para parar:** `Ctrl+C` no terminal

---

## ⚡ Serviço 2 — FastAPI REST

**O que é:** API REST que expõe o motor de scoring via HTTP. Necessária para o frontend React.

**Porta:** `8001`

**Como rodar (obrigatório — não há mais script `run_api.sh`):**

Sempre use o **Uvicorn** manualmente, a partir da raiz do projeto, com o `venv` ativo:

```bash
cd deal-prioritization
source venv/bin/activate
uvicorn api.main:app --reload --port 8001
```

> **Porta 8001:** se o comando falhar com “address already in use”, outro processo está usando a porta. Identifique e encerre esse processo (ou use outra porta e alinhe o `VITE_API_URL` no React). O antigo `run_api.sh` liberava a porta automaticamente; sem ele, isso precisa ser feito à mão quando necessário.

**O que acontece na inicialização:**
- O FastAPI executa o evento `startup` que pré-aquece o `lru_cache` com benchmarks e pipeline
- Isso garante que a primeira requisição já seja rápida
- O cache persiste durante todo o lifetime do processo Uvicorn

**Endpoints disponíveis após subir:**
- Swagger interativo: `http://localhost:8001/docs`
- Health check: `http://localhost:8001/health`
- OpenAPI spec: `http://localhost:8001/openapi.json`

**Para parar:** `Ctrl+C` no terminal

---

## ⚛️ Serviço 3 — React (Frontend B)

**O que é:** UI definitiva voltada para o vendedor. Consome a FastAPI REST. **Requer a API rodando.**

**Porta:** `5173` (padrão do Vite)

**Como rodar:**

```bash
cd deal-prioritization/frontend
npm run dev
```

**O que acontece na inicialização:**
- Vite sobe um servidor de desenvolvimento com HMR (Hot Module Replacement)
- O React carrega o `App.tsx` com React Router + TanStack Query configurados
- As páginas fazem requisições para `http://localhost:8001` (definido em `VITE_API_URL`)

**Status atual:** Infraestrutura completa (roteamento, tipos, fetchers, hooks, componentes base). Páginas ainda não implementadas.

**Para parar:** `Ctrl+C` no terminal

---

## 🔁 Ordem de inicialização recomendada

```
1. Streamlit  →  independente, pode subir isolado
2. FastAPI    →  independente, pode subir isolado
3. React      →  depende da FastAPI para dados
```

O Streamlit e a FastAPI são **completamente independentes entre si** — ambos importam o `core/` diretamente. Apenas o React depende da FastAPI.

---

## 🛠️ Problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| `streamlit: command not found` | venv não ativado | `source venv/bin/activate` |
| `ModuleNotFoundError: core` | Rodando de pasta errada | `cd deal-prioritization` antes |
| `ModuleNotFoundError: No module named 'plotly'` | Pacote Plotly não instalado no venv (páginas Streamlit com gráficos) | Ativar o `venv` e rodar `pip install plotly` (ou `pip install -r requirements.txt` se `plotly` estiver no arquivo) |
| Porta 8001 ocupada por outra API | Outro processo na porta | Encerre o processo (ex.: `lsof -i :8001` no macOS/Linux e `kill` no PID) ou reinicie o terminal após parar o Uvicorn com `Ctrl+C` |
| Swagger mostra API errada | Processo errado na porta 8001 | Garanta que só a API deste projeto está em `8001`; mate o processo conflitante e suba de novo com `uvicorn` |
| React não carrega dados | FastAPI não está rodando | Suba a API primeiro |
| `npm: command not found` | Node não instalado | Instalar Node.js v18+ |
| `npm install` falhou | Dependências desatualizadas | Deletar `node_modules/` e rodar novamente |

---

## 🗂️ Variáveis de ambiente

### React (`frontend/.env.local`)

Crie o arquivo se precisar customizar a URL da API:

```env
VITE_API_URL=http://localhost:8001
```

> Por padrão, `src/api/client.ts` já usa `http://localhost:8001` como fallback se a variável não estiver definida.

### FastAPI

Sem variáveis de ambiente necessárias. Os paths dos CSVs são resolvidos relativamente ao `core/data_loader.py`.
