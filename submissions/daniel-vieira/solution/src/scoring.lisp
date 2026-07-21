;;;; scoring.lisp --- O motor de scoring: dimensões, momentum, composto e listas.
;;;;
;;;; Aplica a metodologia de 'docs/metodologia-scoring.md' (ADR C4X9) sobre a
;;;; base de modelagem carregada por 'model.lisp': normaliza as dimensões por
;;;; percentil, agrega pela média geométrica ponderada das quatro dimensões e
;;;; produz as duas listas rankeadas. Os valores concretos (pesos, forma da
;;;; corcova) residem aqui, como a metodologia determina.

(in-package #:leadscorer)

;;; Parâmetros arbitrados e documentados do MVP. Na forma de agregação corrente
;;; (:GEOMETRIC), os quatro pesos são os expoentes da média geométrica ponderada.

(defparameter *weight-economic* 0.40
  "Expoente do potencial econômico na média geométrica ponderada do composto.")
(defparameter *weight-affinity* 0.35
  "Expoente da afinidade na média geométrica ponderada do composto.")
(defparameter *weight-adherence* 0.25
  "Expoente da aderência do agente na média geométrica ponderada do composto. A
aderência é a dimensão exibida como Especialização (ver ADR G5W2).")
(defparameter *maturity-churn-multiple* 6.0
  "Múltiplo da cadência em que a maturidade de recompra decai a zero. O braço
descendente é assumido, na ausência de contas inativas nesta base.")
(defparameter *maturity-neutral* 0.5
  "Maturidade de um par nunca comprado, que não tem sinal de recompra.")
(defparameter *adherence-series-discount* 0.5
  "Fração aplicada ao histórico de série do agente no recuo, quando falta
histórico no produto exato, por ser evidência indireta.")
(defparameter *weight-momentum* 0.5
  "O peso (expoente) do momentum na média geométrica. Ele permanece o eixo primário
por sua dispersão intrínseca, sem dominar por artefato de escala; o valor 0,5 foi
escolhido pela comparação de formas de agregação da Fase 5 ('aggregation-comparison').")
(defparameter *composite-form* :geometric
  "A forma de agregação: :GEOMETRIC (média geométrica ponderada das quatro
dimensões, padrão) ou :MULTIPLICATIVE (base aditiva vezes o momentum).")
(defparameter *dimension-floor* 1.0
  "Piso das três dimensões da base na média geométrica, para que um zero de
normalização não anule o índice; o momentum não é pisado, pois o seu zero é o
afundamento intencional do recém-fechado.")

(defstruct (scored (:copier nil))
  "O resultado da pontuação de uma tripla: as quatro dimensões, o momentum em
[0,1] e o composto, na escala 0-100 (o momentum em [0,1])."
  (agent "" :read-only t :type string)
  (account "" :read-only t :type string)
  (product "" :read-only t :type string)
  (economic 0.0 :read-only t :type real)
  (affinity 0.0 :read-only t :type real)
  (adherence 0.0 :read-only t :type real)
  (momentum 0.0 :read-only t :type real)
  (composite 0.0 :read-only t :type real))

(defun percentile-rank (x values)
  "O posto percentual 0-100 de X no conjunto VALUES, pela regra do posto médio,
100 * (menores + 0,5 * iguais) / n. Retorna 0.0 quando VALUES é vazio."
  (let ((n (length values))
        (less-count 0)
        (equal-count 0))
    (dolist (v values)
      ;; Igualdade exata deliberada na deteccao de empate: X e um elemento de
      ;; VALUES e os empates verdadeiros produzem floats bit-identicos. Uma
      ;; tolerancia uniria valores distintos, corrompendo o posto medio.
      (cond ((< v x) (incf less-count))
            ((= v x) (incf equal-count))))
    (if (zerop n)
        0.0
        (/ (* 100.0 (+ less-count (* 0.5 equal-count))) n))))

(defparameter *normalization* :percentile
  "A estratégia de normalização das dimensões: :PERCENTILE (padrão) ou :MIN-MAX.
Revinculada na análise de sensibilidade da validação.")

(defun min-max-normalize (x values)
  "A normalização min-max 0-100 de X no conjunto VALUES: 100 * (x - min) /
(max - min), limitada a [0,100]. Retorna 50.0 quando o intervalo é nulo e 0.0
quando VALUES é vazio. A limitação fixa nos extremos um X fora da população de
referência, caso que ocorre ao normalizar uma iniciada contra a população de
pares e sem o qual a forma multiplicativa produziria composto fora de faixa."
  (if (null values)
      0.0
      (let ((minimum (reduce #'min values))
            (maximum (reduce #'max values)))
        ;; Igualdade exata deliberada: apenas min e max estritamente iguais anulam
        ;; o denominador. Uma comparacao com tolerancia achataria faixas quase-
        ;; degeneradas validas, alterando o resultado sem defeito a corrigir.
        (if (= minimum maximum)
            50.0
            (max 0.0 (min 100.0
                          (/ (* 100.0 (- x minimum)) (- maximum minimum))))))))

(defun normalize-value (x values)
  "Normaliza X no conjunto VALUES a 0-100 pela estratégia corrente *NORMALIZATION*."
  (ecase *normalization*
    (:percentile (percentile-rank x values))
    (:min-max (min-max-normalize x values))))

(defun cell-adherence (cell)
  "O valor de aderência a partir de CELL, a lista (WON-PRODUCT WON-SERIES): o Won
no produto, ou o Won na série descontado quando falta o do produto, ou 0."
  (destructuring-bind (&optional won-product won-series) cell
    (cond ((and won-product (plusp won-product)) won-product)
          ((and won-series (plusp won-series))
           (* *adherence-series-discount* won-series))
          (t 0))))

(defun adherence-value (agent product table)
  "O valor de aderência do AGENT no PRODUCT, segundo a hash TABLE de aderência."
  (cell-adherence (gethash (list agent product) table)))

(defun pair-affinity-value (won-count sector-avg)
  "A afinidade de um par: a contagem de Won do par, ou a média de setor quando o
par não registra Won."
  (if (plusp won-count) won-count sector-avg))

(defun momentum-maturity (days-since cadence)
  "A maturidade de recompra em [0,1] para os potenciais, função em corcova de
r = DAYS-SINCE / CADENCE: ascendente até o pico em r igual a 1 e descendente até 0
em r igual a *MATURITY-CHURN-MULTIPLE*. Um par nunca comprado (DAYS-SINCE nulo)
recebe *MATURITY-NEUTRAL*."
  (if (or (null days-since) (null cadence) (not (plusp cadence)))
      *maturity-neutral*
      (let ((r (/ days-since cadence)))
        (cond ((<= r 0) 0.0)
              ((<= r 1) (float r 1.0))
              ((>= r *maturity-churn-multiple*) 0.0)
              (t (max 0.0 (- 1.0 (/ (- r 1.0)
                                    (- *maturity-churn-multiple* 1.0)))))))))

(defun momentum-decay (age decay)
  "O peso de decaimento pós-engajamento em [0,1] para as iniciadas: a fração de
vitória restante na idade AGE, pelo vetor DECAY. Fora da faixa, retorna 0.0."
  (if (and age (<= 0 age) (< age (length decay)))
      (aref decay age)
      0.0))

(defun multiplicative-composite (economic affinity adherence momentum)
  "A forma de agregação legada (:MULTIPLICATIVE, hoje inativa; ver *COMPOSITE-FORM*):
a base aditiva ponderada de {econômico, afinidade, aderência} em 0-100 multiplicada
pelo fator de MOMENTUM em [0,1]. Retida para comparação de formas de agregação."
  (let ((base (/ (+ (* *weight-economic* economic)
                    (* *weight-affinity* affinity)
                    (* *weight-adherence* adherence))
                 (+ *weight-economic* *weight-affinity* *weight-adherence*))))
    (* base momentum)))

(defun geometric-composite (economic affinity adherence momentum)
  "A média geométrica ponderada das quatro dimensões na escala 0-100, com o
MOMENTUM em [0,1] reescalado a 0-100. As três dimensões da base são pisadas em
*DIMENSION-FLOOR*; um MOMENTUM igual a 0 leva o índice a 0."
  (let ((m (* 100.0 momentum)))
    (if (<= m 0.0)
        0.0
        (let ((e (max economic *dimension-floor*))
              (a (max affinity *dimension-floor*))
              (d (max adherence *dimension-floor*))
              (sum (+ *weight-economic* *weight-affinity*
                      *weight-adherence* *weight-momentum*)))
          (expt (* (expt e *weight-economic*)
                   (expt a *weight-affinity*)
                   (expt d *weight-adherence*)
                   (expt m *weight-momentum*))
                (/ 1.0 sum))))))

(defun composite (economic affinity adherence momentum)
  "O composto 0-100 das quatro dimensões, pela forma corrente *COMPOSITE-FORM*. Um
MOMENTUM igual a 0 zera o composto em ambas as formas."
  (ecase *composite-form*
    (:geometric (geometric-composite economic affinity adherence momentum))
    (:multiplicative (multiplicative-composite economic affinity adherence
                                               momentum))))

(defstruct (model (:copier nil))
  "A base de modelagem carregada, com as features das duas listas e as populações
de referência para os percentis."
  (pairs nil :read-only t)
  (opportunities nil :read-only t)
  (adherence nil :read-only t)
  (decay nil :read-only t)
  (economic-values nil :read-only t)
  (affinities nil :read-only t)
  (adherence-values nil :read-only t)
  (agents nil :read-only t))

(defparameter *derived-directory*
  (asdf:system-relative-pathname :leadscorer "data/derived/")
  "Diretorio dos CSV derivados que servem de base ao modelo de scoring, resolvido
relativo ao sistema (nao ao diretorio de trabalho), em consistencia com o seed e
as migracoes.")

(defun load-model (&optional (directory *derived-directory*))
  "Carrega a base de modelagem dos CSV derivados sob DIRECTORY e precomputa as
populações de referência dos percentis. Retorna uma estrutura MODEL."
  (let ((pairs (load-pairs (merge-pathnames "potentials_base.csv" directory)))
        (opportunities (load-opportunities
                        (merge-pathnames "initiated_base.csv" directory)))
        (adherence (load-adherence (merge-pathnames "adherence.csv" directory)))
        (decay (load-decay (merge-pathnames "decay.csv" directory)))
        (adherence-values '())
        (agent-set (make-hash-table :test #'equal)))
    (maphash (lambda (key cell)
               (setf (gethash (first key) agent-set) t)
               (push (cell-adherence cell) adherence-values))
             adherence)
    (make-model
     :pairs pairs
     :opportunities opportunities
     :adherence adherence
     :decay decay
     :economic-values (mapcar #'pair-economic-value pairs)
     :affinities (mapcar (lambda (p)
                           (pair-affinity-value (pair-won-count p)
                                                (pair-sector-avg p)))
                         pairs)
     :adherence-values adherence-values
     :agents (sort (loop for name being the hash-keys of agent-set collect name)
                   #'string<))))

(defun model-pair-context-index (model)
  "Uma hash-table de teste EQUAL, chaveada por (ACCOUNT . PRODUCT), cujo valor e a
plist '(:cadence-days D :last-close-value V)' com os campos de contexto do par vindos
do retrato estatico do MODEL. Expoe apenas dados de exibicao (nao as structs internas),
para enriquecer as linhas de oportunidade da camada de apresentacao. Um par ausente do
modelo simplesmente nao consta da tabela, e o chamador degrada os campos."
  (let ((table (make-hash-table :test #'equal)))
    (dolist (pair (model-pairs model) table)
      (setf (gethash (cons (pair-account pair) (pair-product pair)) table)
            (list :cadence-days (pair-cadence-days pair)
                  :last-close-value (pair-last-close-value pair))))))

(defun score-triple (agent account product economic-value affinity-raw momentum model)
  "Monta a estrutura SCORED de uma tripla AGENT-ACCOUNT-PRODUCT: normaliza o
economico (ECONOMIC-VALUE) e a afinidade (AFFINITY-RAW) contra as populacoes de
referencia do MODEL, busca e normaliza a aderencia por AGENT e PRODUCT, e compoe
com o MOMENTUM ja calculado em [0,1]. Nucleo comum de SCORE-PAIR e
SCORE-OPPORTUNITY, que diferem apenas na origem dos valores e na forma do
momentum."
  (let ((economic (normalize-value economic-value (model-economic-values model)))
        (affinity (normalize-value affinity-raw (model-affinities model)))
        (adherence (normalize-value
                    (adherence-value agent product (model-adherence model))
                    (model-adherence-values model))))
    (make-scored :agent agent :account account :product product
                 :economic economic :affinity affinity :adherence adherence
                 :momentum momentum
                 :composite (composite economic affinity adherence momentum))))

(defun score-pair (agent pair model)
  "Pontua o PAIR para o AGENT no MODEL, com o momentum de maturidade. Retorna uma
estrutura SCORED."
  (score-triple agent (pair-account pair) (pair-product pair)
                (pair-economic-value pair)
                (pair-affinity-value (pair-won-count pair) (pair-sector-avg pair))
                (momentum-maturity (pair-days-since pair) (pair-cadence-days pair))
                model))

(defun score-opportunity (opportunity model)
  "Pontua a OPPORTUNITY iniciada para o seu agente no MODEL, com o momentum de
decaimento. Retorna uma estrutura SCORED."
  (let ((agent (opportunity-agent opportunity)))
    (score-triple agent (opportunity-account opportunity)
                  (opportunity-product opportunity)
                  (opportunity-economic-value opportunity)
                  (pair-affinity-value (opportunity-won-count opportunity)
                                       (opportunity-sector-avg opportunity))
                  (momentum-decay (opportunity-age opportunity) (model-decay model))
                  model)))

(defun score-potentials-for-agent (agent model)
  "A lista de potenciais do AGENT, as triplas pontuadas em ordem decrescente de
composto."
  (stable-sort (mapcar (lambda (pair) (score-pair agent pair model))
                       (model-pairs model))
               #'> :key #'scored-composite))

(defun score-initiated-for-agent (agent model)
  "A lista de iniciadas do AGENT, as suas oportunidades engajadas pontuadas em
ordem decrescente de composto. A ordem inversa é o sinal de desmobilização."
  (stable-sort (mapcar (lambda (opportunity) (score-opportunity opportunity model))
                       (remove-if-not (lambda (opportunity)
                                        (string= agent
                                                 (opportunity-agent opportunity)))
                                      (model-opportunities model)))
               #'> :key #'scored-composite))

(defun scored->row (scored)
  "Converte SCORED em uma lista de campos para escrita CSV, com as dimensões
arredondadas a duas casas."
  (flet ((round2 (x) (/ (fround (* x 100)) 100)))
    (list (scored-agent scored) (scored-account scored) (scored-product scored)
          (round2 (scored-economic scored)) (round2 (scored-affinity scored))
          (round2 (scored-adherence scored))
          (round2 (* 100 (scored-momentum scored)))
          (round2 (scored-composite scored)))))

(defun emit-scored-lists (model &optional (directory #p"data/derived/"))
  "Escreve as listas pontuadas de todos os agentes do MODEL em
'potentials_scored.csv' e 'initiated_scored.csv' sob DIRECTORY. Retorna dois
valores, o número de linhas de potenciais e de iniciadas escritas."
  (let ((header '("sales_agent" "account" "product" "economic" "affinity"
                  "adherence" "momentum" "composite"))
        (potentials '())
        (initiated '()))
    (dolist (agent (model-agents model))
      (dolist (scored (score-potentials-for-agent agent model))
        (push (scored->row scored) potentials))
      (dolist (scored (score-initiated-for-agent agent model))
        (push (scored->row scored) initiated)))
    (let ((n-potentials (length potentials))
          (n-initiated (length initiated)))
      (write-csv-file (merge-pathnames "potentials_scored.csv" directory)
                      header (nreverse potentials))
      (write-csv-file (merge-pathnames "initiated_scored.csv" directory)
                      header (nreverse initiated))
      (values n-potentials n-initiated))))
