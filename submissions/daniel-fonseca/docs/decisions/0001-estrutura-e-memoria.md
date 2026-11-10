# 0001 — Estrutura do repositório e memória agnóstica de harness

- **Status:** Aceita
- **Data:** 2026-11-09
- **Origem:** Daniel (requisito: memória persistente entre sessões e harnesses; poder trocar Claude Code ↔ Codex) · IA (desenho)

## Contexto
O trabalho vai atravessar várias sessões e possivelmente dois harnesses (Claude Code e Codex). Memórias locais de cada ferramenta (`~/.claude/...`, `~/.codex/...`) não são compartilhadas entre si nem visíveis para o avaliador. O G4 também exige que **só** `submissions/daniel-fonseca/` seja modificado.

## Decisão
- Toda a memória canônica vive **dentro da pasta da submissão**, versionada:
  - `AGENTS.md` — regras e protocolo de sessão (formato lido nativamente pelo Codex; `CLAUDE.md` importa via `@AGENTS.md`).
  - `context/STATE.md` — handoff: feito / próximo / bloqueios.
  - `context/data-findings.md` — fatos verificados sobre os dados, com script de origem.
  - `docs/decisions/` — ADRs.
  - `process-log/` — narrativa cronológica + judgment log + evidências.
- Sessões de agente são abertas **dentro de `submissions/daniel-fonseca/`**, onde ficam `AGENTS.md`, `CLAUDE.md` e `.mcp.json`.
- Commits frequentes com trailer de co-autoria do agente → o `git log` vira evidência de processo.

## Alternativas consideradas
- Arquivos na raiz do repo (`/AGENTS.md`, `/.mcp.json`): carregamento mais natural, mas violaria a regra do PR.
- Memória só no Claude Code: some quando trocar para o Codex e o avaliador não vê.

## Consequências
- O avaliador enxerga a mesma memória que os agentes usaram — transparência total do workflow.
- Disciplina necessária: atualizar STATE e process log ao fim de cada sessão (regra no AGENTS.md).
- Arquivos novos entram via `scripts/git-add.sh` (o `.gitignore` upstream ignora `submissions/`; `git add -f` na pasta inteira arrastaria `.venv/` e `data/` — erro cometido e corrigido na sessão 01).
