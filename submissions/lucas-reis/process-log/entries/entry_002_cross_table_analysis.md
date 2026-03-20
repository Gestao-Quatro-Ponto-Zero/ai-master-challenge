# Entry 002b — Análise Cross-Table: o que os dados revelaram

**Data:** 2026-03-20
**Fonte:** entry_002_cross_table_output.md
**Autor:** Lucas Reis

---

## O insight mais surpreendente: hipóteses centrais foram refutadas

### Surpresa #1 — Churners usam MAIS features que retidos (+3.4%)

A hipótese H1 ("baixo uso de features → churn") foi **refutada completamente**.

| Métrica | Churners | Retidos | Esperado |
|---------|---------|---------|----------|
| Features distintas usadas | **28.34** | 27.41 | Churners < Retidos |
| Total de eventos | **52.05** | 49.42 | Churners < Retidos |
| Erros registrados | 28.15 | 28.23 | Churners > Retidos |

**Interpretação:** Os churners da RavenStack não são usuários inativos — são usuários que
**engajaram com o produto, descobriram que ele não entregava o que precisavam, e saíram**.
Isso é consistente com o reason_code #1 = "features" (60.9% dos churners).
O problema não é adoção, é product-market fit.

Nenhuma conta tem menos de 3 features usadas. O produto tem engajamento alto — a retenção
vai falhar por qualidade/completude de features, não por falta de uso.

---

### Surpresa #2 — Tickets urgentes têm churn MENOR que contas sem tickets

| Grupo | Churn rate |
|-------|-----------|
| COM ticket urgent | **19.9%** |
| SEM ticket urgent | **25.7%** |

**Interpretação:** Contra-intuitivo, mas faz sentido. Clientes que abrem tickets urgentes
estão **investidos o suficiente para pedir ajuda**. O grupo sem tickets pode conter
"churners silenciosos" — clientes que decidiram sair sem dar chance ao suporte.

**Exceção:** escalation tem correlação POSITIVA com churn (25.3% vs 21.3%), e as contas
com first_response mais RÁPIDO (Q1) têm o MAIOR churn (29%). Isso sugere que os clientes
mais ativamente insatisfeitos (escalaram, precisaram de resposta urgente) têm maior
probabilidade de sair, mas o mero ato de abrir um ticket não prediz churn.

---

### Surpresa #3 — auto_renew=False tem MENOR churn que auto_renew=True

| Grupo | Churn rate |
|-------|-----------|
| COM auto_renew=False | 21.4% |
| SEM auto_renew=False | 25.4% |
| Lift | **0.85× (inverso)** |

**Interpretação:** H6 foi **refutada**. Quem desativou auto-renovação pode estar
tomando uma decisão financeira consciente (controle de custos) sem intenção de sair.
O churn silencioso — de quem nunca desativou auto_renew e simplesmente parou de usar —
é mais prevalente.

---

### Surpresa #4 — Buyer's remorse é muito menor que o EDA sugeria

O EDA mostrou 18.2% dos churners com preceding_upgrade_flag no churn_events bruto.
Na análise cross-table com o target correto (accounts.churn_flag):

- Apenas **11 churners (10%)** tiveram preceding_upgrade_flag = True
- MRR diferença: $2,140 vs $2,204 — **marginal**
- EdTech tem a maior taxa (20%), mas com n=10 churners — sem significância estatística

A hipótese de buyer's remorse como causa raiz de churn foi **enfraquecida significativamente**.

---

## O que confirmou as hipóteses do EDA

### Confirmado — DevTools como segmento de maior risco

| Indústria | Churn rate |
|-----------|-----------|
| **DevTools** | **31.0%** 🚨 |
| FinTech | 22.3% |
| HealthTech | 21.9% |
| EdTech | 16.5% |
| Cybersecurity | 16.0% |

DevTools tem churn quase **2× o de Cybersecurity e EdTech**. Esta é a segmentação
mais acionável encontrada — permite ao time de CS priorizar contas DevTools.

### Confirmado — Canal event tem o pior perfil de retenção

| Canal | Churn rate |
|-------|-----------|
| event | **30.2%** |
| other | 24.3% |
| ads | 23.5% |
| organic | 17.5% |
| **partner** | **14.6%** |

Clientes adquiridos em eventos têm churn **2× o de clientes via partner**.
Implicação: o perfil do cliente de evento (piloto temporário, curiosidade de conferência)
não converte em usuário comprometido. Refinar a qualificação de leads em eventos ou
focar aquisição em canais partner e organic.

### Confirmado — Product gap é a causa raiz dominante

**60.9% dos churners** declaram "features" como reason_code.
MRR perdido por product gap: **$145,526** — maior de todas as causas.

---

## O que contradisse as hipóteses do EDA

| Hipótese (do EDA) | Status | Resultado real |
|-------------------|--------|---------------|
| H1: baixo uso → churn | ❌ Refutada | Churners usam +3.4% mais features |
| H6: auto_renew=False → churn | ❌ Refutada | auto_renew=False tem churn MENOR |
| H2: tickets urgentes → churn | ❌ Parcialmente refutada | Urgentes têm churn MENOR |
| H8: buyer's remorse dominante | ⚠️ Enfraquecida | Apenas 10% dos churners, não causa raiz |
| Plan tier diferencia churn | ❌ Refutada | 22.1% / 22.0% / 21.9% — idêntico |

---

## Contas específicas em maior risco (lista de ação)

| Account ID | Indústria | MRR/mês | Sinais de risco | Ação |
|-----------|-----------|---------|----------------|------|
| A-e43bf7 | Cybersecurity | $6,667 | 4/4 sinais 🚨 | **Intervenção imediata** |
| A-c58f49 | EdTech | $10,140 | 3/4 sinais | Contato CS prioritário |
| A-76fa4d | HealthTech | $8,812 | 3/4 sinais | Contato CS prioritário |
| A-afa505 | DevTools | $7,334 | 3/4 sinais | Contato CS prioritário |
| A-5c046d | EdTech | $10,486 | 2/4 sinais | Monitorar + outreach |
| A-5b1bcd | DevTools | $8,887 | 2/4 sinais | Monitorar |
| A-56962b | EdTech | $7,801 | 2/4 sinais | Monitorar |

**A-e43bf7 (Cybersecurity, $6,667/mês)** é o caso mais crítico: único com 4/4 sinais
(auto_renew=False, escalation, baixo uso, ticket urgente).

**MRR total em risco imediato (2+ sinais): $710,421**

---

## O que o CEO precisa saber em 3 frases

1. **O produto está afastando clientes que já o adotaram:** 60.9% dos churners saem
   por product gap ("features"), não por falta de uso — o churn está na qualidade e
   completude do produto, não no engajamento.

2. **DevTools (31%) e clientes vindos de eventos (30%) churnam quase 2× a média:**
   a estratégia de aquisição e o produto precisam ser revistos para estes segmentos
   antes de qualquer expansão.

3. **$710K de MRR ativo está em contas com 2+ sinais de risco hoje:** uma campanha de
   CS proativa nas próximas 4 semanas, começando pelos top 10 listados, pode salvar
   uma fração significativa deste MRR antes que o churn se materialize.

---

## O que o Agent 03 (hipóteses) deve priorizar

1. **Validar estatisticamente** a diferença de churn DevTools vs outros setores
2. **Testar** se reason_code=features correlaciona com feature_error_count (produto com bugs)
3. **Investigar** por que Q1 de resposta rápida tem mais churn — efeito de seleção?
4. **Validar** canal event vs partner com teste estatístico
5. **Reformular H6** — auto_renew é anti-sinal neste dataset
6. **Nova hipótese:** contas com escalation + urgente = maior churn que escalation alone
