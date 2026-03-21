# CRP-FIN-02 — Combobox gestor: busca, empty state, acessibilidade

**Data:** 2026-03-21

## Regra de busca (fechada)
- **Lista completa** ao focar (query vazia).
- **Filtro incremental** com `minLen: 1` em `filterManagersByQuery`: **prefixo primeiro**, depois **contém**, case-insensitive (`listAllOrFilterManagers`).
- Estado **«Nenhum gestor encontrado»** quando há texto e zero matches; **«Nenhum gestor disponível»** quando a API não devolve gestores.

## Teclado e foco
- **Tab**: não interceptado.
- **Esc**: fecha painel e remove mensagem de vazio.
- **Setas / Enter**: navegam e selecionam com `aria-activedescendant` e `aria-selected` nas opções.
- **ArrowDown** com painel fechado abre a lista.

## Acessibilidade
- `role="combobox"`, `aria-haspopup="listbox"`, `aria-controls`, `aria-expanded` sincronizado com painel, `aria-autocomplete="list"`.

## Evidência
- Regressão: `python -m pytest -q tests/test_ui_competition_pack.py`
