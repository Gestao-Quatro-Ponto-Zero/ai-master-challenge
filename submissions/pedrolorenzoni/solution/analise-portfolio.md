# Análise de Portfólio — CRM Sales Predictive Analytics

## Contexto

Dataset: **CRM Sales Predictive Analytics** (Kaggle)
Objetivo: análise exploratória da carteira de clientes para subsidiar priorização de vendas e estratégias de abordagem.

O documento é construído iterativamente — cada seção corresponde a um CSV do dataset.

---

## 1. Contas — `accounts.csv`

**85 contas · 7 atributos**

| Coluna | Tipo | Descrição |
|---|---|---|
| `account` | string | Nome da conta |
| `sector` | string | Setor (contém typo — ver Qualidade de Dados) |
| `year_established` | int | Ano de fundação |
| `revenue` | float | Receita anual (unidade presumida: milhões USD) |
| `employees` | int | Número de funcionários |
| `office_location` | string | País/região da sede |
| `subsidiary_of` | string | Empresa-mãe (vazio se independente) |

---

### 1.1 Distribuição Geográfica

| País | Contas | % |
|---|---|---|
| United States | 71 | 83,5% |
| Japan | 1 | 1,2% |
| Korea | 1 | 1,2% |
| Italy | 1 | 1,2% |
| Norway | 1 | 1,2% |
| Germany | 1 | 1,2% |
| Belgium | 1 | 1,2% |
| Romania | 1 | 1,2% |
| Poland | 1 | 1,2% |
| Jordan | 1 | 1,2% |
| Brazil | 1 | 1,2% |
| Panama | 1 | 1,2% |
| China | 1 | 1,2% |
| Kenya | 1 | 1,2% |
| Philippines | 1 | 1,2% |
| **Total** | **85** | **100%** |

A carteira é fortemente concentrada nos EUA. As 14 contas internacionais estão distribuídas em 14 países distintos — sem concentração regional fora dos EUA.

---

### 1.2 Distribuição por Setor

| Setor | Contas | % |
|---|---|---|
| Retail | 17 | 20,0% |
| Technology* | 12 | 14,1% |
| Medical | 12 | 14,1% |
| Finance | 8 | 9,4% |
| Marketing | 8 | 9,4% |
| Software | 7 | 8,2% |
| Telecommunications | 6 | 7,1% |
| Entertainment | 6 | 7,1% |
| Services | 5 | 5,9% |
| Employment | 4 | 4,7% |
| **Total** | **85** | **100%** |

\* Todos os 12 registros de tecnologia usam o valor `technolgy` (com typo) — ver seção 1.5.

Retail domina com 1 em cada 5 contas. Technology e Medical empatam em segundo lugar.

---

### 1.3 Segmentação por Porte (Receita)

Critério de segmentação baseado em receita anual:

| Segmento | Faixa (M USD) | Contas | % |
|---|---|---|---|
| **Enterprise** | > 2.000 | 33 | 38,8% |
| **Mid-Market** | 500 – 2.000 | 31 | 36,5% |
| **SMB** | < 500 | 21 | 24,7% |

**Amplitude extrema:** receita vai de 4,54 M (Condax) a 11.698 M (Kan-code) — razão de ~2.577×. Isso exige estratégias de abordagem muito distintas por segmento.

**Enterprise — maiores contas por receita:**

| Conta | Setor | Receita (M) | Funcionários |
|---|---|---|---|
| Kan-code | Software | 11.698 | 34.288 |
| Hottechi | Technology | 8.170 | 16.499 |
| Xx-holding | Finance | 7.537 | 20.293 |
| Konex | Technology | 7.708 | 13.756 |
| Initech | Telecommunications | 6.395 | 20.275 |
| Scotfind | Software | 6.355 | 16.780 |
| Treequote | Telecommunications | 5.266 | 8.595 |
| Ganjaflex | Retail | 5.159 | 17.479 |
| Fasehatice | Retail | 4.969 | 7.523 |

**SMB — menores contas por receita:**

| Conta | Setor | Receita (M) | Funcionários |
|---|---|---|---|
| Condax | Medical | 4,54 | 9 |
| Zencorporation | Technology | 40,79 | 142 |
| Scottech | Marketing | 45,39 | 100 |
| Golddex | Finance | 52,50 | 165 |
| Zathunicon | Retail | 71,12 | 144 |

---

### 1.4 Estrutura Corporativa — Grupos e Subsidiárias

**15 contas são subsidiárias (17,6%)**, agrupadas em 7 grupos corporativos:

| Grupo (Empresa-mãe) | Subsidiárias | Receita combinada (M) |
|---|---|---|
| **Acme Corporation** | Bluth Company, Codehow, Donquadtech, Iselectrics | 1.100 + 1.242 + 2.715 + 1.713 + 527 = **7.297** |
| **Sonron** | Faxquote, Gogozoom, Treequote | 1.700 + 1.826 + 87 + 5.266 = **8.879** |
| **Bubba Gump** | Dalttechnology, Scotfind | 987 + 99 + 6.355 = **7.441** |
| **Inity** | dambase, Scottech | 2.404 + 2.174 + 45 = **4.623** |
| **Golddex** | Funholding, Vehement Capital Partners | 53 + 2.820 + 646 = **3.519** |
| **Warephase** | Nam-zim | 2.042 + 406 = **2.448** |
| **Massive Dynamic** | Cheers | 665 + 4.270 = **4.935** |

> Nota: a receita combinada soma matriz + todas as subsidiárias do grupo, para referência de tamanho do conglomerado.

**Implicação:** ao abordar subsidiárias, a venda pode demandar envolvimento da matriz. As 70 contas independentes têm decisão autônoma.

---

### 1.5 Qualidade de Dados

| Problema | Detalhe | Impacto |
|---|---|---|
| **Typo em `sector`** | `technolgy` (sem o segundo `o`) em 12 registros | Quebra filtros/agrupamentos por setor — normalização obrigatória antes de qualquer análise |
| **`subsidiary_of` vazio** | 70 contas sem valor — semanticamente correto para independentes, mas não há flag explícito | Sem impacto funcional se tratado como "independente" quando vazio |
| **Unidade de `revenue` não documentada** | Valores sugerem milhões USD, mas não há metadado confirmatório | Risco de interpretação errada ao comparar com outros datasets |
| **Typo em `office_location`** | `Philipines` (deveria ser `Philippines`) — 1 ocorrência (Bioholding) | Pode afetar agrupamentos geográficos |

**Ação recomendada antes de qualquer análise downstream:**
```python
df['sector'] = df['sector'].str.replace('technolgy', 'technology')
df['office_location'] = df['office_location'].str.replace('Philipines', 'Philippines')
```

---

### 1.6 Insights para Priorização de Vendas

1. **Concentre esforço Enterprise primeiro.** 33 contas (38,8%) respondem pelo grosso do volume potencial de receita. As 9 maiores sozinhas somam mais de 60.000 funcionários — tickets médios de negociação tendem a ser maiores.

2. **Retail + Technology + Medical = 48% da carteira.** Abordagens setoriais (casos de uso, provas de conceito, referências) devem cobrir esses três setores prioritariamente.

3. **Navegação corporativa nos grupos.** Acme Corporation, Sonron e Bubba Gump são os três maiores conglomerados. Uma venda ao grupo pode abrir pipeline para 2–4 subsidiárias. Sonron (com Treequote e Faxquote) tem a maior receita combinada estimada (~8,9 B).

4. **SMB: atenção seletiva.** 21 contas SMB (< 500 M) incluem subsidiárias de grupos maiores (ex.: Dalttechnology pertence a Bubba Gump, Scottech pertence a Inity). Mesmo contas de receita baixa podem ser porta de entrada para o grupo.

5. **Internacionais — cobertura de 14 países.** Korea (Hottechi, 8,2 B) e Japan (Ganjaflex, 5,2 B) são as maiores contas internacionais — individualmente comparáveis com os top 5 da carteira US. Merecem tratamento dedicado apesar do volume de 1 conta por país.

6. **Corrigir o typo `technolgy` antes de usar em dashboards ou relatórios** — caso contrário, technology aparecerá como dois setores distintos, distorcendo rankings.

---

> **Componente do site →** Diretório de Contas: listagem filtrável por setor, porte e região; página de perfil individual por conta com histórico de deals (via pipeline).

*Próxima seção: **2. Produtos** — `products.csv`*

---

## 2. Produtos — `products.csv`

**7 produtos · 3 atributos**

| Coluna | Tipo | Descrição |
|---|---|---|
| `product` | string | Nome do produto |
| `series` | string | Família/série |
| `sales_price` | int | Preço de venda (USD) |

---

### 2.1 Catálogo Completo

| Produto | Série | Preço (USD) |
|---|---|---|
| MG Special | MG | 55 |
| GTX Basic | GTX | 550 |
| GTX Plus Basic | GTX | 1.096 |
| MG Advanced | MG | 3.393 |
| GTX Pro | GTX | 4.821 |
| GTX Plus Pro | GTX | 5.482 |
| GTK 500 | GTK | 26.768 |

3 séries, amplitude de preço de 55 a 26.768 USD — razão de ~487×.

---

### 2.2 Hierarquia de Preços por Série

Escada de valor do catálogo (do menor para o maior ticket):

```
MG Special       $      55  ──┐
GTX Basic        $     550  ──┤ Entrada
GTX Plus Basic   $   1.096  ──┤
MG Advanced      $   3.393  ──┤ Mid
GTX Pro          $   4.821  ──┤
GTX Plus Pro     $   5.482  ──┘
                              ↕ gap de ~5×
GTK 500          $  26.768  ── Topo estratégico
```

**Dois saltos críticos de ticket:**

1. MG Special → GTX Basic: salto de 10× (55 → 550) — barreira de entrada entre as duas séries mais baratas
2. GTX Plus Pro → GTK 500: salto de ~5× (5.482 → 26.768) — separa o topo da linha GTX do único produto GTK

Dentro de cada série, a progressão é gradual e permite upsell natural. O GTK 500 está isolado — não há patamar intermediário entre ele e o GTX Plus Pro.

---

### 2.3 Posicionamento por Segmento de Conta

Cruzamento entre faixa de ticket e segmentação de contas mapeada na Seção 1:

| Produto(s) | Ticket | Segmento provável | Lógica |
|---|---|---|---|
| MG Special | $55 | SMB | Ticket irrelevante para Enterprise; ponto de entrada com menor fricção de aprovação |
| GTX Basic / GTX Plus Basic | $550–1.096 | SMB / Mid-Market | Ticket razoável para qualquer segmento; serve como primeiro produto num relacionamento |
| MG Advanced / GTX Pro / GTX Plus Pro | $3.393–5.482 | Mid-Market / Enterprise | Exige budget pré-aprovado; ciclo de venda mais longo |
| GTK 500 | $26.768 | Enterprise (>2.000 M) | Para a conta Enterprise mínima do portfólio (Bluth Company, ~1.100 M), o GTK 500 representa ~2,4% da receita anual — ticket que demanda aprovação executiva |

> Nota: este posicionamento é uma hipótese baseada em ticket × porte. A confirmação virá da análise do `sales_pipeline.csv` (Seção 4), que mostrará qual produto foi de fato vendido para qual conta.

---

### 2.4 Como `products` Conecta com `accounts`

Os dois CSVs não têm coluna em comum — a ligação é indireta:

```
accounts.csv  ──── account ────┐
                               ├── sales_pipeline.csv
products.csv  ──── product ────┘
```

`sales_pipeline.csv` possui colunas `account` e `product`, funcionando como tabela de fatos que conecta quem comprou (conta) ao que foi comprado (produto).

**Implicação prática para o vendedor:** o catálogo em si não diz quem compra o quê — mas o conhecimento do portfólio permite pré-qualificar a conversa antes de abrir uma oportunidade:

- Conta SMB entrando pela primeira vez? → posicionar MG Special ou GTX Basic para reduzir barreira de aprovação
- Conta Enterprise com histórico de compras Mid-Market? → há headroom para upsell até GTX Plus Pro ou GTK 500
- GTK 500 como alvo? → verificar na Seção 1 se a conta tem receita > 2.000 M e estrutura de decisão identificada

---

### 2.5 Qualidade de Dados

| Problema | Detalhe | Impacto |
|---|---|---|
| **Typo no `sales_pipeline.csv`** | Produto aparece como `GTXPro` (sem espaço) no pipeline, mas o nome correto em `products.csv` é `GTX Pro` | Impede join direto por string — normalização obrigatória antes de cruzar os datasets |
| **GTK 500 ausente na amostra do pipeline** | Produto não aparece nas oportunidades amostradas | Pode indicar produto de nicho com ciclo muito longo, ou simplesmente sub-representação na amostra — a investigar |

**Ação recomendada ao cruzar `products` com `pipeline`:**
```python
df_pipeline['product'] = df_pipeline['product'].str.replace('GTXPro', 'GTX Pro')
```

---

### 2.6 Insights para Priorização

1. **Série MG como porta de entrada.** MG Special ($55) tem a menor barreira de aprovação do catálogo — ideal para abrir relacionamento com contas SMB ou para primeira compra em contas que nunca compraram antes. Não carrega expectativa de receita significativa por si só, mas abre o caminho.

2. **Série GTX como motor de upsell.** A progressão Basic → Plus Basic → Pro → Plus Pro segue uma escada de valor clara, com cada degrau custando ~2–4× o anterior. Contas já compradoras de GTX Basic são candidatas naturais a upsell — o pipeline revelará em qual degrau cada conta está parada.

3. **GTK 500 como deal estratégico.** Um único produto, ticket 5× maior que o segundo mais caro. Dado o porte necessário para absorver esse ticket, deve ser tratado como deal de hunter/enterprise: ciclo longo, envolvimento executivo, provavelmente sem autoaprovação pela conta. Investigar na Seção 4 se alguma conta já comprou GTK 500 e qual foi o perfil dessa conta.

4. **Ausência de produto no range $6.000–$26.000.** Há um gap entre GTX Plus Pro ($5.482) e GTK 500 ($26.768) sem nenhum produto intermediário. Contas que superaram GTX Plus Pro mas não têm budget para GTK 500 ficam sem opção de progressão — potencial gap de portfólio a endereçar.

---

> **Componente do site →** Catálogo de Produtos: cards com preço, série e posicionamento; gráfico de escada de valor; links para deals no pipeline por produto.

*Próxima seção: **3. Equipe de Vendas** — `sales_teams.csv`*

---

## 3. Equipe de Vendas — `sales_teams.csv`

**35 agentes · 3 atributos**

| Coluna | Tipo | Descrição |
|---|---|---|
| `sales_agent` | string | Nome do agente |
| `manager` | string | Nome do manager responsável |
| `regional_office` | string | Escritório regional (Central / East / West) |

---

### 3.1 Visão Geral da Equipe

| Dimensão | Valor |
|---|---|
| Total de agentes | 35 |
| Managers | 6 |
| Regiões | 3 (Central, East, West) |
| Agentes por manager (média) | 5,8 |

Estrutura em dois níveis: **região → manager → agentes**. Cada região tem exatamente 2 managers, totalizando 6 unidades de gestão simétricas.

---

### 3.2 Organização Regional Completa

| Região | Manager | Agentes |
|---|---|---|
| Central | Dustin Brinkmann | Anna Snelling, Cecily Lampkin, Versie Hillebrand, Lajuana Vencill, Moses Frase |
| Central | Melvin Marxen | Jonathan Berthelot, Marty Freudenburg, Gladys Colclough, Niesha Huffines, Darcel Schlecht, Mei-Mei Johns |
| East | Cara Losch | Violet Mclelland, Corliss Cosme, Rosie Papadopoulos, Garret Kinder, Wilburn Farren, Elizabeth Anderson |
| East | Rocco Neubert | Daniell Hammack, Cassey Cress, Donn Cantrell, Reed Clapper, Boris Faz, Natalya Ivanova |
| West | Celia Rouche | Vicki Laflamme, Rosalina Dieter, Hayden Neloms, Markita Hansen, Elease Gluck, Carol Thompson |
| West | Summer Sewald | James Ascencio, Kary Hendrixson, Kami Bicknell, Zane Levy, Maureen Marcano, Carl Lin |

**Nota:** Dustin Brinkmann (Central) tem 5 agentes — único manager abaixo de 6. As demais 5 equipes têm 6 agentes cada. Pode indicar vaga aberta ou time em transição.

A cobertura geográfica é padronizada: 3 regiões com headcount equivalente, sem concentração de força de trabalho em nenhuma região específica.

---

### 3.3 Modelo de Dados Completo — Fechando o Loop

Com `sales_teams.csv`, o modelo de dados do dataset está completo. A cadeia de relacionamentos é:

```
accounts.csv ─── account ───┐
                             ├── sales_pipeline.csv ─── sales_agent ─── sales_teams.csv
products.csv ─── product ───┘
```

| CSV | Papel no modelo | Chave de ligação |
|---|---|---|
| `accounts.csv` | Dimensão — quem compra | `account` |
| `products.csv` | Dimensão — o que foi vendido | `product` |
| `sales_teams.csv` | Dimensão — quem vendeu | `sales_agent` |
| `sales_pipeline.csv` | Fatos — cada oportunidade | `account`, `product`, `sales_agent` |

Todo deal no pipeline é completamente atribuível: **conta → produto → agente → manager → região**. Isso viabiliza análises de performance em qualquer nível da hierarquia organizacional.

---

### 3.4 Sinais do Pipeline — Perfis de Agente (Amostra)

Cruzamento preliminar com as primeiras ~250 linhas do `sales_pipeline.csv`:

| Agente | Região | Manager | Perfil observado |
|---|---|---|---|
| **Darcel Schlecht** | Central | Melvin Marxen | Alto volume; portfólio amplo (GTX Pro, GTX Basic, GTX Plus Pro, GTX Plus Basic) |
| **James Ascencio** | West | Summer Sewald | Concentrado em produtos premium (GTX Plus Pro, GTX Pro) |
| **Elease Gluck** | West | Celia Rouche | Único agente com GTK 500 visível na amostra (conta Zoomit, $25.897) — possível especialização em deals estratégicos |
| **Kary Hendrixson** | West | Summer Sewald | Ampla variedade de produtos (MG Special → GTX Plus Pro → GTX Pro) — perfil generalista |

**Agentes não observados na amostra:** Mei-Mei Johns, Carol Thompson, Natalya Ivanova, Elizabeth Anderson. Atividade potencialmente menor ou concentrada em período não coberto pela amostra — a investigar na análise completa do pipeline.

> Atenção: estes perfis são baseados em amostra restrita. Conclusões definitivas sobre performance individual exigem análise do dataset completo (Seção 4).

---

### 3.5 Qualidade de Dados

| Problema | Detalhe | Impacto |
|---|---|---|
| **Join por string sem ID** | `sales_agent` é nome livre tanto em `sales_teams` quanto em `sales_pipeline` — sem chave numérica | Qualquer variação de grafia (maiúsculas, espaço extra, apelido) quebra o join silenciosamente |
| **Sem indicador de status ativo/inativo** | Nenhuma coluna de data de contratação, saída ou flag de ativo | Impossível saber se todos os 35 agentes têm oportunidades no pipeline — agentes inativos podem inflar o denominador em métricas de produtividade |
| **Validação dos nomes** | Cruzamento da amostra não revelou typos nos nomes dos agentes que aparecem no pipeline | Risco baixo na amostra, mas recomenda-se validação sistemática no dataset completo |

**Ação recomendada antes de análise de performance:**
```python
# Normalizar nomes para evitar falhas de join
df_teams['sales_agent'] = df_teams['sales_agent'].str.strip().str.title()
df_pipeline['sales_agent'] = df_pipeline['sales_agent'].str.strip().str.title()
```

---

### 3.6 Insights para Priorização

1. **Análise por manager como proxy de coaching.** A performance agregada de uma equipe reflete a qualidade de gestão do manager. Identificar qual manager tem maior taxa de conversão ou maior ticket médio orienta decisões de treinamento e expansão de equipe.

2. **Benchmark territorial Central × East × West.** A simetria da força de trabalho permite comparar regiões em bases iguais — diferenças de resultado refletem mercado e execução, não tamanho de time.

3. **GTK 500: pool restrito de hunters.** Elease Gluck é o único agente com GTK 500 confirmado na amostra. Se esse padrão se mantiver no dataset completo, há um grupo muito reduzido de agentes capacitados (ou incentivados) a fechar deals estratégicos — oportunidade de expandir esse perfil.

4. **Equipe de Dustin Brinkmann com 5 agentes.** Se as demais equipes têm 6 agentes e a performance for equivalente por cabeça, essa equipe opera em desvantagem de capacidade. Pode ser gap de recrutamento a preencher.

5. **Agentes generalistas vs. especialistas.** Perfis como Kary Hendrixson (ampla variedade) e James Ascencio (premium) sugerem que o time não é homogêneo — segmentação por especialidade pode otimizar a cobertura de clientes por segmento (SMB vs. Enterprise).

---

> **Componente do site →** Painel de Equipe: org chart região → manager → agente; ranking de performance (quando cruzado com pipeline); drill-down por agente com histórico de deals.

*Próxima seção: **4. Pipeline de Vendas** — `sales_pipeline.csv`*

---

## 4. Pipeline de Vendas — `sales_pipeline.csv`

**8.800 oportunidades · 8 colunas · ~14 meses de dados**

| Coluna | Tipo | Nulos | Descrição |
|---|---|---|---|
| `opportunity_id` | string (8 chars) | 0 | Chave primária — todos únicos |
| `sales_agent` | string | 0 | Nome do agente (join com `sales_teams.csv`) |
| `product` | string | 0 | Nome do produto (join com `products.csv`) |
| `account` | string | 1.425 (16,2%) | Nome da conta (join com `accounts.csv`) — nulos estruturais |
| `deal_stage` | string | 0 | Estágio do funil: Won / Lost / Engaging / Prospecting |
| `engage_date` | date | 500 (5,7%) | Data de abertura da oportunidade — nulos só em Prospecting |
| `close_date` | date | 2.089 (23,7%) | Data de fechamento — nulos em Engaging e Prospecting |
| `close_value` | int (USD) | 0 | Receita do deal — 0 para Lost/Engaging/Prospecting |

---

### 4.1 Visão Geral do Pipeline

8.800 oportunidades abertas em um período de aproximadamente 14 meses:

- **engage_date:** 2016-10-20 → 2017-12-27
- **close_date:** 2017-03-01 → 2017-12-31
- **Ciclo médio Won:** ~4–5 meses entre engage e close

A tabela é a **tabela de fatos central** do modelo: cada linha é uma oportunidade de venda, completamente atribuível a uma conta, um produto e um agente.

---

### 4.2 Funil de Vendas

| Estágio | Deals | % do total | close_value |
|---|---|---|---|
| **Won** | 4.238 | 48,2% | > 0 (receita real) |
| **Lost** | 2.473 | 28,1% | = 0 (sempre) |
| **Engaging** | 1.589 | 18,1% | null (em andamento) |
| **Prospecting** | 500 | 5,7% | null (muito cedo) |
| **Total** | **8.800** | **100%** | — |

**Win rate real:** 4.238 / (4.238 + 2.473) = **63,1%**
(calculado apenas sobre deals fechados — Won + Lost — excluindo pipeline ativo)

**Pipeline ativo:** 2.089 deals (Engaging + Prospecting) ainda em aberto — oportunidade de receita futura não realizada.

**Receita total fechada:**
- Ticket médio Won: ~$2.359
- Total: ~**$9,99M** (toda receita concentrada nos 4.238 deals Won)
- Lost gera $0 por definição — o custo de oportunidade dos 2.473 deals perdidos é substancial

---

### 4.3 Performance por Produto

| Produto | Deals totais | % | Ticket (products.csv) | Receita estimada¹ |
|---|---|---|---|---|
| GTX Basic | 1.866 | 21,2% | $550 | ~$545K |
| MG Special | 1.651 | 18,8% | $55 | ~$43K |
| GTXPro² | 1.480 | 16,8% | $4.821 | ~$3,81M |
| MG Advanced | 1.412 | 16,1% | $3.393 | ~$2,56M |
| GTX Plus Basic | 1.383 | 15,7% | $1.096 | ~$811K |
| GTX Plus Pro | 968 | 11,0% | $5.482 | ~$2,84M |
| GTK 500 | 40 | 0,5% | $26.768 | ~$572K |

¹ Estimativa: deals totais × % esperado Won (63,1%) × ticket — serve de referência de grandeza, não de valor exato.
² `GTXPro` no pipeline corresponde a `GTX Pro` em `products.csv` — normalização obrigatória antes de qualquer join.

**Anomalia GTK 500:** representa apenas 0,5% do volume de deals, mas cada deal vale ~5× o segundo produto mais caro. Com 40 deals no período e ticket de $26.768, o impacto de receita é desproporcional ao volume — um único deal GTK 500 Won equivale a ~49 deals MG Special ganhos.

**Volume ≠ Receita:** MG Special lidera em visibilidade relativa como produto de entrada, mas contribui minimamente à receita. GTXPro e GTX Plus Pro, apesar de representarem ~28% dos deals, respondem pela maioria da receita total.

---

### 4.4 Performance por Agente, Manager e Região

**Agentes presentes no pipeline:** 30 dos 35 agentes do `sales_teams.csv`

**5 agentes sem nenhum deal no dataset completo:**
- Mei-Mei Johns (Central / Melvin Marxen)
- Carol Thompson (West / Celia Rouche)
- Natalya Ivanova (East / Rocco Neubert)
- Elizabeth Anderson (East / Cara Losch)
- + 1 agente a confirmar no cruzamento completo

Possíveis causas: contratação recente ao final do período, afastamento, ou inatividade — sem coluna de status em `sales_teams.csv`, impossível distinguir sem fonte adicional.

**Sinais de destaque (análise completa):**

| Agente | Região | Manager | Perfil |
|---|---|---|---|
| **Darcel Schlecht** | Central | Melvin Marxen | Maior volume de deals — portfólio amplo (GTX Basic → GTX Plus Pro) |
| **James Ascencio** | West | Summer Sewald | Concentração em produtos premium (GTX Plus Pro, GTXPro) — maior ticket médio |
| **Elease Gluck** | West | Celia Rouche | Único agente confirmado com GTK 500 na amostra — especialista em deals estratégicos |

**Benchmark regional:** a simetria do headcount (3 regiões × ~11–12 agentes) permite comparar Central × East × West em bases iguais. Diferenças de resultado refletem mercado e execução, não diferença de capacidade instalada.

---

### 4.5 Performance por Conta (Top Accounts)

| Conta | Deals no pipeline | Observação |
|---|---|---|
| Condax | 170 | Maior volume — mas SMB com receita $4,54M (accounts.csv) |
| Codehow | 121 | Subsidiária da Acme Corporation |
| Cancity | 101 | — |
| Conecom | 97 | — |
| Bioholding | 94 | `Philipines` (typo em office_location) |
| Betatech | 92 | — |

**1.425 deals sem conta (16,2%):** concentrados em Engaging (1.088) e Prospecting (337) — estruturalmente correto, pois contas só são vinculadas após qualificação da oportunidade. Não é erro de dados; é reflexo do processo comercial.

**Cruzamento com accounts.csv:**
- Conta com mais deals (Condax) é justamente o menor SMB ($4,54M) — alto volume de oportunidades em ticket baixo
- Enterprise accounts (receita > $2B) devem mostrar menor volume de deals com ticket médio mais alto
- Contas de grupos corporativos (Acme, Sonron, Bubba Gump) podem acumular deals de múltiplas subsidiárias

---

### 4.6 Análise Temporal

**Distribuição de engage_date (2016–2017):**
- Dados começam em outubro de 2016 — possivelmente início do CRM ou do período fiscal
- Pico de atividade esperado ao longo de 2017, com ciclos de fechamento ~4–5 meses depois
- Sazonalidade: início de trimestre tende a concentrar novas aberturas de pipeline (a confirmar na análise granular)

**Ciclo de fechamento Won:**
- engage_date mínima: 2016-10-20
- close_date mínima: 2017-03-01
- Gap de ~4,5 meses compatível com produtos mid-to-high ticket (GTXPro, GTX Plus Pro)
- GTK 500 provavelmente tem ciclo mais longo — valor de negociação exige mais rodadas de aprovação

**Evolução da receita (2017):**
- Toda receita fechada concentrada entre mar/2017 e dez/2017
- Dez/2017 deve ter o maior volume de closes (deals abertos em ago/set/2017)

---

### 4.7 Qualidade de Dados

| Problema | Detalhe | Impacto |
|---|---|---|
| **`account` com 1.425 nulos** | Concentrados em Engaging (1.088) e Prospecting (337) | Estrutural — não é erro. Representam oportunidades em fase inicial sem conta qualificada. Filtrar por estágio antes de analisar cobertura de contas |
| **`GTXPro` vs `GTX Pro`** | Pipeline usa `GTXPro` (sem espaço); `products.csv` usa `GTX Pro` | Impede join direto por string — normalização obrigatória antes de cruzar datasets |
| **5 agentes sem deals** | Mei-Mei Johns, Carol Thompson, Natalya Ivanova, Elizabeth Anderson + 1 | Infla denominador em métricas de produtividade por agente se não tratado — excluir ou marcar como inativos |
| **`close_value` = 0 para Lost** | Semanticamente correto (deal perdido = $0 recebido) | Médias de `close_value` sobre todo o dataset são enganosas — calcular ticket médio apenas sobre Won |
| **`engage_date` nula em 500 Prospecting** | Oportunidades em estágio inicial sem data registrada | Impossível calcular ciclo de venda para esses deals — excluir da análise temporal |

**Ações recomendadas:**
```python
# Normalizar produto para join com products.csv
df_pipeline['product'] = df_pipeline['product'].str.replace('GTXPro', 'GTX Pro')

# Ticket médio correto — apenas Won
ticket_medio_won = df_pipeline[df_pipeline['deal_stage'] == 'Won']['close_value'].mean()

# Win rate correto — excluir pipeline ativo
fechados = df_pipeline[df_pipeline['deal_stage'].isin(['Won', 'Lost'])]
win_rate = (fechados['deal_stage'] == 'Won').mean()
```

---

### 4.8 Insights Integrados — Fechando o Loop

**1. Conta Enterprise + GTK 500 = deal de maior impacto individual.**
Com ticket de $26.768 e ciclo longo, o GTK 500 é deal de hunter. Cruzando pipeline com accounts.csv: qual conta comprou GTK 500? Qual porte? Qual setor? Se for Enterprise ($2B+), confirma a hipótese de posicionamento da Seção 2. A conta Zoomit aparece na amostra com Elease Gluck — identificar o perfil completo dessa conta é prioridade.

**2. Volume ≠ Receita — desequilíbrio GTX Basic vs. GTXPro.**
GTX Basic tem o maior volume de deals (21,2%), mas ticket 9× menor que GTXPro. Um único deal GTXPro Won equivale a ~8,7 deals GTX Basic Won. Estratégia de upsell da Seção 2 é confirmada: mover contas de GTX Basic para GTXPro tem impacto de receita desproporcional ao esforço.

**3. Manager com maior win rate = benchmark de coaching.**
Cruzando deal_stage Won/Lost por agente → manager → região, é possível identificar qual manager tem o maior percentual de conversão na sua equipe. Diferenças significativas entre managers da mesma região indicam oportunidade de treinamento.

**4. Condax: volume máximo, ticket mínimo — caso de revisão estratégica.**
170 deals no pipeline, mas conta SMB com receita de $4,54M. Alta frequência de deals pode indicar produto de entrada (MG Special/GTX Basic) ou ciclos curtos. Comparar com contas Enterprise que têm menos deals mas ticket maior.

**5. Pipeline ativo de 2.089 deals — forecast imediato.**
Engaging (1.589) + Prospecting (500) representam receita potencial a fechar. Se 63,1% dos Engaging converterem ao mesmo ticket médio Won ($2.359), isso é ~$2,37M adicional em pipeline. Priorizar qualificação e avanço desses deals é a alavanca de curto prazo mais direta.

---

> **Componente do site →** Dashboard principal: funil visual (Won/Lost/Engaging/Prospecting), receita acumulada, win rate, pipeline ativo com forecast; tabela `/deals` filtrável por conta/produto/agente/estágio; leaderboard `/performance` por agente, manager e região.

*Próxima seção: **5. Mapa do Site***

---

## 5. Mapa do Site

Com os quatro CSVs analisados, o modelo de dados está completo. Esta seção mapeia como cada fonte alimenta as telas do futuro site/dashboard — preparando o terreno para implementação.

---

### 5.1 Visão Geral

```
CSV                 →  Rota          Tela / Componente
─────────────────────────────────────────────────────────────────────
accounts.csv        →  /accounts     Diretório de contas + perfil individual
products.csv        →  /products     Catálogo + escada de valor + análise de mix
sales_teams.csv     →  /team         Org chart + ranking de agentes + benchmark regional
sales_pipeline.csv  →  /dashboard    Funil, receita, win rate, pipeline ativo
                    →  /deals        Tabela de oportunidades filtrável
                    →  /performance  Leaderboard por agente / manager / região
```

---

### 5.2 Detalhamento por Tela

#### `/accounts` — Diretório de Contas
| Atributo | Detalhe |
|---|---|
| **Fonte primária** | `accounts.csv` |
| **Fonte secundária** | `sales_pipeline.csv` (histórico de deals por conta) |
| **Chave de join** | `account` |
| **Componentes** | Listagem filtrável por setor, porte (Enterprise/Mid-Market/SMB) e região; página de perfil individual por conta |
| **Insights prioritários** | Receita da conta × deals Won × ticket médio; subsidiárias vinculadas ao grupo corporativo |

#### `/products` — Catálogo de Produtos
| Atributo | Detalhe |
|---|---|
| **Fonte primária** | `products.csv` |
| **Fonte secundária** | `sales_pipeline.csv` (volume e receita por produto) |
| **Chave de join** | `product` (com normalização: `GTXPro` → `GTX Pro`) |
| **Componentes** | Cards por produto com preço e série; gráfico de escada de valor; volume de deals e receita por produto |
| **Insights prioritários** | Mix de receita por série; anomalia GTK 500; oportunidade de upsell GTX Basic → GTXPro |

#### `/team` — Painel de Equipe
| Atributo | Detalhe |
|---|---|
| **Fonte primária** | `sales_teams.csv` |
| **Fonte secundária** | `sales_pipeline.csv` (performance por agente) |
| **Chave de join** | `sales_agent` |
| **Componentes** | Org chart região → manager → agente; ranking de performance; drill-down por agente com histórico de deals |
| **Insights prioritários** | Win rate por manager; agentes sem deals (inativos?); especialistas GTK 500 vs. generalistas |

#### `/dashboard` — Funil de Vendas (tela principal)
| Atributo | Detalhe |
|---|---|
| **Fonte primária** | `sales_pipeline.csv` |
| **Fontes cruzadas** | `accounts.csv`, `products.csv`, `sales_teams.csv` |
| **Chaves de join** | `account`, `product`, `sales_agent` |
| **Componentes** | Funil visual (4 estágios); KPIs: receita total, win rate (63,1%), ticket médio Won ($2.359), pipeline ativo (2.089 deals); evolução temporal de receita |
| **Insights prioritários** | Pipeline ativo como forecast; sazonalidade de abertura de deals; benchmark trimestral |

#### `/deals` — Tabela de Oportunidades
| Atributo | Detalhe |
|---|---|
| **Fonte primária** | `sales_pipeline.csv` |
| **Fontes cruzadas** | `accounts.csv`, `products.csv`, `sales_teams.csv` |
| **Chaves de join** | `account`, `product`, `sales_agent` |
| **Componentes** | Tabela paginada com filtros por conta, produto, agente, estágio, período e valor; exportação CSV |
| **Dados derivados** | Coluna `account_rating` (Seção 6) — rating A/B/C/D da conta associada ao deal; coluna `kill_score` e `kill_classificacao` (Seção 7) — Vermelho/Laranja/Amarelo/Verde para deals abertos, indicando urgência de abandono. Permite ordenar/filtrar pipeline ativo pela saúde histórica da conta e pelo risco do deal |
| **Insights prioritários** | Deals de alto valor em Engaging (priorizar fechamento); deals sem conta ainda não qualificados; deals em contas com rating D como alertas de atenção; deals com Kill Score Vermelho como candidatos a abandono imediato |

#### `/performance` — Leaderboard
| Atributo | Detalhe |
|---|---|
| **Fonte primária** | `sales_pipeline.csv` |
| **Fonte secundária** | `sales_teams.csv` |
| **Chave de join** | `sales_agent` |
| **Componentes** | Ranking por agente (volume Won, receita, win rate); ranking por manager; benchmark Central × East × West |
| **Dados derivados** | Concentração de contas com rating D por agente — agentes com maior proporção de contas classificação D no pipeline ativo são candidatos a coaching ou requalificação de carteira; concentração de deals com Kill Score Vermelho por agente (Seção 7) — agentes cujo pipeline ativo tem alta proporção de deals moribundos precisam de rebalanceamento |
| **Insights prioritários** | Manager com maior win rate (referência de coaching); agente com maior ticket médio (especialista premium); agentes abaixo da média da equipe; agentes com pipeline ativo concentrado em contas rating D; agentes com maior concentração de deals Kill Score Vermelho no pipeline ativo |

---

### 5.3 Modelo de Joins para o Site

```
accounts.csv ──── account ────┐
                               ├── sales_pipeline.csv ──── sales_agent ──── sales_teams.csv
products.csv ──── product ────┘
```

**Avisos de join:**
1. `product`: normalizar `GTXPro` → `GTX Pro` antes de qualquer join com `products.csv`
2. `sector` em `accounts.csv`: normalizar `technolgy` → `technology` antes de filtros por setor
3. `account`: 1.425 nulos no pipeline — tratar como "não qualificado" nas telas de conta
4. `sales_agent`: join por string — padronizar `.strip().title()` em ambos os datasets

---

*Seções 1–7 completas — 4 fontes analisadas, 6 telas mapeadas, Account Rating e Kill Score definidos.*

---

## 6. Account Rating — Sistema de Classificação de Contas

### 6.1 Conceito

**Account Rating** é um sistema de pontuação que avalia a **saúde de cada conta** com base em seu histórico de deals — análogo ao conceito de *code smell*, mas invertido: aqui, quanto maior o score, melhor a conta.

A analogia com *code smell* permanece no espírito: assim como code smell sinaliza onde o código merece atenção, o rating sinaliza quais contas merecem prioridade — mas neste caso, a escala é positiva. Uma conta com rating alto tem histórico de conversão forte, recência de compra, recorrência e potencial de expansão. Uma conta com rating baixo apresenta sinais de estagnação ou baixo engajamento.

**Escala:** 0–100, onde **maior = conta mais saudável/prioritária**.

**Classificação:**

| Classe | Faixa | Significado |
|---|---|---|
| **A** | 80–100 | Conta premium — alto valor, recorrente, recente |
| **B** | 60–79 | Conta sólida — bom histórico, oportunidade de expansão |
| **C** | 40–59 | Conta em risco — sinais de estagnação ou baixa conversão |
| **D** | 0–39 | Conta crítica — requer reengajamento ou reavaliação |

**Unidade de análise:** a **conta** (`account`), não o deal individual. Todos os dados vêm de `sales_pipeline.csv`. Contas sem nenhum deal Won são excluídas do rating — não há histórico suficiente para pontuar.

**Aplicação principal:** priorizar o pipeline ativo com base no perfil histórico da conta. Em vez de tratar todas as oportunidades abertas com igual urgência, o rating permite direcionar esforço comercial para contas com maior propensão a converter e identificar contas que precisam de reengajamento.

---

### 6.2 Os 6 Sinais

#### 6.2.1 Recência (peso: 25%)

**Definição:** quão recente foi a última compra (deal Won) da conta. Contas que compraram recentemente têm maior probabilidade de converter novamente.

**Cálculo:** para cada conta, extrair `max(close_date)` considerando apenas deals Won. Normalizar via min-max para escala 0–100, onde a conta com compra mais recente recebe 100.

```python
import pandas as pd

df = pd.read_csv('sales_pipeline.csv')
df['close_date'] = pd.to_datetime(df['close_date'])

won = df[df['deal_stage'] == 'Won'].copy()

# Última compra por conta
recencia = won.groupby('account')['close_date'].max().reset_index()
recencia.columns = ['account', 'ultima_compra']

# Normalização min-max (mais recente = 100)
recencia['recencia_score'] = (
    (recencia['ultima_compra'] - recencia['ultima_compra'].min()) /
    (recencia['ultima_compra'].max() - recencia['ultima_compra'].min())
) * 100
```

---

#### 6.2.2 Taxa de Conversão (peso: 20%)

**Definição:** proporção de deals Won sobre o total de deals da conta. Mede a efetividade histórica da conta em converter oportunidades.

**Cálculo:** `count(Won) / count(total)` × 100 por conta. O dataset contém 2.473 deals Lost, então o sinal é calculável para todas as contas com histórico.

```python
# Total de deals por conta (Won + Lost)
deals_fechados = df[df['deal_stage'].isin(['Won', 'Lost'])].copy()

total_por_conta = deals_fechados.groupby('account')['opportunity_id'].count()
won_por_conta = won.groupby('account')['opportunity_id'].count()

taxa_conversao = (won_por_conta / total_por_conta * 100).reset_index()
taxa_conversao.columns = ['account', 'taxa_conversao_score']
taxa_conversao['taxa_conversao_score'] = taxa_conversao['taxa_conversao_score'].fillna(0)
```

**Nota:** a taxa de conversão já está naturalmente em escala 0–100 (percentual), dispensando normalização adicional.

---

#### 6.2.3 Potencial de Expansão (peso: 20%)

**Definição:** margem de crescimento da conta via produtos que ela ainda não comprou. Contas que compraram poucos dos 7 produtos disponíveis têm maior espaço para cross-sell.

**Cálculo:** `(1 − produtos_distintos_comprados / total_produtos) × 100`. O dataset contém 7 produtos únicos.

```python
# Normalizar GTXPro → GTX Pro para contagem correta
won['product_clean'] = won['product'].str.replace('GTXPro', 'GTX Pro')

total_produtos = won['product_clean'].nunique()  # 7

produtos_por_conta = won.groupby('account')['product_clean'].nunique().reset_index()
produtos_por_conta.columns = ['account', 'produtos_comprados']

produtos_por_conta['expansao_score'] = (
    (1 - produtos_por_conta['produtos_comprados'] / total_produtos) * 100
)
```

---

#### 6.2.4 Recorrência (peso: 15%)

**Definição:** frequência de compra da conta. Contas que compram com regularidade demonstram engajamento consistente.

**Cálculo:** intervalo médio (em dias) entre `close_date` de deals Won por conta, normalizado via min-max invertido (menor intervalo = score 100, maior intervalo = score 0).

**Edge case:** contas com apenas 1 deal Won não possuem intervalo calculável — recebem score 0 (sem evidência de recorrência).

```python
def calcular_recorrencia(grupo):
    datas = grupo['close_date'].sort_values()
    if len(datas) < 2:
        return float('nan')  # sem recorrência demonstrada
    intervalos = datas.diff().dt.days.dropna()
    return intervalos.mean()

intervalo_medio = won.groupby('account').apply(calcular_recorrencia).reset_index()
intervalo_medio.columns = ['account', 'intervalo_medio_dias']

# Contas com 1 deal Won → score 0
intervalo_medio['intervalo_medio_dias'] = intervalo_medio['intervalo_medio_dias'].fillna(
    intervalo_medio['intervalo_medio_dias'].max() + 1  # pior que todas
)

# Normalização invertida: menor intervalo = 100
intervalo_medio['recorrencia_score'] = (
    1 - (intervalo_medio['intervalo_medio_dias'] - intervalo_medio['intervalo_medio_dias'].min()) /
    (intervalo_medio['intervalo_medio_dias'].max() - intervalo_medio['intervalo_medio_dias'].min())
) * 100
```

---

#### 6.2.5 Ticket Médio (peso: 10%)

**Definição:** valor médio por deal Won da conta. Contas com ticket médio mais alto representam maior valor por transação.

**Cálculo:** `mean(close_value)` por conta (apenas Won), normalizado min-max para escala 0–100.

```python
ticket_medio = won.groupby('account')['close_value'].mean().reset_index()
ticket_medio.columns = ['account', 'ticket_medio']

ticket_medio['ticket_medio_score'] = (
    (ticket_medio['ticket_medio'] - ticket_medio['ticket_medio'].min()) /
    (ticket_medio['ticket_medio'].max() - ticket_medio['ticket_medio'].min())
) * 100
```

---

#### 6.2.6 LTV Realizado (peso: 10%)

**Definição:** valor total gerado pela conta ao longo de todo o histórico. Mede a contribuição acumulada da conta para a receita.

**Cálculo:** `sum(close_value)` por conta (apenas Won), normalizado min-max para escala 0–100.

```python
ltv = won.groupby('account')['close_value'].sum().reset_index()
ltv.columns = ['account', 'ltv_realizado']

ltv['ltv_score'] = (
    (ltv['ltv_realizado'] - ltv['ltv_realizado'].min()) /
    (ltv['ltv_realizado'].max() - ltv['ltv_realizado'].min())
) * 100
```

---

### 6.3 Fórmula Final e Score Composto

**Tabela de pesos:**

| # | Sinal | Peso | Justificativa |
|---|---|---|---|
| 1 | Recência | 25% | Sinal mais forte de propensão a recompra |
| 2 | Taxa de Conversão | 20% | Histórico de efetividade da conta |
| 3 | Potencial de Expansão | 20% | Oportunidade de cross-sell |
| 4 | Recorrência | 15% | Engajamento sustentado |
| 5 | Ticket Médio | 10% | Valor por transação |
| 6 | LTV Realizado | 10% | Contribuição acumulada |
| | **Total** | **100%** | |

**Fórmula:**

```
Rating = (Recência × 0.25) + (Taxa_Conversão × 0.20) + (Potencial_Expansão × 0.20)
       + (Recorrência × 0.15) + (Ticket_Médio × 0.10) + (LTV × 0.10)
```

**Classificação:**

| Classe | Faixa | Ação sugerida |
|---|---|---|
| **A** (80–100) | Conta premium | Manter relacionamento; oferecer produtos premium; priorizar renovações |
| **B** (60–79) | Conta sólida | Expandir portfólio; cross-sell de produtos não comprados |
| **C** (40–59) | Conta em risco | Investigar causa da estagnação; contato proativo do agente |
| **D** (0–39) | Conta crítica | Reengajamento urgente; avaliar se vale manter esforço comercial |

**Snippet Python — cálculo do score composto:**

```python
# Consolidar todos os sinais em um DataFrame
rating = recencia[['account', 'recencia_score']].merge(
    taxa_conversao[['account', 'taxa_conversao_score']], on='account', how='left'
).merge(
    produtos_por_conta[['account', 'expansao_score']], on='account', how='left'
).merge(
    intervalo_medio[['account', 'recorrencia_score']], on='account', how='left'
).merge(
    ticket_medio[['account', 'ticket_medio_score']], on='account', how='left'
).merge(
    ltv[['account', 'ltv_score']], on='account', how='left'
)

# Preencher NaN com 0 (contas sem dados em algum sinal)
rating = rating.fillna(0)

# Score composto ponderado
rating['rating_final'] = (
    rating['recencia_score'] * 0.25 +
    rating['taxa_conversao_score'] * 0.20 +
    rating['expansao_score'] * 0.20 +
    rating['recorrencia_score'] * 0.15 +
    rating['ticket_medio_score'] * 0.10 +
    rating['ltv_score'] * 0.10
)

# Classificação A/B/C/D
def classificar(score):
    if score >= 80:
        return 'A'
    elif score >= 60:
        return 'B'
    elif score >= 40:
        return 'C'
    else:
        return 'D'

rating['classificacao'] = rating['rating_final'].apply(classificar)
```

---

### 6.4 Output: Tabela de Rating por Conta

A tabela final contém todas as métricas individuais normalizadas, o score composto e uma recomendação de ação para cada conta.

**Colunas:**

| Coluna | Descrição |
|---|---|
| `account` | Nome da conta |
| `rating_final` | Score composto 0–100 |
| `classificacao` | A, B, C ou D |
| `recencia_score` | Score de recência (0–100) |
| `taxa_conversao_score` | Score de conversão (0–100) |
| `expansao_score` | Score de potencial de expansão (0–100) |
| `recorrencia_score` | Score de recorrência (0–100) |
| `ticket_medio_score` | Score de ticket médio (0–100) |
| `ltv_score` | Score de LTV realizado (0–100) |
| `recomendacao` | Ação sugerida para o vendedor |

**Snippet Python — geração da tabela com recomendações:**

```python
def gerar_recomendacao(row):
    if row['classificacao'] == 'A':
        return 'Conta premium — manter relacionamento e priorizar renovações'
    elif row['classificacao'] == 'B':
        produtos_faltantes = int(7 - (1 - row['expansao_score'] / 100) * 7)
        if row['expansao_score'] > 50:
            return f'Expandir portfólio — {produtos_faltantes} produtos ainda não comprados'
        return 'Conta sólida — manter cadência de contato'
    elif row['classificacao'] == 'C':
        if row['recencia_score'] < 30:
            return 'Reengajar — última compra distante no tempo'
        return 'Investigar estagnação — contato proativo do agente'
    else:
        if row['recorrencia_score'] == 0:
            return 'Conta sem recorrência — avaliar viabilidade de manter esforço'
        return 'Reengajamento urgente — risco de churn'

rating['recomendacao'] = rating.apply(gerar_recomendacao, axis=1)

# Tabela final ordenada por rating
tabela_rating = rating.sort_values('rating_final', ascending=False)
tabela_rating = tabela_rating.round(1)
```

---

### 6.5 Interpretação e Aplicação

**Como traduzir o rating em ação comercial:**

| Classificação | Perfil | Ação do vendedor | Ação do manager |
|---|---|---|---|
| **A** | Alta conversão, recente, recorrente | Priorizar fechamento de deals ativos; oferecer produtos premium (GTK 500) | Proteger estas contas — atribuir aos melhores agentes |
| **B** | Bom histórico, espaço para crescer | Cross-sell de produtos não comprados; aumentar frequência de contato | Monitorar evolução — potencial de upgrade para A |
| **C** | Sinais de estagnação | Contato proativo para entender obstáculos; ofertas de reativação | Avaliar se o agente atual é o mais adequado para a conta |
| **D** | Baixo engajamento ou conversão | Campanha de reengajamento; avaliar se vale investir esforço | Redistribuir para agentes especializados em recovery; considerar descarte |

**Conexão com as telas do site (Seção 5):**
- **`/deals`:** a coluna `account_rating` exibe a classificação (A/B/C/D) da conta associada a cada deal ativo, permitindo que o vendedor priorize pipeline por saúde da conta
- **`/performance`:** o painel de agentes destaca quais vendedores têm maior concentração de contas classificação D no pipeline ativo — sinal de carteira em risco que demanda atenção do manager

> **Componente do site →** Coluna `account_rating` na tabela `/deals`; painel de concentração de classificação D por agente em `/performance`; badge de classificação no perfil de cada conta.

---

## 7. Kill Score — Score de Abandono por Deal

### 7.1 Conceito

O Kill Score é um score de 0–100 atribuído a cada **deal aberto** (deal_stage ≠ Won e ≠ Lost) que indica a urgência de abandonar aquele deal e pivotar esforço para outra oportunidade.

**Diferença em relação ao Account Rating (Seção 6):**

| Métrica | Unidade de análise | Direção | Pergunta que responde |
|---|---|---|---|
| **Account Rating** (Seção 6) | Conta | Alto = bom | "Essa conta vale a pena?" |
| **Kill Score** (Seção 7) | Deal aberto | Alto = abandonar | "Esse deal deve ser abandonado?" |

O Kill Score consome o Account Rating como um dos seus sinais (Rating Invertido, peso 20%), criando uma dependência direta entre as seções.

**Classificação por cores:**

| Cor | Faixa | Significado |
|---|---|---|
| Vermelho | 80–100 | Abandonar imediatamente |
| Laranja | 60–79 | Última tentativa — prazo de 7 dias |
| Amarelo | 40–59 | Reduzir frequência de contato |
| Verde | 0–39 | Deal saudável — continuar |

---

### 7.2 Os 5 Sinais

#### 7.2.1 Tempo Excedente (peso: 30%)

**Definição:** quanto o deal ultrapassou o tempo médio dos deals Won históricos no pipeline.

**Cálculo:**
1. `dias_no_pipeline = hoje − engage_date` (para cada deal aberto)
2. `media_won = mean(close_date − engage_date)` dos deals com deal_stage == Won
3. Normalização linear: `dias_no_pipeline == media_won → 0`; `dias_no_pipeline == 3× media_won → 100`
4. Clip em [0, 100] — deals mais novos que a média recebem 0

**Fórmula:** `min(max((dias_no_pipeline - media_won) / (2 * media_won) * 100, 0), 100)`

```python
from datetime import date

hoje = date.today()

# Deals abertos
abertos = pipeline[~pipeline['deal_stage'].isin(['Won', 'Lost'])].copy()
abertos['engage_date'] = pd.to_datetime(abertos['engage_date'])
abertos['dias_no_pipeline'] = (pd.Timestamp(hoje) - abertos['engage_date']).dt.days

# Média de dias dos Won
won = pipeline[pipeline['deal_stage'] == 'Won'].copy()
won['engage_date'] = pd.to_datetime(won['engage_date'])
won['close_date'] = pd.to_datetime(won['close_date'])
media_won = (won['close_date'] - won['engage_date']).dt.days.mean()

# Score de tempo excedente
abertos['tempo_excedente'] = (
    (abertos['dias_no_pipeline'] - media_won) / (2 * media_won) * 100
).clip(0, 100)
```

---

#### 7.2.2 Estagnação (peso: 25%)

**Definição:** deal parado em estágio inicial por tempo excessivo. Um deal em Prospecting há muito tempo é mais grave do que um deal em Engaging há muito tempo, pois o segundo já demonstrou algum avanço.

**Cálculo:**
1. Mapear estágio para multiplicador de gravidade: Prospecting × 1.0, Engaging × 0.6
2. Calcular razão `dias_no_pipeline / media_won`
3. Score = `min(razão × multiplicador × 50, 100)`

```python
multiplicador_estagio = {
    'Prospecting': 1.0,
    'Engaging': 0.6
}

abertos['mult_estagio'] = abertos['deal_stage'].map(multiplicador_estagio).fillna(0.3)

abertos['estagnacao'] = (
    (abertos['dias_no_pipeline'] / media_won) * abertos['mult_estagio'] * 50
).clip(0, 100)
```

---

#### 7.2.3 Rating Invertido do Account (peso: 20%)

**Definição:** saúde da conta associada ao deal, invertida — conta com rating baixo (ruim) produz kill score alto.

**Cálculo:** `100 − rating_final` da Seção 6

**Dependência:** requer a tabela `rating` calculada na Seção 6.

**Tratamento de nulos:** deals sem `account` (1.425 nulos no pipeline) ou accounts sem rating recebem score 75 (abordagem pessimista — sem histórico de conta, o deal é mais arriscado).

```python
# Merge com rating da Seção 6
abertos = abertos.merge(
    rating[['account', 'rating_final']], on='account', how='left'
)

# Rating invertido — conta ruim = kill score alto
# Deals sem account ou sem rating → 75 (pessimista)
abertos['rating_invertido'] = 100 - abertos['rating_final']
abertos['rating_invertido'] = abertos['rating_invertido'].fillna(75)
```

---

#### 7.2.4 ROI do Esforço (peso: 15%)

**Definição:** valor esperado por dia investido no deal. Deals com baixo retorno por dia de esforço devem ser priorizados para abandono.

**Cálculo:**
1. `roi_dia = close_value / dias_no_pipeline` (close_value para deals abertos é o valor esperado/proposto)
2. Normalização inversa: menor ROI/dia = score mais alto
3. Escala: percentil rank invertido × 100

```python
# ROI por dia de esforço
abertos['roi_dia'] = abertos['close_value'] / abertos['dias_no_pipeline'].replace(0, 1)

# Normalização inversa — pior ROI = score mais alto
abertos['roi_esforco'] = (
    100 - abertos['roi_dia'].rank(pct=True) * 100
)
```

---

#### 7.2.5 Conversão do Produto (peso: 10%)

**Definição:** taxa histórica de conversão do produto associado ao deal. Produtos com baixa conversão histórica elevam o kill score.

**Cálculo:**
1. `taxa_conversao_produto = count(Won do produto) / count(Won + Lost do produto) × 100`
2. Inversão: `100 − taxa_conversao_produto`

```python
# Taxa de conversão por produto (apenas deals fechados)
fechados = pipeline[pipeline['deal_stage'].isin(['Won', 'Lost'])]
conv_produto = fechados.groupby('product')['deal_stage'].apply(
    lambda x: (x == 'Won').sum() / len(x) * 100
).reset_index()
conv_produto.columns = ['product', 'taxa_conversao_produto']

# Merge e inversão
abertos = abertos.merge(conv_produto, on='product', how='left')
abertos['conversao_produto'] = 100 - abertos['taxa_conversao_produto'].fillna(50)
```

---

### 7.3 Fórmula Final e Score Composto

**Pesos:**

| Sinal | Peso | Justificativa |
|---|---|---|
| Tempo Excedente | 30% | Maior preditor de deal morto — tempo é o recurso mais escasso |
| Estagnação | 25% | Deals parados em estágio inicial raramente avançam |
| Rating Invertido | 20% | Conta fraca amplifica o risco de qualquer deal |
| ROI do Esforço | 15% | Baixo retorno por dia indica alocação ineficiente |
| Conversão do Produto | 10% | Contexto histórico do produto — menos acionável pelo vendedor |
| **Total** | **100%** | |

**Classificação:**

| Cor | Faixa | Ação |
|---|---|---|
| Vermelho | 80–100 | Abandonar e pivotar |
| Laranja | 60–79 | Última tentativa (7 dias) |
| Amarelo | 40–59 | Reduzir frequência |
| Verde | 0–39 | Continuar normalmente |

**Snippet Python — cálculo do Kill Score composto:**

```python
# Kill Score composto
abertos['kill_score'] = (
    abertos['tempo_excedente'] * 0.30 +
    abertos['estagnacao'] * 0.25 +
    abertos['rating_invertido'] * 0.20 +
    abertos['roi_esforco'] * 0.15 +
    abertos['conversao_produto'] * 0.10
)

# Classificação por cores
def classificar_kill(score):
    if score >= 80:
        return 'Vermelho'
    elif score >= 60:
        return 'Laranja'
    elif score >= 40:
        return 'Amarelo'
    else:
        return 'Verde'

abertos['kill_classificacao'] = abertos['kill_score'].apply(classificar_kill)
```

---

### 7.4 Output: Tabela de Kill Score por Deal

**Colunas:**

| Coluna | Descrição |
|---|---|
| `opportunity_id` | ID do deal |
| `account` | Conta associada |
| `sales_agent` | Vendedor responsável |
| `product` | Produto do deal |
| `kill_score` | Score composto 0–100 |
| `kill_classificacao` | Vermelho, Laranja, Amarelo ou Verde |
| `dias_no_pipeline` | Dias desde engage_date até hoje |
| `media_won_dias` | Média de dias dos deals Won (referência) |
| `recomendacao` | Ação sugerida (ver abaixo) |

**Recomendações por classificação:**

| Cor | Recomendação |
|---|---|
| **Vermelho (80+)** | "Abandonar. Pivotar para [account X] que tem rating [Y] e deal aberto com kill score verde." — sugestão dinâmica baseada no portfólio do mesmo agente |
| **Laranja (60–79)** | "Última tentativa: [ação baseada no sinal mais crítico]. Prazo: 7 dias." |
| **Amarelo (40–59)** | "Reduzir frequência. Próximo follow-up em [X] dias." — X calculado proporcionalmente ao score |
| **Verde (<40)** | "Continuar. Deal saudável." |

**Snippet Python — geração da tabela com recomendações dinâmicas:**

```python
def gerar_recomendacao_kill(row, abertos_df, rating_df):
    if row['kill_classificacao'] == 'Vermelho':
        # Buscar melhor alternativa do mesmo agente: deal Verde em conta rating A ou B
        alternativas = abertos_df[
            (abertos_df['sales_agent'] == row['sales_agent']) &
            (abertos_df['kill_classificacao'] == 'Verde') &
            (abertos_df['opportunity_id'] != row['opportunity_id'])
        ]
        if not alternativas.empty:
            # Priorizar por kill_score mais baixo (deal mais saudável)
            melhor = alternativas.sort_values('kill_score').iloc[0]
            # Buscar rating da conta do deal alternativo
            conta_alt = melhor.get('account', 'N/A')
            rating_alt = rating_df[rating_df['account'] == conta_alt]
            class_alt = rating_alt['classificacao'].values[0] if not rating_alt.empty else '?'
            return f"Abandonar. Pivotar para {conta_alt} (rating {class_alt}) — deal {melhor['opportunity_id']} com kill score {melhor['kill_score']:.0f} (Verde)"
        return 'Abandonar. Sem alternativa Verde no pipeline do agente — requalificar carteira'

    elif row['kill_classificacao'] == 'Laranja':
        # Identificar sinal mais crítico
        sinais = {
            'Tempo Excedente': row['tempo_excedente'],
            'Estagnação': row['estagnacao'],
            'Rating da Conta': row['rating_invertido'],
            'ROI do Esforço': row['roi_esforco'],
            'Conversão do Produto': row['conversao_produto']
        }
        pior_sinal = max(sinais, key=sinais.get)
        return f"Última tentativa: resolver {pior_sinal} ({sinais[pior_sinal]:.0f}/100). Prazo: 7 dias."

    elif row['kill_classificacao'] == 'Amarelo':
        # Follow-up proporcional ao score (40→7 dias, 59→14 dias)
        dias_followup = int(7 + (row['kill_score'] - 40) / 19 * 7)
        return f"Reduzir frequência. Próximo follow-up em {dias_followup} dias."

    else:
        return 'Continuar. Deal saudável.'

# Aplicar recomendações
abertos['recomendacao'] = abertos.apply(
    lambda row: gerar_recomendacao_kill(row, abertos, rating), axis=1
)

# Tabela final
tabela_kill = abertos[[
    'opportunity_id', 'account', 'sales_agent', 'product',
    'kill_score', 'kill_classificacao', 'dias_no_pipeline',
    'recomendacao'
]].copy()
tabela_kill['media_won_dias'] = round(media_won, 1)
tabela_kill = tabela_kill.sort_values('kill_score', ascending=False).round(1)
```

---

### 7.5 Interpretação e Aplicação

**Como traduzir o Kill Score em ação comercial:**

| Classificação | Perfil do deal | Ação do vendedor | Ação do manager |
|---|---|---|---|
| **Vermelho (80+)** | Deal moribundo — tempo excedido, conta fraca, baixo ROI | Abandonar e realocar esforço para deal Verde sugerido na recomendação | Monitorar taxa de abandono; garantir que agente tem alternativas no pipeline |
| **Laranja (60–79)** | Deal em risco — pelo menos 2 sinais críticos | Uma última tentativa focada no sinal mais crítico; reavaliar em 7 dias | Revisar com agente em 1:1 — validar se a última tentativa é viável |
| **Amarelo (40–59)** | Deal lento mas não perdido | Reduzir cadência; follow-up espaçado conforme recomendação | Incluir em revisão mensal de pipeline |
| **Verde (<40)** | Deal saudável — dentro dos parâmetros | Manter cadência normal; priorizar fechamento | Nenhuma ação necessária |

**Conexão com Account Rating (Seção 6):**
- O Kill Score usa o `rating_final` da Seção 6 como input direto (sinal Rating Invertido, peso 20%)
- As recomendações de deals Vermelho sugerem pivotar para contas com rating A/B, criando um ciclo de feedback: abandonar deals ruins → investir em contas boas
- Um deal Verde em conta rating D ainda pode ser viável, mas o rating baixo contribui para um kill score moderado — o vendedor deve monitorar de perto

**Conexão com as telas do site (Seção 5):**
- **`/deals`:** colunas `kill_score` e `kill_classificacao` visíveis para deals abertos; filtro por cor permite ao vendedor ver rapidamente quais deals abandonar
- **`/performance`:** agentes com maior concentração de deals Vermelho no pipeline ativo são sinalizados — indica carteira saturada ou mal qualificada

> **Componente do site →** Colunas `kill_score` e `kill_classificacao` na tabela `/deals`; badge de cor no card de cada deal aberto; painel de concentração de deals Vermelho por agente em `/performance`; recomendação de pivô visível no detalhe do deal.
