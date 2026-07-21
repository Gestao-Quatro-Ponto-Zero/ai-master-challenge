;;;; model.lisp --- Configuracao canonica dos parametros de modelo e regras.
;;;;
;;;; Fonte canonica dos pesos, da forma de agregacao e das regras de negocio do
;;;; ciclo de engajamento. Lido pela aplicacao como DADO, nao como codigo: o
;;;; leitor e invocado com '*read-eval*' vinculado a NIL e '*package*' ao pacote
;;;; KEYWORD, de modo que nenhuma forma seja avaliada nem simbolo interne em
;;;; pacote de producao (ver 'read-config-form' em 'src/config.lisp'). Quando uma
;;;; chave falta, o default compilado em 'src/config.lisp' e 'src/scoring.lisp'
;;;; prevalece. Uma chave desconhecida e recusada (fail-closed contra erro de
;;;; digitacao).

;;; Parametros do modelo de scoring (revinculam os defparameters de scoring.lisp).
(:weight-economic 0.40
 :weight-affinity 0.35
 :weight-adherence 0.25
 :weight-momentum 0.5
 :composite-form :geometric
 :normalization :percentile
 :dimension-floor 1.0
 :maturity-churn-multiple 6.0
 :maturity-neutral 0.5
 :adherence-series-discount 0.5

 ;; Regras de negocio do ciclo de engajamento.
 :max-engagements 10
 :top-tier-size 10
 ;; Filtro de corte do modelo: oportunidades com potencial abaixo deste limiar
 ;; sao rebaixadas ao final da lista de disponiveis. Um valor 0 desativa o corte.
 :potential-cutoff 40
 :expiration-minutes 20
 :ranking-interval-seconds 60
 :decay-interval-seconds 60
 ;; Ancora do relogio virtual: 2017-12-31T00:00:00Z UTC, o asof da modelagem
 ;; (MAX(close_date) do dataset). O horizonte de decaimento (dias virtuais) e
 ;; data-driven pelo comprimento do vetor 'decay', nao uma chave de config.
 :virtual-epoch 1514678400000)
