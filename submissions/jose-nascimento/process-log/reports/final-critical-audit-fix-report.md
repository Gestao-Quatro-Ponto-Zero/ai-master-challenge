# Report de Remediação da Auditoria Crítica Final

- **Data:** 2026-08-29
- **Base auditada:** commit `86d7800` (`chore: close pre-submission QA gate`)
- **Prompt:** [`final-critical-audit-fix-prompt.md`](../prompts/final-critical-audit-fix-prompt.md)
- **Summary:** [`final-critical-audit-summary.md`](../reviews/final-critical-audit-summary.md)
- **Escopo:** somente a pasta da submissão; sem PR nesta etapa.

## 1. Correções aplicadas

### HIGH-001 — linkage evento–assinatura

- `07_generate_executive_report.py` agora recalcula, a partir de
  `churn_events` e `subscriptions`, os eventos vinculados e não vinculados em
  ±30 dias.
- O valor positivo continua `21,0%` e a formulação negativa usa `79,0%`.
- O gate G9 exige os dois claims, confere os denominadores (`126 + 474 = 600`)
  e rejeita a inversão `21,0% dos eventos não têm`.
- `06_verify_pipeline.py` repete o cálculo de linkage nos raw inputs e valida a
  semântica textual do relatório, sem confiar apenas em uma âncora copiada.

### HIGH-002 — KM em horizonte fixo

- `04_lifecycle_watchlist.py` usa o último ponto KM com `t <= horizonte`,
  preservando a função degrau entre tempos observados.
- Um horizonte além do maior follow-up observado retorna valor não observável,
  em vez de usar silenciosamente o último evento posterior.
- O t12 registra `km_max_observed_days` para tornar o domínio observável.
- A narrativa de It04, o segmento S3 e os consumidores It05/It07 são derivados
  do t12/objeto KM regenerado.
- O gate G13 valida a função, os anchors `0,681461`/`0,515156` e a mediana
  `187`; F8 recalcula o KM de forma independente a partir dos raw inputs.

## 2. Artefatos regenerados

Após a execução integral, os artefatos materiais ficaram com:

| Artefato | Claim esperado |
|---|---|
| `solution/out/tables/t12_reactivation_recurrence.csv` | `km_surv_90d=0,681461...`; `km_surv_180d=0,515156...` |
| `solution/evidence/04_lifecycle_watchlist_report.md` | `S90=0,681`, `S180=0,515`, ≈31,9% e ≈48,5% |
| `solution/out/tables/t15_priority_segments.csv` | S3 com KM e taxa derivados atuais |
| `solution/out/tables/t18_actions_prioritized.csv` | ACT-04 com âncora KM 90d atual |
| `solution/out/tables/t20_measurement_plan.csv` | ACT-04 com âncoras 90d/180d atuais |
| `solution/report-executivo.md` | `79,0%` sem vínculo e KM 90d atual |

## 3. Validação

- Compilação dos sete scripts e `bash -n run.sh`: PASS.
- Estágios isolados 04, 05 e 07 após a correção: PASS.
- `./run.sh` a partir de CWD externo: PASS; verificação final `88 PASS / 0 FAIL`.
- `make all`: PASS; uma segunda execução produziu bytes idênticos em todos os
  arquivos rastreados.
- `make verify`: PASS; `88 PASS / 0 FAIL`, incluindo linkage e KM
  independentes, G13, D1 sem cache e G3 sem links quebrados.
- Testes negativos em cópias descartáveis: arquivo raw ausente, booleano
  inválido, tabela derivada ausente e link quebrado retornaram exit não-zero,
  diagnóstico estruturado e nenhum traceback.
- Clone fresco da branch publicada em `af970a3`: PASS; `./run.sh`, `make all` e
  `make verify` passaram, os arquivos permaneceram byte-idênticos, o worktree
  ficou limpo e nenhum `__pycache__` foi criado.

## 4. Handoff

- Não alterar o histórico de It04–It09 nem transformar esta remediação em E9.
- Atualizar os snapshots e referências documentais somente após rederivar as
  contagens com glob/git.
- Antes do commit, foram revisados `git diff --check`, escopo, arquivos gerados
  e ausência de cache; após o push, o clone fresco foi validado com `make verify`.
- O commit final, push e PR oficial permanecem como pendências formais da
  It10.
