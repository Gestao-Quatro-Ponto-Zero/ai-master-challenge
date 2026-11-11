# Banco do CRM: migrations

Migrations do Postgres (Supabase). Elas saem de `app/ESPEC-TELAS.md` (seção 8), `app/DESENHO-ACOES.md` e `app/DESENHO-CRM.md`, e seguem as premissas de arquitetura, banco de dados e back-end do projeto.

## Estado

Todas as migrations (`0001` a `0034`) e o seed estão **aplicados** no Supabase. A última, `0034_relogio_e_rotina.sql`, foi aplicada em 10/11/2026 (sha256 `ed2065bd…`). Nenhum arquivo aplicado é alterado: mudança nova entra como migration nova.

| Parte | Arquivos | Estado |
|---|---|---|
| Lote 1 | `migrations/0001`–`0006` + `seed/seed_dataset.sql` | aplicado em 10/11/2026: 9 tabelas, 8.800 deals, 85 contas, 43 usuários e 9.006 linhas de auditoria |
| Lote 2 | `migrations/0007`–`0025` | aplicado |
| Teto global | `migrations/0026_limite_global.sql` | aplicado (sha256 `ea36c7b6…443a`) |
| Teto exato | `migrations/0027_limite_exato.sql` | aplicado |
| Contexto obrigatório | `migrations/0028_contexto_obrigatorio.sql` | aplicado (corrige um achado da revisão de segurança do lote 2) |
| Reforço do contexto | `migrations/0029_reforco_contexto.sql` | aplicado |
| Prioridades pela nota | `migrations/0030_prioridades_pela_nota.sql` | aplicado |
| Funil com 5 etapas | `migrations/0031_funil_cinco_etapas.sql` | aplicado |
| 20 prioridades por dia | `migrations/0032_meta_prioridades_20.sql` | aplicado |
| Redistribuição de domingo | `migrations/0033_redistribuicao_de_domingo.sql` | aplicado |
| Relógio e rotina diária | `migrations/0034_relogio_e_rotina.sql` | aplicado em 10/11/2026 (sha256 `ed2065bd…`) |

Cada migration nova foi validada antes de aplicar, num Postgres em memória (PGlite), com e sem o dataset (`validar_tudo.mjs` e `validar_00NN.mjs`).

**Histórico da 0026:** ela foi aplicada antes de um ajuste pedido pela revisão de segurança. A versão aplicada contava o pedido atual e usava `>`, o que deixava passar um pedido a mais que o teto. O arquivo `0026` no repositório é exatamente o que está no banco. O ajuste (contar só os pedidos anteriores e usar `>=`, para o teto ficar exato) entrou como `0027`, que substitui a função `system_iniciar_contexto`.

## Ordem de execução do lote 2 em diante

Cada arquivo numa transação, rodado pelo dono do schema (`postgres`), na ordem. Todos já estão aplicados no Supabase.

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
| 17 | `0023_atividades.sql` | tipo de atividade e comentário obrigatórios no ✓ |
| 18 | `0024_roteamento_repasse.sql` | roteamento sem teto, repasse e penalidade |
| 19 | `0025_permissoes_e_guardas.sql` | proteções das tabelas novas, política do papel de carga e permissões finais |
| 20 | `0026_limite_global.sql` | **teto global** de pedidos do app por janela (soma de todos os usuários); o papel de carga fica fora |
| 21 | `0027_limite_exato.sql` | tetos exatos (no máximo 30 por usuário e 300 no total por janela); limite por IP nas rotas do app é obrigatório |
| 22 | `0028_contexto_obrigatorio.sql` | o app só grava com o pedido registrado em `system_correlacoes` (mesma transação e mesmo usuário); o registro passa por um gatilho que preenche a origem e confere os limites |
| 23 | `0029_reforco_contexto.sql` | recusa usuário inativo na auditoria e no registro; só as funções inserem na auditoria, nos eventos e nos pedidos (`SECURITY DEFINER`); o app só lê as notas (`score_*`) |
| 24 | `0030_prioridades_pela_nota.sql` | Prioridades do dia pela nota para todos os papéis (atendimento atrasado > lead novo com FIT ≥ 75 > nota > HEAT > código, sem valor esperado); a lista guarda a execução usada e, se a execução ativa muda, os itens não marcados são substituídos (`substituida_em`, sem DELETE) e repostos; filtro do manager e do admin no parâmetro `prioridades_gestor`; super hot sem critério de ticket |
| 25 | `0031_funil_cinco_etapas.sql` | "Ganho" vira "Fechado" no rótulo; ação `contato` (registro de atendimento com tipo e comentário obrigatórios, `acao_registrar_contato`); linha do tempo com o atendimento |
| 26 | `0032_meta_prioridades_20.sql` | meta do dia = 20; a lista guarda a meta usada (`meta_dia`) e as listas de hoje com meta menor se completam na próxima abertura |
| 27 | `0033_redistribuicao_de_domingo.sql` | `core_repassar_deal`: as travas do repasse (FIT mínimo, no máximo 3 abaixo do dono, top N) valem só para `repasse_janela`; a redistribuição de domingo é só equilíbrio (deal aberto, sem contato registrado, destino ativo e diferente do dono, motivo "Redistribuição de domingo.", sem penalidade); a linha do tempo mostra os repasses automáticos com o motivo |
| 28 | `0034_relogio_e_rotina.sql` | relógio que anda (âncoras em `config_parametros`; `system_data_negocio()` = âncora de negócio + dias reais desde a âncora real); papel de login `g4_rotina` (sem senha no arquivo, membro só de `system_carga`); `system_rotina_ja_rodou(dia)` para a rotina diária não rodar duas vezes. Depois de aplicar, ver "Banco novo" |

## Banco novo

Para montar o banco do zero (por exemplo, num projeto Supabase novo):

1. **Ordem:** `migrations/0001` a `0006`, depois `seed/seed_dataset.sql`, depois `0007` a `0034`. Cada arquivo numa transação, rodado pelo dono do schema (`postgres`).
2. **Senha do `g4_rotina`:** a `0034` cria o papel de login da rotina diária sem senha. Defina a senha fora do git, direto no banco: `alter role g4_rotina password '…';`.
3. **Segredos do app na Vercel:**
   - `DATABASE_URL_ROTINA`: a URL de conexão com o usuário `g4_rotina`.
   - `CRON_SECRET`: o segredo que o cron da Vercel manda às rotas da rotina.
   - Também `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY`, para as telas.
4. **Datas de simulação** (em `config_parametros`): o dataset termina em 31/12/2017, então o banco simula o tempo.
   - `modo_demonstracao` = `true` liga a simulação.
   - `data_ancora_real` e `data_ancora_negocio` fazem a data de negócio andar 1 dia por dia real: no dia real `data_ancora_real`, a data de negócio é `data_ancora_negocio`. Hoje: 10/11/2026 = 31/12/2017.
   - Sem as âncoras, com a simulação ligada, a data fica parada em `data_referencia`.
   - **Em produção, com dados reais:** remova as datas ancoradas (`data_ancora_real` e `data_ancora_negocio` sem valor) e desligue `modo_demonstracao` (`false`). A data de negócio passa a ser o dia real.

## Segurança

**Papel de carga (`system_carga`).** É um papel de banco separado do papel do app (`service_role`).
- Só ele age como o usuário "sistema": `system_iniciar_contexto_sistema`, `score_ativar_execucao`, `config_gerar_usuarios` e `core_repassar_deal`.
- O app não executa essas funções.
- O app também não consegue escolher o usuário "sistema" nem gravar como ele: o contexto e a auditoria recusam (`GS403`).
- As cargas usam conexão direta, como dono: `set role system_carga;` e depois `select system_iniciar_contexto_sistema('<uuid novo>');`, numa transação.
- O papel de carga tem uma política de RLS só para ele. Não há política para `anon`, `authenticated` ou `service_role`.

**Contexto obrigatório (`0028`).** O app não grava ajustando `app.usuario_id` e `app.correlation_id` à mão.
- Para os papéis do app, a auditoria e os eventos só aceitam o pedido registrado em `system_correlacoes`, na mesma transação e com o mesmo usuário. Fora disso, a gravação é recusada com `GS401`.
- O registro é conferido por gatilho: a origem (app ou carga), a transação e o horário são preenchidos pelo banco. Os limites e a recusa do usuário "sistema" valem até para um registro gravado direto na tabela.
- O papel de carga e o dono seguem o caminho próprio, sem limites.

**Só as funções gravam os registros de controle (`0029`).**
- `system_auditoria`, `system_eventos` e `system_correlacoes` não aceitam INSERT nem UPDATE direto de `service_role`, `anon`, `authenticated` ou `system_carga`. Só as funções gravam nelas: `system_iniciar_contexto`, `system_iniciar_contexto_sistema`, `system_auditar` e `system_registrar_evento`, que agora rodam como dono (`SECURITY DEFINER`, com `search_path` fixo). Nem o app nem a carga forjam uma linha de auditoria.
- Usuário inexistente ou inativo é recusado (`GS401`) também na auditoria e no registro do pedido.
- Para reconhecer o app dentro dessas funções, o banco olha também o papel ativo da sessão (`SET ROLE`). No Supabase, a API entra como `authenticator` e assume `service_role` por `SET ROLE`.
- **O app só lê as notas.** `service_role` tem só SELECT nas 6 tabelas `score_*`; quem grava é a carga do score, pelo papel `system_carga`.

**`correlation_id`.**
- Gerado pelo servidor (na rota, com `crypto.randomUUID()`), nunca aceito do cliente.
- O banco registra cada um em `system_correlacoes`, com a transação. Reaproveitar um `correlation_id` em outra transação é recusado (`GS400`).

**Limites de escrita.** Os dois são contados pelo banco em `system_correlacoes`, na janela `janela_limite_segundos` (60). Valem sempre para o app, que não consegue desligá-los; o papel de carga fica fora dos dois.

| Limite | Conta | Padrão | Erro |
|---|---|---|---|
| por usuário | pedidos daquele usuário | no máximo 30 por janela; o 31º é recusado | `GS429`: "Muitas mudanças seguidas. Espere alguns segundos." |
| global (`0026`, exato desde a `0027`) | pedidos de todos os usuários do app somados | no máximo 300 por janela (`limite_global_escritas`); o 301º é recusado | `GS429`: "O sistema está recebendo muitas mudanças agora. Tente de novo em alguns segundos." |

**Limite por endereço de rede (IP): obrigatório.** Ele fica nas rotas do app, que é onde se conhece o IP, e vem **antes** do banco. É o controle principal contra abuso.
- O teto global do banco é rede de segurança: protege o banco.
- Se o limite por IP faltar, uma só origem pode esgotar o teto global e travar as escritas de todos os usuários até a janela passar.

**Limitação que continua: não há login (decisão de projeto do desafio).** Qualquer pessoa escolhe qualquer usuário da tela, **inclusive o admin**, e age como ele.
- **Sem login, o limite por usuário só organiza o uso:** quem quiser abusar troca de usuário.
- **Proteção contra abuso, em ordem:**
  1. limite por IP nas rotas do app (obrigatório);
  2. teto global no banco (`0026`).
- A auditoria registra qual usuário foi escolhido em cada escrita.
- Para uso real, seria preciso login.

## Regras de negócio no banco (números em `config_parametros`)

- **✓ nas Prioridades do dia:**
  - exige tipo de atividade (`config_tipos_atividade`: Ligação, E-mail, Mensagem, Reunião, Proposta enviada, Requalificado, Sem resposta) e comentário (até 280 caracteres);
  - grava em `acao_registros`, com o item da lista do dia e o horário real (`criado_em`), e atualiza o último contato;
  - o ✗ continua sem registro obrigatório;
  - a assinatura antiga de `acao_marcar_prioridade` (sem tipo) ainda aceita o ✗ e recusa o ✓.
- **Roteamento:**
  - sem teto de abertos;
  - lead novo vai ao vendedor de maior FIT no cohort, menos a penalidade ativa, com o mínimo de casos;
  - a redistribuição de domingo (equilíbrio entre os vendedores ativos) é planejada pela rotina diária do app (`app/src/server/motor`) e gravada pelo papel de carga, por `core_repassar_deal`.
- **Repasse (`core_repassar_deal`, só o papel de carga):**
  - no repasse por mudança de faixa (`repasse_janela`): só com o FIT do novo vendedor ≥ 75, no máximo 3 pontos abaixo do FIT do dono, e o lead no top 5 do novo;
  - na redistribuição de domingo: só equilíbrio, sem essas travas e sem penalidade;
  - nos dois, o lead tem de estar aberto e sem contato registrado;
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
- **Testes de uso: 86 verificações.**
  - Com a 0029: INSERT direto nas três tabelas de controle é recusado (app e carga); usuário inativo é recusado; o app não grava notas, mas continua lendo; a carga grava e ativa a execução de score.
  - Com a 0026: o teto global recusa o app mesmo trocando de usuário, e o papel de carga passa.
  - Com a 0028: o atalho direto é recusado, tanto na gravação quanto no evento; um registro forjado na tabela continua barrado pelo limite; o caminho normal do app e a carga são aceitos.
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


## Pendências

- **Trava do dono pelo manager:** o manager poderia travar o dono de um lead para que ele não seja repassado nem redistribuído. Ainda não existe no banco nem na tela, e hoje ninguém trava nada; a 0033 não trata disso. Quando for feita, `core_repassar_deal` precisa recusar o lead travado nas duas origens.