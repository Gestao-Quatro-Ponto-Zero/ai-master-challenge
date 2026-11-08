# model-lab — validação do score (ambiente isolado)

Laboratório separado do backend para responder: **o score continua condizente com a realidade depois de cada retreino?**
Não altera código, estrutura nem dados do backend:

- importa `legacy_backend/src` (cópia congelada do código do modelo **antigo**, o campeão) só para leitura; o backend de produção já foi migrado para o modelo de 30 dias, então para validar o modelo atual use `G4_LAB_BACKEND=../backend` (e ignore o desafiante, que passa a ser igual ao campeão);
- copia os CSVs para um diretório temporário; o retreino grava artefatos e banco SQLite nesse diretório;
- confere por hash, no fim, que os CSVs de origem não mudaram.

## Rodar
```bash
cd model-lab
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # ambiente próprio, separado do backend
.venv/bin/python run_lab.py                      # backtest real + 7 dias simulados, relatório em out/<data-hora>/
.venv/bin/python run_lab.py --days 3 --skip-backtest
.venv/bin/python -m pytest -q                    # testes de realidade (~6 min com 7 dias)
G4_LAB_DAYS=2 .venv/bin/python -m pytest -q -m "not slow"
```
Variáveis: `G4_LAB_BACKEND` (pasta com `src/`, padrão `legacy_backend`), `G4_LAB_DATA` (CSVs, padrão `../backend/data`),
`G4_LAB_DAYS` (dias simulados nos testes, padrão 7). Para testar um lote novo de dados, aponte `G4_LAB_DATA` para ele.

## O que roda
| Etapa | O que faz |
|---|---|
| Backtest real (`model_lab/backtest_real.py`) | 13 datas de 2017; em cada uma, treina só com o passado e mede o que aconteceu nos 30 dias seguintes |
| Mocks (`model_lab/mockgen.py`) | gera os eventos de cada dia (leads novos, Prospecting → Engaging, ganhos e perdas) no **mesmo formato** dos CSVs; parâmetros estimados dos dados reais |
| Simulação (`model_lab/simulate.py`) | 7 dias: aplica o mock, roda o `run_training` de produção (com o portão de qualidade), treina o desafiante e compara o score com a receita esperada **verdadeira** do mundo mock |
| Veredito (`model_lab/verdict.py`) | critérios de aceite em números (ajustáveis) |

## Critérios de aceite (`model_lab/verdict.py`)
- correlação de Spearman entre o score e a receita real em 30 dias ≥ 0,30;
- no máximo 10% dos deals com score ≥ 80 podem estar parados (idade > P90 do ciclo);
- PSI do score entre dias ≤ 0,25 (estabilidade);
- regras de negócio: zumbi sem score, score entre 0 e 100, Prospecting sem score;
- desafiante "muito melhor" = ≥ 10% a mais de receita capturada no top 20% do backtest real e correlação maior.

`run_lab.py` sai com código 1 quando o score atual não passa, para dar para usar em CI/cron antes de promover.

## Suposições do mock (explícitas)
O real não tem nenhum deal que fechou depois de 138 dias. Para os zumbis o mock supõe 0,3% de chance de fechar por dia e
15% de ganhar quando fecha (`WorldParams`). Isso simula a limpeza de carteira e é o que expõe a fragilidade do limiar "máximo histórico".

## Arquivos
- `notebooks/novo_modelo_receita_30d.ipynb` — implementação de referência do modelo novo, com backtest e checklist para o backend
- `docs/PLANO_NOVO_MODELO.md` — diagnóstico, resultados, parecer do vendedor sênior e plano de implementação
- `tests/test_score_reality.py` — os critérios acima como testes pytest (hoje 1 falha esperada: `test_score_alto_nao_e_deal_parado`, o achado da análise)
- `out/20261107-144716/` — relatório da execução desta análise
