# Intervention Watchlist

## 1. Executive Summary

At cutoff `2024-12-31T19:00:00`, 500 of 500 accounts appear in at least one governed review queue, generating 1609 rule-level items across 7 queues. The result is `PASS_WITH_WARNINGS`: suitable for human triage with preserved quality flags, not for automated decisions, outreach, prediction, or causal interpretation.

## 2. Purpose

The watchlist directs scarce analyst attention to evidence review. It does not prescribe treatment or rank customers by hidden logic.

## 3. Governance principles

Rules are deterministic and versioned; evidence, urgency, materiality, and confidence remain separate; every disposition requires a human reviewer.

## 4. Populations

MAIN includes VALID and VALID_WITH_WARNING without quarantine. STRICT uses VALID only for sensitivity. Quarantine is quality-only and creates no behavioral signal.

## 5. Reference date

All features use evidence at or before `2024-12-31T19:00:00`; denominator is 500 anonymous accounts and historical cutoffs are supported.

## 6. Queues

![Queue distribution](../figures/watchlist-queue-distribution.png)

Queues overlap by design because each rule is evaluated independently. Counts are distinct within queue.

## 7. Rules

![Rule overlap](../figures/watchlist-rule-overlap.png)

Sixteen deterministic rules declare conditions, exclusions, minimum support, owner, investigation, version, and prohibited actions. W002 remains documented without promotion because it has seven cases versus minimum support ten.

## 8. Priority

![Priority distribution](../figures/watchlist-priority-distribution.png)

P1-P4 comes from four discrete components and an explicit matrix; no weighted score is used. LOW confidence blocks behavioral P1.

## 9. Evidence

![Evidence map](../figures/watchlist-evidence-map.png)

Each packet retains cutoff, sources, observed metrics, graph paths, findings, denominators, quality flags, limitations, and structured provenance.

## 10. JourneyGraph

Only promoted ROBUST/SENSITIVE, non-HIGH, non-small patterns enter explanations. Structural paths are non-causal.

## 11. Quality

![Quality confidence](../figures/watchlist-quality-confidence.png)

467 watchlisted accounts require data review; quarantine contributes zero behavioral signals.

## 12. Materiality

![MRR by queue](../figures/watchlist-mrr-by-queue.png)

MRR is de-duplicated inside each queue and is associated context, not saved or lost revenue. Cross-queue sums must not be added because accounts overlap.

## 13. Explanations

Templates state what was observed, why it matched, timing, graph and quality context, limitations, authorized investigation, and prohibited interpretation.

## 14. Findings

At most one aggregate finding is emitted per queue and only when at least 20 distinct accounts support it. Findings include denominator, MRR deduplication, distributions, graph context, quality constraints, confidence, limitations, and human investigation.

## 15. Limitations

Evidence is retrospective, observational, and quality-sensitive. W011 is a justified broad quality exception; W014 and W015 require broad-rule review; the four-account W008 group is not generalized into a finding.

## 16. Human review

The owner confirms source quality and relevance, documents disposition, and closes or escalates the investigation. No contact or intervention is implied.

## 17. Preparation for Experiment Lab

The governed output can inform an Experiment Lab only if eligibility, exclusion, quality, consent, review, and measurement controls remain explicit.
