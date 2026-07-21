;;;; leadscorer.asd --- Definição de sistema ASDF do LeadScorer.

;;; O UIOP já é provido pela imagem SBCL. Registra-se como sistema imutável para
;;; que o grafo de dependências do Postmodern não recarregue a versão do
;;; Quicklisp sobre a embutida, o que emitiria centenas de avisos de
;;; redefinição. Este formulário é avaliado na leitura do arquivo, antes do
;;; carregamento das dependências. Ver o worklog da tarefa 9P4D.
(asdf:register-immutable-system "uiop")

(asdf:defsystem "leadscorer"
  :description "MVP para classificação e distribuição de leads comerciais."
  :author "Polya Technologies"
  :license "Proprietary"
  :depends-on ("fare-csv" "postmodern")
  :serial t
  :components ((:module "src"
                :components ((:file "package")
                             (:file "csv")
                             (:file "model")
                             (:file "scoring")
                             (:file "config")
                             (:file "validation")
                             (:file "db")
                             (:file "migrate")
                             (:file "seed")
                             (:file "verify")
                             (:file "cycle")
                             (:file "engagement"))))
  :in-order-to ((asdf:test-op (asdf:test-op "leadscorer/tests"))))

(asdf:defsystem "leadscorer/tests"
  :description "Suíte de testes Parachute do LeadScorer."
  :author "Polya Technologies"
  :license "Proprietary"
  :depends-on ("leadscorer" "parachute")
  :serial t
  :components ((:module "tests"
                :components ((:file "main")
                             (:file "scoring")
                             (:file "validation")
                             (:file "persistence")
                             (:file "cycle")
                             (:file "engagement"))))
  :perform (asdf:test-op (op c)
             (declare (ignore op c))
             (let ((result (uiop:symbol-call :parachute :test :leadscorer/tests)))
               (unless (eq (uiop:symbol-call :parachute :status result) :passed)
                 (error "A suíte de testes do LeadScorer falhou.")))))

(asdf:defsystem "leadscorer/web"
  :description "Camada web do LeadScorer: aplicações do agente e do gerente."
  :author "Polya Technologies"
  :license "Proprietary"
  :depends-on ("leadscorer" "clack" "clack-handler-hunchentoot" "lack"
               "lack/middleware/session" "ningle" "spinneret")
  :serial t
  :components ((:module "src/web"
                :components ((:file "package")
                             (:file "config")
                             (:file "view")
                             (:file "render")
                             (:file "session")
                             (:file "queries")
                             (:file "scheduler")
                             (:file "model-context")
                             (:file "handlers")
                             (:file "server")))))

(asdf:defsystem "leadscorer/web/tests"
  :description "Suíte de testes Parachute da camada web do LeadScorer."
  :author "Polya Technologies"
  :license "Proprietary"
  :depends-on ("leadscorer/web" "parachute" "flexi-streams")
  :serial t
  :components ((:module "tests/web"
                :components ((:file "main")
                             (:file "view")
                             (:file "render")
                             (:file "session")
                             (:file "queries")
                             (:file "opportunities")
                             (:file "handlers")
                             (:file "integration")
                             (:file "scheduler"))))
  :perform (asdf:test-op (op c)
             (declare (ignore op c))
             (let ((result (uiop:symbol-call :parachute :test :leadscorer/web/tests)))
               (unless (eq (uiop:symbol-call :parachute :status result) :passed)
                 (error "A suíte de testes da camada web do LeadScorer falhou.")))))
