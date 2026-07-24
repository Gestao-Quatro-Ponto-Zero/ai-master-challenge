# Model Card: classificador de tickets de TI

## Propósito

Demonstrar, em dados públicos, uma etapa de triagem com classificação, confiança calibrada e abstenção. O modelo não foi validado para suporte ao cliente da G4 nem para o Dataset 1.

## Dados e protocolo

- Fonte: Dataset 2 do Challenge 002
- Linhas: **47,837**
- Treino e calibração interna: **33,485**
- Validação exclusiva de threshold: **7,176**
- Teste final: **7,176**
- Classes: **8**
- Split: estratificado 70/15/15, seed 42
- Duplicatas normalizadas: nenhuma detectada no data audit

O threshold foi escolhido na validação. O teste final foi usado uma única vez para reportar as métricas abaixo.

## Resultado no teste final

| Métrica | Baseline majoritário | Modelo |
|---|---:|---:|
| Acurácia | 0.285 | 0.867 |
| Macro-F1 | 0.055 | 0.868 |
| Balanced accuracy | n/a | 0.853 |
| Weighted-F1 | n/a | 0.867 |
| ECE, 10 bins | n/a | 0.049 |

## Abstenção

Critério pré-aplicado na validação: maximizar cobertura com acurácia seletiva mínima de 95%.

- Threshold selecionado: **0.75**
- Validação: cobertura **70.1%**, acurácia nos cobertos **96.0%**
- Teste final: cobertura **69.7%**, acurácia nos cobertos **96.6%**

Esse threshold é uma referência técnica para shadow mode. Não autoriza execução em produção.

## Limitações

1. A taxonomia é de suporte interno de TI e não equivale à taxonomia do Dataset 1.
2. O texto já foi pré-processado pela origem.
3. Calibração em dados públicos não representa risco de produção.
4. Não há validação temporal, mudança de domínio nem rótulos da G4.
5. O protótipo deve operar em shadow mode e permitir abstenção, override e kill switch.
