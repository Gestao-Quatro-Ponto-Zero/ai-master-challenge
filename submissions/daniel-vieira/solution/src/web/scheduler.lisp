;;;; scheduler.lisp --- Agendador de fundo dos servicos de ciclo.
;;;;
;;;; Sobe um unico thread 'sb-thread' que, a cada intervalo, executa um tick do
;;;; ciclo ('ls:run-cycle-tick') sob uma conexao propria. O thread e ancorado no
;;;; ciclo de vida do servidor ('start'/'stop'). Um unico thread sequencial
;;;; executa os tres servicos por tick, o que dispensa travas. Se os CSV
;;;; derivados do modelo estiverem ausentes, o agendador nao sobe e o servidor web
;;;; segue servindo.

(in-package #:leadscorer/web)

(defvar *scheduler-thread* nil
  "O thread de fundo do agendador em execucao, ou NIL quando parado.")

(defvar *scheduler-semaphore* nil
  "Semaforo de parada: sinaliza-lo acorda o laço para encerrar de imediato.")

(defvar *scheduler-model* nil
  "O modelo de scoring carregado uma vez no start, insumo dos ticks.")

(defun scheduler-running-p ()
  "Verdadeiro quando o thread do agendador existe e esta vivo."
  (and *scheduler-thread* (sb-thread:thread-alive-p *scheduler-thread*)))

(defun scheduler-loop (model interval-ms semaphore)
  "Laço do agendador: executa um tick do ciclo sob uma conexao propria e aguarda
INTERVAL-MS, ate SEMAPHORE ser sinalizado, quando encerra. Um erro de tick e
registrado em '*ERROR-OUTPUT*' e nao encerra o laço."
  (loop
    (handler-case
        (ls:with-database (ls:run-cycle-tick model))
      (error (condition)
        (format *error-output* "~&Tick do ciclo falhou: ~A~%" condition)))
    (when (sb-thread:wait-on-semaphore semaphore :timeout (/ interval-ms 1000.0))
      (return))))

(defun start-scheduler ()
  "Inicia o agendador do ciclo, se ainda nao estiver em execucao. Aplica a
configuracao, ancora o relogio virtual no instante real corrente, carrega o modelo
de scoring e sobe um thread de fundo que executa um tick a cada intervalo. Qualquer
falha (configuracao invalida ou CSV derivados ausentes) e registrada e NAO propaga:
o servidor web segue servindo sem o agendador. Retorna T quando iniciado, NIL caso
contrario."
  (when (scheduler-running-p)
    (return-from start-scheduler nil))
  (handler-case
      (progn
        (ls:load-config)
        (setf ls:*virtual-t0* (ls:now-unix-ms))
        (let ((model (ls:load-model)))
          (setf *scheduler-model* model
                *scheduler-semaphore* (sb-thread:make-semaphore
                                       :name "leadscorer-cycle")
                *scheduler-thread*
                (sb-thread:make-thread
                 (lambda ()
                   (scheduler-loop model (ls:ranking-interval-ms)
                                   *scheduler-semaphore*))
                 :name "leadscorer-scheduler"))
          t))
    (error (condition)
      (format *error-output*
              "~&Agendador do ciclo nao iniciado: ~A~%" condition)
      nil)))

(defun stop-scheduler ()
  "Para o agendador do ciclo, se em execucao, sinalizando o semaforo e aguardando o
thread encerrar. Zera o estado. Idempotente."
  (when (scheduler-running-p)
    (sb-thread:signal-semaphore *scheduler-semaphore*)
    (sb-thread:join-thread *scheduler-thread*))
  (setf *scheduler-thread* nil
        *scheduler-semaphore* nil
        *scheduler-model* nil)
  (values))
