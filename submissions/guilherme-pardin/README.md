# Submissão — Guilherme Pardin — Challenge 003

## Sobre mim
- **Nome:** Guilherme Pardin
- **LinkedIn:** https://www.linkedin.com/in/guipardindev/
- **Challenge escolhido:** Build-003 — Lead Scorer

---

## Executive Summary

Sistema de Lead Scoring funcional para priorização automática de 
2.089 oportunidades abertas de um pipeline de 8.800 deals. 
A solução calcula um score de 0 a 100 para cada deal usando 6 
features — incluindo win rate histórico por setor e por vendedor, 
calculados do próprio dataset. O vendedor filtra pelo seu nome, 
vê os deals Tier A em verde e recebe recomendação em linguagem 
natural via Claude API. Roda localmente com um comando.

---

## Como rodar

### Pré-requisitos
- Python 3.9 ou superior
- pip

### Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/SEU_USUARIO/ai-master-challenge.git
cd ai-master-challenge/submissions/guilherme-pardin/solution

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Rode o app
streamlit run app.py
```

O app abre automaticamente em http://localhost:8501

### Chave da API (opcional)
Para usar a análise com IA, cole sua chave Anthropic na sidebar.
Sem a chave, o scoring por regras funciona normalmente.
Obtenha em: https://platform.anthropic.com

### Estrutura dos dados
Coloque os 4 CSVs na pasta data/:

```
solution/
├── data/
│   ├── sales_pipeline.csv
│   ├── accounts.csv
│   ├── products.csv
│   └── sales_teams.csv
├── app.py
├── scoring.py
├── ai_insights.py
└── requirements.txt
```

---

## Solução

### Abordagem

Antes de escrever código, analisei os dados reais e encontrei 3 
problemas que precisavam de decisão:

1. close_value é NULL para todos os deals abertos — solução: usar 
   sales_price do produto como valor esperado
2. 1.425 deals sem account no CSV original — solução: classificar 
   como "Desconhecido" e documentar
3. Dataset de 2016-2017 — days_in_pipeline sempre >180, feature 
   contribui 0 pts para todos os deals abertos

Priorizei scoring baseado em regras com IA opcional — o app 
funciona 100% sem API key.

### Resultados

- 2.089 deals abertos processados e priorizados
- 7 deals Tier A (score ≥70) — R$ 187.376 em valor total
- 2.082 deals Tier B — pipeline principal de trabalho
- Win rates reais calculados: por setor e por vendedor
- Interface com 3 abas: Pipeline / Análise IA / Visão do Gestor

### Lógica de scoring (100 pts total)

| Feature | Peso | Fonte |
|---|---|---|
| Deal stage | 30 pts | sales_pipeline |
| Tempo no pipeline | 20 pts | engage_date |
| Valor do deal | 20 pts | sales_price (proxy) |
| Win rate do setor | 15 pts | histórico Won/Lost |
| Win rate do vendedor | 10 pts | histórico Won/Lost |
| Tamanho da conta | 5 pts | revenue + employees |

### Recomendações

1. Conectar a um CRM live para scoring em tempo real
2. Adicionar dados de atividade recente (emails, ligações) como feature
3. Com 6.700 deals históricos Won/Lost, treinar modelo preditivo 
   substituindo as regras

### Limitações

- days_in_pipeline inútil como feature — dataset histórico de 2016-2017
- 68% dos deals abertos sem account identificada no CSV
- close_value ausente nos deals abertos — substituído por sales_price
- Sem dados de atividade recente (último contato, interações)

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usou |
|---|---|
| Claude (claude.ai) | Planejamento da arquitetura, lógica de scoring, revisão das decisões técnicas |
| Claude Code (Desktop) | Geração e iteração de todo o código Python/Streamlit |

### Workflow

1. Defini o problema e discuti a arquitetura com Claude antes de 
   escrever qualquer código
2. Claude Code leu os CSVs e identificou problemas reais nos dados 
   antes de escrever o código
3. Iterei o frontend via Claude Code com pedidos em linguagem natural
4. Claude Code diagnosticou e corrigiu os NaNs investigando a causa 
   raiz, não só substituindo valores

### Onde a IA errou e como corrigi

- Primeira versão da tabela tinha texto invisível nas células coloridas 
  — corrigi pedindo dark mode com cores específicas
- Score médio exibia "50.0" com casa decimal — corrigi com instrução direta

### O que eu adicionei que a IA sozinha não faria

- Decisão de usar sales_price como proxy para close_value nulo 
  — julgamento sobre o negócio, não técnico
- Priorizei win rate histórico como feature diferencial — insight 
  de que o dataset tem histórico suficiente para isso
- Identifiquei que days_in_pipeline seria inútil dado o dataset 
  histórico — a IA implementou mas eu documentei a limitação

---

## Evidências

- [x] Chat exports desta conversa com Claude
- [x] Git history mostrando evolução do código
- [x] Screenshots do app funcionando

---

*Submissão enviada em: abril 2026*
