---
id: X7F2
parent:
project: leadscorer
subject: Propagar a renomeacao da dimensao para Especializacao ao codigo, schema, testes e telas
author: dcvr@
priority: high
status: done
created: 2026-07-20
updated: 2026-07-20
---


# Descrição (o que será feito)

REESCOPO (2026-07-20, decisao do usuario): a Parte 2 e cosmetica, limitada ao nivel de exibicao e
de documentacao. Propaga o nome de exibicao "Especializacao" / "Especializacao do agente" as
superficies visiveis ao usuario -- a aplicacao ('src/web/view.lisp'), os exemplos HTML estaticos e
as notas de ajuda -- corrigindo o rotulo defasado, que ainda exibia "Persuasao" (o nome anterior a
S5J4). Os nomes internos de codigo ('adherence' e simbolos correlatos), a coluna de banco
'score_adherence' e o artefato derivado 'adherence.csv' sao mantidos, em definitivo, como nome
interno herdado; nao ha renomeacao de simbolos, de schema, de fixtures nem regeneracao de
derivados. Inclui a correcao do achado 3 (docstrings dos pesos defasadas frente a agregacao
geometrica), por ser documentacao interna sem mudanca de comportamento. O ADR G5W2 e emendado para
registrar a separacao exibicao-vs-interno como permanente.

O escopo amplo original (renomeacao de simbolos Lisp, schema, artefato, fixtures e testes) foi
descartado; permanece registrado abaixo apenas para historico.


# Motivações (por que será feito)

O ADR G5W2 fixou o nome canonico da dimensao do agente como "Especializacao" (curto) e
"Especializacao do agente" (longo). A Parte 1 (S5J4) reconciliou a documentacao, mas os simbolos
de codigo, o schema e as interfaces usam "adherence", o que mantem uma divergencia doc-codigo
temporaria e deliberada. A propagacao foi diferida porque outro agente constroi em paralelo as
telas de producao do app do agente, e renomear simbolos e rotulos concorrentemente causaria
conflito e confusao. Com o trabalho concorrente concluido, a renomeacao pode ser propagada sem
risco.


# Recursos e dados necessários

- O ADR G5W2 (nome e mecanica canonicos da dimensao) e a tarefa S5J4 (reconciliacao documental);
- O codigo em 'src/scoring.lisp', 'src/model.lisp', 'src/config.lisp', 'src/cycle.lisp',
  'src/package.lisp', 'src/validation.lisp' e a configuracao 'config/model.lisp';
- O schema em 'db/migrations/' (coluna 'score_adherence') e o emissor 'scripts/modeling.sql'
  (artefato 'adherence.csv', colunas 'won_product'/'won_series');
- Os testes em 'tests/scoring.lisp' e 'tests/cycle.lisp' e as fixtures em
  'tests/fixtures/derived/';
- Os exemplos HTML em '.claude/assets/examples/example-{disponiveis,engajadas,home-agente}
  -dark.html' e o texto de ajuda em '.claude/assets/examples/textos-de-ajuda.md';
- O inventario de ocorrencias de "adherence" em codigo levantado na sessao S5J4-2026-07-20-1.


# Plano de trabalho (como será feito)

1. Renomear os simbolos de backend 'adherence' para 'especializacao' em 'src/scoring.lisp'
   ('*weight-adherence*', 'cell-adherence', 'adherence-value', 'scored-adherence',
   'model-adherence-values'), 'src/model.lisp' ('load-adherence'), 'src/config.lisp',
   'src/cycle.lisp', 'src/package.lisp' e 'src/validation.lisp', e as chaves de config
   ('*weight-adherence*', '*adherence-series-discount*');
2. Corrigir o achado 3: atualizar as docstrings dos pesos e de 'multiplicative-composite' em
   'src/scoring.lisp' para descrever expoentes da agregacao geometrica, em vez de "razoes
   de troca da base aditiva";
3. Renomear o artefato 'adherence.csv' para 'especializacao.csv' e as colunas emitidas em
   'scripts/modeling.sql', e ajustar as fixtures em 'tests/fixtures/derived/' e os testes em
   'tests/scoring.lisp' e 'tests/cycle.lisp';
4. Manter a coluna fisica 'score_adherence' no schema como nome herdado, sem migracao de banco.
   A camada de aplicacao mapeia o nome logico 'especializacao' para essa coluna: o INSERT/upsert
   em 'src/cycle.lisp' continua referenciando a coluna 'score_adherence', e o slot/accessor Lisp
   passa a 'especializacao'. Aceita-se a pequena divergencia entre o nome fisico e o logico;
5. Renomear os rotulos de tela nos 3 exemplos HTML e no texto de ajuda, e nas telas de producao
   reais quando expuserem a coluna, para "Especializacao"/"Especializacao do agente";
6. Verificacao completa: compilacao sem avisos, suite Parachute verde, linter mallet sem achados,
   e regeneracao dos derivados afetados.


# Riscos e ressalvas

- Por decisao de projeto, a coluna fisica 'score_adherence' e mantida como nome herdado, evitando
  a migracao de banco; renomeia-se apenas a camada de aplicacao e as telas. O custo aceito e a
  divergencia entre o nome fisico da coluna e o nome logico 'especializacao', a documentar no
  ponto do mapeamento;
- A renomeacao concorrente com o desenvolvimento das telas de producao e a razao do bloqueio; a
  tarefa so deve iniciar apos a conclusao do trabalho do outro agente (P3W7);
- A mudanca e ampla e mecanica; o risco principal e a omissao de uma ocorrencia, mitigado pelo
  inventario e por uma varredura final de residuos de "adherence".


# Dependências

- blocks:
- blocked-by: P3W7


# Definição de pronto

- Nenhuma superficie visivel ao usuario -- a aplicacao ('src/web/view.lisp'), os exemplos HTML e as
  notas de ajuda ('textos-de-ajuda.md') -- exibe "Persuasao"/"aderencia" para a dimensao do agente;
  o nome de exibicao "Especializacao" / "Especializacao do agente" esta aplicado;
- Os nomes internos ('adherence', 'score_adherence', 'adherence.csv') sao preservados, por decisao;
  nao ha renomeacao de simbolos, migracao de schema, alteracao de fixtures nem regeneracao de
  derivados;
- O achado 3 esta corrigido: as docstrings dos pesos e o cabeçalho de 'src/scoring.lisp' refletem a
  agregacao geometrica corrente (expoentes), e a forma legada esta marcada como tal;
- Qualquer teste que assertava o rotulo antigo esta alinhado ao novo nome de exibicao;
- O ADR G5W2 esta emendado, registrando o nome interno 'adherence' como permanente e a separacao
  exibicao-vs-interno como deliberada;
- A verificacao obrigatoria passa: compilacao sem avisos proprios, Parachute verde (descontada a
  falha ambiental pre-existente por ausencia de 'PGDATABASE') e mallet sem achados;
- Uma varredura final nao encontra residuo de "Persuasao"/"aderencia" designando a dimensao nas
  superficies visiveis, preservados os falsos positivos de design/stack e as referencias historicas
  em 'docs/revisao-dimensoes-scoring.md'.
