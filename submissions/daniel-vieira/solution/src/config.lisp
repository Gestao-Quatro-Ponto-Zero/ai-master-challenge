;;;; config.lisp --- Leitura da configuracao em forma Lisp e regras de negocio.
;;;;
;;;; Le 'config/model.lisp' (uma s-expression, dado e nao codigo) e revincula os
;;;; parametros do modelo de scoring alem de fixar as regras de negocio do ciclo
;;;; de engajamento. A leitura desarma a avaliacao em tempo de leitura
;;;; ('*read-eval*' NIL) e interna os simbolos no pacote KEYWORD, seguindo o
;;;; precedente de 'parse-number-or-nil' (model.lisp). A configuracao e a fonte
;;;; canonica dos valores; os defparameters aqui e em 'scoring.lisp' sao o
;;;; fallback quando uma chave falta ou o arquivo esta ausente.

(in-package #:leadscorer)

;;; --- Regras de negocio (defaults; sobrescritos pela configuracao) ---

(defparameter *max-engagements* 10
  "Numero maximo de oportunidades que um agente pode engajar simultaneamente.")

(defparameter *top-tier-size* 10
  "Tamanho do top tier: as N oportunidades melhor ranqueadas de cada agente.")

(defparameter *potential-cutoff* 40
  "Filtro de corte do modelo: as oportunidades disponiveis com potencial abaixo
deste limiar (inteiro 0 a 100) sao rebaixadas ao final da lista. Zero desativa o
corte.")

(defparameter *expiration-minutes* 20
  "Janela de tempo REAL, em minutos, em que uma oportunidade engajada percorre o
horizonte de decaimento ate expirar. Fixa o ritmo do relogio virtual acelerado.")

(defparameter *ranking-interval-seconds* 60
  "Intervalo, em segundos, entre execucoes do tick do ciclo (ranqueamento,
decaimento e expiracao).")

(defparameter *decay-interval-seconds* 60
  "Intervalo nominal, em segundos, do servico de decaimento. No MVP o decaimento
compartilha o tick do ranqueamento; mantido como parametro por fidelidade a
concepcao.")

(defparameter *virtual-epoch* 1514678400000
  "Ancora do relogio virtual em UNIX-ms UTC: a epoca do seed/modelagem
(2017-12-31, o asof MAX(close_date) do dataset). Instantes de engajamento sao
interpretados nesta base de tempo.")

(defparameter *config-path*
  (asdf:system-relative-pathname :leadscorer "config/model.lisp")
  "Caminho do arquivo de configuracao em forma Lisp, fonte canonica dos valores.")

(defconstant +ms-per-day+ 86400000
  "Milissegundos em um dia, para converter idades UNIX-ms em dias.")

;;; --- Schema de validacao ---

(defun non-negative-real-p (x)
  "Verdadeiro quando X e um real nao negativo."
  (and (realp x) (>= x 0)))

(defun positive-integer-p (x)
  "Verdadeiro quando X e um inteiro positivo."
  (and (integerp x) (plusp x)))

(defun composite-form-value-p (x)
  "Verdadeiro quando X e uma forma de agregacao legal."
  (and (member x '(:geometric :multiplicative)) t))

(defun normalization-value-p (x)
  "Verdadeiro quando X e uma estrategia de normalizacao legal."
  (and (member x '(:percentile :min-max)) t))

(defun percentage-integer-p (x)
  "Verdadeiro quando X e um inteiro no intervalo fechado de 0 a 100."
  (and (integerp x) (<= 0 x 100)))

(defparameter *config-schema*
  (list (cons :weight-economic #'non-negative-real-p)
        (cons :weight-affinity #'non-negative-real-p)
        (cons :weight-adherence #'non-negative-real-p)
        (cons :weight-momentum #'non-negative-real-p)
        (cons :composite-form #'composite-form-value-p)
        (cons :normalization #'normalization-value-p)
        (cons :dimension-floor #'non-negative-real-p)
        (cons :maturity-churn-multiple #'non-negative-real-p)
        (cons :maturity-neutral #'non-negative-real-p)
        (cons :adherence-series-discount #'non-negative-real-p)
        (cons :max-engagements #'positive-integer-p)
        (cons :top-tier-size #'positive-integer-p)
        (cons :potential-cutoff #'percentage-integer-p)
        (cons :expiration-minutes #'positive-integer-p)
        (cons :ranking-interval-seconds #'positive-integer-p)
        (cons :decay-interval-seconds #'positive-integer-p)
        (cons :virtual-epoch #'positive-integer-p))
  "Alist de (CHAVE . PREDICADO-DE-TIPO) que define as chaves de configuracao
legais e a validacao de cada valor.")

;;; --- Leitura, validacao e aplicacao ---

(defun read-config-form (path)
  "Le UMA forma de PATH como dado e a retorna. Vincula '*READ-EVAL*' a NIL e
'*PACKAGE*' ao pacote KEYWORD, de modo que nenhuma forma seja avaliada e todo
simbolo interne como palavra-chave. Sinaliza ERROR quando PATH esta vazio, contem
conteudo apos a primeira forma ou a forma nao e uma lista."
  (with-open-file (stream path :direction :input)
    (let ((*read-eval* nil)
          (*package* (find-package :keyword))
          (eof '#:eof))
      (let ((form (read stream nil eof)))
        (when (eq form eof)
          (error "Configuracao vazia em ~A." path))
        (unless (eq (read stream nil eof) eof)
          (error "Configuracao com conteudo apos a primeira forma em ~A." path))
        (unless (listp form)
          (error "Configuracao deve ser uma lista de pares chave-valor."))
        form))))

(defun validate-config (plist)
  "Valida PLIST contra '*CONFIG-SCHEMA*' e a retorna. Sinaliza ERROR quando PLIST
nao e uma lista de pares, quando uma chave e desconhecida (fail-closed contra erro
de digitacao) ou quando um valor viola o predicado de tipo da sua chave."
  (unless (and (listp plist) (evenp (length plist)))
    (error "Configuracao invalida: esperada uma lista de pares chave-valor."))
  (loop for (key value) on plist by #'cddr
        for entry = (assoc key *config-schema*)
        do (unless entry
             (error "Chave de configuracao desconhecida: ~S." key))
           (unless (funcall (cdr entry) value)
             (error "Valor invalido para a chave ~S: ~S." key value)))
  plist)

(defun apply-config-entry (key value)
  "Atribui o parametro global correspondente a CHAVE de configuracao com VALUE.
CHAVE deve ser uma das chaves de '*CONFIG-SCHEMA*' (garantido por VALIDATE-CONFIG)."
  (ecase key
    (:weight-economic (setf *weight-economic* value))
    (:weight-affinity (setf *weight-affinity* value))
    (:weight-adherence (setf *weight-adherence* value))
    (:weight-momentum (setf *weight-momentum* value))
    (:composite-form (setf *composite-form* value))
    (:normalization (setf *normalization* value))
    (:dimension-floor (setf *dimension-floor* value))
    (:maturity-churn-multiple (setf *maturity-churn-multiple* value))
    (:maturity-neutral (setf *maturity-neutral* value))
    (:adherence-series-discount (setf *adherence-series-discount* value))
    (:max-engagements (setf *max-engagements* value))
    (:top-tier-size (setf *top-tier-size* value))
    (:potential-cutoff (setf *potential-cutoff* value))
    (:expiration-minutes (setf *expiration-minutes* value))
    (:ranking-interval-seconds (setf *ranking-interval-seconds* value))
    (:decay-interval-seconds (setf *decay-interval-seconds* value))
    (:virtual-epoch (setf *virtual-epoch* value))))

(defun apply-config (plist)
  "Aplica PLIST, ja validado, aos parametros globais, uma chave presente por vez.
Retorna PLIST. As chaves ausentes preservam o default compilado."
  (loop for (key value) on plist by #'cddr
        do (apply-config-entry key value))
  plist)

(defun load-config (&optional (path *config-path*))
  "Le, valida e aplica a configuracao de PATH aos parametros globais; retorna a
plist aplicada. Quando PATH esta ausente, mantem os defaults compilados, registra
um aviso em '*ERROR-OUTPUT*' e retorna NIL. Sinaliza ERROR quando o arquivo existe
mas e invalido (fail-closed)."
  (if (probe-file path)
      (let ((plist (validate-config (read-config-form path))))
        (apply-config plist)
        plist)
      (progn
        (format *error-output*
                "~&Configuracao ~A ausente; usando os defaults compilados.~%" path)
        nil)))

;;; --- Acessores derivados ---

(defun expiration-ms ()
  "A janela de expiracao em milissegundos de tempo real."
  (* *expiration-minutes* 60000))

(defun ranking-interval-ms ()
  "O intervalo do tick em milissegundos."
  (* *ranking-interval-seconds* 1000))
