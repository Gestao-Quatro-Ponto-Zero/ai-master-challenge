# Segurança

O que está em jogo: a lista de negócios do vendedor (dado comercial) e as respostas que ele dá. O desenho assume uso local ou numa rede interna, **sem login** ([ADR 0006](adr/0006-sem-autenticacao.md)). Abaixo, cada propriedade com a medida real e o limite escrito.

## Confidencialidade

| Medida | Onde | Limite |
|---|---|---|
| A API escuta só em `127.0.0.1` por padrão; com `HOST` fora do loopback, avisa no console ("expõe a API fora desta máquina; não há login") | `apps/api/src/servidor.ts` | Quem acessar a porta vê todos os negócios. Sem login, não há "só o que é seu" |
| `Host` conferido contra a lista do servidor: `localhost`, `127.0.0.1` e `[::1]` na porta dele, mais os hosts das origens do CORS. Fora da lista: 421 `host_invalido`. Impede que uma página de fora, que aponte o próprio domínio para 127.0.0.1 (DNS rebinding), leia a API | `apps/api/src/infra/seguranca.ts` (`hostPermitido`), `config.ts` (`hostsDoServidor`) | Se a API for publicada atrás de um domínio, o domínio precisa entrar na lista |
| CORS restrito às origens do Vite (`http://localhost:5173` e `http://localhost:4173`), só `GET` e `POST`, só o cabeçalho `Content-Type`, **sem credenciais** | `seguranca.ts` (`corsRestrito`), `config.ts`; ajuste por `CORS_ORIGENS` | Em `npm start` a web é da mesma origem e não precisa de CORS |
| `POST` sem `Content-Type: application/json` → 415 `tipo_nao_suportado`. Sem isso, um formulário de outra origem faria um POST "simples", sem o preflight do CORS | `apps/api/src/infra/erros.ts` (`lerJson`) | |
| Erro nunca devolve stack, caminho de arquivo nem o valor recebido: corpo padrão `{ erro: { codigo, mensagem, detalhes? } }`; exceção vira 500 `erro_interno` com mensagem genérica | `erros.ts`, `app.ts` | |
| Log de uma linha por requisição: método, caminho **sem query**, status e duração. Nunca o corpo. Erro interno é logado sem quebra de linha e cortado em 200 caracteres | `apps/api/src/infra/tempo.ts`, `app.ts` | |
| `Referrer-Policy: no-referrer`; `Cache-Control: no-store` em `/api` | `seguranca.ts` | |
| As respostas do vendedor ficam no navegador dele (`localStorage`) e vão à API para o cálculo e para o armazém do servidor (banco compartilhado ou memória) | `apps/web/src/infra/repositorio.ts`, `registrosHttp.ts` | Quem usa o mesmo navegador vê as respostas; sem login, qualquer um com acesso lê os registros pela API |
| **Banco com papel restrito.** A API se conecta por `DATABASE_URL` com um papel que só lê `deals`, `vendedores` e `metadados` e só lê e acrescenta em `respostas` e `decisoes` (schema `lead_scorer`). O código só monta `SELECT` e `INSERT`, com parâmetros (sem concatenar valor no SQL) | `apps/api/src/infra/banco.ts`, `qualificacao/armazem.ts`, `carregador.ts` | Um teste de integração confere que `UPDATE` e `DELETE` são recusados pelo papel |
| **Nenhum segredo no código.** O único segredo é a `DATABASE_URL`, que vem só do ambiente: nunca do código nem do repositório; o log nunca escreve a URL, e as mensagens de erro do banco saem numa linha, cortadas em 200 caracteres. As outras variáveis são de porta, host, caminho do dado e parâmetros da borda (`PORT`, `HOST`, `DEALS_PATH`, `SERVIR_WEB`, `RATE_LIMIT_*`, `TIMEOUT_MS`, `PAYLOAD_MAX_BYTES`, `CORS_ORIGENS`) | `servidor.ts`, `config.ts`, `infra/banco.ts` | |

## Integridade

| Medida | Onde | Limite |
|---|---|---|
| **Checksum do dado.** O SHA-256 do `deals.json` é conferido contra o `.sha256` antes de qualquer cálculo, na API e de novo no modo local da web. Divergente: a API não sobe; o modo local recusa | `packages/dominio/src/pipeline/index.ts` (`conferirChecksum`), `apps/api/src/carregador.ts`, `apps/web/src/infra/clienteLocal.ts` | O `.sha256` mora ao lado do arquivo: protege contra arquivo truncado, corrompido ou trocado por engano, não contra quem pode reescrever os dois. Para isso, assinatura |
| **Formato versionado.** `deals.json` com `formato: 2` e `total` igual ao número de negócios; respostas com `formato: 1`. Outro formato é recusado com mensagem clara | `pipeline/index.ts`, `qualificacao/http.ts` | |
| **Validação na fronteira.** Toda entrada da API passa por schema estrito (zod): campo a mais, tipo errado, id fora do padrão (8 caracteres A–Z/0–9), data fora do ISO, texto de filtro acima de 80 caracteres → 400 `entrada_invalida`, com o caminho do problema | schemas em `packages/dominio/src/*/http.ts`; `apps/api/src/infra/erros.ts` (`validar`) | |
| Respostas lidas do `localStorage` passam pelo mesmo schema; JSON quebrado ou formato errado é ignorado, não quebra a tela | `repositorio.ts` | O usuário pode editar o próprio `localStorage`; o schema limita o que entra, não quem escreveu |
| Respostas de outro negócio ou de outro método são recusadas (`respostas_invalidas`) | `packages/dominio/src/aplicacao/index.ts` | |
| Contestar uma ação exige motivo (3 a 280 caracteres) | `qualificacao/index.ts`, `qualificacao/http.ts` | |
| `X-Content-Type-Options: nosniff` em toda resposta | `seguranca.ts` | |

## Disponibilidade

Detalhe e parâmetros em [resiliencia.md](resiliencia.md).

| Medida | Limite |
|---|---|
| Rate limit por IP (60 de uma vez, 2 por segundo), 429 com `Retry-After`; teto de 10 mil baldes na memória | Em memória, por processo |
| Limite de corpo de 1 MB (413) | |
| Timeout de 5 s por requisição (503) | Não interrompe cálculo síncrono; a fila inteira cabe no limite (medido em `apps/api/test/integracao.test.ts`) |
| Na web: timeout de 4 s, retry com jitter, disjuntor e modo local com o mesmo domínio | O modo local precisa que `/dados/deals.json` seja servido |
| `PORT` validada (1 a 65535) e config da borda validada: valor inválido não sobe o servidor | |

## Autenticidade

| Medida | Limite |
|---|---|
| **Não há login.** "Quem é você?" escolhe a fila; não prova quem é. A tela diz que não é login | Qualquer um escolhe qualquer nome. Para escalar: SSO e autorização por papel |
| Sem cookie nem sessão; o CORS não libera credenciais | |
| A origem do dado é provada pelo checksum (ver Integridade) | Não é assinatura |

## Cabeçalhos e CSP

Em toda resposta, inclusive as de erro e o 429 (`apps/api/src/infra/seguranca.ts`, `cabecalhosDeSeguranca`):

| Cabeçalho | Valor |
|---|---|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Referrer-Policy` | `no-referrer` |
| `Cross-Origin-Resource-Policy` | `same-origin` |
| `Content-Security-Policy` (API e `/health`) | `default-src 'none'; frame-ancestors 'none'` |
| `Content-Security-Policy` (web servida pela API) | `default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'` |
| `Cache-Control` (só `/api`) | `no-store` |

A web não usa script inline nem de terceiros. As fontes vêm do Google Fonts (licença livre), sem SRI; é a única origem externa da página. O visual usa tokens próprios, inspirados num sistema visual de referência; nenhum logo, foto ou fonte paga.

Sem HTTPS: a API fala HTTP em `127.0.0.1`. Publicar fora da máquina pede um proxy com TLS na frente (e, com ele, rever a chave do rate limit e a lista de `Host`).

## Testes que provam

- `apps/api/test/protecoes.test.ts`: cabeçalhos em `/api` e `/health`, CORS (libera da lista, recusa de fora, preflight só GET/POST), rate limit, limite de corpo, timeout, config.
- `apps/api/test/borda.test.ts`: `Host` (atende o próprio, 421 para outro, origens do CORS na lista), 415, teto de baldes.
- `apps/api/test/contrato.test.ts`: 400 com caminho e sem eco do valor, contrato estrito, 500 sem stack nem mensagem interna, log sem query nem corpo.
- `apps/api/test/web.test.ts`: CSP da web no `index.html`, não serve fora da pasta, a API continua respondendo como API.
- `apps/api/test/integracao.test.ts` e `apps/web/src/infra/clienteLocal.test.ts`: dado adulterado não carrega.
- `apps/web/src/infra/repositorio.test.ts`: lixo no `localStorage` é ignorado.
