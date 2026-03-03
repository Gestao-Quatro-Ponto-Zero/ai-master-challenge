# Process Log — Challenge 001: Diagnóstico de Churn
## Marcelo Adriano Nunes Filho | AI Master Challenge G4

---

## Ferramentas Utilizadas

| Ferramenta | Uso Específico |
|------------|---------------|
| Claude Code (Opus 4.6) | Análise exploratória, geração de dashboard, código Python, cruzamento de dados, construção React |
| VS Code | IDE principal, revisão de código e outputs |
| Python + Pandas | Processamento e análise dos 5 CSVs (33.100 registros) |
| Plotly.js | Gráficos interativos no dashboard HTML (v1-v3) |
| Lovable | Hospedagem e deploy do dashboard React interativo final |
| Recharts | Biblioteca de gráficos no dashboard React (10 seções) |
| Git/GitHub | Versionamento, evolução do código (5 commits), submissão via PR |

---

## Timeline do Processo (conversa literal)

### Fase 1: Reconhecimento

**Prompt Marcelo:** "Estou querendo participar desse desafio [...] abra os links, baixe os gits, baixe os dados, faça uma explicação inicial do que falta eu buscar de informações para depois discutirmos o projeto"

**Ações da IA:**
- Fez WebFetch nos links (README challenge, Kaggle dataset, CONTRIBUTING.md)
- Clonou repo `ai-master-challenge` via git
- Instalou Kaggle CLI (`pip install kaggle`)
- Baixou e descompactou os 5 CSVs do Kaggle (~2MB)
- Explorou headers e contagens básicas com Python

**Descobertas iniciais:**
- 500 contas, 110 marcadas churn_flag=True (22%)
- 6 reason_codes distribuídos quase uniformemente (~90-114 cada) — SUSPEITO
- 5.000 subscriptions, 25.000 usage, 2.000 tickets, 600 churn events
- 600 eventos > 110 contas flagged = múltiplos churns por conta

**Resposta da IA:** Resumo completo do desafio + tabela de dados + 5 áreas para investigar + sugestão de próximos passos

---

### Fase 2: Dashboard v1

**Prompt Marcelo:** "comece criando um dashboard em um html local para eu poder entender mais os dados, tabelas, gráficos. aqui no claude code no VS tenho como compartilhar todo o histórico da conversa? se não tiver, crie um notepad para fazer todo o nosso histórico e servir como documentação, também vou tirar alguns prints para documentar"

**Ações da IA:**
- Criou estrutura de pastas `submissions/marcelo-nunes/` (solution, process-log, docs)
- Criou PROCESS_LOG.md como registro do histórico
- Gerou script Python `generate_dashboard.py` (~350 linhas)
- Dashboard v1: 9 abas (Overview, Segmentação, Revenue, Usage, Suporte, Timeline, Lifecycle, Feedback, Dados Brutos)
- Usou Plotly.js para gráficos interativos, CSS dark theme
- Encontrou e corrigiu 2 bugs de merge (colunas duplicadas plan_tier e churn_flag)

**Bugs corrigidos:**
1. `rev_impact.groupby('plan_tier')` falhava — colisão de nome com subscriptions. Fix: rename para `acct_plan`
2. `subs_merged.groupby(['billing_frequency', 'churn_flag'])` falhava — mesma colisão. Fix: rename para `acct_churned`

---

### Fase 3: Questionamento Crítico + Dashboard v2

**Prompt Marcelo:** "antes de começar quero entender melhor os churns. temos 110 de 500, mas temos muito mais se considerarmos segmentações (muitos dados duplicados). faça outro filtro para poder analisar mais unificado. o dashboard não mostra muita coisa sobre satisfação. tem 61 reativações que deram churns, essas estão repetindo? (churn 2x?)"

**Ações da IA (investigação profunda):**
Rodou 3 queries Python em paralelo para investigar:

**Achado #1 — Churn events duplicados:**
- 600 eventos para 352 contas ÚNICAS (não 110!)
- 177 contas com 1 evento, 116 com 2, 47 com 3, 10 com 4, 2 com 5
- 175 contas multi-churn (porta giratória)

**Achado #2 — churn_flag = estado ATUAL, não histórico:**
- churn_flag=True: 110 (atualmente inativos)
- Contas COM evento de churn: 352
- 277 contas churnaram mas VOLTARAM (flag=False, com eventos)
- 110 contas inativas atuais (flag=True): 75 com eventos documentados + 35 sem evento (gap de dados)

**Achado #3 — Satisfação é INÚTIL como indicador:**
- Scores só existem em 3, 4 e 5. NENHUM score 1 ou 2 em 2000 tickets
- Médias idênticas entre churned (4.01) e retained (3.97)
- Idênticas entre prioridades (3.93-4.02), escalados/não-escalados
- 41% sem resposta (null) — viés de não-resposta
- Conclusão: instrumento de satisfação QUEBRADO, não captura insatisfação

**Visão unificada criada:**
| Segmento | Contas | % |
|----------|--------|---|
| Nunca Churnou | 113 | 23% |
| Porta Giratória (churnaram, voltaram) | 277 | 55% |
| Inativos Atuais (75 com evento + 35 sem) | 110 | 22% |

**Dashboard v2 gerado** com as correções acima: 9 abas reconstruídas com 4 segmentos, aba Multi-Churn nova, insight boxes explicando satisfação quebrada.

---

### Fase 4: Validação e Aprofundamento

**Prompt Marcelo:** "para garantir, vc está com as 5 tabelas? na parte de dados brutos não consigo ver todas as tabelas nem completas. com tanto churn e volta, tem como demonstrar claramente para o CEO: o time de produto diz que o uso da plataforma cresceu? está atualizando o process log? (o ideal era ser o mais literal possível entre meus prompts e suas respostas finais)"

**Ações da IA:**
- Atualizou PROCESS_LOG com conversa literal
- Melhorou aba de dados brutos: agora mostra as 5 tabelas com 50 registros cada (scroll)
- Criou aba "Pergunta do CEO" com 4 gráficos provando que uso NÃO cresceu
- Investigou: uso total ~10.500/mês flat por 24 meses, uso por conta ~25 flat, contas ativas ~420 flat

**Achado:** O uso da plataforma NÃO cresceu. ~20 novas contas/mês são anuladas pelo churn. O time de Produto pode estar olhando métricas cumulativas.

---

### Fase 5: Matrizes de Análise + Diagnóstico Final

**Prompt Marcelo:** "vamos focar nas questões principais do projeto [...] além de provar que satisfação está sendo medida errada, existem outras matrizes que podemos usar para tirar insights, na mesma linha que existe matriz RFM para um ecommerce de produto, veja outras que se aplicam nesse caso"

**Pesquisa da IA:**
- WebSearch: frameworks SaaS churn analysis 2025 (Customer Health Score, engagement scoring, value-risk)
- Fontes: EverAfter, Vitally, UserPilot, GrowthWithGary

**Matrizes construídas:**

1. **Customer Health Score (0-100)**: 5 componentes (uso 25%, features 20%, recência 25%, erros 15%, tickets 15%)
   - RESULTADO PARADOXAL: Perdido Permanente (64.7) > Nunca Churnou (61.9) > Porta Giratória (63.6)
   - Health score NÃO prediz churn neste dataset

2. **Matriz Valor x Risco (3x3)**: MRR vs Health Score
   - ACHADO CRÍTICO: High Value + Low Risk = 18 perdidos (o MAIOR número). Empresa perde melhores clientes sem perceber

3. **Engagement Depth Matrix**: Frequência vs Amplitude de features
   - Low Freq + Narrow: 22 perdidos (esperado)
   - High Freq + Broad: 21 perdidos (INESPERADO — usam muito e saem mesmo assim)

4. **Support Burden**: Tickets/conta, escalações, prioridades
   - IDÊNTICO entre todos os segmentos. Suporte não diferencia churn

**Conclusão principal:** O churn é ESTRUTURAL (modelo de negócio), não comportamental. Métricas tradicionais de CS não funcionam.

**Diagnóstico Final criado** respondendo as 3 perguntas do CEO:
1. Causa: Problema estrutural "Porta Giratória" — 55% das contas já cancelaram e voltaram
2. Segmentos em risco: DevTools Enterprise (37.1%), canal "events" (30.2%), High Value + "Low Risk"
3. Recomendações: 6 ações priorizadas (NPS, programa Save, investigar proposta de valor, etc)

---

### Fase 6: Revenue-Weighted + Rigor Estatístico + Estratégias

**Prompt Marcelo:** "precisamos ainda avaliar a questão de perder contas de maior valor/mês. também não adianta só falarmos que eventos não funcionam ou Alemanha é preocupante, sendo que por exemplo Alemanha tem uma base pequena de clientes. existe como propormos algo também em relação a um desconto maior para quem mudar para o plano anual, mesmo perdendo um pouco no valor anual, teríamos menos churn por o cliente já ter pago o anual. outras ideias assim pode sugerir"

**Nota:** A IA compactou o contexto e perdeu este prompt. Tive que repetir as mesmas perguntas na mensagem seguinte.

**Ações da IA (3 análises em paralelo):**

**Achado #1 — Enterprise = 73% do MRR perdido:**
- 25 contas Enterprise perdidas = $122.385/mês ($1.47M/ano)
- Top 10 contas perdidas = $97.361/mês (58% do total perdido, apenas 10 contas)
- Basic perde 28 contas mas só $12.863/mês. Enterprise perde 25 contas mas $122.385/mês
- Conclusão: foco deve ser nas Enterprise, não na quantidade

**Achado #2 — Rigor estatístico derruba vários "insights":**
- DevTools: p=0.004 — ÚNICO segmento estatisticamente significativo (24.8% vs 15% documentado)
- Events: p=0.059 — marginal, vale investigar mas com cautela
- Alemanha (n=25), França (n=22), Canadá (n=23): TODOS com amostra insuficiente para conclusão
- Países, planos: NENHUM significativo — churn é uniforme nesses cortes
- IA ERROU antes ao listar Alemanha como "segmento em risco" sem mencionar n=25

**Achado #3 — Mensal vs Anual (contra-intuitivo):**
- Mensal: 28 perdidos (12.7%), MRR perdido $94.030 (17.0% do MRR mensal)
- Anual: 47 perdidos (16.8%), MRR perdido $72.970 (11.0% do MRR anual)
- Mensal perde MENOS contas mas de MAIOR valor ($3.358 médio vs $1.553)
- Auto-renew: idêntico (14.8% vs 15.7%) — não diferencia

**Estratégias construídas com ROI:**
1. Enterprise Save Program (ROI 7x): 1 CSM ($8k/mês), salvar 5 de 25 = $56.914/mês recuperado
2. Desconto Anual 15%: Net ~$67.700/ano para lock-in de contas mensais de alto valor
3. DevTools PMF Audit: Se reduzir churn de 24.8% a baseline 15% = ~$274k/ano
4. Programa 90-Day Success: Reduzir re-churn da porta giratória em 20% = $80.900/mês protegido
5. Qualificar canal Events: Custo baixo, alterar pitch e onboarding

**Dashboard v3 gerado** (164KB): Nova aba "Estratégia & ROI" com tabela de significância, top 10 perdidos, simulação de impacto. Diagnóstico Final atualizado com ROI e p-valores.

---

### Fase 7: Migração para Dashboard Interativo Lovable

**Prompt Marcelo:** "como iríamos subir eles para apresentação do CEO? quer fazer um lovable para publicarmos? pode dar outras sugestões se achar melhor. se for fazer no lovable lembre de gerar todos os prompts e eu subo no lovable o primeiro e depois coloco no meu github para terminar de editar"

**Decisão de migrar**: O dashboard HTML (Plotly.js) era funcional mas limitado em UX. Migração para Lovable (React + TypeScript + Recharts + Shadcn UI + Tailwind CSS) para criar experiência interativa publicável.

**Ações:**
- A IA gerou prompt estruturado completo (LOVABLE_PROMPT.md, 263 linhas)
- Criei o projeto no Lovable e colei o prompt
- Conectei ao GitHub (marcelinhonunes/ravenstack-churn-insights)
- A IA fez push via Git com melhorias iterativas

**Prompt Marcelo:** "pode fazer ajustes. lembrar que vc consegue fazer push sozinho completo"

**Melhorias na 2ª iteração (via Git push):**
- Adicionou seção **Porta Giratória** (histograma multi-churn, distribuição de motivos, prova que 82% mudam motivo)
- Adicionou tab **Heatmap** na Segmentação (matriz Plan x Industry, DevTools+Enterprise = 31.4%)
- Melhorou todos os gráficos: error bars, tooltips consistentes, cores semânticas
- Utilizou TODOS os 20 datasets exportados (eliminando dados órfãos)
- Melhorou Diagnóstico Final: números-chave inline, "Bottom Line para o CEO", cruzamento das 5 tabelas

**Commits:**
1. `656bda9` — Implement dashboard UI (base Lovable)
2. `082d633` — Major dashboard improvements: new sections, better insights, UX enhancements

---

### Fase 8: Risk Watchlist — Automação para CS

**Motivação:** O challenge pede como diferencial "uma automação que o time de CS poderia usar amanhã". Nenhuma seção até aqui era diretamente acionável como FERRAMENTA.

**Ações da IA (análise Python dos 5 CSVs):**
- Leu os 5 CSVs originais e cruzou: accounts + subscriptions + churn_events + support_tickets + feature_usage
- Filtrou 390 contas ATIVAS (não perdidas permanentemente)
- Calculou score de risco ponderado para cada conta:
  - Churn history: 25 pontos por evento de churn anterior (maior peso — melhor preditor encontrado)
  - Indústria DevTools: +20 pontos (único segmento com p<0.01)
  - Plano Enterprise: +15 pontos (73% do MRR perdido)
  - Billing mensal: +10 pontos (maior ticket médio perdido)
  - MRR alto (>$2k): +10 pontos (maior impacto financeiro)
  - Escalações: +5 pontos por escalação
  - Conta silenciosa (sem resposta satisfação): +5 pontos

**Resultados:**
- 110 contas com score 61+ (risco crítico)
- Top 20 contas em risco com MRR combinado de $62k+/mês
- Contas extremas (score 130+): Company_272, Company_116, Company_382

**Componente RiskWatchlist.tsx criado:**
- KPIs de risco (contas ativas, com histórico, crítico+, MRR em risco)
- Gráfico de distribuição de risco (barras coloridas por faixa)
- Tabela Top 20 com badges EXTREME/CRITICAL/HIGH
- Metodologia transparente (pesos e fontes)
- Playbook CS: o que fazer amanhã, esta semana, este mês
- Nota metodológica: "apenas fatores comprovados, nenhum feeling"

**Commit:** `0bbac3c` — Add Churn Risk Watchlist: cross-table risk scoring for 20 highest-risk active accounts

---

### Fase 9: Polish Final — Tema, Português, UX

**Prompt Marcelo:** "faça uma correção geral em erros de português, também faça uma versão light e dark, veja se tem mais algumas coisas de UX que podem melhorar, ainda acho que a explicação ficou muito longa, poderia ter um resumo inicial e depois toda a apresentação"

**Ações da IA (4 frentes em paralelo):**

**1. Tema Light/Dark:**
- Criou `src/hooks/use-theme.tsx` (ThemeProvider com localStorage, toggle)
- Criou `src/lib/chartTheme.ts` (cores de gráficos por tema — CSS vars não funcionam em SVG inline)
- Reescreveu `src/index.css` com CSS custom properties para light e dark
- Adicionou botão Sun/Moon no header
- Todas as 9 seções atualizadas com `useTheme()` + `chartTheme[theme]`

**2. Correções de português (~73 erros):**
- Agent de auditoria encontrou acentos/cedilhas faltando em todos os componentes
- Corrigidos: "Giratoria" → "Giratória", "distribuicao" → "distribuição", "Satisfacao" → "Satisfação", etc.
- Aplicado em todos os 9 componentes de seção + sidebar + index

**3. TL;DR para CEO:**
- Adicionou hero section no topo com 3 métricas-chave ($2M/ano perdido, 55% porta giratória, ~$1M recuperável)
- 3 bullets de 30 segundos: causa raiz, métricas cegas, ação imediata
- Sidebar atualizada com "TL;DR" como primeira entrada

**4. UX improvements:**
- Animação fadeInUp em cada seção (scroll reveal)
- Scrollbar adaptativa por tema
- Font tabular-nums padronizado em todos os números
- Padronização de font-size nos gráficos (10px XAxis, 11px YAxis)
- Painel "Cruzamento das 5 Tabelas — Rastreabilidade" no Diagnóstico Final

**Commits:** `5852308` — Polish: standardize chart font sizes + `a389e37` — Light/dark theme, Portuguese fixes, TL;DR summary, UX polish

**Dashboard final: 10 seções + TL;DR hero**, tema claro/escuro, 45 screenshots de evidência.

---

## Onde a IA Errou (e como corrigi)

| # | O que a IA fez | Problema | Correção |
|---|---------------|----------|----------|
| 1 | Dashboard v1 tratou churn_flag como binário (churned/retained) | Ignorava 277 contas que churnaram e voltaram, inflava taxa de churn | Questionei: "muitos dados duplicados" e "61 reativações repetem?" — levou à descoberta dos 4 segmentos |
| 2 | Merge de DataFrames sem tratar colunas homônimas | KeyError em plan_tier e churn_flag | A IA corrigiu com rename antes do merge |
| 3 | Satisfação mostrada como métrica útil (4.01 vs 3.97) | Não percebeu que só existem scores 3-5 (instrumento quebrado) | Questionei: "não mostra muita coisa sobre satisfação" — a IA investigou e descobriu ausência total de scores 1-2 |
| 4 | Diagnóstico listou "Alemanha 32% churn" como segmento em risco | Alemanha tem n=25, intervalo de confiança [11.5%-43.4%] — qualquer conclusão é inválida com essa amostra | Apontei: "Alemanha tem base pequena de clientes" — a IA adicionou teste chi-quadrado e IC 95% para todas as segmentações |
| 5 | A IA compactou o contexto e perdeu meu prompt | Tive que repetir as mesmas perguntas sobre revenue e desconto anual | Apontei: "você compactou e perdeu minha pergunta anterior" — repeti o prompt |
| 6 | Agent de auditoria reportou HEATMAP como "dados não utilizados" | HEATMAP é usado na Segmentation.tsx dentro de .find(). Agent não detectou o uso | Verificação manual do código — dado estava corretamente utilizado |
| 7 | Dashboard com ~73 erros de português (acentos/cedilhas) | Todos os textos sem acentuação correta | Pedi correção geral — agent de auditoria encontrou e a IA corrigiu em todos os 9 componentes |

---

## Valor Agregado Humano (além do que a IA produz sozinha)

1. **Questionamento dos dados**: A IA aceitou os 110 contas com churn_flag=True e seguiu em frente. Eu olhei os números e percebi que não batiam — forcei a investigação que revelou a Porta Giratória, o achado central do diagnóstico.

2. **Ceticismo sobre satisfação**: A IA mostrou satisfação como métrica válida. Eu comentei que "não mostra muita coisa" — a investigação revelou o instrumento quebrado (zero scores 1-2).

3. **Rigor estatístico**: A IA listava segmentos "em risco" sem validar. Apontei que Alemanha tem poucos clientes — isso levou aos testes estatísticos que derrubaram várias conclusões iniciais.

4. **Ideia do desconto anual**: Sugeri oferecer desconto para migração de mensal para anual como mecanismo de lock-in. A IA desenvolveu a simulação a partir da minha sugestão.

5. **Pensamento de CEO**: Pedi para "demonstrar claramente para o CEO se o uso cresceu" — exatamente o que o desafio pede.

6. **Sugestão de matrizes tipo RFM**: Perguntei se existiam frameworks tipo RFM para SaaS — levou à descoberta de que health scores não funcionam neste caso.

7. **Decisão de usar Lovable**: Escolhi migrar de HTML para dashboard React interativo com deploy público.

8. **Pedido de síntese**: Reclamei que "a explicação ficou muito longa" — levou ao TL;DR de 30 segundos no topo.

---

## Evidências

- **45 screenshots** salvos em: `process-log/screenshots/` (capturadas durante as 9 fases)
- Este log: atualizado a cada iteração (9 fases documentadas)
- **Git history** (5 commits mostrando evolução):
  1. `656bda9` — Dashboard base Lovable
  2. `082d633` — Seções adicionais + insights aprimorados
  3. `0bbac3c` — Risk Watchlist (automação CS)
  4. `5852308` — Padronização visual + rastreabilidade 5 tabelas
  5. `a389e37` — Tema light/dark + português + TL;DR + UX
- **Dashboard publicado**: [g4-ai-challenge-churn.lovable.app](https://g4-ai-challenge-churn.lovable.app)
- **Código-fonte**: [github.com/marcelinhonunes/ravenstack-churn-insights](https://github.com/marcelinhonunes/ravenstack-churn-insights)
- Dashboard HTML v1 → v2 → v3: evolução mostra iteração humano-IA
- Scripts Python de análise: `solution/` (generate_dashboard.py, build_matrices.py, export_lovable_data.py)
- Dados pré-computados: `solution/master_account_metrics.csv` (158KB, 500 contas x 30+ métricas)

---

## Resumo de Métricas do Processo

| Métrica | Valor |
|---------|-------|
| Fases de iteração | 9 |
| Registros processados | 33.100 (5 tabelas) |
| Erros da IA corrigidos | 7 |
| Contribuições humanas críticas | 8 |
| Screenshots de evidência | 45 |
| Commits Git | 5 |
| Seções do dashboard | 10 + TL;DR |
| Estratégias com ROI | 5 |
| Contas no Risk Watchlist | 20 (de 390 ativas) |
