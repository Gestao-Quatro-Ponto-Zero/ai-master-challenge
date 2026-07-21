;;;; verify-dataset.lisp --- Verificação de integridade dos CSV do dataset CRM.
;;;;
;;;; Executar a partir da raiz do projeto com:
;;;;   qlot exec sbcl --non-interactive --load scripts/verify-dataset.lisp
;;;;
;;;; Para cada arquivo esperado em 'data/', confere o cabeçalho completo e a
;;;; contagem de registros contra os valores canônicos confirmados, e encerra
;;;; com estado não nulo (fail-closed) se algum arquivo divergir ou estiver
;;;; ausente. Todos os arquivos são avaliados antes do desfecho, de modo que um
;;;; arquivo ausente ou divergente não impede o diagnóstico dos demais.

(asdf:load-system :leadscorer)

(defpackage #:leadscorer/verify-dataset
  (:use #:cl))

(in-package #:leadscorer/verify-dataset)

(defparameter *expected*
  '(("accounts.csv"
     ("account" "sector" "year_established" "revenue" "employees"
      "office_location" "subsidiary_of")
     85)
    ("products.csv"
     ("product" "series" "sales_price")
     7)
    ("sales_teams.csv"
     ("sales_agent" "manager" "regional_office")
     35)
    ("sales_pipeline.csv"
     ("opportunity_id" "sales_agent" "product" "account" "deal_stage"
      "engage_date" "close_date" "close_value")
     8800))
  "Especificação de verificação: para cada arquivo, o cabeçalho completo
esperado e a contagem de registros canônica confirmada do dataset CRM Sales
Predictive Analytics. Estes valores são a linha de base de integridade; uma
divergência sinaliza corrupção, versão diferente ou parse incorreto.")

(defun non-empty-row-p (row)
  "Retorna verdadeiro se ROW, uma lista de campos, possui ao menos um campo não
vazio. Serve para ignorar uma eventual linha vazia final produzida por um
arquivo terminado em quebra de linha."
  (some (lambda (field) (plusp (length field))) row))

(defun verify-one (spec)
  "Verifica um arquivo conforme SPEC, uma lista (ARQUIVO CABECALHO CONTAGEM).

Lê o arquivo em 'data/', confere se o cabeçalho iguala CABECALHO e se o número
de linhas não vazias iguala CONTAGEM. Reporta o resultado na saída padrão e
retorna T quando conforme e NIL caso contrário. Um arquivo ausente ou vazio é
reportado como falha em vez de abortar a verificação dos demais."
  (destructuring-bind (file expected-header expected-count) spec
    (let ((path (uiop:subpathname
                 (asdf:system-relative-pathname :leadscorer "data/") file)))
      (handler-case
          (multiple-value-bind (header rows) (leadscorer:read-csv-file path)
            (let* ((data-rows (count-if #'non-empty-row-p rows))
                   (header-ok (equal header expected-header))
                   (count-ok (= data-rows expected-count))
                   (ok (and header-ok count-ok)))
              (format t "~&[~:[FALHA~; OK  ~]] ~A: ~D registros (esperado ~D); ~
                         cabecalho ~:[DIVERGE~;conforme~].~%"
                      ok file data-rows expected-count header-ok)
              ok))
        ((or file-error leadscorer:empty-csv-file) (condition)
          (format t "~&[FALHA] ~A: nao foi possivel ler (~A).~%" file condition)
          nil)))))

(defun run ()
  "Verifica todos os arquivos de *EXPECTED*, reporta cada um e encerra o
processo com estado nulo quando todos estão conformes e não nulo caso
contrário. Avalia todos antes de decidir, sem curto-circuito."
  (let* ((results (mapcar #'verify-one *expected*))
         (all-ok (every #'identity results)))
    (format t "~%Resultado: ~:[HA DIVERGENCIAS~;todos os arquivos conformes~].~%"
            all-ok)
    (uiop:quit (if all-ok 0 1))))

(run)
