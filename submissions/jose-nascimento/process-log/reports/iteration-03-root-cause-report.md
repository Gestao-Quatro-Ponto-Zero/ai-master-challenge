# Report — Iteração 03 · Causa raiz, coortes e economia do onboarding

- **Iteração:** 03 (causa raiz, coortes e onboarding economics — análise central do challenge)
- **Data:** 2026-08-28
- **Executor:** exatamente um subagente `deepseek-max` (via OpenCode Go), sob orquestração do opencode — opencode gerencia agentes/git/evidências; o subagente executou esta iteração (semântica no execution-plan, regra 4)
- **Estado da iteração:** `CONCLUDED` (validação do executor concluída; review gate 3x ainda a disparar pelo orquestrador — permanece `PENDING`)
- **Prompt integral desta iteração:** [`process-log/prompts/iteration-03-prompt.md`](../prompts/iteration-03-prompt.md) (transcrição fiel)
- **Hipóteses pré-registradas:** [`process-log/hypotheses/iteration-03-root-cause-hypotheses.md`](../hypotheses/iteration-03-root-cause-hypotheses.md) — commitadas ANTES de qualquer análise (ver §2 timeline)
- **Decisões registradas:** [`process-log/decisions/iteration-03-root-cause-decisions.md`](../decisions/iteration-03-root-cause-decisions.md)
- **Tempo de relógio (F11):** ~1h20min (leitura da governança + Fase A de hipóteses + script + 6 correções reais + 3 verificações manuais + sandbox + validações + documentos) — acumulado analítico da submissão: ~5h45 (Iterações 01–03 + gate da It02); orquestrador mantém o controle (política de contenção §2 do plano)

---

## 1. Objetivo

Identificar e quantificar o(s) fenômeno(s) central(is) de churn da RavenStack com hipóteses **pré-registradas** (H1–H10), coortes com censura correta (Kaplan–Meier descritivo), economia do onboarding parametrizada (exposição R1 em 30/60/90 dias + cenários CAC-equivalent nomeados), sinais de uso/suporte sem leakage, segmentos com denominador e causalidade delimitada — sem recomendações (It05), sem watchlist (It04), sem modelo preditivo/ML.

## 2. Timeline (prova de que as hipóteses vieram antes)

| Momento | Horário (UTC) | Evidência |
|---|---|---|
| Leitura integral (governança, contrato, It00–It02, scripts 01–02) | ~20:05–20:20 | este report; nenhuma query de negócio antes |
| Escrita das hipóteses H1–H10 + arquivamento do prompt | 20:20–20:28 | `process-log/hypotheses/iteration-03-root-cause-hypotheses.md`; `process-log/prompts/iteration-03-prompt.md` |
| **Commit/push das hipóteses ANTES do código** | **20:28:42Z** | **commit `docs: define churn hypotheses before analysis` — hash `8cb93c33779d199a6cf05a37f5c411ff25fe75f3`** (local == remote) |
| Implementação de `solution/src/03_root_cause.py` | 20:30–21:05 | 6 correções reais (§7) |
| Validações, verificações manuais, sandbox, documentos | 21:05–21:50 | §8; commit final `feat: diagnose churn root cause and cohort dynamics` (hash no fim) |

## 3. Workflow executado

1. **Inspeção do repo**: `git status` limpo; branch `submission/jose-nascimento` tracking `origin` up to date; HEAD `6e7be698…` = esperado; `git remote -v`.
2. **Leitura integral**: instruções oficiais (já lidas nas It00–02, re-verificadas), execution-plan, orchestrator-checklist, prompts/reports/reviews It00–02, `solution/docs/analytical-contract.md` (contrato congelado), `solution/evidence/01_audit_report.md` e `02_consistency_report.md`, scripts 01–02 (convenções: stdlib+pandas; paths relativos; checks PASS/WARN/FAIL; determinismo).
3. **Fase A (hipóteses)**: H1–H10 escritas com threshold pré-registrado, teste falsificável, confundidores e resultado se refutada; prompt arquivado; **commit/push antes de qualquer query** (timeline §2).
4. **Fase B (análise)**: `solution/src/03_root_cause.py` implementado (stdlib + pandas + matplotlib; sem rede; PNG byte-a-byte estáveis) gerando `evidence/03_root_cause_report.md`, 13 tabelas em `out/tables/` e 6 gráficos em `out/charts/`.
5. **Execução + correções reais** (6, §7) até exit 0 (23 PASS / 0 WARN / 0 FAIL).
6. **Idempotência**: 2 execuções → todos os outputs byte-a-byte idênticos (MD5).
7. **3 verificações manuais independentes** (MV-1/MV-2/MV-3, §6) — implementação própria fora do repo (`/tmp/opencode/it03_manual_checks.py`), lendo apenas os CSVs raw.
8. **Sandbox de falha estrutural** (2 cenários, §8) — lição das It01/02 aplicada.
9. **Consistência report↔CSV** (script independente, §8).
10. **Evidência de processo**: prompt, hipóteses, decisions file, este report.
11. **Atualização de governança**: execution-plan (It03 `CONCLUDED`; artefatos/commits reais sincronizados; futuras `PENDING`) e orchestrator-checklist (D12 → `CONCLUDED`; D6/D7 → `OPEN`; F2/F10/F11 desta iteração); validações finais; commit e push.

## 4. Decisões desta iteração (julgamento do executor vs output/contexto da IA)

Resumo; detalhe completo (problema → opções → evidência → decisão → trade-off) no decisions file.

| Decisão | Julgamento do executor | Output/contexto da IA | Onde |
|---|---|---|---|
| D1 — "Pico" = mês de maior contagem (2024-12); "período elevado" = regra 1,5× mediana (2024-03..2024-12) | A primeira versão apresentava o 1º mês elevado (2024-03) como pico — enganoso; o pico real por contagem E taxa é 2024-12 | Prompt: "decomposição do spike por tenure/coorte" (sem definir pico) | decisions D1; report §2 |
| D2 — Controle de composição de tenure no H2 (esperado = Σ elegíveis×taxa-baseline por bucket) | A taxa bruta do pico (22,5%) mistura mix de tenure do pool elegível com taxa real; o controle isola o efeito | Prompt: "coortes... composição de coorte/onboarding, demonstre mecanismo e tamanho" | decisions D2; report §2/H2 |
| D3 — Suporte: desenho calendar-time (churn do mês m vs elegíveis sem evento em m; janela 90d antes do dia 1 de m); sensibilidades nunca-churn e por tenure | Desenho honesto anti-sobrevivência, comparável em calendário; N por lado 346/3.288 conta-mês | Prompt: "desenho honesto: primeiro churn por conta; janelas antes da data índice; controles comparáveis" | decisions D3; report §6 |
| D4 — Bucket `0d` (start=end) no onboarding; share por duração fecha 100% do R1 | 13 assinaturas same-day (46.324; 3,9% do R1) eram invisíveis na tabela de buckets (shares somavam 96%) | Prompt: "quantifique exposição contratual bruta precoce" | decisions D4; report §4; gate G11 |
| D5 — CSAT/resolução só com tickets fechados e com nota; pré-signup excluído no primário de uso/tickets | Contrato §9/§10; sensibilidade com pré-signup incluído reportada | Prompt: "respeite closed_at e política anti-leakage; exclua registros pré-signup no cenário primário" | contrato §9/§10; report §5/§6 |
| D6 — Nenhum modelo preditivo: NO-GO com números (H4/H5 refutadas; sinais não distinguem churn) | Sem sinal pré-evento, ML seria autoengano; mecanismo é coorte/onboarding, não preditor | Prompt: "Se dados sintéticos impedirem inferência, mostre o NO-GO com números. Evite modelo preditivo/ML" | decisions D6; report §9/§12 |

## 5. Resultados (hipótese → veredito → números; detalhe no `03_root_cause_report.md` §10)

| Hipótese | Veredito | Números-chave | Interpretação |
|---|---|---|---|
| H1 — churn é de contas jovens | **SUSTENTADA** | 75,3% dos primeiros eventos com tenure ≤ 6m; mediana 3m (N=352) | fenômeno de início de ciclo de vida |
| H2 — spike é composição de coorte | **SUSTENTADA (aumento real de taxa)** | pico 2024-12: taxa 22,51% vs mediana da janela 7,42% (3,03×) e vs mediana 6m anteriores 13,01% (1,73×); controle de tenure: esperado 24,82, observado 43 (1,73×) | composição (mais signups) + taxa real de churn precoce maior; aumento persiste após controle de tenure |
| H3 — "uso cresceu" é volume | **SUSTENTADA** | total bruto sem pré-signup 2.775 → 9.027 (+225,3%); mediana por conta 2,0 → 2,0 (0,0%); sensibilidade com pré-signup: +1,1% | produto está "certo" no volume, mas a intensidade por conta não cresceu |
| H4 — uso cai antes do churn | **REFUTADA** | mediana de uso alinhado pré-evento 0,0 vs 0,0; zero-uso 73,9% vs 60,2% (Δ 13,7 p.p. < 25) | uso decoplado do churn (estrutura da base); "uso cresceu" e "churn subiu" coexistem sem contradição |
| H5 — suporte diferencia churn | **REFUTADA** | tickets/conta 0,309 vs 0,352; escalação 2,8% vs 5,3% (controle MAIOR); CSAT 4,0 vs 3,97; FRT 89 vs 92 min; resolução 37 vs 34,5 h | "CS diz que satisfação está ok" é consistente com os dados — não contradiz o churn |
| H6 — segmento em risco por taxa | **REFUTADA** | nenhum segmento com taxa ≥ 1,5× global (60,2–75,3% vs 70,4%); N≥25 em todos | churn transversal a indústria/canal/plano/trial; MRR_FLAGs mostram concentração de receita, não de taxa |
| H7 — reasons/CSAT sugestivos frágeis | **SUSTENTADA** | CSAT 41,2% nulos; 'unknown' 15,8%; feedback 24,7% nulos; só 21,0% dos eventos têm assinatura encerrada ±30d; CSAT 3,98 vs 3,98 | reason_code não vira causa |
| H8 — exposição precoce é material | **SUSTENTADA** | 68,4% do R1 vem de assinaturas com ≤ 90d de vida (39,6% em ≤ 30d); 53,4% dos primeiros eventos ≤ 90d do signup | onboarding economics é o coração da economia do churn |
| H9 — mecanismo do pico | **SUSTENTADA** | pico 2024-12: bucket 0-3m com 83,7% dos eventos e razão 2,37× a própria baseline | o pico é churn precoce das coortes novas |
| H10 — rotulagem causal | **APLICADA** | tabela de causalidade (§9 do artefato) | nenhum achado vira causa sem rótulo |

## 6. Causa raiz e nível de certeza

**Causa raiz operacional declarada (múltiplas evidências convergentes):** o churn da RavenStack é **churn precoce de coortes novas, concentrado no onboarding** — 75,3% dos primeiros eventos em ≤ 6 meses do signup (H1), 53,4% em ≤ 90 dias (H8); o "aumento recente" é a combinação de (a) **composição**: mais signups em 2024 ampliam o denominador de contas jovens elegíveis (período elevado sustentado 2024-03..2024-12; 80,5% do R1 concentrado em set–dez/2024) e (b) **taxa**: a taxa por conta elegível no pico é 1,73× o esperado pelo mix de tenure, com o bucket 0-3m contribuindo 83,7% do pico a 2,37× a própria baseline (H2+H9). Uso (H3/H4) e suporte (H5) NÃO distinguem churn — os claims do CEO ("uso cresceu", "satisfação ok") são ambos consistentes com os dados e não contradizem o churn. CSAT/reasons são sugestivos frágeis (H7).

**Nível de certeza:** `hipótese causal plausível` para o mecanismo coorte/onboarding (evidência convergente H1+H2+H8+H9, com controle de composição); `descritivo` para a economia do onboarding (R1 é exposição, não perda; cenários CAC-equivalent nomeados); `não identificável` para qualquer papel causal de uso/suporte/reasons nesta base (decoplamento estrutural). Separação explícita "o que sabemos" vs "o que ainda é hipótese": sabemos os números acima (re-executáveis); é hipótese que o mecanismo operacional seja falha de onboarding/ativação (dado adicional: ativação real, integrações, contato de CS pós-signup — não existem na base).

## 7. Erros reais encontrados e corrigidos (pelo executor, durante a execução — nenhum inventado)

1. **ZeroDivisionError no H4** (primeira execução) — `med_churn / med_ctrl` com controle mediano 0. Causa: falta de guarda. Correção: ratio com guarda `if med_ctrl > 0` e formatação `NA`. Resultado: exit 0.
2. **G5-km falso FAIL (8 violações)** — gate exigia `S(0) = 1`, mas eventos ocorrem no mês 0 (mês do signup), tornando `S(0) < 1` legítimo. Correção: gate verifica `at_risk(0) = N da coorte`, S ∈ [0,1] e monotonicidade (tolerância de arredondamento 1e-3). Resultado: 0 violações em 8 coortes.
3. **G7-support falso FAIL** — pool contava 21 **meses** como N por lado; o pré-registro exige N ≥ 30 **contas** por lado. Correção: `support_analysis` reescrita com sinais por conta (groupby por janela) e `n_account_month` acumulado (churn 346 / controle 3.288). Resultado: gate PASS; leitura correta do §6.
4. **"Pico" enganoso no report** — a primeira versão apresentava o primeiro mês elevado (2024-03) como "pico"; o pico real por contagem e por taxa é 2024-12 (43 eventos; 22,51%). Causa: `spike_months[0]` (ordenação crescente) usado como pico. Correção: `spike_decomposition` distingue **período elevado** (regra pré-registrada 1,5× mediana) de **pico** (mês de maior contagem), decompõe o pico e adiciona **controle de composição de tenure** (esperado 24,82 vs observado 43). Resultado: H2/H9 corretos e interpretáveis.
5. **Bucket de duração sem a faixa 0d** — 13 assinaturas com start = end (46.324; 3,9% do R1) ficavam fora de todos os buckets (shares somavam 96%). Causa: `DURATION_BUCKETS` começava em 1-30d. Correção: bucket `0d` explícito + gate **G11** (Σ buckets = R1 total). Resultado: share fecha 100%; CAC-equivalent consistente.
6. **Formatação float de colunas inteiras** ("<= 30.0d: 91.0 contas") — cast `int()` no render. Resultado: leitura limpa.

## 8. Validações executadas

| Validação | Comando | Resultado |
|---|---|---|
| Syntax/import | `python3 -m py_compile solution/src/03_root_cause.py`; execução de módulo | OK; imports: stdlib + pandas + matplotlib (Agg) |
| Execução | `python3 -W ignore solution/src/03_root_cause.py` (workdir = pasta da submissão) | exit 0; 23 PASS / 0 WARN / 0 FAIL |
| Idempotência | 2 execuções; `md5sum` de report + 13 tabelas + 6 gráficos | byte-a-byte idênticos (report `6324b0d4…`) |
| CWD diferente | execução a partir de `/tmp` com path absoluto do script | exit 0; report idêntico (MD5 igual) |
| Offline | inspeção de imports (stdlib + pandas + matplotlib; nenhuma chamada de rede) | sem rede |
| Sandbox — coluna `churn_date` renomeada | cópia da solução em sandbox fora do repo | exit 1; relatório regravado com "Falha estrutural"; sem traceback; outputs de dados não regenerados |
| Sandbox — arquivo `churn_events.csv` ausente | remoção do arquivo no sandbox | exit 1; FAIL registrado; sem traceback |
| Verificações manuais | 3 sessões independentes (MV-1/MV-2/MV-3, §6) | 3/3 PASS |
| Consistência report↔CSV | script independente (asserts sobre t01/t02/t03/t07/t10 vs texto do report) | todos os asserts PASS |
| Gráficos | dimensões PNG (394–685 px de altura, 1050–1713 px de largura); não-brancos (258–783 cores únicas) | 6/6 íntegros |
| Hygiene | `git diff --check` (após staging) | limpo |
| Escopo | `git status`/`git diff` | somente arquivos de `submissions/jose-nascimento/` |
| Paths pessoais/segredos | grep por `/tmp`, `/home`, `ubuntu` nos artefatos da solução | zero ocorrências fora do prompt arquivado (exceção documentada, regra 8 do plano) |

## 9. Sensibilidades executadas

- **Grão evento vs assinatura**: tempo-ao-churn e taxa usam primeiro evento por conta (lente C); receita usa R1 (exposição) e R2 (estado) separadamente — nunca misturadas (contrato §4/§5).
- **Janelas 30/60/90d**: onboarding por duração de assinatura E por primeiro evento; ambas reportadas.
- **Registros temporais válidos vs todos**: uso e tickets com pré-signup excluído no primário; sensibilidade explícita (uso total: +225,3% vs +1,1% com pré-signup; tickets pré-signup contabilizados no suporte).
- **Denominadores**: elegível (início do mês, contrato §5) para primeiro evento; ativa (fim do mês) para eventos totais; ambas na tabela t01.
- **Censoring**: taxa observada (eventos/n) vs estimativa KM; Q4-2024 notada como não comparável a janela completa; `km_surv_t6` vazio quando não observado.
- **Composição de tenure**: controle padronizado no H2 (esperado 24,82 vs 43).
- **Suporte**: controle nunca-churn (0,378 tickets/conta) e estratificação por tenure (0-6m/7-12m/13+m) — nenhuma inverte o NO-GO.
- **Múltiplos eventos**: primeiro evento por conta em tudo que é taxa/coorte (nunca episódio = logo perdido; contrato §7).

## 10. Riscos e pendências

1. **Review gate 3x da Iteração 03** — obrigatório (regra 2 do plano); orquestrador deve disparar 3 agentes `deepseek-max` read-only; ledger `process-log/reviews/iteration-03-review-summary.md` a criar. Permanece `PENDING`.
2. **Sinteticidade e decoplamento**: uso/suporte/eventos são gerados independentemente do ciclo de vida (76,6% de uso fora da janela; 21% de eventos alinhados a `end_date`); qualquer inferência causal além do mecanismo coorte/onboarding é `não identificável` por construção.
3. **Concentração de R1 em dez/2024** (48,7% do R1 no mês): descritiva; pode ser artefato de geração — não interpretada como causa; handoff It04 deve manter o rótulo.
4. **Determinismo vs versão de pandas** — outputs idênticos com pandas 3.0.5; pinning é objeto da Iteração 06.
5. **Push** — depende de rede/credenciais; se falhar, commit permanece local e o estado real é reportado.

## 11. Handoff explícito para a Iteração 04

**Ao orquestrador (opencode):** a Iteração 03 está `CONCLUDED` (validação do executor concluída; review gate 3x a disparar). Disparar o próximo agente executor `deepseek-max` para a **Iteração 04 — Ciclos de reativação, jornada completa da conta e watchlist**, com:

1. **Entradas:** `solution/evidence/03_root_cause_report.md` (achados e vereditos), `solution/out/tables/` (t01–t10), `solution/out/charts/` (6 PNGs), contrato analítico, `process-log/hypotheses/iteration-03-root-cause-hypotheses.md`, decisions file da It03.
2. **Achados que a It04 deve respeitar (não re-derivar nem contradizer):** churn é precoce (75,3% ≤ 6m; mediana 3m); pico 2024-12 com mecanismo bucket 0-3m; exposição R1 precoce material (68,4% ≤ 90d); uso/suporte/reasons não distinguem churn (NO-GO documentado — não usar como features de watchlist sem rótulo); nenhum segmento com taxa ≥1,5× global; 0 contas inativas no corte pela lente de assinatura (a watchlist não pode ser só "contas com evento" — precisa de jornada completa e estado no corte).
3. **Restrições:** nada fora de `submissions/jose-nascimento/`; sem recomendações (It05); sem modelo preditivo; lente declarada por pergunta; `churn_flag_snapshot_2024_12_31` proibido como feature (contrato §8); CSAT/reasons sugestivos.
4. **Critérios de aceitação objetivos (execution-plan §Iteração 04):** watchlist com contas reais (ID, MRR, sinal, ação); regra de agregação/cap explícita; viés contra contas novas declarado; reativações quantificadas; números reproduzíveis.
5. **Retorno ao orquestrador:** report estruturado com Status PASS/BLOCKED, commit hash, validações, riscos — sem conclusão simulada se algo bloquear.

---

*Prompt integral em [`process-log/prompts/iteration-03-prompt.md`](../prompts/iteration-03-prompt.md); hipóteses em [`process-log/hypotheses/iteration-03-root-cause-hypotheses.md`](../hypotheses/iteration-03-root-cause-hypotheses.md); decisões em [`process-log/decisions/iteration-03-root-cause-decisions.md`](../decisions/iteration-03-root-cause-decisions.md).*