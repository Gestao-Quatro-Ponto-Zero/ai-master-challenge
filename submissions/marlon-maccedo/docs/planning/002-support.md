# Plan 002 — Support Triage

> Status: pronto para implementar
> Segundo desafio — combina análise operacional + protótipo com IA real

---

## Contexto e decisão de arquitetura

Três deliverables: diagnóstico operacional, proposta de automação, e protótipo funcional. A app cobre os três — cada seção tem sua própria rota. O diferencial técnico é o classificador real usando Claude API (não simulado).

**Datasets:**
- Dataset 1: ~30K tickets com métricas operacionais + texto completo (description + resolution)
- Dataset 2: ~48K tickets de IT classificados em 8 categorias — usado para treinar a intuição do classificador e validar acurácia

DuckDB server-side lê ambos os CSVs. API routes retornam agregados para o diagnóstico. Uma API route separada chama Claude para classificação.

---

## Estrutura de rotas

```
/                   → redirect → /diagnostic
/diagnostic         → dashboard operacional: KPIs, gargalos, estimativa de custo
/triage             → protótipo do classificador: input de ticket → categoria + confiança
/proposal           → proposta de automação: o que automatizar, o que não, novo fluxo
```

---

## API routes

### Diagnóstico operacional

```
GET /api/diagnostic/overview
  → { avgResolutionTime, avgFirstResponse, csatAvg, openTickets, closedTickets }

GET /api/diagnostic/bottlenecks
  → array de { channel, ticketType, priority, avgResolution, count, csatAvg }
  → ordenado por avgResolution DESC — gargalos no topo

GET /api/diagnostic/waste
  → { totalHoursWasted, estimatedCostBRL, worstCombinations[] }
  → "horas desperdiçadas" = tempo acima do SLA esperado × volume de tickets
```

**Query de gargalos (DuckDB sobre Dataset 1):**

```sql
SELECT
  "Ticket Channel"      AS channel,
  "Ticket Type"         AS ticket_type,
  "Ticket Priority"     AS priority,
  COUNT(*)              AS volume,
  AVG(CAST(REPLACE("Time to Resolution", ' hours', '') AS DOUBLE)) AS avg_resolution_hours,
  AVG("Customer Satisfaction Rating") AS avg_csat
FROM read_csv_auto('/data/support_tickets.csv')
WHERE "Ticket Status" = 'Closed'
GROUP BY channel, ticket_type, priority
ORDER BY avg_resolution_hours DESC
```

**Estimativa de custo:**
```
custo = horas_acima_do_sla × volume × custo_hora_agente
custo_hora_agente = R$ 35 (estimativa de agente CLT nível pleno — documentar premissa)
sla_esperado = percentil 25 de resolução por tipo de ticket (o que é "rápido" nos dados)
```

### Classificador

```
POST /api/classify
  body: { text: string }
  → { category, confidence, reasoning, suggestedPriority, shouldAutomate }
```

**Prompt para Claude:**

```
System:
Você é um classificador de tickets de suporte técnico.
Classifique o ticket abaixo em UMA das seguintes categorias:
Hardware | HR Support | Access | Storage | Purchase | Internal Project | Administrative Rights | Miscellaneous

Responda APENAS com JSON no formato:
{
  "category": "<categoria>",
  "confidence": <0.0 a 1.0>,
  "reasoning": "<uma frase explicando a classificação>",
  "suggestedPriority": "Low|Medium|High|Critical",
  "shouldAutomate": <true|false>,
  "automationReasoning": "<por que pode ou não ser automatizado>"
}

User:
<texto do ticket>
```

**Fallback (sem API key):** keyword matching por categoria usando termos frequentes do Dataset 2. Retorna confidence ≤ 0.6 e aviso visual de "modo offline".

**Validação com Dataset 2:** uma rota separada `/api/classify/benchmark` roda 100 tickets aleatórios do Dataset 2 (que já têm categoria) e retorna acurácia. Isso vai no process log como prova de que o classificador funciona.

---

## Lógica: o que automatizar vs. não

Esta é a parte mais importante do challenge — e vai tanto na rota `/proposal` quanto no output do classificador.

**Automatizar:**
| Tipo de ticket | Por quê |
|---------------|---------|
| Classificação e roteamento | Volume alto, critério claro, erro tem baixo custo |
| Respostas para perguntas de status (billing, pedidos) | FAQ estruturado, sem julgamento |
| Triagem de prioridade inicial | Urgência pode ser detectada por palavras-chave + LLM |
| Detecção de duplicatas | Comparação semântica entre tickets abertos |

**NÃO automatizar:**
| Tipo de ticket | Por quê |
|---------------|---------|
| Tickets com carga emocional alta | Frustração/raiva exige empatia humana — IA piora |
| Escalações e reclamações formais | Risco legal/reputacional alto demais |
| Problemas técnicos complexos sem precedente | Sem base de conhecimento, IA alucina |
| Qualquer resposta final ao cliente | Sugerir sim, responder diretamente não |

**Regra de ouro documentada na proposta:** IA sugere, humano decide e assina.

---

## Componentes de UI

### `/diagnostic` — Dashboard operacional

**Header com 4 KPIs:**
- Tempo médio de resolução (horas)
- Nota média de satisfação (CSAT)
- Tickets abertos / fechados
- Custo estimado de ineficiência (R$/mês)

**Gráfico de gargalos** (heatmap ou bar chart):
- Eixo X: canal (Email, Phone, Chat, Social Media)
- Eixo Y: tipo de ticket
- Cor/tamanho: tempo médio de resolução
- Tooltip: volume, CSAT, avg resolution

**Tabela "piores combinações":**
- Canal × Tipo × Prioridade → Tempo médio, Volume, CSAT
- Ordenável, top 10 por padrão
- Badge vermelho para combinações acima de 2× a mediana

**Insight em destaque** (card fixo):
- Texto gerado com base nos dados — ex: "Tickets de Technical Issue via Phone têm resolução 3.2× mais lenta que via Chat, representando 34% do volume total"

### `/triage` — Classificador (protótipo)

- Textarea para colar texto do ticket
- Botão "Classificar"
- Loading state com skeleton
- Resultado:
  - Badge de categoria (colorido por tipo)
  - Barra de confiança (0–100%)
  - Raciocínio em uma frase
  - Indicador "pode ser automatizado?" (sim/não com justificativa)
  - Prioridade sugerida

- Abaixo: exemplos pré-carregados de tickets reais do Dataset 1 (3-4 casos interessantes clicáveis)
- Nota de rodapé: "Acurácia validada em 100 tickets do dataset de IT: XX%"

### `/proposal` — Proposta de automação

Página mais estática, mas data-driven. Estrutura:

1. **Diagnóstico resumido** (3 bullets com os achados-chave do dashboard)
2. **Fluxo proposto** (diagrama visual simples em SVG ou componente React):
   ```
   Ticket entra
     ↓
   IA classifica + prioriza (automático)
     ↓
   É FAQ/status? → Resposta sugerida → Agente aprova → Envia
   É técnico/emocional? → Roteado para especialista com contexto
     ↓
   Resolução → IA sugere texto → Agente edita → Fecha ticket
   ```
3. **Tabela O que automatizar / O que não** (conforme lógica acima)
4. **ROI estimado**: horas economizadas/mês se classificação automática reduzir tempo médio em X%
5. **Limitações honestas**: o que a proposta não resolve, o que precisaria de mais dados

---

## Estrutura de arquivos da app

```
apps/support-triage/
├── data/                          # CSVs aqui (gitignored, Railway Volume)
│   ├── support_tickets.csv        # Dataset 1: ~30K tickets
│   └── it_tickets.csv             # Dataset 2: ~48K tickets classificados
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx               # redirect → /diagnostic
│   │   ├── diagnostic/page.tsx
│   │   ├── triage/page.tsx
│   │   └── proposal/page.tsx
│   ├── api/
│   │   ├── diagnostic/
│   │   │   ├── overview/route.ts
│   │   │   ├── bottlenecks/route.ts
│   │   │   └── waste/route.ts
│   │   └── classify/
│   │       ├── route.ts           # POST: classifica um ticket
│   │       └── benchmark/route.ts # GET: testa acurácia em 100 tickets
│   ├── components/
│   │   ├── BottleneckHeatmap.tsx
│   │   ├── KPICard.tsx
│   │   ├── ClassifierInput.tsx
│   │   ├── ClassificationResult.tsx
│   │   ├── AutomationFlow.tsx     # diagrama SVG do fluxo proposto
│   │   └── WasteTable.tsx
│   └── lib/
│       ├── duckdb.ts              # instância compartilhada DuckDB
│       └── classify.ts            # lógica de chamada Claude + fallback
├── package.json
└── next.config.ts
```

---

## Variáveis de ambiente

```env
ANTHROPIC_API_KEY=sk-...          # Railway env var; sem ela, usa fallback keyword
```

---

## O que vai no process log

- Screenshot da análise inicial dos datasets (exploração com DuckDB, primeiras queries)
- Iteração no prompt do classificador: versão 1 vs. versão final (mostrar o que mudou e por quê)
- Screenshot do benchmark de acurácia rodando
- Screenshot do classificador classificando um ticket real com alta confiança e um com baixa
- A decisão documentada de "não automatizar tickets emocionais" com exemplo do dataset
- Screenshot do dashboard com os gargalos reais dos dados

---

## Dependências

```json
{
  "@duckdb/node-api": "latest",
  "@anthropic-ai/sdk": "latest",
  "recharts": "^2",
  "@tanstack/react-table": "^8",
  "next": "15",
  "tailwindcss": "^4"
}
```
