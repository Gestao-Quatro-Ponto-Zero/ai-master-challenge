# Data Quality Notes

## Resumo

O Dataset 1 não foi tratado como fonte confiável para diagnóstico de gargalo por tempo/canal/CSAT. Ele foi usado para:

- identificar riscos de dados sintéticos;
- desenhar guardrails;
- representar um arquétipo B2C externo;
- testar o que **não** automatizar.

O Dataset 2 foi tratado como fonte principal para classificação textual.

---

## Achados no Dataset 1

| Verificação | Resultado |
|---|---:|
| Registros | 8,469 |
| `{product_purchased}` literal nas descrições | 100.0% |
| Tickets fechados | 2,769 |
| Deltas negativos entre resolução e primeira resposta | 1,365 (49.3%) |
| Deltas positivos | 1,404 |
| CSAT uniforme | p=0.797 |
| Status × canal | p=0.771 |
| Delta positivo × canal | p=0.791 |

## Interpretação

Filtrar deltas negativos não resolve o problema. Os deltas positivos restantes também não apresentam diferença significativa por canal. Por isso, a solução **não** usa tempos do Dataset 1 para afirmar ROI, desperdício por canal ou priorização de canal.

## Sobre o 67,3%

O valor é correto apenas como:

```text
Open + Pending Customer Response = 67,3% não fechados
```

Não deve ser escrito como “67,3% aguardando cliente”.

## Sobre `Resolution`

A coluna `Resolution` só existe após atendimento. Usá-la para prever rota inicial seria data leakage. Ela pode ser usada em análises pós-atendimento, mas não como feature do roteador.

## Sobre Dataset 2

O Dataset 2 tem 47,837 tickets de IT classificados em 8 categorias e foi adequado para treinar um classificador textual simples e reproduzível.
