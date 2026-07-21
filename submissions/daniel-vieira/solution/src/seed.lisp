;;;; seed.lisp --- Carga (seed) das tabelas a partir dos CSV normalizados.
;;;;
;;;; Materializa o grupo de referencia e o grupo do ciclo de engajamento a
;;;; partir de 'data/normalized/*.csv', aplicando as convencoes da casa: moeda
;;;; como inteiro na menor unidade com codigo ISO 4217, instantes UNIX em
;;;; milissegundos (UTC) e usernames derivados do nome. A oportunidade e o par
;;;; conta-produto; cada linha do pipeline e um ciclo em 'engagements'. Excluem-
;;;; se, com registro em log, as linhas sem conta e as em estagio Prospecting,
;;;; que nunca engajaram (decisao registrada no worklog da tarefa 9P4D).

(in-package #:leadscorer)

(defparameter *data-directory*
  (asdf:system-relative-pathname :leadscorer "data/normalized/")
  "Diretorio dos CSV normalizados que servem de fonte do seed.")

(defparameter *seed-currency* "USD"
  "Codigo ISO 4217 adotado por convencao, dado que a moeda do dataset e
indeterminada na fonte (ver 'docs/concepcao-inicial.md').")

;;; --- Conversoes puras (cobertas por testes unitarios) ---

(defun blankp (string)
  "Retorna T quando STRING e NIL ou contem apenas espacos em branco."
  (or (null string) (zerop (length (string-trim '(#\Space #\Tab) string)))))

(defun derive-username (name)
  "Deriva um username estavel de NAME: minusculas, espacos convertidos em ponto
e todo caractere fora de [a-z0-9.] removido. Ex.: \"Anna Snelling\" ->
\"anna.snelling\". A unicidade final e assegurada pelas restricoes UNIQUE do
schema."
  (with-output-to-string (out)
    (loop for char across (string-downcase (string-trim '(#\Space #\Tab) name))
          for c = (cond ((char= char #\Space) #\.)
                        ((or (char<= #\a char #\z) (char<= #\0 char #\9)
                             (char= char #\.)) char)
                        (t nil))
          when c do (write-char c out))))

(defun parse-decimal-rational (string)
  "Converte STRING decimal (ex.: \"1100.04\") em um numero racional exato, sem
recorrer a ponto flutuante. Retorna NIL para entrada em branco. Assume valor
nao negativo, como na fonte."
  (unless (blankp string)
    (let* ((s (string-trim '(#\Space #\Tab) string))
           (dot (position #\. s)))
      (if dot
          (let* ((int-part (subseq s 0 dot))
                 (frac-part (subseq s (1+ dot)))
                 (digits (length frac-part))
                 (int (if (plusp (length int-part)) (parse-integer int-part) 0))
                 (frac (if (plusp digits) (parse-integer frac-part) 0)))
            (+ int (/ frac (expt 10 digits))))
          (parse-integer s)))))

(defun cents-from-millions (string)
  "Converte STRING decimal em milhoes de USD para inteiro em centavos, exato
(x 10^8), com arredondamento half-to-even residual. Retorna NIL para branco."
  (let ((value (parse-decimal-rational string)))
    (when value (round (* value 100000000)))))

(defun cents-from-units (string)
  "Converte STRING inteiro em USD (unidade inteira) para inteiro em centavos
(x 100). Retorna NIL para branco."
  (let ((value (parse-integer-or-nil string)))
    (when value (* value 100))))

(defun date->unix-ms (string)
  "Converte STRING de data 'YYYY-MM-DD' para UNIX em milissegundos, UTC, no
instante de meia-noite. Retorna NIL para entrada em branco (ciclo aberto)."
  (unless (blankp string)
    (let ((s (string-trim '(#\Space #\Tab) string)))
      (let ((year (parse-integer s :start 0 :end 4))
            (month (parse-integer s :start 5 :end 7))
            (day (parse-integer s :start 8 :end 10)))
        (* 1000 (- (encode-universal-time 0 0 0 day month year 0)
                   +unix-epoch-universal-time+))))))

;;; --- Auxiliares de insercao ---

(defun sql-value (x)
  "Mapeia NIL de Common Lisp para o NULL de SQL (:NULL), preservando os demais
valores. Necessario porque, no Postmodern, NIL codifica o booleano falso, nao
NULL."
  (if (null x) :null x))

(defun read-normalized-csv (basename)
  "Le 'data/normalized/BASENAME' e retorna as linhas como uma lista de alists
'(coluna . valor)', reutilizando a API de CSV do sistema."
  (multiple-value-bind (header rows)
      (read-csv-file (merge-pathnames basename *data-directory*))
    (csv-rows->alists header rows)))

;;; --- Seed do grupo de referencia ---

(defun seed-regional-offices (team-rows)
  "Insere os escritorios regionais distintos de TEAM-ROWS. Retorna uma tabela
hash de nome de escritorio para id."
  (let ((office->id (make-hash-table :test #'equal)))
    (dolist (row team-rows office->id)
      (let ((office (csv-field row "regional_office")))
        (unless (or (blankp office) (gethash office office->id))
          (setf (gethash office office->id)
                (postmodern:query
                 "INSERT INTO regional_offices (name) VALUES ($1) RETURNING id"
                 office :single)))))))

(defun seed-sales-managers (team-rows office->id)
  "Insere os gerentes distintos de TEAM-ROWS, cada um com o seu escritorio.
Retorna uma tabela hash de nome de gerente para id."
  (let ((manager->id (make-hash-table :test #'equal)))
    (dolist (row team-rows manager->id)
      (let ((manager (csv-field row "manager"))
            (office (csv-field row "regional_office")))
        (unless (or (blankp manager) (gethash manager manager->id))
          (setf (gethash manager manager->id)
                (postmodern:query
                 "INSERT INTO sales_managers (name, username, regional_office_id)
                  VALUES ($1, $2, $3) RETURNING id"
                 manager (derive-username manager) (gethash office office->id)
                 :single)))))))

(defun seed-sales-agents (team-rows manager->id)
  "Insere os agentes de TEAM-ROWS, cada um sob o seu gerente. Retorna uma tabela
hash de nome de agente para id."
  (let ((agent->id (make-hash-table :test #'equal)))
    (dolist (row team-rows agent->id)
      (let ((agent (csv-field row "sales_agent"))
            (manager (csv-field row "manager")))
        (unless (or (blankp agent) (gethash agent agent->id))
          (setf (gethash agent agent->id)
                (postmodern:query
                 "INSERT INTO sales_agents (name, username, sales_manager_id)
                  VALUES ($1, $2, $3) RETURNING id"
                 agent (derive-username agent) (gethash manager manager->id)
                 :single)))))))

(defun seed-accounts (account-rows)
  "Insere as contas de ACCOUNT-ROWS em dois passos: primeiro sem a matriz e, em
seguida, resolvendo 'subsidiary_of' por nome. Retorna uma tabela hash de nome de
conta para id."
  (let ((account->id (make-hash-table :test #'equal)))
    (dolist (row account-rows)
      (let ((name (csv-field row "account")))
        (setf (gethash name account->id)
              (postmodern:query
               "INSERT INTO accounts
                    (name, sector, year_established, revenue_amount,
                     revenue_currency, employees, location)
                VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id"
               name
               (csv-field row "sector")
               (sql-value (parse-integer-or-nil (csv-field row "year_established")))
               ;; Coluna NOT NULL: SQL-VALUE mapeia um valor ausente para NULL,
               ;; produzindo violacao limpa da restricao em vez de codificar NIL
               ;; como o booleano falso do Postmodern.
               (sql-value (cents-from-millions (csv-field row "revenue")))
               *seed-currency*
               (sql-value (parse-integer-or-nil (csv-field row "employees")))
               (sql-value (csv-field row "office_location"))
               :single))))
    (dolist (row account-rows account->id)
      (let ((parent (csv-field row "subsidiary_of")))
        (unless (blankp parent)
          (postmodern:execute
           "UPDATE accounts SET subsidiary_of_id = $1 WHERE id = $2"
           ;; Uma matriz nao presente em accounts.csv resolve para NIL; SQL-VALUE
           ;; o mapeia para NULL (relacao ausente) em vez de codificar NIL como o
           ;; booleano falso do Postmodern, que abortaria com erro de tipo.
           (sql-value (gethash parent account->id))
           (gethash (csv-field row "account") account->id)))))))

(defun seed-products (product-rows)
  "Insere os produtos de PRODUCT-ROWS. Retorna uma tabela hash de nome de
produto para id."
  (let ((product->id (make-hash-table :test #'equal)))
    (dolist (row product-rows product->id)
      (let ((name (csv-field row "product")))
        (setf (gethash name product->id)
              (postmodern:query
               "INSERT INTO products
                    (name, series, list_price_amount, list_price_currency)
                VALUES ($1, $2, $3, $4) RETURNING id"
               name
               (csv-field row "series")
               ;; Coluna NOT NULL: ver a nota em SEED-ACCOUNTS.
               (sql-value (cents-from-units (csv-field row "sales_price")))
               *seed-currency*
               :single))))))

(defparameter *engagement-justifications*
  '(("disagreement" . "Discordancia da avaliacao da oportunidade")
    ("direct-inquiry" . "Consulta direta do cliente sobre o produto")
    ("other" . "Outro motivo"))
  "As tres justificativas de engajamento fora do top tier, conforme
'docs/concepcao-inicial.md'.")

(defun seed-justifications ()
  "Insere as tres justificativas de engajamento."
  (dolist (entry *engagement-justifications*)
    (postmodern:execute
     "INSERT INTO engagement_justifications (code, description) VALUES ($1, $2)"
     (car entry) (cdr entry))))

;;; --- Seed do grupo do ciclo de engajamento ---

(defun pair-key (account product)
  "Retorna a chave de igualdade do par conta-produto."
  (list account product))

(defun engagement-row-p (row)
  "Retorna T quando ROW e um ciclo de engajamento, a saber, tem conta e esta em
estagio Won, Lost ou Engaging. As linhas Prospecting e as sem conta sao
excluidas."
  (and (not (blankp (csv-field row "account")))
       (member (csv-field row "deal_stage") '("Won" "Lost" "Engaging")
               :test #'string=)))

(defun open-cycle-p (row)
  "Retorna T quando ROW e um ciclo aberto (estagio Engaging)."
  (string= (csv-field row "deal_stage") "Engaging"))

(defun choose-open-cycle (rows)
  "Dentre ROWS (ciclos de um mesmo par), retorna o ciclo aberto corrente: o de
'engage_date' mais recente, desempatando pelo 'opportunity_id' de proveniencia
em ordem crescente, de modo deterministico. Um ciclo aberto sem 'engage_date'
ordena como o menos recente, atras de qualquer ciclo datado. Retorna NIL quando
nao ha ciclo aberto."
  (let ((open (remove-if-not #'open-cycle-p rows)))
    (when open
      (first (sort (copy-list open)
                   (lambda (a b)
                     (let ((da (date->unix-ms (csv-field a "engage_date")))
                           (db (date->unix-ms (csv-field b "engage_date"))))
                       (cond ((and da db (/= da db)) (> da db))
                             ;; Data ausente ordena atras de uma data presente.
                             ((and da (null db)) t)
                             ((and (null da) db) nil)
                             ;; Datas iguais ou ambas ausentes: desempate pelo id.
                             (t (string< (csv-field a "opportunity_id")
                                         (csv-field b "opportunity_id")))))))))))

(defun opportunity-created-at (rows)
  "Retorna o instante de criacao do par: o menor 'engage_date' entre os seus
ciclos, ou o instante corrente quando nenhum ciclo possui data de engajamento."
  (let ((instants (loop for row in rows
                        for ms = (date->unix-ms (csv-field row "engage_date"))
                        when ms collect ms)))
    (if instants (reduce #'min instants) (now-unix-ms))))

(defun seed-opportunities (pipeline-rows account->id product->id agent->id)
  "Materializa 'opportunities' como os pares distintos conta-produto das linhas
com conta (todos os estagios). Deriva o estado ativo: 'engaging' quando o par
tem ciclo aberto, senao 'prospecting'. Retorna uma tabela hash de chave de par
para id de oportunidade."
  (let ((by-pair (make-hash-table :test #'equal))
        (pair->id (make-hash-table :test #'equal)))
    ;; Agrupa as linhas com conta por par conta-produto.
    (dolist (row pipeline-rows)
      (unless (blankp (csv-field row "account"))
        (let ((key (pair-key (csv-field row "account") (csv-field row "product"))))
          (push row (gethash key by-pair)))))
    (maphash
     (lambda (key rows)
       (let* ((account (first key))
              (product (second key))
              (cycles (remove-if-not #'engagement-row-p rows))
              (open (choose-open-cycle cycles))
              (status (if open "engaging" "prospecting"))
              (engaged-by (when open
                            (gethash (csv-field open "sales_agent") agent->id)))
              (engaged-at (when open
                            (date->unix-ms (csv-field open "engage_date")))))
         (setf (gethash key pair->id)
               (postmodern:query
                "INSERT INTO opportunities
                     (account_id, product_id, status, engaged_by_id,
                      engaged_at, created_at)
                 VALUES ($1, $2, $3, $4, $5, $6) RETURNING id"
                (gethash account account->id)
                (gethash product product->id)
                status
                (sql-value engaged-by)
                (sql-value engaged-at)
                (opportunity-created-at cycles)
                :single))))
     by-pair)
    pair->id))

(defun seed-engagements (pipeline-rows pair->id agent->id)
  "Insere um registro em 'engagements' para cada ciclo (linha Won, Lost ou
Engaging com conta). Converte datas e valores conforme as convencoes da casa; a
justificativa historica e nula (atribuida em tempo de execucao)."
  (dolist (row pipeline-rows)
    (when (engagement-row-p row)
      (let* ((stage (csv-field row "deal_stage"))
             (key (pair-key (csv-field row "account") (csv-field row "product")))
             (closed-at (date->unix-ms (csv-field row "close_date")))
             (outcome (cond ((string= stage "Won") "won")
                            ((string= stage "Lost") "lost")
                            (t nil)))
             (close-cents (cents-from-units (csv-field row "close_value"))))
        (postmodern:execute
         "INSERT INTO engagements
              (opportunity_id, sales_agent_id, engaged_at, closed_at, outcome,
               expired, close_value_amount, close_value_currency,
               source_opportunity_id)
          VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)"
         (gethash key pair->id)
         ;; Colunas NOT NULL: SQL-VALUE mapeia um agente nao encontrado ou uma
         ;; data em branco para NULL, produzindo violacao limpa da restricao em
         ;; vez de codificar NIL como o booleano falso do Postmodern.
         (sql-value (gethash (csv-field row "sales_agent") agent->id))
         (sql-value (date->unix-ms (csv-field row "engage_date")))
         (sql-value closed-at)
         (sql-value outcome)
         nil                            ; expired: falso para o historico
         (sql-value close-cents)
         (sql-value (when close-cents *seed-currency*))
         (csv-field row "opportunity_id"))))))

;;; --- Orquestracao ---

(defun seed-database ()
  "Carrega todas as tabelas a partir dos CSV normalizados, assumindo uma conexao
ativa (ver WITH-DATABASE). Idempotente: trunca e recarrega as tabelas em uma
unica transacao, reiniciando as identidades. Registra em log o total de linhas
do pipeline excluidas (Prospecting e sem conta). Retorna T."
  (let ((team-rows (read-normalized-csv "sales_teams.csv"))
        (account-rows (read-normalized-csv "accounts.csv"))
        (product-rows (read-normalized-csv "products.csv"))
        (pipeline-rows (read-normalized-csv "sales_pipeline.csv")))
    (postmodern:with-transaction ()
      (postmodern:execute
       "TRUNCATE engagements, opportunity_scores, opportunities,
                 engagement_justifications, sales_agents, sales_managers,
                 regional_offices, accounts, products
        RESTART IDENTITY CASCADE")
      (let* ((office->id (seed-regional-offices team-rows))
             (manager->id (seed-sales-managers team-rows office->id))
             (agent->id (seed-sales-agents team-rows manager->id))
             (account->id (seed-accounts account-rows))
             (product->id (seed-products product-rows)))
        (seed-justifications)
        (let ((pair->id (seed-opportunities pipeline-rows account->id
                                            product->id agent->id)))
          (seed-engagements pipeline-rows pair->id agent->id))))
    (let ((excluded (count-if-not #'engagement-row-p pipeline-rows)))
      (format t "~&Seed concluido. Linhas do pipeline excluidas (em Prospecting ~
                 ou sem conta): ~D de ~D.~%"
              excluded (length pipeline-rows)))
    t))

(defun database-seeded-p ()
  "Retorna T quando o banco ja contem a carga de referencia, detectada pela
presenca de ao menos uma linha em 'regional_offices', a primeira tabela semeada.
Assume o schema ja migrado e uma conexao ativa. Serve ao provisionamento
conteinerizado, que semeia apenas o banco vazio para preservar entre reinicios
os dados que a aplicacao produz por escrita."
  (postmodern:query "SELECT EXISTS (SELECT 1 FROM regional_offices)" :single))
