;;;; migrate.lisp --- Runner idempotente de migracoes SQL numeradas.
;;;;
;;;; Aplica os arquivos 'db/migrations/NNNN_*.sql' em ordem numerica, cada um em
;;;; sua propria transacao, e registra a versao aplicada na tabela de controle
;;;; 'schema_migrations'. A reexecucao ignora as migracoes ja registradas, de
;;;; modo que a aplicacao a partir de um banco vazio seja idempotente. A
;;;; ausencia de uma biblioteca canonica madura para migracao motiva este
;;;; runner proprio (ADR D2K9).

(in-package #:leadscorer)

(defparameter *migrations-directory*
  (asdf:system-relative-pathname :leadscorer "db/migrations/")
  "Diretorio dos arquivos de migracao SQL numerados.")

(defun content-checksum (string)
  "Retorna o checksum FNV-1a de 64 bits de STRING como uma cadeia hexadecimal.
Usa-se um hash nao criptografico simples e deterministico para detectar a
alteracao de uma migracao ja aplicada, evitando uma dependencia de biblioteca
de hashing."
  (let ((hash 14695981039346656037)          ; offset basis FNV-1a 64 bits
        (prime 1099511628211)
        (mask (1- (expt 2 64))))
    (loop for octet across (babel-or-utf8-octets string)
          do (setf hash (logand (* (logxor hash octet) prime) mask)))
    (format nil "~(~16,'0X~)" hash)))

(defun babel-or-utf8-octets (string)
  "Retorna os octetos UTF-8 de STRING. Isola a conversao para um unico ponto."
  (sb-ext:string-to-octets string :external-format :utf-8))

(defun migration-files (&optional (directory *migrations-directory*))
  "Retorna a lista dos arquivos de migracao '*.sql' de DIRECTORY, ordenados pelo
nome, que codifica o prefixo numerico de ordem."
  (sort (directory (merge-pathnames "*.sql" directory))
        #'string< :key #'file-namestring))

(defun migration-version (file)
  "Retorna a versao de FILE, a saber, o nome do arquivo sem extensao."
  (pathname-name file))

(defun split-sql-statements (sql)
  "Divide SQL nas instrucoes individuais, quebrando nos pontos e virgula de
nivel superior e ignorando os que ocorrem em comentario de linha ('--'), em
comentario de bloco ('/* */'), em literal entre aspas simples, em identificador
entre aspas duplas ou em literal delimitado por cifrao ('$tag$...$tag$'). Em SQL
valido as aspas emparelham-se, de modo que um ponto e virgula entre a abertura e
o fechamento e sempre consumido. Retorna a lista das instrucoes nao
vazias, sem o ponto e virgula terminal. Necessario porque o protocolo estendido
do cl-postgres admite apenas uma instrucao por consulta."
  (let ((statements '())
        (start 0)
        (index 0)
        (length (length sql)))
    (labels ((peek (offset)
               (let ((position (+ index offset)))
                 (when (< position length) (char sql position))))
             (dollar-tag-end ()
               ;; Em INDEX ha um '$'; retorna o indice apos o delimitador de
               ;; abertura '$tag$', ou NIL quando nao ha delimitador valido.
               (let ((cursor (1+ index)))
                 (loop while (and (< cursor length)
                                  (let ((char (char sql cursor)))
                                    (or (alphanumericp char) (char= char #\_))))
                       do (incf cursor))
                 (when (and (< cursor length) (char= (char sql cursor) #\$))
                   (1+ cursor))))
             (collect-statement (end)
               (let ((statement (string-trim '(#\Space #\Tab #\Newline #\Return)
                                             (subseq sql start end))))
                 (when (plusp (length statement))
                   (push statement statements)))))
      (loop while (< index length) do
        (let ((char (char sql index)))
          (cond
            ((and (char= char #\-) (eql (peek 1) #\-))
             (loop while (and (< index length) (char/= (char sql index) #\Newline))
                   do (incf index)))
            ((and (char= char #\/) (eql (peek 1) #\*))
             (incf index 2)
             (loop while (and (< index length)
                              (not (and (char= (char sql index) #\*) (eql (peek 1) #\/))))
                   do (incf index))
             (incf index 2))
            ((char= char #\')
             (incf index)
             (loop while (and (< index length) (char/= (char sql index) #\'))
                   do (incf index))
             (incf index))
            ((char= char #\")
             (incf index)
             (loop while (and (< index length) (char/= (char sql index) #\"))
                   do (incf index))
             (incf index))
            ((char= char #\$)
             (let ((tag-end (dollar-tag-end)))
               (if tag-end
                   (let ((tag (subseq sql index tag-end)))
                     (setf index tag-end)
                     (let ((close (search tag sql :start2 index)))
                       (setf index (if close (+ close (length tag)) length))))
                   (incf index))))
            ((char= char #\;)
             (collect-statement index)
             (incf index)
             (setf start index))
            (t (incf index)))))
      (collect-statement length)
      (nreverse statements))))

(defun ensure-migrations-table ()
  "Cria a tabela de controle 'schema_migrations' quando ausente. Idempotente.
Verifica a existencia com 'to_regclass' antes de criar, evitando o aviso do
PostgreSQL emitido por 'CREATE TABLE IF NOT EXISTS' sobre uma tabela presente."
  (unless (postmodern:query
           "SELECT to_regclass('public.schema_migrations') IS NOT NULL" :single)
    (postmodern:execute
     "CREATE TABLE schema_migrations (
          version TEXT PRIMARY KEY,
          applied_at BIGINT NOT NULL,
          checksum TEXT NOT NULL)")))

(defun applied-migrations ()
  "Retorna uma tabela hash da versao de migracao ja registrada para o seu
checksum registrado."
  (let ((table (make-hash-table :test #'equal)))
    (loop for (version checksum)
            in (postmodern:query "SELECT version, checksum FROM schema_migrations")
          do (setf (gethash version table) checksum))
    table))

(defun apply-migration (version sql checksum)
  "Aplica a migracao de VERSION, cujo conteudo e SQL e cujo checksum e CHECKSUM,
em uma transacao, e registra a versao, o instante e o checksum em
'schema_migrations'. A migracao inteira e o registro compoem uma unidade
atomica."
  (postmodern:with-transaction ()
    ;; A migracao pode conter varias instrucoes; aplica-se cada uma
    ;; separadamente, pois o protocolo estendido admite apenas uma por vez.
    (dolist (statement (split-sql-statements sql))
      (cl-postgres:exec-query postmodern:*database* statement))
    (postmodern:query
     "INSERT INTO schema_migrations (version, applied_at, checksum)
      VALUES ($1, $2, $3)"
     version (now-unix-ms) checksum)))

(defun run-migrations (&optional (directory *migrations-directory*))
  "Aplica, em ordem, as migracoes de DIRECTORY ainda nao registradas em
'schema_migrations', assumindo uma conexao ativa (ver WITH-DATABASE). E
idempotente: as migracoes ja aplicadas sao ignoradas. Para uma migracao ja
aplicada, confere o checksum atual contra o registrado e sinaliza ERROR em
divergencia, detectando a alteracao de uma migracao ja aplicada. Retorna a lista
das versoes aplicadas nesta execucao."
  (ensure-migrations-table)
  (let ((applied (applied-migrations))
        (newly '()))
    (dolist (file (migration-files directory) (nreverse newly))
      (let* ((version (migration-version file))
             (sql (uiop:read-file-string file))
             (checksum (content-checksum sql))
             (recorded (gethash version applied)))
        (cond
          ((null recorded)
           (apply-migration version sql checksum)
           (push version newly)
           (format t "~&Migracao aplicada: ~A~%" version))
          ((string/= recorded checksum)
           (error "A migracao ~A ja aplicada foi alterada: checksum registrado ~
                   ~A, atual ~A."
                  version recorded checksum)))))))
