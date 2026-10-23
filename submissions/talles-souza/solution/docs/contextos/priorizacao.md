# Contexto `priorizacao`

## Responsabilidade

Responder à pergunta do vendedor: **onde eu foco hoje?** A política (config) põe cada negócio aberto num bloco pela idade, monta o indicador ("Score 61", a qualidade do negócio: a idade medida + as respostas do vendedor; "US$ 4.821 em jogo" à parte; o "ver por quê" com a posição na lista) e a frase da receita esperada, escolhe a próxima ação e ordena cada bloco pelo valor esperado. Score, ordem e valor são três coisas separadas ([ADR 0012](../adr/0012-score-e-qualidade.md)). As respostas do vendedor mudam o score e a ação, nunca o bloco nem a ordem. Também monta o painel "Acompanhar a equipe" ("onde meu time está perdendo dinheiro?": 4 métricas e a tabela por vendedor, só leitura).

## Contrato público (`packages/dominio/src/priorizacao/index.ts`)

Tipos:
- `Grupo`: o próprio `Bloco` (`foque_agora`, `siga_no_ritmo`, `nutricao`, `sem_inicio`); `GRUPOS` na ordem da tela. `BlocoPorIdade`: os três que a idade decide.
- `PoliticaPriorizacao`: `faixas` (bloco, `ateDias`, rótulo, porquê), `semData`, `chance` (config do replay), `leitura`, `ordenacao` e todos os `textos` da tela (página, indicador, motivos, receita, Nutrição, grupos, perguntas, avisos, painel).
- `ItemFila`: negócio, avaliação, `bloco`, `faixa`, `indicador`, `pendentes`, `respostas`, `proximaAcao`, `decisao`, `porque`.
- `Indicador`: `score` (a qualidade, 0–100, ou null sem data e sem resposta), `qualidade` (a conta: base e um ajuste por resposta), `emJogo` ("GTX Pro · US$ 4.821 em jogo"), `porqueScore` (as linhas do "ver por quê": a idade, cada resposta, a posição), `posicao` e `posicaoTexto`, `chance` (0 a 1) e a conta por fator, taxa, `n`, faixa, número ("Score 61" ou "Score —"), rótulo, motivo, `receita` e `preco` (frases do detalhe).
- `ProximaAcao`, `Fila` (`blocos`, `contadores` com `porBloco`, `receita` com `total` e `semEstimativa`).
- `MetricasDoPainel`: `total`, `receita` (chance × preço dos abertos com data), `foqueSemConversa` (nº e US$ em jogo dos negócios que a tela mostra em Foque agora, com a promoção do Siga, sem "Sim" à próxima conversa; com `foque`, `sim`, `nao`, `semResposta`), `parado` e `semInicio` (nº e US$ em jogo), `respostas` (negócios com alguma resposta ÷ negócios em que as perguntas valem). `EmJogo`: `{ n, valor }`.
- `Painel`: as `MetricasDoPainel` do filtro, `limiteParadoDias` e `vendedores` (uma `LinhaDoPainel` por vendedor do filtro, com as mesmas métricas, ordenada por Foque sem próxima conversa).

Funções:
- `validarPolitica(bruto)`; erro `politica_invalida`.
- `classificar(deal, avaliacao, politica, metodo, respostas, qualidade?)` → `ItemFila`: o score soma ao dado as respostas que valem para o bloco, pelos pesos de `qualidade` (padrão: `configQualidadePadrao`).
- `textoDoScore(politica, qualidade?)`: o que o score é, em "Como a nota funciona", com os pesos do config.
- `montarFila(itens)` → `Fila`.
- `grupoNaTela(itens)`: em que grupo a tela mostra cada negócio (o bloco da idade; o Siga no ritmo vai para o Foque agora quando o Foque do vendedor está vazio).
- `posicionarNaTela(itens)`: a posição de cada negócio da lista de um vendedor na ordem da tela (o grupo, na ordem de `GRUPOS`, depois o que há a ganhar). Não é o score.
- `montarPainel(fila, time, metodo, politica)` → `Painel` (`time` = os vendedores do filtro, por `filtrarTime` do contexto `organizacao`; quem não tem negócio entra com zero).
- `textosDaTela(politica, janela)` e `preencher(modelo, valores)`.
- `politicaAtiva`.

Contrato HTTP (`http.ts`): `ROTA_FILA`, `ROTA_ITEM`, `ROTA_POLITICA`, `ROTA_PAINEL`, `pedidoFilaSchema`, `pedidoItemSchema`.

## Rotas da API

| Rota | O que devolve |
|---|---|
| `POST /api/priorizacao/fila` | `{ filtro, respostas }` (até 2.500 registros de respostas) → a fila do filtro em blocos, com contadores e a receita esperada |
| `POST /api/priorizacao/item` | `{ dealId }` ou `{ lead }`, com as respostas daquele negócio → o item classificado |
| `POST /api/priorizacao/painel` | o mesmo corpo da fila → as 4 métricas do filtro e a linha de cada vendedor |
| `GET /api/priorizacao/politica` | a política em uso, com os textos |

As respostas vêm do navegador no corpo; respostas de outro negócio ou de outro método → 400 `respostas_invalidas`.

## Telas da web

- `apps/web/src/priorizacao/SegundaFeira.tsx`, rota `#/` ("Onde focar hoje"): a tela inicial. "Quem é você?" com o time inteiro; a receita esperada no topo, com a comissão opcional; os grupos na ordem, cada um com contador e a frase de grupo vazio. Nutrição começa recolhida, com "Encaminhar os {n}" e a confirmação na própria tela.
- `apps/web/src/priorizacao/ItemDaFila.tsx`: o cartão de um negócio (cabe em 390 px), em 3 linhas: o score, a ação e "{produto} · US$ {preço} em jogo · ver por quê" (o porquê do score, a posição, a chance e a conta por fator ficam no detalhe); em Nutrição, o botão "Encaminhar para nutrição" ou, depois, "Encaminhado em {data}." com "Contestar".
- `apps/web/src/pipeline/VisaoManager.tsx`, rota `#/manager` ("Acompanhar a equipe"): o painel.

## Testes

- `packages/dominio/src/priorizacao/priorizacao.test.ts`: política válida e inválida, limites inclusivos, indicador e receita, sem data no bloco próprio, ação do grupo, "não" troca a ação sem mudar o bloco, o score com as respostas ("Sim" +10, "Não" −15, limite 0–100, sem data a partir de 50, o preço fora, Nutrição só com a idade), ordenação pelo valor esperado, contadores, textos (nenhum termo proibido; nº 59).
- `packages/dominio/src/aplicacao/aplicacao.test.ts`: outra política (só do teste, 45/90) muda os blocos da fila real sem tocar no motor; "Não" (e "Sim") nas 3 perguntas dos 2.089 abertos não muda nenhum grupo.
- `packages/dominio/src/aplicacao/integracao.test.ts`, com o arquivo real:
  - todos os abertos: Foque agora 30, Siga no ritmo 27, Nutrição 1.532 (1.291 além da janela), Aborde primeiro 500, total 2.089;
  - por região, como a tela mostra (Foque / Siga / Nutrição / Aborde primeiro): West 17/15/716/0, East 16/9/408/0, Central 0/0/408/500;
  - receita esperada pela chance do motor × preço (a soma da fila bate com a de cada negócio) e o backtest pela taxa do replay (2.409 abertos em 30/09/2017: previsto US$ 1.284.794, realizado US$ 1.251.928);
  - o score: Nutrição ≤ 15, Siga ≥ Foque, os 500 sem data sem score, um "Sim" sobe 10 sem mudar a ordem da tela;
  - o painel: sem filtro US$ 69.395 / 33 (US$ 67.896) / 1.532 (US$ 3.779.334) / 500 (US$ 1.073.986), West US$ 38.435 / 17 (US$ 36.502) / 716 (US$ 1.935.958) / 0; cada linha da tabela bate com a fila do vendedor, a soma das linhas é o time, os 35 aparecem e quem não tem negócio fica com zero; um "Sim" à próxima conversa tira o negócio da métrica 2 e as respostas não mexem nas outras;
  - nenhum texto da fila usa "deal", "morto" ou "encerrar".
- `apps/api/test/integracao.test.ts` e `apps/api/test/registros.test.ts`: a mesma fila e o painel pela API.
- `apps/web/src/priorizacao/SegundaFeira.test.tsx`, `apps/web/src/pipeline/VisaoManager.test.tsx` e `e2e/testes/fluxos.spec.ts`.

## Invariantes

- O bloco sai da idade, pelas faixas da política, com tetos inclusivos: até 40 dias Siga no ritmo; 41 a 60 Foque agora; acima de 60 Nutrição (`politica.provisoria.config.ts`). Sem data de início: bloco `sem_inicio` ("Aborde primeiro"), sem idade; o score espera a primeira resposta do vendedor ("Score —").
- Nenhuma resposta muda o bloco nem a ordem: cada resposta soma ou tira do score, e a resposta "não" troca a ação. Em Nutrição as perguntas não valem, e a ação é sempre encaminhar.
- A política só é aceita com as faixas em ordem crescente e a última sem teto (vale para as faixas de idade, de chance e de motivo).
- A ordem da tela é o grupo primeiro; dentro do bloco, a receita esperada (sem data de início, o preço), maior primeiro; empate, preço maior; depois idade menor e id. O score (a qualidade) não muda a ordem nem o grupo, e o preço não entra no score.
- Cada negócio aparece em um só bloco.
- O painel não tem ranking por taxa de ganho nem ação; a tabela por vendedor ordena pelo Foque sem próxima conversa (o que precisa de ação), não pelo desempenho.
- Todo texto da tela vem do config, com `{…}` preenchidos pelo domínio ou pela tela; trocar texto não mexe em componente.
