;;;; config.lisp --- Configuração de ambiente da camada web do LeadScorer.

(in-package #:leadscorer/web)

;;; A configuração operacional (portas de escuta, endereço de vínculo e raiz
;;; dos ativos estáticos) é lida de variáveis de ambiente, com valores padrão
;;; de desenvolvimento. Nenhum segredo é lido aqui; as credenciais do banco
;;; permanecem confinadas a 'src/db.lisp' e às variáveis PG*.

(defun env-integer (name default)
  "Retorna o inteiro da variável de ambiente NAME ou DEFAULT quando ausente ou
vazia. Sinaliza um erro quando o valor presente não é um inteiro, de modo que
uma configuração inválida falhe de imediato em vez de silenciosamente."
  (let ((value (uiop:getenv name)))
    (if (or (null value) (string= value ""))
        default
        (handler-case (parse-integer value)
          (error ()
            (error "A variável de ambiente ~A não é um inteiro válido: ~S."
                   name value))))))

(defun env-string (name default)
  "Retorna o valor da variável de ambiente NAME ou DEFAULT quando ausente ou
vazia."
  (let ((value (uiop:getenv name)))
    (if (or (null value) (string= value ""))
        default
        value)))

(defun env-flag (name)
  "Retorna T quando a variável de ambiente NAME denota verdadeiro (valores '1',
'true', 'yes' ou 'on', insensível à caixa) e NIL caso contrário ou quando
ausente. Codifica a convenção de sinalizador booleano por ambiente do projeto."
  (let ((value (string-downcase (env-string name ""))))
    (and (member value '("1" "true" "yes" "on") :test #'string=) t)))

(defun agent-port ()
  "Porta de escuta da aplicação do agente (LEADSCORER_AGENT_PORT, padrão 8081)."
  (env-integer "LEADSCORER_AGENT_PORT" 8081))

(defun manager-port ()
  "Porta de escuta da aplicação do gerente (LEADSCORER_MANAGER_PORT, padrão
8082)."
  (env-integer "LEADSCORER_MANAGER_PORT" 8082))

(defun bind-address ()
  "Endereço de vínculo dos servidores (LEADSCORER_BIND_ADDRESS, padrão
127.0.0.1, restrito ao laço local no desenvolvimento)."
  (env-string "LEADSCORER_BIND_ADDRESS" "127.0.0.1"))

(defun static-root ()
  "Diretório físico dos ativos estáticos servidos sob '/assets/', a saber,
'src/web/static/' relativo à raiz do sistema."
  (asdf:system-relative-pathname :leadscorer/web "src/web/static/"))

(defun debug-mode ()
  "Retorna T quando o modo de depuração do servidor está habilitado, lido de
LEADSCORER_DEBUG (valores '1', 'true', 'yes' ou 'on', insensível à caixa). O
padrão é NIL: em produção e na execução conteinerizada, um erro de handler
retorna 500 em vez de invocar o depurador, que sob '--non-interactive'
encerraria a thread. O desenvolvimento pode habilitá-lo explicitamente."
  (env-flag "LEADSCORER_DEBUG"))

(defun cookie-secure-p ()
  "Retorna T quando o atributo Secure do cookie de sessão deve ser habilitado,
lido de LEADSCORER_COOKIE_SECURE. O padrão é NIL, adequado ao desenvolvimento
sobre HTTP; na implantação sob TLS deve ser habilitado para o cookie de sessão
não trafegar em canal em claro."
  (env-flag "LEADSCORER_COOKIE_SECURE"))
