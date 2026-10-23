# ADR 0002: API fina e modo local com o mesmo domínio

**Status:** aceita

## Contexto

O vendedor abre a ferramenta na segunda de manhã e precisa ver a fila. O enunciado aceita "aplicação web" ou "API que recebe dados de um deal e retorna score + explicação". Uma API dá contrato claro e permite outro cliente amanhã; uma página que calcula sozinha não depende de servidor. Se a API cair, a lista não pode sumir.

## Decisão

- **API fina** (Hono em Node, `apps/api`): cada rota valida a entrada com o schema do domínio, chama o caso de uso e traduz o `Resultado` em HTTP. Nenhuma regra mora na API.
- **Modo local** na web (`apps/web/src/infra/clienteLocal.ts`): baixa `/dados/deals.json` e o `.sha256`, confere, valida e roda o **mesmo** `criarServicos` do domínio no navegador.
- **Cliente resiliente** (`clienteResiliente.ts`): tenta a API; se ela não responde depois dos retries, se o circuito está aberto ou se responde com erro 5xx, responde pelo modo local e mostra o aviso "Sem conexão com o servidor. A lista foi calculada aqui no seu navegador." A cada 15 s pergunta a `/health` se a API voltou.
- `npm start` serve app + API na mesma porta.

## Consequências

- A fila é a mesma pelos dois caminhos: o teste `apps/web/src/infra/clienteLocal.test.ts` compara o modo local com os casos de uso do domínio sobre o arquivo real.
- O E2E derruba a API (`/api/**` e `/health` abortados) e a fila continua, com o aviso (`e2e/testes/fluxos.spec.ts`, vídeo em `e2e/videos/`).
- O navegador baixa o `deals.json` inteiro (cerca de 5,4 MB) só quando cai para o modo local.
- Toda mudança de regra vale para os dois lados de uma vez.

## Alternativas consideradas

- **Só API:** se ela cai, o vendedor fica sem lista.
- **Só página estática:** sem contrato HTTP para outro cliente (outro canal, integração com o CRM).
- **Regra duplicada no front:** mais simples no começo, diverge com o tempo.
