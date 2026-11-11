-- Dados brutos dos dois datasets do Challenge 002, fiéis ao CSV original.
-- Nenhuma limpeza aqui: transformações ficam em views/consultas para manter rastreabilidade.

-- DS1 — Customer Support Ticket Dataset (sintético; ver context/data-findings.md)
create table if not exists public.ds1_tickets (
  ticket_id            integer primary key,
  customer_name        text,
  customer_email       text,
  customer_age         smallint,
  customer_gender      text,
  product_purchased    text,
  date_of_purchase     date,
  ticket_type          text not null,
  ticket_subject       text,
  ticket_description   text,
  ticket_status        text not null,
  resolution           text,
  ticket_priority      text not null,
  ticket_channel       text not null,
  first_response_at    timestamp,   -- coluna "First Response Time" (é timestamp, não duração)
  resolved_at          timestamp,   -- coluna "Time to Resolution" (é timestamp, não duração)
  csat                 smallint check (csat between 1 and 5)
);

comment on table public.ds1_tickets is
  'DS1 Kaggle suraj520/customer-support-ticket-dataset (CC0). 8.469 tickets. Sintético: variáveis independentes entre si.';

-- DS2 — IT Service Ticket Classification Dataset
create table if not exists public.ds2_tickets (
  id           integer primary key,          -- posição da linha no CSV original (0-based)
  document     text not null,
  topic_group  text not null,
  split        text not null check (split in ('train', 'test'))  -- holdout estratificado 80/20, seed 42
);

comment on table public.ds2_tickets is
  'DS2 Kaggle adisongoh/it-service-ticket-classification-dataset (CC0). 47.837 tickets reais, texto pré-processado, 8 categorias, sem resolução.';

create index if not exists ds1_tickets_dims_idx on public.ds1_tickets (ticket_status, ticket_channel, ticket_priority, ticket_type);
create index if not exists ds2_tickets_split_topic_idx on public.ds2_tickets (split, topic_group);

-- Segurança: RLS ligado e nenhuma policy para anon/authenticated.
-- O app lê por rotas de servidor (service role) ou por views específicas, definidas depois.
alter table public.ds1_tickets enable row level security;
alter table public.ds2_tickets enable row level security;
