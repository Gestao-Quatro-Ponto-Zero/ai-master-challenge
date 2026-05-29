# Submissão — Anderson Hirota — Challenge 003 (Lead Scorer)

## Sobre mim

- **Nome:** Anderson Hirota
- **LinkedIn:** [linkedin.com/in/andersonhirota](https://www.linkedin.com/in/andersonhirota/)
- **Challenge:** 003 — Lead Scorer

---

## TL;DR

> O baseline (Claude/GPT sozinho) entrega um pipeline browser scoreado: 2.089 deals filtráveis, vendedor descobre onde focar. Esta solução **decide por ele** — 3-5 must-acts por vendedor + 5 must-acts próprios do manager + intervenções, redistribuição e sinais sistêmicos. Brief opinionado em todos os níveis da hierarquia, com ações contextuais via LLM-as-judge citando fatos específicos. **E o manager pode AGIR dentro do próprio sistema** (done/defer/skip nos must-acts, send coaching note LLM-pré-preenchida, approve/reject de redistribuição) — o brief encolhe conforme decisões são tomadas, com audit log de tudo.
>
> Antes de construir, gerei 3 baselines progressivos por autocrítica de IA (`baseline-v1/v2/v3/`) pra estabelecer um teto honesto. Os **9 diferenciadores** abaixo são o que IA não converge sozinha mesmo iterando.
>
> Arquitetura espelha conscientemente o playbook que a Anthropic apresentou no SaaStr 2026 (Eleanor Dorfman — *"How Anthropic Built an AI-Native Sales Org"*): Morning Brief skill + Call Prep skill + Coaching skill + cross-tier flow como Slack-as-front-door equivalente. Mapping detalhado abaixo.

---

## Executive Summary

Construí um **Morning Brief opinionado em todos os níveis** — não um pipeline browser scoreado. A diferença não é cosmética: o baseline que IA produz sozinha mostra 2.089 deals filtráveis e pede pro vendedor descobrir onde focar. Esta solução decide POR ELE: 3-5 must-acts por vendedor, ranqueados por qualidade **e** urgência temporal, com ação contextual gerada por LLM-as-judge citando fatos específicos de cada deal. Quem abre o app não navega — age.

**E vai além do vendedor**: o Manager mode espelha a mesma estrutura de brief opinionado. Manager não é "quem coordena os outros" — é **player nos deals estratégicos do time**. Tem must-acts próprios em 3 tipos: deals onde ELE é o closer (authority + relationship unlock), intervenções executivas (rep stuck precisa de chamada C-level), e decisões de sistema (triage 1:1, redistribuição, fix de processo). Mais playbook contextual por rep crítico, sinais sistêmicos cross-rep, coaching de time inteiro.

**E ambos podem AGIR de dentro do app** — rep e manager marcam must-acts como done (com outcome note), defer (com razão) ou skip (com razão). Rep também escala via **🆘 Request manager help** quando precisa de authority/relationship/intel que ele não tem (deal vai direto pro brief do manager). Manager envia coaching note LLM-pré-preenchida, aprova/rejeita redistribuição e responde help requests (acknowledge ou dismiss com razão). Brief encolhe conforme decisões acontecem. Audit log file-based, isolado por actor, exportável em JSON. **Sistema operacional bidirecional**, não relatório.

Para construir um delta claro sobre o teto que IA gera sozinha, gerei 3 baselines progressivos por autocrítica (v1 single-shot → v2 → v3) e medi onde IA converge versus onde só humano contribui. **7 dimensões qualitativas** sobreviveram à iteração da IA e formam o núcleo desta entrega: reframe honesto do dataset histórico, dual-mode (Manager × Rep) com manager como player, LLM-judge contextual em duas vozes (rep + manager), coaching por vendedor e por time, JSON composável, diagnóstico de qualidade de dado, e tratamento explícito de pipeline orphan.

---

## Solução

### Abordagem

1. **Estabeleci um teto IA antes de construir.** Gerei 3 versões progressivas do baseline via autocrítica de IA pura (`baseline-v1/`, `baseline-v2/`, `baseline-v3/`). Cada uma com prompt naïve + iteração. Diminishing returns claros: v1→v2 pegou 8 problemas substantivos; v2→v3 pegou 7 (UX e calibragem). Isso definiu o **chão honesto** sobre o qual minha contribuição precisa demonstrar valor humano agregado, não apenas "melhor uso de IA".

2. **Reframei a tarefa.** O baseline mais sofisticado (v3) ainda é um pipeline browser com filtros. A pergunta certa não é "como ranquear 8.800 deals" — é **"que 3 deals esse vendedor precisa fechar hoje?"** O app inteiro foi reorganizado em torno disso: brief primeiro, tabela como drilldown secundário.

3. **Implementei 9 diferenciadores qualitativos** que IA não converge sozinha em N iterações (verificado empiricamente):
   - Reframe explícito do dataset histórico
   - Dual-mode (Manager × Rep) **com manager como player nos deals chave**, não orquestrador. Mesma estrutura de brief no Rep mode e Manager mode — brief é brief em qualquer nível
   - LLM-as-judge contextual em duas vozes — rep ("VOCÊ aja no deal") e manager ("VOCÊ lidera o close" / "VOCÊ intervém"). Cache + validação contra preamble leak
   - **Action layer**: manager toma decisões DENTRO do app. Done/Defer/Skip em must-acts, send coaching note (LLM-pré-preenchida), approve/reject redistribuição. Brief encolhe conforme ações são tomadas. Audit log persistente, exportável em JSON
   - Camada de coaching por vendedor + por time (alpha/bleed contra média da empresa, padrão temporal, load imbalance)
   - JSON export composável para downstream agents
   - Diagnóstico de qualidade de dado (não esconder problemas atrás de averages neutros)
   - Tratamento explícito de pipeline orphan — 27% dos deals abertos não têm account record. Não dá pra agir num deal que não diz quem ligar. Excluímos do brief e listamos pra cleanup, em vez de fingir que existem

### Resultado — o que foi construído

**Stack:** Streamlit + Python + Claude CLI (LLM-as-judge). 5 módulos.

**Arquitetura:**

```
   ┌─────────────────────────────────────────────────┐
   │  4 CSVs (Kaggle CRM Sales — 8.800 deals)        │
   └────────────────────────┬────────────────────────┘
                            ▼
        scoring.py   →  6 features ponderadas, Bayesian smoothing,
                        percentile entity-level, vectorizado
                            │
            ┌───────────────┴────────────────┐
            ▼                                ▼
     [Active pool 254]            [Ghost 1263 + Orphan 572]
            │                      (excluídos do brief,
            │                       surfacados separadamente)
            ▼
   compute_must_acts (cap 5/rep)
   • high_score (score ≥ 65)
   • time_critical (final 8% da janela ghost, Engaging only)
            │
   ┌────────┴─────────┐
   ▼                  ▼
[Rep mode]      [Manager mode]                              ┌──────────┐
coaching.py     manager.py + coaching.team_alpha_signals    │ judge.py │
(per-rep        (classificação 3 tipos must-acts,           │  ⤺ cache │
 alpha/bleed,   critical reps + playbook,                   │ ✨ LLM    │
 padrão         systemic patterns, redistribuição,          │   judged │
 temporal)      team coaching)                              │  actions │
   │                  │                                     └──────────┘
   └────────┬─────────┘                                          │
            ▼                                                    │
     JSON export composável  ←──────────────────────────────────┘
     (rep brief / manager brief) → downstream skills
```

**Estrutura de pastas (na submissão):**

```
submissions/anderson-hirota/
├── README.md                # este documento
├── solution/                # código do app
│   ├── app.py               # UI, dual-mode, render, action wiring
│   ├── scoring.py           # engine (reusado do baseline-v3)
│   ├── judge.py             # LLM-as-judge (rep + manager + coaching note) com cache
│   ├── coaching.py          # alpha/leverage por rep e por time (100% data)
│   ├── manager.py           # classificação manager, detecção sistêmica, redistribuição
│   ├── actions.py           # audit log do action layer (manager toma decisões dentro do app)
│   ├── generate_judge_cache.py
│   ├── .judge_cache/        # ~117 rep + ~30 manager actions + coaching note drafts cached
│   ├── .action_log/         # audit log file-based de ações do manager (gitignored)
│   ├── data/                # 4 CSVs do Kaggle CRM
│   └── requirements.txt
└── process-log/             # evidência da metodologia baseline-then-exceed
    ├── baseline-v1/         # naïve single-shot Claude output
    ├── baseline-v2/         # autocrítica IA (8 fixes)
    ├── baseline-v3/         # 2ª autocrítica IA (7 fixes)
    └── differentiation-rubric.md
```

**Como rodar:**

```bash
cd submissions/anderson-hirota/solution/
pip install -r requirements.txt

# Popular o cache do LLM-judge (uma vez, ~50 min, ~$0.05 em Claude API)
# Cache pré-populado já está incluído — só rode se quiser regenerar
python3 generate_judge_cache.py

# Subir o app
streamlit run app.py
```

A app abre em `http://localhost:8501`. Se o cache não existir, o app usa o template rule-based como fallback e mostra um aviso.

**LLM dependency — leia antes de avaliar:** todas as actions LLM-judged já estão **pré-geradas e commitadas em `.judge_cache/`**. O app renderiza do cache — você **não precisa de Claude CLI nem ANTHROPIC_API_KEY** pra rodar o demo, navegar pelos modos, baixar JSON, ou ver qualquer must-act com ✨. As únicas features que chamam LLM ao vivo são o botão **"Generate" do Call Prep** (gera dossier sob demanda pro deal selecionado) e o **Regenerate** do mesmo (cache bypass intencional). Sem Claude CLI instalado, essas duas degradam graciosamente com mensagem de fallback. Decisão consciente: manter Claude CLI ao invés de migrar pra API direta evita exigir API key do avaliador ou hardcodar a minha — cache resolve 99% do demo, refactor pra API seria risco grande horas antes do PR.

### O que ver primeiro

- **Banner de ref_date** — explica que o dataset é de 2017 e ancoramos "hoje" na última atividade do CRM, não no relógio
- **Banner pipeline ghost** — 60% dos open deals são ghost (>3× ciclo empírico de fechamento)
- **Banner orphan** — 27% dos abertos sem account record. CRM hygiene issue surfaced, não escondido
- **Modo Manager** (default): seletor de manager → brief com **suas must-acts** (3 tipos: 👑 top-value (manager visibility) / 🚨 executive intervention / 🔧 system decision), reps em estado crítico com playbook contextual e sugestões de redistribuição, sinais sistêmicos cross-rep, coaching de time. Leaderboard cross-team vira drilldown
- **Modo Rep**: selecione um vendedor → 3-5 must-acts com badges (🔥/⭐/🔥⭐), action contextual via LLM (✨), painel coaching individual, download de brief em JSON
- **Botão "Download brief (JSON)"** em **ambos** Rep mode e Manager mode — schema composável para downstream skills (rep-morning-brief, manager-morning-brief)

### Diferenciadores explicados

| Diferencial | O baseline IA tem? | O que adiciona |
|---|---|---|
| **Reframe data-anchored** | ❌ | Usa `max(close_date)` do dataset como "hoje". Sem isso, 100% dos deals viram ghost. |
| **Must-act: score floor + temporal urgency** | ❌ | Combina top por score (floor 65) com Engaging em janela final (8% antes do ghost-flip). Variável por rep — 1 vendedor com 2 must-acts, outro com 5. Não constante 3. |
| **LLM-as-judge contextual (rep + manager)** | ❌ | Duas vozes: action pro rep cita fatos do deal; action pro manager fala diretamente com a liderança ("VOCÊ lidera", "VOCÊ intervém"), citando authority/relationship que rep não tem. Cache no disco — `claude` CLI nunca roda no request path. |
| **Manager mode opinionado (player, não orquestrador)** | ❌ | Manager tem **3 tipos** de must-acts próprios: deals onde é o closer (top-value strategic), intervenções executivas (rep stuck precisa de você), e decisões de sistema (triage 1:1, redistribuição). Sinais sistêmicos cross-rep. Sugestões de redistribuição via capacity-matching com alpha alinhado. |
| **Coaching por vendedor + por time** | ❌ | Alpha por sector/product, padrão temporal de fechamento, comparativo com média do time. No manager mode: team vs company, load imbalance entre reps. 100% derivado dos 8.800 históricos. |
| **JSON composável** | ❌ | Schema versionado para alimentar uma skill Morning-Brief (WhatsApp/Slack/email). `action_source` distingue LLM-judged vs template. |
| **Painel de qualidade de dado + orphan handling** | ❌ | Orphan deals (account NaN) excluídos do brief e listados pra cleanup. Não dá pra "agir" num deal sem company. Conta unmapped accounts (16%), ghost share, desequilíbrio de pipeline. Não esconde problemas atrás de defaults neutros. |
| **Action layer (Manager + Rep) bidirecional** | ❌ | Sistema operacional em ambos níveis com cross-tier flow. Rep marca must-acts done/defer/skip + **🆘 Request manager help** quando precisa do manager pra desbloquear (deal vai pro brief do manager com badge 🆘, sai do brief do rep). Manager mesma coisa + coaching note LLM-pré-preenchida + approve/reject de redistribuição + acknowledge/dismiss de help requests com razão. Audit log file-based isolado por actor. Demo: rep escala às 8h, manager vê às 8:05, intervém, deal fecha. Sistema responde ao humano, não ao contrário. |
| **Call Prep skill** | ❌ | 1-page dossier LLM-gerado por deal antes da call. Estrutura fixa: Account snapshot · Why it matters today · 3 discovery questions (deal-specific, não genéricas) · Positioning angle (cita alpha do rep no sector, account context) · Likely objection + counter. Cached por hash de input — regenerate força bypass. Espelha a `call-prep` skill da Anthropic ([SaaStr Eleanor Dorfman](#mapping-to-anthropic-playbook-eleanor-dorfman-saastr-2026)). |

### Mapping to Anthropic playbook (Eleanor Dorfman, SaaStr 2026)

O reframe central deste sistema espelha conscientemente o playbook que a Anthropic apresentou no SaaStr 2026 — *"How Anthropic's Head of Industries Built an AI-Native Sales Org from Scratch"*. Não é coincidência narrativa: avaliador familiar com o talk reconhece a referência e o paralelo arquitetural.

**As 4 investments da Anthropic → o que fizemos:**

| Anthropic | Nosso sistema |
|---|---|
| **Dual funnel** (Clay+Claude qualifica → self-serve OU sales-led) | ❌ Out of scope — dataset é pipeline existente, não inbound. Cataloged como future work. |
| **Stack as foundation** (Claude como tecido conectivo entre Salesforce/Gong/Slack/Ironclad) | ⚠️ Parcial — sistema é standalone, mas **JSON export composável** é o hook. Schema versionado pra alimentar Morning-Brief skill em qualquer canal (WhatsApp/Slack/email/voice). |
| **Slack como front door** (suporte/legal/RevOps via Slack, Claude tria, escala com contexto) | ✅ **Equivalente UI-nativo**: 🆘 Help request layer é o mesmo pattern — rep "submete ticket" via UI, request aparece no brief do manager em tempo real, manager triages (acknowledge ou dismiss com razão), audit log é o thread bidirecional. **Sem Slack, mesma forma**. |
| **Encode best reps as Skills** | ✅ Skills implementadas: `Morning-Brief` (brief opinionado) + `Call-Prep` (dossier por deal) + `Coaching-Note` (manager → rep com LLM pré-preenchimento) |

**As 5 Skills da Anthropic → cobertura:**

| Skill da Anthropic | Status |
|---|---|
| **Morning Brief** | ✅ Implementada — brief opinionado em ambos os níveis (Manager + Rep) |
| **Call Prep** | ✅ Implementada — dossier estruturado por deal via LLM (Account snapshot / Why it matters / Discovery questions / Positioning / Objection+counter) |
| **Customer Follow-up** | ⚠️ Parcial — **outcome note** opcional no Done captura "o que aconteceu" (versão UI-nativa do follow-up). Sem extração automática de email/Gong ainda. |
| **Competitive Intel** | ❌ Future work — battle card dinâmico por deal exigiria competitor data. |
| **Create-an-Asset** | ❌ Future work — geração de propostas/ROI/landing tailored exigiria asset templates. |

**Os princípios estratégicos da Anthropic já estão neste sistema:**

- *"Sales leaders são systems thinkers"* → Manager mode com must-acts próprios + decisões cross-rep
- *"Dynamic coaching moments, not static methodology"* → `coaching.py` deriva alpha/bleed dos dados, não framework fixo
- *"Forecasts run by Claude, reviewed by managers"* → Manager mode é brief acionável; decisão fica com manager
- *"Thread Claude through the sales cycle you already run"* → LLM-as-judge gera ações citando fatos específicos, não substitui processo

### Limitações

**O que essa solução NÃO faz:**
- Não treina ML supervisionado (XGBoost etc.) — o brief explicitamente desvaloriza "modelos sem interface" e regras/heurísticas bem apresentadas valem mais
- Não persiste feedback do vendedor ("marcar como atuado") — fora do escopo de 4-6h
- Não tem auth, multi-tenant, ou estado entre sessões
- Não roda LLM-judge nos 2.089 deals — só nos ~117 must-acts. Custo proibitivo no caso geral, value baixo no caso particular (ghost deals não merecem prompt contextual)
- Os scores `close_probability` são cohort-derived (Won/(Won+Lost) por stage), não calibrados via ML. Honesto sobre isso no README do baseline-v3 também
- **Stage close-rate de Prospecting e Engaging colapsa pro mesmo valor** (~63%) porque o dataset não tem stage-transition history — todo deal fechado tem `engage_date`, então o denominador é idêntico. Em produção (com stage history table no CRM real) Prospecting estaria em ~30% e Engaging em ~55%. Disclosure explícita no expander "How scoring works" do app, em vez de hard-coding fake differentiation

**Vieses do dataset que o app sinaliza no banner ao invés de esconder:**
- Histórico de 2017 — ref_date precisa anchor manual em produção
- 16% das contas sem sector/revenue (enrichment falhou) — vira fallback global, mas painel de qualidade flaga
- 53% dos deals abertos são ghost — exclui da prioridade do dia, mostra em expander separado por rep

**O que mudaria com dados de produção real:**
- ref_date = `datetime.now()` (1 linha de código)
- Ghost threshold provavelmente menor — produção real tem ciclos mais curtos que 57d mediano
- Time-critical floor (atualmente 92% do threshold ghost) provavelmente sobe — janela mais apertada
- LLM-judge passaria a rodar em deals com sinais de atividade recente (`modify_date` no CRM), não top-N por score apenas

**Testado apenas em desktop.** O app foi desenvolvido e validado em viewport desktop (Chrome/Safari, 1440px+). Layouts responsivos pra mobile/tablet **não foram testados** — `st.columns`, `st.tabs` e dataframes podem quebrar em viewports estreitos. Trade-off consciente dentro do time-box do challenge: o brief é "morning system" — uso primário é desktop antes de calls, não mobile. Cross-device QA fica como future work.

**Action layer — Delegate não foi implementada (intencional).**
Considerei adicionar `🤝 Delegate` como 4ª ação no must-act (transferir pra outro manager / rep / role como Deal Desk / SE / Exec Sponsor). O caso de uso existe e é comum em nível de manager. **Não construí** porque o jeito certo requer um **org-aware target picker** com diretório de pessoas e roles tipadas — não free text. Free text degradaria o audit log a metadata inútil ("Delegated to: Tom" diz nada pro downstream). Cataloged for v2 quando integração com diretório/CRM estiver no escopo. Pattern aplicado: **action types só valem com vocabulário tipado** — caso contrário viram lixo no audit log.

---

## Process Log — Como usei IA

> Este bloco é obrigatório. Sem ele, a submissão é desclassificada.

### Ferramentas usadas

| Ferramenta | Para que usei |
|---|---|
| Claude Code (CLI) | Toda a construção. Tanto generation de baseline para medir o chão, quanto build da diferenciada sob minha direção. |
| `claude -p` via subprocess | LLM-as-judge runtime. Padrão já estabelecido nos meus outros projetos. |

### Workflow

1. **Fase A — Baseline iterado** (não single-shot). Gerei v1 com prompt naïve, depois alimentei IA com a própria saída pedindo autocrítica → v2 → v3. Razão: o baseline que G4 já tem provavelmente não é 1-shot. Comparar minha entrega contra um chão fraco superestima o delta humano. v1→v2 pegou 8 issues substantivos; v2→v3 pegou 7 (UX). Diminishing returns confirmados — parei na v3.

2. **Fase B — Rubrica antes de codar.** Listei 7 diferenciadores qualitativos que IA não converge sozinha mesmo iterando. Escrevi em `differentiation-rubric.md` ANTES de tocar em código. Critério mensurável: cada diferenciador tem que sobreviver a "uma terceira iteração IA pegaria isso?" — se sim, corto da rubrica.

3. **Fase C — Construção em 6 etapas time-boxed.** Cada etapa com smoke test ao final em dados reais. Não próxima etapa sem verificação visual lado a lado (baseline-v3 em `:8501`, submission em `:8502`).

### Onde a IA errou e como corrigi

**Bug 1 — Runtime crash:** `row['product']` em namedtuple do `pd.itertuples()` (TypeError: tuple indices must be integers or slices, not str). **3 iterações de autocrítica IA não pegaram.** Só apareceu ao clicar no painel "Why this score?" no baseline-v3. Sinal: IA é boa em refactor e arquitetura, fraca em **debug mental de paths que precisam ser exercitados** pra falhar.

**Bug 2 — 100% ghost no primeiro smoke test:** ancorar `ref_date` em `datetime.today()` (wall-clock) no dataset de 2017 fez 100% dos open deals classificarem como ghost. Brief renderizou vazio. Decisão: data-anchor em `max(close_date)` do próprio dataset, com banner honesto explicando + indicação da substituição em produção (1 linha). IA não detectou — só apareceu rodando o app com dados reais.

**Bug 3 — LLM segundo-adivinhando suas próprias respostas:** primeiro batch da geração de cache vinha com action correta seguida de `"\n\nWait — that's not the task. Let me reconsider."`. O modelo gera a resposta certa, depois reflete em voz alta e contamina o output. Solução: `_extract_first_sentence()` que pega só a primeira linha não-vazia + validador `_is_clean_action()` rejeitando prefixes de meta-talk (`wait`, `let me`, `here's`, `actually,`...). Aplicado tanto na escrita quanto na leitura do cache, então entradas polluted ficam silenciosamente filtradas. Reaproveitei o cache em vez de jogar fora 50 min de geração.

**Bug 4 — Manager prompt instabilidade entre PT/EN:** alguns outputs do manager LLM-judge vieram em português ("Você escala direto pro decisor de Plussunin...") quando o prompt era em inglês. Não filtrei — manteive, porque o conteúdo está correto e a mistura PT/EN é coerente com a realidade de empresas brasileiras. Process log honesto: deixei consciente porque é judgment call de produto, não bug.

**Gap 5 — Manager mode era read-only:** descoberto em revisão depois do Etapa 7 — Manager mode mostrava recomendações, mas o manager não tinha como AGIR de dentro do app. Contraditório com a tese "manager as player". Adicionei action layer (Etapa 9): `actions.py` com file-based audit log, UI de done/defer/skip nos must-acts, coaching note LLM-pré-preenchida + send, approve/reject de redistribuição, audit log expander exportável em JSON. **Brief encolhe conforme manager age** — esse é o momento narrativo que vende o produto ("8h cheio, 9h vazio").

**Call de design 6 — Delegate ficou de fora (consciente).** Depois de implementar o action layer, considerei adicionar `🤝 Delegate` como 4ª ação no must-act. Anderson identificou que **free text degradaria o audit log a poluição** — "Delegated to: Tom" sem estrutura não alimenta downstream nem vira métrica. Implementação correta requer org-aware picker (managers / reps / roles tipadas tipo Deal Desk, SE, Exec Sponsor), o que requer diretório de pessoas fora do escopo do challenge. Decisão: parar, documentar limitação na README, catalogar como v2. Lição: **action types só valem com vocabulário tipado**. Adicionar uma 4ª opção mal-resolvida teria sido pior que deixar 3 sólidas.

**Gap 7 — Rep mode era read-only também.** Depois do action layer no Manager (Etapa 9), Anderson notou em revisão que o Rep mode caía no mesmo problema que o Manager tinha antes: mostrar must-acts mas não deixar vendedor marcar progresso de dentro do app. Adicionei (Etapa 10): mesma UI de Done/Defer/Skip com **outcome note opcional em Done** (vendedor documenta o que aconteceu — "DM topou em principle, aguarda contraproposta"), counter no topo, filtro acted, audit log próprio. Reusei toda a infra de `actions.py` — só renomeei o parâmetro `manager` → `actor` (audit log file-based isola por nome do actor, então não há contaminação cross-actor). Lição: padrão de UI bem pensado generaliza pro outro lado da hierarquia praticamente sem custo. Manager-first foi acidentalmente útil — viraram a base, depois espelhar pro rep foi quase mecânico.

**Call de design 9 — Sort do Rep leaderboard ("where attention should land today").** Revisão final do Dashboard tab. Sort atual: `time-critical desc → high-score desc → avg_score desc`. Tensão: o nome promete "onde foco gerencial deve ir hoje", mas high-score é sinal **positivo** (deals primed to close). Dois reps com 5 time-critical iguais — um com 🟢 loaded (2 high-score), outro com ⚪ none (0 high-score) — o "loaded" sobe no ranking. Interpretação A: "loaded" merece atenção porque tem upside imediato pra fechar (manager protege a win). Interpretação B: "none" merece mais porque está drowning sem suporte (manager resgata). Mantive A (current) porque alinha com o framing Anthropic de "manager protege onde tem alavanca real" — mas reconheço que B é defensável e seria a escolha óbvia se o painel se chamasse "where rescue should land". Documentar a tensão explicitamente é mais honesto que escolher silently. Em v2 com dados reais, A/B test do sort com managers reais resolveria.

**Gap 8 — Faltava cross-tier flow (rep → manager).** Anderson questionou: "Done/Defer/Skip cobre status, mas e quando o rep não consegue fazer sozinho?". Realidade do RevOps: deal precisa de authority/relationship/pricing exception/competitive intel que rep não tem. Hoje rep teria que escolher entre Defer (mentira: ele não vai conseguir) ou Skip (mentira: é importante). Adicionei **🆘 Request manager help** como 4ª ação (Etapa 11): rep escala com texto livre descrevendo a ajuda específica (free text aqui é semanticamente válido — descreve a ajuda, não uma referência tipada como Delegate). Help request aparece em tempo real no Manager mode em seção dedicada entre Must-acts e Critical reps. Manager Acknowledge (toma pra si) ou Dismiss com razão (que volta pro rep ler). **Bidirectional flow** completa o loop — manager → rep já existia (coaching, redistribuição), agora rep → manager também existe. Demo story: rep escala às 8h, manager vê às 8:05, intervém. Lição: cross-tier signal é a coisa mais importante que faltava — sem ele o "brief opinionado em todos os níveis" era na verdade dois briefs paralelos, não um sistema vivo.

### O que eu adicionei que a IA sozinha não faria

1. **Estratégia baseline-then-exceed** (com 3 versões progressivas pra medir o chão). IA sugeria começar a build direto — eu impus a fase de baseline iterado pra ter delta defensável.

2. **Reframe da tarefa** — "isso não é um pipeline browser scoreado, é um Morning Brief opinionado". IA otimizava o scoring; eu mudei o produto.

3. **Reframe do Manager** — descobrindo o gap em runtime: Rep mode opinionado, Manager mode é dashboard. Não congruente com a tese. Manager não é "quem coordena", é **player nos deals chave**. Reescrevi Manager mode com 3 tipos de must-acts próprios + critical reps + sinais sistêmicos. Esse não estava no baseline em nenhuma versão.

4. **Calibragem dos thresholds que IA não derivaria sozinha**:
   - Floor de score 65 (top ~6% do pool) escolhido após ver a distribuição real
   - Janela time-critical 92% (final 14d antes do ghost) — IA sugeriu 85% no primeiro pass (que pegava 22% do pipeline — não opinionado)
   - Cap 5 must-acts/rep (limite cognitivo de uma manhã, não "tamanho ótimo do dataframe")
   - Cap 5 must-acts/manager — mesmo princípio, escala diferente

5. **Decisão de design priority order time_critical > high_score** — em dataset com pipeline estagnado, urgência domina qualidade como decision lever. Em dataset fresh, score dominaria. IA não derivaria essa contextualização sozinha.

6. **Tratamento honesto de orphan deals** — 27% dos open deals têm `account=NaN`. IA mostrava como "must-act with rep agir em nan". Eu separei pro panel CRM hygiene. Não dá pra ligar pra ninguém num deal sem company name.

7. **Composability hook (JSON export)** — IA não inventaria um schema para alimentar uma skill externa que ela não conhece.

8. **Limitations section honesta** — IA tende a vender features; identificar viés do dataset, deals sem account match, e o que mudaria em produção real é trabalho deliberado.

### Iterações

- Baseline v1 → v2 → v3 (3 iterações IA pura, ~10 prompts cada round de autocrítica)
- Differentiation rubric (1 versão direto após análise dos 3 baselines)
- Submission: 6 etapas construtivas, com smoke test ponta-a-ponta após cada uma

---

## Evidências

- ✅ **`baseline-v1/`, `baseline-v2/`, `baseline-v3/`** — outputs verbatim de cada iteração de IA. Cada um tem `raw-output.md` (output bruto cru) e `prompt-used.md` (prompt exato). Esses são os artefatos do chão sobre o qual minha entrega supera.
- ✅ **`differentiation-rubric.md`** — contrato escrito antes da Fase C
- ✅ **`.judge_cache/`** — cache de actions LLM-judged + payloads que determinam cada cache key
- ✅ **`generate_judge_cache.py`** — script reproducível pra regenerar o cache em qualquer máquina com `claude` CLI

Submissão enviada em: 2026-05-28
