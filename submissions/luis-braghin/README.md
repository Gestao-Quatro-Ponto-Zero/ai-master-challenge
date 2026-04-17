# Submission — Luis Braghin — Challenge 003

## Sobre mim

- **Nome:** Luis Braghin
- **LinkedIn:** [linkedin.com/in/luis-braghin-53916a1b5](https://www.linkedin.com/in/luis-braghin-53916a1b5/)
- **Challenge escolhido:** 003 — Lead Scorer (Vendas / RevOps)

---

## Executive Summary

Construí o **G4 Deal Intelligence**, uma plataforma web que analisa o pipeline de 2.089 deals ativos e prioriza oportunidades para vendedores usando um scoring multidimensional baseado em Esperança Matemática. O modelo usa 5 dimensões para deals Engaging (agent-product affinity, deal value, velocity, account quality, product-sector fit) e 5 para Prospecting (opportunity window substitui velocity). O principal achado é que o pipeline está genuinamente inflado - 84% ultrapassaram o tempo máximo histórico de fechamento (138 dias) — e que a especialização de vendedores por produto é o preditor mais forte (spread de até 73pp entre melhor e pior vendedor para o mesmo produto). Recomendação: focar nos top 20% dos deals por score, limpar deals >138 dias (ou realizar um último sprint nestes leads antes de limpar), e implementar mentoria cruzada entre vendedores baseada em afinidade produto.

**Deploy:** [g4-lead-scorer.vercel.app](https://g4-lead-scorer.vercel.app/)

---

## Solução

### Abordagem

1. **Análise exploratória dos dados** — Carreguei os 4 CSVs e fiz análise completa com Claude Chat. Descobri pipeline inflado, curva bimodal de velocity, sazonalidade trimestral de 30pp, e especialização real de vendedores. Forneci um pouco mais contexto ao Claude sobre área comercial, aceitei alguns pressupostos e rejeitei outros.
2. **Auditoria independente** — Pedi ao Claude Code para analisar os dados de forma independente (sem ver minha conclusão anterior). Debatemos divergências e tomamos decisões fundamentadas (ex: Deal Value no score — eu divergi da IA e prevaleci com base em teoria econômica)
3. **Modelagem de scoring** — Defini pesos por dimensão com justificativa estatística, curva bimodal de velocity validada por produto, blend para amostras pequenas, 5 faixas (HOT/WARM/COOL/COLD/DEAD). Evolução v2 → v3 com redistribuição de pesos e remoção de seasonality
4. **Build do frontend** — Dashboard interativo com React 18 + TypeScript + Vite + shadcn/ui + Recharts. Visões para vendedor, manager e executivo. Scoring pré-calculado em JSON
5. **Refinamento visual** — Migrei de dark mode (quando tentei pela primeira vez via Claude Code, porém resultado não-satisfatório) para light mode (decisão consciente: ferramentas B2B são usadas com projetor, em reuniões, etc.). Design system com HSL tokens, Inter + JetBrains Mono

### Stack Técnica

| Tecnologia | Uso |
|-----------|-----|
| React 18 + TypeScript | Framework UI |
| Vite 5 | Build tool |
| Tailwind CSS 3 + shadcn/ui | Design system (54+ componentes) |
| Recharts | Gráficos (bar, pie, scatter, line) |
| TanStack Query | Gerenciamento de estado/dados |
| React Router 6 | Roteamento |
| Lucide React | Ícones |

### Resultados / Findings

**Dashboard com 6 visões:**

1. **Minhas Prioridades** (`/`) — Top 10 deals do agente selecionado, perfil de performance, pipeline cleanup, deals ordenados por score
2. **Dashboard** (`/dashboard`) — Grid completo de deals com filtros (gerente, vendedor, produto, stage, categoria), KPIs, leaderboard, painel de insights
3. **Deal Detail** (`/deal/:id`) — Score ring, breakdown por dimensão, análise IA (rule-based), dados da conta, enrichment (easter eggs), deals similares
4. **Visão Manager** (`/manager`) — Comparativo entre managers, performance do time, alertas de deals críticos (>130d), afinidade vendedor-produto
5. **Analytics** (`/analytics`) — Win rate por produto/setor/região, tempo de fechamento, scatter score x EV, funil de conversão, sazonalidade, curva de velocidade
6. **Premissas** (`/premissas`) — Metodologia de scoring explicada para não-técnicos, conceitos-chave, backtest, limitações

**Scoring v3 — resultados:**
- Range: 12-81
- 2 deals HOT, 175 WARM, 1.076 COOL, 816 COLD, 20 DEAD
- Expected Value total do pipeline ponderado por score
- Backtest validado contra 6.711 deals históricos: COLD 43% → COOL 60% → WARM 73% → HOT 88% (monotonicamente crescente)

**Insights principais:**
- Pipeline inflado: 93% dos deals em Engaging têm >90 dias; 84% excedem o máximo histórico de 138 dias
- Sweet spot: deals entre 14-30 dias têm 73% de win rate
- Sazonalidade: fim de trimestre = ~80% WR vs ~49% pós-push (30pp de diferença)
- Especialização: win rate varia de 14% a 90% para o MESMO produto dependendo do vendedor

### Recomendações

1. **Limpeza de pipeline** — Fechar como Lost todos os deals >138 dias sem atividade. Libera foco dos vendedores
2. **Mentoria cruzada** — Parear vendedores com alta afinidade em um produto com colegas que têm baixa afinidade nesse mesmo produto. Foi decidido não sugerir reatribuição de deals por não termos informação sobre funcionamento da área comercial, comissões e/ou formas que aqueles leads foram obtidos.
3. **Foco nos top 20%** — Os deals com maior score concentram a maior parte do expected value
4. **Alinhamento sazonal** — Concentrar push comercial nos meses de fim de trimestre (mar/jun/set/dez). Para Prospecting, é calculado através da mediana de fechamento dos deals quando um deal teoricamente seria finalizado, recebendo pontuação maior no score caso esse teórico fechamento ocorra no fim do trimestre (decisão baseada em dados)


### Limitações

1. **Scoring rule-based, não ML** — Pesos definidos por heurística fundamentada em dados, não por modelo treinado. Funciona bem para o dataset, mas em produção deveria ser validado com A/B test
2. **Dados estáticos** — JSON pré-processado, sem integração CRM real. Em produção, precisaria de pipeline de dados
3. **CV alto (76-84%)** no tempo de fechamento — A curva de velocity é uma boa heurística, não um modelo estatístico preciso
4. **Separação Won/Lost modesta** — Diferença média de score ~3-4pp entre Won e Lost. Modelo separa corretamente na direção, mas margem é estreita
5. **Agent-Product Affinity dominante (40%)** — Vendedores com poucas observações dependem de blending com taxa global, que pode ser impreciso
6. **Empresas Fictícias** - não foi possível a implementação de agentes para composição do score para: 1. estudo aprofundado da companhia; 2. análise do fit daquela companhia ao nosso produto/solução; 3. confecção de mensagens personalizadas de prospecção levando em consideração as informações obtidas daquela companhia; 4. agente de compliance para identificar potenciais riscos; 

---

## Process Log — Como usei IA

> **Este bloco é obrigatório.** Sem ele, a submissão é desclassificada.

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Claude (claude.ai) | Planejamento estratégico, análise exploratória dos dados, definição de scoring, debate de decisões de produto |
| Claude Code (Opus 4) | Auditoria independente dos dados, scoring engine, desenvolvimento do dashboard (v1), documentação técnica, auditoria de segurança, revisão e calibração v2→v3 |
| Lovable | Frontend/UI do dashboard final (v2) — design system, componentes shadcn/ui, layout, gráficos |

### Workflow

1. **Planejamento (~2h)** — Conversa iterativa com Claude para escolher o challenge, analisar dados, definir abordagem. Descobri insights (pipeline inflado, sazonalidade, especialização) que fundamentaram todo o scoring
2. **Auditoria independente** — Pedi ao Claude Code para analisar os CSVs SEM ver minha conclusão. Gerou proposta própria de scoring com justificativas. Debatemos 5 decisões divergentes
3. **Decisões de produto** — 12 decisões documentadas. 8 foram iniciativa MINHA (candidato), 4 consenso. 0 decisões da IA sozinha
4. **Build v1 (Claude Code)** — Dashboard funcional com React + Tailwind v4 + Recharts. 7 páginas, scoring engine, script de processamento de dados
5. **Redesign visual (Claude Code)** — Migração dark mode → light mode. Design system HSL completo
6. **Build v2 (Lovable)** — Reconstrução do frontend com shadcn/ui para UI mais polida. Mantive a mesma lógica de dados e scoring
7. **Calibração v3 (Claude Code)** — Revisão completa do scoring: diagnostiquei compressão de score, redistribuí pesos (affinity 40%), removi seasonality, implementei log scale e decay multiplier

### Onde a IA errou e como corrigi

1. **Deal Value fora do score** — Claude Code propôs que o score fosse probabilidade pura, sem valor do deal. EU corrigi com Esperança Matemática: E(X) = P × V. Um deal de $26k com 60% vale mais que um de $55 com 90%. Minha decisão prevaleceu
2. **Reatribuição de deals** — IA sugeriu reatribuir deals entre vendedores. EU corrigi: não conhecemos política de comissões/territórios. Mudamos para mentoria
3. **Leaderboard privado** — IA sugeriu visibilidade restrita. EU argumentei que cultura G4 é de transparência e meritocracia. Mudamos para leaderboard público

### O que eu adicionei que a IA sozinha não faria

1. **Mentoria ao invés de reatribuição** — Experiência profissional com CRM (implementei Ploomes no Travelex Bank). Sei que reatribuir deals é político e depende de muitas variáveis.
2. **Leaderboard público** — Conhecimento da cultura G4 de alta performance e transparência
4. **UX duas camadas** — EU identifiquei o dilema entre informação rápida vs detalhada. Solução: frase-chave + expansível
5. **Botões contextuais por score** — EU questionei "Analisar com IA" como genérico. Mudamos para frases que antecipam a dúvida do vendedor
6. **Backtest pré/pós** — Ideia MINHA de comparar resultados reais vs simulação para demonstrar e calibrar o modelo
7. **Auditoria de segurança** — EU levantei preocupação com prompt injection no repo. Documentamos proteções
8. **Diagnóstico de compressão de score (v3)** — EU identifiquei que velocity colapsada, seasonality constante e deal value binária comprimiam o score. As decisões de calibração (08-10) foram minhas
9. **Validação de close_value unitário** — EU levantei a dúvida se valores do deal representavam somente o valor de uma unidade de produto que venderíamos à companhia, ou se representa o valor do deal completo. Confirmado que é o valor do deal completo.

---

## Evidências

- [x] Git history completo (commits documentados)
- [x] Documentação técnica em `docs/` (3 documentos)
- [x] Deploy funcional em [g4-lead-scorer.vercel.app](https://g4-lead-scorer.vercel.app/)
- [x] Screenshots das conversas com IA (em `process-log/screenshots/`)
- [ ] Chat exports (em `process-log/chat-exports/`)

---

## Setup

**Opção 1 — Deploy (recomendado):**
Acesse [g4-lead-scorer.vercel.app](https://g4-lead-scorer.vercel.app/)

**Opção 2 — Local:**
```bash
# Clonar e instalar
git clone https://github.com/luisbraghin/g4-lead-scorer.git
cd g4-lead-scorer

npm install
npm run dev
# Abrir http://localhost:8080
```

**Requisitos:** Node.js 18+

---

## Documentação Adicional

Todos os documentos técnicos estão em `docs/`:

| Documento | Conteúdo |
|-----------|---------|
| `scoring-methodology.md` | Metodologia v3 — fórmulas, pesos, curvas, limitações |
| `decisions.md` | 12 decisões documentadas com contexto, opções e justificativa |
| `security.md` | Auditoria de segurança do repositório + decisão sobre agentes de IA |

---

*Submissão enviada em: março de 2026*
