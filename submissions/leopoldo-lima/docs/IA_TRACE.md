# Rastreabilidade de IA — narrativa e consolidado

Este arquivo cumpre **`CRP-S07`** (tabela de prompts/correções) e **`CRP-SUB-08`** (narrativa cronológica oficial da construção com IA), em coerência com `PROCESS_LOG.md`.

**Leitura complementar para o avaliador:** hipóteses de produto, validações do score com KPIs do dataset real (8800 / 2089 / 4238 / 2473) e enquadramento explícito do uso de IA — ver o [`README.md`](../README.md) da submissão (secções *Hipóteses e julgamento humano*, *Validações do score* e *Process Log — Como usei IA*).

## Referência metodológica

O método de execução adotado no projeto foi inspirado em **Vibecoding Industrial**, formalizado no livro *Vibecoding Industrial* ([Amazon](https://www.amazon.com/dp/B0GQR585SC)): decomposição em trabalhos pequenos, artefactos rastreáveis e separação entre geração automática e julgamento humano. **Não** é endosso comercial: o repositório é julgado pelos critérios técnicos do challenge e pelo conteúdo verificável do código e dos logs.

---

## Narrativa cronológica (visão geral)

### 1. GPT-5.4 como apoio à modelagem

O **GPT-5.4** foi usado para **estruturar o desafio**, propor **arquitetura em alto nível** e **decompor** o trabalho em passos que pudessem ser executados, testados e registados um de cada vez — evitando a ilusão de “um único prompt resolve o projeto”.

### 2. CRP como unidade de execução

**CRP** significa **Change Request Prompt**: um pacote de trabalho **curto**, com objetivo, tarefas, entregáveis e critérios de aceite. Os CRPs foram a **unidade operacional** entre “ideia” e “commit com evidência”. O conjunto curado está organizado em `process-log/crps/executed/` por tema; o índice máquina-legível é [`indexes/crp-index.csv`](../process-log/indexes/crp-index.csv).

### 3. Cursor e Vibecoding Industrial

O **Cursor** foi usado como ambiente de implementação, com instruções e regras alinhadas à ideia de **engenharia com IA disciplinada** descrita em *Vibecoding Industrial* (ligação acima): CRPs, process log, evidências em `process-log/` (e espelho técnico em `solution/artifacts/process-log/` para scripts), e recusa de narrativa genérica sem prova no repositório.

### 4. Lovable e a primeira casca visual

A **primeira casca de interface** foi gerada no **Lovable** (protótipo visual rápido). Essa base **não** foi o destino final: serviu como **ponto de partida** para o desenho do cockpit.

### 5. GPT-5.4 como integrador / auditor da UI

Com o backend e o contrato a amadurecer, o GPT-5.4 ajudou a **gerar CRPs** para: alinhar contrato HTTP, cliente e repositório na UI (`CRP-API-*`, `CRP-UI-*`), incorporar o fluxo **cockpit** e competição UX (`CRP-UX-*`), e fechar interações como o **combobox de gestor** (`CRP-CBX-*`). Cada passo exigiu **ajuste ao dataset real** e **testes** — não cópia cega do protótipo.

### 6. Revisão humana e iterações

Em todo o percurso houve **revisão humana**: rejeição ou alteração de propostas da IA, correção de testes, alinhamento ao challenge (trilha `CRP-REAL-*`), e auditorias de submissão (`CRP-S*`, `CRP-FIN-*`, `CRP-SUB-*`, `CRP-VID-*`). O registo fino está em **`PROCESS_LOG.md`**; este arquivo resume a **linha narrativa** e os **casos pontuais** mais instructivos (tabela abaixo).

### 7. O que este projeto **não** foi

Não foi **“um prompt → uma resposta → submissão”**. Foi um **processo iterativo** com **correções documentadas**, **quality gates**, **dataset real** como padrão e **evidências versionadas**.

---

## Consolidado (casos pontuais — CRP-S07)

| Data | CRP | Resumo do prompt | Resumo da resposta | Correção humana | Evidência |
|------|-----|------------------|--------------------|-----------------|-----------|
| 2026-03-20 | CRP-003 | Formalizar contrato de dados em Python sem inventar stack. | Proposta de contrato JSON + validação executável. | Ajustado para `account` opcional e alias `GTXPro -> GTX Pro` conforme dataset real. | `PROCESS_LOG.md` (CRP-003), `contracts/repository-data-contract.json`, `scripts/validate_data_contract.py` |
| 2026-03-20 | CRP-005 | Criar API de ranking/detalhe e provar execução. | Proposta de endpoints `ranking`, `detail`, `health` com testes. | Porta tornou-se configurável por ambiente após bloqueio local (`WinError 10013`). | `PROCESS_LOG.md` (CRP-005), `src/api/app.py`, `tests/test_api_contract.py` |
| 2026-03-20 | CRP-008 | Endurecer quality gates e segurança. | Proposta de lint/format/typecheck/security/SBOM no runner. | Escopo de auditoria de dependências ajustado para evitar ruído de ambiente global. | `PROCESS_LOG.md` (CRP-008), `docs/QUALITY_GATES.md`, `requirements-audit.txt` |
| 2026-03-20 | CRP-API-06 | Plugar filtros reais na listagem UI/API. | Proposta de serialização estável de query + busca/ordenação server-side. | Correção no teste para decodificar query bytes (`decode`) e ajustes de lint. | `PROCESS_LOG.md` (CRP-API-06), `src/infrastructure/http/filter_params.py`, `tests/test_api_client.py` |
| 2026-03-20 | CRP-API-08 | Criar testes de contrato com simulação HTTP. | Proposta de suíte com `pytest-httpx`. | URLs mockadas foram alinhadas exatamente com query real gerada pelo client. | `PROCESS_LOG.md` (CRP-API-08), `tests/test_api_client_contract_http.py` |
| 2026-03-20 | CRP-API-09 | Remover acoplamento residual de mocks no caminho API. | Proposta de factory por modo e lazy import. | Removida exportação de mock no `__init__` e criado teste para garantir não-import em modo API. | `PROCESS_LOG.md` (CRP-API-09), `src/infrastructure/repositories/repository_factory.py`, `tests/test_repository_factory.py` |
| 2026-03-20 | CRP-UI-03 | Separar contrato de repositório e implementações na UI shell. | Proposta de contrato + factory + impls API/mock. | Ajuste de teste smoke para validar `"/opportunities"` (compatível com `basePath`) em vez de literal rígido. | `PROCESS_LOG.md` (CRP-UI-03), `public/infrastructure/repositories/`, `tests/test_ui_smoke.py` |
| 2026-03-20 | CRP-UI-05 | Endurecer quality gates da UI. | Proposta inicial com viés TypeScript. | Adaptação para stack real JS via `scripts/validate_ui_quality.py` e tasks Python. | `PROCESS_LOG.md` (CRP-UI-05), `scripts/validate_ui_quality.py`, `scripts/tasks.py` |
| 2026-03-20 | CRP-S04 | Validar critérios do desafio com evidências. | Proposta de checklist critério -> evidência -> estado. | Critério de CI ficou `parcial` por ausência de prova remota, evitando falso positivo. | `PROCESS_LOG.md` (CRP-S04), `docs/CHALLENGE_CHECKLIST.md` |
| 2026-03-20 | CRP-S06 | Auditar linguagem genérica vs verificável. | Proposta de limpeza de termos vagos em docs públicas. | Texto promocional foi substituído por formulação verificável e registrado em nota `antes -> depois`. | `PROCESS_LOG.md` (CRP-S06), `README.md`, `artifacts/process-log/decision-notes/crp-s06-auditoria-output-generico-vs-verificavel.md` |
| 2026-03-20 | CRP-REAL-01 | Executar gap-closure: runtime real vs demo dominante. | Variável `LEAD_SCORER_DATA_SOURCE_MODE`, loader CSV e default `real_dataset`. | Confirmação de não confundir com `LEAD_SCORER_REPOSITORY_MODE`; `conftest` mantém demo só para contrato API. | `PROCESS_LOG.md` (CRP-REAL-01), `docs/RUNTIME_DATA_FLOW.md`, `artifacts/process-log/decision-notes/crp-real-01-baseline-runtime.md` |
| 2026-03-20 | CRP-REAL-02 | Ligar os 5 CSVs ao serving com modelo canónico. | Pacote `src/serving/`, FKs, join produto/metadata, cache por mtime. | Testes com `Generator` tipado no fixture; ID real `1C1I7A6R` para evidência de endpoint. | `PROCESS_LOG.md` (CRP-REAL-02), `docs/SERVING_REAL_DATA.md`, `tests/test_serving_pipeline_integration.py` |

---

## Verificação humana

- Conferência cruzada feita contra as entradas detalhadas do `PROCESS_LOG.md`.
- Apenas casos com impacto real de decisão/correção foram incluídos na tabela (sem duplicação ornamental).
- Nenhum segredo ou dado sensível foi incluído no consolidado.

---

*Última atualização: 2026-03-21 (CRP-SUB-08 narrativa + CRP-S07 tabela preservada)*
