# Diagnóstico de Churn — RavenStack

**Candidato:** Lucas  
**Data:** Março 2026  
**Challenge:** 001 — Diagnóstico de Churn

---

## Executive Summary

A RavenStack perdeu **$255K MRR** (22% da base) em churn. A análise cruzada das 5 tabelas de dados revela que a causa raiz não é pricing, produto ou suporte isoladamente — é uma **falha sistêmica no go-to-market e onboarding** que impede clientes de descobrir valor.

**Achado principal:** DevTools adquiridos via Partner têm **12.5% de churn**. Via Event/Ads, **40.8%**. Mesma indústria, mesmo produto, 3x mais churn. A diferença é qualificação e onboarding.

**Impacto potencial das ações recomendadas:** ~$1.4M ARR preservado.

---

## Pergunta 1: O que está causando o churn?

### Resposta curta

**Combinação de canal de aquisição inadequado + falha no onboarding de features.**

Clientes adquiridos por canais sem qualificação (Event, Ads) não recebem onboarding adequado, não descobrem as features que geram valor, e churnam citando "support" ou "missing features".

### Evidência (cruzamento das 5 tabelas)

#### Teste 1: Combinação de fatores de risco

| Fatores de Risco | Churn Rate | n |
|------------------|------------|---|
| 0 fatores | 17.6% | 108 |
| 1 fator | 16.8% | 184 |
| 2 fatores | 23.4% | 145 |
| **3+ fatores** | **41.5%** | 53 |

#### Teste 2: DevTools por canal (mesmo segmento, canais diferentes)

| Canal | Churn Rate | Core Feature Adoption |
|-------|------------|----------------------|
| Partner | **12.5%** | 25.0% |
| Organic | 25.0% | 24.5% |
| Ads | 38.5% | 23.8% |
| Event | **43.5%** | 25.0% |

**Insight crítico:** Adoção de core features é IGUAL entre canais (~25%), mas churn é 3.5x maior em Event vs Partner. O problema não é o cliente usar menos — é ele não receber suporte para usar certo.

#### Teste 3: Motivos de churn por canal (DevTools)

| Canal | Principal Motivo | % |
|-------|------------------|---|
| Event | **Support** | 33% |
| Partner | Budget | 22% |

Event tem 33% dos churns por "support" — indica expectativa não atendida, não problema de produto.

#### Teste 4: Adoção de core features prediz churn

| % de uso em core features | Churn Rate |
|---------------------------|------------|
| 0-20% | **33.3%** |
| 20-40% | 19.2% |
| 40-60% | **9.1%** |

**Zero overlap** entre top 10 features usadas por churned vs ativos.

### Mecânica do churn

```
Canal sem qualificação (Event/Ads)
         ↓
Traz cliente de segmento complexo (DevTools)
         ↓
Sem onboarding adequado (Partner faz, Event não)
         ↓
Cliente não descobre core features
         ↓
Não percebe valor → abre tickets → frustração
         ↓
Churn (motivo declarado: "support" ou "features")
```

### Hipóteses testadas

| Hipótese | Status | Evidência |
|----------|--------|-----------|
| DevTools = problema de produto | **REFUTADA** | Via Partner funciona (12.5%) |
| DevTools = problema de GTM | **VALIDADA** | Event/Ads = 40%+ churn |
| Event = expectativa inflada | **PARCIAL** | CSAT pior, mas tickets iguais |
| Upgrade = problema | **REFUTADA** | Upgrade REDUZ churn (20.8% vs 23.8%) |
| Features = driver principal | **VALIDADA** | <20% core = 33% churn vs >40% = 9% |

---

## Pergunta 2: Quais segmentos estão em risco?

### Segmentação por risco

| Faixa | Accounts | MRR | Churn Esperado |
|-------|----------|-----|----------------|
| **CRÍTICO (score 7+)** | 20 | $23,782 | ~45% |
| **ALTO (score 5-6)** | 61 | $97,157 | ~35% |
| MÉDIO (score 3-4) | 136 | $395,662 | ~23% |
| BAIXO (score 0-2) | 173 | $447,002 | ~17% |

**81 contas de alto risco** com **$120,939 MRR** em jogo.

### Critérios do risk score

| Fator | Pontos | Justificativa |
|-------|--------|---------------|
| Indústria = DevTools | +3 | 31% churn vs 22% média |
| Canal = Event ou Ads | +3 | 30%/23% churn vs 15% Partner |
| Core feature adoption < 20% | +2 | 33% churn vs 9% |
| Escalação no suporte | +2 | +20% em churned |
| CSAT < 4.0 | +1 | Indicador de insatisfação |

### Top 20 contas para ação imediata

| Account | Indústria | Plano | MRR | Score | Motivos |
|---------|-----------|-------|-----|-------|---------|
| A-9bfc9f | DevTools | Pro | $2,940 | 11 | DevTools + ads + low_core + escalation + csat |
| A-51ec1b | DevTools | Enterprise | $3,383 | 10 | DevTools + ads + low_core + escalation |
| A-ad296b | DevTools | Pro | $1,862 | 9 | DevTools + event + escalation + csat |
| A-7cfe77 | DevTools | Pro | $1,311 | 9 | DevTools + ads + low_core + csat |
| A-ad64c6 | DevTools | Pro | $5,572 | 8 | DevTools + event + low_core |
| A-22d9d2 | DevTools | Pro | $1,568 | 8 | DevTools + event + escalation |
| A-f6b2fb | DevTools | Basic | $437 | 8 | DevTools + event + escalation |
| A-cb5333 | DevTools | Pro | $1,617 | 7 | DevTools + ads + csat |
| A-58b9ff | DevTools | Enterprise | $1,617 | 7 | DevTools + low_core + escalation |
| A-cb6cc6 | DevTools | Basic | $1,225 | 7 | DevTools + ads + csat |

*Lista completa em `contas_alto_risco.csv`*

### Perfil das contas de alto risco

**Por indústria:**
- DevTools: 47 contas | $74,892 MRR
- FinTech: 12 contas | $17,482 MRR
- Cybersecurity: 11 contas | $15,299 MRR

**Por canal:**
- Event: 30 contas | $44,409 MRR
- Ads: 32 contas | $34,136 MRR

---

## Pergunta 3: O que a empresa deveria fazer?

### Ação 1: Intervenção nas 81 contas de alto risco (AGORA)

**O quê:** CS contactar as 81 contas em 2 semanas. Top 20 em 48h.

**Como:**
- Script de health check proativo (NÃO pitch de upsell)
- Identificar gaps de adoção de features
- Oferecer sessão de onboarding guiado
- Escalar para account manager se necessário

**Impacto:** ~$290K ARR preservado (assumindo 50% de redução no churn esperado)

**Esforço:** BAIXO | **Prazo:** 2 semanas

---

### Ação 2: Mudar GTM de DevTools para Partner (30 dias)

**O quê:** Parar aquisição de DevTools via Event/Ads. Redirecionar para Partners.

**Como:**
- Pausar campanhas de Ads segmentadas para DevTools
- Não priorizar DevTools em eventos
- Criar programa de Partners específico para DevTools
- Definir critérios de qualificação mais rigorosos

**Impacto:** ~$259K ARR preservado (redução de churn de 41% para 12%)

**Esforço:** MÉDIO | **Prazo:** 30 dias

---

### Ação 3: Onboarding de core features (45 dias)

**O quê:** Criar onboarding guiado que leve clientes às features que retêm.

**Como:**
- Core features identificadas: feature_32, feature_12, feature_6, feature_2, feature_31
- Onboarding in-app guiando para essas features
- Alerta para CS quando account tem <20% core adoption após 30 dias
- Email sequence educativo (dias 7, 14, 30)
- Dashboard de "feature health" por account

**Impacto:** ~$775K ARR preservado (se migrar accounts de <20% para >40% core adoption)

**Esforço:** MÉDIO | **Prazo:** 45 dias

---

### Ação 4: SLA diferenciado para Enterprise (60 dias)

**O quê:** Implementar SLA que diferencie Enterprise dos outros planos.

**Como:**
- Resolution time Enterprise: <24h (atual: 37h)
- First response: <30min (atual: 89min)
- Account manager dedicado para contas >$5K MRR
- Prioridade em fila de tickets

**Impacto:** ~$127K ARR preservado

**Esforço:** ALTO | **Prazo:** 60 dias

---

### Resumo: Matriz de Priorização

| Ação | ARR Impacto | Esforço | Prazo | Prioridade |
|------|-------------|---------|-------|------------|
| Intervenção 81 contas | $290K | Baixo | 2 sem | ★★★ |
| GTM DevTools → Partner | $259K | Médio | 30 dias | ★★★ |
| Onboarding core features | $775K | Médio | 45 dias | ★★☆ |
| SLA Enterprise | $127K | Alto | 60 dias | ★☆☆ |
| **TOTAL** | **$1.45M** | | | |

---

## Anexos

### Core features (top 10 de accounts ativos)

1. feature_32
2. feature_12
3. feature_6
4. feature_2
5. feature_31
6. feature_17
7. feature_36
8. feature_24
9. feature_30
10. feature_22

### Metodologia

- **Dados:** 5 tabelas (accounts, subscriptions, feature_usage, support_tickets, churn_events)
- **Período:** 2023-2024
- **Cruzamento:** account_id como chave primária, subscription_id para feature_usage
- **Risk score:** Modelo aditivo baseado em fatores validados empiricamente

### Limitações

- Dados sintéticos (sem validação de negócio real)
- Causalidade inferida, não experimentada
- Impactos estimados com premissas conservadoras

---

*Relatório gerado com auxílio de AI (Claude). Process log disponível em `process_log.md`.*
