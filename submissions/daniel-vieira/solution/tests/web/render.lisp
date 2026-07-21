;;;; render.lisp --- Testes do layout base e das páginas Spinneret.

(in-package #:leadscorer/web/tests)

;;; Spinneret emite atributos sem aspas quando o valor as dispensa (HTML5
;;; válido), reservando as aspas para valores com espaços ou barras. As
;;; asserções abaixo espelham essa forma; a validação estrutural por 'vnu'
;;; ocorre no passo de verificação servida.

(defparameter *sample-usernames*
  '("anna.snelling" "boris.faz" "cecily.lampkin")
  "Amostra de nomes de usuário para os testes de renderização, sem tocar o
banco.")

(define-test render-login-agent-markup
  "A página de login do agente reproduz o chrome e o formulário POST reais."
  (let ((html (leadscorer/web::render-login-page :agent *sample-usernames*)))
    (true (search "<!DOCTYPE html>" html))
    (true (search "lang=pt-BR" html))
    (true (search "Aplicação do agente" html))
    (true (search "Identificação" html))
    (true (search "Agente de vendas" html))
    (true (search "name=user" html))
    (true (search "action=\"/login\"" html))
    (true (search "method=post" html))
    (true (search "value=anna.snelling" html))
    ;; O ativo estático e a configuração htmx sob CSP estrita. O 'app.css' e
    ;; versionado por hash para cache-busting (F2K9): o href carrega '?v=<hash>'.
    (true (search "/assets/app.css?v=" html))
    (true (search "/assets/htmx.min.js" html))
    (true (search "htmx-config" html))
    (true (search "allowEval" html))
    ;; O formulário real submete por POST; o artifício estático foi removido.
    (false (search "onsubmit" html))))

(define-test render-login-manager-markup
  "A página de login do gerente difere no escopo e no rótulo do papel."
  (let ((html (leadscorer/web::render-login-page :manager *sample-usernames*)))
    (true (search "Aplicação do gerente" html))
    (true (search "Gerente de vendas" html))
    (true (search "Escolha um gerente" html))))

(define-test render-login-error-message
  "Uma mensagem de erro é exibida quando fornecida."
  (let ((html (leadscorer/web::render-login-page
               :agent *sample-usernames* "Usuário inválido.")))
    (true (search "Usuário inválido." html))
    (true (search "class=error" html))))

(define-test app-css-href-is-versioned
  "O href do 'app.css' carrega um sufixo de versao hexadecimal derivado do
conteudo, estavel entre chamadas (memoizado), para cache-busting (F2K9)."
  (let ((href (leadscorer/web::app-css-href)))
    (true (search "/assets/app.css?v=" href))
    (let ((version (subseq href (+ (search "?v=" href) 3))))
      (is = 12 (length version))
      (true (every (lambda (ch) (digit-char-p ch 16)) version)))
    ;; Memoizado: a segunda chamada retorna o mesmo href.
    (is string= href (leadscorer/web::app-css-href))))

;;; --- Aplicacao do agente: paginas e fragmentos ---

(defun sample-available-row (&key (rank 1) (top t) (overall 80))
  "Uma linha de oportunidade disponivel ja anotada, para os testes de renderizacao."
  (list :opportunity-id 5 :rank rank :top-tier-p top
        :account "Golddex" :product "GTX Plus Pro" :series "GTX"
        :overall overall :momentum 90 :economic 70 :affinity 60 :adherence 50
        :location "East" :sector "technology"
        :employees 5000 :revenue-amount 1234500 :revenue-currency "USD"
        :year-established 2011 :available-at 0
        :cadence-days 18.0 :last-close-value 5482))

(defun sample-kpis ()
  "Uma plist de indicadores para os testes de renderizacao."
  (list :cycles 34 :wins 21 :losses 13 :success-rate-tenths 618
        :avg-ticket-amount 284700 :total-sales-amount 5978700 :avg-days 47
        :currency "USD"))

(defun norm (html)
  "Colapsa sequencias de espaco em branco em um unico espaco. O Spinneret preenche o
texto com quebras de linha para legibilidade (inocuas no navegador, que colapsa o espaco);
a normalizacao torna as assercoes de substring robustas a esse preenchimento."
  (with-output-to-string (out)
    (let ((prev-space nil))
      (loop for ch across html do
        (if (member ch '(#\Space #\Tab #\Newline #\Return))
            (progn (unless prev-space (write-char #\Space out))
                   (setf prev-space t))
            (progn (write-char ch out) (setf prev-space nil)))))))

(defun frag (thunk)
  "Captura um fragmento Spinneret (que emite no fluxo corrente) como string
normalizada."
  (norm (spinneret:with-html-string (funcall thunk))))

(define-test render-agent-home-markup
  "A home do agente apresenta a faixa de indicadores e o top tier."
  (let ((html (norm (leadscorer/web::render-agent-home-page
                     "anna.snelling" (sample-kpis) (list (sample-available-row))))))
    (true (search "Meu desempenho" html))
    (true (search "kpi-grid" html))
    (true (search "Engajamentos" html))
    (true (search "Taxa de sucesso" html))
    (true (search "61,8" html))
    (true (search "US$ 2.847" html))     ; ticket medio
    (true (search "Meu top tier" html))
    (true (search "Golddex" html))
    (true (search "Engajar" html))
    ;; As tres abas do agente estao presentes.
    (true (search "/disponiveis" html))
    (true (search "/engajadas" html))))

(define-test render-available-markup
  "A tela de disponiveis apresenta o chip de corte, os filtros e a lista."
  (let ((html (norm (leadscorer/web::render-available-page
                     "anna.snelling" (list (sample-available-row)) nil
                     '((:location "East" "West")) '((:location . "")) "overall" 128 ""))))
    (true (search "Oportunidades disponiveis" html))
    (true (search "Filtro de corte do modelo" html))
    (true (search "Localidade" html))
    (true (search "Ordenar por" html))
    (true (search "128 pares" html))
    ;; Colunas de contexto exigidas pela estoria (B4): porte, receita e fundacao.
    (true (search "Porte" html))
    (true (search "Receita" html))
    (true (search "Fundacao" html))
    ;; Filtro por data de disponibilizacao (B2).
    (true (search "Disponivel desde" html))
    ;; A nota explicativa da dimensao Momentum (texto identico ao prototipo).
    (true (search "Eixo primário do ranqueamento" html))
    ;; O titulo da nota difere do rotulo da coluna (leiaute do prototipo).
    (true (search "Especialização do agente" html))
    ;; O peso e derivado do config e anexado a nota (D4).
    (true (search "Recebe peso 17%" html))
    (true (search "Golddex" html))))

(define-test render-available-list-fragment
  "O fragmento da lista traz a barra de pontuacao quantizada, o contexto e o corte."
  (let* ((rows (list (sample-available-row :rank 1 :top t :overall 80)
                     (sample-available-row :rank 2 :top nil
                                                           :overall 30)))
         (html (frag (lambda () (leadscorer/web::render-available-list rows 1)))))
    (true (search "id=opp-list" html))
    (true (search "fill-80" html))         ; barra quantizada, sem estilo inline
    (false (search "style=" html))          ; nenhuma largura inline (CSP)
    (true (search "18 d" html))             ; cadencia do modelo
    (true (search "US$ 5.482" html))        ; ultima compra (unidade maior)
    (true (search "Corte do modelo" html))  ; linha separadora em cut-index 1
    (true (search "class=demoted" html))))

(define-test render-engaged-list-fragment
  "O fragmento de engajadas traz os controles de desfecho e a justificativa."
  (let* ((row (list :opportunity-id 7 :account "Konmatfix" :product "GTX Pro"
                    :overall 72 :momentum 40 :economic 55 :affinity 60 :adherence 30
                    :justification-code "direct-inquiry"
                    :engaged-display "19/07 14:03" :expire-label "17 min"
                    :expire-soon nil))
         (html (frag (lambda () (leadscorer/web::render-engaged-list (list row))))))
    (true (search "Konmatfix" html))
    (true (search "Won" html))
    (true (search "Lost" html))
    (true (search "Devolver" html))
    (true (search "consulta direta" html))
    (true (search "17 min" html))
    (true (search "19/07 14:03" html))))

(define-test render-modals
  "O modal de justificativa e o alerta de limite trazem a copia esperada."
  (let ((modal (frag (lambda ()
                       (leadscorer/web::render-justification-modal
                        (sample-available-row :rank 12 :top nil :overall 57)))))
        (alert (frag #'leadscorer/web::render-limit-alert)))
    (true (search "Justificar engajamento" modal))
    (true (search "Discordancia da avaliacao" modal))
    (true (search "Consulta direta do cliente" modal))
    (true (search "Confirmar engajamento" modal))
    (true (search "posicao 12" modal))
    (true (search "Carteira de engajamento cheia" alert))))

;;; --- Aplicacao do gerente: paginas ---

(defun sample-team-engaged-row ()
  "Uma linha de engajada em curso do time, ja enriquecida, para os testes."
  (list :opportunity-id 5 :agent-username "anna.snelling"
        :account "Golddex" :product "GTX Plus Pro" :overall 88
        :engaged-display "19/07 14:03" :expire-label "17 min" :expire-soon nil
        :justification-code nil))

(defun sample-team-cycle-rows ()
  "Cinco ciclos do time, um por estado (aberto, won, lost, expirado, devolvido), ja
enriquecidos, para os testes de acompanhamento."
  (list (list :agent-username "anna.snelling" :account "Golddex" :product "GTX Plus Pro"
              :overall 88 :engaged-display "19/07 14:03" :closed-display nil
              :closed-at nil :outcome nil :expired nil :justification-code nil
              :close-value-amount nil :close-value-currency nil)
        (list :agent-username "boris.faz" :account "Zumgoity" :product "GTX Plus Pro"
              :overall 91 :engaged-display "18/07 10:22" :closed-display "18/07 10:39"
              :closed-at 100 :outcome "won" :expired nil :justification-code nil
              :close-value-amount 548200 :close-value-currency "USD")
        (list :agent-username "gladys.colclough" :account "Betasoloin" :product "MG Advanced"
              :overall 64 :engaged-display "17/07 16:40" :closed-display "17/07 16:58"
              :closed-at 100 :outcome "lost" :expired nil :justification-code "other"
              :close-value-amount nil :close-value-currency nil)
        (list :agent-username "rosalina.dieter" :account "Sumace" :product "GTX Basic"
              :overall 58 :engaged-display "17/07 11:12" :closed-display "17/07 11:32"
              :closed-at 100 :outcome "lost" :expired t :justification-code "direct-inquiry"
              :close-value-amount nil :close-value-currency nil)
        (list :agent-username "anna.snelling" :account "Konmatfix" :product "GTX Pro"
              :overall 81 :engaged-display "18/07 09:05" :closed-display "18/07 09:21"
              :closed-at 100 :outcome nil :expired nil :justification-code nil
              :close-value-amount nil :close-value-currency nil)))

(define-test render-engaged-expiring-disables-actions
  "Uma engajada ja alem do horizonte mostra 'Expirando' e nao oferece controles de desfecho."
  (let* ((row (list :opportunity-id 7 :account "Konmatfix" :product "GTX Pro"
                    :overall 72 :momentum 40 :economic 55 :affinity 60 :adherence 30
                    :justification-code nil
                    :engaged-display "19/07 14:03" :expire-label "00 min"
                    :expire-soon t :expiring-p t))
         (html (frag (lambda () (leadscorer/web::render-engaged-list (list row))))))
    (true (search "Expirando" html))
    (true (search "expira no proximo ciclo" html))
    ;; Sem controles de desfecho na linha expirando.
    (false (search "Won" html))
    (false (search "Devolver" html))
    ;; O badge substitui o countdown; '00 min' nao aparece.
    (false (search "00 min" html))))

(define-test render-acompanhamento-expiring-badge
  "Um ciclo aberto alem do horizonte exibe o badge 'Expirando', nao 'Em curso'."
  (let* ((row (list :agent-username "ann" :account "Golddex" :product "GTX"
                    :overall 88 :engaged-display "19/07 14:03" :closed-display nil
                    :closed-at nil :outcome nil :expired nil :expiring-p t
                    :justification-code nil :close-value-amount nil
                    :close-value-currency nil))
         (html (norm (leadscorer/web::render-acompanhamento-page
                      "m" (list row) '("ann") '("GTX")
                      '((:agent . "")) "engaged" 0 1))))
    (true (search "badge expiring" html))
    (true (search "Expirando" html))
    ;; O ciclo nao e exibido como aberto ('Em curso' consta so como opcao do filtro).
    (false (search "badge open" html))))

(define-test render-manager-home-markup
  "A home do gerente apresenta a faixa agregada do time e o destaque das engajadas."
  (let ((html (norm (leadscorer/web::render-manager-home-page
                     "dustin.brinkmann" (sample-kpis) 6
                     (list (sample-team-engaged-row))))))
    (true (search "Desempenho do time" html))
    (true (search "6 agentes" html))
    (true (search "kpi-grid" html))
    (true (search "Engajadas do meu time" html))
    (true (search "ver acompanhamento completo" html))
    (true (search "/acompanhamento" html))
    ;; A coluna do agente e o contexto da linha de destaque.
    (true (search "anna.snelling" html))
    (true (search "Golddex" html))
    (true (search "17 min" html))
    ;; A tag de papel do gerente no wordmark; sem controles de mutacao.
    (true (search "class=role" html))
    (false (search "/engajar" html))
    (false (search "id=modal" html))
    ;; O wordmark e o status vivem no contêiner colapsavel '.nav-menu' (que migra
    ;; para o hamburguer nas telas pequenas); o Sair permanece na barra de acoes.
    (true (search "nav-menu" html))
    (true (search "Sessão ativa" html))
    (true (search "Sair" html))))

(define-test render-acompanhamento-markup
  "O acompanhamento apresenta a barra de filtros mista e a tabela com os cinco estados."
  (let ((html (norm (leadscorer/web::render-acompanhamento-page
                     "dustin.brinkmann" (sample-team-cycle-rows)
                     '("anna.snelling" "boris.faz") '("GTX Plus Pro" "MG Advanced")
                     '((:agent . "") (:outcome . "")) "engaged" 1 5))))
    (true (search "Acompanhamento do time" html))
    ;; O chip de contagem: os numeros vao em '<b>', logo o rotulo casa isoladamente.
    (true (search "em curso" html))
    (true (search "ciclos" html))
    ;; Barra de filtros mista: select de agente, texto de conta, data e desfecho.
    (true (search "name=agent" html))
    (true (search "type=text" html))
    (true (search "type=date" html))
    (true (search "name=outcome" html))
    (true (search "name=since" html))
    ;; Os cinco badges de estado, incluindo Devolvida (o quinto).
    (true (search "badge open" html))
    (true (search "badge won" html))
    (true (search "badge lost" html))
    (true (search "badge expired" html))
    (true (search "badge returned" html))
    (true (search "Devolvida" html))
    ;; Valor de fechamento do won, formatado em centavos.
    (true (search "US$ 5.482" html))
    ;; CSP: barras de pontuacao por classe, sem largura inline.
    (true (search "fill-90" html))
    (false (search "style=" html))))
