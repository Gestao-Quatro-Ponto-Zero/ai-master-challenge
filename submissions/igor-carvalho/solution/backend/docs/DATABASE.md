# Banco de dados (SQLite) — esquema v1 **CONGELADO**

Arquivo: `src/lead_core/sql/schema_v1.sql`. Um teste (`tests/core/test_schema_frozen.py`) compara o hash
do arquivo com `schema_v1.sha256` e **falha se o esquema mudar**. Só altere com pedido explícito do dono do projeto
(e então: nova migração `schema_v2.sql` + atualizar o hash, nunca editar o v1).

**O que NÃO está no banco:** scores, probabilidades e modelos. Eles ficam em `artifacts/v{versão}/`
(`model.txt`, `tables.json`, `model_card.json`, `scored_deals.parquet`) e o ponteiro `artifacts/CURRENT`.
O banco guarda só dados gerados pela operação.

| Tabela | Função | Regras principais |
|---|---|---|
| `schema_info` | versão do esquema | linha única (`id = 1`) |
| `users` | usuários do MVP (login por `user_key`) | `role` ∈ seller/manager/revops; vendedores e managers vêm de `sales_teams` |
| `deal_feedback` | feedback do vendedor (`worked`/`disagree`/`ignore`) | só inserção; comentário ≤ 280; guarda versão do modelo, score e faixa no momento |
| `model_versions` | registro de versões treinadas | status candidate/active/retired/rejected; **índice único parcial** garante 1 `active` |
| `jobs` | retreino/refresh disparados pela API | índice único parcial: só 1 `retrain` em fila/rodando |

## Fluxo
1. `lead-trainer train` grava `artifacts/v{N}`, registra em `model_versions` e, se passar no portão, promove (atualiza `CURRENT`).
2. A API lê `CURRENT` na subida (e em `POST /admin/refresh`); nunca treina.
3. `POST /admin/retrain` cria um `job` e executa o treinador em subprocesso.

## Acesso ao banco (SQLAlchemy)
`lead_core/persistence/` é a única camada que fala com o SQLite:
- `models/`: um arquivo por entidade (`user.py`, `deal_feedback.py`, `model_version.py`, `job.py`), mapeando as tabelas existentes. O ORM **nunca** cria nem altera tabelas; o DDL é `schema_v1.sql`.
- `database.py`: `Database` (engine + sessões; foreign keys e WAL ligados em toda conexão).
- `repository/`: um repositório por entidade (`user_repository.py`, `feedback_repository.py`, `model_version_repository.py`, `job_repository.py`). Devolvem dicts, nunca objetos ORM.

Services (`lead_api/services`), routers e o treinador usam só os repositórios. Testes de arquitetura (`tests/core/test_architecture.py`)
falham se `sqlite3`, `sqlalchemy` ou SQL cru aparecerem fora dessa camada.
