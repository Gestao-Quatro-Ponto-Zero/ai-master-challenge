# Inventário de evidências UAT — RC4

As imagens são evidências visuais fornecidas pelo usuário, não resultados de execução automatizada.

| Arquivo | Cenário | Objetivo |
|---|---|---|
| `uat-01.png` | Head — Executive Command Center | Visão executiva e indicadores |
| `uat-02.png` | Head — Segmentação | Região, gerente e setor selecionados |
| `uat-03.png` | Manager — Performance | Comparação com os mesmos filtros do Head |
| `uat-04.png` | Seller — Pipeline | Fila comercial e priorização |
| `uat-05.png` | Seller — Opportunity 360 | Contexto da oportunidade |
| `uat-06.png` | Qualification & Rework | Qualificação e pendências |
| `uat-07.png` | Deal Closure Won | Fechamento positivo |
| `uat-08.png` | Deal Closure Lost | Fechamento perdido |
| `uat-09a.png` | Rework E2E — AS-IS | Deal antes da correção |
| `uat-09b.png` | Rework E2E — Trigger | Detecção de Account não identificada |
| `uat-09c.png` | Rework E2E — Correction | Identificação/correção da Account |
| `uat-09d.png` | Rework E2E — TO-BE | Deal corrigido de volta ao Pipeline |

## Aceite e limitações

- As 12 imagens foram recebidas, com nomes e formatos previstos.
- A homologação funcional e visual foi confirmada pelo usuário na conversa.
- O pacote não inclui, por si só, uma trilha transacional exportada do SQLite do ambiente do usuário.
- Os testes automatizados verificam regras e endpoints; prints isolados não comprovam reconciliação numérica ou persistência após reinicialização.
- Para auditoria aprofundada, anexar o log de testes, identificadores de oportunidade e, quando permitido, um snapshot sanitizado das transações UAT.
