# Review Summary — Iteração 02 (ledger versionado do review gate 3x)

- **Iteração revisada:** 02 (Reconciliação das definições/grãos de churn e contrato analítico)
- **Commit revisado:** `9305e2edcdea7506feab0af75e0f29401becf6b7` (`feat: reconcile churn definitions and analytical grain`, base `b9823da`)
- **Data do gate:** 2026-08-28
- **Revisores:** 3 agentes `deepseek-max` independentes, modo read-only, em paralelo (nada no repo foi modificado pelos revisores; testes em sandboxes fora do repo)
- **Corretor sequencial:** 1 agente `deepseek-max` (este), sob orquestração do opencode — commit `fix: strengthen revenue churn contract`
- **Uso:** ledger do review gate; referenciado pelo execution-plan (regra 4), pelo orchestrator-checklist (B3/B10) e pelos reports da Iteração 02 (§11) e da correção

---

## 1. Veredictos e paths externos

| Revisor | Veredicto | Report externo (fora do repo, read-only) |
|---|---|---|
| R1 | `PASS` | `/tmp/opencode/ai-master-review-reports/iteration-02/review-9d3b7e05.md` |
| R2 | `PASS` | `/tmp/opencode/ai-master-review-reports/iteration-02/review-6c2f9a41.md` |
| R3 | `PASS_WITH_FIXES` | `/tmp/opencode/ai-master-review-reports/iteration-02/review-8b41e9c2.md` |

Nenhum veredicto BLOCKER. R1/R2 não apontaram findings obrigatórios (LOWs/INFO apenas); R3 apontou 2 MEDIUM (M1/M2) — tratados como materiais pelo orquestrador e corrigidos por este agente sequencial, junto com a política de `closed_at` (item adiado da It01, LOW L1 do R3) e LOWs baratos convergentes. Os reports externos **não** são copiados para o repo (evidência fora da pasta permitida); este summary é o registro oficial versionado.

## 2. Findings e matriz ação → arquivo:linha (pós-correção)

| Finding | Origem | Severidade | Ação aplicada | Arquivo:linha (pós-correção) |
|---|---|---|---|---|
| M1 — lente de revenue churn por winner quase degenerada (18.507 capturados vs 398.462 ocultos; lente B 1.179.139); contrato §5 não sinalizava magnitude | R3 | MEDIUM | Duas lentes nomeadas no contrato/report: **R1 gross subscription ending MRR** (exposição bruta; 1.179.139/486) e **R2 net account-state MRR loss** (churn-to-inactive 18.507/2 transições + active contraction 150.817/36; total 169.324), com cobertura/trade-off e **proibição** do uso isolado do winner como churn contratual; gap quantificado em runtime (274 assinaturas/422.691 ocultas; episódios conta-mês 254; 226 inalteradas/0 reduzidas; exemplo material A-5a215a 2024-12 — 34.626 encerrados, winner inalterado em 17.313); decisão D9 registrada | `solution/src/02_reconcile_churn.py` `revenue_lenses` `:424-563`; render report §7 `:1007-1061`; render contract §5/§6 `:1198-1263,1283-1296`; `solution/evidence/02_consistency_report.md` §7; `solution/docs/analytical-contract.md` §5/§6/§12; `process-log/decisions/iteration-02-analytical-contract-decisions.md` D9 |
| M2 — números de qualidade hardcoded no render (13.198/1.077/53/90/143/825/41,2%/148; também 76,6%/290/5.568 no report) | R3 | MEDIUM | `quality_metrics()` deriva tudo em runtime (partição de uso, pré-signup, eventos fora da vida de assinaturas, CSAT/reason/feedback, subs por conta, violações end↔flag) e injeta nos renders; varredura extra parametrizou 110/312/352 e 35/277/125 (contrato §4/§12) e a descrição do G7; restaram apenas constantes de regra nomeadas (janelas, quantis) | `02_reconcile_churn.py` `quality_metrics` `:565-640`; renders `:1007-1061,1330-1460`; report §8; contract §9/§10 |
| `closed_at` sem política (item adiado da It01; L1 do R3) | R3 (L1), It01 | LOW→material | Política explícita no contrato §7/§10 (decisão D10): tickets existem por `submitted_at`; resolução/CSAT só com tickets fechados e informação ≤ data índice; nulos excluídos com denominador explícito (1.175); nunca imputar fechamento futuro; `closed_at` promovida a coluna mínima (REQUIRED), parseada (D01) e com gate G15 | `02_reconcile_churn.py:66-72` (REQUIRED), `:836-841` (G15), `:1560-1562` (D01); contract §7/§10; decisions D10 |
| G10 verifica menos que o rótulo (anti-leakage parcial) | R1 (L1) | LOW | Aceito como trade-off documentado (painel gerado na mesma execução; reconstrução célula-a-célula independente 0 divergências; risco de regressão futura monitorado — sem refatoração de gate nesta correção; redação do contrato §8 mantida fiel ao que é verificado + colunas de desfecho rotuladas) | — |
| Quantis de lag arredondados sem nota | R1 (L2) | LOW | Nota de arredondamento `:.0f` + valores subjacentes adicionada ao report §4 | `02_reconcile_churn.py:1101-1111` |
| Tie-break do matching implícito | R1 (L3), R2 | LOW | Regra documentada (primeira ocorrência na ordem estável do CSV, `idxmin`) no report §4 | `02_reconcile_churn.py:1083-1087` |
| Coluna "Acumulado" redundante/enganosa | R1 (L5), R2 (L5), R3 (L2) | LOW | Coluna removida da tabela de alinhamento | `02_reconcile_churn.py:1092-1097` |
| Código morto `cur = int(...)` no G5 | R1 (L5), R2 (L1), R3 (L5) | LOW | Removido | `02_reconcile_churn.py:681-685` |
| Redação D4/§9 diário vs mensal | R1 (L4), R3 (L4) | LOW | Wording do D4 precisado (fim em 12-15 → inativa em dezembro); nota de grão diário vs mensal no report §8 e contrato §9 | `02_reconcile_churn.py:1058-1071`; decisions D4 |
| Erro real nº5 do report (G6 por MRR==0) não reproduzível exatamente | R2 (L2) | INFO | Aceito: estado final verificado corretamente por recálculo independente; claim de processo plausível | — |
| G5/G6 autorreferentes | R2 (L3), R1 | INFO | Aceito como trade-off documentado (âncora na fonte via G7/G9/G10/G14 + reconstrução independente) | — |
| 549/237 trocas valor-neutras de winner (mesmo MRR) | R2 (L4), R3 (L6) | INFO | Aceito: sem impacto econômico; recomendação de preferir `winner_mrr` a atributos categóricos do winner em features | — |
| `csat_mean_month` "" vs NaN | R2 (L6), R3 (L3) | INFO | Aceito (representacional; documentado no README processado); consumidores tratam NaN como sem tickets | — |
| `requirements.txt` sem pinning | R2 (L7) | INFO | Aceito — objeto da Iteração 06 (registrado desde It00/It01) | — |

## 3. Decisão sobre o winner (item 9 do mandato do gate)

**Preservado como estado/risco da conta** (status + MRR dominante; determinístico e reproduzível byte-a-byte; 0 divergências em 5.807 linhas na reconstrução independente), com as seguintes restrições novas:

1. **Proibido** usar a saída do winner isoladamente como total de churn contratual/receita perdida (contrato §5, decisão D9);
2. Receita tem duas lentes nomeadas: **R1 gross subscription ending MRR** (exposição bruta; janela = 1.179.139 / 486 assinaturas; não é perda automática — pode ser troca/replacement/sobreposição) e **R2 net account-state MRR loss** (churn-to-inactive 18.507/2 transições + active contraction 150.817/36 transições; total 169.324; cobertura/trade-off explícitos);
3. **Gap quantificado em runtime:** saídas ocultas não-dominantes = 274 assinaturas / 422.691 (episódios conta-mês 254; 226 com winner_mrr inalterado, 0 reduzido, 28 aumentado); razão vs churn-to-inactive = 22,8×; exemplo material A-5a215a 2024-12 (2×17.313 encerrados, winner S-75cba6 inalterado em 17.313).

## 4. Recálculos independentes (corretor; script próprio fora do repo — `verify_final.py`)

46/46 checks OK, incluindo:

| Número | Valor | Recálculo independente |
|---|---|---|
| Gross ending MRR (lente R1, janela) | 1.179.139 / 486 subs / 312 contas / 10.159.608 ativas | ✓ (e por conta×mês: Σ painel `mrr_ended_in_month` = 1.179.139; 427 conta×mês; 486 em `n_ended_in_month`) |
| Churn-to-inactive (lente R2a) | 18.507 em 2 transições (2023-10→11: 12.736; 2024-08→09: 5.771) | ✓ |
| Active contraction (lente R2b) | 150.817 em 36 transições | ✓ |
| Net account-state MRR loss | 169.324 | ✓ |
| Expansão ativa (contexto) | +2.287.279 em 590 transições | ✓ |
| Saídas ocultas não-dominantes | 274 assinaturas / 422.691 (242 inalteradas/0 reduzidas/32 aumentadas); episódios conta-mês 254 (226/0/28); razão 22,8× | ✓ (algoritmo final documentado: 4 condições) |
| Exemplo material | A-5a215a 2024-12: 2 assinaturas de 17.313 (34.626) encerram; winner S-75cba6 → S-75cba6 (17.313 → 17.313) | ✓ |
| Qualidade | 19.142/25.000 (76,6%); 290; 5.568 (22,3%); 13.198; 1.077; 53; 90; 825 (41,2%); 95; 148; 0 nulos `closed_at`; domínio {3,4,5} | ✓ |
| Painel | 5.807 linhas; 0 duplicatas; célula-a-célula vs CSV commitado (22 colunas): 0 divergências de conteúdo | ✓ |
| MV-A/B/C com novas colunas | A-00bed1 (2024-01: active/S-a7360b/1159, mrr_ended=0); A-0baac2 (2024-09: inactive, mrr_ended=5.771; 2024-12: active/S-21ebb6/6.169, mrr_ended=2.786); A-956988 (2024-12: 12 ativas/S-c069ab/10.945/29.407) | ✓ 3/3 |
| Invariantes | G1–G15: 31 PASS / 1 WARN (G12) / 0 FAIL | ✓ (G14: soma/contagem/conta×mês vs fonte; G15: closed_at 0 nulos) |

**Diferença vs números do R3 (255/398.462):** o algoritmo final do corretor (documentado no report §7 e no contrato §5) produz **274 assinaturas / 422.691** (visão sub) e **254 episódios conta-mês / 422.691** (226 inalterados — **coincidem exatamente** com os 226 do R3; 0 reduzidos em ambas). Causa da diferença: granularidade de agregação e/ou tratamento de episódios limítrofes na rotina do reviewer (script não commitado, não reproduzível byte-a-byte a partir do report); a conclusão material é invariante em todas as variantes da família de definições (gap ≈ 21–23×; exemplo A-5a215a idêntico). O exemplo do R3 ("assinatura de 34.626") corresponde, na base real, a **duas** assinaturas de 17.313 encerrando em 2024-12 (34.626 no total) — estrutura do exemplo preservada.

## 5. LOWs aceitos sem correção (justificativa)

- **G10 parcial (R1-L1):** gate verifica month_end ≤ corte + winner na janela + presença de colunas, sem re-derivar buckets de uso/tickets do raw; painel é gerado na mesma execução e a reconstrução célula-a-célula independente (46/46) confirma 0 vazamentos hoje. Risco de regressão futura monitorado (handoff It03/It06); refatorar o gate agora seria mudança ampla sem benefício material.
- **Erro real nº5 do report It02 não reproduzível exatamente (R2-L2):** claim de processo plausível; estado final do G6 verificado correto (0 meses quebrados).
- **G5/G6 autorreferentes (R2-L3):** âncora na fonte via G7/G9/G10/G14 e reconstrução independente; gates de reconciliação status/MRR vs fonte recomendados à It06.
- **Trocas valor-neutras de winner (R2-L4/R3-L6, 549/237):** sem impacto econômico (winner_mrr idêntico); recomendação registrada: preferir `winner_mrr` a atributos categóricos do winner em features (It04).
- **`csat_mean_month` "" ↔ NaN (R2-L6/R3-L3):** representacional; documentado no README processado; consumidores tratam NaN como "sem tickets".
- **`requirements.txt` sem pinning (R2-L7):** objeto da Iteração 06 (registrado desde It00/It01).

## 6. Testes pós-fix (baseline no repo + sandbox `/tmp/opencode/it02-fail-sandbox/`, fora do repo)

| Cenário | Resultado |
|---|---|
| Baseline execução 1 (dados íntegros) | exit 0; 31 PASS / 1 WARN / 0 FAIL |
| Baseline execução 2 (idempotência) | exit 0; 4 outputs byte-a-byte idênticos (report `33b50369…`; contrato `702fa1b5…`; CSV `b718c4f8…`; README `d30e2790…`) |
| Comparação com outputs commitados (pós-correção) | 4/4 byte-a-byte idênticos |
| Verificação independente (`verify_final.py`, implementação própria) | 46/46 checks OK (painel reconstruído do zero; célula-a-célula 0 divergências; lentes R1/R2; ocultas; qualidade; MVs; invariantes) |
| FAIL 1 — coluna `churn_date` renomeada | exit 1; 9 PASS / 5 FAIL (S01 + R01–R04); report regravado com "Falha estrutural"; sem traceback; outputs de dados NÃO regenerados (MD5 preservados); idempotente |
| FAIL 2 — arquivo `churn_events.csv` removido | exit 1; 8 PASS / 5 FAIL; sem traceback; sem stale |
| FAIL 3 — coluna `signup_date` renomeada | exit 1; 9 PASS / 5 FAIL; sem traceback; sem stale; idempotente |
| Falha combinada acidental (2 colunas quebradas) | exit 1; sem traceback; FAILs estruturados para ambos os arquivos |
| Grep de traceback nos logs de FAIL | 0 ocorrências |
| Syntax/import | `py_compile` OK; import OK |
| Hardcode scan | nenhum número de dados de qualidade no render (restam apenas constantes de regra nomeadas: janelas, quantis, tolerâncias) |
| Hygiene | `git diff --check` limpo; escopo 100% `submissions/jose-nascimento/`; sem segredos/paths pessoais (grep `/tmp|/home|ubuntu` = 0 fora do prompt arquivado) |

## 7. Riscos residuais (monitorar; não bloqueiam)

- **Definição de saídas ocultas (família de variantes):** números dependem da granularidade (sub vs conta-mês); contrato fixa o algoritmo (4 condições) e reporta ambas as visões.
- **G10 parcial** — regressão de bucketing futuro em uso/tickets não seria capturada pelo gate (mitigado por construção e reconstrução independente).
- **Uso indevido de desfechos rotulados (`mrr_ended_in_month`/`n_ended_in_month`/`churn_event_in_month`/`status`)** como features do próprio mês em It03/It04 — mitigado por contrato §8 e nomeação das colunas.
- **Mau uso do `churn_flag_snapshot_2024_12_31`** como série — contrato §8 + G10.
- **Determinismo vs versão de pandas** (3.0.5 verificado; pinning na It06).
- **Trocas valor-neutras de winner** (atributos categóricos mudam sem mudança econômica) — preferir `winner_mrr` em features.
- **`closed_at` futuro com nulos em base real** — política documentada; gate G15 vira WARN se nulos aparecerem.

## 8. Gate final da Iteração 02

- **Gate:** `CONCLUDED` — 3 veredictos recebidos (2 `PASS`, 1 `PASS_WITH_FIXES`); findings materiais M1 (lente de receita degenerada) e M2 (números hardcoded) corrigidos; política de `closed_at` explicitada (D10); LOWs baratos convergentes corrigidos (quantis, tie-break, "Acumulado", código morto, D4/§9) e demais aceitos com justificativa (§5); recálculo independente 46/46 sem diferença material (diferença definicional vs R3 documentada com causa); baseline reexecutado (31 PASS / 1 WARN / 0 FAIL) idempotente; 3 cenários de FAIL estrutural sem stale/traceback; correção commitada e pushada (commit `fix: strengthen revenue churn contract`).
- **Próximo passo:** Iteração 03 (Causa raiz, coortes e onboarding economics) pode ser disparada pelo orquestrador conforme handoff do report de correção (§10) e deste summary.