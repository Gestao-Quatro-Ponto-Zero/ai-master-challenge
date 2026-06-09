# Submissão — Beatriz Dantas — Challenge 004

## Sobre mim

- **Nome:** Beatriz Dantas
- **LinkedIn:** https://www.linkedin.com/in/beatrizdantasbr/
- **Challenge escolhido:**  004 - Social Media
---

## Executive Summary

Oie! (: Primeiramente gostaria de dizer que eu me diverti bastante com o desafio! Nessa entrega, analisei, juntamente a uma LLM, um dataset com aproximadamente 52 mil posts de social media para responder três perguntas do head de marketing.

Minha principal conclusão é que a estratégia não deve ser baseada em médias gerais, nem em regras generalizadas... Os dados indicam que a decisão deve ser tomada por células de performance e em prol de objetivos específicos. Com intencionalidade.  

Como diferencial, desenvolvi também um protótipo de sistema, uma dashboard em HTML para testes baseados nas métricas e com auxílio de IA, em prol de apoiar as decisões de social media antes da publicação de um post. 

---

## Solução

A solução está organizada em duas frentes principais:

-> [Análise final](solution/01-analise-final.md)
-> [Protótipo em HTML do dashboard](solution/dashboard/index.html)


### Abordagem

Iniciei com uma leitura exploratória e um [brainstorm do dataset](process-log/brainstorm-inicial.md) para entender as variáveis disponíveis, as plataformas, os tipos de conteúdo, os dados do público e as métricas de performance. 

Em seguida avancei para benchmarks quantitativos e cruzamentos por células de performance, considerando os critérios fornecidos.

Por fim, a análise também incluiu uma cuidadosa, criteriosa e demorada etapa de validação humana dos dados. Algumas tabelas geradas com apoio da LLM demonstraram inconsistências e foram corrigidas manualmente antes de entrarem na análise final. 



### Resultados / Findings

-> As médias gerais escondem detalhes importantes, por isso uma análise em células de performance é mais eficaz;

-> Views indicam mais distribuição do que de fato o engajamento real, não deve ser encarada como a métrica que prova o sucesso de um determinado post, ela é mais para topo de funil;

-> Engagement_rate tem sua utilidade, mas pode ser tendencioso se analisado sozinho, deve ser visto com outras métricas para evitar conclusões distorcidas;

-> Os vídeos não são sempre a melhor opção para o engajamento, não é universal e outros formatos também apresentaram bons resultados;
-> Compartilhamentos e comentários representam comportamentos de públicos bem divergentes, por isso devem ser priorizados em estratégias individualizadas e específicas;

-> Patrocínio não funciona como regra geral, isto é, conteúdos orgânicos podem se destacar até mais quando a estratégia está bem pensada e direcionada;

-> Hashtags não demonstraram grande influência nos resultados, isso demonstra que isoladamente não deve ser avaliada como critério para engajamento;

-> A estratégia final, por sua vez, deve operar por objetivo de conteúdo. Isso quer dizer que cada post deve nascer com uma intencionalidade clara e a métrica principal deve ser observada a partir desse objetivo;

-> E claro, a certeza: IAs alucinam, verificar é imprescindível!



### Recomendações

Diante da era da personalização em que já vivemos no universo do marketing, minha principal recomendação é que a empresa não planeje conteúdos a partir de regras genéricas como "postar reels no instagram faz o conteúdo performar mais"... Os dados indicam que a estratégia deve ser organizada por objetivo, este individualizado para cada conteúdo, e por células de performance. 

Para além das recomendações específicas presentes na análise final, gostaria de destacar em especial a estratégia de implementar o teste de UGC creators. Essa tática pode ser interessante porque é uma grande tendência e também porque a análise mostrou que conteúdos pouco nativos tendem a perder eficiência. Esses criadores ajudam a aproximar a comunicação de uma lógica mais cotidiana e isso pode contribuir diretamente para a redução do risco de investir alto em uma campanha sem antes entender qual narrativa funciona adequadamente para aquele caso.

Por fim, recomendo fortemente o uso da dashboard como ferramenta de apoio à decisão para simular ideias de posts, avaliar possíveis riscos e orientar quando testar, ajustar, patrocinar ou manter orgânico. A plataforma ajuda a poupar tempo do time, que muitas das vezes se dedica a campanhas, pautas e projetos que podem não performar bem. Com uma camada de análise preditiva baseada no histórico do dataset, o time consegue ter uma ideia inicial do potencial de cada combinação antes de investir mais tempo, esforço criativo ou budget. O dashboard não elimina a necessidade dos testes, mas reduz decisões baseadas em achismos e direciona melhor quais ideias merecem ser priorizadas, ajustadas ou descartadas. 


### Limitações

Gostaria de ter recebido mais métricas financeiras, para que a análise pudesse calcular o ROI, principalmente visando o investimento em conteúdos patrocinados. 

Embora a base tenha mais de 52 mil posts, algumas categorias demonstraram baixo volume de amostra, com isso alguns resultados foram tratados como hipóteses ou pontos de atenção, mas não como de fato conclusões definitivas. 

Outro ponto, foi o tempo... para além da prática em si do desafio, eu gostaria de ter registrado mais etapas em vídeo, como fiz no brainstorm inicial e na primeira leitura do dataset e ter registrado nesse formato dentro do process log. Isso porque eu acredito que essa prática evidencia melhor meu raciocínio, minha identidade também como produtora de conteúdo e as mudanças de direção durante a análise (em outras palavras: consigo transmitir melhor as vozes da minha cabeça estão dizendo hehe).

Além disso, gostaria de ter tido mais tempo para aprimorar o dashboard, principalmente adicionando mais interações, trilhas gamificadas, um agente de IA para apoio nas dúvidas, visualizações comparativas e visuais com gráficos e com toda certeza uma integração mais direta com os dados do dataset. 

Por fim, a IA exigiu revisão humana da minha parte, mas não enxergo isso exatamente como uma limitação. Como IA master, esse processo reforçou um ponto muito importante da entrega: a LLM foi usada como apoio para acelerar a análise, organizar dados e hipóteses, mas não como fonte final sem validação. A checagem humana foi parte essencial do método e ajudou a tornar todo o processo mais criterioso, consciente, intencional e confiável.


---

## Process Log — Como usei IA

Eu iniciei registrando os processos com gravações no meu ipad e também setorizei todas as screenshots dos prompts utilizados, esses registros podem ser encontrados [aqui](process-log)


### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Chat GPT | _Apoio na organização e na decomposição dos dados, auxílio na formatação das tabelas, refinamento de prompts, revisão de coerência/coesão e correção/refinamento da escrita._ |
| Claude | _Desenvolvimento do protótipo em HTML do dashboard interativo_ |
| 

### Workflow

1. Iniciei fazendo um brainstorm para entender o problema central, organizar as perguntas do head de marketing, entender melhor as categorias e definir cuidados metodológicos a seguir antes de analisar os dados;
2. Utilizei o chatGPT como LLM para apoiar a primeira leitura do dataset, identificando quais variáveis estavam disponíveis, quais métricas poderiam ser analisadas e quais segmentações fariam sentido para evitar conclusões genéricas;
3. Em seguida, pedi apoio da IA para construir benchmarks quantitativos iniciais, observando as métricas;
4. A partir dos primeiros achados, optei por aprofundar a análise de conteúdos orgânicos vs patrocinados, usando células comparáveis por plataforma, categoria, formato e creator. A IA me ajudou a organizar os cruzamentos e estrututar possibilidades de leitura dos dados;
5. Posteriormente usei a IA para apoiar a análise de top performers e bottom performers, separando diferentes tipo de de engajamento;
6. Durante o processo, identifiquei alucinações e inconsistências numéricas em algumas tabelas geradas pela LLM. Comparei esses resultados com o dataset original, revisei os números e corrigi manualmente os dados antes de incorporá-los à análise final;
7. A partir da conversa com a IA, realizei a minha própria interpretação dos achados e formulei a análise final com base no meu entendimento do problema, dos dados, da experiência prática com marketing e das solicitações do head de marketing;
8. Utilizei o Claude para executar a minha ideia de uma dashboard de apoio à decisão, tendo desenvolvido um protótipo em HTML para simular combinações de posts e orientar decisões da equipe.
9. Na etapa final, usei a IA como apoio de revisão textual, principalmente para identificar erros de digitação, melhorar redundâncias de termos, organizar melhor as tabelas em markdown e garantir que os arquivos ficassem mais legíveis para a entrega. 

### Onde a IA errou e como corrigi

A principal falha da inteligência artificial durante o processo foi a apresentação de algumas inconsistências numéricas em tabelas resumidas. Em uma etapa da análise de top performers e bottom performers, comparei os valores sugeridos pela IA com o dataset original e notei que alguns números não correspondiam exatamente à base. 

Para corrigir isso, revisei os dados manualmente, comparei as tabelas e ajustei os números antes de incorporar eles na análise final. Além disso, visando corrigir a LLM, passei a direcionar melhor a diferenciação entre dado observado, hipótese e interpretação. 

Portanto, mesmo tendo definido e configurado no início da conversa, qual papel a IA deveria assumir e quais cuidados metodológicos deveria tomar, percebe-se que as regras devem ser retomadas ao longo do processo. Em análises longas, a IA pode perder parte do contexto, simplificar demais decisões, opinar onde não deve e preencher lacunas de forma indevida. Com isso, temos que a qualidade da entrega não depende apenas da qualidade dos prompts iniciais em si, mas também de nossa capacidade humana de revisar, corrigir, questionar, reorientar e interpretar criticamente as respostas geradas. 


### O que eu adicionei que a IA sozinha não faria

Com toda certeza o que eu mais adicionei ao processo foi o meu olhar de quem já trabalha com dados, comunicação, conteúdo e estratégia na prática. A IA conseguiu organizar caminhos e levantar possibilidades, mas eu precisei decidir o que fazia realmente sentido para um problema real de marketing. Por isso eu priorizo sempre o brainstorm antes (e metodologias ágeis no geral), ele possibilita que enxerguemos para o problema de uma ótica ampla!

Através das minhas formações em marketing, dados e IA, também trouxe para o processo uma visão muito clara sobre o potencial da inteligência artificial - sou uma grande entusiasta dela e esse travessão no meio do texto veio de uma humana mesmo - quando ela é bem direcionada. Eu acredito que a IA muda profundamente a forma como trabalhamos, pesquisamos, criamos e tomamos decisões, mas o resultado depende diretamente de como a conduzimos e também de como a validamos. 

O olhar humano crítico foi fundamental uma vez que precisei reavaliar respostas genéricas, revisar números, corrigir inconsistências e separar dados observados de hipóteses. No fim, a IA vem para economizar tempo de tarefas repetitivas e operacionais para que possamos dedicar tempo àquilo que nos torna humanos: a capacidade de questionar e interpretar criticamente tudo à nossa volta. 

A IA amplia nossa capacidade de análise, criação e decisão quando é usada com consciência, repertório e intencionalidade. Para mim, esse desafio reforçou exatamente isso: a tecnologia acelera caminhos, mas o julgamento crítico continua sendo humano.

Obrigada pela oportunidade!

---

## Evidências

_Anexe ou linke as evidências do processo:_

- [Screenshots das conversas com IA](process-log/screenshots)
- [Brainstorm inicial](process-log/brainstorm-inicial.md)
- [Primeira leitura do dataset com IA](process-log/primeira-leitura-dataset.md)

---

_Submissão enviada em: [9 de junho de 2026]_
