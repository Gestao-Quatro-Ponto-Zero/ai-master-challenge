# F1-fix — Report

## Números do passo 2

Gerados por `solution/f1_auditoria_ds2.py` → `solution/outputs/f1_ds2_auditoria.json`, chave `3.5_quase_duplicados`. Todos batem com os valores esperados pelo chat do Projeto.

| Métrica | Valor | Esperado |
|---|---|---|
| `tickets_fora_da_maioria_do_grupo` | 118 | 118 |
| `tickets_em_grupos_tam_2mais` | 3.092 | 3.092 |
| `pct_fora_da_maioria_sobre_tickets_em_grupos` | 3,82% | 3,8% |
| `pct_fora_da_maioria_sobre_base` | 0,25% | ~0,25% |
| `maior_grupo_em_conflito` | `group_id` 11923, 144 tickets: Hardware 112, Storage 18, Miscellaneous 14 | 144 (112/18/14) |
| `grupos_em_conflito_de_tamanho_2` | 41 | 41 |

Os cálculos anteriores (61 grupos e 360 tickets em grupos com conflito, entre outros) não mudaram.

## SHA-256 de `solution/outputs/f1_splits.csv`

- Antes: `37703450a50c406a9c46fe62fa9ecea167b90fa41c4ee0e106d91a6d72865ba0`
- Depois: `37703450a50c406a9c46fe62fa9ecea167b90fa41c4ee0e106d91a6d72865ba0` (inalterado)

## Outras alterações

- `solution/comum.py`: `ENV_PATH = challenge-g4-ai-master/.env`, resolvido via `Path(__file__)`. O `.env` não foi criado e segue no `.gitignore` da submissão.
- `planning/F1-report.md`: corrigidos o item 3.5 e o item de conflito na lista "permitem afirmar"; frase de critério acrescentada ao T5; item dos 30 mil reduzido ao fato, com a origem marcada como não verificada.
- `solution/outputs/f1_ds1_fatos.csv`, linha T5: frase acrescentada ao resultado. A mesma frase entrou no gerador (`solution/f1_auditoria_ds1.py`), para que uma nova execução produza o CSV idêntico. O script não foi rodado de novo.
- `CLAUDE.md` §7: novo bullet **Add** com os dois comandos e a localização da chave em `challenge-g4-ai-master/.env`. A seção não tinha uma instrução de add para trocar, então ela foi acrescentada.

## Desvio: arquivos auxiliares de `planning/F1-revisao/` foram regravados

Rodar `f1_auditoria_ds2.py` (exigido no passo 2) também regrava 4 arquivos auxiliares em `planning/F1-revisao/`: `f1_amostra_idioma.csv`, `f1_amostra_texto.csv`, `f1_conflitos_rotulo.csv` e `f1_pares_fronteira.csv`. Isso contraria o passo 3 ("não toque em planning/F1-revisao/").

- O conteúdo é determinístico (seed 42 e `f1_splits.csv` com o mesmo hash), então deve ser idêntico ao anterior. Isso não foi comparado byte a byte, porque não havia hash prévio.
- `revisao_rotulos.csv`, `revisao_gabarito.csv` e `revisao_pesos.csv` **não** foram tocados (data de modificação ainda 18:54).

## pytest

```
..........                                                               [100%]
10 passed in 0.60s
```

## `git diff --cached --name-only`

```
submissions/gustavo-covaleski/.gitignore
submissions/gustavo-covaleski/process-log/process-log.md
submissions/gustavo-covaleski/requirements.txt
submissions/gustavo-covaleski/solution/comum.py
submissions/gustavo-covaleski/solution/f1_adjudicacao.py
submissions/gustavo-covaleski/solution/f1_auditoria_ds1.py
submissions/gustavo-covaleski/solution/f1_auditoria_ds2.py
submissions/gustavo-covaleski/solution/f1_planilha_revisao.py
submissions/gustavo-covaleski/solution/f1_verificar_dados.py
submissions/gustavo-covaleski/solution/outputs/f1_dados.json
submissions/gustavo-covaleski/solution/outputs/f1_ds1_auditoria.json
submissions/gustavo-covaleski/solution/outputs/f1_ds1_fatos.csv
submissions/gustavo-covaleski/solution/outputs/f1_ds2_auditoria.json
submissions/gustavo-covaleski/solution/outputs/f1_splits.csv
submissions/gustavo-covaleski/solution/tests/test_f1.py
```

Nenhum caminho fora da submissão, nenhum `.venv`, `.env`, `__pycache__` ou `.pytest_cache`, nenhum texto de ticket.

- `f1_dados.json` contém o caminho absoluto de `DATA_DIR` (`C:\Users\gusta\...`), que expõe o nome de usuário do Windows. Não é dado de ticket.
- O git avisou "LF will be replaced by CRLF" (`core.autocrlf`); não houve efeito no conteúdo.

## Commit

- `52e701248dc904a2165178b726258e82d8721cd5`: "F1: auditoria dos dados, grupos de quase-duplicados e holdout congelado". Inclui a linha `Co-Authored-By`. Sem push.
- `docs/`, `process-log/chat-exports/` e `process-log/screenshots/` estão vazios e não entram (o git não rastreia pastas vazias).
- O passo 9 (a "Decisão minha" no process log) foi feito **depois** do commit, na ordem pedida. Por isso `process-log.md` está modificado e fora do commit da F1; entra no próximo.

## Tempo

Das 19:23 às ~19:28, cerca de 5 min (teto: 15).
