# Diagnóstico operacional: o que os dados permitem decidir

## Resumo executivo

O primeiro achado não é um gargalo de atendimento. É um **gargalo de mensuração**. O Dataset 1 tem **8.469 tickets**, embora o brief mencione uma operação de aproximadamente 30 mil tickets por ano. Além disso, não existe timestamp de abertura e os campos de primeira resposta e resolução são datas, não durações.

Entre os **2.769 tickets** com ambos os timestamps, **1.365 (49,3%)** apresentam resolução anterior à primeira resposta. Portanto, o arquivo não permite calcular FRT, TTR, tempo ativo do agente, desperdício ou ROI observado.

## O que foi medido

| Dimensão | Resultado | Decisão suportada |
|---|---:|---|
| Tickets no arquivo | 8.469 | Não tratar o volume narrativo do brief como volume medido |
| Tickets fechados com CSAT | 2.769 | Restringir análises de satisfação a essa população |
| Pares temporais inválidos | 1.365 de 2.769 | Vetar métricas de tempo |
| Descrições com placeholder | 8.469 | Vetar mineração semântica como retrato de clientes reais |
| Emails detectados em descrições | 77 | Aplicar máscara antes de inferência e nunca exportar texto bruto |
| Telefones detectados em descrições | 165 | Aplicar máscara antes de inferência e nunca exportar texto bruto |

## Onde o fluxo trava

Com estes dados, não é defensável afirmar qual canal, prioridade ou tipo perde mais tempo. O que se pode afirmar é:

1. **A instrumentação temporal está quebrada ou semanticamente indefinida.**
2. **Os textos são templados:** todas as descrições contêm `{product_purchased}`.
3. **CSAT não diferencia os segmentos observados:** canal, prioridade, tipo e assunto apresentaram efeitos nulos ou desprezíveis na amostra fechada.
4. **A automação operacional não deve partir do Dataset 1:** ele serve para demonstrar auditoria, não para calibrar uma decisão produtiva.

## CSAT: associação, não causa

Foi aplicado Kruskal-Wallis apenas nos **2.769 tickets fechados**. Nenhuma dimensão apresentou evidência de associação material:

| Dimensão | p-valor | Efeito epsilon quadrado |
|---|---:|---:|
| Canal | 0,278 | 0,0003 |
| Prioridade | 0,629 | 0,0000 |
| Tipo | 0,699 | 0,0000 |
| Assunto | 0,807 | 0,0000 |

Isso não prova igualdade entre segmentos. Apenas mostra que o arquivo não sustenta priorização por CSAT.

## Diagnóstico priorizado

**População:** tickets operacionais da empresa.  
**Problema:** ausência de eventos confiáveis de criação, primeira resposta, interações e encerramento.  
**Consequência:** não é possível localizar espera, estimar capacidade ou provar ROI.  
**Primeira ação:** corrigir a telemetria antes de automatizar decisões de atendimento.

## Telemetria mínima

Registrar por ticket:

- `ticket_created_at`
- `first_human_response_at`
- `resolved_at`
- `active_handling_seconds`
- `reopened_at`
- `queue_id`
- `assigned_agent_id` pseudonimizado
- `suggestion_shown`
- `suggestion_accepted`
- `human_override`
- `final_category`
- `csat_sent_at`
- `csat_received_at`

## Papel do Dataset 2

O Dataset 2 tem **47.837 textos rotulados em oito classes**. Ele não representa a taxonomia de clientes do Dataset 1, mas permite testar uma capacidade técnica isolada: classificar texto, calibrar confiança e abster-se. Essa separação impede que uma prova técnica seja vendida como validação operacional.

## Conclusão

O 80/20 não é responder tickets automaticamente. É instalar a capacidade de **medir, sugerir, comparar e interromper**. Por isso, a solução escolhida é um copiloto em shadow mode, com decisão humana, abstenção e auditoria.
