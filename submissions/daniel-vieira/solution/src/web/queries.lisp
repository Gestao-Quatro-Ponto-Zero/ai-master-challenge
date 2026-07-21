;;;; queries.lisp --- Consultas de identificação por seleção.

(in-package #:leadscorer/web)

;;; As consultas de login leem os usuários semeados e validam a seleção contra
;;; o banco, sempre restritas ao papel da aplicação corrente, o que reforça a
;;; segregação: um nome de usuário do papel oposto não encontra linha e é
;;; recusado. O nome de usuário é entrada externa e trafega como parâmetro
;;; vinculado ($1); a tabela é escolhida por ECASE sobre o papel interno, nunca
;;; interpolada. As indireções '*list-usernames-fn*' e '*lookup-user-fn*'
;;; permitem exercitar as rotas sem um banco vivo nos testes.

(defun db-list-usernames (role)
  "Retorna a lista dos nomes de usuário semeados do papel ROLE (:agent ou
:manager), em ordem alfabética, lida do banco."
  (ls:with-database
    (ecase role
      (:agent
       (postmodern:query
        "SELECT username FROM sales_agents ORDER BY username" :column))
      (:manager
       (postmodern:query
        "SELECT username FROM sales_managers ORDER BY username" :column)))))

(defvar *list-usernames-fn* 'db-list-usernames
  "Função que lista os nomes de usuário de um papel. Vinculável nos testes para
dispensar um banco vivo.")

(defun list-usernames (role)
  "Retorna a lista dos nomes de usuário oferecidos no login do papel ROLE."
  (funcall *list-usernames-fn* role))

(defun db-lookup-user (role username)
  "Retorna o identificador do usuário do papel ROLE cujo nome de usuário é
USERNAME, ou NIL quando não existe tal usuário nesse papel."
  (ls:with-database
    (ecase role
      (:agent
       (postmodern:query
        "SELECT id FROM sales_agents WHERE username = $1" username :single))
      (:manager
       (postmodern:query
        "SELECT id FROM sales_managers WHERE username = $1" username :single)))))

(defvar *lookup-user-fn* 'db-lookup-user
  "Função que valida um nome de usuário de um papel. Vinculável nos testes para
dispensar um banco vivo.")

(defun lookup-user (role username)
  "Retorna o identificador do usuário do papel ROLE com nome USERNAME, ou NIL
quando a seleção é inválida ou pertence ao papel oposto."
  (funcall *lookup-user-fn* role username))

;;; --- Consultas de oportunidades ---
;;;
;;; As linhas retornam como plists de chaves explicitas, de modo que a
;;; apresentacao consuma campos nomeados, nao posicoes. Cada consulta liga o
;;; contexto do banco (conta, produto) as pontuacoes por agente de
;;; 'opportunity_scores'. Os dois campos que residem apenas no modelo estatico
;;; (Prazo de decisao, Ultima compra) sao acrescentados depois por
;;; ENRICH-ROWS-WITH-MODEL. O identificador do agente e vinculado como $1.

(defun denull (value)
  "NIL quando VALUE e o marcador de NULL do Postmodern (o keyword ':null'); senao
VALUE. O Postmodern rende o NULL de SQL como ':null', e a apresentacao trata a
ausencia como NIL: as colunas anulaveis que entram por juncao externa (o potencial
das listas de engajadas do agente e do time, o desfecho e o valor de fechamento dos
ciclos) ou que ficam vazias ate o fechamento sao normalizadas por esta funcao."
  (if (eq value :null) nil value))

(defun prospecting-row->plist (row)
  "Converte uma linha da consulta de disponiveis em uma plist de campos nomeados."
  (destructuring-bind (id account sector location employees revenue-amount
                       revenue-currency year-established product series
                       overall momentum economic affinity adherence created-at)
      row
    (list :opportunity-id id
          :account account :product product :series series
          :sector sector :location location :employees employees
          :revenue-amount revenue-amount :revenue-currency revenue-currency
          :year-established year-established :available-at created-at
          :overall overall :momentum momentum :economic economic
          :affinity affinity :adherence adherence)))

(defun db-list-prospecting-for-agent (agent-id)
  "Lista as oportunidades 'prospecting' com a pontuacao do agente AGENT-ID e o
contexto de conta e produto, como plists, ordenadas por potencial decrescente e
desempatadas pelo id da oportunidade. Le do banco."
  (ls:with-database
    (mapcar #'prospecting-row->plist
            (postmodern:query
             "SELECT o.id, a.name, a.sector, a.location, a.employees,
                     a.revenue_amount, a.revenue_currency, a.year_established,
                     p.name, p.series,
                     s.score_overall, s.score_momentum, s.score_economic,
                     s.score_affinity, s.score_adherence, o.created_at
              FROM opportunities o
              JOIN accounts a ON a.id = o.account_id
              JOIN products p ON p.id = o.product_id
              JOIN opportunity_scores s
                   ON s.opportunity_id = o.id AND s.sales_agent_id = $1
              WHERE o.status = 'prospecting'
              ORDER BY s.score_overall DESC, o.id ASC"
             agent-id))))

(defvar *list-prospecting-fn* 'db-list-prospecting-for-agent
  "Funcao que lista as disponiveis de um agente. Vinculavel nos testes.")

(defun list-prospecting-for-agent (agent-id)
  "Lista as oportunidades disponiveis ranqueadas para o agente AGENT-ID."
  (funcall *list-prospecting-fn* agent-id))

(defun engaged-row->plist (row)
  "Converte uma linha da consulta de engajadas em uma plist de campos nomeados."
  (destructuring-bind (id account sector location product series
                       overall momentum economic affinity adherence
                       engaged-at justification-code)
      row
    (list :opportunity-id id
          :account account :product product :series series
          :sector sector :location location
          :overall (denull overall) :momentum (denull momentum)
          :economic (denull economic) :affinity (denull affinity)
          :adherence (denull adherence)
          :engaged-at engaged-at :justification-code (denull justification-code))))

(defun db-list-engaged-for-agent (agent-id)
  "Lista as oportunidades engajadas pelo agente AGENT-ID com a pontuacao decaida, o
instante de engajamento e o codigo da justificativa (NIL dentro do top tier), como
plists, ordenadas pelo engajamento mais antigo. Le do banco. A pontuacao entra por
juncao externa, degradando para NIL na janela rara entre o engajamento e o proximo
tick do agendador."
  (ls:with-database
    (mapcar #'engaged-row->plist
            (postmodern:query
             "SELECT o.id, a.name, a.sector, a.location, p.name, p.series,
                     s.score_overall, s.score_momentum, s.score_economic,
                     s.score_affinity, s.score_adherence,
                     o.engaged_at, j.code
              FROM opportunities o
              JOIN accounts a ON a.id = o.account_id
              JOIN products p ON p.id = o.product_id
              JOIN engagements e
                   ON e.opportunity_id = o.id AND e.closed_at IS NULL
              LEFT JOIN engagement_justifications j ON j.id = e.justification_id
              LEFT JOIN opportunity_scores s
                   ON s.opportunity_id = o.id AND s.sales_agent_id = $1
              WHERE o.status = 'engaging' AND o.engaged_by_id = $1
              ORDER BY o.engaged_at ASC"
             agent-id))))

(defvar *list-engaged-fn* 'db-list-engaged-for-agent
  "Funcao que lista as engajadas de um agente. Vinculavel nos testes.")

(defun list-engaged-for-agent (agent-id)
  "Lista as oportunidades engajadas pelo agente AGENT-ID."
  (funcall *list-engaged-fn* agent-id))

(defun kpis-plist (cycles wins losses won-sum won-time)
  "A plist de indicadores acumulados a partir dos agregados de ciclos: CYCLES (total),
WINS, LOSSES, WON-SUM (soma dos valores de fechamento 'won', inteiro na unidade menor) e
WON-TIME (soma das duracoes 'won', em ms). As divisoes (taxa de sucesso, ticket medio,
tempo medio) usam arredondamento do banqueiro ('round'). Chaves: :cycles, :wins, :losses,
:success-rate-tenths (decimos de ponto percentual, ou NIL sem ciclos fechados),
:avg-ticket-amount (ou NIL sem 'won'), :total-sales-amount, :avg-days (ou NIL sem 'won') e
:currency. Funcao pura, partilhada pelos indicadores do agente e do time, de modo que a
mecanica dos indicadores resida num unico lugar."
  (let ((closed (+ wins losses)))
    (list :cycles cycles :wins wins :losses losses
          :success-rate-tenths (when (plusp closed) (round (* wins 1000) closed))
          :avg-ticket-amount (when (plusp wins) (round won-sum wins))
          :total-sales-amount won-sum
          :avg-days (when (plusp wins) (round won-time (* wins ls:+ms-per-day+)))
          :currency ls:*seed-currency*)))

(defun db-agent-kpis (agent-id)
  "Retorna a plist dos indicadores acumulados do agente AGENT-ID, computados sobre os
ciclos de 'engagements'. Os valores monetarios sao inteiros na unidade menor; as
divisoes (taxa de sucesso, ticket medio, tempo medio) usam arredondamento do banqueiro
('round'). Chaves: :cycles, :wins, :losses, :success-rate-tenths (decimos de ponto
percentual, ou NIL sem ciclos fechados), :avg-ticket-amount (ou NIL sem 'won'),
:total-sales-amount, :avg-days (ou NIL sem 'won') e :currency. Le do banco."
  (ls:with-database
    (destructuring-bind (cycles wins losses won-sum won-time)
        (postmodern:query
         "SELECT COUNT(*),
                 COUNT(*) FILTER (WHERE outcome = 'won'),
                 COUNT(*) FILTER (WHERE outcome = 'lost'),
                 COALESCE(SUM(close_value_amount) FILTER (WHERE outcome = 'won'), 0),
                 COALESCE(SUM(closed_at - engaged_at) FILTER (WHERE outcome = 'won'), 0)
          FROM engagements
          WHERE sales_agent_id = $1"
         agent-id :row)
      (kpis-plist cycles wins losses won-sum won-time))))

(defvar *agent-kpis-fn* 'db-agent-kpis
  "Funcao que computa os indicadores de um agente. Vinculavel nos testes.")

(defun agent-kpis (agent-id)
  "Os indicadores acumulados do agente AGENT-ID."
  (funcall *agent-kpis-fn* agent-id))

(defun db-justifications ()
  "Retorna as justificativas de engajamento semeadas como plists '(:id I :code C)',
em ordem de id, para resolver o codigo submetido em um engajamento fora do top tier.
Le do banco."
  (ls:with-database
    (mapcar (lambda (row)
              (destructuring-bind (id code) row (list :id id :code code)))
            (postmodern:query
             "SELECT id, code FROM engagement_justifications ORDER BY id"))))

(defvar *justifications-fn* 'db-justifications
  "Funcao que lista as justificativas de engajamento. Vinculavel nos testes.")

(defun justifications ()
  "As justificativas de engajamento oferecidas fora do top tier."
  (funcall *justifications-fn*))

;;; --- Consultas do time (aplicacao do gerente) ---
;;;
;;; A aplicacao do gerente e somente leitura. O time e o conjunto de
;;; 'sales_agents' cujo 'sales_manager_id' e o do gerente da sessao, escopado por
;;; JUNCAO e vinculado como $1. As consultas espelham as do agente (indicadores,
;;; engajadas), agregando ou listando sobre o time em vez de um unico agente, e
;;; retornam plists de chaves explicitas.

(defun db-team-agents (manager-id)
  "Lista os agentes do time do gerente MANAGER-ID como plists '(:id I :name N
:username U)', em ordem de nome de usuario. Serve as opcoes do filtro por agente e
a contagem do time. Le do banco."
  (ls:with-database
    (mapcar (lambda (row)
              (destructuring-bind (id name username) row
                (list :id id :name name :username username)))
            (postmodern:query
             "SELECT id, name, username FROM sales_agents
              WHERE sales_manager_id = $1
              ORDER BY username"
             manager-id))))

(defvar *team-agents-fn* 'db-team-agents
  "Funcao que lista os agentes de um time. Vinculavel nos testes.")

(defun team-agents (manager-id)
  "Os agentes do time do gerente MANAGER-ID."
  (funcall *team-agents-fn* manager-id))

(defun db-team-kpis (manager-id)
  "Retorna a plist dos indicadores agregados do time do gerente MANAGER-ID,
computados sobre os ciclos de 'engagements' dos seus agentes. Espelha
DB-AGENT-KPIS, trocando o escopo de um agente pelo do time via
'sales_manager_id'. Mesmas chaves e mesmas regras (dinheiro inteiro na unidade
menor, arredondamento do banqueiro nas divisoes). Le do banco."
  (ls:with-database
    (destructuring-bind (cycles wins losses won-sum won-time)
        (postmodern:query
         "SELECT COUNT(*),
                 COUNT(*) FILTER (WHERE e.outcome = 'won'),
                 COUNT(*) FILTER (WHERE e.outcome = 'lost'),
                 COALESCE(SUM(e.close_value_amount) FILTER (WHERE e.outcome = 'won'), 0),
                 COALESCE(SUM(e.closed_at - e.engaged_at) FILTER (WHERE e.outcome = 'won'), 0)
          FROM engagements e
          JOIN sales_agents sa ON sa.id = e.sales_agent_id
          WHERE sa.sales_manager_id = $1"
         manager-id :row)
      (kpis-plist cycles wins losses won-sum won-time))))

(defvar *team-kpis-fn* 'db-team-kpis
  "Funcao que computa os indicadores de um time. Vinculavel nos testes.")

(defun team-kpis (manager-id)
  "Os indicadores agregados do time do gerente MANAGER-ID."
  (funcall *team-kpis-fn* manager-id))

(defun team-engaged-row->plist (row)
  "Converte uma linha da consulta de engajadas do time em uma plist de campos
nomeados."
  (destructuring-bind (id agent-username account product series
                       overall engaged-at justification-code)
      row
    (list :opportunity-id id :agent-username agent-username
          :account account :product product :series series
          :overall (denull overall) :engaged-at engaged-at
          :justification-code (denull justification-code))))

(defun db-team-engaged (manager-id)
  "Lista as oportunidades engajadas em curso (ciclo aberto) pelos agentes do time
do gerente MANAGER-ID, como plists, com a identidade do agente, o contexto de
conta e produto, a pontuacao corrente e o instante de engajamento, ordenadas pelo
engajamento mais antigo. Serve a lista de destaque da tela inicial. A pontuacao
entra por juncao externa, degradando para NIL na janela entre o engajamento e o
proximo tick do agendador. Le do banco."
  (ls:with-database
    (mapcar #'team-engaged-row->plist
            (postmodern:query
             "SELECT o.id, sa.username, a.name, p.name, p.series,
                     s.score_overall, o.engaged_at, j.code
              FROM opportunities o
              JOIN accounts a ON a.id = o.account_id
              JOIN products p ON p.id = o.product_id
              JOIN engagements e
                   ON e.opportunity_id = o.id AND e.closed_at IS NULL
              JOIN sales_agents sa ON sa.id = e.sales_agent_id
              LEFT JOIN engagement_justifications j ON j.id = e.justification_id
              LEFT JOIN opportunity_scores s
                   ON s.opportunity_id = o.id AND s.sales_agent_id = e.sales_agent_id
              WHERE o.status = 'engaging' AND sa.sales_manager_id = $1
              ORDER BY o.engaged_at ASC"
             manager-id))))

(defvar *team-engaged-fn* 'db-team-engaged
  "Funcao que lista as engajadas em curso de um time. Vinculavel nos testes.")

(defun team-engaged (manager-id)
  "As oportunidades engajadas em curso pelo time do gerente MANAGER-ID."
  (funcall *team-engaged-fn* manager-id))

(defun team-cycle-row->plist (row)
  "Converte uma linha da consulta de ciclos do time em uma plist de campos
nomeados."
  (destructuring-bind (id agent-username account product series overall
                       engaged-at closed-at outcome expired justification-code
                       close-value-amount close-value-currency)
      row
    (list :engagement-id id :agent-username agent-username
          :account account :product product :series series
          :overall (denull overall) :engaged-at engaged-at
          :closed-at (denull closed-at)
          :outcome (denull outcome) :expired expired
          :justification-code (denull justification-code)
          :close-value-amount (denull close-value-amount)
          :close-value-currency (denull close-value-currency))))

(defun db-team-cycles (manager-id)
  "Lista todos os ciclos de engajamento (abertos e fechados) dos agentes do time do
gerente MANAGER-ID, como plists, com a identidade do agente, o contexto de conta e
produto, a pontuacao corrente do par, os instantes de engajamento e fechamento, o
desfecho, a marca de expiracao, a justificativa e o valor de fechamento, ordenados
pelo engajamento mais recente. Serve a visao de acompanhamento. A pontuacao entra
por juncao externa: para um ciclo fechado a linha de 'opportunity_scores', que e o
ranqueamento corrente do par, pode nao existir, caso em que o potencial degrada
para NIL (exibido com traco). Le do banco."
  (ls:with-database
    (mapcar #'team-cycle-row->plist
            (postmodern:query
             "SELECT e.id, sa.username, a.name, p.name, p.series,
                     s.score_overall, e.engaged_at, e.closed_at, e.outcome,
                     e.expired, j.code, e.close_value_amount, e.close_value_currency
              FROM engagements e
              JOIN sales_agents sa ON sa.id = e.sales_agent_id
              JOIN opportunities o ON o.id = e.opportunity_id
              JOIN accounts a ON a.id = o.account_id
              JOIN products p ON p.id = o.product_id
              LEFT JOIN engagement_justifications j ON j.id = e.justification_id
              LEFT JOIN opportunity_scores s
                   ON s.opportunity_id = e.opportunity_id
                      AND s.sales_agent_id = e.sales_agent_id
              WHERE sa.sales_manager_id = $1
              ORDER BY e.engaged_at DESC"
             manager-id))))

(defvar *team-cycles-fn* 'db-team-cycles
  "Funcao que lista os ciclos de um time. Vinculavel nos testes.")

(defun team-cycles (manager-id)
  "Todos os ciclos de engajamento do time do gerente MANAGER-ID."
  (funcall *team-cycles-fn* manager-id))
