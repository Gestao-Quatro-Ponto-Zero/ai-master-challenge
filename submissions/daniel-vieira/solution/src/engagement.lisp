;;;; engagement.lisp --- Servicos interativos do ciclo de engajamento.
;;;;
;;;; As transicoes de estado que um agente dispara pela interface: engajar uma
;;;; oportunidade 'prospecting', fechar o ciclo com desfecho (won/lost) e devolver
;;;; sem desfecho. Complementam os servicos automaticos de 'cycle.lisp' (expiracao,
;;;; ranqueamento, decaimento) e honram as mesmas invariantes de persistencia
;;;; (migracao 0002 e 'verify.lisp'): o estado ativo casa 'status' com
;;;; 'engaged_by_id'/'engaged_at'; uma 'prospecting' nao tem ciclo aberto; um ciclo
;;;; fechado com desfecho tem valor de fechamento.
;;;;
;;;; CONTRATO DE TEMPO (ver o cabecalho de 'cycle.lisp'): os instantes 'engaged_at'
;;;; e 'closed_at' vivem na base de tempo VIRTUAL. O chamador passa NOW ja como
;;;; instante virtual, tipicamente '(current-virtual-now model)'; carimbar o tempo
;;;; de parede renderia idade negativa e uma oportunidade que nunca decai nem expira.
;;;;
;;;; Cada servico opera dentro de uma transacao unica e e fail-closed: a
;;;; disponibilidade da oportunidade e verificada por um UPDATE guardado por
;;;; 'status', e o limite de engajamentos e serializado por um lock consultivo por
;;;; agente ('pg_advisory_xact_lock'), de modo que uma corrida com o tick do
;;;; agendador ou com outro engajamento do mesmo agente aborte ou espere, em vez de
;;;; violar uma invariante.
;;;;
;;;; POLITICA DE JUSTIFICATIVA: a regra "engajar fora do top tier exige
;;;; justificativa" e imposta na camada web ('engage-for'), que conhece o
;;;; ranqueamento por agente. Este servico apenas registra a 'justification-id'
;;;; recebida e nao recomputa o top tier; uma segunda via de chamada deve replicar a
;;;; politica.

(in-package #:leadscorer)

;;; --- Condicoes ---

;;; A hierarquia de condicoes e o mecanismo padrao de sinalizacao de erro, nao um
;;; modelo de dados em CLOS: um tipo-base permite ao chamador tratar a familia toda,
;;; e cada subtipo carrega o dado que distingue a situacao para o diagnostico.

(define-condition engagement-error (error) ()
  (:documentation "Tipo-base das falhas dos servicos interativos de engajamento."))

(define-condition engagement-limit-reached (engagement-error)
  ((agent-id :initarg :agent-id :reader engagement-error-agent-id)
   (limit :initarg :limit :reader engagement-error-limit))
  (:report (lambda (condition stream)
             (format stream
                     "O agente ~A ja possui o limite de ~D oportunidades engajadas."
                     (engagement-error-agent-id condition)
                     (engagement-error-limit condition))))
  (:documentation "Sinalizada quando um agente no limite '*MAX-ENGAGEMENTS*' tenta
engajar outra oportunidade."))

(define-condition opportunity-not-available (engagement-error)
  ((opportunity-id :initarg :opportunity-id :reader engagement-error-opportunity-id))
  (:report (lambda (condition stream)
             (format stream
                     "A oportunidade ~A nao esta disponivel para a operacao solicitada."
                     (engagement-error-opportunity-id condition))))
  (:documentation "Sinalizada quando a oportunidade alvo nao esta no estado esperado,
tipicamente por ja ter sido engajada, devolvida ou expirada por outro ator."))

;;; --- Servicos ---

(defun count-agent-engagements (agent-id)
  "O numero de oportunidades atualmente engajadas (status 'engaging') pelo agente
AGENT-ID. Assume conexao ativa."
  (postmodern:query
   "SELECT COUNT(*) FROM opportunities
    WHERE status = 'engaging' AND engaged_by_id = $1"
   agent-id :single))

(defun engage-opportunity (opportunity-id agent-id now &key justification-id)
  "Engaja a oportunidade OPPORTUNITY-ID para o agente AGENT-ID no instante virtual
NOW, com a justificativa opcional JUSTIFICATION-ID (o id de 'engagement_justifications',
NIL dentro do top tier). Insere o ciclo aberto e transiciona a oportunidade para
'engaging', tudo em uma transacao. Assume conexao ativa. Retorna OPPORTUNITY-ID.
Sinaliza ENGAGEMENT-LIMIT-REACHED quando o agente ja atingiu '*MAX-ENGAGEMENTS*' e
OPPORTUNITY-NOT-AVAILABLE quando a oportunidade nao esta mais em 'prospecting'."
  (postmodern:with-transaction ()
    ;; Serializa os engajamentos concorrentes do mesmo agente: o lock consultivo por
    ;; agente e mantido ate o fim da transacao, de modo que a verificacao do limite e
    ;; a insercao sejam atomicas mesmo sobre oportunidades distintas. Sem ele, sob
    ;; READ COMMITTED, dois engajamentos concorrentes poderiam ambos ler a contagem
    ;; no limite menos um e exceder o teto (fail-closed do limite).
    (postmodern:query "SELECT pg_advisory_xact_lock($1)" agent-id)
    (when (>= (count-agent-engagements agent-id) *max-engagements*)
      (error 'engagement-limit-reached :agent-id agent-id :limit *max-engagements*))
    ;; A transicao e guardada por 'status = prospecting': afetar zero linhas
    ;; significa que outro ator ja engajou ou removeu a oportunidade (corrida com o
    ;; tick ou com outro agente), e a transacao aborta sem inserir o ciclo.
    (let ((affected
            (postmodern:execute
             "UPDATE opportunities
              SET status = 'engaging', engaged_by_id = $1, engaged_at = $2
              WHERE id = $3 AND status = 'prospecting'"
             agent-id now opportunity-id)))
      (when (zerop affected)
        (error 'opportunity-not-available :opportunity-id opportunity-id))
      (postmodern:execute
       "INSERT INTO engagements
            (opportunity_id, sales_agent_id, justification_id, engaged_at)
        VALUES ($1, $2, $3, $4)"
       opportunity-id agent-id (sql-value justification-id) now)))
  opportunity-id)

(defun close-engagement (opportunity-id agent-id outcome now)
  "Fecha o ciclo aberto da oportunidade OPPORTUNITY-ID engajada por AGENT-ID com o
desfecho OUTCOME (:won ou :lost) no instante virtual NOW, e devolve a oportunidade a
'prospecting', em uma transacao. Assume conexao ativa. Retorna OPPORTUNITY-ID.
Sinaliza OPPORTUNITY-NOT-AVAILABLE quando nao ha ciclo aberto do agente para a
oportunidade.

Valor de fechamento: um 'won' registra o preco de tabela do produto, dado que o MVP
nao captura o valor negociado (simplificacao deliberada; o preco de tabela e um valor
de catalogo real, nao fabricado). Um 'lost' registra valor zero, na moeda da casa,
como faz a expiracao, satisfazendo a invariante de que um ciclo com desfecho tem
valor de fechamento."
  (check-type outcome (member :won :lost))
  (postmodern:with-transaction ()
    (let* ((price-row (postmodern:query
                       "SELECT p.list_price_amount, p.list_price_currency
                        FROM opportunities o
                        JOIN products p ON p.id = o.product_id
                        WHERE o.id = $1"
                       opportunity-id :row))
           (amount (ecase outcome
                     (:won (first price-row))
                     (:lost 0)))
           (currency (ecase outcome
                       (:won (second price-row))
                       (:lost *seed-currency*)))
           (outcome-string (ecase outcome (:won "won") (:lost "lost")))
           (affected
             (postmodern:execute
              "UPDATE engagements
               SET closed_at = $1, outcome = $2,
                   close_value_amount = $3, close_value_currency = $4
               WHERE opportunity_id = $5 AND sales_agent_id = $6
                 AND closed_at IS NULL"
              now outcome-string (sql-value amount) (sql-value currency)
              opportunity-id agent-id)))
      (when (zerop affected)
        (error 'opportunity-not-available :opportunity-id opportunity-id))
      (postmodern:execute
       "UPDATE opportunities
        SET status = 'prospecting', engaged_by_id = NULL, engaged_at = NULL
        WHERE id = $1"
       opportunity-id)))
  opportunity-id)

(defun return-engagement (opportunity-id agent-id now)
  "Devolve a oportunidade OPPORTUNITY-ID engajada por AGENT-ID a 'prospecting' sem
desfecho, fechando o ciclo aberto (grava 'closed_at' = NOW virtual, deixando
'outcome' nulo), em uma transacao. Assume conexao ativa. Retorna OPPORTUNITY-ID.
Sinaliza OPPORTUNITY-NOT-AVAILABLE quando nao ha ciclo aberto do agente para a
oportunidade. Fechar o ciclo preserva a invariante de que uma 'prospecting' nao tem
ciclo aberto; a ausencia de desfecho dispensa o valor de fechamento."
  (postmodern:with-transaction ()
    (let ((affected
            (postmodern:execute
             "UPDATE engagements SET closed_at = $1
              WHERE opportunity_id = $2 AND sales_agent_id = $3
                AND closed_at IS NULL"
             now opportunity-id agent-id)))
      (when (zerop affected)
        (error 'opportunity-not-available :opportunity-id opportunity-id))
      (postmodern:execute
       "UPDATE opportunities
        SET status = 'prospecting', engaged_by_id = NULL, engaged_at = NULL
        WHERE id = $1"
       opportunity-id)))
  opportunity-id)
