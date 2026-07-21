;;;; session.lisp --- Sessão de servidor e portão de autorização por papel.

(in-package #:leadscorer/web)

;;; O middleware de sessão do Lack coloca a tabela de sessão no ambiente da
;;; requisição sob a chave :LACK.SESSION. O acessor 'session-table' isola essa
;;; dependência de API num único ponto; os demais auxiliares operam sobre a
;;; tabela e são puros, testáveis sem servidor nem banco. As chaves da sessão
;;; são palavras-chave.

(defun session-table ()
  "Retorna a tabela de sessão da requisição Ningle corrente, colocada pelo
middleware de sessão do Lack sob :LACK.SESSION no ambiente da requisição."
  (getf (lack/request:request-env ningle:*request*) :lack.session))

(defun session-put (table user-id role username)
  "Grava a identidade autenticada na sessão TABLE: identificador USER-ID, papel
ROLE (:agent ou :manager) e nome de usuário USERNAME. Retorna TABLE."
  (setf (gethash :user-id table) user-id
        (gethash :role table) role
        (gethash :username table) username)
  table)

(defun mark-session-for-id-rotation (env)
  "Marca no ambiente de requisição ENV (plist) a opção ':change-id' em
':lack.session.options', solicitando ao middleware de sessão do Lack a rotação do
identificador na próxima resposta. Puro sobre o plist: retorna T quando marcou, NIL quando
ENV não traz as opções de sessão. Isola a mutação do plist do acesso à API do Lack, à
maneira de SESSION-TABLE, de modo a ser testável sem servidor."
  (when (getf env :lack.session.options)
    (setf (getf (getf env :lack.session.options) :change-id) t)
    t))

(defun regenerate-session-id ()
  "Solicita ao middleware de sessão do Lack a rotação do identificador de sessão na próxima
resposta (ver MARK-SESSION-FOR-ID-ROTATION); os dados da sessão são preservados sob o novo
identificador. Fecha a janela de fixação de sessão na transição de privilégio (login), em
conformidade com o mandato de segurança do projeto. No-op quando não há requisição corrente,
como nos testes das funções núcleo sem servidor."
  (let ((request (and (boundp 'ningle:*request*) ningle:*request*)))
    (when request
      (mark-session-for-id-rotation (lack/request:request-env request)))))

(defun session-user (table)
  "Retorna, como valores múltiplos, o identificador, o papel e o nome de usuário
gravados na sessão TABLE, ou NIL quando a sessão não está autenticada."
  (let ((id (gethash :user-id table)))
    (when id
      (values id (gethash :role table) (gethash :username table)))))

(defun authenticated-p (table)
  "Retorna T quando a sessão TABLE contém uma identidade autenticada. Uma TABLE
nula (sessão ausente) resulta em NIL, mantendo o portão fail-closed."
  (and table (gethash :user-id table) t))

(defun session-role (table)
  "Retorna o papel gravado na sessão TABLE (:agent, :manager) ou NIL."
  (gethash :role table))

(defun session-clear (table)
  "Remove toda a identidade da sessão TABLE (logout). Retorna TABLE."
  (clrhash table)
  table)

(defun role-authorized-p (table role)
  "Retorna T quando a sessão TABLE está autenticada e o seu papel é ROLE. É o
portão de autorização por papel de cada aplicação."
  (and (authenticated-p table)
       (eq (session-role table) role)))
