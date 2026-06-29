# Submissao - Kadug - Challenge 001

## Sobre mim

- **Nome:** Kadug
- **LinkedIn:** Nao informado
- **Challenge escolhido:** 001 - Diagnostico de Churn

---

## Executive Summary

RavenStack nao tem um unico "numero culpado"; a melhor hipotese e erosao de valor antes da renovacao, aparecendo em historico de churn, friccao de suporte, uso de produto que precisa ser filtrado por janela valida e sinais comerciais. A acao mais urgente e uma save motion de duas semanas para 32 contas Critical/High, que somam US$ 1,160,702 de MRR atual e US$ 13,928,424 de ARR atual em risco. O dashboard e os reports nao recalculam nada: consomem exports canonicos gerados por um analytics core reproduzivel. As conclusoes sao tratadas como evidencias observacionais com risco causal explicito, nao como prova causal.

---

## Solucao

### Abordagem

Comecei pelo contrato dos dados, porque o CEO descreve uma contradicao entre times e isso geralmente nasce de labels, janelas e agregacoes diferentes. O pipeline em [`solution/analysis/build_exports.py`](solution/analysis/build_exports.py) le os cinco CSVs brutos, cria uma camada limpa, preserva `account_churn_flag` e `has_churn_event`, gera `feature_usage_row_id` e marca `usage_in_subscription_window_flag`. A partir disso, o script produz exports em [`solution/exports/`](solution/exports/) que viram a unica fonte de verdade para relatorio e dashboard.

Comando de reproducao:

```powershell
python ai-master-challenge/submissions/kadug/solution/analysis/build_exports.py
```

Validacao sem rebuild:

```powershell
python ai-master-challenge/submissions/kadug/solution/analysis/build_exports.py --validate-only
```

Artefatos de apoio:

- [Data quality report](solution/analysis/data_quality_report.md)
- [Findings summary](solution/analysis/findings_summary.md)
- [Export validation report](solution/analysis/export_validation_report.json)
- [Dashboard README](solution/dashboard/README.md)
- [Arquitetura](docs/architecture.md)
- [Estrategia de produto](docs/product-strategy.md)

### Resultados / Findings

#### 1. O que esta causando o churn?

A principal candidata e **erosao de valor antes da renovacao**. Ela afeta 295 contas e US$ 6,691,429 de MRR em risco, combinando historico de churn, friccao de suporte, qualidade de uso e sinais comerciais. Isso nao e prova causal; e uma hipotese operacional para validar com account reviews e intervencoes nos segmentos de maior risco.

Ranking de causas candidatas:

| Rank | Causa candidata | Contas | MRR em risco | Dono |
|---:|---|---:|---:|---|
| 1 | Value-realization erosion before renewal | 295 | US$ 6,691,429 | Leadership |
| 2 | Support friction masks satisfaction average | 456 | US$ 9,317,936 | Support |
| 3 | Commercial renewal and downgrade risk | 238 | US$ 5,080,483 | CS |
| 4 | Pricing and budget pressure | 112 | US$ 2,286,421 | Pricing |
| 5 | Product value / feature fit erosion | 90 | US$ 1,776,214 | Product |

O item de data quality ficou separado como confiabilidade analitica: ele explica por que os times podem discutir com versoes diferentes da verdade, mas nao deve ser tratado como causa de churn de cliente.

#### 2. Quais segmentos e contas estao mais em risco?

O risco acionavel esta concentrado em 32 contas Critical/High com US$ 1,160,702 de MRR atual e US$ 13,928,424 de ARR atual em risco. A lista de contas priorizadas esta em [`priority_accounts.csv`](solution/exports/priority_accounts.csv) e inclui ranking, conta, score, MRR/ARR, driver, owner e proxima acao.

| Segmento | Contas | MRR em risco | ARR em risco | Playbook |
|---|---:|---:|---:|---|
| Critical | 1 | US$ 60,092 | US$ 721,104 | Leadership-sponsored save plan within 7 days |
| High | 31 | US$ 1,100,610 | US$ 13,207,320 | CS intervention with support/product follow-up within 14 days |
| Medium | 263 | US$ 5,530,727 | US$ 66,368,724 | Monitor weekly and trigger playbook on new support or downgrade signal |
| Low | 205 | US$ 3,468,179 | US$ 41,618,148 | Standard health monitoring |

As top 20 contas priorizadas somam US$ 812,268 de MRR e US$ 9,747,216 de ARR em risco. A primeira conta da fila e `A-0cc442 / Company_198`, score 80, segmento Critical, US$ 60,092 de MRR e US$ 721,104 de ARR em risco.

#### 3. O que a empresa deveria fazer?

1. **Leadership + CS:** abrir uma save motion de duas semanas nas 32 contas Critical/High, com owner, data de contato e decisao por conta.
2. **Support:** criar uma fila semanal para contas com historico de churn, tickets high/urgent, escalacoes ou satisfacao sem resposta.
3. **Product:** revisar adocao usando apenas uso dentro da janela valida de assinatura; nao usar volume bruto como proxy de saude.
4. **Pricing / Revenue:** revisar contas com `pricing` ou `budget` como reason code antes de aplicar descontos amplos.
5. **Data:** definir a label operacional de churn e instrumentar validacao de janela de assinatura para uso de features.

O backlog completo esta em [`action_backlog.csv`](solution/exports/action_backlog.csv), com dono, prioridade, esforco, confianca, gatilho e impacto esperado.

### Contradicoes do CEO

#### "O uso cresceu"

O uso bruto realmente cresceu no portfolio: +1.92% em usage count de 2024-H1 para 2024-H2. Mas o ponto critico e que 19,432 de 25,000 linhas de uso estao fora da janela de assinatura; no periodo mais recente, 42.1% dos eventos ainda sao invalidos. Portanto, "uso cresceu" so e uma frase util se a empresa olhar para uso valid-window por segmento, nao apenas volume agregado.

#### "A satisfacao esta ok"

A media de satisfacao nao e suficiente. Contas com evento de churn tiveram 88.9% de incidencia de ticket high/urgent e 59.7% de response rate de satisfacao. A interpretacao correta e que satisfacao respondida pode parecer aceitavel enquanto contas com friccao operacional ja aparecem em risco.

### Recomendacoes

| Prioridade | Acao | Dono | Evidencia | Impacto esperado |
|---|---|---|---|---|
| 1 | Rodar save motion nas contas Critical/High | Leadership + CS | 32 contas, US$ 1,160,702 MRR / US$ 13,928,424 ARR em risco | MRR/ARR protegido e aprendizado de intervencao |
| 2 | Criar fila de suporte para contas com churn history + high/urgent/escalation | Support | Churn-event accounts com 88.9% high/urgent ticket rate | Reduzir friccao em contas de risco |
| 3 | Medir adocao somente com usage valid-window | Product + Data | 19,432 eventos fora da janela | Evitar decisao baseada em uso invalido |
| 4 | Revisar pricing/budget em contas de alto valor | Pricing | 112 contas em candidato pricing/budget | Proteger renovacoes sem desconto indiscriminado |
| 5 | Governar labels de churn | Data | 352 contas com evento vs 110 com account flag | Decisoes consistentes entre times |

### Limitacoes

- A analise e observacional; nao prova causalidade. Cada finding inclui `false_causality_risk` em [`executive_findings.csv`](solution/exports/executive_findings.csv).
- `usage_id` nao e chave unica; foi gerado `feature_usage_row_id`.
- Grande parte de feature usage esta fora da janela de assinatura; metricas de produto usam valid-window por padrao.
- `account_churn_flag` e `has_churn_event` divergem e foram preservados como labels separados.
- `satisfaction_score` tem respostas ausentes; missing nao foi tratado como zero nem como neutro.
- Feedback textual e reason codes ajudam a priorizar hipoteses, mas exigem validacao qualitativa com CS/account owners.

---

## Process Log - Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|---------------|
| Codex / GPT-5 | Leitura do challenge, estruturacao da arquitetura, implementacao do pipeline, geracao de findings e revisoes com agentes |
| Subagentes AIOX | Quality gates por papel: data-engineer, dev, analyst, pm |
| Python / pandas / Streamlit | Analytics core, exports e dashboard minimo |

### Workflow

1. Li as regras do challenge, criterios de qualidade e guia de submissao.
2. Decompus a entrega em contrato de dados, analytics core, exports, findings, relatorio e dashboard.
3. Gerei a camada limpa e validei joins, schema, flags e caveats.
4. Gerei exports canonicos e corrigi dupla contagem de MRR em findings.
5. Usei review `@analyst` para achar lacunas semanticas: campos ausentes em findings, labels incompletas, uso sem teste de crescimento e causa raiz mal ranqueada.
6. Corrigi os exports e rodei gate `@pm`, que passou em rastreabilidade, causalidade e valor para stakeholder.

### Onde a IA errou e como corrigi

- O primeiro finding de backlog somava MRR por acao e duplicava exposicao. Corrigi para expor MRR de portfolio sem dupla contagem.
- A primeira versao de Story 1.3 nao tinha owner, action, causality risk, effort e impact como campos explicitos. Corrigi `executive_findings`.
- A primeira comparacao churners vs non-churners usava so `has_churn_event`. Corrigi para incluir tambem `account_churn_flag`.
- A primeira tabela de causa candidata ranqueou data quality como top causa. Rebaixei para confiabilidade analitica e coloquei causa de negocio no topo.

### O que eu adicionei que a IA sozinha nao faria

Priorizei clareza executiva sobre sofisticao: preferi score de risco auditavel, caveats explicitos e backlog acionavel em vez de modelo preditivo fragil. Tambem separei "causa candidata de churn" de "problema de confiabilidade analitica", porque misturar esses dois pontos criaria uma recomendacao tecnicamente correta, mas ruim para decisao do CEO.

---

## Evidencias

- [x] Narrativa escrita do workflow em [`process-log/ai-workflow-log.md`](process-log/ai-workflow-log.md)
- [x] Exports canonicos em [`solution/exports/`](solution/exports/)
- [x] Data quality report em [`solution/analysis/data_quality_report.md`](solution/analysis/data_quality_report.md)
- [x] Script reproduzivel em [`solution/analysis/build_exports.py`](solution/analysis/build_exports.py)
- [x] Findings summary em [`solution/analysis/findings_summary.md`](solution/analysis/findings_summary.md)
- [x] Dashboard minimo em [`solution/dashboard/`](solution/dashboard/)
- [ ] Screenshots das conversas com IA
- [ ] Screen recording do workflow
- [ ] Git history

---

_Submissao atualizada em: 2026-06-28_
