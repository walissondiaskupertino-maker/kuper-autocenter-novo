from decimal import Decimal
from io import BytesIO

from openpyxl import load_workbook
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import Financeiro, Usuario


def _login_as_admin(app, client):
    with app.app_context():
        usuario = Usuario(
            nome='Administrador',
            email='admin-financeiro@example.com',
            senha=generate_password_hash('senha123'),
            perfil='Admin',
            ativo=True,
        )
        db.session.add(usuario)
        db.session.commit()
        user_id = usuario.id

    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True


def test_financial_pdf_and_excel_exports_follow_type_filter(app, client):
    _login_as_admin(app, client)
    with app.app_context():
        db.session.add_all([
            Financeiro(
                tipo='Entrada',
                descricao='Recebimento teste',
                valor=Decimal('120.00'),
                categoria='Serviço',
                forma_pagamento='Pix',
            ),
            Financeiro(
                tipo='Saida',
                descricao='Despesa teste',
                valor=Decimal('35.00'),
                categoria='Peças',
                forma_pagamento='Dinheiro',
            ),
        ])
        db.session.commit()

    listing = client.get('/financeiro/?tipo=Entrada')
    listing_html = listing.get_data(as_text=True)
    assert listing.status_code == 200
    assert '/relatorios/financeiro/pdf?tipo=Entrada' in listing_html
    assert '/relatorios/financeiro/excel?tipo=Entrada' in listing_html

    pdf_response = client.get('/relatorios/financeiro/pdf?tipo=Entrada')
    assert pdf_response.status_code == 200
    assert pdf_response.mimetype == 'application/pdf'
    assert pdf_response.data.startswith(b'%PDF-')
    assert 'financeiro_entrada_' in pdf_response.headers['Content-Disposition']

    excel_response = client.get('/relatorios/financeiro/excel?tipo=Entrada')
    assert excel_response.status_code == 200
    workbook = load_workbook(BytesIO(excel_response.data), data_only=True)
    sheet = workbook['Financeiro']
    assert sheet['A2'].value == 'Filtro: Entrada'
    assert sheet['B4'].value == 'Entrada'
    assert sheet['C4'].value == 'Recebimento teste'
    assert sheet['F4'].value == 120
    assert sheet['A6'].value == 'TOTAL ENTRADAS:'
    assert sheet['F6'].value == 120
    assert sheet['F7'].value == 0
    assert sheet['F8'].value == 120
    assert 'Despesa teste' not in [
        cell.value for row in sheet.iter_rows() for cell in row
    ]
