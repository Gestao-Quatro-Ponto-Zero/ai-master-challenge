# /docs — Specification Driven Development (SDD)

Este diretório organiza todo o conhecimento relevante do projeto em três camadas hierárquicas.

---

## Camada 1 — Negócio
> Por que estamos construindo isso?

| Arquivo | Conteúdo |
|---------|----------|
| [01-visao-estrategica.md](./01-business/01-visao-estrategica.md) | Contexto da RavenStack, problema de negócio, posicionamento |
| [02-personas.md](./01-business/02-personas.md) | CEO, Customer Success, cliente B2B |
| [03-kpis-e-metricas.md](./01-business/03-kpis-e-metricas.md) | Métricas de negócio e critérios de sucesso da análise |
| [04-jornada-do-cliente.md](./01-business/04-jornada-do-cliente.md) | Ciclo de vida da conta e pontos de fricção |

---

## Camada 2 — Produto
> O que estamos construindo e como funciona?

| Arquivo | Conteúdo |
|---------|----------|
| [01-dados-disponiveis.md](./02-product/01-dados-disponiveis.md) | Schema das 5 tabelas, significado de cada campo, modelo de relacionamento |
| [02-perguntas-da-analise.md](./02-product/02-perguntas-da-analise.md) | Perguntas primárias e secundárias que o produto deve responder |
| [03-deliverables.md](./02-product/03-deliverables.md) | Dashboard analítico + Agente de diagnóstico — specs e critérios de aceite |
| [04-playbook-cs.md](./02-product/04-playbook-cs.md) | Base de conhecimento de CS consultada pelo agente (6 categorias de problema) |

---

## Camada 3 — Engenharia
> Como estamos construindo, com que padrões e restrições?

| Arquivo | Conteúdo |
|---------|----------|
| [01-stack-tecnico.md](./03-engineering/01-stack-tecnico.md) | Stack completo: DuckDB, Parquet, Streamlit, Agno, Claude |
| [02-arquitetura-medalhao.md](./03-engineering/02-arquitetura-medalhao.md) | Fluxo bronze → silver → gold, tabelas por camada |
| [03-modelo-de-dados.md](./03-engineering/03-modelo-de-dados.md) | Schemas completos de todas as tabelas (silver e gold) |
| [04-adr-001-medallion-duckdb.md](./03-engineering/04-adr-001-medallion-duckdb.md) | ADR-001: decisão por Medallion + DuckDB + Parquet |
| [05-adr-002-agno-agent.md](./03-engineering/05-adr-002-agno-agent.md) | ADR-002: decisão por Agno como framework do agente |
| [06-estrutura-do-projeto.md](./03-engineering/06-estrutura-do-projeto.md) | Mapa de arquivos e responsabilidade de cada um |
