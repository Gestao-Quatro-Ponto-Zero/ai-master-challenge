# Revisão e aplicação — migration 0033 (redistribuição de domingo)

**Veredito: pode rodar. Aplicada em 10/11/2026 às 21:34 UTC, sem erro.** Nenhum achado. Nenhum dono de deal mudou.

Ordem O-40. Arquivo `solution/db/migrations/0033_redistribuicao_de_domingo.sql`, sha256 `a8d148a7c8905df69d4780e637c65328dad32ade9bf4834c9694e148d87d4bce`: igual ao informado, conferido na cópia e de novo na hora de aplicar. Registrado em `supabase_migrations.schema_migrations` com o mesmo hash. As 0029–0032 do repositório são idênticas às aplicadas.

## Revisão (comparada com a 0024)

| Ponto | Resultado |
|---|---|
| Nada destrutivo | ✅ só `create or replace` de duas funções; nenhuma alteração de tabela ou dado |
| Repasse por janela (`repasse_janela`) | ✅ continua com as três travas (`fit_minimo`, `max_abaixo_do_dono`, `top_n`), a recusa de lead com contato e a penalidade |
| Redistribuição (`redistribuicao`) | ✅ perde só as três travas de FIT e posição. Continua exigindo deal aberto, vendedor de destino ativo e diferente do dono e o limite por lead (se configurado), com registro em `acao_reatribuicoes` e auditoria, sem penalidade. Motivo: "Redistribuição de domingo." |
| Lead com contato | ✅ a redistribuição **não** passa por cima de lead com contato. Isso ficou mais rígido que antes: na 0024 a checagem de contato valia só para o repasse por janela |
| Contexto | ✅ `core_repassar_deal` continua começando por `system_iniciar_contexto_sistema`, que recusa o app |
| Permissões | ✅ mesma assinatura, então mantém as de antes; no banco: anon, authenticated e service_role **não** executam o repasse; só `system_carga` |
| Linha do tempo | ✅ a 0033 também troca `core_linha_do_tempo` (citado no cabeçalho do arquivo, não na ordem): mesma assinatura; os repasses automáticos aparecem com o motivo ("Redistribuição de domingo. A → B") e a troca de vendedor feita pelo sistema deixa de aparecer duplicada como "Passado para …" |

## Validação (Postgres em memória, sem conexão)

| Validador | Resultado |
|---|---|
| `validar_tudo.mjs --com-dataset` (0001–0033) | ✅ catálogo ok: 61 FKs RESTRICT, 76 funções, 87 gatilhos, 106 índices |
| `validar_tudo.mjs` (uso) | ✅ 137 ok, 0 falha |
| `validar_0030` / `0031` / `0032` | ✅ 21 / 16 / 15 ok, 0 falha |
| `validar_0033.mjs` | ✅ 23 ok, 0 falha: redistribuição aceita fora das travas, sem penalidade e com o motivo novo; recusada com contato, deal fechado, mesmo dono e vendedor inexistente; janela continua recusando as três travas e o contato e gera a penalidade; linha do tempo sem duplicar; só o papel de carga executa; nada apagado |

## Depois de aplicar

| Medida | Antes | Depois |
|---|---|---|
| Funções / gatilhos / índices / FKs | 76 / 87 / 106 / 61 | 76 / 87 / 106 / 61 |
| Deals | 8.801 | **8.801** |
| Donos (md5 de todos os pares deal → vendedor) | `d86dc563…` | **`d86dc563…` (iguais)** |
| `acao_reatribuicoes` / `system_penalidades` | 0 / 0 | 0 / 0 |
| Execução 7 (ativa) | 2.089 notas | 2.089 notas |
| Auditoria gerada pela 0033 | — | **0 linhas** |

Movimento no banco entre a 0032 e a 0033 (não é desta migration): 160 linhas de auditoria em `acao_prioridades`, de vendedores e de um manager, entre 20:54 e 21:19 UTC. É a reconstrução das listas para 20 itens pelo app, como previsto na 0032 (as listas foram de 68 para 124 linhas).
