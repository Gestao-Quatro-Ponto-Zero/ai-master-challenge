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

---

## 09/11 — #5 QA: etapa 1 (baseline) e etapa 2 (checklist)

**Entregue:** `solution/qa/baseline.md`, que reconstrói a entrega típica de uma IA só com o brief e traz 12 erros dela medidos nos dados e 20 armadilhas para marcar, e `solution/qa/checklist.md`, o checklist de entrega.

**Conferência:** a #1 recalculou os números de forma independente, com um script próprio sobre `data/raw/`, data de referência 2017-12-31 e o typo de setor e o nome do produto corrigidos.

| Afirmação da #5 | Recalculado pela #1 | Situação |
|---|---|---|
| 8.800 deals; 4.238 Won / 2.473 Lost / 1.589 Engaging / 500 Prospecting; win rate 63,2% | Igual | ✅ |
| Diferença de win rate entre o melhor e o pior grupo: produto 4,8 p.p. | 4,8 (60,0–64,8) | ✅ |
| Setor 3,6 p.p. | 3,67 → **3,7** | ⚠️ truncado em vez de arredondado |
| Manager 2,3 p.p. | 2,3 | ✅ |
| Região 1,3 p.p. | 1,38 → **1,4** | ⚠️ truncado em vez de arredondado |
| Win rate por quartil de funcionários 64,1 / 61,4 / 63,9 / 63,2 | Igual | ✅ |
| Abertos sem conta: 1.088/1.589 Engaging, 337/500 Prospecting (68%) | Igual (68,2%) | ✅ |
| Correlação 1º × 2º semestre: conta −0,08; vendedor 0,36; win rate do vendedor 55,0–70,4%, mínimo de 79 deals | Igual | ✅ |
| Duração mediana: Lost 14 dias, Won 57; ciclo máximo 138 | Igual | ✅ |
| Chance de ganhar, para deals que já duraram d dias: 63 / 69 / 71 / 76% (d = 0, 14, 90, 120) | 63,2 / 68,6 / 71,3 com "≥ d"; em 120 dá 75,1 com "≥" e 75,6 com "> 120" | ⚠️ critério de corte não declarado; com "≥", o certo é 75% |
| 1.291/1.589 Engaging acima de 138 dias (mediana 165) | Igual | ✅ |
| `close_value` ÷ preço de tabela nos Won: mediana 1,00 (0,66–1,34) | Mediana 1,00, mín–máx 0,66–1,34 | ✅ |
| Fim de trimestre fecha 78–83% Won contra 49–57% nos outros meses | 78,5–82,8 contra 48,6–56,8 | ✅ |
| 5 vendedores sem deals | Os mesmos 5 nomes | ✅ |

**Problemas encontrados:**
1. **Bloqueante:** o item H1 do `checklist.md` cita nominalmente as empresas do candidato que não podem aparecer na entrega, justamente na regra que proíbe citá-las. O commit fica retido, porque o histórico do git vai junto no PR.
2. Arredondamento de setor (3,7) e região (1,4), e o critério de "depois de d dias" a declarar. Não muda nenhuma conclusão.

**Encaminhamento:** devolvido à #5 para corrigir os três pontos. O commit de `solution/qa/` sai depois da correção.

**Retorno da #5 (conferido):**
1. H1 reescrito de forma genérica. A busca por nomes de empresas, projetos e e-mails nos dois arquivos deu zero ocorrências, e os dois estão em LF. ✅
2. Setor 3,7 p.p. e região 1,4 p.p., com nota de que a diferença é calculada antes de arredondar. ✅
3. **A #1 errou neste ponto.** A #5 já usava o mesmo corte estrito (ciclo > d) nos quatro pontos, então o 76% (75,6) estava coerente. A #1 tinha comparado com "≥ d". A #5 declarou o corte e mostrou as duas versões: > d = 63,2 / 68,7 / 71,1 / 75,6%; ≥ d = 63,2 / 68,6 / 71,3 / 75,1%. A #1 conferiu: o ciclo mínimo é 1 dia, por isso d = 0 dá o mesmo nas duas. ✅

**Resultado:** `solution/qa/` aprovado e commitado.
