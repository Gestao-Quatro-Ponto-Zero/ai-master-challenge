# API do Lead Scorer

Servidor: `python3 server.py` (só biblioteca padrão; porta pela variável `PORT`, padrão 8000; interface pela
variável `HOST`, padrão `127.0.0.1`; o Dockerfile usa `0.0.0.0`). Conexão parada fecha depois de 30 segundos.
Todas as rotas são `GET` (ou `HEAD`). Qualquer outro método, inclusive um inventado, devolve `405` e fecha a
conexão.

## Convenções

- **date**: segunda-feira de `2017-07-03` a `2017-12-25`, no formato `AAAA-MM-DD` (só esse: `20171204` ou
  `2017-W49-1` dão 400 em qualquer versão do Python). Sem ela, vale `2017-12-04`. As 26 datas são fixas.
- **Nomes** (vendedor, gestor, cliente) aceitam maiúsculas, minúsculas e espaços a mais. Regional aceita
  `Central`, `East`/`Leste` ou `West`/`Oeste`. Vendedor que só está no cadastro (sem nenhum deal) dá 400 em
  todas as rotas que pedem vendedor (`seller`, `pipeline`, `team`, `time-machine`, `viewer`).
- Parâmetro repetido (`?name=A&name=B`): vale o último.
- **Só o que se sabia na data**: as telas de trabalho não usam estágio, data nem valor de fechamento de
  deal que fechou na data ou depois. As exceções são a máquina do tempo, a qualidade dos dados e a tabela
  de sinais testados, e o próprio texto delas avisa. O campo `account` dos deals abertos vem como está na base
  (o estado final): ele nunca entra em chance, score, ordem ou prova, e a qualidade dos dados explica por que
  ele adianta o desfecho numa data passada. A coluna Prospecção também é a do fim da base (esses deals não têm
  data).
- Números vêm crus: dinheiro em US$ inteiros ou com 2 casas, percentuais como fração de 0 a 1. Ao lado
  vêm rótulos e frases prontos em português.
- Datas vêm no dicionário padrão `date`: `iso`, `label` ("4 dez 2017"), `label_short`, `label_long`,
  `day_month`, `month_name`, `week_of_quarter`, `month_in_quarter`, `quarter_phase` (`abre`, `meio`, `fecha`).
- Deal aberto (dicionário padrão): `id`, `product`, `price`, `account` (como está na base; nunca entra no
  score), `seller`, `region_label`, `engage_date`, `engage_label`, `age_days`, `age_band`, `stale`,
  `band` (`quente`, `morno`, `frio`, `sem_desfecho`), `score` (0 a 100 ou `null`), `chance`, `expected_value`.
- Deal fechado: `id`, `product`, `price`, `account`, `seller`, `region_label`, `close_date`, `close_label`,
  `won`, `close_value`, `cycle_days`.

## Erros

| Situação | Código | Corpo |
|---|---|---|
| Parâmetro inválido ou nome desconhecido | 400 | `{"error": "mensagem em português"}` |
| Linha de requisição inválida, versão de HTTP desconhecida | 400 / 505 | `{"error": "..."}` |
| Endereço com mais de 64 KB | 414 | `{"error": "Endereço longo demais."}` |
| Rota de API desconhecida | 404 | `{"error": "..."}` |
| Arquivo com extensão que não existe em `web/` | 404 | `{"error": "Arquivo não encontrado."}` |
| Método diferente de GET/HEAD | 405 | `{"error": "..."}`, cabeçalhos `Allow` e `Connection: close` |
| Erro inesperado (inclusive erro interno de valor) | 500 | mensagem genérica; o detalhe vai só para o log |

Toda mensagem de erro repete no máximo 60 caracteres do que foi enviado. Ela é texto puro: escape antes de
pôr no HTML. O cabeçalho `Server` é só `LeadScorer/1.0`.

Respostas JSON: UTF-8, `Cache-Control: no-store`, gzip quando o cliente aceita.

## Rotas

### `GET /health`
`{"status": "ok"}`. Não depende da carga da base.

### `GET /api/meta`
Dados fixos: `dataset` (contagens, período, licença), `default_date`, `dates` (as 26 segundas, cada uma
com `in_proof`), `regions`, `managers` (com `team`), `sellers` (só os que têm deals), `products`.

### `GET /api/login?date`
Tela de acesso: `suggestions` (3 vendedores sugeridos com `tag`: `Maior carteira` só para quem tem o maior
valor declarado na data; senão `Carteira em dia` ou `Carteira com deals sem desfecho`), `sellers`, `managers`
(com `descriptor` pronto) e `panel` (`declared_value`, `live_value`, `open_count`, `stale_count`, `headline_1`,
`headline_2`, `sentence`, `stats`; o primeiro card, 8.800 oportunidades, descreve a base inteira e diz isso).

### `GET /api/seller?name&date`
Foco da semana do vendedor. `name` obrigatório.
- `seller`: dicionário de pessoa (`name`, `first_name`, `initials`, `manager`, `region`, `region_label`).
- `date`: dicionário de data com `context_sentence`.
- `summary`: `open_count`, `live_count`, `stale_count`, `declared_value`, `live_value`, `stale_value`,
  `expected_30d`, `live_share`, `sentence`.
- `window`: faixa de idade que mais fecha na data (`from_days`, `to_days`, `max_days`, `chance`) ou `null`.
- `bands`: contagem por faixa de score, com e sem cliente.
- `deals`: abertos em ordem de prioridade (vivos, depois sem desfecho), cada um com `position`, `base`
  (`n`, `y`, `level`), `share_above`, `why` (`reason`, `source`, `excluded`, `action`) e `summary_text`.
- `insights`: 3 cartões (`kind`, `label`, `title`, `body`, `link_label`, `link_target`, `highlight`).
- `rates`: `won`, `lost`, `official`, `with_stale`.

### `GET /api/pipeline?name&date`
Kanban do vendedor. `counts` e `columns`: `prospecting`, `engaging`, `stale`, `won` e `lost` (os dois
últimos com os fechados nos 30 dias antes da data). Cada coluna traz `title`, `hint`, `count`, `deals`
e, exceto `lost`, `value`.

### `GET /api/team?date&manager&region&seller`
Visão do gestor. Filtros opcionais e combináveis (combinação impossível dá 400).
- `scope` (`title`, filtros resolvidos) e `options` (regionais, gestores, vendedores para os seletores).
- `summary`: contagens, valores, `expected_30d`, `live_share`, `stale_share`, `hot_count`, `headline`.
- `rows`: um por vendedor, por valor declarado: contagens, valores, `rate_official`, `rate_with_stale`,
  `rate_delta_points`.
- `agenda`: 3 cartões (decisão, indicador, momento). `messages`: texto pronto para cada vendedor.

### `GET /api/accounts?date&region`
Clientes por regional de casa (sem `region`, todos): `title`, `subtitle`, `count`, `note` e `accounts`
(`closed_count`, `won_count`, `lost_count`, `win_rate`, `won_value`, `last_sale_label`). Ordem: valor ganho.
`home_region_note` explica que a regional de casa (a que mais fechou com o cliente até a véspera) pode mudar
de uma data para outra.

### `GET /api/account?date&name&viewer`
Ficha do cliente. `name` obrigatório; `viewer` marca `is_viewer` nos deals dele (vendedor) ou do time dele
(gestor).
- `account`: porte (`revenue`, `revenue_label`, `employees`, `year_established`, `office_label`, `parent`).
- `history`: fechados até a véspera da data, `avg_ticket`, `last_sale_label`, `headline_detail`.
- `top_products`; `open` (`live`, `stale`, `warning` sobre o cliente dos abertos); `closed` (`by_month`,
  `month_sentence`, `deals` em data de fechamento decrescente e id crescente no empate, como no pipeline).

### `GET /api/time-machine?date&name`
Revela o desfecho de propósito. `name` deve ser vendedor. `lists.score` e `lists.value_only` (10 deals com
`outcome`: `venda`, `perda` ou `aberto`, e `total_label`), `fair` (regra simples com os três desempates e
`sentence`), `window` (dias de desfecho visíveis, cortado no fim da base), `hidden_account_note`.

### `GET /api/proof`
Prova agregada em 22 segundas (3 jul a 27 nov 2017): `n_lists`, `rules` (receita e vendas por regra),
`gains`, `per_date`, `dates_won`, `by_period`, `auc` (`chance`: tabela da data, idade e trimestre;
`age_only`: só a faixa de idade; `price`; `expected_value`: a ordem do app, chance × preço; mais `pairs` e
`positives`), `sensitivity` (top 5 e top 20), `peak` e
`sentences` (`headline`, `method`, `limits`). Calculada uma vez por processo.

### `GET /api/score-model?date&viewer`
Como o score funciona: `example` (um deal com `steps` do cálculo; do `viewer` quando houver), `table`
(chance por faixa de idade, com `n`, `y`, `level`, `in_window`), `training` (segundas usadas), `bands`,
`max_cycle`, `signals` (sinais testados, base inteira) e `proof` (resumo da prova).

### `GET /api/data-quality?date`
Qualidade dos dados (base inteira, salvo os itens marcados "na data"): `coverage`, `items` (5
particularidades com `number`, `title`, `body`, `action`, `scope`), `fields`, `regions`, `fixes`.

### `GET /api/sources`
Fontes de dados: `alert`, `active` (os 4 CSVs), `crms` (lista de referência), `requirements`.

## Arquivos estáticos

`/` entrega `web/index.html`; outros caminhos servem arquivos de `web/` (`Cache-Control: no-cache`).
Caminho sem extensão que não existe, fora da API, também devolve `index.html` (rotas do front). Caminho
com extensão que não existe dá 404. Caminhos que saem de `web/` ou apontam para arquivos ocultos não são
servidos.

## Endereços do app

O front usa rotas depois do `#`: `/#/entrar`, `/#/foco`, `/#/pipeline`, `/#/clientes`, `/#/time` (só gestor),
`/#/maquina-do-tempo`, `/#/como-funciona`, `/#/como-chegamos`, `/#/qualidade-dos-dados` e `/#/fontes-de-dados`.

Três parâmetros abrem o app já como uma pessoa, sem passar pela tela de acesso, e somem do endereço depois
de lidos: `como` (nome do vendedor ou gestor), `perfil` (`vendedor` ou `gestor`, opcional) e `data`
(`AAAA-MM-DD`, uma das segundas aceitas). Exemplos: `/#/foco?como=Daniell%20Hammack&data=2017-12-04` e
`/#/time?como=Rocco%20Neubert`. Nome ou data que o servidor não conhece são ignorados.
`/#/maquina-do-tempo?desfecho=revelado` abre a Máquina do tempo com o desfecho à mostra.
