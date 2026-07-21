;;;; cycle.lisp --- Testes Parachute da configuracao e dos servicos de ciclo.

(in-package #:leadscorer/tests)

;;; --- Configuracao em forma Lisp ---

(defparameter *config-valid*
  (asdf:system-relative-pathname :leadscorer "tests/fixtures/config/valid.lisp")
  "Fixture de configuracao valida.")

(defparameter *config-invalid-type*
  (asdf:system-relative-pathname :leadscorer
                                 "tests/fixtures/config/invalid-type.lisp")
  "Fixture de configuracao com valor de tipo invalido.")

(defparameter *config-read-eval*
  (asdf:system-relative-pathname :leadscorer
                                 "tests/fixtures/config/read-eval.lisp")
  "Fixture que tenta avaliacao em tempo de leitura.")

(define-test config-reads-valid-plist
  (let ((plist (leadscorer::read-config-form *config-valid*)))
    (is = 0.40 (getf plist :weight-economic))
    (is eq :geometric (getf plist :composite-form))
    (is = 1514678400000 (getf plist :virtual-epoch))))

(define-test config-validates-good-plist
  (let ((plist (leadscorer::read-config-form *config-valid*)))
    (is eq plist (leadscorer::validate-config plist))))

(define-test config-rejects-unknown-key
  (fail (leadscorer::validate-config '(:chave-inexistente 1))))

(define-test config-rejects-bad-type
  (let ((plist (leadscorer::read-config-form *config-invalid-type*)))
    (fail (leadscorer::validate-config plist))))

(define-test config-read-eval-disarmed
  (fail (leadscorer::read-config-form *config-read-eval*)))

(define-test config-apply-sets-globals
  (let ((leadscorer::*weight-economic* 0.0)
        (leadscorer::*max-engagements* 1))
    (leadscorer::apply-config '(:weight-economic 0.7 :max-engagements 5))
    (is = 0.7 leadscorer::*weight-economic*)
    (is = 5 leadscorer::*max-engagements*)))

(define-test config-canonical-file-loads
  ;; O arquivo versionado 'config/model.lisp' deve ser valido e aplicavel.
  (let ((leadscorer::*weight-economic* 0.0))
    (let ((plist (leadscorer::validate-config
                  (leadscorer::read-config-form leadscorer::*config-path*))))
      (true (listp plist))
      (leadscorer::apply-config plist)
      (is = 0.40 leadscorer::*weight-economic*))))

;;; --- Relogio virtual e utilitarios puros ---

(defparameter *cycle-model* (leadscorer:load-model *derived-fixtures*)
  "Modelo carregado dos fixtures derivados (decay de 3 pontos, horizonte 2).")

(define-test clock-compression-exact
  ;; horizonte 2 dias virtuais em 20 min reais: 2*86400000 / (20*60000) = 144.
  (let ((leadscorer::*expiration-minutes* 20))
    (is = 144 (leadscorer::clock-compression 2))))

(define-test virtual-now-anchors-and-advances
  (let ((leadscorer::*expiration-minutes* 20))
    ;; Em T0, o instante virtual e a epoca.
    (is = 0 (leadscorer::virtual-now 1000 1000 0 2))
    ;; 20 min reais (1.200.000 ms) avancam o horizonte (2 dias = 172.800.000 ms).
    (is = 172800000 (leadscorer::virtual-now (+ 1000 1200000) 1000 0 2))))

(define-test decay-horizon-from-model
  (is = 2 (leadscorer::decay-horizon-days *cycle-model*)))

(define-test virtual-age-days-cases
  (is eq nil (leadscorer::virtual-age-days 0 nil))
  (is = 1 (leadscorer::virtual-age-days 86400000 0))
  (is = 0 (leadscorer::virtual-age-days 0 86400000)))

(define-test accelerated-age-index-clamps
  (is = 0 (leadscorer::accelerated-age-index 0 3))
  (is = 1 (leadscorer::accelerated-age-index 1 3))
  (is = 2 (leadscorer::accelerated-age-index 5 3)))

(define-test cycle-expired-predicate
  (true (leadscorer::cycle-expired-p 2 2))
  (true (leadscorer::cycle-expired-p 3 2))
  (false (leadscorer::cycle-expired-p 1 2)))

(define-test real-minutes-to-expiration-cases
  ;; Horizonte 2 dias em 20 min reais: idade 0 -> 20 min, idade 1 -> 10, idade >=2 -> 0.
  (let ((leadscorer::*expiration-minutes* 20)
        (day leadscorer:+ms-per-day+)
        (epoch 0))
    (is = 20 (leadscorer:real-minutes-to-expiration epoch epoch *cycle-model*))
    (is = 10 (leadscorer:real-minutes-to-expiration epoch (+ epoch day) *cycle-model*))
    (is = 0 (leadscorer:real-minutes-to-expiration epoch (+ epoch (* 2 day))
                                                    *cycle-model*))))

(define-test engagement-expired-predicate
  ;; Horizonte 2 dias: a mesma regra que zera 'real-minutes-to-expiration'. Idade < 2 nao
  ;; expirou; idade >= 2 (alcancou o horizonte) expirou. NOW ou ENGAGED-AT nulo -> NIL.
  (let ((day leadscorer:+ms-per-day+)
        (epoch 0))
    (false (leadscorer:engagement-expired-p epoch (+ epoch day) *cycle-model*))
    (true (leadscorer:engagement-expired-p epoch (+ epoch (* 2 day)) *cycle-model*))
    (true (leadscorer:engagement-expired-p epoch (+ epoch (* 3 day)) *cycle-model*))
    (is eq nil (leadscorer:engagement-expired-p epoch nil *cycle-model*))
    (is eq nil (leadscorer:engagement-expired-p nil (+ epoch day) *cycle-model*))))

(define-test score-to-int-clamps-and-rounds
  (is = 50 (leadscorer::score->int 49.6))
  (is = 0 (leadscorer::score->int -3))
  (is = 100 (leadscorer::score->int 150))
  (is = 0 (leadscorer::score->int 0.5)))

(define-test index-pairs-by-name
  (let ((pair (gethash (cons "Acme" "GTX Basic")
                       (leadscorer::index-pairs *cycle-model*))))
    (true pair)
    (is equal "GTX Basic" (leadscorer::pair-product pair))))

(define-test median-cadence-of-fixtures
  ;; Cadencias 16, 17, 33 -> mediana 17.
  (is = 17.0 (leadscorer::median-cadence *cycle-model*)))

;;; --- Pontuacao de linhas ---

(define-test fallback-scored-neutral-base
  (let ((s (leadscorer::fallback-scored "Ann" "X" "Y" 0.5 *cycle-model*)))
    (is = 50.0 (leadscorer:scored-economic s))
    (is = 50.0 (leadscorer:scored-affinity s))
    (is = 0.5 (leadscorer:scored-momentum s))))

(define-test prospecting-baseline-matches-score-pair
  (let* ((pair (gethash (cons "Acme" "GTX Basic")
                        (leadscorer::index-pairs *cycle-model*)))
         (baseline (leadscorer::score-pair "Ann" pair *cycle-model*))
         (scored (leadscorer::score-prospecting "Ann" "Acme" "GTX Basic" pair
                                                nil 0 17.0 *cycle-model*)))
    (is = (leadscorer:scored-composite baseline)
        (leadscorer:scored-composite scored))))

(define-test prospecting-live-return-decays-to-zero
  ;; Fechamento vivo no mesmo instante virtual: idade 0 -> maturidade 0 -> comp 0.
  (let* ((pair (gethash (cons "Acme" "GTX Basic")
                        (leadscorer::index-pairs *cycle-model*)))
         (scored (leadscorer::score-prospecting "Ann" "Acme" "GTX Basic" pair
                                                1000 1000 17.0 *cycle-model*)))
    (is = 0.0 (leadscorer:scored-momentum scored))
    (is = 0.0 (leadscorer:scored-composite scored))))

(define-test prospecting-fallback-uses-neutral
  ;; Par desconhecido e nunca fechado: economico/afinidade neutros (50) e momentum
  ;; neutro (*maturity-neutral* = 0,5), nao zero. Com fechamento vivo recente
  ;; (idade 0), o momentum decai a zero (devolucao).
  (let ((idle (leadscorer::score-prospecting "Ann" "NoAccount" "NoProduct" nil
                                             nil 0 17.0 *cycle-model*))
        (returned (leadscorer::score-prospecting "Ann" "NoAccount" "NoProduct" nil
                                                 1000 1000 17.0 *cycle-model*)))
    (is = 50.0 (leadscorer:scored-economic idle))
    (is = 0.5 (leadscorer:scored-momentum idle))
    (true (plusp (leadscorer:scored-composite idle)))
    (is = 0.0 (leadscorer:scored-momentum returned))))

(define-test engaging-decay-decreases-with-age
  (let* ((opp (gethash (cons "Acme" "GTX Basic")
                       (leadscorer::index-opportunities *cycle-model*)))
         (fresh (leadscorer::score-engaging "Ann" "Acme" "GTX Basic" opp 0
                                            *cycle-model*))
         (old (leadscorer::score-engaging "Ann" "Acme" "GTX Basic" opp 2
                                          *cycle-model*)))
    (is = 0.0 (leadscorer:scored-momentum old))
    (is = 0.0 (leadscorer:scored-composite old))
    (true (> (leadscorer:scored-composite fresh)
             (leadscorer:scored-composite old)))))

;;; --- Drivers de persistencia (integracao, gated por banco) ---

(defun setup-cycle-db (engaged-at)
  "Prepara um estado minimo alinhado aos fixtures derivados: agentes Ann/Bob, conta
Acme, produtos GTX Basic/GTK 500/MG Special, duas oportunidades 'prospecting'
(GTK, MG) e uma 'engaging' (Acme x GTX Basic por Ann, engajada em ENGAGED-AT) com
ciclo aberto. Assume conexao ativa; trunca e recarrega em uma transacao. Retorna uma
plist com os ids relevantes."
  (postmodern:with-transaction ()
    (postmodern:execute
     "TRUNCATE engagements, opportunity_scores, opportunities,
               engagement_justifications, sales_agents, sales_managers,
               regional_offices, accounts, products RESTART IDENTITY CASCADE")
    (let* ((office (postmodern:query
                    "INSERT INTO regional_offices (name) VALUES ('R1') RETURNING id"
                    :single))
           (manager (postmodern:query
                     "INSERT INTO sales_managers (name, username, regional_office_id)
                      VALUES ('M1', 'm1', $1) RETURNING id" office :single))
           (ann (postmodern:query
                 "INSERT INTO sales_agents (name, username, sales_manager_id)
                  VALUES ('Ann', 'ann', $1) RETURNING id" manager :single))
           (bob (postmodern:query
                 "INSERT INTO sales_agents (name, username, sales_manager_id)
                  VALUES ('Bob', 'bob', $1) RETURNING id" manager :single))
           (acme (postmodern:query
                  "INSERT INTO accounts (name, sector, revenue_amount, revenue_currency)
                   VALUES ('Acme', 'Tech', 1, 'USD') RETURNING id" :single))
           (gtx (postmodern:query
                 "INSERT INTO products (name, series, list_price_amount,
                      list_price_currency)
                  VALUES ('GTX Basic', 'GTX', 550, 'USD') RETURNING id" :single))
           (gtk (postmodern:query
                 "INSERT INTO products (name, series, list_price_amount,
                      list_price_currency)
                  VALUES ('GTK 500', 'GTK', 26768, 'USD') RETURNING id" :single))
           (mg (postmodern:query
                "INSERT INTO products (name, series, list_price_amount,
                     list_price_currency)
                 VALUES ('MG Special', 'MG', 55, 'USD') RETURNING id" :single))
           (op-gtk (postmodern:query
                    "INSERT INTO opportunities (account_id, product_id, status,
                         created_at)
                     VALUES ($1, $2, 'prospecting', 0) RETURNING id" acme gtk :single))
           (op-mg (postmodern:query
                   "INSERT INTO opportunities (account_id, product_id, status,
                        created_at)
                    VALUES ($1, $2, 'prospecting', 0) RETURNING id" acme mg :single))
           (op-gtx (postmodern:query
                    "INSERT INTO opportunities (account_id, product_id, status,
                         engaged_by_id, engaged_at, created_at)
                     VALUES ($1, $2, 'engaging', $3, $4, 0) RETURNING id"
                    acme gtx ann engaged-at :single)))
      (postmodern:execute
       "INSERT INTO engagements (opportunity_id, sales_agent_id, engaged_at)
        VALUES ($1, $2, $3)" op-gtx ann engaged-at)
      (list :ann ann :bob bob :op-gtk op-gtk :op-mg op-mg :op-gtx op-gtx))))

(defun score-momentum-of (opportunity-id agent-id)
  "O 'score_momentum' de 'opportunity_scores' para OPPORTUNITY-ID e AGENT-ID."
  (postmodern:query
   "SELECT score_momentum FROM opportunity_scores
    WHERE opportunity_id = $1 AND sales_agent_id = $2"
   opportunity-id agent-id :single))

(defun score-overall-of (opportunity-id agent-id)
  "O 'score_overall' de 'opportunity_scores' para OPPORTUNITY-ID e AGENT-ID."
  (postmodern:query
   "SELECT score_overall FROM opportunity_scores
    WHERE opportunity_id = $1 AND sales_agent_id = $2"
   opportunity-id agent-id :single))

(define-test cycle-drivers-integration
  (if (leadscorer::database-reachable-p)
      (leadscorer:with-database
        (leadscorer:run-migrations)
        (let* ((epoch leadscorer::*virtual-epoch*)
               (ms-day leadscorer::+ms-per-day+)
               (model (leadscorer:load-model *derived-fixtures*))
               (ids (setup-cycle-db epoch)))
          ;; 1. Ranqueamento em now=epoch: 2 prospecting x 2 agentes = 4 linhas.
          (leadscorer::rank-prospecting-opportunities model :now epoch)
          (is = 4 (postmodern:query "SELECT COUNT(*) FROM opportunity_scores" :single))
          (is = 4 (postmodern:query
                   "SELECT COUNT(*) FROM opportunity_scores
                    WHERE score_overall BETWEEN 0 AND 100
                      AND score_adherence IS NOT NULL
                      AND score_closing_time IS NULL
                      AND score_inactivity IS NULL" :single))
          ;; A engajada nao recebe linhas de prospecting.
          (is = 0 (postmodern:query
                   "SELECT COUNT(*) FROM opportunity_scores WHERE opportunity_id = $1"
                   (getf ids :op-gtx) :single))
          ;; 2. Decaimento: momentum decresce com a idade virtual.
          (leadscorer::decay-engaged-opportunities model :now epoch)
          (let ((m0 (score-momentum-of (getf ids :op-gtx) (getf ids :ann))))
            (leadscorer::decay-engaged-opportunities model :now (+ epoch ms-day))
            (let ((m1 (score-momentum-of (getf ids :op-gtx) (getf ids :ann))))
              (is = 100 m0)
              (true (< m1 m0))))
          ;; 3. Expiracao no horizonte (2 dias): a engajada volta a prospecting.
          (leadscorer::expire-due-opportunities model :now (+ epoch (* 2 ms-day)))
          (is equal "prospecting"
              (postmodern:query "SELECT status FROM opportunities WHERE id = $1"
                                (getf ids :op-gtx) :single))
          (is = 1 (postmodern:query
                   "SELECT COUNT(*) FROM engagements
                    WHERE opportunity_id = $1 AND outcome = 'lost'
                      AND expired = TRUE AND closed_at IS NOT NULL
                      AND close_value_amount = 0 AND close_value_currency = 'USD'"
                   (getf ids :op-gtx) :single))
          (is = 0 (postmodern:query
                   "SELECT COUNT(*) FROM engagements WHERE closed_at IS NULL" :single))
          ;; Invariante de verify.lisp: nenhum ciclo fechado com desfecho e sem valor.
          (is = 0 (postmodern:query
                   "SELECT COUNT(*) FROM engagements
                    WHERE outcome IS NOT NULL AND close_value_amount IS NULL" :single))
          ;; 4. Devolucao com potencial decaido, recuperando pela corcova.
          (let ((now (+ epoch (* 2 ms-day))))
            (leadscorer::rank-prospecting-opportunities model :now now)
            (let ((fresh (score-overall-of (getf ids :op-gtx) (getf ids :ann))))
              (is = 0 fresh)
              ;; Cadencia do GTX Basic = 16 dias: em now+16 dias, a maturidade sobe.
              (leadscorer::rank-prospecting-opportunities model
                                                          :now (+ now (* 16 ms-day)))
              (true (> (score-overall-of (getf ids :op-gtx) (getf ids :ann))
                       fresh))))
          ;; 5. Reconciliacao apos um tick completo (setup fresco).
          (let ((ids2 (setup-cycle-db epoch)))
            (leadscorer::run-cycle-tick model :now epoch)
            (is = 1 (postmodern:query
                     "SELECT COUNT(*) FROM opportunity_scores WHERE opportunity_id = $1"
                     (getf ids2 :op-gtx) :single))
            (is = 2 (postmodern:query
                     "SELECT COUNT(*) FROM opportunity_scores WHERE opportunity_id = $1"
                     (getf ids2 :op-gtk) :single)))))
      (skip "PostgreSQL indisponivel; teste de integracao do ciclo ignorado.")))
