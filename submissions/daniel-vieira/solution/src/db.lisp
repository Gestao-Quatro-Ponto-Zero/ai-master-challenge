;;;; db.lisp --- Conexao com o PostgreSQL via Postmodern.
;;;;
;;;; Le a especificacao de conexao das variaveis de ambiente e provê a forma
;;;; WITH-DATABASE, que tolera a ordem de subida do container (ADR D4M3)
;;;; retentando a conexao ate um limite antes de sinalizar erro.

(in-package #:leadscorer)

(defparameter *db-connect-retries* 60
  "Numero maximo de tentativas de conexao ao PostgreSQL antes de falhar. A janela
(retries x delay) cobre o primeiro arranque a frio do banco no compose, em que o
'initdb' faz o healthcheck reportar saude pelo socket antes de o TCP aceitar
conexoes; a app tolera essa ordem por retentativa, sem depender do compose (ADR
D4M3).")

(defparameter *db-connect-retry-delay* 1
  "Intervalo em segundos entre tentativas de conexao ao PostgreSQL.")

(defun database-connection-spec ()
  "Retorna a especificacao de conexao Postmodern a partir das variaveis de
ambiente PGDATABASE, PGUSER, PGPASSWORD, PGHOST e PGPORT. Sinaliza ERROR quando
uma variavel obrigatoria esta ausente. PGPORT assume 5432 quando omitida."
  (flet ((required (name)
           (let ((value (uiop:getenv name)))
             (if (and value (plusp (length value)))
                 value
                 (error "A variavel de ambiente ~A e obrigatoria para a conexao ao banco."
                        name)))))
    (list (required "PGDATABASE")
          (required "PGUSER")
          (required "PGPASSWORD")
          (required "PGHOST")
          :port (parse-integer (or (uiop:getenv "PGPORT") "5432")))))

(deftype transient-connect-error ()
  "Uma falha transitoria de estabelecimento de conexao ao PostgreSQL, que justifica
retentativa: socket recusado (CL-POSTGRES:DATABASE-SOCKET-ERROR, que envolve tambem
os erros de resolucao de nome e de stream do SBCL) ou a fase de inicializacao do
banco (SQLSTATE 57P03, CL-POSTGRES-ERROR:CANNOT-CONNECT-NOW). E a fonte unica de
verdade da classificacao de retentativa em CONNECT-WITH-RETRY: qualquer outra
subclasse de DATABASE-ERROR e permanente."
  '(or cl-postgres:database-socket-error
       cl-postgres-error:cannot-connect-now))

(defun connect-with-retry (spec)
  "Estabelece e retorna uma conexao ativa ao PostgreSQL sob SPEC, retentando ate
*DB-CONNECT-RETRIES* vezes espacadas por *DB-CONNECT-RETRY-DELAY* segundos, para
tolerar a ordem de subida do container (ADR D4M3). Apenas erros transitorios de
conexao sao retentados (socket recusado e a fase de inicializacao do banco); um
erro permanente, tal como credencial invalida ou base inexistente, sinaliza ERROR
de imediato, sem exaurir as tentativas. Sinaliza ERROR tambem quando o limite de
tentativas transitorias e excedido. A retentativa cobre apenas o estabelecimento
da conexao; uma vez conectada, os erros de uso posterior nao sao mascarados."
  (loop with attempt = 0 do
    (flet ((retry (condition)
             (incf attempt)
             (when (>= attempt *db-connect-retries*)
               (error "Falha ao conectar ao PostgreSQL apos ~D tentativas: ~A"
                      attempt condition))
             (format *error-output*
                     "~&PostgreSQL indisponivel (tentativa ~D/~D); nova tentativa em ~D s.~%"
                     attempt *db-connect-retries* *db-connect-retry-delay*)
             (sleep *db-connect-retry-delay*)))
      (handler-case
          (return (apply #'postmodern:connect spec))
        ;; Transitorios da subida do container (ADR D4M3), classificados por
        ;; TRANSIENT-CONNECT-ERROR: socket recusado e a fase FATAL "the database
        ;; system is starting up" (57P03). Ambos sao subclasses de DATABASE-ERROR,
        ;; logo esta clausula precede o ramo permanente. Refina a captura ampla
        ;; anterior de ERROR (ver Q7B3).
        (transient-connect-error (condition)
          (retry condition))
        ;; Qualquer outra resposta do servidor com SQLSTATE (credencial invalida,
        ;; base inexistente, etc.) e permanente e falha de imediato. Um desligamento
        ;; do servidor (SERVER-SHUTDOWN, 57P01/57P02) nao e uma subida e tambem cai
        ;; aqui, deliberadamente.
        (cl-postgres:database-error (condition)
          (error "Falha permanente ao conectar ao PostgreSQL: ~A" condition))))))

(defun call-with-database (thunk)
  "Estabelece uma unica conexao de trabalho ao PostgreSQL a partir do ambiente,
com retentativa do estabelecimento, e invoca THUNK com essa conexao ativa.
Desconecta ao final, mesmo diante de erro. Retorna o valor de THUNK. Ver
WITH-DATABASE."
  (let ((postmodern:*database* (connect-with-retry (database-connection-spec))))
    (unwind-protect
         (funcall thunk)
      (postmodern:disconnect postmodern:*database*))))

(defmacro with-database (&body body)
  "Avalia BODY com uma conexao ativa ao PostgreSQL estabelecida a partir das
variaveis de ambiente, com retentativa de conexao. O valor retornado e o da
ultima forma de BODY."
  `(call-with-database (lambda () ,@body)))

(defun database-reachable-p ()
  "Retorna T quando uma conexao ao PostgreSQL pode ser estabelecida a partir do
ambiente, em uma unica tentativa e sem retentativa. Retorna NIL diante de
qualquer erro, inclusive a ausencia das variaveis de ambiente. Util para
condicionar testes de integracao a disponibilidade do banco."
  (handler-case
      (progn (postmodern:with-connection (database-connection-spec)
               (postmodern:query "SELECT 1"))
             t)
    (error () nil)))

(defconstant +unix-epoch-universal-time+ 2208988800
  "Segundos entre a epoca do tempo universal de Common Lisp (1900-01-01) e a
epoca UNIX (1970-01-01), ambas em UTC.")

(defun now-unix-ms ()
  "Retorna o instante corrente como UNIX em milissegundos, UTC, com resolucao
de segundo."
  (* 1000 (- (get-universal-time) +unix-epoch-universal-time+)))
