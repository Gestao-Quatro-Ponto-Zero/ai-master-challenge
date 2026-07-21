;;;; engagement.lisp --- Testes Parachute dos servicos interativos de engajamento.

(in-package #:leadscorer/tests)

;;; --- Condicoes (puras) ---

(define-test engagement-conditions-carry-data
  (let ((limit (make-condition 'leadscorer:engagement-limit-reached
                               :agent-id 7 :limit 10))
        (unavailable (make-condition 'leadscorer:opportunity-not-available
                                     :opportunity-id 42)))
    (is = 7 (leadscorer:engagement-error-agent-id limit))
    (is = 10 (leadscorer:engagement-error-limit limit))
    (is = 42 (leadscorer:engagement-error-opportunity-id unavailable))
    ;; Ambas sao da familia ENGAGEMENT-ERROR, tratavel em bloco pelo chamador.
    (true (typep limit 'leadscorer:engagement-error))
    (true (typep unavailable 'leadscorer:engagement-error))))

;;; --- Servicos (integracao, gated por banco) ---

(defun open-cycle-of (opportunity-id)
  "A linha '(sales_agent_id engaged_at justification_id)' do ciclo aberto de
OPPORTUNITY-ID, ou NIL quando nao ha ciclo aberto."
  (postmodern:query
   "SELECT sales_agent_id, engaged_at, justification_id
    FROM engagements
    WHERE opportunity_id = $1 AND closed_at IS NULL"
   opportunity-id :row))

(defun integrity-violations ()
  "O total de violacoes das tres invariantes do estado ativo verificadas por
'verify.lisp': 'prospecting' com ciclo aberto, 'engaging' sem ciclo aberto e ciclo
fechado com desfecho sem valor. Assume conexao ativa."
  (postmodern:query
   "SELECT (SELECT COUNT(*) FROM opportunities o
            WHERE o.status = 'prospecting'
              AND EXISTS (SELECT 1 FROM engagements e
                          WHERE e.opportunity_id = o.id AND e.closed_at IS NULL))
         + (SELECT COUNT(*) FROM opportunities o
            WHERE o.status = 'engaging'
              AND NOT EXISTS (SELECT 1 FROM engagements e
                              WHERE e.opportunity_id = o.id AND e.closed_at IS NULL))
         + (SELECT COUNT(*) FROM engagements
            WHERE outcome IS NOT NULL AND close_value_amount IS NULL)"
   :single))

(define-test engage-service-integration
  (if (leadscorer::database-reachable-p)
      (leadscorer:with-database
        (leadscorer:run-migrations)
        (let* ((epoch leadscorer::*virtual-epoch*)
               (ids (setup-cycle-db epoch))
               (bob (getf ids :bob))
               (op-gtk (getf ids :op-gtk))
               (op-mg (getf ids :op-mg))
               (op-gtx (getf ids :op-gtx)))
          ;; Engajar uma 'prospecting' (op-gtk) por Bob, sem justificativa.
          (is = op-gtk (leadscorer:engage-opportunity op-gtk bob epoch))
          (is equal "engaging"
              (postmodern:query "SELECT status FROM opportunities WHERE id = $1"
                                op-gtk :single))
          (destructuring-bind (agent engaged-at justification) (open-cycle-of op-gtk)
            (is = bob agent)
            (is = epoch engaged-at)
            (is eq :null justification))
          ;; Engajar uma 'engaging' (op-gtx, ja de Ann) e recusado.
          (fail (leadscorer:engage-opportunity op-gtx bob epoch)
                'leadscorer:opportunity-not-available)
          ;; Justificativa registrada: engajar op-mg por Bob com um id de justificativa.
          (let ((just (postmodern:query
                       "INSERT INTO engagement_justifications (code, description)
                        VALUES ('direct-inquiry', 'x') RETURNING id" :single)))
            (leadscorer:engage-opportunity op-mg bob epoch :justification-id just)
            (is = just (third (open-cycle-of op-mg))))
          (is = 0 (integrity-violations))))
      (skip "PostgreSQL indisponivel; teste de engajamento ignorado.")))

(define-test engage-limit-integration
  (if (leadscorer::database-reachable-p)
      (leadscorer:with-database
        (leadscorer:run-migrations)
        (let* ((epoch leadscorer::*virtual-epoch*)
               (ids (setup-cycle-db epoch))
               (ann (getf ids :ann))
               (op-gtk (getf ids :op-gtk)))
          ;; Ann ja possui uma engajada (op-gtx no setup). Com o limite em 1, engajar
          ;; outra e recusado e nada e escrito (a op-gtk permanece 'prospecting').
          (let ((leadscorer::*max-engagements* 1))
            (fail (leadscorer:engage-opportunity op-gtk ann epoch)
                  'leadscorer:engagement-limit-reached))
          (is equal "prospecting"
              (postmodern:query "SELECT status FROM opportunities WHERE id = $1"
                                op-gtk :single))
          (is = 0 (integrity-violations))))
      (skip "PostgreSQL indisponivel; teste de limite ignorado.")))

(define-test close-and-return-integration
  (if (leadscorer::database-reachable-p)
      (leadscorer:with-database
        (leadscorer:run-migrations)
        (let ((epoch leadscorer::*virtual-epoch*))
          ;; Won: a op-gtx (engajada por Ann) fecha com o preco de tabela do GTX (550).
          (let* ((ids (setup-cycle-db epoch))
                 (ann (getf ids :ann))
                 (op-gtx (getf ids :op-gtx))
                 (op-gtk (getf ids :op-gtk))
                 (now (+ epoch leadscorer::+ms-per-day+)))
            (leadscorer:close-engagement op-gtx ann :won now)
            (is equal "prospecting"
                (postmodern:query "SELECT status FROM opportunities WHERE id = $1"
                                  op-gtx :single))
            (is = 1 (postmodern:query
                     "SELECT COUNT(*) FROM engagements
                      WHERE opportunity_id = $1 AND outcome = 'won'
                        AND closed_at = $2 AND close_value_amount = 550
                        AND close_value_currency = 'USD'"
                     op-gtx now :single))
            ;; Fechar uma oportunidade sem ciclo aberto (op-gtk 'prospecting') e recusado.
            (fail (leadscorer:close-engagement op-gtk ann :won now)
                  'leadscorer:opportunity-not-available)
            (is = 0 (integrity-violations)))
          ;; Lost: valor de fechamento zero.
          (let* ((ids (setup-cycle-db epoch))
                 (ann (getf ids :ann))
                 (op-gtx (getf ids :op-gtx))
                 (now (+ epoch leadscorer::+ms-per-day+)))
            (leadscorer:close-engagement op-gtx ann :lost now)
            (is = 1 (postmodern:query
                     "SELECT COUNT(*) FROM engagements
                      WHERE opportunity_id = $1 AND outcome = 'lost'
                        AND close_value_amount = 0"
                     op-gtx :single))
            (is = 0 (integrity-violations)))
          ;; Devolucao: ciclo fechado sem desfecho, oportunidade de volta a prospecting.
          (let* ((ids (setup-cycle-db epoch))
                 (ann (getf ids :ann))
                 (op-gtx (getf ids :op-gtx))
                 (now (+ epoch leadscorer::+ms-per-day+)))
            (leadscorer:return-engagement op-gtx ann now)
            (is equal "prospecting"
                (postmodern:query "SELECT status FROM opportunities WHERE id = $1"
                                  op-gtx :single))
            (is = 1 (postmodern:query
                     "SELECT COUNT(*) FROM engagements
                      WHERE opportunity_id = $1 AND closed_at = $2
                        AND outcome IS NULL"
                     op-gtx now :single))
            (is = 0 (integrity-violations)))))
      (skip "PostgreSQL indisponivel; teste de fechamento e devolucao ignorado.")))

(define-test rescore-after-outcome-integration
  ;; Ponto de decaimento por acao do agente: um desfecho won/lost decai a oportunidade
  ;; de imediato (reescore); uma devolucao reverte a linha de base (nao e transacao).
  (if (leadscorer::database-reachable-p)
      (leadscorer:with-database
        (leadscorer:run-migrations)
        (let ((now (+ leadscorer::*virtual-epoch* leadscorer:+ms-per-day+))
              (model *cycle-model*))
          ;; Won: apos o fechamento e o reescore, o momentum e o potencial decaem a zero
          ;; (maturidade nula logo apos a transacao).
          (let* ((ids (setup-cycle-db leadscorer::*virtual-epoch*))
                 (ann (getf ids :ann)) (op-gtx (getf ids :op-gtx)))
            (leadscorer:close-engagement op-gtx ann :won now)
            (leadscorer:rescore-opportunity op-gtx model :now now)
            (is = 0 (score-momentum-of op-gtx ann))
            (is = 0 (score-overall-of op-gtx ann)))
          ;; Devolucao: apos o reescore, sem fechamento com desfecho, a pontuacao volta a
          ;; linha de base (positiva), preservando o ranqueamento anterior.
          (let* ((ids (setup-cycle-db leadscorer::*virtual-epoch*))
                 (ann (getf ids :ann)) (op-gtx (getf ids :op-gtx)))
            (leadscorer:return-engagement op-gtx ann now)
            (leadscorer:rescore-opportunity op-gtx model :now now)
            (true (plusp (score-overall-of op-gtx ann))))))
      (skip "PostgreSQL indisponivel; teste de reescore ignorado.")))
