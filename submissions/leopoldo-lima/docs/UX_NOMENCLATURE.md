# Nomenclatura da UI (CRP-UX-05)

**Idioma:** português (Brasil) nos rótulos voltados ao utilizador comercial.

## Estágios do negócio

Os valores canónicos na API e no dataset permanecem em inglês (`Prospecting`, `Engaging`, `Won`, `Lost`). Na UI, os **badges** de estágio usam rótulos em português:

| Valor (API / CSV) | Rótulo na UI |
|-------------------|--------------|
| Prospecting | Prospecção |
| Engaging | Engajamento |
| Won | Ganho |
| Lost | Perdido |

## Faixa de prioridade

A API usa `high` | `medium` | `low`. Na UI:

| API | UI |
|-----|-----|
| high | Alta |
| medium | Média |
| low | Baixa |

## Campos de negócio (sem jargão técnico)

- **Conta**, **Produto**, **Vendedor**, **Gestor**, **Escritório regional**, **Valor de fecho** — alinhados ao vocabulário do challenge.
- Evitar expor nomes de parâmetros HTTP (`region`, `deal_stage`) nos rótulos principais; mantê-los apenas em documentação técnica.

## Modo mock

Quando `LEAD_SCORER_REPOSITORY_MODE=mock`, a cópia deixa explícito que é **ilustrativa** (dados de desenvolvimento), não o dataset oficial.
