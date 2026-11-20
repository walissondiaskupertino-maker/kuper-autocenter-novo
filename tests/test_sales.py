import re
import sqlite3
from pathlib import Path

from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import (
    Cliente,
    Financeiro,
    ItemVenda,
    MovimentacaoEstoque,
    Pagamento,
    Peca,
    Servico,
    Usuario,
    Veiculo,
    Venda,
)


def _login(client, user_id):
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True


def _create_user(profile, email):
    user = Usuario(
        nome=email.split('@')[0],
        email=email,
        senha=generate_password_hash('senha123'),
        perfil=profile,
        ativo=True,
    )
    db.session.add(user)
    db.session.commit()
    return user


def _create_customer_and_vehicle(plate='ABC1D23'):
    cliente = Cliente(nome=f'Cliente {plate}')
    db.session.add(cliente)
    db.session.flush()
    veiculo = Veiculo(
        cliente_id=cliente.id,
        placa=plate,
        modelo='Modelo',
        marca='Marca',
        quilometragem=100,
    )
    db.session.add(veiculo)
    db.session.commit()
    return cliente, veiculo


def _open_sale(
    client, cliente_id, veiculo_id, item_type, item_id, quantity, discount='0'
):
    return client.post('/vendas/nova', data={
        'cliente_id': str(cliente_id),
        'veiculo_id': str(veiculo_id),
        'desconto': discount,
        'tipo_item[]': [item_type],
        'item_id[]': [str(item_id)],
        'quantidade[]': [str(quantity)],
    })


def test_seller_creates_sale_receives_partial_payments_and_deducts_stock_on_quit(
    app, client
):
    with app.app_context():
        seller = _create_user('Vendedor', 'vendedor@example.com')
        cliente, veiculo = _create_customer_and_vehicle()
        peca = Peca(
            descricao='Filtro de óleo',
            preco_custo=10,
            preco_venda=20,
            estoque_atual=4,
            estoque_minimo=1,
        )
        servico = Servico(nome='Revisão', preco_base=50, ativo=True)
        db.session.add_all([peca, servico])
        db.session.commit()
        seller_id = seller.id
        cliente_id = cliente.id
        veiculo_id = veiculo.id
        peca_id = peca.id
        servico_id = servico.id

    _login(client, seller_id)
    assert client.get('/vendas/nova').status_code == 200
    response = client.post('/vendas/nova', data={
        'cliente_id': str(cliente_id),
        'veiculo_id': str(veiculo_id),
        'desconto': '5,00',
        'tipo_item[]': ['peca', 'servico'],
        'item_id[]': [str(peca_id), str(servico_id)],
        'quantidade[]': ['2', '1'],
        'preco_unitario[]': ['0.01', '0.01'],
    })

    assert response.status_code == 302
    venda_id = int(re.search(r'/vendas/(\d+)$', response.headers['Location']).group(1))
    assert client.get(f'/vendas/{venda_id}').status_code == 200

    with app.app_context():
        venda = db.session.get(Venda, venda_id)
        assert venda.total == 85
        assert len(venda.itens) == 2
        assert db.session.get(Peca, peca_id).estoque_atual == 4

    response = client.post(f'/vendas/{venda_id}/pagamentos', data={
        'valor': '40,00',
        'metodo': 'pix',
        'parcelas': '1',
    })
    assert response.status_code == 302

    with app.app_context():
        venda = db.session.get(Venda, venda_id)
        assert venda.status == 'aberta'
        assert venda.valor_restante == 45
        assert db.session.get(Peca, peca_id).estoque_atual == 4
        assert Financeiro.query.filter_by(venda_id=venda_id).one().valor == 40

    response = client.post(f'/vendas/{venda_id}/pagamentos', data={
        'valor': '45,00',
        'metodo': 'cartao_credito',
        'parcelas': '3',
    })
    assert response.status_code == 302

    with app.app_context():
        venda = db.session.get(Venda, venda_id)
        assert venda.status == 'paga'
        assert venda.valor_restante == 0
        assert Pagamento.query.filter_by(venda_id=venda_id).count() == 2
        assert Financeiro.query.filter_by(venda_id=venda_id).count() == 2
        assert db.session.get(Peca, peca_id).estoque_atual == 2
        movimento = MovimentacaoEstoque.query.filter_by(
            descricao=f'Venda #{venda_id}'
        ).one()
        assert movimento.tipo == 'Saida'
        assert movimento.quantidade == 2
        assert ItemVenda.query.filter_by(venda_id=venda_id).count() == 2

    client.post(f'/vendas/{venda_id}/pagamentos', data={
        'valor': '1',
        'metodo': 'pix',
        'parcelas': '1',
    })
    with app.app_context():
        assert Pagamento.query.filter_by(venda_id=venda_id).count() == 2
        assert Financeiro.query.filter_by(venda_id=venda_id).count() == 2


def test_sale_financial_entries_cannot_be_deleted_manually(app, client):
    with app.app_context():
        admin = _create_user('Admin', 'admin-financeiro@example.com')
        cliente, veiculo = _create_customer_and_vehicle('JKL4M56')
        venda = Venda(
            cliente_id=cliente.id,
            veiculo_id=veiculo.id,
            vendedor_id=admin.id,
            status='paga',
            total=10,
        )
        db.session.add(venda)
        db.session.flush()
        lancamento = Financeiro(
            venda_id=venda.id,
            tipo='Entrada',
            descricao=f'Recebimento da venda #{venda.id}',
            valor=10,
            categoria='Venda',
        )
        db.session.add(lancamento)
        db.session.commit()
        admin_id = admin.id
        lancamento_id = lancamento.id

    _login(client, admin_id)
    response = client.post(f'/financeiro/{lancamento_id}/excluir')
    assert response.status_code == 302

    with app.app_context():
        assert db.session.get(Financeiro, lancamento_id) is not None


def test_seller_cannot_view_or_pay_another_sellers_sale(app, client):
    with app.app_context():
        first_seller = _create_user('Vendedor', 'vendedor1@example.com')
        second_seller = _create_user('Vendedor', 'vendedor2@example.com')
        admin = _create_user('Admin', 'admin-vendas@example.com')
        cliente, veiculo = _create_customer_and_vehicle('DEF2G34')
        servico = Servico(nome='Diagnóstico', preco_base=30, ativo=True)
        db.session.add(servico)
        db.session.commit()
        venda = Venda(
            cliente_id=cliente.id,
            veiculo_id=veiculo.id,
            vendedor_id=first_seller.id,
            total=30,
            itens=[ItemVenda(
                tipo='servico',
                servico_id=servico.id,
                quantidade=1,
                preco_unitario=30,
            )],
        )
        db.session.add(venda)
        db.session.commit()
        sale_id = venda.id
        seller_id = second_seller.id
        admin_id = admin.id

    _login(client, seller_id)
    assert client.get(f'/vendas/{sale_id}').status_code == 404
    assert client.post(f'/vendas/{sale_id}/pagamentos', data={
        'valor': '30',
        'metodo': 'pix',
        'parcelas': '1',
    }).status_code == 404

    with app.app_context():
        assert Pagamento.query.filter_by(venda_id=sale_id).count() == 0
        assert Financeiro.query.filter_by(venda_id=sale_id).count() == 0

    _login(client, admin_id)
    assert client.get(f'/vendas/{sale_id}').status_code == 200


def test_vendedor_account_is_created_only_by_local_cli(app):
    result = app.test_cli_runner().invoke(args=[
        'create-vendedor',
        '--email', 'novo-vendedor@example.com',
        '--nome', 'Novo Vendedor',
        '--password', 'segredo123',
    ], input='segredo123\n')

    assert result.exit_code == 0, result.output
    with app.app_context():
        user = Usuario.query.filter_by(email='novo-vendedor@example.com').one()
        assert user.perfil == 'Vendedor'
        assert user.senha != 'segredo123'
        assert user.verificar_senha('segredo123')


def test_overpayment_and_insufficient_stock_do_not_record_payment(app, client):
    with app.app_context():
        seller = _create_user('Vendedor', 'vendedor-estoque@example.com')
        cliente, veiculo = _create_customer_and_vehicle('GHI3J45')
        peca = Peca(
            descricao='Pastilha de freio',
            preco_custo=20,
            preco_venda=60,
            estoque_atual=2,
            estoque_minimo=1,
        )
        db.session.add(peca)
        db.session.commit()
        seller_id = seller.id
        cliente_id = cliente.id
        veiculo_id = veiculo.id
        peca_id = peca.id

    _login(client, seller_id)
    response = _open_sale(
        client,
        cliente_id,
        veiculo_id,
        'peca',
        peca_id,
        2,
    )
    assert response.status_code == 302
    sale_id = int(re.search(r'/vendas/(\d+)$', response.headers['Location']).group(1))

    client.post(f'/vendas/{sale_id}/pagamentos', data={
        'valor': '121',
        'metodo': 'pix',
        'parcelas': '1',
    })
    with app.app_context():
        assert Pagamento.query.filter_by(venda_id=sale_id).count() == 0

        db.session.get(Peca, peca_id).estoque_atual = 1
        db.session.commit()

    client.post(f'/vendas/{sale_id}/pagamentos', data={
        'valor': '120',
        'metodo': 'pix',
        'parcelas': '1',
    })
    with app.app_context():
        venda = db.session.get(Venda, sale_id)
        assert venda.status == 'aberta'
        assert Pagamento.query.filter_by(venda_id=sale_id).count() == 0
        assert Financeiro.query.filter_by(venda_id=sale_id).count() == 0
        assert db.session.get(Peca, peca_id).estoque_atual == 1
        assert MovimentacaoEstoque.query.filter_by(
            descricao=f'Venda #{sale_id}'
        ).count() == 0


def test_sqlite_sales_migration_preserves_existing_user_and_financial_rows():
    connection = sqlite3.connect(':memory:')
    connection.execute('PRAGMA foreign_keys = ON')
    connection.executescript(
        '''
        CREATE TABLE usuarios (id INTEGER PRIMARY KEY, perfil VARCHAR(13) NOT NULL);
        CREATE TABLE clientes (id INTEGER PRIMARY KEY);
        CREATE TABLE veiculos (id INTEGER PRIMARY KEY);
        CREATE TABLE mecanicos (id INTEGER PRIMARY KEY);
        CREATE TABLE pecas (id INTEGER PRIMARY KEY);
        CREATE TABLE servicos (id INTEGER PRIMARY KEY);
        CREATE TABLE financeiro (
            id INTEGER PRIMARY KEY,
            os_id INTEGER,
            tipo VARCHAR(6) NOT NULL,
            descricao VARCHAR(255) NOT NULL,
            valor NUMERIC(10, 2) NOT NULL,
            categoria VARCHAR(80),
            forma_pagamento VARCHAR(50),
            data_movimentacao DATETIME
        );
        INSERT INTO usuarios (id, perfil) VALUES (1, 'Admin');
        INSERT INTO clientes (id) VALUES (1);
        INSERT INTO veiculos (id) VALUES (1);
        INSERT INTO financeiro (id, tipo, descricao, valor)
            VALUES (1, 'Entrada', 'Registro anterior', 25.00);
        '''
    )

    migration_path = (
        Path(__file__).parents[1]
        / 'migrations'
        / 'sqlite'
        / '20261120_add_sales_module.sql'
    )
    connection.executescript(migration_path.read_text(encoding='utf-8'))
    connection.execute(
        'INSERT INTO usuarios (id, perfil) VALUES (2, ?)',
        ('Vendedor',),
    )

    assert connection.execute('SELECT COUNT(*) FROM usuarios').fetchone()[0] == 2
    assert connection.execute(
        'SELECT descricao, valor, venda_id FROM financeiro WHERE id = 1'
    ).fetchone() == ('Registro anterior', 25, None)
    assert {
        row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    } >= {'vendas', 'itens_venda', 'pagamentos'}
    assert connection.execute('PRAGMA foreign_key_check').fetchall() == []
    connection.close()
