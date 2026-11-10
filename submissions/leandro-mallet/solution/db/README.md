# Banco do CRM: migrations

Migrations do Postgres (Supabase). Elas saem de `app/ESPEC-TELAS.md` (seção 8), `app/DESENHO-ACOES.md` e `app/DESENHO-CRM.md`, e seguem as premissas ARQ, BD e BE.

## Estado

| Parte | Arquivos | Estado |
|---|---|---|
| Lote 1 | `migrations/0001`–`0006` + `seed/seed_dataset.sql` | **aplicado** no Supabase em 10/11/2026: 9 tabelas, 8.800 deals, 85 contas, 43 usuários e 9.006 linhas de auditoria. Não alterar: mudanças entram como migrations novas |
| Lote 2 | `migrations/0007`–`0025` | escrito e validado (PGlite); em aplicação |
| Complemento de segurança | `migrations/0026_limite_global.sql` | escrito e validado (PGlite); **falta aplicar**, depois da 0025 |

## Ordem de execução do que falta aplicar

Cada arquivo numa transação, rodado pelo dono do schema (`postgres`), na ordem:

| # | Arquivo | O que faz |
|---|---|---|
| 1 | `0007_core_contatos.sql` | contatos + FK `core_deals.contato_id` |
| 2 | `0008_config_tags.sql` | catálogo de tags |
| 3 | `0009_score.sql` | execuções; nota por deal (`fit`, `heat`, `bonus` 0–20, `score` 0–120); componentes; motivos; FIT por vendedor e cohort; `score_padroes_conta` (padrão de compra por conta) |
| 4 | `0010_acao.sql` | ações, comentários, tags nos deals, prioridades do dia e reatribuições |
| 5 | `0011_system.sql` | lotes, importações, eventos e roteamentos + FKs `system_auditoria.lote_id` e `core_deals.importacao_id` |
| 6 | `0012_guardas.sql` | integridade, auditoria e bloqueios das tabelas do lote 2 |
| 7 | `0013_functions_base.sql` | papel, eventos, id, cohort, faixa, ícone, escopo e trava de versão |
| 8 | `0014_views.sql` | `score_deals_atuais`, `core_deals_visao`, `core_painel_janelas` |
| 9 | `0015_functions_leitura.sql` | busca por etiquetas, colunas, linha do tempo, painel e funil |
| 10 | `0016_functions_deals.sql` | roteamento, cadastro, estágio, encerrar, reabrir, editar, contato, reatribuir e desfazer |
| 11 | `0017_functions_importacao.sql` | importação CSV |
| 12 | `0018_functions_acao.sql` | ações, comentários, tags e prioridades do dia |
| 13 | `0019_functions_lote.sql` | lote e desfazer lote |
| 14 | `0020_functions_cargas.sql` | usuários do time e ativação da execução de score |
| 15 | `0021_permissoes.sql` | permissões das funções |
| 16 | `0022_seguranca.sql` | **correção de segurança**: papel de carga, `correlation_id` único por transação, limite de escritas contado pelo banco |
| 17 | `0023_atividades.sql` | **decisão 37**: tipo de atividade e comentário obrigatórios no ✓ |
| 18 | `0024_roteamento_repasse.sql` | **decisões 35 e 38**: roteamento sem teto, repasse e penalidade |
| 19 | `0025_permissoes_e_guardas.sql` | proteções das tabelas novas, política do papel de carga e permissões finais |
| 20 | `0026_limite_global.sql` | **teto global** de pedidos do app por janela (soma de todos os usuários); o papel de carga fica fora |

## Segurança

**Papel de carga (`system_carga`).** É um papel de banco separado do papel do app (`service_role`).
- Só ele age como o usuário "sistema": `system_iniciar_contexto_sistema`, `score_ativar_execucao`, `config_gerar_usuarios` e `core_repassar_deal`.
- O app não executa essas funções.
- O app também não consegue escolher o usuário "sistema" nem gravar como ele: o contexto e a auditoria recusam (`GS403`).
- As cargas usam conexão direta, como dono: `set role system_carga;` e depois `select system_iniciar_contexto_sistema('<uuid novo>');`, numa transação.
- O papel de carga tem uma política de RLS só para ele. Não há política para `anon`, `authenticated` ou `service_role`.

**`correlation_id`.**
- Gerado pelo servidor (na rota, com `crypto.randomUUID()`), nunca aceito do cliente.
- O banco registra cada um em `system_correlacoes`, com a transação. Reaproveitar um `correlation_id` em outra transação é recusado (`GS400`).

**Limites de escrita.** Os dois são contados pelo banco em `system_correlacoes`, na janela `janela_limite_segundos` (60). Valem sempre para o app, que não consegue desligá-los; o papel de carga fica fora dos dois.

| Limite | Conta | Padrão | Erro |
|---|---|---|---|
| por usuário | pedidos daquele usuário | mais de 30 por janela | `GS429`: "Muitas mudanças seguidas. Espere alguns segundos." |
| global (`0026`) | pedidos de todos os usuários do app somados | mais de 300 por janela (`limite_global_escritas`) | `GS429`: "O sistema está recebendo muitas mudanças agora. Tente de novo em alguns segundos." |

**Limitação que continua: não há login (decisões 12 e 15).** Qualquer pessoa escolhe qualquer usuário da tela, **inclusive o admin**, e age como ele.
- **Sem login, o limite por usuário só organiza o uso:** quem quiser abusar troca de usuário.
- **A proteção real contra abuso tem duas camadas:**
  - o teto global no banco (`0026`);
  - o limite por endereço de rede nas rotas do app (feito no app, não no banco).
- A auditoria registra qual usuário foi escolhido em cada escrita.
- Para uso real, seria preciso login.

## Regras de negócio no banco (números em `config_parametros`)

- **✓ nas Prioridades do dia (decisão 37):**
  - exige tipo de atividade (`config_tipos_atividade`: Ligação, E-mail, Mensagem, Reunião, Proposta enviada, Requalificado, Sem resposta) e comentário (até 280 caracteres);
  - grava em `acao_registros`, com o item da lista do dia e o horário real (`criado_em`), e atualiza o último contato;
  - o ✗ continua sem registro obrigatório;
  - a assinatura antiga de `acao_marcar_prioridade` (sem tipo) ainda aceita o ✗ e recusa o ✓.
- **Roteamento (decisão 38):**
  - sem teto de abertos;
  - lead novo vai ao vendedor de maior FIT no cohort, menos a penalidade ativa, com o mínimo de casos;
  - a distribuição equilibrada do recálculo de domingo é feita pelo score (Python) e gravada pelo papel de carga.
- **Repasse (`core_repassar_deal`, só o papel de carga):**
  - só com o FIT do novo vendedor ≥ 75, no máximo 3 pontos abaixo do FIT do dono, e o lead no top 5 do novo;
  - no repasse por mudança de janela, o lead tem de estar sem contato;
  - fica registrado em `acao_reatribuicoes`, com origem, FITs, posição e faixa.
- **Penalidade (`system_penalidades`):** quem perde lead por repasse de janela recebe `pontos` por `dias`, descontados do FIT só na escolha do vendedor de lead novo. A nota dos deals não muda.
- **Ainda a decidir (ficam `null` até a regra do score fechar):**
  - tamanho e duração da penalidade (`null` = sem penalidade);
  - máximo de repasses por lead (`null` = sem limite).
- **Furar a fila:** `fit_furar_fila` = 75. Quem usa é o score e a lista de prioridades.
- **Nota:** de 0 a 120 (0,70 × FIT + 0,30 × HEAT + bonus de 0 a 20). A fórmula fica no score, não no SQL.

## Validação (sem conectar em banco nenhum)

```bash
# numa pasta temporária, fora do Drive
npm install @electric-sql/pglite@0.5.11
node <solution>/db/validar_lote1.mjs <solution>/db                 # lote 1 + seed
node <solution>/db/validar_tudo.mjs  <solution>/db --com-dataset   # tudo sobre o dataset inteiro + catálogo
node <solution>/db/validar_tudo.mjs  <solution>/db                 # testes de uso
pip install pglast && python <solution>/db/conferir_migrations.py  # conferência por parser
```

Resultado em 10/11/2026, tudo aprovado:
- **Lote 1 + seed:** dados batem com o dataset limpo; guardas conferidas.
- **Tudo sobre o dataset inteiro:** o lote 2 aplica por cima dos 8.800 deals, e as 3 FKs pendentes do lote 1 são criadas e validadas sobre os dados.

  | Objeto | Quantidade |
  |---|---|
  | Tabelas | 29 |
  | FKs (todas RESTRICT e com índice, nenhum CASCADE) | 60 |
  | Funções | 68 |
  | Views (todas `security_invoker`) | 3 |
  | Gatilhos | 86 |
  | Índices | 103 |

  Também: RLS e bloqueio de DELETE e TRUNCATE em todas as tabelas, e nenhuma política fora do papel de carga. `anon` não executa nada; `service_role` não apaga e não executa as funções de carga.
- **Testes de uso: 71 verificações** (com a 0026: o teto global recusa o app mesmo trocando de usuário, e o papel de carga passa).
  - Carga, busca, ícones, roteamento, estágios, conflito de versão, desfazer, contato, ações, comentários, tags, lote, importação, prioridades, painel, linha do tempo e bloqueios.
  - ✓ com tipo e comentário (e as recusas sem eles).
  - Segurança: o app não age como sistema; `correlation_id` reaproveitado é recusado; o 31º pedido no minuto é recusado; a carga grava como sistema.
  - Repasse: as três travas e o repasse com penalidade.
  - Roteamento sem teto, bonus e nota até 120, e o padrão por conta.
- **Parser:** 25 arquivos, sintaxe válida em todos os corpos de função, todo objeto com prefixo, nenhum DELETE.

## Códigos de erro

Para o servidor traduzir em frase simples:

| Código | Significa |
|---|---|
| `GS400` | entrada inválida (inclui `correlation_id` reaproveitado) |
| `GS401` | sem usuário ou sem `correlation_id` |
| `GS403` | papel sem permissão (inclui o app tentando agir como sistema) |
| `GS404` | não encontrado |
| `GS405` | apagar é proibido |
| `GS409` | conflito de versão |
| `GS422` | regra de negócio |
| `GS429` | limite de escritas |

## Arquivos gerados

Para regenerar `0006_config_inicial.sql` e `seed/seed_dataset.sql` a partir de `data/clean/`:

```bash
python solution/data/clean.py
python solution/db/gerar_seed.py
```
