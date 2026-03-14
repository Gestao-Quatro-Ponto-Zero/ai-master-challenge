# 📊 Product Requirements Document (PRD)
## Lead Scorer - Sistema Inteligente de Qualificação de Leads

**Versão:** 2.0
**Data:** Março 2026
**Status:** ✅ Em Desenvolvimento
**Owner:** Product Management

---

## 📑 Índice

1. [Visão Geral](#visão-geral)
2. [Problema & Oportunidade](#problema--oportunidade)
3. [Solução Proposta](#solução-proposta)
4. [Os 7 Pilares do Score](#os-7-pilares-do-score)
5. [Categorização (Tiers)](#categorização-tiers)
6. [Arquitetura Técnica](#arquitetura-técnica)
7. [Casos de Uso](#casos-de-uso)
8. [Métricas de Sucesso](#métricas-de-sucesso)

---

## 🎯 Visão Geral

### O Quê?
**Lead Scorer** é um **sistema inteligente de priorização de leads** que analisa automaticamente oportunidades de vendas usando machine learning baseado em dados históricos, atribuindo um **score de 0-100** a cada deal.

### Por Quê?
Vendedores gastam tempo analisando leads que não convertem. Lead Scorer **automatiza essa análise**, permitindo que times de vendas:
- ✅ Focam nos leads com maior probabilidade de conversão (HOT)
- ✅ Reduzem ciclo de vendas
- ✅ Aumentam taxa de fechamento (Win Rate)
- ✅ Otimizam alocação de recursos

### Para Quem?
- **Vendedores**: Priorizam leads HOT diariamente
- **Managers**: Monitoram pipeline e performance por tier
- **C-Suite**: Visualizam saúde geral do pipeline

### Resultado?
**Cada lead tem uma "nota"** que diz: *"Você deve dar atenção a este lead AGORA"*

---

## 🔍 Problema & Oportunidade

### O Problema
```
┌─────────────────────────────────────┐
│ SEM Lead Scorer:                    │
│                                     │
│ ❌ Análise manual de 100+ leads     │
│ ❌ Decisões baseadas em "feeling"   │
│ ❌ Vendedor perde 40% do tempo em   │
│    leads que não convertem          │
│ ❌ Sem visão clara de prioridades   │
│ ❌ Pipeline desorganizado           │
└─────────────────────────────────────┘
```

### A Oportunidade
```
┌─────────────────────────────────────┐
│ COM Lead Scorer:                    │
│                                     │
│ ✅ Análise automática em segundos   │
│ ✅ Decisões baseadas em dados       │
│ ✅ Vendedor foca nos TOP 5 HOT      │
│ ✅ Visão clara: score + tier        │
│ ✅ Pipeline organizado por          │
│    probabilidade de conversão       │
└─────────────────────────────────────┘
```

---

## 💡 Solução Proposta

### Fluxo do Usuário

```
1. UPLOAD
   └─ Vendedor carrega arquivo CSV com pipeline

2. ANÁLISE AUTOMÁTICA
   └─ Sistema calcula score para cada deal usando 7 pilares

3. CATEGORIZAÇÃO
   └─ Cada lead é classificado em um tier (HOT/WARM/COOL/COLD)

4. VISUALIZAÇÃO
   ├─ Dashboard mostra TOP 5 HOT em destaque
   ├─ Tabela com todos os deals ordenados por score
   └─ Detalhes de cada lead com SPIN Script pronto para usar

5. AÇÃO
   ├─ Vendedor clica em lead HOT
   ├─ Vê score, razão do score, script SPIN
   └─ Faz follow-up imediato
```

### Interface Principal

```
╔════════════════════════════════════════════════════════════╗
║               LEAD SCORER - DASHBOARD                      ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  🔥 SEUS LEADS HOT                                        ║
║  5 oportunidades quentes esperando sua ação               ║
║                                                            ║
║  ┌──────────────┬──────────────┬──────────────┐           ║
║  │ Tech Corp    │ Digital Inc  │ Cloud Systems│  ...      ║
║  │ Score: 94    │ Score: 89    │ Score: 87   │           ║
║  │ 🔥 HOT       │ 🔥 HOT       │ 🔥 HOT      │           ║
║  └──────────────┴──────────────┴──────────────┘           ║
║                                                            ║
║  MÉTRICAS                                                 ║
║  ┌─────────────┬─────────────┬─────────────┐             ║
║  │ Deals: 24   │ HOT: 5      │ Win Rate: 68% │           ║
║  │ Ativos      │ Prioridade  │ Global      │             ║
║  └─────────────┴─────────────┴─────────────┘             ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

---

## ⚙️ Os 7 Pilares do Score

O **score final** é calculado como uma **soma ponderada** de 7 fatores independentes. Cada fator contribui com um **peso específico** que varia de 10% a 20%.

### **Pilar 1️⃣: Histórico da Conta (20%)**

**O Quê?**
Analisa a **taxa de sucesso histórica** daquela empresa específica.

**Como Funciona?**
- Calcula o **Win Rate** de todos os deals passados dessa conta
- Win Rate = (Deals Won / Total de Deals) × 100
- Resultado é normalizado: 0-100%

**Exemplo:**
```
Empresa: TechCorp
├─ Total de deals: 10
├─ Deals won (fechados): 8
├─ Deals lost: 2
│
└─ Win Rate: 8/10 = 80% ✅
   └─ Score contribuído: 80% × 20% = 16 pontos
```

**Por Quê?**
Contas que já compraram com sucesso = maior probabilidade de comprar novamente

**Intervalo:** 0-20 pontos

---

### **Pilar 2️⃣: Valor do Produto (20%)**

**O Quê?**
Analisa o **valor financeiro** do produto sendo vendido.

**Como Funciona?**
- Pega o **preço do produto** (Ticket Médio)
- Normaliza em relação a **todos os produtos** da linha
- Produtos caros = maior contribuição

**Exemplo:**
```
Produtos disponíveis:
├─ Product A: $5.000 (menor)
├─ Product B: $15.000 (médio)
└─ Product C: $50.000 (maior) ⭐

Normalização (0-100):
├─ Product A: Score 20
├─ Product B: Score 60
└─ Product C: Score 100 → 100 × 20% = 20 pontos
```

**Por Quê?**
Deals de maior ticket são mais altos valor = maior foco

**Intervalo:** 0-20 pontos

---

### **Pilar 3️⃣: Performance do Vendedor (15%)**

**O Quê?**
Avalia a **taxa de fechamento** do vendedor específico para aquele **tipo de produto**.

**Como Funciona?**
- Calcula Win Rate do vendedor = (Deals Won / Total) × 100
- Para aquele tipo de produto em específico
- Não é taxa geral = taxa por produto

**Exemplo:**
```
Vendedor: João Silva
├─ Para Product A: 50% Win Rate
├─ Para Product B: 75% Win Rate ⭐
└─ Para Product C: 40% Win Rate

Se fazendo deal de Product B:
└─ Score: 75% × 15% = 11,25 pontos
```

**Por Quê?**
Alguns vendedores são melhores com certos produtos = maior chance de fechar

**Intervalo:** 0-15 pontos

---

### **Pilar 4️⃣: Tempo no Pipeline (15%)**

**O Quê?**
Analisa **quantos dias** o deal está em movimento.

**Como Funciona?**
```
Cálculo: Dias desde = Data Atual - Data de Engajamento

Scoring por faixa:
├─ 0-30 dias:    Pontuação MÁXIMA (100%) = 15 pontos 🔥
│                Razão: Deal quente, momentum alto
│
├─ 30-90 dias:   Pontuação MÉDIA (50%) = 7,5 pontos
│                Razão: Still active, mas perder urgência
│
├─ 90-180 dias:  Pontuação BAIXA (25%) = 3,75 pontos
│                Razão: Decidindo há muito tempo = problema
│
└─ 180+ dias:    PENALIDADE (0%) = 0 pontos ❌
                 Razão: Deal estagnado, talvez morto
```

**Exemplo:**
```
Deal A: Engajado há 15 dias → 100% → 15 pontos
Deal B: Engajado há 60 dias → 50% → 7,5 pontos
Deal C: Engajado há 200 dias → 0% → 0 pontos (PENALIDADE)
```

**Por Quê?**
Deals recentes têm momentum. Deals velhos = procrastinação ou objeção não resolvida

**Intervalo:** 0-15 pontos

---

### **Pilar 5️⃣: Tamanho da Empresa (10%)**

**O Quê?**
Analisa a **dimensão financeira** da empresa (faturamento + funcionários).

**Como Funciona?**
- Cruza 2 dados: Faturamento anual + Número de funcionários
- Compara com **média** de todas as outras contas
- Maior tamanho = maior capacidade de pagar

**Exemplo:**
```
Média do mercado:
├─ Faturamento: $50M
└─ Funcionários: 500 pessoas

Empresa A: $200M + 2000 pessoas → 4x maior → Score 100 = 10 pontos ⭐
Empresa B: $50M + 500 pessoas → Na média → Score 50 = 5 pontos
Empresa C: $5M + 50 pessoas → 10x menor → Score 0 = 0 pontos
```

**Por Quê?**
Empresas maiores = maior poder de compra + orçamento disponível

**Intervalo:** 0-10 pontos

---

### **Pilar 6️⃣: Estágio do Deal (10%)**

**O Quê?**
Analisa em **qual fase do funil** o deal se encontra.

**Como Funciona?**
```
Estágios possíveis:

1. PROSPECTING (Prospecção)
   └─ Score: 50% = 5 pontos
   └─ Razão: Estágio inicial, sem commitment

2. ENGAGING (Engajamento) ⭐
   └─ Score: 100% = 10 pontos
   └─ Razão: Cliente está discutindo, maior probabilidade

3. (Futuros): Closing, Negotiation, etc.
   └─ Score: 100%+ = até 10 pontos (com bônus)
```

**Exemplo:**
```
Deal A: Prospecting → 5 pontos
Deal B: Engaging → 10 pontos (2x mais)
```

**Por Quê?**
Deals em Engaging estão mais avançados no funil = maior proximidade de fechamento

**Intervalo:** 0-10 pontos

---

### **Pilar 7️⃣: Oportunidade de Cross-sell (10%)**

**O Quê?**
Analisa a **diversidade de produtos** que a empresa já comprou.

**Como Funciona?**
- Conta quantos **tipos diferentes de produtos** ela já adquiriu
- Quanto mais diversa = mais "consolidada"
- Contas consolidadas = maior probabilidade de novos produtos

**Exemplo:**
```
Empresa A:
├─ Comprou Product A ✅
├─ Comprou Product B ✅
├─ Comprou Product C ✅
├─ Comprou Product D ✅
└─ Score: 4 produtos diferentes = 100% = 10 pontos ⭐

Empresa B:
├─ Comprou só Product A ❌
└─ Score: 1 produto apenas = 25% = 2,5 pontos
```

**Por Quê?**
Clientes que compram múltiplos produtos = contas estratégicas com maior LTV

**Intervalo:** 0-10 pontos

---

## 📊 Fórmula de Cálculo

```
SCORE FINAL =
  (Histórico × 0.20) +
  (Produto × 0.20) +
  (Vendedor × 0.15) +
  (Tempo × 0.15) +
  (Tamanho × 0.10) +
  (Estágio × 0.10) +
  (Cross-sell × 0.10)

Resultado: 0-100 pontos
```

### Exemplo Real Completo

```
Deal: "Cloud Solutions para TechCorp"

┌─ Histórico: 80% Win Rate da Conta
│  └─ Score: 80 × 0.20 = 16 pontos
│
├─ Produto: $50.000 (Maior ticket)
│  └─ Score: 100 × 0.20 = 20 pontos
│
├─ Vendedor: 75% Win Rate em Enterprise
│  └─ Score: 75 × 0.15 = 11,25 pontos
│
├─ Tempo: 20 dias no pipeline
│  └─ Score: 100 × 0.15 = 15 pontos
│
├─ Tamanho: $200M + 2000 funcionários
│  └─ Score: 100 × 0.10 = 10 pontos
│
├─ Estágio: ENGAGING
│  └─ Score: 100 × 0.10 = 10 pontos
│
└─ Cross-sell: Compra 3 produto diferentes
   └─ Score: 75 × 0.10 = 7,5 pontos

TOTAL: 16 + 20 + 11,25 + 15 + 10 + 10 + 7,5 = 89,75 ≈ 90 PONTOS
```

---

## 🔥 Categorização (Tiers)

Com base no **score final (0-100)**, cada lead é automaticamente classificado:

### **🔥 HOT (Escaldante)**
```
Score: 80-100
├─ O quê: Lead qualificado, pronto para ação imediata
├─ Probabilidade de conversão: 70%+
├─ Ação: Ligar/Email TODAY
├─ Frequência de follow-up: Diária
└─ Prioridade: MÁXIMA ⭐⭐⭐

Exemplo: "TechCorp - Score 90"
```

### **🟡 WARM (Morno)**
```
Score: 60-79
├─ O quê: Bom potencial, requer nurturing
├─ Probabilidade de conversão: 40-60%
├─ Ação: Enviar conteúdo / Agendar demo
├─ Frequência de follow-up: Semanal
└─ Prioridade: MÉDIA ⭐⭐

Exemplo: "DigitalInc - Score 72"
```

### **🔵 COOL (Frio)**
```
Score: 40-59
├─ O quê: Manter no radar, potencial futuro
├─ Probabilidade de conversão: 20-40%
├─ Ação: Manter contato, resgatar periodicamente
├─ Frequência de follow-up: Mensal
└─ Prioridade: BAIXA ⭐

Exemplo: "MediumCorp - Score 50"
```

### **❄️ COLD (Congelado)**
```
Score: 0-39
├─ O quê: Baixa prioridade, revisar
├─ Probabilidade de conversão: <20%
├─ Ação: Revisar se ainda merece pipeline
├─ Frequência de follow-up: Trimestral
└─ Prioridade: MÍNIMA

Exemplo: "SmallCo - Score 25"
```

### Visualização

```
╔════════════════════════════════════════════╗
║        DISTRIBUIÇÃO POR TIER               ║
╠════════════════════════════════════════════╣
║                                            ║
║  🔥 HOT    (80-100): XXXXXXX  (7 leads)    ║
║             Prioridade máxima              ║
║                                            ║
║  🟡 WARM   (60-79): XXXXXXXXXXX (12 leads) ║
║             Bom potencial                  ║
║                                            ║
║  🔵 COOL   (40-59): XXXXXXXXX (9 leads)    ║
║             Manter no radar                ║
║                                            ║
║  ❄️ COLD   (0-39):  XXXXX (5 leads)        ║
║             Revisar                        ║
║                                            ║
║  TOTAL: 33 leads                           ║
║  Win Rate Esperado: 68%                    ║
║                                            ║
╚════════════════════════════════════════════╝
```

---

## 🏗️ Arquitetura Técnica

### Onde o Score é Calculado?

```
Lead Scorer
│
├─ src/hooks/
│  └─ useDealScoring.ts ⭐ [PONTO DE ENTRADA]
│     └─ Aplica os 7 pilares
│     └─ Retorna DealScore[] com scores e tiers
│
├─ src/utils/
│  └─ scoring.ts [FUNÇÕES MATEMÁTICAS]
│     ├─ calculateHistoricalWinRate()
│     ├─ normalizeProductValue()
│     ├─ calculateVendorPerformance()
│     ├─ calculatePipelineTime()
│     ├─ normalizeBizeSize()
│     ├─ getStageBonus()
│     └─ calculateCrossSellOpportunity()
│
├─ src/types/
│  ├─ index.ts [TIPOS TYPESCRIPT]
│  │  ├─ DealScore (resultado final)
│  │  ├─ ScoreFactor (cada pilar)
│  │  └─ TierType (HOT/WARM/COOL/COLD)
│  │
│  └─ CSV Input:
│     ├─ sales_pipeline.csv
│     ├─ accounts.csv
│     └─ products.csv
│
└─ Aplicação em UI:
   ├─ DashboardPage.tsx [Mostra TOP 5 HOT]
   ├─ DealDetailPage.tsx [Detalhes do score]
   └─ DealsPage.tsx [Tabela com todos]
```

### Fluxo de Dados

```
CSV FILES (Input)
     ↓
     ├─ accounts.csv (empresa, faturamento, funcionários)
     ├─ products.csv (nome, preço)
     └─ sales_pipeline.csv (deals, estágio, datas)
     ↓
useDealScoring Hook
     ↓
     ├─ Calcula 7 pilares para cada deal
     └─ Retorna DealScore[] (score + tier + fatores)
     ↓
Dashboard / Tabela / Detalhes
     ↓
     └─ Exibe scores e tiers em tempo real
```

### Arquivo Crítico: `useDealScoring.ts`

```typescript
// Pseudo-código
export function useDealScoring(
  pipeline: PipelineOpportunity[],
  accounts: Account[],
  products: Product[]
) {
  return pipeline.map(deal => {
    const historicalWinRate = calculateHistoricalWinRate(deal.account, pipeline);
    const productValue = normalizeProductValue(deal.product, products);
    const vendorPerformance = calculateVendorPerformance(deal.sales_agent, deal.product, pipeline);
    const pipelineTime = calculatePipelineTime(deal.engage_date);
    const companySize = normalizeCompanySize(deal.account, accounts);
    const stageBonus = getStageBonus(deal.deal_stage);
    const crossSellScore = calculateCrossSellOpportunity(deal.account, pipeline);

    const score = (
      historicalWinRate * 0.20 +
      productValue * 0.20 +
      vendorPerformance * 0.15 +
      pipelineTime * 0.15 +
      companySize * 0.10 +
      stageBonus * 0.10 +
      crossSellScore * 0.10
    );

    const tier = getTier(score); // HOT | WARM | COOL | COLD

    return DealScore {
      opportunity_id,
      score,
      tier,
      factors: [...], // Cada pilar com seus valores
      recommendation: getRecommendation(tier)
    };
  });
}
```

---

## 💼 Casos de Uso

### **Caso 1: Segunda-feira de Manhã (Vendedor)**

```
Vendedor chega no trabalho...
│
├─ Abre Dashboard do Lead Scorer
│
├─ Vê: "5 leads HOT esperando sua ação"
│
├─ Clica em lead HOT #1 (Score 94)
│
├─ Vê:
│  ├─ Razão do score (7 pilares detalhados)
│  ├─ Script SPIN pronto para usar
│  └─ Histórico da empresa
│
└─ Faz follow-up imediato
   └─ Resultado: +3 deals fechados essa semana ✅
```

### **Caso 2: Reunião com Manager**

```
Manager quer revisar pipeline...
│
├─ Abre Dashboard
│
├─ Vê métricas:
│  ├─ 33 deals no pipeline
│  ├─ 7 HOT (prioridade máxima)
│  ├─ 12 WARM (bom potencial)
│  └─ Win Rate esperado: 68%
│
├─ Identifica problema:
│  └─ "Deal X está 200 dias em pipeline → COLD (penalidade)"
│
└─ Ação: Revisar se ainda vale manter no pipeline
```

### **Caso 3: Análise Estratégica**

```
C-Suite quer entender pipeline...
│
├─ Vê distribuição por tier
│
├─ Constata: "Temos muitos WARM, faltam HOT"
│
└─ Ação: Aumentar qualidade de prospecção
   └─ Resultado: Score médio sobe de 55 para 72
```

---

## 📈 Métricas de Sucesso

### KPIs Esperados

```
├─ Tempo de resposta a HOT leads:
│  └─ Métrica: < 4 horas para primeiro contato
│  └─ Baseline: 24 horas (sem Lead Scorer)
│  └─ Objetivo: 100% em 4 horas
│
├─ Taxa de fechamento por tier:
│  ├─ HOT: 70%+ (vs. 40% média geral)
│  ├─ WARM: 50%+ (vs. 25% média geral)
│  └─ COOL: 20%+ (vs. 10% média geral)
│
├─ Ciclo de vendas:
│  └─ Métrica: Dias de pipeline até fechamento
│  └─ Baseline: 120 dias
│  └─ Objetivo: 80 dias (33% mais rápido)
│
├─ Win Rate global:
│  └─ Métrica: Deals Won / Total Deals
│  └─ Baseline: 55%
│  └─ Objetivo: 70%
│
└─ Produtividade do vendedor:
   └─ Métrica: Deals fechados / semana
   └─ Baseline: 2,5 deals
   └─ Objetivo: 4+ deals
```

### Dashboard de Monitoramento

```
╔════════════════════════════════════════════════════════════╗
║              MÉTRICAS DE SUCESSO - LEAD SCORER             ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  Tempo de Resposta HOT:                                   ║
║  ████░░░░ 2.5h (vs. 4h alvo) ✅                           ║
║                                                            ║
║  Win Rate por Tier:                                       ║
║  🔥 HOT: ███████░ 72% (alvo: 70%+) ✅                     ║
║  🟡 WARM: ████░░░ 52% (alvo: 50%+) ✅                     ║
║  🔵 COOL: ██░░░░░ 18% (alvo: 20%+) ⚠️                     ║
║                                                            ║
║  Ciclo de Vendas Médio:                                   ║
║  █████░░░░ 95 dias (alvo: 80 dias)                        ║
║                                                            ║
║  Win Rate Global:                                         ║
║  ███████░░ 68% (alvo: 70%+) ⚠️                            ║
║                                                            ║
║  Deals / Semana por Vendedor:                             ║
║  ███░░░░░░ 3.2 (alvo: 4+)                                 ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

---

## 🛠️ Implementação Técnica

### Stack de Tecnologia

```
Frontend:
├─ React 18+ (UI)
├─ TypeScript (Type Safety)
├─ Tailwind CSS (Styling)
└─ Recharts (Visualizações)

Backend (Simulado):
├─ Hooks (useDealScoring)
├─ Utils (scoring.ts)
└─ Context (DataContext)

Data:
├─ CSV Upload
├─ In-memory processing
└─ Real-time calculations

Deployment:
└─ Vite + npm
```

### Performance

```
Tempo de cálculo:
├─ 10 deals: < 10ms
├─ 100 deals: < 50ms
├─ 1.000 deals: < 500ms
└─ Sem cache (cada upload = recalcula tudo)
```

---

## 📅 Roadmap Futuro

### V2.1 (Próxima Release)
- [ ] Integração com CRM (Salesforce)
- [ ] Webhooks para atualização automática
- [ ] Histórico de scores (timeline)

### V2.5 (Medium-term)
- [ ] Machine Learning (ajustar pesos dinamicamente)
- [ ] Previsões de fechamento
- [ ] Alertas automáticos (score caindo)

### V3.0 (Visão a Longo Prazo)
- [ ] Integração com email/calendário
- [ ] Mobile app nativa
- [ ] IA generativa para script SPIN dinâmico

---

## ✅ Checklist de Aceitação

- [x] Sistema calcula score usando 7 pilares
- [x] Tiers (HOT/WARM/COOL/COLD) funcionam
- [x] Dashboard mostra TOP 5 leads HOT
- [x] Detalhes mostram breakdown do score
- [x] SPIN Script gerado dinamicamente
- [x] Interface minimalista e profissional
- [x] Documentação clara (este PRD)
- [ ] Testes unitários (próxima sprint)
- [ ] Integração com CRM real (backlog)

---

## 🎯 Conclusão

**Lead Scorer** transforma análise manual de leads em um **processo automatizado e inteligente**, permitindo que times de vendas fochem nos leads com maior probabilidade de conversão.

O sistema é **justo, transparente e baseado em dados reais**, usando 7 pilares que capturão os aspectos mais importantes de uma oportunidade de vendas.

**Resultado esperado:** +30% no Win Rate, -30% no ciclo de vendas, +50% na produtividade do vendedor.

---

**Documento PRD v2.0 - Março 2026**
**Owner: Product Management (Morgan, PM)**
**Status: ✅ Aprovado para desenvolvimento**
