# Resiliência

O objetivo é um só: o vendedor abre a ferramenta e vê a lista, mesmo com a API lenta, fora do ar ou sob carga. Cada padrão abaixo protege uma dependência real; o domínio, que não faz I/O, não tem nenhum (ver [ADR 0008](adr/0008-resiliencia-so-onde-ha-dependencia.md)).

Os parâmetros são os do código; as linhas citam onde mudar.

## Na web: a dependência é a API

Ordem em cada chamada: `retry( disjuntor( tentativa com timeout ) )`, e por fora o cliente resiliente decide entre API e modo local.

### Timeout por requisição

| | |
|---|---|
| Protege | o vendedor de esperar uma API que não responde |
| Parâmetro | **4.000 ms** (`TIMEOUT_PADRAO_MS`, `apps/web/src/infra/clienteHttp.ts`) |
| Como | `AbortController`; o prazo cobre cabeçalhos **e corpo** da resposta (o corpo é lido dentro da tentativa) |
| Erro | `ErroCliente('timeout')`, tratado como transitório |
| Testes | `clienteHttp.test.ts` ("aborta pelo timeout e marca como transitório"); `resiliencia-regressao.test.ts` ("o timeout cobre o corpo: o cabeçalho chega, o corpo trava, e vale o timeout") |

### Retry com backoff exponencial e jitter

| | |
|---|---|
| Protege | contra falha passageira (rede, API reiniciando, 429) |
| Parâmetros | **3 tentativas** no total, **base 200 ms**, **teto 2.000 ms** (`RETRY_PADRAO`, `apps/web/src/infra/retry.ts`) |
| Espera | full jitter: sorteada entre 0 e `min(teto, base · 2ⁿ)` depois da falha n |
| Repete | só erro transitório: rede, timeout, HTTP 429, 502, 503 e 504 (`ErroCliente.transitorio`, `erros.ts`) |
| Não repete | erro de entrada (4xx), erro 500 e outros 5xx não listados acima, operação não idempotente. Todas as operações do cliente são leitura ou cálculo puro, marcadas idempotentes em `cliente.ts` |
| `Retry-After` | um 429 com `Retry-After` espera o tempo pedido se couber no teto (2 s); se passar, desiste na hora |
| Testes | `retry.test.ts` (8 casos: limites do jitter, 3 tentativas, desiste na terceira, nunca repete 4xx nem não idempotente, respeita e recusa o `Retry-After`, rede e timeout transitórios); `clienteHttp.test.ts` ("repete um 503", "não repete 400") |

### Circuit breaker (disjuntor)

| | |
|---|---|
| Protege | a API de ser martelada quando já está caindo, e o vendedor de esperar 3 tentativas a cada clique |
| Parâmetros | **abre com 3 falhas seguidas**, fica **aberto 15.000 ms** (`DISJUNTOR_PADRAO`, `apps/web/src/infra/disjuntor.ts`) |
| Conta como falha | `falhaDoServidor`: rede, timeout, 429 e **qualquer 5xx** (inclusive 500, que não é repetido) |
| Não conta | erro de entrada (4xx): a API está de pé |
| Meio-aberto | vencidos os 15 s, deixa passar **uma** sonda por vez: sucesso fecha, falha reabre por mais 15 s; um 4xx na sonda também fecha (a API respondeu) |
| Gerações | cada troca de estado abre uma geração; o resultado de uma requisição que começou antes da última troca não muda o estado (um sucesso atrasado não fecha o circuito, uma falha atrasada não estende a abertura) |
| Detalhe | como cada tentativa do retry passa pelo disjuntor, uma operação que esgota as 3 tentativas já abre o circuito |
| Testes | `disjuntor.test.ts` (6 casos: abre em 3, sucesso zera, 4xx não conta, sonda fecha, sonda reabre, uma sonda por vez); `resiliencia-regressao.test.ts` (gerações; 500 conta como falha); `clienteHttp.test.ts` ("três falhas de rede abrem o disjuntor e a chamada seguinte nem sai") |

### Fallback: modo local

| | |
|---|---|
| Protege | a lista do vendedor quando a API não serve |
| Quando cai | circuito aberto, ou falha do servidor depois do retry (rede, timeout, 429, 5xx) |
| O que faz | baixa `/dados/deals.json` e o `.sha256`, confere o SHA-256, valida o schema e roda o **mesmo** `criarServicos` do domínio no navegador (`clienteLocal.ts`); carrega uma vez e, se falhar, tenta de novo na próxima operação |
| Aviso na tela | "Sem conexão com o servidor. A lista foi calculada aqui no seu navegador." (texto da política) |
| Volta para a API | a cada **15 s** no modo local, a web pergunta a `/health` (`apps/web/src/app/contexto.tsx`); se responde, volta. Só um sucesso que começou depois da última queda volta o modo, para o aviso não piscar |
| Rota que a API não conhece | 404 `nao_encontrado` (API mais antiga que a web): responde pelo local sem trocar o modo |
| Não cai | erro de entrada (4xx): o pedido é que está errado |
| Testes | `clienteResiliente.test.ts` (5 casos); `resiliencia-regressao.test.ts` ("erro 500 responde pelo modo local", "um sucesso atrasado, de antes da queda, não volta o modo para api"); `clienteLocal.test.ts` (mesmo resultado do domínio, checksum que não bate é recusado); E2E "API derrubada → banner de modo local e a segunda-feira continua" (`e2e/testes/fluxos.spec.ts`, vídeo em `e2e/videos/`) |

## Na API: a dependência é o próprio cálculo

Ordem dos middlewares (`apps/api/src/app.ts`): log → cabeçalhos de segurança → `Host` → CORS → rate limit → limite de corpo → timeout → rota. O CORS vem antes do rate limit para que o navegador consiga ler o 429.

### Rate limit (token bucket por IP)

| | |
|---|---|
| Protege | o cálculo da fila (2.089 abertos, recalculados a cada pedido) contra um cliente que dispara sem parar |
| Parâmetros | **capacidade 60**, **recarga 2 por segundo**, limpeza de baldes ociosos a cada **60.000 ms**, teto de **10.000 baldes** na memória (`LIMITE_TAXA_PADRAO`, `apps/api/src/infra/limite-taxa.ts`) |
| Ajuste | `RATE_LIMIT_CAPACIDADE`, `RATE_LIMIT_RECARGA_POR_SEGUNDO` (`apps/api/src/infra/config.ts`); valor inválido não sobe o servidor |
| Resposta | 429 `limite_de_taxa` com `Retry-After` em segundos, arredondado para cima |
| Escopo | só `/api/*`; `/health` fica fora (é do monitoramento) |
| Chave | IP do socket, nunca `X-Forwarded-For` (sem proxy na frente, o cabeçalho seria do próprio cliente) |
| Teto de memória | cheio, limpa os ociosos e, se precisar, descarta o balde mais antigo |
| Limites | em memória, por processo; atrás de um proxy, o limite valeria para o proxy inteiro |
| Testes | `apps/api/test/protecoes.test.ts` (estoura na 4ª com capacidade 3, `Retry-After`, recarga, um balde por IP, `/health` fora, 429 com cabeçalhos e CORS, limpeza); `apps/api/test/borda.test.ts` ("a memória dos baldes tem teto") |

### Limite de corpo

| | |
|---|---|
| Protege | a memória do processo contra corpo gigante |
| Parâmetro | **1.048.576 bytes (1 MB)** (`CONFIG_PADRAO.payloadMaxBytes`); ajuste por `PAYLOAD_MAX_BYTES` |
| Resposta | 413 `payload_grande` |
| Junto | os schemas limitam o conteúdo: até 2.500 registros de respostas na fila, até 50 respostas por negócio, textos de filtro até 80 caracteres |
| Testes | `protecoes.test.ts` ("corpo acima de 1 MB → 413", "corpo abaixo do limite passa para a validação") |

### Timeout por requisição

| | |
|---|---|
| Protege | o cliente de esperar sem fim |
| Parâmetro | **5.000 ms** (`CONFIG_PADRAO.tempoLimiteMs`); ajuste por `TIMEOUT_MS` |
| Resposta | 503 `tempo_esgotado` (a web trata como transitório e repete) |
| Limite | o Node não interrompe código síncrono: o cálculo da fila não é cortado no meio. A fila inteira cabe no limite, medido em `apps/api/test/integracao.test.ts` |
| Testes | `protecoes.test.ts` ("requisição que passa do limite → 503", "dentro do limite responde normalmente") |

### O banco compartilhado (opcional)

Com `DATABASE_URL`, as respostas e decisões vão para um Postgres. A API protege essa dependência:
- **Limites curtos:** 3 conexões, 3 s para conectar, 4 s por consulta (`apps/api/src/infra/banco.ts`).
- **Disjuntor:** 3 falhas seguidas abrem o circuito por 30 s; aberto, a API nem tenta o banco. Passado o tempo, uma tentativa passa e um sucesso fecha.
- **Queda para a memória:** com o banco fora, grava e lê na memória do processo e responde `armazenamento: "memoria"`; a web então trata as respostas como deste navegador. Quando o banco volta, a leitura junta as linhas que ficaram na memória.
- **Na partida:** se o banco não responde ou o metadado dele não bate com o `deals.json`, a API sobe com o arquivo e diz no log por quê.
- **Na web:** gravar no servidor não tem retry (não é idempotente) e falha não é erro: a resposta já está no navegador.

Testes: `apps/api/test/banco.test.ts` (banco falso que falha, disjuntor que abre e fecha, metadado divergente).

### Saúde e partida

- `GET /health` devolve status, versão, total de negócios, referência e o SHA-256 conferido; fica fora do rate limit.
- O servidor não sobe com dado que não confere (checksum, JSON ou schema) nem com config inválida (`PORT` fora de 1 a 65535, número não positivo nas variáveis da borda): sai com código 1 e a mensagem do motivo (`apps/api/src/servidor.ts`).
- `SIGINT`/`SIGTERM` fecham o servidor; se não fechar em 3 s, o processo sai.
