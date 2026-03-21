# PROCESS LOG

### Nota — pacote de submissão (`ai-master-challenge`)

- **README principal do candidato:** `submissions/leopoldo-lima/README.md` — inclui **hipóteses**, **sanity checks do score** (com referência ao JSON `crp-real-09-dashboard-kpis.json`) e **síntese do uso de IA** para leitura rápida do avaliador.
- **Este arquivo (canónico):** `submissions/leopoldo-lima/process-log/PROCESS_LOG.md` (já não há cópia duplicada em `solution/`); detalhe **por CRP** e evidências ligadas a cada passo.
- **Evidências entregues:** pasta `submissions/leopoldo-lima/process-log/` (export de conversas, JSON de fluxo, notas, CRPs, imagens). **`solution/artifacts/process-log/`** serve só para **saídas de scripts** ao correr a solução localmente.

---

## Perspectiva analítica antes da execução

Antes de escalar implementação com IA, a pergunta de produto foi: **como ajudar o comercial a decidir onde agir agora**, e não apenas como ordenar o pipeline por valor ou celebrar deals já fechados. Isso levou a uma hipótese central: **o score precisava favorecer o pipeline aberto** e tratar `Won` como sinal histórico útil, mas **não** como centro da priorização operacional.

Daí vieram algumas decisões humanas que moldaram toda a execução:

- o **dataset oficial** do challenge foi tratado como **fonte de verdade** do runtime;
- `mock` ficou restrito a **fallback controlado** para desenvolvimento e testes, não como base silenciosa da demo;
- a explicação do score precisava sair do jargão da engine e virar **linguagem comercial**, com fatores, riscos e próxima ação;
- a recalibração do score teve de passar por **sanity checks** contra os totais reais do pipeline e contra o risco de inflar artificialmente oportunidades `Won`;
- a IA foi usada para **decompor, propor e acelerar**, mas as **hipóteses de produto**, a **correção de rumo** e o **critério de aceite** ficaram do lado humano.

Esta secção existe para responder, logo no início: **onde houve pensamento antes da execução assistida por IA**.

---

## Visão geral

Este arquivo regista a execução dos CRPs neste *workspace*: objetivos, uso de IA (quando aplicável), decisões, erros, correções humanas e **ligação a evidências** reproduzíveis. Complementa o `LOG.md` (changelog operacional).

### Contexto fixo do pacote

- **Desafio:** `003 - Lead Scorer`
- **Dados:** podem não estar versionados no repositório; declarar no README e nas limitações o que foi usado.
- **Nota:** este repo pode ser *Challenge Pack* (metodologia + referência) ou evoluir para produto; o log deve descrever a realidade verificável em cada momento.

---

## Como usar este arquivo

1. Para **cada CRP** (ou para cada iteração significativa dentro do mesmo CRP), copie o [Template padrão](#template-padrão-por-crp) para uma nova secção `### CRP-XXX — …`.
2. Preencha todos os campos; use *nenhuma* / *N/A* quando fizer sentido.
3. **Monorepo de trabalho:** guarde capturas, exports de chat e logs de teste em `artifacts/process-log/` sob `solution/` ao desenvolver. **Neste pacote de submissão,** o destino auditável é `process-log/` ao lado de `solution/` (ver `process-log/README.md` e `solution/artifacts/process-log/README.md`).
4. No fecho do CRP, inclua referência ao **PR** (número ou URL).

**Guia detalhado:** `docs/PROCESS_LOG_GUIDE.md`  
**Estratégia de submissão:** `docs/SUBMISSION_STRATEGY.md`  
**Governança de CRPs:** `docs/CRP_GOVERNANCE.md`

---

## Template padrão por CRP

Copie o bloco abaixo e substitua os valores.

```markdown
### CRP-XXX — <título curto> — <YYYY-MM-DD>

| Campo | Conteúdo |
|--------|-----------|
| **Data** | YYYY-MM-DD |
| **CRP** | CRP-XXX |
| **Problema** | |
| **Decomposição / subpassos** | |
| **Hipótese inicial** | |
| **Ferramenta de IA usada** | |
| **Prompt** | |
| **Resposta recebida** | |
| **Erro / limitação detectada** | |
| **Julgamento / correção humana** | |
| **Evidência associada** | |
| **Resultado final** | |
| **Número de iterações** | |
| **PR** | |
```

---

## Entradas (formato padronizado)

### CRP-API-04 — Implementar repositório HTTP de oportunidades (Python) — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-API-04 |
| **Problema** | Faltava implementação concreta de repositório para encapsular listagem/detalhe/KPIs/filtros via `ApiClient`, com mapeamento de erros de transporte para erros de domínio de integração. |
| **Hipótese inicial** | Criar `ApiOpportunityRepository` como ponto único de acesso ao backend HTTP aumentaria testabilidade e reduziria acoplamento da camada de aplicação com detalhes do cliente. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-API-04` para implementar repositório HTTP com testes e documentação de responsabilidades. |
| **Resposta recebida** | Proposta de repositório em `src/infrastructure/repositories/`, exceções de domínio (`OpportunityNotFoundError`, `OpportunityRepositoryError`), testes com cliente fake e matriz erro->comportamento em `docs/API_REPOSITORY.md`. |
| **Erro / limitação detectada** | Sem erro bloqueante durante implementação; principal risco era deixar o repositório vazando exceções de transporte para camadas superiores. |
| **Correção humana** | Revisão para garantir encapsulamento de exceções: `404` mapeado para `OpportunityNotFoundError` e demais `ApiClientError` para `OpportunityRepositoryError`, validado por testes dedicados. |
| **Evidência associada** | `src/infrastructure/repositories/api_opportunity_repository.py`, `src/infrastructure/repositories/__init__.py`, `tests/test_api_opportunity_repository.py`, `docs/API_REPOSITORY.md`, `README.md`, `python -m pytest -q tests/test_api_opportunity_repository.py tests/test_api_client.py`, `python -m ruff check src/infrastructure/repositories/api_opportunity_repository.py src/infrastructure/repositories/__init__.py tests/test_api_opportunity_repository.py`, `python -m ruff format --check src/infrastructure/repositories/api_opportunity_repository.py src/infrastructure/repositories/__init__.py tests/test_api_opportunity_repository.py`, `LOG.md`. |
| **Resultado final** | Repositório HTTP de oportunidades entregue com operações principais e tratamento de erro padronizado, validado por testes de sucesso e falhas comuns. |
| **Número de iterações** | 1 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-API-03 — Criar DTOs e mappers (Python) — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-API-03 |
| **Problema** | A API tinha contrato tipado, mas faltava camada explícita de DTO wire + mappers dedicados para separar payload JSON de borda do contrato interno validado. |
| **Hipótese inicial** | Criar DTOs em `infrastructure/http` e mappers pequenos para listagem/detalhe reduziria acoplamento e deixaria claras decisões de coerção/campos legados. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-API-03` para implementar DTOs/mappers e testes de borda. |
| **Resposta recebida** | Proposta de `dtos.py` e `mappers.py` com fallback de `nextBestAction -> next_action`, integração em `src/api/app.py`, testes de mapeamento e documentação dedicada. |
| **Erro / limitação detectada** | Sem erro bloqueante; principal cuidado foi manter coerência com o contrato do `CRP-API-01` e não duplicar lógica de negócio nos mappers. |
| **Correção humana** | Revisão dos mappers para ficarem somente na tradução/validação estrutural e revalidação cruzada com `tests/test_api_contract.py` para garantir compatibilidade de contrato na API. |
| **Evidência associada** | `src/infrastructure/http/dtos.py`, `src/infrastructure/http/mappers.py`, `src/api/app.py`, `tests/test_http_mappers.py`, `tests/test_api_contract.py`, `docs/API_DTO_MAPPERS.md`, `README.md`, `python -m pytest -q tests/test_http_mappers.py tests/test_api_contract.py`, `python -m ruff check src/api/app.py src/infrastructure/http/dtos.py src/infrastructure/http/mappers.py tests/test_http_mappers.py`, `python -m ruff format --check src/api/app.py src/infrastructure/http/dtos.py src/infrastructure/http/mappers.py tests/test_http_mappers.py`, `LOG.md`. |
| **Resultado final** | DTOs e mappers explícitos implantados com cobertura de casos felizes/borda e integração ativa na API sem quebrar o contrato existente. |
| **Número de iterações** | 1 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-API-02 — Criar cliente HTTP (Python) para a API da UI — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-API-02 |
| **Problema** | Chamadas HTTP para contrato UI/API não tinham uma camada Python centralizada para base URL, timeout, headers comuns e tratamento consistente de erro. |
| **Hipótese inicial** | Implementar cliente `httpx` dedicado com configuração por ambiente e exceções de integração reduziria acoplamento e facilitaria testes de contrato. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-API-02` para criar API client Python com tratamento de erro e documentação. |
| **Resposta recebida** | Proposta de `ApiClient` + `ApiClientConfig.from_env()`, exceções específicas, testes com `httpx.MockTransport` e documentação operacional do cliente. |
| **Erro / limitação detectada** | Primeira validação tentou aplicar `ruff` em `.env.example` (sintaxe inválida para parser Python) e houve ajuste de ordenação de imports no cliente. |
| **Correção humana** | Escopo do lint corrigido para arquivos Python apenas e aplicação de `ruff --fix` no cliente antes da revalidação final de testes. |
| **Evidência associada** | `src/infrastructure/http/api_client.py`, `src/infrastructure/http/errors.py`, `src/infrastructure/http/__init__.py`, `src/infrastructure/__init__.py`, `tests/test_api_client.py`, `docs/API_CLIENT.md`, `.env.example`, `pyproject.toml`, `README.md`, `python -m pytest -q tests/test_api_client.py tests/test_api_contract.py`, `python -m ruff check src/infrastructure/http/api_client.py src/infrastructure/http/errors.py src/infrastructure/http/__init__.py tests/test_api_client.py`, `python -m ruff format --check src/infrastructure/http/api_client.py src/infrastructure/http/errors.py src/infrastructure/http/__init__.py tests/test_api_client.py`, `LOG.md`. |
| **Resultado final** | Cliente HTTP Python centralizado entregue com timeout, mapeamento de erro e configuração por ambiente, validado por testes de sucesso, erro 404 e timeout. |
| **Número de iterações** | 2 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-API-01 — Definir contrato HTTP entre UI e backend — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-API-01 |
| **Problema** | O contrato atual estava centrado em `/api/ranking` e não formalizava os endpoints mínimos da trilha UI/API (`/api/opportunities`, `dashboard/kpis`, `dashboard/filter-options`) com modelos explícitos de resposta/erro para validação. |
| **Hipótese inicial** | Definir endpoints canônicos + modelos Pydantic + documentação dedicada reduziria deriva entre o que a UI consome e o que o backend Python serve. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-API-01` para formalizar contrato HTTP UI/backend antes de consolidar clientes/DTOs. |
| **Resposta recebida** | Proposta de criar `src/api/contracts.py`, adicionar endpoints de dashboard em `src/api/app.py`, manter `/api/ranking` por compatibilidade e documentar em `docs/API_CONTRACT_UI.md` + ADR. |
| **Erro / limitação detectada** | Ajustes de estilo/lint no `src/api/app.py` (ordem de imports e linhas longas) após adicionar novos endpoints e response models. |
| **Correção humana** | Aplicado `ruff` + refatoração manual de linhas longas e revalidação com `pytest` para garantir alinhamento real UI/API. |
| **Evidência associada** | `src/api/contracts.py`, `src/api/app.py`, `tests/test_api_contract.py`, `docs/API_CONTRACT_UI.md`, `docs/API_CONTRACT.md`, `docs/ADR/0004-ui-api-http-contract.md`, `README.md`, `python -m pytest -q tests/test_api_contract.py`, `python -m ruff check src/api/app.py src/api/contracts.py tests/test_api_contract.py`, `python -m ruff format --check src/api/app.py src/api/contracts.py tests/test_api_contract.py`, `LOG.md`. |
| **Resultado final** | Contrato HTTP canônico UI/API formalizado e validado por testes de contrato, com compatibilidade legada preservada e documentação/ADR alinhados à submissão. |
| **Número de iterações** | 2 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-D10 — Runbook de dados e evidência para submissão — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-D10 |
| **Problema** | Faltava um runbook de dados direto para avaliador reproduzir ingestão/validação/score sem inferência manual, além de evidência consolidada de fluxo raw -> core -> gold -> score. |
| **Hipótese inicial** | Documentar comandos Python em ordem operacional e gerar artefato de evidência por script reproduzível aumentaria transparência e reduziria risco de erro na avaliação. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-D10` para runbook operacional dos dados e evidências de submissão. |
| **Resposta recebida** | Proposta de `docs/RUNBOOK_DATA.md`, script `scripts/run_data_runbook.py` e integração no task runner para geração automatizada de evidência em `artifacts/data-validation/`. |
| **Erro / limitação detectada** | Limitação de ambiente para provar execução remota de CI; validação foi feita por espelho local completo dos comandos documentados no runbook. |
| **Correção humana** | Revisão de paths/comandos do runbook, execução manual de `python scripts/run_data_runbook.py`, execução via `python scripts/tasks.py runbook-data` e validação final com `python scripts/tasks.py build`. |
| **Evidência associada** | `docs/RUNBOOK_DATA.md`, `scripts/run_data_runbook.py`, `scripts/tasks.py`, `artifacts/data-validation/runbook-data-evidence.json`, `artifacts/data-validation/runbook-data-evidence.md`, `artifacts/data-validation/raw-schema-summary.json`, `artifacts/data-validation/metadata-coverage-report.json`, `artifacts/data-validation/referential-integrity-report.json`, `README.md`, `LOG.md`, `python scripts/run_data_runbook.py`, `python scripts/tasks.py runbook-data`, `python scripts/tasks.py build`. |
| **Resultado final** | Runbook de dados executável e validado, com evidência material reproduzível e comandos sincronizados com README/submissão. |
| **Número de iterações** | 1 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-D09 — Testes de dados e quality gates no CI — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-D09 |
| **Problema** | O workflow de CI já tinha gates gerais, mas não barrava explicitamente regressões críticas de dados/modelagem (qualidade, normalização, integridade referencial e features). |
| **Hipótese inicial** | Tornar esses gates etapas nomeadas no job de qualidade aumentaria fail-fast e deixaria claro, para o avaliador, qual proteção falhou. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-D09` para reforçar quality gates de dados no CI com stack Python. |
| **Resposta recebida** | Proposta de ampliar `.github/workflows/ci-pr.yml`, detalhar severidade em `docs/QUALITY_GATES.md` e atualizar README com status/interpretação de falhas. |
| **Erro / limitação detectada** | Ao rodar espelho local dos gates do CI, `mypy` falhou em `src/api/view_models.py` (tipagem de `float` e serialização), revelando regressão real de tipagem introduzida no CRP anterior. |
| **Correção humana** | Refatoração de `_to_float` e assinatura de serialização em `view_models.py`, seguida de nova execução dos gates críticos (`typecheck`, `test`, `contract`, `data-quality`, `normalization`, `referential-integrity`, `features`) até verde. |
| **Evidência associada** | `.github/workflows/ci-pr.yml`, `docs/QUALITY_GATES.md`, `README.md`, `src/api/view_models.py`, `python scripts/tasks.py lint`, `python scripts/tasks.py format`, `python scripts/tasks.py typecheck`, `python scripts/tasks.py test`, `python scripts/tasks.py contract`, `python scripts/tasks.py data-quality`, `python scripts/tasks.py normalization`, `python scripts/tasks.py referential-integrity`, `python scripts/tasks.py features`, `LOG.md`. |
| **Resultado final** | CI passou a bloquear regressões de dados/modelagem com etapas explícitas e auditáveis; espelho local validou comportamento de gate não decorativo. |
| **Número de iterações** | 2 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-D08 — View models para produto e explicabilidade — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-D08 |
| **Problema** | O contrato de API retornava campos técnicos dispersos para score e explicação, exigindo transformação no cliente e elevando risco de payload pouco coeso para vendedor. |
| **Hipótese inicial** | Introduzir view models explícitos (lista, detalhe e explicação) no backend geraria payload orientado a produto, com prioridade e fatores já prontos para consumo. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-D08` para modelagem de payload e testes de serialização em Python. |
| **Resposta recebida** | Proposta de `src/api/view_models.py`, integração no `src/api/app.py`, documentação dedicada em `docs/VIEW_MODELS.md` e novos testes de serialização/contrato. |
| **Erro / limitação detectada** | Tentativa inicial de lint com alvo amplo retornou ruído não relacionado ao escopo; necessidade de validar lint apenas nos arquivos Python alterados. |
| **Correção humana** | Escopo de lint/formatação refinado para os arquivos do CRP; validação final com `pytest` e `ruff` focados nos contratos/view models. |
| **Evidência associada** | `src/api/view_models.py`, `src/api/app.py`, `tests/test_view_models.py`, `tests/test_api_contract.py`, `docs/VIEW_MODELS.md`, `docs/API_CONTRACT.md`, `python -m pytest -q tests/test_view_models.py tests/test_api_contract.py`, `python -m ruff check src/api/view_models.py src/api/app.py tests/test_view_models.py tests/test_api_contract.py`, `python -m ruff format --check src/api/view_models.py src/api/app.py tests/test_view_models.py tests/test_api_contract.py`, `LOG.md`, `README.md`. |
| **Resultado final** | API passou a entregar payload coeso para produto com explainability pronta no backend, incluindo banda de prioridade e próxima ação, sem exposição de campos crus desnecessários. |
| **Número de iterações** | 2 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-D07 — Camada de features para scoring — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-D07 |
| **Problema** | O scoring ainda operava majoritariamente em campos crus, sem catálogo formal de features interpretáveis com cobertura de stage/datas/joins/nulls. |
| **Hipótese inicial** | Criar módulo de feature engineering dedicado e fazer o motor consumir `OpportunityFeatureSet` aumentaria explainability e desacoplamento do CSV cru. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-D07` para camada de features do scoring. |
| **Resposta recebida** | Proposta de `src/features/engineering.py`, expansão de `OpportunityFeatureSet`, catálogo em Markdown e testes específicos. |
| **Erro / limitação detectada** | `ruff` apontou ordenação de imports no módulo de features na primeira execução. |
| **Correção humana** | Aplicado `ruff --fix`, revalidação de `tests/test_features.py` e `tasks.py build` completo. |
| **Evidência associada** | `src/features/engineering.py`, `src/domain/models.py`, `src/scoring/engine.py`, `tests/test_features.py`, `docs/FEATURE_CATALOG.md`, `python -m pytest -q tests\\test_features.py`, `python .\\scripts\\tasks.py build`, `README.md`, `docs/SETUP.md`, `LOG.md`. |
| **Resultado final** | Camada de features interpretáveis implantada e scoring preparado para consumir feature set, com testes cobrindo stage/datas/joins/nulls. |
| **Número de iterações** | 2 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-D06 — Metadata.csv como dicionário vivo do sistema — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-D06 |
| **Problema** | `metadata.csv` ainda não era usado para gerar dicionário auditável nem para evidenciar cobertura/lacunas contra o schema real dos CSVs. |
| **Hipótese inicial** | Automatizar geração de dicionário + relatório de cobertura metadata-vs-schema reduziria fragilidade documental e aumentaria transparência para avaliador externo. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-D06` para transformar metadata em artefato vivo e reproduzível. |
| **Resposta recebida** | Proposta de script `generate_data_dictionary.py`, saída Markdown em `docs/` e relatório JSON de cobertura em `artifacts/data-validation/`. |
| **Erro / limitação detectada** | Falhas de lint (`E402` e estilo) no script novo e no task runner após primeira integração. |
| **Correção humana** | Ajuste do import para escopo de `main()`, refatoração de linha longa e revalidação completa com `tasks.py build`. |
| **Evidência associada** | `scripts/generate_data_dictionary.py`, `docs/DATA_DICTIONARY.md`, `artifacts/data-validation/metadata-coverage-report.json`, `tests/test_data_dictionary.py`, `python .\\scripts\\generate_data_dictionary.py`, `python .\\scripts\\tasks.py build`, `README.md`, `docs/SETUP.md`, `LOG.md`. |
| **Resultado final** | Dicionário de dados reproduzível gerado a partir de metadata + schema real, com lacunas explícitas e cobertura versionada. |
| **Número de iterações** | 2 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-D05 — Modelos canônicos de domínio: raw, core e gold — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-D05 |
| **Problema** | Os modelos de domínio ainda não explicitavam camadas raw/core/gold nem mapeamento formal raw -> core para reduzir acoplamento ao CSV cru. |
| **Hipótese inicial** | Estruturar dataclasses por camadas + funções de transformação e testes dedicados estabilizaria contratos para scoring/API e facilitaria auditoria técnica. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-D05` para implementar modelos canônicos de domínio em Python. |
| **Resposta recebida** | Proposta de classes raw/core/gold, mapeamento explícito e documentação/ADR de decisão de camadas. |
| **Erro / limitação detectada** | Sem erro bloqueante de runtime; principal limitação foi manter nomenclatura clara sem quebrar consistência das camadas já existentes. |
| **Correção humana** | Revisão dos nomes de modelos e transformação `raw_opportunity_to_core` com normalização semântica aplicada, seguida de testes e build completo. |
| **Evidência associada** | `src/domain/models.py`, `tests/test_domain_models.py`, `docs/DOMAIN.md`, `docs/DATA_CONTRACT.md`, `docs/ADR/0003-domain-model-layers.md`, `python -m pytest -q tests\\test_domain_models.py`, `python .\\scripts\\tasks.py build`, `README.md`, `LOG.md`. |
| **Resultado final** | Modelos raw/core/gold canônicos implantados e mapeamento explícito validado, reduzindo dependência de CSV cru em camadas superiores. |
| **Número de iterações** | 1 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-D04 — Integridade referencial entre fato e dimensões — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-D04 |
| **Problema** | Faltava uma validação referencial explícita e classificável (blocking/warning) entre `sales_pipeline` e dimensões de contas/produtos/agentes. |
| **Hipótese inicial** | Criar validador dedicado com normalização de produto antes do join e relatório reproduzível elevaria confiabilidade do pipeline e da narrativa da demo. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-D04` para integridade referencial com classificação de desvios. |
| **Resposta recebida** | Proposta de módulo `src/integrity/referential.py`, entrypoint de validação, testes e documentação de taxas/achados. |
| **Erro / limitação detectada** | Ajustes de lint (`E501`/imports) em novos arquivos antes da validação final. |
| **Correção humana** | Refatoração de linhas longas/imports, execução de `ruff --fix` e revalidação com script + testes + build completo. |
| **Evidência associada** | `src/integrity/referential.py`, `scripts/validate_referential_integrity.py`, `tests/test_referential_integrity.py`, `docs/REFERENTIAL_INTEGRITY.md`, `artifacts/data-validation/referential-integrity-report.json`, `python .\\scripts\\validate_referential_integrity.py`, `python -m pytest -q tests\\test_referential_integrity.py`, `python .\\scripts\\tasks.py build`, `README.md`, `docs/SETUP.md`, `LOG.md`. |
| **Resultado final** | Joins críticos validados com sucesso, sobras de dimensão classificadas como warning e relatório legível para auditoria técnica. |
| **Número de iterações** | 2 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-D03 — Mapa de normalização semântica — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-D03 |
| **Problema** | Era necessário reconciliar divergência semântica de produto (`GTXPro` vs `GTX Pro`) sem editar o raw e com rastreabilidade auditável. |
| **Hipótese inicial** | Criar camada separada de normalização + mapa versionado + teste dedicado garantiria correção de join sem esconder a divergência original. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-D03` para normalização semântica controlada. |
| **Resposta recebida** | Proposta de `config/normalization-map.json`, `src/normalization/mapper.py`, testes de alias e documentação de regras/risco. |
| **Erro / limitação detectada** | `ruff` apontou ordenação de imports em `src/normalization/mapper.py` na primeira validação. |
| **Correção humana** | Aplicado `ruff --fix`, revalidação de testes de normalização e `tasks.py build` completo antes de encerrar. |
| **Evidência associada** | `config/normalization-map.json`, `src/normalization/mapper.py`, `tests/test_normalization.py`, `docs/NORMALIZATION_RULES.md`, `docs/ADR/0002-normalization-layer.md`, `python -m pytest -q tests\\test_normalization.py`, `python .\\scripts\\tasks.py build`, `README.md`, `docs/SETUP.md`, `LOG.md`. |
| **Resultado final** | Normalização semântica auditável implementada, com rastro original->canônico e caso obrigatório `GTXPro -> GTX Pro` coberto por teste. |
| **Número de iterações** | 2 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-D02 — Validar regras estruturais do dataset — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-D02 |
| **Problema** | Faltavam regras estruturais específicas do `sales_pipeline.csv` com severidade crítica e entrypoint único para validação reproduzível. |
| **Hipótese inicial** | Implementar validador dedicado com regras explícitas de `deal_stage`, datas e `close_value` elevaria confiabilidade da entrada para scoring/API. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-D02` para criar regras estruturais do dataset e testes. |
| **Resposta recebida** | Proposta de módulo `src/raw/data_quality.py`, script `scripts/validate_data_quality.py`, testes `pytest` e doc `docs/DATA_QUALITY_RULES.md`. |
| **Erro / limitação detectada** | Erro de lint (`E402`) no entrypoint por import após bootstrap de path; também houve ajuste de estilo para passar `ruff`. |
| **Correção humana** | Mover import para escopo de `main()`, manter tipagem explícita e reexecutar entrypoint + testes + build completo até verde. |
| **Evidência associada** | `src/raw/data_quality.py`, `scripts/validate_data_quality.py`, `tests/test_data_quality.py`, `docs/DATA_QUALITY_RULES.md`, `python .\\scripts\\validate_data_quality.py`, `python -m pytest -q tests\\test_data_quality.py`, `python .\\scripts\\tasks.py build`, `README.md`, `docs/SETUP.md`, `LOG.md`. |
| **Resultado final** | Regras estruturais críticas automatizadas, documentadas e validadas por entrypoint e testes reproduzíveis em Python. |
| **Número de iterações** | 2 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-D01 — Congelar o contrato raw dos CSVs — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-D01 |
| **Problema** | Faltavam camada raw explícita e snapshot reproduzível do schema dos 5 CSVs oficiais no estado atual do repositório. |
| **Hipótese inicial** | Criar módulo raw Python + script de inspeção + docs de fontes/contrato resolveria rastreabilidade da entrada sem inferência criativa. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-D01` para congelar contrato raw dos CSVs. |
| **Resposta recebida** | Proposta de `src/raw/reader.py`, `scripts/inspect_data.py`, `docs/DATA_SOURCES.md`, `docs/RAW_CONTRACT.md` e artefatos em `artifacts/data-validation/`. |
| **Erro / limitação detectada** | Erro inicial `ModuleNotFoundError: No module named 'src'` ao executar `inspect_data.py`; depois `ruff` apontou `E402` por import em posição inadequada. |
| **Correção humana** | Ajuste do bootstrap de path e import tardio no `main()` do script, seguido de correção/formatação via `ruff` e nova validação completa. |
| **Evidência associada** | `src/raw/reader.py`, `scripts/inspect_data.py`, `docs/DATA_SOURCES.md`, `docs/RAW_CONTRACT.md`, `artifacts/data-validation/raw-schema-summary.json`, `artifacts/data-validation/raw-schema-summary.md`, `python .\\scripts\\inspect_data.py`, `python .\\scripts\\tasks.py build`, `LOG.md`, `README.md`, `docs/SETUP.md`. |
| **Resultado final** | Contrato raw congelado com inspeção reproduzível e documentação coerente com os CSVs reais, sem renomeação de colunas na ingestão. |
| **Número de iterações** | 2 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-012 — Material de submissão e narrativa de avaliação — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-012 |
| **Problema** | O projeto estava tecnicamente robusto, mas faltava consolidação final da narrativa para avaliador externo (README de submissão, demo script e checklist objetivo). |
| **Hipótese inicial** | Reestruturar README com blocos de submissão forte + criar `docs/DEMO_SCRIPT.md` + preencher checklist do desafio deixaria o pacote mais competitivo e auditável. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-012` para material de submissão e narrativa final. |
| **Resposta recebida** | Proposta de narrativa em cinco blocos (summary/abordagem/resultado/recomendações/limitações), roteiro de demo 3-5 min e checklist com evidências concretas do repo. |
| **Erro / limitação detectada** | Sem erro técnico bloqueante; limitação prática de evidências visuais (screenshots) depende de captura manual fora do terminal. |
| **Correção humana** | Explicitar no texto as limitações reais e manter a narrativa ancorada em artefatos verificáveis, sem marketing vazio nem afirmações sem prova. |
| **Evidência associada** | `README.md`, `docs/DEMO_SCRIPT.md`, `docs/CHALLENGE_CHECKLIST.md`, `python .\\scripts\\tasks.py build`, `LOG.md`. |
| **Resultado final** | Material de submissão consolidado com linguagem objetiva, processo auditável e roteiro de demonstração replicável. |
| **Número de iterações** | 1 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-011 — Observabilidade mínima e rastreabilidade — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-011 |
| **Problema** | A API não tinha correlação de requests nem telemetria mínima para depuração auditável na demo. |
| **Hipótese inicial** | Middleware com `x-request-id`, logs JSON e métricas em memória em `/metrics` entregaria rastreabilidade útil sem overengineering. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-011` para adicionar observabilidade mínima ao serviço. |
| **Resposta recebida** | Proposta de middleware HTTP, endpoint de métricas, logs estruturados sanitizados e cobertura de teste para request ID/métricas. |
| **Erro / limitação detectada** | `ruff` acusou ordenação de imports em `src/api/app.py` após instrumentação inicial. |
| **Correção humana** | Aplicado `ruff --fix` e revalidação completa com `tasks.py build`; revisão manual para evitar log de payload sensível. |
| **Evidência associada** | `src/api/app.py`, `tests/test_api_contract.py`, `docs/OBSERVABILITY.md`, `README.md`, `python .\\scripts\\tasks.py build`, chamada manual com `x-request-id=obs-req-1`, `/metrics` com contadores, excerpt de logs JSON do servidor. |
| **Resultado final** | API com rastreabilidade de request, logs estruturados e telemetria mínima funcional, validada por teste automatizado e prova manual. |
| **Número de iterações** | 2 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-010 — Containerização, release e ambiente demo — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-010 |
| **Problema** | A demo dependia de setup local Python; faltava caminho containerizado com runbook para avaliador reproduzir sem acoplamento ao ambiente da equipa. |
| **Hipótese inicial** | Adicionar `Dockerfile` + `docker-compose.yml` + `RUNBOOK` com healthcheck e portas fixas reduziria fricção de avaliação. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-010` para containerização e ambiente demo. |
| **Resposta recebida** | Proposta de imagem Python slim, compose com healthcheck e guia de troubleshooting. |
| **Erro / limitação detectada** | `docker compose up --build -d` falhou por daemon Docker indisponível no ambiente atual (`pipe docker_engine` não encontrado). |
| **Correção humana** | Validação estrutural via `docker compose config`, documentação explícita da exceção no process log/runbook e manutenção de build local verde para garantir consistência do app. |
| **Evidência associada** | `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `docs/RUNBOOK.md`, `README.md`, `docs/SETUP.md`, saída de `docker --version`, `docker compose version`, `docker compose config`, `python .\\scripts\\tasks.py build`. |
| **Resultado final** | Artefatos de containerização e runbook prontos; execução final depende de daemon Docker ativo no host de avaliação. |
| **Número de iterações** | 2 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-009 — CI forte em PR — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-009 |
| **Problema** | Faltava pipeline de CI versionado para PR, então os quality gates dependiam apenas de execução manual local. |
| **Hipótese inicial** | Criar workflow de PR com jobs separados (qualidade e segurança) reproduzindo os comandos locais reduziria risco de regressão antes de merge. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-009` para implantar CI forte em PR. |
| **Resposta recebida** | Proposta de GitHub Actions com `actions/setup-python`, cache `pip`, execução dos gates e upload do SBOM como artefato. |
| **Erro / limitação detectada** | Não foi possível gerar link/ID de run neste ambiente sem remoto conectado; validação ficou local + workflow versionado. |
| **Correção humana** | Registrar explicitamente a limitação no process log e manter README/docs apontando para `Actions` do remoto para validação em PR real. |
| **Evidência associada** | `.github/workflows/ci-pr.yml`, `docs/QUALITY_GATES.md`, `README.md`, `python .\\scripts\\tasks.py build`, `LOG.md`. |
| **Resultado final** | Pipeline de PR criado com gates completos e artefato SBOM, pronto para execução em repositório remoto. |
| **Número de iterações** | 1 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-008 — Quality gates, segurança e dependências — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-008 |
| **Problema** | O fluxo tinha testes/build, mas faltavam gates explícitos de lint/format/typecheck/security, hooks locais e evidência de dependências/SBOM. |
| **Hipótese inicial** | Integrar `ruff`, `mypy`, `pip-audit`, `pre-commit` e SBOM no task runner consolidaria disciplina automatizada para avaliação e CI futuro. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-008` para quality gates, segurança e dependências. |
| **Resposta recebida** | Proposta de novos comandos em `scripts/tasks.py`, docs dedicadas e configuração de hooks (`.pre-commit-config.yaml`). |
| **Erro / limitação detectada** | `ruff` falhou inicialmente (imports/linhas longas) e `pip-audit` no ambiente global trouxe ruído de pacotes não relacionados ao projeto. |
| **Correção humana** | Ajuste de código para padrão `ruff`, escopo de auditoria movido para `requirements-audit.txt` e reexecução dos gates até verde. |
| **Evidência associada** | `docs/QUALITY_GATES.md`, `.pre-commit-config.yaml`, `pyproject.toml`, `requirements-audit.txt`, `scripts/tasks.py`, `artifacts/security/sbom.json`, execução de `tasks.py lint/format/typecheck/security/sbom/build`, instalação `pre-commit`. |
| **Resultado final** | Gates de qualidade e segurança reproduzíveis, SBOM gerado e documentação operacional alinhada ao estado real do repositório. |
| **Número de iterações** | 3 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-007 — Qualidade: testes de unidade, integração e smoke — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-007 |
| **Problema** | A suíte existente cobria base funcional, mas faltava estratégia formal de testes e casos adicionais de integração/smoke para reduzir risco de regressão silenciosa. |
| **Hipótese inicial** | Documentar estratégia + reforçar testes de API/UI com cenários negativos manteria o fluxo crítico auditável para submissão. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-007` para consolidar qualidade e testes. |
| **Resposta recebida** | Proposta de `docs/TEST_STRATEGY.md`, expansão de testes de filtro na API e validação da rota raiz/404 de assets UI. |
| **Erro / limitação detectada** | Sem falhas bloqueantes; limitação de cobertura E2E com navegador real mantida fora de escopo por enquanto. |
| **Correção humana** | Revisão dos casos para garantir utilidade (não cosmética) e alinhamento com comando único de execução (`python -m pytest -q`). |
| **Evidência associada** | `docs/TEST_STRATEGY.md`, `tests/test_api_contract.py`, `tests/test_ui_smoke.py`, `README.md`, `python -m pytest -q`, `python .\\scripts\\tasks.py build`, `LOG.md`. |
| **Resultado final** | Suíte mínima reforçada e estratégia publicada, com execução verde reproduzível localmente e alinhada à narrativa de qualidade automatizada. |
| **Número de iterações** | 1 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-006 — UI shell e fluxo principal — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-006 |
| **Problema** | Havia API funcional, mas faltava interface visual para ranking, filtros e detalhe no fluxo principal de demo. |
| **Hipótese inicial** | Criar shell UI estático (`public/`) servido pela API FastAPI permitiria validar fluxo principal sem introduzir stack frontend adicional. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-006` para materializar UI e integração com API real. |
| **Resposta recebida** | Proposta de `index.html`, `styles.css`, `app.js` com loading/erro/vazio, filtros e detalhe por ID consumindo endpoints existentes. |
| **Erro / limitação detectada** | Sem bloqueio técnico; limitação de evidência visual persistente (screenshots) não foi automatizada neste ambiente CLI. |
| **Correção humana** | Validação manual de assets servidos em `GET /`, `GET /ui/styles.css`, `GET /ui/app.js` e manutenção de smoke test em `pytest` para integração de rotas. |
| **Evidência associada** | `public/index.html`, `public/styles.css`, `public/app.js`, `src/api/app.py`, `tests/test_ui_smoke.py`, `python .\\scripts\\tasks.py test`, `python .\\scripts\\tasks.py build`, smoke HTTP manual em porta 8792 com status 200 dos assets. |
| **Resultado final** | Fluxo principal de UI disponível e integrado à API de ranking/detalhe, com estados básicos e validação automatizada/manual. |
| **Número de iterações** | 1 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-005 — API/serviço de ranking e detalhe — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-005 |
| **Problema** | O motor de scoring existia, mas ainda não estava exposto como interface HTTP consumível para demo/avaliação. |
| **Hipótese inicial** | Implementar API FastAPI com endpoints de ranking e detalhe, mais testes de contrato, entregaria camada de produto verificável. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-005` para criar API de ranking/detalhe e documentação de contrato. |
| **Resposta recebida** | Proposta de `GET /api/ranking`, `GET /api/opportunities/{id}` e `GET /health`, com filtros básicos e payload explicável. |
| **Erro / limitação detectada** | Falha inicial ao testar em `127.0.0.1:8787` por restrição de bind no ambiente local (WinError 10013); lint também falhou por whitespace no contrato. |
| **Correção humana** | Tornar porta configurável via `LEAD_SCORER_PORT` e validar chamadas manuais em porta alternativa (`8791`); corrigido whitespace em `docs/API_CONTRACT.md`. |
| **Evidência associada** | `src/api/app.py`, `tests/test_api_contract.py`, `docs/API_CONTRACT.md`, `python .\\scripts\\tasks.py test`, `python .\\scripts\\tasks.py build`, chamadas HTTP manuais (`/health`, `/api/ranking?limit=2`, `/api/opportunities/OPP-001`) com retorno válido. |
| **Resultado final** | API funcional com contrato documentado, filtros básicos, testes verdes e evidência manual de consumo HTTP. |
| **Número de iterações** | 2 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-004 — Motor de scoring v0 — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-004 |
| **Problema** | O repositório ainda não tinha um motor de scoring explicável e testável em Python, apesar de isso ser núcleo da narrativa do challenge. |
| **Hipótese inicial** | Implementar engine isolada com pesos externos + testes `pytest` iniciais entregaria baseline determinístico sem espalhar lógica por UI. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-004` para criar motor de scoring v0. |
| **Resposta recebida** | Proposta de engine com retorno de `score`, `positives`, `negatives`, `risks` e `next_best_action`, com regras em JSON versionado. |
| **Erro / limitação detectada** | Nenhum erro de execução bloqueante; limitação reconhecida de regras heurísticas ainda não calibradas com histórico real. |
| **Correção humana** | Revisão dos pesos e mensagens explicativas para manter coerência com dataset e evitar afirmações de calibração inexistente. |
| **Evidência associada** | `src/scoring/engine.py`, `config/scoring-rules.json`, `tests/test_scoring_engine.py`, `docs/SCORING.md`, `python .\\scripts\\tasks.py test`, `python .\\scripts\\tasks.py build`, `README.md`, `LOG.md`. |
| **Resultado final** | Motor de scoring v0 ativo, determinístico e explicável, com testes verdes e documentação de uso/limitações. |
| **Número de iterações** | 1 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-003 — Modelo de domínio e contrato dos dados — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-003 |
| **Problema** | Não havia contrato de dados nem validação Python executável alinhada aos CSVs atuais do repositório. |
| **Hipótese inicial** | Criar contrato JSON + modelos de domínio + validador dedicado e integrar ao `tasks.py build` garantiria rastreabilidade e verificação real. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-003` para formalizar modelo e contrato de dados. |
| **Resposta recebida** | Proposta de contrato para `accounts`, `products`, `sales_teams`, `sales_pipeline` e `metadata`, com regras de PK/FK e campos obrigatórios. |
| **Erro / limitação detectada** | Primeira validação falhou por comportamento real do dataset: `account` vazio em parte do pipeline e alias `GTXPro` fora da dimensão de produtos. |
| **Correção humana** | Ajuste do contrato para `account` opcional, inclusão de normalização de alias `GTXPro -> GTX Pro` e documentação explícita das anomalias no contrato. |
| **Evidência associada** | `contracts/repository-data-contract.json`, `src/domain/models.py`, `scripts/validate_data_contract.py`, `docs/DATA_CONTRACT.md`, `python .\\scripts\\tasks.py contract`, `python .\\scripts\\tasks.py build`, `README.md`, `docs/REPO_MAP.md`, `docs/SETUP.md`, `LOG.md`. |
| **Resultado final** | Contrato e validação executável aprovados, com regras aderentes ao snapshot real e sem semântica inventada. |
| **Número de iterações** | 3 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-002 — Ambiente reproduzível e onboarding — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-002 |
| **Problema** | O Quick Start apontava para `scripts/tasks.ps1` e fluxo de API inexistentes no snapshot atual, impedindo onboarding reproduzível. |
| **Hipótese inicial** | Criar um trilho mínimo em Python (`pyproject.toml` + `scripts/tasks.py` + `docs/SETUP.md`) tornaria os comandos executáveis e auditáveis agora. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-002` para padronizar setup e onboarding. |
| **Resposta recebida** | Proposta de setup com comandos Python (`install`, `test`, `lint`, `typecheck`, `build`, `dev`) e atualização do README. |
| **Erro / limitação detectada** | Uso inicial de `&&` falhou no PowerShell local; lint também falhou por whitespace legado em `PROCESS_LOG.md`. |
| **Correção humana** | Ajuste da execução para sequência compatível com PowerShell e refinamento do lint para excluir `PROCESS_LOG.md` legado do gate. |
| **Evidência associada** | `pyproject.toml`, `scripts/tasks.py`, `docs/SETUP.md`, `README.md`, `LOG.md`, execução local de `python .\\scripts\\tasks.py install/test/lint/typecheck/build/dev`. |
| **Resultado final** | Onboarding documentado e validado com comandos reais no ambiente Windows + Python 3.13. |
| **Número de iterações** | 2 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-001 — Fundamentos do método no repo — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-001 |
| **Problema** | Faltavam os artefatos-base de domínio, arquitetura e ADR inicial exigidos pelo CRP. |
| **Hipótese inicial** | Criar os três documentos com foco em governança e submissão restabelece o trilho metodológico sem inventar stack inexistente. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-001` após o baseline (`CRP-000`). |
| **Resposta recebida** | Proposta de criação de `DOMAIN.md`, `ARCHITECTURE.md` e ADR inicial com guardrails de submissão. |
| **Erro / limitação detectada** | Referências históricas a arquitetura de código não comprovável no snapshot atual. |
| **Correção humana** | Redação dos artefatos no nível documental-operacional, aderente ao estado real do repositório. |
| **Evidência associada** | `docs/DOMAIN.md`, `docs/ARCHITECTURE.md`, `docs/ADR/0001-initial-architecture.md`, `LOG.md`, esta entrada em `PROCESS_LOG.md`. |
| **Resultado final** | Trilho documental e de decisão restabelecido para continuidade dos CRPs em sequência. |
| **Número de iterações** | 1 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-000 — Baseline, inventário e contrato do repositório — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-000 |
| **Problema** | O baseline e o mapa de repositório estavam ausentes no snapshot atual, apesar de serem requisitos explícitos da trilha principal. |
| **Hipótese inicial** | Reexecutar o CRP-000 no estado atual permitiria recuperar a rastreabilidade mínima e expor lacunas reais sem inventar artefatos. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Execução direta do `CRP-000` solicitada pelo usuário. |
| **Resposta recebida** | Proposta de inventário rápido, criação de `docs/BASELINE.md` e `docs/REPO_MAP.md`, e atualização de logs. |
| **Erro / limitação detectada** | Documentação previa citava artefatos técnicos não visíveis no snapshot atual do workspace. |
| **Correção humana** | Priorizar evidência do estado real em disco, registrar o descompasso e não simular estruturas ausentes. |
| **Evidência associada** | `docs/BASELINE.md`, `docs/REPO_MAP.md`, `LOG.md`, esta entrada em `PROCESS_LOG.md`. |
| **Resultado final** | Baseline e mapa recriados com inventário verificável; riscos de consistência documental explicitados. |
| **Número de iterações** | 1 |
| **PR** | *pendente — preencher no merge* |

---

### CRP-S01 — Estrutura do PROCESS_LOG e artefatos de submissão — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-S01 (e conjunto CRP-S01–S07 de governança) |
| **Problema** | PROCESS_LOG em formato de lista livre dificultava auditoria alinhada ao *submission guide* (prompt, evidência, PR). |
| **Hipótese inicial** | Um template em tabela reutilizável + guia em `docs/` + pasta de evidências cobre o requisito sem alterar contratos numéricos dos CRPs existentes. |
| **Ferramenta de IA usada** | Cursor (agente) |
| **Prompt** | Pedido do utilizador para robustecer governança, criar docs, `artifacts/process-log/` e CRPs pequenos CRP-Sxx. |
| **Resposta recebida** | Proposta de estrutura de arquivos, documentação em português e novos CRPs de submissão. |
| **Erro / limitação detectada** | Conteúdo legado anterior não tinha campos de prompt/iterações; não forçar reescrita retroativa de todo o histórico. |
| **Correção humana** | Preservar registos antigos na secção legado; novos trabalhos passam a usar o template. |
| **Evidência associada** | `docs/PROCESS_LOG_GUIDE.md`, `docs/SUBMISSION_STRATEGY.md`, `docs/CRP_GOVERNANCE.md`, `docs/README_SUBMISSION_SKELETON.md`, `docs/CHALLENGE_CHECKLIST.md`, `docs/IA_TRACE.md`, `artifacts/process-log/README.md`, `crps/CRP-S*.md`, `LOG.md`, `README.md`, `00-START-HERE.md` |
| **Resultado final** | Estrutura e template publicados; legado mantido abaixo para rastreabilidade histórica. |
| **Número de iterações** | 1 |
| **PR** | *pendente — preencher no merge* |

---

## Registros legados (formato anterior)

*As entradas abaixo conservam o histórico antes da padronização por tabela. Novos CRPs devem usar o [template](#template-padrão-por-crp).*

### CRP-000
- objetivo: congelar baseline auditavel do repositorio
- decisoes: documentar explicitamente que este repo e um pacote-base metodologico
- erros detectados: expectativa inicial de encontrar codigo de aplicacao, scripts e stack real
- correcoes: baseline passou a registrar ausencia de aplicacao como achado principal
- artefatos gerados:
  - `docs/BASELINE.md`
  - `docs/REPO_MAP.md`
  - `LOG.md`

### CRP-001
- objetivo: implantar o trilho documental e de decisao no repo
- decisoes: documentar o dominio e a arquitetura do pacote atual, nao de uma aplicacao inexistente
- erros detectados: templates poderiam induzir a uma arquitetura futura especulativa
- correcoes: ADR inicial formalizou o desacoplamento entre pacote-base e repo real de aplicacao
- artefatos gerados:
  - `docs/DOMAIN.md`
  - `docs/ARCHITECTURE.md`
  - `docs/ADR/0001-initial-architecture.md`
  - `PROCESS_LOG.md`
  - `.github/PULL_REQUEST_TEMPLATE.md`

### CRP-002
- objetivo: criar onboarding reproduzivel com comandos reais para este challenge pack
- decisoes: usar PowerShell em vez de introduzir `package.json`, `Makefile` ou dependencias inexistentes
- erros detectados: o CRP original pressupoe stack de aplicacao, mas este workspace continua documental
- correcoes: os comandos passaram a validar a estrutura e os contratos reais do repositorio; a invocacao foi ajustada para `.\scripts\tasks.ps1` apos validacao local
- artefatos gerados:
  - `.env.example`
  - `scripts/tasks.ps1`
  - `docs/SETUP.md`
  - atualizacao em `README.md`
  - atualizacao em `LOG.md`

### CRP-003
- objetivo: formalizar o contrato de dados real do challenge pack
- decisoes: tratar arquivos, IDs e relacionamentos entre artefatos como o modelo de dados valido deste workspace
- erros detectados: o CRP original pressupoe tabelas e DTOs de produto, mas o repositorio atual so possui dados estruturais de documentacao
- correcoes: o contrato foi modelado em `contracts/repository-data-contract.psd1` e plugado na validacao do `scripts/tasks.ps1`
- artefatos gerados:
  - `docs/DATA_CONTRACT.md`
  - `contracts/repository-data-contract.psd1`
  - atualizacao em `scripts/tasks.ps1`
  - atualizacao em `docs/SETUP.md`
  - atualizacao em `docs/REPO_MAP.md`
  - atualizacao em `README.md`
  - atualizacao em `LOG.md`

### CRP-004
- objetivo: construir um motor de scoring v0 simples, deterministico e explicavel
- decisoes: usar PowerShell como stack da implementacao de referencia e externalizar regras em `config/scoring-rules.psd1`
- erros detectados: o repositorio ainda nao possui dados reais de oportunidades, entao a engine precisou ser modelada como referencia metodologica
- correcoes: os sinais e payloads foram explicitados em `docs/SCORING.md` e validados por testes executaveis no ambiente atual
- artefatos gerados:
  - `src/LeadScorer.Engine.psm1`
  - `config/scoring-rules.psd1`
  - `tests/score-engine.tests.ps1`
  - `docs/SCORING.md`
  - atualizacao em `contracts/repository-data-contract.psd1`
  - atualizacao em `scripts/tasks.ps1`
  - atualizacao em `docs/SETUP.md`
  - atualizacao em `docs/REPO_MAP.md`
  - atualizacao em `docs/DATA_CONTRACT.md`
  - atualizacao em `README.md`
  - atualizacao em `LOG.md`

### CRP-005
- objetivo: expor a engine como servico HTTP consumivel por UI
- decisoes: usar `HttpListener` em PowerShell para manter endpoints reais sem introduzir stack externa neste workspace
- erros detectados: o carregamento inicial do dataset JSON gerou colecao aninhada, quebrando detalhe e validacao estrutural
- correcoes: a leitura do dataset foi ajustada no servico e no `tasks.ps1`; os testes de servico, HTTP e `typecheck` passaram apos a correcao
- artefatos gerados:
  - `data/demo-opportunities.json`
  - `src/LeadScorer.Service.psm1`
  - `src/LeadScorer.Api.psm1`
  - `scripts/start-api.ps1`
  - `docs/API_CONTRACT.md`
  - `tests/api-service.tests.ps1`
  - `tests/api-http.tests.ps1`
  - atualizacao em `contracts/repository-data-contract.psd1`
  - atualizacao em `scripts/tasks.ps1`
  - atualizacao em `README.md`
  - atualizacao em `docs/SETUP.md`
  - atualizacao em `docs/REPO_MAP.md`
  - atualizacao em `docs/DATA_CONTRACT.md`
  - atualizacao em `LOG.md`

### CRP-D01
- objetivo: congelar o contrato raw dos CSVs oficiais
- decisoes: criar uma camada raw explicita em `src/raw/` sem renomear colunas e usar PowerShell para gerar snapshot reproduzivel do schema
- erros detectados: a primeira versao do `inspect-data.ps1` tinha erros de parser e a camada raw precisou ser ajustada para resumir os datasets corretamente
- correcoes: o gerador de snapshot foi simplificado, a leitura raw foi estabilizada e os testes passaram com os cinco CSVs reais presentes em `data/`
- artefatos gerados:
  - `src/raw/LeadScorer.Raw.psm1`
  - `scripts/inspect-data.ps1`
  - `tests/raw-data.tests.ps1`
  - `docs/DATA_SOURCES.md`
  - `docs/RAW_CONTRACT.md`
  - `artifacts/data-validation/raw-schema-summary.json`
  - `artifacts/data-validation/raw-schema-summary.md`
  - atualizacao em `contracts/repository-data-contract.psd1`
  - atualizacao em `scripts/tasks.ps1`
  - atualizacao em `README.md`
  - atualizacao em `docs/SETUP.md`
  - atualizacao em `docs/REPO_MAP.md`
  - atualizacao em `LOG.md`

### CRP-D02
- objetivo: transformar caracteristicas observadas no `sales_pipeline.csv` em regras automatizadas de qualidade estrutural
- decisoes: manter a validacao em PowerShell, junto da camada raw, com regras pequenas e explicitas e comando dedicado `validate-data`
- verificacoes introduzidas:
  - unicidade de `opportunity_id`
  - enum valido de `deal_stage`
  - `Lost` com `close_value = 0`
  - `Won` com `close_value > 0` e `close_date`
  - `Engaging` com `engage_date` e sem `close_date`
  - `Prospecting` sem `close_date` e sem `close_value`
- correcoes: a validacao foi desenhada com base no comportamento real do dataset atual, que passou nessas seis regras sem ajustes no CSV
- artefatos gerados:
  - `src/raw/LeadScorer.DataQuality.psm1`
  - `scripts/validate-data.ps1`
  - `tests/data-quality.tests.ps1`
  - `docs/DATA_QUALITY_RULES.md`
  - atualizacao em `scripts/tasks.ps1`
  - atualizacao em `contracts/repository-data-contract.psd1`
  - atualizacao em `README.md`
  - atualizacao em `docs/SETUP.md`
  - atualizacao em `docs/REPO_MAP.md`
  - atualizacao em `LOG.md`

### CRP-D03
- objetivo: separar normalizacao semantica da camada raw e reconciliar divergencias conhecidas de join
- decisoes: manter o mapa de alias em configuracao versionada e expor uma camada separada em `src/normalization/`
- caso inaugural coberto: `GTXPro` no pipeline passa a casar com `GTX Pro` do catalogo sem editar CSV
- rastreabilidade adicionada:
  - valor original
  - valor canonico
  - estrategia aplicada
  - risco associado
- artefatos gerados:
  - `config/normalization-map.psd1`
  - `src/normalization/LeadScorer.Normalization.psm1`
  - `tests/normalization.tests.ps1`
  - `docs/NORMALIZATION_RULES.md`
  - atualizacao em `docs/ADR-0002-data-domain-alignment.md`
  - atualizacao em `contracts/repository-data-contract.psd1`
  - atualizacao em `scripts/tasks.ps1`
  - atualizacao em `README.md`
  - atualizacao em `docs/SETUP.md`
  - atualizacao em `docs/REPO_MAP.md`
  - atualizacao em `LOG.md`

### CRP-D04
- objetivo: validar integridade referencial entre o fato `sales_pipeline` e as dimensoes de contas, produtos e equipe
- decisoes: tratar orfao no fato como erro bloqueante, sobra de dimensão como `warning` e casos já observados e documentados como `expected`
- relacoes cobertas:
  - `sales_pipeline.account -> accounts.account`
  - `sales_pipeline.product -> products.product` via normalizacao
  - `sales_pipeline.sales_agent -> sales_teams.sales_agent`
- achados confirmados no snapshot atual:
  - contas batem quando `account` está preenchido
  - produtos batem após normalização
  - agentes batem no join crítico
  - 5 agentes existem na dimensão e não aparecem no pipeline
- artefatos gerados:
  - `src/integrity/LeadScorer.ReferentialIntegrity.psm1`
  - `scripts/validate-referential-integrity.ps1`
  - `tests/referential-integrity.tests.ps1`
  - `docs/REFERENTIAL_INTEGRITY.md`
  - `artifacts/data-validation/referential-integrity-report.json`
  - `artifacts/data-validation/referential-integrity-report.md`
  - atualizacao em `docs/ADR-0002-data-domain-alignment.md`
  - atualizacao em `contracts/repository-data-contract.psd1`
  - atualizacao em `scripts/tasks.ps1`
  - atualizacao em `README.md`
  - atualizacao em `docs/SETUP.md`
  - atualizacao em `docs/REPO_MAP.md`
  - atualizacao em `LOG.md`

### CRP-D05
- objetivo: explicitar modelos tipados `raw`, `core` e `gold` para parar de propagar nomes crus de CSV nas camadas superiores
- decisoes:
  - centralizar tipos e mapeamentos em `src/domain/LeadScorer.DomainModels.psm1`
  - manter `raw` como espelho fiel
  - promover `core` como contrato canônico de negócio
  - introduzir `gold` como contrato inicial para explainability e produto
- refatoracoes relevantes:
  - a integridade referencial deixou de depender de nomes crus do CSV e passou a operar sobre `Account`, `Product`, `SalesAgent` e `Opportunity`
  - o mapeamento `raw -> core` ficou explícito em código e em documentação
- testes introduzidos:
  - `tests/domain-models.tests.ps1`
  - regressao da integridade referencial sobre `core`
- artefatos atualizados:
  - `src/domain/LeadScorer.DomainModels.psm1`
  - `tests/domain-models.tests.ps1`
  - `docs/DOMAIN.md`
  - `docs/DATA_CONTRACT.md`
  - `docs/ADR-0002-data-domain-alignment.md`
  - `contracts/repository-data-contract.psd1`
  - `scripts/tasks.ps1`
  - `README.md`
  - `docs/SETUP.md`
  - `docs/REPO_MAP.md`
  - `LOG.md`

### Observações legadas sobre uso de IA
- o que foi gerado pela IA: primeira versao dos artefatos documentais
- o que foi corrigido pelo humano: direcao da execucao, escolha do CRP e validacao do contexto do repositorio
- o que foi descartado: qualquer suposicao sobre stack, API, frontend ou dados nao presentes
- como o julgamento humano alterou a direcao: priorizou registrar a realidade do pacote-base em vez de fingir um produto pronto

### Limitações finais (snapshot legado)
- o processo esta documentado, mas a aplicacao `Lead Scorer` continua ausente deste workspace
- CRPs de implementacao real dependem de outro repositorio ou de uma futura criacao de codigo aqui

### Próximos passos (snapshot legado)
- confirmar onde esta o repositorio real da aplicacao
- se este for apenas o pacote-base, aplicar `CRP-000` e `CRP-001` no repo de produto
- se este repo passar a ser o produto alvo, seguir para `CRP-D06` com aproximacao entre modelos `gold`, scoring e payloads de produto e, em paralelo, resolver a convivencia explicita entre as trilhas `CRP-xxx` e `CRP-Dxx`

---

## Observações globais (atualizar conforme o projeto evolui)

- **CRP:** CRP-API-05 — alternar mock/API por flag
- **Objetivo:** centralizar a decisão de runtime (mock vs API) em um único ponto de composição para evitar `if` espalhado.
- **Decisões técnicas:**
  - criar `create_opportunity_repository()` em `src/infrastructure/repositories/repository_factory.py`
  - default seguro para demo/local: `LEAD_SCORER_REPOSITORY_MODE=mock`
  - modo integração: `LEAD_SCORER_REPOSITORY_MODE=api` usando `ApiClientConfig.from_env()`
- **Artefatos alterados:**
  - `src/infrastructure/repositories/repository_factory.py`
  - `src/infrastructure/repositories/mock_opportunity_repository.py`
  - `src/infrastructure/repositories/__init__.py`
  - `tests/test_repository_factory.py`
  - `.env.example`
  - `docs/RUNTIME_MODES.md`
  - `README.md`
  - `LOG.md`
- **Validação humana executada:**
  - `python -m pytest -q tests/test_repository_factory.py tests/test_api_opportunity_repository.py`
  - `python -m ruff check src/infrastructure/repositories/repository_factory.py src/infrastructure/repositories/mock_opportunity_repository.py src/infrastructure/repositories/__init__.py tests/test_repository_factory.py`
  - `python -m ruff format --check src/infrastructure/repositories/repository_factory.py src/infrastructure/repositories/mock_opportunity_repository.py src/infrastructure/repositories/__init__.py tests/test_repository_factory.py`
- **Rastreabilidade IA e correções:**
  - IA propôs factory e mock repositório.
  - Revisão humana confirmou defaults por ambiente e exigiu documentação explícita de risco para evitar mock em produção.
- **Evidências obrigatórias:**
  - alternância comprovada por testes de factory (default/mock, api, modo inválido).
  - documentação operacional publicada em `docs/RUNTIME_MODES.md`.

- **Uso de IA:** consolidar prompts e correções relevantes também em `docs/` ou artefato dedicado ao fechar `CRP-S07`.
- **Submissão:** seguir `docs/SUBMISSION_STRATEGY.md` e checklist em `CRP-S04`.

- **CRP:** CRP-API-06 — plugar filtros reais na listagem
- **Objetivo:** mover busca/ordenacao da listagem para o servidor com serialização estável de query params no cliente Python.
- **Decisões técnicas:**
  - criar mapper dedicado `filters_to_query_params()` em `src/infrastructure/http/filter_params.py`
  - expandir `ApiClient.list_opportunities()` e `ApiOpportunityRepository.list_opportunities()` com `q`, `sort_by`, `sort_order` e params reservados de paginação
  - aplicar no backend (`/api/opportunities` e `/api/ranking` compat) filtros server-side de busca/ordenação
- **Artefatos alterados:**
  - `src/infrastructure/http/filter_params.py`
  - `src/infrastructure/http/api_client.py`
  - `src/infrastructure/repositories/api_opportunity_repository.py`
  - `src/api/app.py`
  - `tests/test_api_client.py`
  - `tests/test_api_contract.py`
  - `docs/FILTER_EXECUTION_MODEL.md`
  - `docs/API_CONTRACT_UI.md`
  - `docs/API_CLIENT.md`
  - `README.md`
  - `LOG.md`
- **Validação humana executada:**
  - `python -m pytest -q tests/test_api_contract.py tests/test_api_client.py`
  - `python -m ruff check src/api/app.py src/infrastructure/http/api_client.py src/infrastructure/http/filter_params.py src/infrastructure/repositories/api_opportunity_repository.py tests/test_api_contract.py tests/test_api_client.py`
  - `python -m ruff format --check src/api/app.py src/infrastructure/http/api_client.py src/infrastructure/http/filter_params.py src/infrastructure/repositories/api_opportunity_repository.py tests/test_api_contract.py tests/test_api_client.py`
- **Rastreabilidade IA e correções:**
  - IA propôs serialização de query estável e cobertura de busca/ordenação server-side.
  - Correção humana aplicada em teste de query (`request.url.query.decode()`) e ajuste de lint (quebra de linha para `E501`).
- **Evidências obrigatórias:**
  - teste de ordem/encoding da query no `ApiClient`
  - teste de busca + ordenação no endpoint canônico da listagem

- **CRP:** CRP-API-07 — estados de erro e observabilidade da integração
- **Objetivo:** tornar falhas de integração depuráveis e coerentes para UI/API com correlação por request id e mapeamento estável de erros.
- **Decisões técnicas:**
  - especializar erros do cliente HTTP para `404`, `422`, `5xx` e manter timeout separado
  - incluir `request_id` nas exceções de resposta para rastreio ponta a ponta
  - ampliar métricas com contadores por status (`status_404_total`, `status_422_total`, `status_500_total`)
- **Artefatos alterados:**
  - `src/infrastructure/http/errors.py`
  - `src/infrastructure/http/api_client.py`
  - `src/api/app.py`
  - `tests/test_api_client.py`
  - `tests/test_api_contract.py`
  - `docs/OBSERVABILITY_INTEGRATION.md`
  - `README.md`
  - `LOG.md`
- **Validação humana executada:**
  - `python -m pytest -q tests/test_api_contract.py tests/test_api_client.py`
  - `python -m ruff check src/api/app.py src/infrastructure/http/api_client.py src/infrastructure/http/errors.py tests/test_api_contract.py tests/test_api_client.py`
  - `python -m ruff format --check src/api/app.py src/infrastructure/http/api_client.py src/infrastructure/http/errors.py tests/test_api_contract.py tests/test_api_client.py`
- **Rastreabilidade IA e correções:**
  - IA propôs novos tipos de exceção e contadores por status.
  - revisão humana confirmou ausência de segredos em logs e ajuste fino de testes para validar propagação de `x-request-id` e retorno `422`.
- **Evidências obrigatórias:**
  - teste de `422` no contrato HTTP com `x-request-id` preservado
  - testes do `ApiClient` cobrindo `ApiClientNotFoundError`, `ApiClientValidationError`, `ApiClientServerError` e timeout

- **CRP:** CRP-API-08 — testes de contrato e simulação HTTP
- **Objetivo:** fortalecer proteção de contrato UI/API com simulação HTTP real no client Python e cenários de erro com significado.
- **Decisões técnicas:**
  - adotar `pytest-httpx` para simular integração HTTP no `ApiClient`
  - manter `tests/test_api_contract.py` como contrato do servidor e complementar com suíte de contrato do cliente
  - definir em `docs/API_TESTING.md` o que constitui quebra de contrato
- **Artefatos alterados:**
  - `pyproject.toml`
  - `requirements-audit.txt`
  - `tests/test_api_client_contract_http.py`
  - `docs/API_TESTING.md`
  - `docs/API_CLIENT.md`
  - `README.md`
  - `LOG.md`
- **Validação humana executada:**
  - `python -m pip install -e .[dev]`
  - `python -m pytest -q tests/test_api_client_contract_http.py tests/test_api_client.py tests/test_api_contract.py`
  - `python -m ruff check src/infrastructure/http/errors.py src/infrastructure/http/api_client.py tests/test_api_client_contract_http.py tests/test_api_client.py tests/test_api_contract.py`
  - `python -m ruff format --check src/infrastructure/http/errors.py src/infrastructure/http/api_client.py tests/test_api_client_contract_http.py tests/test_api_client.py tests/test_api_contract.py`
- **Rastreabilidade IA e correções:**
  - IA sugeriu fixture com URL sem query; falhou por mismatch no `pytest-httpx`.
  - correção humana: alinhar URLs mockadas com query string efetivamente serializada pelo client.
- **Evidências obrigatórias:**
  - suíte `pytest-httpx` cobrindo listagem, `404`, `422`, `500` e timeout
  - documentação de atualização de fixtures alinhada ao contrato em `docs/API_CONTRACT_UI.md`

- **CRP:** CRP-API-09 — remover acoplamento restante aos mocks
- **Objetivo:** garantir modo API como padrão e evitar carregamento acidental de módulos mock no runtime principal.
- **Decisões técnicas:**
  - trocar default de `LEAD_SCORER_REPOSITORY_MODE` para `api`
  - aplicar import lazy na factory para não carregar mock quando o modo é `api`
  - remover export de `MockOpportunityRepository` em `src/infrastructure/repositories/__init__.py`
- **Artefatos alterados:**
  - `src/infrastructure/repositories/repository_factory.py`
  - `src/infrastructure/repositories/__init__.py`
  - `tests/test_repository_factory.py`
  - `.env.example`
  - `docs/RUNTIME_MODES.md`
  - `docs/MOCK_DECOMMISSIONING.md`
  - `README.md`
  - `LOG.md`
- **Validação humana executada:**
  - `python -m pytest -q tests/test_repository_factory.py tests/test_api_opportunity_repository.py`
  - `python -m ruff check src/infrastructure/repositories/repository_factory.py src/infrastructure/repositories/__init__.py tests/test_repository_factory.py`
  - `python -m ruff format --check src/infrastructure/repositories/repository_factory.py src/infrastructure/repositories/__init__.py tests/test_repository_factory.py`
- **Rastreabilidade IA e correções:**
  - IA sugeriu manter import de mock no `__init__`; revisão humana removeu para evitar acoplamento implícito.
  - IA e humano confirmaram com teste dedicado que modo `api` não importa módulo de mock.
- **Evidências obrigatórias:**
  - teste `test_factory_api_mode_does_not_import_mock_module`
  - relatório `docs/MOCK_DECOMMISSIONING.md` com riscos residuais

- **CRP:** CRP-API-10 — runbook de integração front/back
- **Objetivo:** permitir execução reproduzível de UI contra backend Python com passos explícitos, variáveis e smoke E2E.
- **Decisões técnicas:**
  - criar runbook dedicado `docs/RUNBOOK_UI_API_INTEGRATION.md`
  - consolidar no runbook os modos `api`/`mock`, fluxo de subida, troubleshooting e checklist de smoke
  - alinhar documentação de entrada (`README.md` e `docs/SETUP.md`) para apontar ao novo runbook
- **Artefatos alterados:**
  - `docs/RUNBOOK_UI_API_INTEGRATION.md`
  - `README.md`
  - `docs/SETUP.md`
  - `LOG.md`
- **Validação humana executada:**
  - `python -m pytest -q tests/test_api_contract.py tests/test_ui_smoke.py`
  - revisão manual do checklist E2E e dos links documentais
- **Rastreabilidade IA e correções:**
  - IA sugeriu validação de documentação com `ruff` em arquivos Markdown; revisão humana descartou por ser inválido para `.md`.
  - ajuste aplicado: validação objetiva via smoke tests e revisão manual do texto/comandos.
- **Evidências obrigatórias:**
  - checklist smoke E2E no runbook
  - comandos reproduzíveis para `health`, listagem, detalhe e filtro

- **CRP:** CRP-UI-01 — baseline e governança do frontend
- **Objetivo:** congelar baseline atual da UI e formalizar governança/documentação da trilha frontend.
- **Decisões técnicas:**
  - documentar arquitetura de UI shell real em `docs/ARCHITECTURE_UI.md`
  - criar mapa de trilha frontend em `docs/REPO_MAP_UI.md`
  - manter stack atual (`public/` com HTML/CSS/JS) sem migração de tecnologia
- **Artefatos alterados:**
  - `docs/ARCHITECTURE_UI.md`
  - `docs/REPO_MAP_UI.md`
  - `README.md`
  - `LOG.md`
- **Validação humana executada:**
  - `python -m pytest -q tests/test_ui_smoke.py`
  - revisão manual do conteúdo documental frente ao estado real da UI
- **Rastreabilidade IA e correções:**
  - IA propôs estrutura inicial de docs UI.
  - revisão humana ajustou texto para refletir exatamente o snapshot atual (sem alegar stack React/TypeScript inexistente neste workspace).
- **Evidências obrigatórias:**
  - smoke de UI passou após atualização documental
  - impacto visual em runtime: N/A (CRP documental); justificativa registrada

- **CRP:** CRP-UI-02 — alinhar contratos ao dataset real
- **Objetivo:** alinhar expectativas de frontend ao contrato real servido pela API e ao dataset vigente.
- **Decisões técnicas:**
  - registrar contrato frontend em doc dedicado (`docs/DATA_CONTRACT_FRONTEND.md`)
  - formalizar via ADR que, neste snapshot, a UI consome contrato HTTP (não há `types.ts` frontend)
  - reforçar teste de contrato para limitar `statuses` retornados a `Open|Won|Lost`
- **Artefatos alterados:**
  - `docs/DATA_CONTRACT_FRONTEND.md`
  - `docs/ADR/0005-frontend-dataset-contract-alignment.md`
  - `tests/test_api_contract.py`
  - `README.md`
  - `LOG.md`
- **Validação humana executada:**
  - `python -m pytest -q tests/test_api_contract.py tests/test_ui_smoke.py`
  - revisão manual do dataset (`data/demo-opportunities.json`) versus contrato documentado
- **Rastreabilidade IA e correções:**
  - IA sugeriu foco em `types.ts` conforme CRP, mas revisão humana confirmou que esse arquivo não existe no snapshot atual.
  - correção de rumo: manter stack vigente e entregar alinhamento por contrato HTTP + ADR/documentação, sem inventar camada TypeScript inexistente.
- **Evidências obrigatórias:**
  - teste de contrato reforçado para `statuses`
  - impacto visual em runtime: N/A (mudança contratual/documental); justificativa registrada

- **CRP:** CRP-UI-03 — separar contrato de repositório e implementações
- **Objetivo:** desacoplar camada de apresentação UI de implementações concretas de dados e concentrar seleção em factory.
- **Decisões técnicas:**
  - criar contrato de repositório em `public/application/contracts/opportunity-repository.js`
  - criar implementações `api` e `mock` em `public/infrastructure/repositories/`
  - usar `repository-factory.js` como ponto único de composição e seleção
  - migrar `public/app.js` para consumir apenas o repositório (sem `fetch` direto)
- **Artefatos alterados:**
  - `public/application/contracts/opportunity-repository.js`
  - `public/infrastructure/repositories/api-opportunity-repository.js`
  - `public/infrastructure/repositories/mock-opportunity-repository.js`
  - `public/infrastructure/repositories/repository-factory.js`
  - `public/app.js`
  - `public/index.html`
  - `tests/test_ui_smoke.py`
  - `docs/REPOSITORY_STRATEGY.md`
  - `docs/ARCHITECTURE_UI.md`
  - `README.md`
  - `LOG.md`
- **Validação humana executada:**
  - `python -m pytest -q tests/test_ui_smoke.py tests/test_api_contract.py`
  - revisão manual confirmando que `public/app.js` não importa implementação concreta
- **Rastreabilidade IA e correções:**
  - IA sugeriu assert literal `/api/opportunities` em smoke; correção humana ajustou teste para validar caminho derivado (`/opportunities`) compatível com `basePath`.
  - revisão humana confirmou manutenção da stack JS atual sem introdução artificial de TypeScript no snapshot.
- **Evidências obrigatórias:**
  - smoke UI e contrato API verdes após refatoração
  - impacto visual em runtime: baixo (arquitetural); fluxo funcional preservado

- **CRP:** CRP-UI-04 — isolar mocks como fixture de demo
- **Objetivo:** manter mocks restritos ao modo demo/fallback controlado, sem vazamento para a camada de apresentação.
- **Decisões técnicas:**
  - criar pasta dedicada de fixtures em `public/infrastructure/mocks/fixtures/`
  - dividir fixture de listagem e builder de detalhe em arquivos separados
  - manter consumo de fixtures apenas no `mock-opportunity-repository`
  - reforçar smoke test para detectar import indevido de fixtures em `public/app.js`
- **Artefatos alterados:**
  - `public/infrastructure/mocks/fixtures/opportunity-list.js`
  - `public/infrastructure/mocks/fixtures/opportunity-detail.js`
  - `public/infrastructure/mocks/README.md`
  - `public/infrastructure/repositories/mock-opportunity-repository.js`
  - `tests/test_ui_smoke.py`
  - `docs/MOCK_STRATEGY.md`
  - `docs/REPOSITORY_STRATEGY.md`
  - `README.md`
  - `LOG.md`
- **Validação humana executada:**
  - `python -m pytest -q tests/test_ui_smoke.py tests/test_api_contract.py`
  - revisão manual confirmando ausência de import de mocks na apresentação (`public/app.js`)
- **Rastreabilidade IA e correções:**
  - IA propôs reorganização inicial dos mocks; revisão humana validou caminhos e adicionou regra explícita anti-vazamento no smoke test.
  - ajustes finais garantiram aderência ao contrato UI/API já documentado.
- **Evidências obrigatórias:**
  - smoke tests verdes com checagem de isolamento de mocks
  - impacto visual em runtime: N/A (estrutura de fixture); fluxo da demo preservado

- **CRP:** CRP-UI-05 — endurecer quality gates da UI
- **Objetivo:** sair do modo permissivo na trilha frontend e adicionar gates objetivos de regressão para arquitetura UI.
- **Decisões técnicas:**
  - adaptar o CRP ao snapshot real (UI em JavaScript, sem pipeline TS/npm ativo)
  - criar gate dedicado `validate_ui_quality.py` para validar arquitetura da UI (factory, sem fetch direto, sem import de fixture na apresentação)
  - adicionar tarefas `ui-quality` e `ui-ci-check` no `scripts/tasks.py` e incluir `ui-quality` no `build`
- **Artefatos alterados:**
  - `scripts/validate_ui_quality.py`
  - `scripts/tasks.py`
  - `docs/QUALITY_GATES_UI.md`
  - `docs/QUALITY_GATES.md`
  - `README.md`
  - `LOG.md`
- **Validação humana executada:**
  - `python .\\scripts\\tasks.py ui-quality`
  - `python .\\scripts\\tasks.py ui-ci-check`
  - `python -m pytest -q tests/test_ui_smoke.py tests/test_api_contract.py`
- **Rastreabilidade IA e correções:**
  - IA inicialmente orientada por `tsconfig/eslint` do CRP; revisão humana confirmou inexistência de stack TS no snapshot atual e aplicou equivalente verificável para JS.
  - ajustes documentais registraram claramente a adaptação sem inventar toolchain inexistente.
- **Evidências obrigatórias:**
  - output de `ui-quality` e `ui-ci-check` com sucesso
  - impacto visual em runtime: N/A (mudança em gates/validação); UI preservada

- **CRP:** CRP-UI-06 — refinar camada de dados do dashboard para casos reais
- **Objetivo:** fortalecer carregamento de dashboard com retry/cancelamento e padronização de query keys, mantendo stack JS atual.
- **Decisões técnicas:**
  - criar `public/shared/query/query-keys.js` para padronizar chaves de consulta
  - criar `public/presentation/hooks/use-dashboard-data.js` com cancelamento via `AbortController` e retry simples
  - adaptar `public/app.js` para usar o módulo de dados (sem acessar repositório diretamente)
  - estender repositórios API/mock para aceitar `signal` opcional
- **Artefatos alterados:**
  - `public/shared/query/query-keys.js`
  - `public/presentation/hooks/use-dashboard-data.js`
  - `public/app.js`
  - `public/infrastructure/repositories/api-opportunity-repository.js`
  - `public/infrastructure/repositories/mock-opportunity-repository.js`
  - `tests/test_ui_smoke.py`
  - `docs/QUERY_STRATEGY.md`
  - `docs/ARCHITECTURE_UI.md`
  - `README.md`
  - `LOG.md`
- **Validação humana executada:**
  - `python -m pytest -q tests/test_ui_smoke.py tests/test_api_contract.py`
  - `python .\\scripts\\tasks.py ui-quality`
- **Rastreabilidade IA e correções:**
  - IA propôs abordagem de hook inspirada em React Query; revisão humana adaptou para módulo JS compatível com snapshot (sem React/TS).
  - validação humana confirmou preservação de UX e melhoria de robustez em chamadas concorrentes.
- **Evidências obrigatórias:**
  - smoke UI verde com asserts de `AbortController` e query keys
  - impacto visual em runtime: baixo (robustez de dados); fluxo funcional preservado

- **CRP:** CRP-UI-07 — melhorar UX operacional da tabela e do drawer
- **Objetivo:** tornar a UX da listagem/detalhe mais previsível em cenários reais de filtro, erro e navegação por teclado.
- **Decisões técnicas:**
  - trocar lista simples por tabela com colunas operacionais (id/título/status/score/ação)
  - persistir seleção do item quando compatível com filtros; fallback para primeiro item quando necessário
  - explicitar estados do drawer (loading, erro genérico, not found, cancelamento)
  - adicionar ações de `retry` e `close` no drawer
  - incluir acessibilidade básica de teclado (`Enter`/`Espaço`) nas linhas da tabela
- **Artefatos alterados:**
  - `public/index.html`
  - `public/styles.css`
  - `public/app.js`
  - `tests/test_ui_smoke.py`
  - `docs/UX_DECISIONS.md`
  - `README.md`
  - `LOG.md`
- **Validação humana executada:**
  - `python -m pytest -q tests/test_ui_smoke.py tests/test_api_contract.py`
  - `python .\\scripts\\tasks.py ui-quality`
- **Rastreabilidade IA e correções:**
  - IA propôs melhorias de UX e eventos de teclado; revisão humana confirmou aderência ao snapshot JS (sem React) e preservação do fluxo principal.
  - ajustes manuais garantiram mensagens claras de erro/not found no drawer e comportamento consistente da seleção após filtragem.
- **Evidências obrigatórias:**
  - smoke tests verdes com assert de elementos de UX (`ranking-table`, `detail-retry`, `detail-close`)
  - captura funcional visual: pendente de registro humano local (UI alterada visivelmente)

- **CRP:** CRP-UI-08 — limpar template e consolidar branding
- **Objetivo:** remover “cheiro” de template na superfície pública da UI e alinhar identidade do produto com o posicionamento da submissão.
- **Decisões técnicas:**
  - atualizar `index.html` com title/meta tags e copy de produto
  - consolidar marca frontend como **Focus Score Cockpit**
  - ajustar documentação principal para refletir branding final
  - validar que não houve impacto funcional em fluxos UI/API
- **Artefatos alterados:**
  - `public/index.html`
  - `tests/test_ui_smoke.py`
  - `README.md`
  - `docs/ARCHITECTURE_UI.md`
  - `LOG.md`
- **Validação humana executada:**
  - `python -m pytest -q tests/test_ui_smoke.py tests/test_api_contract.py`
  - `python .\\scripts\\tasks.py ui-quality`
- **Rastreabilidade IA e correções:**
  - IA sugeriu limpeza de copy e metadados; revisão humana validou termos finais de branding e manteve coerência com o contexto do challenge.
  - não houve poda adicional de dependências aplicável ao snapshot (sem toolchain frontend extra ativo).
- **Evidências obrigatórias:**
  - smoke tests verdes após mudança de branding
  - captura funcional visual: pendente de registro humano local (title/primeira vista alterados)

- **CRP:** CRP-UI-09 — cobertura de testes do frontend
- **Objetivo:** aumentar proteção contra regressões em UX operacional e integração UI/API no snapshot atual.
- **Decisões técnicas:**
  - criar suíte `tests/test_ui_front_coverage.py` para estados críticos e acessibilidade básica
  - adicionar task `ui-tests` no runner e reutilizá-la no `ui-quality`
  - documentar estratégia específica da trilha UI em `docs/TEST_STRATEGY_UI.md`
- **Artefatos alterados:**
  - `tests/test_ui_front_coverage.py`
  - `scripts/tasks.py`
  - `docs/TEST_STRATEGY_UI.md`
  - `docs/TEST_STRATEGY.md`
  - `README.md`
  - `LOG.md`
- **Validação humana executada:**
  - `python .\\scripts\\tasks.py ui-tests`
  - `python .\\scripts\\tasks.py ui-quality`
  - `python -m pytest -q tests/test_api_contract.py`
- **Rastreabilidade IA e correções:**
  - IA propôs cobertura baseada em stack TS/React do CRP; revisão humana adaptou para cobertura estrutural/funcional compatível com UI JS do snapshot.
  - asserções foram revisadas para evitar testes decorativos e manter foco em regressões relevantes de demo.
- **Evidências obrigatórias:**
  - output verde de `ui-tests` e `ui-quality` registrado
  - impacto visual em runtime: N/A (foco em testes), sem alteração de UX nesta etapa

- **CRP:** CRP-UI-10 — CI do frontend
- **Objetivo:** fazer PRs da trilha UI falharem cedo com pipeline específica e visível.
- **Decisões técnicas:**
  - criar workflow dedicado `.github/workflows/frontend-ci.yml`
  - executar `ui-tests` e `ui-quality` como gates obrigatórios de frontend
  - documentar pipeline frontend em `docs/CI_FRONTEND.md`
  - atualizar README e docs de quality gates com badge/link do workflow
- **Artefatos alterados:**
  - `.github/workflows/frontend-ci.yml`
  - `docs/CI_FRONTEND.md`
  - `docs/QUALITY_GATES_UI.md`
  - `docs/QUALITY_GATES.md`
  - `README.md`
  - `LOG.md`
- **Validação humana executada:**
  - `python .\\scripts\\tasks.py ui-tests`
  - `python .\\scripts\\tasks.py ui-quality`
  - revisão manual do workflow e dos comandos referenciados na documentação
- **Rastreabilidade IA e correções:**
  - IA sugeriu estrutura de workflow; revisão humana confirmou compatibilidade com stack Python atual e evitou comandos npm inexistentes neste repo.
  - badge e docs foram alinhados ao nome real do workflow (`frontend-ci.yml`).
- **Evidências obrigatórias:**
  - validação local verde dos mesmos gates usados no workflow
  - evidência de run em GitHub Actions: pendente de execução remota (registrar screenshot/URL no `artifacts/process-log/`)

- **CRP:** CRP-S01 — process log: estrutura e template reutilizável
- **Objetivo:** alinhar template da raiz com o guia para garantir preenchimento auditável e sem ambiguidade.
- **Decisões técnicas:**
  - incluir no template da raiz os campos `Decomposição / subpassos` e `Julgamento / correção humana`
  - manter o formato tabular único para novos registros
- **Artefatos alterados:**
  - `PROCESS_LOG.md`
- **Validação humana executada:**
  - revisão manual de consistência entre `PROCESS_LOG.md` e `docs/PROCESS_LOG_GUIDE.md`
  - confirmação de que o template é copiável sem campos faltantes
- **Rastreabilidade IA e correções:**
  - IA sugeriu ajuste do template; revisão humana confirmou nomenclatura final dos campos para ficar idêntica ao guia.
- **Evidências obrigatórias:**
  - template atualizado visível na seção "Template padrão por CRP"
  - referência de preenchimento real nas entradas já existentes

- **CRP:** CRP-S02 — pasta e convenção de evidências do process log
- **Objetivo:** garantir estrutura versionada de evidências e convenção explícita de citação por path relativo.
- **Decisões técnicas:**
  - versionar subpastas com `.gitkeep` para evitar ausência de diretórios no clone limpo
  - reforçar em `artifacts/process-log/README.md` a estrutura mínima e regra de citação no `PROCESS_LOG.md`
- **Artefatos alterados:**
  - `artifacts/process-log/README.md`
  - `artifacts/process-log/screenshots/.gitkeep`
  - `artifacts/process-log/chat-exports/.gitkeep`
  - `artifacts/process-log/test-runs/.gitkeep`
  - `artifacts/process-log/ui-captures/.gitkeep`
  - `artifacts/process-log/decision-notes/.gitkeep`
  - `PROCESS_LOG.md`
- **Validação humana executada:**
  - revisão manual da árvore de evidências e convenção de nomes
  - checagem de que há referência explícita a paths sob `artifacts/process-log/` no próprio log
- **Rastreabilidade IA e correções:**
  - IA propôs apenas README; revisão humana adicionou `.gitkeep` para garantir reprodutibilidade da estrutura no versionamento.
- **Evidências obrigatórias:**
  - subpastas versionadas e documentadas
  - convenção de path relativo reforçada no README de evidências

- **CRP:** CRP-S03 — README de submissão a partir do esqueleto
- **Objetivo:** alinhar README da raiz ao esqueleto de submissão com afirmações verificáveis e links concretos.
- **Decisões técnicas:**
  - manter estrutura forte já existente (Executive Summary, Abordagem, Resultado, Recomendações, Limitações)
  - reforçar no README os campos explícitos do esqueleto: desafio literal, processo auditável e integração via PR
  - evitar texto de marketing sem prova, mantendo links para docs e comandos já validados
- **Artefatos alterados:**
  - `README.md`
  - `LOG.md`
  - `PROCESS_LOG.md`
- **Validação humana executada:**
  - revisão manual cruzada entre `README.md` e `docs/README_SUBMISSION_SKELETON.md`
  - checagem de aderência com `docs/CHALLENGE_CHECKLIST.md` e `docs/DEMO_SCRIPT.md`
- **Rastreabilidade IA e correções:**
  - IA propôs reforço de campos do esqueleto; revisão humana removeu qualquer formulação genérica sem ancoragem em doc/comando do repositório.
- **Evidências obrigatórias:**
  - README atualizado com referências concretas (`PROCESS_LOG.md`, `docs/PROCESS_LOG_GUIDE.md`, `docs/SUBMISSION_STRATEGY.md`)
  - impacto visual em runtime: N/A (CRP documental)

- **CRP:** CRP-S04 — validação contra critérios do desafio
- **Objetivo:** mapear critérios do desafio para evidências verificáveis no repositório, com estados `ok/parcial/N/A` sem maquiagem.
- **Decisões técnicas:**
  - atualizar `docs/CHALLENGE_CHECKLIST.md` com evidências concretas (paths e comandos reproduzíveis)
  - marcar como `parcial` o item de CI automatizada por depender de execução remota em repositório Git (sem inventar prova local)
  - manter referência cruzada com narrativa de submissão já consolidada no `README.md` e estratégia em `docs/SUBMISSION_STRATEGY.md`
- **Artefatos alterados:**
  - `docs/CHALLENGE_CHECKLIST.md`
  - `LOG.md`
  - `PROCESS_LOG.md`
- **Validação humana executada:**
  - revisão linha a linha da tabela `critério -> evidência -> estado`
  - conferência cruzada com `README.md`, `docs/SUBMISSION_STRATEGY.md` e artefatos de qualidade/CI do repositório
- **Rastreabilidade IA e correções:**
  - IA propôs reforço de evidências por comando/path.
  - Revisão humana ajustou o status de CI para `parcial` por ausência de prova remota neste ambiente local.
- **Evidências obrigatórias:**
  - checklist atualizado em `docs/CHALLENGE_CHECKLIST.md`
  - justificativa explícita de gap (CI remota) documentada no próprio checklist

- **CRP:** CRP-S05 — revisão final de submissão via PR
- **Objetivo:** consolidar a revisão final da submissão com checklist de PR e rastreabilidade, sem inventar merge remoto inexistente.
- **Decisões técnicas:**
  - reforçar `.github/PULL_REQUEST_TEMPLATE.md` com seção específica de CRP e checklist de submissão (`CRP-S05`)
  - documentar estado equivalente quando não há remoto Git disponível (auto-revisão com evidência em `artifacts/process-log/decision-notes/`)
  - manter transparência de lacunas remotas (PR/Actions) como pendências explícitas e não como `ok`
- **Artefatos alterados:**
  - `.github/PULL_REQUEST_TEMPLATE.md`
  - `artifacts/process-log/decision-notes/crp-s05-pr-equivalente-sem-remoto.md`
  - `LOG.md`
  - `PROCESS_LOG.md`
- **Validação humana executada:**
  - revisão manual do template de PR contra os critérios do `CRP-S05`
  - conferência de consistência com `docs/SUBMISSION_STRATEGY.md`, `docs/CHALLENGE_CHECKLIST.md` e `README.md`
- **Rastreabilidade IA e correções:**
  - IA propôs estrutura de checklist no template de PR.
  - Revisão humana exigiu campo explícito para lacunas de remoto e atualização de process log para fechamento equivalente.
- **Evidências obrigatórias:**
  - template de PR atualizado em `.github/PULL_REQUEST_TEMPLATE.md`
  - nota de revisão equivalente em `artifacts/process-log/decision-notes/crp-s05-pr-equivalente-sem-remoto.md`
  - estado de PR: *pendente de remoto Git para abertura real*

- **CRP:** CRP-S06 — auditoria output genérico vs verificável
- **Objetivo:** remover formulações vagas e reforçar linguagem verificável nos documentos mais visíveis da submissão.
- **Decisões técnicas:**
  - auditar `README.md`, `docs/SUBMISSION_STRATEGY.md` e `docs/CHALLENGE_CHECKLIST.md`
  - registrar amostras `antes -> depois` em nota versionada de decisão
  - substituir linguagem subjetiva por formulações ancoradas em evidência reproduzível
- **Artefatos alterados:**
  - `README.md`
  - `artifacts/process-log/decision-notes/crp-s06-auditoria-output-generico-vs-verificavel.md`
  - `LOG.md`
  - `PROCESS_LOG.md`
- **Validação humana executada:**
  - revisão manual final dos documentos auditados para confirmar ausência de novas afirmações fortes sem prova
  - conferência de consistência entre narrativa pública e checklist de critérios (`ok/parcial`)
- **Rastreabilidade IA e correções:**
  - IA apoiou detecção de frases potencialmente promocionais.
  - Revisão humana decidiu as substituições finais e manteve apenas formulações comprováveis.
- **Evidências obrigatórias:**
  - nota de auditoria com amostras `antes -> depois` em `artifacts/process-log/decision-notes/crp-s06-auditoria-output-generico-vs-verificavel.md`
  - README ajustado para linguagem verificável

- **CRP:** CRP-S07 — consolidar prompts e correções humanas relevantes
- **Objetivo:** publicar um anexo único e rastreável de uso de IA com foco nos casos de maior impacto técnico e de correção humana.
- **Decisões técnicas:**
  - preencher `docs/IA_TRACE.md` com entradas curtas (prompt/resposta/correção/evidência) em ordem cronológica
  - incluir apenas casos representativos para leitura de 5-10 minutos, evitando redundância
  - adicionar link explícito ao consolidado em `docs/SUBMISSION_STRATEGY.md`
- **Artefatos alterados:**
  - `docs/IA_TRACE.md`
  - `docs/SUBMISSION_STRATEGY.md`
  - `LOG.md`
  - `PROCESS_LOG.md`
- **Validação humana executada:**
  - conferência de coerência entre cada linha do consolidado e entradas já registradas no `PROCESS_LOG.md`
  - revisão para garantir ausência de dados sensíveis e de contradições com a narrativa de submissão
- **Rastreabilidade IA e correções:**
  - IA apoiou a síntese dos casos relevantes por CRP.
  - Revisão humana selecionou os casos finais e ajustou o texto para manter fidelidade ao log detalhado.
- **Evidências obrigatórias:**
  - consolidado publicado em `docs/IA_TRACE.md`
  - referência de navegação em `docs/SUBMISSION_STRATEGY.md`

### CRP-REAL-01 — Baseline do runtime real e eliminação do caminho demo dominante — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-REAL-01 (`focus-score aka build-003-lead-scorer-challenge-gap-closure-pack`) |
| **Problema** | A API HTTP servia apenas `data/demo-opportunities.json`, enfraquecendo a narrativa de aderência ao dataset oficial apesar dos CSVs existirem e serem validados. |
| **Decomposição / subpassos** | Mapear usos de demo; introduzir `LEAD_SCORER_DATA_SOURCE_MODE`; implementar loader a partir de `sales_pipeline.csv` + joins; default `real_dataset`; preservar demo para testes; documentar e gerar evidência. |
| **Ferramentas de IA (diagnóstico)** | Pesquisa semântica/`grep` no repo, leitura de `app.py` e contrato de dados; proposta de separação `DATA_SOURCE` vs `REPOSITORY_MODE`. |
| **Erro / limitação da IA** | Risco de confundir `LEAD_SCORER_REPOSITORY_MODE=api` com “dados reais” no browser — corrigido com variável dedicada ao serving HTTP. |
| **Decisões humanas** | Manter `demo-opportunities.json` e mocks UI/Python como legado controlado; forçar `demo_dataset` só em `test_api_contract.py` via `conftest.py`. |
| **Artefatos alterados / novos** | `src/api/dataset_loader.py`, `src/api/app.py`, `tests/conftest.py`, `tests/test_real_dataset_serving.py`, `docs/RUNTIME_DATA_FLOW.md`, `docs/RUNTIME_MODES.md`, `docs/MOCK_DECOMMISSIONING.md`, `docs/SETUP.md`, `README.md`, `.env.example`, `docker-compose.yml`, `artifacts/process-log/decision-notes/crp-real-01-baseline-runtime.md`, `artifacts/process-log/test-runs/crp-real-01-sample-ranking-real.json`, `LOG.md`, `PROCESS_LOG.md` |
| **Como verificar** | `python -m pytest -q`; `python .\scripts\tasks.py dev` e `GET /api/ranking?limit=2` sem env (esperar `total` ~8800). |
| **Evidências** | JSON amostral em `artifacts/process-log/test-runs/`; nota de decisão em `artifacts/process-log/decision-notes/crp-real-01-baseline-runtime.md`. |
| **PR** | *N/A local* — alinhar a 1 PR pequeno no remoto quando integrar o pacote gap-closure. |
| **Próximo CRP** | CRP-REAL-02 — wire CSVs à serving layer (refinar modelagem/cache se necessário). |

### CRP-REAL-02 — Conectar CSVs reais à camada de serving — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-REAL-02 (`focus-score aka build-003-lead-scorer-challenge-gap-closure-pack`) |
| **Problema** | O REAL-01 já servia CSVs, mas faltava pipeline explícito com **todos** os arquivos oficiais, joins de produto, metadata e validação de integridade antes do serving. |
| **Decomposição** | Novo pacote `src/serving/` com `ServingOpportunity` + `opportunity_pipeline.py`; validação FK agente/produto/conta; join `products` (série, preço); índice `metadata.csv`; cache invalidado por mtime; testes de integração + evidência de endpoint com `opportunity_id` real. |
| **Prompts / IA** | Pedido explícito do CRP-REAL-02; implementação assistida por IA com cruzamento ao contrato em `docs/DATA_CONTRACT.md` e relatório de integridade. |
| **Bugs / joins** | Risco de produto alias: resolvido reutilizando `normalize_value` antes do lookup em `products`. Conta vazia: tratada como `None` sem falha de FK. |
| **Correções humanas** | Confirmação de que o preço de lista vem de `products.sales_price` e que testes devem usar ID real (`1C1I7A6R`) para evidência verificável. |
| **Artefatos** | `src/serving/*`, `src/api/dataset_loader.py`, `docs/SERVING_REAL_DATA.md`, `docs/RUNTIME_DATA_FLOW.md`, `README.md`, `tests/test_serving_pipeline_integration.py`, `artifacts/process-log/test-runs/crp-real-02-detail-1C1I7A6R.json`, `LOG.md`, `PROCESS_LOG.md`, `docs/IA_TRACE.md` |
| **Verificação** | `python -m pytest -q`; `Invoke-RestMethod http://127.0.0.1:8787/api/opportunities/1C1I7A6R` (com `dev` em modo real). |
| **UI** | Sem mudança obrigatória de front: a UI já consome a API; em modo real mostra contas/agentes do CSV (validação manual recomendada no browser). |
| **Próximo CRP** | CRP-REAL-03 — alinhar runtime/domínio ao challenge. |

### CRP-REAL-03 — Alinhar domínio em runtime aos estágios do challenge — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-REAL-03 (`focus-score-challenge-gap-closure-pack`) |
| **Problema** | Resíduos de protótipo (`Open`, `status`, `ui_status`) divergiam do domínio oficial `sales_pipeline.deal_stage`. |
| **Desalinhamento encontrado** | Agregado `Open` na API/UI; `ServingOpportunity.ui_status`; query `status`; dashboard `statuses`; demo JSON com `status`. |
| **Ferramentas de IA** | `grep`/leitura transversal de `app.py`, `contracts`, `serving`, `public/`, `tests`; proposta de módulo `deal_stage` e normalização única. |
| **Decisões / revisão humana** | Labels em PT na UI (“Estágio”, placeholder `Engaging`); confirmar que KPI “abertas” = `Prospecting` + `Engaging`. |
| **Artefatos** | `src/domain/deal_stage.py`, `src/api/app.py`, `src/api/contracts.py`, `src/serving/models.py`, `src/serving/opportunity_pipeline.py`, `src/infrastructure/http/*`, `src/infrastructure/repositories/*`, `data/demo-opportunities.json`, `public/*`, `tests/test_deal_stage.py`, `docs/DOMAIN_ALIGNMENT.md`, `docs/DATA_CONTRACT_FRONTEND.md`, `docs/API_CONTRACT*.md`, ADR 0005, `LOG.md`, evidência em `artifacts/process-log/decision-notes/crp-real-03-domain-alignment.md` |
| **Verificação** | `python -m pytest -q` |
| **Evidências** | Lista de arquivos + exemplo de payload em `artifacts/process-log/decision-notes/crp-real-03-domain-alignment.md`; captura de UI com estágios corretos (anexar PNG pelo humano no mesmo diretório quando disponível). |
| **Próximo CRP** | CRP-REAL-04 em diante (enriquecimento de scoring / UI), conforme pacote gap-closure. |

### CRP-REAL-04 — Enriquecer scoring com features reais — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-REAL-04 (`focus-score-challenge-gap-closure-pack`) |
| **Hipótese** | Combinar joins já existentes (`accounts`, `products`, `sales_teams`) com datas do pipeline melhora a substância do score sem perder explicabilidade. |
| **Erros / riscos (IA)** | Risco de penalidades duplicadas (engage ausente + bucket `unknown`); risco de “ranking regional” sem evidência — mitigado com `known_office_bonus` neutro entre escritórios do dataset. |
| **Decisões humanas** | Manter pesos modestos; documentar que não há calibração por outcome; `version` 2 no JSON com fallback v1 nos testes. |
| **Artefatos** | `config/scoring-rules.json`, `src/scoring/engine.py`, `src/features/engineering.py`, `src/serving/models.py`, `src/serving/opportunity_pipeline.py`, `src/api/app.py`, `docs/SCORING_V2.md`, `docs/SCORING.md`, `tests/test_scoring_v2_features.py`, `artifacts/process-log/decision-notes/crp-real-04-scoring-evidence.md`, `README.md`, `LOG.md` |
| **Verificação** | `python -m pytest -q` |
| **Próximo CRP** | CRP-REAL-05+ conforme pacote (superfície de dados na UI, etc.). |

### CRP-REAL-05 — Superfície de dados reais na UI — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-REAL-05 (`focus-score-challenge-gap-closure-pack`) |
| **Problema** | Com API real, a UI ainda parecia “template” (poucas colunas, detalhe JSON, sem KPIs). |
| **Decisões UX** | Tabela alinhada ao vocabulário do challenge; KPIs no topo; detalhe em secções legíveis; placeholders de filtro baseados em `sales_teams.csv` (Central, Dustin Brinkmann). |
| **Correções vs IA** | Evitar rótulos genéricos “Core/Marcos” como única história; mock renomeado para deixar claro “modo ilustrativo”. |
| **Artefatos** | `public/*`, `src/api/app.py`, `src/api/contracts.py`, `src/infrastructure/http/dtos.py`, mocks Python/JS, `docs/UI_REAL_DATA_ALIGNMENT.md`, `artifacts/process-log/decision-notes/crp-real-05-ui-real-data.md` |
| **Verificação** | `python -m pytest -q`, `python scripts/validate_ui_quality.py` |
| **Próximo CRP** | CRP-REAL-06+ (limpeza de legado / ruído, etc.). |

### CRP-REAL-06 — Limpar ruído e isolar legado — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-REAL-06 (`legacy/focus-score-challenge-gap-closure-pack/crps/…` — pacote agora isolado) |
| **Critérios de corte** | Tudo o que não é importado pelo runtime (`src`, `public`, `tests`, CI) e é claramente “pacote colado” ou dump gigante → `legacy/`. `crps/` mantido na raiz (muitas referências; trilha de governança ativa). |
| **IA: risco** | Tendência a apagar `crps/` ou `docs/` — **não** feito; só isolamento de `focus-score-*`, `prompts/` e concat. |
| **Decisão humana** | Preservar rastreabilidade dos blocos REAL-01..05 no `PROCESS_LOG` mesmo com paths antigos; novos leitores devem usar `legacy/README.md` + `docs/REPO_SHAPE.md`. |
| **Artefatos** | `legacy/` (README + conteúdos movidos), `docs/REPO_SHAPE.md`, `artifacts/process-log/decision-notes/crp-real-06-repo-cleanup.md`, `.gitignore`, `scripts/tasks.py`, `README.md`, `00-START-HERE.md`, `docs/REPO_MAP.md`, `ARCHITECTURE.md`, `BASELINE.md`, `REPO_MAP_UI.md`, `LOG.md` |
| **Verificação** | `python -m pytest -q`, `python scripts/tasks.py lint` |
| **Próximo CRP** | CRP-REAL-07 em diante (README submissão, etc.). |

### CRP-REAL-07 — README como submissão final — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-REAL-07 (`legacy/focus-score-challenge-gap-closure-pack/crps/CRP-REAL-07-rewrite-readme-as-final-submission.md`) |
| **Problema** | O `README.md` ainda soava a “base/pack” e dispersava o leitor com listas enormes antes da narrativa de entrega. |
| **Decomposição** | Reestruturar em blocos exigidos pelo guide; posicionar **Challenge 003 — Lead Scorer** e produto **Focus Score Cockpit** no topo; mover detalhe para `docs/`; documentar cortes e anti-marketing em arquivo dedicado. |
| **IA — risco** | Texto genérico ou hype (“enterprise”, “production”) sem prova; repetir metodologia CRP no lugar do process log. |
| **Julgamento / correção humana** | Manter afirmações verificáveis; checklist de secções no README; decisões explícitas em `docs/README_DECISIONS.md`; evidência com tabela de presença das secções em `artifacts/process-log/decision-notes/crp-real-07-readme-submission.md`. |
| **Artefatos** | `README.md`, `docs/README_DECISIONS.md`, `artifacts/process-log/decision-notes/crp-real-07-readme-submission.md`, `LOG.md`, `PROCESS_LOG.md` |
| **Verificação** | Revisão manual das 7 secções; links relativos a `PROCESS_LOG.md`, `docs/REPO_SHAPE.md`, `docs/SETUP.md` válidos. |
| **Próximo CRP** | CRP-REAL-08+ conforme pacote gap-closure em `legacy/`. |

### CRP-REAL-08 — Testes no caminho principal (dataset real) — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-REAL-08 (`legacy/focus-score-challenge-gap-closure-pack/crps/CRP-REAL-08-upgrade-tests-to-real-dataset-path.md`) |
| **Problema** | Suíte centrada em demo/mocks deixa a submissão frágil no que o challenge exige: **CSVs reais** e fluxo HTTP completo. |
| **Gaps antigos** | `test_api_contract.py` corre em `demo_dataset`; faltavam asserções transversais (filtros + `q` + KPIs + explainability) sobre o mesmo caminho que o utilizador vê em `real_dataset`. |
| **Decomposição** | Novo módulo `test_real_dataset_main_flow.py` com amostras derivadas do listing (sem hardcode de região/manager frágeis); ID `1C1I7A6R` para detalhe; documentação dedicada e evidência em `artifacts/process-log/`. |
| **IA / prompts** | Pedido explícito do CRP + leitura de `app.py`, `conftest.py` e testes REAL-01/02 existentes; casos alinhados a parâmetros reais de query. |
| **Validação humana** | Confirmar que combinação filtros a partir de uma linha real não fica vazia; `q` usa token ≥4 chars para estabilidade; KPIs refletem invariante de estágios. |
| **Artefatos** | `tests/test_real_dataset_main_flow.py`, `docs/TEST_STRATEGY_REAL_DATA.md`, `artifacts/process-log/decision-notes/crp-real-08-real-data-tests.md`, `docs/TEST_STRATEGY.md`, `README.md`, `LOG.md`, `PROCESS_LOG.md` |
| **Verificação** | `python -m pytest -q`; `python scripts/tasks.py lint` |
| **Próximo CRP** | CRP-REAL-09+ conforme pacote em `legacy/`. |

### CRP-REAL-09 — Demo e evidências no fluxo real — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-REAL-09 (`legacy/focus-score-challenge-gap-closure-pack/crps/CRP-REAL-09-refresh-demo-and-evidence-on-real-flow.md`) |
| **Problema** | Roteiro e exemplos ainda apontavam para **demo** (`OPP-001`), gerando inconsistência com o produto servido por defeito a partir dos **CSVs**. |
| **Mudanças na demo** | `docs/DEMO_SCRIPT.md` recentrado em `real_dataset`; exemplos de API com `1C1I7A6R` e `total` ~8800; export reproduzível de JSON. |
| **Evidências antigas** | Amostras REAL-01/02 (schema desatualizado) **regeneradas** pelo script de export para alinhar a `deal_stage` e campos explícitos; narrativa “fonte da verdade” passa a `crp-real-09-*.json` + guia de PNG. |
| **Screenshots** | Não commitados binários neste passo; guia em `artifacts/process-log/ui-captures/REAL-09-SCREENSHOT-GUIDE.md` para captura humana pós-`dev`. |
| **Revisão humana** | Confirmação de que `OPP-001` fica apenas no papel de teste demo, não na história da demo. |
| **Artefatos** | `docs/DEMO_SCRIPT.md`, `scripts/export_real_flow_evidence.py`, `scripts/tasks.py`, `artifacts/process-log/test-runs/crp-real-09-*.json`, refresh `crp-real-01-*.json` / `crp-real-02-*.json`, `artifacts/process-log/ui-captures/REAL-09-SCREENSHOT-GUIDE.md`, `artifacts/process-log/decision-notes/crp-real-09-demo-real-flow.md`, `README.md`, `LOG.md`, `PROCESS_LOG.md` |
| **Verificação** | `python scripts/export_real_flow_evidence.py`; `python -m pytest -q`; `python scripts/tasks.py lint` |
| **Próximo CRP** | CRP-REAL-10+ conforme pacote em `legacy/`. |

### CRP-REAL-10 — Auditoria final contra README / requisitos Challenge 003 — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **CRP** | CRP-REAL-10 (`legacy/focus-score-challenge-gap-closure-pack/crps/CRP-REAL-10-final-audit-against-challenge-readme.md`) |
| **Objetivo** | Matriz requisito × evidência × status; pendências; parecer de prontidão antes do PR final. |
| **Fonte de requisitos** | `legacy/focus-score-challenge-gap-closure-pack/checklists/final_submission_checklist.md` + `docs/CHALLENGE_CHECKLIST.md`. |
| **Divergências (IA)** | Tendência a “tudo verde” sem **ATENDE PARCIALMENTE** — corrigido na matriz (filtro vendedor dedicado, CI remoto, profundidade UI, `legacy/`). |
| **Revisão humana** | Confirmar que não há requisito **NÃO ATENDE** bloqueante; decisão **SUBMETER** com ressalvas documentadas. |
| **Artefatos** | `docs/FINAL_AUDIT_CHALLENGE_003.md`, `artifacts/process-log/decision-notes/crp-real-10-final-audit.md`, `docs/CHALLENGE_CHECKLIST.md`, `README.md`, `LOG.md`, `PROCESS_LOG.md` |
| **Verificação** | Leitura cruzada código/docs/testes citados na matriz; `python -m pytest -q` e `python scripts/tasks.py lint` como sanity check. |
| **Decisão final** | **Submeter** (pendências não bloqueantes na secção 5 de `FINAL_AUDIT_CHALLENGE_003.md`). |

### Trilha CRP-UX-01 … CRP-UX-10 — Pacote competição UX — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **Origem** | `legacy/focus-score-ux-competition-pack/` (`CURSOR_MASTER_PROMPT_UX.md` + CRP-UX-01…10) |
| **UX-01** | Vitrine alinhada ao fluxo real: texto no header + factory com default `api`; mock só explícito. |
| **UX-02** | Detalhe sem JSON cru: cartões, herói de score, listas de fatores; proibido `JSON.stringify` em `public/app.js`. |
| **UX-03** | Layout **cockpit** (KPI deck, grelha ranking + painel de detalhe). |
| **UX-04** | Tabela: faixa de prioridade, próxima ação resumida, destaque `is-top-pick` na 1.ª linha. |
| **UX-05** | Nomenclatura PT para faixa/estágio na UI; `docs/UX_NOMENCLATURE.md`. |
| **UX-06** | Tokens/badges/cartões (reimplementação visual; sem domínio Lovable incorreto — não havia código Lovable no repo). |
| **UX-07** | Filtros: grid compacto, **Limpar**, contagem de resultados, pesquisa `q` (conta/ID/título), filtro `priority_band`; API `GET /api/opportunities` estendida. |
| **UX-08** | Estados de ranking/KPI/detalhe com mensagens mais claras e classes de estado. |
| **UX-09** | `tests/test_ui_competition_pack.py` (sem JSON.stringify, cockpit, query params, `priority_band` real + 422). |
| **UX-10** | `artifacts/process-log/ui-captures/UX-COMPETITION-FINAL-GUIDE.md`; README/DEMO/LOG/evidência consolidada. |
| **Artefatos** | `public/index.html`, `public/styles.css`, `public/app.js`, `public/infrastructure/repositories/*`, `public/application/contracts/opportunity-repository.js`, `public/infrastructure/mocks/fixtures/opportunity-list.js`, `src/api/app.py`, `tests/test_ui_competition_pack.py`, `tests/test_ui_smoke.py`, `tests/test_ui_front_coverage.py`, `docs/UX_NOMENCLATURE.md`, `docs/UX_DECISIONS.md`, `docs/DEMO_SCRIPT.md`, `README.md`, `artifacts/process-log/decision-notes/crp-ux-competition-pack.md`, `LOG.md`, `PROCESS_LOG.md` |
| **Verificação** | `python -m pytest -q`; `python scripts/tasks.py lint` |
| **Riscos remanescentes** | PNG finais ainda manuais; filtro HTTP dedicado por **vendedor** continua como melhoria (pesquisa `q` cobre parcialmente). |

### Trilha CRP-CBX-01 … CRP-CBX-07 — Combobox gestor + filter-options — 2026-03-20

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-20 |
| **Origem** | `focus-score-combobox-crps-pack/` (`cursor-master-prompt.md` + `crps/CRP-CBX-01` … `CRP-CBX-07`) |
| **Problema** | Lista longa de gestores em `<select>` pouco usável; opções de filtro sem garantia de unicidade/ordenação consistente entre API e cliente. |
| **CBX-01** | `GET /api/dashboard/filter-options`: `regional_offices`, `managers`, `deal_stages` deduplicados (CI) e ordenados; `regions` = espelho de `regional_offices`. |
| **CBX-02…05** | Cliente: `normalizeSortDedupeStrings` em `public/shared/filter-options-utils.js`; `getDashboardFilterOptions` nos repositórios; `initFilterWidgets` + `buildFilterObject` com `filter-region`, `filter-deal-stage`, `manager-value`. |
| **CBX-03…04** | Combobox gestor: `wireManagerCombobox` — mínimo 3 letras, debounce, teclado, estado vazio. |
| **CBX-06…07** | Markup `index.html` + estilos combobox em `public/styles.css`. |
| **Artefatos** | `src/api/app.py`, `src/api/contracts.py`, `public/*`, `tests/test_api_contract.py`, `tests/test_real_dataset_serving.py`, `tests/test_ui_competition_pack.py`, `tests/test_ui_smoke.py`, `docs/API_CONTRACT_UI.md`, `docs/UX_DECISIONS.md`, `artifacts/process-log/decision-notes/crp-cbx-combobox-filters.md`, `LOG.md`, `PROCESS_LOG.md` |
| **Verificação** | `python -m pytest -q`; `python scripts/tasks.py lint` |
| **Nota** | Sem migração para React; contrato de query `region` / `manager` / `deal_stage` mantido. |

### CRP-CBX-08 — Combobox gestor funcional (autocomplete + evidência) — 2026-03-21

| Campo | Conteúdo |
|--------|-----------|
| **Data** | 2026-03-21 |
| **CRP** | CRP-CBX-08 (texto do utilizador / pacote combobox) |
| **Objetivo** | Garantir combobox **real** (não textbox estático): lista da API, ≥3 letras, prefixo antes de contém, teclado/rato, estados loading/vazio/sem resultados/selecionado, limpar filtros, clique fora. |
| **Ferramenta IA** | Cursor (agente Auto) |
| **Prompt** | Especificação completa CBX-08 (requisitos funcionais, UX, técnicos, DoD, validação manual). |
| **Proposta IA** | `filterManagersByQuery` em `filter-options-utils.js`; `wireManagerCombobox` com `rootEl`, `aria-activedescendant`, `pointerdown` global, `destroy`; `initFilterWidgets` com `aria-busy` + mensagem de carregamento; textos alinhados ao CRP; testes pytest de strings; guia PNG. |
| **Ajustes manuais** | Hint após sucesso (não ficar em «A carregar…»); clique **dentro** da lista não dispara fecho; **destroy** passou a usar `AbortController` + limpeza de debounce/blur timers. |
| **Evidência** | PNG: `artifacts/process-log/ui-captures/cbx-08/cbx-08-01-combobox-inicial.png`, `cbx-08-01b-menos-tres-letras.png`, `cbx-08-02-tres-letras-sugestoes.png`, `cbx-08-03-sem-resultados.png`, `cbx-08-04-gestor-selecionado.png`, `cbx-08-05-apos-limpar.png`; geração: `python scripts/capture_cbx08_screenshots.py`; guia `artifacts/process-log/ui-captures/CBX-08-SCREENSHOT-GUIDE.md`; nota `artifacts/process-log/decision-notes/crp-cbx-08-manager-combobox.md`; `docs/CBX-08_MANAGER_COMBOBOX.md`. |
| **Artefatos** | `public/index.html`, `public/app.js`, `public/presentation/widgets/manager-combobox.js`, `public/shared/filter-options-utils.js`, `scripts/capture_cbx08_screenshots.py`, `tests/test_ui_competition_pack.py`, `docs/UX_DECISIONS.md`, `LOG.md`, `PROCESS_LOG.md` |
| **Verificação** | `python -m pytest -q tests/test_ui_competition_pack.py tests/test_ui_smoke.py`; `python scripts/capture_cbx08_screenshots.py`; checklist manual no guia de screenshots. |

### CRP-FIN-01 — Combobox gestor: lista total + filtro incremental — 2026-03-21

| Campo | Conteúdo |
|--------|-----------|
| **Pacote** | `legacy/focus-score-final-tuning-crps-pack` (CRP-FIN-01) |
| **Problema** | Textbox com gate de N letras não mostrava a equipa completa ao abrir; pouco operacional para escolher gestor. |
| **Solução** | `listAllOrFilterManagers`; painel abre no **focus** com todos os gestores + linha «Todos os gestores»; digitar afunila com prefixo → contém; `aria-haspopup="listbox"`. |
| **Evidência** | `artifacts/process-log/decision-notes/crp-fin-01-combobox-lista-total.md`; `python -m pytest -q`; script `capture_cbx08_screenshots.py` ajustado (incl. `cbx-08-01c-lista-completa.png`). |
| **arquivos** | `public/presentation/widgets/manager-combobox.js`, `public/shared/filter-options-utils.js`, `public/index.html`, `public/app.js`, `tests/test_ui_competition_pack.py`, `docs/FILTER_EXECUTION_MODEL.md`, `LOG.md`. |

### CRP-FIN-02 — Combobox: padrão de busca, empty state, a11y — 2026-03-21

| Campo | Conteúdo |
|--------|-----------|
| **Objetivo** | Comportamento previsível: prefixo → contém; empty states; teclado + `aria-*` revisados. |
| **Entregue** | Documentação em `artifacts/process-log/decision-notes/crp-fin-02-combobox-a11y.md`; `docs/UX_DECISIONS.md` atualizado (FIN-01/02). Código FIN-01 já cobre Esc, clique fora, `aria-selected`, ArrowDown abre painel. |
| **Verificação** | `python -m pytest -q tests/test_ui_competition_pack.py` |

### CRP-FIN-03 — Score: baseline pipeline aberto — 2026-03-21

| Campo | Conteúdo |
|--------|-----------|
| **Alteração** | `deal_stage_weights` em `config/scoring-rules.json` (menos prémio a `Won`, mais peso a abertos). |
| **Evidência** | `artifacts/process-log/decision-notes/crp-fin-03-open-pipeline-baseline.md`; `docs/SCORING_V2.md`; `pytest` scoring. |

### CRP-FIN-04 — Score: features úteis para open pipeline — 2026-03-21

| Campo | Conteúdo |
|--------|-----------|
| **Alteração** | `pipeline_age`, `missing_engage_date_penalty`, novo `open_operational` + `_apply_open_operational_signals` em `engine.py`. |
| **Evidência** | `artifacts/process-log/decision-notes/crp-fin-04-open-features.md`; `docs/SCORING_V2.md`; `pytest`. |

### CRP-FIN-05 — Próximas ações por contexto — 2026-03-21

| Campo | Conteúdo |
|--------|-----------|
| **Alteração** | `actions_by_context` no JSON; `_pick_contextual_next_action` no motor. |
| **Evidência** | `artifacts/process-log/decision-notes/crp-fin-05-next-actions.md`; `pytest`. |

### CRP-FIN-06 — Explicações humanizadas — 2026-03-21

| Campo | Conteúdo |
|--------|-----------|
| **Alteração** | `src/api/explanation_narrative.py`; integração em `view_models` e `app` (detalhe). |
| **Evidência** | `artifacts/process-log/decision-notes/crp-fin-06-humanize-explanations.md`; `pytest`. |

### CRP-FIN-07 — Diversidade contextual — 2026-03-21

| Campo | Conteúdo |
|--------|-----------|
| **Alteração** | `docs/EXPLANATION_NARRATIVE.md`; variante extra `Won` em `explanation_narrative.py`. |
| **Evidência** | `artifacts/process-log/decision-notes/crp-fin-07-explanation-diversity.md`. |

### CRP-FIN-08 — Limpeza: packs em legacy — 2026-03-21

| Campo | Conteúdo |
|--------|-----------|
| **Alteração** | `git mv` dos packs `focus-score-*` para `legacy/`; `legacy/PACKS_ARCHIVE.md`. |
| **Evidência** | `artifacts/process-log/decision-notes/crp-fin-08-packs-legacy.md`. |

### CRP-FIN-09 — Runtime default real documentado — 2026-03-21

| Campo | Conteúdo |
|--------|-----------|
| **Alteração** | `docs/RUNTIME_DEFAULTS.md`; reforço em `.env.example`. |
| **Evidência** | `artifacts/process-log/decision-notes/crp-fin-09-runtime-defaults.md`. |

### CRP-FIN-10 — README submissão final — 2026-03-21

| Campo | Conteúdo |
|--------|-----------|
| **Alteração** | Reforço do primeiro bloco do `README.md` (submissão + runtime real). |
| **Evidência** | `artifacts/process-log/decision-notes/crp-fin-10-readme-submission.md`. |

### CRP-FIN-11 — Auditoria UI/dados — 2026-03-21

| Campo | Conteúdo |
|--------|-----------|
| **Entregue** | `docs/FIN-11_AUDIT_CHECKLIST.md`; nota `crp-fin-11-audit.md`. |
| **Verificação** | `python -m pytest -q` |

### CRP-FIN-12 — Pacote de submissão — 2026-03-21

| Campo | Conteúdo |
|--------|-----------|
| **Entregue** | `docs/SUBMISSION_PACKAGE.md`; nota `crp-fin-12-submission-package.md`. |
| **Estado** | Pronto para PR após revisão humana. |

### CRP-DEL-01 — Inventário final da entrega — 2026-03-21

| Campo | Conteúdo |
|--------|-----------|
| **Entregue** | `docs/DELIVERY_INVENTORY.md` (presente / lacunas / mapeamento CRP). |
| **Pack** | `focus-score-delivery-submission-crps-pack/` versionado para rastreio da trilha DEL/DOC/SUB/VID. |
| **Verificação** | Revisão humana dos paths listados vs árvore do repo. |

### CRP-DOC-01 — README final em submission/ — 2026-03-21

| Campo | Conteúdo |
|--------|-----------|
| **Entregue** | `submissions/leopoldo-lima/README.md` com secções do template oficial (Sobre mim, Executive Summary, Solução, Abordagem, Resultados, Recomendações, Limitações, Ferramentas, Workflow, IA, valor humano, process log, evidências). |
| **Verificação** | Leitura cruzada com `docs/README_SUBMISSION_SKELETON.md`. |

### CRP-DOC-02 — Documentação de entrega e referências — 2026-03-21

| Campo | Conteúdo |
|--------|-----------|
| **Entregue** | `docs/DELIVERY_NOTES.md` (como correr, validar, evidências; referência sóbria a *Vibecoding Industrial* com link de catálogo Amazon). |
| **README** | `submissions/leopoldo-lima/README.md` atualizado com link às notas de entrega. |

### CRP-DOC-03 — Índice consolidado de evidências — 2026-03-21

| Campo | Conteúdo |
|--------|-----------|
| **Entregue** | `docs/EVIDENCE_INDEX.md` (tabela por categoria: processo, notas, UI, vídeo, test-runs, chat exports, submissão). |
| **README** | `submissions/leopoldo-lima/README.md` com link explícito ao índice. |

### CRP-SUB-01 — Auditoria contra o submission guide — 2026-03-21

| Campo | Conteúdo |
|--------|-----------|
| **Entregue** | `docs/SUBMISSION_GUIDE_AUDIT.md` (requisitos × status × evidência). |
| **Checklist** | `docs/CHALLENGE_CHECKLIST.md` — linha de revisão com referência ao audit. |

### CRP-SUB-02 — Auditoria contra o submission template — 2026-03-21

| Campo | Conteúdo |
|--------|-----------|
| **Entregue** | `docs/SUBMISSION_TEMPLATE_AUDIT.md` (matriz 13 blocos × README). |
| **Correção** | `submissions/leopoldo-lima/README.md` — secção **Submissão via PR** + checklist atualizado. |
| **Conclusão** | Cobertura 100% dos blocos do template. |

### CRP-SUB-03 — Pacote final para PR — 2026-03-21

| Campo | Conteúdo |
|--------|-----------|
| **Entregue** | `docs/PR_HANDOFF.md` (branch, verificação, arquivos novos, exclusões). |
| **README** | `submissions/leopoldo-lima/README.md` — link clicável ao handoff na secção Submissão via PR. |

### CRP-VID-01 — Roteiro e cena do vídeo — 2026-03-21

| Campo | Conteúdo |
|--------|-----------|
| **Entregue** | `docs/VIDEO_SCRIPT.md`; cópia de trabalho `artifacts/process-log/decision-notes/video-script.md`. |
| **Notas** | Duração 3–4 min; cenas alinhadas ao fluxo KPI → filtro → detalhe → combobox gestor. |

### CRP-VID-02 — Captura automatizada com Chromium — 2026-03-21

| Campo | Conteúdo |
|--------|-----------|
| **Entregue** | `scripts/record_demo_chromium.py` (Uvicorn + Playwright Chromium, WebM + PNG); `docs/VIDEO_RUNBOOK.md`. |
| **Pré-requisito** | `pip install playwright` e `python -m playwright install chromium` (opcional-deps). |
| **Verificação** | Execução local documentada no runbook (CRP-VID-03 gera artefatos binários). |

### CRP-VID-03 — Gerar e publicar o vídeo — 2026-03-21

| Campo | Conteúdo |
|--------|-----------|
| **Artefatos** | `artifacts/process-log/screen-recordings/demo-cockpit.webm`; PNG de demo (atualizado para `demo-01`…`demo-07` no refino abaixo). |
| **Correção técnica** | Seletor Playwright para opções de estágio: `option:not([value=""])` (compatível com motor do Playwright). |
| **Docs** | `docs/EVIDENCE_INDEX.md`, `docs/DELIVERY_INVENTORY.md`, `submissions/leopoldo-lima/README.md` com links aos arquivos. |
| **Verificação** | `python scripts/record_demo_chromium.py` (exit 0) em ambiente com dataset em `data/`. |

### Refino — vídeo com filtros e digitação de gestores / pesquisa — 2026-03-21

| Campo | Conteúdo |
|--------|-----------|
| **Script** | `scripts/record_demo_chromium.py`: `--pace slow` (omissão) e `--pace fast`; pausas longas; digitação caractere a caractere em `#search-q` e `#manager-search`; filtro escritório regional; estágio (preferência Engaging/Prospecting); prioridade **Alta**; seleção de gestor por clique na primeira sugestão; detalhe no fim. Viewport 1366×900. |
| **Artefatos** | `demo-cockpit.webm` + `demo-01`…`demo-07.png` regenerados. |
| **Docs** | `docs/VIDEO_RUNBOOK.md`, `docs/EVIDENCE_INDEX.md`, `docs/PR_HANDOFF.md`, `submissions/leopoldo-lima/README.md`. |

### Refino — rolagem + «Aplicar filtros» após cada mudança — 2026-03-21

| Campo | Conteúdo |
|--------|-----------|
| **Script** | `record_demo_chromium.py`: `_scroll_section` com `scrollIntoView({ behavior: 'smooth' })` em `--pace slow`; `_apply_filters_and_wait` + `_after_filter_change` (KPI → ranking → filtros → aplicar → ranking + `#result-count`); `_wait_ranking_idle`; se 0 linhas antes do detalhe, **Limpar filtros**; escolha do `.webm` por **mtime** e remoção de WebMs órfãos. |
| **Artefatos** | `demo-cockpit.webm` e PNG `demo-01`…`demo-07` regenerados. |
| **Docs** | `docs/VIDEO_RUNBOOK.md` (fluxo alinhado à UI real). |

### CRP-SUB-08 — Curadoria dos CRPs e narrativa oficial de construção com IA — 2026-03-21

| Campo | Conteúdo |
|--------|-----------|
| **Objetivo** | Organizar CRPs em `crps/executed/{foundation,data,ui,product-tuning,submission}/`, arquivar lista plana e pack de importação, consolidar narrativa (GPT-5.4, CRPs, Cursor + método *Vibecoding Industrial*, Lovable → industrialização) em README, `IA_TRACE`, `SUBMISSION_STRATEGY`; citação sóbria ao livro com URL canónica. |
| **Por que** | Reduzir ruído para o avaliador; alinhar documentação ao fluxo real de trabalho; evitar aparência de «depósito de oficina» sem apagar evidência. |
| **Decisões** | **Visível:** `crps/executed/`, `indexes/`, `crps/README.md`. **Arquivo:** `crps/*.md` planos → `archive/superseded/crps-root-flat-pre-SUB-08/`; pacote `focus-score-curated-crps` → `archive/superseded/focus-score-curated-crps/` após cópia. **Produto:** sem alteração funcional. |
| **Narrativa** | Resumo no `README.md`; longa por fases em `docs/IA_TRACE.md`; secção executiva em `docs/SUBMISSION_STRATEGY.md`; `docs/CRP_GOVERNANCE.md` e `docs/README_SUBMISSION_SKELETON.md` atualizados. Livro: [*Vibecoding Industrial*](https://www.amazon.com/dp/B0GQR585SC) como referência metodológica apenas. |
| **IA vs humano** | IA: redacção-base e estruturação; humano: curadoria de pastas, validação de coerência com o repo real, tom não promocional. |
| **Evidências** | `artifacts/process-log/decision-notes/crp-sub-08-curation.md`; `indexes/crp-index.csv`; `indexes/suggested-repo-tree.md`; `archive/README.md`; `crps/executed/submission/CRP-SUB-08-curadoria-crps-e-narrativa.md`. |
| **Resumo narrativo** | Ver `docs/IA_TRACE.md` — entrada-resumo para leitores do process log. |
| **Ajuste de tooling** | `scripts/tasks.py`: smoke exige `crps/executed/`; lint MD percorre `crps/**/*.md` e `indexes/*.md`. `pyproject.toml`: `ruff` `extend-exclude` inclui `archive/`. |

### FAXINA-PACOTE-2026-03-21 — Submissão no repo `ai-master-challenge`

| Campo | Conteúdo |
|--------|-----------|
| **Problema** | Duplicação (`solution/docs`, `solution/crps`, `solution/PROCESS_LOG.md`, evidências espelhadas em `solution/artifacts/process-log/`) e referências antigas a `submission/README.md`. |
| **Decisão** | Canónico: `process-log/` e `docs/` apenas ao lado de `solution/`; `solution/artifacts/process-log/` mínimo para outputs de scripts; README principal `submissions/leopoldo-lima/README.md`. |
| **Código** | `tasks.py`: `SUBMISSION_ROOT` para smoke e lint MD; `generate_data_dictionary.py` + `tests/test_data_dictionary.py` escrevem/lêem `docs/DATA_DICTIONARY.md` via `SUBMISSION_ROOT`. |
| **Docs** | Atualização de handoff, índices, auditorias; legado em `docs/archive/`; LinkedIn no README. |
| **Verificação** | `python scripts/tasks.py test` (smoke + `pytest -q`) verde após alterações. |
