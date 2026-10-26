# Chat exports

- **`sessao-orquestracao-claude-code.md`**: a sessão do Claude Code que executou os blocos 0 a 7 (25/10/2026). Começa com o meu prompt de operação e traz cada mensagem minha com horário, o texto do orquestrador (Claude Opus 5.5), os subagentes disparados (com modelo e esforço) e os retornos deles.
  - **Como foi gerado:** veio do export oficial do app (`session-export-*.zip`, cerca de 13 MB, com as transcrições completas dos subagentes) por um script, sem edição manual.
  - **O que foi omitido:** as saídas de ferramentas, os lembretes de sistema e o meu e-mail. Os relatórios completos dos subagentes também ficaram de fora; eles estão consolidados nos `process-log/NN_bloco-N.md`.
- **Fase 0 (app do Claude):** não tem export. Está registrada em narrativa em `process-log/00_fase0_exploracao.md`, com os scripts e as saídas em `process-log/scripts/` e `process-log/outputs/`.

O mapa completo das evidências está em `process-log/README.md`.
