---
subject: Registro histórico do trabalho
author: dcvr@
---


# Escopo deste registro histórico

- O trabalho realizado nas sessões de trabalho é resumido neste documento, a fim de proporcionar
  uma compreensão abrangente do que foi feito recentemente;
- Para os casos em que se requeira uma inspeção mais aprofundada de uma sessão específica, um
  registro individual é mantido para cada sessão neste mesmo diretório, em um arquivo nomeado
  com o formato {parent-task-id}-{YYYY-MM-DD}-{n}.md.


# Como registrar um novo item

- Registrar o resumo de cada sessão como um item separado (um novo marcador) na seção "Resumo do
  trabalho (uma sessão por marcador)";
- Colocar a entrada mais recente no topo da lista;
- Utilizar o seguinte formato para cada entrada: '- {YYYY-MM-DD} --- {parent-task-id}-{n} ---
  {Resumo do que foi feito na sessão, incluindo eventuais tarefas incorporadas} ---
  {Justificativa / breve motivação de por que foi feito}';
- Utilizar apenas caracteres imprimíveis, admitidos os caracteres acentuados do português;
- Quebrar as linhas em 96 colunas e, quando uma entrada exceder 96 colunas, continuá-la na linha
  seguinte com recuo de dois espaços, de modo que a continuação seja tratada como parte do mesmo
  marcador;
- Quando este documento se aproximar do limite de linhas estabelecido pelas convenções gerais de
  formatação de texto, mover as entradas mais antigas para um arquivo nomeado
  _historical-archive-{YYYY}.md neste mesmo diretório.


# Resumo do trabalho (uma sessão por marcador)

- 2026-07-21 --- 6X9H-2 --- Validada a Fase 1 da 6X9H (execucao em um passo) na perspectiva do
  avaliador (clone limpo, build a frio, um comando) e corrigida a recompilacao das dependencias
  Lisp no arranque do conteiner. Causa raiz: o ASDF 3.3.1 da imagem base diverge do uiop-3.3.7
  fixado pelo lock e se auto-atualiza a cada sessao nova de SBCL, forcando uma cascata de
  recompilacao que a reutilizacao do cache de fasls entre build e runtime nao resolvia. Solucao:
  distribuir a aplicacao como imagem de core do SBCL ('save-lisp-and-die'), com o
  'container-entrypoint' arrancando via 'sbcl --core /app/leadscorer.core', de modo que
  'asdf:load-system' vira no-op e nenhuma compilacao ocorre no boot; decisao registrada no ADR
  K6M2. Verificado em build a frio de clone limpo: zero recompilacao no primeiro arranque e na
  re-entrada, apps em 200, seed e ranqueamento intactos. --- A execucao confiavel conforme o
  setup e criterio de avaliacao, e a recompilacao no arranque atrasava a subida e poluia o log a
  ponto de um avaliador interpreta-la como falha.
- 2026-07-21 --- H7C4-1 --- Endurecido o healthcheck do servico 'db' em 'compose.yaml': de
  'pg_isready' (que so verifica a aceitacao de conexoes) para um 'psql -h "$(hostname)" ... -tAc
  "SELECT 1"' autenticado, que forca o caminho TCP casando a regra 'host all all all
  scram-sha-256' do pg_hba e exige a senha (de 'PGPASSWORD', pelo env_file, sem embuti-la no
  comando), com 'start_period: 10s' para tolerar a fase de inicializacao socket-only da imagem.
  Achado central confirmado empiricamente: conectar pelo socket ou '127.0.0.1' de dentro do
  conteiner casa 'trust' e aceita qualquer senha (falso positivo), de modo que so o caminho
  '-h "$(hostname)"' valida a credencial. Verificacao ponta a ponta com Docker em clone limpo e
  projeto isolado: credencial correta leva a 'healthy' e a app conecta e serve ('/login' HTTP
  200); credencial divergente (volume obsoleto) mantem o healthcheck falhando ('FATAL: password
  authentication failed') e o servico vira 'unhealthy'. 'yamllint' limpo; mudanca restrita a
  YAML. Auditoria independente de contexto cortado realizada. --- Fechar a lacuna de diagnostico
  deixada como desenvolvimento futuro da D3P7: o healthcheck reportava 'healthy' sem validar a
  senha, tornando a falha de autenticacao (28P01) tardia e confusa.
- 2026-07-20 --- F2K9-1 --- Versionado o 'app.css' por hash de conteudo no 'href' do link de
  estilo ('/assets/app.css?v=<hash>'), reusando 'content-checksum' (exportado do pacote base),
  com degradacao para o href sem versao quando o arquivo nao pode ser lido. Coberto por teste;
  suite web 382/0 com PostgreSQL real. --- Cache-busting: como cada aplicacao e servida em porta
  distinta, uma alteracao de CSS exigia hard-refresh por aba (debito da N7B2).
- 2026-07-20 --- D3P7-1 --- Tornado o 'scripts/quickstart' robusto a volume e imagem Docker
  obsoletos de um projeto de compose homonimo: quando um '.env' novo e gerado, reinicializa o
  estado ('down --volumes') e forca '--build', garantindo que o banco suba com a senha corrente.
  Verificado por 'shellcheck', 'bats' 4/4 e reproducao ponta a ponta com Docker (28P01 reproduzido
  e corrigido). --- O teste de compilacao Docker da 6X9H travava em '28P01 password authentication
  failed' a partir de um clone limpo, por reuso de um volume persistente com senha divergente.
- 2026-07-20 --- W3Q6-2 --- Sessao de divida tecnica com W3Q6 como tarefa-pai e T3F9 e G3K8
  incorporadas. T3F9: corrigido o slug de 'export-session' (substitui '/' e '.'), resolvendo a
  transcricao bruta em worktree, com teste bats de regressao. G3K8: atributo Secure do cookie de
  sessao dirigido por ambiente (LEADSCORER_COOKIE_SECURE), via 'cookie-secure-p' e o auxiliar
  extraido 'env-flag'. W3Q6 Fase 1: apos revisao empirica (coeficientes de Spearman reproduzidos
  exatamente), mantida a igualdade exata sobre float nos tres sitios com fundamento inline. Fase
  2: 'connect-with-retry' refinado por classe de condicao (deftype TRANSIENT-CONNECT-ERROR) para
  retentar so transitorios (socket e SQLSTATE 57P03) e falhar de imediato nos permanentes,
  validado contra PostgreSQL real. Auditoria independente aprovou; os quatro achados foram
  resolvidos ou endereçados (guarda estrutural do 57P03, comentario de 'ranks', simetria de
  teste). --- Reduzir a divida tecnica pendente do backlog, aproveitando a disponibilidade de
  PostgreSQL real que destravou a Fase 2 da W3Q6.
- 2026-07-20 --- Z8N3-1 --- Revisao de qualidade e aderencia das fases 1 a 6 de 8W2N
  (interface web) e correcao dos achados. Revisao independente em nove eixos, com relatorio
  em 'docs/revisao-8w2n-fases-1-6.md'. Corrigidos A1 (crash HTTP 500 por ':null' nao
  normalizado na lista de engajadas) e A2 (filtro de data do gerente no eixo virtual x real);
  B2/B3/B4 (filtros por data e por serie, colunas de porte/receita/fundacao); C1 (rotacao do
  id de sessao no login); D1-D5 (KPIs, portao de autorizacao, reescore melhor-esforco, pesos
  do config, fatoracoes); E1 (96 colunas). B1 (cross-selling) descopado na concepcao apos
  revisao da especificacao; C2 (Secure/CSRF) ressalvado. Auditoria independente de contexto
  cortado: veredito aprovar, tres itens nao bloqueantes remediados. Verde: web 306/0 (falha
  unica exige PostgreSQL), 'mallet' sem achados, build sem avisos. Integrado por rebase sobre
  a dockerizacao (24c6c77), historico linear, publicado em origin/main. --- Restaura a
  definicao de pronto das fases 5 e 6, corrigindo defeitos de HTTP 500 e lacunas contra as
  estorias de usuario.
- 2026-07-20 --- 6X9H-1 --- Fase 1 de 6X9H (conteinerizacao e execucao em um passo), com a tarefa
  incorporada V9K3 (ADR). Dockerfile multi-stage (clfoundation/sbcl, qlot fixado), servico 'app'
  no compose, entrypoint e provisionamento idempotente ('database-seeded-p' + migra sempre, semeia
  o banco vazio), e versionamento da fonte normalizada e das quatro features derivadas (ADR V9K3)
  como insumos do seed e do agendador. Verificado o comando literal 'docker compose up': as duas
  apps sobem em 127.0.0.1, o agendador materializa as pontuacoes e o reinicio e idempotente.
  Auditoria independente realizada; oito achados remediados ou enderecados (imagens qualificadas,
  portas em loopback, retry a frio, PGPORT fixo, SIGTERM gracioso, caminho do modelo, cadence.csv
  retirado). --- O desafio avalia a execucao confiavel conforme o setup documentado, e a Fase 1
  torna o projeto executavel por um avaliador leigo em um unico comando.
- 2026-07-20 --- N7B2-1 --- Fase 6 de 8W2N: aplicacao web do gerente, somente leitura e segregada,
  espelhando a Fase 5. Tela inicial (faixa dos seis KPIs agregados do time e destaque das
  engajadas em curso) e visao de acompanhamento (todos os ciclos do time, com filtros por agente,
  produto, conta, desfecho e data, e ordenacao). Consultas escopadas por 'sales_manager_id';
  achado do NULL como ':null' do Postmodern normalizado por 'denull'. Por decisao do usuario, a
  devolucao sem desfecho ganhou o rotulo 'Devolvida' (quinto estado). Refinamento pos-feedback: o
  estado de exibicao 'Expirando' passou a derivar da regra logica de expiracao ('engagement-
  expired-p', a mesma da escrita), com o agendador como escritor unico, controles do agente
  desabilitados e exclusao da contagem em curso (ADR E2H7); revertido um piso cosmetico anterior.
  Auditoria independente com contexto cortado: veredito aprovar, quatro achados de baixa gravidade
  remediados ou endereçados (filtro Em curso vs Expirando unificado em 'cycle-display-state';
  validacao de data por round-trip; cobertura de ':since'). Removida a funcao morta
  'render-home-page' e seus dois testes. Verde: core 195/0/0, web 328/0/0, 'mallet' sem achados;
  conducao ponta a ponta por curl para o gerente 'melvin.marxen'. A sessao incorporou tambem a
  Fase 7 de 8W2N (validacao final da interface): verificacao automatica completa verde (build sem
  avisos, Parachute, 'mallet' nos 44 arquivos, 'yamllint', 'shellcheck', HTML servido por 'tidy'
  sem erros nas sete paginas) e passe visual aprovado pelo usuario nas duas apps a 390 px, com um
  ajuste responsivo do navbar (wordmark e status recolhidos no menu-hamburguer nas telas
  pequenas). Com a Fase 7 concluida, a tarefa-pai 8W2N foi marcada como done. --- Entregar a
  segunda das duas aplicacoes de negocio da interface web (terceiro objetivo especifico), fechando
  o ciclo de valor em que o gerente acompanha o trabalho dos agentes, e concluir a interface web
  como um todo, no caminho critico da submissao 6X9H.
- 2026-07-20 --- X7F2-1 --- Parte 2 da renomeacao da dimensao do agente, reescopada por decisao do
  usuario de renomeacao ampla para mudanca cosmetica (exibicao e documentacao): os nomes internos
  ('adherence', coluna 'score_adherence', artefato 'adherence.csv') sao mantidos em definitivo como
  nome interno herdado. Levantamento revelou que a UI ainda exibia 'Persuasao' (nome anterior a
  S5J4), nao 'adherence'; a mudanca real foi 'Persuasao' -> 'Especializacao'/'Especializacao do
  agente' em quatro superficies (aplicacao 'src/web/view.lisp', os tres exemplos HTML estaticos e o
  anexo 'textos-de-ajuda.md'), adotando o corpo de nota encurtado pelo usuario e corrigindo o typo
  'do do'. Corrigido o achado 3 ('src/scoring.lisp': docstrings dos pesos e cabecalho passam de
  'base aditiva' para expoentes da media geometrica corrente; forma legada marcada). Alinhado o
  teste 'render.lisp' e emendado o ADR G5W2 (nome interno permanente, separacao exibicao-vs-interno
  deliberada). Verificacao verde: mallet sem achados, Parachute core 154/0 e web 169/0 exercitaveis
  (a unica falha, 'home-requires-matching-role', e dependencia pre-existente de PGDATABASE,
  confirmada identica em HEAD). Auditoria independente realizada no encerramento. --- Fechar a
  divergencia entre a documentacao (ja em 'Especializacao') e as superficies visiveis ao usuario
  (ainda em 'Persuasao'), no terceiro objetivo especifico e no caminho critico da entrega (6X9H).
- 2026-07-20 --- S5J4-1 --- Reconciliacao documental da dimensao do agente (Parte 1 da S5J4):
  revisao critica da mecanica das dimensoes do scoring, cuja evidencia da EDA (win rate e ruido;
  a alavanca robusta e a contagem de Won) reenquadrou o achado 1 de defeito de codigo para
  defeito de nomenclatura. Renomeacao, em varredura completa, de 'persuasao'/'aderencia'/'share
  de Won' para 'Especializacao'/'Especializacao do agente' em README, base de conhecimento, ADR
  B7Q3 e C4X9, indice e tarefas 3RJ8 e 5T6Q; nota do achado 2 e diferimento da Opcao B na
  metodologia; novo ADR G5W2. Parte 2 (codigo e telas, achado 3) diferida na X7F2 (blocked-by
  P3W7), mantendo a coluna fisica 'score_adherence' sem migracao. Retrospectiva adicionada em
  'docs/retrospectiva.md'. Sessao documental, isenta de auditoria. --- Eliminar a contradicao
  entre documentacao, concepcao e codigo na dimensao do agente, alinhando o nome unico a
  mecanica e a EDA, e preparar insumos para os entregaveis do desafio.
- 2026-07-20 --- P3W7-1 --- Aplicacao do agente (Fase 5 de 8W2N). Construida sobre a fundacao
  'leadscorer/web' em sete passos: servicos de dominio de engajamento ('src/engagement.lisp':
  'engage-opportunity' com limite fail-closed por lock consultivo, 'close-engagement',
  'return-engagement'), consultas e enriquecimento pelo modelo ('src/web/queries.lisp',
  'model-context.lisp'), apresentacao pura ('src/web/view.lisp'), renderizacao e fragmentos
  ('src/web/render.lisp'), handlers e rotas com deteccao HTMX ('handlers.lisp', 'server.lisp'),
  CSS ('app.css') e verificacao ponta a ponta. Interatividade hibrida (filtros/ordenacao por GET;
  acoes e modal por fragmento HTMX com troca out-of-band) sob CSP estrita (barras por classes
  'fill-*', sem estilo inline). Quatro ajustes de feedback do usuario (notas identicas ao
  prototipo; 'dias' por extenso; decaimento imediato por won/lost via reescore alvejado com a
  devolucao revertendo a linha de base; cabecalho de tabela fixo). Auditoria independente com sete
  achados, todos remediados ou endereçados (limite por lock consultivo, preservacao de filtro nas
  trocas HTMX, guarda de acao, e a semantica de decaimento formalizada no ADR S9K5). Verificacao:
  core 190/0/0, web 211/0/0, mallet sem achados, conducao HTTP ponta a ponta e invariantes em 0.
  --- Terceiro objetivo especifico do projeto e ponto de contato do usuario final, no caminho
  critico da entrega (desbloqueia 6X9H).
- 2026-07-20 --- R7M4-1 --- Servicos automaticos do ciclo de engajamento (Fase 4 de 8W2N):
  ranqueamento, decaimento e expiracao operando sobre a persistencia (9P4D) a partir do motor de
  scoring, no ciclo acelerado. Novos 'src/cycle.lisp' (relogio virtual unico ancorado na epoca do
  seed, 20 min reais = 138 dias virtuais; fallback neutro para pares fora do modelo estatico;
  drivers 'expire/rank/decay' e 'run-cycle-tick' com reconciliacao das linhas de
  'opportunity_scores'), 'src/config.lisp' e 'config/model.lisp' (parametros e regras em forma
  Lisp, lidos com '*read-eval*' NIL e schema fail-closed, substituindo o YAML; ADR H4C7) e
  'src/web/scheduler.lisp' (agendador 'sb-thread' engatado em start/stop, com degradacao
  fail-safe). A concepcao e os registros de tarefa foram retificados do YAML para a forma Lisp.
  Verificacao verde: carga sem avisos, mallet, Parachute core 159/0 e web 91/0, e tick servido
  sobre os dados reais (234 expiradas, 15.750 ranqueadas, 80 decaidas, invariantes em 0).
  Auditoria independente realizada; seis achados (um alto, tres medios, dois baixos) todos
  remediados ou endereçados, incluindo a gravacao do valor de fechamento zero na expiracao
  (invariante de 'verify.lisp') e o momentum neutro do fallback ocioso. --- Fase 4 e a precondicao
  remanescente das aplicacoes de negocio (Fases 5-6), que consomem os 'opportunity_scores' e o
  estado do ciclo.
- 2026-07-20 --- K9X4-1 --- Fundacao executavel das duas aplicacoes web segregadas, do agente e
  do gerente, e identificacao por selecao com sessao e segregacao por papel (Fases 2-3 de 8W2N).
  Novo sistema 'leadscorer/web' (Clack sobre Hunchentoot, Ningle, Spinneret, Lack, Postmodern),
  com login sem senha dos usuarios semeados, portao de autenticacao fail-closed, CSP estrita com
  HTMX 2.0.x servido como ativo estatico ('allowEval' falso), cookie de sessao 'HttpOnly' com
  nome distinto por app, layout base do design system (tema Gray 100, IBM Plex local) e
  responsividade. Auditoria independente realizada; cinco achados (dois medios, tres baixos)
  todos remediados, incluindo um teste de integracao em processo da pilha real, os nomes de
  cookie distintos por app e o 'connect-src' na CSP. Verificacao verde: carga sem avisos, mallet,
  Parachute web 88/0 e core 102/0, vnu, markdownlint, e verificacao de navegador limpa pelo
  usuario nas duas aplicacoes. --- Terceiro objetivo especifico do projeto e precondicao comum de
  todas as telas de negocio, isolada num incremento coerente e verificavel.
- 2026-07-19 --- V7C2-1 --- Prototipagem estatica das telas da UI (Fase 1 de 8W2N) e, incorporada,
  a mudanca do modelo de scoring (tarefa W8H5, ADR R4T9). Produzidos oito prototipos autonomos
  HTML/CSS (logins, home e listas do agente, modal de justificativa, home e acompanhamento do
  gerente) em tema escuro Gray 100 com IBM Plex local, notas de ajuda por rotulo, filtro de corte,
  destaque do top tier e menu responsivo. As dimensoes foram renomeadas em toda a documentacao e
  UI (Retorno, Afinidade, Persuasao, Diligencia, Atividade; Momentum e 'Potencial da oportunidade'
  mantidos) e o Retorno foi reancorado do preco de tabela para o ticket medio do par com recuo por
  setor, implementado no codigo ('modeling.sql', 'model.lisp', 'scoring.lisp'). Reaplicado sobre
  o 'main' divergente (persistencia 9P4D e robustez Q7B3/T8D5/W3Q6) por rebase, com quatro conflitos
  resolvidos, e submetido a verificacao canonica de encerramento com o PostgreSQL provisionado:
  compilacao sem avisos, Parachute 102/0 (suite completa), derivados DuckDB sem anomalias, 'mallet',
  'markdownlint' e 'vnu' limpos. ADR R4T9 registrado. Duas auditorias independentes realizadas e
  todos os achados remediados ou endereçados --- Materializar
  a experiencia de uso e refinar o conceito do ranqueamento, em nomes e no insumo economico, antes
  das fases de aplicacao, mantendo os pesos validados do modelo.
- 2026-07-19 --- W3Q6-1 --- Divida tecnica pos-review, fase 3 (limpeza
  nao-corretiva), em worktree isolado. Extraido o nucleo comum 'score-triple' de
  'score-pair'/'score-opportunity', removida a tabela 'seen' redundante de
  'seed-regional-offices' e substituido o 'pushnew' linear de 'load-model' por um
  conjunto hash. Comportamento preservado, confirmado pela reproducao exata dos
  coeficientes de 'run-validation'. Itens obsoleto (sonda) e de avaliacao (escritor
  CSV, mantido) sem alteracao. Fases 1 e 2 pendentes. Motivacao: saldar a divida de
  qualidade de baixo risco.
- 2026-07-19 --- T8D5-2 --- Regeneracao e revalidacao da derivacao DuckDB, precedida
  do registro no backlog das tarefas T8D5 e W3Q6 (sessao T8D5-1). A execucao
  confirmou o determinismo do 'ARG_MAX' (correcao #1 da Q7B3) e CAPTUROU uma
  regressao introduzida pela propria Q7B3: a remediacao do achado #8 (falso positivo)
  havia adicionado 'account IS NOT NULL' a uma assertion que verifica um valor
  canonico da EDA (298), quebrando o guard fail-closed em 'main' (media 89). Revertida
  ao predicado canonico; todas as assertions passam e o scoring foi revalidado
  identico a 'docs/validacao-scoring.md'. Auditoria independente do revert: aprovado.
  Motivacao: fechar a lacuna de verificacao das correcoes de fonte da Q7B3, nao
  executaveis na sessao de origem.
- 2026-07-19 --- Q7B3-1 --- Robustez e reprodutibilidade pos-review das camadas de
  scoring e persistencia, em worktree isolado. Auditoria de code review em alto
  esforco (seis angulos de busca, verificacao adversarial) sobre 'src/', 'tests/' e a
  persistencia; dez correcoes aplicadas por ciclo TDD: guarda de n=0 em 'pearson',
  clamp de 'min-max-normalize' a [0,100], comparador de 'choose-open-cycle' tolerante
  a 'engage_date' em branco, 'sql-value' em colunas inteiras do seed, conexao unica
  com retentativa do estabelecimento em 'call-with-database', restauracao do checksum
  sob 'unwind-protect' e skip explicito no teste de integracao, cobertura adicional, e
  desempate deterministico do 'ARG_MAX' com espelhamento integral do portao em
  'modeling.sql'. Auditoria independente com veredito de aprovacao; achados remediados
  ou endereçados. Motivacao: consolidar a robustez fail-closed das camadas entregues
  em 3RJ8 e 9P4D antes da Fase 4 da 8W2N.
- 2026-07-19 --- 9P4D-1 --- Camada de persistencia em PostgreSQL (Fase B) implementada em
  worktree isolado. Migracoes SQL numeradas ('db/migrations/') das nove tabelas do modelo
  relacional, runner idempotente com 'schema_migrations' e verificacao de checksum, seed em
  Common Lisp (Postmodern) a partir dos CSV normalizados com conversao monetaria exata em
  centavos, datas em UNIX-ms UTC e usernames derivados, e verificador fail-closed. Contagens
  canonicas conferidas (opportunities 530, engagements 7.212, 1.588 linhas excluidas). Postmodern
  adicionado como dependencia; 'compose.yaml' e '.env.example' para provisionamento. Auditoria
  independente realizada e os seis achados remediados ou enderecados; ADR R6T2 registrado. ---
  A fase de aplicacao (8W2N) requer os dados persistidos; a regra de derivacao do ciclo
  (delegada pelo N4P8) foi fixada e o schema tornou-se a fonte canonica do modelo.
- 2026-07-19 --- M5T2-1 --- Concepcao inicial da aplicacao revisada e completada e tarefas de
  aplicacao desdobradas. O documento 'docs/concepcao-inicial.md' foi reescrito: linguagem e
  gramatica corrigidas, estados da oportunidade alinhados (prospecting e engaging persistentes;
  won, lost e expiracao como desfechos no historico com reentrada decaida), modelo de
  qualificacao reconciliado com o codigo (quatro dimensoes ativas e duas inertes exibidas com
  traco, agregacao por portao e media geometrica), estorias de usuario completadas, e o modelo
  relacional substituido por um derivado do esquema real conforme 'std-sql.md' e centrado no
  ciclo de engajamento. Incorporado o painel de indicadores da tela inicial (seis KPIs mais a
  lista de destaque por papel) e adotados prototipos HTML/CSS no lugar de wireframes. As tarefas
  9P4D e 8W2N foram desdobradas com plano, riscos e definicao de pronto, e o ADR N4P8 registrou
  o modelo de dados do ciclo de engajamento. Sessao documental, sem materia auditavel ---
  Consolidar a concepcao como especificacao fiel as fontes canonicas antes de desdobrar a fase
  de aplicacao, evitando propagar premissa errada a persistencia e as apps.
- 2026-07-19 --- K2R7-1 --- Allowlist por literal exato acrescentado a varredura de segredos de
  'scripts/export-session' (arranjo 'ALLOWLIST', 'is_allowlisted', 'scan_secrets' reescrita para
  extrair o texto casado e isentar apenas literais benignos exatos, preservando o gate
  fail-closed). Testes fail-closed reescritos para montar o segredo em runtime e dois testes novos
  de isencao; fixture 'allowlisted-raw.jsonl' criada e as fixtures leaky orfas removidas
  ('bats' 14/14, 'shellcheck' limpo, regressao das transcricoes existentes identica). A transcricao
  de H3V6-1 foi provisionada em '.claude/sessions/' com varredura limpa. ADR P8V4 registrado,
  estendendo J7K4. Auditoria independente realizada --- Fechar a lacuna que a propria propriedade
  fail-closed abria, recusando transcricoes com literais benignos (chaves de exemplo, cadeias
  sinteticas de fixtures), sem enfraquecer a deteccao de segredos reais.
- 2026-07-19 --- H3V6-1 --- Infraestrutura de transcricao de sessao construida: o filtro de
  higienizacao 'scripts/sanitize-transcript.jq' (deny-by-default por tipo de registro) e o
  invocavel 'scripts/export-session', que higieniza a transcricao bruta do Claude Code, valida o
  JSONL e aplica uma varredura de segredos fail-closed por ruleset regex embutido, movendo a
  saida para '.claude/sessions/' so apos a varredura passar. Cobertura por 12 testes bats
  ('tests/export-session.bats'); ADR J7K4 registrado. Provisionadas as transcricoes higienizadas
  das sessoes anteriores (3RJ8 e a mista 7K2M, que cobre 7K2M, 2H5K, 4G7C e 1J8R, com notas
  cruzadas). Auditoria independente realizada; os dois achados de postura de seguranca
  (allow-by-default e falsos-negativos no ruleset) foram corrigidos --- Fechar a lacuna de
  seguranca e de rastreabilidade do protocolo de encerramento, cuja exportacao higienizada com
  varredura fail-closed nao possuia infraestrutura.
- 2026-07-19 --- 3RJ8-1 --- Modelo de scoring de leads concluído. Especificação e realinhamento
  de escopo (a distribuição incorporada ao score como a dimensão de aderência, ADR B7Q3, e a
  5T6Q cancelada), metodologia de indicador composto (ADR C4X9), base de modelagem em DuckDB
  (scripts/modeling.sql) e motor em Common Lisp (src/model.lisp, src/scoring.lisp) com as duas
  listas, e validação por robustez (src/validation.lisp, docs/validacao-scoring.md). A validação
  revelou dominância do momentum por artefato de escala na forma multiplicativa; adotou-se a
  média geométrica ponderada, verificada empiricamente. Duas auditorias independentes realizadas,
  das Fases 3-4 e da Fase 5, e todos os achados remediados. A infraestrutura de transcrição de
  sessão não existe e foi registrada como tarefa de backlog --- Entregar o objetivo específico
  central, o scoring explicável e defensável, ancorado na estrutura real dos dados, com o método
  e o apoio à decisão como propósito, não a acurácia.
- 2026-07-18 --- 1J8R-1 --- Análise exploratória do dataset CRM com DuckDB (37+ consultas em
  scripts/eda.sql) e base de conhecimento em docs/analise-exploratoria.md: a conversão Won/Lost
  é quase invariante (~63%) nos atributos observáveis; win rate, velocidade e ticket do agente
  são ruído ou derivados, e só a especialização por produto é sinal robusto; o momentum é o par
  cliente-produto (cadência de recompra e decaimento pós-engajamento por curva CCDF, com corte
  de expiração em 138 dias); a unidade de atribuição é o par cliente-produto. Auditoria
  independente realizada e achados remediados --- Ancorar scoring e distribuição na estrutura
  real dos dados, com o método e o apoio à decisão como propósito, não a acurácia preditiva.
- 2026-07-18 --- 4G7C-1 --- Fonte CSV normalizada e derivada em data/normalized/, gerada por
  scripts/normalize.sql (correções de produto, setor e país por CASE), fonte única consumida
  pela EDA e pela modelagem, com os brutos imutáveis; ADR F3N8 registrado. Auditoria
  independente realizada e achados remediados --- Eliminar a correção dispersa em consulta e
  prover uma fonte limpa e canônica para a modelagem.
- 2026-07-18 --- 2H5K-1 --- Aquisição e verificação do dataset CRM: kaggle CLI instalado, os
  cinco CSV baixados para 'data/' (ignorado pelo Git) e verificados por
  'scripts/verify-dataset.lisp' contra os valores canônicos (accounts 85, products 7,
  sales_teams 35, sales_pipeline 8.800); método documentado em 'docs/dataset.md', credenciais do
  Kaggle endurecidas para 600 e configuração incorporada do markdownlint; auditoria independente
  realizada e todos os achados remediados ou endereçados --- Disponibilizar o dataset real
  verificado como precondição da modelagem, sem depender do PostgreSQL.
- 2026-07-18 --- 7K2M-1 --- Fundação do projeto pronta para modelagem: repositório Git em
  'main', ADRs D2K9 (stack e persistência faseada), D4M3 (conteinerização) e D6P7 (repositório)
  registrados e indexados, sistema ASDF sob qlot com leitura genérica de CSV (fare-csv) coberta
  por testes Parachute e linter mallet limpo; backlog decomposto em sete tarefas com a aquisição
  do dataset (2H5K) separada e a persistência (9P4D) reposicionada para a fase de aplicação;
  auditoria independente realizada e suas ressalvas de baixa severidade tratadas ou diferidas
  --- Estabelecer base verificável e reproduzível antes da modelagem, com as decisões
  arquiteturais consequentes formalizadas e a fase de modelagem operando direto sobre CSV.
