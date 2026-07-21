;;;; session.lisp --- Testes dos auxiliares puros de sessão.

(in-package #:leadscorer/web/tests)

(defun fresh-session ()
  "Constrói uma tabela de sessão vazia, como a que o middleware do Lack fornece."
  (make-hash-table :test 'eq))

(define-test session-put-and-read
  "A gravação da sessão preenche identidade, papel e nome de usuário."
  (let ((s (fresh-session)))
    (false (leadscorer/web::authenticated-p s))
    (leadscorer/web::session-put s 7 :agent "anna.snelling")
    (true (leadscorer/web::authenticated-p s))
    (is eql :agent (leadscorer/web::session-role s))
    (multiple-value-bind (id role username) (leadscorer/web::session-user s)
      (is eql 7 id)
      (is eql :agent role)
      (is equal "anna.snelling" username))))

(define-test session-clear-deauthenticates
  "A limpeza da sessão remove a autenticação (logout)."
  (let ((s (fresh-session)))
    (leadscorer/web::session-put s 3 :manager "dustin.brinkmann")
    (true (leadscorer/web::authenticated-p s))
    (leadscorer/web::session-clear s)
    (false (leadscorer/web::authenticated-p s))
    (is eql nil (leadscorer/web::session-role s))))

(define-test role-authorized-enforces-role
  "O portão por papel só autoriza a sessão do papel correspondente."
  (let ((agent (fresh-session))
        (manager (fresh-session)))
    (leadscorer/web::session-put agent 7 :agent "anna.snelling")
    (leadscorer/web::session-put manager 3 :manager "dustin.brinkmann")
    (true (leadscorer/web::role-authorized-p agent :agent))
    (false (leadscorer/web::role-authorized-p agent :manager))
    (true (leadscorer/web::role-authorized-p manager :manager))
    (false (leadscorer/web::role-authorized-p manager :agent))
    ;; Uma sessão não autenticada não é autorizada para papel algum.
    (false (leadscorer/web::role-authorized-p (fresh-session) :agent))))

(define-test regenerate-session-id-noop-without-request
  "C1: sem requisição corrente (funções núcleo sem servidor), a rotação do identificador
de sessão é um no-op seguro, sem sinalizar erro nem exigir um ambiente de requisição."
  (is eq nil (leadscorer/web::regenerate-session-id)))

(define-test mark-session-for-id-rotation-sets-change-id
  "C1 (caminho positivo): a marcação define ':change-id' em ':lack.session.options' do
ambiente, de modo que o middleware do Lack gere um novo identificador de sessão preservando
os dados; sem as opções de sessão no ambiente, nada é marcado."
  (let ((env (list :lack.session.options (list :id "antigo" :change-id nil :expire nil))))
    (true (leadscorer/web::mark-session-for-id-rotation env))
    (is eq t (getf (getf env :lack.session.options) :change-id)))
  (is eq nil (leadscorer/web::mark-session-for-id-rotation (list))))
