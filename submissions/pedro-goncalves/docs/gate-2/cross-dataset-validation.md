# Validação cruzada dos datasets

## Pergunta

O classificador treinado nas **47.837 solicitações do Dataset 2** pode ser aplicado diretamente
às **8.469 mensagens do Dataset 1**?

## Teste

O modelo final foi executado sobre `Ticket Subject + Ticket Description` de todas as linhas do
Dataset 1. Esse é um teste fora do domínio: as categorias dos dois arquivos não são equivalentes
e não existe rótulo compatível para calcular acerto.

## Resultado

- 49.5% das mensagens ficaram acima do threshold de 75%;
- a confiança mediana foi 74.7%;
- **Hardware** concentrou 7,203 previsões (85.1%);
- o gate de cuidado com o cliente sinalizou 1,574 mensagens (18.6%).

## Interpretação

A confiança aparente não prova transferência. A concentração extrema numa única categoria mostra
que o modelo de suporte interno de TI não deve rotear automaticamente solicitações de clientes.
O cruzamento dos datasets serve para revelar essa fronteira: o Dataset 2 comprova a viabilidade
técnica do classificador em sua própria taxonomia; o Dataset 1 mostra os campos, os riscos de
qualidade e os sinais de cuidado necessários ao fluxo de atendimento.

## Decisão

O protótipo aceita as filas do exercício e processa todas as linhas selecionadas, mas permanece em
modo de observação. A fila de clientes usa seus campos operacionais e o gate de cuidado; a fila de
TI usa o classificador de oito categorias. Uma taxonomia não substitui a outra.
