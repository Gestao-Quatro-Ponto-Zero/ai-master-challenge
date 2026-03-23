# Submissão — Mariana Peixoto Coelho — Challenge 003

## Sobre mim

- **Nome:** Mariana Peixoto Coelho
- **LinkedIn:** https://www.linkedin.com/in/maripeixotoc/
- **Challenge escolhido:** Challenge 003 — Lead Scorer

---

## Resumo Executivo

Construí um dashboard web funcional de lead scoring para uma equipe de 35 vendedores com ~2.089 oportunidades ativas no pipeline. A solução usa os dados reais do CRM (4 tabelas, 8.800 registros) para calcular um score de 0–100 por deal, com base em 5 fatores explícitos: estágio do deal, valor do produto, perfil da conta, velocidade no pipeline e performance histórica do vendedor. A interface permite ao vendedor abrir o dashboard, ver seus top deals ranqueados e entender exatamente por que cada score é alto ou baixo — sem caixa-preta. A principal recomendação é adotar um threshold de score ≥70 como critério de priorização semanal, substituindo o "feeling" por dados auditáveis.

---

## Solução

### Abordagem

Comecei explorando os 4 CSVs para entender a estrutura real dos dados (distribuição de stages, range de datas, campos disponíveis). Identifiquei que os deals ativos (Engaging + Prospecting) somam 2.089 oportunidades — o universo real de trabalho do vendedor. A partir daí, projetei uma lógica de scoring baseada em regras com 5 componentes explícitos, priorizando explicabilidade sobre complexidade de modelo. A interface foi construída em Next.js 16 + React 19 + Tailwind, aproveitando a estrutura já existente no projeto. O design visual foi gerado com Stitch (Google) a partir de um prompt detalhado, e implementado fielmente em código.

### Resultados / Descobertas

- **2.089 deals ativos** processados (1.589 Engaging + 500 Prospecting)
- **Score médio do pipeline:** ~33/100 — reflexo de um pipeline com muitos deals antigos parados
- Deals com score ≥70 representam as melhores oportunidades de foco semanal
- **Achado relevante:** muitos deals de alto valor (produto caro) ficam com score baixo por pipeline velocity negativa — sinalizando deals esquecidos que precisam de atenção ou encerramento
- **Filtros funcionais** por região, manager e vendedor, com busca livre por conta/produto/vendedor
- **Ordenação Flexível:** Implementei um sistema de ordenação por score (maior/menor) e por data (mais recentes/antigos), facilitando a gestão do tempo e prioridade do pipeline.
- **Estratégia de IA:** Adicionei um Agente de IA que fornece conselhos estratégicos personalizados para cada deal, ajudando o vendedor a decidir a melhor abordagem (ex: urgência, demonstração de ROI, ou re-qualificação).

### Pontuação (0–100 pts)

| Fator | Peso | Lógica |
|---|---|---|
| Estágio do Deal | 25 pts | Engaging (25) > Prospecting (15) |
| Valor do Produto | 20 pts | Preço normalizado vs. portfólio |
| Perfil da Conta | 20 pts | Revenue + Employees normalizados |
| Velocidade no Pipeline | 20 pts | Fresher = maior score (penaliza >150 dias) |
| Performance do Vendedor | 15 pts | Win rate histórico calculado dos dados Won/Lost |

### Recomendações

1. **Pontuação ≥70 = prioridade da semana** — regra simples, adotável imediatamente sem treinamento
2. **Deals com score baixo por velocity** — re-qualificar ou encerrar para limpar pipeline e aumentar foco
3. **Adicionar data de última atividade** ao CRM para refinar o fator velocity (hoje usa apenas engage_date)
4. **Próximo passo técnico:** modelo ML supervisionado treinado nos Won/Lost históricos para validar e ajustar os pesos do scoring com dados reais de resultado

### Limitações

- Dataset não tem campo de "última atividade" — velocity usa apenas engage_date como proxy
- Dataset é de 2016–2017; scoring usa 2017-12-31 como data de referência para dias no pipeline
- Sem dados de contato/interações para enriquecer o score comportamental
- Tabela exibe top 100 deals por performance — filtros resolvem o restante

---

## Configuração — Como executar

```bash
# Pré-requisitos: Node.js 18+

cd web
npm install
npm run dev
```

Acesse: **http://localhost:3000/lead-scorer**

Os dados CSV são lidos de `web/data/` na inicialização. Nenhuma configuração adicional necessária.

---

## Log do Processo — Uso de IA

> **Este bloco é obrigatório.** Sem ele, a submissão é desclassificada.

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Claude Code | Exploração e análise dos dados CSV, design da lógica de scoring, construção completa do dashboard (Next.js, API route, UI em React/Tailwind) |
| Gemini 3 Flash | Modelo de IA utilizado para a execução de tarefas e geração de código |
| Stitch (Google) | Geração do design visual do dashboard a partir de prompt detalhado — 4 telas geradas |
| Antigravity Kit (repositório de agentes) | Repositório de agentes, skills e workflows usado como base para potencializar o desempenho do Claude Code ao longo do desenvolvimento |

> **Repositório de agentes utilizado:** https://github.com/vudovn/antigravity-kit.git

### Workflow

1. Clonagem do [Antigravity Kit](https://github.com/vudovn/antigravity-kit.git) como base — repositório com agentes, skills e workflows que potencializaram o Claude Code durante todo o processo
2. Briefing do challenge → Claude Code explorou os CSVs e mapeou estrutura e distribuição dos dados
3. Claude Code criou prompt detalhado para o Stitch com especificações de UX/UI (layout, cores, componentes, referências visuais)
4. Stitch gerou os 4 designs (dashboard principal, empty state, manager view, deal breakdown)
5. Claude Code construiu a lógica de scoring em TypeScript (`web/src/lib/lead-scorer.ts`) e a API route (`/api/leads`)
6. Claude Code construiu o dashboard React seguindo os designs do Stitch (`web/src/app/lead-scorer/`)
7. Tradução completa para português — interface e textos dos fatores de score
8. Implementação do **Agente de IA Estratégico** para recomendações personalizadas
9. Build validado (zero erros), servidor rodando em `localhost:3000/lead-scorer`

### Onde a IA errou e como corrigi

- **Formatação de números com locale europeu:** Claude Code gerou `34.288` ao invés de `34,288` — identifiquei no output da API e corrigi para `toLocaleString('en-US')`
- **Prompt inicial para o Stitch muito genérico:** a primeira versão gerava designs muito básicos — refinei com referências visuais específicas (Linear, Vercel, Stripe) e especificação explícita de todas as 4 telas
- **Data de referência errada:** Claude Code inicialmente calcularia dias no pipeline a partir de hoje (2026), gerando valores absurdos — identifiquei o problema na análise dos dados e defini manualmente `2017-12-31` como data de referência do dataset

### O que eu adicionei que a IA sozinha não faria

- **Decisão de usar 2017-12-31 como data de referência** — contexto que só faz sentido com leitura crítica dos dados
- **Escolha de priorizar explicabilidade sobre accuracy do modelo** — direção estratégica de negócio, não técnica: um score de regras bem explicado vale mais para o vendedor do que um XGBoost sem contexto
- **Curadoria dos designs do Stitch:** escolhi entre as variações, direcionei a estética neon/dark adequada para o uso em vendas B2B
- **Threshold de score ≥70 como regra de priorização** — interpretação do contexto de negócio, não derivável automaticamente dos dados
- **Agente de IA Estratégico:** Adicionei uma camada consultiva de IA que analisa o score e os dados de cada deal para fornecer orientações estratégicas personalizadas (ex: quando envolver um sênior, como abordar o ROI, ou quando re-qualificar).
    - **Pedido:** "Incluir um Agente de IA para explicar melhor o score e as recomendações de forma estratégica de abordagem de cada cliente".
    - **Implementação:** Desenvolvi uma lógica no `lead-scorer.ts` que correlaciona múltiplos fatores (velocidade, valor, perfil) para gerar conselhos consultivos, exibidos com UI premium (gradientes e badge "AI Beta") no painel de detalhes.

---

## Evidências

- [x] Screenshots dos designs gerados pelo Stitch — `evidence/screenshots/`
- [x] Prompt usado no Stitch — `assets/stitch_prompt.md`
- [x] Git history do desenvolvimento — `git log`
- [ ] Screen recording do workflow — _a adicionar_
- [ ] Chat exports — _a adicionar_

---

_Submissão enviada em: 2026-03-23_
