;;;; validation.lisp --- Validação de robustez do scoring.
;;;;
;;;; Sem alvo discriminativo e sem treinamento, a validação é sobre robustez, e
;;;; não acurácia (Handbook Step 8): não-degenerescência contra baselines,
;;;; sensibilidade à normalização e aos pesos, e validade de face. Os resultados
;;;; consolidam-se em 'docs/validacao-scoring.md'.

(in-package #:leadscorer)

(defun ranks (values)
  "Vetor de postos médios 1-based de VALUES, paralelo a VALUES. Os empates
recebem a média dos postos que ocupariam."
  (let* ((n (length values))
         (indexed (make-array n))
         (result (make-array n)))
    (loop for v in values for i from 0 do (setf (aref indexed i) (cons v i)))
    (setf indexed (sort indexed #'< :key #'car))
    (let ((i 0))
      (loop while (< i n)
            do (let ((j i))
                 ;; Igualdade exata deliberada na deteccao de empate: um empate e,
                 ;; por definicao, igualdade exata, e uma tolerancia fabricaria
                 ;; empates falsos entre valores distintos. Observacao de apoio,
                 ;; dependente do dataset fixo versionado (nao um invariante): sobre
                 ;; o modelo atual nenhum par de valores de dimensao normalizada fica
                 ;; a menos de 1e-9 sem ser exatamente igual (menor intervalo nao-nulo
                 ;; ~1e-8, no momentum), de modo que uma tolerancia so poderia
                 ;; corromper os coeficientes de Spearman validados.
                 (loop while (and (< (1+ j) n)
                                  (= (car (aref indexed j))
                                     (car (aref indexed (1+ j)))))
                       do (incf j))
                 (let ((average-rank (/ (+ i j 2) 2.0d0)))
                   (loop for k from i to j
                         do (setf (aref result (cdr (aref indexed k)))
                                  average-rank)))
                 (setf i (1+ j)))))
    result))

(defun pearson (xs ys)
  "A correlação de Pearson entre os vetores paralelos XS e YS. Retorna 0.0 quando
XS é vazio ou quando uma das variâncias é nula."
  (let ((n (length xs)))
    (if (zerop n)
        0.0
        (let ((mean-x (/ (reduce #'+ xs) n))
              (mean-y (/ (reduce #'+ ys) n))
              (sxy 0.0d0)
              (sxx 0.0d0)
              (syy 0.0d0))
          (loop for x across xs for y across ys
                do (let ((dx (- x mean-x))
                         (dy (- y mean-y)))
                     (incf sxy (* dx dy))
                     (incf sxx (* dx dx))
                     (incf syy (* dy dy))))
          (if (or (zerop sxx) (zerop syy))
              0.0
              (/ sxy (sqrt (* sxx syy))))))))

(defun spearman (xs ys)
  "A correlação de postos de Spearman entre as listas paralelas XS e YS, a
correlação de Pearson dos seus postos médios."
  (pearson (ranks xs) (ranks ys)))

(defun median-of (numbers)
  "A mediana da lista NUMBERS, ou 0 quando vazia."
  (let* ((sorted (sort (copy-list numbers) #'<))
         (n (length sorted)))
    (cond ((zerop n) 0)
          ((oddp n) (nth (floor n 2) sorted))
          (t (/ (+ (nth (1- (floor n 2)) sorted) (nth (floor n 2) sorted)) 2.0)))))

(defun triple-key (scored)
  "A chave (AGENT ACCOUNT PRODUCT) de uma tripla pontuada."
  (list (scored-agent scored) (scored-account scored) (scored-product scored)))

(defun top-k-keys (scored-list k)
  "As chaves das primeiras K triplas de SCORED-LIST, já ordenada."
  (mapcar #'triple-key (subseq scored-list 0 (min k (length scored-list)))))

(defun jaccard (set-a set-b)
  "A similaridade de Jaccard entre as listas SET-A e SET-B tomadas como conjuntos."
  (let* ((intersection (count-if (lambda (x) (member x set-b :test #'equal)) set-a))
         (union-size (- (+ (length set-a) (length set-b)) intersection)))
    (if (zerop union-size)
        0.0
        (/ intersection union-size 1.0))))

(defun baseline-correlations (scored-list)
  "Uma lista de pares (nome . spearman) do composto contra as quatro dimensões e uma
ordem arbitrária determinística, sobre SCORED-LIST. Evidencia se o composto é uma
mistura genuína, nem redundante com uma única dimensão nem aleatória."
  (let ((composite (mapcar #'scored-composite scored-list)))
    (list (cons "economico"
                (spearman composite (mapcar #'scored-economic scored-list)))
          (cons "afinidade"
                (spearman composite (mapcar #'scored-affinity scored-list)))
          (cons "aderencia"
                (spearman composite (mapcar #'scored-adherence scored-list)))
          (cons "momentum"
                (spearman composite (mapcar #'scored-momentum scored-list)))
          (cons "arbitrario"
                (spearman composite
                          (mapcar (lambda (s) (float (sxhash (triple-key s)) 1.0))
                                  scored-list))))))

(defun composites-by-key (scored-list)
  "Hash da chave da tripla para o composto, a partir de SCORED-LIST."
  (let ((table (make-hash-table :test #'equal)))
    (dolist (s scored-list table)
      (setf (gethash (triple-key s) table) (scored-composite s)))))

(defun normalization-sensitivity (model agent k)
  "O Spearman e a sobreposição do top-K entre o composto sob percentil e sob
min-max, para o AGENT no MODEL."
  (let (percentile-scored minmax-scored)
    (let ((*normalization* :percentile))
      (setf percentile-scored (score-potentials-for-agent agent model)))
    (let ((*normalization* :min-max))
      (setf minmax-scored (score-potentials-for-agent agent model)))
    (let ((minmax-map (composites-by-key minmax-scored))
          (xs '())
          (ys '()))
      (dolist (s percentile-scored)
        (push (scored-composite s) xs)
        (push (gethash (triple-key s) minmax-map) ys))
      (list (cons "spearman" (spearman xs ys))
            (cons "top-k-jaccard"
                  (jaccard (top-k-keys percentile-scored k)
                           (top-k-keys minmax-scored k)))))))

(defparameter *weight-scenarios*
  '((0.40 0.35 0.25) (1 1 1) (3 1 1) (1 3 1) (1 1 3))
  "Cenários de peso (econômico afinidade aderência) para a sensibilidade. O
composto normaliza pela soma dos pesos, de modo que apenas as proporções importam.")

(defun rank-map (scored-list)
  "Hash da chave da tripla para o posto 1-based na SCORED-LIST já ordenada."
  (let ((table (make-hash-table :test #'equal))
        (rank 0))
    (dolist (s scored-list table)
      (setf (gethash (triple-key s) table) (incf rank)))))

(defun weight-sensitivity (model agent k)
  "Sobre os *WEIGHT-SCENARIOS*, a estabilidade do top-K e a faixa de posto mediana
das triplas do AGENT no MODEL."
  (let ((per-key-ranks (make-hash-table :test #'equal))
        (base-top-k nil)
        (first-scenario t))
    (dolist (scenario *weight-scenarios*)
      (destructuring-bind (we wa wd) scenario
        (let ((*weight-economic* we)
              (*weight-affinity* wa)
              (*weight-adherence* wd))
          (let* ((scored (score-potentials-for-agent agent model))
                 (rmap (rank-map scored)))
            (when first-scenario
              (setf base-top-k (top-k-keys scored k)
                    first-scenario nil))
            (maphash (lambda (key rank) (push rank (gethash key per-key-ranks)))
                     rmap)))))
    (let ((stable (count-if (lambda (key)
                              (every (lambda (r) (<= r k))
                                     (gethash key per-key-ranks)))
                            base-top-k))
          (ranges '()))
      (maphash (lambda (key rank-list)
                 (declare (ignore key))
                 (push (- (reduce #'max rank-list) (reduce #'min rank-list)) ranges))
               per-key-ranks)
      (list (cons "top-k-estaveis" stable)
            (cons "top-k-total" (length base-top-k))
            (cons "faixa-posto-mediana" (median-of ranges))))))

(defun score-all-potentials (model)
  "Todas as triplas de potenciais pontuadas, de todos os agentes do MODEL."
  (mapcan (lambda (agent) (score-potentials-for-agent agent model))
          (model-agents model)))

(defun run-validation (model &optional (agent (first (model-agents model))) (k 20))
  "Executa a validação de robustez sobre o MODEL: as correlações de baseline sobre
o conjunto agregado e as sensibilidades à normalização e aos pesos sobre um AGENT
representativo, com o top-K. Retorna uma lista associativa com os resultados."
  (let ((pooled (score-all-potentials model)))
    (list (cons "agente-representativo" agent)
          (cons "n-triplas-agregado" (length pooled))
          (cons "baselines" (baseline-correlations pooled))
          (cons "normalizacao" (normalization-sensitivity model agent k))
          (cons "pesos" (weight-sensitivity model agent k)))))

(defparameter *aggregation-settings*
  '((:multiplicative 0.5) (:geometric 0.5) (:geometric 1.0) (:geometric 1.5))
  "Formas de agregação e pesos de momentum comparados na seleção da Fase 5.")

(defun aggregation-comparison (model &optional (agent (first (model-agents model))))
  "Para cada forma de agregação e peso de momentum em *AGGREGATION-SETTINGS*, as
correlações de posto do composto contra as dimensões sobre o conjunto agregado e a
robustez à normalização. É a computação reprodutível que fundamentou a escolha da
média geométrica e do peso do momentum na Fase 5."
  (mapcar (lambda (setting)
            (destructuring-bind (form momentum-weight) setting
              (let ((*composite-form* form)
                    (*weight-momentum* momentum-weight))
                (list (cons "forma" form)
                      (cons "peso-momentum" momentum-weight)
                      (cons "correlacoes"
                            (baseline-correlations (score-all-potentials model)))
                      (cons "robustez-normalizacao"
                            (cdr (assoc "spearman"
                                        (normalization-sensitivity model agent 20)
                                        :test #'string=)))))))
          *aggregation-settings*))
