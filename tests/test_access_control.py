from app.models import Usuario
from app.extensions import db
from werkzeug.security import generate_password_hash


def test_operational_routes_redirect_anonymous_users_to_login(client):
    for path in ('/clientes/', '/veiculos/', '/ordens-servico/', '/financeiro/'):
        response = client.get(path)

        assert response.status_code == 302
        assert response.headers['Location'].startswith('/auth/login')


def test_registration_creates_non_admin_user_with_hashed_password(app, client):
    response = client.post('/auth/cadastro', data={
        'nome': 'Pessoa Teste',
        'email': '  TESTE@example.com ',
        'perfil': 'Recepcionista',
        'senha': 'senha123',
    })

    assert response.status_code == 302
    with app.app_context():
        usuario = Usuario.query.filter_by(email='teste@example.com').one()
        assert usuario.perfil == 'Recepcionista'
        assert usuario.senha != 'senha123'
        assert usuario.verificar_senha('senha123')


def test_registration_rejects_admin_role(app, client):
    response = client.post('/auth/cadastro', data={
        'nome': 'Tentativa Admin',
        'email': 'admin@example.com',
        'perfil': 'Admin',
        'senha': 'senha123',
    })

    assert response.status_code == 200
    with app.app_context():
        assert Usuario.query.filter_by(email='admin@example.com').count() == 0


def test_logout_is_post_only(app):
    logout_rule = next(
        rule for rule in app.url_map.iter_rules()
        if rule.endpoint == 'auth.logout'
    )

    assert 'POST' in logout_rule.methods
    assert 'GET' not in logout_rule.methods


def test_csrf_rejects_post_without_token(app, client):
    app.config['WTF_CSRF_ENABLED'] = True

    response = client.post('/auth/cadastro', data={
        'nome': 'Pessoa Teste',
        'email': 'teste@example.com',
        'perfil': 'Recepcionista',
        'senha': 'senha123',
    })

    assert response.status_code == 400


def test_login_normalizes_email(app, client):
    with app.app_context():
        usuario = Usuario(
            nome='Pessoa Teste',
            email='teste@example.com',
            senha=generate_password_hash('senha123'),
            perfil='Recepcionista',
            ativo=True,
        )
        db.session.add(usuario)
        db.session.commit()

    response = client.post('/auth/login', data={
        'email': '  TESTE@EXAMPLE.COM ',
        'senha': 'senha123',
    })

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/clientes/')


def test_create_admin_cli_creates_admin_with_hashed_password(app):
    result = app.test_cli_runner().invoke(args=[
        'create-admin',
        '--email', 'admin@example.com',
        '--nome', 'Administrador',
        '--password', 'segredo123',
    ], input='segredo123\n')

    assert result.exit_code == 0, result.output
    with app.app_context():
        usuario = Usuario.query.filter_by(email='admin@example.com').one()
        assert usuario.perfil == 'Admin'
        assert usuario.senha != 'segredo123'
        assert usuario.verificar_senha('segredo123')
