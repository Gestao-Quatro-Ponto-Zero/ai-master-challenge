# Journey mining — diagnóstico descritivo

## Executive Summary

Foram construídas 4,221 jornadas governadas para 500 contas, sem quarentena. Padrões representam recorrência observada, não causa, previsão ou recomendação individual. O gate é **PASS_WITH_WARNINGS** porque warnings e ordenação intradiária ainda limitam parte da evidência.

## 1. Objetivo

Descrever sequências recorrentes de uso, suporte, churn e reativação de forma auditável.

## 2. População

Principal: VALID + VALID_WITH_WARNING. Estrita: VALID. Contas: 500.

## 3. Construção das sequências

Unidade conta; cada escopo tem limite temporal explícito e chave única por população.

## 4. Ordenação

`account_id`, `event_time`, `event_order_on_same_day`, `event_id`. O desempate técnico não é causal.

## 5. Normalização

Representações raw, colapsada e bucket diário estruturado; bandas {'short_upper': 21.0, 'medium_upper': 33.0, 'basis': 'MAIN_FULL_OBSERVED_JOURNEY_Q33_Q67'}.

## 6. Transições

- FEATURE → SUBSCRIPTION_START: 161/181 contas; ROBUST.
- SUBSCRIPTION_START → FEATURE: 160/175 contas; UNSTABLE.
- ACCOUNT → SUBSCRIPTION_START: 160/181 contas; UNSTABLE.
- SUBSCRIPTION_START → FEATURE: 160/181 contas; UNSTABLE.
- ACCOUNT → SUBSCRIPTION_START: 160/181 contas; UNSTABLE.
- FEATURE → SUBSCRIPTION_START: 156/175 contas; ROBUST.
- ACCOUNT → SUBSCRIPTION_START: 145/175 contas; UNSTABLE.
- SUPPORT_OPEN → SUPPORT_CLOSE: 122/175 contas; UNSTABLE.

## 7. N-grams

Bigrams a 5-grams colapsados e bigram raw de sensibilidade, com suporte por conta.

## 8. Padrões sequenciais

- SUBSCRIPTION_START -> SUBSCRIPTION_START: 480/500 contas; ROBUST.
- SUBSCRIPTION_START -> FEATURE: 463/500 contas; ROBUST.
- FEATURE -> SUBSCRIPTION_START: 458/500 contas; ROBUST.
- SUBSCRIPTION_START -> FEATURE -> SUBSCRIPTION_START: 449/500 contas; ROBUST.
- ACCOUNT -> SUBSCRIPTION_START: 447/500 contas; ROBUST.
- SUBSCRIPTION_START -> SUBSCRIPTION_START -> FEATURE: 429/500 contas; ROBUST.
- FEATURE -> FEATURE: 413/500 contas; ROBUST.
- FEATURE -> SUBSCRIPTION_START -> FEATURE: 412/500 contas; ROBUST.

## 9. Pré-churn

Sufixos de 2, 3 e 5 eventos foram comparados em janelas fixas de 7/30/60/90 dias; observation_end é o pseudo-cutoff não churn.

## 10. Churn recorrente

Intervalos são descritivos e preservam reativação, retorno de uso, suporte e duração.

## 11. Reativação

Somente eventos explícitos sustentam reativação; ausência de evento não foi tratada como intervenção.

## 12. Taxonomia

Dez classes determinísticas, uma principal e classes secundárias, sem score ou previsão.

## 13. Estabilidade

ROBUST, SENSITIVE e UNSTABLE reconciliam principal e estrita; HIGH nunca é finding.

## 14. Exposição

Janelas fixas, landmarks, suporte por conta e bandas de comprimento limitam viés de jornadas longas.

## 15. Findings

- **Sufixo pré-churn em janela de 90 dias** — SUBSCRIPTION_START -> CHURN ocorreu em 169/325 contas com churn e 0/175 sem churn no pseudo-cutoff comparável.
- **Sufixo pré-churn em janela de 60 dias** — SUBSCRIPTION_START -> CHURN ocorreu em 161/325 contas com churn e 0/175 sem churn no pseudo-cutoff comparável.
- **Sufixo pré-churn em janela de 30 dias** — SUBSCRIPTION_START -> CHURN ocorreu em 131/325 contas com churn e 0/175 sem churn no pseudo-cutoff comparável.
- **Sufixo pré-churn em janela de 90 dias** — FEATURE -> CHURN ocorreu em 107/325 contas com churn e 0/175 sem churn no pseudo-cutoff comparável.
- **Transição recorrente e estável** — SUBSCRIPTION_END → SUBSCRIPTION_START ocorreu em 14/118 contas no escopo BETWEEN_RECURRING_CHURNS (RECURRING_CHURN).
- **Transição recorrente e estável** — FEATURE → SUBSCRIPTION_START ocorreu em 156/175 contas no escopo FULL_OBSERVED_JOURNEY (NO_CHURN_OBSERVED).

## 16. Limitações

Associação não implica causalidade; sistema não observa ações externas; warnings e grupos pequenos limitam interpretação.

## 17. Preparação para o grafo

Somente padrões ROBUST/SENSITIVE, com denominadores, exposição e direção preservados, poderão alimentar a próxima fase. Nenhum grafo foi construído.
