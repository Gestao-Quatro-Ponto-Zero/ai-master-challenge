# Workflow — Challenge 001

## 1. Leitura do desafio

O primeiro passo foi entender o objetivo do Challenge 001.

A pergunta central do case era explicar por que a RavenStack estava perdendo clientes mesmo com uso da plataforma aparentemente saudável e satisfação de suporte estável.

---

## 2. Entendimento dos dados

Foram analisados os cinco datasets disponíveis:

* Accounts
* Subscriptions
* Feature Usage
* Support Tickets
* Churn Events

O objetivo inicial foi entender as chaves de relacionamento entre as tabelas e quais perguntas poderiam ser respondidas a partir delas.

---

## 3. Formulação das hipóteses

As hipóteses iniciais foram:

* churn por baixa adoção;
* churn por suporte ruim;
* churn por plano ou billing;
* churn por segmento;
* churn por canal de aquisição;
* churn por perda de valor percebido.

---

## 4. Primeira rodada de análise

A primeira rodada comparou clientes retidos e churnados em:

* uso da plataforma;
* quantidade de features;
* tickets;
* satisfação;
* plano;
* billing;
* receita;
* indústria;
* canal.

Essa etapa mostrou que uso baixo e suporte não pareciam explicar o churn.

---

## 5. Primeira tese provisória

A primeira tese foi que a RavenStack parecia ter um problema de valor percebido e fit por segmento, e não um problema de operação ou adoção.

Essa tese ainda era preliminar.

---

## 6. Auditoria crítica

Antes de aceitar a tese, foi feita uma auditoria com outra IA.

A função dessa IA era tentar derrubar a análise e apontar falhas.

A auditoria identificou problemas importantes:

* falta de análise temporal;
* risco de confundir volume com taxa de churn;
* uso excessivo de médias;
* ausência de impacto financeiro;
* ausência de análise geográfica;
* modelo preditivo fraco.

---

## 7. Segunda rodada de análise

Após a auditoria, novas análises foram executadas:

* churn mensal;
* taxa mensal de churn;
* churn por indústria ao longo do tempo;
* churn por canal ao longo do tempo;
* motivos de churn ao longo do tempo;
* churn por país;
* impacto financeiro por segmento;
* simulação de impacto financeiro das alavancas.

---

## 8. Modelo exploratório

Foi criado um modelo simples de churn scoring.

Resultado:

```text
ROC-AUC: 0.61
```

O resultado foi considerado insuficiente para previsão confiável.

Por isso, o modelo não foi utilizado como ferramenta preditiva final.

---

## 9. Protótipo

A partir dos fatores de risco identificados, foi construído um protótipo funcional em Streamlit:

```text
RavenStack Churn Risk Prioritization Engine
```

O objetivo do protótipo é priorizar contas para ação de Customer Success, usando critérios explicáveis e conectados aos achados da análise.

---

## 10. Submissão final

A entrega final inclui:

* README executivo;
* notebook de análise;
* protótipo funcional;
* process log detalhado;
* screenshots e evidências do processo;
* dados utilizados na análise.

O objetivo da submissão foi mostrar não apenas o resultado final, mas também o processo de raciocínio, validação e correção das conclusões.
