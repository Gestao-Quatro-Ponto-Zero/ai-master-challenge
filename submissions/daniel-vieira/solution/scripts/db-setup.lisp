;;;; db-setup.lisp --- Provisiona o schema e a carga da persistencia (Fase B).
;;;;
;;;; Invocacao canonica:
;;;;   set -a; . ./.env; set +a
;;;;   qlot exec sbcl --non-interactive --load scripts/db-setup.lisp
;;;;
;;;; Carrega o sistema, estabelece a conexao ao PostgreSQL a partir das
;;;; variaveis de ambiente, aplica as migracoes numeradas, executa o seed a
;;;; partir dos CSV normalizados e verifica as contagens e a integridade. E
;;;; fail-closed: encerra com estado nao nulo quando qualquer etapa falha.

(require :asdf)
(asdf:load-system :leadscorer)

(handler-case
    (leadscorer:with-database
      (leadscorer:run-migrations)
      (leadscorer:seed-database)
      (leadscorer:verify-persistence)
      (uiop:quit 0))
  (error (condition)
    (format *error-output* "~&db-setup falhou: ~A~%" condition)
    (uiop:quit 1)))
