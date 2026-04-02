# PROCESS_LOG.md — Pipeline Coach AI
# Evidências concretas e verificáveis do processo de desenvolvimento com IA

> Este arquivo complementa o README.md com evidências que podem ser auditadas
> independentemente. Cada seção inclui saídas reais, decisões documentadas e
> artefatos que comprovam o que foi feito — não apenas o que foi dito.

---

## 1. Ferramentas de IA — por que e quando cada uma

| Ferramenta | Fase | Função específica | Verificável em |
|------------|------|-------------------|----------------|
| **ChatGPT (GPT-4)** | 1 | Decomposição inicial do problema | Seção 2 — prompt e saída documentados |
| **Claude (Anthropic)** | 2–11 | Análise de dados, especificação, prompts, documentação | Todos os artefatos em `agent-context/` |
| **Lovable** | 7, 10 | Build da aplicação React | App ao vivo: [pipelinecoachai.lovable.app](https://pipelinecoachai.lovable.app/) |
| **Antigravity** | 10 | Validação cruzada dos prompts | Seção 7 — resultado independente documentado |

---

## 2. Fase 1 — ChatGPT: decomposição do problema

**Ferramenta:** ChatGPT (GPT-4)
**Data:** início do projeto

### Prompt enviado ao ChatGPT

```
A Head de Revenue Operations de uma empresa B2B me disse:

"Nossos vendedores gastam tempo demais em deals que não vão fechar e deixam
oportunidades boas esfriar. Preciso de algo funcional — não um modelo no Jupyter
Notebook que ninguém vai usar. Quero uma ferramenta que o vendedor abra, veja o
pipeline, e saiba onde focar. Pode ser simples, mas precisa funcionar."

Temos 4 CSVs: sales_pipeline (8.800 oportunidades), sales_teams (35 vendedores),
products (7 produtos), accounts (85 contas).

Me ajude a estruturar como atacar esse problema antes de começar a fazer qualquer coisa.
```

### Output do ChatGPT (resumo estruturado)

O ChatGPT devolveu uma decomposição em três camadas que guiou todo o projeto:

1. **Dados disponíveis** → entender o que o CRM realmente contém antes de qualquer hipótese
2. **Insights acionáveis** → transformar padrões em critérios de priorização defensáveis
3. **Ferramenta usável** → uma interface que o vendedor abra segunda de manhã sem treinamento

### Decisão humana após o ChatGPT

A decomposição foi útil, mas o output foi genérico — sem nenhum dado real, sem código,
sem especificação técnica. Decisão: usar o ChatGPT apenas para essa fase de estruturação
e migrar para Claude para todo o desenvolvimento subsequente.

**Motivo da migração:** Claude permite manter contexto persistente de arquivos e código
ao longo de muitas iterações. Para um projeto com 8 arquivos `.md` interdependentes +
análise Python + geração de TypeScript, isso foi determinante.

---

## 3. Fase 3 — Claude: análise exploratória dos dados

**Ferramenta:** Claude (Anthropic) com os CSVs como arquivos de projeto
**Output verificável:** `sales_dashboard.html` (artefato gerado nesta fase)

### O que foi pedido ao Claude

Quatro rodadas de análise Python sobre os CSVs, cada uma com um foco:

```
Rodada 1: distribuição de stages, win rate geral, receita total
Rodada 2: win rate por vendedor, ciclo médio, top 5 por receita
Rodada 3: win rate por mês (2017-03 a 2017-12), padrão temporal
Rodada 4: ticket médio por produto, top contas, distribuição de ciclos
```

### Outputs reais que saíram da análise (verificáveis nos dados)

```
Dataset: 8.800 deals | Won: 4.238 | Lost: 2.473 | Open: 2.089
Win rate: 63,2% | Receita: $10.005.534 | Ciclo médio: 51,8d

Win rate por mês:
  Mar/17: 82,1% | Abr/17: 48,6% | Mai/17: 54,4% | Jun/17: 82,8%
  Jul/17: 49,1% | Ago/17: 56,8% | Set/17: 79,2% | Out/17: 49,3%
  Nov/17: 52,9% | Dez/17: 78,5%

Top 5 reps por receita:
  Darcel Schlecht:  $1.153.214 (11,5% da receita total — risco de concentração)
  Vicki Laflamme:   $478.396
  Kary Hendrixson:  $454.298
  Cassey Cress:     $450.489
  Donn Cantrell:    $445.860

Ticket médio por produto:
  GTK 500:        $26.768 (lista) — 15 deals Won, $400.612 receita
  GTX Plus Pro:   $5.482  (lista) — 479 deals Won, $2.629.651 receita
  GTXPro:         $4.821  (lista) — 729 deals Won, $3.510.578 receita
  MG Special:     $55     (lista) — 793 deals Won, $43.768 receita ← sem ROI
```

### Decisão humana sobre o padrão de oscilação

Claude identificou os números. A **interpretação** foi humana: o padrão de ondas mensais
(82% / 48% / 82% / 49%...) não é ruído nem anomalia. É um padrão de pipeline onde deals
abertos num mês fecham em bloco dois meses depois. Isso foi documentado explicitamente
no `MVP_UPDATE_RESULTS_PROMPT.md` para evitar que agentes construtores tratassem como bug.

---

## 4. Fase 5 — Claude: especificação do scoring engine

**Ferramenta:** Claude
**Output verificável:** `agent-context/SCORING_ENGINE.md` + `scoring_engine.py`

### O que foi pedido ao Claude

```
Com base nos dados analisados, preciso especificar um scoring engine que priorize
os deals abertos de cada vendedor. Os critérios devem ser:
1. Defensáveis pelo problema de negócio (não arbitrários)
2. Executáveis em TypeScript no browser (sem backend)
3. Com explainability — o vendedor precisa entender por que cada deal está no topo
```

### Decisão humana sobre os pesos

Claude propôs a fórmula. Os **pesos específicos** foram decisão humana:

- D1 + D2 = 50 pts máximos → porque "deals bons esfriando" é o problema central
- D3 = 20 pts → valor importa, mas não deve dominar sobre urgência
- D4 = 20 pts → Engaging vs Prospecting é discriminante real de conversão
- D5 = 10 pts → bônus de benchmark, não driver principal

Se os pesos fossem invertidos (D3 dominante), o scoring priorizaria sempre GTK 500 —
que tem apenas 15 deals no período. Errado para o problema.

### Saída verificável do scoring engine (execute para confirmar)

```bash
python scoring_engine.py --rep "Darcel Schlecht" --csv-dir .
```

Saída esperada:
```
  PRIORIDADES DO DIA — Darcel Schlecht
  Referência: 2017-12-27 | Deals abertos: 194 | Mostrando Top 5

  #1 [🔴 Crítico] Score: 100
     Conta:   Isdom
     Produto: GTX Plus Pro  |  Stage: Engaging
     Valor:   $5,482  |  161d em aberto (desde 2017-07-19)
     Razão:   161d sem contato · Engaging · $5.5K
     Score breakdown: D1=25 + D2=25 + D3=20 + D4=20 + D5=10 = 100
```

```bash
python scoring_engine.py --validate --csv-dir .
```

Saída esperada (checks que validam os inputs do scoring):
```
  Win rate global (verifica dataset):  63.2%  (esperado: 63,2%) ✅
  Team avg Central Won:  52.6d
  Team avg East    Won:  50.6d
  Team avg West    Won:  51.8d
  Account vazio: 1425 linhas (16.2%)  (esperado: ~16,2%) ✅
  GTXPro no pipeline: 1480 deals  (normalização GTX Pro→GTXPro: ✅ ativa)
```

---

## 5. Fase 6 — Claude: geração do Prompt 1 para construtor de site

**Ferramenta:** Claude
**Output verificável:** `agent-context/MVP_BUILDER_PROMPT.md` (574 linhas)

### O que foi pedido ao Claude

```
Com base em todo o contexto acumulado — análise de dados, scoring engine especificado,
8 arquivos .md de contexto — gere um prompt completo para um agente construtor de sites
(Lovable, Bolt, v0 ou equivalente) construir o MVP do Pipeline Coach AI.

O prompt deve ser executável uma única vez, sem interação intermediária.
O construtor não deve precisar perguntar nada.
```

### Estrutura do prompt gerado (verificável em MVP_BUILDER_PROMPT.md)

O prompt de 574 linhas inclui:

```
Seção 1: Papel e objetivo do agente construtor
Seção 2: Arquivos disponíveis (agent-context/ + CSVs)
Seção 3: Escopo do MVP (3 rotas: /rep, /manager, /upload)
Seção 4: Especificação completa de /upload (validação de headers, anomalias)
Seção 5: Dashboard do Vendedor — 4 blocos + fluxo de registro (≤5 segundos)
Seção 6: Dashboard do Gestor — 5 blocos + filtros
Seção 7: Scoring engine em TypeScript (código completo)
Seção 8: Regras de processamento de CSV (safeFloat, normalizeProduct)
Seção 9: Stack técnica recomendada
Seção 10: Design system (cores obrigatórias, tipografia)
Seção 11: Copy rules (permitido / proibido)
Seção 12: Checklist de validação antes de entregar
Seção 13: Ordem de build recomendada
Seção 14: O que NÃO construir no MVP
```

---

## 6. Fase 7 — Lovable: build da aplicação

**Ferramenta:** Lovable (agente construtor de sites)
**Prompt usado:** `agent-context/MVP_BUILDER_PROMPT.md` (colado integralmente)

### O que aconteceu

O prompt foi executado no Lovable em uma única sessão. A aplicação foi gerada com:
- Upload de CSVs com validação de headers
- Scoring engine em TypeScript (implementação do SCORING_ENGINE.md)
- Dashboard de atividades com 4 blocos acima do fold
- Dashboard do gestor com ranking e filtros
- Seletor de papel na tela inicial

**A aplicação funcionou na primeira execução do prompt.** Nenhum ajuste de prompt foi
necessário para o build inicial.

### Decisão humana após o build

Testando a aplicação como um vendedor real usaria, percebi uma lacuna crítica: o
vendedor via o que **fazer** (atividades), mas não via o que **já tinha feito** (resultados).
Sem histórico de receita, sem evolução de deals fechados, sem nada sobre performance passada.

Essa lacuna **não estava no briefing original** e **não foi identificada pela IA** — foi
identificada usando a aplicação. Isso levou à Fase 8.

---

## 7. Fase 9 — Claude: análise para o dashboard de resultados

**Ferramenta:** Claude
**Output verificável:** `agent-context/MVP_UPDATE_RESULTS_PROMPT.md`

### Análise Python adicional executada

```python
# Receita por mês (para identificar o que mostrar no gráfico principal)
# Mar/17: $1.134.672 | Abr/17: $721.932 | Mai/17: $1.025.713
# Jun/17: $1.338.466 | Jul/17: $696.932  | Ago/17: $1.050.059
# Set/17: $1.235.264 | Out/17: $731.980  | Nov/17: $938.943 | Dez/17: $1.131.573

# Distribuição de ciclo (para o gráfico de barras horizontais)
# < 30 dias:  45,6% dos deals Won (Darcel Schlecht: 159/349)
# 30–60 dias:  8,9%
# 60–90 dias: 25,2%
# > 90 dias:  20,3%

# Top contas por receita (para a tabela)
# Kan-code: 115 deals, $341.455
# Konex:    108 deals, $269.245
# Condax:   105 deals, $206.410
```

### Decisão humana sobre as 7 visualizações

Claude executou a análise. **Eu decidi** quais 7 visualizações incluir e por quê:

1. **KPIs fixos** → primeira coisa que o vendedor vê, sem precisar rolar
2. **Receita mensal** → evolução temporal, linha de win rate sobreposta (padrão de ondas)
3. **Timeline por produto** → quais produtos estão crescendo ou caindo
4. **Ciclo de fechamento** → onde o rep está perdendo tempo (>90d)
5. **Receita acumulada** → narrativa de crescimento, satisfação com progresso
6. **Top contas** → concentração de clientes, risco de churn
7. **Mix de produtos** → diversificação ou dependência de um produto só

---

## 8. Erros da IA e correções aplicadas

### Erro 1 — Scoring com data incorreta

**Ferramenta:** Claude  
**Quando:** primeira versão do scoring engine

**O que aconteceu:**
```python
# Código gerado pela IA (ERRADO):
days_in_stage = (datetime.today() - parse_date(deal['engage_date'])).days
# → Com dataset de 2017, todos os deals ficavam com ~2.500 dias de aging
# → Todos os scores = 100, nenhuma discriminação possível
```

**Como identifiquei:** rodei a análise e todos os 2.089 deals abertos tinham score 100.
Se tudo é urgente, nada é urgente.

**Correção aplicada:**
```python
# Código corrigido:
REFERENCE_DATE = datetime(2017, 12, 27)  # última data do dataset
days_in_stage = (REFERENCE_DATE - parse_date(deal['engage_date'])).days
```

**Propagação da correção:** adicionada como `REFERENCE_DATE = new Date('2017-12-27')` no
TypeScript do Prompt 1 e documentada como erro proibido em `AGENT_INSTRUCTIONS.md`.

---

### Erro 2 — Join de produtos quebrando silenciosamente

**Ferramenta:** Claude  
**Quando:** primeira versão da análise de dados

**O que aconteceu:**
```python
# Código gerado pela IA (ERRADO):
product_info = products[deal['product']]
# → KeyError silencioso para "GTXPro" porque products.csv tem "GTX Pro"
# → Fallback para est_value=0 em 1.480 deals (16,8% do total)
# → D3 zerava para todos esses deals — distorção massiva do scoring
```

**Como identifiquei:** checando a soma de `est_value` dos deals abertos. O total estava
muito abaixo do esperado. Debug mostrou que todos os deals de GTXPro tinham est_value=0.

**Correção aplicada:**
```python
def normalize_product(name: str) -> str:
    return name.replace(" ", "")
# "GTX Pro" → "GTXPro"  (único caso afetado)

products[p['product']] = p
products[normalize_product(p['product'])] = p  # alias normalizado
```

**Propagação:** documentado como "Known Data Issue" em `DATA_SCHEMA.md` e como
erro proibido #1 em `AGENT_INSTRUCTIONS.md`.

---

### Erro 3 — parseFloat() quebrando em deals abertos

**Ferramenta:** Claude  
**Quando:** análise de receita

**O que aconteceu:**
```python
# Código gerado pela IA (ERRADO):
revenue = float(deal['close_value'])
# → Para os 2.089 deals abertos: close_value = "" (string vazia, não null)
# → float("") → ValueError
# → Ou, com try/except ingênuo: NaN propagado por todos os cálculos
```

**Como identifiquei:** receita total calculada como NaN na primeira rodada.

**Correção aplicada:**
```python
def safe_float(val: str, default: float = 0.0) -> float:
    try:
        return float(val) if val and val.strip() else default
    except (ValueError, TypeError):
        return default
```

**Propagação:** função `safeFloat()` incluída no TypeScript do Prompt 1 e documentada
como padrão obrigatório em `AGENT_INSTRUCTIONS.md`.

---

### Erro 4 — Process log insuficiente (feedback do revisor)

**Ferramenta:** humano identificou, Claude corrigiu  
**Quando:** após feedback do PR

**O que aconteceu:** o README.md submetido tinha process log narrativo — descrevia o que
aconteceu, mas não incluía nada que o revisor pudesse executar ou verificar
independentemente.

**Correção aplicada:**
1. `scoring_engine.py` — código Python completo e executável do scoring engine
2. `PROCESS_LOG.md` — este arquivo, com prompts reais, saídas reais e comandos verificáveis
3. README.md atualizado com referências a esses artefatos

---

## 9. O que só o humano fez

### Decisão de qual ferramenta usar em cada fase
A migração de ChatGPT para Claude não foi sugerida por nenhuma IA. Foi a percepção de que
o trabalho de desenvolvimento denso e interdependente precisava de outra ferramenta.

### Identificação do gap de resultados
Depois de testar o MVP no Lovable, percebi que faltava o dashboard de resultados. A IA
entregou exatamente o que foi especificado no PRD original — que não incluía essa visão.
A lacuna só foi visível usando a aplicação como usuário.

### Calibração dos pesos do scoring como tese de produto
D1+D2=50pts porque "deals bons esfriando" é o problema central. Essa decisão de produto
não pode vir da IA — vem da leitura do briefing e do entendimento do que a Head de RevOps
realmente precisava.

### Interpretação do padrão de ondas mensais
Claude calculou os números. A interpretação de que é um padrão estrutural de pipeline
(não ruído, não bug) — e a decisão de documentar isso preventivamente — foi humana.

### Copy rules como governança de produto
Definir que o dashboard do gestor nunca pode usar a palavra "monitoramento" é uma restrição
baseada em risco político real de produtos SaaS comerciais. A IA não tem esse contexto
sem que você forneça explicitamente.

### Validação cruzada em Lovable + Antigravity
A decisão de executar os dois prompts em duas plataformas diferentes foi metodológica —
para confirmar que a especificação era autossuficiente, não que uma plataforma específica
a interpretava bem.

### Resposta ao feedback do revisor
Identificar que o problema levantado pelo revisor era estrutural (artefatos insuficientes
+ process log narrativo) e não cosmético, e decidir criar `scoring_engine.py` e este
`PROCESS_LOG.md` como resposta correta.

---

## 10. Como auditar independentemente

### Verificar o scoring engine

```bash
# Clone/baixe os arquivos do repositório + CSVs do dataset
python scoring_engine.py --validate --csv-dir .
# → Verifica: win rate 63,2%, team averages, account vazio 16,2%, normalização GTXPro

python scoring_engine.py --rep "Darcel Schlecht"
# → Top 5 prioridades com score breakdown linha a linha

python scoring_engine.py --rep "Lajuana Vencill"
# → Rep com WR mais baixo (55%) — ver como o scoring lida com pipeline de baixa qualidade

python scoring_engine.py --all-reps
# → Tabela de top-1 prioridade para todos os 27 reps ativos
```

### Verificar a aplicação ao vivo

1. Acesse [pipelinecoachai.lovable.app](https://pipelinecoachai.lovable.app/)
2. Faça upload dos 5 CSVs na tela `/upload`
3. Selecione "Vendedor" → escolha "Darcel Schlecht"
4. Compare as prioridades exibidas com a saída do `scoring_engine.py --rep "Darcel Schlecht"`
5. Os scores devem ser idênticos (mesma fórmula, mesmos dados, mesma data de referência)

### Verificar os artefatos de processo

| Artefato | Evidencia |
|----------|-----------|
| `agent-context/SCORING_ENGINE.md` | Spec escrita antes do código — compare com `scoring_engine.py` |
| `agent-context/MVP_BUILDER_PROMPT.md` | Prompt que gerou a aplicação — 574 linhas de spec executável |
| `agent-context/DATA_SCHEMA.md` | Anomalias de dados documentadas antes de qualquer código |
| `agent-context/AGENT_INSTRUCTIONS.md` | Lista de erros proibidos — todos baseados em erros reais |
| `sales_dashboard.html` | Análise exploratória construída na Fase 4, antes do PRD |

### Verificar a ordem dos artefatos

Os timestamps dos arquivos confirmam a sequência:
1. `sales_dashboard.html` → análise antes do produto
2. `agent-context/*.md` → spec antes dos prompts para construtores
3. `agent-context/MVP_BUILDER_PROMPT.md` → Prompt 1
4. `agent-context/MVP_UPDATE_RESULTS_PROMPT.md` → Prompt 2 (após gap identificado)
5. `scoring_engine.py` → código auditável gerado como resposta ao feedback do PR
6. `PROCESS_LOG.md` → este arquivo, gerado como resposta ao feedback do PR

---

_Process log gerado em: 31 de março de 2026_  
_Atualizado com: scoring_engine.py e evidências concretas em resposta ao feedback do PR_
