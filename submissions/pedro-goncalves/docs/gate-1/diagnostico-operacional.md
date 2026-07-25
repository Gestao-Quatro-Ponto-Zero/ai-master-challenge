# Diagnóstico operacional: o que os dados permitem decidir

## Resumo executivo

O Dataset 1 é a amostra operacional disponível da empresa fictícia, com **8.469 tickets**. O brief informa uma operação de aproximadamente 30 mil tickets por ano; esse valor contextual não substitui a contagem observada. A base permite analisar filas, textos e sinais de cuidado, mas não possui timestamp de abertura e os campos de primeira resposta e resolução são datas, não durações.

Entre os **2.769 tickets** com ambos os timestamps, **1.365 (49,3%)** apresentam resolução anterior à primeira resposta. Portanto, o arquivo não permite calcular FRT, TTR, tempo ativo do agente, desperdício ou ROI observado.

## O que foi medido

| Dimensão | Resultado | Decisão suportada |
|---|---:|---|
| Tickets no arquivo | 8.469 | Não tratar o volume narrativo do brief como volume medido |
| Tickets fechados com CSAT | 2.769 | Restringir análises de satisfação a essa população |
| Pares temporais inválidos | 1.365 de 2.769 | Vetar métricas de tempo |
| Descrições com placeholder | 8.469 | Usar regras auditáveis e revisar falsos positivos |
| Contatos repetidos sem solução | 460 | Priorizar revisão humana; 152 casos ainda estão abertos e 152 constam como encerrados |
| Emails detectados em descrições | 77 | Aplicar máscara antes de inferência e nunca exportar texto bruto |
| Telefones detectados em descrições | 165 | Aplicar máscara antes de inferência e nunca exportar texto bruto |

## Onde o fluxo trava

Com estes dados, não é defensável afirmar qual canal, prioridade ou tipo perde mais tempo. O que se pode afirmar é:

1. **A instrumentação temporal está quebrada ou semanticamente indefinida.**
2. **A voz do cliente revela reincidência:** 460 descrições dizem que o suporte já foi procurado várias vezes e o problema continua sem solução.
3. **CSAT não diferencia os segmentos observados:** canal, prioridade, tipo e assunto apresentaram efeitos nulos ou desprezíveis na amostra fechada.
4. **O Dataset 1 sustenta o gate de cuidado e a revisão da fila**, mas seus rótulos não sustentam um classificador automático: modelos exploratórios ficaram próximos do acaso.

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
