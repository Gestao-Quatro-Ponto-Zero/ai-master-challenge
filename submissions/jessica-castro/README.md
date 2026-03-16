# Submissão --- Jéssica Castro --- Challenge \[build-003-lead-scorer\]

## Sobre mim

**Nome:** Jéssica Castro\
**LinkedIn:** \[www.linkedin.com/in/jessicarcs\]\
**Challenge escolhido:** Desenvolvimento de um sistema de priorização de
oportunidades comerciais baseado em Deal Scoring.


------------------------------------------------------------------------

# Executive Summary

Neste challenge desenvolvi um **sistema de priorização de oportunidades
comerciais baseado em Deal Scoring**, com o objetivo de ajudar equipes
de vendas a identificar rapidamente quais negócios do pipeline merecem
maior atenção.

A solução inclui três componentes principais: - uma **API REST para
análise de oportunidades**,\
- uma **planilha inteligente com fórmulas de scoring para auditoria do
modelo**,\
- e uma **feature de alertas por email que envia os deals mais críticos
do pipeline**.

O principal insight do projeto é que modelos tradicionais de **Lead
Scoring** não resolvem bem o problema de priorização dentro do pipeline.
Por isso a solução foi estruturada como um **Deal Scoring orientado à
fricção do processo comercial**, focado em fatores operacionais como
estágio da negociação, tempo no estágio, presença de decisor se
concorrência.

A recomendação principal é evoluir o modelo atual (heurístico) para um
**modelo supervisionado treinado com histórico real de oportunidades**,
mantendo a camada de explicabilidade e recomendações operacionais.

------------------------------------------------------------------------

# Solução

## Abordagem

O primeiro passo foi entender qual problema de negócio o challenge
estava tentando resolver.

Em vez de focar em **Lead Scoring (priorização de leads no topo do
funil)**, optei por atacar um problema diferente e muitas vezes mais
relevante em vendas B2B: **priorização de oportunidades já existentes no
pipeline**.

A abordagem foi dividida em quatro etapas principais:

1.  Definição do modelo de Deal Scoring
2.  Construção de uma API REST para operacionalizar o modelo
3.  Criação de uma planilha inteligente para auditoria da lógica
4.  Implementação de alertas operacionais para oportunidades críticas

Essa estrutura permite que o sistema funcione tanto como **ferramenta
analítica quanto operacional para times de vendas**.

------------------------------------------------------------------------

# Evolução da solução

Durante o desenvolvimento do challenge, a solução passou por algumas
iterações importantes.

### Versão 1 --- Lead Scoring inicial

A primeira abordagem considerada foi um modelo tradicional de **Lead
Scoring**, focado na priorização de leads no topo do funil.

Esse tipo de modelo normalmente utiliza fatores como: - perfil da
empresa - cargo do contato - comportamento de marketing - engajamento
com conteúdo

Após análise, percebi que essa abordagem não resolveria bem o problema
central do challenge, pois prioriza **entrada no pipeline**, e não
**gestão de oportunidades já abertas**.

Por isso decidi mudar a abordagem.

### Versão 2 --- Deal Scoring

A solução evoluiu então para um modelo de **Deal Scoring**, focado em
avaliar oportunidades já existentes no pipeline.

O modelo passou a considerar fatores como: - valor do negócio - estágio
da oportunidade - presença de decisor - número de concorrentes - tempo
no estágio atual

Essa versão permitiu estimar: - probabilidade de ganho - nível de
fricção do deal - próxima ação recomendada

### Versão 3 --- API de scoring

Foi construída uma **API REST** para operacionalizar o modelo.

Endpoint principal: POST /score

A API recebe os dados de um deal e retorna: - rating - win_probability -
friction - next_action - explanation

### Versão 4 --- Planilha inteligente

Foi criada uma **planilha inteligente com fórmulas equivalentes ao
modelo**, permitindo: - validar o cálculo do score - simular cenários -
explicar o modelo para stakeholders

### Versão 5 --- Sistema de alertas

Foi criado o endpoint:

POST /notify-email

Essa funcionalidade: 1. identifica os deals mais críticos do pipeline\
2. calcula um priority score\
3. envia um resumo por email

------------------------------------------------------------------------

# Arquitetura da solução

A solução foi desenhada como uma arquitetura simples de MVP composta por
três camadas principais:

### 1. Motor de Deal Scoring

Responsável por calcular: - score final - rating - win_probability -
friction - next_action - explanation

### 2. Camada de serviço (API REST)

Endpoints principais: - POST /score - POST /notify-email

### 3. Camada de consumo

Os resultados podem ser utilizados por: - dashboards - planilha
inteligente - alertas por email

Fluxo:

Dados do Deal\
↓\
Motor de Deal Scoring\
↓\
API REST\
↓\
Dashboard / Planilha / Email

------------------------------------------------------------------------

# Resultados / Findings

A solução final inclui:

### API de scoring

Endpoint principal: POST /score

Transforma dados do pipeline em **informação acionável para
vendedores**.

### Planilha inteligente (submissions/jessica-castro/assets/)

Permite: - validar lógica - simular cenários - explicar o modelo

### Sistema de alertas

Endpoint: POST /notify-email

Identifica oportunidades críticas e envia resumo por email.

------------------------------------------------------------------------

# Recomendações

1.  Evoluir o modelo para aprendizado supervisionado (XGBoost, Gradient
    Boosting).
2.  Separar **Friction Index** de **Win Probability**.
3.  Criar motor de recomendações baseado em playbooks de vendas.

------------------------------------------------------------------------

# Limitações

-   Escolha da ferramenta Steamlimit muito limitada na questão UX e componentes de UI.
-   Dataset incial enviado com pouco dados históricos, dados muito básicos e sem informações de tarefas com os deals.


------------------------------------------------------------------------

# Process Log --- Como usei IA

## Ferramentas usadas

  Ferramenta    Para que usei
  ------------- ------------------------------------------
  Claude Code   Implementação de partes do código e da API
  ChatGPT       Estruturação da arquitetura da solução
  ChatGPT       Revisão crítica do modelo
  ChatGPT       Estruturação da documentação

------------------------------------------------------------------------

## Workflow

1.  Análise do problema do challenge
2.  Brainstorm com IA
3.  Definição do modelo de Deal Scoring
4.  Evoluções após encontrar inconsistência nas análises
4.  Construção da API
5.  Criação da planilha
6.  Implementação de alertas por email
7.  Revisão crítica do modelo

------------------------------------------------------------------------

## Onde a IA errou e como corrigi

Algumas sugestões iniciais criavam soluções excessivamente complexas.

- Fiz ajustes importantes como: - mudança de Lead Scoring para Deal
Scoring 
- simplificação da arquitetura 
- inclusão de explicabilidade - mudança de Slack para email - envio manual em vez de automação completa.
- Vários indicações para qual caminho seguir com relação a UX do dashboard.

- A IA não levou muito em conta o AUC do modelo, fiz fiz anáilises e 3 evolução até conseguir extrair o pontencial que considerei máximo para o dataset que eu tinha:

Data	Versão / Evento	CV AUC-ROC	Observação
11/03 14:43	—	0.9787	⚠️ Leakage detectado (close_value)
11/03 14:44	Correção do leakage	0.6022	Baseline real após remover close_value
12/03 01:30	Refinamento features	0.6249	Melhora com features adicionais
12/03 01:39	Ajuste pipeline	0.6240	Estável
12/03 01:40	Ajuste pipeline	0.6241	Estável
12/03 19:36	Experimento	0.6210	Regressão leve
12/03 21:34	Experimento (suspeito)	0.7968 ± 0.0077	⚠️ Possível leakage ou dataset sintético
12/03 21:36	Nested CV	0.5222 ± 0.0163	Validação mais conservadora
12/03 21:37	Nested CV ajustado	0.5162 ± 0.0190	Abaixo do baseline
12/03 21:37	OOF CV — modelo final	0.6742 ± 0.0099	✅ Versão em produção

------------------------------------------------------------------------

## O que eu adicionei que a IA sozinha não faria

-   escolha estratégica de Deal Scoring
-   definição da arquitetura MVP
-   simplificação da solução
-   análise critica dos resultados alcançados, e listagem de melhorias baseado no meu know how sobre a área e regras de negócio.
-   Pedi que a IA fizesse uma auditoria, após encontrar uma sucessão de incosistências nos dados apresentados (g)


------------------------------------------------------------------------

# Evidências

-   Screenshots das conversas com IA
-   Chat exports
-   Código da API
-   Planilha de scoring
-   Git history

------------------------------------------------------------------------

Submissão enviada em: \[16/03/2026\]
