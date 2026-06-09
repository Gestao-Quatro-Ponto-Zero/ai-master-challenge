# RotaDesk — API do classificador (Render)

TF-IDF + regressão logística (DS2), exposta via **FastAPI** para o Next.js em produção.

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Info do serviço |
| GET | `/health` | Status + se `pipeline.joblib` existe |
| POST | `/classify` | Body: `{"text": "..."}` → `topic_group`, `confidence`, `probabilities` |

## ⚠️ 404 em `/health` ou `/classify`?

O serviço Render está com **Root Directory errado** (apontando para a raiz do repo em vez de `ml/`).

No painel Render → **Settings**:

| Campo | Valor obrigatório |
|-------|-------------------|
| **Root Directory** | `submissions/jean-felipe/solution/rotadesk/ml` |
| **Runtime** | Python 3.11 **ou** Docker |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn api:app --host 0.0.0.0 --port $PORT` |

Salve → **Manual Deploy** → teste:

```
https://ai-master-challenge.onrender.com/health
```

Deve retornar `{"status":"ok","model_loaded":true}` — se ainda 404, o Root Directory não foi aplicado.

### Opção Docker (mais à prova de erro)

1. Render → Settings → **Environment** = Docker
2. Root Directory = `submissions/jean-felipe/solution/rotadesk/ml`
3. Usa o `Dockerfile` desta pasta automaticamente

## Modelo

`pipeline.joblib` já está no repositório. Para regenerar:

```bash
pip install -r requirements.txt
python train_export.py   # precisa do CSV do DS2 em data/
```

## Vercel (Next.js)

```
CLASSIFIER_API_URL=https://ai-master-challenge.onrender.com
```

Só a URL **base**, sem `/classify`. Redeploy na Vercel após o `/health` do Render responder 200.

## Teste local

```bash
pip install -r requirements.txt
uvicorn api:app --reload --port 8000
curl http://localhost:8000/health
curl -X POST http://localhost:8000/classify -H "Content-Type: application/json" -d "{\"text\": \"VPN not working\"}"
```
