# Submissão — Daniel Franco Schkolnick — Challenge 003 — Lead Scorer

## Sobre mim

* **Nome:** Daniel Franco Schkolnick
* **LinkedIn:** https://www.linkedin.com/in/daniel-f-schkolnick-976a22208/
* **Challenge escolhido:** Challenge 003 — Lead Scorer

---

## Executive Summary

Construí uma ferramenta de priorização comercial que combina um CRM operacional com Score Size estrutural e uma camada de gestão para managers. A solução resolve dois problemas centrais: a dificuldade do vendedor em decidir quais leads priorizar no dia a dia e a falta de preenchimento correto do CRM, que impede qualquer priorização confiável. O principal achado foi que o problema de dados incompletos é ainda mais estrutural do que a própria priorização, porque sem preenchimento correto o time comercial perde capacidade de direcionamento, análise e gestão. Como principal recomendação, a empresa deve garantir que todos os leads sejam criados com preenchimento completo e que os gestores passem a cobrar isso sistematicamente, para então usar o Score Size como base de priorização operacional.
Link Produto final: https://g4challenge.lovable.app


---

## Solução

Desenvolvi uma solução funcional com duas frentes principais. A primeira é um CRM operacional com pipeline visual, Score Size estrutural e camada de ação, permitindo que o vendedor entenda rapidamente o que é foco agora, foco depois, baixa prioridade ou correção de cadastro. A segunda é um painel gerencial por manager, criado para dar visibilidade de carga, qualidade da carteira, preenchimento do CRM, tempo médio de fechamento e taxa de ganho por vendedor.

O Score Size foi desenhado como um mecanismo simples, explicável e operacional. Em vez de usar um modelo de ML pouco transparente, optei por uma lógica estrutural baseada em quatro variáveis: taxa de conversão normalizada por segmento, tempo médio de fechamento normalizado por segmento, taxa de conversão normalizada por porte e tempo médio de fechamento normalizado por porte. Depois disso, classifiquei os leads em quartis dinâmicos para gerar os níveis A, B, C e D.

Também incluí uma camada de “Dados incompletos”, porque identifiquei que o problema de preenchimento do CRM era uma causa estrutural do problema de priorização. Sem dados mínimos, os vendedores não sabem o que priorizar e os gestores não conseguem acompanhar a qualidade da carteira. Por isso, a solução não só prioriza, mas também disciplina a operação.

### Abordagem

Meu primeiro passo foi destrinchar o enunciado para entender exatamente o problema de negócio, os stakeholders e o tipo de saída que faria sentido para o desafio. Em seguida, entrei em uma etapa de discovery, explorando os dados e fazendo perguntas estruturadas para identificar padrões, gargalos e comportamentos operacionais relevantes antes de pensar em qualquer solução.

Comecei entendendo o enunciado e depois fui para os dados. O contexto do negócio já estava relativamente claro, mas eu precisava explorar a base para identificar o que realmente estava acontecendo no pipeline e o que poderia estar gerando os problemas descritos.

As principais hipóteses que testei foram:

* havia muitos leads em aberto e uma quantidade elevada de leads por vendedor;
* empresas maiores poderiam demorar mais para fechar, mas talvez apresentassem maior win rate;
* segmentos e portes de empresa poderiam se comportar de forma diferente em taxa de ganho e velocidade de fechamento;
* os times poderiam estar lidando de forma diferente com a pressão, com alguns managers entregando melhor mesmo sob maior carga;
* a ausência de preenchimento correto do CRM poderia estar afetando diretamente a capacidade de priorização.

Optei por um score estrutural porque o objetivo do desafio não era criar um modelo estatístico sofisticado, mas uma ferramenta funcional, explicável e útil para operação real. Ao analisar os dados, ficou claro que existiam variações consistentes por segmento e porte de empresa, tanto em win rate quanto em tempo de fechamento. Isso já fornecia uma base forte para um score simples e operacional. Além disso, como havia diferenças relevantes de desempenho entre times, normalizar essas informações e transformá-las em uma lógica estrutural fazia mais sentido do que construir um modelo mais complexo e menos explicável.

Construí um CRM fake com painel gerencial porque não queria entregar apenas um dashboard analítico. Queria mostrar como o vendedor usaria a priorização na prática e como o gestor acompanharia a execução e os gargalos. Isso me permitiu atacar tanto a operação do dia a dia quanto a camada de gestão.

### Resultados / Findings

Os principais findings foram:

* o pipeline apresentava um volume alto de leads por vendedor, com diferenças relevantes de carga entre times;
* alguns times entregavam melhor mesmo sob maior pressão, o que mostrou que o problema não era apenas volume, mas também disciplina operacional e gestão;
* o achado mais importante foi que a priorização não era o único problema: o preenchimento incorreto do CRM aparecia como uma camada ainda mais estrutural, porque impedia a identificação correta das melhores oportunidades;
* sem os dados mínimos, tudo vira “o mesmo lead”, e o time comercial perde capacidade de distinguir o que deveria ser priorizado.

O produto final construído foi uma ferramenta de direcionamento comercial com foco operacional para vendedores e camada de acompanhamento gerencial para managers. Ela permite priorizar os leads com melhor potencial estrutural, sinalizar leads com dados incompletos e dar ao gestor visibilidade sobre carga, qualidade da carteira e desempenho da equipe.

O que o vendedor consegue fazer com o produto:

* entender quais leads priorizar no dia a dia;
* identificar o que é foco agora e o que é foco depois;
* perceber rapidamente quando um lead está com dados incompletos;
* entender o que está faltando no preenchimento do CRM.

O que o gerente consegue fazer com o produto:

* identificar quem está deixando a desejar em preenchimento;
* analisar a distribuição de leads por vendedor;
* acompanhar o desempenho do time com base em métricas consistentes;
* comparar seu time com o contexto global e entender melhor os gargalos.


### Recomendações

1. Treinar o time comercial para preencher corretamente o CRM e reforçar por que isso é indispensável para priorização.
2. Treinar o time gerencial para identificar gargalos e agir sobre eles com base em carteira, preenchimento e desempenho.
3. Acompanhar diariamente a evolução da operação e cobrar consistência na execução.

O que deve ser implementado imediatamente é a resolução do problema de não preenchimento dos dados. Sem isso, a priorização perde confiabilidade.

Como evolução futura, a empresa pode adicionar comparativos mais sofisticados, automações e camadas preditivas complementares. Mas a primeira versão precisa garantir leitura clara dos dados, preenchimento correto e priorização funcional.

Na prática, o manager deve passar a cobrar preenchimento completo dos dados, uso do score na seleção dos leads de foco agora e disciplina na gestão da carteira. O vendedor, por sua vez, deve preencher os detalhes do CRM de forma completa e focar nos leads Score A e B.

### Limitações

A base não continha informações importantes como origem do lead, histórico de interações, temperatura do lead, data de fechamento esperada e transição detalhada entre etapas.

Minha solução ainda não mede desempenho real com base comportamental ou de engajamento. Ela facilita o direcionamento e melhora a operação, mas não consegue, por exemplo, atualizar automaticamente dados, notificar gestores em tempo real ou prever fechamento individual do lead com base em comportamento.

Também dependeria de integração real com CRM para aplicar as etiquetas em produção, persistir atualizações, extrair métricas continuamente e acionar automações de cobrança ou alerta.

Se eu tivesse mais tempo, faria uma etapa adicional com o time de desenvolvimento e com os gestores para entender dores complementares e validar quais evoluções fariam mais sentido no uso real. Uma próxima camada natural seria adicionar automação de preenchimento ou uma camada preditiva complementar, sem abandonar o MVP estrutural.

---

## Process Log — Como usei IA

> **Este bloco é obrigatório.** Sem ele, a submissão é desclassificada.

### Ferramentas usadas

| Ferramenta                      | Para que usou                                                                                                                           |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| ChatGPT                         | Decomposição do enunciado, análise exploratória dos dados, formulação de hipóteses, desenho do produto e refinamento da lógica do score |
| Lovable                         | Construção do protótipo funcional e iteração da interface                                                                               |
| Planilha (com PROCV)            | Consolidação dos dados e cruzamento entre pipeline, accounts e sales team                                                               |
| Gerador de prompt intermediário | Refinamento do prompt enviado ao Lovable                                                                                                |

### Workflow

1. Entendi o enunciado e identifiquei os outputs esperados.
2. Explorei os dados para encontrar padrões, correlações e potenciais gargalos.
3. Identifiquei os principais problemas: falta de priorização e CRM mal preenchido.
4. Estruturei a lógica do Score Size e a camada de Dados Incompletos.
5. Modelei a solução conceitualmente.
6. Usei um gerador de prompt intermediário para refinar o prompt do Lovable.
7. Construí um primeiro MVP no Lovable.
8. Busquei referências externas e usei uma análise crítica simulada para elevar o nível do produto.
9. Refinei a UX/UI e a lógica operacional do produto até chegar à versão final.

### Onde a IA errou e como corrigi

A IA errou quando começou a assumir correlações demais e a sofisticar excessivamente o score, fugindo do enunciado e do objetivo de criar uma ferramenta prática. Em alguns momentos, ela também propôs algo visualmente interessante, mas pouco útil operacionalmente.

Corrigi isso simplificando o score, mantendo-o explicável e focado em poucas variáveis com alto valor prático. A maior decisão que tomei contra a primeira tendência da IA foi não seguir um modelo excessivamente mutável, com muitas variáveis, que dificultaria a adoção pelo time comercial.

### O que eu adicionei que a IA sozinha não faria

Meu principal julgamento de negócio foi identificar o problema de preenchimento do CRM como causa estrutural do problema de priorização. Esse insight não veio apenas dos dados, mas da experiência prática com operação comercial e gestão.

Também trouxe para a solução elementos que a IA sozinha provavelmente não priorizaria da mesma forma:

* simplicidade operacional do Score Size;
* necessidade de disciplinar o preenchimento do CRM;
* importância de uma camada gerencial para cobrança e acompanhamento;
* preocupação com adoção real no dia a dia do vendedor e do gestor.

O detalhe que mais mostra pensamento de adoção real é a presença do dashboard gerencial como instrumento de cobrança e acompanhamento, e não apenas como visualização. O que supera o baseline de IA foi transformar análise em decisão operacional, usando contexto de negócio e experiência prática para filtrar o que realmente faria sentido implementar.

---

## Evidências

*Anexe ou linke as evidências do processo:*


* [x] Chat exports
Chat principal: https://drive.google.com/file/d/1KnaeOlPpavkFE6Xsr_Dka56fWcYaLHHA/view?usp=sharing
Chat Rafael Milagre: https://drive.google.com/file/d/10Ki4dT4dqUN_Opjg-CAfwh7RO_C_gHX_/view?usp=sharing

* [x] Outro: Link do produto final
https://g4challenge.lovable.app/
---

*Submissão enviada em: 11/03/2026*
