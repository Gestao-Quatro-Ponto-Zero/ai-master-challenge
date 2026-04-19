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
features — incluindo win rate histórico por setor, vendedor e 
sazonalidade, todos calculados do próprio dataset. O vendedor 
filtra pelo seu nome, vê os deals Tier A em destaque e pode 
conversar com um chat de IA para análises específicas do pipeline. 
Roda localmente com um comando.

---

## Como rodar

### Pré-requisitos
- Python 3.9 ou superior
- pip

### Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/guipardindev/ai-master-challenge.git
cd ai-master-challenge/submissions/guilherme-pardin/solution

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Rode o app
streamlit run app.py
```

O app abre automaticamente em http://localhost:8501

### Chave da API (opcional)
Para usar o Chat com IA e a Análise IA, cole sua chave Anthropic 
na sidebar. Sem a chave, o scoring por regras funciona normalmente.
Obtenha em: https://platform.anthropic.com

### Estrutura dos dados
Coloque os 4 CSVs na pasta data/:

```
solution/
├── .streamlit/
│   └── config.toml
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

Antes de escrever qualquer código, o Claude Code leu e analisou 
os 4 CSVs para entender os dados reais. Três problemas foram 
identificados e resolvidos antes de começar o scoring:

1. `close_value` é NULL para todos os deals abertos — solução: 
   usar `sales_price` do produto como valor esperado
2. 1.425 deals sem `account` no CSV original — solução: 
   classificar como "Desconhecido" e documentar
3. Dataset de 2016-2017 — problema crítico descoberto na análise, 
   detalhado abaixo

### Iteração analítica — como o modelo evoluiu

#### O problema com days_in_pipeline

A primeira versão do scoring incluía `days_in_pipeline` como 
feature com peso de 20 pts. A lógica fazia sentido: deals parados 
há muito tempo deveriam ser penalizados.

Porém, ao validar a distribuição da feature nos dados reais, 
descobrimos que **todos os 2.089 deals abertos têm mais de 3.000 
dias no pipeline** — porque o dataset é de 2016-2017. A feature 
contribuía 0 pts para 100% dos deals, sem discriminar ninguém.
Manter essa feature seria ruído puro no modelo.

#### Três hipóteses testadas para substituição

Antes de decidir, investigamos 3 alternativas com o Claude Code 
analisando os dados reais:

**Hipótese 1 — Velocidade de progressão (dias de Prospecting → Engaging)**
Descartada. O dataset não tem a data de entrada em Prospecting — 
só `engage_date`. Impossível calcular a velocidade de progressão. 
Além disso, os 500 deals ainda em Prospecting não teriam essa 
informação de forma alguma.

**Hipótese 2 — Proximidade do close_date**
Descartada. Verificamos nos dados: `close_date` é NULL para 
100% dos deals abertos. A data só é preenchida quando o deal 
fecha (Won ou Lost). Feature inviável.

**Hipótese 3 — Sazonalidade (win rate histórico por mês)**
Aprovada. O dataset tem 6.711 deals históricos (Won + Lost) com 
`engage_date` preenchido. Calculamos o win rate por mês de entrada 
e encontramos variação real e significativa:

| Mês | Win rate | Volume |
|-----|----------|--------|
| Dezembro | 80% | 103 deals |
| Janeiro | 73% | 247 deals |
| Novembro | 69% | 102 deals |
| Julho | 55% | 796 deals |

**Impacto da mudança:**
- Antes: desvio padrão de 4 pts, range de 27 pts, 7 deals Tier A
- Depois: desvio padrão de 8.4 pts, range de 48 pts, 31 deals Tier A
- Feature passou de 1 valor único (0) para 7 valores distintos

### Resultados

- 2.089 deals abertos processados e priorizados
- 31 deals Tier A (score ≥70) — R$ 480.533 em valor total
- Interface com 4 abas: Pipeline / Análise IA / Chat com IA / Gestor

### Lógica de scoring (100 pts total)

| Feature | Peso | Fonte | Notas |
|---|---|---|---|
| Deal stage | 30 pts | sales_pipeline | Engaging=30, Prospecting=15 |
| Sazonalidade | 20 pts | histórico Won/Lost | Win rate do mês de entrada |
| Valor do deal | 20 pts | sales_price | Proxy para close_value nulo |
| Win rate do setor | 15 pts | histórico Won/Lost | Calculado do dataset |
| Win rate do vendedor | 10 pts | histórico Won/Lost | Calculado do dataset |
| Tamanho da conta | 5 pts | accounts | Receita + funcionários |

### Chat com IA

Adicionamos uma aba de chat onde o vendedor pode fazer perguntas 
em linguagem natural sobre o próprio pipeline:

- Filtros inline por vendedor, tier e região — independentes 
  da sidebar
- A IA recebe os top 50 deals do contexto filtrado
- Sugestões de perguntas para guiar o uso
- Histórico de conversa mantido na sessão
- Funciona com claude-sonnet-4 ou claude-haiku-4 (selecionável 
  na sidebar)
- Requer chave da API Anthropic com créditos disponíveis

### Design

O visual foi atualizado para seguir o padrão G4 Educação:
- Paleta de cores extraída do site oficial (azul marinho + dourado)
- Tema dark nativo do Streamlit via config.toml
- Tipografia hierárquica com labels uppercase dourados
- Gráficos plotly com o mesmo sistema de cores

### Recomendações

1. Conectar a um CRM live para scoring em tempo real
2. Adicionar dados de atividade recente (emails, ligações) 
   como feature — maior poder preditivo
3. Com 6.711 deals históricos Won/Lost, treinar modelo 
   preditivo (regressão logística) substituindo as regras

### Limitações

- `days_in_pipeline` removido por ser inútil no dataset histórico
- 68% dos deals abertos sem account identificada no CSV
- `close_value` ausente nos deals abertos — substituído por 
  `sales_price`
- Chat e Análise IA requerem chave Anthropic com créditos
- Dataset de 2016-2017 — sazonalidade baseada em padrões 
  históricos desse período

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usou |
|---|---|
| Claude (claude.ai) | Planejamento da arquitetura, decisões de scoring, análise do feedback, iteração do modelo |
| Claude Code (Desktop) | Geração e iteração de todo o código, análise dos dados reais, diagnóstico de problemas |

### Workflow

1. Discuti a arquitetura e lógica de scoring com Claude antes 
   de escrever qualquer código
2. Claude Code leu os CSVs e identificou 3 problemas nos dados 
   antes de escrever uma linha
3. Recebi feedback que uma feature contribuía 0 pts — investiguei 
   3 hipóteses de substituição com diagnóstico real dos dados
4. Escolhi sazonalidade como substituta baseado em evidência 
   quantitativa (win rate por mês calculado do histórico)
5. Adicionei chat com IA para análise conversacional do pipeline
6. Iterei o design para seguir o padrão visual G4

### Onde a IA errou e como corrigi

- Primeira feature `days_in_pipeline` implementada corretamente 
  mas inútil nos dados — identifiquei o problema validando a 
  distribuição e corrigi substituindo por sazonalidade
- CSS do dark mode causou elementos com fundo branco em várias 
  iterações — resolvi usando o sistema de temas nativo do 
  Streamlit (config.toml) com CSS mínimo complementar
- Tentei 3 abordagens de substituição antes de encontrar a 
  viável — close_date nulo e ausência de data de Prospecting 
  eliminaram duas hipóteses

### O que eu adicionei que a IA sozinha não faria

- Decisão de investigar a distribuição real da feature antes 
  de aceitar o modelo — a IA implementou days_in_pipeline 
  corretamente, mas só eu questionei se ela discriminava 
  os dados
- Escolha de sazonalidade como feature substituta — a IA 
  apresentou 3 opções, eu analisei os trade-offs e decidi
- Decisão de usar sales_price como proxy para close_value nulo 
  — julgamento de negócio, não técnico
- Identificação do padrão de win rate por mês como insight 
  real do negócio — dezembro e janeiro convertem 80% vs 55% 
  em julho

---

## Evidências

- [x] Chat exports das conversas com Claude
- [x] Git history mostrando evolução do código
- [x] Screenshots do app funcionando

---

*Submissão enviada em: abril 2026*
