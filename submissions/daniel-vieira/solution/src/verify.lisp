;;;; verify.lisp --- Verificacao de integridade e de contagem da carga.
;;;;
;;;; Confere as contagens canonicas, a integridade referencial e a invariante do
;;;; estado ativo das oportunidades, assumindo uma conexao ativa. E fail-closed:
;;;; sinaliza ERROR quando qualquer verificacao falha, de modo que os scripts de
;;;; carga encerrem com estado nao nulo.

(in-package #:leadscorer)

(defparameter *canonical-counts*
  '(("accounts" . 85)
    ("products" . 7)
    ("regional_offices" . 3)
    ("sales_managers" . 6)
    ("sales_agents" . 35)
    ("engagement_justifications" . 3)
    ("opportunities" . 530)
    ("engagements" . 7212)
    ("opportunity_scores" . 0))
  "Contagens canonicas esperadas por tabela apos a carga completa, derivadas dos
CSV normalizados e das decisoes da tarefa 9P4D.")

(defparameter *canonical-outcomes*
  '(("won" . 4238) ("lost" . 2473))
  "Contagens esperadas de desfecho em 'engagements'. Os 501 ciclos abertos tem
desfecho nulo.")

(defun scalar (sql)
  "Executa SQL sem parametros e retorna o seu unico valor escalar. SQL provem
apenas das definicoes internas deste modulo, nunca de entrada externa."
  (postmodern:query sql :single))

(defun collect-count-failures ()
  "Retorna a lista das discrepancias de contagem de tabela, cada uma como
'(tabela esperado obtido)'."
  (loop for (table . expected) in *canonical-counts*
        for actual = (scalar (format nil "SELECT COUNT(*) FROM ~A" table))
        unless (= actual expected)
          collect (list table expected actual)))

(defun collect-integrity-failures ()
  "Retorna a lista das violacoes de integridade e da invariante do estado ativo,
cada uma como '(descricao valor-esperado valor-obtido)'. Cada consulta e
formulada de modo que o valor esperado seja zero, salvo as contagens de
desfecho."
  (let ((checks
          (list
           (list "oportunidades 'prospecting' com ciclo aberto" 0
                 (scalar "SELECT COUNT(*) FROM opportunities o
                          WHERE o.status = 'prospecting'
                            AND EXISTS (SELECT 1 FROM engagements e
                                        WHERE e.opportunity_id = o.id
                                          AND e.closed_at IS NULL)"))
           (list "oportunidades 'engaging' sem ciclo aberto" 0
                 (scalar "SELECT COUNT(*) FROM opportunities o
                          WHERE o.status = 'engaging'
                            AND NOT EXISTS (SELECT 1 FROM engagements e
                                            WHERE e.opportunity_id = o.id
                                              AND e.closed_at IS NULL)"))
           (list "oportunidades 'engaging' cujo engaged_by nao tem ciclo aberto" 0
                 (scalar "SELECT COUNT(*) FROM opportunities o
                          WHERE o.status = 'engaging'
                            AND NOT EXISTS (SELECT 1 FROM engagements e
                                            WHERE e.opportunity_id = o.id
                                              AND e.closed_at IS NULL
                                              AND e.sales_agent_id = o.engaged_by_id)"))
           (list "engagements sem valor de fechamento em ciclo fechado com desfecho" 0
                 (scalar "SELECT COUNT(*) FROM engagements
                          WHERE outcome IS NOT NULL AND close_value_amount IS NULL")))))
    (append
     (remove-if (lambda (check) (= (second check) (third check))) checks)
     (loop for (outcome . expected) in *canonical-outcomes*
           for actual = (postmodern:query
                         "SELECT COUNT(*) FROM engagements WHERE outcome = $1"
                         outcome :single)
           unless (= actual expected)
             collect (list (format nil "engagements com desfecho '~A'" outcome)
                           expected actual)))))

(defun verify-persistence ()
  "Verifica as contagens canonicas, a integridade referencial e a invariante do
estado ativo. Imprime um relatorio e retorna T quando tudo confere; sinaliza
ERROR, listando as falhas, caso contrario."
  (let ((failures (append (collect-count-failures) (collect-integrity-failures))))
    (if failures
        (error "Verificacao da persistencia falhou:~{~%  - ~A: esperado ~A, obtido ~A~}"
               (loop for (label expected actual) in failures
                     append (list label expected actual)))
        (progn
          (format t "~&Verificacao da persistencia: todas as contagens e ~
                     invariantes conferem.~%")
          (dolist (entry *canonical-counts*)
            (format t "  ~A: ~D~%" (car entry) (cdr entry)))
          t))))
