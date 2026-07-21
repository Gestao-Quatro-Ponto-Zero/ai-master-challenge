;;;; view.lisp --- Testes dos auxiliares puros de apresentacao.

(in-package #:leadscorer/web/tests)

(define-test format-money-cases
  ;; Valores em centavos (unidade menor): 284700 = US$ 2.847,00 exibido sem centavos.
  (is equal "US$ 2.847" (leadscorer/web::format-money 284700 "USD"))
  (is equal "US$ 59.787" (leadscorer/web::format-money 5978700 "USD"))
  ;; Centavos nao nulos aparecem com ','.
  (is equal "US$ 2,50" (leadscorer/web::format-money 250 "USD"))
  (is equal "R$ 1.000" (leadscorer/web::format-money 100000 "BRL"))
  ;; Moeda desconhecida exibe o proprio codigo; NIL rende travessao.
  (is equal "XYZ 5" (leadscorer/web::format-money 500 "XYZ"))
  (is equal "-" (leadscorer/web::format-money nil "USD")))

(define-test format-percent-tenths-cases
  (is equal "61,8" (leadscorer/web::format-percent-tenths 618))
  (is equal "100,0" (leadscorer/web::format-percent-tenths 1000))
  (is equal "-" (leadscorer/web::format-percent-tenths nil)))

(define-test fill-class-quantizes
  (is equal "fill-55" (leadscorer/web::fill-class 57))
  (is equal "fill-90" (leadscorer/web::fill-class 90))
  (is equal "fill-5" (leadscorer/web::fill-class 3))
  (is equal "fill-100" (leadscorer/web::fill-class 100))
  ;; NIL (pontuacao ausente) rende a barra vazia.
  (is equal "fill-0" (leadscorer/web::fill-class nil)))

(define-test format-expire-and-soon
  (is equal "17 min" (leadscorer/web::format-expire 17))
  (is equal "04 min" (leadscorer/web::format-expire 4))
  (is equal "-" (leadscorer/web::format-expire nil))
  (true (leadscorer/web::expire-soon-p 4))
  (false (leadscorer/web::expire-soon-p 6))
  (false (leadscorer/web::expire-soon-p nil)))

(define-test arrange-available-marks-top-and-cut
  (let ((rows (list (list :overall 90) (list :overall 80) (list :overall 45)
                    (list :overall 40) (list :overall 30) (list :overall 20))))
    (multiple-value-bind (annotated cut-index)
        (leadscorer/web::arrange-available rows 2 40)
      ;; Ranks 1-based; top tier sao os dois primeiros.
      (is = 1 (getf (first annotated) :rank))
      (true (getf (first annotated) :top-tier-p))
      (true (getf (second annotated) :top-tier-p))
      (false (getf (third annotated) :top-tier-p))
      ;; Primeiro abaixo de 40 e o de potencial 30 (indice 4).
      (is = 4 cut-index))
    ;; Corte zero desativa o corte.
    (multiple-value-bind (annotated cut-index)
        (leadscorer/web::arrange-available rows 2 0)
      (declare (ignore annotated))
      (is eq nil cut-index))))

(define-test justification-labels
  (is equal "consulta direta" (leadscorer/web::justification-short "direct-inquiry"))
  (is equal "outro motivo" (leadscorer/web::justification-short "other"))
  ;; Sem justificativa (dentro do top tier): travessao.
  (is equal "-" (leadscorer/web::justification-short nil))
  (is equal "Discordancia da avaliacao"
      (leadscorer/web::justification-field "disagreement" :title)))

(define-test dimension-weight-percent-derives-from-config
  "D4: o peso exibido de cada dimensao deriva dos expoentes correntes do config, e nao de
texto fixo: 0.5/0.40/0.35/0.25 sobre a soma 1.5 rendem 33/27/23/17."
  (is = 33 (leadscorer/web::dimension-weight-percent :momentum))
  (is = 27 (leadscorer/web::dimension-weight-percent :economic))
  (is = 23 (leadscorer/web::dimension-weight-percent :affinity))
  (is = 17 (leadscorer/web::dimension-weight-percent :adherence)))

;;; --- Aplicacao do gerente: estado de ciclo, filtros e ordenacao ---

(define-test cycle-state-five-states
  ;; Ciclo aberto: sem closed_at.
  (is eq :open (leadscorer/web::cycle-state '(:closed-at nil :outcome nil)))
  ;; Fechado com desfecho won.
  (is eq :won (leadscorer/web::cycle-state '(:closed-at 100 :outcome "won")))
  ;; Lost manual (nao expirado) e lost por expiracao distinguem-se pela marca.
  (is eq :lost (leadscorer/web::cycle-state
                '(:closed-at 100 :outcome "lost" :expired nil)))
  (is eq :expired (leadscorer/web::cycle-state
                   '(:closed-at 100 :outcome "lost" :expired t)))
  ;; Devolvido: fechado sem desfecho (o quinto estado).
  (is eq :returned (leadscorer/web::cycle-state '(:closed-at 100 :outcome nil))))

(define-test cycle-state-labels-and-classes
  (is equal "Em curso" (leadscorer/web::cycle-state-label :open))
  (is equal "Devolvida" (leadscorer/web::cycle-state-label :returned))
  (is equal "Expirado" (leadscorer/web::cycle-state-label :expired))
  (is equal "returned" (leadscorer/web::cycle-state-class :returned))
  (is equal "open" (leadscorer/web::cycle-state-class :open))
  ;; ':expiring' e o estado derivado (ciclo aberto alem do horizonte), fora de
  ;; '+cycle-states+' mas com rotulo e classe proprios.
  (is equal "Expirando" (leadscorer/web::cycle-state-label :expiring))
  (is equal "expiring" (leadscorer/web::cycle-state-class :expiring)))

(define-test date-start-ms-utc
  ;; 1970-01-01 e a epoca UNIX: 0 ms.
  (is = 0 (leadscorer/web::date-start-ms "1970-01-01"))
  ;; 1970-01-02 e um dia depois.
  (is = 86400000 (leadscorer/web::date-start-ms "1970-01-02"))
  ;; Entradas nulas, vazias ou malformadas rendem NIL.
  (is eq nil (leadscorer/web::date-start-ms nil))
  (is eq nil (leadscorer/web::date-start-ms ""))
  (is eq nil (leadscorer/web::date-start-ms "2026-13-01"))
  (is eq nil (leadscorer/web::date-start-ms "nao-e-data"))
  ;; Uma data inexistente e recusada com NIL, nao normalizada silenciosamente:
  ;; 31 de fevereiro nao existe; 29 de fevereiro so em ano bissexto.
  (is eq nil (leadscorer/web::date-start-ms "2026-02-31"))
  (is eq nil (leadscorer/web::date-start-ms "2025-02-29"))
  (true (integerp (leadscorer/web::date-start-ms "2024-02-29"))))

(define-test apply-date-since-threshold
  "B2/B3: o filtro por data mantem as linhas cujo instante na chave e maior ou igual ao
inicio do dia; valor vazio ou malformado nao restringe; instante ausente exclui a linha."
  (let ((rows (list (list :account "A" :available-at 0)
                    (list :account "B" :available-at 86400000)
                    (list :account "C" :available-at nil))))
    ;; Limiar 1970-01-02 (86400000): mantem so B (>=), exclui A (<) e C (nil).
    (let ((result (leadscorer/web::apply-date-since rows :available-at "1970-01-02")))
      (is = 1 (length result))
      (is equal "B" (getf (first result) :account)))
    ;; Limiar 1970-01-01 (0): mantem A e B; C (nil) sempre fora.
    (is = 2 (length (leadscorer/web::apply-date-since rows :available-at "1970-01-01")))
    ;; Valor vazio ou malformado nao restringe: as tres linhas passam.
    (is = 3 (length (leadscorer/web::apply-date-since rows :available-at "")))
    (is = 3 (length (leadscorer/web::apply-date-since rows :available-at "xx")))))

(define-test team-filters-heterogeneous
  (let ((rows (list (list :agent-username "ann" :product "GTX Basic" :account "Golddex"
                          :closed-at nil :outcome nil :engaged-at 200 :engaged-real 200)
                    (list :agent-username "bob" :product "MG Special" :account "Zumgoity"
                          :closed-at 100 :outcome "won" :engaged-at 100 :engaged-real 100)
                    (list :agent-username "ann" :product "MG Special" :account "Goldmine"
                          :closed-at 100 :outcome nil :engaged-at 150 :engaged-real 150))))
    ;; Agente por igualdade: duas linhas de ann.
    (is = 2 (length (leadscorer/web::apply-team-filters rows '((:agent . "ann")))))
    ;; Produto por igualdade.
    (is = 1 (length (leadscorer/web::apply-team-filters rows '((:product . "GTX Basic")))))
    ;; Conta por subcadeia insensivel a caixa: 'gold' casa Golddex e Goldmine.
    (is = 2 (length (leadscorer/web::apply-team-filters rows '((:account . "gold")))))
    ;; Desfecho pelo estado derivado: um won, um devolvido, um aberto.
    (is = 1 (length (leadscorer/web::apply-team-filters rows '((:outcome . "won")))))
    (is = 1 (length (leadscorer/web::apply-team-filters rows '((:outcome . "returned")))))
    (is = 1 (length (leadscorer/web::apply-team-filters rows '((:outcome . "open")))))
    ;; Data de engajamento por limiar sobre o instante REAL (':engaged-real'):
    ;; '1970-01-01' (limiar 0) inclui as tres; '1970-01-02' exclui todas (engaged-real
    ;; pequeno, anterior ao limiar).
    (is = 3 (length (leadscorer/web::apply-team-filters rows '((:since . "1970-01-01")))))
    (is = 0 (length (leadscorer/web::apply-team-filters rows '((:since . "1970-01-02")))))
    ;; Valor vazio nao restringe.
    (is = 3 (length (leadscorer/web::apply-team-filters rows '((:account . "")))))
    ;; Combinacao: ann e devolvido -> uma linha (Goldmine).
    (let ((result (leadscorer/web::apply-team-filters
                   rows '((:agent . "ann") (:outcome . "returned")))))
      (is = 1 (length result))
      (is equal "Goldmine" (getf (first result) :account)))))

(define-test team-filter-outcome-uses-display-state
  "O filtro de desfecho usa o estado de EXIBICAO: um ciclo aberto ja expirando nao casa
com 'Em curso' (open), coerente com o badge 'Expirando'."
  (let ((rows (list (list :agent-username "ann" :account "A" :closed-at nil :outcome nil
                          :expiring-p nil :engaged-at 100)
                    (list :agent-username "bob" :account "B" :closed-at nil :outcome nil
                          :expiring-p t :engaged-at 100))))
    ;; Estado de exibicao: aberto vivo -> :open; aberto expirando -> :expiring.
    (is eq :open (leadscorer/web::cycle-display-state (first rows)))
    (is eq :expiring (leadscorer/web::cycle-display-state (second rows)))
    ;; O filtro 'open' casa so o vivo; o expirando fica de fora.
    (let ((open (leadscorer/web::apply-team-filters rows '((:outcome . "open")))))
      (is = 1 (length open))
      (is equal "A" (getf (first open) :account)))))

(define-test team-since-filter-uses-real-time
  "Regressao A2: o filtro ':since' compara o instante REAL de engajamento
(':engaged-real'), no mesmo eixo de tempo exibido ao gerente, e nao o instante virtual
(':engaged-at'). Uma linha engajada em tempo real dentro do intervalo casa mesmo com um
':engaged-at' virtual fora dele; uma linha com ':engaged-real' anterior ao limiar e
excluida ainda que o seu ':engaged-at' virtual o exceda."
  (let* ((inside (leadscorer/web::date-start-ms "2026-07-01"))
         (outside (leadscorer/web::date-start-ms "2025-07-01"))
         (rows (list (list :account "Recente" :engaged-real inside :engaged-at 0)
                     (list :account "Antiga" :engaged-real outside
                           :engaged-at most-positive-fixnum))))
    (let ((result (leadscorer/web::apply-team-filters
                   rows (list (cons :since "2026-01-01")))))
      (is = 1 (length result))
      (is equal "Recente" (getf (first result) :account)))))

(define-test team-sort-orders
  (let ((rows (list (list :agent-username "bob" :account "Zeta" :engaged-at 100
                          :closed-at 300 :overall 50 :close-value-amount 900)
                    (list :agent-username "ann" :account "Alpha" :engaged-at 300
                          :closed-at 100 :overall 90 :close-value-amount 100))))
    ;; Engajada em (recente): 300 antes de 100.
    (is equal "ann" (getf (first (leadscorer/web::apply-team-sort rows :engaged))
                          :agent-username))
    ;; Potencial (maior): 90 antes de 50.
    (is = 90 (getf (first (leadscorer/web::apply-team-sort rows :overall)) :overall))
    ;; Valor (maior): 900 antes de 100.
    (is = 900 (getf (first (leadscorer/web::apply-team-sort rows :value))
                    :close-value-amount))
    ;; Agente (A-Z): ann antes de bob.
    (is equal "ann" (getf (first (leadscorer/web::apply-team-sort rows :agent))
                          :agent-username))
    ;; Cliente (A-Z): Alpha antes de Zeta.
    (is equal "Alpha" (getf (first (leadscorer/web::apply-team-sort rows :account))
                            :account))
    ;; A origem nao e mutada.
    (is = 100 (getf (first rows) :engaged-at))))
