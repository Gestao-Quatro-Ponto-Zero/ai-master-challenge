---
id: G5W2
project: LeadScorer
subject: Dimensão do agente: Especialização por contagem, win rate rejeitado, Opção B diferida
author: dcvr@
status: accepted
created: 2026-07-20
updated: 2026-07-20
---


# Contexto (por que a decisão é necessária)

A revisão da mecânica de scoring (relatório em 'docs/revisao-dimensoes-scoring.md', tarefa S5J4)
constatou que a dimensão do agente aparecia sob nomes divergentes: a metodologia a chamava
"persuasão" e a definia como "o share de Won por agente e produto"; o código a chama
"aderência/adherence"; o README a rotulava "persuasão a produto". A implementação, porém, não
computa share nem taxa alguma: o derivado 'adherence.csv' emite a contagem bruta de Won do agente
por produto e o motor a normaliza por percentil.

A aparente contradição entre "share" na especificação e contagem no código é resolvida pela
análise exploratória. A EDA ('docs/analise-exploratoria.md', seção "O que é sinal e o que é ruído
no agente") estabelece, com teste, que o win rate é ruído: o desvio entre agentes (3,67 pontos
percentuais) mal supera o acaso amostral (3,45 pontos percentuais) e apenas 3 de 30 agentes se
distinguem da média. A EDA conclui que a única alavanca robusta do agente é qual produto ele
comprovadamente vende, de modo que o roteamento deve ser por capacidade de produto demonstrada,
não por win rate. A contagem de Won por agente e produto é a operacionalização correta,
e a recomendação inicial da revisão, de computar uma taxa de vitória, foi retirada por contrariar
a evidência.

Esta decisão complementa o ADR C4X9 (metodologia do composto) e o ADR B7Q3 (personalização por
agente em vez de distribuição), fixando o nome e a mecânica da dimensão do agente.


# Decisão (o que foi decidido)

A dimensão do agente é a Especialização, medida pela contagem de Won demonstrada por agente e
produto, com recuo descontado para a série. É renomeada, de modo canônico, para "Especialização"
(rótulo curto, telas) e "Especialização do agente" (nome longo, documentação e ajuda), unificando
os nomes antes dispersos. A leitura por win rate é rejeitada. A normalização por participação no
produto (Opção B da revisão, a saber, Won do agente sobre o total de Won do produto) é
conscientemente diferida por caráter MVP.

A propagação é segregada em duas partes: a reconciliação da documentação (Parte 1, tarefa
S5J4) e a propagação do nome de exibição às telas, aos exemplos HTML e às notas de ajuda
(Parte 2, tarefa X7F2). A Parte 2 é cosmética, por decisão de projeto: renomeia apenas o que
o usuário vê. Os símbolos internos de código ('adherence'), a coluna de banco
'score_adherence' e o artefato derivado 'adherence.csv' permanecem, em definitivo, com o nome
interno herdado. "Especialização" é o nome de exibição e de documentação, e "adherence" é o
nome interno, numa separação deliberada e estável, e não uma divergência transitória a fechar.


# Alternativas consideradas (o que mais foi ponderado)

- Medir a dimensão por win rate (Won sobre negócios trabalhados): rejeitada, pois a EDA demonstra
  que o win rate é ruído e não separa os agentes, o que injetaria ruído no ranqueamento;
- Normalizar a contagem pela participação no produto (Opção B): não escolhida agora, apenas
  diferida. Atenua a confusão entre a popularidade do produto e a capacidade do agente, mas é
  mudança de mecânica que reabre a validação e a sensibilidade que o MVP deliberadamente conteve;
- Manter o nome "persuasão" ou "aderência" como nome canônico de exibição: rejeitado, pois
  "persuasão" e "share" conotam uma razão ou taxa e destoam do que a mecânica mede, e
  "aderência" duplica um termo já usado para a conformidade a design e a stack.
  "Aderência/adherence" é, ainda assim, retido como nome interno de código e de schema (ver
  Consequências).


# Consequências (o que resulta da decisão)

- A documentação passa a nomear a dimensão de forma única e coerente com a mecânica e com a EDA,
  eliminando a divergência entre especificação e código;
- O código permanece correto. A Parte 2 (X7F2) é cosmética: propaga o nome de exibição
  'Especialização' às telas, aos exemplos HTML e às notas de ajuda, e corrige as docstrings
  dos pesos defasadas frente à agregação geométrica (achado 3). Os símbolos de código
  ('adherence'), a coluna de banco 'score_adherence' e o artefato 'adherence.csv' são
  mantidos, em definitivo, como o nome interno herdado, sem migração de banco nem renomeação
  de símbolos;
- A dimensão passa a ter dois nomes por camada, de forma deliberada e permanente:
  'Especialização' na exibição e na documentação, 'adherence' no código interno e no schema.
  Não é uma divergência transitória a fechar, e sim uma separação exibição-vs-interno assumida;
- A Opção B permanece registrada como refinamento válido para produção, fora do escopo do MVP.


# Relações

- supersedes:
- superseded-by:
- related-tasks: S5J4, X7F2
