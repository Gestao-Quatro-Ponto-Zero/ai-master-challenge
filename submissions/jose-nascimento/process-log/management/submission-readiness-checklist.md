# Submission Readiness Checklist — Challenge 001 (Diagnóstico de Churn · RavenStack)

- **Tipo:** artefato do QA final integral (Iteração 09) — mapeia **cada regra oficial** do G4 AI Master Challenge ao status e à evidência da submissão de Jose Nascimento Moreira (branch `submission/jose-nascimento`, pasta única `submissions/jose-nascimento/`).
- **Estados válidos:** `PASS` (regra atendida com evidência) / `PENDING` (pendente — somente It10). Nenhum item afirma algo ainda não realizado.
- **Fonte das regras oficiais:** `README.md` (raiz), `CONTRIBUTING.md`, `submission-guide.md`, `challenges/data-001-churn/README.md`, `templates/submission-template.md` — lidos integralmente (Iteração 00 e re-lidos na Iteração 09).
- **Pendências atuais:** nenhuma. A data final foi preenchida no README como `2026-08-29`; o commit final e o PR foram concluídos na It10 (gate 3x da It09 `CONCLUDED` em 2026-08-29).
- **Snapshot:** fechamento da Iteração 09 (2026-08-29, pós-gate 3x), com remediação posterior dos dois findings HIGH da auditoria crítica final. Re-derivar contagens na It10.
- **Remediação crítica:** HIGH-001 (polaridade linkage) e HIGH-002 (horizontes KM) estão corrigidos e registrados em [`process-log/reviews/final-critical-audit-summary.md`](../reviews/final-critical-audit-summary.md); a It10 foi concluída com o commit `88e33b5` e o [PR #111](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/111).

---

## A. Regras oficiais — processo e estrutura

| # | Regra oficial (fonte) | Status | Evidência |
|---|---|---|---|
| 1 | Fork do repositório oficial (`Gestao-Quatro-Ponto-Zero/ai-master-challenge`) | PASS | Fork do candidato no GitHub (público — acessível anonimamente via `git ls-remote`; remote `origin` aponta para o fork); `upstream/main` == `origin/main` == `4aed364` (diff vazio) |
| 2 | Branch `submission/seu-nome` | PASS | Branch `submission/jose-nascimento`; 38 commits totais (33 do candidato + 5 de base) no fechamento da It09, lineares, zero merges |
| 3 | Pasta exclusiva `submissions/seu-nome/` | PASS | `submissions/jose-nascimento/`; 100% dos commits do candidato tocam somente esta pasta (`git log --name-only main..HEAD`); nenhum arquivo raiz alterado |
| 4 | Um desafio escolhido (README raiz: "preferimos um bem feito do que dois superficiais") | PASS | Challenge 001 — Diagnóstico de Churn (único conteúdo da pasta) |
| 5 | Solução dentro da pasta + instruções de setup se houver código (CONTRIBUTING checklist) | PASS | `solution/` completa (src 01–07, data, evidence, out); setup documentado em `solution/README.md` §2 e `README.md` da submissão; 1 comando `./run.sh`/`make all` |
| 6 | Process log obrigatório com evidências de uso de IA (README raiz; submission-guide §2; template) | PASS | `process-log/` completo: 22 prompts transcritos, 22 reports, 10 review summaries, 8 erros E1–E8 com causa raiz, decision ledger (18 decisões com atribuição), hipóteses H1–H10 pré-registradas, evidence index; README principal navegável |
| 7 | README da submissão segue o template oficial (CONTRIBUTING; template) | PASS | `README.md` da submissão: Sobre mim (Nome; LinkedIn `Informado no formulario de inscricao`; Challenge escolhido), Executive Summary, Solução (Abordagem/Resultados/Recomendações/Limitações), Process Log (ferramentas/workflow/erros/contribuição), Evidências com checkboxes honestos, data `2026-08-29` |
| 8 | Não modificar arquivos fora da pasta (CONTRIBUTING: "PRs que alteram outros arquivos serão rejeitados") | PASS | Histórico integral auditado (It09): zero arquivos fora de `submissions/jose-nascimento/` em 33 commits; `.gitignore` raiz ignora `submissions/` e commits usam `git add -f` só nos paths pretendidos |
| 9 | Título do PR no formato oficial `[Submission] Nome — Challenge NNN` (CONTRIBUTING; o template usa o número do challenge) | PASS | Título exato: `[Submission] Jose Nascimento Moreira — Challenge 001`; base `upstream main`; [PR #111](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/111) |
| 10 | Um PR por pessoa; atualizações por push na mesma branch (CONTRIBUTING) | PASS | Branch única; [PR #111](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/111) aberto com push final na mesma branch |
| 11 | Sem chat export/screenshot inventado; evidências reais (submission-guide: formatos aceitos; "sem evidência de processo = desclassificado") | PASS | Evidência 100% real e versionada: prompts transcritos, reports, summaries, git history, pipeline reproduzível; checkboxes de chat exports/screenshots/screen recording **desmarcados** (não existem) — gate G6 do verificador |

## B. Regras do challenge 001 (challenges/data-001-churn/README.md)

| # | Regra oficial | Status | Evidência |
|---|---|---|---|
| 12 | Responder **o que está causando o churn** (causa raiz, cruzando tabelas — "quem só olhou uma perdeu o ponto") | PASS | Causa raiz: churn precoce de onboarding (pico dez/24: 43 primeiros eventos, 22,51% vs mediana 13,01%; 83,7% do pico em contas 0–3m; 53,4% dos primeiros eventos ≤90d; 68,4% do R1 ≤90d) — cruzando as 5 tabelas (accounts/subscriptions/churn_events/feature_usage/support_tickets; gates G8-segments e G11-onboarding do evidence 03) |
| 13 | Responder **quais segmentos estão mais em risco** ("com dados, não feeling. Identifique contas específicas") | PASS | Segmentos de jornada S1–S5 com N, MRR e lift de backtest (t15); watchlist top-20 com contas específicas (IDs, MRR, evidência, limitação) em t16/t21 e 10 contas nomeadas no relatório executivo §5 |
| 14 | Responder **o que a empresa deveria fazer** ("ações concretas, priorizadas, com impacto estimado") | PASS | ACT-01..04 com sequenciamento, owners, prazos, stop/go; impacto em faixa com premissas nomeadas (2,7–13,0 eventos e 21.104–101.078 US$ em 90d); plano de medição t20 |
| 15 | Insights verificáveis (mostre os números) | PASS | Números com origem rastreável (tabelas t01–t21, evidence 01–05, apêndice do relatório executivo §10); re-derivação independente na It09: 59/59 âncoras conferem |
| 16 | Recomendações acionáveis (não "melhorar a experiência") | PASS | Ações com owner/prazo/critério de decisão em 3 estados (GO exige IC95 excluindo 0); seção "O que não fazer agora" com justificativas |
| 17 | Correlação vs causalidade distinguida ("nem toda correlação é insight") | PASS | Status por achado (descritivo / hipótese causal plausível / não identificável) em t09/t10 e relatório §§1/3/9; "hipótese causal plausível — não prova" explícito; faixa ≠ CI; lift ≠ efeito; exposição ≠ perda |
| 18 | CEO (não-técnico) consegue ler e agir | PASS | Relatório executivo `solution/report-executivo.md` (2.275 palavras; resposta primeiro; 6 gráficos; decisão solicitada explícita; word count dentro de budget 1.400–2.400 — gate F4) |
| 19 | Diferencial opcional (modelo/dashboard/automação) | PASS (declarado) | Diferencial construído = pipeline reproduzível em 1 comando + verificador com 88 checks; ML/score **não** construído por falta de sinal validado (NO-GO documentado — decisão D12), honestidade > feature |
| 20 | Time budget 4–6 horas (README raiz) | PASS (disclosure honesto) | Execução documentada **~24–28h** no fechamento da It09 (16 fatias ~ por sessão, não aditivas; soma bruta ≈ 27h40; teto da faixa acima da soma bruta por definição — incerteza das estimativas `~` e sessões sem fatia própria) — **excedido por decisão consciente de revisão**, com política de contenção, trims formais desde a It05 e nenhum claim de conformidade (checklist F11; process log §8.5) |

## C. Regras de baseline/originalidade (README raiz: "Parecido com o baseline não é suficiente")

| # | Regra oficial | Status | Evidência |
|---|---|---|---|
| 21 | Entrega supera substancialmente o que a IA produz sozinha | PASS | Pré-registro de hipóteses/premissas/narrativa antes do código; lente por pergunta e regra do winner; gates de honestidade; revisão 3x read-only por etapa (pegou 7/8 erros materiais); inspeção ocular humana do orquestrador (E5); reprodução byte-a-byte em 1 comando; 59/59 números re-derivados |
| 22 | Zero cópia de análises públicas do dataset / benchmark interno como fonte | PASS | Varredura de originalidade na It09: tokens de pesquisa interna/benchmark zero nas entregas (ocorrências somente em prompts/reports históricos com exceção documentada F2/E1 — transparência, não citação); conclusões 100% re-derivadas dos 5 CSVs |
| 23 | Process log mostra iteración e julgamento, não 1 prompt → 1 resposta | PASS | 10 iterações orquestradas; 8 erros reais com causa raiz e correção; nenhuma iteração relatou "não houve erros"; 10 gates 3x (30 revisões read-only); decisões com atribuição candidato vs orquestrador vs executor vs revisores |

## D. Higiene, git e reprodutibilidade (CONTRIBUTING + boas práticas)

| # | Regra | Status | Evidência |
|---|---|---|---|
| 24 | Histórico git auditável (vários commits semânticos, autor do candidato) | PASS | 33 commits do candidato com autor verificado (identidade do candidato via `git log --format='%an <%ae>'` — sem alterar `git config`), mensagens semânticas (feat/fix/docs/chore/build), lineares, sem amend/force/rebase |
| 25 | Reproduzível do clone (setup documentado; 1 comando; offline) | PASS | Clone fresco do origin (sem qualquer diretório externo): `./run.sh` 2× + `make all` + CWD externo + verificador direto — 88 PASS / 0 FAIL, byte-idêntico, ~64–66 s, zero `__pycache__`; FAIL tests (schema/categórico/raw ausente/derivado ausente/link corrompido) com exit 1 estruturado, zero traceback, zero stale |
| 26 | Zero segredos/credenciais; zero binários proibidos/cache/venv/db | PASS | Grep de segredos: zero (somente padrões do próprio verificador); zero `.db/.duckdb/.sqlite/.pyc`/venv/cache na árvore; únicos binários = 6 PNGs de gráficos (manifesto fechado) |
| 27 | `git diff --check` limpo; working tree limpa; remote sync | PASS | `git diff --check` limpo na It09; tree limpa pós-runs; `origin/submission/jose-nascimento` == local |
| 28 | Atribuição do dataset (Kaggle oficial + licença MIT) | PASS | Link oficial Kaggle + licença MIT no `solution/README.md` §11, `data/raw/README.md` e README da submissão; MD5 dos 5 raw CSVs == manifesto commitado (gate C2) |
| 29 | Zero dependência de rede em runtime | PASS | Inspeção de imports (checks D4) + execução em clone isolado com rede não utilizada; dados commitados |
| 30 | Dependências mínimas e pins públicos | PASS | `requirements.txt`: `pandas==3.0.5`, `matplotlib==3.11.1` (pins exatos, determinismo); testado em Python 3.12.3 |

---

## Pendências formais (somente It10)

| # | Item | Estado | Ação na It10 |
|---|---|---|---|
| P1 | Data final de submissão no README | CONCLUDED | `2026-08-29` preenchida no README (It10) |
| P2 | Commit final de submissão | CONCLUDED | `88e33b5 docs: finalize submission` (It10) |
| P3 | Pull Request oficial | CONCLUDED | [PR #111](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/111), título `[Submission] Jose Nascimento Moreira — Challenge 001`; base upstream `main`; descrição com resumo e navegação; somente arquivos da pasta |

---

## Veredito do QA final (Iteração 09)

**PASS** — todos os itens oficiais/analíticos/process/repro atendidos com evidência; **gate 3x da It09 `CONCLUDED`** (3 veredictos `PASS_WITH_FIXES`; correções L1–L3 aplicadas pelo fixer — ver `reports/iteration-09-review-fix-report.md`); pendências exclusivamente: data final, commit final e PR (It10, após aviso ao candidato e auditoria 5x). Evidência integral: [`process-log/reports/iteration-09-final-qa-report.md`](../reports/iteration-09-final-qa-report.md).

*Snapshot no fechamento da It09 (2026-08-29); re-derivar na It10.*
