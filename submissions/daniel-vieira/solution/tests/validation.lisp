;;;; validation.lisp --- Testes Parachute da validação de robustez.

(in-package #:leadscorer/tests)

(define-test spearman-known-cases
  (is near 1.0 (leadscorer::spearman '(1 2 3 4) '(1 2 3 4)))
  (is near -1.0 (leadscorer::spearman '(1 2 3 4) '(4 3 2 1)))
  (is near 0.5 (leadscorer::spearman '(1 2 3) '(2 1 3))))

(define-test min-max-normalize-cases
  (is near 50.0 (leadscorer::min-max-normalize 5 '(0 10)))
  (is near 0.0 (leadscorer::min-max-normalize 0 '(0 10)))
  (is near 100.0 (leadscorer::min-max-normalize 10 '(0 10)))
  (is near 50.0 (leadscorer::min-max-normalize 5 '(5 5 5)))
  (is near 0.0 (leadscorer::min-max-normalize 1 '()))
  ;; Valores fora da populacao de referencia sao fixados nos extremos [0,100],
  ;; caso que ocorre ao normalizar uma iniciada contra a populacao de pares.
  (is near 100.0 (leadscorer::min-max-normalize 15 '(0 10)))
  (is near 0.0 (leadscorer::min-max-normalize -5 '(0 10))))

(define-test pearson-empty-input
  ;; pearson diretamente com vetores vazios (n=0) retorna 0.0, sem sinalizar
  ;; erro de divisao por zero.
  (is near 0.0 (leadscorer::pearson #() #())))

(define-test spearman-degenerate-inputs
  ;; Entrada vazia (n=0) nao sinaliza erro; retorna 0.0.
  (is near 0.0 (leadscorer::spearman '() '()))
  ;; Variancia nula (serie constante) retorna 0.0.
  (is near 0.0 (leadscorer::spearman '(1 1 1) '(1 2 3))))

(define-test normalize-value-dispatch
  (let ((leadscorer::*normalization* :percentile))
    (is near 50.0 (leadscorer::normalize-value 2 '(1 2 3))))
  (let ((leadscorer::*normalization* :min-max))
    (is near 50.0 (leadscorer::normalize-value 2 '(1 3)))))

(define-test jaccard-cases
  (is near 1.0 (leadscorer::jaccard '(a b c) '(a b c)))
  (is near 0.0 (leadscorer::jaccard '(a b) '(c d)))
  (is near (/ 1.0 3.0) (leadscorer::jaccard '(a b) '(b c)))
  ;; Uniao vazia (ambos vazios) retorna 0.0, sem divisao por zero.
  (is near 0.0 (leadscorer::jaccard '() '())))
