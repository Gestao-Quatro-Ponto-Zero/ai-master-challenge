# Contexto `organizacao`

## Responsabilidade

Responder "de quem é esta fila?". O vendedor escolhe o próprio nome e vê só os negócios dele; o manager usa os mesmos filtros para acompanhar a equipe. Monta vendedores, managers e regiões a partir do time inteiro (os 35 de `sales_teams.csv`, que vêm no `deals.json`), conta os abertos de cada um e transforma um perfil num filtro.

O perfil **não é autenticação**: é só a escolha de qual fila mostrar.

## Contrato público (`packages/dominio/src/organizacao/index.ts`)

Tipos:
- `Vendedor` (nome, manager, região, quantos abertos), `Manager` (nome, região, vendedores), `Organizacao`.
- `Perfil`: `{ tipo: 'vendedor', nome }` | `{ tipo: 'manager', nome }` | `{ tipo: 'todos' }`.
- `Filtro`: `vendedor`, `manager`, `regiao`, todos opcionais.

Funções:
- `montarOrganizacao(time, deals)`: todo o time aparece, inclusive quem não tem negócio (abertos 0), em ordem de nome (`pt-BR`).
- `filtroDoPerfil(perfil)` e `aplicarFiltro(deals, filtro)`.
- `filtrarTime(time, filtro)`: os vendedores do time que o filtro alcança, com ou sem negócio (as linhas da tabela do painel).

Contrato HTTP (`http.ts`): `ROTA_ORGANIZACAO`, `filtroSchema` (textos de 1 a 80 caracteres, sem campo extra).

## Rotas da API

| Rota | O que devolve |
|---|---|
| `GET /api/organizacao` | vendedores, managers e regiões |

O `filtroSchema` também valida o `filtro` do corpo de `POST /api/priorizacao/fila`.

## Telas da web

- `apps/web/src/organizacao/SeletorPerfil.tsx`: "Quem é você?", com os 35 agrupados por escritório e manager. O texto da tela diz que não é login; a escolha fica neste navegador (`lead-scorer:perfil:v1`).
- `apps/web/src/organizacao/Filtros.tsx`: vendedor, manager e região, usados em "Acompanhar a equipe".

## Testes

- `packages/dominio/src/organizacao/organizacao.test.ts`: o time inteiro com quem não tem negócio, ordem, contagem de abertos, perfil → filtro, campos ausentes não filtram.
- `packages/dominio/src/aplicacao/integracao.test.ts`: os 35 vendedores (5 sem negócio no histórico, 8 sem negócio aberto), por região e por vendedor, com o dado real.
- `apps/api/test/integracao.test.ts`: a fila de um vendedor real traz só negócios dele, no total de abertos dele.
- `apps/web/src/priorizacao/SegundaFeira.test.tsx`: sem escolha guardada, a tela pergunta "Quem é você?" com o time agrupado; o seletor diz que não é login; o vendedor sem negócio aberto vê zero.
- `apps/web/src/infra/repositorio.test.ts`: o perfil guardado volta igual; lixo vira `null`.
- `e2e/testes/fluxos.spec.ts`: o vendedor sem negócio aberto; o painel com os 35 no filtro, só leitura.

## Invariantes

- Todo o time aparece, sempre: 5 dos 35 não têm nenhum negócio no histórico e outros 3 só têm negócios fechados; os 8 aparecem com zero.
- Ordem por nome com locale fixo `pt-BR`: a API e o modo local ordenam igual em qualquer máquina.
- Campo ausente no filtro não filtra; campos presentes combinam (E).
- O perfil nunca dá nem tira acesso: só escolhe o filtro.
