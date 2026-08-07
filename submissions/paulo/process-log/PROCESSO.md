# 📝 Registro de Processo — Engenharia Assistida por IA

**Candidato:** Paulo Sérgio Oliveira da Silva Júnior  
**Desafio:** Diagnóstico de Churn da RavenStack  

# 🤖 Process Log — Registro de Uso de Inteligência Artificial

Este documento detalha o processo de co-criação, análise exploratória e apoio técnico utilizando Inteligência Artificial (Gemini) no desenvolvimento do **Challenge RavenStack Churn**.

---

## 🛠️ 1. Ferramentas e Metodologia de Interação

* **Assistente de IA:** Gemini (Google DeepMind)
* **Objetivo:** Aceleração do diagnóstico de dados, validação de hipóteses de negócio, estruturação do pipeline em Python e refinamento da narrativa executiva.
* **Abordagem de Prompting:** Interativa e iterativa (Prompting por Fases: Ingestão -> Hipóteses -> Resolução de Gargalos Git/Python -> Síntese Executiva).

---

## 🧠 2. Registro de Prompts & Evolução das Iterações

### Fase 1: Diagnóstico de Receita e Identificação de Paradoxos
* **Prompt de Entrada:** 
  > *"Analise a distribuição de churn da base da RavenStack focando em MRR vs. volume de contas. Verifique se existe discrepância entre número de cancelamentos e impacto na receita."*
* **Insight Gerado pela IA:**
  * Identificação de que a perda volumétrica era moderada, mas o **Churn de Receita atingia 70,48%** devido ao cancelamento/downgrade de contas Enterprise.
  * Formulação das hipóteses contra-intuitivas: o **Paradoxo do Engajamento Oculto** (alto NPS/uso antes da queda) e o **Paradoxo do Volume de Suporte** (*silent churn*).

### Fase 2: Construção da Pipeline e Resolução de Desafios Técnicos
* **Prompt de Entrada:** 
  > *"Ajude a estruturar uma pipeline modular em Python dividida em scripts de ingestão, tratamento, engenharia de atributos e análise exploratória. Como podemos contornar o conflito de merge no `.gitignore` e resolver divergências de remote no Git?"*
* **Ação Executada:**
  * Estruturação dos scripts na pasta `src/` (`01_ingestion.py` até `04_exploratory.py`).
  * Execução dos comandos `git checkout --ours` e sincronização bem-sucedida do repositório/PR #93.

---

## 📸 3. Evidências Visuais e Logs

Para garantir a transparência do processo de co-criação com a ferramenta, os artefatos brutos foram anexados ao repositório:

* **Screenshots das Sessões:** Localizadas em `process_logs/screenshots/`
  * `01_analise_churn.png`: Registro do prompt e insight sobre os 70,48% de churn de receita.
  * `02_paradoxos.png`: Registro do levantamento das hipóteses dos dois paradoxos.
* **Exports de Conversa:** Arquivos na pasta `process_logs/chat_exports/`.

---

## ⚖️ 4. Racional Humano vs. Papel da IA

| Etapa | Papel da Inteligência Artificial | Validação e Racional Humano (Paulo) |
| :--- | :--- | :--- |
| **Geração de Hipóteses** | Identificação de padrões estatísticos e anomalias de uso | Conexão dos padrões com a realidade do negócio SaaS Enterprise |
| **Código Python** | Escrita e otimização dos scripts modulares | Execução em ambiente local, tratamento de erros e validação do output |
| **Resolução de Git** | Diagnóstico de mensagens de erro de terminal | Decisão e execução das estratégias de merge/checkout |