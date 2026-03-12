# Rotas Esperadas do Backend — G4 Compass (Sales Co-Pilot)

Este documento descreve **o que cada tela do frontend precisa do backend**: rotas, payloads e comportamento esperado. O objetivo e alinhar implementacao do backend com a experiencia desenhada no frontend.

## Convencoes gerais
- Todas as rotas (exceto auth) exigem `Authorization: Bearer <token>`.
- Respostas devem ser multi-tenant e filtradas por usuario (vendedor ou manager).
- `role` do usuario deve vir no login (`seller` | `manager`) para controlar visoes no frontend.
- Datas em ISO 8601.

---

## 1. Autenticacao

### `POST /api/auth/login`
**Uso:** login interno (credenciais enviadas por email).  
**Request:**
```json
{ "email": "user@empresa.com", "password": "senha" }
```
**Response:**
```json
{
  "token": "jwt",
  "user": {
    "id": "uuid",
    "name": "Camila Torres",
    "email": "user@empresa.com",
    "role": "seller",
    "team_id": "uuid",
    "manager_id": "uuid",
    "region": "Central"
  }
}
```

### `GET /api/me`
**Uso:** recuperar contexto do usuario logado (nome, role, time, regiao).  
**Response:** mesmo objeto `user` do login.

---

## 2. Home / Briefing (`/briefing`)

### `GET /api/briefing`
**Uso:** dados para cards de briefing.  
**Response (seller):**
```json
{
  "kpis": [
    { "label": "Pipeline total", "value": 3360000, "delta": 0.062 },
    { "label": "Deals em risco", "value": 18, "delta": 4 }
  ],
  "hot_deals": [ { "id": "deal_id", "name": "Acme", "score": 92, "stage": "Engaging", "days": 18, "value": 420000, "action": "Agendar call final" } ],
  "risk_deals": [ { "id": "deal_id", "name": "Umbrella", "score": 42, "stage": "Engaging", "days": 74, "value": 260000, "action": "Reengajar sponsor" } ],
  "insights": [ "3 deals entraram na janela ideal..." ]
}
```
**Response (manager):** inclui `team_snapshot` e KPIs agregados do time.

---

## 3. Pipeline Priorizado (`/pipeline`)

### `GET /api/deals`
**Uso:** lista priorizada com filtros.  
**Query params:**
- `status=hot|risk|stalled`
- `stage=Prospecting|Engaging|Closing`
- `seller_id=...`
- `manager_id=...`
- `region=Central|East|West`

**Response:**
```json
[
  {
    "id": "deal_id",
    "name": "Acme Logistica",
    "score": 92,
    "stage": "Engaging",
    "days": 18,
    "value": 420000,
    "trend": 0.12,
    "status": "hot",
    "action": "Agendar call final"
  }
]
```

---

## 4. Deal Detail (Explainability) (`/deal/:id`)

### `GET /api/deals/:id`
**Uso:** detalhes do deal + explainability.  
**Response:**
```json
{
  "id": "deal_id",
  "name": "Acme Logistica",
  "score": 92,
  "stage": "Engaging",
  "days": 18,
  "value": 420000,
  "owner": "Camila Torres",
  "trend": 0.12,
  "factors": [
    { "factor": "Timing vs ciclo medio", "impact": 18, "detail": "18 dias vs 52 dias", "sentiment": "positive" }
  ],
  "next_actions": [
    "Agendar call de decisao com o sponsor"
  ]
}
```

---

## 5. Compass (Chat) (`/`)

### `POST /api/chat` (streaming)
**Uso:** chat com agente.  
**Request (texto):**
```json
{ "content": "Quais meus deals mais quentes?", "session_id": "uuid" }
```
**Response:** streaming (SSE ou WS) com chunks e `done`.

### `GET /api/chat/history`
**Uso:** carregar historico do chat.  
**Response:** array de mensagens `{ id, role, content }`.

---

## 6. Alertas (`/alerts`)

### `GET /api/alerts`
**Uso:** lista de alertas do usuario.  
**Response:**
```json
{
  "today": [
    { "id": "alert_id", "title": "Deal entrou na janela ideal", "deal": "Acme", "type": "positive", "action": "Agendar call final", "time": "09:12" }
  ],
  "week": [
    { "id": "alert_id", "title": "Deal em risco", "deal": "Umbrella", "type": "risk", "action": "Reengajar sponsor", "time": "Ter, 16:30" }
  ]
}
```

---

## 7. Relatorios (Manager) (`/reports`)

### `GET /api/stats/team`
**Uso:** KPIs do time, pipeline por regiao e gargalos.  
**Response:**
```json
{
  "kpis": [
    { "label": "Pipeline total", "value": 3360000, "delta": 0.062 }
  ],
  "by_region": [
    { "region": "Central", "value": 1420000, "delta": 0.12 }
  ],
  "by_stage": [
    { "stage": "Prospecting", "value": 0.34, "note": "Gargalo inicial" }
  ],
  "top_sellers": [
    { "name": "Camila Torres", "win_rate": 0.7, "pipeline": 420000, "trend": 0.08 }
  ]
}
```

---

## 8. Bases (CSV) — Manager (`/imports`)

### `POST /api/imports`
**Uso:** upload de CSV (multipart).  
**Response:**
```json
{ "import_id": "uuid", "status": "processing" }
```

### `GET /api/imports`
**Uso:** historico de uploads.  
**Response:**
```json
[
  { "id": "uuid", "file": "sales_pipeline.csv", "size": 2100000, "status": "processed", "updated_at": "2026-03-12T09:12:00Z" }
]
```

### `POST /api/imports/:id/reprocess`
**Uso:** reprocessar upload falho.

### `DELETE /api/imports/:id`
**Uso:** remover import.

---

## 9. Configuracoes (`/settings`)

### `GET /api/settings`
**Uso:** preferencias do usuario.  
### `PATCH /api/settings`
**Uso:** atualizar notificacoes, horario de briefing, preferencia de alertas.

---

## 10. Filtros Globais

Todos os endpoints que retornam deals devem aceitar:
- `seller_id`
- `manager_id`
- `region`

O backend deve validar esses filtros com base no `role` do usuario (seller nao pode consultar outro seller; manager pode).
