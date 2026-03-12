# G4 Compass - Backend API Guide

Este documento detalha todos os endpoints da API para integração com o frontend.

## Detalhes Técnicos
- **Base URL:** `http://localhost:8080/api`
- **Autenticação:** JWT Bearer Token (`Authorization: Bearer <token>`)
- **Formatos:** IDs em **UUID v7**, Datas em **ISO 8601 (RFC3339)**

---

## 1. Autenticação

### `POST /auth/login`
**Request:** `{"email": "...", "password": "..."}`
**Response:** `{"token": "jwt", "user": { ... }}`

### `GET /me` (Protegido)
**Response:** Perfil do usuário logado.

---

## 2. Home / Briefing

### `GET /briefing` (Protegido)
Retorna KPIs e deals prioritários para a Home.
**Response:**
```json
{
  "kpis": [{ "label": "Pipeline total", "value": 3360000, "delta": 0.062 }],
  "hot_deals": [ { "id": "...", "name": "...", "score": 92 } ],
  "risk_deals": [ { "id": "...", "name": "...", "score": 42 } ],
  "insights": [ "..." ]
}
```

---

## 3. Pipeline & Deals

### `GET /deals` (Protegido)
Lista deals com filtros.
**Query Params:** `status`, `stage`, `seller_id`, `region`.

### `GET /deals/:id` (Protegido)
Detalhes do deal com explainability estruturada.
**Factors:** `[{ "factor": "...", "impact": 18, "sentiment": "positive" }]`

---

## 4. Agente Compass (Chat)

### `POST /chat` (Streaming SSE)
**Request:** `{"content": "...", "session_id": "..."}`
**Events:** `message` (JSON: `{"text": "...", "session_id": "..."}`) ou `error`.

### `GET /chat/history`
**Query Param:** `session_id=...`
**Response:** Histórico de mensagens.

---

## 5. Alertas

### `GET /alerts` (Protegido)
Categorizados por `today` e `week`.

---

## 6. Management & Reports (Admin)

### `GET /analytics/stats`
DADOS sintéticos para dashboard.

### `GET /stats/team`
KPIs agregados do time e ranking de sellers.

---

## 7. Importação (Manager)

### `POST /imports/upload`
Upload de CSV (`deals`, `accounts`, `products`, `team`).

### `GET /imports`
Histórico de uploads.

### `DELETE /imports/:id`
Remove registro de importação.
