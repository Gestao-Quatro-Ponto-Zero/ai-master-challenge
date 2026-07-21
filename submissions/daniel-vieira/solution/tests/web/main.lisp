;;;; main.lisp --- Suíte de testes Parachute da camada web do LeadScorer.

(defpackage #:leadscorer/web/tests
  (:use #:cl #:parachute))

(in-package #:leadscorer/web/tests)

(define-test package-loads
  "Verifica que a camada web foi carregada e o pacote existe."
  (true (find-package '#:leadscorer/web)))
