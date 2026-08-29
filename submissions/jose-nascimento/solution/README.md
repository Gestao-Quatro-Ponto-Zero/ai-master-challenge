# Solução — Pipeline reprodutível em um comando (Iteração 06)

Toda a análise do Challenge 001 (Diagnóstico de Churn · RavenStack) — Iterações 01–05 —
roda do zero com **um comando**, offline (os 5 CSVs são commitados em `data/raw/`),
deterministicamente (outputs byte-idênticos entre execuções) e sem Docker/CI.

- **Um comando:** `./run.sh` (ou `make all` — mesma fonte única).
- **Verificação:** `make verify` (ou `python3 solution/src/06_verify_pipeline.py`;
  a invocação direta NÃO gera `__pycache__` — o verificador desabilita bytecode).
- **Regeneração de derivados:** `make clean-derived` (nunca toca `data/raw/` nem `process-log/`).

---

## 1. Requisitos

| Item | Exigência | Testado em |
|---|---|---|
| Python | **>= 3.11** | 3.12.3 (Linux, aarch64) |
| pandas | `==3.0.5` (pin exato) | 3.0.5 |
| matplotlib | `==3.11.1` (pin exato) | 3.11.1 |
| Sistema | Linux ou macOS; bash; `make` | Linux (aarch64) |

- **Sem rede:** nenhum script baixa nada; os dados já estão commitados.
- **Sem Docker/CI/notebook/dashboard.**
- Pins exatos garantem determinismo byte-a-byte entre máquinas (ver
  `process-log/decisions/iteration-06-reproducibility-decisions.md`, D1).

## 2. Setup (Linux/macOS)

```bash
# (opcional) ambiente isolado
python3 -m venv .venv
source .venv/bin/activate

# dependências documentadas
pip install -r requirements.txt
```

`requirements.txt` é mínimo: apenas `pandas` e `matplotlib` (inspeção de imports
dos scripts 01–05; `duckdb`/`seaborn`/`jupyterlab`/`numpy` explícito foram removidos).

## 3. Execução — um comando

```bash
./run.sh          # ou: make all
```

**Override de interpretador:** o pipeline e os targets de debug honram
`PYTHON ?= python3` — use `PYTHON=/caminho/python3 ./run.sh` ou
`make PYTHON=/caminho/python3 verify` (mesma convenção nos dois).

O que acontece (em ordem):

1. **Preflight** — `python3` presente e >= 3.11; `pandas`/`matplotlib` importáveis;
   os 5 raw CSVs commitados presentes. Falha útil (exit != 0) se algo faltar.
2. **Estágios 01→05** — `01_ingest_audit.py`, `02_reconcile_churn.py`,
   `03_root_cause.py`, `04_lifecycle_watchlist.py`, `05_actions_impact.py`.
   Cada estágio propaga exit code; falha tratada (schema ausente ou valor
   categórico/booleano inválido) regrava o relatório com FAILs estruturados e o
   pipeline para — sem traceback. Falha inesperada (bug real) mostra o
   diagnóstico do estágio (possivelmente com traceback) e o relatório pode ficar
   desatualizado: corrija a causa e reexecute.
3. **Verificação final** — `06_verify_pipeline.py` (checks A–E + gate de ids
   únicos; contagem exata impressa em runtime); qualquer FAIL torna o `run.sh`
   falho (exit 1).

## 4. Outputs por estágio

| Estágio | Artefatos gerados (determinísticos) |
|---|---|
| 01 — auditoria | `solution/evidence/01_audit_report.md` |
| 02 — reconciliação/contrato | `solution/data/processed/account_month.csv` (+ `README.md`), `solution/docs/analytical-contract.md`, `solution/evidence/02_consistency_report.md` |
| 03 — causa raiz/coortes | `solution/evidence/03_root_cause_report.md`, tabelas `t01–t10` (13), gráficos `a/b/c/d` (4 PNGs) |
| 04 — jornada/watchlist | `solution/evidence/04_lifecycle_watchlist_report.md`, tabelas `t11–t17` (9), gráficos `It04_c/It04_d` (2 PNGs) |
| 05 — ações/impacto | `solution/evidence/05_action_plan.md`, tabelas `t18–t21` (4) |
| 06 — verificação | nenhum output (read-only); exit 0/1 |

Total: **5 evidence reports, 26 tabelas CSV, 6 PNGs, 1 base account-month, 1 contrato**
(40 artefatos derivados regeneráveis; + 5 raw CSVs commitados = 45 outputs do
pipeline; este `README.md` é estático e não é regenerado).

## 5. Estrutura

```
submissions/jose-nascimento/
├── run.sh                      # pipeline em um comando (executável)
├── Makefile                    # all == run.sh; verify; stages; clean-derived
├── requirements.txt            # pandas==3.0.5, matplotlib==3.11.1
├── solution/
│   ├── README.md               # este arquivo
│   ├── data/raw/               # 5 CSVs commitados (MIT; ver README.md local)
│   ├── data/processed/         # account_month.csv (regenerado por 02)
│   ├── docs/analytical-contract.md
│   ├── evidence/               # reports 01–05 (regenerados)
│   ├── out/tables/             # t01–t21 (regenerados por 03–05)
│   ├── out/charts/             # 6 PNGs (regenerados por 03–04)
│   └── src/                    # scripts 01–06
└── process-log/                # plano, checklist, prompts, reports, decisions (não regenerado)
```

## 6. Tempo e memória (medidos nesta máquina; aproximação honesta, não benchmark)

Pipeline completo: **~65–75 s** de relógio (faixa observada em execuções
repetidas; varia com a máquina/carga — rótulo de aproximação, não benchmark).

| Estágio | Tempo (aprox.) | Pico de memória (ru_maxrss, aprox.) |
|---|---|---|
| 01_ingest_audit | ~1 s | ~125 MB |
| 02_reconcile_churn | ~50 s | ~134 MB |
| 03_root_cause | ~6 s | ~176 MB |
| 04_lifecycle_watchlist | ~4 s | ~167 MB |
| 05_actions_impact | ~1–2 s | ~126 MB |
| 06_verify_pipeline | ~1 s | — |

> Memória medida via `resource.getrusage(RUSAGE_CHILDREN).ru_maxrss` (pico por
> estágio, aproximação; não é benchmark universal). Tempo em segundos de relógio
> (`SECONDS`); varia com a máquina.

## 7. Verificação (`make verify`)

`06_verify_pipeline.py` (stdlib + pandas; sem reimplementar análises) verifica:

- **Manifesto** — 5 raw CSVs exatos, scripts 01–06, evidence 01–05, account_month,
  26 tabelas, exatamente 6 PNGs; 4 PNGs pruned (gate It04) ausentes;
- **Parseabilidade** — CSVs legíveis com cabeçalho e linhas; Markdown presente;
  PNGs com magic bytes e tamanho > 0;
- **Consistência com contratos commitados** — contagens e MD5 dos raw CSVs ==
  `data/raw/README.md`; linhas+MD5 do account_month == `data/processed/README.md`;
  invariantes estruturais do painel (unicidade account×mês, janela derivada dos
  dados, mês do signup como piso, domínios) — nenhum número de dados hardcoded;
  reports sem gate FAIL e com gate PASS; relações estruturais entre tabelas
  (t16 ⊆ t11, t21 ⊆ t16, t14b ⊆ t14, t19/t20 ⊆ t18);
- **Higiene** — zero `.db/.duckdb/.sqlite/.pyc` e venv/cache em `solution/`;
  zero paths pessoais/segredos; zero imports de rede; `requirements.txt` mínimo
  (extras são informativos, não bloqueiam); `run.sh` executável e sem CRLF;
  ids de check únicos (gate D7);
- **Sanidade** — `compile()` e import de todos os scripts.

Exit 0 = tudo OK; exit 1 = diagnóstico estruturado por check (sem traceback).
Nota: `make verify` com falha retorna **exit 2** (o GNU make encapsula o exit 1
do script — convenção do make); o script direto retorna exit 1.

## 8. `make clean-derived`

Remove **somente** os artefatos derivados regeneráveis (lista explícita no
Makefile: evidence 01–05, account_month + README processado, contrato, 26
tabelas, 6 PNGs — **40 arquivos**; o target imprime a contagem derivada de
`$(words $(DERIVED))`). **Nunca** apaga `data/raw/` (dados commitados) nem
`process-log/`. Regeneração: `./run.sh` (ou `make all`).

## 9. Troubleshooting

| Sintoma | Causa provável | Solução |
|---|---|---|
| `python3 não encontrado` / `Python >= 3.11 exigido` | interpretador ausente/antigo | instalar Python >= 3.11 |
| `dependências Python ausentes` | `pip install` não executado | `pip install -r requirements.txt` |
| `dado bruto ausente ou vazio` | `data/raw/` incompleto | restaurar os 5 CSVs commitados (não há download) |
| estágio falha com `checks: N PASS / M FAIL` | dado/schema alterado ou valor categórico/booleano inválido (ex.: `churn_flag=TruX`) | ler o relatório do estágio (regravado com FAILs estruturados "não executado (schema/validação)"); restaurar os arquivos originais |
| `make verify` com FAILs | outputs derivados ausentes/alterados | `./run.sh` regenera tudo byte-a-byte |
| `make verify` retorna exit 2 | GNU make encapsula o exit 1 do script (convenção) | comportamento esperado; script direto retorna exit 1 |
| Warnings no stderr de pandas (`numexpr`/`bottleneck` abaixo do mínimo) e matplotlib (`Unable to import Axes3D`) | dependências **opcionais** antigas/ausentes do ambiente (site-packages) | benignos: não afetam outputs nem determinismo; não são suprimidos (nenhum warning analítico é escondido) |
| outputs mudaram após trocar versões | pin mudado | pins exatos em `requirements.txt`; investigue o diff antes de aceitar (não normalize silenciosamente) |

## 10. Definições e lentes (contrato analítico)

Resumo — detalhe completo em `solution/docs/analytical-contract.md`:

- **Três fontes de "churn" divergem** (flag de conta 110 / assinaturas 312 / eventos 352)
  e **não** são comparáveis entre si; cada pergunta usa UMA lente declarada.
- **Lente C (eventos)** — diagnóstico/causa raiz (`churn_events`).
- **Lente de receita — R1 (gross ending MRR)** e **R2 (net account-state loss)**;
  nunca misturar na mesma fórmula (decisão D9).
- **Grão-mestre:** account × mês (`account_month.csv`; 1 linha por conta×mês;
  janela do mês do signup até 2024-12; estado no FIM do mês).
- **Regra do winner:** não-trial, maior MRR, `start_date` mais recente, id lexicográfico.
- **Anti-leakage:** features de risco usam apenas informação até o fim do mês índice;
  desfechos (`churn_event_in_month`, `status`, `mrr_ended_in_month`) nunca são
  features do próprio mês.
- **Evidência sugestiva:** CSAT/reason/feedback nunca são prova causal.

## 11. Dados inclusos e licença

- Os 5 CSVs (`ravenstack_*.csv`) estão **commitados** em `solution/data/raw/`
  (cópia byte-for-byte da origem; MD5 em `data/raw/README.md`) para execução
  **offline** do pipeline — nenhum download em runtime.
- Dataset: [SaaS Subscription & Churn Analytics](https://www.kaggle.com/datasets/rivalytics/saas-subscription-and-churn-analytics-dataset)
  (Kaggle, autor rivalytics), **licença MIT** — conforme o README oficial do
  challenge (`challenges/data-001-churn/README.md`).