# Erros reais da IA e correções aplicadas — ledger consolidado (It00–07)

- **Tipo:** artefato obrigatório do process log (Iteração 08) — item D14 do checklist do orquestrador
- **Escopo:** exatamente **8 erros materiais reais** do processo, selecionados por valor (impacto na análise, risco de reprovação ou lição de processo), **não** cosméticos. Nenhum erro aqui é inventado ou "exemplo ilustrativo": todos foram detectados, corrigidos e validados dentro do próprio processo, com commit e evidência versionada.
- **Definição de "erro material":** output errado ou enganoso (número, gráfico, claim, comportamento de falha) que, se não corrigido, produziria conclusão falsa, diagnóstico inútil ou risco de reprovação — distinto de melhoria de redação/LOW sem impacto (esses vivem nos review summaries, não aqui).
- **Detecção:** 3 revisores `deepseek-max` read-only por gate (contextos separados; erros correlacionados possíveis — ver `../management/orchestration-architecture.md` §6), inspeção ocular do orquestrador (exceção documentada), ou validações executáveis.
- **Registro primário por iteração:** `../reviews/iteration-XX-review-summary.md` (matriz finding→ação→arquivo:linha, recálculos, gate) e `../reports/iteration-XX-review-fix-report.md`; este ledger é a síntese navegável.
- **Contagem:** 8 entradas (E1–E8), uma por erro material; números e hashes conferem com os artefatos citados.

---

## E1 — It01: schema ausente/renomeado → `KeyError` + relatório de auditoria stale

- **Etapa:** Iteração 01 (ingestão e auditoria dos 5 datasets).
- **Output errado:** com coluna esperada ausente ou renomeada (ex.: `account_id`→`acct_id`, `industry`→`industria`), o script registrava `S01 FAIL` mas seguia nos checks semânticos, levantava `KeyError` com traceback e **não regravava** `solution/evidence/01_audit_report.md` — o relatório versionado anterior permanecia com 0 FAIL (stale), como se o pipeline tivesse passado.
- **Por que plausível/perigoso:** o exit code continuava 1 (gate respeitado na superfície), então a falha parecia "tratada"; mas o artefato público de evidência ficava desatualizado e o diagnóstico era um traceback cru, sem FAIL estruturado. Avaliador (ou re-execução) veria relatório antigo com 0 FAIL e contagens que não correspondem aos dados.
- **Detectado por:** os 3 revisores (finding convergente M1, MEDIUM) — reproduzido em sandbox por 3/3.
- **Causa raiz:** acesso sem guarda a `df[key]`/`df[col]` em 7 checks (`check_schema`, `check_types_ranges`, `check_ids`, `check_dates`, `check_global_window`, `check_cross_tables`, `collect_syntheticity_evidence`); `render_report`/`write_text` apenas no fim de `main()` — qualquer exceção interrompia antes da regravação.
- **Decisão/correção:** guards de coluna por check (`missing_cols`/`guard_columns`/`cross_blocked`); checks dependentes registram FAIL "não executado (schema)"; checks possíveis preservados; **sem catch-all** (bugs reais continuam propagando); relatório sempre regravado com os FAILs; exit 1 com diagnóstico estruturado.
- **Validação:** 5 cenários pós-fix (arquivo ausente, chave ausente, coluna categórica ausente, data inválida, arquivo vazio) — todos sem traceback, com relatório regravado e idempotentes; baseline 72 PASS / 18 WARN / 0 FAIL inalterado.
- **Commit:** `b9823da` (`fix: handle schema failures in data audit`) — evidência: [review summary It01](../reviews/iteration-01-review-summary.md) §2/§4/§7.

---

## E2 — It02: lente de revenue churn por winner quase degenerada — encerramentos não dominantes invisíveis

- **Etapa:** Iteração 02 (reconciliação das definições de churn e contrato analítico).
- **Output errado:** a fórmula única de "revenue churn" baseada no winner (Σ winner MRR de contas que ficam inativas) capturava apenas **18.507** (2 transições na janela), enquanto a exposição contratual bruta era **1.179.139** (486 assinaturas encerradas) e as saídas **não-dominantes** (assinaturas encerradas com a conta permanecendo ativa) somavam **422.691** em 274 assinaturas — razão ≈22,8× do capturado. Exemplo material: A-5a215a em 2024-12 — duas assinaturas de 17.313 (34.626) encerram com winner inalterado em 17.313 (perda invisível). O contrato §5 não sinalizava essa magnitude.
- **Por que plausível/perigoso:** "revenue churn" é a métrica que um CEO lê primeiro; subestimada em ~23×, a decisão de negócio mudaria (parecer que não há perda de receita quando a exposição é grande). Números de qualidade também hardcoded no render (M2), o que escondia a origem.
- **Detectado por:** revisor R3 (review-8b41e9c2, MEDIUM M1 + M2); os 3 revisores concordaram na correção (2 veredictos `PASS`, 1 `PASS_WITH_FIXES`).
- **Causa raiz:** lente única baseada no estado dominante da conta (winner) — saídas de assinaturas não-dominantes são estruturalmente invisíveis; sem lentes separadas por pergunta (exposição bruta vs perda líquida de estado) e sem política de `closed_at`.
- **Decisão/correção:** duas lentes nomeadas no contrato §5/§6 — **R1 gross subscription ending MRR** (exposição bruta; NÃO "receita perdida" automática) e **R2 net account-state MRR loss** (churn-to-inactive 18.507 + active contraction 150.817); winner preservado como estado/risco e **proibido** como total de churn contratual isolado; colunas auditáveis `mrr_ended_in_month`/`n_ended_in_month` + invariante G14; gap quantificado em runtime; política de `closed_at` (D10).
- **Validação:** recálculo independente 46/46 (incl. 1.179.139/486, 18.507, 150.817, 422.691, exemplo A-5a215a); 31 PASS / 1 WARN / 0 FAIL; 3 cenários de FAIL estrutural sem stale/traceback.
- **Commit:** `9378a86` (`fix: strengthen revenue churn contract`) — evidência: [review summary It02](../reviews/iteration-02-review-summary.md) §2–§6; [decisões It02](../decisions/iteration-02-analytical-contract-decisions.md) D9/D10.

---

## E3 — It03: meses pré-signup padronizados como zero → hipótese H4 com Δ artificial

- **Etapa:** Iteração 03 (causa raiz, coortes e onboarding economics).
- **Output errado:** a comparação de uso pré-evento (H4) contava meses anteriores ao signup como **zero** nos dois lados → "zero-uso: churn 73,9% vs controle 60,2% (Δ 13,7 p.p.)", artefato de exposição ≈9× maior que o efeito real. O veredito mecânico da hipótese ficava artificialmente forte.
- **Por que plausível/perigoso:** H4 (uso como sinal pré-evento) era candidata a entrar na narrativa causal; um Δ de 13,7 p.p. contra threshold pré-registrado de 25 p.p. ainda refutava, mas com margem falsa — e qualquer leitura do número como "uso distingue churn" seria enganosa. Meses inexistentes como zero é um viés clássico de janela.
- **Detectado por:** revisor review-4c090c69 (M1 material; 1/3 — encontrado por um revisor, confirmado pelos demais no recálculo).
- **Causa raiz:** janela de comparação não restrita a `pm >= signup_month`; meses anteriores ao signup entravam no denominador como zero por construção.
- **Decisão/correção:** janela restrita ao período pós-signup nos DOIS lados; recálculo **61,7% vs 52,7% (Δ 9,0 p.p.)**; veredito REFUTADA inalterado (mais robusto); erro registrado como erro real (decisões D7; report §7.7; nota no t10).
- **Validação:** recálculo independente 49/49 (715/4.283 valores pós-signup conferidos); 23 PASS / 0 WARN / 0 FAIL; report↔CSV linha a linha.
- **Commit:** `12ff47c` (`fix: correct exposure windows in root cause analysis`) — evidência: [review summary It03](../reviews/iteration-03-review-summary.md) §2–§3.

---

## E4 — It03: KM por tempo exato → células vazias (censura mal apresentada) + gráfico B cortado

- **Etapa:** Iteração 03 (mesma correção do gate).
- **Output errado:** (a) sobrevivência KM t6/t12/t18 calculada por "tempo exato" gerava **células vazias** onde o follow-up não alcança o horizonte (ex.: t12 da coorte 2023Q2 vazio; t6 das coortes 2024Q3/Q4 vazio) — leitura "coorte sem sobrevivência" em vez de "não observável"; (b) gráfico B (`b_km_by_signup_quarter.png`) com ylim padrão cortava curvas abaixo de 0,55 e legenda sobre o título.
- **Por que plausível/perigoso:** células vazias em tabela de sobrevivência são interpretadas como dado ausente/erro por avaliador; o gráfico B subestimava visualmente a sobrevivência das coortes recentes — exatamente as coortes do diagnóstico (churn precoce).
- **Detectado por:** revisores (L5/INFO-1/#6 para KM; #5 para o gráfico B) — findings convergentes de robustez/apresentação.
- **Causa raiz:** lookup por tempo exato em vez de função degrau (maior t observado ≤ horizonte); ylim default + legenda dentro da área de plotagem no gráfico B.
- **Decisão/correção:** helper `surv_at_horizon` (função degrau; vazio só se não observável) para coortes e segmentos; gráfico B com ylim (0,0; 1,02) e legenda fora da área; t12 2023Q2 passa a **0,7037**; t6 de coortes sem follow-up permanece vazio com regra explícita.
- **Validação:** 49/49 recálculo independente (incl. KM + carry-forward); gráfico B com 8/8 coortes íntegras; 23 PASS / 0 WARN / 0 FAIL.
- **Commit:** `12ff47c` (mesma correção do gate It03) — evidência: [review summary It03](../reviews/iteration-03-review-summary.md) §2 (L5/INFO-1/#6, #5), §3.

---

## E5 — It04: mapeamento visual R_D↔R_F invertido no backtest (gráfico mostrava o oposto do validado)

- **Etapa:** Iteração 04 (backtest point-in-time e watchlist) — gráfico `It04_d_backtest_lift.png`.
- **Output errado:** a linha rotulada `R_D onboarding<=90d` exibia os lifts de R_F (~0,66/0,40/0,92) e a linha `R_F A e C` (sombreada) exibia os lifts de R_D (1,57/1,56/1,83). Extração keyed pré-fix: **26 dos 27 pares (rule, cutoff) divergiam de t14** (só a regra E, posição simétrica, coincidia).
- **Por que plausível/perigoso:** é o gráfico central da evidência temporal — mostrava exatamente o contrário do achado validado (onboarding como a ÚNICA regra com lift consistente). Um leitor CEO confiaria no gráfico e concluiria o oposto do diagnóstico. Pior: os **validadores programáticos passaram** (mediam bboxes/ink, não os dados dos artists), então o erro sobreviveu ao gate.
- **Detectado por:** **inspeção ocular do orquestrador** (exceção documentada à regra "não executa": visualiza PNGs e descreve problemas) — ver `../reports/orchestrator-visual-correction-report.md`.
- **Causa raiz:** `y = len(rules) - 1 - j` (ordem invertida) vs yticklabels na ordem natural de `RULES` — reversão em cadeia A↔I, B↔H, C↔G, D↔F; a faixa de destaque `axhspan(4.5, 5.5)` cobria o y do label R_F.
- **Decisão/correção:** associação **keyed** `rule → y` (mesma ordem dos labels); faixa de destaque keyed em R_D; **gate programático embutido** no `chart_d` (27 pares == t14; R_D exato 1,574/1,556/1,835; y destacado resolve para o label R_D); rodapés curtos/2 linhas e margens em a/b/c/d (It04_c intocado). Commit `617e4ac` (`fix: align chart labels and final visual spacing`).
- **Validação:** extração keyed pós-fix **27/27 == t14**; teste negativo (corromper R_D → `RuntimeError` com mensagem) ; 26/26 CSV/MD numéricos byte-idênticos ao pré-fix; idempotência 2×; scripts 23/34 PASS.
- **Commit:** `617e4ac` — evidência: [relatório da correção visual](../reports/orchestrator-visual-correction-report.md) §1–§4; [review summary It04](../reviews/iteration-04-review-summary.md) §10.

---

## E6 — It05: regra de decisão GO ≥10% por ponto, sem considerar poder/IC do experimento

- **Etapa:** Iteração 05 (ações, impacto e plano de medição).
- **Output errado:** a regra "GO se redução relativa ≥ 10%" era um threshold **operacional por ponto**, sem vínculo com a estatística do experimento: MDE a 80% power ≈ **37%** (N=136/braço), poder por cenário ≈ **11/31/61%**, **P(falso GO sob nulo) ≈ 24%** — o GO dispararia por ruído em ~1 de 4 experimentos nulos. Junto: linha `annualized` enganosa na t19 (N=320 = 4×estoque vs fluxo real 273/ano) e faixa 0,3393–0,5417 apresentada como se fosse intervalo de confiança (era min/max por cutoff); "evitados" no t18 implicava causalidade não testada.
- **Por que plausível/perigoso:** a recomendação nº 1 (escalar o programa de ativação) seria autorizada por um critério que confunde ponto estimado com evidência; um avaliador com rigor estatístico reprovaria a regra; a faixa rotulada como CI é claim falso de precisão.
- **Detectado por:** **3/3 revisores convergiram** (M1 — review-9a2752e1, review-838ab021, review-c17f9a4e).
- **Causa raiz:** regra de decisão escrita por ponto (piso operacional) sem parear com o desenho experimental (poder/IC); convenções de display (faixa vs CI; annualized) não nomeadas; sequenciamento ACT-01→ACT-03 sem SLA.
- **Decisão/correção:** regra de decisão em **3 estados** — SCALE/GO = ponto ≥ 10% (piso preservado) **E IC95 exclui 0**; CONTINUE/LEARN = ponto favorável com IC95 cruzando 0 (sem alegar eficácia); STOP/HARM = efeito adverso com IC95 excluindo 0 ou guardrail falhado. Poder/falso-GO/Wilson **derivados em runtime** (gates G13); `annualized` removido (gate G13-annualized-absent); faixa nomeada `observed cutoff range` ≠ CI; Wilson 95% 0,362–0,501 derivado separadamente; ACT-03 → Now/pré-requisito com SLA ≤ 30d e ACT-01 gated por instrumentation readiness.
- **Validação:** 45 PASS / 0 WARN / 0 FAIL; recálculo independente (power 10,8/30,9/60,6%; falso-GO 23,7%; Wilson; disjoint 193/0); idempotência 2× + CWD; 6 PNGs byte-idênticos.
- **Commit:** `e0c6b7e` (`fix: align impact scenarios with experiment power`) — evidência: [review summary It05](../reviews/iteration-05-review-summary.md) §1–§4.

---

## E7 — It06: valor categórico inválido → `KeyError` + relatório stale; e pycache gerado pelo próprio verificador

- **Etapa:** Iteração 06 (pipeline de 1 comando e validação técnica).
- **Output errado:** (a) valor categórico inválido com schema intacto (ex.: `churn_flag=TruX` em accounts ou subscriptions) crashava o estágio 01 com `KeyError` + traceback em `check_cross_tables` e **não regravava o relatório** (stale) — mesma classe do E1, agora por corrupção de **valor**; (b) a invocação direta documentada do verificador (`python3 solution/src/06_verify_pipeline.py`) criava `solution/src/__pycache__/` (via importlib no check E2), fazendo o próprio check D1 (zero binários/cache) falhar na execução seguinte — 9 FAILs reproduzidos pelos revisores.
- **Por que plausível/perigoso:** corrupção de dados é o cenário de FAIL que o pipeline promete diagnosticar; crash obscuro + relatório antigo com 0 FAIL era exatamente o comportamento que o avaliador testaria. O verificador que se auto-corrompia invalidava a verificação de higiene (D1) em re-execuções — contradição com a proposta de reprodutibilidade.
- **Detectado por:** (a) review-18199ddc (F1 MEDIUM); (b) review-f1fa7caa (F1 MÉDIO, 9 FAILs reproduzidos) — gate com veredictos `PASS_WITH_FIXES`/`PASS`/`PASS_WITH_FIXES`.
- **Causa raiz:** masking de `churn_flag` executado antes de validar o domínio booleano (sem guard de valor); importlib do check E2 gravando bytecode na árvore; contagens 41/46 e claim de ambiente x86_64 vs aarch64 real (mesmo gate, corrigidos).
- **Decisão/correção:** `guard_bools` valida o domínio booleano ANTES de qualquer masking → FAIL estruturado "não executado (validação)", relatório regravado, exit 1, **sem catch-all**; `sys.dont_write_bytecode = True` no topo do verificador + `PYTHONDONTWRITEBYTECODE=1` em run.sh/Makefile (defesa em profundidade); gate D7-uids (colisão de uid); `PYTHON ?= python3` no Makefile; ambiente documentado como Linux/aarch64; contagens derivadas (40/45).
- **Validação:** clone fresco — `./run.sh` 2× + `make all` + CWD: **45/45 outputs byte-idênticos**, **68 PASS / 0 FAIL**, **zero `__pycache__`** (incl. invocação direta 2×); 6 cenários de FAIL (dado ausente, python ausente, deps ausentes, schema quebrado, categórico inválido ×2, corrupção composta) sem traceback e sem stale.
- **Commit:** `fa6572f` (`fix: harden fresh-clone pipeline verification`) — evidência: [review summary It06](../reviews/iteration-06-review-summary.md) §1–§3.

---

## E8 — It07: drift de contagens, truncamento de tabela e word count no teto (clareza executivo)

- **Etapa:** Iteração 07 (relatório executivo e visualizações).
- **Output errado:** docs de processo com números stale (README "11 commits" vs 24 reais; execution-plan com "2.391 palavras/315 summary/71 PASS"; "7 tabelas" vs 6 reais); tabela de ações do relatório com **células cortadas no meio da palavra** ("0-90d: m", "PM Onboarding (desenho", ">= 10%" sem "e IC95 exclui 0") e sem marcador de corte; word count no teto do budget (2.389/2.400, margem 11); report pós-regeneração com modo 0600 vs 0644 commitado; `lift` sem definição na primeira ocorrência; adendo do outline com precisão incompleta (P(falso GO) ≠ arredondamento).
- **Por que plausível/perigoso:** avaliador lendo docs de processo encontra contagens contraditórias entre si e com o repo (drift); tabela truncada no meio de palavra parece bug de render e esconde o critério de decisão (IC95 exclui 0); word count no teto quebra se qualquer adição de It08/09 passar; modo 0600 pós-regeneração quebra o determinismo percebido.
- **Detectado por:** 3/3 revisores (LOWs convergentes; nenhum finding analítico/material — o núcleo 88/88 âncoras foi validado por todos).
- **Causa raiz:** contagens estáticas não sincronizadas após correções; clipping de célula sem marcador e sem gate pós-render; sem re-medição de word count após edições; `mkstemp` gerando 0600.
- **Decisão/correção:** contagens estáticas removidas ou descritas como medidas em runtime (gate G6); tabela de ações compacta de 5 campos com cortes **somente em fronteira de palavra** e '…' explícito + **novo gate G3b** no gerador (detecta células penduradas/regressões de render); word count restaurado para **2.275** (margem ~125; auditoria: zero números removidos); `os.chmod(tmp, 0o644)` antes do replace; `lift` definido na 1ª ocorrência; adendo §13.3/§15 precisado (~8 p.p. por convenção de cálculo, não arredondamento).
- **Validação:** clone fresco — report byte-idêntico (2× run + CWD), **77 PASS / 0 FAIL**, modo 0644, FAIL de input ausente sem stale, 6 PNGs inalterados, `git diff --check` limpo.
- **Commit:** `a1e99cb` (`docs: polish executive report for decision clarity`) — evidência: [review summary It07](../reviews/iteration-07-review-summary.md) §2; [fix report It07](../reports/iteration-07-review-fix-report.md) §2–§3.

---

## Notas de leitura

- **E1 e E7 são a mesma classe de falha em duas iterações** (guard de schema vs guard de valor): a It02 aplicou a lição do E1 ao contrato (bloqueio estrutural), e a It06 fechou o guard de valor no pipeline integrado — registrado por honestidade, não para "encher".
- **Detecção humana vs modelos:** E5 foi detectado pelo **orquestrador (modelo)** via inspeção ocular — nenhum erro foi detectado por atividade manual do candidato; o candidato definiu a **exigência** de inspeção visual e auditoria final (ver `../decisions/decision-ledger.md`).
- **Nenhuma iteração relatou "não houve erros"** — inclusive a It07 (apenas LOWs, mas documentais e corrigidos).
- Veredictos por gate e matrizes completas: `../reviews/` (8 summaries versionados); os reports brutos dos revisores são working artifacts fora do repo (não versionados) — os summaries são a evidência persistente.