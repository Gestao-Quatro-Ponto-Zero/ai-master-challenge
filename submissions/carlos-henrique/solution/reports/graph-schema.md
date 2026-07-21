# Schema do JourneyGraph

## Account

Propriedades permitidas: `account_key, primary_outcome, mrr_band, associated_mrr, quality_population, quality_coverage_ratio, journey_count, event_count, taxonomy_class, is_anonymized`.

## Journey

Propriedades permitidas: `journey_key, journey_scope, quality_population, journey_start, journey_end, raw_length, collapsed_length, distinct_event_types, observed_days, same_day_order_dependency, contains_churn, contains_reactivation, quality_coverage_ratio, stability_status, journey_length_band`.

## EventInstance

Propriedades permitidas: `event_instance_key, event_type, event_time, event_position, same_day_order, quality_status, source_table, journey_scope, is_warning, is_endpoint_event`.

## EventType

Propriedades permitidas: `event_type`.

## Pattern

Propriedades permitidas: `pattern_key, pattern_family_key, pattern, pattern_type, pattern_length, journey_scope, outcome_context, quality_population, account_support, denominator_accounts, relative_support, confidence, lift, coverage, leverage, discriminative_ratio, principal_support, strict_support, stability_status, same_day_dependency, small_sample, exposure_control, is_promotable, associated_mrr, median_mrr, mean_mrr, mrr_account_count`.

## Outcome

Propriedades permitidas: `outcome, associated_mrr, median_mrr, mean_mrr, mrr_account_count`.

## Taxonomy

Propriedades permitidas: `taxonomy_id, name, definition, associated_mrr, median_mrr, mean_mrr, mrr_account_count`.

## QualityProfile

Propriedades permitidas: `quality_profile_key, population, stability_status, same_day_dependency, small_sample, warning_dependency_ratio_band, coverage_band, confidence_level, limitations_count`.

## Finding

Propriedades permitidas: `finding_id, title, confidence_level, stability_status, business_relevance, recommended_investigation, is_causal`.

## Investigation

Propriedades permitidas: `investigation_type, is_automatic, requires_human_review`.

## Relações

- `HAS_JOURNEY`
- `HAS_EVENT`
- `OF_TYPE`
- `NEXT_EVENT`
- `CLASSIFIED_AS`
- `ASSOCIATED_WITH_OUTCOME`
- `HAS_QUALITY_PROFILE`
- `MATCHES_PATTERN`
- `CONTAINS_EVENT_TYPE`
- `OBSERVED_BEFORE`
- `OBSERVED_AFTER`
- `ASSOCIATED_WITH`
- `SUPPORTED_BY`
- `RECOMMENDS_INVESTIGATION`
- `TRANSITIONS_TO`

## Semântica proibida

`CAUSES`, `CAUSE`, `LEADS_TO`, `RESULTS_IN`, `PREVENTS`, `DRIVES`, `DETERMINES`, `TRIGGERS_CHURN`, `SAVES_REVENUE`, `REVENUE_LOST`, `REVENUE_SAVED`, `PREVENTABLE_REVENUE`.
