# Submissão — Allyson Assunção — Challenge 003

## Sobre mim

- **Nome:** Allyson Henrique Assunção da Silva
- **LinkedIn:** [allyson-henrique-243ab417b](https://www.linkedin.com/in/allyson-henrique-243ab417b)
- **Challenge escolhido:** 003 — Lead Scorer

## Executive Summary

Construí uma ferramenta que prioriza as oportunidades da pipeline por meio de um lead score explicável, combinando valor do produto, histórico comercial e momento da negociação. A análise mostrou que o desempenho e o ciclo de venda variam conforme o produto e a região, tornando esses recortes mais úteis do que uma taxa geral. O protótipo apresenta um Top 5 diário, permite analisar toda a pipeline e identifica oportunidades perdidas que podem ser reativadas e redistribuídas para vendedores da mesma região com melhor histórico no produto. Recomendo que vendedores utilizem principalmente “Foco de hoje” e “Pipeline”, enquanto managers e RevOps utilizem “Equipe” e “Repescagem”, revisando periodicamente as regras com base nos resultados reais. Como limitação, o dataset não informa atividades realizadas, última interação, data de criação de todas as oportunidades ou motivos de perda, o que reduz a precisão da avaliação do momento e das causas de cada resultado.

## Solução

### Abordagem

Comecei traduzindo o problema comercial em uma decisão objetiva: indicar quais oportunidades merecem atenção e explicar o motivo. Decompus o trabalho em público-alvo, leitura e limitações dos dados, critérios de priorização, ações recomendadas e experiência de uso. Priorizei uma heurística simples e auditável, baseada em valor, histórico e momento, e refinei as regras por produto e região sempre que havia amostra suficiente. Por fim, validei a linguagem e a navegação pela perspectiva de um vendedor leigo que precisa abrir a aplicação e saber onde agir.

### Resultados / Findings

Foi construída uma aplicação React com banco local PGlite, capaz de funcionar offline após a instalação inicial. A solução entrega um Top 5 diário, a pipeline completa com filtros, análises gerenciais por vendedor, produto e região e uma lista de repescagem para oportunidades perdidas. A análise mostrou diferenças relevantes na taxa de vendas realizadas e no ciclo comercial entre produtos e regiões; por isso, o histórico regional é utilizado quando a amostra é suficiente. O score é acompanhado de explicações em linguagem comercial e não apenas de uma classificação numérica.

### Recomendações

O vendedor deve começar o dia pelo menu “Foco de hoje” e usar “Pipeline” para acompanhar as demais oportunidades, preferencialmente com o filtro por vendedor. Managers e RevOps devem priorizar “Equipe” e “Repescagem”, usando os filtros por manager ou região para decisões de acompanhamento e redistribuição. Todos os filtros funcionam em todos os menus, mas essa divisão oferece informações mais adequadas às decisões de cada perfil. Recomendo ainda acompanhar os resultados do Top 5, revisar periodicamente as regras e enriquecer o CRM com atividades realizadas, última interação e motivos de perda.

### Lógica do Lead Score
O Lead Score prioriza as oportunidades abertas nos estágios **Prospecting** e **Engaging**. A pontuação varia de 0 a 100 e corresponde à soma de três componentes apresentados na aplicação:

```text
Lead Score = Valor (até 40) + Histórico (até 40) + Momento (até 20)
```

#### Valor — de 10 a 40 pontos
O componente Valor utiliza o `sales_price` do produto vinculado à oportunidade. Os produtos são ordenados pelo preço de catálogo: o produto de menor valor recebe 10 pontos, o de maior valor recebe 40 pontos e os demais recebem pontuações intermediárias. Dessa forma, o potencial financeiro influencia a prioridade, mas não determina sozinho a posição da oportunidade.

#### Histórico — de 0 a 40 pontos
O Histórico representa a proporção de vendas realizadas entre as oportunidades encerradas do mesmo produto e da mesma região:

```text
Taxa histórica = Won / (Won + Lost)
Pontos de Histórico = Taxa histórica × 40
```

A taxa regional é utilizada quando existem pelo menos 30 oportunidades encerradas naquela combinação de produto e região. Quando a amostra regional é menor, a aplicação utiliza o histórico geral do produto e informa esse fallback na explicação do score.

#### Momento — 0, 10 ou 20 pontos
Para oportunidades em **Engaging**, o Momento compara os dias em negociação com o tempo histórico das vendas realizadas do mesmo produto e região:

- até a mediana histórica: 20 pontos;
- acima da mediana, mas dentro do prazo em que 90% das vendas foram realizadas: 10 pontos;
- acima do prazo de 90%: 0 pontos;
- sem `engage_date`: 0 pontos.

O relógio regional é utilizado quando existem pelo menos 30 vendas realizadas com datas válidas. Em amostras menores, o sistema utiliza o ciclo geral do produto e, se ele também for insuficiente, o ciclo global. Como o dataset não informa a data de criação das oportunidades em Prospecting, elas recebem 10 pontos neutros de Momento.

#### Níveis de foco
- **Alto:** 70 pontos ou mais;
- **Médio:** de 50 a 69 pontos;
- **Baixo:** menos de 50 pontos.

O Lead Score não representa uma probabilidade exata de fechamento. Ele é uma heurística de priorização: quanto maior a pontuação, maior a combinação de valor, evidência histórica e momento comercial disponível nos dados.

#### Score de repescagem
A página Repescagem utiliza um cálculo separado para oportunidades perdidas: Valor, até 40 pontos; Recência da perda, até 40 pontos; e Histórico geral do produto, até 20 pontos. São consideradas somente perdas ocorridas nos últimos 90 dias, com conta e data de fechamento, desde que a mesma conta não tenha comprado o mesmo produto posteriormente. Uma redistribuição só é sugerida para outro vendedor da mesma região, com pelo menos 15 oportunidades anteriores no produto, região com pelo menos 30 registros e melhoria histórica estimada de no mínimo 5 pontos percentuais.

### Limitações

O dataset é um recorte histórico e estático, cuja data de referência é 31 de dezembro de 2017. A aplicação não está conectada a um CRM e, portanto, não recebe novas oportunidades, mudanças de estágio ou atividades comerciais automaticamente.

O dataset não contém a data de criação das oportunidades em Prospecting, histórico de atividades, última interação, próximo passo, previsão de fechamento ou motivo de perda. Por isso, Prospecting recebe uma pontuação neutra de Momento, enquanto a repescagem não consegue diferenciar perdas por preço, concorrente, ausência de interesse ou outro motivo comercial.

O `engage_date` informa quando a oportunidade entrou em Engaging, mas não quando ocorreu a última interação. Consequentemente, o componente Momento mede tempo no estágio e não o nível real de atividade do vendedor ou do cliente.

O valor potencial utiliza o preço de catálogo do produto, pois o dataset não possui um valor estimado para oportunidades ainda abertas. Já a receita esperada é uma estimativa baseada no preço do produto e na taxa histórica utilizada pelo score, não uma previsão financeira calibrada.

O Lead Score é uma heurística explicável, e não uma probabilidade validada de fechamento. Ainda seria necessário realizar um backtest temporal e um piloto com o time comercial para verificar se oportunidades com maior score avançam e convertem mais. Quando uma combinação de produto e região possui poucos registros, a aplicação recorre a dados mais gerais, reduzindo a personalização regional.

As sugestões de redistribuição na repescagem consideram o desempenho histórico, mas não conhecem a capacidade atual do vendedor, o relacionamento prévio com a conta, a carteira, o território ou outras regras internas. Elas devem ser tratadas como apoio à decisão do manager ou de RevOps, e não como redistribuições automáticas.

## Process Log — Como usei IA

### Ferramentas usadas
- OpenAI Codex: análise do dataset + brainstorming de indicadores para cálculo do lead score
- Gemini: dupla-validação da análise do dataset + brainstorming secundário de indicadores

### Workflow
Comecei traduzindo o desafio apresentado pela área de Vendas em um problema objetivo: os vendedores precisavam identificar rapidamente quais oportunidades mereciam atenção, sem depender apenas de experiência pessoal ou intuição. Antes de solicitar qualquer implementação à IA, decomponho o problema em cinco partes: público-alvo, dados disponíveis, critérios de priorização, explicação do score e experiência de uso. Também defini três perfis de usuário — vendedor, manager e RevOps — e estabeleci que o foco principal seria o vendedor que abre a ferramenta no início do dia e precisa saber onde agir.

Utilizei o Codex como principal ferramenta de IA durante todo o processo. A ferramenta foi usada para analisar a estrutura dos arquivos CSV, explorar possibilidades de scoring, construir o protótipo, revisar regras de negócio, ajustar textos da interface e documentar a solução. O navegador local também foi utilizado como apoio para visualizar e validar a aplicação em funcionamento, mas não como uma segunda ferramenta de IA.

Na primeira etapa, pedi à IA que analisasse as tabelas de contas, produtos, vendedores e oportunidades. A partir disso, identifiquei três dimensões viáveis para o lead score: valor do produto, histórico de vendas realizadas e momento da oportunidade. Também explorei ideias mais avançadas, como afinidade entre vendedor e contexto, comparação do tempo de negociação por produto, efeito de empresa-mãe e adequação entre produto e tamanho da conta. Entretanto, priorizei somente os critérios que poderiam ser explicados com clareza e sustentados pelos dados disponíveis.

O primeiro protótipo apresentou alguns conceitos excessivamente abstratos, como “acelerar”, “resgatar” e “revisar”. Percebi que essas classificações não deixavam claro o que o vendedor deveria executar. Solicitei que a interface passasse a utilizar verbos e instruções mais diretas, além de separar o potencial comercial da ação recomendada. Também limitei a explicação a poucos motivos por oportunidade e defini que o card principal deveria apresentar pontuação total, oportunidade, produto, identificador, tarefa recomendada, composição do score e ação para concluir.

Outro problema identificado foi a complexidade do cálculo. A primeira versão trazia informações técnicas e textos que poderiam confundir um usuário leigo. Por exemplo, a IA utilizou a frase “a oportunidade ainda precisa ser qualificada” apenas porque o estágio era Prospecting, embora o dataset não confirmasse que uma qualificação não havia ocorrido. Corrigi essa interpretação e passei a apresentar somente fatos comprováveis, como o estágio atual e a ausência de informação temporal para oportunidades em Prospecting.

Também percebi que o mesmo percentual histórico, como 64%, aparecia em muitas oportunidades. Isso acontecia porque a primeira regra utilizava uma taxa geral do produto, sem considerar a região do vendedor. Solicitei então que o histórico passasse a utilizar a combinação entre produto e região quando existisse uma amostra suficiente. A mesma lógica regional foi aplicada ao componente de momento, que compara o tempo da oportunidade com o ciclo histórico de vendas realizadas daquele produto na respectiva região.

A explicação do tempo de negociação também foi revisada. Em vez de textos técnicos como “92 dias em Engaging; dentro do limite de 105 dias”, defini uma comunicação mais próxima da linguagem comercial: “Está em negociação há 92 dias. Normalmente, 90% das vendas realizadas deste produto são concluídas em até 105 dias”. Essa mudança foi importante porque tornou o dado compreensível sem exigir que o vendedor conhecesse a metodologia estatística.

Durante a construção, a IA também interpretou “receita esperada” como uma estimativa ponderada pela probabilidade de fechamento. Essa interpretação era matematicamente possível, mas não correspondia ao conceito que eu queria apresentar nos cards principais. Corrigi a regra para que o valor exibido nas oportunidades fosse relacionado ao preço do produto e alterei o nome do indicador agregado para “Valor potencial da pipeline”. Mantive “Receita esperada” apenas quando a intenção fosse realmente apresentar um valor ponderado pelo histórico de conversão.

Na página de repescagem, questionei por que oportunidades perdidas há mais tempo poderiam aparecer com prioridade superior às perdas recentes. Reforcei que a finalidade não era apenas listar perdas, mas identificar oportunidades com potencial de reativação. Também determinei que qualquer sugestão de redistribuição deveria permanecer na mesma região, respeitando a estrutura comercial. A recomendação passou a considerar valor, recência da perda, histórico do produto e desempenho de outros vendedores da mesma região.

Além do que a IA sugeriu inicialmente, adicionei decisões de negócio que não poderiam ser inferidas apenas pelos dados. Entre elas estavam a divisão das visões por perfil, a restrição de redistribuição à mesma região, a preferência por uma interface simples, o uso de linguagem comercial em português, a apresentação de somente dois motivos por oportunidade e a distinção entre valor potencial e receita esperada. Também defini que “Foco de hoje” e “Pipeline” seriam as principais visões do vendedor, enquanto “Equipe” e “Repescagem” seriam mais adequadas para managers e RevOps.

A aplicação foi refinada em várias etapas de interface. Pedi a inclusão do Top 5 diário, posição de prioridade do primeiro ao quinto lugar, níveis de foco alto, médio e baixo, filtros por vendedor, manager e região, tabelas ordenáveis e análises por vendedor, produto e região. Também solicitei a remoção de elementos que aumentavam a complexidade sem ajudar na decisão, como a fórmula completa exibida nos cards e o menu de metodologia.

Ao final, o resultado foi uma aplicação funcional que transforma os dados históricos do CRM em uma lista explicável de prioridades. A ferramenta permite visualizar o Top 5 do dia, consultar a pipeline completa, analisar o desempenho da equipe e avaliar oportunidades de repescagem. O principal aprendizado foi que a utilidade comercial depende menos da sofisticação do modelo e mais da clareza com que cada pontuação é convertida em uma ação.

A principal limitação encontrada está na qualidade e na abrangência do dataset. Não existem informações completas sobre a data de criação das oportunidades, última interação, atividades realizadas, próximo passo ou motivo de perda. Por isso, algumas regras precisam utilizar aproximações, como atribuir um valor neutro de momento às oportunidades em Prospecting. O lead score também é uma heurística baseada no histórico disponível e ainda precisaria ser validado com o uso real do time comercial.

Considerando cada nova solicitação, validação ou correção como uma iteração, foram necessárias aproximadamente 46 rodadas de interação até chegar à versão atual. Essas rodadas podem ser agrupadas em sete grandes ciclos: entendimento do problema, definição da arquitetura, construção do primeiro protótipo, simplificação do score, revisão da linguagem, inclusão das análises gerenciais e validação final da experiência de uso.

### Onde a IA errou e como corrigi
- Ao formatar e incluir o indicador de "valor potencial" houve uma confusão no entendimento e na definição da nomenclatura. Aqui foi identificado que o melhor seria mostrar ao usuário dois indicadores: Valor Potencial e Receita Esperada. Sendo o "valor potencial", o valor do produto vinculado a oportunidade e "receita esperada" o valor estimado que um determinado vendedor poderia trazer para a empresa com base nas informações históricas.

### O que eu adicionei que a IA sozinha não faria
- Cálculo do score do vendedor com base na região: a região pode influenciar no percentual de venda/perda, portanto esta informação deve ser considerada na fórmula;
- Cálculo do score para perda/repescagem: um segundo "lead score" porém para oportunidades perdidas. Por mais que a oportunidade foi perdida, não quer dizer que o vendedor deva desistir da venda sendo assim foi incluída um "lead score" para que seja possível priorizar a "repescagem" de uma oportunidade
- Repescagem para vendedor da mesma região: uma regra que indica ao manager/revops se a oportunidade perdida pode ser reativa e distribuída a outro vendedor da região com melhor performance para determinado produto.

## Evidências

- [x] [Registro das interações com o Codex](process-log/screen-record/interacoes-com-codex.md)
- [x] [Screen recording do workflow](process-log/screen-record/screen-record-codex.md)
- [x] [Narrativa completa do processo](process-log/story.md)
- [x] Git history da aplicação

## Setup e execução

- Node.js 22.13 ou superior;
- npm, instalado junto com o Node.js;
- acesso à internet durante a primeira instalação;
- porta `3000` disponível.

### Primeira execução

Partindo da raiz do repositório:

```bash
cd submissions/allysonassuncao/solution
npm ci
npm run dev
```

### Próximas execuções

```bash
cd submissions/allysonassuncao/solution
npm run dev
```

### Testes e build

```bash
cd submissions/allysonassuncao/solution
npm test
npm run build
```

Submissão enviada em: 31/08/2026
