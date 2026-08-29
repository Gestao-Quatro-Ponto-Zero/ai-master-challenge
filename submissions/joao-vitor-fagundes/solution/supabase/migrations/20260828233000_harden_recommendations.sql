drop policy if exists "Public read recommendations" on public.power_recommendations;
revoke select on public.power_recommendations from anon, authenticated;

create table if not exists public.power_recommendation_rate_limits (
  bucket_kind text not null check (bucket_kind in ('hour', 'day')),
  bucket_start timestamptz not null,
  request_count integer not null check (request_count >= 0),
  updated_at timestamptz not null default now(),
  primary key (bucket_kind, bucket_start)
);

alter table public.power_recommendation_rate_limits enable row level security;
revoke all on public.power_recommendation_rate_limits from anon, authenticated;
grant select, insert, update on public.power_recommendation_rate_limits to service_role;

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

revoke all on function public.claim_power_recommendation(text, text, text, text, text, integer, integer) from public;
grant execute on function public.claim_power_recommendation(text, text, text, text, text, integer, integer) to service_role;

comment on table public.power_recommendation_rate_limits is
  'Server-only hourly and daily generation budgets for the public challenge demo.';
