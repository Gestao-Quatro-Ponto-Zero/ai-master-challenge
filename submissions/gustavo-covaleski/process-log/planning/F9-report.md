# F9 — Report (Confirmação por categoria no holdout)

Caminhos relativos à submissão (`ai-master-challenge/submissions/gustavo-covaleski/`).

**Commit:** `b9c640b059e8afc6772163fc50706e5eb2995a68`, "F9: confirmação por categoria no holdout; política implantada só rebaixa". Sem push.

## 1. O que foi feito

1. **`solution/f9_confirmacao.py`:**
   - acrescenta a `f8_politica_por_categoria.csv` a coluna `politica_confirmada_holdout`, que aplica a regra da F4 ao LI do holdout em "IA decide" (sem tickets no holdout → mantém a OOF);
   - acrescenta `politica_implantada` (a mais restritiva entre OOF e confirmação);
   - em `f8_faixas.json`, renomeia `holdout_grupo` → `selecao_oof` e grava a chave nova `implantada`;
   - recalcula `f8_economia.csv`;
   - renomeia `dano_ampliado_f8` → `dano_ampliado_f8_oof` e acrescenta nele a distribuição das trocas silenciosas por categoria-alvo e por ataque.
2. **`triagem.carregar_politica`** passou a ler `politica_implantada`. `f5_injecao.py --dano-ampliado-f8` foi rodado de novo com a política implantada, e a nota do JSON foi atualizada.
3. **Testes:** `solution/tests/test_f9.py` com 7 testes (confirmação, "só rebaixa" e a implantada nunca acima da OOF). `pytest` → **69 passed**, com o portão de qualidade.
4. **App:**
   - a aba "Política" mostra as colunas seleção fora da dobra, confirmação no holdout e implantada;
   - o lote usa como referência a chave `implantada`;
   - refeitos `6_lote.png` e `7_politica.png`. Os screenshots 1 a 5 não mudaram de faixa (ids 2906, 17539, 28128, 791 e 33791) e não foram refeitos.
5. **Docs:**
   - em `politica.md`, a seção vigente foi regenerada: duas etapas, tabela de 3 colunas, cobertura, economia e injeção;
   - memo, README, `fluxo.md` e `producao.md` atualizados;
   - o README ganhou "confirmação por categoria no holdout; a regra só rebaixa" na Abordagem e a F9 no workflow e em "Como rodar".
6. **Process log:** "Decisão minha" da F8 preenchida com o texto do Gustavo; linha 12 (F9) com a decisão vazia; erro do F8-report na tabela.

## 2. Resultados

### Política por categoria

| Categoria | Seleção OOF (F8) | LI no holdout | Confirmação | **Implantada** |
|---|---|---|---|---|
| Access | IA decide | 0,9749 | IA decide | **IA decide** |
| Purchase | IA decide | 0,9782 | IA decide | **IA decide** |
| HR Support | IA decide | 0,9604 | IA sugere | **IA sugere** |
| Storage | IA decide | 0,9582 | IA sugere | **IA sugere** |
| Administrative rights | IA decide | 0,8968 | humano decide | **humano decide** |
| Internal Project | IA sugere | — | IA sugere (mantém a OOF) | **IA sugere** |
| Miscellaneous | IA sugere | — | IA sugere (mantém a OOF) | **IA sugere** |
| Hardware | humano decide | — | humano decide (mantém a OOF) | **humano decide** |

Fonte: `f8_politica_por_categoria.csv`. Os valores reais **conferem** com os esperados pelo chat do Projeto.

### F4 × F8 (seleção OOF) × F9 (implantada), no holdout por grupo

| Número | F4 (escolhido no holdout) | F8 seleção OOF | **F9 implantada** | Arquivo |
|---|---|---|---|---|
| Limiares IA decide / IA sugere | 0,74 / 0,66 | 0,71 / 0,64 | 0,71 / 0,64 | `f8_faixas.json` |
| IA decide: cobertura (precisão; IC 95%) | 12,98% (98,87%; 98,12–99,33) | 33,42% (97,75%; 97,17–98,21) | **13,37% (98,75%; 97,98–99,23)** | `f4_politica.json`; `f8_faixas.json` (`selecao_oof`, `implantada`) |
| IA sugere: cobertura (precisão; IC 95%) | 31,41% (96,67%) | 13,58% (94,84%; 93,50–95,92) | **32,12% (96,23%; 95,49–96,84)** | idem |
| Humano: cobertura (precisão do modelo) | 55,61% (75,30%) | 53,01% (74,58%) | **54,51% (75,15%)** | idem |
| Economia, cenário A, base (3 min, R$ 35/h) | R$ 6.815,62 | R$ 17.543,90 | **R$ 7.018,66** | `f4_economia.csv`; `f8_economia.csv` |
| Economia, faixa da grade | R$ 3.245,53–12.982,13 | R$ 8.354,24–33.416,95 | **R$ 3.342,22–13.368,87** | idem |
| Injeção: dano silencioso em IA decide | 0 / 6.210 (LS 0,062%) | 80 / 15.985 (0,50%; LS 0,62%) | **0 / 6.395 (LS 0,06%)** | `f5_injecao.json`: `dano_ampliado`, `dano_ampliado_f8_oof`, `dano_ampliado_f8` |
| Injeção: pares que saem de IA decide | 898 (14,5%) | 2.829 (17,7%) | **860 (13,45%)** | idem |

- **Distribuição das 80 trocas silenciosas da seleção OOF:** todas tinham **Storage** como alvo, e todas vieram do ataque **categoria repetida** (`dano_ampliado_f8_oof.distribuicao_silenciosos`). Storage foi rebaixada para "IA sugere" na confirmação, e por isso o dano zera.
- **Memo:** 399 palavras (373 sem as fontes).
- **`f1_splits.csv`:** mesmo hash.

## 3. O que contraria a hipótese ou a expectativa

- **O resultado da F9 coincide com a F4 em cobertura de IA decide** (13,37% contra 12,98%), mesmo com limiares diferentes. A escolha fora da dobra corrigiu o método, e a confirmação no holdout trouxe o número de volta ao patamar da F4. A diferença está em IA sugere: 32,12% contra 31,41%, com precisão de 96,23% contra 96,67%.
- **Todo o dano silencioso da F8 vinha de uma única categoria-alvo** (Storage), por um único ataque (nome de categoria repetido). Faz sentido: "storage" é palavra de alto peso no vocabulário, e Storage estava em "IA decide" na seleção OOF.
- **A estimativa do chat (~13,4%, ~98,8%) bate com o calculado** (13,37%, 98,75%).

## 4. Desvios da spec

- **Nome da chave:** `holdout_grupo` foi renomeada para `selecao_oof` em `f8_faixas.json` (a spec pede "mantendo a chave atual como `selecao_oof`"). O app foi ajustado.
- **Ordem obrigatória de execução:** rodar `f8_oof.py` de novo sobrescreve o CSV sem as colunas da F9, então `f9_confirmacao.py` precisa vir depois. Isso está registrado em "Como rodar" do README.
- **README, resultados:** a linha "Administrative rights abaixo da meta" (F8) virou "Categorias rebaixadas na confirmação no holdout", com as três categorias.
- **Teste extra:** `test_f9.py` (7 testes); a spec não pedia teste novo.
- **Lote do app:** apaguei `runtime/demo/` antes de refazer `6_lote.png`. O lote é idempotente por `event_id` e devolveria os resultados guardados com a política da F8.

## 5. Erros e correções durante a execução

- O 1º `7_politica.png` saiu com a tabela ainda vazia (a página estava carregando). Refeito esperando o canvas do dataframe e 5 s.
- O README ficou com "Hardware fica com humano" repetido na recomendação 3, depois da troca de texto. Corrigido.

## 6. Pendências e decisões que dependem do Gustavo

1. "Decisão minha" da F9 no process log.
2. A decisão da F9 é pós-hoc e está declarada como tal em `politica.md`, no README (Abordagem) e no JSON. Se quiser, dá para citá-la também no memo; não coube sem passar de 400 palavras.
3. Push e PR.

## 7. Tempo gasto × orçado

Orçado: 30 min (teto 36). Relógio: das 01:46 às ~01:53, cerca de 7 min.
