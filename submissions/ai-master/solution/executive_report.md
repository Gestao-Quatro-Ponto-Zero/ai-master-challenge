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

## O Que Fazer: 5 Ações Priorizadas

### 1. CORRIGIR Workflow Builder e Report Generator
**Impacto estimado: ~$134K MRR preservado**
- Sprint dedicado para reduzir error rate de 44% para <5%
- Retirar features beta de produção até estabilizar
- Comunicar aos clientes afetados que os problemas estão sendo resolvidos
- **Prazo**: 2-4 semanas | **Esforço**: Alto | **ROI**: Muito alto

### 2. REDESENHAR Triagem de Suporte por Risco
**Impacto estimado: ~$59K MRR preservado**
- Criar sistema de prioridade baseado em health score (uso declinante + tickets crescentes = prioridade)
- Meta: first response <2hrs para contas em risco (vs 28hrs atual)
- Adicionar alerta automático quando conta acumula >3 tickets em 30 dias
- **Prazo**: 1-2 semanas | **Esforço**: Médio | **ROI**: Alto

### 3. CORRIGIR Medição de Satisfação
**Impacto: Data quality (fundação para decisões futuras)**
- Trocar CSAT reativo por NPS proativo em momentos-chave
- Segmentar relatórios por tier de saúde da conta
- Implementar "exit interview" obrigatória para accounts em downgrade
- **Prazo**: 1 semana | **Esforço**: Baixo | **ROI**: Médio

### 4. REESTRUTURAR Aquisição via Paid Ads
**Impacto estimado: ~$216K MRR protegido**
- Opção A: Melhorar critérios de qualificação (ICP scoring)
- Opção B: Adicionar onboarding obrigatório para leads de Paid Ads
- Opção C: Redirecionar budget para Referral (22% churn) e Direct Sales (28%)
- **Prazo**: 2-4 semanas | **Esforço**: Médio | **ROI**: Alto

### 5. REFORMAR Experiência de Trial
**Impacto: 47 contas trial ativas em risco**
- Guided onboarding com milestones (ex: "configure 3 features nos primeiros 7 dias")
- CS proativo: contato humano no dia 3 e dia 10 do trial
- Métricas de trial-to-paid por canal/indústria para identificar melhor timing
- **Prazo**: 2-3 semanas | **Esforço**: Médio | **ROI**: Médio

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

1. **Semana 1**: Implementar health score e priorização de suporte
2. **Semanas 1-2**: Iniciar sprint de correção de Workflow Builder/Report Generator
3. **Semana 2**: Corrigir sistema de medição de satisfação
4. **Semanas 2-4**: Reestruturar estratégia de Paid Ads
5. **Mês 2**: Avaliar impacto das ações nos leading indicators (uso, erros, tickets)

---

*Análise realizada com dados de 500 contas, cruzando 5 datasets: accounts, subscriptions, feature usage, support tickets e churn events.*
