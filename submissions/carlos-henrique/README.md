# JourneyGraph — Challenge 001: Diagnóstico de Churn

- **Candidato:** Carlos Henrique
- **Challenge escolhido:** Challenge 001 — Diagnóstico de Churn
- **Status atual:** Fase 0 — fundação

## Tese do produto

JourneyGraph é uma plataforma de inteligência de retenção que reconstrói trajetórias temporais de contas, identifica padrões antes de churn, retenção e reativação, prioriza receita em risco e converte evidências em intervenções e experimentos.

## Problema de negócio

A RavenStack precisa compreender por que clientes deixam a plataforma, quais segmentos e contas exigem atenção e quais intervenções devem ser priorizadas. A resposta deverá reconciliar evidências de contas, assinaturas, uso de funcionalidades, suporte e eventos de churn sem confundir associação temporal com causalidade.

## Perguntas planejadas

1. Quais trajetórias e sinais antecedem churn, retenção e reativação?
2. Como esses sinais variam entre segmentos e ao longo do tempo?
3. Quais contas concentram maior receita em risco?
4. Que padrões contradizem as leituras isoladas de produto, suporte ou satisfação?
5. Quais intervenções podem ser priorizadas e avaliadas por experimentos?

## Arquitetura conceitual resumida

As cinco fontes oficiais serão auditadas antes de qualquer transformação. Depois da validação, um pipeline reproduzível deverá construir um event log temporal, alimentar análises descritivas e temporais, habilitar journey mining e, somente então, materializar um grafo em NetworkX. Evidências validadas poderão abastecer uma watchlist e uma interface de decisão com revisão humana.

## Escopo planejado

- auditoria e reconciliação das cinco fontes;
- contrato de dados validado e rastreável;
- event log temporal antes do grafo;
- diagnóstico descritivo e temporal;
- survival analysis e journey mining;
- grafo MVP em NetworkX;
- priorização de receita em risco;
- watchlist e interface orientadas à decisão;
- recomendações testáveis, com human-in-the-loop.

## Fora de escopo nesta fase

- download, criação ou inspeção analítica de datasets;
- métricas, findings, estimativas ou recomendações analíticas;
- modelos estatísticos ou preditivos;
- event log, mineração de jornadas ou grafos;
- dashboard, API, automação operacional ou infraestrutura cloud;
- Neo4j, GNNs e dependência de APIs pagas no núcleo.

## Fontes de dados esperadas

Os arquivos oficiais são indicados pelo Challenge 001 no dataset público **SaaS Subscription & Churn Analytics**, disponibilizado no Kaggle sob licença MIT:

- `ravenstack_accounts.csv`;
- `ravenstack_subscriptions.csv`;
- `ravenstack_feature_usage.csv`;
- `ravenstack_support_tickets.csv`;
- `ravenstack_churn_events.csv`.

Os datasets ainda não foram adicionados. Nomes, chaves, colunas, granularidades e relacionamentos serão confirmados na Fase 1; nenhuma suposição documental substitui essa auditoria.

## Princípios de governança

- dados brutos são imutáveis e não devem ser versionados;
- toda transformação futura deve ser reproduzível por script;
- metadados, linhagem, reconciliação e testes acompanham os artefatos derivados;
- minimização, controle de acesso e prevenção de segredos orientam o tratamento de dados;
- nenhum dado sintético será usado como substituto silencioso das fontes oficiais;
- afirmações devem manter rastreabilidade até as evidências que as sustentam.

## Associação não é causalidade

Padrões, correlações e sequências temporais poderão orientar hipóteses, mas não serão apresentados como causas de churn. Alegações causais exigirão desenho experimental ou outra estratégia de identificação apropriada.

## Roadmap

1. **Fase 0 — Fundação:** estrutura, documentação, governança e segurança do repositório.
2. **Fase 1 — Auditoria:** inspeção das cinco fontes, contrato real e testes de qualidade.
3. **Fase 2 — Event log:** padronização temporal, reconciliação e validação.
4. **Fase 3 — Diagnóstico:** análises descritivas e segmentação de risco.
5. **Fase 4 — Survival:** modelagem temporal e avaliação de censura.
6. **Fase 5 — Journey mining:** trajetórias, transições e padrões temporais.
7. **Fase 6 — Grafo:** MVP em NetworkX após validação do event log.
8. **Fase 7 — Watchlist:** priorização operacional e intervenções.
9. **Fase 8 — Aplicação:** interface, explicabilidade e experimentação.

## Status de execução

Não existem resultados analíticos nesta versão.

> Esta versão contém apenas a fundação documental e estrutural. Nenhuma análise foi executada e nenhum resultado foi produzido.
