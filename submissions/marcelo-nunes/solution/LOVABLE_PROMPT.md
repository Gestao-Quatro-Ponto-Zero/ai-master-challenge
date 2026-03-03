# Prompt Inicial — Lovable

Cole este prompt inteiro no Lovable para criar o projeto.

---

Crie um dashboard executivo de diagnostico de churn para uma empresa SaaS (RavenStack). Este dashboard sera apresentado ao CEO para mostrar as causas do churn, quais segmentos estao em risco, e o que fazer. Design dark theme profissional, tipo painel de controle financeiro.

## Estrutura do App

Single page com sidebar de navegacao (colapsavel em mobile). 7 secoes:

1. **Executive Summary** — KPIs principais em cards + grafico de pizza dos 4 segmentos
2. **Pergunta do CEO** — "Uso cresceu?" (spoiler: nao). 2 graficos de linha mostrando uso flat por 24 meses
3. **Segmentacao** — Tabelas e graficos por industria, pais, canal com badges de significancia estatistica
4. **Revenue Impact** — Top 10 contas perdidas, MRR por tier, billing frequency
5. **Satisfacao Quebrada** — Prova que o instrumento de satisfacao so mede 3-5 (nunca 1-2)
6. **Estrategia & ROI** — 5 estrategias com custo, recuperacao e ROI estimados
7. **Diagnostico Final** — Respostas diretas as 3 perguntas do CEO

## Design

- Dark theme: background #0f1117, cards #1a1a2e, borders #2a2a3e
- Accent colors: red #e94560, green #00d2a0, yellow #ffd700, blue #4da6ff, purple #b366ff, orange #ff8c42
- Font: system-ui/Segoe UI
- Cards com border-left colorido para KPIs
- Badges/tags: tag-red, tag-green, tag-yellow, tag-orange com background 20% opacity
- Use Recharts para graficos (PieChart, BarChart, LineChart, AreaChart)
- Responsivo: sidebar colapsa em mobile, grid adapta
- Header com titulo "RavenStack — Churn Diagnostic" e subtitulo "500 accounts | 600 churn events | 352 affected"

## Dados

Crie um arquivo `src/data/churnData.ts` com todos os dados abaixo como constantes TypeScript exportadas. TODOS os dados ja estao pre-computados, nao precisa de backend.

```typescript
// src/data/churnData.ts

export const SEGMENTS = [
  { name: "Nunca Churnou", value: 113, color: "#00d2a0", description: "Base saudavel" },
  { name: "Porta Giratoria", value: 277, color: "#ffd700", description: "Churnaram mas voltaram" },
  { name: "Perdido Permanente", value: 75, color: "#e94560", description: "Churn REAL" },
  { name: "Flag sem Evento", value: 35, color: "#ff8c42", description: "Dados incompletos" },
];

export const KPIS = {
  total_accounts: 500,
  total_mrr: 10159608,
  lost_mrr: 167000,
  lost_arr: 2004000,
  multi_churn: 175,
  churn_events_total: 600,
  unique_accounts_churned: 352,
  ent_lost_mrr: 122385,
  ent_lost_pct: 73,
};

export const REV_BY_TIER = [
  { tier: "Basic", n: 28, mrr: 12863, mrr_avg: 459 },
  { tier: "Pro", n: 22, mrr: 31752, mrr_avg: 1443 },
  { tier: "Enterprise", n: 25, mrr: 122385, mrr_avg: 4895 },
];

export const TOP10_LOST = [
  { name: "Company_4", industry: "HealthTech", plan: "Enterprise", mrr: 21691 },
  { name: "Company_240", industry: "FinTech", plan: "Enterprise", mrr: 10945 },
  { name: "Company_84", industry: "DevTools", plan: "Enterprise", mrr: 9154 },
  { name: "Company_171", industry: "Cybersecurity", plan: "Enterprise", mrr: 7960 },
  { name: "Company_68", industry: "FinTech", plan: "Enterprise", mrr: 7164 },
  { name: "Company_115", industry: "FinTech", plan: "Enterprise", mrr: 6766 },
  { name: "Company_497", industry: "DevTools", plan: "Enterprise", mrr: 6567 },
  { name: "Company_125", industry: "DevTools", plan: "Enterprise", mrr: 5970 },
  { name: "Company_195", industry: "EdTech", plan: "Enterprise", mrr: 5572 },
  { name: "Company_400", industry: "FinTech", plan: "Enterprise", mrr: 5572 },
];

export const GLOBAL_CHURN_RATE = 15.0;

export const SIGNIFICANCE = {
  by_industry: [
    { name: "Cybersecurity", n: 100, lost: 11, rate: 11.0, ci_lo: 6.3, ci_hi: 18.6, p: 0.2626, sig: "ns" },
    { name: "DevTools", n: 113, lost: 28, rate: 24.8, ci_lo: 17.7, ci_hi: 33.5, p: 0.0036, sig: "sig" },
    { name: "EdTech", n: 79, lost: 10, rate: 12.7, ci_lo: 7.0, ci_hi: 21.8, p: 0.56, sig: "ns" },
    { name: "FinTech", n: 112, lost: 13, rate: 11.6, ci_lo: 6.9, ci_hi: 18.9, p: 0.3146, sig: "ns" },
    { name: "HealthTech", n: 96, lost: 13, rate: 13.5, ci_lo: 8.1, ci_hi: 21.8, p: 0.689, sig: "ns" },
  ],
  by_country: [
    { name: "AU", n: 32, lost: 4, rate: 12.5, ci_lo: 5.0, ci_hi: 28.1, p: null, sig: "small_n" },
    { name: "CA", n: 23, lost: 3, rate: 13.0, ci_lo: 4.5, ci_hi: 32.1, p: null, sig: "small_n" },
    { name: "DE", n: 25, lost: 6, rate: 24.0, ci_lo: 11.5, ci_hi: 43.4, p: null, sig: "small_n" },
    { name: "FR", n: 22, lost: 5, rate: 22.7, ci_lo: 10.1, ci_hi: 43.4, p: null, sig: "small_n" },
    { name: "IN", n: 49, lost: 5, rate: 10.2, ci_lo: 4.4, ci_hi: 21.8, p: 0.3471, sig: "ns" },
    { name: "UK", n: 58, lost: 8, rate: 13.8, ci_lo: 7.2, ci_hi: 24.9, p: 0.7969, sig: "ns" },
    { name: "US", n: 291, lost: 44, rate: 15.1, ci_lo: 11.5, ci_hi: 19.7, p: 0.9542, sig: "ns" },
  ],
  by_referral: [
    { name: "ads", n: 98, lost: 15, rate: 15.3, ci_lo: 9.5, ci_hi: 23.7, p: 0.9324, sig: "ns" },
    { name: "event", n: 96, lost: 21, rate: 21.9, ci_lo: 14.8, ci_hi: 31.1, p: 0.0592, sig: "marginal" },
    { name: "organic", n: 114, lost: 15, rate: 13.2, ci_lo: 8.1, ci_hi: 20.6, p: 0.5818, sig: "ns" },
    { name: "other", n: 103, lost: 15, rate: 14.6, ci_lo: 9.0, ci_hi: 22.6, p: 0.9012, sig: "ns" },
    { name: "partner", n: 89, lost: 9, rate: 10.1, ci_lo: 5.4, ci_hi: 18.1, p: 0.1966, sig: "ns" },
  ],
};

export const BILLING = [
  { freq: "Mensal", n: 221, n_lost: 28, rate: 12.7, mrr_total: 553918, mrr_lost: 94030, mrr_avg_lost: 3358 },
  { freq: "Anual", n: 279, n_lost: 47, rate: 16.8, mrr_total: 664637, mrr_lost: 72970, mrr_avg_lost: 1553 },
];

export const USAGE_BY_MONTH = [
  { month: "Jan/23", total: 10877, accounts: 440 },
  { month: "Fev/23", total: 9492, accounts: 412 },
  { month: "Mar/23", total: 11031, accounts: 431 },
  { month: "Abr/23", total: 10369, accounts: 432 },
  { month: "Mai/23", total: 10757, accounts: 438 },
  { month: "Jun/23", total: 10002, accounts: 420 },
  { month: "Jul/23", total: 11083, accounts: 415 },
  { month: "Ago/23", total: 10335, accounts: 426 },
  { month: "Set/23", total: 9737, accounts: 409 },
  { month: "Out/23", total: 10968, accounts: 426 },
  { month: "Nov/23", total: 9475, accounts: 412 },
  { month: "Dez/23", total: 10435, accounts: 431 },
  { month: "Jan/24", total: 10621, accounts: 426 },
  { month: "Fev/24", total: 10247, accounts: 422 },
  { month: "Mar/24", total: 10725, accounts: 430 },
  { month: "Abr/24", total: 10131, accounts: 428 },
  { month: "Mai/24", total: 10552, accounts: 427 },
  { month: "Jun/24", total: 10106, accounts: 416 },
  { month: "Jul/24", total: 10601, accounts: 431 },
  { month: "Ago/24", total: 10559, accounts: 422 },
  { month: "Set/24", total: 10195, accounts: 415 },
  { month: "Out/24", total: 11450, accounts: 435 },
  { month: "Nov/24", total: 10039, accounts: 410 },
  { month: "Dez/24", total: 10738, accounts: 428 },
];

export const PER_ACCT_AVG = [
  { month: "Jan/23", avg: 24.7 }, { month: "Fev/23", avg: 23.0 },
  { month: "Mar/23", avg: 25.6 }, { month: "Abr/23", avg: 24.0 },
  { month: "Mai/23", avg: 24.6 }, { month: "Jun/23", avg: 23.8 },
  { month: "Jul/23", avg: 26.7 }, { month: "Ago/23", avg: 24.3 },
  { month: "Set/23", avg: 23.8 }, { month: "Out/23", avg: 25.7 },
  { month: "Nov/23", avg: 23.0 }, { month: "Dez/23", avg: 24.2 },
  { month: "Jan/24", avg: 24.9 }, { month: "Fev/24", avg: 24.3 },
  { month: "Mar/24", avg: 24.9 }, { month: "Abr/24", avg: 23.7 },
  { month: "Mai/24", avg: 24.7 }, { month: "Jun/24", avg: 24.3 },
  { month: "Jul/24", avg: 24.6 }, { month: "Ago/24", avg: 25.0 },
  { month: "Set/24", avg: 24.6 }, { month: "Out/24", avg: 26.3 },
  { month: "Nov/24", avg: 24.5 }, { month: "Dez/24", avg: 25.1 },
];

export const CHURN_REASONS = [
  { reason: "features", count: 114 },
  { reason: "support", count: 104 },
  { reason: "budget", count: 104 },
  { reason: "unknown", count: 95 },
  { reason: "competitor", count: 92 },
  { reason: "pricing", count: 91 },
];

export const SATISFACTION = {
  distribution: [
    { score: "3", count: 396 },
    { score: "4", count: 405 },
    { score: "5", count: 374 },
  ],
  null_pct: 41,
  avg_never: 3.94,
  avg_lost: 3.95,
};

export const MULTI_CHURN_DIST = [
  { churns: "0", accounts: 148 },
  { churns: "1", accounts: 177 },
  { churns: "2", accounts: 116 },
  { churns: "3", accounts: 47 },
  { churns: "4", accounts: 10 },
  { churns: "5", accounts: 2 },
];

export const REASON_CHANGES = 204;
export const REASON_SAME = 44;

export const STRATEGIES = [
  { name: "Enterprise Save Program", description: "1 CSM dedicado para 25 Enterprise perdidas", cost_monthly: 8000, recovery_monthly: 56914, recovery_annual: 682968, roi: "7x", priority: "IMEDIATO", color: "#00d2a0" },
  { name: "Desconto Anual 15%", description: "Lock-in para contas mensais >$2k/mes", cost_monthly: 5600, recovery_monthly: 11300, recovery_annual: 67700, roi: "2x", priority: "CURTO PRAZO", color: "#4da6ff" },
  { name: "DevTools PMF Audit", description: "Unico segmento com p<0.01 — investigar product-market fit", cost_monthly: 0, recovery_monthly: 22800, recovery_annual: 274000, roi: "Alto", priority: "CURTO PRAZO", color: "#ffd700" },
  { name: "Programa 90-Day Success", description: "Milestones de valor para 277 contas Porta Giratoria", cost_monthly: 0, recovery_monthly: 80900, recovery_annual: 970800, roi: "Alto", priority: "MEDIO PRAZO", color: "#b366ff" },
  { name: "Qualificar Canal Events", description: "Alterar pitch e onboarding — canal com p=0.059", cost_monthly: 0, recovery_monthly: 0, recovery_annual: 0, roi: "Qualitativo", priority: "MEDIO PRAZO", color: "#ff8c42" },
];

export const HEATMAP = [
  { plan: "Basic", industry: "Cybersecurity", rate: 9.7, n: 31 },
  { plan: "Basic", industry: "DevTools", rate: 19.4, n: 36 },
  { plan: "Basic", industry: "EdTech", rate: 17.9, n: 28 },
  { plan: "Basic", industry: "FinTech", rate: 8.8, n: 34 },
  { plan: "Basic", industry: "HealthTech", rate: 15.4, n: 39 },
  { plan: "Pro", industry: "Cybersecurity", rate: 10.5, n: 38 },
  { plan: "Pro", industry: "DevTools", rate: 23.8, n: 42 },
  { plan: "Pro", industry: "EdTech", rate: 14.8, n: 27 },
  { plan: "Pro", industry: "FinTech", rate: 12.2, n: 41 },
  { plan: "Pro", industry: "HealthTech", rate: 10.0, n: 30 },
  { plan: "Enterprise", industry: "Cybersecurity", rate: 12.9, n: 31 },
  { plan: "Enterprise", industry: "DevTools", rate: 31.4, n: 35 },
  { plan: "Enterprise", industry: "EdTech", rate: 4.2, n: 24 },
  { plan: "Enterprise", industry: "FinTech", rate: 13.5, n: 37 },
  { plan: "Enterprise", industry: "HealthTech", rate: 14.8, n: 27 },
];
```

## Detalhes de cada secao

### 1. Executive Summary
- 4 KPI cards grandes em row: Total Accounts (500), MRR Perdido ($167k/mes), Porta Giratoria (277 = 55%), Enterprise = 73% do MRR perdido
- PieChart com os 4 segmentos (usar as cores definidas)
- Alert box vermelho: "Correcao Critica: O churn NAO e 22%. churn_flag = estado atual. 277 contas churnaram mas VOLTARAM. Churn permanente real: 75 (15%)"
- Alert box amarelo: "55% das contas (277/500) ja cancelaram pelo menos 1x — Fenomeno Porta Giratoria"

### 2. Pergunta do CEO
- Titulo: "Produto diz que uso cresceu. Algo nao bate."
- LineChart: Uso total por mes (24 meses) com linha de referencia horizontal na media (~10.500). Mostrar que e FLAT
- LineChart: Uso medio por conta (24 meses) — tambem flat em ~24.5
- Alert verde: Bullet points do veredicto: "Uso total NAO cresceu", "Uso por conta NAO cresceu", "Base nao esta crescendo — ~20 signups/mes anulados pelo churn", "Satisfacao ok — mas instrumento quebrado (so mede 3-5)"

### 3. Segmentacao
- 3 tabs: Por Industria, Por Pais, Por Canal
- Table com colunas: Segmento | n | Perdidos | Taxa | IC 95% | p-valor | Significancia
- Coluna Significancia com badges coloridos: sig=vermelho "Significativo", marginal=amarelo "Marginal", ns=verde "Nao sig.", small_n=laranja "n insuficiente"
- Linha de referencia mostrando taxa global (15.0%)
- BarChart comparando taxas por segmento com error bars (CI)
- Insight box: "DevTools e o UNICO segmento estatisticamente significativo (p=0.004). Alemanha (n=25) tem amostra insuficiente — qualquer conclusao e invalida."

### 4. Revenue Impact
- 3 KPI cards: MRR Perdido Total ($167k), Enterprise ($122k = 73%), Top 10 ($97k = 58%)
- BarChart: MRR perdido por tier (Basic $12.8k, Pro $31.7k, Enterprise $122.4k) — mostrar concentracao visual
- Table: Top 10 contas perdidas com colunas: # | Conta | Industria | Plano | MRR/mes | ARR equiv.
- Section "Mensal vs Anual": 2 cards comparativos mostrando que mensal perde MENOS contas mas de MAIOR valor ($3.358 avg vs $1.553)
- BarChart groupado: billing frequency x contas perdidas x MRR perdido

### 5. Satisfacao Quebrada
- BarChart: distribuicao de scores (so 3, 4, 5 — visualmente ausencia de 1 e 2)
- Warning icon grande com texto: "Instrumento de Satisfacao Quebrado — Nenhum score 1 ou 2 em 2.000 tickets"
- 3 stat cards: Avg Nunca Churnou (3.94), Avg Perdido (3.95), Sem resposta (41%)
- Alert: "Medias IDENTICAS entre quem fica e quem sai. Score NAO diferencia. CS esta CEGO."

### 6. Estrategia & ROI
- 5 cards de estrategia, cada um com: nome, prioridade (badge), descricao, custo mensal, recuperacao mensal, recuperacao anual, ROI
- BarChart horizontal: impacto anual estimado por estrategia
- Summary card roxo: "Impacto combinado conservador: ~$85k/mes = ~$1M/ano recuperavel = 51% da perda atual"

### 7. Diagnostico Final
- 3 secoes com icones:
  - "1. O que causa o churn?" — Problema ESTRUTURAL Porta Giratoria. 55% ja cancelaram. Motivos declarados sao ruido (distribuicao uniforme, 63% mudam entre churns). Health Score NAO diferencia segmentos.
  - "2. Quais segmentos em risco?" — DevTools (p=0.004 confirmado), Enterprise ($122k/mes), Contas mensais alto valor, Events (marginal p=0.059). Alemanha/Franca/Canada = amostra insuficiente.
  - "3. O que fazer?" — Resumo das 5 estrategias com ROI

- Box final: "Metricas que NAO funcionam": Satisfaction Score (so 3-5), Platform Usage (flat), Health Score (identico), Reason Codes (ruido)
- Box final: "O que FUNCIONA como sinal": Numero de churns anteriores, Segmento DevTools+Enterprise, Canal events, Silencio (41% sem resposta)

## Creditos

No footer: "Diagnostico por Marcelo Nunes | AI Master Challenge G4 | Dados: RavenStack Synthetic Dataset by River @ Rivalytics"
