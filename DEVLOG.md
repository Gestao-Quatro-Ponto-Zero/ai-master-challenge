# DEVLOG — AI Master Challenge

Registro de decisões e estratégias. Entradas ao vivo, não reconstituídas.
**[user]** = dirigido pelo humano · **[ai]** = sugerido/executado pelo Claude

---

## Sessão 1 — Planejamento e scaffold

**[user]** Decidiu entregar os 4 desafios simultaneamente usando pnpm monorepo + Next.js.

**[ai]** Leu os READMEs dos 4 challenges e avaliou o que cada um realmente exige: 003 é o único onde app é obrigatória; 002 exige protótipo funcional na prática; 001 e 004 são análise com dashboard como diferencial.

**[ai]** Criou `planning/` com macro.md + um plan por challenge. Separação entre arquitetura técnica (definida no plan) e insights de negócio (definidos após os dados reais).

**❌ [ai]** Plans 001 e 004 foram escritos com insights e recomendações inventados antes de ver os dados. **[user]** identificou o problema e pediu correção. Aprendizado: plan define estrutura e queries; análise define conclusões.

**[ai]** Iterou 3 vezes na estratégia de dados: Python→JSON, papaparse manual, até chegar em DuckDB (SQL direto sobre CSV). DuckDB adotado por ser declarativo, sem parsing manual, com cache em memória.

**[user]** Decidiu usar Railway em vez de Vercel. Eliminou a necessidade de DuckDB-WASM e simplificou toda a camada de dados para server-side.

**[user]** Investigou uso da API do Kaggle para servir CSVs sem download. **[ai]** pesquisou e confirmou que é possível mas sempre retorna ZIP — decidiu manter CSVs baixados localmente por simplicidade.

**❌ [ai]** Especificou `@duckdb/node-api@^1.2.2` — versão inexistente. Corrigido para `1.5.0-r.1` após checar `pnpm view`.

**❌ [user]** Colocou os CSVs do Lead Scorer em `challenges/build-003-lead-scorer/data/` em vez de `submissions/bubex/apps/lead-scorer/data/`. **[ai]** identificou e moveu.

**[user]** Pediu criação do DEVLOG e diretriz no CLAUDE.md para registrar tudo ao vivo.

---

## Próximas entradas

<!-- Registrar aqui ao vivo -->
