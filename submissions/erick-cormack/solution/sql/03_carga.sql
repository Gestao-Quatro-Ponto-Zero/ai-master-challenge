-- Lead Scorer — carga dos dados direto do GitHub, dentro do banco (Supabase / Lovable Cloud).
-- Usa a extensão pg_net (assíncrona): o PASSO 1 dispara os downloads; o PASSO 2, rodado
-- alguns segundos depois, confere e insere. Alternativa offline: rodar sql/seed/*.sql em ordem.
--
-- Fonte: dataset "CRM Sales Opportunities" (Maven Analytics; no Kaggle como
-- "CRM Sales Predictive Analytics", licença CC0), espelho público fixado num commit.
-- MD5 esperados (idênticos aos arquivos usados no notebook):
--   products.csv       d9de5a7bf21ae8a7c2d1d9fb96260ddd
--   sales_teams.csv    a0f2389b400aa58368df7ebac22d2eb1
--   accounts.csv       798e794104e6d492d5d91b7588d97498
--   sales_pipeline.csv 06d7d6aedb7c0ed7bf77093565688d03

-- ===================== PASSO 1: disparar downloads =====================
create extension if not exists pg_net;

select arq, net.http_get(
  'https://raw.githubusercontent.com/Dargoul-Ayoub/CRM-Sales-Opportunities-Maven-Sales-Challenge/4db65244196b63f8831dbb0c385496a1ed5c235b/CSV%20Files/' || arq || '.csv'
) as request_id
from unnest(array['products', 'sales_teams', 'accounts', 'sales_pipeline']) as arq;
-- Anote os request_id retornados. Abaixo assumimos 1, 2, 3, 4 (banco novo).

-- ===================== PASSO 2: conferir e carregar =====================
-- Conferência: status 200 e MD5 iguais aos listados no topo
select id, status_code, md5(content) from net._http_response where id in (1, 2, 3, 4) order by id;

-- Tabelas de cadastro (products, sales_teams, accounts)
with arquivos(id, tabela) as (values (1, 'products'), (2, 'sales_teams'), (3, 'accounts')),
csv as (
  select a.tabela, string_to_array(replace(t.linha, E'\r', ''), ',') as c
  from arquivos a
  join net._http_response r on r.id = a.id
  cross join lateral regexp_split_to_table(r.content, E'\n') with ordinality as t(linha, n)
  where t.n > 1 and btrim(replace(t.linha, E'\r', '')) <> ''
),
ins_prod as (
  insert into public.products (product, series, sales_price)
  select c[1], c[2], c[3]::numeric from csv where tabela = 'products'
  on conflict do nothing returning 1
),
ins_team as (
  insert into public.sales_teams (sales_agent, manager, regional_office)
  select c[1], c[2], c[3] from csv where tabela = 'sales_teams'
  on conflict do nothing returning 1
),
ins_acc as (
  insert into public.accounts (account, sector, year_established, revenue, employees, office_location, subsidiary_of)
  select c[1],
         case c[2] when 'technolgy' then 'technology' else c[2] end,      -- correção de grafia
         nullif(c[3], '')::int, nullif(c[4], '')::numeric, nullif(c[5], '')::int,
         case c[6] when 'Philipines' then 'Philippines' else c[6] end,    -- correção de grafia
         nullif(c[7], '')
  from csv where tabela = 'accounts'
  on conflict do nothing returning 1
)
select (select count(*) from ins_prod) as products,    -- esperado 7
       (select count(*) from ins_team) as sales_teams, -- esperado 35
       (select count(*) from ins_acc)  as accounts;    -- esperado 85

-- Pipeline (depois dos cadastros, por causa das chaves estrangeiras)
with csv as (
  select string_to_array(replace(t.linha, E'\r', ''), ',') as c
  from net._http_response r
  cross join lateral regexp_split_to_table(r.content, E'\n') with ordinality as t(linha, n)
  where r.id = 4 and t.n > 1 and btrim(replace(t.linha, E'\r', '')) <> ''
),
ins as (
  insert into public.sales_pipeline (opportunity_id, sales_agent, product, account, deal_stage, engage_date, close_date, close_value)
  select c[1], c[2],
         case c[3] when 'GTXPro' then 'GTX Pro' else c[3] end,            -- produto fora do catálogo
         nullif(c[4], ''), c[5],
         nullif(c[6], '')::date, nullif(c[7], '')::date, nullif(c[8], '')::numeric
  from csv
  on conflict do nothing returning deal_stage
)
select deal_stage, count(*) from ins group by deal_stage order by 1;
-- esperado: Engaging 1589 | Lost 2473 | Prospecting 500 | Won 4238
