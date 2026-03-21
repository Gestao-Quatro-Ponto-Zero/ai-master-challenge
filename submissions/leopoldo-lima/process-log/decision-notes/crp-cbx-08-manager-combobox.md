# CRP-CBX-08 — Combobox «Gestor comercial» funcional

**Data:** 2026-03-21  
**Ferramenta de IA:** Cursor (agente Auto)

## Objetivo
Combobox digitável com autocomplete real a partir de 3 letras, lista servida por `GET /api/dashboard/filter-options`, sem migrar stack.

## Prompt relevante
Pedido do utilizador com requisitos funcionais/UX/técnicos (CRP-CBX-08 completo): estados, teclado, integração com filtros e evidências.

## O que a IA propôs / implementou
- Utilitário **`filterManagersByQuery`** em `public/shared/filter-options-utils.js`: busca case-insensitive com **prefixo primeiro**, depois **contém**; ordenação alfabética dentro de cada grupo.
- **`wireManagerCombobox`**: `rootEl` para fechar ao **clique fora** (`pointerdown` capture no `document`); `aria-activedescendant`; `Tab` explícito sem interferir; `destroy()` para remover listener ao re-inicializar.
- **`initFilterWidgets`**: estado **A carregar gestores…**, `disabled` + `aria-busy` no input durante fetch; após sucesso, helper **Digite 3 letras para buscar**; em falha de API, mensagem de erro e combobox com lista vazia.
- Markup: `id="manager-combobox-root"`, placeholder/helper alinhados ao texto do CRP.
- Testes em `tests/test_ui_competition_pack.py` para strings e utilitário.
- Guia de capturas: `artifacts/process-log/ui-captures/CBX-08-SCREENSHOT-GUIDE.md`.
- Resumo: `docs/CBX-08_MANAGER_COMBOBOX.md`.

## Erros / ajustes manuais
- Primeira versão do listener global em fase **capture** foi validada para não fechar ao clicar **dentro** de `manager-combobox-root` (inclui opções da lista).
- Indentação e hint pós-sucesso em `initFilterWidgets` corrigidos para não deixar «A carregar gestores…» após carregar.
- **Esc** passou a chamar `hideEmpty()` para fechar também a mensagem de zero resultados.
- `destroy()` reforçado: `AbortController` nos `addEventListener` do input + `clearTimeout` de debounce/blur (evita duplicar handlers se `initFilterWidgets` voltar a correr).

## Evidência gerada
- PNG (painel de filtros) em `artifacts/process-log/ui-captures/cbx-08/`: estados inicial, &lt;3 letras, sugestões com 3+ letras, sem resultados, gestor selecionado, após **Limpar filtros**.
- Regeneração automatizada: `python scripts/capture_cbx08_screenshots.py` (sobe `uvicorn` na porta `8799`, Playwright Chromium).
- `python -m pytest -q tests/test_ui_competition_pack.py tests/test_ui_smoke.py`.
