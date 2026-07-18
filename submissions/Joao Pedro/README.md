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

### Ferramentas usadas
- **Antigravity (Gemini 3.1 Pro)**: Análise dos dados, escrita dos scripts de modelagem, desenvolvimento do Dashboard (Streamlit/Flask) e do script gerador de PDF.

| Ferramenta | Para que usou |
| --- | --- |
| Gemini 3.1 Pro | Desenvolvimento ponta a ponta: exploração, engenharia de features, modelagem, criação do dashboard e da documentação. |

### Workflow
A IA foi utilizada de forma pareada (Pair Programming Agentic). A cada fase da análise, o contexto dos dados foi fornecido e a IA desenhou e executou os scripts. Posteriormente, a IA foi orientada a criar uma interface visual. Por fim, a IA ajudou a documentar o manual e organizar a entrega final.

### Onde a IA errou e como corrigi
Durante a construção da IA, não houve falhas graves. No entanto, foi preciso guiar a IA para não alterar scripts concluídos sem necessidade. A arquitetura das pastas foi ajustada no final para seguir o formato de submissão.

### O que eu adicionei que a IA sozinha não faria
A definição do escopo de negócios e o direcionamento de usar IA como um diferencial para a equipe de CS.
