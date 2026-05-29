# Research - G4 Suporte Inteligente (MVP)

## Decision 1: Arquitetura unificada em Next.js + Supabase
- **Decision**: Usar Next.js App Router para frontend e backend serverless no mesmo projeto, com Supabase para auth, banco, storage e vetores.
- **Rationale**: Reduz fricção operacional, acelera entrega e simplifica deploy do MVP.
- **Alternatives considered**:
  - Backend separado (FastAPI/Express): aumenta overhead de setup e integração.
  - Banco local: inviabiliza autenticação e políticas RLS com pouca robustez.

## Decision 2: Deflexão com busca semântica + resposta guiada
- **Decision**: Usar embedding semântico para recuperar casos similares e gerar sugestão contextual com nível de confiança.
- **Rationale**: Mantém foco em prevenção de tickets com base em histórico real.
- **Alternatives considered**:
  - FAQ estático por keyword: menor precisão para linguagem natural variada.
  - Classificação direta sem contexto: perde explicabilidade por fontes similares.

## Decision 3: Pipeline analítico offline para dashboard
- **Decision**: Gerar `insights.json` antes do deploy por scripts Python.
- **Rationale**: Garante previsibilidade de demo, evita custos/latência de cálculo em runtime.
- **Alternatives considered**:
  - Cálculo online em tempo real: maior complexidade e risco de instabilidade.
  - Dashboard manual em documento: reduz credibilidade de produto funcional.

## Decision 4: Classificação automática com fallback
- **Decision**: Classificar categoria/prioridade automaticamente e tratar baixa confiança com fallback seguro.
- **Rationale**: Acelera triagem sem remover controle humano em cenários ambíguos.
- **Alternatives considered**:
  - Taxonomia manual no formulário: pior experiência de cliente.
  - Automação sem score de confiança: risco de erro silencioso.

## Decision 5: Escopo MVP focado em jornada completa
- **Decision**: Entregar fluxo fim a fim com 3 histórias: deflexão cliente, dashboard admin e gestão de tickets.
- **Rationale**: Maximiza percepção de valor com escopo controlado para prazo de challenge.
- **Alternatives considered**:
  - Priorizar apenas analytics: pareceria relatório e não produto.
  - Priorizar apenas operação de tickets: perderia diferencial de prevenção.

## Decision 6: Base vetorial inicial por amostragem
- **Decision**: Popular base vetorial com amostra representativa (3k-5k registros).
- **Rationale**: Equilíbrio entre qualidade de recuperação e custo de API em MVP.
- **Alternatives considered**:
  - Indexar 100% dos dados no início: custo e tempo de processamento maiores.
  - Amostra muito pequena (<1k): risco de baixa cobertura de casos.

## Decision 7: Métricas-chave do MVP
- **Decision**: Monitorar taxa de deflexão, confiança média do RAG e top perguntas resolvidas sem ticket.
- **Rationale**: Evidencia diretamente o valor econômico da prevenção de chamados.
- **Alternatives considered**:
  - Métricas genéricas de pageview: não demonstram impacto operacional.
  - Apenas tempo médio de atendimento: mede processamento, não prevenção.
