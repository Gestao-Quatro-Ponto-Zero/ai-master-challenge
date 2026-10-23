# Diagnóstico de churn — evidências

Gerado por `analysis/diagnostico.py` a partir do silver (Supabase G4-Analysys). Churn = `churn_events`; MRR vigente = assinatura ativa mais recente; seed 42.
## H0 — O churn subiu? (denominador importa)

| q      |   eventos |   mrr_perdido |   repetidos_2o+ |   contas_cadastradas |   assinaturas_ativas |   churn_por_100_contas |   churn_por_100_assinaturas |
|:-------|----------:|--------------:|----------------:|---------------------:|---------------------:|-----------------------:|----------------------------:|
| 2023Q1 |         6 |          2768 |               0 |                   55 |                   31 |                   10.9 |                        19.4 |
| 2023Q2 |        11 |         15741 |               1 |                  109 |                  135 |                   10.1 |                         8.1 |
| 2023Q3 |        19 |         24669 |               3 |                  162 |                  336 |                   11.7 |                         5.7 |
| 2023Q4 |        37 |         73802 |               5 |                  227 |                  648 |                   16.3 |                         5.7 |
| 2024Q1 |        54 |         89978 |              14 |                  283 |                 1093 |                   19.1 |                         4.9 |
| 2024Q2 |        92 |        188929 |              36 |                  348 |                 1742 |                   26.4 |                         5.3 |
| 2024Q3 |       130 |        293187 |              50 |                  420 |                 2769 |                   31   |                         4.7 |
| 2024Q4 |       251 |        536680 |             139 |                  500 |                 4514 |                   50.2 |                         5.6 |

Eventos sobem 6 → 251 por trimestre. Por conta cadastrada, a taxa sobe; por assinatura ativa, fica estável (~5%/tri desde 2023Q3) — as contas acumulam assinaturas. O CEO está certo sobre logos; a pergunta é *quem* está saindo (H8).

## H5 — Nem todo churn pesa igual

| plan       |   eventos |   mrr_perdido |   pct_eventos |   pct_mrr |
|:-----------|----------:|--------------:|--------------:|----------:|
| Basic      |       168 |         74898 |         0.307 | 0.0611036 |
| Enterprise |       198 |        938882 |         0.362 | 0.765963  |
| Pro        |       181 |        211974 |         0.331 | 0.172934  |

MRR perdido somado nos eventos: US$ 1,225,754. Os 10% maiores eventos (54) concentram **43%** do MRR perdido. Enterprise é 36% dos eventos e **77%** do MRR perdido. 53 eventos não têm assinatura anterior à data do churn (dado inconsistente; fora da soma).

## H1 — A satisfação está mascarada?

| grupo            |   tickets |   csat |   taxa_resposta |   pct_escalado |   frt_mediano |
|:-----------------|----------:|-------:|----------------:|---------------:|--------------:|
| churnou          |     3.963 |  3.962 |           0.597 |          0.049 |        88.431 |
| nunca churnou    |     4.088 |  3.97  |           0.606 |          0.045 |        87.031 |
| p (Mann-Whitney) |     0.625 |  0.828 |           0.535 |          0.241 |         0.67  |

|   satisfaction_score |   tickets |
|---------------------:|----------:|
|                  nan |       825 |
|                    4 |       405 |
|                    3 |       396 |
|                    5 |       374 |

Quem churna e quem fica têm **o mesmo CSAT** (3.96 × 3.97) e o mesmo suporte (nenhum p < 0,05). A nota só vai de 3 a 5 (nenhuma nota 1 ou 2) e 41% dos tickets não têm nota. **58% dos churns não abriram nenhum ticket nos 90 dias anteriores.** Conclusão: o CSAT não é falso — ele é *cego*: não separa quem vai sair.

## H2/H3 — O uso cresceu? Erros e beta antecedem o churn?

| q      |   eventos_de_uso |   contas_com_uso |   erros |   contas_cadastradas |   uso_por_conta_com_uso |   taxa_de_erro |
|:-------|-----------------:|-----------------:|--------:|---------------------:|------------------------:|---------------:|
| 2023Q1 |            31400 |              497 |    1795 |                   55 |                   63.18 |           0.06 |
| 2023Q2 |            31128 |              498 |    1869 |                  109 |                   62.51 |           0.06 |
| 2023Q3 |            31155 |              494 |    1698 |                  162 |                   63.07 |           0.05 |
| 2023Q4 |            30878 |              495 |    1729 |                  227 |                   62.38 |           0.06 |
| 2024Q1 |            31593 |              491 |    1802 |                  283 |                   64.34 |           0.06 |
| 2024Q2 |            30789 |              498 |    1757 |                  348 |                   61.83 |           0.06 |
| 2024Q3 |            31355 |              495 |    1775 |                  420 |                   63.34 |           0.06 |
| 2024Q4 |            32227 |              497 |    1682 |                  500 |                   64.84 |           0.05 |

| quartil_erro   |   contas |   churns_por_conta |
|:---------------|---------:|-------------------:|
| Q1 menos erro  |      125 |              1.056 |
| Q2             |      125 |              1.256 |
| Q3             |      125 |              1.288 |
| Q4 mais erro   |      125 |              1.2   |

O uso total é **plano** (~31 mil eventos/tri) e o uso por conta também (~63). Não há crescimento — nem queda — em nenhum plano ou indústria. Pior: 53% do uso tem data **anterior ao cadastro** da conta e ~500 contas aparecem usando desde 2023Q1, quando só 55 existiam: o log de uso não está ancorado no tempo. Uso nos 90 dias antes do churn × controle na mesma data: p = 0.21. Erros × churn: Spearman ρ = 0.05 (p = 0.23), sem dose-resposta. Conclusão: a afirmação "o uso cresceu" não se sustenta, e o dado de uso não serve hoje como sinal de churn.

## H4 — O motivo declarado explica o churn?

| reason_code   |   eventos |   mrr_mediano |   refund_medio |   downgrade_90d |
|:--------------|----------:|--------------:|---------------:|----------------:|
| budget        |       104 |         931   |          12    |            0.06 |
| competitor    |        92 |        1225   |          13.08 |            0.13 |
| features      |       114 |         796   |          16.72 |            0.08 |
| pricing       |        91 |         741   |          14.65 |            0.04 |
| support       |       104 |         987.5 |          11.73 |            0.12 |
| unknown       |        95 |         995   |          18.34 |            0.09 |

Motivos quase uniformes (91–114 cada), sem mudança ao longo do tempo (χ² p = 0.62) e com comportamento parecido. `feedback_text` tem só 4 textos distintos. O motivo declarado **não discrimina nada** — é campo de formulário, não diagnóstico.

## H6 — Algum segmento de cadastro churna mais?

Churns por 100 contas-mês de exposição; teste χ² contra a exposição.

| segmento        |     p | maior             | menor             | significativo após Bonferroni (p<0,0083)   |
|:----------------|------:|:------------------|:------------------|:-------------------------------------------|
| referral_source | 0.025 | organic (13.0)    | ads (8.5)         | False                                      |
| industry        | 0.586 | EdTech (12.3)     | HealthTech (10.0) | False                                      |
| country         | 0.212 | FR (12.8)         | DE (7.9)          | False                                      |
| plan_tier       | 0.684 | Enterprise (11.1) | Basic (10.2)      | False                                      |
| is_trial        | 0.164 | False (11.1)      | True (9.6)        | False                                      |
| faixa_licencas  | 0.336 | Q4 (11.4)         | Q3 (9.4)          | False                                      |

Nenhum segmento de cadastro (canal, indústria, país, plano inicial, trial, licenças) sobrevive à correção para múltiplas comparações. `organic` aparece mais alto (p = 0,025), mas é o tipo de "achado" que some com 6 testes: não vamos recomendar ação por canal.

## H7 — Mudança de plano antecede o churn?

Nos eventos de churn: downgrade nos 90 dias anteriores = 8.8%, upgrade = 20.5%. Base das assinaturas: downgrade = 4.4%, upgrade = 10.6%. As duas taxas dobram — qualquer mudança de plano, não só downgrade. Unidades diferentes (janela de 90 dias × flag da assinatura): **indício fraco**, não causa.

## H8 — Quem está saindo: contas novas e contas que já saíram antes

Churns por 100 contas-mês, por trimestre do calendário × tempo de casa:

| cal_q   |   0-3m |   3-6m |   6-12m |   12m+ |
|:--------|-------:|-------:|--------:|-------:|
| 2023Q1  |    5.6 |  nan   |   nan   |  nan   |
| 2023Q2  |    2.4 |    6.5 |   nan   |  nan   |
| 2023Q3  |    2.7 |    6.5 |     3.7 |  nan   |
| 2023Q4  |    6.8 |    4.7 |     6.2 |  nan   |
| 2024Q1  |    8.4 |   10.9 |     5.7 |    0.9 |
| 2024Q2  |   14.1 |    9   |     9.7 |    5.8 |
| 2024Q3  |   18.7 |   14.1 |     9.5 |    6.8 |
| 2024Q4  |   46.5 |   21.1 |    11.5 |    8.3 |

Modelo de Poisson (conta-mês) com trimestre do calendário, tempo de casa e churn anterior:

|                    |   rate ratio |     p |
|:-------------------|-------------:|------:|
| C(cal_q)[T.2023Q2] |        0.81  | 0.678 |
| C(cal_q)[T.2023Q3] |        1.074 | 0.879 |
| C(cal_q)[T.2023Q4] |        1.564 | 0.312 |
| C(cal_q)[T.2024Q1] |        2.046 | 0.099 |
| C(cal_q)[T.2024Q2] |        3.058 | 0.009 |
| C(cal_q)[T.2024Q3] |        3.8   | 0.002 |
| C(cal_q)[T.2024Q4] |        6.418 | 0     |
| C(ten_b)[T.3-6m]   |        0.713 | 0.003 |
| C(ten_b)[T.6-12m]  |        0.476 | 0     |
| C(ten_b)[T.12m+]   |        0.282 | 0     |
| prior_churn        |        0.877 | 0.168 |

Coortes (contas com ≥ 6 meses de observação), % com churn nos primeiros 6 meses:

| coorte   |   contas |   churn_6m |
|:---------|---------:|-----------:|
| 2023H1   |      109 |      0.266 |
| 2023H2   |      118 |      0.415 |
| 2024H1   |      121 |      0.62  |

Logit controlando canal, plano inicial, indústria, trial e licenças: coorte 2024 tem **3.3×** a chance de churnar em 6 meses (IC 95% 2.0–5.3, p = 9e-07). Nenhum outro controle é significativo — o mix de cadastro **não mudou**; o que mudou foi o resultado das contas novas.

| tipo               |   eventos |    mrr |   pct_eventos |   pct_mrr |
|:-------------------|----------:|-------:|--------------:|----------:|
| 1º churn < 3 meses |       188 | 303081 |         0.313 |  0.247261 |
| 1º churn ≥ 3 meses |       164 | 346591 |         0.273 |  0.282757 |
| repetido (2º+)     |       248 | 576082 |         0.413 |  0.469982 |

Leitura causal: tempo de casa precede o churn ✅, dose-resposta monotônica ✅, se mantém com controles ✅; alternativa "choque de calendário que atinge todos" — existe (rate ratio sobe por trimestre), mas a base antiga sobe ~1,5× enquanto as contas de 0–3 meses sobem ~8×. Contas que já churnaram antes **não** têm risco maior (rate ratio 0.88, p = 0.17): elas pesam porque voltam e saem de novo, não porque sejam piores. O **mecanismo** (onboarding, ativação, qualificação de venda) não está nos dados: é hipótese a validar com experimento.

## Contas em risco (lista de ação)

432 contas ativas em 31/12/2024, MRR vigente US$ 1,060,987. Probabilidade de churn em 90 dias pelo modelo de H8 (tempo de casa + churn anterior, taxas de 2024Q4); MRR em risco esperado: **US$ 334,121**. As 20 primeiras concentram 35% do risco. Lista completa em `analysis/results/risk_accounts.csv`.

| account_id   | account_name   | industry      | plan       | billing   |   mrr |   tenure_meses |   churns_anteriores |   prob_churn_90d |   mrr_em_risco_90d |
|:-------------|:---------------|:--------------|:-----------|:----------|------:|---------------:|--------------------:|-----------------:|-------------------:|
| A-c70870     | Company_253    | Cybersecurity | Enterprise | monthly   | 33830 |              3 |                   1 |             0.48 |           16226.8  |
| A-d4e0d4     | Company_403    | FinTech       | Enterprise | annual    | 23283 |              3 |                   0 |             0.45 |           10582.1  |
| A-ce550d     | Company_4      | HealthTech    | Enterprise | monthly   | 21691 |              3 |                   1 |             0.48 |           10404.2  |
| A-56962b     | Company_177    | EdTech        | Enterprise | monthly   | 32437 |              9 |                   2 |             0.3  |            9682.36 |
| A-09316c     | Company_341    | FinTech       | Enterprise | annual    | 13930 |              4 |                   1 |             0.48 |            6681.61 |
| A-39ddf4     | Company_435    | EdTech        | Enterprise | monthly   |  7960 |              1 |                   1 |             0.77 |            6149.19 |
| A-9174e0     | Company_73     | Cybersecurity | Enterprise | annual    |  7363 |              1 |                   0 |             0.75 |            5498.81 |
| A-5c046d     | Company_130    | EdTech        | Enterprise | annual    | 18507 |              6 |                   0 |             0.28 |            5187.33 |
| A-c37601     | Company_48     | EdTech        | Enterprise | monthly   | 10746 |              3 |                   1 |             0.48 |            5154.39 |
| A-d26ab4     | Company_497    | DevTools      | Enterprise | monthly   |  6567 |              2 |                   1 |             0.77 |            5073.08 |
| A-1f0636     | Company_368    | EdTech        | Enterprise | annual    | 20895 |             12 |                   0 |             0.21 |            4391.91 |
| A-0f6450     | Company_400    | FinTech       | Enterprise | monthly   |  5572 |              1 |                   2 |             0.77 |            4304.43 |
| A-c58f49     | Company_480    | EdTech        | Enterprise | annual    | 13930 |              6 |                   3 |             0.3  |            4158.07 |
| A-e4144b     | Company_316    | EdTech        | Enterprise | annual    |  8159 |              3 |                   0 |             0.45 |            3708.26 |
| A-410e86     | Company_210    | FinTech       | Enterprise | monthly   |  4776 |              2 |                   0 |             0.75 |            3566.8  |
