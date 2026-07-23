// 1. ROBUST transitions by account support
MATCH (a:EventType)-[r:TRANSITIONS_TO]->(b:EventType)
WHERE r.stability_status = 'ROBUST' AND r.is_promotable = true
RETURN a.event_type, b.event_type, r.journey_scope, r.account_support, r.denominator_accounts
ORDER BY r.account_support DESC LIMIT 20;

// 2. SENSITIVE patterns in recurring churn context
MATCH (p:Pattern)-[:ASSOCIATED_WITH|OBSERVED_BEFORE]->(o:Outcome)
WHERE p.stability_status = 'SENSITIVE' AND (o.outcome = 'RECURRING_CHURN' OR p.pattern CONTAINS 'CHURN')
RETURN p.pattern, p.account_support, p.strict_support, p.journey_scope ORDER BY p.account_support DESC LIMIT 20;

// 3. Reactivation journeys with observed use
MATCH (j:Journey)-[:HAS_EVENT]->(e:EventInstance)-[:OF_TYPE]->(t:EventType)
WHERE j.journey_scope = 'BETWEEN_CHURN_AND_REACTIVATION' AND t.event_type = 'FEATURE'
RETURN count(DISTINCT j) AS journeys_with_use;

// 4. Warning-dependent patterns
MATCH (p:Pattern) RETURN p.pattern, p.principal_support, p.strict_support,
       p.principal_support - p.strict_support AS support_gap
ORDER BY support_gap DESC LIMIT 20;

// 5. Churn paths by associated MRR
MATCH (p:Pattern)-[:CONTAINS_EVENT_TYPE]->(t:EventType {event_type:'CHURN'})
RETURN p.pattern, p.associated_mrr, p.mrr_account_count, p.account_support
ORDER BY p.associated_mrr DESC LIMIT 20;

// 6. Taxonomy coverage profiles
MATCH (j:Journey)-[:CLASSIFIED_AS]->(t:Taxonomy)
MATCH (j)-[:HAS_QUALITY_PROFILE]->(q:QualityProfile)
RETURN t.name, q.coverage_band, count(*) AS journeys ORDER BY journeys DESC;

// 7. HIGH-order candidates are intentionally absent from the promoted graph
MATCH (p:Pattern) WHERE p.same_day_dependency = 'HIGH' RETURN count(p) AS must_be_zero;

// 8. Findings recommending data-quality review
MATCH (f:Finding)-[:RECOMMENDS_INVESTIGATION]->(i:Investigation)
WHERE i.investigation_type = 'REVIEW_DATA_QUALITY' RETURN f.finding_id, f.title;

// 9. EventType structural connectivity (not causal importance)
MATCH (a:EventType)-[r:TRANSITIONS_TO]->() RETURN a.event_type, sum(r.account_support) AS weighted_out_degree
ORDER BY weighted_out_degree DESC;

// 10. Pattern families across churn and reactivation contexts
MATCH (p:Pattern) WHERE p.outcome_context CONTAINS 'CHURN' OR p.outcome_context CONTAINS 'REACTIVATION'
RETURN p.pattern_family_key, collect(DISTINCT p.outcome_context) AS contexts, count(*) AS pattern_nodes
ORDER BY pattern_nodes DESC;
