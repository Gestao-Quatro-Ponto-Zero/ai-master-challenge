# CRP-FIN-01 — Combobox gestor: lista completa + filtro incremental

**Data:** 2026-03-21  
**Ferramenta:** Cursor (agente)

## Por que o textbox / “só após N letras” era insuficiente
Gestores reais precisam ver **toda a equipa** ao abrir o campo, não adivinhar prefixos; o requisito FIN-01 pede lista completa ao focar e filtro ao digitar.

## Implementação
- `listAllOrFilterManagers` em `public/shared/filter-options-utils.js`: query vazia devolve cópia ordenada da lista; com texto usa `filterManagersByQuery` com `minLen: 1` (prefixo antes de contém).
- `wireManagerCombobox`: estado `panelOpen`; **focus** abre painel e pinta lista; primeira opção **«Todos os gestores»** limpa o filtro; **input** mantém painel aberto e refiltra; teclado/rato inalterados na essência.
- `index.html` / `app.js`: novo placeholder e hint; `aria-haspopup="listbox"`.
- `scripts/capture_cbx08_screenshots.py`: fluxo alinhado (lista completa após clique, filtro incremental).

## Foco / teclado
- **ArrowDown** com painel fechado abre a lista; **Esc** e clique fora fecham (já coberto por `closePanel`).

## Verificação
- `python -m pytest -q`
