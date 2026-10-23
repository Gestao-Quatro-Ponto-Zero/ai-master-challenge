# Arquitetura

O desenho parte da pergunta do vendedor, "onde eu foco hoje?", e de uma exigência do desafio: a ferramenta precisa funcionar de verdade e outro dev precisa conseguir manter. Por isso toda regra fica num domínio em TypeScript puro, sem I/O, e as duas formas de rodar (pela API ou só no navegador) chamam as mesmas funções.

## Pastas

```
solution/
  packages/dominio/     regras: 5 contextos + composição (TypeScript puro, sem I/O)
  apps/api/             API HTTP fina (Hono em Node): valida, protege, traduz para HTTP
  apps/web/             web (React + Vite): telas, cliente resiliente, modo local
  e2e/                  Playwright, com vídeo de cada fluxo
  data/                 deals.json (+ .sha256) e o script Python que o gera
  scripts/              checagem de fronteiras, testes da camada de dados e o build da Vercel
  vercel.json           deploy A: web estática + API como função (ADR 0010)
```

## Os contextos

Cada contexto é uma fatia vertical: domínio (`packages/dominio/src/<ctx>/`), rotas (`apps/api/src/<ctx>/`), telas (`apps/web/src/<ctx>/`) e testes. O contrato público de cada um é o `index.ts` (e o `http.ts` que ele reexporta, com rotas e schemas).

| Contexto | Responde a | Documento |
|---|---|---|
| `pipeline` | Quais negócios existem, com que idade e com que lacunas? | [contextos/pipeline.md](contextos/pipeline.md) |
| `organizacao` | De quem é esta fila? Quem são vendedores, managers e regiões? | [contextos/organizacao.md](contextos/organizacao.md) |
| `qualificacao` | O que o vendedor confirma sobre o negócio e o que ele decide? | [contextos/qualificacao.md](contextos/qualificacao.md) |
| `score` | O que os fatos do negócio dizem, e qual a chance histórica da idade dele? | [contextos/score.md](contextos/score.md) |
| `priorizacao` | Em que grupo o negócio fica e qual a próxima ação? | [contextos/priorizacao.md](contextos/priorizacao.md) |

Fora dos contextos:
- `compartilhado`: o tipo `Resultado` (sucesso ou falha sem exceção) e o formato de erro.
- `aplicacao`: a **composição**. `criarServicos` monta os casos de uso (`fila`, `item`, `avaliar`, `resumo`…) sobre um pipeline validado. Não tem regra própria: só junta os contextos. A API e o modo local da web chamam esta mesma função.

## Dependências entre os contextos

Medidas pelos imports de `packages/dominio/src/*/index.ts`:

Em camadas, de baixo para cima (cada camada só importa as de baixo):

```
aplicacao        composição: usa todos
priorizacao      usa score, qualificacao, organizacao, pipeline, compartilhado
score            usa pipeline
organizacao      usa pipeline
qualificacao     usa compartilhado
pipeline         usa compartilhado
compartilhado    não importa nenhum
```

Seta = "importa":
- `pipeline` → `compartilhado`
- `organizacao` → `pipeline` (o tipo `Deal`)
- `qualificacao` → `compartilhado`
- `score` → `pipeline`
- `priorizacao` → `compartilhado`, `pipeline`, `organizacao`, `qualificacao`, `score`
- `aplicacao` → todos

Não há ciclo. `priorizacao` é o único contexto que combina os outros, porque é ele que responde à pergunta do vendedor.

## Como uma requisição anda

```
Navegador (web)
  │
  ├─ tela (React) ──► cliente resiliente
  │                      │
  │                      ├─ API disponível ──► cliente HTTP (timeout 4 s, retry com jitter, disjuntor)
  │                      │                         │
  │                      │                         ▼
  │                      │                   API (Hono, apps/api)
  │                      │                     log → cabeçalhos → Host → CORS → rate limit
  │                      │                     → limite de corpo → timeout → rota
  │                      │                         │ valida a entrada (zod)
  │                      │                         ▼
  │                      │                   domínio: criarServicos(...)  ◄── deals.json conferido
  │                      │                         (ou o banco, se o metadado dele conferir)
  │                      │
  │                      └─ API fora ou com erro 5xx ──► modo local
  │                                                     baixa /dados/deals.json + .sha256,
  │                                                     confere, valida e chama
  │                                                     o MESMO criarServicos(...) no navegador
  │
  └─ respostas e decisões do vendedor ──► localStorage (atrás da porta RepositorioRespostas)
                                        └─► API /api/qualificacao/* ──► banco compartilhado
                                            (com DATABASE_URL; disjuntor e queda para a memória)
```

- **API fina.** As rotas só validam a entrada com os schemas do próprio domínio, chamam o caso de uso e traduzem `Resultado` em status HTTP (`apps/api/src/infra/erros.ts`). Nenhuma regra de negócio mora na API.
- **Modo local.** Se a API cai, a web calcula a mesma fila no navegador e mostra um aviso ("Sem conexão com o servidor…"). A cada 15 s pergunta a `/health` se a API voltou. Ver [ADR 0002](adr/0002-api-fina-e-modo-local.md) e [resiliencia.md](resiliencia.md).
- **Uma porta só.** Em `npm start`, a API também serve a web construída (`apps/api/src/infra/web.ts`), então o app e a API ficam em `http://localhost:8787`.
- **O dado entra conferido.** A API e o modo local conferem o SHA-256 do `deals.json` contra o `.sha256` e validam o schema antes de calcular qualquer coisa. Dado adulterado: a API não sobe; o modo local recusa. Com banco, a API só usa os negócios do banco se o metadado dele tiver o mesmo SHA-256 ([ADR 0009](adr/0009-banco-com-papel-restrito.md)).
- **Respostas em dois lugares.** O navegador é a fonte da tela; cada gravação também vai ao servidor, que guarda no banco compartilhado (ou na memória, sem banco). Com a API de pé, a web baixa os registros do servidor e junta por data.
- **Publicado na Vercel.** A web vai como estático e a API como função, montada pelo mesmo `criarApp` ([ADR 0010](adr/0010-deploy-a-vercel.md)).

## A checagem de fronteiras

`scripts/checar-fronteiras.mjs` roda no começo do `npm test` e falha o build se:
- um contexto importa o interno de outro (só vale `../<ctx>` ou `../<ctx>/index`), no domínio, na API e na web;
- alguém importa `@lead-scorer/dominio/.../src/...` em vez do ponto de entrada público (`@lead-scorer/dominio/<ctx>`);
- o domínio importa módulo de I/O (`node:*`, `fs`, `path`, `http`, `net`, `child_process`, `os`), fora dos testes.

Saída esperada: `fronteiras ok: nenhum contexto importa o interno de outro; o domínio não faz I/O`.

## Onde estão as regras que mudam

Duas coisas devem mudar sem mexer em código de motor, e por isso são config validada na carga:
- a **política** (faixas de idade, textos da tela, recuo do replay): `packages/dominio/src/priorizacao/politica.provisoria.config.ts`;
- o **método** de qualificação (critérios, perguntas, efeito de cada resposta): `packages/dominio/src/qualificacao/metodo.provisorio.config.ts`.

Ver [ADR 0003](adr/0003-metodo-e-politica-como-config.md).
