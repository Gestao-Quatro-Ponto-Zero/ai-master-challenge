# Submissão — Jean Felipe — Challenge 002

## Sobre mim

- **Nome:** Jean Felipe
- **LinkedIn:** https://www.linkedin.com/in/jean-felipe-06380b185/
- **Challenge escolhido:** [002 — Redesign de Suporte](../../challenges/process-002-support/README.md) (Operações / CX)

---

## Executive Summary

Analisei **8.469 tickets** de suporte (DS1) e identifiquei que **67,3%** permanecem sem resolução — sendo **2.819** sem primeira resposta e **2.881** em Pending. O tempo de ciclo **não correlaciona** com satisfação (r = −0,001), então a automação deve focar em **ack**, **follow-up** e **triagem**, não em “resolver mais rápido”. Treinei um classificador TF-IDF + regressão logística no DS2 (**macro-F1 86%**) e construí o protótipo **RotaDesk** (Next.js + Supabase): ack automático, roteamento com threshold de **85%** de confiança, humano obrigatório em Refund/Cancel/Critical, e **gpt-4o-mini** para baixa confiança, rascunhos e RAG. **Recomendação:** implantar triagem na entrada com humano no loop antes de prometer ganhos de CSAT por velocidade.

---

## Solução

Entrega em três etapas, alinhada ao brief do challenge:

| Etapa | Pasta | Entregável |
|-------|-------|------------|
| 1. Diagnóstico | `solution/diagnostico/` | Análise operacional DS1 + script reproduzível |
| 2. Automação | `solution/automacao/` | Baseline de classificação DS2 + proposta + ROI |
| 3. Protótipo | `solution/rotadesk/` | App funcional RotaDesk |

### Abordagem

1. **Diagnóstico primeiro (DS1)** — Explorar parse do CSV (campos multilinha), entender missing estruturado por status, calcular tempo de ciclo como `|TTR − FRT|` com `abs()` (49,3% timestamps invertidos), quantificar gargalos e desperdício.
2. **Viabilidade técnica (DS2)** — EDA das 8 categorias, baseline linear sem LLM, holdout 20% + CV 5-fold; só então desenhar automação.
3. **Decisão de produto** — Cruzamento estratégico DS1×DS2 (sem join de datasets): priorizar ack e Pending; não usar ciclo como KPI; threshold 85%; humano em casos sensíveis.
4. **Protótipo** — Implementar fluxo documentado em `solution/automacao/fluxo.md` com stack pedida no challenge.

### Resultados / Findings

#### Dataset 1 — Operação

| Métrica | Valor |
|---------|-------|
| Tickets únicos | 8.469 (29.808 linhas físicas por multilinha) |
| Sem resolução | 5.700 (67,3%) |
| Open (sem FRT) | 2.819 |
| Pending Customer Response | 2.881 |
| Satisfação média (Closed) | 2,99 |
| Correlação nota × tempo de ciclo | −0,001 |
| Desperdício estimado | 59.629 h |

**Gargalos:** Social media/Email (~7,9 h ciclo); Refund/Cancellation (~8 h); combinações com até **80,6%** sem resolução (Phone + Cancellation + Low).

Artefatos: `solution/diagnostico/DIAGNOSTICO.md`, `solution/diagnostico/output/diagnostico_dataset1.txt`, gráficos em `output/`.

#### Dataset 2 — Classificação

| Métrica | Holdout 20% | CV 5-fold |
|---------|-------------|-----------|
| Accuracy | 85,7% | 85,8% ± 0,2% |
| Macro-F1 | 85,7% | 85,9% ± 0,3% |

Classe fraca: **Administrative rights** (F1 0,76). Com confiança ≥ 70%: 55,8% auto-roteáveis com 97,4% de acurácia no subconjunto (referência em `ds2_metrics.json`).

Artefatos: `solution/automacao/ds2_metrics.json`, `PROPOSTA.md`, `fluxo.md`, `roi.md`.

#### Protótipo RotaDesk

- **Dashboard:** métricas, gráficos por cenário/canal/status, últimos tickets.
- **Simulador:** criação de tickets com fluxo completo (ack → sklearn → LLM se &lt; 85% → roteamento).
- **Chat:** atendimento simulado com RAG (`knowledge_articles`) e gpt-4o-mini.
- **Kanban:** acompanhamento por status.
- **Demo:** [RotaDesk na Vercel](https://ai-master-challenge-psi.vercel.app) · [Loom — walkthrough](https://www.loom.com/share/968fa698a69c49e9ad9ac9cdcdbf6204)

Setup: `solution/rotadesk/README.md`

### Recomendações

1. **Ack automático** nos ~2.819 Open — maior alavanca de volume sem prometer CSAT por velocidade.
2. **Follow-up estruturado** nos ~2.881 Pending — reduzir fila parada.
3. **Triagem sklearn na entrada** com confiança ≥ 85% e revisão humana abaixo disso.
4. **Humano obrigatório** em Refund, Cancellation e Critical — sustentado pelo DS1 (satisfação e stall).
5. **Não adotar tempo de ciclo como KPI principal** — investir em qualidade de resolução por tipo de pedido.
6. **Administrative rights** sempre em revisão — F1 0,76 no baseline.

### Limitações

- DS1 e DS2 são **datasets distintos** (taxonomias diferentes); classificador DS2 não foi validado em texto do DS1. Erro esperado em produção (gap de domínio) está quantificado em `solution/automacao/PROPOSTA.md` e reproduzível via `domain_gap` em `ds2_metrics.json` (`python analise_dataset2.py` com ambos CSVs).
- Timestamps do DS1 são **ruidosos** (49,3% ordem invertida); ciclo mede apenas FRT→TTR, não abertura→resolução.
- Estimativas de desperdício em Pending/Open usam **mediana dos Closed** — ilustrativas.
- Triagem **sklearn** em produção via **API no Render** (`CLASSIFIER_API_URL`); Vercel só hospeda o Next.js. Sem medição de CSAT pós-piloto.
- `pipeline.joblib` (~5 MB) deve ser gerado localmente (`python ml/train_export.py`).

---

## Setup rápido (reprodução)

### Datasets (não versionados)

Baixar do [Kaggle DS1](https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset) e [Kaggle DS2](https://www.kaggle.com/datasets/adisongoh/it-service-ticket-classification-dataset).

Colocar na pasta `data/` **na raiz do workspace** (pai do clone `ai-master-challenge/`), ou passar `--dataset /caminho/arquivo.csv` nos scripts:

```
data/dataset1-support-tickets/customer_support_tickets.csv
data/dataset2-it-classification/all_tickets_processed_improved_v3.csv
```

### Diagnóstico DS1

```bash
cd submissions/jean-felipe/solution/diagnostico
pip install -r requirements.txt
python analise_dataset1.py
# alternativa: python analise_dataset1.py --dataset /caminho/customer_support_tickets.csv
```

### Automação DS2

```bash
cd submissions/jean-felipe/solution/automacao
pip install -r requirements.txt
python analise_dataset2.py
# alternativa: python analise_dataset2.py --dataset /caminho/all_tickets_processed_improved_v3.csv
```

### RotaDesk

```bash
cd submissions/jean-felipe/solution/rotadesk
pip install -r ml/requirements.txt && python ml/train_export.py   # gera ml/pipeline.joblib
npm install
cp .env.local.example .env.local   # Supabase + OPENAI_API_KEY
# Rodar supabase/migrations/001_initial.sql no SQL Editor do Supabase
npm run dev
```

Deploy: **Vercel** (frontend) + **Render** (API sklearn) — ver `solution/rotadesk/README.md` e `solution/rotadesk/ml/README.md`.

---

## Process Log — Como usei IA

> Detalhamento completo em [`process-log/PROCESS.md`](./process-log/PROCESS.md)

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|---------------|
| **Cursor (Claude)** | Diagnóstico DS1/DS2, scripts Python, protótipo Next.js, documentação PROPOSTA/fluxo/ROI |
| **OpenAI gpt-4o-mini** | Reclassificação (&lt;85% conf.), rascunhos e chat com RAG no RotaDesk |

### Workflow

1. Exploração DS1 com IA + validação manual (parse multilinha, missing por status).
2. Script `analise_dataset1.py` iterado após correção de timestamps e `abs()`.
3. Baseline DS2 sem LLM; métricas em JSON; decisão de threshold 85%.
4. Documentos de automação (PROPOSTA, fluxo, ROI) antes do código do protótipo.
5. RotaDesk: scaffold Next.js → migration Supabase → pipeline sklearn → APIs → UI em português.

### Onde a IA errou e como corrigi

1. **Contagem de tickets** — IA assumiu ~29k registros; corrigi com parse RFC 4180 (8.469 únicos).
2. **Timestamps** — Tratados como duração; redefini `cycle_hours = |TTR − FRT|` e documentei em DIAGNOSTICO.md.
3. **Caminho do dataset** — `parents[N]` errado no script; ajustado após erro de FileNotFoundError.
4. **OpenAI no build** — Cliente instanciado no import quebrava `next build`; lazy init em runtime.

### O que eu adicionei que a IA sozinha não faria

1. Decisão de **não** priorizar ciclo como KPI após ver correlação ≈ 0 com satisfação.
2. Regra de negócio: **Refund/Cancel/Critical** sempre humanos, independente do classificador.
3. Threshold **85%** (mais conservador que 70% do relatório DS2).
4. Cruzamento DS1×DS2 **sem join** — honestidade metodológica na proposta.

---

## Evidências

- [x] Process log narrativo — `process-log/PROCESS.md`
- [x] Git history — branch `submission/jean-felipe`
- [x] Scripts e relatórios reproduzíveis em `solution/`
- [x] Screen recording — [Loom: walkthrough do RotaDesk](https://www.loom.com/share/968fa698a69c49e9ad9ac9cdcdbf6204)
- [ ] Screenshots — opcional (`process-log/screenshots/`)
- [ ] Chat exports — opcional (`process-log/chat-exports/`)

---

## Checklist do PR

- [x] Challenge 002 lido e respondido (diagnóstico + automação + protótipo)
- [x] Solução em `submissions/jean-felipe/`
- [x] Process log incluído
- [x] README com template preenchido
- [x] Instruções de setup nos READMEs de cada módulo
- [x] Alterações apenas dentro de `submissions/jean-felipe/` *(verificar antes do push)*

**Título sugerido do PR:** `[Submission] Jean Felipe — Challenge 002`

---

_Submissão preparada em: 09/06/2026_
