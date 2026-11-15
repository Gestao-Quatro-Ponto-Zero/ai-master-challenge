# Crítica das telas do estudo de UX (3 revisores)

> Três revisores independentes criticaram as primeiras telas do estudo, cada um por uma lente, antes de qualquer código. Saída bruta de agentes de IA, sem edição além da remoção de caminhos locais.


## criticas


### 1. vendedor

- **lente:** vendedor
- **nivel:** Bom
- **resumo:** Pela lente do vendedor na segunda de manhã, o estudo é forte. Em 10 segundos dá para entender que a lista ordenada pelo score é o centro da tela 02. O bloco "Por que 98" explica bem: traz número, origem e o que não entra. A identidade segue o G4 OS: trilho de ícones à esquerda, sidebar com item ativo marcado em dourado, navy #0B1D2E, Manrope e "Bom dia, Nome". Faltam três coisas. (1) O vendedor não sabe qual negócio é qual: das 10 linhas quentes, 5 são "GTX Pro/GTX Plus Pro · Sem cliente no cadastro", com valores iguais e sem nenhum identificador. A mensagem pronta do gestor herda o mesmo problema ("GTX Plus Pro de 73 dias"). (2) Não existe ação na linha: a tela diz o que fazer ("Confirme com o cliente ou encerre"), mas não oferece um botão para isso. (3) Dois números de conversão se contradizem: o subtítulo fala em "8 em cada 10" e o insight e a chance falam em "metade" e 50%. Há ainda um risco de credibilidade: o +42% aparece no login e na Máquina do tempo como fato, sem a ressalva de que ainda não foi conferido. O resto é ajuste de jargão ("na janela", "pipeline vivo"), de tom em um insight e de densidade (4 números por linha e 4 KPIs que disputam atenção com a lista). O acesso simulado passa no teste dos 5 segundos: Daniell já vem selecionado e o CTA diz "Entrar como Daniell Hammack".

#### criticos


##### 1. item 1

- **tela:** 02 · Vendedor · Foco da semana
- **onde:** Coluna DEAL da lista Quentes (linhas 98, 97, 96, 94, 91)
- **problema:** Cinco das dez linhas mostram só o produto e 'Sem cliente no cadastro'. Valores, chances e esperados são quase idênticos: o 98 e o 97 são ambos 'GTX Plus Pro · US$ 5.482', e quatro deals têm score 94 com US$ 4.821 e 50%. Na tela, a única coisa que diferencia os negócios é a idade em dias.
- **impacto:** O vendedor entende que deve começar pelo 98, mas não consegue achar esse negócio no CRM nem lembrar com quem falar. A lista diz por onde começar sem dizer qual é o negócio. É a falha central da tela.
- **solucao:** Coloque na segunda linha da célula um identificador que existe em todos os deals: código curto do deal e data de abertura. Exemplo: 'GTX Plus Pro' em cima e '#1C1I7A6R · aberto em 22 set' embaixo. Quando houver cliente, use 'Initech · aberto em 18 set'. Torne a linha inteira clicável, abrindo o detalhe do deal com o mesmo identificador.

##### 2. item 2

- **tela:** 02 · Vendedor · Foco da semana / 03 · Gestor (mensagem pronta)
- **onde:** Linhas da lista e card 'Pipeline' da Gabi; caixa 'Para quem não abre o sistema'
- **problema:** Não há ação por deal. O insight manda 'Confirme com o cliente ou encerre', a mensagem do gestor pede 'me diga até sexta quais confirmou', mas a linha não oferece nenhum controle para isso. A mensagem pronta também identifica os deals como 'GTX Plus Pro de 73 dias, GTX Plus Pro de 102 dias', o que não basta para o vendedor achá-los.
- **impacto:** O ciclo segunda de manhã termina em leitura, não em ação. O vendedor que não abre o sistema recebe uma mensagem que não consegue executar.
- **solucao:** Coloque à direita de cada linha, no hover e no deal expandido, dois botões de texto: 'Falei com o cliente' e 'Encerrar'. Na aba Sem desfecho, troque por 'Confirmar que segue' e 'Encerrar como perdido'. Na mensagem pronta, use o mesmo identificador da lista. Exemplo: 'GTX Plus Pro #1C1I7A6R (aberto em 22 set)'.

##### 3. item 3

- **tela:** 02 · Vendedor · Foco da semana
- **onde:** Subtítulo do cabeçalho vs. card 'Momento' da Gabi vs. coluna CHANCE
- **problema:** O subtítulo diz 'Aqui, 8 em cada 10 fechamentos deste mês viram venda'. O card Momento diz 'metade virou venda em 30 dias', e a coluna Chance mostra 49–51%. São bases diferentes (ganhos sobre fechados vs. conversão em 30 dias), mas a tela não explica isso.
- **impacto:** O primeiro número que o vendedor lê (80%) contradiz o número da lista (50%). Ele passa a desconfiar do score logo na primeira frase, o que pesa ainda mais numa avaliação.
- **solucao:** Troque o subtítulo por 'É o último mês do trimestre: deals na faixa certa de idade fecham metade das vezes em 30 dias.' Se quiser manter o 80%, deixe explícita a base: 'Dos deals que fecham em dezembro, 8 em 10 são ganhos.' E nunca coloque esse número ao lado da chance.

##### 4. item 4

- **tela:** 01 · Acesso simulado e 04 · Máquina do tempo
- **onde:** Rodapé do painel escuro do login ('+42% de receita contra ordenar por valor') e bloco de resultado da Máquina do tempo ('+42%' em 64 px)
- **problema:** O +42% é o número mais visível do estudo e aparece como fato. Ele vem de um protótipo ainda sem conferência independente, e nenhuma das duas telas diz isso.
- **impacto:** Se o avaliador recalcular e achar outro número, todos os números reais do produto perdem crédito.
- **solucao:** Coloque um selo 'Preliminar' (texto 12 px, fundo --color-gold-soft) ao lado do número nas duas telas. Na Máquina do tempo, adicione a linha 'Resultado do protótipo, ainda sem conferência independente. Ver o método →'. No login, troque o +42% por um número já conferido, como '1.291 de 1.589 passaram de 138 dias', ou leve o selo junto.

#### importantes


##### 1. item 1

- **tela:** 02 · Vendedor · Foco da semana
- **onde:** Coluna IDADE NA NEGOCIAÇÃO: rótulos 'na janela' / 'entrando na janela' e legenda no rodapé da tabela
- **problema:** 'Janela' é jargão do motor. A régua só se explica pela legenda no fim da tabela, 750 px abaixo do topo. Nas Quentes, 9 de 10 linhas repetem 'na janela', então o rótulo não diferencia nada.
- **impacto:** Quem lê sem manual vê um ponto sobre uma barra bege e não sabe o que ele mede. A repetição vira ruído.
- **solucao:** Troque o cabeçalho para 'IDADE · FAIXA QUE FECHA'. Na linha, mostre rótulo só nas exceções: 'ainda cedo' (antes da faixa), 'no ponto' (dentro dela, opcional) e 'passando do ponto' (depois de 105 dias). Leve a legenda para um tooltip no cabeçalho: 'Faixa bege: idade em que os deals desta empresa mais fecham neste ponto do trimestre (61–105 dias).'

##### 2. item 2

- **tela:** 02 · Vendedor · Foco da semana
- **onde:** Card 'INDICADOR · Sua taxa de ganho real é 46,8%.'
- **problema:** Para o próprio vendedor, 'real' contra 'oficial 59,5%' insinua que o número dele está inflado. É o único insight que soa como bronca, e ele não pede uma ação concreta.
- **impacto:** Gera defesa em vez de ação e contraria a regra de nunca acusar o vendedor.
- **solucao:** Na tela do vendedor, reescreva o card como 'Encerrar os sem desfecho deixa sua taxa mais fiel.', com o corpo 'Hoje o CRM mostra 59,5%. Contando os 47 deals parados há mais de 138 dias, ela fica em 46,8%.' e o CTA 'Revisar os 47 →'. Deixe o comparativo 'real vs. oficial' só na tela do gestor.

##### 3. item 3

- **tela:** 02 · Vendedor · Foco da semana
- **onde:** Faixa de KPIs (Pipeline vivo US$ 106.459 em 44 px + Declarado + Sem desfecho + Esperado em dourado) e barra de 42%
- **problema:** Quatro números e uma barra ocupam a primeira dobra antes da lista. O maior número da tela é o pipeline vivo, que não diz ao vendedor o que fazer. O 'Esperado em 30 dias', em dourado, disputa o acento com o score. 'Pipeline vivo' também é jargão.
- **impacto:** No teste dos 10 segundos o olho vai para 'US$ 106.459' em vez de ir para o deal 98. A lista é o que gera ação e fica em segundo plano.
- **solucao:** Na tela do vendedor, reduza a faixa a uma linha de 16 px: 'US$ 106.459 ainda podem fechar · US$ 42.162 esperados em 30 dias · 47 deals sem desfecho →'. Mantenha a barra com 6 px. Deixe o bloco grande de 4 KPIs só na tela 03 (gestor), onde as duas leituras são o assunto. Troque 'Pipeline vivo' por 'Ainda pode fechar'.

##### 4. item 4

- **tela:** 02 · Vendedor · Foco da semana
- **onde:** Abas 'Quentes 16 · Mornos 17 · Frios 5 · Sem desfecho 47'
- **problema:** Os critérios de Quente, Morno e Frio não aparecem em nenhum lugar. A aba com o maior número (47) é a do problema, e não a das oportunidades.
- **impacto:** O vendedor não sabe por que um deal com score 86 e chance de 35% está nas Quentes. O '47' ao lado chama mais atenção que o '16'.
- **solucao:** Coloque o critério como tooltip ou sublinha de cada aba: 'Quentes · score 80+', 'Mornos · 40–79', 'Frios · abaixo de 40', 'Sem desfecho · mais de 138 dias'. Separe 'Sem desfecho' das outras três com um divisor vertical de 1 px e cor --color-text-muted, deixando claro que é outra coisa e não um quarto nível de temperatura.

##### 5. item 5

- **tela:** 02 · Vendedor · Foco da semana
- **onde:** Linhas com score empatado (quatro '94', dois '96')
- **problema:** Deals com o mesmo score, valor, chance e esperado aparecem em ordem sem critério visível (71, 74, 75 e 73 dias).
- **impacto:** O vendedor não sabe qual dos quatro '94' atacar primeiro, e a ordem parece arbitrária.
- **solucao:** Defina o desempate como 'mais perto do fim da faixa primeiro' (o que tem menos tempo útil) e escreva isso no rodapé, ao lado de 'Ordenado por score': 'Ordenado por score; empate: o que sai da faixa antes'.

#### melhorias


##### 1. item 1

- **tela:** 02 · Vendedor · Foco da semana
- **onde:** Colunas VALOR, CHANCE, ESPERADO + SCORE
- **problema:** São quatro números por linha, e dois deles são derivados: o esperado é chance × valor, e o score é a posição do esperado. A conta já aparece no 'Por que 98'.
- **impacto:** A tabela fica densa e a leitura em diagonal desacelera.
- **solucao:** Tire a coluna ESPERADO da linha (a conta continua no bloco expandido) e coloque o valor embaixo do nome do deal: 'GTX Plus Pro · US$ 5.482'. Ficam Score, Deal, Idade e Chance, e sobra espaço para o identificador e os botões de ação.

##### 2. item 2

- **tela:** 02 · Vendedor · Foco da semana
- **onde:** Texto 'Sem cliente no cadastro' repetido nas linhas
- **problema:** A mesma frase de 13 px em 5 das 10 linhas faz parecer que o produto está quebrado, e ocupa o lugar do identificador.
- **impacto:** É ruído visual e deixa a impressão de que a ferramenta tem dados ruins.
- **solucao:** Mostre um traço '—' em --color-text-muted no lugar do cliente e uma única nota no rodapé: 'Cliente vazio em 68% dos deals abertos. Não entra na conta. Ver qualidade dos dados →'. No detalhe do deal, ofereça 'Adicionar cliente'.

##### 3. item 3

- **tela:** 02 · Vendedor · Foco da semana
- **onde:** Bloco expandido 'Por que 98'
- **problema:** Explica o número muito bem, mas não termina com o próximo passo. 'Só 2% dos deals vivos da empresa valem mais' também é linguagem de estatístico.
- **impacto:** O vendedor entende o porquê, mas não recebe o 'e agora'.
- **solucao:** Adicione uma quarta coluna, ou uma linha final, 'O QUE FAZER': 'Está no meio da faixa. Proponha o fechamento até 15 dez.' Reescreva a última frase como 'Entre os seus e os do time, só 2 em cada 100 deals valem mais que este.'

##### 4. item 4

- **tela:** 02 · Vendedor · Foco da semana
- **onde:** Seletor '4 dez 2017' e 'Você escolhe o dia. A base vai até 31 dez 2017.' no canto superior direito
- **problema:** É um controle de demo dentro da tela de trabalho e duplica a função da Máquina do tempo.
- **impacto:** Disputa atenção com a saudação. Um vendedor real não escolheria o dia.
- **solucao:** Leve o seletor para um chip discreto na sidebar, acima do perfil: 'Data simulada: 4 dez 2017 ▾'. Assim a demo continua navegável e o cabeçalho fica só com a saudação.

##### 5. item 5

- **tela:** 01 · Acesso simulado
- **onde:** Lista 'Pessoa' (3 de 30 visíveis) e alternância Vendedor/Gestor
- **problema:** O avaliador entra rápido com o Daniell, que já vem selecionado, mas não sabe que outras pessoas mostram outros cenários. A 'Darcel Schlecht · carteira em prospecção, sem datas' sugere uma tela vazia. Também não fica claro qual gestor aparece ao trocar a aba.
- **impacto:** Quem tem pressa testa um caminho só e não vê o contraste entre os perfis, que é o ponto do produto.
- **solucao:** Marque cada pessoa sugerida com uma etiqueta de cenário: 'Daniell · Recomendado: muitos sem desfecho', 'Reed · Carteira limpa', 'Darcel · Sem deals datados (estado vazio)'. Na aba Gestor, mostre já selecionado 'Rocco Neubert · Leste · 5 vendedores'. Adicione abaixo do CTA o link 'Ou entre como gestor (Rocco) →'.

##### 6. item 6

- **tela:** 04 · Máquina do tempo
- **onde:** Colunas 'Pelo score' / 'Por valor' e etiquetas 'Venda · US$ 5.627'
- **problema:** Os valores de venda (US$ 5.627, US$ 5.255) diferem do preço de tabela mostrado na tela 02 (US$ 4.821) sem explicação. 'Por valor' não diz que se trata de ordenar pelo preço declarado.
- **impacto:** Quem compara as telas acha que os números não batem.
- **solucao:** Coloque uma nota sob o título: 'Valores de venda são os fechados no CRM; o score usa o preço de tabela.' Renomeie a coluna da direita para 'Pelo maior valor declarado'.

#### acertos

- O bloco 'Por que 98' em três colunas (Por que / De onde vem a chance / O que não entra) mostra o número e a base ('391 deals já estiveram assim') e diz o que foi testado e descartado. É o melhor trecho do estudo.
- O tom do 'sem desfecho' é neutro em todas as telas ('58% passou do prazo sem ganho nem perda'). Nada acusa o vendedor.
- No login, o perfil e a pessoa já vêm pré-selecionados e o CTA nomeia a escolha ('Entrar como Daniell Hammack →'): dá para entrar com um clique.
- O painel escuro do login vende o problema em uma frase de alto contraste ('US$ 3,9 milhões em negociação. US$ 0,7 milhão ainda vivo.'), com a barra cheia contra a tracejada.
- A barra cheia contra a tracejada é a mesma linguagem visual no login, na faixa de KPIs e na tabela do gestor, e se explica sozinha.
- Os insights da Gabi têm rótulo de tipo (MOMENTO, PIPELINE, INDICADOR), número explícito e CTA com contagem ('Ver os 18 deals →'). A linha 'Calculados por regra, com a conta à mostra' cumpre a regra de não ser IA em tempo real.
- A identidade está fiel ao G4 OS sem copiar a marca: trilho de ícones, sidebar com item ativo marcado em dourado, navy #0B1D2E, Manrope, 'Bom dia, Nome' e o selo 'Conceito' fixo.
- A Máquina do tempo põe as duas listas lado a lado, com o desfecho real e o botão 'Esconder o desfecho'. É uma prova honesta e fácil de entender.
- As cores de texto passam em contraste: --color-text-muted #5A6673 e --color-gold-strong #8A6327 sobre branco ficam acima de 4,5:1.

### 2. cetico

- **lente:** cetico
- **nivel:** Bom
- **resumo:** Visto com olhar de gestor e de avaliador cético, o estudo é sólido. As contas fecham entre as telas: no Daniell, 106.459 + 146.909 = 253.368 e 38 + 47 = 85 deals. No time, 438.104 + 386.736 = 824.840, 169 + 138 = 307 deals, a soma dos cinco vendedores bate com os totais e os 47 sem desfecho do Daniell aparecem iguais no login, na tela dele e na do gestor. Os insights mostram o número e oferecem "Ver a conta". A credibilidade, porém, cai em quatro pontos. (1) O +42% aparece como fato no login e na máquina do tempo, sem avisar que vem de um protótipo ainda sem conferência independente. (2) A base de comparação "por valor" é frágil: 8 dos 10 deals dessa lista têm mais de 138 dias, ou seja, são deals que o próprio produto já declara sem desfecho. (3) Frases que afirmam mais do que o dado sustenta: "8 em cada 10 fechamentos viram venda" convive com chances de cerca de 50%, e "taxa de ganho real" supõe que todo deal sem desfecho é perda. (4) Há três âncoras de tempo que não batem: o painel do login usa 31 dez, as telas usam 4 dez, e a máquina do tempo mede o desfecho em 27 dias enquanto a chance promete 30. Também há inconsistências menores: a mensagem pronta diz "com mais chance" mas segue o score, "qualquer segunda-feira de 2017" quando a linha do tempo só vai de jul a dez, 659 listas onde 22 × 30 dariam 660, e o insight do Donn tem tom de ranking.

#### criticos


##### 1. item 1

- **tela:** 01 · Acesso simulado e 04 · Máquina do tempo
- **onde:** Login: rodapé do painel escuro ('+42% de receita contra ordenar por valor'). Máquina do tempo: bloco 'No conjunto: +42%'.
- **problema:** O +42%, as 22 segundas-feiras e as 659 listas vêm de um protótipo ainda sem conferência independente, mas aparecem como resultado definitivo. É o maior número do estudo e o primeiro que o avaliador vê no login.
- **impacto:** Se a conferência der outro valor, cai a credibilidade de todo o resto, inclusive dos números que estão certos. O avaliador cético vai perguntar 'quem conferiu isso?' e a tela não responde.
- **solucao:** No login, trocar por '+42% de receita na amostra do protótipo · conferência pendente' ou tirar o número do login e deixar só '22 segundas-feiras testadas no passado'. Na máquina do tempo, pôr um selo âmbar ao lado do número: 'Resultado preliminar · aguardando conferência independente', com o link 'Ver como foi calculado'.

##### 2. item 2

- **tela:** 04 · Máquina do tempo
- **onde:** Coluna 'Por valor' (0 vendas · US$ 0)
- **problema:** A base de comparação está viciada. Oito dos 10 deals 'por valor' têm de 169 a 334 dias, ou seja, já passaram dos 138 dias que o próprio produto chama de sem desfecho. Como quase todos são GTX Plus Pro de US$ 5.482, o critério de desempate escolheu os mais velhos. O 9º e o 10º (102 e 73 dias) são os mesmos #2 e #1 do score.
- **impacto:** O avaliador vai concluir que o score ganha de um adversário fraco: 'por valor' perde porque inclui deals mortos, não porque valor seja um critério ruim. Isso também contamina o +42%.
- **solucao:** Trocar a base por 'Por valor, só entre os deals com até 138 dias'. Se o +42% foi calculado contra a lista atual, mostrar as duas versões ('contra valor bruto' e 'contra valor sem os sem desfecho'). Escrever o desempate abaixo do título da coluna: 'Empates de valor: mais antigo primeiro'. Se mudar o critério, recalcular o exemplo do Daniell.

##### 3. item 3

- **tela:** 02 · Vendedor · Foco da semana
- **onde:** Subtítulo do cabeçalho: 'Aqui, 8 em cada 10 fechamentos deste mês viram venda.'
- **problema:** A frase dá a entender uma taxa de conversão de 80%, mas logo abaixo os deals quentes mostram chance de 35% a 51%, e o card ao lado diz que a taxa de ganho é 46,8%. Ela só é verdadeira como 'dos deals que tiveram desfecho em dezembro, 80% foram ganhos', mas ninguém vai ler assim.
- **impacto:** Parece o número otimista escolhido a dedo para abrir a tela. É a primeira frase que o vendedor lê, e o avaliador encontra a contradição com a coluna Chance em segundos.
- **solucao:** Trocar por: 'É o último mês do trimestre. Em dezembros e setembros anteriores, dos deals que tiveram desfecho no mês, 8 em cada 10 foram ganhos.' Ou, mais simples e coerente com a tabela: 'É o último mês do trimestre: é quando mais deals desta base fecham.'

##### 4. item 4

- **tela:** 01 · Acesso simulado, 02 e 04
- **onde:** Login: texto do painel ('Em 31 de dezembro de 2017, o último dia da base, 1.291 dos 1.589...'). Máquina do tempo: subtítulo ('Desfecho real até 31 de dezembro').
- **problema:** Três âncoras de tempo diferentes. O login mede em 31 dez, as telas internas em 4 dez, e a máquina do tempo revela o desfecho de 4 dez até 31 dez, ou seja, 27 dias, enquanto a chance e o 'Esperado em 30 dias' são definidos para 30 dias. Além disso, 4 dez não está entre as 22 segundas-feiras do agregado, cujo gráfico termina em novembro.
- **impacto:** O avaliador pergunta 'em que data valem esses números?' e encontra três respostas. O exemplo do Daniell mede uma janela mais curta que a prometida, e isso não está dito.
- **solucao:** Ancorar o painel do login em 4 dez 2017, a mesma data das telas, ou rotular explicitamente 'No último dia da base (31 dez 2017)'. Na máquina do tempo, escrever: 'Desfecho em 27 dias (a base termina em 31 dez). Este exemplo não entra no resultado geral, que só usa segundas com 30 dias completos (jul a nov).'

##### 5. item 5

- **tela:** 02 · Vendedor e 03 · Gestor
- **onde:** Card 'Indicador · Sua taxa de ganho real é 46,8%' e coluna 'Taxa de ganho real' do gestor
- **problema:** Chamar de 'real' uma taxa que conta todo deal sem desfecho como perda afirma mais do que o dado sustenta. A regra correta é 'nenhum deal fechou depois de 138 dias', o que não é o mesmo que 'foram perdidos'. Quando a taxa 'real' aparece grande e a 'oficial' pequena embaixo, a oficial parece falsa.
- **impacto:** Fere a regra de não acusar o vendedor: sugere que o número dele está maquiado. O avaliador vê um rótulo mais forte do que a conta permite.
- **solucao:** Trocar o rótulo por 'Taxa de ganho com os sem desfecho' e o card por: 'Se os 47 deals sem desfecho entrarem como não ganhos, sua taxa vai de 59,5% para 46,8%.' Na tabela do gestor, mostrar as duas no mesmo peso visual, lado a lado: '59,5% → 46,8%'.

##### 6. item 6

- **tela:** 03 · Gestor · Meu time
- **onde:** Mensagem pronta 'Para quem não abre o sistema'
- **problema:** A mensagem diz 'Seus 3 deals com mais chance', mas lista o GTX Plus Pro de 102 dias (49%) e deixa de fora o GTX Pro de 82 dias (51%), que é o #3 do score. A Initech (51%) entra no lugar dele. Ou seja, a seleção não segue nem a chance nem a ordem do score.
- **impacto:** A mensagem é a única leitura que o vendedor que não abre o sistema recebe. Se ela contradiz a lista do próprio vendedor, a coerência do produto quebra no ponto em que deveria ser mais simples.
- **solucao:** Usar os três primeiros do score e o termo certo: 'Seus 3 deals de maior prioridade esta semana: GTX Plus Pro de 73 dias, GTX Plus Pro de 102 dias e GTX Pro de 82 dias.' Se o critério for priorizar deals com cliente cadastrado, dizer isso na tela, porque hoje não está explicado.

#### importantes


##### 1. item 1

- **tela:** 03 · Gestor · Meu time
- **onde:** Card 'Indicador · Na leitura real, o Donn sai de último para segundo'
- **problema:** O insight vira ranking: fala em posições (último → segundo) e, por contraste, aponta Cassey, Daniell e Boris como quem tinha a taxa inflada. É exatamente o 'ranking de culpa' que o produto quer evitar.
- **impacto:** O gestor leva para a reunião uma classificação de pessoas em vez de uma pauta de deals, e o tom de acusação volta pela porta dos fundos.
- **solucao:** Reescrever sobre a régua, não sobre posições: 'A taxa oficial muda conforme o deal parado. Com os sem desfecho na conta, Cassey, Daniell e Boris caem 11 a 14 pontos; Reed e Donn não mudam, porque não têm deal parado.' Título: 'A taxa oficial esconde 138 deals sem resposta.'

##### 2. item 2

- **tela:** 04 · Máquina do tempo
- **onde:** Bloco 'No conjunto' (+42%, 659 listas, '2,2 contra 1,3')
- **problema:** Faltam regras para o teste ser justo e verificável. 22 segundas × 30 vendedores dariam 660 listas, não 659. O +42% é de receita e o 2,2 contra 1,3 é de contagem (+69%), sem dizer em que horizonte. O gráfico não tem eixo nem valores. O subtítulo da página diz 'qualquer segunda-feira de 2017', mas a linha do tempo só vai de jul a dez.
- **impacto:** Cada uma dessas lacunas é uma pergunta do avaliador sem resposta na tela, e juntas fazem o número parecer frágil.
- **solucao:** Acrescentar uma linha de método: 'Segundas de 3 jul a 27 nov (22). 30 vendedores; 1 lista vazia descartada = 659. Venda contada se fechou em até 30 dias. Receita = valor fechado.' Pôr eixo Y com 'vendas' e rótulo no pico. Mudar o subtítulo para 'Volte a qualquer segunda-feira de julho a dezembro de 2017 (antes disso não há histórico suficiente).'

##### 3. item 3

- **tela:** 04 · Máquina do tempo
- **onde:** Selos 'Segue aberto' e 'Venda · US$ 5.627'
- **problema:** 'Segue aberto' não diz se o deal foi perdido, ficou sem desfecho ou apenas não fechou em 27 dias. O valor da venda (US$ 5.627 na Initech) é maior que o preço de tabela da tela 02 (US$ 4.821) sem nenhuma explicação.
- **impacto:** O cético pensa que o valor foi inflado ou que a coluna mistura bases. Sem uma legenda para 'Segue aberto', a coluna 'por valor' parece ainda mais um adversário montado para perder.
- **solucao:** Usar três estados com legenda: 'Venda (valor fechado)', 'Perda' e 'Sem desfecho até 31 dez'. Abaixo do título: 'Valor da venda é o fechado no CRM; pode diferir do preço de tabela usado no score.'

##### 4. item 4

- **tela:** 02 · Vendedor e 03 · Gestor
- **onde:** Abas 'Quentes 16', insight 'Momento · 18 dos seus deals vivos têm entre 61 e 105 dias' e '55 deals quentes no time'
- **problema:** 'Quente' não tem definição em nenhuma tela. O insight fala em 18 deals na faixa de 61 a 105 dias, mas a aba mostra 16 quentes, e a lista quente inclui deals de 57, 102 e 103 dias. O leitor não sabe se quente é por faixa de idade, por score ou por chance.
- **impacto:** Dois números próximos (16 e 18) para conceitos parecidos parecem erro de conta. O mesmo vale para os 55 do gestor.
- **solucao:** Definir uma única vez, numa legenda junto das abas: 'Quente: chance ≥ 35% nos próximos 30 dias.' Ajustar o insight para: '18 dos seus deals vivos estão na faixa de 61 a 105 dias; 16 deles estão em Quentes.'

##### 5. item 5

- **tela:** 03 · Gestor · Meu time
- **onde:** Card 'Decisão · 138 deals esperam uma resposta' e 'Sem desfecho · 138 deals há mais de 138 dias'
- **problema:** Coincidência infeliz: o número de deals do time sem desfecho é igual ao limite de dias. 'US$ 386.736 · 138 deals há mais de 138 dias' parece erro de digitação ou campo repetido.
- **impacto:** O avaliador para para conferir, e alguns vão reportar como bug. Isso desvia a atenção do principal da tela.
- **solucao:** Escrever por extenso, com unidades diferentes: '138 deals parados há mais de 138 dias (sim, os dois números coincidem)', ou usar no card 'Decisão' a forma '138 deals sem resposta, todos com mais de 4 meses e meio'.

##### 6. item 6

- **tela:** 02 · Vendedor e 03 · Gestor
- **onde:** Rótulos dos KPIs e colunas: 'Pipeline vivo' contra 'Pipeline real do time', 'Esperado' sem horizonte, 'Tudo com desfecho' contra 'nenhum deal sem desfecho' (login)
- **problema:** O mesmo conceito tem nomes diferentes em cada tela. A coluna 'Esperado' do gestor não diz que é em 30 dias. Os valores em US$ são a preço de tabela, e isso não aparece em lugar nenhum.
- **impacto:** Fica mais difícil cruzar números entre telas, que é exatamente o que o avaliador vai fazer.
- **solucao:** Padronizar 'Pipeline vivo' nas duas telas. Coluna 'Esperado em 30 dias'. Trocar 'Tudo com desfecho' por 'Nenhum deal sem desfecho'. Pôr uma nota fixa no rodapé do KPI: 'Valores a preço de tabela.'

#### melhorias


##### 1. item 1

- **tela:** 01 · Acesso simulado
- **onde:** Manchete do painel escuro 'US$ 3,9 milhões em negociação. US$ 0,7 milhão ainda vivo.'
- **problema:** A manchete não diz que é preço de tabela nem que 'vivo' significa até 138 dias. 'Nenhum deal fechou depois desse prazo' é um fato da base, mas pode ser lido como lei geral.
- **impacto:** É justo com a base, mas fica a um passo do exagero, logo na primeira tela.
- **solucao:** Acrescentar uma linha pequena abaixo da barra: 'Valores a preço de tabela. Vivo = em negociação há até 138 dias, o prazo depois do qual nenhum deal desta base fechou.'

##### 2. item 2

- **tela:** 02 · Vendedor · Foco da semana
- **onde:** Painel expandido 'Por que 98': 'Só 2% dos deals vivos da empresa valem mais.'
- **problema:** 'Valem mais' pode ser lido como preço maior, mas o score é por receita esperada.
- **impacto:** Confusão leve sobre o que o score mede.
- **solucao:** 'Só 2% dos deals vivos da empresa têm receita esperada maior.'

##### 3. item 3

- **tela:** 03 · Gestor · Meu time
- **onde:** Mensagem pronta: '...me diga até sexta quais confirmou com o cliente e quais vamos encerrar.'
- **problema:** Pedir decisão sobre 47 deals em quatro dias é irrealista e soa como cobrança.
- **impacto:** O vendedor que não abre o sistema recebe uma tarefa grande demais e tende a ignorá-la.
- **solucao:** 'Dos 47 deals abertos há mais de 138 dias, comece pelos 10 maiores: até sexta, me diga quais o cliente confirmou e quais podemos encerrar.'

##### 4. item 4

- **tela:** 02 · Vendedor · Foco da semana
- **onde:** Card 'Indicador': 'Cada um que você encerra aproxima os dois números.'
- **problema:** Dá a entender que encerrar como perda é o objetivo, quando o objetivo é decidir: confirmar com o cliente ou encerrar.
- **impacto:** Pode incentivar fechar deals como perdidos só para alinhar a métrica.
- **solucao:** 'Cada deal que você confirma com o cliente ou encerra deixa a taxa oficial mais perto da realidade.'

##### 5. item 5

- **tela:** 04 · Máquina do tempo
- **onde:** Cabeçalho da coluna 'Pelo score' (5 vendas · US$ 25.687)
- **problema:** O exemplo do Daniell (5 contra 0) é extremo e fica visualmente maior que o agregado. O aviso 'Um vendedor e uma data não provam nada' está em caixa-alta pequena no rodapé.
- **impacto:** O avaliador pode achar que o caso foi escolhido a dedo.
- **solucao:** Pôr no topo da seção, junto ao seletor de vendedor, o aviso 'Exemplo de um vendedor; o resultado geral está abaixo' e um link 'Ver o vendedor em que o score foi pior', para mostrar honestidade.

##### 6. item 6

- **tela:** 04 · Máquina do tempo
- **onde:** Selos 'Segue aberto' (cinza claro sobre cinza) e legenda do gráfico
- **problema:** Texto de cerca de 12 px em cinza médio sobre fundo cinza, com contraste baixo para a informação mais importante da coluna da direita.
- **impacto:** Acessibilidade: a coluna comparativa fica difícil de ler.
- **solucao:** Escurecer o texto do selo para o cinza de corpo da página (em torno de #4A5160) e subir a legenda do gráfico para 13 px.

#### acertos

- As contas fecham entre as telas. Daniell: 106.459 + 146.909 = 253.368 e 38 + 47 = 85. Time: soma dos 5 vendedores = 824.840 declarados, 438.104 vivos e 153.814 esperados; 169 + 138 = 307. Os 47 sem desfecho do Daniell são iguais no login, na tela do vendedor e na do gestor.
- Painel 'Por que 98' com três colunas (por que, de onde vem a chance, o que não entra): explica a conta inteira, sem caixa-preta.
- 'Sem cliente no cadastro' aparece explicitamente na linha, coerente com a regra de mostrar sem usar na conta.
- A barra vivo/declarado com tracejado para o que passou do prazo, reaproveitada nas telas 02 e 03 e na tabela do gestor, é uma metáfora visual clara e honesta.
- A frase 'Um vendedor e uma data não provam nada. No conjunto:' separa o exemplo do agregado; manter e reforçar.
- Insights com 'Ver a conta' / 'Ver os 47', e o subtítulo 'Calculados por regra, com a conta à mostra'.
- Selo 'Conceito', ausência do logo do G4 e o rodapé 'Não é um produto oficial do G4' no login.
- Seletor 'Você escolhe o dia. A base vai até 31 dez 2017' e a régua 'na janela' por deal tornam a temporalidade explícita.
- O vocabulário 'sem desfecho' é usado com consistência, sem acusar o vendedor (com a ressalva do rótulo 'taxa de ganho real').

### 3. visual

- **lente:** visual
- **nivel:** Bom
- **resumo:** Pela minha lente (consistência visual, fidelidade à referência e acessibilidade), o estudo parece um módulo do G4 OS. Ele repete a estrutura das capturas reais: trilho de 60 px com marcador dourado no item ativo, menu lateral de 248 px em cinza claro com grupos em caixa alta e item ativo com fundo cinza e barra dourada, painel branco com raio de 16 px, botão principal azul-marinho, selo no estilo "Beta" (aqui "Conceito") e a mesma família geométrica. Os tokens são bons e todo o texto passa de 4,5:1 (cinza secundário #5A6673 sobre branco dá 5,9:1, sobre o cromo dá 5,3:1 e sobre o chip dá 4,9:1; o dourado escuro #8A6327 dá 5,4:1 sobre branco e 4,7:1 sobre o creme). Os problemas reais são outros. (1) O símbolo do trilho, uma estrela dourada sobre um quadrado azul-marinho no mesmo lugar do símbolo do G4 OS, fica perto demais da marca oficial para uma peça que se declara conceito. (2) Os gráficos que carregam a tese ficam abaixo de 3:1: o tracejado do "sem desfecho" dá 2,2:1, a faixa dourada da janela de fechamento dá 1,4:1 e as barras "Por valor" dão 1,7:1. Essas três cores estão fora dos tokens. (3) O dourado, que o próprio token define como "um uso por tela", aparece em mais de 30 elementos na tela 02. (4) Os rótulos em caixa alta usam três combinações de tamanho e espaçamento, 11 px fora da escala de tokens. (5) Faltam os estados (hover, foco, linha expansível, vazio, carregando, erro), o comportamento abaixo de 1440 px e a tela do vendedor sem deals vivos, que o próprio login já anuncia (Darcel Schlecht).

#### criticos


##### 1. item 1

- **tela:** 02, 03 e 04 (trilho)
- **onde:** Topo do trilho, quadrado de 34 px com o símbolo
- **problema:** O símbolo é uma estrela de quatro pontas dourada sobre um quadrado azul-marinho, no mesmo lugar e com as mesmas cores do símbolo do G4 OS nas capturas de referência. O arquivo também se chama "G4 OS · Vendas". Somando o trilho com as áreas reais do G4 OS (Sessões, Ferramentas, Loja, Arquivos), a peça pode ser lida como produto oficial, o que a regra do produto proíbe.
- **impacto:** Credibilidade e risco de parecer que se passa pelo G4 no processo seletivo. O selo "Conceito" de 11 px não basta para desfazer essa leitura.
- **solucao:** Trocar o símbolo por uma marca própria do módulo: quadrado branco com borda de 1 px #E3E6EA e o ícone de tendência (o mesmo do item Vendas) em #0B1D2E, sem dourado. No trilho, deixar os ícones das outras áreas em #8B95A1 com cursor desabilitado e tooltip "Fora deste conceito". Renomear o arquivo para "Lead Scorer · conceito de módulo de vendas".

##### 2. item 2

- **tela:** 03 · Gestor · Meu time (e barra de resumo da 02)
- **onde:** Coluna "Vivo dentro do declarado", barra do topo (parte "passou do prazo") e legenda "Declarado, mas sem desfecho"
- **problema:** A parte da barra que representa o pipeline sem desfecho, que é a tese do produto, é só um contorno tracejado de 1,5 px em #A9B2BD sobre branco: 2,15:1. O critério para gráfico com significado é 3:1. Além disso, #A9B2BD não existe nos tokens.
- **impacto:** O gestor (às vezes em monitor ruim ou projetor de reunião) não enxerga a diferença entre declarado e vivo. A leitura "as duas leituras lado a lado" se perde.
- **solucao:** Contorno de 2 px em --color-cold (#7C8FA6, 3,3:1 sobre branco) com preenchimento listrado: repeating-linear-gradient(135deg, #7C8FA6 0 2px, transparent 2px 6px). Criar o token --color-undecided = #7C8FA6 e usá-lo também na legenda e na barra do topo da tela 02.

##### 3. item 3

- **tela:** 02 · Vendedor · Foco da semana
- **onde:** Régua "Idade na negociação" de cada linha e legenda "Faixa em que os deals fecham..."
- **problema:** A faixa da janela de fechamento usa #DCC49A (fora dos tokens) sobre a trilha #EAECEF: 1,43:1. A faixa é a única forma de ver se o deal está "na janela", e hoje quase não se distingue da trilha.
- **impacto:** O vendedor não entende o critério de urgência sem ler o texto "na janela", e o desenho vira enfeite.
- **solucao:** Faixa em #5A6673 com 4 px de altura (4,9:1 sobre a trilha) e ponto do deal com 8 px, preenchimento #FFFFFF e borda de 2 px #0B1D2E, para continuar visível em cima da faixa. Remover #DCC49A dos arquivos.

##### 4. item 4

- **tela:** 04 · Máquina do tempo
- **onde:** Gráfico "Vendas nos 10 primeiros de cada vendedor, por data" e pontos da linha do tempo
- **problema:** As barras "Por valor" e os pontos das semanas usam #B8C0CA sobre o cromo #F3F4F6: 1,67:1. O gráfico também não tem eixo Y nem valores, então o +42% não pode ser conferido visualmente. Os pontos das semanas têm cerca de 8 px de alvo clicável.
- **impacto:** A tela de prova não prova: não dá para ler a série de comparação nem a magnitude, e a navegação por semana fica difícil com mouse e impossível com toque.
- **solucao:** Barras "Por valor" em #6B7A8C (4,0:1 sobre #F3F4F6) e criar o token --color-compare. Adicionar três linhas de grade com rótulos de 12 px (0, 2, 4 vendas por lista) e tooltip por barra no formato "11 set · score 3,1 · valor 1,4". Cada semana vira um botão de 32 × 32 px com o ponto centralizado. Ao lado do +42%, no mesmo bloco, incluir em 12 px #5A6673 "Resultado do protótipo, ainda sem conferência independente." (vale também para o +42% do login).

#### importantes


##### 1. item 1

- **tela:** 02 (principalmente) e 04
- **onde:** Marcador vertical à esquerda de cada score, faixas das réguas, texto "na janela", rótulo "ESPERADO EM 30 DIAS", "POR QUE 98", ícone da Gabi, cartão Momento e legenda
- **problema:** O token --color-gold diz "Um uso por tela", mas na tela 02 o dourado aparece em mais de 30 elementos: 10 marcadores de linha, 10 faixas, 10 textos "na janela" e mais 6 pontos. Os 10 marcadores são todos iguais porque todas as linhas já estão na aba Quentes, então não distinguem nada. A referência usa dourado só no indicador do item ativo e no selo.
- **impacto:** O dourado perde a função de atenção. O cartão "É mês de fechar", que deveria ser o único destaque, compete com a lista inteira.
- **solucao:** Manter o dourado apenas em: indicador ativo do trilho e do menu (fidelidade à referência), selo Conceito e um único destaque por tela (o primeiro cartão da Gabi). Remover os marcadores de linha, ou trocá-los por um marcador #0B1D2E só no deal expandido. "na janela" passa para --color-text-muted com peso 600. "ESPERADO EM 30 DIAS" fica igual aos outros rótulos de KPI (#5A6673). Na tela 04, os meses SET e DEZ ficam em #0B1D2E com peso 700 em vez de dourado.

##### 2. item 2

- **tela:** Todas
- **onde:** Rótulos em caixa alta: cabeçalhos de tabela, grupos do menu (PROVA, TRANSPARÊNCIA), rótulos dos cartões (MOMENTO, INDICADOR), meses da linha do tempo, rótulos de KPI e kickers de página
- **problema:** Há três combinações para o mesmo papel: 11 px com 0,08em (49 nós, tamanho fora da escala, já que --text-xs = 12px), 12 px com 0,08em e 12 px com 0,1em no login. O token --tracking-caps = 0,06em não é usado em lugar nenhum. Também há rótulos longos em caixa alta, como "UM VENDEDOR E UMA DATA NÃO PROVAM NADA. NO CONJUNTO:" e "JUL · ABRE O TRIMESTRE", que ficam cansativos de ler.
- **impacto:** Inconsistência visível entre telas, texto abaixo de 12 px e frases inteiras em caixa alta de leitura lenta.
- **solucao:** Um único estilo "label": 12 px, peso 600, 0,06em, #5A6673, só para rótulos de até 3 palavras. Frases passam para caixa normal com 13 px e peso 500: "Um vendedor e uma data não provam nada. No conjunto:" e, nos meses, "Jul · abre o trimestre". O selo "Conceito" sobe para 12 px.

##### 3. item 3

- **tela:** 02 · Vendedor · Foco da semana
- **onde:** Linha do deal 98 expandida e demais linhas da lista
- **problema:** Só a primeira linha aparece aberta e nenhuma linha tem sinal de que pode ser expandida (sem chevron, sem fundo de linha selecionada). O painel "Por que 98" usa fundo #F3F4F6 com raio próprio, sem ligação visual com a linha. Não há estado de hover nem de foco.
- **impacto:** O vendedor não descobre a explicação do score, que é o "por quê" que o produto promete.
- **solucao:** Chevron de 16 px em #5A6673 no fim de cada linha (girado 180° na aberta). Linha aberta com fundo #F3F4F6 contínuo até o fim do painel, sem raio entre linha e painel e com raio de 12 px só embaixo. Hover em #F7F8F9. Foco por teclado com anel de 2 px #0B1D2E e 2 px de afastamento. Toda a linha é um botão com aria-expanded.

##### 4. item 4

- **tela:** 04 · Máquina do tempo
- **onde:** Seletor "Daniell Hammack" ao lado de "Esconder o desfecho", com o usuário logado como vendedor
- **problema:** O vendedor logado tem um seletor para ver a lista de outro vendedor, mas as telas 02 e 03 separam os papéis. Na mesma tela, a data é escolhida pela linha do tempo e pelos botões "Semana anterior / Próxima semana", enquanto nas telas 02 e 03 é escolhida pelo seletor "4 dez 2017": são três controles para o mesmo conceito.
- **impacto:** Quebra a coerência de permissão (a simulação perde verossimilhança) e de componentes.
- **solucao:** No perfil vendedor, trocar o seletor por um texto fixo "Sua lista" e mostrar o seletor de pessoa só no perfil gestor. Manter o seletor de data "4 dez 2017" no cabeçalho das três telas, no mesmo lugar, e na tela 04 tratar a linha do tempo como atalho visual desse mesmo seletor: remover os botões de semana e usar as setas do teclado na linha do tempo.

##### 5. item 5

- **tela:** Todas
- **onde:** Cores e espaçamentos fora do sistema
- **problema:** Há quatro cores sem token (#DCC49A, #B8C0CA, #A9B2BD e #A9B4C0 no painel escuro do login) e espaçamentos fora da escala, como o padding de 18 px nos cartões da Gabi (a escala vai de 16 para 20). A camada da barra do topo da tela 03 se chama "Sem desfecho 58%", mas o texto diz 47%.
- **impacto:** Na implementação, cada valor solto vira um valor mágico no CSS, e a consistência se perde na primeira iteração.
- **solucao:** Criar --color-undecided (#7C8FA6), --color-compare (#6B7A8C) e --color-on-ink-muted (#A9B4C0), ajustar o padding dos cartões para 16 px por 20 px (--spacing-4 e --spacing-5) e corrigir o nome da camada para "Sem desfecho 47%".

##### 6. item 6

- **tela:** 02 e 03 (menu lateral)
- **onde:** Ícones dos itens "Meu time" e "Deals para decidir" (gestor) comparados a "Foco da semana" e "Meu pipeline" (vendedor)
- **problema:** O mesmo ícone de alvo é usado em "Foco da semana" e "Meu time", e o mesmo ícone de linhas em "Meu pipeline" e "Deals para decidir". Funções diferentes têm a mesma marca.
- **impacto:** O usuário que troca de perfil na demonstração não percebe que mudou de contexto.
- **solucao:** "Meu time" com o ícone de pessoas (o mesmo do segmento "Gestor" no login) e "Deals para decidir" com o ícone de lista com check, mantendo o traço de 1,5 px dos demais.

#### melhorias


##### 1. item 1

- **tela:** Nova tela (variação da 02)
- **onde:** Área da lista e dos KPIs quando o vendedor não tem deals vivos
- **problema:** O login já oferece "Darcel Schlecht · carteira em prospecção, sem datas", mas não existe a tela que ele veria. O fluxo da demonstração quebra no terceiro clique possível.
- **impacto:** O avaliador escolhe Darcel e encontra uma lista vazia ou números zerados sem explicação.
- **solucao:** Desenhar o estado vazio no padrão da referência (bloco tracejado de raio 12 px, ícone em quadrado de 32 px, título e ação, como em "Nenhuma automação criada ainda"). Título: "Nenhum deal em negociação com data." Texto: "Seus 12 deals estão em prospecção e ainda não entram no score. Assim que um passar para negociação, ele aparece aqui." Ação secundária: "Ver deals em prospecção" (o número deve vir da base).

##### 2. item 2

- **tela:** 02, 03 e 04
- **onde:** Estados de carregamento e erro
- **problema:** Não há esqueleto de carregamento, nem erro ao calcular, nem resposta do botão "Copiar mensagem".
- **impacto:** Na aplicação real, o primeiro carregamento do cálculo vai mostrar tela branca, e o gestor não sabe se a mensagem foi copiada.
- **solucao:** Esqueleto com blocos #EAECEF animados (opacidade de 100% a 60%) com as mesmas alturas dos KPIs e de 6 linhas da lista. Erro inline no painel: "Não foi possível calcular a lista deste dia. Tentar de novo". "Copiar mensagem" vira "Copiada" com ícone de check por 2 s e aria-live="polite".

##### 3. item 3

- **tela:** 02, 03 e 04
- **onde:** Comportamento abaixo de 1440 px
- **problema:** As pranchas só existem em 1440. A tela 02 tem 6 colunas mais uma coluna de insights de cerca de 300 px, e a 04 tem duas listas lado a lado. Em 1280 (notebook comum), o espaço útil cai para cerca de 890 px.
- **impacto:** Colunas se espremem e o "US$" quebra linha justamente na tela de demonstração.
- **solucao:** Até 1280: os insights da Gabi passam para baixo da lista em linha de 3 cartões e o menu lateral recolhe para 60 px (só ícones, como o trilho). Até 1024: esconder a coluna Valor (fica no detalhe) e empilhar as duas listas da tela 04 com abas "Pelo score / Por valor". Desenhar ao menos uma prancha de 1280.

##### 4. item 4

- **tela:** 02 e 03
- **onde:** Cartões "Insights da Gabi" e "Pauta da Gabi"
- **problema:** A ordem e o destaque mudam de uma tela para outra: na 02 o creme fica com "Momento", na 03 com "Decisão", e "Momento" desce para o terceiro lugar. Sem regra visível, parece arbitrário. O link de ação também varia ("Ver os 18 deals", "Ver a conta", "Ver os 55").
- **impacto:** Fica mais difícil aprender o padrão do componente, que é o mais "G4 OS" do módulo.
- **solucao:** Regra explícita: o creme vai sempre para o insight com ação mais urgente, e os demais seguem a ordem fixa Decisão, Pipeline, Indicador, Momento. Os links seguem o formato "Ver os N deals" ou "Ver a conta": trocar "Ver os 55" por "Ver os 55 deals".

##### 5. item 5

- **tela:** Todas
- **onde:** Selo "Conceito" e cabeçalho do módulo
- **problema:** O selo da referência ("Beta") tem raio de cerca de 6 px. O do estudo é uma pílula de 999 px e 11 px de texto, a única pílula do sistema além dos chips de desfecho.
- **impacto:** Pequena falta de fidelidade e um aviso legal que passa despercebido.
- **solucao:** Selo com raio de 6 px (--radius-sm é 8, então criar --radius-xs = 6px), texto de 12 px e peso 600, e tooltip "Conceito para o AI Master Challenge. Não é um produto oficial do G4."

##### 6. item 6

- **tela:** 01 · Acesso simulado
- **onde:** Lista de pessoas e segmento Vendedor/Gestor
- **problema:** O login mostra só 3 de 30 vendedores sem indicar rolagem e não tem estado de foco no campo de busca nem nas linhas. Ao trocar para Gestor, não se sabe o que acontece com a lista.
- **impacto:** O avaliador pode achar que só existem 3 pessoas e não chegar ao gestor.
- **solucao:** Lista com altura de 4,5 linhas para insinuar a rolagem, ou o rodapé "Mostrando 3 de 30 · role para ver mais" em 12 px #5A6673. Foco com anel de 2 px #0B1D2E. Desenhar a variação do perfil Gestor com a lista "Rocco Neubert · Gestor · Leste · 5 vendedores" e o botão "Entrar como Rocco Neubert".

#### acertos

- A estrutura de trilho de 60 px, menu lateral de 248 px e painel branco de raio 16 px com borda #E3E6EA é fiel às capturas do G4 OS, com o indicador ativo (barra dourada de 3 px e fundo #EAECEF) idêntico ao da referência.
- Os tokens estão bem definidos e documentados (papéis de cor com descrição de uso), e todo o texto passa de 4,5:1: #5A6673 dá 5,9:1 sobre branco, #8A6327 dá 5,4:1 sobre branco e 4,7:1 sobre o creme, e o verde de venda dá 4,6:1 sobre o fundo verde.
- O botão principal azul-marinho, o secundário branco com borda e o controle segmentado (login e "Lado a lado / Declarado / Real") seguem a linguagem da referência e são iguais entre as telas.
- O padrão de item selecionado com barra dourada à esquerda e fundo cinza se repete com coerência no menu, na lista de pessoas do login e no trilho.
- As colunas numéricas (Valor, Chance, Esperado, Taxa de ganho, dias e chips de desfecho) estão alinhadas à direita e formam faixas verticais limpas nas tabelas das telas 02, 03 e 04.
- O tamanho tipográfico da tela 02 tem boa hierarquia: número de 40 px em peso 800 para o pipeline vivo, KPIs secundários em cinza e explicação do score em três colunas legíveis.
- O selo "Conceito" está presente em todas as telas e o rodapé do login declara que não é produto oficial: preservar e reforçar.
- O painel escuro do login é uma escolha própria (a referência não tem superfícies escuras) que funciona como capa sem copiar o G4 OS, com texto secundário #A9B4C0 a 8,1:1 sobre #0B1D2E.

## faltaram


