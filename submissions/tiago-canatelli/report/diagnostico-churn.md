# RavenStack — Por que estamos perdendo clientes

*Para: CEO · Dados até 31/12/2024 · Fonte: lake no Supabase (5 tabelas cruzadas) · Evidências completas em `analysis/results/diagnostico.md`*

## Em uma frase

**O churn subiu porque as contas novas estão falhando nos primeiros 90 dias, e cada coorte de 2024 falha mais rápido que a anterior. Os indicadores que CS e Produto acompanham não conseguem enxergar isso.**

## O que está acontecendo

| | Número | O que significa |
|---|---|---|
| Churns por trimestre | 37 (4º tri 2023) → **251** (4º tri 2024) | O churn subiu de verdade, e não por efeito de base |
| Contas com até 3 meses × contas com 12+ meses | **46,5 × 8,3** churns por 100 contas-mês (4º tri 2024) | Contas novas saem 5,6× mais |
| Churn nos primeiros 6 meses, por coorte | 27% (1º sem. 2023) → **62%** (1º sem. 2024) | Com canal, plano, indústria, trial e licenças controlados, a coorte 2024 tem **3,3×** a chance de sair (IC 2,0–5,3) |
| Quem entra | Mesmo mix de canal, plano e indústria em 2023 e 2024 | O problema não é *quem* vendemos, é o *que acontece depois* da venda |

## Por que "satisfação ok" e "uso cresceu" convivem com o churn em alta

- **A satisfação não está ok: o termômetro é que não mede.** O CSAT é 3,98 tanto para quem sai quanto para quem fica. Notas 1 e 2 **nunca aparecem** em 2.000 tickets, e 41% dos tickets ficam sem nota. Além disso, **58% dos clientes que cancelam não abrem nenhum ticket** nos 90 dias anteriores, ou seja, saem em silêncio.
- **O uso não cresceu: ficou estável.** São cerca de 63 eventos por conta por trimestre, em todos os planos e indústrias. E 53% dos registros de uso têm data **anterior ao cadastro** da conta, então esse dado hoje não permite afirmar tendência nenhuma.

## Onde está o dinheiro

- **Enterprise é 36% dos cancelamentos, mas 77% do MRR perdido.** Os 10% maiores cancelamentos concentram 43% da perda.
- **Hoje:** 432 contas ativas, com US$ 1,06 mi de MRR. Estimamos **US$ 333 mil em risco nos próximos 90 dias**, e as 20 primeiras contas da fila concentram 35% desse valor.
- **Personas que mais concentram risco:** *Em retração* (31% do risco), *Reincidente* (28%) e *Âncora Enterprise* (11%). *Recém-chegado* tem a maior probabilidade de sair (42%).

## O que fazer (ordem de prioridade)

O impacto é estimado em 3 cenários de salvamento: 10%, 20% e 30% do MRR em risco do público-alvo, calculado em `api.risk_queue`. São premissas, que o primeiro experimento vai calibrar. Os públicos se sobrepõem, então **os impactos não se somam**. O total em risco é US$ 333 mil.

| # | Ação | Público | Dono | Métrica | Impacto em 90 dias |
|---|---|---|---|---|---|
| 1 | **Programa de onboarding dos primeiros 90 dias** com marcos de ativação e CS dedicado | 129 contas ativas com menos de 6 meses | CS + Produto | Churn em 3 e 6 meses da coorte | US$ 15–46 mil (sobre US$ 155 mil em risco) |
| 2 | **Fila semanal do CS por MRR em risco** (painel "Contas em risco"), com ligação proativa e sem esperar ticket | Top 50 da fila | CS | % da fila contatada em 7 dias; churn da fila × controle | US$ 19–56 mil (sobre US$ 185 mil) |
| 3 | **Plano de renovação Enterprise:** QBR e revisão 90 dias antes da renovação | 95 contas Enterprise (anual âncora + mensal) | CS / Executivo | GRR Enterprise | US$ 17–51 mil (sobre US$ 168 mil) |
| 4 | **Consertar os instrumentos:** CSAT 1–5 de verdade + pergunta de intenção de renovação; log de uso ligado à assinatura e à data | Toda a base | Suporte + Dados | Taxa de resposta; uso válido em % | Habilita alertas antecipados; sem $ direto |
| 5 | **Validar com experimento:** sortear metade das contas novas para o onboarding (1) | Coortes a partir de jan/2025 | Dados | Diferença de churn em 90 dias | Transforma o indício em causa comprovada |

## O que é certeza, o que é indício e o que é hipótese

- **Certeza (nos dados):** o churn se concentra nos primeiros meses, e a coorte 2024 é pior. Isso se mantém com controles, segue o tempo de casa de forma consistente e vem antes do churn.
- **Indício forte:** como o mix de clientes não mudou, a causa está depois da venda (onboarding, ativação ou expectativa vendida).
- **Hipótese a testar:** *qual* desses mecanismos. Os dados não têm eventos de onboarding, e por isso a ação 5 existe.
- **O que os dados descartam como causa:** suporte, erros e features beta, uso, motivo declarado (os 6 motivos aparecem em proporções quase iguais), canal, indústria, país, plano inicial, trial e licenças.

## Ressalvas

Os dados são **sintéticos** (Kaggle, River @ Rivalytics) e têm inconsistências documentadas:
- churn e assinaturas não se cruzam: só 6 de 600 churns coincidem com o fim de uma assinatura;
- 87% dos churns são seguidos de uma nova assinatura em cerca de 16 dias;
- `churn_flag` contradiz os eventos de churn.

Por isso, os KPIs de **receita** (GRR/NRR) são aproximados, e as conclusões se apoiam em **contagem de churns e tempo de casa**, que não dependem dessas inconsistências.
