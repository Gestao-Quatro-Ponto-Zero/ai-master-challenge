;;;; scheduler.lisp --- Testes do agendador de fundo dos servicos de ciclo.

(in-package #:leadscorer/web/tests)

(defparameter *derived-present-p*
  (probe-file (asdf:system-relative-pathname
               :leadscorer "data/derived/potentials_base.csv"))
  "Verdadeiro quando os CSV derivados do modelo estao provisionados.")

(define-test scheduler-starts-and-stops
  (if (and (leadscorer::database-reachable-p) *derived-present-p*)
      (progn
        ;; Esvazia as tabelas do ciclo para que o tick imediato seja um no-op
        ;; rapido e deterministico: este teste verifica a mecanica de start/stop,
        ;; nao os resultados do tick (exercitados na integracao do dominio).
        (leadscorer:with-database
          (postmodern:execute
           "TRUNCATE opportunity_scores, engagements, opportunities
            RESTART IDENTITY"))
        (leadscorer/web:stop-scheduler)
        (true (leadscorer/web:start-scheduler))
        (true (leadscorer/web:scheduler-running-p))
        (leadscorer/web:stop-scheduler)
        (false (leadscorer/web:scheduler-running-p)))
      (skip "PostgreSQL ou CSV derivados indisponiveis; agendador ignorado.")))
