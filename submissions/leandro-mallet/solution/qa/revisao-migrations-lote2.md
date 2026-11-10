# Revisão e aplicação — banco, lote 2

**Veredito: pode rodar. 0007–0028 aplicadas em 10/11/2026, sem erro.** O L2-1 foi fechado pela 0028. Ficam abertos L2-5 (média: auditoria forjável por inserção direta) e L2-6 (leve), com a correção proposta, para uma próxima migration.

Ordens O-03 (0007–0025, com o acréscimo da 0026), O-10 (0027) e O-12 (0028). O lote 1 já estava aplicado e não foi reaplicado ([revisao-migrations-lote1.md](revisao-migrations-lote1.md)).

## Como foi validado e aplicado

1. Arquivos copiados direto do commit `0a69f6b` (`git show`) para uma pasta temporária; conferidos contra a pasta de trabalho (iguais, fim de linha LF).
2. Revisão estática: nenhum DROP, DELETE, TRUNCATE, CASCADE ou SET NULL; nenhuma função `security definer`; a única política de RLS é para o papel de carga `system_carga`; assinaturas das funções revogadas na 0025 conferidas com as da 0024.
3. Validador da sessão de dados (`db/validar_tudo.mjs`, Postgres em memória, sem conexão): 0001–0026 + dataset inteiro, catálogo **ok**; testes de uso **115 ok, 0 falha**. O validador simula os papéis do app, então os blocos que só rodam quando a `service_role` existe também foram exercitados.
4. Aplicação no Supabase como `postgres`: um arquivo por transação, parada no primeiro erro, registro em `supabase_migrations.schema_migrations` com o sha256.

| Arquivo | sha256 |
|---|---|
| 0007_core_contatos.sql | `d1a61040ccde70bc37a5bed2b34a31f597b5288ba174b5584873e63f4825f932` |
| 0008_config_tags.sql | `70748da0d0b5250ee9e60dd414174cfd027cb8e96f047fabd97c5a3772284dca` |
| 0009_score.sql | `0cf0666683cb938860bac5144a70e1def4dad857bf436ac9599975863529dba5` |
| 0010_acao.sql | `6c873a8c2bc539b64928af81040cf7d8fb12d0bd9c7f8ebb822f04558ecfcdd5` |
| 0011_system.sql | `386e36309388994467d115655c69ebdc196c5d798d37a3861a97113587175bc7` |
| 0012_guardas.sql | `7326bfbd2ec5416a1484beeb13bf41b3e8163e1b2b54fc89f0717a507f3ca2cf` |
| 0013_functions_base.sql | `dafabcb758bd7e55574fdc0d48cfe0bd6aaa169b6df24d3d072a5c5950c9cf8c` |
| 0014_views.sql | `a152f10b58fa2d9bcdb19481faceb88c0b1e235b978428f3c22c5a1b8d3dd9c8` |
| 0015_functions_leitura.sql | `a5e3e03b9bff95501a00e3c9e77823c06b1065fcd078617aa2d79722efe91a08` |
| 0016_functions_deals.sql | `51c65c4b2f7a562cd4d26ed12f19cdce3a8216eed256cbb5bca57544db335737` |
| 0017_functions_importacao.sql | `91a64ba961af991ebc2f0a307a6197a45180f045e7b6550e362d19327486b91b` |
| 0018_functions_acao.sql | `7792075ec77b138e54bc7d829178fdede94273ad971979df76aa796152e245ec` |
| 0019_functions_lote.sql | `15ea7bd01c9a35250db4b311f46e90cb5307bd34cab50cc1730861213e8ea457` |
| 0020_functions_cargas.sql | `495bcfe7dd1ae1e9105cd2ffa85c2a29e05f27f03eaa00529d438d00b4fd679f` |
| 0021_permissoes.sql | `4b3c8858442f71c20d3629eb81e8714e3ac0a967725517a647c3b2b7cd2eeb67` |
| 0022_seguranca.sql | `95e466caeddb071787b0d6975af73519af0825e9a0fc9d54f756e7bf069d8e64` |
| 0023_atividades.sql | `d11f5fc4f26e54aef2433f5cf351f3188a1b88a66bb79f5202d9146acb1fcfce` |
| 0024_roteamento_repasse.sql | `0758527e893e3d6522abdd077a60bc24a29f1221bb70dab51f6d6de0b87e0d7c` |
| 0025_permissoes_e_guardas.sql | `e84f6fa828e2853df8d6b53e1493320a2f3462f3266e44438ebdd8bc34a7cbf1` |
| 0026_limite_global.sql | `ea36c7b605248f5e6f882cc6ec79405fc91f73e4ac3ea49bd2c3abb2619c443a` (commit `d6c4f12`; igual ao do repositório desde `dd5358f`) |
| 0027_limite_exato.sql | `d3a2f05c426a0d548201ca574a5c6416f1597bce7b5e7336122fd954e0a13a62` (commit `dd5358f`) |
| 0028_contexto_obrigatorio.sql | `df81c94ef246ad5866f3cc9e84e5c39a2c838b55bf3cb687ae3f99f5b02abdb7` (commit `375cd5f`) |

### O caso da 0026

A 0026 foi aplicada na versão do commit `d6c4f12` (hash acima), seguindo o acréscimo à O-03. O aviso para segurar a 0026 (ajuste de `>` para `>=`) chegou depois da aplicação. Nada foi desfeito. Combinado com a orquestração: o arquivo da 0026 no repositório volta exatamente à versão aplicada, e qualquer ajuste entra como 0027.

A 0026 aplicada já recusava exatamente o 31º pedido por usuário e o 301º no total, porque a contagem incluía o pedido atual. A 0027 deixa a regra explícita: conta só os pedidos anteriores e usa `>=`. O resultado medido é o mesmo, sem mudar o teto (abaixo). Antes de aplicar, a 0027 passou no validador da sessão de dados (116 ok, 0 falha).

## Conferência no Supabase

| Medida | Esperado | No banco |
|---|---|---|
| Tabelas (todas com prefixo) | 29 | 29 |
| Chaves estrangeiras | 60, RESTRICT, com índice | 60; nenhuma sem RESTRICT, nenhuma sem índice, todas validadas |
| As 3 FKs pendentes do lote 1 | criadas e validadas | `core_deals_contato_id_fkey`, `core_deals_importacao_id_fkey`, `system_auditoria_lote_id_fkey`: validadas |
| Funções nossas (com prefixo) | 68 | 68 (o banco mostra 69: a sobra é `rls_auto_enable`, do próprio Supabase) |
| Views | 3, com security_invoker | 3, todas com security_invoker |
| Gatilhos | 86 | 86 |
| Índices | 104 (com a 0026) | 104, todos com prefixo |
| RLS | todas as tabelas | 29 de 29; 29 políticas, todas só do `system_carga`; nenhuma para anon, authenticated ou service_role |
| Papel de carga | existe | `system_carga` (sem login, sem herança, sem bypass de RLS) |
| Parâmetro `limite_global_escritas` | 300 | 300 |
| `system_iniciar_contexto` executável por anon / authenticated | não | não / não (service_role e system_carga: sim) |
| Funções de carga executáveis pela service_role | não | nenhuma (contexto sistema, score, usuários, repasse) |
| Dados do lote 1 | iguais | 8.800 deals (500/1.589/4.238/2.473), 85 contas, 43 usuários, 1.425 abertos sem conta, receita ganha US$ 10.005.534 |

## Testes no banco real (cada tentativa numa transação desfeita no fim)

| Tentativa | Resultado |
|---|---|
| DELETE nas 10 tabelas com dados | recusado, GS405 |
| DELETE nas 19 tabelas novas | estão vazias (0 linhas): o DELETE não acha linha e nada é apagado. Com uma linha inserida antes (`system_eventos`, `system_correlacoes`), recusado GS405. O catálogo mostra o gatilho de bloqueio nas 29 |
| TRUNCATE nas 29 tabelas | recusado (GS405 pelo gatilho, ou 0A000 pela FK nas referenciadas) |
| TRUNCATE `core_contas` CASCADE | recusado, GS405 |
| DELETE / TRUNCATE como `service_role`; DELETE como `system_carga` | recusado, 42501 |
| `anon` lê `core_deals`; `authenticated` lê `core_deals_visao` | recusado, 42501 |
| `anon` executa `system_iniciar_contexto` | recusado, 42501 |
| `service_role` executa o contexto sistema | recusado, 42501 |
| `service_role` escolhe o usuário sistema | recusado, GS403 |
| `service_role` grava como sistema ajustando o contexto direto | recusado, GS403 |
| Escrita sem usuário | recusado, GS401 |
| UPDATE na auditoria | recusado, GS405 |
| `service_role` chama o repasse | recusado, 42501 |
| Limite por usuário (app), com a 0026 e de novo com a 0027 | 30 aceitos, **31º recusado** (GS429) |
| Teto global (app, espalhado por vários usuários), com a 0026 e de novo com a 0027 | 300 aceitos, **301º recusado** (GS429) |
| Parâmetros depois da 0027 | `limite_escritas_por_minuto` = 30, `limite_global_escritas` = 300 |
| `system_iniciar_contexto` depois da 0027 | anon e authenticated não executam; service_role e system_carga executam |
| Depois de todos os testes | `system_correlacoes` com 0 linhas e auditoria com as mesmas 9.019 linhas: nada ficou gravado |

### Depois da 0028 (O-12)

Validador da sessão de dados com a 0028: catálogo ok; testes de uso 122 linhas ok, 0 falha (incluindo atalho, evento sem pedido e registro forjado). No Supabase, cada teste numa transação desfeita:

| Teste | Resultado |
|---|---|
| Atalho do L2-1: `service_role` ajusta `app.usuario_id`/`app.correlation_id` direto e faz UPDATE | **recusado, GS401** ("Pedido sem registro") |
| Evento pela função sem pedido registrado (`service_role`) | recusado, GS401 |
| Registro forjado direto em `system_correlacoes` para o usuário sistema | recusado, GS403 |
| Registro forjado com origem, transação e horário falsos | aceito, mas o banco reescreve os três: `do_app` = verdadeiro, transação atual, horário de agora |
| Registro forjado com o usuário já no limite (30 pedidos antes) | recusado, GS429 |
| Caminho normal do app (`system_iniciar_contexto` + UPDATE) | aceito; 1 linha de auditoria com o usuário 3, papel vendedor |
| Papel de carga (contexto sistema + UPDATE) | aceito; auditado como sistema, fora dos limites (`do_app` = falso) |
| Catálogo | 70 funções com prefixo, 87 gatilhos, 0028 registrada |
| Restos de teste | `system_correlacoes` 0, `system_eventos` 0, `score_execucoes` 0, auditoria 9.019, nenhum deal alterado |

Testes extras desta rodada, que levaram aos achados L2-5 e L2-6:

| Teste | Resultado |
|---|---|
| `service_role` insere linha falsa em `system_auditoria` (ação atribuída a um manager) | **aceito** (desfeito no fim) |
| `system_carga` insere linha falsa em `system_auditoria` | **aceito** (desfeito no fim) |
| `service_role` insere em `system_eventos` direto, sem contexto | aceito (desfeito) |
| `service_role` insere em `score_execucoes` direto, sem contexto | aceito, sem linha de auditoria (desfeito) |
| Tabelas sem gatilho de auditoria em que a `service_role` insere e altera | `score_componentes`, `score_deals`, `score_execucoes`, `score_fit_vendedores`, `score_motivos`, `score_padroes_conta`, `system_auditoria`, `system_correlacoes`, `system_eventos` |

## Achados

| # | Gravidade | Achado | Correção proposta |
|---|---|---|---|
| L2-1 | **Fechado pela 0028** (era média) | A `service_role` podia gravar como um usuário comum ajustando `app.usuario_id` e `app.correlation_id` direto, sem chamar `system_iniciar_contexto`. A escrita passa: a auditoria registra o usuário, mas o pedido não entra em `system_correlacoes`, então pula o limite por usuário, o teto global e a regra de um correlation_id por pedido. Medido: UPDATE aceito, 0 registros de correlação. Só quem tem a chave da service role (o servidor) consegue isso, mas um erro no código do app passaria sem ser barrado | Na 0027, em `system_auditar`, quando o papel for do app, exigir que o `correlation_id` esteja em `system_correlacoes` com a transação atual e o mesmo usuário; senão, recusar (GS401). Assim toda escrita do app passa pelos limites |
| L2-2 | Informação | `acao_marcar_prioridade` tem duas assinaturas. A antiga, de 5 argumentos, é proposital: chama a nova com o tipo vazio, então um ✓ por ela é recusado e só o ✗ passa | Nenhuma |
| L2-3 | Informação | A função `rls_auto_enable` (sem prefixo) existe em `public`, mas é do Supabase, não das nossas migrations | Nenhuma; contar só as funções com prefixo |
| L2-4 | Resolvido | Risco de o ajuste `>` para `>=` baixar o teto para 29/299 | A 0027 trocou também a contagem (só pedidos anteriores); medido: 30/300 aceitos, como pedido |
| L2-5 | **Média** | A auditoria pode ser forjada: `service_role` e `system_carga` têm INSERT direto em `system_auditoria` e gravam uma linha com qualquer usuário, papel, tabela e conteúdo. Uma ação que não aconteceu pode aparecer na linha do tempo do deal. Hoje só o servidor (chave da service role) e as cargas conseguem isso, mas fere a premissa de auditoria durável (ARQ-04) | Tornar `system_auditar()` e `system_registrar_evento()` `security definer` (dono `postgres`, `search_path` fixo) e revogar INSERT e UPDATE de `system_auditoria` e `system_eventos` para `service_role` e `system_carga`. O gatilho continua gravando; ninguém grava direto. Testar depois: linha forjada recusada (42501) e caminho normal ainda auditado |
| L2-6 | Leve | A `service_role` insere e altera as 6 tabelas `score_*` direto, sem contexto, sem auditoria e sem limite. Pelo desenho, as notas vêm só da carga em Python (`system_carga`) | Se o app só lê notas (confirmar com as sessões do score e do app): revogar INSERT e UPDATE de `score_*` para `service_role`. Se o app precisar gravar algo, fazer por função com contexto |
