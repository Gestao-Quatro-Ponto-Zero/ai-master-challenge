# Prompts utilizados

Este arquivo reúne os principais prompts utilizados durante o desenvolvimento da solução do Challenge 004 - Estratégia Social Media. Os prompts foram organizados em ordem cronológica para evidenciar o processo de uso de IA, desde o enquadramento do problema até a construção da análise e da estratégia final.

## Prompt 1 - Contextualização do desafio e alinhamento com a LLM

**Objetivo:** contextualizar a IA sobre o desafio, definir o papel esperado da LLM e estabelecer cuidados metodológicos antes da análise do dataset.

```text
Eu sou a mais nova AI Master Challenge do G4. Você deve atuar como meu assistente, um parceiro sênior de Marketing Analytics, Social Media Strategy e IA aplicada a negócios. Vou usar você como LLM, visando o apoio estratégico, mas a entrega final precisa ser baseada em dados, com análise crítica e recomendações acionáveis.

Já temos o nosso primeiro desafio: A empresa possui um dataset com aproximadamente 52 mil posts publicados em múltiplas plataformas, incluindo youtube, tiktok, bilibili, instagram e rednote. O Head de Marketing quer entender três coisas principais: o que gera engajamento de verdade, se vale a pena patrocinar influenciadores e qual deveria ser a estratégia de conteúdo baseada em dados.

Antes de analisar os dados da tabela, preciso que considere alguns cuidados importantes:

- não quero conclusões genéricas como "vídeos performam melhor que imagens";
- a análise precisa ser SEGMENTADA por plataforma, período, categoria, tipo de conteúdo, tamanho do creator, audiência, status de patrocínio;
- engagement rate isolado pode enganar, então ele deve ser contextualizado com views, alcance, plataforma e tamanho do creator;
- a comparação entre posts orgânicos e patrocinados precisa ser justa, evitando comparar grupos muito diferentes;
- a entrega final precisa ser compreensível para um Head de Marketing não técnico em poucos minutos, a linguagem precisa ser clara e objetiva;
- quero identificar tanto o que funciona quanto o que NÃO funciona;
- ao final, vou transformar os achados em decisões práticas para o time de social media, a princípio um dashboard interativo.

Entendeu o desafio? Pronto para encarar?
```

## Prompt 2 - Primeiro contato com o dataset

**Objetivo:** iniciar a análise do dataset com uma leitura descritiva, ainda sem gerar recomendações finais. A intenção foi entender quais dados estavam representados, quais categorias existiam e como a base poderia ser explorada nas próximas etapas.

```text
Ok, mãos a obra! Anexei aqui o dataset. Vamos prosseguir com calma, apenas me diga o que você vê entre as categorias, quais são os dados representados? 

Algumas infromações são úteis e tornam esse conjunto de dados interessante: 
Orgânico x patrocinado: flag is_sponsoredpermite comparar ROI de patrocínio diretamente 
Multiplataforma: mesmo tipo de conteúdo com desempenho diferente por plataforma 
Audiência: dados demográficos permitem análise por persona/segmento 
Volume 52K posts é massa suficiente para análise estatística robusta 

Além disso, podemos seguir essas dicas também: 
52.000 postagens é muito dado. Segmente antes de analisar — ​​por plataforma, por período, por categoria. "Vídeos performam melhor que imagens" é o que a IA vai dizer se você colar o brief. “Vídeos de 30-60s na categoria Tech, com criadores de 10K-50K seguidores, geram 3,2x mais compartilhamentos que a mídia da plataforma” é o que um AI Master entrega. Taxa de engajamento isolado mente. 
Contextualize com alcance, plataforma e tamanho do criador. 
Se recomendar "postar mais no TikTok", explique o que postar, para quem , quando , e com que evidência dos dados. 
O Head de Marketing não é cientista de dados. Se ele não entendeu sua saída em 5 minutos, você perdeu. 
Cuidado com as viés de sobrevivência: posts com muito engajamento são visíveis, mas quantos posts tiveram engajamento zero?
```


## Prompt 3 - Análise quantitativa inicial e benchmarks de performance

**Objetivo:** avançar da leitura inicial do dataset para uma primeira análise quantitativa, criando benchmarks de performance antes de aprofundar a comparação entre posts orgânicos e patrocinados.

```text
Ótimo! Agora que já fizemos a primeira leitura do dataset, quero avançar para a análise QUANTITATIVA inicial



Ainda não quero a estratégia final. A ideia agora é construir benchmarks de performance para entender como as métricas se comportam antes de cruzar orgânico vs patrocinado de forma mais profunda, ok?



Considere os pontos de atenção já identificados:



* não há posts com engajamento zero (não vamos tratar isso como um problema ou questionar a veracidade dos números, esse não é o foco)

* as views parecem como proporcionais

* follower_count varia bastante e PRECISA ser usado para segmentar creators

* hashtags e comments_text têm alguns valores ausentes, precisamos avaliar se posts com hashtags engajam mais organicamente, como estratégia de SEO e também posteriormente avaliar qualitativamente os comentários

* ATENCAO: engagement rate isolado pode enganar

* volume de posts não deve ser interpretado automaticamente como performance



Faça a PRIMEIRA análise em etapas:



1. Calcule estatísticas descritivas para:

   - views

   - likes

   - shares

   - comments_count

   - follower_count

   - content_length 

   - engagement_rate



SEJA TÉCNICO, inclua índices de média, mediana, mínimo, máximo, desvio padrão e percentis 25, 50 e 75



2. Compare a performance por:

- plataforma

- categoria

- tipo de conteúdo

- status orgânico vs. patrocinado

- faixa etária da audiência

- gênero da audiência

- localização da audiência



3. Crie faixas de tamanho de creator a partir de follower_count, por exemplo:

   - 1K–10K

   - 0K–50K

   - 50K–100K

   - 100K–500K

   - 500K mais



Depois compare engagement_rate, views, shares e comments_count por essas faixas



4. Não use apenas médias, priorize mediana, distribuição e tamanho da amostra de cada grupo



5. Aponte quais diferenças parecem relevantes e quais parecem pequenas demais para virar recomendação



6. Identifique possíveis GRÁFICOS para visualizar esta etapa.



Não gere ainda recomendações estratégicas finais. O objetivo desta etapa é criar uma base quantitativa confiável para as próximas análises
```


## Prompt 4 - Comparação controlada entre orgânico e patrocinado

**Objetivo:** aprofundar a análise sobre patrocínio (visando responder uma das perguntas do head), evitando uma comparação bruta entre todos os posts patrocinados e todos os posts orgânicos. A intenção foi comparar grupos mais equivalentes para entender em quais condições patrocinar creators parece funcionar ou não.


```text
Ok, muito bom. Essa análise quantitativa inicial mostrou que as metricas agregadas são muito próximas entre os grupos e agora precisamos sair da leitura geral e avançar para cruzamentos mais ESPECÍFICOS! Os detalhes nos interessam!



Vamos caminhar para responder uma das perguntas do head de marketing: vale a pena patrocinar influenciadores?





Quero que você faça a análise de orgânico vs patrocinado de forma controlada



Não compare todos os posts patrocinados contra todos os orgânicos de forma bruta. Compare apenas grupos equivalentes, considerando:

- plataforma

- categoria

- tipo de conteúdo

- faixa de seguidores do creator

- faixa etária da audiência, quando houver volume suficiente

- localização da audiência, quando houver volume suficiente



Crie uma tabela de células de performance com:

1. plataforma

2. categoria

3. tipo de conteúdo

4. faixa de creator

5. número de posts orgânicos

6. número de posts patrocinados

7. mediana de engagement_rate orgânico

8. mediana de engagement_rate patrocinado

9. diferença em pontos percentuais

10. mediana de views orgânico

11. mediana de views patrocinado

12. mediana de shares orgânico

13. mediana de shares patrocinado

14. leitura: patrocinado melhor, orgânico melhor ou diferença irrelevante



use um volume mínimo por célula para evitar conclusões frágeis

Sugira um threshold, um mínimo de amostra antes de interpretar os resultados



Ao final, separe:

- células em que patrocínio parece ter uplift positivo

- células em que patrocínio parece não agregar

- células em que o orgânico performa melhor

- células inconclusivas por baixo volume ou diferença pequena



NÃO gere ainda a estratégia final, eu quero apenas entender em quais condições patrocínio parece funcionar ou não

```


## Prompt 5 - Padrões das células positivas e negativas

**Objetivo:** identificar padrões comuns nas células em que posts patrocinados apresentaram uplift positivo e nas células em que posts orgânicos performaram melhor. A intenção foi entender em quais combinações de plataforma, categoria, tipo de conteúdo, faixa de creator, sponsor_category, disclosure_type, hashtags e audiência o patrocínio parece mais promissor ou mais arriscado, sem ainda transformar os achados em estratégia final.

```text
Certo... em geral  a comparação controlada mostrou que patrocínio não funciona como efeito universal: existem células positivas, negativas, neutras e inconclusivas. PORÉM, acho uma resposta muito abrangente e genérica para o head... precisamos de mais detalhes e especificidade.



Agora quero uma análise de padrões, ainda não gere ainda a estratégia final. Quero entender o que as células positivas e negativas têm em comum



Analise as células em que o patrocinado teve uplift positivo e compare com as células em que o orgânico performou melhor



Considere:

- plataforma

- categoria

- tipo de conteúdo

- faixa de creator

- mediana de engagement_rate

- mediana de views

- mediana de shares

- sponsor_category, quando houver

- disclosure_type, quando houver

- presença de hashtags

- faixa etária da audiência

- localização da audiência



Quero que você responda:

1. quais padrões aparecem nas células em que o patrocinado performa melhor?

2. quais padrões aparecem nas células em que o orgânico performa melhor?

3. existe alguma plataforma onde o patrocínio parece mais promissor?

4. existe alguma categoria onde o patrocínio parece mais arriscado?

5. existe algum tipo de conteúdo que perde eficiência quando patrocinado?

6. alguma faixa de crator parece mais adequada para patrocínio?

7. sponsor_category ou disclosure_type parecem influenciar a performance?

8. hashtags parecem ajudar mais em posts orgânicos ou patrocinados?

9. quais achados são consistentes o suficiente para virar hipótese estratégica?

10. quais achados ainda são frágeis e precisam de teste?



Ao final, crie uma síntese em três blocos:

- padrões que favorecem patrocínio

- padrões que favorecem orgânico

- hipóteses para teste controlado



Se as diferenças forem pequenas SINALIZE isso claramente!!!

Não transforme diferença pequena em recomendação forte
```


## Prompt 6 - Apoio à construção das tabelas da análise de patrocínio
**Objetivo:** solicitar apoio da LLM para transformar os resultados da análise de patrocínio em tabelas claras para o relatório final. Nesta etapa, a IA foi usada para organizar a comunicação dos achados já obtidos, especialmente os critérios de comparação, o resumo das células analisadas e os exemplos de células em que patrocinado ou orgânico performaram melhor.

```text
Certo, acredito que chegamos em um caminho para a pergunta de número dois. 
Estou escrevendo a análise e preciso que você me auxilie com algumas tabelas específicas, para que eu junte ao conteúdo que estou formatando:

 - uma tabela para explicar os critérios e regras utilizadas para a comparar conteúdos orgânicos e patrocinados

 - uma tabela para falar do resultado geral das células analisadas, msotrando a leitura e o número de cédulas 

 - uma tabela que separe plataforma, categoria, tipo, faixa de creator e leitura, para mostrar as células em que o patrocinado perfomou melhor 

 - e uma outra tabela semelhante a de cima, mas para os posts orgânicos
 ```

## Prompt 7 - Análise de top performers e bottom performers

**Objetivo:** voltar à primeira pergunta do desafio — o que gera engajamento de verdade — a partir de uma análise mais específica de top performers e bottom performers. Nesta etapa, a intenção foi observar diferentes dimensões de engajamento, como alcance, engagement_rate, shares e comments_count, sem depender apenas de médias gerais ou de uma única métrica.


```text
Perfeito. Agora que já avançamos na análise de orgânico vs patrocinado, eu quero voltar para a primeira pergunta do head: o que gera engajamento de verdade?



De novo: não quero uma resposta genérica baseada apenas em médias gerais. A análise anterior já mostrou que as métricas agregadas são muito próximas, então precisamos olhar para padrões mais específicos



Faça uma análise de top performers e bottom performers, considerando diferentes formas de engajamento:



Alcance/distribuição

- posts com maiores views

- padrões por plataforma, categoria, tipo de conteúdo, faixa de creator, audiencia e status de patrocínio



Engajamento relativo

posts ou células com maior engagement_rate

cuidado para não interpretar engagement_rate isoladamente

contextualize com views, follower_count e tamanho da amostra



Circulação orgânica

posts ou células com maior número de shares

identifique quais combinações parecem gerar maior compartilhamento



Conversa/profundidade

posts ou células com maior comments_count

identifique padrões de categoria, plataforma, formato, audiencia...



Baixo desempenho

identifique bottom performers

mostre combinações que aparecem associadas a baixo engagement_rate, baixo share ou baixa conversa

diferencie baixo desempenho real de células com baixo volume.



Quero que a análise seja segmentada por:

plataforma

categoria

tipo de conteúdo

faixa de seguidores do creator

status orgânico vs patrocinado

faixa etária da audiência

genero da audiência

localização da audiência

presença ou ausência de hashtags quando fizer sentido



Regras importantes:

- Não use apenas medias. Priorize mediana, distribuição e tamanho da amostra

- Não transforme volume de posts em conclusão de performance

- Nao use engagement_rate sozinho como resposta final

- Separe achados fortes de hipóteses frágeis

- Quando uma diferença for pequena demais, diga que não sustenta recomendacao

- Quando houver baixo volume, classifique como inconclusivo

- Quero tabelas que ajudem a comunicar os achados de forma executiva



Ao final, responda de forma OBJETIVA:

quais combinações parecem gerar mais engajamento?

quais combinações parecem gerar mais compartilhamento?

quais combinações geram mais conversa?

o que parece não funcionar?

quais achados são fortes o suficiente para entrar na estratégia final?

quais achados ainda precisam ser tratados como hipótese??
 ```

 ## Prompt 8 — Apoio à construção das tabelas da análise de engajamento

**Objetivo:** solicitar apoio da LLM para transformar os achados sobre top performers e bottom performers em tabelas claras para a análise final. Nesta etapa, a IA foi usada para organizar visualmente as principais evidências da Pergunta 1, separando alcance, engagement_rate, shares e comments_count.

```text
 Ok. Vou começar a desenvolver essa parte da análise final também e novamente preciso do auxílio com algumas tabelas:

  - uma tabela que mostre o alcance em views e suas células de maiores números, para mostrar que não necessariamente siginifica engajamento forte 

  - Uma tabela para o engagement_rate, mostrando que as melhores células aparecem em combinações específicas 

  - uma tabela para a métrica de share, evidenciando que células com maior mediana de compartilhamentos apareceram e NAO estão concentradas em vídeos (diferente do padrão anterior) 

  - uma tabela para os comentários, mostrando que comments_count dependem principalmente de questões de contexto.
 ```


## Prompt 9 — Checagem crítica de alucinações e inconsistências numéricas

**Objetivo:** registrar uma checagem crítica sobre inconsistências numéricas identificadas em uma resposta anterior da LLM. Nesta etapa, a IA havia gerado tabelas resumidas para apoiar a análise de top performers e bottom performers, mas alguns dados não correspondiam ao dataset original. O objetivo do prompt foi sinalizar o problema, reforçar a necessidade de precisão e rastreabilidade dos dados e estabelecer regras mais rígidas para as próximas etapas da análise.

```text
 Antes de avançarmos para a próxima etapa, preciso registrar um ponto importante sobre as suas respostas anteriores, das tabelas que eu solicitei...comparei os dados do dataset com algumas tabelas resumidas que você gerou para a análise de top performers e bottom performers e identifiquei dados alterados/inconsistentes em relação à base original


 Isso é um problema MUITO serio, porque alucinações ou alterações numéricas em uma análise quantitativa podem comprometer toda a leitura estratégica!

neste desafio, a entrega precisa ser baseada em dados. Por isso, qualquer tabela, número, ranking, mediana ou interpretação quantitativa precisa vir diretamente do dataset e não de aproximações, suposições ou reconstruções livres. Eu já revisei e corrigi manualmente os números que estavam inconsistentes, então não preciso que você refaça essas tabelas agora. Mas preciso que, daqui em diante, você siga estas regras com mais rigor: não invente números, não reordene rankings sem recalcular a partir da base, não preencha lacunas com suposições, não altere valores para tornar a análise mais “coerente”, quando não tiver certeza, diga explicitamente que precisa RECALCULAR, diferencie claramente dado observado, hipótese e interpretação e mantenha todos os números rastreáveis ao dataset. VERIFIQUE! 

Erros desse tipo são prejudiciais porque me obrigam a revisar e refazer manualmente partes da análise, além de reduzirem a confiança no processo. Quero continuar usando a IA como apoio estratégico, mas a análise quantitativa precisa ser verificável. A partir de agora, priorize precisão e rastreabilidade dos dados antes de qualquer conclusão executiva
 ```


## Prompt 10 - Construção da estratégia de conteúdo baseada em dados

**Objetivo:** transformar os achados das análises anteriores em uma estratégia executiva para o time de Social Media. Nesta etapa, a LLM foi orientada a não criar novos números e a usar apenas os aprendizados já discutidos sobre engajamento, patrocínio, formatos, categorias, audiência e creators. O objetivo do prompt foi passar da análise descritiva para recomendações práticas, diferenciando recomendações fortes, hipóteses de teste e pontos de atenção.

```text
Ok, obrigada. agora vamos para a terceira pergunta do head: qual deveria ser a estratégia de conteúdo baseada em dados? 



Não quero que você invente novos números ou gere conclusões sem base Use apenas os achados já discutidos ate aqui: 

- métricas agregadas são muito proximas entre os grupos 

- views não significam necessariamente engajamento forte 

- engagement_rate isolado pode enganar 

- shares e comments_ count indicam tipos diferentes de engajamento 

- formatos text, mixed e image aparecem bem em algumas metricas, então vídeo não deve ser tratado como resposta universal 

- Lifestyle em Video orgânico apareceu bem em algumas células 

- text e mxed apareceram bem para compartilhamento e conversa

 - tech é uma categoria ambígua, com potencial, mas também risco

- hashtags, quando analisadas apenas por presença, não explicam performance -audiência deve funcionar como camada de persona e não como explicação isolada 

- patrocinio não funciona como regra geral 

- patrocínio deve ser decidido por célula de performance, considerando plataforma, categoria, formato e faixa de creator.



 A partir disso, construa uma estratégia de conteúdo executiva para o time de SOCIAL MEDIA 





Organize a resposta em: 



1. Princípio estratégico geral 

- qual deve ser a lógica central da estratégia 

- como o time deve deixar de pensar em “melhor plataforma” ou “melhor formato” e passar a pensar por objetivo de conteúdo 



2. Estratégia por objetivo 

- o que fazer quando o objetivo for alcance 

- o que fazer quando o objetivo for engagement_rate 

- o que fazer quando o objetivo for compartilhamento 

- o que fazer quando o objetivo for comentários/conversa 



3. Estratégia por formato 

- quando usar video 

- quando usar text 

- quando usar mixed 

- quando usar imagem 



4. Estratégia por categoria 

- como tratar beauty 

- como tratar Lifestyle 

- como tratar tech 



5. Estratégia de patrocínio 

- quando patrocinar 

- quando manter orgânico 

- quando evitar ou redesenhar o patrocinio 

- quais critérios usar para decidir se uma célula merece investimento 



6. Estrategia de creators

- como considerar a faixa de seguidores

- por que follower_count não deve ser usado sozinho

- como combinar tamanho do creator com objetivo, formato e plataforma.



7. Estratégia de audiência/persona

- como usar idade, gênero e localização sem transformar isso em explicação isolada

- como pensar personas comportamentais a partir do objetivo: quem assiste, quem compartilha, quem comenta e quem decide



8. O que PARAR de fazer

- práticas que os dados não sustentam

- decisões que parecem arriscadas

- interpretações que devem ser evitadas



9. Quick wins 

- ações práticas que o time poderia testar primeiro 

- priorize ações de baixo risco e alta capacidade de aprendizado 



10. Matriz de decisão 

crie uma matriz simples com as colunas: objetivo, melhor aposta inicial, evitar, métrica principal, métrica de apoio e observação. 



REGRAS IMPORTANTES: - Não crie números novos - Não transforme hipótese em certeza - diferencie recomendação forte, hipotese de teste e ponto de atenção - Use linguagem executiva, clara e objetiva - a resposta precisa ser util para um head tomar decisão em poucos minutos 
 ```



## Prompt 11- Desenvolvimento do prompt para proposta de dashboard interativo


**Objetivo:** construir um prompt completo para solicitar ao Claude o desenvolvimento de uma proposta de dashboard interativo para apoio à decisão em Social Media. Nesta etapa, a ideia inicial foi transformar os achados do relatório em um sistema capaz de simular combinações de post, considerando rede social, formato, status orgânico ou patrocinado, métricas de performance, audiência e creators. O objetivo do prompt foi orientar a criação de uma ferramenta que ajudasse a estimar potencial de desempenho, avaliar chances de engajamento, indicar se vale a pena patrocinar, sugerir creators adequados e recomendar estratégias com base nos padrões identificados na análise.

```text
ótimo, agora quero criar um prompt para que o claude desenvolva um sistema de dashboard. MINHA IDEIA inicial é que o sistema possibilite um "teste" de post, em que a pessoa escollha a rede social, o formato, se vai ser organico ou nao, todas essas metricas que vimos no relatorio, para que consiga ter uma IDEA se aquele post tem chance de ter bons numeros... se sim, quais numeros? quais as chances de engajar? vale a pena patrocinar? existem creators desse nicho que fazem sentido serem contatos? quais estrategias podemos usar baseados nos numeros? desenvolva esse prompt completp

 ```




## Prompt 12- Proposta de dashboard interativo para decisão de conteúdo

**Objetivo:** desenvolver a ideia de um dashboard interativo como diferencial da entrega final do desafio. Nesta etapa, a LLM foi orientada a transformar os achados da análise em uma proposta de sistema capaz de apoiar decisões de Social Media, simulando combinações de plataforma, categoria, formato, status orgânico ou patrocinado, audiência e faixa de creator. O objetivo do prompt foi estruturar uma ferramenta de apoio à decisão que estimasse potencial de performance, indicasse riscos, sugerisse estratégias e ajudasse o time a decidir quando testar, ajustar, patrocinar ou manter um conteúdo orgânico.

```text

 Você deve atuar como um arquiteto de produto, especialista em data analytics, social media strategy, UX e desenvolvimento de dashboards interativos.

Estou participando do AI Master Challenge do G4 e desenvolvi uma análise sobre um dataset com aproximadamente 52 mil posts de social media publicados em plataformas como YouTube, TikTok, Bilibili, Instagram e RedNote.

A análise buscou responder três perguntas principais do Head de Marketing:

1. O que gera engajamento de verdade?
2. Vale a pena patrocinar influenciadores?
3. Qual deveria ser a estratégia de conteúdo baseada em dados?

A partir da análise, identifiquei alguns aprendizados importantes:

* métricas agregadas são muito próximas entre os grupos;
* views não significam necessariamente engajamento forte;
* engagement_rate isolado pode enganar;
* shares e comments_count indicam tipos diferentes de engajamento;
* vídeo não deve ser tratado como resposta universal;
* formatos Text, Mixed e Image aparecem bem em algumas métricas;
* Lifestyle em Video orgânico apareceu bem em algumas células;
* Text e Mixed apareceram bem para compartilhamento e conversa;
* Tech é uma categoria ambígua, com potencial, mas também risco;
* hashtags, quando analisadas apenas por presença, não explicam performance;
* audiência deve funcionar como camada de persona, não como explicação isolada;
* follower_count deve ser usado como variável de controle, não como critério único de escolha;
* patrocínio não funciona como regra geral;
* patrocínio deve ser decidido por célula de performance, considerando plataforma, categoria, formato, faixa de creator e objetivo do conteúdo.

Agora quero desenvolver a ideia de um **dashboard interativo de decisão para social media**, que funcione como uma ferramenta prática para o time de marketing.

## Ideia central do sistema

Quero criar um dashboard em que a pessoa consiga simular ou testar uma ideia de post antes de publicar.

A pessoa deve conseguir escolher variáveis como:

* plataforma;
* categoria;
* tipo de conteúdo;
* status orgânico ou patrocinado;
* faixa de seguidores do creator;
* faixa etária da audiência;
* gênero da audiência;
* localização da audiência;
* presença ou ausência de hashtags;
* objetivo principal do conteúdo.

Com base nessas escolhas, o sistema deve retornar uma leitura estratégica, por exemplo:

* se aquela combinação tem bom potencial de performance;
* quais métricas podem ser esperadas com base em células semelhantes do dataset;
* se o post parece mais forte para alcance, engagement_rate, shares ou comments_count;
* se vale a pena patrocinar ou manter orgânico;
* quais riscos existem naquela combinação;
* quais ajustes podem melhorar a chance de performance;
* quais tipos de creators fazem mais sentido para aquele cenário;
* quais estratégias de conteúdo são recomendadas com base nos dados.

## O que quero que você desenvolva

Desenvolva uma proposta completa para esse sistema de dashboard, como se fosse uma especificação de produto para entrar na entrega final do desafio.

Organize a resposta nas seguintes seções:

1. Nome e conceito do dashboard

Crie um nome profissional para a ferramenta.

Explique em poucas linhas o conceito do dashboard e qual problema ele resolve para o time de Social Media.

2. Objetivo do sistema

Explique para que o dashboard serve.

Ele não deve prometer prever o futuro com certeza, mas sim estimar potencial de performance a partir de padrões históricos do dataset.

Deixe claro que o sistema deve funcionar como apoio à decisão, não como decisão automática.

3. Usuários do dashboard

Descreva quem usaria a ferramenta, por exemplo:

* Head de Marketing;
* Social Media Manager;
* Analista de Conteúdo;
* Analista de Influenciadores;
* time de mídia paga;
* time de planejamento.

Explique o que cada perfil poderia fazer dentro do dashboard.

4. Funcionalidades principais

Desenvolva as principais funcionalidades do sistema, incluindo pelo menos:

1. Simulador de post;
2. Comparador orgânico vs. patrocinado;
3. Recomendador de objetivo;
4. Avaliação de risco da combinação;
5. Sugestão de formato;
6. Sugestão de estratégia de creator;
7. Mapa de oportunidades por célula;
8. Painel de métricas esperadas;
9. Recomendações acionáveis;
10. Histórico de testes e aprendizados.

Para cada funcionalidade, explique:

* o que ela faz;
* quais inputs recebe;
* quais outputs entrega;
* como ajuda na decisão.

5. Simulador de post

Detalhe especialmente o simulador de post.

O usuário deve conseguir preencher campos como:

* plataforma;
* categoria;
* formato;
* orgânico ou patrocinado;
* faixa de creator;
* objetivo do post;
* público-alvo;
* uso de hashtags;
* tipo de conteúdo: tutorial, review, trend, lista, comparação, demonstração, storytelling etc.

Depois disso, o sistema deve devolver:

* score de potencial;
* leitura da célula;
* métrica principal recomendada;
* métricas de apoio;
* estimativa baseada em células semelhantes;
* recomendação de patrocínio;
* alertas de risco;
* sugestões de ajuste criativo;
* recomendação de formato;
* recomendação de creator ou UGC creator;
* próximos testes sugeridos.

6. Modelo de score

Proponha uma lógica de score de performance.

Não precisa criar fórmula matemática complexa, mas precisa ser coerente.

O score pode considerar:

* aderência da combinação ao histórico do dataset;
* tamanho da amostra da célula;
* diferença entre orgânico e patrocinado;
* força do engagement_rate;
* força de shares;
* força de comments_count;
* consistência entre objetivo e métrica principal;
* risco por baixo volume;
* risco de depender de uma única métrica;
* risco de patrocínio em formatos sensíveis;
* adequação entre creator size e objetivo.

Crie uma sugestão de classificação, por exemplo:

* Alto potencial;
* Potencial moderado;
* Testar com cautela;
* Baixa confiança;
* Não recomendado sem ajuste.

Explique o que cada classificação significa.

7. Saídas estratégicas do dashboard

Explique quais respostas o dashboard deve entregar ao usuário.

Exemplos:

* “Essa combinação é melhor para alcance do que para conversa”;
* “Patrocínio não é recomendado nesta célula sem teste prévio”;
* “Formato Mixed pode ser uma alternativa mais segura que Video”;
* “A métrica principal deve ser shares, não views”;
* “Essa célula tem baixa amostra; trate como hipótese”;
* “UGC creators podem ser usados para testar linguagem antes de escalar com creators maiores”.

8. Estratégia de creators e UGC creators

Desenvolva uma seção específica sobre creators.

Explique como o dashboard poderia ajudar a decidir:

* quando usar creators grandes;
* quando testar creators médios ou nichados;
* quando usar UGC creators;
* quando manter conteúdo orgânico sem creator;
* quando patrocinar;
* quando evitar patrocínio.

Explique que UGC creators podem ser úteis para testar mensagens, formatos e linguagem nativa antes de escalar investimento.

9. Estrutura visual do dashboard

Descreva como seria a interface.

Sugira telas ou módulos, por exemplo:

* visão geral;
* simulador de post;
* comparação orgânico vs. patrocinado;
* mapa de células;
* painel de creators;
* recomendações;
* histórico de testes;
* exportação de relatório.

Para cada tela, descreva quais informações aparecem.

10. Métricas exibidas

Liste as métricas que devem aparecer no dashboard, como:

* views;
* likes;
* shares;
* comments_count;
* engagement_rate;
* follower_count;
* content_length;
* tamanho da amostra;
* mediana por célula;
* diferença entre orgânico e patrocinado;
* score de confiança;
* score de potencial;
* recomendação de ação.

Explique como cada métrica deve ser interpretada.

11. Regras de segurança analítica

Inclua regras para evitar interpretações erradas:

* não usar views como única métrica de sucesso;
* não usar engagement_rate isolado;
* não recomendar patrocínio sem comparar com orgânico;
* não recomendar com confiança alta quando a amostra for pequena;
* não transformar hipótese em certeza;
* não recomendar “mais vídeo” como regra geral;
* sempre diferenciar dado observado, hipótese e recomendação.

12. Possível arquitetura simples

Sugira uma arquitetura simples para construir o dashboard.

Pode considerar:

* dataset em CSV;
* processamento em Python ou notebook;
* backend simples em Python;
* frontend em Streamlit, Dash, Retool ou outra ferramenta;
* filtros interativos;
* tabelas e gráficos;
* exportação em PDF ou CSV.

Não preciso de código completo ainda, mas quero uma arquitetura clara e viável para um protótipo.

13. MVP do dashboard

Defina uma versão mínima viável do produto.

Liste o que entra no MVP e o que pode ficar para uma versão futura.

O MVP deve ser viável para apresentar no desafio, mesmo que seja como protótipo conceitual.

14. Exemplo de uso

Crie um exemplo prático de uso do dashboard.

Exemplo:

Uma pessoa quer testar um post de Beauty no Instagram, formato Video, com creator de 50K–100K seguidores, patrocinado, objetivo de comentários ou compartilhamento.

Mostre como o dashboard interpretaria esse cenário e quais recomendações entregaria.

### 15. Texto final para colocar na entrega

Ao final, escreva uma seção pronta para ser usada na minha entrega final, explicando o dashboard como diferencial da solução.

Essa seção deve ter linguagem profissional, objetiva e parecer escrita por uma pessoa, não por IA.

## Regras importantes

* Não invente números específicos que não estejam no dataset.
* Não prometa previsão exata de performance.
* Trate o dashboard como ferramenta de apoio à decisão.
* Diferencie estimativa, hipótese e recomendação.
* Use linguagem clara para um Head de Marketing.
* A proposta deve parecer viável para um desafio de negócios e IA aplicada.
* O foco é transformar a análise em uma ferramenta prática para o time de Social Media.

```
