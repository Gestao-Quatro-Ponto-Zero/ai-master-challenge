# Differentiation Rubric — Fase B

**Contrato do que vamos construir na Fase C.** Tudo aqui é o delta sobre o baseline-v3 (que já tem scoring multi-feature, Bayesian smoothing, percentile correto, action templated, account rollup, freshness renormalizada, KPIs, sort customizável).

---

## Reframe central

A baseline pergunta *"onde você quer focar?"*. A nossa **responde** *"foque aqui hoje."*

O app não é um pipeline browser com scores. É um **Morning Brief opinionado** com pipeline disponível como drilldown.

A inversão de hierarquia (brief primeiro, tabela secundário) é o move estrutural — sem ela, nenhuma feature abaixo entrega o que o brief promete.

---

## Os 7 diferenciadores

### 1. Dual-mode: Manager view + Rep view

Toggle no topo do app. **Mesma engine de scoring/judge**, dois renders diferentes:

- **Modo Manager** (default — persona da Head RevOps do brief): brief consolidado do time. *"Hoje 8 deals precisam de ação. Carlos: 3, Maria: 2, João: 3. Combined pipeline value $XYZ."* Leaderboard de rep × urgency.
- **Modo Rep**: seleciona vendedor → brief individual. *"Carlos, hoje você tem 3 must-acts:..."*

Disciplina de escopo: backend só roda 1 vez. Render é cosmético.

### 2. LLM-as-judge para action contextual (substitui template)

O baseline gera 232 variantes de `"Stalled {N}d — re-engage with new angle"`. Nossa versão **lê o deal** e gera ação contextual.

Implementação: para o top N (talvez 20–50 deals que passam o threshold de "must-act"), faz uma chamada Claude por deal (batched ou paralelo) passando: account, sector, produto, dias parado, valor, sinais de outros deals do account. Retorna ação específica.

Exemplo:
- Template: *"Stalled 3209d — re-engage with new angle"*
- LLM-judge: *"Kan-code tem 4 outros open deals em produtos complementares — proponha bundle multi-product nesta call. Histórico de Won na conta sugere ciclo de 60d, então acelera."*

Limita custo: só roda no top N do brief, não nos 2089. Cache local pra não pagar 2x.

### 3. Camada de coaching por vendedor

Painel novo só no Modo Rep: *"Onde você tem alavanca, onde você sangra"*. Baseado em dados históricos do CRM:
- Win rate por stage onde esse rep performa acima/abaixo da média
- Padrão temporal: rep fecha mais em deals <30d vs deals stuck
- Combinações product × sector onde rep tem alpha

Não invento dado — calculo dos 8800 históricos.

### 4. Reframe explícito do use case histórico

53% dos open deals têm 3000+ dias. O baseline finge que são leads vivos. Nós **dizemos a verdade** num banner no topo:

> *"Detectamos que 1.114 deals abertos têm engagement > 1 ano. Em produção real isso seria um problema de dado (deals não fechados no CRM). Para fins desse challenge, classificamos esses como 'pipeline ghost' e separamos. O brief de hoje considera apenas os 975 deals com sinais reais de atividade."*

Honesto. Mostra judgment. Diferencia.

### 5. Composabilidade com Morning-Brief (engine hook)

Export JSON estruturado do brief diário do rep — não só CSV. Schema documentado. README explicita: *"Output formato compatível com qualquer skill agentic downstream (ex: morning brief no WhatsApp do rep)."*

Conecta ao `case-g4-ai-master.md` sem citá-lo: avaliador que viu o caso reconhece a engine, avaliador que não viu lê como "boa engenharia composável".

### 6. Diagnóstico de qualidade de dado

Painel/expander no Modo Manager mostrando:
- 1.425 deals (16%) sem account match → `sector`/`revenue` NaN
- 1.114 deals (53% do open) sem atividade recente
- N reps com pipeline severamente desbalanceado vs média do time

Não é só "score 50 neutro" como na baseline. É *"esses dados estão quebrados, aqui está o quanto."*

### 7. README + Process Log com judgment

Não é checklist de features. É:
- **Por que estas escolhas** e não outras (incluindo o que NÃO automatizei — ex: por que não treinei XGBoost)
- **3 calls difíceis** durante a construção (com decisão final e o porquê)
- **2 momentos onde Claude sugeriu algo que recusei** (o anti-baseline em ação)
- **Limitations honestas**: o que esse app não faz, qual viés do dataset, o que mudaria com dados de produção
- **Composabilidade explícita**: como o output alimenta um sistema maior

---

## O que NÃO vamos fazer (cortes conscientes)

| Não-feature | Por quê |
|---|---|
| ML model (XGBoost, churn predictor) | Brief literal diz "regras + heurísticas, bem apresentado, vale mais". E não cabe em 3h. |
| Visual elaborado / dashboard charts | Visualizações comem tempo, não decisão. Brief é texto-first. |
| Auth / multi-user state | Out of scope. |
| Persistência de feedback do rep | "Mark as acted" é fácil mas adia. Future work. |
| LLM-judge em todos os 2089 deals | Caro, lento, não compõe brief opinionado de 3-5 itens. Top N apenas. |

---

## Time-box rígido por feature (3h total Fase C)

| Feature | Tempo |
|---|---|
| Reframe + dual-mode skeleton (refactor app.py + scoring engine reuse) | 45 min |
| LLM-as-judge para top N actions | 45 min |
| Coaching layer por rep | 30 min |
| Reframe banner + pipeline ghost split | 15 min |
| JSON export composável | 15 min |
| Data quality panel (Manager mode) | 15 min |
| Polish + smoke test | 15 min |

Se LLM-judge passar de 1h calibrando prompt → corto e uso template + sinais explícitos (account_open_deals, sector). É a feature mais arriscada em time.

---

## Verificação pré-PR

1. Modo Manager renderiza brief consolidado em <3s
2. Modo Rep renderiza brief individual em <3s para qualquer dos 35 reps
3. Actions do top 5 são **claramente contextuais** (não 5 variantes da mesma string)
4. README abre com a tese da diferenciada — não com setup
5. Process log tem 3 calls difíceis nomeadas (não genérico "iterei o prompt")
6. Side-by-side baseline-v3 vs submission: delta visível em 30 segundos
