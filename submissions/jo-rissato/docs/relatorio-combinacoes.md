# Piores combinações: real ou acaso?

Teste de permutação com 1000 embaralhamentos por cruzamento. Mínimo de 30 tickets por combinação (8 no cruzamento triplo).

## 1. Tempo até resolver (mediana de horas)

Base: 1404 tickets fechados com registro coerente, de 8469 no total. Os outros não têm tempo de resolução (5700 não fechados) ou têm resolução antes da 1ª resposta (1365).

| Cruzamento | Pior combinação real | Tickets | Pior por acaso (mediana) | Limite do acaso (95%) | Real? |
|---|---|---|---|---|---|
| Canal × prioridade | Chat / Alta | 101 | 7.9 h | 8.8 h | não (8.4 h) |
| Prioridade × tipo | Alta / Reembolso | 83 | 8.2 h | 9.2 h | não (8.8 h) |
| Canal × tipo | Chat / Cancelamento | 75 | 8.2 h | 9.2 h | não (7.3 h) |
| Canal × prioridade × tipo | Chat / Baixa / Problema técnico | 15 | 11.8 h | 14.3 h | não (13.2 h) |

## 2. Tickets sem nenhuma resposta (%)

Base: 8469 tickets, 100% do Dataset 1.

| Cruzamento | Pior combinação real | Tickets | Pior por acaso (mediana) | Limite do acaso (95%) | Real? |
|---|---|---|---|---|---|
| Canal × prioridade | Telefone / Baixa | 499 | 36.8% | 38.6% | sim (38.9%) |
| Prioridade × tipo | Alta / Cancelamento | 398 | 37.5% | 39.8% | não (37.9%) |
| Canal × tipo | Redes sociais / Cancelamento | 413 | 37.5% | 39.6% | não (36.3%) |
| Canal × prioridade × tipo | Telefone / Alta / Cobrança | 103 | 44.4% | 48.4% | não (44.7%) |

## Verificação do único "sim"

Telefone / Baixa passou do limite de 95% por 0,3 ponto (38,9% contra 38,6%). Conferência com 5.000
embaralhamentos: p = 0,049. Foram feitos 8 testes nesta página (4 cruzamentos × 2 medidas); a 5%,
espera-se 0,4 falso positivo só por acaso. Com a correção de Bonferroni para 8 testes, o limite
sobe para 40,1%, e 38,9% não passa. **Resultado: nenhuma combinação é pior que o acaso.**

## Conclusão

- O resultado anterior de tempo (1.404 tickets) se mantém com 1.000 embaralhamentos: nenhuma
  combinação real passa do limite do acaso.
- Em 100% da base (8.469), medindo tickets sem resposta, também nenhuma combinação se destaca
  depois da correção para testes múltiplos.
