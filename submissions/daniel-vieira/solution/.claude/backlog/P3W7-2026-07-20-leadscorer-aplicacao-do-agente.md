---
id: P3W7
parent: 8W2N
project: LeadScorer
subject: Aplicacao do agente (Fase 5 de 8W2N)
author: dcvr@
priority: medium
status: done
created: 2026-07-20
updated: 2026-07-20
---


# Descrição (o que será feito)

Construir a aplicacao web do agente de vendas sobre a fundacao 'leadscorer/web' existente,
correspondendo a Fase 5 da tarefa-pai 8W2N. Compreende a tela inicial (faixa de cartoes de
indicadores e destaque do top tier), a lista de oportunidades disponiveis (estado 'prospecting')
com filtros, ordenacao, nota explicativa das dimensoes, filtro de corte e destaque do top tier, o
fluxo de engajamento (limite de dez engajadas simultaneas e modal de justificativa para engajar
fora do top tier) e a lista de oportunidades engajadas com os desfechos 'won', 'lost' e devolucao
sem desfecho.


# Motivações (por que será feito)

Subtarefa atomica da tarefa-pai 8W2N, cuja decomposicao em fases foi definida na M5T2 e cujas
fases 1 a 4 (prototipagem, esqueleto, sessao, servicos de ciclo) estao concluidas por V7C2, K9X4
e R7M4. A aplicacao do agente e o ponto de contato do usuario final com a solucao e a primeira
das duas aplicacoes de negocio; ela produz por escrita os registros de engajamento (desfecho,
justificativa, datas) que a aplicacao do gerente (Fase 6) posteriormente le. O contrato de tempo
virtual deixado por R7M4 (engajamento vivo grava 'engaged_at = virtual-now'; limites
'*max-engagements*' e '*top-tier-size*' impostos pelas telas) e o insumo direto desta fase.


# Recursos e dados necessários

- Especificacao funcional: 'docs/concepcao-inicial.md' (estorias do agente, tela inicial, ciclo
  de computacao, modelo relacional);
- Prototipos estaticos (V7C2): '.claude/assets/examples/example-home-agente-dark.html',
  'example-disponiveis-dark.html', 'example-engajadas-dark.html',
  'example-engajar-justificativa-dark.html' e 'textos-de-ajuda.md';
- Fundacao web (K9X4) e servicos de ciclo (R7M4): 'src/web/' (server, handlers, render, queries,
  session, scheduler) e 'src/cycle.lisp';
- Motor de scoring: 'src/scoring.lisp' e 'src/model.lisp'; persistencia (9P4D): 'opportunities',
  'opportunity_scores', 'engagements' em 'db/migrations/', acesso em 'src/db.lisp';
- Configuracao em forma Lisp: 'config/model.lisp' e 'src/config.lisp' ('*max-engagements*',
  '*top-tier-size*', parametros do ciclo);
- Design system: '.claude/rules/design.md' e '.claude/assets/tokens/'.


# Plano de trabalho (como será feito)

A detalhar no modo de planejamento antes da execucao. Em linhas gerais, ciclos TDD no padrao de
funcoes nucleo com sufixo '-for' (testaveis sem servidor nem banco), sobre: (a) camada de consulta
de leitura de oportunidades e engajamentos; (b) tela inicial do agente; (c) lista de disponiveis
com filtros, ordenacao, nota explicativa e corte; (d) escritas de engajamento com limite e
justificativa; (e) lista de engajadas e desfechos.


# Riscos e ressalvas

- O engajamento manual deve gravar 'engaged_at = virtual-now' (contrato de R7M4); a gravacao em
  tempo de parede produziria idade negativa e ausencia de decaimento e expiracao;
- Sob READ COMMITTED, ha janela residual de corrida entre as escritas interativas do agente e o
  tick do agendador, documentada por R7M4; no MVP so o thread do agendador reescreve
  'opportunity_scores', mas o engajamento altera o estado de 'opportunities' e 'engagements';
- O padrao de integracao HTMX com Common Lisp e implementado manualmente por inspecao do
  cabecalho HX-Request (ADR D2K9), sem documentacao oficial;
- Pares que retornam de um ciclo vivo ou engajadas antigas podem nao ter 'pair' no modelo
  estatico; o fallback neutro de R7M4 ja trata a pontuacao, mas as telas devem exibir os
  indicadores de forma consistente.


# Dependências

- blocks:
- blocked-by: R7M4


# Definição de pronto

- A tela inicial do agente apresenta a faixa de cartoes de indicadores e a lista de destaque do
  top tier especificadas na concepcao;
- A lista de disponiveis apresenta o potencial e as quatro dimensoes ativas por oportunidade, o
  destaque do top tier, a nota explicativa por dimensao, os filtros e a ordenacao especificados e
  o filtro de corte;
- O engajamento respeita o limite de dez engajadas simultaneas e exige justificativa para
  oportunidades fora do top tier, gravando 'engaged_at = virtual-now';
- A lista de engajadas permite alterar o desfecho para 'won', 'lost' ou devolver sem desfecho,
  registrando o ciclo no historico quando ha desfecho e devolvendo a oportunidade a lista de
  disponiveis; um desfecho won ou lost a devolve com o potencial decaido pela recencia da
  transacao, ao passo que uma devolucao sem desfecho a reverte ao ranqueamento de linha de base,
  conforme o ADR S9K5;
- A aplicacao e responsiva no iPhone 13 e em conformidade com o design system;
- A verificacao de software aplicavel passa (compilacao sem avisos, testes Parachute, linter
  'mallet', e as verificacoes de HTML e CSS pertinentes).
