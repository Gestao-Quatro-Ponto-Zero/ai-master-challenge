# F8 — Correções da revisão pré-push (spec para o Claude Code)

- **Teto:** 80 min. Ao chegar a 96 min (120%), pare e proponha o corte no report.
- **Ordem obrigatória:** A → B → C → D → E → F. Rode `pytest solution/tests -q` ao fim de cada parte. Se uma parte deixar teste falhando, **pare** e reporte; não siga para a próxima.
- **Ordem de corte, se estourar:** primeiro a parte D; depois a aba "Política" da parte E. **Nunca cortar A nem B.**
- **Leia antes:** `CLAUDE.md`; `solution/triagem.py`; `solution/app.py`; `solution/f3_faixas.py`; `solution/f4_politica.py`; `docs/producao.md`.
- **Origem:** revisão do chat do Projeto antes do push, pedida pelo Gustavo. As falhas 1 e 2 foram reproduzidas: colisão de chave entre "pedido 1111" e "pedido 2222"; e, com 6 processos simultâneos × 15 eventos, 14 eventos com 2–3 decisões no log e 15 retornos "falha interna".

## Parte A — Idempotência (falhas 1 e 2)

1. **Chave sem `event_id`:** SHA-256 de `texto.strip()` **bruto** (sem `normalizar`, que troca dígitos por 0) + `|` + canal + `|` + janela de 10 min (`int(time.time() // 600)`). Para não perder duplicados na virada da janela, considere duplicado se a chave da janela atual **ou** a da anterior já existir; grave só a da atual. Com `event_id`, a chave continua `evt:<id>`, sem janela.
2. **Reservar antes de processar** (elimina a corrida):
   - `sqlite3.connect(..., timeout=5)`; tabela `eventos (chave TEXT PRIMARY KEY, resultado TEXT)`;
   - `INSERT OR IGNORE INTO eventos (chave, resultado) VALUES (?, NULL)` + `commit()` imediato;
   - se `rowcount == 1`, este chamador processa e, no fim, faz `UPDATE` do resultado;
   - se `rowcount == 0`, é duplicado: espere até 2 s (passos de 50 ms) pelo `resultado`. Se ele chegar, devolva-o com `duplicado = True`. Se não chegar, devolva `{"duplicado": True, "status": "em_processamento", "faixa": "humano decide", ...}`. **Em nenhum dos dois casos registre uma nova decisão.**
3. **Liberar a reserva em caso de falha:** se ocorrer qualquer exceção depois da reserva e antes do `UPDATE` (por exemplo, falha ao gravar o log), apague a linha reservada (`DELETE`), para que a reentrega processe, e devolva `falha interna`.
4. **Duplicado também vai para o log:** grave uma linha com `"tipo": "duplicado"`, a chave e o timestamp, sem texto. Atualize em `docs/producao.md` a métrica "taxa de duplicados", que passa a sair do log.
5. **Testes** (`test_f8.py`):
   - "pedido 1111" e "pedido 2222" sem `event_id` → chaves diferentes, os dois processados;
   - o mesmo texto bruto e o mesmo canal duas vezes seguidas → o 2º é duplicado;
   - **corrida:** 6 processos (`multiprocessing`, com barreira; função de trabalho no nível do módulo, para funcionar com *spawn* no Windows) × 10 eventos com o mesmo `event_id` cada → exatamente 1 decisão por evento no log, 0 "falha interna", os demais com `duplicado = True`;
   - exceção forçada na gravação do log (monkeypatch) → a reserva é liberada e uma 2ª chamada processa normalmente;
   - duplicado grava linha `tipo = duplicado`.
   Use `TRIAGEM_RUNTIME_DIR` temporário em todos.

## Parte B — Limiar e política escolhidos fora do holdout (falha 3)

1. `solution/f8_oof.py`: no **treino** (`split_grupo == treino`), use `StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)` com `groups = group_id`, o mesmo pipeline da F3 e predições fora da dobra (`predict_proba`). Saída: `solution/outputs/f8_probs_oof_treino.csv` (sem texto).
2. Sobre as predições fora da dobra, aplique **as mesmas funções e regras** já registradas: a curva e as faixas de `f3_faixas.py`, com o mesmo *e*_Q2 = 3,82% e o mesmo IC, e a regra por categoria de `f4_politica.py`. Obtenha `t_decide`, `t_sugere` e a política por categoria. **Não altere as regras nem os parâmetros.**
3. **Congele** esses limiares e essa política e aplique-os **uma única vez** no holdout por grupo. Reporte cobertura e precisão, com IC de Wilson 95%, de cada faixa, no geral e por categoria. Saídas: `f8_faixas.json` e `f8_politica_por_categoria.csv` (mesmas colunas que o triagem lê hoje).
4. **Economia** (cenário A, grade 3 × 3) com a nova cobertura de "IA decide" → `f8_economia.csv`.
5. **Dano da injeção:** rode de novo só o `dano_ampliado` do clássico com a nova política (sem LLM) → chave `dano_ampliado_f8` em `f5_injecao.json`. A amostra do LLM da F3 continua a definida pelo limiar antigo; registre isso.
6. `triagem.carregar_politica` passa a ler `f8_faixas.json` e `f8_politica_por_categoria.csv`. Os arquivos `f3_faixas.json` e `f4_politica_por_categoria.csv` ficam como histórico.
7. **Portão de qualidade:** mantenha os mínimos (acurácia ≥ 0,84 e precisão de "IA decide" ≥ 0,97). Se a nova política não passar no holdout, **não baixe o mínimo**: reporte e pare.
8. Os números que saírem são os números. Nenhum ajuste depois de ver o holdout.

## Parte C — Versão do modelo e rollback executável (falha 4)

- `modelo_versao` = SHA-256 de (SHA-256 de `f1_splits.csv` + `PARAMS`), 12 caracteres. Arquivo: `modelo_cache/modelo_<versao>.joblib`. Diretório configurável por `TRIAGEM_CACHE_DIR`, para os testes.
- `TRIAGEM_MODELO_VERSAO=<versao>` carrega essa versão, se o arquivo existir; se não existir, `triar` vai para o fallback ("falha do classificador"), sem treinar. Sem a variável, usa a versão atual e treina se faltar.
- **Nunca apague versões antigas.**
- Atualize o rollback de modelo em `docs/producao.md`: definir `TRIAGEM_MODELO_VERSAO` para a versão anterior, que precisa estar guardada.
- Teste: duas versões falsas num cache temporário; a variável escolhe qual carregar; uma versão inexistente vira fallback.

## Parte D — Pequenas (falha 5)

- A aba "lote" do app roda com um runtime separado (`runtime/demo/`), restaurando a variável de ambiente ao final, para não poluir o log real.
- O app checa o retorno de `registrar_correcao` e mostra erro quando ele for `False`.
- Em Limitações do README, uma linha: o treino usa texto sem máscara e a inferência usa texto mascarado; o efeito é desprezível no DS2, que tem 0 dado pessoal por regex (`f1_ds2_auditoria.json`).

## Parte E — App e screenshots

1. **Cartão de resultado** na aba "ticket", sem JSON cru:
   - a faixa com cor: `st.success` para IA decide, `st.warning` para IA sugere, `st.error` para humano decide;
   - `st.metric` para a categoria e a confiança em %;
   - uma linha **"Por que esta faixa"** gerada pelo caminho real da decisão: confiança × limiar, teto da política da categoria, regra de ação, texto insuficiente, possível injeção, duplicado ou modo sombra;
   - uma tabela com as duas categorias mais prováveis e suas %;
   - os termos do motivo;
   - o JSON completo num `st.expander("detalhe técnico")`;
   - o seletor de tipo com `index=None` e placeholder "—".
2. **Aba "Política":** a tabela de `f8_politica_por_categoria.csv` (categoria, política, precisão com IC, n).
3. **Aba "lote":** cobertura e precisão em %, uma coluna com o valor de referência do holdout (`f8_faixas.json`), um gráfico de barras da cobertura por faixa e as linhas dentro de um `st.expander`.
4. `.streamlit/config.toml` **na raiz da submissão** (onde se roda `streamlit run solution/app.py`), com `[client] toolbarMode = "viewer"`.
5. **Screenshots** com Playwright, página inteira, largura 1280, `deviceScaleFactor = 2`, runtime temporário:
   - `1_ia_decide.png`, `2_ia_sugere.png`, `3_humano_politica.png` (um ticket de categoria em "humano decide"), `4_reembolso.png` (ticket de alta confiança com `tipo = Refund request`), `5_duplicado.png` (o mesmo `event_id` enviado de novo), `6_lote.png`, `7_politica.png`;
   - os tickets vêm **só** dos ids de `f4_exemplos_ids.csv`, cujos trechos já estão em `docs/politica.md`. Confira a faixa de cada um com a política nova antes de capturar; se um id não cair mais na faixa desejada, use outro da mesma lista e registre;
   - remova `f5_app_ticket.png` e `f5_app_lote.png` com `git rm`.
6. No README, em Resultados, embuta `2_ia_sugere.png` e `6_lote.png` (`![...](process-log/screenshots/...)`) e liste os demais.

## Parte F — Documentos, process log, commit

1. Atualize memo, README e docs com os números da parte B. Faça um `grep` por `0,74`, `57,17`, `12,98`, `13,0`, `31,41`, `55,61`, `98,87`, `98,9`, `97,37`, `52,84`, `34,18`, `6.815`, `6,8 mil`, `3,2 mil`, `13 mil`, `1.242`, `6.210` e `898` em `README.md`, `docs/*.md` e `process-log/process-log.md`. Troque cada ocorrência nos textos da entrega. **No process log, não reescreva as linhas históricas:** acrescente a linha da F8 dizendo o que mudou, de quanto para quanto. Liste cada troca no report.
2. Na seção "Abordagem" do README: "limiar e política escolhidos com predições fora da dobra no treino; holdout usado uma única vez".
3. Process log:
   - linha da F8, com "Decisão minha" vazia;
   - na tabela de erros, quatro entradas:
     - colisão de chave: F5-spec (chat) omitiu a janela de tempo do `fluxo.md` e permitiu o hash normalizado;
     - corrida check-then-insert (implementação da F5);
     - limiar e política escolhidos no holdout (desenho da F3/F4-spec, chat);
     - rollback de modelo não executável (F6).
   - Em todas: "detectado na revisão pré-push pedida pelo Gustavo; 1 e 2 reproduzidos antes da correção".
4. Checagens: `pytest`; `f1_splits.csv` com o mesmo hash; add filtrado e `git diff --cached --name-only` com as regras de aborto da F5 (inclui abortar se houver `runtime/` ou `modelo_cache/`); checagem de segredo; nenhum `[GUSTAVO`; texto do DS2 só nas 3 exceções, mais os screenshots, que usam só trechos já em `docs/politica.md`.
5. Commit: `F8: idempotência sem colisão nem corrida, limiar fora do holdout, modelo versionado, app e screenshots`. Sem push.
6. `planning/F8-report.md` no formato da seção 8 do `CLAUDE.md`, com uma tabela antes × depois dos números de capa.
