# Evidência — CRP-SUB-08 (curadoria CRPs + narrativa)

**Data:** 2026-03-21

## Snapshot da estrutura `crps/executed/`

Contagem de arquivos `.md` por pasta (2026-03-21):

| Pasta | arquivos |
|-------|-----------|
| `foundation/` | 13 |
| `data/` | 24 |
| `ui/` | 37 |
| `product-tuning/` | 7 |
| `submission/` | 12 |
| **Total** | **93** |

Comando de verificação local:

```powershell
Get-ChildItem -Recurse -Filter *.md crps/executed | Group-Object { $_.Directory.Name } | Sort-Object Name
```

## O que foi arquivado

- arquivos que estavam em `crps/*.md` (lista plana) → `archive/superseded/crps-root-flat-pre-SUB-08/` (substituídos pela mesma versão curada sob `crps/executed/**`).

## Pacote curado de origem

- `focus-score-curated-crps/` foi movido para `archive/superseded/focus-score-curated-crps/` após cópia para `crps/executed/`, para reduzir duplicação na raiz do repositório (o canónico para leitura é `crps/executed/`).

## Onde a IA ajudou vs revisão humana

- **IA:** proposta de estrutura de pastas, redacção-base da narrativa cronológica, agregação do índice CSV a partir do pack curado.
- **Humano:** decisão de visibilidade (executed vs archive), validação de coerência com o produto real (`public/`, `src/`), tom não promocional e URL canónica do livro.

## Diff de narrativa

- `README.md` — secção curta «Construção com IA»
- `docs/IA_TRACE.md` — narrativa longa por fases + tabela S07 preservada
- `docs/SUBMISSION_STRATEGY.md` — secção executiva sobre uso de IA
