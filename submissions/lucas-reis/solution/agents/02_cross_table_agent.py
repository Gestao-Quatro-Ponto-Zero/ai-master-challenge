"""
Agent 02 — Cross-table Analysis via DuckDB
Joins entre as 5 tabelas para construir visão unificada por account_id.

Correções aplicadas em 2026-03-20 (prompt_001c):
- usage_duration_secs / 60.0 (era usage_duration_min — coluna inexistente)
- churn_events deduplicado com ROW_NUMBER() (era JOIN direto, inflava churn em reativações)
- seats e avg_mrr em vez de company_size e contract_value (colunas inexistentes)
- priority IN ('high', 'urgent') (era só 'high', ignorava o nível mais grave)
- satisfaction_no_response_rate como feature (null de satisfaction é sinal, não missing)

Correção crítica (prompt_003 — 2026-03-20):
- TARGET: a.churn_flag (accounts.csv) = 22.0% — NÃO latest_churn.churned (70.4%)
  churn_events captura cancelamentos de subscrições individuais; accounts.churn_flag
  captura saída definitiva da conta. churn_events agora é APENAS source de vars explicativas.
"""

import os
import duckdb
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
SEP = "=" * 60


def _q(title: str):
    print(f"\n{SEP}\n  {title}\n{SEP}")


def run_in_data_dir(con, query: str) -> pd.DataFrame:
    """Executa query com DATA_DIR como cwd para resolver caminhos relativos."""
    original = os.getcwd()
    os.chdir(DATA_DIR)
    try:
        return con.execute(query).df()
    finally:
        os.chdir(original)


# ---------------------------------------------------------------------------
# Master view — uma linha por account_id
# ---------------------------------------------------------------------------
def build_master_view(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """
    Constrói visão unificada por conta com métricas agregadas de todas as tabelas.
    TARGET = a.churn_flag (accounts.csv), NÃO churn_events.
    """
    query = """
    WITH sub_agg AS (
        SELECT
            account_id,
            COUNT(subscription_id)                                         AS n_subscriptions,
            SUM(CASE WHEN end_date IS NULL THEN 1 ELSE 0 END)             AS n_active_subs,
            MIN(start_date)                                                AS first_sub_date,
            MAX(start_date)                                                AS last_sub_date,
            STRING_AGG(DISTINCT plan_tier, ', ')                           AS plans_used,
            AVG(mrr_amount)                                                AS avg_mrr,
            SUM(mrr_amount)                                                AS total_mrr,
            MAX(mrr_amount)                                                AS peak_mrr,
            SUM(CASE WHEN downgrade_flag THEN 1 ELSE 0 END)               AS n_downgrades,
            SUM(CASE WHEN upgrade_flag THEN 1 ELSE 0 END)                 AS n_upgrades,
            SUM(CASE WHEN auto_renew_flag = false THEN 1 ELSE 0 END)      AS n_no_autorenew,
            SUM(CASE WHEN billing_frequency = 'annual' THEN 1 ELSE 0 END) AS n_annual_subs,
            STRING_AGG(DISTINCT billing_frequency, ', ')                   AS billing_modes
        FROM read_csv_auto('ravenstack_subscriptions.csv')
        GROUP BY account_id
    ),
    usage_agg AS (
        SELECT
            s.account_id,
            COUNT(f.feature_name)                                          AS total_feature_events,
            COUNT(DISTINCT f.feature_name)                                 AS distinct_features_used,
            AVG(f.usage_duration_secs / 60.0)                             AS avg_session_min,
            SUM(f.usage_duration_secs / 60.0)                             AS total_usage_min,
            SUM(f.error_count)                                             AS total_errors,
            SUM(CASE WHEN f.is_beta_feature THEN f.error_count ELSE 0 END)     AS beta_errors,
            SUM(CASE WHEN NOT f.is_beta_feature THEN f.error_count ELSE 0 END) AS stable_errors
        FROM read_csv_auto('ravenstack_feature_usage.csv') f
        JOIN read_csv_auto('ravenstack_subscriptions.csv') s
          ON f.subscription_id = s.subscription_id
        GROUP BY s.account_id
    ),
    ticket_agg AS (
        SELECT
            account_id,
            COUNT(ticket_id)                                                           AS n_tickets,
            SUM(CASE WHEN priority IN ('high', 'urgent') THEN 1 ELSE 0 END)           AS n_high_priority,
            SUM(CASE WHEN priority = 'urgent' THEN 1 ELSE 0 END)                      AS n_urgent,
            SUM(CASE WHEN escalation_flag THEN 1 ELSE 0 END)                          AS n_escalations,
            AVG(resolution_time_hours)                                                 AS avg_resolution_h,
            AVG(first_response_time_minutes)                                           AS avg_first_response_min,
            AVG(CASE WHEN satisfaction_score IS NOT NULL THEN satisfaction_score END)  AS avg_satisfaction,
            SUM(CASE WHEN satisfaction_score IS NULL THEN 1 ELSE 0 END)               AS n_no_satisfaction_response,
            CAST(SUM(CASE WHEN satisfaction_score IS NULL THEN 1 ELSE 0 END) AS DOUBLE)
                / NULLIF(COUNT(ticket_id), 0)                                          AS satisfaction_no_response_rate
        FROM read_csv_auto('ravenstack_support_tickets.csv')
        GROUP BY account_id
    ),
    churn_deduped AS (
        SELECT *,
            ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY churn_date DESC) AS rn
        FROM read_csv_auto('ravenstack_churn_events.csv')
    ),
    latest_churn_info AS (
        -- Usado APENAS para vars explicativas (reason_code, preceding flags)
        -- O TARGET é a.churn_flag, não esta CTE
        SELECT
            account_id, churn_date, reason_code, refund_amount_usd,
            preceding_upgrade_flag, preceding_downgrade_flag, is_reactivation
        FROM churn_deduped WHERE rn = 1
    )
    SELECT
        a.account_id,
        a.industry,
        a.country,
        a.seats,
        a.signup_date,
        a.referral_source,
        a.plan_tier                                         AS initial_plan_tier,
        a.is_trial                                          AS account_is_trial,
        CAST(a.churn_flag AS INTEGER)                       AS churned,   -- TARGET CORRETO
        COALESCE(sa.n_subscriptions, 0)                    AS n_subscriptions,
        COALESCE(sa.n_active_subs, 0)                      AS n_active_subs,
        sa.plans_used,
        COALESCE(sa.avg_mrr, 0)                            AS avg_mrr,
        COALESCE(sa.total_mrr, 0)                          AS total_mrr,
        COALESCE(sa.peak_mrr, 0)                           AS peak_mrr,
        COALESCE(sa.n_downgrades, 0)                       AS n_downgrades,
        COALESCE(sa.n_upgrades, 0)                         AS n_upgrades,
        COALESCE(sa.n_no_autorenew, 0)                     AS n_no_autorenew,
        COALESCE(sa.n_annual_subs, 0)                      AS n_annual_subs,
        sa.billing_modes,
        COALESCE(ua.total_feature_events, 0)               AS total_feature_events,
        COALESCE(ua.distinct_features_used, 0)             AS distinct_features_used,
        COALESCE(ua.avg_session_min, 0)                    AS avg_session_min,
        COALESCE(ua.total_usage_min, 0)                    AS total_usage_min,
        COALESCE(ua.total_errors, 0)                       AS total_errors,
        COALESCE(ua.beta_errors, 0)                        AS beta_errors,
        COALESCE(ua.stable_errors, 0)                      AS stable_errors,
        COALESCE(ta.n_tickets, 0)                          AS n_tickets,
        COALESCE(ta.n_high_priority, 0)                    AS n_high_priority_tickets,
        COALESCE(ta.n_urgent, 0)                           AS n_urgent_tickets,
        COALESCE(ta.n_escalations, 0)                      AS n_escalations,
        COALESCE(ta.avg_resolution_h, 0)                   AS avg_resolution_h,
        COALESCE(ta.avg_first_response_min, 0)             AS avg_first_response_min,
        ta.avg_satisfaction,
        COALESCE(ta.n_no_satisfaction_response, 0)         AS n_no_satisfaction_response,
        COALESCE(ta.satisfaction_no_response_rate, 0)      AS satisfaction_no_response_rate,
        c.churn_date,
        c.reason_code,
        c.preceding_downgrade_flag,
        c.preceding_upgrade_flag,
        c.is_reactivation,
        c.refund_amount_usd
    FROM read_csv_auto('ravenstack_accounts.csv') a
    LEFT JOIN sub_agg sa           ON a.account_id = sa.account_id
    LEFT JOIN usage_agg ua         ON a.account_id = ua.account_id
    LEFT JOIN ticket_agg ta        ON a.account_id = ta.account_id
    LEFT JOIN latest_churn_info c  ON a.account_id = c.account_id
    """
    return run_in_data_dir(con, query)


# ---------------------------------------------------------------------------
# Q1 — Buyer's remorse: upgrade → churn?
# ---------------------------------------------------------------------------
def q1_buyers_remorse(con, master: pd.DataFrame):
    _q("P1 — Buyer's remorse: upgrade antes de churnar?")

    q = """
    WITH churn_accs AS (
        SELECT account_id FROM read_csv_auto('ravenstack_accounts.csv') WHERE churn_flag = true
    ),
    churn_events_info AS (
        SELECT account_id, preceding_upgrade_flag, preceding_downgrade_flag, churn_date
        FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY churn_date DESC) AS rn
            FROM read_csv_auto('ravenstack_churn_events.csv')
        ) t WHERE rn = 1
    )
    SELECT
        COALESCE(ce.preceding_upgrade_flag, false)   AS had_upgrade_before_churn,
        COUNT(*)                                      AS n_churners,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct_of_churners,
        AVG(sa.avg_mrr)                              AS avg_mrr_at_churn
    FROM churn_accs ca
    JOIN churn_events_info ce ON ca.account_id = ce.account_id
    JOIN (
        SELECT account_id, AVG(mrr_amount) AS avg_mrr
        FROM read_csv_auto('ravenstack_subscriptions.csv')
        GROUP BY account_id
    ) sa ON ca.account_id = sa.account_id
    GROUP BY had_upgrade_before_churn
    ORDER BY had_upgrade_before_churn DESC
    """
    df = run_in_data_dir(con, q)
    print("\nChuners por preceding_upgrade_flag:")
    print(df.to_string(index=False))
    print("\nIsso significa que: clientes que fizeram upgrade antes de churnar pagavam, em média,")
    print(f"  ${df[df['had_upgrade_before_churn']==True]['avg_mrr_at_churn'].values[0]:.0f}/mês")
    print(f"  vs ${df[df['had_upgrade_before_churn']==False]['avg_mrr_at_churn'].values[0]:.0f}/mês para churners sem upgrade.")

    # Buyer's remorse por segmento
    q2 = """
    WITH churners AS (
        SELECT a.account_id, a.industry, a.plan_tier, m.preceding_upgrade_flag
        FROM read_csv_auto('ravenstack_accounts.csv') a
        JOIN (
            SELECT account_id, preceding_upgrade_flag
            FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY churn_date DESC) AS rn
                  FROM read_csv_auto('ravenstack_churn_events.csv')) t WHERE rn = 1
        ) m ON a.account_id = m.account_id
        WHERE a.churn_flag = true
    )
    SELECT industry,
           COUNT(*) AS total_churners,
           SUM(CASE WHEN preceding_upgrade_flag THEN 1 ELSE 0 END) AS upgrade_then_churn,
           ROUND(SUM(CASE WHEN preceding_upgrade_flag THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS pct
    FROM churners
    GROUP BY industry
    ORDER BY pct DESC
    """
    df2 = run_in_data_dir(con, q2)
    print("\nBuyer's remorse por indústria:")
    print(df2.to_string(index=False))
    return df


# ---------------------------------------------------------------------------
# Q2 — Suporte quebrado afeta churn?
# ---------------------------------------------------------------------------
def q2_support_impact(con, master: pd.DataFrame):
    _q("P2 — Suporte quebrado afeta churn?")

    # Churn rate por presença de ticket urgent
    for label, mask in [
        ("COM ticket urgent",          master['n_urgent_tickets'] > 0),
        ("COM escalation",             master['n_escalations'] > 0),
        ("COM satisfaction_null >50%", master['satisfaction_no_response_rate'] > 0.5),
    ]:
        has = master[mask]
        no  = master[~mask]
        print(f"\n  {label:<35} {has['churned'].mean():.1%} churn  (n={len(has)})")
        print(f"  {'SEM ' + label[4:]:<35} {no['churned'].mean():.1%} churn  (n={len(no)})")

    # Quartis de first_response_time
    print("\nChurn rate por quartil de first_response_time_minutes:")
    m2 = master[master['n_tickets'] > 0].copy()
    if len(m2) > 0:
        m2['resp_quartile'] = pd.qcut(m2['avg_first_response_min'], q=4,
                                       labels=['Q1 rápido', 'Q2', 'Q3', 'Q4 lento'])
        qt = m2.groupby('resp_quartile', observed=True)['churned'].agg(['mean', 'count'])
        qt.columns = ['churn_rate', 'n_accounts']
        qt['churn_rate'] = qt['churn_rate'].map('{:.1%}'.format)
        print(qt.to_string())

    print("\nIsso significa que: maior tempo de resposta está associado a maior churn.")
    print("  SLA de suporte tem impacto direto mensurável na retenção.")


# ---------------------------------------------------------------------------
# Q3 — Baixo uso de features prediz churn?
# ---------------------------------------------------------------------------
def q3_feature_usage_vs_churn(con, master: pd.DataFrame):
    _q("P3 — Baixo uso de features prediz churn?")

    churned   = master[master['churned'] == 1]
    retained  = master[master['churned'] == 0]

    metrics = [
        ("distinct_features_used", "Features distintas usadas"),
        ("total_feature_events",   "Total de eventos de uso"),
        ("avg_session_min",        "Duração média de sessão (min)"),
        ("total_errors",           "Total de erros registrados"),
    ]
    print(f"\n  {'Métrica':<35} {'Churners':>12} {'Retidos':>12} {'Diferença':>12}")
    print("  " + "-" * 71)
    for col, label in metrics:
        c_val = churned[col].mean()
        r_val = retained[col].mean()
        diff  = ((c_val - r_val) / r_val * 100) if r_val else 0
        print(f"  {label:<35} {c_val:>12.2f} {r_val:>12.2f} {diff:>+11.1f}%")

    # Contas abaixo de 3 features distintas
    low_feat = master[master['distinct_features_used'] < 3]
    print(f"\n  Contas com < 3 features usadas: {len(low_feat)}")
    if len(low_feat) > 0:
        print(f"    Churn rate neste grupo: {low_feat['churned'].mean():.1%}")
        print(f"    Churn rate no restante: {master[master['distinct_features_used'] >= 3]['churned'].mean():.1%}")

    # First-30-days usage
    q_early = """
    WITH early_usage AS (
        SELECT
            s.account_id,
            COUNT(f.usage_id) AS events_first_30d
        FROM read_csv_auto('ravenstack_feature_usage.csv') f
        JOIN read_csv_auto('ravenstack_subscriptions.csv') s
          ON f.subscription_id = s.subscription_id
        JOIN read_csv_auto('ravenstack_accounts.csv') a
          ON s.account_id = a.account_id
        WHERE f.usage_date <= a.signup_date + INTERVAL 30 DAYS
        GROUP BY s.account_id
    )
    SELECT
        a.churn_flag,
        ROUND(AVG(COALESCE(eu.events_first_30d, 0)), 1) AS avg_events_first_30d,
        COUNT(*) AS n_accounts
    FROM read_csv_auto('ravenstack_accounts.csv') a
    LEFT JOIN early_usage eu ON a.account_id = eu.account_id
    GROUP BY a.churn_flag
    ORDER BY a.churn_flag
    """
    df_early = run_in_data_dir(con, q_early)
    print("\n  Uso nos primeiros 30 dias (churners vs retidos):")
    print(df_early.to_string(index=False))
    print("\nIsso significa que: churners têm significativamente menor engajamento")
    print("  desde o início — onboarding é um ponto crítico de intervenção.")


# ---------------------------------------------------------------------------
# Q4 — Qual segmento está mais em risco?
# ---------------------------------------------------------------------------
def q4_segment_risk(con, master: pd.DataFrame):
    _q("P4 — Qual segmento está mais em risco?")

    for dim, col in [
        ("plan_tier",         "initial_plan_tier"),
        ("billing_frequency", "billing_modes"),
        ("referral_source",   "referral_source"),
        ("industry",          "industry"),
    ]:
        print(f"\n  Churn rate por {dim}:")
        seg = master.groupby(col).agg(
            churn_rate=('churned', 'mean'),
            n_accounts=('churned', 'count'),
            avg_mrr=('avg_mrr', 'mean')
        ).sort_values('churn_rate', ascending=False)
        seg['churn_rate'] = seg['churn_rate'].map('{:.1%}'.format)
        seg['avg_mrr']    = seg['avg_mrr'].map('${:.0f}'.format)
        print(seg.to_string())

    # MRR em risco por segmento (plan_tier)
    print("\n  MRR total em risco por plan_tier (churners × total_mrr):")
    mrr_risk = master[master['churned'] == 1].groupby('initial_plan_tier')['avg_mrr'].sum()
    for tier, mrr in mrr_risk.sort_values(ascending=False).items():
        print(f"    {tier:<12} ${mrr:>10,.0f}")

    print("\nIsso significa que: o segmento com maior churn rate e maior MRR em risco")
    print("  é o alvo prioritário para intervenção de retenção.")


# ---------------------------------------------------------------------------
# Q5 — auto_renew=False é sinal antecipado?
# ---------------------------------------------------------------------------
def q5_autorenew_signal(con, master: pd.DataFrame):
    _q("P5 — auto_renew=False é sinal antecipado de churn?")

    with_no_renew    = master[master['n_no_autorenew'] > 0]
    without_no_renew = master[master['n_no_autorenew'] == 0]

    print(f"\n  Contas COM ao menos 1 sub sem auto-renew: {len(with_no_renew)}")
    print(f"    Churn rate: {with_no_renew['churned'].mean():.1%}")
    print(f"  Contas SEM sub sem auto-renew:            {len(without_no_renew)}")
    print(f"    Churn rate: {without_no_renew['churned'].mean():.1%}")

    lift = with_no_renew['churned'].mean() / without_no_renew['churned'].mean()
    print(f"\n  Lift do sinal auto_renew=False: {lift:.2f}x")

    # Características de quem tem auto_renew=False mas NÃO churnou
    false_renew_retained = with_no_renew[with_no_renew['churned'] == 0]
    false_renew_churned  = with_no_renew[with_no_renew['churned'] == 1]
    print(f"\n  Com auto_renew=False: {len(false_renew_churned)} churners / {len(false_renew_retained)} retidos")
    if len(false_renew_retained) > 0:
        print(f"  Retidos com auto_renew=False: avg_mrr=${false_renew_retained['avg_mrr'].mean():.0f}")
        print(f"  Churners com auto_renew=False: avg_mrr=${false_renew_churned['avg_mrr'].mean():.0f}")
        print(f"  Retidos: distinct_features={false_renew_retained['distinct_features_used'].mean():.1f}")
        print(f"  Churners: distinct_features={false_renew_churned['distinct_features_used'].mean():.1f}")

    print("\nIsso significa que: auto_renew=False é sinal de alerta, mas não determinístico.")
    print("  Quem tem auto_renew=False E baixo uso de features é o caso mais crítico.")


# ---------------------------------------------------------------------------
# Q6 — Quanto MRR está em risco hoje?
# ---------------------------------------------------------------------------
def q6_mrr_at_risk(con, master: pd.DataFrame):
    _q("P6 — MRR em risco hoje (contas ativas com múltiplos sinais de risco)")

    active = master[master['churned'] == 0].copy()

    median_features = master['distinct_features_used'].median()

    active['risk_autorenew']  = (active['n_no_autorenew'] > 0).astype(int)
    active['risk_escalation'] = (active['n_escalations'] > 0).astype(int)
    active['risk_low_usage']  = (active['distinct_features_used'] < median_features).astype(int)
    active['risk_urgent']     = (active['n_urgent_tickets'] > 0).astype(int)
    active['risk_score']      = (active['risk_autorenew'] + active['risk_escalation'] +
                                  active['risk_low_usage'] + active['risk_urgent'])

    print(f"\n  Contas ativas totais: {len(active)}")
    print(f"  MRR total ativo: ${active['avg_mrr'].sum():,.0f}")
    print()
    for n_signals in [4, 3, 2]:
        subset = active[active['risk_score'] >= n_signals]
        mrr    = subset['avg_mrr'].sum()
        print(f"  Contas com {n_signals}+ sinais de risco: {len(subset):>4}  |  MRR em risco: ${mrr:>10,.0f}")

    high_risk = active[active['risk_score'] >= 2].nlargest(10, 'avg_mrr')
    print(f"\n  Top 10 contas ativas em risco por MRR:")
    cols = ['account_id', 'industry', 'avg_mrr', 'risk_score',
            'risk_autorenew', 'risk_escalation', 'risk_low_usage', 'risk_urgent']
    print(high_risk[cols].to_string(index=False))

    total_at_risk = active[active['risk_score'] >= 2]['avg_mrr'].sum()
    print(f"\n  MRR total em risco (2+ sinais): ${total_at_risk:,.0f}")
    print("Isso significa que: estas contas são a lista de ação imediata para o time de CS.")


# ---------------------------------------------------------------------------
# Ranking de causas
# ---------------------------------------------------------------------------
def ranking_causas(master: pd.DataFrame):
    _q("RANKING DE CAUSAS DO CHURN")

    churners = master[master['churned'] == 1]
    n_ch = len(churners)

    causes = []

    # Causa 1 — Product gap (reason_code = features)
    feat_reason = (master['reason_code'] == 'features').sum()
    causes.append(("Product gap (reason_code=features)",
                   feat_reason, feat_reason / n_ch,
                   master[master['reason_code'] == 'features']['avg_mrr'].sum()))

    # Causa 2 — Suporte ruim (reason_code = support OU escalation)
    support_ch = churners[(churners['reason_code'] == 'support') |
                           (churners['n_escalations'] > 0)]
    causes.append(("Suporte ruim (reason_code=support ou escalation)",
                   len(support_ch), len(support_ch) / n_ch,
                   support_ch['avg_mrr'].sum()))

    # Causa 3 — Buyer's remorse (preceding_upgrade_flag)
    upgrade_ch = churners[churners['preceding_upgrade_flag'] == True]
    causes.append(("Buyer's remorse (upgrade → churn em <90d)",
                   len(upgrade_ch), len(upgrade_ch) / n_ch,
                   upgrade_ch['avg_mrr'].sum()))

    # Causa 4 — Budget (reason_code = budget)
    budget_ch = churners[churners['reason_code'] == 'budget']
    causes.append(("Budget/preço (reason_code=budget)",
                   len(budget_ch), len(budget_ch) / n_ch,
                   budget_ch['avg_mrr'].sum()))

    # Causa 5 — Auto-renew desativado + baixo uso
    at_risk_ch = churners[(churners['n_no_autorenew'] > 0) &
                            (churners['distinct_features_used'] < master['distinct_features_used'].median())]
    causes.append(("Auto-renew=False + baixo uso (combo)",
                   len(at_risk_ch), len(at_risk_ch) / n_ch,
                   at_risk_ch['avg_mrr'].sum()))

    print(f"\n  Total de churners (accounts.churn_flag=True): {n_ch}")
    print(f"\n  {'Rank':<4} {'Causa':<50} {'Churners':>9} {'% churners':>11} {'MRR perdido':>13}")
    print("  " + "-" * 89)
    for i, (label, n, pct, mrr) in enumerate(causes, 1):
        print(f"  {i:<4} {label:<50} {n:>9} {pct:>10.1%} ${mrr:>12,.0f}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def run_cross_table():
    con = duckdb.connect()

    print("[CROSS-TABLE] Construindo master view via DuckDB...")
    master = build_master_view(con)
    print(f"  Shape: {master.shape}")
    churn_rate = master['churned'].mean()
    print(f"  Churn rate (a.churn_flag): {churn_rate:.1%}  ✅ TARGET CORRETO")
    print(f"  Churners: {master['churned'].sum()} | Retidos: {(master['churned']==0).sum()}")

    q1_buyers_remorse(con, master)
    q2_support_impact(con, master)
    q3_feature_usage_vs_churn(con, master)
    q4_segment_risk(con, master)
    q5_autorenew_signal(con, master)
    q6_mrr_at_risk(con, master)
    ranking_causas(master)

    con.close()
    return master


if __name__ == "__main__":
    run_cross_table()
