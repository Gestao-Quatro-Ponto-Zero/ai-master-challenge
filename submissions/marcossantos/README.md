# Submissão — Marcos Santos — Challenge 003 — Lead Scorer

## Sobre mim

- **Nome:** Marcos Santos
- **LinkedIn:** https://www.linkedin.com/in/marcos-santos/
- **Challenge escolhido:** 003 — Lead Scorer · Vendas / RevOps

---

## Executive Summary

Construí o Lead Scorer, uma plataforma web completa de priorização de deals para o time de vendas. A solução vai além do pedido: além do dashboard com scoring explicável, implementei autenticação JWT com roles, alertas automáticos com notificação por email, histórico de contatos que alimenta o score em tempo real, e analytics para managers — tudo com código limpo e separação de responsabilidades clara. O resultado é uma ferramenta que um vendedor abre na segunda-feira de manhã e sabe exatamente onde focar, com explicação do porquê de cada score.

---

## Como rodar o projeto

### Pré-requisitos
- Python 3.10+
- Node.js 18+

### 1. Dataset (obrigatório)

Baixe o dataset do Kaggle:  
👉 https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics

Coloque os 4 CSVs dentro de `backend/data/`:

```
backend/
└── data/
    ├── sales_pipeline.csv
    ├── accounts.csv
    ├── products.csv
    └── sales_teams.csv
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
```

**Windows (PowerShell):**
```powershell
$env:PYTHONPATH = "."
python -m uvicorn main:app --reload --port 8000
```

**Mac / Linux:**
```bash
PYTHONPATH=. uvicorn main:app --reload --port 8000
```

✅ API em: `http://localhost:8000`  
✅ Swagger: `http://localhost:8000/docs`

### 3. Frontend

Abra um **novo terminal**:

```bash
cd frontend
npm install
npm run dev
```

✅ Dashboard em: `http://localhost:5173`

### 4. Logins de demo

| Perfil | Email | Senha | Acesso |
|--------|-------|-------|--------|
| Admin | admin@leadscorer.com | admin123 | Pipeline completo + analytics |
| Manager | melanie@leadscorer.com | senha123 | Time + analytics |
| Agent | hayden@leadscorer.com | senha123 | Próprios deals |

### 5. (Opcional) Notificações por email

Edite `backend/.env`:

```env
EMAIL_ENABLED=true
EMAIL_USER=seu_email@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx
ALERT_RECIPIENT=destinatario@gmail.com
```

> App Password do Gmail: https://myaccount.google.com/apppasswords

Teste pelo Swagger:
- `POST /api/notifications/test-alert` → email de alerta imediato
- `POST /api/notifications/test-digest` → resumo diário agora

---

## Solução

### Abordagem

Antes de escrever qualquer código, discuti a arquitetura com IA e revisei os critérios de qualidade do challenge para identificar gaps. A primeira proposta tinha só features óbvias (stage, valor, tamanho da conta) — revisamos antes de codar e adicionamos 3 features não-óbvias que fazem a diferença real no scoring.

Stack escolhida: **Python + FastAPI** no backend (fit natural com pandas para os CSVs), **React** no frontend. Decisão pragmática para demo local: menos boilerplate, setup rápido, pandas é a ferramenta certa para o trabalho.

### Resultados / Findings

**Scoring engine com 6 fatores (0–100 pts):**

| Fator | Peso | Por que importa |
|---|---|---|
| Stage Score | 25 pts | Engaging > Prospecting — mais perto do fechamento |
| Velocity ⭐ | 25 pts | Compara vs. média histórica de Won deals *do produto específico* |
| Account Fit | 20 pts | Porte + setor vs. perfil de contas que fecham |
| Product Win Rate ⭐ | 15 pts | GTX Pro fecha 65% vs MG Special 30% nos dados reais |
| Agent Performance ⭐ | 15 pts | Win rate histórico do vendedor responsável |
| Notes Activity ⭐ | 10 pts | Contato recente documentado prediz engajamento |

Os fatores marcados com ⭐ vão além do óbvio. O Velocity Score é o mais impactante: compara o deal contra a média histórica de Won deals **daquele produto específico** — captura esfriamento contextualizado.

**O que foi construído além do mínimo:**

- **JWT + Roles** — agent vê só os próprios deals, manager vê o time, admin vê tudo
- **Senhas bcrypt** — work factor 12, migração automática no startup
- **Sistema de alertas** — scheduler assíncrono a cada 15min, 4 tipos de alerta com deduplicação
- **Notificação por email** — alerta crítico dispara email imediato + resumo diário agendado
- **Deal Notes** — vendedor registra contatos e o score atualiza automaticamente
- **Analytics para manager** — ranking de vendedores, funil por produto, deals em risco por região
- **Interface CRM** — paleta profissional, score bars inline, painel com breakdown fator a fator

**22 endpoints** organizados em 7 módulos: data, scoring, auth, alerts, notes, analytics, notifications.

### Recomendações

Para produção, as prioridades seriam:

1. Conectar ao CRM real (Salesforce/HubSpot) via webhook — elimina o CSV estático
2. Migrar para PostgreSQL — persistência real para notas e alertas
3. XGBoost treinado nos dados históricos com SHAP values — mantém explainability
4. Script de sync de usuários a partir do `sales_teams.csv`

### Limitações

- Pipeline reflete snapshot dos CSVs no startup — sem atualização em tempo real
- Notas e alertas em JSON — funciona, mas não é banco de dados
- JWT sem refresh token — sessão expira em 8h
- `users.json` precisa ter nomes idênticos aos do CSV para filtros por role funcionarem

---

## Process Log — Como usei IA

**Ferramenta principal:** Claude (Anthropic) via claude.ai — pair programmer do início ao fim.

### Ferramentas usadas

| Ferramenta | Para que usou |
|---|---|
| Claude (claude.ai) | Arquitetura, geração de código, debugging, documentação |

### Workflow

1. **Pedi arquitetura antes de codar** — discutimos stack, separação de módulos e trade-offs antes de qualquer código
2. **Revisei critérios de qualidade com a IA** — identificamos que a primeira proposta tinha só features óbvias. Revisamos a arquitetura para incluir features não-óbvias e explainability real
3. **Geração módulo por módulo** — loader → factors → engine → main → auth → alerts → notes → analytics → notifications → frontend
4. **Debugging de erros reais no Windows** — colei mensagens do terminal e recebi causa + solução diretamente
5. **Iteração contínua** — a cada módulo novo, revisamos o que já existia para manter consistência

### Onde a IA errou e como corrigi

- **DATA_DIR errado** — calculou path com base em estrutura que eu não tinha. Corrigi para `Path(__file__).parent`
- **`users.json` com nomes fictícios** — nomes precisam bater com o CSV. Corrigi consultando o `sales_teams.csv`
- **Import circular no fator de notas** — corrigi movendo o import para dentro da função

### O que eu adicionei que a IA sozinha não faria

- **Decisão de stack** — avaliei o argumento da IA contra Java/Spring Boot e decidi
- **Priorização das features** — decidi manter scoring por regras em vez de ML porque explainability vale mais para esse público
- **Sequência de desenvolvimento** — decidi a ordem dos módulos
- **Escopo além do mínimo** — bcrypt, email com digest diário, analytics para manager foram decisões minhas

---

## Evidências

- [x] **Narrativa escrita** — process-log.md com linha do tempo, decisões e debugging documentados
- [x] **Git history** — commits mostrando evolução da solução na branch `submission/marcossantos`
- [x] **Código funcional** — backend + frontend completos na pasta `submissions/marcossantos/`

---

*Submissão enviada em: junho de 2026*