# Relatório de quarentena temporal — Fase 2

## Total

Eventos em quarentena: **21659** de 35586 (60.86%).

## Por fonte

- `churn_events`: 78 (0.22% dos eventos gerados);
- `feature_usage`: 19432 (54.61% dos eventos gerados);
- `support_tickets`: 2149 (6.04% dos eventos gerados);

## Motivos

- `AMBIGUOUS_CHURN_SUBSCRIPTION`: 22;
- `CHURN_BEFORE_FIRST_SUBSCRIPTION`: 53;
- `CHURN_WITHOUT_ACTIVE_SUBSCRIPTION`: 53;
- `DUPLICATE_CANDIDATE_KEY`: 6;
- `DUPLICATE_SOURCE_ID`: 28;
- `MULTIPLE_ACTIVE_SUBSCRIPTIONS`: 22;
- `POST_SUBSCRIPTION_USAGE`: 290;
- `PRE_ACCOUNT_EVENT`: 15347;
- `PRE_SUBSCRIPTION_USAGE`: 19142;
- `REACTIVATION_WITHOUT_PRIOR_CHURN`: 31;
- `SAME_DAY_ORDER_ASSIGNED`: 2547;

Um evento pode possuir mais de um motivo; por isso a soma das flags não representa eventos únicos.

## Impacto

A quarentena reduz a cobertura analítica, principalmente de uso e suporte, mas impede que cronologias impossíveis contaminem sequências, features as-of e conclusões futuras.

## Possibilidade de recuperação

- eventos pré/pós-assinatura exigem correção ou explicação da fonte e não podem ser reativados por conveniência;
- eventos pré-conta exigem reconciliação de calendários ou identidade;
- churn anterior à primeira assinatura exige definição de produto ou correção upstream;
- IDs/timestamps inválidos exigem reparo rastreável na origem;
- duplicatas distintas permanecem no log ativo com warning e não dependem de recuperação.

## Recomendação futura

Manter a quarentena imutável por build, monitorar taxas por regra e somente promover registros mediante evidência upstream versionada. Nenhum ID completo, nome ou texto livre é listado neste relatório.
