# Submissão — Luiz Fernando Mendes — Challenge AI Master

## Sobre mim

- **Nome:** Luiz Fernando Mendes
- **LinkedIn:** [[Link de Perfil]](https://www.linkedin.com/in/luizfmmendes/)
- **Challenge escolhido:** Lead Scorer Inteligente (RevOps & Data Science)

---

## Executive Summary

Desenvolvi uma plataforma preditiva de Lead Scoring que transforma o pipeline estático em um motor de priorização estratégica. Através de um diagnóstico profundo de RevOps, identifiquei uma "Zona de Ouro" de conversão (75%) entre 30 e 120 dias de maturidade. A solução final é um dashboard executivo em React, hospedado no Netlify, que processa 2.089 deals ativos e isola as 229 oportunidades com maior probabilidade de fechamento (Score 75+), permitindo uma alocação eficiente do time comercial.

---

## Solução

A solução pode ser acessada em tempo real pelo link abaixo:
🚀 **Aplicação Funcional:** [https://leadscoreinteligente.netlify.app](https://leadscoreinteligente.netlify.app)

### Abordagem

O problema foi decomposto em três frentes:
1.  **Diagnóstico de Dados:** Análise exploratória dos CSVs para identificar gargalos (ex: 68% de accounts não vinculados e a "Zona de Morte" nos primeiros 15 dias).
2.  **Modelagem Matemática:** Criação de um algoritmo de scoring ponderado: Maturidade (35%), Performance do Agente (30%), Fit de Produto (20%) e Firmographics (15%).
3.  **Entrega de Produto:** Evolução de um MVP em Python (Streamlit) para uma aplicação de alta performance em React para garantir UX executiva.

### Resultados / Findings

* **Pipeline Ativo:** Processamento total de 2.089 deals em tempo real via upload de CSV.
* **Identificação de Ouro:** Isolamento de 229 deals de "Alta Prioridade" que possuem os pilares ideais de fechamento.
* **Explainability:** O sistema detalha individualmente o "porquê" de cada score, eliminando a "caixa-preta" da IA para o vendedor.
* **Identidade Visual:** Interface customizada com a paleta G4 Scale (#1E293B e #476382).

### Recomendações

1.  **Foco Imediato:** Concentrar o time de vendas exclusivamente nos 229 leads identificados com Score 75+.
2.  **Saneamento de CRM:** Corrigir o fluxo de entrada de dados, visto que 68% dos deals não possuem conta vinculada, prejudicando a análise de Firmographics.
3.  **Automação de Pipeline:** Utilizar a estrutura de API já prevista no código para conectar a ferramenta diretamente ao HubSpot/Salesforce.

### Limitações

A principal limitação foi a qualidade dos dados de Firmographics no dataset original. Devido à ausência de informações em muitos registros, o algoritmo foi ajustado para aplicar um "score neutro" nesses casos, evitando a despriorização injusta de bons negócios por falha de cadastro.

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| **Gemini 3 Flash** | Mentor de estratégia, diagnóstico de RevOps e correção de bugs técnicos de build e lógica. |
| **Google AI Studio** | Prototipagem da interface React e estruturação do dashboard executivo. |
| **Vite/Netlify** | Build e hospedagem da aplicação final. |

### Workflow

1.  **Análise de Dados:** Usei o Gemini para identificar padrões de conversão e definir os pesos do algoritmo de scoring.
2.  **Prototipagem:** Construí a lógica inicial no Python e transpus para React usando o Google AI Studio para ganhar sofisticação visual.
3.  **Iteração Técnica:** Passei por 4 ciclos de correção de erros de build no Netlify e ajustes de indentação no Python.
4.  **Ajuste Temporal:** Corrigi o "Bug do Tempo" onde a IA usava 2026 como referência para dados de 2017.

### O onde a IA errou e como corrigi

A IA tentou calcular a maturidade dos deals usando a data atual (2026). Como o dataset é histórico (2017), todos os scores resultavam em zero ("Expirado"). **Minha correção:** Instruí a IA a identificar a data máxima do dataset e utilizá-la como a "Data de Referência" dinâmica, devolvendo a vida aos scores da Zona de Ouro. Além disso, corrigi erros de resolução de caminhos no Vite (`main.tsx`) que impediam o deploy no Netlify.

### O que eu adicionei que a IA sozinha não faria

O **Julgamento de Negócio**. A IA sugeriu penalizar severamente deals sem "Account" vinculado. Eu identifiquei que, como 68% do pipeline estava assim, a penalização destruiria a utilidade da ferramenta. Decidi configurar um peso neutro para essa categoria, priorizando a usabilidade do time comercial enquanto o problema de governança de dados é resolvido.

---

## Evidências

- [x] Link do Netlify: [https://leadscoreinteligente.netlify.app](https://leadscoreinteligente.netlify.app)
- [x] Repositório GitHub com histórico de commits.
- [x] Screenshots do Dashboard incluídos na pasta `/assets`.

---

_Submissão enviada em: 13/03/2026_
