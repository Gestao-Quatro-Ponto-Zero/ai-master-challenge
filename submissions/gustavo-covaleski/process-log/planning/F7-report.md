# F7 — Report (Comunicação)

Caminhos relativos à submissão (`ai-master-challenge/submissions/gustavo-covaleski/`).

**Antes da F7:** a F6 foi commitada em `c17dc5cfb6b5676d94b4ff918a0eafb778e50291`. O commit tem 8 arquivos, todos dentro da submissão, e passou nas mesmas checagens da F5: caminho, `.venv`, `.env`, `runtime`, `modelo_cache`, cache, `planning`, `findstr sk-ant`, valor da chave, nome e e-mail do DS1 e texto de ticket. A "Decisão minha" da F6 entrou antes do commit.

## 1. O que foi feito

1. **Passo 0:** `f5_injecao.py --dano-ampliado` (função nova `dano_ampliado`, mesmos 5 ataques, só clássico). Universo: os 1.242 tickets do holdout por grupo na faixa "IA decide", o que dá 6.210 pares. Gravado em `f5_injecao.json`, chave `dano_ampliado`.
2. **Passo 1:** `docs/memo-diretor.md`. Tem 376 palavras no total (349 sem a lista de fontes), e cada número leva uma nota com o arquivo de origem.
3. **Passo 2:** `README.md` no template do G4, nas seções e na ordem do template, com uma tabela de 12 achados, cada um com arquivo.
4. **Passo 3:**
   - `process-log.md` recebeu a linha da F7 ("Decisão minha" vazia), a tabela de tempo por fase e a contagem de iterações;
   - 14 specs e reports (F1 a F7, sem este report) foram copiados para `process-log/planning/` depois de uma checagem automática;
   - este `F7-report.md` foi copiado no fim, com a mesma checagem.
5. **Passo 4:** checagens finais (§2).

## 2. Resultados

| Item | Valor | Origem |
|---|---|---|
| Dano silencioso (par continua em "IA decide" com rótulo trocado) | **0 de 6.210**; IC Wilson 95% de 0 a **0,062%** | `f5_injecao.py --dano-ampliado` → `f5_injecao.json` |
| Ataque atinge o alvo e continua em "IA decide" | **0 de 6.210**; limite superior 0,062% | idem |
| Pares que saem de "IA decide" por causa do ataque | 898 de 6.210 (vão para humano ou sugestão) | idem |
| Palavras do memo | 376 (349 sem as fontes) | `wc -w` |
| `pytest solution/tests -q` | 54 passed | — |
| Links relativos do README | 19 links; todos existem (inclusive `process-log/planning/`, criado no passo 3) | checagem em Python |
| Arquivos citados no memo | todos existem | idem |
| `f1_splits.csv` | SHA-256 `37703450…865ba0` (inalterado) | — |
| Checagem de texto de ticket e dado pessoal | 0 sequências de 8 palavras do DS2 e 0 nome ou e-mail do DS1 nos 15 arquivos de `planning/F*-{spec,report}.md`; todos copiados | `checar_planning.py` (script temporário, fora do repositório) |
| Controle positivo da checagem | `docs/politica.md` acusa 133 sequências de 8 palavras do DS2 (como esperado, pelos trechos aprovados) | idem |

## 3. O que contraria a hipótese ou a expectativa

- **Dano zero, mas com efeito colateral não previsto:** 898 dos 6.210 pares (14,5%) **saem** de "IA decide" quando atacados. O ataque reduz a confiança e o ticket vai para um humano. Não há dano silencioso, mas há custo operacional: um atacante pode aumentar a carga humana. O memo e o README não dizem isso. Ver §6.
- **O tempo real não fecha com as estimativas.** A soma das estimativas do Claude Code mais os tempos medidos pelo Gustavo dá ~337 min, abaixo dos 360 orçados. A projeção do Gustavo era ~465 min. A diferença vem do tempo de planejamento e revisão no chat, que o Claude Code não mede. Por isso, o process log usa a projeção do Gustavo como referência e deixa `[GUSTAVO: …]` para o valor final.

## 4. Desvios da spec

- **Total de tempo:** não fechei um número final de tempo nem de estouro, porque F4–F7 não têm tempo medido pelo Gustavo. A tabela mostra a soma (~337) com uma ressalva, e a projeção do Gustavo (465 − 360 = ~105 min) como referência, rotulada como projeção.
- **"Revisor externo concorda 47%":** no memo, a fonte citada é `f3_h2.json` (`gustavo_x_original` = 46,67%), além da planilha adjudicada, porque o número está calculado no JSON.
- **Arredondamentos no memo:** 12,98% → 13,0%; 98,87% → 98,9%; 85,07% → 85,1%; R$ 12.982,13 → R$ 13,0 mil. Os valores exatos estão no README e nos arquivos.
- **README:** tem a seção "Como rodar" depois de "Evidências" (o template não tem essa seção, e a spec a pede). A ordem das seções do template foi mantida.
- **F0-escopo.md não foi copiado** para `process-log/planning/`: a spec pede `F*-spec.md` e `F*-report.md`, e o escopo não segue esse padrão de nome.

## 5. Erros e correções durante a execução

- No process log, escrevi primeiro "o estouro é de ~105 min" como se fosse medido. Corrigi para "projeção do Gustavo… o valor final não foi medido".
- A checagem de links acusou `process-log/planning/` como quebrado antes da cópia. Depois da cópia, o link existe.

## 6. Pendências e decisões que dependem do Gustavo

**`[GUSTAVO: …]` pendentes:**
1. `README.md:1`: nome no título.
2. `README.md:5`: nome.
3. `README.md:6`: LinkedIn.
4. `README.md:145`: complementar "O que eu adicionei" com o que não está no process log.
5. `README.md:155`: exportar as conversas para `process-log/chat-exports/`. A pasta está vazia, e o git não versiona pasta vazia.
6. `README.md:182`: data da submissão.
7. `process-log/process-log.md`, na ressalva da tabela de tempo: tempo real de F4 a F7, com revisão.

**Outras decisões:**
- **Carga extra por ataque:** citar no memo ou no README que um ataque desvia o ticket para humano em 14,5% dos pares (custo, não dano)?
- **"Decisão minha"** da F7 no process log e a coluna "já vi em produção" em `docs/producao.md` continuam em branco, como pede a spec.
- **Antes do PR:** o commit da F7, o push e o PR são seus. O título do PR deve ser `[Submission] Gustavo Covaleski — Challenge 002`.

## 7. Tempo gasto × orçado

Orçado: 35 min (teto 42). Relógio: das 00:17 às ~00:24, cerca de 7 min de execução, mais a escrita do memo e do README.
