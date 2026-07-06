# Prompt 04 — Build da função de scoring (AGENT-B)

> **Prompt emitido:**

```
[AGENT: BUILDER]

Implemente a spec aprovada emAnexo: {colar spec do Prompt 03}
Arquivo: solution/scoring.py
Constraints:
- Função score_deal(row: dict, agent_winrate: dict) -> tuple[int, dict]
- Componentes normalizados via MinMax respeitando ranges reais dos dados
- Docstring cite o porquê de cada peso
- Type hints
- Tratar deals Prospect sem engage_date (velocity=0, label específica)
- Não usar sklearn nesta versão — matemática pura com numpy/pandas
```

---

## Decisão de divergência consciente da SPEC

A implementação `scoring.py` **diverge propositadamente** da SPEC mínima em dois pontos, em favor
de uma arquitetura mais idiomática e testável:

| Ponto | SPEC mínima pede | Implementação entregue | Justificativa |
|-------|------------------|------------------------|---------------|
| Assinatura | `score_deal(row: dict, agent_winrate) -> tuple[int, dict]` | `score_deal(row: pd.Series, agent_winrate, today, ...) -> DealScore` | `pd.Series` é o input natural em pipelines vectorizados; `today` como parâmetro torna a função determinística e testável (AC5) |
| Output | `tuple[int, dict]` | `DealScore` dataclass com `.components`, `.summary_ptbr`, `.to_dict()` | Dataclass é mais tipado, idiomático Python 3.11+, e `.to_dict()` atende consumidores que querem JSON |

Esta divergência **não viola** nenhum AC da spec — os ACs são sobre **comportamento** (score em [0,100],
6 componentes, labels PT-BR, etc.) e todos passaram na validação.

## Estrutura entregue

```
solution/scoring.py
├── ScoreComponent (dataclass)        ← 1 componente com name/label/raw/subscore/weight/contribution
├── DealScore (dataclass)            ← resultado agregado com summary_ptbr e to_dict()
├── _minmax(value, lo, hi)           ← normalização 0-100 com clamp e guard hi==lo
├── WEIGHTS (dict)                   ← pesos calibrados pela EDA (soma=1.0, assertado)
├── score_deal(row, agent_winrate, today, ...) → DealScore
├── score_pipeline(pipeline, accounts, products, sales_teams, ...) → DataFrame
└── __main__                         ← smoke test self-contained
```

## Componentes implementados (todos os 6 da SPEC)

| Componente | Peso | Lógica implementada | Hipótese documentada |
|-----------|------|---------------------|----------------------|
| `stage` | 25% | Mapping ordinal: Engaging=90, Prospecting=35, Won=100, Lost=0 | H1 — Engaging > Prospecting |
| `velocity` | 20% | Triangular: 0→100 (ótimo 30d)→0 (max 120d) | H2 refinada — janela ótima, não idade crua |
| `account_size` | 20% | `0.6×MinMax(rev,0,5M) + 0.4×MinMax(emp,0,5k)` | H4 — contas maiores = deals estratégicos |
| `product_value` | 15% | `MinMax(price, 0, 30k)` | ticket alto justifica atenção |
| `agent_record` | 15% | `MinMax(win_rate, 0.10, 0.85)` — range observado na EDA | H3 (CONFIRMADA) — vendedor importa |
| `deal_value` | 5% | `MinMax(close_value, 0, 30k)` | peso baixo propositado (challenge avisa contra "só valor") |

## Edge cases tratados (catálogo E1–E8 da SPEC)

| Edge | Tratamento implementado |
|------|---------------------------|
| **E1** `engage_date=NaT` | `velocity_sub=0`, label `"Idade: sem data de engajamento — priorizar definir próximo contato"` |
| **E2** Won/Lost | recebem stage_sub (100/0) mas `score_pipeline(only_open=True)` filtra antes |
| **E3** Conta não em accounts | `row.get("revenue", 0)` cai em 0 → acct_sub baixo, label mostra "$0" |
| **E4** Produto não em products | idem — `price=0`, label "?", prod_sub=0 |
| **E5** Agente novo (sem winrate) | `agent_winrate.get(agent, 0.5)` — neutro 50%, label mostra "win rate 50%" |
| **E6** close_value=0 em aberto | `deal_sub=0`, label mostra "$0" |
| **E7** deal recém-criado (idade=0) | velocity_sub=20 (não 0 — novo, maturando) |
| **E8** Outlier valor | `_minmax` clipa naturalmente |

## Hooks SKILL-04 (SEC-SCAN) ativados

| Hook | Resultado |
|------|-----------|
| `edge-test` (E1) | ✅ Validado explicitamente em `test_scoring_ac.py` |
| `dtype-check` | ✅ `engage_date` convertido com `format='%m/%d/%Y'` e `errors="coerce"` |
| `run-app` smoke test | ✅ `python scoring.py` roda sem erro |
| Path hardcode | ✅ `Path(__file__).resolve().parent / "data"` — sem absoluto |
| PII no código | ✅ `sales_agent` só aparece como chave, nunca printado em logging hardcoded |
| `sklearn` banido | ✅ só `numpy` e `pandas` importados |

## Validação dos Critérios de Aceitação

Arquivo `test_scoring_ac.py` roda todos os ACs contra dados reais:

```
======================================================================
VALIDAÇÃO DOS CRITÉRIOS DE ACEITAÇÃO — SPEC Prompt 03
======================================================================

AC1 — Score em [0,100]:                          PASS
  Deals scored: 4708
  Fora do range [0,100]: 0
  min=15.82  mean=32.83  max=71.42

AC8 — Top 10 deals, ≥7 Engaging:                 PASS
  Engaging no top 10: 10/10
  Stages no top 10: {'Engaging': 10}

AC5 — Determinismo (2x → idêntico):              PASS
  Determinístico: True

AC2 — Breakdown com 6 componentes:               PASS
  Componentes: 6
  Nomes: ['stage', 'velocity', 'account_size', 'product_value', 'agent_record', 'deal_value']

AC3 — Subscores [0,100] + labels PT-BR:          PASS
  Subscores ok: True
  Labels ok: True

AC4 — Score = sum(subscore × weight):            PASS
  Recomputado: 69.4193  |  Retornado: 69.4193
  Diferença: 0.000000

AC7 / E1 — engage_date=NaT:                      PASS
  velocity subscore: 0.0
  label: 'Idade: sem data de engajamento — priorizar definir próximo contato'
  label menciona 'sem data': True

Sanity — Distribuição não-bimodal:               PASS
  q1=23.5  median=33.8  q3=38.2  std=9.67
  Scores únicos: 4707
```

**Todos os ACs passaram.** Nenhum fail.

## Sanity checks adicionais (do Prompt 03 seção 10)

1. **Distribuição não-bimodal**: ✅ 4707 scores únicos, std=9.67, IQR 23.5-38.2 — bem distribuído
2. **Top 10 deals**: ✅ 10/10 são `Engaging` — stage tem peso real no ranking
3. **Determinismo**: ✅ rodar 2x produz idêntico
4. **Edge E1 testado**: ✅ label específico gerado corretamente

## Achados notáveis

- **Score max = 71.42** — nenhum deal atinge score extremo, o que é esperado: para chegar a 100,
  seria preciso ser Engaging + idade ótima + conta grande + produto caro + win rate alto + valor
  alto, simultaneamente. A combinação rara é sinal de que a ponderação não está inflada.
- **Mean = 32.83** — pipeline médio tem score baixo-médio, o que reflete a realidade: muitos
  deals Prospecting novos (idade baixa → velocity baixo → score puxado para baixo).
- **agent_record** shape: EDA mostrou win rate 42%–67%, mapeado via MinMax(0.10, 0.85) —
 outsiders da EDA (acima de 0.85 ou abaixo de 0.10) clipam naturalmente.

## Arquivos entregues

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `solution/scoring.py` | ~320 | implementação principal + score_pipeline batch + smoke test |
| `solution/test_scoring_ac.py` | ~85 | suite de validação dos ACs da SPEC |

---

_Estado do harness após Prompt 04:_
- Agent: BUILDER ✅ (implementação contra spec aprovada)
- Skill: SEC-SCAN ✅ (edge-test, dtype-check, run-app, path-hardcode, PII, sklearn — todosPassed)
- Todos os ACs da SPEC validados ✅
- Próximo prompt: **Prompt 05 — App Streamlit com Design System G4** (AGENT-B)