;;;; scoring.lisp --- Testes Parachute do motor de scoring.

(in-package #:leadscorer/tests)

(defparameter *derived-fixtures*
  (asdf:system-relative-pathname :leadscorer "tests/fixtures/derived/")
  "Diretório de fixtures derivados mínimos para os testes de scoring.")

(defun near (expected actual &optional (tolerance 1d-3))
  "Verdadeiro quando EXPECTED e ACTUAL diferem por menos de TOLERANCE."
  (< (abs (- expected actual)) tolerance))

(define-test percentile-rank-mid-rank
  (is near 50.0 (leadscorer::percentile-rank 2 '(1 2 3)))
  (is near 16.6667 (leadscorer::percentile-rank 1 '(1 2 3)))
  (is near 83.3333 (leadscorer::percentile-rank 3 '(1 2 3)))
  (is near 50.0 (leadscorer::percentile-rank 5 '(5)))
  (is near 0.0 (leadscorer::percentile-rank 1 '())))

(define-test cell-adherence-fallback
  (is = 5 (leadscorer::cell-adherence '(5 10)))
  (is near 5.0 (leadscorer::cell-adherence '(0 10)))
  (is = 0 (leadscorer::cell-adherence '(0 0)))
  (is = 0 (leadscorer::cell-adherence nil)))

(define-test pair-affinity-fallback
  (is = 3 (leadscorer::pair-affinity-value 3 7.0))
  (is near 7.0 (leadscorer::pair-affinity-value 0 7.0)))

(define-test momentum-maturity-hump
  (is near 0.0 (leadscorer::momentum-maturity 0 16))
  (is near 0.5 (leadscorer::momentum-maturity 8 16))
  (is near 1.0 (leadscorer::momentum-maturity 16 16))
  (is near 0.6 (leadscorer::momentum-maturity 48 16))
  (is near 0.0 (leadscorer::momentum-maturity 96 16))
  (is near 0.0 (leadscorer::momentum-maturity 200 16))
  (is near 0.5 (leadscorer::momentum-maturity nil 16)))

(define-test momentum-decay-lookup
  (let ((decay (vector 1.0 0.5 0.0)))
    (is near 1.0 (leadscorer::momentum-decay 0 decay))
    (is near 0.5 (leadscorer::momentum-decay 1 decay))
    (is near 0.0 (leadscorer::momentum-decay 2 decay))
    (is near 0.0 (leadscorer::momentum-decay 5 decay))
    (is near 0.0 (leadscorer::momentum-decay nil decay))))

(define-test composite-momentum-sink
  ;; Um momentum 0 zera o composto em ambas as formas (critério de aceitação),
  ;; e o pleno em todas as dimensões dá 100.
  (let ((leadscorer::*composite-form* :geometric))
    (is near 0.0 (leadscorer::composite 80 80 80 0.0))
    (is near 100.0 (leadscorer::composite 100 100 100 1.0)))
  (let ((leadscorer::*composite-form* :multiplicative))
    (is near 0.0 (leadscorer::composite 80 80 80 0.0))
    (is near 100.0 (leadscorer::composite 100 100 100 1.0))))

(define-test multiplicative-composite-value
  (let ((leadscorer::*composite-form* :multiplicative))
    (is near 43.0 (leadscorer::composite 60 40 20 1.0))
    (is near 0.0 (leadscorer::composite 0 0 0 1.0))))

(define-test geometric-composite-value
  (let ((leadscorer::*composite-form* :geometric)
        (leadscorer::*weight-momentum* 0.5))
    ;; (50 50 50 1.0): (50^1.0 * 100^0.5)^(1/1.5) = 500^(2/3)
    (is near (expt 500.0 (/ 2.0 3.0)) (leadscorer::composite 50 50 50 1.0))))

(define-test geometric-composite-dimension-floor
  ;; Uma dimensao da base igual a 0 nao anula o indice geometrico: o piso
  ;; *DIMENSION-FLOOR* impede a aniquilacao quando o momentum e positivo.
  (let ((leadscorer::*composite-form* :geometric))
    (true (plusp (leadscorer::composite 0 50 50 1.0)))))

(define-test scored-row-momentum-on-0-100
  (let ((row (leadscorer::scored->row
              (leadscorer::make-scored :agent "A" :account "X" :product "P"
                                       :economic 40.0 :affinity 30.0
                                       :adherence 20.0 :momentum 0.5
                                       :composite 22.5))))
    (is near 50.0 (nth 6 row))))

(define-test load-model-and-ordering
  (let* ((model (leadscorer:load-model *derived-fixtures*))
         (potentials (leadscorer:score-potentials-for-agent "Ann" model)))
    (is equal '("Ann" "Bob") (leadscorer:model-agents model))
    (is = 3 (length potentials))
    (is string= "MG Special"
        (leadscorer:scored-product (car (last potentials))))
    (is near 0.0 (leadscorer:scored-composite (car (last potentials))))
    (true (apply #'>= (mapcar #'leadscorer:scored-composite potentials)))
    (is = 1 (length (leadscorer:score-initiated-for-agent "Ann" model)))
    (is = 0 (length (leadscorer:score-initiated-for-agent "Bob" model)))))

(define-test load-pairs-economic-value
  ;; A dimensao economica passa a ler o ticket medio (economic_value), distinto
  ;; do preco de tabela (ADR R4T9).
  (let ((pair (first (leadscorer::load-pairs
                      (merge-pathnames "potentials_base.csv" *derived-fixtures*)))))
    (is near 545.0 (leadscorer::pair-economic-value pair))
    (is = 550 (leadscorer::pair-list-price pair))))
