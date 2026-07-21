;;;; model.lisp --- Estruturas de dados e carga da base de modelagem.
;;;;
;;;; Lê os artefatos derivados em 'data/derived/' (gerados por
;;;; 'scripts/modeling.sql') em estruturas do domínio do scoring. As estruturas
;;;; e os carregadores residem aqui; o motor de scoring, em 'scoring.lisp'.

(in-package #:leadscorer)

(defun csv-field (alist name)
  "O valor da coluna NAME na linha ALIST, ou NIL quando a coluna está ausente."
  (cdr (assoc name alist :test #'string=)))

(defun parse-number-or-nil (string)
  "Converte STRING em um número, ou NIL quando STRING é nula ou vazia.

Vincula *READ-EVAL* a NIL e exige que o resultado seja um número, de modo que a
leitura não avalie formas arbitrárias. Sinaliza ERROR se STRING não for numérica."
  (when (and string (plusp (length string)))
    (let ((*read-eval* nil))
      (let ((value (read-from-string string)))
        (unless (numberp value)
          (error "Campo numérico inválido: ~S." string))
        value))))

(defun parse-integer-or-nil (string)
  "Converte STRING em um inteiro, ou NIL quando STRING é nula ou vazia. Reservado
aos campos inteiros, evitando o leitor genérico. Sinaliza ERROR se STRING não
representar um inteiro."
  (when (and string (plusp (length string)))
    (parse-integer string)))

(defstruct (pair (:copier nil))
  "Um par conta-produto candidato da lista de potenciais, com as features brutas
lidas de 'potentials_base.csv'. A dimensão econômica lê ECONOMIC-VALUE (ticket
médio com recuo por setor); LIST-PRICE é mantido como diagnóstico."
  (account "" :read-only t :type string)
  (sector "" :read-only t :type string)
  (product "" :read-only t :type string)
  (series "" :read-only t :type string)
  (list-price 0 :read-only t :type integer)
  (economic-value 0 :read-only t :type real)
  (last-close-value nil :read-only t)
  (cadence-days nil :read-only t)
  (won-count 0 :read-only t :type integer)
  (sector-avg 0 :read-only t :type real)
  (days-since nil :read-only t))

(defstruct (opportunity (:copier nil))
  "Uma oportunidade Engaging não expirada da lista de iniciadas, lida de
'initiated_base.csv'. A dimensão econômica lê ECONOMIC-VALUE; LIST-PRICE é
mantido como diagnóstico."
  (id "" :read-only t :type string)
  (account "" :read-only t :type string)
  (sector "" :read-only t :type string)
  (product "" :read-only t :type string)
  (agent "" :read-only t :type string)
  (list-price 0 :read-only t :type integer)
  (economic-value 0 :read-only t :type real)
  (won-count 0 :read-only t :type integer)
  (sector-avg 0 :read-only t :type real)
  (age 0 :read-only t :type integer))

(defun load-pairs (path)
  "Lê 'potentials_base.csv' em PATH e retorna uma lista de estruturas PAIR."
  (multiple-value-bind (header rows) (read-csv-file path)
    (mapcar (lambda (row)
              (make-pair
               :account (csv-field row "account")
               :sector (csv-field row "sector")
               :product (csv-field row "product")
               :series (csv-field row "series")
               :list-price (parse-integer-or-nil (csv-field row "list_price"))
               :economic-value (or (parse-number-or-nil (csv-field row "economic_value"))
                                   (parse-integer-or-nil (csv-field row "list_price")))
               :last-close-value (parse-integer-or-nil
                                  (csv-field row "last_close_value"))
               :cadence-days (parse-number-or-nil (csv-field row "cadence_days"))
               :won-count (parse-integer-or-nil (csv-field row "pair_won_count"))
               :sector-avg (parse-number-or-nil (csv-field row "sector_won_avg"))
               :days-since (parse-integer-or-nil
                            (csv-field row "days_since_last_close"))))
            (csv-rows->alists header rows))))

(defun load-opportunities (path)
  "Lê 'initiated_base.csv' em PATH e retorna uma lista de estruturas OPPORTUNITY."
  (multiple-value-bind (header rows) (read-csv-file path)
    (mapcar (lambda (row)
              (make-opportunity
               :id (csv-field row "opportunity_id")
               :account (csv-field row "account")
               :sector (csv-field row "sector")
               :product (csv-field row "product")
               :agent (csv-field row "sales_agent")
               :list-price (parse-integer-or-nil (csv-field row "list_price"))
               :economic-value (or (parse-number-or-nil (csv-field row "economic_value"))
                                   (parse-integer-or-nil (csv-field row "list_price")))
               :won-count (parse-integer-or-nil (csv-field row "pair_won_count"))
               :sector-avg (parse-number-or-nil (csv-field row "sector_won_avg"))
               :age (parse-integer-or-nil (csv-field row "engagement_age_days"))))
            (csv-rows->alists header rows))))

(defun load-adherence (path)
  "Lê 'adherence.csv' em PATH e retorna uma hash-table cuja chave é a lista
(AGENT PRODUCT) e cujo valor é a lista (WON-PRODUCT WON-SERIES)."
  (multiple-value-bind (header rows) (read-csv-file path)
    (let ((table (make-hash-table :test #'equal)))
      (dolist (row (csv-rows->alists header rows) table)
        (setf (gethash (list (csv-field row "sales_agent")
                             (csv-field row "product"))
                       table)
              (list (parse-integer-or-nil (csv-field row "won_product"))
                    (parse-integer-or-nil (csv-field row "won_series"))))))))

(defun load-decay (path)
  "Lê 'decay.csv' em PATH e retorna um vetor indexado pela idade em dias, cujo
elemento é a fração de vitória restante. Assume idades contíguas a partir de 0."
  (multiple-value-bind (header rows) (read-csv-file path)
    (let* ((alists (csv-rows->alists header rows))
           (vector (make-array (length alists) :initial-element 0.0)))
      (dolist (row alists vector)
        (setf (aref vector (parse-integer-or-nil (csv-field row "age_days")))
              (parse-number-or-nil (csv-field row "win_fraction")))))))
