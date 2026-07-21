;;;; integration.lisp --- Teste de integração em processo da pilha web.

(in-package #:leadscorer/web/tests)

;;; SB-POSIX provê SETENV/UNSETENV, usados pelos testes que exercitam a leitura
;;; de configuração por variável de ambiente (o atributo Secure do cookie).
(eval-when (:compile-toplevel :load-toplevel :execute)
  (require "SB-POSIX"))

;;; Este teste exercita a pilha real de middleware (cabeçalho de segurança,
;;; ativos estáticos e sessão do Lack) e o roteamento Ningle, chamando o app
;;; Clack embrulhado em processo, sem abrir portas nem cliente HTTP. Fecha a
;;; lacuna que os testes de lógica '-for' não cobrem: a persistência da sessão
;;; com Set-Cookie, a forma dos parâmetros POST entregue pelo Ningle e a
;;; resolução dos ativos estáticos. As consultas ao banco são substituídas por
;;; indireções vinculadas, de modo que o teste dispensa PostgreSQL.

(defun make-env (method path &key cookie body hx)
  "Constrói um ambiente Clack mínimo para METHOD e PATH, com um cabeçalho de
cookie COOKIE opcional, um corpo urlencoded BODY opcional (para POST) e, quando HX,
o cabeçalho 'HX-Request' que sinaliza uma troca parcial do HTMX."
  (let ((headers (make-hash-table :test 'equal)))
    (when cookie (setf (gethash "cookie" headers) cookie))
    (when hx (setf (gethash "hx-request" headers) "true"))
    (let ((env (list :request-method method :script-name "" :path-info path
                     :server-name "localhost" :server-port 8081
                     :server-protocol :http/1.1 :request-uri path
                     :url-scheme "http" :remote-addr "127.0.0.1"
                     :query-string "" :headers headers)))
      (when body
        (let ((octets (sb-ext:string-to-octets body :external-format :utf-8)))
          (setf (gethash "content-type" headers) "application/x-www-form-urlencoded")
          (setf env (append env
                            (list :content-type "application/x-www-form-urlencoded"
                                  :content-length (length octets)
                                  :raw-body (flexi-streams:make-in-memory-input-stream
                                             octets))))))
      env)))

(defun cookie-header-from (response)
  "Extrai o par 'nome=valor' do cabeçalho Set-Cookie de RESPONSE, apto a ser
reenviado como cabeçalho Cookie, ou NIL quando ausente."
  (let ((set-cookie (getf (second response) :set-cookie)))
    (when set-cookie
      (subseq set-cookie 0 (position #\; set-cookie)))))

(defun body-string (response)
  "Decodifica o corpo de RESPONSE em string. Trata o corpo em octetos das
respostas de HTML e a lista de strings de outras respostas."
  (let ((body (third response)))
    (typecase body
      ((vector (unsigned-byte 8)) (sb-ext:octets-to-string body :external-format :utf-8))
      (list (apply #'concatenate 'string (remove-if-not #'stringp body)))
      (string body)
      (t ""))))

(define-test web-stack-round-trip-in-process
  "Percorre login, home autenticada, papel cruzado e logout pela pilha real."
  (let ((leadscorer/web::*lookup-user-fn*
          (lambda (role username)
            (if (and (eq role :agent) (string= username "anna.snelling")) 42 nil)))
        (leadscorer/web::*list-usernames-fn*
          (lambda (role) (declare (ignore role)) *sample-usernames*))
        ;; As consultas de oportunidade sao substituidas por fixtures, de modo que a
        ;; home e as listas do agente rendam sem PostgreSQL.
        (leadscorer/web::*list-prospecting-fn*
          (lambda (agent) (declare (ignore agent)) (list (sample-available-row))))
        (leadscorer/web::*list-engaged-fn*
          (lambda (agent) (declare (ignore agent)) '()))
        (leadscorer/web::*agent-kpis-fn*
          (lambda (agent) (declare (ignore agent)) (sample-kpis)))
        (leadscorer/web::*web-model* nil)
        (agent (leadscorer/web::make-agent-app))
        (manager (leadscorer/web::make-manager-app)))
    ;; 1) A tela de login é servida com o markup e os usuários semeados.
    (let ((r (funcall agent (make-env :get "/login"))))
      (is = 200 (first r))
      (true (search "text/html" (getf (second r) :content-type)))
      (true (search "content-security-policy"
                    (string-downcase (format nil "~{~a ~}" (second r)))))
      (let ((html (body-string r)))
        (true (search "Aplicação do agente" html))
        (true (search "value=anna.snelling" html))))
    ;; 2) O ativo estático é resolvido pela middleware de estáticos.
    (let ((r (funcall agent (make-env :get "/assets/app.css"))))
      (is = 200 (first r))
      (true (search "text/css" (getf (second r) :content-type))))
    ;; 3) A home sem sessão é negada por padrão (fail-closed).
    (let ((r (funcall agent (make-env :get "/"))))
      (is = 302 (first r))
      (is equal "/login" (getf (second r) :location)))
    ;; 3b) As rotas do ciclo também são negadas sem sessão (deny-by-default).
    (let ((r (funcall agent (make-env :get "/disponiveis"))))
      (is = 302 (first r))
      (is equal "/login" (getf (second r) :location)))
    ;; 4) O login válido grava a sessão e emite o cookie próprio do app.
    (let* ((r (funcall agent (make-env :post "/login" :body "user=anna.snelling")))
           (cookie (cookie-header-from r)))
      (is = 302 (first r))
      (is equal "/" (getf (second r) :location))
      (true (and cookie (search "lack.session.agent" cookie)))
      ;; 5) A home autenticada é servida e traz o nome de usuário e o top tier.
      (let ((h (funcall agent (make-env :get "/" :cookie cookie))))
        (is = 200 (first h))
        (let ((html (body-string h)))
          (true (search "anna.snelling" html))
          (true (search "Meu top tier" html))
          (true (search "Golddex" html))))
      ;; 5b) As telas de disponíveis e engajadas do agente são servidas.
      (let ((d (funcall agent (make-env :get "/disponiveis" :cookie cookie))))
        (is = 200 (first d))
        (true (search "Oportunidades disponiveis" (body-string d)))
        (true (search "Golddex" (body-string d))))
      (let ((e (funcall agent (make-env :get "/engajadas" :cookie cookie))))
        (is = 200 (first e))
        (true (search "Minhas oportunidades engajadas" (body-string e))))
      ;; 7) O logout limpa a sessão; a home volta a ser negada com o mesmo cookie.
      (let ((out (funcall agent (make-env :post "/logout" :cookie cookie))))
        (is = 302 (first out))
        (is equal "/login" (getf (second out) :location)))
      (let ((after (funcall agent (make-env :get "/" :cookie cookie))))
        (is = 302 (first after))
        (is equal "/login" (getf (second after) :location))))
    ;; 6) Segregação: o mesmo nome de agente é recusado no app do gerente.
    (let ((r (funcall manager (make-env :post "/login" :body "user=anna.snelling"))))
      (is = 200 (first r))
      (is eql nil (getf (second r) :location)))))

;;; --- Aplicacao do gerente: handlers e round-trip (sem PostgreSQL) ---

(defun manager-team-cycles-fixture ()
  "Dois ciclos crus do time (aberto de ann, won de bob), como a consulta os retornaria,
para os testes do gerente sem banco. O handler os enriquece."
  (list (list :engagement-id 1 :agent-username "ann" :account "Golddex"
              :product "GTX Plus Pro" :series "GTX" :overall 88 :engaged-at 100
              :closed-at nil :outcome nil :expired nil :justification-code nil
              :close-value-amount nil :close-value-currency nil)
        (list :engagement-id 2 :agent-username "bob" :account "Zumgoity"
              :product "GTX Plus Pro" :series "GTX" :overall 91 :engaged-at 100
              :closed-at 200 :outcome "won" :expired nil :justification-code nil
              :close-value-amount 548200 :close-value-currency "USD")))

(defun manager-team-agents-fixture ()
  "Dois agentes do time, como a consulta os retornaria."
  (list (list :id 1 :name "Ann" :username "ann")
        (list :id 2 :name "Bob" :username "bob")))

(define-test acompanhamento-authorization-and-filter
  "O acompanhamento exige sessao de gerente e aplica os filtros de PARAMS."
  (let ((manager-table (fresh-session))
        (agent-table (fresh-session))
        (empty (fresh-session))
        (leadscorer/web::*team-agents-fn*
          (lambda (id) (declare (ignore id)) (manager-team-agents-fixture)))
        (leadscorer/web::*team-cycles-fn*
          (lambda (id) (declare (ignore id)) (manager-team-cycles-fixture)))
        (leadscorer/web::*web-model* nil)
        (leadscorer/web::*scheduler-model* nil))
    (leadscorer/web::session-put manager-table 9 :manager "m1")
    (leadscorer/web::session-put agent-table 42 :agent "ann")
    ;; Papel cruzado (agente) e sessao vazia: negados por padrao.
    (is = 302 (response-status
               (leadscorer/web::acompanhamento-for :manager agent-table nil)))
    (is = 302 (response-status
               (leadscorer/web::acompanhamento-for :manager empty nil)))
    ;; Papel correto: 200, com os dois ciclos e o contador do time.
    (let ((full (body-string
                 (leadscorer/web::acompanhamento-for :manager manager-table nil))))
      (true (search "Acompanhamento do time" full))
      (true (search "Golddex" full))
      (true (search "Zumgoity" full))
      (true (search "em curso" full))
      (true (search "ciclos" full)))
    ;; Filtro por agente 'ann': Golddex presente, Zumgoity ausente.
    (let ((filtered (body-string
                     (leadscorer/web::acompanhamento-for
                      :manager manager-table '(("agent" . "ann"))))))
      (true (search "Golddex" filtered))
      (false (search "Zumgoity" filtered)))
    ;; Filtro por desfecho 'won': Zumgoity presente, Golddex (aberto) ausente.
    (let ((won (body-string
                (leadscorer/web::acompanhamento-for
                 :manager manager-table '(("outcome" . "won"))))))
      (true (search "Zumgoity" won))
      (false (search "Golddex" won)))))

(define-test manager-stack-round-trip-in-process
  "Percorre o login do gerente, a home do time, o acompanhamento e a segregacao (as
rotas de mutacao do agente estao ausentes na aplicacao do gerente) pela pilha real."
  (let ((leadscorer/web::*lookup-user-fn*
          (lambda (role username)
            (if (and (eq role :manager) (string= username "dustin.brinkmann")) 9 nil)))
        (leadscorer/web::*list-usernames-fn*
          (lambda (role) (declare (ignore role)) '("dustin.brinkmann")))
        (leadscorer/web::*team-kpis-fn*
          (lambda (id) (declare (ignore id)) (sample-kpis)))
        (leadscorer/web::*team-agents-fn*
          (lambda (id) (declare (ignore id)) (manager-team-agents-fixture)))
        (leadscorer/web::*team-engaged-fn*
          (lambda (id) (declare (ignore id))
            (list (list :opportunity-id 5 :agent-username "anna.snelling"
                        :account "Golddex" :product "GTX Plus Pro" :overall 88
                        :engaged-at 100 :justification-code nil))))
        (leadscorer/web::*team-cycles-fn*
          (lambda (id) (declare (ignore id)) (manager-team-cycles-fixture)))
        (leadscorer/web::*web-model* nil)
        (leadscorer/web::*scheduler-model* nil)
        (manager (leadscorer/web::make-manager-app)))
    ;; Login do gerente grava a sessao e o cookie proprio do app.
    (let* ((r (funcall manager (make-env :post "/login" :body "user=dustin.brinkmann")))
           (cookie (cookie-header-from r)))
      (is = 302 (first r))
      (true (and cookie (search "lack.session.manager" cookie)))
      ;; Home do time: faixa de KPI e destaque das engajadas do time.
      (let ((h (funcall manager (make-env :get "/" :cookie cookie))))
        (is = 200 (first h))
        (let ((html (body-string h)))
          (true (search "Desempenho do time" html))
          (true (search "Engajadas do meu time" html))
          (true (search "Golddex" html))))
      ;; Acompanhamento: cabecalho, contador e os badges de estado.
      (let ((a (funcall manager (make-env :get "/acompanhamento" :cookie cookie))))
        (is = 200 (first a))
        (let ((html (body-string a)))
          (true (search "Acompanhamento do time" html))
          (true (search "badge open" html))
          (true (search "badge won" html))))
      ;; Segregacao: as rotas de mutacao do agente NAO existem no app do gerente.
      (let ((eng (funcall manager (make-env :post "/engajar" :cookie cookie
                                            :body "opp=1&origem=available")))
            (dsf (funcall manager (make-env :post "/desfecho" :cookie cookie
                                            :body "opp=1&acao=won"))))
        (is = 404 (first eng))
        (is = 404 (first dsf))))))

(define-test agent-engagement-flow-in-process
  "Percorre o ciclo do agente pela pilha real: login, engajar (top tier, direto, via
HTMX), lista de engajadas e desfecho won, verificando as transicoes de estado no banco.
Exige PostgreSQL e o modelo derivado (para o relogio virtual)."
  (if (leadscorer::database-reachable-p)
      (let ((model (handler-case (leadscorer:load-model) (error () nil))))
        (if (null model)
            (skip "Modelo derivado ausente; fluxo de engajamento ignorado.")
            (let ((ids (leadscorer:with-database
                         (leadscorer:run-migrations)
                         (setup-web-opps))))
              (let ((leadscorer::*virtual-t0* (leadscorer:now-unix-ms))
                    (leadscorer/web::*web-model* model)
                    (leadscorer/web::*scheduler-model* nil)
                    (app (leadscorer/web::make-agent-app))
                    (op-gtx (getf ids :op-gtx))
                    (agent-id (getf ids :agent)))
                (let* ((r (funcall app (make-env :post "/login" :body "user=ann")))
                       (cookie (cookie-header-from r)))
                  (is = 302 (first r))
                  ;; A op-gtx (Acme x GTX Basic) consta das disponiveis.
                  (let ((d (funcall app (make-env :get "/disponiveis" :cookie cookie))))
                    (is = 200 (first d))
                    (true (search "Acme" (body-string d))))
                  ;; Engajar a op-gtx (unica disponivel, logo top tier, direto), por HTMX:
                  ;; a resposta e o fragmento da lista.
                  (let ((e (funcall app (make-env :post "/engajar" :cookie cookie :hx t
                                                  :body (format nil "opp=~D&origem=available"
                                                                op-gtx)))))
                    (is = 200 (first e))
                    (true (search "opp-list" (body-string e))))
                  ;; O estado transicionou para engajada pelo agente.
                  (leadscorer:with-database
                    (is equal "engaging"
                        (postmodern:query
                         "SELECT status FROM opportunities WHERE id = $1" op-gtx :single))
                    (is = agent-id
                        (postmodern:query
                         "SELECT engaged_by_id FROM opportunities WHERE id = $1"
                         op-gtx :single)))
                  ;; A op-gtx passa a constar das engajadas.
                  (let ((g (funcall app (make-env :get "/engajadas" :cookie cookie))))
                    (is = 200 (first g))
                    (true (search "GTX Basic" (body-string g))))
                  ;; Desfecho won por HTMX: o ciclo fecha com o preco de tabela (550) e a
                  ;; oportunidade volta a prospecting.
                  (let ((w (funcall app (make-env :post "/desfecho" :cookie cookie :hx t
                                                  :body (format nil "opp=~D&acao=won"
                                                                op-gtx)))))
                    (is = 200 (first w)))
                  (leadscorer:with-database
                    (is equal "prospecting"
                        (postmodern:query
                         "SELECT status FROM opportunities WHERE id = $1" op-gtx :single))
                    (is = 1
                        (postmodern:query
                         "SELECT COUNT(*) FROM engagements
                          WHERE opportunity_id = $1 AND outcome = 'won'
                            AND close_value_amount = 550"
                         op-gtx :single))))))))
      (skip "PostgreSQL indisponivel; fluxo de engajamento ignorado.")))

(define-test cookie-secure-p-reads-environment
  "COOKIE-SECURE-P segue LEADSCORER_COOKIE_SECURE: NIL por padrao, T para os
valores verdadeiros reconhecidos e NIL para valores falsos ou vazio."
  (unwind-protect
       (progn
         (sb-posix:unsetenv "LEADSCORER_COOKIE_SECURE")
         (is eql nil (leadscorer/web::cookie-secure-p))
         (sb-posix:setenv "LEADSCORER_COOKIE_SECURE" "1" 1)
         (is eql t (leadscorer/web::cookie-secure-p))
         (sb-posix:setenv "LEADSCORER_COOKIE_SECURE" "TRUE" 1)
         (is eql t (leadscorer/web::cookie-secure-p))
         (sb-posix:setenv "LEADSCORER_COOKIE_SECURE" "off" 1)
         (is eql nil (leadscorer/web::cookie-secure-p))
         (sb-posix:setenv "LEADSCORER_COOKIE_SECURE" "" 1)
         (is eql nil (leadscorer/web::cookie-secure-p)))
    (sb-posix:unsetenv "LEADSCORER_COOKIE_SECURE")))

(define-test session-cookie-secure-attribute-is-env-driven
  "O atributo Secure do Set-Cookie de sessao e dirigido por LEADSCORER_COOKIE_SECURE:
presente quando habilitado, ausente por padrao. O app le a configuracao ao ser
construido, de modo que cada ramo constroi um app sob o ambiente pretendido."
  (let ((leadscorer/web::*lookup-user-fn*
          (lambda (role username)
            (if (and (eq role :agent) (string= username "anna.snelling")) 42 nil)))
        (leadscorer/web::*list-usernames-fn*
          (lambda (role) (declare (ignore role)) *sample-usernames*))
        (leadscorer/web::*web-model* nil))
    (unwind-protect
         (progn
           ;; Habilitado: o Set-Cookie carrega o atributo '; secure'.
           (sb-posix:setenv "LEADSCORER_COOKIE_SECURE" "1" 1)
           (let* ((app (leadscorer/web::make-agent-app))
                  (r (funcall app (make-env :post "/login" :body "user=anna.snelling")))
                  (set-cookie (getf (second r) :set-cookie)))
             (is = 302 (first r))
             (true (search "; secure" (string-downcase set-cookie))))
           ;; Padrao (variavel ausente): o Set-Cookie nao carrega o atributo secure.
           (sb-posix:unsetenv "LEADSCORER_COOKIE_SECURE")
           (let* ((app (leadscorer/web::make-agent-app))
                  (r (funcall app (make-env :post "/login" :body "user=anna.snelling")))
                  (set-cookie (getf (second r) :set-cookie)))
             (is = 302 (first r))
             (false (search "; secure" (string-downcase set-cookie)))))
      (sb-posix:unsetenv "LEADSCORER_COOKIE_SECURE"))))
