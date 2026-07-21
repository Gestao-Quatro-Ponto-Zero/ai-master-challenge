---
id: S9K5
project: LeadScorer
subject: Semantica de decaimento por desfecho no ciclo de engajamento interativo
author: dcvr@
status: accepted
created: 2026-07-20
updated: 2026-07-20
---


# Contexto (por que a decisao e necessaria)

O ciclo de engajamento interativo da aplicacao do agente (tarefa P3W7) permite tres desfechos
para uma oportunidade engajada: venda fechada (won), venda perdida (lost) e devolucao sem
desfecho. Ao encerrar o ciclo, a oportunidade retorna a lista publica de disponiveis, e o seu
ranqueamento deve refletir o que acabou de ocorrer.

A concepcao original ('docs/concepcao-inicial.md') afirmava, para os tres casos, que a
oportunidade "retorne a lista publica de disponiveis com o seu potencial decaido". Ao exercitar
o comportamento, verificou-se que tratar a devolucao como as vendas produz um resultado indesejado:
uma oportunidade que o agente engaja e devolve de imediato, por engano ou reavaliacao, cairia ao
fim da lista, embora nada tenha ocorrido com o cliente. O usuario, ao testar, esclareceu a
intencao: won e lost devem rebaixar a oportunidade (transacao recente), enquanto uma devolucao
rapida deve preserva-la proxima ao topo, decaindo apenas pelo envelhecimento acumulado durante o
engajamento.

O motor de scoring (R7M4) modela o decaimento pos-fechamento pela corcova de maturidade do
momentum, indexada pelos dias virtuais desde o ultimo fechamento do par. A deteccao desse
"fechamento vivo" no ranqueamento nao distinguia, ate aqui, um fechamento com desfecho de uma
devolucao sem desfecho.


# Decisao (o que foi decidido)

- Um desfecho won ou lost e uma TRANSACAO recente: grava um fechamento em tempo virtual com
  desfecho, e o ranqueamento o detecta como fechamento vivo, reduzindo o momentum ao minimo pela
  corcova de maturidade (recuperando em direcao a cadencia de recompra). O rebaixamento e imediato
  no caminho interativo, por um reescore alvejado da oportunidade ('rescore-opportunity'), sem
  esperar o proximo tick do agendador;
- Uma devolucao sem desfecho NAO e uma transacao: fecha o ciclo (preservando a invariante de que
  uma 'prospecting' nao tem ciclo aberto), mas o ranqueamento ignora fechamentos sem desfecho, de
  modo que a oportunidade reverte ao seu ranqueamento de linha de base. A deteccao de fechamento
  vivo passa a exigir 'outcome IS NOT NULL';
- Won e lost decaem de forma identica; a distincao entre eles reside no historico e no registro
  economico, nao na curva de decaimento;
- A expiracao automatica de uma engajada nao concluida grava o desfecho lost e, portanto, decai:
  uma engajada que estoura o corte de vinte minutos e tratada como uma perda de fato, nao como uma
  devolucao.


# Alternativas consideradas (o que mais foi ponderado)

- Manter a semantica literal da concepcao, com a devolucao decaindo como um desfecho: rejeitada
  por contrariar a intencao de uso, dado que a devolucao nao e um evento economico e uma devolucao
  imediata nao deveria penalizar a oportunidade;
- Preservar na devolucao o envelhecimento acumulado enquanto a oportunidade esteve engajada:
  diferida por escolha de MVP; exigiria que a linha de base considerasse a duracao do engajamento,
  o que o retrato estatico do modelo nao suporta hoje. A devolucao reverte integralmente a linha
  de base, e a limitacao esta registrada nas ressalvas de 'docs/metodologia-scoring.md';
- Decaimento assimetrico entre won e lost, por exemplo um resfriamento distinto apos uma recusa:
  diferido por escolha de MVP; nao ha na base evidencia para calibrar a assimetria.


# Consequencias (o que resulta da decisao)

- A implementacao restringe a deteccao de fechamento vivo a 'outcome IS NOT NULL' em
  'rank-prospecting-opportunities' e em 'rescore-opportunity' ('src/cycle.lisp'); a devolucao
  ('return-engagement') fecha o ciclo sem desfecho e reverte a linha de base;
- O caminho interativo reescreve as pontuacoes da oportunidade de imediato, eliminando a defasagem
  de ate um tick (~60 s) entre a acao do agente e o rebaixamento visivel;
- A concepcao ('docs/concepcao-inicial.md') e o criterio de pronto da P3W7 sao ajustados para
  refletir a distincao entre desfecho e devolucao; a metodologia ('docs/metodologia-scoring.md',
  secao Ressalvas) registra as duas limitacoes diferidas;
- A assimetria entre a devolucao (nao decai) e a expiracao (decai como lost) e deliberada e fica
  documentada, de modo que um leitor futuro nao a tome por inconsistencia.


# Relações

- supersedes:
- superseded-by:
- related-tasks: P3W7, R7M4
