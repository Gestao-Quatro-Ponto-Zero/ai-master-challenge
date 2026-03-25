# Classificador de tickets - Dataset 2

Shape do dataset: (47837, 2), colunas: ['text', 'label']
Distribuição de classes:
label
Hardware                 13617
HR Support               10915
Access                    7125
Miscellaneous             7060
Storage                   2777
Purchase                  2464
Internal Project          2119
Administrative rights     1760
Duplicidade aproximada: 0.000

## Métricas principais
- Accuracy: 0.855
- Macro F1: 0.853
- Melhor classe (F1): Purchase = 0.913
- Pior classe (F1): Administrative rights = 0.727
- Principais confusões:
  - HR Support rotulado como Hardware: 184 casos
  - Miscellaneous rotulado como Hardware: 130 casos
  - Hardware rotulado como HR Support: 119 casos
  - Administrative rights rotulado como Hardware: 105 casos
  - Hardware rotulado como Miscellaneous: 99 casos

## Classification report
- Access: precision 0.910, recall 0.892, f1 0.901
- Administrative rights: precision 0.870, recall 0.625, f1 0.727
- HR Support: precision 0.870, recall 0.854, f1 0.862
- Hardware: precision 0.799, recall 0.880, f1 0.837
- Internal Project: precision 0.897, recall 0.847, f1 0.871
- Miscellaneous: precision 0.823, recall 0.825, f1 0.824
- Purchase: precision 0.962, recall 0.868, f1 0.913
- Storage: precision 0.925, recall 0.861, f1 0.892

Matriz de confusão: ver submissions/bruno-reis/outputs/classifier_confusion_matrix.png