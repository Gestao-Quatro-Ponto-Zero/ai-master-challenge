# ADR 0006: Sem autenticação

**Status:** aceita

## Contexto

O vendedor precisa ver a fila dele. O enunciado pede algo funcional que "pode ser simples", com filtro por vendedor, manager e região como bônus. Login exige provedor de identidade, gestão de usuários e segredos, sem nada disso no dataset (os vendedores são só nomes).

## Decisão

- Não há login. O seletor "Quem é você?" escolhe a fila; não é autenticação, e a tela diz isso.
- Sem sessão, sem cookie, sem segredo: o CORS não libera credenciais.
- A API sobe em `127.0.0.1` por padrão. Com `HOST` fora do loopback, o servidor avisa no console: "expõe a API fora desta máquina; não há login".
- O cabeçalho `Host` é conferido contra a lista do próprio servidor (421 `host_invalido`), para que uma página de fora não leia a API local por DNS rebinding.

## Consequências

- Qualquer pessoa com acesso à porta vê todos os negócios e pode escolher qualquer nome.
- Não há registro de quem respondeu ou decidiu: o banco grava o vendedor dono do negócio, não quem clicou ([ADR 0009](0009-banco-com-papel-restrito.md)).
- Para escalar: SSO e autorização por papel (vendedor vê os seus, manager o time dele), e então quem respondeu em cada linha.
- Testes: `apps/api/test/borda.test.ts` (Host), `apps/api/test/protecoes.test.ts` (CORS sem credenciais), `apps/web/src/priorizacao/SegundaFeira.test.tsx` (o seletor diz que não é login).

## Alternativas consideradas

- **Login simples com senha:** traria segredo para guardar e uma tela a mais, sem ganho real para quem avalia localmente.
- **SSO:** é o caminho para produção, mas depende de um provedor que o desafio não tem.
