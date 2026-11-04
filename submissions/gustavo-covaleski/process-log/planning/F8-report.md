# F8 — Report (Correções da revisão pré-push)

Caminhos relativos à submissão (`ai-master-challenge/submissions/gustavo-covaleski/`). As partes foram executadas na ordem A → F, com `pytest` ao fim de cada uma, e nenhuma deixou teste falhando.

**Commit:** `fdd1c81a72a1b107c9779b05ee993cbdbc26129f`, "F8: idempotência sem colisão nem corrida, limiar fora do holdout, modelo versionado, app e screenshots". Sem push.

## 1. O que foi feito

1. **A — Idempotência** (`triagem.py`):
   - chave sem `event_id` = SHA-256 de texto bruto + canal + janela de 10 min; a janela anterior também conta como duplicado;
   - reserva com `INSERT OR IGNORE` + `commit` antes de processar;
   - o duplicado espera até 2 s pelo resultado ou devolve `em_processamento`;
   - falha depois da reserva → `DELETE` da reserva;
   - o duplicado grava uma linha `tipo = duplicado` no log;
   - o log passou a ser serializado por um lock em sqlite, porque o append no Windows não é atômico entre processos;
   - 6 testes novos, entre eles a corrida com 6 processos `spawn` × 10 eventos.
2. **B — Limiar e política fora do holdout** (`f8_oof.py`):
   - `StratifiedGroupKFold(5)` no treino, predições fora da dobra;
   - as mesmas `curva`/`faixas` (F3) e `politica_categoria` (F4), com *e*_Q2 = 3,82%;
   - tudo congelado e aplicado uma única vez no holdout;
   - `triagem.carregar_politica` passou a ler os arquivos `f8_*`;
   - `dano_ampliado_f8` recalculado só com o clássico.
3. **C — Modelo versionado:**
   - `versao_atual()` = SHA-256(SHA-256 de `f1_splits.csv` + `PARAMS`)[:12], gravado em `modelo_cache/modelo_<versao>.joblib`;
   - `TRIAGEM_CACHE_DIR` e `TRIAGEM_MODELO_VERSAO` configuráveis; versão inexistente → fallback, sem treinar;
   - 3 testes.
4. **D — Pequenas:**
   - a aba "lote" roda em `runtime/demo/` e restaura a variável de ambiente;
   - o app checa o retorno de `registrar_correcao`;
   - linha de Limitações sobre treino sem máscara e inferência com máscara.
5. **E — App:**
   - cartão de resultado com cor, `st.metric`, "Por que esta faixa" pelo caminho real, top-2, termos e JSON no expander;
   - abas "Política" e "lote" (com referência do holdout e gráfico);
   - `.streamlit/config.toml`;
   - 7 screenshots (1280 px, `deviceScaleFactor` 2, runtime temporário);
   - os 2 antigos removidos com `git rm`.
6. **F — Fechamento:** docs, memo, README e process log atualizados; checagens; commit.

## 2. Resultados

### Antes × depois (números de capa)

| Número | Antes (F3/F4, escolhido no holdout) | Depois (F8, escolhido fora da dobra) | Arquivo |
|---|---|---|---|
| Limiares IA decide / IA sugere | 0,74 / 0,66 | **0,71 / 0,64** | `f8_faixas.json` |
| Cobertura IA decide | 12,98% | **33,42%** | `f8_faixas.json` |
| Precisão IA decide (IC 95%) | 98,87% (98,12–99,33) | **97,75% (97,17–98,21)** | idem |
| Cobertura IA sugere / precisão | 31,41% / 96,67% | 13,58% / 94,84% (93,50–95,92) | idem |
| Cobertura humano / precisão do modelo | 55,61% / 75,30% | 53,01% / 74,58% | idem |
| Política: IA decide | Access, Purchase | Access, Purchase, **HR Support, Storage, Administrative rights** | `f8_politica_por_categoria.csv` |
| Política: IA sugere | HR Support, Internal Project, Miscellaneous, Storage | Internal Project, Miscellaneous | idem |
| Política: humano decide | Hardware, Administrative rights | Hardware | idem |
| Economia, cenário A (base 3 min, R$ 35/h) | R$ 6.815,62/ano | **R$ 17.543,90/ano** | `f8_economia.csv` |
| Economia, faixa da grade | R$ 3.245,53 – 12.982,13 | R$ 8.354,24 – 33.416,95 | idem |
| Injeção: dano silencioso em IA decide | 0 de 6.210 (LS 0,062%) | **80 de 15.985 (0,50%; LS 0,62%)** | `f5_injecao.json` (`dano_ampliado` × `dano_ampliado_f8`) |
| Injeção: pares que saem de IA decide | 898 (14,5%) | 2.829 (17,7%) | idem |
| Acurácia no holdout (portão ≥ 0,84) | 85,07% | 85,07% (o modelo não mudou) | `f8_faixas.json` |
| Testes | 54 passed | **63 passed** | `pytest solution/tests -q` |
| Memo | 400 palavras | 397 (371 sem as fontes) | `wc -w` |

### Por categoria

| Categoria | Política (OOF) | LI fora da dobra | Precisão em IA decide no holdout (IC 95%) |
|---|---|---|---|
| Access | IA decide | 0,9849 | 98,52% (97,49–99,13) |
| Administrative rights | IA decide | 0,9743 | **95,08% (89,68–97,73)**, abaixo da meta |
| HR Support | IA decide | 0,9684 | 97,04% (96,04–97,80) |
| Storage | IA decide | 0,9810 | 97,95% (95,82–99,00) |
| Purchase | IA decide | 0,9873 | 99,25% (97,82–99,74) |
| Miscellaneous | IA sugere | 0,9563 | — |
| Internal Project | IA sugere | 0,9669 | — |
| Hardware | humano decide | 0,9462 | — |

Origem: `f8_politica_por_categoria.csv`.

### Trocas de texto (parte F)

| Arquivo | De → para |
|---|---|
| `README.md` | Resumo: 13,0% / 98,9% → 33,4% / 97,8%; "só em Access e Purchase" → "nas 5 categorias que passaram na meta fora do holdout" |
| `README.md` | Tabela de resultados: linha das faixas 12,98/31,41/55,61 → 33,42/13,58/53,01 (`f8_faixas.json`); linha da sensibilidade pós-hoc da F4 (12,98/52,84/34,18) **substituída** pela linha de Administrative rights abaixo da meta no holdout; injeção 0 de 6.210 / 898 → 80 de 15.985 / 2.829; economia R$ 6.815,62 → R$ 17.543,90 (`f8_economia.csv`) |
| `README.md` | Recomendação 3 reescrita (5 categorias, alerta para Administrative rights; Hardware com 95,18% fora da dobra e limite inferior 0,9462 contra a meta de 0,9545, no lugar de "95,9%"); Abordagem: "limiar e política escolhidos com predições fora da dobra no treino; holdout usado uma única vez"; fases F0 a F8; linha da F8 no workflow e nos erros; linha de Limitações sobre máscara; screenshots embutidos (2 e 6) e listados (1, 3, 4, 5 e 7) |
| `docs/memo-diretor.md` | Decisão: "só em Access e Purchase" → "nas 5 categorias que passaram na meta"; 13,0% / 98,9% → 33,4% / 97,8%; R$ 6,8 mil (3,2–13,0) → R$ 17,5 mil (8,4–33,4); injeção 6.210 / 898 → 15.985 / 80 / 2.829; S4 com o alerta de Administrative rights; fontes [3] e [7] → `f8_faixas.json` e `f8_economia.csv`; texto encurtado para ficar em até 400 palavras |
| `docs/politica.md` | Nova seção "Política vigente (F8)" no topo (tabela por categoria, cobertura, economia, alerta de Administrative rights, exemplos que mudaram de faixa); o conteúdo antigo ficou sob "Histórico da F4 (substituído na F8)", **sem reescrever os números**, que são o registro da F4 |
| `docs/fluxo.md` | 0,74 / 0,66 (`f3_faixas.json`) → 0,71 / 0,64 (`f8_faixas.json`); base de drift 12,98% → 33,42% |
| `docs/producao.md` | Linha do duplicado (chave, reserva, linha no log, testes da F8); métrica de taxa de duplicados tirada do log; base de cobertura 12,98% → 33,42%; injeção com os números da F8 (os da F4 aparecem como comparação); rollback de política → arquivos `f8_*`; rollback de modelo → `TRIAGEM_MODELO_VERSAO` |
| `process-log/process-log.md` | Linha 11 (F8) e 4 erros novos; as linhas históricas não foram mexidas |

## 3. O que contraria a hipótese ou a expectativa

- **A escolha correta fora do holdout aumentou a cobertura automática** (12,98% → 33,42%), em vez de reduzi-la. Na F4, a regra por categoria aplicada ao próprio holdout rebaixou HR Support, Storage e Administrative rights por pouco. No treino fora da dobra, com n maior e IC mais estreito, as três passam.
- **Administrative rights passou fora da dobra (LI 0,9743), mas no holdout ficou com precisão de 95,08% (LI 0,8968),** abaixo das duas metas. Pela regra, não ajustei. É a mesma categoria com 6 de 6 "original errado" na revisão. O memo e o README pedem atenção a ela no piloto.
- **Com a nova política, a injeção passa a ter dano silencioso:** 80 de 15.985 pares (0,50%) mudam para a categoria-alvo e continuam em "IA decide"; com a política da F4 eram 0 de 6.210. A política mais conservadora da F4 é que continha o dano. O memo deixou de dizer "nenhum mudou".
- **Precisão de "IA decide" no holdout de 97,75%:** passa no portão (≥ 0,97), mas o limite inferior (97,17%) está perto da meta.
- **Corrida:** sem o lock no log, a corrida de 6 processos podia intercalar linhas no Windows, onde o append não é atômico. O lock em sqlite foi acrescentado de forma preventiva; não reproduzi a intercalação.

## 4. Desvios da spec

- **`test_f5.py` mudou em dois pontos** por consequência da parte A:
  1. `test_idempotencia_sem_event_id_usa_hash` esperava duplicado entre textos que só diferiam em maiúsculas; com texto bruto, isso deixou de valer, e o teste usa espaços nas pontas (`strip()`);
  2. o helper `log()` passou a ignorar linhas `tipo = duplicado`, porque o golden mede `decisoes_no_log`.
- **Sensibilidade pós-hoc da F4** (52,84 / 34,18): não recalculei para a política da F8, porque não está na spec. No README, a linha foi substituída pela de Administrative rights; em `politica.md`, ficou no histórico.
- **`politica.md`:** em vez de trocar cada número antigo, criei a seção vigente e marquei a antiga como histórico. Os números da F4 continuam visíveis como registro.
- **Screenshot `3_humano_politica.png`:** usa o id 28128 (Hardware, 81,6%, rebaixado pelo teto da política), não o 19701, cujo trecho de 120 caracteres tem confiança de 62,9% e cairia em humano pelo limiar, não pela política. Ids usados: 2906 (1), 17539 (2), 28128 (3), 791 com Refund request (4) e 33791 com `event_id` repetido (5). Todos são trechos já em `docs/politica.md`. Com a política nova, os ids 917 e 17550 mudaram de "IA sugere" para "IA decide" (registrado em `politica.md`).
- **`modelo_cache/modelo.joblib`** (versão antiga, `82d03ed9a103`, no esquema anterior de nome) não foi apagado nem renomeado. O rollback para ele exigiria copiá-lo como `modelo_<versao>.joblib`.
- **Arquivo extra** `f8_curva_oof.csv` (curva cobertura × acerto no OOF).

## 5. Erros e correções durante a execução

1. Depois da parte A, `test_idempotencia` da F5 falhou (2 linhas no log em vez de 1, porque o duplicado passou a gravar uma linha). Corrigido no helper do teste (§4).
2. A tabela de `politica.md` saiu com ponto decimal (um `replace` na linha inteira). Corrigida no mesmo passo.
3. Playwright: o seletor de tipo travou no 1º script (corrigido com o teclado), e a espera pelo lote olhava um cabeçalho oculto (corrigido esperando o gráfico).
4. O memo passou de 400 palavras depois das trocas (426). Cortei frases fora dos números até 397.

## 6. Pendências e decisões que dependem do Gustavo

1. **Administrative rights em "IA decide":** a regra registrada manda ativar, mas o holdout mostra 95,08%. Manter, com atenção no piloto (como está), ou decidir outra coisa, sabendo que seria uma decisão depois de ver o holdout?
2. **Dano silencioso da injeção de 0,50% com a política nova:** aceitar e declarar (como está) ou tratar? O detector segue desligado pela regra da F6.
3. "Decisão minha" da F8 no process log.
4. Push e PR.

## 7. Tempo gasto × orçado

- Orçado: 80 min (teto 96).
- Relógio: das 01:18 às 01:43, cerca de 25 min. Inclui ~7 min de validação cruzada no treino, ~1,5 min de retreino do modelo versionado e ~5 min de screenshots.
