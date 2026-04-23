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

#### Como isso impacta a tomada de decisão do vendedor

Antes dessa melhoria, dois deals com o mesmo vendedor recebiam 
o mesmo peso na Feature 5 — independente do setor.

Com o win rate combinado, o sistema diferencia:

**Exemplo real dos dados:**

| Situação | Vendedor | Setor | Win Rate usado | Pts Feature 5 |
|---|---|---|---|---|
| Deal A | Boris Faz | software | 81,0% | 8 pts |
| Deal B | Boris Faz | finance | 35,3% | 4 pts |
| Deal C | Markita Hansen | entertainment | 90,5% | 9 pts |
| Deal D | Markita Hansen | technology | 35,7% | 4 pts |

Na prática:
- Boris Faz abre o app e vê seus deals de software no topo — 
  o sistema sabe que ele converte 81% nesse setor
- Seus deals de finance aparecem mais abaixo — histórico de 
  apenas 35% de conversão nesse setor
- O gestor identifica que Boris Faz não deve receber leads de 
  finance e redireciona para vendedores com melhor fit
- Markita Hansen vê seus deals de entertainment priorizados 
  (90,5%) e os de technology despriorizados (35,7%) — mesmo 
  que o valor dos deals seja similar

Isso transforma o score de uma métrica genérica em uma 
recomendação personalizada — o sistema conhece os pontos 
fortes e fracos de cada vendedor com base em histórico real.

#### Melhoria 3 — Vetorização do scoring e cache da IA

**Performance do scoring:**
O scoring original usava loop Python puro com apply() e criação 
de pd.Series por linha — 2.089 iterações com overhead de objeto 
por deal. Após profiling identificamos o bottleneck e reescrevemos 
usando operações vetorizadas pandas:

- deal_stage_pts: pd.Series.map()
- close_value_pts: operação vetorial direta
- sector_wr_pts: df["sector"].map(sector_wr)
- tier: pd.cut() com bins e labels
- Apenas o combo vendedor+setor manteve loop (fallback condicional 
  necessário)

Resultado: 135ms → 54ms (2,5× mais rápido). Em produção com 
volume maior o ganho seria proporcional.

**Cache das respostas da IA:**
Cada clique em "Analisar com IA" fazia uma chamada nova à API — 
mesmo para o mesmo deal. Implementamos cache em memória com 
chave MD5 baseada nos campos relevantes do deal + modelo selecionado.

- get_recommendation(): cacheia por opportunity_id + campos do deal + model
- chat_completion(): cacheia por hash das mensagens + contexto + model  
- get_executive_summary(): cacheia por hash dos stats do pipeline

Cache HIT retorna instantaneamente sem chamada à API.
Cache MISS chama a API, armazena e retorna.

**Resumo executivo automático:**
Adicionamos na Aba Gestor um botão "Gerar resumo com IA" que 
envia os dados agregados do pipeline para o Claude e retorna 
4 bullets executivos com insights acionáveis — top vendedor, 
setor com mais Tier A, meses de maior e menor conversão histórica. 
O resultado é cacheado na sessão para não regenerar a cada 
interação.

---

### Como o app ajuda o vendedor na prática

O objetivo central do sistema não é gerar um número — é ajudar 
o vendedor a tomar decisões melhores em menos tempo. Cada parte 
do app foi pensada para isso:

#### Segunda-feira de manhã — Aba Pipeline

O vendedor filtra pelo próprio nome na sidebar e vê 
imediatamente seus deals ordenados por score. Tier A em verde, 
Tier B em dourado, Tier C em vermelho. Sem precisar analisar 
nada: os deals que merecem atenção hoje estão no topo.

O score não é uma caixa preta — o vendedor consegue entender 
rapidamente por que um deal está bem ou mal posicionado pelas 
cores e pela posição na tabela.

#### Entendendo o score — Aba Análise IA

Ao clicar em qualquer deal, o vendedor vê o breakdown visual 
do score: um gráfico de barras mostrando quantos pontos cada 
feature contribuiu. Ele entende imediatamente se o deal está 
bem rankeado por causa do estágio, do setor, do valor ou da 
sazonalidade.

Com a chave da API conectada, o botão "Analisar com IA" gera 
em segundos:
- O principal risco daquele deal específico
- A próxima ação recomendada para hoje ou amanhã
- Uma justificativa conectando os dados ao score

#### Análise conversacional — Aba Chat com IA

O vendedor pode fazer perguntas em linguagem natural sobre 
o próprio pipeline, sem precisar filtrar tabelas ou interpretar 
gráficos:

- "Quais meus 3 melhores deals para fechar essa semana?"
- "Por que meu score médio está baixo?"
- "Quais setores têm mais chance de fechar?"
- "Quais deals devo abandonar?"

O chat usa os dados reais do pipeline filtrado — responde com 
contas, números e contexto específico do vendedor, não respostas 
genéricas. Tem filtros inline por vendedor, tier e região 
independentes da sidebar.

#### Visão do gestor — Aba Gestor

O manager vê em uma tela quais vendedores têm mais deals Tier A, 
o valor total do pipeline por equipe, e o win rate histórico por 
mês — útil para entender sazonalidade e planejar metas.

O gráfico de win rate por mês mostra visualmente quais períodos 
historicamente convertem melhor, ajudando a calibrar expectativas 
e intensidade de esforço ao longo do ano.

#### Resultado esperado

Um vendedor com 80-100 deals abertos gastava tempo decidindo 
no feeling onde focar. Com o app, em menos de 2 minutos ele 
sabe quais são seus top deals, por que estão priorizados, 
qual a próxima ação recomendada e pode perguntar qualquer 
coisa sobre o pipeline em linguagem natural.

#### Flexibilidade de provedor de IA

O app suporta 3 provedores de IA intercambiáveis — o usuário 
escolhe na sidebar e cola a própria chave:

| Provedor | Modelo | Quando usar |
|---|---|---|
| Anthropic | Claude Sonnet/Haiku | Melhor qualidade de análise |
| Google | Gemini 2.0 Flash Lite | Gratuito com conta Google |
| OpenAI | GPT-4o mini | Alternativa acessível |

O scoring por regras funciona 100% sem nenhuma chave — 
a IA é uma camada de enriquecimento opcional.

---

### Resultados

- 2.072 deals abertos processados e priorizados
- 32 deals Tier A (score ≥70) — R$ 486.015 em valor total
- 2.040 deals Tier B — pipeline principal de trabalho
- Win rates reais calculados: por setor, por vendedor e por 
  combinação vendedor+setor (235 combinações com ≥10 deals)
- Scoring vetorizado com pandas — 2,5x mais rápido que loop Python
- Cache em memória para respostas da IA — zero rechamadas para 
  o mesmo deal na mesma sessão
- Interface com 4 abas: Pipeline / Análise IA / Chat com IA / Gestor
- Suporte a 3 provedores de IA: Anthropic Claude, Google Gemini 
  e OpenAI GPT-4o mini — usuário escolhe na sidebar e cola 
  a própria chave

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
- IA requer chave própria do usuário (Anthropic, Google ou 
  OpenAI) — o scoring por regras funciona sem chave, mas 
  chat e análise detalhada dependem de API key com créditos

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usou |
|---|---|
| Claude (claude.ai) | Planejamento da arquitetura, decisões de scoring, análise do feedback, iteração do modelo |
| Claude Code (Desktop) | Geração e iteração de todo o código, análise dos dados reais, diagnóstico de problemas |

### Técnicas de prompting utilizadas

Cada interação com o modelo foi estruturada com técnicas deliberadas de engenharia de prompt — não prompts genéricos.

**Role prompting + domain grounding**
Cada sessão iniciou com definição explícita de persona e contexto de domínio, ancorando o modelo no problema real antes de qualquer instrução técnica. Efeito: o modelo priorizou decisões de negócio sobre soluções técnicas genéricas — ex: sugeriu win rate histórico como feature antes de qualquer métrica de ML clássica.

Exemplo aplicado:
"Você é um especialista em RevOps e análise de dados para times de vendas B2B. Está construindo um MVP funcional de Lead Scoring. O critério principal de avaliação é: funciona de verdade, o vendedor consegue usar, e o scoring vai além do óbvio."

**Data grounding via file injection**
Antes de qualquer geração de código, o Claude Code foi instruído a inspecionar os arquivos reais do dataset. Isso forçou o modelo a trabalhar com o schema real — valores exatos de deal_stage, tipos de coluna, distribuição de nulos — evitando código escrito para dados imaginários. Foi essa inspeção que revelou o GTXPro vs GTX Pro, o close_value nulo nos deals abertos e o dataset de 2016-2017.

Exemplo aplicado:
"PRIMEIRA AÇÃO OBRIGATÓRIA: leia todos os arquivos em data/ e liste os campos reais e valores exatos de deal_stage antes de escrever qualquer linha de código."

**Diagnostic-first prompting**
Para qualquer problema identificado, o prompt bloqueava a geração de solução até que o diagnóstico estivesse completo. Resultado: em vez de substituir NaN por zero (correção superficial), o modelo identificou que 68% dos deals abertos não tinham account no CSV de origem — limitação real documentada, não escondida.

Exemplo aplicado:
"Antes de corrigir os NaNs, investigue a causa raiz. Mostre quantas linhas têm NaN por coluna e quais valores do sales_pipeline não casaram com as outras tabelas."

**Chain-of-thought estruturado para análise exploratória**
Na etapa de aprofundamento do scoring, o prompt decompôs a análise em sub-queries independentes antes de qualquer conclusão. Essa decomposição forçou o modelo a calcular cada dimensão separadamente antes de sintetizar — o que permitiu identificar que a variação de 54 pp em combinações vendedor+setor era estrutural, não ruído amostral.

Exemplo aplicado:
"Analise os dados históricos e responda em sequência: 1) win rate por deal_stage de entrada, 2) tabela cruzada sector x stage x win_rate, 3) win rate por sales_agent com ranking, 4) win rate por produto, 5) combinações sales_agent x sector com delta maior que 10pp vs média global."

**Output-constrained prompting para validação**
Cada implementação foi acompanhada de critério de aceitação explícito no próprio prompt. Isso criou um loop de validação quantitativa — a mudança só era aceita se os números confirmassem o comportamento esperado, não apenas se o código rodasse sem erro.

Exemplo aplicado:
"Após implementar, mostre obrigatoriamente: quantas combinações vendedor+setor têm 10 ou mais deals, top 5 win rate e bottom 5 win rate, comparação da distribuição Tier A/B/C antes e depois."

**Human-in-the-loop para decisões de negócio**
A divisão de responsabilidade foi explícita ao longo de todo o projeto. A IA executou: leitura de dados, geração de código, cálculo de win rates, validação de distribuições. O humano decidiu: qual hipótese investigar, qual feature faz sentido de negócio, qual trade-off aceitar.

Exemplo concreto: o modelo calculou que a variação de vendedor+setor chegava a 54 pp. A interpretação — que isso representa fit vendedor+setor e não talento individual, e que Boris Faz não deveria receber leads de finance — foi decisão humana com base nos números.

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
7. Após receber feedback que o scoring precisava de mais 
   profundidade, rodei uma análise exploratória completa dos 
   6.711 deals históricos com o Claude Code para identificar 
   quais features tinham mais poder preditivo real. A análise 
   revelou que a combinação vendedor + setor tinha variação de 
   até 54 pp — muito maior que qualquer feature isolada. Com 
   base nesse diagnóstico, decidi substituir o win rate do 
   vendedor isolado pelo win rate combinado vendedor + setor 
   com fallback inteligente.
8. Após implementar as melhorias analíticas, identifiquei 
   gargalos de performance com profiling real (timeit sobre 
   5 execuções) e reescrevi o scoring com operações vetorizadas 
   pandas. Implementei cache em memória com hash MD5 para evitar 
   rechamadas desnecessárias à API — decisão de custo e UX, 
   não só performance técnica.
9. Durante a hospedagem, tentei usar Gemini API no free tier 
   para deixar a IA ativa sem custo. Descobri que a conta 
   precisava de faturamento configurado e que o modelo 
   disponível variava por região e plano. Em vez de forçar 
   um único provider com limitações, decidi arquitetar o 
   sistema para suportar 3 providers intercambiáveis — 
   Anthropic, Google e OpenAI — com o usuário trazendo 
   a própria chave. Isso elimina dependência de custo meu 
   e torna o app mais flexível para demonstração.

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
- Na análise de aprofundamento do scoring, o Claude Code 
  apresentou os dados brutos de win rate por combinação 
  vendedor+setor mas não identificou automaticamente o insight 
  de negócio mais importante: que a variação não é de talento 
  individual (apenas 15 pp de spread entre vendedores) mas sim 
  de fit vendedor+setor (até 54 pp). Essa leitura foi minha — 
  a IA trouxe os números, eu trouxe a interpretação.

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
- Interpretação do padrão vendedor+setor como problema de fit, 
  não de talento — isso mudou a feature de "quão bom é esse 
  vendedor" para "quão adequado é esse vendedor para esse setor 
  específico". A IA calculou os números, eu defini o que eles 
  significavam para o negócio.
- Decisão de cachear respostas da IA por hash de conteúdo — 
  a IA implementou o cache, mas a decisão de qual granularidade 
  usar (por deal vs por sessão vs por modelo) foi minha, 
  balanceando custo de API, freshness dos dados e UX
- Identificação do bottleneck real de performance via profiling 
  antes de otimizar — em vez de otimizar às cegas, medi primeiro 
  e otimizei onde importava
- Decisão arquitetural de suportar múltiplos providers de IA 
  em vez de forçar um único — surgiu de uma limitação prática 
  (quota do Gemini) mas virou um diferencial de design: 
  o app não está acoplado a nenhum provider específico e 
  pode ser adaptado conforme o custo e disponibilidade 
  de cada organização

---

## Evidências

- [x] Chat exports das conversas com Claude
- [x] Git history mostrando evolução do código
- [x] Screenshots do app funcionando

---

*Submissão enviada em: abril 2026*
