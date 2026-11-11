# Revisão e aplicação — migration 0032 (20 prioridades por dia)

**Veredito: pode rodar. Aplicada em 10/11/2026, sem erro.** Nenhum achado.

Ordem O-35. Arquivo `solution/db/migrations/0032_meta_prioridades_20.sql`, sha256 `6424589b3802343999e039ab50320163860454ab4e6760b1a16935b48c5e76c5`: igual ao informado, conferido na cópia e de novo na hora de aplicar. Registrado em `supabase_migrations.schema_migrations` com o mesmo hash. As 0026–0031 do repositório são idênticas às aplicadas.

## Revisão

| Ponto | Resultado |
|---|---|
| Nada destrutivo | ✅ um UPDATE de 1 linha em `config_parametros` (auditado, com `system_iniciar_contexto_sistema`), uma coluna nova `acao_prioridades.meta_dia` (com regra `> 0`) e duas funções trocadas. Nenhum DELETE, DROP ou TRUNCATE |
| Assinaturas | ✅ `acao_lista_desatualizada(bigint) → boolean` e `acao_prioridades_do_dia(bigint, uuid) → table(…)` iguais às da 0030, então as permissões se mantêm. Nenhuma função nova |
| Contexto, limites, auditoria | ✅ `acao_prioridades_do_dia` continua começando por `system_iniciar_contexto` e pela trava de transação por usuário; a gravação de `meta_dia` passa pela auditoria de `acao_prioridades` |
| Permissões no banco | ✅ anon e authenticated não executam as duas funções; service_role executa; nenhuma função executável por anon ou authenticated no schema |
| Lista curta | ✅ quando não há deals suficientes para a meta, as linhas ativas passam a guardar a meta nova e a lista não fica sendo reconstruída a cada leitura (coberto pelo validador) |

## Validação (Postgres em memória, sem conexão)

| Validador | Resultado |
|---|---|
| `validar_tudo.mjs --com-dataset` (0001–0032) | ✅ catálogo ok: 61 FKs RESTRICT, 76 funções, 87 gatilhos, 106 índices |
| `validar_tudo.mjs` (uso) | ✅ 136 linhas ok, 0 falha |
| `validar_0030.mjs` | ✅ 21 ok, 0 falha |
| `validar_0031.mjs` | ✅ 16 ok, 0 falha |
| `validar_0032.mjs` | ✅ 15 ok, 0 falha: a lista de 10 fica desatualizada, vai a 20 na próxima abertura, os 10 de antes ficam no lugar e marcados, os novos entram pela nota, nada apagado, lista curta não fica presa |

## Depois de aplicar

| Medida | Antes | Depois |
|---|---|---|
| `meta_prioridades_dia` | 10 | **20** |
| Funções com prefixo / gatilhos / índices / FKs | 76 / 87 / 106 / 61 | 76 / 87 / 106 / 61 |
| Deals | 8.801 | **8.801** |
| Execução ativa / notas da execução 7 | 7 / 2.089 | **7 / 2.089** |
| Linhas em `acao_prioridades` | 68 | 68, todas ainda sem `meta_dia` (nenhuma lista aberta pelo banco; a primeira abertura pelo app completa até 20) |
| Auditoria | — | +1 linha, do usuário sistema (o parâmetro). O salto de numeração (9227 → 9230) vem de transações desfeitas nos testes da 0031 |
