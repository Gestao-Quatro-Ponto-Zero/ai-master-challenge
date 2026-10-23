# ADR 0008: Resiliência só onde há dependência

**Status:** aceita

## Contexto

O vendedor não pode ficar sem a lista na segunda de manhã. A solução tem duas dependências reais: a web depende da API (rede, processo de pé) e a API depende do próprio cálculo (CPU, memória), que um cliente pode martelar. O domínio é puro e não chama nada de fora. Pôr padrão de resiliência onde não há dependência só aumentaria código.

## Decisão

Na **web → API** (`apps/web/src/infra/`):
- timeout por requisição de 4 s, cobrindo cabeçalhos e corpo;
- retry com backoff exponencial e full jitter (3 tentativas, base 200 ms, teto 2 s), só em erro transitório (rede, timeout, 429, 502, 503, 504) e só em operação idempotente; respeita o `Retry-After` se couber no teto;
- disjuntor: 3 falhas seguidas abrem por 15 s; depois, uma sonda;
- fallback para o modo local ([ADR 0002](0002-api-fina-e-modo-local.md)).

Na **API** (`apps/api/src/infra/`):
- rate limit por IP (token bucket: 60 de uma vez, 2 por segundo depois);
- limite de corpo de 1 MB;
- timeout de 5 s por requisição;
- `Host` conferido, CORS restrito, cabeçalhos de segurança.

No **domínio**: nada. Ele não faz I/O (a checagem de fronteiras garante).

## Consequências

- Cada padrão tem parâmetro no código e teste que o prova; a lista está em [resiliencia.md](../resiliencia.md).
- O E2E derruba a API e a fila continua com o aviso de modo local.
- O timeout da API não interrompe cálculo síncrono (limite do Node). A fila inteira de 2.089 abertos cabe no limite: `apps/api/test/integracao.test.ts` mede.
- O rate limit vive na memória do processo; com várias instâncias, cada uma conta o seu.

## Alternativas consideradas

- **Biblioteca de resiliência pronta:** mais uma dependência para três padrões pequenos e testáveis.
- **Retry em tudo, inclusive 4xx:** repetiria pedido errado e somaria carga sem chance de sucesso.
- **Sem fallback local:** com a API fora, o vendedor ficaria sem a lista.
