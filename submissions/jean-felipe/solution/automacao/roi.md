# Estimativa de ROI — RotaDesk

Premissas explícitas. Números operacionais do **DS1** (`diagnostico/output/diagnostico_dataset1.txt`); viabilidade de triagem do **DS2** (`ds2_metrics.json`).

**Horizonte:** recorte anual equivalente ao volume do DS1 (**8.469 tickets**). Valores em horas e USD são **ilustrativos**, não auditoria financeira.

---

## Premissas compartilhadas

| # | Premissa | Valor | Fonte / justificativa |
|---|----------|-------|------------------------|
| P1 | Volume anual de tickets | **8.469** | DS1: registros parseados |
| P2 | Custo hora agente | **US$ 35/h** | DS1: mesmo parâmetro do relatório de desperdício |
| P3 | Tickets Open (sem FRT) | **2.819** (33,3%) | DS1 |
| P4 | Tickets Pending | **2.881** (34,0%) | DS1 |
| P5 | Tickets sem resolução | **5.700** (67,3%) | DS1 |
| P6 | Correlação tempo × satisfação | **−0,001** | DS1 — ROI **não** assume ganho de CSAT por velocidade |
| P7 | Macro-F1 classificador | **0,8568** | DS2 holdout |
| P8 | Threshold auto-roteamento | **85%** | Decisão de produto |
| P9 | Acurácia subconjunto auto (referência) | **≥ 98,43%** | DS2 holdout em conf **≥ 0,8** (ponto medido mais próximo de 85%) |
| P10 | % auto-roteável em conf ≥ 0,8 | **45,4%** | DS2 holdout — em **≥ 0,85** usamos **≤ 45,4%** (conservador) |
| P11 | DS1 e DS2 sem join | — | Taxonomias diferentes; benefício de triagem é **estimado por analogia**, não medido no DS1 |
| P12 | Erro em produção (gap DS2×DS1) | **~3,1%** no auto-subset (conservador) | Holdout in-domain: **1,57%** erro em conf ≥ 0,8; penalidade **2×** por domain shift — ver `PROPOSTA.md` e `domain_gap` em `ds2_metrics.json` |
| P13 | Misroutes/ano (ilustrativo) | **~105** (conservador) | 3.388 auto-roteados × 3,1%; pessimista **~390** — só tickets sem revisão humana |

---

## Alavanca 1 — Auto-confirmação (ack)

### Problema (DS1)

**2.819** tickets em Open **sem** `First Response Time` — fila sem qualquer primeira resposta registrada.

### Premissas desta alavanca

| Premissa | Valor |
|----------|-------|
| Tempo médio manual para ack (ler + responder + registrar) | **8 min/ticket** |
| % dos Open que passariam por ack automático no ano 1 | **90%** (2.537 tickets) |
| Redução de tempo agente por ack automático | **100%** do tempo de ack manual |

### Cálculo

```
Horas economizadas = 2.537 × (8 / 60) = 338 h/ano
Valor ilustrativo  = 338 × US$ 35 = US$ 11.830/ano
```

### Benefício qualitativo (não quantificado no relatório)

- Reduz tickets “fantasma” na fila Open.
- Alinha operação ao KPI de **ack SLA**, não de ciclo completo.

---

## Alavanca 2 — Follow-up em Pending Customer Response

### Problema (DS1)

**2.881** tickets em Pending — tempo investido sem fechamento. Estimativa DS1 de horas em Pending: **19.303 h** (2.881 × mediana 6,7 h) — componente B do relatório de desperdício.

### Premissas desta alavanca

| Premissa | Valor |
|----------|-------|
| % Pending elegível a follow-up automático | **80%** (2.305 tickets) |
| Tempo agente evitado por follow-up manual (média) | **12 min/ticket** (lembrar cliente + atualizar ticket) |
| Taxa de retorno do cliente após follow-up automático | **15%** — **premissa de produto**, não está no relatório |

### Cálculo (somente tempo de agente evitado)

```
Horas economizadas = 2.305 × (12 / 60) = 461 h/ano
Valor ilustrativo  = 461 × US$ 35 = US$ 16.135/ano
```

### O que não assumimos

- Não convertemos as **19.303 h** de desperdício Pending em economia total — são estimativa estrutural do DS1, não tempo evitável só com email automático.
- Não prometemos melhoria de satisfação (correlação tempo ≈ 0).

---

## Alavanca 3 — Triagem / roteamento automático (DS2)

### Base (DS2)

- Macro-F1 **0,8568**; CV **0,8594 ± 0,0028**.
- Com conf **≥ 0,8**: **45,4%** auto-roteados, acurácia **0,9843** no subconjunto.
- **Administrative rights**: F1 **0,762** → excluído do auto-roteamento no produto.
- Threshold produto **85%** → fração auto-roteada **≤ 45,4%** (premissa P10).

### Premissas desta alavanca

| Premissa | Valor |
|----------|-------|
| Tickets/ano passando pelo classificador | **8.469** (100%) |
| % auto-roteados (conf ≥ 85%, conservador) | **40%** (3.388 tickets) — abaixo dos 45,4% medidos em 0,8 |
| % enviados a revisão humana | **60%** |
| Tempo triagem manual evitado por auto-roteado | **5 min/ticket** |
| Tempo revisão humana (conf &lt; 85% ou regra) | **3 min/ticket** (mais rápido que triagem do zero) |
| Tickets Refund + Cancel + Critical (humano obrigatório) | **~41%** do DS1 (1.752 + 1.695 = 3.447 → **40,7%**) — **não** economizam triagem |

### Cálculo (triagem pura)

Auto-roteados elegíveis (excluindo ~40,7% regra humana obrigatória do fluxo de triagem automática):

```
Base triagem automática ≈ 8.469 × 40% auto × (1 - 0% bloqueio pós-classificação)
Usamos cenário conservador: 3.388 tickets auto × 5 min = 16.940 min = 282 h/ano

Revisão: (8.469 - 3.388) × 3 min = 15.081 min = 251 h gastos em revisão

Economia líquida vs triagem manual total (8.469 × 8 min = 1.126 h):
  Triagem manual hipotética = 8.469 × (8/60) = 1.129 h
  Com automação = 282 h evitados nos auto + 251 h revisão + (3.447 × 8/60) humano obrigatório sem triagem ML
```

**Cenário simplificado (comparável ao relatório DS1):**

```
Economia triagem = tickets auto-roteados × tempo triagem manual evitado
                 = 3.388 × (5 / 60) = 282 h/ano
Valor ilustrativo = 282 × US$ 35 = US$ 9.870/ano
```

---

## Consolidação

| Alavanca | Horas economizadas (ilustrativo) | USD/ano (@ US$ 35/h) |
|----------|----------------------------------|----------------------|
| 1. Ack automático | **338 h** | **US$ 11.830** |
| 2. Follow-up Pending | **461 h** | **US$ 16.135** |
| 3. Triagem (conf ≥ 85%) | **282 h** | **US$ 9.870** |
| **Total** | **~1.081 h** | **~US$ 37.835** |

### Referência de escala (DS1)

O relatório DS1 estima **59.629 h** de desperdício total no recorte (Closed + Pending + Open). A automação proposta ataca **~1,8%** desse total em horas de agente evitadas — **premissa conservadora**, focada em tarefas de baixo julgamento (ack, lembrete, triagem inicial).

Cenário DS1 de recuperação em Closed (P75→P25): **8.838 h** — **não** incluído aqui porque o protótipo **não** prioriza redução de ciclo como KPI.

---

## Custos do protótipo (ordem de grandeza)

| Item | Premissa |
|------|----------|
| Supabase (free/pro) | US$ 0–25/mês no desafio |
| Hospedagem Next.js (Vercel) | US$ 0–20/mês |
| Manutenção modelo | Retreino trimestral — horas internas, não quantificado |

**Payback ilustrativo** vs custo infra desprezível no piloto; valor está em **validação do fluxo** para o challenge.

---

## Riscos que reduzem ROI (dos relatórios)

| Risco | Evidência |
|-------|-----------|
| Classificador errado em Admin rights | F1 **0,762** — mitigado por revisão obrigatória |
| Auto-roteamento em Refund/Cancel | DS1: pior satisfação e alto stall — mitigado por regra humana |
| Confundir linhas físicas com tickets | DS1: 29.808 linhas → 8.469 tickets |
| Prometer CSAT por velocidade | Correlação **−0,001** |
| Aplicar % do DS2 diretamente ao DS1 | Sem join — % auto-roteado é **analogia** |
| Domain shift DS2→DS1 | Classificador de TI em texto de suporte ao cliente; **~105 misroutes/ano** no cenário conservador (3,1% × auto) — proxy em `analise_dataset2.py` §5 |
| ROI de triagem superestimado | Queda de confiança OOD pode **aumentar % em revisão** e reduzir as 282 h economizadas na alavanca 3 |

---

## KPIs para validar ROI no piloto (não ciclo)

1. **Ack &lt; 5 min:** meta ≥ **95%** dos novos tickets.
2. **Open backlog:** redução vs baseline **2.819**.
3. **Pending &gt; 14 dias:** redução vs snapshot atual.
4. **Triagem:** medir % auto em conf ≥ 85% e taxa de correção na revisão humana.
5. **Satisfação:** medir **após** piloto — não assumir no modelo de ROI.

---

## Resumo executivo

A proposta monetiza **tempo de agente em ack, follow-up e triagem**, não “resolução mais rápida”. Os números do DS1 justificam **priorizar os 2.819 Open e 2.881 Pending**; o DS2 (**86% macro-F1**) justifica **triagem com threshold 85% e humano no loop**. ROI consolidado ilustrativo: **~US$ 38k/ano** e **~1.081 h** no volume de 8.469 tickets — conservador frente aos **59.629 h** de desperdício estimados no relatório completo.
