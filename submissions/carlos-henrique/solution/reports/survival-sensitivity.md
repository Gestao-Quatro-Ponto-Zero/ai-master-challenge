# Sensibilidade da sobrevivência

## Cenários

- `A_MAIN`: n=500, eventos=325, censura=35.00%, mediana=191.0.
- `B_STRICT`: n=497, eventos=46, censura=90.74%, mediana=NOT_REACHED.
- `C_SIGNUP_ORIGIN`: n=500, eventos=325, censura=35.00%, mediana=215.0.
- `D_SUBSCRIPTION_ORIGIN`: n=500, eventos=325, censura=35.00%, mediana=191.0.
- `E_NO_BASELINE_OVERLAP`: n=486, eventos=314, censura=35.39%, mediana=197.0.
- `F_QUALITY_GE_050`: n=126, eventos=89, censura=29.37%, mediana=305.0.

## Comparações métricas

| Cenário | Métrica | Referência | Alternativa | Classe |
|---|---|---:|---:|---|
| `B_STRICT` | `censoring_rate` | 0.35 | 0.9074446680080483 | `UNSTABLE` |
| `B_STRICT` | `survival_90d` | 0.6261421954683256 | 0.905281676291793 | `UNSTABLE` |
| `B_STRICT` | `survival_180d` | 0.5128803120271309 | 0.905281676291793 | `UNSTABLE` |
| `B_STRICT` | `survival_365d` | 0.33177574368361473 | 0.9015253207885076 | `UNSTABLE` |
| `B_STRICT` | `first_plan_ordering_at_180d` | Basic > Pro > Enterprise | Basic > Enterprise > Pro | `UNSTABLE` |
| `C_SIGNUP_ORIGIN` | `censoring_rate` | 0.35 | 0.35 | `ROBUST` |
| `C_SIGNUP_ORIGIN` | `survival_90d` | 0.6261421954683256 | 0.694413622553771 | `SENSITIVE` |
| `C_SIGNUP_ORIGIN` | `survival_180d` | 0.5128803120271309 | 0.5574950885006018 | `ROBUST` |
| `C_SIGNUP_ORIGIN` | `survival_365d` | 0.33177574368361473 | 0.35731114339330977 | `ROBUST` |
| `C_SIGNUP_ORIGIN` | `first_plan_ordering_at_180d` | Basic > Pro > Enterprise |  | `UNSTABLE` |
| `D_SUBSCRIPTION_ORIGIN` | `censoring_rate` | 0.35 | 0.35 | `ROBUST` |
| `D_SUBSCRIPTION_ORIGIN` | `survival_90d` | 0.6261421954683256 | 0.6261421954683256 | `ROBUST` |
| `D_SUBSCRIPTION_ORIGIN` | `survival_180d` | 0.5128803120271309 | 0.5128803120271309 | `ROBUST` |
| `D_SUBSCRIPTION_ORIGIN` | `survival_365d` | 0.33177574368361473 | 0.33177574368361473 | `ROBUST` |
| `D_SUBSCRIPTION_ORIGIN` | `first_plan_ordering_at_180d` | Basic > Pro > Enterprise | Basic > Pro > Enterprise | `ROBUST` |
| `E_NO_BASELINE_OVERLAP` | `censoring_rate` | 0.35 | 0.3539094650205762 | `ROBUST` |
| `E_NO_BASELINE_OVERLAP` | `survival_90d` | 0.6261421954683256 | 0.6393024857901182 | `ROBUST` |
| `E_NO_BASELINE_OVERLAP` | `survival_180d` | 0.5128803120271309 | 0.5232379006253964 | `ROBUST` |
| `E_NO_BASELINE_OVERLAP` | `survival_365d` | 0.33177574368361473 | 0.33743044672877104 | `ROBUST` |
| `E_NO_BASELINE_OVERLAP` | `first_plan_ordering_at_180d` | Basic > Pro > Enterprise | Basic > Pro > Enterprise | `ROBUST` |
| `F_QUALITY_GE_050` | `censoring_rate` | 0.35 | 0.2936507936507936 | `SENSITIVE` |
| `F_QUALITY_GE_050` | `survival_90d` | 0.6261421954683256 | 0.785714285714286 | `SENSITIVE` |
| `F_QUALITY_GE_050` | `survival_180d` | 0.5128803120271309 | 0.6746031746031751 | `UNSTABLE` |
| `F_QUALITY_GE_050` | `survival_365d` | 0.33177574368361473 | 0.45878136200716885 | `UNSTABLE` |
| `F_QUALITY_GE_050` | `first_plan_ordering_at_180d` | Basic > Pro > Enterprise | Basic > Pro > Enterprise | `ROBUST` |

## Interpretação

`ROBUST` indica variação relativa de até 10%; `SENSITIVE`, até 30%; `UNSTABLE`, acima de 30%, mudança de direção ou ausência de suporte. Resultados instáveis não são findings principais. Comparações entre signup e assinatura avaliam a origem temporal, não a causalidade da assinatura.
