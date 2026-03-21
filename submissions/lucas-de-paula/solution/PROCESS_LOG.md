# DEVLOG — Challenge 003 G4 Educação · Lead Scorer

**Ferramentas:** Claude Code (Anthropic) · Claude agente PM personalizado · Gemini 2.0 Flash (Google)
**Repositório:** https://github.com/oetnegro/lead-scorer-g4
**Live:** https://lead-scorer-g4.vercel.app

---

## Onde a IA errou — e eu corrigi

Resumo dos 3 momentos em que identifiquei erro da IA e redirecionei:

| # | Erro da IA | O que eu fiz |
|---|---|---|
| 1 | `scoreDeals()` chamado sem o parâmetro `winRates` — chamada implementada antes de verificar a assinatura da função | Identifiquei no output do TypeScript, pedi para importar `calcAgentWinRates()` e passar como segundo argumento |
| 2 | KPI cards com overlap: `Em risco` usava `days > 30` e capturava deals +90d que já tinham card próprio (zumbis) — total não fechava | Revisei os números, corrigi para `days > 30 && days <= 90`. A IA não percebeu o overlap — eu identifiquei validando a soma dos cards |
| 3 | `HowToUsePanel` inicializou state com `localStorage` direto no `useState(() => localStorage...)` — padrão inválido em SSR, gerou erros de hydration #418, #423, #425 em produção | Identifiquei em produção (não aparecia em dev), apliquei padrão SSR-safe com `useState(true)` + `useEffect` |

Detalhes completos em cada seção ERRO #1, #2, #3 abaixo.

---

## [2026-03-11 — ANÁLISE EXPLORATÓRIA DOS DADOS (sem IA)]

**Contexto:** li o desafio e os dados antes de abrir qualquer ferramenta de IA. Tenho um SaaS de pré-vendas — sabia exatamente qual dor a Head de RevOps estava descrevendo. Queria minha própria leitura dos dados antes de deixar um LLM criar vieses.

**O que analisei nos 4 CSVs:**
- `sales_pipeline.csv` — campo central: `deal_stage`, `engage_date`, `close_date`, `close_value`
- `accounts.csv` — `annual_revenue`, `sector`, `parent_company` (subsidiárias)
- `products.csv` — preço de cada produto (variação de 486× entre GTK 500 e MG Special)
- `sales_teams.csv` — estrutura de managers e escritórios regionais

**Achados que eu trouxe — a IA não teria chegado sem os dados:**
- 71% dos deals em Engaging estão parados há mais de 90 dias — zumbis invisíveis no pipeline
- GTK 500 = R$55.900 · MG Special = R$115 — diferença de 486× justifica peso dedicado ao produto
- Win rate varia de ~20% a ~70% entre vendedores do mesmo time — dado ignorado no CRM
- Ciclo médio saudável de Engaging: ~52 dias (calculado manualmente)

**Decisão tomada:** os quatro achados acima viraram os quatro componentes do scoring engine. Nenhum foi gerado por IA.

---

## [2026-03-11 — DEFINIÇÃO DO PRODUTO COM AGENTE PM]

**Ferramenta:** agente PM customizado (Claude) para estruturar a visão de produto.

**O que o agente PM fez:** estruturou as features em must-have vs. nice-to-have e mapeou a jornada do usuário-alvo.

**Decisões que eu tomei — não a IA:**

| Decisão | Alternativa descartada | Motivo |
|---|---|---|
| Interface web funcional | Jupyter Notebook | "O vendedor abre" — notebook não é produto |
| Score explicável por componente | Score único opaco | Entender "por que 83?" vale mais que accuracy |
| Foco no gestor/manager | Foco no vendedor individual | 35 vendedores + 2.092 deals = visão de portfólio é mais útil |
| Slack webhook | Email com nodemailer (SMTP) | Gestores de vendas B2B usam Slack, não configuram SMTP |
| Gemini 2.0 Flash para AI Coach | GPT-4 | Custo/performance para análise contextual de deals individuais |

**Fora do escopo inicial:** IA generativa, Slack, autenticação robusta, notificações. Entraram em iterações posteriores à medida que o MVP foi validado.

---

## [2026-03-12 — MVP: SCORING ENGINE + API + DASHBOARD]

**O que foi construído:**
- `lib/scoring.ts` — scoring engine com 4 componentes (0–100 pts)
- `lib/data.ts` — parse e merge dos 4 CSVs via Supabase
- `app/api/deals/route.ts` — GET que retorna deals ativos com score calculado
- `app/page.tsx` — dashboard com tabela paginada, filtros e KPI cards
- `app/components/ScoreBreakdown.tsx` — modal com breakdown dos 4 fatores por deal
- `app/components/DealTable.tsx` — tabela ordenável com ScoreBadge colorido

**Scoring engine — 4 componentes calibrados:**

| Componente | Peso | Lógica |
|---|---|---|
| A. Stage + Momentum | 30pts | Engaging ≤30d=30 · 31–60d=22 · 61–90d=12 · +90d=4 · Prospecting com conta=10 |
| B. Produto / Ticket | 25pts | GTK 500=25 · GTX Plus Pro=22 · GTXPro=20 · MG Special=3 |
| C. Qualidade da Conta | 25pts | Enterprise=25 · Large=18 · Mid-market=11 · SMB=6 · Sem conta=0 · +3 subsidiária |
| D. Win Rate do Vendedor | 20pts | Calculado do histórico real Won/Lost · >70%=20 · >50%=15 · >30%=10 · ≤30%=5 |

**Por que esses pesos:** Stage/Momentum é o indicador mais acionável no curto prazo — um deal parado 6 meses não merece o mesmo foco que um deal quente. Produto captura impacto de receita (GTK 500 vs MG Special não são comparáveis). Conta filtra deals sem qualificação. Win rate ajusta a expectativa por vendedor.

**Justificativa do MG Special (3pts) — baseada nos dados do challenge:**

| Produto | Deals no pipeline | Ticket médio | Receita potencial total |
|---|---|---|---|
| GTK 500 | 41 | R$26.768 | R$1.097.488 |
| GTX Plus Pro | 78 | R$8.450 | R$659.100 |
| GTXPro | 243 | R$2.890 | R$702.270 |
| **MG Special** | **1.651** | **R$55** | **R$90.805** |

O MG Special representa 79% dos deals do pipeline em volume, mas apenas 4% da receita potencial total. Um vendedor que fecha 1 MG Special gera R$55 — o mesmo vendedor com 1 GTK 500 gera R$26.768, ou seja, 486× mais receita. Dar peso alto ao MG Special distorceria o ranking priorizando volume de baixíssimo valor sobre deals que movem receita real. Os 3pts refletem que o produto existe no portfólio e merece acompanhamento, mas não deve dominar a priorização.

---

## [2026-03-12 — ERRO #1: scoreDeals() chamado sem parâmetro obrigatório]

**Problema:** Claude Code chamou `scoreDeals(deals)` sem passar `winRates`. A função exigia dois parâmetros: `deals` e `winRates`. TypeScript apontou o erro.

**Causa raiz:** a IA implementou a chamada antes de verificar a assinatura completa da função que ela mesma havia escrito.

**Correção:** identifiquei o erro no output do TypeScript e pedi para importar `calcAgentWinRates()` + `loadPipeline()` e passar o resultado como segundo argumento.

**Registro de erro:** eu (Claude Code) devia ter verificado a assinatura da função antes de implementar a chamada. A ordem de implementação estava errada — a chamada veio antes de garantir que os dados de entrada estavam completos.

---

## [2026-03-12 — PONTO DE INFLEXÃO #1: KPI cards com overlap — total não fechava]

**Contexto:** primeiro KPI implementado foi "Alta prioridade" (score ≥70). Problema: esse critério é cross-cutting — um deal zumbi (+90d) de uma conta Enterprise ainda pode ter score ≥70. Os 4 cards somavam mais que o total de deals ativos.

**Diagnóstico:** o gestor abriria o painel e veria números que não fecham. Isso gera desconfiança imediata — se os cards não somam ao total, o vendedor não confia nos dados.

**Decisão tomada (minha, não da IA):** substituir "Alta prioridade (score ≥70)" por "Saudável (≤30d)" — um critério baseado em stage + dias que é mutuamente exclusivo com os outros grupos.

**Funil final — grupos mutuamente exclusivos:**
- 🟢 Saudável (≤30d): 20 deals
- 🟡 Em risco (31–90d): 93 deals → filtro corrigido para `days > 30 && days <= 90`
- 🔵 Prospecting: 500 deals
- 💀 Zumbis (+90d): 1.479 deals
- **Total: 2.092** ✓

**Erro #2 registrado:** `Em risco` usava `days > 30` que capturava deals +90d que já tinham card próprio (zumbis). Corrigi para `days > 30 && days <= 90`. A IA não percebeu o overlap — eu identifiquei revisando os números.

---

## [2026-03-12 — ERRO #3: hydration mismatch no Next.js (SSR)]

**Problema:** `HowToUsePanel` inicializava state com `localStorage`:
```ts
// Errado — localStorage não existe no servidor
const [open, setOpen] = useState(() => {
  return localStorage.getItem("pipeline-howto-closed") !== "1";
});
```
React lançou os erros de hidratação #418, #423, #425 em produção. Em desenvolvimento local não aparecia porque o SSR se comporta diferente.

**Causa raiz:** Claude Code aplicou o padrão de `localStorage` no inicializador do `useState` sem considerar que o Next.js renderiza esse componente no servidor onde `window` é `undefined`.

**Correção:**
```ts
// Correto — SSR-safe
const [open, setOpen] = useState(true);
useEffect(() => {
  setOpen(localStorage.getItem("pipeline-howto-closed") !== "1");
}, []);
```

**Registro de erro:** eu (Claude Code) devia ter aplicado o padrão SSR-safe desde o início. `localStorage` em `useState` direto é um erro clássico em Next.js App Router — não deveria ter gerado esse padrão.

---

## [2026-03-12 — INTEGRAÇÃO SLACK: nodemailer descartado]

**Primeira versão:** Claude Code implementou relatórios por email via `nodemailer` (SMTP).

**Problema identificado por mim:** gestores de vendas B2B usam Slack como canal operacional primário. Pesquisei que a G4 Educação usa Slack internamente como principal canal de comunicação de times — faz sentido que o relatório chegue onde o gestor já trabalha, não em um canal paralelo. Configurar SMTP para uma demo é complexidade desnecessária — o avaliador não vai configurar um servidor de email para testar.

**Decisão:** descartei nodemailer e reimplementei com Slack webhook.

**O que foi construído:**
- `lib/slack.ts` — `buildMorningBlocks()` + `buildEveningBlocks()` + `sendSlackBlocks()` (Block Kit)
- `app/api/admin/settings/route.ts` — GET/POST para webhook URL salva no Supabase
- `app/api/slack/report/route.ts` — endpoint que dispara o relatório
- `app/admin/page.tsx` — painel Admin com SlackTab para configurar o webhook

---

## [2026-03-12 — DEPLOY: variáveis de ambiente no Vercel]

**Problema:** o `.env.local` está no `.gitignore` — não sobe para o repositório. Deploy inicial no Vercel falhou com 401 em todas as chamadas autenticadas.

**Causa:** todas as env vars precisavam ser configuradas manualmente no painel do Vercel:
```
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
ADMIN_TOKEN=g4admin2024
VIEWER_TOKEN=g4viewer2024
GEMINI_API_KEY
```

**Erro adicional detectado:** estava testando na URL de deploy com hash imutável (`lead-scorer-g4-bbprc0whr-oetnegros-projects.vercel.app`) em vez da URL de produção (`lead-scorer-g4.vercel.app`). Deploys com hash são snapshots imutáveis — não refletem as env vars adicionadas depois. Identifiquei o padrão e direcionei os testes para a URL de produção.

---

## [2026-03-13 — AI COACH COM GEMINI 2.0 FLASH]

**Motivação:** scoring passivo diz "esse deal tem score 83" mas não diz o que o vendedor deve fazer. Um coach de IA que analisa cada deal individualmente transforma o número em ação concreta.

**O que foi construído:**
- `app/api/ai/analyze/route.ts` — POST endpoint que recebe os dados do deal, monta prompt com benchmarks do pipeline e retorna JSON estruturado via Gemini

**Prompt montado com contexto real do pipeline:**
```
Benchmarks do pipeline: ciclo médio saudável = 52 dias, score ≥70 = alta prioridade.
Deal: [todos os campos — conta, produto, ticket, receita, setor, stage, dias, score, vendedor, manager, região]
Retorne JSON: { urgencia, resumo, acao, raciocinio }
```

**Por que incluí os benchmarks:** sem contexto do pipeline, o Gemini retornaria análise genérica. Com os benchmarks, ele consegue dizer "esse deal está 38 dias além do ciclo médio" em vez de "o deal está em Engaging há muito tempo".

**Erro #4: model name incorreto**

Claude Code usou `gemini-1.5-flash` — modelo com problemas na versão da API utilizada. Erro 500 retornado. Corrigi para `gemini-2.0-flash` e mudei o tratamento de erro para expor a mensagem real em vez de string genérica ("Falha") — isso permitiu debugar mais rápido.

**Erro #5: GEMINI_API_KEY não estava no Vercel**

O AI Coach funcionou local mas retornou 500 em produção. A env var não havia sido adicionada ao Vercel. Adicionada manualmente e redeploy realizado.

---

## [2026-03-13 — REVISÃO FINAL: WelcomeModal + mobile + vídeo]

**WelcomeModal:**
- Criado com 4 tiles de features, botão CTA e backdrop para fechar
- Movido de `page.tsx` para `layout.tsx` para aparecer em todas as páginas
- Botão "?" na Navbar despacha `CustomEvent("reopen-welcome")` para reabrir sem recarregar
- Fix: `pathname === "/login"` adicionado para não renderizar na tela de login

**Responsividade mobile:**
- `DealTable.tsx`: colunas `#` e `Ticket` com `hidden sm:table-cell`, `Produto` e `Vendedor` com `hidden md:table-cell`
- Padding ajustado no `app/page.tsx` para dispositivos pequenos

**Vídeo demo:**
- Gravado e publicado no YouTube: https://youtu.be/6IO9yX8Lra8
- URL de embed configurada como fallback em `WelcomeModal.tsx`

---

## [2026-03-13 — ESTADO FINAL DA SUBMISSÃO]

| Entregável | Arquivo | Status |
|---|---|---|
| Solução funcional | https://lead-scorer-g4.vercel.app | ✅ Live em produção |
| Scoring engine (4 componentes) | `lib/scoring.ts` | ✅ Completo |
| Dashboard com filtros | `app/page.tsx` + `DealTable.tsx` | ✅ Completo |
| ScoreBreakdown modal | `app/components/ScoreBreakdown.tsx` | ✅ Completo |
| Visão de Equipe | `app/manager/page.tsx` | ✅ Completo |
| Insights | `app/insights/page.tsx` | ✅ Completo |
| AI Coach (Gemini) | `app/api/ai/analyze/route.ts` | ✅ Live |
| Integração Slack | `lib/slack.ts` + Admin | ✅ Completo |
| Auth com perfis | `middleware.ts` | ✅ Admin + Viewer |
| Mobile responsivo | `DealTable.tsx` + `page.tsx` | ✅ Completo |
| README (template G4) | `README.md` | ✅ Completo |
| Process Log | `PROCESS_LOG.md` | ✅ Completo |
| Vídeo demo | https://youtu.be/6IO9yX8Lra8 | ✅ Publicado |

**O que a solução entrega que vai além do esperado:**
- AI Coach embarcado rodando em produção com contexto real do pipeline — não só score passivo
- Integração Slack com Block Kit (relatórios matinais + noturnos prontos para configurar)
- KPI cards com funil matematicamente fechado — gestores não confiam em números que não somam
- Auth com dois perfis (Admin/Viewer) — já pensando em segregação de acesso
- WelcomeModal com vídeo demo integrado — onboarding do usuário resolvido

**Registro de erros documentados (total: 5):**
1. `scoreDeals()` chamado sem `winRates` — erro de sequência de implementação
2. KPI `Em risco` com `days > 30` capturava zumbis — overlap não detectado pela IA
3. Hydration mismatch: `localStorage` em `useState` direto no Next.js SSR
4. Gemini model name incorreto: `gemini-1.5-flash` → `gemini-2.0-flash`
5. `GEMINI_API_KEY` ausente no Vercel — env var local não sobe com `.gitignore`
