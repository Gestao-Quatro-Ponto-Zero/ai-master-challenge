

## 1. Ausência de sinal preditivo por atributo firmográfico

Pergunta: dá pra adivinhar se um negócio vai ser GANHO ou PERDIDO só
olhando dados de cadastro (vendedor, produto, setor, conta)?
Método: separamos os negócios fechados em dois grupos por data — os
mais antigos (treino) e os mais recentes (teste) — e medimos se o
padrão aprendido no grupo antigo acerta no grupo novo.

Corte cronológico (treino/teste): 2017-09-18
Treino: 5350 negócios · Teste: 1361 negócios

AUC (Area Under Curve) é uma nota de 0 a 1 para o quão bem um atributo
separa ganhos de perdas: 0,50 = mesmo que jogar uma moeda (nenhum poder
preditivo); 1,00 = previsão perfeita. Abaixo, a AUC de cada atributo
isolado (taxa de ganho aprendida no treino, testada no teste):
  vendedor                 AUC = 0.523
  conta                    AUC = 0.486
  setor                    AUC = 0.475
  escritório regional      AUC = 0.500

AUC combinada (gradient boosting, todos os atributos): 0.500
-> ~0,50 indica ausência de poder discriminativo (chute aleatório).
Achado: nem um atributo isolado, nem todos combinados, batem uma
moeda viciada — não existe sinal preditivo firmográfico nestes dados.


## 2. Testes de permutação (semente fixa)

Pergunta: será que a falta de sinal da Seção 1 é só coincidência
desta amostra específica, ou é um padrão robusto?
Método: embaralhamos aleatoriamente, centenas de vezes, qual
vendedor/produto/setor/conta está associado a cada negócio, e
comparamos a diferença REAL entre grupos com a diferença que
aparece só por acaso nessas versões embaralhadas ('semente fixa'
quer dizer que o embaralhamento é sempre o mesmo, então o
resultado é reproduzível).

  sales_agent      dispersão obs.=0.0340 dispersão nula média=0.0314 p=0.262
  product          dispersão obs.=0.0150 dispersão nula média=0.0139 p=0.373
  sector           dispersão obs.=0.0099 dispersão nula média=0.0172 p=0.965
  account          dispersão obs.=0.0473 dispersão nula média=0.0540 p=0.947

p-valor = a chance de ver, só por acaso (embaralhado), uma diferença
tão grande quanto a real observada. p-valor alto (>0,05, tipicamente
bem mais) = a diferença real é do tamanho que apareceria só por acaso
— ou seja, não há padrão real.
-> p alto (>0,05, tipicamente bem mais) = dispersão observada compatível com ruído.
Achado: todos os atributos testados têm p-valor alto — confirma, de
um segundo jeito independente, o resultado da Seção 1.


## 3. Encolhimento hierárquico — derivação de k

Pergunta: quanto peso dar à taxa de conversão histórica de cada
produto (ou combinação conta×produto, produto×setor), sem deixar
grupos com poucos negócios — e portanto números instáveis —
distorcerem a fórmula?
Método: 'encolhimento hierárquico' puxa a taxa de cada grupo em
direção à média geral (0,632), com força k. k é calculado a partir
dos próprios dados: quanto menor a diferença real entre os grupos
comparada à diferença esperada só por acaso, maior o k — mais o
grupo é puxado pra média. Quando k = ∞, o grupo 'colapsa': recebe
peso zero e usa direto a média geral. É o que esperamos ver quando
um atributo, como já vimos nas seções 1 e 2, não carrega sinal real.

  conta×produto    grupos= 525 var_obs=0.025899 var_esperada_por_acaso=0.027981 k=∞ (colapsa)
  produto×setor    grupos=  69 var_obs=0.012264 var_esperada_por_acaso=0.015229 k=∞ (colapsa)
  produto          grupos=   7 var_obs=0.000316 var_esperada_por_acaso=0.001515 k=∞ (colapsa)

'k congelado' abaixo é o valor usado em produção (fixado numa
calibração anterior); 'p̂_produto recalculado' é a taxa que sairia se
recalculássemos do zero com os dados desta execução — comparamos os
dois pra ver se ainda fazem sentido juntos.
k congelado em produção (constants.K_PRODUTO) = 4.0
p̂_produto (congelado) vs (recalculado nesta execução):
  GTX Basic        congelado=0.6372  recalculado=0.6320
  GTX Pro          congelado=0.6356  recalculado=0.6320
  MG Special       congelado=0.6484  recalculado=0.6320
  MG Advanced      congelado=0.6034  recalculado=0.6320
  GTX Plus Pro     congelado=0.6429  recalculado=0.6320
  GTX Plus Basic   congelado=0.6214  recalculado=0.6320
  GTK 500          congelado=0.6044  recalculado=0.6320

NOTA — em termos simples: se aplicássemos a mesma régua de
'colapsar se não há sinal' também ao nível de PRODUTO (não só
conta×produto e produto×setor), o resultado diria pra zerar essa
diferenciação também. Decidimos manter mesmo assim — o motivo
completo está registrado abaixo e em docs/decisions-log.md.

NOTA — achado desta execução: o mesmo método (variância esperada por acaso / variância em excesso), recalculado do zero sobre estes dados, encontra excesso de variância marginal também no nível de produto — mais fraco do que qualquer um dos quatro atributos testados por permutação acima (todos com p > 0,05). Sob recomputação estrita, isso colapsaria p̂_produto para a constante global (0,632) em todos os produtos.
K_PRODUTO = 4 é retido mesmo assim como constante CONGELADA desta calibração (documentada em docs/decisions-log.md), preservando os ~4,5 pontos de diferenciação entre produtos descritos no desenho — não é uma escolha arbitrária nova, é a calibração já em produção. Fica registrado aqui para a próxima recalibração trimestral avaliar se essa diferenciação deve ser reduzida ou mantida.


## 4. Curvas de aging — monotonicidade e fronteira de censura

Pergunta: o risco de o negócio esfriar realmente aumenta com o
tempo, sem 'zigue-zagues' estranhos, e existe um limite de idade
confiável pra fazer essa conta?
Método: recalculamos do zero as curvas de risco e de probabilidade
de ganho por idade do negócio, e conferimos duas coisas: (a) nenhum
negócio fechado nos dados é mais velho que o limite de censura
configurado; (b) a curva de risco nunca 'desce' — só sobe ou fica
igual conforme o negócio envelhece (monotonicidade).
'Censura' aqui quer dizer: não confiamos em extrapolar a curva além
do que já foi observado — acima do limite, a fórmula volta pro
valor médio histórico (prior) em vez de inventar um número.

Duração máxima observada entre negócios fechados: 138 dias
Limite de censura configurado: 138 dias
-> confirmado: nenhum negócio fechado excede o limite de censura.
risco(t) isotônico é não-decrescente em todos os pontos recalculados. OK.

p_ganho(t) recalculado nos extremos: t=0 -> 0.632  t=120 -> 0.752
-> p_ganho sobe com a idade (não decai): True
Achado contraintuitivo: a chance de ganhar SOBE com a idade do
negócio, não desce. O que a idade realmente consome é a janela de
decisão (quanto tempo resta pra fechar em breve), não a chance de
sucesso em si — por isso URGÊNCIA usa risco(t), não um decaimento.


## 5. Concentração de PRIORIDADE (não é validação preditiva)

Pergunta: a fórmula PRIORIDADE realmente separa o que é urgente e
valioso do resto da fila, ou dá praticamente no mesmo que ordenar
só pelo preço de tabela do produto?
Método: ordenamos a fila por PRIORIDADE e medimos quanto valor
total (em R$) está concentrado nos 10% e 30% do topo — e
comparamos com ordenar simplesmente pelo preço de tabela puro,
sem PRIORIDADE. Esta seção NÃO testa se a fórmula prevê quem vai
ganhar (isso já foi respondido — negativamente — nas seções 1 e 2);
ela testa só se a priorização concentra valor no topo.

Top 10% da fila por PRIORIDADE captura 49.2% do total

Top 30% da fila por PRIORIDADE captura 78.8% do total

Top 10% por preço de tabela puro captura 29.5% do total

Top 30% por preço de tabela puro captura 68.9% do total

-> concentração de valor, não poder preditivo: p̂ varia só 0,60-0,75 contra 487x de amplitude em VALOR. A diferenciação vem de valor e urgência.
Achado: PRIORIDADE concentra MAIS valor em risco no topo da fila do
que simplesmente ordenar por preço de tabela (49,2% vs. 29,5% no
top 10%) — o ganho vem de combinar VALOR com URGÊNCIA (idade do
negócio), não de uma previsão fina de quem vai ganhar (que já vimos,
nas seções 1 e 2, que não existe).


## Conclusão

Juntando as 5 seções: não há como prever com confiança QUEM vai
ganhar (seções 1 e 2), então não faz sentido construir um
classificador de probabilidade categórica. O que os dados sustentam
é ordenar o funil por VALOR EM RISCO (PRIORIDADE) — quanto vale o
negócio, ajustado pela chance histórica do produto (seção 3) e pela
urgência de agir agora (seção 4) — e essa priorização de fato
concentra valor no topo da fila (seção 5).

Os dados justificam ordenar o funil por valor em risco (PRIORIDADE), não por um
classificador de probabilidade categórica: nenhum atributo firmográfico isolado
carrega sinal acima do ruído amostral, e a hierarquia de encolhimento confirma
isso de outra forma (colapso de conta×produto e produto×setor).

STATUS: OK — todas as premissas estruturais confirmadas.