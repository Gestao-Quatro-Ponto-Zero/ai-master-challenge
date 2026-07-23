# Manual do Usuário: Dashboard RavenStack Churn & Analytics

## 1. Visão Geral
O Dashboard RavenStack é uma aplicação interativa que fornece insights sobre o uso, suporte e faturamento de clientes, ajudando a identificar riscos reais de churn (cancelamento). O dashboard inclui gráficos dinâmicos e um Analista de Dados Virtual inteligente.

## 2. Como Utilizar o Dashboard

O dashboard está dividido em duas abas principais:

### Aba 1: Visão Geral
Nesta aba, você encontrará métricas consolidadas e gráficos interativos:
- **Métricas Principais**: Visualize a Taxa Global de Churn, MRR (Receita Mensal Recorrente) Médio por Conta e Uso Médio dos últimos 30 dias.
- **Churn por Indústria**: Um gráfico de barras demonstrando a taxa de cancelamento segmentada pelo setor de atuação dos clientes.
- **Uso de Features**: Um boxplot comparando o volume de uso do sistema (últimos 30 dias) entre clientes retidos e clientes que deram churn.
- **Tempo de Resolução**: Comparativo do tempo médio de resolução de tickets de suporte.
- **Visão Detalhada**: Uma tabela completa com os dados individuais dos clientes.

### Aba 2: Chatbot com os Dados (LLM)
Nesta aba, você interage com um Analista de Dados Virtual:
1. **Configuração**: Na barra lateral esquerda ("Configurações"), insira a sua **OpenAI API Key** (Chave de API da OpenAI). Isso é necessário para habilitar a inteligência artificial.
2. **Interação**: Após inserir a chave, utilize a caixa de texto para fazer perguntas em linguagem natural sobre a base de dados (`master_table.csv`).
3. **Respostas**: O agente analisará a pergunta, executará comandos em background e retornará a resposta detalhada baseada nos seus dados reais.


## 3. Como Hospedar e Executar Localmente

Siga os passos abaixo para rodar o dashboard na sua própria máquina.

### Pré-requisitos
- **Python 3.8+** instalado.
- Chave de API da **OpenAI**.

### Passo 1: Preparar o Ambiente
Recomenda-se o uso de um ambiente virtual para evitar conflitos de bibliotecas.
Abra o terminal na pasta do projeto e execute:
- **Windows**: `python -m venv venv` e depois `venv\Scripts\activate`
- **Mac/Linux**: `python3 -m venv venv` e depois `source venv/bin/activate`

### Passo 2: Instalar Dependências
Instale as bibliotecas necessárias. Execute o comando:
`pip install streamlit pandas plotly langchain-experimental langchain-openai`

### Passo 3: Arquivo de Dados
Verifique se o arquivo `master_table.csv` e `app.py` estão no mesmo diretório.

### Passo 4: Executar o Aplicativo
No terminal, certifique-se de estar na pasta do projeto e execute:
`streamlit run app.py`

### Passo 5: Acessar o Dashboard
O Streamlit iniciará um servidor local. O seu navegador padrão deve abrir automaticamente. Caso não abra, acesse a URL: `http://localhost:8501`
