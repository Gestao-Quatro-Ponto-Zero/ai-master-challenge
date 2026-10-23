-- Usuários do painel e papéis por área (perfis das skills) + admin.
-- O login é feito pela API (código pessoal com hash PBKDF2); o banco guarda só o hash.

create table app.roles (
  role         text primary key,
  label        text not null,
  profile_slug text references app.analysis_profiles (slug),
  tabs         text[] not null,
  can_edit     boolean not null default false
);
comment on table app.roles is 'Papéis: quais abas do painel e qual perfil de análise cada área usa. Todos veem a visão geral.';

insert into app.roles (role, label, profile_slug, tabs, can_edit) values
  ('admin',      'Administrador',     null,         '{geral,risco,dados,ia}', true),
  ('executivo',  'Executivo (CEO)',   'executivo',  '{geral,risco,ia}',       false),
  ('financeiro', 'Financeiro',        'financeiro', '{geral,ia}',             false),
  ('cs',         'Customer Success',  'cs',         '{geral,risco,ia}',       false),
  ('suporte',    'Suporte',           'suporte',    '{geral,ia}',             false),
  ('produto',    'Produto',           'produto',    '{geral,ia}',             false),
  ('marketing',  'Marketing',         'marketing',  '{geral,ia}',             false),
  ('vendas',     'Vendas',            'vendas',     '{geral,risco,ia}',       false),
  ('dados',      'Dados',             'dados',      '{geral,dados,ia}',       true);

create table app.users (
  email      text primary key,
  name       text not null,
  role       text not null references app.roles (role),
  code_hash  text not null,
  active     boolean not null default true,
  created_at timestamptz not null default now(),
  last_login timestamptz
);
comment on table app.users is 'Usuários do painel; code_hash = pbkdf2_sha256$iter$salt$hash do código pessoal.';

alter table app.roles enable row level security;
alter table app.users enable row level security;
alter table app.ai_runs add column if not exists user_email text;
