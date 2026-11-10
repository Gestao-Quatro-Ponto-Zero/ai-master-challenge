"""Mede o sinal de cada variável candidata a entrar no score (Won x Lost).

Rodar depois de data/clean.py:  python solution/analysis/signal.py
Grava tabelas em analysis/tables/ e um resumo em analysis/signal_summary.json.
Só pandas e numpy (o p-valor do qui-quadrado é calculado aqui, sem scipy).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
CLEAN = HERE.parent / "data" / "clean"
TABLES = HERE / "tables"
MIN_N = 30          # abaixo disso o grupo é marcado como "poucos casos"
SEED = 7


# ---------------------------------------------------------------- estatística
def wilson(k: float, n: float, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (math.nan, math.nan)
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (mid - half, mid + half)


def _gammaincc(a: float, x: float) -> float:
    """Q(a, x) regularizada (Numerical Recipes: série ou fração contínua)."""
    if x <= 0:
        return 1.0
    gln = math.lgamma(a)
    if x < a + 1:
        ap, s, d = a, 1.0 / a, 1.0 / a
        for _ in range(10_000):
            ap += 1
            d *= x / ap
            s += d
            if abs(d) < abs(s) * 1e-15:
                break
        return 1.0 - s * math.exp(-x + a * math.log(x) - gln)
    b, c, d = x + 1 - a, 1e300, 1 / (x + 1 - a)
    h = d
    for i in range(1, 10_000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = 1e-300 if abs(d) < 1e-300 else d
        c = b + an / c
        c = 1e-300 if abs(c) < 1e-300 else c
        d = 1 / d
        h *= d * c
        if abs(d * c - 1) < 1e-15:
            break
    return math.exp(-x + a * math.log(x) - gln) * h


def chi2_test(groups: pd.Series, y: pd.Series) -> dict:
    tab = pd.crosstab(groups, y)
    obs = tab.to_numpy(float)
    exp = obs.sum(1, keepdims=True) * obs.sum(0, keepdims=True) / obs.sum()
    stat = float(((obs - exp) ** 2 / exp).sum())
    dof = (obs.shape[0] - 1) * (obs.shape[1] - 1)
    p = _gammaincc(dof / 2, stat / 2) if dof > 0 else math.nan
    v = math.sqrt(stat / (obs.sum() * (min(obs.shape) - 1))) if dof > 0 else math.nan
    return {"chi2": round(stat, 2), "dof": dof, "p_value": p, "cramers_v": round(v, 4),
            "min_expected": round(float(exp.min()), 1)}


def permutation_p(groups: pd.Series, y: pd.Series, n_perm: int = 2000) -> float:
    """p-valor por permutação do qui-quadrado (confere o analítico)."""
    keep = groups.notna().to_numpy()
    codes = pd.factorize(groups[keep])[0]
    yy = y[keep].to_numpy(int)
    k = codes.max() + 1
    n_g = np.bincount(codes, minlength=k).astype(float)
    p0 = yy.mean()

    def stat(v):
        w = np.bincount(codes, weights=v, minlength=k)
        e1, e0 = n_g * p0, n_g * (1 - p0)
        return (((w - e1) ** 2) / e1 + (((n_g - w) - e0) ** 2) / e0).sum()

    s0 = stat(yy)
    rng = np.random.default_rng(SEED)
    hits = sum(stat(rng.permutation(yy)) >= s0 for _ in range(n_perm))
    return (hits + 1) / (n_perm + 1)


def mann_whitney(a: np.ndarray, b: np.ndarray) -> dict:
    """Teste U (aproximação normal, com correção de empates)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    n1, n2 = len(a), len(b)
    r = pd.Series(np.concatenate([a, b])).rank().to_numpy()
    u = r[:n1].sum() - n1 * (n1 + 1) / 2
    t = pd.Series(np.concatenate([a, b])).value_counts().to_numpy(float)
    n = n1 + n2
    sd = math.sqrt(n1 * n2 / 12 * ((n + 1) - (t ** 3 - t).sum() / (n * (n - 1))))
    z = (u - n1 * n2 / 2) / sd
    p = math.erfc(abs(z) / math.sqrt(2))
    return {"U": float(u), "z": round(z, 3), "p_value": p,
            "prob_a_gt_b": round(u / (n1 * n2), 4)}


# ---------------------------------------------------------------- tabelas
def win_table(df: pd.DataFrame, by, overall: float) -> pd.DataFrame:
    g = df.groupby(by, observed=True)["won"].agg(n="count", won="sum").reset_index()
    g["win_rate"] = g["won"] / g["n"]
    ci = [wilson(k, n) for k, n in zip(g["won"], g["n"])]
    g["ci_low"] = [c[0] for c in ci]
    g["ci_high"] = [c[1] for c in ci]
    g["diff_vs_overall_pp"] = (g["win_rate"] - overall) * 100
    g["ci_excludes_overall"] = (g["ci_low"] > overall) | (g["ci_high"] < overall)
    g["poucos_casos"] = g["n"] < MIN_N
    return g.sort_values("win_rate", ascending=False)


def main() -> None:
    TABLES.mkdir(exist_ok=True)
    deals = pd.read_csv(CLEAN / "deals.csv", parse_dates=["engage_date", "close_date"])
    ref = pd.Timestamp(json.loads((CLEAN / "cleaning_report.json").read_text("utf-8"))["reference_date"])
    closed = deals[deals["won"].notna()].copy()
    closed["won"] = closed["won"].astype(int)
    overall = closed["won"].mean()

    # variáveis derivadas só para análise
    closed["us_hq"] = np.where(closed["office_location"] == "United States", "EUA", "fora dos EUA")
    closed["is_subsidiary"] = np.where(closed["parent_company"] != closed["account"], "subsidiária", "independente")
    closed["company_age_band"] = pd.cut(ref.year - closed["year_established"], [0, 15, 25, 100],
                                        labels=["<=15 anos", "16-25 anos", ">25 anos"]).astype(str)
    closed["engage_quarter"] = closed["engage_date"].dt.to_period("Q").astype(str)
    closed["close_quarter"] = closed["close_date"].dt.to_period("Q").astype(str)
    closed["close_month"] = closed["close_date"].dt.month
    closed["engage_weekday"] = closed["engage_date"].dt.day_name()
    closed["price_band"] = pd.cut(closed["list_price"], [0, 600, 1200, 6000, 1e6],
                                  labels=["<=600", "601-1200", "1201-6000", ">6000"]).astype(str)
    closed["agent_x_product"] = closed["sales_agent"] + " | " + closed["product"]
    closed["agent_x_sector"] = closed["sales_agent"] + " | " + closed["sector"]

    variables = {
        "product": "product", "series": "series", "price_band": "price_band",
        "sector": "sector", "revenue_band": "revenue_band", "employees_band": "employees_band",
        "us_hq": "us_hq", "is_subsidiary": "is_subsidiary", "company_age_band": "company_age_band",
        "account": "account", "sales_agent": "sales_agent", "manager": "manager",
        "regional_office": "regional_office", "agent_x_product": "agent_x_product",
        "agent_x_sector": "agent_x_sector",
        "engage_quarter": "engage_quarter", "close_quarter": "close_quarter",
        "engage_weekday": "engage_weekday",
    }
    summary = {"reference_date": ref.date().isoformat(), "closed_deals": int(len(closed)),
               "overall_win_rate": round(overall, 4),
               "overall_ci": [round(x, 4) for x in wilson(closed["won"].sum(), len(closed))],
               "variables": {}}
    n_tests = len(variables)
    for name, col in variables.items():
        t = win_table(closed, col, overall)
        t.to_csv(TABLES / f"win_rate_by_{name}.csv", index=False, lineterminator="\n")
        test = chi2_test(closed[col], closed["won"])
        test["p_bonferroni"] = min(1.0, test["p_value"] * n_tests)
        if t.shape[0] <= 200:
            test["p_permutation"] = permutation_p(closed[col], closed["won"])
        test.update({
            "groups": int(len(t)),
            "groups_poucos_casos": int(t["poucos_casos"].sum()),
            "groups_ci_excludes_overall": int(t["ci_excludes_overall"].sum()),
            "win_rate_min": round(float(t["win_rate"].min()), 4),
            "win_rate_max": round(float(t["win_rate"].max()), 4),
            "win_rate_min_n30": round(float(t.loc[~t["poucos_casos"], "win_rate"].min()), 4) if (~t["poucos_casos"]).any() else None,
            "win_rate_max_n30": round(float(t.loc[~t["poucos_casos"], "win_rate"].max()), 4) if (~t["poucos_casos"]).any() else None,
        })
        summary["variables"][name] = test

    # deals por conta: o mix de produto/vendedor muda o resultado da conta?
    # (efeito do vendedor controlando pelo produto: win rate esperado pelo mix)
    prod_rate = closed.groupby("product")["won"].mean()
    closed["exp_by_product"] = closed["product"].map(prod_rate)
    ag = closed.groupby("sales_agent").agg(n=("won", "size"), won=("won", "sum"),
                                           expected=("exp_by_product", "sum")).reset_index()
    ag["win_rate"] = ag["won"] / ag["n"]
    ag["lift_vs_product_mix_pp"] = (ag["won"] - ag["expected"]) / ag["n"] * 100
    ag.sort_values("lift_vs_product_mix_pp", ascending=False).to_csv(
        TABLES / "agent_lift_vs_product_mix.csv", index=False, lineterminator="\n")

    # ------------------------------------------------------------ ciclo
    cyc = closed.groupby(["product", "deal_stage"])["cycle_days"].describe(
        percentiles=[.25, .5, .75, .9]).reset_index()
    cyc.to_csv(TABLES / "cycle_by_product_and_outcome.csv", index=False, lineterminator="\n")
    cyc_all = closed.groupby("deal_stage")["cycle_days"].describe(percentiles=[.25, .5, .75, .9, .95])
    cyc_all.to_csv(TABLES / "cycle_by_outcome.csv", lineterminator="\n")
    mw = mann_whitney(closed.loc[closed.won == 1, "cycle_days"], closed.loc[closed.won == 0, "cycle_days"])
    summary["cycle"] = {
        "won_median": float(closed.loc[closed.won == 1, "cycle_days"].median()),
        "lost_median": float(closed.loc[closed.won == 0, "cycle_days"].median()),
        "won_p90": float(closed.loc[closed.won == 1, "cycle_days"].quantile(.9)),
        "max_closed_cycle": int(closed["cycle_days"].max()),
        "mann_whitney_won_vs_lost": mw,
        "product_effect_on_cycle_won_kruskal_like": None,
    }
    # ciclo por produto (só Won) — há diferença real entre produtos?
    medians = closed[closed.won == 1].groupby("product")["cycle_days"].median()
    summary["cycle"]["won_median_by_product"] = medians.round(1).to_dict()

    bins = [-1, 7, 30, 60, 90, 120, 10_000]
    labels = ["0-7", "8-30", "31-60", "61-90", "91-120", ">120"]
    closed["cycle_bucket"] = pd.cut(closed["cycle_days"], bins, labels=labels).astype(str)
    cb = win_table(closed, "cycle_bucket", overall)
    cb["order"] = cb["cycle_bucket"].map({l: i for i, l in enumerate(labels)})
    cb.sort_values("order").drop(columns="order").to_csv(
        TABLES / "win_rate_by_cycle_bucket.csv", index=False, lineterminator="\n")
    summary["variables"]["cycle_bucket"] = chi2_test(closed["cycle_bucket"], closed["won"])

    # "já está aberto há t dias": win rate final dos deals que duraram >= t
    surv = []
    for t in [0, 15, 30, 45, 60, 75, 90, 105, 120]:
        s = closed[closed["cycle_days"] >= t]
        lo, hi = wilson(s["won"].sum(), len(s))
        surv.append({"open_at_least_days": t, "n": len(s), "win_rate": s["won"].mean(),
                     "ci_low": lo, "ci_high": hi})
    pd.DataFrame(surv).to_csv(TABLES / "win_rate_given_age.csv", index=False, lineterminator="\n")

    # truncamento: nenhum fechamento antes de 2017-03-01
    em = closed.groupby(closed["engage_date"].dt.to_period("M").astype(str)).agg(
        n=("won", "size"), win_rate=("won", "mean"),
        cycle_min=("cycle_days", "min"), cycle_median=("cycle_days", "median"))
    em.to_csv(TABLES / "by_engage_month.csv", lineterminator="\n")

    # ------------------------------------------------------------ robustez
    # Coorte sem viés de corte: engajados de 2017-03-01 a 2017-08-15
    # (antes disso faltam os fechamentos anteriores a março/2017; depois,
    #  os deals longos ainda estariam abertos em 31/12/2017).
    coh = closed[(closed["engage_date"] >= "2017-03-01") & (closed["engage_date"] <= "2017-08-15")].copy()
    coh["cycle_bucket2"] = pd.cut(coh["cycle_days"], [-1, 14, 10_000], labels=["0-14", "15+"]).astype(str)
    ctab = win_table(coh, "cycle_bucket2", coh["won"].mean())
    ctab.to_csv(TABLES / "cohort_win_rate_by_first_two_weeks.csv", index=False, lineterminator="\n")
    coh_surv = []
    for t in [0, 7, 15, 30, 60, 90, 120]:
        s = coh[coh["cycle_days"] >= t]
        lo, hi = wilson(s["won"].sum(), len(s))
        coh_surv.append({"open_at_least_days": t, "n": len(s), "win_rate": s["won"].mean(),
                         "ci_low": lo, "ci_high": hi})
    pd.DataFrame(coh_surv).to_csv(TABLES / "cohort_win_rate_given_age.csv", index=False, lineterminator="\n")
    summary["robustness"] = {
        "cohort": "engage 2017-03-01..2017-08-15",
        "cohort_n": int(len(coh)),
        "cohort_win_rate": round(float(coh["won"].mean()), 4),
        "cohort_first_two_weeks": {r["cycle_bucket2"]: {"n": int(r["n"]), "win_rate": round(r["win_rate"], 4),
                                                        "ci": [round(r["ci_low"], 4), round(r["ci_high"], 4)]}
                                   for _, r in ctab.iterrows()},
        "cohort_first_two_weeks_test": chi2_test(coh["cycle_bucket2"], coh["won"]),
    }

    # Mês dentro do trimestre (1º, 2º, 3º): regra de calendário do ciclo
    closed["close_month_in_q"] = (closed["close_date"].dt.month - 1) % 3 + 1
    coh["close_month_in_q"] = (coh["close_date"].dt.month - 1) % 3 + 1
    coh["engage_month_in_q"] = (coh["engage_date"].dt.month - 1) % 3 + 1
    miq = closed.groupby("close_month_in_q")["cycle_days"].agg(
        n="count", min="min", median="median", max="max").reset_index()
    miq.to_csv(TABLES / "cycle_by_close_month_in_quarter.csv", index=False, lineterminator="\n")
    summary["robustness"]["cycle_by_close_month_in_quarter"] = {
        int(r["close_month_in_q"]): {"n": int(r["n"]), "median": float(r["median"]), "max": int(r["max"])}
        for _, r in miq.iterrows()}

    # As 2 primeiras semanas controlando pelo calendário (coorte sem viés)
    def two_weeks_by(stratum: str) -> dict:
        rows, out = [], {}
        for m, g in coh.groupby(stratum):
            res = {}
            for label, s in g.groupby("cycle_bucket2"):
                lo, hi = wilson(s["won"].sum(), len(s))
                rows.append({stratum: m, "cycle_bucket2": label, "n": len(s),
                             "win_rate": s["won"].mean(), "ci_low": lo, "ci_high": hi})
                res[label] = {"n": int(len(s)), "win_rate": round(float(s["won"].mean()), 4)}
            if g["cycle_bucket2"].nunique() == 2:
                res["p_value"] = chi2_test(g["cycle_bucket2"], g["won"])["p_value"]
            out[int(m)] = res
        pd.DataFrame(rows).to_csv(TABLES / f"cohort_two_weeks_by_{stratum}.csv", index=False, lineterminator="\n")
        return out

    summary["robustness"]["two_weeks_by_close_month_in_quarter"] = two_weeks_by("close_month_in_q")
    summary["robustness"]["two_weeks_by_engage_month_in_quarter"] = two_weeks_by("engage_month_in_q")

    # Fim de trimestre: fechamentos em mar/jun/set/dez
    closed["quarter_end_month"] = np.where(closed["close_date"].dt.month.isin([3, 6, 9, 12]), "fim de trimestre", "meio de trimestre")
    qe = win_table(closed, "quarter_end_month", overall)
    qe.to_csv(TABLES / "win_rate_by_quarter_end_month.csv", index=False, lineterminator="\n")
    summary["robustness"]["quarter_end"] = {
        "win_rate": qe.set_index("quarter_end_month")["win_rate"].round(4).to_dict(),
        "n": qe.set_index("quarter_end_month")["n"].astype(int).to_dict(),
        "test": chi2_test(closed["quarter_end_month"], closed["won"]),
        "median_cycle": closed.groupby(["quarter_end_month", "deal_stage"])["cycle_days"].median().unstack().to_dict(),
        "share_of_won_closed_at_quarter_end": round(float((closed.loc[closed.won == 1, "quarter_end_month"] == "fim de trimestre").mean()), 4),
        "share_of_lost_closed_at_quarter_end": round(float((closed.loc[closed.won == 0, "quarter_end_month"] == "fim de trimestre").mean()), 4),
    }
    pd.crosstab(closed["close_date"].dt.to_period("M").astype(str), closed["deal_stage"]).to_csv(
        TABLES / "closes_by_month.csv", lineterminator="\n")

    # Fora do tempo: o histórico ANTERIOR da conta/vendedor prevê o próximo deal?
    oot = closed.sort_values(["close_date", "opportunity_id"]).copy()
    out_oot = {}
    for key, min_prior in [("account", 10), ("sales_agent", 30)]:
        prior_n = oot.groupby(key).cumcount()
        prior_rate = (oot.groupby(key)["won"].cumsum() - oot["won"]) / prior_n.replace(0, np.nan)
        m = prior_n >= min_prior
        q = pd.qcut(prior_rate[m], 4, labels=["Q1 (pior histórico)", "Q2", "Q3", "Q4 (melhor histórico)"])
        t = oot[m].groupby(q, observed=True)["won"].agg(n="count", win_rate="mean").reset_index()
        t.columns = ["prior_win_rate_quartile", "n", "next_deal_win_rate"]
        t.to_csv(TABLES / f"out_of_time_{key}_history.csv", index=False, lineterminator="\n")
        out_oot[key] = {"min_prior_deals": min_prior,
                        "next_deal_win_rate_by_prior_quartile": t.set_index("prior_win_rate_quartile")["next_deal_win_rate"].round(4).to_dict(),
                        "test": chi2_test(q.astype(str), oot.loc[m, "won"])}
    summary["robustness"]["out_of_time_history"] = out_oot

    # ------------------------------------------------------------ abertos
    opn = deals[deals["is_open"]].copy()
    eng = opn[opn["deal_stage"] == "Engaging"]
    p90 = summary["cycle"]["won_p90"]
    mx = summary["cycle"]["max_closed_cycle"]
    age = eng["days_since_engage"]
    summary["open"] = {
        "open": int(len(opn)),
        "prospecting": int((opn.deal_stage == "Prospecting").sum()),
        "engaging": int(len(eng)),
        "without_account": int(opn["account"].isna().sum()),
        "without_account_by_stage": opn[opn["account"].isna()]["deal_stage"].value_counts().to_dict(),
        "engaging_age_days": age.describe(percentiles=[.1, .25, .5, .75, .9]).round(1).to_dict(),
        "engaging_older_than_won_p90": int((age > p90).sum()),
        "engaging_older_than_max_closed_cycle": int((age > mx).sum()),
        "engaging_engaged_in_last_90d": int((age <= 90).sum()),
        "open_by_product": opn["product"].value_counts().to_dict(),
        "open_by_agent_top": opn["sales_agent"].value_counts().head(5).to_dict(),
        "open_by_agent_min": int(opn["sales_agent"].value_counts().min()),
        "open_by_agent_max": int(opn["sales_agent"].value_counts().max()),
    }
    age_b = pd.cut(age, [-1, 30, 60, 90, 120, 180, 365, 10_000],
                   labels=["0-30", "31-60", "61-90", "91-120", "121-180", "181-365", ">365"])
    age_b.value_counts().sort_index().to_csv(TABLES / "open_engaging_age.csv", lineterminator="\n")

    # ------------------------------------------------------------ valor
    won = closed[closed.won == 1]
    pr = won.groupby("product")["price_ratio"].describe(percentiles=[.05, .5, .95])
    pr.to_csv(TABLES / "won_price_ratio_by_product.csv", lineterminator="\n")
    summary["value"] = {
        "won_price_ratio": won["price_ratio"].describe(percentiles=[.01, .05, .5, .95, .99]).round(4).to_dict(),
        "won_value_by_product_mean": won.groupby("product")["close_value"].mean().round(0).to_dict(),
        "share_of_won_revenue_by_product": (won.groupby("product")["close_value"].sum()
                                            / won["close_value"].sum()).round(4).to_dict(),
    }

    # ------------------------------------------------------------ sinais de dado sintético
    wk = closed["engage_weekday"].value_counts(normalize=True).round(4).to_dict()
    deals_per_acc = closed.groupby("account").size()
    sim = []
    rng = np.random.default_rng(SEED)
    # dispersão do win rate por vendedor x o que se espera se todos tivessem a mesma taxa
    n_ag = closed.groupby("sales_agent").size().to_numpy()
    obs_sd = closed.groupby("sales_agent")["won"].mean().std()
    for _ in range(2000):
        sim.append(np.std(rng.binomial(n_ag, overall) / n_ag, ddof=1))
    summary["synthetic_checks"] = {
        "engage_weekday_share": wk,
        "weekend_share_engage": round(float(closed["engage_date"].dt.dayofweek.ge(5).mean()), 4),
        "weekend_share_close": round(float(closed["close_date"].dt.dayofweek.ge(5).mean()), 4),
        "deals_per_account": deals_per_acc.describe().round(1).to_dict(),
        "agent_winrate_sd_observed": round(float(obs_sd), 4),
        "agent_winrate_sd_if_all_equal_p50": round(float(np.median(sim)), 4),
        "agent_winrate_sd_if_all_equal_p95": round(float(np.quantile(sim, .95)), 4),
        "accounts_per_agent_median": float(closed.groupby("sales_agent")["account"].nunique().median()),
    }

    def _clean(o):
        if isinstance(o, dict):
            return {str(k): _clean(v) for k, v in o.items()}
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating, float)):
            return None if math.isnan(o) else float(o)
        return o

    (HERE / "signal_summary.json").write_text(
        json.dumps(_clean(summary), indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(_clean(summary), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
