#!/usr/bin/env python3
"""Build the seven-page RavenStack executive paper from verified local artifacts."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PDF_PATH = HERE / "RAVENSTACK-THE-CHURN-PARADOX.pdf"
MANIFEST_PATH = HERE / "PAPER-NUMERICAL-EVIDENCE-MANIFEST.md"
SOLUTION = ROOT / "solution"
DATA = SOLUTION / "data/raw"
LEDGER_PATH = SOLUTION / "analysis/daily_portfolio_churn/outputs/g4-alignment/daily-portfolio-churn.json"
BUSINESS_PATH = SOLUTION / "analysis/business_drivers/outputs/g4-alignment/business-investigation.json"
TRANSITION_PATH = SOLUTION / "analysis/transition_audit/outputs/transition-audit.json"

W, H = A4
M = 42
INK = colors.HexColor("#202323")
MUTED = colors.HexColor("#626866")
PAPER = colors.HexColor("#F5F2EA")
WHITE = colors.HexColor("#FFFEFA")
GOLD = colors.HexColor("#C7A45A")
GOLD_DARK = colors.HexColor("#92763D")
GREEN = colors.HexColor("#537A68")
RED = colors.HexColor("#A8574D")
PALE_GOLD = colors.HexColor("#EEE5D2")
PALE_GREEN = colors.HexColor("#E6EEE8")
PALE_RED = colors.HexColor("#F2E5E1")
GRID = colors.HexColor("#D9D6CD")
FONT = "RavenSans"
FONT_BOLD = "RavenSans-Bold"
FONT_SERIF = "RavenSerif"
FONT_SERIF_BOLD = "RavenSerif-Bold"


def register_fonts() -> None:
    root = Path("/usr/share/fonts/truetype/dejavu")
    pdfmetrics.registerFont(TTFont(FONT, str(root / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, str(root / "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFont(TTFont(FONT_SERIF, str(root / "DejaVuSerif.ttf")))
    pdfmetrics.registerFont(TTFont(FONT_SERIF_BOLD, str(root / "DejaVuSerif-Bold.ttf")))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_evidence() -> dict:
    ledger = read_json(LEDGER_PATH)
    business = read_json(BUSINESS_PATH)
    transitions = read_json(TRANSITION_PATH)
    source_names = [
        "ravenstack_accounts.csv", "ravenstack_subscriptions.csv",
        "ravenstack_feature_usage.csv", "ravenstack_support_tickets.csv",
        "ravenstack_churn_events.csv",
    ]
    hashes = {name: sha256(DATA / name) for name in source_names}
    expected = ledger["metadata"]["source_hashes_sha256"]
    if hashes != expected:
        raise SystemExit("Source CSV hashes differ from the daily-ledger evidence; regenerate analyses first.")
    if len(ledger["periods"]["MONTHLY"]) != 24:
        raise SystemExit("Expected exactly 24 monthly rows (2023-01 through 2024-12).")
    if ledger["periods"]["MONTHLY"][0]["period"] != "2023-01" or ledger["periods"]["MONTHLY"][-1]["period"] != "2024-12":
        raise SystemExit("Monthly observation bounds do not match the source ledger.")
    return {"ledger": ledger, "business": business, "transitions": transitions, "hashes": hashes}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if not n:
        return (math.nan, math.nan)
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return mid - half, mid + half


def derived(e: dict) -> dict:
    ledger, business = e["ledger"], e["business"]
    months = ledger["periods"]["MONTHLY"]
    years = {}
    for year in ("2023", "2024"):
        rows = [r for r in months if r["period"].startswith(year)]
        account_exp = sum(r["opening_customers"] for r in rows)
        relation_exp = sum(r["opening_plan_relations"] for r in rows)
        events = sum(r["recorded_event_rows"] for r in rows)
        plan_losses = sum(r["gross_plan_relation_loss_events"] for r in rows)
        account_losses = sum(r["gross_customer_churn_events"] for r in rows)
        years[year] = {
            "account_months": account_exp,
            "relation_months": relation_exp,
            "events": events,
            "event_per_100": events / account_exp * 100 if account_exp else None,
            "plan_losses": plan_losses,
            "plan_per_100": plan_losses / relation_exp * 100 if relation_exp else None,
            "account_losses": account_losses,
            "account_per_100": account_losses / account_exp * 100 if account_exp else None,
        }
    y0, y1 = years["2023"], years["2024"]
    r0, r1 = y0["events"] / y0["account_months"], y1["events"] / y1["account_months"]
    scale = (y1["account_months"] - y0["account_months"]) * (r0 + r1) / 2
    intensity = (r1 - r0) * (y0["account_months"] + y1["account_months"]) / 2
    annual24 = next(r for r in ledger["periods"]["ANNUAL"] if r["period"] == "2024")
    segs = []
    for row in annual24["plan_segments"]:
        k = row["opening_relations_lost_any_time"]
        n = row["opening_relations"]
        lo, hi = wilson(k, n)
        segs.append({**row, "low": lo * 100, "high": hi * 100})
    reasons = Counter()
    event_file = DATA / "ravenstack_churn_events.csv"
    with event_file.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            reasons[row["reason_code"] or "unknown"] += 1
    accounts = [a for a in ledger["account_movement_candidates"] if a["complete_customer_loss_events"] > 0]
    movements = ledger["movements"]
    case_rows = []
    for account in accounts:
        ms = sorted((m for m in movements if m["account_id"] == account["account_id"]), key=lambda x: (x["date"], x["type"]))
        losses = [m for m in ms if m["type"] == "CUSTOMER_CHURN"]
        if not losses:
            continue
        first_loss = losses[0]
        ret = next((m for m in ms if m["type"] == "CUSTOMER_REACTIVATION" and m["date"] > first_loss["date"]), None)
        loss_tier = next((m.get("plan_tier") for m in ms if m["date"] == first_loss["date"] and m["type"] == "PLAN_RELATION_LOSS"), "Multiple/unknown")
        return_tier = None
        if ret:
            return_tier = next((m.get("plan_tier") for m in ms if m["date"] == ret["date"] and m["type"] in {"NEW_PLAN_RELATIONSHIP", "PLAN_RELATION_REACTIVATION"}), None)
        case_rows.append({
            **account, "loss_date": first_loss["date"],
            "return_date": ret["date"] if ret else "UNKNOWN",
            "loss_tier": loss_tier or "Multiple/unknown",
            "return_tier": return_tier or "Coverage restored",
        })
    support = {r["group"]: r for r in business["support"]["by_label"] if r["label"] == "any_event"}
    usage = {str(r["year"]): r for r in business["usage"]["yearly_source_trend"]}
    return {
        "years": years,
        "scale_component": scale,
        "intensity_component": intensity,
        "annual24": annual24,
        "segments": segs,
        "reasons": reasons,
        "cases": sorted(case_rows, key=lambda x: x["loss_date"]),
        "support": support,
        "usage": usage,
        "monthly": months,
    }


def style(size=9, leading=None, color=INK, font=FONT, align=TA_LEFT):
    return ParagraphStyle(
        "p", fontName=font, fontSize=size, leading=leading or size * 1.4,
        textColor=color, alignment=align, spaceAfter=0, spaceBefore=0,
        allowWidows=0, allowOrphans=0,
    )


def para(c, text, x, top, width, size=9, leading=None, color=INK, font=FONT, align=TA_LEFT):
    p = Paragraph(escape(str(text)).replace("\n", "<br/>"), style(size, leading, color, font, align))
    w, h = p.wrap(width, H)
    p.drawOn(c, x, top - h)
    return top - h


def label(c, text, x, y, color=GOLD_DARK, size=7.2):
    c.setFillColor(color)
    c.setFont(FONT_BOLD, size)
    c.drawString(x, y, text.upper())


def begin_page(c, num, section, title, dek="", dark=False):
    bg = INK if dark else PAPER
    fg = WHITE if dark else INK
    c.setFillColor(bg)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    if not dark:
        label(c, "RAVENSTACK  /  THE CHURN PARADOX", M, H - 30, color=INK, size=7)
        label(c, section, W - M - 148, H - 30, color=GOLD_DARK, size=7)
        c.setFillColor(GRID)
        c.rect(M, H - 39, W - 2 * M, 0.6, stroke=0, fill=1)
        y = H - 67
        c.setFillColor(fg)
        c.setFont(FONT_SERIF_BOLD, 23)
        c.drawString(M, y, title)
        y -= 22
        if dek:
            y = para(c, dek, M, y, W - 2 * M, 8.7, 12, MUTED) - 10
        c.setFillColor(GRID)
        c.rect(M, 34, W - 2 * M, 0.6, stroke=0, fill=1)
        c.setFillColor(MUTED)
        c.setFont(FONT, 6.5)
        c.drawString(M, 21, "Independent G4 AI Master Challenge 001 submission  |  THOMAS LEICK")
        c.drawRightString(W - M, 21, f"{num:02d} / 07")
        return y
    return H - 42


def card(c, x, top, width, height, fill=WHITE, stroke=None, radius=8):
    c.setFillColor(fill)
    c.setStrokeColor(stroke or fill)
    c.roundRect(x, top - height, width, height, radius, stroke=1 if stroke else 0, fill=1)


def table(c, data, x, top, widths, font_size=7.5, header=True, row_heights=None, alignments=None):
    converted = []
    for ri, row in enumerate(data):
        converted.append([Paragraph(escape(str(v)), style(font_size, font_size * 1.25, WHITE if header and ri == 0 else INK, FONT_BOLD if header and ri == 0 else FONT)) for v in row])
    t = Table(converted, colWidths=widths, rowHeights=row_heights, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.35, GRID),
    ]
    if header:
        commands.append(("BACKGROUND", (0, 0), (-1, 0), INK))
        for i in range(1, len(data)):
            if i % 2 == 0:
                commands.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#EFECE4")))
    if alignments:
        for col, alignment in enumerate(alignments):
            commands.append(("ALIGN", (col, 0), (col, -1), alignment))
    t.setStyle(TableStyle(commands))
    w, h = t.wrap(sum(widths), H)
    t.drawOn(c, x, top - h)
    return top - h


def metric_card(c, x, y, w, h, title, value, sub, accent=GOLD):
    card(c, x, y, w, h, WHITE)
    c.setFillColor(accent)
    c.roundRect(x, y - h, 4, h, 2, stroke=0, fill=1)
    label(c, title, x + 13, y - 19, color=MUTED, size=6.5)
    c.setFillColor(INK)
    c.setFont(FONT_SERIF_BOLD, 21)
    c.drawString(x + 13, y - 48, value)
    para(c, sub, x + 13, y - 57, w - 24, 7, 9.3, MUTED)


def draw_coffee(c, x, y, col):
    c.setStrokeColor(col); c.setLineWidth(1.2)
    c.roundRect(x, y, 13, 10, 2, stroke=1, fill=0)
    c.arc(x + 10, y + 2, x + 19, y + 9, 260, 210)
    c.line(x + 2, y - 2, x + 15, y - 2)
    c.line(x + 5, y + 13, x + 4, y + 17); c.line(x + 10, y + 13, x + 9, y + 17)


def draw_cube(c, x, y, col):
    c.setStrokeColor(col); c.setLineWidth(1.1)
    p = c.beginPath(); p.moveTo(x + 9, y + 17); p.lineTo(x + 18, y + 12); p.lineTo(x + 9, y + 7); p.lineTo(x, y + 12); p.close()
    c.drawPath(p, stroke=1, fill=0)
    c.line(x, y + 12, x, y + 2); c.line(x + 18, y + 12, x + 18, y + 2); c.line(x + 9, y + 7, x + 9, y - 3)
    c.line(x, y + 2, x + 9, y - 3); c.line(x + 18, y + 2, x + 9, y - 3)


def draw_dumbbell(c, x, y, col):
    c.setStrokeColor(col); c.setLineWidth(1.7)
    c.line(x + 4, y + 7, x + 19, y + 7)
    for xx in (x, x + 3, x + 19, x + 22): c.line(xx, y + 2, xx, y + 12)


def draw_cover(c):
    c.setFillColor(INK); c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(GOLD); c.rect(M, H - 78, 53, 2, stroke=0, fill=1)
    label(c, "G4 AI MASTER CHALLENGE 001  /  BUSINESS DIAGNOSIS", M, H - 61, GOLD, 7)
    c.setFillColor(WHITE); c.setFont(FONT_SERIF_BOLD, 32)
    c.drawString(M, H - 167, "RavenStack -")
    c.drawString(M, H - 207, "Beyond the Churn")
    c.drawString(M, H - 247, "Headline")
    para(c, "A monthly, evidence-driven diagnosis of growth, retention and commercial movement", M, H - 286, 432, 13, 19, colors.HexColor("#D7CFBC"), FONT)
    c.setFillColor(colors.HexColor("#343936")); c.roundRect(M, H - 385, 260, 30, 15, stroke=0, fill=1)
    label(c, "CONDITIONAL DATE RECONSTRUCTION", M + 15, H - 373, GOLD, 6.5)
    para(c, "More events do not automatically mean more customers lost. In the data, event and plan-loss intensity rise while complete account-coverage-loss intensity falls.", M, H - 436, 440, 11, 17, WHITE, FONT)
    c.setFillColor(GOLD); c.setFont(FONT_SERIF_BOLD, 13); c.drawString(M, H - 522, "Measure the movement. Then decide what to fix.")
    c.setFillColor(WHITE); c.setFont(FONT_BOLD, 10); c.drawString(M, 171, "Prepared by Thomas Leick")
    c.setFillColor(colors.HexColor("#C8C9C3")); c.setFont(FONT, 7)
    c.drawString(M, 155, "Independent submission. No G4 affiliation or endorsement implied.")
    icons = [(M + 12, draw_coffee, "OBSERVE"), (M + 142, draw_cube, "DECOMPOSE"), (M + 286, draw_dumbbell, "PERSIST"), (M + 428, None, "BUILD")]
    for x, fn, title in icons:
        if fn: fn(c, x, 91, GOLD)
        else:
            c.setFillColor(GOLD); c.setFont(FONT_BOLD, 15); c.drawString(x, 96, "</>")
        label(c, title, x + 27 if fn else x + 35, 94, WHITE, 6.3)
    c.setStrokeColor(colors.HexColor("#454A46")); c.line(M, 64, W - M, 64)
    c.setFillColor(colors.HexColor("#AEB2AC")); c.setFont(FONT, 6.5)
    c.drawString(M, 45, "COFFEE / CUBE / DISCIPLINE / CODE")
    c.drawRightString(W - M, 45, "EVIDENCE BEFORE CERTAINTY")


def draw_line_chart(c, rows, x, bottom, width, height):
    left, right, top = x + 36, x + width - 8, bottom + height - 16
    plot_h = height - 40
    maxv = 1.0
    c.setStrokeColor(GRID); c.setLineWidth(0.5)
    for tick in (0, .25, .5, .75, 1.0):
        y = bottom + 22 + plot_h * tick / maxv
        c.line(left, y, right, y)
        c.setFillColor(MUTED); c.setFont(FONT, 6.2); c.drawRightString(left - 6, y - 2, f"{tick:.2f}%")
    for idx, row in enumerate(rows):
        xx = left + (right - left) * idx / max(1, len(rows) - 1)
        if idx % 3 == 0:
            c.setFillColor(MUTED); c.setFont(FONT, 5.8); c.drawCentredString(xx, bottom + 8, row["period"])
    series = [
        ("opening_cohort_churn_any_pct", GOLD_DARK, "Plan relation - lost during month"),
        ("opening_cohort_churn_at_close_pct", RED, "Plan relation - still lost at close"),
        ("opening_cohort_customer_churn_any_pct", GREEN, "Customer - complete coverage loss"),
    ]
    for key, color, _name in series:
        c.setStrokeColor(color); c.setFillColor(color); c.setLineWidth(1.6)
        previous = None
        for idx, row in enumerate(rows):
            val = row.get(key)
            if val is None:
                previous = None; continue
            xx = left + (right - left) * idx / max(1, len(rows) - 1)
            yy = bottom + 22 + plot_h * min(maxv, val) / maxv
            if previous: c.line(previous[0], previous[1], xx, yy)
            c.circle(xx, yy, 2.1, stroke=0, fill=1)
            previous = (xx, yy)
    leg_y = bottom + height - 6
    lx = left
    for _key, color, name in series:
        c.setFillColor(color); c.circle(lx, leg_y, 3, stroke=0, fill=1)
        c.setFillColor(MUTED); c.setFont(FONT, 6.2); c.drawString(lx + 7, leg_y - 2, name)
        lx += 170


def draw_bars(c, rows, x, bottom, width, height, key_a, key_b, label_a, label_b, maxv=None):
    left, right = x + 30, x + width - 6
    plot_h = height - 30
    maxv = maxv or max(max(r.get(key_a, 0), r.get(key_b, 0)) for r in rows) * 1.1 or 1
    c.setStrokeColor(GRID); c.setLineWidth(.5)
    for tick in range(4):
        y = bottom + 18 + plot_h * tick / 3
        c.line(left, y, right, y)
    slot = (right - left) / len(rows)
    for i, row in enumerate(rows):
        mid = left + slot * (i + .5)
        for j, (key, col) in enumerate(((key_a, GOLD_DARK), (key_b, GREEN))):
            value = row.get(key, 0) or 0
            bh = plot_h * value / maxv
            c.setFillColor(col); c.rect(mid - 3.5 + j * 4, bottom + 18, 3.1, bh, stroke=0, fill=1)
        if i % 3 == 0:
            c.setFillColor(MUTED); c.setFont(FONT, 5.8); c.drawCentredString(mid, bottom + 7, row["period"])
    c.setFillColor(GOLD_DARK); c.rect(left, bottom + height - 4, 5, 5, stroke=0, fill=1)
    c.setFillColor(MUTED); c.setFont(FONT, 6.2); c.drawString(left + 8, bottom + height - 3, label_a)
    c.setFillColor(GREEN); c.rect(left + 146, bottom + height - 4, 5, 5, stroke=0, fill=1)
    c.setFillColor(MUTED); c.drawString(left + 154, bottom + height - 3, label_b)


def write_manifest(e, d, scenarios):
    lines = [
        "# Paper numerical evidence manifest", "",
        "This manifest is generated by `generate_paper.py` from the checked local analysis outputs and source CSVs. Values are evidence references, not new business claims.",
        "", "## Inputs and integrity", "",
        "| Input | Path | SHA-256 |", "|---|---|---|",
    ]
    for name, digest in e["hashes"].items(): lines.append(f"| {name} | `solution/data/raw/{name}` | `{digest}` |")
    for name, path in (("Daily ledger", LEDGER_PATH), ("Five-table business analysis", BUSINESS_PATH), ("Transition audit", TRANSITION_PATH)):
        lines.append(f"| {name} | `{path.relative_to(ROOT)}` | `{sha256(path)}` |")
    lines += ["", "## Claims and calculations", "", "| Paper claim | Calculation / denominator | Source and classification |", "|---|---|---|"]
    claims = [
        ("73 event rows in 2023; 527 in 2024", "Rows grouped by `churn_date` year; 600 rows total.", "Original churn-events CSV / business-investigation.json; OBSERVED EVENT ROWS"),
        ("8.64 and 13.48 event rows per 100 account-months", "73/845×100; 527/3,909×100. Exposure is sum of monthly opening customer counts.", "Daily ledger monthly rows; NORMALIZED EVENT INTENSITY, not churn rate"),
        ("6 and 56 plan proxy losses; 0.427 and 0.595 per 100 relation-months", "6/1,406×100; 56/9,414×100.", "Daily ledger monthly rows; CONDITIONAL PLAN-PROXY INTENSITY"),
        ("2 and 6 complete account coverage-loss episodes; 0.237 and 0.153 per 100 account-months", "2/845×100; 6/3,909×100.", "Daily ledger; CONDITIONAL ACCOUNT-COVERAGE EPISODE INTENSITY"),
        ("2024 opening cohort: 7/374 = 1.87%; 3/374 = 0.80%; 0/190 accounts", "Opening account-plan-tier relationships lost any time / still lost at close; opening accounts with complete coverage loss.", "Daily ledger 2024 annual period; CONDITIONAL DATE RECONSTRUCTION"),
        ("January 2023 monthly opening-cohort rates are UNDEFINED", "The monthly ledger has zero opening account-plan relations and zero opening customers; both rate denominators are zero and the source rates are null.", "Daily ledger 2023-01 row; UNDEFINED, not zero"),
        ("October 2024: 9/1,073 = 0.84% opening-cohort loss rate, the 24-month maximum", "Unique opening-cohort relations lost any time / opening relations; 9 / 1,073 × 100 = 0.83877%.", "Daily ledger monthly row 2024-10; CONDITIONAL DATE RECONSTRUCTION"),
        ("December 2024: 11 gross plan-loss events; 5/1,279 = 0.39% opening-cohort loss", "All gross date-derived loss events can include relations acquired during the month; cohort loss uses opening relations only. These numerators are not interchangeable.", "Daily ledger monthly row 2024-12; CONDITIONAL DATE RECONSTRUCTION"),
        ("54 of 62 plan losses retained another plan; 8 complete-loss episodes later returned; 60 accounts affected", "Count movement ledger, distinct account IDs; count returned coverage episodes over observation window.", "Daily ledger summary and account movement candidates; CONDITIONAL PLAN-LEVEL PROXY"),
        ("Enterprise 5/120; Basic 2/132; Pro 0/122", "Opening 2024 plan-tier cohort loss any time / opening relations; Wilson 95% intervals computed in generator.", "Daily ledger annual 2024 plan_segments; CONDITIONAL, small event counts"),
        ("Usage: 124,561 to 125,964 (+1.13%); 24.462 to 24.747 per observed account-month (+1.17%)", "Source recorded counts; no temporal causal claim. 19,142 rows before linked subscription start, 290 after end; 5,568 within reconstructed intervals.", "Five-table business-investigation.json; DESCRIPTIVE SOURCE VOLUME"),
        ("Support: 3.9804 vs 3.9833 mean ticket satisfaction; response 89 vs 87 min; resolution 35h both", "Event-history vs no-event account groups; 815/1,395 and 360/605 scored/missing-ticket denominators; account cluster summaries also reported.", "Business analysis support.by_label; DESCRIPTIVE, NON-TEMPORAL"),
        ("Reason codes: features 114, support 104, budget 104, unknown 95, competitor 92, pricing 91", "Counts of all 600 event rows; percent of 600, not percent of churned customers.", "Original churn-events CSV grouped by reason_code; DECLARED REASONS"),
        ("Upgrade/downgrade flags: 529/218 rows; 23 both", "Source subscription rows; no dated from/to linkage.", "Original subscriptions CSV and transition-audit.json; ROW FLAGS, MIGRATION UNKNOWN"),
    ]
    for a,b,c0 in claims: lines.append(f"| {a} | {b} | {c0} |")
    lines += ["", "## Scenario assumptions (illustrative, not observed)", "", "All `$` amounts below are hypothetical USD-equivalent units, not a currency observed in the source data. Eligible pool is hypothetically 60 accounts, using historical affected-account count only as a sizing reference; current eligibility is UNKNOWN. Cost per contacted account is assumed to be $20 in all three scenarios, so total assumed cost is $1,200. `Expected retained equivalents = 60 × uptake × incremental lift`; `gross modeled value = retained equivalents × assumed monthly value × horizon`; `net modeled value = gross - contact cost`; `break-even monthly value = contact cost / (retained equivalents × horizon)`. No scenario is measured lift, revenue, accounting profit or ROI.", "", "| Scenario | Uptake | Lift | Retained equivalents | Monthly value | Months | Gross | Cost | Net | Break-even / month |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for s in scenarios:
        lines.append(f"| {s['name']} | {s['uptake']:.0%} | {s['lift']:.0%} | {s['retained']:.2f} | ${s['monthly_value']:,.2f} | {s['months']} | ${s['gross']:,.2f} | ${s['cost']:,.2f} | ${s['net']:,.2f} | ${s['breakeven']:,.2f} |")
    lines += ["", "## Generated artifact", "", f"- PDF: `{PDF_PATH.relative_to(ROOT)}`", f"- PDF SHA-256: `{sha256(PDF_PATH)}`", "- Markdown narrative: `docs/paper/RAVENSTACK-THE-CHURN-PARADOX.md`", "- Generator: `docs/paper/generate_paper.py`", "- Source tables: five original CSVs; hashes above.", "- Reported customer churn remains UNKNOWN as a commercially verified KPI; plan-level calculations are conditional date reconstructions.", ""]
    MANIFEST_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_json_manifest(e, d, scenarios):
    source_rows = e["business"]["record_counts"]
    claims = {
        "event_rows_by_year": {year: d["years"][year]["events"] for year in ("2023", "2024")},
        "exposure_event_intensity_per_100": {year: round(d["years"][year]["event_per_100"], 6) for year in ("2023", "2024")},
        "plan_proxy_loss_intensity_per_100_relation_months": {year: round(d["years"][year]["plan_per_100"], 6) for year in ("2023", "2024")},
        "complete_account_coverage_loss_intensity_per_100_account_months": {year: round(d["years"][year]["account_per_100"], 6) for year in ("2023", "2024")},
        "opening_2024_cohort": {
            "opening_relations": d["annual24"]["opening_plan_relations"],
            "lost_any_time": d["annual24"]["opening_relations_lost_any_time"],
            "lost_at_close": d["annual24"]["opening_relations_lost_at_close"],
            "opening_customers": d["annual24"]["opening_customers"],
            "customers_lost_at_close": d["annual24"]["opening_customers_lost_at_close"],
        },
        "plan_segments_2024": [{
            "tier": s["plan_tier"], "opening": s["opening_relations"],
            "lost_any_time": s["opening_relations_lost_any_time"],
            "rate_pct": round(100 * s["opening_relations_lost_any_time"] / s["opening_relations"], 4),
            "wilson_95_pct": [round(s["low"], 4), round(s["high"], 4)],
        } for s in d["segments"]],
        "reason_rows": dict(d["reasons"]),
        "account_cases": [{k: a[k] for k in ("account_id", "industry", "country", "referral_source", "loss_date", "return_date", "loss_tier", "return_tier")} for a in d["cases"]],
        "scenario_assumptions_and_results": scenarios,
        "classification": "Customer churn is commercially UNKNOWN; plan-tier is a conditional proxy reconstructed from dates.",
    }
    manifest = {
        "manifest_version": "2.0",
        "generated_at": date.today().isoformat(),
        "paper": {
            "pdf": str(PDF_PATH.relative_to(ROOT)), "pdf_sha256": sha256(PDF_PATH),
            "pdf_pages": 7, "page_size": "A4",
            "markdown": "docs/paper/RAVENSTACK-THE-CHURN-PARADOX.md",
            "markdown_sha256": sha256(HERE / "RAVENSTACK-THE-CHURN-PARADOX.md"),
            "generator": "docs/paper/generate_paper.py",
            "generator_sha256": sha256(HERE / "generate_paper.py"),
        },
        "source_csv": {name: {"sha256": digest} for name, digest in e["hashes"].items()},
        "analysis_artifacts": {
            "daily_ledger": {"path": str(LEDGER_PATH.relative_to(ROOT)), "sha256": sha256(LEDGER_PATH)},
            "five_table_analysis": {"path": str(BUSINESS_PATH.relative_to(ROOT)), "sha256": sha256(BUSINESS_PATH)},
            "transition_audit": {"path": str(TRANSITION_PATH.relative_to(ROOT)), "sha256": sha256(TRANSITION_PATH)},
            "monthly_rows": len(d["monthly"]),
        },
        "source_row_counts": source_rows,
        "claims": claims,
        "visual_validation": {
            "rendered_pages": 7,
            "render_prefix": "docs/paper/qa-render-v11/page-*.png",
            "inspection": "All seven rendered pages inspected; final visual pass after corrections.",
        },
    }
    (HERE / "EVIDENCE-MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_pdf(e, d, scenarios):
    register_fonts()
    c = canvas.Canvas(str(PDF_PATH), pagesize=A4, pageCompression=1)
    c.setTitle("RavenStack - Beyond the Churn Headline")
    c.setAuthor("Thomas Leick")
    c.setSubject("G4 AI Master Challenge 001 - evidence-driven churn diagnosis")
    c.setCreator("RavenStack paper generator")

    # Page 1 - cover
    draw_cover(c); c.showPage()

    # Page 2 - three direct answers
    y = begin_page(c, 2, "EXECUTIVE ANSWER", "The record is mixed - and actionable", "Events and plan losses intensified; complete-account coverage-loss intensity did not. That distinction changes the decision.")
    card(c, M, y, W - 2 * M, 90, INK)
    label(c, "THE BUSINESS FINDING", M + 15, y - 20, GOLD, 6.5)
    para(c, "In 2024 the event log and conditional plan-proxy loss rate rose, but the normalized rate of complete account coverage-loss episodes fell. Fifty-four of 62 plan losses left another plan active; all eight complete-loss episodes later returned. This is not a verified customer-churn trend.", M + 15, y - 31, W - 2 * M - 30, 9.5, 13.5, WHITE)
    y -= 108
    answers = [
        ("Q1  /  WHY?", "Diagnosis: 62 reconstructed account-plan losses; in 54 (87.1%), another plan relation remained active, so most were not complete account-coverage losses. Priority hypotheses: features 114/600 (19.0%), support 104/600 (17.3%) and budget 104/600 (17.3%). These are declared reasons, not proof of why customers ended a commercial relationship. Confidence: high on counts; low on causality.", GOLD_DARK),
        ("Q2  /  WHO?", "Enterprise has 5/120 conditional 2024 opening relations lost (4.17%); Basic 2/132 (1.52%); Pro 0/122. Eight complete-loss/return histories merit reconciliation, not risk scoring. Confidence: moderate on date-reconstructed history; low on future risk.", RED),
        ("Q3  /  WHAT NEXT?", "Fix lifecycle/event links; reconcile 60 historical affected accounts; audit tier flags; then randomize eligible accounts into outreach and holdout. Scenario net value ranges from -$1,056 to +$16,080 under stated assumptions. Confidence: high on arithmetic; low on assumptions.", GREEN),
    ]
    for q, text, accent in answers:
        h = 108
        card(c, M, y, W - 2*M, h, WHITE)
        c.setFillColor(accent); c.roundRect(M, y - h, 4, h, 2, stroke=0, fill=1)
        label(c, q, M + 15, y - 19, accent, 7)
        para(c, text, M + 15, y - 29, W - 2*M - 30, 9.1, 13.2, INK)
        y -= h + 10
    label(c, "DECISION", M, y - 2, GOLD_DARK, 6.7)
    para(c, "Fund measurement and focused case review now. Do not fund broad discounting on the strength of event counts alone.", M, y - 12, W - 2*M, 9, 12, INK, FONT_BOLD)
    c.showPage()

    # Page 3 - monthly mathematics
    y = begin_page(c, 3, "MONTHLY CHURN MATHEMATICS", "Scale, rate and unit tell different stories", "Monthly values aggregate the daily account x plan-tier ledger. Jan-23 has no opening base, so its churn rate is UNDEFINED, not 0%.")
    summary = [
        ["Measure", "2023", "2024", "Change / read"],
        ["Recorded event rows", "73", "527", "+454 rows; events, not lost customers"],
        ["Opening account exposure", "845 acct-months", "3,909 acct-months", "4.63x exposure"],
        ["Events / 100 account-months", "8.64", "13.48", "+56.1% recorded intensity"],
        ["Plan-proxy losses / relation-months", "6 / 1,406", "56 / 9,414", "0.427 to 0.595 per 100"],
        ["Complete coverage-loss episodes", "2", "6", "0.237 to 0.153 per 100 account-months"],
    ]
    y = table(c, summary, M, y, [154, 83, 92, 182], 7.2) - 13
    c.setFillColor(INK); c.setFont(FONT_BOLD, 7); c.drawString(M, y, "Opening-cohort monthly loss rates (%) - 24 months")
    oct = next(row for row in d["monthly"] if row["period"] == "2024-10")
    dec = next(row for row in d["monthly"] if row["period"] == "2024-12")
    c.setFont(FONT_BOLD, 5.8); c.setFillColor(GOLD_DARK)
    c.drawString(M, y-10, f"OCT '24 · {oct['opening_relations_lost_any_time']} opening-cohort losses / {oct['opening_plan_relations']:,} = {oct['opening_cohort_churn_any_pct']:.2f}% rate peak")
    c.setFillColor(RED)
    c.drawRightString(W-M, y-10, f"DEC '24 · {dec['gross_plan_relation_loss_events']} gross events; {dec['opening_relations_lost_any_time']}/{dec['opening_plan_relations']:,} opening cohort = {dec['opening_cohort_churn_any_pct']:.2f}%")
    draw_line_chart(c, d["monthly"], M, y - 190, W - 2*M, 170)
    chart_bottom = y - 204
    c.setFillColor(INK); c.setFont(FONT_BOLD, 7); c.drawString(M, chart_bottom, "Monthly flows (counts) - losses vs. additions")
    draw_bars(c, d["monthly"], M, chart_bottom - 111, W - 2*M, 98,
              "gross_plan_relation_loss_events", "new_plan_relationships",
              "plan coverage losses", "new plan relations", maxv=150)
    draw_bars(c, d["monthly"], M, chart_bottom - 219, W - 2*M, 98,
              "new_customers", "customer_reactivations",
              "new customers", "customer reactivations", maxv=45)
    y2 = chart_bottom - 226
    para(c, f"The +454 event-row increase decomposes symmetrically into {d['scale_component']:.1f} rows from greater exposure and {d['intensity_component']:.1f} from higher event intensity. This is arithmetic, not causal attribution; logging change and composition effects remain unidentifiable.", M, y2, W - 2*M, 7.1, 9.5, MUTED)
    c.showPage()

    # Page 4 - cross-table drivers
    y = begin_page(c, 4, "DRIVERS & EVIDENCE", "Lifecycle data are the decision gate", "Five tables describe different parts of the customer journey. Their joins and time fields limit causal interpretation.")
    half = (W - 2*M - 12) / 2
    # cards with fixed sizes
    card(c, M, y, half, 195, WHITE)
    label(c, "DECLARED EVENT REASONS  /  N=600", M+13, y-19, GOLD_DARK, 6.3)
    reason_rows = [["Reason", "Rows", "Share"]]
    for reason in ("features", "support", "budget", "unknown", "competitor", "pricing"):
        count = d["reasons"][reason]
        reason_rows.append([reason.title(), str(count), f"{count/600:.1%}"])
    table(c, reason_rows, M+10, y-31, [88, 39, 53], 6.7)
    para(c, "Feature/value, service and affordability deserve separate validation. The reason code is not a verified cause or a unique customer count.", M+13, y-164, half-24, 7.0, 9.1, MUTED)

    x2 = M + half + 12
    card(c, x2, y, half, 195, WHITE)
    label(c, "USAGE  /  SOURCE VOLUME", x2+13, y-19, GOLD_DARK, 6.3)
    u23, u24 = d["usage"]["2023"], d["usage"]["2024"]
    para(c, f"Usage count: {u23['recorded_usage_count']:,.0f} to {u24['recorded_usage_count']:,.0f} (+1.13%). Per observed account-month: {u23['usage_count_per_observed_account_month']:.3f} to {u24['usage_count_per_observed_account_month']:.3f} (+1.17%).", x2+13, y-36, half-26, 8.2, 12, INK)
    para(c, "But 19,142/25,000 usage rows predate linked subscription start, and 290 follow recorded end. Only 5,568 rows are interval-valid; not a verified pre-loss window.", x2+13, y-99, half-26, 7.4, 10, MUTED)

    row2 = y - 208
    card(c, M, row2, half, 190, WHITE)
    label(c, "SUPPORT  /  ANY EVENT VS NONE", M+13, row2-19, GOLD_DARK, 6.3)
    pos, neg = d["support"]["positive"], d["support"]["negative"]
    support_rows = [
        ["Measure", "Event", "No event"],
        ["Mean satisfaction", f"{pos['satisfaction_mean_ticket']:.4f} (815 scored)", f"{neg['satisfaction_mean_ticket']:.4f} (360)"],
        ["Missing scores", f"{pos['satisfaction_missing_tickets']}/{pos['ticket_rows']}", f"{neg['satisfaction_missing_tickets']}/{neg['ticket_rows']}"],
        ["Median first response", f"{pos['first_response_median_minutes']} min", f"{neg['first_response_median_minutes']} min"],
        ["Median resolution", f"{pos['resolution_median_hours']} h", f"{neg['resolution_median_hours']} h"],
        ["Account mean escalation", f"{pos['mean_account_escalation_rate']:.2%}", f"{neg['mean_account_escalation_rate']:.2%}"],
    ]
    table(c, support_rows, M+10, row2-31, [88, 68, 68], 6.1)
    para(c, "Small retrospective differences; tickets cluster by account and are not aligned to loss dates. Satisfaction is missing on 825/2,000 tickets.", M+13, row2-151, half-24, 6.8, 8.6, MUTED)

    card(c, x2, row2, half, 190, PALE_GOLD)
    label(c, "LIFECYCLE  /  STRONGEST ACTIONABLE FINDING", x2+13, row2-19, GOLD_DARK, 6.1)
    para(c, "500 accounts; 5,000 subscriptions; 600 event rows across 352 accounts. Account churn flags mark 110 accounts; subscription flags touch 312. Account flag vs. any-event history differs for 312/500 accounts.", x2+13, row2-36, half-26, 7.8, 11, INK)
    para(c, "The subscription table contains 529 upgrade and 218 downgrade flags (23 both), but no dated from/to linkage. Instrument the lifecycle before treating these as migrations.", x2+13, row2-115, half-26, 7.2, 9.6, MUTED)

    c.showPage()

    # Page 5 - segments and cases
    y = begin_page(c, 5, "SEGMENTS & ACCOUNTS", "Prioritize investigation, not prediction", "Small, conditional opening-cohort losses identify where to look first - not who is likely to leave next.")
    segment_data = [["Plan-tier proxy", "Opening", "Lost any time", "Rate (95% Wilson)", "Still lost"]]
    seg_by = {s["plan_tier"]: s for s in d["segments"]}
    for name in ("Enterprise", "Basic", "Pro"):
        s = seg_by[name]
        k,n = s["opening_relations_lost_any_time"],s["opening_relations"]
        segment_data.append([name, str(n), str(k), f"{100*k/n:.2f}% ({s['low']:.2f}-{s['high']:.2f})", str(s["opening_relations_lost_at_close"])])
    y = table(c, segment_data, M, y, [106, 65, 95, 145, 74], 7.2) - 10
    para(c, "Enterprise is 2.65 percentage points above Basic (4.17% vs. 1.52%), but the Wilson intervals overlap widely. No stable tier ranking or calibrated risk follows from 5, 2 and 0 events.", M, y, W - 2*M, 8.1, 11.5, MUTED)
    y -= 31
    label(c, "EIGHT COMPLETE-COVERAGE-LOSS EPISODES THAT LATER RETURNED", M, y, GOLD_DARK, 6.6)
    y -= 11
    case_data = [["Account", "Segment / source", "First loss -> return", "Coverage around event"]]
    for a in d["cases"]:
        case_data.append([
            a["account_id"],
            f"{a['industry']} / {a['country']} / {a['referral_source']}",
            f"{a['loss_date']} -> {a['return_date']}",
            f"{a['loss_tier']} lost; {a['return_tier']}",
        ])
    y = table(c, case_data, M, y, [74, 119, 119, 173], 6.45)
    y -= 14
    para(c, "Why these cases: each has an observed date-derived interval with no plan-tier coverage, followed by a recorded return. Review the eight first, then the broader 60-account loss population. Validate current status before outreach; account-only event reasons cannot be attached to a particular plan.", M, y, W-2*M, 7.6, 10, INK)
    c.showPage()

    # Page 6 - decision and scenarios
    y = begin_page(c, 6, "DECISION & QUANTIFIED IMPACT", "Measure first. Test retention next.", "Five actions translate the strongest evidence into reversible decisions. Only the scenario values are hypothetical.")
    actions = [
        ("01", "Instrument lifecycle identity", "Data / RevOps · days 0-30", "Link cancellation, reactivation and plan-change events to account + subscription + effective date. KPI: linked and reconciled event share."),
        ("02", "Reconcile affected histories", "CS Operations / RevOps · days 0-30", "Review 60 historical accounts, starting with 8 complete-loss/return cases. Planning effort: 19 analyst/CS-ops hours (assumed)."),
        ("03", "Audit Enterprise and tier flags", "RevOps · days 30-60", "Test 5/120 Enterprise versus 2/132 Basic and 0/122 Pro against contracts; verify the 529/218 row flags."),
        ("04", "Validate stated reasons", "CS / Product · days 30-60", "Follow up feature, support and budget reasons separately; link customer-confirmed reason to a lifecycle outcome."),
        ("05", "Randomized retention pilot", "CS / Analytics · days 60-90", "After eligibility is reliable, randomize at account level; 90-day verified coverage primary, downgrade and support guardrails."),
    ]
    row_h = 49
    for no, title, owner, text in actions:
        card(c, M, y, W-2*M, row_h, WHITE)
        c.setFillColor(GOLD_DARK); c.setFont(FONT_SERIF_BOLD, 14); c.drawString(M+10, y-29, no)
        c.setFillColor(INK); c.setFont(FONT_BOLD, 7.8); c.drawString(M+39, y-17, title)
        c.setFillColor(GOLD_DARK); c.setFont(FONT_BOLD, 6.1); c.drawRightString(W-M-10, y-17, owner)
        para(c, text, M+39, y-23, W-2*M-51, 6.9, 8.7, MUTED)
        y -= row_h + 6
    y -= 4
    label(c, "PILOT SENSITIVITY  /  ILLUSTRATIVE USD-EQUIVALENT  /  NOT OBSERVED REVENUE OR CAUSAL ROI", M, y, GOLD_DARK, 6.1)
    y -= 12
    scenario_data = [["Case", "Uptake x lift", "Retained eq.", "Value x months", "Gross", "Cost", "Net", "Break-even / mo"]]
    for s in scenarios:
        net = f"-${abs(s['net']):,.0f}" if s["net"] < 0 else f"${s['net']:,.0f}"
        scenario_data.append([
            s["name"], f"{s['uptake']:.0%} x {s['lift']*100:.0f} pp", f"{s['retained']:.2f}",
            f"${s['monthly_value']:.0f} x {s['months']}", f"${s['gross']:,.0f}",
            f"${s['cost']:,.0f}", net, f"${s['breakeven']:,.2f}",
        ])
    y = table(c, scenario_data, M, y, [61, 73, 68, 77, 60, 55, 61, 78], 6.3)
    y -= 7
    y = para(c, "The 60 accounts are historical investigation cases, not a verified current eligible retention population. All scenarios assume eligibility and hypothetical values; they are not observed revenue or causal ROI.", M, y, W-2*M, 7.0, 9.3, INK, FONT_BOLD) - 6
    para(c, "Model inputs: 60 hypothetical eligible accounts; $20 contact cost each ($1,200 total); scenario uptake 40/60/80%; assumed incremental retention lift 2/5/10 percentage points; monthly value $100/$200/$400; benefit horizon 3/6/9 months. Net = modeled value minus outreach cost only. Conservative case is -$1,056. All inputs require validation; no present-day eligibility, margin, labor, discounting or accounting revenue is observed.", M, y, W-2*M, 6.65, 8.7, MUTED)
    c.showPage()

    # Page 7 - roadmap and method
    y = begin_page(c, 7, "EXECUTION ROADMAP & METHOD", "A decision sequence with explicit gates", "The paper is the primary deliverable; the local monthly laboratory is a companion for inspecting evidence and assumptions.")
    steps = [
        ["WHEN", "DELIVER", "EXIT GATE"],
        ["0-30 days", "Lifecycle data contract; review eight full-loss/return cases and 60 plan-loss histories.", "Effective dates and a customer-level active/lost definition approved by RevOps/CS."],
        ["31-60 days", "Audit Enterprise cohort and plan flags; validate stated feature/support/budget reasons; instrument activation.", "Outcome/event linkage and current eligible population are measurable."],
        ["61-90 days", "Account-randomized outreach/holdout pilot; publish 90-day effect and guardrails with uncertainty.", "Scale only if customer outcome improves and downside guardrails hold."],
    ]
    y = table(c, steps, M, y, [75, 245, 173], 7.1) - 20
    label(c, "WHAT THE NUMBERS MEAN", M, y, GOLD_DARK, 6.8); y -= 12
    method = (
        "Customer churn rate = unique eligible customers lost in the period / unique active customers at its opening. A commercially verified customer churn KPI is not identifiable here. "
        "The conditional 2024 account x plan-tier opening cohort gives 7/374 (1.87%) losing coverage at any time, 3/374 (0.80%) still uncovered at year-end, and 0/190 opening accounts with complete coverage loss. "
        "Use this only as a PLAN-LEVEL PROXY under date intervals [start_date, end_date). There is no product_id; dates do not establish effective commercial end; account-only events have no subscription link. "
        "Recorded-event intensity is rows per opening account-month, not a churn rate. Recurring revenue changes, causal drivers and calibrated future risk remain UNKNOWN."
    )
    y = para(c, method, M, y, W-2*M, 8, 11.2, INK) - 18
    card(c, M, y, W-2*M, 76, INK)
    label(c, "REPRODUCE / EXPLORE", M+14, y-19, GOLD, 6.4)
    para(c, "Paper source, generator and numerical evidence manifest live in docs/paper/. From solution/: run the documented analysis commands, then `docker compose up --build` for the companion monthly lab. Source hashes and formulas are in the manifest. Dataset credit: River @ Rivalytics (synthetic, MIT-like terms). This is independent of G4; no endorsement is implied.", M+14, y-31, W-2*M-28, 7.4, 10, WHITE)
    y -= 92
    label(c, "AUTHORIAL MARK", M, y, GOLD_DARK, 6.5)
    para(c, "Coffee - observe. Cube - decompose. Training - persist. Code - test and build. A personal working signature, not a credential claim.", M, y-10, W-2*M, 7.4, 10, MUTED)
    c.showPage()
    c.save()


def main() -> None:
    e = load_evidence()
    d = derived(e)
    scenarios = []
    for name, uptake, lift, value, months in [
        ("Conservative", .40, .02, 100.0, 3),
        ("Base", .60, .05, 200.0, 6),
        ("Optimistic", .80, .10, 400.0, 9),
    ]:
        eligible = 60
        cost = eligible * 20.0
        retained = eligible * uptake * lift
        gross = retained * value * months
        scenarios.append({"name": name, "uptake": uptake, "lift": lift, "monthly_value": value,
                          "months": months, "eligible": eligible, "cost": cost, "retained": retained,
                          "gross": gross, "net": gross - cost,
                          "breakeven": cost / (retained * months) if retained * months else math.inf})
    build_pdf(e, d, scenarios)
    write_manifest(e, d, scenarios)
    write_json_manifest(e, d, scenarios)
    print(f"Generated {PDF_PATH} ({PDF_PATH.stat().st_size} bytes)")
    print(f"Pages: 7; source rows: {e['business']['record_counts']}; monthly rows: {len(d['monthly'])}")
    print(f"2024 opening plan loss: {d['annual24']['opening_relations_lost_any_time']}/{d['annual24']['opening_plan_relations']}")
    print(f"Scenarios: {[(s['name'], round(s['retained'],2), round(s['gross'],2), round(s['net'],2)) for s in scenarios]}")


if __name__ == "__main__":
    main()
