---
id: R4T9
project: LeadScorer
subject: Ancoramento da dimensão de retorno no ticket médio do par conta-produto
author: dcvr@
status: accepted
created: 2026-07-19
updated: 2026-07-19
---


# Contexto (por que a decisão é necessária)

A dimensão econômica do scoring (renomeada para "Retorno") era ancorada no preço de tabela do
produto ('sales_price'), escolha registrada no ADR C4X9 e fundamentada na análise exploratória:
o valor de fechamento acompanha de perto o preço de tabela e as compras são praticamente
unitárias, de modo que o preço, sempre presente, era um estimador direto do retorno econômico de
um lead. Durante a revisão da concepção e da interface, decidiu-se que a dimensão reflita o
valor econômico efetivo da relação do cliente com o produto, e não apenas o preço nominal do
catálogo, medindo o ticket médio do cliente para aquele produto (a média dos valores de
fechamento dos ciclos Won do par conta-produto). A exploração do código confirmou a viabilidade:
a view 'pair_won' de 'scripts/modeling.sql' já agrega por par conta-produto, bastando expor a
média de 'close_value'. Permanece a ressalva da EDA de que o valor fechado acompanha o preço de
tabela, de modo que o ganho de sinal independente pode ser limitado, e o problema estrutural do
arranque a frio, dado que pares sem histórico de venda não têm ticket.


# Decisão (o que foi decidido)

A dimensão de Retorno passa a ancorar-se no ticket médio do cliente para aquele produto, isto é,
na média dos valores de fechamento ('close_value') dos ciclos Won do par conta-produto. Para os
pares sem histórico de venda, adota-se um recuo por setor (a média do valor de fechamento do setor
para o produto, à semelhança do recuo já usado na dimensão de afinidade) e, em último caso, o
preço de tabela do produto. A estrutura do composto, os pesos e o expoente de momentum permanecem
inalterados; muda apenas o insumo da dimensão econômica. A implementação no código e na modelagem
foi realizada na tarefa W8H5 e verificada pela suíte de testes e pelo linter.


# Alternativas consideradas (o que mais foi ponderado)

- Manter o preço de tabela: preserva a simplicidade e evita o arranque a frio, e é sustentado
  pela EDA (o valor fechado acompanha o preço de tabela). Foi preterido por não refletir o valor
  econômico efetivo da relação cliente-produto, que é o objetivo da revisão;
- Ticket médio com recuo direto ao preço de tabela, sem o passo por setor: mais simples, mas com
  menos suavização para pares sem histórico; preterido em favor do recuo por setor, que espelha
  o padrão já adotado na afinidade e é mais informativo que o preço nominal;
- Usar o último valor de fechamento do par ('last_close_value', já disponível) em vez da média:
  preterido por ser mais ruidoso e menos representativo que a média.


# Consequências (o que resulta da decisão)

- A dimensão econômica passa a ter muitos mais níveis (por par, não por produto), o que atenua a
  limitação registrada na metodologia de que ela contribuía pouco para a ordenação fina;
- Introduz-se a dependência de um recuo para o arranque a frio, ausente no caminho anterior por
  preço de tabela; o recuo por setor usa a nova view 'sector_ticket', de média de 'close_value';
- A mudança altera as saídas do scoring e exige a regeneração das fixtures derivadas e a
  atualização dos valores esperados nos testes; a implementação deve seguir o ciclo orientado a
  testes;
- A implementação foi realizada: a view 'pair_won' passou a expor a média de 'close_value', a
  view 'sector_ticket' provê o recuo por setor, as bases emitem a coluna 'economic_value' e o
  motor de scoring consome esse insumo; a divergência entre a decisão e o código foi fechada;
- A verificação canônica foi executada após o provisionamento do dataset e do qlot: compilação
  sem avisos, suíte Parachute verde (59 casos) e linter mallet sem achados, com os derivados
  regenerados via DuckDB.


# Relações

- supersedes:
- superseded-by:
- related-tasks: W8H5, 3RJ8, V7C2
