# CRP-REAL-05 — Fazer a UI refletir claramente o dataset real

## Objetivo
Garantir que o produto visível demonstre, sem ambiguidade, que está operando sobre dados reais do challenge.

## Problema que resolve
Mesmo com API real, a UI pode continuar parecendo demo se mostrar labels, IDs ou exemplos artificiais.

## Tarefas
1. Revisar a tabela principal, filtros, KPIs e drawer de detalhe.
2. Remover textos/nomes sintéticos que não façam sentido no contexto do dataset real.
3. Garantir que a UI mostre:
   - `opportunity_id` real
   - `account`
   - `product`
   - `sales_agent`
   - `manager`
   - `regional_office`
   - `deal_stage`
   - `close_value`
   - score e explicação
4. Ajustar copy para narrativa de produto B2B, não demo template.

## Entregáveis
- UI atualizada
- `docs/UI_REAL_DATA_ALIGNMENT.md`
- atualização de `LOG.md`
- atualização de `PROCESS_LOG.md`

## Impacto na Submissão
- aumenta a percepção de aderência ao challenge
- torna a demo mais convincente

## Evidências obrigatórias
- screenshots da dashboard com dados reais
- screenshot do drawer com explicação real
- nota comparando antes/depois da UI

## Atualizações obrigatórias de process log
- registrar decisões de UX e limpeza visual
- anotar onde a IA propôs labels genéricos e como foram corrigidos

## Atualizações obrigatórias de README/Submission
- atualizar screenshots e roteiro de demo se necessário

## Definition of Done
- UI principal deixa claro o uso do dataset real
- não há mais cara de dataset sintético no fluxo de demo
- evidências, LOG e PROCESS_LOG atualizados
