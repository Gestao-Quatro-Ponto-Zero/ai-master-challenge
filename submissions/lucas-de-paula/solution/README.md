# Submissão — Lucas de Paula — Challenge 003

## Sobre mim

- **Nome:** Lucas de Paula
- **LinkedIn:** https://www.linkedin.com/in/lucas-de-paula-b73a4496/
- **Challenge escolhido:** Challenge 003 — G4 Educação · Lead Scoring para Pipeline B2B

---

## Executive Summary

O Lead Scorer transforma um pipeline de ~8.800 oportunidades B2B em inteligência acionável para gestores e vendedores. Cada deal recebe um score 0–100 calculado a partir de quatro fatores calibrados contra os dados reais do CRM (stage + momentum, produto/ticket, qualidade da conta e win rate histórico do vendedor).

O principal achado da análise exploratória: **~71% dos deals em Engaging estão parados há mais de 90 dias** — zumbis invisíveis que consomem atenção de vendedores que deveriam estar focados nos ~34 deals de alta prioridade. A ausência de critério objetivo de priorização é o maior problema operacional do pipeline.

A recomendação principal é integrar a ferramenta diretamente ao CRM via API para receber e atualizar leads automaticamente — eliminando a dependência de exports manuais e tornando a plataforma o centro de operações comerciais do time.

🔗 **Live:** https://lead-scorer-g4.vercel.app
🔑 **Token de acesso:** `g4admin2024` (Admin) · `g4viewer2024` (Viewer)

---

## Solução

Aplicação web full-stack com três camadas de visão, um motor de scoring explicável e um coach de IA embarcado.

### Pipeline (Vendedor / Manager)

2.092 deals ativos scorados e rankeados em tempo real. O score é recalculado a cada carregamento com base nos dados do Supabase — qualquer atualização nos dados de entrada reflete imediatamente nos rankings.

KPI cards com **funil matematicamente fechado**:
- 🟢 **Saudável (≤30d):** 20 deals — ciclo dentro do normal
- 🟡 **Em risco (31–90d):** 93 deals — atenção urgente
- 🔵 **Prospecting:** 500 deals — qualificação pendente
- 💀 **Zumbis (+90d):** 1.479 deals — revisar ou encerrar
- **Total: 2.092** ✓ (grupos mutuamente exclusivos, sem overlap)

Cada deal tem **action tag automática** baseada em stage + dias + score:
- 🚀 Prioridade máxima · ⚠️ Contato urgente · 💀 Revisar ou encerrar · ➡️ Mover p/ Engaging · 📋 Avançar proposta

**ScoreBreakdown modal** explica os 4 componentes do score — qualquer vendedor entende por que um deal tem score 83.

### Coach de IA (Gemini 2.0 Flash)

Qualquer deal pode ser analisado individualmente com um clique. O Gemini recebe todos os dados do deal (conta, produto, ticket, receita da conta, setor, stage, dias no stage, score, vendedor, manager, região) mais os benchmarks do pipeline (ciclo médio saudável = 52 dias; score ≥70 = alta prioridade) e retorna em JSON estruturado:

- **Urgência:** alta / média / baixa
- **Resumo:** avaliação geral em 1 frase
- **Ação:** o que o vendedor deve fazer hoje (específico e concreto)
- **Raciocínio:** explicação em 2-3 frases baseada nos dados numéricos

Isso transforma o scoring passivo em orientação ativa — o vendedor não precisa interpretar o número, recebe diretamente a próxima ação.

### Visão de Equipe (Manager)

Win rate e volume de deals por vendedor. Ranking com performance relativa — identifica quem precisa de coaching e quem está acima da média. Win rate calculado do histórico real de Won/Lost de cada agente (varia de ~20% a ~70% no mesmo time).

### Admin

Configuração de webhook Slack para relatórios automáticos: top deals do dia + lista de zumbis direto no canal do time, sem precisar abrir a plataforma.

---

## Abordagem

### 1. Leitura e análise manual dos dados — antes de qualquer prompt

Li o desafio inteiro e analisei os quatro CSVs em planilha antes de abrir qualquer IA. Objetivo: ter minha própria leitura dos dados sem deixar um LLM criar vieses na minha análise.

Tenho um SaaS voltado para pré-vendas, então sabia exatamente qual dor a Head de RevOps estava descrevendo. Os campos que priorizei: `deal_stage`, `days_in_stage` (calculado), `close_value`, `account_revenue`, `product_price`, histórico Won/Lost por agente.

**Insights que eu trouxe — a IA não teria chegado neles sem os dados:**
- ~71% dos deals em Engaging são zumbis (+90d) — o problema de foco é estrutural, não individual
- GTK 500 custa 486× mais que MG Special — peso do produto na prioridade é enorme
- Win rate varia de ~20% a ~70% entre vendedores do mesmo time — dado ignorado no CRM atual
- Ciclo médio saudável de Engaging: ~52 dias — benchmarks reais, não estimativas

### 2. Definição de produto com agente PM

Com os dados entendidos, usei meu agente PM customizado (Claude) para estruturar o produto — não para gerar código, mas para pensar: quais features resolvem o problema real vs. são nice-to-have? Qual é a jornada do usuário-alvo na segunda de manhã?

**Decisões que tomei — não a IA:**
- Foco no **gestor/manager**, não só no vendedor individual — com 35 vendedores e 2.092 deals, quem precisa de visão de portfólio é o manager
- Score **explicável por componente** — entender "por que 83?" é mais útil que só ver o número
- **Slack** ao invés de email — gestores de vendas B2B usam Slack, não configuram SMTP
- **Gemini** ao invés de GPT — custo/benefício melhor para análise contextual de deals individuais

### 3. Scoring engine — 4 componentes calibrados (0–100 pts)

| Componente | Peso | Lógica |
|---|---|---|
| **A. Stage + Momentum** | 30pts | Engaging ≤30d=30 · 31–60d=22 · 61–90d=12 · +90d=4 (zumbi) · Prospecting com conta=10 |
| **B. Produto / Ticket** | 25pts | GTK 500=25 · GTX Plus Pro=22 · GTXPro=20 · MG Special=3 |
| **C. Qualidade da Conta** | 25pts | Enterprise(>$2B rev)=25 · Large=18 · Mid-market=11 · SMB=6 · Sem conta=0 · +3 subsidiária |
| **D. Win Rate do Vendedor** | 20pts | Calculado do histórico real Won/Lost · >70%=20 · >50%=15 · >30%=10 · ≤30%=5 |

**Por que esses pesos?** Stage/Momentum é o indicador mais acionável no curto prazo. Produto captura impacto de receita real (GTK 500 vs MG Special não são comparáveis). Conta filtra leads sem qualificação mínima. Win rate ajusta a expectativa de conversão por vendedor — dois deals idênticos valem diferente dependendo de quem está gerenciando.

### 4. Construção incremental com Claude Code

Todo o desenvolvimento foi feito com Claude Code (CLI), com eu direcionando cada etapa. A IA implementava; eu decidia o quê, por quê e validava.

---

## Resultados / Findings

| Métrica | Valor |
|---|---|
| Deals ativos scorados | 2.092 |
| Zumbis identificados (+90d) | 1.479 (71% do Engaging) |
| Alta prioridade (score ≥70) | ~34 deals |
| Deals saudáveis (≤30d) | 20 deals |
| Em risco (31–90d) | 93 deals |
| Win rate range no time | ~20% a ~70% |
| Componentes de score explicados | 4 (com breakdown visual) |

**O que o gestor vê na segunda de manhã:**
1. KPI cards — funil completo em 4 números que somam ao total
2. Top deals rankeados por score com action tag + urgency note
3. Coach de IA sob demanda — análise individualizada com próxima ação concreta
4. Ranking de equipe — quem está performando e quem precisa de suporte

---

## Recomendações

### 1. Conectar ao CRM real via API — próximo passo imediato

A arquitetura atual (Next.js + Supabase) já suporta integração real. Substituir os CSVs importados por webhooks do HubSpot ou Salesforce faria o pipeline atualizar automaticamente a cada novo deal ou mudança de stage, sem nenhum export manual. O scoring recalcularia em tempo real.

### 2. Recepção direta de leads via API + distribuição automática

Conectar a ferramenta diretamente ao CRM para receber novos leads via webhook → distribuir automaticamente por vendedor com base em regras do pipeline (região, segmento, carga do time). O lead entra no CRM e já aparece no Lead Scorer rankeado e com action tag — zero trabalho manual de distribuição.

### 3. Central de canais — WhatsApp, e-mail, tráfego pago

Solução mais completa: integrar os canais de entrada de leads (WhatsApp Business, inbox de e-mail, formulários de tráfego pago) para que o recebimento, a qualificação e a distribuição dos leads sejam centralizados e trabalhados diretamente no pipeline. Lead chega pelo canal que for → entra no Lead Scorer → recebe score → vai para o vendedor certo.

### 4. Autenticação por usuário com RLS

Em produção, cada vendedor teria login próprio e veria apenas seu próprio pipeline. O manager veria tudo. Hoje é token compartilhado — adequado para MVP e validação, não para produção com dados sensíveis.

### 5. Score dinâmico com ML supervisionado

O modelo de regras é ótimo para começar e tem explainability total. Com 6–12 meses de dados de conversão, um modelo supervisionado (XGBoost ou regressão logística) poderia substituir os pesos fixos, aprendendo com os resultados reais do time.

### 6. Histórico de score por deal

Rastrear como o score de cada deal evolui ao longo do tempo — identifica padrões de aceleração ou deterioração antes que sejam visíveis no stage.

---

## Limitações

- **Sem integração live com CRM** — o pipeline é alimentado via importação de CSVs para o Supabase. O scoring recalcula em tempo real, mas a fonte de dados não é um CRM conectado. Dados novos precisam ser importados manualmente.
- **Autenticação simplificada** — token único compartilhado, sem Row Level Security por usuário. Adequado para demonstração; inadequado para dados sensíveis em produção.
- **Pesos do score heurísticos** — calibrados com base na análise dos dados reais, mas não validados contra dados de conversão futura. O modelo de regras é um bom ponto de partida; precisaria de dados de resultado para calibração supervisionada.
- **Anotações no localStorage** — notas por deal salvas no navegador local; não persistem entre dispositivos nem são compartilhadas.
- **Sem suite de testes automatizados** — a solução foi validada manualmente com dados reais do pipeline e está funcional em produção, mas não tem cobertura de testes unitários ou de integração para CI/CD.
- **Rate limiting no Gemini** — a API key está segura nas env vars do Vercel, mas em produção com múltiplos usuários simultâneos precisaria de controle de rate limiting e cache de análises.

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usei |
|---|---|
| **Claude Code** (CLI) | Desenvolvimento principal — toda a aplicação (Next.js, APIs, componentes, deploy) |
| **Claude (agente PM)** | Fase de produto — estruturar visão, definir features, priorizar escopo |
| **Gemini 2.0 Flash** | Feature de IA Coach embarcada no produto — análise de deal individual |

### Workflow

1. **Análise manual dos dados** (sem IA) — li o challenge, baixei os CSVs, analisei campo a campo em planilha. Formei minha própria hipótese do problema antes de abrir qualquer ferramenta.

2. **Sessão com agente PM** — usei meu agente PM customizado para decompor o problema de produto: usuário-alvo real, jornada de uso, features que entram vs. ficam de fora, critérios de prioridade.

3. **Desenvolvimento com Claude Code** — implementei feature por feature, com eu definindo a lógica e a IA implementando. ~30 sessões de edição com ciclos de "implementa → testa → ajusta → decide".

4. **Validação com dados reais** — testei cada feature contra os dados reais do pipeline. Onde a lógica não batia com o que eu esperava dos dados (ex: overlap nos KPI cards), eu identifiquei e corrigi.

5. **Iterações de produto** — várias features foram adicionadas ou removidas durante o desenvolvimento com base no meu julgamento de valor para o gestor.

### Onde a IA errou e como corrigi

| Erro | O que aconteceu | Como resolvi |
|---|---|---|
| `scoreDeals()` com 1 argumento | IA chamou a função sem o parâmetro `winRates` obrigatório | Identifiquei o erro de TypeScript e pedi para importar `calcAgentWinRates` + `loadPipeline` |
| Hydration mismatch (React) | `HowToUsePanel` usava `localStorage` diretamente no `useState` — roda no SSR do servidor, onde `window` é undefined | Corrigi: inicializar como `true` e ajustar em `useEffect` |
| URL errada no Vercel | Estava testando na URL com hash de deploy antigo (imutável no Vercel) | Identifiquei o padrão de URL e direcionei os testes para a URL de produção |
| SMTP com nodemailer | Primeira versão usava nodemailer — complexo demais para o gestor configurar em uma demo | Decidi trocar por Slack webhook (mais simples, mais adotado por times de vendas B2B) |
| KPI cards com overlap | `Em risco` usava `days > 30` e capturava deals +90d que já tinham card próprio (zumbis) | Corrigi para `days > 30 && days <= 90` — grupos mutuamente exclusivos |
| KPI "Alta prioridade" cruzado | Card de score ≥70 se sobrepunha com grupos de stage — total não fechava | Substituí por "Saudável (≤30d)" para que 4 grupos somassem exatamente o total |

### O que eu adicionei que a IA sozinha não faria

1. **A lógica dos pesos do score** — calibrei A=30, B=25, C=25, D=20 com base na leitura dos dados reais. Um LLM sem os dados chutaria pesos genéricos; eu soube dar peso 25 ao produto porque vi que GTK 500 custa 486× mais que MG Special.

2. **A decisão de usar Slack** — entendo que gestores de vendas B2B usam Slack como canal primário de operação. A IA sugeriu email com SMTP; eu corrigi para webhook Slack.

3. **O KPI "Saudável (≤30d)"** — a IA gerou "Alta prioridade (score ≥70)" que se sobrepunha aos grupos de stage. Eu identifiquei o problema de comunicação para o gestor (números que não fecham geram desconfiança) e propus o grupo que fechava o funil matematicamente.

4. **O foco no gestor** — o challenge diz "vendedor", mas com 35 vendedores e 2.092 deals, a ferramenta mais útil é para quem gerencia o portfólio. Essa decisão de produto mudou toda a arquitetura da interface.

5. **O AI Coach com contexto de pipeline** — não pedi só para a IA analisar o deal; mandei os benchmarks do pipeline junto (ciclo médio 52d, threshold de score ≥70) para que a análise fosse relativa ao contexto real, não genérica.

### Evidências

- **Git history:** https://github.com/oetnegro/lead-scorer-g4 — commits descritivos mostrando a evolução de MVP básico até Coach de IA e responsividade mobile (~30 iterações)
- **Live app:** https://lead-scorer-g4.vercel.app — funcional em produção com dados reais
- **Vídeo demo:** https://youtu.be/6IO9yX8Lra8

---

*Submissão enviada em: março de 2026*
