# Process log — Lead Scorer

Índice das evidências de processo desta submissão.

## Onde olhar

- **[diario.md](diario.md)** — decisões fase a fase (auditoria → scoring →
  backtest → app), com o raciocínio e as trocas feitas em cada uma. É o
  documento mais importante deste log: mostra o "porquê", não só o "o quê".
- **[screenshots/](screenshots/)** — capturas do app funcionando (matriz,
  filtros, drivers expandidos) e do histórico de commits/conversas que
  geraram o código.

## Ferramentas de IA usadas

- **Claude Code** (Sonnet e Opus) — construção do pipeline de análise
  (`analysis/`), do motor de scoring, do backtest e do app (`app/`).
- **Claude (chat)** — discussão de abordagem e revisão de decisões fora do
  terminal.
- **Claude in Chrome** — teste funcional do app no navegador (matriz,
  filtros, drivers) antes de considerar cada fase concluída.

Detalhe técnico de cada fase (dados, mismatches, backtest) está em
`../analysis/`, não duplicado aqui.
