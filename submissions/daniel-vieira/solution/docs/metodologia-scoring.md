# Metodologia do modelo de scoring de leads

Este documento formaliza o método do indicador composto de priorização de leads da tripla
produto-empresa-agente. Ele descreve princípios, estrutura e fundamentação; os valores concretos
(pesos, limiares, curvas empíricas) residem no código e na configuração da implementação
(Fases 3 e 4 da tarefa 3RJ8) e não são reafirmados aqui. Os achados que sustentam as escolhas
residem na análise exploratória, em 'docs/analise-exploratoria.md'; em caso de conflito, a EDA
e o código prevalecem sobre este texto.

O propósito, herdado do enquadramento da EDA, é demonstrar o método e apoiar a decisão do agente
comercial, e não a acurácia preditiva sobre este dataset, cujo sinal para prever o sucesso
individual é fraco e documentado.


## Enquadramento na prática de scoring de oportunidades

O indicador é um substituto transparente do paradigma canônico de priorização de pipeline, o
valor esperado, definido como a probabilidade de ganho multiplicada pelo valor da transação.
Como a análise exploratória mostrou que a probabilidade de ganho não é aprendível a partir dos
atributos observáveis, ela é deliberadamente substituída pelo momentum, que é o timing, e pela
especialização do agente, que é a sua capacidade de venda demonstrada. O composto prioriza por
valor, timing e capacidade, omitindo conscientemente a propensão.

As dimensões não-de-agente correspondem ao modelo Recency-Frequency-Monetary (RFM), canônico na
mensuração de valor de cliente: o momentum corresponde à recência, a afinidade ou consumo à
frequência e o retorno ao valor monetário. A especialização do agente é a extensão
específica deste problema, o eixo do agente ausente do RFM clássico. O alinhamento a um modelo
estabelecido documenta que a escolha das dimensões não é ad hoc.


## Entidade pontuada e saídas

- A unidade pontuada é a tripla produto-empresa-agente. O indicador de potencial é um valor de 0
  a 100, personalizado por agente pela dimensão de especialização do agente;
- O sistema expõe duas listas de decisão:
  - Potenciais (oportunidades não iniciadas): pares conta-produto conhecidos e não engajados,
    visíveis a todos os agentes, ordenados pelo indicador personalizado, com um filtro de corte
    exibido na interface;
  - Iniciadas (por agente): as oportunidades que o agente engajou, ordenadas pelo decaimento,
    até expirarem por idade ou serem marcadas como Won ou Lost.


## Dimensões

Cada dimensão é normalizada a uma escala de 0 a 100 e exibível na visualização em teia. As quatro
primeiras são computacionalmente ativas; as duas últimas são carregadas por completude
metodológica e transparência, com peso zero ou nulo nesta base, conforme justificado adiante.

1. Retorno: a magnitude econômica do negócio, ancorada no ticket médio do cliente para aquele
   produto, isto é, na média dos valores de fechamento do par, com recuo para a média do setor e,
   em último caso, para o preço de tabela quando o par não tem histórico de venda. A EDA registra
   que o valor de ganho acompanha de perto o preço de tabela, o que torna o recuo natural. O
   ancoramento no ticket médio, em lugar do preço de tabela, está implementado na modelagem e
   registrado no ADR R4T9;
2. Afinidade ou consumo: o volume histórico do par empresa-produto, medido pela contagem de
   negócios Won, com recuo para a classe ou setor onde o par tem pouca história;
3. Momentum: o eixo de peso alto, aplicado multiplicativamente. Tem duas faces conforme a lista,
   detalhadas na seção própria. Incorpora, como sub-componentes de demonstração inertes nesta
   base saturada, a frequência do cliente, a frequência da categoria de produto e uma regra de
   cross ou up-sell do tipo comprou X, compra Y;
4. Especialização do agente: a capacidade de venda demonstrada do agente no produto, medida
   pela contagem de Won do agente por produto, com recuo descontado para a série onde o agente
   tem pouco histórico próprio. A EDA estabelece que o win rate é ruído e que a única alavanca
   robusta do agente é a especialização de produto que ele comprovadamente vende, o que
   fundamenta a contagem e afasta o win rate. A participação no produto (Won do agente sobre o
   total de Won do produto), alternativa da revisão, é conscientemente diferida por caráter MVP
   (ver ADR G5W2). É uma dimensão suave, jamais um portão, para permitir o desenvolvimento do
   agente em produtos que ainda não vende;
5. Diligência (tempo de fechamento): com peso zero no composto e não exibida na listagem. Os
   testes mostram que ela não distingue desfecho e é colinear com o decaimento do momentum: a
   fração da variância do ciclo atribuível à empresa é de 1,4%, a correlação entre a taxa de Won
   e o ciclo mediano da empresa é de 0,019, o produto explica 0,4% da variância do ciclo, e o
   sinal é invertido, pois os negócios Lost fecham mais rápido que os Won. É mantida por
   completude metodológica, sem peso que injete ruído no ranqueamento;
6. Atividade do cliente (inatividade): com peso aproximadamente nulo e não exibida na listagem.
   Nesta base nenhuma conta está mais de 32 dias sem um Won, de modo que a dimensão é quase
   constante e a sua contribuição é nula. É ativável em produção, com janela longa e contas
   realmente inativas.


## Normalização

- A normalização padrão é por percentil, robusta a outlier e à assimetria, e de leitura direta
  ao usuário. A validação reporta a sensibilidade ao método alternativo min-max, conforme a
  recomendação de análise de sensibilidade da literatura de indicadores compostos.


## Ponderação

- Os pesos são arbitrados e documentados, e residem na configuração da implementação. A escolha
  de arbitrar, em vez de aprender os pesos dos dados, é deliberada: não há alvo discriminativo a
  partir do qual aprendê-los, pois a EDA mostra a conversão praticamente plana; aprender os pesos
  ajustaria ruído e contradiria a própria análise.


## Agregação: o composto

A agregação combina um portão não compensatório e uma média geométrica ponderada:

1. Portão de elegibilidade, não compensatório: a tripla é elegível apenas quando a conta existe
   e, na lista de iniciadas, quando o engajamento não excede o corte de expiração observado na
   EDA. Uma tripla inelegível não recebe pontuação;
2. Média geométrica ponderada das quatro dimensões, todas na escala 0 a 100 (o momentum, em
   [0,1], reescalado a 0 a 100). A média geométrica é a agregação não compensatória canônica do
   Handbook (Step 6): penaliza o desequilíbrio, de modo que uma dimensão baixa, inclusive um
   momentum baixo, arrasta o índice, e um momentum igual a 0, o par recém-fechado, o zera. As
   três dimensões da base recebem um piso mínimo para que um zero de normalização não anule o
   índice; o momentum não é pisado, pois o seu zero é o afundamento intencional. O momentum
   recebe o maior peso e permanece o eixo primário, o que atende à exigência de que um par com
   timing ruim afunde independentemente das demais dimensões;
3. As dimensões de peso zero ou nulo entram apenas na exibição, não no valor do composto.

A forma inicial, uma base aditiva multiplicada por um fator de momentum em [0,1], foi substituída
pela média geométrica após a validação da Fase 5 revelar que aquela forma tornava o momentum
dominante por artefato de escala, pois o momentum, ao chegar a 0, tinha dispersão relativa muito
maior que a base, uma média de percentis concentrada no meio, e era apenas moderadamente robusta
à escolha de normalização. A média geométrica, com o peso a controlar a influência em vez de um
acidente de escala, reequilibra as dimensões de valor e é substancialmente mais robusta, o que se
confirmou empiricamente; a decisão está no ADR C4X9 e a evidência em 'docs/validacao-scoring.md'.


## Momentum em detalhe

O momentum é um sinal do par cliente-produto, com duas faces conforme a lista:

- Maturidade de recompra, na lista de potenciais: uma função em corcova do tempo desde o último
  fechamento do par em relação à cadência de recompra do produto. O braço ascendente, um par
  recém-fechado é imaturo e sobe à medida que o relógio de cadência amadurece, é empírico e
  fundamentado nas cadências observadas na EDA. O braço descendente, um par muito além da
  cadência é tratado como possivelmente perdido, é uma suposição documentada, pois esta base não
  tem contas inativas para ajustá-lo;
- Decaimento pós-engajamento, na lista de iniciadas: a função de sobrevivência empírica do
  potencial de vitória restante, a fração de negócios Won cujo ciclo é maior ou igual à idade
  desde o engajamento, com o corte duro de expiração. É um proxy transparente, comunicável ao
  vendedor e sem parâmetro arbitrário, e não um modelo de sobrevivência rigoroso; a sua cautela
  de censura à direita e a alternativa rigorosa estão registradas na seção de cautelas.


## Validação

A validação, executada na Fase 5, adapta-se à ausência de um alvo discriminativo. Como não há
probabilidade de ganho a prever, não há acurácia out-of-sample a medir; o que se valida é a
qualidade do ranqueamento e a robustez das escolhas:

- Comparação com baselines: o ranqueamento do composto é comparado a baselines ingênuos, a saber,
  só-valor, só-recência e uma ordem arbitrária, por correlação de posto de Spearman, o que
  evidencia se o composto é uma mistura genuína, nem redundante com uma única dimensão nem
  aleatória;
- Análise de sensibilidade: a estabilidade do ranqueamento é testada sob o método de normalização
  (percentil versus min-max), a forma de agregação e o peso do momentum, e os pesos de valor, por
  correlação de posto e sobreposição do top-k. As bandas de incerteza por Monte Carlo (mediana e
  percentis 5 e 95) recomendadas pelo Handbook ficam como refinamento futuro;
- Validade de face: a inspeção de que as triplas no topo e na base fazem sentido de negócio.


## Cautelas e literatura

As técnicas adotadas foram confrontadas com a literatura estabelecida. As fontes primárias são
citadas e as cautelas registradas; onde uma afirmação é inferência de aplicabilidade ao nosso
caso, e não afirmação da fonte, isto está sinalizado.

- Agregação e compensabilidade. O Handbook on Constructing Composite Indicators (OECD/JRC, 2008),
  Passo 6, adverte que a agregação aditiva implica compensabilidade total, na qual o desempenho
  fraco em uma dimensão é compensado por valores altos em outras, e exige independência de
  preferências, tratada como premissa forte e pouco realista. A agregação geométrica ou
  multiplicativa oferece não-compensabilidade parcial e recompensa perfis equilibrados; em ambas,
  os pesos são razões de troca, não coeficientes de importância. Aplicação ao nosso composto:
  adota-se a média geométrica ponderada das quatro dimensões, a agregação não-compensatória
  canônica do Handbook, que penaliza o desequilíbrio; um momentum baixo, ou nulo no par
  recém-fechado, arrasta o índice, o que atende à não-substituibilidade do timing. A forma
  inicial, uma base aditiva multiplicada pelo momentum, presumia as três dimensões de valor
  mutuamente substituíveis; a validação da Fase 5 deu razão epistêmica para revisar essa premissa,
  pois aquela forma tornava o momentum dominante por artefato de escala. A alternativa mais
  rigorosa, uma agregação multicritério não-compensatória (Condorcet ou Borda), é descartada para
  o MVP pela inexistência de regra de agregação perfeita (Arrow e Raynaud, 1986) e pelo custo
  computacional;
- Normalização. O Handbook, Passo 5, documenta que o ranking ou percentil não é afetado por
  outliers mas descarta a informação de nível, que o min-max é distorcido por outliers e amplia
  indicadores de baixa variância, e que a padronização dá peso maior aos valores extremos. Ele
  recomenda testar a robustez entre métodos e remover outliers antes de normalizar. Aplicação: a
  normalização por percentil é adequada ao 'close_value', de cauda longa até cerca de 30.000, ao
  custo de descartar a magnitude absoluta, aceitável para um instrumento de ranqueamento; a
  sensibilidade ao min-max é reportada na validação;
- Peso de decaimento por CCDF empírica. Kaplan e Meier (1958) estabelecem que, sob censura à
  direita, o estimador correto da função de sobrevivência é o produto-limite, e que a CCDF
  empírica ingênua é viesada, pois subestima a sobrevivência ao tratar observações ainda em curso
  como se o evento já tivesse ocorrido. Aplicação: a curva de decaimento é a fração de negócios
  Won com ciclo maior ou igual à idade, calculada sobre negócios já fechados; as oportunidades
  ainda abertas são observações censuradas e a sua exclusão enviesa a curva. Adota-se, ainda
  assim, o proxy empírico pela transparência e comunicabilidade ao vendedor e por não ter
  parâmetro arbitrário, com a ressalva de censura registrada; o corte duro de expiração observado
  na EDA limita a instabilidade da cauda, que também afeta o próprio Kaplan-Meier. A
  inconsistência da CCDF empírica sob censura é corroborada por fontes secundárias de análise de
  sobrevivência, não por citação de página do texto canônico;
- Cadência e churn. Os modelos Pareto/NBD (Schmittlein, Morrison e Colombo, 1987) e BG/NBD
  (Fader, Hardie e Lee, 2005) inferem a inatividade não observada a partir da recência e da
  frequência de compras de repetição, e degradam quando a frequência é muito baixa, próxima de
  um, caso em que a recência e a frequência não separam o cliente inativo do ativo que ainda não
  recomprou. Aplicação, marcada como inferência e não afirmada pelas fontes: a matriz
  cliente-produto saturada, com no máximo uma transação por célula em muitos casos, e a janela de
  cerca de dez meses colocam o problema nesse regime degenerado, o que inviabiliza esses modelos
  e justifica o proxy de cadência simples e a inércia da dimensão de atividade nesta base;
- Avaliação sem verdade-fundamental. O Handbook, Passo 7, e Saisana, Saltelli e Tarantola (2005)
  estabelecem que, sem critério externo, a validação é sobre robustez, consistência e
  transparência, e não sobre acurácia preditiva, e que um composto pode ser internamente robusto
  sem estar validado contra qualquer desfecho, sendo o arcabouço teórico o ingrediente primário.
  Recomendam um experimento de Monte Carlo variando simultaneamente as fontes de incerteza,
  reportar o ranking com bandas de incerteza (mediana e percentis 5 e 95), a análise de
  sensibilidade baseada em variância e a correlação de ranking (Spearman, Kendall) como
  ferramenta descritiva de comparação, não como prova de validação. A validação da Fase 5 adota
  essa orientação: o arcabouço teórico é a EDA e esta metodologia, e os baselines, a sensibilidade
  e a validade de face medem robustez, não a acurácia, que a EDA já declarou fraca.


## Ressalvas

- A base tem marcas de dado sintético, a saber, conversão invariante, contas todas quentes,
  preços colados à lista e ciclo travado no corte de expiração, o que limita inferências de
  comportamento de compra e sustenta o enquadramento de demonstração do método;
- O braço descendente da curva de momentum é uma suposição, na ausência de contas inativas;
- A âncora neutra de 0,5 do momentum para o par nunca comprado é constante para a maioria dos
  potenciais, a matriz cliente-produto sendo esparsa, de modo que a discriminação por momentum
  concentra-se nos pares com histórico e a ordenação dos demais recai sobre o retorno e a
  afinidade; o valor 0,5 é arbitrado e mantido no MVP, sinalizado para calibração em produção;
- As dimensões de diligência e de atividade, e a sub-regra de cross ou up-sell, são
  inertes nesta base e mantidas por completude, sem distorcer o ranqueamento;
- O modelo é estático por escolha de MVP; em produção, um laço de realimentação capturaria os
  desfechos realizados para recalibrar pesos e curvas, momento em que as dimensões hoje inertes,
  diligência e atividade, se tornariam calibráveis;
- Uma dimensão de fit de conta ou perfil de cliente ideal, padrão na prática de fit e
  engajamento, é omitida por ser inerte nesta base, pois a EDA mostrou que porte, setor e
  geografia não distinguem a conversão; é uma dimensão válida em produção;
- Quando ancorada no preço de tabela, a dimensão econômica contribui pouco para a ordenação fina,
  pois tem apenas sete níveis, um por produto. O ancoramento no ticket médio por par, ora
  implementado (ADR R4T9), introduz muitos mais níveis e atenua essa limitação, embora a EDA
  advirta que o valor fechado acompanha de perto o preço de tabela;
- A estrutura primária do ranqueamento, regida pelo momentum, é robusta, mas a ordenação fina
  entre os pares maduros depende dos pesos arbitrados das dimensões de valor; a sensibilidade aos
  pesos está reportada na validação, e o instrumento deve ser lido como um apoio de priorização
  da região de topo, não como uma ordem total precisa;
- No fechamento interativo de um ciclo pelo agente, os desfechos Won e Lost produzem o mesmo
  decaimento de momentum: ambos registram um fechamento recente que reduz a maturidade de
  recompra ao mínimo pela corcova, e a distinção entre eles reside no histórico e no registro
  econômico, não na curva de decaimento. Um decaimento assimétrico entre Won e Lost, por exemplo
  um resfriamento distinto após uma recusa, é um refinamento diferido por escolha de MVP;
- A devolução de uma oportunidade sem desfecho a reconduz à sua linha de base de ranqueamento,
  por não constituir uma transação, de modo que não decai pela recência. O envelhecimento
  acumulado enquanto esteve engajada não é preservado na linha de base ao devolvê-la; preservá-lo
  exigiria que a linha de base considerasse a duração do engajamento, um refinamento diferido por
  escolha de MVP.
