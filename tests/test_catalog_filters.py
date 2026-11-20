from decimal import Decimal

from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import Cliente, Mecanico, Peca, Servico, Usuario, Veiculo


def _login_as_admin(app, client):
    with app.app_context():
        usuario = Usuario(
            nome='Administrador',
            email='admin-catalog@example.com',
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


def test_catalog_list_filters(app, client):
    _login_as_admin(app, client)
    with app.app_context():
        cliente_alfa = Cliente(nome='Cliente Alfa', cpf_cnpj='11111111111')
        cliente_beta = Cliente(nome='Cliente Beta', cpf_cnpj='22222222222')
        mecanico_ativo = Mecanico(nome='Motor Alfa', especialidade='Motor', ativo=True)
        mecanico_inativo = Mecanico(nome='Motor Beta', especialidade='Motor', ativo=False)
        peca_baixa = Peca(
            codigo='FILTRO-ALFA',
            descricao='Filtro Alfa',
            preco_custo=Decimal('5.00'),
            preco_venda=Decimal('10.00'),
            estoque_atual=1,
            estoque_minimo=5,
        )
        peca_normal = Peca(
            codigo='FILTRO-BETA',
            descricao='Filtro Beta',
            preco_custo=Decimal('5.00'),
            preco_venda=Decimal('10.00'),
            estoque_atual=10,
            estoque_minimo=2,
        )
        servico_ativo = Servico(nome='Revisão Alfa', preco_base=Decimal('100.00'), ativo=True)
        servico_inativo = Servico(nome='Revisão Beta', preco_base=Decimal('100.00'), ativo=False)
        db.session.add_all([
            cliente_alfa, cliente_beta, mecanico_ativo, mecanico_inativo,
            peca_baixa, peca_normal, servico_ativo, servico_inativo,
        ])
        db.session.flush()
        veiculo_alfa = Veiculo(
            cliente_id=cliente_alfa.id,
            placa='ABC1D23',
            marca='Marca Alfa',
            modelo='Modelo Alfa',
        )
        veiculo_beta = Veiculo(
            cliente_id=cliente_beta.id,
            placa='XYZ9Z99',
            marca='Marca Beta',
            modelo='Modelo Beta',
        )
        db.session.add_all([veiculo_alfa, veiculo_beta])
        db.session.commit()
        cliente_alfa_id = cliente_alfa.id

    response = client.get('/clientes/?busca=Alfa')
    assert 'Cliente Alfa' in response.get_data(as_text=True)
    assert 'Cliente Beta' not in response.get_data(as_text=True)

    response = client.get(f'/veiculos/?busca=Marca&cliente_id={cliente_alfa_id}')
    assert 'ABC1D23' in response.get_data(as_text=True)
    assert 'XYZ9Z99' not in response.get_data(as_text=True)

    response = client.get('/mecanicos/?busca=Motor&status=ativo')
    assert 'Motor Alfa' in response.get_data(as_text=True)
    assert 'Motor Beta' not in response.get_data(as_text=True)

    response = client.get('/pecas/?busca=FILTRO&estoque=baixo')
    assert 'Filtro Alfa' in response.get_data(as_text=True)
    assert 'Filtro Beta' not in response.get_data(as_text=True)

    response = client.get('/servicos/?busca=Revis%C3%A3o&status=ativo')
    assert 'Revisão Alfa' in response.get_data(as_text=True)
    assert 'Revisão Beta' not in response.get_data(as_text=True)


def test_catalog_forms_render_input_masks(app, client):
    _login_as_admin(app, client)
    with app.app_context():
        db.session.add(Cliente(nome='Cliente para veículo'))
        db.session.commit()

    assert 'data-mask="document"' in client.get('/clientes/novo').get_data(as_text=True)
    assert 'data-mask="plate"' in client.get('/veiculos/novo').get_data(as_text=True)
    assert 'data-mask="cpf"' in client.get('/mecanicos/novo').get_data(as_text=True)
    assert 'data-decimal="true"' in client.get('/pecas/novo').get_data(as_text=True)
    assert 'data-decimal="true"' in client.get('/servicos/novo').get_data(as_text=True)


def test_client_form_normalizes_values_and_rejects_invalid_document(app, client):
    _login_as_admin(app, client)
    invalid_response = client.post('/clientes/novo', data={
        'nome': 'Cliente Inválido',
        'cpf_cnpj': '123',
        'telefone': '',
        'email': '',
        'endereco': '',
    })

    assert invalid_response.status_code == 200
    assert 'Informe um CPF com 11 dígitos ou CNPJ com 14 dígitos.' in invalid_response.get_data(as_text=True)

    response = client.post('/clientes/novo', data={
        'nome': '  Cliente Válido  ',
        'cpf_cnpj': '123.456.789-09',
        'telefone': '(11) 99999-9999',
        'email': '  CLIENTE@EXAMPLE.COM ',
        'endereco': '',
    })
    assert response.status_code == 302
    with app.app_context():
        cliente = Cliente.query.filter_by(cpf_cnpj='123.456.789-09').one()
        assert cliente.nome == 'Cliente Válido'
        assert cliente.email == 'cliente@example.com'


def test_price_forms_accept_decimal_comma_and_reject_negative(app, client):
    _login_as_admin(app, client)
    response = client.post('/pecas/novo', data={
        'codigo': ' p-001 ',
        'descricao': ' Peça de teste ',
        'preco_custo': '12,50',
        'preco_venda': '25,99',
        'estoque_atual': '3',
        'estoque_minimo': '1',
    })
    assert response.status_code == 302
    with app.app_context():
        peca = Peca.query.filter_by(codigo='P-001').one()
        assert peca.preco_custo == Decimal('12.50')
        assert peca.preco_venda == Decimal('25.99')
        assert peca.descricao == 'Peça de teste'

    response = client.post('/servicos/novo', data={
        'nome': 'Serviço inválido',
        'descricao': '',
        'preco_base': '-1,00',
        'ativo': 'y',
    })
    assert response.status_code == 200
    with app.app_context():
        assert Servico.query.filter_by(nome='Serviço inválido').count() == 0
