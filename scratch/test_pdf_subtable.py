import sys
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def test():
    doc = SimpleDocTemplate("test_output.pdf", pagesize=landscape(A4))
    story = []
    
    style_left = ParagraphStyle(
        name='LeftText',
        fontName='Helvetica',
        fontSize=6.5,
        leading=7.8,
        textColor=colors.HexColor('#1A1A1A'),
        alignment=0
    )
    
    style_right = ParagraphStyle(
        name='RightText',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=9,
        textColor=colors.HexColor('#1C3144'),
        alignment=2 # Right aligned
    )
    
    # Let's build a cell list of flowables
    sub_table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ])
    
    # Cell 1: Day 13 with Garcia R. and Day shift
    # First line content: "- Garcia R."
    # Remaining content: "<b>Día (8-20):</b><br/>- Núñez"
    p_first = Paragraph("- Garcia R.", style_left)
    p_num = Paragraph("<b>13</b>", style_right)
    
    sub_table = Table([[p_first, p_num]], colWidths=[85, 18])
    sub_table.setStyle(sub_table_style)
    
    p_remaining = Paragraph("<b>Día (8-20):</b><br/>- Núñez", style_left)
    
    cell_flowables = [sub_table, p_remaining]
    
    # Main table
    main_table_data = [[cell_flowables]]
    main_table = Table(main_table_data, colWidths=[111.7], rowHeights=[60])
    main_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    
    story.append(main_table)
    doc.build(story)
    print("PDF test built successfully!")

if __name__ == '__main__':
    test()
