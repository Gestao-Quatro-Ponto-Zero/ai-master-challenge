# Trilha CRP-UX-01 … UX-10 — Pacote competição UX

**Data:** 2026-03-20  
**Origem:** `legacy/focus-score-ux-competition-pack/` (prompt master + CRPs)

## Resumo executivo

- **UX-01:** reforço de que o runtime principal da UI usa API default `api` + dataset real; cópia no header e comentário na factory.
- **UX-02:** detalhe em cartões / herói de score; remoção de qualquer `JSON.stringify` no `app.js`.
- **UX-03:** layout cockpit (grid KPI → filtros + ranking + painel lateral).
- **UX-04:** colunas Faixa, Próxima ação; primeira linha com `is-top-pick`.
- **UX-05:** rótulos PT estágio/faixa; `docs/UX_NOMENCLATURE.md`.
- **UX-06:** tokens CSS, badges, cartões (inspiração visual sem reintroduzir domínio errado).
- **UX-07:** filtros compactos, limpar, contagem, `q` + `priority_band`; API estendida.
- **UX-08:** mensagens de loading / erro / vazio mais claras.
- **UX-09:** `tests/test_ui_competition_pack.py` + ajustes em smoke/coverage.
- **UX-10:** guia de screenshots `UX-COMPETITION-FINAL-GUIDE.md`; README/DEMO/PROCESS_LOG atualizados.

## Lovable

Não havia código Lovable no repo; decisão documentada: padrões visuais reimplementados de forma mínima e alinhada ao domínio atual.

## Artefatos

- `public/*`, `src/api/app.py`, `tests/test_ui_competition_pack.py`, `docs/UX_NOMENCLATURE.md`, `docs/UX_DECISIONS.md`, `README.md`, `docs/DEMO_SCRIPT.md`, `PROCESS_LOG.md`, `LOG.md`
