# Tasks: G4 Suporte Inteligente (MVP)

**Input**: Design documents from `/specs/001-g4-suporte-inteligente-mvp/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Testes automatizados são recomendados para contratos críticos de API, com validação manual obrigatória dos critérios de aceite do MVP.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicializar base do projeto e dependências essenciais.

- [x] T001 Inicializar app Next.js 14 em submissions/pedro-henrique-silva/solution/package.json
- [x] T002 Configurar variáveis de ambiente base em submissions/pedro-henrique-silva/solution/.env.example
- [x] T003 [P] Configurar dependências UI e gráficos em submissions/pedro-henrique-silva/solution/package.json
- [x] T004 [P] Criar documentação técnica inicial do projeto em submissions/pedro-henrique-silva/solution/README.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestrutura transversal obrigatória para todas as histórias.

**⚠️ CRITICAL**: Nenhuma história deve avançar antes desta fase.

- [x] T005 Implementar schema de banco e função de similaridade em submissions/pedro-henrique-silva/solution/supabase/schema.sql
- [x] T006 [P] Implementar cliente Supabase server-side em submissions/pedro-henrique-silva/solution/lib/supabase/server.ts
- [x] T007 [P] Implementar cliente Supabase client-side em submissions/pedro-henrique-silva/solution/lib/supabase/client.ts
- [x] T008 [P] Implementar cliente OpenAI e helpers comuns em submissions/pedro-henrique-silva/solution/lib/openai.ts
- [x] T009 Implementar middleware de autenticação e roles em submissions/pedro-henrique-silva/solution/middleware.ts
- [x] T010 [P] Implementar utilitários de erros/respostas de API em submissions/pedro-henrique-silva/solution/lib/api.ts
- [x] T011 [P] Criar script de seed de usuários de teste em submissions/pedro-henrique-silva/solution/scripts/seed_users.ts
- [x] T012 Definir tipos centrais de domínio em submissions/pedro-henrique-silva/solution/lib/types.ts

**Checkpoint**: Fundação pronta para implementação independente das histórias.

---

## Phase 3: User Story 1 - Resolver no primeiro contato (Priority: P1) 🎯 MVP

**Goal**: Permitir que o cliente tente resolver o problema por texto/áudio antes da abertura de ticket.

**Independent Test**: Customer autenticado consegue enviar texto ou áudio, receber sugestão, clicar em "Resolveu" ou "Ainda preciso", e observar comportamento esperado (deflexão ou criação de ticket).

### Implementation for User Story 1

- [x] T013 [P] [US1] Implementar componente de gravação de áudio em submissions/pedro-henrique-silva/solution/components/VoiceRecorder.tsx
- [x] T014 [P] [US1] Implementar componente de exibição de sugestão RAG em submissions/pedro-henrique-silva/solution/components/RagSuggestion.tsx
- [x] T015 [US1] Implementar página de novo ticket com fluxo texto/áudio em submissions/pedro-henrique-silva/solution/app/customer/new/page.tsx
- [x] T016 [US1] Implementar endpoint de transcrição em submissions/pedro-henrique-silva/solution/app/api/transcribe/route.ts
- [x] T017 [US1] Implementar endpoint de busca semântica e sugestão em submissions/pedro-henrique-silva/solution/app/api/rag-search/route.ts
- [x] T018 [US1] Implementar endpoint de classificação automática em submissions/pedro-henrique-silva/solution/app/api/classify/route.ts
- [x] T019 [US1] Implementar endpoint de registro de deflexão em submissions/pedro-henrique-silva/solution/app/api/deflection/route.ts
- [x] T020 [US1] Implementar criação de ticket (POST) em submissions/pedro-henrique-silva/solution/app/api/tickets/route.ts
- [x] T021 [US1] Implementar telemetria mínima de confiança/latência do fluxo em submissions/pedro-henrique-silva/solution/lib/observability.ts

**Checkpoint**: US1 funcional e validável isoladamente.

---

## Phase 4: User Story 2 - Diagnóstico executivo em minutos (Priority: P2)

**Goal**: Expor diagnóstico operacional em dashboard admin com dados reais processados offline.

**Independent Test**: Admin autenticado abre `/admin`, visualiza quatro blocos analíticos e card de deflexão sem recálculo em runtime.

### Implementation for User Story 2

- [x] T022 [P] [US2] Implementar script de download dos datasets via kagglehub em submissions/pedro-henrique-silva/solution/scripts/download_datasets.py
- [x] T023 [P] [US2] Implementar script de análise e geração de insights em submissions/pedro-henrique-silva/solution/scripts/analyze_datasets.py
- [x] T024 [P] [US2] Implementar script de carga da base vetorial em submissions/pedro-henrique-silva/solution/scripts/populate_kb.py
- [x] T025 [US2] Criar estrutura de insights no dashboard em submissions/pedro-henrique-silva/solution/components/InsightCards.tsx
- [x] T026 [US2] Implementar visualização heatmap/tabela de gargalos em submissions/pedro-henrique-silva/solution/components/HeatmapChart.tsx
- [x] T027 [US2] Implementar endpoint de leitura de insights para admin em submissions/pedro-henrique-silva/solution/app/api/insights/route.ts
- [x] T028 [US2] Implementar página dashboard admin em submissions/pedro-henrique-silva/solution/app/admin/page.tsx
- [x] T029 [US2] Versionar snapshot inicial de insights em submissions/pedro-henrique-silva/solution/public/insights.json

**Checkpoint**: US2 funcional e validável isoladamente.

---

## Phase 5: User Story 3 - Operação assistida por IA (Priority: P3)

**Goal**: Permitir acompanhamento e gestão operacional de tickets para cliente e admin.

**Independent Test**: Cliente vê seus tickets; admin vê todos, aplica filtros e atualiza status/prioridade com persistência.

### Implementation for User Story 3

- [x] T030 [US3] Implementar listagem de tickets do cliente em submissions/pedro-henrique-silva/solution/app/customer/tickets/page.tsx
- [x] T031 [US3] Implementar listagem e filtros de tickets admin em submissions/pedro-henrique-silva/solution/app/admin/tickets/page.tsx
- [x] T032 [US3] Implementar listagem de tickets (GET) com escopo por role em submissions/pedro-henrique-silva/solution/app/api/tickets/route.ts
- [x] T033 [US3] Implementar atualização de ticket (PATCH) para ações admin em submissions/pedro-henrique-silva/solution/app/api/tickets/route.ts
- [x] T034 [P] [US3] Implementar componentes de tabela/detalhe de ticket em submissions/pedro-henrique-silva/solution/components/TicketTable.tsx
- [x] T035 [P] [US3] Implementar componentes de filtros de tickets em submissions/pedro-henrique-silva/solution/components/TicketFilters.tsx

**Checkpoint**: US3 funcional e validável isoladamente.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Robustez final para demonstração e submissão.

- [x] T036 [P] Aplicar estados de loading/erro/sucesso nas jornadas em submissions/pedro-henrique-silva/solution/app/customer/new/page.tsx
- [x] T037 [P] Aplicar estados vazios e feedback operacional em submissions/pedro-henrique-silva/solution/app/admin/page.tsx
- [x] T038 Consolidar README final de execução local/deploy em submissions/pedro-henrique-silva/solution/README.md
- [x] T039 Atualizar narrativa de evidências de processo em submissions/pedro-henrique-silva/process-log/NOTES.md
- [x] T040 Executar checklist de compliance e registrar evidência em submissions/pedro-henrique-silva/docs/03-process-and-roi.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Sem dependências.
- **Phase 2 (Foundational)**: Depende da conclusão da Phase 1 e bloqueia todas as histórias.
- **Phase 3 (US1)**: Começa após Phase 2.
- **Phase 4 (US2)**: Começa após Phase 2; pode ocorrer em paralelo com US1 após base pronta.
- **Phase 5 (US3)**: Começa após Phase 2; preferencialmente após endpoints centrais de tickets da US1.
- **Phase 6 (Polish)**: Depende das histórias selecionadas concluídas.

### User Story Dependencies

- **US1 (P1)**: Independente após fundação; define o MVP mínimo demonstrável.
- **US2 (P2)**: Independente após fundação, depende apenas de `insights.json` gerado.
- **US3 (P3)**: Reusa domínio de tickets e auth; ideal executar após US1 consolidar criação de tickets.

### Within Each User Story

- Componentes de UI podem iniciar em paralelo com utilitários de suporte.
- Endpoints devem ser finalizados antes de integração plena da página.
- Validação de aceite deve ocorrer ao fechar cada história antes de avançar.

### Parallel Opportunities

- Setup: T003 e T004 podem rodar em paralelo após T001/T002.
- Foundation: T006, T007, T008, T010, T011 podem rodar em paralelo.
- US1: T013 e T014 em paralelo antes de T015.
- US2: T022, T023 e T024 em paralelo por responsáveis distintos.
- US3: T034 e T035 em paralelo enquanto T032/T033 evoluem.

---

## Parallel Example: User Story 1

```bash
# Paralelizar componentes da jornada de cliente
Task: "Implementar componente de gravação de áudio em submissions/pedro-henrique-silva/solution/components/VoiceRecorder.tsx"
Task: "Implementar componente de exibição de sugestão RAG em submissions/pedro-henrique-silva/solution/components/RagSuggestion.tsx"

# Paralelizar APIs independentes da jornada
Task: "Implementar endpoint de classificação automática em submissions/pedro-henrique-silva/solution/app/api/classify/route.ts"
Task: "Implementar endpoint de registro de deflexão em submissions/pedro-henrique-silva/solution/app/api/deflection/route.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Concluir Phase 1 e Phase 2.
2. Entregar US1 completa (T013-T021).
3. Validar critérios críticos de latência e deflexão.
4. Demonstrar fluxo cliente fim a fim.

### Incremental Delivery

1. Após MVP, adicionar US2 para prova de valor executivo.
2. Em seguida, adicionar US3 para completar ciclo operacional.
3. Finalizar com polish e compliance de submissão.

### Parallel Team Strategy

1. Pessoa A: infra/API base (Phase 2 + endpoints).
2. Pessoa B: telas cliente e admin.
3. Pessoa C: scripts offline e dados analíticos.

---

## Notes

- Cada tarefa referencia caminho explícito para execução assistida por IA.
- Tasks com `[P]` evitam conflito de arquivo e podem ser paralelizadas.
- US1 é a fronteira de MVP mínimo funcional para demo.
- Antes de cada push, validar se nada foi alterado fora de `submissions/pedro-henrique-silva/`.
