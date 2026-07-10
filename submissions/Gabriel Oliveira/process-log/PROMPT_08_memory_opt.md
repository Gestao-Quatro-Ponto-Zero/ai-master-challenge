# Prompt 08 — Consolidar memória (SKILL-05 MEMORY-OPT)

> **Prompt emitido:**

```
[SKILL: MEMORY-OPT]

Resuma esta sessão inteira para /memories/session/:
1. Decisões e por quês
2. Prompts que funcionaram (vira template)
3. Erros do GLM-5.2 e correções
4. Estado do repositório
5. Próximos 3 passos
Formato markdown conciso.
```

---

## 1. Decisões e por quês

| Decisão | Por quê |
|---------|---------|
| Challenge 003 Lead Scorer (não 001/002/004) | "construir software" alinha com perfil vibe-coding, e o challenge explicitamente valoriza ferramenta funcional sobre documento |
| Stack Streamlit + pandas + plotly | ROI máximo dentro do budget 4-6h do challenge; vendedor não-técnico abre no browser |
| Scoring heurístico (regras + MinMax) em vez de ML black-box | README do challenge diz literalmente "scoring baseado em regras bem apresentado vale mais que XGBoost sem interface" |
| Explainability-first (cada componente tem label PT-BR) |_critério de qualidade multiplicador de valor: "vendedor entender POR QUE é 10x mais útil" |
| 6 componentes com pesos 25/20/20/15/15/5 | calibrados pela EDA (Prompt 02) contra win rate real 42-67% e close_value 0-21K |
| Spec-Driven: spec markdown aprovada ANTES do build | força julgamento humano antes do primeiro prompt de implementação |
| Design system G4 extraído via Playwright do g4business.com | navy #001F35 + cream #F5F4F3 + Manrope/PPMuseum — alinha UI do Lead Scorer à marca do avaliador |
| Dataset sintético como fallback quando Kaggle CLI falhou (sem credenciais) | destravar desenvolvimento; documentado transparentemente no README com instruções para swap com dados reais |
| TODAY fixado em 2025-07-01 em vez de `pd.Timestamp.now()` | determinismo para auditoria (AC5 da SPEC) — reprodutível por outro avaliador |
| `@st.cache_data(ttl=600)` em `load_scored_pipeline` | scoring O(n) sobre 8800 rows não deve recomputar a cada interação de filtro |
| Branch `submission/seu-nome` (renomeada para `Gabriel Oliveira`) | segue CONTRIBUTING.md do challenge que exige pasta `submissions/seu-nome/` |

## 2. Prompts que funcionaram (viram template)

### Padrão de prompt harness-nativo

Cada um dos 8 prompts seguiu o envelope:
```
[AGENT: X] [SKILL: Y]
Contexto + Estado atual + Tarefa + Constraints + Formato esperado
```

### Templates validados (reutilizáveis em outros challenges)

| Template | Quando usar |
|----------|-------------|
| `[AGENT: ARCHITECT] [SKILL: RESEARCH-FIRST]` | antes de codar — gera hipóteses falsificáveis e catálogo de armadilhas |
| `[AGENT: BUILDER] [SKILL: SEC-SCAN]` | EDA com output paralelo em arquivo, PII anonimizada, paths relativos |
| `[AGENT: ARCHITECT] [SKILL: SPEC-DRIVEN]` | escrever SPEC markdown com ACs mensuráveis antes de build |
| `[AGENT: BUILDER]` puro | implementar contra spec aprovada, sem invenção de colunas |
| `[AGENT: BUILDER] + Design System tokens` | UI alinhada à marca do avaliador |
| `[AGENT: REVIEWER] [SKILL: SEC-SCAN]` | code review cético item-a-item; "nada de looks good" |
| `[AGENT: REVOPS-EXPERT]` | teste de uso por persona não-técnica; captura confuses e próximas iterações |
| `[SKILL: MEMORY-OPT]` | consolidar sessão — vira ponto de partida pra próxima |

## 3. Erros da IA (GLM-5.2) e correções aplicadas

| # | Onde | Erro | Correção |
|---|------|------|----------|
| E-1 | EDA inicial | Assumiu `engage_date` em ISO; real era MM/DD/YYYY | `pd.to_datetime(..., format='%m/%d/%Y')` — virou instinto do HARNESS |
| E-2 | Spec do scoring | IA sugeriu peso 5% para win rate do agente | Elevei para 15% baseado na EDA (dispersão 42-67%) |
| E-3 | App Streamlit | Gerou `st.selectbox("Vendedor", ["Option 1"])` hardcoded | Corrigido para ler `df.unique()` em runtime |
| E-4 | App Streamlit | Não tratou edge case `engage_date=NaT` em abertos | Spec E1 definiu velocity=0 com label específico |
| E-5 | Streamlit API | `use_container_width=True` deprecated (warning 2025-12-31) | Substituído por `width="stretch"` |
| E-6 | Label agente novo | Dizia "win rate 50%" mascarando agente sem histórico | Spec E5: label explícita "novo, sem histórico ainda" |
| E-7 | Conversão de data duplicated | `score_deal` reconvertia dentro de apply (lento) | Movida para caller `score_pipeline` conforme SPEC seção 6 |
| E-8 | Color_discrete_map incompleto | Só mapeava Engaging/Prospecting | Adicionei Won/Lost para robustez futura |
| E-9 | PII em arquivo auxiliar | `_agent_winrate_synth.csv` redundante | Adicionado ao `.gitignore` |

## 4. Estado atual do repositório

### Estrutura final entregue

```
submissions/Gabriel Oliveira/
├── README.md                                ← template oficial preenchido
├── docs/
│   └── HARNESS_STEPS.md                     ← sistema operacional agentic
├── process-log/
│   ├── PROCESS_LOG.md                       ← evidência viva (coração do process log)
│   ├── PROMPT_01_research_first.md
│   ├── PROMPT_02_eda.md
│   ├── PROMPT_03_spec_scoring.md
│   ├── PROMPT_04_build_scoring.md
│   ├── PROMPT_05_app_streamlit.md
│   ├── PROMPT_06_review.md
│   ├── PROMPT_07_revops_test.md
│   └── PROMPT_08_memory_opt.md              ← este arquivo
└── solution/
    ├── app.py                               ← Streamlit app (~320 linhas)
    ├── scoring.py                           ← score_deal + score_pipeline
    ├── eda.py                               ← EDA com output em arquivo
    ├── test_scoring_ac.py                   ← suite de ACs da SPEC
    ├── generate_synth_data.py               ← fallback se Kaggle indisponível
    ├── requirements.txt                     ← streamlit, pandas, plotly, numpy, openpyxl
    ├── eda_report.txt                       ← output gerado pela EDA
    ├── .streamlit/
    │   └── config.toml                      ← tema G4 aplicado
    └── data/                                ← CSVs (sintéticos ou reais do Kaggle)
        ├── accounts.csv
        ├── products.csv
        ├── sales_teams.csv
        └── sales_pipeline.csv
```

### Métricas de qualidade

| Métrica | Valor |
|---------|-------|
| Arquivos entregues | 17 (código + docs + logs) |
| Linhas de código Python | ~1.200 (app+scoring+eda+test+gen) |
| ACs da SPEC validados | 8/8 PASS |
| Bugs críticos do review | 0 |
| Correções aplicadas pós-review | 6 (R1, R2, R10, R12, R19, R25) |
| Prompts harness executados | 8/8 |
| Score range observado | 15.8 a 71.4 (4.708 deals abertos scored) |
| Top-10 deals | 10/10 Engaging (valida peso 25% de stage) |
| Componentes explicáveis | 6/6 com label PT-BR |
| Design system G4 tokens aplicados | 8 (3 cores + 2 fontes + 3 component tokens) |

### Branch git

- Repo clonado de `Gestao-Quatro-Ponto-Zero/ai-master-challenge`
- Branch local: `submission/seu-nome` (do CONTRIBUTING.md)
- Pasta renomeada para `Gabriel Oliveira`
- **PR não aberto ainda** — precisa de fork no GitHub do Gabriel + push + PR

## 5. Próximos 3 passos imediatos

### Passo 1 — Abrir o PR (bloqueia entrega)
1. Criar fork do `ai-master-challenge` na conta GitHub do Gabriel
2. Adicionar remote do fork: `git remote add fork https://github.com/GABRIEL-USUARIO/ai-master-challenge.git`
3. Push: `git push fork submission/seu-nome`
4. Abrir PR no GitHub com título `[Submission] Gabriel Oliveira — Challenge 003`
5. No corpo do PR colar o executive summary do README.md

### Passo 2 — Swap dataset sintético → real do Kaggle
1. Conseguir credenciais Kaggle API (`kaggle.json` em `~/.kaggle/`)
2. Rodar `kaggle datasets download -d agungpambudi/crm-sales-predictive-analytics -p data --unzip`
3. Substituir os 4 CSVs sintéticos pelos reais
4. Re-rodar `python eda.py` → atualizar `eda_report.txt`
5. Re-rodar `python test_scoring_ac.py` → confirmar que ACs continuam PASS
6. Commit com mensagem "feat: swap to real Kaggle dataset"

### Passo 3 — Iterações recomendadas pelo Head de RevOps (PROMPT_07)
Antes de rollout full pros 35 vendedores, aplicar 3 fixes:

1. **Account humanizada (1h)** — substituir `account_0077` por `industry · country · parent_company` no card (já estão no accounts.csv, só falta expor). Resolve C7.
2. **Ação no deal (2h)** — botão "Assumir"/"Descartar" via `st.session_state` que marca `status` no DataFrame local. Resolve C5.
3. **PII toggle (30min)** — checkbox "Modo apresentação" na sidebar que mascara `sales_agent` para `agent_NN`. Resolve C4.

Esses 3 fixes promovem o app de "demo boa" para "ferramenta usada no dia-a-dia".

---

## Reflexão final do SKILL-05

### O que funcionou bem no harness
- **Schema validation antes de qualquer prompt de implementação** (instinct "GLM-5.2 alucina colunas") preveniu bugs caros
- **Prompt envelopes `[AGENT: X] [SKILL: Y]`** tornaram cada interação rastreável e reproduzível
- **SPEC markdown aprovada antes do build** forçou arquitetura humana antes de execução de IA
- **Bug encontrado e corrigido em loop** (R1-R25 do Prompt 06) confirmou valor do AGENT-REVIEWER

### O que melhoraria na próxima sessão
- **Mais iterações usuario-AGENT-D durante o build**, não só no final — pegaria C7 (account_0077 como ID inútil) antes do Prompt 05
- **Capturas de screenshots com Playwright em mais etapas** — visual > textual pras evidências
- **Calibração dinâmica de ranges de MinMax** com percentis reais (R3 diferido) faria scores mais discriminantes

### Insight estratégico final
O desafio foi resolvido dentro do budget de 4-6h do challenge. Mas o valor real está no **harness como ativo reutilizável** — os 8 prompts viram templates para qualquer outro challenge de "build com IA". O HARNESS.md não é documentação do Lead Scorer, é documentação de **como Gabriel opera com IA em qualquer problema**.

---

_Estado final do harness:_
- Skill: MEMORY-OPT ✅ executada, resumo persistido
- Sessão: 8/8 prompts completos
- Próxima sessão: executar Passo 1 (abrir PR no GitHub)
