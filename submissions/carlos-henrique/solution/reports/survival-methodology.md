# Metodologia de sobrevivência

## Definições

- **Unidade:** conta, uma linha por `account_id` no Parquet operacional local.
- **Origem principal:** primeira assinatura utilizável; **alternativa:** signup utilizável.
- **Endpoint:** primeiro churn utilizável em ou após a origem.
- **Censura:** direita, administrativa, em `2024-12-31T19:00:00`.

## Fórmulas conceituais

Kaplan–Meier multiplica, em cada tempo de evento, `1 - dᵢ/nᵢ`; o intervalo de 95% usa variância de Greenwood e limites truncados em `[0,1]`. Nelson–Aalen soma `dᵢ/nᵢ`. RMST integra a função de sobrevivência até τ. O log-rank compara eventos observados e esperados sob igualdade das curvas; p-values pairwise recebem Benjamini–Hochberg.

## Origem temporal, exclusões e grupos

Duração negativa, origem ausente ou origem posterior ao fim administrativo são excluídas com código. Duração zero é preservada como `SAME_DAY_EVENT`. Grupos ordinários usam atributos de baseline (`first_plan`, MRR inicial, quantidade e sobreposição no baseline, qualidade). Uso e suporte são analisados apenas em janelas landmark fixas, evitando tempo imortal no agrupamento comum.

## Landmarks

Nos marcos de 30, 60 e 90 dias entram apenas contas elegíveis, observáveis até o marco e sem churn até ou no marco. Features consideram exclusivamente eventos entre exposição e marco; a duração posterior inicia no próprio marco. Exclusões e denominadores reconciliam exatamente.

## Log-rank, RMST e Cox

Log-rank exige pelo menos 20 contas e 5 eventos por grupo. RMST usa 90/180/365 dias e é diferença observada, não causal. Cox foi `NOT_EXECUTED` porque warning-sensitive endpoints and untested proportional hazards prevent a stable, leakage-controlled descriptive model in this phase.

## Pressupostos

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

## Contrato visual

As seis figuras são PNGs estáticos reproduzíveis. Perguntas: forma geral e incerteza; influência da qualidade; diferença por plano inicial; risco acumulado; sobrevivência condicional nos landmarks; RMST por horizonte. Linhas, tracejados e rótulos complementam uma paleta azul/laranja/oliva/rosa; nenhum ID ou PII aparece. QA final ocorre nos PNGs exportados.

## Uso permitido

Descrição agregada de tempo até primeiro churn, suporte temporal, censura, diferenças exploratórias e sensibilidade.

## Uso proibido

Probabilidade individual, score, ranking, causalidade, previsão, taxa empresarial generalizável, ação automatizada ou curva independente por assinatura.

## Ambiente reproduzível

pandas 3.0.3, numpy 2.5.1, scipy 1.18.0, matplotlib 3.11.1, pyarrow 25.0.0, pytest 9.1.1.
