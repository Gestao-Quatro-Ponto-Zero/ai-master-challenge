#!/usr/bin/env python3
"""Build the RavenStack executive paper from the checked analytical outputs."""
from __future__ import annotations

import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle


ROOT = Path(__file__).resolve().parents[2]
PAPER_DIR = Path(__file__).resolve().parent
ANALYTICS = ROOT / "solution/analysis/daily_portfolio_churn/outputs/g4-alignment/daily-portfolio-churn.json"
BUSINESS = ROOT / "solution/analysis/business_drivers/outputs/g4-alignment/business-investigation.json"
OUTPUT = PAPER_DIR / "RAVENSTACK-THE-CHURN-PARADOX.pdf"

PAGE_W, PAGE_H = A4
INK = colors.HexColor("#202625")
CHARCOAL = colors.HexColor("#171C1B")
IVORY = colors.HexColor("#F4F1E8")
PAPER = colors.HexColor("#FCFAF4")
GOLD = colors.HexColor("#AE8C52")
GOLD_LIGHT = colors.HexColor("#D8C69F")
MOSS = colors.HexColor("#527260")
RED = colors.HexColor("#A25645")
MUTED = colors.HexColor("#727970")
RULE = colors.HexColor("#D8D4C9")
WHITE = colors.white

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
pdfmetrics.registerFont(TTFont("DejaVu", str(FONT_DIR / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Oblique", str(FONT_DIR / "DejaVuSans-Oblique.ttf")))


def clean(value: str) -> str:
    return (value.replace("–", "-").replace("—", "-").replace("−", "-")
            .replace("‑", "-").replace("×", "x").replace("÷", "/")
            .replace("•", "·").replace("→", "to").replace("≥", ">="))


def p(c: canvas.Canvas, text: str, x: float, top: float, width: float,
      size: float = 9, leading: float | None = None, color=INK,
      bold: bool = False, font: str | None = None, align=TA_LEFT) -> float:
    text = clean(text)
    face = font or ("DejaVu-Bold" if bold else "DejaVu")
    style = ParagraphStyle(
        name="paper", fontName=face, fontSize=size, leading=leading or size * 1.42,
        textColor=color, alignment=align, spaceAfter=0, spaceBefore=0,
        allowWidows=0, allowOrphans=0,
    )
    para = Paragraph(text, style)
    _, height = para.wrap(width, PAGE_H)
    para.drawOn(c, x, top - height)
    return height


def page_bg(c: canvas.Canvas, page_no: int, section: str) -> None:
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    c.setFillColor(INK)
    c.setFont("DejaVu-Bold", 7.2)
    c.drawString(42, PAGE_H - 29, "RAVENSTACK  /  THE CHURN PARADOX")
    c.setFillColor(GOLD)
    c.drawRightString(PAGE_W - 42, PAGE_H - 29, section.upper())
    c.setStrokeColor(RULE)
    c.setLineWidth(.55)
    c.line(42, PAGE_H - 38, PAGE_W - 42, PAGE_H - 38)
    c.line(42, 31, PAGE_W - 42, 31)
    c.setFillColor(MUTED)
    c.setFont("DejaVu", 7)
    c.drawString(42, 19, "Independent G4 AI Master Challenge 001 submission")
    c.drawRightString(PAGE_W - 42, 19, f"THOMAS LEICK     /     {page_no:02d}")


def title(c, kicker, heading, deck, y=PAGE_H - 65):
    p(c, kicker.upper(), 42, y, PAGE_W - 84, 7.2, color=GOLD, bold=True)
    h = p(c, heading, 42, y - 16, PAGE_W - 84, 24, 28, color=INK, bold=True)
    p(c, deck, 42, y - 16 - h - 7, PAGE_W - 84, 9, 13, color=MUTED)
    return y - 16 - h - 28


def card(c, x, top, width, height, label, value, note, accent=GOLD):
    c.setFillColor(IVORY)
    c.roundRect(x, top - height, width, height, 8, stroke=0, fill=1)
    c.setFillColor(accent)
    c.rect(x, top - height, 3, height, stroke=0, fill=1)
    p(c, label.upper(), x + 14, top - 13, width - 26, 7, color=MUTED, bold=True)
    p(c, value, x + 14, top - 32, width - 26, 21, 24, color=INK, bold=True)
    p(c, note, x + 14, top - 63, width - 26, 7.4, 10.4, color=MUTED)


def pill(c, x, y, text, fill=GOLD):
    text = clean(text)
    w = pdfmetrics.stringWidth(text, "DejaVu-Bold", 6.4) + 16
    c.setFillColor(fill)
    c.roundRect(x, y - 4, w, 17, 8, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont("DejaVu-Bold", 6.4)
    c.drawString(x + 8, y + 1, text)
    return w


def draw_line_chart(c, rows, x, y, width, height):
    left, right, bottom, top = x + 37, x + width - 10, y + 27, y + height - 18
    maxv = 1.0
    c.setStrokeColor(RULE)
    c.setLineWidth(.5)
    for tick in range(0, 6):
        val = tick * .2
        yy = bottom + (top - bottom) * val / maxv
        c.line(left, yy, right, yy)
        c.setFillColor(MUTED)
        c.setFont("DejaVu", 6)
        c.drawRightString(left - 7, yy - 2, f"{val:.1f}%")
    n = len(rows)
    xs = [left + (right - left) * i / max(1, n - 1) for i in range(n)]
    series = [
        ("opening_cohort_churn_any_pct", GOLD, "Plan proxy - gross"),
        ("opening_cohort_churn_at_close_pct", GOLD_LIGHT, "Plan proxy - still lost"),
        ("opening_cohort_customer_churn_any_pct", MOSS, "Customer - gross"),
        ("opening_cohort_customer_churn_at_close_pct", colors.HexColor("#93AD9B"), "Customer - still lost"),
    ]
    for key, color, _ in series:
        pts = [(xs[i], bottom + (top - bottom) * (row[key] or 0) / 100 / maxv)
               for i, row in enumerate(rows) if row[key] is not None]
        c.setStrokeColor(color)
        c.setLineWidth(1.6)
        c.setDash(4, 3) if "at_close" in key else c.setDash()
        for a, b in zip(pts, pts[1:]):
            c.line(a[0], a[1], b[0], b[1])
        c.setDash()
        c.setFillColor(color)
        for px, py in pts:
            c.circle(px, py, 1.8, stroke=0, fill=1)
    c.setFillColor(MUTED)
    c.setFont("DejaVu", 5.8)
    for i in range(0, n, 3):
        c.saveState()
        c.translate(xs[i], bottom - 9)
        c.rotate(35)
        c.drawString(0, 0, rows[i]["period"])
        c.restoreState()
    legend_y = y + 3
    lx = x + 40
    for _, color, label in series:
        c.setStrokeColor(color)
        c.setLineWidth(1.5)
        c.line(lx, legend_y, lx + 13, legend_y)
        p(c, label, lx + 17, legend_y + 4, 92, 6.1, color=MUTED)
        lx += 123


def draw_bar_chart(c, rows, x, y, width, height):
    left, right, bottom, top = x + 28, x + width - 8, y + 20, y + height - 14
    maxv = max(150, max(max(r["new_plan_relationships"], r["new_customers"], r["gross_plan_relation_loss_events"], r["plan_reactivations"]) for r in rows))
    c.setStrokeColor(RULE)
    c.setLineWidth(.5)
    for tick in range(0, 4):
        value = maxv * tick / 3
        yy = bottom + (top - bottom) * tick / 3
        c.line(left, yy, right, yy)
        c.setFillColor(MUTED)
        c.setFont("DejaVu", 6)
        c.drawRightString(left - 6, yy - 2, f"{value:.0f}")
    colorset = [GOLD, RED, MOSS, colors.HexColor("#81988A")]
    keys = ["new_plan_relationships", "gross_plan_relation_loss_events", "new_customers", "plan_reactivations"]
    labels = ["New plan relations", "Plan loss events", "New customers", "Plan returns"]
    groupw = (right - left) / len(rows)
    bw = max(1.1, groupw * .17)
    for i, row in enumerate(rows):
        center = left + groupw * (i + .5)
        for j, key in enumerate(keys):
            h = (top - bottom) * row[key] / maxv
            xx = center + (j - 1.5) * (bw + 1)
            c.setFillColor(colorset[j])
            c.rect(xx, bottom, bw, h, stroke=0, fill=1)
        if i % 3 == 0:
            c.setFillColor(MUTED)
            c.setFont("DejaVu", 5.7)
            c.saveState()
            c.translate(center, bottom - 10)
            c.rotate(35)
            c.drawString(0, 0, row["period"])
            c.restoreState()
    lx = x + 36
    for color, label in zip(colorset, labels):
        c.setFillColor(color)
        c.rect(lx, y + 2, 6, 6, stroke=0, fill=1)
        p(c, label, lx + 10, y + 9, 95, 6.1, color=MUTED)
        lx += 125


def draw_icon_row(c):
    xs = [74, 201, 333, 463]
    labels = ["OBSERVE", "DECOMPOSE", "PERSIST", "BUILD"]
    # Cup: small line-drawn mark.
    c.setStrokeColor(GOLD_LIGHT); c.setLineWidth(1.4)
    c.roundRect(xs[0], 155, 18, 14, 2, stroke=1, fill=0); c.arc(xs[0] + 14, 157, xs[0] + 25, 168, 265, 195)
    c.line(xs[0] + 3, 174, xs[0] + 5, 181); c.line(xs[0] + 10, 174, xs[0] + 12, 181)
    # Cube.
    x = xs[1] + 5; y = 160
    c.line(x, y + 8, x + 11, y + 14); c.line(x + 11, y + 14, x + 22, y + 8); c.line(x + 22, y + 8, x + 11, y + 2); c.line(x + 11, y + 2, x, y + 8)
    c.line(x, y + 8, x, y - 3); c.line(x, y - 3, x + 11, y - 9); c.line(x + 11, y - 9, x + 22, y - 3); c.line(x + 22, y - 3, x + 22, y + 8)
    c.line(x + 11, y + 2, x + 11, y - 9); c.line(x, y + 8, x + 11, y + 14); c.line(x + 11, y + 14, x + 11, y + 2); c.line(x + 22, y + 8, x + 11, y + 2)
    # Barbell.
    x = xs[2]; y = 164
    c.line(x, y, x + 28, y); c.line(x + 4, y - 9, x + 4, y + 9); c.line(x + 1, y - 6, x + 1, y + 6)
    c.line(x + 24, y - 9, x + 24, y + 9); c.line(x + 27, y - 6, x + 27, y + 6)
    # Code mark.
    c.setFont("DejaVu-Bold", 16); c.drawString(xs[3], 158, "</>")
    for x, label in zip(xs, labels):
        c.setFillColor(GOLD_LIGHT); c.setFont("DejaVu-Bold", 6.5); c.drawCentredString(x + 12, 132, label)


def page1(c):
    c.setFillColor(CHARCOAL); c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    # Restrained architectural lines and gold rule establish an original editorial identity.
    c.setStrokeColor(colors.HexColor("#3A403D")); c.setLineWidth(.7)
    c.line(42, 748, PAGE_W - 42, 748); c.line(42, 111, PAGE_W - 42, 111)
    c.setFillColor(GOLD); c.rect(42, 748, 48, 3, stroke=0, fill=1)
    p(c, "G4 AI MASTER CHALLENGE 001     /     BUSINESS DIAGNOSIS", 42, 727, 400, 8, color=GOLD_LIGHT, bold=True)
    p(c, "RavenStack -\nBeyond the Churn\nHeadline", 42, 665, PAGE_W - 84, 37, 43, color=IVORY, bold=True)
    p(c, "A monthly, evidence-driven diagnosis of growth, retention and commercial movement", 43, 475, 435, 16, 22, color=GOLD_LIGHT)
    p(c, "The count rose. The customer-retention answer is more complicated.", 43, 401, 420, 12, 17, color=IVORY, bold=True)
    p(c, "A decision paper grounded in five source tables, a daily account-plan reconstruction and a monthly executive view.", 43, 365, 390, 9, 14, color=colors.HexColor("#B7B9B2"))
    pill(c, 43, 294, "CONDITIONAL LIFECYCLE RECONSTRUCTION", GOLD)
    p(c, "Prepared by Thomas Leick", 43, 236, 300, 11, color=IVORY, bold=True)
    p(c, "Independent submission · 22 October 2026 · No G4 affiliation implied", 43, 216, 440, 8, color=colors.HexColor("#9EA29A"))
    draw_icon_row(c)
    c.setFillColor(colors.HexColor("#9EA29A")); c.setFont("DejaVu", 7)
    c.drawString(43, 83, "COFFEE / CUBE / DISCIPLINE / CODE")
    c.drawRightString(PAGE_W - 42, 83, "EVIDENCE BEFORE CERTAINTY")
    c.showPage()


def page2(c, daily):
    page_bg(c, 2, "Executive verdict")
    y = title(c, "Q1 / root cause", "The headline is not yet a churn rate.", "No causal root cause is established. The strongest verified finding is a conflict among outcome indicators and lifecycle records.")
    gap, cw, ch = 14, (PAGE_W - 84 - 14) / 2, 94
    card(c, 42, y, cw, ch, "Commercial customer churn", "UNKNOWN", "No reconciled customer outcome / eligible opening population. Conditional ledger result is shown separately.", RED)
    card(c, 42 + cw + gap, y, cw, ch, "2024 plan-proxy gross loss", "1.87%", "7 / 374 opening account x plan-tier relations lost coverage at least once.", GOLD)
    card(c, 42, y - ch - 12, cw, ch, "Plan proxy still lost at close", "0.80%", "3 / 374 opening relations remained without that plan-tier coverage at year close.", GOLD)
    card(c, 42 + cw + gap, y - ch - 12, cw, ch, "2024 opening customers lost", "0 / 190", "No opening-cohort account lost all reconstructed plan coverage; this is not certified commercial churn.", MOSS)
    yy = y - 2 * (ch + 12) - 10
    p(c, "THE FINDING", 42, yy, 120, 7.2, color=GOLD, bold=True)
    yy -= 18
    yy -= p(c, "A customer may lose one plan-tier relationship and remain active through another. Across 2023-2024, 54 of 62 date-derived plan losses occurred while another plan remained active. Eight episodes reached zero plan-proxy coverage; all eight later returned within the observed horizon.", 42, yy, PAGE_W - 84, 9.2, 13.6)
    yy -= 20
    c.setFillColor(INK); c.roundRect(42, yy - 92, PAGE_W - 84, 92, 7, stroke=0, fill=1)
    p(c, "LEADERSHIP DECISION", 58, yy - 14, PAGE_W - 116, 7, color=GOLD_LIGHT, bold=True)
    p(c, "Reconcile lifecycle and event linkage before funding a broad retention campaign. Review the 60 accounts with reconstructed plan loss, starting with the 8 full-coverage-loss/return cases. Run a controlled test after defining eligible customers and a verified 90-day outcome.", 58, yy - 31, PAGE_W - 116, 9, 13.2, color=IVORY)
    c.showPage()


def page3(c, daily):
    page_bg(c, 3, "Growth mathematics")
    rows = daily["periods"]["MONTHLY"]
    y = title(c, "02 / exposure, flows and rate", "More losses can accompany a larger base.", "The monthly ledger is the executive series. Counts, exposure and normalized indicators answer different questions.")
    p(c, "MONTHLY OPENING-COHORT LOSS RATES · 24 MONTHS", 42, y - 2, PAGE_W - 84, 7, color=GOLD, bold=True)
    draw_line_chart(c, rows, 42, y - 204, PAGE_W - 84, 185)
    p(c, "Solid = opening-cohort relations/customers losing coverage during month. Dashed = still lost at month close. Rates use the matching opening plan proxy or unique-account base; Jan 2023 is undefined because opening denominators are zero.", 42, y - 218, PAGE_W - 84, 7.1, 10, color=MUTED)
    p(c, "MONTHLY MOVEMENTS · COUNTS, NOT RATES", 42, y - 251, PAGE_W - 84, 7, color=GOLD, bold=True)
    draw_bar_chart(c, rows, 42, y - 420, PAGE_W - 84, 150)
    box_y = y - 445
    data = daily["annual_monthly_summary"]
    left, right = data["2023"], data["2024"]
    cards = [
        ("Recorded events / 100 account-months", f"{left['recorded_event_rows_per_100_opening_account_months']:.2f}  ->  {right['recorded_event_rows_per_100_opening_account_months']:.2f}"),
        ("Plan losses / 100 relation-months", f"{left['plan_loss_events_per_100_opening_relation_months']:.3f}  ->  {right['plan_loss_events_per_100_opening_relation_months']:.3f}"),
        ("Complete-loss episodes / 100 account-months", f"{left['customer_coverage_loss_events_per_100_opening_account_months']:.3f}  ->  {right['customer_coverage_loss_events_per_100_opening_account_months']:.3f}"),
    ]
    cw = (PAGE_W - 84 - 20) / 3
    for i, (label, value) in enumerate(cards):
        xx = 42 + i * (cw + 10)
        c.setFillColor(IVORY); c.roundRect(xx, box_y - 55, cw, 55, 5, stroke=0, fill=1)
        p(c, label, xx + 8, box_y - 7, cw - 14, 6.3, 8.3, color=MUTED, bold=True)
        p(c, value, xx + 8, box_y - 26, cw - 14, 8.1, color=INK, bold=True)
    p(c, "2023 -> 2024: event rows 73 -> 527; opening exposure 845 -> 3,909 account-months (4.63x); plan losses 6 -> 56 across 1,406 -> 9,414 relation-months. A symmetric arithmetic split attributes about 339 additional event rows to exposure and 115 to event intensity. This is not causal attribution; recording change is not identifiable.", 42, box_y - 68, PAGE_W - 84, 7.3, 10.1, color=INK)
    c.showPage()


def page4(c, business, daily):
    page_bg(c, 4, "Evidence across five tables")
    y = title(c, "03 / cross-table diagnosis", "The records explain the disagreement, not its cause.", "The five tables were compared at their natural grain; account outcomes were deduplicated before cross-table summaries.")
    items = [
        ("ACCOUNTS · 500", "110 account churn flags. Compared with any event history: 75 both, 35 flag-only, 277 event-only, 113 neither; 312 accounts differ pairwise."),
        ("SUBSCRIPTIONS · 5,000", "5,000 unique subscription IDs; 529 upgrade-flag rows and 218 downgrade-flag rows, with 23 rows carrying both. No linked from/to plan change or effective transition record."),
        ("FEATURE USAGE · 25,000", "Source usage count 124,561 -> 125,964 (+1.13%); per observed account-month 24.462 -> 24.747 (+1.17%). 19,142 rows predate linked subscription start; 290 follow an end date."),
        ("SUPPORT · 2,000 TICKETS", "825/2,000 satisfaction scores missing (41.25%). Any-event vs no-event mean: 3.9804 (815 scored; 580 missing) vs 3.9833 (360; 245 missing). Escalation: 71/1,395 (5.09%) vs 24/605 (3.97%)."),
        ("CHURN EVENTS · 600", "73 rows in 2023; 527 in 2024; 352 accounts; 339 non-reactivation rows. Reasons: features 114, support 104, budget 104, unknown 95, competitor 92, pricing 91."),
    ]
    data = [[Paragraph(f"<b>{escape(k)}</b>", ParagraphStyle("k", fontName="DejaVu-Bold", fontSize=7.3, leading=9, textColor=GOLD)),
             Paragraph(clean(v), ParagraphStyle("v", fontName="DejaVu", fontSize=7.4, leading=10.1, textColor=INK))] for k, v in items]
    table = Table(data, colWidths=[126, PAGE_W - 84 - 126], rowHeights=[63, 63, 69, 74, 64])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), IVORY), ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 10), ("RIGHTPADDING", (0,0), (-1,-1), 9),
        ("TOPPADDING", (0,0), (-1,-1), 9), ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LINEBELOW", (0,0), (-1,-2), 0.5, PAPER),
        ("LINEBEFORE", (1,0), (1,-1), 1.5, GOLD),
    ]))
    _, th = table.wrapOn(c, PAGE_W - 84, PAGE_H)
    table.drawOn(c, 42, y - th)
    yy = y - th - 22
    p(c, "WHAT IS SUPPORTED", 42, yy, PAGE_W - 84, 7.2, color=GOLD, bold=True)
    yy -= 17
    p(c, "Usage totals rose slightly while the observed account-month denominator was nearly unchanged; that is descriptive source volume, not verified adoption by active customers. Ticket satisfaction is very similar across retrospective event labels, but missing scores and unknown event timing limit the comparison. Reason codes can prioritize customer interviews; they do not prove root cause.", 42, yy, PAGE_W - 84, 8.3, 12, color=INK)
    yy -= 69
    p(c, "RECORDED MONEY FIELDS", 42, yy, PAGE_W - 84, 7.2, color=GOLD, bold=True)
    yy -= 17
    p(c, "The subscription file includes `mrr_amount` and `arr_amount` for all 5,000 rows; 778 rows are zero and ARR equals 12 x MRR on every row. Yet the source does not provide a reconciled account billing ledger or a validated effective-period/change mapping. Do not add repeated contract-row values and call the sum lost revenue. Revenue contraction remains not identified.", 42, yy, PAGE_W - 84, 8.3, 12, color=INK)
    c.showPage()


def page5(c, daily):
    page_bg(c, 5, "Segments and accounts")
    y = title(c, "Q2 / who needs attention", "A historical case list is not a risk model.", "All rates below are conditional date-derived plan-tier proxy comparisons, not predictive probabilities.")
    p(c, "2024 OPENING PLAN-RELATION COHORT", 42, y, PAGE_W - 84, 7.2, color=GOLD, bold=True)
    rows = [["Tier proxy", "Opening", "Lost in year", "Rate", "Still lost at close"],
            ["Enterprise", "120", "5", "4.17%", "2"],
            ["Basic", "132", "2", "1.52%", "1"],
            ["Pro", "122", "0", "0.00%", "0"]]
    data = [[Paragraph(f"<b>{escape(str(v))}</b>", ParagraphStyle("h", fontName="DejaVu-Bold", fontSize=7.3, leading=9, textColor=WHITE if ri == 0 else INK)) for v in row] for ri, row in enumerate(rows)]
    t = Table(data, colWidths=[140, 76, 95, 68, 120], rowHeights=24)
    t.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), INK), ("BACKGROUND", (0,1), (-1,-1), IVORY), ("VALIGN",(0,0),(-1,-1),"MIDDLE"), ("LEFTPADDING",(0,0),(-1,-1),8), ("GRID",(0,0),(-1,-1),0.4,PAPER)]))
    _, h = t.wrapOn(c, PAGE_W - 84, PAGE_H); t.drawOn(c, 42, y - 16 - h)
    yy = y - 16 - h - 18
    p(c, "Industry exposure (conditional plan-loss rows / relation-months) also varied: DevTools 10/2,215 (0.451 per 100); FinTech 8/2,146 (0.373); HealthTech 9/1,937 (0.465); Cybersecurity 9/1,716 (0.524); EdTech 6/1,400 (0.429). These are exposure diagnostics, not annual customer churn rates or causal rankings.", 42, yy, PAGE_W - 84, 7.7, 10.7, color=INK)
    yy -= 54
    p(c, "EIGHT RECONCILIATION CANDIDATES", 42, yy, PAGE_W - 84, 7.2, color=GOLD, bold=True)
    yy -= 16
    p(c, "Each account below had a reconstructed complete-coverage-loss episode followed by later date-derived coverage. Ask CS/RevOps to confirm whether the customer actually left, paused or changed contracts.", 42, yy, PAGE_W - 84, 7.7, 10.7, color=MUTED)
    yy -= 37
    accounts = [
        ("A-180abf", "DevTools / US / event / Pro", "2 plan losses; 1 full-loss episode"),
        ("A-0a282f", "DevTools / US / organic / Basic", "1 plan loss; 1 full-loss episode"),
        ("A-0baac2", "FinTech / DE / organic / Enterprise", "1 plan loss; 1 full-loss episode"),
        ("A-40a557", "Cybersecurity / AU / partner / Pro", "1 plan loss; 1 full-loss episode"),
        ("A-410e86", "FinTech / US / organic / Basic", "1 plan loss; 1 full-loss episode"),
        ("A-432483", "Cybersecurity / US / ads / Pro", "1 plan loss; 1 full-loss episode"),
        ("A-8adedc", "EdTech / US / event / Basic", "1 plan loss; 1 full-loss episode"),
        ("A-c9bb3e", "EdTech / US / ads / Pro", "1 plan loss; 1 full-loss episode"),
    ]
    colw = (PAGE_W - 94) / 2
    for i, (aid, segment, signal) in enumerate(accounts):
        col, row = i % 2, i // 2
        xx = 42 + col * (colw + 10)
        top = yy - row * 58
        c.setFillColor(IVORY); c.roundRect(xx, top - 49, colw, 49, 5, stroke=0, fill=1)
        p(c, aid, xx + 9, top - 7, colw - 18, 8, color=INK, bold=True)
        p(c, segment, xx + 9, top - 21, colw - 18, 6.4, 8, color=MUTED)
        p(c, signal, xx + 9, top - 34, colw - 18, 6.1, 8, color=GOLD)
    yy -= 4 * 58 + 4
    p(c, "These are account IDs for follow-up, not validated future-risk labels. The source event table has account_id but no subscription_id, so the event-to-plan relation remains unproven.", 42, yy, PAGE_W - 84, 7, 9.5, color=MUTED)
    c.showPage()


def page6(c):
    page_bg(c, 6, "Decision and impact")
    y = title(c, "Q3 / what should RavenStack do?", "Five moves. One measurement gate.", "The investment sequence follows evidence readiness: correct lifecycle definitions, reconcile cases, then test retention.")
    actions = [
        ("01", "Instrument lifecycle", "Data / Product Analytics · 0-30 days", "Link cancellation, reactivation and plan change to account + subscription IDs and effective timestamps. KPI: linked, reconciled lifecycle events."),
        ("02", "Review historical cases", "Customer Success + RevOps · 0-30 days", "Review 60 accounts with any plan loss, starting with the 8 full-coverage-loss/return cases. KPI: customer-confirmed outcome and reason documented."),
        ("03", "Audit transition flags", "RevOps / Product · 30-60 days", "Reconcile 529 upgrade and 218 downgrade rows, including 23 with both. KPI: dated source/destination plan and comparable contract amount."),
        ("04", "Measure activation", "Product Analytics · 30-60 days", "Instrument a canonical first-value event and meaningful adoption per eligible account cohort. KPI: 7/30-day instrumentation coverage."),
        ("05", "Run a holdout test", "Customer Success + Analytics · 60-90 days", "Randomize eligible accounts to outreach vs. holdout after definitions are stable. Primary metric: verified customer coverage at 90 days."),
    ]
    yy = y
    for no, heading, owner, body in actions:
        c.setFillColor(INK); c.circle(53, yy - 18, 11, stroke=0, fill=1)
        c.setFillColor(GOLD_LIGHT); c.setFont("DejaVu-Bold", 7); c.drawCentredString(53, yy - 20, no)
        p(c, heading, 73, yy, PAGE_W - 115, 10, color=INK, bold=True)
        p(c, owner, 73, yy - 15, PAGE_W - 115, 6.7, color=GOLD, bold=True)
        p(c, body, 73, yy - 27, PAGE_W - 115, 7.2, 9.5, color=MUTED)
        yy -= 58
    # Conditional impact frame: outcome units are intentionally separate from revenue.
    c.setFillColor(IVORY); c.roundRect(42, 82, PAGE_W - 84, 306, 7, stroke=0, fill=1)
    p(c, "IMPACT SENSITIVITY - NOT REVENUE OR CAUSAL ROI", 56, 374, PAGE_W - 112, 7.2, color=GOLD, bold=True)
    p(c, "Reference population: 60 historical accounts with a reconstructed plan loss; current eligibility is unknown. If all 60 were contacted, retained-account equivalents = 60 x assumed uptake x assumed incremental lift.", 56, 356, PAGE_W - 112, 7.1, 9.5, color=INK)
    data = [["Case", "Assumed uptake x lift", "Retained equivalents", "Gross benefit", "Contact cost", "Break-even monthly value"],
            ["Conservative", "50% x 5 pp", "1.5", "1.5 x V x H", "60 x C", "40 x C / H"],
            ["Base", "70% x 10 pp", "4.2", "4.2 x V x H", "60 x C", "14.29 x C / H"],
            ["Optimistic", "90% x 15 pp", "8.1", "8.1 x V x H", "60 x C", "7.41 x C / H"]]
    styles = [ParagraphStyle("th", fontName="DejaVu-Bold", fontSize=5.4, leading=6.3, textColor=WHITE), ParagraphStyle("td", fontName="DejaVu", fontSize=5.8, leading=7, textColor=INK)]
    tab = Table([[Paragraph(clean(str(v)), styles[0] if ri == 0 else styles[1]) for v in row] for ri, row in enumerate(data)], colWidths=[76,82,83,78,65,89], rowHeights=[26,20,20,20])
    tab.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),INK),("BACKGROUND",(0,1),(-1,-1),PAPER),("GRID",(0,0),(-1,-1),.35,RULE),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4)]))
    _, th = tab.wrapOn(c, PAGE_W - 112, 70); tab.drawOn(c, 56, 303 - th)
    p(c, "V = assumed monthly contribution per retained account; H = benefit horizon in months; C = assumed contact cost per account. These parameters are not estimated from RavenStack's records. Net modeled contribution = gross benefit - contact cost. No verified MRR, LTV or treatment effect is claimed.", 56, 205, PAGE_W - 112, 6.3, 8.3, color=MUTED)
    c.showPage()


def page7(c):
    page_bg(c, 7, "Method and limits")
    y = title(c, "06 / method, limits and laboratory", "Use the model to ask better questions.", "The paper's measures are deliberately explicit about unit, period and evidence status.")
    sections = [
        ("CLASSIC CUSTOMER CHURN", "Unique eligible customers lost in the month / unique active customers at month opening x 100. This commercial KPI is NOT IDENTIFIABLE as verified because supplied statuses, event records and date-derived coverage conflict."),
        ("PLAN-COVERAGE PROXY", "Unit = account x plan_tier. Monthly gross opening-cohort loss = distinct opening relations losing coverage at least once / opening relations x 100. Persistent closing loss uses opening relations still inactive at month close. This is not product churn."),
        ("TIME AND CENSORING", "Daily ledger is the source; executive reporting is monthly. Intervals use [start_date, end_date); null ends remain open to the observed horizon. End-date commercial meaning and intraday ordering are not independently validated. January 2023 opening base is zero: rate is UNDEFINED."),
        ("CAUSE AND ECONOMICS", "No causal root cause or calibrated future risk was established. Refunds are not recurring revenue. Subscription-row MRR/ARR and flags lack a fully reconciled effective-dated account billing/change ledger. Revenue contraction, GRR, NRR and LTV exposure remain unknown."),
        ("DECISION EXPERIMENT", "After lifecycle repair, define eligible paid accounts at risk of verified cancellation; randomize at account level to CS outreach or holdout; measure account coverage at 90 days, plan contraction and support guardrails. Report intention-to-treat difference and confidence interval; avoid mixing ticket-level records as independent customers."),
    ]
    yy = y
    for heading, body in sections:
        p(c, heading, 42, yy, PAGE_W - 84, 7, color=GOLD, bold=True)
        yy -= 14
        h = p(c, body, 42, yy, PAGE_W - 84, 7.3, 10.1, color=INK)
        yy -= h + 12
    c.setFillColor(INK); c.roundRect(42, 116, PAGE_W - 84, 90, 7, stroke=0, fill=1)
    p(c, "THE MONTHLY BUSINESS LABORATORY", 57, 190, PAGE_W - 114, 7.2, color=GOLD_LIGHT, bold=True)
    p(c, "The local React + FastAPI application is a companion for observed monthly flows and transparent scenarios. Run from the standalone package: cd solution && docker compose up --build. API: http://localhost:8000 · web: http://localhost:5173. Source analyses, data provenance, tests and the chronological process log remain inside this submission.", 57, 173, PAGE_W - 114, 7.2, 10.2, color=IVORY)
    p(c, "SOURCES", 42, 100, PAGE_W - 84, 7, color=GOLD, bold=True)
    refs = [
        "G4 Challenge 001: github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/tree/main/challenges/data-001-churn",
        "Submission guide and template: github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge",
        "SaaS Subscription & Churn Analytics, Kaggle, synthetic; credit River @ Rivalytics; MIT license per dataset/challenge metadata.",
    ]
    yy = 87
    for ref in refs:
        p(c, ref, 42, yy, PAGE_W - 84, 6.3, 8.4, color=MUTED)
        yy -= 11
    c.showPage()


def main():
    daily = json.loads(ANALYTICS.read_text(encoding="utf-8"))
    business = json.loads(BUSINESS.read_text(encoding="utf-8"))
    rows = daily["periods"]["MONTHLY"]
    assert len(rows) == 24 and rows[0]["period"] == "2023-01" and rows[-1]["period"] == "2024-12"
    assert rows[0]["opening_customers"] == rows[0]["opening_plan_relations"] == 0
    assert rows[0]["opening_cohort_churn_any_pct"] is None
    assert daily["summary"]["plan_relation_loss_events"] == 62
    c = canvas.Canvas(str(OUTPUT), pagesize=A4, pageCompression=1)
    c.setTitle("RavenStack - Beyond the Churn Headline")
    c.setAuthor("Thomas Leick")
    c.setSubject("G4 AI Master Challenge 001 - evidence-driven churn diagnosis")
    page1(c)
    page2(c, daily)
    page3(c, daily)
    page4(c, business, daily)
    page5(c, daily)
    page6(c)
    page7(c)
    c.save()
    print(f"Created {OUTPUT} ({OUTPUT.stat().st_size} bytes), 7 pages")


if __name__ == "__main__":
    main()
