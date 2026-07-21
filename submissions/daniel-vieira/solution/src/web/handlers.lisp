;;;; handlers.lisp --- Respostas e lógica de rota das aplicações web.

(in-package #:leadscorer/web)

;;; A lógica de cada rota reside em funções núcleo com sufixo '-for', que
;;; recebem a tabela de sessão explicitamente e, portanto, são testáveis sem
;;; servidor nem banco (vinculando '*list-usernames-fn*' e '*lookup-user-fn*').
;;; Os finos invólucros de rota Ningle, em 'server.lisp', apenas fornecem a
;;; tabela de sessão corrente via 'session-table'.

(defun html-response (html &optional (status 200))
  "Constrói uma resposta Clack de HTML a partir da string HTML, com o corpo
codificado em UTF-8 (octetos), de modo que os acentos do português sejam
transmitidos sem ambiguidade de codificação."
  (list status
        (list :content-type "text/html; charset=utf-8")
        (sb-ext:string-to-octets html :external-format :utf-8)))

(defun redirect (location &optional (status 302))
  "Constrói uma resposta Clack de redirecionamento para LOCATION."
  (list status (list :location location) (list "")))

(defun login-page-response (role &optional error-message)
  "Resposta da tela de login do papel ROLE, com os usuários semeados e, quando
fornecida, uma ERROR-MESSAGE."
  (html-response (render-login-page role (list-usernames role) error-message)))

(defun login-submit-for (role table params)
  "Processa a submissão do login do papel ROLE com os parâmetros PARAMS,
gravando a identidade na sessão TABLE e redirecionando à home quando a seleção
é válida para o papel, ou re-renderizando o login com erro caso contrário. A
validação é restrita ao papel, o que recusa um nome de usuário do papel oposto.
No sucesso, rotaciona o identificador de sessão (REGENERATE-SESSION-ID) para fechar
a janela de fixação de sessão na transição de privilégio."
  (let* ((username (cdr (assoc "user" params :test #'string=)))
         (id (and username (plusp (length username)) (lookup-user role username))))
    (if id
        (progn
          (session-put table id role username)
          (regenerate-session-id)
          (redirect "/"))
        (login-page-response
         role "Seleção inválida. Escolha um usuário da lista."))))

(defun logout-response-for (table)
  "Encerra a sessão TABLE e redireciona ao login."
  (when table (session-clear table))
  (redirect "/login"))

(defun call-with-authorized-user (role table function)
  "Portão de autorização fail-closed único das rotas: quando TABLE está autenticada e o seu
papel é ROLE, chama FUNCTION com o identificador e o nome de usuário da sessão (dois
argumentos) e devolve o seu resultado; caso contrário devolve um redirecionamento ao login.
Concentra a decisão de acesso num único ponto, de modo que uma rota nova não possa omiti-la
por cópia. As rotas específicas de um papel são montadas apenas nesse papel (ver
MAKE-APP), de modo que ROLE fixa o papel exigido."
  (if (and table (role-authorized-p table role))
      (multiple-value-bind (id session-role username) (session-user table)
        (declare (ignore session-role))
        (funcall function id username))
      (redirect "/login")))

(defun home-response-for (role table)
  "Resposta da tela inicial do papel ROLE quando a sessão TABLE está autorizada
para esse papel; caso contrário, redireciona ao login (portão de autenticação). No
papel de agente, apresenta a faixa de indicadores e o top tier; no de gerente, a faixa
agregada do time e o destaque das engajadas em curso do time."
  (call-with-authorized-user
   role table
   (lambda (id username)
     (if (eq role :agent)
         (multiple-value-bind (arranged cut) (agent-prospecting-arranged id)
           (declare (ignore cut))
           (html-response
            (render-agent-home-page
             username (agent-kpis id)
             (remove-if-not (lambda (row) (getf row :top-tier-p)) arranged))))
         (manager-home-response id username)))))

;;; --- Contexto de requisição e utilitários de parâmetro ---

(defun hx-request-p ()
  "Verdadeiro quando a requisição corrente traz o cabeçalho 'HX-Request', ou seja, é uma
troca parcial disparada pelo HTMX. Lê o ambiente da requisição corrente, seguindo a mesma
idiomática de SESSION-TABLE; por isso é chamada pelos invólucros de rota, não pelas
funções núcleo '-for', que permanecem testáveis sem servidor."
  (let ((headers (getf (lack/request:request-env ningle:*request*) :headers)))
    (and headers (gethash "hx-request" headers) t)))

(defun param (params name)
  "O valor do parâmetro NAME em PARAMS (alist de Ningle), ou NIL quando ausente."
  (cdr (assoc name params :test #'string=)))

(defun parse-opp (string)
  "O identificador inteiro de oportunidade em STRING, ou NIL quando STRING é nula ou não
representa um inteiro. Valida a entrada externa sem sinalizar erro (':junk-allowed')."
  (and string (values (parse-integer string :junk-allowed t))))

(defun sort-key-from (string options default)
  "A chave de ordenação de OPTIONS (alist chave . rótulo) cujo nome em minúsculas casa com
STRING, ou DEFAULT quando nenhuma casa."
  (or (loop for (key . nil) in options
            when (and string (string= string (string-downcase (symbol-name key))))
              return key)
      default))

(defun oob-modal (inner-html)
  "Um envelope out-of-band do HTMX que substitui '#modal' por INNER-HTML (string de HTML
já renderizado, ou vazia para fechar o modal). Concatenado à resposta principal, permite
atualizar a lista e o modal em uma só troca."
  (format nil "<div id=\"modal\" hx-swap-oob=\"true\">~A</div>" inner-html))

;;; --- Disponíveis: leitura, arranjo, filtros e fontes ---

(defun agent-prospecting-arranged (agent-id)
  "Busca as oportunidades disponíveis do agente AGENT-ID, enriquece-as com os campos do
modelo e as arranja com o rank e a marca de top tier. Retorna, como valores, as linhas
anotadas e o índice de corte sobre a ordem de ranqueamento."
  (let* ((rows (list-prospecting-for-agent agent-id))
         (model (current-model))
         (enriched (enrich-rows-with-model
                    rows (and model (ls:model-pair-context-index model)))))
    (arrange-available enriched)))

(defun available-filters (params)
  "O alist de filtros correntes da lista de disponíveis, lido de PARAMS."
  (list (cons :location (param params "location"))
        (cons :sector (param params "sector"))
        (cons :series (param params "series"))
        (cons :product (param params "product"))))

(defun available-sources (rows)
  "O alist de opções de filtro da lista de disponíveis, com os valores distintos de ROWS."
  (list (cons :location (distinct-values rows :location))
        (cons :sector (distinct-values rows :sector))
        (cons :series (distinct-values rows :series))
        (cons :product (distinct-values rows :product))))

(defun available-view (arranged params)
  "Aplica a ARRANGED (as disponíveis já anotadas e ordenadas por potencial) os filtros de
igualdade, o filtro por data de disponibilização (limiar inferior sobre ':available-at') e
a ordenação de PARAMS. Retorna, como valores, as linhas exibidas, o índice de corte (NIL
fora da ordem de potencial), a chave de ordenação (string), o alist de filtros de igualdade
e o valor corrente do filtro por data. Partilhada pela página completa e pelo fragmento
re-renderizado após uma ação, de modo que o recorte corrente seja preservado nas trocas
HTMX."
  (let* ((filters (available-filters params))
         (since (param params "available_since"))
         (sort (or (param params "sort") "overall"))
         (sort-key (sort-key-from sort +sort-options+ :overall))
         (filtered (apply-date-since (apply-filters arranged filters)
                                     :available-at since))
         (display (if (eq sort-key :overall) filtered (apply-sort filtered sort-key)))
         (cut (when (and (eq sort-key :overall) (plusp ls:*potential-cutoff*))
                (position-if
                 (lambda (row) (< (or (getf row :overall) 0) ls:*potential-cutoff*))
                 display))))
    (values display cut sort filters since)))

(defun available-for (role table params)
  "Resposta da lista de disponíveis do agente autorizado em TABLE, aplicando os filtros e a
ordenação de PARAMS (interatividade híbrida por GET). O corte só se aplica na ordem de
ranqueamento; em outra ordenação, a lista é plana, preservando o rank e o destaque."
  (call-with-authorized-user
   role table
   (lambda (id username)
     (multiple-value-bind (arranged cut) (agent-prospecting-arranged id)
       (declare (ignore cut))
       (multiple-value-bind (display display-cut sort filters since)
           (available-view arranged params)
         (html-response
          (render-available-page username display display-cut
                                 (available-sources arranged) filters sort
                                 (length arranged) since)))))))

;;; --- Engajadas: leitura, campos de exibição e ordenação ---

(defun enrich-engaged-display (rows model now)
  "Acrescenta a cada linha de ROWS os campos de exibição dependentes do relógio: o horário
real do engajamento (':engaged-display'), o instante real numérico do engajamento
(':engaged-real', base do filtro por data de engajamento, no eixo de tempo real), os
minutos reais a expirar (':expire-minutes'), o rótulo (':expire-label'), a marca de
proximidade (':expire-soon') e ':expiring-p', que indica a oportunidade já além do
horizonte (logicamente expirada, pendente do fechamento pelo agendador). MODEL/NOW nulos
degradam os campos para travessão e ':expiring-p' a NIL."
  (mapcar (lambda (row)
            (let* ((engaged (getf row :engaged-at))
                   (real (and model (ls:real-instant-of-virtual engaged model)))
                   (minutes (and model now
                                 (ceiling (ls:real-minutes-to-expiration
                                           engaged now model)))))
              (list* :engaged-display (format-datetime-ms real)
                     :engaged-real real
                     :expire-minutes minutes
                     :expire-label (format-expire minutes)
                     :expire-soon (expire-soon-p minutes)
                     :expiring-p (ls:engagement-expired-p engaged now model)
                     row)))
          rows))

(defun sort-engaged (rows key)
  "Ordena ROWS de engajadas pela chave KEY: ':expire' pelo menor tempo restante, ':overall'
pelo maior potencial, ':account' em ordem alfabética."
  (ecase key
    (:expire (sort (copy-list rows) #'<
                   :key (lambda (row) (or (getf row :expire-minutes)
                                          most-positive-fixnum))))
    (:overall (apply-sort rows :overall))
    (:account (apply-sort rows :account))))

(defun agent-engaged-enriched (agent-id)
  "As oportunidades engajadas do agente AGENT-ID, enriquecidas com os campos de exibição
dependentes do relógio, sem filtro nem ordenação."
  (let ((rows (list-engaged-for-agent agent-id)))
    (multiple-value-bind (model now) (current-model-and-now)
      (enrich-engaged-display rows model now))))

(defun engaged-view (enriched params)
  "Aplica a ENRICHED (as engajadas já enriquecidas) a ordenação, os filtros de igualdade e
o filtro por data de engajamento (limiar inferior sobre ':engaged-real') de PARAMS.
Retorna, como valores, as linhas exibidas, o alist de fontes de filtro, o alist de filtros
de igualdade, a chave de ordenação (string) e o valor corrente do filtro por data.
Partilhada pela página completa e pelo fragmento re-renderizado após um desfecho, de modo
que o recorte corrente seja preservado."
  (let* ((sort (or (param params "sort") "expire"))
         (sort-key (sort-key-from sort +engaged-sort-options+ :expire))
         (sorted (sort-engaged enriched sort-key))
         (since (param params "engaged_since"))
         (filters (list (cons :product (param params "product"))
                        (cons :series (param params "series"))
                        (cons :location (param params "location"))
                        (cons :sector (param params "sector"))))
         (shown (apply-date-since (apply-filters sorted filters) :engaged-real since))
         (sources (list (cons :product (distinct-values enriched :product))
                        (cons :series (distinct-values enriched :series))
                        (cons :location (distinct-values enriched :location))
                        (cons :sector (distinct-values enriched :sector)))))
    (values shown sources filters sort since)))

(defun engaged-for (role table params)
  "Resposta da lista de engajadas do agente autorizado em TABLE, com os filtros e a
ordenação de PARAMS."
  (call-with-authorized-user
   role table
   (lambda (id username)
     (let ((enriched (agent-engaged-enriched id)))
       (multiple-value-bind (shown sources filters sort since)
           (engaged-view enriched params)
         (html-response
          (render-engaged-page username shown sources filters sort
                               (length enriched) since)))))))

;;; --- Engajamento e desfecho: fragmentos e transições ---

(defun agent-list-fragment (agent-id origin params)
  "O fragmento de lista a re-renderizar após uma ação, conforme ORIGIN: 'home' devolve o
top tier; 'available' devolve a lista de disponíveis reaplicando os filtros e a ordenação de
PARAMS (incluídos na ação via 'hx-include' da barra de filtros), de modo que o recorte
corrente do usuário seja preservado."
  (multiple-value-bind (arranged cut) (agent-prospecting-arranged agent-id)
    (declare (ignore cut))
    (if (string= origin "home")
        (spinneret:with-html-string
          (render-top-tier-table
           (remove-if-not (lambda (row) (getf row :top-tier-p)) arranged)))
        (multiple-value-bind (display display-cut) (available-view arranged params)
          (spinneret:with-html-string (render-available-list display display-cut))))))

(defun engage-page-of (origin)
  "A rota de página cheia correspondente a ORIGIN, para o fallback sem HTMX."
  (if (string= origin "home") "/" "/disponiveis"))

(defun engage-response (hx origin agent-id params)
  "Resposta de sucesso do engajamento: sob HTMX, a lista re-renderizada (no recorte de
PARAMS) mais o fechamento out-of-band do modal; sem HTMX, um redirecionamento à origem."
  (if hx
      (html-response (concatenate 'string (agent-list-fragment agent-id origin params)
                                  (oob-modal "")))
      (redirect (engage-page-of origin))))

(defun engage-modal-response (hx origin agent-id row params)
  "Resposta que reabre o modal de justificativa (fora do top tier, sem justificativa),
sem engajar: a lista inalterada mais o modal out-of-band."
  (if hx
      (html-response (concatenate 'string (agent-list-fragment agent-id origin params)
                                  (oob-modal (spinneret:with-html-string
                                               (render-justification-modal row)))))
      (redirect (engage-page-of origin))))

(defun engage-limit-response (hx origin agent-id params)
  "Resposta do limite de engajamentos atingido: a lista inalterada mais o alerta de limite
out-of-band."
  (if hx
      (html-response (concatenate 'string (agent-list-fragment agent-id origin params)
                                  (oob-modal (spinneret:with-html-string
                                               (render-limit-alert)))))
      (redirect (engage-page-of origin))))

(defun justification-id-of (code)
  "O identificador da justificativa de código CODE, ou NIL quando CODE é nulo ou
desconhecido."
  (and code (getf (find code (justifications)
                        :key (lambda (j) (getf j :code)) :test #'equal)
                  :id)))

(defun justify-modal-for (role table params)
  "Fragmento do modal de justificativa para a oportunidade de PARAMS, quando o agente em
TABLE está autorizado. Localiza a linha na lista ranqueada do agente para compor o texto."
  (call-with-authorized-user
   role table
   (lambda (id username)
     (declare (ignore username))
     (let ((opp (parse-opp (param params "opp"))))
       (multiple-value-bind (arranged cut) (agent-prospecting-arranged id)
         (declare (ignore cut))
         (let ((row (find opp arranged
                          :key (lambda (r) (getf r :opportunity-id)))))
           (if row
               (html-response (spinneret:with-html-string
                                (render-justification-modal row)))
               (html-response (oob-modal "")))))))))

(defun engage-for (role table params hx)
  "Processa o engajamento de uma oportunidade pelo agente autorizado em TABLE. Impõe a
política de justificativa fora do top tier (reabrindo o modal quando falta) e carimba o
instante virtual corrente. Traduz as condições do serviço de domínio: limite atingido no
alerta, indisponibilidade na re-renderização. HX seleciona fragmento ou redirecionamento."
  (call-with-authorized-user
   role table
   (lambda (agent username)
     (declare (ignore username))
     (let ((opp (parse-opp (param params "opp")))
           (origin (or (param params "origem") "available"))
           (just-id (justification-id-of (param params "just"))))
       (multiple-value-bind (model now) (current-model-and-now)
         (declare (ignore model))
         (multiple-value-bind (arranged cut) (agent-prospecting-arranged agent)
           (declare (ignore cut))
           (let* ((row (find opp arranged
                             :key (lambda (r) (getf r :opportunity-id))))
                  (top (and row (getf row :top-tier-p))))
             (cond
               ;; NOW nulo indica que o relógio virtual não está ancorado (agendador
               ;; parado, por CSV derivados ausentes); nesse estado degradado o ciclo
               ;; inteiro está inoperante e as listas vêm vazias, de modo que a ação
               ;; apenas re-renderiza. É uma pré-condição de operação, não um erro
               ;; interativo.
               ((or (null opp) (null now))
                (engage-response hx origin agent params))
               ((and (not top) (null just-id))
                (engage-modal-response hx origin agent row params))
               (t
                (handler-case
                    (progn
                      (ls:with-database
                        (ls:engage-opportunity opp agent now :justification-id just-id))
                      (engage-response hx origin agent params))
                  (ls:engagement-limit-reached ()
                    (engage-limit-response hx origin agent params))
                  (ls:opportunity-not-available ()
                    (engage-response hx origin agent params))))))))))))

(defun outcome-response (hx agent-id params)
  "Resposta de um desfecho: sob HTMX, a lista de engajadas re-renderizada no recorte de
PARAMS (filtros e ordenação preservados); sem HTMX, um redirecionamento a '/engajadas'."
  (if hx
      (html-response (spinneret:with-html-string
                       (render-engaged-list
                        (engaged-view (agent-engaged-enriched agent-id) params))))
      (redirect "/engajadas")))

(defparameter *outcome-actions* '("won" "lost" "return")
  "As ações de desfecho válidas para uma oportunidade engajada.")

(defun outcome-for (role table params hx)
  "Processa o desfecho de uma oportunidade engajada pelo agente autorizado em TABLE: 'won',
'lost' ou devolução. Carimba o instante virtual corrente e tolera a indisponibilidade
(outro ator fechou o ciclo). Só toca o banco quando a ação é válida e o relógio está
ancorado. Re-renderiza a lista de engajadas."
  (call-with-authorized-user
   role table
   (lambda (agent username)
     (declare (ignore username))
     (let ((opp (parse-opp (param params "opp")))
           (acao (param params "acao")))
       (multiple-value-bind (model now) (current-model-and-now)
         (when (and opp now (member acao *outcome-actions* :test #'string=))
           (handler-case
               (ls:with-database
                 (cond ((string= acao "won") (ls:close-engagement opp agent :won now))
                       ((string= acao "lost") (ls:close-engagement opp agent :lost now))
                       ((string= acao "return") (ls:return-engagement opp agent now)))
                 ;; O reescore imediato faz a lista publica refletir o rebaixamento
                 ;; (won/lost) ou a permanencia (devolucao) sem esperar o proximo tique.
                 ;; E uma otimizacao interativa de melhor-esforco: o desfecho ja foi
                 ;; persistido em sua propria transacao e o agendador reescora no proximo
                 ;; tique, de modo que uma falha do reescore nao deve derrubar a resposta
                 ;; do desfecho ja concluido.
                 (handler-case (ls:rescore-opportunity opp model :now now)
                   (error (condition)
                     (format *error-output*
                             "~&Reescore interativo pos-desfecho falhou (oportunidade ~
                              ~A); o agendador reescora no proximo tique: ~A~%"
                             opp condition)
                     nil)))
             (ls:opportunity-not-available () nil)))
         (outcome-response hx agent params))))))

(defun modal-close-response ()
  "Resposta que esvazia o hospedeiro de modal, para os botões Cancelar e Fechar."
  (html-response ""))

;;; --- Aplicacao do gerente: tela inicial e acompanhamento (somente leitura) ---

(defun manager-home-response (id username)
  "Resposta da tela inicial do gerente ID (nome USERNAME): a faixa de indicadores
agregada do time e o destaque das engajadas em curso do time, enriquecidas com os campos
de exibicao dependentes do relogio virtual (horario real do engajamento e tempo a
expirar)."
  (multiple-value-bind (model now) (current-model-and-now)
    (let ((engaged (enrich-engaged-display (team-engaged id) model now)))
      (html-response
       (render-manager-home-page username (team-kpis id)
                                 (length (team-agents id)) engaged)))))

(defun enrich-cycles-display (rows model now)
  "Acrescenta a cada ciclo de ROWS os instantes reais de exibicao ':engaged-display' e
':closed-display', invertendo o relogio virtual (o engajamento e o fechamento sao
carimbados no tempo virtual), o instante real numerico do engajamento ':engaged-real'
(base do filtro por data, que opera no mesmo eixo real exibido ao gerente) e ':expiring-p'
para o ciclo aberto ja alem do horizonte (logicamente expirado, pendente do fechamento
pelo agendador). MODEL/NOW nulos degradam os campos; ':closed-display' e NIL quando o ciclo
esta aberto, exibido como travessao pela renderizacao."
  (mapcar (lambda (row)
            (let* ((engaged (getf row :engaged-at))
                   (closed (getf row :closed-at))
                   (real-engaged (and model (ls:real-instant-of-virtual engaged model)))
                   (real-closed (and model closed
                                     (ls:real-instant-of-virtual closed model))))
              (list* :engaged-display (format-datetime-ms real-engaged)
                     :engaged-real real-engaged
                     :closed-display (and closed (format-datetime-ms real-closed))
                     :expiring-p (and (null closed)
                                      (ls:engagement-expired-p engaged now model))
                     row)))
          rows))

(defun team-cycles-enriched (manager-id)
  "Os ciclos do time do gerente MANAGER-ID, enriquecidos com os instantes reais de
exibicao e a marca de expiracao logica, sem filtro nem ordenacao."
  (multiple-value-bind (model now) (current-model-and-now)
    (enrich-cycles-display (team-cycles manager-id) model now)))

(defun team-filters (params)
  "O alist de filtros correntes do acompanhamento, lido de PARAMS, por id de filtro."
  (list (cons :agent (param params "agent"))
        (cons :product (param params "product"))
        (cons :account (param params "account"))
        (cons :outcome (param params "outcome"))
        (cons :since (param params "since"))))

(defun acompanhamento-for (role table params)
  "Resposta da visao de acompanhamento do time do gerente autorizado em TABLE, aplicando os
filtros e a ordenacao de PARAMS (interatividade por GET de pagina inteira; a aplicacao do
gerente e somente leitura). Os contadores (em curso e total) refletem o time inteiro, antes
dos filtros."
  (call-with-authorized-user
   role table
   (lambda (id username)
     (let* ((enriched (team-cycles-enriched id))
            (agents (mapcar (lambda (agent) (getf agent :username)) (team-agents id)))
            (products (distinct-values enriched :product))
            (filters (team-filters params))
            (sort (or (param params "sort") "engaged"))
            (sort-key (sort-key-from sort +team-sort-options+ :engaged))
            (shown (apply-team-sort (apply-team-filters enriched filters) sort-key))
            ;; "Em curso" conta apenas os ciclos abertos genuinamente vivos: um ciclo
            ;; aberto ja alem do horizonte esta logicamente expirado (pendente do
            ;; fechamento pelo agendador) e nao e contado nem exibido como em curso.
            (open-count (count-if (lambda (row)
                                    (and (eq (cycle-state row) :open)
                                         (not (getf row :expiring-p))))
                                  enriched)))
       (html-response
        (render-acompanhamento-page username shown agents products filters sort
                                    open-count (length enriched)))))))
