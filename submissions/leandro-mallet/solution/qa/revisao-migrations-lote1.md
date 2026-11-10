# Revisão e aplicação — banco, lote 1

**Veredito: pode rodar. Aplicado em 10/11/2026, sem erro.**

Escopo: migrations 0001–0006 e a carga do dataset (`db/seed/seed_dataset.sql`), da pasta oficial `solution/db/`. O rascunho anterior de 18 arquivos (`app/supabase/migrations/`) foi revisado, mas **não** foi aplicado: a orquestração trocou a base antes da aplicação.

## Como foi aplicado

- Arquivos copiados para uma pasta temporária antes de aplicar; hash conferido depois com o commit `0a69f6b` (idênticos).
- Conexão direta ao Postgres do Supabase como `postgres` (dono do schema), pelo `DATABASE_URL` do `.env` local (fora do git).
- Um arquivo por vez, cada um numa transação: falhou = rollback e parada. O seed tem `begin`/`commit` próprios e rodou como está.
- Controle das aplicadas em `supabase_migrations.schema_migrations` (schema padrão do Supabase para migrations, fora do `public`, para não criar tabela sem prefixo), com o sha256 de cada arquivo.
- Nenhum DROP, DELETE ou TRUNCATE. Banco vazio antes (0 tabelas em `public`).

| Arquivo | sha256 |
|---|---|
| 0001_core_cadastros.sql | `33c8cc1733a38d8383731b4e4dea0aa1193f0761df7f81263fe4547be08ec1e7` |
| 0002_config_usuarios.sql | `71343ec7fb2d1da70693b33fcb49933dcdb2fc935337693eeffe5499c453905b` |
| 0003_core_deals.sql | `f3ff29061359ad037333ee327861af0a67b0fedbc248c4818f1c34d49938f827` |
| 0004_system_auditoria.sql | `e60b08f359a45c03229a0b631c7a278a33a4812541b8dcbeef7ffb32dc81b79b` |
| 0005_guardas_base.sql | `fd900f5115eb983944c25cf8c5093d5c730b64f52d721d8799f090414d02d9b3` |
| 0006_config_inicial.sql | `b161eb6b8d9d6b482dcda9692dd0e72bb5b34ae202e05ae64c333ab792e9ba58` |
| seed/seed_dataset.sql | `480b1cf5e90d538421d4b40d8d213af2d5b6b819f63d8ef32dd282f4aafd29e6` |

## Critérios conferidos

| Critério | Fonte | Resultado |
|---|---|---|
| Prefixo de domínio, snake_case, plural | BD-01 | ✅ 9 tabelas, todas com prefixo |
| Toda FK declarada, com índice e ON DELETE RESTRICT, nenhum CASCADE | BD-02 | ✅ 11 FKs; as 3 que apontam para tabelas do lote 2 (`contato_id`, `importacao_id`, `lote_id`) ficaram como coluna com índice e foram criadas e validadas no lote 2 |
| Deal sem conta = chave nula | BD-02 | ✅ 1.425 abertos com `conta_nome` nula; 0 fechados |
| RLS em todas as tabelas, sem política pública; anon e authenticated sem acesso | BD-03 | ✅ |
| Nenhuma exclusão; DELETE e TRUNCATE barrados | BD-04 | ✅ testado (abaixo) |
| Dinheiro em inteiro | BD-05 | ✅ `preco`, `close_value` inteiros; `receita_milhoes` é medida (numeric) |
| Auditoria: antes, depois, usuário, papel, momento, correlation_id; escrita sem usuário recusada | ARQ-04 | ✅ 9.006 linhas, todas do usuário "sistema" |
| Data de referência fixa | premissas | ✅ `data_referencia` = 2017-12-31, modo demonstração ligado |
| Colunas que as telas pedem (ESPEC-TELAS 8.1) | ESPEC | ✅ `nome`, `data_abertura`, `ultimo_contato_em`, `criado_em`, `criado_por`, `porte`, motivo da perda |

## Conferência depois da carga

| Medida | Esperado | No banco |
|---|---|---|
| Deals | 8.800 | 8.800 |
| Prospecting / Engaging / Won / Lost | 500 / 1.589 / 4.238 / 2.473 | 500 / 1.589 / 4.238 / 2.473 |
| Abertos sem empresa | 1.425 | 1.425 |
| Fechados sem empresa | 0 | 0 |
| Receita ganha | US$ 10.005.534 | US$ 10.005.534 |
| Deals de GTX Pro (corrigido de "GTXPro") | 1.480 | 1.480 |
| Contas / produtos | 85 / 7 | 85 / 7 |
| Vendedores / managers / escritórios | 35 / 6 / 3 | 35 / 6 / 3 |
| Usuários | 43 (35 vendedores, 6 managers, admin, sistema) | 43 |
| Linhas de auditoria do usuário sistema | 9.006 | 9.006 |

## Testes de recusa (cada um numa transação desfeita no fim)

| Tentativa | Resultado |
|---|---|
| DELETE em `core_deals`, `core_contas`, `config_usuarios`, `system_auditoria`, `core_escritorios` (postgres) | recusado, GS405 |
| TRUNCATE em `core_deals`, `system_auditoria` | recusado, GS405 |
| TRUNCATE em tabela referenciada (`core_contas`, `config_usuarios`, `core_escritorios`) | recusado pela FK (0A000); com CASCADE, recusado pelo gatilho (GS405, testado no lote 2) |
| DELETE e TRUNCATE como `service_role` | recusado, 42501 (sem permissão) |
| SELECT como `anon` e `authenticated`; UPDATE como `anon` | recusado, 42501 |
| UPDATE na auditoria | recusado, GS405 |

## Achados

| # | Gravidade | Achado | Situação |
|---|---|---|---|
| L1-1 | Grave | No lote 1, qualquer papel com permissão de execução podia chamar `system_iniciar_contexto_sistema` e gravar como "sistema" | Corrigido no lote 2 (0022 e 0025), conferido no banco: a `service_role` é recusada (42501 e GS403). Nenhum app conectou antes da correção |
| L1-2 | Leve | `core_deals` não tem índice só em `close_date`; o filtro "fechou em…" usa o índice (`estagio`, `close_date`) | Sem ação agora; rever se a tela filtrar por data sem estágio |
| L1-3 | Informação | TRUNCATE em tabela referenciada é recusado primeiro pela FK; a trava própria (GS405) aparece com CASCADE | Comportamento correto |
