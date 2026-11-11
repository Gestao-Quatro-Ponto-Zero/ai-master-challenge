# Revisão e aplicação — migration 0034 (relógio e rotina)

**Veredito: pode rodar. Aplicada em 10/11/2026 às 22:44 UTC, sem erro.** Nenhum achado de segurança. Senha do papel da rotina definida fora do git.

Ordem O-44. Arquivo `solution/db/migrations/0034_relogio_e_rotina.sql`, sha256 `ed2065bdc49c3ca345f79d74be5541fcb0cc6df138cbc6ad477fe956093f0f64`: igual ao informado, conferido na cópia e de novo na hora de aplicar. Registrado em `supabase_migrations.schema_migrations` com o mesmo hash. A 0033 do repositório é idêntica à aplicada.

Antes de aplicar: nenhuma transação aberta no banco. A redistribuição da sessão do score já tinha terminado (475 reatribuições, última gravação às 21:51 UTC).

## Revisão

| Ponto | Resultado |
|---|---|
| Nada destrutivo | ✅ 2 parâmetros novos (`data_ancora_real`, `data_ancora_negocio`), a descrição de `modo_demonstracao`, `system_data_negocio()` trocada (mesma assinatura), 1 função nova e o papel `g4_rotina`. Tudo auditado como sistema |
| Papel `g4_rotina` | ✅ login, `noinherit`, sem superusuário, sem `createrole`, sem `createdb`, sem replicação, sem `bypassrls`; membro só de `system_carga`; sem senha no arquivo |
| Função nova `system_rotina_ja_rodou(date)` | ✅ sem execução para public, anon e authenticated; só leitura de `system_eventos` |
| Relógio | ✅ data de negócio = âncora de negócio + (dia real − âncora real). Hoje (10/11/2026 no fuso do CRM) devolve **31/12/2017**. Em 17/11/2026 será 07/01/2018 (domingo) |
| Contexto, limites, auditoria | ✅ intactos; nenhuma função de segurança tocada |

## Validação (Postgres em memória, sem conexão)

| Validador | Resultado |
|---|---|
| `validar_tudo.mjs --com-dataset` (0001–0034) | ✅ catálogo ok: 61 FKs RESTRICT, 77 funções, 87 gatilhos, 106 índices |
| `validar_tudo.mjs` (uso) | ✅ 138 ok, 0 falha |
| `validar_0030` / `0031` / `0032` / `0033` | ✅ 21 / 16 / 15 / 23 ok, 0 falha |
| `validar_0034.mjs` | ✅ 15 ok, 0 falha (âncoras, 7 dias depois = 07/01/2018 domingo, view anda junto, papel só de `system_carga`, rotina registra o dia, falha não conta, app continua sem agir como sistema, anon sem execução) |

## Senha do `g4_rotina`

- Gerada aleatória (64 caracteres hexadecimais) e aplicada com `alter role … password`, por parâmetro, sem passar pelo git nem por arquivo de migration.
- A URL do pooler, com o usuário no formato do pooler (`g4_rotina.<ref>`), foi gravada **só** em `ai-master-challenge/.env` como `DATABASE_URL_ROTINA`. O `.env` é ignorado pelo git (`.git/info/exclude`, conferido com `git check-ignore`). Fim de linha LF.
- A senha e a URL não foram impressas em nenhum momento.

## Teste da conexão como `g4_rotina` (cada tentativa numa transação desfeita)

| Tentativa | Resultado |
|---|---|
| Conectar pelo pooler | ✅ `current_user = session_user = g4_rotina` |
| Sem assumir a carga: `system_data_negocio()`, ler `core_deals` e `score_deals`, atualizar `core_deals` | recusado (42501) em todos |
| `set role postgres` / `service_role` / `authenticated` | recusado (42501) em todos |
| Com `set role system_carga`: `system_data_negocio()` | ✅ 31/12/2017 |
| Com `system_carga`: `system_rotina_ja_rodou(hoje)` | ✅ falso (a rotina ainda não rodou) |
| Com `system_carga`: ler `core_deals` | ✅ 8.801 |
| Com `system_carga`: DELETE em `core_deals`; INSERT direto em `system_auditoria` e `system_eventos` | recusado (42501) |
| Com `system_carga`: UPDATE sem contexto | recusado (GS401) |
| Com `system_carga`: contexto sistema + `system_registrar_evento` | ✅ permitido (desfeito; nenhum evento de teste ficou) |
| Com `system_carga`: criar papel, alterar tabela | recusado |

## Depois de aplicar

| Medida | Antes | Depois |
|---|---|---|
| Funções com prefixo / gatilhos / índices / FKs | 76 / 87 / 106 / 61 | **77** / 87 / 106 / 61 |
| Deals | 8.801 | 8.801 |
| Donos (md5 de todos os pares deal → vendedor) | `4e4f8e94…` | `4e4f8e94…` (iguais) |
| Reatribuições / penalidades | 475 / 0 | 475 / 0 |
| Execução ativa / notas | 9 / 2.089 | 9 / 2.089 |
| Auditoria gerada pela 0034 | — | 3 linhas do sistema (as 2 âncoras e a descrição de `modo_demonstracao`) |
