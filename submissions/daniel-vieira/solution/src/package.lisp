;;;; package.lisp --- Definição do pacote do sistema LeadScorer.

(defpackage #:leadscorer
  (:use #:cl)
  (:documentation "Pacote principal do sistema LeadScorer.")
  (:export #:read-csv-file
           #:csv-rows->alists
           #:write-csv-file
           #:empty-csv-file
           #:empty-csv-file-path
           #:load-model
           #:model-agents
           #:model-pair-context-index
           #:score-potentials-for-agent
           #:score-initiated-for-agent
           #:emit-scored-lists
           #:run-validation
           #:aggregation-comparison
           #:*weight-momentum*
           #:*weight-economic*
           #:*weight-affinity*
           #:*weight-adherence*
           #:with-database
           #:now-unix-ms
           #:+ms-per-day+
           #:+unix-epoch-universal-time+
           #:*seed-currency*
           #:content-checksum
           #:run-migrations
           #:seed-database
           #:database-seeded-p
           #:verify-persistence
           #:load-config
           #:ranking-interval-ms
           #:run-cycle-tick
           #:rescore-opportunity
           #:current-virtual-now
           #:real-minutes-to-expiration
           #:engagement-expired-p
           #:real-instant-of-virtual
           #:*virtual-t0*
           #:*max-engagements*
           #:*top-tier-size*
           #:*potential-cutoff*
           #:engage-opportunity
           #:close-engagement
           #:return-engagement
           #:engagement-error
           #:engagement-limit-reached
           #:opportunity-not-available
           #:engagement-error-agent-id
           #:engagement-error-limit
           #:engagement-error-opportunity-id
           #:scored-agent
           #:scored-account
           #:scored-product
           #:scored-economic
           #:scored-affinity
           #:scored-adherence
           #:scored-momentum
           #:scored-composite))
