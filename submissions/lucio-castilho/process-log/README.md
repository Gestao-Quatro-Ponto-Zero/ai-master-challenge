# Process Log — G4 Lead Scorer

Este documento registra como a IA foi usada durante a resolução do Challenge 003 e, principalmente, onde as hipóteses iniciais foram rejeitadas após verificação nos dados.

## Ferramentas usadas

| Ferramenta      | Uso                                                                                                                |
| --------------- | ------------------------------------------------------------------------------------------------------------------ |
| ChatGPT         | Estruturação do problema, geração de hipóteses, revisão metodológica, assistência no código, testes e documentação |
| Python / pandas | Auditoria e validação quantitativa diretamente nos CSVs                                                            |
| Streamlit       | Construção do MVP web                                                                                              |

## Workflow

### 1. Problema antes da ferramenta

A primeira decisão foi não construir "um modelo de ML" como objetivo. A pergunta operacional escolhida foi:

> O vendedor abre o pipeline na segunda-feira. Em quais oportunidades deve focar primeiro e por quê?

O escopo foi reduzido a uma aplicação web sem autenticação, cadastro ou CRM fictício.

### 2. Auditoria dos dados

A IA inicialmente trabalhou a partir da descrição do dataset, mas a etapa foi reaberta quando os CSVs reais foram disponibilizados.

Verificações realizadas:

- 8.800 oportunidades no pipeline;
- 6.711 encerradas e 2.089 abertas;
- cerca de 68% das oportunidades abertas sem `account`;
- todos os accounts não nulos possuem correspondência;
- inconsistência `GTXPro` vs `GTX Pro`;
- `Prospecting` sem `engage_date`, conforme o significado do campo.

Decisão humana relevante: um score dependente de `account` seria pouco útil no pipeline real, apesar de parecer mais sofisticado historicamente.

### 3. Controle de leakage

Foi estabelecido que `close_date` e `close_value` nunca seriam features do score. Também foi rejeitado o uso de `close_value` como valor potencial para oportunidades abertas.

### 4. Hipóteses de negócio

Foram testados produto, setor, tamanho da empresa, região, manager, vendedor e interações.

Várias hipóteses intuitivas foram rejeitadas:

- produto isolado apresentou pouca diferenciação;
- empresas maiores não converteram de forma monotonicamente melhor;
- região e manager foram sinais fracos;
- combinações como Product × Sector mostraram mais variação, mas dependem de dados ausentes em grande parte do pipeline.

### 5. Tentativa de modelo preditivo

Antes de definir uma fórmula heurística, foram comparados candidatos com split temporal e Lift@10%, Lift@20% e Lift@30%.

Resultado: os modelos supervisionados apresentaram AUC próxima de 0,50 e lifts pequenos/instáveis.

#### Onde a IA poderia ter errado

A direção inicial mais óbvia era criar um `Win Score` com Logistic Regression ou Gradient Boosting e colocá-lo no dashboard. Isso produziria um protótipo visualmente convincente, mas não sustentado pelos resultados fora da amostra.

#### Correção

O `Win Score` foi descartado. Historical Fit passou a ser apenas contexto histórico, sem ser vendido como probabilidade de fechamento.

### 6. Redesenho para a dor operacional

A solução foi dividida em duas perguntas:

1. Existe contexto histórico favorável? → `Historical Fit`.
2. Este deal precisa de atenção agora? → `Attention Need`.

A partir disso foi criada uma matriz de decisão com categorias como:

- Focus Now;
- Follow Up;
- Re-engage;
- Requalify;
- Qualify or Drop.

Uma decisão importante foi fazer `Stale` reduzir a urgência numérica comparada à janela de `Urgent Review`, porque um deal extremamente antigo precisa de decisão, não necessariamente de mais esforço.

### 7. Build

A aplicação foi implementada em Python/Streamlit com:

- filtros por vendedor, manager, região, estágio, produto e ação;
- fila priorizada;
- detalhe explicável;
- exportação Excel;
- exportação PDF;
- testes de scoring e leakage.

## Onde a IA errou e como corrigi

1. **Risco de assumir que uso de ML era necessário:** corrigido após validação temporal mostrar sinal insuficiente.
2. **Risco de tratar deal mais velho como sempre pior:** corrigido ao separar janela de follow-up de pipeline stale.
3. **Risco de depender de account:** corrigido após auditoria mostrar ausência em cerca de 68% do pipeline aberto.
4. **Risco de usar close_value como valor potencial:** rejeitado por ser informação posterior ao outcome.
5. **Risco de juntar produtos sem normalização:** identificado e corrigido (`GTXPro` → `GTX Pro`).

## O que eu adicionei que a IA sozinha não faria

O principal julgamento foi não otimizar a solução para parecer "mais IA". A escolha de rejeitar um modelo preditivo fraco e construir uma fila operacional mais simples veio da combinação entre:

- a dor explícita da Head de RevOps;
- as limitações reais do dataset;
- a necessidade de uma ferramenta que alguém realmente consiga usar;
- a preocupação em não apresentar correlação ou score heurístico como probabilidade.

Também foi priorizada a separação entre **necessidade de atenção** e **qualidade da oportunidade**. Um deal com score alto pode precisar ser encerrado, não perseguido; por isso a Action Category tem precedência sobre o número.

## Iterações

As principais iterações foram:

1. ideia inicial de Win Score + Priority Score;
2. auditoria real dos CSVs e mudança para Core + Enriched evidence;
3. teste de sinais individuais e interações;
4. comparação de modelos com split temporal;
5. rejeição do modelo preditivo como motor;
6. definição quantitativa de Attention Need;
7. definição quantitativa de Historical Fit;
8. construção da matriz de Action Category;
9. implementação e testes do dashboard.

## Evidências anexáveis

As pastas abaixo foram deixadas preparadas para evidências adicionais:

- `screenshots/` — capturas das conversas e do app;
- `chat-exports/` — export desta conversa, caso utilizado;
- histórico de commits — evolução do código no Git.

A narrativa deste arquivo já é um formato aceito pelo Guia de Submissão, mas screenshots e histórico de commits reforçam a evidência do processo.

## Ajuste de integração com o repositório

Durante a preparação do build local, foi verificado que o `.gitignore` oficial exclui `datasets/` e `submissions/`. A primeira versão do protótipo carregava os CSVs dentro de `solution/data/`; isso foi corrigido antes da submissão final.

A versão final:

- não versiona nenhum CSV do Kaggle;
- resolve os dados a partir de `datasets/crm-sales-predictive-analytics/` ou `CRM_DATA_DIR`;
- mostra uma mensagem de setup clara quando os dados não estão presentes;
- mantém testes de integração contra a base oficial quando ela está disponível localmente;
- exige `git add -f submissions/lucio-castilho` apenas porque o repositório-base ignora a pasta `submissions/`.

Esse ajuste foi uma verificação de conformidade com as regras do repositório, não uma mudança na lógica analítica da solução.
