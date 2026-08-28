# Report — Iteração 01 · Ingestão e Auditoria dos 5 Datasets

- **Iteração:** 01 (ingestão e auditoria dos 5 datasets RavenStack)
- **Data:** 2026-08-28
- **Executor:** exatamente um subagente `deepseek-max` (via OpenCode Go), sob orquestração do opencode — opencode gerencia agentes/git/evidências; o subagente executou esta iteração (semântica no execution-plan, regra 4)
- **Estado da iteração:** `CONCLUDED` (validação do executor concluída; review gate 3x ainda a disparar pelo orquestrador)
- **Prompt integral desta iteração:** [`process-log/prompts/iteration-01-prompt.md`](../prompts/iteration-01-prompt.md) (transcrição fiel)
- **Tempo de relógio (F11):** ~55 min (exploração read-only + escrita do script + 2 correções + validações) — acumulado da submissão até aqui: Iteração 00 (governança+gate, sem fatia analítica) + esta etapa; orquestrador mantém o controle (política de contenção §2 do plano)

---

## 1. Objetivo

Ingerir os 5 CSVs RavenStack de forma reproduzível e auditável (offline, byte-for-byte, checksums), auditar cada tabela contra o brief (contagens, schema, chaves, nulos, duplicatas, janelas de data, unidades, domínios), validar conectividade entre tabelas (FKs) e ordens temporais, e emitir parecer de sinteticidade **somente com evidência objetiva** — sem escolher definição de churn (Iteração 02) e sem conclusões de negócio.

## 2. Workflow executado

1. **Inspeção do repo** (antes de editar): `git status` (working tree limpo), branch `submission/jose-nascimento` tracking `origin/submission/jose-nascimento` up to date, `git log --oneline -10`, `git remote -v` (origin = fork do candidato). Nada a reverter; nada fora da pasta alterado.
2. **Leitura integral das instruções oficiais e governança**: README.md, CONTRIBUTING.md, submission-guide.md, challenges/data-001-churn/README.md, templates/submission-template.md, execution-plan.md, orchestrator-checklist.md, reports e reviews da Iteração 00 (incl. checksums MD5 capturados na Iteração 00, §2.4 do planning-report).
3. **Iteração 01 marcada `OPEN`** no execution-plan (início lógico da etapa).
4. **Exploração read-only dos CSVs** (fora do repo, em sessão `python3` temporária): schema, tipos, nulos, domínios, janelas de data, FKs, flags — para desenhar os checks com conhecimento real da base e calibrar PASS/WARN/FAIL.
5. **Ingestão**: `solution/data/raw/` criado; 5 CSVs copiados com `cp -p`; MD5 origem vs destino idênticos (e iguais aos checksums da Iteração 00); contagens de linha conferidas (501/5.001/25.001/2.001/601 com cabeçalho = 500/5.000/25.000/2.000/600 registros). `solution/data/raw/README.md` escrito (origem Kaggle oficial citada pelo challenge, licença MIT, checksums, contagens, propósito, uso offline).
6. **Implementação de `solution/src/01_ingest_audit.py`**: stdlib + pandas apenas; paths relativos ao próprio projeto (`Path(__file__).resolve().parent.parent`); sem rede; sem hardcode de paths de máquina; saída determinística (sem timestamp; ordenação estável; contagens com `value_counts().sort_index()`).
7. **Execução + idempotência**: 2 execuções → relatório byte-a-byte idêntico (diff vazio; MD5 igual).
8. **3 verificações manuais independentes** dos achados materiais (detalhe em §4).
9. **Evidência de processo**: prompt arquivado (este report, itens acima); remoção do `solution/.gitkeep` (substituído por arquivos reais).
10. **Atualização de governança**: execution-plan (Iteração 01 `CONCLUDED`) e orchestrator-checklist (somente fatos comprovados); validações finais; commit e push.

## 3. Decisões desta iteração (julgamento do executor vs output da IA)

| Decisão | Julgamento do executor | Output/contexto da IA | Decisão registrada |
|---|---|---|---|
| D1 — Semântica de WARN para anomalias de qualidade | Anomalias conhecidas da base (IDs duplicados de uso, uso fora da janela, flags divergentes) não quebram joins nem a estrutura essencial → WARN, não FAIL | Prompt pedia distinguir WARN (anomalia esperada) de FAIL (estrutura ausente) | WARN para anomalias; FAIL restrito a presença/schema/chave/FK estrutural |
| D2 — Janela global de datas em granularidade de data | `closed_at` com hora `19:00` de `2024-12-31` está **dentro** da janela de datas; comparar datetime completo contra limite de data é falso-positivo | Correção de bug do próprio script (2 valores marcados FAIL por hora do dia) | Janela comparada em `dt.normalize()` (data calendário) |
| D3 — `end_date` nulo não é erro de parse | 4.514 `end_date` nulos = assinaturas ativas (semântica do schema); contar como "não parseável" era falso-positivo | Correção de bug do próprio script (FAIL D01 subscriptions) | Só valores presentes não-parseáveis contam como erro |
| D4 — Divergências de churn flag/eventos são WARN, não conclusão | As 3 fontes de churn (accounts.churn_flag, subscriptions.churn_flag, churn_events) divergem (35/277/125) — quantificar e **adiar** a reconciliação para a Iteração 02, sem interpretar causa | Prompt: "identifica problemas de dados, mas NÃO escolhe definição de churn" | C01/C02 como WARN com números; explicitamente "reconciliação é objeto da Iteração 02" |
| D5 — `requirements.txt` inalterado | Script usa apenas `pandas` (já presente); nada novo necessário; lock/pinning é objeto da Iteração 06 (finding L3 da Iteração 00) | Prompt: "atualize apenas se realmente necessário" | Sem mudança; nota registrada |
| D6 — Relatório sem timestamp | Timestamp quebraria a determinância byte-a-byte exigida | Prompt: "gerar deterministicamente" | Proveniência sem timestamp; versões Python/pandas no stdout (fora do arquivo) |

## 4. Arquivos criados/alterados (somente dentro de `submissions/jose-nascimento/`)

| Arquivo | Ação |
|---|---|
| `solution/data/raw/ravenstack_accounts.csv` | Adicionado (cópia byte-for-byte; MD5 `2c1dbd0d9d25ef044564c10e56ce59a5`) |
| `solution/data/raw/ravenstack_churn_events.csv` | Adicionado (MD5 `7ac3c66bc4212f9f2136772ed3bfcb4d`) |
| `solution/data/raw/ravenstack_feature_usage.csv` | Adicionado (MD5 `0377a02ec034ef5d30f05b66a434e1ab`) |
| `solution/data/raw/ravenstack_subscriptions.csv` | Adicionado (MD5 `94073fd10488eda224a1687d5414bb7c`) |
| `solution/data/raw/ravenstack_support_tickets.csv` | Adicionado (MD5 `51e144eced16a86370f9d4ce7ef0b9e4`) |
| `solution/data/raw/README.md` | Adicionado (origem Kaggle oficial, licença MIT, checksums, contagens, propósito, uso offline) |
| `solution/src/01_ingest_audit.py` | Adicionado (pipeline de auditoria; stdlib + pandas; sem rede) |
| `solution/evidence/01_audit_report.md` | Adicionado (relatório gerado pelo script; regenerável) |
| `process-log/prompts/iteration-01-prompt.md` | Adicionado (transcrição fiel deste prompt) |
| `process-log/reports/iteration-01-ingest-audit-report.md` | Adicionado (este report) |
| `process-log/management/execution-plan.md` | Alterado (Iteração 01: `PENDING` → `OPEN` → `CONCLUDED`) |
| `process-log/management/orchestrator-checklist.md` | Alterado (C2, C3, C4, D1 → `CONCLUDED` com evidência; verificação F2/F10 desta iteração) |
| `solution/.gitkeep` | Removido (substituído por arquivos reais) |

Nenhum arquivo fora da pasta do candidato foi alterado.

## 5. Resultados (checks executados pelo script)

- **Exit code:** 0 (estrutura essencial íntegra; nenhum FAIL).
- **Resumo:** 72 PASS · 18 WARN · 0 FAIL (relatório: `solution/evidence/01_audit_report.md`).
- **Registros vs brief:** 500/5.000/25.000/2.000/600 — todos exatamente iguais ao valor anunciado (~) — PASS.
- **Schema/chaves:** colunas idênticas ao brief nos 5 arquivos; chaves candidatas sem nulos; sem linhas duplicadas; `usage_id` com **21 IDs duplicados** (reuso em linhas distintas — WARN, joins não afetados).
- **FKs:** 0 órfãos em `subscriptions→accounts`, `tickets→accounts`, `churn_events→accounts`, `feature_usage→subscriptions` (PASS); **33 assinaturas sem nenhuma linha de uso** (WARN).
- **Datas:** todas parseáveis; janela global 2023-01-01..2024-12-31 respeitada em todos os arquivos; `closed_at >= submitted_at` (0 violações); `resolution_time_hours <=` tempo decorrido (0 violações).
- **Anomalias temporais (WARN, sem interpretação causal):**
  - `feature_usage`: **19.142 de 25.000 linhas (76,6%)** com `usage_date` anterior ao `start_date` da assinatura (4.783 assinaturas afetadas; assinaturas com início em 2024 = 4.334 de 5.000) — maior anomalia da base.
  - 13.198 linhas de uso anteriores ao signup da conta; 1.077 tickets abertos antes do signup; 53 eventos de churn anteriores à primeira assinatura; 90 eventos posteriores à última `end_date`.
- **Unidades/domínios:** `ARR = 12 × MRR` em 100% das linhas com MRR>0; trial ⇒ MRR=0 (778) e não-trial ⇒ MRR>0 (0 violações); CSAT ∈ {3,4,5} com 825 nulos (41,2%); domínios categóricos válidos (indústrias 5, países 7, canais 5, planos 3, prioridades 4, reason codes 6, features 40); `seats>0`; refunds ≥ 0.
- **Flags vs datas/consistência:** `churn_flag` ↔ `end_date` perfeitamente consistentes nas assinaturas (0 violações); 23 linhas com `upgrade_flag` e `downgrade_flag` simultâneos (WARN); **divergência entre fontes de churn quantificada** (WARN, adiada para Iteração 02): contas com flag sem evento = 35; contas com evento sem flag = 277 (de 110 com flag e 352 com evento, 600 eventos); contas com evento sem assinatura churn_flag = 125; 175 contas com >1 evento (máx 5; 61 eventos `is_reactivation` — insumo da Iteração 02).

## 6. Parecer de sinteticidade (evidência objetiva — sem causa de negócio)

O relatório (§5) lista padrões observados, consistentes com base **gerada sinteticamente**:

1. IDs com esquema determinístico `<PREFIXO>-<6 hex>` (A/S/T/C/U) em 100% das linhas, 0 violações.
2. Distribuições quase uniformes em categorias (prioridades 485–514; reason codes 91–114; canais 89–114; planos 1602/1675/1723) e uso mensal uniforme em 24 meses (944–1.137 por mês) — padrão típico de amostragem aleatória, não de demanda real.
3. **Desacoplamento temporal**: 76,6% do uso fora da janela da assinatura (uso uniforme 2023–2024 vs 87% das assinaturas iniciando em 2024) — o gerador atribuiu datas de uso independentes do ciclo de vida da assinatura.
4. Estruturas exatas: `ARR = 12×MRR` em 100% das linhas; trial ⇒ MRR=0 em 100%.
5. CSAT restrito a {3,4,5}; 21 IDs de uso reutilizados em linhas distintas (mesmo ID; assinaturas diferentes em 21/21; features diferentes em 19/21).

Essas observações **não** extrapolam causa de negócio e **não** escolhem definição de churn; apenas caracterizam o processo de geração da base.

## 7. Verificações manuais independentes (3, diretamente nos CSVs)

Metodologia: sessões `python3` com pandas **independentes do script**, lendo `solution/data/raw/*.csv`, com `assert` contra os números do relatório.

| # | Achado verificado | Comando/metodologia | Resultado |
|---|---|---|---|
| MV1 | D09 — uso antes do início da assinatura (19.142; 76,6%) | `python3 -W ignore - <<EOF` (heredoc pandas): `use.merge(sub[["subscription_id","start_date"]], on="subscription_id")`; `(m.usage_date < m.start_date).sum()`; exemplo `S-0fcf7d` (usage 2023-02-22 vs start 2024-11-23) | PASS — 19.142 de 25.000 (76,6%); 4.783 assinaturas distintas afetadas |
| MV2 | C01/C02 — divergência de fontes de churn (35/277/125) | `python3 -W ignore - <<EOF` (heredoc pandas): conjuntos `set(acc.loc[acc.churn_flag,"account_id"])`, `set(churn.account_id)`, `set(sub.loc[sub.churn_flag,"account_id"])`; diferenças de conjunto; exemplo `A-00bed1` (1 evento, 0 assinaturas churn_flag, accounts.churn_flag=False) | PASS — 110 flag / 352 contas com evento / 600 eventos; 35 flag-sem-evento; 277 evento-sem-flag; 125 evento-sem-assinatura-churn |
| MV3 | S03 + D07 — 21 `usage_id` duplicados; 1.077 tickets antes do signup | `python3 -W ignore - <<EOF` (heredoc pandas): `use["usage_id"].duplicated().sum()` + `groupby("usage_id")["subscription_id"].nunique()` (reuso entre assinaturas); `tic.merge(acc[["account_id","signup_date"]],on="account_id")`; `(submitted_at[:10] < signup_date).sum()`; exemplo `T-0024de` (submitted 2023-07-27 vs signup 2023-12-16) | PASS — 21 IDs duplicados (21/21 com >1 assinatura); 1.077 tickets antes do signup |

## 8. Erros reais encontrados e corrigidos (pelo executor, durante a execução)

1. **D01-subscriptions falso FAIL** — primeira versão do script contava os 4.514 `end_date` nulos como "não parseáveis", gerando FAIL e exit 1. Causa: semântica de `end_date` nulo = assinatura ativa não considerada. Correção: apenas valores **presentes** não-parseáveis contam (0); nulos documentados como semântica. Resultado: exit 0.
2. **D02-tickets falso FAIL** — 2 valores de `closed_at` (2024-12-31 13:00:00 e 19:00:00) marcados fora da janela. Causa: comparação de datetime completo contra limite de **data**. Correção: janela comparada em granularidade de data (`dt.normalize()`); o horário do dia na data-limite é válido. Resultado: 0 fora da janela.
3. **Cosmético** — detalhe "1 colunas de ID" (plural) e F01 só registrado em falha; corrigidos para legibilidade e auditabilidade (F01 agora sempre registrado, com bytes do arquivo).

Nenhum erro foi inventado; os dois primeiros foram encontrados nas execuções reais (exit 1 → diagnóstico → correção → exit 0).

## 9. Comandos de validação executados

| Validação | Comando | Resultado |
|---|---|---|
| Ingestão byte-for-byte | `cp -p` + loop `md5sum` origem vs destino | 5/5 MATCH (MD5 iguais à origem e aos checksums da Iteração 00) |
| Contagens | `wc -l` | 501/5.001/25.001/2.001/601 (com cabeçalho) |
| Execução do script | `python3 -W ignore solution/src/01_ingest_audit.py` (workdir = pasta da submissão) | exit 0; 72 PASS / 18 WARN / 0 FAIL |
| Idempotência | 2 execuções; `diff` + `md5sum` dos relatórios | idênticos byte-a-byte (`719663ced05be97dc0235a02a7637d40`) |
| Offline | inspeção do script (imports: stdlib + pandas; nenhuma chamada de rede) | sem rede |
| Hygiene | `git diff --check` (após staging) | limpo |
| Escopo | `git status`/`git diff` | somente arquivos de `submissions/jose-nascimento/` |
| Paths pessoais/segredos | grep por `/tmp`, `/home`, `ubuntu` nos artefatos da solução | zero ocorrências fora do prompt arquivado (transparência de processo, regra 8 do plano) |

## 10. Riscos e pendências

1. **Revisão 3x da Iteração 01** — obrigatória (regra 2 do plano); orquestrador deve disparar 3 agentes `deepseek-max` read-only; ledger em `process-log/reviews/iteration-01-review-summary.md` (a criar pelo orquestrador/revisores).
2. **Reconciliação de churn (Iteração 02)** — a divergência de fontes (35/277/125 + múltiplos eventos por conta) é o insumo central; esta iteração **não** escolhe definição.
3. **Anomalias temporais** — 76,6% do uso fora da janela da assinatura afeta qualquer análise temporal (coortes, uso vs churn); a Iteração 02 deve fixar regras de janela no contrato analítico.
4. **`accounts` como snapshot** — divergências seats/plano (439/363) sem fonte canônica definida; contrato analítico (Iteração 02) deve decidir.
5. **`requirements.txt`** — sem pinning; lock é objeto da Iteração 06 (finding L3 da Iteração 00).
6. **Push** — depende de rede/credenciais; se falhar, commit permanece local e o estado real é reportado.

## 11. Handoff explícito para a Iteração 02

**Ao orquestrador (opencode):** a Iteração 01 está `CONCLUDED` (validação do executor concluída; review gate 3x a disparar). Disparar o próximo agente executor `deepseek-max` para a **Iteração 02 — Reconciliação das definições/grãos de churn e contrato analítico**, com:

1. **Entradas:** `solution/evidence/01_audit_report.md` (checks C01/C02/C03: divergências de flag/eventos 35/277/125; 175 contas com >1 evento, máx 5; 61 eventos de reativação), `solution/data/raw/` (CSVs commitados), brief, execution-plan (critérios da Iteração 02).
2. **Fatos a reconciliar (números da auditoria, sem interpretação):** accounts.churn_flag=110 vs 352 contas com evento (600 eventos) vs subscriptions.churn_flag=312 contas; 33 assinaturas sem uso; janelas temporais de uso/eventos.
3. **Restrições:** nada fora de `submissions/jose-nascimento/`; sem conclusão causal; pipeline offline; números re-executados (nada de pesquisa interna).
4. **Critérios de aceitação objetivos (execution-plan §Iteração 02):** divergências quantificadas; definição única point-in-time justificada; grão account-month; invariantes de contagem e MRR passando; CSAT/reason codes marcados como evidência sugestiva; contrato analítico em `docs/analytical-contract.md`.
5. **Retorno ao orquestrador:** report estruturado com Status PASS/BLOCKED, commit hash, validações, riscos — sem conclusão simulada se algo bloquear.

---

*Prompt integral desta iteração em [`process-log/prompts/iteration-01-prompt.md`](../prompts/iteration-01-prompt.md).*