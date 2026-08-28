# Plano de Execução — Challenge 001 (Diagnóstico de Churn · RavenStack)

- **Candidato:** Jose Nascimento
- **Branch:** `submission/jose-nascimento`
- **Pasta exclusiva:** `submissions/jose-nascimento/`
- **Ferramenta real:** opencode como orquestrador + subagentes `deepseek-max` (via OpenCode Go), um por etapa, em sequência
- **Última atualização:** 2026-08-28 (fim da Iteração 01; validação do executor concluída — review gate 3x da Iteração 01 pendente de disparo)
- **Status desta versão:** Iteração 00 `CONCLUDED` (incl. review gate 3x e correções — ver `process-log/reviews/iteration-00-review-summary.md`); Iteração 01 `CONCLUDED` (validação do executor; gate 3x a disparar); Iterações 02–10 `PENDING`

---

## 1. Regras de orquestração (vigentes do início ao fim)

1. **Um agente por etapa:** cada iteração é executada por exatamente um agente `deepseek-max`, sequencialmente. O orquestrador (opencode) não implementa código; apenas gerencia agentes.
2. **Revisão 3x após cada etapa:** ao terminar uma etapa, 3 agentes `deepseek-max` revisam o resultado em paralelo e em modo read-only. Se encontrarem problemas materiais, um agente sequencial faz as correções.
3. **Reports em disco:** toda etapa produz report estruturado em `process-log/reports/`, com diretórios e filenames disciplinados.
4. **Estados do plano (semântica):** `PENDING` = iteração/item ainda não iniciado; `OPEN` = executor trabalhando na iteração/item; `CONCLUDED` = implementação da iteração concluída **e validada pelo executor** (critérios objetivos de aceitação atendidos com evidência). O review gate 3x é acompanhado **separadamente** no `orchestrator-checklist.md` (item B3) e no ledger de revisões (`process-log/reviews/iteration-XX-review-summary.md`); um finding material pode reabrir a iteração (`OPEN`) ou gerar correção sequencial antes da próxima etapa. Este arquivo usa exclusivamente os estados `PENDING`, `OPEN` e `CONCLUDED`; `CONCLUDED` de iteração **não** implica review gate concluído — o gate é registrado à parte (Iteração 00: gate e correções concluídos em 2026-08-28).
5. **Escopo git:** somente arquivos dentro de `submissions/jose-nascimento/` podem ser alterados ou commitados. O `.gitignore` raiz ignora `submissions/`; commits usam `git add -f` apenas nos paths pretendidos.
6. **Autor dos commits:** identidade do candidato (verificada: `Jose Nascimento <322186960+josenascimento1@users.noreply.github.com>`), sem alterar `git config`.
7. **Evidência real:** nada é afirmado sem arquivo ou número verificável no repo; nenhuma conclusão de análise pública ou de material de pesquisa é citada — tudo é re-derivado do processo e dos dados.
8. **Disclosure de pesquisa interna (benchmark vs fonte da solução):** pesquisa interna de benchmark foi usada apenas para **mapear riscos e regras** do processo (ex.: critérios de reprovação, time budget, armadilhas comuns). Nenhum número, código, fraseado ou conclusão dessa pesquisa é copiado para a solução — toda conclusão é rederivada e reproduzível a partir dos 5 CSVs pelo pipeline próprio (Iterações 01–06). O prompt de gestão arquivado (`process-log/prompts/iteration-00-prompt.md`) referencia os paths dessa pesquisa **por transparência** (histórico preservado, evidência honesta); a solução não cita essas fontes. Distinção clara: **pesquisa de benchmark** (contexto de processo, nunca citada nas entregas) ≠ **análise pública do dataset** (fonte proibida de conclusões — regra 7).

---

## 2. Política de contenção (time budget oficial 4–6h)

O README oficial projeta o desafio para **4–6 horas** e não premia soluções longas. Esta política é vigente da Iteração 01 à 10, aplicada pelo orquestrador e reavaliada ao fim de cada etapa:

1. **Escopo mínimo por iteração:** cada iteração entrega somente o que seus critérios objetivos de aceitação exigem; nada além (feature creep é cortado imediatamente).
2. **Diferencial opcional só com evidência:** o diferencial (ex.: modelo preditivo, dashboard) é opcional e só entra se (a) o time budget permitir e (b) houver evidência real de sinal nos dados — a Iteração 05 testa o baseline antes de qualquer alegação. Sem evidência, o diferencial **não** é construído e o "o que NÃO fazer" documenta a decisão.
3. **Revisores em paralelo:** a revisão 3x read-only após cada iteração é **obrigatória** (exigência do candidato, regra 2 acima) e roda em paralelo — 3 agentes de uma vez, custo de 1 passada de relógio, nunca em série.
4. **Correções apenas materiais:** o agente de correção sequencial trata findings materiais (erros factuais, violações de regra, claims falsas, risco de reprovação). Findings LOW/de redação podem ser aceitos com justificativa no review summary ou corrigidos no mesmo passe — sem passadas extras por iteração além do necessário.
5. **Stop conditions:** (a) iteração estourando sua fatia de tempo → orquestrador reduz escopo (validações opcionais) e segue; (b) acumulado ultrapassando ~5h antes da Iteração 09 → orquestrador funde/trim escopo (ex.: Iterações 06–07) — **nunca** sacrificando: 1 comando reproduzível (It06), relatório executivo (It07), process log (It08), QA final (It09); (c) artefatos concisos: reports de iteração curtos e objetivos, 4–6 visualizações com significado, sem documentos longos.
6. **Registro de tempo:** cada report de iteração registra o tempo de relógio da etapa; o orquestrador mantém o acumulado no checklist (item F11) e decide cortes com base nele.

---

## 3. Estrutura de governança (arquivos de controle)

| Arquivo | Papel |
|---|---|
| `process-log/management/execution-plan.md` | Este plano; estados por iteração |
| `process-log/management/orchestrator-checklist.md` | Checklist interno do orquestrador (estados por item) |
| `process-log/reports/iteration-XX-*.md` | Report estruturado ao fim de cada iteração |
| `process-log/prompts/iteration-XX-prompt.md` | Prompt integral recebido pelo agente executor de cada iteração |

---

## 4. Iterações

> Cada iteração registra: objetivo, entradas, artefatos esperados, critérios objetivos de aceitação, validações, commit esperado, dependências e status.

### Iteração 00 — Planejamento e governança

- **Status:** `CONCLUDED` (2026-08-28) — review gate 3x realizado (3 veredictos `PASS_WITH_FIXES`, read-only) e correções aplicadas por agente sequencial; registro em `process-log/reviews/iteration-00-review-summary.md`
- **Objetivo:** estabelecer a arquitetura mínima de gestão da submissão (plano de execução, checklist do orquestrador, report da iteração), corrigir informação incorreta no README scaffold (ferramenta alegada) e versionar/pushar a base de governança.
- **Entradas:** instruções oficiais (README.md, CONTRIBUTING.md, submission-guide.md, challenges/data-001-churn/README.md, templates/submission-template.md); scaffold existente da pasta do candidato; estado do repo (branch, remotes, log); presença dos 5 CSVs em `/tmp/opencode/ravendata/` (inspeção de presença/contagem/checksum, sem análise).
- **Artefatos esperados:**
  - `process-log/management/execution-plan.md`
  - `process-log/management/orchestrator-checklist.md`
  - `process-log/reports/iteration-00-planning-report.md`
  - `process-log/prompts/iteration-00-prompt.md`
  - `README.md` (correção de 1 linha na tabela "Ferramentas usadas")
  - remoção de `process-log/.gitkeep` (substituído por arquivos reais)
- **Critérios objetivos de aceitação:**
  - Os 3 documentos de governança existem e não são placeholders vazios.
  - Estados: Iteração 00 `CONCLUDED`; Iterações 01–10 `PENDING`.
  - Checklist não afirma nada ainda não realizado.
  - README scaffold não alega mais ferramenta incorreta ("Claude Code/deepseek-v4-flash" removido; processo real descrito: opencode + subagentes deepseek-max).
  - Nenhum arquivo fora de `submissions/jose-nascimento/` alterado.
  - `git diff --check` limpo; commit semântico; push para `origin/submission/jose-nascimento`.
- **Validações:** leitura integral das 5 instruções oficiais; inspeção de branch/remotes/status/log; checagem de estados válidos (`PENDING|OPEN|CONCLUDED`) por script; `git diff --check`; grep de nomes de análises públicas do dataset e termos de baseline na pasta (zero ocorrências; exceção documentada: prompt arquivado referencia paths de pesquisa interna por transparência — ver regra 8); `git status` final e tracking do remote.
- **Commit esperado:** `docs: establish execution plan and governance`
- **Dependências:** nenhuma (ponto de partida).

### Iteração 01 — Ingestão e auditoria dos 5 datasets

- **Status:** `CONCLUDED` (2026-08-28) — implementação validada pelo executor (exit 0; 72 PASS / 18 WARN / 0 FAIL; idempotência byte-a-byte; 3 verificações manuais; commit `feat: ingest and audit RavenStack datasets`). Review gate 3x: a disparar pelo orquestrador (rastreado à parte, regra 4).
- **Objetivo:** ingerir os 5 CSVs de forma reproduzível e auditar cada tabela contra o brief: contagens, schema, chaves, nulos, duplicatas, janelas de data válidas, consistência de tipos e unidades; declarar com evidência a natureza sintética/gerada dos dados; gravar relatório de auditoria com gates.
- **Entradas:** CSVs em `/tmp/opencode/ravendata/`; brief do challenge (tabelas esperadas); checksums capturados na Iteração 00.
- **Artefatos esperados:** `data/raw/` (5 CSVs commitados, licença MIT); `src/01_ingest_audit.py`; `evidence/01_audit_report.md`; entrada no process log.
- **Critérios objetivos de aceitação:** contagem real vs brief documentada por tabela; schema/nulos/duplicatas/chaves reportados; janelas de data inválidas identificadas; parecer de sinteticidade com evidência concreta (ex.: distribuições, duplicatas, valores); gates FAIL/PASS; relatório em markdown com números reproduzíveis.
- **Validações:** re-execução do script; conferência manual de 3 achados; `git diff --check`.
- **Commit esperado:** `feat: ingest and audit the five RavenStack datasets`
- **Dependências:** Iteração 00.

### Iteração 02 — Reconciliação das definições/grãos de churn e contrato analítico

- **Status:** `PENDING`
- **Objetivo:** reconciliar as diferentes fontes de "churn" entre tabelas (flag de conta, flag/fim de assinatura, eventos de churn), quantificar as divergências, definir **uma** definição de churn point-in-time com justificativa, fixar o grão-mestre (account-month com regra de assinatura vencedora), e congelar o contrato analítico (métricas, janelas, invariantes de contagem e MRR, scoreboard mensal) que todas as iterações seguintes usam.
- **Entradas:** outputs da Iteração 01; brief; contrato analítico proposto nesta iteração.
- **Artefatos esperados:** `src/02_consistency.py` (reconciliação + checks de invariante); `evidence/02_consistency_report.md`; `docs/analytical-contract.md` (definição de churn, grão, métricas, janelas, decisões "minha vs consenso vs IA").
- **Critérios objetivos de aceitação:** divergências entre fontes quantificadas com números; definição única adotada e justificada; grão account-month definido; checks de invariante (contagem e MRR) passando; CSAT/reason codes marcados como evidência sugestiva (não prova) no contrato; nenhuma conclusão posterior contradiz o contrato.
- **Validações:** re-execução; conferência manual de 3 achados; `git diff --check`.
- **Commit esperado:** `feat: reconcile churn definitions and freeze analytical contract`
- **Dependências:** Iteração 01.

### Iteração 03 — Causa raiz, coortes e onboarding economics

- **Status:** `PENDING`
- **Objetivo:** registrar hipóteses **antes** da análise; testar cada hipótese com números (coortes por período de signup, tempo-para-churn com censoring, comparações alinhadas no tempo); identificar e quantificar o(s) fenômeno(s) central(is) de churn — inclusive padrões temporais e o custo do churn precoce (onboarding economics) com premissas explícitas e em faixa; distinguir correlação de causalidade em cada afirmação.
- **Entradas:** contrato analítico (Iteração 02); auditoria (Iteração 01).
- **Artefatos esperados:** `src/03_eda.py`; `evidence/03_hypotheses.md` (registradas antes da execução); `evidence/03_insights.md`; `out/charts/` (4–6 visualizações com significado); entrada no process log com rótulos de correlação/causalidade.
- **Critérios objetivos de aceitação:** hipóteses versionadas antes da análise; cada hipótese com veredito (sustentada/refutada) e número; análises com censoring e alinhamento temporal (sem viés de sobrevivência); premissas do onboarding economics nomeadas e em faixa; nenhuma afirmação causal sem rótulo.
- **Validações:** re-execução; conferência manual de 3 achados; `git diff --check`.
- **Commit esperado:** `feat: root-cause, cohort and onboarding economics analysis`
- **Dependências:** Iterações 01–02.

### Iteração 04 — Ciclos de reativação, jornada completa da conta e watchlist

- **Status:** `PENDING`
- **Objetivo:** reconstruir a jornada completa de cada conta (todas as assinaturas, múltiplas entradas/saídas, ciclos de reativação e re-churn); medir receita acumulada vs perda; derivar watchlist de contas específicas em risco (contas reais com MRR, sinal e ação recomendada); declarar regras de cap/agregação e advertências de viés (ex.: contas novas).
- **Entradas:** contrato analítico; outputs das Iterações 01–03.
- **Artefatos esperados:** `src/04_journey.py`; `out/accounts_at_risk.csv` (watchlist); `evidence/04_journey_report.md`; gráficos da jornada.
- **Critérios objetivos de aceitação:** watchlist com contas reais (ID, MRR, sinal, ação); regra de agregação/cap explícita e justificada; viés contra contas novas declarado; reativações quantificadas (frequência, re-churn); números reproduzíveis.
- **Validações:** re-execução; conferência manual de 3 contas da watchlist; `git diff --check`.
- **Commit esperado:** `feat: account journey, reactivation cycles and risk watchlist`
- **Dependências:** Iterações 01–03.

### Iteração 05 — Recomendações, impacto estimado, priorização e causalidade

- **Status:** `PENDING`
- **Objetivo:** converter achados em 3–5 ações concretas priorizadas (matriz impacto × esforço), cada uma com impacto estimado **em faixa paramétrica** e premissas nomeadas (nunca número único sem origem); rotular explicitamente correlação vs causalidade em todas as recomendações; declarar o que **não** deve ser feito (ex.: modelo preditivo sem sinal, automação de risco) com justificativa.
- **Entradas:** achados das Iterações 03–04; contrato analítico.
- **Artefatos esperados:** `src/05_recommendations.py`; `out/action_plan_priorizado.csv`; `evidence/05_recommendations.md`.
- **Critérios objetivos de aceitação:** cada ação com custo × retorno × prazo; impacto em faixa com premissas nomeadas e origem (arquivo:linha); cada afirmação rotulada (correlação observada / hipótese causal / evidência); seção explícita de "o que não fazer".
- **Validações:** re-execução; conferência manual de 3 números; `git diff --check`.
- **Commit esperado:** `feat: prioritized recommendations with impact ranges`
- **Dependências:** Iterações 03–04.

### Iteração 06 — Artefato reproduzível e validação técnica

- **Status:** `PENDING`
- **Objetivo:** garantir que toda a análise rode do zero com **1 comando** (`./run.sh` ou `make all`), sem rede e sem dependência externa (CSVs já commitados); adicionar validação técnica (testes de invariantes, verificação de que outputs são determinísticos e batem com os relatórios).
- **Entradas:** scripts 01–05; dados commitados.
- **Artefatos esperados:** `run.sh`/`Makefile`; `requirements.txt` atualizado; testes de validação; `evidence/06_validation_report.md` (log de execução do zero).
- **Critérios objetivos de aceitação:** execução limpa em ambiente sem rede; 1 comando reproduz todos os outputs; outputs idênticos entre execuções; docs ↔ código consistentes; nenhum binário/`.duckdb`/`.db` commitado.
- **Validações:** execução em clone limpo (fora do repo); comparação de outputs; `git diff --check`.
- **Commit esperado:** `feat: one-command reproducible pipeline with validation`
- **Dependências:** Iterações 01–05.

### Iteração 07 — Relatório executivo e visualizações

- **Status:** `PENDING`
- **Objetivo:** produzir o relatório executivo (markdown + HTML estático) orientado ao CEO não-técnico: resposta primeiro (causa + custo + pedido), como o churn foi definido, causa raiz, segmentos em risco com contas específicas, ações priorizadas com impacto em faixa, limitações e apêndice com a derivação de cada número (arquivo:linha).
- **Entradas:** achados e recomendações (Iterações 03–05); visualizações geradas.
- **Artefatos esperados:** `out/report_executivo.md` e `.html`; 4–6 visualizações; preenchimento do `README.md` da submissão (template oficial).
- **Critérios objetivos de aceitação:** CEO não-técnico consegue ler e agir; cada número tem origem rastreável; visualizações com significado (sem variância ~0 apresentada como insight); README segue o template oficial.
- **Validações:** leitura crítica do relatório por outro agente (parte da revisão 3x); conferência de 5 números contra o pipeline; `git diff --check`.
- **Commit esperado:** `docs: executive report and visualizations`
- **Dependências:** Iterações 03–06.

### Iteração 08 — Process log e evidências reais

- **Status:** `PENDING`
- **Objetivo:** consolidar o process log com evidências reais e auditáveis: prompts literais por fase (em `process-log/prompts/`), erros reais da IA com causa raiz e correção aplicada (5–8, nunca "não houve erros"), decisões "minha vs consenso vs IA", hipóteses antes da IA, momentos em que o julgamento humano corrigiu a ferramenta.
- **Entradas:** exports/prompts coletados durante as Iterações 01–07; decisões registradas.
- **Artefatos esperados:** `process-log/` completo (prompts literais, `ai-errors-fixed.md`, `decisions-log.md`, `hypotheses.md`, evidências em texto).
- **Critérios objetivos de aceitação:** todo item marcado no README/checklist corresponde a arquivo commitado (zero checkbox fantasma); prompts literais; erros com causa raiz e correção; nenhuma alegação sem suporte.
- **Validações:** verificação arquivo-a-arquivo; conferência de que o arco da iteração está documentado (não só o estado final); `git diff --check`.
- **Commit esperado:** `docs: process log with evidence and human judgment`
- **Dependências:** Iterações 01–07.

### Iteração 09 — QA final integral contra as instruções oficiais

- **Status:** `PENDING`
- **Objetivo:** revisar a entrega inteira contra todas as instruções oficiais (README, CONTRIBUTING, submission-guide, challenge README, template) e contra o `orchestrator-checklist.md`: estrutura de pastas, reprodutibilidade, hygiene, consistência docs ↔ código, originalidade (zero referências a análises públicas), estados do plano, autor dos commits, escopo de alterações.
- **Entradas:** submissão completa; checklist do orquestrador; instruções oficiais.
- **Artefatos esperados:** `process-log/reports/iteration-09-qa-final-report.md`; checklist 100% preenchido com evidência.
- **Critérios objetivos de aceitação:** checklist integral verificado (todo item `CONCLUDED` ou justificado); nenhum arquivo fora da pasta em todo o histórico; `git diff --check` limpo; 1 comando reproduz do zero; números do relatório conferem com o pipeline.
- **Validações:** auditoria arquivo-a-arquivo; re-execução limpa; grep de originalidade; `git log` completo.
- **Commit esperado:** `chore: final QA against official instructions`
- **Dependências:** Iterações 00–08.

### Iteração 10 — Git e PR final

- **Status:** `PENDING`
- **Objetivo:** garantir commits semânticos e autor do candidato em todo o histórico, push final e abertura do Pull Request conforme CONTRIBUTING.md.
- **Entradas:** submissão QA-aprovada (Iteração 09).
- **Artefatos esperados:** Pull Request para `main` com título `[Submission] Jose Nascimento — Challenge 001`; descrição com resumo e navegação dos artefatos.
- **Critérios objetivos de aceitação:** PR contém apenas arquivos de `submissions/jose-nascimento/`; título no formato oficial; commits semânticos com autor do candidato; histórico auditável (vários commits, não 1 único gigante).
- **Validações:** `git log`; `git diff main...branch --stat` (escopo); conferência do título/descrição.
- **Commit esperado:** `docs: finalize submission` (push final e abertura do PR)
- **Dependências:** Iteração 09.

---

## 5. Definição de pronto da submissão

1. Relatório de diagnóstico responde às 3 perguntas do challenge (causa raiz, segmentos com contas específicas, ações priorizadas com impacto estimado).
2. Dados cruzados entre as 5 tabelas; números verificáveis; correlação vs causalidade distinguida.
3. Process log obrigatório com evidências reais em texto.
4. Reproduzível com 1 comando, offline, a partir do clone.
5. QA integral contra as instruções oficiais aprovado (Iteração 09).
6. PR aberto com título oficial e apenas arquivos da pasta do candidato.