# Process Log - Jornada do Projeto

Este documento registra cada etapa da construção do projeto, incluindo decisões, ferramentas utilizadas e aprendizados.

---

<details>
<summary><strong>📋 01. Setup Inicial - Criação da Estrutura de Log</strong> | 09 Mar 2026 | 18:02</summary>

### Objetivo da Etapa

Estabelecer um sistema de documentação estruturado para registrar a jornada completa do projeto, permitindo rastreabilidade de decisões, ferramentas utilizadas e evolução do pensamento durante o desenvolvimento.

### Ferramenta/IA Usada

- **GitHub Copilot** (Claude Haiku 4.5)
- **Git** (Versionamento)
- **VS Code** (Editor)

### Prompt ou Instrução Dada

> "Quero criar um arquivo 01-ProcessLog.md que funcione como um diário do projeto. Cada commit será uma seção nova no formato dropdown, contendo:
>
> - Título + Data/hora
> - Objetivo da etapa
> - Ferramenta/IA usada
> - Prompt ou instrução dada
> - Saída obtida
> - O que aproveitei
> - O que descartei
> - Próxima decisão"

### Saída Obtida

Criação de um template estruturado em Markdown com seções em dropdown (`<details>/<summary>`) que permite:

- Manter o documento limpo e navegável
- Consultar informações passadas sem poluição visual
- Rastrear a evolução das decisões tomadas
- Documentar pontos de virada do projeto

### O que Aproveitei

- Estrutura em dropdowns para melhor organização e legibilidade
- Uso de emojis para rápida identificação visual de cada etapa
- Formatos estruturados que facilitam análise posterior
- Versionamento com Git para histórico completo

### O que Descartei

- Estrutura de múltiplos arquivos (uma seção por arquivo) - menos prático
- Formato de simples lista - pouco profissional e difícil de manter organizado
- Documentação sem rastreabilidade de data/hora - não permite análise temporal

### Próxima Decisão

Iniciar o processo de análise do desafio e definir a estratégia de solução para o problema a ser resolvido.

</details>

---

<details>
<summary><strong>🎯 02. Escolha do Desafio e Planejamento Inicial</strong> | 09 Mar 2026 | 18:37</summary>

### Objetivo da Etapa

Selecionar o desafio a ser desenvolvido (Challenge 002 — Redesign de Suporte) e criar um checklist estruturado de informações necessárias para guiar todo o processo de construção do projeto.

### Ferramenta/IA Usada

- **ChatGPT** (Planejamento e estruturação)
- **GitHub Copilot** (Documentação)
- **Git** (Versionamento)

### Prompt ou Instrução Dada

> "Vou escolher o Challenge 002 — Redesign de Suporte. Nessa próxima etapa eu criei um checklist de informações para criar o processo de construção do projeto."

**Link completo da conversa:**  
🔗 [ChatGPT - Planejamento Challenge 002](https://chatgpt.com/share/e/69af3bef-f91c-8009-8cae-d8b748904466)

### Saída Obtida

- Definição clara do desafio a ser trabalhado: **Process-002-Support (Redesign de Suporte)**
- Criação de checklist estruturado com todas as informações necessárias para o desenvolvimento
- Mapeamento inicial das etapas do projeto
- Estratégia de abordagem documentada na conversa com ChatGPT

### O que Aproveitei

- Abordagem estruturada com checklist para não perder informações importantes
- Uso de IA para brainstorming e planejamento inicial
- Documentação externa (ChatGPT) vinculada ao processo log para rastreabilidade completa
- Definição clara de escopo antes de iniciar o desenvolvimento

### O que Descartei

- Começar a codificar sem planejamento prévio
- Escolher múltiplos desafios simultaneamente
- Planejamento apenas mental sem documentação

### Próxima Decisão

Analisar os dados do desafio e começar a estruturação da solução técnica, definindo arquitetura e tecnologias a serem utilizadas.

</details>

---

<details>
<summary><strong>🔍 03. Análise do Dataset de Suporte - Mapeamento de Colunas</strong> | 09 Mar 2026 | 19:33</summary>

### Objetivo da Etapa

Realizar análise profunda do dataset de suporte ao cliente para entender o papel de cada coluna no processo operacional e identificar oportunidades de automação. Descoberta de limitação técnica do NotebookLLM (máximo de 500.000 palavras) e pivotagem para uso do Google Gemini para análise.

### Ferramenta/IA Usada

- **Google Gemini** (Análise de dados e classificação de colunas)
- **NotebookLLM** (Tentativa inicial - descartado por limitação técnica)
- **ChatGPT** (Suporte adicional)
- **GitHub Copilot** (Documentação)

### Prompt ou Instrução Dada

**Pergunta 1:**
> "Analise este dataset de suporte ao cliente. Explique o papel provável de cada coluna no processo operacional de atendimento. Classifique cada coluna em uma destas categorias:
> - identificador
> - atributo do cliente
> - variável operacional
> - variável de experiência do cliente
> - variável textual
> - variável potencial para automação
> 
> Apresente a resposta em formato de tabela."

**Pergunta 2:**
> "Considerando o objetivo de analisar eficiência operacional e oportunidades de automação no suporte ao cliente, quais colunas são mais críticas para entender o fluxo de atendimento?"

### Saída Obtida

#### Resposta do Gemini - Parte 1: Classificação das Colunas

O Gemini identificou **17 colunas** no dataset e classificou cada uma conforme solicitado:

| Coluna | Papel no Processo Operacional de Atendimento | Categoria |
|--------|----------------------------------------------|-----------|
| **Ticket ID** | Funciona como o código de rastreamento único de cada chamado. Permite que o cliente e os agentes encontrem rapidamente o histórico e acompanhem o caso. | identificador |
| **Customer Name** | Usado para a comunicação e saudação com o cliente. Ajuda a humanizar o atendimento chamando-o pelo nome. | atributo do cliente |
| **Customer Email** | Canal principal de contato de retorno (para e-mails) e também como chave de busca secundária para o perfil e histórico de solicitações do usuário. | atributo do cliente |
| **Customer Age** | Pode ser usado para contextualizar a abordagem, permitindo ao agente adotar um tom de voz ou nível de didática técnica mais apropriado. | atributo do cliente |
| **Customer Gender** | Contribui para traçar o perfil demográfico da base de clientes e auxilia no uso correto de pronomes durante a comunicação personalizada. | atributo do cliente |
| **Product Purchased** | Indica de qual produto o cliente está falando, permitindo que o ticket seja direcionado a um agente especializado na categoria daquele produto. | variável operacional |
| **Date of Purchase** | Crucial para validar a elegibilidade do cliente a serviços de garantia, trocas, devoluções e verificar o ciclo de vida do equipamento. | variável operacional |
| **Ticket Type** | (Ex: Dúvida, Problema Técnico). Define a grande categoria do chamado, influenciando o roteamento e direcionando os KPIs da operação. | variável operacional |
| **Ticket Subject** | É o "assunto" que funciona como o resumo principal da solicitação. Usado pelo agente de triagem para bater o olho e entender rapidamente do que se trata o problema. | variável textual |
| **Ticket Description** | Contém o relato completo (texto livre) escrito pelo cliente. É aqui que algoritmos de IA podem ser aplicados para análise de sentimentos, respostas automáticas via chatbots ou auto-roteamento (NLP). | variável potencial para automação |
| **Ticket Status** | (Ex: Aberto, Pendente, Fechado). Controla em que etapa do fluxo de trabalho o chamado se encontra, sendo vital para gestão das filas de atendimento e SLAs. | variável operacional |
| **Resolution** | Relato de como o chamado foi resolvido. Serve de registro histórico para auditorias e para retroalimentar bases de conhecimento (FAQs). | variável textual |
| **Ticket Priority** | Define a urgência da solicitação. Garante que problemas críticos passem à frente na fila para não violar acordos de tempo de serviço. | variável potencial para automação |
| **Ticket Channel** | Indica a origem do chamado (Chat, E-mail, Redes Sociais). Permite gerenciar a alocação de equipe por canal. | variável operacional |
| **First Response Time** | Tempo que a operação demorou para dar a primeira resposta ao cliente. Métrica essencial de controle de performance de SLA. | variável operacional |
| **Time to Resolution** | O tempo total utilizado para solucionar a demanda e fechar o ticket. Indica a eficiência global da equipe e gargalos. | variável operacional |
| **Customer Satisfaction Rating** | A nota final (CSAT) dada pelo cliente após o atendimento. Termômetro principal do nível de excelência do serviço. | variável de experiência do cliente |

#### Resposta do Gemini - Parte 2: Colunas Críticas para Análise

**1. Colunas Críticas para Eficiência Operacional:**
- **Time to Resolution**: Principal métrica de eficiência. Identifica gargalos e tipos de problemas que travam o fluxo.
- **First Response Time**: Avalia agilidade em acolher o cliente. Tempos altos indicam filas longas ou falta de equipe.
- **Ticket Status**: Mapeia o estado atual do fluxo. Análise histórica identifica chamados "presos" em áreas específicas.
- **Ticket Channel**: Fundamental para dimensionar equipe corretamente por canal de entrada.
- **Ticket Priority**: Mostra como o fluxo está sendo ordenado. Garante resolução prioritária de chamados críticos.

**2. Colunas Críticas para Oportunidades de Automação:**
- **Ticket Description**: Mina de ouro da automação. NLP pode identificar problemas reais, extrair entidades e sugerir respostas automáticas.
- **Ticket Subject** e **Ticket Type**: Cruciais para automação de triagem e roteamento inteligente sem intervenção humana.
- **Resolution**: Textos de resolução formam base de conhecimento para treinar LLMs e chatbots.
- **Product Purchased**: Permite criar fluxos de autoatendimento específicos por produto.

**Resumo da Dinâmica:**
Usar variáveis de automação (Description, Subject, Product) para resolver chamados simples ou repassá-los inteligentemente, consequentemente melhorando variáveis de eficiência operacional (reduzindo First Response Time e Time to Resolution) e desafogando a equipe.

**📸 Evidências Visuais:**
- [Print da Análise Gemini](prints/gemini.google.com-Google%20Gemini-fpscreenshot.jpeg)

### O que Aproveitei

- Classificação estruturada das 17 colunas em categorias claras
- Identificação precisa de variáveis críticas para eficiência vs. automação
- Insights sobre como automatizar triagem e roteamento via NLP
- Compreensão da dinâmica entre variáveis de automação e métricas operacionais
- Tabela completa como referência para próximas etapas de engenharia de features

### O que Descartei

- Uso do NotebookLLM devido à limitação de 500.000 palavras
- Análise superficial sem categorização detalhada
- Foco apenas em métricas sem considerar potencial de automação
- Análise isolada sem entender a inter-relação entre as colunas

### Próxima Decisão

Realizar análise exploratória de dados (EDA) focada nas colunas críticas identificadas, especialmente nas variáveis textuais (Description, Subject, Resolution) para descobrir padrões e oportunidades concretas de automação.

</details>

---

<details>
<summary><strong>🔧 04. Auditoria de Qualidade de Dados - Sanitização e Diagnóstico</strong> | 09 Mar 2026 | 20:01</summary>

### Objetivo da Etapa

Realizar auditoria estrutural completa do dataset `customer_support_tickets` para identificar problemas de qualidade de dados (valores ausentes, duplicações, inconsistências) que possam comprometer as análises. Testar diferentes ferramentas e abordagens para sanitização e análise em escala.

### Ferramenta/IA Usada

- **ChatGPT** (Análise estrutural com Python - ESCOLHIDA)
- **ChatGPT Agent Mode** (Tentativa inicial - descartado por lentidão)
- **Google Gemini** (Tentativa - descartado por limitação de context length)
- **Airtable** (Tentativa - descartado por perda massiva de dados: 8 linhas de 30.000)
- **GitHub Copilot** (Documentação)

### Prompt ou Instrução Dada

**Contexto do problema:**
> "Estou sanitizando as tabelas enviadas pois há dados inconsistentes, estou pedindo para o ChatGPT estruturar e analisar utilizando Python."

**Solicitação principal:**
> "Pedi para fazer uma análise geral da tabela customer_support_tickets"

**Análise solicitada:**
> Auditoria estrutural verificando cinco dimensões críticas de qualidade de dados:
> - Ausência de valores
> - Duplicação
> - Consistência de formato
> - Valores fora de faixa
> - Padrões suspeitos

**Link completo da conversa:**  
🔗 [ChatGPT - Auditoria de Qualidade de Dados](https://chatgpt.com/share/e/69af50d3-1e98-8009-b050-88a7892fa829)

### Saída Obtida

#### Tabela de Diagnóstico Completo

| Coluna | Valores nulos | % nulos | Valores únicos | Duplicações | Possíveis problemas |
|--------|---------------|---------|----------------|-------------|---------------------|
| Ticket ID | 0 | 0% | 1000 | 0 | nenhum problema evidente |
| Customer Name | 0 | 0% | 1000 | 0 | nenhum problema evidente |
| Customer Email | 0 | 0% | 1000 | 0 | nenhum problema evidente |
| Customer Age | 0 | 0% | 53 | 947 | nenhum problema evidente |
| Customer Gender | 0 | 0% | 3 | 997 | nenhum problema evidente |
| Product Purchased | 0 | 0% | 5 | 995 | nenhum problema evidente |
| Date of Purchase | 0 | 0% | 367 | 633 | nenhum problema evidente |
| Ticket Type | 0 | 0% | 4 | 996 | nenhum problema evidente |
| Ticket Subject | 0 | 0% | 1000 | 0 | nenhum problema evidente |
| Ticket Description | 0 | 0% | 1000 | 0 | nenhum problema evidente |
| Ticket Status | 0 | 0% | 3 | 997 | nenhum problema evidente |
| **Resolution** | **505** | **50.5%** | 495 | 505 | **valores ausentes** |
| Ticket Priority | 0 | 0% | 3 | 997 | nenhum problema evidente |
| Ticket Channel | 0 | 0% | 4 | 996 | nenhum problema evidente |
| **First Response Time** | **205** | **20.5%** | 794 | 206 | **valores ausentes** |
| **Time to Resolution** | **205** | **20.5%** | 794 | 206 | **valores ausentes** |
| **Customer Satisfaction Rating** | **205** | **20.5%** | 5 | 205 | **valores ausentes** |

#### Principais Problemas Identificados

**1️⃣ Ausência sistemática de dados em colunas de resultado**

**Resolution — 50,5% nulos**
- **Cenários possíveis:**
  - Tickets ainda não resolvidos (esperado)
  - Falha de registro da solução (crítico)
- **Impacto:**
  - Perda de base de conhecimento
  - Impossibilidade de treinar sistemas de automação
  - Falta de material para FAQs e chatbots
- **Campo crítico para:** análise de causas, construção de base de conhecimento, automação de respostas

**First Response Time — 20,5% nulos**
- **Possíveis causas:**
  - Ticket resolvido automaticamente
  - Sistema não registrou a primeira resposta
  - Dados vieram de canais diferentes (ex: telefone)
- **Impacto:**
  - Compromete análises de tempo médio de resposta
  - Falha de rastreamento de SLA
  - Impossibilita avaliação de qualidade do atendimento

**Time to Resolution — 20,5% nulos**
- **Causa provável:** Tickets ainda em aberto
- **Inconsistência crítica a verificar:**
  ```
  Se: Ticket Status = "Resolved"
  E: Time to Resolution = null
  Então: INCONSISTÊNCIA GRAVE
  ```

**Customer Satisfaction Rating — 20,5% nulos**
- **Causas comuns:**
  - Cliente não respondeu à pesquisa
  - Ticket ainda não finalizado
- **Risco:** **Viés de avaliação** — clientes insatisfeitos respondem mais frequentemente, distorcendo métricas

**2️⃣ Distribuições altamente repetidas (NORMAL)**

Colunas com alta duplicação são esperadas em sistemas operacionais:

| Coluna | Motivo |
|--------|--------|
| Customer Gender | Poucas categorias possíveis |
| Product Purchased | Catálogo limitado |
| Ticket Type | Classificação operacional |
| Ticket Priority | Níveis de urgência |
| Ticket Channel | Poucos canais de entrada |

✅ **Não é problema estrutural**

**3️⃣ Verificações de faixa de valores**

**Não foram encontrados:**
- ❌ Idades negativas
- ❌ Idades acima de 100
- ❌ Avaliações fora da escala 1–5
- ❌ Tempos negativos

✅ **Sem valores absurdos evidentes**

**4️⃣ Integridade dos identificadores**

**Ticket ID:**
- ✅ Nenhum valor nulo
- ✅ Nenhum duplicado
- ✅ **Boa integridade de chave primária**

**5️⃣ Campos textuais sem anomalias estruturais**

**Campos:** Ticket Subject, Ticket Description, Resolution
- ✅ Sem duplicações excessivas
- ✅ Sem campos vazios inesperados (exceto Resolution)
- ✅ **Positivo para análises de NLP e automação**

#### Problemas que Comprometem Análises

**🚨 Crítico 1: Métricas de SLA incompletas**
- **Campos afetados:** First Response Time, Time to Resolution
- **Consequência:** Impossível medir desempenho real do suporte e produtividade

**🚨 Crítico 2: Conhecimento operacional incompleto**
- **Campo afetado:** Resolution
- **Consequência:** Perda de base de conhecimento, aprendizado organizacional e material para automação

**🚨 Crítico 3: Viés em análise de satisfação**
- **Campo afetado:** Customer Satisfaction Rating
- **Consequência:** Clientes moderadamente satisfeitos não respondem pesquisas, inflando/distorcendo indicadores

#### Diagnóstico Geral

**Qualidade estrutural:** ✅ BOA  
**Qualidade analítica:** ⚠️ MODERADA

**Conclusão:**
> O dataset está bem estruturado, porém algumas métricas de resultado estão incompletas.
> 
> **Em termos práticos:**
> - Análise operacional → **possível**
> - Análise de experiência do cliente → **exige tratamento de nulos**

### O que Aproveitei

- **Tabela de diagnóstico completa** coluna por coluna com percentuais de nulos
- Identificação de **3 problemas críticos** que podem comprometer análises
- Entendimento sobre **quando duplicações são normais** vs. quando são problemas
- Verificação de **integridade de chave primária** (Ticket ID)
- Insights sobre **viés de satisfação** quando há dados faltantes
- Confirmação de que **campos textuais estão íntegros** para NLP
- Metodologia de auditoria estrutural replicável para outros datasets

### O que Descartei

- **ChatGPT Agent Mode:** Demora excessiva para análises em escala
- **Google Gemini:** Limitação de context length impediu análise completa
- **Airtable:** Perda massiva de dados (8 linhas retornadas de 30.000 originais) - inviável para datasets grandes
- Análise sem verificação de integridade referencial (Status vs. Time to Resolution)
- Assumir que campos nulos são sempre problemas (alguns são esperados)

### Próxima Decisão

Definir estratégia de tratamento de dados ausentes (imputação vs. exclusão) e verificar inconsistências críticas (tickets "Resolved" sem Time to Resolution). Preparar dataset limpo para análise exploratória (EDA) focada em padrões textuais e métricas operacionais.

</details>

---
