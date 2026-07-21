---
id: R7M4
parent: 8W2N
project: LeadScorer
subject: Servicos de ciclo de engajamento (Fase 4 de 8W2N)
author: dcvr@
priority: medium
status: done
created: 2026-07-20
updated: 2026-07-20
---


# Descrição (o que será feito)

Implementar os servicos automaticos do ciclo de engajamento especificados na concepcao
('docs/concepcao-inicial.md'), a saber, o ranqueamento personalizado por agente, o decaimento
e a expiracao, operando sobre a persistencia (9P4D) a partir do motor de scoring existente
('src/scoring.lisp', 'src/model.lisp'). O ranqueamento recomputa e persiste, por par de
oportunidade disponivel e agente, a pontuacao geral e as dimensoes em 'opportunity_scores'; o
decaimento reduz o potencial das oportunidades engajadas em funcao da idade desde o engajamento;
e a expiracao encerra, no corte de vinte minutos, os ciclos vencidos, registrando o desfecho
'lost' e devolvendo a oportunidade ao rol das disponiveis com potencial decaido. Adota-se o
ciclo de computacao acelerado da concepcao (ranqueamento e decaimento a cada minuto, expiracao
em vinte minutos). Esta fase introduz tambem a externalizacao dos parametros de modelo e das
regras de negocio em um arquivo de configuracao em forma Lisp (s-expression), lido pelo leitor
nativo com '*read-eval*' em falso, diferida da tarefa K9X4 por nao ser consumida pela fundacao.
A forma Lisp substitui o YAML antes previsto, dispensando a introducao de uma dependencia de
leitura de YAML.


# Motivações (por que será feito)

E a Fase 4 do plano da tarefa-pai 8W2N. Os servicos de ciclo produzem os 'opportunity_scores' e
mantem o estado das oportunidades, que sao o insumo direto das telas das aplicacoes do agente
(Fase 5) e do gerente (Fase 6). Sem eles, as listas de oportunidades nao teriam pontuacoes a
exibir nem o ciclo de vida a operar. A fundacao executavel e a sessao ja estao prontas (K9X4)
e a persistencia esta disponivel (9P4D), de modo que esta fase e a precondicao remanescente das
aplicacoes de negocio.


# Recursos e dados necessários

- Motor de scoring: 'src/scoring.lisp' e 'src/model.lisp' (dimensoes, momentum, composto, listas);
- Persistencia (9P4D): tabelas 'opportunities', 'opportunity_scores' e 'engagements', schema em
  'db/migrations/' e acesso em 'src/db.lisp';
- Concepcao: 'docs/concepcao-inicial.md' (ciclo de computacao, estados, decaimento e expiracao)
  e ADR C4X9 (metodologia de scoring);
- Fundacao web: sistema 'leadscorer/web' (K9X4), que hospedara os servicos ou os invocara;
- Parametros de modelo e regras de negocio a externalizar em um arquivo de configuracao em forma
  Lisp (s-expression), lido pelo leitor nativo com '*read-eval*' em falso, sem nova dependencia.


# Plano de trabalho (como será feito)

O plano detalhado sera desenvolvido no modo de planejamento da sessao dedicada. Em linhas gerais:
o servico de ranqueamento persistindo 'opportunity_scores' por par disponivel e agente; o servico
de decaimento e expiracao sobre as engajadas; o agendamento no ciclo acelerado; e a externalizacao
dos parametros de modelo em um arquivo de configuracao em forma Lisp (s-expression).


# Dependências

- blocks:
- blocked-by:


# Definição de pronto

- O ranqueamento recomputa e persiste, por par de oportunidade disponivel e agente, a pontuacao
  geral e as dimensoes em 'opportunity_scores', a partir do motor de 'src/scoring.lisp';
- O decaimento reduz o potencial das oportunidades engajadas conforme a idade desde o
  engajamento;
- A expiracao encerra os ciclos no corte de vinte minutos, registra o desfecho 'lost' e devolve
  a oportunidade ao rol das disponiveis com potencial decaido;
- Os servicos executam no ciclo acelerado da concepcao (ranqueamento e decaimento a cada minuto,
  expiracao em vinte minutos);
- Os parametros de modelo e as regras de negocio residem em um arquivo de configuracao em forma
  Lisp (s-expression), lido pela aplicacao com '*read-eval*' em falso;
- A verificacao de software aplicavel passa (compilacao e carga sem avisos, testes Parachute,
  linter mallet e as verificacoes de configuracao pertinentes).
