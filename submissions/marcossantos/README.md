# Lead Scorer — CRM Sales Prioritization Tool

Ferramenta de priorização de deals para o time de vendas.  
O vendedor abre o dashboard, vê o pipeline ordenado por score e sabe exatamente onde focar.

---

## Índice

1. [Setup rápido](#setup-rápido)
2. [Estrutura do projeto](#estrutura-do-projeto)
3. [Lógica de scoring](#lógica-de-scoring)
4. [Autenticação e roles](#autenticação-e-roles)
5. [Sistema de alertas](#sistema-de-alertas)
6. [Deal Notes](#deal-notes)
7. [Analytics](#analytics)
8. [Notificações por email](#notificações-por-email)
9. [Referência da API](#referência-da-api)
10. [Limitações e próximos passos](#limitações-e-próximos-passos)

---

## Setup rápido

### Pré-requisitos
- Python 3.10+
- Node.js 18+

### 1. Dataset

Baixe o dataset do Kaggle:  
👉 https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics

Coloque os 4 CSVs dentro de `backend/data/`:

```
lead-scorer/
├── backend/
│   ├── data/
│   │   ├── sales_pipeline.csv   ← tabela central
│   │   ├── accounts.csv
│   │   ├── products.csv
│   │   └── sales_teams.csv
│   ├── main.py
│   └── ...
└── frontend/
    └── ...
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt

# Windows (PowerShell ou CMD)
$env:PYTHONPATH = "."
python -m uvicorn main:app --reload --port 8000

# Mac / Linux
PYTHONPATH=. uvicorn main:app --reload --port 8000
```

API disponível em: `http://localhost:8000`  
Documentação interativa (Swagger): `http://localhost:8000/docs`

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
# Abre em http://localhost:5173
```

### 4. Primeiro acesso

Abra `http://localhost:5173` e use um dos acessos de demo:

| Perfil  | Email                    | Senha    | O que vê                      |
|---------|--------------------------|----------|-------------------------------|
| Admin   | admin@leadscorer.com     | admin123 | Pipeline completo + analytics |
| Manager | melanie@leadscorer.com   | senha123 | Time dela + analytics         |
| Agent   | hayden@leadscorer.com    | senha123 | Só os próprios deals          |

---

## Estrutura do projeto

```
lead-scorer/
├── backend/
│   ├── main.py                    # Rotas FastAPI — sem lógica de negócio
│   ├── requirements.txt
│   ├── .env                       # Credenciais (não commitar)
│   ├── .gitignore
│   ├── users.json                 # Usuários de demo
│   ├── notes.json                 # Notas persistidas (gerado automaticamente)
│   ├── alerts.json                # Fila de alertas (gerado automaticamente)
│   │
│   ├── data/
│   │   └── loader.py              # Lê CSVs, join das 4 tabelas, métricas históricas
│   │
│   ├── scoring/
│   │   ├── factors.py             # 6 fatores — cada um é uma função isolada
│   │   └── engine.py              # Orquestra fatores → score 0-100 + ação
│   │
│   ├── models/
│   │   └── schemas.py             # Contratos Pydantic da API
│   │
│   ├── auth/
│   │   ├── models.py              # Schemas de autenticação
│   │   ├── service.py             # JWT manual + bcrypt para senhas
│   │   ├── dependencies.py        # get_current_user, require_role()
│   │   └── router.py              # POST /auth/login, GET /auth/me
│   │
│   ├── alerts/
│   │   ├── models.py              # Alert, AlertType, AlertSeverity
│   │   ├── detector.py            # 4 detectores independentes
│   │   ├── queue.py               # Persistência + deduplicação
│   │   ├── scheduler.py           # Job assíncrono a cada 15 min
│   │   └── router.py              # GET/POST /api/alerts
│   │
│   ├── notes/
│   │   ├── models.py              # Note, NoteCreate, NotesResponse
│   │   ├── store.py               # Persistência em notes.json
│   │   └── router.py              # GET/POST/DELETE /api/deal/{id}/notes
│   │
│   ├── analytics/
│   │   ├── models.py              # Schemas de analytics
│   │   ├── service.py             # Lógica de agregação isolada das rotas
│   │   └── router.py              # GET /api/analytics/{team,funnel,at-risk}
│   │
│   └── notifications/
│       ├── config.py              # Lê credenciais do .env
│       ├── sender.py              # SMTP Gmail + templates HTML
│       ├── digest.py              # Scheduler do resumo diário
│       └── router.py             # GET/POST /api/notifications
│
└── frontend/
    └── src/
        ├── App.jsx                # Roteamento login ↔ pipeline ↔ analytics
        ├── main.jsx               # Entrada React com AuthProvider
        ├── index.css              # Design tokens + estilos globais
        ├── context/
        │   └── AuthContext.jsx    # Estado global de auth, token em memória
        ├── hooks/
        │   └── useApi.js          # Hooks: usePipeline, useAlerts, useNotes, useAnalytics
        └── components/
            ├── LoginPage.jsx      # Tela de login com acesso rápido demo
            ├── Sidebar.jsx        # Filtros + navegação pipeline/analytics
            ├── TopBar.jsx         # KPIs + sino de alertas + usuário logado
            ├── DealsTable.jsx     # Tabela de deals com score bar inline
            ├── DetailPanel.jsx    # Painel deslizante: score + fatores + notas
            ├── AlertsPanel.jsx    # Painel de alertas com dismiss
            └── analytics/
                ├── AnalyticsPage.jsx   # Container com tabs
                ├── TeamRanking.jsx     # Ranking de vendedores
                ├── FunnelCharts.jsx    # Gráficos de stage e produto
                └── AtRiskTable.jsx     # Deals em risco por região
```

---

## Lógica de scoring

O score vai de **0 a 100** e é composto por **6 fatores**.  
Os 3 marcados com ⭐ vão além das features óbvias do enunciado.

### Fator 1 — Stage Score (0–25 pts)

| Stage | Pontos |
|-------|--------|
| Engaging | 25 |
| Prospecting | 10 |

### Fator 2 — Velocidade no Pipeline (0–25 pts) ⭐

Compara `days_in_pipeline` vs. média histórica de Won deals do mesmo produto.

| Ratio (dias / média do produto) | Pontos | Sinal |
|---------------------------------|--------|-------|
| ≤ 0.5x — muito rápido | 25 | 🟢 Momentum quente |
| 0.5–0.85x | 20 | 🟢 Ritmo bom |
| 0.85–1.2x — na média | 15 | 🟡 Normal |
| 1.2–1.8x | 8 | 🔴 Esfriando |
| > 1.8x | 2 | 🔴 Parado |

### Fator 3 — Fit da Conta (0–20 pts)

Porte da empresa (`employees` + `revenue`) vs. perfil histórico de contas que fecham.  
Bônus de +3 pts para setores com win rate acima da média global.

### Fator 4 — Win Rate do Produto (0–15 pts) ⭐

Win rate histórico calculado dos dados reais por produto.

### Fator 5 — Performance do Vendedor (0–15 pts) ⭐

Win rate histórico do vendedor responsável pelo deal.

### Fator 6 — Atividade de Contato (0–10 pts)

Baseado nas notas registradas no deal.

| Situação | Pontos |
|----------|--------|
| Nota nos últimos 2 dias | 10 |
| Nota nos últimos 5 dias | 7 |
| Nota nos últimos 10 dias | 3 |
| Sem notas (deal novo) | 5 neutro |
| Engaging sem nota há 10–20 dias | 0 ⚠ |
| Engaging sem nota há 20+ dias | 0 🚨 |

### Tiers

| Score | Tier | Ação gerada |
|-------|------|-------------|
| 70–100 | 🔥 HOT | "Ligue HOJE — deal prioritário esfriando" |
| 45–69 | 🌡 WARM | "Monitore — mantenha cadência" |
| 0–44 | ❄ COLD | "Reavalie — foque em prioritários primeiro" |

---

## Autenticação e roles

JWT implementado com `hmac` + `hashlib` do Python padrão (sem biblioteca externa).  
Senhas armazenadas com **bcrypt** (work factor 12) — migração automática no startup.  
Token válido por 8 horas, armazenado em memória no frontend (sem localStorage).

### Sistema de roles

| Role | Pipeline | Analytics | Notificações |
|------|----------|-----------|--------------|
| `agent` | Só os próprios deals | ✗ | ✗ |
| `manager` | Só o seu time | ✅ time dele | ✗ |
| `admin` | Pipeline completo | ✅ tudo | ✅ |

### Endpoints de auth

```
POST /auth/login   → { email, password } → { access_token }
GET  /auth/me      → dados do usuário logado
POST /auth/logout  → instrução para descartar o token
```

### Adicionar usuários

Edite `backend/users.json`. Os campos `sales_agent` e `manager` devem bater **exatamente** com os nomes nos CSVs.

```json
{
  "id": "9",
  "name": "Nome Completo",
  "email": "email@empresa.com",
  "password": "senha_em_texto",
  "role": "agent",
  "sales_agent": "Nome Completo",
  "manager": "Nome do Manager",
  "regional_office": "East"
}
```

> A senha é convertida para hash bcrypt automaticamente no próximo startup.

---

## Sistema de alertas

Scheduler roda 3 segundos após o startup e depois a cada 15 minutos.  
Alertas persistidos em `alerts.json` com deduplicação — o mesmo deal não gera dois alertas iguais.  
Alertas críticos também disparam **email imediato** se as notificações estiverem configuradas.

### Tipos de alerta

| Tipo | Quando dispara | Severidade |
|------|---------------|------------|
| `deal_stale` | Deal 1.5x acima da média do produto | warning |
| `deal_critical_stale` | Deal 2x+ acima da média | critical |
| `high_value_at_risk` | Deal de alto valor esfriando | critical |
| `no_engaging_deals` | Vendedor sem nenhum deal em Engaging | warning |

### Endpoints

```
GET  /api/alerts                  → alertas do usuário (filtrado por role)
POST /api/alerts/{id}/dismiss     → marca como visto
POST /api/alerts/dismiss-all      → marca todos como vistos
POST /api/alerts/refresh          → força detecção agora (manager/admin)
```

---

## Deal Notes

Vendedores registram contatos diretamente no deal.  
As notas alimentam o **Fator 6** do scoring — deals com contato recente sobem de score automaticamente.

```
GET    /api/deal/{id}/notes            → histórico de notas
POST   /api/deal/{id}/notes            → { "content": "Falei com o CEO..." }
DELETE /api/deal/{id}/notes/{note_id}  → remove nota (autor ou admin)
```

---

## Analytics

Disponível para `manager` e `admin` — acessível pelo menu lateral do dashboard.

```
GET /api/analytics/team     → ranking de vendedores com win rate e status de coaching
GET /api/analytics/funnel   → distribuição por stage e win rate por produto
GET /api/analytics/at-risk  → deals em risco agrupados por região
```

---

## Notificações por email

### Configuração

Edite o arquivo `backend/.env`:

```env
EMAIL_ENABLED=true
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=seu_email@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_FROM_NAME=Lead Scorer
ALERT_RECIPIENT=destinatario@gmail.com
DAILY_DIGEST_TIME=08:00
DAILY_DIGEST_ENABLED=true
```

> **Gmail:** gere uma App Password em https://myaccount.google.com/apppasswords  
> Não use sua senha normal — o Gmail bloqueia acesso via SMTP com senha comum.

### Tipos de notificação

**1. Alerta crítico (imediato)**  
Enviado automaticamente quando o scheduler detecta um alerta de severidade `critical`.  
Inclui: nome da conta, vendedor responsável, dias no pipeline e valor do deal.

**2. Resumo diário**  
Enviado no horário configurado em `DAILY_DIGEST_TIME`.  
Inclui: KPIs hot/warm/cold, valor total em pipeline, top 5 deals por score e contagem de alertas ativos.

### Testar (Swagger — login como admin)

```
GET  /api/notifications/status      → confirma configuração SMTP
POST /api/notifications/test-alert  → envia email de alerta agora
POST /api/notifications/test-digest → envia resumo diário agora
```

---

## Referência da API

### Pública

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/health` | Status da API |

### Autenticação

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/auth/login` | Login → JWT |
| GET | `/auth/me` | Dados do usuário logado |
| POST | `/auth/logout` | Logout |

### Pipeline

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/filters` | Opções de filtro |
| GET | `/api/pipeline` | Deals com scores |
| GET | `/api/deal/{id}` | Score detalhado |
| GET | `/api/summary` | KPIs do pipeline |

### Alertas

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/alerts` | Lista alertas |
| POST | `/api/alerts/{id}/dismiss` | Marca como visto |
| POST | `/api/alerts/dismiss-all` | Limpa todos |
| POST | `/api/alerts/refresh` | Força detecção |

### Notas

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/deal/{id}/notes` | Histórico |
| POST | `/api/deal/{id}/notes` | Adiciona nota |
| DELETE | `/api/deal/{id}/notes/{note_id}` | Remove nota |

### Analytics

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/analytics/team` | Ranking de vendedores |
| GET | `/api/analytics/funnel` | Funil de conversão |
| GET | `/api/analytics/at-risk` | Deals em risco |

### Notificações (admin)

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/notifications/status` | Status SMTP |
| POST | `/api/notifications/test-alert` | Teste de alerta |
| POST | `/api/notifications/test-digest` | Teste de digest |

### Admin

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/admin/users` | Lista usuários |

---

## Limitações e próximos passos

### O que a solução não faz

- **Sem ML preditivo** — scoring baseado em regras + heurísticas. Explicável e útil, mas não aprende automaticamente.
- **Sem banco de dados** — CSVs em memória, notas e alertas em JSON. Reiniciar o servidor relê tudo.
- **Sem atualização em tempo real** — pipeline reflete o snapshot dos CSVs no startup.
- **JWT sem refresh token** — sessão expira em 8h sem renovação automática.

### Para escalar para produção

1. **Banco de dados** — PostgreSQL + SQLAlchemy substituindo CSVs e JSONs
2. **Integração com CRM real** — webhooks Salesforce/HubSpot para pipeline em tempo real
3. **ML** — XGBoost treinado nos dados históricos com SHAP values para manter explainability
4. **Refresh token** — par access/refresh com rotação automática
5. **WebSocket** — alertas em push real-time em vez de polling a cada 60s