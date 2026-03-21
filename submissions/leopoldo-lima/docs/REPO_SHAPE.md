# Forma do repositório (CRP-REAL-06)

## Objetivo
Deixar **óbvio** para um avaliador onde está a solução executável e onde está **material de apoio / protótipo importado**.

## Antes → depois (raiz)

### Antes (ruído misturado com a solução)
- Três pastas `focus-score-*` com CRPs importados ao lado de `src/` e `public/`.
- `prompts/` com dezenas de `.txt` na raiz.
- `concat_repo_all_text.py` e, por vezes, `repo_concat_all.md` (arquivo gigante) na raiz.

### Depois (isolamento)
- **Raiz:** código, testes, dados, docs do produto, `crps/executed/` (CRPs curados por tema) + `indexes/`, CI, Docker.
- **`legacy/`:** pacotes `focus-score-*`, `prompts/` de metodologia, ferramenta de concat e (se existir) o dump `repo_concat_all.md`.

## Árvore lógica (resumo)

```
build-003-lead-scorer/
├── src/                 # Backend Python (API, serving, scoring, …)
├── public/              # UI shell
├── tests/               # Pytest
├── data/                # CSVs oficiais + demo JSON
├── config/              # Regras de scoring, normalização, …
├── docs/                # Documentação do produto e processo
├── scripts/             # Task runner, validações
├── contracts/           # Contrato de dados (JSON)
├── artifacts/           # Evidências de processo
├── crps/executed/       # CRPs curados: foundation, data, ui, product-tuning, submission
├── indexes/             # crp-index.csv, suggested-repo-tree.md
├── archive/             # Superseded (lista plana antiga, pack de importação curada)
├── legacy/              # ← Pacotes importados, prompts .txt, tools ad-hoc
├── README.md
└── …
```

## Critérios de corte (decisão humana + IA)

| Critério | Ação |
|----------|------|
| Pasta não importada por `src/`, `tests`, `public` nem CI | Candidata a `legacy/` se for só metodologia/prompts. |
| Artefato regenerável e muito grande (`repo_concat_all.md`) | Manter fora da raiz; opcionalmente ignorado no Git. |
| Trilha `crps/` | **Curada (CRP-SUB-08):** definições em `crps/executed/`; índice em `indexes/crp-index.csv`; cópias superseded em `archive/superseded/`. |

## Riscos da IA (mitigados)

- **Apagar demais:** evitado — não se removeu `crps/` nem `docs/`; apenas isolaram-se pacotes claramente “importados”.
- **Preservar demais:** `legacy/README.md` documenta o que ficou e porquê; avaliador pode ignorar `legacy/` por completo ao correr o produto.

## Verificação

```powershell
python .\scripts\tasks.py test
python .\scripts\tasks.py lint
```
