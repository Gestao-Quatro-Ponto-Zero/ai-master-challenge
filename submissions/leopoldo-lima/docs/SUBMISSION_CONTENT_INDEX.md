# Índice da submissão — ordem de leitura recomendada

Todas as paths são relativas a `submissions/leopoldo-lima/`.

## Leitura essencial (avaliador com pouco tempo)

| Ordem | arquivo | Conteúdo |
|-------|----------|----------|
| 1 | [`README.md`](../README.md) | Narrativa da submissão, requisitos do challenge 003, como correr, onde está o process log |
| 2 | [`process-log/PROCESS_LOG.md`](../process-log/PROCESS_LOG.md) | **Process log obrigatório** — CRPs, IA, correções humanas |
| 3 | [`docs/SETUP.md`](SETUP.md) | Comandos de instalação e execução (a partir de `solution/`) |
| 4 | [`docs/SCORING_V2.md`](SCORING_V2.md) | Lógica de priorização e explicabilidade |
| 5 | [`docs/FINAL_AUDIT_CHALLENGE_003.md`](FINAL_AUDIT_CHALLENGE_003.md) | Matriz de aderência ao enunciado oficial |

## Process log e evidências

| Pasta / arquivo | Uso |
|------------------|-----|
| [`process-log/LOG.md`](../process-log/LOG.md) | Changelog operacional |
| [`process-log/decision-notes/`](../process-log/decision-notes/) | Notas de decisão e espelhos |
| [`process-log/chat-exports/`](../process-log/chat-exports/) | Exports / reconstruções de conversas |
| [`process-log/test-runs/`](../process-log/test-runs/) | Snapshots JSON (fluxo HTTP, dataset real) |
| [`process-log/ui-captures/`](../process-log/ui-captures/) | Guias e imagens de UI |
| [`process-log/crps/`](../process-log/crps/) | CRPs executados (Markdown) |
| [`process-log/indexes/crp-index.csv`](../process-log/indexes/crp-index.csv) | Índice tabular de CRPs |
| [`solution/artifacts/process-log/`](../solution/artifacts/process-log/) | **Só** saídas geradas por scripts ao correr a solução (ver README dentro da pasta) |

## Documentação complementar (profundidade técnica)

Contratos e API: [`API_CONTRACT.md`](API_CONTRACT.md), [`API_CONTRACT_UI.md`](API_CONTRACT_UI.md), [`DATA_CONTRACT.md`](DATA_CONTRACT.md).  
Arquitetura: [`ARCHITECTURE.md`](ARCHITECTURE.md), [`ADR/`](ADR/).  
Demo e operação: [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md), [`RUNBOOK.md`](RUNBOOK.md), [`RUNBOOK_UI_API_INTEGRATION.md`](RUNBOOK_UI_API_INTEGRATION.md).  
Testes: [`TEST_STRATEGY_REAL_DATA.md`](TEST_STRATEGY_REAL_DATA.md).  
PR: [`PR_HANDOFF.md`](PR_HANDOFF.md).  
Metadados do dataset: [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md) (gerado pelo pipeline em `solution/`).

## Arquivo (não é caminho principal)

- [`docs/archive/`](archive/README.md) — material legado / interno (ex.: narrativa antiga da pasta `submission/` do repo de trabalho).

## Referências oficiais do repositório do challenge

- [`submission-guide.md`](../../submission-guide.md)  
- [`templates/submission-template.md`](../../templates/submission-template.md)  
- [`challenges/build-003-lead-scorer/README.md`](../../challenges/build-003-lead-scorer/README.md)  
- [`CONTRIBUTING.md`](../../CONTRIBUTING.md)

## Princípio de separação

| Pasta | Função |
|-------|--------|
| `solution/` | Produto executável, dados, scripts, CI, artefatos **gerados por ferramentas** |
| `process-log/` | Rastreabilidade, CRPs, evidências entregues |
| `docs/` | Documentação complementar e auditorias |
