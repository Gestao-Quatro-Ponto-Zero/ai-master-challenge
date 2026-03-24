# Fase 3 — Análise de Causa Raiz

## Hipótese central
"Se as médias são iguais entre churned e retidos, o problema está nos segmentos."

Testei sistematicamente com a IA executando queries que EU defini:

## Testes realizados

| Teste | Resultado | Insight |
|---|---|---|
| Churn por indústria | DevTools = 31% (2x média) | Product-market fit fraco nesse vertical |
| Churn por canal | Eventos = 30% (2x partners) | Leads de baixa qualidade |
| Churn por MRR tier | Mid-market $1K-2.5K = 26%, 55% da base | Gap de atendimento |
| Churn temporal | 6 → 251 eventos/trimestre (42x em 2 anos) | Crise acelerando |
| Uso per-account H1→H2 | Caiu -0.3% count, -2.5% duração | CEO errado |
| Satisfação churned vs retidos | 4.01 vs 3.97 (churned MAIOR) | Paradoxo explicável |
| Escala de satisfação | Zero notas 1 e 2 em 2.000 tickets | Instrumento quebrado |
| Feedback textual | 36% preço, 34% features, 30% competidor | Multifatorial |

## O que EU adicionei

### Validação do claim do CEO
A IA analisa o que eu peço. Mas a decisão de TESTAR se "uso cresceu" segmentando por account e por semestre foi minha. Ela não questionaria a premissa do CEO espontaneamente.

### Paradoxo de satisfação
A IA flagou que churned > retidos. A interpretação de que isso indica churn por fatores exógenos (pricing/competitive) e não por insatisfação com suporte foi julgamento meu.

### Escala quebrada
Ao investigar o non-response bias, descobri que a escala só tem notas 3, 4 e 5. Isso não é uma pesquisa — é uma confirmação forçada de satisfação. O CS está medindo com régua de borracha.
