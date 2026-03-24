# Submissão — [Lucas Oriani] — Challenge [AI Master]

## Sobre mim

- **Nome:Lucas Oriani Carreira**
- **LinkedIn:https://www.linkedin.com/in/lucas-oriani-carreira/**
- **Challenge escolhido:data-001-churn**

---

## Executive Summary

Desenvolvi um modelo de churn utilizando BigQuery ML com foco não apenas na predição, mas na explicabilidade e acionabilidade por conta. 
Identifiquei que o churn está fortemente aumento de tickets e sua resolubilidade. 
Estruturei um score de churn por account_id junto com decomposição por feature importance, permitindo entender o “porquê” do risco.
A principal recomendação é implementar ações segmentadas por driver de churn, priorizando quick wins de retenção em contas de alto risco junto de estruturantes de médio e longo prazo.

---

## Solução

Modelo supervisionado boosted_tree_classifie

### Abordagem

Comecei estruturando a base analítica consolidada (model_base) com variáveis.

Modelei o churn com BigQuery ML utilizando árvore (modelo explicável)
Extraí probabilidades de churn por conta (churn_probability)
Transformei em score (0–100) para facilitar consumo pelo negócio
Analisei feature importance (gain, weight, cover) para entender drivers
Estruturei a saída final por account_id com score + drivers

Priorizei explicabilidade e usabilidade pelo time de negócio, evitando modelos “black box”.


### Resultados / Findings

1. Modelo de churn por conta

Geração de probabilidade de churn individual (account_id)
Score padronizado (0–100) para priorização

2. Drivers principais de churn

Variáveis comportamentais (ex: queda de uso recente) têm maior importância
Baixo engajamento recente é mais relevante que perfil demográfico
Feature importance mostra concentração em poucas variáveis-chave (modelo eficiente)

3. Estrutura analítica acionável

Tabela final com:
account_id
churn_probability
churn_score
contribuição das principais features

4. Insight crítico
Não basta saber quem vai churnar — é essencial saber por quê.



### Recomendações

1. Ações Curto Prazo

  1.1 Error_rate_per_usage (Erros por uso)- Diminuir erros técnico com atendimento ativo e preditivo
  1.2 Ticket_Count (Nº tickets) - Sanar causa raiz de abertura de tickets
  1.3 Avg_resolution_time_hours (Tempo de resolução) - Reorganizar e redimensionar o time de suporte para diminuir tempo de resolução e Focar em clientes mais rentáveis, criar atendimento dedicado
  1.4 Criar uma matriz RACCI- Plano de comunicação em caso de incidente
  1.5 Dashboards e alertas realtime
  1.6 Adicionar churn e métricas correlatas ao plano de metas (PLR)
  1.7 Rever estrutura organizacional e gestão
    1.7.1 O problema evoluiu ao longo de 2024
    1.7.2 Falta de urgência /  ownership

2. Ações de Médio Prazo

 2.1 Criar célula de pós-retenção - Atendimento próximo durante quarentena
 2.2 Canais de atendimento com o score de churn do cliente que estão atendendo - Descriminado por pontos de atrito
 2.3 Criar célula de retenção pró-ativa - Se o score do cliente subir, alarma e o time ativamente atende e “desatrita” o cliente
 2.4 Backlog de produto e CS alimentados via modelo 
 2.5 No roadmap dessas áreas deve ter prioridade correção de incidentes ligados ao churn
 2.6 Agente supervisor de qualidade
   2.6.1 Analisa os tickets abertos
   2.6.2 Cruza com transcrições 
   2.6.3 Avalia se o atendimento foi eficaz e resolutivo


3. Ações Longom Prazo

 3.1 Modelo de correção de erros on demand
 3.2 Copiloto de atendimento
   3.2.1 Usando dados do agente supervisor de qualidade 
   3.2.2 Gera recomendação de atendimento para novos tickets similares
   3.2.3 Expor na tela do atendente em tempo de atendimento
     3.2.3.1 Ou até dar autonomia de um agente aplicar correção

### Limitações

Melhor definição de churn nas bases
Modelo baseado em correlação (não causalidade)
Dependência da qualidade e granularidade das variáveis disponíveis
Não foram implementadas ações reais de retenção (sem validação experimental)
Feature importance não explica interações complexas entre variáveis


---

## Process Log — Como usei IA
Os prompts utilizados estão documentados em `process/chatgpt_prompts.md`, incluindo como cada output foi aplicado na análise.

Utilizei o ChatGPT 5.3 para estruturar a análise, definir a abordagem do problema e apoiar na explicação das métricas do modelo, além de auxiliar na interpretação das feature importance e na geração de insights de negócio. 
E BigQuery ML para o treinamento do modelo de churn, permitindo construir e avaliar o modelo diretamente sobre a base de dados.                         


### Ferramentas usadas

| Ferramenta     | Para que usou                                                            |
| -------------- | ------------------------------------------------------------------------ |
| ChatGPT        | Estruturação da análise, definição de abordagem e explicação de métricas |
| BigQuery ML    | Treinamento do modelo de churn                                           |
| SQL (BigQuery) | Construção da base e extração dos resultados                             |
| IA (ChatGPT)   | Interpretação de feature importance e geração de insights                |


### Workflow

_Descreva passo a passo como você trabalhou. Onde a IA entrou em cada etapa?_

Estruturei a base de dados consolidada para modelagem
Treinei o modelo de churn no BigQuery ML
Extraí probabilidades e construí o churn score
Analisei feature importance para identificar drivers
Usei IA para refinar explicações e transformar resultados em recomendações de negócio

### Onde a IA errou e como corrigi

Primeiro modelo que fiz foi com regressão logistica, não teve bons resultados e seria dificil trangibilizar para o negócio.
Substitui por árevore de decisão
As propsotas de como aplicar o modelo  na operação do negócio eram muito genericas inicialmente


### O que eu adicionei que a IA sozinha não faria

- Proposta de novo modelo
- Priorização de explicabilidade sobre complexidade do modelo
- Definição de ações práticas de retenção com foco em produto
- Estruturação da saída para uso real (account-level + drivers)


---

## Evidências

- https://github.com/lucasoriani/ai-master-challenge/blob/main/master_table.sql
- https://github.com/lucasoriani/ai-master-challenge/blob/main/model%20tree.sql
- https://github.com/lucasoriani/ai-master-challenge/blob/main/modelo_tree_feature.sql
- https://github.com/lucasoriani/ai-master-challenge/blob/main/g4%20case%20AI%20master.pdf
- https://chatgpt.com/share/69c19697-9ac8-8010-84a9-f7bd1e7f560f

- [ ] Screenshots das conversas com IA
- [ ] Screen recording do workflow
- [x] Chat exports
- [x] Git history (se construiu código)
- [ ] Outro: _____________

---

_Submissão enviada em: 23/03/2026
