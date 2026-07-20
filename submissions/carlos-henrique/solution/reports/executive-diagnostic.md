# Diagnóstico executivo RavenStack

## 1. Executive Summary — resumo executivo

- **A leitura é utilizável com ressalvas:** 39.14% dos 35,586 eventos gerados são analiticamente utilizáveis; a quarentena não entra em comportamento, receita ou jornadas.
- **Os estados de churn dependem fortemente dos warnings:** 325 de 500 contas têm churn observado na população ampliada, mas métricas instáveis não são promovidas como findings.
- **A estrutura de assinaturas exige cautela:** 99.84% dos 5.000 episódios se sobrepõem e episódios abertos permanecem administrativamente censurados.
- **Ação de maior retorno e menor esforço:** corrigir cronologias upstream e validar a semântica de múltiplas assinaturas antes de operacionalizar retenção individual.

## 2. Cobertura e qualidade

Foram usados 10,703 eventos válidos e 3,224 com warning; 21,659 ficaram restritos à saúde dos dados. O indicador mede cobertura do conjunto analítico, não desempenho da RavenStack.

## 3. População

A população principal é `VALID + VALID_WITH_WARNING`; a estrita contém somente `VALID`. Ambas excluem quarentena. A janela vai de 2023-01-02 00:00:00 a 2024-12-31 19:00:00, com granularidade diária, tempo sem timezone e censura administrativa.

## 4. Churn observado

| Estado principal | Contas | Proporção observada |
|---|---:|---:|
| `REACTIVATED_THEN_CHURNED_AGAIN` | 4 | 0.80% |
| `REACTIVATED` | 22 | 4.40% |
| `RECURRING_CHURN` | 118 | 23.60% |
| `SINGLE_CHURN` | 181 | 36.20% |
| `NO_CHURN_OBSERVED` | 175 | 35.00% |

As proporções são observadas entre contas, não taxas temporais de churn.

## 5. Churn recorrente

Há 128 contas com dois ou mais churns utilizáveis. O intervalo mediano entre churns é 61.0 dias entre 167 intervalos observados.

## 6. Reativação

Há 26 contas com reativação explícita utilizável e 30 eventos. 33 de 492 churns observados possuem reativação posterior no horizonte disponível.

## 7. Uso de produto

216 de 500 contas não têm uso nos 30 dias anteriores ao cutoff. Rankings usam somente categorias estruturadas de feature e comparações representam associação descritiva.

## 8. Suporte

Foram observadas 923 aberturas e 928 fechamentos utilizáveis. Satisfação está disponível em 554 fechamentos e ausente em 374.

## 9. Receita associada

O MRR somado nos episódios é 11338747.00; 10159608.00 está associado a episódios abertos. Esses valores não representam automaticamente perda, recuperação ou receita reconhecida.

## 10. Coortes

Foram produzidos 66 grupos por cadastro, primeira assinatura, plano inicial, MRR e uso inicial. 19 grupos têm menos de 20 contas e recebem `SMALL_SAMPLE`.

## 11. Jornadas agregadas

A jornada completa mais frequente, após colapsar duplicatas consecutivas e limitar a 12 passos, foi `ACCOUNT_CREATED → SUBSCRIPTION_STARTED → FEATURE_USED → SUBSCRIPTION_STARTED → FEATURE_USED → SUBSCRIPTION_STARTED → FEATURE_USED → SUBSCRIPTION_STARTED → FEATURE_USED → SUBSCRIPTION_STARTED → FEATURE_USED → SUBSCRIPTION_STARTED`, observada em 8 contas. Trata-se de resumo ordenado, não de mineração formal.

## 12. Situações prioritárias

| Situação | Contas | MRR associado | Prioridade |
|---|---:|---:|---|
| `HIGH_MRR_RECENT_CHURN` | 35 | 1112347.00 | `HIGH` |
| `REACTIVATED_HIGH_VALUE` | 2 | 84064.00 | `HIGH` |
| `RECURRING_CHURN_ACCOUNT` | 128 | 973863.00 | `HIGH` |
| `LOW_USAGE_HIGH_MRR` | 27 | 871159.00 | `MEDIUM` |
| `DATA_QUALITY_REVIEW_REQUIRED` | 374 | 5248582.00 | `HIGH` |

As situações são regras descritivas agregadas, não scores preditivos.

## 13. Findings

- **F001 — A cobertura analítica limita a leitura comportamental.** Menos da metade dos eventos gerados compõe a população analítica utilizável. Confiança `HIGH`; sensibilidade `ROBUST`.
- **F002 — Sobreposição de assinaturas é quase universal no snapshot.** A maioria dos episódios possui ao menos uma sobreposição temporal observada. Confiança `HIGH`; sensibilidade `ROBUST`.
- **F003 — Ausência de uso recente aparece em parte relevante das contas.** Há contas sem eventos de uso nos 30 dias anteriores ao cutoff governado. Confiança `MEDIUM`; sensibilidade `SENSITIVE`.
- **F004 — A satisfação tem cobertura parcial entre fechamentos utilizáveis.** Uma parcela dos fechamentos de suporte utilizáveis não possui satisfação observada. Confiança `MEDIUM`; sensibilidade `ROBUST`.
- **F005 — O MRR de episódios abertos domina o snapshot.** A maior parcela do MRR de episódios está associada a episódios administrativamente censurados. Confiança `HIGH`; sensibilidade `ROBUST`.

## 14. Análise de sensibilidade

Todas as métricas principais foram recalculadas nas populações estrita e ampliada. 4 de 8 métricas numéricas foram classificadas `UNSTABLE`; nenhuma delas sustenta finding principal.

## 15. Limitações

- timestamps diários e ausência de timezone impedem interpretação intradiária;
- censura administrativa e tempos de seguimento desiguais permanecem;
- warnings expandem substancialmente a cobertura de churn e reativação;
- suporte não possui atribuição única a assinatura;
- MRR associado não demonstra perda ou recuperação financeira;
- nenhuma associação aqui demonstra mecanismo explicativo.

## 16. Próximos passos

Preservar populações, cutoffs e censura na Fase 4; investigar qualidade upstream; validar a semântica de sobreposição com billing; e manter revisão humana antes de qualquer ação por conta.

**Fontes internas:** `event_log.parquet`, `subscription_episodes.parquet`, `quarantined_events.parquet` apenas para qualidade, e `ravenstack_support_tickets.csv` apenas para resolução de fechamentos utilizáveis.
