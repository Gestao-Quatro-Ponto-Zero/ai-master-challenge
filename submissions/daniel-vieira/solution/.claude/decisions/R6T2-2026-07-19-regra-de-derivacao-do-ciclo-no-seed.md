---
id: R6T2
project: LeadScorer
subject: Regra de derivação do ciclo de engajamento no seed
author: dcvr@
status: accepted
created: 2026-07-19
updated: 2026-07-19
---


# Contexto (por que a decisão é necessária)

O ADR N4P8 fixou o modelo de dados do ciclo de engajamento, no qual a oportunidade é o par
conta-produto e cada linha de 'sales_pipeline' é um ciclo, mas delegou explicitamente à tarefa
9P4D a regra de derivação do estado ativo e a materialização de 'opportunities' e 'engagements'.
O dado real impõe decisões que afetam o que é persistido e são custosas de reverter: das 8.800
linhas do pipeline, 1.425 não têm conta (1.088 em Engaging, 337 em Prospecting) e não formam um
par conta-produto válido; as 500 linhas em Prospecting nunca engajaram (sem 'engage_date'); e
142 pares distintos possuem mais de um ciclo Engaging aberto ao mesmo tempo, o que torna a
escolha do agente engajado ambígua. A regra precisa ser inequívoca, determinística e íntegra do
ponto de vista referencial.


# Decisão (o que foi decidido)

- 'opportunities' é o conjunto dos pares distintos conta-produto entre as linhas com conta, em
  qualquer estágio;
- 'engagements' são as linhas do pipeline em estágio Won, Lost ou Engaging que possuem conta;
- As linhas em Prospecting e as linhas sem conta são excluídas da carga, com o total registrado
  em log. Não se cria entidade sem lastro no dado (por exemplo, uma conta marcadora), preservando
  a integridade referencial estrita;
- O estado ativo do par é 'engaging' quando há ao menos um ciclo aberto (Engaging), senão
  'prospecting'. Entre múltiplos ciclos abertos, o ciclo corrente é o de 'engage_date' mais
  recente, desempatando pelo 'opportunity_id' de proveniência em ordem crescente, o que produz
  uma ordem total e uma escolha determinística;
- 'opportunity_scores' não é semeada nesta fase; o ranqueamento personalizado é computado pela
  aplicação (tarefa 8W2N).

As contagens canônicas resultantes (opportunities 530; engagements 7.212 = 4.238 Won + 2.473
Lost + 501 Engaging com conta; 1.588 linhas excluídas) residem, como fonte canônica, em
'src/verify.lisp'.


# Alternativas consideradas (o que mais foi ponderado)

- Conta marcadora "não atribuída" para acolher os 1.088 ciclos Engaging sem conta: descartada,
  pois polui a tabela de referência com entidade fora do dataset, contraria o N4P8 ("sem lastro
  no dado") e distorce métricas por conta;
- Incluir as linhas Prospecting como engagements: descartada, pois não representam um ciclo
  engajado (sem 'engage_date') e violariam a semântica de 'engagements' como histórico de ciclos;
- Estado ativo por booleano de dois valores: já descartado no N4P8; o ciclo tem quatro situações
  e o histórico precisa preservar os desfechos;
- Desempate não determinístico ou por ordem de leitura: descartado, pois tornaria a carga não
  reproduzível.


# Consequências (o que resulta da decisão)

- A carga é reproduzível e determinística, com integridade referencial estrita assegurada pelo
  schema e verificada pós-carga;
- 1.588 linhas do pipeline (500 Prospecting e 1.088 Engaging sem conta) não são materializadas
  como ciclos; a exclusão é deliberada, registrada em log e documentada, e reduz o histórico de
  ciclos ao subconjunto com par conta-produto válido;
- A invariante do estado ativo em 'src/verify.lisp' ('closed_at IS NULL' equivale a ciclo
  Engaging) vale por construção do seed, dado que na fonte todo Engaging tem 'close_date' vazio e
  todo Won/Lost o tem preenchido, sem exceção; o acoplamento entre as duas definições é
  consciente;
- A regra é canônica a partir das migrações e do seed; uma revisão futura exigiria nova carga e
  potencial mudança da semântica dos dados persistidos.


# Relações

- supersedes:
- superseded-by:
- related-tasks: 9P4D, 8W2N
