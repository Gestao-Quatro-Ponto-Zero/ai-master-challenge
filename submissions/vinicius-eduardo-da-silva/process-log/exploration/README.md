# Scripts de exploração

Evidência de cada etapa, na ordem em que foram usados. Não fazem parte da ferramenta.

| Script | Pergunta | Argumentos |
|---|---|---|
| `audit.py` | Onde os dados enganam? | dados |
| `signals.py` | Quais sinais preveem o resultado? Requer `scikit-learn` | dados |
| `first_replay.py` | A priorização funciona em segundas passadas? | dados |
| `variant_test.py` | Quais critérios entram no score? Roda apenas no commit `4a93295`, antes da troca de mês por semana | dados, `solution/scoring` |
| `rep_coverage.py` | Por que só 17 vendedores têm deals vivos? | dados, `solution/scoring` |
| `quarter_start_check.py` | As chances estão infladas no início do trimestre? | dados, `solution/scoring` |
| `final_audit.py` | O resultado principal sobrevive a um ataque? | dados, `solution/scoring` |

Exemplo, a partir da pasta da submissão:

```bash
python process-log/exploration/final_audit.py solution/data solution/scoring
```
