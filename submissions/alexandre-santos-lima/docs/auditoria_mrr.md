# Auditoria do MRR

Gerado por `solution/scripts/08_auditoria_mrr.py`.

| checagem | resultado | leitura |
|---|---|---|
| MRR = assentos × preço de tabela | 100,0% | preço fixo por assento: Basic US$ 19, Enterprise US$ 199, Pro US$ 49; sem desconto nem proporcionalidade |
| ARR = 12 × MRR | 100,0% | inclusive em contrato anual |
| Assinaturas pagas ativas ao mesmo tempo por conta | mediana 8, máx. 16 | só 4 contas têm uma só: assinaturas se sobrepõem |
| MRR ativo por conta | mediana US$ 16.654, máx. US$ 131.911 | soma de assinaturas sobrepostas: total provavelmente inflado |
| MRR ativo total (soma) | US$ 10.159.608 | usar com cautela |
| Assinaturas com upgrade E downgrade | 20 | marcações contraditórias |
| Plano da conta = plano mais frequente nas assinaturas | 30,6% | acaso seria ~33% |
| Assentos da conta × soma dos assentos ativos | ρ = 0,53 | cadastro e assinaturas não batem |

# Churn de receita por segmento

% do MRR (assinaturas pagas) em assinaturas encerradas. Média geral: **10,4%**. IC 95% por bootstrap de contas.


## Indústria

| nível | churn de receita | IC 95% | contas | assinaturas |
|---|---|---|---|---|
| Cybersecurity | 12,4% | 8,9–16,4% | 100 | 866 |
| HealthTech | 10,6% | 7,4–14,1% | 96 | 786 |
| DevTools | 9,9% | 7,0–13,4% | 113 | 984 |
| EdTech | 9,7% | 4,9–15,7% | 79 | 656 |
| FinTech | 9,5% | 6,5–12,7% | 112 | 930 |

Acima da média com IC: nenhum · abaixo: nenhum

## País

| nível | churn de receita | IC 95% | contas | assinaturas |
|---|---|---|---|---|
| FR | 17,1% | 3,6–30,2% | 22 | 173 |
| UK | 14,4% | 9,2–20,4% | 58 | 497 |
| DE | 11,5% | 4,4–19,4% | 25 | 176 |
| AU | 10,5% | 4,7–18,6% | 32 | 261 |
| US | 9,7% | 8,0–11,6% | 291 | 2513 |
| CA | 9,1% | 3,0–17,8% | 23 | 178 |
| IN | 6,8% | 2,7–11,9% | 49 | 424 |

Acima da média com IC: nenhum · abaixo: nenhum

## Canal de aquisição

| nível | churn de receita | IC 95% | contas | assinaturas |
|---|---|---|---|---|
| event | 13,6% | 9,3–18,1% | 96 | 777 |
| other | 11,5% | 6,8–16,6% | 103 | 858 |
| organic | 9,5% | 7,0–12,3% | 114 | 1001 |
| ads | 9,0% | 6,0–12,2% | 98 | 838 |
| partner | 8,8% | 5,7–12,2% | 89 | 748 |

Acima da média com IC: nenhum · abaixo: nenhum

## Plano da assinatura

| nível | churn de receita | IC 95% | contas | assinaturas |
|---|---|---|---|---|
| Enterprise | 10,9% | 8,8–13,2% | 468 | 1450 |
| Basic | 9,5% | 7,7–11,5% | 457 | 1356 |
| Pro | 8,6% | 6,9–10,3% | 460 | 1416 |

Acima da média com IC: nenhum · abaixo: Pro

## Cobrança

| nível | churn de receita | IC 95% | contas | assinaturas |
|---|---|---|---|---|
| monthly | 11,0% | 8,8–13,4% | 497 | 2135 |
| annual | 9,8% | 7,6–12,3% | 492 | 2087 |

Acima da média com IC: nenhum · abaixo: nenhum
