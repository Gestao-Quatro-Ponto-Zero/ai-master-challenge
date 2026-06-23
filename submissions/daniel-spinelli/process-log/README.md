# Process Log — Daniel Spinelli

## Challenge

**Challenge 001 — Diagnóstico de Churn**

Este documento descreve como utilizei IA durante o processo de análise, validação e construção da solução para o desafio RavenStack.

O objetivo não foi usar IA para gerar uma resposta pronta, mas sim como ferramenta de investigação, aceleração, contestação e refinamento analítico.

---

# 1. Ferramentas utilizadas

| Ferramenta              | Como foi usada                                                                                                                                |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| ChatGPT                 | Planejamento da análise, formulação de hipóteses, geração de blocos de código, interpretação inicial dos resultados e estruturação da entrega |
| Google Colab            | Execução das análises em Python e cruzamento dos datasets                                                                                     |
| IA Auditor / segunda IA | Auditoria crítica das conclusões, busca por falhas metodológicas e contestação das hipóteses iniciais                                         |
| GitHub / GitHub Desktop | Versionamento, organização da submissão e abertura do Pull Request                                                                            |
| Streamlit               | Construção do protótipo funcional de priorização de risco                                                                                     |

---

# 2. Como decompus o problema

O case apresentava um conflito entre três narrativas internas:

1. O CEO afirmava que o churn havia aumentado.
2. O time de CS afirmava que a satisfação estava boa.
3. O time de Produto afirmava que o uso da plataforma havia crescido.

A pergunta central passou a ser:

> Se o uso está saudável e a satisfação não caiu, por que o churn continua aumentando?

A partir disso, defini que a análise não deveria começar por um modelo preditivo, mas sim por uma investigação estruturada das hipóteses mais prováveis.

---

# 3. Hipóteses iniciais

As primeiras hipóteses investigadas foram:

1. Clientes churnam porque usam pouco a plataforma.
2. Clientes churnam por problemas de suporte.
3. Clientes churnam por plano, billing ou receita.
4. O churn está concentrado em segmentos específicos.
5. O churn aumentou ao longo do tempo, e não apenas em volume absoluto.
6. O problema pode estar ligado à percepção de valor e competitividade do produto.

---

# 4. Primeira rodada de análise

Na primeira rodada, usei IA para apoiar a criação dos blocos de código e a organização das perguntas analíticas.

Foram cruzados os cinco datasets:

* `ravenstack_accounts.csv`
* `ravenstack_subscriptions.csv`
* `ravenstack_feature_usage.csv`
* `ravenstack_support_tickets.csv`
* `ravenstack_churn_events.csv`

As primeiras análises compararam clientes retidos e churnados em:

* volume de uso;
* número de features utilizadas;
* tickets de suporte;
* tempo médio de resolução;
* satisfação média;
* plano contratado;
* billing frequency;
* receita média;
* indústria;
* canal de aquisição.

---

# 5. Primeiros achados

A análise inicial indicou que:

* clientes churnados não usavam menos a plataforma;
* clientes churnados tinham volume de tickets semelhante aos retidos;
* satisfação média era semelhante entre retidos e churnados;
* plano e billing não explicavam o churn de forma clara;
* DevTools apresentava maior taxa de churn;
* Event apresentava pior retenção por canal;
* FinTech apresentava maior impacto financeiro.

A primeira conclusão provisória foi que o churn parecia estar mais relacionado a fit, proposta de valor e segmentação do que a baixa adoção ou suporte.

---

# 6. Onde a IA começou a caminhar para uma conclusão incompleta

A IA inicialmente ajudou a estruturar uma tese plausível:

> O churn não é causado por baixa adoção, mas por usuários engajados que percebem falta de valor ou limitações do produto.

Essa tese fazia sentido com os dados iniciais, mas ainda era frágil. Ela estava baseada principalmente em comparações médias e não considerava suficientemente:

* evolução temporal;
* diferença entre volume e taxa de churn;
* impacto financeiro;
* possíveis variáveis de confusão;
* concentração de churn em segmentos ou canais;
* limitações do modelo preditivo.

Por isso, decidi não aceitar essa tese como conclusão final.

---

# 7. Auditoria crítica com outra IA

Para validar a análise, usei uma segunda IA com um papel diferente: atuar como auditora hostil.

O prompt utilizado pedia explicitamente que a IA:

* tentasse destruir a tese;
* identificasse erros metodológicos;
* separasse fatos comprovados de hipóteses;
* apontasse análises ausentes;
* avaliasse a entrega como se fosse uma banca executiva.

Essa auditoria foi uma etapa decisiva, porque ela mostrou que a análise inicial ainda estava incompleta.

---

# 8. Principais críticas levantadas pela auditoria

A auditoria apontou pontos importantes:

1. A análise não tinha componente temporal suficiente.
2. Havia risco de confundir volume de churn com taxa de churn.
3. As médias poderiam esconder padrões relevantes.
4. O modelo preditivo ainda era fraco.
5. Faltava traduzir os achados em impacto financeiro.
6. As variáveis geográficas surgiram no modelo, mas não haviam sido investigadas.
7. O protótipo não deveria ser vendido como modelo preditivo se o AUC fosse baixo.

Essas críticas mudaram a direção do trabalho.

---

# 9. Segunda rodada de análise

Após a auditoria, executei novas análises para responder às lacunas apontadas.

Foram investigados:

* churn mensal;
* taxa mensal de churn;
* active accounts por mês;
* churn por indústria ao longo do tempo;
* churn por canal ao longo do tempo;
* motivos de churn ao longo do tempo;
* impacto financeiro por segmento;
* churn por país;
* simulação de impacto financeiro para alavancas prioritárias.

---

# 10. Mudança da tese

A análise temporal mostrou que o churn não apenas cresceu em volume, mas também em taxa.

A taxa mensal chegou a **19,2% em dezembro de 2024**.

Isso mudou a leitura do problema.

A pergunta deixou de ser apenas:

> Quem churna?

E passou a ser:

> Por que a retenção deteriorou ao longo de 2024, mesmo com uso e satisfação relativamente saudáveis?

---

# 11. Achados após a segunda rodada

Os principais achados refinados foram:

* o churn acelerou significativamente ao longo de 2024;
* baixa adoção não explicou o churn;
* suporte não apareceu como principal driver;
* DevTools teve a maior taxa de churn;
* FinTech teve o maior impacto financeiro;
* Event teve pior retenção por canal;
* Alemanha teve a maior taxa percentual de churn por país;
* Estados Unidos concentrou o maior volume absoluto de churn;
* feedbacks relacionados a `too expensive`, `missing features` e `switched to competitor` cresceram ao longo do ano.

Com isso, a tese final passou a ser que o problema principal da RavenStack está ligado à aderência da proposta de valor para determinados perfis de cliente, não a uma falha operacional simples.

---

# 12. Modelo exploratório

Foi criado um modelo simples de churn scoring.

O resultado foi:

```text
ROC-AUC: 0.61
```

Esse resultado foi tratado com cautela.

Em vez de apresentar o modelo como uma ferramenta de previsão confiável, decidi declarar explicitamente sua limitação.

A conclusão foi:

> O modelo não tem performance suficiente para automatizar decisões de churn. Ele deve ser usado apenas como apoio exploratório para identificar fatores que podem alimentar uma priorização explicável.

Essa decisão foi importante porque evitou exagerar o valor de um modelo fraco.

---

# 13. Decisão sobre o protótipo

Com base na limitação do modelo, decidi não construir um “churn prediction tool”.

Em vez disso, construí um:

## RavenStack Churn Risk Prioritization Engine

O objetivo do protótipo é ajudar Customer Success e Revenue a priorizarem contas com base em fatores explicáveis, como:

* indústria;
* canal de aquisição;
* país;
* MRR;
* uso de features;
* escalonamentos;
* perfil de risco identificado na análise.

O protótipo foi construído em Streamlit e usa os dados reais incluídos na submissão.

---

# 14. Onde a IA errou e como corrigi

## Erro 1 — Aceitar uma tese cedo demais

A IA inicialmente caminhou para a tese de que usuários engajados churnavam por falta de valor. Essa tese era plausível, mas ainda não estava suficientemente validada.

**Correção:** usei uma segunda IA para auditar a análise e apontar fragilidades metodológicas.

---

## Erro 2 — Analisar volume antes de taxa

A IA ajudou a identificar crescimento no volume de churn, mas isso ainda não provava deterioração da retenção.

**Correção:** calculei taxa mensal de churn considerando contas ativas por mês.

---

## Erro 3 — Tratar médias como evidência suficiente

Comparações de médias ajudaram a orientar a análise, mas não sustentavam sozinhas a conclusão.

**Correção:** complementei a análise com evolução temporal, segmentação, impacto financeiro e auditoria crítica.

---

## Erro 4 — Dar peso excessivo ao modelo

O modelo teve AUC de 0.61. Isso não é forte o suficiente para uma ferramenta preditiva autônoma.

**Correção:** reposicionei o modelo como exploratório e criei um motor explicável de priorização.

---

## Erro 5 — Ignorar variáveis geográficas

O modelo indicou `country_US` e `country_DE` como variáveis relevantes, mas isso não estava inicialmente na narrativa.

**Correção:** investiguei churn por país e incorporei Alemanha e Estados Unidos na análise final.

---

# 15. O que eu adicionei além da IA

A IA ajudou a acelerar a análise, mas as decisões finais dependeram de julgamento humano.

Exemplos:

* decidir não aceitar a primeira tese;
* criar uma etapa explícita de auditoria;
* interpretar que AUC 0.61 não deveria ser vendido como previsão robusta;
* separar taxa de churn de volume absoluto;
* diferenciar taxa de churn de impacto financeiro;
* transformar achados em recomendações executivas;
* construir um protótipo explicável em vez de um modelo opaco;
* documentar limitações de forma honesta.

---

# 16. Evidências anexadas

As evidências do processo estão disponíveis em:

```text
process-log/screenshots/
```

Screenshots incluídos:

1. hipótese inicial e formulação do problema;
2. primeira exploração dos dados;
3. primeira auditoria crítica;
4. segunda auditoria em modo banca executiva;
5. consolidação dos achados;

---

# 17. Resultado final do processo

O processo não foi linear.

A análise começou com hipóteses simples, passou por uma primeira tese, foi criticada por outra IA, refeita em partes importantes e consolidada em uma solução mais robusta.

A IA foi usada como ferramenta de aceleração e contestação, não como fonte final de verdade.

A solução final reflete uma combinação de:

* análise quantitativa;
* revisão crítica;
* julgamento humano;
* prototipagem operacional;
* comunicação executiva.
