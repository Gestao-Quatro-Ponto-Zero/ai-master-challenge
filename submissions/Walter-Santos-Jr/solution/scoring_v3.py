"""Versioned, deterministic commercial decision policy (not a win probability).

V3 retains the validated V2 baseline as the commercial attractiveness measure.
Qualification is a separate evidence assessment; missing fields are unknown,
not negative. Operational urgency is separate from attractiveness.
"""
from dataclasses import dataclass

POLICY_VERSION = '3.0.0-decision-support'
BANDS = ((45, 'LOW'), (65, 'MEDIUM'), (100, 'HIGH'))
QUALIFICATION_FIELDS = ('decision_maker', 'timeline', 'budget')


def assess(row, qualification=None):
    qualification = qualification or {}
    baseline = float(row['priority_score'])
    components = [
        {'label': 'Sales stage', 'weight': 40, 'component': float(row['stage_component']), 'points': round(.4 * float(row['stage_component']), 1)},
        {'label': 'Catalog price', 'weight': 35, 'component': float(row['product_component']), 'points': round(.35 * float(row['product_component']), 1)},
        {'label': 'Account scale', 'weight': 25, 'component': float(row['account_component']), 'points': round(.25 * float(row['account_component']), 1)},
    ]
    evidence = {key: qualification.get(key, 'unknown') for key in QUALIFICATION_FIELDS}
    if any(v not in {'yes', 'no', 'unknown'} for v in evidence.values()):
        raise ValueError('Invalid qualification evidence')
    known = sum(v != 'unknown' for v in evidence.values())
    # Qualification readiness is an ordinal evidence summary, not a win probability.
    positive = sum(v == 'yes' for v in evidence.values())
    negative = sum(v == 'no' for v in evidence.values())
    readiness = 'UNASSESSED' if known == 0 else ('BLOCKED' if negative else 'QUALIFIED' if known == 3 else 'PARTIAL')
    confidence = {
        'account_known': bool(row['account_known']),
        'qualification_known': known,
        'qualification_total': len(QUALIFICATION_FIELDS),
        'level': 'LOW' if known == 0 or not row['account_known'] else ('HIGH' if known == 3 else 'MEDIUM'),
    }
    risks = []
    if not row['account_known']:
        risks.append({'code': 'ACCOUNT_MISSING', 'severity': 'MEDIUM', 'reason': 'Account not identified; account-scale factor is neutral.'})
    if negative:
        risks.append({'code': 'QUALIFICATION_BLOCKER', 'severity': 'HIGH', 'reason': 'One or more qualification answers are explicitly no.'})
    if known < 3:
        risks.append({'code': 'QUALIFICATION_INCOMPLETE', 'severity': 'MEDIUM', 'reason': f'{3-known} qualification fields remain unknown.'})
    # Never infer stagnation from 2016/17 engage_date versus today's clock.
    if not row['account_known']:
        action = 'IDENTIFY_ACCOUNT'
    elif negative:
        action = 'RESOLVE_QUALIFICATION_BLOCKER'
    elif row['deal_stage'] == 'Prospecting' or known < 3:
        action = 'QUALIFY_OPPORTUNITY'
    else:
        action = 'REVIEW_ENGAGEMENT'
    # Operational job urgency requires evidence of due date or explicit blocker.
    job_priority = 'P1' if negative else 'P2' if not row['account_known'] else 'P3'
    return {
        'policy_version': POLICY_VERSION,
        'priority_score': round(baseline, 1),
        'priority_band': next(name for limit, name in BANDS if baseline <= limit),
        'score_explanation': components,
        'score_basis': 'V2 baseline retained pending empirical weight calibration; not a close probability.',
        'buying_readiness': readiness,
        'qualification_evidence': evidence,
        'qualification_evidence_summary': {'known': known, 'positive': positive, 'negative': negative},
        'data_confidence_detail': confidence,
        'deal_health_flags': risks,
        'next_best_action': action,
        'job_priority_hint': job_priority,
        'job_priority_explanation': 'Evidence-based triage only; no historical-date urgency inferred.',
    }
