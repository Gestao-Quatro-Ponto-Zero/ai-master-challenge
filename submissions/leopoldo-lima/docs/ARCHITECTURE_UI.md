# Architecture UI

## Objetivo
Documentar a arquitetura atual do frontend (UI shell) e seus limites no snapshot corrente.

## Baseline atual (frontend UI shell simplificado)
- stack de runtime: HTML + CSS + JavaScript em `public/`
- branding de produto: **Focus Score Cockpit**
- servidor da UI: o próprio backend FastAPI (`src/api/app.py`) servindo estáticos
- sem build step frontend dedicado (sem `npm`, `vite` ou `react` neste snapshot)
- fluxo principal: formulário de filtros -> listagem -> detalhe

## Componentes e responsabilidades
- `public/index.html`
  - estrutura da página, formulário de filtros e áreas de listagem/detalhe
- `public/styles.css`
  - estilos básicos da UI shell
- `public/app.js`
  - estado de tela e integração com contrato de repositório
  - não importa implementação concreta de dados
- `public/application/contracts/opportunity-repository.js`
  - contrato mínimo da camada de dados consumido pela UI
- `public/infrastructure/repositories/*`
  - implementações concreta API/mock e factory de seleção
- `public/presentation/hooks/use-dashboard-data.js`
  - coordena carregamento do dashboard com retry/cancelamento
- `public/shared/query/query-keys.js`
  - padroniza query keys da UI
- `src/api/app.py`
  - `GET /` entrega `index.html`
  - `app.mount("/ui", StaticFiles(...))` disponibiliza assets

## Contrato de integração UI/API
- contrato canônico: `docs/API_CONTRACT_UI.md`
- filtros e execução server-side: `docs/FILTER_EXECUTION_MODEL.md`
- estados de erro/observabilidade: `docs/OBSERVABILITY_INTEGRATION.md`
- estratégia de repositório: `docs/REPOSITORY_STRATEGY.md`
- estratégia de queries/dashboard: `docs/QUERY_STRATEGY.md`

## Limitações conhecidas
- UI atual é shell funcional e intencionalmente simples (sem framework de componentes)
- mensagens de erro de UI são genéricas e focadas em UX mínima
- ausência de pipeline de build frontend separado (adequado ao estágio atual, mas limitado para evolução)

## Convenções de ownership e evolução
- mudanças visuais e de fluxo em `public/`
- mudanças de contrato apenas após atualização coordenada de:
  - `src/api/contracts.py`
  - `docs/API_CONTRACT_UI.md`
  - testes de contrato (`tests/test_api_contract.py`)
- qualquer alteração de onboarding/execução deve refletir em:
  - `README.md`
  - `docs/SETUP.md`
  - `PROCESS_LOG.md`
