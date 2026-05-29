# Implementation Plan: G4 Suporte Inteligente (MVP)

**Branch**: `001-g4-suporte-inteligente-mvp` | **Date**: 2026-05-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-g4-suporte-inteligente-mvp/spec.md`

## Summary

Construir um MVP web de suporte inteligente com duas jornadas principais: (1) cliente registra problema por texto/áudio e recebe sugestão para possível deflexão; (2) admin visualiza diagnóstico operacional e gerencia tickets. A solução usa análise offline para gerar insights de dashboard e base semântica para sugestão contextual.

## Technical Context

**Language/Version**: TypeScript 5.x + Node.js 20.x (web app), Python 3.11+ (pipeline analítico)

**Primary Dependencies**: Next.js 14 (App Router), Tailwind CSS, shadcn/ui, Supabase JS SDK, OpenAI SDK, Recharts, pandas, scikit-learn, kagglehub

**Storage**: Supabase Postgres + pgvector + Supabase Storage (áudio) + arquivo estático `insights.json`

**Testing**: ESLint + TypeScript checks + smoke tests manuais de jornada + validação de scripts analíticos

**Target Platform**: Web responsiva (desktop/mobile) com deploy em Vercel e serviços em Supabase Cloud

**Project Type**: Aplicação web full-stack com rotas serverless e pipeline offline de dados

**Performance Goals**:
- Transcrição de áudio até 30s em <= 8s (p90, ambiente de demonstração)
- Sugestão RAG em <= 4s (p90, ambiente de demonstração)
- Tela admin inicial renderizada em <= 3s com `insights.json` local

**Constraints**:
- Nenhum arquivo fora de `submissions/pedro-henrique-silva/`
- Código do produto integralmente em `submissions/pedro-henrique-silva/solution/`
- Segregação de acesso por papel (`admin` e `customer`)
- Não comitar arquivos de dados brutos grandes do Kaggle

**Scale/Scope**:
- MVP com 2 personas principais e 3 jornadas centrais
- 6 rotas de API principais
- Base vetorial inicial com amostra de 3k a 5k registros para viabilizar custo/latência

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Scope compliance (Pass)**: Planejamento e implementação limitados à pasta de submissão.
- **Product value (Pass)**: User stories priorizam deflexão e decisão executiva.
- **AI guardrails (Pass)**: Baixa confiança exige fallback explícito e abertura de ticket.
- **Role-based access (Pass)**: Regras de acesso por papel incluídas no modelo e contratos.
- **Reproducibility (Pass)**: Pipeline offline, artefatos e quickstart definidos.

## Project Structure

### Documentation (this feature)

```text
specs/001-g4-suporte-inteligente-mvp/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── api.openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
submissions/pedro-henrique-silva/
├── docs/
├── process-log/
├── solution/
│   ├── app/
│   │   ├── (auth)/login/page.tsx
│   │   ├── customer/new/page.tsx
│   │   ├── customer/tickets/page.tsx
│   │   ├── admin/page.tsx
│   │   ├── admin/tickets/page.tsx
│   │   └── api/
│   │       ├── transcribe/route.ts
│   │       ├── rag-search/route.ts
│   │       ├── classify/route.ts
│   │       ├── tickets/route.ts
│   │       ├── deflection/route.ts
│   │       └── insights/route.ts
│   ├── components/
│   ├── lib/
│   ├── public/insights.json
│   ├── scripts/
│   └── supabase/schema.sql
└── specs/
```

**Structure Decision**: Estrutura de aplicação web única em `solution/`, separando UI por persona, APIs por responsabilidade e pipeline offline em `solution/scripts/`, para manter baixa complexidade e rastreabilidade do MVP.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Nenhuma violação de constituição identificada | N/A | N/A |
