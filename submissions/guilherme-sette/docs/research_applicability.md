# Aplicabilidade da pesquisa de forecast e scoring ao desafio Lead Scorer

Data da analise: 2026-06-23

## Fontes analisadas

- Pesquisa anexada pelo usuario: [`deep-research-report-2.md`](./research_sources/deep-research-report-2.md)
- Pesquisa anexada pelo usuario: [`forecast-pipeline-scoring-preditivo-nao-convencional.pdf`](./research_sources/forecast-pipeline-scoring-preditivo-nao-convencional.pdf)
- README do desafio neste diretorio.
- CSVs processados em `data/processed`.

## Conclusao executiva

A pesquisa e boa como arquitetura mental, mas e grande demais para o dataset e para o escopo do challenge. O nosso desafio nao pede uma plataforma enterprise de forecast; pede uma ferramenta funcional para vendedor e RevOps priorizarem oportunidades reais.

O que deve ser aproveitado agora:

- Separar ranking operacional de probabilidade estatistica.
- Usar scoring explicavel com reason codes.
- Avaliar por captura de valor no topo da lista, nao so por acuracia.
- Tratar dados faltantes como componente de confianca.
- Usar o historico de vendedor por produto, ticket e perfil de empresa como sinal de especialidade, nao como roteamento automatico.

O que nao deve entrar no V1:

- LLM enrichment, porque nao temos notas, calls, emails ou texto de CRM.
- Graph ML, porque nao temos contatos, buying group ou relacionamento multi-stakeholder.
- Uplift/causal, porque nao temos registro de acoes comerciais e tratamentos.
- Foundation forecasting, porque nao temos serie temporal de snapshots nem escopo de forecast corporativo.
- Survival formal, porque temos um snapshot estatico, nao historico de mudanca de estagio ao longo do tempo.

## Estado concreto do nosso universo

Os CSVs processados permitem uma solucao util, mas nao sustentam promessas fortes de ML preditivo.

- Temos 6.711 oportunidades fechadas para aprender padroes historicos.
- A taxa historica de ganho em oportunidades fechadas e 63,15%.
- Temos 2.089 oportunidades abertas para priorizar.
- O valor estimado aberto e US$ 4.966.215.
- O pipeline aberto tem 1.589 oportunidades em `engaging` e 500 em `prospecting`.
- 1.425 oportunidades abertas, ou 68,2%, nao tem conta conhecida.
- Existem 1.693 combinacoes historicas vendedor-segmento analisadas.
- 343 combinacoes aparecem como `strong_fit` ou `possible_fit`.
- O roteamento irrestrito por especialista concentra recomendacoes em apenas 3 vendedores, entao a recomendacao nao deve virar reatribuicao automatica.

## Matriz de aplicabilidade

| Ideia da pesquisa | Aplicabilidade agora | Decisao pratica |
|---|---:|---|
| Ranking / learning-to-rank | Alta | Aplicar como score de prioridade explicavel. Nao precisa LGBMRanker no V1. |
| GBDT calibrado | Media | Usar como challenger futuro. O dataset tem poucos sinais fortes e a ferramenta precisa ser entendida pelo vendedor. |
| Revenue-weighted precision / recall@k | Alta | Usar como metrica principal de validacao offline: quanto valor bom aparece no topo da lista. |
| Lift por decil | Alta | Comparar score V1 contra baseline de ordenar por valor e baseline de ordenar por stage/idade. |
| Brier/calibracao | Media | So usar se o produto mostrar probabilidade. Se mostrar apenas prioridade, nao vender como probabilidade calibrada. |
| Survival / time-to-close | Media-baixa | Adaptar para risco de envelhecimento: idade do deal vs historico de fechamento. Nao chamar de survival model. |
| Forecast probabilistico | Baixa no V1 | Pode virar painel de cenarios, mas nao deve ser promessa central do desafio. |
| Graph ML | Baixa | Nao aplicar agora. Usar joins relacionais simples entre conta, produto, vendedor e oportunidade. |
| LLM sobre CRM nao estruturado | Baixa | Nao aplicar agora. Nao ha texto operacional para extrair champion, objecao ou next step. |
| Uplift / causal policy | Baixa | Nao aplicar agora. Sem historico de intervencao, o modelo confundiria propensao com incrementalidade. |
| Foundation models | Baixa | Descartar no challenge. Complexidade alta e pouca aderencia aos dados disponiveis. |

## Score V1 recomendado

O score deve ser uma prioridade operacional de 0 a 100, nao uma probabilidade de fechamento. Isso evita vender uma precisao que os dados atuais nao sustentam.

Componentes sugeridos:

| Componente | Peso | Como usar |
|---|---:|---|
| Valor economico | 20 | Priorizar deals com maior valor estimado, com escala por ticket para nao deixar produtos caros dominarem tudo so por preco. |
| Fit vendedor-segmento | 25 | Usar historico por produto, ticket, setor, porte e conta quando houver amostra suficiente. |
| Urgencia / envelhecimento | 20 | Comparar `days_open_as_of_snapshot` com o tempo historico de fechamento. Deal muito antigo vira risco, nao prioridade cega. |
| Stage operacional | 10 | `engaging` tende a ter mais acao imediata que `prospecting`, mas deve sofrer penalidade se estiver parado demais. |
| Qualidade da conta / ICP | 10 | Usar setor, receita, funcionarios e idade da conta quando presentes. Se conta faltar, reduzir confianca. |
| Risco de carteira | 10 | Considerar carga aberta, performance historica e possivel desalinhamento entre vendedor atual e especialista. |
| Confianca dos dados | 5 | Penalizar ausencia de conta, ausencia de data de engajamento e segmentos com pouca amostra. |

Saidas minimas para cada oportunidade:

- `priority_score`
- `priority_band`: `alta`, `media`, `baixa`, `revisao`
- `confidence_band`: `alta`, `media`, `baixa`
- `reason_codes`: 3 a 5 motivos legiveis para vendedor
- `recommended_action`: `agir agora`, `revisar com manager`, `consultar especialista`, `nutrir`, `corrigir dados`
- `specialist_signal`: indicar quando existe vendedor historicamente mais aderente, sem sugerir reatribuicao automatica

## Uso correto do fit vendedor vs oportunidade

O fit deve funcionar como uma camada de especialidade, nao como motor de distribuicao cega de leads.

Regra recomendada:

- Manter o dono atual da oportunidade por padrao.
- Sugerir especialista apenas quando o deal tiver valor relevante, o vendedor atual tiver fit fraco e outro vendedor tiver fit forte com amostra suficiente.
- Para deals de alto valor com baixa confianca, gerar `manager_review`.
- Para vendedores novatos ou com pouco historico, reduzir a forca do julgamento historico e destacar que o score esta menos consolidado.

Isso preserva praticidade operacional e evita o problema ja observado: concentrar oportunidades nos mesmos poucos top performers.

## Validacao possivel sem prometer demais

Como nao temos snapshots historicos reais, a validacao deve ser honesta.

Baselines obrigatorios:

- Ordenar por valor estimado.
- Ordenar por stage + idade.
- Ordenar por win rate historico do vendedor.
- Ordenar pelo score V1.

Metricas recomendadas:

- Win rate no top 10%, 20% e 30%.
- Receita ganha capturada no top 10%, 20% e 30%.
- Lift por decil contra o baseline de valor.
- Revenue-weighted precision@k.
- Distribuicao de score por vendedor e manager para detectar concentracao injustificavel.

O melhor teste offline viavel e um pseudo-backtest por `engage_date`: treinar/calibrar regras em oportunidades antigas e avaliar ranking em oportunidades fechadas mais recentes. Isso nao substitui snapshot as-of real, mas e melhor que avaliar tudo misturado.

## Como transformar em produto do desafio

O caminho mais pragmatico e construir um cockpit de priorizacao:

- Tela por vendedor: top oportunidades, motivos, valor, idade, stage, confianca e acao sugerida.
- Tela por manager: carteira por vendedor, concentracao de risco, deals de alto valor desalinhados com fit, oportunidades antigas em `engaging`.
- Filtros por vendedor, manager, regiao, produto, stage e faixa de ticket.
- Export CSV para a rotina comercial.
- Documentacao clara dizendo que o score e uma priorizacao explicavel, nao uma previsao garantida.

## Decisao final

A pesquisa deve influenciar o projeto em tres pontos: camada de ranking, metricas ponderadas por valor e governanca contra leakage/miscalibration. O V1 deve ficar deliberadamente simples, explicavel e executavel.

A solucao mais forte para este challenge nao e "usar o modelo mais avancado"; e mostrar que, com dados imperfeitos, conseguimos orientar melhor a segunda-feira do vendedor sem fingir que temos sinais que o CRM nao fornece.
