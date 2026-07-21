---
id: K9X4
parent: 8W2N
project: LeadScorer
subject: Fundacao da aplicacao web e identificacao por sessao (Fases 2-3 de 8W2N)
author: dcvr@
priority: medium
status: done
created: 2026-07-19
updated: 2026-07-20
---


# Descrição (o que será feito)

Erguer a fundacao executavel das duas aplicacoes web server-side segregadas do LeadScorer, a do
agente e a do gerente, conforme as Fases 2 e 3 do plano da tarefa-pai 8W2N. Compreende o esqueleto
Clack sobre Hunchentoot, o roteamento com Ningle, a renderizacao com Spinneret, o HTMX 2.0.x
servido como ativo estatico sob CSP estrita com 'htmx.config.allowEval' em falso, o layout base
derivado dos tokens do design system e dos protótipos da V7C2, e a identificacao por selecao do
usuario semeado, sem senha, com sessao de servidor e segregacao das duas aplicacoes por papel.
Nao contempla as listas de oportunidades, o painel de indicadores nem os servicos de ciclo, que
sao objeto das sub-tarefas seguintes de 8W2N.


# Motivações (por que será feito)

8W2N e ampla e composta e o seu plano exige decomposicao em sub-tarefas atomicas no inicio da
sessao. A Fase 1 (V7C2) entregou os protótipos estaticos e o modelo economico (W8H5); a
persistencia (9P4D) esta pronta. A fundacao executavel e a sessao sao a precondicao comum das
aplicacoes do agente e do gerente: sem servidor, layout base e identificacao com segregacao por
papel, nenhuma das telas subsequentes pode ser servida. Esta sub-tarefa isola esse nucleo comum
em um incremento coerente e verificavel, evitando acoplar a sua validacao a das telas de negocio.


# Recursos e dados necessários

- Stack de aplicacao do ADR D2K9 (Clack, Hunchentoot, Ningle, Spinneret, Postmodern, HTMX
  2.0.x), a ser fixada no 'qlfile' e no 'qlfile.lock' via qlot;
- Protótipos estaticos da V7C2 em '.claude/assets/examples/' como referencia do layout base
  (navbar, wordmark, menu responsivo, tema escuro Gray 100);
- Tokens do design system em '.claude/assets/tokens/' e as regras de '.claude/rules/design.md';
- Fontes IBM Plex locais em '.claude/assets/fonts/';
- Schema e seed da persistencia (9P4D): tabelas 'sales_agents', 'sales_managers' e demais, para
  a lista de selecao do login;
- Concepcao funcional em 'docs/concepcao-inicial.md' (estorias de identificacao e acesso,
  arquitetura server-side, segregacao das aplicacoes).


# Plano de trabalho (como será feito)

O plano detalhado e desenvolvido no modo de planejamento da sessao e registrado no worklog. Em
linhas gerais, seguindo as Fases 2 e 3 da tarefa-pai:

1. Fixar as dependencias de aplicacao no 'qlfile'/'qlfile.lock' via qlot e adicionar os
   componentes de aplicacao ao sistema ASDF;
2. Montar o esqueleto Clack sobre Hunchentoot, o roteamento Ningle e a renderizacao Spinneret,
   com o layout base a partir dos tokens e a servir o HTMX como ativo estatico sob CSP estrita;
3. Implementar a identificacao por selecao do usuario semeado, sem senha, com sessao de servidor
   e a segregacao das duas aplicacoes por papel;
4. Validar a responsividade do layout base (iPhone 13), a conformidade com o design system e a
   verificacao de software aplicavel.


# Riscos e ressalvas

- O padrao de integracao HTMX com Common Lisp nao e coberto por documentacao oficial e e
  implementado manualmente por inspecao do cabecalho HX-Request (ADR D2K9); nesta fase o HTMX e
  apenas provisionado como ativo, sem fragmentos de negocio;
- A adicao das dependencias de servidor ao 'qlfile' altera o grafo de dependencias e pode
  reintroduzir avisos de redefinicao analogos ao caso do UIOP/Postmodern ja tratado no
  'leadscorer.asd'; a compilacao limpa deve ser verificada apos a fixacao;
- A segregacao por papel sem gestao de papeis exige duas aplicacoes distintas; a decisao de como
  materializar a segregacao (dois handlers, duas portas ou um discriminador de sessao) deve ser
  fixada no planejamento.


# Dependências

- blocks:
- blocked-by: 9P4D, V7C2


# Definição de pronto

- As duas aplicacoes, do agente e do gerente, sobem sem avisos de compilacao e servem o layout
  base tematizado (tema escuro Gray 100, IBM Plex local) em conformidade com o design system;
- O HTMX 2.0.x e servido como ativo estatico sob CSP estrita com 'htmx.config.allowEval' em
  falso;
- O login por selecao do usuario semeado, sem senha, estabelece a sessao de servidor correta
  para cada papel, e as duas aplicacoes ficam segregadas;
- O layout base e responsivo no iPhone 13;
- A verificacao de software aplicavel passa (compilacao e carga sem avisos, testes Parachute,
  linter mallet, e as verificacoes de HTML, CSS e YAML pertinentes).
