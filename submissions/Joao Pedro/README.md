# Submissão — João Nunes — Challenge RavenStack Churn Analysis

## Sobre mim
- **Nome:** João Pedro Nunes
- **LinkedIn:** www.linkedin.com/in/jaypi
- **Challenge escolhido:** G4 Churn Challenge (RavenStack)

## Executive Summary
Foi realizada uma análise completa da base de dados de clientes da RavenStack para entender os motivos de churn e identificar perfis de risco. Através da exploração de dados, engenharia de features e modelagem preditiva, identificou-se que o uso das funcionalidades (especialmente nos últimos 30 dias) e o tempo de resolução de tickets são os principais preditores de cancelamento. Foi desenvolvido um Dashboard Interativo contendo um Analista Virtual IA, capaz de responder perguntas sobre os dados utilizando LangChain, permitindo um monitoramento contínuo e inteligente.

## Solução
A solução foi dividida em duas grandes entregas:
1. **Pipelines de Análise de Dados (Python):** Scripts segmentados em fases para limpeza, cruzamento de dados, teste de hipóteses e criação de um modelo de risco. A base final consolidada é a \master_table.csv\.
2. **Dashboard Interativo & IA:** Um aplicativo desenvolvido em Streamlit (\pythonapp.py\) e uma versão em Flask (\flask_app.py\). O Streamlit possui gráficos (Plotly) de taxa de churn e uso, além de uma integração com a OpenAI via LangChain, onde o usuário pode conversar com os dados da tabela em linguagem natural.

## Abordagem
O projeto iniciou com o carregamento e tratamento exploratório. Em seguida, os dados foram unificados em uma visão 360 do cliente, consolidando atributos de CRM, uso de produto e suporte. Formulamos hipóteses de negócio focadas em engajamento e atendimento, e as validamos. Após isso, features adicionais foram extraídas e um modelo de predição de risco de churn foi implementado. Por fim, encapsulamos os insights e a base final em um Dashboard para consumo por stakeholders, incorporando IA Generativa para facilitar a geração de insights 'on-the-fly'.

## Resultados / Findings
- **Uso do Produto:** Clientes com menor atividade nos últimos 30 dias apresentam risco acentuado de churn.
- **Atendimento ao Cliente:** Tempos altos de resolução de tickets correlacionam positivamente com cancelamentos.
- **Ferramenta de IA:** O agente construído demonstrou ser muito eficaz na tradução de perguntas de negócios em código e respostas diretas.

## Recomendações
1. **Ação Proativa Baseada em Uso:** Criar alertas automatizados no CRM para contas cujo uso caia abaixo do limiar crítico identificado, disparando campanhas de reengajamento.
2. **Priorização de Tickets:** Reduzir SLAs de tempo de resolução para clientes com alto MRR, dado o impacto do suporte na retenção.
3. **Adoção do Dashboard:** Expandir o uso da ferramenta com Chatbot LLM para as equipes de Customer Success e Vendas.

## Limitações
- A ferramenta de IA (LangChain Pandas Agent) exige precauções (como sandboxing) para mitigar riscos de segurança ao executar código em produção.
- Seria interessante integrar diretamente no CRM no futuro, ao invés de apenas rodar sobre arquivos exportados.

## Process Log — Como usei IA

Esta seção documenta em detalhes o ciclo de desenvolvimento iterativo realizado em *Pair Programming* com a Inteligência Artificial. Para fins de auditoria, uma versão completa e independente em texto puro também foi salva na pasta `process-log/process_log.md`.

### Ferramentas usadas e Por Quê
1. **Agente Antigravity (IA Codificadora):** Utilizado como engenheiro de dados, cientista de dados e desenvolvedor Full-Stack. O racional foi acelerar a etapa braçal (ETL, montagem de CSV) para que pudéssemos focar no valor analítico e na prototipação rápida.
2. **LangChain (Pandas DataFrame Agent) + OpenAI (GPT-4o-mini):** Utilizados *dentro do produto final*. Racional: Permitir que o CEO faça perguntas estatísticas não roteirizadas (ex: "Quantos clientes da indústria FinTech deram churn?") e obtenha respostas imediatas através da base final processada.

### Como o problema foi decomposto antes de promptar
A solução não foi pedida em um único prompt mágico. O problema foi particionado em 5 fases (Scripts de 1 a 5):
1. **Fase 1 (ETL):** Mapear as 5 bases de dados CSV e entender a integridade referencial.
2. **Fase 2 (Feature Engineering & O Paradoxo Temporal):** Ao invés de somar o uso *lifetime* (que esconderia o problema real), dividimos o uso em `usage_last_30` vs histórico. O prompt foi: *"Crie features que meçam o uso dos últimos 30 dias em comparação ao período anterior para testar o paradoxo de uso que o CEO relatou"*.
3. **Fase 3 e 4 (Modelagem Preditiva):** Treinar um modelo algorítmico (Scikit-Learn Random Forest) para evitar *achismos* e ranquear as colunas que matematicamente mais pesam no churn.
4. **Fase 5 (Dashboard & Web App):** Empacotamento do resultado cruzado com uma LLM.

### Prompts Reais e Decisões Tomadas
- **Prompt (Decisão Financeira):** *"O CEO quer saber quem está em risco. Não trate todos os churns igualmente. Multiplique a probabilidade de churn gerada pelo modelo pelo `current_mrr` para extrairmos os top 15 clientes em perigo imediato."*
  - **Racional Técnico:** Uma visão orientada a "Risco de Caixa" é muito mais acionável para a liderança do que simplesmente contar clientes.
- **Prompt (Migração Arquitetural):** *"Vamos mudar esse desenvolvimento em Streamlit para Flask. Crie um frontend do zero em Vanilla CSS com identidade da G4 Business School."*
  - **Racional Técnico:** Embora o Streamlit seja ótimo para POCs, migrar para Flask + HTML/JS provou ser necessário para garantir isolamento assíncrono do chatbot e customização estética ilimitada que *frameworks* engessados não permitem.

### Onde a IA errou e como foi corrigido
1. **Erro de Ambiente (Background Task):** A IA falhou inicialmente ao tentar rodar a instalação silenciosa das bibliotecas Python devido ao limite do PATH do Windows no terminal isolado do *Sandbox*.
   - **Correção (Humano+IA):** Intervenção no prompt para rodar o comando explícito: `python -m pip install`.
2. **Erro Analítico (Overfitting em Região):** Em certo momento, a IA atribuiu alto peso de churn a determinados países pela amostragem pequena, gerando ruído linear.
   - **Correção:** Orientamos a focar o Random Forest estritamente em colunas *comportamentais* e financeiras, removendo dados geográficos dispersos e aumentando o rigor do modelo.

### O que foi adicionado que a IA sozinha não faria
A IA pura classificaria risco (0 ou 1) ou geraria gráficos padrões estáticos (Roxo/Azul). A intervenção e refinamento de produto envolveu:
1. **O Refinamento do "Microcopy":** A IA usava nomenclaturas difíceis para os gráficos (ex: "churn_flag: True/False"). Foi instruída a usar "Status do Cliente: Cancelou / Ativo".
2. **Adaptação Identidade Corporativa:** Instruir ativamente o CSS a incorporar a paleta profunda Vermelho (`#FF1A1A`) e Preto da G4 Educação e não a sugerida pela base técnica.

### Quantas iterações foram necessárias
Cerca de **6 iterações iterativas profundas**. Desde a concepção da Tabela Mestre, refutação da hipótese dos clientes "Beta", cálculo de probabilidade de risco, elaboração da UI em Streamlit e refatoração completa para Flask/JS assíncrono.
