;;;; container-provision.lisp --- Provisiona a persistencia no conteiner.
;;;;
;;;; Invocado pelo entrypoint do conteiner antes de subir os servidores web.
;;;; Difere de 'db-setup.lisp' (ferramenta de desenvolvimento) por ser idempotente
;;;; sobre um volume persistido: aplica sempre as migracoes (idempotentes) e
;;;; semeia apenas o banco vazio, preservando entre reinicios os dados que a
;;;; aplicacao produz por escrita. A verificacao de contagens canonicas so vale
;;;; logo apos o seed, de modo que e executada apenas quando o seed ocorre; num
;;;; reinicio de banco ja semeado, as contagens ja divergem pela atividade da
;;;; aplicacao e a verificacao seria indevida.
;;;;
;;;; E fail-closed: encerra com estado nao nulo quando qualquer etapa falha. A
;;;; espera pela subida do banco e coberta pela retentativa de conexao de
;;;; WITH-DATABASE (ver 'src/db.lisp', ADR D4M3).

(require :asdf)
;;; Guarda o carregamento para o arranque a partir do core: quando o pacote ja
;;; existe (sistema pre-carregado no core), pular 'asdf:load-system' evita a
;;; re-verificacao de stamps do ASDF e a consequente recompilacao no arranque.
(unless (find-package '#:leadscorer)
  (asdf:load-system :leadscorer))

(handler-case
    (leadscorer:with-database
      (leadscorer:run-migrations)
      (if (leadscorer:database-seeded-p)
          (format t "~&Banco ja semeado; seed e verificacao ignorados.~%")
          (progn
            (leadscorer:seed-database)
            (leadscorer:verify-persistence)))
      (uiop:quit 0))
  (error (condition)
    (format *error-output* "~&Provisionamento do conteiner falhou: ~A~%" condition)
    (uiop:quit 1)))
