;;;; opportunities.lisp --- Testes das consultas de oportunidades e do
;;;; enriquecimento pelo modelo.

(in-package #:leadscorer/web/tests)

;;; --- Enriquecimento pelo modelo (puro) ---

(define-test enrich-rows-with-model-adds-context
  (let ((index (make-hash-table :test #'equal)))
    (setf (gethash (cons "Acme" "GTX Basic") index)
          (list :cadence-days 16 :last-close-value 500))
    (let* ((rows (list (list :account "Acme" :product "GTX Basic" :overall 80)
                       (list :account "Nobody" :product "GTX Basic" :overall 10)))
           (enriched (leadscorer/web::enrich-rows-with-model rows index)))
      ;; Par conhecido: os dois campos do modelo sao acrescentados.
      (is = 16 (getf (first enriched) :cadence-days))
      (is = 500 (getf (first enriched) :last-close-value))
      ;; Os campos originais permanecem acessiveis.
      (is = 80 (getf (first enriched) :overall))
      ;; Par ausente do indice: os campos degradam para NIL.
      (is eq nil (getf (second enriched) :cadence-days))
      (is eq nil (getf (second enriched) :last-close-value)))))

(define-test enrich-rows-with-model-nil-index
  ;; Indice NIL (modelo indisponivel): os campos ficam NIL, sem erro.
  (let ((enriched (leadscorer/web::enrich-rows-with-model
                   (list (list :account "Acme" :product "GTX Basic")) nil)))
    (is eq nil (getf (first enriched) :cadence-days))
    (is eq nil (getf (first enriched) :last-close-value))))

;;; --- Consultas de oportunidades (integracao, gated por banco) ---

(defun setup-web-opps ()
  "Prepara um estado minimo para as consultas de oportunidades: um agente, uma conta
Acme, dois produtos (GTX Basic prospecting, MG Special engajado pelo agente), as linhas
de 'opportunity_scores' do agente, um ciclo aberto com justificativa e dois ciclos
fechados (um won de 200 fechado em um dia virtual, um lost). Assume conexao ativa; trunca
e recarrega em uma transacao. Retorna uma plist com os ids relevantes."
  (let ((epoch leadscorer::*virtual-epoch*)
        (day leadscorer:+ms-per-day+))
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
             (agent (postmodern:query
                     "INSERT INTO sales_agents (name, username, sales_manager_id)
                      VALUES ('Ann', 'ann', $1) RETURNING id" manager :single))
             (acme (postmodern:query
                    "INSERT INTO accounts
                         (name, sector, location, employees, revenue_amount,
                          revenue_currency, year_established)
                     VALUES ('Acme', 'Tech', 'East', 50, 1000, 'USD', 2001)
                     RETURNING id" :single))
             (gtx (postmodern:query
                   "INSERT INTO products (name, series, list_price_amount,
                        list_price_currency)
                    VALUES ('GTX Basic', 'GTX', 550, 'USD') RETURNING id" :single))
             (mg (postmodern:query
                  "INSERT INTO products (name, series, list_price_amount,
                       list_price_currency)
                   VALUES ('MG Special', 'MG', 55, 'USD') RETURNING id" :single))
             (op-gtx (postmodern:query
                      "INSERT INTO opportunities (account_id, product_id, status,
                           created_at)
                       VALUES ($1, $2, 'prospecting', 0) RETURNING id"
                      acme gtx :single))
             (op-mg (postmodern:query
                     "INSERT INTO opportunities (account_id, product_id, status,
                          engaged_by_id, engaged_at, created_at)
                      VALUES ($1, $2, 'engaging', $3, $4, 0) RETURNING id"
                     acme mg agent epoch :single))
             (just (postmodern:query
                    "INSERT INTO engagement_justifications (code, description)
                     VALUES ('direct-inquiry', 'x') RETURNING id" :single)))
        ;; Pontuacoes do agente para as duas oportunidades.
        (postmodern:execute
         "INSERT INTO opportunity_scores
              (opportunity_id, sales_agent_id, score_overall, score_economic,
               score_affinity, score_momentum, score_adherence, computed_at)
          VALUES ($1, $2, 80, 70, 60, 90, 50, 0)" op-gtx agent)
        (postmodern:execute
         "INSERT INTO opportunity_scores
              (opportunity_id, sales_agent_id, score_overall, score_economic,
               score_affinity, score_momentum, score_adherence, computed_at)
          VALUES ($1, $2, 40, 35, 30, 25, 20, 0)" op-mg agent)
        ;; Ciclo aberto (op-mg) com justificativa e dois ciclos fechados (won/lost).
        (postmodern:execute
         "INSERT INTO engagements
              (opportunity_id, sales_agent_id, justification_id, engaged_at)
          VALUES ($1, $2, $3, $4)" op-mg agent just epoch)
        (postmodern:execute
         "INSERT INTO engagements
              (opportunity_id, sales_agent_id, engaged_at, closed_at, outcome,
               close_value_amount, close_value_currency)
          VALUES ($1, $2, $3, $4, 'won', 200, 'USD')" op-gtx agent epoch (+ epoch day))
        (postmodern:execute
         "INSERT INTO engagements
              (opportunity_id, sales_agent_id, engaged_at, closed_at, outcome,
               close_value_amount, close_value_currency)
          VALUES ($1, $2, $3, $4, 'lost', 0, 'USD')" op-gtx agent epoch (+ epoch day))
        (list :agent agent :op-gtx op-gtx :op-mg op-mg :just just :epoch epoch)))))

(define-test opportunity-queries-integration
  (if (leadscorer::database-reachable-p)
      (leadscorer:with-database
        (leadscorer:run-migrations)
        (let* ((ids (setup-web-opps))
               (agent (getf ids :agent))
               (epoch (getf ids :epoch)))
          ;; Disponiveis: uma linha (op-gtx), com contexto e pontuacoes.
          (let ((available (leadscorer/web::list-prospecting-for-agent agent)))
            (is = 1 (length available))
            (let ((row (first available)))
              (is equal "Acme" (getf row :account))
              (is equal "GTX Basic" (getf row :product))
              (is equal "East" (getf row :location))
              (is = 50 (getf row :employees))
              (is = 80 (getf row :overall))
              (is = 90 (getf row :momentum))
              (is = 70 (getf row :economic))))
          ;; Engajadas: uma linha (op-mg), com justificativa e instante de engajamento.
          (let ((engaged (leadscorer/web::list-engaged-for-agent agent)))
            (is = 1 (length engaged))
            (let ((row (first engaged)))
              (is equal "MG Special" (getf row :product))
              (is = 40 (getf row :overall))
              (is = epoch (getf row :engaged-at))
              (is equal "direct-inquiry" (getf row :justification-code))))
          ;; Indicadores: 3 ciclos, 1 won, 1 lost, taxa 50,0%, ticket 200, tempo 1 dia.
          (let ((kpis (leadscorer/web::agent-kpis agent)))
            (is = 3 (getf kpis :cycles))
            (is = 1 (getf kpis :wins))
            (is = 1 (getf kpis :losses))
            (is = 500 (getf kpis :success-rate-tenths))
            (is = 200 (getf kpis :avg-ticket-amount))
            (is = 200 (getf kpis :total-sales-amount))
            (is = 1 (getf kpis :avg-days))
            (is equal "USD" (getf kpis :currency)))
          ;; Justificativas: a semeada consta com o seu codigo.
          (let ((js (leadscorer/web::justifications)))
            (is = 1 (length js))
            (is equal "direct-inquiry" (getf (first js) :code)))))
      (skip "PostgreSQL indisponivel; teste de consultas de oportunidades ignorado.")))

;;; --- Consultas do time (aplicacao do gerente, integracao gated) ---

(defun setup-web-team ()
  "Prepara um estado minimo para as consultas do time: um gerente M1 com dois
agentes (ann, bob) e um gerente M2 com um agente (carol) que serve de controle de
escopo. Uma conta Acme e dois produtos; op1 (GTX) engajada por ann com ciclo aberto
e op2 (MG) prospecting com os ciclos fechados. Os cinco estados de ciclo do time M1
ficam representados (aberto, won, lost, expirado, devolvido); um won de carol (M2)
NAO deve aparecer para M1. Assume conexao ativa; trunca e recarrega em transacao.
Retorna uma plist com os ids relevantes."
  (let ((epoch leadscorer::*virtual-epoch*)
        (day leadscorer:+ms-per-day+))
    (postmodern:with-transaction ()
      (postmodern:execute
       "TRUNCATE engagements, opportunity_scores, opportunities,
                 engagement_justifications, sales_agents, sales_managers,
                 regional_offices, accounts, products RESTART IDENTITY CASCADE")
      (let* ((office (postmodern:query
                      "INSERT INTO regional_offices (name) VALUES ('R1') RETURNING id"
                      :single))
             (m1 (postmodern:query
                  "INSERT INTO sales_managers (name, username, regional_office_id)
                   VALUES ('M1', 'm1', $1) RETURNING id" office :single))
             (m2 (postmodern:query
                  "INSERT INTO sales_managers (name, username, regional_office_id)
                   VALUES ('M2', 'm2', $1) RETURNING id" office :single))
             (ann (postmodern:query
                   "INSERT INTO sales_agents (name, username, sales_manager_id)
                    VALUES ('Ann', 'ann', $1) RETURNING id" m1 :single))
             (bob (postmodern:query
                   "INSERT INTO sales_agents (name, username, sales_manager_id)
                    VALUES ('Bob', 'bob', $1) RETURNING id" m1 :single))
             (carol (postmodern:query
                     "INSERT INTO sales_agents (name, username, sales_manager_id)
                      VALUES ('Carol', 'carol', $1) RETURNING id" m2 :single))
             (acme (postmodern:query
                    "INSERT INTO accounts
                         (name, sector, location, employees, revenue_amount,
                          revenue_currency, year_established)
                     VALUES ('Acme', 'Tech', 'East', 50, 1000, 'USD', 2001)
                     RETURNING id" :single))
             (gtx (postmodern:query
                   "INSERT INTO products (name, series, list_price_amount,
                        list_price_currency)
                    VALUES ('GTX Basic', 'GTX', 550, 'USD') RETURNING id" :single))
             (mg (postmodern:query
                  "INSERT INTO products (name, series, list_price_amount,
                       list_price_currency)
                   VALUES ('MG Special', 'MG', 55, 'USD') RETURNING id" :single))
             (op1 (postmodern:query
                   "INSERT INTO opportunities (account_id, product_id, status,
                        engaged_by_id, engaged_at, created_at)
                    VALUES ($1, $2, 'engaging', $3, $4, 0) RETURNING id"
                   acme gtx ann epoch :single))
             (op2 (postmodern:query
                   "INSERT INTO opportunities (account_id, product_id, status,
                        created_at)
                    VALUES ($1, $2, 'prospecting', 0) RETURNING id"
                   acme mg :single))
             (just (postmodern:query
                    "INSERT INTO engagement_justifications (code, description)
                     VALUES ('direct-inquiry', 'x') RETURNING id" :single)))
        ;; Pontuacoes correntes por par.
        (dolist (spec (list (list op1 ann 80) (list op2 ann 55) (list op2 bob 60)))
          (destructuring-bind (op agent overall) spec
            (postmodern:execute
             "INSERT INTO opportunity_scores
                  (opportunity_id, sales_agent_id, score_overall, score_economic,
                   score_affinity, score_momentum, score_adherence, computed_at)
              VALUES ($1, $2, $3, 50, 50, 50, 50, 0)" op agent overall)))
        ;; Ciclo aberto de ann (op1), com justificativa.
        (postmodern:execute
         "INSERT INTO engagements
              (opportunity_id, sales_agent_id, justification_id, engaged_at)
          VALUES ($1, $2, $3, $4)" op1 ann just epoch)
        ;; Won de ann (op2, valor 200).
        (postmodern:execute
         "INSERT INTO engagements
              (opportunity_id, sales_agent_id, engaged_at, closed_at, outcome,
               close_value_amount, close_value_currency)
          VALUES ($1, $2, $3, $4, 'won', 200, 'USD')" op2 ann epoch (+ epoch day))
        ;; Lost nao expirado de bob (op2).
        (postmodern:execute
         "INSERT INTO engagements
              (opportunity_id, sales_agent_id, engaged_at, closed_at, outcome, expired)
          VALUES ($1, $2, $3, $4, 'lost', FALSE)" op2 bob epoch (+ epoch day))
        ;; Expirado (lost + expired) de bob (op2).
        (postmodern:execute
         "INSERT INTO engagements
              (opportunity_id, sales_agent_id, engaged_at, closed_at, outcome, expired)
          VALUES ($1, $2, $3, $4, 'lost', TRUE)" op2 bob epoch (+ epoch day))
        ;; Devolvido (fechado sem desfecho) de ann (op2).
        (postmodern:execute
         "INSERT INTO engagements
              (opportunity_id, sales_agent_id, engaged_at, closed_at)
          VALUES ($1, $2, $3, $4)" op2 ann epoch (+ epoch day))
        ;; Controle de escopo: won de carol (M2), fora do time de M1.
        (postmodern:execute
         "INSERT INTO engagements
              (opportunity_id, sales_agent_id, engaged_at, closed_at, outcome,
               close_value_amount, close_value_currency)
          VALUES ($1, $2, $3, $4, 'won', 999, 'USD')" op2 carol epoch (+ epoch day))
        (list :m1 m1 :m2 m2 :ann ann :bob bob :carol carol
              :op1 op1 :op2 op2 :epoch epoch)))))

(define-test team-queries-integration
  (if (leadscorer::database-reachable-p)
      (leadscorer:with-database
        (leadscorer:run-migrations)
        (let* ((ids (setup-web-team))
               (m1 (getf ids :m1)))
          ;; Agentes do time: ann e bob, em ordem de username; carol (M2) excluida.
          (let ((agents (leadscorer/web::team-agents m1)))
            (is = 2 (length agents))
            (is equal "ann" (getf (first agents) :username))
            (is equal "bob" (getf (second agents) :username)))
          ;; Indicadores do time M1 (5 ciclos: won, lost, expirado, devolvido, aberto):
          ;; 1 won, 2 losses (lost + expirado), taxa 33,3%, ticket 200, tempo 1 dia.
          ;; O won de carol (999) NAO entra.
          (let ((kpis (leadscorer/web::team-kpis m1)))
            (is = 5 (getf kpis :cycles))
            (is = 1 (getf kpis :wins))
            (is = 2 (getf kpis :losses))
            (is = 333 (getf kpis :success-rate-tenths))
            (is = 200 (getf kpis :avg-ticket-amount))
            (is = 200 (getf kpis :total-sales-amount))
            (is = 1 (getf kpis :avg-days)))
          ;; Engajadas em curso: apenas o ciclo aberto de ann (op1).
          (let ((engaged (leadscorer/web::team-engaged m1)))
            (is = 1 (length engaged))
            (let ((row (first engaged)))
              (is equal "ann" (getf row :agent-username))
              (is equal "GTX Basic" (getf row :product))
              (is = 80 (getf row :overall))
              (is equal "direct-inquiry" (getf row :justification-code))))
          ;; Ciclos do time: os cinco de M1, com os cinco estados; carol ausente.
          (let ((cycles (leadscorer/web::team-cycles m1)))
            (is = 5 (length cycles))
            (true (every (lambda (r) (member (getf r :agent-username)
                                             '("ann" "bob") :test #'equal))
                         cycles))
            (let ((states (mapcar #'leadscorer/web::cycle-state cycles)))
              (dolist (state '(:open :won :lost :expired :returned))
                (true (member state states)
                      "Estado ~S presente nos ciclos do time." state))))))
      (skip "PostgreSQL indisponivel; teste de consultas do time ignorado.")))
