# Evidências do process log

Pasta **canónica** de evidências auditáveis ligadas a `PROCESS_LOG.md` **nesta submissão**. O código, ao correr a partir de `solution/`, pode gravar cópias de trabalho em `solution/artifacts/process-log/` — antes do PR, consolidar o que for relevante **aqui** (ver `solution/artifacts/process-log/README.md`).

## Convenção de nomes (sugestão)

- `YYYY-MM-DD_<CRP>_<tipo>_<slug-curto>.<ext>`
- Exemplo: `2025-03-20_CRP-004_test-run_score-engine.png`
- Sempre citar paths relativos no `PROCESS_LOG.md` (no repo de trabalho: `artifacts/process-log/...`; nesta submissão: `process-log/...` na pasta do candidato).

## Subpastas

| Pasta | Uso |
|--------|-----|
| `screenshots` | Capturas de menu de ferramentas, erros, configurações. |
| `chat-exports` | Exportações de conversas com IA (JSON, Markdown, TXT), **sem dados sensíveis**. |
| `test-runs` | Logs ou relatórios de execução de testes / validações reproduzíveis; exports HTTP do fluxo real (`python .\\scripts\\tasks.py export-real-flow-evidence` a partir de `solution/`, CRP-REAL-09). |
| `ui-captures` | Capturas da interface ou fluxos demonstráveis. |
| `decision-notes` | Notas curtas de decisão, checklists ou rascunhos que sustentam o log. |

Em cada entrada do `PROCESS_LOG.md`, referencie o caminho relativo ao repositório em que o texto foi escrito (no pacote de submissão: `process-log/test-runs/...`).

## Estrutura mínima versionada

As subpastas abaixo existem **nesta pasta** (podem estar vazias salvo `.gitkeep`):
- `screenshots/`
- `chat-exports/`
- `test-runs/`
- `ui-captures/`
- `decision-notes/`
