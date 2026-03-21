# UX Decisions (Tabela e Drawer)

Decisões de UX operacional aplicadas ao dashboard da UI shell.

## Melhorias implementadas
- tabela de oportunidades substituiu lista simples para leitura mais previsível
- seleção persistida quando o item segue visível após aplicar filtros
- fallback automático para primeiro item quando seleção anterior sai do resultado
- drawer com estados explícitos:
  - loading
  - sucesso
  - not found
  - erro genérico
  - requisição cancelada
- ações do drawer:
  - `Tentar novamente`
  - `Fechar detalhe`
- acessibilidade básica:
  - linhas da tabela focáveis
  - abrir detalhe com `Enter` e `Espaço`

## Trade-offs
- sem paginação/ordenação visual neste estágio (apenas preparo estrutural da tabela)
- sem framework de componentes (mantido JS modular para aderência ao snapshot)

## Preparação para evolução
- estrutura de tabela e seleção já pronta para paginação/ordenação futura
- hook de dados já suporta cancelamento/retry, reduzindo retrabalho da UX

## Filtros combobox + select (CRP-CBX-01 … CBX-08)
- **Escritório regional** e **estágio**: `<select>` preenchidos a partir de `GET /api/dashboard/filter-options` (listas deduplicadas e ordenadas no servidor; cliente reutiliza `normalizeSortDedupeStrings`).
- **Gestor comercial**: combobox com autocomplete **a partir de 3 caracteres** (debounce ~120 ms), setas/Enter/Esc, valor enviado à API via campo oculto `manager-value` (parâmetro `manager` inalterado).
- **Compat API**: resposta inclui `regional_offices` e `regions` (espelho); a UI prefere `regional_offices` quando presente.
- **CBX-08 / FIN-01 / FIN-02**: combobox **funcional** (lista da API, **lista completa ao focar** + filtro incremental, helper dinâmico, estado **A carregar gestores…**, `aria-busy`), filtro **prefixo → contém** via `listAllOrFilterManagers` / `filterManagersByQuery`, `aria-haspopup="listbox"`, `aria-selected` nas opções, fecho com **clique fora** (`pointerdown` em `document`) e `aria-activedescendant` no teclado; **Esc** fecha e remove estado vazio; `destroy()` com `AbortController`.

## Trilha UX competição (CRP-UX-01 … CRP-UX-10)
- layout **cockpit**: KPIs no topo, ranking central, painel de detalhe lateral (desktop)
- detalhe em **cards** e herói de score — sem JSON cru nem `JSON.stringify`
- tabela com **faixa de prioridade**, **próxima ação** resumida e destaque da **primeira linha** (top pick)
- barra de **filtros** compacta: limpar filtros, contagem de resultados, pesquisa por conta/ID/título, faixa de prioridade
- nomenclatura: ver `docs/UX_NOMENCLATURE.md`
- testes de regressão: `tests/test_ui_competition_pack.py`
