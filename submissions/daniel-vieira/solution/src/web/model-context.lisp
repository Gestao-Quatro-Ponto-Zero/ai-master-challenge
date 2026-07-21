;;;; model-context.lisp --- Enriquecimento das linhas de oportunidade pelo modelo.
;;;;
;;;; A camada web une aos campos de contexto do banco os dois campos que residem
;;;; apenas no retrato estatico do modelo de scoring: a cadencia de recompra (Prazo
;;;; de decisao) e o valor da ultima compra (Ultima compra), casando por (conta,
;;;; produto). O modelo e o do agendador quando em execucao, ou um carregado sob
;;;; demanda; quando indisponivel (CSV derivados ausentes), os dois campos degradam
;;;; para NIL e a apresentacao exibe um travessao. A funcao de enriquecimento e pura
;;;; e recebe o indice ja construido, de modo a ser testavel sem banco nem modelo.

(in-package #:leadscorer/web)

(defvar *web-model* nil
  "Modelo de scoring carregado sob demanda para a camada web, cacheado, quando o
agendador nao proveu um. Ver CURRENT-MODEL.")

(defun current-model ()
  "O modelo de scoring para a camada web: o do agendador ('*SCHEDULER-MODEL*') quando
em execucao, senao um carregado sob demanda e cacheado em '*WEB-MODEL*'. Retorna NIL
quando o modelo nao pode ser carregado (CSV derivados ausentes), caso em que os campos
dependentes do modelo degradam para NIL."
  (or *scheduler-model*
      *web-model*
      (setf *web-model*
            (handler-case (ls:load-model)
              (error (condition)
                (format *error-output*
                        "~&Modelo indisponivel para a camada web: ~A~%" condition)
                nil)))))

(defun current-model-and-now ()
  "Retorna, como valores, o modelo de scoring corrente (CURRENT-MODEL) e o instante virtual
corrente NOW, ou NIL para NOW quando o relogio virtual nao esta ancorado (agendador parado,
'*virtual-t0*' nulo). Concentra o idioma de ancoragem do relogio partilhado pelos handlers
que carimbam ou exibem o tempo do ciclo."
  (let ((model (current-model)))
    (values model (and model ls:*virtual-t0* (ls:current-virtual-now model)))))

(defun enrich-rows-with-model (rows index)
  "Retorna ROWS, uma lista de plists de oportunidade, com as chaves ':cadence-days' e
':last-close-value' acrescentadas a partir de INDEX, a hash-table de
'ls:model-pair-context-index' chaveada por (conta . produto). Quando INDEX e NIL, ou o
par nao consta, os dois campos ficam NIL. Puro: nao consulta o banco nem o relogio."
  (mapcar (lambda (row)
            (let ((context (and index
                                (gethash (cons (getf row :account)
                                               (getf row :product))
                                         index))))
              (list* :cadence-days (getf context :cadence-days)
                     :last-close-value (getf context :last-close-value)
                     row)))
          rows))
