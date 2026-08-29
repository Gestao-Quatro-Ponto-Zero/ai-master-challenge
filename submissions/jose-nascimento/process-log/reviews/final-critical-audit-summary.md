# Summary da Auditoria Crítica Final — Remediação

- **Data:** 2026-08-29
- **Commit auditado:** `86d7800`
- **Escopo da auditoria:** somente findings `CRITICAL` e `HIGH`; leitura
  independente do deliverable, dos scripts e dos artefatos derivados.
- **Resultado inicial:** `NOT_READY` por dois findings HIGH. Nenhum arquivo foi
  alterado durante a auditoria externa.
- **Registro:** este summary é uma remediação pós-It09 e não altera os
  summaries históricos nem o ledger E1–E8.

## Matriz de Findings

| Finding | Evidência | Ação de remediação | Estado |
|---|---|---|---|
| HIGH-001 — polaridade invertida | `21,0%` é `126/600` eventos com assinatura encerrada em ±30d; `79,0%` é `474/600` sem vínculo | Derivar `linked`/`unlinked` dos raw CSVs no gerador; renderizar `79,0%` na frase “não têm”; adicionar gates de polaridade no gerador e no verificador | Corrigido e validado; G9/F8 PASS |
| HIGH-002 — ponto KM posterior ao horizonte | o código anterior usava o primeiro ponto `t >= horizonte`; os pontos corretos são `S90=0,681461` e `S180=0,515156` pelo carry-forward | Centralizar `S(max(t <= h))`, marcar horizonte sem follow-up como não observável, recalcular independentemente no verificador e regenerar consumidores | Corrigido e validado; G13/F8 PASS |

## Valores corrigidos observados

| Métrica | Valor correto | Uso |
|---|---:|---|
| Eventos totais | 600 | denominador do linkage |
| Eventos com assinatura encerrada em ±30d | 126 / 21,0% | claim positivo |
| Eventos sem assinatura encerrada em ±30d | 474 / 79,0% | limitação executiva |
| KM de reativação em 90d | 0,681461 | taxa complementar ≈31,9% |
| KM de reativação em 180d | 0,515156 | taxa complementar ≈48,5% |
| Mediana KM | 187d | horizonte alcançado |

## Escopo preservado

- Os valores antigos `0,653`/`0,476` continuam citados apenas em registros
  históricos da It04 como valores anteriormente publicados; estão marcados
  como superados pela remediação e não são usados nos outputs atuais.
- E1–E8 permanecem exatamente oito erros materiais do processo original. Os
  dois findings desta auditoria são defeitos do deliverable final e ficam
  registrados aqui, não como um novo erro E9.
- It08 e It09 continuam `CONCLUDED`; It10 continua `PENDING` para o commit
  final e o PR.

## Rastreamento

- Prompt executado: [`final-critical-audit-fix-prompt.md`](../prompts/final-critical-audit-fix-prompt.md).
- Report de implementação: [`final-critical-audit-fix-report.md`](../reports/final-critical-audit-fix-report.md).
- Código KM: [`04_lifecycle_watchlist.py`](../../solution/src/04_lifecycle_watchlist.py).
- Gerador e gate de linkage: [`07_generate_executive_report.py`](../../solution/src/07_generate_executive_report.py).
- Verificação independente: [`06_verify_pipeline.py`](../../solution/src/06_verify_pipeline.py).
