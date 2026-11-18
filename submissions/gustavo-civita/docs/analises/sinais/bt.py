"""Framework de backtest: snapshots do pipeline aberto em varias datas de corte.
Toda feature usa apenas informacao disponivel ate a data de corte T."""
from common import *

CUT_A = ["2017-06-15", "2017-06-30", "2017-07-15", "2017-07-31"]   # periodo A
CUT_B = ["2017-08-15", "2017-08-31", "2017-09-15", "2017-09-30"]   # periodo B
CUT_C = ["2017-10-15", "2017-10-31", "2017-11-15", "2017-11-30"]   # periodo C (so horizonte 30d)
K = 10  # encolhimento das taxas historicas

def shrunk(key_hist, won_hist, key_now, glob):
    g = pd.DataFrame({"k": key_hist, "w": won_hist}).groupby("k").w.agg(["sum", "count"])
    s = key_now.map(g["sum"]).fillna(0); n = key_now.map(g["count"]).fillna(0)
    return (s + K * glob) / (n + K), n, s

def key(df, cols):
    return df[cols[0]].astype(str).str.cat([df[c].astype(str) for c in cols[1:]], sep="|") if len(cols) > 1 else df[cols[0]].astype(str)

def snapshot(d, T):
    T = pd.Timestamp(T)
    s = scoring.open_at(d, T)
    chance = scoring.win_chance_by_age(d, T)
    s["T"] = T
    s["p0"] = [scoring.chance_for(chance, a) for a in s.age]
    later = s.close_date.notna()
    s["y_ever"] = ((s.deal_stage == "Won") & later).astype(float)
    s["y30"] = ((s.deal_stage == "Won") & (s.close_date <= T + pd.Timedelta(days=30))).astype(float)
    s["closes_later"] = later.astype(float)
    s["val_future"] = np.where(s.y_ever == 1, s.close_value, 0.0)
    s["val30"] = np.where(s.y30 == 1, s.close_value, 0.0)
    s["days_to_close"] = (s.close_date - T).dt.days
    s["has_account"] = s.account.notna()
    hist = d[d.closed & (d.close_date <= T)]
    glob = hist.won.mean()
    d["size_b"] = pd.qcut(d.revenue, 3, labels=["P", "M", "G"]).astype(object)
    s["size_b"] = d.loc[s.index, "size_b"]; hist = hist.assign(size_b=d.loc[hist.index, "size_b"])
    for name, cols in {"agent": ["sales_agent"], "product": ["product"], "account": ["account"], "sector": ["sector"],
                       "manager": ["manager"], "office": ["regional_office"],
                       "agent_x_product": ["sales_agent", "product"], "agent_x_account": ["sales_agent", "account"],
                       "account_x_product": ["account", "product"], "sector_x_product": ["sector", "product"],
                       "size_x_product": ["size_b", "product"], "agent_x_sector": ["sales_agent", "sector"],
                       "manager_x_product": ["manager", "product"]}.items():
        wr, n, w = shrunk(key(hist, cols), hist.won, key(s, cols), glob)
        s[f"wr_{name}"] = wr; s[f"n_{name}"] = n; s[f"won_{name}"] = w
    for name in ["agent_x_account", "account_x_product"]:
        s[f"prior_won_{name}"] = (s[f"won_{name}"] > 0).astype(float)
        s[f"prior_any_{name}"] = (s[f"n_{name}"] > 0).astype(float)
    # recencia de compra da conta
    lastwon = hist[hist.won == 1].groupby("account").close_date.max()
    s["days_since_acc_won"] = (T - s.account.map(lastwon)).dt.days
    s["acc_won_30d"] = (s.days_since_acc_won <= 30).astype(float)
    s["acc_won_60d"] = (s.days_since_acc_won <= 60).astype(float)
    lastlost = hist[hist.won == 0].groupby("account").close_date.max()
    s["acc_lost_30d"] = ((T - s.account.map(lastlost)).dt.days <= 30).astype(float)
    w90 = hist[(hist.close_date > T - pd.Timedelta(days=90))]
    s["acc_wr_90d"], _, _ = shrunk(w90.account, w90.won, s.account, w90.won.mean())
    s["acc_open_n"] = s.account.map(s.account.value_counts())
    s["acc_agent_open_n"] = key(s, ["sales_agent", "account"]).map(key(s, ["sales_agent", "account"]).value_counts())
    # carga do vendedor
    s["agent_open_n"] = s.sales_agent.map(s.sales_agent.value_counts())
    fresh = s[s.age <= 90]
    s["agent_open_fresh_n"] = s.sales_agent.map(fresh.sales_agent.value_counts()).fillna(0)
    s["agent_stale_share"] = s.sales_agent.map((s.age > 100).groupby(s.sales_agent).mean())
    new30 = d[(d.engage_date > T - pd.Timedelta(days=30)) & (d.engage_date <= T)]
    s["agent_new30_n"] = s.sales_agent.map(new30.sales_agent.value_counts()).fillna(0)
    c30 = hist[hist.close_date > T - pd.Timedelta(days=30)]
    s["agent_closed30_n"] = s.sales_agent.map(c30.sales_agent.value_counts()).fillna(0)
    s["agent_wr_30d"], _, _ = shrunk(c30.sales_agent, c30.won, s.sales_agent, c30.won.mean() if len(c30) else glob)
    s["agent_cycle_med"] = s.sales_agent.map(hist.groupby("sales_agent").cycle.median())
    s["agent_volume"] = s.sales_agent.map(d[d.engage_date <= T].sales_agent.value_counts())
    s["load_rel"] = s.agent_open_n / s.agent_volume
    s["agent_ratio_hist"] = s.sales_agent.map(hist[hist.won == 1].groupby("sales_agent").ratio.mean())
    # estaticas
    s["is_sub"] = s.is_sub.astype(float)
    s["log_rev"] = np.log(s.revenue); s["log_emp"] = np.log(s.employees)
    s["log_price"] = np.log(s.sales_price)
    s["eng_dow"] = s.engage_date.dt.dayofweek; s["eng_weekend"] = (s.eng_dow >= 5).astype(float)
    s["eng_dom"] = s.engage_date.dt.day; s["eng_dom_late"] = (s.eng_dom >= 21).astype(float)
    s["us_account"] = (s.office_location == "United States").astype(float)
    s["age_bin"] = (s.age // 10).clip(upper=20)
    return s

def build(d, cuts):
    return pd.concat([snapshot(d, T) for T in cuts]).reset_index().rename(columns={"index": "deal"})

def fwl(S, f, y, mask=None):
    """Efeito de f sobre y controlando estrato (T x faixa de idade de 10 dias). Erro-padrao agrupado por deal.
    Retorna n, n_deals, beta, se, p, efeito p10->p90 (em unidades de y)."""
    from scipy import stats
    X = S if mask is None else S[mask]
    X = X[X[f].notna() & X[y].notna()].copy(); X[f] = X[f].astype(float)
    if len(X) < 50: return dict(n=len(X), deals=X.deal.nunique(), eff=np.nan, p=np.nan, beta=np.nan)
    g = X.groupby(["T", "age_bin"])
    rf = X[f] - g[f].transform("mean"); ry = X[y] - g[y].transform("mean")
    sxx = (rf ** 2).sum()
    if sxx <= 0: return dict(n=len(X), deals=X.deal.nunique(), eff=np.nan, p=np.nan, beta=np.nan)
    beta = (rf * ry).sum() / sxx
    e = ry - beta * rf
    sc = (rf * e).groupby(X.deal).sum()
    se = np.sqrt((sc ** 2).sum()) / sxx
    p = 2 * stats.norm.sf(abs(beta / se)) if se > 0 else np.nan
    spread = X[f].quantile(.9) - X[f].quantile(.1)
    if X[f].nunique() == 2: spread = 1.0
    return dict(n=len(X), deals=X.deal.nunique(), eff=beta * spread, p=p, beta=beta)

def bh(p):
    p = np.asarray(p, float); ok = ~np.isnan(p); q = np.full(len(p), np.nan)
    idx = np.where(ok)[0]; o = idx[np.argsort(p[idx])]; m = len(o)
    adj = p[o] * m / (np.arange(m) + 1); adj = np.minimum.accumulate(adj[::-1])[::-1]
    q[o] = np.minimum(adj, 1); return q

if __name__ == "__main__":
    d = load()
    S = build(d, CUT_A + CUT_B + CUT_C)
    S.to_pickle("snapshots.pkl")
    print(S.groupby("T").agg(n=("deal", "size"), p0=("p0", "mean"), y_ever=("y_ever", "mean"), y30=("y30", "mean"),
                             closes=("closes_later", "mean"), hasacc=("has_account", "mean"), val=("val_future", "sum")).round(3))
    # calibracao da baseline
    S["p0b"] = pd.cut(S.p0, [-.01, .01, .1, .2, .3, .4, .5, .6, .7, 1])
    AB = S[S["T"] <= "2017-09-30"]
    print(AB.groupby("p0b", observed=True).agg(n=("deal", "size"), p0=("p0", "mean"), y=("y_ever", "mean")).round(3))
