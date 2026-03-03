# Process Log — Como Usei IA para Construir o LeadScore AI

## Resumo

Construí uma ferramenta funcional de priorização de deals para vendedores usando **Gemini 2.5 Pro + Antigravity IDE** como par de programação. O processo todo levou **~1h30min** desde o primeiro prompt até o build final funcionando.

A IA foi usada como **co-piloto**, não como piloto. Cada decisão de negócio, design de algoritmo e julgamento crítico foi meu — a IA acelerou a execução e me ajudou a iterar rapidamente.

---

## Timeline Completa

| Hora | Fase | O que aconteceu |
|------|------|-----------------|
| 23:21 | Entendimento | Primeiro prompt: "Bora trabalhar, me explique tudo sobre esse challenge" |
| 23:21–23:27 | Entendimento | IA leu todos os arquivos do repositório e resumiu o challenge completo |
| 23:27 | Decisão | Escolhi o Challenge 003 — Lead Scorer (combina com meu perfil de dev frontend) |
| 23:27–23:45 | Dados | Download do dataset Kaggle (enfrentamos problemas de autenticação e PATH) |
| 23:45–23:55 | Análise | Script Python exploratório analisou todas as 4 tabelas CSV |
| 23:55 | Insight-chave | Descoberta: Deals perdidos morrem em 14 dias (mediana), enquanto ganhos demoram 57 dias |
| 23:55–23:59 | Planejamento | Criei o plano de implementação: Stack, scoring, UI, estrutura |
| 23:59–00:01 | Revisão crítica | **Submeti o plano para outra IA (Gemini) como "CTO"** — recebi 4 críticas fundamentais |
| 00:01–00:05 | Replanning | Incorporei os 4 pontos: EV scoring, time decay, cold start, UX de trincheira |
| 00:05–00:14 | Setup | Inicializei Vite + React, instalei dependências, copiei os CSV |
| 00:14–00:20 | Engine | Construí o scoring engine com 6 fatores e 2 camadas (Win Prob → Priority) |
| 00:20–00:30 | UI | Construí todos os componentes: Sidebar, Header, Dashboard, Pipeline Table, Agent Leaderboard |
| 00:30–00:35 | Bug fixing | Scores estavam todos baixos (~30 avg) — GTK 500 esmagava a normalização |
| 00:35–00:38 | Fix | Implementei normalização log-scale — scores corrigidos (60-73 nos top deals) |
| 00:38–00:42 | Build | `npm run build` passou limpo, verificação final no browser |
| 00:42–00:50 | Docs | Process log, README, documentação |

**Tempo total: ~1h30min**

---

## Ferramentas Usadas

| Ferramenta | Para que usei | Impacto |
|------------|---------------|---------|
| **Gemini 2.5 Pro (Antigravity IDE)** | Par de programação principal — análise, código, testes, debug | Aceleraram a execução 5-10x |
| **Gemini (chat separado)** | Revisão crítica do plano como "CTO do G4" | Encontrou 4 buracos fundamentais no scoring |
| **Python + Pandas** | Exploração de dados | Script analisou as 5 tabelas em segundos |
| **Kaggle CLI** | Download dos dados | Precisei contornar problemas de PATH e autenticação |
| **Browser (Chromium via Antigravity)** | Testes visuais automatizados | Screenshots e gravações das 3 views |

---

## Workflow Detalhado

### Fase 1: Entendimento do Problema (23:21–23:55)

**O que fiz:** Pedi para a IA ler todo o repositório do challenge, entender as regras, os critérios de avaliação, e me explicar tudo.

**Meu julgamento:** Escolhi o Challenge 003 porque combina com meu perfil (forte em frontend/React). A IA sugeriu o mesmo, mas a decisão foi minha baseada na minha experiência com dashboards financeiros.

**Problemas com a IA:** O download do Kaggle deu vários problemas:
1. `kaggle` CLI não estava no PATH → Solução: `python -m kaggle` 
2. Kaggle v2 não suporta `__main__` → Solução: API Python diretamente
3. Autenticação Kaggle via API Token → Precisei criar conta manualmente

**Insight que a IA encontrou (e eu validei):** A anomalia temporal — deals perdidos morrem em 14 dias (mediana) vs. ganhos que demoram 57 dias. Isso virou o pilar do algoritmo de Pipeline Velocity.

### Fase 2: Análise Crítica via Outra IA (23:59–00:05)

**Decisão minha:** Antes de sair codando, submeti o plano completo para o Gemini (chat separado) pedindo que fizesse o papel de "CTO do G4 avaliando a análise". Isso foi estratégico — queria encontrar buracos no meu raciocínio antes de investir tempo codando.

**Os 4 problemas que o Gemini encontrou:**

1. **Probabilidade ≠ Valor Esperado** — Um deal de $55 com 90% de chance não vale mais que um de $4.800 com 40%. O score precisava ser Expected Value, não apenas probabilidade.

2. **Time Decay dinâmico** — A mediana de 57 dias é um número, mas o scoring precisa ser uma curva: deals que sobrevivem a "zona de morte" (~14d) ganham pontos, deals que estagnam (~100d+) sangram pontos.

3. **Cold Start (16% deals sem account)** — Se o scoring depende de dados da conta (setor, tamanho), 16% do pipeline fica sem score. Precisava de fallback.

4. **UX de trincheira** — A tabela precisa ser paginada, com todos os deals, não um "top 5" gerencial.

**Minha avaliação:** Concordei com os 4 pontos e incorporei todos. O ponto 1 (EV) foi o mais impactante — mudou a filosofia do scoring de "chance de fechar" para "onde o vendedor deve investir tempo".

### Fase 3: Construção (00:05–00:42)

**Como usei a IA para codar:**

A IA funcionou como **par de programação** — eu definia a arquitetura e as regras de negócio, e ela gerava o código. Para cada módulo eu:

1. Expliquei o que queria (em linguagem de negócio)
2. A IA gerou o código
3. Eu revisava, ajustava, e pedia iterações

**Módulos construídos:**
- `dataLoader.js` — Parse CSV + merge das 4 tabelas + cálculo de dias no pipeline
- `scoringEngine.js` — 6 fatores ponderados + curva de Pipeline Velocity + cold start
- `analytics.js` — KPIs, distribuição de scores, leaderboard
- `useData.js` — Hook React com filters, memoização, loading state
- `index.css` — Design system dark theme completo
- 8 componentes React (Sidebar, Header, Dashboard, KpiCards, ScoreDistribution, PipelineTable, ScoreBreakdown, AgentLeaderboard)

**O maior bug encontrado:**

Após o primeiro build, todos os scores estavam entre 0-59 (avg = 30). A maioria dos deals era "Cold". O problema: a normalização de valor usava **escala linear**, e o GTK 500 ($26.768) fazia com que o MG Special ($55) tivesse valor normalizado de 0.002 (praticamente zero).

A correção: mudei para **normalização logarítmica**:
- $55 → 0.45 (antes: 0.002)
- $550 → 0.65 (antes: 0.02)
- $5.482 → 0.87 (antes: 0.20)
- $26.768 → 1.0

Isso distribuiu os scores corretamente: top deals agora são 60-73 (Warm), maioria 40-59 (Cool), e os low-priority 0-39 (Cold).

---

## Onde a IA Errou e Como Corrigi

| O que a IA fez | O problema | Como corrigi |
|----------------|-----------|-------------|
| Normalização linear de preço | GTK 500 ($27K) esmagava todos os outros produtos | Mudei para log-scale normalization |
| `python -m kaggle` | Kaggle v2 não tem `__main__` | Usei `from kaggle import api` diretamente |
| Criou projeto no diretório errado | Vite criou `lead-scorer/` na raiz em vez de `submissions/` | Movi manualmente para a pasta correta |
| Fragment sem key no React | Warning no console | Troquei `<>` por `<Fragment key={...}>` |
| Scoring `winProbability * 0.6 + winProbability * valueNorm * 0.4` | Com valueNorm ≈ 0.002 para MG Special, score ficava = 60% da probabilidade | Rebalancei para usar log-scale e blend 55/45 |

---

## O Que Eu Adicionei que a IA Sozinha Não Faria

1. **A decisão de submeter o plano para revisão como "CTO"** — Isso nunca viria espontaneamente. Foi uma metacognição minha usar uma IA para auditar outra IA.

2. **A escolha do EV como score principal** — A IA original fez um scoring de probabilidade pura. A mudança para Expected Value foi uma decisão de negócio que requer entender como vendedores pensam.

3. **A curva de Pipeline Velocity** — Eu validei os 14d/57d olhando os dados antes de transformar em algoritmo. A IA gerou o insight, mas eu confirmei que fazia sentido no contexto de vendas B2B.

4. **UX de trincheira** — A decisão de fazer a tabela completa como view padrão (não dashboard gerencial) veio do meu entendimento de como operações de vendas funcionam no dia-a-dia.

5. **O fix de log-scale** — Quando vi que os scores estavam todos baixos, identifiquei que era problema de normalização, não do algoritmo base. A IA não teria detectado isso sozinha.

---

## Evidências

### Screenshots

| # | Descrição | Arquivo |
|---|-----------|---------|
| 1 | Pipeline com deals priorizados | `screenshots/01-pipeline-view.png` |
| 2 | Dashboard com KPIs e charts | `screenshots/02-overview-dashboard.png` |
| 3 | Agent Leaderboard | `screenshots/03-agent-leaderboard.png` |
| 4 | Score Breakdown + Cold Start | `screenshots/04-score-breakdown-cold-start.png` |

### Recordings (Browser sessions automáticas)

| # | Descrição | Arquivo |
|---|-----------|---------|
| 5 | Teste completo das 3 views | `screenshots/05-recording-full-app-test.webp` |
| 6 | Verificação pós-fix dos scores | `screenshots/06-recording-score-fix-verification.webp` |

### Git History

O histórico de commits mostra a evolução do código com AI-assisted development. Cada arquivo foi gerado e iterado via par de programação com IA.

---

*Process log gerado em: 03/03/2026, 00:50*
*Tempo total do challenge: ~1h30min (23:21 → 00:50)*
