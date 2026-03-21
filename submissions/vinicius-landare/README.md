# Submissão v2 — Vinicius Landare — Challenge 004

## Sobre mim

- **Nome:** Vinicius Landare
- **LinkedIn:** [linkedin.com/in/vinicius-landare](https://linkedin.com/in/vinicius-landare)
- **Challenge escolhido:** Challenge 004 — Estratégia Social Media

---

## Executive Summary

Reestruturei a solução após feedback, passando de um dashboard analítico estático para um **sistema operacional de social media** que responde diretamente as 3 perguntas do gestor. O sistema gera recomendações de conteúdo baseadas nos dados do dataset (top combinações, melhores horários, piores formatos a evitar), com pipeline IA de 3 etapas usando modelos diferentes por step, calendário de aprovação, explorador interativo de patrocínio, ranking de influenciadores com mensagens WhatsApp contextualizadas via ZAPI, e análise de perfis reais via Apify (5 plataformas). Todas as recomendações incluem disclaimers honestos sobre as limitações do dataset.

---

## O que mudou da v1 para a v2

### Feedback recebido

> "Os resultados apresentados precisam de análise crítica antes de virar recomendação — verifique se as diferenças encontradas têm relevância prática real e comunique isso com honestidade. A configuração do ambiente de desenvolvimento precisa garantir que o candidato mantém controle e revisão sobre o que a IA produz."

### Como respondi a cada ponto

| Feedback | O que fiz |
|----------|-----------|
| "Análise crítica antes de virar recomendação" | Testes estatísticos (Mann-Whitney U, Kruskal-Wallis) com p-values. Badge "significativo / não significativo" em cada insight. Afirmações absolutas trocadas por tendências |
| "Diferenças com relevância prática real" | Disclaimer em todas as seções. Tab Análise de Perfil com Apify para validação com dados reais |
| "Comunique com honestidade" | "Parar de investir" virou "Menor performance relativa". "Vale a pena" virou "Tendência positiva (validar com dados reais)" |
| "Controle sobre o que a IA produz" | Documentado abaixo: cada decisão estratégica veio de mim, a IA executou |

---

## Solução v2

**Stack:** Next.js 16 + TypeScript + Tailwind CSS v4 + shadcn/ui + Recharts + OpenRouter (Gemini Flash + Claude Sonnet 4.5) + ZAPI + Apify

**Como rodar:**

```bash
cd submissions/vinicius-landare/solution
cp .env.example .env
# Preencha as variáveis no .env (veja comentários no arquivo)
npm install
npm run dev
# http://localhost:3456
# Senha: g4social2024
```

**Variáveis de ambiente:** Copie `.env.example` para `.env` e preencha. Comentários no arquivo explicam onde obter cada credencial.

| Variável | Obrigatória? | Onde obter |
|----------|-------------|------------|
| `OPENROUTER_API_KEY` | Sim — geração de conteúdo | [openrouter.ai/keys](https://openrouter.ai/keys) |
| `APIFY_TOKEN` | Opcional — análise de perfil real | [console.apify.com](https://console.apify.com) |
| `ZAPI_INSTANCE_ID` / `ZAPI_TOKEN` / `ZAPI_CLIENT_TOKEN` | Opcional — WhatsApp | [z-api.io](https://z-api.io) |

Para solicitar credenciais de demonstração (com limites de uso pré-configurados): **viniciusoliveira@example.com**

**Capturas de tela:** O processo completo de criação com IA está documentado em `process-log/screenshots/`.

### As 6 abas e o que cada uma entrega

| Aba | Pergunta do gestor | O que mostra |
|-----|-------------------|--------------|
| **Visão Geral** | As 3 perguntas de uma vez | 3 cards (engajamento, patrocínio, estratégia) + recomendações do dataset (onde investir, o que evitar, melhores dias/horários) + conteúdos pendentes de aprovação |
| **Engajamento** | "O que gera engajamento de verdade?" | Plataforma, formato, público, timing, mercados em seções colapsáveis com badges de significância |
| **Patrocínio** | "Vale a pena patrocinar?" | Explorador interativo com filtros cruzados (6 dimensões × 3 métricas). Gráfico comparativo orgânico vs patrocinado + tabela com veredicto |
| **Calendário** | "Ferramenta para acompanhar no dia a dia" | Calendário semanal. Conteúdos gerados pela IA baseados no dataset. Aprovar ou descartar |
| **Influenciadores** | "Com que influenciador?" | Ranking (score 0-100), paginação, filtros, mensagem WhatsApp contextualizada com dados + envio via ZAPI ou wa.me |
| **Análise de Perfil** | Validação com dados reais | Busca perfil via Apify (5 plataformas), cruza com dataset ou benchmark do mercado |

---

## Como o sistema gera conteúdo

### O problema que resolvi

O gestor pediu: "me dá uma ferramenta pra acompanhar isso no dia a dia". Um dashboard estático não resolve. O gestor precisa de conteúdos prontos, baseados em dados, para aprovar e publicar.

### A solução: Pipeline baseado no dataset

O sistema não gera posts aleatórios. Cada recomendação é fundamentada nos dados:

**1. Seleção do mix semanal (dados do dataset)**

O cron carrega as top 20 combinações do dataset (plataforma × formato × categoria × audiência) e seleciona 3-5 slots para a semana, variando plataformas e priorizando as combinações com maior engagement. Os dias são os melhores do dataset (segunda, quarta, sexta, domingo) nos horários de pico (7h, 11h, 18h, 21h).

**2. Geração com contexto (Draft — Gemini 3 Flash)**

O prompt recebe o contexto completo do dataset:
- Top 5 melhores combinações com engagement exato
- 3 piores combinações para evitar
- Melhores dias e horários
- Hashtags com melhor performance
- Dados de patrocínio (lift, % ROI positivo)
- Histórico de conteúdos descartados/reprovados (para não repetir)

A IA gera 5 ideias de conteúdo específicas para a combinação selecionada (ex: "Carrossel de beauty para 19-25 no Instagram").

**3. Avaliação crítica (Critique — Claude Sonnet 4.5)**

Modelo diferente avalia cada ideia em 4 dimensões: originalidade, viabilidade, alinhamento, risco. Nota mínima 7 para seguir. Ideias reprovadas são salvas no histórico para aprendizado.

**4. Auto-retry**

Se nenhuma ideia atingir nota 7, o pipeline refaz com mais criatividade (temperature sobe) e injeção no prompt: "ideias anteriores foram reprovadas, seja mais criativo". Até 3 tentativas. Se mesmo assim nenhuma passar, usa as melhores disponíveis — o gestor sempre recebe resultado.

**5. Roteiro final (Refinement — Gemini 3 Flash)**

Ideias aprovadas viram roteiros prontos para produção: copy exata, especificação visual, hashtags, horário, CTA, descrição de thumbnail.

**6. Aprovação do gestor**

Conteúdos aparecem na Visão Geral e no Calendário como "pendentes". O gestor revê, edita se quiser, e aprova ou descarta. Descartados vão para o histórico — a IA aprende o que o gestor não gosta.

### Por que modelos diferentes por step?

| Step | Modelo | Razão |
|------|--------|-------|
| Draft | Gemini 3 Flash | Rápido e criativo — precisa de volume de ideias |
| Critique | Claude Sonnet 4.5 | Melhor raciocínio analítico — precisa ser duro na avaliação |
| Refinement | Gemini 3 Flash | Rápido para formatação — o conteúdo já foi validado |

Essa decisão veio da minha pesquisa: artigo da Anthropic sobre prompt chaining + vídeo do Don Woodlock sobre Draft → Critique → Output. Combinei as duas fontes.

---

## Explorador de Patrocínio

O gestor não quer uma tabela fixa de "SIM/NÃO". Ele quer explorar os dados por conta própria.

O explorador permite:
- **Agrupar por:** plataforma, tier do creator, categoria, formato, faixa etária, mercado
- **Cruzar com:** qualquer segunda dimensão
- **Filtrar:** valor específico da segunda dimensão
- **Métrica:** engagement rate, alcance relativo, custo por engajamento

O resultado é um gráfico comparativo (orgânico vs patrocinado) + tabela detalhada com veredicto por linha.

Script Python dedicado (`analysis/07_sponsorship_explorer.py`) gera todos os cruzamentos possíveis: 30 por dimensão individual, 105 por pares, 150 por detalhe de sponsor.

---

## Análise de Perfil — Como funciona a coleta e o cálculo

### O problema do engagement em diferentes formatos

O Instagram retorna métricas diferentes por tipo de conteúdo:
- **Vídeos:** têm `views` públicas → engagement = (likes + comments) / views
- **Carrosséis e imagens:** NÃO têm `views` públicas → como calcular?

### A solução: duas métricas de engagement

Implementei duas formas de medir engagement, e o gestor alterna entre elas:

**1. Engagement por Seguidores (padrão da indústria)**
- Fórmula: (likes + comments) / seguidores × 100
- Funciona para TODOS os formatos
- Permite comparação justa entre vídeo, carrossel e imagem
- É o padrão usado por ferramentas como HypeAuditor, Social Blade, etc.

**2. Engagement por Views (complementar)**
- Fórmula: (likes + comments) / views × 100
- Só funciona para vídeos
- Útil para avaliar performance de vídeos específicos

### Fluxo técnico da coleta

1. **Normalização de input:** O sistema aceita qualquer formato — @usuario, username, link de perfil, link de post. Detecta a plataforma pela URL automaticamente.

2. **Coleta em duas etapas (Instagram):**
   - Etapa 1: `resultsType: "details"` → busca dados do perfil (seguidores, bio, nome)
   - Etapa 2: `resultsType: "posts"` com `searchType: "user"` → busca últimos 5 posts

3. **Normalização dos dados:** Cada post é normalizado para o mesmo schema. Valores negativos do Instagram (likesCount: -1 em alguns posts) são tratados como 0.

4. **Cálculo de engagement:** Ambas as métricas são calculadas para cada post. O gráfico mostra barras coloridas por tipo de conteúdo (laranja = vídeo, navy = carrossel, verde = imagem).

5. **Cruzamento com dataset:** Se o influenciador existe no ranking do dataset, mostra dados comparativos. Se é novo, compara com benchmark do mercado (plataforma × categoria).

6. **Histórico em localStorage:** Análises ficam salvas para consulta rápida sem precisar chamar Apify novamente.

### Por que essa abordagem?

Ao testar com o perfil @g4.business, o primeiro resultado mostrava engagement de 9.001% — claramente errado. O problema: o Instagram retornava `likesCount: -1` para carrosséis e o cálculo dividia por `views: 1` (estimativa fictícia).

Identifiquei o bug e mudei a abordagem: em vez de inventar views para posts estáticos, uso engagement por seguidores como métrica principal. Isso permite comparar todos os formatos na mesma escala, que é exatamente o que o gestor precisa para decidir qual formato investir.

### 5 plataformas suportadas

| Plataforma | Actor Apify | Dados coletados |
|------------|-------------|-----------------|
| Instagram | `apify/instagram-scraper` | Perfil (seguidores) + posts (likes, comments, views) |
| TikTok | `clockworks/tiktok-scraper` | Posts (likes, comments, shares, views) |
| YouTube | `streamers/youtube-scraper` | Vídeos (likes, comments, views) |
| RedNote | `easyapi/all-in-one-rednote-xiaohongshu-scraper` | Posts (likes) |
| Bilibili | `kuaima/bilibili-detail` | Vídeos (likes, comments, shares, views, coins) |

---

## Integração WhatsApp (ZAPI)

O gestor pode enviar mensagens para influenciadores direto do dashboard:

1. Configura ZAPI no `.env` (instance ID, token, client-token)
2. Escaneia QR Code no modal (clicando "Conectar WhatsApp" no header)
3. Na tab Influenciadores, clica num influenciador → gera mensagem via IA
4. Edita a mensagem no textarea se quiser
5. Envia via wa.me (link direto) ou via ZAPI (API)

A mensagem é contextualizada com dados do influenciador: engagement, comparação com benchmark, ações concretas. Antes de enviar via ZAPI, o sistema verifica se o WhatsApp está conectado e mostra erro claro se não estiver.

---

## Análise de Perfil (5 plataformas via Apify)

O gestor busca qualquer perfil e o sistema cruza com o dataset:

**Cenário A — Influenciador do dataset:** Apify coleta posts reais → cruza com dados históricos → mostra delta.

**Cenário B — Influenciador novo:** Apify coleta → gestor seleciona mercado → compara com benchmark do dataset naquele mercado.

**Plataformas suportadas:**

| Plataforma | Actor Apify |
|------------|-------------|
| Instagram | `apify/instagram-scraper` |
| TikTok | `clockworks/tiktok-scraper` |
| YouTube | `streamers/youtube-scraper` |
| RedNote | `easyapi/all-in-one-rednote-xiaohongshu-scraper` |
| Bilibili | `kuaima/bilibili-detail` |

---

## Resultados / Findings

### O que gera engajamento?

**Tendências identificadas** (dataset com variância de ~1.25%):
- Top: Instagram + image + beauty para 50+ (20.09%), RedNote + mixed + tech para 36-50 (20.07%)
- Horários de pico: 7h, 11h, 18h, 21h
- Melhores dias: sexta e domingo
- Posts com 2 hashtags performam melhor que 5+

**Nota de honestidade:** Diferenças de ~1.25% entre melhor e pior combinação. Em dados reais, esperamos 5-20%. As tendências indicam *direção*, não certeza.

### Patrocínio funciona?

**Depende do contexto. Diferenças pequenas no dataset.**

- Lift geral: +0.001% (não significativo, p > 0.05)
- Tendência positiva: Nano/Micro no Bilibili e YouTube
- Tendência negativa: Mega no TikTok
- Use o explorador interativo para cada combinação específica

### Estratégia de conteúdo

Sistema gera conteúdos baseados nos dados do dataset (não aleatórios). Cada recomendação referencia qual dado justifica a escolha. O gestor aprova ou descarta. Descartados alimentam o aprendizado da IA.

---

## Limitações

1. **Dataset simulado** — variância de ~1.25%. Disclaimers em todas as seções.
2. **Sem dados de conversão** — apenas métricas de engajamento.
3. **Texto lorem ipsum** — impossibilita análise de sentimento.
4. **Temporalidade limitada** — 9 meses sem sazonalidade real.
5. **Dados Apify simulados na demo** — com token configurado, coleta dados reais de 5 plataformas.

---

## Process Log v2

### Ferramentas usadas

| Ferramenta | Para que usei |
|------------|---------------|
| Claude Code (Opus 4.6) | Arquitetura, código, análise crítica, implementação |
| OpenRouter (Gemini Flash + Claude Sonnet 4.5) | Pipeline Draft/Critique/Output para geração de conteúdo |
| Python + pandas + scipy | Testes estatísticos, ranking, tráfego pago, sponsorship explorer |
| ChatGPT Codex + Antigravity | Validação cruzada de abordagens |
| ZAPI | Integração WhatsApp para mensagens a influenciadores |
| Apify | Coleta de dados reais de 5 plataformas |

### Evolução v1 → v2: Decisões que eu tomei

**1. "Os dados antigos não servem para o gestor"**
Dashboard v1 era organizado por hipóteses técnicas. Reorganizei para 6 tabs por pergunta de negócio.

**2. "Recomendações absolutas viram tendências"**
"SIM para micro" com diferença de 0.17% não é um "SIM". É uma tendência a validar.

**3. "O gestor não quer clicar para gerar"**
Criei cron que gera automaticamente com área de aprovação na Visão Geral.

**4. "Geração não pode ser aleatória"**
O cron carrega top combinações do dataset para definir o mix semanal. Cada conteúdo referencia qual dado do dataset justifica a escolha.

**5. "Score mínimo com histórico"**
Nota < 7 = auto-retry (até 3x). Conteúdos reprovados e descartados salvos para a IA aprender.

**6. "Mensagens genéricas não servem"**
Prompt com dados específicos: engagement, benchmark, ações mensuráveis. Textarea editável antes de enviar.

**7. "O gestor quer explorar, não só ver resumo"**
Explorador interativo de patrocínio com 6 dimensões × 3 métricas × filtros cruzados.

**8. "Dados reais via Apify"**
Análise de Perfil com 5 plataformas. Cruza com dataset ou benchmark por mercado.

**9. "Recomendações na Visão Geral"**
Além dos conteúdos pendentes, a Visão Geral mostra onde investir, o que evitar, melhores dias e horários — tudo do dataset.

**10. "WhatsApp funcional"**
ZAPI integrado com QR Code no modal, verificação de status antes de enviar, erros claros.

### Onde a IA errou e como corrigi

| O que aconteceu | Como corrigi |
|-----------------|-------------|
| Diferenças de 0.1% como insights acionáveis | Disclaimers + badges de significância |
| 9 tabs técnicas por hipótese | 6 tabs por pergunta de negócio |
| Geração de conteúdo aleatória | Mix semanal baseado nos dados do dataset |
| Score exposto ao gestor | Removido da UI — pipeline avalia internamente |
| Gráfico de campanhas confuso (barras horizontais) | Trocado por tabela visual + explorador interativo |
| Mensagens de influenciador genéricas | Prompt com dados + benchmark + ações mensuráveis |
| Botão "Enviar ZAPI" sem verificação | Verifica status antes, mostra erro claro |
| Texto sem acentos (Patrocinio, Calendario) | Busca completa e correção em todos os componentes |
| "Credenciais expostas no frontend" | Removido, credenciais só no .env (server-side) |

### O que eu adicionei que a IA não faria

1. **Análise crítica do próprio output** — identifiquei que recomendações absolutas não são honestas com diferenças de 0.1%.

2. **Pesquisa sobre prompt engineering** — combinei artigo da Anthropic (prompt chaining) + Don Woodlock (Draft → Critique → Output) para definir o pipeline com modelos diferentes por step.

3. **Multi-ferramenta** — validei com Claude Code, ChatGPT Codex e Antigravity. Decisão final minha.

4. **Geração baseada no dataset, não aleatória** — exigi que o cron carregasse os dados reais (top combinações, horários, hashtags) para fundamentar cada recomendação.

5. **Honestidade intelectual** — a IA nunca adiciona disclaimers nas próprias recomendações. Fui eu que forcei.

6. **Explorador interativo** — em vez de gráfico estático, o gestor monta sua própria consulta.

7. **Histórico de aprendizado** — descartados e reprovados alimentam o próximo ciclo. A IA evolui com o uso.

### Evidências

- [x] Process log documentando evolução v1 → v2
- [x] Git history com toda a iteração
- [x] Dashboard funcional: 6 abas + 14 API routes
- [x] 7 scripts Python (hipóteses + estatística + ranking + tráfego pago + Apify 5 plataformas + sponsorship explorer)
- [x] 40+ JSONs com metadados temporais e testes de significância
- [x] Pipeline IA: Draft (Gemini) → Critique (Claude) → Output (Gemini) com auto-retry
- [x] Calendário com geração baseada no dataset + aprovação do gestor
- [x] Recomendações na Visão Geral (onde investir, o que evitar, timing)
- [x] Explorador interativo de patrocínio (6 dimensões × 3 métricas)
- [x] Integração ZAPI com QR Code + verificação de status
- [x] Apify para 5 plataformas (Instagram, TikTok, YouTube, RedNote, Bilibili)
- [x] Histórico de aprendizado (content-history.json)
- [x] Disclaimers honestos em todas as seções
- [x] Senha: `g4social2024`

---

**Submissão v1:** 2026-03-11
**Submissão v2:** 2026-03-21
