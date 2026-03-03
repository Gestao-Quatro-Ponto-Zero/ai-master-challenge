# RavenStack — Diagnóstico de Churn
## Relatório Executivo para o CEO

**Data:** Março 2026
**Análise:** Cruzamento de 5 datasets — 500 contas, 4.627 assinaturas, 17.887 registros de uso, 2.284 tickets de suporte, 554 eventos de churn

---

## TL;DR — Resumo em 30 Segundos

| Pergunta do CEO | Resposta |
|-----------------|----------|
| *"O churn subiu?"* | Sim. 209 de 500 contas (42%) churnearam. $833K de MRR total em risco. |
| *"Mas o uso cresceu..."* | Cresceu para quem ficou. Quem saiu já tinha 19x menos uso. A média agregada mascara uma base que está se bifurcando. |
| *"E a satisfação está OK..."* | Não está. Churners dão nota 2.71/5 (vs 3.79 dos retidos) e 46% deles nem respondem à pesquisa. O CS está medindo os satisfeitos. |
| *"O que está causando?"* | Duas features quebradas (44% de erros) + suporte 3x mais lento para contas em risco + aquisição de baixa qualidade via Paid Ads. |
| *"Quanto custa?"* | $134K de MRR perdido só por Product Issues. $216K em risco por Paid Ads. Total perdido em contas únicas: $311K. |

---

## 1. O Paradoxo Explicado

O CEO perguntou: *"Uso cresceu, satisfação está ok, mas o churn subiu. O que está acontecendo?"*

As três afirmações estão tecnicamente corretas — mas cada uma esconde metade da história.

### 1.1 "O Uso Cresceu" — Verdade Parcial

| Métrica | Clientes Retidos | Clientes que Saíram | Diferença |
|---------|:----------------:|:-------------------:|:---------:|
| Uso total médio por conta | **3.039** | **160** | 19x menor |
| Features adotadas | 9.5 | 7.2 | 25% menos |
| Erro rate | 5.6% | **20.5%** | 3.7x maior |

**O que está acontecendo:** Os 10% mais ativos (power users) geram 31.5% de todo o uso da plataforma e têm **0% de churn**. Enquanto isso, os 25% menos ativos têm **96.6% de churn**.

O uso cresceu no agregado porque os power users estão usando cada vez mais. Mas quem saiu já estava desengajado. O CEO vê o total; o que importa é a distribuição.

**Analogia para o CEO:** Imagine um restaurante onde 10 clientes fiéis comem 3 pratos cada. A cozinha diz: "servimos mais pratos que nunca!" Mas 50 clientes provaram a entrada, não gostaram, e nunca mais voltaram. O volume subiu. A retenção caiu.

### 1.2 "A Satisfação Está OK" — Viés de Sobrevivência

| Métrica | Retidos | Churned |
|---------|:-------:|:-------:|
| Nota de satisfação média | **3.79**/5 | **2.71**/5 |
| Taxa de resposta à pesquisa | **78.1%** | **54.3%** |
| Gap na nota | +1.08 ponto a favor dos retidos |
| Gap na resposta | 24 pontos percentuais a mais nos retidos |

**O que está acontecendo:** O CS reporta satisfação de 3.22/5 e diz "está OK". Mas essa média é distorcida por dois fatores:

1. **Quem responde?** 78% dos retidos respondem vs apenas 54% dos churners. Os mais insatisfeitos simplesmente não aparecem nos dados.
2. **Quando respondem, dizem o quê?** Churners dão nota 1.08 ponto mais baixa.

**O CS está medindo a satisfação dos clientes satisfeitos.** É como medir a temperatura de um hospital perguntando só aos médicos.

---

## 2. As 4 Causas Raiz (Cruzamento de 5 Tabelas)

### Causa #1: Duas Features Estão Quebrando a Confiança

**Cruzamento:** `feature_usage` × `churn_events` × `support_tickets`

| Feature | Error Rate (Retidos) | Error Rate (Churned) | Multiplicador |
|---------|:-------------------:|:--------------------:|:-------------:|
| **Workflow Builder** | 12.1% | **43.8%** | 3.6x |
| **Report Generator** | 12.1% | **44.5%** | 3.7x |
| Todas as outras | ~4% | ~15% | ~3.5x |

Para clientes que saíram, **quase metade dos usos** de Workflow Builder e Report Generator resulta em erro. O feedback textual dos eventos de churn confirma:

| Feedback | Menções |
|----------|:-------:|
| *"AI features kept giving wrong suggestions"* | 26 |
| *"The platform was down 3 times in one month"* | 18 |
| *"Beta features crashed our production workflows"* | 16 |

**Product Issues é a razão #1 de churn por MRR perdido: $134K.**

### Causa #2: Suporte que Acelera a Saída (em vez de prevenir)

**Cruzamento:** `support_tickets` × `accounts` × `churn_events`

| Métrica de Suporte | Retidos | Churned | Multiplicador |
|:------------------:|:-------:|:-------:|:-------------:|
| First response time | 9.3h | **28.1h** | **3.0x** |
| Resolution time | 42.8h | **145.8h** | **3.4x** |
| Taxa de escalação | 9.4% | **35.1%** | **3.7x** |
| Taxa de reabertura | 7.8% | **24.8%** | **3.2x** |
| Tickets por conta | 3.0 | **6.8** | **2.3x** |

Clientes que saíram tinham mais problemas (6.8 tickets vs 3.0), mais graves (33.8% técnicos vs 23.9%), e receberam atendimento dramaticamente pior.

**A cadeia causal:** Feature quebra → Cliente abre ticket → Espera 28h por resposta → Ticket não resolve (24.8% reaberto) → Abre outro ticket → Desiste.

O suporte deveria ser a rede de segurança quando o produto falha. Em vez disso, está acelerando a saída.

### Causa #3: Aquisição de Baixa Qualidade

**Cruzamento:** `accounts` × `churn_events` × `subscriptions`

| Canal de Aquisição | Churn Rate | MRR Perdido | Avaliação |
|:------------------:|:---------:|:-----------:|:---------:|
| **Paid Ads** | **65.1%** | **$216K** | Pior canal |
| **Event** | **56.2%** | **$117K** | Segundo pior |
| Content Marketing | 42.6% | $173K | Mediano |
| Organic Search | 42.6% | $156K | Mediano |
| Partner | 39.1% | $108K | Aceitável |
| **Direct Sales** | **27.6%** | **$22K** | Bom |
| **Referral** | **22.1%** | **$42K** | Melhor canal |

Paid Ads traz 2 em cada 3 clientes que vão sair. Referral retém 3x melhor.

**Trial é um red flag adicional:** 71.2% dos trial accounts churnearam vs 37.3% dos não-trial. O trial não está demonstrando valor suficiente para converter.

### Causa #4: Segmentos Estruturais de Risco

**Cruzamento:** `accounts` × `subscriptions` × `churn_events`

**Por plano:**
| Plano | Churn Rate | Contas | Impacto |
|:-----:|:---------:|:------:|:-------:|
| **Starter** | **61.0%** | 97/159 | Plano básico demais |
| **Professional** | **44.0%** | 81/184 | Maior volume $$ perdido |
| Enterprise | 19.4% | 20/103 | Saudável |
| Custom | 20.4% | 11/54 | Saudável |

**Por indústria:**
| Indústria | Churn Rate | MRR Perdido |
|:---------:|:---------:|:-----------:|
| **Retail** | **64.4%** | $140K |
| **Education** | **50.0%** | $85K |
| Healthcare | 44.8% | **$191K** (maior!) |
| Technology | 29.9% | $79K |
| Finance | 36.4% | $63K |

**Por billing:**
| Frequência | Churn Rate |
|:----------:|:---------:|
| Monthly | **47.3%** |
| Annual | 38.1% |

**Churn pesado vs leve:** Contas com MRR >= $1.000 representam apenas **39.2% dos eventos** de churn mas **91.2% do MRR perdido** ($760K). Perder 10 contas Starter de $50 = $500/mês. Perder 1 conta Enterprise de $5.000 = $5.000/mês.

---

## 3. A Cadeia Causal Completa

```
Features quebradas (Workflow Builder / Report Generator com 44% de erros)
    ↓
Tickets de suporte técnico crescem (churners: 6.8 tickets/conta)
    ↓
Suporte lento (28h vs 9h) + tickets sem resolução (25% reabertos)
    ↓
Satisfação real cai (2.71/5), mas CS não vê (54% response rate)
    ↓
Cliente desiste silenciosamente
    ↓
CEO vê churn subir sem entender por quê
(porque o agregado de uso e satisfação mascara tudo)
```

---

## 4. Modelo Preditivo — Validação por Machine Learning

Treinamos um modelo de Gradient Boosting / Random Forest para confirmar matematicamente quais fatores mais predizem o churn:

| Rank | Variável | Importância | Interpretação |
|:----:|----------|:-----------:|---------------|
| 1 | Total de sessões | 0.157 | Engajamento é o principal protetor |
| 2 | Uso médio | 0.140 | Quanto mais usa, menos churn |
| 3 | Uso total | 0.119 | Volume confirma engajamento |
| 4 | Tempo de resposta do suporte | 0.117 | Suporte lento = churn |
| 5 | Taxa de erros | 0.115 | Features quebradas = churn |
| 6 | Tempo de resolução | 0.083 | Tickets sem resolver = churn |
| 7 | Uso do Workflow Builder | 0.055 | Feature-chave problemática |
| 8 | Uso do Report Generator | 0.047 | Feature-chave problemática |

**O modelo confirma:** os drivers de churn são **engajamento** (uso) e **qualidade da experiência** (erros + suporte). Não é preço. Não é concorrência. É a experiência do produto.

---

## 5. Quem Estamos Perdendo — Contas Específicas em Risco

### Perfil de risco combinado (maior probabilidade de churn)

Uma conta tem risco máximo quando combina:
- Plano **Starter ou Professional**
- Veio por **Paid Ads ou Event**
- Indústria **Retail ou Education**
- Billing **Monthly**
- Trial convertido
- Uso declinante + erros em Workflow Builder / Report Generator
- 3+ tickets nos últimos 30 dias
- Satisfação < 3/5 (ou sem resposta)

### Distribuição de risco no portfólio

| Tier de Risco | Contas | % do Total | Ação Necessária |
|:-------------:|:------:|:----------:|:---------------:|
| Crítico (>80%) | ~50 | 10% | Outreach pessoal imediato |
| Alto (60-80%) | ~80 | 16% | Campanha de intervenção |
| Médio (40-60%) | ~100 | 20% | Check-in proativo |
| Baixo (<40%) | ~270 | 54% | Monitoramento + upsell |

**Os risk scores individuais por conta estão disponíveis no arquivo `account_risk_scores.csv` para que o CS possa agir conta a conta.**

### Mapa de Calor — Top 50 Contas de Maior Risco

O mapa abaixo cruza **25 contas ativas em maior risco** ($36.9K MRR) com **25 contas já perdidas de maior valor** ($114.2K MRR) como padrão de referência. Seis fatores de risco são apresentados — quanto mais alto o valor, mais urgente a intervenção.

> **Como ler:** Contas marcadas "CHURNED" já saíram e mostram o padrão. Contas marcadas "**ATIVA**" são as que o CS deve priorizar **agora**. Foco em: taxa de erros alta, tempo de resposta alto, e uso total baixo.

| # | Empresa | Indústria | Plano | Status | MRR | Prob. Churn | Erros | Resp. Suporte | Uso Total |
|:-:|---------|-----------|-------|:------:|----:|:----------:|:-----:|:-------------:|----------:|
| 1 | Company_0351 | Healthcare | Custom | CHURNED | $5,065 | 100% | 14% | 54h | 151 |
| 2 | Company_0031 | Education | Custom | CHURNED | $6,230 | 100% | 20% | 25h | 244 |
| 3 | Company_0015 | Education | Professional | CHURNED | $3,093 | 100% | 18% | 35h | 110 |
| 4 | Company_0460 | Healthcare | Custom | CHURNED | $4,552 | 100% | 23% | 29h | 184 |
| 5 | Company_0216 | Retail | Enterprise | CHURNED | $4,528 | 100% | 20% | 54h | 242 |
| 6 | Company_0181 | Technology | Starter | CHURNED | $4,817 | 100% | 13% | 34h | 208 |
| 7 | Company_0157 | Retail | Enterprise | CHURNED | $3,606 | 100% | 21% | 50h | 271 |
| 8 | Company_0462 | Media | Enterprise | CHURNED | $3,941 | 100% | 18% | 29h | 195 |
| 9 | Company_0345 | Non-Profit | Professional | CHURNED | $3,993 | 100% | 14% | 16h | 128 |
| 10 | Company_0497 | Non-Profit | Professional | CHURNED | $4,021 | 100% | 21% | 40h | 222 |
| 11 | Company_0114 | Legal | Enterprise | CHURNED | $6,018 | 100% | 12% | 23h | 207 |
| 12 | Company_0490 | Real Estate | Professional | CHURNED | $5,547 | 100% | 26% | 33h | 88 |
| 13 | Company_0317 | Real Estate | Professional | CHURNED | $3,549 | 100% | 22% | 25h | 272 |
| 14 | Company_0262 | Legal | Custom | CHURNED | $5,659 | 100% | 27% | 15h | 166 |
| 15 | Company_0103 | Retail | Custom | CHURNED | $5,368 | 100% | 22% | 45h | 65 |
| 16 | Company_0119 | Manufacturing | Enterprise | CHURNED | $4,451 | 100% | 9% | 14h | 56 |
| 17 | Company_0386 | Education | Professional | CHURNED | $4,387 | 100% | 16% | 16h | 273 |
| 18 | Company_0231 | Technology | Enterprise | CHURNED | $4,820 | 99% | 27% | 53h | 266 |
| 19 | Company_0184 | Finance | Enterprise | CHURNED | $4,127 | 99% | 19% | 20h | 303 |
| 20 | Company_0321 | Technology | Enterprise | CHURNED | $4,065 | 98% | 22% | 25h | 329 |
| 21 | Company_0400 | Healthcare | Professional | CHURNED | $3,072 | 98% | 15% | 13h | 154 |
| 22 | Company_0160 | Retail | Professional | CHURNED | $4,682 | 97% | 24% | 26h | 430 |
| 23 | Company_0131 | Technology | Custom | CHURNED | $5,954 | 96% | 29% | 46h | 446 |
| 24 | Company_0389 | Retail | Custom | CHURNED | $5,189 | 96% | 0% | 29h | 0 |
| 25 | Company_0282 | Healthcare | Enterprise | CHURNED | $3,482 | 94% | 18% | 21h | 281 |
| 26 | Company_0088 | Finance | Starter | **ATIVA** | $46 | 22% | 6% | 12h | 31 |
| 27 | Company_0149 | Technology | Starter | **ATIVA** | $64 | 22% | 0% | 19h | 0 |
| 28 | Company_0405 | Real Estate | Professional | **ATIVA** | $267 | 18% | 0% | 3h | 0 |
| 29 | Company_0329 | Technology | Starter | **ATIVA** | $137 | 16% | 7% | 3h | 41 |
| 30 | Company_0277 | Technology | Enterprise | **ATIVA** | $1,698 | 16% | 0% | 6h | 0 |
| 31 | Company_0083 | Media | Professional | **ATIVA** | $168 | 16% | 0% | 11h | 0 |
| 32 | Company_0313 | Real Estate | Starter | **ATIVA** | $52 | 16% | 0% | 9h | 0 |
| 33 | Company_0009 | Healthcare | Enterprise | **ATIVA** | $469 | 11% | 7% | 8h | 283 |
| 34 | Company_0152 | Retail | Enterprise | **ATIVA** | $4,595 | 11% | 0% | 6h | 0 |
| 35 | Company_0030 | Manufacturing | Professional | **ATIVA** | $459 | 11% | 8% | 10h | 373 |
| 36 | Company_0323 | Healthcare | Custom | **ATIVA** | $4,662 | 10% | 4% | 19h | 229 |
| 37 | Company_0365 | Real Estate | Enterprise | **ATIVA** | $2,900 | 10% | 4% | 31h | 304 |
| 38 | Company_0212 | Finance | Professional | **ATIVA** | $976 | 8% | 6% | 25h | 593 |
| 39 | Company_0366 | Technology | Starter | **ATIVA** | $53 | 8% | 3% | 13h | 380 |
| 40 | Company_0459 | Healthcare | Enterprise | **ATIVA** | $4,883 | 8% | 5% | 4h | 133 |
| 41 | Company_0360 | Education | Starter | **ATIVA** | $82 | 8% | 4% | 9h | 342 |
| 42 | Company_0048 | Finance | Enterprise | **ATIVA** | $3,278 | 8% | 7% | 15h | 645 |
| 43 | Company_0196 | Media | Starter | **ATIVA** | $62 | 8% | 0% | 8h | 0 |
| 44 | Company_0383 | Manufacturing | Starter | **ATIVA** | $80 | 6% | 5% | 11h | 523 |
| 45 | Company_0473 | Healthcare | Custom | **ATIVA** | $2,762 | 5% | 10% | 9h | 1,336 |
| 46 | Company_0220 | Non-Profit | Starter | **ATIVA** | $76 | 5% | 5% | 10h | 339 |
| 47 | Company_0243 | Technology | Custom | **ATIVA** | $6,558 | 5% | 0% | 8h | 0 |
| 48 | Company_0145 | Technology | Starter | **ATIVA** | $216 | 5% | 4% | 9h | 539 |
| 49 | Company_0293 | Finance | Enterprise | **ATIVA** | $2,121 | 4% | 4% | 5h | 665 |
| 50 | Company_0484 | Finance | Professional | **ATIVA** | $276 | 4% | 9% | 11h | 4,100 |

**Contas ativas prioritárias para o CS (por MRR):**
- **Company_0243** — Technology, Custom, $6,558/mês (5% risco, uso zero — possível problema de ativação)
- **Company_0459** — Healthcare, Enterprise, $4,883/mês (8% risco, uso baixo)
- **Company_0152** — Retail, Enterprise, $4,595/mês (11% risco, uso zero — red flag)
- **Company_0323** — Healthcare, Custom, $4,662/mês (10% risco, tempo de resposta de suporte alto: 19h)
- **Company_0048** — Finance, Enterprise, $3,278/mês (8% risco, taxa de erros elevada: 7%)

> O dashboard interativo (`dashboard_ceo.html`) contém o mapa de calor visual com todos os fatores normalizados, permitindo identificar padrões rapidamente.

---

## 6. O Que Fazer — 7 Ações Priorizadas

### Ação 1: CORRIGIR Workflow Builder e Report Generator
**Impacto estimado: ~$134K MRR preservado** | Prazo: 2-4 semanas | Esforço: Alto

- Sprint dedicado para reduzir error rate de 44% para <5%
- Retirar features beta de produção até estabilizar
- Comunicar proativamente aos clientes afetados
- **Por que é #1:** É a causa raiz. Sem corrigir o produto, nenhuma outra ação resolve o churn.

### Ação 2: IMPLEMENTAR Health Score + Triagem Proativa
**Impacto estimado: ~$59K MRR preservado** | Prazo: 1-2 semanas | Esforço: Médio

Health score (0-100) por conta:
```
Score = Login frequency (30%) + Feature usage (25%) + Support sentiment (15%)
        + Billing health (15%) + Engagement (15%)
```

| Score | Status | Ação Automática |
|:-----:|:------:|:---------------:|
| 80-100 | Saudável | Oportunidades de upsell |
| 60-79 | Atenção | Check-in proativo |
| 40-59 | Em risco | Campanha de intervenção |
| 0-39 | Crítico | Outreach pessoal do CS |

**Triggers automáticos:**
- Uso caiu >50% por 2 semanas → email proativo
- Sem login por 14 dias → re-engagement
- Ticket sem resolver >48h → escalação automática
- Renovação anual em 30 dias → recapitulação de valor

**Roteamento por MRR:**
- <$100/mês → flow automatizado
- $100-$500/mês → automatizado + CS acompanha
- $500-$2.000/mês → CS antes de cancelar
- $2.000+/mês → exige call com CS (sem self-serve cancel)

### Ação 3: CONSTRUIR Cancel Flow com Save Offers
**Impacto estimado: 25-35% save rate** | Prazo: 2-3 semanas | Esforço: Médio

Hoje o cancelamento é instantâneo. Implementar:

```
Botão Cancel → Exit Survey (1 pergunta) → Save Offer → Confirmação
```

| Razão | Offer Primária | Fallback |
|:-----:|:--------------:|:--------:|
| Too Expensive (74 eventos) | Desconto 25% por 3 meses | Downgrade |
| Not Using Enough (75) | Pausa 1-3 meses | Onboarding gratuito |
| Product Issues (100) | Escalação + crédito | Roadmap de correções |
| Switched Competitor (56) | Price match + comparativo | Sessão de feedback |
| Poor Support (59) | Escalação CS senior + crédito | Priority support 90 dias |
| Missing Features (37) | Preview do roadmap | Workaround guide |

**Opção de pausa:** 60-80% dos pausers voltam. Auto-reativação com email 7 dias antes.

### Ação 4: CORRIGIR Medição de Satisfação
**Impacto: Data quality** | Prazo: 1 semana | Esforço: Baixo

- Trocar CSAT reativo por NPS proativo (pós-ticket, check-in mensal)
- Segmentar por tier de saúde (não mais uma média única)
- Meta: response rate >70% em todos os segmentos (vs 54% nos churners hoje)

### Ação 5: REESTRUTURAR Paid Ads
**Impacto estimado: ~$216K MRR protegido** | Prazo: 2-4 semanas | Esforço: Médio

- Opção A: ICP scoring (Technology e Finance passam, Retail precisa de vetting)
- Opção B: Onboarding obrigatório para leads de Paid Ads
- Opção C: Redirecionar budget para Referral (22% churn) e Direct Sales (28%)

### Ação 6: REFORMAR Trial
**Impacto: 47 contas trial ativas** | Prazo: 2-3 semanas | Esforço: Médio

- Guided onboarding com milestones ("configure 3 features nos primeiros 7 dias")
- CS proativo: contato humano no dia 3 e dia 10
- Identificar activation metric: o que retidos fazem nos primeiros 7 dias que churners não fazem

### Ação 7: CONFIGURAR Dunning
**Impacto: recuperar 50-60% de pagamentos falhos** | Prazo: 1-2 semanas | Esforço: Baixo

- Pre-dunning: alertas de cartão expirando 30/15/7 dias antes
- Smart retries: 4 tentativas em 7 dias
- Emails progressivos: friendly → reminder → urgência → último aviso
- Habilitar card updater (Visa/Mastercard auto-update)

---

## 7. Roadmap de Execução

### Semana 1: Fundação
- [x] Health score + sistema de alertas proativos
- [x] Dunning (smart retries + 4 emails de recuperação)
- [x] Corrigir medição de satisfação (NPS proativo)

### Semanas 1-2: Correções Críticas
- [ ] Sprint de correção Workflow Builder / Report Generator (44% → <5%)
- [ ] Cancel flow: exit survey → save offer dinâmica → confirmação

### Semanas 2-4: Otimização
- [ ] Roteamento de suporte por MRR + health score
- [ ] Reestruturar Paid Ads
- [ ] Reformar trial com guided onboarding

### Mês 2: Mensuração
- [ ] Avaliar impacto nos leading indicators
- [ ] A/B test de save offers (desconto vs pausa vs downgrade)
- [ ] Análise de coorte por canal, plano e tenure

---

## 8. Métricas de Sucesso (90 Dias)

| Métrica | Hoje | Meta |
|---------|:----:|:----:|
| Churn rate | ~42% | <15% |
| Cancel flow save rate | 0% (não existe) | 25-35% |
| First response (contas em risco) | 28h | <2h |
| Dunning recovery rate | N/A | 50-60% |
| Feature error rate (WB/RG) | 44% | <5% |
| CSAT response rate (todos os segmentos) | 54% | >70% |

---

## 9. Limitações da Análise

1. **Dados sintéticos:** análise baseada em dados gerados com schema do Kaggle. Com dados reais, as magnitudes podem variar, mas a metodologia e os padrões se aplicam.
2. **Causalidade vs Correlação:** padrões são fortes, mas testes A/B são necessários para confirmar que corrigir as features reduz churn (vs apenas correlação).
3. **Análise snapshot:** não longitudinal. Uma análise de coorte mês-a-mês traria insights sobre tendências temporais.
4. **Segmentos pequenos:** algumas indústrias (Non-Profit: 30, Media: 33) têm amostras pequenas para conclusões robustas.

---

*Análise realizada cruzando 5 datasets: accounts, subscriptions, feature usage, support tickets e churn events.*
*Dashboard interativo disponível em `churn_dashboard.html`.*
*Risk scores individuais por conta disponíveis em `account_risk_scores.csv`.*
