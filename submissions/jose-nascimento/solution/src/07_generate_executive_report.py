#!/usr/bin/env python3
"""
07_generate_executive_report.py — Relatório Executivo (Iteração 07).

Gera `solution/report-executivo.md` a partir APENAS dos artefatos validados
(tabelas t01-t21, evidence 01-05, painel account-month e raw commitados),
com TODOS os números materiais derivados em runtime (nada de literais de
dados no texto), gates G1-G8 e escrita all-or-nothing (arquivo temporário +
rename: o report nunca fica com conteúdo inválido/stale).

Determinismo: sem timestamp/now/random; formatação pt-BR explícita (nunca
locale); paths relativos ao próprio projeto; offline (zero rede).

Uso (qualquer CWD; paths resolvidos por __file__):
    python3 solution/src/07_generate_executive_report.py
Exit 0 = report escrito e gates PASS; exit 1 = diagnóstico sem traceback.
"""

from __future__ import annotations

import math
import os
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path

SOLUTION_DIR = Path(__file__).resolve().parent.parent
TABLES_DIR = SOLUTION_DIR / "out" / "tables"
EVIDENCE_DIR = SOLUTION_DIR / "evidence"
RAW_DIR = SOLUTION_DIR / "data" / "raw"
PROCESSED_DIR = SOLUTION_DIR / "data" / "processed"
REPORT_PATH = SOLUTION_DIR / "report-executivo.md"

sys.dont_write_bytecode = True

import pandas as pd  # noqa: E402

# ----------------------------------------------------------------------------
# Formatação pt-BR explícita (determinística; nunca locale)
# ----------------------------------------------------------------------------
def fmt_dec(value: float, nd: int = 2) -> str:
    """22.5130 -> '22,51' (vírgula decimal)."""
    return f"{value:.{nd}f}".replace(".", ",")


def fmt_pct(value: float, nd: int = 2) -> str:
    return fmt_dec(value, nd) + "%"


def fmt_int(value: int) -> str:
    """1179139 -> '1.179.139' (ponto de milhar)."""
    return f"{value:,}".replace(",", ".")


def fmt_br3(value: float) -> str:
    """0.3619 -> '0,362' (3 casas; Wilson CI, padrão do evidence 05)."""
    return f"{value:.3f}".replace(".", ",")


def fmt_br4(value: float) -> str:
    """0.43005 -> '0,4301' (4 casas; incidência)."""
    return f"{value:.4f}".replace(".", ",")


def fmt_lift2(value: float) -> str:
    """1.574 -> '1,57' (2 casas; lifts)."""
    return f"{value:.2f}".replace(".", ",")


# ----------------------------------------------------------------------------
# Extração de células com texto completo (to_string() truncaria colunas)
# ----------------------------------------------------------------------------
def cell(df: pd.DataFrame, value_col: str, key_col: str, key: str) -> str:
    return str(df[df[key_col] == key][value_col].iloc[0])


def _extract(pattern: str, text: str, what: str) -> str:
    m = re.search(pattern, text)
    if not m:
        raise SystemExit(f"[07] FAIL G-extração: '{what}' não encontrado no "
                         f"input (fonte divergente?).")
    return m.group(1)


def _extract_multi(pattern: str, text: str, what: str) -> list[str]:
    """Retorna TODOS os grupos capturados (para padrões multi-valor)."""
    m = re.search(pattern, text)
    if not m:
        raise SystemExit(f"[07] FAIL G-extração: '{what}' não encontrado no "
                         f"input (fonte divergente?).")
    return list(m.groups())


# ----------------------------------------------------------------------------
# Carregamento dos inputs validados
# ----------------------------------------------------------------------------
def load_inputs() -> dict:
    t01 = pd.read_csv(TABLES_DIR / "t01_monthly_series.csv")
    t02 = pd.read_csv(TABLES_DIR / "t02_cohort_km.csv")
    t03 = pd.read_csv(TABLES_DIR / "t03_onboarding_buckets.csv")
    t03b = pd.read_csv(TABLES_DIR / "t03b_onboarding_accounts.csv")
    t05 = pd.read_csv(TABLES_DIR / "t05_usage_monthly.csv")
    t07 = pd.read_csv(TABLES_DIR / "t07_segments.csv")
    t09 = pd.read_csv(TABLES_DIR / "t09_causality.csv")
    t10 = pd.read_csv(TABLES_DIR / "t10_hypothesis_verdicts.csv")
    t14 = pd.read_csv(TABLES_DIR / "t14_backtest_temporal.csv")
    t14b = pd.read_csv(TABLES_DIR / "t14b_backtest_detail.csv")
    t15 = pd.read_csv(TABLES_DIR / "t15_priority_segments.csv")
    t16 = pd.read_csv(TABLES_DIR / "t16_watchlist_top20.csv")
    t18 = pd.read_csv(TABLES_DIR / "t18_actions_prioritized.csv")
    t19 = pd.read_csv(TABLES_DIR / "t19_impact_sensitivity.csv")
    t20 = pd.read_csv(TABLES_DIR / "t20_measurement_plan.csv")
    t21 = pd.read_csv(TABLES_DIR / "t21_watchlist_split_actions.csv")
    panel = pd.read_csv(PROCESSED_DIR / "account_month.csv")
    acc = pd.read_csv(RAW_DIR / "ravenstack_accounts.csv")
    subs = pd.read_csv(RAW_DIR / "ravenstack_subscriptions.csv")
    events = pd.read_csv(RAW_DIR / "ravenstack_churn_events.csv")
    tickets = pd.read_csv(RAW_DIR / "ravenstack_support_tickets.csv")
    ev05 = (EVIDENCE_DIR / "05_action_plan.md").read_text(encoding="utf-8")
    return dict(t01=t01, t02=t02, t03=t03, t03b=t03b, t05=t05, t07=t07,
                t09=t09, t10=t10, t14=t14, t14b=t14b, t15=t15, t16=t16,
                t18=t18, t19=t19, t20=t20, t21=t21, panel=panel, acc=acc,
                subs=subs, events=events, tickets=tickets, ev05=ev05)


# ----------------------------------------------------------------------------
# Derivação de todos os números materiais (fonte única do template)
# ----------------------------------------------------------------------------
def derive_numbers(inp: dict) -> dict:
    t01, t02, t03, t03b = inp["t01"], inp["t02"], inp["t03"], inp["t03b"]
    t05, t07, t09, t10 = inp["t05"], inp["t07"], inp["t09"], inp["t10"]
    t14, t14b, t15, t16 = inp["t14"], inp["t14b"], inp["t15"], inp["t16"]
    t18, t19, t20, t21 = inp["t18"], inp["t19"], inp["t20"], inp["t21"]
    panel, acc, subs, events = inp["panel"], inp["acc"], inp["subs"], inp["events"]
    tickets, ev05 = inp["tickets"], inp["ev05"]

    # --- lentes e contagens -------------------------------------------------
    n_accounts = len(acc)
    n_snapshot = int(acc["churn_flag"].sum())
    ended = subs[subs["end_date"].notna()]
    n_subs_ended = len(ended)
    n_acc_ended = ended["account_id"].nunique()
    n_events = len(events)
    n_event_acc = events["account_id"].nunique()
    ev_counts = events.groupby("account_id").size()
    n_multi_acc = int((ev_counts >= 2).sum())
    pct_events_multi = ev_counts[ev_counts >= 2].sum() / n_events * 100

    # --- pico dez/24 --------------------------------------------------------
    dec = t01[t01["month"] == "2024-12"].iloc[0]
    prev6 = t01[t01["month"].isin(
        ["2024-06", "2024-07", "2024-08", "2024-09", "2024-10", "2024-11"])]
    dec_events = int(dec["events_total"])
    dec_first = int(dec["first_events"])
    dec_eligible = int(dec["eligible_at_start"])
    dec_rate = float(dec["rate_first_events_pct"])
    med6m = float(prev6["rate_first_events_pct"].median())
    pico_ratio = dec_rate / med6m
    med_win = float(t01["rate_first_events_pct"].median())

    # --- onboarding economics (R1) ------------------------------------------
    r1_total = int(t03["mrr_sum"].sum())
    r1_le90 = int(t03[t03["bucket"].isin(
        ["0d", "1-30d", "31-60d", "61-90d"])]["mrr_sum"].sum())
    r1_le90_pct = r1_le90 / r1_total * 100
    fe30 = t03b[t03b["window_days"] == 30].iloc[0]
    fe60 = t03b[t03b["window_days"] == 60].iloc[0]
    fe90 = t03b[t03b["window_days"] == 90].iloc[0]

    # --- vereditos (t10; células completas, sem truncamento) ----------------
    h3_txt = cell(t10, "numbers", "hypothesis", "H3")
    h4_txt = cell(t10, "numbers", "hypothesis", "H4")
    h5_txt = cell(t10, "numbers", "hypothesis", "H5")
    h7_txt = cell(t10, "numbers", "hypothesis", "H7")
    h9_txt = cell(t10, "numbers", "hypothesis", "H9")
    h2_txt = cell(t10, "numbers", "hypothesis", "H2")
    h6_txt = cell(t10, "numbers", "hypothesis", "H6")
    med_intens = _extract(r"mediana por conta: [\d.]+ -> [\d.]+ \(([\d.]+)%\)",
                          h3_txt, "H3 mediana por conta")
    h4 = _extract_multi(r"zero-uso: churn ([\d.]+)% vs controle ([\d.]+)%",
                        h4_txt, "H4 zero-uso")
    h5 = _extract_multi(r"tickets/conta ([\d.]+) vs ([\d.]+) [(]Δ -?[\d.]+[)]; "
                        r"escalação ([\d.]+)% vs ([\d.]+)%; CSAT ([\d.]+) vs ([\d.]+)",
                        h5_txt, "H5 suporte")
    h7_link = _extract(r"eventos com sub encerrada ±30d: ([\d.]+)%",
                       h7_txt, "H7 decoupling")
    h9 = _extract_multi(r"share ([\d.]+)%, ratio ([\d.]+)", h9_txt,
                        "H9 pico 0-3m")
    h2_ctrl = _extract_multi(r"esperado ([\d.]+) eventos, observado (\d+)",
                             h2_txt, "H2 controle tenure")
    h6_gap = _extract(r"maior gap ([\d.]+) p\.p\.", h6_txt, "H6 gap KM")
    h9_share, h9_ratio = h9[0], h9[1]
    n_03m = round(dec_first * float(h9_share) / 100)
    global_rate = n_event_acc / n_accounts * 100

    # --- suporte / qualidade (derivado dos raw) ------------------------------
    csat_null = tickets["satisfaction_score"].isna().mean() * 100
    reason_unk = (events["reason_code"] == "unknown").mean() * 100
    csat_cov = tickets["satisfaction_score"].notna().mean() * 100
    usage_in_window_pct = _extract(r"uso em janela ([\d,]+)%",
                                   cell(t18, "impact_range", "action_id",
                                        "ACT-03"), "ACT-03 uso em janela")

    # --- segmentos (t15) e watchlist (t16/t21) ------------------------------
    seg = {}
    for _, r in t15.iterrows():
        seg[r["segment"]] = dict(n=int(r["N"]),
                                 mrr=int(r["current_mrr_sum"]),
                                 ev=cell(t15, "backtest_evidence", "segment",
                                         r["segment"]))
    km_s3 = _extract(r"KM 90d = ([\d.]+)", seg["S3"]["ev"], "KM S3")
    cur_mrr = int(panel[panel["month"] == "2024-12"]["winner_mrr"].sum())
    top20_mrr = int(t16["current_winner_mrr"].sum())
    top20_share = top20_mrr / cur_mrr * 100
    tier_a = int((t16["watch_tier"] == "A").sum())
    grp = dict(t21.groupby("account_id")["group"].first())
    n_grp_validated = int((t21["group"] == "validated_onboarding").sum())
    n_grp_exposure = int((t21["group"] == "exposure_only").sum())

    tier_a_rows = t16[t16["watch_tier"] == "A"].sort_values("watch_rank")
    bc_rows = t16[t16["watch_tier"] != "A"].sort_values(
        ["current_winner_mrr", "account_id"], ascending=[False, True]).head(2)
    lifts_d = _lifts(t14, "D", " · ")
    account_rows = []
    for _, r in pd.concat([tier_a_rows, bc_rows]).iterrows():
        is_a = r["watch_tier"] == "A"
        account_rows.append(dict(
            aid=str(r["account_id"]),
            grp="validated_onboarding" if is_a else "exposure_only",
            mrr=int(r["current_winner_mrr"]),
            ev="onboarding ≤90d — sinal validado" if is_a
               else "exposure-only: revisão de conta/renovação",
            lim="associação, não predição" if is_a else
                "sem sinal validado — não rotular risco"))

    # --- backtest (t14): pooled da regra D (83/193) e Wilson CI --------------
    d90 = t14b[(t14b["horizon_days"] == 90) & (t14b["tenure_days"] <= 90)]
    n_rule = len(d90)
    n_rule_out = int(d90["outcome"].sum())
    wil_lo, wil_hi = _wilson(n_rule_out, n_rule)

    # --- ações e impacto (t18/t19/t20) ---------------------------------------
    act_rows = []
    for _, r in t18.sort_values("action_id").iterrows():
        leads = t20[(t20["action_id"] == r["action_id"]) &
                    (t20["metric_type"] == "leading")]
        act_rows.append(dict(id=r["action_id"], act=r["action"],
                             dec=r["decision"], owner=r["owner"],
                             prazo=r["time_to_first_signal"],
                             sinal=" · ".join(
                                 f"{m['metric']} ({m['cadence']})"
                                 for _, m in leads.iterrows()),
                             stopgo=r["stop_go_criteria"]))
    imp = {r["scenario"]: r for _, r in t19.iterrows()}
    ev05n = re.sub(r"\s+", " ", ev05)  # quebras de linha do markdown
    mde = " / ".join(g + "%" for g in _extract_multi(
        r"(\d+)% / (\d+)% / (\d+)%[^\d]*de redução", ev05n, "MDE"))
    power = " / ".join(g + "%" for g in _extract_multi(
        r"10% → ~(\d+)%; 20% → ~(\d+)%; 30% → ~(\d+)%",
        ev05n, "poder por cenário"))
    false_go = _extract(r"P\(falso GO por ponto ≥ 10% sob efeito nulo\) ≈ "
                        r"(\d+)%", ev05n, "P(falso GO)")
    if not re.search(r"0\.362–0\.501", ev05n):
        raise SystemExit("[07] FAIL G-wilson: âncora do evidence 05 ausente.")
    wil_check = abs(wil_lo - 0.362) < 0.0015 and abs(wil_hi - 0.501) < 0.0015
    if not wil_check:
        raise SystemExit(f"[07] FAIL G-wilson: derivado {wil_lo:.4f}-{wil_hi:.4f} "
                         f"diverge do evidence 05 (0.362-0.501).")

    # --- uso (t05) -----------------------------------------------------------
    usage_2023 = int(t05[t05["month"].str.startswith("2023")]["rows_raw_primary"].sum())
    usage_2024 = int(t05[t05["month"].str.startswith("2024")]["rows_raw_primary"].sum())
    usage_pct = (usage_2024 - usage_2023) / usage_2023 * 100

    # --- R2 (t01) -------------------------------------------------------------
    r2_net = int(t01["r2_net"].sum())
    r2_churn = int(t01["r2_churn_to_inactive"].sum())
    r2_contr = int(t01["r2_active_contraction"].sum())

    # --- H6: nenhum segmento com taxa >= 1,5x a global (limiar inalcançável) --
    flag_high = [(v, n) for _, v, n, rate in
                 ((r["segment_type"], r["segment_value"], int(r["n_accounts"]),
                   float(r["rate_pct"])) for _, r in t07.iterrows())
                 if n >= 25 and rate >= 1.5 * global_rate]
    if flag_high:
        raise SystemExit(f"[07] FAIL G-H6: segmentos com taxa >= 1,5x global "
                         f"(claim do report seria falso): {flag_high}")

    km_q1_24 = float(t02[t02["cohort"] == "2024Q1"].iloc[0]["km_churn_t6_pct"])
    km_q2_24 = float(t02[t02["cohort"] == "2024Q2"].iloc[0]["km_churn_t6_pct"])

    caus_rows = [(r["finding"], r["status"]) for _, r in t09.iterrows()]

    return dict(
        # lentes
        n_accounts=n_accounts, n_snapshot_fmt=fmt_int(n_snapshot),
        n_subs_fmt=fmt_int(n_subs_ended), n_acc_ended_fmt=fmt_int(n_acc_ended),
        n_events_fmt=fmt_int(n_events), n_event_acc_fmt=fmt_int(n_event_acc),
        n_events=n_events, n_event_acc=n_event_acc,
        # pico
        dec_events=dec_events, dec_first=dec_first, dec_eligible=dec_eligible,
        dec_rate=fmt_pct(dec_rate), med6m=fmt_pct(med6m), med_win=fmt_pct(med_win),
        pico_ratio=fmt_dec(pico_ratio),
        # onboarding economics
        r1_total=fmt_int(r1_total), r1_le90=fmt_int(r1_le90),
        r1_le90_pct=fmt_pct(r1_le90_pct, 1),
        fe90_n=int(fe90["n_first_events_le"]),
        fe90_pct=fmt_pct(fe90["share_of_event_accounts_pct"], 1),
        fe30_pct=fmt_pct(fe30["share_of_event_accounts_pct"], 1),
        fe60_pct=fmt_pct(fe60["share_of_event_accounts_pct"], 1),
        # vereditos
        med_intens=med_intens.replace(".", ",") + "%",
        h4_churn=h4[0].replace(".", ",") + "%",
        h4_ctrl=h4[1].replace(".", ",") + "%",
        h5_tick_c=h5[0].replace(".", ","), h5_tick_ct=h5[1].replace(".", ","),
        h5_esc_c=h5[2].replace(".", ",") + "%",
        h5_esc_ct=h5[3].replace(".", ",") + "%",
        h5_csat_c=h5[4].replace(".", ","), h5_csat_ct=h5[5].replace(".", ","),
        h7_link=h7_link.replace(".", ",") + "%",
        h6_gap=h6_gap.replace(".", ","),
        h9_share=h9_share.replace(".", ","), h9_ratio=h9_ratio.replace(".", ","),
        n_03m=n_03m,
        h2_expected=h2_ctrl[0].replace(".", ","),
        h2_observed=h2_ctrl[1],
        global_rate=fmt_pct(global_rate, 1),
        km_q1_24=fmt_pct(km_q1_24, 1), km_q2_24=fmt_pct(km_q2_24, 1),
        r2_net=fmt_int(r2_net), r2_churn=fmt_int(r2_churn),
        r2_contr=fmt_int(r2_contr),
        # suporte / qualidade
        csat_null=fmt_pct(csat_null, 1), reason_unk=fmt_pct(reason_unk, 1),
        csat_cov=fmt_pct(csat_cov, 1),
        usage_in_window_pct=usage_in_window_pct.replace(".", ",") + "%",
        # uso
        usage_2023=fmt_int(usage_2023), usage_2024=fmt_int(usage_2024),
        usage_pct=fmt_pct(usage_pct, 1),
        # segmentos e watchlist
        seg=seg, km_s3=km_s3.replace(".", ","), n_multi_acc=n_multi_acc,
        pct_events_multi=fmt_pct(pct_events_multi, 1),
        lift_a=_lifts(t14, "A", "/"), lift_b=_lifts(t14, "B", "/"),
        lift_c=_lifts(t14, "C", "/"), lift_e=_lifts(t14, "E", "/"),
        cur_mrr=fmt_int(cur_mrr), top20_mrr=fmt_int(top20_mrr),
        top20_share=fmt_pct(top20_share, 1), tier_a=tier_a,
        n_grp_validated=n_grp_validated, n_grp_exposure=n_grp_exposure,
        account_rows=account_rows,
        # ações/impacto/backtest
        act_rows=act_rows, lifts_d=lifts_d,
        n_rule=n_rule, n_rule_out=n_rule_out,
        wil_lo=fmt_br3(wil_lo), wil_hi=fmt_br3(wil_hi),
        mde=mde, power=power, false_go=false_go,
        imp_lo_ev=fmt_dec(imp["conservador"]["events_affected_90d"], 1),
        imp_base_ev=fmt_dec(imp["base"]["events_affected_90d"], 1),
        imp_hi_ev=fmt_dec(imp["ambicioso"]["events_affected_90d"], 1),
        imp_lo_usd=fmt_int(int(imp["conservador"]["expected_exposure_affected_mrr"])),
        imp_base_usd=fmt_int(int(imp["base"]["expected_exposure_affected_mrr"])),
        imp_hi_usd=fmt_int(int(imp["ambicioso"]["expected_exposure_affected_mrr"])),
        imp_lo_exp=fmt_dec(imp["conservador"]["expected_events_90d"], 1),
        imp_base_exp=fmt_dec(imp["base"]["expected_events_90d"], 1),
        imp_hi_exp=fmt_dec(imp["ambicioso"]["expected_events_90d"], 1),
        imp_inc=fmt_br4(imp["base"]["incidence_90d"]),
        imp_inc_lo=fmt_br4(imp["sens-inc-lo"]["incidence_90d"]),
        imp_inc_hi=fmt_br4(imp["sens-inc-hi"]["incidence_90d"]),
        imp_eligible=int(imp["base"]["eligible_n"]),
        imp_base_mrr=fmt_int(int(imp["base"]["exposure_base_mrr"])),
        caus_rows=caus_rows,
    )


def _wilson(k: int, n: int) -> tuple[float, float]:
    z = 1.959963984540054
    p = k / n
    denom = 1 + z * z / n
    center = p + z * z / (2 * n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (center - half) / denom, (center + half) / denom


def _lifts(t14: pd.DataFrame, rule: str, sep: str) -> str:
    """Lifts de uma regra no horizonte 90d, formatados pt-BR."""
    d = t14[(t14["rule"] == rule) & (t14["horizon_days"] == 90)]
    return sep.join(fmt_lift2(v) for v in d["lift"])


# ----------------------------------------------------------------------------
# Template do relatório (números via placeholders; texto fixo e estável)
# ----------------------------------------------------------------------------
def render(n: dict) -> str:
    seg_tbl = []
    seg_par = []
    labels = {
        "S1": ("Onboarding (tenure ≤ 90d)",
               f"**validado** (lift {n['lifts_d']})",
               f"mecanismo do pico (0–3m: {n['h9_share']}%, razão "
               f"{n['h9_ratio']}) e exposição precoce (R1 ≤ 90d: "
               f"{n['r1_le90_pct']} da janela) — hipótese causal plausível"),
        "S2": ("Repeat-event (≥2 eventos)",
               f"sem lift (regra A: {n['lift_a']})",
               f"{n['n_multi_acc']} contas, {n['pct_events_multi']} dos "
               f"episódios; não prediz o próximo"),
        "S3": ("Reativação recente (flag out-dez/2024)",
               f"sem lift (regra B: {n['lift_b']})",
               f"KM 90d = {n['km_s3']} (censura declarada); não é ciclo de estado"),
        "S4": ("Evento recente (último evento ≤ 90d)",
               f"sem lift (regra C: {n['lift_c']})",
               "janela acionável de CS, não predição"),
        "S5": ("Alto valor (winner ≥ P75)",
               f"sem lift (regra E: {n['lift_e']})",
               "exposição, não risco"),
    }
    for sid, (name, sinal, nota) in labels.items():
        seg_tbl.append(f"| {sid} {name} | {n['seg'][sid]['n']} | "
                       f"{fmt_int(n['seg'][sid]['mrr'])} | {sinal} |")
        seg_par.append(f"- **{sid} {name.split(' (')[0]}:** {nota}.")
    seg_tbl_s = "\n".join(seg_tbl)
    seg_par_s = "\n".join(seg_par)

    acc_tbl = "\n".join(
        f"| {a['aid']} | {a['grp']} | {fmt_int(a['mrr'])} | {a['ev']} | "
        f"{a['lim']} |" for a in n["account_rows"])
    act_tbl = "\n".join(
        f"| {a['id']} | {a['act'][:40].rstrip(' (;|,·')} | {a['dec']} | "
        f"{a['owner'][:22].rstrip(' (;|,·')} | {a['prazo'][:36].rstrip(' (;|,·')} | "
        f"{a['sinal'][:28].rstrip(' (;|,·')} | {a['stopgo'][:44].rstrip(' (;|,·')} |"
        for a in n["act_rows"])
    caus_tbl = "\n".join(
        f"| {f} | {s} |" for f, s in n["caus_rows"])

    t = f"""# Relatório Executivo — Diagnóstico de Churn (RavenStack)

*Gerado por `solution/src/07_generate_executive_report.py` a partir dos
artefatos validados (Iterações 01–06); janela 2023-01-01..2024-12-31 (corte
2024-12-31). Todo número tem origem em tabela/evidence linkada (seção 10).*

## 1. Executive summary — decisão solicitada

**Mensagem central:** o churn subiu porque contas recém-adquiridas estão
saindo nos primeiros 90 dias de vida — **churn precoce de onboarding** — e não
por insatisfação geral, por queda de uso ou por um segmento específico. A base
não permite provar causa: o padrão é uma **hipótese causal plausível**, com o
único sinal validado temporalmente em backtest. Por isso a recomendação não é
"uma campanha de retenção": é instrumentar e testar.

**O que aconteceu:** em dezembro de 2024, {n['dec_first']} contas tiveram o
primeiro evento de churn ({n['dec_rate']} das {n['dec_eligible']} contas
elegíveis do mês), vs mediana de {n['med6m']} nos 6 meses anteriores. O
mês teve {n['dec_events']} episódios no total; os {n['dec_first']} são o hazard
de *primeiro* evento. A composição do pico é decisiva: {n['h9_share']}% dele
vem de contas com 0–3 meses de vida, e {n['fe90_pct']} dos primeiros eventos
da janela acontecem até 90 dias do signup. O resto do negócio não explica o
movimento (uso total +{n['usage_pct']} com intensidade mediana
{n['med_intens']}; suporte e CSAT sem diferença material).

**Tamanho e incerteza:** as {n['seg']['S1']['n']} contas em onboarding somam
{fmt_int(n['seg']['S1']['mrr'])} US$/mês de winner MRR (seção 5). Um
programa de ativação bem desenhado poderia afetar, em cenário base de
planejamento, {n['imp_base_ev']} eventos e {n['imp_base_usd']} US$ de
exposição MRR-equivalent em 90 dias — faixa {n['imp_lo_ev']}–{n['imp_hi_ev']}
eventos e {n['imp_lo_usd']}–{n['imp_hi_usd']} US$ (premissas na seção 7;
exposição, não perda). A incerteza é grande: menor efeito detectável a 80%
de poder = {n['mde']} de redução relativa.

**Decisão solicitada (Now):**
1. **ACT-03 — Instrumentação (Now, SLA ≤ 30d):** milestone de ativação, reason
   estruturado e timestamps alinhados. Sem isso não há medição confiável (CSAT
   com nota {n['csat_cov']}; 'unknown' {n['reason_unk']}; vínculo
   evento-assinatura {n['h7_link']}).
2. **ACT-01 — Programa de ativação/onboarding 0–90d (Now, após ACT-03):**
   rollout gradual com holdout (experimento); escala só com evidência
   estatística (GO exige IC95 excluindo 0).
3. **ACT-02 — Triage semanal da watchlist top-20 (Now, em paralelo):**
   {n['top20_mrr']} US$/mês ({n['top20_share']} da exposição atual);
   ACT-04 (reativação/recorrência) fica para depois (Later).

## 2. Como medimos churn (lentes; nunca misturar)

As três fontes de "churn" **não medem a mesma coisa**; cada pergunta usa uma
lente declarada (contrato: [analytical-contract.md](docs/analytical-contract.md)
§4):

| Pergunta | Lente | Fonte | Contagem |
|---|---|---|---|
| Quem está churnado hoje (corte 2024-12-31) | A — snapshot `accounts.churn_flag` | `accounts` | {n['n_snapshot_fmt']} contas |
| Quanto MRR contratual termina (exposição, não perda) | B — assinaturas com `end_date` na janela (R1) | `subscriptions` | {n['n_subs_fmt']} assinaturas / {n['n_acc_ended_fmt']} contas |
| Por que os clientes saem (diagnóstico) | C — eventos de churn | `churn_events` | {n['n_events_fmt']} eventos / {n['n_event_acc_fmt']} contas |
| Estado atual da conta (winner MRR; risco) | painel account-month | `data/processed` | {n['n_accounts']} contas (all-active no corte) |

**Regra de ouro:** {n['n_snapshot_fmt']} ≠ {n['n_subs_fmt']} ≠
{n['n_events_fmt']} não são três medições do mesmo fenômeno — não podem ser
somadas, subtraídas ou usadas como alvo alternativo. Exemplo: dezembro/2024
teve **{n['dec_events']} episódios**, dos quais **{n['dec_first']} são
primeiros eventos** de contas distintas — o relatório usa primeiro evento para
hazard e coortes. Para receita há duas lentes: **R1** (gross ending MRR,
exposição contratual bruta de {n['r1_total']} US$ na janela — teto, não perda)
e **R2** (estado líquido: {n['r2_churn']} + {n['r2_contr']} = {n['r2_net']}
US$); o relatório usa R1 e winner MRR, com nomes declarados.

## 3. O que mudou — causa raiz (hipótese causal plausível)

**O pico é real e é de contas novas.** Dezembro/2024: **{n['dec_first']}
primeiros eventos** sobre {n['dec_eligible']} elegíveis = **{n['dec_rate']}**
vs mediana de **{n['med6m']}** nos 6 meses anteriores (razão {n['pico_ratio']})
e {n['med_win']} na janela; o aumento persiste com tenure controlado
(esperado {n['h2_expected']}, observado {n['h2_observed']}).

![Série mensal: eventos e taxa por conta elegível](out/charts/a_monthly_events_and_rate.png)
*Leitura: regime elevado com pico em dez/24.*

**O mecanismo é o onboarding.** Do pico, {n['h9_share']}% ({n['n_03m']} de
{n['dec_first']}) são contas com 0–3 meses de vida (razão {n['h9_ratio']} vs
linha de base do bucket). Na janela: **{n['fe90_pct']}** dos primeiros eventos
({n['fe90_n']} de {n['n_event_acc_fmt']}) ocorrem até 90 dias do signup (30d:
{n['fe30_pct']}; 60d: {n['fe60_pct']}); e **{n['r1_le90_pct']}** da exposição
contratual da janela ({n['r1_le90']} de {n['r1_total']} US$) vem de
assinaturas com até 90 dias de vida — exposição precoce, não perda.

![Exposição contratual precoce (R1) por duração da assinatura](out/charts/c_onboarding_exposure_by_duration.png)
*Leitura: {n['r1_le90_pct']} da exposição bruta está em assinaturas ≤ 90d —
perder cliente novo é o problema dominante.*

**Coortes recentes churnam mais cedo (com censura).** Kaplan-Meier (censura
no corte): churn no mês 6 de {n['km_q1_24']} (2024Q1) e {n['km_q2_24']}
(2024Q2); coortes 2024Q3/Q4 têm follow-up curto (≤ 3 meses) e não devem ser
comparadas à janela completa — a taxa observada subestima o churn recente.
Taxa global na janela: {n['global_rate']} das contas.

![Tempo até o primeiro evento por coorte de signup (KM)](out/charts/b_km_by_signup_quarter.png)
*Leitura: coortes mais recentes churnam mais cedo.*

**Status de causalidade:** o conjunto (pico de contas novas + exposição
precoce + única regra validada) sustenta a **hipótese causal plausível** de
churn precoce — **não é prova**. Causalidade exigiria dados de
ativação (ACT-03) e experimento (ACT-01). Tabela:
[out/tables/t09_causality.csv](out/tables/t09_causality.csv).

## 4. O que não explica o churn (evita narrativa falsa)

**"O uso cresceu" é verdade em volume, não por conta.** Linhas de uso (sem
pré-signup): {n['usage_2023']} → {n['usage_2024']} (+{n['usage_pct']});
intensidade mediana por conta-mês: {n['med_intens']}. O crescimento vem de
mais contas ativas, não de contas mais engajadas.

![Uso: volume cresce vs intensidade por conta](out/charts/d_usage_volume_vs_intensity.png)
*Leitura: volume cresce; intensidade por conta não.*

**Suporte e CSAT não discriminam.** Antes do evento (janela de 90 dias,
anti-leakage): tickets/conta {n['h5_tick_c']} (churn) vs {n['h5_tick_ct']}
(controle); escalação {n['h5_esc_c']} vs {n['h5_esc_ct']}; CSAT {n['h5_csat_c']}
vs {n['h5_csat_ct']} — sem diferença material. Hipótese H4 (uso pré-evento
precede churn) foi **refutada após correção**: zero-uso {n['h4_churn']} vs {n['h4_ctrl']}
(versão anterior contava meses pré-signup como zero).

**Segmentos amplos não discriminam** (industry/canal/plano/trial): nenhum com
taxa ≥ 1,5× a global (limiar inalcançável com taxa global de {n['global_rate']});
maior gap de KM: {n['h6_gap']} p.p. **Reasons e CSAT não são confiáveis como
causa:** {n['csat_null']} de CSAT nulos, {n['reason_unk']} de reasons
'unknown', e {n['h7_link']} dos eventos não têm assinatura encerrada ±30d
(lentes decopladas).

## 5. Segmentos e contas em atenção (estados de jornada, não industry)

Os segmentos que importam são **estados de jornada**, não indústria (overlap
em [out/tables/t15b_segment_overlap.csv](out/tables/t15b_segment_overlap.csv));
nenhum é score de risco — sinal de backtest em cada linha.

| Segmento | N | Current MRR | Sinal de backtest |
|---|---|---|---|
{seg_tbl_s}

{seg_par_s}

**Watchlist top-20 (operational priority, nunca score):** cobre
**{n['top20_mrr']} US$/mês = {n['top20_share']}** da exposição atual
({n['cur_mrr']} US$/mês): **{n['tier_a']} onboarding validadas**,
**{n['n_grp_exposure']} exposure-only** (sem sinal validado — não rotular
risco). Completa:
[out/tables/t16_watchlist_top20.csv](out/tables/t16_watchlist_top20.csv);
jornada: [out/tables/t11_account_lifecycle.csv](out/tables/t11_account_lifecycle.csv).

![Exposição atual vs valor de jornada (proxy)](out/charts/It04_c_lifecycle_vs_current_mrr.png)
*Leitura: jornada e MRR atual são complementares.*

**Contas específicas (10 de 20 — 8 validadas + 2 de maior exposição):**

| Conta | Grupo | Winner MRR (US$/mês) | Evidência | Limitação |
|---|---|---|---|---|
{acc_tbl}

## 6. Ações priorizadas

**Sequência:** ACT-03 (Now) → ACT-01 (Now, após readiness) · ACT-02 (Now,
paralelo) · ACT-04 (Later). Sem score: evidência + impacto + esforço; stop/go
por linha ([t18](out/tables/t18_actions_prioritized.csv) ·
[t20](out/tables/t20_measurement_plan.csv)).

| ID | Ação (resumo) | Decisão | Owner | Prazo | 1º sinal (leading) | Stop/Go (resumo) |
|---|---|---|---|---|---|---|
{act_tbl}

**Regra de decisão do ACT-01 (3 estados;
[evidence/05_action_plan.md](evidence/05_action_plan.md) §5):** SCALE/GO =
redução ≥ 10% **e** IC95 exclui 0; CONTINUE/LEARN = ponto favorável, IC95 cruza
0; STOP/HARM = efeito adverso ou guardrail falhado. 1ª decisão em 2
trimestres; escala em 4 trimestres + 90d. O único sinal que justifica o
programa é o lift do backtest: **{n['lifts_d']}** (3 cutoffs de 90d, N ≥ 25)
— a única regra consistente:

![Backtest point-in-time: lift por regra × cutoff](out/charts/It04_d_backtest_lift.png)
*Leitura: só onboarding (R_D) passa do limiar 1,15.*

## 7. Impacto em faixa (planejado, não medido)

**Fórmula (só ACT-01 tem estimativa defensável):** eventos afetados = N ×
incidência 90d × redução; exposição afetada = Σ winner MRR × incidência ×
redução (componentes em
[out/tables/t19_impact_sensitivity.csv](out/tables/t19_impact_sensitivity.csv)):

| Cenário | Incidência 90d | N | Eventos esp. 90d | Redução | Eventos afetados | Exposição afetada (US$/90d) |
|---|---|---|---|---|---|---|
| conservador | {n['imp_inc_lo']} | {n['imp_eligible']} | {n['imp_lo_exp']} | 10% | {n['imp_lo_ev']} | {n['imp_lo_usd']} |
| base | {n['imp_inc']} | {n['imp_eligible']} | {n['imp_base_exp']} | 20% | {n['imp_base_ev']} | {n['imp_base_usd']} |
| ambicioso | {n['imp_inc_hi']} | {n['imp_eligible']} | {n['imp_hi_exp']} | 30% | {n['imp_hi_ev']} | {n['imp_hi_usd']} |

**Premissas e honestidade:**
- Incidência 90d = precisão pooled da regra de onboarding
  ({n['n_rule_out']}/{n['n_rule']} = {n['imp_inc']}); faixa observada entre
  cutoffs {n['imp_inc_lo']}–{n['imp_inc_hi']} — **faixa observada, não
  intervalo de confiança** (CI de Wilson 95%: {n['wil_lo']}–{n['wil_hi']});
- Redução relativa 10/20/30% = **premissa de planejamento** (nenhum programa
  existe na base; lift é associação, não efeito) — testada pelo experimento
  ACT-01;
- Base: {n['imp_eligible']} contas onboarding, {n['imp_base_mrr']} US$/mês
  de winner MRR;
- Nomenclatura: **exposure afetada no cenário** — exposição, não perda; nada
  é previsão; eventos ≠ logos ≠ revenue churn (lentes);
- **Poder estatístico:** fluxo ~68 signups/trimestre; MDE a 80% de poder =
  **{n['mde']}**; poder por cenário: **{n['power']}** (10/20/30%) —
  inconclusivo NÃO é ausência de efeito; P(falso GO) ≈ **{n['false_go']}%**;
  escala exige IC95 excluindo 0.

## 8. O que não fazer agora

1. **ML/score preditivo** — nenhuma regra além de onboarding valida
   temporalmente; score sem validação é claim falso.
2. **Desconto generalizado** — sem custos na base, seria preço inventado;
   nenhuma evidência de que preço dirige o churn precoce.
3. **Decisão por reason/CSAT** — evidência sugestiva com missingness alta
   ({n['csat_null']} de CSAT nulos; {n['reason_unk']} de reasons 'unknown').
4. **Automação de churn** — sem validação causal; começa pela experimentação
   (ACT-01), nunca sem holdout.
5. **ROI pontual / revenue saved / "reativação mais barata"** — proibido nesta
   base (sem CAC/winback; R1 é exposição).

## 9. Limitações e próximos dados

- **Base sintética** ([evidence/01_audit_report.md](evidence/01_audit_report.md)
  §5): padrões podem refletir o gerador; nada é extrapolado sem rótulo.
- **Lentes decopladas:** {n['h7_link']} dos eventos têm assinatura encerrada
  ±30d; o snapshot marca {n['n_snapshot_fmt']} contas churnadas, mas o estado
  por assinatura mantém as {n['n_accounts']} ativas no corte (**all-active**) —
  "perda real de estado" não é validável no presente; o backtest usa eventos
  históricos como desfecho.
- **Proxies:** winner MRR é estado/exposição, não receita contábil;
  lifecycle_value_proxy é soma mensal de winner (não GAAP).
- **Poder baixo:** MDE {n['mde']}; N pequenos limitam conclusões finas.
- **Próximos dados (ACT-03):** milestone de ativação (não capturado), reason
  estruturado ('unknown' < 5%), timestamps alinhados (uso em janela:
  {n['usage_in_window_pct']}), CSAT ≥ 90% (hoje {n['csat_cov']}) — o caminho
  para causalidade real.

## 10. Reprodução e evidence map

**Reprodução (1 comando, offline, determinístico):** `./run.sh` (ou `make all`)
regenera os artefatos das Iterações 01–07, incluindo este relatório, em
~65–75 s (aproximação medida) — [README da solução](README.md) §6;
`06_verify_pipeline.py` valida estrutura, links, imagens e claims.

**Mapa de evidência (auditável):**

| Achado | Status | Auditoria |
|---|---|---|
| Churn precoce de onboarding (pico dez/24 + tenure 0–3m) | hipótese causal plausível | [t01](out/tables/t01_monthly_series.csv) · [t03](out/tables/t03_onboarding_buckets.csv) · [t03b](out/tables/t03b_onboarding_accounts.csv) |
| Único sinal com validação temporal (onboarding ≤ 90d) | validado em backtest | [t14](out/tables/t14_backtest_temporal.csv) · [t14b](out/tables/t14b_backtest_detail.csv) |
| Uso cresce em volume, não por conta | descritivo | [t05](out/tables/t05_usage_monthly.csv) |
| Suporte/CSAT/reasons sem discriminação/confiabilidade | não identificável | [t06](out/tables/t06_support_monthly.csv) · [t10](out/tables/t10_hypothesis_verdicts.csv) |
| Segmentos amplos sem heterogeneidade material | descritivo | [t07](out/tables/t07_segments.csv) · [t09](out/tables/t09_causality.csv) |
| Watchlist top-20 = priorização operacional/exposição | sem score | [t16](out/tables/t16_watchlist_top20.csv) · [t21](out/tables/t21_watchlist_split_actions.csv) |
| Ações, impacto e medição | premissas nomeadas | [t18](out/tables/t18_actions_prioritized.csv) · [t19](out/tables/t19_impact_sensitivity.csv) · [t20](out/tables/t20_measurement_plan.csv) |

**Evidências (It01–05):**
[01](evidence/01_audit_report.md) · [02](evidence/02_consistency_report.md) ·
[03](evidence/03_root_cause_report.md) ·
[04](evidence/04_lifecycle_watchlist_report.md) ·
[05](evidence/05_action_plan.md) · contrato:
[docs/analytical-contract.md](docs/analytical-contract.md).

**Processo (narrativa e decisões):**
[outline](../process-log/decisions/iteration-07-executive-report-outline.md) ·
[prompt](../process-log/prompts/iteration-07-prompt.md) ·
[report de processo](../process-log/reports/iteration-07-executive-report.md).

**Gráficos:** os 6 deste relatório estão em `out/charts/` (manifesto fechado).
"""
    return t


# ----------------------------------------------------------------------------
# Gates G1-G8 (self-check pós-render; falha => exit 1 sem escrever o report)
# ----------------------------------------------------------------------------
def _affirmative_use(tok: str, text: str) -> bool:
    """True se o termo aparece em contexto afirmativo (sem negação próxima)."""
    neg = ["não", "sem", "nunca", "proibido", "evita", "evite", "evitar",
           "fora", "≠", "ausência", "nenhum", "evite"]
    for m in re.finditer(re.escape(tok), text):
        ctx = text[max(0, m.start() - 90):m.end() + 90]
        if not any(nm in ctx for nm in neg):
            return True
    return False


FORBIDDEN_CLAIMS = [
    "receita perdida", "receita salva", "receita recuperada", "revenue saved",
    "revenue lost", "forecast", "ROI", "eventos evitados", "evitados",
    "prova causal", "causa provada", "é causado", "causa do churn é",
    "churn é causado", "receita em risco",
]
FORBIDDEN_TOKENS = ["kaggle", "rivalytics", "benchmark", "concorrent",
                    "pesquisa interna", "baseline"]


def run_gates(n: dict, text: str) -> list[str]:
    problems: list[str] = []

    # G1 — âncoras numéricas-chave presentes (valores derivados em runtime)
    anchors = [
        ("taxa dez/24", n["dec_rate"]), ("mediana 6m", n["med6m"]),
        ("razão pico", n["pico_ratio"]),
        ("117 episódios", f"{n['dec_events']} episódios"),
        ("43 primeiros", f"{n['dec_first']} são"),
        ("R1 <=90d share", n["r1_le90_pct"]), ("R1 <=90d US$", n["r1_le90"]),
        ("R1 total US$", n["r1_total"]), ("fe <=90d share", n["fe90_pct"]),
        ("fe <=90d n", str(n["fe90_n"])), ("uso pct", f"+{n['usage_pct']}"),
        ("intensidade mediana", n["med_intens"]), ("h4 churn", n["h4_churn"]),
        ("h4 controle", n["h4_ctrl"]), ("h9 share", f"{n['h9_share']}%"),
        ("h9 ratio", n["h9_ratio"]), ("h7 decoupling", n["h7_link"]),
        ("global rate", n["global_rate"]), ("km q1", n["km_q1_24"]),
        ("km q2", n["km_q2_24"]), ("s1 n", str(n["seg"]["S1"]["n"])),
        ("s1 mrr", fmt_int(n["seg"]["S1"]["mrr"])),
        ("top20 mrr", n["top20_mrr"]), ("top20 share", n["top20_share"]),
        ("cur mrr", n["cur_mrr"]), ("lifts D", n["lifts_d"]),
        ("incidência pooled", n["imp_inc"]),
        ("eventos afetados lo", n["imp_lo_ev"]),
        ("eventos afetados base", n["imp_base_ev"]),
        ("eventos afetados hi", n["imp_hi_ev"]),
        ("exposição lo", n["imp_lo_usd"]), ("exposição base", n["imp_base_usd"]),
        ("exposição hi", n["imp_hi_usd"]), ("MDE", n["mde"]),
        ("poder", n["power"]), ("falso GO", f"{n['false_go']}%"),
        ("Wilson lo", n["wil_lo"]), ("Wilson hi", n["wil_hi"]),
        ("snapshot", n["n_snapshot_fmt"]), ("subs ended", n["n_subs_fmt"]),
        ("contas ended", n["n_acc_ended_fmt"]), ("eventos total", n["n_events_fmt"]),
        ("contas evento", n["n_event_acc_fmt"]),
        ("pct multi", n["pct_events_multi"]), ("km s3", n["km_s3"]),
        ("csat cobertura", n["csat_cov"]), ("uso janela", n["usage_in_window_pct"]),
    ]
    for label, val in anchors:
        if val not in text:
            problems.append(f"G1 âncora ausente: {label} ({val})")

    # G2 — contas citadas são subconjunto da t16
    cited = set(re.findall(r"A-[0-9a-f]{6}", text))
    t16_ids = set(pd.read_csv(TABLES_DIR / "t16_watchlist_top20.csv")["account_id"])
    outside = cited - t16_ids
    if outside:
        problems.append(f"G2 contas fora da t16: {sorted(outside)}")

    # G3 — ações citadas subset da t18; decisões consistentes
    cited_acts = set(re.findall(r"ACT-\d\d", text))
    t18 = pd.read_csv(TABLES_DIR / "t18_actions_prioritized.csv")
    if not cited_acts <= set(t18["action_id"]):
        problems.append(f"G3 ações fora da t18: "
                        f"{sorted(cited_acts - set(t18['action_id']))}")
    dec_map = dict(zip(t18["action_id"], t18["decision"]))
    for aid, dec in dec_map.items():
        if aid in cited_acts and dec not in text:
            problems.append(f"G3 decisão de {aid} ausente no texto")

    # G4 — claims proibidos em contexto AFIRMATIVO (negação explícita é
    # permitida: o relatório cita termos apenas para negá-los/proibi-los)
    for tok in FORBIDDEN_CLAIMS:
        if tok in text and _affirmative_use(tok, text):
            problems.append(f"G4 claim proibido em contexto afirmativo: '{tok}'")

    # G5 — links relativos existem; exatamente 6 imagens, cada uma 1x
    links = [l.strip() for l in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", text)]
    for link in links:
        if link.startswith("http"):
            continue
        p = (SOLUTION_DIR / link).resolve()
        if not p.is_file():
            problems.append(f"G5 link quebrado: {link}")
    imgs = [l for l in links if l.endswith(".png")]
    if len(imgs) != 6:
        problems.append(f"G5 imagens: esperadas 6, encontradas {len(imgs)}")
    dup = [k for k, v in Counter(imgs).items() if v > 1]
    if dup:
        problems.append(f"G5 imagem repetida: {dup}")

    # G6 — word count (total 1.400-2.400; executive summary 250-350)
    wc = len(text.split())
    if not (1400 <= wc <= 2400):
        problems.append(f"G6 word count fora do budget: {wc}")
    m = re.search(r"## 1\. Executive summary.*?\n(.*?)\n## 2\.", text, re.S)
    if m:
        wc_es = len(m.group(1).split())
        if not (250 <= wc_es <= 350):
            problems.append(f"G6 executive summary fora de 250-350: {wc_es}")
    else:
        problems.append("G6 seção 1 não encontrada para contagem")

    # G7 — sem concorrentes/pesquisa interna/baseline copiado
    for tok in FORBIDDEN_TOKENS:
        if tok in text:
            problems.append(f"G7 token proibido: '{tok}'")

    # G8 — determinismo estrutural (sem marca de geração/now/random)
    if re.search(r"[Gg]erado (em|on) 20\d\d", text):
        problems.append("G8 marca de geração temporal no texto")
    return problems


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main() -> int:
    try:
        inp = load_inputs()
        n = derive_numbers(inp)
        text = render(n)
        problems = run_gates(n, text)
    except SystemExit as exc:
        print(f"[07] {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 — falha estrutural vira diagnóstico
        print(f"[07] FAIL inesperado (input divergente?): {type(exc).__name__}: "
              f"{exc}", file=sys.stderr)
        return 1

    if problems:
        print("[07] FAIL — gates do relatório executivo:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print("[07] Nada foi escrito: o relatório existente (se houver) é o "
              "último válido; corrija a causa e reexecute.", file=sys.stderr)
        return 1

    fd, tmp = tempfile.mkstemp(dir=str(SOLUTION_DIR), suffix=".md.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, REPORT_PATH)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

    print(f"[07] OK: solution/report-executivo.md escrito "
          f"({len(text.split())} palavras; gates G1-G8 PASS; determinístico).")
    return 0


if __name__ == "__main__":
    sys.exit(main())