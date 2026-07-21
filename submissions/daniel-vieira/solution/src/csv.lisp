;;;; csv.lisp --- Leitura genérica de arquivos CSV.
;;;;
;;;; Provê a leitura de arquivos CSV com linha de cabeçalho em estruturas de
;;;; dados Lisp genéricas. As estruturas de domínio específicas (contas,
;;;; produtos, agentes, oportunidades) são definidas nas tarefas de modelagem;
;;;; aqui reside apenas a leitura genérica, reutilizável por todas elas.

(in-package #:leadscorer)

(define-condition empty-csv-file (error)
  ((path :initarg :path :reader empty-csv-file-path
         :documentation "O caminho do arquivo CSV que se revelou vazio."))
  (:report (lambda (condition stream)
             (format stream "O arquivo CSV ~A está vazio."
                     (empty-csv-file-path condition))))
  (:documentation
   "Sinalizada por READ-CSV-FILE quando o arquivo lido não contém nenhuma linha."))

(defun read-csv-file (path)
  "Lê o arquivo CSV em PATH, cuja primeira linha é tomada como o cabeçalho.

Retorna dois valores: a lista de nomes de coluna do cabeçalho, como cadeias, e
a lista das linhas de dados, cada uma como uma lista de cadeias na ordem do
cabeçalho. Sinaliza a condição EMPTY-CSV-FILE se o arquivo não contiver
nenhuma linha. Assume campos separados por vírgula e codificação UTF-8."
  (let ((rows (fare-csv:read-csv-file (pathname path))))
    (when (null rows)
      (error 'empty-csv-file :path path))
    (values (first rows) (rest rows))))

(defun csv-rows->alists (header rows)
  "Combina HEADER e ROWS em uma lista de alists, um por linha.

HEADER é uma lista de nomes de coluna e ROWS é uma lista de linhas, cada uma
uma lista de valores na ordem do cabeçalho, conforme retornado por
READ-CSV-FILE. Retorna uma lista de alists que mapeiam cada nome de coluna ao
valor correspondente da linha. Assume que cada linha possui o mesmo número de
campos que o cabeçalho; o emparelhamento cessa no menor dentre os dois."
  (mapcar (lambda (row)
            (mapcar #'cons header row))
          rows))

(defun quote-csv-field (value)
  "A representação CSV de VALUE: a cadeia de PRINC-TO-STRING, entre aspas e com as
aspas internas duplicadas quando o valor contém vírgula, aspas ou quebra de linha,
conforme a RFC 4180."
  (let ((string (princ-to-string value)))
    (if (find-if (lambda (character)
                   (member character '(#\, #\" #\Newline #\Return)))
                 string)
        (with-output-to-string (out)
          (write-char #\" out)
          (loop for character across string
                do (when (char= character #\") (write-char #\" out))
                   (write-char character out))
          (write-char #\" out))
        string)))

(defun write-csv-file (path header rows)
  "Escreve o arquivo CSV em PATH com a linha de cabeçalho HEADER e as linhas ROWS.

HEADER é uma lista de nomes de coluna e cada linha de ROWS é uma lista de valores
na ordem do cabeçalho. Cada valor é convertido por PRINC-TO-STRING e citado
conforme a RFC 4180 quando necessário. Sobrescreve o arquivo se já existir e o
cria caso contrário. Retorna PATH."
  (with-open-file (out path :direction :output :if-exists :supersede
                            :if-does-not-exist :create :external-format :utf-8)
    (flet ((emit-row (fields)
             (format out "~{~A~^,~}~%" (mapcar #'quote-csv-field fields))))
      (emit-row header)
      (dolist (row rows)
        (emit-row row))))
  path)
