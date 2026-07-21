---
id: T3F9
parent:
project: leadscorer
subject: Corrigir o slug de 'export-session' para resolver a transcricao bruta em worktree
author: dcvr@
priority: medium
status: done
created: 2026-07-20
updated: 2026-07-20
---


# Descrição (o que será feito)

Corrigir a funcao de resolucao do caminho bruto em 'scripts/export-session' para que o slug do
diretorio de trabalho seja computado da mesma forma que o Claude Code nomeia o diretorio de
projeto em '~/.claude/projects/'. Atualmente o script substitui apenas '/' por '-'
('slug="${PWD//\//-}"'), enquanto o Claude Code substitui tambem '.', logo os caminhos que
contem '.' (em particular '.claude', presente em qualquer worktree sob '.claude/worktrees/') nao
sao resolvidos e a exportacao automatica falha.


# Motivações (por que será feito)

Na sessao S5J4-2026-07-20-1, executada em um worktree, a exportacao da transcricao pelo
'export-session' nao resolveu o caminho bruto automaticamente: o slug computado
('...mvp-leadscorer-.claude-worktrees-...') diverge do nome real do diretorio de projeto
('...mvp-leadscorer--claude-worktrees-...'). O encerramento usou o contorno de passar
o caminho bruto explicito, mas a resolucao automatica deve funcionar para qualquer sessao,
inclusive em worktree, sem intervencao manual.


# Recursos e dados necessários

- O script 'scripts/export-session' (funcao 'resolve_raw_path') e o filtro
  'scripts/sanitize-transcript.jq';
- Os testes 'bats-core' do script, ou a criacao de um caso cobrindo um PWD com '.';
- A convencao de nomeacao de diretorio de projeto do Claude Code em '~/.claude/projects/'.


# Plano de trabalho (como será feito)

1. Ajustar o calculo do slug para substituir tambem '.' por '-' (por exemplo, uma segunda
   expansao de parametro), confirmando contra o nome real do diretorio de projeto;
2. Cobrir o caso por teste, com um PWD sintetico que contenha '.', verificando a resolucao;
3. Validar com 'shellcheck' e executar a exportacao de uma sessao real de worktree sem contorno.


# Riscos e ressalvas

- O contorno (caminho bruto explicito) ja funciona, de modo que a correcao e de conveniencia e
  robustez, nao bloqueante;
- Deve-se confirmar a regra exata de nomeacao do Claude Code (quais caracteres alem de '/' e '.'
  sao substituidos) para nao introduzir uma segunda divergencia.


# Dependências

- blocks:
- blocked-by:


# Definição de pronto

- 'export-session' resolve o caminho bruto automaticamente para uma sessao em worktree,
  sem o contorno de caminho explicito;
- O comportamento esta coberto por teste e o 'shellcheck' nao relata avisos.
