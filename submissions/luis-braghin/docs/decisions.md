# Registro de Decisões

> Decisões de design tomadas durante o desenvolvimento do G4 Deal Intelligence.
> Cada registro documenta o contexto, as opções consideradas e quem decidiu.

---

## Decisão 01 — Deal Value no Score

| Campo | Detalhe |
|-------|---------|
| **Contexto** | A IA propôs que o valor do deal não deveria compor o score de prioridade, argumentando que valor alto não significa maior probabilidade de fechamento. O candidato divergiu. |
| **Opções consideradas** | (A) Excluir valor do score. (B) Incluir valor como dimensão com peso próprio. |
| **Decisão** | Incluir Deal Value como dimensão (20% Engaging, 20% Prospecting). |
| **Justificativa** | A prioridade comercial não é apenas probabilidade — é **Esperança Matemática**: E(X) = P × V. Um deal de R$26.768 com 40% de chance vale mais que um de R$55 com 90%. Ignorar valor seria matematicamente incorreto para alocação de tempo do vendedor. |
| **Quem decidiu** | Candidato |

---

## Decisão 02 — Velocity: curva única bimodal

| Campo | Detalhe |
|-------|---------|
| **Contexto** | A curva de velocity poderia ser modelada por produto (cada produto com ciclo médio diferente) ou como curva única validada em todos os produtos. |
| **Opções consideradas** | (A) Curva por produto. (B) Curva única após validação de homogeneidade. |
| **Decisão** | Curva única bimodal, validada em todos os produtos. |
| **Justificativa** | A análise estatística mostrou que os ciclos de venda dos diferentes produtos não apresentam diferença significativa. Uma curva única é mais simples, robusta e evita overfitting com amostras pequenas por produto. |
| **Quem decidiu** | Consenso |

---

## Decisão 03 — Account Quality: peso reduzido

| Campo | Detalhe |
|-------|---------|
| **Contexto** | Dados mostraram que a diferença de win rate entre contas com melhor e pior histórico era de apenas 2—6 pontos percentuais. |
| **Opções consideradas** | (A) Peso de 15% como dimensão padrão. (B) Peso de 10% reconhecendo baixo poder preditivo. (C) Remover completamente. |
| **Decisão** | Manter Account Quality com peso reduzido (15% Engaging, 20% Prospecting). |
| **Justificativa** | O spread de 2—6pp é estatisticamente fraco mas não desprezível. Em produção com mais dados (NPS, churn, lifetime value), esta dimensão ganha relevância. Manter com peso baixo preserva a arquitetura. |
| **Quem decidiu** | Consenso |

---

## Decisão 04 — Mentoria ao invés de reatribuição

| Campo | Detalhe |
|-------|---------|
| **Contexto** | A IA sugeriu que deals com baixa afinidade agente-produto deveriam ser reatribuídos a outros vendedores. O candidato corrigiu: não conhecemos a política de comissão nem os territórios da empresa. |
| **Opções consideradas** | (A) Recomendar reatribuição de deals entre vendedores. (B) Recomendar mentoria — sugerir que o vendedor busque apoio do colega com melhor afinidade naquele produto. |
| **Decisão** | Mentoria ao invés de reatribuição. |
| **Justificativa** | Reatribuir deals impacta comissão, relacionamento com cliente e territórios — variáveis que não temos no dataset. Mentoria preserva o ownership do deal enquanto transfere conhecimento. É uma recomendação segura que não depende de políticas internas desconhecidas. |
| **Quem decidiu** | Candidato |

---

## Decisão 05 — Leaderboard público

| Campo | Detalhe |
|-------|---------|
| **Contexto** | O dashboard poderia ter rankings privados (cada vendedor vê só o seu) ou um leaderboard público com todos os vendedores visíveis. |
| **Opções consideradas** | (A) Ranking privado por vendedor. (B) Leaderboard público com todos os vendedores. |
| **Decisão** | Leaderboard público. |
| **Justificativa** | A cultura do G4 Educação é transparência e meritocracia. Um leaderboard público reforça esses valores, estimula competição saudável e alinha com a filosofia de gestão à vista. |
| **Quem decidiu** | Candidato |

---

## Decisão 06 — UX duas camadas

| Campo | Detalhe |
|-------|---------|
| **Contexto** | Como apresentar a análise de cada deal sem sobrecarregar a interface. |
| **Opções consideradas** | (A) Tudo visível sempre. (B) Resumo sempre visível + análise expansível. (C) Modal com detalhes. |
| **Decisão** | Duas camadas: resumo sempre visível + análise expansível. |
| **Justificativa** | Vendedores precisam de scan rápido (score, status, valor) para triagem. A análise detalhada (dimensões, recomendações) é necessária apenas quando o vendedor decide agir. Duas camadas respeitam o fluxo natural de trabalho. |
| **Quem decidiu** | Consenso |

---

## Decisão 07 — Botões contextuais por score

| Campo | Detalhe |
|-------|---------|
| **Contexto** | Os botões de ação em cada card de deal poderiam ser genéricos (Analisar, Ver detalhes) ou contextuais baseados no score. |
| **Opções consideradas** | (A) Botões genéricos (Analisar). (B) Botões contextuais (Por que é prioridade?, O que está travando?, Vale recuperar?). |
| **Decisão** | Botões contextuais que mudam conforme a faixa de score. |
| **Justificativa** | Um deal HOT gera a pergunta Por que é prioridade? — diferente de um deal COLD que gera Vale recuperar?. Botões contextuais antecipam a dúvida do vendedor e reduzem cliques desnecessários. |
| **Quem decidiu** | Candidato |

---

## Decisão 08 — Redistribuição de pesos: Agent-Product Affinity dominante (40%)

| Campo | Detalhe |
|-------|---------|
| **Contexto** | A análise exploratória revelou que afinidade agente-produto é de longe o preditor mais forte dos dados, com spread de 66pp dentro do mesmo vendedor (Niesha Huffines: 80% GTX Plus Pro vs 14% GTX Pro). Produto, setor, região e manager individualmente têm spreads de apenas 3-5pp. Na v2, todas as dimensões tinham pesos similares (15-20%), dando importância igual a preditores com poder muito diferente. |
| **Opções consideradas** | (A) Manter pesos equilibrados (20% cada) — simples mas ignora a realidade dos dados. (B) 30% para affinity — incremento conservador. (C) 40% para affinity — agressivo mas proporcional ao poder preditivo. |
| **Decisão** | 40% para Agent-Product Affinity, redistribuindo o restante proporcionalmente ao poder preditivo de cada dimensão: velocity 20%, dealValue 20%, accountQuality 15%, productSectorFit 5%. |
| **Justificativa** | 40% é agressivo mas reflete a realidade dos dados — não é uma escolha arbitrária. A análise mostrou que affinity sozinha explica mais variância que todas as outras dimensões combinadas. O risco de score "unidimensional" é mitigado porque as outras 4 dimensões ainda somam 60%. |
| **Quem decidiu** | Candidato, após análise dos dados com IA |

---

## Decisão 09 — Deal Value com escala logarítmica

| Campo | Detalhe |
|-------|---------|
| **Contexto** | A normalização linear com 7 preços fixos ($55 a $26.768) fazia 6 dos 7 produtos ficarem entre 0-20 no score de dealValue, e apenas GTK 500 chegava em 100. A dimensão era quase binária: "é GTK 500 ou não". Isso desperdiçava o poder discriminativo — um deal de $4.821 (GTX Pro) recebia dealValue=18, quase igual a $55 (MG Special) com dealValue=0. |
| **Opções consideradas** | (A) Manter linear — honesto sobre a distância real ($55 vs $26K). (B) Logarítmica — diferencia melhor os produtos intermediários. (C) Buckets discretos por faixa de preço. |
| **Decisão** | Logarítmica: score = ((log(price) - log(55)) / (log(26768) - log(55))) × 100. |
| **Justificativa** | O vendedor precisa saber que um deal de $4.821 (score=72) merece mais atenção que um de $550 (score=37), não só que $26K é rei. A escala logarítmica reflete como humanos percebem valor — a diferença entre $55 e $550 é tão relevante quanto entre $5.482 e $26.768. Resultados: $55→0, $550→37, $1.096→48, $3.393→67, $4.821→72, $5.482→74, $26.768→100. |
| **Quem decidiu** | Candidato |

---

## Decisão 10 — Multiplicador de decay para deals >138 dias

| Campo | Detalhe |
|-------|---------|
| **Contexto** | O max histórico de fechamento é 138 dias — nenhum deal Won levou mais que isso. 83,6% dos deals em Engaging excedem esse limite. A step function de velocity já dava 10 para >130d, mas não diferenciava 131d de 400d. Um deal com 400 dias no pipeline é qualitativamente diferente de um com 140 dias, mas ambos recebiam o mesmo score. |
| **Opções consideradas** | (A) Decay gradual dentro da dimensão velocity (mudar a step function). (B) Multiplicador no score final: `max(0.5, 1 - (days-138)/500)`. (C) Manter como está — velocity=10 já penaliza. |
| **Decisão** | Multiplicador no score final (opção B). Deal com 200d recebe ~88% do score, 300d recebe ~68%, 400d+ recebe 50% (cap mínimo). |
| **Justificativa** | Escolhemos multiplicador no score final em vez de mexer na velocity porque o problema não é só de velocity — é o deal inteiro que está comprometido. Um deal estagnado há 400 dias não tem apenas velocity ruim; toda a oportunidade se degradou. O cap de 0.5 (50%) existe porque não queremos zerar: o deal pode ter valor informacional mesmo estagnado (conta existente, vendedor com afinidade alta). |
| **Quem decidiu** | Candidato |

---

## Decisão 11 — Expected Value: manter score/100 como proxy de probabilidade

| Campo | Detalhe |
|-------|---------|
| **Contexto** | O Expected Value é calculado como `(score / 100) × preço do produto`. Isso trata o score como probabilidade percentual de fechamento. O backtest mostrou que a relação score→win rate real não é 1:1 (score 30 tem win rate real de 43%, score 70 tem win rate real de 73%), mas é monotonicamente crescente — scores mais altos consistentemente correlacionam com win rates mais altos. |
| **Opções consideradas** | (1) Calibrar o EV usando win rate real por faixa do backtest (COLD→43%, COOL→60%, WARM→73%, HOT→88%). Vantagem: mais preciso para forecast. Desvantagem: comprime 1.076 deals COOL (51% do pipeline) para a mesma probabilidade, eliminando diferenciação dentro da faixa. Gera confusão quando vendedor vê score 45 mas EV é calculado com 60%. (2) Interpolação linear entre as faixas. Mais granular, mas adiciona complexidade sem evidência de que a interpolação é correta. (3) Manter score/100 como está. |
| **Decisão** | Opção 3 — manter score/100. O score está funcionando bem como métrica de priorização (backtest confirma monotonicidade) e como proxy razoável para probabilidade. A simplificação é transparente e fácil de explicar. As limitações são documentadas. |
| **Limitação conhecida** | O EV subestima deals de score baixo (COLD tem win rate real 13pp acima do que o score implica) e é aproximado para deals altos (WARM e HOT ficam próximos do real). Para forecast de pipeline agregado, os valores devem ser tratados como indicativos, não como previsão financeira. |
| **Double-counting** | Deal Value (preço em escala logarítmica) compõe 20% do score, e depois o score é multiplicado pelo preço para calcular EV. O efeito é que deals caros recebem um boost duplo. Decisão: manter intencionalmente — deals de maior valor devem receber mais atenção do vendedor, e o double-counting reforça isso. A análise mostrou que a remoção do Deal Value do score não altera significativamente o ranking de EV (GTK 500 domina de qualquer forma pela diferença de preço de 487x). |
| **Quem decidiu** | Candidato, após análise detalhada de todas as opções com IA |

---

## Decisão 12 — Validação: close_value é unitário, não representa volume

| Campo | Detalhe |
|-------|---------|
| **Contexto** | Durante a revisão final, surgiu a dúvida se o valor do deal representava uma única venda ou um volume (ex: 1.000 unidades de $55 = $55.000). Se fosse volume, toda a lógica de Deal Value no scoring estaria errada — deals de MG Special ($55) poderiam representar contratos muito maiores. |
| **Verificação** | Analisamos os 4.238 deals Won. O close_value varia ±30% do sales_price (ex: MG Special fecha entre $38-$72, GTX Basic entre $365-$716). Nenhum múltiplo inteiro aparece (não há $110, $165 pra MG Special). Distribuição em forma de sino centrada no preço de lista. Conclusão: cada deal é 1 unidade a preço negociado. |
| **Decisão** | Manter Deal Value como está. O valor do deal é unitário com variação por negociação, não por quantidade. |
| **Quem decidiu** | Candidato, após verificação empírica dos dados |

---

## Resumo de Autoria

| Quem decidiu | Quantidade | Decisões |
|--------------|-----------|----------|
| **Candidato** | 8 | 01, 04, 05, 07, 08, 09, 10, 11, 12 |
| **Consenso** | 4 | 02, 03, 06 |
| **IA (sozinha)** | 0 | — |

> Nota: nenhuma decisão foi tomada exclusivamente pela IA. Todas passaram por validação do candidato ou foram iniciativa dele. O documento em questão foi sendo escrito pela IA conforme prompts de decisão iriam ocorrendo.
