# 📊 RavenStack — Diagnóstico de Churn & Plano de Ação de Emergência

Autor: Paulo Sérgio Oliveira da Silva Júnior
Área: Dados / Analytics & Business Strategy
Para: CEO, RavenStack

---

# 📊 Analise Estratégica de Churn e Diagnóstico de Receita — Challenge RavenStack

##  Executive Summary

A presente análise investigou a dinâmica de retenção e cancelamentos da **RavenStack**, identificando um cenário crítico de degradação financeira: enquanto o churn volumétrico de clientes apresenta taxas moderadas, o **Churn de Receita atinge alarmantes 70,48%**. 

A solução desenvolvida utiliza uma pipeline modular em Python dividida em fases (ingestão, higienização, engenharia de atributos e diagnóstico exploratório) combinada com o uso ostensivo de Inteligência Artificial para identificação de padrões não óbvios e hipóteses de negócio.

---

## 🚨 O Diagnóstico Principal: Churn de Receita (70,48%)

O achado central do estudo demonstra que **a perda financeira da empresa é desproporcional ao número de contas canceladas**.

[ Base total de Clientes ]  --->  Churn de Clientes (Volumétrico): Moderado
[ Base total de Receita  ]  --->  Churn de Receita (ARR/MRR): 70,48% 💥

### Por que isso acontece?
* **Concentração no Enterprise/Mid-Market:** As contas que estão dando cancelamento ou *downgrade* agressivo são justamente as de maior *Ticket Médio (LTV)*.
* **Efeito "Cauda Longa de Baixo Valor":** A base permanece numericamente estável devido à retenção de clientes de planos de entrada (menor MRR), mas a receita real está evaporando pelos clientes de grande porte.

---

## 🎭 A Tese dos Dois Paradoxos

Através da análise exploratória apoiada por IA, identificamos dois comportamentos contra-intuitivos nos dados de uso e suporte:

### 1. O Paradoxo do Engajamento Oculto (NPS vs. Churn)
* **O Fenômeno:** Clientes com pontuações altas de satisfação (NPS/CSAT) e alto volume de uso diário das funcionalidades centrais apresentaram repentinos cancelamentos de contrato.
* **Racional da Decisão Analítica:** Diferente da premissa tradicional de que "cliente engajado não dá churn", a análise revelou que contas Enterprise usavam intensamente a plataforma até atingirem gargalos técnicos severos de escalabilidade ou integração, optando por migrações abruptas para concorrentes sem registrar insatisfação formal prévia.

### 2. O Paradoxo do Volume de Suporte (Suporte Baixo ≠ Cliente Saudável)
* **O Fenômeno:** Contas de alto MRR no período imediatamente anterior ao churn apresentavam **queda quase zero no número de chamados abertos no suporte**.
* **Racional da Decisão Analítica:** A ausência de tickets de suporte não significava satisfação, mas sim **desengajamento operacional e abandono silencioso (*silent churn*)**. A equipe do cliente parava de tentar resolver dúvidas/problemas no sistema porque já estava em processo de transição para outra ferramenta.

---

## 🛠️ Metodologia e Pipeline Python em Fases

A solução foi estruturada de forma modular no repositório para garantir reprodutibilidade e governança analítica:

src/
├── 01_ingestion.py    # Carga de dados, validação de schema e tipos
├── 02_cleaning.py     # Tratamento de nulos, inconsistências e deduplicação
├── 03_engineering.py  # Criação de atributos (MRR por conta, Cohorts, Churn Rate)
└── 04_exploratory.py  # Análise estatística, testes de hipóteses e geração dos gráficos

### Racional das Decisões Analíticas
1. **Atribuição do Status de Churn:** Considerou-se como churn não apenas o cancelamento total da conta, mas também contrações de receita (*contraction churn*) superiores a 50% do MRR histórico da conta.
2. **Segregação por Cohort de Entrada:** Permitiu identificar se as saídas eram reflexo de problemas na integração inicial (*Onboarding*) ou fadiga de valor após 12+ meses de contrato.

---

## 💡 Plano de Ação & Próximos Passos (Mitigação)

Para estancar a sangria de 70,48% da receita, recomendam-se as seguintes frentes imediatas:

### 1. Ações de Emergência (Curto Prazo - 0 a 30 dias)
* **Playbook de Silent Churn:** Criar alerta automatizado para contas Enterprise que apresentem queda abrupta de chamados no suporte + estagnação no volume de dados consumidos.
* **Redesign do Onboarding de Grandes Contas:** Acompanhamento dedicado (*Customer Success*) com marcos rígidos de entrega técnica de integração.

### 2. Ações Estruturais (Médio/Longo Prazo - 30 a 90 dias)
* **Estruturação de Modelo Preditivo com IA:** Implementar algoritmo supervisionado (Random Forest / XGBoost) treinando a probabilidade de churn com base nas variáveis comportamentais identificadas.
* **Revisão da Política de Pricing & Tiering:** Alinhar o valor cobrado com as funcionalidades avançadas que seguram as contas de grande porte.

---

## 📂 Estrutura do Repositório

* `README.md`: Este relatório executivo e técnico.
* `PROCESSO.md`: Documentação detalhada da interação com a IA (prompts, evoluções e racional).
* `process_logs/`: Evidências visuais, screenshots e logs brutos do chat de IA.
* `src/`: Código fonte do pipeline em Python.
* `data/`: Datasets limpos e tratados (respeitando as regras de versionamento).