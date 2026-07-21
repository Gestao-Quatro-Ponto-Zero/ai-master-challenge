---
id: N4P8
project: LeadScorer
subject: Modelo de dados do ciclo de engajamento
author: dcvr@
status: accepted
created: 2026-07-19
updated: 2026-07-19
---


# Contexto (por que a decisão é necessária)

A concepção da aplicação, consolidada na tarefa M5T2, requer um modelo de dados que sustente o
ciclo de engajamento (ranqueamento, seleção, decaimento, fechamento e expiração) e o
ranqueamento personalizado por agente. O dataset de origem mistura histórico e estado em uma
única tabela, 'sales_pipeline', na qual cada linha é uma transação individual rotulada por
estágio, e a hierarquia comercial reside em 'sales_teams'. A estrutura de armazenamento precisa
ser decidida antes de a tarefa 9P4D materializar as migrações, pois afeta a arquitetura de
armazenamento e é custosa de reverter. A especificação detalhada reside em
'docs/concepcao-inicial.md', seção "Modelo relacional".


# Decisão (o que foi decidido)

Adota-se o modelo relacional especificado na concepção, com as seguintes escolhas estruturais:

- A oportunidade é o par conta-produto, e não a transação do dataset; cada transação histórica é
  um ciclo, registrado em 'engagements'. O identificador de oportunidade do CSV é mantido apenas
  como proveniência;
- O estado ativo do par ('prospecting' ou 'engaging') é separado do histórico imutável de
  ciclos; os desfechos 'won', 'lost' e a expiração são eventos em 'engagements', e o par reentra
  em 'prospecting' com o potencial decaído após o desfecho;
- O ranqueamento é personalizado por agente em 'opportunity_scores', com uma linha por par
  oportunidade-agente e os indicadores inteiros de 0 a 100, sendo as duas dimensões inertes
  nulas;
- As entidades de referência são semeadas dos CSV normalizados, com 'regional_offices',
  'sales_managers' e 'sales_agents' derivados de 'sales_teams', e a identificação por login de
  seleção com username sem senha;
- A nomenclatura segue 'std-sql.md', os valores monetários são inteiros na menor unidade com
  código ISO 4217 e os instantes são UNIX em milissegundos, em UTC.


# Alternativas consideradas (o que mais foi ponderado)

- Manter a oportunidade como a transação do dataset: descartado, pois não modela o par
  recorrente nem o estado ativo único, ambos necessários ao ciclo de engajamento;
- Representar o estado da oportunidade por um booleano de dois valores: descartado, pois o ciclo
  tem quatro situações e o histórico precisa preservar os desfechos;
- Criar uma entidade de escritório e códigos de time e username sem lastro no dado: descartado,
  pois a hierarquia escritório-gerente-agente é limpa e derivável de 'sales_teams';
- Persistir os indicadores como ponto flutuante: descartado, pois a interface exibe inteiros de
  0 a 100, que é a forma armazenada.


# Consequências (o que resulta da decisão)

- O seed materializa 'opportunities' como os pares distintos e 'engagements' como as linhas do
  pipeline, exigindo uma regra explícita de derivação do estado ativo; a complexidade concentra-
  se na tarefa 9P4D;
- O ranqueamento personalizado recomputa uma pontuação por par disponível e agente a cada
  minuto; a implicação de escala é aceitável para o MVP, e a distribuição explícita fica para
  produção, conforme o ADR B7Q3;
- O modelo torna-se a fonte canônica quando 9P4D produzir as migrações numeradas; até lá, a
  concepção é a especificação;
- A adesão a 'std-sql.md' e às regras monetária e de tempo da casa é assegurada desde o schema.


# Relações

- supersedes:
- superseded-by:
- related-tasks: M5T2, 9P4D, 8W2N
