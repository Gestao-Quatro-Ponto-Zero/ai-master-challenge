alter table public.power_scores
add column if not exists power_priority_score numeric(5, 2) generated always as (
  case
    when propensity_score is null or execution_fit_score is null then null
    else round((
      12 * propensity_score
      + 3 * opportunity_value_score
      + 4 * warmth_score
      + 6 * execution_fit_score
    ) / 25.0, 2)
  end
) stored;

create index if not exists power_scores_priority_idx
  on public.power_scores (power_priority_score desc, opportunity_id);

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

comment on view public.opportunity_power is
  'Read model for the CRM. POWER Priority is stored and ordered independently inside each pipeline stage.';
