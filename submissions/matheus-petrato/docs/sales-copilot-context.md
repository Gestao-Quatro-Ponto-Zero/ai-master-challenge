# G4 Compass — Sales Co-Pilot
## Contexto da Aplicação

---

## O que é

G4 Compass é um **Sales Co-Pilot pessoal** para equipes de vendas B2B. É uma PWA que combina um pipeline inteligente com um agente de IA conversacional, entregando para cada vendedor uma visão priorizada dos seus deals e um assistente que responde perguntas em linguagem natural sobre o pipeline.

O problema que resolve: vendedores gastam tempo em deals que não vão fechar e deixam oportunidades boas esfriarem por falta de priorização. A ferramenta substitui o "feeling" por dados, mas de forma conversacional e acessível — não um dashboard que ninguém abre.

---

## Usuários

- **Vendedor:** acessa seu pipeline pessoal, conversa com o agente, recebe alertas proativos. Vê apenas seus próprios deals.
- **Manager:** visão consolidada do time, ranking de vendedores, deals críticos. Pode navegar pelo pipeline de cada vendedor do seu time.

O login define o contexto — o app sabe quem é o usuário e personaliza tudo automaticamente.

---

## Funcionalidades principais

**1. Daily Briefing (Home)**
Primeira tela após login. Mostra os top deals para focar na semana, deals entrando em zona de risco, e um insight proativo do agente. Orientado a ação, não a dados brutos.

**2. Pipeline priorizado**
Lista completa dos deals do vendedor ordenada por score (0–100). Cada deal exibe score, stage, dias no pipeline, receita potencial e indicador de tendência. Filtros por stage e status (quente, em risco, etc.).

**3. Deal Detail com Explainability**
Ao abrir um deal, o vendedor vê o score detalhado com os fatores que o compõem — positivos e negativos — e uma comparação com a média histórica. A explicação é em linguagem natural. Ex: *"Deals similares com esse produto fecham em 52 dias — este está no dia 38, dentro da janela ideal."*

**4. Chat com o Agente (Compass)**
Interface conversacional onde o vendedor pergunta em linguagem natural:
- *"Quais meus deals mais quentes essa semana?"*
- *"O deal com a Acme ainda tem chance?"*
- *"Como está meu pipeline comparado ao mês passado?"*

O agente é um ReAct agent com ferramentas específicas sobre o pipeline. Responde com texto contextualizado e cards de deals inline quando relevante.

**5. Alertas proativos**
O agente roda em background (scheduler) e envia notificações push sem o vendedor precisar abrir o app:
- Deal entrou na janela ideal de fechamento
- Deal estagnado ultrapassou ciclo médio
- Lembrete semanal com os deals priorizados

**6. Perfil e configurações**
Stats pessoais do vendedor (win rate, ticket médio, produto forte, ciclo médio). Preferências de notificação e horário do briefing diário.

---

## Scoring de deals

O score (0–100) é calculado por um engine de regras + heurísticas, **não ML**, com foco em explainability. Fatores:

- **Timing:** dias no pipeline vs. ciclo médio histórico do produto
- **Stage:** Engaging pontua mais que Prospecting
- **Produto:** win rate histórico daquele produto
- **Vendedor:** win rate histórico do vendedor naquele stage/produto
- **Conta:** revenue e setor da empresa
- **Decay:** deals muito além do ciclo médio de perda perdem score progressivamente

Cada score retorna um array `reasons[]` com os fatores em linguagem natural — é isso que alimenta o explainability e o agente.

---

## Dados

O backend parte de 5 CSVs importados para banco relacional:

| Arquivo | Conteúdo |
|---|---|
| `sales_pipeline.csv` | 8.800 deals com stage, datas, produto, conta, valor |
| `sales_teams.csv` | 35 vendedores com manager e região (Central/East/West) |
| `products.csv` | 7 produtos com série e preço (de $55 a $26.768) |
| `accounts.csv` | 85 contas com setor, revenue, employees, localização |
| `metadata.csv` | Descrição dos campos |

**Números relevantes do pipeline:**
- 2.089 deals ativos (1.589 Engaging, 500 Prospecting)
- 71% dos ativos têm mais de 82 dias no pipeline (acima do ciclo médio de perda) — "zombie deals"
- Ciclo médio até fechar (Won): 52 dias
- Ciclo médio até perder (Lost): 41 dias
- Win rate médio: ~63% (varia por vendedor: 55%–70%)
- Receita potencial total em deals ativos: ~$3,36M

O data layer é abstraído no backend — hoje lê dos CSVs importados, no futuro conecta a um CRM (HubSpot, Salesforce, Pipedrive) sem mudar contratos de API.

---

## Arquitetura

```
PWA (SvelteKit)
  └── API REST (Go)
        ├── Auth (JWT por vendedor)
        ├── ReAct Agent Engine
        │     └── Tools: get_my_deals, score_deal, get_deal_detail,
        │                get_at_risk_deals, get_hot_deals,
        │                get_agent_stats, compare_to_avg
        ├── Scoring Engine (regras + heurísticas)
        ├── Scheduler (alertas proativos / cron)
        ├── Memory layer por vendedor
        └── Data Layer (abstrato)
              ├── Hoje: PostgreSQL ← CSVs importados
              └── Futuro: conector CRM
```

**LLM:** Claude (Anthropic) via API — usado pelo ReAct agent para raciocínio e síntese de respostas em linguagem natural.

---

## Design System

Baseado na identidade visual do G4 Business.

**Cores:**
- Background dark: `#0C1923` (navy)
- Accent: `#C4952A` (gold)
- Texto: `#1A2332` / `#4A5568` / `#94A3B8`
- Semânticas: green `#10B981` | amber `#F59E0B` | red `#EF4444`

**Tipografia:**
- Headings: **Outfit** (700/800/900)
- UI/Body: **DM Sans** (400/500/600)

**Padrão visual:**
- Dark mode no header/nav, light mode no conteúdo
- Cards com borda esquerda colorida por status
- Score ring SVG circular (vermelho → âmbar → verde → gold)
- Pills/badges arredondadas para status e filtros
- Bottom navigation fixa (mobile-first)

---

## Contratos de API

```
POST /api/auth/login
GET  /api/me
GET  /api/deals?stage=&filter=
GET  /api/deals/:id
GET  /api/alerts
POST /api/chat                  ← streaming
GET  /api/stats/me
GET  /api/stats/team            ← apenas manager
```

---

*Versão: 1.0 — MVP | Março 2026*
