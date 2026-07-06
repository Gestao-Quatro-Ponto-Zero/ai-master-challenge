# Project Master Report — Lead Scorer (Challenge 003)

> Documento mestre consolidado de handoff, manutenção e operação do Lead Scorer.
> Único arquivo necessário para entender o histórico, executar localmente e manter o projeto.
> Operador: Gabriel Oliveira · Modelo: GLM-5.2 (GitHub Copilot) · Data: 06/07/2026

---

## Índice

1. [Resumo executivo](#1-resumo-executivo)
2. [Objetivo de negócio e contexto do challenge](#2-objetivo-de-negocio-e-contexto-do-challenge)
3. [Escopo implementado](#3-escopo-implementado)
4. [Arquitetura da solução](#4-arquitetura-da-solucao)
5. [Linha do tempo de execução](#5-linha-do-tempo-de-execucao)
6. [Decisões técnicas e trade-offs](#6-decisoes-tecnicas-e-trade-offs)
7. [Erros encontrados e correções](#7-erros-encontrados-e-correcoes)
8. [Design system e decisões de UX](#8-design-system-e-decisoes-de-ux)
9. [Funcionalidades implementadas](#9-funcionalidades-implementadas)
10. [Passo a passo para rodar localmente](#10-passo-a-passo-para-rodar-localmente)
11. [Guia de manutenção (runbook)](#11-guia-de-manutencao-runbook)
12. [Qualidade e validação](#12-qualidade-e-validacao)
13. [Estrutura de pastas relevante](#13-estrutura-de-pastas-relevante)
14. [Pendências abertas e riscos](#14-pendencias-abertas-e-riscos)
15. [Roadmap v2](#15-roadmap-v2)
16. [Changelog consolidado por etapa](#16-changelog-consolidado-por-etapa)
17. [Checklist final de handoff](#17-checklist-final-de-handoff)

---

## 1. Resumo executivo

- App Streamlit funcional que prioriza 4.708 deals abertos com score 0-100 explicável.
- Scoring composto por 6 componentes ponderados (regras + heurísticas, sem ML black-box).
- Filtros por vendedor, manager, escritório, stage, score mínimo e top N.
- Feature DISC + Assistente de Follow-up: 3 copys por tom, ganchos de venda, próxima melhor ação.
- Design system G4 aplicado (tokens extraídos de g4business.com via Playwright).
- Metodologia: Spec-Driven Development + Prompt Harness de 8 prompts rastreáveis.
- Dataset: fallback sintético schema-compatível (credenciais Kaggle indisponíveis noambiente).
- Validação: 8 ACs do scoring + 6 testes unitários da feature DISC/follow-up passando.

---

## 2. Objetivo de negócio e contexto do challenge

- **Challenge:** 003 — Lead Scorer (Vendas / RevOps) do G4 AI Master Challenge.
- **Problema:** pipeline de ~8.800 oportunidades com priorização "no feeling".
- **Stakeholders:** Head de RevOps, 35 vendedores, managers regionais, time de RevOps.
- **Critério central:** score explicável 0-100 + app funcional que vendedor não-técnico use.
- **Regra do regulamento:** "regras bem apresentadas valem mais que XGBoost sem interface".

---

## 3. Escopo implementado

### Entregue

- `scoring.py`: motor de scoring com 6 componentes + breakdown PT-BR.
- `app.py`: app Streamlit com filtros, KPIs, top-N, tabela, charts Plotly e design G4.
- `disc_profile.py`: inferência DISC explicável (D/I/S/C/indefinido) com confiança e racional.
- `followup_engine.py`: 3 copys por tom (consultivo, direto, provocativo elegante) + fallback.
- `sales_hooks.py`: 3-5 ganchos de venda por DISC + próxima melhor ação.
- `eda.py`: diagnóstico exploratório + `eda_report.txt`.
- `generate_synth_data.py`: fallback sintético schema-compatível.
- `test_scoring_ac.py`: validação dos 8 ACs da SPEC de scoring.
- `tests/`: 6 testes unitários para DISC + follow-up + hooks.
- Documentação: `HARNESS.md`, `HARNESS_STEPS.md`, `G4-DESIGN-SYSTEM-PROMPT.md`, `DISC_FOLLOWUP_SPEC.md`, `PROCESS_LOG.md` + 8 prompts.

### Não entregue (decisão consciente)

- ML preditivo calibrado (Non-Goal conforme README do challenge).
- Integração com CRM real.
- Auth/role-based masking (documentado como roadmap).
- Vetorização para 100K+ deals (Non-Goal nesta versão).

---

## 4. Arquitetura da solução

### Fluxo de dados

```
CSVs (accounts, products, sales_teams, sales_pipeline)
  └─> score_pipeline(pipeline, accounts, products, sales_teams, today, only_open=True)
        ├─ merge pipeline + accounts + products + sales_teams
        ├─ calcula agent_winrate do histórico (Won+Lost)
        ├─ filtra abertos (Prospecting/Engaging)
        └─ apply(score_deal) por linha
              └─ DealScore(total_score, components[6], summary_ptbr)
  └─> app.py (Streamlit)
        ├─ cache load_scored_pipeline()
        ├─ filtros sidebar (vendedor/manager/escritório/stage/score/topN)
        ├─ KPIs (deals ativos, score médio, valor em jogo, top deal)
        ├─ top-N deals com badge + breakdown
        ├─ Assistente de Follow-up (DISC + 3 copys + ganchos + next action)
        ├─ tabela completa
        └─ charts (histograma + scatter score×valor)
```

### Componentes do scoring (pesos)

| Componente | Peso | Feature(s) |
|-----------|------|------------|
| Stage advancement | 25% | `deal_stage` |
| Pipeline velocity | 20% | dias desde `engage_date` |
| Account size | 20% | `revenue`, `employees` |
| Product value | 15% | `sales_price` |
| Agent track record | 15% | win rate por `sales_agent` |
| Deal value | 5% | `close_value` |

### Feature DISC + Follow-up

- `disc_profile.build_lead_profile(row, today)` → objeto LeadProfile.
- `followup_engine.generate_followup_package(profile)` → {copies[3], hooks[3-5], next_best_action}.
- `sales_hooks.get_sales_hooks(profile)` e `get_next_best_action(profile, hooks)`.
- UI integrada com botão Copiar via JS + fallback "Selecionar texto".

---

## 5. Linha do tempo de execução

| Etapa | Prompt | Skill/Agent | Entrega |
|-------|--------|-------------|---------|
| 1 | Research-First | ARCHITECT + SKILL-01 | Hipóteses + armadilhas do dataset |
| 2 | EDA | BUILDER + SKILL-04 | `eda.py` + `eda_report.txt` |
| 3 | SPEC scoring | ARCHITECT + SKILL-02 | SPEC com 8 ACs + edge cases |
| 4 | Build scoring | BUILDER | `scoring.py` funcional |
| 5 | App Streamlit | BUILDER + DESIGN-SYSTEM-G4 | `app.py` com filtros/KPIs/charts |
| 6 | Review | REVIEWER + SEC-SCAN | 25 itens auditados, 6 fixes |
| 7 | RevOps test | REVOPS-EXPERT | Avaliação de uso real |
| 8 | Memory-OPT | SKILL-05 | Consolidação de sessão |
| 9 | Design System update | BUILDER | Super prompt canônico + tokens novos aplicados |
| 10 | DISC + Follow-up | BUILDER + SPEC-DRIVEN | `disc_profile.py`, `followup_engine.py`, `sales_hooks.py`, UI integrada |
| 11 | Docs consolidation | DOC-UPDATER + MEMORY-OPT | Este documento mestre |

---

## 6. Decisões técnicas e trade-offs

- **Streamlit sobre Plotly Dash/React:** velocidade de entrega + vendedor abre no navegador + Python end-to-end.
- **Regras + heurísticas > ML:** explainability é multiplicador de valor; calibragem de modelo exigiria dados históricos rotulados.
- **Componente "Agent track record" (15%):** impacto do vendedor na conversão, frequentemente ignorado pela IA genérica.
- **`TODAY` fixado em 2025-07-01:** determinismo/auditoria (AC5).
- **Dataset sintético:** fallback transparente por ausência de credenciais Kaggle; app funciona igual com dados reais.
- **DISC inferido de features disponíveis:** sem inventar colunas; fallback "indefinido" quando evidência é insuficiente.
- **Clipboard via JS com fallback:** robustez para ambientes sem `navigator.clipboard`.

---

## 7. Erros encontrados e correções

| # | Erro | Correção |
|---|------|----------|
| 1 | `engage_date` assumido em ISO; real era MM/DD/YYYY | `pd.to_datetime(format='%m/%d/%Y')` virou instinto do HARNESS |
| 2 | Peso 5% para agent win rate (IA) | Elevado para 15% com base na EDA |
| 3 | `st.selectbox` com options hardcoded | Corrigido para ler `df.unique()` em runtime |
| 4 | Edge case `engage_date=NaT` não tratado | SPEC E1: velocity=0 com label específico |
| 5 | `use_container_width=True` deprecated | Substituído por `width="stretch"` |
| 6 | Label de agente novo mascarava "sem histórico" | SPEC E5: label explícita |
| 7 | `score_deal` reconvertia data dentro do apply | Conversão movida para `score_pipeline` |
| 8 | `color_discrete_map` só cobria 2 stages | Adicionado Won/Lost para robustez |
| 9 | Super prompt DS novo não referenciado no harness | Seção 5 substituída por apontamento canônico |
| 10 | KPIs quebravam linha em telas estreitas | Tipografia responsiva com `clamp()` + modo compacto |
| 11 | `StreamlitDuplicateElementId` no selectbox do assistente | `render_followup_assistant` movido para fora do loop de deals |

---

## 8. Design system e decisões de UX

- Fonte canônica: `docs/G4-DESIGN-SYSTEM-PROMPT.md`.
- Tokens aplicados: color-1 (navy), color-9 (cream), color-5 (gold), color-6 (green), primary-color (vermelho).
- Tipografia: PPMuseum (display) + Libre Baskerville (editorial) + Manrope (body/UI).
- Cores de badge: >80 verde, 50-80 gold, <50 primary-color, todas em wash 10%.
- CTA: radius-sm (3px), weight 800, sem uppercase, com hover/focus-visible/disabled.
- KPI cards: radius-md (10px), padding 36px, números em clamp(30-40px).
- Tabela: zebra alternando color-10/color-9, sem bordas pesadas.
- Charts: fundo transparente, gridlines em color-7, scatter colorido por faixa de score.

---

## 9. Funcionalidades implementadas

| Funcionalidade | Status |
|---------------|--------|
| Score 0-100 explicável | ✅ |
| 6 componentes ponderados | ✅ |
| Filtros (vendedor/manager/escritório/stage/score/topN) | ✅ |
| KPIs (deals ativos, score médio, valor em jogo, top deal) | ✅ |
| Top-N deals com badge + breakdown | ✅ |
| Tabela completa ordenada por score | ✅ |
| Histograma de scores | ✅ |
| Scatter score × valor | ✅ |
| Design system G4 | ✅ |
| Inferência DISC explicável | ✅ |
| 3 copys de follow-up por tom | ✅ |
| Botão Copiar com fallback | ✅ |
| Ganchos de venda por DISC | ✅ |
| Próxima melhor ação | ✅ |
| Testes unitários (scoring + DISC) | ✅ |
| Process log + harness | ✅ |
| Auth/role-based masking | ⏸️ roadmap |
| ML preditivo | ⏸️ Non-Goal |
| CRM integration | ⏸️ roadmap |

---

## 10. Passo a passo para rodar localmente

### Pré-requisitos

- Python 3.11+ (testado com 3.12)
- PowerShell (Windows) ou bash (Linux/Mac)

### Setup

```powershell
cd "c:\Users\Administrador\Desktop\Desafio G4\ai-master-challenge\submissions\Gabriel Oliveira\solution"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Dados

- Dataset sintético já em `solution/data/` (gerado por `generate_synth_data.py`).
- Para dados reais: baixar do Kaggle (link no README do challenge) e colocar os 4 CSVs em `solution/data/`.

### Rodar o app

```powershell
.\venv\Scripts\python.exe -m streamlit run app.py --server.port 8502 --server.headless true
```

Abrir: http://localhost:8502

### Rodar testes

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
.\venv\Scripts\python.exe test_scoring_ac.py
```

### Rodar EDA

```powershell
.\venv\Scripts\python.exe eda.py
```

Saída: `eda_report.txt` na mesma pasta.

---

## 11. Guia de manutenção (runbook)

### Onde alterar regras de score

- `solution/scoring.py`:
  - `WEIGHTS` (linha do dict) → ajustar pesos dos 6 componentes.
  - `score_deal()` → ajustar subscore de cada componente (stage_scores, velocity, account_size, etc.).
  - `_minmax()` → ajustar normalização.

### Onde alterar UI

- `solution/app.py`:
  - `CSS` (bloco f-string) → tokens, tipografia, componentes.
  - `render_sidebar()` → filtros.
  - `render_kpi()` → cards do topo.
  - `render_followup_assistant()` → seção DISC + copys + ganchos.
  - `render_distribution_chart()` / `render_scatter_chart()` → gráficos Plotly.
- `solution/.streamlit/config.toml` → tema base do Streamlit.

### Onde alterar textos/copies

- `solution/followup_engine.py`:
  - `_copy_templates()` → 3 copys (consultivo, direto, provocativo elegante).
  - `_validate_copies()` → regras de CTA e tamanho.
- `solution/sales_hooks.py`:
  - `PROFILE_HOOKS` → ganchos por perfil DISC.
  - `get_next_best_action()` → recomendação de próxima ação.

### Onde alterar inferência DISC

- `solution/disc_profile.py`:
  - `infer_disc_profile()` → regras de scoring D/I/S/C.
  - `build_lead_profile()` → schema do LeadProfile.

### Como adicionar novos filtros

1. Em `app.py` → `render_sidebar()`: adicionar `st.sidebar.selectbox` ou `st.slider`.
2. Retornar valor no dict de filtros.
3. Em `apply_filters()`: aplicar condição sobre `df`.

### Como depurar problemas comuns

- **NaT em datas:** confirmar `format='%m/%d/%Y'` em `score_pipeline`.
- **Widget duplicado (StreamlitDuplicateElementId):** garantir que a função não seja chamada dentro de loop; usar `key` único.
- **Clipboard não copia:** verificar sandbox do iframe; fallback "Selecionar texto" está implementado.
- **Score fora de [0,100]:** checar `_minmax()` clamping.
- **DISC sempre indefinido:** verificar se `deal_stage` e `close_value` estão populados.

---

## 12. Qualidade e validação

### Testes executados

- `test_scoring_ac.py`: 8 ACs da SPEC de scoring (todos PASS).
- `tests/test_disc_profile.py`: DISC definido + fallback indefinido.
- `tests/test_followup_engine.py`: 3 tons únicos + CTA + fallback.
- `tests/test_sales_hooks.py`: 3-5 hooks + next_best_action não vazio.
- Resultado: 6 testes unitários passando.

### Smoke checks

- App renderiza sem erro em http://localhost:8502.
- KPIs legíveis sem quebra de linha.
- Assistente de Follow-up renderiza perfil, 3 copys, ganchos e próxima ação.
- Botoes Copiar/Selecionar texto presentes por copy.
- Tabela com zebra e coluna de score como ProgressColumn.

### Limitações conhecidas

- Dataset sintético (credenciais Kaggle indisponíveis).
- Scoring heurístico, não ML preditivo.
- PII `sales_agent` exibida no app (roadmap: toggle de masking).
- `TODAY` fixado para determinismo.
- `df.apply` axis=1 (não vetorizado) — OK para 4.708 deals.
- Range de `agent_sub` genérico (não calibrado com percentis).

---

## 13. Estrutura de pastas relevante

```
submissions/Gabriel Oliveira/
├── README.md
├── docs/
│   ├── HARNESS.md
│   ├── HARNESS_STEPS.md
│   ├── G4-DESIGN-SYSTEM-PROMPT.md
│   ├── G4-DISC-FOLLOWUP-PROMPT.md
│   ├── G4-SELLER-FRIENDLY-UX-PROMPT.md
│   ├── G4-DOCS-CONSOLIDATION-SUPERPROMPT.md
│   ├── DISC_FOLLOWUP_SPEC.md
│   ├── PROJECT_MASTER_REPORT.md (este)
│   └── MAINTENANCE_NOTES.md
├── process-log/
│   ├── PROCESS_LOG.md
│   └── PROMPT_01..08_*.md
└── solution/
    ├── app.py
    ├── scoring.py
    ├── disc_profile.py
    ├── followup_engine.py
    ├── sales_hooks.py
    ├── eda.py
    ├── eda_report.txt
    ├── generate_synth_data.py
    ├── test_scoring_ac.py
    ├── requirements.txt
    ├── .streamlit/config.toml
    ├── data/ (4 CSVs)
    ├── tests/
    │   ├── test_disc_profile.py
    │   ├── test_followup_engine.py
    │   └── test_sales_hooks.py
    └── venv/ (gitignored)
```

---

## 14. Pendências abertas e riscos

- Substituir dataset sintético por Kaggle real (depende de `kaggle.json`).
- Abrir PR final no fork (passo externo não executado).
- PII toggle ("Modo apresentação") para masking de nomes.
- Account humanizada (`account_0077` → `Media · Australia · Acme Corp`).
- Ação no deal (botão "Assumir"/"Descartar" via `st.session_state`).
- Calibração de `agent_sub` com percentis reais do dataset.
- Vetorização para escalar a 100K+ deals.

---

## 15. Roadmap v2 (priorizado)

1. **Account humanizada** (1h) — enrich account com industry/country/parent_company.
2. **PII toggle** (30min) — "Modo apresentação" mascarando nomes reais.
3. **Ação no deal** (2h) — botão "Assumir"/"Descatar" via `st.session_state`.
4. **Dataset real Kaggle** — substituir CSVs sintéticos quando credenciais disponíveis.
5. **Calibração de pesos** — usar percentis reais do dataset para `agent_sub` e outros.
6. **ML baseline** — Gradient Boosting para comparar contra heurística.
7. **CRM integration** — conectar com Salesforce/HubSpot via API.
8. **Vetorização** — refatorar `score_deal` com NumPy para 100K+ deals.
9. **Auth/roles** — login + role-based masking para produção.
10. **Histórico de scores** — trend temporal para comparar períodos.

---

## 16. Changelog consolidado por etapa

- **Prompt 01 (Research-First):** hipóteses e armadilhas catalogadas.
- **Prompt 02 (EDA):** `eda.py` + `eda_report.txt`; formato de data MM/DD/YYYY confirmado.
- **Prompt 03 (SPEC scoring):** 6 componentes com 8 ACs e edge cases.
- **Prompt 04 (Build scoring):** `scoring.py` com `score_deal` + `score_pipeline`.
- **Prompt 05 (App Streamlit):** `app.py` com filtros, KPIs, charts, design G4.
- **Prompt 06 (Review):** 25 itens auditados, 6 correções aplicadas.
- **Prompt 07 (RevOps test):** avaliação de uso real como Head de RevOps.
- **Prompt 08 (Memory-OPT):** consolidação de sessão e memórias.
- **Design System update:** super prompt canônico + tokens novos aplicados no app e harness.
- **DISC + Follow-up:** `disc_profile.py`, `followup_engine.py`, `sales_hooks.py`, UI integrada, 6 testes.
- **Docs consolidation:** `PROJECT_MASTER_REPORT.md` + `MAINTENANCE_NOTES.md` + entrada final no PROCESS_LOG.

---

## 17. Checklist final de handoff

- [x] App funcional rodando em http://localhost:8502
- [x] 8 ACs de scoring validados (PASS)
- [x] 6 testes unitários DISC/follow-up passando
- [x] Design system G4 aplicado e canônico
- [x] Feature DISC + Follow-up + Ganchos integrada
- [x] PROCESS_LOG.md atualizado com entrada final
- [x] MAINTENANCE_NOTES.md criado (quick reference)
- [x] PROJECT_MASTER_REPORT.md criado (este documento)
- [x] Estrutura de pastas documentada
- [x] Runbook de manutenção incluído
- [x] Roadmap v2 priorizado
- [x] Limitações e riscos documentados
- [ ] Dataset real Kaggle (pendente credenciais)
- [ ] PR final no fork (pendente)

---

## Onboarding de 10 minutos (novo dev)

1. Ler este `PROJECT_MASTER_REPORT.md` (seções 1-4 e 10).
2. Rodar `streamlit run app.py` no venv.
3. Abrir `scoring.py` → entender os 6 componentes e pesos.
4. Abrir `app.py` → `CSS` (design), `render_sidebar` (filtros), `render_followup_assistant` (DISC).
5. Rodar `python -m unittest discover -s tests` para ver testes passando.
6. Consultar `MAINTENANCE_NOTES.md` para mudanças rápidas.
