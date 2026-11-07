"""
Correção do 05 após a revisão independente (agente Esquadro). Dois vieses no 05:

1. Seleção pelo futuro: o teste usava só deals que ACABARAM fechando. O alvo "decidiu em até 30 dias"
   é conhecido para TODO deal aberto em S (o dataset vai até 31/12/2017, bem depois de S+30),
   então o teste agora usa todos os abertos em S.
2. Censura: a curva era estimada só com deals fechados, ignorando os que seguiam abertos.
   Aqui ela é estimada por Kaplan-Meier: fechados antes de S são eventos, abertos em S são censurados
   na idade que tinham em S.

Também: horizonte com a mesma convenção (fecha em até S+30, inclusive) e zumbis deduplicados.
Uso:  python 06_momentum_km_backtest.py
"""
import numpy as np
import pandas as pd

D = "../data/"
H = 30
p = pd.read_csv(D + "sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
p = p[p.engage_date.notna()].copy()  # prospecção não tem idade
END = p.close_date.max()


def auc(y, s):
    y = np.asarray(y); r = pd.Series(s).rank().values
    n1 = y.sum(); n0 = len(y) - n1
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def km_survival(durations, events, tmax):
    """S[t] = P(T > t), t = 0..tmax (Kaplan-Meier, censurados em risco no próprio dia)."""
    durations = np.asarray(durations); events = np.asarray(events)
    S = np.ones(tmax + 1); s = 1.0
    for t in range(tmax + 1):
        n = (durations >= t).sum()
        d = ((durations == t) & events).sum()
        if n > 0:
            s *= 1 - d / n
        S[t] = s
    return S


def curve_from_S(S, max_age):
    return np.array([1 - S[a + H] / S[a] if S[a] > 0 else 0.0 for a in range(max_age + 1)])


def naive_curve(closed_days, max_age):
    out, last = [], 0.0
    for a in range(max_age + 1):
        alive = closed_days[closed_days > a]
        if len(alive) >= 30:
            last = (alive <= a + H).mean()
        out.append(last)
    return np.array(out)


rows, zombie_ids = [], {}
for S_ in pd.to_datetime(["2017-05-01", "2017-07-01", "2017-09-01"]):
    known_closed = p[p.close_date < S_]
    open_at_S = p[(p.engage_date < S_) & (p.close_date.isna() | (p.close_date >= S_))].copy()
    open_at_S["age"] = (S_ - open_at_S.engage_date).dt.days
    cdays = (known_closed.close_date - known_closed.engage_date).dt.days.values
    max_cycle = int(cdays.max())

    # Zumbis em S: abertos há mais que o maior ciclo conhecido. Algum fechou depois?
    z = open_at_S[open_at_S.age > max_cycle]
    for _, r in z.iterrows():
        zombie_ids[r.opportunity_id] = zombie_ids.get(r.opportunity_id, False) or pd.notna(r.close_date)

    # Kaplan-Meier com o que se sabia em S
    dur = np.concatenate([cdays, open_at_S.age.values])
    ev = np.concatenate([np.ones(len(cdays), bool), np.zeros(len(open_at_S), bool)])
    S = km_survival(dur, ev, max_cycle + H + 1)
    km = curve_from_S(S, max_cycle)
    nv = naive_curve(cdays, max_cycle)

    t = open_at_S[open_at_S.age <= max_cycle].copy()  # vivos (o app pontua só estes)
    t["y"] = (t.close_date.notna() & (t.close_date <= S_ + pd.Timedelta(days=H))).astype(int)
    t["km"] = km[t.age.values]
    t["naive"] = nv[t.age.values]
    rows.append({
        "snapshot": S_.date(), "vivos_em_S": len(t), "decidiram_30d": round(t.y.mean(), 3),
        "AUC_km": round(auc(t.y, t.km), 3), "prev_media_km": round(t.km.mean(), 3),
        "AUC_ingenua": round(auc(t.y, t.naive), 3), "prev_media_ingenua": round(t.naive.mean(), 3),
        "zumbis_em_S": len(z),
    })

res = pd.DataFrame(rows)
pd.set_option("display.width", 200)
print(res.to_string(index=False))
print(f"\nZumbis únicos (somando os 3 snapshots): {len(zombie_ids)} | fecharam até {END.date()}: {sum(zombie_ids.values())}")

# Calibração por faixa de previsão (KM), juntando os snapshots
print("\nCalibração KM (prev × real), por faixa:")
allt = []
for S_ in pd.to_datetime(["2017-05-01", "2017-07-01", "2017-09-01"]):
    kc = p[p.close_date < S_]; o = p[(p.engage_date < S_) & (p.close_date.isna() | (p.close_date >= S_))].copy()
    o["age"] = (S_ - o.engage_date).dt.days
    cd = (kc.close_date - kc.engage_date).dt.days.values; mc = int(cd.max())
    Sv = km_survival(np.concatenate([cd, o.age.values]), np.concatenate([np.ones(len(cd), bool), np.zeros(len(o), bool)]), mc + H + 1)
    k = curve_from_S(Sv, mc); o = o[o.age <= mc]
    o["pred"] = k[o.age.values]; o["y"] = (o.close_date.notna() & (o.close_date <= S_ + pd.Timedelta(days=H))).astype(int)
    allt.append(o)
allt = pd.concat(allt)
print(allt.groupby(pd.cut(allt.pred, [0, .1, .2, .3, .5, 1], include_lowest=True), observed=True)
      .agg(n=("y", "size"), prev=("pred", "mean"), real=("y", "mean")).round(3))

# Curva final (com todo o histórico, "hoje" = END), a mesma que o app usa
cdays = (p[p.close_date.notna()].close_date - p[p.close_date.notna()].engage_date).dt.days.values
op = p[p.close_date.isna()]; ages = (END - op.engage_date).dt.days.values
Sf = km_survival(np.concatenate([cdays, ages]), np.concatenate([np.ones(len(cdays), bool), np.zeros(len(ages), bool)]), int(cdays.max()) + H + 1)
kf = curve_from_S(Sf, int(cdays.max()))
print("\nCurva KM final (idade → p decisão 30d):", {a: round(kf[a], 3) for a in range(0, len(kf), 15)})
