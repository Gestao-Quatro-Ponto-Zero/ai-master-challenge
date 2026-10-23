# Sessão 06 — Motor de pontos, score de qualidade, painel do manager e verificação

**Data:** 2026-10-23 · **Ferramentas:** Claude Code (Claude Opus 5.5) como coordenador; workers do Orca para a construção, cada um com spec em arquivo · **Etapas:** E3 construir, E4 verificar, E5 documentar

## Problema

O vendedor abre a ferramenta na segunda de manhã e pergunta "onde eu foco hoje?". O enunciado pede três coisas que esta sessão fecha:

- **lógica de scoring que "não é só ordenar por valor"** (L66);
- o vendedor **entender "por que" o score é alto ou baixo** (L67; L98: "Explainability ganha. Se o vendedor entender POR QUE o deal tem score 85, a ferramenta é 10x mais útil que um número sem contexto");
- um scoring que **"vai além do óbvio"** (L86), com tempo no pipeline, tamanho da conta, produto e vendedor citados como as features óbvias (L96).

**Critério de aceite:** o sistema calcula a chance a partir do histórico, testando os fatores óbvios e os derivados fora da amostra e sem olhar o futuro; o score que o vendedor vê diz se o negócio é bom e explica cada ponto; a ordem da tela e o valor em jogo aparecem separados do score; o manager vê onde o time está perdendo dinheiro; cada número tem teste no `deals.json` e o E2E roda com vídeo.

## O desenho final e o porquê

| Decisão | Por quê (enunciado e dado) |
|---|---|
| **O sistema calcula a chance (motor de pontos).** 19 fatores: os óbvios (idade, produto, série, setor, receita e funcionários da conta, vendedor, gerente, escritório, estágio) e os derivados (idade ÷ ciclo típico do produto e do vendedor; ganhos, perdas e taxa de ganho da conta antes do corte; a conta já comprou; empresa-mãe; preço ÷ receita da conta; carga do vendedor) | L86 pede "além do óbvio": os derivados são as hipóteses que um vendedor experiente levantaria (o negócio está atrasado para o produto dele? a conta já comprou?). Ninguém digita peso: o motor mede |
| **Replay temporal sem olhar o futuro.** Cada fator é medido só com o que se sabia no dia do corte: pontos nos 1.686 abertos em 30/06/2017 (desfecho até 30/09), escolha nos 2.409 abertos em 30/09/2017 (desfecho até 31/12) | Um fator medido com o desfecho dentro dele parece prever e não prevê. O corte separa quem calcula de quem é testado |
| **Seleção gulosa fora da amostra.** Entra o fator de maior AUC na validação; depois, só quem sobe o AUC em 0,005 ou mais | O óbvio "parece" separar (vendedores de 55% a 70% de ganho). Só fica o que se repete em negócios que o cálculo não viu |
| **Só a idade sobreviveu: AUC 0,830.** Vendedor, gerente e escritório pioram a previsão; nenhum outro fator soma | `evidencias/motor-de-pontos-2026-10-23.txt`. A chance fica com a idade porque o motor mediu, e se o dado mudar ela muda sozinha |
| **O score é a qualidade do negócio.** `round(100 × chance da faixa de idade ÷ melhor faixa)` (até 40 dias 90 a 100; 41–50 d 61; 51–60 d 41; 61–90 d 15; acima de 90 d 1), mais as respostas do BANT: +10 por "Sim", −15 por "Não", entre 0 e 100 | O vendedor lê o número do cartão como "esse negócio é bom?" (L98). Os pesos das respostas são **heurística declarada** num config próprio: o histórico não tem essas respostas, então não há como medi-los. "Não" pesa mais porque é um fato que trava a venda |
| **O porquê do score em linhas que o vendedor lê.** "Aberto há 57 dias: 22% dos negócios com essa idade fecharam (a melhor faixa fecha 52%).", uma linha por resposta ("Decisor confirmado: +10") e a posição na lista | L67: entender por que o score é alto ou baixo, em linguagem de vendedor |
| **A ordem da tela é outra coisa:** o grupo (Foque agora, Siga no ritmo, Aborde primeiro, Nutrição), depois o valor esperado (chance × preço) | L66: o valor só ordena dentro do grupo, e a idade decide o grupo. O score não muda a ordem |
| **O valor em jogo fica numa linha própria** ("GTX Pro · US$ 4.821 em jogo") e não entra no score | O mesmo negócio com outro preço tem o mesmo score: multiplicar o preço por 10 não muda o score de nenhum dos 1.589 com data (`evidencias/score-qualidade-2026-10-23.txt`) |
| **Receita esperada pela razão** (taxa base × e^(pontos ÷ 10)) | É a conversão que bate com o que fechou no backtest (ver abaixo). Nos 2.089 abertos: US$ 69.395 |
| **O painel do manager responde "onde meu time está perdendo dinheiro?"** com 4 números, cada um com o que está em jogo: receita esperada do time (US$ 69.395, "nos próximos 3 meses, sem contar negócios novos"); Foque agora sem próxima conversa marcada (33 negócios, US$ 67.896: "vai esfriar se ninguém agir"); pipeline parado (1.532, US$ 3.779.334: "inflando o pipeline"); leads sem primeira conversa (500, US$ 1.073.986: "nunca abordados") | Quem age é o vendedor; o manager precisa saber em que lista agir. Os 4 números são, na equipe, as 4 coisas da tela do vendedor: o que deve render, o que esfria, o que está parado e o que nunca começou |
| **Tabela por vendedor** com as mesmas colunas e as respostas registradas, ordenada pelo Foque sem próxima conversa; os 35 vendedores aparecem, com zero quando for o caso | "Bonus: filtro por vendedor/manager/região" (L100). A ordem é pelo que precisa de ação, não por taxa de ganho: o vendedor não prevê ganho fora da amostra (AUC 0,522), e um ranking por taxa julgaria pessoas por ruído |
| **A curva por idade e a qualidade do dado ficam em "Como a nota funciona"** | São explicação do score, não a decisão da semana do manager |

No West, por exemplo: US$ 38.435 de receita esperada, 17 negócios com US$ 36.502 em jogo no Foque sem próxima conversa, 716 parados com US$ 1.935.958 e nenhum sem primeira conversa; os 500 sem data são todos da Central.

## A verificação

| Item | Resultado |
|---|---|
| `npm test` (fronteiras, typecheck, lint, domínio, API, web, dados) | verde: domínio 143, API 65 (+3 que só rodam com banco), web 88, dados 11 |
| Painel no `deals.json` (`packages/dominio/src/aplicacao/integracao.test.ts`) | cada linha da tabela bate com a fila daquele vendedor; a soma das linhas é o time; o filtro por região muda os números; quem não tem negócio aparece com zero; um "Sim" à próxima conversa tira o negócio da métrica 2 com o preço dele |
| `npm run test:e2e` | 12 de 12, com vídeo em `solution/e2e/videos/` (no painel: as 4 métricas, os 35 vendedores na tabela e o filtro por região) |
| Score (`scripts/score_qualidade.mjs`) | Nutrição entre 1 e 15 (0 dos 1.532 acima); em nenhum dos 27 vendedores com negócio aberto um Siga fica abaixo de um Foque; os 500 sem data com "Score —" |

## Onde desconfiei e conferi

- **A conversão por log-odds errava a receita.** O motor tinha duas formas de transformar pontos em chance. No backtest (2.409 abertos em 30/09/2017, desfecho até 31/12), a log-odds previa US$ 1.077.805 contra US$ 1.251.928 fechados (−13,9%): ela comprimia a curva, e a faixa de 0 a 10 dias, que fechou 49,8%, virava chance de 38%. A razão previa US$ 1.254.677 (+0,2%). Ficou a razão (`evidencias/motor-de-pontos-2026-10-23.txt`, seção "calibração da receita"). É dentro da amostra: mostra coerência, não previsão.
- **Um negócio da Nutrição aparecia com score acima do Foque.** A verificação em produção mostrou, na lista de Zane Levy, o primeiro da Nutrição (GTX Pro, US$ 4.821, chance de 8%) acima do único do Foque agora (GTX Basic, US$ 550, chance de 21%): o valor esperado da lista inteira deixava um produto caro parado passar um negócio vivo barato. Corrigido: a ordem é o grupo primeiro, o valor só dentro dele, e o score mede a qualidade, separado da ordem. A evidência confere, nos 27 vendedores com negócio aberto, que nenhum Siga fica abaixo de um Foque e que toda a Nutrição fica em 15 ou menos.
- **O grupo Foque ficava vazio com negócios vivos no Siga.** Na mesma verificação, vendedores sem nenhum negócio de 41 a 60 dias abriam a tela com o Foque vazio enquanto tinham negócios de até 40 dias, que ainda fecham. Corrigido: quando o Foque de um vendedor está vazio, o Siga dele sobe para o Foque, na ordem da tela; o grupo da idade não muda. Hoje são 3 negócios de 2 vendedores do West; o E2E tem um fluxo para isso, e o painel conta o Foque como a tela do vendedor o mostra.
- **Vazamento pelo "sem dado" no motor.** Neste histórico, todo negócio que fecha tem conta: os sem conta estão todos abertos. Medido na população inteira, qualquer fator de conta "separava" quem tem conta de quem não tem, e o "sem dado" virava sinal do desfecho. Corrigido no motor: a taxa geral dos pontos é a de quem tem o dado, o "sem dado" vale 0, e o efeito de cada fator na seleção se mede só nos negócios que têm aquele dado (`solution/packages/dominio/src/score/motor.ts`, com teste de vazamento).
- **O painel conferido contra a fila.** Os números do painel não são uma conta à parte: o teste recalcula cada linha a partir da fila daquele vendedor e confere a soma com o time, para que o manager e o vendedor vejam o mesmo negócio no mesmo lugar.

## Próximo passo

Publicar em `https://lead-scorer-g4.vercel.app`, conferir a URL no ar e abrir o PR, com o OK do Talles.
