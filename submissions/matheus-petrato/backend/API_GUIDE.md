# G4 Compass - Backend API Guide (Final & Aligned) 🚀

Este guia reflete os contratos finais da API, suportando 100% das telas e fluxos do frontend (Pipeline, Home, Reports, Chat e Admin).

## Informações Gerais
- **Base URL:** `http://localhost:8080/api`
- **Autenticação:** JWT Bearer Token (`Authorization: Bearer <token>`)
- **Formatos:** IDs em **UUID v7**, Datas em **RFC3339**.

---

## Configuração (Variáveis de Ambiente)
O backend utiliza as seguintes ENVs (veja `.env.example` para detalhes):
- `DATABASE_URL`: String de conexão PostgreSQL (ex: `postgres://user:pass@host:port/db`).
- `JWT_SECRET`: Chave para assinatura dos tokens JWT.
- `MERCURY_API_KEY`: Chave da API Mercury para o agente inteligente.
- `ENV`: Defina como `development` para habilitar o override de senha `admin123`.

---

## Credenciais de Teste (Seeding)
Utilize as credenciais abaixo após subir o banco com `docker compose up`:

- **Gestora (Manager):** `camila@g4.com` / `admin123`
- **Vendedor (Seller):** `joao@g4.com` / `admin123`

---

## 1. Autenticação & Perfil do Usuário

### `POST /auth/login` | `GET /me`
Retornam o perfil completo necessário para permissões e filtros.

**Response Body:**
```json
{
  "id": "uuid",
  "name": "João da Silva",
  "email": "joao@g4.com",
  "role": "seller | manager",
  "region": "São Paulo", 
  "team_id": "uuid", 
  "manager_id": "uuid",
  "sales_agent_id": "uuid (nulo se for manager)",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

---

## 2. Visão Home (Briefing)

### `GET /briefing`
Retorna dados personalizados baseados no `role`.

**Se for Seller:**
- `kpis`: Resumo pessoal (Pipeline total, Deals em risco).
- `hot_deals`: Top 5 deals com score alto.
- `risk_deals`: Deals estagnados ou com score baixo.
- `insights`: Sugestões em texto.

**Se for Manager:**
- `team_snapshot`: `{ "total_value": 0, "active_agents": 0, "avg_health": 0 }`
- `kpis`: Resumo agregado do time.
- `critical_deals`: Deals de qualquer vendedor que precisam de atenção.
- `insights`: Alertas de gargalos no time.

---

## 3. Pipeline de Negócios

### `GET /deals`
Lista deals com **validação de papel nativa no backend**.

**Query Params:**
- `status`: (hot | risk | warm | cold)
- `stage`: Estágio do funil.
- `seller_id`: ID do vendedor (ignorável se role=seller).
- `manager_id`: ID do gestor.
- `region`: Nome da região.

**Comportamento de Segurança:**
- **Seller:** Mostra apenas seus próprios deals.
- **Manager:** Visualiza qualquer deal conforme os filtros.

### `GET /deals/:id`
Detalhes com explainability:
- `factors`: `[{ "factor": "Timing", "impact": 30, "sentiment": "positive", "detail": "..." }]`

---

## 4. Agente Compass (Chat)

### `POST /chat`
Inicia ou continua conversas com streaming.
- `session_id`: Opcional. Se não enviado, cria uma nova.

### `GET /chat/history`
**Query Param:** `session_id` (Opcional).
- **Fallback:** Se omitido, retorna o histórico da **última conversa** do usuário autenticado.

---

## 5. Relatórios Gerenciais (Reports)

### `GET /stats/team`
Consolidado para Managers.

**Estrutura da Resposta:**
- `kpis`: Lista de métricas agregadas com `delta`.
- `by_region`: `[{ "region": "Sul", "value": 500000, "delta": 0.1 }]`
- `by_stage`: `[{ "stage": "...", "value": 0.45, "note": "Gargalo inicial" }]`
- `top_sellers`: `[{ "name": "...", "win_rate": 0.7, "pipeline": 100000, "trend": 0.08 }]`

---

## 6. Importação (Manager Only)

### `POST /imports`
Upload de CSV de bases.

### `GET /imports`
Histórico: `[{ "id": "...", "file": "...", "status": "processing|success|failed", "updated_at": "...", "size": 0 }]`

### `POST /imports/:id/reprocess`
Reinicia o processamento de um arquivo já enviado.
