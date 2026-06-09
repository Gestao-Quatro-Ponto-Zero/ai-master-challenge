# Process Log — Jean Felipe — Challenge 002 (Redesign de Suporte)

> Evidência de como usei IA para chegar na solução. Complementa o README da submissão.

---

## Ferramentas usadas

| Ferramenta | Para que usou |
|------------|---------------|
| **Cursor (Auto / Claude)** | Sessão principal: estrutura da submissão, `analise_dataset1.py`, `analise_dataset2.py`, RotaDesk (Next.js + Supabase), PROPOSTA/fluxo/ROI, revisão de números |
| **OpenAI gpt-4o-mini** | No protótipo: reclassificação quando sklearn &lt; 85%, rascunhos de resposta e chat com RAG |

---

## Decisões humanas (com justificativa)

| # | Decisão | O que a IA sugeriu / risco | Por que mudei | Evidência |
|---|---------|---------------------------|---------------|-----------|
| 1 | **Não tratar ciclo como KPI** | Otimizar tempo de resolução | Correlação nota × ciclo **r = −0,001** no DS1 — velocidade sozinha não move satisfação | `diagnostico/output/diagnostico_dataset1.txt` |
| 2 | **Priorizar ack + Pending**, não “resolver mais rápido” | Automação genérica de resolução | **2.819** Open sem FRT + **2.881** Pending = **67,3%** sem resolução | DS1, `DIAGNOSTICO.md` §3 |
| 3 | **Threshold 85%** (não 70%) | Relatório DS2 recomenda ≥ 70% (55,8% auto, 97,4% acc) | Mais conservador; em produção o gap DS2×DS1 derruba confiança — só **2,56%** dos textos DS1 passariam de 85% | `ds2_metrics.json` → `domain_gap` |
| 4 | **Refund / Cancel / Critical → humano sempre** | Roteamento só pelo classificador | Pior satisfação (Refund **2,93**) e alto stall; **~41%** do volume DS1 | DS1 + `routing.ts` |
| 5 | **Sem join DS1 + DS2** | Cruzar datasets para treino | Taxonomias incompatíveis (Refund/Billing vs Hardware/HR); cruzamento só em regras de produto | `PROPOSTA.md`, `roi.md` P11 |
| 6 | **`cycle_hours = \|TTR − FRT\|`** (não duração absoluta) | Usar colunas como horas ou TTR−FRT sem abs | **49,3%** dos Closed têm timestamps invertidos; `abs()` mede intervalo entre eventos | `DIAGNOSTICO.md` §2 — *highlight do process log* |

---

## Gap DS2 × suporte real (proxy executado)

Rodei `analise_dataset2.py` com ambos os CSVs. Resultados em `ds2_metrics.json` → `domain_gap`:

| Métrica | In-domain (holdout DS2) | Out-of-domain (texto DS1) |
|---------|-------------------------|---------------------------|
| Confiança (mediana) | — | **0,42** (média 0,45) |
| Auto-roteável em conf ≥ **85%** | **39,0%** | **2,56%** (217 tickets) |
| Gap de auto-roteamento | — | **−36,5 pp** |
| Classe predita dominante no DS1 | — | Hardware **56%**, Admin rights **29%** (DS1 real: Refund/Cancel ~41%) |

**Bounds de erro no subconjunto auto** (holdout in-domain, conf ≥ 85%): medido **1,13%** → conservador **2,26%** → pessimista **11,13%**.

**Misroutes/ano ilustrativos** (217 auto no DS1 @ 85%): **~5** (conservador) | **~24** (pessimista).

**Leitura:** o classificador é viável no DS2 (macro-F1 **85,7%**), mas aplicado cegamente ao texto do DS1 quase nada passa de 85% de confiança — a fila de revisão humana seria o modo normal, não exceção. Isso valida threshold alto + regras DS1 e explica por que o ROI de triagem é conservador (`roi.md` alavanca 3).

---

## Workflow por entrega

### 1. Diagnóstico operacional (`solution/diagnostico/`)

**Dataset:** `data/dataset1-support-tickets/customer_support_tickets.csv`

| Etapa | O que fiz | Como a IA ajudou | O que ajustei manualmente |
|-------|-----------|------------------|---------------------------|
| 1. Exploração | Shape, dtypes, missing, cardinalidade | Gerou script inicial e queries pandas | Validei que 29k linhas ≠ 29k tickets (multilinha); confirmei 8.469 IDs únicos |
| 2. Gargalos | Volume Open/Pending, ciclo por canal/tipo/prioridade | Automatizou agregações e tabelas | Priorizei combinações com % sem resolução, não só média de horas |
| 3. Satisfação | Médias por dimensão, correlação com ciclo | Cálculo e interpretação inicial | Decisão #1: não usar ciclo como KPI |
| 4. Desperdício | Soma Closed + estimativa Pending/Open | Metodologia A/B/C no script | Marquei estimativas B/C como ilustrativas no DIAGNOSTICO.md |

### 2. Proposta de automação (`solution/automacao/`)

**Datasets:** DS1 (contexto) + DS2 (classificação)

| Etapa | O que fiz | Como a IA ajudou | O que ajustei manualmente |
|-------|-----------|------------------|---------------------------|
| 1. EDA DS2 | Distribuição 8 classes, tamanho de texto | Script `analise_dataset2.py` | — |
| 2. Baseline | TF-IDF + Logistic Regression, holdout + CV | Pipeline sklearn e `ds2_metrics.json` | Sem LLM na primeira abordagem (requisito) |
| 2b. Gap DS2×DS1 | `assess_domain_gap()` — confiança e % auto no DS1 | Função no script + seção em `PROPOSTA.md` | Rodei com ambos CSVs; números acima |
| 3. Proposta | PROPOSTA.md, fluxo.md, roi.md | Rascunho dos docs e diagrama mermaid | Decisões #3–#5; tabela do que não automatizar |
| 4. Limiares | Curva confiança × % auto × acurácia | Métricas em `confidence_triage` | Escolhi 85% após ver gap −36,5 pp no DS1 |

### 3. Protótipo RotaDesk (`solution/rotadesk/`)

| Etapa | O que fiz | Como a IA ajudou | O que ajustei manualmente |
|-------|-----------|------------------|---------------------------|
| 1. Escopo | Ack, triagem, chat, kanban, dashboard | Mapeamento PROPOSTA → páginas | UI em pt-BR conforme `base.txt` (zinc light, sidebar) |
| 2. Implementação | Next.js, Supabase migration, APIs, sklearn via Python | Scaffold completo do app | Configurei `.env.local` com Supabase/OpenAI reais |
| 3. Fluxo de ticket | `ticket-pipeline.ts` + regras em `routing.ts` | Implementação do fluxo.md | Ordem: regras DS1 → sklearn → LLM → roteamento |

---

## Onde a IA errou e como corrigi

1. **Volume DS1** — Interpretação inicial de ~29k tickets. Corrigi explicando multilinha e validando `Ticket ID` único (8.469).
2. **First Response Time / TTR** — Risco de tratar como horas. Documentei timestamps e decisão #6 (`abs()` em 49,3% invertidos).
3. **`WORKSPACE_ROOT` no Python** — `parents[5]` apontava para pasta errada. Ajuste para `parents[4]`.
4. **Encoding Windows** — Caracteres Unicode no print quebravam cp1252. Removi símbolos problemáticos no stdout do script.
5. **Build Next.js** — `new OpenAI()` no top-level quebrava build sem API key. Lazy initialization em `getOpenAI()`.

---

## Iterações

| Parte | Iterações (~) | Observação |
|-------|---------------|------------|
| Diagnóstico | 3–4 | Parse multilinha, abs() timestamps, DIAGNOSTICO.md |
| Automação | 3 | Baseline DS2 → docs → gap DS2×DS1 com números reais |
| RotaDesk | 2–3 | Scaffold, APIs, correção build OpenAI |
| Submissão | 1–2 | README + PROCESS + revisão pós-feedback |

---

## Evidências anexadas

| Item | Status |
|------|--------|
| `../solution/diagnostico/output/` — relatório e gráficos DS1 | [x] |
| `../solution/automacao/ds2_metrics.json` — métricas DS2 + `domain_gap` | [x] |
| Git history na branch `submission/jean-felipe` | [x] |
| [Loom — walkthrough do RotaDesk](https://www.loom.com/share/968fa698a69c49e9ad9ac9cdcdbf6204) | [x] |
| `screenshots/` — prints das conversas com Cursor | [ ] opcional |
| `chat-exports/` — exports se houver sessões externas | [ ] opcional |

---

_Última atualização: 09/06/2026_
