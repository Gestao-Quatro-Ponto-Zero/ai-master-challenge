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
        export_df.to_excel(writer, index=False, sheet_name='Pipeline Priorizado')

        guide = pd.DataFrame({
            'Item': [
                'Pontuação de Prioridade', 'Aderência Histórica', 'Necessidade de Atenção', 'Confiança nas Evidências',
                'Foco Imediato', 'Retomar o contato', 'Qualificar ou Descartar', 'Limitação importante'
            ],
            'Significado': [
                'Classificação operacional. Não representa uma probabilidade de fechamento.',
                'Contexto histórico relativo, baseado em padrões suavizados de negócios encerrados.',
                'Quão excepcional é o tempo atual na etapa de Negociação em comparação com ciclos históricos semelhantes.',
                'Quantidade de evidências históricas que sustentam a explicação da aderência.',
                'Contexto histórico favorável e uma janela de tempo que exige ação imediata.',
                'Contexto histórico favorável, mas a oportunidade está muito além dos padrões normais do ciclo.',
                'A oportunidade exige uma decisão explícita sobre o pipeline antes que mais esforço seja investido.',
                'O conjunto de dados de origem não possui data de criação para oportunidades em Prospecção nem um valor esperado confiável para os negócios.'
            ]
        })
        guide.to_excel(writer, index=False, sheet_name='Guia de Pontuação')

        workbook = writer.book
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#C7FF00', 'font_color': '#0A0A0A', 'border': 1})
        text_fmt = workbook.add_format({'text_wrap': True, 'valign': 'top'})
        score_fmt = workbook.add_format({'num_format': '0.0', 'align': 'center'})

        for sheet_name in ['Pipeline Priorizado', 'Guia de Pontuação']:
            worksheet = writer.sheets[sheet_name]
            worksheet.freeze_panes(1, 0)
            worksheet.autofilter(0, 0, (len(export_df) if sheet_name == 'Pipeline Priorizado' else len(guide)),
                                 (len(export_df.columns) if sheet_name == 'Pipeline Priorizado' else len(guide.columns)) - 1)
            for col_idx, col in enumerate((export_df.columns if sheet_name == 'Pipeline Priorizado' else guide.columns)):
                worksheet.write(0, col_idx, col, header_fmt)
                width = 18
                if 'explanation' in str(col) or col in ['recommended_action', 'Meaning']:
                    width = 42
                elif col in ['opportunity_id', 'account', 'sales_agent']:
                    width = 22
                worksheet.set_column(col_idx, col_idx, width, text_fmt)

        if 'priority_score' in export_df.columns:
            idx = export_df.columns.get_loc('priority_score')
            writer.sheets['Pipeline Priorizado'].set_column(idx, idx, 14, score_fmt)
    return output.getvalue()


def _format_filters(filters: Mapping[str, object]) -> str:
    parts = []
    for key, value in filters.items():
        if value not in (None, '', [], ['All'], 'All'):
            if isinstance(value, list):
                value = ', '.join(map(str, value))
            parts.append(f'{key}: {value}')
    return ' | '.join(parts) if parts else 'Todas as oportunidades em aberto'


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
        Paragraph('Relatório de Ações do Pipeline', styles['Heading3']),
        Spacer(1, 4*mm),
        Paragraph(f'<b>Filtros:</b> {_format_filters(filters)}', styles['SmallG4']),
        Spacer(1, 5*mm),
    ]

    focus_count = int((filtered['action_category'] == 'Focus Now').sum())
    decision_count = int(filtered['action_category'].isin(['Review Now', 'Requalify', 'Qualify or Drop', 'Re-engage']).sum())
    summary = [
        ['Oportunidades em aberto', 'Foco imediato', 'Requer decisão', 'Evidências limitadas'],
        [str(len(filtered)), str(focus_count), str(decision_count), str(int((filtered['evidence_confidence'] == 'Limited').sum()))]
    ]
    table = Table(summary, colWidths=[45*mm]*4)
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

    story.append(Paragraph('Principais prioridades', styles['SectionG4']))
    for idx, (_, row) in enumerate(top.iterrows(), start=1):
        account = row['account'] if pd.notna(row.get('account')) else 'Conta indisponível'
        story.append(Paragraph(
            f"<b>{idx}. {row['opportunity_id']} - {account}</b><br/>"
            f"Categoria da Ação: <b>{row['action_category']}</b> | Prioridade: <b>{row['priority_score']:.1f}</b> | "
            f"Etapa: {row['deal_stage']} | Produto: {row['product']}", styles['BodyG4']))
        why = [row.get(f'explanation_{i}', '') for i in range(1,5)]
        why = [x for x in why if isinstance(x, str) and x.strip()]
        for line in why[:3]:
            story.append(Paragraph(f'• {line}', styles['SmallG4']))
        story.append(Paragraph(f"<b>Ação recomendada:</b> {row['recommended_action']}", styles['SmallG4']))
        story.append(Spacer(1, 3*mm))

    story += [PageBreak(), Paragraph('Notas da pontuação', styles['SectionG4'])]
    notes = [
        'A Pontuação de Prioridade é uma classificação operacional, não uma probabilidade de fechamento.',
        'A Aderência Histórica utiliza padrões históricos suavizados e é intencionalmente secundária à Necessidade de Atenção.',
        'A Necessidade de Atenção compara o tempo na etapa de Engajamento com ciclos históricos de negócios comparáveis.',
        'Negócios muito antigos são tratados como candidatos à revisão do pipeline, em vez de receberem urgência ilimitada.',
        'Negócios em Prospecção não possuem um indicador confiável de tempo, pois os dados de origem não incluem a data de criação.'
    ]
    for note in notes:
        story.append(Paragraph(f'• {note}', styles['BodyG4']))

    doc.build(story)
    return output.getvalue()
