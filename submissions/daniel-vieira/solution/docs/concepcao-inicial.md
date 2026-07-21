# Escopo e propósito desta concepção inicial

Este documento não deve ser encarado como uma especificação fechada e completa, nem como um
retorno ao modelo cascata. A sua inspiração como artefato remete ao Processo Unificado Iterativo
(RUP) e ao reconhecimento de que, ainda que existam muitas bordas cinzas, há um núcleo de
conhecimento estabelecido e documentável no projeto LeadScorer.

Este documento é a base para a expansão do domínio sobre o problema-objeto e para a geração e o
desdobramento das tarefas de desenvolvimento do aplicativo web de classificação (ranqueamento)
de leads, o objeto final do projeto LeadScorer.

As fontes canônicas prevalecem sobre este texto em caso de conflito: a metodologia de scoring
reside em 'docs/metodologia-scoring.md' e no código de 'src/scoring.lisp'; a análise
exploratória, em 'docs/analise-exploratoria.md'; o esquema de dados de referência, nos arquivos
de 'data/normalized/'. Quando as migrações de schema (tarefa 9P4D) e os parâmetros de modelo
existirem, tornam-se a fonte canônica do modelo de dados e da parametrização, e este documento
passa a referenciá-los.


# Propósito geral da aplicação

O aplicativo web LeadScorer tem o objetivo de demonstrar o ranqueamento de oportunidades de
venda de um determinado produto a um cliente potencial, conduzido por um agente de vendas
específico. Além de demonstrar o modelo de ranqueamento e as suas dimensões de análise, o
aplicativo realiza a gestão básica do ciclo de vida de engajamento necessário para a
retroalimentação das oportunidades.


# Oportunidade e ciclo de engajamento

O modelo de ranqueamento mede o potencial, naquele momento, de venda de um determinado produto
para um determinado cliente (conta), considerando a ação de um agente de vendas específico.
Assim, uma oportunidade bruta é o binômio de um produto para uma conta, ao passo que uma
oportunidade qualificada é o trinômio de um produto para uma conta engajada por um agente.

Uma oportunidade assume dois estados persistentes: (a) 'prospecting', quando está disponível
para ser avaliada por qualquer agente de vendas; e (b) 'engaging', quando é engajada por um
agente e, até o final do ciclo de engajamento, fica visível apenas para esse agente. Os
desfechos de venda, 'won' e 'lost', não são estados persistentes da oportunidade: são eventos
registrados no histórico de ciclos, e a oportunidade retorna ao estado 'prospecting' após o
desfecho, conforme detalhado adiante.

As oportunidades disponíveis são listadas por ordem de potencial, permitindo que os agentes as
avaliem e se engajem em uma ou mais. De forma arbitrária, admite-se que um agente se engaje em
até dez oportunidades simultaneamente. O agente consegue estratificar e filtrar as oportunidades
por características do produto ou da conta, bem como reordenar a listagem por qualquer parâmetro
escalar ou alfabético.

As dez primeiras oportunidades exibidas para cada agente compõem o seu top tier de escolha.
Espera-se que, em situações normais, sejam engajadas antes das demais. Quando um agente engajar
uma oportunidade fora do seu top tier, precisará justificar a ação, escolhendo uma das
justificativas possíveis: (a) discordância da avaliação daquela oportunidade; (b) consulta
direta do cliente sobre aquele produto; ou (c) outro motivo.

As oportunidades engajadas, enquanto neste estado, são exibidas apenas ao agente que as puxou. O
agente consegue estratificar e filtrar as oportunidades engajadas por características do produto
ou da conta, bem como pela data do engajamento, e reordenar tal listagem por qualquer parâmetro
escalar, temporal ou alfabético.

Quando uma oportunidade chega ao final do ciclo de engajamento, seja por expiração, seja por
ação do agente de vendas, o seu potencial sofre decaimento, pois uma venda foi realizada,
recusada ou não concluída a tempo, e ela é retroalimentada nas partes mais baixas da lista de
oportunidades disponíveis. A regra de decaimento define um processo de redução do potencial da
oportunidade, que afeta o seu scoring e, portanto, a sua ordem nas listagens, e observa uma data
de corte de expiração, a partir da qual a oportunidade retorna ao rol das disponíveis, ainda que
com a sua qualificação revisada.

Caso o ciclo se conclua por entendimento do agente, este declara se a ação de venda logrou êxito
(desfecho 'won') ou fracasso (desfecho 'lost'). O registro histórico dessas ações, a saber, qual
a oportunidade, quando começou, quando terminou e como terminou, é armazenado em um histórico
específico de ciclos. Para fins de normalização, as oportunidades expiradas pela regra de
decaimento são marcadas nesse histórico com o desfecho 'lost'.


# Modelo de qualificação de oportunidades

A análise exploratória do problema, a proposta de modelagem do ranqueamento e do ciclo de
decaimento, bem como o teste de validação, residem em 'docs/analise-exploratoria.md',
'docs/metodologia-scoring.md' e 'docs/validacao-scoring.md'. Esta seção descreve o modelo do
ponto de vista da aplicação; a formalização e os valores concretos residem nessas fontes e no
código.

O potencial de uma oportunidade é representado por um número inteiro de 0 a 100 e considera seis
dimensões, cada uma também normalizada a uma escala de 0 a 100. Quatro dimensões são
computacionalmente ativas e participam do potencial com peso próprio; duas são inertes nesta
base, com peso zero, e não são exibidas como colunas na listagem. O registro dessas dimensões é
deliberado: demonstra que elas foram consideradas e são válidas no mundo real, embora a base de
dados disponível, de caráter artificial e insuficiente, não as sustente. A nota explicativa do
potencial as menciona.

Dimensões ativas:

- Momentum: o potencial relativo ao comportamento de compra daquela conta para aquele produto. É
  o eixo primário, de maior peso, e tem duas faces conforme a lista, a maturidade de recompra
  nas disponíveis e o decaimento pós-engajamento nas engajadas;
- Retorno: o potencial econômico do negócio, ancorado no ticket médio do cliente para aquele
  produto, com recuo por setor quando o par não tem histórico de venda;
- Afinidade: o interesse do cliente pelo produto, medido pelo volume de negócios fechados do par;
- Especialização do agente: a habilidade de venda demonstrada do agente para aquele produto ou
  perfil de cliente. É a dimensão que personaliza o ranqueamento por agente.

Dimensões inertes nesta base (peso zero, não exibidas na listagem):

- Diligência do cliente: a diligência em fechar transações, ancorada no tempo médio de
  fechamento. A validação mostra que não distingue o desfecho nesta base e é colinear com o
  decaimento do momentum, com sinal invertido, de modo que recebe peso zero para não injetar
  ruído;
- Atividade do cliente: o grau de recência e atividade de consumo, derivado do inverso do tempo
  de inatividade. Nesta base nenhuma conta permanece inativa, de modo que a dimensão é quase
  constante e a sua contribuição é nula. É ativável em produção.

A adoção de pesos arbitrados, aplicados de maneira fundamentada, decorre de a análise
exploratória não permitir aprender tais pesos dos dados, dada a conversão praticamente plana; os
pesos residem na configuração da implementação, conforme adiante, e não são reafirmados aqui.
Embora a forma de computação de cada dimensão possa ser discutida e enriquecida à medida que
mais dados de comportamento de compra sejam disponibilizados, as dimensões representam um grupo
coeso e canônico dos vetores que governam o potencial de uma oportunidade de venda, alinhado ao
modelo Recency-Frequency-Monetary acrescido do eixo do agente, conforme a metodologia.

O potencial não é uma soma ponderada. A agregação combina um portão de elegibilidade não
compensatório com a média geométrica ponderada das quatro dimensões ativas, de modo que uma
dimensão baixa, em particular um momentum baixo, arrasta o índice, e um momentum nulo o zera. A
fundamentação, a evolução desde a forma aditiva inicial e a evidência empírica residem no ADR
C4X9 e em 'docs/validacao-scoring.md'.

A listagem de oportunidades exibe tanto o potencial geral quanto os valores por dimensão,
permitindo o refinamento do julgamento por parte do agente de vendas. Ao posicionar o ponteiro
sobre o rótulo de uma dimensão, o agente vê uma nota explicativa com o resumo da dimensão e o
seu peso na análise geral. O mesmo comportamento aplica-se ao rótulo do potencial geral.

Neste MVP, os pesos e os demais valores dos modelos e das regras de negócio são mantidos em um
arquivo de configuração em forma Lisp (s-expression), lido pela aplicação pelo leitor nativo com
a avaliação em tempo de leitura desabilitada ('*read-eval*' em falso), de modo que a configuração
seja dado, e não código executável. Esse arquivo, quando existir, torna-se a fonte canônica da
parametrização.


# Ciclo de computação do modelo

A documentação do modelo apresenta os prazos reais de computação, decaimento e expiração. Para
conferir dinamismo ao uso deste MVP, adota-se o seguinte ciclo de computação acelerado:

- O serviço de ranqueamento é executado a cada minuto;
- O serviço de decaimento e expiração é executado a cada minuto;
- Uma oportunidade engajada expira em vinte minutos.

O ranqueamento é personalizado por agente, de modo que o serviço recomputa, a cada ciclo, uma
pontuação por par de oportunidade disponível e agente. Trata-se de uma implicação de arquitetura
que o documento declara explicitamente: o volume de pontuações recomputadas é da ordem do
produto entre o número de pares disponíveis e o número de agentes, aceitável para a escala deste
MVP. Em produção, a personalização por agente para todo o universo de pares seria substituída
por uma regra de distribuição, que atribui subconjuntos de leads a agentes e evita o cômputo
exaustivo; essa direção é coerente com o ADR B7Q3, que incorpora a capacidade do agente ao
próprio potencial em vez de manter um modelo separado de distribuição, deixando a distribuição
explícita fora do escopo do MVP.


# Tela inicial

A tela inicial de cada aplicação apresenta, no alto, uma faixa de cartões de indicadores-chave
(KPIs) e, logo abaixo, a lista de destaque pertinente ao papel do usuário. Não há gráficos na
tela inicial deste MVP, em conformidade com o princípio de simplicidade e com o diferimento dos
dashboards de visualização; a faixa de cartões e a lista de destaque concentram a informação de
abertura.

## Faixa de indicadores

Os cartões resumem o desempenho do escopo do usuário: os do próprio agente, na aplicação do
agente, e os agregados do time, na aplicação do gerente. Os indicadores são derivados por
agregação sobre o histórico de ciclos ('engagements') e não requerem tabela adicional. Os
cartões seguem o padrão do design system, com rótulo, valor destacado e sub-rótulo, sem efeitos
de profundidade.

Os seis indicadores adotados são:

- Total acumulado de engajamentos: a contagem de ciclos de engajamento do escopo;
- Total de sucessos: a contagem de ciclos com desfecho 'won';
- Taxa de sucesso: a proporção de ciclos 'won' sobre os ciclos fechados ('won' mais 'lost'),
  expressa em pontos percentuais;
- Ticket médio: a média do valor de fechamento dos ciclos 'won', em USD;
- Total acumulado em vendas: a soma do valor de fechamento dos ciclos 'won', em USD;
- Tempo médio de venda: a média da duração entre o engajamento e o fechamento dos ciclos 'won',
  em dias corridos.

Os valores monetários observam a regra da casa, isto é, inteiro na menor unidade da moeda com o
código ISO 4217, e são apenas formatados para exibição. As agregações residem no código da
aplicação, não sendo reafirmadas aqui.

## Lista de destaque

Abaixo da faixa de cartões, a tela inicial do agente lista o seu top tier, isto é, as dez
oportunidades disponíveis mais bem ranqueadas para aquele agente, de modo que a ação prioritária
esteja imediatamente à mão; a lista completa de disponíveis, com filtros e ordenação, permanece
acessível em visão própria. A tela inicial do gerente lista as oportunidades engajadas pelo seu
time, de modo que o acompanhamento esteja imediatamente à mão; a visão completa, com filtros e
ordenação, permanece acessível em visão própria.


# Descrição de usuários

- Agente de vendas: usuário responsável pelo engajamento de oportunidades de venda. Analisa uma
  lista ranqueada de oportunidades, escolhe oportunidades para engajar e gerencia o ciclo de
  engajamento;
- Gerente de vendas: usuário especial, que agrupa agentes de vendas e caracteriza, assim, um
  time de vendas. Visualiza, filtra e reordena a lista de oportunidades engajadas pelos agentes
  membros da sua equipe, com a finalidade de acompanhar o trabalho do time.


# Estórias de usuário

## Identificação e acesso

Como um USUÁRIO (agente ou gerente), desejo me identificar por seleção do meu nome de usuário, a
partir de uma lista dos usuários semeados, sem senha, de modo que a aplicação estabeleça a minha
sessão e apresente a interface correspondente ao meu papel.

## Tela inicial: painel de indicadores

Como um AGENTE DE VENDAS, ao acessar a TELA INICIAL, desejo ver uma faixa de CARTÕES DE
INDICADORES com o meu desempenho acumulado, a saber, total de engajamentos, total de sucessos,
taxa de sucesso, ticket médio, total acumulado em vendas e tempo médio de venda, de modo que eu
avalie o meu resultado antes de escolher novas oportunidades.

Como um GERENTE DE VENDAS, ao acessar a TELA INICIAL, desejo ver a mesma faixa de CARTÕES DE
INDICADORES agregada para o meu TIME, considerando os agentes vinculados a mim, de modo que eu
acompanhe o desempenho do time.

Como um AGENTE DE VENDAS, na TELA INICIAL, abaixo dos CARTÕES DE INDICADORES, desejo ver o meu
TOP TIER, as dez oportunidades disponíveis mais bem ranqueadas para mim, de modo que eu engaje
as prioritárias sem navegar à lista completa de disponíveis.

Como um GERENTE DE VENDAS, na TELA INICIAL, abaixo dos CARTÕES DE INDICADORES, desejo ver as
OPORTUNIDADES ENGAJADAS pelo meu time, de modo que eu acompanhe o trabalho corrente sem navegar
à visão completa.

## Agente de vendas: lista de oportunidades disponíveis

Como um AGENTE DE VENDAS, desejo visualizar uma LISTA RANQUEADA de OPORTUNIDADES DISPONÍVEIS
(estado 'prospecting'), pública a todos os agentes. Cada OPORTUNIDADE refere-se a um par
conta-produto e apresenta um número inteiro de 0 a 100 para o POTENCIAL DA OPORTUNIDADE,
indicadores individuais inteiros de 0 a 100 para cada uma das quatro DIMENSÕES ATIVAS (Momentum,
Retorno, Afinidade e Especialização), não exibindo as duas dimensões inertes (Diligência e
Atividade), bem como informações de CONTEXTO da oportunidade (nome do cliente, produto indicado,
prazo médio de decisão do cliente para aquele produto, valor da última compra do cliente para
aquele produto, porte do cliente, receita do cliente, data de fundação do cliente, setor do
cliente e localidade do cliente).

Como um AGENTE DE VENDAS, ao visualizar a LISTA RANQUEADA de OPORTUNIDADES DISPONÍVEIS, desejo
que as dez primeiras oportunidades, o meu TOP TIER, sejam visualmente destacadas, de modo que eu
reconheça a região de topo recomendada pelo modelo.

Como um AGENTE DE VENDAS, ao posicionar o ponteiro sobre o rótulo do POTENCIAL DA OPORTUNIDADE
ou sobre o rótulo de qualquer DIMENSÃO, desejo ver uma NOTA EXPLICATIVA com o resumo do
indicador e o seu peso na análise geral, de modo que eu compreenda a composição do ranqueamento.

Como um AGENTE DE VENDAS, ao visualizar a LISTA RANQUEADA de OPORTUNIDADES DISPONÍVEIS ou a
minha LISTA DE OPORTUNIDADES ENGAJADAS, desejo filtrar as OPORTUNIDADES por localidade do
cliente, setor do cliente, série do produto e nome do produto. Na lista de disponíveis,
desejo filtrar também por data de disponibilização; na lista de engajadas, por data de
engajamento.

Como um AGENTE DE VENDAS, ao visualizar a LISTA RANQUEADA de OPORTUNIDADES DISPONÍVEIS ou a
minha LISTA DE OPORTUNIDADES ENGAJADAS, desejo ordenar as OPORTUNIDADES por porte do cliente,
prazo médio de decisão do cliente para aquele produto, valor da última compra do cliente para
aquele produto, número de funcionários, receita do cliente e data de fundação do cliente.

Como um AGENTE DE VENDAS, ao visualizar a LISTA RANQUEADA de OPORTUNIDADES DISPONÍVEIS, desejo
ver o FILTRO DE CORTE aplicado pelo modelo, de modo que eu reconheça o limiar de potencial
abaixo do qual as oportunidades são omitidas ou rebaixadas.

## Agente de vendas: engajamento e ciclo

Como um AGENTE DE VENDAS, desejo ENGAJAR uma OPORTUNIDADE DISPONÍVEL, trazendo-a para a minha
área de controle, de modo que ela deixe de ser listada como disponível para os demais agentes e
passe a constar da minha LISTA DE OPORTUNIDADES ENGAJADAS.

Como um AGENTE DE VENDAS, ao ENGAJAR uma OPORTUNIDADE que não esteja no meu TOP TIER, desejo
fornecer uma JUSTIFICATIVA, escolhida entre discordância da avaliação, consulta direta do
cliente e outro motivo, de modo que o desvio da recomendação do modelo fique registrado.

Como um AGENTE DE VENDAS, ao tentar ENGAJAR uma OPORTUNIDADE quando já possuo dez oportunidades
engajadas, desejo ser impedido de fazê-lo e informado do limite, de modo que a minha carteira de
engajamento respeite o limite de dez oportunidades simultâneas.

Como um AGENTE DE VENDAS, na minha LISTA DE OPORTUNIDADES ENGAJADAS, desejo alterar o desfecho
de uma OPORTUNIDADE ENGAJADA para VENDA FECHADA (desfecho 'won'), VENDA PERDIDA (desfecho
'lost') ou DEVOLVÊ-LA sem desfecho, de modo que a oportunidade deixe a minha lista pessoal e o
ciclo seja registrado no histórico quando houver desfecho. Um desfecho, won ou lost, devolve a
oportunidade à lista pública de disponíveis com o potencial decaído pela recência da transação;
uma devolução sem desfecho, por não constituir uma transação, devolve a oportunidade ao seu
ranqueamento de linha de base, sem decaimento por recência, conforme o ADR S9K5.

## Gerente de vendas: acompanhamento do time

Como um GERENTE DE VENDAS, desejo visualizar a LISTA DE OPORTUNIDADES ENGAJADAS pelos AGENTES DE
VENDAS vinculados a mim. Cada registro refere-se a um par agente-oportunidade e apresenta a
identificação do agente, a data de engajamento, a data de fechamento, o desfecho, a
justificativa de engajamento e os dados da oportunidade.

Como um GERENTE DE VENDAS, ao visualizar a LISTA DE OPORTUNIDADES ENGAJADAS do meu time, desejo
filtrar os registros por agente, por características do produto e da conta e pela data de
engajamento, e reordená-los por qualquer parâmetro escalar, temporal ou alfabético, de modo que
eu acompanhe o trabalho do time sob diferentes recortes.

## Serviços automáticos do sistema

Como o SISTEMA, a cada minuto recomputo o RANQUEAMENTO das oportunidades disponíveis para cada
agente, de modo que as listas reflitam o potencial corrente.

Como o SISTEMA, a cada minuto aplico o DECAIMENTO do potencial das oportunidades engajadas em
função da idade desde o engajamento e EXPIRO as que ultrapassam o corte de vinte minutos,
registrando a expiração no histórico com o desfecho 'lost' e devolvendo a oportunidade à lista
de disponíveis com potencial decaído.


# Modelo relacional

O modelo abaixo é a especificação conceitual da qual a tarefa 9P4D derivará as migrações SQL
numeradas, que se tornarão a fonte canônica. Os nomes seguem '.claude/rules/std-sql.md', a
saber, tabelas no plural em snake_case, colunas no singular e sem repetição do nome da tabela.
As chaves substitutas (id) são inteiras; as entidades de referência são semeadas dos arquivos de
'data/normalized/' e são imutáveis no MVP. Os valores monetários são armazenados como inteiro na
menor unidade da moeda acompanhado do código ISO 4217; a moeda do dataset é indeterminada na
fonte e adota-se USD como convenção documentada. Os instantes são armazenados como UNIX em
milissegundos, em UTC.

## Grupo de referência (semeado dos CSV, imutável no MVP)

- Tabela 'accounts' (origem: accounts.csv)
  - id: chave substituta
  - name: nome da conta (único)
  - sector: setor
  - year_established: ano de fundação
  - revenue_amount: receita, inteiro na menor unidade
  - revenue_currency: código ISO 4217 da receita
  - employees: número de funcionários
  - location: localidade da conta (origem: office_location)
  - subsidiary_of_id: chave estrangeira para accounts.id, nula para conta não subsidiária

- Tabela 'products' (origem: products.csv)
  - id: chave substituta
  - name: nome do produto (único)
  - series: série do produto
  - list_price_amount: preço de tabela, inteiro na menor unidade (origem: sales_price)
  - list_price_currency: código ISO 4217 do preço de tabela

- Tabela 'regional_offices' (origem: coluna regional_office de sales_teams.csv)
  - id: chave substituta
  - name: nome do escritório (Central, East, West), único

- Tabela 'sales_managers' (origem: coluna manager de sales_teams.csv)
  - id: chave substituta
  - name: nome do gerente (único)
  - username: identificador de login por seleção (único), derivado do nome
  - regional_office_id: chave estrangeira para regional_offices.id

- Tabela 'sales_agents' (origem: sales_teams.csv)
  - id: chave substituta
  - name: nome do agente (único)
  - username: identificador de login por seleção (único), derivado do nome
  - sales_manager_id: chave estrangeira para sales_managers.id
  - (o escritório do agente é derivado via gerente, dado que cada gerente pertence a um único
    escritório, e não é duplicado)

- Tabela 'engagement_justifications' (semeada, três valores)
  - id: chave substituta
  - code: código estável da justificativa (único)
  - description: descrição legível

## Grupo do ciclo de engajamento (operacional)

- Tabela 'opportunities' (par conta-produto, estado ativo)
  - id: chave substituta
  - account_id: chave estrangeira para accounts.id
  - product_id: chave estrangeira para products.id
  - status: estado persistente, restrito a 'prospecting' ou 'engaging'
  - engaged_by_id: chave estrangeira para sales_agents.id, nula fora do estado 'engaging'
  - engaged_at: instante do engajamento, nulo fora do estado 'engaging'
  - created_at: instante de criação
  - restrição de unicidade sobre (account_id, product_id): um par ativo por vez

- Tabela 'opportunity_scores' (ranking personalizado por agente)
  - id: chave substituta
  - opportunity_id: chave estrangeira para opportunities.id
  - sales_agent_id: chave estrangeira para sales_agents.id
  - score_overall: potencial geral, inteiro de 0 a 100
  - score_economic: dimensão de Retorno (potencial econômico), inteiro de 0 a 100
  - score_affinity: dimensão de Afinidade, inteiro de 0 a 100
  - score_momentum: dimensão de Momentum, inteiro de 0 a 100
  - score_adherence: dimensão de Especialização do agente (o símbolo score_adherence será
    renomeado na Parte 2, tarefa X7F2), inteiro de 0 a 100
  - score_closing_time: dimensão de Diligência (tempo de fechamento), inerte, nula (não exibida)
  - score_inactivity: dimensão de Atividade (inatividade), inerte, nula (não exibida)
  - computed_at: instante da última computação
  - restrição de unicidade sobre (opportunity_id, sales_agent_id)

- Tabela 'engagements' (histórico de ciclos: semeado do pipeline e ao vivo) (observação: as
  linhas Won, Lost e Engaging de sales_pipeline.csv semeiam esta tabela; o opportunity_id do CSV
  é mantido apenas como proveniência, pois a oportunidade aqui é o par conta-produto, e cada
  linha do pipeline é um ciclo)
  - id: chave substituta
  - opportunity_id: chave estrangeira para opportunities.id
  - sales_agent_id: chave estrangeira para sales_agents.id
  - justification_id: chave estrangeira para engagement_justifications.id, nula quando o
    engajamento ocorre dentro do top tier
  - engaged_at: instante do engajamento
  - closed_at: instante do fechamento, nulo enquanto o ciclo está aberto
  - outcome: desfecho, restrito a 'won' ou 'lost', nulo enquanto aberto ou se devolvido
  - expired: indicador de expiração automática
  - close_value_amount: valor de fechamento, inteiro na menor unidade, nulo quando não
    aplicável
  - close_value_currency: código ISO 4217 do valor de fechamento

O momentum de cada dimensão lê os ciclos fechados de 'engagements' para o par conta-produto,
tanto a maturidade de recompra na lista de disponíveis quanto o decaimento pós-engajamento na
lista de engajadas.


# Arquitetura e stack tecnológica

- Aplicação do gerente de vendas e aplicação do agente de vendas segregadas, sem gestão de
  papéis;
- Aplicação web responsiva (validação no iPhone 13), inteiramente server-side, não SPA;
- Identificação por login de seleção, sem senha, com sessão de servidor;
- Camada de persistência em PostgreSQL, com a versão fixada;
- Parâmetros de modelo e regras de negócio (limites, pesos e afins) em um arquivo de configuração
  em forma Lisp (s-expression), lido pela aplicação com '*read-eval*' em falso;
- Backend em Common Lisp, conforme o ADR D2K9 (Clack, Hunchentoot, Ningle, Spinneret,
  Postmodern);
- Componentes de interface e frontend com HTMX e HTML/CSS, respeitando o escopo server-side;
- Entrega e distribuição com Docker e Docker Compose em produção e Podman em desenvolvimento,
  conforme o ADR D4M3.


# Aspectos de interface e experiência

- O projeto adota o tema escuro e é monotema;
- As diretrizes do design system residem em '.claude/rules/design.md';
- Os tokens de estilo residem em '.claude/assets/tokens/';
- A tela inicial de cada aplicação apresenta, no alto, a faixa de cartões de indicadores
  descrita na seção "Painel de indicadores da tela inicial"; as listas de oportunidades seguem o
  padrão de tabela do design system, com cabeçalhos, indicadores de status e algarismos
  tabulares;
- A interface é responsiva, com validação no iPhone 13, colapsando a grade de cartões e a
  navegação nas larguras estreitas;
- Os arquivos de imagem em '.claude/assets/examples/' são exemplos ilustrativos, não normativos,
  de outra aplicação que compartilha o mesmo tema escuro, mantidos como referência de padrão
  visual; a fonte canônica de estilo permanece o design system;
- Em vez de wireframes stricto sensu, adota-se o processo orientado a exemplos do design system,
  produzindo protótipos autônomos em HTML e CSS nomeados no padrão
  'example-{topic}-{theme}.html' e arquivados em '.claude/assets/examples/'.


# Limitações intencionais de escopo

Dado o caráter de protótipo deste projeto, os seguintes recursos e funcionalidades são
deliberadamente diferidos (lista não exaustiva):

- Recuperação de senhas e credenciais;
- Cadastro e gestão de usuários;
- Gestão de papéis de usuários;
- Cadastro e parametrização de produtos;
- Cadastro e parametrização de clientes;
- Justificativas customizadas para um engajamento fora do top tier;
- Indicador de cross-selling da oportunidade, tanto como contexto exibido quanto como filtro: o
  dataset não o carrega como campo e a sua derivação (a conta possui negócio ganho para um
  produto distinto do da oportunidade) constituiria um incremento de modelagem de dados não
  justificado no MVP; a dimensão Afinidade já cobre o histórico do cliente para o mesmo produto;
- Ambiente administrativo para parametrização do modelo ou das regras de negócio;
- Distribuição explícita de leads como alocação a agentes, com heurísticas de casamento ou de
  equilíbrio de carga, conforme o ADR B7Q3;
- Registro do ciclo de vida do processo de venda e do relacionamento com o cliente;
- Registro financeiro da venda;
- API e demais recursos para integração e uso programático;
- Ferramentas para interação com clientes.
