# CRP-UX-10 — Capturas finais sugeridas (competição)

Gerar **depois** de `python .\scripts\tasks.py dev` com dataset real (sem `demo_dataset`).

## arquivos sugeridos (`artifacts/process-log/screenshots/`)

| arquivo | Conteúdo |
|----------|----------|
| `ux-final-cockpit-dashboard.png` | KPIs + barra de filtros + tabela com colunas Faixa / Próxima ação + painel de detalhe. |
| `ux-final-filters-applied.png` | Filtros preenchidos + contagem de resultados. |
| `ux-final-detail-explain.png` | Painel com herói de score, cartões e “Porque este score?”. |
| `ux-final-empty-state.png` | Estado vazio após filtros impossíveis (opcional). |

## Narrativa mínima

1. Dados reais (~8800 oportunidades) visíveis no resultado.
2. Explicabilidade legível (sem JSON cru).
3. Filtros como ferramenta (limpar, contagem, pesquisa).

## Relação com código

- UI: `public/index.html`, `public/styles.css`, `public/app.js`
- API: `GET /api/opportunities` com `q`, `priority_band` (ver `docs/API_CONTRACT_UI.md` se atualizado)
