# Banco do CRM: migrations

Pasta oficial das migrations do Postgres (Supabase). Elas saem de `app/ESPEC-TELAS.md` (seção 8), `app/DESENHO-ACOES.md` e `app/DESENHO-CRM.md`, e seguem as premissas ARQ, BD e BE.

A base é a versão escrita em `app/supabase/migrations/`, já validada num Postgres em memória. Ela foi consolidada aqui e separada em dois lotes.

## Lote 1: cadastros, usuários, auditoria e carga do dataset

Roda sozinho e permite carregar o dataset.

**Ordem de execução:**

| # | Arquivo | Cria |
|---|---|---|
| 1 | `migrations/0001_core_cadastros.sql` | `core_escritorios`, `core_managers`, `core_vendedores`, `core_produtos` e `core_contas` (accounts) |
| 2 | `migrations/0002_config_usuarios.sql` | `config_usuarios` (users, com o papel = profile), `config_parametros` e as funções de leitura de parâmetro |
| 3 | `migrations/0003_core_deals.sql` | `core_deals` (deals) |
| 4 | `migrations/0004_system_auditoria.sql` | `system_auditoria` |
| 5 | `migrations/0005_guardas_base.sql` | relógio do CRM, contexto de quem escreve, auditoria por gatilho, versão do deal, bloqueio de DELETE e TRUNCATE, RLS e permissões |
| 6 | `migrations/0006_config_inicial.sql` | usuários `sistema` (1) e `admin` (2) e os 27 parâmetros (**gerado**) |
| 7 | `seed/seed_dataset.sql` | o dataset limpo (**gerado**), descrito abaixo |

**O que o seed carrega:**
- 3 escritórios, 6 managers, 35 vendedores e 7 produtos;
- 85 contas, das quais 15 têm empresa-mãe;
- 41 usuários do time;
- 8.800 deals.

O seed roda numa transação só, assinado pelo usuário `sistema`.

**Profile:** não há tabela de perfis separada. O perfil é `config_usuarios.papel` (vendedor, manager, admin, sistema), com o vínculo a `vendedor_nome` ou `manager_nome`. Os ids são fixos:

| Id | Usuário |
|---|---|
| 1 | sistema |
| 2 | admin |
| 3–37 | vendedores, de A a Z |
| 38–43 | managers, de A a Z |

**Regras da carga:**
- nome do deal = "Empresa · Produto" (ou "Sem empresa · Produto");
- `data_abertura` = `engage_date`; os Prospecting ficam sem data;
- `close_value` inteiro, com Lost = 0;
- porte = tercil de funcionários;
- empresa independente fica sem empresa-mãe.

Rodar o seed de novo não duplica nem sobrescreve nada (`on conflict do nothing`).

**Ligações com o lote 2:** `core_deals.contato_id`, `core_deals.importacao_id` e `system_auditoria.lote_id` já existem, com índice. As FKs delas são criadas no lote 2, junto com `core_contatos`, `system_importacoes` e `system_lotes`.

### Validação do lote 1 (sem conectar em banco nenhum)

```bash
# numa pasta temporária
npm install @electric-sql/pglite@0.5.11
node <solution>/db/validar_lote1.mjs <solution>/db
```

Aplica as 6 migrations e o seed num Postgres em memória (PGlite), com os papéis do Supabase (`service_role` com `bypassrls`). Resultado em 10/11/2026: **aprovado**.

- **Catálogo:**
  - 9 tabelas, todas com prefixo, e 71 functions, triggers e índices com prefixo;
  - 11 FKs, todas `on delete restrict` e com índice, nenhum CASCADE;
  - RLS e bloqueio de DELETE e TRUNCATE nas 9 tabelas; nenhuma política pública.
- **Dados:** batem com o dataset limpo.
  - 8.800 deals: 4.238 Won, 2.473 Lost, 1.589 Engaging e 500 Prospecting;
  - 1.425 abertos sem empresa e nenhum fechado sem empresa;
  - receita ganha de US$ 10.005.534;
  - 1.480 "GTXPro" corrigidos.
- **Auditoria da carga:** 9.006 linhas, uma por inserção, todas do usuário `sistema`, com data do negócio 31/12/2017.
- **Guardas:**
  - DELETE e TRUNCATE recusados (`GS405`);
  - escrita sem usuário recusada (`GS401`);
  - UPDATE e DELETE na auditoria recusados;
  - `anon` não lê; `service_role` lê e grava, mas não apaga;
  - um update com contexto grava antes, depois e usuário, e atualiza a versão do deal;
  - o seed rodado de novo não muda nada.

Conferência por parser (também sem banco):

```bash
pip install pglast
python solution/db/conferir_migrations.py
```

Confere a sintaxe, inclusive dos corpos PL/pgSQL, e que não há CASCADE, FK sem índice, objeto sem prefixo, DELETE ou TRUNCATE.

### Para regenerar os arquivos gerados

```bash
python solution/data/clean.py
python solution/db/gerar_seed.py
```

## Lote 2: o resto do CRM

Roda depois do lote 1 e do seed, em ordem:

| Arquivo | Cria |
|---|---|
| `0007_core_contatos.sql` | `core_contatos` + FK `core_deals.contato_id` |
| `0008_config_tags.sql` | `config_tags` |
| `0009_score.sql` | execuções; nota por deal com `fit`, `heat` e `bonus` (0–20) e `score` de 0 a 120 (decisão 33); componentes e motivos (grupos fit, heat e bonus); FIT por vendedor e cohort; **`score_padroes_conta`** (padrão de compra por conta) |
| `0010_acao.sql` | ações, comentários, tags nos deals, prioridades do dia e reatribuições |
| `0011_system.sql` | lotes, importações, eventos e roteamentos + FKs `system_auditoria.lote_id` e `core_deals.importacao_id` |
| `0012_guardas.sql` | contato da mesma empresa, limite de tags, último contato, versão do contato, auditoria e bloqueios das tabelas novas |
| `0013_functions_base.sql` | papel, eventos, id, cohort, faixa, ícone, escopo e trava de versão |
| `0014_views.sql` | `score_deals_atuais`, `core_deals_visao` (com `bonus`), `core_painel_janelas` |
| `0015_functions_leitura.sql` | busca por etiquetas, colunas, linha do tempo, painel e funil |
| `0016_functions_deals.sql` | roteamento, cadastro, estágio, encerrar, reabrir, editar, contato, reatribuir e desfazer |
| `0017_functions_importacao.sql` | importação CSV |
| `0018_functions_acao.sql` | ações, comentários, tags e prioridades do dia |
| `0019_functions_lote.sql` | lote e desfazer lote |
| `0020_functions_cargas.sql` | usuários do time (idempotente) e ativação da execução de score |
| `0021_permissoes.sql` | só a service role executa funções |

**`score_padroes_conta`** guarda, por execução e por conta:
- tamanho do histórico (`compras_ganhas`, `receita_ganha`);
- `intervalo_tipico_dias`, `mes_habitual`, `ultima_compra` e `proxima_compra_esperada`;
- `na_janela`, `bonus` e `explicacao`.

O cálculo fica no Python (proposta: recalcular todo domingo).

### Validação completa (sem banco)

```bash
node <solution>/db/validar_tudo.mjs <solution>/db --com-dataset
node <solution>/db/validar_tudo.mjs <solution>/db
```

- **Com o dataset inteiro:** o lote 2 aplica por cima dos 8.800 deals, as 3 FKs pendentes são criadas e validadas sobre os dados, e `core_deals_visao` lê os 8.800 deals. Catálogo final:

  | Objeto | Quantidade |
  |---|---|
  | Tabelas | 26 |
  | FKs (todas RESTRICT e com índice) | 53 |
  | Funções | 64 |
  | Views (todas `security_invoker`) | 3 |
  | Gatilhos | 77 |
  | Índices | 92 |

  Também: RLS e bloqueio em todas as tabelas, `anon` sem acesso e `service_role` sem DELETE.
- **Testes de uso:** 52 verificações aprovadas em 10/11/2026.
  - 45 vêm do validador original: carga, busca, ícones, roteamento, estágios, conflito de versão, desfazer, contato, ações, comentários, tags, lote, importação, prioridades, painel, linha do tempo e bloqueios.
  - 7 são novas: nota 120 com bonus 20; nota 121 e bonus 21 recusados; padrão por conta gravado; padrão de conta inexistente recusado; DELETE no padrão recusado; bonus na visão.

## Dúvidas abertas

1. **Faixas da nota com nota até 120:** os cortes (alta ≥ 70, média ≥ 40) ficam como estão até a #3 decidir se mudam.
2. **Valores ainda provisórios em `config_parametros`:**
   - P5 (abertura como primeiro contato = false);
   - P14 (motivo da perda opcional);
   - roteamento com teto de 200 abertos e mínimo de 10 casos;
   - cohort só por produto.
3. **Aba "Contas" (Leads):** a tabela `score_padroes_conta` está pronta. Os nomes das colunas devem ser alinhados com a ESPEC-TELAS quando a #4 detalhar a aba. Uma view de leitura entra junto.

## Códigos de erro

Para o servidor traduzir em frase simples:

| Código | Significa |
|---|---|
| `GS400` | entrada inválida |
| `GS401` | sem usuário ou sem `correlation_id` |
| `GS403` | papel sem permissão |
| `GS404` | não encontrado |
| `GS405` | apagar é proibido |
| `GS409` | conflito de versão |
| `GS422` | regra de negócio |
| `GS429` | limite de escritas |

## Como as cargas escrevem

A auditoria exige usuário e `correlation_id` em toda escrita.
- A carga começa com `select system_iniciar_contexto_sistema('<uuid>');` dentro de uma transação, e assina como `sistema`.
- Pela REST cada pedido é uma transação, e o contexto se perde. Por isso as cargas usam conexão direta ou um arquivo SQL como o seed.

`_rascunho_v1/` guarda a primeira versão destas migrations, já substituída. Não aplicar.
