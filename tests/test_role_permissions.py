import sqlite3
from pathlib import Path

from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import (
    Cliente,
    Mecanico,
    MovimentacaoEstoque,
    OrdemServico,
    OsPeca,
    OsServico,
    Peca,
    Servico,
    Usuario,
    Veiculo,
)


def _login(client, user_id):
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True


def _create_user(profile, email, mechanic_id=None):
    user = Usuario(
        nome=email.split('@')[0],
        email=email,
        senha=generate_password_hash('senha123'),
        perfil=profile,
        mecanico_id=mechanic_id,
    )
    db.session.add(user)
    db.session.commit()
    return user


def _create_order(mechanic_id, plate):
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
    db.session.flush()
    ordem = OrdemServico(
        veiculo_id=veiculo.id,
        mecanico_id=mechanic_id,
        status='Aberto',
        defeito_relatado='Ruído',
    )
    db.session.add(ordem)
    db.session.commit()
    return ordem


def test_receptionist_can_operate_customers_but_not_finance_or_dashboard(app, client):
    with app.app_context():
        user = _create_user('Recepcionista', 'recepcao@example.com')
        ordem = _create_order(None, 'JJJ1J11')
        user_id = user.id
        order_id = ordem.id

    _login(client, user_id)

    assert client.get('/clientes/').status_code == 200
    assert client.get(f'/ordens-servico/{order_id}').status_code == 200
    assert client.get('/financeiro/').status_code == 403
    assert client.get('/').status_code == 403
    assert client.post('/auth/logout').status_code == 302


def test_admin_keeps_dashboard_and_finance_access(app, client):
    with app.app_context():
        user = _create_user('Admin', 'admin-dashboard@example.com')
        ordem = _create_order(None, 'KKK2K22')
        user_id = user.id
        order_id = ordem.id

    _login(client, user_id)

    assert client.get('/').status_code == 200
    assert client.get('/financeiro/').status_code == 200
    assert client.get(f'/ordens-servico/{order_id}').status_code == 200


def test_receptionist_cannot_complete_order_through_edit_form(app, client):
    with app.app_context():
        user = _create_user('Recepcionista', 'recepcao-os@example.com')
        ordem = _create_order(None, 'III9I99')
        user_id = user.id
        order_id = ordem.id
        vehicle_id = ordem.veiculo_id

    _login(client, user_id)
    response = client.post(f'/ordens-servico/{order_id}/editar', data={
        'veiculo_id': str(vehicle_id),
        'mecanico_id': '0',
        'status': 'Concluído',
        'defeito_relatado': 'Ruído',
        'diagnostico': 'Revisado',
    })

    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(OrdemServico, order_id).status == 'Aberto'


def test_mechanic_sees_only_assigned_orders_and_can_update_diagnosis(app, client):
    with app.app_context():
        assigned_mechanic = Mecanico(nome='Mecânico 1')
        other_mechanic = Mecanico(nome='Mecânico 2')
        db.session.add_all([assigned_mechanic, other_mechanic])
        db.session.flush()
        user = _create_user(
            'Mecanico',
            'mecanico@example.com',
            assigned_mechanic.id,
        )
        assigned_order = _create_order(assigned_mechanic.id, 'AAA1A11')
        other_order = _create_order(other_mechanic.id, 'BBB2B22')
        user_id = user.id
        assigned_order_id = assigned_order.id
        other_order_id = other_order.id

    _login(client, user_id)

    listing = client.get('/ordens-servico/')
    assert listing.status_code == 200
    assert b'AAA1A11' in listing.data
    assert b'BBB2B22' not in listing.data
    details = client.get(f'/ordens-servico/{assigned_order_id}')
    assert details.status_code == 200
    assert b'Salvar diagn' in details.data
    assert b'Total da OS' not in details.data
    assert client.get(f'/ordens-servico/{other_order_id}').status_code == 404

    response = client.post(
        f'/ordens-servico/{assigned_order_id}/diagnostico',
        data={'diagnostico': 'Verificado pelo mecânico.'},
    )
    assert response.status_code == 302
    with app.app_context():
        ordem = db.session.get(OrdemServico, assigned_order_id)
        assert ordem.diagnostico == 'Verificado pelo mecânico.'

    assert client.get('/pecas/').status_code == 403
    assert client.post(f'/ordens-servico/{assigned_order_id}/concluir').status_code == 403


def test_unlinked_mechanic_cannot_log_in(app, client):
    with app.app_context():
        _create_user('Mecanico', 'sem-vinculo@example.com')

    response = client.post('/auth/login', data={
        'email': 'sem-vinculo@example.com',
        'senha': 'senha123',
    })

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/auth/login')


def test_link_mechanic_cli_assigns_account(app):
    with app.app_context():
        mechanic = Mecanico(nome='Mecânico CLI')
        user = Usuario(
            nome='Mecânico CLI',
            email='mecanico-cli@example.com',
            senha=generate_password_hash('senha123'),
            perfil='Mecanico',
        )
        db.session.add_all([mechanic, user])
        db.session.commit()
        mechanic_id = mechanic.id

    result = app.test_cli_runner().invoke(args=[
        'link-mechanic',
        '--email', 'mecanico-cli@example.com',
        '--mecanico-id', str(mechanic_id),
    ])

    assert result.exit_code == 0, result.output
    with app.app_context():
        user = Usuario.query.filter_by(email='mecanico-cli@example.com').one()
        assert user.mecanico_id == mechanic_id


def test_service_subtotal_is_generated_and_quantity_must_be_positive(app, client):
    with app.app_context():
        user = _create_user('Admin', 'admin@example.com')
        ordem = _create_order(None, 'CCC3C33')
        servico = Servico(nome='Revisão', preco_base=100)
        db.session.add(servico)
        db.session.commit()
        user_id = user.id
        ordem_id = ordem.id
        servico_id = servico.id

    _login(client, user_id)

    response = client.post(
        f'/ordens-servico/{ordem_id}/adicionar-servico',
        data={'servico_id': servico_id, 'quantidade': '2'},
    )
    assert response.status_code == 302
    with app.app_context():
        item = OsServico.query.filter_by(os_id=ordem_id).one()
        ordem = db.session.get(OrdemServico, ordem_id)
        assert item.subtotal == 200
        assert ordem.valor_total == 200

    response = client.post(
        f'/ordens-servico/{ordem_id}/adicionar-servico',
        data={'servico_id': servico_id, 'quantidade': '-1'},
    )
    assert response.status_code == 302
    with app.app_context():
        assert OsServico.query.filter_by(os_id=ordem_id).count() == 1


def test_vehicle_with_work_order_cannot_be_deleted(app, client):
    with app.app_context():
        user = _create_user('Recepcionista', 'recepcao-veiculos@example.com')
        ordem = _create_order(None, 'DDD4D44')
        vehicle_id = ordem.veiculo_id
        order_id = ordem.id
        user_id = user.id

    _login(client, user_id)
    response = client.post(f'/veiculos/{vehicle_id}/excluir')

    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(Veiculo, vehicle_id) is not None
        assert db.session.get(OrdemServico, order_id) is not None
    with client.session_transaction() as session:
        assert session.get('_flashes') is not None


def test_customer_with_vehicle_cannot_be_deleted(app, client):
    with app.app_context():
        user = _create_user('Recepcionista', 'recepcao-clientes@example.com')
        ordem = _create_order(None, 'HHH8H88')
        customer_id = db.session.get(Veiculo, ordem.veiculo_id).cliente_id
        order_id = ordem.id
        vehicle_id = ordem.veiculo_id
        user_id = user.id

    _login(client, user_id)
    response = client.post(f'/clientes/{customer_id}/excluir')

    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(Cliente, customer_id) is not None
        assert db.session.get(Veiculo, vehicle_id) is not None
        assert db.session.get(OrdemServico, order_id) is not None


def test_sqlite_mechanic_link_migration_adds_nullable_unique_foreign_key():
    connection = sqlite3.connect(':memory:')
    connection.execute('PRAGMA foreign_keys = ON')
    connection.executescript(
        'CREATE TABLE mecanicos (id INTEGER PRIMARY KEY);'
        'CREATE TABLE usuarios (id INTEGER PRIMARY KEY, email TEXT NOT NULL);'
    )

    migration_path = (
        Path(__file__).parents[1]
        / 'migrations'
        / 'sqlite'
        / '20261119_add_usuario_mecanico_id.sql'
    )
    connection.executescript(migration_path.read_text(encoding='utf-8'))

    columns = {row[1] for row in connection.execute('PRAGMA table_info(usuarios)')}
    foreign_keys = list(connection.execute('PRAGMA foreign_key_list(usuarios)'))
    indexes = list(connection.execute('PRAGMA index_list(usuarios)'))

    assert 'mecanico_id' in columns
    assert any(row[2] == 'mecanicos' and row[3] == 'mecanico_id' for row in foreign_keys)
    assert any(row[1] == 'uq_usuarios_mecanico_id' and row[2] == 1 for row in indexes)


def test_invalid_part_quantity_does_not_change_stock(app, client):
    with app.app_context():
        user = _create_user('Admin', 'admin-estoque@example.com')
        ordem = _create_order(None, 'EEE5E55')
        peca = Peca(
            descricao='Filtro',
            preco_custo=10,
            preco_venda=20,
            estoque_atual=5,
            estoque_minimo=1,
        )
        db.session.add(peca)
        db.session.commit()
        user_id = user.id
        order_id = ordem.id
        part_id = peca.id

    _login(client, user_id)
    response = client.post(
        f'/ordens-servico/{order_id}/adicionar-peca',
        data={'peca_id': part_id, 'quantidade': '-2'},
    )

    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(Peca, part_id).estoque_atual == 5
        assert OsPeca.query.filter_by(os_id=order_id).count() == 0
        assert MovimentacaoEstoque.query.filter_by(os_id=order_id).count() == 0


def test_item_cannot_be_removed_by_using_another_work_order_id(app, client):
    with app.app_context():
        user = _create_user('Admin', 'admin-os@example.com')
        first_order = _create_order(None, 'FFF6F66')
        second_order = _create_order(None, 'GGG7G77')
        service = Servico(nome='Alinhamento', preco_base=50)
        db.session.add(service)
        db.session.commit()
        user_id = user.id
        first_order_id = first_order.id
        second_order_id = second_order.id
        service_id = service.id

    _login(client, user_id)
    client.post(
        f'/ordens-servico/{second_order_id}/adicionar-servico',
        data={'servico_id': service_id, 'quantidade': '1'},
    )

    with app.app_context():
        item = OsServico.query.filter_by(os_id=second_order_id).one()
        item_id = item.id

    response = client.post(
        f'/ordens-servico/{first_order_id}/remover-item/servico/{item_id}'
    )

    assert response.status_code == 404
    with app.app_context():
        assert OsServico.query.filter_by(id=item_id, os_id=second_order_id).count() == 1
