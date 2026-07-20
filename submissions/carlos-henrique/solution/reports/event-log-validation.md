# Validação do event log temporal — Fase 2

## 1. Objetivo

Validar uma camada temporal canônica, reproduzível e rastreável, sem executar diagnóstico de churn, journey mining, análise de receita, survival analysis ou grafo.

## 2. Fontes

Foram carregadas as cinco fontes oficiais com validação de presença e SHA-256 contra o manifest da Fase 1. Os CSVs permaneceram read-only.

## 3. Modelo do event log

Cada evento preserva entidade, tempo, tipo, origem, linha física, regra de geração, qualidade e vínculo opcional a episódio. Churn permanece no grão de conta; `candidate_subscription_id` é somente uma atribuição auditável.

## 4. Tipos de evento

| tipo de evento | eventos |
|---|---:|
| `ACCOUNT_CREATED` | 500 |
| `CHURN_RECORDED` | 539 |
| `FEATURE_USED` | 25.000 |
| `REACTIVATION_RECORDED` | 61 |
| `SUBSCRIPTION_ENDED` | 486 |
| `SUBSCRIPTION_STARTED` | 5.000 |
| `SUPPORT_TICKET_CLOSED` | 2.000 |
| `SUPPORT_TICKET_OPENED` | 2.000 |

Não foram criados eventos comportamentais derivados, upgrade ou downgrade, pois não existe timestamp inequívoco para essas transições no snapshot.

## 5. Volume por evento

- oportunidades de evento: 35586;
- eventos gerados: 35586;
- event log ativo: 13927;
- quarentena: 21659.

## 6. Reconciliação

| fonte | registros | oportunidades | ativos | quarentena | removidos | diferença |
|---|---:|---:|---:|---:|---:|---:|
| `accounts` | 500 | 500 | 500 | 0 | 0 | 0 |
| `churn_events` | 600 | 600 | 522 | 78 | 0 | 0 |
| `feature_usage` | 25000 | 25000 | 5568 | 19432 | 0 | 0 |
| `subscriptions` | 5000 | 5486 | 5486 | 0 | 0 | 0 |
| `support_tickets` | 2000 | 4000 | 1851 | 2149 | 0 | 0 |

A reconciliação usa oportunidades de evento porque uma assinatura pode gerar início e fim e um ticket pode gerar abertura e fechamento. Diferença não explicada: **0**.

## 7. Qualidade

| classificação | eventos |
|---|---:|
| `QUARANTINED` | 21.659 |
| `VALID` | 10.703 |
| `VALID_WITH_WARNING` | 3.224 |

Eventos com cronologia impossível foram preservados na quarentena. Warnings permanecem utilizáveis apenas com filtros explícitos.

## 8. Duplicatas

- duplicatas exatas removidas: 0;
- linhas afetadas por `DUPLICATE_SOURCE_ID`: 42;
- excedentes de `usage_id`: 21;
- linhas afetadas por `DUPLICATE_CANDIDATE_KEY`: 6;
- excedentes da chave candidata: 3.

Registros distintos com ID ou chave candidata repetidos foram preservados e sinalizados; nenhuma soma ou descarte silencioso foi aplicado.

## 9. Churn recorrente

- contas sem churn explícito: 161;
- contas com um churn: 190;
- contas com múltiplos churns: 149;
- máximo de churns por conta: 5.

## 10. Reativação

Foram preservadas 61 reativações explícitas em 55 contas. Reativações sem churn anterior utilizável: 31.

## 11. Episódios

- episódios: 5000;
- abertos: 4514;
- encerrados: 486;
- com sobreposição: 4992.

Cada `subscription_id` permanece um episódio independente; churn não encerra assinatura automaticamente.

## 12. Limitações

- datas sem hora são representadas à meia-noite, sem inferência intradiária;
- o timezone é `NAIVE_SOURCE_TIME`;
- grande parte dos usos contradiz o início/fim da assinatura e fica em quarentena;
- múltiplas assinaturas ativas tornam a atribuição de churn ambígua;
- snapshot não prova estabilidade histórica dos IDs nem disponibilidade as-of de atributos mutáveis.

## 13. Uso permitido

Reconstrução de jornadas, diagnóstico descritivo e análises temporais futuras usando apenas eventos ativos, cutoffs as-of e segmentação explícita por qualidade.

## 14. Uso proibido

Usar quarentena como evidência válida, interpretar desempate como causal, transformar flags snapshot em eventos, usar texto livre, atribuir churn ambiguamente ou calcular features com informação posterior ao cutoff.

## 15. Gate para Fase 3

**`PASS_WITH_WARNINGS`**. O event log está reconciliado e auditável, mas qualquer diagnóstico deve excluir quarentena, respeitar warnings e declarar a política temporal utilizada.
