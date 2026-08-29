# Prompt de Remediação da Auditoria Crítica Final

- **Escopo:** corrigir somente os findings HIGH da auditoria externa final do
  commit `86d7800`.
- **Data:** 2026-08-29
- **Executor:** estágio de remediação no mesmo workspace da submissão.
- **Restrições:** alterar somente `submissions/jose-nascimento/`; preservar o
  ledger histórico E1–E8 e as iterações It00–09; não criar E9; não abrir PR.

## Findings obrigatórios

1. **HIGH-001 — polaridade evento–assinatura:** os dados definem `21,0%`
   (`126/600`) como eventos com assinatura encerrada em até 30 dias. A frase
   que diz “não têm” deve usar `79,0%` (`474/600`). O gerador deve derivar as
   duas contagens dos CSVs e um gate deve rejeitar a polaridade invertida.
2. **HIGH-002 — horizonte KM:** a estimativa deve usar a função degrau
   `S(h) = S(max(t <= h))` quando o horizonte é observável; se não houver
   follow-up suficiente, deve retornar valor não observável. Recalcular
   independentemente e regenerar todos os consumidores.

## Critérios de aceitação

- `solution/src/04_lifecycle_watchlist.py` implementa a semântica de horizonte
  e registra o maior tempo observado.
- `solution/src/05_actions_impact.py`, evidence 04, t12, t15, t18, t20 e o
  relatório executivo usam os valores recalculados, sem valores stale.
- `solution/src/07_generate_executive_report.py` deriva e testa com/sem vínculo.
- `solution/src/06_verify_pipeline.py` testa a polaridade textual e recalcula
  o KM a partir dos raw inputs, sem depender apenas de anchors estáticos.
- A execução é offline, determinística, sem `__pycache__`, com `./run.sh`,
  `make all`, `make verify`, testes negativos e clone fresco.
- Documentar a remediação em [`final-critical-audit-summary.md`](../reviews/final-critical-audit-summary.md)
  e [`final-critical-audit-fix-report.md`](../reports/final-critical-audit-fix-report.md).
- Completar commit/push somente depois de todas as validações; a etapa formal
  It10 e o PR continuam pendentes neste prompt.
