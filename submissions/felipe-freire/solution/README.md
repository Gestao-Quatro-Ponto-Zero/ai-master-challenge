# Submissão — Felipe Freire — Challenge 004

## Sobre mim

- **Nome:** Felipe Freire
- **LinkedIn:** https://www.linkedin.com/in/felipe-freire-659615284/
- **Challenge escolhido:** 004 — Estratégia Social Media

## Executive Summary

Analisei 52.214 posts, construí pipeline reproduzível, inferência ajustada e dashboard. O dataset não sustenta vencedores por plataforma/formato e patrocínio não apresentou ganho de engagement ou alcance após controles. A recomendação central é parar expansão não experimental, instrumentar custos/conversões e decidir escala por testes controlados e break-even.

## Solução

### Abordagem

Pipeline por gates: planejamento → qualidade → EDA → inferência → estratégia → dashboard → integração → revisão. Findings exploratórios só entram na estratégia após validação, efeito, intervalo e limitações.

### Arquitetura de agentes de IA

Em vez de pedir "faça a análise" para um único chat, arquitetei um **sistema multiagente hub-and-spoke**: um Orchestrator central que coordena, mais 12 agentes especializados, cada um com entrada/saída, proibições e critério de qualidade próprios, definidos em `.claude/agents/*.md`. A especificação completa está em [`docs/agent-architecture.md`](../docs/agent-architecture.md) (fluxo, matriz operacional, armadilhas estatísticas) e [`docs/handoff-protocol.md`](../docs/handoff-protocol.md) (formato de handoff e evidence records); aqui vai o resumo.

**Por que hub-and-spoke, e não os agentes conversando entre si:** subagentes do Claude Code não conseguem invocar outros subagentes, então o Orchestrator roda como agente principal da sessão (`claude --agent orchestrator`) e delega um agente por vez, com contexto mínimo — nunca o histórico completo do chat, nunca dados fora do escopo daquela etapa. Isso evita "telefone sem fio", faz cada conclusão ser rastreável a um evidence ID e impede que um agente redefina o próprio escopo (ex.: o Data Analyst não pode decidir estratégia; o Software Engineer não pode escolher teste estatístico).

**Os 12 agentes e seus gates:**

| Ordem | Gate | Agente | Faz | Nunca faz |
|---:|---|---|---|---|
| — | — | **Orchestrator** | estado, roteamento, manifest, aprovações humanas | analisar dado, escrever conclusão |
| 1 | `P0` | **Planner** | perguntas → decisão → evidência → método → owner | calcular resultado, prometer causalidade |
| 2 | `DQ` | **Data Engineer** | ingestão, schema, contratos, lineage, quality report | interpretar performance, comparar patrocínio |
| 3 | `TECH-FOUNDATION` | **Software Engineer** (modo 1) | scaffolding, dependências, comandos, testes-base | interpretar dados, definir KPI |
| 4 | `EDA` | **Data Analyst** | tabelas/gráficos segmentados, evidence `EXPLORATORY` | causalidade, recomendação de orçamento |
| 5 | `INF` | **Statistician** | ajuste, clustering, overlap, FDR, evidence `VALIDATED`/`REJECTED` | recomendar negócio, chamar associação de causa |
| 6 | `STR` | **Marketing Strategist** | traduz evidência validada em decisão/prioridade/KPI/stop condition | recalcular métrica, inventar ROI |
| 7 | `ML` (condicional) | **ML Engineer** | modelo preditivo só com go/no-go justificado | rodar "por ter ML", vazamento treino/teste |
| 8 | `UI` | **Dashboard Builder** | KPIs congelados, reconciliação, `n` visível | criar KPI novo, interpretar resultado |
| 9 | `TECH-CONSOLIDATION` | **Software Engineer** (modo 2) | integra tudo, CI, testes end-to-end, execução limpa | alterar conclusão, "corrigir" divergência analítica |
| 10 | `DOC` | **Executive Writer** | relatório executivo: decisão → evidência → limitação | mudar direção/segmento, esconder limitação |
| 11 | `FINAL` | **Reviewer** | auditoria adversarial, read-only, `PASS`/`FAIL` por severidade | corrigir o que revisa, aprovar por aparência |
| 12 | `PUBLISH` (condicional) | **GitHub Publisher** | commit/push/PR só com `FINAL=PASS` + autorização humana | publicar por inferência, alterar conteúdo aprovado |

**Mecânica de controle:**
- **Gates travados:** nenhuma etapa começa sem a anterior em `PASS` (ou `CONDITIONAL_PASS` com pendência documentada e sem impacto na conclusão); o estado vive em `outputs/manifests/run-manifest.yaml`.
- **Evidence records:** todo achado citável tem `evidence_id`, população, método, efeito, intervalo, `n`, limitações e estado (`EXPLORATORY` → `VALIDATED`/`REJECTED`). Estratégia e relatório só citam `VALIDATED`.
- **Solicitação de correção, não retrabalho:** um agente que encontra um problema no output de outro não o edita — abre uma correção formal (`owner`, `severity`, `evidence`, `expected_fix`, `gates_to_rerun`) e devolve ao dono. Nesta execução isso aconteceu de verdade: o Orchestrator encontrou `follower_count` instável dentro do mesmo `creator_id` (DQ-007) e um evidence pack incompleto no EDA (EDA-008); ambos foram registrados no manifest, devolvidos ao owner certo e resolvidos sem reabrir gates que não precisavam.
- **Aprovação humana obrigatória:** métrica primária, exclusões ambíguas, conclusão causal, política de investimento, decisão de ML e publicação nunca são automáticas — ficam `BLOCKED` até uma decisão humana explícita.

### Resultados

- diferença máxima entre plataformas: 0,0105 p.p.;
- diferença máxima entre formatos: 0,0121 p.p.;
- patrocínio ajustado: −0,0010 p.p., IC95% −0,0095 a +0,0074;
- efeito em views: +0,26, IC95% −1,50 a +2,02;
- R² do modelo de engagement: 0,000899;
- ML: `NO-GO`, por ausência de sinal útil;
- dashboard: funcional, reconciliado e testado, com respostas explícitas às perguntas do desafio e audiência cruzada por plataforma, conteúdo e categoria.

Leia o [relatório executivo](../reports/executive-report.md) e o [registro de estratégia](../reports/strategy-register.md).

### Dashboard — evidências visuais

Visão geral com KPIs e respostas diretas sobre engagement e patrocínio:

![Dashboard — visão geral e respostas do desafio](../outputs/figures/dashboard/dashboard-01-visao-geral.png)

Audiência cruzada por plataforma, com tamanho amostral, engagement médio/mediano e views:

![Dashboard — audiência por plataforma](../outputs/figures/dashboard/dashboard-02-audiencia.png)

Exploração por dimensão, com escala fixa para não exagerar diferenças pequenas:

![Dashboard — exploração dos dados](../outputs/figures/dashboard/dashboard-03-exploracao.png)

### Recomendações

1. suspender patrocínio não experimental;
2. coletar custo, conversão e receita;
3. testar conteúdo/frequência com hipótese e stop condition;
4. não realocar por rankings deste arquivo;
5. definir política por efeito incremental e break-even.

### Limitações

Fortes sinais de dataset sintético, ausência de zeros, creator names inconsistentes, sem custos/conversões/frequência e desenho observacional. Resultados descrevem este arquivo e não devem ser generalizados sem validação real.

## Execução

Consulte `docs/technical-setup.md`. Com o ambiente configurado:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_pipeline.ps1
.\.venv\Scripts\python.exe -m streamlit run dashboard\app.py
```

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Uso |
|---|---|
| Claude Code | arquitetura de agentes e execução inicial |
| Codex | recuperação por manifest, engenharia, análise, testes, dashboard e documentação |
| ChatGPT/Gemini | conversas externas preservadas nos links do process log para arquitetar e criar|

### Workflow

1. problema decomposto em gates e agentes especializados;
2. dados validados antes da análise;
3. EDA separada da inferência;
4. recomendações ligadas a evidence IDs;
5. componentes integrados e revisados por testes.

### Onde a IA errou e como corrigi

- respostas do Claude caíram com `Connection closed mid-response`;
- Python/ExecutionPolicy impediram execução inicial;
- decimais saíram dependentes de locale;
- teste de unicidade e backend gráfico falharam;
- rankings aparentes foram rejeitados após inferência e relevância prática.

Cada incidente e correção está no [chat export](../process-log/chat-export.md) e nos relatórios técnicos.

### O que exigiu julgamento

Recusar ROI sem custos, não transformar pequenas diferenças em winners, marcar ML como `NO-GO`, limitar validade externa do dataset sintético e propor experimentação/instrumentação em vez de recomendações artificiais.

## Evidências

- [x] gravações em `process-log/evidence/videos/`;
- [x] chat export;
- [x] links de conversas externas;
- [x] hashes SHA-256;
- [x] pipeline, testes e artifacts reproduzíveis.

**Data:** 16 de julho de 2026
