"""Diagnóstico de churn da RavenStack: testa as hipóteses sobre o silver e gera evidências.

Uso (na raiz do monorepo):
    uv run --group analysis python analysis/diagnostico.py

Saídas:
    analysis/results/diagnostico.md   tabelas e números de cada hipótese
    analysis/results/numbers.json     números-chave (consumidos pelo relatório e pelo RAG)
    analysis/results/risk_accounts.csv contas ativas em risco, ordenadas por MRR em risco

Regras (skill churn-data-scientist): churn = churn_events; MRR vigente = assinatura ativa
mais recente da conta; toda comparação com tamanho de amostra e teste estatístico.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
from load import load_silver  # noqa: E402

OUT = Path(__file__).parent / "results"
END = pd.Timestamp("2024-12-31")  # fim dos dados
RNG = np.random.default_rng(42)
TENURE_BINS = [-1, 2, 5, 11, 30]
TENURE_LABELS = ["0-3m", "3-6m", "6-12m", "12m+"]

sections: list[str] = []
numbers: dict[str, object] = {}


def section(title: str, *parts: str) -> None:
    sections.append(f"## {title}\n\n" + "\n\n".join(parts))


def md(df: pd.DataFrame | pd.Series, digits: int = 3) -> str:
    return df.round(digits).to_markdown()


# --------------------------------------------------------------------------- base


def latest_sub_at(subs: pd.DataFrame, account_id: str, at: pd.Timestamp) -> pd.Series | None:
    """MRR vigente: assinatura ativa mais recente na data (fallback: a última iniciada antes)."""
    s = subs[(subs.account_id == account_id) & (subs.start_date <= at)]
    active = s[s.end_date.isna() | (s.end_date >= at)]
    pick = active if len(active) else s
    return None if pick.empty else pick.iloc[-1]


def enrich_churn(churn: pd.DataFrame, subs: pd.DataFrame, acc: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for a, dt in zip(churn.account_id, churn.churn_date, strict=True):
        s = latest_sub_at(subs, a, dt)
        rows.append(
            (np.nan, None, None)
            if s is None
            else (float(s.mrr_amount), s.plan_tier, s.billing_frequency)
        )
    churn[["mrr", "plan", "billing"]] = rows
    churn["q"] = churn.churn_date.dt.to_period("Q").astype(str)
    churn["nth"] = churn.groupby("account_id").cumcount() + 1
    churn = churn.merge(acc[["signup_date"]], left_on="account_id", right_index=True)
    churn["tenure_m"] = (churn.churn_date - churn.signup_date).dt.days / 30.44
    return churn


def account_month_panel(acc: pd.DataFrame, churn: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por conta × mês desde o cadastro; y = eventos de churn no mês."""
    months = pd.period_range("2023-01", "2024-12", freq="M")
    ev = churn.assign(m=churn.churn_date.dt.to_period("M")).groupby(["account_id", "m"]).size()
    first_churn = churn.groupby("account_id").churn_date.min().dt.to_period("M")
    rows = []
    for a, r in acc.iterrows():
        sm0 = r.signup_date.to_period("M")
        for m in months:
            if m < sm0:
                continue
            prior = a in first_churn.index and first_churn[a] < m
            rows.append((a, str(m.asfreq("Q")), (m - sm0).n, int(prior), int(ev.get((a, m), 0))))
    p = pd.DataFrame(rows, columns=["acc", "cal_q", "ten", "prior_churn", "y"])
    p["ten_b"] = pd.cut(p.ten, TENURE_BINS, labels=TENURE_LABELS)
    return p


# ---------------------------------------------------------------------- hipóteses


def h0_trend(acc: pd.DataFrame, churn: pd.DataFrame, subs: pd.DataFrame) -> None:
    by_q = churn.groupby("q").agg(eventos=("mrr", "size"), mrr_perdido=("mrr", "sum"))
    by_q["repetidos_2o+"] = churn[churn.nth > 1].groupby("q").size()
    for q in by_q.index:
        e = pd.Period(q).end_time
        by_q.loc[q, "contas_cadastradas"] = (acc.signup_date <= e).sum()
        by_q.loc[q, "assinaturas_ativas"] = (
            (subs.start_date <= e) & (subs.end_date.isna() | (subs.end_date >= e))
        ).sum()
    by_q["churn_por_100_contas"] = 100 * by_q.eventos / by_q.contas_cadastradas
    by_q["churn_por_100_assinaturas"] = 100 * by_q.eventos / by_q.assinaturas_ativas
    numbers["churn_events_2024q4"] = int(by_q.loc["2024Q4", "eventos"])
    numbers["churn_events_2023q4"] = int(by_q.loc["2023Q4", "eventos"])
    numbers["repeat_share_2024q4"] = round(
        float(by_q.loc["2024Q4", "repetidos_2o+"] / by_q.loc["2024Q4", "eventos"]), 3
    )
    section(
        "H0 — O churn subiu? (denominador importa)",
        md(by_q.fillna(0), 1),
        "Eventos sobem 6 → 251 por trimestre. Por conta cadastrada, a taxa sobe; por assinatura "
        "ativa, fica estável (~5%/tri desde 2023Q3) — as contas acumulam assinaturas. O CEO está "
        "certo sobre logos; a pergunta é *quem* está saindo (H8).",
    )


def h5_revenue(churn: pd.DataFrame) -> None:
    c = churn.dropna(subset=["mrr"])
    top = c.sort_values("mrr", ascending=False)
    n10 = int(len(c) * 0.1)
    share_top = float(top.head(n10).mrr.sum() / c.mrr.sum())
    by_plan = c.groupby("plan").agg(eventos=("mrr", "size"), mrr_perdido=("mrr", "sum"))
    by_plan["pct_eventos"] = by_plan.eventos / by_plan.eventos.sum()
    by_plan["pct_mrr"] = by_plan.mrr_perdido / by_plan.mrr_perdido.sum()
    numbers.update(
        mrr_lost_total=float(c.mrr.sum()),
        mrr_lost_top10pct_share=round(share_top, 3),
        enterprise_share_mrr_lost=round(float(by_plan.loc["Enterprise", "pct_mrr"]), 3),
        enterprise_share_events=round(float(by_plan.loc["Enterprise", "pct_eventos"]), 3),
        churn_events_without_subscription=int(churn.mrr.isna().sum()),
    )
    section(
        "H5 — Nem todo churn pesa igual",
        md(by_plan),
        f"MRR perdido somado nos eventos: US$ {c.mrr.sum():,.0f}. Os 10% maiores eventos "
        f"({n10}) concentram **{share_top:.0%}** do MRR perdido. Enterprise é "
        f"{by_plan.loc['Enterprise', 'pct_eventos']:.0%} dos eventos e "
        f"**{by_plan.loc['Enterprise', 'pct_mrr']:.0%}** do MRR perdido. "
        f"{int(churn.mrr.isna().sum())} eventos não têm assinatura anterior à data do churn "
        "(dado inconsistente; fora da soma).",
    )


def h1_support(acc: pd.DataFrame, churn: pd.DataFrame, tickets: pd.DataFrame) -> None:
    t = tickets.assign(has_csat=tickets.satisfaction_score.notna())
    churned = set(churn.account_id)
    per_acc = t.groupby("account_id").agg(
        tickets=("ticket_id", "size"),
        csat=("satisfaction_score", "mean"),
        taxa_resposta=("has_csat", "mean"),
        pct_escalado=("escalation_flag", "mean"),
        frt_mediano=("first_response_time_minutes", "median"),
    )
    per_acc = per_acc.reindex(acc.index).fillna({"tickets": 0})
    per_acc["grupo"] = np.where(per_acc.index.isin(churned), "churnou", "nunca churnou")
    comp = per_acc.groupby("grupo").mean(numeric_only=True)
    pvals = {
        c: stats.mannwhitneyu(
            per_acc[per_acc.grupo == "churnou"][c].dropna(),
            per_acc[per_acc.grupo == "nunca churnou"][c].dropna(),
        ).pvalue
        for c in comp.columns
    }
    comp.loc["p (Mann-Whitney)"] = pd.Series(pvals)

    def window(a: str, end: pd.Timestamp) -> int:
        w = t[(t.account_id == a) & (t.submitted_at < end)]
        return int((w.submitted_at >= end - pd.Timedelta(days=90)).sum())

    silent = float(
        np.mean(
            [window(a, d) == 0 for a, d in zip(churn.account_id, churn.churn_date, strict=True)]
        )
    )
    dist = t.satisfaction_score.value_counts(dropna=False).rename("tickets")
    numbers.update(
        csat_churned=round(float(comp.loc["churnou", "csat"]), 2),
        csat_retained=round(float(comp.loc["nunca churnou", "csat"]), 2),
        csat_no_response_pct=round(float(1 - t.has_csat.mean()), 3),
        csat_scale_observed="3-5",
        silent_churn_pct=round(silent, 3),
    )
    section(
        "H1 — A satisfação está mascarada?",
        md(comp),
        md(dist.to_frame(), 0),
        f"Quem churna e quem fica têm **o mesmo CSAT** ({comp.loc['churnou', 'csat']:.2f} × "
        f"{comp.loc['nunca churnou', 'csat']:.2f}) e o mesmo suporte (nenhum p < 0,05). A nota só "
        f"vai de 3 a 5 (nenhuma nota 1 ou 2) e {1 - t.has_csat.mean():.0%} dos tickets não têm "
        f"nota. **{silent:.0%} dos churns não abriram nenhum ticket nos 90 dias anteriores.** "
        "Conclusão: o CSAT não é falso — ele é *cego*: não separa quem vai sair.",
    )


def h2_h3_usage(
    acc: pd.DataFrame, churn: pd.DataFrame, usage: pd.DataFrame, subs: pd.DataFrame
) -> None:
    u = usage.assign(q=usage.usage_date.dt.to_period("Q").astype(str))
    u = u.merge(acc[["signup_date"]], left_on="account_id", right_index=True)
    before_signup = float((u.usage_date < u.signup_date).mean())
    by_q = u.groupby("q").agg(
        eventos_de_uso=("usage_count", "sum"),
        contas_com_uso=("account_id", "nunique"),
        erros=("error_count", "sum"),
    )
    by_q["contas_cadastradas"] = [
        (acc.signup_date <= pd.Period(q).end_time).sum() for q in by_q.index
    ]
    by_q["uso_por_conta_com_uso"] = by_q.eventos_de_uso / by_q.contas_com_uso
    by_q["taxa_de_erro"] = by_q.erros / by_q.eventos_de_uso

    per = u.groupby("account_id").agg(uso=("usage_count", "sum"), erros=("error_count", "sum"))
    per["taxa_erro"] = per.erros / per.uso
    per["churns"] = per.index.map(churn.account_id.value_counts()).fillna(0)
    per["quartil_erro"] = pd.qcut(
        per.taxa_erro, 4, labels=["Q1 menos erro", "Q2", "Q3", "Q4 mais erro"]
    )
    dose = per.groupby("quartil_erro", observed=True).agg(
        contas=("uso", "size"), churns_por_conta=("churns", "mean")
    )
    rho = stats.spearmanr(per.taxa_erro, per.churns)

    never = acc.index.difference(churn.account_id.unique()).to_numpy()

    def usage_90(a: str, end: pd.Timestamp) -> float:
        w = u[
            (u.account_id == a)
            & (u.usage_date < end)
            & (u.usage_date >= end - pd.Timedelta(days=90))
        ]
        return float(w.usage_count.sum())

    ch = [usage_90(a, d) for a, d in zip(churn.account_id, churn.churn_date, strict=True)]
    ct = [usage_90(RNG.choice(never), d) for d in churn.churn_date]
    p_use = stats.mannwhitneyu(ch, ct).pvalue
    numbers.update(
        usage_before_signup_pct=round(before_signup, 3),
        usage_per_account_flat=round(
            float(by_q.uso_por_conta_com_uso.std() / by_q.uso_por_conta_com_uso.mean()), 3
        ),
        error_rate_churn_spearman=round(float(rho.statistic), 3),
        usage_90d_churn_vs_control_p=round(float(p_use), 3),
    )
    section(
        "H2/H3 — O uso cresceu? Erros e beta antecedem o churn?",
        md(by_q, 2),
        md(dose),
        f"O uso total é **plano** (~31 mil eventos/tri) e o uso por conta também (~63). Não há "
        f"crescimento — nem queda — em nenhum plano ou indústria. Pior: {before_signup:.0%} do uso "
        "tem data **anterior ao cadastro** da conta e ~500 contas aparecem usando desde 2023Q1, "
        "quando só 55 existiam: o log de uso não está ancorado no tempo. "
        f"Uso nos 90 dias antes do churn × controle na mesma data: p = {p_use:.2f}. Erros × churn: "
        f"Spearman ρ = {rho.statistic:.2f} (p = {rho.pvalue:.2f}), sem dose-resposta. "
        'Conclusão: a afirmação "o uso cresceu" não se sustenta, e o dado de uso não serve hoje '
        "como sinal de churn.",
    )


def h4_reasons(churn: pd.DataFrame) -> None:
    by_r = churn.groupby("reason_code").agg(
        eventos=("mrr", "size"),
        mrr_mediano=("mrr", "median"),
        refund_medio=("refund_amount_usd", "mean"),
        downgrade_90d=("preceding_downgrade_flag", "mean"),
    )
    p_time = stats.chi2_contingency(pd.crosstab(churn.q, churn.reason_code))[1]
    numbers["reason_vs_quarter_p"] = round(float(p_time), 3)
    section(
        "H4 — O motivo declarado explica o churn?",
        md(by_r, 2),
        f"Motivos quase uniformes (91–114 cada), sem mudança ao longo do tempo (χ² p = {p_time:.2f}) "
        "e com comportamento parecido. `feedback_text` tem só 4 textos distintos. O motivo "
        "declarado **não discrimina nada** — é campo de formulário, não diagnóstico.",
    )


def h6_segments(acc: pd.DataFrame, churn: pd.DataFrame) -> None:
    a = acc.copy()
    a["exp_meses"] = ((END - a.signup_date).dt.days / 30.44).clip(lower=0.5)
    a["churns"] = a.index.map(churn.account_id.value_counts()).fillna(0)
    a["faixa_licencas"] = pd.qcut(a.seats, 4, labels=["Q1", "Q2", "Q3", "Q4"])
    out = []
    for col in [
        "referral_source",
        "industry",
        "country",
        "plan_tier",
        "is_trial",
        "faixa_licencas",
    ]:
        g = a.groupby(col, observed=True).agg(churns=("churns", "sum"), exp=("exp_meses", "sum"))
        expected = g.exp / g.exp.sum() * g.churns.sum()
        p = stats.chisquare(g.churns, expected).pvalue
        rate = 100 * g.churns / g.exp
        out.append(
            {
                "segmento": col,
                "p": p,
                "maior": f"{rate.idxmax()} ({rate.max():.1f})",
                "menor": f"{rate.idxmin()} ({rate.min():.1f})",
            }
        )
    df = pd.DataFrame(out).set_index("segmento")
    df["significativo após Bonferroni (p<0,0083)"] = df.p < 0.05 / len(df)
    numbers["segments_significant"] = int(df.iloc[:, -1].sum())
    section(
        "H6 — Algum segmento de cadastro churna mais?",
        "Churns por 100 contas-mês de exposição; teste χ² contra a exposição.",
        md(df),
        "Nenhum segmento de cadastro (canal, indústria, país, plano inicial, trial, licenças) "
        "sobrevive à correção para múltiplas comparações. `organic` aparece mais alto (p = 0,025), "
        'mas é o tipo de "achado" que some com 6 testes: não vamos recomendar ação por canal.',
    )


def h7_downgrade(churn: pd.DataFrame, subs: pd.DataFrame) -> None:
    section(
        "H7 — Mudança de plano antecede o churn?",
        f"Nos eventos de churn: downgrade nos 90 dias anteriores = "
        f"{churn.preceding_downgrade_flag.mean():.1%}, upgrade = {churn.preceding_upgrade_flag.mean():.1%}. "
        f"Base das assinaturas: downgrade = {subs.downgrade_flag.mean():.1%}, upgrade = "
        f"{subs.upgrade_flag.mean():.1%}. As duas taxas dobram — qualquer mudança de plano, não só "
        "downgrade. Unidades diferentes (janela de 90 dias × flag da assinatura): **indício fraco**, "
        "não causa.",
    )


def h8_tenure_cohort(acc: pd.DataFrame, churn: pd.DataFrame) -> pd.DataFrame:
    panel = account_month_panel(acc, churn)
    haz = 100 * panel.pivot_table(
        index="cal_q", columns="ten_b", values="y", aggfunc="mean", observed=False
    )
    model = smf.glm(
        "y ~ C(cal_q) + C(ten_b) + prior_churn", data=panel, family=sm.families.Poisson()
    ).fit()
    rr = np.exp(model.params).rename("rate ratio").to_frame()
    rr["p"] = model.pvalues
    rr = rr.drop(index="Intercept")

    first = churn.groupby("account_id").tenure_m.min()
    el = acc[acc.signup_date <= END - pd.Timedelta(days=183)].copy()
    el["churn_6m"] = (el.index.map(first) < 6).astype(int)
    el["coorte"] = (
        el.signup_date.dt.year.astype(str) + "H" + np.where(el.signup_date.dt.month <= 6, "1", "2")
    )
    el["y2024"] = (el.signup_date.dt.year == 2024).astype(int)
    el["trial"] = el.is_trial.astype(int)
    el["seats_l"] = np.log(el.seats)
    logit = smf.logit(
        "churn_6m ~ y2024 + C(referral_source) + C(plan_tier) + C(industry) + trial + seats_l",
        data=el,
    ).fit(disp=0)
    or_2024 = float(np.exp(logit.params["y2024"]))
    ci = np.exp(logit.conf_int().loc["y2024"]).tolist()
    by_coh = el.groupby("coorte").churn_6m.agg(contas="size", churn_6m="mean")

    early = churn.assign(
        tipo=np.select(
            [churn.nth > 1, churn.tenure_m < 3],
            ["repetido (2º+)", "1º churn < 3 meses"],
            "1º churn ≥ 3 meses",
        )
    )
    mix = early.groupby("tipo").agg(eventos=("mrr", "size"), mrr=("mrr", "sum"))
    mix["pct_eventos"] = mix.eventos / mix.eventos.sum()
    mix["pct_mrr"] = mix.mrr / mix.mrr.sum()

    numbers.update(
        hazard_0_3m_2024q4=round(float(haz.loc["2024Q4", "0-3m"]), 1),
        hazard_12m_2024q4=round(float(haz.loc["2024Q4", "12m+"]), 1),
        rr_tenure_12m_vs_0_3m=round(float(rr.loc["C(ten_b)[T.12m+]", "rate ratio"]), 2),
        rr_prior_churn=round(float(rr.loc["prior_churn", "rate ratio"]), 2),
        cohort_2024_or_churn_6m=round(or_2024, 2),
        cohort_2024_or_ci=[round(x, 2) for x in ci],
        cohort_2024_p=float(logit.pvalues["y2024"]),
        churn_6m_2023h1=round(float(by_coh.loc["2023H1", "churn_6m"]), 3),
        churn_6m_2024h1=round(float(by_coh.loc["2024H1", "churn_6m"]), 3),
        early_or_repeat_share_events=round(
            float(1 - mix.loc["1º churn ≥ 3 meses", "pct_eventos"]), 3
        ),
        early_or_repeat_share_mrr=round(float(1 - mix.loc["1º churn ≥ 3 meses", "pct_mrr"]), 3),
    )
    section(
        "H8 — Quem está saindo: contas novas e contas que já saíram antes",
        "Churns por 100 contas-mês, por trimestre do calendário × tempo de casa:",
        md(haz, 1),
        "Modelo de Poisson (conta-mês) com trimestre do calendário, tempo de casa e churn anterior:",
        md(rr, 3),
        "Coortes (contas com ≥ 6 meses de observação), % com churn nos primeiros 6 meses:",
        md(by_coh),
        f"Logit controlando canal, plano inicial, indústria, trial e licenças: coorte 2024 tem "
        f"**{or_2024:.1f}×** a chance de churnar em 6 meses (IC 95% {ci[0]:.1f}–{ci[1]:.1f}, "
        f"p = {logit.pvalues['y2024']:.0e}). Nenhum outro controle é significativo — o mix de "
        "cadastro **não mudou**; o que mudou foi o resultado das contas novas.",
        md(mix),
        "Leitura causal: tempo de casa precede o churn ✅, dose-resposta monotônica ✅, se mantém "
        'com controles ✅; alternativa "choque de calendário que atinge todos" — existe '
        "(rate ratio sobe por trimestre), mas a base antiga sobe ~1,5× enquanto as contas de "
        "0–3 meses sobem ~8×. Contas que já churnaram antes **não** têm risco maior "
        f"(rate ratio {rr.loc['prior_churn', 'rate ratio']:.2f}, p = {rr.loc['prior_churn', 'p']:.2f}): elas pesam "
        "porque voltam e saem de novo, não porque sejam piores. O **mecanismo** (onboarding, ativação, qualificação de venda) não "
        "está nos dados: é hipótese a validar com experimento.",
    )
    return panel


def risk_accounts(
    acc: pd.DataFrame, churn: pd.DataFrame, subs: pd.DataFrame, panel: pd.DataFrame
) -> None:
    """Contas ativas em 2024-12-31 com taxa esperada de churn (modelo de H8) × MRR vigente."""
    model = smf.glm(
        "y ~ C(ten_b) + prior_churn",
        data=panel[panel.cal_q == "2024Q4"],
        family=sm.families.Poisson(),
    ).fit()
    last_churn = churn.groupby("account_id").churn_date.max()
    rows = []
    for a, r in acc.iterrows():
        s = latest_sub_at(subs, a, END)
        if s is None:
            continue
        lc = last_churn.get(a)
        reactivated = lc is not None and (
            subs[(subs.account_id == a) & (subs.start_date > lc)].shape[0] > 0
        )
        if lc is not None and not reactivated:
            continue  # churnou e não voltou
        ten = (END.to_period("M") - r.signup_date.to_period("M")).n + 1
        rows.append(
            dict(
                account_id=a,
                account_name=r.account_name,
                industry=r.industry,
                plan=s.plan_tier,
                billing=s.billing_frequency,
                mrr=float(s.mrr_amount),
                tenure_meses=ten,
                churns_anteriores=int((churn.account_id == a).sum()),
                prior_churn=int(lc is not None),
                ten=ten,
            )
        )
    df = pd.DataFrame(rows)
    df["ten_b"] = pd.cut(df.ten, TENURE_BINS, labels=TENURE_LABELS)
    monthly = model.predict(df[["ten_b", "prior_churn"]])
    df["prob_churn_90d"] = 1 - np.exp(-3 * monthly)
    df["mrr_em_risco_90d"] = df.prob_churn_90d * df.mrr
    df = df.sort_values("mrr_em_risco_90d", ascending=False).drop(
        columns=["ten", "ten_b", "prior_churn"]
    )
    df.to_csv(OUT / "risk_accounts.csv", index=False)
    top = df.head(15)
    numbers.update(
        active_accounts=int(len(df)),
        active_mrr=float(df.mrr.sum()),
        mrr_at_risk_90d=float(df.mrr_em_risco_90d.sum()),
        top20_share_mrr_at_risk=round(
            float(df.head(20).mrr_em_risco_90d.sum() / df.mrr_em_risco_90d.sum()), 3
        ),
    )
    section(
        "Contas em risco (lista de ação)",
        f"{len(df)} contas ativas em 31/12/2024, MRR vigente US$ {df.mrr.sum():,.0f}. Probabilidade "
        "de churn em 90 dias pelo modelo de H8 (tempo de casa + churn anterior, taxas de 2024Q4); "
        f"MRR em risco esperado: **US$ {df.mrr_em_risco_90d.sum():,.0f}**. As 20 primeiras "
        f"concentram {numbers['top20_share_mrr_at_risk']:.0%} do risco. Lista completa em "
        "`analysis/results/risk_accounts.csv`.",
        md(top.set_index("account_id"), 2),
    )


def main() -> None:
    OUT.mkdir(exist_ok=True)
    d = load_silver()
    acc = d["accounts"].set_index("account_id")
    # mesmo desempate do SQL (gold.subscription_at): início mais recente, depois maior subscription_id
    subs = d["subscriptions"].sort_values(["start_date", "subscription_id"])
    churn = enrich_churn(d["churn_events"].sort_values("churn_date").copy(), subs, acc)

    h0_trend(acc, churn, subs)
    h5_revenue(churn)
    h1_support(acc, churn, d["support_tickets"])
    h2_h3_usage(acc, churn, d["feature_usage"], subs)
    h4_reasons(churn)
    h6_segments(acc, churn)
    h7_downgrade(churn, subs)
    panel = h8_tenure_cohort(acc, churn)
    risk_accounts(acc, churn, subs, panel)

    header = (
        "# Diagnóstico de churn — evidências\n\n"
        "Gerado por `analysis/diagnostico.py` a partir do silver (Supabase G4-Analysys). "
        "Churn = `churn_events`; MRR vigente = assinatura ativa mais recente; seed 42.\n"
    )
    (OUT / "diagnostico.md").write_text(header + "\n\n".join(sections) + "\n")
    (OUT / "numbers.json").write_text(
        json.dumps(numbers, indent=2, ensure_ascii=False, default=float)
    )
    print(json.dumps(numbers, indent=2, ensure_ascii=False, default=float))


if __name__ == "__main__":
    main()
