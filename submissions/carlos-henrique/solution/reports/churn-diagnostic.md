# Diagnóstico descritivo de churn e reativação

## População e denominador

VALID + VALID_WITH_WARNING; quarantine excluded. Denominador: 500 contas. Proporções são observadas, não taxas temporais.

## Estados principais

| Estado principal | Contas | Proporção observada |
|---|---:|---:|
| `REACTIVATED_THEN_CHURNED_AGAIN` | 4 | 0.80% |
| `REACTIVATED` | 22 | 4.40% |
| `RECURRING_CHURN` | 118 | 23.60% |
| `SINGLE_CHURN` | 181 | 36.20% |
| `NO_CHURN_OBSERVED` | 175 | 35.00% |

## Recorrência e intervalos

- churn observado: 325 contas (65.00%);
- churn recorrente: 128 contas (25.60%);
- tempo mediano cadastro → primeiro churn: 104.0 dias;
- intervalo mediano entre churns: 61.0 dias;
- intervalo mediano churn → reativação: 45.0 dias;
- intervalo mediano reativação → novo churn: 56.5 dias.

## Comparações

As comparações de uso, suporte, satisfação, MRR e assinaturas estão em `churn_diagnostics.json`, com média, mediana, quartis, diferença, razão, n e missingness.

## Ressalvas

Ausência de churn é `NO_CHURN_OBSERVED`; eventos com warning alteram materialmente os estados; nenhuma comparação demonstra mecanismo explicativo.
