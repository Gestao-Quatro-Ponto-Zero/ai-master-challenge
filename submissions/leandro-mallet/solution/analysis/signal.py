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


def _p_2x2(k1, n1, k2, n2) -> float:
    """p-valor do qui-quadrado 2x2 (célula x resto), sem correção de continuidade."""
    n = n1 + n2
    k = k1 + k2
    if n1 == 0 or n2 == 0 or k == 0 or k == n:
        return 1.0
    obs = np.array([[k1, n1 - k1], [k2, n2 - k2]], float)
    exp = np.array([[n1 * k / n, n1 * (n - k) / n], [n2 * k / n, n2 * (n - k) / n]])
    stat = float(((obs - exp) ** 2 / exp).sum())
    return _gammaincc(0.5, stat / 2)


# ---------------------------------------------------------------- vendedor
SHRINK_M = 20          # força do encolhimento: o recorte "pesa" como 20 deals na média do vendedor
MIN_CELL_H1 = 10       # mínimo de deals no 1º semestre para um recorte concorrer a ponto forte
MIN_ACCOUNT = 10       # empresa só entra como recorte com 10+ deals do vendedor
N_PERM_AGENT = 1000


def agent_strengths(pos: pd.DataFrame, summary: dict) -> None:
    """Ponto forte por vendedor (interação vendedor x atributo) e teste fora do tempo."""
    df = pos.copy()
    df["half"] = np.where(df["close_date"] < "2017-07-01", "H1", "H2")
    dims = {"produto": "product", "serie": "series", "setor": "sector",
            "funcionarios": "employees_band", "receita": "revenue_band",
            "empresa": "account", "tempo_venda": "fast_band", "sede": "us_hq"}
    long = []
    for dname, col in dims.items():
        part = df[["opportunity_id", "sales_agent", "won", "half"]].copy()
        part["dimensao"] = dname
        part["valor"] = df[col].astype(str).to_numpy()
        long.append(part)
    long = pd.concat(long, ignore_index=True)
    # empresa só com casos suficientes dentro do vendedor
    acc_n = long[long["dimensao"] == "empresa"].groupby(["sales_agent", "valor"]).size()
    ok_acc = set(acc_n[acc_n >= MIN_ACCOUNT].index)
    is_acc = long["dimensao"] == "empresa"
    keep = ~is_acc | pd.Series(list(zip(long["sales_agent"], long["valor"]))).isin(ok_acc).to_numpy()
    long = long[keep].reset_index(drop=True)
    long["cell"] = long["sales_agent"] + " | " + long["dimensao"] + " | " + long["valor"]
    cell_codes, cell_names = pd.factorize(long["cell"])
    n_cells = len(cell_names)
    cell_agent = pd.Series(cell_names).str.split(" | ", regex=False).str[0].to_numpy()
    agents = sorted(df["sales_agent"].unique())
    agent_idx = {a: i for i, a in enumerate(agents)}
    cell_agent_i = np.array([agent_idx[a] for a in cell_agent])
    h2 = (long["half"] == "H2").to_numpy()
    # índice de cada linha longa -> linha do deal (para permutar o rótulo por deal)
    deal_pos = pd.Series(np.arange(len(df)), index=df["opportunity_id"].to_numpy())
    long_deal = deal_pos.loc[long["opportunity_id"]].to_numpy()
    deal_agent = np.array([agent_idx[a] for a in df["sales_agent"]])
    deal_h2 = (df["half"] == "H2").to_numpy()
    y0 = df["won"].to_numpy(int)

    n_h = [np.bincount(cell_codes[h2 == hh], minlength=n_cells).astype(float) for hh in (False, True)]
    agent_n_h = [np.bincount(deal_agent[deal_h2 == hh], minlength=len(agents)).astype(float) for hh in (False, True)]

    def stats(y: np.ndarray) -> dict:
        yl = y[long_deal]
        k_h = [np.bincount(cell_codes[h2 == hh], weights=yl[h2 == hh], minlength=n_cells) for hh in (False, True)]
        ak_h = [np.bincount(deal_agent[deal_h2 == hh], weights=y[deal_h2 == hh], minlength=len(agents)) for hh in (False, True)]
        pa = [ak_h[i] / np.maximum(agent_n_h[i], 1) for i in (0, 1)]
        pa_c = [pa[i][cell_agent_i] for i in (0, 1)]
        shr1 = (k_h[0] + SHRINK_M * pa_c[0]) / (n_h[0] + SHRINK_M)
        lift1 = np.where(n_h[0] >= MIN_CELL_H1, shr1 - pa_c[0], np.nan)
        raw2 = np.where(n_h[1] > 0, k_h[1] / np.maximum(n_h[1], 1), np.nan)
        lift2 = raw2 - pa_c[1]
        best, worst = [], []
        for ai in range(len(agents)):
            idx = np.where((cell_agent_i == ai) & ~np.isnan(lift1) & (n_h[1] > 0))[0]
            if len(idx) == 0:
                continue
            best.append(idx[np.nanargmax(lift1[idx])])
            worst.append(idx[np.nanargmin(lift1[idx])])
        best, worst = np.array(best), np.array(worst)
        both = (n_h[0] >= MIN_CELL_H1) & (n_h[1] >= MIN_CELL_H1)
        corr = float(np.corrcoef(lift1[both], lift2[both])[0, 1])
        return {"k_h": k_h, "pa": pa, "lift1": lift1, "lift2": lift2, "best": best, "worst": worst,
                "best_mean_lift2": float(np.mean(lift2[best])), "worst_mean_lift2": float(np.mean(lift2[worst])),
                "corr": corr, "n_corr": int(both.sum())}

    obs = stats(y0)
    rng = np.random.default_rng(SEED)
    perm_best, perm_worst, perm_corr = [], [], []
    groups_idx = [np.where(deal_agent == ai)[0] for ai in range(len(agents))]
    for _ in range(N_PERM_AGENT):
        y = y0.copy()
        for g in groups_idx:               # embaralha ganho/perda dentro do vendedor
            y[g] = rng.permutation(y0[g])
        s = stats(y)
        perm_best.append(s["best_mean_lift2"])
        perm_worst.append(s["worst_mean_lift2"])
        perm_corr.append(s["corr"])
    perm_best, perm_worst, perm_corr = map(np.array, (perm_best, perm_worst, perm_corr))

    # ---- tabela fora do tempo: ponto forte (e fraco) do 1º semestre visto no 2º
    oot_rows = []
    for kind, arr in (("forte", obs["best"]), ("fraco", obs["worst"])):
        for c in arr:
            a = cell_agent_i[c]
            k2, n2 = obs["k_h"][1][c], n_h[1][c]
            ka2, na2 = obs["pa"][1][a] * agent_n_h[1][a], agent_n_h[1][a]
            p = _p_2x2(k2, n2, ka2 - k2, na2 - n2)
            oot_rows.append({
                "vendedor": agents[a], "tipo": kind, "recorte": cell_names[c].split(" | ", 1)[1],
                "n_h1": int(n_h[0][c]), "taxa_h1": obs["k_h"][0][c] / n_h[0][c] * 100,
                "media_vendedor_h1": obs["pa"][0][a] * 100, "lift_h1_encolhido_pp": obs["lift1"][c] * 100,
                "n_h2": int(n2), "taxa_h2": k2 / n2 * 100, "media_vendedor_h2": obs["pa"][1][a] * 100,
                "lift_h2_pp": obs["lift2"][c] * 100, "p_h2_vs_resto": p,
                "p_h2_bonferroni_30": min(1.0, p * len(agents)),
                "repete": bool((obs["lift2"][c] > 0) if kind == "forte" else (obs["lift2"][c] < 0)),
                "poucos_casos_h2": n2 < MIN_N,
            })
    oot = pd.DataFrame(oot_rows)
    oot.to_csv(TABLES / "agent_strength_out_of_time.csv", index=False, lineterminator="\n")

    # ---- perfil do período inteiro (todas as células)
    k_all = obs["k_h"][0] + obs["k_h"][1]
    n_all = n_h[0] + n_h[1]
    ak_all = np.bincount(deal_agent, weights=y0, minlength=len(agents))
    an_all = np.bincount(deal_agent, minlength=len(agents)).astype(float)
    prof = pd.DataFrame({"cell": cell_names, "n": n_all.astype(int), "won": k_all.astype(int)})
    parts = prof["cell"].str.split(" | ", regex=False)
    prof["vendedor"], prof["dimensao"], prof["valor"] = parts.str[0], parts.str[1], parts.str[2]
    prof["taxa"] = prof["won"] / prof["n"] * 100
    prof["media_vendedor"] = (ak_all / an_all)[cell_agent_i] * 100
    prof["diff_pp"] = prof["taxa"] - prof["media_vendedor"]
    ci = [wilson(k, n) for k, n in zip(prof["won"], prof["n"])]
    prof["ci_low"], prof["ci_high"] = [c[0] * 100 for c in ci], [c[1] * 100 for c in ci]
    prof["taxa_encolhida"] = (prof["won"] + SHRINK_M * prof["media_vendedor"] / 100) / (prof["n"] + SHRINK_M) * 100
    prof["diff_encolhida_pp"] = prof["taxa_encolhida"] - prof["media_vendedor"]
    prof["p_value"] = [_p_2x2(k, n, ak_all[a] - k, an_all[a] - n)
                       for k, n, a in zip(prof["won"], prof["n"], cell_agent_i)]
    prof["p_bonferroni"] = np.minimum(1.0, prof["p_value"] * len(prof))
    prof["poucos_casos"] = prof["n"] < MIN_N
    prof = prof.drop(columns="cell").sort_values(["vendedor", "dimensao", "valor"])
    prof.to_csv(TABLES / "agent_profile_cells.csv", index=False, lineterminator="\n")

    bw = []
    for a, g in prof.groupby("vendedor"):
        b = g.loc[g["diff_encolhida_pp"].idxmax()]
        w = g.loc[g["diff_encolhida_pp"].idxmin()]
        non_us = df[(df["sales_agent"] == a) & (df["us_hq"] != "EUA")]
        bw.append({
            "vendedor": a, "deals": int(an_all[agent_idx[a]]), "media": ak_all[agent_idx[a]] / an_all[agent_idx[a]] * 100,
            "deals_empresa_fora_eua": len(non_us), "empresas_fora_eua": int(non_us["account"].nunique()),
            "melhor_recorte": f'{b["dimensao"]} = {b["valor"]}', "melhor_n": int(b["n"]), "melhor_taxa": b["taxa"],
            "melhor_ci": f'{b["ci_low"]:.1f}–{b["ci_high"]:.1f}', "melhor_encolhida": b["taxa_encolhida"],
            "melhor_p_bonf": b["p_bonferroni"], "melhor_poucos_casos": bool(b["poucos_casos"]),
            "pior_recorte": f'{w["dimensao"]} = {w["valor"]}', "pior_n": int(w["n"]), "pior_taxa": w["taxa"],
            "pior_ci": f'{w["ci_low"]:.1f}–{w["ci_high"]:.1f}', "pior_encolhida": w["taxa_encolhida"],
            "pior_p_bonf": w["p_bonferroni"], "pior_poucos_casos": bool(w["poucos_casos"]),
        })
    pd.DataFrame(bw).to_csv(TABLES / "agent_best_worst.csv", index=False, lineterminator="\n")

    # quantas células "significativas" no período inteiro x o que o acaso daria
    sig_obs = int((prof["p_value"] < 0.05).sum())
    fortes = oot[oot["tipo"] == "forte"]
    summary["agent_strengths"] = {
        "cells": int(len(prof)), "shrink_m": SHRINK_M, "min_cell_h1": MIN_CELL_H1, "min_account": MIN_ACCOUNT,
        "halves": "H1 = fechados até 2017-06-30; H2 = 2017-07-01 em diante",
        "cells_p_lt_005": sig_obs, "cells_p_lt_005_expected_if_noise": round(0.05 * len(prof), 1),
        "cells_significant_bonferroni": int((prof["p_bonferroni"] < 0.05).sum()),
        "best_h1_mean_lift_h2_pp": round(obs["best_mean_lift2"] * 100, 2),
        "best_perm_mean_pp": round(float(perm_best.mean()) * 100, 2),
        "best_perm_p95_pp": round(float(np.quantile(perm_best, .95)) * 100, 2),
        "best_p_value_perm": float((np.sum(perm_best >= obs["best_mean_lift2"]) + 1) / (N_PERM_AGENT + 1)),
        "worst_h1_mean_lift_h2_pp": round(obs["worst_mean_lift2"] * 100, 2),
        "worst_perm_mean_pp": round(float(perm_worst.mean()) * 100, 2),
        "worst_p_value_perm": float((np.sum(perm_worst <= obs["worst_mean_lift2"]) + 1) / (N_PERM_AGENT + 1)),
        "corr_lift_h1_h2": round(obs["corr"], 4), "corr_cells": obs["n_corr"],
        "corr_perm_mean": round(float(perm_corr.mean()), 4),
        "corr_perm_p95": round(float(np.quantile(perm_corr, .95)), 4),
        "corr_p_value_perm": float((np.sum(perm_corr >= obs["corr"]) + 1) / (N_PERM_AGENT + 1)),
        "strong_repeats_h2": int(fortes["repete"].sum()), "agents": int(len(fortes)),
        "strong_confirmed_bonferroni": fortes.loc[(fortes["lift_h2_pp"] > 0) & (fortes["p_h2_bonferroni_30"] < 0.05),
                                                  ["vendedor", "recorte", "lift_h2_pp", "p_h2_bonferroni_30"]].round(4).to_dict(orient="records"),
    }


MIN_CELL_WINDOW = 10   # mínimo de deals do recorte na janela de 3 meses
AGENT_DIMS = {"produto": "product", "serie": "series", "setor": "sector",
              "funcionarios": "employees_band", "receita": "revenue_band",
              "empresa": "account", "tempo_venda": "fast_band", "sede": "us_hq"}


def agent_momentum(pos: pd.DataFrame, summary: dict) -> None:
    """Ponto forte do vendedor em média móvel de 3 meses (pela data de fechamento)."""
    df = pos.copy().reset_index(drop=True)
    months = pd.period_range(df["close_date"].min(), df["close_date"].max(), freq="M")
    m_idx = {p: i for i, p in enumerate(months)}
    df["m"] = df["close_date"].dt.to_period("M").map(m_idx).astype(int)
    n_m = len(months)
    agents = sorted(df["sales_agent"].unique())
    a_idx = {a: i for i, a in enumerate(agents)}
    deal_a = df["sales_agent"].map(a_idx).to_numpy()

    rows_a, rows_v, rows_d = [], [], []
    for dname, col in AGENT_DIMS.items():
        rows_a.append(df["sales_agent"].to_numpy())
        rows_v.append((dname + " = " + df[col].astype(str)).to_numpy())
        rows_d.append(np.arange(len(df)))
    la, lv, ld = np.concatenate(rows_a), np.concatenate(rows_v), np.concatenate(rows_d)
    cell_codes, cell_names = pd.factorize(pd.Series(la) + " | " + pd.Series(lv))
    n_cells = len(cell_names)
    cell_agent = np.array([a_idx[c.split(" | ", 1)[0]] for c in cell_names])
    l_month = df["m"].to_numpy()[ld]
    key = cell_codes * n_m + l_month
    N = np.bincount(key, minlength=n_cells * n_m).reshape(n_cells, n_m).astype(float)
    AN = np.bincount(deal_a * n_m + df["m"].to_numpy(), minlength=len(agents) * n_m).reshape(len(agents), n_m).astype(float)

    def roll3(x):  # soma da janela que termina em cada mês (m-2..m)
        c = np.cumsum(x, axis=1)
        out = c.copy()
        out[:, 3:] = c[:, 3:] - c[:, :-3]
        return out

    NW, ANW = roll3(N), roll3(AN)
    first_full = 2                       # 1ª janela completa termina no 3º mês (mai/2017)
    y0 = df["won"].to_numpy(int)

    def compute(y):
        K = np.bincount(key, weights=y[ld], minlength=n_cells * n_m).reshape(n_cells, n_m)
        AK = np.bincount(deal_a * n_m + df["m"].to_numpy(), weights=y,
                         minlength=len(agents) * n_m).reshape(len(agents), n_m)
        KW, AKW = roll3(K), roll3(AK)
        pa_w = AKW / np.maximum(ANW, 1)
        shr = (KW + SHRINK_M * pa_w[cell_agent]) / (NW + SHRINK_M)
        score = np.where(NW >= MIN_CELL_WINDOW, shr, -np.inf)
        best = np.full((len(agents), n_m), -1)
        for ai in range(len(agents)):
            cols = score[cell_agent == ai]
            ids = np.where(cell_agent == ai)[0]
            arg = np.argmax(cols, axis=0)
            ok = np.isfinite(cols[arg, np.arange(n_m)])
            best[ai] = np.where(ok, ids[arg], -1)
        # acerto: o forte da janela que termina em m converte acima do vendedor no mês m+1?
        hits = ties = trials = 0
        lifts = []
        for m in range(first_full, n_m - 1):
            for ai in range(len(agents)):
                c = best[ai, m]
                if c < 0 or N[c, m + 1] == 0 or AN[ai, m + 1] == 0:
                    continue
                rc = K[c, m + 1] / N[c, m + 1]
                ra = AK[ai, m + 1] / AN[ai, m + 1]
                trials += 1
                hits += rc > ra
                ties += rc == ra
                lifts.append(rc - ra)
        return {"K": K, "AK": AK, "KW": KW, "AKW": AKW, "pa_w": pa_w, "shr": shr, "best": best,
                "hit_rate": hits / max(trials, 1), "ties": ties, "trials": trials,
                "mean_lift_next": float(np.mean(lifts)) if lifts else float("nan")}

    obs = compute(y0)
    rng = np.random.default_rng(SEED)
    groups = [np.where(deal_a == ai)[0] for ai in range(len(agents))]
    perm_hit, perm_lift = [], []
    for _ in range(N_PERM_AGENT):
        y = y0.copy()
        for g in groups:
            y[g] = rng.permutation(y0[g])
        s = compute(y)
        perm_hit.append(s["hit_rate"])
        perm_lift.append(s["mean_lift_next"])
    perm_hit, perm_lift = np.array(perm_hit), np.array(perm_lift)

    last = n_m - 1
    cur_rows, series_rows = [], []
    for ai, a in enumerate(agents):
        c = obs["best"][ai, last]
        if c < 0:
            cur_rows.append({"vendedor": a, "ponto_forte_atual": None})
            continue
        lo, hi = wilson(obs["KW"][c, last], NW[c, last])
        cur_rows.append({
            "vendedor": a, "janela": f"{months[last - 2]}..{months[last]}",
            "ponto_forte_atual": cell_names[c].split(" | ", 1)[1],
            "n_janela": int(NW[c, last]), "ganhos_janela": int(obs["KW"][c, last]),
            "taxa_janela": obs["KW"][c, last] / NW[c, last] * 100,
            "ci_low": lo * 100, "ci_high": hi * 100,
            "taxa_encolhida": obs["shr"][c, last] * 100,
            "taxa_geral_vendedor_janela": obs["pa_w"][ai, last] * 100,
            "n_geral_vendedor_janela": int(ANW[ai, last]),
            "diff_pp": (obs["KW"][c, last] / NW[c, last] - obs["pa_w"][ai, last]) * 100,
            "diff_encolhida_pp": (obs["shr"][c, last] - obs["pa_w"][ai, last]) * 100,
            "p_vs_resto_vendedor": _p_2x2(obs["KW"][c, last], NW[c, last],
                                          obs["AKW"][ai, last] - obs["KW"][c, last], ANW[ai, last] - NW[c, last]),
            "poucos_casos": NW[c, last] < MIN_N,
        })
        for m in range(first_full, n_m):
            series_rows.append({
                "vendedor": a, "ponto_forte_atual": cell_names[c].split(" | ", 1)[1],
                "janela_fim": str(months[m]), "n_recorte": int(NW[c, m]),
                "taxa_recorte_mm3": obs["KW"][c, m] / NW[c, m] * 100 if NW[c, m] else np.nan,
                "taxa_recorte_mm3_encolhida": obs["shr"][c, m] * 100,
                "taxa_vendedor_mm3": obs["pa_w"][ai, m] * 100, "n_vendedor": int(ANW[ai, m]),
                "forte_da_janela": cell_names[obs["best"][ai, m]].split(" | ", 1)[1] if obs["best"][ai, m] >= 0 else None,
            })
    cur = pd.DataFrame(cur_rows)
    cur["p_bonferroni_30"] = np.minimum(1.0, cur["p_vs_resto_vendedor"] * len(agents))
    cur.to_csv(TABLES / "agent_strength_current_mm3.csv", index=False, lineterminator="\n")
    pd.DataFrame(series_rows).to_csv(TABLES / "agent_strength_mm3_series.csv", index=False, lineterminator="\n")

    # quantas vezes o ponto forte troca de um mês para o outro
    changes = []
    for ai in range(len(agents)):
        b = obs["best"][ai, first_full:]
        changes.append(int((b[1:] != b[:-1]).sum()))
    summary["agent_momentum"] = {
        "window": "3 meses pela data de fechamento; janelas terminando de "
                  f"{months[first_full]} a {months[last]}",
        "min_cell_window": MIN_CELL_WINDOW, "shrink_m": SHRINK_M,
        "current_window": f"{months[last - 2]}..{months[last]}",
        "current_diff_pp_mean": round(float(cur["diff_pp"].mean()), 2),
        "current_diff_encolhida_pp_mean": round(float(cur["diff_encolhida_pp"].mean()), 2),
        "current_significant_bonferroni": int((cur["p_bonferroni_30"] < 0.05).sum()),
        "current_poucos_casos": int(cur["poucos_casos"].sum()),
        "strength_changes_per_agent_mean": round(float(np.mean(changes)), 2),
        "strength_changes_max_possible": int(n_m - first_full - 1),
        "next_month_trials": obs["trials"], "next_month_ties": int(obs["ties"]),
        "next_month_hit_rate": round(obs["hit_rate"], 4),
        "next_month_hit_rate_perm_mean": round(float(perm_hit.mean()), 4),
        "next_month_hit_rate_perm_p95": round(float(np.quantile(perm_hit, .95)), 4),
        "next_month_hit_p_value_perm": float((np.sum(perm_hit >= obs["hit_rate"]) + 1) / (N_PERM_AGENT + 1)),
        "next_month_mean_lift_pp": round(obs["mean_lift_next"] * 100, 2),
        "next_month_mean_lift_perm_mean_pp": round(float(perm_lift.mean()) * 100, 2),
        "next_month_mean_lift_perm_p95_pp": round(float(np.quantile(perm_lift, .95)) * 100, 2),
        "next_month_lift_p_value_perm": float((np.sum(perm_lift >= obs["mean_lift_next"]) + 1) / (N_PERM_AGENT + 1)),
    }


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

    # Faixas de tempo de venda por percentil (Won + Lost juntos).
    # Empates: corte pelo VALOR do dia. O limite de cada faixa é o menor dia d
    # com F(d) >= p (np.quantile, method="inverted_cdf"), e todos os deals com
    # duração <= d ficam nela. Deals com a mesma duração nunca são separados,
    # por isso o tamanho real de cada faixa difere do nominal.
    pct = [0.05, 0.20, 0.50, 0.70, 0.95]
    labels_p = ["até P5 (5% mais rápidas)", "P5–P20", "P20–P50", "P50–P70", "P70–P95", "acima de P95 (5% mais lentas)"]
    nominal = [5, 15, 30, 20, 25, 5]
    cuts_d = [int(np.quantile(closed["cycle_days"], p, method="inverted_cdf")) for p in pct]
    edges = [-1] + cuts_d + [10_000]
    closed["speed_band"] = pd.cut(closed["cycle_days"], edges, labels=labels_p)
    total_deals = len(deals)
    rows = []
    for lab, nom in zip(labels_p, nominal):
        s = closed[closed["speed_band"] == lab]
        k, n = int(s["won"].sum()), len(s)
        lo, hi = wilson(k, n)
        rows.append({
            "faixa": lab, "dias_min": int(s["cycle_days"].min()), "dias_max": int(s["cycle_days"].max()),
            "deals": n, "pct_fechados": n / len(closed) * 100, "pct_nominal": nom,
            "pct_total_8800": n / total_deals * 100, "won": k, "lost": n - k,
            "conversao_pct": k / n * 100, "perda_pct": (n - k) / n * 100,
            "conversao_ci_low": lo * 100, "conversao_ci_high": hi * 100,
        })
    sb = pd.DataFrame(rows)
    sb.to_csv(TABLES / "speed_bands_by_percentile.csv", index=False, lineterminator="\n")
    summary["speed_bands"] = {
        "cut_days": dict(zip(["P5", "P20", "P50", "P70", "P95"], cuts_d)),
        "tie_rule": "corte por valor do dia (inverted_cdf); empates ficam juntos na faixa de baixo",
        "test": chi2_test(closed["speed_band"].astype(str), closed["won"]),
        "rows": sb.round(2).to_dict(orient="records"),
    }

    # ------------------------------------------------------------ perdas rápidas
    # Faixas por POSIÇÃO: ordena por duração e desempata por opportunity_id.
    # Cada deal cai em uma faixa só e os tamanhos batem com o nominal; um mesmo
    # dia pode ficar dividido entre duas faixas (mostrado em fast_band_boundaries).
    pos = closed.sort_values(["cycle_days", "opportunity_id"]).reset_index(drop=True)
    n_cl = len(pos)
    b1, b2 = round(0.05 * n_cl), round(0.15 * n_cl)
    pos["fast_band"] = np.select([pos.index < b1, pos.index < b2], ["faixa 1 (0–5%)", "faixa 2 (5–15%)"], "demais (15–100%)")
    bnd = []
    for name, cut in [("faixa 1 | faixa 2", b1), ("faixa 2 | demais", b2)]:
        day = int(pos.loc[cut - 1, "cycle_days"])
        same = pos[pos["cycle_days"] == day]
        bnd.append({"fronteira": name, "dia": day,
                    "deals_com_esse_dia": len(same),
                    "ficaram_antes": int((same.index < cut).sum()),
                    "ficaram_depois": int((same.index >= cut).sum())})
    pd.DataFrame(bnd).to_csv(TABLES / "fast_band_boundaries.csv", index=False, lineterminator="\n")
    fb = pos.groupby("fast_band").agg(deals=("won", "size"), won=("won", "sum"),
                                      dias_min=("cycle_days", "min"), dias_max=("cycle_days", "max")).reset_index()
    fb["lost"] = fb["deals"] - fb["won"]
    fb["perda_pct"] = fb["lost"] / fb["deals"] * 100
    fb.to_csv(TABLES / "fast_bands_by_position.csv", index=False, lineterminator="\n")

    pos["close_month"] = pos["close_date"].dt.month
    pos["engage_month"] = pos["engage_date"].dt.month
    fast = pos["fast_band"] != "demais (15–100%)"
    lost = pos["won"] == 0
    groups = {
        "lost_rapidos": pos[fast & lost],
        "lost_demais": pos[~fast & lost],
        "won_rapidos": pos[fast & ~lost],
        "base_fechados": pos,
    }
    comparisons = [("lost_rapidos", "lost_demais"), ("lost_rapidos", "won_rapidos"), ("lost_rapidos", "base_fechados")]
    dims = ["regional_office", "manager", "close_month", "engage_month"]
    n_cells = sum(pos[d].nunique() for d in dims) * len(comparisons)
    n_global = len(dims) * len(comparisons)
    rows, glob = [], {}
    for dim in dims:
        for a, b in comparisons:
            ga, gb = groups[a], groups[b]
            # teste global: a distribuição da dimensão difere entre os dois grupos?
            if b == "base_fechados":   # A está contido na base: compara A com o resto da base
                gb_test = pos.drop(ga.index)
            else:
                gb_test = gb
            lab = pd.Series(["A"] * len(ga) + ["B"] * len(gb_test))
            val = pd.concat([ga[dim], gb_test[dim]]).astype(str).reset_index(drop=True)
            t = chi2_test(val, (lab == "A").astype(int))
            glob[f"{dim} | {a} x {b}"] = {"p_value": t["p_value"], "p_bonferroni": min(1.0, t["p_value"] * n_global),
                                          "cramers_v": t["cramers_v"]}
            for v in sorted(pos[dim].unique()):
                ka, na = int((ga[dim] == v).sum()), len(ga)
                kb, nb = int((gb_test[dim] == v).sum()), len(gb_test)
                lo, hi = wilson(ka, na)
                cell = chi2_test(pd.Series(["A"] * na + ["B"] * nb),
                                 pd.Series([1] * ka + [0] * (na - ka) + [1] * kb + [0] * (nb - kb)))
                rows.append({
                    "dimensao": dim, "valor": v, "grupo_a": a, "grupo_b": b,
                    "n_a": ka, "pct_a": ka / na * 100, "ci_low_a": lo * 100, "ci_high_a": hi * 100,
                    "n_b": int((gb[dim] == v).sum()), "pct_b": (gb[dim] == v).mean() * 100,
                    "diff_pp": (ka / na - (gb[dim] == v).mean()) * 100,
                    "p_value": cell["p_value"], "p_bonferroni": min(1.0, cell["p_value"] * n_cells),
                    "poucos_casos": ka < MIN_N,
                })
    fl = pd.DataFrame(rows)
    fl.to_csv(TABLES / "fast_lost_patterns.csv", index=False, lineterminator="\n")
    summary["fast_lost"] = {
        "band_sizes": fb.set_index("fast_band")[["deals", "lost", "dias_min", "dias_max"]].to_dict(orient="index"),
        "boundaries": bnd,
        "group_sizes": {k: int(len(v)) for k, v in groups.items()},
        "global_tests": glob,
        "n_cell_tests": n_cells,
        "cells_significant_after_bonferroni": fl.loc[fl["p_bonferroni"] < 0.05,
                                                     ["dimensao", "valor", "grupo_b", "pct_a", "pct_b", "diff_pp", "p_bonferroni"]].round(4).to_dict(orient="records"),
    }

    agent_strengths(pos, summary)
    agent_momentum(pos, summary)

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
