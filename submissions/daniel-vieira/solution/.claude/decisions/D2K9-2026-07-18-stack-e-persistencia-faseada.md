---
id: D2K9
project: LeadScorer
subject: Stack da aplicação e persistência faseada
author: dcvr@
status: accepted
created: 2026-07-18
updated: 2026-07-18
---


# Contexto (por que a decisão é necessária)

O projeto requer uma linguagem de propósito geral, uma pilha web e uma camada de persistência
para um MVP de classificação e distribuição de leads, avaliado por usabilidade e
explicabilidade para usuários não técnicos. As regras da casa fixam Common Lisp sobre SBCL como
linguagem de propósito geral e PostgreSQL como persistência. As escolhas de bibliotecas foram
precedidas de pesquisa em fontes primárias (documentação oficial e repositórios), conforme as
cláusulas de cautela do CLAUDE.md. O usuário confirmou uma aplicação web server-side em Common
Lisp com HTMX e PostgreSQL e definiu que a fase de modelagem operaria diretamente sobre os
arquivos CSV, postergando o banco.


# Decisão (o que foi decidido)

Adota-se persistência faseada. Na fase de modelagem, o código Common Lisp lê os arquivos CSV
diretamente (biblioteca fare-csv), com testes em Parachute e dependências fixadas com qlot. Na
fase de aplicação, adota-se Clack sobre Hunchentoot como servidor, Ningle para roteamento,
Spinneret para renderização de HTML e fragmentos, PostgreSQL via Postmodern (sem a camada DAO
de CLOS, vedada pelo std-common-lisp) e HTMX 2.0.x servido como ativo estático. As migrações de
schema são arquivos SQL numerados e versionados, aplicados por script. O PostgreSQL é
introduzido apenas na fase de aplicação.


# Alternativas consideradas (o que mais foi ponderado)

- Woo como servidor: descartado por status beta auto-declarado, dependência da biblioteca C
  libev e restrição a sistemas UNIX; desnecessário para um MVP.
- cl-who para renderização: descartado por não escapar valores por padrão, elevando o risco de
  XSS; Spinneret escapa por padrão.
- cl-dbi para acesso ao banco: descartado por prover independência de banco desnecessária;
  Postmodern é mais maduro e específico para PostgreSQL, com queries parametrizadas e S-SQL.
- Snooze e Caveman2 para roteamento: descartados por perfil orientado a REST ou a baterias
  incluídas, inadequado a uma interface HTML server-side; Ningle é minimalista e dá controle
  total da resposta, necessário para devolver fragmentos.
- Mito para migração e ORM: descartado por status alpha auto-declarado e por auto-migração
  arriscada em produção.
- cl-csv para leitura de CSV: descartado por arrastar a cadeia cl-interpol e cl-unicode, que
  tenta construir tabelas Unicode em tempo de carga, tornando a compilação frágil e pesada;
  fare-csv é enxuto e cobre o RFC 4180.
- Streamlit ou Python: descartado por violar integralmente o stack canônico Common Lisp.


# Consequências (o que resulta da decisão)

- Aderência ao stack canônico Common Lisp e PostgreSQL das regras da casa.
- A fase de modelagem permanece enxuta, operando sobre CSV sem erguer banco nem contêiner.
- O escaping por padrão do Spinneret reduz o risco de XSS; o uso de HTMX exige definir
  htmx.config.allowEval a falso sob uma CSP estrita.
- A camada de migração não dispõe de biblioteca canônica madura; assume-se o uso de arquivos
  SQL numerados, cuja aplicação idempotente é responsabilidade de um script próprio.
- O padrão de integração HTMX com Common Lisp não é coberto pela documentação oficial e é
  implementado manualmente, inspecionando o cabeçalho HX-Request para decidir entre fragmento e
  página completa.
- As dependências ficam fixadas por qlot: Quicklisp 2026-01-01, fare-csv ql-2024-10-12,
  parachute ql-2026-01-01, registradas em qlfile e qlfile.lock.
- O qlot reside fora do PATH global neste ambiente; o Dockerfile da Fase B deve instalá-lo
  explicitamente.


# Relações

- supersedes:
- superseded-by:
- related-tasks: 7K2M, 9P4D, 3RJ8, 5T6Q, 8W2N
