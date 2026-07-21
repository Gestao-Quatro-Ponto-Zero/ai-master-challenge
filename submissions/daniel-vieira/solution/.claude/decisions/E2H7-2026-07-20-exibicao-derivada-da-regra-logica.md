---
id: E2H7
project: LeadScorer
subject: Exibicao do estado de engajamento derivada da regra logica; agendador como escritor unico
author: dcvr@
status: accepted
created: 2026-07-20
updated: 2026-07-20
---


# Contexto (por que a decisao e necessaria)

O ciclo de engajamento opera sob um relogio virtual acelerado: uma oportunidade engajada
expira ao alcancar o horizonte de decaimento (vinte minutos reais percorrem o horizonte). A
transicao de estado --- fechar o ciclo aberto, registrar o desfecho 'lost' com a marca de
expiracao e devolver a oportunidade a 'prospecting' com o potencial decaido --- e realizada
exclusivamente pelo agendador, que roda a cada minuto (ver 'expire-due-opportunities' em
'src/cycle.lisp' e o ADR S9K5).

Disso resulta um descompasso entre duas nocoes de "expirada":

- Logica: a idade virtual alcancou o horizonte ('cycle-expired-p' sobre 'virtual-age-days'),
  verdadeira no instante exato em que o horizonte e cruzado;
- Persistida: 'opportunities.status = engaging' com ciclo aberto, transicionada apenas quando
  o agendador roda.

A persistida atrasa a logica em ate um intervalo do agendador (~60s). Nessa janela, uma
oportunidade ja logicamente expirada permanece listada como engajada, exibindo um countdown
que chega a "00 min". Um usuario observou o sintoma na lista de destaque do gerente. Um piso
cosmetico no rotulo (exibir "01 min" em vez de "00 min") foi tentado e rejeitado por mascarar
o problema em vez de corrigi-lo: continuava apresentando como ativa uma oportunidade ja
expirada.


# Decisao (o que foi decidido)

O estado de engajamento exibido e uma funcao pura da regra logica, nao da cadencia do
agendador. A regra logica reside em um unico predicado de dominio, 'engagement-expired-p'
(src/cycle.lisp, exportado), que e a mesma regra que 'expire-due-opportunities' aplica na
escrita. A camada de leitura marca ':expiring-p' no ciclo aberto ja alem do horizonte e o
exibe como um estado derivado "Expirando", distinto do "Em curso": na lista de engajadas do
agente com os controles de desfecho desabilitados, e no destaque e no acompanhamento do
gerente com o badge proprio, excluido da contagem "em curso".

O agendador permanece o escritor unico de toda transicao de estado do ciclo. Nenhuma leitura
dispara escrita.


# Alternativas consideradas (o que mais foi ponderado)

- Piso cosmetico no rotulo (exibir no minimo "01 min"): rejeitada por tratar o sintoma e nao a
  causa; a oportunidade logicamente expirada continuava apresentada como ativa, com countdown.
- Apertar a cadencia do agendador para encurtar a janela: rejeitada por ser paliativa (a janela
  nunca e eliminada) e por nao atacar o principio de que a exibicao nao deve depender da
  cadencia da escrita.
- Expiracao na leitura (uma leitura que encontra um ciclo expirado dispara o seu fechamento):
  rejeitada por violar o escritor unico e o carater somente-leitura da aplicacao do gerente, e
  por introduzir concorrencia entre a leitura e o agendador sobre o mesmo ciclo aberto.


# Consequencias (o que resulta da decisao)

- A exibicao torna-se consistente e independente da cadencia do agendador; o sintoma "00 min em
  uma engajada ainda listada" desaparece.
- Os controles de desfecho de uma engajada expirando ficam desabilitados no app do agente,
  eliminando a corrida agente-vs-agendador (marcar 'won' em algo que sera fechado como 'lost').
- A regra de expiracao passa a ter uma fonte unica ('engagement-expired-p'), compartilhada pela
  leitura e reutilizada pela mesma logica da escrita, reduzindo o risco de divergencia.
- Surge uma janela de limbo de ate ~60s em que a oportunidade nao aparece como ativa (correto)
  nem ainda no historico/KPIs (o ciclo nao fechou). E aceitavel e autocorrige no proximo tique;
  a alternativa (exibi-la como ativa) e pior.
- ':expiring' e um estado derivado de exibicao, fora de '+cycle-states+' (os estados
  persistidos filtraveis), de modo que nao e um criterio de filtro do acompanhamento.


# Relacoes

- supersedes:
- superseded-by:
- related-tasks: N7B2, 8W2N
