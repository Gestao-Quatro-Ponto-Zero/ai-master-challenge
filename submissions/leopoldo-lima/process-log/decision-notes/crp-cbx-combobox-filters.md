# CRP-CBX — Combobox gestor + selects (filter-options)

**Data:** 2026-03-20  
**Origem:** `focus-score-combobox-crps-pack/` (`cursor-master-prompt.md` + CRP-CBX-01…07)

## Decisões
- `GET /api/dashboard/filter-options` expõe `regional_offices`, `managers`, `deal_stages` com valores únicos (CI) e ordenados; `regions` duplica `regional_offices` para compat.
- UI: escritório e estágio como `<select>`; gestor como combobox com busca a partir de **3 caracteres** (`public/presentation/widgets/manager-combobox.js`), parâmetro HTTP `manager` inalterado.
- Estilos: `.combobox-wrap`, `.combobox-list`, `.combobox-option` em `public/styles.css`.

## Verificação
- `python -m pytest -q`
- `python scripts/tasks.py lint`
