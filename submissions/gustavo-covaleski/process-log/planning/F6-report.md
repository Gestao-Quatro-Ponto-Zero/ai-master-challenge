# F6 — Report (Prontidão para produção)

Caminhos relativos à submissão (`ai-master-challenge/submissions/gustavo-covaleski/`).

**Antes da F6:** a F5 foi commitada em `145db22f942d8f671a1493f26436407ca8195a48`. O commit tem 14 arquivos, todos dentro da submissão. Nenhum `.venv`, `.env`, `runtime`, `modelo_cache` nem cache; `findstr sk-ant` vazio; a chave não aparece em nenhum arquivo staged; nenhum nome ou e-mail do DS1; nenhum texto de ticket fora das exceções. A "Decisão minha" da F5 entrou antes do commit.

## 1. O que foi feito

1. **CPF × celular** (`triagem.py`): 11 dígitos viram `[CPF]` só se passarem no dígito verificador (`cpf_valido`); caso contrário, `[TELEFONE]`.
2. **`registrar_correcao`**:
   - valida a categoria (uma das 8);
   - devolve `False` em vez de lançar exceção;
   - grava `observacao_mascarada` (opcional, mascarada).
3. **Dano real da injeção** (`f5_injecao.py --so-classico`): trocas e sucessos que caem em "IA decide" depois da política. O LLM não foi chamado de novo; o bloco `llm` de `f5_injecao.json` foi preservado.
4. **Detector de injeção** (`detectar_injecao`, critério da spec escrito antes de medir) e medição em `solution/f6_detector.py` → `f6_detector.json`. Pela regra de adoção, **não foi adotado**: `DETECTOR_PADRAO = "off"`, e ele pode ser ligado com `TRIAGEM_DETECTOR=on`.
5. **`solution/tests/test_f6.py`** com 8 testes. `pytest solution/tests -q` → **54 passed**; os 46 da F5 continuam passando.
6. **`docs/producao.md`**: matriz de 9 falhas (com a coluna "já vi em produção" em branco), 7 métricas de monitoramento com limiares como premissa, e rollback em 3 níveis.
7. **Retreino medido de novo** (`triagem._treinar()`): 78,2 s, com a versão `82d03ed9a103`, idêntica à da F5.

## 2. Resultados

| Número | Valor | Script → arquivo |
|---|---|---|
| Detector: falso positivo no holdout por grupo | **4,75%** (454 de 9.567) | `f6_detector.py` → `f6_detector.json` |
| … disparos por padrão de instrução / só por nome de categoria repetido | 159 / 295 | idem |
| Detector: cobertura nos 100 pares de ataque | **100%** (20/20 em cada ataque) | idem |
| Regra de adoção (≤ 1%) | **não adotado** | idem |
| Dano: trocas de rótulo do clássico em "IA decide" | **0** de 9 trocas | `f5_injecao.py --so-classico` → `f5_injecao.json` |
| Dano: ataques bem-sucedidos em "IA decide" | **0** de 3 sucessos | idem |
| Pares de ataque em "IA decide" (sem troca) | 10 de 100 | idem |
| Testes | 54 passed | `pytest solution/tests -q` |
| Retreino (rollback de modelo) | 21,5 s (F5) / 78,2 s (F6) | `triagem._treinar()` |
| `f1_splits.csv` | SHA-256 `37703450…865ba0` (inalterado) | — |

## 3. O que contraria a hipótese ou a expectativa

- **O detector derruba tickets legítimos demais.** 295 dos 454 falsos positivos vêm só da regra "nome de categoria repetido 3 ou mais vezes". No DS2 pré-processado, tickets reais repetem "access", "hardware" e "storage" naturalmente (assunto + corpo). Os outros 159 vêm dos padrões de instrução, em tickets reais: "instruction" em 86 tickets, "category" em 46, "ignore" em 30 e "classify" em 3 (contagem por ticket, com sobreposição). Chaves `{ }` não aparecem, porque o texto foi pré-processado. Pela regra fixada, o detector fica desligado. Não ajustei os padrões.
- **A política por categoria já contém o dano da injeção:** nenhuma das 9 trocas nem dos 3 sucessos do clássico cai em "IA decide". Os ataques que funcionam desviam para categorias com teto "IA sugere" ou "humano decide", ou baixam o `p_max`. A defesa efetiva hoje é a política, não o detector. Com só 100 pares e 10 deles em "IA decide", é um resultado fraco como prova; a taxa real de dano pode não ser zero.
- **O retreino levou 78,2 s, contra 21,5 s na F5,** na mesma máquina e com a mesma versão do modelo. A causa não foi investigada (o servidor Streamlit já não estava rodando na checagem). Em `docs/producao.md` está "planejar ~1,5 min".

## 4. Desvios da spec

- **`registrar_correcao`:** a assinatura ganhou `observacao` opcional (mascarada) e passou a devolver `bool`. Sem isso, o requisito "não grava texto sem máscara" não teria o que testar, porque a função não recebia texto.
- **Detector aplicado ao texto já mascarado.** Os marcadores de máscara usam `[ ]`, não `{ }`, então não disparam o padrão de chaves.
- **"Nome de categoria repetido":** implementado como contagem por palavra inteira (`\b`) do nome em minúsculas. Nomes de várias palavras ("hr support") só contam quando aparecem juntos.
- **O portão de qualidade com detector ligado** não foi exigido, porque o detector não foi adotado.
- **Tempo de rollback de política e do modo sombra:** não medido; está estimado em "segundos" e rotulado assim no doc.

## 5. Erros e correções durante a execução

- Em `docs/producao.md`, atribuí a lentidão do retreino ao servidor Streamlit "ainda rodando". A checagem seguinte mostrou a porta 8599 sem resposta, então a atribuição não se sustentava. Troquei por "diferença não explicada, provavelmente carga da máquina".
- O servidor Streamlit da F5 já não estava rodando na F6; não precisou ser encerrado.

## 6. Pendências e decisões que dependem do Gustavo

1. Detector desligado por regra. Se quiser uma versão 2 (por exemplo, sem a regra de nome repetido), o critério precisa ser fixado antes de medir de novo.
2. O fato de a política conter a injeção (0 casos em "IA decide") é a principal evidência de segurança, mas a amostra é pequena (100 pares). Ampliar a amostra com o clássico (custo ≈ 0) ou declarar como limitação na F7?
3. Preencher a coluna "já vi em produção" da matriz de falhas.
4. Commit da F6.

## 7. Tempo gasto × orçado

- Orçado: 20 min (teto 24).
- Relógio: das 00:09 às ~00:14 de execução da F6, depois do commit da F5. Inclui ~78 s de retreino e ~20 s de medição do detector.
