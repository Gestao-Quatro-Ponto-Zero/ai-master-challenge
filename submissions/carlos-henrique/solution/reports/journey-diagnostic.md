# Jornadas agregadas descritivas

## Método

Eventos consecutivos repetidos são colapsados, a ordem estável é preservada e cada sequência é limitada a 12 passos. Quarentena é excluída.

## Jornadas completas

Top 1: `ACCOUNT_CREATED → SUBSCRIPTION_STARTED → FEATURE_USED → SUBSCRIPTION_STARTED → FEATURE_USED → SUBSCRIPTION_STARTED → FEATURE_USED → SUBSCRIPTION_STARTED → FEATURE_USED → SUBSCRIPTION_STARTED → FEATURE_USED → SUBSCRIPTION_STARTED` — 8/500 contas.

## Prefixos pré-churn

Foram resumidas 325 contas com prefixo até o primeiro churn.

## Churn e reativação

Há 26 contas com sequência churn → reativação e 26 com sequência pós-reativação.

## Suporte e limitações

Cada ranking registra suporte absoluto, relativo e denominador em `journey_summary.json`. A ordem no mesmo dia é técnica; as sequências são agregados descritivos, sem mineração formal ou grafo.
