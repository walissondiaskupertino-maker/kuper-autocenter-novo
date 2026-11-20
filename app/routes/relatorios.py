from flask import Blueprint, send_file, render_template, request
from flask_login import login_required
from app.models import OrdemServico, Cliente, Veiculo, Financeiro, Peca
from app.extensions import db
from sqlalchemy.sql import func
from datetime import datetime
import io
import os

relatorios_bp = Blueprint('relatorios', __name__)


def _finance_report_data():
    tipo = request.args.get('tipo', '')
    if tipo not in ('Entrada', 'Saida'):
        tipo = ''

    query = Financeiro.query
    if tipo:
        query = query.filter_by(tipo=tipo)
    lancamentos = query.order_by(
        Financeiro.data_movimentacao.desc(),
        Financeiro.id.desc(),
    ).all()
    total_entradas = sum(
        (lanc.valor for lanc in lancamentos if lanc.tipo == 'Entrada'),
        start=0,
    )
    total_saidas = sum(
        (lanc.valor for lanc in lancamentos if lanc.tipo == 'Saida'),
        start=0,
    )
    return tipo, lancamentos, total_entradas, total_saidas


def _format_currency_br(value):
    return f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


# ============ PDF - Lista de OS ============
@relatorios_bp.route('/os/pdf')
@login_required
def os_pdf():
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=30, alignment=1)
        
        elements.append(Paragraph("RELATÓRIO DE ORDENS DE SERVIÇO", title_style))
        elements.append(Spacer(1, 0.5*cm))
        
        ordens = OrdemServico.query.order_by(OrdemServico.data_abertura.desc()).all()
        
        data = [['OS #', 'Veículo', 'Cliente', 'Status', 'Valor', 'Data']]
        for os_obj in ordens:
            data.append([
                str(os_obj.id),
                f"{os_obj.veiculo.placa} - {os_obj.veiculo.marca}",
                os_obj.veiculo.cliente.nome[:20],
                os_obj.status,
                f"R$ {os_obj.valor_total:.2f}",
                os_obj.data_abertura.strftime('%d/%m/%Y')
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        buffer.seek(0)
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'os_relatorio_{datetime.now().strftime("%Y%m%d")}.pdf'
        )
    except Exception as e:
        return f"Erro ao gerar PDF: {str(e)}", 500

# ============ PDF - OS Individual (Profissional) ============
@relatorios_bp.route('/os/<int:id>/pdf')
@login_required
def os_pdf_detalhe(id):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        
        os_obj = OrdemServico.query.get_or_404(id)
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        elements = []
        styles = getSampleStyleSheet()
        
        # Cabeçalho
        header_style = ParagraphStyle('Header', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#1e293b'), alignment=1)
        elements.append(Paragraph("ORDEM DE SERVIÇO", header_style))
        elements.append(Paragraph(f"Nº {os_obj.id:05d}", ParagraphStyle('Sub', parent=styles['Normal'], fontSize=12, alignment=1)))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#3b82f6')))
        elements.append(Spacer(1, 0.5*cm))
        
        # Dados
        info_style = ParagraphStyle('Info', parent=styles['Normal'], fontSize=10, leading=14)
        elements.append(Paragraph(f"<b>Cliente:</b> {os_obj.veiculo.cliente.nome}", info_style))
        elements.append(Paragraph(f"<b>Telefone:</b> {os_obj.veiculo.cliente.telefone or '-'}", info_style))
        elements.append(Paragraph(f"<b>Veículo:</b> {os_obj.veiculo.marca} {os_obj.veiculo.modelo} - Placa: {os_obj.veiculo.placa}", info_style))
        elements.append(Paragraph(f"<b>Mecânico:</b> {os_obj.mecanico.nome if os_obj.mecanico else 'Não atribuído'}", info_style))
        elements.append(Spacer(1, 0.3*cm))
        elements.append(Paragraph(f"<b>Defeito Relatado:</b> {os_obj.defeito_relatado or '-'}", info_style))
        elements.append(Paragraph(f"<b>Diagnóstico:</b> {os_obj.diagnostico or '-'}", info_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Tabela Serviços
        if os_obj.servicos:
            elements.append(Paragraph("<b>SERVIÇOS REALIZADOS</b>", styles['Heading3']))
            data = [['Descrição', 'Qtd', 'Preço Unit.', 'Subtotal']]
            for item in os_obj.servicos:
                data.append([
                    item.servico.nome, 
                    str(item.quantidade), 
                    f"R$ {item.preco_unitario:.2f}", 
                    f"R$ {item.subtotal:.2f}"
                ])
            table = Table(data, colWidths=[8*cm, 2*cm, 3*cm, 3*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3b82f6')),
                ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('FONTSIZE', (0,0), (-1,-1), 9)
            ]))
            elements.append(table)
            elements.append(Spacer(1, 0.5*cm))

        # Tabela Peças
        if os_obj.pecas:
            elements.append(Paragraph("<b>PEÇAS UTILIZADAS</b>", styles['Heading3']))
            data = [['Peça', 'Código', 'Qtd', 'Preço Unit.', 'Subtotal']]
            for item in os_obj.pecas:
                data.append([
                    item.peca.descricao, 
                    item.peca.codigo or '-', 
                    str(item.quantidade), 
                    f"R$ {item.preco_unitario:.2f}", 
                    f"R$ {item.subtotal:.2f}"
                ])
            table = Table(data, colWidths=[6*cm, 2*cm, 2*cm, 3*cm, 3*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#10b981')),
                ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('FONTSIZE', (0,0), (-1,-1), 9)
            ]))
            elements.append(table)

        # Total
        elements.append(Spacer(1, 1*cm))
        total_style = ParagraphStyle('Total', parent=styles['Heading2'], fontSize=16, textColor=colors.HexColor('#1e293b'), alignment=2)
        elements.append(Paragraph(f"TOTAL GERAL: R$ {os_obj.valor_total:.2f}", total_style))
        
        # Assinatura
        elements.append(Spacer(1, 3*cm))
        elements.append(HRFlowable(width="40%", thickness=1, color=colors.black))
        elements.append(Paragraph("Assinatura do Cliente", ParagraphStyle('Sign', alignment=1, fontSize=9)))
        
        doc.build(elements)
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'OS_{os_obj.id:05d}.pdf')
    except Exception as e:
        return f"Erro ao gerar PDF: {str(e)}", 500

# ============ PDF - Estoque ============
@relatorios_bp.route('/estoque/pdf')
@login_required
def estoque_pdf():
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=30, alignment=1)
        
        elements.append(Paragraph("RELATÓRIO DE ESTOQUE DE PEÇAS", title_style))
        elements.append(Spacer(1, 0.5*cm))
        
        pecas = Peca.query.order_by(Peca.descricao).all()
        
        data = [['Código', 'Descrição', 'Atual', 'Mínimo', 'Status', 'Preço Venda']]
        for peca in pecas:
            status = 'BAIXO' if peca.estoque_atual < peca.estoque_minimo else 'OK'
            data.append([
                peca.codigo or '-',
                peca.descricao[:25],
                str(peca.estoque_atual),
                str(peca.estoque_minimo),
                status,
                f"R$ {peca.preco_venda:.2f}"
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        buffer.seek(0)
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'estoque_{datetime.now().strftime("%Y%m%d")}.pdf'
        )
    except Exception as e:
        return f"Erro ao gerar PDF: {str(e)}", 500

# ============ EXCEL - Financeiro ============
@relatorios_bp.route('/financeiro/excel')
@login_required
def financeiro_excel():
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    tipo, lancamentos, total_entradas, total_saidas = _finance_report_data()
    wb = Workbook()
    ws = wb.active
    ws.title = 'Financeiro'

    ws.merge_cells('A1:F1')
    ws['A1'] = 'RELATÓRIO FINANCEIRO - KUPER AUTOCENTER'
    ws['A1'].font = Font(bold=True, size=14, color='FFFFFF')
    ws['A1'].fill = PatternFill(
        start_color='1e293b',
        end_color='1e293b',
        fill_type='solid',
    )
    ws['A1'].alignment = Alignment(horizontal='center')
    ws['A2'] = f'Filtro: {tipo or "Todos os lançamentos"}'
    headers = ['Data', 'Tipo', 'Descrição', 'Categoria', 'Forma de pagamento', 'Valor (R$)']
    ws.append(headers)

    header_row = 3
    header_fill = PatternFill(
        start_color='3b82f6',
        end_color='3b82f6',
        fill_type='solid',
    )
    for cell in ws[header_row]:
        cell.fill = header_fill
        cell.font = Font(bold=True, color='FFFFFF')

    first_data_row = header_row + 1
    for lanc in lancamentos:
        row = ws.max_row + 1
        ws.cell(row, 1, lanc.data_movimentacao)
        ws.cell(row, 1).number_format = 'dd/mm/yyyy hh:mm'
        ws.cell(row, 2, lanc.tipo)
        ws.cell(row, 3, lanc.descricao)
        ws.cell(row, 4, lanc.categoria or '-')
        ws.cell(row, 5, lanc.forma_pagamento or '-')
        value_cell = ws.cell(row, 6, float(lanc.valor))
        value_cell.number_format = '"R$" #,##0.00'
        value_cell.font = Font(
            color='008000' if lanc.tipo == 'Entrada' else 'FF0000',
            bold=True,
        )
        for column in range(2, 6):
            ws.cell(row, column).data_type = 's'

    last_data_row = ws.max_row
    if lancamentos:
        ws.auto_filter.ref = f'A{header_row}:F{last_data_row}'
    else:
        ws.cell(first_data_row, 1, 'Nenhum lançamento encontrado.')
        ws.merge_cells(
            start_row=first_data_row,
            start_column=1,
            end_row=first_data_row,
            end_column=6,
        )

    summary_row = ws.max_row + 2
    summary = (
        ('TOTAL ENTRADAS:', float(total_entradas), '008000'),
        ('TOTAL SAÍDAS:', float(total_saidas), 'FF0000'),
        ('SALDO FINAL:', float(total_entradas - total_saidas), '1e40af'),
    )
    for offset, (label, value, color) in enumerate(summary):
        ws.cell(summary_row + offset, 1, label).font = Font(bold=True)
        value_cell = ws.cell(summary_row + offset, 6, value)
        value_cell.number_format = '"R$" #,##0.00'
        value_cell.font = Font(bold=True, color=color)

    for column, width in {'A': 20, 'B': 14, 'C': 42, 'D': 24, 'E': 24, 'F': 18}.items():
        ws.column_dimensions[column].width = width
    ws.freeze_panes = f'A{first_data_row}'

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    suffix = f'_{tipo.lower()}' if tipo else ''
    return send_file(
        buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'financeiro{suffix}_{datetime.now().strftime("%Y%m%d")}.xlsx',
    )


@relatorios_bp.route('/financeiro/pdf')
@login_required
def financeiro_pdf():
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
    )
    from xml.sax.saxutils import escape

    tipo, lancamentos, total_entradas, total_saidas = _finance_report_data()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title='Relatório Financeiro - Kuper Autocenter',
    )
    styles = getSampleStyleSheet()
    cell_style = ParagraphStyle(
        'FinanceCell',
        parent=styles['BodyText'],
        fontSize=8,
        leading=10,
    )
    elements = [
        Paragraph('RELATÓRIO FINANCEIRO - KUPER AUTOCENTER', styles['Title']),
        Paragraph(
            f'Filtro: {escape(tipo or "Todos os lançamentos")} | '
            f'Gerado em {datetime.now().strftime("%d/%m/%Y %H:%M")}',
            styles['Normal'],
        ),
        Spacer(1, 0.5 * cm),
    ]
    data = [[
        'Data', 'Tipo', 'Descrição', 'Categoria', 'Forma de pagamento', 'Valor',
    ]]
    for lanc in lancamentos:
        data.append([
            lanc.data_movimentacao.strftime('%d/%m/%Y %H:%M')
            if lanc.data_movimentacao else '-',
            lanc.tipo,
            Paragraph(escape(lanc.descricao or '-'), cell_style),
            Paragraph(escape(lanc.categoria or '-'), cell_style),
            Paragraph(escape(lanc.forma_pagamento or '-'), cell_style),
            _format_currency_br(lanc.valor),
        ])
    if not lancamentos:
        data.append(['Nenhum lançamento encontrado.', '', '', '', '', ''])

    table = Table(
        data,
        repeatRows=1,
        colWidths=[3.0 * cm, 2.2 * cm, 7.2 * cm, 4.2 * cm, 4.2 * cm, 3.2 * cm],
    )
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f1f5f9')]),
        ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.extend([
        table,
        Spacer(1, 0.5 * cm),
        Paragraph(f'Total de entradas: {_format_currency_br(total_entradas)}', styles['Normal']),
        Paragraph(f'Total de saídas: {_format_currency_br(total_saidas)}', styles['Normal']),
        Paragraph(
            f'Saldo final: {_format_currency_br(total_entradas - total_saidas)}',
            styles['Heading3'],
        ),
    ])
    doc.build(elements)
    buffer.seek(0)
    suffix = f'_{tipo.lower()}' if tipo else ''
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'financeiro{suffix}_{datetime.now().strftime("%Y%m%d")}.pdf',
    )

# ============ WORD - Clientes ============
@relatorios_bp.route('/clientes/word')
@login_required
def clientes_word():
    try:
        from docx import Document
        from docx.shared import Pt
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        
        doc = Document()
        
        titulo = doc.add_heading('RELATÓRIO DE CLIENTES', 0)
        titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_paragraph(f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}')
        doc.add_paragraph('')
        
        table = doc.add_table(rows=1, cols=5)
        table.style = 'Table Grid'
        
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Nome'
        hdr_cells[1].text = 'CPF/CNPJ'
        hdr_cells[2].text = 'Telefone'
        hdr_cells[3].text = 'E-mail'
        hdr_cells[4].text = 'Endereço'
        
        # Estilo do cabeçalho da tabela Word
        for cell in hdr_cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True
        
        clientes = Cliente.query.order_by(Cliente.nome).all()
        for cliente in clientes:
            row_cells = table.add_row().cells
            row_cells[0].text = cliente.nome
            row_cells[1].text = cliente.cpf_cnpj or '-'
            row_cells[2].text = cliente.telefone or '-'
            row_cells[3].text = cliente.email or '-'
            row_cells[4].text = cliente.endereco or '-'
        
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=f'clientes_{datetime.now().strftime("%Y%m%d")}.docx'
        )
    except Exception as e:
        return f"Erro ao gerar Word: {str(e)}", 500