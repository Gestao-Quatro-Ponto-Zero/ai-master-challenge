# Desenho: perfis, ações do vendedor e limpeza do pipeline

> Proposta para decisão. Nada disto está construído.
> Stack (decisão 11): Next.js com TypeScript strict, Postgres no Supabase G4_AI_Mastering e publicação na Vercel. Estrutura de pastas em [DESENHO-NEXT.md](DESENHO-NEXT.md).
> Identidade (decisão 12): sem login e sem senha. A pessoa escolhe o perfil (vendedor, manager ou admin) e, se for vendedor ou manager, o próprio nome.

## Perfis

| Perfil | Escolhe | Tela inicial | Enxerga | Pode registrar ação em |
|---|---|---|---|---|
| **Vendedor** | o nome, entre os 35 do dataset | Meu dia | o próprio pipeline | deals dele |
| **Manager** | o nome, entre os managers do dataset | Visão do time | o pipeline do time; abre o "Meu dia" de cada vendedor | deals do time |
| **Admin** | nada | Visão geral (todos os times) | tudo, com os filtros de região, manager e vendedor | qualquer deal |

- A escolha fica num cookie (`perfil` = papel + nome), gravado pela rota `POST /api/perfil` depois de conferir que o nome existe no dataset com aquele papel.
- O topo mostra quem está usando ("Anna Snelling, vendedora") e o botão **Trocar perfil**, que volta para a escolha.
- O perfil define as telas e os filtros: o vendedor não vê os filtros de região e manager; o manager só filtra entre os vendedores do time; o admin vê todos.
- Sem senha, o perfil organiza a tela e assina as ações, mas não protege nada: qualquer pessoa pode escolher qualquer perfil. Para uma demonstração, é suficiente. Para uso real, entraria o login com Supabase Auth sobre a mesma estrutura (tabela e rotas não mudam; só a origem do autor).

## Fluxo da escolha

```
/  ──►  "Quem é você?"  [Vendedor]  [Manager]  [Admin]
          │ Vendedor → lista dos vendedores, agrupada por manager (com a contagem de deals)
          │ Manager  → lista dos managers, com a região e o tamanho do time
          │ Admin    → entra direto
          ▼
        POST /api/perfil  → cookie  → tela inicial do perfil
```

Quem chega por um link direto sem perfil escolhido (ex.: `/time`) cai na escolha e, depois dela, volta ao link.

## O que o vendedor e o manager ganham

- No detalhe de cada deal: botões **Liguei**, **Requalifiquei**, **Desisti** (e **Desfazer**), com uma nota curta opcional.
- Deal marcado como "Desisti" sai das listas do vendedor. O pipeline fica limpo, mas nada é apagado.
- Visão do manager: quantos deals o score sugeriu encerrar e quantos o time confirmou, e quem não registra nenhuma ação há dias.
- Tela "Limpeza do pipeline": a lista de deals que o score marca como `desistir`, com confirmação em lote ("Confirmar desistência dos 43"). Cada confirmação vira um registro. O vendedor vê os dele, o manager os do time e o admin todos.

## Dois modos de leitura (o Leandro ainda confirma o modo banco)

| Modo | Quando | De onde vêm deals e notas | Ações |
|---|---|---|---|
| **Banco** | Credenciais presentes e banco respondendo em até 3 s | `core_*` + `score_*` da execução de score ativa | Leitura e gravação em `acao_registros` |
| **Arquivo** (reserva) | Sem credenciais, banco fora, projeto pausado ou tempo esgotado | `deals_scored.json` (a cópia dentro do app; sem ela, o exemplo) | Só leitura: os botões somem e uma linha discreta avisa "Registro de ações indisponível" |

- O app escolhe o modo a cada carregamento do servidor. Se o banco falha no meio do caminho, a página cai no arquivo em vez de dar erro.
- O rodapé mostra a fonte em uso: "Dados: banco, notas de 31/12/2017" ou "Dados: arquivo".
- A escolha de perfil funciona nos dois modos: a lista de nomes vem de `core_vendedores` e `core_managers` ou, no modo arquivo, do próprio JSON.
- **Quem escreve o quê:** o pipeline em Python (dados e score) carrega `core_*` e `score_*`, e o app só lê essas tabelas. O app só grava em `acao_registros` e `system_eventos`. Assim o `deals_scored.json` continua sendo o contrato, e o banco é uma cópia dele mais as ações.

## Banco (DB-01 prefixos por domínio, DB-02 chaves estrangeiras)

Projeto Supabase **G4_AI_Mastering**, usado só para este desafio. Regras aplicadas em todas as tabelas:
- nome com prefixo, em snake_case e no plural;
- toda chave estrangeira declarada, com índice próprio e `on delete restrict`;
- RLS ligado sem política: só a service role, no servidor, acessa.

### Mapa das chaves

```
core_escritorios ◄── core_managers ◄── core_vendedores ◄── core_deals ──► core_produtos
                                                               │
                                       core_contas ◄───────────┘   (core_contas.empresa_mae → core_contas)

score_execucoes ◄── score_deals ──► core_deals
                        ▲   ▲
        score_componentes   score_motivos

acao_registros ──► core_deals, core_vendedores (dono), score_execucoes (nota vista na hora),
                   core_vendedores / core_managers (autor)

config_parametros        system_eventos        (sem chaves estrangeiras)
```

### Tabelas

```sql
-- core_: dados do CRM (carregados pelo pipeline em Python; o app só lê)
create table core_escritorios (
  nome text primary key                                  -- Central, East, West
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

create table core_deals (
  opportunity_id text primary key,
  vendedor_nome  text not null references core_vendedores(nome) on delete restrict,
  produto_nome   text not null references core_produtos(nome) on delete restrict,
  conta_nome     text references core_contas(nome) on delete restrict,   -- nulo: deal sem empresa
  estagio        text not null check (estagio in ('Prospecting','Engaging','Won','Lost')),
  engage_date    date,
  close_date     date,
  close_value    numeric(12,2)
);
create index on core_deals (vendedor_nome);
create index on core_deals (produto_nome);
create index on core_deals (conta_nome);

-- score_: notas, componentes e motivos (uma execução por rodada do score)
create table score_execucoes (
  id             bigint generated always as identity primary key,
  reference_date date not null,
  gerado_em      timestamptz not null,
  versao         text not null,                         -- versão das regras do score
  pesos          jsonb not null,                        -- component_weights
  arquivo_sha256 text not null unique                   -- o deals_scored.json carregado
);

create table score_deals (
  execucao_id      bigint not null references score_execucoes(id) on delete restrict,
  opportunity_id   text   not null references core_deals(opportunity_id) on delete restrict,
  score            int    not null check (score between 0 and 100),
  acao_sugerida    text   not null check (acao_sugerida in ('focar','requalificar','desistir')),
  dias_no_pipeline int,
  valor_esperado   numeric(12,2) not null,
  marcadores       text[] not null default '{}',        -- esfriando, sem_conta, sem_data
  primary key (execucao_id, opportunity_id)
);
create index on score_deals (execucao_id);
create index on score_deals (opportunity_id);

create table score_componentes (
  execucao_id    bigint not null,
  opportunity_id text   not null,
  componente     text   not null,                       -- chance, valor, tempo, conta (ou os nomes finais)
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

-- config_: parâmetros do app (os perfis vêm de core_vendedores e core_managers; admin não precisa de tabela)
create table config_parametros (
  chave         text primary key,                       -- execucao_ativa, acoes_desde, limite_por_minuto
  valor         jsonb not null,
  atualizado_em timestamptz not null default now()
);

-- acao_: o que o vendedor, o manager ou o admin registra (só acrescenta; nunca apaga nem edita)
create table acao_registros (
  id             bigint generated always as identity primary key,
  opportunity_id text not null references core_deals(opportunity_id) on delete restrict,
  vendedor_nome  text not null references core_vendedores(nome) on delete restrict,  -- dono do deal na hora
  execucao_id    bigint references score_execucoes(id) on delete restrict,           -- nota que estava na tela
  acao           text not null check (acao in ('liguei','requalifiquei','desisti','desfazer')),
  nota           text check (char_length(nota) <= 280),
  autor_papel    text not null check (autor_papel in ('vendedor','manager','admin')),
  autor_vendedor text references core_vendedores(nome) on delete restrict,
  autor_manager  text references core_managers(nome) on delete restrict,
  criado_em      timestamptz not null default now(),
  check (
    (autor_papel = 'vendedor' and autor_vendedor is not null and autor_manager is null) or
    (autor_papel = 'manager'  and autor_manager  is not null and autor_vendedor is null) or
    (autor_papel = 'admin'    and autor_vendedor is null     and autor_manager  is null)
  )
);
create index on acao_registros (opportunity_id, criado_em desc);
create index on acao_registros (vendedor_nome);
create index on acao_registros (execucao_id);
create index on acao_registros (autor_vendedor, criado_em desc);
create index on acao_registros (autor_manager, criado_em desc);

-- system_: auditoria e logs
create table system_eventos (
  id        bigint generated always as identity primary key,
  tipo      text not null,          -- carga_score, gravacao_recusada, banco_indisponivel
  detalhe   jsonb not null default '{}',
  criado_em timestamptz not null default now()
);
create index on system_eventos (tipo, criado_em desc);

-- RLS ligado sem política em todas: só a service role acessa
```

- **Autor com chave estrangeira:** em vez de um nome solto, há duas colunas (`autor_vendedor`, `autor_manager`), cada uma com FK, e um `check` que amarra cada uma ao papel. O admin não tem nome.
- **Estado atual de um deal:** a última linha dele em `acao_registros`. "Desfazer" é um registro novo, não uma remoção. Uma view `acao_estados_atuais` entrega isso pronto.
- **Nota em uso:** a execução apontada por `config_parametros.execucao_ativa`. Uma rodada nova de score cria outra execução e só depois troca o ponteiro, sem apagar a anterior. Com `acao_registros.execucao_id`, dá para comparar a ação sugerida com o que a pessoa fez.
- **Limite de gravações:** contado direto em `acao_registros` (último minuto, por autor), sem tabela própria. O teto fica em `config_parametros.limite_por_minuto`.
- **Auditoria:** gravações recusadas (403), cargas de score e quedas para o modo arquivo vão para `system_eventos`.
- **"Zerar" a demonstração:** as telas mostram só as ações a partir de `config_parametros.acoes_desde`. Nada é apagado.
- **Migrações:** um arquivo por domínio (`0001_core.sql`, `0002_score.sql`, `0003_config_system.sql`, `0004_acao.sql`), num só lugar. Proposta: `solution/app/supabase/migrations/`.

## Rotas de API do Next

| Rota | O que faz | Sem credenciais do banco |
|---|---|---|
| `POST /api/perfil` | `{papel, nome?}`: confere o nome (banco ou JSON) e grava o cookie | funciona |
| `DELETE /api/perfil` | Trocar perfil (apaga só o cookie) | funciona |
| `GET /api/acoes` | Última ação de cada deal visível para o perfil | `503 {"disponivel": false}` |
| `POST /api/acoes` | Registra uma ação `{opportunity_id, acao, nota?}`; aceita lote para a limpeza | `503` |

Como a gravação é conferida, em `src/server/acoes.ts`:
1. Lê o perfil do cookie. Sem perfil, responde 401.
2. Confere que o nome existe no dataset com aquele papel (o cookie pode ter sido editado). Se não, 403.
3. Confere que cada deal do pedido pertence ao pipeline do perfil: vendedor → `deal.sales_agent == nome`; manager → `deal.manager == nome`; admin → qualquer deal aberto do arquivo. Se algum falhar, responde 403 e não grava nada do lote.
4. Confere o limite (`limite_por_minuto`, padrão 30, contado em `acao_registros`, o que vale entre as instâncias da Vercel) e o tamanho da nota. Recusas vão para `system_eventos`.
5. Grava em `acao_registros` com a service role, com o papel e o autor vindos do perfil e a `execucao_id` da nota em uso.

Os passos 2, 3 e a regra do limite são funções puras em `src/lib/permissao.ts`, testadas sem banco.

**Onde ficam as chaves:** só `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY`, ambas usadas apenas em `src/server/` (`import "server-only"`; o build falha se um componente do navegador importar um desses arquivos). Não há variável pública: sem login, o navegador não fala com o Supabase. Localmente as chaves ficam em `.env.local` na pasta do app (fora do git; há um `.env.example` com os nomes); na Vercel, nas variáveis de ambiente do projeto.

## Riscos

- **Qualquer um grava como qualquer um.** É aceito para a demonstração. Há duas contenções: o limite por minuto e a regra de pipeline (um vendedor escolhido só grava nos deals dele).
- **Sujeira da demonstração** (avaliadores clicando): sem DELETE. As telas mostram só as ações a partir de `config_parametros.acoes_desde`. Para "zerar" a demonstração, basta avançar a data.
- **Plano gratuito do Supabase pausa após 7 dias sem uso:** o app cai no modo só leitura e avisa. Antes de enviar a entrega, conferir se o projeto está ativo.

## Na tela (mudanças previstas)

- O detalhe do deal ganha os botões e a última ação ("Anna ligou em 12/11").
- Os cartões e as listas mostram um selo com a última ação. Os deals com "Desisti" ficam numa seção recolhida "Encerrados".
- Ao gravar, a tela mostra "Ação registrada" na hora. Se a gravação falhar, o botão volta e aparece "Não foi possível registrar. Tente de novo."

## Decisões em aberto

1. Confirmar o modo banco (deals e notas no banco, JSON como reserva).
2. Quem carrega `core_*` e `score_*`. Proposta: um script em Python do pipeline (`scoring/carregar_banco.py`), já que é ele que tem os dados em mãos. O app não escreve nessas tabelas.
3. Onde ficam as migrações (proposta: `solution/app/supabase/migrations/`).
4. O admin registra ações em qualquer deal (proposta) ou só lê?
5. Junto com o score: se "Liguei" mexe no score e se a limpeza fica com os três perfis (proposta) ou só com manager e admin.
