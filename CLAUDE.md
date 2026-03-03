# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

This is a **selection challenge repository** for G4's AI Master role. Candidates fork it, pick one challenge, build a solution, and submit via Pull Request. There is no application to build or tests to run — the content is the challenges themselves and candidate submissions.

## Repository Structure

```
/challenges/          — Four independent challenge briefs (each self-contained)
  data-001-churn/     — SaaS churn analysis (5 CSV tables from Kaggle)
  process-002-support/— Support ticket redesign + automation prototype (~30K tickets)
  build-003-lead-scorer/ — Sales pipeline prioritization tool (~8.8K deals)
  marketing-004-social/  — Social media strategy from 52K posts
/submissions/         — Candidate work goes here (gitignored by default)
/templates/           — submission-template.md for candidates to fill out
submission-guide.md   — What to submit and how to structure it
CONTRIBUTING.md       — Step-by-step PR instructions for candidates
```

## Submission Workflow

Candidates must:
1. Fork → create branch `submission/their-name` → work in `submissions/their-name/`
2. Structure: `solution/`, `process-log/` (mandatory), optional `docs/`
3. Open PR to `main` with title format: `[Submission] Name — Challenge XXX`
4. **PRs that modify files outside `submissions/their-name/` are rejected**

## Evaluation Bar

The repo maintainers pre-ran all 4 challenges through multiple LLMs (Claude, GPT, Gemini) to establish baselines. Submissions that simply prompt-dump are disqualified. Strong submissions demonstrate:
- Cross-table/cross-dataset analysis (not single-file summaries)
- Iterative AI use with documented corrections and judgment calls
- Actionable outputs (specific recommendations, working software, not generic documents)
- Process log showing prompts, iterations, and what the human added beyond AI output

## Challenge Data Sources

All datasets are public Kaggle links referenced inside each challenge README — candidates download them directly. Data files are gitignored (`datasets/`). When working on challenge solutions, fetch data from the Kaggle links in the respective challenge README.

| Challenge | Dataset | Key tables/fields |
|-----------|---------|------------------|
| 001 Churn | SaaS Subscription & Churn Analytics | 5 CSVs joined on `account_id`/`subscription_id` |
| 002 Support | Customer Support Ticket Dataset + IT Service Ticket Classification | `Ticket Description`, `Resolution`, `Customer Satisfaction Rating` |
| 003 Lead Scorer | CRM Sales Predictive Analytics | `sales_pipeline.csv` central table, joined to accounts/products/teams |
| 004 Social | Social Media Sponsorship & Engagement | `is_sponsored` flag, cross-platform engagement metrics |

## Working on a Challenge Submission

When helping build a submission for any challenge:

- **001 (Churn)**: Must cross all 5 tables. Root cause analysis, not surface metrics. CEO-readable output.
- **002 (Support)**: Three deliverables — operational diagnosis (with numbers), automation proposal (distinguishing what NOT to automate), and a functional prototype.
- **003 (Lead Scorer)**: Primary deliverable is **running software**, not a document. Explainability matters ("why score 85") over model sophistication. Scoring must use real dataset features beyond just deal value.
- **004 (Social)**: Go beyond obvious cuts (platform averages). Control for creator size when comparing sponsored vs. organic. Segment before analyzing — 52K rows is too much to treat as one population.

## Branch Convention

Active submission branch: `submission/brunocamparadiniz`
Target for PRs: `main`
