"""
DealSignal — Report generation utilities.
Produces CSV and PDF exports of the filtered pipeline data.
"""

import io
from datetime import date
from typing import Optional

import pandas as pd
from fpdf import FPDF

# ── Rating colour palette (R, G, B) ──────────────────────────────────────────
RATING_RGB = {
    "AAA": (26, 122, 26),
    "AA":  (46, 204, 113),
    "A":   (130, 224, 170),
    "BBB": (243, 156, 18),
    "BB":  (230, 126, 34),
    "B":   (231, 76, 60),
    "CCC": (146, 43, 33),
}

DISPLAY_COLS = [
    ("deal_rating",            "Rating"),
    ("account",                "Account"),
    ("product",                "Product"),
    ("sales_agent",            "Sales Agent"),
    ("win_probability",        "Win Prob"),
    ("expected_revenue",       "Exp. Revenue"),
    ("effective_value",        "Deal Value"),
    ("top_contributing_factors", "Key Factors"),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_filename(prefix: str, ext: str, active_filters: dict) -> str:
    """Build a filename that embeds today's date and active filter values."""
    today = date.today().isoformat()
    parts = [prefix, today]
    for val in active_filters.values():
        if val and val != "All":
            slug = val.lower().replace(" ", "-")
            parts.append(slug)
    return "_".join(parts) + f".{ext}"


def _format_table(df: pd.DataFrame) -> pd.DataFrame:
    """Return a display-ready copy of the pipeline DataFrame."""
    cols = {src: label for src, label in DISPLAY_COLS if src in df.columns}
    out = df[list(cols.keys())].copy()
    out = out.rename(columns=cols)

    if "Win Prob" in out.columns:
        out["Win Prob"] = (
            pd.to_numeric(out["Win Prob"], errors="coerce")
            .mul(100).round(1).astype(str) + "%"
        )
    for money_col in ("Exp. Revenue", "Deal Value"):
        if money_col in out.columns:
            out[money_col] = (
                pd.to_numeric(out[money_col], errors="coerce")
                .apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "—")
            )
    return out


# ── CSV ───────────────────────────────────────────────────────────────────────

def generate_csv(filtered_df: pd.DataFrame) -> bytes:
    """Return UTF-8 CSV bytes of the formatted pipeline table."""
    table = _format_table(filtered_df)
    buf = io.StringIO()
    table.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


def make_csv_filename(active_filters: dict) -> str:
    return _make_filename("dealsignal", "csv", active_filters)


# ── PDF ───────────────────────────────────────────────────────────────────────

def _safe(text: str) -> str:
    """Replace characters outside latin-1 range with ASCII equivalents."""
    return (
        str(text)
        .replace("\u2014", "-")   # em dash
        .replace("\u2013", "-")   # en dash
        .replace("\u2018", "'")   # left single quote
        .replace("\u2019", "'")   # right single quote
        .replace("\u201c", '"')   # left double quote
        .replace("\u201d", '"')   # right double quote
        .encode("latin-1", errors="replace")
        .decode("latin-1")
    )


class _PDF(FPDF):
    def __init__(self, active_filters: dict):
        super().__init__(orientation="L", unit="mm", format="A4")
        self.active_filters = active_filters
        self.set_auto_page_break(auto=True, margin=12)
        self.add_page()

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(30, 30, 30)
        self.cell(0, 8, _safe("DealSignal - Pipeline Report"), ln=True)

        self.set_font("Helvetica", "", 8)
        self.set_text_color(100, 100, 100)
        today = date.today().strftime("%B %d, %Y")
        filter_summary = "  |  ".join(
            f"{k}: {v}" for k, v in self.active_filters.items()
            if v and v != "All"
        ) or "No filters applied"
        self.cell(0, 5, _safe(f"Generated: {today}    Filters: {filter_summary}"), ln=True)
        self.ln(3)

    def footer(self):
        self.set_y(-10)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, _safe(f"Page {self.page_no()} - DealSignal"), align="C")


def _kpi_row(pdf: _PDF, kpis: dict) -> None:
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_text_color(30, 30, 30)
    col_w = pdf.epw / len(kpis)
    for label, value in kpis.items():
        pdf.cell(col_w, 7, _safe(label), border=1, fill=True, align="C")
    pdf.ln()
    pdf.set_font("Helvetica", "", 10)
    for label, value in kpis.items():
        pdf.cell(col_w, 8, _safe(str(value)), border=1, align="C")
    pdf.ln(6)


def _table(pdf: _PDF, table: pd.DataFrame, col_widths: Optional[list] = None) -> None:
    """Render a DataFrame as a PDF table with header + data rows."""
    cols = list(table.columns)
    n = len(cols)
    available = pdf.epw
    widths = col_widths if col_widths else [available / n] * n

    # Header row
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_fill_color(50, 50, 50)
    pdf.set_text_color(255, 255, 255)
    for col, w in zip(cols, widths):
        pdf.cell(w, 6, _safe(str(col)[:20]), border=1, fill=True, align="C")
    pdf.ln()

    # Data rows
    pdf.set_font("Helvetica", "", 6.5)
    pdf.set_text_color(30, 30, 30)
    for _, row in table.iterrows():
        rating = str(row.get("Rating", "")) if "Rating" in row.index else ""
        row_h = 5
        for col, w in zip(cols, widths):
            val = _safe(str(row[col]) if pd.notna(row[col]) else "-")
            val = val[:28]  # truncate long strings
            fill = False
            if col == "Rating" and rating in RATING_RGB:
                r, g, b = RATING_RGB[rating]
                pdf.set_fill_color(r, g, b)
                pdf.set_text_color(255, 255, 255)
                fill = True
            pdf.cell(w, row_h, val, border=1, fill=fill, align="C" if col == "Rating" else "L")
            if fill:
                pdf.set_fill_color(255, 255, 255)
                pdf.set_text_color(30, 30, 30)
        pdf.ln()


def generate_pdf(
    filtered_df: pd.DataFrame,
    kpis: dict,
    active_filters: dict,
    metadata: dict,
) -> bytes:
    """Return PDF bytes of the full report."""
    pdf = _PDF(active_filters)

    # KPI section
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, _safe("Key Metrics"), ln=True)
    _kpi_row(pdf, kpis)

    # Top 10
    top10 = _format_table(filtered_df.head(10))
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, _safe("Top 10 Deals to Prioritize"), ln=True)
    top10_widths = [14, 38, 28, 35, 18, 28, 22, 54]  # total ≈ 237 mm (A4L effective)
    # Exclude Key Factors from top10
    top10_display = top10.drop(columns=["Key Factors"], errors="ignore")
    widths_no_kf = top10_widths[:len(top10_display.columns)]
    _table(pdf, top10_display, widths_no_kf)
    pdf.ln(4)

    # Full pipeline
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, _safe(f"Full Pipeline ({len(filtered_df)} deals)"), ln=True)
    full = _format_table(filtered_df)
    full_widths = [14, 32, 24, 30, 16, 24, 20, 77]
    _table(pdf, full, full_widths)

    return bytes(pdf.output())


def make_pdf_filename(active_filters: dict) -> str:
    return _make_filename("dealsignal", "pdf", active_filters)
