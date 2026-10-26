# Bloco 6: revisão, correções e fechamento

## O que o bloco 6 fez
- Duas revisões independentes (subagentes de contexto limpo, notas médias de cerca de 3,6 em 5) em `06_revisao-independente.md`, com triagem do orquestrador.
- Correções de interface, texto e documentos sem tocar no modelo (curva, parâmetros, critério e métrica congelados).
- Correções pós-revisão 2: aviso do Foque com 61+ dias na tela, "<1%" no card, linha do revisor no README. Tabela com antes e depois em `06_revisao-independente.md`.
- Verificação do zero: `data.js`, briefs e snapshots apagados e recriados.

## Checklist da definição de pronto
Todos os comandos com cwd `solution`, `$PY` = Python da `.venv`.

| Item | Comando | Resultado |
|---|---|---|
| pytest | `& $PY -B -m pytest -p no:cacheprovider` | exit 0, 100% (3 linhas de pontos, sem falha) |
| Build do zero | `Remove-Item app\data.js, briefs\*.md, data\processed\snapshot_*.csv`; `& $PY -B -m scorer.build --reference-date 2017-12-31` | exit 0; recriou `data.js` (3,76 MB), 27 briefs + README, 3 CSVs de snapshot |
| `index.html` em `file://` sem erro de console | `& $PY -B tools\check_app.py --prefix final` | exit 0, 24 de 24 PASSOU, "console: zero erros, pageerror e requestfailed" |
| README no template, resumo com até 5 frases | `test_readme` dentro do pytest | passou |
| 5 docs em `docs/` | `Get-ChildItem docs` | SCOPE, DATA_QUALITY, SCORING, MODEL_CARD, DECISIONS (mais o briefing.md) |
| Docs em dia com os dados | `& $PY -B -m scorer.docs --check` | exit 0, todos "sem mudanças" |
| SCORING com tabela contra os 3 baselines em pelo menos 2 cortes | `tests` de documentos (pytest) | passou; tabela no SCORING seção de resultados |
| Process log blocos 0 a 6, screenshots, 2 revisões | `Get-ChildItem process-log` | `00_bloco-0` a `06_bloco-6`, `06_revisao-independente.md` (revisões 1 e 2), `screenshots/final_*` (10 PNG) |
| Nada fora da pasta | `& $PY "$PM\tools\gitw.py" status` | "FORA da pasta da submissão: nada" |

## Pendências humanas
- Revisar o rascunho "O que eu adicionei" (`[RASCUNHO — Rafael revisar]`).
- Ativar o GitHub Pages e trocar o link (`[ativar — Rafael]`).
- Preencher a data (`[preencher ao abrir o PR]`).
- Decidir sobre o gradiente de idade dentro do platô do Foque. O sinal troca entre cortes (-17,4 / +19,2 / +21,3 / -41,3 pp), então adotá-lo seria decisão pós-hoc; se for adotada, registrar em DECISIONS e SCORING com novo backtest (ver a tabela de comparação em `06_revisao-independente.md`).

## Nota do orquestrador (Claude Opus 5.5): verificação final, de fato do zero

O executor fez o build do zero antes das últimas correções do README e do `app.js`. Por isso o orquestrador repetiu a verificação depois de tudo pronto, com cwd `solution/`, nesta ordem:

1. Apagou `app/data.js`, `briefs/*.md` e `data/processed/snapshot_*.csv`. Depois disso, `Test-Path app/data.js` deu False.
2. `python -B -m scorer.build --reference-date 2017-12-31`: exit 0.
   - Recriou `data.js` com 3.939.482 bytes (3,76 MB), 28 briefs (27 vendedores e o índice) e 3 snapshots.
   - Hoje: Foque 126, Reative 172, Limpe 1.291, Qualifique 500.
3. `python -B -m pytest -p no:cacheprovider`: 199 passed em 71 s.
4. `python -B -m scorer.docs --check`: exit 0.
5. `python -B tools/check_app.py --prefix final`: 24 passaram, 0 falharam, 0 puladas. RESULTADO: PASSOU (inclui zero erros de console em `file://`).
6. Nenhum `__pycache__` na submissão. `gitw.py status`: "FORA da pasta da submissão: nada".