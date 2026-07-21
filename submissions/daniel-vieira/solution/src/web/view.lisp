;;;; view.lisp --- Auxiliares puros de apresentacao da aplicacao do agente.
;;;;
;;;; Concentram a logica de formatacao e de arranjo que a renderizacao Spinneret
;;;; consome, isolada do DOM e, portanto, testavel sem servidor. Nao tocam banco,
;;;; relogio nem estado global mutavel: recebem os dados ja lidos e retornam
;;;; strings, nomes de classe ou listas anotadas. As barras de pontuacao usam
;;;; classes utilitarias quantizadas ('fill-*') porque a CSP estrita proibe estilo
;;;; inline (nenhum 'style=width'); o numero exato acompanha a barra como texto.

(in-package #:leadscorer/web)

;;; --- Formatacao monetaria e numerica ---

(defparameter +currency-symbols+
  '(("USD" . "US$") ("BRL" . "R$"))
  "Simbolos de exibicao por codigo de moeda ISO 4217. Codigos ausentes exibem o
proprio codigo.")

(defun currency-symbol (code)
  "O simbolo de exibicao da moeda CODE, ou o proprio CODE quando desconhecido."
  (or (cdr (assoc code +currency-symbols+ :test #'string=)) code))

(defun group-thousands (n)
  "A representacao decimal do inteiro nao negativo N com o separador de milhar '.' a
cada tres digitos."
  (let* ((digits (format nil "~D" n))
         (len (length digits)))
    (with-output-to-string (out)
      (dotimes (i len)
        (when (and (plusp i) (zerop (mod (- len i) 3)))
          (write-char #\. out))
        (write-char (char digits i) out)))))

(defun format-money (amount currency)
  "AMOUNT, inteiro na unidade menor da moeda CURRENCY (codigo ISO 4217), formatado com
o simbolo da moeda e o separador de milhar '.'; a parte decimal, com ',', aparece apenas
quando nao nula. NIL rende um travessao. Nunca converte por ponto flutuante."
  (if (null amount)
      "-"
      (multiple-value-bind (major minor) (truncate amount 100)
        (let ((symbol (currency-symbol currency)))
          (if (zerop minor)
              (format nil "~A ~A" symbol (group-thousands major))
              (format nil "~A ~A,~2,'0D" symbol (group-thousands major) minor))))))

(defun format-money-major (amount currency)
  "Formata AMOUNT, ja inteiro na unidade MAIOR da moeda CURRENCY (nao na unidade menor),
com o simbolo e o separador de milhar '.'. NIL rende um travessao. Usada para os montantes
do retrato estatico do modelo (o valor da ultima compra, em dolares inteiros do dataset),
distintos dos montantes do banco, que residem em centavos e usam FORMAT-MONEY."
  (if (null amount)
      "-"
      (format nil "~A ~A" (currency-symbol currency) (group-thousands amount))))

(defun format-datetime-ms (ms)
  "Formata MS (UNIX-ms, UTC) como 'DD/MM HH:MM' em UTC. NIL rende um travessao. Os
registros de tempo permanecem em UTC, sem conversao para hora local."
  (if (null ms)
      "-"
      (multiple-value-bind (sec min hour day month)
          (decode-universal-time (+ (floor ms 1000) ls:+unix-epoch-universal-time+) 0)
        (declare (ignore sec))
        (format nil "~2,'0D/~2,'0D ~2,'0D:~2,'0D" day month hour min))))

(defun format-percent-tenths (tenths)
  "Formata TENTHS, decimos de ponto percentual (inteiro), como 'NN,N'. NIL rende um
travessao."
  (if (null tenths)
      "-"
      (multiple-value-bind (whole frac) (truncate tenths 10)
        (format nil "~D,~D" whole frac))))

(defun fill-class (n)
  "O nome da classe CSS da barra de preenchimento para a pontuacao N (0 a 100),
quantizada ao passo de 5% (a CSP proibe a largura inline). NIL rende a barra vazia."
  (let ((value (if n (max 0 (min 100 (* 5 (round n 5)))) 0)))
    (format nil "fill-~D" value)))

(defun format-expire (minutes)
  "Formata MINUTES (inteiro de minutos reais restantes) como 'NN min'. NIL rende um
travessao."
  (if minutes (format nil "~2,'0D min" minutes) "-"))

(defun expire-soon-p (minutes &optional (threshold 5))
  "Verdadeiro quando MINUTES nao e NIL e esta em ou abaixo de THRESHOLD (padrao 5),
sinalizando proximidade da expiracao."
  (and minutes (<= minutes threshold)))

;;; --- Arranjo da lista de disponiveis ---

(defun arrange-available (rows &optional (top-size ls:*top-tier-size*)
                                         (cutoff ls:*potential-cutoff*))
  "Anota ROWS, ja ordenadas por potencial decrescente, com ':rank' (1-based) e
':top-tier-p' (posicao ate TOP-SIZE), e retorna, como valores, a lista anotada e o
indice 0-based da primeira oportunidade com potencial abaixo de CUTOFF, ou NIL quando
nenhuma. Como as linhas ja vem ordenadas, as abaixo do corte sao contiguas ao final; o
indice apenas marca onde inserir a linha separadora de corte. CUTOFF zero desativa o
corte."
  (let ((annotated
          (loop for row in rows
                for i from 1
                collect (list* :rank i :top-tier-p (<= i top-size) row)))
        (cut-index (and (plusp cutoff)
                        (position-if (lambda (row) (< (or (getf row :overall) 0) cutoff))
                                     rows))))
    (values annotated cut-index)))

;;; --- Metadados das dimensoes e das justificativas (copia da concepcao) ---

;;; As notas explicativas reproduzem, em forma, conteudo e leiaute, as dos prototipos
;;; estaticos ('.claude/assets/examples/example-disponiveis-dark.html'), a fonte
;;; canonica dos textos. Cada nota tem um titulo (distinto do rotulo da coluna) e um
;;; corpo, exibidos como '<b>titulo</b> (0 a 100)<br>corpo'. O peso relativo de cada
;;; dimensao NAO e fixado no texto do corpo: e derivado em tempo de renderizacao dos
;;; expoentes correntes do config (a fonte canonica) por DIMENSION-WEIGHT-PERCENT e
;;; anexado ao corpo pela renderizacao, de modo que uma alteracao dos pesos no config se
;;; reflita na nota sem edicao manual do texto.

(defparameter +potential-help+
  (list :title "Potencial da oportunidade"
        :body (concatenate 'string
                           "Potencial de venda do produto indicado para o cliente "
                           "específico. Média geométrica ponderada das quatro dimensões "
                           "de decisão: Momentum, Retorno, Afinidade e Especialização. Após "
                           "o engajamento, sofre decaimento temporal, acompanhando o "
                           "decaimento do Momentum."))
  "Titulo e corpo da nota explicativa do Potencial da oportunidade.")

(defparameter +active-dimensions+
  (list
   (list :key :momentum :label "Momentum" :title "Momentum"
         :body (concatenate 'string
                            "Eixo primário do ranqueamento. Exprime o comportamento e "
                            "recorrência de compra do cliente no tempo para o produto "
                            "indicado. Medida de maturidade para (re)compra. Após o "
                            "engajamento, sofre decaimento temporal."))
   (list :key :economic :label "Retorno" :title "Retorno"
         :body (concatenate 'string
                            "Exprime o potencial econômico da transação, ancorado no "
                            "ticket médio do cliente para aquele produto, com recuo por "
                            "setor."))
   (list :key :affinity :label "Afinidade" :title "Afinidade com o produto"
         :body (concatenate 'string
                            "Exprime interesse potencial do cliente no produto indicado. "
                            "Medida da afinidade histórica do cliente pelo produto, "
                            "ancorada no volume de negócios fechados anteriormente."))
   (list :key :adherence :label "Especialização" :title "Especialização do agente"
         :body (concatenate 'string
                            "Exprime habilidade histórica do agente em obter sucesso na "
                            "venda do produto indicado. Personaliza o ranqueamento por "
                            "agente.")))
  "As quatro dimensoes ativas, na ordem de exibicao, com o rotulo da coluna, o titulo e
o corpo da nota explicativa. As duas dimensoes inertes (Diligencia, Atividade) nao sao
exibidas.")

(defun dimension-weight-percent (key)
  "O peso relativo da dimensao KEY (:momentum, :economic, :affinity ou :adherence) na media
geometrica ponderada, como percentual inteiro derivado dos expoentes correntes do config (a
fonte canonica); a soma dos quatro percentuais pode nao ser exatamente 100 por
arredondamento. Funcao pura sobre os parametros de peso."
  (let ((weight (ecase key
                  (:momentum ls:*weight-momentum*)
                  (:economic ls:*weight-economic*)
                  (:affinity ls:*weight-affinity*)
                  (:adherence ls:*weight-adherence*)))
        (total (+ ls:*weight-momentum* ls:*weight-economic*
                  ls:*weight-affinity* ls:*weight-adherence*)))
    (round (* 100 weight) total)))

(defparameter +justifications+
  (list
   (list :code "disagreement" :title "Discordancia da avaliacao"
         :short "discordancia"
         :description "Julgo o potencial desta oportunidade maior do que o atribuido.")
   (list :code "direct-inquiry" :title "Consulta direta do cliente"
         :short "consulta direta"
         :description "O cliente procurou diretamente sobre este produto.")
   (list :code "other" :title "Outro motivo"
         :short "outro motivo"
         :description "Motivo diverso dos anteriores."))
  "As tres justificativas de engajamento fora do top tier, com o titulo e a descricao
para o modal e um rotulo curto para a lista de engajadas. O codigo casa com
'engagement_justifications' semeado.")

(defun justification-field (code field)
  "O valor de FIELD (:title, :short ou :description) da justificativa de codigo CODE, ou
NIL quando CODE e desconhecido ou nulo."
  (let ((entry (find code +justifications+
                     :key (lambda (j) (getf j :code)) :test #'equal)))
    (and entry (getf entry field))))

(defun justification-short (code)
  "O rotulo curto da justificativa CODE para a lista de engajadas, ou um travessao
quando nao ha justificativa (engajamento dentro do top tier)."
  (or (justification-field code :short) "-"))

;;; --- Filtragem e ordenacao (puras) ---
;;;
;;; A interatividade hibrida aplica filtros e ordenacao por parametros de query
;;; (GET, pagina inteira). Estas funcoes operam sobre as plists ja lidas, sem tocar
;;; o banco: recebem os valores de filtro e a chave de ordenacao e retornam uma nova
;;; lista, deixando a de origem intacta.

(defparameter +filter-fields+
  '((:location . "Localidade") (:sector . "Setor")
    (:series . "Serie do produto") (:product . "Produto"))
  "Os campos de filtro oferecidos, com o rotulo de exibicao. A chave e a mesma da
plist de oportunidade.")

(defparameter +sort-options+
  '((:overall . "Potencial (maior)")
    (:account . "Cliente (A-Z)")
    (:employees . "Porte do cliente")
    (:revenue . "Receita do cliente")
    (:founded . "Data de fundacao")
    (:cadence . "Prazo de decisao")
    (:last-close . "Valor da ultima compra"))
  "As chaves de ordenacao oferecidas, com o rotulo. ':overall' e a ordem de
ranqueamento padrao.")

(defparameter +engaged-filter-fields+
  '((:product . "Produto") (:series . "Serie do produto")
    (:location . "Localidade") (:sector . "Setor"))
  "Os campos de filtro de igualdade da lista de engajadas. A data de engajamento e um
filtro por limiar, tratado a parte no handler.")

(defparameter +engaged-sort-options+
  '((:expire . "Expira em (menor)")
    (:overall . "Potencial (maior)")
    (:account . "Cliente (A-Z)"))
  "As chaves de ordenacao da lista de engajadas. ':expire' (menor tempo restante) e o
padrao; tratada no handler, pois depende do tempo a expirar computado por linha.")

(defun distinct-values (rows key)
  "Os valores distintos e nao nulos da chave KEY em ROWS, em ordem alfabetica, para
compor as opcoes de um filtro."
  (let ((values (remove-duplicates
                 (remove nil (mapcar (lambda (row) (getf row key)) rows))
                 :test #'equal)))
    (sort values #'string< :key #'princ-to-string)))

(defun row-matches-filters-p (row filters)
  "Verdadeiro quando ROW satisfaz todos os pares (CHAVE . VALOR) de FILTERS cujo VALOR
nao e NIL nem vazio. A comparacao e de igualdade sobre o campo correspondente."
  (loop for (key . value) in filters
        always (or (null value) (string= value "")
                   (equal (getf row key) value))))

(defun apply-filters (rows filters)
  "Retorna as linhas de ROWS que satisfazem FILTERS, um alist de (CHAVE . VALOR); os
valores NIL ou vazios nao restringem."
  (remove-if-not (lambda (row) (row-matches-filters-p row filters)) rows))

(defun date-start-ms (string)
  "Converte STRING no formato 'YYYY-MM-DD' no instante UNIX-ms (UTC) do inicio daquele
dia (00:00:00 UTC), ou NIL quando STRING e nulo, vazio ou malformado. O armazenamento e
UNIX-ms em UTC, sem conversao para hora local (ver 'ls:+unix-epoch-universal-time+').
Compartilhada pelos filtros por data do agente e do gerente."
  (when (and (stringp string) (= (length string) 10))
    (let ((year (parse-integer string :start 0 :end 4 :junk-allowed t))
          (month (parse-integer string :start 5 :end 7 :junk-allowed t))
          (day (parse-integer string :start 8 :end 10 :junk-allowed t)))
      (when (and year month day (<= 1 month 12) (<= 1 day 31))
        (let ((universal (encode-universal-time 0 0 0 day month year 0)))
          ;; 'encode-universal-time' normaliza uma data inexistente em vez de recusa-la
          ;; (por exemplo 2026-02-31 torna-se marco); um round-trip por 'decode' confirma
          ;; que dia, mes e ano sobreviveram, rejeitando a data invalida com NIL.
          (multiple-value-bind (s mi h decoded-day decoded-month decoded-year)
              (decode-universal-time universal 0)
            (declare (ignore s mi h))
            (when (and (= decoded-day day) (= decoded-month month)
                       (= decoded-year year))
              (* 1000 (- universal ls:+unix-epoch-universal-time+)))))))))

(defun apply-date-since (rows key value)
  "Retorna as linhas de ROWS cujo instante na chave KEY (UNIX-ms) e maior ou igual ao
inicio do dia de VALUE ('YYYY-MM-DD'); VALUE nulo, vazio ou malformado nao restringe.
Serve aos filtros por data das listas do agente (disponibilizacao e engajamento), sempre
no eixo de tempo real: ':available-at' vem do banco e ':engaged-real' e pre-computado no
enriquecimento a partir do instante virtual."
  (let ((threshold (date-start-ms value)))
    (if threshold
        (remove-if-not (lambda (row)
                         (let ((instant (getf row key)))
                           (and instant (>= instant threshold))))
                       rows)
        rows)))

(defun sort-key-value (row key)
  "O valor de ordenacao de ROW para a chave KEY, com um neutro para o campo ausente."
  (ecase key
    (:overall (or (getf row :overall) 0))
    (:account (or (getf row :account) ""))
    (:employees (or (getf row :employees) 0))
    (:revenue (or (getf row :revenue-amount) 0))
    (:founded (or (getf row :year-established) 0))
    (:cadence (or (getf row :cadence-days) 0))
    (:last-close (or (getf row :last-close-value) 0))))

(defun sort-rows (rows key value-fn alpha-keys)
  "Retorna uma copia de ROWS ordenada pela chave KEY: as chaves em ALPHA-KEYS em ordem
alfabetica crescente sobre o valor textual, as demais em ordem decrescente do valor
numerico. VALUE-FN mapeia (ROW KEY) ao valor de ordenacao. Nao muta ROWS. Esqueleto de
ordenacao partilhado pelas listas do agente e do gerente."
  (if (member key alpha-keys)
      (sort (copy-list rows) #'string< :key (lambda (row) (funcall value-fn row key)))
      (sort (copy-list rows) #'> :key (lambda (row) (funcall value-fn row key)))))

(defun apply-sort (rows key)
  "Ordena as disponiveis por KEY: ':account' em ordem alfabetica crescente, as demais em
ordem decrescente do valor numerico (o padrao ':overall' e o potencial decrescente). Nao
muta ROWS."
  (sort-rows rows key #'sort-key-value '(:account)))

;;; --- Estado do ciclo (aplicacao do gerente) ---
;;;
;;; O acompanhamento do gerente exibe o estado de cada ciclo de 'engagements'. Os
;;; cinco estados sao derivados de (closed_at, outcome, expired): um ciclo aberto
;;; nao tem 'closed_at'; um fechado sem 'outcome' e uma devolucao (:returned), o
;;; quinto estado, ausente dos prototipos e adicionado por decisao de produto; um
;;; 'lost' com 'expired' distingue a expiracao automatica da perda manual.

(defparameter +cycle-states+
  '((:open . "Em curso") (:won . "Won") (:lost . "Lost")
    (:expired . "Expirado") (:returned . "Devolvida"))
  "Os cinco estados de ciclo, na ordem de exibicao, com o rotulo. ':returned'
(devolucao sem desfecho) e o quinto estado, ausente dos prototipos.")

(defun cycle-state (row)
  "O estado do ciclo ROW, derivado de ':closed-at', ':outcome' e ':expired': ':open'
(ciclo aberto, sem fechamento), ':returned' (fechado sem desfecho), ':won', ':expired'
('lost' com marca de expiracao) ou ':lost' ('lost' manual). Funcao pura."
  (let ((closed (getf row :closed-at))
        (outcome (getf row :outcome))
        (expired (getf row :expired)))
    (cond ((null closed) :open)
          ((null outcome) :returned)
          ((string= outcome "won") :won)
          (expired :expired)
          (t :lost))))

(defun cycle-state-label (state)
  "O rotulo de exibicao do estado de ciclo STATE, ou um travessao quando desconhecido.
':expiring' e o estado derivado (ciclo aberto ja alem do horizonte); nao consta de
'+cycle-states+', que lista apenas os estados persistidos filtraveis."
  (if (eq state :expiring)
      "Expirando"
      (or (cdr (assoc state +cycle-states+)) "-")))

(defun cycle-state-class (state)
  "O nome da classe CSS do badge do estado de ciclo STATE, o proprio nome do estado em
caixa baixa ('open', 'won', 'lost', 'expired', 'returned', 'expiring')."
  (string-downcase (symbol-name state)))

(defun cycle-display-state (row)
  "O estado de exibicao do ciclo ROW: ':expiring' quando o ciclo esta aberto e ja alem do
horizonte (marca ':expiring-p'), senao o estado persistido de CYCLE-STATE. E a sobreposicao
logica unica, partilhada pela renderizacao do badge e pelo filtro de desfecho, de modo que
um ciclo logicamente expirado nao seja exibido nem filtrado como 'Em curso'."
  (if (and (getf row :expiring-p) (eq (cycle-state row) :open))
      :expiring
      (cycle-state row)))

;;; --- Filtragem e ordenacao do acompanhamento (puras) ---
;;;
;;; Os filtros do gerente sao heterogeneos, ao contrario dos do agente (todos select
;;; sobre valores distintos): agente e produto por igualdade, conta por subcadeia
;;; insensivel a caixa, desfecho por igualdade sobre o estado de ciclo derivado e a
;;; data de engajamento por limiar inferior. Operam sobre as plists ja lidas.

(defparameter +team-filter-fields+
  '((:agent "Agente" :select)
    (:product "Produto" :select)
    (:account "Conta" :text)
    (:outcome "Desfecho" :outcome)
    (:since "Engajada desde" :date))
  "Os campos de filtro do acompanhamento, cada um '(ID ROTULO TIPO)'. O TIPO governa o
controle de entrada renderizado: ':select' (opcoes dinamicas), ':text', ':outcome'
(os estados de ciclo) e ':date'.")

(defparameter +team-sort-options+
  '((:engaged . "Engajada em (recente)")
    (:closed . "Fechada em (recente)")
    (:overall . "Potencial (maior)")
    (:value . "Valor de fechamento (maior)")
    (:agent . "Agente (A-Z)")
    (:account . "Cliente (A-Z)"))
  "As chaves de ordenacao do acompanhamento, com o rotulo. ':engaged' (engajamento mais
recente) e o padrao.")

(defun team-filter-match-p (row id value)
  "Verdadeiro quando ROW satisfaz o filtro ID com VALOR nao vazio: ':agent' e
':product' por igualdade, ':account' por subcadeia insensivel a caixa, ':outcome' por
igualdade sobre o estado de EXIBICAO do ciclo (de modo que um ciclo aberto ja expirando
nao case com 'Em curso', coerente com o badge que exibe 'Expirando') e ':since' por
engajamento em ou apos o inicio da data. O filtro ':since' compara o instante REAL de
engajamento (':engaged-real', pre-computado no enriquecimento), no mesmo eixo de tempo
real exibido na coluna 'Engajada em', e nao o instante virtual ':engaged-at'."
  (ecase id
    (:agent (equal (getf row :agent-username) value))
    (:product (equal (getf row :product) value))
    (:account (and (search (string-downcase value)
                           (string-downcase (or (getf row :account) "")))
                   t))
    (:outcome (string-equal value (symbol-name (cycle-display-state row))))
    (:since (let ((threshold (date-start-ms value))
                  (engaged (getf row :engaged-real)))
              (and threshold engaged (>= engaged threshold))))))

(defun row-matches-team-filters-p (row filters)
  "Verdadeiro quando ROW satisfaz todos os pares (ID . VALOR) de FILTERS cujo VALOR nao e
NIL nem vazio."
  (loop for (id . value) in filters
        always (or (null value) (string= value "")
                   (team-filter-match-p row id value))))

(defun apply-team-filters (rows filters)
  "Retorna as linhas de ROWS que satisfazem FILTERS, um alist de (ID . VALOR); os valores
NIL ou vazios nao restringem."
  (remove-if-not (lambda (row) (row-matches-team-filters-p row filters)) rows))

(defun team-sort-value (row key)
  "O valor de ordenacao de ROW para a chave KEY do acompanhamento, com um neutro para o
campo ausente."
  (ecase key
    (:engaged (or (getf row :engaged-at) 0))
    (:closed (or (getf row :closed-at) 0))
    (:overall (or (getf row :overall) 0))
    (:value (or (getf row :close-value-amount) 0))
    (:agent (or (getf row :agent-username) ""))
    (:account (or (getf row :account) ""))))

(defun apply-team-sort (rows key)
  "Ordena os ciclos do time por KEY: ':agent' e ':account' em ordem alfabetica crescente,
as demais em ordem decrescente do valor (o padrao ':engaged' e o engajamento mais
recente). Nao muta ROWS."
  (sort-rows rows key #'team-sort-value '(:agent :account)))
