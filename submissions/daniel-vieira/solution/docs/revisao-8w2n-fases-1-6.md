# Revisão de qualidade e aderência das fases 1 a 6 da tarefa 8W2N

## Escopo e método

Esta revisão examina os artefatos das fases 1 a 6 da tarefa 8W2N (interface web), a saber, a
fundação das aplicações (fases 1 a 4), a aplicação do agente (fase 5) e a aplicação do gerente
(fase 6). O escopo corresponde ao diff acumulado `915054c..HEAD` restrito a `src/web/`,
`tests/web/` e aos protótipos `.claude/assets/examples/example-*.html`, com cerca de 6.500
linhas em 35 arquivos. A fase 7 (responsividade e verificação) está fora do escopo pedido; suas
alterações nos mesmos arquivos são incidentais e mínimas.

O método combinou nove eixos independentes de análise (correção linha a linha, comportamento
ausente, rastreamento entre arquivos, reuso, simplificação, eficiência, altitude de design,
conformidade com as convenções internas, aderência à especificação e segurança), seguidos de
verificação direta no código-fonte dos achados de maior gravidade. A especificação de referência
é a definição de pronto da tarefa 8W2N e as estórias de usuário de `docs/concepcao-inicial.md`.

## Veredito geral

A implementação é sólida e amplamente aderente. As superfícies primárias de segurança estão
corretas, a saber, SQL integralmente parametrizado, CSP estrita com `allowEval` em falso, escape
do Spinneret sem `:raw`, HTMX servido como ativo local, segregação por papel imposta no servidor
e mutações escopadas por `sales_agent_id` (IDOR fechado na camada de dados). O ciclo de
engajamento completo opera. Contudo, dois defeitos de correção produzem falha visível e quatro
lacunas de especificação (filtros e colunas exigidos pelas estórias) impedem declarar a definição
de pronto integralmente satisfeita para as fases 5 e 6.

## Achados por grupo

Os achados estão ordenados por gravidade dentro de cada grupo. A coluna de disposição registra a
decisão de encaminhamento tomada na sessão de revisão.

### A. Correção (bloqueadores)

- A1 (corrigir) --- `src/web/queries.lisp`, `engaged-row->plist`: as colunas de pontuação da
  lista de engajadas do agente são armazenadas cruas, sem `denull`, ao contrário das funções
  irmãs do time (`team-engaged-row->plist`, `team-cycle-row->plist`). A junção externa de
  `opportunity_scores` degrada para o marcador `:null` do Postmodern na janela entre o
  engajamento e o próximo tique do agendador; `render-score` chama `fill-class`, cujo `(round
  :null 5)` sinaliza `type-error` e produz HTTP 500 em `GET /engajadas` e na ordenação por
  potencial. O próprio contrato da consulta afirma degradar para NIL, o que o código não cumpre.

- A2 (corrigir) --- `src/web/view.lisp`, `team-filter-match-p` no ramo `:since`: o filtro
  "Engajada desde" do acompanhamento do gerente compara o instante de engajamento, carimbado em
  tempo virtual (ancorado em `*virtual-epoch*`), contra um limiar produzido por `date-start-ms`,
  que é um instante de calendário real em UNIX-ms. A coluna é exibida convertida para o tempo
  real; a comparação, porém, opera sobre o tempo virtual. O filtro retorna vazio para qualquer
  data plausível. O teste então vigente mascarava o defeito com instantes de brinquedo.

### B. Aderência à especificação

- B1 (descopado) --- Indicador de cross-selling ausente em ambas as listas (filtro e contexto).
  A revisão da especificação concluiu que o indicador não é campo do dataset e que a sua
  derivação (a conta possui negócio ganho para um produto distinto do da oportunidade) seria um
  incremento de modelagem não justificado no MVP; o requisito foi removido da concepção
  ('docs/concepcao-inicial.md', Limitações intencionais de escopo), resolvendo a lacuna por
  exclusão em vez de implementação.

- B2 (corrigir) --- Lista de disponíveis sem filtro por data de disponibilização, exigido pela
  estória. A data de disponibilização passa a ser selecionada e filtrável.

- B3 (corrigir, exceto cross-selling) --- Lista de engajadas sem filtro por data de engajamento
  (e sem série do produto), exigidos pela mesma estória. O filtro por cross-selling é diferido
  junto de B1.

- B4 (corrigir) --- Lista de disponíveis omite as colunas de contexto de porte, receita e data
  de fundação do cliente, exigidas pela estória. Os campos já residem na plist e eram usados
  apenas como chaves de ordenação.

### C. Segurança (endurecimento)

- C1 (corrigir) --- `src/web/handlers.lisp`, `login-submit-for`: a identidade autenticada é
  gravada sem rotação do identificador de sessão, deixando uma janela de fixação de sessão. A
  rotação passa a ocorrer na transição de privilégio.

- C2 (ressalvar) --- `src/web/server.lisp`: o atributo `Secure` do cookie de sessão fica no
  padrão (falso) e não há defesa em profundidade contra CSRF além de `SameSite=Lax`. Adequado ao
  MVP local; registrado como cautela de implantação, sem alteração de código nesta sessão.

### D. Qualidade e manutenção

- D1 (corrigir) --- Derivação de indicadores duplicada entre `db-agent-kpis` e `db-team-kpis`;
  extraída para um auxiliar puro comum.

- D2 (corrigir) --- Portão de autorização copiado em múltiplos handlers; unificado em um
  combinador fail-closed por papel.

- D3 (corrigir) --- Reescore de desfecho invocado na camada web; a invariante "desfecho implica
  reescore" é levada ao serviço de ciclo.

- D4 (corrigir) --- Pesos das dimensões exibidos como prosa fixa; derivados da configuração
  canônica.

- D5 (corrigir) --- Máquinas de filtro e ordenação do agente e do gerente duplicadas, idioma de
  âncora do relógio repetido e literal de deslocamento de época triplicado; fatorados.

### E. Convenções

- E1 (corrigir) --- Linhas de código-fonte acima de 96 colunas em `render.lisp`, `view.lisp` e
  `app.css`, contra o limite obrigatório de `.claude/rules/std-common-lisp.md` e do `CLAUDE.md`.
  As strings longas de `format` são quebradas.

## Superfícies verificadas conformes

SQL parametrizado, CSP e configuração do HTMX, escape do Spinneret, segregação por papel no
servidor, IDOR fechado nas mutações, leitura da configuração com `*read-eval*` em falso e ausência
de segredos no código. Estes pontos foram inspecionados e não apresentaram achados.
