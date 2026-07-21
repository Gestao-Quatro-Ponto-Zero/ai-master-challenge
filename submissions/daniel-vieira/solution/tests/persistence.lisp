;;;; persistence.lisp --- Testes Parachute da camada de persistencia.
;;;;
;;;; Os testes de conversao e de derivacao sao puros e nao requerem banco. O
;;;; teste de integracao materializa o schema e a carga contra o PostgreSQL e e
;;;; ignorado quando o banco nao esta acessivel ou os CSV normalizados estao
;;;; ausentes, de modo que a suite passe em um ambiente sem banco.

(in-package #:leadscorer/tests)

(defun make-pipeline-row (&rest fields)
  "Constroi uma linha de pipeline como alist a partir de FIELDS, uma lista
alternada de nome de coluna e valor."
  (loop for (name value) on fields by #'cddr collect (cons name value)))

(define-test derive-username-from-name
  (is string= "anna.snelling" (leadscorer::derive-username "Anna Snelling"))
  (is string= "dustin.brinkmann" (leadscorer::derive-username "Dustin Brinkmann"))
  ;; Caracteres fora de [a-z0-9.] (apostrofo, hifen) sao removidos, sem virar
  ;; ponto; apenas o espaco vira ponto. A caixa e normalizada e as bordas sao
  ;; aparadas.
  (is string= "ohare" (leadscorer::derive-username "O'Hare"))
  (is string= "jeanluc" (leadscorer::derive-username "  Jean-Luc  ")))

(define-test decimal-rational-is-exact
  ;; A conversao decimal e racional exata, sem ponto flutuante.
  (is eql 110004/100 (leadscorer::parse-decimal-rational "1100.04"))
  (is eql 525/10 (leadscorer::parse-decimal-rational "52.5"))
  (is eql 42 (leadscorer::parse-decimal-rational "42"))
  (true (rationalp (leadscorer::parse-decimal-rational "1100.04")))
  (is eql nil (leadscorer::parse-decimal-rational "")))

(define-test money-conversion-to-cents
  ;; Milhoes de USD para centavos: valor x 10^8, exato.
  (is eql 110004000000 (leadscorer::cents-from-millions "1100.04"))
  (is eql 5250000000 (leadscorer::cents-from-millions "52.5"))
  ;; Unidade inteira de USD para centavos: valor x 100.
  (is eql 55000 (leadscorer::cents-from-units "550"))
  (is eql 0 (leadscorer::cents-from-units "0"))
  (is eql nil (leadscorer::cents-from-units ""))
  ;; O resultado e sempre inteiro (nunca ponto flutuante).
  (true (integerp (leadscorer::cents-from-millions "1100.04"))))

(define-test date-to-unix-ms-utc
  ;; 1970-01-01 UTC e a epoca UNIX (zero milissegundos).
  (is eql 0 (leadscorer::date->unix-ms "1970-01-01"))
  ;; 2016-10-20 UTC a meia-noite.
  (is eql 1476921600000 (leadscorer::date->unix-ms "2016-10-20"))
  ;; Data em branco (ciclo aberto) resulta em NIL.
  (is eql nil (leadscorer::date->unix-ms ""))
  (is eql nil (leadscorer::date->unix-ms "   ")))

(define-test sql-value-maps-nil-to-null
  ;; NIL vira :NULL (pois NIL codifica falso no Postmodern); os demais passam.
  (is eql :null (leadscorer::sql-value nil))
  (is eql 0 (leadscorer::sql-value 0))
  (is string= "x" (leadscorer::sql-value "x")))

(define-test split-sql-ignores-quoted-and-commented-semicolons
  (let ((statements
          (leadscorer::split-sql-statements
           "CREATE TABLE a (x INT); -- comentario; nao divide
            INSERT INTO a VALUES ('a;b');
            /* bloco; ainda nao */ SELECT 1;")))
    (is = 3 (length statements))
    ;; O ponto e virgula dentro do literal nao dividiu a instrucao (o comentario
    ;; de linha precedente permanece anexado, o que e inocuo na execucao).
    (true (search "INSERT INTO a VALUES ('a;b')" (second statements))))
  ;; O ponto e virgula dentro de um identificador entre aspas duplas tambem nao
  ;; divide a instrucao.
  (let ((statements
          (leadscorer::split-sql-statements "SELECT 1; SELECT \"a;b\" FROM t;")))
    (is = 2 (length statements))))

(define-test choose-open-cycle-tie-break
  ;; Entre ciclos abertos, escolhe-se o de engage_date mais recente.
  (let ((recent (make-pipeline-row "deal_stage" "Engaging"
                                   "engage_date" "2017-05-01"
                                   "opportunity_id" "B"))
        (older (make-pipeline-row "deal_stage" "Engaging"
                                  "engage_date" "2017-01-01"
                                  "opportunity_id" "A"))
        (closed (make-pipeline-row "deal_stage" "Won"
                                   "engage_date" "2017-06-01"
                                   "opportunity_id" "C")))
    (is equal recent (leadscorer::choose-open-cycle (list older recent closed)))
    ;; Sem ciclo aberto, retorna NIL.
    (is eql nil (leadscorer::choose-open-cycle (list closed))))
  ;; Empate na data e resolvido pelo opportunity_id em ordem crescente.
  (let ((first-id (make-pipeline-row "deal_stage" "Engaging"
                                     "engage_date" "2017-05-01"
                                     "opportunity_id" "A"))
        (second-id (make-pipeline-row "deal_stage" "Engaging"
                                      "engage_date" "2017-05-01"
                                      "opportunity_id" "B")))
    (is equal first-id (leadscorer::choose-open-cycle (list second-id first-id))))
  ;; Um ciclo aberto sem engage_date nao quebra o comparador; o ciclo datado
  ;; prevalece sobre o sem data.
  (let ((dated (make-pipeline-row "deal_stage" "Engaging"
                                  "engage_date" "2017-03-01"
                                  "opportunity_id" "A"))
        (blank (make-pipeline-row "deal_stage" "Engaging"
                                  "engage_date" ""
                                  "opportunity_id" "B")))
    (is equal dated (leadscorer::choose-open-cycle (list blank dated))))
  ;; Dois ciclos abertos sem data desempatam pelo opportunity_id.
  (let ((blank-a (make-pipeline-row "deal_stage" "Engaging"
                                    "engage_date" ""
                                    "opportunity_id" "A"))
        (blank-b (make-pipeline-row "deal_stage" "Engaging"
                                    "engage_date" ""
                                    "opportunity_id" "B")))
    (is equal blank-a (leadscorer::choose-open-cycle (list blank-b blank-a)))))

(define-test seed-integration-materializes-canonical-counts
  ;; Requer PostgreSQL acessivel e os CSV normalizados presentes; caso
  ;; contrario, o teste e deliberadamente ignorado para nao falhar sem banco.
  (if (and (leadscorer::database-reachable-p)
           (probe-file (merge-pathnames "accounts.csv" leadscorer::*data-directory*)))
      (leadscorer:with-database
        (leadscorer:run-migrations)
        (leadscorer:seed-database)
        (true (leadscorer:verify-persistence))
        (is = 530 (leadscorer::scalar "SELECT COUNT(*) FROM opportunities"))
        (is = 7212 (leadscorer::scalar "SELECT COUNT(*) FROM engagements"))
        (is = 0 (leadscorer::scalar "SELECT COUNT(*) FROM opportunity_scores"))
        ;; Com a carga presente, o predicado do provisionamento acusa banco ja
        ;; semeado. A transacao abortada exercita o ramo do banco vazio sem
        ;; poluir a base compartilhada: o TRUNCATE e revertido no rollback.
        (true (leadscorer:database-seeded-p))
        (postmodern:with-transaction (probe)
          (postmodern:execute "TRUNCATE regional_offices RESTART IDENTITY CASCADE")
          (false (leadscorer:database-seeded-p))
          (postmodern:abort-transaction probe))
        ;; A alteracao de uma migracao ja aplicada e detectada pelo checksum.
        (let* ((file (first (leadscorer::migration-files)))
               (version (leadscorer::migration-version file))
               (real (leadscorer::content-checksum (uiop:read-file-string file))))
          ;; A adulteracao e a restauracao correm sob UNWIND-PROTECT: o checksum
          ;; real e sempre restaurado, mesmo se uma assercao sinalizar, para nao
          ;; envenenar schema_migrations na base compartilhada.
          (unwind-protect
               (progn
                 (postmodern:execute
                  "UPDATE schema_migrations SET checksum = $1 WHERE version = $2"
                  "adulterado" version)
                 (fail (leadscorer:run-migrations)))
            (postmodern:execute
             "UPDATE schema_migrations SET checksum = $1 WHERE version = $2"
             real version))
          ;; Com o checksum restaurado, a reexecucao conclui sem erro (lista
          ;; vazia, pois nada novo ha a aplicar).
          (finish (leadscorer:run-migrations))))
      (skip "PostgreSQL ou dados indisponiveis; teste de integracao ignorado.")))

(define-test connect-with-retry-distingue-transitorio-de-permanente
  ;; Requer PostgreSQL acessivel: o ramo permanente e exercitado por uma senha
  ;; invalida contra o host real (resposta 28P01), e o transitorio por uma porta
  ;; fechada (socket recusado). Sem banco, o teste e ignorado.
  (if (leadscorer::database-reachable-p)
      (let ((leadscorer::*db-connect-retries* 3)
            (leadscorer::*db-connect-retry-delay* 0))
        (destructuring-bind (db user pass host &rest kw)
            (leadscorer::database-connection-spec)
          (declare (ignore pass))
          ;; (a) Erro permanente (credencial invalida): falha de imediato, com a
          ;; mensagem de falha permanente, sem exaurir as tentativas.
          (let* ((bad-cred (list* db user "credencial-definitivamente-invalida" host kw))
                 (msg (handler-case
                          (progn (leadscorer::connect-with-retry bad-cred)
                                 "conectou-inesperadamente")
                        (error (c) (princ-to-string c)))))
            (true (search "permanente" msg))
            (false (search "tentativas" msg)))
          ;; (b) Erro transitorio (socket recusado numa porta fechada): retenta ate
          ;; o limite e falha com a mensagem de tentativas exauridas, confirmando que
          ;; o socket-error continua sendo retentado.
          (let* ((closed-port (list db user "qualquer" host :port 59999))
                 (msg (handler-case
                          (progn (leadscorer::connect-with-retry closed-port)
                                 "conectou-inesperadamente")
                        (error (c) (princ-to-string c)))))
            (true (search "tentativas" msg))
            (false (search "permanente" msg)))))
      (skip "PostgreSQL indisponivel; teste de retry ignorado.")))

(define-test transient-connect-error-classifica-socket-e-inicializacao
  ;; Guarda estrutural, independente de dados e de banco, do tipo
  ;; TRANSIENT-CONNECT-ERROR, a fonte unica de verdade da classificacao de
  ;; retentativa em CONNECT-WITH-RETRY. Cobre a fase de inicializacao (SQLSTATE
  ;; 57P03), impraticavel de reproduzir deterministicamente contra um banco real:
  ;; se alguem removesse CANNOT-CONNECT-NOW do tipo, o FATAL "starting up"
  ;; recairia no ramo permanente e a tolerancia a subida do container (ADR D4M3)
  ;; regrediria; esta assercao falharia, ao contrario dos testes comportamentais.
  (true (subtypep 'cl-postgres:database-socket-error
                  'leadscorer::transient-connect-error))
  (true (subtypep 'cl-postgres-error:cannot-connect-now
                  'leadscorer::transient-connect-error))
  ;; O erro base do servidor (e, portanto, os permanentes como credencial
  ;; invalida) nao e transitorio.
  (false (subtypep 'cl-postgres:database-error
                   'leadscorer::transient-connect-error)))
