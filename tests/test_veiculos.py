from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import Cliente, Usuario, Veiculo


def _login(client, user_id):
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True


def _create_receptionist_and_client():
    cliente = Cliente(nome='Cliente de Teste')
    usuario = Usuario(
        nome='Recepcionista',
        email='recepcao-veiculos@example.com',
        senha=generate_password_hash('senha123'),
        perfil='Recepcionista',
        ativo=True,
    )
    db.session.add_all([cliente, usuario])
    db.session.commit()
    return usuario.id, cliente.id


def test_vehicle_registration_renders_and_saves_normalized_plate(app, client):
    with app.app_context():
        user_id, client_id = _create_receptionist_and_client()

    _login(client, user_id)
    assert client.get('/veiculos/novo').status_code == 200

    response = client.post('/veiculos/novo', data={
        'cliente_id': str(client_id),
        'placa': '  abc1d23 ',
        'modelo': 'Hatch',
        'marca': 'Marca',
        'ano': '2024',
        'quilometragem': '0',
    })

    assert response.status_code == 302
    with app.app_context():
        veiculo = Veiculo.query.filter_by(placa='ABC1D23').one()
        assert veiculo.cliente_id == client_id
        assert veiculo.quilometragem == 0


def test_vehicle_registration_reports_duplicate_plate(app, client):
    with app.app_context():
        user_id, client_id = _create_receptionist_and_client()
        db.session.add(Veiculo(
            cliente_id=client_id,
            placa='ABC1D23',
            modelo='Sedan',
            marca='Marca',
            quilometragem=100,
        ))
        db.session.commit()

    _login(client, user_id)
    response = client.post('/veiculos/novo', data={
        'cliente_id': str(client_id),
        'placa': 'abc1d23',
        'modelo': 'Hatch',
        'marca': 'Marca',
        'ano': '2024',
        'quilometragem': '0',
    })

    assert response.status_code == 200
    assert 'Já existe um veículo cadastrado com esta placa.' in response.get_data(as_text=True)
    with app.app_context():
        assert Veiculo.query.filter_by(placa='ABC1D23').count() == 1
