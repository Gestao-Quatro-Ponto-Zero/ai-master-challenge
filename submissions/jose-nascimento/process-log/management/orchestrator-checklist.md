# Checklist do Orquestrador — Challenge 001 (Diagnóstico de Churn · RavenStack)

**Finalidade:** checklist interno, exaustivo porém operacional, usado pelo orquestrador (opencode) para governar a submissão de Jose Nascimento. Estados válidos: `PENDING` (não realizado), `OPEN` (em andamento), `CONCLUDED` (realizado com evidência). **Nenhum item pode afirmar algo ainda não realizado.** Atualizado ao fim de cada iteração.

**Última atualização:** 2026-08-28 (fim da Iteração 00)

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
| B2 | Uma etapa = um agente `deepseek-max` sequencial | PENDING | A partir da Iteração 01 (Iteração 00 executada pelo agente executor designado) |
| B3 | Revisão 3x read-only após cada etapa (3 agentes `deepseek-max` em paralelo) | PENDING | Pendente inclusive para a Iteração 00 — a ser disparada pelo orquestrador após este report |
| B4 | Correções por agente sequencial quando revisores apontarem problemas materiais | PENDING | Disparado conforme necessidade após cada revisão 3x |
| B5 | Toda etapa produz report estruturado em `process-log/reports/` | CONCLUDED | Report da Iteração 00 criado; padrão de naming `iteration-XX-*.md` |
| B6 | Prompt integral de cada iteração arquivado em `process-log/prompts/` | CONCLUDED | Prompt da Iteração 00 arquivado; demais iterações seguem o padrão |
| B7 | Estados do execution-plan atualizados ao fim de cada etapa, somente `PENDING/OPEN/CONCLUDED` | CONCLUDED | Iteração 00: 00 `CONCLUDED`, 01–10 `PENDING`; validado por script |
| B8 | Orquestrador não implementa código (apenas gerencia agentes) | PENDING | Regra contínua; verificação ao fim de cada iteração |
| B9 | Ferramentas de IA listadas no process log com o que fizeram | PENDING | Iteração 08 |

## C. Dados e licenciamento

| # | Item | Estado | Evidência / nota |
|---|---|---|---|
| C1 | Dataset oficial identificado: Kaggle "SaaS Subscription & Churn Analytics", licença MIT | CONCLUDED | Declarado no brief do challenge (lido na Iteração 00) |
| C2 | 5 CSVs reais commitados em `data/raw/` para reprodutibilidade offline | PENDING | Iteração 01 |
| C3 | Zero dependência de rede (wget/kagglehub/download) no pipeline | PENDING | Iteração 01 e 06 |
| C4 | Natureza sintética/gerada dos dados declarada com evidência (não apenas afirmada) | PENDING | Iteração 01 |
| C5 | Atribuição/licença do dataset mencionada no README final | PENDING | Iteração 07 |
| C6 | Nenhum artefato binário de dados commitado (`.duckdb`, `.db`, `.sqlite`) | PENDING | Verificação contínua; Iteração 06 e 09 |

## D. Auditoria e análise

| # | Item | Estado | Evidência / nota |
|---|---|---|---|
| D1 | Auditoria das 5 tabelas vs brief: contagens, schema, chaves, nulos, duplicatas, janelas de data | PENDING | Iteração 01 |
| D2 | Reconciliação das definições de churn entre tabelas; definição única point-in-time justificada | PENDING | Iteração 02 |
| D3 | Grão-mestre account-month com regra de assinatura vencedora; sem contagens dobradas | PENDING | Iteração 02 |
| D4 | Checks de invariante (contagem e MRR) com gates FAIL/PASS | PENDING | Iteração 02 e 06 |
| D5 | CSAT/reason codes tratados como evidência sugestiva, nunca prova | PENDING | Iteração 02 (contrato) e 03 |
| D6 | Números verificáveis com origem rastreável (arquivo:linha no apêndice) | PENDING | Iterações 03–05, consolidado na 07 |
| D7 | Correlação vs causalidade rotulada em cada afirmação | PENDING | Iterações 03 e 05 |
| D8 | Contas específicas em risco (watchlist com ID real, MRR, sinal, ação) | PENDING | Iteração 04 |
| D9 | Impacto estimado em faixa paramétrica com premissas nomeadas (nunca número único sem origem) | PENDING | Iteração 05 |
| D10 | Seção explícita do que NÃO fazer (ex.: modelo preditivo sem sinal, automação de risco) | PENDING | Iteração 05 |
| D11 | Limitações explícitas (o que não é calculável com essa base) | PENDING | Iteração 05 e 07 |
| D12 | Hipóteses registradas ANTES da análise com IA | PENDING | Iteração 03 |
| D13 | Decisões documentadas "minha vs consenso vs IA" | PENDING | Iteração 08 |
| D14 | Erros reais da IA com causa raiz e correção aplicada (5–8; nunca "não houve erros") | PENDING | Iteração 08 |

## E. Originalidade

| # | Item | Estado | Evidência / nota |
|---|---|---|---|
| E1 | Zero referências/citações a análises públicas do mesmo dataset ou a outras submissões | CONCLUDED | Grep de nomes/termos conhecidos na pasta na Iteração 00: zero ocorrências; re-verificar no QA final |
| E2 | Números re-executados pelo próprio pipeline (nada copiado de fonte externa) | PENDING | Iterações 01–06, verificado na 09 |
| E3 | Narrativa, estrutura e visualizações com voz própria (não replicam baseline) | PENDING | Iterações 03–07 |
| E4 | Achados apresentados como descoberta do processo (hipótese → teste → resultado) | PENDING | Iterações 03–05 e 08 |

## F. Higiene, git e entrega

| # | Item | Estado | Evidência / nota |
|---|---|---|---|
| F1 | `.gitignore` adequado desde o início (sem node_modules/venv/pycache/binários) | CONCLUDED | `.gitignore` da pasta commitado no commit inicial do scaffold (1f3017a) |
| F2 | Zero segredos, chaves ou paths pessoais commitados | PENDING | Verificação por iteração; nenhum detectado até a Iteração 00 |
| F3 | Commits semânticos incrementais (vários, não 1 único gigante) | PENDING | Em curso: scaffold + esta iteração já semânticos; 8–10+ commits esperados até o fim |
| F4 | Autor do candidato em todos os commits (sem alterar git config) | CONCLUDED | Verificado: scaffold `Jose Nascimento <322186960+josenascimento1@users.noreply.github.com>`; identidade reutilizada nesta iteração |
| F5 | Setup com 1 comando (`./run.sh` ou `make all`), offline, do clone limpo | PENDING | Iteração 06 |
| F6 | Notebook/saídas com outputs renderizados como evidência visual | PENDING | Iteração 06/07 |
| F7 | Evidências em texto puro (markdown/CSV/JSONL); zero PDF/DOCX/JPEG como fonte primária de evidência | PENDING | Iteração 08 e 09 |
| F8 | Checklist do README marcado somente com arquivos commitados (zero checkbox fantasma) | PENDING | Iteração 08/09 |
| F9 | QA final integral contra todas as instruções oficiais | PENDING | Iteração 09 |
| F10 | Reprovação por hygiene evitável: `git diff --check` limpo em todo commit | CONCLUDED | Executado no commit da Iteração 00; re-executar em toda iteração |

---

## Notas de manutenção

- Este checklist é atualizado pelo orquestrador ao fim de **cada iteração**, antes da revisão 3x.
- Itens com estado `CONCLUDED` podem voltar a `OPEN`/`PENDING` se uma revisão encontrar problema material.
- A revisão 3x da Iteração 00 (item B3) está pendente e é responsabilidade do orquestrador após o retorno do agente executor.