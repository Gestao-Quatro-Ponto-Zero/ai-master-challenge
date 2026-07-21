;;;; cycle.lisp --- Servicos automaticos do ciclo de engajamento.
;;;;
;;;; Implementa o ranqueamento, o decaimento e a expiracao sobre a persistencia
;;;; (9P4D) a partir do motor de scoring ('scoring.lisp', 'model.lisp'). O motor
;;;; opera sobre um retrato estatico (CSV derivados, asof fixo 2017-12-31); a
;;;; persistencia e viva. O ciclo acelerado e uma sobreposicao de RELOGIO VIRTUAL
;;;; ancorado na epoca do seed: 20 minutos reais percorrem o horizonte de
;;;; decaimento (138 dias virtuais). As funcoes puras (relogio, idade, pontuacao)
;;;; sao testaveis sem banco; os drivers assumem uma conexao ativa (WITH-DATABASE),
;;;; como 'seed-database'.
;;;;
;;;; CONTRATO DE TEMPO: os instantes de dominio 'engaged_at' e 'closed_at' vivem na
;;;; base de tempo VIRTUAL (ancorada em '*virtual-epoch*'), nao no tempo de parede.
;;;; O seed grava 'engaged_at' na data historica, que ja e virtual. O caminho
;;;; interativo da Fase 5 (engajar/fechar) DEVE gravar 'engaged_at'/'closed_at' com
;;;; '(virtual-now (now-unix-ms) *virtual-t0* *virtual-epoch* ...)', e nao com
;;;; 'now-unix-ms' cru: um instante em tempo real (~2026) ficaria muito acima do
;;;; tempo virtual corrente (~2017), rendendo idade negativa (limitada a 0) e uma
;;;; oportunidade que nunca decai nem expira. O 'computed_at' de 'opportunity_scores'
;;;; e, ao contrario, tempo de parede real (metadado de frescor).

(in-package #:leadscorer)

;;; --- Parametros de fallback (afinacao de modelo, nao config de operacao) ---

(defparameter *fallback-normalized* 50.0
  "Valor neutro (mediana do percentil) das dimensoes economica e de afinidade para
um par sem registro no modelo estatico (retorno de par antes engajado, ou engajada
alem do horizonte). A aderencia permanece computada, pois independe de
potentials_base.")

(defparameter *fallback-cadence-days* 30.0
  "Cadencia de recompra substituta para a corcova de maturidade quando um par
retorna ao rol sem registro em potentials_base.")

;;; --- Relogio virtual ---

(defvar *clock-fn* 'now-unix-ms
  "Funcao que retorna o instante REAL corrente em UNIX-ms. Vinculavel nos testes
para dispensar o relogio de parede (padrao de '*lookup-user-fn*').")

(defvar *virtual-t0* nil
  "Instante REAL (UNIX-ms) de ancoragem, capturado no start do agendador. Em T0, o
instante virtual e '*VIRTUAL-EPOCH*'.")

(defun clock-now ()
  "O instante real corrente em UNIX-ms, pela indirecao '*CLOCK-FN*'."
  (funcall *clock-fn*))

(defun decay-horizon-days (model)
  "O horizonte de decaimento em dias virtuais do MODEL: o indice maximo do vetor
de decaimento (comprimento menos um). A expiracao ocorre neste horizonte."
  (1- (length (model-decay model))))

(defun clock-compression (horizon-days)
  "O fator de compressao do relogio virtual, como racional exato: quantos
milissegundos virtuais avancam por milissegundo real. HORIZON-DAYS dias virtuais
sao percorridos em '*EXPIRATION-MINUTES*' minutos reais."
  (/ (* horizon-days +ms-per-day+) (expiration-ms)))

(defun virtual-now (real-now t0 epoch horizon-days)
  "O instante virtual (UNIX-ms) correspondente ao instante real REAL-NOW, dada a
ancoragem real T0, a epoca virtual EPOCH e o horizonte HORIZON-DAYS. Puro."
  (+ epoch (round (* (- real-now t0) (clock-compression horizon-days)))))

(defun current-virtual-now (model)
  "O instante virtual corrente, derivado do relogio real e da ancoragem
('*VIRTUAL-T0*', '*VIRTUAL-EPOCH*') e do horizonte do MODEL."
  (virtual-now (clock-now) *virtual-t0* *virtual-epoch* (decay-horizon-days model)))

(defun real-instant-of-virtual (virtual model)
  "O instante REAL (UNIX-ms) que corresponde ao instante VIRTUAL, invertendo a
compressao do relogio: 'real = t0 + (virtual - epoca) / compressao'. Retorna NIL quando
a ancoragem '*VIRTUAL-T0*' ainda nao foi fixada (agendador parado). Util para exibir o
horario real de um evento gravado em tempo virtual, como o engajamento."
  (when *virtual-t0*
    (+ *virtual-t0*
       (round (- virtual *virtual-epoch*)
              (clock-compression (decay-horizon-days model))))))

(defun virtual-age-days (now instant)
  "A idade em dias virtuais de INSTANT ate NOW (ambos UNIX-ms), limitada a zero, ou
NIL quando INSTANT e NIL."
  (when instant (max 0 (floor (- now instant) +ms-per-day+))))

(defun accelerated-age-index (age-days decay-length)
  "O indice no vetor de decaimento para AGE-DAYS, limitado a [0, DECAY-LENGTH-1]."
  (max 0 (min (1- decay-length) age-days)))

(defun cycle-expired-p (age-days horizon-days)
  "Verdadeiro quando AGE-DAYS alcancou ou passou o horizonte HORIZON-DAYS."
  (>= age-days horizon-days))

(defun engagement-expired-p (engaged-at now model)
  "Verdadeiro quando a oportunidade engajada cujo 'engaged_at' virtual e ENGAGED-AT ja
alcancou o horizonte de decaimento do MODEL no instante virtual NOW, isto e, esta
LOGICAMENTE expirada, ainda que o agendador --- o escritor unico da transicao --- so a
feche no proximo tique. Puro dado o MODEL. Retorna NIL quando NOW ou ENGAGED-AT e NIL (o
relogio nao esta ancorado). E a mesma regra que EXPIRE-DUE-OPPORTUNITIES aplica na
escrita, de modo que a exibicao derive da regra logica, nao da cadencia do agendador."
  (let ((age (and now engaged-at (virtual-age-days now engaged-at))))
    (and age (cycle-expired-p age (decay-horizon-days model)) t)))

(defun real-minutes-to-expiration (engaged-at now model)
  "Os minutos de tempo REAL restantes ate a expiracao de uma oportunidade engajada cujo
'engaged_at' virtual e ENGAGED-AT, dado o instante virtual corrente NOW e o MODEL.
Retorna 0 quando a idade ja alcancou o horizonte (ou o horizonte e nulo). Puro dado o
MODEL: nao consulta o relogio. Como '*EXPIRATION-MINUTES*' minutos reais percorrem o
horizonte inteiro, cada dia virtual restante vale 'expiration/horizonte' minutos reais.
Retorna um racional; o chamador arredonda para exibicao."
  (let ((horizon-days (decay-horizon-days model)))
    (if (plusp horizon-days)
        (let ((remaining-days
                (max 0 (- horizon-days (or (virtual-age-days now engaged-at) 0)))))
          (/ (* remaining-days (expiration-ms)) (* horizon-days 60000)))
        0)))

;;; --- Indices nome->struct do modelo ---

(defun index-pairs (model)
  "Uma hash-table de (ACCOUNT . PRODUCT) para a struct PAIR do MODEL, para casar
oportunidades vivas por nome."
  (let ((table (make-hash-table :test #'equal)))
    (dolist (pair (model-pairs model) table)
      (setf (gethash (cons (pair-account pair) (pair-product pair)) table) pair))))

(defun index-opportunities (model)
  "Uma hash-table de (ACCOUNT . PRODUCT) para a struct OPPORTUNITY de
initiated_base, para casar engajadas vivas por nome."
  (let ((table (make-hash-table :test #'equal)))
    (dolist (opp (model-opportunities model) table)
      (setf (gethash (cons (opportunity-account opp) (opportunity-product opp))
                     table)
            opp))))

(defun median-cadence (model)
  "A mediana das cadencias de recompra dos pares do MODEL, ou
'*FALLBACK-CADENCE-DAYS*' quando nenhum par tem cadencia."
  (let* ((cadences (sort (loop for pair in (model-pairs model)
                               for cadence = (pair-cadence-days pair)
                               when cadence collect cadence)
                         #'<))
         (n (length cadences)))
    (cond ((zerop n) *fallback-cadence-days*)
          ((oddp n) (nth (floor n 2) cadences))
          (t (/ (+ (nth (1- (floor n 2)) cadences) (nth (floor n 2) cadences)) 2)))))

;;; --- Pontuacao de linhas (puras dado o MODEL) ---

(defun fallback-scored (agent account product momentum model)
  "Uma struct SCORED para um par SEM registro no modelo estatico: economico e
afinidade recebem o neutro '*FALLBACK-NORMALIZED*'; a aderencia e computada e
normalizada por AGENT e PRODUCT; MOMENTUM (em [0,1]) e fornecido."
  (let ((economic *fallback-normalized*)
        (affinity *fallback-normalized*)
        (adherence (normalize-value
                    (adherence-value agent product (model-adherence model))
                    (model-adherence-values model))))
    (make-scored :agent agent :account account :product product
                 :economic economic :affinity affinity :adherence adherence
                 :momentum momentum
                 :composite (composite economic affinity adherence momentum))))

(defun score-prospecting (agent account product pair live-closed-at now
                          fallback-cadence model)
  "A struct SCORED de uma oportunidade 'prospecting'. Sem fechamento vivo
(LIVE-CLOSED-AT nil), reproduz a maturidade estatica de SCORE-PAIR, preservando o
score validado. Com fechamento vivo, computa a maturidade a partir da idade virtual
desde o fechamento em NOW (devolucao com potencial decaido, recuperando pela
corcova). Sem PAIR no MODEL, aplica o fallback neutro com FALLBACK-CADENCE."
  (cond
    ((and pair (null live-closed-at))
     (score-pair agent pair model))
    (pair
     (let* ((days-since (virtual-age-days now live-closed-at))
            (momentum (momentum-maturity days-since (pair-cadence-days pair))))
       (score-triple agent account product
                     (pair-economic-value pair)
                     (pair-affinity-value (pair-won-count pair)
                                          (pair-sector-avg pair))
                     momentum model)))
    (t
     ;; Sem fechamento vivo, DAYS-SINCE fica NIL para que MOMENTUM-MATURITY renda a
     ;; maturidade neutra (*MATURITY-NEUTRAL*), e nao zero: um par nunca fechado nao
     ;; e um recem-fechado. Com fechamento vivo, a idade virtual rege a corcova.
     (let* ((days-since (and live-closed-at (virtual-age-days now live-closed-at)))
            (momentum (momentum-maturity days-since fallback-cadence)))
       (fallback-scored agent account product momentum model)))))

(defun score-engaging (agent account product opportunity age-index model)
  "A struct SCORED de uma oportunidade 'engaging', com o momentum de decaimento no
indice de idade AGE-INDEX. Com OPPORTUNITY (features de initiated_base), usa
SCORE-TRIPLE; sem ela, aplica o fallback neutro."
  (let ((momentum (momentum-decay age-index (model-decay model))))
    (if opportunity
        (score-triple agent account product
                      (opportunity-economic-value opportunity)
                      (pair-affinity-value (opportunity-won-count opportunity)
                                           (opportunity-sector-avg opportunity))
                      momentum model)
        (fallback-scored agent account product momentum model))))

(defun score->int (x)
  "Converte o real X para inteiro na faixa [0,100], arredondando half-to-even."
  (max 0 (min 100 (round x))))

;;; --- Persistencia dos scores (assumem transacao ativa) ---

(defun upsert-score (opportunity-id agent-id scored computed-at)
  "Insere ou atualiza a linha de 'opportunity_scores' de OPPORTUNITY-ID e AGENT-ID
a partir de SCORED, com COMPUTED-AT (instante real). As dimensoes inertes
(closing_time, inactivity) ficam nulas por omissao."
  (postmodern:execute
   "INSERT INTO opportunity_scores
        (opportunity_id, sales_agent_id, score_overall, score_economic,
         score_affinity, score_momentum, score_adherence, computed_at)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    ON CONFLICT (opportunity_id, sales_agent_id) DO UPDATE SET
        score_overall = EXCLUDED.score_overall,
        score_economic = EXCLUDED.score_economic,
        score_affinity = EXCLUDED.score_affinity,
        score_momentum = EXCLUDED.score_momentum,
        score_adherence = EXCLUDED.score_adherence,
        computed_at = EXCLUDED.computed_at"
   opportunity-id agent-id
   (score->int (scored-composite scored))
   (score->int (scored-economic scored))
   (score->int (scored-affinity scored))
   (score->int (* 100 (scored-momentum scored)))
   (score->int (scored-adherence scored))
   computed-at))

;;; --- Drivers dos tres servicos ---

(defun expire-due-opportunities (model &key (now (current-virtual-now model)))
  "Encerra os ciclos das oportunidades 'engaging' cuja idade virtual alcancou o
horizonte de decaimento e as devolve a 'prospecting', registrando o desfecho 'lost'
com o indicador de expiracao. Fechar o ciclo aberto (em vez de inserir novo)
preserva a invariante de que uma 'prospecting' nao tem ciclo aberto. Assume conexao
ativa. Retorna o numero de oportunidades expiradas. NOW e o instante virtual."
  (let ((cutoff (- now (* (decay-horizon-days model) +ms-per-day+))))
    (postmodern:with-transaction ()
      ;; O ciclo expirado e um 'lost' sem venda: grava valor de fechamento zero e a
      ;; moeda da casa, segundo a convencao do seed ('*seed-currency*'), para
      ;; satisfazer a invariante de 'verify-persistence' (um ciclo fechado com
      ;; desfecho tem valor de fechamento).
      (postmodern:execute
       "UPDATE engagements SET closed_at = $1, outcome = 'lost', expired = TRUE,
               close_value_amount = 0, close_value_currency = $2
        WHERE closed_at IS NULL
          AND opportunity_id IN (SELECT id FROM opportunities
                                 WHERE status = 'engaging' AND engaged_at <= $3)"
       now *seed-currency* cutoff)
      (postmodern:execute
       "UPDATE opportunities SET status = 'prospecting', engaged_by_id = NULL,
               engaged_at = NULL
        WHERE status = 'engaging' AND engaged_at <= $1"
       cutoff))))

(defun rank-prospecting-opportunities (model &key (now (current-virtual-now model))
                                             (computed-at (clock-now)))
  "Recomputa e persiste, por oportunidade 'prospecting' e agente, a pontuacao em
'opportunity_scores', a partir do MODEL. Reconcilia removendo as linhas de
oportunidades nao 'prospecting'. Assume conexao ativa. Retorna o numero de linhas
escritas. NOW e o instante virtual; COMPUTED-AT o instante real de observabilidade."
  (let ((pairs (index-pairs model))
        (fallback-cadence (median-cadence model))
        (closes (make-hash-table :test #'eql))
        (written 0))
    ;; As leituras (agentes, prospecting, fechamentos) ocorrem DENTRO da transacao,
    ;; junto do DELETE de reconciliacao e dos upserts, para que a escrita seja
    ;; atomica com a leitura e nao veja um estado intermediario de um engajamento
    ;; concorrente (fronteira com a Fase 5). No MVP so o thread do agendador escreve.
    (postmodern:with-transaction ()
      (let ((agents (postmodern:query
                     "SELECT id, name FROM sales_agents ORDER BY id"))
            (prospecting (postmodern:query
                          "SELECT o.id, a.name, p.name
                           FROM opportunities o
                           JOIN accounts a ON a.id = o.account_id
                           JOIN products p ON p.id = o.product_id
                           WHERE o.status = 'prospecting'")))
        ;; So os fechamentos COM desfecho (won/lost) contam como transacao recente
        ;; que decai o momentum pela corcova de maturidade. Uma devolucao sem desfecho
        ;; fecha o ciclo mas nao e uma transacao: a oportunidade reverte a linha de
        ;; base, retornando ao seu ranqueamento anterior (ver RESCORE-OPPORTUNITY).
        (dolist (row (postmodern:query
                      "SELECT opportunity_id, MAX(closed_at)
                       FROM engagements
                       WHERE closed_at IS NOT NULL AND outcome IS NOT NULL
                         AND closed_at > $1
                       GROUP BY opportunity_id"
                      *virtual-epoch*))
          (setf (gethash (first row) closes) (second row)))
        (postmodern:execute
         "DELETE FROM opportunity_scores
          WHERE opportunity_id IN (SELECT id FROM opportunities
                                   WHERE status <> 'prospecting')")
        (dolist (opp prospecting)
          (destructuring-bind (opp-id account product) opp
            (let ((pair (gethash (cons account product) pairs))
                  (live-closed (gethash opp-id closes)))
              (dolist (agent agents)
                (destructuring-bind (agent-id agent-name) agent
                  (upsert-score opp-id agent-id
                                (score-prospecting agent-name account product pair
                                                   live-closed now fallback-cadence
                                                   model)
                                computed-at)
                  (incf written))))))))
    written))

(defun decay-engaged-opportunities (model &key (now (current-virtual-now model))
                                          (computed-at (clock-now)))
  "Recomputa e persiste a pontuacao decaida da linha do agente engajador de cada
oportunidade 'engaging', a partir do MODEL. Assume conexao ativa. Retorna o numero
de linhas escritas. NOW e o instante virtual."
  (let ((opportunities (index-opportunities model))
        (decay-length (length (model-decay model)))
        (engaged (postmodern:query
                  "SELECT o.id, a.name, p.name, o.engaged_by_id, ag.name,
                          o.engaged_at
                   FROM opportunities o
                   JOIN accounts a ON a.id = o.account_id
                   JOIN products p ON p.id = o.product_id
                   JOIN sales_agents ag ON ag.id = o.engaged_by_id
                   WHERE o.status = 'engaging'"))
        (written 0))
    (postmodern:with-transaction ()
      (dolist (row engaged)
        (destructuring-bind (opp-id account product agent-id agent-name engaged-at)
            row
          (let ((age-index (accelerated-age-index
                            (virtual-age-days now engaged-at) decay-length))
                (opp (gethash (cons account product) opportunities)))
            (upsert-score opp-id agent-id
                          (score-engaging agent-name account product opp age-index
                                          model)
                          computed-at)
            (incf written)))))
    written))

(defun rescore-opportunity (opportunity-id model
                            &key (now (current-virtual-now model))
                                 (computed-at (clock-now)))
  "Recomputa e persiste as pontuacoes de UMA oportunidade 'prospecting' (OPPORTUNITY-ID)
para todos os agentes, a partir do MODEL, no caminho interativo apos um desfecho ou uma
devolucao. Evita a defasagem ate o proximo tick do agendador: sem ela, as linhas antigas
(anteriores ao engajamento) permaneceriam ate o tick, exibindo a oportunidade com o
ranqueamento defasado. Aplica a mesma logica de RANK-PROSPECTING-OPPORTUNITIES, restrita a
esta oportunidade, com a mesma regra de fechamento vivo (apenas desfechos won/lost decaem;
uma devolucao reverte a linha de base). Assume conexao ativa e a oportunidade em
'prospecting'. NOW e o instante virtual; COMPUTED-AT o real. Retorna o numero de linhas
escritas."
  (let ((pairs (index-pairs model))
        (fallback-cadence (median-cadence model))
        (written 0))
    (postmodern:with-transaction ()
      (let ((info (postmodern:query
                   "SELECT a.name, p.name FROM opportunities o
                    JOIN accounts a ON a.id = o.account_id
                    JOIN products p ON p.id = o.product_id
                    WHERE o.id = $1 AND o.status = 'prospecting'"
                   opportunity-id :row))
            (agents (postmodern:query
                     "SELECT id, name FROM sales_agents ORDER BY id")))
        (when info
          (destructuring-bind (account product) info
            (let* ((pair (gethash (cons account product) pairs))
                   ;; MAX sobre um conjunto vazio (sem desfecho) retorna o NULL do SQL,
                   ;; que o Postmodern rende como ':null'; INTEGERP o coage a NIL, o
                   ;; sinal de "sem fechamento vivo" esperado por SCORE-PROSPECTING.
                   (max-close (postmodern:query
                               "SELECT MAX(closed_at) FROM engagements
                                WHERE opportunity_id = $1 AND outcome IS NOT NULL
                                  AND closed_at > $2"
                               opportunity-id *virtual-epoch* :single))
                   (live-closed (when (integerp max-close) max-close)))
              (dolist (agent agents)
                (destructuring-bind (agent-id agent-name) agent
                  (upsert-score opportunity-id agent-id
                                (score-prospecting agent-name account product pair
                                                   live-closed now fallback-cadence
                                                   model)
                                computed-at)
                  (incf written))))))))
    written))

(defun run-cycle-tick (model &key (now (current-virtual-now model)))
  "Executa um tick do ciclo na ordem expiracao, ranqueamento e decaimento, cada um
em sua transacao. Assume conexao ativa. Retorna, como valores, o numero de
oportunidades expiradas, linhas ranqueadas e linhas decaidas. NOW e o instante
virtual corrente. Um unico thread sequencial executa o tick, o que evita corridas
sem travas. A ordem dos efeitos e preservada pela avaliacao sequencial de LET."
  (let ((expired (expire-due-opportunities model :now now))
        (ranked (rank-prospecting-opportunities model :now now))
        (decayed (decay-engaged-opportunities model :now now)))
    (values expired ranked decayed)))
