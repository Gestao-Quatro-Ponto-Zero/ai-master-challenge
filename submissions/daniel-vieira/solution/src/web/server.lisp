;;;; server.lisp --- Construção e ciclo de vida das duas aplicações web.

(in-package #:leadscorer/web)

;;; As duas aplicações, do agente e do gerente, são apps Ningle distintos,
;;; servidos por handlers Clack/Hunchentoot em portas próprias, no mesmo
;;; processo. A segregação é imposta no servidor pelo portão de autorização por
;;; papel (fail-closed) e reforçada por nomes de cookie de sessão distintos por
;;; aplicação: como os cookies são escopados por host, e não por porta, dois
;;; apps no mesmo host precisam de nomes de cookie próprios para não se
;;; sobrescreverem. Cada app é envolvido pela mesma pilha de middleware: o
;;; cabeçalho de segurança (CSP estrita e nosniff) no topo, cobrindo inclusive
;;; os ativos e as respostas de erro; a seguir os ativos estáticos sob
;;; '/assets/'; e a sessão.

(defparameter +content-security-policy+
  (concatenate 'string
               "default-src 'none'; script-src 'self'; style-src 'self'; "
               "connect-src 'self'; font-src 'self'; img-src 'self'; "
               "base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
  "Política de segurança de conteúdo estrita. Autoriza apenas ativos e conexões
de mesma origem; dispensa 'unsafe-inline' e 'unsafe-eval' porque o CSS e o HTMX
são servidos como ativos estáticos e o HTMX opera com 'allowEval' em falso. O
'connect-src 'self'' habilita as requisições XHR de mesma origem do HTMX, que é
o mecanismo central desta aplicação (ADR D2K9).")

(defun add-security-headers (response)
  "Acrescenta a CSP estrita e 'X-Content-Type-Options: nosniff' aos cabeçalhos
de RESPONSE, uma resposta Clack (status cabeçalhos corpo)."
  (destructuring-bind (status headers body) response
    (list status
          (append headers
                  (list :content-security-policy +content-security-policy+
                        :x-content-type-options "nosniff"))
          body)))

(defun security-headers-middleware (app)
  "Middleware Lack que aplica os cabeçalhos de segurança a toda resposta de
APP."
  (lambda (env)
    (add-security-headers (funcall app env))))

(defun make-app (role)
  "Constrói a aplicação web do papel ROLE (:agent ou :manager): um app Ningle
com as rotas de login, logout e home, envolvido pela pilha de middleware de
segurança, ativos estáticos e sessão. Retorna o app Clack funcallable."
  (let ((app (make-instance 'ningle:app))
        ;; Nome de cookie distinto por aplicação: cookies são escopados por
        ;; host, não por porta, de modo que dois apps no mesmo host se
        ;; sobrescreveriam sob um nome comum, deslogando um ao usar o outro.
        (cookie-key (ecase role
                      (:agent "lack.session.agent")
                      (:manager "lack.session.manager"))))
    (setf (ningle:route app "/login" :method :get)
          (lambda (params)
            (declare (ignore params))
            (login-page-response role)))
    (setf (ningle:route app "/login" :method :post)
          (lambda (params)
            (login-submit-for role (session-table) params)))
    (setf (ningle:route app "/logout" :method :post)
          (lambda (params)
            (declare (ignore params))
            (logout-response-for (session-table))))
    (setf (ningle:route app "/" :method :get)
          (lambda (params)
            (declare (ignore params))
            (home-response-for role (session-table))))
    ;; Rotas do ciclo de engajamento, exclusivas da aplicacao do agente. A do
    ;; gerente mantem apenas login, logout e home ate a Fase 6.
    (when (eq role :agent)
      (setf (ningle:route app "/disponiveis" :method :get)
            (lambda (params)
              (available-for role (session-table) params)))
      (setf (ningle:route app "/engajadas" :method :get)
            (lambda (params)
              (engaged-for role (session-table) params)))
      (setf (ningle:route app "/engajar/justificar" :method :get)
            (lambda (params)
              (justify-modal-for role (session-table) params)))
      (setf (ningle:route app "/engajar" :method :post)
            (lambda (params)
              (engage-for role (session-table) params (hx-request-p))))
      (setf (ningle:route app "/desfecho" :method :post)
            (lambda (params)
              (outcome-for role (session-table) params (hx-request-p))))
      (setf (ningle:route app "/modal/fechar" :method :get)
            (lambda (params)
              (declare (ignore params))
              (modal-close-response))))
    ;; Rota de acompanhamento, exclusiva da aplicacao do gerente. Somente leitura:
    ;; nenhuma rota de mutacao do ciclo e registrada para o gerente.
    (when (eq role :manager)
      (setf (ningle:route app "/acompanhamento" :method :get)
            (lambda (params)
              (acompanhamento-for role (session-table) params))))
    (lack:builder
     #'security-headers-middleware
     (:static :path "/assets/" :root (static-root))
     ;; Cookie de sessão endurecido: HttpOnly impede o acesso por script e
     ;; SameSite=Lax mitiga CSRF. Secure é dirigido por ambiente (COOKIE-SECURE-P,
     ;; via LEADSCORER_COOKIE_SECURE): falso por padrão no desenvolvimento sobre
     ;; HTTP e habilitado na implantação sob TLS. O nome do cookie é próprio de
     ;; cada app (ver COOKIE-KEY acima).
     (:session :state (lack/session/state/cookie:make-cookie-state
                       :httponly t :samesite :lax :secure (cookie-secure-p)
                       :cookie-key cookie-key))
     app)))

(defun make-agent-app ()
  "Constrói a aplicação do agente."
  (make-app :agent))

(defun make-manager-app ()
  "Constrói a aplicação do gerente."
  (make-app :manager))

(defvar *agent-app* nil
  "A aplicação Clack do agente em execução, ou NIL quando parada.")

(defvar *manager-app* nil
  "A aplicação Clack do gerente em execução, ou NIL quando parada.")

(defvar *agent-handler* nil
  "O handler Clack do servidor do agente, ou NIL quando parado.")

(defvar *manager-handler* nil
  "O handler Clack do servidor do gerente, ou NIL quando parado.")

(defun start (&key (agent-port (agent-port)) (manager-port (manager-port))
                   (address (bind-address)) (debug (debug-mode)))
  "Inicia os dois servidores, do agente e do gerente, em portas distintas,
vinculados a ADDRESS. Quando DEBUG é NIL (padrão), um erro de handler retorna
500 em vez de invocar o depurador. Sinaliza um erro se já estiverem em
execução. Retorna, como valores, as duas portas."
  (when (or *agent-handler* *manager-handler*)
    (error "Os servidores já estão em execução; chame STOP antes de reiniciar."))
  (setf *agent-app* (make-agent-app)
        *manager-app* (make-manager-app))
  (setf *agent-handler*
        (clack:clackup *agent-app* :server :hunchentoot
                                   :port agent-port :address address
                                   :use-thread t :debug debug))
  ;; Se a subida do gerente falhar, desfaz a do agente para não deixar um
  ;; handler órfão que bloquearia uma nova tentativa (a partida é tudo ou nada).
  (let ((started nil))
    (unwind-protect
         (progn
           (setf *manager-handler*
                 (clack:clackup *manager-app* :server :hunchentoot
                                              :port manager-port :address address
                                              :use-thread t :debug debug))
           (setf started t))
      (unless started
        (clack:stop *agent-handler*)
        (setf *agent-handler* nil *agent-app* nil *manager-app* nil))))
  ;; Com os dois servidores no ar, sobe o agendador do ciclo. Uma falha do
  ;; agendador (config invalida ou CSV derivados ausentes) e degradada para um
  ;; aviso, sem derrubar o servico web (ver START-SCHEDULER).
  (start-scheduler)
  (values agent-port manager-port))

(defun stop ()
  "Para os dois servidores, se em execução, e zera os handlers, apos parar o
agendador do ciclo. Idempotente."
  (stop-scheduler)
  (when *agent-handler*
    (clack:stop *agent-handler*)
    (setf *agent-handler* nil *agent-app* nil))
  (when *manager-handler*
    (clack:stop *manager-handler*)
    (setf *manager-handler* nil *manager-app* nil))
  (values))
