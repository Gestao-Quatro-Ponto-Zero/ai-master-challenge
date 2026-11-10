# Desenho: usuários, operação do pipeline e auditoria

> Proposta para decisão. Nada disto está construído.
> Estrutura de pastas do app em [DESENHO-NEXT.md](DESENHO-NEXT.md).

Decisões do Leandro que este desenho segue:

| # | Decisão |
|---|---|
| 11 | Next.js com TypeScript strict, Postgres no Supabase G4_AI_Mastering e Vercel. Análise e score seguem em Python. |
| 12 | Sem login e sem senha: a pessoa escolhe o próprio usuário. |
| 14 | DB-01 (prefixo por domínio, snake_case, plural) e DB-02 (chave estrangeira declarada, com índice, `on delete restrict`). |
| 15 | Tabela `config_usuarios` gerada do dataset: vendedores, managers e um admin. Sem checagem de nome. |
| 16 | Sistema operacional: insert e update liberados. DELETE, DROP e exclusão em massa continuam proibidos. Toda escrita é auditada (ARQ-05). O servidor não bloqueia por dono do deal. |

## O que cada pessoa faz

| Usuário | Tela inicial | Enxerga | Pode fazer |
|---|---|---|---|
| **Vendedor** | Meu dia | o próprio pipeline | registrar ação (Liguei, Requalifiquei, Desisti), avançar o estágio, preencher a empresa do deal, encerrar como ganho ou perdido, desfazer a própria ação |
| **Manager** | Visão do time | o pipeline do time; abre o "Meu dia" de cada vendedor | o mesmo, nos deals do time, e a limpeza em lote do time |
| **Admin** | Visão geral | tudo, com filtros de região, manager e vendedor | o mesmo, em qualquer deal, e a limpeza em lote geral |

- A tela mostra só o que é de cada usuário. O servidor não bloqueia por dono (decisão 16): quem escolhe um usuário age como ele.
- "Limpeza do pipeline": a lista de deals que o score marca como `desistir`, com encerramento em lote como perdido (até 100 por vez, com confirmação que mostra a quantidade). Cada deal encerrado é um update auditado. Nada é apagado.

## Escolha do usuário (decisão 15)

```
/  ──►  "Quem é você?"  [Vendedor]  [Manager]  [Admin]
          │ Vendedor → vendedores de config_usuarios, agrupados por manager (com a contagem de deals abertos)
          │ Manager  → managers, com a região e o tamanho do time
          │ Admin    → entra direto
          ▼
        POST /api/perfil {usuario_id}  → cookie  → tela inicial do usuário
```

- A lista vem de `config_usuarios`. No modo reserva (sem banco), a mesma lista é montada a partir do JSON, com os mesmos ids.
- O cookie guarda só o `usuario_id`. O servidor lê o usuário pela chave (se a chave não existir ou estiver inativa, volta para a escolha). Não há mais a conferência "o nome existe no dataset".
- O topo mostra quem está usando ("Anna Snelling, vendedora") e **Trocar perfil**.
- Quem chega por um link sem usuário escolhido passa pela escolha e volta ao link.

## Fonte principal: o banco (o Leandro ainda confirma)

| Modo | Quando | Leitura | Escrita |
|---|---|---|---|
| **Banco** (principal) | Credenciais presentes e banco respondendo em até 3 s | `core_*`, `score_*`, `acao_*`, `config_*` | Liberada, com auditoria |
| **Reserva** | Sem credenciais, banco fora, projeto pausado ou tempo esgotado | `deals_scored.json` (a cópia no app; sem ela, o exemplo) | Nenhuma: os botões somem e uma linha discreta avisa "Modo somente leitura: banco indisponível" |

- O app decide o modo a cada carregamento do servidor. Se o banco falha no meio do caminho, a página cai na reserva em vez de dar erro.
- O rodapé mostra a fonte: "Dados: banco, notas de 31/12/2017" ou "Dados: arquivo (somente leitura)".

**Quem escreve o quê:**
- **Carga inicial (Python, uma vez):** cria `core_*` a partir dos CSVs limpos, `config_usuarios` a partir do `sales_teams` e a primeira execução de `score_*`. A carga usa `on conflict do nothing` em `core_*`: rodar de novo nunca sobrescreve o que foi editado no app.
- **Operação (app):** depois da carga, o banco é a fonte da verdade de `core_deals`. O app atualiza estágio, empresa e fechamento, e grava em `acao_registros`.
- **Nova rodada de score (Python):** lê `core_*` do banco, não dos CSVs, para considerar o que os vendedores mudaram. Grava uma nova `score_execucoes` e troca o ponteiro em `config_parametros`.
- Um deal alterado depois da última rodada de score mostra o selo "Atualizado depois da nota" até a próxima rodada.

## Banco

Projeto **G4_AI_Mastering**. Em todas as tabelas:
- prefixo de domínio, snake_case e plural (DB-01);
- toda chave estrangeira declarada, com índice próprio e `on delete restrict` (DB-02);
- RLS ligado sem política, para que só a service role, no servidor, acesse.

### Quem aponta para quem

| Tabela | Chaves estrangeiras |
|---|---|
| `core_managers` | → `core_escritorios` |
| `core_vendedores` | → `core_managers` |
| `core_contas` | → `core_contas` (empresa-mãe) |
| `core_deals` | → `core_vendedores`, `core_produtos`, `core_contas`, `config_usuarios` (quem atualizou por último) |
| `config_usuarios` | → `core_vendedores`, `core_managers` |
| `score_deals` | → `score_execucoes`, `core_deals` |
| `score_componentes`, `score_motivos` | → `score_deals` |
| `acao_registros` | → `core_deals`, `config_usuarios` (autor e quem desfez), `score_execucoes` (nota vista na hora) |
| `system_auditoria` | → `config_usuarios` |
| `core_escritorios`, `core_produtos`, `score_execucoes`, `config_parametros`, `system_eventos` | nenhuma |

### Tabelas (15)

```sql
-- core_: dados do CRM
create table core_escritorios (
  nome text primary key                                   -- Central, East, West
);
create table core_managers (
  nome            text primary key,
  escritorio_nome text not null references core_escritorios(nome) on delete restrict
);
create index on core_managers (escritorio_nome);

create table core_vendedores (
  nome         text primary key,
  manager_nome text not null references core_managers(nome) on delete restrict
);
create index on core_vendedores (manager_nome);

create table core_produtos (
  nome  text primary key,
  serie text not null,
  preco numeric(12,2) not null
);

create table core_contas (
  nome             text primary key,
  setor            text,
  ano_fundacao     int,
  receita_milhoes  numeric(14,2),
  funcionarios     int,
  pais             text,
  empresa_mae_nome text references core_contas(nome) on delete restrict
);
create index on core_contas (empresa_mae_nome);

-- config_: usuários (decisão 15) e parâmetros
create table config_usuarios (
  id            bigint generated always as identity primary key,
  papel         text not null check (papel in ('vendedor','manager','admin','sistema')),
  nome_exibicao text not null,
  vendedor_nome text unique references core_vendedores(nome) on delete restrict,
  manager_nome  text unique references core_managers(nome) on delete restrict,
  ativo         boolean not null default true,
  check (
    (papel = 'vendedor' and vendedor_nome is not null and manager_nome is null) or
    (papel = 'manager'  and manager_nome  is not null and vendedor_nome is null) or
    (papel in ('admin','sistema') and vendedor_nome is null and manager_nome is null)
  )
);
create index on config_usuarios (vendedor_nome);
create index on config_usuarios (manager_nome);
-- carga: 35 vendedores + 6 managers do sales_teams, 1 admin e 1 usuário "sistema" (assina as cargas do Python)

create table config_parametros (
  chave         text primary key,                        -- execucao_ativa, acoes_desde, limite_por_minuto
  valor         jsonb not null,
  atualizado_em timestamptz not null default now()
);

create table core_deals (
  opportunity_id text primary key,
  vendedor_nome  text not null references core_vendedores(nome) on delete restrict,
  produto_nome   text not null references core_produtos(nome) on delete restrict,
  conta_nome     text references core_contas(nome) on delete restrict,    -- nulo: deal sem empresa
  estagio        text not null check (estagio in ('Prospecting','Engaging','Won','Lost')),
  engage_date    date,
  close_date     date,
  close_value    numeric(12,2),
  atualizado_em  timestamptz not null default now(),                      -- também serve de controle de versão
  atualizado_por bigint references config_usuarios(id) on delete restrict,
  check (estagio not in ('Won','Lost') or close_date is not null),
  check (estagio <> 'Won' or close_value > 0)
);
create index on core_deals (vendedor_nome);
create index on core_deals (produto_nome);
create index on core_deals (conta_nome);
create index on core_deals (atualizado_por);

-- score_: notas, componentes e motivos (uma execução por rodada; gravado só pelo Python)
create table score_execucoes (
  id             bigint generated always as identity primary key,
  reference_date date not null,
  gerado_em      timestamptz not null,
  versao         text not null,
  pesos          jsonb not null,
  arquivo_sha256 text not null unique
);

create table score_deals (
  execucao_id      bigint not null references score_execucoes(id) on delete restrict,
  opportunity_id   text   not null references core_deals(opportunity_id) on delete restrict,
  score            int    not null check (score between 0 and 100),
  acao_sugerida    text   not null check (acao_sugerida in ('focar','requalificar','desistir')),
  dias_no_pipeline int,
  valor_esperado   numeric(12,2) not null,
  marcadores       text[] not null default '{}',
  primary key (execucao_id, opportunity_id)
);
create index on score_deals (execucao_id);
create index on score_deals (opportunity_id);

create table score_componentes (
  execucao_id    bigint not null,
  opportunity_id text   not null,
  componente     text   not null,
  pontos         numeric(6,2) not null,
  primary key (execucao_id, opportunity_id, componente),
  foreign key (execucao_id, opportunity_id) references score_deals on delete restrict
);
create index on score_componentes (execucao_id, opportunity_id);

create table score_motivos (
  execucao_id    bigint not null,
  opportunity_id text   not null,
  ordem          smallint not null,
  texto          text   not null,
  primary key (execucao_id, opportunity_id, ordem),
  foreign key (execucao_id, opportunity_id) references score_deals on delete restrict
);
create index on score_motivos (execucao_id, opportunity_id);

-- acao_: o que a pessoa registra
create table acao_registros (
  id             bigint generated always as identity primary key,
  opportunity_id text   not null references core_deals(opportunity_id) on delete restrict,
  usuario_id     bigint not null references config_usuarios(id) on delete restrict,
  papel          text   not null,                                          -- papel na hora da ação
  execucao_id    bigint references score_execucoes(id) on delete restrict, -- nota que estava na tela
  acao           text   not null check (acao in ('liguei','requalifiquei','desisti')),
  nota           text   check (char_length(nota) <= 280),
  criado_em      timestamptz not null default now(),
  desfeita_em    timestamptz,                                              -- desfazer = update, não delete
  desfeita_por   bigint references config_usuarios(id) on delete restrict
);
create index on acao_registros (opportunity_id, criado_em desc);
create index on acao_registros (usuario_id, criado_em desc);
create index on acao_registros (execucao_id);
create index on acao_registros (desfeita_por);

-- system_: auditoria (ARQ-05) e eventos
create table system_auditoria (
  id             bigint generated always as identity primary key,
  tabela         text   not null,
  registro_id    text   not null,
  operacao       text   not null check (operacao in ('insert','update')),
  antes          jsonb,                                                    -- nulo no insert
  depois         jsonb  not null,
  usuario_id     bigint not null references config_usuarios(id) on delete restrict,
  papel          text   not null,
  correlation_id uuid   not null,
  criado_em      timestamptz not null default now()
);
create index on system_auditoria (usuario_id);
create index on system_auditoria (tabela, registro_id, criado_em desc);
create index on system_auditoria (correlation_id);

create table system_eventos (
  id             bigint generated always as identity primary key,
  tipo           text not null,          -- carga_score, conflito_versao, banco_indisponivel, lote_limpeza
  detalhe        jsonb not null default '{}',
  correlation_id uuid,
  criado_em      timestamptz not null default now()
);
create index on system_eventos (tipo, criado_em desc);
create index on system_eventos (correlation_id);
```

## Como a escrita funciona e por que a auditoria não pode ser pulada

Toda escrita passa por uma **função no banco**, chamada pelo servidor com `supabase.rpc(...)`. A função faz o trabalho dentro de uma transação. Um **gatilho** em cada tabela operacional grava a auditoria.

```
navegador ─► rota do Next (zod valida; gera correlation_id) ─► rpc('core_atualizar_deal', {...})
                                                                 │ set_config('app.usuario_id', ..., true)
                                                                 │ set_config('app.correlation_id', ..., true)
                                                                 │ update core_deals ...
                                                                 ▼
                                    gatilho system_auditar(): insert em system_auditoria (antes, depois,
                                    usuário, papel, momento, correlation_id)
```

| Função | Faz |
|---|---|
| `acao_registrar(usuario_id, correlation_id, opportunity_id, acao, nota)` | insert em `acao_registros` |
| `acao_desfazer(usuario_id, correlation_id, acao_id)` | update de `desfeita_em` / `desfeita_por` |
| `core_atualizar_deal(usuario_id, correlation_id, opportunity_id, versao, estagio?, conta_nome?)` | update de estágio e empresa |
| `core_encerrar_deal(usuario_id, correlation_id, opportunity_id, versao, resultado, close_value?)` | Won (com valor) ou Lost, com `close_date` = hoje |
| `core_encerrar_lote(usuario_id, correlation_id, opportunity_ids[])` | Lost em até 100 deals; um registro de auditoria por deal e um evento `lote_limpeza` |

- **Auditoria garantida:** o gatilho `system_auditar()` fica em `core_deals`, `core_contas`, `acao_registros`, `config_usuarios` e `config_parametros`. Se a escrita chegar sem `app.usuario_id` ou `app.correlation_id`, o gatilho recusa a operação. Não existe escrita sem auditoria, nem pelo app nem pela carga do Python (que assina como o usuário "sistema").
- **DELETE e TRUNCATE proibidos no próprio banco:** gatilho `before delete` que recusa em todas as tabelas, e `revoke delete, truncate` de `anon`, `authenticated` e `service_role`. O DROP fica fora do alcance do app, que não tem permissão de dono do schema.
- **Duas pessoas no mesmo deal:** a tela envia a `versao` (o `atualizado_em` que leu). Se o deal mudou no meio, a função recusa e a rota responde 409. A tela mostra "Este deal foi alterado por Cara Losch às 14:32. Recarregue para ver a versão atual.", e o caso vai para `system_eventos`.
- **Estágios aceitos:** Prospecting → Engaging → Won ou Lost. Reabrir um deal encerrado (Won/Lost → Engaging) fica com manager e admin. É regra de dado, não de dono.
- **correlation_id:** gerado pela rota a cada pedido. Volta no cabeçalho `x-correlation-id` e aparece nas mensagens de erro ("código para suporte: 3f2a…"), para achar a linha na auditoria.
- **Limite de abuso** (sem senha, qualquer um age como qualquer usuário): até `config_parametros.limite_por_minuto` escritas por usuário, contadas em `system_auditoria`.

## Rotas do Next

| Rota | Faz | Modo reserva |
|---|---|---|
| `POST /api/perfil` `{usuario_id}` / `DELETE /api/perfil` | escolhe / troca o usuário (cookie) | funciona (ids iguais aos do banco) |
| `POST /api/acoes` | `acao_registrar` | 503 |
| `PATCH /api/acoes/[id]` `{desfazer: true}` | `acao_desfazer` | 503 |
| `PATCH /api/deals/[id]` `{versao, estagio?, conta_nome?}` | `core_atualizar_deal` | 503 |
| `POST /api/deals/[id]/encerrar` `{versao, resultado, close_value?}` | `core_encerrar_deal` | 503 |
| `POST /api/limpeza` `{opportunity_ids}` | `core_encerrar_lote` | 503 |

A leitura não passa por rota de API: as páginas leem no servidor (`src/server/fonte.ts`).

**Onde ficam as chaves:** só `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY`, usadas apenas em `src/server/` (`import "server-only"`; o build falha se um componente do navegador importar um desses arquivos). O navegador nunca fala com o Supabase.

## Na tela (mudanças previstas)

- **Detalhe do deal:**
  - os botões de ação;
  - o estágio, com "Avançar para Em negociação";
  - a empresa, com busca entre as contas cadastradas;
  - "Encerrar: ganho" (pede o valor) e "Encerrar: perdido";
  - o histórico do deal, lido da auditoria ("Anna mudou o estágio para Em negociação em 12/11 às 9:14").
- **Cartões e listas:** selo com a última ação. Os deals encerrados saem das listas de foco e vão para "Encerrados" (recolhido).
- **Retorno:** ao gravar, a tela mostra o resultado na hora ("Ação registrada", "Deal encerrado como perdido"). Se falhar, o controle volta ao estado anterior e a mensagem diz o que fazer, com o código para suporte.

## Riscos

- **Qualquer um age como qualquer usuário** (decisão 12). A auditoria mostra qual usuário foi escolhido em cada escrita, e o limite por minuto segura abuso automático.
- **Sujeira da demonstração** (avaliadores mexendo):
  - nada é apagado;
  - a data de corte `acoes_desde` esconde as ações antigas;
  - cada encerramento fica na auditoria com o "antes" e pode ser revertido por update, deal a deal.
- **Plano gratuito do Supabase pausa após 7 dias sem uso:** o app cai na reserva somente leitura e avisa. Antes de enviar a entrega, conferir se o projeto está ativo.

## Decisões em aberto

1. Confirmar o banco como fonte principal, com o JSON como reserva somente leitura.
2. Carga e rodadas de score em Python lendo do banco (`scoring/carregar_banco.py`, dono #3), com `on conflict do nothing` em `core_*`.
3. Se o vendedor pode criar empresa nova ao preencher a conta do deal, ou só escolher entre as 85 existentes (proposta: só escolher).
4. Se reabrir deal encerrado fica só com manager e admin (proposta acima).
5. Onde ficam as migrações (proposta: `solution/app/supabase/migrations/`).
6. Junto com o score: se "Liguei" e as mudanças de estágio entram na próxima rodada de score.
