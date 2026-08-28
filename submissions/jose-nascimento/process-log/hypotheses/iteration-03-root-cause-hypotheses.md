# Hipóteses da Iteração 03 — Causa raiz, coortes e economia do onboarding

**Status deste arquivo:** HIPÓTESES PRÉ-REGISTRADAS — escritas ANTES de qualquer query exploratória de resultado de negócio desta iteração. Nenhuma linha abaixo é conclusão; cada hipótese tem teste falsificável e threshold decidido previamente (só com o brief + contrato analítico congelado da Iteração 02 + relatórios 01/02, sem consultar os dados de negócio). Vereditos e números reais serão registrados no report da iteração (`process-log/reports/iteration-03-root-cause-report.md`) e no `solution/evidence/03_root_cause_report.md` após a execução.

- **Data de registro:** 2026-08-28 (antes da implementação de `solution/src/03_root_cause.py`)
- **Commit de versionamento:** registrado no git (ver report da iteração)
- **Fatos de entrada permitidos (já derivados nas Iterações 01–02, não re-hipóteses):** 600 eventos / 352 contas com evento / 175 multi-evento / 61 reativações em 55 contas; 486 assinaturas encerradas (9,7%), 312 contas, gross ending MRR R1 = 1.179.139; churn-to-inactive R2 = 18.507 (2 transições) + active contraction 150.817 (36 transições) = 169.324 líquido; 110 contas no flag do corte; 76,6% do uso fora da janela da assinatura; 13.198 linhas de uso e 1.077 tickets anteriores ao signup; CSAT {3,4,5} com 41,2% nulos; 95 reason 'unknown'; 148 feedback nulos; 0 contas inativas no corte pela lente de assinatura.
- **Brief (claims a testar):** "o churn subiu nos últimos meses"; "CS diz que a satisfação está ok"; "produto diz que o uso da plataforma cresceu"; "algo não bate".

---

## 0. Convenções de veredito (aplicadas a TODAS as hipóteses)

- **Sustentada:** o teste cruza o threshold pré-registrado e o resultado é robusto às sensibilidades declaradas (variantes de definição; denominadores).
- **Parcialmente sustentada:** cruza o threshold apenas em uma variante, ou em magnitude menor que a metade do limiar.
- **Refutada:** o teste não cruza o threshold em nenhuma variante razoável.
- **Inconclusiva:** o dado não permite discriminar (ex.: janela de observação curta demais, N pequeno, decoplamento estrutural) — registrado com o motivo numérico.
- Toda hipótese sustenta **correlação observada**, nunca causalidade; o status causal é decidido na tabela do report (seção H do artefato) com confundidores e dado adicional necessário.
- Lente obrigatória por pergunta (contrato §4): eventos (C) para diagnóstico; assinaturas (B) para receita (R1/R2); painel account-month para estado/risco. Nenhuma comparação entre lentes na mesma fórmula.
- Anti-leakage (contrato §8): features de risco com data ≤ fim do mês m−1 quando o desfecho é do mês m; nenhum uso de `churn_flag_snapshot_2024_12_31` como feature; CSAT/resolução apenas com tickets fechados (contrato §10).

---

## H1 — Composição/tenure: o churn é um fenômeno de contas jovens (início do ciclo de vida)

- **Pergunta:** os eventos de churn se concentram em contas com pouco tempo desde o signup?
- **Métrica/fonte/grão:** meses do signup → primeiro evento por conta (lente C — `churn_events` + `accounts`); grão: conta (primeiro evento). Censura no corte 2024-12-31 para contas sem evento (tratadas na H2/coortes).
- **Teste falsificável:** distribuição de `months_since_signup` no primeiro evento entre as contas com evento; mediana e share em janelas de tenure (0–3, 4–6, 7–12, 13–24 meses).
- **Threshold (decidido antes de ver os dados):** sustentada se **≥ 50%** dos primeiros eventos ocorrerem com **≤ 6 meses** de tenure E mediana ≤ 6 meses; parcial se 35–49% em ≤ 6 meses; refutada se < 35%.
- **Confundidores:** (a) mais signups em 2024 ⇒ mais contas jovens existentes (composição, não taxa — ver H2); (b) censura: coortes recentes têm menos meses observáveis; (c) múltiplos eventos por conta (usa-se primeiro evento; sensibilidade com todos os eventos).
- **Se refutada:** eventos espalhados por tenure ⇒ foco desloca para sinais transversais (H4/H5/H6) e para coortes específicas (H2).

## H2 — Coortes: o "spike" de churn é composição de coorte (mais signups), não aumento real de taxa

- **Pergunta:** o aumento mensal de eventos nos "últimos meses" reflete mais contas elegíveis no denominador ou uma taxa por conta realmente maior?
- **Métrica/fonte/grão:** taxa mensal de **primeiro evento** por conta elegível (contrato §5: contas com signup ≤ m, sem primeiro evento anterior, não censuradas) e taxa de eventos totais por conta ativa (painel); grão: mês (2023-01..2024-12).
- **Teste falsificável:** série mensal de (a) contas novas no mês, (b) taxa de primeiro evento por conta elegível, (c) taxa de eventos totais por conta ativa; comparar meses de pico vs mediana da janela.
- **Threshold (decidido antes de ver os dados):**
  - Se a taxa por conta elegível no(s) mês(es) de pico ficar **dentro de ±25%** da mediana da janela 2023–2024 ⇒ composição domina (**H2a sustentada**);
  - Se a taxa de pico for **≥ 1,5×** a mediana dos 6 meses anteriores ⇒ aumento real de taxa (**H2b sustentada**);
  - Ambos ⇒ misto (composição + taxa).
- **Confundidores:** sazonalidade sintética; múltiplos eventos (primário: primeiro evento; sensibilidade: todos); censura no corte (Q4-2024 tem janela incompleta — nunca comparar Q4 com janela completa sem nota).
- **Se refutada (nem composição nem taxa):** o pico é explicado por mecanismo de segmento/tenure específico (H1/H6/H9) ou é ruído de base.

## H3 — Uso: "o uso cresceu" é volume (mais contas/linhas), não intensidade por conta

- **Pergunta:** o crescimento de uso reportado pelo produto é verdadeiro por conta ativa ou artefato de volume?
- **Métrica/fonte/grão:** linhas de uso por mês — total bruto e alinhado (contrato §9: `usage_rows_month` vs `usage_rows_in_window_month`) vs intensidade por conta ativa (linhas/account-mês); primário exclui uso pré-signup (linhas com `usage_date < signup_date`); sensibilidade com tudo.
- **Teste falsificável:** comparação 2023 vs 2024 (e mês a mês) do total vs da mediana por conta ativa.
- **Threshold (decidido antes de ver os dados):** sustentada se o total crescer **≥ 20%** entre semestres/anos E a intensidade mediana por conta ativa mudar **< 10%** (ou cair); refutada se a intensidade por conta crescer junto (≥ 10%).
- **Confundidores:** 76,6% do uso fora da janela da assinatura (alinhado vs bruto); 13.198 linhas pré-signup; mais contas em 2024 (denominador).
- **Se refutada:** o claim do produto é verdadeiro também per-account ⇒ uso crescente não explica churn (direção contrária ao esperado) — reforça a tese de decoplamento (H4).

## H4 — Uso não precede churn: atividade pré-evento não diferencia contas que churnam

- **Pergunta:** contas com primeiro evento mostram queda/ausência de uso ALINHADO antes do evento (padrão típico de "uso caiu antes de sair")?
- **Métrica/fonte/grão:** uso alinhado por conta em janelas pré-evento [t−90, t−30] e [t−30, t) vs controle (contas sem evento no mesmo período calendário, comparáveis por tenure/tier quando viável); features apenas ≤ m−1 (anti-leakage contrato §8); nunca atividade pós-churn como preditor.
- **Teste falsificável:** diferença de mediana de uso mensal alinhado e share de contas com zero uso alinhado pré-evento.
- **Threshold (decidido antes de ver os dados):** sustentada se a mediana pré-evento do grupo-churn for **< 50%** da mediana do controle OU o share de zero-uso alinhado for **≥ 25 p.p.** maior; caso contrário refutada (uso decoplado do churn na base).
- **Confundidores:** uso pré-signup massivo (polui o alinhado); janelas curtas; ruído sintético; censura.
- **Se refutada (decoplamento):** "uso cresceu" e "churn subiu" podem coexistir sem contradição nos dados — a incoerência do CEO é resolvida por decoplamento estrutural da base (registrar como achado, não como falha de produto).

## H5 — Suporte: sinais pré-evento (tickets, escalação, resposta, resolução, CSAT) diferenciam churn

- **Pergunta:** contas com primeiro evento têm sinais de suporte materialmente piores ANTES do evento do que controles sem evento?
- **Métrica/fonte/grão:** por conta, janela de 90 dias antes do primeiro evento (e controle no mesmo calendário): nº de tickets, taxa de escalação, mediana `first_response_time_minutes`, mediana `resolution_time_hours`, CSAT médio apenas de tickets fechados com nota (denominador explícito — contrato §10); tickets pré-signup tratados à parte.
- **Teste falsificável:** comparação churn vs controle com N ≥ 30 contas por lado.
- **Threshold (decidido antes de ver os dados):** sustentada se pelo menos um dos limiares: diferença **≥ 1 ticket/conta**; taxa de escalação **≥ 1,5×**; CSAT médio ≤ 3,5 vs > 4,0 no controle; mediana de first-response/resolution **≥ 1,5×** o controle.
- **Confundidores:** 1.077 tickets pré-signup (poluem janelas); volume de contas jovens; censura; nulos de CSAT (41,2%).
- **Se refutada:** suporte não explica churn nos dados ⇒ o "CS diz que satisfação está ok" não contradiz o churn (coexistência de fato), reforçando decoplamento.

## H6 — Segmentos: churn concentrado em industry/channel/plan_tier/trial

- **Pergunta:** algum segmento tem taxa de churn materialmente pior (com denominador) ou concentra a exposição bruta R1?
- **Métrica/fonte/grão:** por segmento (industry, referral_source, plan_tier, is_trial da conta): N contas, N com primeiro evento, taxa (primeiro evento / conta elegível), sobrevivência KM descritiva, Σ gross ending MRR R1; mínimo de amostra e flag de instabilidade.
- **Teste falsificável:** taxa do segmento vs taxa global; share de R1.
- **Threshold (decidido antes de ver os dados):** segmento **flag** se N ≥ 25 contas E taxa ≥ **1,5×** a global E share de R1 > **10%** do total (ou sobrevivência no mês 6 ≥ 10 p.p. abaixo da global). Segmentos com N < 25: reportados com flag `N_BAIXO`, sem ranking.
- **Confundidores:** mix de tenure/coorte (segmento com signups recentes parece pior — comparar taxa por tenure); winner do mês (plano); trials (MRR 0).
- **Se refutada:** nenhum segmento cruza o limiar ⇒ churn transversal; segmentação não é o mecanismo primário.

## H7 — CSAT/reasons/feedback: evidência sugestiva frágil (missingness + inconsistência estrutural)

- **Pergunta:** CSAT, reason_code e feedback conseguem sustentar uma narrativa causal de churn?
- **Métrica/fonte/grão:** missingness (CSAT 41,2% na base; 95 'unknown'; 148 feedback nulos — fatos da It01/02); consistência: reason_code com refund/downgrade/upgrade flags do próprio evento; associação reason↔lente de assinatura; CSAT de contas com evento vs sem (janela pré-evento, fechados apenas).
- **Teste falsificável:** quantificação + associações bivariadas descritivas.
- **Threshold (decidido antes de ver os dados):** se missingness > 25% OU 'unknown' > 10% OU **nenhuma** associação observável de reason_code com (refund, upgrade, downgrade) ⇒ H7 sustentada (evidência sugestiva frágil; proibido transformar reason_code em causa — contrato §10). Se associações claras e consistentes ⇒ H7 refutada (sugestiva mais forte, ainda nunca causal).
- **Confundidores:** base sintética; nulos não-aleatórios; decoplamento das lentes.
- **Se refutada:** reasons passam a sugestão de mecanismo (ex.: pricing/support), mas permanecem correlação; causalidade segue não identificável.

## H8 — Onboarding economics: exposição contratual bruta precoce é material

- **Pergunta:** quanto da exposição bruta R1 acontece cedo no ciclo de vida (30/60/90 dias) e qual o valor em cenários nomeados CAC-equivalent?
- **Métrica/fonte/grão:** por assinatura encerrada: dias start→end; Σ MRR com duração ≤ 30/60/90 dias; share do R1 total (1.179.139 na janela); por conta: primeiro evento ≤ 30/60/90 dias do signup. **CAC-equivalent exposure** = cenários explicitamente nomeados (múltiplos de MRR: 1×, 3×, 6×, 12×) sobre a exposição precoce — NUNCA chamados de "CAC queimado" ou "receita perdida" (o dataset não contém custo; R1 é exposição, não perda — contrato §5).
- **Teste falsificável:** distribuição de duração das assinaturas encerradas; share precoce.
- **Threshold (decidido antes de ver os dados):** sustentada se **≥ 25%** do R1 total vier de assinaturas com ≤ 90 dias de vida OU **≥ 30%** dos primeiros eventos ocorrerem ≤ 90 dias do signup; sensibilidade de janelas 30/60/90 e de definição (assinatura vs conta).
- **Confundidores:** trials (MRR 0); sobreposição (saída pode ser troca — R1 não é perda); assinaturas curtas mas substituídas.
- **Se refutada:** exposição precoce pequena ⇒ churn tardio domina; economia do onboarding perde prioridade para retenção de longo prazo.

## H9 — Decomposição do spike: o pico mensal é explicado por tenure/coorte específicos

- **Pergunta:** nos meses de pico de eventos, qual bucket de tenure e qual coorte de signup contribuem mais — e com taxa acima da própria linha de base?
- **Métrica/fonte/grão:** série mensal de primeiro-evento por bucket de tenure (0–3, 4–6, 7–12, 13–24) e por coorte de signup (mês e trimestre); taxa por conta elegível no bucket.
- **Teste falsificável:** pico do mês M decomposto: eventos do pico vs média dos 6 meses anteriores por bucket/coorte; contribuição absoluta × taxa relativa à linha de base do próprio bucket.
- **Threshold (decidido antes de ver os dados):** o mecanismo do pico é o bucket com maior contribuição absoluta AO PICO E taxa acima da própria linha de base (≥ 1,5×). Se o bucket dominante for tenure 0–3/4–6, o pico é consistente com H1 (churn jovem); se for uma coorte específica, com H2.
- **Confundidores:** censura no corte; múltiplos eventos; mudança de mix de coortes.
- **Se refutada:** pico transversal a todos os buckets/coortes ⇒ mecanismo externo não capturado pelas variáveis da base (registrar como não identificável).

## H10 — Rotulagem causal transversal (compromisso de análise, não hipótese de negócio)

- Toda afirmação do report recebe status: `descritivo` | `hipótese causal plausível` | `não identificável`, com confundidores e dado adicional necessário (tabela H no artefato). Nenhuma associação observada será apresentada como causa sem esse rótulo. Causa raiz operacional SOMENTE se sustentada por múltiplas evidências independentes (ex.: H1 + H2 + H8 + H9 convergentes); caso contrário, reportar "não identificável com esta base" com os números.

---

## Nota de método (pré-registro)

- Thresholds acima foram fixados ANTES de rodar qualquer query de negócio desta iteração, com base apenas no brief e nos fatos de entrada das Iterações 01–02. Se a execução revelar que um threshold é inaplicável (ex.: N insuficiente), a hipótese é marcada `inconclusiva` com o motivo numérico — thresholds não são renegociados após ver os resultados.
- Sensibilidades obrigatórias: evento vs assinatura (grão); janelas 30/60/90 dias; registros temporais válidos vs todos (pré-signup incluído/excluído); denominadores (elegível vs ativa); censoring (taxa observada vs estimativa censurada); múltiplos eventos nunca viram múltiplos logos (contrato §7).
- Análises de coorte NUNCA comparam Q4-2024 com janela completa sem nota de censura (coortes de Q4 têm ≤ 3 meses observáveis).