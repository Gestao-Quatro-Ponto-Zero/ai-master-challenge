# F9 — Confirmação por categoria no holdout (spec para o Claude Code)

- **Teto:** 30 min. Ao chegar a 36 min (120%), pare e proponha o corte no report.
- **Decisão do Gustavo:** a política implantada passa a exigir **duas etapas**. A categoria precisa passar na seleção fora da dobra (F8) **e** na confirmação no holdout. É uma regra decidida depois de ver o holdout, mas **só rebaixa**, nunca promove. Declare isso como decisão conservadora pós-hoc.
- **Motivo:** em `f8_politica_por_categoria.csv`, 3 das 5 categorias em "IA decide" ficam abaixo de 1 − *e*_inferior (0,9680) no holdout: Administrative rights (LI 0,8968), HR Support (LI 0,9604) e Storage (LI 0,9582). O memo hoje diz "5 categorias que passaram na meta", o que é falso no conjunto de teste. O F8-report citou só Administrative rights.

## Passo 1 — Política implantada

Em `f8_politica_por_categoria.csv`, acrescente a coluna `politica_confirmada_holdout`, aplicando a mesma regra da F4 aos limites inferiores **do holdout** (os da faixa "IA decide" de cada categoria):
- LI ≥ 1 − *e*_inferior → IA decide;
- LI ≥ 1 − *e*_superior → IA sugere;
- abaixo disso → humano decide;
- categoria sem tickets em "IA decide" no holdout → mantém a política OOF.

Acrescente também `politica_implantada` = a **mais restritiva** entre `politica` (OOF) e `politica_confirmada_holdout`. `triagem.carregar_politica` passa a ler `politica_implantada`.

Esperado, pela leitura do chat do Projeto (confira e reporte os valores reais):
- Access e Purchase em IA decide;
- HR Support e Storage em IA sugere;
- Administrative rights em humano decide.

## Passo 2 — Números de capa recalculados

Com a política implantada, no holdout: cobertura e precisão, com IC de Wilson, de cada faixa. Grave em `f8_faixas.json`, na chave `implantada`, mantendo a chave atual como `selecao_oof`. A estimativa do chat é de ~13,4% em "IA decide", com ~98,8% de precisão; é só uma conta de referência, não para copiar.

Recalcule também:
- `f8_economia.csv` (grade 3 × 3), pela cobertura implantada;
- `dano_ampliado_f8` do clássico com a política implantada, guardando o resultado anterior como `dano_ampliado_f8_oof`;
- a distribuição das 80 trocas silenciosas anteriores por categoria-alvo, para mostrar de onde vinha o dano.

## Passo 3 — App, screenshots, docs

- Refaça só os screenshots cuja faixa mudou com a nova política, mais `6_lote.png` e `7_politica.png`. A tabela da aba "Política" mostra as colunas OOF, holdout e implantada.
- **Memo, README e docs:** troque os números de capa pelos da política implantada. A frase central passa a ser: "a seleção fora da dobra indicou 5 categorias (33,4% do volume); a confirmação no teste sustentou 2 (≈ X%); só essas são ativadas". Corrija também o "5 categorias que passaram na meta" e a linha S4 do memo. Mantenha o memo em até 400 palavras.
- No README (Abordagem), acrescente: "confirmação por categoria no holdout; a regra só rebaixa".
- Use `grep` para garantir que não sobrou nenhum `33,4`, `33,42`, `17,5 mil`, `17.543` ou `5 categorias` fora das frases que descrevem a seleção OOF.

## Passo 4 — Process log, report, commit

1. **Process log:**
   - preencha a "Decisão minha" da F8: "Aprovada: idempotência corrigida e reproduzida em teste; limiar e política escolhidos fora da dobra. Política implantada passa a exigir confirmação por categoria no holdout (F9)."
   - linha da F9 com "Decisão minha" vazia;
   - na tabela de erros: "F8-report (Claude Code) citou só Administrative rights abaixo da meta no holdout; HR Support e Storage também estavam abaixo. O memo afirmava '5 categorias que passaram na meta'. Detectado pela revisão do chat do Projeto no `f8_politica_por_categoria.csv`."
2. `pytest solution/tests -q` passa, com o portão de qualidade.
3. Checagens de commit da F8 completas.
4. Commit: `F9: confirmação por categoria no holdout; política implantada só rebaixa`. Sem push.
5. `planning/F9-report.md` com uma tabela F4 × F8 seleção OOF × F9 implantada: limiares, cobertura e precisão por faixa, economia e dano da injeção.
