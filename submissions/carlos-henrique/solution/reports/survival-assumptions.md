# Pressupostos da análise de sobrevivência

## Classificação formal

- `ACCOUNT_LEVEL_APPROXIMATE_INDEPENDENCE` — **ACCEPTABLE**: A unidade principal contém uma linha por conta; episódios correlacionados não são tratados como unidades independentes.
- `NON_INFORMATIVE_CENSORING` — **LIMITED**: A censura é administrativa e explícita, mas o mecanismo de saída da observação não pode ser testado com as fontes disponíveis.
- `PROPORTIONAL_HAZARDS` — **NOT_TESTED**: Cox não foi executado; nenhuma suposição de proporcionalidade foi promovida.
- `SAMPLE_SIZE` — **ACCEPTABLE**: População principal n=500 e 325 primeiros churns observados.
- `TAIL_SUPPORT` — **ACCEPTABLE**: Em 540 dias permanecem 31 contas em risco; mínimo configurado=20.
- `COLLINEARITY` — **NOT_TESTED**: Nenhum modelo multivariado foi ajustado.
- `SMALL_GROUPS` — **LIMITED**: Comparações exigem n≥20 e ao menos 5 eventos por grupo; demais grupos são registrados e omitidos dos testes.
- `MISSINGNESS` — **LIMITED**: Satisfação e resolução de suporte são esparsas; ausências permanecem nulas e não são imputadas.
- `SUBSCRIPTION_OVERLAP` — **VIOLATED**: 99,84% dos episódios se sobrepõem; curvas por assinatura não foram executadas.
- `WARNING_INFLUENCE` — **VIOLATED**: Sobrevivência em 180 dias entre principal e estrita foi classificada como UNSTABLE.

## Decisão sobre Cox

Status `NOT_EXECUTED`. Warning-sensitive endpoints and untested proportional hazards prevent a stable, leakage-controlled descriptive model in this phase. Riscos proporcionais permanecem `NOT_TESTED`, portanto não há modelo a promover.

## Decisão sobre assinaturas

Curvas por assinatura não foram executadas: 99,84% dos episódios se sobrepõem, término não equivale necessariamente a churn e episódios da mesma conta não são independentes.
