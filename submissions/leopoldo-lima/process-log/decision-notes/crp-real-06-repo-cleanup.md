# CRP-REAL-06 — Evidência de limpeza / legado

## Árvore: o que mudou na raiz

**Removido da raiz (movido para `legacy/`):**
- `focus-score-challenge-gap-closure-pack/`
- `focus-score-ui-api-crps/`
- `focus-score-ux-competition-pack/`
- `prompts/`
- `concat_repo_all_text.py` → `legacy/tools/concat_repo_all_text.py`
- `repo_concat_all.md` (se existia) → `legacy/repo_concat_all.md`

**Mantido na raiz (solução + governança):**
- `src/`, `public/`, `tests/`, `data/`, `config/`, `docs/`, `scripts/`, `contracts/`, `artifacts/`, `crps/`, arquivos de projeto (`pyproject.toml`, Docker, README, …).

## Justificativa por bloco

| Bloco | Porque saiu da raiz |
|-------|---------------------|
| `focus-score-*` | Pacotes de **referência** de CRPs; não são módulos da aplicação. |
| `prompts/*.txt` | Artefactos de metodologia; confundem com código ou config do produto. |
| Concat + dump MD | Ferramenta local e saída **enorme**; enfraquecem a primeira impressão do repo. |

## O que **não** foi movido (e porquê)

- **`crps/`:** continua na raiz por contrato documental (`00-START-HERE.md`, `LOG.md`, `PROCESS_LOG.md`, `tasks.py` smoke). Realocar exigiria reescrita massiva de links; ganho marginal.

## Documentação nova

- `legacy/README.md` — índice do legado.
- `docs/REPO_SHAPE.md` — topologia oficial para submissão.
