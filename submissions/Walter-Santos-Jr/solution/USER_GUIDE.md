# Guia operacional ilustrado — RC4

Este guia utiliza as capturas fornecidas e homologadas pelo usuário. Os passos pressupõem a execução local do app e a seleção da persona correspondente. A identificação de um Deal deve ser consistente ao comparar telas de uma mesma jornada.

## UAT-01 — Head — Executive Command Center

**Finalidade:** Visão executiva e indicadores.

![Head — Executive Command Center](docs/uat_evidencias/uat-01.png)

## UAT-02 — Head — Segmentação

**Finalidade:** Região, gerente e setor selecionados.

![Head — Segmentação](docs/uat_evidencias/uat-02.png)

## UAT-03 — Manager — Performance

**Finalidade:** Comparação com os mesmos filtros do Head.

![Manager — Performance](docs/uat_evidencias/uat-03.png)

## UAT-04 — Seller — Pipeline

**Finalidade:** Fila comercial e priorização.

![Seller — Pipeline](docs/uat_evidencias/uat-04.png)

## UAT-05 — Seller — Opportunity 360

**Finalidade:** Contexto da oportunidade.

![Seller — Opportunity 360](docs/uat_evidencias/uat-05.png)

## UAT-06 — Qualification & Rework

**Finalidade:** Qualificação e pendências.

![Qualification & Rework](docs/uat_evidencias/uat-06.png)

## UAT-07 — Deal Closure Won

**Finalidade:** Fechamento positivo.

![Deal Closure Won](docs/uat_evidencias/uat-07.png)

## UAT-08 — Deal Closure Lost

**Finalidade:** Fechamento perdido.

![Deal Closure Lost](docs/uat_evidencias/uat-08.png)

## UAT-09A — Rework E2E — AS-IS

**Finalidade:** Deal antes da correção.

![Rework E2E — AS-IS](docs/uat_evidencias/uat-09a.png)

## UAT-09B — Rework E2E — Trigger

**Finalidade:** Detecção de Account não identificada.

![Rework E2E — Trigger](docs/uat_evidencias/uat-09b.png)

## UAT-09C — Rework E2E — Correction

**Finalidade:** Identificação/correção da Account.

![Rework E2E — Correction](docs/uat_evidencias/uat-09c.png)

## UAT-09D — Rework E2E — TO-BE

**Finalidade:** Deal corrigido de volta ao Pipeline.

![Rework E2E — TO-BE](docs/uat_evidencias/uat-09d.png)

## Jornada Closed-Loop de Rework

1. **AS-IS (`uat-09a`)**: identificar o Deal no Pipeline do Seller.
2. **Detect (`uat-09b`)**: acionar o Rework e observar a pendência de identificação da Account.
3. **Correct (`uat-09c`)**: executar a identificação/correção e conferir o status apresentado.
4. **Verify (`uat-09d`)**: retornar ao Pipeline e localizar o Deal corrigido.

As capturas documentam o fluxo visual. A comprovação técnica de persistência depende dos testes e do banco de dados correspondente.
