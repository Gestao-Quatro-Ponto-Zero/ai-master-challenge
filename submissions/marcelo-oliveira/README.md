
# Submissão — [Marcelo Oliveira] — Challenge [Challenge 003 — Lead Scorer]

## Sobre mim
Profissional com mais de 15 anos de experiência em Marketing Estratégico, atuando em empresas multinacionais como Cummins, BorgWarner e CBA Votorantim, com forte foco em análise de mercado, geração de valor e tomada de decisão orientada a dados.
Recentemente expandi minha atuação para Ciência de Dados e Inteligência Artificial, aplicando Python, Machine Learning e análise preditiva para resolver problemas reais de negócio, especialmente em contextos B2B.

Minha experiência combina visão estratégica de negócio com execução técnica, permitindo transformar dados em decisões práticas — como neste projeto, onde desenvolvi um motor de priorização de leads aplicável diretamente ao dia a dia comercial.

Tenho especial interesse em aplicar IA para ganho de eficiência, automação e melhoria de performance em áreas como marketing e vendas.- 

-**Nome:** Marcelo Oliveira
-**LinkedIn:** https://www.linkedin.com/in/marcelo-oliveira-marketing/
-**Challenge escolhido:** Challenge 3 - Lead Score


---

## Executive Summary

Desenvolvi um motor de priorização de leads baseado em dados históricos de vendas, com o objetivo de orientar a tomada de decisão comercial de forma objetiva e escalável.

A solução combina taxa de conversão, valor do negócio e qualidade de preço para gerar um score explicável, utilizando fallback hierárquico para garantir robustez mesmo com baixa volumetria de dados.

Durante a análise, identifiquei que uma parcela relevante dos dados estava incompleta, impactando diretamente a eficiência do processo comercial.

Como principal recomendação, a empresa deve priorizar leads com maior score devidamente calibrados e, paralelamente, investir na melhoria da qualidade dos dados, que é o também um  limitador de performance.

---

## Solução

A solução desenvolvida consiste em um motor de priorização de leads baseado em dados históricos de vendas, com foco em aplicação real no processo comercial.

O pipeline foi estruturado em cinco etapas principais:

**1. Integração e preparação dos dados**  
Foram consolidadas diferentes fontes (deals, accounts, products e estrutura comercial), garantindo consistência e padronização das informações. Dados incompletos foram identificados e separados para análise de qualidade. Executamos um merge com estes dados.

**2. Engenharia de métricas de negócio**  
Foram criadas métricas-chave para representar performance comercial:

- **Win Rate:** taxa histórica de conversão por combinação de variáveis entre vendedor, cliente, segmento e mercado.
- **Ticket Normalizado:** valor do deal em relação ao máximo do produto  
- **Preço Alvo (%):** relação entre preço praticado e preço de referência  
- **Ciclo de Vendas:** tempo médio de fechamento (em dias), utilizado como indicador de eficiência operacional  

Além disso, o **estágio da negociação (deal stage)** foi mantido no modelo como variável contextual, permitindo interpretar o momento do lead no funil (ex: prospecting, engaging), sem interferir diretamente no cálculo do score.

**3. Modelo de scoring explicável**  
O score foi construído como uma combinação ponderada das métricas:
- 50% Win Rate  
- 30% Ticket  
- 20% Preço  

A escolha prioriza interpretabilidade e aderência ao contexto de negócio, permitindo fácil leitura pelo time comercial.

**4. Fallback hierárquico (robustez estatística)**  
Para evitar distorções em cenários com poucos dados, foi implementado um sistema de fallback progressivo, reduzindo o nível de granularidade (produto, setor, região) até atingir uma base estatisticamente relevante.

**5. Aplicação interativa (Streamlit)**  
Foi desenvolvida uma interface web que permite:
- Filtrar por vendedor, gerente e região  
- Visualizar ranking priorizado de leads  
- Analisar estágio da negociação e tempo de ciclo por oportunidade  
- Monitorar qualidade dos dados (completo vs incompleto)
- Incluindo um descritivo objetivo para que o vendedor entenda de forma simples qual o critério adotado na lista de prioridade 

🔗 Aplicação: https://ai-sales-prioritization-engine-vbayfyecuz7lyyejzgpvst.streamlit.app/
🔗 Código: https://github.com/mpobzl/ai-sales-prioritization-engine  

A solução foi desenhada para ser simples, robusta e diretamente utilizável pelo time comercial, conectando análise estatística com tomada de decisão prática.

### Abordagem

A abordagem partiu de uma perspectiva de negócio: como transformar um processo hoje baseado em intuição em uma decisão orientada por dados.

O primeiro passo foi entender o problema operacional — um pipeline com alto volume de oportunidades e baixa eficiência na priorização — e mapear quais variáveis realmente impactam o sucesso comercial (conversão, valor e qualidade de negociação).

A partir disso, defino o problema em três frentes principais:
1. **Qualidade e estrutura dos dados** — integração de múltiplas bases, validação de chaves e identificação de inconsistências (ex: registros com "nan" como string), além da separação entre dados completos e incompletos  
2. **Construção de métricas representativas** — definição de indicadores que traduzem performance real (Win Rate, Ticket, Preço Alvo e Ciclo de Vendas), diferenciando variáveis de decisão e variáveis de contexto  
3. **Modelagem com robustez estatística** — desenvolvimento de um modelo simples e explicável, complementado por um sistema de fallback hierárquico para evitar distorções causadas por baixa volumetria  

Durante o processo, priorizei três princípios:
- **Simplicidade e explicabilidade** em vez de modelos complexos  
- **Robustez estatística** para garantir confiabilidade dos resultados  
- **Aplicabilidade prática**, pensando no uso real pelo time comercial

- Toda a solução foi desenvolvida integralmente em Python, cobrindo desde a integração e tratamento de dados até a modelagem e construção da aplicação.

Optou-se intencionalmente por não utilizar modelos mais complexos de Machine Learning, como XGBoost ou redes neurais, uma vez que o problema foi resolvido de forma eficiente com um modelo estatístico simples, explicável e robusto.

Essa decisão priorizou interpretabilidade, facilidade de uso pelo time comercial e aplicabilidade prática no contexto real de negócio.

Por fim, a solução foi estruturada como um produto, evoluindo da análise para uma aplicação interativa, permitindo uso direto no dia a dia de vendedores, gerentes e liderança.



### Resultados / Findings

A análise gerou não apenas um modelo de priorização, mas também insights relevantes sobre a estrutura dos dados e o processo comercial.

**1. Qualidade de dados como principal gargalo**  
Foi identificado um volume significativo de dados incompletos (1425 dos leads ativos no atributo account no arquivo pipeline). Esses registros foram excluídos do modelo, mas evidenciam um problema estrutural no CRM que impacta diretamente a capacidade de análise e decisão.

**2. Tentativa de enriquecimento de dados**  
Foram realizados testes de correlação entre variáveis (produto, setor, região e vendedor) com o objetivo de inferir ou enriquecer dados faltantes. No entanto, não foram encontradas relações suficientemente fortes que permitissem imputação confiável, reforçando a necessidade de melhoria na coleta de dados na origem.

**3. Definição e validação do modelo de scoring**  
A estrutura de pesos (50% Win Rate, 30% Ticket e 20% Preço) mostrou-se a mais equilibrada para refletir:
- Probabilidade de conversão  
- Potencial financeiro  
- Qualidade da negociação  

**4. Importância do fallback estatístico**  
Foi identificado que muitos contextos apresentavam baixa volumetria (ex: poucos deals por combinação de variáveis).  
O uso do fallback hierárquico evitou distorções, como win rates artificialmente altos em amostras pequenas, garantindo maior robustez ao modelo.

**5. Estrutura comercial complexa (multi-contexto)**  
Observou-se que vendedores atuam em múltiplos produtos, setores e regiões, o que justifica a modelagem por contexto e a necessidade de granularidade controlada via fallback.

**6. Baixa variação de preço (insight relevante)**  
A análise de dispersão (scatter plot) entre preço praticado e preço base indicou baixa variabilidade, sugerindo:
- Política de preços relativamente padronizada  
- Menor impacto do desconto como diferencial competitivo  

Isso reforça que o principal driver do score é a conversão histórica, e não a variação de preço.

**7. Papel do ciclo de vendas e estágio da negociação**  
Embora não façam parte do score, essas variáveis mostraram alto valor interpretativo:
- Ciclos mais curtos indicam maior eficiência operacional  
- Estágios mais avançados indicam proximidade de fechamento  

Essas dimensões foram mantidas como suporte à decisão, enriquecendo a leitura do ranking.

**8. Output acionável (resultado final)**  
A solução entrega um ranking claro e utilizável, permitindo:
- Foco imediato nos leads com maior probabilidade de fechamento  
- Melhor alocação de tempo do vendedor  
- Visibilidade sobre gargalos de dados 
 

### Recomendações

- Melhorar a qualidade dos dados (prioridade máxima)
O principal limitador identificado foi o alto volume de dados incompletos,  que inviabiliza o a abordagem com o cliente. São 1425 leads que não terão destinação adequada. Isto gera um grande impacto em termos de faturamento perdido.
Recomenda-se:
- Padronizar o preenchimento de campos críticos (account, sales_price, stage)
- Definir processo de enriquecimento de dados quando acontecem missing datas.
- Priorizar leads com score alto (>0.8)
- Criar SLA de preenchimento de CRM
- Implementar validação obrigatória de campos críticos
- Usar score como input para distribuição de leads
- Monitorar taxa de conversão por vendedor


### Limitações

### Limitações

A principal limitação identificada foi a qualidade dos dados, com um volume significativo de leads incompletos que não puderam ser utilizados no modelo.

Foram realizados testes para inferência e enriquecimento desses dados a partir de variáveis como produto, setor e região, porém não foram encontradas relações suficientemente robustas que permitissem imputação confiável. Dessa forma, optou-se por excluir esses registros para preservar a consistência do modelo.

Além disso, o modelo depende exclusivamente de dados históricos, não incorporando variáveis externas que podem impactar o fechamento (ex: timing de mercado, concorrência ou relacionamento comercial).

A efetividade da solução está diretamente ligada à qualidade dos dados de entrada. Sem melhorias estruturais no CRM, parte do potencial do modelo permanece restrita.

---

## Process Log — Como usei IA

>> Utilizei IA (ChatGPT) como ferramenta de apoio ao longo de todo o desenvolvimento, principalmente para acelerar a estruturação do código em Python, debugging e organização da solução.

A IA foi utilizada nas seguintes etapas:
- Estruturação inicial do pipeline de dados (merge, limpeza e padronização)
- Apoio na implementação das funções de cálculo (win rate, score, fallback)
- Construção da aplicação em Streamlit
- Suporte no troubleshooting durante o deploy (ex: dependências e erros de ambiente)
- Revisão e organização da documentação (README e submissão)

No entanto, todas as decisões críticas foram tomadas manualmente, incluindo:
- Definição das métricas de negócio relevantes  
- Estrutura do modelo de scoring e escolha dos pesos  
- Implementação do fallback hierárquico  
- Interpretação dos dados e identificação de insights  
- Priorização de simplicidade e explicabilidade em vez de modelos complexos  

A IA também apresentou limitações em alguns momentos, sugerindo abordagens excessivamente complexas ou soluções genéricas que não se aplicavam ao contexto do problema. Essas sugestões foram avaliadas e descartadas quando não agregavam valor prático.

Dessa forma, a IA foi utilizada como acelerador de execução, enquanto o raciocínio analítico, as decisões de negócio e a validação da solução foram conduzidos de forma independente.

### Ferramentas usadas

Chat GPT, Python e Streamlit

| Ferramenta | Para que usou |
|------------|--------------|

| ChatGPT | Estruturação da solução, apoio na codificação em Python, debugging e organização do raciocínio |
| Python (Pandas, NumPy) | Integração, limpeza e análise dos dados, cálculo das métricas e construção do modelo de scoring |
| Streamlit | Desenvolvimento da aplicação web interativa para visualização do ranking e uso prático pelo time comercial |

### Workflow

1. **Entendimento do problema e definição da abordagem**  
   Iniciei analisando o contexto do challenge e o problema de negócio (priorização de leads).  
   Utilizei IA para estruturar possíveis abordagens, mas a definição final das métricas e estratégia foi conduzida manualmente.

2. **Integração e exploração dos dados**  
   Realizei o merge das bases (pipeline, accounts, products e sales team) e análise exploratória inicial.  
   A IA foi utilizada como apoio na escrita de código e validação de estruturas, enquanto a interpretação dos dados foi feita manualmente.

### Onde a IA errou e como corrigi
3. **Limpeza e tratamento de dados**  
   Identifiquei inconsistências (ex: valores "nan" como string) e separei dados completos e incompletos.  
   A IA auxiliou na implementação das rotinas de limpeza, mas as decisões sobre critérios de exclusão foram feitas com base em análise crítica.

4. **Definição de métricas e modelagem**  
   Desenvolvi as métricas principais (Win Rate, Ticket, Preço Alvo e Ciclo de Vendas) e construí o modelo de scoring.  
   A IA apoiou na codificação, mas a definição dos pesos e da lógica do modelo foi uma decisão de negócio.

5. **Implementação do fallback hierárquico**  
   Criei a lógica para garantir robustez estatística em cenários com baixo volume de dados.  
   Essa foi uma decisão estratégica, com apoio pontual da IA na implementação técnica.

6. **Validação do modelo**  
   Realizei validação manual dos cálculos e consistência dos resultados.  
   Essa etapa foi conduzida sem uso de IA, garantindo confiabilidade da solução.

### O que eu adicionei que a IA sozinha não faria
7. **Desenvolvimento da interface (Streamlit)**  
   Construí a aplicação web com filtros e visualização do ranking de visualização simples e funcional.
   Identifiquei a necessidade de atributos adicionais no filtro de gerentes e regionais, adicionado a lista de vendedores vinculados aquela região ou liderança.

_Qual foi seu julgamento, contexto, ou insight que fez diferença?_
8. **Deploy e ajustes em produção**  
  A definição dos pesos no score, a hierarquia na regra do fallback

9. **Documentação e organização final**  
   Estruturei o README e a submissão, utilizando a IA para revisão e clareza na comunicação.
---

### O que eu adicionei que a IA sozinha não faria

A AI não tem visão de negócio executiva, nem sempre faz um jugamento adequado de algum output. Um exemplo foi a definição do critério do score. A IA sozinha não consegue dizer se o número é adequado ou não para a situação. Nem sempre a IA sugere a melhor hipotese a ser testada, como foi no caso de range de preço. No grafico de box plot ela identificou um outlier mas era apenas um produto premium com preço superior. Se eu apenas seguisse a IA, poderia eliminar da base um dado muito relevante.
A IA inicialmente sugeriu um modelo multiplicativo: (EV = win_rate × ticket × price_ratio) que não era a melhor equação. Trabalhando com variações de formulas, foi identificado a melhor equação.
A IA não trouxe um modelo de fallback adequado inicialmente. Tivemos que testar modelos diferentes. Fomos adequando o melhor numero para amostragem mínima e depois reduzindo atributos até ter o melhor formato.
A IA sugeriu colocar no peso da formula do score o fator ciclo de venda mas entendi não ser adequado. Isso traria mais ruido apenas e optei em não colocar este dado na formula.
A IA assumiu inicialmente que o preço era um fator relevante para conversão mas vimos que o range de variação de preço não mostrou isso. Criamos graficos para entender media, mediana e moda para validar.

## Evidências

_Anexe ou linke as evidências do processo:_

- [ ] Screenshots das conversas com IA
- [ ] <img width="1280" height="720" alt="Imagem 1" src="https://github.com/user-attachments/assets/6bf9f42a-8752-4575-b130-0500fc5e439b" />
      <img width="1280" height="720" alt="imagem2" src="https://github.com/user-attachments/assets/0c3922ed-a2d6-4839-b4f0-4832a5bdcce6" />
      https://github.com/user-attachments/files/26256643/Evidencias.de.uso.de.IA.docx


- [ ] Screen recording do workflow
- [ ] Chat exports
- [ ] Git history (se construiu código)
