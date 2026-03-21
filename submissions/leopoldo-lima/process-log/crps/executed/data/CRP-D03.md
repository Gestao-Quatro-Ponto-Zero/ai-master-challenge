# CRP-D03 — Mapa de normalização semântica

## Objetivo
Resolver divergências conhecidas sem mutilar o raw.

## Caso obrigatório
- `GTXPro` no pipeline precisa ser reconciliado com `GTX Pro` do catálogo

## Tarefas
- criar `normalization_map`
- separar correção semântica, alias técnico e fallback
- garantir rastreabilidade: valor original + valor canônico

## Saídas
- `docs/NORMALIZATION_RULES.md`
- `src/.../normalization/`
- atualização de `ADR`

## Definition of Done
- produto do pipeline consegue casar com catálogo
- a normalização não altera o CSV original
- existe teste cobrindo `GTXPro -> GTX Pro`

## Prompt para o Cursor
```text
Implemente o CRP-D03: normalização semântica controlada.

Contexto:
O dataset tem divergência conhecida de produto:
- catálogo: GTX Pro
- pipeline: GTXPro

Tarefa:
1. Criar uma camada de normalização separada da ingestão raw.
2. Implementar mapa de alias/canonicalização para campos de join de negócio.
3. Manter rastreabilidade:
   - valor original
   - valor normalizado
4. Criar docs/NORMALIZATION_RULES.md com:
   - campo
   - problema
   - regra aplicada
   - risco
5. Adicionar testes cobrindo os casos conhecidos.
6. Atualizar ADR e LOG.md.

Critérios:
- Não editar os CSVs manualmente
- Não esconder a divergência
- Normalização deve ser audível
```
