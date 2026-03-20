# DEVLOG — AI Master Challenge

Registro cronológico de decisões, estratégias e aprendizados ao longo da construção da submissão. Mantido ao vivo — cada entrada no momento em que acontece.

---

## Sessão 1 — Planejamento macro

### ✅ CLAUDE.md criado
Arquivo de orientação para futuras instâncias do Claude Code. Cobre estrutura do repo, os 4 desafios, fluxo de submissão e filosofia de avaliação.

### ✅ Avaliação dos 4 desafios
Leitura dos READMEs de cada challenge para entender o que realmente é obrigatório vs. diferencial:
- 003 (Lead Scorer): app é o entregável principal — obrigatório
- 002 (Suporte): "quero ver algo rodando" — app obrigatória na prática
- 001 e 004: análise é o core, dashboard amplifica — diferencial forte

**Decisão:** entregar os 4 como apps funcionais em monorepo pnpm + Next.js.

### ✅ Estrutura de planejamento organizada
Criado `planning/` com `macro.md` e stubs para cada challenge. Separação clara entre arquitetura técnica (definida aqui) e insights de negócio (definidos depois dos dados reais).

### ❌ Erro: insights pré-fabricados nos plans
`planning/001-churn.md` e `planning/004-social.md` foram escritos com números e recomendações específicas antes de ver os dados (ex: "uso cai 65% nos 45 dias antes do churn", "micro-creators têm 2.3× mais engajamento"). Corrigido: planos de ação e insights removidos — serão preenchidos após exploração dos dados reais.

**Aprendizado:** plan técnico define estrutura e queries; análise define conclusões. Nunca inverter.

---

## Sessão 1 — Definição da stack de dados

### 🔄 Iteração na estratégia de dados (3 versões)

**v1 — Python pré-processando para JSON**
CSV → scripts Python → JSON commitado → Next.js lê JSON.
Descartado: adiciona camada desnecessária, dois runtimes, processo manual de re-gerar JSONs.

**v2 — papaparse em API routes**
CSV → API route (fs.readFile + papaparse) → JSON para o client.
Descartado: parsing manual em JS, joins e agregações viram código imperativo feio.

**v3 — DuckDB sobre CSV ✅**
CSV → DuckDB (SQL direto sobre arquivo) → API route retorna agregado.
Adotado: SQL nativo, joins declarativos, zero parsing manual, cache em memória automático.

### ✅ Deploy: Railway (não Vercel)
Vercel tem filesystem efêmero em serverless functions — DuckDB precisaria de workarounds (Vercel Blob ou JSONs pré-gerados). Railway roda container Node.js persistente com filesystem real: DuckDB funciona sem restrição nenhuma.

**Consequência:** DuckDB-WASM (planejado para o Lead Scorer client-side) foi eliminado. Mais simples: API route com DuckDB server-side retorna os 8.8K deals com score; TanStack Table filtra client-side.

---

## Sessão 1 — Scaffold do monorepo

### ✅ Estrutura criada
```
submissions/bubex/
├── apps/{lead-scorer,churn-dashboard,support-triage,social-dashboard}
├── packages/{ui,data-utils}
├── pnpm-workspace.yaml
└── package.json
```
Next.js 15, Tailwind v4, TypeScript strict, App Router. `@duckdb/node-api` centralizado em `packages/data-utils`.

### ❌ Erro: versão do @duckdb/node-api
Especificado `^1.2.2` — não existe. A versão mais recente usa sufixo de pre-release: `1.5.0-r.1`. Semver com `^` não resolve pre-releases. Corrigido para versão exata `1.5.0-r.1`.

**Aprendizado:** sempre checar versões disponíveis com `pnpm view <pkg> versions` antes de especificar no package.json.

### ❌ Erro: CSVs colocados em lugar errado
Datasets do Lead Scorer foram colocados em `challenges/build-003-lead-scorer/data/` em vez de `submissions/bubex/apps/lead-scorer/data/`. Movidos para o lugar correto.

**Aprendizado:** a estrutura de `challenges/` é do repo original (definições dos desafios). Nossa solução vive inteiramente em `submissions/bubex/`.

### ✅ Kaggle API investigada e descartada para dados
A API Kaggle existe (`GET /api/v1/datasets/download/{owner}/{dataset}/{file}`) mas retorna sempre ZIP, não CSV direto. Requer unzip em memória + parse. Para Railway com volume persistente, download manual + CSV no container é mais simples e robusto.

**Decisão:** CSVs baixados manualmente, armazenados em `apps/{app}/data/` (gitignored), Railway Volume para persistência em produção.

---

## Próximas entradas

<!-- Registrar aqui ao vivo conforme avançamos -->
