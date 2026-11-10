# Banco do CRM: migrations

Migrations SQL do Postgres (Supabase), derivadas de `app/ESPEC-TELAS.md` (seção 8), `app/DESENHO-ACOES.md`, `app/DESENHO-CRM.md` e das premissas ARQ, BD e BE.
**Escritas, não aplicadas**: nenhuma foi rodada contra o banco.

## Arquivos (aplicar em ordem)

| Arquivo | Responsabilidade |
|---|---|
| `0001_core.sql` | escritórios, managers, vendedores, produtos, contas, contatos e deals |
| `0002_config.sql` | usuários, parâmetros, tags, motivos de perda; fecha as FKs de `core_` para `config_`; funções de leitura de parâmetro |
| `0003_score.sql` | execuções, notas (score, fit, heat), componentes, motivos e cohorts por vendedor |
| `0004_acao.sql` | ações, prioridades do dia, comentários, tags no deal e atribuições (roteamento e reatribuição) |
| `0005_system.sql` | lotes, auditoria, eventos e importações; fecha a FK `core_deals.importacao_id` |
| `0006_guardas.sql` | contexto obrigatório, auditoria por gatilho, bloqueio de DELETE e TRUNCATE, RLS, revoke e gatilhos de regra |
| `0007_views.sql` | `score_deals_atuais`, `core_deals_visao`, `core_painel_janelas` |
| `0008_functions.sql` | leitura das telas, escrita, lote, roteamento e permissão de execução só para a service role |
| `0009_dados_iniciais.sql` | **gerado** por `gerar_dados_iniciais.py`: parâmetros, motivos de perda, time do dataset e `config_usuarios` |

Contas, produtos, deals e notas não estão nas migrations: entram pela carga em Python (`on conflict do nothing`), assinada pelo usuário `sistema` (id 1).

## Conferir sem conectar no banco

```bash
pip install pglast
python solution/db/conferir_migrations.py
```

Usa o parser oficial do Postgres (libpg_query) e confere:
- sintaxe de todos os comandos e dos corpos PL/pgSQL e SQL;
- nenhum CASCADE;
- toda FK com `on delete restrict` e com índice;
- prefixo em todo objeto;
- nenhum DELETE ou TRUNCATE;
- todas as tabelas no laço de RLS e bloqueio.

Resultado atual:

| Objeto | Quantidade |
|---|---|
| Tabelas | 25 |
| FKs | 52 |
| Índices explícitos | 64 |
| Views | 3 |
| Functions | 47 |
| Triggers | 70 (20 explícitos + 50 de bloqueio: delete e truncate em cada tabela) |

O parser **não** confere nomes de colunas nem tipos: isso só aparece aplicando num Postgres de teste.

## Garantias

- **Sem DELETE e sem TRUNCATE.** Todas as tabelas têm gatilho `before delete` e `before truncate`, além de `revoke delete, truncate` de `public`, `anon`, `authenticated` e `service_role`. Remover é sempre update: `removido_em`, `removida_em`, `inativo_em`, `ativo = false` ou encerrar o deal.
- **RLS ligado em todas, sem política.** `anon` e `authenticated` perdem tudo (inclusive as functions). Só a service role, no servidor, lê e grava.
- **Auditoria obrigatória.** Toda function de escrita começa com `system_definir_contexto(usuario_id, correlation_id)`.
  - O gatilho `system_auditar` recusa escrita sem contexto.
  - Grava antes, depois, usuário, papel, `correlation_id`, `lote_id` e `data_negocio`.
  - Em `core_contatos`, e-mail e telefone ficam mascarados.
- **Versão do deal.** A tela envia `p_versao` (o `atualizado_em` que leu). Se o deal mudou, a escrita é recusada com `G4409` (HTTP 409).
- **Dinheiro em inteiro:** `preco`, `close_value`, `valor_esperado`.
- **Dono do deal não bloqueia nada.** Só duas regras de papel ficam no banco, por serem regra de dado: reabrir deal encerrado e reatribuir deal (manager e admin).

**Códigos de erro (SQLSTATE) para a API traduzir em frase simples:**

| Código | Significa |
|---|---|
| `G4401` | sem contexto ou usuário inválido |
| `G4403` | papel sem permissão |
| `G4404` | não encontrado |
| `G4405` | remoção proibida |
| `G4409` | conflito de versão |
| `G4422` | dado inválido (a mensagem é um código, ex.: `motivo_de_perda_obrigatorio`) |
| `G4429` | limite de escritas por minuto |

## Score: só a estrutura

`SCORE = 0,70 × FIT + 0,30 × HEAT`. Os pesos vão em `score_execucoes.pesos`. O banco não calcula FIT nem HEAT: a fórmula é da sessão do score.

| Onde | O que guarda |
|---|---|
| `score_deals` | `score`, `fit`, `heat` (nulos = sem dado), `acao_sugerida`, `valor_esperado`, `marcadores` e o `vendedor_nome` dono na hora da nota |
| `score_componentes` | `grupo` (fit, heat ou outro), `rotulo`, `pontos` e `maximo`, para o "X de Y pontos" do modal |
| `score_motivos` | frases do modal, em ordem |
| `score_vendedor_cohorts` | taxa de ganho por vendedor × cohort em média móvel de 3 meses, com encolhimento (base do FIT e do roteamento) |

As dimensões aceitas em `score_vendedor_cohorts` são `produto`, `serie`, `setor`, `porte`, `receita`, `empresa`, `sede` e `tempo_venda`.

Os replies previstos para o HEAT entram como `acao_registros.acao = 'resposta_recebida'`. O dataset não tem esse dado.

## Roteamento de lead novo

`core_criar_deal` sem vendedor chama `core_rotear_lead`:

1. Escolhe o vendedor ativo de maior `taxa_encolhida` num cohort que casa com o lead (produto, série, setor, porte, empresa, sede), na execução ativa. Só concorre quem tem pelo menos `roteamento_min_casos` (10) deals no cohort e menos de `roteamento_teto_abertos` (200) abertos.
2. Sem execução ativa ou sem candidato, o lead vai para o vendedor ativo com menos abertos (`roteamento_reserva`, com evento em `system_eventos`).

Tudo fica em `acao_atribuicoes`. A reatribuição pelo manager (`core_reatribuir_deal`) também é registrada lá, com o motivo.

## Nomes: o que mudou em relação à ESPEC-TELAS (para a camada de dados do app)

Os nomes de tabelas e colunas da ESPEC foram mantidos. O que mudou:

**Tabelas novas:**
- `config_motivos_perda` (FK de `core_deals.motivo_perda`);
- `score_vendedor_cohorts` (FIT e roteamento);
- `acao_atribuicoes` (roteamento e reatribuição).

**Colunas novas:**

| Tabela | Colunas |
|---|---|
| `core_deals` | `engage_date` (valor original, ao lado de `data_abertura`) e `ultimo_contato_carga` (piso do último contato vindo da carga, P5) |
| `core_vendedores` | `ativo` |
| `core_contas` | `atualizado_em`, `atualizado_por` |
| `config_parametros` | `descricao`, `atualizado_por` |
| `config_tags` | `arquivada_em`, `arquivada_por` |
| `score_execucoes` | `parametros`, `origem`, `notas`, `criado_por` (e `arquivo_sha256` passa a aceitar nulo, para rodadas lidas do banco) |
| `score_deals` | `vendedor_nome`, `fit`, `heat` |
| `score_componentes` | `grupo`, `rotulo`, `maximo`, `ordem` |
| `score_motivos` | `componente` |
| `acao_registros` | `correlation_id`; a ação `resposta_recebida` |
| `system_auditoria` | `data_negocio` |
| `system_eventos` | `usuario_id` |
| `system_importacoes` | `recusas` |
| `system_lotes` | `detalhe` |

**Functions:**
- Todas as de escrita recebem `p_usuario_id` e `p_correlation_id` primeiro, inclusive `core_mudar_estagio`, `system_executar_lote` e `system_desfazer_lote`.
- `acao_prioridades_do_dia` também recebe `p_correlation_id`, porque grava a fila na primeira chamada do dia.
- `core_encerrar_lote` (DESENHO-ACOES) virou `system_executar_lote` com tipo `encerrar_perdido`.
- Novas: `core_desfazer_mudanca` (Desfazer de 10 s), `core_reatribuir_deal`, `core_rotear_lead`, `core_filtrar_deals` e `core_escopo_vendedores`.

**Etiquetas aceitas por `core_buscar_deals` / `core_filtrar_deals` (`p_etiquetas`):**
- `estagios`, `nota_min`, `nota_menor_que`, `sem_nota`, `icones`
- `abertura_de`, `abertura_ate`, `sem_abertura`, `dias_abertura_maior_que`
- `contato_ha_dias_min` (inclui sem contato), `contato_ha_dias_max`, `sem_contato`, `sem_contato_principal`
- `setores`, `portes`, `sem_empresa`, `empresas`, `produtos`, `series`
- `vendedores`, `managers`, `regioes`, `acoes`
- `fechamento_de`, `fechamento_ate`, `valor_min`
- `tags` (ids), `sem_tag`, `com_comentario`, `contem`

**Ordens:** `nota`, `valor`, `dias_sem_contato`, `dias_abertura`, `data_abertura`, `ultimo_contato`, `fechamento`, `vendedor`, `lead` e `padrao_leads`.

**Escopo:** `{"vendedor": nome}`, `{"manager": nome}` ou `{}`, com `regiao`, `manager` e `vendedor` opcionais e combináveis.

## O que pode faltar por causa das telas Insights e Configurações (ainda não especificadas)

**Insights:**
- functions de agregação (ex.: conversão por cohort, ciclo por faixa de tempo, ponto forte por vendedor);
- talvez tabelas de resumo ou views materializadas, se a base crescer;
- leitura da série de `score_vendedor_cohorts` (já está gravada por execução) e o histórico de `score_execucoes`.

**Configurações:**
- functions de escrita para `config_parametros` (hoje só a migration e a carga gravam), com validação por chave;
- gestão de usuários (ativar ou desativar, criar usuário) e de `core_vendedores.ativo`;
- edição de motivos de perda e reativar tag arquivada;
- cadastro de empresa nova (`core_criar_conta`), que depende da decisão "só escolher ou também criar empresa" (DESENHO-CRM, item 5).

**Nas duas:**
- quem pode ver e editar o quê, se surgir regra de papel além das duas que já estão no banco.

## Dúvidas

1. **Relógio fixo × prioridades do dia:**
   - Com `data_referencia` fixa em 31/12/2017, o "dia" nunca acaba. A fila montada na primeira abertura fica para sempre.
   - O alerta de "pulado 3 dias seguidos" nunca dispara.
   - Proposta: a fila do dia usar a data real e as datas de negócio continuarem fixas.
2. **Último contato (P5):** a carga preenche `ultimo_contato_carga` com `engage_date` nos deals em negociação, ou deixa vazio? O gatilho nunca fica abaixo desse piso.
3. **Ações que contam como contato:** hoje Liguei e Requalifiquei (`acoes_contato`). A `resposta_recebida` também conta?
4. **Teto de abertos do roteamento:** 200 é chute; o maior pipeline hoje tem 194. Precisa de um número decidido, assim como o mínimo de casos (10, o mesmo da análise em média móvel).
5. **Tokens de cor das tags:** usei `marinho`, `dourado`, `dourado-medio`, `dourado-claro`, `bronze` e `bronze-escuro`. A #4 confirma os 6 do tema.
6. **Motivos de sistema:**
   - `cadastro_desfeito` e `importacao_desfeita` estão na lista para o "Desfazer cadastro" e o encerramento em lote de uma importação.
   - A tela precisa esconder esses dois da lista de escolha.
7. **Regras de "quem pode" que ficaram só na tela:**
   - editar o próprio comentário;
   - apagar comentário (autor, manager ou admin);
   - criar tag (manager e admin);
   - importar (manager e admin).
   Pela decisão 16 o banco não bloqueia por dono. Se alguma delas tiver que valer no banco, é uma linha por function.
8. **Busca "Contém":** usa `ilike`, que ignora maiúsculas mas não acentos. Para ignorar acentos, falta a extensão `unaccent`.
9. **Desfazer cadastro:** segue a P9, que encerra como Perdido (motivo `cadastro_desfeito`). A tela chama `core_encerrar_deal`.
10. **Score sem auditoria:** as tabelas `score_` não são auditadas linha a linha, porque a carga é em massa. Cada rodada fica registrada em `score_execucoes` e num evento `carga_score`.
