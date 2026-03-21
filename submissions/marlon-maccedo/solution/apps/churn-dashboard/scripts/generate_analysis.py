#!/usr/bin/env python3
"""
Generate churn analysis JSON from 5 RavenStack CSVs.

Usage:
    cd apps/churn-dashboard
    python scripts/generate_analysis.py

Output:
    data/churn_analysis.json
"""

import json
import os
import re
from pathlib import Path
from collections import Counter

import pandas as pd
import numpy as np
from scipy import stats

DATA_DIR    = Path(__file__).parent.parent / 'data'
OUTPUT_FILE = DATA_DIR / 'churn_analysis.json'

STOP_WORDS = {
    'to', 'and', 'the', 'a', 'is', 'in', 'it', 'for', 'of', 'with',
    'was', 'not', 'are', 'by', 'from', 'at', 'on', 'no', 'too', 'but',
    'our', 'we', 'my', 'had', 'has', 'have', 'this', 'that', 'an', 'or',
    'be', 'as', 'so', 'do', 'did', 'its', 'very', 'i', 'us',
}


# ── Data loading ──────────────────────────────────────────────────────────────

def load_data():
    accounts  = pd.read_csv(DATA_DIR / 'ravenstack_accounts.csv')
    subs      = pd.read_csv(DATA_DIR / 'ravenstack_subscriptions.csv')
    features  = pd.read_csv(DATA_DIR / 'ravenstack_feature_usage.csv')
    tickets   = pd.read_csv(DATA_DIR / 'ravenstack_support_tickets.csv')
    events    = pd.read_csv(DATA_DIR / 'ravenstack_churn_events.csv')

    # Normalize Python-style booleans from CSV strings
    bool_map = {'True': True, 'False': False}
    for df in [accounts, subs, features, tickets, events]:
        for col in df.select_dtypes(include='object').columns:
            if set(df[col].dropna().unique()).issubset({'True', 'False'}):
                df[col] = df[col].map(bool_map)

    print(f'  accounts:  {len(accounts):,}')
    print(f'  subs:      {len(subs):,}')
    print(f'  features:  {len(features):,}')
    print(f'  tickets:   {len(tickets):,}')
    print(f'  events:    {len(events):,}')

    return accounts, subs, features, tickets, events


# ── Overview ──────────────────────────────────────────────────────────────────

def compute_overview(accounts, subs):
    sub_agg = subs.groupby('account_id').agg(
        mrr=('mrr_amount', 'sum'),
        arr=('arr_amount', 'sum'),
    ).reset_index()

    merged = accounts.merge(sub_agg, on='account_id', how='left')
    merged['mrr'] = merged['mrr'].fillna(0)
    merged['arr'] = merged['arr'].fillna(0)

    total   = len(merged)
    churn_m = merged['churn_flag'] == True
    churned = int(churn_m.sum())

    avg_mrr_c = merged.loc[churn_m, 'mrr'].mean()
    avg_mrr_r = merged.loc[~churn_m, 'mrr'].mean()

    return {
        'totalAccounts':   total,
        'churnedAccounts': churned,
        'churnRate':       round(churned / total * 100, 1) if total else 0,
        'mrrTotal':        round(float(merged['mrr'].sum()), 0),
        'mrrChurned':      round(float(merged.loc[churn_m, 'mrr'].sum()), 0),
        'mrrRetained':     round(float(merged.loc[~churn_m, 'mrr'].sum()), 0),
        'arrTotal':        round(float(merged['arr'].sum()), 0),
        'avgMrrChurned':   round(float(avg_mrr_c) if not np.isnan(avg_mrr_c) else 0, 0),
        'avgMrrRetained':  round(float(avg_mrr_r) if not np.isnan(avg_mrr_r) else 0, 0),
    }


# ── Segment breakdowns ────────────────────────────────────────────────────────

def compute_segment_breakdown(accounts, subs, col):
    sub_agg = subs.groupby('account_id').agg(mrr=('mrr_amount', 'sum')).reset_index()
    merged  = accounts.merge(sub_agg, on='account_id', how='left')
    merged['mrr'] = merged['mrr'].fillna(0)

    rows = []
    for seg, grp in merged.groupby(col):
        total   = len(grp)
        churned = int((grp['churn_flag'] == True).sum())
        rows.append({
            'segment':   str(seg),
            'total':     total,
            'churned':   churned,
            'churnRate': round(churned / total * 100, 1) if total else 0,
            'mrrLost':   round(float(grp.loc[grp['churn_flag'] == True, 'mrr'].sum()), 0),
        })

    return sorted(rows, key=lambda x: x['churnRate'], reverse=True)


# ── Feature analysis ──────────────────────────────────────────────────────────

def compute_feature_analysis(accounts, subs, features):
    # Join path: feature_usage → subscriptions → accounts (for churn_flag)
    sub_churn = subs[['subscription_id', 'account_id']].merge(
        accounts[['account_id', 'churn_flag']], on='account_id', how='left'
    )
    fu = features.merge(sub_churn[['subscription_id', 'churn_flag']], on='subscription_id', how='left')
    fu = fu.dropna(subset=['churn_flag'])

    results = []
    for feat in sorted(fu['feature_name'].unique()):
        df = fu[fu['feature_name'] == feat]
        u_c = df.loc[df['churn_flag'] == True,  'usage_count']
        u_r = df.loc[df['churn_flag'] == False, 'usage_count']
        e_c = df.loc[df['churn_flag'] == True,  'error_count']
        e_r = df.loc[df['churn_flag'] == False, 'error_count']

        avg_c  = float(u_c.mean()) if len(u_c) else 0.0
        avg_r  = float(u_r.mean()) if len(u_r) else 0.0
        err_c  = float(e_c.mean()) if len(e_c) else 0.0
        err_r  = float(e_r.mean()) if len(e_r) else 0.0

        p_val  = None
        if len(u_c) >= 5 and len(u_r) >= 5:
            try:
                _, p_val = stats.mannwhitneyu(u_c, u_r, alternative='two-sided')
                p_val = round(float(p_val), 4)
            except Exception:
                p_val = None

        results.append({
            'feature':          feat,
            'avgCountChurned':  round(avg_c, 2),
            'avgCountRetained': round(avg_r, 2),
            'delta':            round(avg_r - avg_c, 2),   # positive = retained use more
            'avgErrorChurned':  round(err_c, 2),
            'avgErrorRetained': round(err_r, 2),
            'pValue':           p_val,
        })

    results.sort(key=lambda x: abs(x['delta']), reverse=True)
    protective = [r['feature'] for r in results if r['delta'] > 0][:5]
    warning    = [r['feature'] for r in results if r['delta'] < 0][:5]

    return {
        'features':           results,
        'protectiveFeatures': protective,
        'warningFeatures':    warning,
    }


# ── Support analysis ──────────────────────────────────────────────────────────

def compute_support_analysis(accounts, tickets):
    merged = tickets.merge(accounts[['account_id', 'churn_flag']], on='account_id', how='left')
    merged = merged.dropna(subset=['churn_flag'])

    ch = merged[merged['churn_flag'] == True]
    re = merged[merged['churn_flag'] == False]

    # Tickets per account (fill 0 for accounts with no tickets)
    tc = tickets.groupby('account_id').size()
    churn_ids    = accounts.loc[accounts['churn_flag'] == True,  'account_id']
    retained_ids = accounts.loc[accounts['churn_flag'] == False, 'account_id']

    avg_t_c = float(tc.reindex(churn_ids,    fill_value=0).mean())
    avg_t_r = float(tc.reindex(retained_ids, fill_value=0).mean())

    avg_res_c = float(ch['resolution_time_hours'].mean()) if len(ch) else 0.0
    avg_res_r = float(re['resolution_time_hours'].mean()) if len(re) else 0.0

    csat_c = ch['satisfaction_score'].mean()
    csat_r = re['satisfaction_score'].mean()

    esc_c = float((ch['escalation_flag'] == True).mean()) * 100
    esc_r = float((re['escalation_flag'] == True).mean()) * 100

    return {
        'avgTicketsChurned':          round(avg_t_c, 2),
        'avgTicketsRetained':         round(avg_t_r, 2),
        'avgResolutionHoursChurned':  round(avg_res_c, 1),
        'avgResolutionHoursRetained': round(avg_res_r, 1),
        'avgCsatChurned':             round(float(csat_c), 2) if not pd.isna(csat_c) else None,
        'avgCsatRetained':            round(float(csat_r), 2) if not pd.isna(csat_r) else None,
        'escalationRateChurned':      round(esc_c, 1),
        'escalationRateRetained':     round(esc_r, 1),
    }


# ── Churn reasons ─────────────────────────────────────────────────────────────

def compute_churn_reasons(events):
    total  = len(events)
    grps   = events.groupby('reason_code').agg(
        count=('churn_event_id', 'count'),
        mrrLost=('refund_amount_usd', 'sum'),
    ).reset_index()

    rows = sorted([
        {
            'reasonCode': row['reason_code'],
            'count':      int(row['count']),
            'mrrLost':    round(float(row['mrrLost']), 0),
            'pct':        round(float(row['count']) / total * 100, 1) if total else 0,
        }
        for _, row in grps.iterrows()
    ], key=lambda x: x['count'], reverse=True)

    # Feedback word frequency
    texts  = events['feedback_text'].dropna().astype(str).tolist()
    words  = []
    for text in texts:
        tokens = re.findall(r'\b[a-z]+\b', text.lower())
        words.extend(t for t in tokens if t not in STOP_WORDS and len(t) > 2)

    themes = [{'theme': w, 'count': c} for w, c in Counter(words).most_common(20)]

    return {'reasonBreakdown': rows, 'feedbackThemes': themes}


# ── At-risk accounts ──────────────────────────────────────────────────────────

def compute_at_risk_accounts(accounts, subs, features, tickets):
    """Score retained accounts by churn risk (0–100)."""
    retained = accounts[accounts['churn_flag'] == False].copy()

    # MRR + downgrade flag per account
    sub_agg = subs.groupby('account_id').agg(
        mrr=('mrr_amount', 'sum'),
        downgrade_flag=('downgrade_flag', 'max'),
    ).reset_index()
    retained = retained.merge(sub_agg, on='account_id', how='left')
    retained['mrr']            = retained['mrr'].fillna(0)
    retained['downgrade_flag'] = retained['downgrade_flag'].fillna(False)

    # Feature usage per account
    sub_ids = subs[['subscription_id', 'account_id']]
    fu      = features.merge(sub_ids, on='subscription_id', how='left')

    feat_cnt = fu.groupby('account_id')['feature_name'].nunique().rename('features_used')
    avg_use  = fu.groupby('account_id')['usage_count'].mean().rename('avg_usage')

    retained = retained.join(feat_cnt, on='account_id').join(avg_use, on='account_id')
    retained['features_used'] = retained['features_used'].fillna(0)
    retained['avg_usage']     = retained['avg_usage'].fillna(0)

    # Support per account
    tkt_grp = tickets.groupby('account_id').agg(
        ticket_count=('ticket_id', 'count'),
        escalations=('escalation_flag', lambda x: (x == True).sum()),
    )
    retained = retained.join(tkt_grp, on='account_id')
    retained['ticket_count'] = retained['ticket_count'].fillna(0)
    retained['escalations']  = retained['escalations'].fillna(0)

    avg_features = retained['features_used'].mean()
    avg_tickets  = retained['ticket_count'].mean()

    results = []
    for _, row in retained.iterrows():
        score = 0
        flags = []

        if row['features_used'] < avg_features * 0.5:
            score += 30
            flags.append('baixo uso de features')
        elif row['features_used'] < avg_features * 0.8:
            score += 15
            flags.append('uso moderado de features')

        if row['is_trial']:
            score += 20
            flags.append('conta trial')

        if row['downgrade_flag']:
            score += 20
            flags.append('downgrade recente')

        if row['ticket_count'] > avg_tickets * 1.5:
            score += 15
            flags.append('alto volume de tickets')

        if row['escalations'] > 0:
            score += 10
            flags.append('tickets escalados')

        if row['plan_tier'] == 'Basic':
            score += 5

        results.append({
            'accountId':   row['account_id'],
            'accountName': row['account_name'],
            'industry':    row['industry'],
            'country':     row['country'],
            'planTier':    row['plan_tier'],
            'mrr':         round(float(row['mrr']), 0),
            'riskScore':   min(score, 100),
            'riskFlags':   flags,
        })

    results.sort(key=lambda x: (-x['riskScore'], -x['mrr']))
    return results[:100]


# ── Timeline ──────────────────────────────────────────────────────────────────

def compute_timeline(events):
    df = events[events['is_reactivation'] == False].copy()
    df['month'] = df['churn_date'].astype(str).str[:7]

    monthly = df.groupby('month').agg(
        count=('churn_event_id', 'count'),
        mrrLost=('refund_amount_usd', 'sum'),
    ).reset_index()

    return sorted([
        {'month': row['month'], 'count': int(row['count']), 'mrrLost': round(float(row['mrrLost']), 0)}
        for _, row in monthly.iterrows()
    ], key=lambda x: x['month'])


# ── NaN sanitizer ─────────────────────────────────────────────────────────────

def nan_to_none(obj):
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: nan_to_none(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [nan_to_none(v) for v in obj]
    return obj


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print('Loading data...')
    accounts, subs, features, tickets, events = load_data()

    print('Computing overview...')
    overview = compute_overview(accounts, subs)
    print(f'  churn rate: {overview["churnRate"]}%  |  MRR churned: ${overview["mrrChurned"]:,.0f}')

    print('Computing segment breakdowns...')
    segments = {
        'by_industry': compute_segment_breakdown(accounts, subs, 'industry'),
        'by_channel':  compute_segment_breakdown(accounts, subs, 'referral_source'),
        'by_plan':     compute_segment_breakdown(accounts, subs, 'plan_tier'),
        'by_country':  compute_segment_breakdown(accounts, subs, 'country'),
    }

    print('Computing feature analysis (Mann-Whitney)...')
    feature_analysis = compute_feature_analysis(accounts, subs, features)
    print(f'  {len(feature_analysis["features"])} features  |  '
          f'{len(feature_analysis["protectiveFeatures"])} protective  |  '
          f'{len(feature_analysis["warningFeatures"])} warning')

    print('Computing support analysis...')
    support_analysis = compute_support_analysis(accounts, tickets)
    print(f'  tickets/churned: {support_analysis["avgTicketsChurned"]}  |  '
          f'tickets/retained: {support_analysis["avgTicketsRetained"]}')

    print('Computing churn reasons...')
    churn_reasons = compute_churn_reasons(events)
    print(f'  {len(churn_reasons["reasonBreakdown"])} reasons  |  '
          f'{len(churn_reasons["feedbackThemes"])} theme words')

    print('Computing at-risk accounts...')
    at_risk = compute_at_risk_accounts(accounts, subs, features, tickets)
    print(f'  {len(at_risk)} at-risk retained accounts')

    print('Computing timeline...')
    timeline = compute_timeline(events)
    print(f'  {len(timeline)} months')

    output = nan_to_none({
        'overview':        overview,
        'segments':        segments,
        'featureAnalysis': feature_analysis,
        'supportAnalysis': support_analysis,
        'churnReasons':    churn_reasons,
        'atRiskAccounts':  at_risk,
        'timeline':        timeline,
    })

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f'\nDone. Output: {OUTPUT_FILE}')


if __name__ == '__main__':
    main()
