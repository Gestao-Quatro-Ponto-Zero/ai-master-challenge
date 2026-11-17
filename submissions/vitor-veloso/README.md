# Submissão — Vitor Veloso — Challenge 003 (Lead Scorer)

## Sobre mim

- **Nome:** Vitor Ricardo Ferreira Veloso
- **GitHub:** [vvitorveloso](https://github.com/vvitorveloso)
- **E-mail:** vitorveloso@iid.org.br
- **Challenge escolhido:** 003 — Lead Scorer (Vendas / RevOps, Build)

---

## Executive Summary

Para solucionar a dor da Head de RevOps (vendedores gastando tempo com oportunidades que não convertem e deixando leads quentes esfriar), construí o **Lead Scorer & Prioritization Hub**: uma ferramenta funcional completa (CLI analítica + Dashboard Web Interativo) alimentada por um motor heurístico e probabilístico calibrado no dataset real de 8.800 oportunidades do CRM. A análise histórica revelou que deals estagnados há mais de 75 dias têm queda drástica de conversão e que ~68% das oportunidades ativas estão em risco por falta de cadastro de conta corporativa ou inatividade prolongada. A solução classifica cada deal em 4 tiers acionáveis (Prioridade Alta, Média, Baixa e Em Risco), fornece explainability multidimensional transparente por oportunidade e sugere o próximo passo comercial imediato, permitindo que cada vendedor e gestor regional saiba com clareza matemática e contextual onde focar na segunda-feira de manhã.

---

## Solução

A solução foi desenvolvida como software real e executável, dividida em módulos modulares e reutilizáveis localizados na pasta `solution/`:
- `scoring_engine.py`: Motor matemático e analítico que realiza o carregamento, saneamento das 4 tabelas relacionais do CRM, cálculo de benchmarks históricos e scoring com explainability.
- `lead_scorer_app.py`: Interface de linha de comando (CLI) operacional que gera relatórios no terminal, exporta CSV e compila o dashboard executivo autocontido.
- `server.py`: Servidor web local zero-dependency para visualização interativa do painel em tempo real (`http://localhost:8050`).
- `data/`: Conjunto de dados real integrado e sanitizado (`accounts.csv`, `products.csv`, `sales_teams.csv`, `sales_pipeline.csv`).

### Abordagem

1. **Exploração & Higienização dos Dados Reais:**
   - Detectou-se e tratou-se a inconsistência de catálogo entre `GTXPro` (tabela de pipeline) e `GTX Pro` (catálogo de produtos).
   - Constatou-se que das 8.800 oportunidades, 6.711 já foram encerradas (4.238 Won com valor médio de $2.361, e 2.473 Lost com valor $0), restando 2.089 oportunidades em aberto (1.589 em `Engaging` e 500 em `Prospecting`).
   - Identificou-se que 1.425 oportunidades ativas não possuem conta corporativa vinculada (`account = NaN`), operando como prospects frios que necessitam de qualificação urgente.

2. **Engenharia de Features & Benchmarking Histórico:**
   - **Win Rate Histórico da Conta:** Calculado sobre contas com histórico (variando entre 53% e 75% de taxa de conversão).
   - **Win Rate Histórico do Vendedor:** Variação entre 55% e 70% entre os 35 consultores comerciais.
   - **Ciclo de Maturação:** O ciclo médio de negócios fechados com vitória (`Won`) é de 52 dias (mediana de 57 dias), enquanto deals que ultrapassam 90 dias sem evolução sofrem estagnação severa.

3. **Lógica de Scoring e Explainability (0 a 100 pontos):**
   A pontuação de cada oportunidade é baseada em 5 pilares transparentes:
   - **Estágio no Funil (até 25 pts):** `Engaging` (+25) vs `Prospecting` (+10).
   - **Frescor / Idade do Pipeline (-25 a +20 pts):** Deals de 0 a 20 dias ganham +20; 21 a 45 dias +15; 46 a 75 dias +5; 76 a 120 dias sofrem penalidade de -10; acima de 120 dias sofrem penalidade de -25 por risco crítico de estagnação.
   - **Fit & Histórico da Conta (0 a 20 pts):** Contas corporativas cadastradas pontuam base (+10) com bônus de até +10 se o win rate histórico da conta for superior a 68%. Leads sem conta são alertados com pontuação mínima (+5) e sinalizador de cadastro incompleto.
   - **Potencial de Receita e Ticket do Produto (0 a 20 pts):** Produtos de ticket enterprise (ex: GTK 500 a $26.768) ou alto valor (GTX Plus Pro / GTX Pro a ~$5.000) recebem +15 a +20 pts.
   - **Desempenho Histórico do Vendedor (0 a 15 pts):** Reconhecimento de consultores com histórico de alta conversão (+15 pts).
   - **Expected Deal Value ($ EV):** Calculado como $\text{Score} \times \text{Valor do Produto}$, permitindo que a liderança enxergue o valor ponderado real da carteira.

### Resultados & Findings

- **Distribuição do Pipeline Ativo (2.089 oportunidades):**
  - **Prioridade Alta (38 deals):** Contas mapeadas, em negociação ativa fresca e alto ticket. Ação imediata: agendamento de call de fechamento.
  - **Prioridade Média (571 deals):** Deals em maturação normal que demandam avanço de proposta e alinhamento de ROI.
  - **Prioridade Baixa (30 deals):** Tickets muito baixos ou prospecções embrionárias sem conta vinculada.
  - **Em Risco (1.450 deals):** Deals estagnados há mais de 90 dias ou cadastros órfãos que poluem a previsão de vendas da equipe.
- **Explainability Individual:** Cada oportunidade na interface exibe detalhadamente os pontos positivos (▲), os fatores de risco (▼) e a **Ação Comercial Recomendada**.
- **Filtros Operacionais:** Segmentação instantânea por Vendedor (35 consultores), Região (Central, East, West), Tier de Prioridade e Busca Textual por nome da empresa cliente.

### Recomendações para RevOps

1. **Foco Imediato dos Vendedores:** Os vendedores devem dedicar as manhãs de segunda e terça-feira exclusivamente aos 38 deals de Prioridade Alta (que concentram alto valor esperado e probabilidade de conversão acima de 70%).
2. **Higienização de Pipeline ("Deal Staling"):** Instituir política de CRM onde oportunidades em `Engaging` há mais de 90 dias sem contato sejam movidas para nutrição ou dadas como perdidas, saneando o forecast comercial.
3. **Obrigatoriedade de Associação de Conta:** Exigir cadastro da conta cliente antes de mover o deal para `Engaging`, sanando a lacuna de 1.425 oportunidades órfãs.

### Limitações

- **Ausência de Logs de Atividades Intermediárias:** O dataset não disponibiliza número de e-mails trocados, reuniões realizadas ou ligações efetuadas (engajamento comportamental diário).
- **Datas Estáticas:** Os dados refletem o histórico de 2017; para produção, o cálculo de dias deve utilizar `datetime.now()` em tempo real conectado à API do CRM corporativo (Salesforce, HubSpot ou Pipedrive).

---

## Como Rodar a Solução (Setup Instructions)

A solução foi construída utilizando Python 3 padrão e pandas, sem necessidade de frameworks pesados ou dependências complexas.

### Pré-requisitos
- Python 3.9+
- Biblioteca `pandas`

```bash
pip install pandas
```

### 1. Execução via Linha de Comando (CLI)
Para visualizar o ranking priorizado no terminal e gerar os arquivos analíticos:
```bash
cd submissions/vitor-veloso/solution
python3 lead_scorer_app.py --top 10
```

Opções disponíveis na CLI:
- `--agent "Nome do Vendedor"`: Filtra o ranking por um vendedor específico.
- `--office "Central|East|West"`: Filtra por escritório regional.
- `--top N`: Exibe os top N registros no terminal (padrão: 10).
- `--export-csv "caminho.csv"`: Exporta os resultados calculados com scores e explainability.

### 2. Execução do Dashboard Interativo (Navegador)
Para abrir a interface gráfica web com filtros dinâmicos, KPIs executivos e explainability visual:
```bash
cd submissions/vitor-veloso/solution
python3 server.py
```
Acesse no seu navegador: **`http://localhost:8050`** (ou abra diretamente o arquivo `lead_scorer_dashboard.html`).

---

## Process Log — Como usei IA

> **Evidência de processo e co-criação com IA (obrigatório).**

### Ferramentas usadas

| Ferramenta | Para que usou |
|---|---|
| **Google Antigravity CLI / Gemini 3.8 Flash** | Análise exploratória automatizada dos 4 datasets, identificação de inconsistências em strings (`GTXPro`), engenharia de regras de negócio de RevOps, codificação do motor de scoring e desenvolvimento do dashboard responsivo. |
| **Python Standard Library & pandas** | Verificação determinística das hipóteses estatísticas, validação de ciclo médio de conversão e cálculo de métricas. |
| **Git / GitHub SSH** | Versionamento atômico, criação da branch de entrega e submissão via Pull Request. |

### Workflow de Desenvolvimento

1. **Decomposição do Problema de RevOps:**
   Antes de gerar qualquer linha de código, analisei o pedido da Head de RevOps sob a perspectiva da usabilidade do vendedor: "o que um vendedor precisa enxergar às 8h da manhã?". O problema foi decomposto em 3 camadas: integridade de dados (limpeza), motor de scoring explicável (explainability) e interface de consumo imediato (CLI + Web Dashboard).
2. **Auditoria dos Dados Reais com IA:**
   Ao carregar o dataset `agungpambudi/crm-sales-predictive-analytics`, a IA identificou uma divergência no nome do produto (`GTXPro` no pipeline versus `GTX Pro` na tabela de produtos) que gerava perda de 1.147 oportunidades no merge. Foi implementado o tratamento automático dessa discrepância.
3. **Modelagem de Regras de Negócio e Heurística:**
   Em vez de criar uma "caixa preta" de Machine Learning (como um XGBoost sem explicabilidade que vendedores rejeitariam), desenhamos uma lógica de pontuação por pilares fundamentados na prática comercial (estágio, dias no funil, fit da conta, ticket do produto e win rate do vendedor).
4. **Implementação da Ferramenta de Entrega:**
   Desenvolvimento do script `scoring_engine.py` desacoplado da interface. Em seguida, criação do `lead_scorer_app.py` que gera a interface web interativa rica em visualizações, cartões de KPI, filtros por vendedor/região e detalhamento individual de cada deal.
5. **Verificação Prática:**
   Execução ponta a ponta dos scripts, validação das rotas HTTP do servidor e teste visual do dashboard no navegador.

### Onde a IA errou e como corrigi

- **Erro inicial de suposição de modelo complexo:** A IA inicialmente sugeriu treinar um modelo supervisionado RandomForest/XGBoost para estimar probabilidade. Corrigi a direção estratégica: a instrução do case enfatizava claramente que *"a Head de RevOps não quer um modelo em notebook que ninguém vai usar, e explainability ganha"*. Um modelo puramente preditivo não forneceria a granularidade e clareza de recomendação que um motor por pilares explicáveis oferece.
- **Tratamento de dados nulos nas oportunidades ativas:** Durante a exploração, constatamos que mais de 68% das oportunidades ativas não possuíam `account` definida. A IA inicialmente ignorou os registros sem conta; ajustei a lógica para categorizar esses casos como "prospects frios sem cadastro corporativo", atribuindo alertas operacionais específicos para que o vendedor realize a qualificação.

### O que eu adicionei que a IA sozinha não faria

- **Visão de Negócio em RevOps:** Introdução do conceito de *Expected Value* ($\text{Score} \times \text{Valor}$), que permite à diretoria enxergar a receita ponderada do pipeline e não apenas o valor facial.
- **Recomendações Práticas Acionáveis:** Inclusão de um campo direto de "Próximo Passo Recomendado" associado a cada tier de oportunidade, tornando a ferramenta um guia de ação imediata para o consultor.
- **Arquitetura Zero-Dependência:** Escolha de gerar um dashboard HTML+JS estático de alta fidelidade servido por servidor Python nativo, garantindo que qualquer membro da equipe consiga rodar a ferramenta em qualquer computador sem conflitos de ambiente virtual ou compilação.

---

## Evidências

- **Código Fonte Completo:** Localizado em `submissions/vitor-veloso/solution/` (`scoring_engine.py`, `lead_scorer_app.py`, `server.py`).
- **Dashboard Web Gerado:** Arquivo `submissions/vitor-veloso/solution/lead_scorer_dashboard.html`.
- **Dados Reais Incluídos:** Diretório `submissions/vitor-veloso/solution/data/` contendo os 4 CSVs originais do Kaggle.
- **Process Log Detalhado:** Arquivo `submissions/vitor-veloso/process-log/PROCESS_LOG.md`.
- **Git History:** Commits detalhados registrando cada etapa da construção.

---
_Submissão concluída em: 17 de Novembro de 2026_
