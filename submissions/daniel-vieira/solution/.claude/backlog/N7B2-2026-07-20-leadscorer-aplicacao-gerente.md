---
id: N7B2
parent: 8W2N
project: LeadScorer
subject: Aplicacao do gerente (Fase 6 de 8W2N)
author: dcvr@
priority: medium
status: done
created: 2026-07-20
updated: 2026-07-20
---


# Descrição (o que será feito)

Construir a aplicacao web do gerente de vendas, a segunda das duas aplicacoes de negocio da
tarefa-pai 8W2N (Fase 6), segregada da aplicacao do agente e sem gestao de papeis. A aplicacao
apresenta, na tela inicial, a faixa de cartoes de indicadores agregada para o time do gerente e
a lista de destaque das oportunidades engajadas em curso pelo time; e, em visao propria de
acompanhamento, a lista completa dos ciclos de engajamento do time, com filtros por agente,
produto, conta, desfecho e data de engajamento, e ordenacao por parametro escalar, temporal ou
alfabetico. A aplicacao e somente leitura: o gerente observa o trabalho do time, sem operar o
ciclo de engajamento.


# Motivações (por que será feito)

- E a segunda aplicacao de negocio da interface web (terceiro objetivo especifico do projeto) e
  fecha o ciclo de valor: o gerente acompanha o trabalho que os agentes produzem na Fase 5
  (P3W7). Com a Fase 5 concluida, esta e a proxima etapa do caminho critico para a entrega
  (a tarefa-pai 8W2N bloqueia a submissao 6X9H);
- O desafio oferece bonus explicito pela filtragem por individuo, gerente ou regiao, que a visao
  de acompanhamento do time realiza.


# Recursos e dados necessários

- Concepcao 'docs/concepcao-inicial.md' (secoes "Tela inicial", "Descricao de usuarios",
  estorias "Tela inicial: painel de indicadores" e "Gerente de vendas: acompanhamento do time",
  "Modelo relacional");
- Prototipos estaticos canonicos '.claude/assets/examples/example-home-gerente-dark.html' e
  'example-acompanhamento-gerente-dark.html' (V7C2);
- Camada web existente da Fase 5 'src/web/' (queries, handlers, render, view, server), a ser
  estendida espelhando o padrao do agente; auxiliares de dominio de 'src/scoring.lisp',
  'src/cycle.lisp' e 'src/engagement.lisp';
- Persistencia: tabelas 'engagements', 'opportunity_scores', 'opportunities', 'sales_agents'
  (chave 'sales_manager_id') e 'sales_managers' (db/migrations/0001-0002);
- Design system '.claude/rules/design.md' e '.claude/assets/tokens/'; CSS de aplicacao
  'src/web/static/app.css'.


# Plano de trabalho (como será feito)

A ser detalhado no planejamento da sessao. Em linhas gerais, espelhando a Fase 5:

1. Consultas de leitura do time (KPIs agregados do time; engajadas em curso do time; ciclos do
   time para o acompanhamento), escopadas por 'sales_manager_id' e com o agente vinculado como
   parametro;
2. Auxiliares puros de apresentacao (badge de desfecho, filtros e ordenacao do acompanhamento);
3. Renderizacao das duas telas do gerente (tela inicial com KPI e destaque; acompanhamento com
   barra de filtros e tabela), CSP-limpa;
4. Handlers e rotas (ramo do gerente em 'home-response-for'; rota de acompanhamento; registro
   das rotas apenas na aplicacao do gerente), interatividade hibrida como no agente;
5. Porte do CSS das telas do gerente (badges de desfecho, colunas do acompanhamento);
6. Verificacao completa e conducao ponta a ponta pela pilha HTTP real.


# Riscos e ressalvas

- Estado de ciclo devolvido: uma devolucao sem desfecho ('closed_at' preenchido, 'outcome'
  nulo, 'expired' falso) e um quinto estado de ciclo que os prototipos do gerente nao rotulam
  (contemplam Em curso, Won, Lost, Expirado). O acompanhamento deve rotula-lo de forma explicita
  ou justificar a sua exclusao;
- A aplicacao do gerente e somente leitura; nenhuma rota de mutacao do ciclo deve ser exposta a
  ela, preservando a segregacao deny-by-default ja estabelecida;
- Os prototipos sao nao normativos: os dados exibidos (contagens, valores) sao ilustrativos e
  nao devem ser reproduzidos como fixos.


# Dependências

- blocked-by: P3W7


# Definição de pronto

- A tela inicial do gerente apresenta a faixa dos seis cartoes de indicadores agregada para o
  time e a lista de destaque das oportunidades engajadas em curso pelo time, conforme a
  concepcao;
- A visao de acompanhamento apresenta a lista completa dos ciclos do time com os filtros (agente,
  produto, conta, desfecho, data de engajamento) e a ordenacao especificados, com o estado de
  cada ciclo rotulado, incluindo o ciclo devolvido;
- A aplicacao do gerente permanece segregada e somente leitura, sem rotas de mutacao do ciclo, em
  conformidade com o design system e responsiva no iPhone 13;
- A verificacao de software aplicavel passa (compilacao sem avisos, testes Parachute, linter
  mallet, e as verificacoes de HTML, CSS e YAML pertinentes).
