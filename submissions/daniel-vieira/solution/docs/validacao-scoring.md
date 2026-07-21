# Relatório de validação do scoring

Este relatório consolida a validação de robustez do indicador composto (tarefa 3RJ8, Fase 5). A
metodologia reside em 'docs/metodologia-scoring.md' (ADR C4X9); a computação reprodutível está
em 'src/validation.lisp', invocável por 'run-validation', que é a fonte canônica dos valores
aqui reportados.

Como o composto é uma função determinística de features documentadas e pesos arbitrados, não há
treinamento e, portanto, não há sobreajuste a detectar: a validação out-of-sample no sentido de
aprendizado de máquina não se aplica. Conforme o Handbook (Step 8), a validação de um indicador
composto sem alvo discriminativo é sobre robustez, consistência e transparência, e não sobre
acurácia preditiva. A invariância da conversão estabelecida na EDA (~63% em qualquer recorte)
é o controle negativo que dispensa um classificador de probabilidade.


## Método

- Não-degenerescência: a correlação de ranking de Spearman entre o composto e cada dimensão, sobre
  o conjunto agregado de todas as triplas, mais uma ordem arbitrária determinística como piso;
- Sensibilidade à normalização: o Spearman e a sobreposição do top-20 entre o composto sob
  percentil e sob min-max;
- Sensibilidade aos pesos: sobre um conjunto de cenários de peso, a estabilidade do top-20 e a
  faixa de posto mediana;
- Seleção da forma de agregação: 'aggregation-comparison' reproduz as correlações e a robustez à
  normalização sob a forma multiplicativa inicial e sob a média geométrica em vários pesos de
  momentum, o que fundamentou a escolha da média geométrica e do peso 0,5;
- Validade de face: os extremos do ranqueamento e o afundamento por momentum.


## Resultados

Não-degenerescência, sobre 9.835 triplas, a correlação de Spearman do composto contra:

| Baseline | Spearman |
| --- | --: |
| Retorno | 0,01 |
| Afinidade | 0,28 |
| Especialização | 0,32 |
| Momentum | 0,76 |
| Ordem arbitrária | 0,01 |

Sensibilidade à normalização, para um agente representativo: Spearman entre o composto sob
percentil e sob min-max de 0,96; sobreposição do top-20 de 0,54.

Sensibilidade aos pesos: 7 de 20 do top-20 permanecem no top-20 em todos os cenários; a faixa de
posto mediana entre os cenários é de 79 posições.


## Interpretação

- Mistura genuína, não degenerada. O composto correlaciona-se positivamente com o momentum (o eixo
  primário), com afinidade e especialização (as dimensões de valor contribuem), e é praticamente
  nulo contra a ordem arbitrária. Não é redundante com uma única dimensão nem é aleatório;
- Robustez à normalização alta. O Spearman de 0,96 entre percentil e min-max indica que a escolha
  de normalização quase não altera o ranqueamento. A média geométrica corrigiu a fragilidade da
  forma de agregação inicial, cuja robustez era de apenas 0,62, o que 'aggregation-comparison'
  reproduz;
- Quando ancorado no preço de tabela, o retorno contribuía pouco para a ordenação fina, com
  correlação de posto próxima de zero, pois tinha só sete níveis, um por produto. Com o
  ancoramento no ticket médio do cliente para o produto, ora implementado (ADR R4T9), o retorno
  passa a ter muitos mais níveis, o que atenua essa limitação; a EDA adverte, porém, que o valor
  fechado acompanha de perto o preço de tabela;
- A estrutura primária do ranqueamento, regida pelo momentum, é robusta, mas a ordenação fina
  entre os pares maduros depende dos pesos arbitrados das dimensões de valor, como a estabilidade
  do top-20 e a faixa de posto evidenciam. O instrumento deve ser lido como um apoio de
  priorização da região de topo, não como uma ordem total precisa; a dependência dos pesos é
  esperada, pois os pesos são juízos de valor (Handbook).


## Validade de face

- O afundamento por momentum verifica-se: um par recém-fechado, com momentum 0, recebe
  composto 0 ainda que a afinidade e a especialização sejam altas;
- As faixas são coerentes: o composto varia de 0 a cerca de 81 e o momentum de 0 a 100 na saída;
- Os topos de um agente concentram pares maduros, de alta afinidade e alta especialização para
  o seu perfil de produto.


## Limitações e trabalho futuro

- A validação estabelece robustez, não acurácia preditiva, que a EDA já declarou fraca; um backtest
  preditivo é de valor limitado, pois não há treinamento nem sobreajuste a detectar, o decaimento
  do momentum é quase circular in-sample e a janela de dez meses é curta;
- A sensibilidade aos pesos foi medida por cenários determinísticos. O experimento de
  Monte Carlo completo, com as bandas de incerteza por mediana e percentis 5 e 95 recomendadas pelo
  Handbook, fica como refinamento futuro;
- As correlações agregadas repousam sobre triplas não independentes, pois as dimensões de par se
  repetem entre agentes, variando apenas a especialização; a conclusão se mantém, mas o peso
  efetivo do momentum é algo inflado.
