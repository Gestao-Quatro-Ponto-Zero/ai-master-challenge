# DealSignal — Process Log (Uso de IA no desenvolvimento)

Este documento registra os momentos do desenvolvimento do DealSignal em que ferramentas de IA foram utilizadas para acelerar decisões técnicas, investigar problemas e evoluir a arquitetura do sistema. O objetivo não é registrar toda a conversa, mas destacar **interações que influenciaram diretamente o design do produto**.

---

## 1. Definição do modelo de priorização

### Prompt
> "Quero fazer um lead scoring similar ao rating bancário para ter mais precisão. Quais critérios devo analisar?"

**[IMAGEM 1 — Captura_de_Tela_2026-04-09_a_s_22_12_22.png]**

### Resposta resumida da IA
A IA sugeriu estruturar o scoring com múltiplos fatores inspirados em modelos de risco de crédito: histórico de conversão do vendedor, performance do produto, velocidade do pipeline, características da conta e valor do deal. Também propôs criar **ratings em faixas** (AAA, AA, A, BBB, BB, B, CCC), semelhante a ratings financeiros.

A conversa avançou para a estrutura matemática do modelo (Logistic Regression) e métricas de avaliação típicas de fintechs.

**[IMAGEM 2 — Captura_de_Tela_2026-04-09_a_s_22_21_58.png]**
**[IMAGEM 3 — Captura_de_Tela_2026-04-09_a_s_22_23_34.png]**

### Impacto no projeto
Essa exploração levou à criação do conceito central do produto: o **Deal Rating Engine**. O DealSignal passou a classificar oportunidades em ratings, facilitando leitura rápida do pipeline.

---

## 2. Investigação do modelo preditivo

### Prompt
> "Tem alguma inconsistência no modelo, me ajude a achar gerando um prompt para o Claude Code investigar."

**[IMAGEM 4 — Captura_de_Tela_2026-04-09_a_s_22_57_26.png]**

### Resposta da IA
A IA identificou a inconsistência diretamente na imagem do dashboard: "Desempenho do Produto = Fraco" com score 20, mas o detalhe mostrava 62% de taxa de conversão histórica, 122 deals e interpretação "favorável ao fechamento". Esse conflito disparou uma auditoria do modelo.

A análise crítica chegou a uma conclusão importante: o problema não estava só no modelo, mas em qualidade de sinal do dataset, definição do target, features pouco discriminantes e validação inadequada.

**[IMAGEM 5 — Captura_de_Tela_2026-04-09_a_s_22_52_24.png]**

### Reescrita do modelo
A partir do diagnóstico, a IA sugeriu reescrever o modelo em três camadas (dados → features → modelo), com um novo conjunto de features mais discriminantes.

**[IMAGEM 6 — Captura_de_Tela_2026-04-09_a_s_22_52_34.png]**
**[IMAGEM 7 — Captura_de_Tela_2026-04-09_a_s_22_52_44.png]**

### Impacto no projeto
Essa investigação levou a duas decisões estruturais:
1. Separar **predição estatística** de **diagnóstico operacional**
2. Criar motores determinísticos de análise para complementar o ML

---

## 3. Criação da arquitetura híbrida

### Prompt
> "Entendi, mas afinal qual ficou a participação da IA com isso tudo, são apenas regras?"

**[IMAGEM 8 — Captura_de_Tela_2026-04-09_a_s_23_02_47.png]**

### Resposta da IA
A IA explicou que o modelo ideal não é "só regras" nem "IA decide tudo" — é **híbrido**. Cada camada tem uma função específica:

- **ML model** → prevê probabilidade
- **Rating engines** → explicam o score
- **Friction engine (regras)** → diagnostica bloqueios
- **LLM** → traduz tudo em insight humano

**[IMAGEM 9 — Captura_de_Tela_2026-04-09_a_s_23_07_15.png]**
**[IMAGEM 10 — Captura_de_Tela_2026-04-09_a_s_23_08_28.png]**

### Impacto no projeto
Esse conceito se tornou o princípio central do DealSignal:

> **"O sistema decide, a IA explica."**

---

## 4. Diagnóstico de fricção no pipeline

### Prompt
> "Quero identificar o que está bloqueando um deal, sem deixar a IA inventar lógica."

**[IMAGEM 11 — Captura_de_Tela_2026-04-09_a_s_23_04_10.png]**

### Resposta da IA
A IA reforçou onde **não** deve decidir (qual ação tomar isoladamente, porque pode ser inconsistente, repetir frases ou inventar lógica) e propôs um **Friction Engine** baseado em regras determinísticas para detectar bloqueios: fricção de decisão, urgência, consenso e execução.

### Impacto no projeto
Essa camada passou a explicar **por que** um deal não avança, transformando o produto de um simples scoring em um sistema de **diagnóstico de vendas**.

---

## 5. Next Best Action Engine

### Prompt
> "Gostei, mas as regras estão muito simplórias. Faça um bench com outras ferramentas e sugira regras mais inteligentes — não quero nada óbvio, precisa ser um insight."

**[IMAGEM 12 — Captura_de_Tela_2026-04-09_a_s_23_06_37.png]**

### Resposta da IA
A IA concordou que as regras iniciais estavam óbvias demais e fez benchmark com Salesforce Einstein Next Best Action, mostrando que ferramentas maduras tentam detectar **o bloqueio mais provável do deal**, não apenas mapear score → ação.

### Impacto no projeto
O Next Best Action Engine deixou de ser uma tabela simples de "se X então Y" e passou a recomendar ações baseadas no padrão de fricção detectado, respondendo à pergunta mais importante para o vendedor: **"O que eu devo fazer agora?"**

---

## 6. Uso de IA para interpretação do pipeline

### Prompt
> "Me ajude a dar instruções para a IA construir um texto melhor para o cálculo de probabilidade de fechamento. O texto ficou ruim, lembrando que este dashboard é para os vendedores."

**[IMAGEM 13 — Captura_de_Tela_2026-04-09_a_s_23_08_07.png]**

### Resposta da IA
A IA identificou três problemas no texto original: parecia explicação técnica de modelo, misturava métricas sem hierarquia e não dizia o que fazer com a informação. A recomendação foi estruturar a saída em três blocos: "Por que este deal é forte / O que está impulsionando o score / Qual ação tomar".

Em seguida, foi criado um prompt robusto que **obriga** a IA a buscar deals semelhantes no histórico antes de gerar qualquer insight, evitando alucinação:

**[IMAGEM 14 — Captura_de_Tela_2026-04-09_a_s_23_07_40.png]**

### Impacto no projeto
A IA passou a funcionar como camada de **interpretação**, não de decisão, com regras anti-alucinação: linguagem simples, sem termos técnicos, sem inventar dados, ancorada em padrões reais do pipeline.

---

## 7. Melhoria da visualização do pipeline

### Prompt
> "Hoje a tabela está assim. Minha questão é quanto ao UX da tabela. Com todas estas informações extras não ficará ruim a leitura?"

**[IMAGEM 15 — Captura_de_Tela_2026-04-09_a_s_22_42_32.png]**

### Resposta da IA
A IA confirmou o problema: key factors técnicos (`+days_since_engage(+0.15), +pipeline_velocity(+0.06)`) dentro da tabela geram poluição visual, baixa compreensão para vendedores e quebram o scanning rápido do pipeline. Tabela de pipeline precisa ser escaneável em 2-3 segundos.

A solução foi separar **tabela simples → detalhe expandido**, com motores de rating visualmente claros (Força do Vendedor, Momento do Deal, Desempenho do Produto, Solidez da Conta) e modal de detalhes ao clicar.

**[IMAGEM 16 — Captura_de_Tela_2026-04-09_a_s_22_47_27.png]**

### Impacto no projeto
A mudança tornou o dashboard escaneável para vendedores, mantendo a profundidade analítica acessível sob demanda.

---

## 8. Validação crítica e tratamento de leakage

### Contexto
Depois de reescrever o modelo, o AUC ainda estava em **0.624** — baixo para sustentar uma narrativa de "alta assertividade". Decidi testar se a limitação vinha do dataset (falta de sinal) ou do modelo.

**[IMAGEM 17 — Captura_de_Tela_2026-04-09_a_s_22_54_25.png]**

### Prompt
> "Quero fazer um teste com um dataset completo para ter certeza que o AUC aumentaria. O que precisaria ter exatamente neste dataset?"

**[IMAGEM 18 — Captura_de_Tela_2026-04-09_a_s_22_56_39.png]**

### Resultado do experimento
Com o dataset sintético completo (incluindo features comportamentais e de pipeline), o AUC saltou de 0.496 (baseline) para 0.997 (completo).

**[IMAGEM 19 — Captura_de_Tela_2026-04-09_a_s_23_07_26.png]**

### Crítica honesta — identificação de target leakage
A IA imediatamente apontou que **0.997 é artificialmente alto**: o dataset sintético foi gerado com a mesma função logística que o modelo tenta aprender, configurando *target leakage* clássico (target = função direta das features).

**[IMAGEM 20 — Captura_de_Tela_2026-04-09_a_s_23_08_00.png]**

### Impacto no projeto
A conclusão foi conceitual, não numérica: **dados comportamentais e de pipeline mudam significativamente o poder preditivo** de modelos de previsão de vendas. O número 0.997 não foi usado como evidência de performance real — foi tratado como demonstração de que o limite atual do DealSignal vem da qualidade de sinal do dataset, não da arquitetura do modelo.

---

## Conclusão

A IA foi utilizada em três níveis durante o desenvolvimento do DealSignal:

1. **Exploração de soluções** — modelo de scoring, arquitetura, benchmarks de mercado
2. **Diagnóstico de problemas técnicos** — inconsistências no modelo, identificação de leakage, auditoria de features
3. **Apoio no design de produto** — UX da tabela, hierarquia de informação para vendedores, prompts anti-alucinação

As decisões finais de arquitetura foram tomadas manualmente, garantindo que o sistema fosse **interpretável, confiável e orientado à tomada de decisão real de vendedores**. O princípio "o sistema decide, a IA explica" guiou todas as escolhas — a IA está presente como camada de interpretação e geração de linguagem natural, nunca como decisora autônoma.
