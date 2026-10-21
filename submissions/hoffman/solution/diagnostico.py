"""Diagnóstico operacional — Dataset 1 (reproduz métricas do README)."""
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LinearRegression

CSV1 = Path(__file__).parent / "data/customer_support_tickets.csv"
CSV2 = Path(__file__).parent / "data/all_tickets_processed_improved_v3.csv"
CUSTO_H = 120
MIN_TRIAGEM_MANUAL = 4
MIN_TRIAGEM_AUTO = 0.5
TAXA_ELEGIVEL = 0.70  # tickets com texto classificável (excl. refund/cancel na prática)


def post_frt_hours(df: pd.DataFrame) -> pd.Series:
    frt = pd.to_datetime(df["First Response Time"], errors="coerce")
    ttr = pd.to_datetime(df["Time to Resolution"], errors="coerce")
    return (ttr - frt).dt.total_seconds() / 3600


def fmt_h(h: float) -> str:
    return f"{h:.1f}".replace(".", ",")


def main() -> None:
    df = pd.read_csv(CSV1)
    n = len(df)
    df["post_frt_h"] = post_frt_hours(df)
    closed = df["Ticket Status"].eq("Closed")
    both_ts = closed & df["post_frt_h"].notna()
    valid = both_ts & (df["post_frt_h"] >= 0)
    t = df.loc[valid].copy()
    n_closed_ts = int(both_ts.sum())
    n_valid = len(t)

    print(f"=== Diagnóstico Dataset 1 ({n:,} tickets) ===".replace(",", "."))
    print(
        f"Fechados com ambos timestamps: {n_closed_ts:,} | "
        f"pós-FRT cronológico (≥0 h): {n_valid:,}".replace(",", ".")
    )

    phys_lines = sum(1 for _ in open(CSV1, encoding="utf-8", errors="replace")) - 1
    closed_both = df.loc[both_ts, "post_frt_h"]
    pct_inv = 100 * (closed_both < 0).sum() / n_closed_ts if n_closed_ts else 0
    pct_le0 = 100 * (closed_both <= 0).sum() / n_closed_ts if n_closed_ts else 0
    open_pending = df["Ticket Status"].isin(["Open", "Pending Customer Response"])
    frt = pd.to_datetime(df["First Response Time"], errors="coerce")
    sem_frt_abertos = int((open_pending & frt.isna()).sum())

    print("\n--- Qualidade Dataset 1 (leia antes dos gargalos) ---")
    print(
        f"Registros (pandas): {n:,} | linhas físicas CSV (multiline em texto): {phys_lines:,}".replace(",", ".")
    )
    print(f"Fechados: {pct_inv:.1f}% timestamps invertidos (pós-FRT < 0) | {pct_le0:.1f}% resolução ≤ 1ª resposta")
    print(f"Open/Pending sem First Response Time: {sem_frt_abertos} (backlog sem resposta registrada)")

    p50 = t["post_frt_h"].median()
    p90 = t["post_frt_h"].quantile(0.9)
    print(f"Pós-FRT global — mediana: {fmt_h(p50)} h | p90: {fmt_h(p90)} h (recorte ≥0 h; exploratório)")

    print("\n--- Onde o fluxo trava? (média pós-FRT h; exploratório) ---")
    for col in ("Ticket Channel", "Ticket Priority", "Ticket Type"):
        g = t.groupby(col)["post_frt_h"].mean().sort_values(ascending=False)
        parts = [f"{k} ({fmt_h(v)})" for k, v in g.items()]
        print(f"{col}: {', '.join(parts)}")

    worst_ch = t.groupby("Ticket Channel")["post_frt_h"].median().idxmax()
    wc = t[t["Ticket Channel"] == worst_ch]["post_frt_h"]
    print(f"Canal com mediana mais alta ({worst_ch}): p50 {fmt_h(wc.median())} h, p90 {fmt_h(wc.quantile(0.9))} h")

    combo = (
        t.groupby(["Ticket Channel", "Ticket Priority", "Ticket Type"], observed=True)["post_frt_h"]
        .agg(["mean", "count"])
        .reset_index()
    )
    combo = combo[combo["count"] >= 20].sort_values("mean", ascending=False).head(4)
    print("\nPiores combinações (n≥20):")
    for _, r in combo.iterrows():
        print(
            f"  {r['Ticket Channel']} + {r['Ticket Priority']} + {r['Ticket Type']} "
            f"({fmt_h(r['mean'])} h, n={int(r['count'])})"
        )

    print("\n--- O que impacta satisfação? ---")
    csat = df["Customer Satisfaction Rating"].dropna()
    print(f"CSAT médio: {csat.mean():.2f}/5 (n={len(csat)})")
    for col in ("Ticket Type", "Ticket Channel"):
        g = df.groupby(col)["Customer Satisfaction Rating"].mean().sort_values()
        print(f"  {col} — pior: {g.index[0]} ({g.iloc[0]:.2f}), melhor: {g.index[-1]} ({g.iloc[-1]:.2f})")

    sub = t.dropna(subset=["Customer Satisfaction Rating"])
    corr = sub["Customer Satisfaction Rating"].corr(sub["post_frt_h"])
    print(f"Correlação CSAT × pós-FRT: {corr:.2f}")

    drivers = df.dropna(subset=["Customer Satisfaction Rating"]).copy()
    X = pd.get_dummies(
        drivers[["Ticket Channel", "Ticket Type", "Ticket Priority"]].astype(str),
        drop_first=True,
    )
    y = drivers["Customer Satisfaction Rating"].values
    reg = LinearRegression().fit(X, y)
    r2 = reg.score(X, y)
    coef = pd.Series(reg.coef_, index=X.columns).abs().sort_values(ascending=False)
    print(f"Regressão CSAT (canal/tipo/prioridade): R² = {r2:.3f}")
    print("Top drivers CSAT (|coef| regressão linear, dummies; escala: pontos CSAT):")
    for name, c in coef.head(3).items():
        sign = reg.coef_[X.columns.get_loc(name)]
        print(f"  {name}: {sign:+.3f}")

    print("\n--- Quanto estamos desperdiçando? ---")
    backlog = df["Ticket Status"].isin(["Open", "Pending Customer Response"]).sum()
    med_closed = t["post_frt_h"].median()
    horas_ub = backlog * med_closed
    print(f"Open/Pending: {backlog} ({100 * backlog / n:.0f}%)")
    print(f"Upper bound ilustrativo backlog: {horas_ub:,.0f} h (mediana pós-FRT × backlog)".replace(",", "."))
    print(f"Custo ilustrativo @ R$ {CUSTO_H}/h: R$ {horas_ub * CUSTO_H:,.0f}".replace(",", "."))

    print("\n--- ROI triagem (premissas) ---")
    tickets_dia = n / 365
    min_save = MIN_TRIAGEM_MANUAL - MIN_TRIAGEM_AUTO
    h_mes = tickets_dia * 22 * (min_save / 60) * TAXA_ELEGIVEL
    print(f"Volume ~{tickets_dia:.1f} tickets/dia (DS1/{365}d)")
    print(f"Triagem manual {MIN_TRIAGEM_MANUAL} min → auto {MIN_TRIAGEM_AUTO} min; elegível {TAXA_ELEGIVEL:.0%}")
    print(f"Economia ilustrativa triagem: ~{h_mes:.0f} h/mês")

    print("\n--- Cruzamento Dataset 2 (roteamento padrão) ---")
    d2 = pd.read_csv(CSV2)
    sens = {"HR Support", "Administrative rights"}
    vc = d2["Topic_group"].value_counts()
    n2 = len(d2)
    hum = vc[vc.index.isin(sens)].sum()
    print(f"Volume DS2: {n2:,}".replace(",", "."))
    print(f"Destino HUMANA (HR + Admin): {hum/n2:.1%} | L1 (demais): {1 - hum/n2:.1%}")
    for cat, cnt in vc.items():
        dest = "HUMANA" if cat in sens else "L1"
        print(f"  {cat}: {100*cnt/n2:.1f}% → {dest}")


if __name__ == "__main__":
    main()
