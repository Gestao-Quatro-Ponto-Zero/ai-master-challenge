# Prompt 001 — Setup do projeto

**Data:** 2026-03-20
**Agent:** Setup
**Ferramenta:** Claude Code
**Executado por:** Lucas Reis

## Objetivo
Criar estrutura completa do projeto, CLAUDE.md e arquivos base do process log.

## Prompt enviado ao Claude Code

> Você é o assistente técnico do projeto G4 AI Master Challenge — Challenge 001 Diagnóstico de Churn.
>
> Sua primeira tarefa é criar toda a estrutura do projeto e os arquivos de prompt que serão usados como evidência do process log.
>
> **TAREFA 1** — Criar estrutura de pastas em submissions/lucas-reis/ com: solution/data, solution/agents (6 arquivos), solution/notebooks, solution/dashboard, process-log/prompts (6 prompts), process-log/entries, process-log/screenshots, docs/
>
> **TAREFA 2** — CLAUDE.md na raiz com contexto do projeto: stack (DuckDB, LightGBM, SHAP, Plotly, Quarto), estrutura dos 5 CSVs, regras do projeto.
>
> **TAREFA 3** — Preencher process-log/prompts/prompt_001_setup.md com data, objetivo, prompt enviado, output gerado e decisão estratégica.
>
> **TAREFA 4** — Criar docs/architecture.md com visão geral dos 6 agents, fluxo de dados e stack técnica.
>
> **TAREFA 5** — Rodar `find submissions/lucas-reis -type f | sort` e mostrar output completo.

## Output gerado
- Estrutura de pastas criada (solution/, process-log/, docs/)
- CLAUDE.md criado na raiz do repositório
- 6 arquivos de agent criados em solution/agents/ (00–05)
- 6 arquivos de prompt criados em process-log/prompts/
- docs/architecture.md criado
- .gitkeep em data/, notebooks/, dashboard/, entries/, screenshots/

## Decisão estratégica
Documentar cada prompt como arquivo .md garante rastreabilidade completa do uso de IA —
exigência eliminatória do processo seletivo G4. Cada prompt registra: data, ferramenta,
objetivo, prompt literal enviado e output gerado. Isso permite auditar exatamente qual
decisão foi tomada por humano vs. IA em cada etapa do pipeline.
