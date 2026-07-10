# Prompt 02 — EDA contra schema real (AGENT-B + SKILL-04)

> **Prompt emitido:**

```
[AGENT: BUILDER] [SKILL: SEC-SCAN]

Escreva script EDA em pandas para sales_pipeline.csv.
Requisitos:
- Carregar de solution/data/sales_pipeline.csv (path relativo com pathlib)
- Não assumir nomes de coluna — print df.columns e dtypes primeiro
- Checar nulos por coluna
- Distribuição de deal_stage
- Win rate (Won / Won+Lost) por sales_agent, ordenado
- Distribuição de close_value por stage
- Tempo médio entre engage_date e close_date por stage
  (USAR format='%m/%d/%Y' — descobri na mão que é MM/DD/YYYY)

Sem hardcode. Sem PII printado. Salvar resultados em solution/eda_report.txt
também, não só printar.
```

---

## Script entregue

`solution/eda.py` — construído contra todas as regras do Prompt 02:
- ✅ Paths relativos via `pathlib.Path(__file__).resolve().parent`
- ✅ Schema impresso primeiro (colunas + dtypes) antes de qualquer agregação
- ✅ Formato de data `MM/DD/YYYY` explicitado em `DATE_FORMAT`
- ✅ Output paralelo em `eda_report.txt` (buffer único `_emit` captura stdout + arquivo)
- ✅ PII de `sales_agent` anonimizada no relatório (`agent_01..agent_35`)
- ✅ Armadilhas A2 (nulos em engage por stage) e A10 (manager×office) checadas

## Achados principais (numéricos)

### Schema
- 8.800 linhas × 8 colunas — bate com o brief
- Colunas: `opportunity_id, sales_agent, product, account, deal_stage, engage_date, close_date, close_value`
- Datas convertidas com `format='%m/%d/%Y'` — sem NaT silencioso

### Distribuição de stage
| Stage | Contagem | % |
|-------|---------|---|
| Engaging | 2484 | 28.23% |
| Won | 2360 | 26.82% |
| Prospecting | 2224 | 25.27% |
| Lost | 1732 | 19.68% |

### Nulos
- `close_date`: 53.5% nulos — **esperado** (deals em aberto não têm close_date)
- Demais colunas: 0% nulos
- ALERTA de armadilha A2: 0 nulos em `engage_date` mesmo em `Prospecting` — para os dados sintéticos está OK, mas em dados reais este é o ponto de atenção

### Win rate por agente
- 35 agentes
- Faixa: **42.37% a 66.96%** (dispersão significativa — suporta H3 do Prompt 01)
- Média global: 57.67%
- Top: agent_01 (67%), Bottom: agent_35 (42%)

### close_value por stage
- Won: mean $3.847, median $1.495, max $37.554
- Engaging: mean $2.141 (valor esperado de deals abertos)
- Prospecting: mean $2.239
- Lost: $0 (confirmado — 0 deals Won com `close_value=0`, sem bug A4)

### Velocidade no pipeline (Won+Lost)
- Média: 61.3 dias
- Mediana: 62 dias
- IQR: 32–91 dias
- Sem diferença material entre Won (61.4) e Lost (61.2) — **H2 parcialmente refutada**: idade isolada não distingue outcome, mas pode haver janela não-linear a investigar

### Manager × Office (armadilha A10)
- 3 managers × 5 escritórios
- Nenhum manager cobre só 1 escritório → **não são colineares**, posso usar ambos como features

### Tabelas auxiliares
- accounts.csv: 85 contas, 8 indústrias, 6 países
  - revenue: $1.881 a $287.787 (mediana $23.968)
  - employees: 8 a 5.720
  - has_trial: 11 True / 74 False (~13% — variância suficiente para discriminar)
- products.csv: 7 produtos, preços $800 (CRM Connect) a $25.000 (GTX Enterprise)

## Hooks ativados (SKILL-04 SEC-SCAN)

| Hook | Resultado |
|------|-----------|
| `dtype-check` | ✅ dtypes impressos no topo do relatório, datas convertidas com formato explícito |
| `pct-null-alert` | ✅ `close_date` em 53.5% — sinalizado como esperado (deals abertos) |
| Edge case A2 | ✅ Nulos em engage por stage validados a zero (sintético); em dados reais este é o ponto de atenção |

## Decisões de scoring derivadas da EDA

Com base nos achados, calibrei os pesos do Prompt 03 (spec):

1. **Stage advancement** (25%) — confirmado: Won Engaging > Prospecting
2. **Pipeline velocity** (20%) — revisão: como Won≈Lost em idade, vou criar **velocidade relativa ao stage** como mediana-bucketed, não idade crua
3. **Account size** (20%) — confirmado: contas têm variância suficiente (revenue 1.8K–287K)
4. **Product value** (15%) — confirmado: 7 produtos com preços bem estratificados
5. **Agent track record** (15%) — **FORTALECIDO**: win rate varia 42%–67%, essa feature discrimina muito
6. **Deal value** (5%) — confirmado: close_value tem range amplo em Won

---

_Estado do harness após Prompt 02:_
- Agent: BUILDER ✅ (execução contra spec)
- Skill: SEC-SCAN ✅ (hooks ativados, PII protegida, paths relativos)
- EDA rodada contra CSVs reais ✅
- Próximo prompt: **Prompt 03 — Spec do Scoring** (AGENT-A + SKILL-02)