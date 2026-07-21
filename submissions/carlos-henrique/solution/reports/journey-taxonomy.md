# Taxonomia de jornadas

## ADOPTION_JOURNEY (J01)

High 30-day use and multiple active days after subscription start. Janela: 30D. Limitações: DESCRIPTIVE_NOT_CAUSAL.

## LOW_ENGAGEMENT_JOURNEY (J02)

Low activity in the fixed 30-day window. Janela: 30D. Limitações: ABSENCE_OF_EVENT_IS_NOT_INTERVENTION.

## SUPPORT_HEAVY_JOURNEY (J03)

At least three support openings in the observed journey. Janela: FULL. Limitações: TICKET_CONTENT_NOT_USED.

## CHURN_PATH (J04)

Observed journey includes one churn and no later recovery class. Janela: FULL. Limitações: NO_CAUSAL_ATTRIBUTION.

## RECURRING_CHURN_PATH (J05)

Observed journey contains at least two churn events. Janela: FULL. Limitações: DESCRIPTIVE_NOT_PREDICTIVE.

## REACTIVATION_PATH (J06)

Churn is followed by an observed reactivation. Janela: POST_CHURN. Limitações: CUSTOMER_SUCCESS_ACTION_NOT_INFERRED.

## RECOVERY_JOURNEY (J07)

Reactivation is followed by feature use or subscription start. Janela: POST_REACTIVATION. Limitações: ACTIVITY_DOES_NOT_IMPLY_CAUSATION.

## DORMANT_JOURNEY (J08)

At least 90 days between adjacent usable events. Janela: FULL. Limitações: OUTSIDE_SYSTEM_ACTIVITY_UNOBSERVED.

## HIGH_VALUE_LOW_USAGE (J09)

High MRR and low activity in a fixed window. Janela: 30D. Limitações: VALUE_BAND_IS_DESCRIPTIVE.

## DATA_QUALITY_CONSTRAINED (J10)

Warnings or limited quality coverage constrain classification. Janela: FULL. Limitações: QUALITY_STATUS_NOT_CUSTOMER_BEHAVIOR.

## Distribuição principal

- ADOPTION_JOURNEY: 43
- CHURN_PATH: 190
- DATA_QUALITY_CONSTRAINED: 20
- DORMANT_JOURNEY: 24
- HIGH_VALUE_LOW_USAGE: 39
- REACTIVATION_PATH: 2
- RECOVERY_JOURNEY: 17
- RECURRING_CHURN_PATH: 116
- SUPPORT_HEAVY_JOURNEY: 49
