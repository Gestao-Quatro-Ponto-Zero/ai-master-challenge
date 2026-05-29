# Submissão — Pedro Henrique Silva — Challenge 002

## Sobre mim

- **Nome:** Pedro Henrique Silva
- **LinkedIn:** https://www.linkedin.com/in/pedro-henrique
- **Challenge escolhido:** Challenge 002 — Redesign de Suporte

<!-- TODO: revise ou complemente os dados acima -->

---

## Executive Summary

- Entreguei um MVP funcional chamado **G4 Help** — um sistema de suporte inteligente com duas jornadas completas: cliente (abertura de chamado por texto ou voz com tentativa de resolução automática por RAG) e admin (dashboard analítico com EDA sobre os dados reais, gestão de tickets, base de conhecimento vetorial e uma página dedicada ao racional da camada de IA).

- O diagnóstico sobre os 8.469 tickets fechados revelou três achados acionáveis: Chat técnico resolve 3× mais devagar que os demais canais por ausência de triagem de prioridade; CSAT é estatisticamente desconectado de qualquer variável operacional; e há R$ 921 mil em eficiência represada — 26,4% do tempo total recuperável sem nenhum novo sistema.

- A recomendação central é iniciar automação assistida com guardrails de confiança, priorizando a deflexão dos ~60% de tickets de baixa complexidade que a IA já sabe responder pelo histórico.

<!-- TODO: adicione sua perspectiva pessoal aqui — o que você mais se surpreendeu ao ver nos dados? -->

---

## Solução

MVP funcional disponível em: https://g4-help.vercel.app/login

### Abordagem

- Antes de escrever qualquer linha de código, analisei o que o briefing do e-mail, da vaga e cada um dos challenges estava dizendo.
- Como fui Analista de Dados no Bradesco por 4 anos, tenho naturalmente um perfil mais analítico, então vi que o desafio era grande e fui com calma, lendo cada uma das instruções e aplicando as diferentes IAs cada uma com suas melhores área de atuação para construir o melho projeto possível.
<!-- TODO: adicione detalhes do seu raciocínio inicial — o que chamou sua atenção no brief? -->

**Estrutura de execução em fases** (documentada em `docs/00-PLANO-DE-EXECUCAO.md`):

| Fase | Escopo | Resultado |
|------|--------|-----------|
| **0 — Setup** | Estrutura do projeto, Spec Kit, plano técnico | `SPEC-MVP.md`, plano de execução, backlog por US |
| **1 — Diagnóstico** | EDA nos dois datasets, 5 perguntas focais | `public/insights.json` com métricas reais |
| **2 — Protótipo** | Next.js + APIs serverless + pipeline de NLP | App funcional com fallback local |
| **3 — Processo + ROI** | Matriz humano vs IA, modelo de ROI | `docs/03-process-and-roi.md` |
| **4 — Submissão** | README, process log, refinamentos de UX | Produto apresentável + documentação |
| **5 — Verificação** | Build, lint, checklist de qualidade | `npm run build` sem erros |


### Findings do diagnóstico (Dataset 1 — 8.469 tickets)

| Achado | Dado | Implicação |
|--------|------|------------|
| **Chat + Técnico + Low: pior combinação** | 14,6 h médias de resolução | Triagem de prioridade inexistente — Low demora mais que Critical (11,94 h vs 11,44 h) |
| **CSAT desconectado da operação** | r = −0,019 (p = 0,33) com tempo de resolução; ANOVA p > 0,28 para canal e tipo | Não adianta otimizar SLA esperando ganhar em CSAT — o dado é sintético e uniforme |
| **Eficiência represada** | 26,4% do tempo total = 26.307 h · R$ 921k estimados (R$ 35/h) | Quick win: 278 tickets P90+ = R$ 109k com intervenção pontual, sem mudar sistema |


### O que foi construído

**Jornada do cliente** (`/customer/new`):
- Entrada por texto ou voz (OpenAI Whisper-1)
- Sugestão imediata via RAG (text-embedding-3-small + pgvector + GPT-4o-mini com contexto)
- Fluxo de deflexão: "Resolveu" encerra sem abrir ticket / "Ainda preciso" cria chamado pré-classificado
- Proteção contra prompt injection (limite de 2.000 chars + validação server-side)
- Cards de resposta rápida com conteúdo real dos programas G4 (G4 Pass, G4 Gestão, G4 Traction, G4 Sales, G4 Tools)

**Dashboard admin — 4 páginas:**
- `/admin` — Visão Geral: KPIs em tempo real, 3 gráficos (gargalo por canal, tipo de ticket, satisfação), EDA com 3 cards de análise exploratória com headlines orientadas a decisão
- `/admin/tickets` — Gestão de tickets com filtro por status e prioridade
- `/admin/kb` — Base de conhecimento vetorial: criar, editar, excluir artigos com embeddings automáticos; suporte a upload em lote
- `/admin/nlp` — Pipeline de IA: fluxo de processamento, specs dos 3 modelos com custos reais, estimativa (~R$ 5/mês para 700 tickets) e racional estratégico dos 3 pilares de valor

**Pipeline de NLP** (documentado em `/admin/nlp`):

```
Entrada (texto/voz)
  → [se voz] whisper-1  →  texto
  → text-embedding-3-small  →  vetor 1.536 dim
  → pgvector (threshold ≥ 0,60)  →  5 artigos similares da KB
  → gpt-4o-mini (RAG)  →  sugestão imediata
  → classify: vetor (threshold ≥ 0,35) ou gpt-4o-mini fallback  →  categoria + prioridade
```

**APIs implementadas:**
`/api/transcribe` · `/api/rag-search` · `/api/classify` · `/api/tickets` · `/api/insights` · `/api/kb` · `/api/kb/[id]` · `/api/kb/upload`

### Matriz Humano vs IA

| Tipo de ticket | Decisão | Justificativa |
|---|---|---|
| Reset de senha / acesso básico | **Automatizar com guardrail** | Alto volume, baixa ambiguidade, resolução padronizada |
| Dúvidas sobre programas G4 (Pass, Gestão, Traction) | **Automatizar com guardrail** | KB vetorial cobre com alta confiança |
| Reembolso e cancelamento | **Assistir humano** | Risco financeiro e de retenção exige decisão contextual |
| Erro de acesso VPN / ambiente específico | **Assistir humano** | Necessita contexto do ambiente do usuário |
| Incidente crítico / cliente VIP | **Humano primeiro** | Alto risco, confiança IA provavelmente < threshold |
| Casos ambíguos / confiança < 0,75 | **Escalar automaticamente** | Guardrail explícito — evita falso positivo e fricção |

### Modelo de ROI

Premissas: R$ 35/h por agente · cenário misto 70% texto / 30% voz

| Cenário | Deflexão | Economia mensal (700 tickets/mês) | Custo IA/mês |
|---------|----------|----------------------------------|--------------|
| Conservador | 15% | ~R$ 3.675 (105 tickets × 1h avg) | ~R$ 4,50 |
| Base | 20% | ~R$ 4.900 | ~R$ 4,50 |
| Agressivo | 30% | ~R$ 7.350 | ~R$ 4,50 |

Custo operacional de IA: **< R$ 5/mês**. ROI mínimo no cenário conservador: **> 800×**.

### Recomendações

1. **Automação assistida, não full-auto** — iniciar com os 3–5 padrões mais repetitivos (acesso, certificados, dúvidas sobre programas) com threshold de confiança ≥ 0,75 antes de escalar ao humano
2. **Triagem de prioridade com IA** — o maior ganho imediato não é resposta automática, é reclassificar os tickets Low via Chat que acumulam 14,6 h de delay. Um re-router por embeddings resolve sem mudar o fluxo atual
3. **Medir deflexão semanalmente** — com 15–30% de deflexão nos tickets de baixa complexidade, o ROI supera 100× o custo operacional em semanas. A métrica-chave é `tickets_deflexionados / tickets_iniciados` por categoria

### Limitações

- Auth de produção usa cookie de demo — Supabase Auth está configurado nas variáveis de ambiente mas não ativado no fluxo de UI para não bloquear a validação sem infraestrutura externa
- Pipeline de insights é offline (`scripts/analyze_datasets.py`); em produção seria um job periódico ou webhook de atualização
- KB vetorial populada com 20 artigos reais sobre programas G4 — em produção cresceria organicamente com tickets resolvidos
- CSAT do Dataset 1 é sintético e uniforme, o que tornou inviável a análise de drivers reais de satisfação (resultado reportado honestamente no dashboard)

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usei |
|------------|--------------|
| **Claude Code** | Par de programação durante toda a implementação: EDA, arquitetura, código Next.js/TypeScript, APIs, design de UI, iterações e ajustes finais de produto |
| **Spec Kit** | Estruturação da spec MVP (`specify`), plano técnico (`plan`) e backlog por user story (`tasks`) antes de abrir o editor |
| **OpenAI API** | whisper-1 (STT), text-embedding-3-small (vetorização), gpt-4o-mini (RAG + classify) — integrados no produto final |
| **Supabase** | pgvector para busca semântica, Postgres para tickets e KB |

<!-- TODO: adicione ou ajuste ferramentas que você usou no processo que não estão listadas -->

### Workflow detalhado

**Etapa 1 — Leitura e decomposição do problema (antes de qualquer código)**

Li o README do challenge completo e escrevi `docs/00-PLANO-DE-EXECUCAO.md` antes de abrir o editor. O documento responde: o que o G4 está realmente testando, o que o baseline produz, e onde está a janela de diferenciação. Essa etapa definiu que o protótipo seria Next.js (não Streamlit), que o foco seria deflexão (não triage assistida), e que o process log seria evidência de julgamento — não de quantidade de prompts.

<!-- TODO: adicione sua perspectiva sobre esse momento inicial — o que você entendeu do brief que outros candidatos provavelmente não entendem? -->

**Etapa 2 — Spec e planejamento técnico**

Usei Spec Kit para converter o brief em user stories priorizadas (`SPEC-MVP.md`) e um plano de execução em 5 fases com timeboxes. A spec definiu a stack (Next.js 16, Supabase pgvector, OpenAI), os módulos e — crucialmente — o que **não** seria feito (treinar modelo próprio, dashboard interativo complexo, analytics demográficos).

<!-- TODO: comente sobre como o Spec Kit ajudou ou limitou o processo -->

**Etapa 3 — EDA e diagnóstico**

Rodei o script de análise nos dois datasets (Dataset 1: 8.469 tickets operacionais; Dataset 2: 48K tickets classificados). As 5 perguntas focais — onde o tempo morre, quem está insatisfeito, quanto custa, quais padrões são repetitivos, o que o histórico de resoluções revela — produziram o `insights.json` que alimenta o dashboard em tempo real. O achado mais contra-intuitivo: tickets com prioridade Low demoram **mais** que Critical no canal Chat (11,94 h vs 11,44 h), evidência direta de ausência de SLA por prioridade.

<!-- TODO: adicione sua reação ao ver os dados — houve algum achado que te surpreendeu? -->

**Etapa 4 — Implementação com Claude Code**

Implementei em ordem de dependência técnica:
1. Fundação: schema Supabase, libs (openai.ts, vector-search.ts, rag.ts), auth por cookie de demo
2. APIs serverless: transcribe, rag-search, classify, tickets, insights, kb
3. Jornada do cliente: `/customer/new` com texto/voz, RAG, deflexão
4. Dashboard admin: Visão Geral com gráficos reais, Tickets, KB, NLP & IA
5. Refinamentos de UX: hero, input bar pill com microfone, cards EDA com headlines para diretor

**Etapa 5 — Decisões de produto durante a implementação**

Três decisões que mudaram o produto e não vieram da IA:
- **Deflexão antes do ticket**: inverta a lógica — resolve primeiro, só abre chamado se não resolver
- **Página NLP & IA no admin**: o racional estratégico e os custos documentados *dentro do produto* transformam um protótipo em argumento de negócio
- **Headlines orientadas a impacto**: "R$ 921 mil em eficiência represados na operação hoje" em vez de "estimativa de desperdício"

<!-- TODO: descreva alguma decisão sua que mudou a direção do produto durante a execução -->

**Etapa 6 — Verificação e submissão**

Checklist executado antes da submissão (documentado em `docs/03-process-and-roi.md`):
- `npm run lint` → OK
- `npm run build` → OK
- App funciona sem chaves externas (todos os fallbacks testados)
- Números do dashboard batem com o script de análise
- Executive summary entendível por não-técnico

### Onde a IA errou e como corrigi

- **MediaRecorder + stale closure** — o `onstop` handler capturava `handleGenerateSuggestion` da closure inicial e ignorava updates de estado posteriores. A IA sugeriu `useRef` mas implementou errado na primeira tentativa. Identifiquei a causa raiz (ref não era atualizado a cada render) e corrigi com o padrão `genSuggRef.current = fn` dentro do efeito de render

- **`useEffect` não importado** — a IA adicionou auto-resize do textarea sem importar o hook. O erro só apareceu no runtime. Corrigi e adicionei ao import statement

- **Layout do admin com padding duplo** — em algumas páginas o `admin-content` wrappava o `admin-header`, quebrando o layout sticky. Detectei ao revisar visualmente e padronizei para `<> <header> <div className="admin-content"> </>` em todas as páginas

- **Cards de categoria com emojis** — gerados com emojis na versão inicial. Removi — o contexto de suporte corporativo G4 pede sobriedade, não informalidade

- **Sidebar com "G4 Educação" acima de "G4 Help"** — a IA manteve o label duplicado na refatoração do componente. Removi e alinhei a altura da seção de marca com o `admin-header` via `--ad-header-h` CSS variable

<!-- TODO: adicione outros momentos onde você precisou corrigir ou redirecionar a IA -->

### O que eu adicionei que a IA sozinha não faria

- **Inversão da lógica do produto** — deflexão antes do ticket, não depois. A IA teria construído um formulário de abertura melhorado. Eu mudei a tese do produto inteiro
- **Racional estratégico como página do produto** — documentar o "porquê" da IA dentro do admin para o decisor, não só o "o quê". Isso transforma um protótipo em argumento de negócio
- **Headlines orientadas ao Diretor** — "R$ 921 mil em eficiência represados" em vez de "estimativa de desperdício". A IA gerou títulos técnicos; eu os reformulei para comunicar impacto a quem vai tomar decisão
- **Guardrails de prompt injection** — limite de 2.000 chars com slice no onChange, paste handler e validação server-side. A IA não adicionou isso por conta própria
- **Fallback em todas as APIs** — decisão consciente de resiliência: o app funciona sem nenhuma chave externa configurada, com dados de demonstração realistas. A IA teria acoplado direto às APIs

<!-- TODO: adicione outros pontos onde seu julgamento fez diferença — insights dos dados, decisões de UX, cortes de escopo -->

---

## Evidências

- [x] Git history completo na branch `submission/pedro-henrique-silva` - só não está totalmente detalhado por que acabei deixando para commitar acumulativamente.
- [x] Artefatos de planejamento em `docs/` (`SPEC-MVP.md`, `00-PLANO-DE-EXECUCAO.md`, `03-process-and-roi.md`)
- [x] Build e lint validados (`npm run build` sem erros, `npm run lint` sem warnings)
- [x] Chat exports — disponíveis.
- [x] Screenshots — disponível.

<!-- TODO: adicione ou marque outras evidências que você queira incluir -->

---

_Submissão enviada em: 2026-05-28_
