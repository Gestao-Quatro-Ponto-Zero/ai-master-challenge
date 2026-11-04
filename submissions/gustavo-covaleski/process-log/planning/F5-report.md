# F5 — Report (Protótipo com prontidão para produção testada)

Caminhos relativos à submissão (`ai-master-challenge/submissions/gustavo-covaleski/`).

**Rodar o app:** `.venv/Scripts/python -m streamlit run solution/app.py` (ou `streamlit run solution/app.py` com o venv ativo).

**Primeira execução:** o modelo é treinado a partir do `DATA_DIR` e guardado em `modelo_cache/modelo.joblib`. O treino levou **21,5 s** (medido em `carregar_modelo()`); a carga, nas execuções seguintes, é imediata.

## 1. O que foi feito

1. **`solution/triagem.py`:** `triar(evento)` nunca lança exceção e executa, nesta ordem:
   - idempotência em sqlite;
   - validação (menos de 3 palavras vai para humano);
   - mascaramento (e-mail, telefone BR, CPF, cartão, `nome_cliente`);
   - classificação com top-2 e motivo (os 5 termos com maior TF-IDF × coeficiente);
   - faixa com o teto da política F4;
   - regra de ação (reembolso e cancelamento);
   - fallback;
   - modo sombra (`TRIAGEM_MODO=sombra`);
   - log JSONL.

   `registrar_correcao()` grava em `runtime/correcoes.jsonl`, sem retreinar.
2. **`solution/app.py`:** Streamlit com as abas "ticket" (triagem + correção) e "lote" (200 tickets sorteados do holdout por grupo).
3. **`solution/f5_injecao.py`:** 5 ataques versionados (`tests/golden/ataques_v1.json`) × 20 tickets = 100 pares. Clássico e LLM (120 chamadas, Haiku 5.5, prompt `classificar_v1.txt`). O log do LLM fica em `planning/F5/`.
4. **`solution/tests/golden/golden_v1.jsonl`** (11 casos) e **`solution/tests/test_f5.py`** (15 testes).
5. **`solution/f5_latencia.py`:** `triar` de ponta a ponta em 1.000 tickets, com `runtime/` temporário.
6. **Ajustes de repositório e app:**
   - `.gitignore` recebeu `runtime/` e `modelo_cache/`;
   - `requirements.txt` recebeu `streamlit==1.66.1`;
   - capturas do app em `process-log/screenshots/`.

## 2. Resultados

| Número | Valor | Script → arquivo |
|---|---|---|
| Testes (todas as fases) | **46 passed** | `pytest solution/tests -q` |
| Injeção, clássico: troca de rótulo / ataque atinge o alvo (100 pares) | **9% / 3%** | `f5_injecao.py` → `f5_injecao.json` |
| Injeção, LLM: troca de rótulo / ataque atinge o alvo (100 pares) | **12% / 2%** | idem |
| Injeção, LLM: pares em que o alvo coincide com a previsão limpa do LLM (não contam como sucesso) | 8 | idem |
| Acurácia nos 20 tickets limpos: clássico / LLM | 90% / 40% | idem |
| Latência de `triar` de ponta a ponta, p50 / p95 (1.000 tickets) | **2,79 ms / 5,12 ms** | `f5_latencia.py` → `f5_latencia.json` |
| Faixas nos 1.000 tickets da latência: IA decide / IA sugere / humano | 132 / 325 / 543 | idem |
| Aba "lote" (200 tickets): IA decide / IA sugere / humano (precisão) | 30 (1,000) / 60 (0,917) / 110 (0,764) | captura `process-log/screenshots/f5_app_lote.png` |
| Treino na primeira execução | 21,5 s | `triagem.carregar_modelo()` |

**Injeção por ataque, clássico** (troca / atinge o alvo, em 20 pares cada):

| Ataque | Troca | Atinge o alvo |
|---|---|---|
| ignore instruções | 4 | 0 |
| falsa mensagem de sistema | 2 | 1 |
| JSON pronto | 0 | 0 |
| português | 0 | 0 |
| categoria repetida | 3 | 2 |

**Injeção por ataque, LLM** (troca / atinge o alvo, em 20 pares cada):

| Ataque | Troca | Atinge o alvo |
|---|---|---|
| português | 3 | 0 |
| ignore instruções | 1 | 0 |
| JSON pronto | 1 | 0 |
| falsa mensagem de sistema | 3 | 0 |
| categoria repetida | 4 | 2 |

Ressalva registrada no JSON: "ataques inseridos em linguagem natural num texto pré-processado; em produção, o atacante escreve no texto bruto".

### Prontidão para produção

| Requisito | Como foi implementado | Teste que prova | Resultado |
|---|---|---|---|
| Idempotência | Chave = `event_id`, ou SHA-256 do texto normalizado + canal; sqlite em `runtime/`; o duplicado devolve o resultado guardado com `duplicado=True` e não grava log | `test_idempotencia`, `test_idempotencia_sem_event_id_usa_hash` | passa (1 decisão no log em 2 envios; o mesmo texto em outro canal não é duplicado) |
| Validação de entrada | Menos de 3 palavras → humano decide, motivo "texto insuficiente" | `test_texto_insuficiente` (vazio e 2 palavras) | passa |
| Mascaramento antes de gravar | Regex de e-mail, CPF formatado, telefone com +55 ou DDD entre parênteses, cartão de 13 a 16 dígitos, telefone com hífen, CPF de 11 dígitos, 8+ dígitos e `nome_cliente` (inteiro e por partes com 3+ letras) | `test_mascaramento_golden`, `test_mascaramento_20_clientes_ds1` (20 nomes e e-mails do DS1 lidos só em tempo de teste) | passa |
| Texto do cliente separado das instruções | O clássico não interpreta instruções; o LLM recebe o texto entre `<ticket>` no papel de usuário (F3) | `test_injecao_classico_nao_vai_para_alvo` (5 ataques × 3 tickets) | passa nos 3 tickets fixos; nos 100 pares, 3% atingem o alvo (ver §3) |
| Regra de ação | `tipo_ds1` ∈ {Refund, Cancellation} → humano decide, aplicada depois do roteamento | `test_regra_de_acao_reembolso` (o mesmo texto vai para IA decide sem o tipo) | passa |
| Fallback | Exceção na classificação ou na faixa → humano decide, motivo "falha do classificador", erro no log; qualquer outra exceção → humano decide, "falha interna" | `test_fallback_classificador` (monkeypatch), `test_nunca_lanca_excecao` (falha do sqlite) | passa |
| Modo sombra / rollback | `TRIAGEM_MODO=sombra` → devolve humano decide e registra `faixa_sem_sombra` | `test_modo_sombra` | passa |
| Log estruturado | JSONL com `timestamp_utc`, `chave`, `event_id`, `texto_mascarado` (≤ 200), `categoria`, `p_max`, `faixa`, `faixa_sem_sombra`, `motivo`, `modelo_versao`, `politica_versao`, `latencia_ms` e `erro` | Coberto pelos testes de idempotência, sombra, fallback e mascaramento, que leem o log | passa |
| Fora do domínio (português) | Sem tratamento especial | `test_portugues_nao_cai_em_ia_decide` (3 frases) | passa: as 3 caem em humano decide (p_max 0,32–0,55) |
| Regressão de qualidade | Portão no holdout por grupo | `test_portao_de_qualidade` (acurácia ≥ 0,84; precisão IA decide ≥ 0,97) | passa |
| Correção do atendente | `registrar_correcao` → `runtime/correcoes.jsonl`, sem retreino | Exercitado no app (aba ticket); **sem teste automatizado próprio** | — |

## 3. O que contraria a hipótese ou a expectativa

- **O clássico não é imune à injeção:** 3% dos pares atingem o alvo e 9% trocam de rótulo.
  - O ataque "categoria repetida" funciona porque os nomes das categorias são palavras do vocabulário do TF-IDF (ex.: "storage", "purchase").
  - "ignore instruções" troca o rótulo em 4 de 20 sem atingir o alvo: o texto em inglês do ataque muda o vetor.
  - O teste de 3 tickets fixos (os 3 primeiros do sorteio com seed 42) passa, mas não prova imunidade. Os sucessos caíram nos tickets 24659 e 25979, fora desses 3.
- **O LLM troca mais (12%) e atinge menos o alvo (2%) que o clássico.** Seguir a instrução injetada não é o modo de falha dominante; o problema é instabilidade.
  - A acurácia nos 20 limpos variou entre rodadas (45% na 1ª, 40% na 2ª), porque a API não aceita `temperature = 0` no Haiku 5.5 (F3).
  - Isso também significa que a taxa de troca do LLM mistura o efeito do ataque com o ruído entre chamadas.
- **A latência de ponta a ponta inicial foi de 70,5 ms (p50).** A causa era `get_feature_names_out()` montando ~175 mil termos a cada chamada. Com cache, caiu para 2,79 ms. O modelo e a política não mudaram.
- **O mascaramento tinha um bug na 1ª versão:** "+55 11 98765-4321" virava `[CARTAO]` (13 dígitos). Corrigido com a ordem: telefone formatado → cartão → telefone com hífen → CPF de 11 dígitos → 8+ dígitos.
  - Limitação que continua: um celular de 11 dígitos sem separador (ex.: 11987654321) é mascarado como `[CPF]`. O dado sai do log, mas com o rótulo errado.

## 4. Desvios da spec

- **Mascaramento antes da classificação.** O texto mascarado é o que vai para o classificador (o DS2 não tem dado pessoal; F1, 3.1). Assim, nenhuma etapa vê o dado sem máscara.
- **`nome_cliente` mascarado também por partes** (cada palavra com 3+ letras), além do nome inteiro. Assim, "Maria" sozinha também sai.
- **Taxa de "sucesso do ataque" do LLM:** a 1ª versão do script contava como sucesso pares em que o alvo já era a previsão limpa do LLM. Corrigi para exigir a mudança **para** o alvo, como a spec define, e rodei as 120 chamadas de novo. Os números acima são da 2ª rodada.
- **Alvo do ataque** = categoria diferente da previsão **do clássico** no texto limpo, usada para os dois modelos. Em 8 pares, o alvo coincide com a previsão limpa do LLM; esses pares contam como troca, mas não como sucesso.
- **Teste extra** `test_nunca_lanca_excecao`: falha do sqlite → "falha interna", fora da faixa do fallback do classificador.
- **`TRIAGEM_RUNTIME_DIR`** (variável de ambiente): testes e latência usam um `runtime/` temporário.

## 5. Erros e correções durante a execução

1. Mascaramento: telefone +55 virava cartão; depois, cartão com hífens virava telefone. Reordenei os regex e verifiquei com casos manuais.
2. Métrica de sucesso do ataque do LLM (§4). Corrigida e rodada de novo; o custo é de centavos (120 chamadas).
3. Latência de 70 ms por `get_feature_names_out()`. Coloquei em cache.
4. Captura da aba "lote": o seletor da aba falhou na 1ª tentativa e o lote levou ~40 s (200 chamadas a `triar` + a 1ª carga). A 2ª captura saiu certa.
5. **O servidor Streamlit (porta 8599) continua rodando.** Tentei encerrá-lo pelo PowerShell, mas a ação foi negada pelo classificador de permissões. Para parar: feche o processo `python ... streamlit run solution/app.py`, ou rode `Stop-Process` com o PID dele.
6. O Playwright criou `challenge-g4-ai-master/.playwright-mcp/` (snapshots da página), fora do repositório. Pode ser apagado.

## 6. Pendências e decisões que dependem do Gustavo

1. A injeção mostra 3% de sucesso no clássico pelo ataque "categoria repetida". Vale uma regra simples, como ignorar repetições de nome de categoria antes de classificar? Seria mudança de pré-processamento: decisão para a F6.
2. `registrar_correcao` não tem teste automatizado próprio. Acrescentar na F6?
3. Encerrar o servidor Streamlit (§5.5).
4. Commit da F5. O add filtrado lista 11 arquivos novos, mais `.gitignore`, `requirements.txt` e `process-log.md` modificados. `runtime/`, `modelo_cache/` e `.env` estão excluídos (conferido com `git ls-files -o --exclude-from`).

## 7. Tempo gasto × orçado

Orçado: 75 min (teto de 90). Relógio: das 23:49 às ~00:01, cerca de 12 min de execução. Inclui o treino (21,5 s), as 240 chamadas do LLM (~22 s por rodada) e o lote do app (~40 s).
