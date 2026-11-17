# Diagnóstico do dataset de suporte

Total de tickets: 8.469

## 1. Qualidade dos dados (antes de qualquer conclusão)

Tickets por status: Pending Customer Response 2881, Open 2819, Closed 2769
- Closed: tempo preenchido 100.0%, satisfação preenchida 100.0%
- Open: tempo preenchido 0.0%, satisfação preenchida 0.0%
- Pending Customer Response: tempo preenchido 0.0%, satisfação preenchida 0.0%
- As colunas de 'tempo' são data/hora, não duração. Todas as primeiras respostas cabem em 27 horas (31/05/2023 a 02/06/2023).
- Em 49.3% dos tickets fechados, a resolução acontece ANTES da primeira resposta.
- Distribuição da satisfação (1 a 5): 1: 553, 2: 549, 3: 580, 4: 543, 5: 544
- Descrições com o texto-modelo '{product_purchased}' não preenchido: 100.0%
- Frases de abertura diferentes nas descrições: 16
- Domínios de e-mail: example.com, example.org, example.net

## 2. Onde o fluxo trava?

### Status por Ticket Channel

| Ticket Channel   |   Closed |   Open |   Pending Customer Response |
|:-----------------|---------:|-------:|----------------------------:|
| Chat             |    0.325 |  0.33  |                       0.344 |
| Email            |    0.336 |  0.327 |                       0.337 |
| Phone            |    0.324 |  0.345 |                       0.331 |
| Social media     |    0.322 |  0.329 |                       0.349 |

### Status por Ticket Type

| Ticket Type          |   Closed |   Open |   Pending Customer Response |
|:---------------------|---------:|-------:|----------------------------:|
| Billing inquiry      |    0.333 |  0.33  |                       0.337 |
| Cancellation request |    0.304 |  0.343 |                       0.352 |
| Product inquiry      |    0.325 |  0.324 |                       0.351 |
| Refund request       |    0.34  |  0.322 |                       0.338 |
| Technical issue      |    0.332 |  0.345 |                       0.323 |

### Status por Ticket Priority

| Ticket Priority   |   Closed |   Open |   Pending Customer Response |
|:------------------|---------:|-------:|----------------------------:|
| Critical          |    0.341 |  0.325 |                       0.334 |
| High              |    0.338 |  0.338 |                       0.324 |
| Low               |    0.312 |  0.337 |                       0.35  |
| Medium            |    0.317 |  0.332 |                       0.352 |

- Tickets parados aguardando o cliente: 2881 (34.0%)

## 3. O que impacta a satisfação?

- Ticket Channel: médias {'Chat': 3.08, 'Email': 2.96, 'Phone': 2.95, 'Social media': 2.97} | ANOVA p = 0.28 (diferença compatível com acaso)
- Ticket Type: médias {'Billing inquiry': 3.03, 'Cancellation request': 3.03, 'Product inquiry': 3.02, 'Refund request': 2.93, 'Technical issue': 2.96} | ANOVA p = 0.70 (diferença compatível com acaso)
- Ticket Priority: médias {'Critical': 2.96, 'High': 2.98, 'Low': 3.05, 'Medium': 2.98} | ANOVA p = 0.63 (diferença compatível com acaso)
- Correlação entre o 'tempo' calculado e a satisfação: 0.02

Conclusão: com estes dados não é possível afirmar onde se perde tempo nem o que move a satisfação. O achado é que a operação não mede de forma confiável o que importa.