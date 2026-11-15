# A contribuição do Rodrigo

Este documento responde a uma pergunta: o que o Rodrigo acrescentou que a IA sozinha não faria. Cada item tem três partes: **o que ele disse ou decidiu**, **o que isso virou no produto** (com onde conferir) e **sem isso**, o que a IA tinha proposto ou faria por padrão. As mensagens dele estão na íntegra em `process-log/prompts-do-rodrigo.md`. Os números vêm da API do app, na data simulada padrão (4 dez 2017) quando não há outra data; os principais também são recalculados do zero pelo script de conferência (`solution/verify.py`). Os nomes de tela em "Onde ver" são os do app (capturas em `docs/app/`), e a rota da API indicada permite conferir o dado.

## 1. "Esfriou é menos pior que Perdeu"

- **Disse:** "muitos vendedores abandonam por esquecimento, outros deixam em aberto para nao marcar que perdeu e contabilizar algo negativo... Esfriou é menos pior que Perdeu".
- **Virou:** a faixa **Sem desfecho** (deal aberto há mais do que o maior ciclo já visto na base, 138 dias; sai da fila e fica sem score) e uma segunda taxa de ganho que conta esses deals como não ganhos. Daniell Hammack: 59,5% na taxa oficial, 46,8% contando os 47 deals sem desfecho. Onde ver: Foco da semana e Meu time; `/api/seller` e `/api/team`; no código, `solution/engine/core.py` (classe `Snapshot`) e `solution/engine/rules.py` (`rate_with_stale`).
- **Sem isso:** o deal parado seria só um deal antigo, com chance baixa, no fim da lista. A taxa oficial (ganhos sobre ganhos mais perdas) seria o único número, e ela melhora justamente quando o vendedor não registra a perda.

## 2. Empurrar a data e registrar atividade

- **Disse:** "Ficar atualizando a data de fechamento, registrar atividades na oportunidade etc.." (como um deal parado ganha cara de ativo).
- **Virou:** o score usa só a data de entrada em negociação, que ninguém atualiza. A tela Fontes de dados lista o histórico da data prevista e as atividades com data e tipo como requisitos de uma integração real, com a nota de que vêm da prática de CRM. Código: `solution/engine/quality.py`, função `sources`.
- **Sem isso:** esta base nem tem esses campos, então a análise da IA não teria como enxergar o problema. Numa integração real, um score baseado em "última atividade" ou "data prevista" premiaria o deal maquiado.

## 3. O gestor quer as duas leituras

- **Decidiu:** "Traria as duas opções" (pipeline declarado e pipeline real).
- **Virou:** declarado e vivo lado a lado, nunca um no lugar do outro. Time de Rocco Neubert: US$ 824.840 declarados, US$ 438.104 vivos (53%). Onde ver: Meu time; `/api/team`; `solution/engine/team.py`.
- **Sem isso:** o caminho mais curto seria trocar o número do CRM por um número "corrigido". O gestor perderia a referência que já conhece e não veria a distância entre os dois.

## 4. Nem todo vendedor abre o sistema

- **Disse:** "isso de abrir na segunda feira é relativo.. Tem alguns que nao tao nem ai pra nada, depende 100% do cliente cobrar e chamar.. e outros que sao hunter".
- **Virou:** o foco da semana de cada vendedor também sai como uma mensagem pronta, que o gestor copia e envia. Onde ver: Meu time; `/api/team`, campo `messages`.
- **Sem isso:** o próprio enunciado do desafio parte de que o vendedor abre a ferramenta na segunda de manhã. A ferramenta só alcançaria os vendedores que já se organizam sozinhos.

## 5. "Fácil e rápido de validar"

- **Disse:** "Não quero algo que faça ser dificil de rodar [...] queria que fosse facil e rapido de validar sabe?".
- **Virou:** três escolhas. Acesso simulado sem senha (escolher vendedor ou gestor e a pessoa). Máquina do tempo: qualquer uma das 26 segundas de jul a dez 2017, com o desfecho revelado ao lado da lista. Servidor só com a biblioteca padrão do Python, que sobe com `python3 server.py`.
- **Sem isso:** a validação dependeria de confiar na prova agregada. Com a máquina do tempo, quem avalia escolhe a data e vê o resultado: em 4 dez 2017, com desfecho até 31 dez (27 dias, porque a base acaba aí), a lista do score do Daniell teve 5 vendas (US$ 25.687); a lista só por valor, 0.

## 6. O inventário antes da análise

- **Decidiu:** "quais infos temos dos clientes e oportunidades? quero saber antes de te responder essa analise". Depois, com o inventário, propôs hipóteses próprias (seção 9).
- **Virou:** as hipóteses testadas, que aparecem em Como o score funciona, tabela de sinais testados (`/api/score-model`, campo `signals`). A tela Qualidade dos dados, que ele também pediu, mostra o que a base tem e o que falta.
- **Sem isso:** as hipóteses da seção 9, que revelaram a armadilha do campo cliente, foram propostas por ele depois de ver o inventário.

## 7. Decisões de produto

| Pedido dele | O que virou | Onde ver |
|---|---|---|
| "Temos que entregar tambem um score para os deals" | Score de 0 a 100 por deal, com o porquê aberto em cada linha | Foco da semana; `engine/core.py` |
| "Insights da Gabi", com "perda escondida" | Três cartões no Foco da semana e três na pauta do Meu time. São calculados por regra, não por um modelo de linguagem: cada um traz o número e a ação; o de taxa de ganho mostra a conta no próprio texto | Foco da semana; Meu time; `engine/seller.py`, `engine/team.py` |
| "visao kamban [...] com as fases" | Pipeline com Prospecção, Em negociação, Sem desfecho, e Ganhos e Perdidos dos 30 dias antes da data | Pipeline; `/api/pipeline` |
| Filtro "Com Cliente" e "Sem Cliente" | Filtro na lista. O teste do campo mostrou que ele adianta o desfecho, então o filtro serve para navegar, não para priorizar | Foco da semana; `engine/seller.py` |
| Tela de clientes com painel de três abas | Dados, Em aberto e Fechadas, com aviso sobre o cliente dos deals abertos | Clientes; `engine/accounts.py` |
| Configurações com lista de CRMs e o alerta escrito por ele | Fontes de dados. O texto dele está no código com o comentário "manter a redação" (só o acento de "vêm" foi corrigido) | Fontes de dados; `engine/quality.py` |
| Transparência: como chegamos aqui e o que cada um fez | Tela Como chegamos aqui, com a coluna "Onde a IA errou" | Como chegamos aqui |
| Identidade parecida com a do G4 OS, como um módulo de vendas | Visual do módulo "Vendas", com o selo "Conceito" sempre visível | Todas as telas; `docs/ux/00-fundamentos.png` |
| UX desenhada antes, no Paper, e exportada | Estudo com 12 pranchas | `docs/ux/` |

Um limite: o desafio já pede lógica de score, então o "score por deal" confirmou um requisito. O que foi dele é a forma: um número por deal, sempre com o porquê.

## 8. Decisões de método

- **Recomeçar do zero:** "Esquece o que ja foi feito, vamos começar do zero aqui". Havia uma primeira tentativa do mesmo dia (um app local e uma análise). Ele descartou em vez de remendar.
- **Não olhar outros candidatos** e **discutir antes de construir:** antes de qualquer código vieram as três perguntas sobre o uso do CRM. Depois, a análise, o aceite do score e o estudo de telas. O app só começou a ser construído com "Pode iniciar o desenvolvimento".

## 9. Ideias dele que foram testadas e não entraram

| Hipótese | O que o teste mostrou | Por que foi útil mesmo assim |
|---|---|---|
| Tempo de fechamento por produto ("Fechar um desenvolvimento de website e um de um software + app tem prazos diferentes") | As medianas ficam entre 39 e 52 dias. Só o GTK 500 foge (69 dias), com 9 vendas | O produto entra só pelo preço. A tela Como o score funciona mostra o teste, então o vendedor sabe que a pergunta foi feita |
| Faturamento do cliente ("se ela nao tem dinheiro pra comprar, nao vai fechar") | Entre os fechados, a taxa de ganho é 63,2%, 63,0% e 63,2% do menor ao maior terço de faturamento (Como o score funciona, `/api/score-model`; `hyp.py` faz o mesmo teste em quatro faixas: 64,4%, 61,2%, 64,6% e 62,5%). Entre os abertos aparecia um sinal | Investigar esse sinal revelou que o cliente dos deals abertos não é confiável: vazio em 68% no fim da base; no resto, a regional do vendedor bate com a do cliente em 32% dos casos, contra 95% nos fechados |
| Histórico de compras | Parecia forte: entre os deals com cliente que entraram de 1 abr a 14 ago 2017, 22,3% ficaram sem desfecho quando o vendedor nunca tinha vendido ao cliente, e 3,6% quando já tinha. Entre os fechados, 59,5% com venda anterior e 60,9% sem | Mesma armadilha. Um score com porte ou histórico dependeria de um campo que falta em 68% dos deals abertos no fim da base (52% em 4 dez 2017) e, no resto, muitas vezes não bate com o vendedor |

Daí veio a regra mais importante do app: o campo cliente nunca entra em chance, score, ordem ou prova. A IA depois mostrou que ele também adianta o desfecho: em 4 dez 2017, nenhum dos 549 deals vivos sem cliente fechou até o fim da base; dos 750 com cliente, 404 viraram venda. Não dá para saber se a armadilha apareceria por outro caminho. Ela apareceu ao testar as hipóteses dele.

## O que foi da IA

- **A fórmula do score** (chance por idade e ponto do trimestre, vezes o preço de tabela) foi proposta pela IA. O Rodrigo aceitou.
- **Toda a análise de dados:** inventário, limpeza dos três nomes com grafia errada, teste de cada hipótese e scripts em `process-log/evidencias/analise/`.
- **A prova e a correção dela:** a IA calculou o "+42%" contra ordenar só por valor. Uma segunda implementação, feita por outro agente sem ver o código, levou ao número justo: +22% contra ordenar por valor já sem os deals sem desfecho, e um ganho menor em outubro e novembro (+10% no app). A comparação com uma regra simples com o mais novo na frente veio depois, no app e em `check2.py`: 1% abaixo dela nesses dois meses. Essa correção não veio do Rodrigo.
- **A maior parte dos erros foi pega pela própria IA**, em conferências e revisões: tabela de ciclo enviesada, ranking de vendedores que era diferença entre regionais, frase de estudo de UX desmentida pelo dado.
- **Desenho e construção:** as 12 pranchas no Paper, as revisões de usabilidade, o motor e a API, feitos por fluxos de vários agentes; a interface, por outro fluxo, com três revisores e um teste final tela por tela no navegador. São 190 testes automatizados passando (185 do motor e da API, 5 da interface); a recontagem às cegas bateu em 33.505 de 33.507 comparações (`process-log/evidencias/revisoes/03-revisao-do-motor-e-da-api.md`).

Em resumo: a IA fez quase todo o trabalho de execução e de verificação. O Rodrigo definiu o problema a partir da prática de vendas e decidiu o que o produto devia fazer e como validar.
