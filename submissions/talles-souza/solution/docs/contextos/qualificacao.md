# Contexto `qualificacao`

## Responsabilidade

Guardar o que só o vendedor sabe e o que ele decide. O método de qualificação é config: critérios e perguntas de sim ou não (opcionais), cada uma com a frase da ação para quando a resposta é "não". O contexto registra as respostas e a decisão do vendedor sobre a ação sugerida (aceitar ou contestar, com motivo), uma por vez ou em lote ("Encaminhar os N"), e monta o estado atual a partir das linhas gravadas.

O método em uso é **BANT** (`metodo.provisorio.config.ts`): T (tempo) e B (orçamento) vêm do dado; A (quem decide), N (necessidade) e o compromisso (próxima conversa com data) viram as três perguntas.

## Contrato público (`packages/dominio/src/qualificacao/index.ts`)

Tipos:
- `Bloco`: `foque_agora` | `siga_no_ritmo` | `nutricao` | `sem_inicio`; `BLOCOS` na ordem da tela.
- `MetodoQualificacao` (id, versão, `criterios`, `perguntas`, `fontes`), `CriterioMetodo` (origem `dado` ou `vendedor`), `PerguntaFato` (`aplicaEm`, `acaoSeNao` e `noScore`, os rótulos da resposta no porquê do score: "Decisor confirmado" / "Sem decisor"). Não há efeito de resposta sobre o bloco.
- `RespostasDoDeal` (formato 1): `respostas` e `decisao`.
- `DecisaoDoVendedor`: `acao`, `aceita`, `motivo`, `em`.
- `TipoAcao`: `avancar_hoje` | `manter_ritmo` | `qualificar` | `encaminhar_para_nutricao`.
- `LinhaResposta` e `LinhaDecisao`: o que o banco guarda (uma linha por resposta e por decisão, com o vendedor e a data).
- `RepositorioRespostas`: a porta da persistência no navegador (`ler`, `salvar`, `listar`, `limpar`).

Funções:
- `validarMetodo(bruto)`; erro `metodo_invalido` (campo desconhecido, como um efeito sobre o bloco, é recusado).
- `validarRespostas(bruto)`; erro `respostas_invalidas`.
- `responder(atual, dealId, metodo, perguntaId, valor, agoraIso)`; erro `pergunta_inexistente`.
- `decidir(atual, dealId, metodo, decisao, agoraIso)`; erro `motivo_obrigatorio`.
- `decidirEmLote(atual, dealIds, metodo, decisao, agoraIso)`: um registro por negócio, mesma data e mesmo motivo; erros `lote_vazio`, `lote_repetido` e os de `decidir`.
- `montarRegistros(linhasRespostas, linhasDecisoes, metodoId)`: o estado atual (por pergunta, a resposta mais recente; a decisão mais recente).
- `mesclarRegistros(a, b)`: junta o registro do navegador com o do servidor pelo mesmo critério.
- `perguntasPendentes(metodo, bloco, respostas)`.
- `criarRepositorioEmMemoria()`; `metodoAtivo`.

Contrato HTTP (`http.ts`): `ROTA_METODO`, `ROTA_REGISTROS`, `ROTA_RESPONDER`, `ROTA_DECIDIR`, `ROTA_DECIDIR_LOTE`, `respostasDoDealSchema` e os schemas dos pedidos.

## Rotas da API

| Rota | O que devolve |
|---|---|
| `GET /api/qualificacao/metodo` | o método em uso |
| `GET /api/qualificacao/registros` | `{ armazenamento: 'banco' \| 'memoria', registros }`, com filtro opcional por vendedor, manager ou região |
| `POST /api/qualificacao/responder` | grava `{ dealId, perguntaId, valor }` → o registro atual do negócio |
| `POST /api/qualificacao/decidir` | grava `{ dealId, acao, aceita, motivo? }` → o registro atual |
| `POST /api/qualificacao/decidir-lote` | grava `{ dealIds, acao, aceita, motivo? }`, um por negócio → `{ armazenamento, registros, em }` |

O armazém é o banco compartilhado (com `DATABASE_URL`) ou a memória do processo ([ADR 0009](../adr/0009-banco-com-papel-restrito.md)). A data de cada linha é a do servidor.

## Telas da web

- `apps/web/src/qualificacao/Perguntas.tsx`: as perguntas com Sim/Não, dentro da tela do negócio.
- `apps/web/src/qualificacao/NovoLead.tsx` (`#/novo-lead`, "Novo negócio"): um cliente que ainda não está no sistema; mostra o grupo em que entraria e o que falta perguntar. Não é guardado.
- `apps/web/src/qualificacao/ComoFunciona.tsx` (`#/como-funciona`): o cálculo da nota, o que foi testado, os grupos e as perguntas do método.
- A persistência no navegador fica em `apps/web/src/infra/repositorio.ts` (`localStorage`, prefixo `lead-scorer:respostas:v1:`); o envio e a leitura no servidor, em `apps/web/src/infra/registrosHttp.ts`.

## Testes

- `packages/dominio/src/qualificacao/qualificacao.test.ts`: método válido e inválido (inclusive com efeito sobre o bloco), responder e trocar resposta, pergunta inexistente, respostas de outro negócio, contestar exige motivo, lote (mesma data, vazio, repetido), montar e mesclar registros.
- `packages/dominio/src/aplicacao/aplicacao.test.ts`: outro método (só do teste) muda pendentes e a ação, nunca o bloco; "Não" nas 3 perguntas dos 2.089 abertos não muda nenhum grupo.
- `apps/api/test/registros.test.ts` e `apps/api/test/banco.test.ts`: as rotas, o lote numa linha por negócio, o SQL só de `SELECT` e `INSERT`, a queda para a memória.
- `apps/web/src/score/TelaDeal.test.tsx`: "não" troca a ação e guarda a resposta com a data; contestar sem motivo não salva.
- `apps/web/src/infra/repositorio.test.ts`: JSON quebrado ou formato errado é ignorado; storage que lança não derruba a tela.
- `e2e/testes/fluxos.spec.ts`: "Não" muda a ação, contestar exige motivo, a decisão sobrevive ao recarregar a página, "Encaminhar os N".

## Invariantes

- Toda resposta é opcional; deixar em branco não penaliza o negócio.
- Nenhuma resposta muda o bloco nem a ordem da tela. Cada resposta soma ou tira do score (+10 por "Sim", −15 por "Não"; pesos em `score/qualidade.config.ts`, heurística declarada: o histórico não tem essas respostas; ver [ADR 0012](../adr/0012-score-e-qualidade.md)); "não" troca a ação pela frase da pergunta (a primeira, na ordem do método).
- Contestar exige motivo de 3 a 280 caracteres; aceitar dispensa.
- Respostas têm formato versionado (1), no máximo 50 por negócio, datas ISO 8601 com fuso. Lidas de fora, passam pelo schema; o que não passa é ignorado (no navegador) ou recusado com 400 (na API).
- Respostas de outro negócio ou de outro método não valem para este.
- Gravado é só acrescentado: o estado atual sai das linhas, nunca de uma linha alterada.
- Método válido: ids de pergunta e de critério únicos; critério do vendedor aponta para uma pergunta que existe.
