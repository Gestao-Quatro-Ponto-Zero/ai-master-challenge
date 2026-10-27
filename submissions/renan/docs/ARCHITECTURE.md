# Arquitetura — Régua (Challenge 003)

> Estado final da entrega. O plano original (antes do código) está no histórico do git deste arquivo.

## 1. Objetivo do produto

Uma ferramenta que o vendedor abre na segunda-feira de manhã e, em menos de 30 segundos, sabe **quais deals atacar, em que ordem, por quê, e o que largar**. O manager usa a mesma ferramenta para ver a higiene do pipeline do time.

Princípios:

1. **Decisão > dado:** toda tela responde a uma pergunta ("onde foco hoje?"), não apenas mostra uma tabela.
2. **Explicabilidade obrigatória:** nenhum score aparece sem os fatores que o compõem.
3. **Uma única fonte de verdade:** o mesmo motor de score roda na análise, no backtest, na UI e no agente.
4. **Roda com um comando:** clone → `npm install` → `npm run dev`. Os dados estão no repositório (licença CC0).

## 2. Stack

| Camada | Escolha | Por quê |
|---|---|---|
| Runtime | Node.js ≥ 20.9 | Um único ecossistema para análise, motor e UI |
| Linguagem | TypeScript (`strict`) | Tipos do domínio compartilhados entre scripts, UI e agente |
| Framework | Next.js 16 (App Router, Cache Components) + React 19 | Server Components leem os dados no servidor; as telas saem pré-renderizadas e os filtros chegam por streaming |
| Estilo | Tailwind CSS v4 | Tokens de design em CSS (`globals.css`), sem biblioteca de componentes genérica |
| Ícones | Lucide (ISC) | Ícones do menu e dos cards |
| Validação | Zod | CSVs, entradas das ferramentas do agente e corpo das rotas |
| CSV | `papaparse` | Robusto, sem dependência nativa |
| Gráficos | CSS puro (barras, anel com `conic-gradient`, histograma) | Gráficos pequenos e sob medida, sem biblioteca |
| IA no produto | `@anthropic-ai/sdk` (Claude Opus 5.5 por padrão) | Agente Gestor com tool use |
| Testes | Vitest | 34 testes |
| Lint | ESLint (`eslint-config-next`) | Padrão do Next.js |
| Deploy | Vercel | https://regua-lead-scorer.vercel.app |

Fora de escopo de propósito: banco de dados, login e ML de caixa-preta. O dataset tem ~8.800 linhas e cabe em memória.

## 3. Estrutura de pastas

```
submissions/renan/
├── README.md                  ← submissão (template do G4)
├── CLAUDE.md                  ← instruções para o Claude Code nesta pasta
├── git-add.sh                 ← adiciona arquivos apesar do .gitignore da raiz (que ignora submissions/)
├── docs/                      ← ARCHITECTURE, SCORING, FINDINGS (gerado), DESIGN, DIFFERENTIALS, PLAN
├── design/                    ← 10 direções visuais (round-1/), fichas e ROUND-2-CONTEXT (direção fixada)
├── process-log/               ← PROCESS_LOG.md, scripts de exploração, texto do PR
└── solution/                  ← app Next.js
    ├── data/raw/              ← CSVs do Kaggle, sem alteração
    ├── data/generated/        ← dataset.json + analysis.json (gerados; gitignored)
    ├── scripts/
    │   ├── build-data.ts      ← CSV → valida → normaliza → liga as tabelas → dataset.json
    │   └── analyze.ts         ← achados + backtest → analysis.json e docs/FINDINGS.md
    ├── src/
    │   ├── domain/types.ts    ← tipos do negócio (sem React)
    │   ├── lib/data/          ← schemas Zod, normalização, montagem do dataset
    │   ├── lib/scoring/       ← motor de score: histórico, Bayes empírico, curva de sobrevivência, backtest
    │   ├── lib/agent/         ← Radar (insights), ferramentas, configuração e erros do agente
    │   ├── lib/pipeline.ts    ← dados carregados uma vez, filtros e resumos usados pelas telas
    │   ├── app/               ← telas e rotas (/api/agente, /api/agente/teste)
    │   └── components/        ← app shell, cards, tabelas, régua de dias, chat do agente
    └── tests/                 ← dados, score, backtest, agente (API simulada)
```

## 4. Fluxo de dados

```
data/raw/*.csv
   │  npm run analyze  (roda sozinho no predev e no prebuild)
   ▼
build-data.ts  → parse + validação Zod → normalização ("GTXPro" → "GTX Pro", "technolgy" → "technology")
               → liga deal + conta + produto + vendedor → relatório de qualidade → dataset.json
analyze.ts     → histórico, achados e backtest em 3 datas → analysis.json + docs/FINDINGS.md
   ▼
lib/pipeline.ts (escopo do módulo) → buildHistory + rankPipeline → telas, Radar e ferramentas do agente
```

- **Data de referência ("hoje"):** a maior data presente no pipeline (31/12/2017), mostrada na interface.
- **Sem vazamento de informação:** as estatísticas que pontuam deals abertos vêm só de deals fechados; no backtest, só dos fechados antes de cada corte.

## 5. Motor de score (`src/lib/scoring`)

Funções puras, sem I/O:

```ts
buildHistory(deals): History                             // taxa geral, curva de sobrevivência, ciclos, fatores encolhidos
scoreDeal(deal, history, refDate)                        // momento, chance decomposta em fatores, valor esperado, próxima ação
rankPipeline(deals, history, refDate): ScoredDeal[]      // ordena por valor esperado e calcula o score 0–100
backtest(deals, cutoff): BacktestResult                  // AUC e receita no top 20% contra estratégias ingênuas
```

`ScoredDeal` traz: `daysOpen`, `momentum` (prospecção, início, em andamento, reta final, parado), `winProbability` (nula para parados), `expectedValue`, `factors[]` (pontos percentuais que somam a chance), `nextAction`, `flags` e `score`.

Detalhes em [SCORING.md](./SCORING.md).

## 6. Telas

| Rota | Para quem | Pergunta que responde |
|---|---|---|
| `/` Hoje | Vendedor | "Onde eu foco hoje?": pauta por valor esperado, indicadores e painel da fila de revisão |
| `/pipeline` | Vendedor e manager | Todos os deals abertos, com busca e filtros na URL |
| `/parados` | Vendedor e manager | "O que eu largo?": deals além de 138 dias, para revisar ou desqualificar |
| `/deal/[id]` | Vendedor | "Por que esse score?": ficha, régua de dias e recibo do score |
| `/time` | Manager | Higiene do pipeline por vendedor, sem ranking de desempenho |
| `/agente` | Vendedor e manager | Radar de alertas e perguntas aos dados |
| `/metodologia` | Avaliador e RevOps | Como o score funciona, achados e backtest |
| `/configuracoes` | Usuário do agente | Chave da API do próprio usuário, modelo e esforço |

## 6.1 Agente Gestor

- `src/lib/agent/insights.ts`: Radar (alertas determinísticos por vendedor ou manager).
- `src/lib/agent/tools.ts`: 7 ferramentas somente leitura sobre o motor de score, mais a ferramenta `responder` (formato de painel).
- `src/app/api/agente/route.ts`: loop de tool use (Opus 5.5 por padrão, esforço configurável, fallback de recusa no Opus e no Sonnet). O escopo fica restrito aos dados pelo system prompt. Os deals da resposta são montados pelo servidor a partir do motor.
- **Chave:** do próprio usuário, salva no navegador e enviada no cabeçalho `x-anthropic-key` a cada pergunta; não é guardada no servidor. Sem chave, o Radar funciona e o chat pede a configuração.

## 7. Qualidade

- Acessibilidade: navegação por teclado, foco visível, contraste AA nos dois temas, `prefers-reduced-motion` e link "pular para o conteúdo".
- Responsivo até 375 px, com o menu em gaveta no celular.
- Tema sistema/claro/escuro sem piscar na carga.
- Textos em pt-BR; valores em US$, a moeda do dataset.
- Testes: dados (casos de borda), score (recibo que fecha a conta, Bayes empírico), backtest (AUC), agente (ferramentas, rota, loop com API simulada, Radar).

## 8. Como escalar

- Trocar os CSVs por um conector do CRM (Salesforce/HubSpot) com sync diário.
- Triagem de 1 clique na fila de parados (ainda ativo / desqualificar com motivo / fechou), com escrita no CRM. Isso gera o sinal que hoje falta e alimenta os pesos.
- Banco para histórico de scores e triagens; SSO e chave da empresa num cofre de segredos para o agente.
- Notificação semanal por e-mail ou Slack com a pauta de cada vendedor.
