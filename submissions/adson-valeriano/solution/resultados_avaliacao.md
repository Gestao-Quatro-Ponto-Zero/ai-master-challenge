# Resultados da avaliação do classificador

- Tickets de teste (nunca vistos no treino): 9.568
- Acurácia geral: 86.6%
- Referência (chutar sempre a categoria mais comum): 28.5%

## Cobertura x acerto por limiar de confiança

| Limiar | Tickets que a IA decide sozinha | Acerto nesses tickets |
|---|---|---|
| 50% | 88.4% | 91.2% |
| 60% | 80.0% | 93.8% |
| 70% | 71.7% | 95.6% |
| 80% | 62.4% | 97.3% |
| 90% | 50.5% | 98.7% |

## Desempenho por categoria

```
                       precision    recall  f1-score   support

               Access       0.90      0.90      0.90      1425
Administrative rights       0.77      0.80      0.79       352
           HR Support       0.89      0.86      0.88      2183
             Hardware       0.86      0.84      0.85      2724
     Internal Project       0.84      0.91      0.87       424
        Miscellaneous       0.81      0.86      0.84      1412
             Purchase       0.94      0.90      0.92       493
              Storage       0.90      0.91      0.90       555

             accuracy                           0.87      9568
            macro avg       0.86      0.87      0.87      9568
         weighted avg       0.87      0.87      0.87      9568

```

## Matriz de confusão (linha = real, coluna = previsto)

|                       |   Access |   Administrative rights |   HR Support |   Hardware |   Internal Project |   Miscellaneous |   Purchase |   Storage |
|:----------------------|---------:|------------------------:|-------------:|-----------:|-------------------:|----------------:|-----------:|----------:|
| Access                |     1277 |                      13 |           26 |         53 |                 12 |              35 |          2 |         7 |
| Administrative rights |        4 |                     283 |            5 |         52 |                  0 |               7 |          0 |         1 |
| HR Support            |       37 |                       8 |         1884 |        129 |                 25 |              76 |          5 |        19 |
| Hardware              |       76 |                      50 |          114 |       2299 |                 20 |             131 |         18 |        16 |
| Internal Project      |        2 |                       1 |           11 |         16 |                384 |               9 |          0 |         1 |
| Miscellaneous         |       22 |                       6 |           62 |         82 |                 15 |            1211 |          1 |        13 |
| Purchase              |        2 |                       3 |            7 |         27 |                  1 |               9 |        442 |         2 |
| Storage               |        2 |                       4 |           11 |         20 |                  1 |              10 |          0 |       507 |

## Teste de transferência: modelo de TI aplicado ao dataset de suporte ao cliente

- Confiança média: 55% (no dataset de TI: 81%)
- Tickets acima do limiar de 70%: 18.6%
- Categoria mais prevista: Hardware (74% dos tickets, inclusive cobrança e reembolso)
- Conclusão: o modelo não transfere. Para o suporte da empresa, é preciso treinar com tickets rotulados da própria operação.