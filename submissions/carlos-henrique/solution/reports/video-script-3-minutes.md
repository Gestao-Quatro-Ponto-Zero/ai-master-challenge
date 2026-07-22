# JourneyGraph — Three-Minute Video Script

## Recording Target

- **Target duration:** 3 minutes 5 seconds.
- **Accepted rehearsal window:** 2 minutes 45 seconds to 3 minutes 15 seconds.
- **Primary language:** English.
- **Supporting language:** Brazilian Portuguese.
- **Evidence boundary:** fixed historical snapshot through December 31, 2024; descriptive evidence only.

## Main Script — English

### 00:00–00:20 — Opening and Problem

Retention teams rarely lack data. They lack a trustworthy sequence. Accounts, subscriptions, usage, support, churn, and reactivation arrive at different grains, so a simple join can inflate metrics and a final churn flag can erase the customer journey. JourneyGraph turns that fragmented history into governed retention evidence.

### 00:20–00:40 — Why Conventional Views Fail

Before analysis, the project tests relationships and chronology. The unsafe five-source join expanded 500 accounts into almost 148 thousand rows. Separately, thousands of parseable events violated lifecycle order. JourneyGraph preserves those problems instead of hiding them: invalid chronology goes to quarantine, and every downstream claim keeps a defined grain and cutoff.

### 00:40–01:05 — Executive Overview

This overview shows the fixed historical snapshot. From 35,586 processed events, 13,927 are usable in the MAIN population and 21,659 remain quarantined. The usable evidence forms 4,221 governed journeys. These are descriptive results, not a forecast, and the snapshot ends on December 31, 2024.

### 01:05–01:25 — Data Quality

The quality page makes exclusion visible. MAIN retains valid events plus documented warnings; STRICT keeps only valid events for sensitivity. Quarantine is a data-quality backlog, never a customer-behavior signal. This separation prevents invalid chronology from becoming an operational conclusion.

### 01:25–01:50 — Journey Explorer

The Journey Explorer uses controlled anonymous profiles. It preserves recurrent churn and explicit reactivation rather than reducing an account to one terminal label. Each view shows ordered events, scope, outcome, and quality context without exposing operational account identifiers.

### 01:50–02:15 — JourneyGraph

The graph promotes only supported ROBUST or SENSITIVE evidence. Here, 435 patterns and 43 transitions remain connected to support, population, stability, and provenance. The view is intentionally bounded. Direction and centrality describe historical structure; they do not establish why churn happened.

### 02:15–02:35 — Review Queue

Seven deterministic queues organize 1,609 evidence items for human review. Rules and priority components are inspectable, and data-quality review remains separate from behavioral review. There is no predictive churn score and no automated customer action.

### 02:35–02:50 — Experiment Lab

Eight experiment designs convert observations into testable hypotheses. One is ready for review, one is pilot only, four are underpowered, and two are not feasible. These are experiment designs, not completed experiments, and all remain `UNTESTED`.

### 02:50–03:05 — Governance and Closing

JourneyGraph is a local, reproducible demonstration with fixed JSON evidence, no runtime external service, and explicit privacy and causal boundaries. It helps teams decide what deserves investigation or a future governed test. The next step remains a human decision.

## Supporting Script — Português do Brasil

### 00:00–00:40 — Problema

Equipes de retenção têm muitos dados, mas nem sempre uma sequência confiável. Contas, assinaturas, uso, suporte, churn e reativação estão em granularidades diferentes. O JourneyGraph transforma essa história fragmentada em evidência governada, evitando joins que inflam métricas e status finais que apagam recorrências.

### 00:40–01:25 — Evidência e qualidade

A visão executiva apresenta um snapshot histórico fixo: 35.586 eventos processados, 13.927 utilizáveis, 21.659 em quarentena e 4.221 jornadas. A população MAIN inclui warnings documentados; a STRICT mantém apenas eventos válidos. Quarentena representa qualidade de dados, não comportamento.

### 01:25–02:15 — Jornadas e grafo

O explorador mostra perfis anônimos, churn recorrente e reativação explícita. O grafo promove somente evidência ROBUST ou SENSITIVE com suporte, totalizando 435 padrões e 43 transições. A estrutura é histórica e descritiva; direção e centralidade não explicam a causa do churn.

### 02:15–02:50 — Revisão e experimentos

Sete filas determinísticas organizam 1.609 itens para revisão humana. Não existe score preditivo nem ação automática sobre clientes. O laboratório apresenta oito desenhos experimentais: um pronto para revisão, um piloto, quatro subdimensionados e dois inviáveis. Eles não são experimentos concluídos e permanecem `UNTESTED`.

### 02:50–03:05 — Encerramento

O JourneyGraph é uma demonstração local, reproduzível e limitada ao snapshot de 31 de dezembro de 2024. Ele apoia a decisão sobre o que investigar ou testar; a decisão final continua humana.

## Teleprompter — English

Retention teams rarely lack data. They lack a trustworthy sequence. Accounts, subscriptions, usage, support, churn, and reactivation arrive at different grains, so a simple join can inflate metrics and a final churn flag can erase the customer journey. JourneyGraph turns that fragmented history into governed retention evidence.

Before analysis, the project tests relationships and chronology. The unsafe five-source join expanded 500 accounts into almost 148 thousand rows. Thousands of parseable events also violated lifecycle order. JourneyGraph preserves those problems: invalid chronology goes to quarantine, and every downstream claim keeps a defined grain and cutoff.

The overview shows a fixed historical snapshot. From 35,586 processed events, 13,927 are usable and 21,659 remain quarantined. The usable evidence forms 4,221 governed journeys. MAIN includes valid events plus documented warnings; STRICT keeps only valid events for sensitivity. Quarantine is never a behavior signal.

The Journey Explorer uses anonymous profiles and preserves recurrent churn and explicit reactivation. The graph then promotes only supported ROBUST or SENSITIVE evidence: 435 patterns and 43 transitions connected to support, population, stability, and provenance. Graph structure is descriptive; it does not establish why churn happened.

Seven deterministic queues organize 1,609 evidence items for human review. There is no predictive churn score and no automated customer action. Eight experiment designs turn observations into testable hypotheses, but they are not completed experiments and all remain `UNTESTED`.

JourneyGraph is a local, reproducible demonstration with fixed JSON evidence, no runtime external service, and explicit privacy and causal boundaries. It helps teams decide what deserves investigation or a future governed test. The next step remains a human decision.

## Delivery Notes

- Pause briefly after each number group; do not read table labels.
- Keep the cursor still while explaining a decision.
- Use the segmented timing as the recording source of truth.
- If rehearsal exceeds 3:15, shorten the conventional-view explanation before removing governance language.
