# CLAUDE.md — Submissão Challenge 003 (Lead Scorer)

Instruções para o Claude Code trabalhar nesta pasta.

## Contexto

Processo seletivo G4 "AI Master". Desafio: [challenges/build-003-lead-scorer](../../challenges/build-003-lead-scorer/README.md). A avaliação pesa: funcionar de verdade, scoring que faz sentido e é explicável, UI que ajuda a decidir, código mantível e **evidência de processo**. Respostas parecidas com o "baseline" (colar o brief numa IA) são reprovadas.

Leia antes de mexer: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/SCORING.md](docs/SCORING.md), [docs/DESIGN.md](docs/DESIGN.md), [docs/PLAN.md](docs/PLAN.md).

## Regras do repositório (críticas)

- Só alterar arquivos dentro de `submissions/renan/`. PRs que tocam outros arquivos são rejeitados.
- O `.gitignore` da raiz ignora `submissions/`. Para adicionar arquivos, rode `sh submissions/renan/git-add.sh`. **Nunca** `git add -f submissions/renan`: isso força o `node_modules` junto.
- Branch: `submission/renan`. Título do PR: `[Submission] Renan — Challenge 003`.
- Commits pequenos e descritivos: o histórico do git faz parte do process log.

## Stack

Node.js + TypeScript (strict) + Next.js App Router + React 19 + Tailwind CSS v4 + Zod + Vitest. App em `solution/`.

## Convenções

- Motor de scoring em `solution/src/lib/scoring`: funções puras, sem React nem I/O, com testes.
- Server Components por padrão; `"use client"` só onde há interação.
- Filtros no `searchParams` da URL.
- Textos da interface em pt-BR; valores em US$.
- Nenhum número na UI ou nos docs que o script `analyze` não reproduza.
- Design: seguir `docs/DESIGN.md`. Usar as skills `frontend-design`, `ui-typography`, `vercel-react-best-practices`; auditar com `design-audit` e `web-design-guidelines`.

## Process log

A cada fase, adicionar uma entrada em `process-log/PROCESS_LOG.md`: o que foi pedido, onde a IA errou, o que foi decidido por mim. Atualizar o "Tempo real" em `docs/PLAN.md`.
