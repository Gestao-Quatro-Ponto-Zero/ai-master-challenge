# Decisões de framing — README de submissão (CRP-REAL-07)

Este arquivo regista **escolhas humanas** na reescrita do `README.md` para leitura de **submissão final**, não de “pacote-base”.

## Objetivo

- Primeira impressão: **produto entregue ao Challenge 003 — Lead Scorer**.
- Reduzir na raiz listas longas de CRPs, arquivos duplicados e instruções do tipo “cole este pacote no repo”.

## O que foi cortado ou movido para referências

- **Lista extensa “Base documental criada neste repo”** (~100 linhas com entradas repetidas): substituída por **tabela curta** + remissão genérica a `docs/`.
- **“Como usar” (passos de importação do pack)** e **“O que este pacote não faz”**: removidos do README principal — não comunicam entrega final ao avaliador.
- **Quick Start com dezenas de comandos `tasks.py` em sequência**: condensado para `install` + `build` + `dev`; detalhe mantido em `docs/SETUP.md`.
- **Ordem longa CRP-000…CRP-012 + S01…S07**: substituída por `crps/executed/`, `indexes/crp-index.csv` e `docs/CRP_GOVERNANCE.md` (CRP-SUB-08).

## O que foi mantido explícito (honestidade)

- Modo **`real_dataset`** por omissão vs **`demo_dataset`** para testes.
- **Limitações** (Docker, métricas em memória, UI simples, ausência de calibração por outcome).
- Ligação obrigatória ao **`PROCESS_LOG.md`** e **`artifacts/process-log/`**.

## Onde a IA tende a exagerar (e como foi contido)

- **Marketing:** evitar superlativos (“enterprise-ready”, “production-grade”) sem prova no repo; o texto descreve o que existe (testes, contratos, CI local).
- **Metodologia:** não usar o README como substituto do process log; CRPs são **apontados**, não recontados linha a linha.

## Julgamento humano

- Priorizar **secções exigidas pelo guide** (Executive Summary, Abordagem, Resultado, Recomendações, Limitações, Setup, Demo) **no topo**, antes de pointers administrativos.
- Incluir **checklist de secções** no próprio README e duplicar a verificação na nota de evidência em `artifacts/process-log/decision-notes/crp-real-07-readme-submission.md`.

## Artefatos relacionados

- `README.md` (raiz)
- `artifacts/process-log/decision-notes/crp-real-07-readme-submission.md`
- `PROCESS_LOG.md` — bloco **CRP-REAL-07**
- `LOG.md` — entrada do dia
