# Diagnostico operacional - Challenge 002

## Resumo executivo

A operacao tem dois problemas centrais: backlog alto e pouca diferenciacao de tratamento por risco. No Dataset 1, ha 8.469 tickets, mas apenas 2.769 fechados com satisfacao e tempo de resolucao disponiveis; 5.700 tickets estao abertos ou aguardando cliente. A mediana corrigida de resolucao e 11,6h, com p90 de 21,7h. O maior ganho nao vem de automatizar tudo, mas de separar tickets repetitivos com alta confianca para auto-roteamento e manter casos criticos ou ambiguidade alta com humano.

## Qualidade dos dados

O Dataset 1 anunciado no briefing fala em cerca de 30.000 registros, mas o arquivo publico baixado tem 8.469 tickets. Alem disso, 1.365 dos 2.769 tickets fechados tinham `Time to Resolution` anterior ao `First Response Time`. Para estimar duracao sem descartar metade da amostra fechada, tratei deltas negativos como virada de dia, somando 24h.

Essa decisao e uma limitacao importante: a analise mostra gargalos relativos e priorizacao operacional, mas nao deve ser usada como SLA financeiro definitivo sem validar o significado original dos timestamps.

## Onde o fluxo trava

### Visao geral

| Metrica | Valor |
|---|---:|
| Tickets totais | 8.469 |
| Tickets fechados com tempo e CSAT | 2.769 |
| Tickets abertos ou pendentes | 5.700 |
| Mediana de resolucao corrigida | 11,6h |
| P90 de resolucao corrigida | 21,7h |
| Horas acima da mediana nos tickets fechados | 8.733,5h |

### Canal

| Canal | Tickets fechados | Media h | Mediana h | P90 h | CSAT medio |
|---|---:|---:|---:|---:|---:|
| Phone | 691 | 12,09 | 12,33 | 21,85 | 2,95 |
| Social media | 684 | 11,91 | 12,17 | 21,86 | 2,97 |
| Chat | 674 | 11,55 | 11,32 | 21,54 | 3,08 |
| Email | 720 | 11,55 | 11,10 | 21,49 | 2,96 |

Telefone e social media concentram os piores tempos medios. Chat tem tempo similar, mas CSAT mais alto, sugerindo que o canal suporta melhor interacao rapida ou alinhamento de expectativa.

### Tipo de ticket

| Tipo | Tickets fechados | Media h | Mediana h | P90 h | CSAT medio |
|---|---:|---:|---:|---:|---:|
| Product inquiry | 533 | 12,18 | 12,17 | 21,87 | 3,02 |
| Refund request | 596 | 11,98 | 11,94 | 21,59 | 2,93 |
| Billing inquiry | 544 | 11,75 | 11,70 | 22,16 | 3,03 |
| Cancellation request | 516 | 11,51 | 11,38 | 21,45 | 3,03 |
| Technical issue | 580 | 11,45 | 11,03 | 21,42 | 2,96 |

Refund request tem CSAT mais baixo entre os tipos, mesmo sem ser o maior tempo medio. Isso indica que parte da insatisfacao provavelmente vem de politica/resultado do atendimento, nao apenas velocidade.

## Combinacoes criticas

Combinacoes com pelo menos 25 tickets fechados:

| Canal | Prioridade | Tipo | Tickets | Media h | P90 h | CSAT |
|---|---|---|---:|---:|---:|---:|
| Chat | Low | Technical issue | 33 | 14,61 | 22,35 | 3,18 |
| Chat | High | Refund request | 41 | 14,10 | 21,40 | 3,15 |
| Social media | Medium | Technical issue | 30 | 14,09 | 23,14 | 2,67 |
| Social media | Critical | Product inquiry | 34 | 13,85 | 22,53 | 2,79 |
| Phone | Medium | Product inquiry | 49 | 13,84 | 22,37 | 3,06 |
| Phone | Medium | Cancellation request | 33 | 13,51 | 21,82 | 2,97 |
| Phone | High | Refund request | 31 | 13,44 | 21,72 | 2,29 |

O pior ponto de satisfacao e `Phone + High + Refund request`: media de 13,4h e CSAT 2,29. Esse e um bom candidato para playbook humano prioritario, nao para automacao cega.

## O que impacta satisfacao

Um modelo exploratorio para prever CSAT teve baixo poder preditivo, com R2 negativo e MAE de 1,22 ponto. Isso sugere que as variaveis estruturadas do Dataset 1 explicam pouco da nota de satisfacao. Mesmo assim, as maiores importancias relativas foram tempo de resolucao, idade do cliente e hora da primeira resposta.

Interpretacao: nao ha evidencia forte de que apenas reduzir tempo resolva CSAT. Para melhorar satisfacao, a operacao precisa combinar rapidez com melhor decisao de tratamento por tipo: refund, cancelamento e problemas tecnicos em social/telefone exigem playbooks especificos.

## Backlog

Maiores grupos abertos ou pendentes:

| Canal | Tipo | Tickets abertos/pendentes |
|---|---|---:|
| Social media | Technical issue | 313 |
| Chat | Technical issue | 311 |
| Phone | Cancellation request | 308 |
| Social media | Cancellation request | 305 |
| Email | Product inquiry | 301 |
| Social media | Refund request | 300 |

O backlog tem massa suficiente em tipos repetitivos para justificar triagem automatizada e roteamento por categoria/confianca.

## Recomendacoes priorizadas

1. Implantar triagem IA em duas camadas: classificacao automatica + regra de confianca. Alta confianca roteia; media vai para revisao rapida; baixa confianca fica com humano.
2. Criar fila prioritaria para `Phone + High + Refund request`, `Social media + Technical issue` e cancelamentos em telefone/social.
3. Padronizar respostas sugeridas apenas para tickets recorrentes e nao criticos, especialmente billing, product inquiry e technical issue de alta confianca.
4. Separar metricas de SLA operacional de metricas de satisfacao. A satisfacao nao parece ser explicada apenas por tempo; refund e cancelamento precisam de politica, tom e autonomia do agente.
5. Corrigir instrumentacao de dados antes de usar isso para meta oficial: timestamps devem diferenciar criacao, primeira resposta e resolucao em campos consistentes.
