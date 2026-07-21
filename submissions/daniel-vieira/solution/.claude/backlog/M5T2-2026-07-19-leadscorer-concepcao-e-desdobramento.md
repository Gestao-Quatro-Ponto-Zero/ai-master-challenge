---
id: M5T2
parent:
project: LeadScorer
subject: Revisão e completude da concepção inicial e desdobramento das tarefas de aplicação
author: dcvr@
priority: high
status: done
created: 2026-07-19
updated: 2026-07-19
---


# Descrição (o que será feito)

Revisar e completar o documento 'docs/concepcao-inicial.md', que consolida a concepção da
aplicação web LeadScorer. A revisão abrange a linguagem e a gramática, a consistência e a
completude, a reconciliação com as fontes canônicas (a metodologia de scoring, o esquema real
dos CSV e o código de scoring), a remodelagem do modelo de dados centrada no controle do ciclo
de engajamento, o complemento das estórias de usuário e o ajuste das demais seções. Ao final,
desdobrar os passos de implementação para as tarefas de persistência (9P4D) e de aplicação
(8W2N), atualizando os respectivos arquivos de backlog.


# Motivações (por que será feito)

A concepção inicial é a base para a fase de aplicação, da qual dependem 9P4D e 8W2N, e apresenta
problemas materiais que, se não corrigidos, propagariam premissa errada para a implementação: a
apresentação das dimensões diverge do código canônico (o documento sugere seis dimensões ativas,
enquanto o scoring tem quatro ativas e duas inertes por peso zero), a agregação real (portão
mais média geométrica ponderada, ADR C4X9) não está refletida, o modelo relacional diverge do
esquema real dos CSV e viola 'std-sql.md', as estórias de usuário estão incompletas e o
documento afirma incorretamente que os wireframes já existem. Consolidar a concepção antes de
desdobrar 9P4D e 8W2N é o desdobramento interdependente correto, pois ambas derivam seus passos
desta especificação.


# Recursos e dados necessários

- 'docs/concepcao-inicial.md': documento objeto da revisão;
- Fontes canônicas de reconciliação: 'docs/metodologia-scoring.md', 'src/scoring.lisp',
  'src/model.lisp', 'docs/analise-exploratoria.md', 'docs/validacao-scoring.md';
- Esquema real dos dados: 'data/normalized/*.csv' (accounts, products, sales_teams,
  sales_pipeline) e 'data/normalized/metadata.csv';
- Padrões internos: '.claude/rules/std-sql.md' (modelo de dados), '.claude/rules/design.md' e
  tokens (UI/UX);
- ADRs pertinentes: B7Q3 (escopo distribuição), C4X9 (agregação), D2K9 (stack e persistência
  faseada), D4M3 (empacotamento);
- Decisões do usuário desta sessão: dimensões (4 ativas + 2 inertes com traço), modelo derivado
  do real com revisão prévia, login por seleção sem senha, reentrada pós-desfecho com potencial
  decaído.


# Plano de trabalho (como será feito)

1. Revisão de linguagem e gramática de todo o documento, preservando o conteúdo conceitual;
2. Reconciliação do modelo de qualificação com a fonte canônica: quatro dimensões ativas com
   pesos e duas inertes exibidas com traço, agregação por portão e média geométrica ponderada;
3. Remodelagem do modelo de dados derivada do esquema real dos CSV, conforme 'std-sql.md',
   centrada no ciclo de engajamento, apresentada ao usuário para revisão antes de fixar;
4. Complemento e detalhamento das estórias de usuário faltantes (login, tooltip de dimensões,
   limite de engajamentos, top-tier, expiração automática, visão do gerente, filtro de corte);
5. Ajuste das demais seções (ciclo de computação, UI/UX com correção da afirmação sobre
   wireframes, arquitetura, limitações de escopo);
6. Desdobramento dos passos de implementação para 9P4D e 8W2N, com atualização dos arquivos de
   backlog e das relações de dependência.


# Riscos e ressalvas

- A remodelagem do modelo de dados afeta diretamente 9P4D; uma reconciliação incompleta com o
  dado real propagaria erro para a persistência. Mitigação: checkpoint de aprovação do modelo
  antes de fixar;
- O documento é conceitual e não executável; a maior parte da sessão é documental e isenta de
  auditoria independente, exceto se produzir configuração executável (por exemplo, esboço de
  schema SQL ou YAML de parâmetros);
- O ciclo de computação proposto (serviços a cada minuto, expiração em 20 min) tem implicações
  de escala e de arquitetura que devem ser declaradas, ainda que aceitáveis para o MVP.


# Dependências

- blocks: 9P4D, 8W2N
- blocked-by:


# Definição de pronto

- O documento 'docs/concepcao-inicial.md' está revisado quanto à linguagem, à consistência e à
  completude, sem afirmações factualmente incorretas;
- A apresentação do modelo de qualificação é consistente com 'src/scoring.lisp' e
  'docs/metodologia-scoring.md' (quatro dimensões ativas, duas inertes, agregação correta);
- O modelo de dados deriva do esquema real dos CSV, adere a 'std-sql.md' e sustenta o ciclo de
  engajamento, tendo sido aprovado pelo usuário;
- As estórias de usuário cobrem os fluxos do agente e do gerente identificados, com detalhe
  suficiente para orientar os wireframes e a implementação;
- Os arquivos de backlog de 9P4D e 8W2N foram atualizados com os passos desdobrados e as
  relações de dependência ajustadas.
