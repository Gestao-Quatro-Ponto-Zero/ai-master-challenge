# Análise exploratória do dataset CRM

Este documento consolida os achados da análise exploratória dos dados brutos e as suas
implicações para a modelagem de scoring e de distribuição. As consultas que produzem cada
achado residem em 'scripts/eda.sql', a fonte canônica reprodutível; os números abaixo são o seu
resultado sobre a fonte normalizada 'data/normalized/', gerada por 'scripts/normalize.sql' a
partir do dataset obtido pela tarefa 2H5K, conforme o ADR F3N8.

Convenção: os valores monetários são reproduzidos como constam do dataset, cuja moeda não é
especificada na fonte; são tratados como nominais e sem unidade explícita.


## Enquadramento e propósito

O rótulo Won/Lost é o dado central: é o sinal supervisionado do que gera sucesso. A pergunta que
organiza a análise é o que distingue um Won de um Lost. A resposta, sustentada ao longo do
documento com testes de robustez, é que quase nenhum atributo observável distingue Won de Lost.

Disto decorre um enquadramento explícito do MVP, que também deve constar da documentação de
entrega: o objetivo é demonstrar o método de como atacar o problema e como apoiar a decisão do
agente comercial, e não a acurácia preditiva sobre este dataset em particular. O baixo sinal
preditivo é uma limitação documentada, não um defeito da abordagem. O scoring não é, portanto,
um classificador de probabilidade de ganho, o que os dados não sustentam, mas um ranqueamento
por valor econômico e por momentum.

A tese de modelagem adotada é que o sinal não é o que vender nem globalmente quando, mas o
momentum do par cliente-produto: quando vender o produto X para o cliente Y. As
empresas compram quase todos os produtos e recompram de forma recorrente, de modo que o valor
está em sinalizar quando um par cliente-produto está maduro para uma nova venda, e em
reconhecer que esse potencial decai após o engajamento.


## Visão geral do pipeline

O pipeline tem 8.800 oportunidades:

| Estágio | Oportunidades | Percentual |
| --- | --: | --: |
| Won | 4.238 | 48,2% |
| Lost | 2.473 | 28,1% |
| Engaging | 1.589 | 18,1% |
| Prospecting | 500 | 5,7% |

Os estágios formam um ciclo: Prospecting (não engajado), Engaging (engajado, em aberto), Won e
Lost (fechados). Entre os 6.711 fechados, a taxa de conversão é 63,1%. Os 6.711 fechados são a
base rotulada; os 2.089 abertos (Engaging mais Prospecting) são os leads a priorizar. Todos os
sete produtos possuem vendas, do GTK 500, com 15 Won, ao GTX Basic, com 915.


## A invariância da probabilidade de ganho

A taxa de conversão é notavelmente estável em torno de 63% ao ser recortada por praticamente
qualquer dimensão do cliente, do produto ou da geografia: por produto (60,0% a 64,8%), por setor
(61,2% a 64,8%), por região (62,6% a 63,9%), por porte da conta em terços de receita (63,0% a
63,2%) e de funcionários (62,4% a 63,6%), e por localização e pertencimento (todos ~63%). Receita
e funcionários medem o mesmo porte (correlação 0,95). Nenhum desses eixos separa ganho de perda.

A consequência é direta: um scoring de sucesso ancorado em atributos observáveis seria quase
plano. Isto motiva o enquadramento por valor e momentum, e não por probabilidade.


## O que é sinal e o que é ruído no agente

Cada dimensão do agente foi submetida a teste de robustez, o que reverteu conclusões preliminares:

- Win rate: ruído. O desvio entre agentes (3,67 pp) mal supera o esperado por acaso amostral
  (3,45 pp), e apenas 3 de 30 agentes são estatisticamente distinguíveis de 63,1%, próximo dos
  falsos positivos esperados. Não é sinal confiável;
- Velocidade de fechamento: ruído. Embora o ciclo varie muito dentro de um mesmo produto, essa
  variação não é consistente entre produtos (a correlação do ciclo de um agente entre GTX Basic
  e GTX Pro é -0,12); um agente rápido num produto não é rápido no outro. A dispersão vem da
  distribuição de ciclo intrinsecamente larga, não de uma habilidade estável;
- Ticket: derivado, não habilidade. Como o valor de ganho acompanha o preço de tabela, o ticket
  típico de um agente é apenas o reflexo do mix de produtos que ele vende;
- Especialização por linha de produto: sinal real e forte. O desvio do percentual de GTX entre
  agentes (20,9 pp) é cinco vezes o esperado por ruído (4,0 pp), e 22 de 30 agentes são
  significativamente distintos da média. O caso extremo é o GTK 500, ganho apenas por três
  agentes (Elease Gluck, Rosalina Dieter, Markita Hansen), com contagens de 3 a 7 contra menos
  de 0,5 esperado por acaso, enquanto 27 agentes nunca o venderam.

A única alavanca robusta do agente é, portanto, qual produto ou linha ele comprovadamente vende.
A distribuição deve rotear por capacidade de produto demonstrada, não por win rate, velocidade
ou ticket. Gerente e região discriminam pouco.


## Base de clientes e ausência de afinidade agente-cliente

São 85 contas, em 10 setores e 15 países, com 83,5% nos Estados Unidos; 15 têm matriz declarada.
O porte é heterogêneo (receita mediana 1.224, funcionários mediana 2.769). O porte não altera a
probabilidade de ganho, mas escala o consumo: contas maiores fecham mais negócios e com ticket
um pouco maior. Não há cliente predominante: os 20% maiores respondem por 31,7% da receita.

Os vendedores atendem todos os tipos de cliente, mas vendem produtos específicos. A correlação
entre o ticket típico do agente e o porte do cliente que ele atende é -0,15, isto é, nula, e
cada conta é servida por 8 a 29 agentes distintos (mediana 10). Não há posse de carteira nem
afinidade agente-cliente a explorar; a especialização do agente é por produto, ortogonal ao
perfil do cliente. Isto libera a distribuição para casar o lead com o agente por capacidade.


## Retorno econômico

O 'close_value' só está preenchido nos fechados: em Won varia de 38 a 30.288, com mediana 1.117;
em Lost é 0; nos abertos é nulo. O valor de ganho acompanha de perto o preço de tabela do
produto, de modo que esse preço, sempre presente, é o estimador do retorno de um lead aberto. A
linha GTX domina as vendas: 65,5% dos Won e 73,4% da receita. O valor de tabela do pipeline
aberto soma cerca de 4,97 milhões, concentrado em GTX (3,43 milhões); os 15 leads GTK abertos,
que só três agentes podem fechar, somam cerca de 401 mil.


## Momentum: quando vender o produto X para o cliente Y

O momentum é o eixo central e é um sinal por par cliente-produto, não por interação isolada. Ele
tem duas componentes reais.

Cadência de recompra por produto: o intervalo mediano entre compras Won consecutivas do mesmo
produto pela mesma conta cresce com o preço, de 16 dias no GTX Basic e 17 no MG Special a 27 no
GTX Plus Pro. É o relógio que indica quando um par cliente-produto amadurece para uma nova venda.
O intervalo é censurado pela janela de dez meses e é um proxy operacional.

Decaimento após o engajamento: entre os fechados, o ciclo de engajamento a fechamento tem mediana
de 57 dias em Won e 14 em Lost, com um teto idêntico de 138 dias para ambos os desfechos e nenhum
negócio fechado além disso. Esse teto exato sugere uma regra de expiração da oportunidade por
volta de 138 dias. O potencial de vitória decai continuamente com a idade desde o engajamento: a
fração dos Won que fecham em ciclo igual ou superior a uma idade cai de 50% na mediana (57 dias)
para 43% em 68 dias, que é 1,2 vez a mediana e o ponto de inflexão da curva, 24% em 90 dias e
menos de 4% em 120, chegando a zero em 138. Essa curva empírica, a fração de Won com ciclo maior
ou igual à idade, é usada como o peso de momentum, sem parâmetro arbitrário, e é transparente de
comunicar ao vendedor. É um proxy do potencial de vitória restante, não um modelo de sobrevivência
rigoroso, o que basta ao propósito do MVP.

Os leads Engaging estão majoritariamente estagnados: na data de referência (2017-12-31), apenas
298 dos 1.589 (19%) estão dentro da janela viável de 138 dias, 841 entre 139 e 250 e 450 além. As
habilidades de fechador rápido e de recuperador foram testadas e revelaram-se ruído: a velocidade
não é consistente entre produtos, e o share de Won tardio por agente (desvio de 4,6 pontos
percentuais contra 3,8 esperados por ruído, com 4 de 30 significativos) não distingue
recuperadores. Não há base para realocar leads estagnados a supostos recuperadores; o tratamento
correto é a triagem.

Daí uma limpeza dupla da lista de interações abertas: um corte duro em 138 dias, que remove os
leads expirados, e o decaimento contínuo, que ordena o que resta. O score de um lead aberto é o
valor econômico, ancorado no preço do produto, multiplicado pelo decaimento por idade e, quando
há conta, pela maturidade de recompra do par cliente-produto. Estas componentes sustentam duas
listas de decisão: um ranking do que engajar, pelos pares cliente-produto maduros para recompra,
e um ranking invertido das interações abertas, por decaimento, que sinaliza o que desmobilizar.


## Estrutura dos dados e ressalvas de premissa

O dataset é centrado em oportunidades, não em relacionamento. Cada conta é servida por muitos
agentes, a matriz conta-produto está saturada (nenhuma conta compra uma só linha), não há
sequência de up-sell (cerca de metade das contas compra o topo de uma linha antes do produto de
entrada) e nenhuma conta nunca comprou. Portanto, jornada de cliente, ciclo de recompra e
potencial de cross-sell como alavancas de relacionamento não têm sustentação robusta; a cadência
de recompra é usada como proxy operacional do momentum, com essa ressalva.


## Qualidade dos dados

A normalização reside na fonte 'data/normalized/', gerada por 'scripts/normalize.sql', e corrige
o produto 'GTXPro' para 'GTX Pro' (que alinhava ao catálogo de preços), o setor 'technolgy' e o
país 'Philipines'. Permanece um limite de cobertura: 'account' é nulo em cerca de dois terços dos
leads abertos, de modo que a cadência de recompra por conta se aplica apenas ao terço com conta,
e o momentum dos demais recai sobre o estágio e a idade de engajamento. Cinco dos 35 agentes não
têm histórico e recebem leads por perfil de produto, não por histórico próprio.


## Síntese para a modelagem

Scoring de leads (tarefa 3RJ8): ranqueamento por valor econômico esperado, ancorado no preço do
produto, ponderado pelo momentum do par cliente-produto, a saber, a maturidade de recompra quando
há conta e a idade de engajamento com decaimento. Não é uma classificação de probabilidade, o que
se ressalva na entrega.

Distribuição de leads (tarefa 5T6Q): a unidade de atribuição é o par cliente-produto, a
oportunidade, e não a conta; o agente recebe a tarefa de vender o produto X ao cliente Y. O
roteamento é por capacidade de produto demonstrada do agente, o único sinal robusto, com
destaque para os leads GTK, que só três agentes podem fechar; com equilíbrio de carga e política
para os cinco agentes sem histórico, distribuídos por perfil de produto. A atribuição por par,
e não por conta, casa com a especialização de produto do agente e com a ausência de posse de
carteira.

Nota (ADR B7Q3, 2026-07-18): a distribuição deixou de ser uma tarefa separada; a capacidade
demonstrada do agente é incorporada ao indicador de scoring como a dimensão de especialização
do agente, que personaliza o ranqueamento por agente. Os achados acima sobre roteamento por
capacidade permanecem válidos, agora realizados dentro do próprio score.


## Vieses e ressalvas

- O propósito é demonstrar o método e o apoio à decisão, não a acurácia preditiva sobre estes
  dados, cujo sinal para prever o sucesso individual é fraco;
- A estagnação dos leads Engaging sugere acúmulo de negócios nunca marcados como Lost; a idade
  em aberto deve ser lida como inércia, não oportunidade viva;
- A recuperação de leads estagnados é uma hipótese de negócio não suportada pelo histórico, que
  não tem precedente de fechamento além de 138 dias, e deve ser validada por um experimento
  prospectivo, não assumida; o sistema pode sinalizar candidatos, tratando a eficácia como
  hipótese a testar;
- A taxa de conversão global (63,1%) pode refletir a composição do dataset e não é
  necessariamente generalizável;
- As cadências de recompra são censuradas pela janela de dez meses; a moeda não é especificada.
