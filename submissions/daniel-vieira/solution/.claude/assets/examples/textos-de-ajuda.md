# Textos de ajuda das notas explicativas (para revisão)

Este documento transcreve, para revisão, os textos das notas de ajuda exibidas ao pousar o
ponteiro sobre os rótulos do potencial e das dimensões nos protótipos da interface. A fonte
canônica de cada texto é o próprio arquivo HTML do protótipo; este documento é um anexo de apoio
e não normativo. Os pesos abaixo são os do modelo canônico, expressos como o peso relativo de
cada dimensão na média geométrica ponderada.

As telas que exibem estas notas são a lista de oportunidades disponíveis
('example-disponiveis-dark.html'), a lista de oportunidades engajadas
('example-engajadas-dark.html') e a tela inicial do agente ('example-home-agente-dark.html').
Quando o texto varia conforme a tela, as variantes são indicadas.


## Potencial

- Todas as telas:

"**Potencial da oportunidade** (0 a 100)  
Potencial de venda do produto indicado para o cliente específico. Média geométrica ponderada das
quatro dimensões de decisão: Momentum, Retorno, Afinidade e Especialização. Após o engajamento,
sofre decaimento temporal, acompanhando o decaimento do Momentum."


## Momentum

- Todas as telas:

"**Momentum** (0 a 100)  
Eixo primário do ranqueamento. Exprime o comportamento e recorrência de compra do cliente no
tempo para o produto indicado. Medida de maturidade para (re)compra. Após o engajamento, sofre
decaimento temporal. Recebe peso 33%."


## Retorno

- Todas as telas:

"**Retorno** (0 a 100)  
Exprime o potencial econômico da transação, ancorado no ticket médio do cliente para aquele
produto, com recuo por setor. Recebe peso 27%."


## Afinidade

- Todas as telas:

"**Afinidade com o produto** (0 a 100)  
Exprime interesse potencial do cliente no produto indicado. Medida da afinidade histórica do
cliente pelo produto, ancorada no volume de negócios fechados anteriormente. Recebe peso 23%."


## Especialização

- Todas as telas:

"**Especialização do agente** (0 a 100)  
Exprime habilidade histórica do agente em obter sucesso na venda do produto indicado.
Personaliza o ranqueamento por agente. Recebe peso 17%."


## Diligência (desconsiderado no MVP)

- Todas as telas:

"**Diligência do cliente** (0 a 100)  
Exprime a diligência do cliente em fechar transações, com base no comportamento histórico,
ancorada no tempo médio de fechamento. Recebe peso 0%."


## Atividade (desconsiderado no MVP)

- Todas as telas:

"**Atividade do cliente** (0 a 100)  
Exprime o grau de recência e atividade de consumo do cliente. É um indicador baseado no inverso
do tempo de inatividade de compra do cliente. Medida de temperatura da relação do cliente
conosco. Recebe peso 0%."
