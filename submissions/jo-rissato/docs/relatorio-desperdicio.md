# Quanto estamos desperdiçando?

Pergunta do brief: "Quantifique em horas e, se possível, estime custo. Onde está o maior desperdício recuperável?"
Base: Dataset 1, 8.469 tickets (100%). Cada número traz a sua base.

## 1. O que o dado permite medir em horas

| Grupo | Tickets | % da base | Horas medíveis? |
|---|---|---|---|
| Fechados com registro coerente | 1.404 | 16,6% | sim: horas entre a 1ª resposta e a resolução |
| Fechados com resolução antes da 1ª resposta | 1.365 | 16,1% | não: tempo negativo (soma de -10.799 h) |
| Abertos, sem nenhuma resposta | 2.819 | 33,3% | não: sem data de abertura nem de resposta |
| Respondidos, aguardando o cliente | 2.881 | 34,0% | não: sem data de abertura nem de fechamento |

Só 16,6% da base tem tempo medível. A hora medida é tempo decorrido entre a 1ª resposta e a resolução,
não tempo trabalhado pelo atendente: o dado não registra esforço.

## 2. As horas medíveis (n = 1.404)

- Soma: 10.639 h. Média 7,6 h, mediana 6,3 h, 90% abaixo de 16,0 h, máximo 23,5 h.
- Os 25% mais lentos (acima de 11,4 h) somam 51,7% das horas.
- Por recorte, as horas se distribuem na proporção do volume, sem diferença real:

| Recorte | Faixa da média por categoria | Fatia das horas | p (Kruskal) |
|---|---|---|---|
| Tipo | 7,0 h (cobrança) a 8,1 h (reembolso) | 18,0% a 23,2% | 0,160 |
| Canal | 7,3 h (telefone) a 7,9 h (redes sociais) | 22,3% a 26,8% | 0,791 |
| Prioridade | 7,1 h (crítica) a 8,1 h (alta) | 23,0% a 26,9% | 0,091 |

## 3. Custo

O dado não tem custo por hora, salário, número de atendentes nem tempo trabalhado. Estimar custo em reais
exigiria inventar essas premissas, e isso não foi feito. A conta fica pronta para quando o dado existir:
custo = horas trabalhadas por ticket × custo da hora do atendente × volume.

## 4. Repetição de texto (candidato a duplicata)

47 textos de descrição se repetem, cobrindo 439 tickets. Em nenhum grupo o mesmo cliente aparece duas vezes,
e só 5 dos 47 grupos têm o mesmo tipo de ticket. São textos-modelo do dado gerado, não tickets duplicados.
Duplicata não é desperdício mensurável aqui.

## 5. Onde está o maior desperdício recuperável

| Desperdício | Tamanho | Base |
|---|---|---|
| Demanda sem nenhuma resposta | 2.819 tickets (33,3%), dos quais 692 críticos | 8.469 |
| Registro de tempo que não serve para gestão | 1.365 de 2.769 fechados (49,3%) | 2.769 |
| Cauda de tempo nos fechados | 25% dos tickets = 51,7% das 10.639 h | 1.404 |
| Satisfação não coletada | 5.700 tickets (67,3%) | 8.469 |

O maior em volume é o terço sem resposta, distribuído igual por canal, prioridade e tipo. Não dá para
convertê-lo em horas, porque o dado não tem a data de abertura.
