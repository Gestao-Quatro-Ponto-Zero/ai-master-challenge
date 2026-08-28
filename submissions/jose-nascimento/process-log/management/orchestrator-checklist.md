# Checklist do Orquestrador — Challenge 001 (Diagnóstico de Churn · RavenStack)

**Finalidade:** checklist interno, exaustivo porém operacional, usado pelo orquestrador (opencode) para governar a submissão de Jose Nascimento. Estados válidos: `PENDING` (não realizado), `OPEN` (em andamento), `CONCLUDED` (realizado com evidência). **Nenhum item pode afirmar algo ainda não realizado.** Atualizado ao fim de cada iteração.

**Última atualização:** 2026-08-28 (fim da Iteração 03 — hipóteses commitadas antes da análise, implementação validada; review gate 3x a disparar; ver `process-log/reports/iteration-03-root-cause-report.md`)

---

## A. Regras oficiais e estrutura

| # | Item | Estado | Evidência / nota |
|---|---|---|---|
| A1 | README.md oficial lido na íntegra | CONCLUDED | Leitura integral; ver Iteração 00 report |
| A2 | CONTRIBUTING.md lido na íntegra | CONCLUDED | Leitura integral; ver Iteração 00 report |
| A3 | submission-guide.md lido na íntegra | CONCLUDED | Leitura integral; ver Iteração 00 report |
| A4 | challenges/data-001-churn/README.md lido na íntegra | CONCLUDED | Leitura integral; ver Iteração 00 report |
| A5 | templates/submission-template.md lido | CONCLUDED | Leitura integral; ver Iteração 00 report |
| A6 | Pasta correta `submissions/jose-nascimento/` (plural, conforme tooling oficial) | CONCLUDED | Verificado na Iteração 00 (git ls-files/status) |
| A7 | Nenhum arquivo fora da pasta alterado — verificação da iteração corrente | CONCLUDED | Verificado na Iteração 00 via `git status`/`git diff` (working tree limpo antes e depois) |
| A8 | Nenhum arquivo fora da pasta alterado — verificação em TODAS as iterações | PENDING | Re-executar ao fim de cada iteração e no QA final (Iteração 09) |
| A9 | README da submissão segue o template oficial | CONCLUDED | Scaffold baseado em `templates/submission-template.md` (verificado na Iteração 00) |
| A10 | README da submissão preenchido com conteúdo final | PENDING | Iteração 07 |
| A11 | Título do PR no formato oficial `[Submission] Jose Nascimento — Challenge 001` | PENDING | Iteração 10 |
| A12 | Descrição do PR com resumo e navegação dos artefatos | PENDING | Iteração 10 |

## B. Processo e ferramenta

| # | Item | Estado | Evidência / nota |
|---|---|---|---|
| B1 | Ferramenta real documentada com honestidade (opencode como orquestrador + subagentes `deepseek-max` via OpenCode Go; NÃO "Claude Code", NÃO "deepseek-v4-flash" como ferramenta) | CONCLUDED | Correção aplicada no README scaffold (Iteração 00); docs de governança usam a mesma descrição |
| B2 | Uma etapa = um agente `deepseek-max` sequencial | CONCLUDED | Iteração 00 executada por exatamente um subagente `deepseek-max` (via OpenCode Go), sob orquestração do opencode (que não implementa); regra vigente para as Iterações 01–10 (verificação ao fim de cada etapa) |
| B3 | Revisão 3x read-only após cada etapa (3 agentes `deepseek-max` em paralelo) | CONCLUDED | Iteração 00: 3 revisores `deepseek-max` read-only em paralelo (2026-08-28), veredictos `PASS_WITH_FIXES` ×3; correções aplicadas por agente sequencial (commit `docs: address iteration 00 review findings`); registro em `process-log/reviews/iteration-00-review-summary.md`. Iteração 01: 3 revisores `deepseek-max` read-only em paralelo (2026-08-28), veredictos `PASS_WITH_FIXES` ×3; finding MEDIUM M1 (schema quebrado → `KeyError` + relatório stale) corrigido por agente sequencial (commit `fix: handle schema failures in data audit`); registro em `process-log/reviews/iteration-01-review-summary.md`. Iteração 02: 3 revisores `deepseek-max` read-only em paralelo (2026-08-28), veredictos `PASS` ×2 e `PASS_WITH_FIXES` ×1; findings materiais M1 (lente de revenue churn degenerada) e M2 (números hardcoded) corrigidos por agente sequencial (commit `fix: strengthen revenue churn contract`), junto com política de `closed_at` (D10) e LOWs baratos; registro em `process-log/reviews/iteration-02-review-summary.md`. Iteração 03: review gate a disparar pelo orquestrador (ledger `process-log/reviews/iteration-03-review-summary.md` a criar). Revisões das Iterações 03–10: a disparar ao fim de cada etapa |
| B4 | Correções por agente sequencial quando revisores apontarem problemas materiais | CONCLUDED | Iteração 00: correções materiais aplicadas pelo agente corretor sequencial `deepseek-max` (ver B3); demais iterações: disparo conforme necessidade após cada revisão 3x |
| B5 | Toda etapa produz report estruturado em `process-log/reports/` | CONCLUDED | Report da Iteração 00 criado; padrão de naming `iteration-XX-*.md` |
| B6 | Prompt integral de cada iteração arquivado em `process-log/prompts/` | CONCLUDED | Prompt da Iteração 00 arquivado; prompt de correção do review gate arquivado; demais iterações seguem o padrão |
| B7 | Estados do execution-plan atualizados ao fim de cada etapa, somente `PENDING/OPEN/CONCLUDED` | CONCLUDED | Iteração 00: 00 `CONCLUDED`, 01–10 `PENDING`; validado por script |
| B8 | Orquestrador não implementa código (apenas gerencia agentes) | PENDING | Regra contínua; verificação ao fim de cada iteração |
| B9 | Ferramentas de IA listadas no process log com o que fizeram | PENDING | Iteração 08 |
| B10 | Review gate 3x registrado em ledger versionado `process-log/reviews/iteration-XX-review-summary.md` | CONCLUDED | Iteração 00: `iteration-00-review-summary.md` criado (veredictos, findings, decisão de governança, matriz finding→ação, riscos, gate); Iteração 01: `iteration-01-review-summary.md` criado (3 veredictos `PASS_WITH_FIXES`, finding convergente M1, matriz finding→ação→arquivo:linha, recálculos, testes pós-fix, riscos, gate); Iteração 02: `iteration-02-review-summary.md` criado (3 veredictos `PASS`/`PASS`/`PASS_WITH_FIXES`, findings M1/M2, matriz finding→ação→arquivo:linha, decisão sobre o winner, recálculos 46/46, testes pós-fix, riscos, gate `CONCLUDED`); demais iterações seguem o padrão |

## C. Dados e licenciamento

| # | Item | Estado | Evidência / nota |
|---|---|---|---|
| C1 | Dataset oficial identificado: Kaggle "SaaS Subscription & Churn Analytics", licença MIT | CONCLUDED | Declarado no brief do challenge (lido na Iteração 00) |
| C2 | 5 CSVs reais commitados em `data/raw/` para reprodutibilidade offline | CONCLUDED | Iteração 01: `solution/data/raw/ravenstack_*.csv` commitados (cópia byte-for-byte; MD5 iguais à origem e aos checksums da Iteração 00; contagens 500/5.000/25.000/2.000/600; `data/raw/README.md` com origem/licença/checksums) |
| C3 | Zero dependência de rede (wget/kagglehub/download) no pipeline | CONCLUDED | Iteração 01: script `src/01_ingest_audit.py` usa apenas stdlib+pandas, lê de `data/raw/` por path relativo; nenhuma chamada de rede (inspeção de imports). Re-verificar na Iteração 06 |
| C4 | Natureza sintética/gerada dos dados declarada com evidência (não apenas afirmada) | CONCLUDED | Iteração 01: parecer com evidência objetiva no `evidence/01_audit_report.md` §5 (esquema de IDs, distribuições quase uniformes, uso mensal uniforme 24 meses, 76,6% do uso fora da janela da assinatura, ARR=12×MRR em 100%, CSAT {3,4,5}); sem extrapolação de causa de negócio |
| C5 | Atribuição/licença do dataset mencionada no README final | PENDING | Iteração 07 (já registrada em `data/raw/README.md`) |
| C6 | Nenhum artefato binário de dados commitado (`.duckdb`, `.db`, `.sqlite`) | PENDING | Verificação contínua; Iteração 06 e 09 |

## D. Auditoria e análise

| # | Item | Estado | Evidência / nota |
|---|---|---|---|
| D1 | Auditoria das 5 tabelas vs brief: contagens, schema, chaves, nulos, duplicatas, janelas de data | CONCLUDED | Iteração 01: `solution/evidence/01_audit_report.md` — 72 PASS / 18 WARN / 0 FAIL, exit 0; contagens 500/5.000/25.000/2.000/600 iguais ao brief; FKs sem órfãos; 3 verificações manuais independentes (MV1/MV2/MV3 no report da iteração) |
| D2 | Reconciliação das definições de churn entre tabelas; definição única point-in-time justificada | CONCLUDED | Iteração 02: lente primária POR pergunta no contrato (`solution/docs/analytical-contract.md` §4); divergências 35/277/125 recalculadas (75/227/50 Venn) em `solution/evidence/02_consistency_report.md` §3; decisões D1–D8 em `process-log/decisions/iteration-02-analytical-contract-decisions.md`. Pós-gate: duas lentes de receita nomeadas (R1 gross ending MRR / R2 net account-state MRR loss — contrato §5, decisão D9) e política de `closed_at` (contrato §7/§10, decisão D10) |
| D3 | Grão-mestre account-month com regra de assinatura vencedora; sem contagens dobradas | CONCLUDED | Iteração 02: `solution/data/processed/account_month.csv` (5.807 linhas, 1 por account×mês); winner determinístico (não-trial, max MRR, start recente, id); soma ingênua vs winner = 2,16× (report §6); invariantes G1–G13. Pós-gate: colunas auditáveis `mrr_ended_in_month`/`n_ended_in_month` (lente R1) e invariante G14 (1.179.139/486/427 vs fonte); invariantes agora G1–G15 |
| D4 | Checks de invariante (contagem e MRR) com gates FAIL/PASS | CONCLUDED | Iteração 02: G1–G15 em `solution/evidence/02_consistency_report.md` §9 (31 PASS / 1 WARN esperado / 0 FAIL); transições fecham com tolerância 0 (contagem e MRR); gross ending MRR reconciliado à fonte (G14); política de `closed_at` (G15); falha estrutural → exit 1 + relatório regravado (3 cenários sandbox) |
| D5 | CSAT/reason codes tratados como evidência sugestiva, nunca prova | CONCLUDED | Iteração 02: contrato §10 (domínio {3,4,5}, 41,2% nulos; reason 'unknown' 95; feedback 148 nulos — derivados em runtime); resolução/CSAT apenas com tickets fechados, `closed_at` nulo excluído com denominador explícito, nunca imputar fechamento futuro; relações futuras rotuladas como correlação (It03–05) |
| D6 | Números verificáveis com origem rastreável (arquivo:linha no apêndice) | OPEN | Iteração 03: números do report rastreáveis às tabelas `out/tables/t01–t10` e verificação report↔CSV executada; apêndice consolidado na Iteração 07 |
| D7 | Correlação vs causalidade rotulada em cada afirmação | OPEN | Iteração 03: tabela de causalidade gerada (descritivo / hipótese causal plausível / não identificável + confundidores + dado adicional) no `03_root_cause_report.md` §9; consolidação final na Iteração 05 |
| D8 | Contas específicas em risco (watchlist com ID real, MRR, sinal, ação) | PENDING | Iteração 04 |
| D9 | Impacto estimado em faixa paramétrica com premissas nomeadas (nunca número único sem origem) | PENDING | Iteração 05 |
| D10 | Seção explícita do que NÃO fazer (ex.: modelo preditivo sem sinal, automação de risco) | PENDING | Iteração 05 |
| D11 | Limitações explícitas (o que não é calculável com essa base) | PENDING | Iteração 05 e 07 |
| D12 | Hipóteses registradas ANTES da análise com IA | CONCLUDED | Iteração 03: H1–H10 pré-registradas com threshold fixado antes de ver resultados (`process-log/hypotheses/iteration-03-root-cause-hypotheses.md`), commitadas/pushadas ANTES do código (commit `docs: define churn hypotheses before analysis`, hash `8cb93c3`, 2026-08-28T20:28:42Z); timeline no report da iteração §2 |
| D13 | Decisões documentadas "minha vs consenso vs IA" | PENDING | Iteração 08 |
| D14 | Erros reais da IA com causa raiz e correção aplicada (5–8; nunca "não houve erros") | PENDING | Iteração 08 |

## E. Originalidade

| # | Item | Estado | Evidência / nota |
|---|---|---|---|
| E1 | Zero referências/citações a análises públicas do mesmo dataset ou a outras submissões **nas entregas da solução** | CONCLUDED | Grep na Iteração 00 (term-list: nomes de análises públicas do dataset e termos de baseline): zero ocorrências; zero cópia/citação de conclusões nos artefatos. Exceção documentada: o prompt de gestão arquivado (`process-log/prompts/iteration-00-prompt.md:19-24`) referencia por path os materiais de pesquisa interna — evidência de processo/transparência, não citação de conclusão (ver decisão de governança no review summary). Re-verificar no QA final (Iteração 09) |
| E2 | Números re-executados pelo próprio pipeline (nada copiado de fonte externa) | PENDING | Iterações 01–06, verificado na 09 |
| E3 | Narrativa, estrutura e visualizações com voz própria (não replicam baseline) | PENDING | Iterações 03–07 |
| E4 | Achados apresentados como descoberta do processo (hipótese → teste → resultado) | PENDING | Iterações 03–05 e 08 |

## F. Higiene, git e entrega

| # | Item | Estado | Evidência / nota |
|---|---|---|---|
| F1 | `.gitignore` adequado desde o início (sem node_modules/venv/pycache/binários) | CONCLUDED | `.gitignore` da pasta commitado no commit inicial do scaffold (1f3017a) |
| F2 | Zero segredos e chaves commitados; paths pessoais monitorados (exceção documentada) | CONCLUDED | Verificação por iteração. Iteração 01: grep nos artefatos da solução por `/tmp`, `/home`, `ubuntu` → zero ocorrências fora do prompt arquivado (exceção documentada da Iteração 00). Iteração 02: re-verificado — idem (ocorrências apenas no prompt arquivado). Iteração 03: re-verificado — idem. Re-verificar em toda iteração |
| F3 | Commits semânticos incrementais (vários, não 1 único gigante) | PENDING | Em curso: scaffold + governança + It01 (2 commits) + It02 (1 commit) já semânticos; 8–10+ commits esperados até o fim |
| F4 | Autor do candidato em todos os commits (sem alterar git config) | CONCLUDED | Verificado: scaffold `Jose Nascimento <322186960+josenascimento1@users.noreply.github.com>`; identidade reutilizada nesta iteração |
| F5 | Setup com 1 comando (`./run.sh` ou `make all`), offline, do clone limpo | PENDING | Iteração 06 |
| F6 | Notebook/saídas com outputs renderizados como evidência visual | PENDING | Iteração 06/07 |
| F7 | Evidências em texto puro (markdown/CSV/JSONL); zero PDF/DOCX/JPEG como fonte primária de evidência | PENDING | Iteração 08 e 09 |
| F8 | Checklist do README marcado somente com arquivos commitados (zero checkbox fantasma) | PENDING | Iteração 08/09 |
| F9 | QA final integral contra todas as instruções oficiais | PENDING | Iteração 09 |
| F10 | Reprovação por hygiene evitável: `git diff --check` limpo em todo commit | CONCLUDED | Executado no commit da Iteração 00 e re-executado nas Iterações 01, 02 e 03; re-executar em toda iteração |
| F11 | Controle de time budget (4–6h): acumulado registrado por iteração; cortes conforme política do execution-plan §2 | PENDING | Iteração 01: ~55 min. Iteração 02: ~1h55min (leitura + exploração + script + 7 correções + 3 verificações manuais + sandbox + validações). Correção do gate It02: ~1h40min (3 revisões + exploração de dados + implementação M1/M2/closed_at + verificação independente 46/46 + sandbox + documentos). Iteração 03: ~1h20min (hipóteses + script + 6 correções + MV 3/3 + sandbox + validações + documentos). Acumulado analítico ~5h45; orquestrador mantém o controle e decide cortes |

---

## Notas de manutenção

- Este checklist é atualizado pelo orquestrador ao fim de **cada iteração**, antes da revisão 3x.
- Itens com estado `CONCLUDED` podem voltar a `OPEN`/`PENDING` se uma revisão encontrar problema material.
- A revisão 3x da Iteração 00 foi concluída em 2026-08-28 (3 veredictos `PASS_WITH_FIXES`, correções aplicadas por agente sequencial) — ver `process-log/reviews/iteration-00-review-summary.md`; o estado de B3 acima reflete isso, e a semântica de `CONCLUDED` (execução validada pelo executor) vs review gate (rastreado à parte) está definida no execution-plan, regra 4.