---
id: B7Q3
project: LeadScorer
subject: Realinhamento de escopo: distribuição como ranking personalizado por especialização
author: dcvr@
status: accepted
created: 2026-07-18
updated: 2026-07-18
---


# Contexto (por que a decisão é necessária)

O README interno do projeto listava, como objetivo específico, um modelo de distribuição de leads
aos agentes comerciais. A verificação da especificação do desafio build-003, em fonte primária
(README do desafio, obtido via raw.githubusercontent.com), estabeleceu que a distribuição de leads
a agentes não é entregável exigido nem critério de avaliação: o desafio exige a lógica de
scoring/priorização explicável, a documentação e o process log, e menciona apenas, como bônus, o
filtro por vendedor, gerente ou região. A distribuição era, portanto, escopo autoimposto.

Adicionalmente, a análise exploratória (1J8R) estabeleceu que o único sinal robusto do agente
é a sua capacidade de produto demonstrada, e não win rate, velocidade ou ticket. Esse sinal pode
ser incorporado diretamente ao indicador de scoring como uma dimensão, personalizando o
ranqueamento por agente, o que torna um modelo de distribuição separado redundante.


# Decisão (o que foi decidido)

A distribuição de leads deixa de ser uma tarefa e um objetivo separados. A capacidade
demonstrada do agente é incorporada ao indicador de scoring como a dimensão de especialização
do agente, de modo que o sistema produz um ranqueamento de oportunidades personalizado por
agente. Todos os agentes veem as oportunidades potenciais não iniciadas, ordenadas pela sua
própria especialização; cada agente
vê as suas oportunidades iniciadas. Não há algoritmo de alocação nem atribuição um-a-um.


# Alternativas consideradas (o que mais foi ponderado)

- Manter a distribuição como tarefa separada (5T6Q), com um algoritmo de alocação que casa leads
  a agentes com equilíbrio de carga: rejeitada por adicionar complexidade não exigida pelo
  desafio e por duplicar o sinal de capacidade que o scoring já incorpora;
- Empurrar leads aos agentes (modelo de push) em vez de expô-los para escolha (modelo de pull):
  rejeitada para o MVP por exigir política de alocação e de carga, mantendo-se o modelo de pull,
  mais simples e alinhado à ausência de posse de carteira observada nos dados.


# Consequências (o que resulta da decisão)

- O projeto simplifica-se: um modelo em vez de dois, sem algoritmo de alocação;
- A habilidade de venda passa a integrar o indicador principal, e o ranqueamento torna-se
  personalizado por agente;
- Perde-se a garantia de equilíbrio de carga e de cobertura, própria de um modelo de alocação; é
  uma limitação aceitável no MVP e documentada;
- A tarefa 5T6Q é cancelada, absorvida pela 3RJ8, e a dependência da 8W2N é atualizada;
- O README e a nota de síntese da análise exploratória são revisados para refletir o
  realinhamento.


# Relações

- supersedes:
- superseded-by:
- related-tasks: 3RJ8, 5T6Q, 8W2N
