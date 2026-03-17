# Submissão — Pedro Margon Lorenzoni — Challenge build-003-lead-scorer

## Sobre mim

- **Nome: Pedro Margon Lorenzoni**
- **LinkedIn: https://www.linkedin.com/in/pedro-margon-lorenzoni-488673221/**
- **Challenge escolhido: data-003-lead-scorer**

---

## Executive Summary

Construí um dashboard completo de CRM e sales analytics para o G4 Business, usando dados reais de pipeline de vendas (8.800+ deals, 85 contas, 35 agentes). A solução entrega dois sistemas de scoring originais: **Account Rating** (saúde da conta, escala A–D com 6 sinais ponderados) e **Kill Score** (risco de abandono de deal ativo, escala 0–100 com 5 sinais). O dashboard diferencia dois papéis — vendedor e gerente — com views dedicadas: o seller vê seu pipeline em lista ou kanban com um Daily Briefing automático dos 3 deals mais críticos; o admin acessa visão 360 com performance regional, leaderboard de agentes e análise por produto. O app foi deployado em produção no Vercel em `g4-lead-scorer.vercel.app`, construído integralmente com Claude Code como copiloto principal.

---

## Solução

### Abordagem

Parti do dataset de sales pipeline da Kaggle (4 CSVs: `sales_pipeline.csv`, `accounts.csv`, `sales_teams.csv`, `products.csv`) e os transformei em arrays TypeScript in-memory em `lib/data.ts`. O problema central do challenge era: **como priorizar deals e contas de forma inteligente?**

Decomposição:
1. Primeiro defini os dois eixos de scoring: saúde de conta (olhar para trás — histórico de Won/Lost) e risco de abandono de deal (olhar para agora — sinais de estagnação).
2. Depois planejei as views por papel: seller precisa saber "o que eu faço hoje?"; admin precisa saber "onde está o problema no time?".
3. Implementei o frontend seguindo a identidade visual da G4 Business (`id-visual.md`) — paleta navy/terracota/gold, tipografia Manrope, tokens Tailwind customizados.
4. Usei Claude Code com subagentes especializados: `backend-skeleton-builder` → `backend-architect` → `back-metrics-reviewer` → `frontend-builder`.

### Resultados / Findings

**Sistema de scoring implementado:**

| Métrica | Lógica | Output |
|---------|--------|--------|
| **Account Rating** | 6 sinais: recência (25%), conversão (20%), expansão (20%), recorrência (15%), ticket médio (10%), LTV (10%) | A / B / C / D |
| **Kill Score** | 5 sinais: tempo excedente (30%), estagnação (25%), rating invertido (20%), ROI do esforço (15%), conversão do produto (10%) | Vermelho / Laranja / Amarelo / Verde |
| **Deal Smell** | Atratividade do deal: stage (30%), valor (25%), receita da conta (25%), recência (20%) | 0–100 |
| **Killer Score** | Potencial máximo do deal: preço do produto (35%), employees da conta (30%), urgência de stage (20%), frescor (15%) | 0–100 + badge "KILLER" se ≥ 80 |

**Páginas entregues:**
- `/login` — seleção de papel (seller ou admin) com dropdown de agentes
- `/dashboard` — KPIs, sidebar de contas, List View e Kanban View, Daily Briefing Modal (top 3 deals por combined score)
- `/deals` — tabela admin com 50 deals/página, filtros, kill score colorido
- `/accounts` — grid de 85 contas com modal detalhado, rating breakdown, red dot para contas D
- `/performance` — 3 tabs: Agentes, Managers, Regiões (com bar chart de benchmark e leaderboard)
- `/products` — cards com win rate por produto, bar chart e pie chart de market share
- `/team` — leaderboard de 35 agentes com drawer de detalhes

**App ao vivo:** [g4-lead-scorer.vercel.app](https://g4-lead-scorer.vercel.app)

### Recomendações

Com base nos dados e na lógica dos scorings:

1. **Priorizar abandono de deals Vermelho/Laranja** — o Kill Score identifica deals estagnados há mais de 90 dias com contas rating D. Redirecionar energia do vendedor para deals com Amarelo/Verde aumenta win rate.
2. **Monitorar contas rating D proativamente** — contas com score < 40 têm histórico fraco de conversão. Um workflow de re-engajamento estruturado antes do próximo deal reduz perda de tempo.
3. **GTK 500 é o produto de maior ROI** — preço mais alto (~$6.000), mas com win rate competitivo. Treinar o time para identificar contas Enterprise (>2.000 funcionários) onde o GTK 500 fecha melhor.
4. **Daily Briefing como hábito** — o modal automático que mostra os 3 deals mais críticos do dia reduz o tempo que o vendedor passa navegando a lista completa.

### Limitações

- **Dados hardcoded:** Todo o dataset está em `lib/data.ts` — mudanças de stage no Kanban/ListView não persistem após refresh. Sem backend ou banco de dados.
- **Dataset histórico:** Os dados vão até dezembro de 2017; os scores usam `2018-01-01` como data de referência. Não reflete pipeline real atual.
- **Auth mock:** Login usa `localStorage` sem validação server-side — qualquer usuário pode alterar o papel manualmente.
- **Typo no CSV original:** `sector = "technolgy"` (faltando um 'o') em 2 contas — nunca normalizado, aparece nas views.
- **Sem persistência de feedback:** Não há como o vendedor salvar notas ou histórico de ações em um deal.

---

## Process Log — Como usei IA

> **Este bloco é obrigatório.** Sem ele, a submissão é desclassificada.

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| **Claude Code (claude-sonnet-4-6)** | Copiloto principal — planejamento, scaffold, debugging, revisão de código em tempo real |
| **Claude subagente `backend-skeleton-builder`** | Leu os CSVs e gerou o esqueleto inicial de `lib/data.ts`, modelos TypeScript e estrutura de rotas |
| **Claude subagente `backend-architect`** | Implementou a lógica completa de `accountRating.ts` e `killScore.ts` com pesos e fórmulas |
| **Claude subagente `back-metrics-reviewer`** | Revisou a implementação dos scores contra os dados reais dos CSVs para validar consistência |
| **Claude subagente `frontend-builder`** | Construiu todas as páginas e componentes React/Tailwind seguindo `id-visual.md` e `analise-portfolio.md` |

### Workflow

1. **Definição do problema:** Li o enunciado do challenge (`build-003-lead-scorer`) e defini que o entregável seria um dashboard interativo com scoring de leads/deals, não apenas um script de análise.
2. **Extração dos dados:** Usei `backend-skeleton-builder` para parsear os 4 CSVs e gerar os tipos TypeScript e os arrays de dados em `lib/data.ts`.
3. **Design do scoring:** Trabalhei com `backend-architect` para definir os 6 sinais do Account Rating e os 5 sinais do Kill Score, com pesos calibrados manualmente com base no que faz sentido para o negócio.
4. **Revisão dos scores:** `back-metrics-reviewer` conferiu se os valores calculados batiam com os dados brutos dos CSVs — identificou o problema do `GTXPro` duplicado.
5. **Construção do frontend:** `frontend-builder` leu o `id-visual.md` e `analise-portfolio.md` antes de escrever qualquer componente. Cada página foi construída de forma iterativa: primeiro a estrutura, depois os filtros, depois os modals de detalhe.
6. **Iterações de UX:** Refinei o Daily Briefing Modal, o Kanban view (colunas Prospecting/Engaging), o sidebar de contas e o Deal Detail Panel com base em feedback visual próprio.
7. **Deploy:** Configurei o projeto no Vercel com Root Directory apontando para `solution/` e deployei via CLI (`npx vercel --prod`).

### Onde a IA errou e como corrigi

1. **GTXPro vs GTX Pro:** O `backend-skeleton-builder` importou o produto `GTXPro` como entrada duplicada junto com `GTX Pro`. O `back-metrics-reviewer` identificou o problema. Solução: normalizei para `GTX Pro` nos deals e adicionei `filter(p => p.product !== 'GTXPro')` nas views de produtos.
2. **Data de referência inconsistente:** `scores.ts` (arquivo mais antigo) usava `2017-02-15` como "hoje" para cálculo de recência. Os novos módulos `accountRating.ts` e `killScore.ts` usavam `2018-01-01`. Percebi a inconsistência comparando os scores do mesmo deal nos dois sistemas. Corrigi o `scores.ts` mas mantive os dois arquivos separados para não quebrar o Daily Briefing que já usava o antigo.
3. **TypeScript: Set spread não suportado:** O `frontend-builder` usou `[...new Set(arr)]` em vários lugares, mas o `tsconfig.json` tinha target que não suportava essa sintaxe. Corrigi para `Array.from(new Set(arr))` em todos os arquivos afetados.
4. **Kanban com 4 colunas:** A IA implementou inicialmente Kanban com Won e Lost como colunas arrastáveis — o que não faz sentido operacional (vendedor não "arrasta" um deal para Won). Redirecionei para apenas 2 colunas ativas (Prospecting e Engaging), com Won/Lost como estados finais não editáveis.
5. **Métricas iniciais:** Estava fazendo um brainstorm com a IA sobre pontos importantes com base na minha interpretação dos dados, mas ela não consiga ir para frente e indicar algo util. Logo, peguei uma folha de papel e comecei desenhar.

### O que eu adicionei que a IA sozinha não faria

- **Calibração dos pesos dos scorings:** A IA gerou fórmulas válidas, mas os pesos (ex: recência com 25% no Account Rating vs 15% na recorrência) foram decididos por mim com base no raciocínio de negócio — qual sinal importa mais para prever o comportamento futuro de uma conta.
- **Decisão do Daily Briefing:** A ideia de um modal que abre automaticamente na primeira sessão do dia com os 3 deals mais críticos foi minha — a IA não propôs isso, eu descrevi o comportamento e ela implementou.
- **Role-based UX:** A distinção entre seller (foco em seu pipeline) e admin (visão 360) foi uma decisão de arquitetura que tomei antes de começar. A IA implementou conforme especificado, mas a lógica de "o que cada papel precisa ver" veio de mim.
- **Identidade visual:** Alimentei a IA com `id-visual.md` extraído do site real da G4 Business. Sem esse arquivo, o resultado seria um dashboard genérico. Eu fiz a análise do site e gerei os tokens de design.

---

## Evidências

- [x] Git history (branch `submissions/pedrolorenzoni` com histórico completo de commits)
- [x] App ao vivo: [g4-lead-scorer.vercel.app](https://g4-lead-scorer.vercel.app)
- [ ] Screenshots das conversas com IA _(a adicionar)_
- [x] Screen recording do workflow: [Loom — G4 Lead Scorer Demo](https://www.loom.com/share/22f64ecc89fb4ce29ed9be46f7abf483)

---

_Submissão enviada em: 2026-03-17_
