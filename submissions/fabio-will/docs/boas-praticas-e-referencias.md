# Boas práticas e literatura de referência para o 002 (Redesign de Suporte)

Checado em 13/11/2026. "Confirmado" = li a fonte primária ou página oficial; fonte secundária vem sinalizada.

---

## 1. Operação de suporte

### 1.1 Esforço do cliente (The Effortless Experience, CES)
- **Ideia.** Encantar não paga; facilitar paga. Lealdade se perde por esforço, e o livro traz uma versão nova do Customer Effort Score.
- **Fonte.** Dixon, Toman e DeLisi, *The Effortless Experience*, Portfolio, 2013; antes, Dixon, Freeman e Toman, "Stop Trying to Delight Your Customers", HBR, 2010. Release da CEB (16/10/2013): 96% dos clientes com alto esforço tendem à deslealdade, contra 6% com baixo esforço (mais de 125 mil clientes).
- **No 002.** Cada reatribuição de fila é uma transferência que o cliente sente; medimos reatribuição, não só acurácia.
- **Status.** Confirmado em https://www.prnewswire.com/news-releases/delighting-customers-doesnt-pay-making-their-lives-easier-does-227994941.html e https://hbr.org/2010/07/stop-trying-to-delight-your-customers. Redação exata do CES 2.0 (escala de 7 pontos) só em fontes de fornecedores: não confirmado.

### 1.2 Contatos evitáveis (The Best Service Is No Service)
- **Ideia.** Sete princípios; o primeiro é eliminar "dumb contacts" com correção de causa raiz; o sexto lembra que nem todo contato deve sumir, porque contato é informação. Métrica: contatos por cliente ou transação (CPX).
- **Fonte.** Bill Price e David Jaffe, *The Best Service Is No Service*, Jossey-Bass, 2008.
- **No 002.** O painel mostra volume e reincidência por categoria: o repetitivo vira candidato a eliminação na origem, não só a automação.
- **Status.** Confirmado no trecho oficial do livro em https://content.e-bookshelf.de/media/reading/L-588986-07ae21fdad.pdf e em https://customerthink.com/the-best-service-is-no-service-turns-10-going-strong/

### 1.3 KCS (Knowledge-Centered Success, antes Knowledge-Centered Service)
- **Ideia.** Conhecimento capturado dentro do atendimento (Solve Loop: Capture, Structure, Reuse, Improve) e analisado pela organização (Evolve Loop). "Reuse is review": quem reutiliza um artigo responde por ele. O nome mudou em abr/2026.
- **Fonte.** Consortium for Service Innovation, KCS v6 Practices Guide; post de 07/05/2026 sobre a mudança.
- **No 002.** Tickets parecidos com a resolução aplicada são a base viva; o rascunho do LLM só se apoia em casos reais.
- **Status.** Confirmado em https://library.serviceinnovation.org/KCS/KCS_v6/KCS_v6_Practices_Guide e https://www.serviceinnovation.org/from-service-to-success-kcs-is-evolving/

### 1.4 ITIL 4
- **Ideia.** Service desk captura a demanda (ponto único de contato); incident management restaura o serviço o quanto antes; service level management fixa metas de negócio e as acompanha. "Efeito melancia": SLA verde por fora, cliente insatisfeito por dentro.
- **Fonte.** ITIL 4, AXELOS, fev/2019 (marca da PeopleCert desde 2021).
- **No 002.** O roteador é a etapa de categorização e atribuição do incidente; SLA sem reabertura e satisfação cai no efeito melancia.
- **Status.** Data confirmada em https://en.wikipedia.org/wiki/ITIL. Propósitos das práticas e efeito melancia: só fontes secundárias (site da AXELOS bloqueia leitura automática), não confirmado na primária.

### 1.5 Métricas: o que cada uma mede de verdade (leitura nossa)
- **Ideia.** FRT mede espera, não solução. AHT mede capacidade e, como meta, incentiva encerrar cedo. FCR só vale pela visão do cliente. Reabertura é o contrapeso de FCR e AHT. Backlog é estoque: precisa de idade e de entrada contra saída.
- **Fonte.** Strathern, "'Improving ratings': audit in the British University system", *European Review* 5(3), 1997 ("when a measure becomes a target, it ceases to be a good measure"), a partir de Goodhart (1975). SQM Group: medir FCR pela perspectiva do cliente.
- **No 002.** Metas sempre em par: automação com precisão, velocidade com reabertura.
- **Status.** Strathern em https://en.wikipedia.org/wiki/Goodhart%27s_law (secundária). SQM confirmado em https://sqmgroup.com/resources/library/blog/fcr-enterprise-level-metric

### 1.6 Dimensionamento (Erlang C)
- **Ideia.** Erlang C ignora abandono; a revisão de referência recomenda Erlang A como padrão.
- **Fonte.** Gans, Koole e Mandelbaum, "Telephone Call Centers: Tutorial, Review, and Research Prospects", *MSOM* 5(2), 2003.
- **No 002.** Não usamos (tempos sintéticos, fila assíncrona); serve para explicar por que não dimensionamos headcount.
- **Status.** Confirmado em https://aviman.technion.ac.il/files/References/Gans-Koole-Mandelbaum-CCReview.pdf

---

## 2. IA em suporte com humano no loop

### 2.1 Opção de rejeição e classificação seletiva
- **Ideia.** O classificador pode abster-se, com troca ótima entre erro e rejeição. Depois: controlar o risco pela cobertura e aprender quando passar ao humano, considerando a qualidade dele.
- **Fonte.** C. K. Chow, "On optimum recognition error and reject tradeoff", *IEEE Trans. Information Theory* 16(1), 1970. Geifman e El-Yaniv, "Selective Classification for Deep Neural Networks", NIPS 2017. Madras, Pitassi e Zemel, "Predict Responsibly", NeurIPS 2018. Mozannar e Sontag, "Consistent Estimators for Learning to Defer to an Expert", ICML 2020.
- **No 002.** É o gate de três níveis: limiar automático escolhido para precisão de 95% na validação, faixa assistida e humano.
- **Status.** Chow confirmado em registro bibliográfico (https://doi.org/10.1109/TIT.1970.1054406); demais em https://arxiv.org/abs/1705.08500, https://proceedings.neurips.cc/paper/2018/hash/09d37c08f7b129e96277388757530c72-Abstract.html e https://icml.cc/virtual/2020/poster/6448

### 2.2 Calibração de probabilidade
- **Ideia.** Redes modernas são mal calibradas; temperature scaling corrige no mesmo domínio. Naive Bayes empurra probabilidades para 0 e 1. Sob mudança de dados, a calibração pós-hoc "fica aquém".
- **Fonte.** Guo, Pleiss, Sun e Weinberger, "On Calibration of Modern Neural Networks", ICML 2017. Niculescu-Mizil e Caruana, "Predicting Good Probabilities with Supervised Learning", ICML 2005. Ovadia et al., "Can You Trust Your Model's Uncertainty?", NeurIPS 2019.
- **No 002.** Regressão logística porque o limiar exige confiança honesta (ECE perto de 0,01 contra 0,29 do Complement NB no lab.json). Fora do domínio a calibração não vale: no estresse com o Dataset 1, sem a guarda de novidade, cerca de metade iria para automático.
- **Status.** Confirmado em https://arxiv.org/abs/1706.04599, https://mlanthology.org/icml/2005/niculescumizil2005icml-predicting e https://arxiv.org/abs/1906.02530

### 2.3 Dívida técnica de ML
- **Ideia.** Pouco do sistema é código de ML. CACE ("Changing Anything Changes Everything"). O modelo influencia os próprios dados futuros (mitigável com aleatorização). Monitorar "prediction bias" (previsto contra observado) e impor "action limits" que disparam intervenção manual.
- **Fonte.** D. Sculley et al., "Hidden Technical Debt in Machine Learning Systems", NIPS 2015.
- **No 002.** Amostra aleatória de automáticos vai para auditoria humana (rótulo sem viés para retreino); painel compara mix previsto e corrigido; teto de automação por hora.
- **Status.** Confirmado em https://papers.nips.cc/paper_files/paper/2015/hash/86df7dcfd896fcaf2674f757a2463eba-Abstract.html

### 2.4 Rules of Machine Learning
- **Ideia.** Regra 1: não tenha medo de lançar sem ML. Regra 2: primeiro desenhe e implemente métricas. Regra 10: cuidado com falhas silenciosas.
- **Fonte.** Martin Zinkevich, "Rules of Machine Learning: Best Practices for ML Engineering", Google.
- **No 002.** Filas sensíveis são regra fixa, não modelo; métricas de sustentação existem antes do primeiro automático.
- **Status.** Confirmado em https://developers.google.com/machine-learning/guides/rules-of-ml

### 2.5 Drift e monitoramento
- **Ideia.** Covariate shift, label shift e concept drift são coisas distintas; sistemas de ML "falham em silêncio"; rótulos atrasam, então previsões e entradas viram proxy; registre todo feedback do usuário.
- **Fonte.** Chip Huyen, *Designing Machine Learning Systems*, O'Reilly, 2022, cap. 8; nota da autora de 07/02/2022.
- **No 002.** Override do agente é o rótulo que chega rápido; PSI e mix de filas são o proxy até lá.
- **Status.** Confirmado em https://huyenchip.com/2022/02/07/data-distribution-shifts-and-monitoring.html

### 2.6 Workflow antes de agente
- **Ideia.** Workflows seguem caminhos de código predefinidos; agentes decidem o próprio processo. Comece pela solução mais simples possível. O padrão "Routing" usa atendimento como exemplo.
- **Fonte.** Erik Schluntz e Barry Zhang, "Building effective agents", Anthropic, 19/12/2024.
- **No 002.** Workflow de roteamento com checkpoint humano, não agente autônomo.
- **Status.** Confirmado em https://www.anthropic.com/engineering/building-effective-agents

### 2.7 RAG e tickets parecidos como fonte
- **Ideia.** Geração com memória recuperável produz texto mais específico e factual; dar proveniência às respostas era problema em aberto.
- **Fonte.** Patrick Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", NeurIPS 2020.
- **No 002.** O rascunho mostra os tickets que o embasaram; sem vizinho parecido, não há rascunho.
- **Status.** Confirmado em https://arxiv.org/abs/2005.11401

### 2.8 Interação humano e IA, e viés de automação
- **Ideia.** Deixar claro quão bem o sistema funciona (G2), facilitar correção (G9), reduzir escopo na dúvida (G10), explicar por que fez o que fez (G11). Mas ajuda imperfeita gera complacência e viés de automação, até em especialistas.
- **Fonte.** Amershi et al., "Guidelines for Human-AI Interaction", CHI 2019. Parasuraman e Manzey, *Human Factors* 52(3), 2010.
- **No 002.** Explicação por palavras atende G11. Override baixo no nível assistido não prova acerto: daí a auditoria cega por amostra.
- **Status.** Confirmado em https://www.microsoft.com/en-us/research/uploads/prod/2019/03/AI_Guidelines_Poster_PrintQuality.pdf e https://doi.org/10.1177/0018720810376055

### 2.9 Evidência de campo
- **Ideia.** Assistente generativo para 5.172 agentes de suporte elevou em 15% os casos resolvidos por hora; ganho maior nos menos experientes, pequena queda de qualidade nos mais experientes. No working paper de 2023: 14% na média, 34% para novatos.
- **Fonte.** Brynjolfsson, Li e Raymond, "Generative AI at Work", *QJE* 140(2), 2025.
- **No 002.** Âncora para o ganho do nível assistido: dezenas de por cento, não 100%.
- **Status.** Confirmado em https://econpapers.repec.org/RePEc:oup:qjecon:v:140:y:2025:i:2:p:889-942 e https://www.nber.org/papers/w31161

### 2.10 Quando NÃO automatizar
- **Ideia.** O titular pode pedir revisão de decisão só automatizada (LGPD, art. 20); saúde e vida sexual são dados sensíveis (art. 5º, II). 64% dos clientes prefeririam atendimento sem IA; o maior medo é não chegar a uma pessoa. A Klarna anunciou em 2024 que a IA fazia o trabalho de 700 agentes e admitiu em 2025 "qualidade mais baixa" por foco em custo. Segurança tem processo próprio.
- **Fonte.** Lei 13.709/2018; Gartner, 09/07/2024 (5.728 clientes); Klarna, 27/02/2024; Bloomberg via Maginative, 08/05/2025; NIST SP 800-61r3, 2025.
- **No 002.** RH, acesso privilegiado e suspeita de segurança nunca vão para automático; o humano está sempre a um clique.
- **Status.** Confirmado em https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm, https://insurance-canada.ca/2024/07/15/gartner-survey-ai-for-customer-service/ (release da Gartner bloqueia leitura automática), https://www.klarna.com/international/press/klarna-ai-assistant-handles-two-thirds-of-customer-service-chats-in-its-first-month/, https://www.maginative.com/article/klarna-dials-back-its-ai-customer-service-strategy-now-its-hiring-humans-again/ e https://csrc.nist.gov/pubs/sp/800/61/r3/final

### 2.11 Ataque de evasão em classificador de texto
- **Ideia.** Colar palavras "inocentes" num texto empurra o classificador para outra classe. É o ataque clássico de filtro de spam (good word attack) e é o primeiro item do Top 10 de segurança de ML da OWASP (ML01, manipulação de entrada); envenenar o dado de treino é o segundo (ML02).
- **Fonte.** Lowd, D. e Meek, C. (2005). Good Word Attacks on Statistical Spam Filters. CEAS. OWASP Machine Learning Security Top 10 (2023).
- **No 002.** O pentest colou palavras de Hardware em tickets de RH e de administrador: 42% escapavam das travas. Entraram a leitura por trecho de 8 palavras e a trava de sequência; o escape caiu para 10% a 15%. Retreino só com rótulo confirmado, por causa do ML02.
- **Status.** Confirmado em https://dblp.uni-trier.de/rec/conf/ceas/LowdM05.html e https://owasp.org/www-project-machine-learning-security-top-ten/

---

## 3. Comunicação executiva

### 3.1 Princípio da Pirâmide (Minto)
- **Ideia.** Ideias em pirâmide sob um único ponto; a introdução Situação, Complicação, Pergunta (SCQ) identifica a pergunta do leitor, e o topo a responde.
- **Fonte.** Barbara Minto, *The Pyramid Principle*, 1987; *The Minto Pyramid Principle*, 1996.
- **No 002.** Slide 1 é a resposta. S: 30 mil tickets/ano; C: os dados de tempo não sustentam diagnóstico; Q: onde a IA ajuda com segurança?
- **Status.** Confirmado em https://barbaraminto.com/. "Comece pela resposta" como frase da autora: só em fontes secundárias.

### 3.2 Memorando narrativo da Amazon
- **Ideia.** "We don't do PowerPoint": memorandos de seis páginas em estrutura narrativa, lidos em silêncio no início da reunião, escritos ao longo de uma semana ou mais.
- **Fonte.** Jeff Bezos, carta aos acionistas de 2017 (publicada em abr/2018).
- **No 002.** O README é o memorando; o deck resume o que o README sustenta.
- **Status.** Confirmado em https://www.aboutamazon.com/company-news/2017-letter-to-shareholders/

---

## 4. Business case honesto

- **Ideia.** Avaliações tendem ao otimismo e devem ser ajustadas explicitamente; testar sensibilidade nas premissas-chave; "valor de virada" é onde uma premissa faz a opção deixar de valer a pena. A Forrester (TEI) desconta benefícios por risco, mas seus estudos são encomendados pelo fornecedor.
- **Fonte.** HM Treasury, *The Green Book*, edição 2026; Forrester, Total Economic Impact.
- **No 002.** Economia líquida = (tickets automáticos × minutos de triagem evitados − erros × minutos de retrabalho − horas de auditoria) × custo-hora. Cada premissa é controle no painel, com cenários pessimista, base e otimista, e o valor de virada da precisão aparece.
- **Status.** Green Book confirmado em https://www.gov.uk/government/publications/the-green-book--2/the-green-book-2026; TEI em estudo de exemplo, https://tei.forrester.com/go/coursera/courseraforbusiness

---

## Frases que podemos usar

1. "Automatizar só onde o modelo sabe que sabe: é a opção de rejeição de Chow, de 1970." (Chow, 1970)
2. "Confiança de 0,9 tem que significar acertar 9 em 10; senão o limiar é decorativo." (Guo et al., 2017)
3. "Nem todo contato deve sumir: contato também é informação." (Price e Jaffe, 2008)
4. "Comece pela solução mais simples possível; agente só quando precisar." (Anthropic, 2024)
5. "Sistemas de ML falham em silêncio; o override do agente é nosso alarme." (Huyen, 2022)
6. "Override baixo pode ser só confiança demais na máquina; por isso auditamos às cegas." (Parasuraman e Manzey, 2010)
7. "IA no atendimento rendeu 15% a mais por hora num estudo com 5 mil agentes, não 100%." (Brynjolfsson, Li e Raymond, 2025)
8. "Quando a medida vira meta, deixa de ser boa medida: cada meta vem com contrapeso." (Strathern, 1997)

## O que evitar dizer

- "Automatizamos 100% da triagem": o próprio enunciado chama isso de red flag.
- "A Gartner previu 85% das interações sem humano até 2020": ano e redação variam e não achei o documento original.
- "Cada 1% de FCR dá 1% de CSAT": dado proprietário da SQM, sem metodologia aberta.
- "CES prevê lealdade melhor que NPS e CSAT": não confirmei no texto da HBR.
- "PSI acima de 0,25 prova drift": regra prática de crédito (atribuída a Lewis, 1994, popularizada por Siddiqi), com limiares tidos como arbitrários.
- "A Klarna trocou 700 atendentes por IA": número da própria empresa, que recuou em 2025.
- "Nosso classificador acerta 95%": os 95% são a precisão do nível automático, não do total.
- Qualquer tempo de resolução ou CSAT do Dataset 1 como diagnóstico real: a base é sintética.
