# ADR 0001: Monorepo com npm workspaces e TypeScript

**Status:** aceita

## Contexto

O desafio pede software que o vendedor use e que "outro dev consiga dar manutenção". A mesma regra precisa rodar em dois lugares: na API e no navegador, quando a API cai (ver [ADR 0002](0002-api-fina-e-modo-local.md)). Duas cópias da regra divergiriam com o tempo.

## Decisão

- Um repositório com npm workspaces: `packages/dominio`, `apps/api`, `apps/web` e `e2e`.
- TypeScript em tudo, com `strict`, `noUncheckedIndexedAccess` e `verbatimModuleSyntax` (`tsconfig.base.json`).
- O domínio é importado como pacote (`@lead-scorer/dominio/<contexto>`), pelos pontos de entrada públicos declarados no `package.json` dele.
- Versões fixas (sem `^`) e `package-lock.json` versionado.
- `npm` como gerenciador: vem com o Node, o avaliador não instala nada a mais.
- Um `npm test` na raiz roda fronteiras, typecheck, lint e os testes de todos os pacotes.

## Consequências

- Uma regra, um lugar: a API e o modo local chamam o mesmo `criarServicos`.
- O typecheck pega a quebra de contrato entre pacotes antes do teste.
- `npm install` uma vez na raiz instala tudo.
- Exige Node 22.18 ou mais novo e npm 10.9 ou mais novo (`engines`).

## Alternativas consideradas

- **Repositórios separados para API e web:** duplicaria o domínio ou exigiria publicar um pacote.
- **Outro gerenciador de workspaces (pnpm, yarn):** mais rápido, mas é uma instalação a mais para quem avalia.
- **JavaScript sem tipos:** mais rápido de escrever, mais caro de manter; os contratos entre contextos ficariam só no comentário.
- **Python ponta a ponta (ex.: um app de dashboard):** a camada de dados já é Python, mas o modo local no navegador exigiria a regra em JavaScript de qualquer jeito.
