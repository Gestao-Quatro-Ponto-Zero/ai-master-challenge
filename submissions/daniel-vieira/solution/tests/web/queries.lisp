;;;; queries.lisp --- Testes das consultas de login (integração com PostgreSQL).

(in-package #:leadscorer/web/tests)

;;; Estes testes exigem um PostgreSQL alcançável e semeado. Seguem a convenção
;;; da suíte de persistência: quando o banco não está disponível, o teste é
;;; ignorado ('skip') de modo que a suíte permaneça verde sem banco. As
;;; contagens canônicas (35 agentes, 6 gerentes) residem em 'src/verify.lisp'.

(define-test list-usernames-and-lookup-live
  "Lista os usuários semeados por papel e valida a segregação na busca."
  (if (leadscorer::database-reachable-p)
      (progn
        (leadscorer:with-database
          (leadscorer:run-migrations)
          (leadscorer:seed-database))
        (let ((agents (leadscorer/web::list-usernames :agent))
              (managers (leadscorer/web::list-usernames :manager)))
          (is = 35 (length agents))
          (is = 6 (length managers))
          ;; Um nome de agente é validado no papel de agente e recusado no de
          ;; gerente, e vice-versa: a segregação por papel na própria consulta.
          (let ((agent-name (first agents))
                (manager-name (first managers)))
            (true (integerp (leadscorer/web::lookup-user :agent agent-name)))
            (is eql nil (leadscorer/web::lookup-user :manager agent-name))
            (true (integerp (leadscorer/web::lookup-user :manager manager-name)))
            (is eql nil (leadscorer/web::lookup-user :agent manager-name)))
          ;; Uma seleção inexistente é recusada.
          (is eql nil (leadscorer/web::lookup-user :agent "inexistente.ninguem"))))
      (skip "PostgreSQL indisponível; teste de integração de login ignorado.")))

(define-test engaged-row-denulls-outer-join-columns
  "Regressao A1: a conversao da lista de engajadas do agente normaliza o marcador
':null' do Postmodern (juncao externa de opportunity_scores na janela entre o
engajamento e o proximo tique, e da justificativa dentro do top tier) para NIL, de modo
que RENDER-SCORE nao sinalize um type-error sobre ':null'. Teste puro, sem banco."
  (let ((row (leadscorer/web::engaged-row->plist
              (list 7 "Golddex" "Tech" "SP" "GTX Basic" "basic"
                    :null :null :null :null :null
                    1514678400000 :null))))
    (is eq nil (getf row :overall))
    (is eq nil (getf row :momentum))
    (is eq nil (getf row :economic))
    (is eq nil (getf row :affinity))
    (is eq nil (getf row :adherence))
    (is eq nil (getf row :justification-code))
    ;; O instante de engajamento nao vem de juncao externa: permanece intacto.
    (is = 1514678400000 (getf row :engaged-at))))

(define-test kpis-plist-derivation
  "D1: a derivacao dos indicadores a partir dos agregados de ciclos, partilhada pelo agente
e pelo time: taxa de sucesso em decimos de ponto percentual, ticket e tempo medios com
arredondamento do banqueiro, e NIL sem ciclos fechados ou sem 'won'. Teste puro, sem banco."
  (let ((k (leadscorer/web::kpis-plist 10 6 4 600000 (* 6 3 leadscorer:+ms-per-day+))))
    (is = 10 (getf k :cycles))
    (is = 6 (getf k :wins))
    (is = 4 (getf k :losses))
    (is = 600 (getf k :success-rate-tenths))   ; 6 won sobre 10 fechados = 60,0%
    (is = 100000 (getf k :avg-ticket-amount))  ; 600000 / 6
    (is = 600000 (getf k :total-sales-amount))
    (is = 3 (getf k :avg-days)))               ; (6*3 dias) / 6
  (let ((k (leadscorer/web::kpis-plist 0 0 0 0 0)))
    (is eq nil (getf k :success-rate-tenths))
    (is eq nil (getf k :avg-ticket-amount))
    (is eq nil (getf k :avg-days))
    (is = 0 (getf k :total-sales-amount))))
