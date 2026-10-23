# Submissão — Tiago Canatelli — Challenge 001

## Sobre mim

- **Nome:** Tiago Canatelli
- **LinkedIn:** https://www.linkedin.com/in/otiagocanatelli-eaas
- **Challenge escolhido:** 001 — Diagnóstico de Churn (RavenStack)

---

## Executive Summary

Montei um data lake no Supabase (raw → bronze → silver → gold) alimentado pelo MCP do Kaggle, cruzei as 5 tabelas e testei 9 hipóteses com estatística, separando correlação de causa. O churn subiu (37 → 251 eventos por trimestre) porque **as contas novas estão falhando nos primeiros 90 dias**: contas de até 3 meses churnam a 46,5 por 100 contas-mês, contra 8,3 das veteranas, e a coorte de 2024 tem 3,3× a chance de churnar em 6 meses, sem mudança no mix de clientes. "Satisfação ok" e "uso cresceu" convivem com isso porque os instrumentos são cegos: o CSAT só vai de 3 a 5 e é igual para quem sai e quem fica, 58% dos churns não abrem ticket, e o uso é estável e tem datas anteriores ao cadastro. **Recomendação principal:** um programa de onboarding dos primeiros 90 dias, validado com experimento, e uma fila semanal do CS por MRR em risco (US$ 333 mil em risco em 90 dias), que já roda no painel entregue.

---

## Solução

| Entregável | Onde |
|---|---|
| **Relatório para o CEO** (1–2 páginas) | [`report/diagnostico-churn.md`](report/diagnostico-churn.md) |
| Evidências de cada hipótese (reproduzível) | [`analysis/results/diagnostico.md`](analysis/results/diagnostico.md) · `uv run --group analysis python analysis/diagnostico.py` |
| Lista de contas em risco | `analysis/results/risk_accounts.csv` e a tabela `gold.risk_scores` |
| **Painel** com login por área (CEO, Financeiro, CS, Suporte, Produto, Marketing, Vendas, Dados + admin) | https://ravenstack-dashboard.onrender.com |
| API, assistente de IA (Claude) e **MCP** para Claude e outras IAs | https://ravenstack-api.onrender.com · `/mcp` — guia de conexão em [`docs/mcp.md`](docs/mcp.md) |
| Data lake (migrations versionadas) | [`supabase/migrations/`](supabase/migrations/) |
| Pipeline de ingestão (Kaggle MCP → Supabase) | [`packages/ravenlake/`](packages/ravenlake/) — **roda sozinha no Render a cada 15 min** (pg_cron do Supabase → `POST /ingest/cron`) e pelo botão "Executar ingestão agora" no painel (admin/Dados), com progresso ao vivo |
| Qualidade de dados | [`docs/data-quality.md`](docs/data-quality.md) |
| **Modelo de dados (DER) e como resolvemos o lake** | [`docs/modelo-de-dados.md`](docs/modelo-de-dados.md) · dicionário: [`docs/dicionario-de-dados.md`](docs/dicionario-de-dados.md) |
| **Linha do tempo do dia** (passos reais, pelos commits) | [`docs/timeline-do-dia.md`](docs/timeline-do-dia.md) |

### Abordagem

1. **Entender antes de executar.** O pedido do CEO é um paradoxo: o churn subiu × "satisfação ok" × "uso cresceu". Escrevi o [plano de projeto](docs/01-plano-projeto.md) e o [plano técnico](docs/02-plano-tecnico.md) e criei as skills por papel em `.claude/skills/`: cientista de dados, negócio, engenharia Python, React/UX e process log.
2. **Ir à fonte.** Li o README original do dataset, baixei os dados pelo MCP do Kaggle e conferi as regras contra os CSVs. Isso derrubou suposições da própria IA (ver *Onde a IA errou*).
3. **Lake reproduzível.** bronze idêntico ao CSV, silver tipado (0 de 33.100 linhas rejeitadas, totais conferidos contra o CSV) e 16 checagens de qualidade, que viraram achados.
4. **Diagnóstico com rigor.** Para cada hipótese: tabelas cruzadas, número, teste estatístico e checklist de causalidade (precedência temporal, controle por segmento, dose-resposta e alternativa descartada). Corrigi para múltiplas comparações e separei efeito de calendário de efeito de coorte.
5. **Transformar em ferramenta.** A camada gold reproduz o diagnóstico em SQL, com score de risco, personas e visão 360. A API, o painel por área e o MCP usam as mesmas views, então o mesmo número aparece em todo lugar.

### Resultados / Findings

| # | Hipótese | Veredito | Número-chave |
|---|---|---|---|
| H0 | O churn subiu? | ✅ em logos | 37 → 251 eventos por trimestre |
| H8 | Contas novas falham cedo *(surgiu dos dados)* | ✅ padrão; mecanismo a testar | 46,5 × 8,3 por 100 contas-mês; coorte 2024 com OR 3,3 (p = 9e-07) |
| H1 | Satisfação mascarada | ✅, mas o instrumento é cego | CSAT 3,96 × 3,97; só notas 3–5; 58% de churn silencioso |
| H2 | O uso cresceu? | ❌ | Estável, cerca de 63 por conta; 53% do uso antes do cadastro |
| H5 | Peso em receita | ✅ | Enterprise = 77% do MRR perdido; top 10% = 43% |
| H3 | Erros e beta antecedem o churn | ❌ | ρ = 0,05 (p = 0,23) |
| H4 | O motivo declarado explica | ❌ | 6 motivos uniformes; só 4 textos de feedback distintos |
| H6 | Segmento de cadastro (canal, indústria…) | ❌ após Bonferroni | Nenhum de 6 testes significativo |
| H7 | Downgrade antecede o churn | inconclusiva | Mudança de plano 2× (indício fraco) |
| H9 | Quem churna volta? | inconclusiva (validade do dado) | 87% têm nova assinatura em cerca de 16 dias |

Detalhes em [`process-log/hypotheses.md`](process-log/hypotheses.md).

### Recomendações

1. **Onboarding dos primeiros 90 dias** (CS + Produto): 129 contas novas, US$ 155 mil em risco, impacto de US$ 15–46 mil em 90 dias.
2. **Fila semanal do CS por MRR em risco**, sem esperar ticket: top 50 contas, US$ 185 mil em risco, impacto de US$ 19–56 mil. Já está no painel, na aba "Contas em risco".
3. **Plano de renovação Enterprise:** 95 contas, US$ 168 mil em risco, impacto de US$ 17–51 mil.
4. **Consertar os instrumentos:** CSAT 1–5 real com pergunta de intenção de renovação, e log de uso ancorado na assinatura e na data.
5. **Experimento:** sortear metade das contas novas para o onboarding e medir o churn em 90 dias. Isso transforma o indício em causa.

Os impactos usam 3 cenários de salvamento (10, 20 e 30%) e não se somam, porque os públicos se sobrepõem.

### Limitações

- **Dataset sintético** (Kaggle, River @ Rivalytics, MIT): churn e assinaturas são desacoplados, `churn_flag` contradiz os eventos e o uso tem datas impossíveis. Por isso os KPIs de receita (GRR/NRR) são aproximados, e as conclusões usam contagem de churns e tempo de casa.
- **O mecanismo da causa (onboarding, ativação ou expectativa) não está nos dados:** é hipótese a validar com experimento.
- As personas "Âncora Enterprise" (22 contas) e "Pro anual" (24) ficaram abaixo do mínimo de 30.
- **Cortes de escopo, por tempo:**
  - RAG com busca híbrida;
  - provedores OpenAI e Gemini, com avaliação comparativa;
  - análise 360 com várias lentes ao mesmo tempo;
  - painéis dedicados por área e por persona (cada área usa a visão geral + o assistente com a sua lente);
  - resposta em streaming.
- **Ingestão "em tempo real":** a fonte (Kaggle) é estática, na versão 1 desde 2025-07. O agendador verifica a versão a cada 15 min e registra `skipped` quando nada mudou. Com "reprocessar tudo" no painel, o pipeline completo roda ao vivo. Os cron jobs do Render são pagos (a conta bloqueou serviços pagos), por isso o agendador fica no Supabase.
- O plano gratuito do Render dorme quando fica parado: o primeiro acesso pode levar cerca de 1 minuto.

---

## Process Log — Como usei IA

> Process log completo em [`process-log/`](process-log/): journal, prompts-chave, decisões, erros da IA, hipóteses e timeline.

### Ferramentas usadas

| Ferramenta | Para que usou |
|---|---|
| Claude Code (Claude Opus 5.5) | Planejamento, skills, SQL, pipeline, análise estatística, API, painel, deploy e documentação |
| MCP do Supabase | Aplicar migrations, consultar o lake e rodar os advisors de segurança e desempenho |
| MCP do Kaggle | Baixar o dataset e checar a versão, sem login |
| Claude API (Claude Opus 5.5) | O assistente do painel, respondendo com tools sobre o lake |
| Render (API REST) | Deploy da API e do painel |
| Navegador embutido | Ler o README do dataset e validar o painel |

### Workflow

1. Planejei com a IA e só depois executei: plano de projeto, plano técnico e 5 skills revisadas uma a uma comigo ([`process-log/prompts.md`](process-log/prompts.md)).
2. Conferi cada regra das skills contra os CSVs reais antes de construir.
3. Lake: migrations aplicadas no Supabase, ingestão pelo Kaggle MCP, totais conferidos e execução repetida para provar idempotência.
4. Diagnóstico: testes de hipótese em script reproduzível; eu cobrei correção para múltiplos testes e a separação entre calendário e coorte.
5. Gold, API, painel com papéis e deploy, com testes que comparam o gold contra o CSV.

Linha do tempo real, tirada dos commits: [`docs/timeline-do-dia.md`](docs/timeline-do-dia.md) (detalhe por fase em [`process-log/timeline.md`](process-log/timeline.md)).

### Onde a IA errou e como corrigi

Lista completa: [`process-log/ai-errors.md`](process-log/ai-errors.md).

- **Schema e soluções desenhadas sem olhar o dado.** A IA assumiu colunas e planejou um RAG sobre `feedback_text`, que só tem 4 textos distintos. Corrigi depois de checar a fonte.
- **Quase-achado falso.** O "plano atual" deu p < 0,001, mas era causalidade reversa: o plano era posterior ao churn. Descartado.
- **GRR implausível (45%)** por dupla contagem: corrigido. **Views lentas** por funções que o Postgres não incorpora na consulta: materializadas.
- **`git add -f` commitou 4.306 arquivos** de `.venv` e caches. Refiz o commit e criei `scripts/stage.sh`.
- **Horários inventados no process log:** reescritos com os timestamps dos commits.
- **Impactos estimados em vez de consultados** no primeiro rascunho do relatório: recalculados no banco.

### O que eu adicionei que a IA sozinha não faria

- Pedi planejamento e skills por papel **antes** de executar, e revisei cada skill.
- Escolhi `churn_events` como fonte de verdade quando as três definições de churn discordavam.
- Pedi para ir à fonte primária (o README do dataset e o MCP do Kaggle) em vez de confiar no resumo do challenge.
- Defini um ambiente único no Supabase SaaS, um painel por persona com login por área e um admin, e um assistente que responde sempre com o "porquê".
- Priorizei por MRR e cortei escopo para cumprir o prazo, mantendo o diagnóstico intacto.

---

## Evidências

- [x] Git history: commits pequenos por passo, na branch `submission/tiago-canatelli`
- [x] Process log escrito: journal, prompts-chave, decisões, erros da IA, hipóteses e timeline
- [x] Código reproduzível: migrations, pipeline, script de diagnóstico e testes (`uv run pytest packages`)
- [x] Painel e API no ar (Render), com auditoria das respostas da IA em `app.ai_runs`
- [ ] Chat export: ver `process-log/chat-exports/`

---

## Como rodar

Pré-requisitos: [`uv`](https://docs.astral.sh/uv/), Node 22. Não é preciso Docker: tudo roda no Supabase SaaS.

```bash
cp .env.example .env                                  # preencher DATABASE_URL, SUPABASE_*, ANTHROPIC_API_KEY, AUTH_SECRET
uv sync --all-packages --group analysis
uv run python scripts/apply_sql.py supabase/migrations/<arquivo>.sql   # em ordem; ou supabase db push --linked
uv run python scripts/apply_sql.py supabase/seed/prompts_and_profiles.sql
cd packages/ravenlake && uv run ravenlake ingest      # Kaggle MCP → raw → bronze → silver → DQ → gold → catálogo
uv run python scripts/create_users.py                 # admin + 1 usuário por área (códigos em .users.local.md)
uv run uvicorn api.main:app --reload                  # API em :8000 (assistente + /mcp)
cd apps/dashboard && npm ci && npm run dev            # painel em :5173 (VITE_API_URL)
uv run python scripts/render_deploy.py                # deploy no Render
```

MCP no Claude Code:

```bash
claude mcp add --transport http ravenstack-churn https://ravenstack-api.onrender.com/mcp --header "Authorization: Bearer <MCP_TOKEN>"
```

Dataset: *SaaS Subscription & Churn Analytics* — River @ Rivalytics (Kaggle, MIT).

---

_Submissão enviada em: 2026-10-23_
