# CRP-FIN-09 — Runtime padrão inequívoco

**Data:** 2026-03-21

## Ambiguidade anterior
Risco de um avaliador não perceber que **omissão de env** = dataset real.

## Fecho
- Documento `docs/RUNTIME_DEFAULTS.md` com tabela backend + UI.
- `.env.example` com cabeçalho explícito sobre padrão real.
- Código já garantia `real_dataset` e `api` por defeito; sem alteração de lógica obrigatória.

## Verificação
- Leitura cruzada `dataset_loader.py` + `repository-factory.js` + `.env.example`.
