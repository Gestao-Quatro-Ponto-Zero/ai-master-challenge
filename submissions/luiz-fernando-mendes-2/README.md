# Submissão — Luiz Fernando Mendes — Challenge AI Master

## Sobre mim

- **Nome:** Luiz Fernando Mendes
- **LinkedIn:** [Perfil LinkedIn](https://www.linkedin.com/in/luizfmmendes/)
- **Challenge escolhido:** Lead Scorer Inteligente (RevOps & Data Science)

---

## Executive Summary

Desenvolvi uma plataforma preditiva de Lead Scoring que transforma o pipeline estático em um motor de priorização estratégica. Através de um diagnóstico profundo de RevOps, identifiquei uma **"Zona de Ouro"** de conversão entre 30 e 120 dias de maturidade. A solução final é um dashboard executivo em React, hospedado no Netlify, que processa 2.089 deals ativos e isola as **229 oportunidades** com maior probabilidade de fechamento (Score 75+), permitindo uma alocação eficiente do time comercial e maximização de receita.

---

## Solução

A solução pode ser acessada em tempo real pelo link abaixo:
🚀 **Aplicação Funcional:** [https://leadscoreinteligente.unaux.com/](https://leadscoreinteligente.unaux.com/)

### Abordagem

O problema foi decomposto em três frentes:
1. **Diagnóstico de Dados:** Análise exploratória dos CSVs para identificar gargalos (ex: 68% de accounts não vinculados e a "Zona de Morte" nos primeiros 15 dias).
2. **Modelagem Matemática:** Criação de um algoritmo de scoring ponderado: Maturidade (35%), Performance do Agente (30%), Fit de Produto (20%) e Firmographics (15%).
3. **Entrega de Produto:** Evolução de um MVP em Python (Streamlit) para uma aplicação de alta performance em React para garantir UX executiva e explicabilidade.

### Validação Técnica (Data Science)
Para garantir a integridade das afirmações analíticas, incluí o script de derivação:
* 📁 **Arquivo:** `solution/data_analysis.py`
* **O que ele prova:** Processa o `sales_pipeline.csv` original, calcula o Win Rate por janelas temporais e valida matematicamente que a maior conversão histórica ocorre na janela de **30-120 dias**, sustentando a lógica do Dashboard. O script carrega os dados reais que eu usei calculando o tempo de fechamento (Close Date - Created Date) e agrupando os leads por janelas de tempo. Isso prova matematicamente que o Win Rate é maior entre 30 e 120 dias.

### Resultados / Findings

* **Pipeline Ativo:** Processamento total de 2.089 deals em tempo real via upload de CSV.
* **Identificação de Ouro:** Isolamento de 229 deals de "Alta Prioridade" com os pilares ideais de fechamento.
* **Explainability:** O sistema detalha individualmente o "porquê" de cada score, eliminando a "caixa-preta" da IA para o vendedor.
* **Consistência Monetária:** Interface totalmente ajustada para **USD ($)**, mantendo fidelidade ao dataset original.
* **Priorização Realista:** Ajuste manual de thresholds de scoring (limite de **50 pontos**) para garantir que nenhum lead em risco seja ignorado pelo dashboard, corrigindo distorções geradas pela lógica automatizada inicial.

---

## Process Log — Como usei IA

O processo completo, com mais de 40 evidências visuais e histórico de tomadas de decisão, está disponível em:
📁 **Documentação:** `process-log/PROCESS_LOG.md`

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| **Gemini 3 Flash (GEM Luiz)** | Mentor de estratégia (Napoleon Hill/Kotler), diagnóstico de RevOps e suporte técnico. |
| **Qwen** | Geração da lógica bruta inicial em Python e prototipagem rápida. |
| **Google AI Studio** | Reconstrução total do sistema em React para entrega de nível corporativo. |
| **VS Code / Netlify** | Debug local de ambiente Python 3.14 e deploy da aplicação final. |

### O que eu adicionei que a IA sozinha não faria

1. **Julgamento de Negócio:** A IA sugeriu penalizar deals sem "Account". Identifiquei que isso ocultaria 68% do pipeline e decidi configurar um peso neutro para manter a utilidade da ferramenta.
2. **Pivô Estratégico:** Após 4 horas em Python, identifiquei que o fluxo era lento e pouco intuitivo. Tomei a decisão executiva de abandonar o código e reconstruir em React para garantir a melhor experiência ao usuário G4.
3. **Homenagem e Contexto:** Criei o GEM "Luiz", uma homenagem ao meu pai, garantindo que a IA operasse sob diretrizes éticas e psicológicas específicas, e não apenas como um gerador de código.

---

## Evidências

- [x] **Aplicação em Produção:** [https://leadscoreinteligente.unaux.com/](https://leadscoreinteligente.unaux.com/)
- [x] **Process Log Auditável:** Localizado em `/process-log/` com screenshots numeradas.
- [x] **Derivação de Dados:** Script `data_analysis.py` incluído na pasta `/solution`.
- [x] **Consistência de Interface:** Moeda ajustada para USD e dados batendo com o dataset.

---
_Submissão finalizada em: 13/03/2026_
