# Registro de estratégia

## Tese executiva

Este dataset não sustenta uma estratégia de “apostar nos vencedores”. As diferenças entre plataforma, formato, creator size e audiência são pequenas, o modelo explica menos de 0,1% do engagement e patrocínio não apresenta ganho ajustado em engagement, views, share rate ou alcance relativo. A decisão defensável é parar patrocínio indiscriminado, melhorar instrumentação e executar experimentos controlados antes de realocar orçamento.

## Decisões priorizadas

### STR-001 — Suspender expansão de patrocínio não experimental

- Prioridade: P0, imediata.
- Evidência: `INF-SPON-001`, `EDA-SPON-001`.
- Ação: novos patrocínios só entram como piloto controlado com custo, objetivo, hipótese, comparação e stop condition.
- Motivo: efeito ajustado −0,0010 p.p.; IC95% −0,0095 a +0,0074 p.p.; nenhuma melhora de views.
- KPI: efeito incremental em métrica aprovada e custo por resultado incremental.
- Guardrail: brand safety, frequência, qualidade da audiência e tamanho amostral.
- Stop condition: interromper se o IC indicar que o ganho não alcança o break-even definido pelo negócio.
- Owner sugerido: Head de Marketing + Performance Marketing.
- Limite: break-even não pode ser calculado até custos/receita serem coletados.

### STR-002 — Não realocar esforço entre plataformas por este ranking

- Prioridade: P0.
- Evidência: `EDA-PLAT-001` e relatório INF.
- Ação: manter presença necessária por objetivo de canal; decidir realocação somente após experimento ou dados operacionais reais.
- Motivo: amplitude bruta de plataforma 0,0105 p.p.; coeficientes ajustados incluem zero.
- KPI: incremental reach/engagement/conversão por hora e por real investido.
- Stop condition: nenhuma mudança estrutural até haver efeito material replicado.
- Owner: Social Media Lead.

### STR-003 — Substituir “formato vencedor” por backlog experimental

- Prioridade: P1, esta semana.
- Evidência: `EDA-CONTENT-001`, `EDA-COMBO-001`.
- Ação: planejar células plataforma×formato×categoria com hipótese e replicação, evitando rankings de top posts.
- Motivo: amplitude de formato 0,0121 p.p.; combinações extremas têm células pequenas e multiplicidade.
- KPI: efeito dentro de plataforma e audiência, com intervalo e taxa de replicação.
- Guardrail: volume mínimo por célula e FDR para exploração em escala.
- Stop condition: arquivar hipótese após duas rodadas sem efeito material pré-definido.
- Owner: Content Lead + Analytics.

### STR-004 — Implantar instrumentação mínima de campanha

- Prioridade: P0, esta semana.
- Evidência: DQ-003 e `INF-SPON-001`.
- Ação: coletar `campaign_id`, custo total, fee de creator, mídia, produção, objetivo, CTA, impressões/reach únicos, cliques, conversões, receita/margem, janela de atribuição e grupo de comparação.
- KPI: cobertura e completude ≥95%; reconciliação financeira; latência de atualização.
- Stop condition: campanha sem campos mínimos não entra em avaliação de ROI.
- Owner: Marketing Ops + Data Engineering.

### STR-005 — Tratar audiência como hipótese, não targeting validado

- Prioridade: P1.
- Evidência: `EDA-AUD-001`.
- Ação: testar mensagens por segmento em desenho controlado; não usar a categoria agregada do post para inferir comportamento individual.
- KPI: efeito por segmento com tamanho amostral e intervalo.
- Guardrail: privacidade, consentimento e não discriminação.
- Owner: Audience/CRM + Analytics.

### STR-006 — Definir frequência por teste, não pelo arquivo histórico

- Prioridade: P1.
- Evidência: limitação do contrato fonte.
- Ação: testar cadências dentro de plataforma mantendo conteúdo/creator comparáveis; capturar frequência e saturação.
- KPI: alcance incremental, engagement incremental por post, unfollow/hide e custo operacional.
- Stop condition: aumentar frequência só enquanto o ganho marginal superar custo e guardrails.
- Limite: o dataset não contém frequência planejada/exposição individual; nenhuma cadência numérica é defensável hoje.

## Política de patrocínio proposta

1. Não existe threshold de seguidores validado; follower count não mostrou relação útil com engagement.
2. Patrocínio requer hipótese, segmento, custo completo, outcome e comparação antes da aprovação.
3. Preferir randomização; quando inviável, usar rollout escalonado ou matching pré-registrado.
4. Começar pequeno e escalonar somente após efeito material replicado e break-even financeiro.
5. Não contratar por engagement histórico isolado; auditar qualidade da audiência, fraude, brand fit e estabilidade.
6. Sem custo e receita, classificar resultado como performance/eficiência observada, nunca ROI.

## Quick wins — próxima semana

| Ordem | Ação | Evidência de conclusão |
|---:|---|---|
| 1 | congelar expansão de campanhas sem mensuração | checklist de aprovação ativo |
| 2 | adicionar campos mínimos de custo/conversão | contrato e cobertura inicial |
| 3 | criar backlog de 3 hipóteses testáveis | hipótese, métrica, MDE e stop condition |
| 4 | publicar dashboard descritivo com alertas de limitação | KPIs reconciliados e `n` visível |
| 5 | revisar 90 dias de patrocínios com custos reais | tabela campanha→custo→outcome→comparador |

## O que parar

- rankings de médias sem incerteza e suporte;
- declarar vídeo/plataforma/creator size vencedor;
- avaliar patrocínio por engagement isolado;
- usar top performers como prova causal;
- definir frequência a partir deste arquivo;
- segmentar indivíduos por categoria agregada de audiência;
- chamar qualquer resultado atual de ROI.

## Roadmap de 90 dias

- 0–14 dias: instrumentação, metric registry aprovado e dashboard descritivo.
- 15–45 dias: pilotos randomizados/rollout por plataforma com custos e conversões.
- 46–75 dias: replicação dos efeitos e análise por segmento pré-especificado.
- 76–90 dias: política de escala baseada em break-even; reconsiderar ML somente com sinal real e decisão pré-post.

## Decisão de ML

`NO-GO / SKIPPED`. O modelo ajustado atual tem R² 0,000899 e as variáveis não contêm sinal decisório relevante. Treinar um preditor sofisticado provavelmente modelaria ruído do processo sintético. Reabrir o gate após coleta de dados reais, definição de target/horizonte e baseline, com ganho mínimo acordado.

## Aprovação humana necessária

O Head de Marketing deve aprovar métrica primária, MDE/threshold material, break-even, orçamento de pilotos, guardrails e política final. Este registro recomenda decisões; não executa gasto nem publicação.
