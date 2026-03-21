# Meu Processo — Challenge 001: Diagnóstico de Churn

---

# PARTE 1: VERSÃO SIMPLES (pra eu entender)

## O que é esse challenge?

A G4 Educação criou um processo seletivo pra achar gente que sabe usar IA de verdade — não só jogar prompt no ChatGPT e entregar o que sai. Eles querem ver **como** eu penso e **como** eu uso IA como ferramenta, não como muleta.

O challenge simula uma empresa chamada RavenStack (SaaS B2B, tipo um Slack/Notion da vida). O CEO dessa empresa tá preocupado porque tão perdendo clientes, mas ninguém sabe por quê. O time de suporte diz que a satisfação tá boa. O time de produto diz que o uso cresceu. Mas os clientes continuam indo embora.

Meu trabalho: descobrir o que tá acontecendo de verdade.

## O que eu fiz até agora?

### Passo 1 — Peguei os dados e olhei tudo

Tinha 5 planilhas com dados diferentes:
- **Contas** (500 empresas clientes)
- **Assinaturas** (5.000 contratos)
- **Uso de features** (25.000 registros de como usam a plataforma)
- **Tickets de suporte** (2.000 chamados)
- **Eventos de churn** (600 vezes que alguém cancelou)

Antes de fazer qualquer análise, verifiquei se os dados batiam entre si. Se a planilha de tickets referencia uma conta que não existe na planilha de contas, a análise toda vai ser furada. Tudo bateu.

### Passo 2 — Juntei tudo numa tabela só

Cruzei as 5 planilhas numa tabela master com 55 colunas. Cada linha é uma conta, e cada coluna é uma informação: quanto paga, há quanto tempo é cliente, quantas vezes usou cada feature, quantos tickets abriu, se churneou ou não.

**Decisão importante:** a IA sugeriu usar só a última assinatura de cada conta. Rejeitei — isso perderia o histórico de upgrades e downgrades. Usei TODAS as assinaturas e criei médias e totais.

### Passo 3 — Descobri o que tá causando o churn

Aqui é onde ficou interessante. Descobri 9 coisas:

**1. O churn tá explodindo.**
No começo de 2023 eram 6 cancelamentos por trimestre. No fim de 2024 foram 251. Isso é 42 vezes mais. Não é flutuação — é uma crise acelerando.

**2. DevTools é o segmento que mais perde gente.**
31% das empresas de DevTools cancelaram. Pra comparar: EdTech e Cybersecurity ficaram em 16%. Quase o dobro.

**3. Clientes que vêm de eventos cancelam muito mais.**
30% dos que vieram de eventos foram embora. De parceiros (partners)? Só 15%. Metade. A empresa tá gastando dinheiro em eventos que trazem clientes ruins.

**4. Empresas de porte médio ($1K-$2.5K/mês) são as mais vulneráveis.**
São grandes demais pra funcionar no self-service, mas pequenas demais pra receberem atenção de conta enterprise. Ficam no limbo.

**5. As médias escondem o problema.**
Quando eu olho a média de todas as contas, churned e retidos parecem iguais em tudo — uso, satisfação, tickets, erros. Isso explica por que todo mundo acha que "tá tudo ok". O problema aparece quando eu olho por segmento.

**6. O CEO tá errado sobre o uso.**
Ele disse que "uso cresceu". Verifiquei: o uso por conta CAIU ligeiramente no segundo semestre de 2024. O time de produto provavelmente tá olhando uso total (mais contas = mais uso no agregado), não uso per capita.

**7. A satisfação dos que cancelaram é MAIOR que dos que ficaram.**
Parece estranho, mas faz sentido: quem sai por preço ou competidor pode estar satisfeito com o suporte — o problema não é atendimento, é outra coisa.

**8. 70% das contas já cancelaram pelo menos uma vez.**
O CEO vê 22% de churn (as que estão canceladas AGORA). Mas 352 de 500 contas já passaram por pelo menos um cancelamento. 175 cancelaram mais de uma vez. O problema é muito maior do que parece.

**9. Os clientes dizem por que saem: preço (36%), features faltando (34%), competidor (30%).**
Não tem uma causa só — são três problemas diferentes que precisam de soluções diferentes.

### Passo 4 — Quem vai cancelar?

Duas abordagens:

**Clustering (K-Means, k=4):** Agrupei as 500 contas em 4 perfis. Cada perfil tem comportamento diferente de MRR, uso, tempo como cliente e tickets. Serve pra personalizar intervenções.

**Risk Scoring (0-100):** O modelo de ML deu F1 = 0.098 — péssimo. Mas os segmentos da Parte 3 funcionam. Então construí um score baseado em 5 fatores que já provei que importam:
- Indústria (25%) — DevTools = 100 pontos, Cybersecurity = 25
- Canal de aquisição (25%) — Evento = 100, Partner = 20
- Faixa de MRR (25%) — Mid-market = 100, Enterprise = 30
- Escalações (15%) — quanto mais graves os tickets, mais risco
- Histórico de churn (10%) — já cancelou antes? Pode cancelar de novo

**O score funciona.** Contas classificadas como "Crítico" têm 50% de churn real. "Baixo" tem 11%. Isso é 4.5x de separação — muito melhor que o modelo ML.

**Top 20 contas em risco:** $35K MRR em risco imediato. O CEO pode ligar amanhã.

### Passo 5 — Dashboard atualizado

Atualizei o dashboard com:
- Gráfico de aceleração trimestral (6 → 251 eventos, 42x)
- Seção "Validação dos Claims do CEO" (uso cresceu? FALSO. Satisfação ok? VERDADE mas irrelevante. Churn 22%? INCOMPLETO)
- Matriz de risco visual: scatter plot com 4 quadrantes (risk score × MRR)
- Top 20 contas em risco com score e justificativa
- Risk scoring integrado em toda a análise

### O que falta?

- **Parte 6:** Documentar tudo e mandar o PR

---

# PARTE 2: VERSÃO TÉCNICA (pra decorar e compartilhar)

## Contexto e Abordagem

Fui designado como AI Master da RavenStack para diagnosticar o aumento de churn numa base de ~500 contas SaaS B2B. O CEO reportou aumento de churn apesar de métricas de uso crescentes e satisfação estável — uma contradição que precisava de investigação cross-functional.

### Metodologia

Utilizei Claude Code (Opus 4.6) como ferramenta principal de análise. O processo seguiu 6 etapas: ingestão e validação, integração cross-table, análise de causa raiz, segmentação de risco, construção de dashboard interativo, e documentação.

**Stack:** Python 3.11, Pandas, Plotly, Streamlit, Scikit-learn.

### Fase 1: Data Validation & Integration

Validei integridade referencial entre as 5 tabelas (accounts, subscriptions, feature_usage, support_tickets, churn_events) — todas as foreign keys íntegras, zero orphans.

Construí uma master table de 500 rows × 55 cols com feature engineering:
- **Subscription features**: sub_churn_rate, net_plan_movement (upgrades - downgrades), pct_annual, pct_auto_renew
- **Usage features**: error_rate, unique_features_used, pct_beta_usage, avg_usage_duration
- **Support features**: escalation_rate, avg_resolution_hours, avg_first_response_min
- **Churn features**: total_churn_events, primary_reason (moda), any_reactivation

**Decisão de design:** agreguei por account_id (não subscription_id) porque a unidade de decisão do CEO é "cliente", não "contrato". A IA inicialmente sugeriu usar apenas a última subscrição — corrigi para agregar todas, preservando histórico de movimentação.

**Sobre nulls:** satisfaction_score tem 41.6% de missing. A IA sugeriu imputar com a média. Rejeitei — há evidência de non-response bias (clientes insatisfeitos tendem a não responder pesquisas de satisfação), então imputar seria introduzir viés.

### Fase 2: Root Cause Analysis (7 Findings)

**Finding 1 — Aceleração exponencial do churn:**
De 6 eventos/quarter (Q1/2023) para 251 (Q4/2024) — crescimento de 42x. A curva é exponencial, não linear, indicando um problema sistêmico que se auto-reforça (ex: network effects negativos no mercado).

**Finding 2 — Concentração setorial em DevTools:**
Churn rate de 31.0% vs 16.5% (EdTech) e 16.0% (Cybersecurity). Cross-tab de reason_code × industry mostra DevTools com scores altos em todas as categorias — não é um problema pontual, é product-market fit fraco nesse vertical.

**Finding 3 — Canal de aquisição como driver primário:**
- Events: 30.2% churn
- Other: 24.3%
- Ads: 23.5%
- Organic: 17.5%
- Partners: 14.6%

Enquanto isso, churn por plan_tier é uniforme (~22% em Basic, Pro e Enterprise). Conclusão: a qualidade do lead importa mais que o produto contratado.

**Finding 4 — Mid-market squeeze ($1K-$2.5K MRR):**
Este tier concentra 55% da base (275 contas) com 25.8% de churn. Na cross-tab reason_code × mrr_tier, domina TODOS os reason codes. Hipótese: gap de atendimento entre self-service e enterprise.

**Finding 5 — Invalidação do claim de uso:**
O CEO afirmou que "uso cresceu". Segmentei por semestre:
- Retidos H1→H2 2024: usage_count 10.02→9.99 (−0.3%), duration 3061→2984s (−2.5%)
- Churned: flat

O time de Produto provavelmente reporta uso agregado (mais contas × mesmo uso = total maior). Per-account, o uso CAIU.

**Finding 6 — Paradoxo da satisfação:**
Satisfaction score médio: churned 4.01 vs retidos 3.97. A princípio contraintuitivo, mas consistente com churn driven por pricing/competition (não por insatisfação com suporte). O CS está tecnicamente correto — mas está medindo a variável errada.

**Finding 7 — Análise de feedback textual:**
- "too expensive": 161 (36%)
- "missing features": 155 (34%)
- "switched to competitor": 136 (30%)

Distribuição uniforme confirma natureza multifatorial. Não há silver bullet — cada driver precisa de intervenção específica.

### Fase 3: Segmentação de Risco

**Clustering (K-Means, k=4):** 4 perfis naturais com distinções claras em MRR, tenure, uso e escalações. Elbow method confirmou k=4. Normalização com StandardScaler.

**Risk Scoring (rule-based, 0-100):** 5 fatores ponderados baseados nos achados da Fase 2:
- Industry (25%): DevTools=100, FinTech=75, HealthTech=65, EdTech=30, Cybersecurity=25
- Referral source (25%): event=100, other=70, ads=65, organic=40, partner=20
- MRR tier (25%): $1K-2.5K=100 (mid-market squeeze), <$500=50, $5K+=30
- Escalation rate (15%): proporcional (0-100)
- Sub churn rate (10%): proporcional (0-100)

**Validação:** Critico = 50% churn real, Alto = 44%, Moderado = 18%, Baixo = 11%. Separação de 4.5x — muito superior ao RF (F1=0.098).

**Decisão:** Rule-based > ML neste caso. O ML falhou porque features comportamentais são quase idênticas entre churned e retidos. Features estruturais (indústria, canal, tier) TÊM poder discriminativo comprovado.

**Random Forest:** Mantido como complemento analítico (F1=0.098). O baixo F1 é em si um insight — churn driven por fatores exógenos, não comportamentais.

### Recomendações (priorizadas por impacto)

| # | Ação | Impacto | Prazo |
|---|------|---------|-------|
| 1 | CS squad dedicado DevTools | ~$50K MRR em risco | 90 dias |
| 2 | Realocar budget de eventos → partners | CAC optimization | 30 dias |
| 3 | Tier "Growth" para mid-market | ~$120K MRR em risco | 120 dias |
| 4 | Outreach proativo contas alto risco | Retenção imediata | 48h |
| 5 | Implementar 3 métricas de churn (logo, revenue, repeat) | Visibilidade | 30 dias |

### Dashboard

Dashboard Streamlit com 3 abas:
1. **Diagnóstico**: KPIs, churn por segmento, mapa geográfico, timeline, drill-down por conta
2. **Preditiva**: modelo RF, feature importance, ranking de risco, consulta individual
3. **Recomendações**: 5 ações priorizadas com impacto estimado em $ e prazo

```bash
cd submissions/theo-garcia && streamlit run app.py
```

### Onde a IA Errou e Como Corrigi

1. **Modelo preditivo fraco (F1=0.098):** Em vez de forçar overfitting, reconheci que o baixo F1 é um dado, não um bug. Features comportamentais não discriminam churn neste dataset.

2. **Agregação de subscrições:** IA sugeriu usar última subscrição. Corrigi para agregar todas — perder histórico de up/downgrade seria perder um sinal importante.

3. **Imputação de satisfaction:** IA sugeriu média. Rejeitei por non-response bias — clientes insatisfeitos não respondem pesquisas.

### O que EU Adicionei que a IA Sozinha Não Faria

- **Validação do claim do CEO:** A IA analisou os dados que pedi. Mas a decisão de TESTAR se "uso cresceu" segmentando por account e por semestre foi minha — ela não questionaria a premissa do CEO por conta própria.
- **Interpretação do paradoxo de satisfação:** A IA flagou que churned > retidos em satisfação. A interpretação de que isso indica churn por fatores exógenos (pricing) e não por insatisfação foi julgamento humano.
- **Decisão de não forçar o modelo:** A tentação de tunar hiperparâmetros até o modelo parecer bom é forte. Reconhecer que F1=0.098 é um insight sobre a natureza do dataset, não um problema a ser "resolvido", requer julgamento.

---

*Documento atualizado conforme o progresso. Última atualização: Parte 3 concluída.*
