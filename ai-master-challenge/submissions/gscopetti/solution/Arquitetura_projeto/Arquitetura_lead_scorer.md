# 🎯 Arquitetura — Lead Scorer (Build 003)

> **G4 AI Master Challenge** · Área: Vendas / RevOps · Tipo: Build  
> Documento de arquitetura para distribuição ao **Agente Master** e seus agentes de desenvolvimento.

---

## 1. ENTENDIMENTO DO DESAFIO

### 1.1 O Problema
O time comercial (35 vendedores, 3 regiões) prioriza deals "no feeling". Deals bons esfriam, deals ruins consomem tempo. A Head de RevOps quer uma **ferramenta funcional** (não um notebook) onde o vendedor abra na segunda-feira de manhã e saiba **onde focar**.

### 1.2 O que NÃO é
- Não é um modelo de ML no Jupyter
- Não é mockup/wireframe/PowerPoint
- Não é dashboard que "só mostra dados" sem direcionamento

### 1.3 O que É
- Software que **roda de verdade** com os dados reais
- Scoring com **explicabilidade** (o vendedor entende o POR QUÊ)
- **Ferramenta de decisão**, não só de visualização
- Com filtro por vendedor/manager/região

### 1.4 Dados Disponíveis (análise real dos CSVs)

| Arquivo | Registros | Campos-chave | Observação |
|---------|-----------|--------------|------------|
| `accounts.csv` | 85 | account, sector, revenue, employees, office_location | 10 setores; campo "subsidiary_of" frequentemente vazio |
| `products.csv` | 7 | product, series, sales_price | 3 séries (GTX, MG, GTK); preços de 55 a 26.768 |
| `sales_teams.csv` | 35 | sales_agent, manager, regional_office | 3 regiões (Central, East, West) |
| `sales_pipeline.csv` | 8.800 | opportunity_id, sales_agent, product, account, deal_stage, engage_date, close_date, close_value | **Tabela central**. 4.238 Won, 2.473 Lost, 1.589 Engaging, 500 Prospecting |

### 1.5 Descobertas Críticas dos Dados

**⚠️ ATENÇÃO — estes pontos devem guiar o desenvolvimento:**

1. **Deals ativos sem account**: 68% dos Engaging (1.088/1.589) e 67% dos Prospecting (337/500) **não têm account associado**. O scoring de deals ativos precisa funcionar mesmo sem dados da conta.
2. **Nomes de produto inconsistentes**: no pipeline aparecem "GTXPro" e "GTX Plus Pro", mas na tabela de produtos é "GTX Pro" e "GTX Plus Pro". Precisa normalizar.
3. **Deals Won com close_value**: variam de 49 a ~27.000. Deals Lost têm close_value = 0.
4. **Deals ativos (Engaging/Prospecting)**: não têm close_date nem close_value — são o alvo principal do scoring.
5. **Dados temporais**: deals de ~2016-2017. Tratar como se fossem "atuais" para fins do desafio.

---

## 2. ARQUITETURA DA SOLUÇÃO

### 2.1 Decisão Técnica

**Stack: React (Vite + TypeScript) — Single Page Application client-side**

Justificativa:
- Roda 100% no browser, sem backend — fácil de fazer deploy e demonstrar
- Processamento de CSV client-side com PapaParse
- Scoring computado em tempo real no frontend
- Atende o requisito "precisa rodar" sem dependências externas

| Camada | Tecnologia | Motivo |
|--------|-----------|--------|
| Framework | React 18 + TypeScript + Vite | Performance, tipagem, DX |
| Estilização | Tailwind CSS | Prototipagem rápida, responsivo |
| Componentes UI | Shadcn/UI | Profissional, acessível, consistente |
| Gráficos | Recharts | Integração nativa React, declarativo |
| CSV Parsing | PapaParse | Parser robusto, handles edge cases |
| Estado Global | React Context + useReducer | Simples, sem over-engineering |
| IA Generativa | API Claude (Anthropic) | Scripts SPIN personalizados (com fallback offline) |

### 2.2 Estrutura de Pastas

```
lead-scorer/
├── public/
│   └── sample-data/          # CSVs de exemplo para demo
├── src/
│   ├── components/
│   │   ├── layout/           # Sidebar, Header, MainContent
│   │   ├── upload/           # DropZone, CSVPreview, ValidationStatus
│   │   ├── dashboard/        # KPICards, Charts, PipelineOverview
│   │   ├── leads/            # LeadTable, LeadFilters, LeadSearch
│   │   ├── deal-detail/      # DealScoreCard, ScoreBreakdown, Timeline
│   │   └── spin/             # SPINScript, ScriptSection, ExportButton
│   ├── hooks/
│   │   ├── useDataLoader.ts       # Parse e normalização dos CSVs
│   │   ├── useDealScoring.ts      # Motor de scoring por deal
│   │   ├── useAccountScoring.ts   # Scoring agregado por account
│   │   └── useSPINGenerator.ts    # Geração de scripts SPIN
│   ├── utils/
│   │   ├── scoring.ts             # Funções puras de cálculo de score
│   │   ├── normalizer.ts          # Limpeza e normalização de dados
│   │   ├── formatters.ts          # Formatação de valores, datas, %
│   │   └── spin-templates.ts      # Templates SPIN parametrizados
│   ├── types/
│   │   └── index.ts               # Todas as interfaces TypeScript
│   ├── context/
│   │   └── DataContext.tsx         # Estado global dos dados
│   ├── App.tsx
│   └── main.tsx
├── docs/
│   ├── SETUP.md                   # Como rodar
│   ├── SCORING_LOGIC.md           # Explicação da lógica
│   └── LIMITATIONS.md             # O que não faz
├── package.json
└── README.md
```

### 2.3 Fluxo de Dados

```
[Upload 4 CSVs]
      ↓
[PapaParse → Parsing + Validação]
      ↓
[Normalização → DataContext]
      ↓
[Motor de Scoring]
  ├── Deal Scoring (cada oportunidade ativa)
  └── Account Scoring (agregado por conta)
      ↓
[Classificação em Tiers]
      ↓
[Gerador SPIN Selling]
      ↓
[Dashboard + Tabela + Detalhes]
```

---

## 3. LÓGICA DE SCORING (O CORE DO PROJETO)

### 3.1 Dual Scoring: Deal-Level + Account-Level

O desafio pede para o vendedor saber **onde focar**. Isso tem duas dimensões:

**A) Deal Score (0-100)** — aplicado a cada deal ativo (Engaging/Prospecting)
> "Este deal específico vale a pena eu investir tempo?"

**B) Account Score (0-100)** — aplicado a cada conta
> "Esta conta como um todo tem potencial? Devo buscar novas oportunidades aqui?"

### 3.2 Deal Score — Fórmula

Para cada deal com status Engaging ou Prospecting:

| Fator | Peso | Como calcular | Por quê |
|-------|------|---------------|---------|
| Histórico da conta (win rate) | 20% | Won/(Won+Lost) dos deals passados desta conta. Sem conta = usar média geral. | Contas com histórico de compra convertem mais |
| Valor potencial do produto | 20% | sales_price do produto / max(sales_price). Normalizado 0-1. | Deals de alto valor merecem mais atenção |
| Performance do vendedor | 15% | Win rate pessoal do sales_agent em deals similares (mesmo produto ou série). | Vendedores com track record no produto convertem mais |
| Tempo no pipeline | 15% | Dias desde engage_date. Curva: 0-30d = bom (1.0), 30-90d = ok (0.7), 90-180d = atenção (0.4), >180d = frio (0.2). | Deals parados há muito tempo provavelmente estão mortos |
| Tamanho da conta | 10% | Revenue da account normalizado. Sem conta = 0.5 (neutro). | Contas maiores = deals maiores potenciais |
| Estágio do deal | 10% | Engaging = 0.7, Prospecting = 0.4. | Engaging está mais avançado no funil |
| Cross-sell opportunity | 10% | Conta já comprou outros produtos? Diversidade de séries adquiridas. | Clientes existentes convertem mais em novos produtos |

**Fórmula**: `deal_score = Σ (fator_i × peso_i) × 100`

### 3.3 Account Score — Fórmula

Para cada account (agregado):

| Fator | Peso | Como calcular | Por quê |
|-------|------|---------------|---------|
| Win Rate | 25% | Won/(Won+Lost). Min 3 deals para ser significativo. | Indicador #1 de probabilidade de fechar |
| Ticket Médio | 20% | Média close_value dos Won / max média. | Contas que pagam mais = mais receita por esforço |
| Volume de atividade | 15% | Total de deals (todos os estágios) normalizado por quartil. | Contas engajadas mantêm pipeline ativo |
| Pipeline ativo | 15% | Quantidade de deals Engaging + Prospecting agora. | Oportunidades imediatas de trabalho |
| Recência | 10% | Dias desde o deal mais recente. Mais recente = melhor. | Conta ativa vs conta dormindo |
| Tamanho da empresa | 10% | (revenue_normalizado + employees_normalizado) / 2. | Empresas maiores = mais potencial de expansão |
| Diversidade de produtos | 5% | Quantidade de séries diferentes compradas / total séries. | Penetração do portfólio = cliente consolidado |

### 3.4 Classificação em Tiers

| Tier | Score | Badge | Cor | Ação sugerida |
|------|-------|-------|-----|---------------|
| 🔥 HOT | 80-100 | Hot Lead | Vermelho | Prioridade máxima — agendar contato esta semana |
| 🟡 WARM | 60-79 | Warm Lead | Amarelo | Bom potencial — nurturing ativo, follow-up quinzenal |
| 🔵 COOL | 40-59 | Cool Lead | Azul | Potencial moderado — manter no radar, abordagem consultiva |
| ⚪ COLD | 0-39 | Cold Lead | Cinza | Baixa prioridade — revisar se vale manter no pipeline |

### 3.5 Tratamento de Dados Ausentes

Este é um ponto crítico (68% dos deals Engaging não têm account):

| Dado ausente | Estratégia |
|--------------|-----------|
| Account em deal ativo | Usar médias gerais para fatores de account. Reduzir peso dos fatores dependentes de account em 50%. Aumentar peso de fatores independentes (vendedor, produto, tempo). |
| Revenue/Employees | Atribuir valor neutro (mediana do dataset) |
| subsidiary_of vazio | Ignorar (não impacta scoring) |
| close_date em deal ativo | Esperado — calcular tempo desde engage_date |

---

## 4. FRAMEWORK SPIN SELLING — GERAÇÃO DE SCRIPTS

### 4.1 Estrutura do Script

Para cada lead com score ≥ 40 (Cool+), gerar um mini-relatório com script de abordagem:

```
┌─────────────────────────────────────────┐
│  RELATÓRIO DO LEAD: [Account Name]      │
│  Score: 87/100 (🔥 HOT)                │
├─────────────────────────────────────────┤
│  CONTEXTO RÁPIDO                        │
│  • Setor: Technology | 2.822 funcionários│
│  • Win Rate: 73% (11 Won / 4 Lost)     │
│  • Ticket Médio: $4.230                 │
│  • Produto mais comprado: GTX Plus Pro  │
│  • Deals ativos: 2 (Engaging)           │
├─────────────────────────────────────────┤
│  SCRIPT SPIN SELLING                    │
│                                         │
│  [S] SITUAÇÃO                           │
│  "Como empresa de tecnologia com mais   │
│  de 2.800 funcionários, imagino que     │
│  vocês lidam com [contexto do setor]..."│
│                                         │
│  [P] PROBLEMA                           │
│  "Notei que os últimos deals na série   │
│  MG não avançaram. Que desafios vocês   │
│  encontraram com [produto_perdido]?"    │
│                                         │
│  [I] IMPLICAÇÃO                         │
│  "Com o ticket médio de $4.230, cada    │
│  oportunidade perdida representa um     │
│  impacto significativo. Em 12 meses     │
│  isso pode significar $X em receita..." │
│                                         │
│  [N] NECESSIDADE-PAYOFF                 │
│  "Se conseguíssemos resolver [problema],│
│  qual seria o impacto no time de vocês? │
│  Outros clientes do setor de technology │
│  viram [benefício] com [produto]..."    │
└─────────────────────────────────────────┘
```

### 4.2 Variáveis Dinâmicas para Templates

O gerador SPIN deve usar estas variáveis extraídas dos dados:

```typescript
interface SPINContext {
  // Dados da conta
  accountName: string;
  sector: string;
  employees: number;
  revenue: number;
  location: string;
  
  // Métricas calculadas
  winRate: number;
  avgTicket: number;
  totalDeals: number;
  wonDeals: number;
  lostDeals: number;
  activeDeals: number;
  
  // Análise de padrões
  topProduct: string;           // produto mais vendido para esta conta
  failedProducts: string[];     // produtos dos deals Lost
  missingProducts: string[];    // séries nunca compradas (cross-sell)
  bestAgent: string;            // vendedor com mais Won nesta conta
  avgCycleTime: number;         // dias médios de engage→close
  lostRevenue: number;          // soma de sales_price dos deals Lost
  
  // Deal específico (se aplicável)
  currentProduct: string;
  currentStage: string;
  daysInPipeline: number;
}
```

### 4.3 Implementação: Duas Opções

**Opção A — Templates Parametrizados (funciona offline, obrigatório)**

Criar templates com variáveis que são preenchidas automaticamente:

```typescript
const spinTemplates = {
  situation: {
    withAccount: "Como empresa do setor de {sector} com {employees} funcionários em {location}, vocês provavelmente lidam com desafios de [área específica do setor]. Vi que vocês já utilizam nosso {topProduct} — como tem sido a experiência?",
    withoutAccount: "Vi que você está avaliando nosso {currentProduct}. Empresas que escolhem esta solução geralmente buscam [benefício-chave do produto]. É esse o cenário de vocês?"
  },
  problem: {
    hasLostDeals: "Notei que em oportunidades anteriores com {failedProducts}, o deal não avançou. Que desafios vocês encontraram? Houve alguma questão de [timing/orçamento/fit técnico]?",
    noLostDeals: "Outros clientes do setor de {sector} costumam enfrentar [desafio típico]. Isso também é uma preocupação para vocês?"
  },
  implication: {
    highTicket: "Com investimentos na faixa de ${avgTicket}, cada decisão tem impacto relevante. Se a solução atual não está atendendo, o custo de oportunidade em {avgCycleTime} dias de ciclo pode significar ${lostRevenue} em produtividade.",
    lowTicket: "Embora o investimento unitário seja acessível, a escala de utilização com {employees} funcionários amplifica significativamente o impacto."
  },
  needPayoff: {
    crossSell: "Vocês já tiveram resultados com {topProduct}. Se estendêssemos isso para a série {missingProducts}, qual seria o impacto? Clientes similares viram [resultado específico].",
    upsell: "Considerando o histórico de sucesso com nossos produtos (win rate de {winRate}%), faz sentido explorarmos como {currentProduct} pode complementar?"
  }
};
```

**Opção B — API Claude para linguagem natural (se disponível, bonus)**

```typescript
const prompt = `
Você é um especialista em vendas B2B usando metodologia SPIN Selling.

DADOS DO LEAD:
${JSON.stringify(spinContext)}

Gere um script de abordagem SPIN personalizado com:
1. SITUAÇÃO: Uma pergunta para entender o contexto atual do cliente
2. PROBLEMA: Uma pergunta que revele dores relacionadas aos deals perdidos
3. IMPLICAÇÃO: Quantifique o impacto financeiro usando os dados reais
4. NECESSIDADE-PAYOFF: Direcione para a solução com base nos produtos que tiveram sucesso

Seja natural, use os dados concretos, e mantenha cada seção em 2-3 frases.
Tom: consultivo, não agressivo.
`;
```

---

## 5. INTERFACE DO USUÁRIO — TELAS E COMPONENTES

### 5.1 Navegação Principal

```
┌──────────────────────────────────────────────────────┐
│  🎯 Lead Scorer          [Filtros Globais ▾]         │
├──────────┬───────────────────────────────────────────┤
│          │                                           │
│  📤 Upload│                                          │
│  📊 Painel│         [ Área Principal ]               │
│  🔥 Deals │                                          │
│  🏢 Contas│                                          │
│  👥 Time  │                                          │
│          │                                           │
└──────────┴───────────────────────────────────────────┘
```

### 5.2 Tela: Upload de Dados

**Propósito**: O vendedor (ou admin) carrega os 4 CSVs.

Componentes:
- 4 zonas de drop (uma por CSV), cada uma com ícone e label do arquivo esperado
- Ao dropar: preview das 5 primeiras linhas em mini-tabela
- Validação automática: ✅ colunas corretas / ❌ coluna faltando com mensagem
- Status geral: barra de progresso com os 4 arquivos
- Botão "Processar Dados" (habilitado só quando os 4 CSVs estão válidos)
- Ao processar: spinner → redireciona para Painel

### 5.3 Tela: Painel (Dashboard Overview)

**Propósito**: Visão executiva — o vendedor entende o cenário em 5 segundos.

Componentes:
```
┌─────────────────────────────────────────────────────┐
│  [KPI 1]      [KPI 2]       [KPI 3]      [KPI 4]   │
│  Deals Ativos  Hot Deals     Win Rate    Pipeline $  │
│  2.089         127           63.2%       $2.4M       │
├─────────────────────────┬───────────────────────────┤
│                         │                           │
│  Distribuição por Tier  │   Top 10 Deals por Score  │
│  (Donut Chart)          │   (Barras horizontais)    │
│                         │                           │
├─────────────────────────┴───────────────────────────┤
│                                                     │
│  Deals Won vs Lost por Mês (Line Chart timeline)    │
│                                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Performance por Região (Grouped Bar Chart)          │
│  Central | East | West — Win Rate + Volume           │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Filtros globais** (presentes em todas as telas):
- Por vendedor (dropdown com autocomplete)
- Por manager (dropdown)
- Por região (Central, East, West)
- Por produto/série (multi-select)
- Por tier (Hot, Warm, Cool, Cold)

### 5.4 Tela: Deals Ativos (A mais importante — "segunda-feira de manhã")

**Propósito**: Tabela priorizadas dos deals Engaging + Prospecting.

```
┌─────────────────────────────────────────────────────┐
│  🔍 Buscar deal...    [Filtros ▾]    [Exportar CSV]  │
├─────────────────────────────────────────────────────┤
│ Score│ Tier │ Account     │ Produto       │ Stage    │
│      │      │             │               │ Dias     │
│ Vendedor    │ Valor Pot.  │ Win Rate Conta│ Ação     │
├──────┼──────┼─────────────┼───────────────┤──────────┤
│  92  │ 🔥   │ Acme Corp   │ GTK 500       │ Engaging │
│      │      │             │               │ 45 dias  │
│ Moses Frase │ $26.768     │ 73%           │ [Ver →]  │
├──────┼──────┼─────────────┼───────────────┼──────────┤
│  87  │ 🔥   │ Betasoloin  │ GTX Plus Pro  │ Engaging │
│      │      │             │               │ 23 dias  │
│ Anna Snell. │ $5.482      │ 68%           │ [Ver →]  │
├──────┼──────┼─────────────┼───────────────┤──────────┤
│  41  │ 🔵   │ —           │ MG Special    │ Prospect.│
│      │      │             │               │ 120 dias │
│ Darcel S.   │ $55         │ —             │ [Ver →]  │
└──────┴──────┴─────────────┴───────────────┴──────────┘
```

Funcionalidades:
- Ordenação padrão: por score (descendente)
- Sort por qualquer coluna clicando no header
- Deals sem account mostram "—" e explicação no tooltip
- Badge de tier com cor
- Coluna "Dias" com cor gradiente (verde → amarelo → vermelho)
- Click na linha → abre Painel de Detalhes

### 5.5 Tela: Detalhes do Deal / Lead (Painel Lateral ou Página)

**Propósito**: O vendedor tem TUDO que precisa para agir neste deal.

```
┌─────────────────────────────────────────────────────┐
│  ← Voltar                                           │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ ACME CORPORATION          Score: 92/100 🔥    │  │
│  │ Technology • 2.822 func. • United States      │  │
│  │ Deal: GTK 500 • Engaging • 45 dias            │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ── POR QUE ESTE SCORE? ──────────────────────────  │
│                                                     │
│  Win Rate da Conta  ████████████████░░  73%  (+18)  │
│  Valor do Produto   ████████████████████ 100% (+20) │
│  Perf. Vendedor     ████████████░░░░░░  65%  (+10)  │
│  Tempo no Pipeline  ████████████████░░  70%  (+11)  │
│  Tamanho Empresa    ██████████████░░░░  78%  (+8)   │
│  Estágio do Deal    █████████████░░░░░  70%  (+7)   │
│  Cross-sell Opp.    ████████████████████ 100% (+10) │
│                                         Total: 92   │
│                                                     │
│  ── HISTÓRICO DA CONTA ───────────────────────────  │
│                                                     │
│  ✅ Won  GTX Plus Pro    $5.169   2017-03-10        │
│  ✅ Won  GTX Basic       $588     2017-03-09        │
│  ✅ Won  MG Special      $53      2017-03-10        │
│  ❌ Lost MG Advanced     $0       2017-03-18        │
│  🔄 Engaging GTK 500     ~$26.768 em andamento      │
│                                                     │
│  ── SCRIPT DE ABORDAGEM (SPIN Selling) ───────────  │
│                                                     │
│  📋 SITUAÇÃO                                        │
│  "Como empresa de tecnologia com mais de 2.800      │
│  funcionários nos EUA, vocês já conhecem nosso      │
│  portfólio — GTX Plus Pro tem performado bem.       │
│  Como tem sido a utilização do GTX Plus Pro no      │
│  dia a dia da operação?"                            │
│                                                     │
│  📋 PROBLEMA                                        │
│  "Vi que a solução MG Advanced não avançou na       │
│  última tentativa. O que impediu? Houve alguma      │
│  questão de adequação técnica ou foi mais de        │
│  timing e orçamento?"                               │
│                                                     │
│  📋 IMPLICAÇÃO                                      │
│  "Considerando o porte da Acme e o investimento     │
│  no GTK 500 (~$26.768), a decisão certa aqui       │
│  pode impactar toda a operação. Qual o custo de    │
│  manter a solução atual por mais 6 meses?"         │
│                                                     │
│  📋 NECESSIDADE-PAYOFF                              │
│  "Outros clientes de tecnologia com perfil          │
│  similar viram ROI em 4 meses com o GTK 500.       │
│  Se trouxesse um resultado parecido, como isso     │
│  mudaria a priorização de vocês neste trimestre?"  │
│                                                     │
│  [📄 Exportar Relatório]  [📋 Copiar Script]        │
└─────────────────────────────────────────────────────┘
```

### 5.6 Tela: Contas (Account-Level View)

Mesma estrutura da tabela de deals, mas agregada por account com:
- Account Score
- Total de deals (Won/Lost/Ativos)
- Win Rate
- Revenue total gerada
- Último deal
- Tier

### 5.7 Tela: Time (Performance dos Vendedores)

Tabela com:
- Vendedor, Manager, Região
- Win Rate pessoal
- Total de deals ativos
- Pipeline value
- Ranking (posição entre os 35)

---

## 6. FASES DE DESENVOLVIMENTO — INSTRUÇÕES PARA O AGENTE MASTER

### REGRA DE OURO PARA O MASTER

> Cada fase só inicia quando a anterior estiver **testada e validada**.
> Exceção: Fase 3 e Fase 4 podem rodar **em paralelo** após a Fase 2.

---

### FASE 1 — FUNDAÇÃO E INGESTÃO DE DADOS

**Agente responsável**: Agente de Dados  
**Dependência**: Nenhuma (primeira fase)  
**Duração estimada**: 45-60 minutos  

#### Tarefa 1.1 — Setup do Projeto
```
Ação: Criar projeto React com Vite + TypeScript
Comando: npm create vite@latest lead-scorer -- --template react-ts
Instalar: papaparse, recharts, lucide-react, tailwindcss, @shadcn/ui
Configurar: tailwind.config.ts, tsconfig paths, estrutura de pastas conforme Seção 2.2
Resultado esperado: `npm run dev` roda sem erros, página em branco no browser
```

#### Tarefa 1.2 — Definição de Tipos TypeScript
```
Ação: Criar src/types/index.ts com todas as interfaces

Interfaces obrigatórias:
- Account { account, sector, year_established, revenue, employees, office_location, subsidiary_of }
- Product { product, series, sales_price }
- SalesTeam { sales_agent, manager, regional_office }
- PipelineOpportunity { opportunity_id, sales_agent, product, account, deal_stage, engage_date, close_date, close_value }
- DealScore { opportunity_id, score, tier, factors: ScoreFactor[], recommendation }
- AccountScore { account, score, tier, factors: ScoreFactor[], deals_summary }
- ScoreFactor { name, weight, raw_value, normalized_value, contribution, explanation }
- SPINScript { situation, problem, implication, need_payoff }
- LeadReport { account_score?, deal_score, spin_script, context: SPINContext }

Resultado esperado: Compilação TypeScript sem erros
```

#### Tarefa 1.3 — Parser de CSV e Normalização
```
Ação: Criar src/hooks/useDataLoader.ts e src/utils/normalizer.ts

Funcionalidades:
1. Parse de cada CSV com PapaParse (header: true, dynamicTyping: true, skipEmptyLines: true)
2. Normalização de produtos: mapear variações para nomes canônicos
   - "GTXPro" → "GTX Pro"
   - "GTX Plus Basic" → "GTX Plus Basic" (já correto)
   - Comparação case-insensitive, trim whitespace
3. Limpeza: revenue e employees como number, datas como Date objects
4. Validação: verificar colunas obrigatórias, reportar erros por arquivo
5. Join: enriquecer pipeline com dados de account, product e sales_team

Resultado esperado: Console.log mostra dados parseados corretamente, sem NaN/undefined inesperados
```

#### Tarefa 1.4 — Context API Global
```
Ação: Criar src/context/DataContext.tsx

Estado:
- accounts: Account[]
- products: Product[]
- salesTeams: SalesTeam[]
- pipeline: PipelineOpportunity[]
- isLoaded: boolean
- errors: string[]

Actions:
- LOAD_DATA: recebe os 4 arrays parseados
- RESET_DATA: limpa tudo (para re-upload)

Resultado esperado: Qualquer componente acessa os dados via useContext
```

#### Critério de Aceite Fase 1
- [ ] Projeto roda com `npm run dev`
- [ ] Upload de 4 CSVs funciona via interface (pode ser um botão simples)
- [ ] Dados aparecem corretos no console (verificar manualmente 5 registros)
- [ ] Produtos normalizados (verificar "GTXPro" → "GTX Pro")
- [ ] Deals ativos sem account são mantidos (não descartados)

---

### FASE 2 — MOTOR DE SCORING

**Agente responsável**: Agente de Analytics  
**Dependência**: Fase 1 concluída  
**Duração estimada**: 60-90 minutos  

#### Tarefa 2.1 — Funções de Cálculo
```
Ação: Criar src/utils/scoring.ts com funções PURAS (sem side effects)

Funções obrigatórias:
- calcWinRate(deals: PipelineOpportunity[]): number
- calcAvgTicket(wonDeals: PipelineOpportunity[]): number
- calcDaysInPipeline(engageDate: Date): number
- calcAgentPerformance(agent: string, product: string, allDeals: PipelineOpportunity[]): number
- normalizeValue(value: number, min: number, max: number): number
- calcAccountSize(revenue: number, employees: number, allAccounts: Account[]): number
- calcProductDiversity(accountDeals: PipelineOpportunity[], allProducts: Product[]): number
- calcRecency(deals: PipelineOpportunity[]): number

Cada função deve retornar um valor normalizado entre 0 e 1.

Resultado esperado: Testes manuais com dados conhecidos produzem resultados coerentes
```

#### Tarefa 2.2 — Hook de Deal Scoring
```
Ação: Criar src/hooks/useDealScoring.ts

Input: pipeline (deals Engaging/Prospecting), accounts, products, salesTeams
Output: DealScore[] — array ordenado por score (desc)

Implementar a fórmula da Seção 3.2 deste documento.

CRÍTICO: Cada DealScore deve ter um array de ScoreFactor com:
- name: nome do fator em português
- weight: peso percentual
- raw_value: valor original (ex: "73%")
- normalized_value: valor 0-1
- contribution: pontos contribuídos ao score final
- explanation: frase em português explicando ("Win rate de 73% está acima da média de 63%")

O vendedor PRECISA entender cada fator.

Resultado esperado: Array de ~2.089 DealScores, ordenados, com fatores detalhados
```

#### Tarefa 2.3 — Hook de Account Scoring
```
Ação: Criar src/hooks/useAccountScoring.ts

Input: pipeline (todos os deals), accounts, products
Output: AccountScore[] — array ordenado por score (desc)

Implementar a fórmula da Seção 3.3 deste documento.

Tratar: Contas com menos de 3 deals totais recebem flag "dados insuficientes" mas ainda são classificadas.

Resultado esperado: Array de ~85 AccountScores, ordenados, com fatores detalhados
```

#### Tarefa 2.4 — Classificação em Tiers
```
Ação: Função assignTier(score: number): Tier

Tiers conforme Seção 3.4.
Aplicar tanto a DealScore quanto AccountScore.

Resultado esperado: Distribuição razoável entre tiers (não pode ter 90% Hot ou 90% Cold)
```

#### Critério de Aceite Fase 2
- [ ] Scores calculados para todos os ~2.089 deals ativos
- [ ] Scores calculados para todas as ~85 accounts
- [ ] Distribuição de tiers parece razoável (verificar manualmente top 10 e bottom 10)
- [ ] Cada score tem fatores explicáveis (breakdown funciona)
- [ ] Deals sem account são classificados (com tratamento da Seção 3.5)
- [ ] Console.log mostra: "Deal XYZ: 87/100 (HOT) — Win Rate 73% (+18), Produto GTK 500 (+20)..."

---

### FASE 3 — GERADOR SPIN SELLING

**Agente responsável**: Agente de Conteúdo  
**Dependência**: Fase 2 concluída  
**Pode rodar em paralelo com**: Fase 4 (componentes base)  
**Duração estimada**: 45-60 minutos  

#### Tarefa 3.1 — Análise Contextual
```
Ação: Criar src/utils/spin-context.ts

Função: buildSPINContext(deal, account, pipeline, products) → SPINContext

Calcular todas as variáveis da Seção 4.2:
- topProduct: produto mais comprado pela conta (maior qtd Won)
- failedProducts: produtos dos deals Lost
- missingProducts: séries que a conta nunca comprou
- bestAgent: vendedor com mais Won nesta conta
- avgCycleTime: média de dias entre engage_date e close_date
- lostRevenue: soma do sales_price dos produtos dos deals Lost

Para deals sem account: contexto reduzido (só produto, vendedor, estágio)

Resultado esperado: SPINContext completo e tipado para qualquer deal
```

#### Tarefa 3.2 — Templates Parametrizados (obrigatório)
```
Ação: Criar src/utils/spin-templates.ts

Implementar templates conforme Seção 4.3, Opção A.

Regras:
- Cada seção (S, P, I, N) tem 2+ variantes baseadas em condições
- Variantes para: com/sem account, com/sem deals perdidos, alto/baixo ticket
- Substituição de variáveis com dados reais ({sector}, {employees}, {avgTicket}...)
- Tom consultivo, não agressivo
- Português BR

Resultado esperado: Qualquer deal gera um script SPIN legível e contextual
```

#### Tarefa 3.3 — Integração com API Claude (opcional/bonus)
```
Ação: Criar src/hooks/useSPINGenerator.ts

Se API key disponível:
- Montar prompt conforme Seção 4.3, Opção B
- Chamar API Claude com contexto completo
- Parse da resposta em seções S, P, I, N
- Cache: não regenerar se contexto não mudou

Se API key não disponível:
- Usar templates parametrizados da Tarefa 3.2

Resultado esperado: Scripts SPIN gerados para qualquer deal (online ou offline)
```

#### Critério de Aceite Fase 3
- [ ] Todo deal com score ≥ 40 tem script SPIN gerado
- [ ] Scripts com account têm dados contextuais reais (setor, ticket, produtos)
- [ ] Scripts sem account ainda fazem sentido (contexto reduzido)
- [ ] Leitura humana: o script parece natural, não um template robótico
- [ ] Nenhum placeholder visível ({sector} ou undefined) nos scripts finais

---

### FASE 4 — INTERFACE E DASHBOARD

**Agente responsável**: Agente de Frontend  
**Dependência**: Fase 1 concluída (para estrutura). Fases 2 e 3 para dados completos.  
**Pode iniciar em paralelo com**: Fase 3 (usando dados mockados/parciais)  
**Duração estimada**: 90-120 minutos  

#### Tarefa 4.1 — Layout Base e Navegação
```
Ação: Criar componentes de layout

Componentes:
- src/components/layout/Sidebar.tsx — navegação entre telas
- src/components/layout/Header.tsx — título + filtros globais
- src/components/layout/MainContent.tsx — wrapper da área principal

Navegação: Upload | Painel | Deals | Contas | Time
Filtros globais: região, manager, vendedor, produto/série, tier

Usar: Shadcn/UI para Sidebar, Select, MultiSelect, Badge
Estilo: Dark mode, profissional, cores sóbrias
Responsivo: sidebar colapsável em telas < 1024px

Resultado esperado: Navegação funciona, filtros renderizam (sem dados ainda é ok)
```

#### Tarefa 4.2 — Tela de Upload
```
Ação: Criar componentes de upload conforme Seção 5.2

Componentes:
- src/components/upload/DropZone.tsx — zona de arrasto por arquivo
- src/components/upload/CSVPreview.tsx — mini-tabela com 5 linhas
- src/components/upload/ValidationStatus.tsx — ✅/❌ por campo

Fluxo: Drop → Parse → Preview → Valida → Botão "Processar"
Ao processar: salva no DataContext e redireciona para Painel

Resultado esperado: Usuário carrega 4 CSVs e vê preview + validação
```

#### Tarefa 4.3 — Dashboard Overview
```
Ação: Criar componentes do dashboard conforme Seção 5.3

Componentes:
- src/components/dashboard/KPICards.tsx — 4 cards com métricas-chave
- src/components/dashboard/TierDistribution.tsx — Donut chart (Recharts PieChart)
- src/components/dashboard/TopDeals.tsx — Bar chart horizontal top 10
- src/components/dashboard/TimelineChart.tsx — Line chart Won vs Lost por mês
- src/components/dashboard/RegionPerformance.tsx — Grouped bar chart

KPIs: Deals Ativos, Hot Deals, Win Rate Geral, Pipeline Value ($)
Todos os gráficos devem respeitar os filtros globais.

Resultado esperado: Dashboard renderiza com dados reais, gráficos interativos
```

#### Tarefa 4.4 — Tabela de Deals Ativos
```
Ação: Criar componentes conforme Seção 5.4

Componentes:
- src/components/leads/LeadTable.tsx — tabela principal sortável
- src/components/leads/LeadFilters.tsx — filtros específicos da tabela
- src/components/leads/LeadSearch.tsx — busca por texto
- src/components/leads/TierBadge.tsx — badge colorido do tier

Funcionalidades:
- Sort por qualquer coluna (default: score desc)
- Filtro por tier, produto, vendedor
- Busca por account name
- Paginação ou scroll virtual (se > 100 rows visíveis)
- Click na linha abre detalhes
- Cor do badge "Dias" muda: verde (< 30d), amarelo (30-90d), vermelho (> 90d)

Resultado esperado: Tabela funcional com sort, filtro, busca e click
```

#### Tarefa 4.5 — Painel de Detalhes (A TELA MAIS IMPORTANTE)
```
Ação: Criar componentes conforme Seção 5.5

Componentes:
- src/components/deal-detail/DealHeader.tsx — account, score gauge, tier, info básica
- src/components/deal-detail/ScoreBreakdown.tsx — barras visuais por fator com explicação
- src/components/deal-detail/DealTimeline.tsx — timeline de todos os deals da conta
- src/components/deal-detail/SPINSection.tsx — script SPIN completo formatado
- src/components/deal-detail/ExportButton.tsx — exportar como PDF (window.print) ou copiar texto

CRÍTICO: O ScoreBreakdown é o coração da ferramenta.
Cada fator deve mostrar:
- Nome do fator
- Barra visual proporcional
- Valor real (ex: "73%")
- Contribuição em pontos (ex: "+18")
- Tooltip ou texto explicativo

O SPINSection deve:
- Mostrar cada seção (S, P, I, N) com ícone e cor diferente
- Texto fluido e natural
- Botão "Copiar Script" para clipboard
- Se usando API Claude: botão "Regenerar"

Resultado esperado: Vendedor entende o score E tem script pronto para agir
```

#### Tarefa 4.6 — Telas de Contas e Time
```
Ação: Criar telas secundárias conforme Seções 5.6 e 5.7

Contas: Tabela similar à de deals, mas com AccountScore, métricas agregadas
Time: Tabela de vendedores com win rate, pipeline, ranking

Ambas respeitam filtros globais.

Resultado esperado: Todas as 5 telas da navegação funcionam
```

#### Critério de Aceite Fase 4
- [ ] Todas as 5 telas renderizam com dados reais
- [ ] Filtros globais funcionam em todas as telas
- [ ] Tabela de deals ordena, filtra e busca corretamente
- [ ] Detalhes do deal mostra score breakdown legível
- [ ] Script SPIN aparece formatado e copiável
- [ ] Gráficos do dashboard são interativos (hover mostra valores)
- [ ] Navegação entre telas é fluida (sem recarregar página)
- [ ] Dark mode consistente em toda a aplicação

---

### FASE 5 — INTEGRAÇÃO, POLISH E DOCUMENTAÇÃO

**Agente responsável**: Agente de QA / Integração  
**Dependência**: Fases 3 e 4 concluídas  
**Duração estimada**: 30-45 minutos  

#### Tarefa 5.1 — Integração End-to-End
```
Ação: Testar fluxo completo

Fluxo: Upload → Processamento → Dashboard → Tabela → Detalhes → Script SPIN

Verificar:
1. Upload dos 4 CSVs reais funciona sem erros
2. Scoring gera resultados para todos os deals ativos
3. Dashboard mostra KPIs corretos (verificar matematicamente)
4. Tabela mostra todos os deals, filtros funcionam
5. Detalhes de um deal Hot mostram breakdown coerente
6. Script SPIN de um deal sem account não tem placeholders vazios
7. Filtro por vendedor filtra corretamente em todas as telas
```

#### Tarefa 5.2 — Validação de Sanidade dos Scores
```
Ação: Verificar coerência manual

Testes:
- Deal de GTK 500 (produto mais caro, $26.768) em conta com alto win rate → deve ser HOT
- Deal de MG Special ($55) em conta sem histórico → deve ser COLD ou COOL
- Vendedor com win rate de 80% em produto específico → deve aumentar score
- Deal há 200+ dias em Prospecting → deve ser penalizado
- Distribuição geral: não deve ter > 40% em um único tier
```

#### Tarefa 5.3 — Responsividade
```
Ação: Testar em 3 breakpoints

- Desktop (1440px): layout completo, sidebar fixa
- Tablet (768px): sidebar colapsável, tabela com scroll horizontal
- Mobile (375px): menu hamburger, cards empilhados, tabela simplificada

Ajustar Tailwind classes conforme necessário.
```

#### Tarefa 5.4 — Documentação
```
Ação: Criar 3 documentos

1. docs/SETUP.md
   - Pré-requisitos: Node.js 18+, npm
   - Comandos: npm install → npm run dev → abrir http://localhost:5173
   - Como usar: fazer upload dos 4 CSVs → navegar pelo dashboard
   - Opção de demo com dados pré-carregados (se implementado)

2. docs/SCORING_LOGIC.md
   - Explicação do dual scoring (deal + account)
   - Tabela de fatores e pesos
   - Tratamento de dados ausentes
   - Exemplos de cálculo com dados reais

3. docs/LIMITATIONS.md
   - Scoring baseado em regras, não ML preditivo
   - Dados históricos (2016-2017), não real-time
   - Templates SPIN são genéricos (sem LLM é limitado)
   - Não tem persistência (dados recarregados a cada sessão)
   - Para escalar: backend, banco de dados, integração CRM, ML

3. README.md na raiz
   - Overview do projeto
   - Screenshot ou GIF do dashboard
   - Quick start
   - Links para docs
```

#### Critério de Aceite Fase 5 (Critério Final)
- [ ] Fluxo completo funciona do upload ao script SPIN sem erros
- [ ] Scores fazem sentido (validação manual de 10 deals)
- [ ] Responsivo em 3 breakpoints
- [ ] Documentação permite que outra pessoa rode o projeto
- [ ] Código limpo: sem console.logs, sem TODO, sem dead code
- [ ] `npm run build` gera bundle de produção sem erros

---

## 7. FLUXO DE ORQUESTRAÇÃO DO MASTER

```
                    ┌──────────────┐
                    │ AGENTE MASTER│
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   FASE 1     │
                    │ Agente Dados │
                    │  (45-60min)  │
                    └──────┬───────┘
                           │ ✅ Dados carregados e normalizados
                    ┌──────▼────────┐
                    │    FASE 2     │
                    │Agente Analytics│
                    │  (60-90min)   │
                    └──────┬────────┘
                           │ ✅ Scores calculados
                    ┌──────┴──────┐
              ┌─────▼─────┐ ┌────▼──────┐
              │  FASE 3   │ │  FASE 4   │
              │  Conteúdo │ │ Frontend  │
              │ (45-60min)│ │(90-120min)│
              └─────┬─────┘ └────┬──────┘
                    │            │
                    └──────┬─────┘
                           │ ✅ Scripts + UI prontos
                    ┌──────▼───────┐
                    │    FASE 5    │
                    │  Agente QA   │
                    │  (30-45min)  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  ✅ ENTREGA  │
                    │  App pronto  │
                    └──────────────┘
```

**Tempo total estimado: 4.5-6 horas** (dentro do budget do desafio)

### Regras para o Master

1. **Nunca pular fase**: os dados (Fase 1) são fundação de tudo
2. **Validar antes de avançar**: cada fase tem "Critério de Aceite" — só seguir quando todos os checkboxes estiverem marcados
3. **Paralelizar quando possível**: Fases 3 e 4 podem rodar juntas
4. **Priorizar funcionalidade sobre beleza**: um score que funciona > um dashboard bonito sem lógica
5. **Se estourar o tempo**: cortar Fase 4.6 (telas de Contas e Time) e Tarefa 3.3 (API Claude). O core é: Upload → Scores → Tabela de Deals → Detalhes com SPIN.

### Instruções Específicas por Agente

| Agente | Foco principal | O que NÃO fazer |
|--------|---------------|-----------------|
| **Dados** | Robustez no parsing, normalização de produtos, tipagem forte | Não se preocupar com UI, não criar componentes visuais |
| **Analytics** | Fórmulas corretas, explicabilidade de cada fator, tratamento de missing data | Não otimizar prematuramente, não usar ML complexo |
| **Conteúdo** | Scripts naturais e contextuais, templates que cobrem todos os cenários | Não criar UI, focar só na lógica de geração de texto |
| **Frontend** | UX do vendedor, filtros funcionais, painel de detalhes completo | Não reimplementar scoring, consumir hooks prontos |
| **QA** | Fluxo end-to-end, sanidade dos dados, documentação | Não reescrever código, só ajustar e documentar |

---

## 8. CHECKLIST FINAL DE ENTREGA (ALINHADO AO CHALLENGE)

### Requisitos Obrigatórios do Desafio

- [ ] **Solução funcional**: roda com `npm run dev`, não é mockup
- [ ] **Usa dados reais**: 4 CSVs do dataset carregados e processados
- [ ] **Lógica de scoring**: não é só ordenar por valor — 7 fatores ponderados
- [ ] **Explicabilidade**: vendedor entende POR QUE o score é alto/baixo
- [ ] **Documentação**: SETUP.md + SCORING_LOGIC.md + LIMITATIONS.md
- [ ] **Process log**: evidências de uso de IA no desenvolvimento

### Critérios de Qualidade

- [ ] Funciona de verdade? → Testar fluxo completo
- [ ] Scoring faz sentido? → Validar top 10 e bottom 10 manualmente
- [ ] Vendedor não-técnico consegue usar? → UI limpa, linguagem simples
- [ ] Ajuda a tomar decisão? → Script SPIN = ação concreta
- [ ] Código limpo? → Outro dev consegue dar manutenção

### Bonus Points

- [ ] Filtro por vendedor/manager/região
- [ ] Script de vendas (SPIN Selling) personalizado
- [ ] Exportar relatório
- [ ] Dark mode profissional
- [ ] Responsivo
