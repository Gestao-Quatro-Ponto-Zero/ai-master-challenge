# Auditoria das sessões — Challenge 003

A sessão #1 (orquestração) confere cada entrega das outras sessões antes do commit. Registro do que foi entregue, do que foi conferido e do que estava errado.

| Sessão | Papel | Pasta |
|---|---|---|
| #2 | Dados | `solution/data/`, `solution/analysis/` |
| #3 | Score | `solution/scoring/`, `solution/data/scored/` |
| #4 | App | `solution/app/` |
| #5 | QA e baseline | `solution/qa/` |

---

## 09/11 ~21:50 — Estado encontrado quando a #1 assumiu

Até então, a #1 só tinha lido o repositório e os arquivos de contexto. Não baixou nem analisou dados, então não havia nada a passar para a #2.

Ao assumir, a pasta já tinha trabalho das outras sessões, ainda sem auditoria e sem commit:

| Arquivo | Sessão provável | Situação |
|---|---|---|
| `solution/data/raw/*.csv` (5 arquivos, incluindo `metadata.csv`) | #2 | Baixados do Kaggle; aguardando o aviso de etapa da #2 |
| `solution/data/clean/*` + `solution/data/clean.py` + `cleaning_report.json` | #2 | Em andamento (gravados entre 21:48 e 21:49) |
| `solution/qa/baseline.md` | #5 | Em andamento |
| `solution/app/index.html` + `app/sample/` | #4 | Em andamento, com amostra no formato do contrato |
| `solution/analysis/`, `solution/scoring/`, `solution/data/scored/` | #2, #3 | Vazios |

**O que estava faltando:**
- `decisoes.md` estava em branco. As decisões da Etapa 0 só foram registradas agora (linhas 1–9), a partir da narrativa da preparação.
- Nada versionado. O `.gitignore` oficial ignora `submissions/`, então o git não via nenhum desses arquivos.

**Decisões técnicas já tomadas pela #2 que ainda dependem do Leandro** (aparecem no `cleaning_report.json` e serão levadas a ele com a entrega da #2):
- Data de referência fixa em 2017-12-31, a última `close_date` do arquivo.
- Correção de nomes: `GTXPro` virou `GTX Pro` (1.480 deals) e o setor `technolgy` foi corrigido (12 contas).
- Faixas de porte por tercis de receita e de funcionários.
