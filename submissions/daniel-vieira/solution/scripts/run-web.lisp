;;;; run-web.lisp --- Sobe as duas aplicações web para verificação manual.
;;;;
;;;; Invocação (a partir da raiz do projeto, com o PostgreSQL provisionado):
;;;;   set -a; . ./.env; set +a
;;;;   qlot exec sbcl --non-interactive --load scripts/run-web.lisp
;;;;
;;;; As portas são configuráveis por LEADSCORER_AGENT_PORT e
;;;; LEADSCORER_MANAGER_PORT (padrões 8081 e 8082). O login lê os usuários
;;;; semeados, de modo que o banco deve estar de pé e semeado. Encerre com
;;;; Ctrl-C (SIGINT) ou 'docker stop'/'podman stop' (SIGTERM), que param os dois
;;;; servidores de forma ordenada.

(require :asdf)

;;; Quando o processo parte de uma imagem de core com o sistema pre-carregado (o
;;; arranque do conteiner, ver 'scripts/container-entrypoint'), o pacote ja
;;; existe. Chamar 'asdf:load-system' nesse caso faria o ASDF re-verificar os
;;; stamps dos arquivos e, pela divergencia entre o ASDF embutido e o 'uiop'
;;; fixado, recompilar as dependencias no arranque. A guarda pula o carregamento
;;; quando o sistema ja esta presente, e o mantem para o uso em desenvolvimento
;;; sem core.
(unless (find-package '#:leadscorer/web)
  (asdf:load-system :leadscorer/web))

(defun shutdown-servers ()
  "Para os dois servidores de forma ordenada e encerra o processo com estado
nulo. Compartilhada pelos tratadores de SIGINT e de SIGTERM."
  (format t "~&Encerrando os servidores...~%")
  (finish-output)
  (leadscorer/web:stop)
  (uiop:quit 0))

;;; Encerramento ordenado em SIGTERM ('docker stop'/'podman stop'). Sem este
;;; tratador, o SBCL como PID 1 do conteiner ignoraria o SIGTERM e o runtime o
;;; encerraria por SIGKILL apos o periodo de graca, sem parar os servidores.
(sb-sys:enable-interrupt sb-unix:sigterm
                         (lambda (signal info context)
                           (declare (ignore signal info context))
                           (shutdown-servers)))

(multiple-value-bind (agent-port manager-port) (leadscorer/web:start)
  (format t "~&Aplicacao do agente:  http://127.0.0.1:~D/login~%" agent-port)
  (format t "Aplicacao do gerente: http://127.0.0.1:~D/login~%" manager-port)
  (format t "Ctrl-C ou 'docker stop' para encerrar.~%")
  (finish-output))

(handler-case
    (loop (sleep 60))
  (sb-sys:interactive-interrupt ()
    (shutdown-servers)))
