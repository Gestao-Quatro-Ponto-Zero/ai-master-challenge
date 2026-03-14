# Como Usar — G4 IA: Inteligência de Suporte

## Pré-requisitos

- Python 3.10+
- Node.js 18+
- API key do Google Gemini (gratuita em [aistudio.google.com](https://aistudio.google.com))

---

## Instalação e Configuração

### 1. Backend

```bash
cd solution/backend
pip install -r requirements.txt
```

Crie o arquivo `.env` a partir do template:

```bash
cp .env.example .env
```

Abra o `.env` e insira sua API key:

```
GOOGLE_API_KEY=sua_chave_aqui
```

Inicie o servidor:

```bash
uvicorn main:app --reload --port 8000
```

Na primeira execução, o sistema indexa ~56.500 documentos na base RAG (pode levar alguns minutos). As embeddings ficam cacheadas em `.cache/` para as próximas inicializações.

### 2. Frontend

```bash
cd solution/frontend
npm install
npm run dev
```

Acesse **http://localhost:3000**. O frontend faz proxy automático das chamadas `/api/*` para o backend em `localhost:8000`.

---

## Credenciais de Acesso

| Perfil  | Email                        | Senha       |
|---------|------------------------------|-------------|
| Agente  | `agente1@g4suporte.com`      | `agente123` |
| Agente  | `agente2@g4suporte.com`      | `agente123` |
| Agente  | `agente3@g4suporte.com`      | `agente123` |
| Gestor  | `gestor@g4suporte.com`       | `gestor123` |
| Diretor | `diretor@g4suporte.com`      | `diretor123`|

---

## Como Testar

### Criar ticket manualmente

1. Faça login como **agente**
2. Clique em **"Novo Ticket"**
3. Descreva o problema do cliente, selecione o canal e envie
4. O sistema classifica automaticamente em uma das 8 categorias, avalia severidade e toma a ação adequada

### Importar dados da empresa (CSV/XLSX)

1. Faça login como **gestor**
2. Acesse **"Importar Dados"** no menu lateral
3. Envie um arquivo CSV ou XLSX com pelo menos uma coluna de texto (ex: `texto`, `Document`, `Ticket Description`)
4. Os dados são indexados na base RAG para melhorar as respostas da IA

### Integrar via Webhook (CRM/Zendesk/Salesforce)

Envie tickets automaticamente via API:

```bash
curl -X POST http://localhost:8000/webhook/ticket \
  -H "Content-Type: application/json" \
  -H "X-API-Key: g4-webhook-key-2026" \
  -d '{"texto": "Não consigo acessar minha conta", "cliente": "João Silva", "canal": "email"}'
```

### Consultar a Base RAG

1. Como agente, acesse **"Base RAG — Soluções"** no menu lateral
2. Descreva um problema e busque soluções já aplicadas em tickets similares

---

## O que cada perfil vê

### Agente (operação)

- **Fila de Tickets** — tickets em aberto, filtro por severidade, botões "Assumir" e "Resolver"
- **Resolvidos** — histórico de tickets resolvidos
- **Base RAG — Soluções** — busca semântica por soluções já aplicadas
- **Detalhe do Ticket** — resumo IA, soluções sugeridas (para críticos), ações de resolução/escalação

### Gestor (governança)

- **Dashboard** — métricas consolidadas por período
- **Volume por Nível** — distribuição de tickets por severidade
- **Motivos por Nível** — top motivos de abertura com filtros
- **Alertas** — notificações automáticas quando volume excede limites (atualiza a cada 10s)
- **Agentes Online** — status em tempo real dos agentes
- **Gestão de Equipe** — CRUD de usuários (criar, editar, ativar/desativar)
- **Importar Dados** — upload de CSV/XLSX para alimentar o RAG
- **Diagnóstico** — análise operacional do Dataset 1 com gráficos e KPIs

---

## Lógica de Triagem (3 níveis)

| Severidade | Ação da IA | Papel do humano |
|------------|-----------|-----------------|
| **Baixo** | Classifica + responde automaticamente → ticket resolvido | Nenhum |
| **Médio** | Classifica + responde + notifica agente | Monitora |
| **Crítico** | Classifica + resume + gera 3 soluções + escala | Agente resolve com apoio da IA |

---

## Stack Técnica

| Componente | Tecnologia |
|-----------|-----------|
| Backend | FastAPI (Python) |
| Frontend | Next.js 14 + Tailwind CSS + Recharts |
| LLM | Gemini 3.1 Flash Lite |
| Embeddings / RAG | Gemini Embedding 2 (768d) |
| Autenticação | JWT |
| Fallback | DeBERTa + templates (quando Gemini indisponível) |
