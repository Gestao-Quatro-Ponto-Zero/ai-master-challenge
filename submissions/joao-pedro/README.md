# **README**

> **AI Master Challenge · G4 Educação**  
> Área: Vendas / RevOps · Tipo: Build 

## O README está dividido em duas partes:

- 1. **Submission-template**
- 1. **README "tradicional" da aplicação**

---

# Submission-template:

### Sobre mim

#### Nome: João Pedro Testa

#### Linkedin: [https://www.linkedin.com/in/joaoptesta/](https://www.linkedin.com/in/joaoptesta/)

#### Challenge escolhido: 003 - score

---

# Executive Summary:

Analisei 8.800 oportunidades e descobri que o problema não era vendedores 
"não sabendo priorizar" — era vendedores sobrecarregados protegendo deals 
ruins. 

57% não prospectam, criando um círculo vicioso: 
carga alta → sem novos deals → protegem os ruins → pipeline trava (165 dias mediana vs 
57 dias Won). 

Construí um sistema funcional que separa importância (Score) de capacidade (Viabilidade), gerando ações contextuais por vendedor. 

O principal output de tudo isso é a recomendação de redistribuir 413 deals (26% do pipeline) de vendedores  sobrecarregados para vendedores com capacidade — isso quebraria o círculo 
vicioso e liberaria atenção para os 32 deals realmente críticos.

---

# Solução + Abordagem

**Ponto de partida: Decompor a pergunta**

A Head de RevOps pediu "uma ferramenta que mostre onde focar". Poderia ter 
feito um modelo preditivo tradicional (probabilidade × valor, ordenar, done). 

Rejeitei essa abordagem porque ela responde "qual deal vale mais", não 
"o que fazer segunda-feira de manhã".

Decomposição do problema:

1. **Exploração:** Por que pipeline está travado? (análise de tempo de ciclo)
2. **Diagnóstico:** O que causa isso? (análise de prospecting e carga)
3. **Validação:** Tempo corrói probabilidade? (correlação quantitativa)
4. **Solução:** Como priorizar considerando contexto? (Score × Viabilidade)

**Prioridades:**

- ✅ Explicabilidade > Precisão (vendedor precisa confiar)
- ✅ Contexto de capacidade (não adianta score alto se vendedor não pode agir)
- ✅ Ações claras (não só número, mas "o que fazer")
- ✅ Zero fricção inicial (usar dados existentes, não pedir input novo)

**Stack técnico:**

- Python (análise + backend)
- Streamlit (interface funcional)
- Heurísticas + regras (não ML black box)

---

### Resultados / Findings

**🔍 Finding #1: Pipeline Travado por Falta de Ação**

```
Tempo de ciclo (medianas):
- Won: 57 dias
- Lost: 14 dias
- Engaging: 165 dias (2.9× Won)
```

**Insight:** Se Won fecha em 57d e Lost desiste em 14d, por que Engaging 
demora 165d? Não é dificuldade — é falta de ação.

---

**🔍 Finding #2: Círculo Vicioso de Sobrecarga**

```
Vendedores sem prospecting: 17/30 (57%)

Padrão identificado:
- Sem prospecting → Carga média: 108 deals
- Com prospecting (>20) → Carga média: 52 deals

Diferença: 2× de carga
```

**Insight:** Vendedores não prospectam porque estão sobrecarregados. 
Protegem deals ruins para "manter pipeline". Isso trava ainda mais o pipeline.

---

**🔍 Finding #3: Tempo Corrói Probabilidade**

```
Win Rate por tempo em pipeline:
- <28d: 68%
- 28-57d: 64%
- 57-85d: 61%
- 85-165d: 55%
- >200d: 38% (perda de 25 pontos vs global 63%)
```

**Insight:** Deals >200 dias têm probabilidade 40% menor. Ocupam atenção 
mas não geram retorno.

---

**🔍 Finding #4: Desbalanceamento de Capacidade**

```
Top 3 sobrecarregados:
- Corliss Cosme: 177 deals, 0 prospecting
- Anna Snelling: 112 deals, 0 prospecting
- Dustin Brinkmann: 130 deals, 0 prospecting

Top 3 com capacidade:
- Wilburn Tomas: 31 deals, 25 prospecting
- Marty Freudenburg: 87 deals, 54 prospecting
- Versie Hillebrand: 45 deals, 33 prospecting
```

**Insight:** Alguns vendedores têm 5× a carga de outros. Oportunidade 
de redistribuição.

---

**💡 Solução Construída: Sistema de Priorização Contextual**

**Arquitetura:**

```
SCORE (0-100) = 50% Urgência + 30% Probabilidade + 20% Valor
└─ Importância OBJETIVA do deal (mesmo para todos os vendedores)

VIABILIDADE (0-100) = f(prospecting, carga, especialização)
└─ Capacidade CONTEXTUAL do vendedor (personalizada)

AÇÃO = Matriz(Score, Viabilidade)
└─ PUSH_HARD, TRANSFER, DISCARD, MONITOR, etc.
```

**Componentes do Score:**

- **Urgência (50%):** Baseada em thresholds de tempo
  - ≥200d → 100 pts (frozen)
  - ≥165d → 80 pts (mediana Engaging)
  - ≥57d → 40 pts (mediana Won)
  - Multiplicadores: carga do vendedor, dificuldade da conta, deal oversized
- **Probabilidade (30%):** Prior bayesiano × fatores
  - Base: 63.15% (global win rate)
  - Fatores: vendedor × produto × conta × região × especialização
  - Penalidades: tempo excessivo, oversize, overload
- **Valor (20%):** Percentil + ajustes estratégicos
  - Percentil na distribuição (não absoluto)
  - Bonus: produto premium (GTK 500), conta top 20
  - Desconto: probabilidade baixa (valor esperado)

**Viabilidade (separada):**

```
Viabilidade = 50 × prospecting_factor × load_factor × specialist_factor

- prospecting_factor: 0.5 (sem) → 1.3 (ativo)
- load_factor: 0.6 (>150 deals) → 1.3 (<40 deals)
- specialist_factor: 0.8 (mismatch) → 1.2 (expert)
```

**Interface funcional:**

Sistema Streamlit com 9 páginas:

- 📊 Macro: Visão geral
- 🧠 Heurística: Como chegamos à tese
- 📋 Deal List: Todos os deals priorizados
- 🔍 Deal Details: Drill-down com breakdown completo
- 👥 Seller Analysis: Capacidade e carga por vendedor
- 🔀 Transfer Analysis: 413 transferências recomendadas
- 🎯 Action Analysis: Distribuição de ações
- 📦 Product Analysis: Performance por produto
- 🌍 Regional Analysis: Por região

---

### Recomendações

**🎯 Prioridade 1: Testar Redistribuição (Quick Win)**

**O quê:** Transferir 50-100 deals de vendedores sobrecarregados para 
vendedores com capacidade.

**Como:**

1. Começar com 19 transfers CRÍTICOS (score ≥70, viab <40)
2. Usar hierarquia: same team → same region → other region
3. Medir impacto em 30 dias

**Critério de sucesso:**

- Vendedores sobrecarregados voltam a prospectar (>10 novos/mês)
- Win rate em deals transferidos ≥ média global (63%)
- Tempo de ciclo cai 20%

**ROI esperado:**

- Libera ~40h/semana de atenção
- 19 deals críticos ganham vendedor com capacidade
- Quebra círculo vicioso

---

**🎯 Prioridade 2: Campanha de Descarte (Liberar Atenção)**

**O quê:** Descartar 443 deals (28% do pipeline) com score <60 e viab <40.

**Como:**

1. Vendedor revisa lista de DISCARD gerada pelo sistema
2. Confirma descarte com 1 clique (ou contesta)
3. Sistema move para Lost com tag "descarte_estratégico"

**Critério de sucesso:**

- Liberar ~150h/semana de atenção no time
- Carga média cai de 87 para 65 deals (-25%)
- Vendedores reportam "mais foco nos deals que importam"

**ROI esperado:**

- Deals descartados tinham prob média 38% (vs 63% global)
- Tempo investido neles tinha ROI negativo
- Atenção liberada vai para 32 deals HIGH (prob 75%+)

---

**🎯 Prioridade 3: Implementar Sistema (30-60 dias)**

**O quê:** Colocar sistema em produção com vendedores reais.

**Como:**

1. **Fase 1 (piloto - 2 semanas):** 5 vendedores testam
2. **Fase 2 (feedback - 2 semanas):** Ajustar com input real
3. **Fase 3 (rollout - 4 semanas):** Todo o time

**Melhorias necessárias:**

- Integração com CRM (API Salesforce/HubSpot)
- Alertas proativos (deal sem ação há 30d)
- Mobile-friendly (vendedor acessa no celular)
- Feedback loop (ação foi útil? 👍/👎)

**Critério de sucesso:**

- Adoção ≥80% do time em 60 dias
- Sistema consultado ≥3× por semana por vendedor
- Qualidade de dados melhora (deals atualizados)

---

**🎯 Prioridade 4: Melhorias Iterativas (60-90 dias)**

**O quê:** Aprender com uso real e refinar modelo.

**Como:**

1. Capturar feedback de vendedores
2. Ajustar thresholds (50/30/20 pode virar 55/25/20)
3. Adicionar ML para refinar probabilidade (mantendo explicabilidade)
4. Personalizar por vendedor (aprender padrões individuais)

**Não fazer agora:**

- ❌ Modelo preditivo complexo (ainda não temos dados de engajamento)
- ❌ Automação de ações (vendedor precisa manter controle)
- ❌ Integração com calendário/email (complexidade > valor no curto prazo)

---

### Limitações

**📉 Dados Faltantes**

- ❌ **Engajamento:** Não temos emails enviados, calls feitos, propostas apresentadas
  - **Impacto:** Probabilidade é aproximada (baseada em histórico, não em ação recente)
  - **Workaround:** Usar tempo sem update como proxy (deal sem ação há 90d)
- ❌ **Motivação do vendedor:** Não sabemos se vendedor QUER o deal
  - **Impacto:** Pode recomendar PUSH em deal que vendedor já desistiu mentalmente
  - **Workaround:** Vendedor pode marcar deal como "não prioritário" (override manual)
- ❌ **Contexto de mercado:** Não temos dados de sazonalidade, ciclos econômicos
  - **Impacto:** Probabilidade não considera contexto externo
  - **Workaround:** Adicionar fator manual "mercado aquecido/frio" (futuro)

---

**⚙️ Escolhas Técnicas**

- ❌ **Regras fixas vs ML adaptativo:** Thresholds (200d, 165d, 57d) são fixos
  - **Impacto:** Pode não generalizar para outros times/indústrias
  - **Workaround:** Permitir configuração de thresholds por empresa
- ❌ **Viabilidade simplificada:** Só 3 fatores (prospecting, carga, especialização)
  - **Impacto:** Ignora contexto tipo "vendedor em férias", "novo no time"
  - **Workaround:** Adicionar campo "status" (ativo, férias, onboarding)

---

**🔄 Premissas Não Validadas**

- ⚠️ **Vendedores usarão o sistema:** Assumo que interface funcional = adoção
  - **Risco:** Se não virem valor imediato, abandonam
  - **Mitigação:** Value-first design (gera insight sem pedir esforço)
- ⚠️ **Dados estão atualizados:** Modelo depende de `deal_stage` correto
  - **Risco:** Garbage in, garbage out
  - **Mitigação:** Alertas de qualidade ("deal sem update há 90d")
- ⚠️ **Transferências são viáveis:** Assumo que vendedores aceitam receber deals
  - **Risco:** Cultura de "cada um cuida do seu"
  - **Mitigação:** Manager media transferências (não automático)

---

**🕐 Restrições de Tempo**

- ❌ **Não validei com vendedores reais:** Sistema é simulação
  - **Impacto:** Pode ter blindspots que só aparecem no uso real
  - **Próximo passo:** Piloto com 5 vendedores por 2 semanas
- ❌ **Não implementei feedback loop:** Sistema não aprende (ainda)
  - **Impacto:** Não melhora com uso
  - **Próximo passo:** Adicionar "ação foi útil?" (👍/👎)
- ❌ **Não testei performance em escala:** 1.589 deals funciona, mas e 50.000?
  - **Impacto:** Pode ser lento em empresas maiores
  - **Próximo passo:** Otimizar queries, adicionar cache

---

# Process Log - Como usei IA

### Ferramentas usadas:

| Ferramenta | Para que usou |
|------------|--------------|
| _Claude Code_ | _Conversa inicial sobre o desafio + entendimento básico sobre os dados fornecidos_ |
| _Cursor_ | _Construção do protótipo web_ |
| _Claude code + Cursor_ | _Agente do claude dentro do cursor para auxílio no protótipo web_ |

### Workflow:
1. A primeira coisa que fiz foi recolher e juntar todo o material de contexto disponível do desafio.
2. Juntei a descrição da vaga + descrição do desafio + sumário resumido do escopo dos dados fornecidos.
3. Desde o princípio eu já tinha a ideia de trabalhar no desafio 03, mas mesmo assim enviei todas as descrições ao Claude para que - com base em um arquivo eu.md do meu ambiente -, ele pudesse me confirmar a escolha.
4. Feita a escolha do desafio e, com todo contexto dele "em mãos", abri o kaggle e começei a tirar as minhas primeiras conclusões. 
5. Confesso que apenas visualizando os dados-base fornecidos, não estava conseguindo ir muito além de um modelo preditivo tradicional.
6. Foi quando finalmente comecei a utilizar o Claude para a análise de fato dos dados da data-base.
8. Contextualizei o Claude sobre algumas análises que eu havia feito e o instiguei a "pensarmos fora da caixa".
9. Foi ai que chegamos ao conceito de "features óbvias" vs "features imperdíveis".
10. O claude me gerou +20 features chamadas de "imperdíveis", mas a maioria esmagadora era pautada em modelos de ML complexos e detalhados.
11. Deixei claro a ele que o desafio não priorizava complexidade, e que a partir daquele momento nossa energia deveria estar concentrada em responder: "O que o vendedor precisa ver na tela segunda-feira de manhã?"
12. Com esse conceito batido, abri o cursor e criei um projeto com os 4 arquivos csv da data-base. 
13. Utilizando o ploty criei uma view-base dos dados dos csvs fornecidos - nada demais, apenas tornar visual as métricas primárias. 
14. Devo confessar novamente que apenas com as visualização das métricas primárias, não consegui enxergar nada demais além do óbvio. 
15. Foi aí que pedi ao agente do claude, dentro do cursor, que criasse as views detalhadas das features "imperdíveis" - as páginas de "Analysis" do streamlit.
14. Com as métricas detalhadas em mãos, comecei a descartar algumas das 20 features imperdíveis.
15. Em uma primeira limpeza, as 20 métricas foram reduzidas para 10.  
16. Até que em dado momento chegamos ao questionamento principal da tese: Por que vendedores com 0 prospects tem sobrecarga em engage? 
17. Ao investigar a fundo o ponto, descobrimos correlações com outras métricas e definimos que seria essa a tese.
18. Com isso em mente, tratei de criar as documentações base da aplicação, que serviria posteriormente para um readme da vida mas principalmente que seriviria como ouro para a janela de contexto do agente Claude que eu conversava - criei vários arquivos .md dos conceitos discutidos e sempre que precisava recupera-los no contexto solicitava ao Claude. 
19. Estimo que 70% do tempo investido no desafio foi na estruturação da página que pode ser visualizada no streamlit, eis o porque:
20. Pode-se inferir que a página do streamlit é o data-center de toda a aplicação.
21. Se observado com detalhe, todas as pontas que se derivam do projeto vem do que foi construído no streamlit: Documentações, teses, readme, gráficos, métricas, etc.
22. Com essa "base" pronta, o que fiz após foi somente destinar os resultados lá armazenados aos destinos corretos: Alguns pontos foram para documentações, outros foram para o frontend em react, outros para arquivos do desafio como esse. 
23. Bom, eu nunca havia descrito um process log de utilização de IA em algum projeto, e não achei que seria tão difícil.
24. Mas se eu pudesse sintetizar todo o processo de utilização de IA nesse projeto, diria que foquei em utilizar a IA para fazer um arroz com feijão bem feito: Boas documentações e explicabilidade antes de modelos complexos ou lógicas revolucionárias. 

# Onde a IA errou e como corrigi

### Devo adimitir que não lembro de erros muito expressivos das IAs que utilzei na elaboração e construção da tese.
### Um dos pontos nesse sentido claros e frescos para mim era que constantemente eu tinha que relembrar o contexto simples da tese, no sentido de rejeitar modelos complexos de ML ou coisas do tipo. 

# Evidências:

Em anexo abaixo todo o conteúdo recuperado referente ao desenvolvimento da tese com IA:
>Me coloco a disposição para enviar maiores contextos de comprovação caso necessário 

1. Chathistory da primeira conversa que tive com o Claude sobre o contexto inicialL: 
https://claude.ai/share/07714d82-b304-43f4-b9b5-3c365b9d38c1

2. Screenshots de algumas sessões (Claude + Cursor):



# README "Tradicional"

> **Nota sobre este README**
> Este documento cobre a entrega, a arquitetura e o funcionamento geral da solução.
> Os fundamentos que embasaram as decisões de design — análise exploratória, raciocínio do modelo e limitações — não são detalhados aqui.
>
> Para o entendimento completo do que foi construído e por quê, é fortemente recomendada a leitura dos quatro tópicos disponíveis em **Fundamentos** no Streamlit:
>
>
> | Tópico          | O que cobre                                                   |
> | --------------- | ------------------------------------------------------------- |
> | **Macro**       | Problema, diagnóstico, decisões de design e KPIs esperados    |
> | **Heurística**  | Análise exploratória — como os dados revelaram a tese central |
> | **Score-model** | Lógica técnica detalhada do scoring e das transferências      |
> | **Limitações**  | O que o modelo não faz, trade-offs e caminhos de evolução     |
>

## Documentação


| Arquivo                                          | Conteúdo                                                                 |
| ------------------------------------------------ | ------------------------------------------------------------------------ |
| `[docs/macro.md](docs/macro.md)`                 | Big picture — problema, diagnóstico, decisões de design e KPIs esperados |
| `[docs/heuristica.md](docs/heuristica.md)`       | Análise exploratória completa — como os dados revelaram a tese central   |
| `[docs/logica.md](docs/logica.md)`               | Detalhamento técnico do scoring, viabilidade e lógica de transferência   |
| `[docs/limitacoes.md](docs/limitacoes.md)`       | O que o modelo não faz, trade-offs e caminhos de evolução                |
| `[docs/stack.md](docs/stack.md)`                 | Arquitetura, estrutura de pastas e decisões de design                    |
| `[docs/inicializacao.md](docs/inicializacao.md)` | Pré-requisitos e instruções completas de inicialização dos três serviços |
| `[docs/README.api.md](docs/README.api.md)`       | Documentação de todos os endpoints REST                                  |


---

## O Desafio

### Contexto

> "Nossos vendedores gastam tempo demais em deals que não vão fechar e deixam oportunidades boas esfriar. 
> Preciso de algo funcional — não um modelo no Jupyter Notebook que ninguém vai usar. Quero uma ferramenta que o vendedor abra, veja o pipeline, e saiba onde focar. Pode ser simples, mas precisa funcionar."


|                 |                                              |
| --------------- | -------------------------------------------- |
| 👥 **Time**     | 30 vendedores, 3 regiões, múltiplos managers |
| 📦 **Pipeline** | ~8.800 oportunidades                         |
| ⚠️ **Problema** | Priorização feita "no feeling"               |


### O ponto-chave:

> **"O que o vendedor deve trabalhar segunda-feira de manhã?"**

### Dados Disponíveis

Quatro tabelas de um CRM, todas interconectadas.

> Dataset: CRM Sales Predictive Analytics (licença CC0)


| Arquivo              | O que contém                                                                                           | Registros | Campo-chave                  |
| -------------------- | ------------------------------------------------------------------------------------------------------ | --------- | ---------------------------- |
| `accounts.csv`       | Contas clientes — setor, receita, número de funcionários, localização, empresa-mãe                     | ~85       | `account`                    |
| `products.csv`       | Catálogo de produtos com série e preço                                                                 | 7         | `product`                    |
| `sales_teams.csv`    | Vendedores com seu manager e escritório regional                                                       | 35        | `sales_agent`                |
| `sales_pipeline.csv` | Pipeline completo — cada oportunidade com stage, datas, vendedor, produto, conta e valor de fechamento | ~8.800    | `opportunity_id` → liga tudo |


**Estrutura dos dados:**

```
accounts ←— sales_pipeline —→ products
                ↓
           sales_teams
```

O `sales_pipeline.csv` é a tabela central. Cada registro é uma oportunidade com:

- `deal_stage`: Prospecting, Engaging, Won, Lost
- `engage_date` / `close_date`: timeline do deal
- `close_value`: valor real de fechamento (0 se Lost)

---

## O que foi entregue

Uma aplicação funcional de priorização de pipeline com duas interfaces complementares:

- **Streamlit** — exploração analítica dos dados, validação do modelo, documentação interativa
- **React + FastAPI** — produto final voltado para o vendedor e o manager, com views específicas por papel

A solução roda com dados reais do CRM, gera ação recomendada para cada deal, e explica o porquê de cada decisão — sem black box.

---

#### Streamlit View

- Interface analítica com 26 páginas organizadas em seis grupos, acessíveis por um hub de navegação central.
  - Documentação e contexto — enunciado do challenge, guia de navegação, instruções de inicialização e o próprio README renderizado na interface.
  - Raciocínio e modelo — cinco páginas que reconstroem o processo de decisão: visão macro do problema, análise heurística exploratória, preview interativo da lógica de scoring, detalhamento técnico do modelo e limitações conhecidas.
  - Dados brutos — visualização direta dos quatro CSVs do CRM (pipeline, contas, produtos, equipes) com contagem de linhas e prévia da estrutura.
  - Listas e cadastros — tabelas filtráveis de deals, contas, produtos, vendedores e managers, com métricas calculadas pelo motor de scoring aplicadas sobre cada entidade.
  - Análises — seis painéis com gráficos interativos: saúde e tempo do pipeline, distribuição de ações recomendadas, performance por produto, análise regional, drilldown por vendedor e análise de transferências recomendadas.
  - Sistema — Descrição completa sobre inicialização, arquitetura & stack e API da aplicação.

---

#### Seller View

- A experiência do vendedor começa com um dashboard pessoal: gráficos de saúde do pipeline, distribuição de ações recomendadas, série temporal de valor convertido e análise de win rate por produto — tudo filtrado para o próprio portfólio. 
  - O elemento central, porém, é o **feed de deals priorizados**:
  - Cada deal é apresentado como um conjunto de três cartões conectados por linhas:
    - O primeiro traz o contexto completo do deal (conta, região, produto, dias no pipeline, score com breakdown em urgência, probabilidade, valor e viabilidade); 
    - O segundo apresenta a ação recomendada em destaque com a justificativa em linguagem natural e os próximos passos numerados; 
    - O terceiro, exibido apenas em deals com sugestão de transferência, mostra o vendedor de destino recomendado, sua viabilidade esperada e as razões específicas do match — por que aquele vendedor, naquele momento, tem mais condições de fechar esse deal.
  - O vendedor navega horizontalmente pelo feed, deal a deal, e sai sabendo exatamente o que fazer — sem precisar interpretar um único número.

---

#### Manager View

- A view do manager é organizada em cartões verticais que ocupam a altura total da tela, navegáveis com scroll. 
  - O primeiro cartão é um **dashboard analítico em carrossel** com três seções: 
    - *Macro Analysis* (KPIs agregados, valor convertido no tempo, saúde do prospecting e medianas de tempo no pipeline); 
    - *Products & Regional Analysis* (performance por produto e por escritório regional); 
    - *Transfer Analysis* (4 métricas de resumo — total de transfers, críticos, consider e score médio — seguidas de dois gráficos, razões mais frequentes para transferência e distribuição do ganho de viabilidade esperado, e três mini-cards de impacto: Δ viabilidade média, viabilidade atual → target e contagem de transfers de alto impacto). 
    - Outros cartões incluem **Transfers** (feed de deals com ações TRANSFER e CONSIDER_TRANSFER), **Seller Analysis** (drilldown por vendedor), **Alertas** e **Squad** (cards dos vendedores com acesso à seller view).

---

## O insight que mudou a direção

> **57%** dos vendedores protegem deals ruins para se defenderem contra a falta de novos leads.

- A abordagem óbvia seria ordenar deals por `probabilidade × valor`. 
- Rejeitamos antes de escrever uma linha de código.

**Por quê:** essa solução responde "qual deal vale mais" — não responde "o que o vendedor deve fazer segunda de manhã". São perguntas diferentes.

A análise exploratória revelou o problema real:

```
Won  (fechados)      →  57 dias (mediana)
Lost (perdidos)      →  14 dias (mediana)   ← percebem rápido que não vai
Engaging (travados)  → 165 dias (mediana)   ← 2.9× Won. Ninguém age.
```

→ **Deals não ficam parados porque são difíceis.**
→ **Ficam parados porque ninguém age sobre eles.**

E a causa raiz: 57% dos vendedores têm prospecting = 0. 

Estão sobrecarregados (carga média 108 deals), protegendo o pipeline antigo para "manter aparência de pipeline". 

→ **Círculo vicioso clássico**.

Isso mudou o design inteiro: o sistema precisa considerar **capacidade do vendedor**, não só importância do deal.

→ A documentação descritiva completa da análise está em `[docs/heuristica.md](docs/heuristica.md)`

---

## Como o scoring funciona

Dois componentes independentes:

```
SCORE (0–100)        importância objetiva do deal
  50%  Urgência      → tempo travado vs. mediana histórica do produto
  30%  Probabilidade → win rate do vendedor ponderado por estágio e setor
  20%  Valor         → ticket vs. média histórica do portfólio

VIABILIDADE (0–100)  capacidade contextual do vendedor agora
  →  prospecting ativo?
  →  carga de deals suportável?
  →  especialização no produto/setor?
```

A cruzamento Score × Viabilidade gera a ação:


| Score \ Viabilidade | Alta ≥ 60    | Média 40–60    | Baixa < 40              |
| ------------------- | ------------ | -------------- | ----------------------- |
| **≥ 80**            | 🔥 PUSH HARD | 🔄 RE-QUALIFY  | 🔀 TRANSFER             |
| **70–79**           | 🔥 PUSH HARD | 🔄 RE-QUALIFY  | 🔀 TRANSFER · ❌ DISCARD |
| **60–69**           | ⚡ ACCELERATE | 🔍 INVESTIGATE | 🔀 CONSIDER TRANSFER    |
| **< 60**            | ⏸ MONITOR    | ⏸ MONITOR      | ⏸ MONITOR               |


**Por que viabilidade baixa pode significar transferência — não descarte:**

- Um deal com viabilidade 22 pode ser excelente. 
- O problema é o contexto: O vendedor com 148 deals e win rate de 31% naquele produto simplesmente não vai conseguir trabalhar esse deal.

Transferido para um vendedor com carga de 41 deals e win rate de 57% no produto, a viabilidade sobe para 68. 

→ **O deal não mudou — o contexto mudou**.

→ Lógica técnica completa em `[docs/logica.md](docs/logica.md)`

→ Raciocínio sobre transferências em `[docs/heuristica.md#transferências](docs/heuristica.md)`

---

## Como rodar: Resumo Rápido

> → Três terminais, três comandos. 

> → Cada serviço roda de forma independente.

- **Streamlit:** páginas como `Deals_Analysis.py` usam **Plotly** (`plotly.express`). 
- Com o `venv` ativo, instale dependências Python antes do primeiro run — por exemplo `pip install -r requirements.txt` (inclui `plotly` se listado no arquivo). 
- Detalhes em **Plotly (páginas Streamlit)** nos Pré-requisitos.

```bash
# Terminal 1 — Streamlit (Frontend A)
cd deal-prioritization
source venv/bin/activate
streamlit run streamlit_app/app.py

# Terminal 2 — API REST (FastAPI)
cd deal-prioritization
source venv/bin/activate
uvicorn api.main:app --reload --port 8001

# Terminal 3 — React (Frontend B)
cd deal-prioritization/frontend
npm run dev
```


| Serviço    | URL                          | Depende de                |
| ---------- | ---------------------------- | ------------------------- |
| Streamlit  | `http://localhost:8501`      | `core/` (direto, sem API) |
| FastAPI    | `http://localhost:8001`      | `core/` (direto)          |
| Swagger UI | `http://localhost:8001/docs` | FastAPI rodando           |
| React      | `http://localhost:5173`      | FastAPI rodando           |


> → Acesse a documentação completa de Inicialização em /Sistema/Inicialização no streamlit.

---

## Arquitetura & Stack

### Visão Geral da Arquitetura

O sistema é composto por três camadas independentes que compartilham um núcleo (`core/`) de dados e lógica de negócio.

```
┌─────────────────────────────────────────────────────────┐
│                      DATA SOURCES                        │
│   accounts.csv · products.csv · sales_pipeline.csv      │
│   sales_teams.csv                                        │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                        core/                             │
│   data_loader.py      — CSVs, joins, load_benchmarks()  │
│   scoring_engine.py   — score, viabilidade, ação, etc.  │
│   features.py · pipeline_win_rate_buckets.py — auxiliares│
└──────────┬──────────────────────────┬───────────────────┘
           │                          │
           ▼                          ▼
┌──────────────────┐       ┌─────────────────────────────┐
│  streamlit_app/  │       │           api/               │
│  (Frontend A)    │       │      (FastAPI REST)          │
│                  │       │                              │
│  Análise e       │       │  Expõe os dados via HTTP     │
│  exploração de   │       │  para consumo do frontend    │
│  dados           │       │  React                       │
└──────────────────┘       └──────────┬──────────────────┘
                                      │
                                      ▼
                           ┌─────────────────────────────┐
                           │        frontend/             │
                           │    (React — Frontend B)      │
                           │                              │
                           │  Seller + Manager views      │
                           │  (consome a API)             │
                           └─────────────────────────────┘
```

### Fluxo de Dados

```
data/metrics/          4 CSVs do CRM (accounts, products, sales_teams, pipeline)
      │
      ▼
core/                  Motor de scoring — Python puro, sem framework
  data_loader.py       → lê, normaliza e faz join das 4 tabelas
  scoring_engine.py    → calcula score, viabilidade e ação por deal
  benchmarks.py        → medianas históricas, win rates, top 20 contas
      │
      ├──▶  streamlit_app/    Frontend A — análise e validação (Streamlit)
      │
      └──▶  api/              FastAPI REST — expõe o motor via HTTP
                │
                ▼
            frontend/          Frontend B — produto final (React + TypeScript)
```

O `core/` é completamente desacoplado. Tanto o Streamlit quanto a API importam a mesma lógica — sem duplicação.

→ Detalhe completo da stack em `[docs/stack.md](docs/stack.md)`
→ Documentação dos endpoints em `[docs/README.api.md](docs/README.api.md)`

### Estrutura de pastas

```
deal-prioritization/
│
├── 📂 core/                          # Motor de dados e scoring (Python puro)
│   ├── data_loader.py                #   CSVs, joins, load_benchmarks(), preprocess
│   ├── scoring_engine.py             #   Urgência · Probabilidade · Valor · Score · Ação
│   ├── features.py                   #   Feature engineering auxiliar
│   ├── pipeline_win_rate_buckets.py  #   Faixas de tempo no pipeline (win rate)
│   └── __init__.py
│
├── 📂 data/
│   └── metrics/                      # CSVs originais do CRM
│       ├── accounts.csv
│       ├── products.csv
│       ├── sales_teams.csv
│       └── sales_pipeline.csv
│
├── 📂 docs/                          # Documentação em Markdown
│   ├── macro.md
│   ├── heuristica.md
│   ├── logica.md
│   ├── limitacoes.md
│   ├── stack.md
│   ├── inicializacao.md
│   └── README.api.md                 #   Documentação dos endpoints REST
│
├── 📂 api/                           # FastAPI REST — porta 8001
│   ├── main.py                       #   App, CORS, routers, GET /benchmarks, warmup
│   ├── dependencies.py               #   Cache de benchmarks e DataFrame do pipeline
│   └── routers/
│       ├── deals.py                  #   /deals
│       ├── sellers.py                #   /sellers
│       ├── managers.py               #   /managers
│       ├── products.py               #   /products
│       ├── accounts.py               #   /accounts
│       └── analysis.py               #   /analysis/*
│
├── 📂 streamlit_app/                 # Frontend A — análise e exploração
│   ├── app.py                        #   Hub de navegação (st.navigation)
│   └── pages/
│       ├── Navegacao.py              #   Mapa do sistema
│       ├── Inicializacao.py          #   Como rodar os serviços
│       ├── Challenge.py
│       ├── Macro.py
│       ├── Como_funciona.py
│       ├── Heuristica.py
│       ├── Score_Model.py
│       ├── Limitacoes.py
│       ├── Stack.py
│       ├── API.py
│       ├── Deal_List.py · Deal_Details.py
│       ├── Accounts_List.py · Products_List.py · Sellers_List.py · Managers_List.py
│       ├── Raw_Pipeline.py · Raw_Accounts.py · Raw_Products.py · Raw_Teams.py
│       └── Deals_Analysis.py · Action_Analysis.py · Products_Analysis.py
│           Regional_Analysis.py · Seller_Analysis.py · Transfer_Analysis.py
│
├── 📂 frontend/                      # Frontend B — React + Vite
│   ├── index.html
│   ├── vite.config.ts
│   ├── package.json
│   └── src/
│       ├── App.tsx · main.tsx
│       ├── types/index.ts
│       ├── api/                      #   client.ts + fetchers por entidade
│       ├── hooks/                    #   TanStack Query
│       ├── pages/
│       │   ├── Home.tsx              #   Manager view
│       │   └── SellerPage.tsx        #   Seller view
│       ├── components/               #   Dashboards, feed, charts (Recharts)
│       └── lib/                      #   utils.ts, helpers
│
├── README.md
└── requirements.txt
```

---

## Limitações & Escalabilidade

**Dados**

- Sem timestamps por estágio — urgência usa proxy de tempo total, não tempo real travado em cada fase
- Sem dados de atividade — não diferenciamos "deal sendo trabalhado" de "deal abandonado"
- Sem contexto competitivo — probabilidade não considera pressão de concorrentes

**Escopo do MVP**

- Modelo baseado em regras (não ML) — thresholds fixos, não detecta padrões não-óbvios; escolha consciente por explicabilidade
- Viabilidade calculada por vendedor, não por deal — não captura nuances como relacionamento pessoal com o cliente
- Ações são sugestões, não execuções — depende de adoção humana, sem tracking de taxa de execução
- Lê CSVs estáticos — sem integração com CRM real, sem sincronização bidirecional

**Escala e produção**

- Sem banco de dados real, sem cache distribuído, sem testes automatizados e sem autenticação/RBAC

→ Análise completa com caminhos de evolução em `[docs/limitacoes.md](docs/limitacoes.md)`

---

## Documentação


| Arquivo                                    | Conteúdo                                                     |
| ------------------------------------------ | ------------------------------------------------------------ |
| `[docs/macro.md](docs/macro.md)`           | Big picture — problema, diagnóstico, solução, KPIs esperados |
| `[docs/heuristica.md](docs/heuristica.md)` | Análise exploratória completa — como chegamos na tese        |
| `[docs/logica.md](docs/logica.md)`         | Detalhamento técnico do scoring e lógica de transferência    |
| `[docs/README.api.md](docs/README.api.md)` | Documentação de todos os endpoints REST                      |
| `[docs/stack.md](docs/stack.md)`           | Arquitetura, estrutura de pastas, decisões de design         |
| `[docs/limitacoes.md](docs/limitacoes.md)` | O que o modelo não faz e o que precisaria pra escalar        |


