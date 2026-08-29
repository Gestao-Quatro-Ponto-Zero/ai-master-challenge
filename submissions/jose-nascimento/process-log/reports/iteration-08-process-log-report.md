# Report da Iteração 08 — Process log final e evidências de uso de IA

- **Iteração:** 08 (consolidação do process log — item eliminatório)
- **Data:** 2026-08-29
- **Executor:** exatamente um subagente `deepseek-max` (DeepSeek V4 Flash, max reasoning, via OpenCode Go), sob orquestração do opencode (`openai/gpt-5.6-sol` — "GPT 5.6 Sol Max")
- **Prompt integral:** [`process-log/prompts/iteration-08-prompt.md`](../prompts/iteration-08-prompt.md) (arquivado; paths de máquina normalizados — política F2/It08)
- **HEAD base:** `a1e99cb8493b0c21e7470cc20c669ee97de1ce68` (confirmado; working tree limpo; branch `submission/jose-nascimento`)
- **Tempo de relógio (F11):** ~2h30 (leitura integral de artefatos + 4 documentos + prompt/report + verificador G1–G11 + validações 2×/CWD/clone fresco/FAIL test + git)

---

## 1. Status

**PASS** — 4 artefatos obrigatórios do process log criados e navegáveis
(`README.md` entrada principal; `errors/ai-errors-and-corrections.md` com
exatamente 8 erros materiais E1–E8; `decisions/decision-ledger.md` com 18
decisões atribuídas candidato vs orquestrador vs executor vs consenso
reviewers; `evidence-index.md` com índice completo de paths versionados);
prompt e report desta iteração arquivados; README da submissão atualizado
(workflow + links aos 4 artefatos, síntese factual de erros/contribuição,
checkboxes honestos, data `pendente`, LinkedIn `não informado`); execution-plan
e checklist atualizados (**It08 `CONCLUDED`**; **review gate 3x da It08
`PENDING`**; It09/10 `PENDING`); verificador ampliado com gates de processo
**G1–G11** (**88 PASS / 0 FAIL**); validações completas (2× `./run.sh` + CWD +
clone fresco byte-idênticos; report executivo/6 PNGs/números inalterados; FAIL
test em sandbox com diagnóstico útil; `git diff --check` limpo). Commit
`docs: consolidate AI process log and evidence` e push concluídos.

## 2. Método de inventário (como os números foram derivados)

| Fonte | O que foi derivado |
|---|---|
| `git log --author="Jose Nascimento"` (branch `submission/jose-nascimento`) | 25 commits do candidato no HEAD base; mapeamento iteração → commit de etapa → commit de correção; contagem de fixers (9: 8 gates + 1 correção visual pós-gate It04) |
| `git ls-files submissions/jose-nascimento` | 114 arquivos versionados antes desta iteração; +6 após (process log README, errors, decision-ledger, evidence-index, prompt It08, report It08) = 120 |
| Globs de `process-log/{prompts,reports,reviews,decisions,hypotheses,errors}` | 19 prompts (16 It00–07 + adendo + correção visual + It08), 19 reports, 8 review summaries, 6 arquivos de decisões (It02–07) + ledger consolidado, 1 hipóteses (H1–H10), 1 ledger de erros |
| Leitura integral de prompts/reports/reviews/decisions/hypotheses It00–07 | Os 8 erros materiais (E1–E8) com números e hashes; veredictos por gate (24 revisores = 8 gates × 3); matrizes finding→ação |
| Reports externos dos revisores (working artifacts fora do repo) | **Não copiados** (24 arquivos); a evidência persistente é a versão consolidada: 8 summaries + fix reports + prompts + git — explicado no evidence-index §0 e no README do process log §8.6 |
| `./run.sh` + verificador | 77 PASS (It07) → 88 PASS com G1–G11; determinismo byte-a-byte (2× + CWD + clone fresco) |

**Definições usadas nas contagens:** *iteração* = etapa orquestrada com prompt
arquivado, executor único e report; *review gate 3x* = 3 revisores read-only em
paralelo + ledger versionado; *correção sequencial* = fixer commitando
correções materiais de um gate (ou correção visual pós-gate). *Erro material*
= output errado/enganoso com impacto na análise, no risco de reprovação ou
lição de processo (definição no ledger de erros).

## 3. Decisões desta iteração

1. **4 artefatos navegáveis em vez de dump:** narrativa curta no
   `process-log/README.md` apontando para detalhe em erros/decisões/índice —
   sem copiar os 24 reports brutos nem despejar 40 prompts.
2. **Prompt arquivado com paths de máquina normalizados** (`<repo-workdir>`,
   `<review-reports-dir>`) — política F2/It08: docs novos sem paths absolutos;
   conteúdo integral preservado (nota de normalização no próprio arquivo).
3. **Verificador com gates G1–G11 derivados por glob/parse** — contagens de
   reviews/prompts/reports derivadas de glob (sem hardcode frágil); exatamente
   8 erros é requisito de aceitação (parse, não glob); hashes de commit citados
   resolvem via `git rev-parse` (sem lista hardcoded).
4. **Checkboxes honestos no README:** chat exports/screenshots/screen
   recording **desmarcados** (não existem); git history e "Outro" (process log
   completo) **marcados**; prompts descritos como transcrições de prompts, não
   como exports de chat.
5. **Gate 3x da It08 deixado `PENDING`** (a executar pelo orquestrador após
   este commit) — separação implementação/revisão preservada, como nas It00–07.

## 4. Números (derivados — ver §2)

| Métrica | Valor |
|---|---|
| Iterações executadas | 9 (It00–08) |
| Review gates 3x concluídos | 8 (It00–07) — It08 `PENDING` |
| Revisores (instâncias) | 24 (8 gates × 3; reports externos working artifacts) |
| Correções sequenciais commitadas | 9 (`9907024`, `b9823da`, `9378a86`, `12ff47c`, `1517a73`, `e0c6b7e`, `fa6572f`, `a1e99cb` + visual `617e4ac`) |
| Erros materiais registrados | 8 (E1–E8) — E3/E4 no mesmo commit `12ff47c`; E7 cobre categórico-inválido + pycache (mesmo gate `fa6572f`) |
| Prompts arquivados | 19 | Reports versionados | 19 |
| Decisões (ledger consolidado) | 18 (D-01..D-18) |
| Arquivos versionados na pasta | 114 → 120 |
| Commits do candidato | 25 (HEAD `a1e99cb`) → 26 (este commit) |
| Verificador | 77 PASS → **88 PASS / 0 FAIL** (G1–G11) |
| Detecção dos 8 erros | 7/8 pelos revisores (convergência 3/3: E1, E6, E8; 2/3: E7; 1/3: E2–E4) · 1/8 inspeção ocular do orquestrador (E5) |

## 5. Evidência (links)

- [Process log — entrada principal](../README.md)
- [Erros reais E1–E8](../errors/ai-errors-and-corrections.md)
- [Decision ledger (candidato vs modelos)](../decisions/decision-ledger.md)
- [Evidence index (paths versionados)](../evidence-index.md)
- [README da submissão](../../README.md) (process log consolidado; checkboxes honestos)
- [Verificador com gates G1–G11](../../solution/src/06_verify_pipeline.py)
- [Execution plan (It08 CONCLUDED)](../management/execution-plan.md) · [Checklist](../management/orchestrator-checklist.md)

## 6. Erros reais desta iteração (registro honesto)

1. **Campo de detecção divergente no ledger de erros (G2):** a 1ª versão do
   ledger usava "Quem detectou" enquanto o gate G2 exigia "Detectado por" —
   a primeira execução do verificador falhou 8/8 entradas ("incompletos E1–E8").
   **Detectado:** pelo próprio verificador (validação executável), antes de
   qualquer revisão. **Correção:** campos alinhados à convenção do gate
   (Etapa / Detectado por / Causa raiz / Commit). **Validação:** G2 PASS.
2. **Vazamento de tokens de path pessoal no próprio verificador (D2):** os
   comentários/strings novos de `06_verify_pipeline.py` continham literais de
   diretório temporário, diretório home e nome de usuário — a varredura D2
   (que inclui o verificador) acusou o próprio arquivo. Na mesma rodada, o
   gate G4 flagrou menções literais de diretório temporário no prompt
   arquivado (3 ocorrências do texto original do prompt) e na tabela de
   validações do report.
   **Detectado:** D2/G4 na 1ª execução. **Correção:** token composto em
   runtime (`TMP_TOKEN`) e redação sem literais no verificador; menções do
   prompt normalizadas conforme a política F2/It08 (nota de normalização já
   declarada no arquivo). **Validação:** D2/G4 PASS.
3. **Falso positivo do gate de modelos (G5):** a 1ª versão do G5 varria os
   docs novos por substrings e flagou "Claude Code" no ledger de decisões
   (coluna de alternativas consideradas — menção legítima, não claim de uso)
   e no próprio report (descrição do gate). **Detectado:** 1ª execução do
   verificador. **Correção:** escopo do G5 restrito aos READMEs de entrada
   (submissão e process log), onde uma ferramenta errada seria um claim;
   menções em contexto de alternativas/verificação são permitidas e
   documentadas no comentário do gate. **Validação:** G5 PASS.
4. **Gates G10/G11 com defeito na 1ª versão (auto-correção do verificador):**
   o regex de estados do plano não tolerava a linha em branco entre o header
   da seção e a linha de Status (G10 None/None/None); o check de placeholders
   por substring casava a palavra portuguesa "todo" (ex.: "todo path", "todos")
   (G11 4 falsos positivos). **Detectado:** 1ª execução do verificador.
   **Correção:** regex multilinha tolerante + lista de tokens inequívocos
   (exclui "todo") com word-boundary (`\b…\b`). **Validação:** G10/G11 PASS;
   regressão testada (injeção de placeholder → FAIL).

Nenhum erro desta iteração alterou outputs analíticos, números, relatório
executivo ou PNGs (verificados byte-a-byte nas validações); todos os defeitos
foram nos docs/verificador novos e foram corrigidos antes do commit.

## 7. Validações

| Validação | Resultado |
|---|---|
| `./run.sh` (1ª e 2ª) + CWD externo | exit 0; **88 PASS / 0 FAIL** (77 + G1–G11); outputs byte-idênticos entre execuções (report executivo md5 inalterado `86518eac0d55…`; 6 PNGs e 26 tabelas intactos) |
| Clone fresco (isolado) pós-commit | idem; tree limpa; zero `__pycache__` |
| Process link checker (G3) | todos os links relativos de `process-log/**` + README resolvem (arquivos e diretórios); zero link para diretório temporário ou absoluto |
| Exactly-8-errors (G2) | 8 entradas E1–E8 com campos obrigatórios |
| Evidence index coverage (G1/G7/G8) | 4 artefatos + 3 de governança + 8 summaries + inventário completo por glob |
| Commit hashes (G9) | todos os hashes citados nos docs novos resolvem via `git rev-parse` |
| Machine paths/segredos (G4/D2/D3) | zero em docs novos; zero em `solution/` |
| Models/harness (G5) | IDs corretos presentes no process log README; ferramentas erradas ausentes dos READMEs de entrada |
| Checkboxes (G6) | git history e "Outro" marcados; chat exports/screenshots/screen recording desmarcados; data `pendente`; LinkedIn `não informado` |
| FAIL test (sandbox) | link de evidência corrompido → verifier **exit 1** com diagnóstico apontando o link quebrado (G3); entrada de erro removida → G2 exit 1 |
| Markdown/hygiene | `git diff --check` limpo; sem CRLF; compile/imports OK; escopo 100% `submissions/jose-nascimento/` |

## 8. Git

- Commit **`docs: consolidate AI process log and evidence`** (escopo: só
  `submissions/jose-nascimento/`; novos: process log README, errors ledger,
  decision ledger, evidence index, prompt It08, report It08, + modificados:
  README da submissão, verificador, execution-plan, checklist); sem
  amend/force/config/destrutivo; push validado (local == origin); tree limpa;
  autor do candidato (identidade verificada, sem alterar git config).
- Post-push: clone fresco da branch (via origin) revalidado — ver §7.

## 9. Riscos remanescentes / handoff It09

1. **Review gate 3x da It08 `PENDING`** — executar após este commit; ledger em
   `process-log/reviews/iteration-08-review-summary.md`; se houver findings
   materiais, correção sequencial + commit próprio.
2. **It09 (QA final integral):** re-execução limpa (2× + CWD + clone fresco),
   greps de originalidade (term-list E1), auditoria arquivo-a-arquivo,
   checklist A–F integral, `git log` completo (autor/escopo), conferência de
   claims candidato vs IA (ledger D-01..D-18), conferência de que o report
   executivo não foi alterado por It08 (byte-idêntico já verificado).
3. **Gate G4 acoplado à política F2/It08:** qualquer doc novo em process-log
   deve seguir a regra de paths normalizados — revisar no QA.
4. **Gate G9 depende da convenção "backtick + hex = hash de commit":** docs
   novos não devem citar MD5/outros hex em backticks; manter convenção
   documentada no verificador.
5. **Word count do report executivo com margem ~125:** nenhuma alteração foi
   feita em It08; qualquer adição futura exige re-medição (G6/F4).
6. **Time budget:** acumulado ~19h35 vs 4–6h oficiais — **acima do gatilho de
   contenção**, registrado no F11 com a decisão consciente (item eliminatório
   obrigatório; trims formais vigentes desde a It05).
7. **It10:** data de submissão no README (`pendente` até lá) + PR oficial
   `[Submission] Jose Nascimento — Challenge 001`.