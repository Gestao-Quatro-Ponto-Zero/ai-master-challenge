# Contexto `score`

## Responsabilidade

Explicar ao vendedor, em frases, o que os fatos de um negócio dizem: a idade contra a janela dos ganhos, a **chance histórica** de quem tinha a mesma idade, o preço de tabela, a **receita esperada** (taxa da faixa × preço de tabela) e o contexto que não decide nada (conta, porte, setor). Sem modelo de linguagem: tudo é cálculo sobre o histórico.

E calcula a nota: o **motor de pontos** (`motor.ts`, limites em `motor.config.ts`) testa 19 fatores no histórico, pontua cada valor pelo método HubSpot em escala log, escolhe os fatores por seleção gulosa fora da amostra e devolve, para cada negócio aberto, a chance com a conta por fator. Também mede a **tabela de pontos** por atributo (taxa ÷ taxa geral, nos fechados), a medição anterior ao motor.

## Score, ordem da tela e valor: três coisas separadas ([ADR 0012](../adr/0012-score-e-qualidade.md))

- **O score diz se o negócio é bom** (`qualidade.ts`, pesos em `qualidade.config.ts`). A parte do dado é `round(100 × chance da faixa de idade ÷ maior chance entre as faixas)`, com as chances do motor (`chancesDaIdade`, conversão do config). A parte do vendedor soma +10 por "Sim" e −15 por "Não" a cada pergunta respondida; sem resposta, nada muda; o resultado fica entre 0 e 100. **Os pesos das respostas são heurística declarada: o histórico não tem essas respostas.** Sem data de início e sem resposta não há score ("Score —"); com resposta, ele parte de 50.
- **O lugar na tela diz por onde começar** (`posicao.ts`): o grupo, depois o valor esperado (chance × preço; sem data, o preço). A posição (`k` de `n`) aparece só no "ver por quê"; não é o score.
- **O valor diz quanto está em jogo**: o preço de tabela, numa linha própria do cartão ("US$ 4.821 em jogo"). Ele não entra no score.

Hoje, no `deals.json`: até 40 dias 90–100, 41–50 dias 61, 51–60 dias 41, 61–90 dias 15, acima de 90 dias 1 ([`score-qualidade-2026-10-23.txt`](../../../process-log/evidencias/score-qualidade-2026-10-23.txt)).

## O motor de pontos (`motor.ts`)

- `medirMotor(deals, referencia, faixasIdade, config)` → `{ motor, pontuar }`. `motor: MotorDePontos` traz os recortes (treino: abertos em R − `treinoDias`, desfecho até R − `horizonteDias`; validação: abertos em R − `horizonteDias`, desfecho até R), a taxa base, cada `FatorDoMotor` (entrou ou não, motivo, AUC sozinho na validação, ganho de AUC, pontos por categoria no treino e os que valem hoje), os escolhidos, o AUC do score e o AUC só da idade. `pontuar(deal)` → `ScoreDoDeal` (score, chance, soma dos pontos, parcelas por fator e a principal) ou null sem data de início.
- `fatoresNoCorte(deals, corte, faixasIdade, config)`: as categorias de cada fator dos abertos num corte. Serve ao teste de vazamento.
- `calcularAuc(scores, ganhou)`: Mann-Whitney, empate vale meio.
- Invariantes: todo fator usa só o que se sabia no corte (o teste apaga o futuro e compara); "sem dado" vale 0 e a taxa geral de cada fator é a de quem tem o dado; categoria com n < `nMinimo` vale 0; o ganho de AUC de um fator é medido nos negócios que têm o dado dele; nenhum peso está no código; a mesma entrada dá o mesmo motor.
- O que ele mediu neste dataset: [`process-log/evidencias/motor-de-pontos-2026-10-23.txt`](../../../process-log/evidencias/motor-de-pontos-2026-10-23.txt) (só a idade entrou; AUC 0,830 na validação).

## Contrato público (`packages/dominio/src/score/index.ts`)

Tipos:
- `Avaliacao`: `situacao`, `idadeDias`, `emJogo` (preço de tabela), `esperado` (chance do motor × preço de tabela; null sem idade), `score` (o `ScoreDoDeal` do motor: a chance absoluta e a conta por fator; null sem idade), `qualidade` (a parte do dado no score: a chance da faixa, a maior chance, a parte de 0 a 100 e o que fechou de fato no replay; null sem idade), `posicao` (a posição na lista aberta do vendedor, por onde começar; null fora de uma lista), `chance` (a faixa de idade do replay), `fatos`, `contexto`, `explicacao`, `referencia`, `maxJanelaDias`.
- `ChanceDoDeal`: faixa, taxa e `n`.
- `EntradaDaLista` e `PosicaoNaLista` (`posicao.ts`): a entrada traz `grupo` (a ordem do grupo em que a tela mostra o negócio, 0 = o primeiro), `esperado`, `emJogo` e `idadeDias`. A posição traz `k` (1 = o primeiro; uma posição por negócio), `n` e `pelo` (`esperado` ou, sem data de início, `preco`). `posicionar(lista)` posiciona uma lista; `compararNaLista` é a ordem: o grupo, depois o valor esperado ou, sem data, o preço, desc; empate, o preço maior, depois o mais novo e o id. Quem diz o grupo de cada negócio é `posicionarNaTela` (contexto `priorizacao`); quem monta a lista de cada vendedor é `criarServicos`.
- Invariante: em toda lista, a posição `k` é a ordem em que a tela mostra os negócios. O score não segue a posição: é a qualidade de cada negócio.
- `ConfigQualidade` (`porSim`, `porNao`, `semDataBase`), `QualidadeDoDado` e `ScoreDeQualidade` (`score`, `base`, `temIdade`, `ajustes` por resposta), em `qualidade.ts`.
- `ChanceHistorica`: corte, população, ganhos e as `FaixaDeChance` do replay.
- `ConfigChance`: `corteDias` e as faixas (vem da política).
- `TabelaDePontos` e `AtributoPontuado` (eixo `perfil` ou `interesse`, pontos mínimo e máximo).

Funções:
- `medirChance(deals, referencia, config)`: o replay. Corte = referência − `corteDias`; população = negócios com início até o corte e ainda abertos nele; idade no corte; ganho = Won fechado até a referência.
- `chanceDaIdade(chance, idadeDias)`.
- `medirPontos(deals, chance)`: pontos = taxa de fechamento do valor ÷ taxa de base. Perfil (setor, produto, porte em quartis de receita, escritório, vendedor) nos fechados; Interesse (idade) no replay.
- `avaliar(deal, contexto)`: inclui a parte do dado (`qualidade`).
- `parteDoDado(chance, maxima)`, `qualidadeDoDado(chance, faixas, fecharam)` e `pontuarQualidade(dado, respostas, config)`: o score de qualidade. `configQualidadePadrao`: os pesos (heurística declarada).
- `chanceDosPontos(motor, pontos)` e `chancesDaIdade(motor)`: a chance de uma soma de pontos e a de cada faixa de idade, pela conversão do config.

Contrato HTTP (`http.ts`): `ROTA_AVALIAR`, `ROTA_CHANCE`, `ROTA_PONTOS`, `pedidoAvaliacaoSchema`.

## Rotas da API

| Rota | O que devolve |
|---|---|
| `POST /api/score/avaliar` | `{ dealId }` ou `{ lead }` → o negócio e a avaliação; inexistente → 404; lead inválido → 400 |
| `GET /api/score/chance` | a chance histórica por faixa de idade (replay) |
| `GET /api/score/pontos` | a tabela de pontos por atributo (taxa ÷ taxa geral, nos fechados) |
| `GET /api/score/motor` | o motor de pontos: fatores, AUC na validação, escolhidos, pontos por categoria |

## Tela da web

`apps/web/src/score/TelaDeal.tsx`, rota `#/deal/<id>` ("o negócio por dentro"): o score e o que está em jogo, o "ver por quê" (a idade, uma linha por resposta e a posição na lista), a conta da chance (`ContaDoScore`, também no cartão da lista), o grupo, a ação (aceitar ou contestar), as perguntas e os fatos com o contexto. A tela "Como a nota funciona" usa `chance` e `motor`.

## Testes

- `packages/dominio/src/score/motor.test.ts`: AUC, pontos HubSpot em log com suavização, n pequeno, "sem dado" neutro, seleção gulosa (só a idade quando o resto é ruído; um segundo fator entra quando sobe o AUC), vazamento (apagar o futuro não muda nenhum fator), score reproduzível nas duas conversões e Prospecting sem score.
- `packages/dominio/src/score/score.test.ts`: frases da idade contra a janela, prospecção sem idade, "sem dado de conta" sem penalidade, replay com dados de teste, pontos e quartis.
- `packages/dominio/src/score/qualidade.test.ts`: a parte do dado (a melhor faixa = 100), "Sim" +10 e "Não" −15, limite 0–100, sem data sem resposta = sem score e com resposta a partir de 50.
- `packages/dominio/src/score/posicao.test.ts`: a ordem da tela (o grupo, depois o valor; empates; a ordem de entrada não muda nada).
- `packages/dominio/src/aplicacao/integracao.test.ts`, o score com o arquivo real: Nutrição ≤ 15, Siga ≥ Foque, os 500 sem data sem score, o mesmo score para a mesma idade (o preço não entra), um "Sim" sobe 10 sem mudar a ordem da tela.
- `packages/dominio/src/aplicacao/integracao.test.ts`, com o arquivo real:
  - replay com corte em 2017-09-30 e população de 2.409;
  - 41 a 50 dias: 164 negócios, 32,3%; 51 a 60: 201, 21,9%; 61 a 90: 460, 6,7%; acima de 90: 0%; até 40 dias: 859, 50,2%;
  - tabela de pontos: taxa geral 63,2% de 6.711 fechados; setor 0,97–1,03, produto 0,95–1,03, porte 0,97–1,04, escritório 0,99–1,01, vendedor 0,87–1,11; idade acima de 1,5.
- `apps/api/test/contrato.test.ts` (blocos `score` e `organização, método e política`).
- `apps/web/src/score/TelaDeal.test.tsx`.

## Invariantes

- Falta de dado vira "sem dado", nunca penalidade.
- `emJogo` é o preço de tabela do catálogo e `esperado` é a chance do score (com o motor no contexto; sem ele, a taxa da faixa de idade), sem arredondar, × esse preço ([ADR 0011](../adr/0011-receita-esperada.md)). Nos ganhos, a mediana do `close_value` é 1,0 × o preço de tabela nos 7 produtos ([`process-log/evidencias/explorar-pipeline.txt`](../../../process-log/evidencias/explorar-pipeline.txt)).
- Sem idade (sem data de início), não há chance: `chance` é `null` e a tela diz "Não dá pra calcular a chance".
- A chance diz se negócios com essa idade costumam fechar. O score junta essa chance (contra a melhor faixa) com o que só o vendedor sabe; o preço nunca entra nele.
- Conta, porte e setor entram em `contexto` e são fatores candidatos do motor; neste dataset nenhum entrou na nota (o motor mediu). Nenhum deles muda o grupo.
- Faixa sem nenhum negócio no replay tem taxa `null`, não zero.
