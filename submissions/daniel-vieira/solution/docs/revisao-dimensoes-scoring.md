# Revisao da mecanica de calculo das dimensoes do scoring

Este documento registra uma revisao critica da mecanica de calculo de cada dimensao do modelo
de ranqueamento de oportunidades. O criterio de avaliacao e a racionalidade logica, o bom senso
e a praticidade funcional de cada mecanica, e nao a acuracia preditiva, que a propria
metodologia declara fraca por insuficiencia do dataset em largura e profundidade.

A revisao confronta a intencao declarada em 'docs/metodologia-scoring.md' com a implementacao
canonica, a saber, os valores brutos e parametros empiricos em 'scripts/modeling.sql' e o motor
de composicao em 'src/scoring.lisp', com a configuracao de pesos em 'config/model.lisp'. As
referencias de linha remetem ao estado do repositorio no commit 3ffe841 (2026-07-20); em caso
de divergencia posterior, o codigo prevalece sobre este texto.

Os achados sao apresentados em ordem decrescente de gravidade. Cada dimensao recebe um veredito
qualificado. O tratamento dos achados e conduzido pela tarefa S5J4, cuja Parte 1 e documental e
cuja Parte 2 (tarefa X7F2) propaga a renomeacao da dimensao do agente ao codigo e as telas.

Nota de revisao (2026-07-20): o achado 1 foi reenquadrado apos a evidencia da EDA de que o win
rate e ruido e de que a alavanca robusta do agente e a especializacao por produto, medida por
contagem. A recomendacao inicial de computar uma taxa foi retirada; ver a secao do achado 1.


## Achado 1 --- Nomenclatura da dimensao do agente incoerente com a mecanica e a EDA

A dimensao do agente aparecia sob nomes divergentes: a metodologia a chamava "persuasao" e a
definia como "o share de Won por agente e produto" ('docs/metodologia-scoring.md', dimensao 4);
o codigo a chama "aderencia/adherence"; o README a rotulava "persuasao a produto". A
implementacao nao computa share nem taxa: o derivado 'adherence.csv' emite a contagem bruta de
Won do agente no produto ('scripts/modeling.sql', emissao 3), e 'cell-adherence'
('src/scoring.lisp') devolve essa contagem, ou a contagem na serie descontada por
'*adherence-series-discount*' no recuo.

A evidencia da EDA resolve a aparente contradicao a favor do codigo. A EDA
('docs/analise-exploratoria.md', secao "O que e sinal e o que e ruido no agente") estabelece,
com teste, que o win rate e ruido --- o desvio entre agentes (3,67 pp) mal supera o acaso
amostral (3,45 pp) --- e que a unica alavanca robusta do agente e qual produto ele
comprovadamente vende, de modo que o roteamento deve ser por capacidade de produto demonstrada,
nao por win rate. A contagem de Won por agente e produto e, portanto, a operacionalizacao
correta da capacidade demonstrada; computar uma taxa injetaria justamente o ruido que a
metodologia evita.

Logo, o defeito nao esta no codigo, e sim na nomenclatura: o termo "persuasao", e a palavra
"share" na metodologia, conota uma razao ou taxa e destoa do que a mecanica mede, a
especializacao por produto. A recomendacao inicial desta revisao, de computar uma taxa de
vitoria, foi retirada por contrariar a evidencia da EDA.

Resolucao adotada (Opcao A): manter a contagem; renomear a dimensao para "Especializacao"
(rotulo curto) e "Especializacao do agente" (nome longo); rejeitar a leitura por win rate; e
diferir conscientemente a normalizacao por participacao no produto (Opcao B) por carater MVP. A
renomeacao e registrada no ADR G5W2, propagada a documentacao na Parte 1 e ao codigo e as telas
na Parte 2 (tarefa X7F2).

Ressalva menor de mecanica, independente do nome: a populacao de referencia da normalizacao
inclui as 245 celulas agente-produto, a maioria com valor zero, de modo que, no percentil, a
dimensao aproxima-se de um binario "tem algum Won no produto ou nao tem". E aceitavel numa
dimensao suave e de menor peso, mas fica registrado.

Veredito: defeito de nomenclatura, nao de racionalidade da mecanica; corrigido por renomeacao.


## Achado 2 --- Momentum neutro de 0,5 inativa a dimensao no grosso dos potenciais

Para a lista de potenciais, 'momentum-maturity' ('src/scoring.lisp') atribui
'*maturity-neutral*', igual a 0,5, a todo par sem historico de compra (dias desde o ultimo
fechamento nulo) ou cujo produto nao tem cadencia estimada.

A logica de fundo e valida: um par nunca comprado nao tem relogio de recompra, de modo que um
valor neutro e honesto, e zera-lo excluiria justamente o cross-sell frio que se deseja promover.
O problema e de praticidade funcional:

- Na grade de 85 contas por 7 produtos, a maioria das celulas nunca foi comprada. Assim, a
  maioria dos potenciais recebe momentum 0,5 constante. Como o momentum e o eixo de maior
  peso mas fica inerte nessa maioria, a ordenacao desses pares passa a ser regida inteiramente
  por retorno e afinidade, de modo silencioso. O momentum so discrimina na minoria de pares com
  historico;
- O valor 0,5 especifico, em vez de 0,3 ou 0,7, e arbitrario e, por entrar geometricamente com o
  maior expoente, fixa o nivel de base de toda a populacao nunca-comprada frente a populacao com
  historico. Consequencia concreta: um par nunca comprado (0,5) supera, em momentum, um par que
  comprou ha pouco e esta a 30% da cadencia (0,3). Isto e defensavel, pois nao se reaborda quem
  comprou recentemente, mas e uma decisao de ranqueamento embutida em um unico parametro que
  merece estar explicita.

Recomendacao: registrar na metodologia o efeito da ancora neutra sobre a populacao
nunca-comprada e avaliar se o valor deve permanecer em 0,5 ou ser parametrizado por evidencia.

Veredito: ressalva material, mecanica aceitavel para o MVP mas com efeito nao documentado.


## Achado 3 --- Docstrings defasadas frente a forma de agregacao corrente

As docstrings de '*weight-economic*', '*weight-affinity*' e '*weight-adherence*'
('src/scoring.lisp') e a docstring de 'multiplicative-composite' descrevem os pesos como "razoes
de troca entre as tres dimensoes substituiveis da base aditiva". Essa linguagem e herdada da
forma multiplicativa, hoje inativa: a configuracao corrente e ':composite-form :geometric'
('config/model.lisp'), na qual os quatro pesos sao expoentes da media geometrica, nao
coeficientes de uma base aditiva. Nada quebra em execucao, mas o texto contradiz a forma
efetivamente aplicada e pode induzir o leitor ao erro.

Recomendacao: atualizar as docstrings para refletir o papel dos pesos como expoentes na
agregacao geometrica, preservando a nota historica apenas onde util. Executado na Parte 2
(tarefa X7F2), por tocar codigo.

Veredito: divida de documentacao, sem efeito de calculo.


## Dimensoes sem objecao de mecanica

- Retorno: a escada de recuo "ticket medio do par, ticket medio do setor por produto,
  preco de tabela" ('scripts/modeling.sql', emissoes 4 e 5) e uma hierarquia de especificidade
  racional, e o recuo e natural, pois a EDA registra que o valor fechado acompanha o preco de
  tabela. A percentilizacao descarta a magnitude absoluta, compromisso ja reconhecido na
  metodologia e aceitavel para um instrumento de ranqueamento;

- Afinidade ou consumo: contagem de Won do par, com recuo para a media do setor por produto
  ('pair-affinity-value' em 'src/scoring.lisp'). Logica coerente. Nota de bom senso: o recuo e
  uma media de contagens, tipicamente fracionaria, enquanto a contagem real e inteira e maior ou
  igual a um, de modo que a expectativa setorial pode ultrapassar uma unica compra real. E
  defensavel como prior de consumo tipico, mas convem ter consciencia do efeito;

- Momentum, decaimento pos-engajamento (iniciadas): a CCDF empirica, fracao de Won com ciclo
  maior ou igual a idade ('scripts/modeling.sql', emissao 2; 'momentum-decay' em
  'src/scoring.lisp'), e um proxy transparente e monotonico decrescente para o potencial de
  vitoria restante, e a ordenacao inversa como sinal de desmobilizacao e coerente. O vies de
  censura a direita (Kaplan-Meier) esta honestamente registrado como cautela consciente na
  metodologia;

- Momentum, forma da corcova e portao: a funcao em corcova e continua e bem-formada, ascendente
  linear ate o pico na cadencia e descendente linear ate zero em '*maturity-churn-multiple*'
  vezes a cadencia ('src/scoring.lisp'), sem descontinuidade nem valor fora de faixa. O braco
  descendente e assumido e assim declarado. O portao nao compensatorio (conta existe; iniciada
  com idade menor ou igual a 138 dias) e sensato e consistente com o comprimento do vetor de
  decaimento;

- Agregacao geometrica: media geometrica ponderada das quatro dimensoes, com piso nas tres de
  base para que um zero normalizado nao anule o indice e sem piso no momentum, para preservar
  o afundamento intencional do recem-fechado ('geometric-composite' em 'src/scoring.lisp'). A
  penalizacao do desequilibrio e a escolha canonica bem fundamentada. A fracao do momentum
  no expoente total e de um terco, o maior peso individual sem dominar, coerente com o objetivo;

- Diligencia e atividade: peso zero ou nulo, justificado por evidencia da EDA, a saber, a
  colinearidade e o sinal invertido da diligencia e a ausencia de contas inativas para a
  atividade. Mante-las carregadas mas sem peso, para completude e ativacao futura em producao, e
  uma decisao sobria e sem efeito no ranqueamento.


## Sintese

| Dimensao ou aspecto                     | Veredito                                        |
|-----------------------------------------|-------------------------------------------------|
| Retorno (economico)                     | Solida                                          |
| Afinidade ou consumo                    | Solida (prior setorial pode superar a evidencia)|
| Momentum, decaimento (iniciadas)        | Solida                                          |
| Momentum, corcova e portao              | Solida                                          |
| Agregacao geometrica                    | Coerente                                        |
| Diligencia e atividade                  | Corretamente inertes                            |
| Momentum, ancora neutra de 0,5          | Ressalva material (achado 2)                    |
| Especializacao do agente                | Defeito de nomenclatura (achado 1)              |
| Docstrings dos pesos                    | Divida de documentacao (achado 3, Parte 2)      |

No conjunto, a arquitetura e racional e, apos a reconciliacao, sustentada pela EDA. O
encadeamento de recuos, o portao nao compensatorio e a escolha da agregacao geometrica revelam
bom senso e praticidade. O achado 1 nao era um defeito de mecanica, e sim de nomenclatura,
resolvido pela renomeacao da dimensao do agente para Especializacao; em menor grau, o achado 2,
o momentum inerte no grosso da lista de potenciais, fica documentado. A mecanica de contagem e a
leitura da Especializacao por contagem, e nao por win rate, sao as sustentadas pela EDA.
