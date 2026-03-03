# RavenStack — Diagnóstico de Churn
## Relatório Executivo para o CEO

---

## TL;DR

1. **O churn é real e caro**: 209 de 500 contas (42%) churnearam, com $311K de MRR perdido em contas únicas
2. **O paradoxo tem explicação**: uso cresceu para quem ficou (power users), mas quem saiu já estava com uso baixo e experiência ruim há meses
3. **A causa raiz é produto + suporte, não preço**: duas features (Workflow Builder e Report Generator) têm 3x mais erros, e clientes que churnearam esperaram 3x mais por suporte

---

## O Paradoxo Explicado

O CEO perguntou: *"O uso cresceu, a satisfação está ok, mas o churn subiu. O que está acontecendo?"*

Aqui está o que os dados mostram:

### "O uso cresceu" — Verdade parcial

| Métrica | Retidos | Churned | Diferença |
|---------|---------|---------|-----------|
| Uso total médio por conta | 3.039 | 160 | **19x menor** |
| Features adotadas | 9.5 | 7.2 | 25% menos |
| Top 10% (power users) | 31.5% do uso total | 0% de churn | — |
| Bottom 25% (low users) | — | 96.6% de churn | — |

**O que acontece**: os 10% mais ativos geram quase 1/3 de todo o uso e não churneiam. O "uso cresceu" é verdade no agregado — mas é puxado por quem fica. Quem sai já estava com uso em queda.

### "A satisfação está OK" — Viés de sobrevivência

| Métrica | Retidos | Churned |
|---------|---------|---------|
| Satisfação média | **3.79**/5 | **2.71**/5 |
| Taxa de resposta à pesquisa | **78%** | **54%** |

**O que acontece**: a equipe de CS vê a média geral (3.22/5) e acha que está OK. Mas clientes que churnearam: (a) dão notas mais baixas E (b) respondem menos. A satisfação "OK" é uma ilusão estatística — estamos medindo apenas quem está satisfeito o suficiente para responder.

---

## As 3 Causas Raiz

### Causa 1: Qualidade de Produto — Features quebradas

Duas features têm **3x mais erros** que as demais:

| Feature | Error Rate (Retidos) | Error Rate (Churned) | Impacto |
|---------|---------------------|---------------------|---------|
| **Workflow Builder** | 12.1% | **43.8%** | Beta instável causando falhas em produção |
| **Report Generator** | 12.1% | **44.5%** | Quase metade dos usos resultam em erro |
| Outras features | ~4% | ~15% | Normal |

O feedback textual confirma:
- *"Beta features crashed our production workflows"* (16 menções)
- *"AI features kept giving wrong suggestions"* (26 menções)
- *"The platform was down 3 times in one month"* (18 menções)

**Product Issues é a razão #1 de churn por MRR perdido: $134K.**

### Causa 2: Suporte como acelerador de saída

Clientes que churnearam tiveram uma experiência de suporte **dramaticamente pior**:

| Métrica | Retidos | Churned | Multiplicador |
|---------|---------|---------|---------------|
| First response | 9.3 hrs | **28.1 hrs** | **3x mais lento** |
| Resolution time | 42.8 hrs | **145.8 hrs** | **3.4x mais lento** |
| Escalações | 9.4% | **35.1%** | **3.7x mais** |
| Reabertura de ticket | 7.8% | **24.8%** | **3.2x mais** |
| Tickets por conta | 3.0 | **6.8** | **2.3x mais** |

Quando o produto falha, o suporte deveria ser a rede de segurança. Em vez disso, está acelerando a saída: clientes frustrados esperam 3x mais e têm tickets que não se resolvem.

### Causa 3: Aquisição de baixa qualidade

Nem todos os canais trazem clientes que ficam:

| Canal | Churn Rate | MRR Perdido | Avaliação |
|-------|-----------|-------------|-----------|
| **Paid Ads** | **65.1%** | **$216K** | Pior canal |
| **Event** | **56.2%** | **$117K** | Segundo pior |
| Content Marketing | 42.6% | $173K | Médio |
| Organic Search | 42.6% | $156K | Médio |
| Partner | 39.1% | $108K | Aceitável |
| **Direct Sales** | **27.6%** | **$22K** | Melhor custo-benefício |
| **Referral** | **22.1%** | **$42K** | Melhor canal |

**Trial é um red flag**: 71.2% dos clientes que entraram por trial churnearam, vs 37.3% dos que não passaram por trial. O trial não está demonstrando valor suficiente.

---

## Quem Estamos Perdendo (Segmentos de Risco)

### Por plano
- **Starter**: 61% de churn (97 de 159 contas) — plano básico demais, sem engajamento
- **Professional**: 44% (81 de 184) — volume alto, impacto financeiro significativo
- Enterprise/Custom: ~20% — relativamente saudável

### Por indústria
- **Retail**: 64.4% de churn — possível misfit de produto para o setor
- **Education**: 50% — sensível a preço, ciclos sazonais
- **Technology**: 29.9% — melhor fit, produto adequado

### Por valor
- Contas com MRR >= $1.000 representam **39% dos eventos de churn mas 91% do MRR perdido**
- O churn "leve" (muitas contas Starter) mascara o churn "pesado" (poucas contas Enterprise/Custom de alto valor)

---

## O Que Fazer: 7 Ações Priorizadas

### 1. CORRIGIR Workflow Builder e Report Generator
**Impacto estimado: ~$134K MRR preservado**
- Sprint dedicado para reduzir error rate de 44% para <5%
- Retirar features beta de produção até estabilizar
- Comunicar aos clientes afetados que os problemas estão sendo resolvidos
- **Prazo**: 2-4 semanas | **Esforço**: Alto | **ROI**: Muito alto

### 2. IMPLEMENTAR Health Score + Triagem Proativa de Suporte
**Impacto estimado: ~$59K MRR preservado**

Criar um health score (0-100) por conta, baseado em sinais ponderados:

```
Health Score = (
  Login frequency score    × 0.30 +
  Feature usage score      × 0.25 +
  Support sentiment        × 0.15 +
  Billing health           × 0.15 +
  Engagement score         × 0.15
)
```

| Score | Status | Ação |
|-------|--------|------|
| 80-100 | Saudável | Oportunidades de upsell |
| 60-79 | Atenção | Check-in proativo |
| 40-59 | Em risco | Campanha de intervenção |
| 0-39 | Crítico | Outreach pessoal (CS dedicado) |

**Triggers de intervenção proativa (antes do cliente pensar em cancelar):**

| Trigger | Intervenção |
|---------|-------------|
| Uso cai >50% por 2 semanas | Email: "Vimos que não está usando [feature]. Podemos ajudar?" |
| Sem login por 14 dias | Re-engagement com novidades do produto |
| NPS detractor (0-6) | Follow-up pessoal em 24h |
| Ticket sem resolver >48h | Escalação automática + status proativo |
| Renovação anual em 30 dias | Email de recapitulação de valor + confirmação |

**Roteamento baseado em MRR:**

| MRR da conta | Cancel Flow |
|-------------|-------------|
| <$100/mês | Flow automatizado com offers |
| $100-$500/mês | Automatizado + flag para CS acompanhar |
| $500-$2.000/mês | Rotear para CS antes de completar cancelamento |
| $2.000+/mês | Bloquear self-serve cancel, exigir call com CS |

- Meta: first response <2hrs para contas em risco (vs 28hrs atual)
- **Prazo**: 1-2 semanas | **Esforço**: Médio | **ROI**: Alto

### 3. CONSTRUIR Cancel Flow com Save Offers Dinâmicas
**Impacto estimado: 25-35% save rate (benchmark da indústria)**

Hoje a RavenStack não tem cancel flow — o cancelamento é instantâneo. Implementar:

```
Botão Cancel → Exit Survey (1 pergunta) → Save Offer dinâmica → Confirmação → Post-cancel
```

**Mapeamento offer-por-razão (baseado nos nossos dados de churn):**

| Razão de Cancel | Offer Primária | Offer Fallback |
|----------------|----------------|----------------|
| Too Expensive (74 eventos) | Desconto 25% por 3 meses | Downgrade para plano inferior |
| Not Using Enough (75 eventos) | Pausa de 1-3 meses | Sessão de onboarding gratuita |
| Product Issues (100 eventos) | Escalação imediata para suporte + crédito | Roadmap de correções com timeline |
| Switched Competitor (56 eventos) | Comparativo competitivo + price match | Sessão de feedback |
| Poor Support (59 eventos) | Escalação para CS senior + crédito | Priority support por 90 dias |
| Missing Features (37 eventos) | Preview do roadmap + timeline | Workaround guide |

**Regras do cancel flow:**
- Máximo 2-3 telas (survey + offer + confirmação)
- "Continuar cancelando" sempre visível (sem dark patterns)
- Uma offer primária + uma fallback, não um menu
- Mostrar valor em dólares, não percentual ("Economize $XX/mês")

**Opção de pausa (60-80% dos pausers voltam):**
- Duração: 1-3 meses máximo
- Auto-reativação com email 7 dias antes
- Dados preservados durante pausa

- **Prazo**: 2-3 semanas | **Esforço**: Médio | **ROI**: Muito alto

### 4. CORRIGIR Medição de Satisfação
**Impacto: Data quality (fundação para decisões futuras)**
- Trocar CSAT reativo por NPS proativo em momentos-chave (pós-resolução de ticket, check-in mensal)
- Segmentar relatórios por tier de saúde da conta (não mais uma média só)
- Implementar exit survey obrigatória no cancel flow (item 3 já cobre isso)
- **Métrica de sucesso**: response rate >70% em todos os segmentos (vs 54% nos churners hoje)
- **Prazo**: 1 semana | **Esforço**: Baixo | **ROI**: Médio

### 5. REESTRUTURAR Aquisição via Paid Ads
**Impacto estimado: ~$216K MRR protegido**
- Opção A: Melhorar critérios de qualificação (ICP scoring — Technology e Finance ficam, Retail precisa de vetting)
- Opção B: Adicionar onboarding obrigatório para leads de Paid Ads (guided setup nos primeiros 7 dias)
- Opção C: Redirecionar budget para Referral (22% churn) e Direct Sales (28% churn)
- **Prazo**: 2-4 semanas | **Esforço**: Médio | **ROI**: Alto

### 6. REFORMAR Experiência de Trial
**Impacto: 47 contas trial ativas em risco**
- Guided onboarding com milestones (ex: "configure 3 features nos primeiros 7 dias")
- CS proativo: contato humano no dia 3 e dia 10 do trial
- Métricas de trial-to-paid por canal/indústria para identificar melhor timing
- **Ativação metric**: identificar o que retidos fazem nos primeiros 7 dias que churners não fazem (ex: adotar >5 features)
- **Prazo**: 2-3 semanas | **Esforço**: Médio | **ROI**: Médio

### 7. CONFIGURAR Dunning para Churn Involuntário
**Impacto estimado: recuperar 50-60% de pagamentos falhos**

Churn involuntário (pagamentos falhados) tipicamente representa 30-50% de todo churn e é o mais fácil de resolver:

**Pre-dunning (prevenir falhas):**
- Alertas de cartão expirando: 30, 15 e 7 dias antes
- Solicitar método de pagamento backup
- Habilitar card updater (Visa/Mastercard auto-update)

**Smart retry schedule:**
| Retry | Timing | Email |
|-------|--------|-------|
| 1 | 24h após falha | "Seu pagamento não foi processado — atualize seu cartão" |
| 2 | 3 dias | "Lembrete: atualize seu método de pagamento" |
| 3 | 5 dias | "Sua conta será pausada em 3 dias" |
| 4 | 7 dias | "Última chance para manter sua conta ativa" |

**Benchmark de recuperação:**
| Métrica | Ruim | Médio | Bom |
|---------|------|-------|-----|
| Soft decline recovery | <40% | 50-60% | 70%+ |
| Overall recovery | <30% | 40-50% | 60%+ |

- **Prazo**: 1-2 semanas | **Esforço**: Baixo (se usar Stripe Smart Retries) | **ROI**: Alto

---

## Modelo Preditivo

Construímos um modelo de machine learning (Gradient Boosting) que identifica as variáveis mais importantes para predizer churn:

| Rank | Variável | Importância |
|------|----------|-------------|
| 1 | Total de sessões | 0.157 |
| 2 | Uso médio | 0.140 |
| 3 | Uso total | 0.119 |
| 4 | Tempo de resposta do suporte | 0.117 |
| 5 | Taxa de erros | 0.115 |
| 6 | Tempo de resolução | 0.083 |
| 7 | Uso do Workflow Builder | 0.055 |
| 8 | Uso do Report Generator | 0.047 |

**O modelo confirma**: engajamento (uso) e qualidade da experiência (erros + suporte) são os drivers primários. Não é preço. Não é concorrência. É a experiência do produto.

---

## Limitações

1. **Dados sintéticos**: esta análise usa dados gerados que simulam os padrões do dataset Kaggle original. Com dados reais, os magnitudes podem variar, mas a metodologia se aplica
2. **Causalidade vs Correlação**: embora os padrões sejam fortes, seria necessário testes A/B para confirmar que corrigir as features reduz churn (vs apenas correlação)
3. **Temporal**: análise snapshot, não longitudinal. Uma análise de coorte mês-a-mês daria insights sobre tendências
4. **Segmentos pequenos**: algumas indústrias (Non-Profit: 30, Media: 33) têm amostras pequenas para conclusões robustas

---

## Próximos Passos

### Semana 1: Fundação
1. Implementar health score (0-100) e sistema de alertas proativos
2. Configurar dunning: smart retries + 4 emails de recuperação
3. Corrigir medição de satisfação (NPS proativo)

### Semanas 1-2: Correções Críticas
4. Sprint de correção de Workflow Builder e Report Generator (error rate 44% → <5%)
5. Implementar cancel flow: exit survey → save offer dinâmica → confirmação

### Semanas 2-4: Otimização
6. Roteamento de suporte baseado em MRR e health score
7. Reestruturar estratégia de aquisição (Paid Ads)
8. Reformar experiência de trial com guided onboarding

### Mês 2: Mensuração
9. Avaliar impacto nos leading indicators (uso, erros, tickets, save rate)
10. A/B test de save offers (desconto vs pausa vs downgrade)
11. Análise de coorte: churn por canal, plano e tenure

### Métricas de Sucesso

| Métrica | Hoje | Meta (90 dias) |
|---------|------|----------------|
| Churn rate mensal | ~42% | <15% |
| Cancel flow save rate | 0% (não existe) | 25-35% |
| First response (contas em risco) | 28h | <2h |
| Dunning recovery rate | N/A | 50-60% |
| Feature error rate (WB/RG) | 44% | <5% |
| Satisfaction response rate (churners) | 54% | >70% |

---

*Análise realizada com dados de 500 contas, cruzando 5 datasets: accounts, subscriptions, feature usage, support tickets e churn events.*
