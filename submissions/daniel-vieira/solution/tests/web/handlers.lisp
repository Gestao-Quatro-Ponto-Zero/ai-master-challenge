;;;; handlers.lisp --- Testes da lógica de rota (sessão simulada, sem servidor).

(in-package #:leadscorer/web/tests)

;;; As funções núcleo '-for' recebem a tabela de sessão explicitamente e as
;;; consultas ao banco são substituídas por indireções vinculadas, de modo que
;;; a lógica de rota (portão por papel, segregação, redirecionamentos, mutação
;;; da sessão) é exercitada sem servidor nem PostgreSQL.

(defun response-status (response) (first response))
(defun response-location (response) (getf (second response) :location))

(define-test html-response-shape
  "A resposta de HTML traz status, tipo de conteúdo UTF-8 e corpo em octetos."
  (let ((r (leadscorer/web::html-response "<p>oi</p>")))
    (is = 200 (response-status r))
    (true (search "utf-8" (getf (second r) :content-type)))
    (true (typep (third r) '(vector (unsigned-byte 8))))))

(define-test redirect-shape
  "O redirecionamento traz status 302 e o destino em Location."
  (let ((r (leadscorer/web::redirect "/login")))
    (is = 302 (response-status r))
    (is equal "/login" (response-location r))))

(define-test login-submit-success-populates-session
  "Uma seleção válida grava a sessão e redireciona à home."
  (let ((table (fresh-session))
        (leadscorer/web::*lookup-user-fn*
          (lambda (role username)
            (if (and (eq role :agent) (string= username "anna.snelling")) 42 nil))))
    (let ((r (leadscorer/web::login-submit-for
              :agent table '(("user" . "anna.snelling")))))
      (is = 302 (response-status r))
      (is equal "/" (response-location r))
      (true (leadscorer/web::authenticated-p table))
      (is eql :agent (leadscorer/web::session-role table)))))

(define-test login-submit-wrong-role-rejected
  "Um nome de usuário não pertencente ao papel é recusado, sem autenticar."
  (let ((table (fresh-session))
        (leadscorer/web::*lookup-user-fn* (lambda (role username)
                                            (declare (ignore role username)) nil))
        (leadscorer/web::*list-usernames-fn* (lambda (role)
                                               (declare (ignore role))
                                               *sample-usernames*)))
    (let ((r (leadscorer/web::login-submit-for
              :agent table '(("user" . "dustin.brinkmann")))))
      (is = 200 (response-status r))
      (false (leadscorer/web::authenticated-p table)))))

(define-test home-requires-matching-role
  "A home exige sessão autenticada do papel correto; senão redireciona ao login."
  (let ((agent-table (fresh-session))
        (empty (fresh-session)))
    (leadscorer/web::session-put agent-table 42 :agent "anna.snelling")
    ;; Papel correto: serve a home.
    (is = 200 (response-status
               (leadscorer/web::home-response-for :agent agent-table)))
    ;; Papel cruzado: recusa e redireciona.
    (let ((r (leadscorer/web::home-response-for :manager agent-table)))
      (is = 302 (response-status r))
      (is equal "/login" (response-location r)))
    ;; Sessão vazia: redireciona ao login.
    (is = 302 (response-status (leadscorer/web::home-response-for :agent empty)))))

(define-test logout-clears-session-and-redirects
  "O logout limpa a sessão e redireciona ao login."
  (let ((table (fresh-session)))
    (leadscorer/web::session-put table 42 :agent "anna.snelling")
    (let ((r (leadscorer/web::logout-response-for table)))
      (is = 302 (response-status r))
      (is equal "/login" (response-location r))
      (false (leadscorer/web::authenticated-p table)))))

(define-test apps-construct-as-callables
  "As duas aplicações são construídas como objetos funcallable."
  (true (functionp (leadscorer/web::make-agent-app)))
  (true (functionp (leadscorer/web::make-manager-app))))
