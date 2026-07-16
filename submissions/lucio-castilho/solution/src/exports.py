from __future__ import annotations

from io import BytesIO
from typing import Mapping

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ACCENT = colors.HexColor('#C7FF00')
BLACK = colors.HexColor('#0A0A0A')
DARK = colors.HexColor('#171717')
MID = colors.HexColor('#333333')
LIGHT = colors.HexColor('#F4F4F4')
WHITE = colors.white

EXPORT_COLUMNS = [
    'opportunity_id', 'account', 'sales_agent', 'manager', 'regional_office', 'product', 'series',
    'deal_stage', 'priority_score', 'action_category', 'historical_fit', 'fit_category',
    'attention_need', 'attention_state', 'evidence_confidence', 'days_in_engaging',
    'recommended_action', 'explanation_1', 'explanation_2', 'explanation_3', 'explanation_4'
]


def build_excel_export(filtered: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        export_df = filtered[[c for c in EXPORT_COLUMNS if c in filtered.columns]].copy()
        export_df.to_excel(writer, index=False, sheet_name='Prioritized Pipeline')

        guide = pd.DataFrame({
            'Item': [
                'Priority Score', 'Historical Fit', 'Attention Need', 'Evidence Confidence',
                'Focus Now', 'Re-engage', 'Qualify or Drop', 'Important limitation'
            ],
            'Meaning': [
                'Operational ranking. It is not a probability of closing.',
                'Relative historical context from smoothed patterns in closed deals.',
                'How exceptional the current time in Engaging is versus comparable historical cycles.',
                'Amount of historical evidence supporting the fit explanation.',
                'Positive historical context and a time window that warrants immediate action.',
                'Historically positive context, but the deal is far beyond normal cycle patterns.',
                'The deal needs an explicit pipeline decision before more effort is invested.',
                'The source dataset has no created date for Prospecting and no reliable expected deal value.'
            ]
        })
        guide.to_excel(writer, index=False, sheet_name='Scoring Guide')

        workbook = writer.book
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#C7FF00', 'font_color': '#0A0A0A', 'border': 1})
        text_fmt = workbook.add_format({'text_wrap': True, 'valign': 'top'})
        score_fmt = workbook.add_format({'num_format': '0.0', 'align': 'center'})

        for sheet_name in ['Prioritized Pipeline', 'Scoring Guide']:
            worksheet = writer.sheets[sheet_name]
            worksheet.freeze_panes(1, 0)
            worksheet.autofilter(0, 0, (len(export_df) if sheet_name == 'Prioritized Pipeline' else len(guide)),
                                 (len(export_df.columns) if sheet_name == 'Prioritized Pipeline' else len(guide.columns)) - 1)
            for col_idx, col in enumerate((export_df.columns if sheet_name == 'Prioritized Pipeline' else guide.columns)):
                worksheet.write(0, col_idx, col, header_fmt)
                width = 18
                if 'explanation' in str(col) or col in ['recommended_action', 'Meaning']:
                    width = 42
                elif col in ['opportunity_id', 'account', 'sales_agent']:
                    width = 22
                worksheet.set_column(col_idx, col_idx, width, text_fmt)

        if 'priority_score' in export_df.columns:
            idx = export_df.columns.get_loc('priority_score')
            writer.sheets['Prioritized Pipeline'].set_column(idx, idx, 14, score_fmt)
    return output.getvalue()


def _format_filters(filters: Mapping[str, object]) -> str:
    parts = []
    for key, value in filters.items():
        if value not in (None, '', [], ['All'], 'All'):
            if isinstance(value, list):
                value = ', '.join(map(str, value))
            parts.append(f'{key}: {value}')
    return ' | '.join(parts) if parts else 'All open opportunities'


def build_pdf_export(filtered: pd.DataFrame, filters: Mapping[str, object]) -> bytes:
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=14*mm, leftMargin=14*mm, topMargin=14*mm, bottomMargin=14*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TitleG4', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=BLACK))
    styles.add(ParagraphStyle(name='SectionG4', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=BLACK, spaceBefore=8, spaceAfter=6))
    styles.add(ParagraphStyle(name='SmallG4', parent=styles['BodyText'], fontSize=8.5, leading=11, textColor=colors.HexColor('#404040')))
    styles.add(ParagraphStyle(name='BodyG4', parent=styles['BodyText'], fontSize=9.5, leading=13, textColor=BLACK))

    story = [
        Paragraph('G4 | LEAD SCORER', styles['TitleG4']),
        Paragraph('Pipeline Action Report', styles['Heading3']),
        Spacer(1, 4*mm),
        Paragraph(f'<b>Filters:</b> {_format_filters(filters)}', styles['SmallG4']),
        Spacer(1, 5*mm),
    ]

    focus_count = int((filtered['action_category'] == 'Focus Now').sum())
    decision_count = int(filtered['action_category'].isin(['Review Now', 'Requalify', 'Qualify or Drop', 'Re-engage']).sum())
    summary = [
        ['Open deals', 'Focus now', 'Need decision', 'Limited evidence'],
        [str(len(filtered)), str(focus_count), str(decision_count), str(int((filtered['evidence_confidence'] == 'Limited').sum()))]
    ]
    table = Table(summary, colWidths=[42*mm]*4)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), ACCENT), ('TEXTCOLOR', (0,0), (-1,0), BLACK),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOX', (0,0), (-1,-1), 0.5, MID), ('INNERGRID', (0,0), (-1,-1), 0.25, MID),
        ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story += [table, Spacer(1, 6*mm)]

    priority_actions = ['Focus Now', 'Review Now', 'Follow Up', 'Re-engage', 'Requalify', 'Qualify or Drop']
    top = filtered[filtered['action_category'].isin(priority_actions)].head(20)
    if top.empty:
        top = filtered.head(20)

    story.append(Paragraph('Top priorities', styles['SectionG4']))
    for idx, (_, row) in enumerate(top.iterrows(), start=1):
        account = row['account'] if pd.notna(row.get('account')) else 'Account unavailable'
        story.append(Paragraph(
            f"<b>{idx}. {row['opportunity_id']} - {account}</b><br/>"
            f"Action: <b>{row['action_category']}</b> | Priority: <b>{row['priority_score']:.1f}</b> | "
            f"Stage: {row['deal_stage']} | Product: {row['product']}", styles['BodyG4']))
        why = [row.get(f'explanation_{i}', '') for i in range(1,5)]
        why = [x for x in why if isinstance(x, str) and x.strip()]
        for line in why[:3]:
            story.append(Paragraph(f'• {line}', styles['SmallG4']))
        story.append(Paragraph(f"<b>Recommended action:</b> {row['recommended_action']}", styles['SmallG4']))
        story.append(Spacer(1, 3*mm))

    story += [PageBreak(), Paragraph('Scoring notes', styles['SectionG4'])]
    notes = [
        'Priority Score is an operational ranking, not a probability of closing.',
        'Historical Fit uses smoothed historical patterns and is intentionally secondary to Attention Need.',
        'Attention Need compares time in Engaging with comparable historical deal cycles.',
        'Very old deals are treated as pipeline review candidates instead of receiving unlimited urgency.',
        'Prospecting deals have no reliable age signal because the source data does not include a created date.'
    ]
    for note in notes:
        story.append(Paragraph(f'• {note}', styles['BodyG4']))

    doc.build(story)
    return output.getvalue()
