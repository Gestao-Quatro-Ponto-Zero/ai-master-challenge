# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a challenge repository for G4 Educação's "AI Master" selection process. It contains 4 business challenges where candidates must deliver functional solutions (not presentations) using AI tools strategically. The repo manages challenge definitions and candidate submissions.

**There is no build system, test runner, or CI/CD pipeline** — this is a documentation and submission management repo.

## Repository Structure

- `challenges/` — Four standalone business challenges, each with its own README
- `templates/submission-template.md` — Template candidates must use for submissions
- `submissions/` — Candidate submissions (gitignored, not committed to main)
- `CONTRIBUTING.md` — Step-by-step submission process
- `submission-guide.md` — Evaluation criteria and what makes strong/weak submissions

## The Four Challenges

| ID | Name | Domain | Dataset Source |
|----|------|--------|----------------|
| `data-001-churn` | Diagnóstico de Churn | Data/Analytics | SaaS Subscription & Churn Analytics (Kaggle, MIT) |
| `process-002-support` | Redesign de Suporte | Operations/CX | Customer Support Tickets (Kaggle, CC0) |
| `build-003-lead-scorer` | Lead Scorer | Sales/RevOps | CRM Sales Predictive Analytics (Kaggle, CC0) |
| `marketing-004-social` | Estratégia Social Media | Marketing | Social Media Sponsorship & Engagement (Kaggle, MIT) |

Datasets are downloaded separately by candidates and excluded via `.gitignore` (`datasets/`).

## Submission Flow

Candidates must:
1. Fork the repo
2. Create branch `submission/seu-nome`
3. Create folder `submissions/seu-nome/` with the structure from `templates/submission-template.md`
4. Only modify files inside their own `submissions/seu-nome/` folder
5. Open a PR to `main` titled `[Submission] Seu Nome — Challenge XXX`

The PR structure enforces git competency as part of the evaluation.

## Key Evaluation Philosophy

- Solutions must go beyond a single AI prompt → response cycle
- A mandatory **process log** (screenshots, chat exports, git history, narrative) is required
- Emphasis on human judgment, iteration, and knowing *what not to automate*
- Time budget is 4–6 hours per challenge; doing more doesn't earn extra points
- Baseline: running the problem directly through an AI model won't pass — submissions must demonstrate strategic AI usage

## Documentation Language

All documentation in this repo is in **Portuguese**. When adding or editing challenge READMEs, `CONTRIBUTING.md`, or submission guides, write in Portuguese.

## DEVLOG — Registro obrigatório

`DEVLOG.md` na raiz do projeto é o diário de decisões e estratégias da submissão. **Toda vez que uma decisão relevante for tomada, um erro for identificado, ou uma etapa for concluída, registrar uma entrada no DEVLOG antes de fazer o commit.**

Formato de entrada:
- `**[user]**` para decisões e direcionamentos do humano
- `**[ai]**` para o que foi sugerido ou executado pelo Claude
- `**❌ [user|ai]**` para erros — sempre com o aprendizado

O DEVLOG serve como process log da submissão e memória do projeto. Não reconstruir retroativamente — registrar ao vivo, antes do commit.
