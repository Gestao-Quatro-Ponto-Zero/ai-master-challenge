-- Lead Scorer — esquema do banco (Postgres / Supabase)
-- Tabelas espelham os 4 CSVs do CRM, já limpos por scripts/preparar_dados.py.

create table if not exists public.products (
  product      text primary key,
  series       text not null,
  sales_price  numeric(12,2) not null check (sales_price > 0)
);

create table if not exists public.sales_teams (
  sales_agent      text primary key,
  manager          text not null,
  regional_office  text not null
);

create table if not exists public.accounts (
  account           text primary key,
  sector            text,
  year_established  int,
  revenue           numeric(14,2),   -- receita anual em US$ milhões
  employees         int,
  office_location   text,
  subsidiary_of     text
);

create table if not exists public.sales_pipeline (
  opportunity_id  text primary key,
  sales_agent     text not null references public.sales_teams (sales_agent),
  product         text not null references public.products (product),
  account         text references public.accounts (account),   -- 1.425 deals abertos vêm sem conta
  deal_stage      text not null check (deal_stage in ('Prospecting', 'Engaging', 'Won', 'Lost')),
  engage_date     date,
  close_date      date,
  close_value     numeric(12,2)
);
create index if not exists sales_pipeline_stage_idx on public.sales_pipeline (deal_stage);
create index if not exists sales_pipeline_agent_idx on public.sales_pipeline (sales_agent);

-- Parâmetros do score, editáveis sem mexer em código.
--   data_referencia : o "hoje" do snapshot (última data do CRM)
--   ciclo_max_dias  : maior ciclo já observado entre deals fechados (nenhum fechou depois disso)
--   fase_risco_dias : janela em que as perdas se concentram
--   reta_final_dias : percentil 90 do ciclo; a partir daqui o prazo histórico está acabando
create table if not exists public.parametros (
  id               int primary key default 1 check (id = 1),
  data_referencia  date not null,
  ciclo_max_dias   int  not null,
  fase_risco_dias  int  not null,
  reta_final_dias  int  not null,
  amostra_minima   int  not null default 100   -- n mínimo para confiar na curva de chance
);
insert into public.parametros (id, data_referencia, ciclo_max_dias, fase_risco_dias, reta_final_dias, amostra_minima)
values (1, '2017-12-31', 138, 14, 104, 100)
on conflict (id) do nothing;

-- Leitura pública (dataset público, app sem login). Escrita só pelo dono do banco.
alter table public.products        enable row level security;
alter table public.sales_teams     enable row level security;
alter table public.accounts        enable row level security;
alter table public.sales_pipeline  enable row level security;
alter table public.parametros      enable row level security;

create policy "leitura publica" on public.products       for select to anon, authenticated using (true);
create policy "leitura publica" on public.sales_teams    for select to anon, authenticated using (true);
create policy "leitura publica" on public.accounts       for select to anon, authenticated using (true);
create policy "leitura publica" on public.sales_pipeline for select to anon, authenticated using (true);
create policy "leitura publica" on public.parametros     for select to anon, authenticated using (true);
