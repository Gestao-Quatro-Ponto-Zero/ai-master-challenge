# 📝 Registro de Processo — Engenharia Assistida por IA

**Candidato:** Paulo Sérgio Oliveira da Silva Júnior  
**Desafio:** Diagnóstico de Churn da RavenStack  

---

## 🎯 1. Ferramentas de IA Utilizadas e Por Quê

*   **Gemini (Google):** Utilizado como parceiro principal de desenvolvimento (*pair programming* e *business sparring*). A escolha se deu pela capacidade do modelo de processar contexto de negócios complexo, validar formatação de dados e auxiliar na tomada de decisões estratégicas de produto/engenharia a partir de dados brutos.

---

## 💡 2. Como o Problema foi Resolvido (Antes da IA)

Antes de iniciar as interações com a IA, fiz uma análise estrutural preliminar das 5 bases de dados fornecidas (`ravenstack_...`). Identifiquei que:
1. Havia uma grande perda de receita acumulada (faturamento recorrente mensal vazando).
2. O time de produto estava olhando para métricas agregadas (médias de uso diário) que não indicavam queda de engajamento antes do cancelamento, o que parecia um paradoxo.
3. Formulei a hipótese de que o Churn na RavenStack era **reativo** (motivado por frustrações pontuais, como bugs ou falta de ferramentas), e não progressivo.

Com essas hipóteses de negócio desenhadas, utilizei a IA para refinar a análise técnica e validar essas suposições matematicamente.

---

## 🔄 3. Iterações e Onde a IA Errou (Como Corrigi)

O desenvolvimento não foi um processo de "um único prompt". Houve refinamento mútuo:

*   **Modelagem de Risco Simples vs. Ponderada:** Inicialmente, a IA sugeriu monitorar apenas a volumetria bruta de uso diário para prever o Churn. Eu intervim, pontuando que os dados de uso de clientes churnados eram visualmente idênticos aos de clientes ativos (o Paradoxo do "Uso Saudável"). 
*   **A Correção:** Instruí a IA a cruzarmos os dados de uso com os dados de **erros logados** e **histórico de chamados de suporte**. Juntos, criamos a heurística do **Risk Score (0 a 2)**, que pontua como risco crítico (Score 2) apenas o cliente que tem uso decrescente *combinado* com uma alta taxa de erro diário recente (experiência técnica frustrante).

---

## 🧠 4. O que eu adicionei (Que a IA sozinha não faria)

Embora a IA tenha ajudado a estruturar o pipeline em Pandas e a polir o código, o **direcionamento de negócios** partiu inteiramente do meu julgamento:

*   **Viés do Sobrevivente no CSAT:** Identifiquei que o CSAT "saudável" apresentado pelo time de CS era enganoso porque ignorava os clientes que já haviam cancelado. Traduzi essa análise de dados fria em um conceito estratégico vital para o CEO.
*   **Plano de Ação de Emergência (48h / 30 dias / 60 dias):** Desenhei a estratégia prática de contenção focando em ligar imediatamente para as contas de maior MRR que estavam com score crítico, criando um processo acionável que a empresa pode executar no dia seguinte.

---

## 🛠️ 5. Limitações Identificadas do Processo

*   A análise atual é puramente histórica e heurística. Para os próximos passos, mapeamos a necessidade de rodar modelos preditivos de Machine Learning (como XGBoost) para automatizar a classificação de risco à medida que novos dados de telemetria forem ingeridos.