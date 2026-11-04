# F2 — Report (Diagnóstico enxuto + instrumentação)

Caminhos relativos à submissão (`ai-master-challenge/submissions/gustavo-covaleski/`). Os scripts rodam com `.venv/Scripts/python`.

## 1. O que foi feito

1. **Passo 0.1:** `f1_verificar_dados.py` passou a gravar `data_dir` como `"$DATA_DIR (padrão ../../../data relativo à submissão)"`, sem caminho absoluto. Rodei de novo só esse script. Os demais campos de `f1_dados.json` são idênticos aos anteriores (comparação programática: `True`).
2. **Passo 0.2:** `ler_csv_excel` (`solution/comum.py`) detecta o separador `;` ou `,` pela linha de cabeçalho. Tenta as codificações `utf-8-sig`, `utf-8` e `cp1252`, nessa ordem. A escrita não mudou. Há 3 testes com arquivos sintéticos em `tmp_path`.
3. **Passo 1:** `solution/f2_diagnostico.py` cobre o MDE, as piores combinações e o custo de triagem. As saídas são `f2_mde.csv`, `f2_premissas.json`, `f2_diagnostico.json` e `f2_custo_triagem.csv`. Os testes ficam em `solution/tests/test_f2.py`.
4. **Passos 2 e 3:** `docs/instrumentacao.md` e `docs/diagnostico.md` (5 linhas).
5. `pytest solution/tests -q` → **16 passed**.

## 2. Resultados

| Número | Valor | Script → arquivo |
|---|---|---|
| Base da duração (Closed, duração > 0) | n = 1.402 | `f2_diagnostico.py` → `f2_diagnostico.json` |
| sd da duração (premissa de variância; variável inválida, T3) | 5,59 h (5,5888) | → `f2_premissas.json` |
| z₁₋α/₂ + z_poder (α = 0,05, poder = 0,8) | 2,8016 | → `f2_premissas.json` |
| n por grupo para MDE = 2 h | 123 | → `f2_mde.csv` |
| MDE atual entre os 2 menores grupos de prioridade (Low 332 × Medium 341) | 1,21 h | → `f2_mde.csv` |
| MDE atual entre os 2 menores grupos de canal (Phone 327 × Social media 348) | 1,21 h | → `f2_mde.csv` |
| MDE atual entre canal × prioridade (69 × 69) | 2,67 h | → `f2_mde.csv` |
| MDE atual entre as 2 menores combinações canal × prioridade × tipo com n ≥ 20 (20 × 20) | 4,96 h | → `f2_mde.csv` |
| Semanas até MDE de 2 h no menor grupo: prioridade (Low, 24,36%) | 0,9 | → `f2_mde.csv` |
| Semanas: canal (Chat, 24,48%; fora do pedido da spec, ver §4) | 0,9 | → `f2_mde.csv` |
| Semanas: canal × prioridade (Phone \| Low, 5,89%) | 3,6 | → `f2_mde.csv` |
| Semanas: canal × prioridade × tipo (Chat \| Critical \| Product inquiry, 1,00%) | 21,2 | → `f2_mde.csv` |
| 1.2: combinações com n ≥ 20 | 29 de 80 | → `f2_diagnostico.json` |
| 1.2: maior diferença de média (Chat \| High \| Refund request, n 22 × Chat \| Critical \| Billing inquiry, n 20) | 5,97 h | → `f2_diagnostico.json`, `f2_mde.csv` |
| 1.2: MDE para esses n | 4,84 h | → idem |
| Custo de triagem, cenário A, base (3 min, R$ 35/h, 30 mil tickets/ano) | R$ 52.500/ano | → `f2_custo_triagem.csv` |
| Custo de triagem, cenário A, faixa da grade | R$ 25.000 a R$ 100.000/ano | → `f2_custo_triagem.csv` |
| Cenário B | economia de triagem = 0; ganho não calculável | → `f2_diagnostico.json` |
| `f1_splits.csv` SHA-256 | `37703450…865ba0` (inalterado) | — |
| `planning/F1-revisao/` | os 10 arquivos com o mesmo SHA-256 de antes da fase | — |

Todas as premissas estão rotuladas como `premissa (editável), não dado` nos arquivos. Toda saída que usa a duração traz o rótulo `variável sintética e inválida (T3); usada só como premissa de variância`.

## 3. O que contraria a hipótese ou a expectativa

- **1.2:** a maior diferença observada (5,97 h) **supera** o MDE para os mesmos n (4,84 h). Lida isoladamente, sugeriria um gargalo detectável. Três motivos impedem essa leitura:
  - é o máximo entre 29 combinações (406 pares possíveis), então está inflado por comparações múltiplas;
  - nenhum teste foi feito, porque o F0 proíbe;
  - a variável é inválida (T3).
  O texto em `docs/diagnostico.md` declara isso, mas o número pode ser mal lido por quem lê com pressa. Para decidir no portão: manter a linha ou só citar o MDE.
- **O MDE atual por prioridade (1,21 h) já fica abaixo da meta de 2 h** com os n do DS1. A barreira para diagnosticar por prioridade não é o tamanho da amostra, e sim a validade da variável de tempo. Reforça a instrumentação, mas muda o argumento: não é "faltam dados", é "faltam dados válidos".
- **Só 29 das 80 combinações** canal × prioridade × tipo têm n ≥ 20 na base de duração.

## 4. Desvios da spec

- **Participação para as semanas:** usei a participação observada no **DS1 inteiro** (8.469 tickets, todos os status), já que o volume de 30 mil se refere a todos os tickets. Os `n_atual` e os MDE atuais usam a base de duração (1.402). Por isso, o "menor grupo" para as semanas (ex.: canal = Chat) pode diferir dos 2 menores grupos usados no MDE atual (Phone × Social media). As duas colunas estão separadas no CSV.
- **Linha extra "canal"** em `f2_mde.csv`. A spec pede o MDE atual por canal, mas as semanas só para 3 granularidades. A linha também traz as semanas (0,9), por ter o mesmo formato.
- **Teste da planilha da F1 alterado** (`test_f1.py::test_planilha_revisao`). Exigia `meu_rotulo` vazio, e o Gustavo já preencheu a planilha, então o teste falhou. Agora `rotulo_original` continua obrigatoriamente vazio, e `meu_rotulo` deve estar todo vazio ou todo dentro das 8 categorias. A planilha só foi lida, não modificada.
- **Teste extra** `test_n_para_mde_inverte_mde`: confere que `n_para_mde` devolve o menor n que atinge o MDE.

## 5. Erros e correções durante a execução

- O 1º teste sintético `;` + `utf-8-sig` falhou por bug do teste: o BOM foi codificado em cada linha, e não só no início do arquivo. Corrigido codificando o conteúdo inteiro de uma vez.
- `test_planilha_revisao` falhou porque a planilha já estava preenchida (ver §4).

## 6. Pendências e decisões que dependem do Gustavo

1. A linha 1 do diagnóstico mantém "5,97 h vs MDE 4,84 h"? Ver §3.
2. Participação usada nas semanas: DS1 inteiro (escolha atual) ou só a base de duração?
3. Commit da F2 com o comando de add do `CLAUDE.md` §7. Arquivos pendentes:
   - modificados: `process-log.md`, `comum.py`, `f1_verificar_dados.py`, `f1_dados.json`, `test_f1.py`;
   - novos: `f2_diagnostico.py`, `test_f2.py`, `f2_*` e `docs/*.md`.
4. A planilha da revisão já foi lida por `ler_csv_excel`, mas `f1_adjudicacao.py preparar` não foi rodado (spec).

## 7. Tempo gasto × orçado

- Orçado: 30 min (teto de 36).
- O relógio do sistema marcou 21:12 no início e 21:15 nas checagens finais. Esse intervalo não é confiável como medida, porque a sessão anterior mostrou saltos parecidos. A estimativa do trabalho efetivo é de 10 a 15 min, dentro do orçado.
