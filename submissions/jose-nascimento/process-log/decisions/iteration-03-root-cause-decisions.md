# Decisões — Iteração 03 · Causa raiz, coortes e onboarding (problema → opções → evidência → decisão → trade-off)

- **Iteração:** 03 (causa raiz, coortes e economia do onboarding)
- **Data:** 2026-08-28
- **Executor:** exatamente um subagente `deepseek-max` (via OpenCode Go), sob orquestração do opencode — julgamento do executor registrado de forma explícita vs output/contexto da IA, conforme regra de governança.
- **Evidência dos números:** todas as decisões abaixo usam números re-derivados dos 5 CSVs commitados (`solution/data/raw/`) e do painel (`solution/data/processed/account_month.csv`) pelo `solution/src/03_root_cause.py`; nada é copiado de fonte externa. Thresholds das hipóteses foram fixados ANTES da análise (`process-log/hypotheses/iteration-03-root-cause-hypotheses.md`).

---

## D1 — "Pico" = mês de maior contagem; "período elevado" = regra pré-registrada 1,5× mediana

- **Problema:** a primeira versão do script apresentava como "pico" o PRIMEIRO mês elevado (2024-03, 18 eventos) por usar `spike_months[0]` (lista ordenada crescentemente). O mês de maior contagem — e de maior taxa — é 2024-12 (43 primeiros eventos; 22,51%). O headline ficava enganoso.
- **Opções:** (1) pico = primeiro mês elevado; (2) pico = mês de maior contagem; (3) pico = mês de maior taxa.
- **Evidência:** série mensal (t01): 2024-03..2024-12 todos com first_events ≥ 1,5× mediana (nível elevado sustentado); 2024-12 = máximo em contagem (43) E em taxa (22,51%).
- **Decisão:** opção 2 — pico = mês de maior contagem de primeiros eventos (desempate: primeiro cronologicamente); "período elevado" reportado como contexto (2024-03..2024-12). Decomposição (H9) e comparações (H2) usam o pico.
- **Trade-off:** um único mês de pico simplifica a leitura; o caráter "sustentado" do aumento fica explícito na seção de período elevado.

## D2 — Controle de composição de tenure no H2 (esperado por mix de tenure × baseline de bucket)

- **Problema:** a taxa bruta do pico (22,51% em 2024-12) mistura dois efeitos: (a) o pool elegível em dez/2024 é composto majoritariamente por contas jovens (as antigas já tiveram primeiro evento), e contas jovens têm baseline de churn mais alto; (b) uma taxa real acima do baseline. Comparar a taxa bruta com a mediana da janela não separa (a) de (b).
- **Opções:** (1) apenas taxas brutas (threshold pré-registrado); (2) + controle padronizado: eventos esperados = Σ_bucket contas elegíveis no bucket × taxa-baseline do bucket (média dos 6 meses anteriores); (3) modelo estatístico (fora de escopo).
- **Evidência:** esperado 24,82 eventos pelo mix de tenure; observado 43 → ratio 1,73× — o aumento persiste após o controle de composição.
- **Decisão:** opção 2 — o veredito mecânico do H2 usa os thresholds brutos pré-registrados (razão vs mediana da janela e vs mediana dos 6 meses anteriores); o ratio padronizado entra nos números/nota como sensibilidade e no process report como interpretação.
- **Trade-off:** mais um número para explicar; em troca, o confundidor de composição (listado na hipótese H2) é efetivamente controlado, não apenas nomeado.

## D3 — Suporte: desenho calendar-time com janela pré-evento de 90 dias; controles nunca-churn e por tenure como sensibilidades

- **Problema:** comparar "contas que churnam" com "contas que não churnam" diretamente tem viés de sobrevivência e de calendário (janelas de observação diferentes).
- **Opções:** (1) churn vs nunca-churn sem alinhamento; (2) por mês m: churn = primeiro evento em m; controle = elegíveis no início de m sem evento em m (calendar-time; controles podem churnar depois — o que é honesto: ainda não churnaram em m); janela W(m) = [dia 1 de m − 90d, dia 1 de m); (3) matching 1:1 por signup.
- **Evidência:** N por lado 346 vs 3.288 conta-mês (≥ 30 exigidos); resultados idênticos em direção com controle nunca-churn e estratificação por tenure (nenhuma inverte o NO-GO).
- **Decisão:** opção 2 como primário + sensibilidades (nunca-churn; estratificação 0-6m/7-12m/13+m; tickets pré-signup excluídos no primário).
- **Trade-off:** controles de meses iniciais incluem contas que churnarão depois (diluição conservadora — o sinal, se existisse, seria subestimado; o NO-GO é portanto conservador).

## D4 — Bucket `0d` (start = end) na economia do onboarding; share fecha 100% do R1

- **Problema:** 13 assinaturas encerradas no mesmo dia do início (46.324; 3,9% do R1) caíam fora de todos os buckets de duração (1-30d…), e a tabela de exposição por duração somava 96% do R1 — inconsistência detectada na verificação report↔CSV (CAC 12× de 90d ≠ 12× soma dos buckets).
- **Opções:** (1) ignorar (silencioso); (2) bucket `0d` explícito + gate G11 (Σ buckets = R1 total).
- **Evidência:** 13 subs same-day, todas no fim de 2024; incluídas no ≤90d da exposição.
- **Decisão:** opção 2 — `0d` visível na tabela, no gráfico e no gate; nada descartado silenciosamente (mesma política do contrato §9).
- **Trade-off:** uma categoria a mais no gráfico; em troca, auditabilidade total (100% do R1 explicado por faixa de duração).

## D5 — CSAT/resolução só com tickets fechados e com nota; pré-signup excluído no primário de uso/tickets

- **Problema:** CSAT com 41,2% de nulos e 1.077 tickets anteriores ao signup podem vazar ou inflar sinais.
- **Opções:** (1) usar todos os tickets; (2) política do contrato §10 (fechados com nota; denominador explícito) + excluir pré-signup no primário com sensibilidade.
- **Evidência:** G15 (It02): 0 nulos de `closed_at`; nulos de satisfação excluídos com denominador explícito.
- **Decisão:** opção 2 — seguindo o contrato congelado; sensibilidade com pré-signup incluído reportada (uso total +1,1% vs +225,3%).
- **Trade-off:** primário mais limpo; a diferença entre variantes fica explícita (e é material no uso).

## D6 — Sem modelo preditivo: NO-GO com números (sinais de uso/suporte não distinguem churn)

- **Problema:** o diferencial do challenge permite modelo preditivo; sem sinal pré-evento, um modelo seria autoengano.
- **Opções:** (1) construir modelo com features de painel; (2) não construir, documentando o NO-GO com números.
- **Evidência:** H4 REFUTADA (zero-uso pré-evento 73,9% vs 60,2%; Δ 13,7 p.p. < 25) e H5 REFUTADA (tickets/conta 0,309 vs 0,352; escalação 2,8% vs 5,3%; CSAT 4,0 vs 3,97) — nenhum sinal pré-evento distingue churn; o mecanismo identificado é coorte/onboarding (taxas, não preditores).
- **Decisão:** opção 2 — NO-GO documentado; a Iteração 05 decide formalmente sobre o diferencial com esta evidência.
- **Trade-off:** sem diferencial de ML; em troca, honestidade analítica (nenhum número inventado por um modelo sem sinal).

---

## Adendo — Correções do review gate It03 (2026-08-28; ver `process-log/reviews/iteration-03-review-summary.md`)

> As decisões D1–D6 acima permanecem como registradas. Este adendo documenta as correções aplicadas pelo agente sequencial após o review gate 3x (veredictos `PASS_WITH_FIXES` ×3). Hipóteses pré-registradas NÃO foram alteradas (arquivo `process-log/hypotheses/iteration-03-root-cause-hypotheses.md` intacto entre `8cb93c3` e o commit de correção — verificado por git).

## D7 — H4: janela de exposição restrita a tempo em risco/observável (meses ≥ signup); Δ 13,7 p.p. registrado como artefato

- **Problema (finding M1, revisores):** a janela pré-evento do grupo churn (`months[mi-3:mi]`) não filtrava `pm >= signup_month` — 333 de 1.048 valores (31,8%) eram meses anteriores ao signup (período inexistente, contrato §2) contados como zero por construção. O controle tinha o mesmo erro no caso `m == signup_month` (810 de 5.093 valores = 15,9%). O zero-uso reportado (73,9% vs 60,2%; Δ 13,7 p.p.) superestimava a associação pré-evento.
- **Opções:** (1) corrigir só o lado churn (61,7% vs 60,2%; Δ 1,5 p.p. — o controle permaneceria com 810 zeros pré-signup, contrariando o contrato §2); (2) corrigir os DOIS lados simetricamente (só meses ≥ signup).
- **Evidência:** recálculo independente (script próprio, 49/49 checks): lado churn pós-signup = 715 valores, zero-uso 61,7%; lado controle pós-signup = 4.283 valores, zero-uso 52,7%; Δ = 9,0 p.p.
- **Decisão:** opção 2 — "não padronize período inexistente como zero" vale para os dois lados; a expectativa dos revisores (60,2% no controle) mantinha o viés no controle e é documentada como tal no review summary. Threshold pré-registrado (25 p.p.) preservado; veredito **REFUTADA** inalterado e mais robusto (Δ 9,0 < 25 p.p.).
- **Trade-off:** o número corrigido difere da estimativa inicial dos revisores; em troca, o desenho fica contratualmente correto e simétrico.

## D8 — H6: threshold RATE_FLAG estruturalmente inalcançável — erro de desenho do pré-registro, documentado (não renegociado)

- **Problema (L2/LOW-6/finding #7):** com taxa global 70,4%, o limiar 1,5× = 105,6% > 100% — o teste de taxa nunca poderia disparar; o veredito mecânico "REFUTADA por RATE_FLAG" era pré-determinado e pouco informativo.
- **Opções:** (1) ignorar e manter o veredito como "teste informativo"; (2) documentar o erro de desenho e basear a conclusão no critério alternativo pré-registrado válido (SURV_FLAG: KM t6 ≥ 10 p.p. abaixo da global); (3) rotular INCONCLUSIVA.
- **Evidência:** SURV_FLAG avaliável: nenhum segmento cruza (maior gap 6,9 p.p., organic 0,3734 vs global 0,4428); spread de taxas 60,2–75,3% (razão máx. 1,07×).
- **Decisão:** opção 2 — hipótese original preservada (sem reescrita); nota explícita no t10/evidence: limiar inalcançável por desenho; conclusão "sem heterogeneidade material" baseada no SURV_FLAG (critério alternativo pré-registrado) + spread reportado. Erro de desenho registrado como tal (erro real nº 9 do report §7), sem justificativa retroativa.
- **Trade-off:** o rótulo REFUTADA permanece mecânico; a leitura correta fica explícita ("sem heterogeneidade MATERIAL segundo os critérios pré-registrados aplicáveis; variação não-negligenciável reportada").

## D9 — KM: horizontes fixos pela função degrau (carry-forward), vazio só quando não observável

- **Problema (L5/INFO-1/finding #6):** `surv_at.get(6|12|18, "")` exigia evento/censura exatamente em t = horizonte; células com follow-up suficiente ficavam vazias (ex.: 2023Q2 t12 vazio com 20 meses observados; 2023-02 t6 vazio com 22 meses).
- **Decisão:** helper `surv_at_horizon` — valor no maior t ≤ horizonte (função degrau), vazio SOMENTE quando follow-up < horizonte (não observável, censura no corte). Aplicado a coortes (t02/t02a) e segmentos (t07). Gate G5 inalterado.
- **Trade-off:** tabelas de auditoria passam a mostrar valores estimáveis; a regra de vazio fica explícita e conservadora (Q4-2024/Q3-2024 continuam vazios em t6).

## D10 — Suporte: seed do `prev_ev` (contas com 1º evento em 2023-01..03 fora do controle)

- **Problema (finding #3):** o controle exige "elegíveis sem primeiro evento anterior" (contrato §5); sem seed, 6 contas com primeiro evento em 2023-01..03 entravam no controle de todos os meses (n_control 3.288 vs 3.162 contratuais).
- **Decisão:** `prev_ev` seedado com os primeiros eventos de 2023-01..03. Recalculado: controle 3.162; tickets/conta 0,349; escalação 5,1%; FRT 93,5 min; resolução 35,0 h — imaterial, H5 permanece REFUTADA.
- **Trade-off:** desenho fica fiel ao contrato §5; números pooled/estratificados mudam levemente (reportados na forma corrigida).

## D11 — Correções factuais baratas (sem impacto em números/vereditos)

- Gráfico B: ylim (0; 1,02) — nenhuma curva cortada (2024Q2 = 0,3077); legenda fora da área de plotagem.
- Gráfico C: rodapé "tabela t04" → `t03c_cac_equivalent.csv`.
- Wording "39,6% em ≤30d" → "43,6% ≤ 30d incluindo same-day (513.586); bucket 1-30d = 39,6% (467.262)".
- Frase "nível elevado de 2024-03 em diante" → período elevado (9 meses; 2024-03, 05..12) com vale em 2024-04 (15 < 1,5× mediana 11,5 = 17,25) — sem enfraquecer o achado.
- Mediana de uso alinhado clarificada: mediana-das-medianas-mensais (primário) vs pooled (1,0 → 2,0 = +100%, nota).
- Process report: MD5 stale corrigido (6324b0d4 = geração intermediária pré-D4; 996debf9 = commitado em 9e02e18; e25b2375 = pós-fix) e timeline alinhada ao CommitDate (20:47:32Z), com nota de correção — passado git não reescrito.