;;;; render.lisp --- Layout base e páginas em Spinneret da camada web.

(in-package #:leadscorer/web)

;;; O layout base reproduz o chrome dos protótipos autônomos de
;;; '.claude/assets/examples/' (tema escuro Gray 100), servindo o CSS e o HTMX
;;; como ativos estáticos sob CSP estrita. Spinneret escapa o texto por padrão,
;;; de modo que os nomes de usuário vindos do banco são escapados sem ação
;;; adicional. As funções auxiliares emitem no fluxo Spinneret corrente
;;; ('spinneret:with-html'); as funções de página retornam a string completa
;;; ('spinneret:with-html-string').

(defparameter +htmx-config+
  "{\"allowEval\":false,\"includeIndicatorStyles\":false}"
  "Configuração do HTMX embutida como meta estática, não como script inline, de
modo a permanecer compatível com a CSP 'script-src 'self''. Desliga 'eval'
(dispensa 'unsafe-eval') e a injeção do estilo de indicador (que o
'style-src 'self'' bloquearia; o estilo reside em 'app.css').")

(defun role-scope (role)
  "Texto do escopo de aplicação exibido no chrome, por papel."
  (ecase role
    (:agent "Aplicação do agente")
    (:manager "Aplicação do gerente")))

(defun role-field-label (role)
  "Rótulo do campo de seleção de usuário, por papel."
  (ecase role
    (:agent "Agente de vendas")
    (:manager "Gerente de vendas")))

(defun role-placeholder (role)
  "Texto da opção inicial desabilitada do seletor, por papel."
  (ecase role
    (:agent "Escolha um agente")
    (:manager "Escolha um gerente")))

(defun role-context (role)
  "Substantivo do papel para títulos e sub-rótulos."
  (ecase role
    (:agent "agente")
    (:manager "gerente")))

(defun role-hint (role)
  "Nota recíproca informando que a outra aplicação é servida em endereço
próprio, com a mesma identificação, sem gestão de papéis."
  (ecase role
    (:agent
     "A aplicação do gerente é servida em endereço próprio, com a mesma forma
de identificação. As duas aplicações são segregadas, sem gestão de papéis.")
    (:manager
     "A aplicação do agente é servida em endereço próprio, com a mesma forma
de identificação. As duas aplicações são segregadas, sem gestão de papéis.")))

(defvar *app-css-version* nil
  "Versão memoizada do 'app.css' para cache-busting, o prefixo do hash de
conteúdo do arquivo servido. Computada preguiçosamente por APP-CSS-HREF, uma vez
por imagem, de modo que uma alteração do CSS (novo build) altere a versão e o
navegador rebusque o ativo.")

(defun app-css-href ()
  "Retorna o 'href' do 'app.css' com um sufixo de versão derivado do hash de
conteúdo do arquivo servido ('/assets/app.css?v=<hash>'), de modo que uma
alteração do CSS seja buscada pelo navegador sem hard-refresh. A versão é
computada uma vez e memoizada; a query-string é compatível com a CSP
'style-src 'self'' e ignorada pela middleware de ativos estáticos. Quando o
arquivo servido não pode ser lido, degrada para o 'href' sem versão, de modo que
a página renderize em vez de falhar."
  (let ((version
          (or *app-css-version*
              ;; A degradacao (leitura falha) nao e memoizada: mantendo
              ;; *APP-CSS-VERSION* em NIL, uma leitura posterior bem-sucedida ainda
              ;; produz o sufixo, em vez de cachear o href sem versao.
              (handler-case
                  (setf *app-css-version*
                        (subseq (leadscorer:content-checksum
                                 (uiop:read-file-string
                                  (merge-pathnames "app.css" (static-root))))
                                0 12))
                (file-error () nil)))))
    (if version
        (format nil "/assets/app.css?v=~A" version)
        "/assets/app.css")))

(defun render-head (title)
  "Emite o <head> comum: metadados, título, folha de estilo estática e a
configuração e o carregamento do HTMX como ativo estático."
  (spinneret:with-html
    (:head
     (:meta :charset "utf-8")
     (:meta :name "viewport" :content "width=device-width, initial-scale=1")
     (:title title)
     (:link :rel "stylesheet" :href (app-css-href))
     (:meta :name "htmx-config" :content +htmx-config+)
     (:script :src "/assets/htmx.min.js" :defer t))))

(defun render-footer ()
  "Emite o rodapé comum das páginas."
  (spinneret:with-html
    (:footer "LeadScorer --- MVP de classificação e priorização de leads")))

(defun render-appbar (role)
  "Emite a faixa superior mínima das telas de login, com o wordmark e o escopo
da aplicação."
  (spinneret:with-html
    (:header :class "appbar"
             (:span :class "wordmark" "LeadScorer")
             (:span :class "scope" (role-scope role)))))

(defun agent-tabs ()
  "As abas de navegação da aplicação do agente, como '(rótulo href chave)'."
  '(("Início" "/" :home)
    ("Oportunidades Disponíveis" "/disponiveis" :available)
    ("Oportunidades Engajadas" "/engajadas" :engaged)))

(defun manager-tabs ()
  "As abas de navegação da aplicação do gerente, como '(rótulo href chave)'."
  '(("Início" "/" :home)
    ("Acompanhamento" "/acompanhamento" :tracking)))

(defun render-nav-tabs (role active)
  "Emite as abas de navegação por papel, marcando ACTIVE. O agente tem as três abas
do ciclo; o gerente, a inicial e o acompanhamento do time."
  (spinneret:with-html
    (:div :class "nav-tabs"
          (dolist (tab (if (eq role :agent) (agent-tabs) (manager-tabs)))
            (destructuring-bind (label href key) tab
              (spinneret:with-html
                (:a :href href :class (when (eq key active) "active") label)))))))

(defun render-navbar (role username &optional (active :home))
  "Emite a barra de navegação autenticada, com o menu responsivo por alternância
CSS pura. O wordmark (com a tag de papel no gerente), as abas de navegação (com
ACTIVE marcada) e a pílula de status da aplicação residem no contêiner '.nav-menu',
que colapsa no menu-hambúrguer nas telas pequenas; o nome de usuário da sessão e o
botão de saída (formulário POST) permanecem visíveis na barra."
  (spinneret:with-html
    (:nav :class "navbar"
          (:input :type "checkbox" :id "nav" :class "nav-cb"
                  :aria-label "Abrir menu")
          (:label :class "nav-toggle" :for "nav"
                  (:span) (:span) (:span))
          (:div :class "nav-menu"
                (:span :class "brand" "LeadScorer"
                       (when (eq role :manager)
                         (spinneret:with-html (:span :class "role" "gerente"))))
                (render-nav-tabs role active)
                (:span :class "pill" (:span :class "dot") "Sessão ativa"))
          (:div :class "nav-right"
                (:span :class "user-pill" username)
                (:form :class "logout-form" :method "post" :action "/logout"
                       (:button :class "btn btn-sm" :type "submit" "Sair"))))))

(defun render-login-page (role usernames &optional error-message)
  "Retorna a string HTML da tela de identificação por seleção, por papel.
USERNAMES é a lista de nomes de usuário semeados a oferecer; ERROR-MESSAGE,
quando fornecida, é exibida acima do formulário. O formulário submete por POST
a '/login'."
  (spinneret:with-html-string
    (:doctype)
    (:html :lang "pt-BR"
           (render-head (format nil "LeadScorer --- Identificação (~A)"
                                (role-context role)))
           (:body
            (render-appbar role)
            (:main :class "login-main"
                   (:div :class "card"
                         (:h1 "Identificação")
                         (:p :class "lead"
                             "Selecione o seu nome de usuário para iniciar a "
                             "sessão. O acesso é por seleção, sem senha, "
                             "restrito aos usuários semeados.")
                         (when error-message
                           (spinneret:with-html
                             (:p :class "error" error-message)))
                         (:form :method "post" :action "/login"
                                (:div :class "field"
                                      (:label :for "user" (role-field-label role))
                                      (:span :class "select"
                                             (:select :id "user" :name "user"
                                                      (:option :value "" :disabled t
                                                               :selected t
                                                               (role-placeholder role))
                                                      (dolist (u usernames)
                                                        (spinneret:with-html
                                                          (:option :value u u))))))
                                (:button :class "btn btn-primary btn-block"
                                         :type "submit" "Entrar"))
                         (:p :class "hint" (role-hint role))))
            (render-footer)))))

;;; --- Aplicacao do agente: chrome, celulas e controles ---

(defmacro with-agent-page ((title username active) &body body)
  "Envolve BODY no chrome autenticado da aplicacao do agente e retorna a string HTML
completa. Inclui o hospedeiro de modal '#modal' (vazio), alvo das trocas HTMX."
  `(spinneret:with-html-string
     (:doctype)
     (:html :lang "pt-BR"
            (render-head ,title)
            (:body
             (render-navbar :agent ,username ,active)
             ,@body
             (:div :id "modal")
             (render-footer)))))

(defun render-help (label title body &optional right)
  "Emite o rotulo LABEL com a nota explicativa em tooltip (apenas CSS, sem script),
reproduzindo o leiaute do prototipo: '<b>TITLE</b> (0 a 100)<br>BODY'. RIGHT alinha a
nota a direita, para as colunas numericas."
  (spinneret:with-html
    (:span :class (if right "help r" "help")
           (:span label) (:span :class "ico" "?")
           (:span :class "tip" (:b title) " (0 a 100)" (:br) body))))

(defun render-potential-th ()
  "Emite o cabecalho da coluna Potencial com a sua nota explicativa."
  (spinneret:with-html
    (:th :class "n" (render-help "Potencial" (getf +potential-help+ :title)
                                 (getf +potential-help+ :body) t))))

(defun render-dimension-ths ()
  "Emite os cabecalhos das quatro dimensoes ativas com as suas notas explicativas. O peso
relativo da dimensao e derivado do config (DIMENSION-WEIGHT-PERCENT) e anexado ao corpo da
nota, de modo a acompanhar os expoentes correntes sem edicao do texto."
  (dolist (d +active-dimensions+)
    (spinneret:with-html
      (:th :class "n"
           (render-help (getf d :label) (getf d :title)
                        (format nil "~A Recebe peso ~D%."
                                (getf d :body)
                                (dimension-weight-percent (getf d :key)))
                        t)))))

(defun render-score (n)
  "Emite a celula de potencial: o numero em negrito e a barra proporcional quantizada
(classe 'fill-*', sem largura inline, por causa da CSP). N e 0..100 ou NIL."
  (spinneret:with-html
    (:span :class "score"
           (:b (if n (princ-to-string n) "-"))
           (:span :class "bar" (:i :class (fill-class n))))))

(defun render-dim (n &optional momentum)
  "Emite a celula de uma dimensao com o valor N (0..100 ou NIL). MOMENTUM aplica a
variante de destaque do Momentum na lista de engajadas."
  (spinneret:with-html
    (:span :class (if momentum "mcell mom" "mcell")
           (:span :class "v" (if n (princ-to-string n) "-")))))

(defun render-engage-control (row origin)
  "Emite o controle de engajamento da linha ROW. Dentro do top tier, um formulario que
engaja diretamente (HTMX POST, trocando '#opp-list'); fora dele, um botao que abre o
modal de justificativa. ORIGIN ('home' ou 'available') informa o handler qual fragmento
re-renderizar apos o engajamento."
  (let ((id (getf row :opportunity-id)))
    (spinneret:with-html
      (if (getf row :top-tier-p)
          (:form :class "engage-form" :hx-post "/engajar"
                 :hx-target "#opp-list" :hx-swap "outerHTML" :hx-include ".toolbar"
                 (:input :type "hidden" :name "opp" :value id)
                 (:input :type "hidden" :name "origem" :value origin)
                 (:button :class "btn btn-sm btn-primary" :type "submit" "Engajar"))
          (:button :class "btn btn-sm" :type "button"
                   :hx-get (format nil "/engajar/justificar?opp=~A" id)
                   :hx-target "#modal" :hx-swap "innerHTML"
                   "Engajar")))))

(defun render-outcome-controls (row)
  "Emite os controles de desfecho de uma linha engajada ROW: os botoes Won, Lost e
Devolver, como um formulario HTMX POST cujo botao acionado carrega a acao."
  (let ((id (getf row :opportunity-id)))
    (spinneret:with-html
      (:form :class "actions" :hx-post "/desfecho"
             :hx-target "#opp-list" :hx-swap "outerHTML" :hx-include ".toolbar"
             (:input :type "hidden" :name "opp" :value id)
             (:button :class "btn btn-sm btn-won" :type "submit"
                      :name "acao" :value "won" "Won")
             (:button :class "btn btn-sm btn-lost" :type "submit"
                      :name "acao" :value "lost" "Lost")
             (:button :class "btn btn-sm" :type "submit"
                      :name "acao" :value "return" "Devolver")))))

;;; --- Aplicacao do agente: filtros ---

(defun render-select (name label options current)
  "Emite um filtro de selecao NAME rotulado LABEL, com a opcao inicial 'Todos' e as
OPTIONS (valores), marcando CURRENT como selecionado."
  (spinneret:with-html
    (:div :class "filter"
          (:label label)
          (:span :class "select"
                 (:select :name name
                          (:option :value ""
                                   :selected (or (null current) (string= current ""))
                                   "Todos")
                          (dolist (opt options)
                            (let ((val (princ-to-string opt)))
                              (spinneret:with-html
                                (:option :value val :selected (equal val current)
                                         val)))))))))

(defun render-sort-select (options current)
  "Emite o seletor de ordenacao com as OPTIONS (alist chave . rotulo), marcando a chave
corrente CURRENT (string)."
  (spinneret:with-html
    (:div :class "filter"
          (:label "Ordenar por")
          (:span :class "select"
                 (:select :name "sort"
                          (dolist (opt options)
                            (destructuring-bind (key . label) opt
                              (let ((val (string-downcase (symbol-name key))))
                                (spinneret:with-html
                                  (:option :value val :selected (string= val current)
                                           label))))))))))

(defun render-date-filter (name label current)
  "Emite um filtro de data NAME rotulado LABEL, com o valor corrente CURRENT (ISO
'YYYY-MM-DD')."
  (spinneret:with-html
    (:div :class "filter"
          (:label label)
          (:span :class "f-input"
                 (:input :type "date" :name name :value (or current ""))))))

(defun render-filter-form (action fields sort-options sources filters sort
                           &optional date-filter)
  "Emite a barra de filtros e ordenacao como um formulario GET para ACTION (recarrega a
pagina inteira, na interatividade hibrida). FIELDS e a lista de (chave . rotulo); SOURCES
o alist chave->valores das opcoes; FILTERS os valores correntes (alist); SORT-OPTIONS as
opcoes de ordenacao (ou NIL) e SORT a corrente. DATE-FILTER, quando fornecido, e a lista
'(NAME LABEL CURRENT)' de um filtro por data (limiar inferior), rendido apos os selects."
  (spinneret:with-html
    (:form :class "toolbar" :method "get" :action action
           (dolist (field fields)
             (destructuring-bind (key . label) field
               (render-select (string-downcase (symbol-name key)) label
                              (cdr (assoc key sources))
                              (cdr (assoc key filters)))))
           (when date-filter
             (destructuring-bind (name label current) date-filter
               (render-date-filter name label current)))
           (when sort-options (render-sort-select sort-options sort))
           (:button :class "btn btn-sm" :type "submit" "Aplicar"))))

;;; --- Aplicacao do agente: tela inicial (indicadores e top tier) ---

(defun render-kpi-card (label main unit foot &key positive)
  "Emite um cartao de indicador com o rotulo LABEL, o valor principal MAIN (string), o
sufixo UNIT (ou NIL) em '.unit', a legenda FOOT e, quando POSITIVE, o acento positivo."
  (spinneret:with-html
    (:div :class (if positive "kpi pos" "kpi")
          (:div :class "label" label)
          (:div :class (if positive "value pos" "value")
                main
                (when unit (spinneret:with-html (:span :class "unit" unit))))
          (:div :class "foot" foot))))

(defun render-kpi-band (kpis)
  "Emite a faixa dos seis indicadores acumulados do agente a partir da plist KPIS."
  (let ((currency (getf kpis :currency)))
    (spinneret:with-html
      (:div :class "kpi-grid"
            (render-kpi-card "Engajamentos" (princ-to-string (getf kpis :cycles))
                             nil "ciclos acumulados")
            (render-kpi-card "Sucessos" (princ-to-string (getf kpis :wins))
                             nil "desfecho won" :positive t)
            (render-kpi-card "Taxa de sucesso"
                             (format-percent-tenths (getf kpis :success-rate-tenths))
                             "%" "won sobre fechados")
            (render-kpi-card "Ticket medio"
                             (format-money (getf kpis :avg-ticket-amount) currency)
                             nil "media de fechamento")
            (render-kpi-card "Total em vendas"
                             (format-money (getf kpis :total-sales-amount) currency)
                             nil "soma dos won" :positive t)
            (render-kpi-card "Tempo medio de venda"
                             (let ((d (getf kpis :avg-days)))
                               (if d (princ-to-string d) "-"))
                             " dias" "engajamento a fechamento")))))

(defun render-tier-head ()
  "Emite o cabecalho reduzido comum ao top tier: rank, cliente, produto, potencial e as
quatro dimensoes ativas, todos com as notas explicativas."
  (spinneret:with-html
    (:tr (:th "#") (:th "Cliente") (:th "Produto")
         (render-potential-th)
         (render-dimension-ths)
         (:th ""))))

(defun render-dimension-cells (row)
  "Emite as quatro celulas de dimensao ativa da linha ROW, na ordem de exibicao."
  (spinneret:with-html
    (:td :class "n" (render-dim (getf row :momentum)))
    (:td :class "n" (render-dim (getf row :economic)))
    (:td :class "n" (render-dim (getf row :affinity)))
    (:td :class "n" (render-dim (getf row :adherence)))))

(defun render-top-tier-table (rows)
  "Emite o fragmento do top tier (identificado por '#opp-list' para as trocas HTMX): a
tabela reduzida das melhores disponiveis do agente, todas em destaque, com engajamento
direto."
  (spinneret:with-html
    (:div :id "opp-list" :class "table-wrap"
          (:table
           (:thead (render-tier-head))
           (:tbody
            (if (null rows)
                (spinneret:with-html
                  (:tr (:td :colspan "9" :class "empty"
                            "Nenhuma oportunidade disponivel no momento.")))
                (dolist (row rows)
                  (spinneret:with-html
                    (:tr :class "top"
                         (:td :class "rank" (format nil "~2,'0D" (getf row :rank)))
                         (:td :class "acct" (getf row :account))
                         (:td :class "prod" (getf row :product))
                         (:td :class "n" (render-score (getf row :overall)))
                         (render-dimension-cells row)
                         (:td (render-engage-control row "home")))))))))))

(defun render-agent-home-page (username kpis top-rows)
  "Retorna a string HTML da tela inicial do agente: a faixa de indicadores acumulados e
o top tier das disponiveis. KPIS e a plist de indicadores; TOP-ROWS as linhas do top
tier ja anotadas."
  (with-agent-page ((format nil "LeadScorer --- Meu desempenho (~A)" username)
                    username :home)
    (:main :class "page"
           (:div :class "page-head"
                 (:h1 "Meu desempenho")
                 (:span :class "sub" (format nil "agente ~A --- acumulado" username)))
           (render-kpi-band kpis)
           (:section :class "tier"
                     (:div :class "section-head"
                           (:h2 "Meu top tier")
                           (:span :class "note"
                                  "as melhores disponiveis ranqueadas para mim --- "
                                  (:a :href "/disponiveis" "ver todas as disponiveis")))
                     (render-top-tier-table top-rows)))))

;;; --- Aplicacao do agente: lista de disponiveis ---

(defun render-available-list (rows cut-index)
  "Emite o fragmento da lista de disponiveis (identificado por '#opp-list'): a tabela com
o potencial, as quatro dimensoes, o contexto e o controle de engajamento por linha. As
linhas do top tier recebem a classe 'top', as abaixo do corte 'demoted', e a linha
separadora de corte e inserida em CUT-INDEX (ou nenhuma quando NIL)."
  (spinneret:with-html
    (:div :id "opp-list" :class "table-wrap"
          (:table
           (:thead
            (:tr (:th "#") (:th "Cliente") (:th "Produto")
                 (render-potential-th)
                 (render-dimension-ths)
                 (:th "Localidade") (:th "Setor")
                 (:th :class "n" "Porte") (:th :class "n" "Receita")
                 (:th :class "n" "Fundacao")
                 (:th :class "n" "Prazo dec.") (:th :class "n" "Ult. compra")
                 (:th "")))
           (:tbody
            (if (null rows)
                (spinneret:with-html
                  (:tr (:td :colspan "16" :class "empty"
                            "Nenhuma oportunidade corresponde aos filtros.")))
                (loop for row in rows for i from 0 do
                  (when (eql i cut-index)
                    (spinneret:with-html
                      (:tr :class "cut"
                           (:td :colspan "16"
                                (format nil "Corte do modelo --- abaixo de ~D o ~
                                             potencial rebaixa a oportunidade ao ~
                                             final da lista."
                                        ls:*potential-cutoff*)))))
                  (spinneret:with-html
                    (:tr :class (cond ((and cut-index (>= i cut-index)) "demoted")
                                      ((getf row :top-tier-p) "top")
                                      (t nil))
                         (:td :class "rank" (format nil "~2,'0D" (getf row :rank)))
                         (:td :class "acct" (getf row :account))
                         (:td :class "prod" (getf row :product))
                         (:td :class "n" (render-score (getf row :overall)))
                         (render-dimension-cells row)
                         (:td :class "ctx" (or (getf row :location) "-"))
                         (:td :class "ctx" (or (getf row :sector) "-"))
                         (:td :class "n"
                              (let ((employees (getf row :employees)))
                                (if employees (group-thousands employees) "-")))
                         (:td :class "n"
                              (format-money (getf row :revenue-amount)
                                            (getf row :revenue-currency)))
                         (:td :class "n"
                              (let ((year (getf row :year-established)))
                                (if year (princ-to-string year) "-")))
                         (:td :class "n"
                              (let ((c (getf row :cadence-days)))
                                (if c (format nil "~D d" (round c)) "-")))
                         (:td :class "n"
                              (format-money-major (getf row :last-close-value) "USD"))
                         (:td (render-engage-control row "available")))))))))))

(defun render-available-page (username rows cut-index sources filters sort total since)
  "Retorna a string HTML da tela de disponiveis: o cabecalho, o chip de corte, a barra de
filtros e ordenacao e a lista. ROWS ja vem anotada, filtrada e ordenada; CUT-INDEX marca
o corte; SOURCES o alist de opcoes de filtro; FILTERS e SORT o estado corrente; TOTAL o
numero de pares do agente; SINCE o valor corrente do filtro por data de disponibilizacao."
  (with-agent-page ((format nil "LeadScorer --- Disponiveis (~A)" username)
                    username :available)
    (:main :class "page"
           (:div :class "page-head"
                 (:h1 "Oportunidades disponiveis")
                 (:span :class "sub"
                        (format nil "ranqueadas para ~A --- ~D pares conta-produto"
                                username total))
                 (:span :class "cut-chip" (:span :class "dot")
                        (format nil "Filtro de corte do modelo: potencial a partir de ~D"
                                ls:*potential-cutoff*)))
           (render-filter-form "/disponiveis" +filter-fields+ +sort-options+
                               sources filters sort
                               (list "available_since" "Disponivel desde" since))
           (render-available-list rows cut-index))))

;;; --- Aplicacao do agente: lista de engajadas ---

(defun render-engaged-list (rows)
  "Emite o fragmento da lista de engajadas (identificado por '#opp-list'): a tabela com o
potencial e as dimensoes decaidas, o instante de engajamento, o tempo a expirar, a
justificativa e os controles de desfecho. Os campos de exibicao dependentes do relogio
(':engaged-display', ':expire-label', ':expire-soon') sao pre-computados pelo handler."
  (spinneret:with-html
    (:div :id "opp-list" :class "table-wrap"
          (:table
           (:thead
            (:tr (:th "Oportunidade")
                 (render-potential-th)
                 (render-dimension-ths)
                 (:th "Engajada em") (:th :class "n" "Expira em")
                 (:th "Justificativa") (:th "Desfecho")))
           (:tbody
            (if (null rows)
                (spinneret:with-html
                  (:tr (:td :colspan "10" :class "empty"
                            "Voce nao possui oportunidades engajadas.")))
                (dolist (row rows)
                  (spinneret:with-html
                    (:tr (:td (:div :class "opp-name" (getf row :account))
                              (:div :class "opp-prod" (getf row :product)))
                         (:td :class "n" (render-score (getf row :overall)))
                         (:td :class "n" (render-dim (getf row :momentum) t))
                         (:td :class "n" (render-dim (getf row :economic)))
                         (:td :class "n" (render-dim (getf row :affinity)))
                         (:td :class "n" (render-dim (getf row :adherence)))
                         (:td :class "when" (getf row :engaged-display))
                         (:td :class "n" (render-expire-cell row))
                         (:td :class "just"
                              (justification-short (getf row :justification-code)))
                         ;; Uma engajada ja alem do horizonte (expirando) tem as acoes
                         ;; desabilitadas: sera fechada como 'lost' pelo agendador no
                         ;; proximo tique, e marcar 'won' criaria uma corrida com ele.
                         (:td (if (getf row :expiring-p)
                                  (:span :class "just none"
                                         "expira no proximo ciclo")
                                  (render-outcome-controls row))))))))))))

(defun render-engaged-page (username rows sources filters sort engaged-count since)
  "Retorna a string HTML da tela de engajadas: o cabecalho, o contador, a nota de
decaimento, os filtros e a lista. ROWS ja vem filtrada e ordenada, com os campos de
exibicao computados; ENGAGED-COUNT o total corrente; SINCE o valor corrente do filtro por
data de engajamento."
  (with-agent-page ((format nil "LeadScorer --- Engajadas (~A)" username)
                    username :engaged)
    (:main :class "page"
           (:div :class "page-head"
                 (:h1 "Minhas oportunidades engajadas")
                 (:span :class "sub" (format nil "visiveis apenas para ~A" username))
                 (:span :class "count-chip"
                        (:b (princ-to-string engaged-count))
                        (format nil " de ~D engajadas" ls:*max-engagements*)))
           (:p :class "decay-note"
               "O potencial e o momentum decaem a cada minuto desde o engajamento; a "
               "oportunidade expira em vinte minutos e retorna as disponiveis com o "
               "potencial decaido.")
           (render-filter-form "/engajadas" +engaged-filter-fields+
                               +engaged-sort-options+ sources filters sort
                               (list "engaged_since" "Engajada desde" since))
           (render-engaged-list rows))))

;;; --- Aplicacao do agente: modais (fragmentos) ---

(defun render-justification-modal (row)
  "Emite o fragmento do modal de justificativa para engajar a oportunidade ROW fora do
top tier, com as tres opcoes de motivo. Confirmar submete o engajamento (HTMX POST) e
Cancelar limpa o modal."
  (let ((id (getf row :opportunity-id)))
    (spinneret:with-html
      (:div :class "backdrop"
            (:div :class "modal" :role "dialog" :aria-modal "true"
                  (:h2 "Justificar engajamento")
                  (:p :class "ctx-line"
                      "A oportunidade "
                      (:b (format nil "~A --- ~A"
                                  (getf row :account) (getf row :product)))
                      (format nil " (potencial ~A) esta na posicao ~A, fora do seu ~
                                   top tier. Registre o motivo do desvio da ~
                                   recomendacao do modelo."
                              (or (getf row :overall) "-") (getf row :rank)))
                  (:form :hx-post "/engajar" :hx-target "#opp-list" :hx-swap "outerHTML"
                         :hx-include ".toolbar"
                         (:input :type "hidden" :name "opp" :value id)
                         (:input :type "hidden" :name "origem" :value "available")
                         (:fieldset :class "just-options"
                                    (:legend "Motivo do engajamento")
                                    (loop for j in +justifications+ for i from 0 do
                                      (spinneret:with-html
                                        (:label :class "opt"
                                                (:input :type "radio" :name "just"
                                                        :value (getf j :code)
                                                        :checked (zerop i))
                                                (:span :class "t" (getf j :title))
                                                (:span :class "d"
                                                       (getf j :description))))))
                         (:div :class "modal-actions"
                               (:button :class "btn" :type "button"
                                        :hx-get "/modal/fechar" :hx-target "#modal"
                                        :hx-swap "innerHTML" "Cancelar")
                               (:button :class "btn btn-primary" :type "submit"
                                        "Confirmar engajamento"))
                         (:p :class "foot-note"
                             "Engajamentos dentro do top tier nao exigem justificativa.")))))))

(defun render-limit-alert ()
  "Emite o fragmento do alerta de limite de engajamentos atingido."
  (spinneret:with-html
    (:div :class "backdrop"
          (:div :class "modal alert" :role "alertdialog"
                (:div :class "mark" (:span :class "dot") "Limite atingido")
                (:h2 "Carteira de engajamento cheia")
                (:p (format nil "Voce ja possui o limite de ~D oportunidades ~
                                 engajadas simultaneas. Conclua uma venda (won ou ~
                                 lost) ou devolva uma oportunidade para engajar outra."
                            ls:*max-engagements*))
                (:div :class "modal-actions"
                      (:button :class "btn" :type "button"
                               :hx-get "/modal/fechar" :hx-target "#modal"
                               :hx-swap "innerHTML" "Fechar")
                      (:a :class "btn btn-primary" :href "/engajadas"
                          "Ver minhas engajadas"))))))

;;; --- Aplicacao do gerente: chrome e telas (somente leitura) ---

(defmacro with-manager-page ((title username active) &body body)
  "Envolve BODY no chrome autenticado da aplicacao do gerente e retorna a string HTML
completa. A aplicacao do gerente e somente leitura: nao inclui o hospedeiro de modal
'#modal' nem controles de mutacao."
  `(spinneret:with-html-string
     (:doctype)
     (:html :lang "pt-BR"
            (render-head ,title)
            (:body
             (render-navbar :manager ,username ,active)
             ,@body
             (render-footer)))))

(defun render-cycle-badge (state)
  "Emite o badge do estado de ciclo STATE (:open, :won, :lost, :expired, :returned ou o
estado derivado :expiring), com o rotulo e a classe de cor correspondentes."
  (spinneret:with-html
    (:span :class (format nil "badge ~A" (cycle-state-class state))
           (cycle-state-label state))))

(defun render-expire-cell (row)
  "Emite o conteudo da celula 'Expira em' de uma engajada: o badge 'Expirando' quando a
oportunidade ja alcancou o horizonte (expiracao pendente do tique do agendador), senao o
countdown, com o realce de proximidade."
  (spinneret:with-html
    (if (getf row :expiring-p)
        (:span :class "badge expiring" "Expirando")
        (:span :class (if (getf row :expire-soon) "expire soon" "expire")
               (getf row :expire-label)))))

(defun render-team-engaged-table (rows)
  "Emite a tabela de destaque da tela inicial do gerente: as oportunidades engajadas em
curso pelo time, com o agente, o contexto, o potencial, o instante de engajamento, o
tempo a expirar e a justificativa. Os campos de exibicao dependentes do relogio
(':engaged-display', ':expire-label', ':expire-soon') sao pre-computados pelo handler."
  (spinneret:with-html
    (:div :class "table-wrap"
          (:table
           (:thead
            (:tr (:th "Agente") (:th "Cliente") (:th "Produto")
                 (:th :class "n" "Potencial")
                 (:th "Engajada em") (:th :class "n" "Expira em")
                 (:th "Justificativa")))
           (:tbody
            (if (null rows)
                (spinneret:with-html
                  (:tr (:td :colspan "7" :class "empty"
                            "Nenhuma oportunidade engajada pelo time no momento.")))
                (dolist (row rows)
                  (spinneret:with-html
                    (:tr (:td :class "agent" (getf row :agent-username))
                         (:td :class "acct" (getf row :account))
                         (:td :class "prod" (getf row :product))
                         (:td :class "n" (render-score (getf row :overall)))
                         (:td :class "when" (getf row :engaged-display))
                         (:td :class "n" (render-expire-cell row))
                         (:td :class "just"
                              (justification-short
                               (getf row :justification-code))))))))))))

(defun render-manager-home-page (username kpis team-size engaged-rows)
  "Retorna a string HTML da tela inicial do gerente: a faixa dos seis indicadores
agregados do time e a lista de destaque das engajadas em curso do time. KPIS e a plist
de indicadores do time; TEAM-SIZE o numero de agentes; ENGAGED-ROWS as engajadas ja
enriquecidas com os campos de exibicao."
  (with-manager-page ((format nil "LeadScorer --- Desempenho do time (~A)" username)
                      username :home)
    (:main :class "page"
           (:div :class "page-head"
                 (:h1 "Desempenho do time")
                 (:span :class "sub"
                        (format nil "gerente ~A --- ~D agentes --- acumulado"
                                username team-size)))
           (render-kpi-band kpis)
           (:section :class "tier"
                     (:div :class "section-head"
                           (:h2 "Engajadas do meu time")
                           (:span :class "note"
                                  "oportunidades em engajamento pelos agentes --- "
                                  (:a :href "/acompanhamento"
                                      "ver acompanhamento completo")))
                     (render-team-engaged-table engaged-rows)))))

;;; --- Aplicacao do gerente: acompanhamento (filtros mistos e ciclos) ---

(defun render-text-filter (name label current placeholder)
  "Emite um filtro de texto livre NAME rotulado LABEL, com o valor corrente CURRENT e o
texto de exemplo PLACEHOLDER."
  (spinneret:with-html
    (:div :class "filter"
          (:label label)
          (:span :class "f-input"
                 (:input :type "text" :name name :value (or current "")
                         :placeholder placeholder)))))

(defun render-outcome-filter (name label current)
  "Emite o filtro de desfecho NAME rotulado LABEL, com a opcao inicial 'Todos' e os cinco
estados de ciclo (valor = nome do estado em caixa baixa), marcando CURRENT."
  (spinneret:with-html
    (:div :class "filter"
          (:label label)
          (:span :class "select"
                 (:select :name name
                          (:option :value ""
                                   :selected (or (null current) (string= current ""))
                                   "Todos")
                          (dolist (state +cycle-states+)
                            (destructuring-bind (key . lbl) state
                              (let ((val (string-downcase (symbol-name key))))
                                (spinneret:with-html
                                  (:option :value val :selected (equal val current)
                                           lbl))))))))))

(defun render-team-toolbar (agents products filters sort)
  "Emite a barra de filtros do acompanhamento como um formulario GET para
'/acompanhamento' (recarrega a pagina inteira; o gerente e somente leitura). AGENTS e a
lista de nomes de usuario do time; PRODUCTS os produtos distintos; FILTERS o alist de
valores correntes por id de filtro; SORT a ordenacao corrente."
  (spinneret:with-html
    (:form :class "toolbar" :method "get" :action "/acompanhamento"
           (render-select "agent" "Agente" agents (cdr (assoc :agent filters)))
           (render-select "product" "Produto" products (cdr (assoc :product filters)))
           (render-text-filter "account" "Conta" (cdr (assoc :account filters))
                               "Nome do cliente")
           (render-outcome-filter "outcome" "Desfecho" (cdr (assoc :outcome filters)))
           (render-date-filter "since" "Engajada desde" (cdr (assoc :since filters)))
           (render-sort-select +team-sort-options+ sort)
           (:button :class "btn btn-sm" :type "submit" "Aplicar"))))

(defun render-team-cycles-table (rows)
  "Emite a tabela completa dos ciclos do time no acompanhamento: agente, contexto,
potencial, instantes de engajamento e fechamento, estado do ciclo (badge), justificativa
e valor de fechamento. Os campos de exibicao (':engaged-display', ':closed-display') sao
pre-computados pelo handler; o estado deriva de CYCLE-STATE."
  (spinneret:with-html
    (:div :class "table-wrap"
          (:table
           (:thead
            (:tr (:th "Agente") (:th "Cliente") (:th "Produto")
                 (:th :class "n" "Potencial")
                 (:th "Engajada em") (:th "Fechada em") (:th "Desfecho")
                 (:th "Justificativa") (:th :class "n" "Valor")))
           (:tbody
            (if (null rows)
                (spinneret:with-html
                  (:tr (:td :colspan "9" :class "empty"
                            "Nenhum ciclo corresponde aos filtros.")))
                (dolist (row rows)
                  (let ((state (cycle-display-state row)))
                    (spinneret:with-html
                      (:tr (:td :class "agent" (getf row :agent-username))
                           (:td :class "acct" (getf row :account))
                           (:td :class "prod" (getf row :product))
                           (:td :class "n" (render-score (getf row :overall)))
                           (:td :class "when" (getf row :engaged-display))
                           (:td :class "when"
                                (or (getf row :closed-display) "-"))
                           (:td (render-cycle-badge state))
                           (:td :class "just"
                                (justification-short
                                 (getf row :justification-code)))
                           (:td :class "n val"
                                (format-money (getf row :close-value-amount)
                                              (getf row :close-value-currency)))))))))))))

(defun render-acompanhamento-page (username rows agents products filters sort
                                   open-count total-count)
  "Retorna a string HTML da tela de acompanhamento do time: o cabecalho, o contador (em
curso e total), a barra de filtros mista e a tabela de ciclos. ROWS ja vem filtrada e
ordenada, com os campos de exibicao computados; AGENTS e PRODUCTS as opcoes de filtro;
FILTERS e SORT o estado corrente."
  (with-manager-page ((format nil "LeadScorer --- Acompanhamento (~A)" username)
                      username :tracking)
    (:main :class "page"
           (:div :class "page-head"
                 (:h1 "Acompanhamento do time")
                 (:span :class "sub"
                        (format nil "oportunidades engajadas e ciclos recentes do time de ~A"
                                username))
                 (:span :class "count-chip"
                        (:b (princ-to-string open-count)) " em curso --- "
                        (:b (princ-to-string total-count)) " ciclos"))
           (render-team-toolbar agents products filters sort)
           (render-team-cycles-table rows))))
