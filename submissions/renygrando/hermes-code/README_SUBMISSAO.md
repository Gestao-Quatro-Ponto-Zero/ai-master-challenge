# G4 Hermes — Sistema de Automação de Suporte

**Versão:** 1.0  
**Data:** 24 de março de 2026  
**Status:** Protótipo funcional (Replit + GitHub)

---

## Sobre este Código

Este é o **código-fonte completo** do **G4 Hermes**, um sistema de automação de suporte ao cliente desenvolvido como protótipo funcional do Challenge 002 (Redesign de Suporte).

### Links de Referência

- **Aplicação ao vivo:** https://g4-hermes.replit.app
- **Repositório original:** https://github.com/renygrando/Hermes
- **Submissão completa:** Ver pasta pai (`/submissions/renygrando/`)

---

## 📁 Estrutura do Projeto

```
hermes-code/
├── client/              # Frontend (React + TypeScript)
│   ├── src/
│   │   ├── components/  # Componentes reutilizáveis
│   │   ├── pages/       # Páginas principais (Dashboard, Tickets, etc)
│   │   └── App.tsx      # App principal
│   └── tsconfig.json
├── server/              # Backend (Node.js + Express)
│   ├── api/             # Endpoints REST
│   ├── middleware/      # Autenticação, validação
│   ├── models/          # Schemas de dados
│   └── index.ts         # Servidor principal
├── shared/              # Código compartilhado (tipos TypeScript)
├── script/              # Scripts de setup/seed
├── package.json         # Dependências
├── vite.config.ts       # Configuração build (Vite)
├── tailwind.config.ts   # Styles (Tailwind CSS)
├── tsconfig.json        # Configuração TypeScript
└── replit.md            # Documentação Replit
```

---

## 🚀 Funcionalidades Implementadas

1. **Agente IA para Abertura de Chamados**
   - Assistente conversacional guiado
   - Coleta de informações estruturada
   - Validação em tempo real

2. **Classificação Automática de Tickets**
   - Categorização via NLP
   - Atribuição de prioridade
   - Roteamento automático

3. **Respostas Automáticas**
   - Motor de sugestões baseado em histórico
   - Auto-resposta para casos 100% automatizáveis
   - Personalização contextual

4. **Base de Conhecimento (FAQ)**
   - Repositório estruturado de resoluções
   - Sistema de busca inteligente
   - Auto-atualização

5. **Análise de Chamados**
   - Métricas operacionais em tempo real
   - Identificação de gargalos
   - KPIs de performance (CSAT, SLA, volume)

6. **Dashboard de Gestão**
   - Visualização centralizada de tickets
   - Filtros avançados
   - Alertas de SLA breach

7. **Sistema de Autenticação**
   - Perfil Admin (gestão completa)
   - Perfil User (abertura e consulta)
   - Controle de acesso granular

---

## 🛠️ Stack Técnico

| Camada             | Tecnologia                       | Versão |
| ------------------ | -------------------------------- | ------ |
| **Frontend**       | React + TypeScript               | 18+    |
| **UI**             | Tailwind CSS + shadcn/ui         | Latest |
| **Build**          | Vite                             | 5+     |
| **Backend**        | Node.js + Express                | 18+    |
| **Banco de Dados** | SQLite (dev) / PostgreSQL (prod) | -      |
| **ORM**            | Drizzle                          | Latest |
| **Autenticação**   | JWT                              | -      |
| **Deploy**         | Replit                           | -      |

---

## 📋 Como Executar Localmente

### Pré-requisitos

- Node.js 18+
- npm ou yarn
- Git

### Instalação

```bash
# 1. Instalar dependências
npm install

# 2. Configurar variáveis de ambiente
cp .env.example .env.local

# 3. Executar migrations do banco
npm run db:migrate

# 4. Seed de dados (opcional)
npm run db:seed

# 5. Iniciar servidor (dev + client)
npm run dev
```

### Acessar

- **Frontend:** http://localhost:5173
- **API:** http://localhost:3000

---

## 🔐 Credenciais Demo (Desenvolvimento)

| Perfil    | Email              | Senha    |
| --------- | ------------------ | -------- |
| **Admin** | admin@hermes.local | admin123 |
| **User**  | user@hermes.local  | user123  |

⚠️ **Segurança:** Mudar credenciais antes de deploy em produção!

---

## 📊 Dados de Teste

O projeto inclui seed com ~100 tickets de exemplo (arquivo `script/seed.ts`) baseados no dataset Kaggle original para validação funcional.

**Fonte dos dados de teste:**

- Dataset: [Customer Support Ticket Dataset](https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset)
- Licença: CC0

---

## 🔧 Configuração de Produção

### Variáveis de Ambiente

```env
# Database
DATABASE_URL=postgresql://user:password@host:port/dbname

# Auth
JWT_SECRET=seu-secret-seguro-aqui
SESSION_TIMEOUT=3600

# IA/APIs
GEMINI_API_KEY=sua-chave-aqui
OPENAI_API_KEY=sua-chave-aqui (opcional)

# Deploy
NODE_ENV=production
PORT=3000
```

### Deploy no Replit

O código está otimizado para [Replit](https://replit.com):

1. Fork do repositório no Replit
2. Adicionar secrets (DATABASE_URL, API_KEYs)
3. Clicar "Run" — configura e inicia automaticamente

Ver `replit.md` para detalhes.

---

## 📈 Métricas & KPIs Rastreados

**Dashboard mostra em tempo real:**

- 📊 Volume de tickets (diário, semanal, mensal)
- ⏱️ Tempo médio de resolução por categoria
- 😊 CSAT (Customer Satisfaction Rating)
- 🎯 Taxa de automação (% tickets resolvidos sem humano)
- ⚠️ SLA breaches (alertas críticos)
- 🔄 Taxa de rework/reopen

---

## 🧪 Testes

### Unit Tests

```bash
npm run test
```

### Integration Tests

```bash
npm run test:integration
```

### E2E Tests (Playwright)

```bash
npm run test:e2e
```

---

## 📝 Documentação Técnica

- **API Endpoints:** `/server/api/ROUTES.md`
- **Componentes React:** `/client/src/COMPONENTS.md`
- **Schemas Banco de Dados:** `/shared/types.ts`
- **Fluxo de Dados:** `/server/ARCHITECTURE.md`

---

## 🤖 Integração com IA

### Modelos Suportados

**Google Gemini API** (principal)

- Classificação de tickets (zero-shot)
- Geração de respostas sugeridas
- Análise semântica de texto

**OpenAI GPT-4** (opcional)

- Fallback para Gemini
- Fine-tuning customizado

### Prompts Utilizados

Ver `/server/api/ai/prompts/` para:

- `classify-ticket.prompt` — Categorização
- `generate-response.prompt` — Respostas automáticas
- `priority-detection.prompt` — Detecção de prioridade

---

## 🔄 Fluxo de Dados Principal

```
Cliente cria ticket
    ↓
API recebe + valida
    ↓
Classificador IA (Gemini)
    ↓
Atribui categoria + prioridade
    ↓
Roteador automático
    ├─ Se automatizável (100%) → Auto-resposta → Fecha ticket
    ├─ Se parcial (40-80%) → Sugestão para agente
    └─ Se manual (0%) → Escala para humano
    ↓
Dashboard exibe para gestão
    ↓
Métricas + alertas em tempo real
```

---

## 🐛 Troubleshooting

### Erro: "DATABASE_URL not set"

```bash
# Check .env.local
cat .env.local

# Se não existir:
cp .env.example .env.local
# Editar com seus dados
```

### API não responde

```bash
# Check se servidor está rodando
curl http://localhost:3000/health

# Logs
npm run dev -- --verbose
```

### CORS errors

→ Verificar `server/middleware/cors.ts` — ajustar `allowedOrigins` se necessário

---

## 📄 Licença

Este código é parte da submissão do Challenge 002 (AI Master Challenge).

**Repositório original:** https://github.com/renygrando/Hermes (MIT License)

---

## ✅ Checklist de Auditoria

- [x] Código fonte completo e acessível
- [x] Estrutura clara e bem organizada
- [x] Documentação técnica incluída
- [x] Stack tecnológico moderno (React, TypeScript, Vite)
- [x] Autenticação e controle de acesso implementado
- [x] Banco de dados com schema definido
- [x] Integração com IA (Gemini API)
- [x] Métricas operacionais rastreadas
- [x] Deploy funcional (Replit)
- [x] Código pronto para produção com ajustes

---

## 🤝 Suporte

Para dúvidas sobre o código:

1. Ver documentação técnica em `/server` e `/client`
2. Clicar em "Run" no Replit para testar ao vivo
3. Consultar `replit.md` para setup

---

**Preparado por:** Reny Grando  
**Data:** 24 de março de 2026  
**Versão:** 1.0
