# Plano de execução — Challenge 004

**Run:** `20260716-1729-4aed364`
**Owner:** Planner
**Status:** aprovado para execução técnica
**Dataset observado:** `data/raw/social_media_dataset.csv`, 27 colunas, aproximadamente 23,3 MB

## Objetivo decisório

Entregar ao Head de Marketing uma estratégia cross-platform sustentada por evidências sobre: fatores associados a engagement; desempenho ajustado de conteúdo patrocinado; perfis de audiência; iniciativas de baixo desempenho; prioridades, quick wins e política experimental de patrocínio. O dashboard deve transformar métricas aprovadas em monitoramento recorrente. ML só prossegue se oferecer ganho decisório mensurável sobre baseline simples.

## Escopo e perguntas

| ID | Pergunta | Decisão habilitada | Evidência mínima | Owner final |
|---|---|---|---|---|
| Q1 | Quais combinações de plataforma, conteúdo, categoria e faixa de creator associam-se a melhor engagement e alcance? | mix de conteúdo e esforço por canal | distribuição, efeito relativo, `n`, estabilidade temporal e validação ajustada | Analyst + Statistician |
| Q2 | Patrocinado supera orgânico em condições comparáveis? | política de patrocínio e testes de investimento | contraste bruto e ajustado, overlap, efeitos por segmento e sensibilidade | Statistician |
| Q3 | Quais perfis de audiência mais engajam por canal/conteúdo? | segmentação e hipóteses de targeting | composição, efeitos estratificados e suporte amostral | Analyst + Statistician |
| Q4 | O que não funciona? | lista priorizada de ações a parar/reduzir | segmentos abaixo do baseline, estabilidade, incerteza e custo ausente declarado | Strategist |
| Q5 | Que ações começam esta semana e nos próximos 90 dias? | plano operacional | recomendações ligadas a evidence IDs, owner, KPI, guardrail e stop condition | Strategist |
| Q6 | Como acompanhar recorrente? | dashboard operacional | KPIs congelados, filtros, freshness, `n` e reconciliação | Dashboard Builder |
| Q7 | Uma previsão pré-post melhora a decisão? | go/no-go de ML | target/horizonte, features disponíveis, baseline e validação temporal/creator | ML Engineer |

## População, grão e métricas preliminares

- População inicial: todas as linhas válidas do CSV; exclusões só após relatório DQ e regra documentada.
- Unidade de análise: post (`id`/`content_id`), com dependência por `creator_id`.
- Tempo: `post_date`, convertido com timezone/ambiguidade documentados; análises devem verificar drift e sazonalidade.
- Métrica primária proposta: engagement por view, `(likes + shares + comments_count) / views`, somente após reconciliação de `views=0` e definição no metric registry.
- Métricas complementares: views, likes, shares, comments, taxa de share/comment, proporção de zero engagement e alcance relativo ao follower count, quando denominadores forem válidos.
- “ROI” é proibido sem custo/receita. O projeto reportará eficiência ou associação ajustada e recomendará coleta de custos.
- Faixas de creator serão definidas após distribuição; valores contínuos serão preservados nos modelos.

## Comparação patrocinado versus orgânico

1. Diagnóstico descritivo por plataforma, período, categoria, tipo de conteúdo e follower count.
2. Verificação de overlap/suporte e células pequenas.
3. Estimativa ajustada por modelo/regressão, ponderação ou matching escolhido pelo Statistician após diagnósticos.
4. Dependência tratada por erros clusterizados/efeitos por creator quando aplicável.
5. Efeitos e intervalos por segmentos pré-especificados; correção de multiplicidade.
6. Sensibilidade a outliers, definição de engagement, período e especificação.
7. Linguagem observacional; recomendação causal somente como experimento futuro.

## Descoberta e confirmação

- EDA gera records `EXPLORATORY`, incluindo resultados nulos e negativos.
- Statistician valida somente famílias de hipóteses registradas, reportando efeito, intervalo, `n`, pressupostos e FDR/FWER.
- Evidência sem suporte ou instável fica `REJECTED`/`INCONCLUSIVE` e não pode fundamentar política permanente.

## Entregáveis e gates

| Ordem | Gate | Artefato/aceite |
|---:|---|---|
| 1 | P0 | este plano cobre brief, métricas, riscos, gates e go/no-go |
| 2 | DQ | dados processados, contratos, dicionário, lineage, quality report e testes |
| 3 | TECH-FOUNDATION | dependências, comandos, scaffolding, contratos técnicos e testes-base |
| 4 | EDA | tabelas/gráficos reproduzíveis e evidence pack exploratório |
| 5 | INF | findings validados/rejeitados, métodos, diagnósticos e sensibilidades |
| 6 | STR | estratégia priorizada, política de patrocínio, quick wins e stop conditions |
| 7 | ML | condicional; model card e holdout ou `SKIPPED` justificado |
| 8 | UI | dashboard reconciliado e testado |
| 9 | TECH-CONSOLIDATION | integração, execução limpa, CI e testes end-to-end |
| 10 | DOC | relatório executivo fiel aos findings congelados |
| 11 | FINAL | Reviewer com zero BLOCKER/MAJOR |
| 12 | PUBLISH | somente com autorização humana explícita |

## Go/no-go de ML

`GO` apenas se, após INF/STR: existe decisão pré-post recorrente; target e horizonte são válidos; features existem no momento da decisão; volume/suporte permitem split temporal e por creator; e o ganho mínimo sobre baseline é definido. Caso contrário, registrar `ML=SKIPPED` com justificativa. O dashboard permanece obrigatório.

## Riscos prioritários e controles

- Dataset possivelmente sintético ou com URLs/textos artificiais: Data Engineer deve verificar documentação, padrões e declarar validade externa.
- Engagement rate não fornecido no schema observado: definir e reconciliar fórmula, sem fingir que veio da fonte.
- Custo implícito ausente: não alegar ROI.
- Seleção/sobrevivência e posts removidos: limitar população à cobertura observada.
- Dependência por creator, leakage e tempo: splits/erros apropriados.
- Simpson, confundimento e overlap: comparar agregado/estratos e bloquear extrapolação.
- Outliers, zeros, missingness e duplicidade: quantificar e executar sensibilidades.
- Audiência é categórica/agregada: evitar inferência individual e falácia ecológica.
- Hashtags/textos geram alta multiplicidade: exploração separada e validação temporal/FDR.
- Respostas de IA interrompidas: qualquer etapa truncada vira `INCOMPLETE`; validar artefatos antes do gate.

## Aprovações humanas

Antes de política final: confirmar objetivo e métrica primária; aprovar exclusões ambíguas; validar restrições/orçamento; decidir ML após diagnóstico; aprovar recomendações; autorizar publicação. A falta de resposta não equivale a aprovação.

## Definição de pronto do P0

- [x] Todas as entregas obrigatórias e o process log estão cobertos.
- [x] Perguntas ligam-se a decisões, evidências e owners.
- [x] Unidade, métricas preliminares, confundidores e multiplicidade estão previstos.
- [x] Patrocínio exige comparação ajustada e não promete ROI/causalidade.
- [x] ML possui regra go/no-go; dashboard está no fluxo.
- [x] Gates técnicos, analíticos, revisão e autorização humana estão definidos.
