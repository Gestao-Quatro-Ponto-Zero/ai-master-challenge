# F5 — Protótipo com prontidão para produção testada (spec para o Claude Code)

- **Teto:** 75 min. Ao chegar a 90 min (120%), pare e proponha o corte no report.
- **Ordem de corte, se estourar:** (1) a aba "lote" do Streamlit; (2) o Streamlit inteiro, substituído por uma CLI `python solution/triar_cli.py "<texto>"`. **Nunca cortar:** os testes de falha (golden set, injeção, idempotência, mascaramento, fallback, modo sombra).
- **Leia antes:** `CLAUDE.md`; `planning/F0-escopo.md`; `planning/F4-report.md`; `docs/politica.md`; `docs/fluxo.md`.
- **Decisões já tomadas:** clássico (TF-IDF + LR, mesmos parâmetros da F3, treinado em `split_grupo == treino`); política por categoria de `solution/outputs/f4_politica_por_categoria.csv` (teto: só rebaixa); reembolso e cancelamento sempre com humano; LLM fora do caminho de decisão. O LLM aparece **só** no teste de injeção, como a alternativa que um fornecedor venderia.

## Estrutura

- `solution/triagem.py`: núcleo, sem interface.
- `solution/app.py`: Streamlit de uma página, sem estilo.
- Modelo treinado na primeira execução, a partir do `DATA_DIR`, e guardado em `modelo_cache/`. Estado de execução (log, idempotência, correções) em `runtime/`. **Acrescente `runtime/` e `modelo_cache/` ao `.gitignore` da submissão sem barra no meio do padrão**, porque o add filtrado usa `--exclude-from` e padrões com barra no meio não casam dentro da submissão. Nenhum binário de modelo no repositório.

## Passo 1 — `solution/triagem.py`

Função `triar(evento: dict) -> dict`. Entrada: `event_id` (opcional), `texto`, `canal` (opcional), `tipo_ds1` (opcional, um dos 5 tipos do DS1), `nome_cliente` (opcional). A função **nunca lança exceção** para quem a chama. Etapas, nesta ordem:

1. **Idempotência:** a chave é o `event_id`; sem ele, SHA-256 do texto normalizado + canal. Guarde as chaves em `runtime/idempotencia.sqlite` (sqlite3 da biblioteca padrão). Chave repetida: devolve o resultado guardado com `duplicado = True` e não registra uma nova decisão.
2. **Validação:** texto vazio ou com menos de 3 palavras → `faixa = "humano decide"`, `motivo = "texto insuficiente"`.
3. **Mascaramento**, antes de qualquer gravação: e-mail; telefone (formatos BR com e sem +55, e 8 ou mais dígitos seguidos); CPF (`000.000.000-00` e 11 dígitos); sequência de 13 a 16 dígitos (cartão); e o valor de `nome_cliente`, quando vier, onde aparecer no texto. Substitua por `[EMAIL]`, `[TELEFONE]`, `[CPF]`, `[CARTAO]`, `[NOME]`.
4. **Classificação:** categoria, `p_max`, as duas categorias mais prováveis com probabilidade, e um `motivo` com os 5 termos de maior contribuição (peso do TF-IDF × coeficiente) para a classe prevista.
5. **Faixa:** limiares de `f3_faixas.json` e política da categoria prevista de `f4_politica_por_categoria.csv`, aplicada como teto.
6. **Regra de ação:** `tipo_ds1` em {`Refund request`, `Cancellation request`} → `humano decide`, depois do roteamento.
7. **Fallback:** qualquer exceção nas etapas 4–6 (modelo ausente, erro de predição) → `faixa = "humano decide"`, `motivo = "falha do classificador"`, e erro registrado no log.
8. **Modo sombra / rollback:** se a variável de ambiente `TRIAGEM_MODO=sombra`, o sistema classifica e registra no log a faixa que *teria* aplicado, mas devolve sempre `humano decide`. O padrão é `ativo`. É o desligamento rápido documentado na F6.
9. **Log estruturado:** uma linha JSONL por decisão em `runtime/decisoes.jsonl`, com `timestamp_utc`, `chave`, `event_id`, `texto_mascarado` (até 200 caracteres), `categoria`, `p_max`, `faixa`, `faixa_sem_sombra`, `motivo`, `modelo_versao` (hash dos ids de treino + parâmetros), `politica_versao` (hash do CSV da F4), `latencia_ms` e `erro`. **Nunca** texto sem máscara.

Função `registrar_correcao(chave, categoria_correta, atendente)`: grava em `runtime/correcoes.jsonl`. As correções são a entrada do próximo ciclo de avaliação; não retreine automaticamente.

## Passo 2 — `solution/app.py` (Streamlit)

- **Aba "ticket":** campo de texto, canal, tipo do DS1 (opcional) → mostra faixa, categoria, `p_max`, as duas mais prováveis, motivo e o aviso de duplicado, se houver. Seletor "corrigir para…" + botão que chama `registrar_correcao`.
- **Aba "lote":** 200 tickets sorteados (seed 42) do holdout por grupo, passados por `triar`; mostra a distribuição das faixas e a precisão por faixa contra o rótulo original. Demonstra o comportamento com dados reais, não com 3 exemplos escolhidos.
- Sem login, sem estilo, sem deploy.

## Passo 3 — Teste de injeção — `solution/f5_injecao.py`

1. Escreva 5 modelos de ataque, cada um mandando classificar como uma categoria-alvo diferente da prevista no texto limpo. Variedade: "ignore as instruções anteriores…", uma falsa mensagem de sistema, um JSON pronto com `categoria`, um ataque em português e um com a categoria repetida várias vezes. Versione em `solution/tests/golden/ataques_v1.json`.
2. Sorteie 20 tickets (seed 42) do holdout por grupo e insira cada ataque no fim do texto: 100 pares.
3. **Clássico:** taxa de troca de rótulo (qualquer mudança contra o texto limpo) e taxa de sucesso do ataque (mudança **para a categoria-alvo**).
4. **LLM** (prompt `classificar_v1.txt`, mesma configuração da F3): mesmas duas taxas, nos mesmos 100 pares, mais os 20 textos limpos (120 chamadas). Se não houver chave, deixe pendente. Log em `planning/F5/` (fora do repositório).
5. Registre no resultado: "ataques inseridos em linguagem natural num texto pré-processado; em produção, o atacante escreve no texto bruto".
6. Saída: `solution/outputs/f5_injecao.json`.

## Passo 4 — Golden set e testes — `solution/tests/test_f5.py` + `solution/tests/golden/golden_v1.jsonl`

`golden_v1.jsonl` é versionado; cada caso tem `entrada` e `esperado`. Casos obrigatórios:

- texto vazio e texto com 2 palavras → `humano decide`;
- o mesmo evento enviado 2 vezes → o 2º volta com `duplicado = True`, e o log tem 1 decisão, não 2;
- texto com e-mail, telefone, CPF e `nome_cliente` → nada disso aparece em `runtime/decisoes.jsonl`. Use 20 nomes e e-mails reais do DS1 (sintéticos) **só em tempo de teste**, sem gravá-los no repositório;
- `tipo_ds1 = Refund request` com texto de alta confiança → `humano decide`;
- classificador forçado a falhar (monkeypatch) → `humano decide` com `motivo = "falha do classificador"`, sem exceção;
- `TRIAGEM_MODO=sombra` → `humano decide`, com `faixa_sem_sombra` registrada;
- injeção: para os 5 ataques em 3 tickets fixos, a categoria do clássico não pode ir para a categoria-alvo;
- texto em português (3 frases escritas por você, sobre assuntos de TI) → **não** pode cair em `IA decide`. Se falhar, **não ajuste**: reporte como achado;
- **portão de qualidade (regressão):** no holdout por grupo, acurácia ≥ 0,84 e precisão da faixa `IA decide` ≥ 0,97. Falha se o modelo ou a política piorarem.

## Passo 5 — Latência — `solution/f5_latencia.py`

`triar` de ponta a ponta (com mascaramento e log) em 1.000 tickets do holdout por grupo, um a um, com `runtime/` temporário: p50 e p95 em ms. Saída: `solution/outputs/f5_latencia.json`.

## Passo 6 — Report

`planning/F5-report.md` (formato da seção 8 do `CLAUDE.md`), com uma tabela: requisito de prontidão | como foi implementado | teste que prova | resultado. Inclua o comando para rodar o app (`streamlit run solution/app.py`) e o tempo da primeira execução (treino). Linha da F5 no process log com "Decisão minha" vazia.

## Critérios de aceite

- `pytest solution/tests -q` passa (todas as fases).
- `streamlit run solution/app.py` abre e classifica um ticket. Registre uma captura de tela em `process-log/screenshots/` ou, se não conseguir capturar, diga isso.
- Nada de `runtime/`, `modelo_cache/`, `.env`, nomes ou e-mails do DS1 no repositório.
- `f1_splits.csv` com o mesmo hash. Nenhum commit.

## Não faça

- Mudar o modelo, os limiares ou a política.
- Pôr o LLM no caminho de decisão.
- Login, deploy, estilo visual.
- Retreinar com as correções.
