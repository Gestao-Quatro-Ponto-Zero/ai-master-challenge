create extension if not exists pgcrypto;

create table public.accounts (
  account text primary key,
  sector text not null,
  year_established smallint,
  revenue_musd numeric(14, 2),
  employees integer,
  office_location text,
  subsidiary_of text
);

create table public.products (
  product_key text primary key,
  product text not null unique,
  series text not null,
  sales_price integer not null check (sales_price >= 0),
  value_tier text not null check (value_tier in ('Bronze', 'Silver', 'Gold', 'Diamond'))
);

create table public.sales_teams (
  sales_agent text primary key,
  manager text not null,
  regional_office text not null
);

create table public.opportunities (
  opportunity_id text primary key,
  sales_agent text not null references public.sales_teams(sales_agent),
  product_key text not null references public.products(product_key),
  account text references public.accounts(account),
  deal_stage text not null check (deal_stage in ('Prospecting', 'Engaging', 'Won', 'Lost')),
  engage_date date,
  close_date date,
  close_value integer,
  snapshot_date date not null,
  potential_value integer not null check (potential_value >= 0),
  age_days integer check (age_days is null or age_days >= 0)
);

create table public.power_score_runs (
  run_id uuid primary key default gen_random_uuid(),
  score_version text not null,
  snapshot_date date not null,
  opportunity_count integer not null,
  closed_history_count integer not null,
  propensity_history_threshold integer not null,
  assumptions jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table public.power_scores (
  opportunity_id text primary key references public.opportunities(opportunity_id) on delete cascade,
  score_version text not null,
  input_hash text not null,
  propensity_score numeric(5, 2) check (propensity_score between 0 and 100),
  propensity_evidence jsonb not null default '{}'::jsonb,
  opportunity_value_score numeric(5, 2) not null check (opportunity_value_score between 0 and 100),
  opportunity_value_tier text not null check (opportunity_value_tier in ('Bronze', 'Silver', 'Gold', 'Diamond')),
  warmth_score numeric(5, 2) not null check (warmth_score between 0 and 100),
  warmth_temperature text not null check (warmth_temperature in ('Sem contato', 'Quente', 'Morna', 'Fria', 'Estagnada')),
  warmth_evidence jsonb not null default '{}'::jsonb,
  execution_fit_score numeric(5, 2) check (execution_fit_score between 0 and 100),
  execution_fit_evidence jsonb not null default '{}'::jsonb,
  power_priority_score numeric(5, 2) generated always as (
    case
      when propensity_score is null or execution_fit_score is null then null
      else round((
        12 * propensity_score
        + 3 * opportunity_value_score
        + 4 * warmth_score
        + 6 * execution_fit_score
      ) / 25.0, 2)
    end
  ) stored,
  calculated_at timestamptz not null default now()
);

create table public.power_recommendations (
  recommendation_id uuid primary key default gen_random_uuid(),
  opportunity_id text not null references public.opportunities(opportunity_id) on delete cascade,
  input_hash text not null,
  prompt_version text not null,
  provider text not null,
  model text not null,
  status text not null check (status in ('generating', 'ready', 'error')),
  action_label text,
  recommendation text,
  rationale jsonb,
  suggested_approach text,
  support_needed text,
  limitations jsonb,
  error_message text,
  usage jsonb,
  generated_at timestamptz,
  updated_at timestamptz not null default now(),
  unique (opportunity_id, input_hash, prompt_version)
);

create table public.power_recommendation_rate_limits (
  bucket_kind text not null check (bucket_kind in ('hour', 'day')),
  bucket_start timestamptz not null,
  request_count integer not null check (request_count >= 0),
  updated_at timestamptz not null default now(),
  primary key (bucket_kind, bucket_start)
);

create index opportunities_stage_idx on public.opportunities(deal_stage);
create index opportunities_seller_idx on public.opportunities(sales_agent);
create index opportunities_product_idx on public.opportunities(product_key);
create index opportunities_account_idx on public.opportunities(account);
create index power_recommendations_lookup_idx
  on public.power_recommendations(opportunity_id, input_hash, prompt_version, status);

create or replace function public.touch_power_recommendation_updated_at()
returns trigger
language plpgsql
set search_path = public
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger power_recommendations_updated_at
before update on public.power_recommendations
for each row execute function public.touch_power_recommendation_updated_at();

create or replace function public.claim_power_recommendation(
  p_opportunity_id text,
  p_input_hash text,
  p_prompt_version text,
  p_provider text,
  p_model text,
  p_hourly_limit integer default 500,
  p_daily_limit integer default 2000
)
returns table (recommendation_id uuid, claim_status text)
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_existing public.power_recommendations%rowtype;
  v_claimed_id uuid;
  v_bucket_count integer;
begin
  select pr.* into v_existing
  from public.power_recommendations pr
  where pr.opportunity_id = p_opportunity_id
    and pr.input_hash = p_input_hash
    and pr.prompt_version = p_prompt_version;

  if v_existing.status = 'ready' then
    return query select v_existing.recommendation_id, 'cached'::text;
    return;
  end if;

  if v_existing.status = 'generating'
    and v_existing.updated_at >= now() - interval '2 minutes' then
    return query select v_existing.recommendation_id, 'generating'::text;
    return;
  end if;

  if v_existing.recommendation_id is null then
    insert into public.power_recommendations (
      opportunity_id, input_hash, prompt_version, provider, model, status, error_message
    ) values (
      p_opportunity_id, p_input_hash, p_prompt_version, p_provider, p_model, 'generating', null
    )
    on conflict (opportunity_id, input_hash, prompt_version) do nothing
    returning public.power_recommendations.recommendation_id into v_claimed_id;
  else
    update public.power_recommendations pr
    set provider = p_provider,
        model = p_model,
        status = 'generating',
        error_message = null,
        updated_at = now()
    where pr.recommendation_id = v_existing.recommendation_id
      and (
        pr.status = 'error'
        or (pr.status = 'generating' and pr.updated_at < now() - interval '2 minutes')
      )
    returning pr.recommendation_id into v_claimed_id;
  end if;

  if v_claimed_id is null then
    select pr.* into v_existing
    from public.power_recommendations pr
    where pr.opportunity_id = p_opportunity_id
      and pr.input_hash = p_input_hash
      and pr.prompt_version = p_prompt_version;
    return query select v_existing.recommendation_id,
      case when v_existing.status = 'ready' then 'cached'::text else v_existing.status end;
    return;
  end if;

  v_bucket_count := null;
  insert into public.power_recommendation_rate_limits as limits (
    bucket_kind, bucket_start, request_count, updated_at
  ) values (
    'day', date_trunc('day', now()), 1, now()
  )
  on conflict (bucket_kind, bucket_start) do update
    set request_count = limits.request_count + 1,
        updated_at = now()
    where limits.request_count < greatest(p_daily_limit, 1)
  returning request_count into v_bucket_count;

  if v_bucket_count is null then
    update public.power_recommendations
    set status = 'error', error_message = 'Daily demo generation limit reached'
    where public.power_recommendations.recommendation_id = v_claimed_id;
    return query select v_claimed_id, 'rate_limited'::text;
    return;
  end if;

  v_bucket_count := null;
  insert into public.power_recommendation_rate_limits as limits (
    bucket_kind, bucket_start, request_count, updated_at
  ) values (
    'hour', date_trunc('hour', now()), 1, now()
  )
  on conflict (bucket_kind, bucket_start) do update
    set request_count = limits.request_count + 1,
        updated_at = now()
    where limits.request_count < greatest(p_hourly_limit, 1)
  returning request_count into v_bucket_count;

  if v_bucket_count is null then
    update public.power_recommendations
    set status = 'error', error_message = 'Hourly demo generation limit reached'
    where public.power_recommendations.recommendation_id = v_claimed_id;
    return query select v_claimed_id, 'rate_limited'::text;
    return;
  end if;

  return query select v_claimed_id, 'claimed'::text;
end;
$$;

create or replace view public.opportunity_power
with (security_invoker = true)
as
select
  o.opportunity_id,
  o.deal_stage,
  o.engage_date,
  o.close_date,
  o.close_value,
  o.snapshot_date,
  o.potential_value,
  o.age_days,
  o.sales_agent,
  st.manager,
  st.regional_office,
  p.product_key,
  p.product,
  p.series,
  p.sales_price,
  p.value_tier,
  a.account,
  a.sector,
  a.year_established,
  a.revenue_musd,
  a.employees,
  a.office_location,
  ps.score_version,
  ps.input_hash,
  ps.propensity_score,
  ps.propensity_evidence,
  ps.opportunity_value_score,
  ps.opportunity_value_tier,
  ps.warmth_score,
  ps.warmth_temperature,
  ps.warmth_evidence,
  ps.execution_fit_score,
  ps.execution_fit_evidence,
  ps.calculated_at,
  ps.power_priority_score
from public.opportunities o
join public.sales_teams st on st.sales_agent = o.sales_agent
join public.products p on p.product_key = o.product_key
left join public.accounts a on a.account = o.account
left join public.power_scores ps on ps.opportunity_id = o.opportunity_id;

alter table public.accounts enable row level security;
alter table public.products enable row level security;
alter table public.sales_teams enable row level security;
alter table public.opportunities enable row level security;
alter table public.power_score_runs enable row level security;
alter table public.power_scores enable row level security;
alter table public.power_recommendations enable row level security;
alter table public.power_recommendation_rate_limits enable row level security;

create policy "Public read accounts" on public.accounts for select to anon, authenticated using (true);
create policy "Public read products" on public.products for select to anon, authenticated using (true);
create policy "Public read sales teams" on public.sales_teams for select to anon, authenticated using (true);
create policy "Public read opportunities" on public.opportunities for select to anon, authenticated using (true);
create policy "Public read score runs" on public.power_score_runs for select to anon, authenticated using (true);
create policy "Public read power scores" on public.power_scores for select to anon, authenticated using (true);
grant usage on schema public to anon, authenticated;
grant select on public.accounts to anon, authenticated;
grant select on public.products to anon, authenticated;
grant select on public.sales_teams to anon, authenticated;
grant select on public.opportunities to anon, authenticated;
grant select on public.power_score_runs to anon, authenticated;
grant select on public.power_scores to anon, authenticated;
grant select on public.opportunity_power to anon, authenticated;
grant select on public.opportunity_power to service_role;
grant select on public.opportunities, public.accounts, public.products,
  public.sales_teams, public.power_scores to service_role;

grant select, insert, update on public.power_recommendations to service_role;
grant select, insert, update on public.power_recommendation_rate_limits to service_role;
revoke all on function public.claim_power_recommendation(text, text, text, text, text, integer, integer) from public;
grant execute on function public.claim_power_recommendation(text, text, text, text, text, integer, integer) to service_role;

comment on table public.power_scores is
  'Deterministic P, O, W and E results plus the stored POWER Priority. R is generated automatically on first open and cached separately.';
comment on table public.power_recommendations is
  'Seller-facing Recommendation results keyed by score input hash and prompt version.';
comment on table public.power_recommendation_rate_limits is
  'Server-only hourly and daily generation budgets for the public challenge demo.';
