# Maintenance Notes — Lead Scorer (Quick Reference)

> Versão resumida do runbook. Para detalhes completos, ver `PROJECT_MASTER_REPORT.md`.

## Rodar localmente

```powershell
cd "...\submissions\Gabriel Oliveira\solution"
.\venv\Scripts\python.exe -m streamlit run app.py --server.port 8502 --server.headless true
```

## Rodar testes

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
.\venv\Scripts\python.exe test_scoring_ac.py
```

## Onde mexer no que

| Quero alterar | Arquivo | Função/Seção |
|---------------|---------|--------------|
| Pesos do score | `scoring.py` | `WEIGHTS` (dict) |
| Lógica de um componente | `scoring.py` | `score_deal()` |
| Normalização | `scoring.py` | `_minmax()` |
| Tokens/cores/fontes | `app.py` | bloco `CSS` |
| Tema base Streamlit | `.streamlit/config.toml` | `[theme]` |
| Filtros sidebar | `app.py` | `render_sidebar()` |
| KPIs | `app.py` | `render_kpi()` + `main()` |
| Top-N deals | `app.py` | loop em `main()` |
| Tabela | `app.py` | `st.dataframe` em `main()` |
| Charts | `app.py` | `render_distribution_chart()` / `render_scatter_chart()` |
| Assistente Follow-up | `app.py` | `render_followup_assistant()` |
| Texto das copys | `followup_engine.py` | `_copy_templates()` |
| Ganchos por DISC | `sales_hooks.py` | `PROFILE_HOOKS` |
| Próxima melhor ação | `sales_hooks.py` | `get_next_best_action()` |
| Inferência DISC | `disc_profile.py` | `infer_disc_profile()` |
| Schema LeadProfile | `disc_profile.py` | `build_lead_profile()` |

## Depuração rápida

- **NaT em datas:** confirmar `format='%m/%d/%Y'` em `score_pipeline`.
- **Widget duplicado:** função não deve ser chamada dentro de loop; usar `key` único.
- **Clipboard não copia:** sandbox do iframe; fallback "Selecionar texto" já existe.
- **Score fora de [0,100]:** checar `_minmax()` clamping.
- **DISC sempre indefinido:** verificar se `deal_stage` e `close_value` estão populados.

## Design system canônico

- Fonte: `docs/G4-DESIGN-SYSTEM-PROMPT.md` (prevalece sobre qualquer versão antiga).
- Tokens de badge: >80 verde (color-6), 50-80 gold (color-5), <50 primary-color.

## Limitações ativas

- Dataset sintético (credenciais Kaggle indisponíveis).
- `TODAY` fixado em 2025-07-01 (determinismo).
- PII `sales_agent` exibida (roadmap: toggle).
- `df.apply` não vetorizado (OK para 4.708 deals).

## Próximos 3 fixes rápidos

1. Account humanizada (1h).
2. PII toggle (30min).
3. Ação no deal via `st.session_state` (2h).
