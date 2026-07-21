;;;; main.lisp --- Suíte de testes Parachute do LeadScorer.

(defpackage #:leadscorer/tests
  (:use #:cl #:parachute)
  (:import-from #:leadscorer #:read-csv-file #:csv-rows->alists))

(in-package #:leadscorer/tests)

(defparameter *fixture-path*
  (asdf:system-relative-pathname :leadscorer "tests/fixtures/sample.csv")
  "Caminho do fixture CSV mínimo usado nos testes de leitura.")

(defparameter *empty-fixture-path*
  (asdf:system-relative-pathname :leadscorer "tests/fixtures/empty.csv")
  "Caminho de um fixture CSV vazio, usado para testar a sinalização de erro.")

(define-test read-csv-file-header-and-rows
  (multiple-value-bind (header rows) (read-csv-file *fixture-path*)
    (is equal '("id" "nome" "valor") header)
    (is = 3 (length rows))
    (is equal '("1" "Alfa" "100") (first rows))))

(define-test csv-rows->alists-pairs-columns
  (multiple-value-bind (header rows) (read-csv-file *fixture-path*)
    (let ((alists (csv-rows->alists header rows)))
      (is = 3 (length alists))
      (is equal "Beta"
          (cdr (assoc "nome" (second alists) :test #'string=))))))

(define-test read-csv-file-signals-on-empty
  (fail (read-csv-file *empty-fixture-path*) 'leadscorer:empty-csv-file))
