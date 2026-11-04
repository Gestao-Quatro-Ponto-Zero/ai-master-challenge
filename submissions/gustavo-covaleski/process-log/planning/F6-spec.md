# F6 — Prontidão para produção: lacunas da F5 + matriz de falhas (spec para o Claude Code)

- **Teto:** 20 min. Ao chegar a 24 min (120%), pare e proponha o corte no report.
- **Leia antes:** `CLAUDE.md`; `planning/F5-report.md`; `docs/fluxo.md`; `solution/triagem.py`.
- **Não mude:** o modelo, os limiares, a política por categoria, o prompt do LLM.

## Passo 1 — Lacunas da F5 (≤ 8 min)

1. **CPF × celular:** em `triagem.py`, uma sequência de 11 dígitos só vira `[CPF]` se passar no dígito verificador do CPF; caso contrário, vira `[TELEFONE]`. Teste com 1 CPF válido gerado no teste, 1 celular de 11 dígitos (DDD + 9) que não passa no verificador, e o caso com separadores. Registre no report a limitação restante: um celular que por acaso passe no verificador (~1%) sai como `[CPF]`, mas sai do log do mesmo jeito.
2. **Teste de `registrar_correcao`:** grava uma linha em `runtime/correcoes.jsonl` com chave, categoria correta, atendente e timestamp; recusa categoria fora das 8 sem lançar exceção ao chamador; não grava texto sem máscara.
3. **Ataque que cai em "IA decide":** em `f5_injecao.py`, para os 100 pares, conte quantos ataques bem-sucedidos (mudança para a categoria-alvo) **e** quantas trocas de rótulo caem na faixa `IA decide`, depois da política. É a métrica de dano real: o que passa sem humano. Grave em `f5_injecao.json`. Não rode o LLM de novo; use só o clássico.

## Passo 2 — Detector de injeção como rebaixamento (≤ 5 min)

Critério fixado antes de medir:
- **Detector:** padrões de instrução no texto ("ignore", "instruction", "system:", "categoria", "category", "classify", "classifique", chaves `{` `}`, ou o nome de uma categoria repetido 3 ou mais vezes).
- **Efeito:** só **rebaixa** a faixa para `humano decide`, com `motivo = "possível injeção"`. Nunca promove.
- **Medida 1, falso positivo:** % do holdout por grupo que dispara o detector **sem** ataque.
- **Medida 2, cobertura:** % dos 100 pares que disparam o detector.
- **Regra de adoção:** adote (ligado por padrão) **só** se o falso positivo for ≤ 1% do holdout; caso contrário, deixe desligado e registre os números como achado. Não ajuste os padrões depois de ver o resultado.
- Teste: um texto com ataque cai em `humano decide`; um ticket limpo do golden set não é afetado.

## Passo 3 — `docs/producao.md` (≤ 7 min)

1. **Matriz de falhas:** falha | como detecta | o que o sistema faz | quem é avisado | teste que prova (nome do teste) | **já vi em produção** (coluna em branco; quem preenche é o Gustavo). Linhas mínimas:
   - evento duplicado;
   - texto vazio ou curto;
   - classificador falha ou modelo ausente;
   - injeção no texto;
   - dado pessoal no texto;
   - texto fora do idioma;
   - drift de categoria ou de vocabulário;
   - política ou modelo novo pior que o anterior (o portão de qualidade do golden set barra);
   - LLM indisponível (não se aplica ao caminho de decisão; dizer isso).
2. **Monitoramento:** métrica | como calcular a partir de `runtime/decisoes.jsonl` e `correcoes.jsonl` | alerta (com limiar escrito como premissa editável). Mínimo:
   - cobertura semanal da faixa `IA decide`;
   - taxa de correção na faixa `IA sugere` e precisão estimada pelas correções;
   - distribuição das categorias previstas contra a do treino;
   - taxa de fallback;
   - taxa de duplicados;
   - taxa de disparo do detector de injeção;
   - latência p95.
3. **Rollback, em três níveis:**
   - **imediato:** `TRIAGEM_MODO=sombra`, tudo vai para humano e o log continua;
   - **política:** voltar o CSV da política para a versão anterior (o `politica_versao` está no log);
   - **modelo:** apagar `modelo_cache/` e retreinar a versão anterior (o `modelo_versao` está no log).
   Diga quanto tempo leva cada um, medindo quando for possível (o retreino leva ~21,5 s, F5).
4. Nenhuma afirmação sobre a experiência do Gustavo.

## Passo 4 — Report

`planning/F6-report.md` (formato da seção 8 do `CLAUDE.md`). Linha da F6 no process log com "Decisão minha" vazia.

## Critérios de aceite

- `pytest solution/tests -q` passa; os testes da F5 continuam passando.
- O portão de qualidade continua passando com o detector ligado (se adotado).
- `f1_splits.csv` com o mesmo hash. Nenhum commit.
