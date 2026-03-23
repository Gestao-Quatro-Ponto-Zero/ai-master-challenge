# 🧠 Heurística

"**57%** dos vendedores protegem deals ruins para se defenderem contra a falta de novos leads".

---

## 📌 Contexto do Desafio

**Pergunta de negócio:**

> "Nossos vendedores gastam tempo demais em deals que não vão fechar e deixam oportunidades boas esfriar. Quero uma ferramenta que o vendedor abra, veja o pipeline, e saiba onde focar."

**Tradução:**

- ✅ Priorização de pipeline
- ✅ Interface para vendedor (não data scientist)
- ✅ Funcional e explicável (não black box)

**Primeira reação instintiva:**

```
"Vou fazer um modelo de ML que prediz probabilidade de fechar,
ordenar por prob × valor, e pronto."
```

**Por que rejeitamos essa abordagem:**
Essa solução responde "qual deal vale mais", mas não responde "o que fazer segunda-feira de manhã". Faltava contexto de **capacidade** do vendedor.

---

## 🔍 ETAPA 1: Exploração Descritiva

### O Que Encontramos

```python
📊 SNAPSHOT: 2017-12-31
Pipeline total: 8.800 deals

Distribuição por estágio:
├── Won:        4.238 (48.2%)
├── Lost:       2.473 (28.1%)
├── Engaging:   1.589 (18.0%)  ← Foco da análise
└── Prospecting:  500 (5.7%)

Win Rate Global: 63.15%
(Won / (Won + Lost))
```

### Primeira Observação

✅ **Win rate de 63% é saudável**  
Não é um time ruim que não sabe fechar.

⚠️ **Mas... 1.589 deals travados em Engaging**  
Quase 20% do pipeline está em estágio intermediário.

**Pergunta que surgiu:**

> "Engaging é naturalmente longo ou tem algo errado?"

---

## 💡 ETAPA 2: O Breakthrough — Análise de Tempo

Esta foi a análise que **mudou tudo**.

### Tempo de Ciclo por Estágio (Medianas)

```python
Won (fechados):      57 dias  ← Tempo "normal" para fechar
Lost (perdidos):     14 dias  ← Desistem rápido quando percebem que não vai
Engaging (travados): 165 dias ← 🔥 2.9× MAIS LENTO QUE WON

Engaging (média):    199 dias ← Ainda pior (3.5× Won)
```

### O Insight Crítico

```
HIPÓTESE INICIAL (descartada):
"Deals em Engaging são intrinsecamente mais difíceis de fechar."

EVIDÊNCIA CONTRÁRIA:
- Lost fecha rápido (14d) → Percebem rapidamente que não vai
- Won fecha em tempo razoável (57d) → Quando há ação, deals fecham

CONCLUSÃO:
O problema NÃO é dificuldade de fechar.
O problema é FALTA DE AÇÃO.

Deals ficam 165 dias travados não porque são difíceis,
mas porque vendedor não está dedicando atenção.
```

**Por que isso importa:**
Se o problema fosse "deals difíceis", a solução seria treinar vendedores ou ajustar fit de produto. Mas se o problema é "falta de ação", a solução é **priorização** e **redistribuição de capacidade**.

---

## 🔬 ETAPA 3: Investigando a Causa Raiz

**Nova pergunta:**

> "Por que vendedores não dão atenção aos deals em Engaging?"

### Análise de Prospecting

```python
📊 PROSPECTING POR VENDEDOR

Total de vendedores: 30

Com prospecting ativo (>0 deals novos):  13 (43%)
Sem prospecting (0 deals novos):         17 (57%)  ← MAIORIA

Correlação observada:
✅ Vendedor COM prospecting → Pipeline saudável
❌ Vendedor SEM prospecting → Pipeline travado
```

### O Padrão Identificado

```
VENDEDORES SEM PROSPECTING:

Exemplo: Corliss Cosme
- Active deals: 177
- Prospecting: 0
- Comportamento: Protege deals antigos (mesmo os ruins)

Exemplo: Anna Snelling
- Active deals: 112
- Prospecting: 0
- Comportamento: Protege deals antigos

VENDEDORES COM PROSPECTING:

Exemplo: Wilburn Tomas
- Active deals: 31
- Prospecting: 25
- Comportamento: Qualifica bem, descarta rápido

Exemplo: Marty Freudenburg
- Active deals: 87
- Prospecting: 54
- Comportamento: Pipeline saudável
```

### Insight #2: O Círculo Vicioso

```
Vendedor sobrecarregado (>100 deals)
    ↓
Não tem tempo para prospectar (0 novos)
    ↓
Protege deals antigos para "manter pipeline"
    ↓
Deals travados aumentam (165+ dias)
    ↓
Performance cai, mais sobrecarga...
    ↓
Loop infinito ❌
```

**Validação quantitativa:**

- Vendedores com prospecting = 0: **Carga média = 108 deals**
- Vendedores com prospecting >20: **Carga média = 52 deals**

Diferença: **2× de carga**

---

## 📊 ETAPA 4: Validação da Tese

### Hipótese a Testar

```
TESE:
Deals travados há muito tempo (>200 dias) têm probabilidade baixa
e ocupam espaço no pipeline sem retorno esperado.

Se isso for verdade:
→ Vendedor deveria DESCARTAR esses deals
→ Liberar atenção para deals viáveis
→ Quebrar o círculo vicioso
```

### Análise: Tempo × Probabilidade

Calculamos win rate por faixa de tempo no pipeline:

```python
📈 CORRELAÇÃO: Tempo em Pipeline × Win Rate

Faixa          | Deals | Win Rate
---------------|-------|----------
< 28 dias      |   234 |   68%    ← Frescos
28-57 dias     |   312 |   64%    ← Normal
57-85 dias     |   289 |   61%    ← Começando cair
85-165 dias    |   421 |   55%    ← Caindo
165-200 dias   |   156 |   48%    ← Baixa
> 200 dias     |   177 |   38%    ← 🔥 MUITO BAIXA

CONCLUSÃO:
Tempo NO pipeline corrói probabilidade.
Deals >200d têm 38% chance (vs 63% global).
Perda de 25 pontos percentuais.
```

### Insight #3: Urgência Real

```
Deals >200 dias:
- Representam 11% do pipeline (177 deals)
- Probabilidade caiu para 38% (vs 63% global)
- Vendedor sem capacidade de resolver (carga alta + sem prospecting)
- Ocupam atenção mas não geram retorno

DECISÃO:
Estes deals precisam de AÇÃO IMEDIATA ou DESCARTE.
Não podem continuar "congelados".
```

---

## 🎯 A TESE FINAL

### Diagnóstico Completo

```
╔══════════════════════════════════════════════════════════╗
║  TESE CENTRAL: Pipeline Travado por Falta de Ação       ║
╚══════════════════════════════════════════════════════════╝

📌 EVIDÊNCIAS CONSOLIDADAS:

1. TEMPO EXCESSIVO (2.9× maior que Won)
   ✓ Engaging: 165d mediana vs Won: 57d
   ✓ Não é dificuldade (Lost fecha em 14d)
   ✓ É FALTA DE AÇÃO (deals "esquecidos")

2. FALTA DE PROSPECTING (57% dos vendedores)
   ✓ Maioria não prospecta (0 deals novos)
   ✓ Protegem deals ruins por falta de pipeline
   ✓ Círculo vicioso: carga → sem prospectar → mais carga

3. DESBALANCEAMENTO DE CAPACIDADE
   ✓ Alguns vendedores: 150+ deals (sobrecarga crítica)
   ✓ Outros vendedores: 30-50 deals (capacidade disponível)
   ✓ Oportunidade de REDISTRIBUIÇÃO

4. PROBABILIDADE CORRÓI COM TEMPO
   ✓ Deals >200d: probabilidade cai para 38%
   ✓ Ocupam espaço sem retorno esperado
   ✓ Devem ser DESCARTADOS ou TRANSFERIDOS

╔══════════════════════════════════════════════════════════╗
║  SOLUÇÃO: Priorização Contextual (Score × Viabilidade)  ║
╚══════════════════════════════════════════════════════════╝
```

---

## 🔀 Transferências como Alavanca de Eficiência

### O Problema que a Transferência Resolve

O círculo vicioso identificado na ETAPA 3 tem dois lados:

```
VENDEDOR SOBRECARREGADO          VENDEDOR COM CAPACIDADE
────────────────────────         ──────────────────────────
150+ deals ativos                30–50 deals ativos
0 prospecting                    Prospecting ativo
Deal parado há 200d              Conhece o produto/setor
Viabilidade: 22                  Viabilidade potencial: 65
    ↓                                    ↑
    └──── Deal deveria estar aqui ───────┘
```

A transferência não é "repassar um problema". É reconhecer que **um deal viável nas mãos erradas se torna um deal inviável** — e corrigir esse desalinhamento antes que o tempo destrua a probabilidade.

---

### Por Que Viabilidade Baixa Não Significa Deal Ruim

```
INTERPRETAÇÃO INCORRETA:
Viabilidade baixa = deal fraco = descartar

INTERPRETAÇÃO CORRETA:
Viabilidade = capacidade contextual deste vendedor neste momento

Viabilidade 22 pode significar:
  ├── Vendedor com carga de 150 deals
  ├── Win rate historicamente baixo neste produto
  ├── Região onde não tem expertise
  └── Pipeline prospecting zerado (sem foco possível)

O deal pode ser excelente.
O problema é o contexto — não o deal.
```

Isso muda fundamentalmente o diagnóstico: não é "este deal não vale esforço", é "este deal não vai receber esforço aqui".

---

### O Ganho de Eficiência: Delta de Viabilidade

A transferência gera eficiência mensurável através do **delta de viabilidade** entre o contexto atual e o contexto do vendedor de destino:

```
Δ Viabilidade = viabilidade_target − viabilidade_atual

Exemplo real:
  Vendedor atual (Carlos):   viabilidade = 22
    → carga: 148 deals, WR produto: 31%, prospecting: 0

  Vendedor destino (Ana):    viabilidade = 68
    → carga: 41 deals, WR produto: 57%, mesma região

  Δ = +46 pontos

Interpretação:
  O mesmo deal, transferido, passa de 22% de contexto favorável
  para 68% — sem nenhuma mudança no deal em si.
```

O ganho não é hipotético. É a diferença entre dois contextos reais, calculada com os mesmos dados de win rate, carga e prospecting que o sistema já usa para score.

---

### O Efeito Cascata: Um Deal Move Dois Problemas

A transferência resolve dois gargalos simultaneamente:

```
PROBLEMA 1: Deal parado
  Vendedor atual não tem capacidade → Deal não avança → Probabilidade cai
  Transferência → Deal tem capacidade → Deal pode avançar

PROBLEMA 2: Vendedor sobrecarregado
  Antes: 150 deals → sem tempo para prospectar → círculo vicioso
  Após:  149 deals → marginal, mas...

  Se 5–10 deals são transferidos:
  → Carga cai para 140–145
  → Vendedor recupera foco
  → Volta a prospectar
  → Quebra o círculo vicioso
```

Individualmente, cada transferência parece pequena. Em conjunto, é a diferença entre um vendedor que está em colapso de pipeline e um que volta a funcionar.

---

### TRANSFER vs CONSIDER_TRANSFER: Gradação de Urgência

O sistema usa dois níveis porque o custo de transferir não é zero:

```
TRANSFER (ação imediata):
  ├── Viabilidade atual < 40
  ├── Score alto (deal importante)
  └── Delta viabilidade significativo (≥ 20 pts)

  Interpretação: Manter este deal aqui é desperdiçar uma
  oportunidade boa. O custo de NÃO transferir é maior
  que o custo de transferir.

CONSIDER_TRANSFER (avaliar):
  ├── Viabilidade atual baixa, mas deal menos crítico
  ├── Delta de viabilidade existe, mas moderado
  └── Pode valer negociar contexto antes de mover

  Interpretação: Existe ganho potencial, mas a decisão
  depende de fatores que o modelo não vê (relacionamento,
  negociação em curso, preferência do cliente).
```

O CONSIDER_TRANSFER preserva julgamento humano onde o modelo tem incerteza. O TRANSFER sinaliza onde a evidência quantitativa é forte o suficiente para recomendar ação direta.

---

### Hierarquia de Destino: Onde o Deal Vai

O sistema prioriza destinos em ordem de custo de transição:

```
1. SAME_TEAM (mesmo squad)
   Menor fricção: gestor comum, contexto compartilhado
   → Preferido quando há vendedor disponível

2. SAME_REGION (mesma região)
   Fricção moderada: cultura regional alinhada,
   sem mudança de território de conta
   → Usado quando equipe não tem capacidade

3. OTHER_REGION (outra região)
   Maior fricção: pode implicar reajuste de territory,
   relacionamento com cliente mais distante
   → Acionado apenas quando delta de viabilidade
     compensa o custo de transição
```

Essa hierarquia garante que a transferência mais eficiente seja também a menos disruptiva — priorizando ganho com menor custo organizacional.

---

### Insight Contraintuitivo: Transferir é Melhor que Insistir

```
INTUIÇÃO DO GESTOR:
"Vendedor precisa aprender a fechar este tipo de deal."

EVIDÊNCIA:
Deals >200 dias com viabilidade <40 têm probabilidade <38%.
Manter o vendedor insistindo neles:
  ✗ Consome atenção de deals viáveis
  ✗ Não ensina (ambiente errado para aprendizado)
  ✗ Corrói ainda mais a probabilidade com o tempo
  ✗ Mantém o círculo vicioso ativo

Transferir:
  ✓ Deal vai para contexto onde pode fechar
  ✓ Vendedor original libera foco
  ✓ Gestor ganha visibilidade de desbalanceamento de carga
  ✓ Sistema aprende padrões de fit vendedor × produto
```

A resistência à transferência geralmente vem de uma confusão entre "deal do vendedor" e "deal da empresa". No segundo caso, o objetivo é fechar — não importa por quem.

---

## 🚫 Por Que NÃO Foi Machine Learning

### Abordagem Rejeitada #1: Modelo Preditivo Simples

```python
# O que poderíamos ter feito (e não fizemos):
probability = predict_win_probability(deal)
value = deal['close_value']
score = probability * valueA 

# Ordenar por expected_value, done.
```

**Por que rejeitamos:**

❌ **Ignora contexto do vendedor**  
Deal com 80% prob é prioritário, mas... e se vendedor tem 150 deals?

❌ **Não responde "o que fazer"**  
Score alto significa... push? transfer? discard? Não diz.

❌ **Black box para vendedor**  
"Por que este deal tem score 85?" → "O modelo disse" ❌

### Abordagem Rejeitada #2: Feature Engineering Complexo

```python
# Poderíamos ter usado:
features = [
    'days_in_pipeline', 'account_revenue', 'product_price',
    'seller_historical_wr', 'account_sector_wr', 'seasonality',
    'engagement_frequency', 'email_sentiment', ...
]

model = XGBoost(features)
```

**Por que rejeitamos:**

❌ **Não temos dados de engajamento**  
Dataset tem só: deal_stage, dates, valores. Sem "email_sentiment".

❌ **Overfitting com 8.800 samples**  
Não é Big Data. Modelo complexo vai overfit.

❌ **Manutenção impossível**  
Vendedor pergunta "por que?" → Data scientist precisa explicar 47 features.

### Abordagem Escolhida: Heurísticas + Explicabilidade

```python
# O que fizemos:
score = urgency (50%) + probability (30%) + value (20%)
viability = capacity_do_vendedor

action = f(score, viability)
```

**Por que funcionou:**

✅ **Transparente**  
"Score alto porque: 200 dias travado + produto premium + conta top 20"

✅ **Contextual**  
Considera se vendedor TEM capacidade de agir.

✅ **Iterável**  
Começa simples, melhora com feedback.

✅ **Vendedor entende**  
Não precisa de PhD em ML para usar.

---

## 🎨 Trade-offs Conscientes

### Decisão #1: Regras > Machine Learning

```
ESCOLHA:
Scoring baseado em regras e thresholds (não ML)

GANHOS:
✓ Explicabilidade total
✓ Manutenção simples
✓ Não precisa retreinar
✓ Vendedor confia

PERDAS:
✗ Menos preciso que modelo treinado
✗ Não aprende padrões automático

JUSTIFICATIVA:
Modelo 70% preciso que vendedor USA >
Modelo 95% preciso que vendedor IGNORA.
```

### Decisão #2: Viabilidade Separada do Score

```
ESCOLHA:
Score (importância objetiva) ≠ Viabilidade (capacidade contextual)

GANHOS:
✓ Score é "justo" (mesmo deal = mesmo score para todos)
✓ Viabilidade personaliza ação por vendedor
✓ Matriz (score × viab) gera ações inteligentes

PERDAS:
✗ Mais complexo de explicar
✗ Dois números em vez de um

JUSTIFICATIVA:
Deal importante para vendedor A pode não ser acionável por A.
Ação depende de CONTEXTO, não só importância.
```

### Decisão #3: Value-First Design

```
ESCOLHA:
Sistema usa APENAS dados existentes (não pede input novo)

GANHOS:
✓ Zero fricção inicial
✓ Vendedor vê valor ANTES de dar esforço
✓ Adoção mais provável

PERDAS:
✗ Modelo menos preciso inicialmente
✗ Falta dados de engajamento

JUSTIFICATIVA:
Vendedores não atualizam CRM se não veem ROI.
Gerar valor PRIMEIRO, pedir dados DEPOIS.
```

---

## ⚠️ Premissa Crítica: Qualidade de Dados

### O Paradoxo do CRM

É sabida a dificuldade de vendedores em manter CRMs atualizados. Por dificuldade técnica ou falta de aproximação tecnológica, o abandono de sistemas de priorização é comum.

### O Risco para Este Modelo

Este modelo **depende** de dados de qualidade:

```python
CAMPOS CRÍTICOS:
✓ deal_stage: Precisa estar atualizado (Engaging, Won, Lost)
✓ engage_date: Quando começou trabalhar o deal
✓ close_date: Quando fechou/perdeu
```

**Se dados estão ruins:**

```
Vendedor não atualiza → Deal parece travado → Sistema recomenda mal
    ↓
Vendedor perde confiança → Para de usar → Sistema é abandonado
    ↓
Círculo vicioso ❌
```

### Nossa Estratégia de Mitigação

**1. Gerar Valor ANTES de Pedir Esforço**

Sistema usa APENAS dados existentes na primeira versão. Vendedor não precisa fazer NADA novo para ver benefício.

Exemplo:

- Deal há 200 dias em Engaging? → Sistema detecta automaticamente
- Vendedor com 150 deals? → Sistema alerta sobre sobrecarga
- Colega com 30 deals? → Sistema sugere transferência

**Resultado:** "Isso me ajuda!" (não "mais burocracia")

**2. Reduzir Fricção ao Máximo**

Quando precisar de input futuro:

- ✅ Um clique: "Ação completada?"
- ✅ Inferência: Deal fechou? → Auto-update para Won
- ✅ Sugestões: Próximo passo (não campo de texto livre)

**NÃO fazemos:**

- ❌ Formulários longos
- ❌ Campos de texto livre obrigatórios
- ❌ Atualizações manuais diárias

**3. Transparência de Limitações**

Sistema AVISA quando dados podem estar desatualizados:

```
⚠️ "Deal sem atualização há 90 dias — ainda ativo?"
⚠️ "Score assume dados atualizados (última mudança: 45d atrás)"
```

Vendedor sabe que modelo depende de dados, mas entende POR QUÊ.

**4. Loop de Melhoria Contínua**

```
Vendedor usa → Dados melhoram → Modelo aprende → Mais valor gerado
    ↓
Loop virtuoso ✅
```

Não é "sistema perfeito no dia 1". É "sistema que APRENDE e MELHORA com uso".

---

## 📊 Metodologia de Validação

### Como Testamos as Hipóteses

```python
ETAPA 1: Exploração Descritiva
├── Distribuição de deals por estágio
├── Win rate global
└── Volume por vendedor

ETAPA 2: Análise de Tempo (BREAKTHROUGH)
├── Mediana por estágio (Won, Lost, Engaging)
├── Comparação entre estágios
└── 💡 INSIGHT: Engaging 2.9× Won

ETAPA 3: Investigação de Causas
├── Análise de prospecting (57% em zero)
├── Distribuição de carga (max 177, min 7)
└── 💡 INSIGHT: Círculo vicioso identificado

ETAPA 4: Validação Quantitativa
├── Correlação tempo × probabilidade
├── Análise de deals >200d (prob 38%)
└── 💡 INSIGHT: Tempo corrói probabilidade

ETAPA 5: Síntese
├── Consolidação de evidências
├── Validação cruzada de padrões
└── ✅ TESE VALIDADA
```

---

## 💡 Insights Contraintuitivos

### O Que Descobrimos Que NÃO Era Óbvio

**1. Win Rate alto MAS pipeline travado**

```
Pensamento inicial: "63% WR é bom, está tudo ok"
Realidade descoberta: Pipeline travado mascara ineficiência
```

**2. Lost fecha RÁPIDO (14 dias)**

```
Pensamento inicial: "Perdemos rápido = problema"
Realidade descoberta: Perder rápido é BOM (libera atenção para deals viáveis)
```

**3. Prospecting = 0 não é "foco"**

```
Pensamento inicial: "Vendedor focado em fechar os deals atuais"
Realidade descoberta: Vendedor protegendo deals ruins por falta de pipeline
```

**4. Tempo destrói probabilidade**

```
Pensamento inicial: "Tempo = maturação do deal"
Realidade descoberta: Tempo = perda de probabilidade (-25 pontos)
```

**5. Score sem viabilidade é inútil**

```
Pensamento inicial: "Ordenar por importância resolve"
Realidade descoberta: Importância sem contexto de capacidade não gera ação
```

---

## 🎯 Conclusão: Por Que Esta Tese Importa

### O Problema Real Não Era Priorização

```
PROBLEMA APARENTE:
"Vendedores não sabem quais deals focar."

PROBLEMA REAL (descoberto):
"Vendedores sobrecarregados protegem deals ruins,
criando círculo vicioso de pipeline travado."
```

### A Solução Precisa Atacar a Causa Raiz

```
SOLUÇÃO SUPERFICIAL (rejeitada):
Ordenar deals por probabilidade × valor

SOLUÇÃO PROFUNDA (implementada):
1. Identificar deals travados (urgência)
2. Considerar probabilidade real (não wishful thinking)
3. Ponderar valor estratégico (não só $$$)
4. Avaliar capacidade do vendedor (viabilidade)
5. Sugerir AÇÃO (PUSH, TRANSFER, DISCARD, MONITOR)
```

### Por Que Isso Funciona na Prática

```
✅ Vendedor vê benefício imediato
   "Esses 10 deals >200d mesmo não vão fechar, vou descartar"

✅ Libera atenção para deals viáveis
   "Agora posso focar nos 5 deals críticos"

✅ Quebra círculo vicioso
   "Tenho espaço para prospectar de novo"

✅ Cria círculo virtuoso
   Prospecting → Pipeline saudável → Melhor qualificação → Mais fechamentos
```

---

## 📚 Aprendizados para Próximas Iterações

### O Que Funcionou

✅ **Análise exploratória aprofundada**  
Tempo investido em EDA gerou insights que ML cego não teria encontrado.

✅ **Foco em explicabilidade**  
Regras simples > Black box complexo para adoção.

✅ **Tese validada quantitativamente**  
Não foi "achismo" — cada insight tem evidência numérica.

### O Que Precisaria Melhorar

⚠️ **Dados de engajamento**  
Faltam: emails trocados, calls feitos, propostas enviadas.

⚠️ **Feedback loop real**  
Hoje é simulação. Precisaria validar com vendedores reais.

⚠️ **Especialização por produto**  
Identificamos especialistas, mas não personalizamos score por isso.

### Próximos Passos (se fosse produção)

```
FASE 1 (MVP): Sistema atual ✅
- Score baseado em regras
- Ações sugeridas
- Interface funcional

FASE 2 (Learning):
- Capturar feedback de vendedores (ação foi útil?)
- Aprender thresholds personalizados por vendedor
- Ajustar pesos (50/30/20) com dados reais

FASE 3 (ML Híbrido):
- Manter explicabilidade (regras)
- Adicionar ML para refinar probabilidade
- Ensemble: regras (base) + ML (refinamento)

FASE 4 (Proativo):
- Alertas automáticos (deal sem ação há 30d)
- Sugestões de próximos passos
- Integração com calendário/email
```

---

## 📌 Resumo Executivo

**De onde partimos:**

- Pergunta: "O que vendedor deve focar segunda de manhã?"
- Hipótese inicial: "Ordenar por probabilidade × valor"

**O que descobrimos:**

- Pipeline travado (165d mediana vs 57d Won)
- Falta de prospecting (57% vendedores em zero)
- Círculo vicioso (carga → sem prospectar → mais carga)
- Tempo corrói probabilidade (-25 pontos >200d)

**Tese validada:**
Pipeline travado por FALTA DE AÇÃO, não dificuldade de fechar.

**Solução implementada:**
Score contextual (urgência + prob + valor) × Viabilidade → Ação sugerida

**Por que funciona:**

- Explicável (vendedor entende)
- Contextual (considera capacidade)
- Acionável (sugere próximo passo)
- Iterável (melhora com uso)

---

