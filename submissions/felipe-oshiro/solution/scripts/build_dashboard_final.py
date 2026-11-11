"""Builds the FINAL self-contained executive dashboard (step e):

solution/dashboard/dashboard_g4.html — vertical-scroll storytelling in 6
sections (hero, diagnosis, classifier, routing, non-automation, decisions),
G4 brand (PPMuseum embedded, navy/gold palette), every figure and font
embedded as base64 data-URI, zero external dependencies.

All numbers come from files read at build time:
- docs/relatorio_fluxo_atendimento.md (diagnosis)
- solution/artifacts/{router_threshold.json, step1_results.json, per_class_metrics.csv}
- solution/artifacts/transformer/{step2_results.json, classification_report.txt}
- solution/artifacts/routed_tickets.csv (derived batch impact — pandas)

Run with: solution/.venv/bin/python solution/scripts/build_dashboard_final.py
"""
import base64
import csv
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent  # solution/
SUB = ROOT.parent                                # submission root
BRAND = ROOT / "brand"
ART = ROOT / "artifacts"
TRANS = ART / "transformer"
ANALYSIS = SUB / "analysis"
OUT = ROOT / "dashboard" / "dashboard_g4.html"
TEMPLATE = ROOT / "dashboard" / "dashboard_final_template.html"


def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


# ---------------------------------------------------------------- inputs ----
step1 = json.loads((ART / "step1_results.json").read_text())["results"]
step2 = json.loads((TRANS / "step2_results.json").read_text())
router = json.loads((ART / "router_threshold.json").read_text())

per_class = list(csv.DictReader((ART / "per_class_metrics.csv").open()))
# classic champion per-class report (transformer one is authoritative for step 2)
trans_report = (TRANS / "classification_report.txt").read_text()
def report_row(cls: str) -> dict:
    line = [l for l in trans_report.splitlines() if l.strip().startswith(cls)][0]
    p, r, f1, s = line.split()[-4:]
    return {"precision": float(p), "recall": float(r), "f1": float(f1), "support": int(s)}

worst = sorted(("Administrative rights", "Miscellaneous", "Internal Project", "Hardware"),
               key=lambda c: report_row(c)["f1"])
worst_rows = [
    {
        "name": c,
        "precision": report_row(c)["precision"],
        "recall": report_row(c)["recall"],
        "f1": report_row(c)["f1"],
        "support": report_row(c)["support"],
    }
    for c in worst
]

# holdout majority baseline (largest class share of the 9,568-ticket holdout)
largest_support = max(int(r["support"]) for r in per_class)
holdout_n = sum(int(r["support"]) for r in per_class)
majority_pct = 100 * largest_support / holdout_n
assert 28.0 < majority_pct < 29.0, majority_pct

# ------------------------------------------------- routed batch (derived) ----
routed = pd.read_csv(ART / "routed_tickets.csv")
n_routed = len(routed)
auto = int((routed["decision"] == "AUTO").sum())
humano = n_routed - auto
reasons = routed["reason"].value_counts()
by_topic = (
    routed.groupby("predicted_topic")
    .agg(n=("decision", "size"), auto_pct=("decision", lambda s: 100 * (s == "AUTO").mean()))
    .sort_values("n", ascending=False)
)
conf_median = float(routed["confidence"].median())

derived = {
    "n": n_routed,
    "auto": auto, "auto_pct": 100 * auto / n_routed,
    "humano": humano, "humano_pct": 100 * humano / n_routed,
    "low_conf": int(reasons["low_confidence"]), "low_conf_pct": 100 * reasons["low_confidence"] / n_routed,
    "sens": int(reasons["sensitive_class"]), "sens_pct": 100 * reasons["sensitive_class"] / n_routed,
    "ok": int(reasons["ok"]),
    "topics": [
        {"name": t, "n": int(r.n), "n_pct": 100 * r.n / n_routed, "auto_pct": r.auto_pct}
        for t, r in by_topic.iterrows()
    ],
    "conf_median": conf_median,
}
# sanity — the honesty note hinges on these
assert router["coverage"] * 100 > derived["auto_pct"] + 50  # 80.7% >> 21.5%
assert derived["auto"] == int(reasons["ok"])


def br(x: float, dec: int = 1) -> str:
    return f"{x:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(x: float, dec: int = 1) -> str:
    return br(x, dec) + "%"


# ------------------------------------------------------------ HTML assets ----
logo_white = (BRAND / "logo-g4-completa-branca.svg").read_text().strip()
logo_white = logo_white.replace("<svg ", '<svg role="img" aria-label="G4 Educação" ', 1)
logo_dark = (BRAND / "logo-g4-completa-escura.svg").read_text().strip()
logo_dark = logo_dark.replace("<svg ", '<svg role="img" aria-label="G4 Educação" ', 1)

# dark logo is optional: used only if the template places the brand on a light surface
replacements = {
    "__LOGO_DARK__": logo_dark,
    "__FONT_REGULAR__": b64(BRAND / "PPMuseum-Regular.ttf"),
    "__FONT_ULTRABOLD__": b64(BRAND / "PPMuseum-Ultrabold.ttf"),
    "__FAVICON__": b64(BRAND / "icone-azul-270.png"),
    "__LOGO_WHITE__": logo_white,
    "__IMG_FUNIL__": b64(ANALYSIS / "funil_fluxo.png"),
    "__IMG_CSAT__": b64(ANALYSIS / "csat_sorteio.png"),
    "__IMG_CENARIOS__": b64(ANALYSIS / "cenarios_desperdicio.png"),
    "__IMG_CONFUSION__": b64(TRANS / "confusion_matrix.png"),
    "__IMG_PRECISION__": b64(TRANS / "precision_coverage.png"),
    # numbers
    "__MAJORITY_PCT__": pct(majority_pct),
    "__TFIDF_ACC__": pct(100 * step1["tfidf_word12_logreg"]["accuracy"], 1),
    "__TFIDF_ACC2__": pct(100 * step1["tfidf_word12_logreg"]["accuracy"], 2),
    "__TRANS_ACC__": pct(100 * step2["test_accuracy"], 1),
    "__TRANS_MACROF1__": pct(100 * step2["macro_f1"], 1),
    "__HOLDOUT_N__": br(holdout_n, 0),
    "__THRESHOLD__": br(router["threshold"], 2),
    "__ROUTER_PRECISION__": pct(100 * router["auto_precision"], 1),
    "__ROUTER_COVERAGE__": pct(100 * router["coverage"], 1),
    # worst classes table
    "__WORST_ROWS__": "".join(
        f'<tr><td>{w["name"]}</td><td class="num">{pct(100 * w["precision"])}</td>'
        f'<td class="num">{pct(100 * w["recall"])}</td>'
        f'<td class="num {"low" if w["name"] == "Administrative rights" else ""}">{pct(100 * w["f1"])}</td>'
        f'<td class="num">{br(w["support"], 0)}</td></tr>'
        for w in worst_rows
    ),
    # routed batch
    "__N_ROUTED__": br(derived["n"], 0),
    "__AUTO_N__": br(derived["auto"], 0),
    "__AUTO_PCT__": pct(derived["auto_pct"]),
    "__HUMANO_N__": br(derived["humano"], 0),
    "__HUMANO_PCT__": pct(derived["humano_pct"]),
    "__LOWCONF_N__": br(derived["low_conf"], 0),
    "__LOWCONF_PCT__": pct(derived["low_conf_pct"]),
    "__SENS_N__": br(derived["sens"], 0),
    "__SENS_PCT__": pct(derived["sens_pct"]),
    "__CONF_MEDIAN__": br(derived["conf_median"], 2),
    "__TOPIC_ROWS__": "".join(
        f'<tr><td>{t["name"]}</td><td class="num">{br(t["n"], 0)}</td>'
        f'<td class="num">{pct(t["n_pct"])}</td>'
        f'<td class="num">{pct(t["auto_pct"])}</td></tr>'
        for t in derived["topics"]
    ),
}

html = TEMPLATE.read_text(encoding="utf-8")
optional = {"__LOGO_DARK__"}
for key, value in replacements.items():
    if key not in html:
        if key in optional:
            continue
        raise SystemExit(f"placeholder {key} not found in template")
    html = html.replace(key, value)
leftover = re.findall(r"__[A-Z_]+__", html)
if leftover:
    raise SystemExit(f"unresolved placeholders: {leftover}")

OUT.write_text(html, encoding="utf-8")
print(f"written: {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")
