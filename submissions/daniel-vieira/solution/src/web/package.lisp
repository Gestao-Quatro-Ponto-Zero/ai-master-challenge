;;;; package.lisp --- Definição do pacote da camada web do LeadScorer.

(defpackage #:leadscorer/web
  (:use #:cl)
  (:local-nicknames (#:ls #:leadscorer))
  (:documentation
   "Camada web do LeadScorer: as duas aplicações segregadas, do agente e do
gerente, servidas server-side com Clack, Ningle e Spinneret. Reúne a
identificação por seleção, a sessão e o layout base do design system.")
  (:export #:start
           #:stop
           #:start-scheduler
           #:stop-scheduler
           #:scheduler-running-p
           #:make-agent-app
           #:make-manager-app
           #:*agent-app*
           #:*manager-app*))
