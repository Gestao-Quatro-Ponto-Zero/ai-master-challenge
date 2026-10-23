# ADR 0005: Respostas e decisões no `localStorage`, atrás de uma porta, com o servidor como cópia compartilhada

**Status:** aceita

## Contexto

O vendedor responde às perguntas do método e aceita ou contesta a ação sugerida. Isso precisa sobreviver a recarregar a página, sem exigir banco de dados para rodar a solução, e sem amarrar o domínio a um jeito de guardar.

## Decisão

- O domínio declara a porta `RepositorioRespostas` (`ler`, `salvar`, `listar`, `limpar`) em `qualificacao`.
- A web implementa com `localStorage` (`apps/web/src/infra/repositorio.ts`), uma chave por negócio com prefixo versionado `lead-scorer:respostas:v1:`.
- O registro tem formato versionado (`formato: 1`); toda leitura passa por `validarRespostas`. JSON quebrado ou formato errado é ignorado.
- Todo acesso fica em try/catch. Sem `localStorage` (bloqueado ou cheio), guarda em memória pela sessão da tela.
- Para calcular, a web manda as respostas no corpo de `POST /api/priorizacao/fila`, `/item` e `/painel`, e a API as valida antes de usar.
- Cada gravação também vai para o servidor (`apps/web/src/infra/registrosHttp.ts`), que guarda no banco compartilhado, se houver, ou na memória ([ADR 0009](0009-banco-com-papel-restrito.md)). Com a API de pé, a web baixa os registros do servidor e junta com os do navegador: por pergunta, vale a resposta mais recente. Falha do servidor não é erro para o vendedor: a resposta fica no navegador.

## Consequências

- Roda sem banco e sem login. O E2E prova que a decisão sobrevive ao recarregar (`e2e/testes/fluxos.spec.ts`).
- Sem o banco compartilhado, as respostas ficam naquele navegador (e na memória da API até ela reiniciar): não passam para outro aparelho e o painel do manager só mostra as dele. Está nas Limitações do README.
- O domínio não sabe onde as respostas ficam: a porta no navegador e o armazém no servidor implementam o mesmo contrato de registros.
- Testes: `apps/web/src/infra/repositorio.test.ts` (salva, lê, lista, limpa; ignora lixo; storage que lança não derruba a tela; sem storage, memória).

## Alternativas consideradas

- **Só o banco, sem cópia no navegador:** a tela pararia quando o servidor caísse; com o navegador como fonte, o vendedor nunca perde a resposta.
- **Cookie:** limite de tamanho e vai em toda requisição sem necessidade.
- **IndexedDB:** mais capacidade, mais código; o volume (até 50 respostas por negócio) cabe no `localStorage`.
