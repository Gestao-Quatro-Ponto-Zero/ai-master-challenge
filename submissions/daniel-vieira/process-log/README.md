# Process Log — Índice da evidência

Este diretório é um índice. A evidência integral do trabalho assistido por IA reside em
`../solution/.claude/`, preservada no lugar original do projeto para não fragmentá-lo nem
quebrar as referências relativas entre a documentação, o código e os registros. Este documento
é o guia de leitura dessa evidência.

O projeto não foi construído por prompt único: foi conduzido por um pipeline assistido por LLM
com backlog, registro de sessão (worklog), transcrições higienizadas, registros de decisão de
arquitetura (ADR), code-review por fase e auditoria independente com contexto cortado. O que
segue mapeia onde cada tipo de evidência está.


## Onde está cada coisa

- `../solution/.claude/worklog/`: 27 worklogs de sessão, um por sessão de trabalho, com a
  conduta, as motivações e o raciocínio do que foi feito, mais o resumo histórico em
  `_historical.md`. É o registro de referência do processo;
- `../solution/.claude/sessions/`: 19 transcrições higienizadas das sessões, em formato JSONL,
  que preservam os prompts, as decisões e os nomes das chamadas de ferramenta e descartam as
  saídas de ferramenta, onde se concentra o risco de exposição de dados sensíveis. São os chat
  exports do processo real;
- `../solution/.claude/decisions/`: 17 ADRs e o índice `_adr-index.md`, registrando as escolhas
  consequentes (metodologia do scoring, escopo, stack, empacotamento, política de transcrição);
- `../solution/.claude/backlog/`: as tarefas atômicas do projeto, com identificador, prioridade,
  status e dependências;
- `../solution/.claude/rules/`: os padrões internos de Common Lisp, Bash, SQL e do sistema de
  design que governaram a construção;
- `../solution/.claude/assets/examples/`: capturas de tela da aplicação e artefatos de
  demonstração do sistema de design.


## Roteiro de leitura sugerido

1. `../solution/.claude/worklog/_historical.md`, para a visão geral cronológica do projeto;
2. `../solution/docs/analise-exploratoria.md` e `../solution/docs/metodologia-scoring.md`, para
   o achado que redirecionou a modelagem e a formalização do indicador;
3. `../solution/.claude/decisions/_adr-index.md`, para as decisões consequentes em ordem;
4. Uma transcrição de sessão à escolha em `../solution/.claude/sessions/`, para ver o processo
   de raciocínio humano-agente em detalhe;
5. A seção "Relatório de auditoria" ao final de um worklog, para ver a auditoria independente em
   ação.


## Nota sobre completude

Das 27 sessões de trabalho, 19 possuem a transcrição JSONL correspondente. As 8 restantes não a
possuem: a forma bruta da transcrição não é retida por política de segurança, de modo que essas
transcrições provavelmente não são recuperáveis. Os worklogs e os ADRs cobrem integralmente
todas as sessões, incluindo as 8 sem transcrição.


## Nota sobre segredos

As transcrições versionadas são higienizadas e submetidas a uma varredura de segredos
fail-closed antes de qualquer publicação, conforme a política registrada nos ADRs J7K4 e P8V4
do projeto.
Nenhuma chave, senha ou token é versionada em código, documentação, log ou transcrição.
