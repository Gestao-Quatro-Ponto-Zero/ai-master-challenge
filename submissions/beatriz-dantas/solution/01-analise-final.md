# Análise Final - Challenge 004: estratégia social media
por: Beatriz Dantas


## 1. Resumo executivo

Esta análise foi desenvolvida a partir do dataset do Challenge 004 - estratégia social media, composto por um pouco mais de 52 mil posts publicados em múltiplas plataformas como Instagram, YouTube, Bilibili, TikTok e RedNote.

O objetivo central foi responder três perguntas propostas pelo head de marketing:

1. O que gera engajamento de verdade?
2. Vale a pena patrocinar influenciadores?
3. Qual deveria ser a estratégia de conteúdo baseada em dados?

A principal conclusão é que não existe uma resposta universal sobre o que funciona em social media. As métricas agregadas são próximas em muitos casos, views não indicam necessariamente engajamento forte e engagement_rate isolado pode distorcer a leitura de performance. Por isso, a análise considerou diferentes sinais de engajamento, como shares, comments_count, views e engagement_rate, sempre em relação à plataforma, formato, categoria, tamanho do creator, audiência e presença ou ausência de patrocínio.

Os achados indicam que a estratégia deve ser organizada por objetivo de conteúdo. COm muita intencionalidade. Isto é, conteúdos voltados para alcance devem ser avaliados principalmente por views, conteúdos de distribuição, por shares, ao mesmo tempo que conteúdos de conversa, por comments_count; e conteúdos de eficiência relativa, por engagement_rate contextualizado. Também foi observado que formatos como text, mixed e image aparecem bem em algumas métricas, portanto vídeo não deve ser tratado como uma estratégia universal, como se funcionasse em todos os contextos.

Em relação ao patrocínio, a recomendação também é não tratá-lo como regra geral. A decisão deve ser feita por célula de performance, considerando plataforma, categoria, formato e faixa de creator. O investimento só se justifica quando o patrocinado apresenta vantagem clara em relação ao orgânico e quando as métricas de apoio confirmam essa vantagem.

Como complemento, foi desenvolvido um protótipo de dashboard em HTML para apoiar a tomada de decisão do time de social media. A ferramenta organiza os principais aprendizados da análise em uma interface prática, permitindo simular combinações de plataforma, categoria, formato, objetivo de conteúdo, faixa de creator e patrocínio. O dashboard funciona como uma primeira versão operacional para transformar os achados do dataset em rotina de planejamento, priorização e acompanhamento de performance.


## 2. Como a análise foi conduzida

A análise foi conduzida em etapas em prol de evitar conclusões genéricas e/ou baseadas apenas em médias gerais fornecidas pela base de dados. Primeiramente, foi feita uma leitura exploratória do dataset para entender quais variáveis estavam disponíveis, quais plataformas faziam parte da base, quais tipos de conteúdo estavam representados e quais métricas poderiam ser usadas para avaliar performance. 

Depois dessa leitura inicial, foram calculados benchmarks quantitativos para métricas como views, likes, shares, comments_count, follower_count, content_lenght e engagement_rate. Essa etapa mostrou que as métricas agregadas eram muito próximas entre os principais grupos, o que indicou que uma análise geral não seria suficiente para responder às perguntas do desafio.

A partir disso, o estudo passou a funcionar com células de performance, combinando plataforma, categoria, tipo de conteúdo, faixa de creator, status orgânico ou patrocinado e, quando necessário, dados do público. Tal abordagem permitiu comparar contextos mais equivalentes e evitar conclusões distorcidas, como comparar posts de plataformas, formatos ou creators muito diferentes como se fossem iguais.

No mais, também foi realizada a validação humana dos dados. A partir disso, verifiquei que algumas tabelas geradas com apoio da IA ao serem comparadas com a base original demonstraram inconsistências numéricas e estas foram corrigidas manualmente antes de serem incorporadas à análise final. Esse cuidado foi importante para garantir que as conclusões fossem baseadas em dados verificados com o apoio da ferramenta da IA para organização das informações.



## 3. Pergunta 1: O que gera engajamento de verdade?

Na prática: conteúdo que gera engajamento é aquele que performa bem em relação objetivo para o qual foi planejado. Quer likes? Shares? Tudo depende.

Essa leitura também dialoga com uma tendência atual do marketing: a personalização. Em vez de buscar uma fórmula mágica de conteúdo - tal qual uma receita de bolo - a análise sugere que a performance depende da adequação entre mensagem, plataforma, formato, categoria, perfil do creator e comportamento esperado da audiência. Nesse sentido, personalizar não significa apenas trocar linguagem ou segmentar público, mas significa principalmente organizar a produção a partir de objetivos específicos e de combinações de performance observadas nos dados.

A principal conclusão desta etapa é que não existe um único fator capaz de explicar o engajamento. A base não sustenta uma resposta simples como "vídeo performa melhor" ou "TikTok é melhor". As métricas agregadas são muito próximas entre grupos, então a análise precisa considerar combinações específicas. 

Para responder essa pergunta, engajamento foi tratado como um conjunto de dimensões diferentes e não como métrica única. Diante dessa análise, foram considerados quatro tipos de desempenho:

-> alcance, sendo observado a partir das views;
-> engajamento relativo, observado a partir da métrica de engagement_rate;
-> circulação orgânica, observada a partir dos compartilhamentos/shares;
-> conversa, observada a partir de comments_count.

Essa separação foi importante uma vez que cada métrica responde a um questionamento diferente. Um conteúdo pode ter alcance alto, mas não gerar resposta proporcional da audiência. Da mesma forma, um conteúdo pode não ser o mais visto, mas gerar mais compartilhamento ou mais conversa. 



### 3.1 Alcance: views altas não significam engajamento forte

As células com maiores views aparecem em combinações como:

| Plataforma | Categoria | Tipo | Faixa de creator | Status | Posts | Mediana views | ER mediano | Shares | Comments | Leitura |
|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| RedNote | Beauty | Video | 50K-100K | Patrocinado | 53 | 10150 | 19,84% | 298 | 200 | Alto alcance, mas ER abaixo da mediana global |
| RedNote | Tech | Video | 10K-50K | Patrocinado | 30 | 10144 | 19,69% | 299 | 195 | Alto alcance, baixo ER e baixa conversa |
| YouTube | Tech | Mixed | 100K-500K | Patrocinado | 42 | 10138 | 19,82% | 298 | 198,5 | Alto alcance, mas engajamento relativo fraco |
| TikTok | Beauty | Video | 10K-50K | Patrocinado | 40 | 10136,5 | 19,84% | 302 | 192 | Alto alcance e bom share, mas baixa conversa |
| YouTube | Lifestyle | Video | 50K-100K | Orgânico | 62 | 10133 | 19,95% | 298 | 201 | Alto alcance com ER ligeiramente acima da mediana |
| Bilibili | Tech | Video | 50K-100K | Patrocinado | 32 | 10131,5 | 19,80% | 292 | 196,5 | Alto alcance, mas share e conversa baixos |
| YouTube | Tech | Image | 500K+ | Orgânico | 124 | 10131 | 19,93% | 301 | 201 | Alto alcance com métricas equilibradas |
| YouTube | Lifestyle | Mixed | 100K-500K | Patrocinado | 73 | 10130 | 19,90% | 299 | 198 | Alto alcance, mas sem destaque forte em engajamento |


O ponto mais importante é que as células com mais views não são necessariamente as células com melhor engagement_rate, mais compartilhamentos ou mais comentários. Isso nos mostra que o alcance sozinho, pode gerar uma interpretação equivocada e uma leitura incompleta.

Um exemplo relevante de célula é RedNote + Tech + Video + 10k-50k + patrocinado. Ela aparece entre os maiores alcances, mas não aparece como destaque proporcional em outras métricas de engajamento. Isso indica que o conteúdo foi distribuído, mas não necessariamente gerou resposta proporcional da audiência. 


### 3.2 Engagement_rate: os melhores sinais aparecem em combinações específicas

As melhores células de engagement_rate aparecem em combinações como:


| Plataforma | Categoria | Tipo | Faixa creator | Status | Posts | ER | Views | Followers | Shares | Comments | Leitura |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| TikTok | Lifestyle | Video | 10K-50K | Orgânico | 52 | 20,12% | 10094,5 | 31888,5 | 298 | 203,5 | Melhor ER; bom para resposta relativa, não para share |
| Bilibili | Lifestyle | Video | 10K-50K | Orgânico | 53 | 20,06% | 10100 | 30790 | 296 | 204 | Alto ER e boa conversa |
| RedNote | Lifestyle | Text | 100K-500K | Patrocinado | 67 | 20,06% | 10104 | 306440 | 303 | 201 | Text patrocinado com bom ER e share |
| TikTok | Tech | Mixed | 500K+ | Orgânico | 53 | 20,04% | 10094 | 836289 | 303 | 202 | Bom ER em creator grande e formato misto |
| RedNote | Beauty | Text | 100K-500K | Patrocinado | 65 | 20,04% | 10064 | 299473 | 301 | 201 | Text patrocinado aparece bem em Beauty |
| RedNote | Lifestyle | Video | 50K-100K | Patrocinado | 54 | 20,04% | 10096 | 75815 | 300 | 203 | Bom ER com creator médio |
| Bilibili | Lifestyle | Video | 10K-50K | Patrocinado | 56 | 20,03% | 10109 | 28748 | 298,5 | 202 | Bom ER, mas share sem destaque |
| Bilibili | Tech | Video | 50K-100K | Orgânico | 43 | 20,03% | 10085 | 71356 | 297 | 196 | Bom ER, mas conversa baixa |


Essas células indicam sinais importantes sobre como o engagement_rate se comporta quando a análise considera combinações específicas, e não apenas médias gerais. Em TikTok e Bilibili, a presença de Lifestyle em vídeo orgânico sugere que conteúdos mais nativos, menos comerciais e mais próximos da linguagem da plataforma podem gerar boa resposta proporcional da audiência.

A presença de text patrocinado em RedNote, especialmente nas categorias Beauty e Lifestyle, também é relevante porque contraria a leitura mais óbvia de que vídeo sempre seria o formato dominante. Em alguns contextos, formatos textuais podem funcionar melhor por permitirem explicação, recomendação, review ou argumentação, especialmente quando a audiência precisa de mais elementos para interpretar ou compartilhar o conteúdo.

A categoria Tech exige uma leitura mais cuidadosa, porque aparece tanto em algumas células fortes quanto em resultados mais fracos. Esse comportamento indica que Tech não deve ser tratada automaticamente como uma categoria de alta performance, já que seu desempenho parece depender bastante do formato, da plataforma, da clareza da mensagem e da execução criativa.

Ainda assim, as diferenças de engagement_rate não devem ser exageradas. A mediana geral da base fica próxima de 19,90%, enquanto as melhores células ficam pouco acima de 20%. Portanto, os resultados sustentam hipóteses de priorização, mas não regras absolutas.


### 3.3 Compartilhamentos: não estão concentrados apenas em vídeos

Quando a métrica analisada é shares, o padrão se modificou. As células com maior mediana de compartilhamentos apareceram em combinações como:


| Plataforma | Categoria | Tipo | Faixa creator | Status | Posts | Shares | ER | Views | Comments | Leitura |
|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| Bilibili | Beauty | Mixed | 100K-500K | Patrocinado | 69 | 305 | 19,90% | 10100 | 201 | Alto share em formato misto |
| YouTube | Beauty | Text | 100K-500K | Patrocinado | 71 | 305 | 19,95% | 10099 | 200 | Text aparece bem para compartilhamento |
| Instagram | Beauty | Mixed | 100K-500K | Orgânico | 92 | 305 | 19,92% | 10096 | 201,5 | Mixed orgânico com alto share |
| Bilibili | Lifestyle | Image | 500K+ | Patrocinado | 176 | 305 | 19,86% | 10103 | 198 | Image com alto share, mas ER mais baixo |
| RedNote | Tech | Text | 100K-500K | Patrocinado | 35 | 305 | 19,87% | 10105 | 200 | Text com bom share, mas amostra menor |
| RedNote | Lifestyle | Mixed | 100K-500K | Patrocinado | 90 | 305 | 19,97% | 10092 | 199,5 | Mixed com bom share e ER acima da mediana |
| TikTok | Beauty | Text | 500K+ | Patrocinado | 100 | 304,5 | 19,85% | 10109 | 198 | Bom share, mas ER/conversa abaixo da mediana |
| YouTube | Lifestyle | Text | 100K-500K | Orgânico | 95 | 304 | 19,94% | 10116 | 202 | Text orgânico com bom share e conversa |



O achado mais relevante é que mixed, text e image aparecem bem em compartilhamentos, enquanto os vídeos não demonstram tanto domínio dessa métrica. 

Isso sugere que o conteúdo mais compatível provavelmente não seja o mais dinâmico, mas aquele que oferece utilidade, recomendação, comparação ou valor de repasse. Em outras palavras, o compartilhamento parece ser mais ligado ao motivo que a pessoa tem para enviar, salvar ou usar aquele conteúdo como referência. 

Já a categoria beauty aparece com frequência em células de alto share, especialmente quando combinada com formatos mixed e text. Isso pode indicar que conteúdos de beleza funcionam bem quando trazem comparação, recomendação, review, lista ou demonstrações condensadas. 

Para a estratégia, isso significa que, se o objetivo for circulação orgânica, não basta apostar em vídeo. Formatos textuais, mistos e visuais podem gerar mais compartilhamentos em algumas categorias.



### 3.4 Comments_count: conversas dependem de contexto

As células com mais comentários aparecem em combinações como:


| Plataforma | Categoria | Tipo | Faixa creator | Status | Posts | Comments | ER | Views | Shares | Leitura |
|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| Instagram | Tech | Text | 500K+ | Patrocinado | 46 | 204,5 | 19,90% | 10112 | 298 | Tech em Text gera conversa, mas não share |
| Bilibili | Tech | Mixed | 100K-500K | Patrocinado | 31 | 204 | 19,98% | 10102 | 294 | Boa conversa, baixo share |
| YouTube | Beauty | Text | 100K-500K | Orgânico | 91 | 204 | 19,90% | 10110 | 301 | Text orgânico com conversa e share equilibrados |
| Bilibili | Tech | Mixed | 100K-500K | Orgânico | 57 | 204 | 19,85% | 10109 | 297 | Conversa alta, mas ER abaixo da mediana |
| Instagram | Beauty | Video | 10K-50K | Orgânico | 52 | 204 | 19,92% | 10076,5 | 301 | Vídeo orgânico com boa conversa |
| Bilibili | Beauty | Video | 10K-50K | Orgânico | 66 | 204 | 19,96% | 10086 | 302,5 | Boa conversa e bom share |
| Instagram | Beauty | Text | 100K-500K | Orgânico | 86 | 204 | 19,99% | 10086,5 | 302 | Text orgânico com conversa e ER fortes |
| Bilibili | Lifestyle | Video | 10K-50K | Orgânico | 53 | 204 | 20,06% | 10100 | 296 | Alta conversa e alto ER, mas share menor |


O padrão de comentários é diferente do padrão de shares, como vimos. Comentários aparecem com mais força quando o conteúdo abre espaço para opinião, dúvida, explicação, comparação, identificação ou discussão. 

Por isso, text e mixed aparecem bem para conversa, especialmente em tech e beauty. Vídeos orgânicos também aparecem bem em algumas células, principalmente quando combinados com Lifestyle ou Beauty.

Esse ponto é importante porque comentário não deve ser tratado apenas como "mais uma interação", por ele mede de fato a profundidade das interações. Algumas células podem ter bom engagement_rate, mas baixa conversa. Outras podem não liderar em compartilhamento, mas gerar mais discussões proveitosas nos comentários. Isso reforça a necessidade de analisar cada métrica conforme o objetivo da estratégia. 


### 3.5 Hashtags: presença simples não interfere no engajamento

A simples presença de hashtag não alterou de forma relevante as medianas de performance. Posts orgânicos com hashtag e sem hashtag tiveram métricas de engagement_rate muito próximas e o mesmo aconteceu entre os posts patrocinados.

Por isso, a conclusão não deve girar em torno de "hashtag funciona ou não", mas considerar que a presença é fraca quando analisada sozinha.

Para que essa análise gere uma recomendação mais útil, seria necessário avaliar e obervar com mais granularidade aspectos como: quantidade de hashtags, hashtags generalizadas e por categorias, efeito por plataforma e tipo de conteúdo. 


### 3.6 Público: idade, gênero e localização 

Os recortes por audiência não apresentaram diferenças fortes o suficiente para sustentar uma recomendação isolada. Faixa etária, gênero e localização aparecem distribuídos entre top performers e bottom performers, sem um padrão único capaz de explicar o desempenho. 

No dataset, a faixa-etária 19-25 anos aparece com frequência em algumas células de melhor desempenho. Esse grupo pode ser lido como um público jovem-adulto, mais acostumado à linguagem de creators, recomendações, trends e formatos nativos de plataforma.

A faixa 13-18 anos deve ser tratada com cautela, pois representa um público em entrada ou consolidação no uso de redes sociais. Para esse grupo, formatos rápidos, visuais e adaptados à linguagem da plataforma tendem a ser mais coerentes.

Quanto à faixa de 26-35 anos pode ser interpretada como um público mais orientado a utilidade, comparação e decisão. Isso ajuda a explicar por que formatos de text e mixed aparecem bem em algumas células de shares e comments, especialmente em beauty e tech. 

Por sua vez, faixas acima de 35 anos tendem a exigir conteúdos mais claros, explicativos e úteis, com menos dependência de linguagem de trend.

Por fim, a persona, nesta análise deve ser pensada para além de suas características biológicas, mas principalmente por seus hábitos comportamentais: quem consome para se informar, quem compartilha em prol da recomendação, quem comenta para participar da discussão e quem assume uma postura de apenas espectador sem interação.



### 3.7 Conclusão sobre engajamento de verdade 

O que gera engajamento de verdade não é uma plataforma isolada, um formato isolado ou o fato do post ser patrocinado. Vemos que o principal fator é o encaixe entre objetivo, plataforma, formato e contexto do criador.

Para engagement_rate, aparecem células positivas em vídeos orgânicos de Lifestyle nas plataformas TikTok e Bilibili, além de formatos textuais patrocinados no RedNote para Beauty e Lifestyle.

Já quanto ao compartilhamento, os melhores resultados foram em formatos mixed, texto e imagem, principalmente nos nichos de Beauty e Lifestyle.

Para conversas, aparecem em texto e mixed e também em alguns vídeos orgânicos, especialmente em tech, beauty e lifestyle.

Portanto, a principal implicação é que a estratégia de conteúdo precisa ser orientada por objetivo. Conteúdos para alcance, compartilhamento e conversa não devem ser planejados com a mesma lógica.


## 4. Pergunta 2: Vale a pena patrocinar influenciadores?

A análise não sustenta uma resposta binária para a pergunta "vale a pena patrocinar influenciadores?" O patrocínio não apresentou ganho universal, mas também não deve ser descartado. Ele funciona melhor em combinações específicas de plataforma, categoria, tipo de conteúdo e faixa de creator.

Na prática, isso significa que patrocínio não deve ser tratado como uma política ampla de investimento, aplicada da mesma forma para qualquer creator ou qualquer tipo de conteúdo. A decisão precisa ser feita por célula de performance, comparando contextos semelhantes: mesma plataforma, categoria próxima, formato equivalente e faixa de creator comparável.

Por essa razão, a decisão de patrocinar deve deixar de ser tratada como uma política generalizada e ampla, e passar a funcionar como uma decisão por célula de performance. Isto é, testar, manter ou escalar patrocínio apenas quando houver evidência de uplift, de melhora real, em contextos comparáveis. 

### 4.1 O porquê da comparação bruta não ser o suficiente 

A comparação agregada entre posts orgânicos e patrocinados mostrou diferenças muito pequenas. Isso indica que comparar os posts patrocinados contra todos os posts orgânicos de uma vez seria insuficiente para orientar a decisão.

Logo, esse tipo de comparação mistura plataformas, categorias, formatos e creators de tamanhos diferentes. Como resultado, pode gerar uma leitura distorcida sobre a efetividade do patrocínio. 

Para responder à pergunta de forma mais justa, a análise comparou posts orgânicos e patrocinados dentro de células equivalentes.

### 4.2 Como a comparação controlada foi feita 

A comparação entre orgânicos e patrocinados foi feita considerando células formadas por: plataforma, categoria, tipo de conteúdo e faixa de seguidores do creator. 

Foi utilizado um threshold, um limite, mínimo de amostra para evitar conclusões frágeis: 

| Critério | Regra utilizada | Justificativa |
|---|---|---|
| Unidade de comparação | Célula controlada | Evita comparar todos os posts patrocinados contra todos os orgânicos de forma bruta. |
| Variáveis de controle | Plataforma, categoria, tipo de conteúdo e faixa de creator | Permite comparar posts em contextos mais equivalentes. |
| Métrica principal | Mediana de engagement_rate | A mediana reduz o efeito de outliers e é mais estável que a média. |
| Métricas de apoio | Views, shares e comments_count | Ajudam a contextualizar o engagement_rate e evitar leitura isolada. |
| Faixa de creator | 1K–10K, 10K–50K, 50K–100K, 100K–500K e 500K+ | O número de seguidores varia muito e influencia a leitura de performance. |
| Volume mínimo por célula | Pelo menos 30 posts orgânicos e 30 posts patrocinados | Reduz risco de conclusão frágil por amostra pequena. |
| Diferença mínima relevante | Acima de ±0,05 ponto percentual em engagement_rate | Diferenças menores foram tratadas como empate prático. |
| Classificação da célula | Patrocinado melhor, orgânico melhor, diferença irrelevante ou inconclusiva | Facilita a leitura executiva e evita interpretação exagerada. |

Células abaixo do volume mínimo foram classificadas como inconclusivas. Diferenças entre -0,05 p.p e +0,05 p.p foram tratadas como diferença irrelevante ou empate prático. 

### 4.3 Resultado geral das células analisadas

Foram encontradas 299 células possíveis combinando plataforma, categoria, tipo de conteúdo e faixa creator.

| Leitura da célula | Número de células | Interpretação |
|---|---|---|
| Inconclusiva por baixo volume | 162 | Células com menos de 30 posts em pelo menos um dos grupos. Não devem sustentar decisão. |
| Diferença irrelevante / empate prático | 75 | Células em que orgânico e patrocinado tiveram desempenho muito próximo, dentro do intervalo de ±0,05 p.p. em engagement_rate. |
| Patrocinado melhor | 34 | Células em que o patrocinado teve mediana de engagement_rate superior ao orgânico acima do threshold definido. |
| Orgânico melhor | 28 | Células em que o orgânico teve mediana de engagement_rate superior ao patrocinado acima do threshold definido. |

A maior parte das células não permite afirmar que o patrocínio gera uplift transparente. Muitas ficaram inconclusivas por baixo volume ou apresentaram diferença pequena demais para interpretação prática.

Esse resultado indica que patrocínio não funciona como efeito universal e imutável. Ele aparenta depender da combinação entre plataforma, categoria, formato e faixa de creator.

### 4.4 Células em que o patrocinado performou melhor

As células com maior sinal positivo para posts patrocinados apareceram em combinações específicas.

| Plataforma | Categoria | Tipo de conteúdo | Faixa de creator | Posts orgânicos | Posts patrocinados | Diferença em p.p. | Leitura |
|---|---|---|---|---:|---:|---:|---|
| Instagram | Beauty | Video | 50K–100K | 78 | 47 | +0,211 | Patrocinado melhor |
| TikTok | Tech | Image | 100K–500K | 85 | 81 | +0,206 | Patrocinado melhor |
| YouTube | Beauty | Mixed | 500K+ | 114 | 79 | +0,202 | Patrocinado melhor |
| RedNote | Beauty | Video | 10K–50K | 56 | 49 | +0,177 | Patrocinado melhor |
| TikTok | Tech | Text | 100K–500K | 48 | 39 | +0,152 | Patrocinado melhor |
| TikTok | Lifestyle | Image | 100K–500K | 170 | 129 | +0,140 | Patrocinado melhor |
| RedNote | Lifestyle | Video | 50K–100K | 74 | 54 | +0,135 | Patrocinado melhor |
| Bilibili | Tech | Mixed | 100K–500K | 57 | 31 | +0,134 | Patrocinado melhor |
| RedNote | Lifestyle | Text | 100K–500K | 98 | 67 | +0,133 | Patrocinado melhor |
| RedNote | Beauty | Text | 100K–500K | 76 | 65 | +0,131 | Patrocinado melhor |


Os maiores uplifts positivos ficaram em torno de +0,21 ponto percentual de engagement_rate. O ganho é positivo, mas moderado. Por isso, essas células devem ser interpretadas como hipóteses para teste e não como provas definitivas de ROI. 


### 4.5 Células em que o orgânico performou melhor

Também foram identificadas células em que o orgânico superou o patrocinado.

| Plataforma | Categoria | Tipo de conteúdo | Faixa de creator | Posts orgânicos | Posts patrocinados | Diferença em p.p. | Leitura |
|---|---|---|---|---:|---:|---:|---|
| TikTok | Lifestyle | Video | 10K–50K | 52 | 42 | -0,262 | Orgânico melhor |
| Bilibili | Tech | Video | 50K–100K | 43 | 32 | -0,231 | Orgânico melhor |
| Bilibili | Beauty | Video | 50K–100K | 80 | 57 | -0,202 | Orgânico melhor |
| TikTok | Tech | Mixed | 500K+ | 53 | 47 | -0,188 | Orgânico melhor |
| YouTube | Tech | Mixed | 100K–500K | 39 | 42 | -0,153 | Orgânico melhor |
| TikTok | Beauty | Video | 10K–50K | 48 | 40 | -0,146 | Orgânico melhor |
| TikTok | Lifestyle | Text | 100K–500K | 123 | 73 | -0,142 | Orgânico melhor |
| Instagram | Beauty | Text | 500K+ | 122 | 98 | -0,128 | Orgânico melhor |
| YouTube | Beauty | Video | 10K–50K | 42 | 50 | -0,123 | Orgânico melhor |
| Bilibili | Lifestyle | Text | 500K+ | 115 | 86 | -0,120 | Orgânico melhor |

A maior queda observada ficou em torno de -0,26 ponto percentual de engagement_rate. Assim como nos casos positivos, a diferença é moderada, mas suficiente para indicar que o patrocínio pode reduzir eficiência em alguns contextos. 


### 4.6 Padrões que favorecem o patrocínio 

A análise das células positivas mostrou certos padrões iniciais:

-> RedNote e Instagram aparecem com mais frequência entre as células em que o patrocínio performou melhor;
-> Tech foi a categoria com maior número de células positivas, embora também tenha aparecido em células negativas;
-> as evidências mais úteis apareceram principalmente em creators acima de 100k de seguidores.

### 4.7 Padrões que favorecem o orgânico

As células em que o orgânico performou melhor indicam outros padrões importantes a serem destacados:

-> TikTok e Youtube apareceram com mais frequência entre células negativas para patrocínio;
-> o formato "vídeo" concentrou mais casos em que o orgânico venceu o patrocinado, devido ao potencial de viralização;
-> categorias como Tech e Beauty apareceram tanto em células positivas quanto negativas;
-> creators grandes aparecem também tanto em células positivas quanto negativas, logo, tamanho de audiência não deve ser visto como critério isolado para avaliação de resultado.

O achado mais importante é que vídeos patrocinados aparecem mais sensíveis à execução criativa. Em plataformas como TikTok e YouTube, o conteúdo patrocinado pode perder eficiência quando não aparece nativo ou bem integrado à linguagem da plataforma. 

### 4.8 Sponsor category, disclosure e hashtags

Sponsor_category, disclosure_type e presença simples de hashtags não explicaram fortemente a diferença entre orgânico e patrocinado nesta etapa da análise. 

As categorias de patrocinados aparecem distribuídas de forma relativamente parecida entre células positivas, negativas e neutras. Disclosure explícito e implícito também diveram diferenças pequenas. A presença de hashtags foi alta tanto em posts orgânicos quanto patrocinados, mas não explicou o uplift de patrocínio. 

Essas variáveis ainda podem ser úteis, mas precisam ser avaliadas com maior grau de critérios, considerando principalmente o tipo de hashtag, o número de hashtags, a plataforma, o formato e a categoria.


### 4.9 Conclusão sobre patrocínio 

O patrocínio não deve ser utilizado como bloco único, comprado de uma vez. A análise não sustenta uma política ampla e generalizada de patrocínio em influenciadores. Por sua vez, também não sustenta abandonar completamente a estratégia. O resultado aponta para uma política vista como intermediária: testar e escalar apenas células com evidência positiva, manter orgânico em células neutras e evitar redesenhar ou evitar investimentos patrocinados em contextos em que o orgânico performa melhor. 


## 5. Pergunta 3: Qual estratégia de conteúdo os dados sugerem?

A estratégia de conteúdo baseada em dados deve partir principalmente do OBJETIVO que cada conteúdo precisa cumprir. 

A análise demonstrou que o engajamento não é métrica isolada... views, engagement_rate, shares e comments_count representam comportamentos diferentes da audiência. Por essa razão, a estratégia precisa organizar o conteúdo por FUNÇÃO: distribuir, gerar respostas proporcionais, estimular a circulação ou até mesmo iniciar um debate.

A lógica central é deixar de tomar decisões por média gerais e passar a trabalhar por células de performance, considerando principalmente: plataforma, categoria, formato, faixa de creator, status orgânico ou patrocinado e o objetivo do conteúdo.

A questão é: qual combinação de formato, plataforma, categoria e creator tem maior chance de gerar o comportamento esperado?

### 5.1 Estratégia por objetivo 

Quando o objetivo for alcance, a métrica principal deve ser views, mas ela não pode ser interpretada sozinha. Views indicam distribuição, não necessariamente qualidade do engajamento. Por isso, conteúdos de alcance devem ser avaliados junto com engagement_rate, shares e comments_count.

Quando o objetivo for engagement_rate, a prioridade deve ser eficiência relativa. Nesse caso, o time deve observar quais conteúdos geram mais interações em relação ao volume de visualizações. Ainda assim, engagement_rate precisa ser lido com contexto, porque pode parecer alto em células menores ou com menor alcance.

Quando o objetivo for compartilhamento, a métrica principal deve ser shares. A análise mostrou que compartilhamento não está concentrado apenas em vídeos. Formatos Text, Mixed e Image também apareceram bem em algumas células, especialmente quando o conteúdo tem valor de utilidade, recomendação, comparação ou repasse.

Quando o objetivo for conversa, a métrica principal deve ser comments_count. Comentários indicam profundidade e dependem mais do contexto do conteúdo do que do formato isolado. Conteúdos que abrem espaço para dúvida, opinião, comparação, identificação ou debate tendem a ser mais coerentes para esse objetivo.

### 5.2 Estratégia por formato

O formato video deve ser usado quando o objetivo for gerar presença, identificação, demonstração ou narrativa curta. Ele continua importante, mas não deve ser tratado como resposta universal. A análise mostrou que vídeos orgânicos de lifestyle apareceram bem em algumas células, enquanto vídeos patrocinados podem perder eficiência quando parecem pouco nativos ou excessivamente publicitários.

O formato text deve ser usado quando o valor do conteúdo está na explicação, recomendação, comparação, síntese ou argumentação. Esse formato apareceu bem em algumas células de compartilhamento e conversa, o que indica potencial para conteúdos de utilidade e decisão.

O formato mixed deve ser tratado como formato estratégico, não secundário. Ele pode funcionar bem quando o conteúdo precisa combinar clareza visual com explicação, como listas, comparações, tutoriais, rankings, reviews ou conteúdos que precisam ser facilmente compartilháveis.

O formato Image pode ser útil quando o objetivo for comunicar uma ideia simples, gerar compartilhamento, destacar benefício claro ou criar peças salváveis. Ele deve ser pensado menos como peça estética isolada e mais como conteúdo com valor de consulta ou repasse.


### 5.3 Estratégia por categoria

A categoria beauty deve ser tratada como uma categoria com potencial para compartilhamento e conversa, especialmente quando o conteúdo envolve comparação, recomendação, review, escolha, resultado ou opinião. A estratégia não deve limitar Beauty a vídeo, porque Text, Mixed e Image também apareceram com sinais relevantes.

A categoria Lifestyle parece funcionar melhor quando o conteúdo mantém naturalidade e linguagem nativa da plataforma. Os sinais positivos em Video orgânico sugerem que essa categoria pode ser boa para identificação, rotina, proximidade e resposta proporcional.

A categoria Tech exige mais cuidado. Ela apareceu tanto em células fortes quanto em células fracas, o que indica potencial, mas também risco. Tech não deve ser escalada automaticamente. O conteúdo precisa ser claro, bem contextualizado e adequado ao formato. Text e Mixed podem ser bons caminhos quando o objetivo for explicar, comparar ou gerar conversa. 

### 5.4 Estratégia por patrocínio 

Patrocínio deve ser decidido por célula de performance, não por média geral.

Uma célula patrocinada merece investimento quando existe coerência entre plataforma, categoria, formato, faixa de creator e objetivo da campanha. Também precisa haver volume suficiente para análise, desempenho superior ou estável em relação ao orgânico e compatibilidade entre a métrica principal e o objetivo do conteúdo.

O time deve manter orgânico quando o formato depende de naturalidade, quando a célula orgânica já performa bem ou quando o patrocínio pode reduzir a percepção de autenticidade.

O patrocínio deve ser evitado ou redesenhado quando há views, mas pouca resposta proporcional; quando o formato patrocinado parece pouco nativo; quando vídeo patrocinado perde eficiência; ou quando a comparação controlada mostra vantagem para o orgânico.

Em termos práticos, patrocínio pode ampliar exposição, mas não garante qualidade de engajamento. Por isso, ele deve ser tratado como teste controlado, não como solução automática.


### 5.5 Estratégia de creators 

A métrica follower_count precisa ser usada como camada de controle e não apenas como critério único de escolha. Creators maiores podem ajudar em alcance, mas não necessariamente entregam engajamento proporcional, compartilhamento ou conversas. Creators menores ou médios podem apresentar boa resposta relativa, mas precisam de volume suficiente para validar o padrão. 

A escolha de creators deve combinar: objetivo do conteúdo, plataforma, categoria, formato, faixa de seguidores, métrica principal e tipo de engajamento esperado. 

Para alcance, creators maiores podem ser úteis, desde que o desempenho seja acompanhado por outras métricas. Para engagement_rate, creators médios ou nichados podem ser testados. Já para compartilhamentos, faz sentido priorizar criadores capazes de entregar conteúdo útil, recomendável ou salvável. 

Além da seleção tradicional de influenciadores, uma frente estratégica é testar os chamados UGC creators. Nesse caso, o foco não é apenas o tamanho da audiência, mas a capacidade de produzir conteúdos com aparência nativa, linguagem cotidiana e maior proximidade com o uso real do produto ou tema. 

Tal abordagem faz sentido porque a análise demonstrou que formatos muito comerciais ou pouco nativos podem perder eficiência, especialmente em vídeos patrocinados. UGC creators podem ajudar a reduzir esse risco, criando conteúdos que funcionem mais como recomendação, demonstração, review ou relato de experiência do que como uma simples peça publicitária tradicional. 


### 5.6 Estratégia de público e persona

Idade, gênero e localização não devem ser tratados como explicações isoladas de performance. Esses dados funcionam melhor como camada de persona e ajuste de mensagem. 

A estratégia deve pensar na audiência de forma COMPORTAMENTAL. 

| Persona comportamental | Comportamento esperado | Métrica principal |
|---|---|---|
| Quem assiste | Consome e gera distribuição | Views |
| Quem engaja | Interage proporcionalmente | Engagement_rate |
| Quem compartilha | Repassa valor para outras pessoas | Shares |
| Quem comenta | Responde, debate ou pergunta | Comments_count |
| Quem decide | Pode converter ou influenciar compra | Conversão, clique ou métrica de negócio |

Tal perspectiva é mais útil do que assumir simplesmente que uma faixa etária, gênero ou país explica por si só o desempenho. O dado demográfico ajuda a ajustar a linguagem e o contexto, mas a decisão estratégica deve vir do cruzamento entre público, formato, plataforma, categoria e objetivo.


### 5.7 O que PARAR de fazer

A análise indica algumas práticas que o time deve evitar:

1- Tratar vídeo como resposta universal
Esse formato continua relevante, mas text, mixed e imagem também aparecem como métricas importantes.

2- Usar views como sinônimo de sucesso
Elas medem distribuição, mas não o engajamento real.

3- Usar engagement_rate como critério isolado 
Essa métrica precisa ser lida juntamente às views, follower_count, shares, comments_count e também o tamanho da amostra.

4- Decidir patrocínio generalizado
Os conteúdos patrocinados não funcionam com regras gerais e deve ser avaliados por célula. 

5- Usar hashtag sem estratégia
A presença aleatória de hashtags não explicou performance. O próximo passo seria analisar o tipo, função e contexto do uso delas.

6- Escalar tech sem validação
A categoria tem potencial, mas também apresenta risco, então precisa de testes mais controlados antes de receber investimento maior. 

### 5.8 Quick wins

Um primeiro quick win é separar o calendário editorial por objetivo, isto é: cada post deve nascer com uma função principal: alcance, engagement_rate, compartilhamento, conversa ou conversão.

Em segundo lugar, é interessante testar text e mixed para conteúdos de utilidade, como listas, comparações, recomendações, reviews e explicações. 

O terceiro é testar vídeos orgânicos de lifestyle quando o objetivo for identificação e resposta proporcional, pois como vimos, tendem a funcionar para esses casos. 

O quarto é revisar vídeos patrocinados antes de escalar investimento, avaliando se o conteúdo está nativo, claro e adequado à plataforma. Além disso, é interessante também priorizar o patrocínio de conteúdos que tenham apresentado bons números quando testados organicamente.

Em quinto lugar, criar um score simples de decisão por célula antes de patrocinar. Esse score pode considerar objetivo, histórico de célula, plataforma, categoria, formato, faixa de creator, métrica principal, métrica de apoio, volume da amostra e risco de interpretação.

Por fim, o sexto é qualificar as melhores hashtags, em prol de SEO. Em vez de medir apenas presença ou ausência, o time pode separar as tags de marca, campanha, categoria, busca e até mesmo as genéricas. 

### 5.9 Matriz de decisão 


| Objetivo | Melhor aposta inicial | Evitar | Métrica principal | Métrica de apoio | Observação |
|---|---|---|---|---|---|
| Alcance | Conteúdos com potencial de distribuição por plataforma e creator | Usar views como única prova de sucesso | Views | ER, shares e comments | Alcance mede distribuição, não engajamento real |
| Engagement_rate | Combinações com bom encaixe entre formato, categoria e plataforma | Avaliar ER sem views e follower_count | Engagement_rate | Views e tamanho da amostra | ER alto precisa ser contextualizado |
| Compartilhamento | Text, Mixed e Image com valor de utilidade ou repasse | Assumir que vídeo sempre compartilha mais | Shares | ER e views | Shares indicam circulação ativa |
| Conversa | Text, Mixed e vídeos orgânicos com abertura para opinião | Conteúdo apenas expositivo | Comments_count | ER e qualidade dos comentários | Comentário mede profundidade e contexto |
| Patrocínio | Células com histórico favorável e objetivo claro | Patrocinar por média geral ou por creator isolado | Métrica do objetivo | Shares, comments e views | Patrocínio deve ser decidido por célula |
| Creators | Combinar faixa de seguidores com objetivo e formato | Escolher apenas por follower_count | Métrica do objetivo | Follower_count e amostra | Tamanho do creator é controle, não resposta |
| Audiência | Usar idade, gênero e localização como camada de persona | Tratar demografia como causa isolada | Métrica do objetivo | Segmento e comportamento | Persona deve considerar comportamento, não só perfil |
| Tech | Testar com controle criativo e formato adequado | Escalar sem validação | ER, shares ou comments | Views e amostra | Categoria com potencial e risco |
| Beauty | Testar Text, Mixed e Image para recomendação e comparação | Reduzir categoria a vídeo | Shares e comments | ER | Pode funcionar bem quando gera utilidade ou opinião |
| Lifestyle | Testar Video orgânico para identificação | Transformar todo Lifestyle em patrocinado | ER | Comments e views | Funciona melhor quando parece nativo |


### 5.10 Conclusão sobre estratégia 

A estratégia de conteúdo necessita sair da lógica de melhor formato ou melhor plataforma, para operar por objetivos específicos de engajamento. Se o objetivo é alcance, views devem ser acompanhadas de outras métricas, assim como se o objetivo for a circulação, formatos com valor de compartilhamento como text e image devem ser testados. Por sua vez, se o intuito principal é iniciar uma conversa, propor um debate, o conteúdo precisa abrir esse espaço para opinião, dúvida, comparação e até mesmo identificação.

Os vídeos permanecem como formatos importantes, mas não os mais eficazes em todos os casos. Patrocínio também pode funcionar, mas em células específicas. Hashtags e audiência demográfica devem ser usadas como camadas de análise, não como apenas explicações isoladas.

Portanto, a decisão prática do time é que cada conteúdo deve nascer de um bom brainstorm, com um objetivo claro, uma célula de performance esperada e uma meta de métrica principal a ser atingida e avaliada. 


## 6. O que não funciona

A análise indica que o baixo desempenho não está concentrado em uma única plataforma, categoria ou formato, mas aparece principalmente quando a estratégia trata uma variável isolada como resposta suficiente. Esse tipo de leitura leva a decisões frágeis, como usar vídeo apenas porque “vídeo engaja”, patrocinar influenciadores apenas porque “influenciador dá resultado” ou medir sucesso somente pelo volume de views.

Quando o alcance é usado como sinônimo de sucesso, a avaliação de performance se torna incompleta. Algumas células com alto número de views não apresentaram engagement_rate, shares ou comments_count fortes, o que mostra que um conteúdo pode ser bem distribuído sem gerar resposta proporcional da audiência. Por isso, views devem ser usadas como métrica de distribuição, mas não como prova final de engajamento.

Logo, ao tratar vídeo como formato universal, a estratégia também corre o risco de ignorar diferenças importantes entre contexto, plataforma e intenção de conteúdo. O formato apareceu bem em alguns cenários, especialmente em conteúdos orgânicos de Lifestyle, mas também esteve presente entre células de baixo desempenho, principalmente quando patrocinado. Isso indica que vídeo precisa ser avaliado pela linguagem da plataforma, pelo objetivo do conteúdo e pelo nível de naturalidade da execução.

Quando a decisão de patrocínio é tomada a partir de médias agregadas, o investimento tende a perder precisão. A análise de orgânico vs. patrocinado mostrou que o patrocínio não funciona como regra geral, já que em algumas células o patrocinado performou melhor, enquanto em outras o orgânico teve vantagem. Dessa forma, aumentar investimento em influenciadores sem considerar plataforma, categoria, formato e faixa de creator pode gerar desperdício.

Ao usar engagement_rate de forma isolada, a análise também pode produzir uma leitura distorcida sobre o desempenho real do conteúdo. Embora seja uma métrica importante para avaliar eficiência relativa, ela precisa ser contextualizada com views, follower_count, shares, comments_count e tamanho da amostra. Um ER alto pode indicar boa eficiência proporcional, mas não necessariamente escala, circulação orgânica ou profundidade de interação.

Quando hashtags são tratadas como solução genérica, a recomendação também perde força analítica. A presença simples de hashtags não explicou diferenças relevantes de performance, o que não significa que hashtags sejam inúteis. O ponto é que a análise precisa considerar tipo, função e contexto de uso, observando se as hashtags são de marca, campanha, categoria, busca ou apenas termos genéricos.

No caso da categoria Tech, o principal cuidado é evitar uma leitura automática de alto potencial. A categoria apareceu tanto em células fortes quanto fracas, o que sugere oportunidade, mas também risco. Conteúdos de Tech pouco explicativos, pouco nativos ou desalinhados ao formato da plataforma podem perder eficiência rapidamente.

De modo geral, o que não funciona é tomar decisões com base em atalhos... A estratégia não deve partir de “mais vídeo”, “mais patrocínio”, “mais hashtags” ou “mais creators grandes”, mas da definição do objetivo do conteúdo, da escolha da célula de performance mais coerente e da avaliação do resultado pela métrica certa.


## 7. Limitações da análise

Como o dataset permite avaliar performance de conteúdo, mas não traz informações financeiras ou comerciais completas, está análise consegue apontar contextos em que determinados formatos, plataformas, categosias e estratégias parecem performar melhor ou pior, mas não permite afirmar o retorno financeiro (ROI) de forma mais eficaz. As métricas disponíveis ajudam a entender o comportamento de social media, porém não substituem dados de custo, conversão ou receita, principalmente quando falamos de conteúdos patrocinados.

No caso do patrocínio, essa limitação é especialmente importante, já que a base não informa fee pago a creators, investimento em mídia, CPM, CPC, CPE ou qualquer outro indicador de custo. Com isso, foi possível observar sinais de desempenho em termos de engajamento, mas não calcular se determinada campanha, creator ou célula patrocinada teria retorno financeiro suficiente para justificar o investimento.

Além dos dados financeiros, a ausência de métricas de conversão também limita a leitura estratégica. O dataset não inclui cliques, vendas, leads, cadastros, receita ou retenção, o que faz com que as recomendações fiquem concentradas em performance de conteúdo, e não em impacto comercial direto. Um post pode gerar alcance, compartilhamento ou conversa, mas, com os dados disponíveis, não é possível afirmar se ele gerou resultado de negócio.

A própria leitura de engagement_rate também exigiu cuidado, porque essa métrica ajuda a observar eficiência relativa, mas não deve ser tratada como medida absoluta de sucesso. Por isso, ao longo da análise, ela foi cruzada com views, shares, comments_count, follower_count e tamanho da amostra, evitando que uma taxa aparentemente positiva fosse interpretada fora de contexto.

Mesmo com uma base de pouco mais de 52 mil posts, alguns cruzamentos ficaram com baixo volume quando combinei plataforma, categoria, formato, faixa de creator, audiência e status de patrocínio. Nessas situações, os resultados foram tratados como hipóteses ou pontos de atenção, e não como conclusões definitivas, porque uma célula pequena pode apontar um caminho interessante, mas ainda não sustenta uma recomendação forte sozinha.

A análise de hashtags também tem uma limitação importante, já que, em algumas etapas, foi possível observar apenas presença ou ausência de hashtags. Esse recorte não mostra o tipo de hashtag utilizada, sua função, sua relação com marca, campanha, categoria ou busca. Para uma recomendação mais precisa, seria necessário separar hashtags de marca, campanha, categoria, busca e termos genéricos, além de observar o efeito disso por plataforma e formato.

Os dados de audiência, como idade, gênero e localização, também precisam ser interpretados como camadas de contexto, e não como explicações isoladas de performance. Essas informações ajudam a pensar persona, linguagem e contexto cultural, mas perdem força analítica quando são cruzadas com muitas outras variáveis ao mesmo tempo, já que a amostra fica mais fragmentada.

Para além das limitações do dataset, também reconheço limitações do próprio processo de entrega. Gostaria de ter tido mais tempo para aprofundar algumas análises, registrar mais etapas em vídeo e aprimorar o dashboard, principalmente com mais interações, visualizações comparativas, trilhas de decisão e integração direta com a base de dados. Ainda assim, o protótipo já ajuda a materializar a proposta de transformar a análise em uma ferramenta de apoio à decisão.

O uso de IA também exigiu validação constante. A LLM foi útil para acelerar análises, organizar hipóteses, estruturar tabelas e apoiar a escrita, mas algumas respostas precisaram ser verificadas manualmente. Em uma etapa, identifiquei inconsistências numéricas em tabelas geradas com apoio da IA e corrigi esses dados antes de incorporá-los à análise final.

Apesar disso, não enxergo a revisão humana apenas como uma limitação, mas como parte essencial do método! A IA ajudou a acelerar o processo, mas a checagem, a interpretação e a decisão final continuaram sendo humanas. Por isso, as conclusões deste relatório devem ser lidas como base para priorização e desenho de testes, não como regras definitivas. O ideal é usar esses achados para orientar decisões iniciais, validar hipóteses em novas campanhas e acompanhar os resultados com métricas de negócio, custo e conversão.


## 8. Principais aprendizados para decisão 

A análise mostrou que a estratégia de social media deve sair de uma lógica genérica, baseada em fórmulas prontas, e passar a operar intecionalmente a partir do objetivo de cada conteúdo. O principal aprendizado é que nenhuma plataforma, categoria ou formato explica o engajamento sozinho. O resultado depende da combinação entre contexto, linguagem, tipo de conteúdo, perfil do criador e comportamente esperado da audiência.

Um dos pontos mais importantes é que as views não significam necessariamente um engajamento dote. O alcance continua sendo métrica importante para entender distribuição, mas precisa ser lido junto com métricas como engagement_rate, compartilhamentos e comentários, já que o conteúdo pode chegar a muitas pessoas e ainda assim gerar pouca resposta, gerar um retorno desproporcional.

O mesmo cuidado vale para a métrica de engagement_rate, visto que é um marcador útil para avaliar eficiência relativa, mas não deve ser usada de forma isolada, porque vira uma informação realmente estratégica quando é cruzada com viwes, followe_count, tamanho da amostra, shares e comentários. Sem essa contextualização, existe o risco de interpretar como sucesso uma performance que pode ser pequena, pouco escalável ou até mesmo pouco relevante para o objetivo do conteúdo.

Outro aprendizado importante é que vídeo não pode ser tratado como resposta universal. O formato apareceu bem em alguns contextos, especialmente em conteúdos orgânicos de Lifestyle, mas Text, Mixed e Image também apresentaram sinais relevantes para compartilhamento e conversa. Isso reforça que a escolha do formato precisa partir do que o conteúdo pretende gerar, e não de uma regra fixa sobre o que “engaja mais”.

Também ficou claro que shares e comments_count representam comportamentos diferentes da audiência. Compartilhamento indica circulação ativa, utilidade e valor de repasse, enquanto comentário indica profundidade, dúvida, opinião, identificação ou abertura para conversa. Por isso, um conteúdo pensado para ser compartilhado não necessariamente deve ser planejado da mesma forma que um conteúdo pensado para gerar debate ou participação nos comentários.

No caso do patrocínio, o aprendizado central é que ele não funciona como regra geral. A comparação entre orgânico e patrocinado mostrou células em que o patrocinado performa melhor, células em que o orgânico tem vantagem e muitos casos em que a diferença é irrelevante ou inconclusiva. Por isso, a decisão de patrocinar precisa ser feita por célula de performance, considerando plataforma, categoria, formato, faixa de creator e objetivo do conteúdo.

A análise também mostra que follower_count não deve ser o principal critério para escolha de creators. Creators maiores podem ajudar em alcance, mas não garantem maior engajamento proporcional, compartilhamento ou conversa. A escolha precisa considerar o tipo de resposta que se espera da audiência e o papel que aquele creator pode cumprir dentro da estratégia.

Em relação à audiência, idade, gênero e localização funcionam melhor como camada de persona do que como explicação isolada de performance. Esses dados ajudam a ajustar linguagem, formato e contexto cultural, mas não explicam sozinhos por que um conteúdo performa melhor. Para esta estratégia, a leitura mais útil de persona é comportamental: quem assiste, quem engaja, quem compartilha, quem comenta e quem pode avançar para uma decisão.

As hashtags também não devem ser tratadas como solução genérica. A presença simples de hashtags não explicou diferenças relevantes de performance, então uma recomendação mais forte exigiria analisar tipo, função e contexto de uso, separando, por exemplo, hashtags de marca, campanha, categoria, busca e termos genéricos.

Em termos práticos, o principal aprendizado para o time é que cada conteúdo deve nascer com três definições claras: objetivo principal, célula de performance esperada e métrica principal de avaliação. Isso permite planejar melhor, medir com mais precisão e evitar decisões baseadas em atalhos e achismos.



