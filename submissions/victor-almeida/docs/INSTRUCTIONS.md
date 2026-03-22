# Conversa: Lead Scorer Challenge — G4

**Data:** 21 de março de 2026

---

## [Eu] Contexto do Challenge

Isso é um challenge pra entrar no G4, eu li mas mesmo assim queria sua percepção do que é esse problema de fato, e do que vamos resolver.

**Challenge 003 — Lead Scorer**

**Área:** Vendas / RevOps **Tipo:** Build (construir solução funcional) **Time budget:** 4-6 horas

### Contexto

Você é o novo AI Master da área de Vendas. O time comercial tem 35 vendedores distribuídos em escritórios regionais, gerenciados por managers, trabalhando um pipeline de ~8.800 oportunidades. Hoje, a priorização é feita "no feeling" — cada vendedor decide quais deals focar com base na própria experiência e intuição.

A Head de Revenue Operations te chamou e disse:

> "Nossos vendedores gastam tempo demais em deals que não vão fechar e deixam oportunidades boas esfriar. Preciso de algo funcional — não um modelo no Jupyter Notebook que ninguém vai usar. Quero uma ferramenta que o vendedor abra, veja o pipeline, e saiba onde focar. Pode ser simples, mas precisa funcionar."

Este é o challenge mais "mão na massa". O deliverable principal é software funcionando — não um documento.

### Dados disponíveis

Quatro tabelas de um CRM, todas interconectadas:

Dataset: **CRM Sales Predictive Analytics** (licença CC0)

|Arquivo|O que contém|Registros|Campos-chave|
|---|---|---|---|
|`accounts.csv`|Contas clientes — setor, receita, número de funcionários, localização, empresa-mãe|~85|`account`|
|`products.csv`|Catálogo de produtos com série e preço|7|`product`|
|`sales_teams.csv`|Vendedores com seu manager e escritório regional|35|`sales_agent`|
|`sales_pipeline.csv`|Pipeline completo — cada oportunidade com stage, datas, vendedor, produto, conta e valor de fechamento|~8.800|`opportunity_id` → liga tudo|

### Estrutura dos dados

```
accounts ←── sales_pipeline ──→ products
                   ↓
              sales_teams
```

O `sales_pipeline.csv` é a tabela central. Cada registro é uma oportunidade com:

- `deal_stage`: Prospecting, Engaging, Won, Lost
- `engage_date` / `close_date`: timeline do deal
- `close_value`: valor real de fechamento (0 se Lost)

### O que entregar

**1. Solução funcional (obrigatório)**

Construa algo que um vendedor possa usar. Não importa a tecnologia — importa que funcione.

Exemplos de soluções válidas:

- Aplicação web (Streamlit, React, HTML+JS, qualquer coisa)
- Dashboard interativo (Plotly Dash, Retool, Metabase)
- CLI tool ou script que gera relatório priorizados
- API que recebe dados de um deal e retorna score + explicação
- Planilha inteligente com fórmulas de scoring
- Bot que envia prioridades por Slack/email

Requisitos mínimos:

- Precisa rodar (não é mockup, wireframe ou PowerPoint)
- Precisa usar os dados reais do dataset
- Precisa ter lógica de scoring/priorização (não é só ordenar por valor)
- O vendedor precisa entender por que um deal tem score alto ou baixo

**2. Documentação mínima (obrigatório)**

- Setup: Como rodar a solução (dependências, comandos, URL)
- Lógica: Que critérios de scoring você usou e por quê
- Limitações: O que a solução não faz e o que precisaria pra escalar

**3. Process log (obrigatório)**

Evidências de como você usou IA para construir. Leia o Guia de Submissão.

### Critérios de qualidade

- A solução funciona de verdade? Dá pra rodar seguindo as instruções?
- O scoring faz sentido? Usa as features certas? Vai além do óbvio?
- O vendedor (não-técnico) consegue usar e entender?
- A interface ajuda a tomar decisão ou só mostra dados?
- O código é limpo o suficiente pra outro dev dar manutenção?

### Dicas

- A Head de RevOps não pediu ML perfeito. Pediu algo útil. Comece simples, itere.
- Deal stage, tempo no pipeline, tamanho da conta, produto e vendedor são features óbvias. O que mais importa? Olhe os dados.
- Um scoring baseado em regras + heurísticas, bem apresentado, vale mais que um XGBoost sem interface.
- Explainability ganha. Se o vendedor entender POR QUE o deal tem score 85, a ferramenta é 10x mais útil que um número sem contexto.
- Pense no uso real: o vendedor abre isso na segunda-feira de manhã. O que ele precisa ver?
- Bonus: se a solução tiver filtro por vendedor/manager/região, fica imediatamente mais útil.

---

## [Claude] Minha leitura do problema

O que está acontecendo aqui é bem claro e é um problema clássico de RevOps: **alocação ineficiente de atenção comercial**. Com 35 vendedores e ~8.800 oportunidades, cada vendedor está lidando com ~250 deals em média. Sem critério objetivo, o vendedor naturalmente gravita pro deal que ele "sente" que vai fechar — que muitas vezes é o que ele tem mais afinidade, não o que tem maior probabilidade real.

O resultado são dois problemas simétricos: tempo queimado em deals mortos e deals bons que esfriam por falta de follow-up.

**O que a Head de RevOps está pedindo na essência:** trocar "feeling" por dados, mas de um jeito que o vendedor realmente use. Ela já sabe que um modelo num notebook não resolve nada — o gargalo não é inteligência analítica, é **adoção**. Por isso a ênfase em "funcional" e "que o vendedor abra e saiba onde focar".

**O que vamos construir:** uma aplicação web com scoring baseado em regras e heurísticas extraídas dos dados reais. O scoring vai considerar coisas como deal stage, tempo no pipeline (deals parados há muito tempo tendem a morrer), tamanho da conta, produto, e win rate histórica do vendedor e da conta. Cada score vai ter uma explicação legível — "Score 82: conta grande, produto premium, mas deal parado há 45 dias". Filtros por vendedor, manager e região pra cada nível da hierarquia conseguir usar.

---

## [Eu] Perguntas de refinamento

Claude preciso refinar ainda mais o entendimento do problema, vou mandar algumas perguntas:

1. **Valor vs Probabilidade:** Como vamos equilibrar o Valor do Deal versus a Probabilidade de Fechamento? Um deal de R$ 100 mil com 20% de chance vale mais a atenção do vendedor do que um de R$ 5 mil com 90%? Como o algoritmo vai refletir o Valor Esperado para garantir que o vendedor não foque apenas em contas pequenas fáceis?
    
2. **Sales Velocity:** Quero que você analise a Sales Velocity. Qual o tempo médio de conversão de cada estágio? Se um deal passar 20% acima desse tempo médio sem mudar de fase, o score deve cair drasticamente. Como vamos implementar essa penalidade de score por inatividade ou estagnação?
    
3. **Win Rate por Vendedor/Setor:** Temos dados de sales_team. Como podemos normalizar o score com base na Win Rate histórica do vendedor? Se o Vendedor A tem 80% de win rate em contas do setor Software, o score de um deal desse setor para ele deve ser maior do que para o Vendedor B que nunca vendeu para esse setor?
    
4. **Next Best Action:** Além do score e da explicação, a ferramenta pode sugerir uma Próxima Melhor Ação? Ex: Se o score caiu porque o deal está parado há 15 dias, a ferramenta deve dizer "Ação sugerida: Enviar case de sucesso do setor X". Como estruturar essa lógica de recomendações baseada nos motivos do score?
    
5. **Deal Zumbi:** Como podemos usar os dados para identificar Lixo no Pipeline? Consegue criar um filtro ou uma flag de "Deal Zumbi" para oportunidades que têm valor alto, mas comportamento de dados (datas e estágios) que indicam que nunca vão fechar? Isso ajudaria o Manager a limpar o forecast.
    

---

## [Claude] Respostas conceituais (pré-dados)

### 1. Valor do Deal vs. Probabilidade — o conceito de Expected Value

A resposta curta: **nunca usar valor bruto nem probabilidade isolada**. O score precisa refletir o **Valor Esperado (EV)**, que é `valor × probabilidade`. O deal de R$100k com 20% tem EV de R$20k. O de R$5k com 90% tem EV de R$4.5k. Nesse caso, o deal grande ainda vale mais atenção.

Mas tem um detalhe que o EV simples ignora: **esforço restante**. Um deal em Engaging com 90% de chance precisa de um push final — o custo de atenção é baixo. Um deal em Prospecting com 20% vai consumir semanas do vendedor. Então o score ideal seria algo como:

```
Score = (Valor × Probabilidade) / Esforço Estimado Restante
```

Na prática, vamos implementar isso como um **score composto com pesos**. A probabilidade base vem do stage (Prospecting = baixa, Engaging = alta), ajustada pelos outros fatores. O valor entra como multiplicador, mas com uma curva logarítmica pra não deixar um mega-deal dominar tudo — senão o vendedor vai ficar obcecado com a baleia branca e ignorar 20 deals médios que somam mais.

A implementação seria algo como:

```
base_probability = stage_probability × decay_factor × seller_fit
value_component = log(1 + close_value) / log(1 + max_value)  
expected_score = (base_probability × 0.6) + (value_component × 0.4)
```

Os pesos (60/40) são um ponto de partida — com os dados reais a gente calibra.

### 2. Sales Velocity e Penalidade por Estagnação

Essa é provavelmente a feature mais importante do scoring. A lógica:

**Primeiro**, calcular o tempo médio que deals **Won** levaram em cada transição (Prospecting → Engaging, Engaging → Won). Isso nos dá o benchmark de velocidade saudável.

**Segundo**, pra cada deal ativo, calcular quanto tempo ele está no stage atual versus a média.

**A penalidade seria exponencial, não linear:**

```
dias_no_stage = hoje - data_entrada_no_stage
media_stage = media_dias_won_nesse_stage
ratio = dias_no_stage / media_stage

if ratio <= 1.0:  decay = 1.0       (dentro do normal)
if ratio 1.0-1.2: decay = 0.85      (atenção)  
if ratio 1.2-1.5: decay = 0.60      (alerta)
if ratio > 1.5:   decay = 0.30      (deal zumbi candidato)
if ratio > 2.0:   decay = 0.10      (quase morto)
```

Por que exponencial e não linear? Porque os dados de pipeline geralmente seguem uma distribuição onde, passado certo ponto, a probabilidade de conversão despenca. Um deal que está 50% acima do tempo médio não é "um pouco pior" — ele é **drasticamente** pior. A curva de decaimento precisa refletir isso.

### 3. Win Rate do Vendedor por Setor (Seller-Deal Fit)

Cruzando `sales_pipeline` com `sales_teams` e `accounts`, a gente consegue calcular:

- Win rate geral de cada vendedor
- Win rate **por setor** de cada vendedor
- Win rate **por faixa de valor** de cada vendedor

O ajuste de score funcionaria como um **multiplicador de fit**:

```
seller_sector_winrate = wins do vendedor nesse setor / total de deals dele nesse setor
team_sector_winrate = wins do time nesse setor / total do time nesse setor

if vendedor tem >= 5 deals no setor:
    fit_multiplier = seller_sector_winrate / team_sector_winrate
else:
    fit_multiplier = 1.0  (dados insuficientes, usa média)
```

Isso resolve o exemplo: se o Vendedor A tem 80% de win rate em Software vs 45% do time, o `fit_multiplier` dele seria ~1.78 pra deals de Software. O deal automaticamente sobe no ranking dele.

**O cuidado importante:** com 35 vendedores e ~85 contas, algumas combinações vendedor×setor vão ter poucos dados. É preciso um **threshold mínimo** (5 deals) antes de usar a taxa específica. Abaixo disso, usa a média do time como fallback.

### 4. Próxima Melhor Ação (NBA - Next Best Action)

A lógica de recomendação seria **baseada em regras derivadas dos fatores do score**:

```
REGRAS NBA:

SE deal parado > média do stage:
   → "Deal parado há X dias. Agendar follow-up ou requalificar."
   
SE deal parado > 1.5× média:
   → "Deal em risco de esfriar. Enviar case de sucesso do setor [setor da conta]."

SE valor alto + stage Prospecting há muito tempo:
   → "Conta de alto valor ainda em Prospecting. Considerar envolver manager para aceleração."

SE vendedor tem baixo win rate nesse setor:
   → "Seu histórico nesse setor é abaixo da média. Consultar [vendedor com melhor rate] para estratégia."

SE conta tem múltiplos deals lost:
   → "Esta conta já teve X deals perdidos. Revisar approach antes de investir mais tempo."

SE deal está em Engaging + valor alto + tempo OK:
   → "Deal saudável e de alto valor. Prioridade máxima para fechar esta semana."
```

Na interface, isso aparece como um card junto ao score: **"Score 72 ↓ — Deal parado há 18 dias (média: 12). Ação: agendar call de requalificação."**

A sacada é que a NBA transforma o score de um número passivo numa **instrução ativa**. O vendedor não precisa interpretar — ele sabe o que fazer.

### 5. Deal Zumbi — Limpeza de Pipeline

Definição de Deal Zumbi seria multicritério:

```
DEAL É ZUMBI SE:
  (tempo_no_stage > 2× média do stage)
  E (deal_stage != "Won" e != "Lost")
  
DEAL É ZUMBI CRÍTICO SE:
  Zumbi = True
  E close_value > percentil 75 de valor
  (porque infla o forecast sem probabilidade real de fechar)
```

Na interface:

- Uma **flag visual** (tag vermelha "Zumbi") nos deals do pipeline
- Um **filtro dedicado** "Mostrar Deal Zumbis" que o manager usa na reunião de forecast
- Um **resumo** tipo: "12 deals zumbis representando R$X em pipeline inflado"

Camada adicional: **padrão de conta**. Se uma conta já teve 2+ deals que foram Lost, e tem um novo deal ativo parado, a probabilidade desse deal ser zumbi é muito maior.

### Resumo da Arquitetura do Score

```
SCORE FINAL (0-100) = 

  Base (Stage)           × 30%    [Prospecting=30, Engaging=70]
  + Valor Esperado       × 25%    [log-scaled do close_value]  
  + Velocidade           × 25%    [decay por tempo no stage]
  + Seller-Deal Fit      × 10%    [win rate vendedor × setor]
  + Saúde da Conta       × 10%    [histórico de wins/losses na conta]

  FLAGS:
  - Deal Zumbi (tempo > 2× média)
  - Conta Recorrente Lost (2+ losses)
  
  OUTPUT:
  - Score numérico (0-100)
  - Explicação textual dos fatores
  - Next Best Action
  - Flag de Zumbi (se aplicável)
```

---
## [Eu] Envio dos arquivos csv
![[accounts.csv]]

![[metadata.csv]]

![[products.csv]]

![[sales_pipeline.csv]]

![[sales_teams 1.csv]]

## [Claude] Análise dos Dados Reais — Calibração do Scoring

Após receber os CSVs, realizei uma análise exploratória completa. Aqui estão os achados que calibram cada componente:

### Visão Geral do Dataset

|Métrica|Valor|
|---|---|
|Total de oportunidades|8.800|
|Won|4.238 (48.2%)|
|Lost|2.473 (28.1%)|
|Engaging (ativo)|1.589 (18.1%)|
|Prospecting (ativo)|500 (5.7%)|
|Win Rate (deals fechados)|**63.2%**|
|Contas únicas|~85|
|Vendedores|35 (27 com deals ativos)|
|Produtos|7|

### 1. Valor vs. Probabilidade — Calibração

Distribuição de valor extremamente bimodal:

|Produto|Preço Lista|Avg Won Value|WR|
|---|---|---|---|
|GTK 500|$26.768|$26.707|60.0%|
|GTX Plus Pro|$5.482|$5.490|64.3%|
|GTXPro|$4.821|$4.816|63.6%|
|MG Advanced|$3.393|$3.389|60.3%|
|GTX Plus Basic|$1.096|$1.080|62.1%|
|GTX Basic|$550|$546|63.7%|
|MG Special|$55|$55|64.8%|

**Achado:** A diferença de valor entre produtos é de **486x** (GTK 500 vs MG Special). Win rates são surpreendentemente similares entre produtos (~60-65%). Isso confirma a necessidade da curva logarítmica — sem ela, GTK 500 domina todo o scoring.

### 2. Sales Velocity — O Dado Mais Revelador

**Deals Won (Engaging → Close):**

- Mediana: **57 dias**
- P25: 9 dias | P75: 88 dias | P90: 106 dias

**Deals Lost (Engaging → Close):**

- Mediana: **14 dias** — perdem rápido

**Deals Ativos em Engaging:**

- Mediana: **165 dias** no stage
- **96.7%** já passaram da mediana de velocidade dos Won
- **88.3%** estão acima do dobro da mediana

**Win Rate por Bucket de Velocidade:**

|Bucket (dias)|Win Rate|n|
|---|---|---|
|0-15|56.1%|2.877|
|15-30|71.3%|286|
|30-60|66.3%|569|
|60-90|66.5%|1.621|
|90-120|70.4%|1.165|
|120-150|75.6%|193|

**Achado contra-intuitivo:** Deals que fecham entre 90-150 dias têm WR **mais alta** (70-75%) do que deals de 0-15 dias (56%). Deals rápidos incluem muitos que são desqualificados rapidamente. Deals que sobrevivem mais e fecham são deals maiores e mais trabalhados.

**Calibração:** O decay não deve começar aos 57 dias (mediana), mas sim mais perto do **P75 (88 dias)**, com decaimento forte após **120 dias**.

### 3. Win Rate por Vendedor e Setor

**Variação entre vendedores:**

- Top: Hayden Neloms (70.4%, 152 deals) e Maureen Marcano (70.0%, 213 deals)
- Bottom: Lajuana Vencill (55.0%, 231 deals) e Markita Hansen (57.3%, 227 deals)

**Combinações Vendedor × Setor (272 com ≥5 deals):**

Melhores fits (WR > 80%):

|Vendedor|Setor|WR|Deals|
|---|---|---|---|
|Rosalina Dieter|marketing|100%|7|
|Moses Frase|telecom|100%|6|
|Wilburn Farren|finance|100%|7|
|Cecily Lampkin|software|91.7%|12|
|Markita Hansen|entertainment|90.5%|21|

Piores fits (WR < 40%):

|Vendedor|Setor|WR|Deals|
|---|---|---|---|
|Donn Cantrell|telecom|30.0%|10|
|Jonathan Berthelot|employment|33.3%|6|
|Markita Hansen|technology|35.7%|28|
|Boris Faz|finance|35.3%|17|

**Achado:** Markita Hansen tem 90.5% WR em entertainment mas 35.7% em technology — a mesma vendedora performa radicalmente diferente por setor. Isso valida fortemente o multiplicador de Seller-Deal Fit.

### 4. Win Rate por Setor da Conta

|Setor|Win Rate|Deals|
|---|---|---|
|marketing|64.8%|623|
|entertainment|64.7%|402|
|MG Special|64.8%|1.223|
|software|63.9%|704|
|retail|63.1%|1.267|
|technology|63.4%|1.058|
|services|63.4%|352|
|employment|62.6%|286|
|medical|62.3%|950|
|telecom|62.5%|456|
|finance|61.2%|613|

**Achado:** Win rates por setor são bastante homogêneas (61-65%). A variação setor×vendedor é muito mais significativa que o setor isolado.

### 5. Deal Zumbi — Diagnóstico do Pipeline

**Deals ativos em Engaging:**

- 1.589 deals
- Mediana de **165 dias** no stage (referência Won: 57 dias)
- Média de **77 deals ativos por vendedor** (range: 31-194)

**Contas com múltiplos losses:**

- 85 contas têm 3+ losses
- Top: Hottechi (82 losses), Kan-code (72), Konex (63)

**Achado:** O pipeline está massivamente inflado. A maioria dos deals Engaging já ultrapassou qualquer benchmark razoável de velocidade. Os "Deal Zumbis" não são exceção — são quase regra neste dataset. O threshold de classificação precisa ser calibrado cuidadosamente pra ter utilidade (senão tudo é zumbi).

### Estrutura dos Dados — Notas Técnicas

- Deals em **Prospecting**: sem engage_date, sem close_date, sem close_value (tudo null)
- Deals em **Engaging**: têm engage_date, mas sem close_date e sem close_value (null)
- Deals **Won**: close_value = valor real do fechamento
- Deals **Lost**: close_value = 0
- O "hoje" para cálculos usa a data máxima do dataset: **2017-12-31**
- Revenue das contas é em **milhões de USD** (range: $4.5M a $11.7B)

---

_Próximo passo: construir a aplicação web com scoring calibrado a partir destes achados._