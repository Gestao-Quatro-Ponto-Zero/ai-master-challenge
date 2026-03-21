# Demo script (3–5 minutos) — **fluxo real** (dataset oficial)

## Objetivo
Demonstrar a solução tal como o challenge a consome: **CSVs em `data/`**, scoring explicável, API, UI e rastreabilidade — **sem** depender do snapshot `demo-opportunities.json` na narrativa principal.

## Preparação (antes da demo)

1. **Modo de dados:** não definir `LEAD_SCORER_DATA_SOURCE_MODE`, ou garantir `real_dataset` (omissão = real).
   **Evitar** `demo_dataset` na demo ao vivo — esse modo existe para testes determinísticos (`test_api_contract.py`), não para a história do produto.
2. Dependências: `python -m pip install -e .[dev]`
3. Qualidade: `python .\scripts\tasks.py build` (ou `test` + `lint` se o tempo for curto)
4. Subir API/UI: `python .\scripts\tasks.py dev`

## Roteiro sugerido

### 0:00 – 0:40 | Contexto e entrega
- Challenge **003 — Lead Scorer**; entrega **Focus Score Cockpit** (API + UI + governança).
- Pilares: dados oficiais, score explicável, testes, CI, observabilidade, `PROCESS_LOG.md`.

### 0:40 – 1:50 | Fluxo funcional (runtime real)
- Abrir `http://127.0.0.1:8787/`.
- **Cockpit:** faixa de KPIs no topo; **filtros** compactos (incl. pesquisa por conta/ID/título, faixa de prioridade, **Limpar filtros** e contagem de resultados); **ranking** central; **painel de detalhe** com score em destaque e cartões “Porque este score?”.
- **KPIs** (~8800 oportunidades): totais, abertas, ganhas, perdidas, score médio.
- **Tabela:** IDs do `sales_pipeline.csv`, conta, produto, vendedor, gestor, escritório, estágio (rótulos PT nos badges), valor, **score**, **faixa de prioridade**, **próxima ação** resumida; primeira linha destacada como topo da página.
- **Filtro:** ex. região **Central** ou gestor **Dustin Brinkmann** (valores reais do dataset; pode confirmar em **Filtros** da UI ou em `GET /api/dashboard/filter-options`).
- Abrir **detalhe** de uma linha (ex. ID **`1C1I7A6R`** — conta Cancity) e mostrar explicabilidade **legível** (sem JSON cru): fatores positivos/negativos, alertas, próxima ação.

### 1:50 – 2:30 | API e contrato (**exemplos reais**)
- Ranking: `http://127.0.0.1:8787/api/ranking?limit=3` — `total` ≈ 8800, itens com `deal_stage`, `account`, `product`.
- Detalhe real: `http://127.0.0.1:8787/api/opportunities/1C1I7A6R` — **não** usar `OPP-001` na demo principal (é só modo demo).
- Opcional: `GET /api/dashboard/kpis` e `GET /api/dashboard/filter-options`.
- Contratos: `docs/API_CONTRACT.md`, `docs/API_CONTRACT_UI.md`.

**Evidência versionada (mesmo payload, sem browser):**
`python .\scripts\tasks.py export-real-flow-evidence` gera JSON em `artifacts/process-log/test-runs/crp-real-09-*.json` (reproduzível).

### 2:30 – 3:10 | Qualidade e segurança
- `python .\scripts\tasks.py build` (ou resumo dos gates já corridos).
- `docs/QUALITY_GATES.md`.

### 3:10 – 3:50 | Rastreabilidade
- `PROCESS_LOG.md`, `LOG.md`, `artifacts/process-log/` (incl. nota **CRP-REAL-09**).

### 3:50 – 4:30 | Observabilidade
- `GET /metrics`; header `x-request-id` num pedido à API.
- `docs/OBSERVABILITY.md`.

### 4:30 – 5:00 | Limitações e próximos passos
- Docker, métricas em memória, UI minimalista; roadmap curto.

## Capturas de menu (UI real)

Instruções e nomes sugeridos de arquivos: **`artifacts/process-log/ui-captures/REAL-09-SCREENSHOT-GUIDE.md`**.
Colocar PNGs em `artifacts/process-log/screenshots/` após gravar a demo (ex.: dashboard + detalhe com ID real).

## Checklist de apresentação
- [ ] Tempo total ≤ 5 minutos.
- [ ] **Nenhum** exemplo principal baseado em `OPP-001` / `demo_dataset`.
- [ ] Limitações explícitas.
- [ ] Processo / IA referenciados no `PROCESS_LOG.md`.

## O que mudou vs roteiros antigos
- Removida a referência a **`/api/opportunities/OPP-001`** como passo principal da API.
- Alinhamento explícito a **IDs do pipeline** e a export reproduzível de evidência JSON (**CRP-REAL-09**).
