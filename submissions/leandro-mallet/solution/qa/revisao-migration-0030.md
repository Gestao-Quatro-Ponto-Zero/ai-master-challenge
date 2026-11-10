# Revisão e aplicação — migration 0030 (Prioridades do dia pela nota)

**Veredito: pode rodar. Aplicada em 10/11/2026 às 14:13 UTC, sem erro.** Nenhum achado de segurança.

Ordem O-26. Arquivo `solution/db/migrations/0030_prioridades_pela_nota.sql`, sha256 `8741e6f46d7f9c42068b9a2cd190960c0f031472fa48a64f616f88eaa560194d`: igual ao informado, conferido na cópia e de novo na hora de aplicar. Registrado em `supabase_migrations.schema_migrations` com o mesmo hash. As 0026–0029 do repositório são idênticas às aplicadas.

## Revisão

| Ponto | Resultado |
|---|---|
| Nada destrutivo | ✅ só `add column`, `create index`, `create or replace function`, um `update` e um `insert … on conflict do nothing` em `config_parametros`, os dois auditados como sistema. Nenhum DELETE, DROP ou TRUNCATE. A substituição de itens da lista é por `substituida_em`, nunca por DELETE |
| Trava de contexto, limites, auditoria | ✅ intactos. Nenhuma função de 0022/0026–0029 foi tocada. As funções de escrita da lista (`acao_prioridades_do_dia`, `acao_puxar_mais_prioridades`, `acao_marcar_prioridade`) continuam começando por `system_iniciar_contexto`. O `p_contar_limite = false` não desliga nada para o app desde a 0027/0028, porque o limite vale sempre para pedidos do app |
| Funções auxiliares chamadas direto pelo app | ✅ `acao_atualizar_prioridades` e `acao_montar_prioridades` gravam em `acao_prioridades`, que tem auditoria: sem pedido registrado, a gravação é recusada (0028) |
| Permissões | ✅ as 5 funções novas: sem execução para public, anon e authenticated; executáveis por service_role e system_carga. As 6 funções substituídas mantêm a mesma assinatura, então mantêm as permissões atuais. No banco depois de aplicar: 0 funções executáveis por anon e 0 por authenticated; service_role continua sem as funções de carga |
| Trava por usuário | ✅ `pg_advisory_xact_lock(30030, usuario)` é de transação: solta sozinha no commit ou no rollback. Chamada duas vezes na mesma transação (lista do dia → atualizar) não trava, porque a mesma sessão pode pegar a mesma trava de novo |
| Nova chave estrangeira | ✅ `acao_prioridades.execucao_id → score_execucoes`, ON DELETE RESTRICT, com índice |
| Compatibilidade com o app | ✅ quando `acao_listar_prioridades` volta vazia, o app chama `acao_prioridades_do_dia`, que reconstrói a lista (`repositorio-banco.ts`, linhas 288–289). As 33 linhas de lista que já existiam não têm `execucao_id`, então a primeira abertura de cada usuário pelo app reconstrói a lista dele, como pedido |
| Regras de posição | ✅ itens novos entram depois da maior posição do dia; o item reaproveitado ganha posição nova; não conflita com a posição única por usuário e dia |

## Validação (Postgres em memória, sem conexão)

| Validador | Resultado |
|---|---|
| `validar_tudo.mjs --com-dataset` (0001–0030 sobre o dataset inteiro) | ✅ catálogo ok: 29 tabelas, 61 FKs RESTRICT, 75 funções, 87 gatilhos, 106 índices |
| `validar_tudo.mjs` (testes de uso) | ✅ 134 linhas ok, 0 falha |
| `validar_0030.mjs` | ✅ 21 linhas ok, 0 falha (ordem, super hot sem ticket, filtro do gestor, troca de execução sem apagar, ✓ em item substituído recusado, auditoria) |

## Depois de aplicar (somente leitura)

| Medida | Antes | Depois |
|---|---|---|
| Funções com prefixo | 70 | **75** |
| Gatilhos | 87 | **87** |
| Índices | 104 | **106** |
| Chaves estrangeiras | 60 | **61** |
| `icone_cortes.preco_min_quente` | 3000 | **null** (janela 15/106/138 mantida) |
| `prioridades_gestor` | — | **{"filtro": "atencao"}** |
| Deals | 8.801 (8.800 do dataset + o lead de teste) | 8.801 |
| Notas na execução 5 (ativa) | 2.089 | 2.089 |
| Linhas em `acao_prioridades` | 33 | 33 (nenhuma lista aberta pelo banco) |
| Auditoria | — | +2 linhas, do usuário sistema (os dois parâmetros) |
| Ícones dos abertos | — | super hot 150, em risco 141, esfriou 1.291, sem ícone 507 (o super hot passou de 66 para 150 sem o critério de ticket) |
